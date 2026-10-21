#include "zidis_core/dsp.h"
#include <math.h>
#include <string.h>

#define PI 3.14159265358979323846f

// Simple Radix-2 FFT (in-place)
// Assumes n is a power of 2. For ZIDIS, n = 128.
static void fft_radix2(float real[], float imag[], int n) {
    int i, j, k;
    float u_r, u_i, w_r, w_i, t_r, t_i;

    // Bit-reversal permutation
    j = 0;
    for (i = 0; i < n - 1; i++) {
        if (i < j) {
            float tmp = real[i];
            real[i] = real[j];
            real[j] = tmp;
            
            tmp = imag[i];
            imag[i] = imag[j];
            imag[j] = tmp;
        }
        k = n / 2;
        while (k <= j) {
            j -= k;
            k /= 2;
        }
        j += k;
    }

    // Cooley-Tukey decimation-in-time radix-2 FFT
    for (k = 1; k < n; k *= 2) {
        w_r = cosf(PI / k);
        w_i = -sinf(PI / k);
        u_r = 1.0f;
        u_i = 0.0f;

        for (j = 0; j < k; j++) {
            for (i = j; i < n; i += 2 * k) {
                t_r = u_r * real[i + k] - u_i * imag[i + k];
                t_i = u_r * imag[i + k] + u_i * real[i + k];
                
                real[i + k] = real[i] - t_r;
                imag[i + k] = imag[i] - t_i;
                real[i] += t_r;
                imag[i] += t_i;
            }
            // Complex multiplication
            float tmp_u_r = u_r;
            u_r = tmp_u_r * w_r - u_i * w_i;
            u_i = tmp_u_r * w_i + u_i * w_r;
        }
    }
}

void Dsp_Init(DspState_t *state) {
    state->sta = 0.0f;
    state->lta = 0.0f;
    state->is_triggered = false;
    state->trigger_sta_lta_ratio = 0.0f;
    state->window_idx = 0;
    state->window_full = false;
    memset(state->window, 0, sizeof(state->window));
}

// Processes one sample (at 100Hz). Returns true if window is full and ready for extraction.
bool Dsp_ProcessSample(DspState_t *state, float sample) {
    float abs_sample = fabsf(sample);

    // Exponential moving average for STA and LTA
    // alpha = 1 - exp(-dt / tau)
    // dt = 0.01s (100Hz)
    // tau_sta = 0.5s -> alpha_sta = 1 - exp(-0.01/0.5) = 1 - exp(-0.02) = 0.0198
    // tau_lta = 10s -> alpha_lta = 1 - exp(-0.01/10) = 1 - exp(-0.001) = 0.001
    float alpha_sta = 0.0198f;
    float alpha_lta = 0.001f;

    state->sta = (alpha_sta * abs_sample) + ((1.0f - alpha_sta) * state->sta);
    
    // "Critically, the long-term average is frozen while triggered."
    if (!state->is_triggered) {
        state->lta = (alpha_lta * abs_sample) + ((1.0f - alpha_lta) * state->lta);
    }

    // Guard against division by zero
    float lta_safe = state->lta > 0.0001f ? state->lta : 0.0001f;
    float ratio = state->sta / lta_safe;

    // Trigger logic with hysteresis
    if (!state->is_triggered) {
        if (ratio > STA_LTA_TRIG_THRESH) {
            state->is_triggered = true;
            state->trigger_sta_lta_ratio = ratio; // Capture trigger ratio
            state->window_idx = 0;
            state->window_full = false;
        }
    } else {
        if (ratio < STA_LTA_DETRIG_THRESH) {
            state->is_triggered = false;
        }
    }

    // Collect 128 samples after trigger
    if (state->is_triggered && !state->window_full) {
        state->window[state->window_idx++] = sample;
        if (state->window_idx >= ZIDIS_WINDOW_SIZE) {
            state->window_full = true;
            // We do not de-trigger immediately, wait for ratio to drop.
            // But we do signal that we have a window ready for ML.
            return true; 
        }
    }
    
    return false;
}

