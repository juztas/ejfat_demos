# gr-ejfat: GNU Radio EJFAT Source and Sink Blocks

GNU Radio out-of-tree module providing file-based, shared memory, and E2SAR network-based complex sample I/O blocks.

## Test Summary

The module includes comprehensive unit tests for all blocks:

- **qa_ejfat_sink.py**: Tests file-based sink block instantiation and writing complex data to binary files
- **qa_ejfat_source.py**: Tests file-based source block reading from files and repeat/loop mode
- **qa_ejfat_shm_sink.py**: Tests shared memory sink block writing complex data to POSIX shared memory with multi-batch writes
- **qa_ejfat_shm_source.py**: Tests shared memory source block reading complex data and handling multiple events with proper event sequencing
- **qa_e2sar_segmenter_sink.py**: Tests E2SAR segmenter sink instantiation and vector input (requires e2sar_py)
- **qa_e2sar_reassembler_source.py**: Tests E2SAR reassembler source instantiation and vector output (requires e2sar_py)

All tests use the GNU Radio unittest framework and validate block behavior with temporary resources that are automatically cleaned up.

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

### E2SAR Network Blocks

These blocks require the E2SAR library (e2sar_py) to be installed.

#### E2SAR Segmenter Sink
Transmits complex (I/Q) samples over the network using the E2SAR data plane segmenter.

**Parameters:**
- `uri`: EJFAT URI string (e.g., `'ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1:19522'`)
- `data_id`: Data identifier, uint16 (default: `1`)
- `event_src_id`: Event source identifier, uint32 (default: `1`)
- `vector_size`: Size of input complex vectors (integer, default: `1` for streaming samples)
- `use_cp`: Use control plane (boolean, default: `False`)
- `mtu`: Maximum transmission unit in bytes (integer, default: `9000`)
- `rate_gbps`: Target data rate in Gbps (float, default: `1.0`)

**Input:**
- Complex float stream (gr_complex/fc32) or vectors

**Features:**
- E2SAR network transmission with load balancing
- Configurable MTU and data rate
- Automatic event numbering
- Vector or streaming sample support

#### E2SAR Reassembler Source
Receives complex (I/Q) samples over the network using the E2SAR data plane reassembler.

**Parameters:**
- `uri`: EJFAT URI string (e.g., `'ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1'`)
- `data_ip`: Data plane IP address (string, default: `'127.0.0.1'`)
- `starting_port`: Starting UDP port for receiving data (integer, default: `19522`)
- `vector_size`: Size of output complex vectors (integer, default: `1` for streaming samples)
- `num_recv_threads`: Number of receiver threads (integer, default: `1`)
- `use_cp`: Use control plane (boolean, default: `False`)
- `use_host_address`: Use IP address for gRPC instead of hostname (boolean, default: `False`)
- `period_ms`: SendState thread period in milliseconds (integer, default: `100`)
- `validate_cert`: Validate control plane TLS certificate (boolean, default: `True`)
- `with_lb_header`: Expect load balancer header (boolean, default: `True` for testing without LB)
- `event_timeout_ms`: Event timeout in milliseconds (integer, default: `5000`)
- `rcv_socket_buf_size`: Socket receive buffer size in bytes (integer, default: `3145728`)
- `port_range`: 2^portRange listening ports, -1 = auto (integer, default: `-1`)

**PID Control Parameters:**
- `epoch_ms`: PID control epoch period in milliseconds (integer, default: `1000`)
- `ki`: PID integral gain (float, default: `0.0`)
- `kp`: PID proportional gain (float, default: `0.0`)
- `kd`: PID derivative gain (float, default: `0.0`)
- `set_point`: PID setpoint for queue occupancy % (float, default: `0.0`)

**Load Balancing Parameters:**
- `weight`: Node processing power weight (float, default: `1.0`)
- `min_factor`: Min slot allocation factor (float, default: `0.5`)
- `max_factor`: Max slot allocation factor (float, default: `2.0`)

**Output:**
- Complex float stream (gr_complex/fc32) or vectors

**Features:**
- E2SAR network reception with load balancing
- Multi-threaded receiver
- PID-based flow control
- Event reassembly and sequencing
- Vector or streaming sample output

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
cp grc/ejfat_e2sar_segmenter_sink.block.yml ~/.grc_gnuradio/
cp grc/ejfat_e2sar_reassembler_source.block.yml ~/.grc_gnuradio/
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

# E2SAR network blocks (requires e2sar_py)
python python/ejfat/qa_e2sar_segmenter_sink.py
python python/ejfat/qa_e2sar_reassembler_source.py
```

## Usage in GNU Radio Companion

1. Open GNU Radio Companion
2. Look for blocks in the **[EJFAT]** category:
   - **EJFAT Sink**: Save complex stream to file
   - **EJFAT Source**: Read complex stream from file
   - **EJFAT SHM Sink**: Write complex stream to shared memory
   - **EJFAT SHM Source**: Read complex stream from shared memory
   - **E2SAR Segmenter Sink**: Transmit complex stream over E2SAR network
   - **E2SAR Reassembler Source**: Receive complex stream from E2SAR network

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

**E2SAR Network: Inter-Process Communication over Network**
```
Transmitter Process:
Signal Source → Throttle → E2SAR Segmenter Sink

Receiver Process:
E2SAR Reassembler Source → QT GUI Frequency Sink
```
Configure matching EJFAT URIs in both blocks. The Segmenter sends data through the EJFAT load balancer to the Reassembler. Requires E2SAR infrastructure to be running.

**E2SAR Network: Example**
```bash
# Run the included example demonstrating E2SAR network blocks
python examples/test_e2sar_blocks.py
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

### E2SAR Network Blocks

```python
from gnuradio import gr, analog, blocks
from gnuradio import ejfat

# Transmitter flowgraph
class transmitter_fg(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        src = analog.sig_source_c(32000, analog.GR_COS_WAVE, 1000, 1, 0)
        throttle = blocks.throttle(gr.sizeof_gr_complex, 32000)
        e2sar_sink = ejfat.e2sar_segmenter_sink(
            uri='ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1:19522',
            data_id=1,
            event_src_id=1,
            vector_size=1024,  # Send in vectors of 1024 samples
            use_cp=False,
            mtu=9000,
            rate_gbps=1.0
        )

        self.connect(src, throttle, e2sar_sink)

# Receiver flowgraph (run in separate process or machine)
class receiver_fg(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        e2sar_source = ejfat.e2sar_reassembler_source(
            uri='ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1',
            data_ip='127.0.0.1',
            starting_port=19522,
            vector_size=1024,  # Receive vectors of 1024 samples
            num_recv_threads=1,
            use_cp=False,
            with_lb_header=True
        )
        sink = blocks.null_sink(gr.sizeof_gr_complex * 1024)

        self.connect(e2sar_source, sink)

# Start transmitter first, then receiver
# Requires E2SAR infrastructure (load balancer, etc.) to be running
```

## License

GPL-3.0-or-later

## Authors

gr-ejfat development team
