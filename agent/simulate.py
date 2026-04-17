"""
BurnoutRadar — Event Simulator
Generates realistic synthetic behavioural data for testing the pipeline.
Supports different scenarios: normal, fatigue, burnout, crisis.
"""

import argparse
import asyncio
import json
import random
import time
import math

try:
    import httpx
    HTTP_CLIENT = "httpx"
except ImportError:
    import urllib.request
    HTTP_CLIENT = "urllib"


# --- Scenario Profiles ---

SCENARIOS = {
    "normal": {
        "description": "Normal productive work session",
        "mouse_speed": (180, 300),
        "mouse_jitter": (5, 15),
        "clicks": (8, 20),
        "wpm": (55, 75),
        "backspace_rate": (0.02, 0.06),
        "key_pauses": (0, 2),
        "scroll_depth": (0.2, 0.6),
        "scroll_backtracks": (0, 3),
        "idle_sec": (1, 5),
        "task_switches": (0, 2),
        "score_range": "15-30",
    },
    "fatigue": {
        "description": "Mild fatigue — slowing down",
        "mouse_speed": (120, 220),
        "mouse_jitter": (12, 25),
        "clicks": (5, 12),
        "wpm": (35, 55),
        "backspace_rate": (0.06, 0.12),
        "key_pauses": (2, 5),
        "scroll_depth": (0.1, 0.4),
        "scroll_backtracks": (3, 8),
        "idle_sec": (5, 12),
        "task_switches": (2, 5),
        "score_range": "40-55",
    },
    "burnout": {
        "description": "High burnout — erratic behaviour",
        "mouse_speed": (80, 180),
        "mouse_jitter": (20, 45),
        "clicks": (2, 8),
        "wpm": (20, 40),
        "backspace_rate": (0.10, 0.20),
        "key_pauses": (4, 8),
        "scroll_depth": (0.05, 0.25),
        "scroll_backtracks": (5, 15),
        "idle_sec": (8, 20),
        "task_switches": (4, 8),
        "score_range": "65-85",
    },
    "crisis": {
        "description": "Crisis — near-zero productivity",
        "mouse_speed": (30, 100),
        "mouse_jitter": (35, 60),
        "clicks": (0, 4),
        "wpm": (5, 20),
        "backspace_rate": (0.15, 0.30),
        "key_pauses": (6, 12),
        "scroll_depth": (0.0, 0.1),
        "scroll_backtracks": (8, 20),
        "idle_sec": (15, 28),
        "task_switches": (5, 10),
        "score_range": "85-100",
    },
    "ramp": {
        "description": "Gradual burnout ramp (normal -> crisis)",
        "dynamic": True,
    },
}


def generate_event(profile: dict, user_id: str, hour: int = None) -> dict:
    """Generate a single event window from a scenario profile."""
    if hour is None:
        hour = time.localtime().tm_hour

    def _rint(tup):
        """Safe randint from a possibly-float tuple."""
        return random.randint(int(tup[0]), int(tup[1]))

    return {
        "user_id": user_id,
        "ts": time.time(),
        "window_sec": 30,
        "mouse_speed_mean": round(random.uniform(*profile["mouse_speed"]), 1),
        "mouse_jitter": round(random.uniform(*profile["mouse_jitter"]), 1),
        "clicks": _rint(profile["clicks"]),
        "wpm_estimate": round(random.uniform(*profile["wpm"]), 1),
        "backspace_rate": round(random.uniform(*profile["backspace_rate"]), 3),
        "key_pause_count": _rint(profile["key_pauses"]),
        "scroll_depth_pct": round(random.uniform(*profile["scroll_depth"]), 2),
        "scroll_backtracks": _rint(profile["scroll_backtracks"]),
        "idle_sec": round(random.uniform(*profile["idle_sec"]), 1),
        "task_switches": _rint(profile["task_switches"]),
        "hour_of_day": hour,
    }


