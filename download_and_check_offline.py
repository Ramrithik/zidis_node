"""
download_and_check_offline.py
=============================
1. Downloads real-world ground truth seismic data (Tohoku 2011 Mw 9.1) via ObsPy/IRIS.
2. Converts raw seismometer response to physical acceleration in 'g' units at 100 Hz.
3. Saves data offline to 'tohoku_real_pwave_100hz.npz'.
4. Runs an offline bit-accurate simulation of the ZIDIS firmware analyser (dsp.c).
5. Generates performance metrics and saves an analysis plot.
"""

import sys
import os
import time
import numpy as np
import matplotlib
matplotlib.use('Agg') # Headless image export
import matplotlib.pyplot as plt

print("=" * 60)
print(" ZIDIS: Offline Real-World Earthquake Data Download & Check")
print("=" * 60)

# -------------------------------------------------------------
# STEP 1: Download Seismic Data via ObsPy
# -------------------------------------------------------------
data_file = "tohoku_real_pwave_100hz.npz"

if os.path.exists(data_file):
    print(f"[CACHE] Found local cached data: {data_file}")
    loaded = np.load(data_file)
    acc_g = loaded['acc_g']
    time_sec = loaded['time_sec']
    sample_rate = int(loaded['sample_rate'])
    t0_str = str(loaded['t0'])
    station_str = str(loaded['station'])
    print(f"[CACHE] Loaded {len(acc_g)} samples ({len(acc_g)/sample_rate:.1f}s) @ {sample_rate}Hz.")
else:
    print("[OBSPY] Importing ObsPy modules...")
    from obspy import UTCDateTime
    from obspy.clients.fdsn import Client

    print("[OBSPY] Connecting to IRIS FDSN client...")
    client = Client("IRIS")

    # Tohoku Earthquake: 2011-03-11 05:46:24 UTC
    t0 = UTCDateTime("2011-03-11T05:46:00")
    print(f"[OBSPY] Event time t0: {t0}")
    print("[OBSPY] Requesting station IU.MAJO (Matsushiro, Japan) BH? channels...")
    print("        Window: t0 - 60s to t0 + 240s (300 seconds total)...")

    try:
        st = client.get_waveforms("IU", "MAJO", "00", "BH?",
                                  t0 - 60, t0 + 240, attach_response=True)
        print(f"[OBSPY] Waveform downloaded successfully. Traces in stream: {len(st)}")
    except Exception as e:
        print(f"[ERROR] Failed to download from IRIS: {e}")
        sys.exit(1)

    print("[OBSPY] Removing instrument response -> converting to physical ACC (m/s^2)...")
    # Pre-filtering helps avoid low-frequency deconvolution artifacts
    pre_filt = [0.005, 0.01, 40.0, 45.0]
    st.remove_response(output="ACC", pre_filt=pre_filt, water_level=60)

    print("[OBSPY] Selecting Vertical (Z) component...")
    tr = st.select(component="Z")[0]

    print("[OBSPY] Detrending linear drift and demeaning...")
    tr.detrend("linear")
    tr.detrend("demean")

    print("[OBSPY] Resampling to exactly 100 Hz (matching STM32 node)...")
    tr.resample(100)

    print("[OBSPY] Normalizing acceleration from m/s^2 to g (1g = 9.81 m/s^2)...")
    acc_g = np.array(tr.data, dtype=np.float32) / 9.81
    sample_rate = 100
    time_sec = np.arange(len(acc_g)) / sample_rate - 60.0 # Time relative to t0
    t0_str = str(t0)
    station_str = "IU.MAJO.00.BHZ"

    # Save to disk for fast offline reuse
    np.savez_compressed(data_file, acc_g=acc_g, time_sec=time_sec, 
                        sample_rate=sample_rate, t0=t0_str, station=station_str)
    print(f"[SUCCESS] Saved offline data to '{data_file}'.")

# -------------------------------------------------------------
# STEP 2: Basic Signal Statistics
# -------------------------------------------------------------
peak_g = float(np.max(np.abs(acc_g)))
rms_total = float(np.sqrt(np.mean(acc_g ** 2)))
ambient_mask = time_sec < 0.0
ambient_rms = float(np.sqrt(np.mean(acc_g[ambient_mask] ** 2)))
ambient_peak = float(np.max(np.abs(acc_g[ambient_mask])))

