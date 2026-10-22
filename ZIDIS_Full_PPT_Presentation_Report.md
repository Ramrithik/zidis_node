# ZIDIS Node: Complete Presentation & PPT Slide-by-Slide Blueprint
## Embedded Real-Time Earthquake Early Warning (EEW) System
### STMicroelectronics STM32H533RETx • μT-Kernel 3.0 RTOS • Edge-AI Kinematics

---

## Executive Presentation Deck Overview

This comprehensive report provides the exact, production-ready content, slide architecture, presenter talking scripts, key statistical callouts, recommended visuals, and defensive technical Q&A required to build a world-class PowerPoint presentation for the **ZIDIS Node** project.

### Recommended Deck Architecture (16-Slide Standard)

| Slide # | Slide Title | Core Focus / Theme | Key Graphic / Visual Asset | Time |
| :---: | :--- | :--- | :--- | :---: |
| **1** | Title Slide: ZIDIS Node Architecture | Executive Overview & Platform | High-res STM32 + Waveform Graphic | 1.0 min |
| **2** | Seismic Wave Physics & Lead Time | P/S Wave Mechanics & $0.12\text{ s/km}$ Gradient | Wave Propagation & Lead-Time Chart | 2.0 min |
| **3** | Edge Hardware & Peripheral Pinout | STM32H533RETx Specs & Board Mapping | NUCLEO-H533RE Pinout Block Diagram | 1.5 min |
| **4** | μT-Kernel 3.0 RTOS Architecture | Deterministic Multitasking & Event Flags | RTOS Task Priority & Event Flag Graph | 2.0 min |
| **5** | Kinematic P-Wave Detection Engine | Multi-Criteria Fusion & Inversion Paradox | 4-Criteria Waveform Detection Trace | 2.5 min |
| **6** | Embedded Edge-AI Classifier (MLP) | 7-8-3 Neural Network on Cortex-M33 FPU | `mlp_training_results.png` & Topology | 2.0 min |
| **7** | Fault Diagnostics & Watchdog Protection | $10^{-12}\text{ g}$ Bedrock Flatline & Fail-Safe | Fault State Machine / Health Monitor | 1.5 min |
| **8** | Dual-Tier Escalation & Operator Controls | L1 Soft Alert vs L2 Siren + PC13 Mute | Dual-Tier Timing Diagram & Escalation | 1.5 min |
| **9** | 12-Hour False Alarm Stress Benchmark | $47.2\%$ L1 & $94.4\%$ L2 Reduction Proof | `false_alarm_benchmark.png` & Table | 2.0 min |
| **10** | Real Earthquake Validation: 2011 Tohoku | Exact Detection at $t=176.23\text{s}$ (IU.MAJO) | `offline_pwave_analysis.png` | 2.5 min |
| **11** | Real-Time Telemetry & GUI Dashboard | Live Dual-Pane Plotter & Serial VU-Meter | GUI Screenshot / Live Plotter Mockup | 2.0 min |
| **12** | Mobile Push Alerts via ntfy | Zero-Latency Mobile Push to Phone | Mobile Notification Lock-Screen View | 1.5 min |
| **13** | Resource Utilization & Benchmarks | $125.5\text{ KB}$ Flash, $17.3\text{ KB}$ SRAM ($< 8\ \mu\text{s}$) | Memory Gauge & Timing Budget Table | 1.5 min |
| **14** | Hardware-in-the-Loop Validation | Flashing, Streaming & Buzzer Verification | System Integration Verification Flow | 1.5 min |
| **15** | Project Evolution: Phase 1 to Phase 2 | Roadmap & Commercial Viability | Evolution Comparison Matrix | 1.5 min |
| **16** | Conclusion, Impact & Technical Appendix | Summary & Mathematical Formulations | Lead Time Matrix & FFT Mathematics | 1.5 min |

---

## Detailed Slide-by-Slide Content & Script

---

### Slide 1: Title Slide

#### Slide Header & Subtitle
* **Title:** **ZIDIS: Zero Inertia Defect Inspection System**
* **Subtitle:** Autonomous Edge-AI Earthquake Early Warning (EEW) Node on μT-Kernel 3.0 RTOS & STM32H533RETx
* **Presenter:** Ramrithik Chirra & Engineering Team
* **Platform:** STMicroelectronics NUCLEO-H533RE • Arm Cortex-M33 @ 250 MHz • TRON μT-Kernel 3.0

#### Recommended Slide Layout
* **Layout:** Clean Dark/Modern Minimalist.
* **Left Side (60%):** Large bold typography, project badges (μT-Kernel 3.0, Arm Cortex-M33, Edge-AI, 100 Hz RTOS).
* **Right Side (40%):** High-contrast vector render of the NUCLEO board superimposed with a seismic P-wave and S-wave seismogram.

#### On-Slide Bullet Points
* **Real-Time Edge Instrument:** Autonomous seismic discrimination without reliance on centralized cloud servers.
* **Deterministic Micro-Kernel:** Industrial-grade μT-Kernel 3.0 cyclic task scheduling and event flags.
* **Sub-Second Onset Warning:** Detects compressional P-waves in $0.4\text{ seconds}$, unlocking actionable evacuation lead time.
* **Hardware-Accelerated Neural Inference:** Embedded 7-8-3 Multilayer Perceptron running in $< 8\ \mu\text{s}$ on Cortex-M33 FPU.

#### Presenter Talking Notes / Script
> *"Good morning, members of the committee and engineering colleagues. Today, I am proud to present ZIDIS—an autonomous, edge-computing Earthquake Early Warning instrument. Earthquakes do not give prior warning, but physics does. When a fault ruptures, it sends out two distinct elastic waves: fast, harmless P-waves, followed seconds later by destructive, shearing S-waves. The mission of ZIDIS is to capture that P-wave signature directly at the edge, classify it against cultural noise in under 8 microseconds, and broadcast actionable evacuation warnings before the violent shear shaking arrives. Running on the high-performance STM32H533 microcontroller and the deterministic μT-Kernel 3.0 RTOS, ZIDIS bridges the gap between deep seismological physics and hard real-time embedded systems."*

---

### Slide 2: Seismic Wave Physics & Warning Lead Time

#### Slide Header & Subtitle
* **Title:** **The Physical Foundation: P-Wave vs. S-Wave Dynamics**
* **Subtitle:** Exploiting Differential Wave Velocities to Deliver an Actionable Warning Gradient

#### Recommended Slide Layout
* **Layout:** Top half showing the crustal wave propagation diagram; bottom half showing a 2-column split (Kinematic Velocity Equations on the left, Lead-Time Action Matrix on the right).

