# FM Transmitter Bluesky Control Demo

This demo shows how to use Bluesky (a Python experiment orchestration framework) to control the FM transmitter GNU Radio flowgraph.

## Overview

The `fm_bluesky_control.py` script provides programmatic control over the FM transmitter's center frequency using:
- **Direct XML-RPC**: Simple frequency control without Bluesky
- **Bluesky Integration**: Full integration with Bluesky's RunEngine and plan system

## Prerequisites

1. **FM Transmitter Running**: Start the FM transmitter flowgraph first:
   ```bash
   cd fm/
   python fm_transmitter_shm.py
   # Or open fm_transmitter_shm.grc in GNU Radio Companion
   ```

2. **XML-RPC Server**: The flowgraph must have an XML-RPC server block configured on `localhost:8080` (already configured in `fm_transmitter_shm.grc`)

3. **Optional - Bluesky**: For advanced features, install Bluesky:
   ```bash
   pip install bluesky ophyd
   ```

## Usage

### Test Connection

```bash
python fm_bluesky_control.py --test
```

This verifies the FM transmitter is running and shows the current frequency.

### Set Frequency

```bash
# Tune to 98.5 MHz
python fm_bluesky_control.py --freq 98.5

# Tune to WGBH Boston (89.7 MHz)
python fm_bluesky_control.py --freq 89.7
```

### Sweep FM Band (Simple)

```bash
# Default sweep: 88.0 - 108.0 MHz, 0.2 MHz steps, 2 second dwell
python fm_bluesky_control.py --sweep

# Custom sweep range
python fm_bluesky_control.py --sweep --start 95.0 --stop 100.0 --step 0.1 --dwell 1.0
```

### Sweep with Bluesky (Advanced)

```bash
# Bluesky sweep with 100 points
python fm_bluesky_control.py --bluesky-sweep

# Custom Bluesky sweep
python fm_bluesky_control.py --bluesky-sweep --start 95.0 --stop 100.0 --num-points 50 --dwell 0.5
```

### Remote Control

```bash
# Connect to GNU Radio on another machine
python fm_bluesky_control.py --test --host 192.168.1.100 --port 8080
```

## How It Works

### XML-RPC Interface

The `fm_transmitter_shm.grc` flowgraph includes:
1. **Variable**: `freq` (variable_qtgui_range) - controls SDR center frequency
2. **XML-RPC Server Block**: Exposes `get_freq()` and `set_freq()` methods

### Direct Control (No Bluesky)

```python
import xmlrpc.client

# Connect to FM transmitter
rpc = xmlrpc.client.ServerProxy('http://localhost:8080')

# Get current frequency
current_freq = rpc.get_freq()  # Returns Hz
print(f"Current: {current_freq / 1e6} MHz")

# Set frequency to 98.5 MHz
rpc.set_freq(98.5e6)
```

### Bluesky Integration

The script includes a custom `FMTransmitter` device that wraps the XML-RPC interface:

```python
from gnuradio_bluesky.gnuradio_device import GNURadioSignalGenerator

class FMTransmitter(GNURadioSignalGenerator):
    """Ophyd device for FM transmitter control."""
    # Uses get_freq/set_freq instead of get_frequency/set_frequency
```

This allows using Bluesky plans:

```python
from bluesky import RunEngine
from bluesky import plan_stubs as bps

# Create device and RunEngine
fm_tx = FMTransmitter('', name='fm_tx')
RE = RunEngine({})

# Use in Bluesky plans
RE(bps.abs_set(fm_tx.frequency, 98.5e6, wait=True))
```

## Command-Line Options

```
usage: fm_bluesky_control.py [-h] [--test] [--freq MHZ] [--sweep]
                              [--bluesky-sweep] [--start MHZ] [--stop MHZ]
                              [--step MHZ] [--num-points N] [--dwell SEC]
                              [--host HOST] [--port PORT]

Options:
  --test                Test connection to FM transmitter
  --freq MHZ            Set FM frequency in MHz (e.g., 98.5)
  --sweep               Sweep through FM band (simple)
  --bluesky-sweep       Use Bluesky for FM band sweep

Sweep parameters:
  --start MHZ           Sweep start frequency in MHz (default: 88.0)
  --stop MHZ            Sweep stop frequency in MHz (default: 108.0)
  --step MHZ            Sweep step size in MHz (default: 0.2)
  --num-points N        Number of points for Bluesky sweep (default: 100)
  --dwell SEC           Dwell time per frequency in seconds (default: 2.0)

Connection:
  --host HOST           XML-RPC server hostname (default: localhost)
  --port PORT           XML-RPC server port (default: 8080)
```

## Example Session

```bash
# Terminal 1: Start FM transmitter
cd fm/
python fm_transmitter_shm.py

# Terminal 2: Control the transmitter
cd ..
python fm_bluesky_control.py --test
# Output:
# ======================================================================
# Testing connection to FM transmitter...
# ======================================================================
# ✓ Connected to GNU Radio at http://localhost:8080
# ✓ Current FM frequency: 98.5 MHz

python fm_bluesky_control.py --freq 89.7
# Output:
# Setting FM frequency to 89.7 MHz (89700000 Hz)...
# ✓ Frequency set to 89.7 MHz

python fm_bluesky_control.py --sweep --start 95 --stop 100 --step 0.5
# Output:
# ======================================================================
# FM Band Sweep
# ======================================================================
# Frequency range: 95.0 - 100.0 MHz
# Step size: 0.5 MHz
# Dwell time: 2.0 seconds
#
# Watch/listen to the GNU Radio GUI!
# Press Ctrl+C to stop the sweep
# ======================================================================
#
# Starting sweep (11 steps)...
#
# [  1/11]   95.0 MHz
# [  2/11]   95.5 MHz
# ...
```

