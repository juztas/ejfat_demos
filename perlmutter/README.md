# EJFAT Perlmutter Demo

This directory contains a Makefile for building and operating the EJFAT (ESnet JLab FPGA Accelerated Transport) load balancer on NERSC's Perlmutter supercomputer. The Makefile uses `podman-hpc` containers and SLURM for distributed computing.

## Prerequisites

- Access to a Perlmutter login node
- `podman-hpc` installed and configured
- Network access to `ejfat-lb.es.net`
- `SCRATCH` environment variable set (typically configured on Perlmutter)

## Quick Start

1. **Build the container image:**
   ```bash
   make build
   ```

2. **Reserve a load balancer instance:**
   ```bash
   make reserve EJFAT_URI_BETA=<your-ejfat-uri>
   ```

3. **Run a receiver (in one terminal):**
   ```bash
   make receive
   ```

4. **Send data (in another terminal):**
   ```bash
   make send
   ```

5. **Monitor the system (optional):**
   ```bash
   make monitor
   ```

6. **Free the reservation when done:**
   ```bash
   make free
   ```

## Available Targets

### Setup & Configuration

- **`make help`** - Display help information about the EJFAT system
- **`make build`** - Build the `e2sar_dev` container image from the parent directory's Containerfile
- **`make test`** - Display current configuration values (MY_IP, MY_INTERFACE, LB_IP, etc.)

### Load Balancer Management

- **`make reserve`** - Reserve a load balancer instance
  - Requires: `EJFAT_URI_BETA` environment variable
  - Creates an `INSTANCE_URI` file with the reservation details
  - Example: `make reserve EJFAT_URI_BETA=ejfat://your-uri LB_NAME=my_test LB_RESERVE_DURATION=5`

- **`make free`** - Release the current load balancer reservation

### Data Transmission

- **`make send`** - Send data frames through the load balancer
  - Uses the reserved INSTANCE_URI
  - Configurable via TX_RATE, TX_LENGTH, SEND_SOCKETS, NFRAMES, DATA_ID

- **`make receive`** - Receive data frames
  - Configurable via RX_DURATION, RX_THREADS, RX_BUFSIZE, RX_TIMEOUT, etc.

### File Transfer

- **`make gen_test_files`** - Generate random test files for file transfer testing
  - Creates files in `$SCRATCH/storage/ejfat_ft/data` by default
  - Configurable via FT_NUMFILES, FT_FILESIZE, FT_PREFIX, FT_EXTENSION

- **`make send_file`** - Send files through the load balancer
  - Reads files from DATA_DIR
  - Configurable via FT_RATE, FT_SOCKETS, FT_EXTENSION

- **`make receive_file`** - Receive files
  - Saves files to DATA_RX_DIR
  - Configurable via FT_TIMEOUT, FT_THREADS, FT_EXTENSION, FT_PREFIX

### Monitoring

- **`make monitor`** - Monitor the load balancer and network traffic
  - Configurable via MONITOR_PORTS, MONITOR_INTERVAL

## Configuration Variables

All variables can be overridden on the command line using `make target VAR=value`.

### Network Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `IP_VERSION` | `-6` | IP version to use (-4 for IPv4, -6 for IPv6) |
| `LB_IP` | Auto-detected | Load balancer IP address |
| `MY_IP` | Auto-detected | Local IP address |
| `MY_INTERFACE` | Auto-detected | Network interface name |
| `EJFAT_URI_BETA` | (required) | EJFAT URI for making reservations |
| `INSTANCE_URI` | From file | Instance URI from the reservation |

### Performance Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RX_DURATION` | 120 | Receiver duration in seconds |
| `RX_THREADS` | 16 | Number of receiver threads |
| `RX_BUFSIZE` | 400000000 | Receiver buffer size in bytes |
| `RX_TIMEOUT` | 7000 | Receiver timeout in milliseconds |
| `RX_CORES` | 1 | Number of cores for receiver |
| `RX_DEQ` | 16 | Dequeue depth for receiver |
| `TX_RATE` | 0.1 | Transmit rate in Gbps |
| `TX_LENGTH` | 2097152 | Transmit data length in bytes (2 MB) |
| `SEND_SOCKETS` | 8 | Number of sending sockets |
| `NFRAMES` | 10000 | Number of frames to send |
| `DATA_ID` | Random 1-1000 | Data ID for transmission |

