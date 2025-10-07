# gr-ejfat: GNU Radio EJFAT Source and Sink Blocks

GNU Radio out-of-tree module providing file-based and shared memory complex sample I/O blocks.

## Blocks

### File-Based Blocks

#### EJFAT Sink
Writes complex (I/Q) samples from a GNU Radio flowgraph to a binary file.

**Parameters:**
- `filename`: Output file path (string)

**Input:**
- Complex float stream (gr_complex/fc32)

**File Format:**
Raw binary complex64 samples (interleaved 32-bit float I/Q pairs)

#### EJFAT Source
Reads complex (I/Q) samples from a binary file and outputs them to a GNU Radio flowgraph.

**Parameters:**
- `filename`: Input file path (string)
- `repeat`: Loop playback when reaching end of file (boolean, default: True)

**Output:**
- Complex float stream (gr_complex/fc32)

**File Format:**
Raw binary complex64 samples (interleaved 32-bit float I/Q pairs)

### Shared Memory Blocks

#### EJFAT SHM Sink
Writes complex (I/Q) samples to a POSIX shared memory FIFO for high-performance inter-process communication.

**Parameters:**
- `shm_name`: Unique identifier for the shared memory FIFO (string, default: `'ejfat_fifo'`)
- `capacity`: Number of entries in circular buffer (integer, default: `1024`)
- `entry_size`: Maximum bytes per entry including metadata (integer, default: `4096`)

**Input:**
- Complex float stream (gr_complex/fc32)

**Features:**
- Zero-copy shared memory transfer
- Non-blocking writes with drop counting
- Automatic event number tracking
- Statistics reporting

#### EJFAT SHM Source
Reads complex (I/Q) samples from a POSIX shared memory FIFO created by EJFAT SHM Sink.

**Parameters:**
- `shm_name`: Unique identifier for the shared memory FIFO (string, default: `'ejfat_fifo'`)
- `timeout`: Seconds to wait for data - `None`=block forever, `0`=non-blocking (float/None, default: `None`)
- `max_samples_per_read`: Maximum number of samples per work() call (integer, default: `8192`)

**Output:**
- Complex float stream (gr_complex/fc32)

**Features:**
- Low-latency memory-based IPC
- Configurable blocking/non-blocking reads
- Event sequence validation
- Missing event detection

## Installation

### Quick Install (Python-only)

```bash
# From the gr-ejfat directory
pip install -e .

# Copy GRC block definitions
mkdir -p ~/.grc_gnuradio
cp grc/ejfat_ejfat_sink.block.yml ~/.grc_gnuradio/
cp grc/ejfat_ejfat_source.block.yml ~/.grc_gnuradio/
cp grc/ejfat_ejfat_shm_sink.block.yml ~/.grc_gnuradio/
cp grc/ejfat_ejfat_shm_source.block.yml ~/.grc_gnuradio/
```

### Full CMake Build (if dependencies are available)

```bash
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig  # Linux only
```

## Testing

Run the unit tests:

```bash
# File-based blocks
python python/ejfat/qa_ejfat_sink.py
python python/ejfat/qa_ejfat_source.py

# Shared memory blocks
python python/ejfat/qa_ejfat_shm_sink.py
python python/ejfat/qa_ejfat_shm_source.py
```

## Usage in GNU Radio Companion

1. Open GNU Radio Companion
2. Look for blocks in the **[EJFAT]** category:
   - **EJFAT Sink**: Save complex stream to file
   - **EJFAT Source**: Read complex stream from file
   - **EJFAT SHM Sink**: Write complex stream to shared memory
   - **EJFAT SHM Source**: Read complex stream from shared memory

### Example Flowgraphs

**File-Based: Recording**
```
Signal Source → EJFAT Sink
```
Set the filename parameter in EJFAT Sink to save data.

**File-Based: Playback**
```
EJFAT Source → QT GUI Frequency Sink
```
Set the filename parameter in EJFAT Source to load data.

**File-Based: Record and Playback**
```
RTL-SDR Source → EJFAT Sink

(In another flowgraph or later:)
EJFAT Source → Audio Sink / QT GUI Sinks
```

**Shared Memory: Inter-Process Communication**
```
Writer Process:
Signal Source → Throttle → EJFAT SHM Sink

Reader Process:
EJFAT SHM Source → QT GUI Frequency Sink
```
Use matching `shm_name` in both blocks. Start the writer process first.

**Shared Memory: Example**
```bash
# Run the included example demonstrating shared memory IPC
python examples/test_ejfat_shm_blocks.py
```

## File Format Details

The blocks use a simple raw binary format:
- Each sample is a complex64 (8 bytes total)
- 4 bytes: I component (32-bit float, little-endian)
- 4 bytes: Q component (32-bit float, little-endian)
- Samples are stored sequentially

This format is compatible with:
- GNU Radio File Sink/Source blocks
- NumPy: `np.fromfile(filename, dtype=np.complex64)`
- MATLAB/Octave: `fread(fid, [2, inf], 'float32')`
- Python: `struct.unpack('ff', ...)`

## Python API

### File-Based Blocks

```python
from gnuradio import gr, blocks
from gnuradio import ejfat

# Create flowgraph
tb = gr.top_block()

# Write to file
sink = ejfat.ejfat_sink(filename='/path/to/output.bin')

# Read from file
source = ejfat.ejfat_source(filename='/path/to/input.bin', repeat=True)

# Connect blocks
tb.connect(some_source, sink)
tb.connect(source, some_sink)

# Run
tb.run()
```

### Shared Memory Blocks

```python
from gnuradio import gr, analog, blocks
from gnuradio import ejfat

# Writer flowgraph
class writer_fg(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        src = analog.sig_source_c(32000, analog.GR_COS_WAVE, 1000, 1, 0)
        throttle = blocks.throttle(gr.sizeof_gr_complex, 32000)
        shm_sink = ejfat.ejfat_shm_sink(
            shm_name='my_channel',
            capacity=1024,
            entry_size=4096
        )

        self.connect(src, throttle, shm_sink)

# Reader flowgraph (run in separate process)
class reader_fg(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        shm_source = ejfat.ejfat_shm_source(
            shm_name='my_channel',
            timeout=None,
            max_samples_per_read=8192
        )
        sink = blocks.null_sink(gr.sizeof_gr_complex)

        self.connect(shm_source, sink)

# Start writer first, then reader
```

## License

GPL-3.0-or-later

## Authors

gr-ejfat development team
