"""
BurnoutRadar — Tkinter Data-Collection Control Panel
A rich dark-themed GUI that wraps the real-time tracker with
Start / Stop / Pause controls and a live log console.

Usage:
    python tracker_gui.py
"""

import math
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime

# Import tracker internals
from real_tracker import MetricAccumulator, send_payload

try:
    from pynput import mouse, keyboard
except ImportError:
    messagebox.showerror("Missing dependency", "Install pynput:  pip install pynput")
    raise


# ─────────────────────────────────────────────
#  Color Palette — Dark Theme
# ─────────────────────────────────────────────

COLORS = {
    "bg_dark":       "#0f0f14",
    "bg_panel":      "#16161d",
    "bg_card":       "#1e1e28",
    "bg_input":      "#252530",
    "border":        "#2a2a3a",
    "text":          "#e4e4ef",
    "text_dim":      "#8888a0",
    "accent":        "#7c6aef",
    "accent_hover":  "#9484f7",
    "green":         "#4ade80",
    "green_dim":     "#1a3a25",
    "yellow":        "#facc15",
    "yellow_dim":    "#3a3518",
    "red":           "#f87171",
    "red_dim":       "#3a1a1a",
    "orange":        "#fb923c",
    "cyan":          "#22d3ee",
    "stop_btn":      "#e53e3e",
    "pause_btn":     "#d69e2e",
}


# ─────────────────────────────────────────────
#  Application
# ─────────────────────────────────────────────

