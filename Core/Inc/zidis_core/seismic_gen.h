#ifndef ZIDIS_CORE_SEISMIC_GEN_H
#define ZIDIS_CORE_SEISMIC_GEN_H

#include "config.h"
#include <stdbool.h>

// ── Seismic Generator State Machine ──
typedef enum {
    SEISMIC_PHASE_QUIET,       // Background micro-seismic noise
    SEISMIC_PHASE_ONSET,       // Sudden P-wave onset (ramp-up)
    SEISMIC_PHASE_BODY,        // Main P-wave body with irregularities
    SEISMIC_PHASE_CODA,        // Decaying tail (coda waves)
    SEISMIC_PHASE_AFTERSHOCK   // Small secondary pulses
} SeismicPhase_t;

typedef struct {
    SeismicPhase_t phase;

    // Timing
    uint32_t phase_start_ms;       // When current phase started
    uint32_t next_event_ms;        // When next earthquake event triggers
    uint32_t event_duration_ms;    // Duration of current event (randomized)

    // Waveform state
    float    phase_accum_f1;       // Phase accumulator for primary frequency
    float    phase_accum_f2;       // Phase accumulator for secondary frequency
    float    phase_accum_f3;       // Phase accumulator for tertiary frequency
    float    freq_primary;         // Current primary frequency (drifts)
    float    freq_secondary;       // Current secondary frequency
    float    freq_tertiary;        // Current tertiary frequency
    float    peak_amplitude;       // Peak amplitude for this event

    // Irregularity state
    float    amplitude_jitter;     // Current jitter multiplier
    uint32_t jitter_update_counter;// Counter for updating jitter
    float    freq_drift_rate;      // How fast primary freq drifts (Hz/s)

    // Aftershock state
    int      aftershock_count;     // How many aftershocks remain
    uint32_t aftershock_gap_ms;    // Gap between aftershocks

    // PRNG state (simple LCG for deterministic randomness)
    uint32_t rng_state;
} SeismicGenState_t;

// ── API ──
void  SeismicGen_Init(SeismicGenState_t *state, uint32_t seed);
float SeismicGen_GetSample(SeismicGenState_t *state, uint32_t current_time_ms);

#endif // ZIDIS_CORE_SEISMIC_GEN_H
