# GNU Radio + Bluesky Integration Plan

## Overview

This document describes the plan for creating a GNU Radio Companion (GRC) flowgraph with a controllable sine wave generator that can be adjusted remotely by a Bluesky experiment control process.

## Objectives

1. Create a GRC flowgraph that generates a sine wave with adjustable frequency
2. Visualize the signal in both time domain (plotter) and frequency domain (spectrum analyzer)
3. Enable remote control of the sine wave frequency from a Bluesky experiment
4. Provide a clean integration interface between GNU Radio and Bluesky

## Architecture

### System Components

```
┌─────────────────────────────────────┐
│      Bluesky Experiment Control     │
│  ┌────────────────────────────────┐ │
│  │  Ophyd Device (XML-RPC Client) │ │
│  │  - Set frequency                │ │
│  │  - Read current value           │ │
│  └────────────┬───────────────────┘ │
└───────────────┼─────────────────────┘
                │ XML-RPC
                │ (HTTP on port 8080)
                ▼
┌─────────────────────────────────────┐
│      GNU Radio Flowgraph            │
│  ┌────────────────────────────────┐ │
│  │  XML-RPC Server                │ │
│  │  - Receives frequency updates  │ │
│  └────────────┬───────────────────┘ │
│               ▼                     │
│  ┌────────────────────────────────┐ │
│  │  Variable: frequency           │ │
│  │  - Controllable via XML-RPC    │ │
│  └────────────┬───────────────────┘ │
│               ▼                     │
│  ┌────────────────────────────────┐ │
│  │  Signal Source (Sine Wave)     │ │
│  │  - Uses frequency variable     │ │
│  └────────────┬───────────────────┘ │
│               ▼                     │
│  ┌────────────────────────────────┐ │
│  │  Throttle                      │ │
│  └────────────┬───────────────────┘ │
│               ▼                     │
│         ┌─────┴─────┐               │
│         ▼           ▼               │
│  ┌───────────┐ ┌──────────────┐    │
│  │ Time Sink │ │ Freq Sink    │    │
│  │ (Plotter) │ │ (Spectrum)   │    │
│  └───────────┘ └──────────────┘    │
└─────────────────────────────────────┘
```

### Communication Protocol: XML-RPC

**Selected Approach:** XML-RPC (HTTP-based RPC)

**Rationale:**
- Built-in support in GNU Radio Companion
- Simple to implement on both sides
- Well-documented and reliable
- Sufficient for control-plane operations (not data streaming)

**Alternative Approaches Considered:**
- **ZMQ (ZeroMQ):** Better for high-throughput data streaming, more complex setup
- **File-based IPC:** Simple but higher latency, polling overhead
- **gRPC:** Modern alternative but requires additional dependencies

## Implementation Plan

### Phase 1: GNU Radio Flowgraph

**File:** `sine_wave_demo.grc`

**Blocks Required:**
1. **Options Block**
   - Title: "Adjustable Sine Wave Demo"
   - Author: [to be filled]
   - Generate options: QT GUI

2. **Variable Block** (`frequency`)
   - Default value: 1000 (1 kHz)
   - Label: "Frequency (Hz)"
   - Type: Float

3. **XML-RPC Server Block**
   - Address: `localhost`
   - Port: `8080`
   - Exposes all variables for remote control

4. **Variable Block** (`samp_rate`)
   - Default value: 32000 (32 kHz)
   - Sample rate for the flowgraph

5. **Signal Source Block**
   - Waveform: Cosine (sine wave)
   - Frequency: `frequency` (variable)
   - Sample Rate: `samp_rate`
   - Amplitude: 1.0

6. **Throttle Block**
   - Sample Rate: `samp_rate`
   - Prevents CPU spinning when not using hardware

7. **QT GUI Time Sink**
   - Number of points: 1024
   - Sample Rate: `samp_rate`
   - Displays time-domain waveform

8. **QT GUI Frequency Sink**
   - FFT Size: 1024
   - Sample Rate: `samp_rate`
   - Displays frequency spectrum

**Block Connections:**
```
Signal Source → Throttle → ┬→ Time Sink
                            └→ Frequency Sink
```

### Phase 2: Bluesky Integration

#### File 1: `bluesky/gnuradio_device.py`

**Purpose:** Ophyd device wrapper for GNU Radio XML-RPC control

**Key Components:**
- `GNURadioSignalGenerator` class (inherits from `Device`)
- `frequency` signal (settable, units: Hz)
- XML-RPC client connection to GNU Radio
- Error handling and connection management

**Example Structure:**
```python
from ophyd import Device, Component as Cpt, Signal
import xmlrpc.client

class GNURadioSignalGenerator(Device):
    frequency = Cpt(Signal, value=1000, kind='hinted')

    def __init__(self, *args, host='localhost', port=8080, **kwargs):
        super().__init__(*args, **kwargs)
        self.rpc_client = xmlrpc.client.ServerProxy(
            f'http://{host}:{port}'
        )

    def set_frequency(self, value):
        self.rpc_client.set_frequency(value)
        self.frequency.put(value)

    def get_frequency(self):
        return self.rpc_client.get_frequency()
```