### File Transfer Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FT_EXTENSION` | root | File extension for file transfer |
| `FT_PREFIX` | test | File prefix for file transfer |
| `FT_RATE` | 1 | File transfer rate in Gbps |
| `FT_SOCKETS` | 4 | Number of sockets for file transfer |
| `FT_TIMEOUT` | 7000 | File transfer timeout in milliseconds |
| `FT_THREADS` | 4 | Number of threads for file transfer |
| `FT_NUMFILES` | 25 | Number of test files to generate |
| `FT_FILESIZE` | 300 | Size of test files in MB |
| `DATA_DIR` | `$SCRATCH/storage/ejfat_ft/data` | Source data directory |
| `DATA_RX_DIR` | `$SCRATCH/storage/ejfat_ft/data_rx` | Receive data directory |

### Monitoring Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MONITOR_PORTS` | 10000-10015 | Port range to monitor (format: start-end) |
| `MONITOR_INTERVAL` | 0.1 | Monitoring sample interval in seconds |

### Load Balancer Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LB_RESERVE_DURATION` | 5 | Reservation duration in days |
| `LB_NAME` | yk_testing | Load balancer instance name |

### Logging Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_DIR` | ./ | Directory for log files |

## Usage Examples

### Basic Data Transfer Test

```bash
# Terminal 1: Reserve and receive
make reserve EJFAT_URI_BETA=ejfat://your-uri
make receive RX_DURATION=60 RX_THREADS=8

# Terminal 2: Send data
make send TX_RATE=0.5 NFRAMES=50000

# Terminal 3: Monitor (optional)
make monitor

# When done
make free
```

### File Transfer Test

```bash
# Generate test files
make gen_test_files FT_NUMFILES=10 FT_FILESIZE=100

# Terminal 1: Receive files
make receive_file

# Terminal 2: Send files
make send_file FT_RATE=2 FT_SOCKETS=8

# Verify received files
ls -lh $SCRATCH/storage/ejfat_ft/data_rx
```

### High-Performance Configuration

```bash
# Optimize for high throughput
make receive RX_THREADS=32 RX_BUFSIZE=800000000 RX_CORES=2
make send TX_RATE=10 SEND_SOCKETS=16 TX_LENGTH=4194304
```

### IPv4 Mode

```bash
# Use IPv4 instead of IPv6
make reserve IP_VERSION=-4 EJFAT_URI_BETA=ejfat://your-uri
make receive IP_VERSION=-4
make send IP_VERSION=-4
```

## Workflow

1. **Build** the container image (once)
2. **Reserve** a load balancer instance
3. **Start receiver(s)** on one or more nodes
4. **Start sender(s)** to transmit data
5. **Monitor** performance (optional)
6. **Free** the reservation when complete

## Files Created

- `INSTANCE_URI` - Contains the reservation URI (auto-generated by `make reserve`)
- Log files in `LOG_DIR` (if configured)
- Received files in `DATA_RX_DIR` for file transfers

## Troubleshooting

- **Check configuration**: Run `make test` to verify network settings
- **IP detection fails**: Manually set `MY_IP` and `MY_INTERFACE`
- **No INSTANCE_URI**: Make sure to run `make reserve` before other operations
- **Permission errors**: Ensure podman-hpc is properly configured
- **Network issues**: Verify connectivity to `ejfat-lb.es.net` and firewall rules

## Notes

- The Makefile is designed to run on Perlmutter login nodes
- Each target runs in an isolated container with host networking
- The `INSTANCE_URI` file stores the reservation details and is automatically read by other targets
- All paths are automatically detected or use Perlmutter's `$SCRATCH` directory
- The container must be built before running any other targets

## Author

Yatish Kumar, July 2024
