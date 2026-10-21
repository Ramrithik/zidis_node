#ifndef ZIDIS_CORE_CONFIG_H
#define ZIDIS_CORE_CONFIG_H

#include <stdint.h>
#include <stdbool.h>

// Sampling configuration
#define ZIDIS_SAMPLE_RATE_HZ 100
#define ZIDIS_WINDOW_SIZE    128

// STA/LTA Configuration
#define STA_WINDOW_SAMPLES   50   // 0.5s @ 100Hz
#define LTA_WINDOW_SAMPLES   1000 // 10s @ 100Hz
#define STA_LTA_TRIG_THRESH  3.0f
#define STA_LTA_DETRIG_THRESH 1.5f

// ── Seismic Generator Configuration ──
#define SEISMIC_QUIET_MIN_MS      8000   // Min quiet period between events (ms)
#define SEISMIC_QUIET_MAX_MS     20000   // Max quiet period between events (ms)
#define SEISMIC_EVENT_DURATION_MS 3000   // Base earthquake event length (ms)
#define SEISMIC_PEAK_AMPLITUDE    1.5f   // Peak acceleration (g)

// ── Input Source Selection ──
// Set to 1 to replay real-world 2011 Tohoku Mw 9.1 P-wave data
// Set to 0 to use synthetic autonomous wave generator
#define USE_REAL_EARTHQUAKE_DATA   1

// ── Seismic Analyser Configuration ──
#define ANALYSER_RMS_WINDOW        50    // 0.5s RMS sliding window (samples)
#define ANALYSER_ZCR_WINDOW        50    // Zero-crossing rate window (samples)
#if USE_REAL_EARTHQUAKE_DATA
#define ANALYSER_PEAK_THRESH      0.002f // Peak amplitude threshold for real vault data (g)
#else
#define ANALYSER_PEAK_THRESH      0.3f   // Peak amplitude threshold (g)
#endif
#define ANALYSER_RMS_RATIO_THRESH 4.0f   // Short RMS / Long RMS jump threshold
#define ANALYSER_ZCR_RATIO_THRESH 2.0f   // ZCR jump threshold vs baseline
#define ANALYSER_MIN_CRITERIA      2     // Min total criteria to fire for detection

// ── Non-Energy & Waveform Discrimination (#7) ──
#define ANALYSER_REQUIRE_NON_ENERGY  1    // Require at least 1 non-energy criterion to reject hammer taps
#define ANALYSER_SUSTAINED_SAMPLES    8    // Min 8 samples (80 ms) elevated energy (impulse rejection)
#define ZCR_MIN_SEISMIC_CROSSINGS     1    // Min 1 crossing per 0.5s (seismic fundamental ~1-2 Hz)
#define ZCR_MAX_SEISMIC_CROSSINGS     8    // Max 8 crossings per 0.5s (seismic passband <= 8 Hz; rejects high-freq taps > 12)

// ── Sensor Fault Detection (#13) ──
#define SENSOR_FAULT_FLATLINE_LIMIT 300   // 3 seconds of static/zero-variance readings
#if USE_REAL_EARTHQUAKE_DATA
// High-sensitivity seismic vault data: quiet noise is ~2 ug (variance ~4e-12 g^2)
// True dead sensor / disconnected ADC has bitwise identical readings or diff < 1e-12 g
#define SENSOR_FAULT_DIFF_THRESH    1e-12f
#else
// Standard MEMS accelerometer noise floor (~0.5 - 1.0 mg)
#define SENSOR_FAULT_DIFF_THRESH    1e-5f
#endif
#define SENSOR_FAULT_CLIP_THRESH    3.8f  // Near-rail saturation threshold (g)
#define SENSOR_FAULT_CLIP_LIMIT      15   // 150 ms continuous saturation

// ── Alarm Hold-Off & S-P Lead Time (#5, #15) ──
#define ALARM_HOLD_OFF_MS          5000   // 5s hold-off before clearing alarm after shaking ends
#define S_P_DELAY_PER_KM           0.12f  // 0.12 s/km warning time (1/3.5 - 1/6 s per km)

// Network / Quorum configuration
#define ZIDIS_NODE_ID_SELF   1
#define ZIDIS_MAX_NODES      8
#define ZIDIS_QUORUM_FLOOR   2
#define ZIDIS_SLIDING_WINDOW_MS 5000

// Event Classes
typedef enum {
    EVENT_NOISE = 0,
    EVENT_IMPULSE = 1,
    EVENT_EARTHQUAKE = 2
} EventClass_t;

// Claim Structure
typedef struct {
    uint8_t  source_node;
    uint32_t sequence_num;
    uint32_t timestamp_ms;
    uint8_t  event_class;
    float    confidence;
} ClaimPacket_t;

// Beacon Structure
typedef struct {
    uint8_t  source_node;
    uint32_t sequence_num;
    uint32_t timestamp_ms;
} BeaconPacket_t;

#endif // ZIDIS_CORE_CONFIG_H
