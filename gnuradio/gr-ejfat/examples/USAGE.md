# EJFAT Blocks Usage Guide

## Test Flowgraph Included

The file `test_ejfat_blocks.grc` provides a complete test of both blocks:

### What it does:

1. **Signal Generation & Recording**
   - Generates a cosine wave signal (adjustable frequency with slider)
   - Writes it to `/tmp/ejfat_test.bin` using **EJFAT Sink**
   - Displays the original signal in a time-domain plot

2. **Playback**
   - Reads the same file using **EJFAT Source** (with repeat enabled)
   - Displays the playback in a frequency spectrum plot

### How to run:

```bash
# Option 1: Open in GNU Radio Companion
gnuradio-companion examples/test_ejfat_blocks.grc

# Option 2: Generate and run Python code
grcc examples/test_ejfat_blocks.grc
python examples/test_ejfat_blocks.py
```

### What to expect:

- **Original Signal** window shows the time-domain waveform being recorded
- **Frequency Spectrum** window shows the frequency content of the playback
- Adjust the "Signal Frequency" slider to change the tone
- The frequency peak should appear at the selected frequency in the spectrum

## Manual Testing Steps

### Step 1: Record a signal

Create a simple flowgraph:
```
Signal Source → Throttle → EJFAT Sink
```

Parameters:
- Signal Source: Type=Complex, Frequency=1000, Sample Rate=32000
- EJFAT Sink: Filename="/tmp/test.bin"

Run for a few seconds, then stop.

### Step 2: Playback the signal

Create a new flowgraph:
```
EJFAT Source → QT GUI Frequency Sink
```

Parameters:
- EJFAT Source: Filename="/tmp/test.bin", Repeat=True
- Frequency Sink: Sample Rate=32000

You should see a peak at 1000 Hz in the frequency display.

## Recording Real Signals

### Example: Record FM Radio

```
RTL-SDR Source → EJFAT Sink
```

Parameters:
- RTL-SDR: Sample Rate=2.4M, Frequency=98.5e6
- EJFAT Sink: Filename="/tmp/fm_recording.bin"

### Example: Playback FM Recording

```
EJFAT Source → Low Pass Filter → FM Demod → Audio Sink
```

This allows you to record RF data and play it back later for analysis or processing.

## File Format

Files created by EJFAT Sink can be read by:

### Python
```python
import numpy as np
data = np.fromfile('/tmp/test.bin', dtype=np.complex64)
print(f"Loaded {len(data)} samples")
```

### GNU Radio File Source
Use the built-in File Source block with Type=Complex and File=/tmp/test.bin

### MATLAB/Octave
```matlab
fid = fopen('/tmp/test.bin', 'rb');
data = fread(fid, [2, inf], 'float32');
data = complex(data(1,:), data(2,:));
fclose(fid);
```

## Troubleshooting

**Q: Blocks don't appear in GNU Radio Companion**
- Make sure you copied the .block.yml files to ~/.grc_gnuradio/
- Try: `gnuradio-config-info --prefix` to find where GRC looks for blocks
- Restart GNU Radio Companion

**Q: Import error when running flowgraph**
- Verify installation: `python -c "from gnuradio import ejfat; print('OK')"`
- Reinstall if needed: `pip install -e .` from gr-ejfat directory

**Q: File not found error**
- For EJFAT Source: Make sure the file exists before running
- For EJFAT Sink: Make sure the directory exists (e.g., /tmp/)
- Use absolute paths to avoid confusion

**Q: No data in frequency plot**
- Check that EJFAT Sink ran long enough to write data
- Verify file size: `ls -lh /tmp/test.bin`
- Make sure sample rates match between recording and playback
