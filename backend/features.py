"""
Feature extraction from raw event windows.
Computes rolling aggregations and z-score normalization against personal baselines.
"""

import numpy as np
from typing import Optional


# Metric keys that get extracted from raw event windows
METRIC_KEYS = [
    "mouse_speed_mean", "mouse_jitter", "clicks",
    "wpm_estimate", "backspace_rate", "key_pause_count",
    "scroll_depth_pct", "scroll_backtracks",
    "idle_sec", "task_switches", "hour_of_day"
]


def compute_baseline_stats(events: list[dict]) -> dict:
    """
    Compute mean and std for each metric from a list of event windows.
    Used to build personal baselines.
    """
    if not events:
        return {}

    stats = {}
    for key in METRIC_KEYS:
        values = [e.get(key, 0) for e in events]
        stats[key] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)) if len(values) > 1 else 1.0,
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }
    return stats


def z_score(value: float, mean: float, std: float) -> float:
    """Compute z-score, clamped to [-2, 2] (was ±3) to dampen outlier spikes."""
    if std == 0 or std < 0.001:
        return 0.0
    z = (value - mean) / std
    return max(-2.0, min(2.0, z))


def extract_features(event: dict, baseline: Optional[dict] = None) -> dict:
    """
    Extract ML-ready features from a single event window.
    If baseline is provided, features are z-score normalized.

    Returns a feature vector dict.
    """
    features = {}

    # Raw metrics
    mouse_speed = event.get("mouse_speed_mean", 0)
    mouse_jitter = event.get("mouse_jitter", 0)
    clicks = event.get("clicks", 0)
    wpm = event.get("wpm_estimate", 0)
    backspace_rate = event.get("backspace_rate", 0)
    key_pauses = event.get("key_pause_count", 0)
    scroll_depth = event.get("scroll_depth_pct", 0)
    scroll_backtracks = event.get("scroll_backtracks", 0)
    idle_sec = event.get("idle_sec", 0)
    task_switches = event.get("task_switches", 0)
    hour = event.get("hour_of_day", 12)
    window_sec = event.get("window_sec", 30)

    # Derived features
    idle_ratio = idle_sec / max(window_sec, 1)
    late_hour_flag = 1.0 if hour >= 21 else 0.0
    active_minutes = max((window_sec - idle_sec) / 60, 0.01)
    task_switch_rate = task_switches / active_minutes

    if baseline and len(baseline) > 0:
        # Z-score normalized features
        features["mouse_jitter_zscore"] = z_score(
            mouse_jitter,
            baseline.get("mouse_jitter", {}).get("mean", 0),
            baseline.get("mouse_jitter", {}).get("std", 1)
        )
        features["wpm_zscore"] = z_score(
            wpm,
            baseline.get("wpm_estimate", {}).get("mean", 0),
            baseline.get("wpm_estimate", {}).get("std", 1)
        )
        features["backspace_zscore"] = z_score(
            backspace_rate,
            baseline.get("backspace_rate", {}).get("mean", 0),
            baseline.get("backspace_rate", {}).get("std", 1)
        )
        features["mouse_speed_zscore"] = z_score(
            mouse_speed,
            baseline.get("mouse_speed_mean", {}).get("mean", 0),
            baseline.get("mouse_speed_mean", {}).get("std", 1)
        )
        features["idle_zscore"] = z_score(
            idle_sec,
            baseline.get("idle_sec", {}).get("mean", 0),
            baseline.get("idle_sec", {}).get("std", 1)
        )
    else:
        # Raw normalized features (no baseline yet).
        # Treat zero/low activity as NEUTRAL (0.0), not as burnout.
        # Only flag deviations that are clearly anomalous.

        # Mouse jitter: only flag if unusually jerky (>45°)
        features["mouse_jitter_zscore"] = min(max(mouse_jitter - 20.0, 0.0) / 50.0, 2.0)

        # WPM: only penalize if user was actively typing but very slowly.
        # If wpm==0 (user idle/not typing), treat as neutral (0), not burnout.
        if wpm == 0:
            features["wpm_zscore"] = 0.0
        else:
            features["wpm_zscore"] = max(1.0 - (wpm / 40.0), -1.0)

        # Backspace rate: only flag above 20%
        features["backspace_zscore"] = min(max(backspace_rate - 0.10, 0.0) / 0.20, 2.0)

        # Mouse speed: neutral unless extremely slow while moving
        features["mouse_speed_zscore"] = min(mouse_speed / 1000.0, 2.0)

        # Idle: only flag if nearly completely idle (>85% of window)
        features["idle_zscore"] = min(max(idle_ratio - 0.85, 0.0) * 10.0, 2.0)

    features["idle_ratio"] = idle_ratio
    features["late_hour_flag"] = late_hour_flag
    features["task_switch_rate"] = task_switch_rate
    features["scroll_backtracks"] = float(scroll_backtracks)
    features["clicks"] = float(clicks)
    features["scroll_depth_pct"] = scroll_depth

    return features
