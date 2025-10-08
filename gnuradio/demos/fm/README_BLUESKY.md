# Bluesky Control for GNU Radio FM Transmitter

This directory contains a complete Bluesky integration for controlling the EJFAT GNU Radio FM transmitter. It demonstrates how to use Bluesky's experiment orchestration framework to control radio frequency parameters in real-time.

## Overview

The integration provides:
- **Ophyd device wrapper** (`GNURadioFMTransmitter`) for the FM transmitter
- **Bluesky plans** for common FM tuning operations
- **XML-RPC backend** for communication with GNU Radio
- **Test scripts** to verify functionality
- **Interactive demo** with pre-loaded environment

## Architecture

```
┌─────────────────┐     XML-RPC      ┌──────────────────────┐
│  Bluesky Plan   │ ◄──────────────► │  GNU Radio Flowgraph │
│  (Python code)  │   (port 8080)    │  fm_transmitter_shm  │
└─────────────────┘                  └──────────────────────┘
         │                                      │
         │                                      │
         ▼                                      ▼
  ┌────────────┐                        ┌──────────┐
  │ RunEngine  │                        │ EJFAT    │
  │ (Bluesky)  │                        │ SHM Sink │
  └────────────┘                        └──────────┘
```

## Quick Start

### 1. Install Bluesky (Optional)

The test script works without Bluesky, but for full functionality:

```bash
conda activate gnuradio
pip install bluesky ophyd
```

### 2. Start the FM Transmitter

In one terminal:

```bash
cd fm
python fm_transmitter_shm.py
```

This starts the GNU Radio flowgraph with:
- RTL-SDR or other SDR hardware input
- XML-RPC server on port 8080
- EJFAT shared memory sink for data streaming
- GUI with frequency controls and waterfall display

### 3. Test the Integration

In another terminal:

```bash
cd fm
python test_bluesky_fm.py
```

This runs a series of tests:
1. Direct XML-RPC communication
2. FM band sweep (88-98 MHz)
3. Preset station visits
4. Bluesky device wrapper (if installed)

### 4. Run Interactive Demo

For interactive control:

```bash
cd fm
python run_bluesky_fm.py
```

This drops you into an IPython shell with everything pre-loaded.

## Usage Examples

### Basic Frequency Control

```python
from bluesky import RunEngine
from fm_bluesky import GNURadioFMTransmitter, set_fm_frequency

# Create RunEngine and device
RE = RunEngine({})
fm_tx = GNURadioFMTransmitter('', name='fm_tx')

# Set frequency to 98.5 MHz (KQED San Francisco)
RE(set_fm_frequency(fm_tx, 98.5e6))

# Read current frequency
freq = fm_tx.get_frequency()
print(f"Current frequency: {freq / 1e6:.2f} MHz")
```

### Frequency Sweep

Sweep through a range of frequencies:

```python
from fm_bluesky import frequency_sweep

# Sweep the entire FM band (88-108 MHz) in 100 steps
RE(frequency_sweep(fm_tx, 88e6, 108e6, 100, dwell_time=0.5))
```

### Preset Stations

Visit preset FM stations for your region:

```python
from fm_bluesky import preset_stations

# San Francisco Bay Area stations
RE(preset_stations(fm_tx, region='san_francisco'))

# Other available regions: 'new_york', 'los_angeles', 'test'
```

### Custom Frequency List

Visit specific frequencies:

```python
from fm_bluesky import frequency_steps

# Visit custom stations
stations = [88.5e6, 91.1e6, 94.9e6, 98.5e6, 101.3e6]
RE(frequency_steps(fm_tx, stations, dwell_time=2.0))
```

### Frequency Ramp

Create a smooth frequency ramp:

```python
from fm_bluesky import frequency_ramp

# Ramp through the entire FM band over 20 seconds
RE(frequency_ramp(fm_tx, 88e6, 108e6, duration=20, step_size=100e3))
```

### Data Collection

Scan frequency while collecting data:

