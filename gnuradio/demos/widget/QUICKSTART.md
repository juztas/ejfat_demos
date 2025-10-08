# Bluesky + GNU Radio Quick Start

## Simple 2-Step Setup

### Step 1: Start GNU Radio Flowgraph

In Terminal 1:
```bash
conda activate gnuradio
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/widget
python sine_wave_demo.py
```

This opens two GUI windows showing the sine wave in time and frequency domain.

### Step 2: Run Bluesky Demo

In Terminal 2:
```bash
conda activate gnuradio
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/widget
python run_bluesky_demo.py
```

This automatically:
- Checks the GNU Radio connection
- Creates the RunEngine (`RE`)
- Creates the signal generator device (`sig_gen`)
- Drops you into IPython with everything ready to go

## Example Commands

Once you're in the IPython shell:

```python
# Set frequency to 2500 Hz
RE(set_sine_frequency(sig_gen, 2500))

# Sweep from 100 Hz to 5 kHz in 50 steps
RE(frequency_sweep(sig_gen, 100, 5000, 50, dwell_time=0.5))

# Step through specific frequencies (musical notes)
RE(frequency_steps(sig_gen, [440, 880, 1320, 1760], dwell_time=1.0))

# Smooth ramp from 100 Hz to 5 kHz over 10 seconds
RE(frequency_ramp(sig_gen, 100, 5000, duration=10, step_size=50))
```

Watch the GNU Radio GUI windows update in real-time!

## Testing Without Bluesky

If you don't have Bluesky installed or want a quick test:

```bash
python test_bluesky_control.py
```

This runs automated tests using direct XML-RPC (no Bluesky required).

## Troubleshooting

**"Cannot connect to GNU Radio"**
- Make sure `sine_wave_demo.py` is running in Terminal 1
- Check that port 8080 is not blocked

**"ModuleNotFoundError: No module named 'bluesky'"**
```bash
conda activate gnuradio
pip install bluesky ophyd
```

**Need to regenerate Python from GRC?**
```bash
grcc sine_wave_demo.grc
```

## What's Available?

- **Plans in `gnuradio_bluesky/sine_control_plan.py`:**
  - `set_sine_frequency` - Set specific frequency
  - `frequency_sweep` - Sweep through range
  - `frequency_steps` - Step through list
  - `frequency_ramp` - Smooth continuous ramp
  - `frequency_scan` - Scan with detector data collection
  - `characterize_sine_wave` - Multi-sample characterization

- **Device in `gnuradio_bluesky/gnuradio_device.py`:**
  - `GNURadioSignalGenerator` - Main device wrapper
  - `GNURadioVariable` - Generic variable control

See `README_BLUESKY.md` for full documentation.
