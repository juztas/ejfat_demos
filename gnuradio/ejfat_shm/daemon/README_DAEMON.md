# EJFAT SHM Daemon

A high-performance C/C++ daemon that bridges events from a POSIX shared memory FIFO to the EJFAT network protocol for distributed event processing.

## Overview

The `ejfat_shm_daemon` reads events from a shared memory FIFO (created by the Python `ejfat_shm` package or any compatible writer) and broadcasts them using the EJFAT protocol via the E2SAR library. This enables zero-copy, low-latency event distribution from processes like GNU Radio to distributed compute nodes.

```
┌─────────────────┐
│ Writer Process  │  (Python/GNU Radio/C)
│   ejfat_shm     │
└────────┬────────┘
         │ POSIX SHM FIFO
         ▼
┌─────────────────┐      ┌──────────────────┐
│ ejfat_shm_daemon│─────▶│  E2SAR Segmenter │
│   (this daemon) │      │  (UDP/EJFAT)     │
└─────────────────┘      └──────┬───────────┘
                                │ Network
                                ▼
                         ┌──────────────────┐
                         │  Load Balancer   │
                         │    (UDPLBd)      │
                         └──────┬───────────┘
                                │
                        ┌───────┴────────┐
                        ▼                ▼
                  ┌──────────┐    ┌──────────┐
                  │ Worker 1 │    │ Worker 2 │
                  └──────────┘    └──────────┘
```

## Features

- **Zero-copy SHM reading**: Direct memory-mapped access to shared FIFO
- **EJFAT protocol**: Uses E2SAR library for segmentation and reliable UDP delivery
- **High performance**: Lock-free FIFO, configurable buffering, rate limiting
- **Flexible deployment**: Run as daemon or foreground process
- **Comprehensive configuration**: Fine-tune network, performance, and system settings
- **Production-ready**: Signal handling, PID files, syslog integration, statistics

## Prerequisites

### Build Dependencies

1. **E2SAR Library**: EJFAT protocol implementation
   ```bash
   # Clone and build E2SAR (see E2SAR README for full instructions)
   git clone --recurse-submodules https://github.com/JeffersonLab/E2SAR.git
   cd E2SAR
   . ./setup_compile_env.sh
   meson setup build
   meson compile -C build
   ```

2. **System Libraries**:
   - POSIX threads (pthread)
   - POSIX real-time (rt) - for semaphores and shared memory
   - C++17 compatible compiler (g++ or clang++)

3. **E2SAR Dependencies** (transitively required):
   - Boost libraries (>= 1.70)
   - gRPC (>= 1.40)
   - Protocol Buffers

### Runtime Dependencies

