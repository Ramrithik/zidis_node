"""
false_alarm_test.py
===================
Continuous False-Alarm Stress Test on Extended Background Noise (#8)
Simulates hours of continuous ambient geological noise, diurnal drift,
and intermittent non-earthquake transient impulses (taps, footsteps, bumps).

Compares:
  - Baseline Engine (Old overlapping criteria: STA/LTA + RMS jump fires on impulses)
  - Hardened Engine (New: Requires >= 1 non-energy criterion + hysteresis ZCR + persistence)

Outputs:
  - Total Hours Tested
  - False Trigger Count (Baseline vs Hardened)
  - False Alarm Rate (FAR / hour)
  - Mean Time Between False Alarms (MTBFA)
  - Generates 'false_alarm_benchmark.png'
"""

import sys
import os
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("=" * 65)
print(" ZIDIS: False-Alarm Continuous Stress Test (#8)")
print(" Extended Background Noise & Transient Impulses Benchmark")
print("=" * 65)

# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
TEST_HOURS = 12.0 # 12 Hours of continuous data
SAMPLE_RATE = 100  # 100 Hz
TOTAL_SAMPLES = int(TEST_HOURS * 3600 * SAMPLE_RATE)
print(f"[CONFIG] Simulating {TEST_HOURS:.1f} hours ({TOTAL_SAMPLES:,} samples @ 100 Hz)...")

# -------------------------------------------------------------
# Load Real Geological Noise Seed
# -------------------------------------------------------------
real_data_path = "tohoku_real_pwave_100hz.npz"
real_noise_slice = None

if os.path.exists(real_data_path):
    d = np.load(real_data_path)
    real_noise_slice = d['acc_g'][0:10000] # Clean pre-rupture bedrock noise
    print(f"[DATA] Using real IRIS seismic background noise ({len(real_noise_slice)} samples) as seed.")

# -------------------------------------------------------------
# Simulation State Classes
# -------------------------------------------------------------
class AnalyserSim:
    def __init__(self, require_non_energy=False):
        self.require_non_energy = require_non_energy
        self.sta = 0.0005
        self.lta = 0.0005
        self.sta_lta_fired = False

        self.rms_buf = np.zeros(50, dtype=np.float32)
        self.rms_idx = 0
        self.rms_short = 0.0
        self.rms_long = 0.0005
        self.rms_fired = False

        self.zcr_buf = np.zeros(50, dtype=np.float32)
        self.zcr_idx = 0
        self.zcr_fired = False

        self.peak_buf = np.zeros(50, dtype=np.float32)
        self.peak_idx = 0
        self.peak_fired = False

        self.sustained_count = 0
        self.sustained_fired = False

        self.cooldown_ticks = 0
        self.false_alarm_count = 0
        self.false_alarm_timestamps = []

    def process(self, sample, tick):
        if self.cooldown_ticks > 0:
            self.cooldown_ticks -= 1

        abs_sample = abs(sample)

        # 1. STA/LTA
        alpha_sta = 0.0198
        alpha_lta = 0.001
        self.sta = (alpha_sta * abs_sample) + ((1.0 - alpha_sta) * self.sta)
        if not self.sta_lta_fired:
            self.lta = (alpha_lta * abs_sample) + ((1.0 - alpha_lta) * self.lta)
        lta_safe = max(self.lta, 0.0001)
        ratio = self.sta / lta_safe

        self.sta_lta_fired = (ratio > 3.0)
        if ratio < 1.5:
            self.sta_lta_fired = False

        # 2. RMS Energy Jump
        self.rms_buf[self.rms_idx] = sample * sample
        self.rms_idx = (self.rms_idx + 1) % 50
        self.rms_short = np.sqrt(np.mean(self.rms_buf))

        alpha_rms = 0.00067
        if not self.rms_fired:
            self.rms_long = (alpha_rms * self.rms_short) + ((1.0 - alpha_rms) * self.rms_long)
        rms_safe = max(self.rms_long, 0.0001)
        self.rms_fired = (self.rms_short / rms_safe) > 4.0

        # 3. ZCR
        self.zcr_buf[self.zcr_idx] = sample
        self.zcr_idx = (self.zcr_idx + 1) % 50

        if not self.require_non_energy:
            # Old simplistic ZCR logic
            crossings = 0
            for j in range(1, 50):
                p = self.zcr_buf[(self.zcr_idx + j - 1) % 50]
                c = self.zcr_buf[(self.zcr_idx + j) % 50]
                if (p >= 0 and c < 0) or (p < 0 and c >= 0):
                    crossings += 1
            self.zcr_fired = (crossings > 12)
        else:
            # New hysteresis ZCR seismic passband check (#7):
            # Passes 1.0 - 8.0 Hz (1 - 8 crossings / 0.5s); rejects high-frequency impulses
            deadband = 0.20 * lta_safe
            crossings = 0
            last_sign = 0
            for j in range(50):
                val = self.zcr_buf[(self.zcr_idx + j) % 50]
                if val > deadband:
                    if last_sign == -1: crossings += 1
                    last_sign = 1
                elif val < -deadband:
                    if last_sign == 1: crossings += 1
                    last_sign = -1
            self.zcr_fired = (1 <= crossings <= 8)

        # 4. Peak
        self.peak_buf[self.peak_idx] = abs_sample
        self.peak_idx = (self.peak_idx + 1) % 50
        self.peak_fired = (np.max(self.peak_buf) > 0.002)

        # 5. Sustained Duration (#7)
        if abs_sample > (1.5 * lta_safe) or self.rms_short > (2.0 * self.rms_long):
            self.sustained_count = min(self.sustained_count + 1, 100)
        else:
            self.sustained_count = max(self.sustained_count - 1, 0)
        self.sustained_fired = (self.sustained_count >= 8)

        # Decision
        energy_count = int(self.sta_lta_fired) + int(self.rms_fired) + int(self.peak_fired)
        non_energy_count = int(self.zcr_fired) + int(self.sustained_fired)
        total_count = energy_count + non_energy_count

        if not self.require_non_energy:
            # Old logic: fires on any 2 criteria (e.g. STA/LTA + RMS)
            detected = (total_count >= 2) and (self.cooldown_ticks == 0)
        else:
            # New logic (#7): strictly requires >= 1 non-energy criterion!
            detected = (energy_count >= 1) and (non_energy_count >= 1) and (total_count >= 2) and (self.cooldown_ticks == 0)

        if detected:
            self.false_alarm_count += 1
            self.false_alarm_timestamps.append(tick / (SAMPLE_RATE * 3600.0)) # in hours
            self.cooldown_ticks = 200 # 2 seconds debounce

