"""
Personal baseline calibration.
Collects initial data to establish per-user norms, then uses deviations for scoring.
"""

import json
from sqlmodel import Session, select
from database import UserBaseline, EventWindow, engine
from features import compute_baseline_stats, METRIC_KEYS

# Number of event windows required before calibration is considered ready
# Lowered from 50 → 20 so personal baseline activates after ~10 min instead of 25 min.
# Baseline z-score scoring is far more accurate and stable than cold-start heuristics.
CALIBRATION_THRESHOLD = 20


def get_or_create_baseline(user_id: str, session: Session) -> UserBaseline:
    """Get existing baseline or create a new one."""
    statement = select(UserBaseline).where(UserBaseline.user_id == user_id)
    baseline = session.exec(statement).first()

    if not baseline:
        baseline = UserBaseline(user_id=user_id)
        session.add(baseline)
        session.commit()
        session.refresh(baseline)

    return baseline


def update_baseline(user_id: str, session: Session) -> dict:
    """
    Recalculate baseline from all stored events for this user.
    Returns the baseline data dict.
    """
    # Fetch all events for this user
    statement = select(EventWindow).where(EventWindow.user_id == user_id)
    events = session.exec(statement).all()

    event_dicts = [
        {key: getattr(e, key, 0) for key in METRIC_KEYS}
        for e in events
    ]

    stats = compute_baseline_stats(event_dicts)
    sample_count = len(event_dicts)
    calibration_ready = sample_count >= CALIBRATION_THRESHOLD

    # Update or create baseline record
    baseline = get_or_create_baseline(user_id, session)
    baseline.sample_count = sample_count
    baseline.baseline_data = json.dumps(stats)
    baseline.calibration_ready = calibration_ready

    session.add(baseline)
    session.commit()

    return {
        "user_id": user_id,
        "sample_count": sample_count,
        "calibration_ready": calibration_ready,
        "stats": stats,
    }


def get_baseline_data(user_id: str, session: Session) -> dict | None:
    """Get parsed baseline data for feature extraction."""
    baseline = get_or_create_baseline(user_id, session)

    if not baseline.calibration_ready:
        return None

    return json.loads(baseline.baseline_data)


def reset_baseline(user_id: str, session: Session) -> bool:
    """Reset a user's baseline (requires recalibration)."""
    statement = select(UserBaseline).where(UserBaseline.user_id == user_id)
    baseline = session.exec(statement).first()

    if baseline:
        baseline.sample_count = 0
        baseline.baseline_data = "{}"
        baseline.calibration_ready = False
        session.add(baseline)
        session.commit()
        return True

    return False
