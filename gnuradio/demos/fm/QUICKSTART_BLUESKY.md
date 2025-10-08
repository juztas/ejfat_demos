# Quick Start: Bluesky Control of FM Transmitter

## Installation

```bash
# Optional: Install Bluesky (test script works without it)
conda activate gnuradio
pip install bluesky ophyd
```

## Running the Demo

### Terminal 1: Start FM Transmitter

```bash
cd fm
python fm_transmitter_shm.py
```

Wait for the GNU Radio GUI to appear. You should see:
- Frequency slider (88-108 MHz)
- Waterfall display
- Spectrum analyzer

### Terminal 2: Test or Run Interactive Demo

**Option A: Run Tests (works without Bluesky)**

```bash
cd fm
python test_bluesky_fm.py
```

This will:
1. Test XML-RPC connection
2. Sweep through FM band (88-98 MHz)
3. Visit preset stations
4. Test Bluesky device (if installed)

**Option B: Interactive Demo (requires Bluesky)**

```bash
cd fm
python run_bluesky_fm.py
```

This drops you into IPython with everything loaded.

## Example Commands (in Interactive Demo)

```python
# Set to 98.5 MHz
RE(set_fm_frequency(fm_tx, 98.5e6))

# Sweep entire FM band
RE(frequency_sweep(fm_tx, 88e6, 108e6, 50, dwell_time=0.5))

# Visit Bay Area stations
RE(preset_stations(fm_tx, region='san_francisco'))

# Custom frequency list
stations = [88.5e6, 94.9e6, 98.5e6, 101.3e6, 106.1e6]
RE(frequency_steps(fm_tx, stations, dwell_time=2.0))

# Smooth ramp over 20 seconds
RE(frequency_ramp(fm_tx, 88e6, 108e6, duration=20))
```

## What Got Created

```
fm/
├── fm_transmitter_shm.py           # Modified with XML-RPC server
├── fm_bluesky/                     # Bluesky integration package
│   ├── __init__.py
│   ├── fm_device.py                # GNURadioFMTransmitter device
│   └── fm_control_plan.py          # Bluesky plans
├── test_bluesky_fm.py              # Test script
├── run_bluesky_fm.py               # Interactive demo
├── README_BLUESKY.md               # Full documentation
└── QUICKSTART_BLUESKY.md           # This file
```

## Troubleshooting

**Connection Error?**
- Make sure `fm_transmitter_shm.py` is running first
- Check that port 8080 is not in use

**Import Error?**
- Test script works without Bluesky
- For full demo: `pip install bluesky ophyd`

**Frequency not changing?**
- Check SDR is connected
- Verify flowgraph is running (not paused)
- Ensure frequency is in SDR range (88-108 MHz)

## Learn More

See `README_BLUESKY.md` for:
- Complete API reference
- Architecture details
- Advanced usage examples
- Custom plan development