baseline_eng = AnalyserSim(require_non_energy=False)
hardened_eng = AnalyserSim(require_non_energy=True)

# -------------------------------------------------------------
# Execute Continuous Stream
# -------------------------------------------------------------
print("[STREAM] Running continuous noise stream with periodic non-earthquake mechanical transients...")

block_size = 360000 # 1 hour chunks
num_chunks = int(TOTAL_SAMPLES / block_size)

np.random.seed(123)
global_tick = 0
total_impulses_injected = 0

start_wall_time = time.time()

for chunk in range(num_chunks):
    # 1. Base real-world microseismic noise + slight pink noise drift
    noise = np.random.normal(0, 0.00015, block_size)
    if real_noise_slice is not None:
        rep = int(block_size / len(real_noise_slice)) + 1
        real_repeated = np.tile(real_noise_slice, rep)[:block_size]
        noise += real_repeated * np.random.uniform(0.8, 1.2)
        
    # Diurnal low-frequency thermal drift
    t_chunk = np.arange(block_size) / (SAMPLE_RATE * 3600.0) + chunk
    diurnal = 0.00008 * np.sin(2 * np.pi * t_chunk / 24.0)
    noise += diurnal

    # 2. Inject sporadic non-earthquake mechanical impulses (hammer taps, footsteps, door slams)
    # Average 15 impulses per hour
    num_impulses = np.random.poisson(15)
    total_impulses_injected += num_impulses
    for _ in range(num_impulses):
        pos = np.random.randint(100, block_size - 100)
        imp_type = np.random.choice(['tap', 'footstep', 'slam'])
        if imp_type == 'tap':
            pulse_len = 20 # 200ms
            t_p = np.arange(pulse_len) / 100.0
            pulse = np.random.uniform(0.003, 0.015) * np.exp(-t_p / 0.02) * np.sin(2 * np.pi * 35.0 * t_p)
        elif imp_type == 'footstep':
            pulse_len = 30
            t_p = np.arange(pulse_len) / 100.0
            pulse = np.random.uniform(0.001, 0.005) * np.exp(-t_p / 0.06) * np.sin(2 * np.pi * 12.0 * t_p)
        else: # slam
            pulse_len = 25
            t_p = np.arange(pulse_len) / 100.0
            pulse = np.random.uniform(0.002, 0.008) * np.exp(-t_p / 0.04) * np.sin(2 * np.pi * 25.0 * t_p)
            
        noise[pos:pos+pulse_len] += pulse

    # Feed chunk sample by sample
    for val in noise:
        baseline_eng.process(val, global_tick)
        hardened_eng.process(val, global_tick)
        global_tick += 1

    elapsed = time.time() - start_wall_time
    print(f"  Processed {chunk+1:02d}/{num_chunks:02d} Hours | "
          f"Baseline False Alarms: {baseline_eng.false_alarm_count:3d} | "
          f"Hardened False Alarms: {hardened_eng.false_alarm_count:3d}")