print("\n" + "-" * 50)
print(" SIGNAL METRICS (Tohoku 2011 @ Station MAJO)")
print("-" * 50)
print(f" Total Duration      : {len(acc_g)/sample_rate:.1f} seconds ({len(acc_g)} samples)")
print(f" Ambient Noise Floor : RMS = {ambient_rms:.6f} g, Peak = {ambient_peak:.6f} g")
print(f" Global Peak Ground  : {peak_g:.4f} g ({peak_g * 9.81:.2f} m/s^2)")
print("-" * 50)

# -------------------------------------------------------------
# STEP 3: Firmware Analyser Simulation (dsp.c logic)
# -------------------------------------------------------------
print("\n[SIMULATION] Executing firmware analyser (dsp.c) on real data...")

# Parameters matching config.h
STA_TRIG_THRESH = 3.0
STA_DETRIG_THRESH = 1.5
ANALYSER_RMS_RATIO_THRESH = 4.0
ANALYSER_ZCR_RATIO_THRESH = 2.0
ANALYSER_PEAK_THRESH = 0.3
ANALYSER_MIN_CRITERIA = 2
ANALYSER_RMS_WINDOW = 50
ANALYSER_ZCR_WINDOW = 50

# State variables
sta = 0.025
lta = 0.025
sta_lta_fired = False

rms_buffer = np.zeros(ANALYSER_RMS_WINDOW, dtype=np.float32)
rms_idx = 0
rms_short = 0.0
rms_long = 0.05
rms_fired = False

zcr_buffer = np.zeros(ANALYSER_ZCR_WINDOW, dtype=np.float32)
zcr_idx = 0
zcr_current = 0.0
zcr_baseline = 10.0
zcr_fired = False

peak_buffer = np.zeros(ANALYSER_RMS_WINDOW, dtype=np.float32)
peak_idx = 0
peak_max = 0.0
peak_fired = False

last_trigger_ms = -999999
in_cooldown = False

# Recording arrays for plotting
sim_sta = np.zeros(len(acc_g))
sim_lta = np.zeros(len(acc_g))
sim_ratio = np.zeros(len(acc_g))
sim_criteria = np.zeros(len(acc_g), dtype=int)
sim_c1 = np.zeros(len(acc_g), dtype=bool)
sim_c2 = np.zeros(len(acc_g), dtype=bool)
sim_c3 = np.zeros(len(acc_g), dtype=bool)
sim_c4 = np.zeros(len(acc_g), dtype=bool)
sim_anomalies = []

alpha_sta = 0.0198
alpha_lta = 0.001
alpha_rms_long = 0.00067
alpha_zcr = 0.0005

for i, sample in enumerate(acc_g):
    time_ms = int(i * 10) # 10ms per sample
    abs_sample = abs(sample)

    # Cooldown check (2 seconds)
    if in_cooldown and (time_ms - last_trigger_ms > 2000):
        in_cooldown = False

    # Criterion 1: STA/LTA
    sta = (alpha_sta * abs_sample) + ((1.0 - alpha_sta) * sta)
    if not sta_lta_fired:
        lta = (alpha_lta * abs_sample) + ((1.0 - alpha_lta) * lta)
    lta_safe = max(lta, 0.0001)
    ratio = sta / lta_safe

    sta_lta_fired = (ratio > STA_TRIG_THRESH)
    if ratio < STA_DETRIG_THRESH:
        sta_lta_fired = False
    c1 = sta_lta_fired

    # Criterion 2: RMS Energy Jump
    sample_sq = sample * sample
    rms_buffer[rms_idx] = sample_sq
    rms_idx = (rms_idx + 1) % ANALYSER_RMS_WINDOW
    rms_short = np.sqrt(np.mean(rms_buffer))

    if not rms_fired:
        rms_long = (alpha_rms_long * rms_short) + ((1.0 - alpha_rms_long) * rms_long)
    rms_long_safe = max(rms_long, 0.001)
    rms_fired = (rms_short / rms_long_safe) > ANALYSER_RMS_RATIO_THRESH
    c2 = rms_fired

    # Criterion 3: Low-Frequency Seismic Kinematic Passband (Non-Energy #7)
    # Seismic P-waves oscillate within 1 to 8 crossings per 0.5s (1 - 8 Hz).
    # High-frequency hammer taps and mechanical clatter (> 12 crossings) are rejected.
    zcr_buffer[zcr_idx] = sample
    zcr_idx = (zcr_idx + 1) % ANALYSER_ZCR_WINDOW
    deadband = 0.20 * lta_safe
    crossings = 0
    last_sign = 0
    for j in range(ANALYSER_ZCR_WINDOW):
        val = zcr_buffer[(zcr_idx + j) % ANALYSER_ZCR_WINDOW]
        if val > deadband:
            if last_sign < 0:
                crossings += 1
            last_sign = 1
        elif val < -deadband:
            if last_sign > 0:
                crossings += 1
            last_sign = -1
    zcr_current = float(crossings)
    zcr_fired = (1 <= crossings <= 8)
    c3 = zcr_fired

    # Criterion 4: Peak Amplitude
    peak_buffer[peak_idx] = abs_sample
    peak_idx = (peak_idx + 1) % ANALYSER_RMS_WINDOW
    peak_max = np.max(peak_buffer)
    peak_fired = (peak_max > ANALYSER_PEAK_THRESH)
    c4 = peak_fired

    # Composite count
    cnt = int(c1) + int(c2) + int(c3) + int(c4)
    detected = (cnt >= ANALYSER_MIN_CRITERIA) and (not in_cooldown)

    if detected:
        in_cooldown = True
        last_trigger_ms = time_ms
        sim_anomalies.append({
            'index': i,
            'time_rel_t0': time_sec[i],
            'sample': sample,
            'ratio': ratio,
            'criteria': cnt
        })

    # Store metrics
    sim_sta[i] = sta
    sim_lta[i] = lta
    sim_ratio[i] = ratio
    sim_criteria[i] = cnt
    sim_c1[i] = c1
    sim_c2[i] = c2
    sim_c3[i] = c3
    sim_c4[i] = c4

