# E2SAR No Control Plane Configuration - Quick Reference

## ✓ Current Status: CONTROL PLANE DISABLED

All test flowgraphs are configured for standalone operation without control plane.

## Configuration at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│  E2SAR MODE: No Control Plane (Standalone)                  │
├─────────────────────────────────────────────────────────────┤
│  Segmenter:   use_cp = False                                │
│  Reassembler: use_cp = False                                │
├─────────────────────────────────────────────────────────────┤
│  Data IP:     127.0.0.1 (localhost)                         │
│  Data Port:   19522                                         │
│  Vector Size: 1024 samples                                  │
├─────────────────────────────────────────────────────────────┤
│  Status:      Ready for local loopback testing              │
│  Dependencies: None (no external services)                  │
└─────────────────────────────────────────────────────────────┘
```

## Verify Configuration

```bash
cd /Users/yak/Projects/EJFAT/ejfat_demos/e2sar_test/gnuradio/demos/e2sar_test/e2sar_test
./check_e2sar_config.sh
```

Expected output: `✓ Control Plane: DISABLED`

## Quick Start

### Option 1: Simple Python Script (Recommended for first test)

```bash
conda activate gnuradio
./test_e2sar_simple.py
```

**What you'll see:**
```
E2SAR Segmenter/Reassembler Loopback Test
Configuration:
  EJFAT URI:        ejfat://...&data=127.0.0.1:19522
  ...
✓ E2SAR Python bindings found
Starting flowgraph...
Press Ctrl+C to stop
Running... (5/30 seconds)
...
```

### Option 2: GNU Radio Companion (Visual Interface)

```bash
conda activate gnuradio
gnuradio-companion test_e2sar_loopback.grc
```

Then click the Execute (▶) button. You'll see:
- **Frequency spectrum** with 10 kHz peak
- **Time domain** showing clean sinusoid

## Block Configuration

### Segmenter (Transmit Side)

```python
e2sar_segmenter_sink(
    uri="ejfat://...&data=127.0.0.1:19522",
    data_id=1285,           # 0x0505
    event_src_id=287454020, # 0x11223344
    vector_size=1024,
    use_cp=False,           # ← NO CONTROL PLANE
    mtu=9000,
    rate_gbps=1.0
)
```

**Key Points:**
- `use_cp=False` - Standalone mode
- No worker registration
- No dynamic load balancing
- Sends data directly to specified address

### Reassembler (Receive Side)

```python
e2sar_reassembler_source(
    uri="ejfat://...&data=127.0.0.1:19522",
    data_ip="127.0.0.1",
    starting_port=19522,
    vector_size=1024,
    num_recv_threads=1,
    use_cp=False,           # ← NO CONTROL PLANE
    with_lb_header=True,    # Still expect LB header format
    event_timeout_ms=5000
)
```

**Key Points:**
- `use_cp=False` - Standalone mode
- No control plane connection
- No PID controller
- Direct UDP reception
- `with_lb_header=True` - Still processes EJFAT packet format

## What's Ignored in No Control Plane Mode

These parameters are **ignored** when `use_cp=False`:

### Reassembler (Control Plane Parameters)
```python
use_host_address=False,  # Ignored
period_ms=100,           # Ignored
validate_cert=True,      # Ignored
epoch_ms=1000,           # Ignored
ki=0.0,                  # Ignored (PID)
kp=0.0,                  # Ignored (PID)
kd=0.0,                  # Ignored (PID)
set_point=0.0,           # Ignored (PID)
weight=1.0,              # Ignored (Load balancing)
min_factor=0.5,          # Ignored (Load balancing)
max_factor=2.0,          # Ignored (Load balancing)
```

You can leave these at default values - they have no effect.

## EJFAT URI for No Control Plane

```
ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1:19522
        ^^^^^^^^                                                      ^^^^^^^^^^^^^^^^
        Can be dummy                                                  MUST BE VALID!
```

**In no control plane mode:**
- ✗ Load balancer address (`192.168.100.1:9876`) - not used
- ✗ Sync server address (`sync=192.168.0.1:12345`) - not used
- ✓ **Data address (`data=127.0.0.1:19522`) - MUST BE CORRECT!**

The data address is where packets are actually sent/received.

## Signal Flow (No Control Plane)

```
TRANSMITTER                           RECEIVER
───────────                           ────────