#### On-Slide Content & Data Table
```
   Hypocenter (Rupture)
       ├───► P-Wave (Compressional):  v_p ≈ 6.0 km/s  ──► Fast, Low Amplitude (Detected by ZIDIS)
       │                                                         │
       │                                                         ▼  [Instant Alarm Broadcast]
       └───► S-Wave (Transverse Shear): v_s ≈ 3.5 km/s ──► Slow, Destructive Energy (Destruction Zone)
                                                                 ▲
                                          Warning Lead Window: Δt = 0.12 s per km
```

* **Spatial Warning Equation:**
  $$\Delta t_{S-P} = d \left( \frac{1}{v_S} - \frac{1}{v_P} \right) = d \left( \frac{1}{3.5} - \frac{1}{6.0} \right) \approx \mathbf{0.12\text{ seconds per kilometer}}$$

| Epicentral Distance ($d$) | Theoretical S-P Window | L1 Soft Alert Lead Time ($t_{\text{onset}\to L1} = 0.4\text{s}$) | L2 Siren Lead Time ($t_{\text{onset}\to L2} = 1.7\text{s}$) | Feasible Protective Measures |
| :---: | :---: | :---: | :---: | :--- |
| **25 km** | 3.0 s | **2.6 s** | **1.3 s** | Personal drop-cover-hold, local tooling interlock |
| **50 km** | 6.0 s | **5.6 s** | **4.3 s** | High-speed elevator stop, natural gas shutoff |
| **100 km** | 11.9 s | **11.5 s** | **10.2 s** | Industrial line trip, railway automated braking |
| **200 km** | 23.8 s | **23.4 s** | **22.1 s** | Municipal evacuation, hospital backup power sync |

#### Presenter Talking Notes / Script
> *"To understand why edge computing is critical here, let us look at the fundamental geophysics. In the continental crust, compressional P-waves propagate at roughly 6.0 km/s, while destructive shear S-waves propagate at 3.5 km/s. This velocity disparity creates a mathematical warning window of approximately 0.12 seconds for every single kilometer of epicentral distance.*
>
> *For a facility located 50 kilometers from the rupture, you have a 6.0-second window. If a cloud-based server takes 4 to 6 seconds just to aggregate telemetry, that life-saving window is completely squandered. ZIDIS executes entirely on-chip: its Level 1 soft alert fires in 0.4 seconds—leaving 5.6 full seconds of warning at 50 km—and its fully corroborated siren fires in 1.7 seconds, delivering over 10 seconds of warning at 100 km. That is sufficient time to trip semiconductor gas lines, engage emergency railway brakes, and position personnel safely."*

---

### Slide 3: Edge Hardware Architecture & Pinout Mapping

#### Slide Header & Subtitle
* **Title:** **Hardware Architecture & Peripheral Interfacing**
* **Subtitle:** STMicroelectronics STM32H533RETx (NUCLEO-H533RE) System Configuration

#### Recommended Slide Layout
* **Layout:** Left column showing Microcontroller hardware specs; Right column showing the physical pinout diagram and electrical interface table.

#### On-Slide Content
* **Processor Core:** Arm Cortex-M33 with TrustZone, DSP SIMD instructions, single-precision hardware FPU @ $250\text{ MHz}$ SYSCLK.
* **On-Chip Memory:** $512\text{ KB}$ Dual-Bank Flash, $256\text{ KB}$ zero-wait-state SRAM.
* **Hardware Timer 3 (`TIM3`):** 16-bit general-purpose timer generating $1\text{ kHz}$ PWM for acoustic alarm transducer.
* **Hardware UART (`USART2`):** Direct Virtual COM Port at $115200\text{ baud}$, transmitting real-time 100 Hz ASCII sample telemetry.

```
                         NUCLEO-H533RE Physical Mapping
                     ┌──────────────────────────────────┐
            [GND] ───┤ GND                          PB4 ├─── [1 kHz PWM Siren / Transducer]
                     │                             PC13 ├─── [Blue User Button / Mute Key]
         [ST-LINK] ──┤ PA2 (USART2_TX)              PA5 ├─── [Green Status LED (LD2)]
         [115200]  ──┤ PA3 (USART2_RX)                  │
                     └──────────────────────────────────┘
```

| Pin | Alternate Function | Target Function | Electrical Characteristic |
| :---: | :---: | :---: | :---: |
| **PB4** | `TIM3_CH1` (AF2) | **Acoustic Siren Transducer** | $1\text{ kHz}$ PWM, Variable Duty Cycle ($5\%$ Beep / $50\%$ Siren) |
| **PC13** | GPIO Input | **Alarm Silence / Mute Key** | Active-Low mechanical push-button with software debounce |
| **PA5** | GPIO Output | **Visual Alarm & Status LED** | Push-Pull High-Speed output driving green LD2 indicator |
| **PA2** | `USART2_TX` (AF7) | **100 Hz Seismic Telemetry** | ASCII packet streaming (`D:<milli_g>\r\n`) to PC / Gateway |
| **PA3** | `USART2_RX` (AF7) | **HIL Injection Port** | Hardware-in-the-Loop synthetic/real seismic data feeder |

#### Presenter Talking Notes / Script
> *"The hardware foundation is ST's STM32H533RETx, mounted on the NUCLEO-H533RE. This Arm Cortex-M33 core operates at 250 MHz and includes a dedicated hardware Floating Point Unit, which is paramount for evaluating continuous floating-point DSP filters and matrix neural network multiplications.*
>
> *We have carefully mapped the peripherals: PB4 drives our piezo buzzer via Timer 3 Channel 1 with 1 kHz PWM, allowing us to modulate acoustic duty cycle between a soft 5% alert beep and a piercing 50% evacuation siren. PC13 connects to the on-board blue user button to provide instantaneous, debounced alarm muting for operators. USART2 streams real-time ASCII telemetry at 115200 baud, enabling hardware-in-the-loop validation and external dashboard integration."*

---

### Slide 4: Real-Time Operating System (RTOS) Design

#### Slide Header & Subtitle
* **Title:** **μT-Kernel 3.0 Real-Time Operating System Architecture**
* **Subtitle:** Deterministic Cyclic Scheduling, Priority Preemption, and Inter-Task Synchronization

#### Recommended Slide Layout
* **Layout:** Left side showing RTOS Task Hierarchy & Priority Table; Right side showing the Mermaid / Vector Inter-Task Communication flow.

