# E2SAR Segmenter/Reassembler Test Flowgraphs

This directory contains test flowgraphs for the E2SAR segmenter and reassembler GNU Radio blocks.

## Overview

The E2SAR (Experiment to Software Analysis in Realtime) system provides:
- **Segmenter**: Breaks data streams into events and sends them via EJFAT
- **Reassembler**: Receives events from EJFAT and reconstructs the data stream

These test flowgraphs demonstrate basic functionality in a loopback configuration.

## Available Tests

### 1. Simple Python Script (`test_e2sar_simple.py`)

A standalone Python script that runs a complete loopback test.

**Features:**
- Single flowgraph with both segmenter and reassembler
- Generates a 10 kHz test tone
- Sends via E2SAR segmenter
- Receives via E2SAR reassembler
- Runs for 30 seconds and displays status

**Usage:**
```bash
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/e2sar_test
conda activate gnuradio
./test_e2sar_simple.py
```

### 2. GNU Radio Companion Flowgraph (`test_e2sar_loopback.grc`)

A visual flowgraph that can be edited in GNU Radio Companion (GRC).

**Features:**
- Visual signal flow diagram
- Frequency spectrum display
- Time domain display
- Interactive controls
- Same loopback configuration as simple script

**Usage:**
```bash
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/e2sar_test
conda activate gnuradio
gnuradio-companion test_e2sar_loopback.grc
```

Then click the "Execute" (play) button in GRC to run the flowgraph.

### 3. Separate TX/RX Scripts (`../../gr-ejfat/examples/test_e2sar_blocks.py`)

A more advanced example that can run transmitter and receiver separately.

**Usage:**
```bash
# Terminal 1 - Run transmitter
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/gr-ejfat/examples
conda activate gnuradio
python test_e2sar_blocks.py --tx --duration 30

# Terminal 2 - Run receiver
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/gr-ejfat/examples
conda activate gnuradio
python test_e2sar_blocks.py --rx --duration 30 --output received_data.bin
```

## Configuration

### Default Parameters

All test flowgraphs use these default parameters:

| Parameter | Value | Description |
|-----------|-------|-------------|
| Data IP | 127.0.0.1 | Localhost for loopback testing |
| Data Port | 19522 | UDP port for data plane |
| Data ID | 0x0505 (1285) | Identifies this data stream |
| Event Source ID | 0x11223344 (287454020) | Identifies event source |
| Vector Size | 1024 samples | Events per packet |
| Sample Rate | 1 MSps | Signal sample rate |
| Signal Frequency | 10 kHz | Test tone frequency |
| MTU | 9000 bytes | Maximum transmission unit |
| Rate | 1.0 Gbps | Target data rate |

### EJFAT URI Format

The EJFAT URI specifies the load balancer and data plane configuration:

```
ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1:19522
```

Breaking this down:
- `ejfat://` - URI scheme
- `useless@192.168.100.1:9876` - Load balancer address (dummy for local testing)
- `/lb/1` - Load balancer ID
- `sync=192.168.0.1:12345` - Sync address (dummy for local testing)
- `data=127.0.0.1:19522` - Data plane IP and port (actual loopback address)

**Note:** For loopback testing, the load balancer and sync addresses can be dummy values. Only the data IP and port need to be valid.

## Prerequisites

### 1. E2SAR Installation

The E2SAR Python bindings must be installed and available:

```bash
# Check if E2SAR is available
python -c "import e2sar_py; print('E2SAR found')"
```

If not found, install E2SAR:

```bash
# Locate E2SAR repository (common locations)
E2SAR_PATH=../../E2SAR  # or ~/Projects/E2SAR, etc.

# Build E2SAR with Python bindings
cd $E2SAR_PATH
meson setup build
meson compile -C build

# Add to Python path
export PYTHONPATH=$E2SAR_PATH/build/src/pybind:$PYTHONPATH
```

### 2. GNU Radio Environment

Activate the GNU Radio conda environment:

```bash
conda activate gnuradio
```

### 3. gr-ejfat Module

The GNU Radio EJFAT module must be installed:

```bash
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/gr-ejfat
make install
```

## Signal Flow

### Transmitter Path

```
Signal Source (10 kHz tone)
    ↓
Throttle (prevent CPU overload)
    ↓
Stream to Vector (convert to events)
    ↓
E2SAR Segmenter Sink (send via EJFAT)
```