void Dsp_ExtractFeatures(DspState_t *state, ZidisFeatures_t *out_features) {
    float real[ZIDIS_WINDOW_SIZE];
    float imag[ZIDIS_WINDOW_SIZE];

    // Apply simple windowing (e.g., Hanning) or just copy
    for (int i = 0; i < ZIDIS_WINDOW_SIZE; i++) {
        // Hanning window to reduce spectral leakage
        float multiplier = 0.5f * (1.0f - cosf(2.0f * PI * i / (ZIDIS_WINDOW_SIZE - 1)));
        real[i] = state->window[i] * multiplier;
        imag[i] = 0.0f;
    }

    fft_radix2(real, imag, ZIDIS_WINDOW_SIZE);

    // Compute power spectrum
    // 128-point FFT gives 64 bins (Nyquist = 50Hz, each bin = 50/64 = 0.78125Hz)
    // Bands: 0-2, 2-5, 5-10, 10-20, 20-35, 35-50 Hz
    float band_energies[6] = {0.0f};
    float total_energy = 0.0f;

    for (int i = 1; i < ZIDIS_WINDOW_SIZE / 2; i++) { // Skip DC (bin 0)
        float freq = i * 0.78125f;
        float power = (real[i]*real[i]) + (imag[i]*imag[i]);
        
        int band = -1;
        if (freq < 2.0f)       band = 0;
        else if (freq < 5.0f)  band = 1;
        else if (freq < 10.0f) band = 2;
        else if (freq < 20.0f) band = 3;
        else if (freq < 35.0f) band = 4;
        else if (freq <= 50.0f) band = 5;

        if (band >= 0) {
            band_energies[band] += power;
            total_energy += power;
        }
    }

    if (total_energy < 0.0001f) total_energy = 1.0f; // avoid div by zero

    for (int i = 0; i < 6; i++) {
        out_features->features[i] = band_energies[i] / total_energy; // Fractional energy
    }
    
    // 7th feature is STA/LTA ratio
    out_features->features[6] = state->trigger_sta_lta_ratio;
}

// ══════════════════════════════════════════════════════════════════
//               SEISMIC ANALYSER — Multi-Criteria Detector
// ══════════════════════════════════════════════════════════════════

void Analyser_Init(AnalyserState_t *state) {
    state->sta = 0.0f;
    state->lta = 0.0f;
    state->sta_lta_fired = false;

    memset(state->rms_buffer, 0, sizeof(state->rms_buffer));
    state->rms_idx = 0;
    state->rms_short = 0.0f;
    state->rms_long = 0.05f;  // Pre-seed with expected noise floor
    state->rms_fired = false;

    memset(state->zcr_buffer, 0, sizeof(state->zcr_buffer));
    state->zcr_idx = 0;
    state->zcr_current = 0.0f;
    state->zcr_baseline = 6.0f; // Typical baseline crossings
    state->zcr_fired = false;

    memset(state->peak_buffer, 0, sizeof(state->peak_buffer));
    state->peak_idx = 0;
    state->peak_max = 0.0f;
    state->peak_fired = false;

    state->sustained_count = 0;
    state->sustained_fired = false;

    state->energy_criteria_count = 0;
    state->non_energy_criteria_count = 0;
    state->criteria_count = 0;
    state->anomaly_detected = false;

    state->onset_start_ms = 0;
    state->detection_latency_ms = 0;
    state->last_trigger_ms = 0;
    state->in_cooldown = false;

    state->fault_status = SENSOR_OK;
    state->last_sample = 0.0f;
    state->flatline_count = 0;
    state->clipped_count = 0;
}