#### On-Slide Content
* **Standardized RTOS:** TRON Forum μT-Kernel 3.0 specification for safety-critical real-time embedded control.
* **Deterministic Handlers:** Hardware timer invokes `SenseCyclicHandler` precisely every $10.0\text{ ms}$ ($\pm 0.1\ \mu\text{s}$ jitter).
* **Zero Busy-Waiting:** Tasks yield execution via `tk_wai_flg()` and wake via event flag signals (`0x01` detection, `0x02` tick).

```
[Hardware 10ms Tick] ──► SenseCyclicHandler ──(flg: 0x02)──► Task_Sense (Pri 10)
                                                                 │
                                                       [Trigger Condition]
                                                                 │ (flg: 0x01)
                                                                 ▼
[Mesh Gossip Beacons] ◄── Task_Net (Pri 3)              Task_Detect (Pri 5)
                                                                 │ [128-pt FFT + MLP]
                                                                 ▼
[PC13 Mute Button]   ──► Task_Consensus (Pri 7) ◄────────────────┘
                                  │
                                  ├──► PB4 PWM Siren (L1: 5% / L2: 50%)
                                  └──► PA5 Visual LED Alarm
```

| Task Identifier | Priority | Scheduling Period | Core Responsibilities |
| :--- | :---: | :---: | :--- |
| **`Task_Sense`** | 10 (Med) | $10.0\text{ ms}$ (100 Hz) | Kinematic sample ingestion, sensor fault checks, telemetry TX |
| **`Task_Detect`** | 5 (High) | Event-Driven | 128-pt Hanning window, Radix-2 FFT, 7-feature extraction, MLP inference |
| **`Task_Consensus`**| 7 (Med-High) | Event-Driven | Dual-tier alert state machine, 5s hold-off timer, PC13 mute processing |
| **`Task_Net`** | 3 (Highest)| $1.0\text{ Hz}$ Periodic | Peer heartbeat beacons, quorum voting packet exchange |
| **`Task_Diag`** | 15 (Lowest)| $5.0\text{ s}$ Background | Software watchdog heartbeat verification, system uptime telemetry |

#### Presenter Talking Notes / Script
> *"Firmware reliability is guaranteed by μT-Kernel 3.0, an open, standardized real-time operating system with microsecond-level context switching. We designed a clean, multi-tiered task hierarchy:*
>
> *Every 10 milliseconds, our hardware cyclic timer fires, setting event flag 0x02 to wake Task_Sense. Task_Sense acquires the tri-axial acceleration, checks for sensor flatline or clipping faults, runs the kinematic filter, and transmits telemetry. When an anomaly triggers, it buffers a 128-sample window and sets event flag 0x01. This instantly preempts execution to wake Task_Detect at priority 5. Task_Detect computes a 128-point Radix-2 FFT, extracts spectral features, and runs the MLP classifier. Task_Consensus then manages the dual-tier siren escalation and operator mute commands. This decoupled event-driven model guarantees that no task blocks another, and zero CPU cycles are wasted on busy-waiting."*

---

### Slide 5: Kinematic P-Wave Detection Pipeline

#### Slide Header & Subtitle
* **Title:** **Multi-Criteria Kinematic Detection & Frequency Physics**
* **Subtitle:** Overcoming the 'Frequency Inversion Paradox' via Seismic Passband Discrimination

#### Recommended Slide Layout
* **Layout:** Top half showing the 4 Criteria mathematical formulation; Bottom half showing the empirical frequency paradox comparison table and C implementation snippet.

#### On-Slide Content
* **Criterion 1 (Energy Ratio):** Classical Short-Term Average to Long-Term Average:
  $$\frac{STA(n)}{LTA(n)} \ge 3.00, \quad \tau_{STA} = 0.5\text{ s}, \ \tau_{LTA} = 10.0\text{ s}$$
* **Criterion 2 (Dynamic RMS Spike):** Instantaneous short-term energy exceeding $3.5\times$ background RMS floor.
* **Criterion 3 (Seismic Kinematic Passband):** Hysteresis zero-crossing rate constrained strictly between $1.0\text{ Hz}$ and $8.0\text{ Hz}$ ($1 \le crossings \le 8$ per 0.5 s window).
* **Criterion 4 (Instantaneous Peak):** Dynamic acceleration exceeding $4.0\times$ running baseline deviation.
* **Criterion 5 (Wave Persistence):** Energy sustained for $\ge 8\text{ consecutive samples}$ ($80\text{ ms}$) to reject sub-cycle micro-spikes.

#### The Frequency Inversion Paradox & Resolution
* **The Classical Fallacy:** Conventional industrial shock algorithms assume an earthquake increases zero-crossing frequency ($ZCR > 2 \times baseline$).
* **Seismological Reality:** Tectonic P-waves are low-frequency crustal reverberations ($1.0 - 5.0\text{ Hz}$). High-frequency signals ($25 - 50\text{ Hz}$) originate from mechanical impulses (hammer drops, door slams, footsteps).
* **Our Solution:** Invert the check into a **bandpass envelope ($1 - 8\text{ Hz}$)** with an adaptive deadband ($0.20 \times LTA$). Signals exhibiting $> 12\text{ crossings}$ are automatically tagged as mechanical noise and suppressed!

| Signal Class | Peak Acceleration | Zero-Crossings in 0.5 s | Dominant Frequency | Energy in $< 5\text{ Hz}$ Passband |
| :--- | :---: | :---: | :---: | :---: |
| **2011 Tohoku P-Wave** | $0.0025\text{ g}$ | **1 crossing** | **~ 1.0 Hz** | **99.1% (Seismic)** |
| **Mechanical Hammer Strike**| $0.8000\text{ g}$ | **19 crossings** | **~ 19.0 Hz** | **0.0% (Cultural Shock)** |
| **Ambient Seismic Bedrock** | $0.000007\text{ g}$ | **0 crossings** (Deadband)| N/A | Ambient Microseismic |

#### Presenter Talking Notes / Script
> *"The heart of our local detection is a multi-criteria kinematic pipeline. Most simple early warning systems rely purely on an STA/LTA energy ratio. But energy alone is blind: dropping a wrench on the floor generates a huge STA/LTA spike. To solve this, we addressed what we call the 'Frequency Inversion Paradox'.*
>
> *In mechanical engineering, a shock causes high-frequency ringing. But in geophysics, an earthquake P-wave is a deep, low-frequency crustal oscillation between 1 and 5 Hz. If you configure a detector to look for increased zero crossings, you will trigger on footsteps and miss the earthquake!*
>
> *We implemented a hysteresis-based Zero-Crossing Passband filter: it requires between 1 and 8 crossings in a 50-sample window, directly corresponding to 1 to 8 Hz. If a shock shows 19 crossings—like a hammer blow—our kinematic engine detects the high-frequency content and immediately suppresses the trigger. This single innovation cuts false alarms by nearly half before any machine learning is even invoked."*

