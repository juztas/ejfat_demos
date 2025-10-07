# EJFAT GNU Radio Plugin - Installation and Testing Guide

## Project Overview

This GNU Radio out-of-tree (OOT) module provides two custom blocks for file-based I/Q sample storage:

- **ejfat_sink**: Records complex streams to binary files
- **ejfat_source**: Plays back complex streams from binary files

## Installation Status

✅ **Already Installed!** The blocks are ready to use in your system.

### What Was Installed

1. **Python Package**: `gnuradio-ejfat` installed in editable mode
2. **GRC Block Definitions**: Copied to `~/.grc_gnuradio/`
3. **Blocks Available**: Under the **[EJFAT]** category in GNU Radio Companion

### Installation Commands (for reference)

If you need to reinstall:

```bash
cd /Users/yak/Projects/Claude/gnu-radio/gr-ejfat

# Install Python package
pip install -e .

# Install GRC block definitions
mkdir -p ~/.grc_gnuradio
cp grc/ejfat_ejfat_sink.block.yml ~/.grc_gnuradio/
cp grc/ejfat_ejfat_source.block.yml ~/.grc_gnuradio/
```

## Project Structure

```
gr-ejfat/
├── QUICKSTART.md                      # Quick start guide
├── README.md                          # Complete documentation
├── INSTALLATION_AND_TESTING.md        # This file
├── setup.py                           # Python package installer
│
├── python/ejfat/
│   ├── __init__.py                   # Package initialization
│   ├── ejfat_sink.py                 # Sink block implementation
│   ├── ejfat_source.py               # Source block implementation
│   ├── qa_ejfat_sink.py              # Sink unit tests ✓
│   └── qa_ejfat_source.py            # Source unit tests ✓
│
├── grc/
│   ├── ejfat_ejfat_sink.block.yml    # Sink GRC GUI definition
│   └── ejfat_ejfat_source.block.yml  # Source GRC GUI definition
│
└── examples/
    ├── test_ejfat_blocks.grc         # 🎯 Complete test flowgraph
    ├── test_ejfat.py                 # Python test script
    └── USAGE.md                      # Detailed usage examples
```

## Testing the Installation

### Option 1: Run Unit Tests

Verify the blocks work correctly:

```bash
cd /Users/yak/Projects/Claude/gnu-radio/gr-ejfat

# Test the sink block
python python/ejfat/qa_ejfat_sink.py

# Test the source block (may take ~60 seconds)
python python/ejfat/qa_ejfat_source.py
```

Expected output: Test results showing "OK" or "PASSED"

### Option 2: Quick Python Test

```python
# Verify blocks can be imported
python -c "from gnuradio import ejfat; print('✓ EJFAT blocks imported successfully')"
```

### Option 3: Test in GNU Radio Companion

The easiest way to test is using the provided flowgraph:

```bash
# Open the test flowgraph
gnuradio-companion examples/test_ejfat_blocks.grc
```

**What the test flowgraph does:**

1. **Signal Generation (Top Path)**
   - Generates a cosine wave at adjustable frequency (100-10000 Hz)
   - Throttles to 32 kHz sample rate
   - Writes to `/tmp/ejfat_test.bin` using **EJFAT Sink**
   - Displays original signal in time-domain plot

2. **Playback (Bottom Path)**
   - Reads from `/tmp/ejfat_test.bin` using **EJFAT Source**
   - Throttles playback
   - Displays frequency spectrum

**How to run:**
1. Click the "Execute the flowgraph" button (▶ play icon)
2. Two windows will open:
   - **Original Signal**: Time-domain waveform being recorded
   - **Frequency Spectrum**: Frequency content of playback
3. Adjust the "Signal Frequency" slider (100-10000 Hz)
4. Watch the frequency peak move in the spectrum plot
5. Click Stop when done

## Block Details

### EJFAT Sink Block

**Purpose**: Write complex stream data to a binary file

**Parameters:**
- `filename` (string): Output file path
  - In GRC: File save dialog
  - Default: empty string

**Ports:**
- Input: Complex stream (gr_complex/fc32)
- Output: None (sink block)

**File Format:**
- Raw binary complex64
- 8 bytes per sample (4-byte float I, 4-byte float Q)
- Little-endian on x86/ARM systems

**Implementation**: `python/ejfat/ejfat_sink.py`

### EJFAT Source Block

**Purpose**: Read complex stream data from a binary file

**Parameters:**
- `filename` (string): Input file path
  - In GRC: File open dialog
  - Default: empty string
- `repeat` (boolean): Loop playback at end of file
  - True: Continuous loop
  - False: Output zeros after EOF
  - Default: True

**Ports:**
- Input: None (source block)
- Output: Complex stream (gr_complex/fc32)

**File Format:**
- Raw binary complex64 (same as sink)

**Implementation**: `python/ejfat/ejfat_source.py`

## File Format Compatibility

Files created by EJFAT Sink are compatible with:

### Python/NumPy
```python
import numpy as np
data = np.fromfile('/tmp/ejfat_test.bin', dtype=np.complex64)
print(f"Loaded {len(data)} samples")
```

