# E2SAR Configuration Guide

This document explains the configuration options for E2SAR segmenter and reassembler blocks, with focus on control plane vs. no control plane modes.

## Control Plane Overview

E2SAR supports two operating modes:

### 1. **No Control Plane Mode** (Standalone, Simple Testing) ✓ CURRENT

In this mode, E2SAR operates independently without worker registration or dynamic load balancing.

**Use Cases:**
- Local loopback testing
- Simple point-to-point communication
- Development and debugging
- Scenarios where load balancing is not needed

**Configuration:**
```python
# Segmenter
e2sar_segmenter_sink(
    uri=ejfat_uri,
    data_id=1285,
    event_src_id=287454020,
    vector_size=1024,
    use_cp=False,        # ← No control plane
    mtu=9000,
    rate_gbps=1.0
)

# Reassembler
e2sar_reassembler_source(
    uri=ejfat_uri,
    data_ip="127.0.0.1",
    starting_port=19522,
    vector_size=1024,
    num_recv_threads=1,
    use_cp=False,        # ← No control plane
    with_lb_header=True,
    event_timeout_ms=5000
)
```

**Advantages:**
- ✓ Simpler setup - no control plane server needed
- ✓ Faster startup
- ✓ No network dependencies beyond data plane
- ✓ Ideal for testing and development

**Limitations:**
- ✗ No dynamic load balancing
- ✗ No worker registration
- ✗ No PID-based rate control
- ✗ No slot allocation management

---

### 2. **With Control Plane Mode** (Production, Multi-Worker)

In this mode, E2SAR connects to a control plane server for worker registration and dynamic load balancing.

**Use Cases:**
- Production deployments
- Multiple worker nodes
- Dynamic load balancing needed
- Adaptive rate control
- Distributed processing

**Configuration:**
```python
# Segmenter
e2sar_segmenter_sink(
    uri=ejfat_uri,
    data_id=1285,
    event_src_id=287454020,
    vector_size=1024,
    use_cp=True,         # ← Enable control plane
    mtu=9000,
    rate_gbps=1.0
)

# Reassembler
e2sar_reassembler_source(
    uri=ejfat_uri,
    data_ip="127.0.0.1",
    starting_port=19522,
    vector_size=1024,
    num_recv_threads=1,
    use_cp=True,                    # ← Enable control plane
    use_host_address=False,         # Use hostname for gRPC
    period_ms=100,                  # SendState period
    validate_cert=True,             # Validate TLS cert

    # PID Controller Parameters
    epoch_ms=1000,                  # PID update period
    ki=0.1,                         # Integral gain
    kp=0.5,                         # Proportional gain
    kd=0.05,                        # Derivative gain
    set_point=50.0,                 # Target queue % (50%)

    # Load Balancing Parameters
    weight=1.0,                     # Worker weight
    min_factor=0.5,                 # Min slot allocation
    max_factor=2.0,                 # Max slot allocation

    with_lb_header=True,
    event_timeout_ms=5000
)
```

**Advantages:**
- ✓ Dynamic load balancing across workers
- ✓ PID-based adaptive rate control
- ✓ Worker health monitoring
- ✓ Slot allocation management
- ✓ Better for production systems

**Requirements:**
- ✓ Control plane server running
- ✓ Network connectivity to control plane
- ✓ gRPC properly configured
- ✓ TLS certificates (if validation enabled)

---

## Current Test Configuration

All test flowgraphs in this directory are configured for **No Control Plane Mode**:

| File | Segmenter use_cp | Reassembler use_cp |
|------|------------------|-------------------|
| `test_e2sar_loopback.grc` | False | False |
| `test_e2sar_simple.py` | False | False |
| `../../gr-ejfat/examples/test_e2sar_blocks.py` | False | False |

This configuration is ideal for:
- ✓ Local loopback testing (127.0.0.1)
- ✓ Simple validation of E2SAR functionality
- ✓ Development without external dependencies
- ✓ Quick smoke tests

---

## Parameter Reference

### Segmenter Parameters

#### Core Parameters (Always Required)
```python
uri               # EJFAT connection string
data_id           # Data stream identifier (uint16)
event_src_id      # Event source identifier (uint32)
vector_size       # Samples per event
mtu               # Maximum transmission unit (bytes)
rate_gbps         # Target data rate (Gbps)
```

#### Control Plane Parameter
```python
use_cp            # Enable/disable control plane (True/False)
```

### Reassembler Parameters

#### Core Parameters (Always Required)
```python
uri               # EJFAT connection string
data_ip           # Local IP to bind for data reception
starting_port     # First UDP port for data reception
vector_size       # Samples per event (must match segmenter)
num_recv_threads  # Number of receiver threads
```

#### Network Parameters
```python
with_lb_header       # Expect LB header in packets (True/False)
event_timeout_ms     # Event reassembly timeout (milliseconds)
rcv_socket_buf_size  # Socket receive buffer size (bytes)
port_range           # Number of ports as 2^N (-1 = auto)
```

#### Control Plane Parameters (Only when use_cp=True)
```python
use_cp               # Enable control plane (True/False)
use_host_address     # Use IP instead of hostname for gRPC
period_ms            # SendState update period (milliseconds)
validate_cert        # Validate TLS certificate (True/False)
```

#### PID Control Parameters (Only when use_cp=True)
```python
epoch_ms             # PID controller update period (ms)
ki                   # Integral gain
kp                   # Proportional gain
kd                   # Derivative gain
set_point            # Target queue occupancy (%)
```

#### Load Balancing Parameters (Only when use_cp=True)
```python
weight               # Relative worker processing power
min_factor           # Minimum slot allocation multiplier
max_factor           # Maximum slot allocation multiplier
```

---