```python
from ophyd import Signal
from fm_bluesky import scan_fm_band

# Create a simulated detector
power_meter = Signal(name='power', value=0)

# Scan and collect data
RE(scan_fm_band([power_meter], fm_tx, 88e6, 108e6, 100))
```

## API Reference

### Device: `GNURadioFMTransmitter`

Ophyd device for controlling the FM transmitter.

**Parameters:**
- `prefix` (str): Device prefix (not used for XML-RPC)
- `host` (str): XML-RPC server hostname (default: 'localhost')
- `port` (int): XML-RPC server port (default: 8080)
- `name` (str): Device name for Bluesky

**Attributes:**
- `frequency`: XMLRPCSignal for frequency control (Hz)

**Methods:**
- `set_frequency(value)`: Set frequency in Hz
- `get_frequency()`: Get current frequency in Hz
- `stage()`: Stage device for scan
- `unstage()`: Unstage device after scan

### Plans

#### `set_fm_frequency(fm_tx, frequency)`
Set the FM transmitter to a specific frequency.

**Parameters:**
- `fm_tx`: GNURadioFMTransmitter device
- `frequency`: Target frequency in Hz (e.g., 98.5e6)

#### `frequency_sweep(fm_tx, start, stop, num_points, dwell_time=0.5)`
Sweep through a range of frequencies.

**Parameters:**
- `fm_tx`: GNURadioFMTransmitter device
- `start`: Starting frequency in Hz
- `stop`: Ending frequency in Hz
- `num_points`: Number of frequency points
- `dwell_time`: Time at each frequency in seconds

#### `frequency_steps(fm_tx, frequencies, dwell_time=1.0)`
Step through discrete frequencies.

**Parameters:**
- `fm_tx`: GNURadioFMTransmitter device
- `frequencies`: List of frequencies in Hz
- `dwell_time`: Time at each frequency in seconds

#### `scan_fm_band(detectors, fm_tx, start=88e6, stop=108e6, num_points=100)`
Scan the FM band while collecting data.

**Parameters:**
- `detectors`: List of detector objects to read
- `fm_tx`: GNURadioFMTransmitter device
- `start`: Starting frequency in Hz (default: 88 MHz)
- `stop`: Ending frequency in Hz (default: 108 MHz)
- `num_points`: Number of frequency points

#### `preset_stations(fm_tx, region='san_francisco')`
Visit preset FM stations for a region.

**Parameters:**
- `fm_tx`: GNURadioFMTransmitter device
- `region`: Region name ('san_francisco', 'new_york', 'los_angeles', 'test')

#### `frequency_ramp(fm_tx, start, stop, duration, step_size=100e3)`
Ramp frequency smoothly over time.

**Parameters:**
- `fm_tx`: GNURadioFMTransmitter device
- `start`: Starting frequency in Hz
- `stop`: Ending frequency in Hz
- `duration`: Total ramp duration in seconds
- `step_size`: Frequency step size in Hz

## File Structure

```
fm/
├── fm_transmitter_shm.py          # Main GNU Radio flowgraph (modified)
├── fm_transmitter_shm.grc         # GNU Radio Companion flowgraph
├── fm_bluesky/                    # Bluesky integration package
│   ├── __init__.py                # Package initialization
│   ├── fm_device.py               # Ophyd device wrapper
│   └── fm_control_plan.py         # Bluesky plans
├── test_bluesky_fm.py             # Test script (works without Bluesky)
├── run_bluesky_fm.py              # Interactive demo (requires Bluesky)
└── README_BLUESKY.md              # This file
```

## How It Works

### XML-RPC Communication

The FM transmitter exposes a ZeroMQ RPC server on port 8080 that provides:
- `get_freq()`: Read current frequency
- `set_freq(value)`: Set frequency to value (Hz)

The Ophyd device wrapper uses Python's `xmlrpc.client` to communicate with this server.

### Ophyd Device Wrapper

The `GNURadioFMTransmitter` class:
1. Connects to the XML-RPC server on initialization
2. Creates an `XMLRPCSignal` for the frequency parameter
3. Overrides the Signal's `put()` method to use XML-RPC
4. Implements Bluesky's staging protocol

