"""
SQLite database layer using SQLModel.
Stores raw event windows and computed burnout scores.
"""

from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional
from datetime import datetime
import json


# --- Models ---

class EventWindow(SQLModel, table=True):
    """Raw 30-second behavioural event window from the agent."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    timestamp: float  # Unix epoch
    window_sec: int = 30
    mouse_speed_mean: float = 0.0
    mouse_jitter: float = 0.0
    clicks: int = 0
    wpm_estimate: float = 0.0
    backspace_rate: float = 0.0
    key_pause_count: int = 0
    scroll_depth_pct: float = 0.0
    scroll_backtracks: int = 0
    idle_sec: float = 0.0
    task_switches: int = 0
    hour_of_day: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BurnoutScore(SQLModel, table=True):
    """Computed burnout score for a user at a point in time."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    timestamp: float
    score: float
    severity: str  # low, moderate, high, critical
    factors: str = "{}"  # JSON string of top contributing factors
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class UserBaseline(SQLModel, table=True):
    """Personal baseline statistics for calibration."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(unique=True, index=True)
    sample_count: int = 0
    baseline_data: str = "{}"  # JSON: {metric: {mean, std, min, max}}
    calibration_ready: bool = False
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# --- Engine ---

DATABASE_URL = "sqlite:///./burnout_radar.db"
engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """Create all tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield a database session."""
    with Session(engine) as session:
        yield session