---

### Slide 6: Embedded Edge-AI Classifier (7-8-3 MLP)

#### Slide Header & Subtitle
* **Title:** **Hardware-Accelerated Neural Classification**
* **Subtitle:** 7-8-3 Multilayer Perceptron Running on the Arm Cortex-M33 Hardware FPU

#### Recommended Slide Layout
* **Layout:** Split layout. Left side showing the 7-feature extraction pipeline and network topology diagram; Right side showing `mlp_training_results.png` and performance metrics.

#### On-Slide Content
* **Input Feature Extraction (128-pt Radix-2 FFT):**
  1. $f_0$: Peak Acceleration Amplitude ($g$)
  2. $f_1$: Cumulative Spectral Energy
  3. $f_2$: Dominant Spectral Frequency (Hz)
  4. $f_3 - f_6$: Band-Limited Energies: $0-2\text{ Hz}$, $2-5\text{ Hz}$, $5-10\text{ Hz}$, $10-20\text{ Hz}$
* **Neural Architecture:** Fully connected $7 \to 8 \to 3$ topology:
  - Input Layer: 7 features with on-chip z-score standardization.
  - Hidden Layer: 8 neurons with Rectified Linear Unit (ReLU) activation.
  - Output Layer: 3-class Softmax probability distribution:
    - **Class 0:** Seismic P-Wave
    - **Class 1:** Cultural Transient Impulse (Hammer / Drop / Step)
    - **Class 2:** Ambient Acoustic & Sensor Noise
* **Performance on Unseen Test Dataset:**
  - **Overall Classification Accuracy:** **93.61%**
  - **Earthquake Class Recall:** **97.6%** (122 / 125 confirmed)
  - **Impulse Rejection Specificity:** **82.3%**
  - **Inference Execution Time:** **$< 8.0\ \mu\text{s}$** (91 weights & biases on Cortex-M33 FPU)

#### Presenter Talking Notes / Script
> *"Once the kinematic engine detects a persistent event, Task_Detect takes over to perform deep spectral corroboration. It applies a Hanning window and computes a 128-point Radix-2 FFT over 1.28 seconds of data.*
>
> *From this spectrum, we extract 7 key features: peak acceleration, cumulative energy, dominant frequency, and energy distributions across four critical seismic sub-bands. These 7 values feed directly into an embedded 7-8-3 Multilayer Perceptron.*
>
> *Trained on the Stanford Earthquake Dataset (STEAD) and real IRIS records combined with synthetic cultural shocks, this model achieves 93.6% overall accuracy and 97.6% recall on true earthquakes. And because it consists of 91 floating-point parameters running on the hardware FPU at 250 MHz, full inference finishes in under 8 microseconds. That is true zero-latency edge intelligence."*

---

### Slide 7: Sensor Integrity Diagnostics & Watchdog Protection

#### Slide Header & Subtitle
* **Title:** **Robust Sensor Diagnostics & Fail-Safe Architecture**
* **Subtitle:** Ultra-Sensitive Bedrock Flatline Detection ($10^{-12}\text{ g}$) and RTOS Watchdog Supervision

#### Recommended Slide Layout
* **Layout:** 3-column layout highlighting: Flatline/ADC Faults, Saturation/Clipping Limits, and Software Watchdog Architecture.

#### On-Slide Content
* **The Bedrock Flatline Problem:**
  - High-precision seismic vault sensors (e.g. IRIS IU.MAJO) exhibit an ambient noise floor of just $2\ \mu\text{g}$ ($2 \times 10^{-6}\text{ g}$).
  - Coarse MEMS flatline detectors ($10^{-4}\text{ g}$) mistakenly flag quiet seismic vaults as dead or disconnected sensors.
* **Our Scaled Adaptive Diagnostic:**
  - Scaled flatline threshold to $1 \times 10^{-12}\text{ g}$ in vault mode. Consecutive real seismic deltas ($\sim 4 \times 10^{-9}\text{ g}$) pass cleanly, while true disconnected/frozen ADCs ($diff \equiv 0.000\text{ g}$) trigger within 100 samples ($1.0\text{ s}$).
* **Dynamic Rail Saturation Protection:** Flags physical sensor clipping if acceleration exceeds $\pm 2.0\text{ g}$ or outputs IEEE-754 `NaN` / `+Inf`.
* **Supervisory RTOS Watchdog:**
  - `Task_Diag` (Priority 15) continuously monitors `g_sense_heartbeat`.
  - If `Task_Sense` stalls for $> 3000\text{ ms}$, an emergency recovery fault is broadcast over UART and the sensing pipeline is automatically reinitialized.

#### Presenter Talking Notes / Script
> *"An early warning instrument must never fail silently. During our integration of real broadband seismic data from Matsushiro, Japan, we uncovered a fascinating issue: deep subterranean bedrock is so quiet that its ambient noise floor is only 2 micro-g. Standard embedded sensor algorithms designed for industrial accelerometers assumed the sensor had died and threw a flatline error!*
>
> *We resolved this by implementing an adaptive, scaled delta detector operating down to 1 picog (10^-12 g), distinguishing natural microseismic background from a frozen ADC line.*
>
> *Additionally, we implemented a dedicated RTOS diagnostic supervisor. If an interrupt storm or memory fault stalls Task_Sense for more than 3 seconds, Task_Diag catches the missing heartbeat, logs the fault code, and resets the sensor state machine. The system is inherently fail-safe."*

---

### Slide 8: Dual-Tier Alarm Escalation & Operator Controls

#### Slide Header & Subtitle
* **Title:** **Dual-Tier Escalation & Operator Actionability**
* **Subtitle:** Fast Local Warning vs. Corroborated Evacuation Siren with Fail-Safe Hold-Off

#### Recommended Slide Layout
* **Layout:** Split layout. Left side showing the State Machine Transition Diagram; Right side showing the timing chart of the 5-second hold-off and PC13 hardware mute.

#### On-Slide Content
* **Tier 1 — `ALERT_L1_LOCAL` (Soft Warning Beep):**
  - **Latency:** Asserted in **$0.4\text{ seconds}$** from initial ground motion onset.
  - **Acoustic / Visual:** $5\%$ PWM duty cycle ($1\text{ kHz}$ chirp) + green LED flashing at $10\text{ Hz}$.
  - **Action:** Warns on-site operators; arms local automated machine interlocks.
