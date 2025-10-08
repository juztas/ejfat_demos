# E2SAR GNU Radio Blocks

This document describes the E2SAR Segmenter Sink and Reassembler Source blocks for GNU Radio, which enable transmission and reception of complex signal data over the EJFAT network using E2SAR's data plane.

## Overview

The E2SAR blocks integrate E2SAR's high-performance segmentation and reassembly capabilities directly into GNU Radio flowgraphs. These blocks are designed to:

- **Segment and transmit** complex signal vectors over the EJFAT network
- **Receive and reassemble** complex signal vectors from the EJFAT network
- Support **high-throughput** real-time signal processing pipelines
- Enable **distributed signal processing** across multiple nodes

## Blocks

### E2SAR Segmenter Sink

**Module:** `ejfat.e2sar_segmenter_sink`

Takes complex vectors from GNU Radio and sends them via E2SAR's data plane segmenter.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `uri` | string | (required) | EJFAT URI (e.g., `ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1:19522`) |
| `data_id` | int | 1 | Data identifier (uint16) |
| `event_src_id` | int | 1 | Event source identifier (uint32) |
| `vector_size` | int | 1024 | Size of input complex vectors |
| `use_cp` | bool | False | Use control plane registration |
| `mtu` | int | 9000 | Maximum transmission unit (bytes) |
| `rate_gbps` | float | 1.0 | Target data rate in Gbps |

#### Input

- **Type:** `complex64` vectors
- **Vector Length:** Specified by `vector_size` parameter
- Each input vector becomes one E2SAR event

#### Usage Example

```python
from gnuradio import blocks, ejfat

# Create signal source
signal_source = analog.sig_source_c(sample_rate, analog.GR_COS_WAVE, freq, 1.0, 0)

# Convert stream to vectors
stream_to_vector = blocks.stream_to_vector(gr.sizeof_gr_complex, 1024)

# E2SAR segmenter sink
e2sar_sink = ejfat.e2sar_segmenter_sink(
    uri='ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1:19522',
    data_id=1,
    event_src_id=1,
    vector_size=1024,
    use_cp=False,
    mtu=9000,
    rate_gbps=1.0
)

# Connect
self.connect(signal_source, stream_to_vector, e2sar_sink)
```

### E2SAR Reassembler Source

**Module:** `ejfat.e2sar_reassembler_source`

Receives complex vectors via E2SAR's data plane reassembler and outputs them to GNU Radio.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `uri` | string | (required) | EJFAT URI (e.g., `ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1`) |
| `data_ip` | string | 127.0.0.1 | Data plane IP address |
| `starting_port` | int | 19522 | Starting UDP port for receiving data |
| `vector_size` | int | 1024 | Size of output complex vectors |
| `num_recv_threads` | int | 1 | Number of receiver threads |
| `use_cp` | bool | False | Use control plane registration |
| `with_lb_header` | bool | True | Expect load balancer header (True for testing without LB) |
| `event_timeout_ms` | int | 5000 | Event timeout in milliseconds |

#### Output

- **Type:** `complex64` vectors
- **Vector Length:** Specified by `vector_size` parameter
- Each received E2SAR event becomes one or more output vectors

#### Usage Example

```python
from gnuradio import blocks, ejfat

# E2SAR reassembler source
e2sar_source = ejfat.e2sar_reassembler_source(
    uri='ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1',
    data_ip='127.0.0.1',
    starting_port=19522,
    vector_size=1024,
    num_recv_threads=1,
    use_cp=False,
    with_lb_header=True,
    event_timeout_ms=5000
)

# Convert vectors back to stream
vector_to_stream = blocks.vector_to_stream(gr.sizeof_gr_complex, 1024)

# File sink or other processing
file_sink = blocks.file_sink(gr.sizeof_gr_complex, 'output.dat', False)

# Connect
self.connect(e2sar_source, vector_to_stream, file_sink)
```

## Installation

### Prerequisites

1. **E2SAR with Python bindings** (`e2sar_py`) must be installed:
   ```bash
   cd $E2SAR_PATH
   meson setup build
   meson compile -C build
   export PYTHONPATH=$E2SAR_PATH/build/src/pybind:$PYTHONPATH
   ```

2. **GNU Radio environment** with the gr-ejfat module:
   ```bash
   cd gr-ejfat
   make install  # or use CMake build for C++ blocks
   ```