#### File 2: `bluesky/sine_control_plan.py`

**Purpose:** Example Bluesky plans for controlling the sine wave

**Plans to Implement:**
1. **Set frequency:** Simple plan to set a specific frequency
2. **Frequency sweep:** Scan through a range of frequencies
3. **Frequency step scan:** Discrete steps with dwell time at each

**Example Structure:**
```python
from bluesky import plans as bp
from bluesky.utils import Msg

def set_sine_frequency(signal_gen, frequency):
    """Set the sine wave frequency"""
    yield Msg('set', signal_gen.frequency, frequency)

def frequency_sweep(signal_gen, start, stop, num_points):
    """Sweep through frequencies"""
    yield from bp.scan([], signal_gen.frequency, start, stop, num_points)

def frequency_steps(signal_gen, frequencies, dwell_time=1.0):
    """Step through discrete frequencies with dwell time"""
    for freq in frequencies:
        yield from set_sine_frequency(signal_gen, freq)
        yield Msg('sleep', None, dwell_time)
```

### Phase 3: Documentation

**File:** `README_BLUESKY.md`

**Contents:**
- Installation requirements
- Setup instructions
- Usage examples
- Troubleshooting guide
- Architecture diagrams

## File Structure

```
widget/
├── sine_wave_demo.grc              # GRC flowgraph (XML format)
├── sine_wave_demo.py               # Generated Python (auto-created by GRC)
├── bluesky/
│   ├── __init__.py                 # Package marker
│   ├── gnuradio_device.py          # Ophyd device for GNU Radio
│   └── sine_control_plan.py        # Example Bluesky plans
├── README_BLUESKY.md               # User documentation
└── BLUESKY_INTEGRATION_PLAN.md     # This file

```

## Dependencies

### GNU Radio Side
- GNU Radio >= 3.10
- gr-qtgui (for visualization blocks)
- Python XML-RPC server (built-in to GNU Radio)

### Bluesky Side
- Bluesky framework
- Ophyd (device abstraction)
- Python `xmlrpc.client` (standard library)

## Configuration Parameters

### GNU Radio
- **XML-RPC Server Port:** 8080 (default)
- **Sample Rate:** 32 kHz (adjustable)
- **Default Frequency:** 1 kHz (adjustable)
- **FFT Size:** 1024 points
- **Time Sink Points:** 1024 samples

### Bluesky
- **GNU Radio Host:** localhost (for local testing)
- **GNU Radio Port:** 8080 (match GRC XML-RPC server)
- **Frequency Range:** 100 Hz - 10 kHz (example limits)

## Testing Plan

### Unit Tests
1. **GRC Flowgraph Standalone:**
   - Run `sine_wave_demo.py` directly
   - Verify GUI windows display correctly
   - Manually adjust frequency variable in GUI

2. **XML-RPC Interface:**
   - Test XML-RPC connection with Python client
   - Verify frequency updates reflect in GUI
   - Test error handling (invalid values, disconnection)

3. **Bluesky Device:**
   - Instantiate device without RunEngine
   - Test `set_frequency()` and `get_frequency()` methods
   - Verify XML-RPC communication

### Integration Tests
1. **End-to-End Control:**
   - Start GNU Radio flowgraph
   - Run Bluesky plan to set frequency
   - Verify waveform changes in Time Sink
   - Verify peak moves in Frequency Sink

2. **Frequency Sweep:**
   - Run frequency sweep plan
   - Verify smooth transitions
   - Check for dropped connections

## Future Enhancements

### Short Term
- Add amplitude control
- Add waveform type selection (sine, square, triangle)
- Add signal recording capability

### Long Term
- Integrate with EJFAT data streaming
- Add multi-channel support
- Implement feedback control loops
- Add data logging to Bluesky documents

## Security Considerations

- XML-RPC server runs on localhost by default (no network exposure)
- For remote control, consider SSH tunneling or firewall rules
- No authentication in XML-RPC (suitable for trusted environments only)

## Performance Considerations

- XML-RPC latency: ~1-10 ms (sufficient for control plane)
- Frequency update rate: Limited by GUI refresh (typically 10-30 Hz)
- Not suitable for real-time signal processing control (use ZMQ for that)

## References

- [GNU Radio XML-RPC Documentation](https://wiki.gnuradio.org/index.php/XMLRPC)
- [Bluesky Documentation](https://blueskyproject.io/)
- [Ophyd Device Tutorial](https://blueskyproject.io/ophyd/)
- [Python XML-RPC Documentation](https://docs.python.org/3/library/xmlrpc.html)

## Revision History

- 2025-10-08: Initial plan created
