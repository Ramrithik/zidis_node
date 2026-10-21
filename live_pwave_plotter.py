"""
ZIDIS Live P-Wave Monitor & Real-World Simulation Dashboard
===========================================================
Dual-Pane Architecture:
  [LEFT PANE]  Waveform Display:
               - Top: Full 300-second Earthquake Record (Overview + Moving Scrubber)
               - Bottom: Real-Time Sliding P-Wave Window (High-resolution live oscillation)
  [RIGHT PANE] Seismic Analyser Engine (C-firmware dsp.c exact replication):
               - Top: STA & LTA Exponential Moving Averages
               - Middle: STA/LTA Dynamic Ratio with Trigger (3.0) & Detrigger (1.5) lines
               - Bottom: Multi-Criteria Fusion (STA/LTA + RMS + ZCR + Peak) with Alarm state

Input Sources:
  1. Real-world downloaded earthquake data ('tohoku_real_pwave_100hz.npz') [DEFAULT]
  2. Live physical NUCLEO-H533RE serial stream (COM port)
  3. Optional HIL (Hardware-in-the-Loop): feeds real earthquake samples into STM32 over serial!

Usage:
  python live_pwave_plotter.py                  # Replays downloaded 2011 Tohoku real earthquake
  python live_pwave_plotter.py --speed 2.0      # Replays at 2x speed
  python live_pwave_plotter.py --mode live      # Connects directly to NUCLEO COM port
  python live_pwave_plotter.py --port COM5      # Sends samples to board while plotting
"""

import sys
import os
import time
import argparse
import threading
from collections import deque
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Button

# -------------------------------------------------------------
# 1. Configuration & Constants
# -------------------------------------------------------------
SAMPLE_RATE = 100          # 100 Hz = 10 ms per sample
MAX_SLIDING_SAMPLES = 500  # 5-second live window
BAUD_RATE = 115200

# Analyser Thresholds (matching config.h in STM32 firmware)
STA_LTA_TRIG = 3.0
STA_LTA_DETRIG = 1.5
ANALYSER_RMS_RATIO_THRESH = 4.0
ANALYSER_ZCR_RATIO_THRESH = 2.0
ANALYSER_PEAK_THRESH = 0.3
ANALYSER_MIN_CRITERIA = 2
ANALYSER_RMS_WINDOW = 50
ANALYSER_ZCR_WINDOW = 50

# -------------------------------------------------------------
# 2. Global State & Circular Buffers
# -------------------------------------------------------------
samples_buf = deque(maxlen=MAX_SLIDING_SAMPLES)
sta_buf = deque(maxlen=MAX_SLIDING_SAMPLES)
lta_buf = deque(maxlen=MAX_SLIDING_SAMPLES)
ratio_buf = deque(maxlen=MAX_SLIDING_SAMPLES)
criteria_buf = deque(maxlen=MAX_SLIDING_SAMPLES)

# Analyser State (exact mirror of AnalyserState_t in dsp.h)
sta = 0.025
lta = 0.025
sta_lta_fired = False

rms_buffer = deque(maxlen=ANALYSER_RMS_WINDOW)
rms_long = 0.05
rms_fired = False

zcr_buffer = deque(maxlen=ANALYSER_ZCR_WINDOW)
zcr_baseline = 10.0
zcr_fired = False

peak_buffer = deque(maxlen=ANALYSER_RMS_WINDOW)
peak_max = 0.0
peak_fired = False

analyser_cooldown = False
last_trigger_time = -999.0
total_anomalies_detected = 0
anomaly_active = False

# Simulation / Playback tracking
# Default to index 22600 (t = 166.0s) so the P-wave arrival (t = 176.3s) strikes within 10 seconds!
current_sample_idx = 22600
is_paused = False
playback_speed = 1.0

# Pre-loaded full dataset
full_wave_data = None
full_time_data = None
data_source_label = "2011 Tohoku Mw 9.1 (IU.MAJO @ 100Hz)"

# Audio Buzzer Alarm Control
buzzer_enabled = True

def sound_buzzer_alert(alert_type="pwave"):
    """Sounds an audible buzzer alarm through the PC speaker when triggered."""
    if not buzzer_enabled:
        return
    def _beep():
        try:
            import winsound
            if alert_type == "pwave":
                # Rapid 3-chirp early warning beep (1400 Hz)
                for _ in range(3):
                    winsound.Beep(1400, 110)
                    time.sleep(0.04)
            elif alert_type == "siren":
                # High-low alternating siren
                for _ in range(3):
                    winsound.Beep(1800, 180)
                    winsound.Beep(1100, 180)
        except Exception:
            try:
                # Terminal bell fallback
                sys.stdout.write('\a')
                sys.stdout.flush()
            except Exception:
                pass

    t = threading.Thread(target=_beep, daemon=True)
    t.start()

