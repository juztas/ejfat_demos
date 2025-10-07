# EJFAT Blocks Quick Start

## What You Have

Two custom GNU Radio blocks for file-based I/Q sample storage:

- **EJFAT Sink**: Writes complex stream → binary file
- **EJFAT Source**: Reads binary file → complex stream

## Quick Installation

```bash
cd /Users/yak/Projects/Claude/gnu-radio/gr-ejfat

# Install Python package
pip install -e .

# Install GRC block definitions
mkdir -p ~/.grc_gnuradio
cp grc/ejfat_ejfat_sink.block.yml ~/.grc_gnuradio/
cp grc/ejfat_ejfat_source.block.yml ~/.grc_gnuradio/
```

## Quick Test

### Option 1: Open the test flowgraph in GRC

```bash
gnuradio-companion examples/test_ejfat_blocks.grc
```

Click "Run" and you'll see:
- Original signal being written to file
- Same signal being read back and displayed in frequency plot

### Option 2: Python test

```python
from gnuradio import gr, blocks
from gnuradio import ejfat
import numpy as np

# Create test flowgraph
tb = gr.top_block()

# Write test data
test_data = np.exp(1j * 2 * np.pi * np.arange(1000) / 10)
src = blocks.vector_source_c(test_data.tolist())
sink = ejfat.ejfat_sink(filename='/tmp/quick_test.bin')
tb.connect(src, sink)
tb.run()

print("✓ File written successfully!")

# Read it back
tb2 = gr.top_block()
source = ejfat.ejfat_source(filename='/tmp/quick_test.bin', repeat=False)
dst = blocks.vector_sink_c()
tb2.connect(source, dst)
tb2.run()

print(f"✓ Read {len(dst.data())} samples back")
print("Test PASSED!" if len(dst.data()) >= len(test_data) else "Test FAILED")
```

## Where to Find Things

- **Documentation**: `README.md` - Complete reference
- **Usage Guide**: `examples/USAGE.md` - How to use the blocks
- **Test Flowgraph**: `examples/test_ejfat_blocks.grc` - Working example
- **Source Code**: `python/ejfat/` - Block implementations
- **Unit Tests**: `python/ejfat/qa_*.py` - Test suite

## Use Cases

### Record SDR data for later processing
```
RTL-SDR Source → EJFAT Sink (filename: "capture.bin")
```

### Replay recorded data
```
EJFAT Source (filename: "capture.bin") → Your processing chain
```

### Create test datasets
```
Signal Generator → EJFAT Sink → Known signal for testing
```

### Debug signal processing
Record at multiple points in your flowgraph, compare outputs

## File Format

- **Type**: Raw binary complex64 (interleaved I/Q)
- **Sample**: 8 bytes (4-byte float I, 4-byte float Q)
- **Endianness**: Native (typically little-endian on x86/ARM)
- **Compatible with**: GNU Radio File Source/Sink, NumPy, MATLAB

## Next Steps

1. Open `examples/test_ejfat_blocks.grc` in GNU Radio Companion
2. Click "Execute the flowgraph" (play button)
3. Adjust the frequency slider and watch the spectrum
4. Modify the flowgraph to use your own signal sources
5. Read `examples/USAGE.md` for more examples

## Support

- Check `README.md` for detailed documentation
- Run unit tests: `python python/ejfat/qa_ejfat_sink.py`
- Example code in `examples/` directory