### Verifying Installation

```python
# Test E2SAR Python bindings
python -c "import e2sar_py; print('e2sar_py available')"

# Test GNU Radio blocks
python -c "from gnuradio.ejfat import e2sar_segmenter_sink, e2sar_reassembler_source; print('E2SAR blocks available')"
```

## Running the Example

The `test_e2sar_blocks.py` example demonstrates the E2SAR blocks in action.

### Transmitter Mode

Run in one terminal to transmit a test signal:

```bash
python examples/test_e2sar_blocks.py --tx --duration 30
```

### Receiver Mode

Run in another terminal to receive and save the signal:

```bash
python examples/test_e2sar_blocks.py --rx --duration 30 --output received_signal.dat
```

### Command Line Options

```
--tx                Run transmitter
--rx                Run receiver
--duration N        Run for N seconds (default: 10)
--data-ip IP        Data plane IP address (default: 127.0.0.1)
--data-port PORT    Data plane port (default: 19522)
--output FILE       Output file for receiver (default: None)
```

## Configuration

### EJFAT URI Format

The EJFAT URI specifies the EJFAT infrastructure endpoints:

```
ejfat://[token@]lb_host:lb_port/lb_path[?sync=sync_host:sync_port&data=data_host[:data_port]]
```

- **lb_host:lb_port** - Load balancer address
- **sync_host:sync_port** - Synchronization service address
- **data_host[:data_port]** - Data plane destination (port optional, sink only)

### Vector Size Selection

The `vector_size` parameter determines:
- Number of complex samples per E2SAR event
- Latency vs. throughput tradeoff
- Memory usage per event

**Recommendations:**
- **Low latency:** 256-512 samples
- **Balanced:** 1024-2048 samples
- **High throughput:** 4096-8192 samples

### Performance Tuning

1. **MTU Size:** Set to match your network (1500 for standard Ethernet, 9000 for jumbo frames)
2. **Rate Limit:** Set `rate_gbps` to match your network capacity
3. **Receiver Threads:** Increase `num_recv_threads` for high-rate reception
4. **Event Timeout:** Adjust `event_timeout_ms` based on network latency

## Testing

Unit tests are provided for both blocks:

```bash
# Test segmenter sink
python python/ejfat/qa_e2sar_segmenter_sink.py

# Test reassembler source
python python/ejfat/qa_e2sar_reassembler_source.py
```

**Note:** Full integration tests require E2SAR infrastructure to be running.

## Troubleshooting

### "e2sar_py module not found"

Ensure E2SAR Python bindings are in your PYTHONPATH:
```bash
export PYTHONPATH=$E2SAR_PATH/build/src/pybind:$PYTHONPATH
```

### "Error starting E2SAR segmenter/reassembler"

Check:
1. EJFAT URI is correctly formatted
2. Network connectivity to EJFAT infrastructure
3. Control plane is accessible (if `use_cp=True`)
4. Data plane IP and port are not in use

### No data received

Verify:
1. Transmitter and receiver use matching URIs
2. Data plane IP and port match between sender and receiver
3. Firewall allows UDP traffic on the data port
4. `with_lb_header=True` when testing without a load balancer

## Architecture

### Data Flow

**Transmit Path:**
```
GNU Radio Stream → Stream to Vector → E2SAR Segmenter Sink → Network
```

**Receive Path:**
```
Network → E2SAR Reassembler Source → Vector to Stream → GNU Radio Stream
```

### Threading Model

- **Segmenter:** Uses E2SAR's internal send threads for non-blocking transmission
- **Reassembler:** Uses E2SAR's internal receive threads for non-blocking reception
- **GNU Radio:** work() function is called by GNU Radio scheduler

### Memory Management

- Vectors are copied into E2SAR events (segmenter side)
- E2SAR manages event buffer allocation and cleanup
- Received vectors are zero-copied when possible (reassembler side)

## Related Documentation

- [E2SAR GitHub Repository](https://github.com/JeffersonLab/E2SAR)
- [GNU Radio Out-of-Tree Modules](https://wiki.gnuradio.org/index.php/OutOfTreeModules)
- [EJFAT Project Documentation](https://jeffersonlab.github.io/ejfat/)

## License

SPDX-License-Identifier: GPL-3.0-or-later