## Integration with Existing Bluesky Model

This demo uses the same architecture as the `widget/` sine wave demo:

1. **Device wrapper**: `FMTransmitter` extends `GNURadioSignalGenerator`
2. **XML-RPC communication**: Uses `XMLRPCSignal` for variable control
3. **Bluesky plans**: Compatible with standard Bluesky scan plans

You can use the same patterns from `widget/gnuradio_bluesky/` to create more complex control scenarios.

## Troubleshooting

### Connection refused
```
✗ Connection failed: [Errno 61] Connection refused
```
**Solution**: Make sure the FM transmitter flowgraph is running first.

### Wrong method names
```
✗ Failed to set frequency: <Fault 1: 'set_frequency: method name is not valid'>
```
**Solution**: The FM transmitter uses `get_freq`/`set_freq` (not `get_frequency`/`set_frequency`). The `FMTransmitter` class handles this.

### Bluesky not installed
```
✗ Bluesky not installed: No module named 'bluesky'
```
**Solution**: Install Bluesky: `pip install bluesky ophyd` or use `--sweep` instead of `--bluesky-sweep`.

## Automated Test Scripts

### Ottawa FM Station Test Scripts

Two automated test scripts are available that handle the entire workflow: starting GNU Radio components, sweeping through actual Ottawa FM radio stations, and cleaning up:

#### Quick Test (5 stations)

**`run_ottawa_fm_quick_test.py`** - Fast test with 5 representative Ottawa FM stations

```bash
# Default: 10 seconds per station
python run_ottawa_fm_quick_test.py

# Custom dwell time
python run_ottawa_fm_quick_test.py --dwell 5
python run_ottawa_fm_quick_test.py --dwell 15

# Show help
python run_ottawa_fm_quick_test.py --help
```

**Features:**
- Auto-starts FM transmitter and receiver
- Sweeps 5 Ottawa stations: 89.9, 93.9, 98.5, 102.5, 106.1 MHz
- Default 10-second dwell time (configurable via `--dwell`)
- Total runtime: ~40-65 seconds (depending on dwell time)
- Automatic cleanup on exit or Ctrl+C

#### Full Test (23 stations)

**`run_ottawa_fm_test.py`** - Complete test of all Ottawa FM radio stations

```bash
# Default: 5 seconds per station
python run_ottawa_fm_test.py

# Custom dwell time
python run_ottawa_fm_test.py --dwell 10
python run_ottawa_fm_test.py --dwell 2   # Fast sweep

# Show help
python run_ottawa_fm_test.py --help
```

**Features:**
- Auto-starts FM transmitter and receiver
- Sweeps all 23 Ottawa FM stations (88.5 - 106.9 MHz)
- Default 5-second dwell time (configurable via `--dwell`)
- Bluesky integration with fallback to simple XML-RPC
- Total runtime: ~2-4 minutes (depending on dwell time)
- Automatic cleanup on exit or Ctrl+C

**Ottawa FM Stations Included:**
- 88.5 FM - CILV Live 88.5 (Adult Contemporary)
- 89.9 FM - CIHT Hot 89.9 (Top 40)
- 93.9 FM - CIMF FREQ 93.9 (Francophone)
- 98.5 FM - CFMO EZ Rock (Adult Contemporary)
- 100.3 FM - CHEZ The Bear (Classic Rock)
- 102.5 FM - CIDV Move 102.5 (Rhythmic CHR)
- 106.1 FM - CHEZ-FM (Classic Rock)
- ... and 16 more stations

**Test Workflow:**
1. Cleanup any existing GNU Radio processes
2. Start FM transmitter (5s initialization wait)
3. Start FM receiver (3s initialization wait)
4. Test XML-RPC connection
5. Sweep through all Ottawa FM stations
6. Clean shutdown of all processes

**Command-Line Options:**
```
--dwell SECONDS    Dwell time per frequency in seconds
                   Quick test default: 10s
                   Full test default: 5s
```

## Related Files

- **FM Transmitter Flowgraph**: `fm/fm_transmitter_shm.grc`
- **Generated Python**: `fm/fm_transmitter_shm.py`
- **FM Receiver Flowgraph**: `fm/fm_receiver_shm.grc`
- **Generated Python**: `fm/fm_receiver_shm.py`
- **Manual Control Script**: `fm_bluesky_control.py`
- **Quick Test Script**: `run_ottawa_fm_quick_test.py`
- **Full Test Script**: `run_ottawa_fm_test.py`
- **Bluesky Device Library**: `widget/gnuradio_bluesky/gnuradio_device.py`
- **Bluesky Plans**: `widget/gnuradio_bluesky/sine_control_plan.py`

## Next Steps

- Integrate with other detectors using Bluesky's `scan()` plans
- Create custom Bluesky plans for FM frequency characterization
- Add data acquisition synchronized with frequency changes
- Control multiple GNU Radio flowgraphs simultaneously
- Extend test scripts for other regions or custom station lists