# -------------------------------------------------------------
# 3. Analyser Module (Exact Algorithm from dsp.c)
# -------------------------------------------------------------
alpha_sta = 0.0198       # tau = 0.5s @ 100Hz
alpha_lta = 0.001        # tau = 10s @ 100Hz
alpha_rms_long = 0.00067 # tau = 15s
alpha_zcr = 0.0005       # tau = 20s

def format_ascii_meter(val, max_val=0.015, width=8):
    """Generates an ASCII VU-meter representing seismic acceleration."""
    norm = min(abs(val) / max_val, 1.0)
    bars = int(norm * width)
    if val >= 0:
        return "[" + " " * width + "|" + "#" * bars + " " * (width - bars) + "]"
    else:
        return "[" + " " * (width - bars) + "#" * bars + "|" + " " * width + "]"

def process_sample(sample_val, current_sim_time):
    """
    Evaluates one sample through the 4-criteria firmware analyser pipeline.
    Returns: (sta, lta, ratio, criteria_count, is_anomaly)
    """
    global sta, lta, sta_lta_fired
    global rms_long, rms_fired
    global zcr_baseline, zcr_fired
    global peak_max, peak_fired
    global analyser_cooldown, last_trigger_time
    global total_anomalies_detected, anomaly_active

    abs_sample = abs(sample_val)

    # 2.0-second Cooldown Check
    if analyser_cooldown and (current_sim_time - last_trigger_time > 2.0):
        analyser_cooldown = False
        anomaly_active = False

    # Criterion 1: STA/LTA Ratio
    sta = (alpha_sta * abs_sample) + ((1.0 - alpha_sta) * sta)
    if not sta_lta_fired:
        lta = (alpha_lta * abs_sample) + ((1.0 - alpha_lta) * lta)
    lta_safe = max(lta, 0.0001)
    ratio = sta / lta_safe

    if not sta_lta_fired:
        if ratio > STA_LTA_TRIG:
            sta_lta_fired = True
    else:
        if ratio < STA_LTA_DETRIG:
            sta_lta_fired = False
    c1 = sta_lta_fired

    # Criterion 2: RMS Energy Jump
    rms_buffer.append(sample_val * sample_val)
    rms_short = np.sqrt(np.mean(list(rms_buffer))) if len(rms_buffer) > 0 else 0.0
    if not rms_fired:
        rms_long = (alpha_rms_long * rms_short) + ((1.0 - alpha_rms_long) * rms_long)
    rms_long_safe = max(rms_long, 0.001)
    c2 = (rms_short / rms_long_safe) > ANALYSER_RMS_RATIO_THRESH

    # Criterion 3: Low-Frequency Seismic Kinematic Passband (Non-Energy #7)
    # Seismic P-waves oscillate within 1 to 8 crossings per 0.5s (1 - 8 Hz).
    # High-frequency hammer taps and mechanical clatter (> 12 crossings) are rejected.
    zcr_buffer.append(sample_val)
    deadband = 0.20 * lta_safe
    crossings = 0
    last_sign = 0
    for v in zcr_buffer:
        if v > deadband:
            if last_sign < 0:
                crossings += 1
            last_sign = 1
        elif v < -deadband:
            if last_sign > 0:
                crossings += 1
            last_sign = -1
    zcr_current = float(crossings)
    c3 = (1 <= crossings <= 8)

    # Criterion 4: Peak Acceleration
    peak_buffer.append(abs_sample)
    peak_max = max(peak_buffer) if len(peak_buffer) > 0 else 0.0
    c4 = (peak_max > ANALYSER_PEAK_THRESH)

    # Composite Multi-Criteria Decision
    criteria_count = int(c1) + int(c2) + int(c3) + int(c4)
    detected = (criteria_count >= ANALYSER_MIN_CRITERIA) and (not analyser_cooldown)

    if detected:
        analyser_cooldown = True
        anomaly_active = True
        last_trigger_time = current_sim_time
        total_anomalies_detected += 1
        sound_buzzer_alert("pwave")
        print("\n" + "=" * 78, flush=True)
        print(f"[ANALYSER] *** P-WAVE ANOMALY TRIGGERED! *** Time: t0+{current_sim_time:6.2f}s", flush=True)
        print(f"           Signal Amplitude : {sample_val:+.5f} g (Peak: {peak_max:.4f} g)", flush=True)
        print(f"           STA/LTA Ratio    : {ratio:.2f} (Trigger Threshold: {STA_LTA_TRIG})", flush=True)
        print(f"           Criteria Fired   : {criteria_count}/4 (STA/LTA={int(c1)}, RMS={int(c2)}, ZCR={int(c3)}, Peak={int(c4)})", flush=True)
        print(f"           Early Alert      : LOCAL ALERT L1 (Soft Warning Beep Activated)", flush=True)
        print(f"           Lead Time S-Wave : ~14.4s (0.12 s/km @ 120km epicenter)", flush=True)
        print(f"           Total Detections : {total_anomalies_detected}", flush=True)
        print("=" * 78 + "\n", flush=True)

    return sta, lta, ratio, criteria_count, detected