# -------------------------------------------------------------
# Results & Metrics
# -------------------------------------------------------------
far_base = baseline_eng.false_alarm_count / TEST_HOURS
far_hard = hardened_eng.false_alarm_count / TEST_HOURS

mtbfa_base = (TEST_HOURS / baseline_eng.false_alarm_count) if baseline_eng.false_alarm_count > 0 else float('inf')
mtbfa_hard = (TEST_HOURS / hardened_eng.false_alarm_count) if hardened_eng.false_alarm_count > 0 else float('inf')

print("\n" + "=" * 65)
print(" FALSE-ALARM BENCHMARK RESULTS")
print("=" * 65)
print(f" Total Simulated Duration       : {TEST_HOURS:.1f} Hours ({TOTAL_SAMPLES:,} samples)")
print(f" Non-Earthquake Impulses Tested : {total_impulses_injected} events (taps, footsteps, slams)\n")

print(f" [1] BASELINE ENGINE (Old Overlapping Criteria):")
print(f"     False Alarms Triggered     : {baseline_eng.false_alarm_count}")
print(f"     False Alarm Rate (FAR)     : {far_base:.2f} alarms / hour")
print(f"     Mean Time Between Alarms   : {mtbfa_base:.2f} hours\n")

print(f" [2] HARDENED ENGINE (New Non-Energy + Persistence #7):")
print(f"     False Alarms Triggered     : {hardened_eng.false_alarm_count}")
print(f"     False Alarm Rate (FAR)     : {far_hard:.2f} alarms / hour")
mtbfa_str = f"{mtbfa_hard:.2f} hours" if mtbfa_hard < 999 else "Infinite (> 12 hours clean)"
print(f"     Mean Time Between Alarms   : {mtbfa_str}\n")

reduction = ((baseline_eng.false_alarm_count - hardened_eng.false_alarm_count) / max(baseline_eng.false_alarm_count, 1)) * 100.0
print(f" False Alarm Reduction Rate     : {reduction:.1f}% Improvement!")
print("=" * 65)

# -------------------------------------------------------------
# Generate Benchmark Plot
# -------------------------------------------------------------
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
fig.patch.set_facecolor('#070714')

# Timeline of False Alarms
ax1.set_facecolor('#0d0d24')
ax1.grid(True, color='#191938', alpha=0.6)
ax1.set_title(f'12-Hour Continuous False Alarm Benchmark (Background Noise + Impulses)', color='#00e5ff', fontweight='bold', fontsize=12)
ax1.set_ylabel('Engine Events', color='white')

# Plot event markers
for t in baseline_eng.false_alarm_timestamps:
    ax1.axvline(x=t, color='#ff1744', alpha=0.7, linewidth=1.2, linestyle=':')
ax1.plot([], [], color='#ff1744', linewidth=1.5, label=f'Baseline False Triggers (Total = {baseline_eng.false_alarm_count})')

for t in hardened_eng.false_alarm_timestamps:
    ax1.axvline(x=t, color='#76ff03', linewidth=2.0)
ax1.plot([], [], color='#76ff03', linewidth=2.0, label=f'Hardened False Triggers (Total = {hardened_eng.false_alarm_count})')

ax1.legend(loc='upper right', framealpha=0.3)
ax1.set_ylim(0, 1)
ax1.set_yticks([])

# Cumulative False Alarms Curve
ax2.set_facecolor('#0d0d24')
ax2.grid(True, color='#191938', alpha=0.6)
ax2.set_title('Cumulative False Alarms Over 12 Hours', color='#ffea00', fontweight='bold', fontsize=11)
ax2.set_xlabel('Time (Hours)', color='white')
ax2.set_ylabel('Cumulative False Alarms', color='white')

hours_axis = np.linspace(0, TEST_HOURS, 100)
base_cum = [np.sum(np.array(baseline_eng.false_alarm_timestamps) <= h) for h in hours_axis]
hard_cum = [np.sum(np.array(hardened_eng.false_alarm_timestamps) <= h) for h in hours_axis]

ax2.step(hours_axis, base_cum, color='#ff1744', linewidth=2.0, label=f'Baseline (FAR: {far_base:.2f}/hr)')
ax2.step(hours_axis, hard_cum, color='#76ff03', linewidth=2.5, label=f'Hardened (FAR: {far_hard:.2f}/hr)')
ax2.legend(loc='upper left', framealpha=0.3)

plt.tight_layout()
plt.savefig("false_alarm_benchmark.png", dpi=150, facecolor=fig.get_facecolor())
print("[SUCCESS] Benchmark plot saved to 'false_alarm_benchmark.png'.")
print("=" * 65)
