# GNU Radio + Bluesky Integration

This directory contains a GNU Radio Companion (GRC) flowgraph with Bluesky experiment control integration. The setup allows you to control a GNU Radio signal generator remotely from Bluesky experiments via XML-RPC.

## Overview

**Components:**
- `sine_wave_demo.grc` - GNU Radio Companion flowgraph with adjustable sine wave
- `sine_wave_demo.py` - Auto-generated Python code (created by GRC)
- `gnuradio_bluesky/gnuradio_device.py` - Ophyd device wrapper for GNU Radio control
- `gnuradio_bluesky/sine_control_plan.py` - Example Bluesky plans for frequency control

**Architecture:**
```
Bluesky Experiment ←→ XML-RPC (port 8080) ←→ GNU Radio Flowgraph
                                                    ↓
                                            Time & Freq Sinks
```

## Requirements

### GNU Radio Side
- GNU Radio >= 3.10
- gr-qtgui (QT GUI blocks)
- Python 3.9+ (should match your conda environment)

### Bluesky Side
- Bluesky framework: `pip install bluesky`
- Ophyd: `pip install ophyd`
- Python XML-RPC client (standard library, no install needed)

## Installation

### 1. Activate GNU Radio Environment

```bash
conda activate gnuradio
```

### 2. Install Bluesky (if not already installed)

```bash
pip install bluesky ophyd
```

### 3. Generate Python from GRC

Open the flowgraph in GNU Radio Companion and generate the Python code:

```bash
gnuradio-companion sine_wave_demo.grc
# In GRC: Click "Generate" button or press F5
```

This creates `sine_wave_demo.py` from the flowgraph.

Alternatively, generate from command line:
```bash
grcc sine_wave_demo.grc
```

## Usage

### Quick Start

**Terminal 1 - Start GNU Radio flowgraph:**
```bash
conda activate gnuradio
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/widget
python sine_wave_demo.py
```

This opens two windows:
- Time domain plotter (waveform view)
- Frequency domain analyzer (spectrum view)

The flowgraph starts with a 1 kHz sine wave (default).

**Terminal 2 - Run Bluesky control:**
```python
# Start IPython
ipython

# Import required modules
from bluesky import RunEngine
from gnuradio_bluesky.gnuradio_device import GNURadioSignalGenerator
from gnuradio_bluesky.sine_control_plan import *

# Create RunEngine and device
RE = RunEngine({})
sig_gen = GNURadioSignalGenerator('', name='sig_gen', host='localhost', port=8080)

# Set frequency to 2.5 kHz
RE(set_sine_frequency(sig_gen, 2500))

# Sweep from 100 Hz to 5 kHz in 50 steps
RE(frequency_sweep(sig_gen, 100, 5000, 50, dwell_time=0.5))

# Step through specific frequencies
freqs = [440, 880, 1320, 1760, 2200]  # Musical A and harmonics
RE(frequency_steps(sig_gen, freqs, dwell_time=2.0))
```

Watch the GNU Radio GUI windows update in real-time as Bluesky changes the frequency!

### Manual XML-RPC Testing

You can test the XML-RPC interface directly without Bluesky:

```python
import xmlrpc.client

# Connect to GNU Radio
rpc = xmlrpc.client.ServerProxy('http://localhost:8080')

# Read current frequency
print(rpc.get_frequency())

# Set frequency to 3 kHz
rpc.set_frequency(3000)

# Verify
print(rpc.get_frequency())
```

## Bluesky Device API

### GNURadioSignalGenerator

The main device class for controlling the signal generator.

**Initialization:**
```python
sig_gen = GNURadioSignalGenerator(
    '',                    # prefix (not used for XML-RPC)
    name='sig_gen',        # Bluesky device name
    host='localhost',      # GNU Radio host
    port=8080,             # XML-RPC port
    timeout=5.0            # Connection timeout
)
```

**Methods:**
- `sig_gen.set_frequency(value)` - Set frequency in Hz, returns DeviceStatus
- `sig_gen.get_frequency()` - Get current frequency in Hz
- `sig_gen.reconnect()` - Reconnect to GNU Radio if connection lost

**Signals:**
- `sig_gen.frequency` - Frequency signal (readable and settable)