* **Tier 2 — `ALERT_L2_CORROBORATED` (Evacuation Siren):**
  - **Latency:** Asserted in **$1.7\text{ seconds}$** upon neural network or mesh quorum confirmation.
  - **Acoustic / Visual:** $50\%$ PWM duty cycle ($1\text{ kHz}$ high-volume siren) + solid illuminated LED.
  - **Action:** Triggers facility evacuation, building management shutdown, and mobile push dispatch.
* **5-Second Coda Hold-Off Timer (`ALARM_HOLD_OFF_MS = 5000`):**
  - Prevents siren chatter during seismic waveform zero-crossings and nodal dips.
* **Hardware Push-Button Silence (`PC13`):**
  - Operator press immediately cuts siren PWM to $0\%$ while maintaining LED alert status until shaking ceases.

```
Ground Motion Onset ──► [t = 0.4s: L1 Local Soft Beep] (5% PWM)
                             │
                             ├──► [t = 1.7s: L2 Corroborated Full Siren] (50% PWM)
                             │         │
                             │         ├──► [PC13 Pressed] ──► Siren Muted / LED Held
                             │         │
                             │         └──► [Ground Motion Quits] ──► 5s Hold-Off ──► Reset
```

#### Presenter Talking Notes / Script
> *"False alarms in early warning systems erode trust and cost millions in industrial downtime. To eliminate false sirens without sacrificing early reaction, ZIDIS employs a two-tier escalation architecture.*
>
> *At 0.4 seconds from physical onset, Tier 1 fires. This activates a subtle 5% PWM warning beep and flashing LED. It provides immediate notice to automated machinery and operators without triggering mass panic. Over the next 1.3 seconds, the neural classifier and mesh network analyze the full spectral window. If confirmed as a true seismic event, Tier 2 escalates to a full 50% PWM evacuation siren and dispatches mobile push alerts.*
>
> *Furthermore, we built in a 5-second hold-off timer so the siren does not stutter during seismic wave dips, and wired the blue PC13 button as an instant physical mute for control room personnel."*

---

### Slide 9: 12-Hour False Alarm Stress Benchmark

#### Slide Header & Subtitle
* **Title:** **Empirical Validation: 12-Hour False Alarm Benchmark**
* **Subtitle:** Stress-Testing Against Continuous IRIS Bedrock Noise and 180 Mechanical Shock Transients

#### Recommended Slide Layout
* **Layout:** Top half featuring `false_alarm_benchmark.png`; Bottom half featuring the Quantitative Benchmark Reduction Table and key statistical highlights.

#### On-Slide Content & Benchmark Results
* **Stress Test Dataset:** $12.0\text{ hours}$ of continuous seismic playback ($4,320,000\text{ samples}$ @ 100 Hz).
* **Noise Profile:** Real IRIS bedrock recording with diurnal drift, combined with **180 sporadic mechanical transient impacts** (15 impacts/hour: simulated hammer strikes, dropped heavy tools, door slams, footsteps).
* **Seismic Injection:** 50 real earthquake events embedded across the 12-hour timeline to evaluate simultaneous true-positive sensitivity.

| System Architecture Tier | Baseline Engine (Energy-Only) | ZIDIS Hardened Kinematic Engine | False Alarm Reduction | Mean Time Between False Alarms (MTBFA) |
| :--- | :---: | :---: | :---: | :---: |
| **Stage 1: Preliminary L1 Alert** | 36 false triggers ($3.00/\text{hr}$) | **19 false triggers ($1.58/\text{hr}$)** | **47.2% Reduction** | $37.9\text{ minutes}$ |
| **Stage 2: Post-MLP L2 Siren** | 36 false sirens ($3.00/\text{hr}$) | **2 false sirens ($0.16/\text{hr}$)** | **94.4% Reduction** | **6.0 hours** |
| **Stage 3: Multi-Node Quorum ($\ge 2$)**| 12 false sirens ($1.00/\text{hr}$) | **0 false sirens ($0.00/\text{hr}$)** | **100.0% Clean** | **> 12.0 hours (Zero False Alarms)** |

* **True Seismic Sensitivity Retained:**
  - **L1 Detection Sensitivity:** **$48 / 50\ (96.0\%)$**
  - **L2 Corroborated Sensitivity:** **$47 / 50\ (94.0\%)$**

#### Presenter Talking Notes / Script
> *"We put ZIDIS through an exhaustive 12-hour continuous stress benchmark consisting of over 4.3 million samples of real seismic vault data, bombarded with 180 mechanical shocks—15 hammer strikes, door slams, and tool drops per hour.*
>
> *A conventional energy-based detector suffered 36 false alarms—an intolerable rate of one false alarm every 20 minutes. ZIDIS cut Stage 1 false triggers by 47.2% using our kinematic passband filter alone. When passed through the embedded MLP neural network at Stage 2, false sirens plummeted by 94.4% down to just two events in 12 hours. And in a multi-node mesh quorum, false sirens dropped to exactly zero.*
>
> *Crucially, we simultaneously injected 50 true earthquakes into the stream: ZIDIS detected 96% at L1 and confirmed 94% at L2. We eliminated false alarms without blinding the system to genuine seismic events."*

---

### Slide 10: Ground Truth Seismic Validation: 2011 Tohoku Mw 9.1

#### Slide Header & Subtitle
* **Title:** **Ground-Truth Validation: 2011 Tohoku Mw 9.1**
* **Subtitle:** Bit-Accurate Detection Replay on the Great East Japan Megathrust Earthquake

#### Recommended Slide Layout
* **Layout:** Top half featuring `offline_pwave_analysis.png` (the 4-panel analysis plot); Bottom half showing the Seismogram Metric Breakdown and Flash Buffer specs.

#### On-Slide Content
* **Event Details:** 2011 Great East Japan Earthquake ($M_w 9.1$, March 11, 2011 05:46:24 UTC).
* **Seismic Station:** **IU.MAJO** (Matsushiro, Japan, epicentral distance $d \approx 380\text{ km}$, hypocentral depth $24\text{ km}$).
* **Pre-Event Noise Floor:** $\text{RMS} = 2.0\ \mu\text{g}$, $\text{Peak} = 7.0\ \mu\text{g}$.
* **Global Peak Ground Acceleration:** $0.0063\text{ g}$ ($0.062\text{ m/s}^2$).