### Bluesky Plans

Plans are Python generators that yield Bluesky messages:
- `abs_set`: Set a device to a value
- `rd`: Read a device value
- `sleep`: Wait for a duration
- `trigger_and_read`: Trigger detectors and read data

The RunEngine interprets these messages and executes them.

## Modifications to GNU Radio Flowgraph

The `fm_transmitter_shm.py` file was modified to add XML-RPC support:

1. Import ZeroMQ RPC module:
   ```python
   from gnuradio import zeromq
   ```

2. Add RPC server block:
   ```python
   self.zeromq_rpc_server_0 = zeromq.rpc_server(8080, 1000)
   ```

The RPC server automatically exposes all flowgraph variables with:
- `get_<variable_name>()` getter methods
- `set_<variable_name>(value)` setter methods

In this case, the `freq` variable becomes:
- `get_freq()`: Returns current frequency
- `set_freq(value)`: Sets frequency

## Troubleshooting

### Connection Errors

**Problem:** `Failed to connect to GNU Radio XML-RPC server`

**Solution:** Make sure `fm_transmitter_shm.py` is running first:
```bash
python fm_transmitter_shm.py
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'bluesky'`

**Solution:** Install Bluesky:
```bash
pip install bluesky ophyd
```

### Frequency Not Changing

**Problem:** Frequency commands don't change the SDR tuning

**Solution:** Check that:
1. The SDR is connected and working
2. The GNU Radio flowgraph is running (not stopped)
3. The frequency is within the SDR's supported range (typically 88-108 MHz for RTL-SDR)

### Port Already in Use

**Problem:** `Address already in use` when starting flowgraph

**Solution:** Kill any existing GNU Radio processes:
```bash
pkill -f fm_transmitter_shm
```

Then restart the flowgraph.

## Advanced Usage

### Custom Plans

You can write custom plans for your specific use cases:

```python
from bluesky import plan_stubs as bps
from bluesky.preprocessors import run_decorator

def my_custom_scan(fm_tx, detector):
    """Custom plan that does something specific."""

    @run_decorator(md={'plan_name': 'my_custom_scan'})
    def inner_plan():
        # Set initial frequency
        yield from bps.abs_set(fm_tx.frequency, 98.5e6, wait=True)

        # Wait for settling
        yield from bps.sleep(1.0)

        # Take measurement
        yield from bps.trigger_and_read([detector])

        # Return to original frequency
        yield from bps.abs_set(fm_tx.frequency, 88e6, wait=True)

    yield from inner_plan()

# Use your custom plan
RE(my_custom_scan(fm_tx, power_meter))
```

### Integration with Data Acquisition

Combine with Bluesky's data acquisition and analysis tools:

```python
from bluesky.callbacks import LiveTable, LivePlot

# Create a callback to display data in real-time
table = LiveTable(['fm_tx_frequency', 'power'])

# Register callback with RunEngine
RE(scan_fm_band([power_meter], fm_tx, 88e6, 108e6, 100), table)
```

### Metadata and Logging

Add metadata to your runs:

```python
# Add metadata to a plan
md = {
    'operator': 'John Doe',
    'purpose': 'FM band survey',
    'sdr_model': 'RTL-SDR v3',
}

RE(frequency_sweep(fm_tx, 88e6, 108e6, 100), **md)
```

## References

- [Bluesky Documentation](https://blueskyproject.io/)
- [Ophyd Documentation](https://blueskyproject.io/ophyd/)
- [GNU Radio Wiki](https://wiki.gnuradio.org/)
- [EJFAT Project](https://github.com/JeffersonLab/EJFAT)

## Related Examples

See also:
- `../widget/` - Simpler sine wave example
- `fm_receiver_shm.py` - FM receiver counterpart
- `fm_transmitter_ejfat.py` - EJFAT network sink variant

## License

This code is released under the GPL-3.0 license, consistent with GNU Radio.