### Receiver Path

```
E2SAR Reassembler Source (receive from EJFAT)
    ↓
Vector to Stream (convert back to stream)
    ↓
Display / Sink
```

## Expected Results

When running successfully, you should see:

1. **Console output:**
   - "E2SAR Python bindings found"
   - "Starting flowgraph..."
   - Status updates every 5 seconds
   - "Test completed successfully!"

2. **In GRC GUI (if using .grc file):**
   - Frequency spectrum showing a peak at 10 kHz
   - Time domain showing a clean sinusoidal waveform
   - Smooth, continuous signal reception

## Troubleshooting

### "e2sar_py module not found"

**Solution:** Install E2SAR Python bindings (see Prerequisites above)

### "Destination port unreachable" or networking errors

**Possible causes:**
- Firewall blocking UDP port 19522
- Another process using port 19522
- Network interface issues

**Solutions:**
```bash
# Check if port is in use
sudo lsof -i :19522

# Temporarily disable firewall (macOS)
sudo pfctl -d

# Try a different port
# Edit the flowgraph to change data_port to something else (e.g., 19523)
```

### Segmenter starts but reassembler receives no data

**Possible causes:**
- Loopback interface not working
- E2SAR configuration mismatch
- URI format error

**Solutions:**
```bash
# Test UDP loopback
# Terminal 1: Listen
nc -u -l 19522

# Terminal 2: Send
echo "test" | nc -u 127.0.0.1 19522

# If this doesn't work, your loopback interface has issues
```

### "Dependency 'boost' not found" or other build errors

**Solution:** Check that the GNU Radio environment is properly set up with E2SAR-compatible dependencies. See `../gnuradio/CLAUDE.md` for environment setup instructions.

## Advanced Usage

### Modifying Parameters

To test different configurations, you can modify:

**In Python scripts:**
- Edit the configuration constants at the top of the file
- Example: Change `VECTOR_SIZE = 1024` to `VECTOR_SIZE = 512`

**In GRC flowgraph:**
- Open in GNU Radio Companion
- Click on any block to edit its parameters
- Double-click variables to change their values
- Click "Generate" (gear icon) then "Execute" (play icon)

### Adding Analysis

You can add additional blocks for analysis:

**Spectrum analysis:**
- Add `QT GUI Frequency Sink` block
- Connect to received signal

**Time domain:**
- Add `QT GUI Time Sink` block
- Connect to received signal

**File recording:**
- Add `File Sink` block
- Connect to received signal
- Specify output filename

**Statistics:**
- Add `Probe Signal` blocks
- Monitor signal levels, SNR, etc.

## Network Testing

To test over a real network (not loopback):

1. **On the receiver machine:**
   - Find IP address: `ifconfig` or `ip addr`
   - Note the IP (e.g., 192.168.1.100)

2. **Update configuration:**
   - Change `DATA_IP` from `127.0.0.1` to receiver's IP
   - Update EJFAT URI accordingly

3. **Run receiver first:**
   ```bash
   python test_e2sar_blocks.py --rx --data-ip 192.168.1.100
   ```

4. **Then run transmitter:**
   ```bash
   python test_e2sar_blocks.py --tx --data-ip 192.168.1.100
   ```

## Performance Tips

### For High Data Rates

1. **Increase buffer sizes:**
   - In reassembler: `rcv_socket_buf_size=10485760` (10 MB)

2. **Use multiple receiver threads:**
   - In reassembler: `num_recv_threads=4`

3. **Adjust port range:**
   - In reassembler: `port_range=2` (for 4 ports = 2^2)

4. **Enable jumbo frames (if supported):**
   - In segmenter: `mtu=9000`

### For Low Latency

1. **Reduce vector size:**
   - Smaller events = lower latency
   - Example: `vector_size=256`

2. **Reduce event timeout:**
   - In reassembler: `event_timeout_ms=1000`

## API Documentation

For detailed API documentation:

- Segmenter API: `../../custom/segmenter_api.md`
- Reassembler API: `../../custom/reassembler_api.md`
- E2SAR GitHub: https://github.com/JeffersonLab/E2SAR

## References

- GNU Radio Wiki: https://wiki.gnuradio.org/
- E2SAR Documentation: See E2SAR repository
- EJFAT Project: https://www.jlab.org/ejfat
