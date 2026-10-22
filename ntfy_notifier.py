"""
ntfy_notifier.py
================
Real-Time ntfy Mobile Push Notification Dispatcher for ZIDIS
------------------------------------------------------------
Delivers immediate, high-priority push notifications directly to your phone
(Android, iOS, or Web) when the ZIDIS STM32 Node triggers an earthquake event.

Features:
  1. Zero external dependencies: Uses standard library urllib.request + JSON POST.
  2. Non-blocking asynchronous dispatch: Runs in background daemon thread without
     stalling the 100 Hz RTOS serial loop or real-time GUI animation.
  3. Smart cooldown & deduplication: Prevents notification floods while prioritizing
     immediate critical escalations (L1 Soft Alert -> L2 Full Siren).
  4. Rich push metadata: Emojis, urgent priority (overrides Do Not Disturb & sounds alarm),
     seismic metrics (Peak Acc, STA/LTA ratio, S-wave warning lead times).
  5. CLI & Test Mode: Quick test dispatch and topic configuration from terminal.

Quick Setup on Phone:
  1. Install "ntfy" app on your phone (Google Play Store, F-Droid, or Apple App Store).
  2. Tap "+" and subscribe to your topic (e.g., 'zidis_earthquake_alert').
  3. Run `python ntfy_notifier.py --test` to verify your phone rings!
"""

import sys
import os
import time
import json
import threading
import argparse
import urllib.request
import urllib.error

# Windows console encoding safeguard
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ntfy_config.json")
DEFAULT_TOPIC = "zidis_earthquake_alert"
DEFAULT_SERVER = "https://ntfy.sh"
DEFAULT_COOLDOWN = 15.0  # seconds between repeated alerts of same category

# Global lock & cooldown tracking
_state_lock = threading.Lock()
_last_alert_times = {}  # category -> timestamp
_cached_config = None


def load_config():
    """Loads configuration from ntfy_config.json, with env var and fallback overrides."""
    global _cached_config
    cfg = {
        "topic": os.environ.get("NTFY_TOPIC", DEFAULT_TOPIC),
        "server": os.environ.get("NTFY_SERVER", DEFAULT_SERVER),
        "cooldown_seconds": DEFAULT_COOLDOWN,
        "enabled": True
    }
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    cfg.update(loaded)
        except Exception as e:
            print(f"[NTFY WARNING] Failed to read {CONFIG_FILE}: {e}", file=sys.stderr)

    # CLI / ENV overrides take precedence if set
    if "NTFY_TOPIC" in os.environ:
        cfg["topic"] = os.environ["NTFY_TOPIC"]
    if "NTFY_SERVER" in os.environ:
        cfg["server"] = os.environ["NTFY_SERVER"]

    _cached_config = cfg
    return cfg


def save_config(new_config):
    """Saves updated configuration dict back to ntfy_config.json."""
    global _cached_config
    cfg = load_config()
    cfg.update(new_config)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        _cached_config = cfg
        return True
    except Exception as e:
        print(f"[NTFY ERROR] Failed to save config: {e}", file=sys.stderr)
        return False


def _send_http_request(server, topic, payload):
    """Internal HTTP POST worker running in a background thread."""
    url = f"{server.rstrip('/')}/{topic}"
    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "ZIDIS-Node-EEW/1.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            if resp.status in (200, 201):
                return True
            else:
                print(f"[NTFY] Server returned status {resp.status}", file=sys.stderr)
                return False
    except urllib.error.URLError as e:
        print(f"[NTFY ERROR] Network error reaching {url}: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[NTFY ERROR] Unexpected error: {e}", file=sys.stderr)
        return False


def send_notification(
    title,
    message,
    priority="urgent",
    tags=None,
    topic=None,
    server=None,
    category="default",
    force=False,
    click_url=None
):
    """
    Asynchronously sends a push notification to ntfy.

    Parameters:
      - title: Header string shown on phone lockscreen
      - message: Body text with alert details
      - priority: "urgent" (5), "high" (4), "default" (3), "low" (2), "min" (1)
      - tags: List of emojis or string keywords (e.g. ['rotating_light', 'warning'])
      - topic: Optional topic override (defaults to config topic)
      - server: Optional server override (defaults to https://ntfy.sh)
      - category: Deduplication key for rate-limiting
      - force: If True, bypasses cooldown checks
      - click_url: URL opened when tapping notification on phone
    """
    cfg = load_config()
    if not cfg.get("enabled", True):
        return False

    final_topic = topic or cfg.get("topic", DEFAULT_TOPIC)
    final_server = server or cfg.get("server", DEFAULT_SERVER)
    cooldown = float(cfg.get("cooldown_seconds", DEFAULT_COOLDOWN))

    now = time.time()
    with _state_lock:
        last_time = _last_alert_times.get(category, 0.0)
        if not force and (now - last_time < cooldown):
            # Suppress duplicate message within cooldown window
            return False
        _last_alert_times[category] = now

    payload = {
        "topic": final_topic,
        "title": title,
        "message": message,
        "priority": priority,
        "tags": tags or ["warning", "earthquake"]
    }
    if click_url:
        payload["click"] = click_url

    # Dispatch in background thread so caller never blocks
    thread = threading.Thread(
        target=_send_http_request,
        args=(final_server, final_topic, payload),
        daemon=True,
        name=f"ntfy-dispatch-{category}"
    )
    thread.start()
    return True