## EJFAT URI Format

The URI tells E2SAR how to connect to the EJFAT infrastructure:

```
ejfat://useless@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345&data=127.0.0.1:19522
```

Breaking this down:

| Component | Value | Purpose | Note for Testing |
|-----------|-------|---------|------------------|
| Scheme | `ejfat://` | Protocol identifier | Always required |
| User | `useless` | Authentication (unused) | Can be dummy for testing |
| LB Host | `192.168.100.1` | Load balancer IP | Can be dummy for loopback |
| LB Port | `9876` | Load balancer port | Can be dummy for loopback |
| LB ID | `/lb/1` | Load balancer instance | Can be dummy for loopback |
| Sync | `sync=192.168.0.1:12345` | Sync server address | Can be dummy for loopback |
| Data | `data=127.0.0.1:19522` | **Data plane address** | **Must be valid!** |

### For No Control Plane Mode (Current Configuration)

**Only the data IP and port matter!** The other fields can be dummy values:

```python
# Minimal working URI for loopback testing
ejfat_uri = "ejfat://test@dummy:9999/lb/1?sync=0.0.0.0:0&data=127.0.0.1:19522"
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^         ^^^^^^^^^^^^^^^^
                    Can be dummy values                      Must be valid!
```

### For With Control Plane Mode

**All fields must be valid and point to real services:**

```python
# Production URI with real control plane
ejfat_uri = "ejfat://user@lb.example.com:9876/lb/1?sync=sync.example.com:12345&data=10.0.1.100:19522"
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^
                    Must point to real load balancer and sync server              Must be valid!
```

---

## Switching Between Modes

### To Disable Control Plane (Current Configuration) ✓

In **test_e2sar_loopback.grc**:
```yaml
ejfat_e2sar_segmenter_sink_0:
  use_cp: 'False'

ejfat_e2sar_reassembler_source_0:
  use_cp: 'False'
  # PID and load balancing parameters ignored when use_cp=False
```

In **test_e2sar_simple.py**:
```python
# Segmenter
self.e2sar_sink = e2sar_segmenter_sink(
    uri=EJFAT_URI,
    data_id=DATA_ID,
    event_src_id=EVENT_SRC_ID,
    vector_size=VECTOR_SIZE,
    use_cp=False,  # ← No control plane
    mtu=9000,
    rate_gbps=1.0
)

# Reassembler
self.e2sar_source = e2sar_reassembler_source(
    uri=EJFAT_URI,
    data_ip=DATA_IP,
    starting_port=DATA_PORT,
    vector_size=VECTOR_SIZE,
    num_recv_threads=1,
    use_cp=False,  # ← No control plane
    with_lb_header=True,
    event_timeout_ms=5000
)
```

### To Enable Control Plane

1. **Update the EJFAT URI** to point to real services
2. **Set use_cp=True** in both segmenter and reassembler
3. **Configure PID parameters** (reassembler only)
4. **Configure load balancing parameters** (reassembler only)
5. **Ensure control plane server is running**

Example for GRC (edit in GNU Radio Companion):

```yaml
ejfat_e2sar_reassembler_source_0:
  use_cp: 'True'
  use_host_address: 'False'
  period_ms: '100'
  validate_cert: 'True'
  epoch_ms: '1000'
  ki: '0.1'
  kp: '0.5'
  kd: '0.05'
  set_point: '50.0'
  weight: '1.0'
  min_factor: '0.5'
  max_factor: '2.0'
```

---

## Verification

### Check Current Configuration

**For GRC flowgraph:**
```bash
grep "use_cp" test_e2sar_loopback.grc
```

Expected output:
```
    use_cp: 'False'
    use_cp: 'False'
```

**For Python script:**
```bash
grep "use_cp" test_e2sar_simple.py
```

Expected output:
```python
    use_cp=False,
    use_cp=False,
```

### Runtime Verification

When running with **use_cp=False**, you should see:
- ✓ Immediate startup (no control plane connection)
- ✓ Data transmission starts right away
- ✓ No gRPC-related messages

When running with **use_cp=True**, you should see:
- Worker registration messages
- gRPC connection status
- PID controller updates
- Slot allocation updates

---

## Troubleshooting

### Problem: "Control plane connection failed"

**Solution:** You're trying to use control plane mode without a control plane server.

Change `use_cp=True` to `use_cp=False` in your flowgraph.

### Problem: "gRPC error" or "TLS certificate validation failed"

**Solution:** Control plane is enabled but not configured correctly.

Either:
1. Disable control plane: `use_cp=False`
2. Or configure control plane properly with valid URI and certificates

### Problem: Data not being received in loopback test

**Check:**
1. ✓ `use_cp=False` in both segmenter and reassembler
2. ✓ URI data field points to correct IP:port (e.g., `127.0.0.1:19522`)
3. ✓ Firewall allows UDP on the data port
4. ✓ `with_lb_header=True` in reassembler
5. ✓ `vector_size` matches in both blocks

---

## Summary

**Current Configuration (All Test Flowgraphs):**
- ✓ No control plane mode (`use_cp=False`)
- ✓ Standalone operation
- ✓ Perfect for local testing
- ✓ No external dependencies

**To Enable Control Plane:**
1. Set `use_cp=True`
2. Configure valid EJFAT URI
3. Set PID and load balancing parameters
4. Ensure control plane server is accessible

**Recommendation:**
- Use **no control plane** for development and testing
- Use **with control plane** for production deployments with multiple workers

---

## See Also

- E2SAR Test README: `E2SAR_TEST_README.md`
- Segmenter API: `../../custom/segmenter_api.md`
- Reassembler API: `../../custom/reassembler_api.md`
- Block definitions: `../../gr-ejfat/grc/*.block.yml`