### GNU Radio File Source Block
- Set Type: Complex
- Set File: /tmp/ejfat_test.bin

### MATLAB/Octave
```matlab
fid = fopen('/tmp/ejfat_test.bin', 'rb');
data = fread(fid, [2, inf], 'float32');
data = complex(data(1,:), data(2,:));
fclose(fid);
```

## Common Use Cases

### 1. Record SDR Data

```
RTL-SDR Source → EJFAT Sink
```

**Configuration:**
- RTL-SDR: Sample Rate=2.4M, Frequency=98.5e6 (FM radio)
- EJFAT Sink: Filename="/tmp/fm_capture.bin"

### 2. Replay Recorded Data

```
EJFAT Source → Your Processing Chain → Audio/Display Sink
```

**Configuration:**
- EJFAT Source: Filename="/tmp/fm_capture.bin", Repeat=True

### 3. Create Test Datasets

```
Signal Generator → EJFAT Sink
```

Generate known signals for testing and algorithm development.

### 4. Debug Signal Processing

Insert EJFAT Sink blocks at multiple points in your flowgraph to capture intermediate signals for offline analysis.

## Troubleshooting

### Blocks Don't Appear in GRC

**Problem**: EJFAT blocks not visible in GNU Radio Companion

**Solution:**
```bash
# Verify block files are in place
ls ~/.grc_gnuradio/ejfat_*.yml

# If missing, copy them
cp grc/ejfat_ejfat_sink.block.yml ~/.grc_gnuradio/
cp grc/ejfat_ejfat_source.block.yml ~/.grc_gnuradio/

# Restart GNU Radio Companion
```

### Import Error in Flowgraph

**Problem**: `ModuleNotFoundError: No module named 'gnuradio.ejfat'`

**Solution:**
```bash
# Verify installation
python -c "from gnuradio import ejfat; print('OK')"

# If it fails, reinstall
cd /Users/yak/Projects/Claude/gnu-radio/gr-ejfat
pip install -e .
```

### File Not Found Error

**Problem**: EJFAT Source can't find the file

**Solution:**
- For Source: Ensure file exists before running flowgraph
- Check file path is absolute (e.g., `/tmp/test.bin` not `test.bin`)
- Verify file was created: `ls -lh /tmp/ejfat_test.bin`

### No Data in Plots

**Problem**: Frequency plot shows no signal

**Solution:**
- Let Sink run for a few seconds to write data
- Check file size: `ls -lh /tmp/ejfat_test.bin` (should be > 0 bytes)
- Ensure sample rates match between recording and playback
- Try toggling repeat mode in Source block

### Namespace Package Warning

**Problem**: Warning about `'NoneType' object has no attribute 'loader'`

**Solution:**
- This is a harmless warning related to Python namespace packages
- Blocks will still function correctly
- Can be safely ignored

## Verification Checklist

- [ ] Unit tests pass: `python python/ejfat/qa_ejfat_sink.py`
- [ ] Blocks importable: `python -c "from gnuradio import ejfat"`
- [ ] GRC blocks visible: Check [EJFAT] category in GNU Radio Companion
- [ ] Test flowgraph runs: `gnuradio-companion examples/test_ejfat_blocks.grc`
- [ ] File created: `/tmp/ejfat_test.bin` exists and has size > 0
- [ ] Frequency peak visible in spectrum at selected frequency

## Additional Resources

- **Quick Start**: See `QUICKSTART.md` for immediate usage
- **Complete Documentation**: See `README.md` for full API reference
- **Usage Examples**: See `examples/USAGE.md` for more flowgraph examples
- **Source Code**: Browse `python/ejfat/` for implementation details

## Technical Details

### Block Type
Both blocks are implemented as GNU Radio `sync_block` in Python.

### Data Type
- Input/Output: `numpy.complex64`
- GNU Radio type: `gr_complex`
- Size: 8 bytes per sample

### File Handling
- **Sink**: Opens file in `start()`, writes in `work()`, closes in `stop()`
- **Source**: Opens file in `start()`, reads in `work()`, closes in `stop()`
- **Error Handling**: Graceful handling of I/O errors with console messages

### Performance
- Pure Python implementation
- Uses NumPy for efficient file I/O
- Suitable for moderate data rates (< 10 MHz)

## Development Information

**Created**: October 5, 2025
**GNU Radio Version**: 3.10.12.0
**Python Version**: 3.13.7
**License**: GPL-3.0-or-later

## Next Steps

1. **Try the test flowgraph**: Open `examples/test_ejfat_blocks.grc` in GRC
2. **Explore examples**: Check `examples/USAGE.md` for more use cases
3. **Integrate into your projects**: Use EJFAT blocks in your own flowgraphs
4. **Read the docs**: See `README.md` for complete API documentation

---

**Status**: ✅ Installation complete and tested
**Test Flowgraph**: `examples/test_ejfat_blocks.grc`
**Documentation**: `README.md`, `QUICKSTART.md`, `examples/USAGE.md`