def send_from_log_line(line, topic=None):
    """
    Parses a raw serial log line from the STM32 NUCLEO-H533RE board
    and triggers the appropriate categorized mobile push notification.
    """
    line_clean = line.strip()

    # 1. Corroborated Quorum Alert (Level 2 Full Siren)
    if "ALERT: CORROBORATED" in line_clean or "FULL SIREN ACTIVE" in line_clean:
        return send_notification(
            title="🚨 CRITICAL: CORROBORATED EARTHQUAKE SIREN!",
            message=(
                "ZIDIS Consensus: Level 2 Full Siren Escalation!\n"
                "Multiple seismic sensing nodes have verified the primary P-wave arrival.\n"
                "Destructive S-wave arrival imminent. Take cover immediately!"
            ),
            priority="urgent",
            tags=["rotating_light", "earthquake", "siren"],
            topic=topic,
            category="alert_l2",
            force=True  # Always escalate immediately
        )

    # 2. Local MLP Neural Detection
    elif "[T_DETECT] Earthquake Event Detected!" in line_clean:
        return send_notification(
            title="⚡ ZIDIS: Earthquake Event Detected!",
            message=(
                "On-board 7-8-3 MLP Neural Network classified incoming waveform as an EARTHQUAKE (Class 2).\n"
                "Dual-level consensus protocol initiated."
            ),
            priority="urgent",
            tags=["zap", "earthquake", "warning"],
            topic=topic,
            category="detect_mlp"
        )

    # 3. Kinematic Analyser P-Wave Anomaly Trigger
    elif "ANOMALY DETECTED" in line_clean:
        # Extract latency info if present in log line
        latency_str = ""
        if "Latency:" in line_clean:
            parts = line_clean.split("Latency:")
            if len(parts) > 1:
                latency_str = f"\nDetection: {parts[1].strip()}"

        return send_notification(
            title="⚠️ PRE-WARNING: Seismic P-Wave Triggered",
            message=(
                "ZIDIS Kinematic Engine triggered on incoming P-wave arrival!\n"
                "Lead times: ~3.0s @ 25km | ~6.0s @ 50km | ~12.0s @ 100km (0.12 s/km)"
                f"{latency_str}"
            ),
            priority="high",
            tags=["warning", "chart_with_upwards_trend"],
            topic=topic,
            category="analyser_anomaly"
        )

    # 4. Preliminary Local Soft Alert
    elif "ALERT: LOCAL" in line_clean:
        return send_notification(
            title="⚠️ ALERT: Local P-Wave Soft Warning",
            message=(
                "ZIDIS Node: Preliminary Level 1 warning beep activated.\n"
                "Awaiting quorum confirmation from consensus network."
            ),
            priority="high",
            tags=["sound", "warning"],
            topic=topic,
            category="alert_l1"
        )

    # 5. Alert Cleared / Safe
    elif "ALERT: CLEAR" in line_clean:
        return send_notification(
            title="✅ ZIDIS: Seismic Alert Normalised",
            message="Hold-off timer expired. Seismic vibrations returned to baseline.",
            priority="low",
            tags=["white_check_mark", "shield"],
            topic=topic,
            category="alert_clear"
        )

    # 6. Sensor Hardware Fault
    elif "[FAULT]" in line_clean:
        return send_notification(
            title="🛠️ ZIDIS Hardware Diagnostic: Sensor Fault",
            message=f"Warning: {line_clean}",
            priority="default",
            tags=["wrench", "warning"],
            topic=topic,
            category="sensor_fault"
        )

    return False