**Usage in Plans:**
```python
# Direct set
yield from bps.abs_set(sig_gen.frequency, 1500, wait=True)

# Read current value
current_freq = yield from bps.rd(sig_gen.frequency)
```

## Example Plans

All plans are in `gnuradio_bluesky/sine_control_plan.py`.

### 1. Set Frequency
```python
RE(set_sine_frequency(sig_gen, 2500))
```
Sets frequency to 2500 Hz.

### 2. Frequency Sweep
```python
RE(frequency_sweep(sig_gen, start=100, stop=5000, num_points=50, dwell_time=0.5))
```
Sweeps from 100 Hz to 5000 Hz in 50 equal steps, dwelling 0.5 seconds at each.

### 3. Frequency Steps
```python
freqs = [100, 500, 1000, 2000, 5000]
RE(frequency_steps(sig_gen, freqs, dwell_time=1.0))
```
Steps through specific frequencies with 1 second dwell time.

### 4. Frequency Ramp
```python
RE(frequency_ramp(sig_gen, start=100, stop=5000, duration=10, step_size=50))
```
Ramps smoothly from 100 Hz to 5 kHz over 10 seconds.

### 5. Frequency Scan with Detector
```python
from ophyd import Signal
detector = Signal(name='det', value=0)

RE(frequency_scan([detector], sig_gen, start=100, stop=5000, num_points=50))
```
Scans frequency while collecting data from detector(s).

### 6. Characterize Sine Wave
```python
freqs = [1000, 2000, 3000]
RE(characterize_sine_wave([detector], sig_gen, freqs, num_samples=10))
```
Takes multiple measurements at each frequency for statistical analysis.

## GRC Flowgraph Details

### Blocks in sine_wave_demo.grc

1. **XML-RPC Server** (port 8080)
   - Exposes all variables for remote control
   - Listens on localhost

2. **Variable: frequency** (default: 1000 Hz)
   - Controllable via XML-RPC
   - Type: float

3. **Variable: samp_rate** (default: 32000)
   - Sample rate for flowgraph
   - 32 kHz sampling

4. **Signal Source**
   - Waveform: Cosine (sine wave)
   - Frequency: uses `frequency` variable
   - Amplitude: 1.0

5. **Throttle**
   - Prevents CPU spinning
   - Rate: `samp_rate`

6. **QT GUI Time Sink**
   - Shows waveform in time domain
   - 1024 sample points

7. **QT GUI Frequency Sink**
   - Shows spectrum (FFT)
   - 1024 point FFT

### Flow Diagram
```
Signal Source → Throttle → ┬→ Time Sink (waveform)
                            └→ Freq Sink (spectrum)
```

## Configuration

### Changing XML-RPC Port

In `sine_wave_demo.grc`:
1. Open in GNU Radio Companion
2. Double-click the "XML-RPC Server" block
3. Change "Port" parameter
4. Regenerate Python code (F5)

In Python code:
```python
sig_gen = GNURadioSignalGenerator('', name='sig_gen', port=NEW_PORT)
```

### Changing Sample Rate

Edit the `samp_rate` variable in the GRC flowgraph:
1. Double-click the `samp_rate` variable block
2. Change "Value" parameter
3. Regenerate Python code

Higher sample rates allow higher frequency sine waves (Nyquist: max freq = samp_rate/2).

### Adjusting Frequency Range

The current setup (32 kHz sample rate) supports frequencies up to ~16 kHz (Nyquist limit).

To go higher:
- Increase `samp_rate` in the flowgraph
- Be aware of GUI refresh rate limitations

## Troubleshooting

### GNU Radio won't start
```bash
# Check if port 8080 is in use
lsof -i :8080

# Kill existing process if needed
kill -9 <PID>
```

### Connection refused
```
ConnectionError: Failed to connect to GNU Radio XML-RPC server
```

**Solution:**
1. Verify GNU Radio flowgraph is running
2. Check XML-RPC server block is in the flowgraph
3. Verify port number matches (default: 8080)
4. Check for firewall blocking localhost connections

### Frequency not updating
```python
# Test XML-RPC directly
import xmlrpc.client
rpc = xmlrpc.client.ServerProxy('http://localhost:8080')
rpc.set_frequency(2000)  # Should update immediately
```