# -------------------------------------------------------------
# 4. Simulation Feeder Thread & Pre-warm
# -------------------------------------------------------------
def prewarm_analyser(target_idx):
    """
    Fast pre-computes firmware analyser state up to target_idx
    so STA/LTA exponential moving averages and baseline buffers match physics.
    Also pre-fills plotting buffers so the GUI displays live history immediately!
    """
    global sta, lta, sta_lta_fired, rms_long, rms_fired, zcr_baseline, zcr_fired
    global total_anomalies_detected, anomaly_active, analyser_cooldown

    print(f"[PREWARM] Synchronizing analyser state up to sample #{target_idx} (t0+{full_time_data[target_idx]:.2f}s)...", flush=True)
    for i in range(target_idx):
        s_val = float(full_wave_data[i])
        t_val = float(full_time_data[i])
        s, l, r, crit, trig = process_sample(s_val, t_val)

        # Populate circular buffers for the last MAX_SLIDING_SAMPLES
        if i >= target_idx - MAX_SLIDING_SAMPLES:
            samples_buf.append(s_val)
            sta_buf.append(s)
            lta_buf.append(l)
            ratio_buf.append(r)
            criteria_buf.append(crit)

    # Reset event counters for live session
    total_anomalies_detected = 0
    anomaly_active = False
    analyser_cooldown = False
    print(f"[PREWARM] Synchronized! Ambient LTA={lta:.6f}g, Buffer={len(samples_buf)} samples ready.", flush=True)

# -------------------------------------------------------------
# 5. Unified Command Handler & Terminal Keyboard Listener
# -------------------------------------------------------------
def handle_command_key(key):
    """
    Unified command handler for both GUI and Terminal keyboard inputs,
    as well as GUI on-screen buttons.
    """
    global is_paused, current_sample_idx, playback_speed

    if key is None:
        return

    if key == ' ':
        k = ' '
    else:
        k = str(key).strip().lower()

    if k in [' ', 'space', 'p']:
        is_paused = not is_paused
        status = "PAUSED (Playback frozen)" if is_paused else f"RESUMED ({playback_speed:.1f}x speed)"
        print(f"\n[CONTROL] >>> {status} <<<", flush=True)

    elif k in ['j', 'jump']:
        target = 23000  # 6 seconds before verified P-wave arrival at t=176.3s
        current_sample_idx = target
        prewarm_analyser(target)
        print(f"\n[CONTROL] >>> JUMPED TO P-WAVE ARRIVAL (t0 + {full_time_data[target]:.1f}s) <<<", flush=True)

    elif k in ['r', 'reset']:
        target = 0      # Reset to beginning (t0 - 60s)
        current_sample_idx = target
        prewarm_analyser(target)
        print(f"\n[CONTROL] >>> RESET TO BEGINNING (t0 - 60.0s) <<<", flush=True)

    elif k in ['+', '=', 'faster', 'f']:
        playback_speed = min(playback_speed * 1.5, 10.0)
        print(f"\n[CONTROL] >>> SPEED INCREASED: {playback_speed:.1f}x <<<", flush=True)

    elif k in ['-', '_', 'slower', 's']:
        playback_speed = max(playback_speed / 1.5, 0.2)
        print(f"\n[CONTROL] >>> SPEED DECREASED: {playback_speed:.1f}x <<<", flush=True)

    elif k in ['b', 'buzzer', 'mute']:
        buzzer_enabled = not buzzer_enabled
        status = "PC BUZZER ENABLED (Audible Alarms ON)" if buzzer_enabled else "PC BUZZER MUTED (Silent Mode)"
        print(f"\n[CONTROL] >>> {status} <<<", flush=True)
        if buzzer_enabled:
            sound_buzzer_alert("pwave")

    elif k in ['q', 'quit']:
        print("\n[CONTROL] Quitting dashboard...", flush=True)
        os._exit(0)

def start_terminal_keyboard_listener():
    """
    Starts a background thread that captures keystrokes directly
    from the PowerShell / CMD console so terminal users can pause/jump/change speed.
    """
    def listener_loop():
        try:
            import msvcrt
            while True:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    try:
                        key_str = ch.decode('utf-8', errors='ignore')
                    except Exception:
                        continue
                    handle_command_key(key_str)
                else:
                    time.sleep(0.04)
        except Exception:
            pass

    t = threading.Thread(target=listener_loop, daemon=True)
    t.start()

