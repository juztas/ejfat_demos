---
marp: true
theme: default
paginate: true
---

# FM Shared Memory Demo
## EJFAT Real-Time Signal Streaming

---

## Overview

**Purpose:** Demonstrates real-time FM radio signal streaming between processes using EJFAT shared memory

**Architecture:** Two-process system communicating via shared memory IPC

- **Transmitter Process:** SDR → Shared Memory
- **Receiver Process:** Shared Memory → Audio Output

---

## System Architecture

```
┌─────────────────────┐
│   SDR Hardware      │
│   (RTL-SDR/UHD)     │
└──────────┬──────────┘
           │ 2.4 MSPS
           ▼
┌─────────────────────┐
│  FM Transmitter     │
│  - Low-pass filter  │
│  - Stream to vector │
└──────────┬──────────┘
           │ EJFAT SHM ("fm_stream")
           │ 8192-sample vectors
           ▼
┌─────────────────────┐
│  FM Receiver        │
│  - FM demodulation  │
│  - Audio output     │
└─────────────────────┘
```

---

## Transmitter: fm_transmitter_shm.py

**Input:** SDR hardware (RTL-SDR, USRP, etc.)
**Output:** EJFAT shared memory sink

### Key Components:
- **SDR Source:** 2.4 MSPS, tunable 88-108 MHz FM band
- **Low-pass Filter:** 75 kHz passband, 25 kHz transition
- **Stream to Vector:** Packs 8192 samples per vector
- **EJFAT SHM Sink:** Ring buffer named "fm_stream"

### GUI Features:
- Frequency slider (88-108 MHz)
- Waterfall display
- Spectrum analyzer

---

## Receiver: fm_receiver_shm.py

**Input:** EJFAT shared memory source
**Output:** Audio hardware

### Key Components:
- **EJFAT SHM Source:** Reads from "fm_stream" buffer
- **Vector to Stream:** Unpacks vectors to sample stream
- **Decimation:** 2.4 MSPS → 480 kHz (5x decimation)
- **FM Demodulator:** Wideband FM receiver block
- **Audio Resampler:** 48 kHz audio output

### GUI Features:
- Volume control
- Signal visualization

---

## Shared Memory Details

**EJFAT SHM Configuration:**
- **Name:** `fm_stream`
- **Capacity:** 1024 entries (ring buffer)
- **Entry Size:** 65,552 bytes
- **Vector Length:** 8192 samples
- **Data Type:** Complex float (gr_complex)

**Performance:**
- Zero-copy IPC between processes
- Low-latency streaming (~milliseconds)
- Efficient for high-throughput RF data

---

## Signal Processing Chain

### Transmitter:
1. SDR captures RF at 2.4 MSPS
2. Low-pass filter isolates FM signal (75 kHz)
3. Samples packed into 8192-element vectors
4. Vectors written to shared memory

### Receiver:
1. Vectors read from shared memory
2. Unpacked to sample stream
3. Decimated 5x to 480 kHz
4. FM demodulation (10x audio decimation)
5. Audio output at 48 kHz

---

## Bluesky Integration

**Remote Control via XML-RPC (port 8080)**

### Ophyd Device Wrapper:
```python
fm_tx = GNURadioFMTransmitter('', name='fm_tx')
```

### Example Control Plans:
- **Set Frequency:** `RE(set_fm_frequency(fm_tx, 98.5e6))`
- **Frequency Sweep:** `RE(frequency_sweep(fm_tx, 88e6, 108e6, 100))`
- **Preset Stations:** `RE(preset_stations(fm_tx, region='san_francisco'))`
- **FM Band Scan:** `RE(scan_fm_band([detector], fm_tx, 88e6, 108e6, 100))`

---

## Bluesky Use Cases

**Experiment Orchestration:**
- Automated RF testing and measurement
- Data collection synchronized with frequency changes
- Repeatable scan sequences
- Multi-instrument coordination

**Example: Automated Station Survey**
```python
# Scan all major FM stations and collect signal strength
stations = [88.5e6, 91.1e6, 94.9e6, 98.5e6, 101.3e6]
RE(frequency_steps(fm_tx, stations, dwell_time=2.0))
```

---

## Key Features

✅ **Real-time IPC:** Zero-copy shared memory between processes
✅ **Flexible Architecture:** Transmitter and receiver run independently
✅ **Remote Control:** XML-RPC API for programmatic control
✅ **GUI Visualization:** Waterfall, spectrum, and frequency controls
✅ **Bluesky Integration:** Experiment automation and orchestration
✅ **E2SAR Compatible:** Uses EJFAT shared memory library

---

## Technical Specifications

| Parameter | Value |
|-----------|-------|
| Sample Rate | 2.4 MSPS |
| Frequency Range | 88-108 MHz (FM band) |
| Vector Size | 8192 samples |
| SHM Buffer Size | 1024 entries |
| Audio Output | 48 kHz stereo |
| Control Interface | XML-RPC (port 8080) |
| Data Type | 32-bit complex float |

---

## Demo Files

**Main Applications:**
- `fm_transmitter_shm.py` - SDR to shared memory
- `fm_receiver_shm.py` - Shared memory to audio
- `fm_transmitter_shm.grc` - GNU Radio Companion flowgraph
- `fm_receiver_shm.grc` - GNU Radio Companion flowgraph

**Bluesky Control:**
- `fm_bluesky_control.py` - Ophyd device and plans
- `run_ottawa_fm_test.py` - Automated test script
- `run_ottawa_fm_quick_test.py` - Quick verification script

---

## Running the Demo

**Terminal 1 - Start Transmitter:**
```bash
cd fm
python fm_transmitter_shm.py
```

**Terminal 2 - Start Receiver:**
```bash
cd fm
python fm_receiver_shm.py
```

**Terminal 3 - Bluesky Control (Optional):**
```bash
python run_ottawa_fm_test.py
```

---

## Applications

**RF Research:**
- Software-defined radio experimentation
- Signal processing algorithm development
- Real-time spectrum analysis

**Experiment Automation:**
- Automated frequency sweeps
- Signal strength surveys
- Multi-station monitoring

**Education:**
- GNU Radio tutorials
- IPC demonstration
- RF signal processing concepts

---

## Summary

The FM Shared Memory Demo showcases:

1. **EJFAT shared memory** for high-performance IPC
2. **GNU Radio integration** for signal processing
3. **Bluesky orchestration** for automated experiments
4. **Real-time streaming** with minimal latency
5. **Modular architecture** supporting independent processes

**Result:** A flexible, high-performance platform for RF experimentation and automation