def send_plotter_alert(
    peak_acc=0.0,
    sta_lta_ratio=0.0,
    criteria_fired=0,
    current_time=0.0,
    lead_time_s=14.4,
    topic=None
):
    """
    Sends an earthquake alert triggered from the live P-wave plotter
    or simulation replay engine.
    """
    title = "🚨 EARTHQUAKE EARLY WARNING: P-Wave Arrival!"
    message = (
        f"Seismic P-Wave detected at t0+{current_time:.2f}s\n"
        f"Peak Acc: {peak_acc:.4f} g | STA/LTA Ratio: {sta_lta_ratio:.2f}\n"
        f"Criteria Met: {criteria_fired}/4\n"
        f"Estimated S-Wave Warning Lead Time: ~{lead_time_s:.1f}s (0.12 s/km @ 120km epicenter)"
    )
    return send_notification(
        title=title,
        message=message,
        priority="urgent",
        tags=["rotating_light", "earthquake", "warning"],
        topic=topic,
        category="plotter_alert"
    )


def send_test_notification(topic=None):
    """Synchronously sends a test notification to verify mobile setup."""
    cfg = load_config()
    final_topic = topic or cfg.get("topic", DEFAULT_TOPIC)
    final_server = cfg.get("server", DEFAULT_SERVER)

    print("=" * 65)
    print(" ZIDIS Mobile Notification Test Dispatch")
    print("=" * 65)
    print(f" Target Server : {final_server}")
    print(f" Topic Name    : {final_topic}")
    print(f" Mobile Link   : {final_server.rstrip('/')}/{final_topic}")
    print("=" * 65)
    print("Sending test notification to phone...", end=" ", flush=True)

    payload = {
        "topic": final_topic,
        "title": "🔔 ZIDIS EEW: Mobile Alerts Connected!",
        "message": (
            "Congratulations! Your phone is now paired with the ZIDIS Earthquake Early Warning System.\n"
            f"Active Topic: {final_topic}\n"
            "You will receive instant, urgent push alerts whenever an earthquake is detected."
        ),
        "priority": "urgent",
        "tags": ["tada", "earthquake", "bell"]
    }

    success = _send_http_request(final_server, final_topic, payload)
    if success:
        print("[SUCCESS!]")
        print("\nYour test alert was successfully dispatched!")
        print(f"Check your phone ntfy app now. If you haven't subscribed yet, open:")
        print(f"  ->  {final_server.rstrip('/')}/{final_topic}")
        print("and tap 'Subscribe' to receive alerts anytime.")
    else:
        print("[FAILED]")
        print("Please check your internet connection or server settings.")
    print("=" * 65)
    return success


def main():
    parser = argparse.ArgumentParser(description="ZIDIS ntfy Mobile Push Notification Tool")
    parser.add_argument("--test", action="store_true", help="Send a test notification to your phone")
    parser.add_argument("--topic", default=None, help="Specify or override the ntfy topic name")
    parser.add_argument("--set-topic", default=None, help="Save a new default topic to ntfy_config.json")
    parser.add_argument("--status", action="store_true", help="Display current notification configuration")
    parser.add_argument("--message", default=None, help="Send a custom notification message")
    parser.add_argument("--title", default="⚠️ ZIDIS Alert", help="Title for custom notification")
    args = parser.parse_args()

    cfg = load_config()

    if args.set_topic:
        new_topic = args.set_topic.strip()
        save_config({"topic": new_topic})
        print(f"[SUCCESS] Default topic updated to: '{new_topic}' in {CONFIG_FILE}")
        return

    if args.status:
        print("=" * 60)
        print(" ZIDIS Mobile Notification Configuration")
        print("=" * 60)
        print(f" Config File : {CONFIG_FILE}")
        print(f" Topic       : {cfg.get('topic')}")
        print(f" Server      : {cfg.get('server')}")
        print(f" Cooldown    : {cfg.get('cooldown_seconds')}s")
        print(f" Enabled     : {cfg.get('enabled')}")
        print(f" Phone Link  : {cfg.get('server').rstrip('/')}/{cfg.get('topic')}")
        print("=" * 60)
        return

    if args.test:
        send_test_notification(topic=args.topic)
        return

    if args.message:
        target_topic = args.topic or cfg.get("topic", DEFAULT_TOPIC)
        print(f"Sending custom message to '{target_topic}'...")
        ok = send_notification(
            title=args.title,
            message=args.message,
            priority="urgent",
            topic=target_topic,
            force=True
        )
        time.sleep(1.0) # Wait briefly for async thread
        print("[DONE] Alert dispatched.")
        return

    # Default: Show help and status
    parser.print_help()
    print("\nCurrent Status:")
    print(f"  Topic: {cfg.get('topic')}")
    print(f"  Phone Link: {cfg.get('server').rstrip('/')}/{cfg.get('topic')}")


if __name__ == "__main__":
    main()