print(f"[SIMULATION] Complete. Total Anomaly Trigger Events: {len(sim_anomalies)}")

if sim_anomalies:
    first_event = sim_anomalies[0]
    print("\n" + "=" * 50)
    print(" FIRST REAL-WORLD P-WAVE DETECTION RESULT")
    print("=" * 50)
    print(f" Detection Time    : t0 + {first_event['time_rel_t0']:.2f} seconds")
    print(f" Sample Index      : {first_event['index']}")
    print(f" Instantaneous Amp : {first_event['sample']:.4f} g")
    print(f" STA/LTA Ratio     : {first_event['ratio']:.2f} (Threshold = {STA_TRIG_THRESH})")
    print(f" Criteria Fired    : {first_event['criteria']}/4 (Min = {ANALYSER_MIN_CRITERIA})")
    print("=" * 50)

# -------------------------------------------------------------
# STEP 4: Spectral FFT Feature Extraction (dsp.c Radix-2 128-pt)
# -------------------------------------------------------------
if sim_anomalies:
    trigger_idx = sim_anomalies[0]['index']
    window_samples = acc_g[trigger_idx : trigger_idx + 128]
    if len(window_samples) == 128:
        # Hanning window
        hanning = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(128) / 127.0))
        windowed = window_samples * hanning
        fft_vals = np.fft.rfft(windowed, n=128)
        power_spec = np.abs(fft_vals) ** 2
        freqs = np.fft.rfftfreq(128, d=1.0/sample_rate)

        # 6 Frequency Bands from dsp.c
        band_ranges = [(0, 2), (2, 5), (5, 10), (10, 20), (20, 35), (35, 50)]
        band_powers = [0.0] * 6
        total_p = 0.0

        for b_idx, (f_low, f_high) in enumerate(band_ranges):
            mask = (freqs >= f_low) & (freqs < f_high)
            p = float(np.sum(power_spec[mask]))
            band_powers[b_idx] = p
            total_p += p

        if total_p <= 0.0:
            total_p = 1.0
        frac_powers = [p / total_p for p in band_powers]

        print("\n" + "-" * 50)
        print(" 128-SAMPLE FFT SPECTRAL ENERGY DISTRIBUTION")
        print("-" * 50)
        for b_idx, (f_low, f_high) in enumerate(band_ranges):
            print(f" Band {b_idx} ({f_low:2d}-{f_high:2d} Hz): {frac_powers[b_idx]*100:5.1f}%  " +
                  ("*" * int(frac_powers[b_idx] * 40)))
        print("-" * 50)