If direct XML-RPC works but Bluesky doesn't:
- Check the device is properly staged
- Verify `wait=True` in `abs_set` calls
- Reconnect the device: `sig_gen.reconnect()`

### GUI not refreshing

The GUI updates based on its refresh rate (~10-30 Hz). Very fast frequency changes may not be visible.

**Solution:** Add dwell time in your plans:
```python
RE(frequency_sweep(sig_gen, 100, 5000, 50, dwell_time=0.5))  # 500ms dwell
```

### Import errors
```python
ModuleNotFoundError: No module named 'bluesky'
```

**Solution:**
```bash
conda activate gnuradio
pip install bluesky ophyd
```

## Advanced Usage

### Custom Variables

The `GNURadioVariable` class allows control of any GNU Radio variable:

```python
from gnuradio_bluesky.gnuradio_device import GNURadioVariable

# If your flowgraph has an 'amplitude' variable
amplitude = GNURadioVariable('', variable_name='amplitude',
                             initial_value=1.0, name='amplitude')

# Use it in plans
yield from bps.abs_set(amplitude.value, 0.5, wait=True)
```

### Multiple Signal Generators

Control multiple GNU Radio instances:

```python
sig_gen_1 = GNURadioSignalGenerator('', name='gen1', port=8080)
sig_gen_2 = GNURadioSignalGenerator('', name='gen2', port=8081)

# Scan both simultaneously
yield from bp.grid_scan([], sig_gen_1.frequency, 100, 1000, 10,
                            sig_gen_2.frequency, 200, 2000, 10)
```

### Adding Detectors

Integrate real measurement devices:

```python
from ophyd import EpicsSignalRO

# Example: EPICS detector
detector = EpicsSignalRO('BEAMLINE:detector', name='det')

# Scan frequency and measure
RE(frequency_scan([detector], sig_gen, 100, 5000, 50))

# Data is automatically saved by Bluesky
```

### Data Logging

Use Bluesky's data broker to log scan results:

```python
from databroker import Broker

# Create data broker
db = Broker.named('temp')
RE.subscribe(db.insert)

# Run scan - data is automatically logged
RE(frequency_scan([detector], sig_gen, 100, 5000, 50))

# Retrieve data
run = db[-1]  # Most recent run
table = run.table()
print(table)
```

## Integration with EJFAT

This demo can be extended to work with EJFAT data streaming:

1. Replace the simple sine source with EJFAT data source
2. Add EJFAT segmenter/reassembler blocks
3. Control EJFAT parameters via XML-RPC
4. Use Bluesky to orchestrate multi-site experiments

See the main EJFAT demos directory for more complex examples.

## Performance Notes

- **XML-RPC Latency:** ~1-10 ms per call (suitable for control plane)
- **GUI Refresh Rate:** 10-30 Hz (limits visible update rate)
- **Frequency Update Rate:** Can update as fast as ~100 Hz via XML-RPC
- **Not for Real-Time DSP:** For real-time control, use ZMQ instead of XML-RPC

## References

- [GNU Radio XML-RPC Documentation](https://wiki.gnuradio.org/index.php/XMLRPC)
- [Bluesky Documentation](https://blueskyproject.io/)
- [Ophyd Device Tutorial](https://blueskyproject.io/ophyd/tutorials/single-PV.html)
- [GNU Radio Tutorials](https://wiki.gnuradio.org/index.php/Tutorials)

## Contributing

To add new features:

1. **New GNU Radio variable:**
   - Add variable in GRC flowgraph
   - Regenerate Python code
   - Use `GNURadioVariable` class in Bluesky

2. **New Bluesky plan:**
   - Add function to `sine_control_plan.py`
   - Use `@run_decorator` for metadata
   - Document in this README

3. **New detector:**
   - Create Ophyd device
   - Add to plans as list: `[det1, det2]`
   - Use standard Bluesky scan plans

## License

This code is part of the EJFAT demos and follows the same license as the main project.

## Support

For issues or questions:
- EJFAT GitHub: https://github.com/JeffersonLab/E2SAR
- GNU Radio mailing list: discuss-gnuradio@gnu.org
- Bluesky discussions: https://github.com/bluesky/bluesky/discussions
