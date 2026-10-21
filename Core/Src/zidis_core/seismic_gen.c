#include "zidis_core/seismic_gen.h"
#include <math.h>

#define PI 3.14159265358979323846f

// ── Simple LCG PRNG (avoids stdlib rand for reproducibility) ──
static uint32_t seismic_rand(SeismicGenState_t *state) {
    state->rng_state = state->rng_state * 1664525u + 1013904223u;
    return state->rng_state;
}

// Returns a float in [0.0, 1.0)
static float seismic_randf(SeismicGenState_t *state) {
    return (float)(seismic_rand(state) >> 8) / 16777216.0f;
}

// Returns a float in [min, max)
static float seismic_randf_range(SeismicGenState_t *state, float min, float max) {
    return min + seismic_randf(state) * (max - min);
}

// ── Initialize a new earthquake event (randomize parameters) ──
static void start_earthquake_event(SeismicGenState_t *state, uint32_t now_ms) {
    state->phase = SEISMIC_PHASE_ONSET;
    state->phase_start_ms = now_ms;

    // Randomize event duration: 2-4 seconds
    state->event_duration_ms = 2000 + (seismic_rand(state) % 2001);

    // Randomize peak amplitude: 0.8g to 2.0g
    state->peak_amplitude = seismic_randf_range(state, 0.8f, 2.0f);

    // Randomize primary frequency: 6-10 Hz (typical P-wave)
    state->freq_primary   = seismic_randf_range(state, 6.0f, 10.0f);
    state->freq_secondary = seismic_randf_range(state, 11.0f, 15.0f);
    state->freq_tertiary  = seismic_randf_range(state, 3.0f, 6.0f);

    // Random frequency drift: -1 to +1 Hz/s
    state->freq_drift_rate = seismic_randf_range(state, -1.0f, 1.0f);

    // Reset phase accumulators with random initial phase
    state->phase_accum_f1 = seismic_randf(state) * 2.0f * PI;
    state->phase_accum_f2 = seismic_randf(state) * 2.0f * PI;
    state->phase_accum_f3 = seismic_randf(state) * 2.0f * PI;

    // Jitter
    state->amplitude_jitter = 1.0f;
    state->jitter_update_counter = 0;

    // Aftershocks: 1-3 small pulses after main event
    state->aftershock_count = 1 + (seismic_rand(state) % 3);
    state->aftershock_gap_ms = 500 + (seismic_rand(state) % 1000);
}

// ── Schedule next quiet-to-event transition ──
static void schedule_next_event(SeismicGenState_t *state, uint32_t now_ms) {
    state->phase = SEISMIC_PHASE_QUIET;
    state->phase_start_ms = now_ms;
    // Next event in 8-20 seconds
    uint32_t quiet_duration = SEISMIC_QUIET_MIN_MS +
                              (seismic_rand(state) % (SEISMIC_QUIET_MAX_MS - SEISMIC_QUIET_MIN_MS));
    state->next_event_ms = now_ms + quiet_duration;
}

// ── Generate background micro-seismic noise ──
static float generate_noise(SeismicGenState_t *state) {
    // Gaussian-ish noise using sum of uniform randoms (Central Limit Theorem)
    float noise = 0.0f;
    for (int i = 0; i < 4; i++) {
        noise += seismic_randf(state) - 0.5f;
    }
    noise *= 0.025f; // Scale to ~±0.05g RMS
    return noise;
}

// ── Generate the earthquake waveform for current time ──
static float generate_earthquake_sample(SeismicGenState_t *state, float t_event) {
    float dt = 0.01f; // 10ms sample period (100Hz)

    // --- Frequency drift: primary freq shifts over time ---
    float f1 = state->freq_primary + state->freq_drift_rate * t_event;
    float f2 = state->freq_secondary;
    float f3 = state->freq_tertiary;

    // --- Advance phase accumulators ---
    state->phase_accum_f1 += 2.0f * PI * f1 * dt;
    state->phase_accum_f2 += 2.0f * PI * f2 * dt;
    state->phase_accum_f3 += 2.0f * PI * f3 * dt;

    // Keep accumulators bounded
    if (state->phase_accum_f1 > 2.0f * PI) state->phase_accum_f1 -= 2.0f * PI;
    if (state->phase_accum_f2 > 2.0f * PI) state->phase_accum_f2 -= 2.0f * PI;
    if (state->phase_accum_f3 > 2.0f * PI) state->phase_accum_f3 -= 2.0f * PI;

    // --- Multi-frequency superposition ---
    float wave = 0.55f * sinf(state->phase_accum_f1)   // Primary P-wave
               + 0.25f * sinf(state->phase_accum_f2)   // Higher harmonic
               + 0.20f * sinf(state->phase_accum_f3);  // Low-freq body wave

    // --- Amplitude jitter: update every ~5 samples for irregular bursts ---
    state->jitter_update_counter++;
    if (state->jitter_update_counter >= 5) {
        state->jitter_update_counter = 0;
        // Jitter: 0.7 to 1.3 (±30% variation)
        state->amplitude_jitter = 0.7f + seismic_randf(state) * 0.6f;
    }
    wave *= state->amplitude_jitter;

    // --- Envelope ---
    float envelope = 1.0f;
    float event_duration_s = (float)state->event_duration_ms / 1000.0f;

    if (state->phase == SEISMIC_PHASE_ONSET) {
        // Exponential ramp-up over ~100ms
        envelope = 1.0f - expf(-t_event * 15.0f);
    } else if (state->phase == SEISMIC_PHASE_BODY) {
        // Sustained with slight decay
        envelope = expf(-t_event * 0.3f);
    } else if (state->phase == SEISMIC_PHASE_CODA) {
        // Faster decay (coda)
        float coda_t = t_event - event_duration_s * 0.7f;
        envelope = expf(-coda_t * 2.0f) * 0.4f;
    } else if (state->phase == SEISMIC_PHASE_AFTERSHOCK) {
        // Short burst envelope
        float burst_t = t_event;
        float burst_env = (1.0f - expf(-burst_t * 20.0f)) * expf(-burst_t * 3.0f);
        envelope = burst_env * 0.3f; // Aftershocks are ~30% of main event
    }

    return state->peak_amplitude * envelope * wave;
}

