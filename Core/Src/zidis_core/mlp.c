#include "zidis_core/mlp.h"
#include <math.h>

/*
 * AUTO-GENERATED WEIGHTS FROM train_zidis_mlp.py
 * Model Architecture: 7-8-3 Multi-Layer Perceptron (MLP)
 * Trained on: 100 Hz STEAD/IRIS Real Seismic + Impulses (Hammer/Footsteps) + Noise
 * Test Accuracy on Unseen Events: 93.6%
 */

#define INPUT_NODES  7
#define HIDDEN_NODES 8
#define OUTPUT_NODES 3

// Weights for Hidden Layer (8 nodes x 7 inputs)
static const float w_hidden[HIDDEN_NODES][INPUT_NODES] = {
    {+0.327011f, +0.200185f, +0.191892f, -0.227230f, -0.133076f, -0.224431f, +0.031842f},
    {-0.112106f, -0.027831f, -0.081815f, +0.028106f, -0.086110f, -0.034688f, -0.014371f},
    {-0.922962f, -0.668585f, -0.957222f, -1.121709f, +1.108521f, +1.805745f, -0.052496f},
    {+1.058148f, +0.961785f, +0.959995f, -0.812185f, -0.726738f, -1.254647f, +0.601120f},
    {+3.347534f, +2.225271f, +1.009036f, -3.078934f, -1.080071f, -1.654391f, -0.341827f},
    {-1.888416f, -1.115664f, -0.445112f, +2.389218f, +0.743401f, +1.113035f, -0.323342f},
    {-3.285217f, -2.262623f, -1.430878f, +3.212409f, +1.368994f, +2.151667f, +0.107057f},
    {-0.018952f, -0.101064f, +0.050838f, +0.014913f, +0.025347f, -0.049108f, -0.015223f}
};

// Biases for Hidden Layer (8 nodes)
static const float b_hidden[HIDDEN_NODES] = {
    +0.092410f, +0.000000f, -1.444933f, -0.153591f, +3.800634f, +1.295899f, -0.929002f, -0.066156f
};

// Weights for Output Layer (3 nodes x 8 inputs)
static const float w_output[OUTPUT_NODES][HIDDEN_NODES] = {
    {-0.119314f, +0.003432f, -0.122270f, -3.039216f, +1.533672f, +0.210056f, -0.712229f, -0.009984f}, // Class 0: NOISE
    {-0.045692f, +0.037902f, +0.364506f, +1.375567f, -1.283242f, +0.287663f, +0.871123f, +0.120001f}, // Class 1: IMPULSE
    {+0.056310f, +0.079355f, -0.378898f, +1.864043f, -0.200490f, -0.595324f, -0.086323f, -0.063605f}  // Class 2: EARTHQUAKE
};

// Biases for Output Layer (3 nodes)
static const float b_output[OUTPUT_NODES] = {
    +0.780940f, -0.067241f, -0.713647f
};

void Mlp_Init(void) {
    // Static weights compiled into flash memory
}

EventClass_t Mlp_Classify(const ZidisFeatures_t *features, float *out_confidence) {
    float hidden_layer[HIDDEN_NODES];
    float output_layer[OUTPUT_NODES];

    // Forward pass: Hidden Layer (ReLU activation)
    for (int i = 0; i < HIDDEN_NODES; i++) {
        float sum = b_hidden[i];
        for (int j = 0; j < INPUT_NODES; j++) {
            sum += features->features[j] * w_hidden[i][j];
        }
        hidden_layer[i] = (sum > 0.0f) ? sum : 0.0f; // ReLU
    }

    // Forward pass: Output Layer
    for (int i = 0; i < OUTPUT_NODES; i++) {
        float sum = b_output[i];
        for (int j = 0; j < HIDDEN_NODES; j++) {
            sum += hidden_layer[j] * w_output[i][j];
        }
        output_layer[i] = sum;
    }

    // Softmax for probability distribution
    float max_val = output_layer[0];
    for(int i = 1; i < OUTPUT_NODES; i++) {
        if (output_layer[i] > max_val) max_val = output_layer[i];
    }
    
    float sum_exp = 0.0f;
    for(int i = 0; i < OUTPUT_NODES; i++) {
        output_layer[i] = expf(output_layer[i] - max_val);
        sum_exp += output_layer[i];
    }
    
    int best_class = 0;
    float best_prob = 0.0f;
    for(int i = 0; i < OUTPUT_NODES; i++) {
        float prob = output_layer[i] / sum_exp;
        if (prob > best_prob) {
            best_prob = prob;
            best_class = i;
        }
    }

    *out_confidence = best_prob;
    return (EventClass_t)best_class;
}
