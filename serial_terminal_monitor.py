"""
serial_terminal_monitor.py
==========================
Real-Time Terminal Console & Serial Telemetry Monitor for ZIDIS STM32 Node
--------------------------------------------------------------------------
Features:
  1. Auto-detects ST-LINK VCP COM port (e.g. COM5) or accepts --port COMx.
  2. Displays all uT-Kernel 3.0 RTOS task logs:
       - [BOOT] System initialization and configuration
       - [T_SENSE] Seismic sensor acquisition & 100 Hz sampling
       - [T_DETECT] 128-pt FFT feature extraction & MLP neural classification
       - [T_CONSENSUS] Dual-level alert escalation (L1 Soft Beep -> L2 Siren)
       - [T_DIAG] Software watchdog & system health heartbeats
       - [FAULT] Sensor fault diagnostics (flatline, clipping, NaN/Inf)
       - [USER_IO] Push-button (PC13) alarm silence / mute events
  3. Decodes raw 'D:<value>' sample packets into a live terminal VU-meter & status line.

Usage:
  python serial_terminal_monitor.py               # Auto-detects port
  python serial_terminal_monitor.py --port COM5   # Explicit port
"""

import sys
import os
import time
import argparse
import serial
import serial.tools.list_ports
import ntfy_notifier

# Windows console encoding safeguard
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BAUD_RATE = 115200

def find_stlink_port():
    """Auto-detect ST-LINK Virtual COM Port."""
    for p in serial.tools.list_ports.comports():
        desc = (p.description or '').lower()
        hwid = (p.hwid or '').lower()
        if '0483:' in hwid or 'stlink' in desc or 'st-link' in desc or 'usb serial' in desc:
            return p.device
    return None

def format_meter(val, max_val=0.015, width=10):
    norm = min(abs(val) / max_val, 1.0)
    bars = int(norm * width)
    if val >= 0:
        return "[" + " " * width + "|" + "#" * bars + " " * (width - bars) + "]"
    else:
        return "[" + " " * (width - bars) + "#" * bars + "|" + " " * width + "]"

def main():
    parser = argparse.ArgumentParser(description="ZIDIS Terminal Serial Monitor")
    parser.add_argument("--port", default=None, help="Serial COM port (default: auto-detect)")
    parser.add_argument("--baud", type=int, default=BAUD_RATE, help="Baud rate (default: 115200)")
    parser.add_argument("--ntfy-topic", default=None, help="ntfy topic to send mobile alerts to (overrides ntfy_config.json)")
    parser.add_argument("--no-ntfy", action="store_true", help="Disable ntfy mobile notifications")
    args = parser.parse_args()

    # Load ntfy configuration
    ntfy_cfg = ntfy_notifier.load_config()
    active_topic = args.ntfy_topic or ntfy_cfg.get("topic", "zidis_earthquake_alert")
    ntfy_enabled = (not args.no_ntfy) and ntfy_cfg.get("enabled", True)

    port = args.port
    if not port:
        port = find_stlink_port()
        if not port:
            print("[ERROR] No ST-LINK or USB Serial device detected!")
            print("        Please connect your NUCLEO-H533RE board and try again.")
            sys.exit(1)

    print("=" * 78)
    print(" ZIDIS NUCLEO-H533RE Terminal Serial Console")
    print(f" Port: {port}  |  Baud: {args.baud}  |  RTOS: uT-Kernel 3.0")
    if ntfy_enabled:
        print(f" Mobile Alerts : ENABLED -> https://ntfy.sh/{active_topic}")
    else:
        print(" Mobile Alerts : DISABLED")
    print("=" * 78)
    print("Connecting to STM32 board...", flush=True)

    try:
        ser = serial.Serial(port, args.baud, timeout=0.1)
    except Exception as e:
        print(f"\n[ERROR] Cannot open {port}: {e}")
        print("Note: If STM32CubeIDE's internal Console/Terminal tab or another script has COM5 open,")
        print("      please close/disconnect it first, then re-run.")
        sys.exit(1)

    print(f"[CONNECTED] Listening to {port}...\n", flush=True)

    sample_count = 0
    recent_samples = []
    sta = 0.0002
    lta = 0.0002
    alpha_sta = 0.02
    alpha_lta = 0.001

    try:
        while True:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if not line:
                continue

            if line.startswith('D:'):
                try:
                    raw_val = int(line[2:])
                except ValueError:
                    continue
                val = raw_val / 1000.0 # acceleration in g
                sample_count += 1

                # Update live STA/LTA in Python
                abs_val = abs(val)
                sta = alpha_sta * abs_val + (1.0 - alpha_sta) * sta
                lta = alpha_lta * abs_val + (1.0 - alpha_lta) * lta
                ratio = sta / max(lta, 1e-5)

                if sample_count % 25 == 0: # Print status every 250ms (4 times per second)
                    meter = format_meter(val)
                    status_text = f"[SAMPLES #{sample_count:06d}] {meter} Acc: {val:+.4f}g | STA/LTA: {ratio:4.2f}"
                    # Print on same line or print cleanly
                    sys.stdout.write(f"\r{status_text}")
                    sys.stdout.flush()
            else:
                # Clear line and print board message with clean banner
                sys.stdout.write('\r' + ' ' * 78 + '\r')
                if "[FAULT]" in line:
                    print(f"\033[91m{line}\033[0m", flush=True)
                    if ntfy_enabled:
                        ntfy_notifier.send_from_log_line(line, topic=active_topic)
                elif "ALERT" in line or "ANOMALY" in line or "Earthquake" in line:
                    print("\n" + "=" * 78, flush=True)
                    print(f" >>> {line}", flush=True)
                    print("=" * 78, flush=True)
                    # Trigger audible PC alert
                    try:
                        import winsound
                        import threading
                        def _b():
                            for _ in range(3):
                                winsound.Beep(1500, 120)
                                time.sleep(0.05)
                        threading.Thread(target=_b, daemon=True).start()
                    except Exception:
                        sys.stdout.write('\a')
                        sys.stdout.flush()

                    # Trigger ntfy mobile push notification
                    if ntfy_enabled:
                        dispatched = ntfy_notifier.send_from_log_line(line, topic=active_topic)
                        if dispatched:
                            print(f" [NTFY] -> Push alert dispatched to phone: https://ntfy.sh/{active_topic}", flush=True)
                else:
                    # Check for alert clear message
                    if "ALERT: CLEAR" in line and ntfy_enabled:
                        ntfy_notifier.send_from_log_line(line, topic=active_topic)
                    print(line, flush=True)

    except KeyboardInterrupt:
        print("\n\n[TERMINAL] Monitor closed by user.")
    finally:
        ser.close()

if __name__ == '__main__':
    main()