Signal Source
     ↓
Throttle
     ↓
Stream to Vector
     ↓
┌────────────────────┐                ┌────────────────────┐
│ E2SAR Segmenter    │   UDP Packets  │ E2SAR Reassembler  │
│ use_cp=False       │ ────────────→  │ use_cp=False       │
│                    │  127.0.0.1     │                    │
└────────────────────┘  :19522        └────────────────────┘
                                               ↓
                                      Vector to Stream
                                               ↓
                                      Display / Sink
```

**No gRPC connections, no control plane server, just UDP!**

## Files Configured

| File | Location | Segmenter | Reassembler |
|------|----------|-----------|-------------|
| `test_e2sar_loopback.grc` | demos/e2sar_test/ | use_cp='False' | use_cp='False' |
| `test_e2sar_simple.py` | demos/e2sar_test/ | use_cp=False | use_cp=False |
| `test_e2sar_blocks.py` | gr-ejfat/examples/ | use_cp=False | use_cp=False |

## Troubleshooting

### Problem: No data received

**Check:**
```bash
# 1. Verify configuration
./check_e2sar_config.sh

# 2. Check if port is available
sudo lsof -i :19522

# 3. Test UDP loopback
# Terminal 1:
nc -u -l 19522

# Terminal 2:
echo "test" | nc -u 127.0.0.1 19522

# If Terminal 1 doesn't show "test", your loopback has issues
```

### Problem: "Control plane connection failed"

**This should NOT happen with use_cp=False!**

If you see this:
1. Double-check: `grep use_cp test_e2sar_simple.py`
2. Should show: `use_cp=False` (not True)
3. Re-run: `./check_e2sar_config.sh`

### Problem: E2SAR not found

```bash
# Check E2SAR installation
python -c "import e2sar_py; print('OK')"

# If fails, install E2SAR:
cd $E2SAR_PATH
meson setup build
meson compile -C build
export PYTHONPATH=$E2SAR_PATH/build/src/pybind:$PYTHONPATH
```

## When to Use No Control Plane

✓ **Use no control plane when:**
- Testing locally (loopback)
- Developing new features
- Single transmitter → single receiver
- Don't need load balancing
- Want simple, fast setup

✗ **Don't use no control plane when:**
- Multiple worker nodes
- Need dynamic load balancing
- Production deployment
- Adaptive rate control needed
- Distributed processing

## Switching to Control Plane Mode

If you need to enable control plane:

1. **See full guide:** `E2SAR_CONFIGURATION.md`
2. **Change:** `use_cp=False` → `use_cp=True`
3. **Configure:** PID and load balancing parameters
4. **Update:** EJFAT URI with real control plane addresses
5. **Ensure:** Control plane server is running

## Performance in No Control Plane Mode

**Expected performance (loopback on localhost):**

| Metric | Typical Value |
|--------|---------------|
| Latency | < 1 ms |
| Throughput | Limited by CPU/throttle, not network |
| Packet loss | ~0% (loopback is reliable) |
| CPU usage | Low (single-threaded) |

**To improve performance:**
- Increase `num_recv_threads` (e.g., 4)
- Increase `rcv_socket_buf_size` (e.g., 10485760)
- Use larger `mtu` if network supports (e.g., 9000)
- Adjust `rate_gbps` for your data rate

## Summary

```
┌──────────────────────────────────────────────────────┐
│ ✓ All flowgraphs: NO CONTROL PLANE                  │
│ ✓ Configuration: Standalone loopback testing        │
│ ✓ Ready to run: ./test_e2sar_simple.py              │
│ ✓ No dependencies: Works immediately                │
└──────────────────────────────────────────────────────┘
```

**You're all set for testing!**

## See Also

- **Full configuration guide:** `E2SAR_CONFIGURATION.md`
- **Test usage guide:** `E2SAR_TEST_README.md`
- **Verify configuration:** `./check_e2sar_config.sh`
