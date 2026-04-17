"""
BurnoutRadar — Real-Time Data Collection Agent
Captures actual mouse and keyboard behavioural metrics using OS-level hooks.
Privacy-first: NO keystroke content is recorded — only counts and timing.
"""

import argparse
import json
import math
import threading
import time
import sys

from pynput import mouse, keyboard

try:
    import requests
    HTTP_LIB = "requests"
except ImportError:
    import httpx
    HTTP_LIB = "httpx"


# ─────────────────────────────────────────────
#  Metric Accumulator (thread-safe)
# ─────────────────────────────────────────────

class MetricAccumulator:
    """
    Collects raw input events and computes aggregate metrics
    for each reporting window.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        """Zero-out all counters for a new window."""
        self._window_start = time.time()

        # Mouse
        self._mouse_positions: list[tuple[float, float]] = []
        self._mouse_distances: list[float] = []
        self._mouse_angles: list[float] = []
        self._last_mouse_pos: tuple[float, float] | None = None
        self._prev_angle: float | None = None
        self._click_count = 0

        # Keyboard
        self._key_count = 0          # alphanumeric keys only
        self._backspace_count = 0
        self._total_key_count = 0    # all keys (for backspace rate denominator)
        self._key_timestamps: list[float] = []
        self._pause_count = 0        # pauses > PAUSE_THRESHOLD seconds
        self._last_key_time: float | None = None

        # Activity tracking (for idle computation)
        self._last_activity_time = time.time()

        # Scroll
        self._scroll_total = 0
        self._scroll_direction_changes = 0
        self._last_scroll_dir: int | None = None

        # Task switches (approximated by rapid alt-tab detection)
        self._task_switch_count = 0
        self._alt_held = False

    # ── Mouse callbacks ──────────────────────

    def on_mouse_move(self, x: int, y: int):
        with self._lock:
            now = time.time()
            self._last_activity_time = now

            current = (float(x), float(y))
            if self._last_mouse_pos is not None:
                dx = current[0] - self._last_mouse_pos[0]
                dy = current[1] - self._last_mouse_pos[1]
                dist = math.hypot(dx, dy)
                self._mouse_distances.append(dist)

                # Direction angle for jitter computation
                if dist > 0.5:  # ignore micro-movements
                    angle = math.atan2(dy, dx)
                    if self._prev_angle is not None:
                        delta_angle = abs(angle - self._prev_angle)
                        if delta_angle > math.pi:
                            delta_angle = 2 * math.pi - delta_angle
                        self._mouse_angles.append(delta_angle)
                    self._prev_angle = angle

            self._last_mouse_pos = current

    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            with self._lock:
                self._click_count += 1
                self._last_activity_time = time.time()

    def on_mouse_scroll(self, x, y, dx, dy):
        with self._lock:
            self._last_activity_time = time.time()
            self._scroll_total += abs(dy)

            current_dir = 1 if dy > 0 else -1
            if self._last_scroll_dir is not None and current_dir != self._last_scroll_dir:
                self._scroll_direction_changes += 1
            self._last_scroll_dir = current_dir

    # ── Keyboard callbacks ───────────────────

    PAUSE_THRESHOLD = 2.0  # seconds of silence between keys → counts as a pause

    def on_key_press(self, key):
        with self._lock:
            now = time.time()
            self._last_activity_time = now
            self._total_key_count += 1

            # Detect alt-tab as a task switch proxy
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                self._alt_held = True
            if self._alt_held and key == keyboard.Key.tab:
                self._task_switch_count += 1

            # Pause detection
            if self._last_key_time is not None:
                gap = now - self._last_key_time
                if gap >= self.PAUSE_THRESHOLD:
                    self._pause_count += 1
            self._last_key_time = now

            # Categorize key
            try:
                if hasattr(key, 'char') and key.char is not None:
                    self._key_count += 1
                    self._key_timestamps.append(now)
            except AttributeError:
                pass

            if key == keyboard.Key.backspace or key == keyboard.Key.delete:
                self._backspace_count += 1

    def on_key_release(self, key):
        with self._lock:
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                self._alt_held = False

    # ── Aggregation ──────────────────────────

    def harvest(self, window_sec: float, baseline: dict | None = None) -> dict:
        """
        Snapshot and reset all metrics.
        Returns a payload dict matching the backend /ingest schema.
        If a baseline dict is provided, continuous metrics are normalized
        relative to the user's personal calibration window.
        """
        with self._lock:
            now = time.time()
            elapsed = now - self._window_start

            # ---------- Mouse speed (px/s) ----------
            total_dist = sum(self._mouse_distances) if self._mouse_distances else 0
            mouse_speed = total_dist / elapsed if elapsed > 0 else 0

            # ---------- Mouse jitter (mean angular change in degrees) ----------
            if self._mouse_angles:
                jitter = math.degrees(
                    sum(self._mouse_angles) / len(self._mouse_angles)
                )
            else:
                jitter = 0

            # ---------- Clicks ----------
            clicks = self._click_count

            # ---------- WPM estimate ----------
            minutes = elapsed / 60.0
            chars = self._key_count
            words = chars / 5.0  # standard WPM convention: 5 chars = 1 word
            wpm = words / minutes if minutes > 0 else 0

            # ---------- Backspace rate ----------
            if self._total_key_count > 0:
                backspace_rate = self._backspace_count / self._total_key_count
            else:
                backspace_rate = 0

            # ---------- Key pauses ----------
            pause_count = self._pause_count

            # ---------- Scroll depth (proxy via total scroll units) ----------
            # Normalize: 100 scroll units ≈ 100% depth
            scroll_depth = min(self._scroll_total / 100.0, 1.0)

            # ---------- Scroll backtracks ----------
            scroll_backtracks = self._scroll_direction_changes

            # ---------- Idle seconds ----------
            idle_sec = now - self._last_activity_time

            # ---------- Task switches ----------
            task_switches = self._task_switch_count

            # ---------- Hour of day ----------
            hour = time.localtime().tm_hour

            # ---------- Apply personal baseline normalization ----------
            # If a baseline exists, scale continuous metrics so they represent
            # deviation from YOUR normal rather than an absolute value.
            # Values stay in the same range — we clamp to avoid negatives.
            if baseline:
                def _norm(val, base_val, floor=0.0):
                    """Shift val by how much it deviates from baseline."""
                    if base_val and base_val > 0:
                        ratio = val / base_val  # 1.0 = same as calibration
                        return max(floor, val * ratio)
                    return val

                mouse_speed  = _norm(mouse_speed, baseline.get("mouse_speed_mean", 0))
                jitter       = _norm(jitter,      baseline.get("mouse_jitter", 0))
                wpm          = _norm(wpm,         baseline.get("wpm_estimate", 0))

            payload = {
                "ts": now,
                "window_sec": round(window_sec, 1),
                "mouse_speed_mean": round(mouse_speed, 1),
                "mouse_jitter": round(jitter, 1),
                "clicks": clicks,
                "wpm_estimate": round(wpm, 1),
                "backspace_rate": round(backspace_rate, 3),
                "key_pause_count": pause_count,
                "scroll_depth_pct": round(scroll_depth, 2),
                "scroll_backtracks": scroll_backtracks,
                "idle_sec": round(idle_sec, 1),
                "task_switches": task_switches,
                "hour_of_day": hour,
            }

            # Reset for next window
            self.reset()

            return payload


# ─────────────────────────────────────────────
#  HTTP Sender
# ─────────────────────────────────────────────

def send_payload(payload: dict, base_url: str) -> dict | None:
    """POST the event payload to the backend /ingest endpoint."""
    url = f"{base_url}/ingest"
    try:
        if HTTP_LIB == "requests":
            resp = requests.post(url, json=payload, timeout=5)
            resp.raise_for_status()
            return resp.json()
        else:
            resp = httpx.post(url, json=payload, timeout=5)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
#  Main Tracker Loop
# ─────────────────────────────────────────────

def run_tracker(
    user_id: str = "demo",
    interval: int = 5,
    base_url: str = "http://10.182.193.110:8000",
    calibration_sec: int = 7,
):
    acc = MetricAccumulator()

    # --- Start listeners ---
    mouse_listener = mouse.Listener(
        on_move=acc.on_mouse_move,
        on_click=acc.on_mouse_click,
        on_scroll=acc.on_mouse_scroll,
    )
    key_listener = keyboard.Listener(
        on_press=acc.on_key_press,
        on_release=acc.on_key_release,
    )

    mouse_listener.daemon = True
    key_listener.daemon = True
    mouse_listener.start()
    key_listener.start()

    print("═" * 60)
    print("  🔥  BurnoutRadar — Real-Time Tracker")
    print("═" * 60)
    print(f"  User       : {user_id}")
    print(f"  Interval   : {interval}s")
    print(f"  Backend    : {base_url}")
    print(f"  Privacy    : Keystroke CONTENT is NOT recorded")
    print("─" * 60)

    # ── Calibration phase ────────────────────────────────────────
    # Collect data silently for `calibration_sec` seconds.
    # Nothing is sent to the backend during this window.
    # The result becomes YOUR personal baseline for this session.
    baseline: dict | None = None

    if calibration_sec > 0:
        print(f"  ⏳  Calibration ({calibration_sec}s) — use your computer normally...")
        cal_start = time.time()
        while True:
            remaining = calibration_sec - int(time.time() - cal_start)
            print(f"\r  ⏳  Calibrating... {remaining}s remaining   ", end="", flush=True)
            if time.time() - cal_start >= calibration_sec:
                break
            time.sleep(0.5)

        baseline = acc.harvest(window_sec=calibration_sec)
        print(f"\r  ✅  Calibration done!                              ")
        print(f"      Baseline → WPM: {baseline['wpm_estimate']:.1f}  "
              f"│  Mouse speed: {baseline['mouse_speed_mean']:.1f} px/s  "
              f"│  Jitter: {baseline['mouse_jitter']:.1f}°")
        print("─" * 60)

    print("  Tracking started. Press Ctrl+C to stop.\n")

    event_count = 0

    try:
        while True:
            time.sleep(interval)

            payload = acc.harvest(window_sec=interval, baseline=baseline)
            payload["user_id"] = user_id
            event_count += 1

            result = send_payload(payload, base_url)

            if result and "error" not in result:
                score = result.get("score", "?")
                severity = result.get("severity", "?")
                bar_len = int(float(score) / 2) if isinstance(score, (int, float)) else 0
                bar = "█" * bar_len + "░" * (50 - bar_len)
                print(
                    f"  [{event_count:4d}]  Score: {score:>5}  │  {severity:<10}  │  "
                    f"[{bar}]  │  WPM: {payload['wpm_estimate']:>5.1f}  "
                    f"│  Jitter: {payload['mouse_jitter']:>5.1f}"
                )
            else:
                err = result.get("error", "Unknown") if result else "No response"
                print(f"  [{event_count:4d}]  ⚠ Error: {err}")

    except KeyboardInterrupt:
        print("\n\n  Tracker stopped by user.")
    finally:
        mouse_listener.stop()
        key_listener.stop()
        print(f"  Total events sent: {event_count}")
        print("═" * 60)


# ─────────────────────────────────────────────
#  CLI Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="BurnoutRadar Real-Time Tracker — collects live behavioural metrics"
    )
    parser.add_argument(
        "--user", default="demo",
        help="User ID sent with each payload (default: demo)"
    )
    parser.add_argument(
        "--interval", type=int, default=5,
        help="Seconds between reports to the backend (default: 5)"
    )
    parser.add_argument(
        "--url", default="http://10.182.193.110:8000",
        help="Backend base URL (default: http://10.182.193.110:8000)"
    )
    parser.add_argument(
        "--calibration", type=int, default=7,
        help="Calibration window in seconds before tracking begins (default: 7, set 0 to skip)"
    )

    args = parser.parse_args()
    run_tracker(
        user_id=args.user,
        interval=args.interval,
        base_url=args.url,
        calibration_sec=args.calibration,
    )