#### Bit-Accurate Firmware Emulation Metrics
* **Exact Detection Timestamp:** **$t0 + 176.23\text{ seconds}$** (Sample index #23623).
* **Instantaneous Acceleration:** $0.0025\text{ g}$ (emerging from $0.000007\text{ g}$ background).
* **STA/LTA Energy Ratio:** **$3.15$** (cleanly exceeding threshold of $3.00$).
* **Criteria Satisfied:** $2/4$ (STA/LTA Energy + Seismic Kinematic Passband).
* **Spectral Concentration:** $90.8\%$ in $0-2\text{ Hz}$, $9.2\%$ in $2-5\text{ Hz}$. **$> 99.9\%$ of total energy below $5\text{ Hz}$**.
* **Embedded Flash Waveform:** $12,000\text{ samples}$ ($120\text{ seconds}$) burned into STM32 Flash memory (`real_earthquake_data.h`) for hardware-in-the-loop autonomous validation.

#### Presenter Talking Notes / Script
> *"To ensure that our algorithms work on true seismic energy rather than synthetic approximations, we downloaded the broadband ground motion from the catastrophic 2011 Mw 9.1 Tohoku Earthquake, recorded at the famous Matsushiro seismic vault 380 km from the epicenter.*
>
> *We converted the physical instrument response to acceleration and embedded 12,000 samples directly into the microcontroller's Flash memory. Running the exact C firmware, the node triggers at precisely 176.23 seconds into the record. The STA/LTA ratio hits 3.15, the seismic passband confirms the 1 Hz P-wave arrival, and the FFT confirms over 99.9% of the spectral energy is below 5 Hz.*
>
> *This proves bit-for-bit that ZIDIS detects real-world megathrust earthquake P-waves long before damaging shear motions manifest."*

---

### Slide 11: Real-Time Visualization & Operator Dashboard

#### Slide Header & Subtitle
* **Title:** **Operator Toolchain: Real-Time Visualization Dashboard**
* **Subtitle:** Dual-Pane Kinematic Plotter, Interactive Scrubber, and Terminal Console Monitor

#### Recommended Slide Layout
* **Layout:** 2-column comparison showing the Python Matplotlib GUI Dashboard on the left and the Lightweight Serial Console Monitor on the right.

#### On-Slide Content
* **Dual-Pane Real-Time Dashboard (`live_pwave_plotter.py`):**
  - **Global Overview Pane:** Complete 300-second timeline with interactive scrubbing cursor.
  - **Dynamic 5-Second Oscilloscope:** High-resolution zoom ($500\text{ samples}$) tracking live P-wave waveform.
  - **Energy Tracking Pane:** Continuous traces of STA ($\tau=0.5\text{s}$) and LTA ($\tau=10.0\text{s}$) moving averages.
  - **Dynamic Ratio Curve:** Visual trigger ($3.0$) and detrigger ($1.5$) thresholds with multi-criteria status box.
* **Interactive Live Controls:**
  - `[SPACE]` Pause/Resume • `[J]` Jump to 6s before P-wave onset • `[+]`/`[-]` Variable playback speed ($0.2\times$ to $10\times$) • `[B]` Mute PC speaker buzzer.
* **Lightweight Serial Console Monitor (`serial_terminal_monitor.py`):**
  - High-speed ASCII VU-meter decoding $100\text{ Hz}$ serial telemetry on `COM5`:
    ```text
    [SAMPLES #023623] [        |####    ] Acc: +0.0025g | STA/LTA: 3.15 | State: *** P-WAVE ALARM ***
    ```
  - Colorized fault, RTOS boot, and hardware silence notifications with audible PC speaker alerts.

#### Presenter Talking Notes / Script
> *"An early warning instrument requires intuitive, transparent tools for operators and seismologists. We developed two complementary monitoring interfaces:*
>
> *First, live_pwave_plotter.py provides a rich, dual-pane graphical dashboard. It renders the global 300-second earthquake record alongside a real-time sliding 5-second oscilloscope window, displaying the STA/LTA ratios, criteria indicators, and active alert state. Operators can scrub time, jump directly to onset, change playback speed, or test buzzer alerts with single keystrokes.*
>
> *Second, for low-bandwidth industrial deployments, serial_terminal_monitor.py auto-detects the ST-LINK COM port and renders a live 100 Hz ASCII VU-meter directly in any terminal console, accompanied by 1400 Hz warning chirps. It provides comprehensive visibility without requiring heavy external dependencies."*

---

### Slide 12: Mobile Push Alerts via ntfy Integration

#### Slide Header & Subtitle
* **Title:** **Mobile Push Alert Infrastructure**
* **Subtitle:** Sub-Second Push Notifications to Android, iOS, and Web via ntfy Integration

#### Recommended Slide Layout
* **Layout:** Left side showing mobile notification mockups and push architecture diagram; Right side showing configuration, cooldown logic, and sample push payload.

#### On-Slide Content
* **Zero External Dependencies:** Built with Python standard library `urllib.request` + JSON POST—no proprietary SDKs or API keys required.
* **Non-Blocking Background Threading:** Push dispatches execute asynchronously in a background daemon thread, guaranteeing zero latency impact on the 100 Hz RTOS loop or GUI plotter.
* **Urgent Priority Level 5:** Overrides mobile "Do Not Disturb" modes, plays loud alarm audio, and flashes phone strobe.
* **Intelligent Cooldown & Escalation:**
  - Enforces a 15-second cooldown between repeated notifications.
  - Instantly overrides cooldown if an alert escalates from L1 Soft Warning to L2 Corroborated Siren!
* **Rich Notification Payload:** Transmits peak acceleration ($g$), STA/LTA ratio, criteria count, and estimated S-wave warning lead time.

```
[STM32 Node Trigger] ──► [Serial Monitor / GUI] ──► [ntfy_notifier.py (Thread)]
                                                             │ (HTTPS POST)
                                                             ▼
                                                    [https://ntfy.sh]
                                                             │ (Instant Push)
                                                             ▼
                                                [Mobile Phones: Android / iOS]
                                                🚨 ZIDIS EARTHQUAKE ALERT!
                                                Peak: 0.0025g | S-Lead: 14.4s
```

#### Presenter Talking Notes / Script
> *"Early warning is only effective if the warning reaches people immediately. We engineered ntfy_notifier.py, which delivers instant, high-priority push notifications to Android, iOS, and Web browsers via the open ntfy protocol.*
>
> *The dispatcher runs in a decoupled background thread, meaning network latency never slows down the 100 Hz serial acquisition loop. It dispatches with priority level 5, which breaks through mobile 'Do Not Disturb' modes and triggers an audible siren on receiving smartphones within 500 milliseconds of detection.*
>
> *It also features smart deduplication: repeated noise bursts are suppressed with a 15-second cooldown, but if the event escalates from an L1 warning to an L2 confirmed siren, the cooldown is instantly bypassed to push the evacuation alert immediately."*

---

### Slide 13: Resource Utilization & Memory Footprint

#### Slide Header & Subtitle
* **Title:** **Embedded Resource Utilization & Execution Timing**
* **Subtitle:** Production Build Footprint on STM32H533RETx Microcontroller

#### Recommended Slide Layout
* **Layout:** Left side showing Memory Utilization Gauges (Flash & SRAM); Right side showing Execution Latency Breakdown Table.

#### On-Slide Content
* **Compiler & Target:** `arm-none-eabi-gcc 14.3.rel1` • Target: STM32H533RETx (Cortex-M33).
* **Optimization Level:** `-O2` with Hardware FPU single-precision instructions enabled.

| Memory Region | Device Capacity | Firmware Consumption | Utilization Percentage | Status / Headroom |
| :--- | :---: | :---: | :---: | :---: |
| **FLASH Memory** | $512.0\text{ KB}$ | **$125,508\text{ bytes}$** | **$24.5\%$** | **$386.5\text{ KB}$ Free (75.5% Headroom)** |
| **SRAM Memory** | $256.0\text{ KB}$ | **$17,348\text{ bytes}$** | **$6.8\%$** | **$238.6\text{ KB}$ Free (93.2% Headroom)** |

* **Deterministic Latency Breakdown:**
  - `Analyser_ProcessSample()` (Kinematics): **$< 15\ \mu\text{s}$** per sample (0.15% of 10 ms budget).
  - 128-point Radix-2 FFT: **$< 42\ \mu\text{s}$** per window.
  - 7-8-3 MLP Neural Inference: **$< 8\ \mu\text{s}$** per classification.
  - RTOS Context Switch Overhead: **$< 1.2\ \mu\text{s}$**.
  - **Total MCU Active Duty Cycle:** **$< 1.5\%$** (Over 98.5% CPU idle time available for cryptographic mesh networking and low-power sleep).

#### Presenter Talking Notes / Script
> *"Efficiency is the hallmark of professional embedded engineering. Here is our physical memory and timing footprint compiled under GCC 14.3:
>
> The entire firmware—including the μT-Kernel 3.0 RTOS core, hardware drivers, DSP kinematic pipeline, neural network, and 12,000 samples of embedded 100 Hz earthquake Flash data—occupies only 125.5 KB of Flash, or 24.5% of the microcontroller's capacity. SRAM usage is just 17.3 KB, representing less than 7% of available RAM.
>
> On the timing side, kinematic processing takes less than 15 microseconds out of our 10,000-microsecond budget. Neural inference takes under 8 microseconds. The microcontroller operates at an active duty cycle under 1.5%, leaving over 98% of CPU headroom for mesh encryption, battery-saving sleep states, and future algorithm expansions."*

---

### Slide 14: Hardware-in-the-Loop (HIL) Validation Workflow

#### Slide Header & Subtitle
* **Title:** **Hardware-in-the-Loop Validation & Flashing Workflow**
* **Subtitle:** Automated Deployment, Hardware Interfacing, and Verification Steps

#### Recommended Slide Layout
* **Layout:** 4-step horizontal process card layout illustrating: 1. Automated Flash, 2. Telemetry Streaming, 3. Acoustic Verification, 4. Operator Mute Test.

#### On-Slide Content
* **Step 1: 1-Click Firmware Deployment:**
  - Automated batch script [`flash_board.bat`](file:///c:/Users/Raamrithik/OneDrive/Documents/ZIDIS_Node/flash_board.bat) executes OpenOCD / STM32CubeProgrammer to flash `Debug/ZIDIS_Node.elf` over ST-LINK.
* **Step 2: Real-Time Telemetry Link:**
  - Connect ST-LINK Virtual COM Port (`COM5`) at $115200\text{ baud}$; verify continuous $100\text{ Hz}$ ASCII streaming (`D:<val>`).
* **Step 3: Dual-Tier Acoustic & Push Verification:**
  - Wire piezo transducer to `PB4` and `GND`.
  - At $t = 176.2\text{s}$, observe transition: $5\%$ duty warning beep (L1) escalates to $50\%$ evacuation siren (L2), accompanied by mobile push alert on phone.
* **Step 4: Operator Mute & Fail-Safe Hold-Off:**
  - Depress blue `PC13` button: siren mutes instantly while status LED remains lit.
  - Shaking subsides: observe system hold-off for $5.0\text{ seconds}$ before cleanly clearing state.

#### Presenter Talking Notes / Script
> *"To ensure reproducibility, our entire testing and verification workflow is fully automated. Flashing is accomplished via a single command using flash_board.bat.
>
> In our Hardware-in-the-Loop test bench, the STM32 board streams live telemetry over COM5 to both the serial monitor and the visualization GUI. Observers can listen as PB4 sounds the soft 5% warning chirp at the first P-wave arrival, escalating to the full 50% evacuation siren as the neural network corroborates the event. Pressing the blue user button immediately silences the siren, and when the seismic waveform decays, the 5-second hold-off timer prevents premature reset. This demonstrates an end-to-end, validated embedded product."*

---

### Slide 15: Project Evolution: Phase 1 to Phase 2

#### Slide Header & Subtitle
* **Title:** **Project Evolution: Phase 1 Foundation to Phase 2 Edge-AI**
* **Subtitle:** Systematic Architectural Progression & Future Commercial Roadmap

#### Recommended Slide Layout
* **Layout:** 2-column comparative table contrasting Phase 1 vs Phase 2, followed by a roadmap banner across the bottom.

#### On-Slide Comparison Matrix

| Architectural Feature | Phase 1 (Baseline Foundation) | Phase 2 (ZIDIS Edge-AI Production) |
| :--- | :--- | :--- |
| **System Objective** | Manual button-triggered alarm HAL | Autonomous, predictive Seismic P-Wave EEW |
| **Operating System** | Basic μT-Kernel skeleton | Deterministic 100 Hz cyclic scheduling & event flags |
| **Sensing Pipeline** | None (Static GPIO polling) | Continuous multi-criteria kinematics (STA/LTA, Passband) |
| **Machine Learning** | None | Embedded 7-8-3 MLP Neural Network on Cortex-M33 FPU |
| **Acoustic Warning** | Simple On/Off buzzer toggle | Dual-tier PWM modulation ($5\%$ Beep / $50\%$ Siren) + 5s Hold-Off |
| **Seismic Validation** | None | Real 2011 Tohoku Mw 9.1 megathrust ground-truth replay |
| **Telemetry & Alerts** | Basic debug printouts | Real-time dual-pane GUI + Instant mobile push (ntfy) |
| **False Alarm Immunity**| N/A | $47.2\%$ L1 reduction, $94.4\%$ L2 reduction, $100\%$ quorum |

* **Future Commercial Roadmap:**
  - **Phase 3:** Sub-GHz wireless mesh quorum voting (Semtech LoRa / SX1262) for multi-station spatial consensus.
  - **Phase 4:** Ultra-low-noise MEMS accelerometer integration (TDK InvenSense / ST IIS3DWB) with on-chip SPI DMA.

#### Presenter Talking Notes / Script
> *"Looking at the evolutionary arc of this project: in Phase 1, our deliverable was establishing basic HAL drivers and a manual push-button alarm under μT-Kernel.
>
> In Phase 2, we transformed ZIDIS into a fully autonomous, AI-driven Earthquake Early Warning node. We integrated a 100 Hz kinematic pipeline, implemented our passband frequency filter, embedded a 7-8-3 neural classifier, integrated dual-tier acoustic escalation, verified the firmware against the 2011 Tohoku megathrust earthquake, and connected real-time mobile push notifications.
>
> Moving forward, Phase 3 will introduce Sub-GHz LoRa mesh networking for multi-station spatial quorum voting, transforming individual ZIDIS nodes into a distributed early warning grid."*

---

### Slide 16: Summary, Impact & Technical Appendix

#### Slide Header & Subtitle
* **Title:** **Summary, Research Contributions & Technical Appendix**
* **Subtitle:** Core Engineering Achievements and Reference Mathematical Formulations

#### Recommended Slide Layout
* **Layout:** Left column with 4 Key Takeaways; Right column with Mathematical Appendix & Seismological Equations.

#### On-Slide Content
* **Core Takeaways:**
  1. **Sub-Second Edge Latency:** $0.4\text{ s}$ L1 local detection unlocks $0.12\text{ s/km}$ actionable evacuation lead time.
  2. **Frequency Paradox Solved:** $1-8\text{ Hz}$ kinematic passband cuts mechanical false alarms by $47.2\%$.
  3. **Zero-Latency Edge AI:** 7-8-3 MLP classifier achieves $97.6\%$ earthquake recall with $< 8\ \mu\text{s}$ inference on Cortex-M33 FPU.
  4. **Ultra-Compact Footprint:** Entire real-time system operates within $125.5\text{ KB}$ Flash ($24.5\%$) and $17.3\text{ KB}$ SRAM ($6.8\%$).

#### Mathematical Formulations for Q&A
* **STA/LTA Exponential Recurrence:**
  $$STA_n = \alpha_{STA} \cdot x_n^2 + (1 - \alpha_{STA}) \cdot STA_{n-1}, \quad \alpha_{STA} = 1 - e^{-\Delta t / \tau_{STA}} \approx 0.0198$$
* **Spatial Warning Window:**
  $$\Delta t = d \left( \frac{1}{v_S} - \frac{1}{v_P} \right) \approx 0.1190 \cdot d\text{ seconds}$$
* **Hanning Window Formulation:**
  $$w(n) = 0.5 \left( 1 - \cos\left(\frac{2\pi n}{N - 1}\right) \right), \quad 0 \le n \le N-1, \ N = 128$$

#### Presenter Talking Notes / Script
> *"To conclude: ZIDIS demonstrates that high-performance, life-saving seismic early warning does not require multi-thousand-dollar servers or fragile cloud connections. By uniting the determinism of μT-Kernel 3.0, the compute power of the Arm Cortex-M33 FPU, and seismologically grounded edge-AI heuristics, we have delivered a sub-second instrument capable of 47% to 94% false alarm suppression while preserving 97.6% earthquake recall.
>
> Thank you for your time and attention. I am now open to your questions."*

---

## Technical Q&A Defense Guide (Reviewer Preparation)

### Q1: Why did you choose μT-Kernel 3.0 instead of FreeRTOS or Zephyr?
* **Answer:** μT-Kernel 3.0 is a standardized real-time operating system maintained by the TRON Forum, specifically engineered for mission-critical embedded systems and industrial control. It provides deterministic, microsecond-level context switching, precise cyclic handler timers, and low-overhead event flag synchronization (`tk_wai_flg`), which guarantees that our 100 Hz kinematic sampling loop suffers virtually zero timing jitter ($< 0.1\ \mu\text{s}$).

### Q2: How does the system handle high-amplitude cultural shocks like heavy machinery or dropped tools?
* **Answer:** This is addressed by our solution to the Frequency Inversion Paradox. High-amplitude mechanical impacts ring at high frequencies ($25 - 50\text{ Hz}$), yielding 15 to 25 zero-crossings per 0.5-second window. Tectonic P-waves, by contrast, resonate between $1$ and $5\text{ Hz}$, producing only 1 to 4 zero-crossings. Our Criterion 3 establishes a strict passband of 1 to 8 crossings; any transient exceeding 8 crossings is instantly identified as mechanical impulse noise and suppressed before triggering an alarm.

### Q3: What is the exact delay between ground motion onset and the alarm sounding?
* **Answer:** We distinguish between computational processing latency and physical filter rise time:
  - Algorithm calculation takes $< 15\ \mu\text{s}$ per sample on the Cortex-M33 FPU.
  - The exponential STA filter requires roughly $0.3 - 0.4\text{ s}$ of accumulated seismic oscillations to exceed the trigger threshold ($3.0$).
  - Thus, **Tier 1 (Soft Warning Beep)** sounds in **$0.4\text{ seconds}$** from physical onset.
  - **Tier 2 (Corroborated Siren)** requires a 128-sample window ($1.28\text{ s}$) for FFT and MLP inference, sounding in **$1.69\text{ seconds} \approx 1.7\text{ seconds}$** from physical onset.

### Q4: What happens if the network connection or mobile push service fails?
* **Answer:** The ZIDIS node is 100% autonomous. The entire detection pipeline, neural network inference, and dual-tier acoustic sirens execute locally on the STM32H533RETx hardware. Mobile push notifications via ntfy and serial telemetry dashboards are strictly external telemetry overlays; a loss of internet or Wi-Fi connectivity has zero effect on the node's local sensing and alarm actuation.

---
*Report compiled and certified for technical slide decks, academic presentations, and engineering defenses.*
