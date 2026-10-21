#ifndef ZIDIS_CORE_DSP_H
#define ZIDIS_CORE_DSP_H

#include "config.h"
#include <stdbool.h>

// Feature vector: 6 frequency bands + STA/LTA ratio
#define ZIDIS_NUM_FEATURES 7

typedef struct {
    float features[ZIDIS_NUM_FEATURES];
} ZidisFeatures_t;

// DSP State for continuous processing
typedef struct {
    float sta;
    float lta;
    bool  is_triggered;
    float trigger_sta_lta_ratio;
    
    // Circular buffer for 128 samples (triggered window)
    float window[ZIDIS_WINDOW_SIZE];
    int   window_idx;
    bool  window_full;
} DspState_t;

// ── Sensor Fault Diagnostics (#13) ──
typedef enum {
    SENSOR_OK = 0,
    SENSOR_FAULT_FLATLINE,
    SENSOR_FAULT_CLIPPED,
    SENSOR_FAULT_INVALID
} SensorFault_t;

// ── Seismic Analyser State ──
// Multi-criteria anomaly detector that runs on every sample
typedef struct {
    // ── Energy Criteria ──
    float sta;
    float lta;
    bool  sta_lta_fired;

    float rms_buffer[ANALYSER_RMS_WINDOW];
    int   rms_idx;
    float rms_short;         // RMS of recent samples
    float rms_long;          // Long-term average RMS (exponential)
    bool  rms_fired;

    float peak_buffer[ANALYSER_RMS_WINDOW]; // Reuse same window size
    int   peak_idx;
    float peak_max;           // Max |sample| in recent window
    bool  peak_fired;

    // ── Non-Energy / Waveform Dynamics Criteria (#7) ──
    float zcr_buffer[ANALYSER_ZCR_WINDOW];
    int   zcr_idx;
    float zcr_current;       // Current ZCR in window
    float zcr_baseline;      // Long-term average ZCR (exponential)
    bool  zcr_fired;

    // Sustained duration / Persistence (impulse vs continuous wave)
    uint32_t sustained_count;// Consecutive samples above baseline
    bool     sustained_fired;// True if duration >= ANALYSER_SUSTAINED_SAMPLES

    // Composite classification
    int   energy_criteria_count;     // Criteria 1, 2, 4
    int   non_energy_criteria_count; // Criteria 3 (ZCR), Sustained duration
    int   criteria_count;            // Total criteria fired
    bool  anomaly_detected;          // True if valid multi-criteria detection

    // Latency & Timing Measurement (#5)
    uint32_t onset_start_ms;
    uint32_t detection_latency_ms;
    uint32_t last_trigger_ms;
    bool     in_cooldown;

    // Sensor Fault Monitoring (#13)
    SensorFault_t fault_status;
    float    last_sample;
    uint32_t flatline_count;
    uint32_t clipped_count;
} AnalyserState_t;

void Dsp_Init(DspState_t *state);
bool Dsp_ProcessSample(DspState_t *state, float sample);
void Dsp_ExtractFeatures(DspState_t *state, ZidisFeatures_t *out_features);

// ── Analyser API ──
void Analyser_Init(AnalyserState_t *state);
bool Analyser_ProcessSample(AnalyserState_t *state, float sample, uint32_t time_ms);

#endif // ZIDIS_CORE_DSP_H