# -------------------------------------------------------------
# 6. Simulation Feeder Thread
# -------------------------------------------------------------
def simulation_feeder_worker(serial_conn=None):
    """
    Feeds downloaded earthquake samples at 100 Hz in real-time,
    processes them through the analyser, and optionally transmits to STM32.
    """
    global current_sample_idx, is_paused, playback_speed

    total_samples = len(full_wave_data)

    print(f"[SIMULATION] Feeder running ({total_samples} samples, initial speed={playback_speed}x)...", flush=True)

    sample_counter = 0

    while True:
        if is_paused:
            time.sleep(0.04)
            continue

        start_time = time.time()
        val = float(full_wave_data[current_sample_idx])
        sim_time = float(full_time_data[current_sample_idx])

        # Run analyser
        s, l, r, crit, trig = process_sample(val, sim_time)

        # Update plotting circular buffers
        samples_buf.append(val)
        sta_buf.append(s)
        lta_buf.append(l)
        ratio_buf.append(r)
        criteria_buf.append(crit)

        # Continuous Terminal Status Output (every 50 samples = 0.5s of simulated time)
        sample_counter += 1
        if sample_counter % 50 == 0:
            meter = format_ascii_meter(val)
            state_tag = "*** P-WAVE ALARM ***" if anomaly_active else "NORMAL MONITORING"
            crit_stars = "*" * crit + "." * (4 - crit)
            pause_tag = " [PAUSED]" if is_paused else f" [{playback_speed:.1f}x]"
            print(f"[STATUS] t0+{sim_time:6.2f}s | {meter} {val:+.5f}g | STA/LTA: {r:5.2f} | "
                  f"Crit: [{crit_stars}] {crit}/4 | State: {state_tag:<20}{pause_tag} | Evts: {total_anomalies_detected}", flush=True)

        # If serial port is open, transmit to NUCLEO board!
        if serial_conn is not None:
            try:
                # Format: "D:<integer>\r\n" matching firmware UART_PrintSample
                milli_g = int(val * 1000.0)
                msg = f"D:{milli_g}\r\n".encode('ascii')
                serial_conn.write(msg)
            except Exception:
                pass

        # Advance index (loop at end)
        current_sample_idx = (current_sample_idx + 1) % total_samples

        # Dynamic interval based on current playback_speed
        interval = 1.0 / (SAMPLE_RATE * max(playback_speed, 0.1))
        elapsed = time.time() - start_time
        sleep_dur = interval - elapsed
        if sleep_dur > 0:
            time.sleep(sleep_dur)

# -------------------------------------------------------------
# 5. Live Serial Stream Worker (For Live Board Mode)
# -------------------------------------------------------------
def serial_reader_worker(ser):
    """Reads live samples directly generated from the NUCLEO board."""
    global total_anomalies_detected
    sim_time = 0.0
    sample_counter = 0
    print("[SERIAL] Live serial stream worker active. Listening to STM32 board on COM port...", flush=True)
    while True:
        try:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if not line:
                continue
            if line.startswith('D:'):
                try:
                    raw = int(line[2:])
                except ValueError:
                    continue
                val = raw / 1000.0
                sim_time += 0.01
                s, l, r, crit, trig = process_sample(val, sim_time)
                samples_buf.append(val)
                sta_buf.append(s)
                lta_buf.append(l)
                ratio_buf.append(r)
                criteria_buf.append(crit)

                sample_counter += 1
                if sample_counter % 50 == 0:
                    meter = format_ascii_meter(val)
                    state_tag = "*** P-WAVE ALARM ***" if anomaly_active else "NORMAL MONITORING"
                    crit_stars = "*" * crit + "." * (4 - crit)
                    print(f"[STM32 LIVE] t0+{sim_time:6.2f}s | {meter} {val:+.5f}g | STA/LTA: {r:5.2f} | "
                          f"Crit: [{crit_stars}] {crit}/4 | State: {state_tag:<20} | Evts: {total_anomalies_detected}", flush=True)
            else:
                print(f"[STM32 BOARD] {line}", flush=True)
        except Exception:
            time.sleep(0.01)