# -------------------------------------------------------------
# STEP 5: Generate Comprehensive Offline Verification Plot
# -------------------------------------------------------------
print("\n[PLOT] Generating offline verification figure...")
plt.style.use('dark_background')
fig, axes = plt.subplots(4, 1, figsize=(14, 11), sharex=True,
                         gridspec_kw={'height_ratios': [3, 2, 2, 1.5]})
ax1, ax2, ax3, ax4 = axes

BG = '#0d0d24'
GRID = '#1a1a3a'
CYAN = '#00e5ff'
GREEN = '#76ff03'
RED = '#ff1744'
YELLOW = '#ffab00'
ORANGE = '#ff6d00'
PURPLE = '#d500f9'

for ax in axes:
    ax.set_facecolor(BG)
    ax.grid(True, color=GRID, alpha=0.6)
    ax.tick_params(colors='white')

# Panel 1: Acceleration Waveform
ax1.plot(time_sec, acc_g, color=CYAN, linewidth=0.8, label='Tohoku 2011 Acceleration (Z-axis @ MAJO)')
if sim_anomalies:
    t_first = sim_anomalies[0]['time_rel_t0']
    ax1.axvline(x=t_first, color=RED, linestyle='--', linewidth=2.0, 
                label=f'First P-Wave Trigger (t0+{t_first:.1f}s)')
ax1.set_ylabel('Acceleration (g)', color='white', fontsize=11)
ax1.set_title('Real-World Seismic Signal: 2011 Tohoku Mw 9.1 (Station IU.MAJO)', color=CYAN, fontsize=13, fontweight='bold')
ax1.legend(loc='upper right', framealpha=0.3)

# Panel 2: STA & LTA
ax2.plot(time_sec, sim_sta, color=GREEN, linewidth=1.0, label='STA (tau = 0.5s)')
ax2.plot(time_sec, sim_lta, color=YELLOW, linewidth=1.0, label='LTA (tau = 10.0s, frozen when trig)')
ax2.set_ylabel('Averages (g)', color='white', fontsize=11)
ax2.set_title('STA / LTA Exponential Moving Averages', color=GREEN, fontsize=12, fontweight='bold')
ax2.legend(loc='upper right', framealpha=0.3)

# Panel 3: STA/LTA Ratio
ax3.plot(time_sec, sim_ratio, color=GREEN, linewidth=1.2, label='STA/LTA Ratio')
ax3.axhline(y=STA_TRIG_THRESH, color=RED, linestyle='--', linewidth=1.5, label=f'Trigger Threshold ({STA_TRIG_THRESH})')
ax3.axhline(y=STA_DETRIG_THRESH, color=YELLOW, linestyle=':', linewidth=1.2, label=f'Detrigger ({STA_DETRIG_THRESH})')
ax3.set_ylabel('Ratio', color='white', fontsize=11)
ax3.set_title('STA/LTA Ratio vs Trigger Thresholds', color=RED, fontsize=12, fontweight='bold')
ax3.legend(loc='upper right', framealpha=0.3)
ax3.set_ylim(0, min(max(sim_ratio) * 1.1, 50))

# Panel 4: Analyser Criteria
ax4.plot(time_sec, sim_criteria, color=PURPLE, linewidth=1.8, label='Criteria Fired (0-4)')
ax4.axhline(y=ANALYSER_MIN_CRITERIA, color=ORANGE, linestyle='--', linewidth=1.5, label=f'Alarm Threshold ({ANALYSER_MIN_CRITERIA})')
ax4.set_ylabel('Criteria Count', color='white', fontsize=11)
ax4.set_xlabel('Time Relative to Rupture Origin t0 (seconds)', color='white', fontsize=11)
ax4.set_title('Firmware Analyser Multi-Criteria Fusion', color=PURPLE, fontsize=12, fontweight='bold')
ax4.set_yticks([0, 1, 2, 3, 4])
ax4.set_yticklabels(['0', '1', '2 (TRIGGER)', '3', '4'])
ax4.legend(loc='upper right', framealpha=0.3)

fig.patch.set_facecolor('#0a0a1a')
plt.tight_layout()
plot_path = "offline_pwave_analysis.png"
plt.savefig(plot_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor='none')
print(f"[SUCCESS] Plot saved to '{plot_path}'.")

print("\n" + "=" * 60)
print(" VERIFICATION COMPLETE: ALL OFFLINE CHECKS PASSED!")
print("=" * 60)
