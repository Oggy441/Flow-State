"""
BurnoutRadar — FastAPI Backend
Main application entrypoint with all API routes and WebSocket endpoints.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from contextlib import asynccontextmanager
from typing import Optional
import json
import time

from database import init_db, get_session, EventWindow, BurnoutScore, engine
from features import extract_features
from model import predict_score
from calibration import update_baseline, get_baseline_data, reset_baseline
from ws_manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="BurnoutRadar API",
    description="Real-time burnout detection via behavioural biometrics",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow dashboard dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Ingest Endpoint ---

@app.post("/ingest")
async def ingest_event(event: dict):
    """
    Receive a raw 30-second event window from the agent.
    Stores the event, extracts features, computes score, and pushes via WebSocket.
    """
    user_id = event.get("user_id", "demo")
    ts = event.get("ts", time.time())

    with Session(engine) as session:
        # Store raw event
        db_event = EventWindow(
            user_id=user_id,
            timestamp=ts,
            window_sec=event.get("window_sec", 30),
            mouse_speed_mean=event.get("mouse_speed_mean", 0),
            mouse_jitter=event.get("mouse_jitter", 0),
            clicks=event.get("clicks", 0),
            wpm_estimate=event.get("wpm_estimate", 0),
            backspace_rate=event.get("backspace_rate", 0),
            key_pause_count=event.get("key_pause_count", 0),
            scroll_depth_pct=event.get("scroll_depth_pct", 0),
            scroll_backtracks=event.get("scroll_backtracks", 0),
            idle_sec=event.get("idle_sec", 0),
            task_switches=event.get("task_switches", 0),
            hour_of_day=event.get("hour_of_day", 12),
        )
        session.add(db_event)
        session.commit()

        # Update baseline with new data
        baseline_info = update_baseline(user_id, session)
        baseline_data = get_baseline_data(user_id, session)

        # Extract features and predict
        features = extract_features(event, baseline_data)
        result = predict_score(features)

        # Store score
        db_score = BurnoutScore(
            user_id=user_id,
            timestamp=ts,
            score=result["score"],
            severity=result["severity"],
            factors=json.dumps(result["factors"]),
        )
        session.add(db_score)
        session.commit()

    # Push to WebSocket clients
    ws_payload = {
        "type": "score_update",
        "user_id": user_id,
        "timestamp": ts,
        "score": result["score"],
        "severity": result["severity"],
        "color": result["color"],
        "factors": result["factors"],
        "calibration_ready": baseline_info["calibration_ready"],
        "sample_count": baseline_info["sample_count"],
        # Raw sensor metrics — always included so the dashboard can display them
        "metrics": {
            "mouse_speed": event.get("mouse_speed_mean", 0),
            "mouse_jitter": event.get("mouse_jitter", 0),
            "clicks": event.get("clicks", 0),
            "wpm": event.get("wpm_estimate", 0),
            "backspace_rate": event.get("backspace_rate", 0),
            "idle_sec": event.get("idle_sec", 0),
            "scroll_depth": event.get("scroll_depth_pct", 0),
            "scroll_backtracks": event.get("scroll_backtracks", 0),
            "task_switches": event.get("task_switches", 0),
        },
    }
    await manager.send_score_update(user_id, ws_payload)

    return {
        "status": "ok",
        "score": result["score"],
        "severity": result["severity"],
    }


# --- Score Endpoint ---

@app.get("/score/{user_id}")
def get_score(user_id: str):
    """Get the latest burnout score for a user."""
    with Session(engine) as session:
        statement = (
            select(BurnoutScore)
            .where(BurnoutScore.user_id == user_id)
            .order_by(BurnoutScore.timestamp.desc())
            .limit(1)
        )
        score = session.exec(statement).first()

        if not score:
            return {"score": 0, "severity": "low", "color": "#4ade80", "factors": []}

        return {
            "score": score.score,
            "severity": score.severity,
            "color": None,
            "factors": json.loads(score.factors),
            "timestamp": score.timestamp,
        }


# --- History Endpoint ---

@app.get("/history/{user_id}")
def get_history(user_id: str, range: str = "7d", limit: int = 500):
    """Get historical burnout scores for trend visualization."""
    range_map = {"1h": 3600, "6h": 21600, "1d": 86400, "7d": 604800, "30d": 2592000}
    seconds = range_map.get(range, 604800)
    cutoff = time.time() - seconds

    with Session(engine) as session:
        statement = (
            select(BurnoutScore)
            .where(BurnoutScore.user_id == user_id)
            .where(BurnoutScore.timestamp >= cutoff)
            .order_by(BurnoutScore.timestamp.asc())
            .limit(limit)
        )
        scores = session.exec(statement).all()

        return [
            {
                "timestamp": s.timestamp,
                "score": s.score,
                "severity": s.severity,
            }
            for s in scores
        ]


# --- Factors Endpoint ---

@app.get("/factors/{user_id}")
def get_factors(user_id: str):
    """Get top contributing factors from the latest score."""
    with Session(engine) as session:
        statement = (
            select(BurnoutScore)
            .where(BurnoutScore.user_id == user_id)
            .order_by(BurnoutScore.timestamp.desc())
            .limit(1)
        )
        score = session.exec(statement).first()

        if not score:
            return {"factors": []}

        return {"factors": json.loads(score.factors)}


# --- Heatmap Data Endpoint ---

@app.get("/heatmap/{user_id}")
def get_heatmap(user_id: str):
    """
    Get activity heatmap data — average burnout score by day-of-week x hour-of-day.
    Returns a 7x24 grid.
    """
    with Session(engine) as session:
        statement = (
            select(BurnoutScore)
            .where(BurnoutScore.user_id == user_id)
            .order_by(BurnoutScore.timestamp.desc())
            .limit(2000)
        )
        scores = session.exec(statement).all()

        if not scores:
            return {"heatmap": []}

        from datetime import datetime
        grid = {}
        for s in scores:
            dt = datetime.fromtimestamp(s.timestamp)
            day = dt.weekday()  # 0=Monday
            hour = dt.hour
            key = f"{day}-{hour}"
            if key not in grid:
                grid[key] = []
            grid[key].append(s.score)

        heatmap = []
        for day in range(7):
            for hour in range(24):
                key = f"{day}-{hour}"
                values = grid.get(key, [])
                avg = sum(values) / len(values) if values else 0
                heatmap.append({
                    "day": day,
                    "hour": hour,
                    "score": round(avg, 1),
                    "count": len(values),
                })

        return {"heatmap": heatmap}


# --- Calibration Endpoints ---

@app.get("/calibration/{user_id}")
def get_calibration_status(user_id: str):
    """Check calibration status for a user."""
    with Session(engine) as session:
        baseline_data = get_baseline_data(user_id, session)
        info = update_baseline(user_id, session)
        return {
            "calibration_ready": info["calibration_ready"],
            "sample_count": info["sample_count"],
        }


@app.post("/calibrate/reset")
def reset_calibration(user_id: str = "demo"):
    """Reset personal baseline (requires recalibration)."""
    with Session(engine) as session:
        success = reset_baseline(user_id, session)
        return {"status": "reset" if success else "not_found"}


# --- WebSocket Endpoint ---

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Real-time WebSocket connection for score updates."""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive — client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


# --- Health Check ---

@app.get("/health")
def health():
    return {
        "status": "ok",
        "connections": manager.connection_count,
    }