# -------------------------------------------------------------
# 6. Main Dashboard Construction & Animation
# -------------------------------------------------------------
def build_dashboard():
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(16, 9.5))
    fig.patch.set_facecolor('#070714')

    # Header title
    fig.suptitle('ZIDIS SEISMIC ANALYSER & P-WAVE EARLY WARNING CONSOLE', 
                 fontsize=15, fontweight='bold', color='#00e5ff', fontfamily='monospace', y=0.98)

    # Grid layout: 2 Columns
    # Left Column: Waveform Display (Top: 300s Full Overview, Bottom: 5s Live Window)
    # Right Column: Analyser Module (STA/LTA, Ratio, Multi-Criteria)
    gs = gridspec.GridSpec(3, 2, width_ratios=[1.2, 1.0], height_ratios=[1.3, 1.1, 1.1],
                           left=0.06, right=0.97, top=0.92, bottom=0.07, hspace=0.35, wspace=0.22)

    BG = '#0d0d24'
    GRID = '#191938'
    CYAN = '#00e5ff'
    GREEN = '#76ff03'
    RED = '#ff1744'
    YELLOW = '#ffab00'
    ORANGE = '#ff6d00'
    PURPLE = '#d500f9'

    # ── Left Column: Graphs ──
    # [1] Full Earthquake Waveform Overview
    ax_full = fig.add_subplot(gs[0, 0])
    ax_full.set_facecolor(BG)
    ax_full.grid(True, color=GRID, alpha=0.6)
    ax_full.tick_params(colors='white', labelsize=8)
    ax_full.set_title(f'Full Earthquake Record: {data_source_label}', color=CYAN, fontsize=10, fontweight='bold', pad=6)
    ax_full.set_ylabel('Acceleration (g)', color='white', fontsize=9)
    ax_full.set_xlabel('Time Relative to Rupture Origin (s)', color='white', fontsize=8)

    # Plot complete static waveform in background
    ax_full.plot(full_time_data, full_wave_data, color='#005b7f', linewidth=0.7, label='Full Record (300s)')
    scrubber_line = ax_full.axvline(x=full_time_data[0], color='#ffea00', linewidth=2.0, label='Playback Scrubber')
    ax_full.legend(loc='upper right', fontsize=8, framealpha=0.3)
    ax_full.set_xlim(full_time_data[0], full_time_data[-1])
    max_amp = max(abs(np.min(full_wave_data)), abs(np.max(full_wave_data)), 0.005) * 1.15
    ax_full.set_ylim(-max_amp, max_amp)

    # [2] Real-Time Sliding P-Wave Window
    ax_live = fig.add_subplot(gs[1:, 0])
    ax_live.set_facecolor(BG)
    ax_live.grid(True, color=GRID, alpha=0.6)
    ax_live.tick_params(colors='white', labelsize=8)
    ax_live.set_title('Live Simulated Sensor Feed (Sliding 5-Second Window @ 100Hz)', 
                      color=CYAN, fontsize=11, fontweight='bold', pad=8)
    ax_live.set_ylabel('Acceleration (g)', color='white', fontsize=10)
    ax_live.set_xlabel('Sample Buffer Index (Recent 500 samples)', color='white', fontsize=9)
    line_live, = ax_live.plot([], [], color=CYAN, linewidth=1.2, label='Instantaneous P-Wave')
    ax_live.axhline(0, color='#333366', linewidth=0.8, linestyle='--')
    ax_live.legend(loc='upper right', fontsize=8, framealpha=0.3)
    ax_live.set_xlim(0, MAX_SLIDING_SAMPLES)
    ax_live.set_ylim(-max_amp, max_amp)

    # Status Banner on Live Waveform
    live_status_text = ax_live.text(0.03, 0.94, '', transform=ax_live.transAxes, fontsize=10,
                                    verticalalignment='top', color='white', fontfamily='monospace',
                                    bbox=dict(boxstyle='round,pad=0.5', facecolor='#12122b', edgecolor=CYAN, alpha=0.85))

    # ── Right Column: Analyser Module ──
    # [3] STA / LTA Tracking
    ax_stalta = fig.add_subplot(gs[0, 1])
    ax_stalta.set_facecolor(BG)
    ax_stalta.grid(True, color=GRID, alpha=0.6)
    ax_stalta.tick_params(colors='white', labelsize=8)
    ax_stalta.set_title('Analyser Module: STA / LTA Tracking', color=GREEN, fontsize=10, fontweight='bold', pad=6)
    ax_stalta.set_ylabel('Moving Avg (g)', color='white', fontsize=8)
    line_sta, = ax_stalta.plot([], [], color=GREEN, linewidth=1.0, label='STA (tau=0.5s)')
    line_lta, = ax_stalta.plot([], [], color=YELLOW, linewidth=1.0, label='LTA (tau=10.0s, Frozen in Trig)')
    ax_stalta.legend(loc='upper right', fontsize=8, framealpha=0.3)
    ax_stalta.set_xlim(0, MAX_SLIDING_SAMPLES)
    ax_stalta.set_ylim(0, 0.01)

    # [4] Dynamic STA/LTA Ratio vs Threshold
    ax_ratio = fig.add_subplot(gs[1, 1])
    ax_ratio.set_facecolor(BG)
    ax_ratio.grid(True, color=GRID, alpha=0.6)
    ax_ratio.tick_params(colors='white', labelsize=8)
    ax_ratio.set_title('STA/LTA Ratio (Primary Energy Detection)', color=RED, fontsize=10, fontweight='bold', pad=6)
    ax_ratio.set_ylabel('Ratio', color='white', fontsize=8)
    line_ratio, = ax_ratio.plot([], [], color=GREEN, linewidth=1.3, label='STA/LTA Ratio')
    ax_ratio.axhline(y=STA_LTA_TRIG, color=RED, linestyle='--', linewidth=1.4, label=f'Trigger ({STA_LTA_TRIG})')
    ax_ratio.axhline(y=STA_LTA_DETRIG, color=YELLOW, linestyle=':', linewidth=1.1, label=f'Detrigger ({STA_LTA_DETRIG})')
    ax_ratio.legend(loc='upper right', fontsize=8, framealpha=0.3)
    ax_ratio.set_xlim(0, MAX_SLIDING_SAMPLES)
    ax_ratio.set_ylim(0, 8.0)

    # [5] Multi-Criteria Fusion Detector
    ax_crit = fig.add_subplot(gs[2, 1])
    ax_crit.set_facecolor(BG)
    ax_crit.grid(True, color=GRID, alpha=0.6)
    ax_crit.tick_params(colors='white', labelsize=8)
    ax_crit.set_title('Multi-Criteria Fusion (STA/LTA + RMS + ZCR + Peak)', color=PURPLE, fontsize=10, fontweight='bold', pad=6)
    ax_crit.set_ylabel('Criteria Count', color='white', fontsize=8)
    ax_crit.set_xlabel('Sample Buffer Index', color='white', fontsize=8)
    line_crit, = ax_crit.plot([], [], color=PURPLE, linewidth=1.8, label='Fired Criteria (0-4)')
    ax_crit.axhline(y=ANALYSER_MIN_CRITERIA, color=ORANGE, linestyle='--', linewidth=1.4, label=f'Alarm Threshold ({ANALYSER_MIN_CRITERIA})')
    ax_crit.set_yticks([0, 1, 2, 3, 4])
    ax_crit.set_yticklabels(['0', '1', '2 [TRIGGER]', '3', '4'])
    ax_crit.legend(loc='upper right', fontsize=8, framealpha=0.3)
    ax_crit.set_xlim(0, MAX_SLIDING_SAMPLES)
    ax_crit.set_ylim(-0.5, 4.5)

    # Alarm Indicator Box
    alarm_box = ax_crit.text(0.03, 0.88, '', transform=ax_crit.transAxes, fontsize=10,
                             verticalalignment='top', color='white', fontfamily='monospace',
                             bbox=dict(boxstyle='round,pad=0.4', facecolor='#19193a', edgecolor=PURPLE, alpha=0.85))

    # ── Interactive Keypress Controls & Conflict Unbinding ──
    for conf_key in ['keymap.home', 'keymap.save', 'keymap.fullscreen', 'keymap.all_axes']:
        if conf_key in plt.rcParams:
            plt.rcParams[conf_key] = []

    def on_key(event):
        handle_command_key(event.key)

    fig.canvas.mpl_connect('key_press_event', on_key)

    # ── Interactive On-Screen Control Buttons ──
    btn_color = '#151532'
    btn_hover = '#282855'
    btn_text_color = '#00e5ff'

    # [1] Pause / Play Button
    ax_btn_pause = fig.add_axes([0.06, 0.015, 0.14, 0.038])
    btn_pause = Button(ax_btn_pause, '❚❚ Pause / Play', color=btn_color, hovercolor=btn_hover)
    btn_pause.label.set_color(btn_text_color)
    btn_pause.label.set_fontsize(9)
    btn_pause.label.set_fontweight('bold')
    btn_pause.on_clicked(lambda event: handle_command_key(' '))

    # [2] Jump to P-Wave Button
    ax_btn_jump = fig.add_axes([0.22, 0.015, 0.16, 0.038])
    btn_jump = Button(ax_btn_jump, '⏩ Jump to P-Wave', color=btn_color, hovercolor=btn_hover)
    btn_jump.label.set_color('#76ff03')
    btn_jump.label.set_fontsize(9)
    btn_jump.label.set_fontweight('bold')
    btn_jump.on_clicked(lambda event: handle_command_key('j'))

    # [3] Speed Up (+) Button
    ax_btn_fast = fig.add_axes([0.40, 0.015, 0.14, 0.038])
    btn_fast = Button(ax_btn_fast, '⚡ Faster (+)', color=btn_color, hovercolor=btn_hover)
    btn_fast.label.set_color('#ffea00')
    btn_fast.label.set_fontsize(9)
    btn_fast.label.set_fontweight('bold')
    btn_fast.on_clicked(lambda event: handle_command_key('+'))

    # [4] Speed Down (-) Button
    ax_btn_slow = fig.add_axes([0.56, 0.015, 0.14, 0.038])
    btn_slow = Button(ax_btn_slow, '🐌 Slower (-)', color=btn_color, hovercolor=btn_hover)
    btn_slow.label.set_color('#ffab00')
    btn_slow.label.set_fontsize(9)
    btn_slow.label.set_fontweight('bold')
    btn_slow.on_clicked(lambda event: handle_command_key('-'))

    # [5] Reset to Start Button
    ax_btn_reset = fig.add_axes([0.72, 0.015, 0.14, 0.038])
    btn_reset = Button(ax_btn_reset, '↺ Reset (t0-60s)', color=btn_color, hovercolor=btn_hover)
    btn_reset.label.set_color('#d500f9')
    btn_reset.label.set_fontsize(9)
    btn_reset.label.set_fontweight('bold')
    btn_reset.on_clicked(lambda event: handle_command_key('r'))

    fig._control_buttons = [btn_pause, btn_jump, btn_fast, btn_slow, btn_reset]

    # ── Animation Update Function ──
    heartbeat_tick = 0
    def animate(frame):
        nonlocal heartbeat_tick
        heartbeat_tick += 1

        if len(samples_buf) < 2:
            live_status_text.set_text("● WAITING FOR SAMPLES... (Initializing stream)\nEnsure board or replay is active.")
            live_status_text.set_color(YELLOW)
            return line_live, scrubber_line, line_sta, line_lta, line_ratio, line_crit, live_status_text

        x = np.arange(len(samples_buf))
        line_live.set_data(x, list(samples_buf))
        line_sta.set_data(x, list(sta_buf))
        line_lta.set_data(x, list(lta_buf))
        line_ratio.set_data(x, list(ratio_buf))
        line_crit.set_data(x, list(criteria_buf))

        # Update Scrubber on Full Waveform
        current_time = float(full_time_data[current_sample_idx])
        scrubber_line.set_xdata([current_time, current_time])

        # Auto-scale Y axes smoothly
        s_arr = list(samples_buf)
        live_max = max(abs(min(s_arr)), abs(max(s_arr)), 0.0002) * 1.3
        ax_live.set_ylim(-live_max, live_max)

        r_arr = list(ratio_buf)
        ratio_max = max(max(r_arr) if r_arr else 5.0, 5.0) * 1.15
        ax_ratio.set_ylim(0, ratio_max)

        sta_max = max(max(list(sta_buf)), max(list(lta_buf)), 0.0005) * 1.3
        ax_stalta.set_ylim(0, sta_max)

        # Status text update with live pulsing dot
        curr_ratio = r_arr[-1] if r_arr else 0.0
        curr_crit = criteria_buf[-1] if criteria_buf else 0
        curr_sample = s_arr[-1] if s_arr else 0.0
        pulse = "●" if (heartbeat_tick % 10 < 5) else "○"

        if anomaly_active:
            status_str = f"*** {pulse} DANGER: P-WAVE ANOMALY DETECTED! ***"
            text_color = RED
            border_color = RED
            line_live.set_color(RED)
        else:
            status_str = f"{pulse} LIVE MONITORING (Normal Ambient Floor)"
            text_color = CYAN
            border_color = CYAN
            line_live.set_color(CYAN)

        pause_tag = " [PAUSED]" if is_paused else f" [{playback_speed:.1f}x Speed]"
        live_status_text.set_text(
            f"TIME: t0+{current_time:6.2f}s  |  SAMPLE #{current_sample_idx:05d} / {len(full_wave_data)}{pause_tag}\n"
            f"{status_str}\n"
            f"ACCEL: {curr_sample:+.5f}g  |  STA/LTA: {curr_ratio:4.2f}  |  EVENTS DETECTED: {total_anomalies_detected}\n"
            f"Keys: [SPACE]=Pause  [J]=Jump to P-Wave  [R]=Reset  [+/-]=Speed"
        )
        live_status_text.set_color(text_color)
        live_status_text.get_bbox_patch().set_edgecolor(border_color)

        crit_color = RED if curr_crit >= ANALYSER_MIN_CRITERIA else '#a0a0ff'
        alarm_box.set_text(f"Criteria Active: {curr_crit}/4  |  Trigger Events: {total_anomalies_detected}\n"
                           f"Threshold: {ANALYSER_MIN_CRITERIA} Criteria Fired")
        alarm_box.set_color(crit_color)

        return line_live, scrubber_line, line_sta, line_lta, line_ratio, line_crit, live_status_text, alarm_box

    ani = animation.FuncAnimation(fig, animate, interval=40, blit=False, cache_frame_data=False)
    plt.show()