bool Analyser_ProcessSample(AnalyserState_t *state, float sample, uint32_t time_ms) {
    // ──────────────────────────────────────────
    // 0. Sensor Fault Diagnostics (#13)
    // ──────────────────────────────────────────
    if (isnan(sample) || isinf(sample)) {
        state->fault_status = SENSOR_FAULT_INVALID;
        return false;
    }

    float abs_sample = fabsf(sample);

    // Flatline / Disconnected wire detection
    if (fabsf(sample - state->last_sample) < SENSOR_FAULT_DIFF_THRESH) {
        state->flatline_count++;
        if (state->flatline_count > SENSOR_FAULT_FLATLINE_LIMIT) {
            state->fault_status = SENSOR_FAULT_FLATLINE;
            return false;
        }
    } else {
        state->flatline_count = 0;
        if (state->fault_status == SENSOR_FAULT_FLATLINE) {
            state->fault_status = SENSOR_OK;
        }
    }
    state->last_sample = sample;

    // Saturation / Clipping detection
    if (abs_sample >= SENSOR_FAULT_CLIP_THRESH) {
        state->clipped_count++;
        if (state->clipped_count > SENSOR_FAULT_CLIP_LIMIT) {
            state->fault_status = SENSOR_FAULT_CLIPPED;
            return false;
        }
    } else {
        state->clipped_count = 0;
        if (state->fault_status == SENSOR_FAULT_CLIPPED) {
            state->fault_status = SENSOR_OK;
        }
    }

    // ── Cooldown check (2 seconds after last trigger) ──
    if (state->in_cooldown) {
        if (time_ms - state->last_trigger_ms > 2000) {
            state->in_cooldown = false;
        }
    }

    // ──────────────────────────────────────────
    // Criterion 1: STA/LTA Ratio (Energy)
    // ──────────────────────────────────────────
    float alpha_sta = 0.0198f;  // tau = 0.5s
    float alpha_lta = 0.001f;   // tau = 10s

    state->sta = (alpha_sta * abs_sample) + ((1.0f - alpha_sta) * state->sta);

    if (!state->sta_lta_fired) {
        state->lta = (alpha_lta * abs_sample) + ((1.0f - alpha_lta) * state->lta);
    }

    float lta_safe = state->lta > 0.0001f ? state->lta : 0.0001f;
    float sta_lta_ratio = state->sta / lta_safe;

    state->sta_lta_fired = (sta_lta_ratio > STA_LTA_TRIG_THRESH);

    // Reset LTA freeze when ratio drops
    if (sta_lta_ratio < STA_LTA_DETRIG_THRESH) {
        state->sta_lta_fired = false;
        state->onset_start_ms = 0;
    } else if (state->onset_start_ms == 0 && sta_lta_ratio > 1.8f) {
        // Track the moment energy started rising
        state->onset_start_ms = time_ms;
    }

    // ──────────────────────────────────────────
    // Criterion 2: RMS Energy Jump (Energy)
    // ──────────────────────────────────────────
    float sample_sq = sample * sample;
    state->rms_buffer[state->rms_idx] = sample_sq;
    state->rms_idx = (state->rms_idx + 1) % ANALYSER_RMS_WINDOW;

    // Compute short-window RMS
    float rms_sum = 0.0f;
    for (int i = 0; i < ANALYSER_RMS_WINDOW; i++) {
        rms_sum += state->rms_buffer[i];
    }
    state->rms_short = sqrtf(rms_sum / ANALYSER_RMS_WINDOW);

    // Update long-term RMS average (exponential, tau = 15s)
    float alpha_rms_long = 0.00067f;
    if (!state->rms_fired) {
        state->rms_long = (alpha_rms_long * state->rms_short)
                        + ((1.0f - alpha_rms_long) * state->rms_long);
    }

    float rms_long_safe = state->rms_long > 0.001f ? state->rms_long : 0.001f;
    state->rms_fired = (state->rms_short / rms_long_safe) > ANALYSER_RMS_RATIO_THRESH;

    // ──────────────────────────────────────────
    // Criterion 3: Zero-Crossing Rate (Non-Energy / Dynamics) (#7)
    // ──────────────────────────────────────────
    state->zcr_buffer[state->zcr_idx] = sample;
    state->zcr_idx = (state->zcr_idx + 1) % ANALYSER_ZCR_WINDOW;

    // Deadband hysteresis zero-crossing logic to ignore noise-floor micro-chatter
    float deadband = 0.25f * lta_safe;
    int crossings = 0;
    int last_sign = 0; // -1 = negative, +1 = positive

    for (int i = 0; i < ANALYSER_ZCR_WINDOW; i++) {
        int idx = (state->zcr_idx + i) % ANALYSER_ZCR_WINDOW;
        float val = state->zcr_buffer[idx];
        if (val > deadband) {
            if (last_sign == -1) crossings++;
            last_sign = 1;
        } else if (val < -deadband) {
            if (last_sign == 1) crossings++;
            last_sign = -1;
        }
    }
    state->zcr_current = (float)crossings;

    // P-waves oscillate within 2 to 18 crossings per 0.5s (2 - 18 Hz passband)
    state->zcr_fired = (crossings >= ZCR_MIN_SEISMIC_CROSSINGS &&
                        crossings <= ZCR_MAX_SEISMIC_CROSSINGS &&
                        state->rms_short > (1.5f * state->rms_long));

    // ──────────────────────────────────────────
    // Criterion 4: Peak Amplitude (Energy)
    // ──────────────────────────────────────────
    state->peak_buffer[state->peak_idx] = abs_sample;
    state->peak_idx = (state->peak_idx + 1) % ANALYSER_RMS_WINDOW;

    state->peak_max = 0.0f;
    for (int i = 0; i < ANALYSER_RMS_WINDOW; i++) {
        if (state->peak_buffer[i] > state->peak_max) {
            state->peak_max = state->peak_buffer[i];
        }
    }
    state->peak_fired = (state->peak_max > ANALYSER_PEAK_THRESH);

    // ──────────────────────────────────────────
    // Criterion 5: Sustained Wave Persistence (Non-Energy) (#7)
    // ──────────────────────────────────────────
    // Taps/footsteps die within 10-30 ms; tectonic waves sustain energy for > 80 ms
    if (abs_sample > (1.5f * lta_safe) || state->rms_short > (2.0f * state->rms_long)) {
        if (state->sustained_count < 100) state->sustained_count++;
    } else {
        if (state->sustained_count > 0) state->sustained_count--;
    }
    state->sustained_fired = (state->sustained_count >= ANALYSER_SUSTAINED_SAMPLES);

    // ──────────────────────────────────────────
    // Composite Decision: Overlapping Criteria Guard (#7)
    // ──────────────────────────────────────────
    state->energy_criteria_count = 0;
    if (state->sta_lta_fired) state->energy_criteria_count++;
    if (state->rms_fired)     state->energy_criteria_count++;
    if (state->peak_fired)    state->energy_criteria_count++;

    state->non_energy_criteria_count = 0;
    if (state->zcr_fired)       state->non_energy_criteria_count++;
    if (state->sustained_fired) state->non_energy_criteria_count++;

    state->criteria_count = state->energy_criteria_count + state->non_energy_criteria_count;

    // RULE: To prevent hammer taps/bumps from firing on (STA/LTA + RMS) alone,
    // we strictly require at least ONE non-energy criterion!
#if ANALYSER_REQUIRE_NON_ENERGY
    bool detected = (state->energy_criteria_count >= 1) &&
                    (state->non_energy_criteria_count >= 1) &&
                    (state->criteria_count >= ANALYSER_MIN_CRITERIA) &&
                    !state->in_cooldown;
#else
    bool detected = (state->criteria_count >= ANALYSER_MIN_CRITERIA) && !state->in_cooldown;
#endif

    if (detected) {
        state->anomaly_detected = true;
        state->last_trigger_ms = time_ms;
        state->in_cooldown = true;
        state->detection_latency_ms = (state->onset_start_ms > 0 && time_ms >= state->onset_start_ms)
                                      ? (time_ms - state->onset_start_ms)
                                      : 10;
    } else {
        state->anomaly_detected = false;
    }

    return detected;
}
