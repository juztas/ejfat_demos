# EJFAT ESnetDTN Demo

Quick start guide for running EJFAT sender and receiver on ESnet DTN nodes.

## Prerequisites

- Access to ESnet DTN nodes
- EJFAT load balancer reservation
- Conda environment with e2sar installed

## Quick Start

### 1. Reserve a Load Balancer

```bash
cd /path/to/ESnetDTN
make -f ../scripts/Makefile.local reserve
```

This creates an `INSTANCE_URI` file containing your load balancer instance.

### 2. Configure Receiver

Copy and edit the receiver configuration:

```bash
cp receiver_config.yaml.example receiver_config.yaml
# Edit receiver_config.yaml as needed
```

Key settings:
- `rx_duration`: How long to receive (seconds)
- `rx_cores`: Number of CPU cores to use
- `ip_version`: 4 or 6

### 3. Configure Sender

Copy and edit the sender configuration:

```bash
cp sender_config.yaml.example sender_config.yaml
# Edit sender_config.yaml as needed
```

Key settings:
- `tx_rate`: Transmission rate in Gbps
- `tx_length`: Packet size in bytes
- `nframes`: Number of frames to send

### 4. Start Receiver

**Local execution:**
```bash
./start_receiver.sh receiver_config.yaml
```

**Remote execution via SSH:**
```bash
./start_receiver.sh --node nid001234 receiver_config.yaml
```

### 5. Start Sender

**Local execution:**
```bash
./start_sender.sh sender_config.yaml
```

**Remote execution via SSH:**
```bash
./start_sender.sh --node nid001234 sender_config.yaml
```

## Configuration Files

### receiver_config.yaml

Controls receiver behavior and generates `reassembler_config.ini`:
- **Receiver settings**: Duration, cores, buffer sizes, timeouts
- **Reassembler settings**: Control plane, data plane, PID controller
- **Monitoring**: Port ranges and intervals

See `receiver_config.yaml.example` for all options.

### sender_config.yaml

Controls sender behavior and generates `segmenter_config.ini`:
- **Sender settings**: Rate, packet size, number of frames, sockets
- **Segmenter settings**: Control plane, data plane parameters
- **Performance tuning**: MTU, buffer sizes, smoothing

See `sender_config.yaml.example` for all options.

## Generated Files

The start scripts automatically generate INI files:
- `reassembler_config.ini` - Generated from receiver YAML config
- `segmenter_config.ini` - Generated from sender YAML config

These INI files configure the underlying E2SAR libraries.

## Direct Makefile Usage

You can also use the Makefiles directly:

```bash
# Local execution
make -f ../scripts/Makefile.local receive RX_DURATION=60 RX_CORES=4

# Remote SSH execution
make -f ../scripts/Makefile.ssh send NODE=nid001234 TX_RATE=1.0

# Free load balancer
make -f ../scripts/Makefile.local free
```

## Troubleshooting

**No INSTANCE_URI file:**
```bash
make -f ../scripts/Makefile.local reserve
```

**Cannot connect:**
- Verify IP version matches load balancer configuration
- Check network interface selection
- Ensure firewall rules allow traffic

**Permission errors:**
- Make sure scripts are executable: `chmod +x start_*.sh`

## Advanced Configuration

### Reassembler INI Settings

Fine-tune reassembler behavior via YAML:
- **Control plane**: TLS validation, address preferences
- **Data plane**: Port range, event timeout, socket buffers
- **PID controller**: Gains, weights, slot allocation factors

### Segmenter INI Settings

Fine-tune segmenter behavior via YAML:
- **Control plane**: Warmup period, sync intervals
- **Data plane**: Connected sockets, MTU, rate smoothing
- **Multi-port mode**: For back-to-back testing

## More Information

For detailed configuration options, see the example YAML files:
- `receiver_config.yaml.example` - All receiver/reassembler options
- `sender_config.yaml.example` - All sender/segmenter options
