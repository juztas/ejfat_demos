# Quick Start Guide

This guide will help you build and test the EJFAT SHM daemon in minutes.

## Prerequisites

1. **E2SAR library must be built first**:
   ```bash
   cd ~/Projects/E2SAR
   . ./setup_compile_env.sh
   meson setup build
   meson compile -C build
   ```

2. **Python ejfat_shm package** (for test writer):
   ```bash
   cd /Users/yak/Projects/Claude/gnu-radio/ejfat_shm
   pip install -e .
   ```

## Build the Daemon

```bash
cd daemon

# Build with default E2SAR location
make

# Or specify custom E2SAR build directory
make E2SAR_BUILD_DIR=~/Projects/E2SAR/build
```

Expected output:
```
Using E2SAR library: /Users/yak/Projects/E2SAR/build/src/libe2sar.so
gcc -Wall -Wextra -O2 -g -fPIC -Iinclude -I/Users/yak/Projects/E2SAR/include -c src/shm_reader.c -o src/shm_reader.o
gcc -Wall -Wextra -O2 -g -fPIC -Iinclude -I/Users/yak/Projects/E2SAR/include -c src/config.c -o src/config.o
g++ -Wall -Wextra -O2 -g -fPIC -std=c++17 -Iinclude -I/Users/yak/Projects/E2SAR/include -c src/ejfat_shm_daemon.cpp -o src/ejfat_shm_daemon.o
g++ -o ejfat_shm_daemon src/shm_reader.o src/config.o src/ejfat_shm_daemon.o -pthread -lrt -L/Users/yak/Projects/E2SAR/build/src -le2sar -Wl,-rpath,/Users/yak/Projects/E2SAR/build/src
```

## Quick Test

### Option 1: Test with Mock EJFAT (no UDPLBd required)

1. **Edit test config** to disable control plane:
   ```bash
   nano test_config.conf
   ```

   Set:
   ```ini
   use_control_plane = false
   ```

2. **Terminal 1 - Start daemon**:
   ```bash
   ./ejfat_shm_daemon -c test_config.conf -f
   ```

   Expected output:
   ```
   [INFO] Opening SHM FIFO: test_fifo
   [INFO] Initializing EJFAT Segmenter with URI: ejfat://...
   [INFO] EJFAT Segmenter initialized successfully
   [INFO] Daemon initialized successfully
   [INFO] Starting event loop...
   ```

3. **Terminal 2 - Run test writer**:
   ```bash
   ./test_writer.py
   ```

   Expected output:
   ```
   Creating SHM FIFO: test_fifo
   FIFO created successfully
   Starting event writer...
   [   0] Sent event 0, size 45 bytes
   [  10] Sent event 10, size 45 bytes
   ...
   ```

4. **Observe daemon output**:
   ```
   [DEBUG] Sending event 0, size 45
   [DEBUG] Sending event 1, size 45
   [INFO] Stats: Events sent=100, failed=0, SHM(writes=100, reads=100, drops=0, avail=0), Send(msgs=100, bytes=4500, errs=0), Sync(msgs=2, errs=0)
   ```

5. **Stop daemon** (Ctrl+C in Terminal 1):
   ```
   ^C[INFO] Received signal 2, shutting down...
   [INFO] Event loop finished. Total events sent: 100, failed: 0
   [INFO] Cleaning up...
   [INFO] Daemon exited
   ```

### Option 2: Test with Full EJFAT Stack (requires UDPLBd)

If you have UDPLBd running:

1. **Edit test config**:
   ```ini
   use_control_plane = true
   ejfat_uri = ejfats://your_token@your_cp_host:18347/lb/your_lb_id?sync=sync_ip:port&data=data_ip:port
   ```

2. **Run same test as above**

3. **Verify on receiver nodes** that events are being distributed

## Troubleshooting

### "Failed to open shared memory"
- Writer hasn't created FIFO yet
- Check: `ls -l /dev/shm | grep ejfat_shm`
- Solution: Start writer first, or remove stale SHM: `rm /dev/shm/ejfat_shm_*`

### "E2SAR library not found"
- E2SAR not built
- Solution: Build E2SAR first (see Prerequisites)
- Or specify path: `make E2SAR_BUILD_DIR=/path/to/e2sar/build`

### "Segmentation fault"
- Check E2SAR build matches runtime library
- Verify EJFAT URI is valid
- Try with debug: `gdb --args ./ejfat_shm_daemon -c test_config.conf -f`

### Daemon hangs on startup
- Check if trying to connect to unavailable control plane
- Solution: Set `use_control_plane = false` for testing

### No events being sent
- Check daemon is running: `ps aux | grep ejfat_shm_daemon`
- Check daemon logs (foreground mode shows all output)
- Verify writer is sending: check SHM stats in writer output

## Next Steps

1. **Production Configuration**:
   - Copy `ejfat_shm_daemon.conf.example` to `/etc/`
   - Edit for your environment
   - Set `foreground = false` to run as daemon

2. **systemd Integration**:
   - See `README_DAEMON.md` for systemd service file
   - Enable auto-start: `systemctl enable ejfat_shm_daemon`

3. **Performance Tuning**:
   - Adjust socket buffer sizes
   - Set CPU affinity
   - Tune MTU for your network
   - See "Performance Tuning" in `README_DAEMON.md`

4. **Integration**:
   - Replace `test_writer.py` with your real event source
   - Configure FIFO capacity and entry size appropriately
   - Monitor statistics and tune as needed

## File Locations

After successful test:

- Daemon binary: `./ejfat_shm_daemon`
- Test config: `./test_config.conf`
- Test writer: `./test_writer.py`
- Full docs: `./README_DAEMON.md`
- Example config: `./ejfat_shm_daemon.conf.example`

## Common Commands

```bash
# Build
make

# Clean build
make clean && make

# Run in foreground with debug
./ejfat_shm_daemon -c test_config.conf -f

# Check daemon is running
ps aux | grep ejfat_shm_daemon

# View real-time logs (if using syslog)
tail -f /var/log/ejfat_shm_daemon.log

# Kill daemon
pkill ejfat_shm_daemon
# or
kill $(cat /var/run/ejfat_shm_daemon.pid)

# Check shared memory
ls -lh /dev/shm | grep ejfat_shm

# Clean up shared memory
rm /dev/shm/ejfat_shm_*
```

## Support

If you encounter issues:

1. Check daemon runs in foreground mode with debug logs (`log_level = 3`)
2. Verify E2SAR library path: `ldd ./ejfat_shm_daemon`
3. Test Python writer independently
4. Check EJFAT URI is valid
5. Review `README_DAEMON.md` for detailed troubleshooting

## Quick Reference

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `test_writer.py` | Generate test events | Testing daemon functionality |
| `test_config.conf` | Minimal config | Quick testing without UDPLBd |
| `ejfat_shm_daemon.conf.example` | Full config | Production deployment |
| `-f` flag | Foreground mode | Debugging, development |
| Daemon mode | Background operation | Production |

Enjoy your high-performance event broadcasting! 🚀