class TrackerGUI:
    """Main application window."""

    # States
    STATE_IDLE        = "idle"
    STATE_CALIBRATING = "calibrating"
    STATE_RUNNING     = "running"
    STATE_PAUSED      = "paused"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BurnoutRadar — Data Collection")
        self.root.configure(bg=COLORS["bg_dark"])
        self.root.minsize(900, 640)
        self.root.geometry("960x720")

        # Internal state
        self.state = self.STATE_IDLE
        self.accumulator: MetricAccumulator | None = None
        self.mouse_listener = None
        self.key_listener = None
        self.tracker_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()   # set = paused
        self.event_count = 0
        self.error_count = 0
        self.session_start: float | None = None
        self.baseline: dict | None = None
        self.last_score: float | None = None
        self.last_severity: str = ""

        self._build_ui()
        self._apply_theme()
        self._update_clock()

    # ─── UI Construction ──────────────────────

    def _build_ui(self):
        # ── Top bar ──────────────────────────
        top = tk.Frame(self.root, bg=COLORS["bg_panel"], height=56)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)

        title_lbl = tk.Label(
            top, text="🔥  BurnoutRadar", font=("Segoe UI Semibold", 16),
            fg=COLORS["accent"], bg=COLORS["bg_panel"],
        )
        title_lbl.pack(side="left", padx=16)

        self.clock_lbl = tk.Label(
            top, text="", font=("Consolas", 11),
            fg=COLORS["text_dim"], bg=COLORS["bg_panel"],
        )
        self.clock_lbl.pack(side="right", padx=16)

        self.status_lbl = tk.Label(
            top, text="● IDLE", font=("Segoe UI Semibold", 11),
            fg=COLORS["text_dim"], bg=COLORS["bg_panel"],
        )
        self.status_lbl.pack(side="right", padx=8)

        # ── Separator ───────────────────────
        sep = tk.Frame(self.root, bg=COLORS["border"], height=1)
        sep.pack(fill="x")

        # ── Main body (left: controls, right: stats) ──
        body = tk.Frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=0, pady=0)

        # -- Left pane -------
        left = tk.Frame(body, bg=COLORS["bg_dark"], width=300)
        left.pack(side="left", fill="y", padx=(12, 6), pady=12)
        left.pack_propagate(False)

        self._build_config_card(left)
        self._build_control_card(left)
        self._build_stats_card(left)

        # -- Right pane (log) --
        right = tk.Frame(body, bg=COLORS["bg_dark"])
        right.pack(side="left", fill="both", expand=True, padx=(6, 12), pady=12)

        self._build_log_card(right)

    # ── Config card ─────────────────────────

    def _build_config_card(self, parent):
        card = self._card(parent, "⚙  Configuration")

        row1 = tk.Frame(card, bg=COLORS["bg_card"])
        row1.pack(fill="x", pady=(0, 6))
        tk.Label(row1, text="User ID", width=12, anchor="w",
                 font=("Segoe UI", 10), fg=COLORS["text_dim"],
                 bg=COLORS["bg_card"]).pack(side="left")
        self.user_var = tk.StringVar(value="demo")
        tk.Entry(row1, textvariable=self.user_var, width=18,
                 bg=COLORS["bg_input"], fg=COLORS["text"],
                 insertbackground=COLORS["text"],
                 relief="flat", font=("Consolas", 10),
                 highlightthickness=1,
                 highlightcolor=COLORS["accent"],
                 highlightbackground=COLORS["border"]).pack(side="left", fill="x", expand=True)

        row2 = tk.Frame(card, bg=COLORS["bg_card"])
        row2.pack(fill="x", pady=(0, 6))
        tk.Label(row2, text="Interval (s)", width=12, anchor="w",
                 font=("Segoe UI", 10), fg=COLORS["text_dim"],
                 bg=COLORS["bg_card"]).pack(side="left")
        self.interval_var = tk.IntVar(value=5)
        tk.Spinbox(row2, from_=1, to=120, textvariable=self.interval_var,
                   width=6, bg=COLORS["bg_input"], fg=COLORS["text"],
                   buttonbackground=COLORS["bg_panel"],
                   relief="flat", font=("Consolas", 10),
                   highlightthickness=1,
                   highlightcolor=COLORS["accent"],
                   highlightbackground=COLORS["border"]).pack(side="left")

        row3 = tk.Frame(card, bg=COLORS["bg_card"])
        row3.pack(fill="x", pady=(0, 6))
        tk.Label(row3, text="Backend URL", width=12, anchor="w",
                 font=("Segoe UI", 10), fg=COLORS["text_dim"],
                 bg=COLORS["bg_card"]).pack(side="left")
        self.url_var = tk.StringVar(value="http://10.182.193.110:8000")
        tk.Entry(row3, textvariable=self.url_var, width=18,
                 bg=COLORS["bg_input"], fg=COLORS["text"],
                 insertbackground=COLORS["text"],
                 relief="flat", font=("Consolas", 10),
                 highlightthickness=1,
                 highlightcolor=COLORS["accent"],
                 highlightbackground=COLORS["border"]).pack(side="left", fill="x", expand=True)

        row4 = tk.Frame(card, bg=COLORS["bg_card"])
        row4.pack(fill="x", pady=(0, 2))
        tk.Label(row4, text="Calibration (s)", width=12, anchor="w",
                 font=("Segoe UI", 10), fg=COLORS["text_dim"],
                 bg=COLORS["bg_card"]).pack(side="left")
        self.cal_var = tk.IntVar(value=7)
        tk.Spinbox(row4, from_=0, to=120, textvariable=self.cal_var,
                   width=6, bg=COLORS["bg_input"], fg=COLORS["text"],
                   buttonbackground=COLORS["bg_panel"],
                   relief="flat", font=("Consolas", 10),
                   highlightthickness=1,
                   highlightcolor=COLORS["accent"],
                   highlightbackground=COLORS["border"]).pack(side="left")

    # ── Control buttons card ────────────────

    def _build_control_card(self, parent):
        card = self._card(parent, "▶  Controls")

        btn_frame = tk.Frame(card, bg=COLORS["bg_card"])
        btn_frame.pack(fill="x")

        self.start_btn = tk.Button(
            btn_frame, text="▶  Start", font=("Segoe UI Semibold", 11),
            bg=COLORS["green"], fg="#000", activebackground=COLORS["green"],
            relief="flat", cursor="hand2", width=8,
            command=self._on_start,
        )
        self.start_btn.pack(side="left", padx=(0, 6), ipady=4)

        self.pause_btn = tk.Button(
            btn_frame, text="⏸  Pause", font=("Segoe UI Semibold", 11),
            bg=COLORS["pause_btn"], fg="#000", activebackground=COLORS["yellow"],
            relief="flat", cursor="hand2", width=8,
            command=self._on_pause, state="disabled",
        )
        self.pause_btn.pack(side="left", padx=(0, 6), ipady=4)

        self.stop_btn = tk.Button(
            btn_frame, text="⏹  Stop", font=("Segoe UI Semibold", 11),
            bg=COLORS["stop_btn"], fg="#fff", activebackground=COLORS["red"],
            relief="flat", cursor="hand2", width=8,
            command=self._on_stop, state="disabled",
        )
        self.stop_btn.pack(side="left", ipady=4)

    # ── Stats card ──────────────────────────

    def _build_stats_card(self, parent):
        card = self._card(parent, "📊  Session Stats")

        self.stat_labels: dict[str, tk.Label] = {}

        stats = [
            ("status",    "Status"),
            ("events",    "Events sent"),
            ("errors",    "Errors"),
            ("elapsed",   "Elapsed"),
            ("score",     "Last Score"),
            ("severity",  "Severity"),
        ]

        for key, label_text in stats:
            row = tk.Frame(card, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label_text, width=12, anchor="w",
                     font=("Segoe UI", 10), fg=COLORS["text_dim"],
                     bg=COLORS["bg_card"]).pack(side="left")
            val_lbl = tk.Label(row, text="—", anchor="w",
                               font=("Consolas", 10, "bold"),
                               fg=COLORS["text"], bg=COLORS["bg_card"])
            val_lbl.pack(side="left")
            self.stat_labels[key] = val_lbl

    # ── Log console card ────────────────────

    def _build_log_card(self, parent):
        card = self._card(parent, "📜  Live Logs", expand=True)

        self.log_text = scrolledtext.ScrolledText(
            card, wrap="word", state="disabled",
            bg=COLORS["bg_dark"], fg=COLORS["text"],
            font=("Consolas", 9), relief="flat",
            insertbackground=COLORS["text"],
            selectbackground=COLORS["accent"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.log_text.pack(fill="both", expand=True, pady=(4, 0))

        # Tag styles
        self.log_text.tag_configure("info",    foreground=COLORS["cyan"])
        self.log_text.tag_configure("success", foreground=COLORS["green"])
        self.log_text.tag_configure("warning", foreground=COLORS["yellow"])
        self.log_text.tag_configure("error",   foreground=COLORS["red"])
        self.log_text.tag_configure("dim",     foreground=COLORS["text_dim"])
        self.log_text.tag_configure("accent",  foreground=COLORS["accent"])

        # Bottom bar: clear + autoscroll
        bottom = tk.Frame(card, bg=COLORS["bg_card"])
        bottom.pack(fill="x", pady=(6, 0))

        self.autoscroll_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            bottom, text="Auto-scroll", variable=self.autoscroll_var,
            font=("Segoe UI", 9), fg=COLORS["text_dim"],
            bg=COLORS["bg_card"], selectcolor=COLORS["bg_input"],
            activebackground=COLORS["bg_card"],
            activeforeground=COLORS["text"],
        ).pack(side="left")

        tk.Button(
            bottom, text="Clear",
            font=("Segoe UI", 9), bg=COLORS["bg_input"],
            fg=COLORS["text_dim"], relief="flat", cursor="hand2",
            command=self._clear_logs,
        ).pack(side="right")

    # ─── Helpers ──────────────────────────────

    def _card(self, parent, title: str, expand=False):
        """Create a styled card frame with a title."""
        outer = tk.Frame(parent, bg=COLORS["border"], bd=0)
        outer.pack(fill="both", expand=expand, pady=(0, 10))

        inner = tk.Frame(outer, bg=COLORS["bg_card"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        tk.Label(inner, text=title, font=("Segoe UI Semibold", 11),
                 fg=COLORS["text"], bg=COLORS["bg_card"],
                 anchor="w").pack(fill="x", padx=10, pady=(10, 6))

        sep = tk.Frame(inner, bg=COLORS["border"], height=1)
        sep.pack(fill="x", padx=10)

        content = tk.Frame(inner, bg=COLORS["bg_card"])
        content.pack(fill="both", expand=True, padx=12, pady=10)

        return content

    def _apply_theme(self):
        """Style ttk widgets via the root option database."""
        self.root.option_add("*TCombobox*Listbox*Background", COLORS["bg_input"])
        self.root.option_add("*TCombobox*Listbox*Foreground", COLORS["text"])

    def _update_clock(self):
        """Tick the top-right clock every second."""
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_lbl.config(text=now)

        # Also update elapsed if running
        if self.state in (self.STATE_RUNNING, self.STATE_PAUSED, self.STATE_CALIBRATING):
            if self.session_start:
                elapsed = int(time.time() - self.session_start)
                m, s = divmod(elapsed, 60)
                h, m = divmod(m, 60)
                self.stat_labels["elapsed"].config(text=f"{h:02d}:{m:02d}:{s:02d}")

        self.root.after(1000, self._update_clock)

    # ─── Logging ──────────────────────────────

    def _log(self, msg: str, tag: str = ""):
        """Append a stamped message to the log console (thread-safe)."""
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}]  {msg}\n"

        def _append():
            self.log_text.config(state="normal")
            if tag:
                self.log_text.insert("end", line, tag)
            else:
                self.log_text.insert("end", line)
            if self.autoscroll_var.get():
                self.log_text.see("end")
            self.log_text.config(state="disabled")

        self.root.after(0, _append)

    def _clear_logs(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    # ─── Button handlers ─────────────────────

    def _set_state(self, new_state: str):
        self.state = new_state
        state_display = {
            self.STATE_IDLE:        ("● IDLE",        COLORS["text_dim"]),
            self.STATE_CALIBRATING: ("◉ CALIBRATING", COLORS["yellow"]),
            self.STATE_RUNNING:     ("● RUNNING",     COLORS["green"]),
            self.STATE_PAUSED:      ("● PAUSED",      COLORS["orange"]),
        }
        text, color = state_display.get(new_state, ("● IDLE", COLORS["text_dim"]))
        self.status_lbl.config(text=text, fg=color)
        self.stat_labels["status"].config(text=new_state.upper(), fg=color)

        # Button states
        if new_state == self.STATE_IDLE:
            self.start_btn.config(state="normal", text="▶  Start", bg=COLORS["green"])
            self.pause_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
        elif new_state == self.STATE_CALIBRATING:
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
        elif new_state == self.STATE_RUNNING:
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal", text="⏸  Pause", bg=COLORS["pause_btn"])
            self.stop_btn.config(state="normal")
        elif new_state == self.STATE_PAUSED:
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal", text="▶  Resume", bg=COLORS["green"])
            self.stop_btn.config(state="normal")

        # Lock/unlock config inputs
        config_state = "disabled" if new_state != self.STATE_IDLE else "normal"
        for widget in self.root.winfo_children():
            self._set_entry_state_recursive(widget, config_state, new_state)

    def _set_entry_state_recursive(self, widget, config_state, app_state):
        """Recursively enable/disable Entry and Spinbox widgets."""
        if isinstance(widget, (tk.Entry, tk.Spinbox)):
            try:
                widget.config(state=config_state)
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            self._set_entry_state_recursive(child, config_state, app_state)

    def _on_start(self):
        self.event_count = 0
        self.error_count = 0
        self.last_score = None
        self.last_severity = ""
        self.session_start = time.time()
        self.baseline = None
        self._stop_event.clear()
        self._pause_event.clear()

        self._update_stat_labels()
        self._log("═" * 50, "accent")
        self._log("Session starting...", "info")
        self._log(f"  User       : {self.user_var.get()}", "dim")
        self._log(f"  Interval   : {self.interval_var.get()}s", "dim")
        self._log(f"  Backend    : {self.url_var.get()}", "dim")
        self._log(f"  Calibration: {self.cal_var.get()}s", "dim")
        self._log("═" * 50, "accent")

        self._set_state(self.STATE_CALIBRATING if self.cal_var.get() > 0 else self.STATE_RUNNING)

        # Start tracking thread
        self.tracker_thread = threading.Thread(target=self._tracker_loop, daemon=True)
        self.tracker_thread.start()

    def _on_pause(self):
        if self.state == self.STATE_RUNNING:
            self._pause_event.set()
            self._set_state(self.STATE_PAUSED)
            self._log("⏸  Tracking paused.", "warning")
        elif self.state == self.STATE_PAUSED:
            self._pause_event.clear()
            self._set_state(self.STATE_RUNNING)
            self._log("▶  Tracking resumed.", "success")

    def _on_stop(self):
        self._stop_event.set()
        self._pause_event.clear()
        self._log("⏹  Stopping tracker...", "warning")

        # State goes IDLE once the thread cleans up (see _tracker_cleanup)

    # ─── Tracker thread ──────────────────────

    def _tracker_loop(self):
        """Runs on a background thread — mirrors real_tracker.run_tracker()."""
        acc = MetricAccumulator()
        self.accumulator = acc

        # Start listeners
        ml = mouse.Listener(
            on_move=acc.on_mouse_move,
            on_click=acc.on_mouse_click,
            on_scroll=acc.on_mouse_scroll,
        )
        kl = keyboard.Listener(
            on_press=acc.on_key_press,
            on_release=acc.on_key_release,
        )
        ml.daemon = True
        kl.daemon = True
        ml.start()
        kl.start()
        self.mouse_listener = ml
        self.key_listener = kl

        self._log("Input listeners started (mouse + keyboard)", "success")

        # ── Calibration ──────────────────
        cal_sec = self.cal_var.get()
        if cal_sec > 0:
            self._log(f"⏳  Calibrating for {cal_sec}s — use your computer normally.", "info")
            cal_start = time.time()
            while time.time() - cal_start < cal_sec:
                if self._stop_event.is_set():
                    self._tracker_cleanup(ml, kl)
                    return
                remaining = cal_sec - int(time.time() - cal_start)
                self._log(f"   Calibrating... {remaining}s remaining", "dim")
                time.sleep(1)

            self.baseline = acc.harvest(window_sec=cal_sec)
            self._log("✅  Calibration complete!", "success")
            self._log(
                f"   Baseline → WPM: {self.baseline['wpm_estimate']:.1f}  "
                f"│  Mouse: {self.baseline['mouse_speed_mean']:.1f} px/s  "
                f"│  Jitter: {self.baseline['mouse_jitter']:.1f}°",
                "info",
            )

        self.root.after(0, lambda: self._set_state(self.STATE_RUNNING))
        self._log("Tracking active. Sending events...", "success")

        interval = self.interval_var.get()
        base_url = self.url_var.get()
        user_id = self.user_var.get()

        # ── Main loop ───────────────────
        while not self._stop_event.is_set():
            # Sleep in small increments so we can react to stop quickly
            slept = 0.0
            while slept < interval:
                if self._stop_event.is_set():
                    break
                # While paused, don't advance the sleep counter
                if self._pause_event.is_set():
                    time.sleep(0.2)
                    continue
                time.sleep(0.25)
                slept += 0.25

            if self._stop_event.is_set():
                break

            # Don't harvest if we're paused (should not happen, but guard)
            if self._pause_event.is_set():
                continue

            payload = acc.harvest(window_sec=interval, baseline=self.baseline)
            payload["user_id"] = user_id
            self.event_count += 1

            result = send_payload(payload, base_url)

            if result and "error" not in result:
                score = result.get("score", "?")
                severity = result.get("severity", "?")
                self.last_score = float(score) if isinstance(score, (int, float)) else None
                self.last_severity = str(severity)

                bar_len = int(float(score) / 2) if isinstance(score, (int, float)) else 0
                bar = "█" * bar_len + "░" * (50 - bar_len)
                self._log(
                    f"[{self.event_count:4d}]  Score: {score:>5}  │  {severity:<10}  │  "
                    f"WPM: {payload['wpm_estimate']:>5.1f}  │  Jitter: {payload['mouse_jitter']:>5.1f}",
                    "success" if float(score) < 40 else ("warning" if float(score) < 70 else "error"),
                )
            else:
                err = result.get("error", "Unknown") if result else "No response"
                self.error_count += 1
                self._log(f"[{self.event_count:4d}]  ⚠  Error: {err}", "error")

            self.root.after(0, self._update_stat_labels)

        self._tracker_cleanup(ml, kl)

    def _tracker_cleanup(self, ml, kl):
        """Stop listeners and reset state."""
        try:
            ml.stop()
        except Exception:
            pass
        try:
            kl.stop()
        except Exception:
            pass

        self._log(f"Session ended. Total events: {self.event_count}  |  Errors: {self.error_count}", "info")
        self._log("═" * 50, "accent")
        self.root.after(0, lambda: self._set_state(self.STATE_IDLE))

    # ─── Stats Update ────────────────────────

    def _update_stat_labels(self):
        self.stat_labels["events"].config(text=str(self.event_count))
        self.stat_labels["errors"].config(
            text=str(self.error_count),
            fg=COLORS["red"] if self.error_count > 0 else COLORS["text"],
        )
        if self.last_score is not None:
            score_color = COLORS["green"]
            if self.last_score >= 70:
                score_color = COLORS["red"]
            elif self.last_score >= 40:
                score_color = COLORS["yellow"]
            self.stat_labels["score"].config(text=f"{self.last_score:.1f}", fg=score_color)
            self.stat_labels["severity"].config(text=self.last_severity.upper(), fg=score_color)
        else:
            self.stat_labels["score"].config(text="—")
            self.stat_labels["severity"].config(text="—")


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    root = tk.Tk()

    # Set window icon (optional — graceful fallback)
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = TrackerGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: _on_close(app, root))
    root.mainloop()


def _on_close(app: TrackerGUI, root: tk.Tk):
    """Graceful shutdown on window close."""
    if app.state != TrackerGUI.STATE_IDLE:
        if not messagebox.askyesno("Confirm", "Tracker is running.\nStop and exit?"):
            return
        app._stop_event.set()
        app._pause_event.clear()
        # Give the thread a moment to clean up
        time.sleep(0.5)
    root.destroy()


if __name__ == "__main__":
    main()