def interpolate_profiles(profile_a: dict, profile_b: dict, t: float) -> dict:
    """Linearly interpolate between two profiles (t=0 is A, t=1 is B)."""
    result = {}
    for key in profile_a:
        if key in ("description", "score_range", "dynamic"):
            continue
        a_low, a_high = profile_a[key]
        b_low, b_high = profile_b[key]
        result[key] = (
            a_low + (b_low - a_low) * t,
            a_high + (b_high - a_high) * t,
        )
    return result


def send_event_sync(event: dict, base_url: str):
    """Send event to the backend using available HTTP client."""
    url = f"{base_url}/ingest"
    data = json.dumps(event).encode("utf-8")

    if HTTP_CLIENT == "httpx":
        import httpx
        response = httpx.post(url, json=event, timeout=5.0)
        return response.json()
    else:
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())


def run_simulation(
    user_id: str = "demo",
    scenario: str = "normal",
    duration: int = 300,
    interval: int = 3,
    base_url: str = "http://localhost:8000",
    hour: int = None,
):
    """Run a simulation sending events at the given interval."""
    print(f"\n--- BurnoutRadar Simulator ---")
    print(f"User:     {user_id}")
    print(f"Scenario: {scenario}")
    print(f"Duration: {duration}s")
    print(f"Interval: {interval}s")
    print(f"Backend:  {base_url}")
    print(f"---\n")

    profile_data = SCENARIOS[scenario]
    is_ramp = profile_data.get("dynamic", False)

    start_time = time.time()
    event_count = 0

    try:
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            progress = elapsed / duration

            if is_ramp:
                # Ramp from normal -> crisis
                if progress < 0.3:
                    t = progress / 0.3
                    profile = interpolate_profiles(
                        SCENARIOS["normal"], SCENARIOS["fatigue"], t
                    )
                elif progress < 0.6:
                    t = (progress - 0.3) / 0.3
                    profile = interpolate_profiles(
                        SCENARIOS["fatigue"], SCENARIOS["burnout"], t
                    )
                else:
                    t = (progress - 0.6) / 0.4
                    profile = interpolate_profiles(
                        SCENARIOS["burnout"], SCENARIOS["crisis"], t
                    )
            else:
                profile = profile_data

            event = generate_event(profile, user_id, hour)
            event_count += 1

            try:
                result = send_event_sync(event, base_url)
                score = result.get("score", "?")
                severity = result.get("severity", "?")
                bar_len = int(float(score) / 2) if isinstance(score, (int, float)) else 0
                bar = "#" * bar_len + "-" * (50 - bar_len)
                print(
                    f"[{event_count:4d}] Score: {score:>5} | {severity:<10} | [{bar}] | "
                    f"WPM: {event['wpm_estimate']:>5.1f} | Jitter: {event['mouse_jitter']:>5.1f}"
                )
            except Exception as e:
                print(f"[{event_count:4d}] Error sending event: {e}")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nSimulation stopped by user.")

    elapsed = time.time() - start_time
    print(f"\n--- Done: {event_count} events sent in {elapsed:.0f}s ---\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BurnoutRadar Event Simulator")
    parser.add_argument("--user", default="demo", help="User ID (default: demo)")
    parser.add_argument(
        "--scenario",
        default="ramp",
        choices=list(SCENARIOS.keys()),
        help="Simulation scenario (default: ramp)",
    )
    parser.add_argument(
        "--duration", type=int, default=300, help="Duration in seconds (default: 300)"
    )
    parser.add_argument(
        "--interval", type=int, default=3, help="Seconds between events (default: 3)"
    )
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Backend base URL"
    )
    parser.add_argument(
        "--hour", type=int, default=None, help="Override hour of day (0-23)"
    )

    args = parser.parse_args()
    run_simulation(
        user_id=args.user,
        scenario=args.scenario,
        duration=args.duration,
        interval=args.interval,
        base_url=args.url,
        hour=args.hour,
    )
