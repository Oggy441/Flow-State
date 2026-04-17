"""
ML Burnout Scoring Engine.
Uses a heuristic-weighted model for hackathon (no pre-trained model needed).
Designed to be swappable with a real sklearn/xgboost model later.
"""

import numpy as np
from typing import Tuple


# ─────────────────────────────────────────────
#  Score Smoother (per-user EMA)
# ─────────────────────────────────────────────

class ScoreSmoother:
    """
    Exponential Moving Average smoother.
    alpha=0.3 means the new raw score contributes 30% and the running
    average contributes 70% — keeps the gauge from jumping on every tick.
    Increase alpha (max 1.0) to make it more reactive.
    """
    ALPHA = 0.25  # smoothing factor — lower = less sensitive, higher = more reactive

    def __init__(self):
        self._scores: dict[str, float] = {}  # user_id -> last smoothed score

    def smooth(self, user_id: str, raw_score: float) -> float:
        if user_id not in self._scores:
            self._scores[user_id] = raw_score  # first sample: no smoothing
        else:
            self._scores[user_id] = (
                self.ALPHA * raw_score
                + (1 - self.ALPHA) * self._scores[user_id]
            )
        return self._scores[user_id]

    def reset(self, user_id: str):
        self._scores.pop(user_id, None)


# Singleton — shared across all requests
smoother = ScoreSmoother()


# Feature weights for burnout scoring (heuristic model)
# Positive weight = contributes to burnout
# Weights reduced ~40% across the board so normal activity variations
# don't meaningfully shift the burnout score.
FEATURE_WEIGHTS = {
    "mouse_jitter_zscore": 8.0,      # High jitter = stress/fatigue
    "wpm_zscore": 7.0,               # Negative WPM deviation = fatigue
    "backspace_zscore": 8.0,         # High error rate = mental fatigue
    "idle_ratio": 2.0,               # High idle = disengagement (reduced — idle alone ≠ burnout)
    "idle_zscore": 3.0,              # Unusual idle pattern = break in rhythm
    "late_hour_flag": 6.0,           # Working late = burnout risk
    "task_switch_rate": 5.0,         # Frequent switching = fragmentation
    "scroll_backtracks": 3.0,        # Re-reading = comprehension drop
    "mouse_speed_zscore": 3.0,       # Erratic speed = stress
    "clicks": -2.0,                  # More clicks = engagement (reduces score)
    "scroll_depth_pct": -3.0,        # Deep scroll = engagement (reduces score)
}


def classify_severity(score: float) -> str:
    """Map a 0-100 score to severity band."""
    if score <= 40:
        return "low"
    elif score <= 62:
        return "moderate"
    elif score <= 80:
        return "high"
    else:
        return "critical"


def get_severity_color(severity: str) -> str:
    """Return hex colour for severity band."""
    return {
        "low": "#4ade80",
        "moderate": "#facc15",
        "high": "#f97316",
        "critical": "#ef4444",
    }.get(severity, "#9ca3af")


def get_top_factors(features: dict, n: int = 3) -> list[dict]:
    """
    Identify top N factors contributing to the burnout score.
    Returns list of {factor, value, contribution, message}.
    """
    contributions = []
    for key, weight in FEATURE_WEIGHTS.items():
        if key in features:
            val = features[key]
            contrib = val * weight
            if contrib > 0:  # Only factors that increase burnout
                contributions.append({
                    "factor": key,
                    "value": round(val, 2),
                    "contribution": round(contrib, 1),
                    "message": _factor_message(key, val),
                })

    contributions.sort(key=lambda x: x["contribution"], reverse=True)
    return contributions[:n]


def _factor_message(factor: str, value: float) -> str:
    """Human-readable explanation for each factor."""
    messages = {
        "mouse_jitter_zscore": "Mouse movement is more erratic than usual",
        "wpm_zscore": "Typing speed has dropped significantly",
        "backspace_zscore": "Error/correction rate is elevated",
        "idle_ratio": "Extended periods of inactivity detected",
        "idle_zscore": "Idle pattern is unusual compared to baseline",
        "late_hour_flag": "Working during late hours",
        "task_switch_rate": "Frequent context switching detected",
        "scroll_backtracks": "Re-reading content more than usual",
        "mouse_speed_zscore": "Mouse speed patterns are irregular",
    }
    return messages.get(factor, f"{factor} is elevated")


def predict_score(features: dict, user_id: str = "demo") -> dict:
    """
    Predict burnout score from feature vector.

    Uses weighted heuristic model. Score is 0-100.
    Applies per-user EMA smoothing so the displayed score drifts
    gradually rather than jumping on every payload.
    Returns {score, severity, color, factors}.
    """
    raw_score = 0.0

    for key, weight in FEATURE_WEIGHTS.items():
        value = features.get(key, 0.0)
        raw_score += value * weight

    # Shift center to 30 so an idle/neutral signal lands around 20-25,
    # and genuine stress signals push it up into moderate/high territory.
    score = 100.0 / (1.0 + np.exp(-0.04 * (raw_score - 30)))
    score = max(0.0, min(100.0, score))

    # Apply per-user EMA smoothing
    score = smoother.smooth(user_id, score)

    severity = classify_severity(score)
    factors = get_top_factors(features)

    return {
        "score": round(float(score), 1),
        "severity": severity,
        "color": get_severity_color(severity),
        "factors": factors,
    }