1. **UDPLBd Load Balancer** (optional, if using control plane):
   - See [UDPLBd documentation](https://github.com/esnet/udplbd)

2. **Shared Memory Writer**:
   - Python `ejfat_shm` package, or
   - Any compatible SHM FIFO writer

## Building

```bash
cd daemon

# Default build (assumes E2SAR in ~/Projects/E2SAR/build_fec)
make

# Custom E2SAR location
make E2SAR_BUILD_DIR=~/path/to/E2SAR/build

# Install to /usr/local
sudo make install

# Install to custom prefix
make install PREFIX=/opt/ejfat
```

### Makefile Variables

- `E2SAR_DIR`: E2SAR source directory (default: `~/Projects/E2SAR`)
- `E2SAR_BUILD_DIR`: E2SAR build directory (default: `$(E2SAR_DIR)/build_fec`)
- `PREFIX`: Installation prefix (default: `/usr/local`)

## Configuration

Copy the example configuration file and edit for your environment:

```bash
cp ejfat_shm_daemon.conf.example /etc/ejfat_shm_daemon.conf
nano /etc/ejfat_shm_daemon.conf
```

### Required Settings

```ini
# Shared memory FIFO name (must match writer)
fifo_name = ejfat_fifo

# EJFAT URI for load balancer
ejfat_uri = ejfat://token@cp_host:18347/lb/1?sync=sync_ip:12345&data=data_ip:19522
```

### Key Configuration Sections

1. **SHM FIFO Settings**: FIFO name and read timeout
2. **EJFAT Settings**: URI, data/event source IDs
3. **Network Settings**: IPv6, MTU, sync parameters
4. **Performance Settings**: Socket count, buffer sizes, rate limiting
5. **System Settings**: CPU affinity, logging, daemon mode
6. **Statistics**: Reporting interval

See `ejfat_shm_daemon.conf.example` for detailed documentation of all options.

## Usage

### Running in Foreground (for testing)

```bash
# Run in foreground with verbose logging
./ejfat_shm_daemon -c /etc/ejfat_shm_daemon.conf -f
```

### Running as Daemon

```bash
# Start daemon
./ejfat_shm_daemon -c /etc/ejfat_shm_daemon.conf

# Check status
ps aux | grep ejfat_shm_daemon

# Stop daemon
kill $(cat /var/run/ejfat_shm_daemon.pid)

# View logs
tail -f /var/log/ejfat_shm_daemon.log
# or (if using syslog)
journalctl -u ejfat_shm_daemon -f
```

### Command-Line Options

- `-c <file>`: Configuration file (required)
- `-f`: Run in foreground (overrides config file setting)
- `-v`: Print version and exit
- `-h`: Show help message

### Signals

- `SIGTERM`, `SIGINT`, `SIGHUP`: Graceful shutdown
- `SIGPIPE`: Ignored (handled internally)

## systemd Integration

Create `/etc/systemd/system/ejfat_shm_daemon.service`:

```ini
[Unit]
Description=EJFAT SHM to Network Bridge Daemon
After=network.target

[Service]
Type=forking
PIDFile=/var/run/ejfat_shm_daemon.pid
ExecStart=/usr/local/bin/ejfat_shm_daemon -c /etc/ejfat_shm_daemon.conf
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure
RestartSec=5s

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/run /var/log

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ejfat_shm_daemon
sudo systemctl start ejfat_shm_daemon
sudo systemctl status ejfat_shm_daemon
```

## Complete Example: Python Writer + Daemon

### 1. Create Python Writer

```python
from ejfat_shm import ShmFIFO, WriteStatus
import time

# Create FIFO
fifo = ShmFIFO("ejfat_fifo", capacity=1024, entry_size=4096, create=True)

# Write events
for i in range(100):
    data = f"Event {i} data".encode()
    result = fifo.write_event(data, event_number=i)

    if result.status == WriteStatus.SUCCESS:
        print(f"Wrote event {i}")
    else:
        print(f"Failed to write event {i}: {result.status}")

    time.sleep(0.1)

fifo.close()
fifo.unlink()
```

### 2. Configure Daemon

```ini
# /etc/ejfat_shm_daemon.conf
fifo_name = ejfat_fifo
ejfat_uri = ejfat://token@192.168.1.100:18347/lb/1?sync=192.168.1.10:12345&data=192.168.1.20:19522
foreground = true
log_level = 3
stats_interval = 10
```

### 3. Run Daemon

```bash
# Terminal 1: Start daemon
./ejfat_shm_daemon -c /etc/ejfat_shm_daemon.conf -f

# Terminal 2: Run writer
python3 writer.py
```

### 4. Monitor

```bash
# Daemon output shows:
# - SHM FIFO connection
# - EJFAT segmenter initialization
# - Events received and sent
# - Periodic statistics (every 10 seconds)
```

## Monitoring and Statistics

When `stats_interval` is configured (in seconds), the daemon periodically logs:

- **Events**: Total sent and failed
- **SHM FIFO**: Writes, reads, drops, available entries
- **Network Send**: Messages, bytes, errors
- **Sync**: Sync messages, errors

Example log output:

```
[INFO] Stats: Events sent=1000, failed=0, SHM(writes=1000, reads=1000, drops=0, avail=0), Send(msgs=1000, bytes=65536000, errs=0), Sync(msgs=10, errs=0)
```

## Performance Tuning

### 1. System Limits

Increase socket buffer limits:

```bash
# Increase max socket buffer size (Linux)
sudo sysctl -w net.core.wmem_max=33554432  # 32MB
sudo sysctl -w net.core.rmem_max=33554432  # 32MB

# Make permanent
echo "net.core.wmem_max = 33554432" | sudo tee -a /etc/sysctl.conf
echo "net.core.rmem_max = 33554432" | sudo tee -a /etc/sysctl.conf
```

### 2. CPU Affinity

Pin daemon to specific CPU core to reduce context switching:

```ini
cpu_core = 2  # Use core 2
```

### 3. Socket Configuration

```ini
num_send_sockets = 8          # More sockets for better LAG distribution
send_socket_buffer_size = 16777216  # 16MB per socket
```

### 4. Rate Limiting

```ini
rate_gbps = 10.0  # Limit to 10 Gbps
smooth_rate = true  # Smooth traffic shaping
```

### 5. MTU Optimization

```ini
mtu = 9000  # Jumbo frames (if network supports)
```

## Troubleshooting

### Daemon won't start

1. **Check E2SAR library path**:
   ```bash
   ldd ./ejfat_shm_daemon | grep e2sar
   ```

2. **Verify SHM FIFO exists**:
   ```bash
   ls -l /dev/shm | grep ejfat_shm
   ```

3. **Check configuration**:
   ```bash
   ./ejfat_shm_daemon -c /etc/ejfat_shm_daemon.conf -f
   ```

### High drop rate

- Increase FIFO capacity in writer
- Increase `num_send_sockets`
- Check network congestion
- Reduce `rate_gbps` if saturating network

### Connection refused

- Verify EJFAT URI is correct
- Check UDPLBd is running (if using control plane)
- Try with `use_control_plane = false` for debugging

### Semaphore timeout errors

- Writer may have stopped
- Check `read_timeout` setting
- Verify writer is still running and writing

## Architecture Details

### SHM Reader

The daemon uses a C implementation (`shm_reader.c`) that:

1. Opens POSIX shared memory (`shm_open`)
2. Memory-maps the FIFO structure (`mmap`)
3. Opens data semaphore for blocking reads (`sem_open`)
4. Reads entries from circular buffer using atomic operations
5. Compatible with Python `ejfat_shm` package

### EJFAT Integration

Uses E2SAR C++ library (`Segmenter` class) to:

1. Parse EJFAT URI and connect to control plane
2. Fragment large events into MTU-sized UDP packets
3. Add EJFAT headers (LB, RE, Sync)
4. Send data and periodic sync messages
5. Handle rate limiting and buffer management

### Threading Model

- **Main thread**: Reads from SHM FIFO, queues events to EJFAT
- **E2SAR threads** (internal):
  - Send thread: Transmits UDP packets
  - Sync thread: Sends periodic sync messages

## Security Considerations

1. **Shared Memory**: Accessible to all users with permissions
   - Use appropriate permissions on `/dev/shm/ejfat_shm_*`

2. **Network**: EJFAT uses UDP (no encryption by default)
   - Use TLS-enabled EJFAT URI (`ejfats://`) for control plane

3. **Daemon Mode**: Runs with privileges of launching user
   - Consider using dedicated service account

4. **PID File**: Default location requires root access
   - Override with writable location for non-root usage

## Files and Directories

```
daemon/
├── Makefile                          # Build system
├── README_DAEMON.md                  # This file
├── ejfat_shm_daemon.conf.example     # Example configuration
├── include/
│   ├── shm_reader.h                 # SHM FIFO reader API
│   └── config.h                     # Configuration structures
└── src/
    ├── shm_reader.c                 # SHM FIFO reader implementation
    ├── config.c                     # Configuration parser
    └── ejfat_shm_daemon.cpp         # Main daemon
```

## License

MIT License (same as ejfat_shm package)

## See Also

- [E2SAR Documentation](https://jeffersonlab.github.io/E2SAR-doc/)
- [UDPLBd Documentation](https://github.com/esnet/udplbd)
- [ejfat_shm Python Package](../README.md)
- [EJFAT Project](https://github.com/JeffersonLab/)

## Contributing

Contributions welcome! Please ensure:
- Code compiles without warnings
- Configuration validation works
- Signal handling is clean
- Documentation is updated

## Support

For issues or questions:
- Check E2SAR documentation and examples
- Review daemon logs with `log_level = 3`
- Test with `-f` flag for foreground debugging
- Verify SHM FIFO with Python examples first