// ══════════════════════════════════════════════════════════════════
//                         PUBLIC API
// ══════════════════════════════════════════════════════════════════

void SeismicGen_Init(SeismicGenState_t *state, uint32_t seed) {
    state->rng_state = seed ^ 0xDEADBEEF;
    state->phase = SEISMIC_PHASE_QUIET;
    state->phase_start_ms = 0;
    state->phase_accum_f1 = 0.0f;
    state->phase_accum_f2 = 0.0f;
    state->phase_accum_f3 = 0.0f;
    state->freq_primary = 8.0f;
    state->freq_secondary = 12.0f;
    state->freq_tertiary = 5.0f;
    state->peak_amplitude = 1.5f;
    state->amplitude_jitter = 1.0f;
    state->jitter_update_counter = 0;
    state->freq_drift_rate = 0.0f;
    state->aftershock_count = 0;
    state->aftershock_gap_ms = 0;
    state->event_duration_ms = 3000;

    // First earthquake happens 5-12 seconds after boot
    state->next_event_ms = 5000 + (seismic_rand(state) % 7000);
}

float SeismicGen_GetSample(SeismicGenState_t *state, uint32_t current_time_ms) {
    float noise = generate_noise(state);
    uint32_t elapsed = current_time_ms - state->phase_start_ms;

    switch (state->phase) {
        case SEISMIC_PHASE_QUIET:
            // Check if it's time for an earthquake
            if (current_time_ms >= state->next_event_ms) {
                start_earthquake_event(state, current_time_ms);
                // Fall through to onset processing
                return noise + generate_earthquake_sample(state, 0.0f);
            }
            return noise; // Just background noise

        case SEISMIC_PHASE_ONSET: {
            float t = (float)elapsed / 1000.0f;
            // Onset lasts ~150ms, then transition to body
            if (elapsed > 150) {
                state->phase = SEISMIC_PHASE_BODY;
                state->phase_start_ms = current_time_ms;
            }
            return noise + generate_earthquake_sample(state, t);
        }

        case SEISMIC_PHASE_BODY: {
            float t = (float)elapsed / 1000.0f + 0.15f; // Add onset duration
            // Body lasts ~70% of event duration
            uint32_t body_duration = (uint32_t)(state->event_duration_ms * 0.7f);
            if (elapsed > body_duration) {
                state->phase = SEISMIC_PHASE_CODA;
                state->phase_start_ms = current_time_ms;
            }
            return noise + generate_earthquake_sample(state, t);
        }

        case SEISMIC_PHASE_CODA: {
            float event_t = (float)(state->event_duration_ms * 0.7f) / 1000.0f + 0.15f;
            float coda_t = (float)elapsed / 1000.0f;
            float t = event_t + coda_t;
            // Coda lasts ~30% of event duration
            uint32_t coda_duration = (uint32_t)(state->event_duration_ms * 0.3f);
            if (elapsed > coda_duration) {
                // Check for aftershocks
                if (state->aftershock_count > 0) {
                    state->aftershock_count--;
                    state->phase = SEISMIC_PHASE_AFTERSHOCK;
                    state->phase_start_ms = current_time_ms + state->aftershock_gap_ms;
                    // Vary the gap for next aftershock
                    state->aftershock_gap_ms += 200 + (seismic_rand(state) % 500);
                } else {
                    // Event complete, schedule next
                    schedule_next_event(state, current_time_ms);
                }
                return noise;
            }
            return noise + generate_earthquake_sample(state, t);
        }

        case SEISMIC_PHASE_AFTERSHOCK: {
            // Wait for gap, then generate short burst
            if (current_time_ms < state->phase_start_ms) {
                return noise; // Still in gap
            }
            float t = (float)(current_time_ms - state->phase_start_ms) / 1000.0f;
            // Aftershock burst lasts ~500ms
            if (current_time_ms - state->phase_start_ms > 500) {
                if (state->aftershock_count > 0) {
                    state->aftershock_count--;
                    state->phase_start_ms = current_time_ms + state->aftershock_gap_ms;
                    state->aftershock_gap_ms += 200 + (seismic_rand(state) % 500);
                } else {
                    schedule_next_event(state, current_time_ms);
                }
                return noise;
            }
            return noise + generate_earthquake_sample(state, t);
        }

        default:
            return noise;
    }
}