def run_cli_monitor():
    """Terminal-only live monitoring loop (runs without requiring GUI window)."""
    print("\n" + "=" * 78, flush=True)
    print(" ZIDIS Terminal Live Monitor (Console Mode)", flush=True)
    print(" Streaming real-time telemetry directly to terminal...", flush=True)
    print(" Controls: Press Ctrl+C in terminal to stop.", flush=True)
    print("=" * 78 + "\n", flush=True)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[TERMINAL] Monitoring stopped by user.\n", flush=True)

# -------------------------------------------------------------
# 7. Entry Point & CLI
# -------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ZIDIS Live P-Wave Monitor & Simulation Dashboard")
    parser.add_argument("--data", default="tohoku_real_pwave_100hz.npz", help="Path to downloaded .npz data")
    parser.add_argument("--mode", choices=["replay", "live"], default="replay", help="Mode: 'replay' downloaded data or 'live' serial")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier (e.g. 1.0, 2.0)")
    parser.add_argument("--port", default=None, help="Serial COM port for NUCLEO board (e.g. COM5)")
    parser.add_argument("--cli", "--no-gui", action="store_true", dest="cli_mode", help="Run in terminal-only console mode without GUI window")
    args = parser.parse_args()

    playback_speed = max(args.speed, 0.1)

    # 1. Check & Load Real-World Downloaded Dataset
    data_path = args.data
    if not os.path.exists(data_path):
        # Fallback search in directory
        alt = os.path.join(os.path.dirname(__file__), "tohoku_real_pwave_100hz.npz")
        if os.path.exists(alt):
            data_path = alt
        else:
            print(f"[ERROR] Could not find '{data_path}'. Run download_and_check_offline.py first!", flush=True)
            sys.exit(1)

    print(f"[DATA] Loading real earthquake dataset from '{data_path}'...", flush=True)
    loaded = np.load(data_path)
    full_wave_data = loaded['acc_g']
    full_time_data = loaded['time_sec']
    station_name = str(loaded.get('station', 'IU.MAJO'))
    data_source_label = f"Tohoku 2011 ({station_name} @ 100Hz)"
    print(f"[DATA] Successfully loaded {len(full_wave_data)} samples ({len(full_wave_data)/100:.1f} seconds).", flush=True)

    # 2. Check Serial Connection (HIL or Live)
    serial_obj = None
    port_to_use = args.port
    if not port_to_use and args.mode == "live":
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            desc = (p.description or '').lower()
            hwid = (p.hwid or '').lower()
            if '0483:' in hwid or 'stlink' in desc or 'st-link' in desc or 'usb serial' in desc:
                port_to_use = p.device
                print(f"[SERIAL] Auto-detected ST-LINK port: {port_to_use}", flush=True)
                break

    if port_to_use:
        import serial
        try:
            serial_obj = serial.Serial(port_to_use, BAUD_RATE, timeout=0.1)
            print(f"[SERIAL] Successfully connected to {port_to_use} at {BAUD_RATE} baud.", flush=True)
        except Exception as e:
            print(f"[SERIAL] ERROR: Could not open {port_to_use}: {e}", flush=True)
            if args.mode == "live":
                print("[SERIAL] Note: If STM32CubeIDE's internal Console/Terminal tab has COM5 open, please disconnect it there first.", flush=True)
                sys.exit(1)

    # 3. Pre-warm Analyser and Launch Worker Thread
    if args.mode == "replay":
        prewarm_analyser(current_sample_idx)
        feeder_thread = threading.Thread(target=simulation_feeder_worker, args=(serial_obj,), daemon=True)
        feeder_thread.start()
    else:
        if not serial_obj:
            print("[ERROR] '--mode live' could not establish serial connection.", flush=True)
            sys.exit(1)
        feeder_thread = threading.Thread(target=serial_reader_worker, args=(serial_obj,), daemon=True)
        feeder_thread.start()

    # 4. Start Terminal Keyboard Listener
    start_terminal_keyboard_listener()

    # 5. Open Interactive Dashboard or Console Mode
    if args.cli_mode:
        run_cli_monitor()
    else:
        print("[UI] Opening ZIDIS Dual-Pane P-Wave Dashboard...", flush=True)
        print("     [CONTROLS ACTIVE IN TERMINAL & GUI WINDOW]:", flush=True)
        print("       [SPACE]  = Pause / Resume Playback", flush=True)
        print("       [J]      = Jump to P-Wave Arrival (t0 + 170s)", flush=True)
        print("       [+]      = Speed Up (Faster)", flush=True)
        print("       [-]      = Speed Down (Slower)", flush=True)
        print("       [R]      = Reset to Beginning", flush=True)
        print("       [Buttons]= Click on-screen buttons at bottom of GUI", flush=True)
        build_dashboard()
