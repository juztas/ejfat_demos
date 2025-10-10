# E2SAR Python Reassembler API (`e2sar_py`)

The E2SAR library provides Python bindings for reassembling UDP packet segments back into complete data events. The Reassembler receives packets from the EJFAT load balancer and reconstructs the original events.

## Module Structure

The Python module is organized as:
```python
import e2sar_py
from e2sar_py.DataPlane import Reassembler
```

## Main Classes

### 1. **Reassembler** (`e2sar_py.DataPlane.Reassembler`)

The Reassembler receives UDP segments and reconstructs complete events. It runs on or next to worker nodes performing event processing.

**Constructors:**

```python
# With explicit data IP and number of threads
reas = Reassembler(uri, data_ip, starting_port,
                   num_recv_threads=1,
                   rflags=ReassemblerFlags())

# With explicit data IP and CPU core affinity
reas = Reassembler(uri, data_ip, starting_port,
                   cpu_core_list,
                   rflags=ReassemblerFlags())

# Auto-detect data IP with number of threads
reas = Reassembler(uri, starting_port,
                   num_recv_threads=1,
                   rflags=ReassemblerFlags(),
                   v6=False)

# Auto-detect data IP with CPU core affinity
reas = Reassembler(uri, starting_port,
                   cpu_core_list,
                   rflags=ReassemblerFlags(),
                   v6=False)
```

**Parameters:**
- `uri` (`EjfatURI`): EJFAT URI with lb_id and instance token
- `data_ip` (`ip.address`, optional): IP address (v4/v6) to listen on (auto-detected if omitted)
- `starting_port` (uint16): Starting UDP port number for listening
- `num_recv_threads` (size_t, optional): Number of receive threads (default: 1)
- `cpu_core_list` (list of ints, optional): CPU cores for receive threads (sets affinity)
- `rflags` (`ReassemblerFlags`, optional): Configuration flags
- `v6` (bool, optional): Use IPv6 dataplane (default: False)

### 2. **ReassemblerFlags** (`Reassembler.ReassemblerFlags`)

Configuration structure with sensible defaults:

```python
flags = Reassembler.ReassemblerFlags()

# Configurable fields:
flags.useCP = True                  # Use control plane (sendState, registerWorker)
flags.useHostAddress = False        # Use IP address for gRPC instead of hostname
flags.period_ms = 100               # SendState thread period (ms)
flags.validateCert = True           # Validate control plane TLS certificate
flags.epoch_ms = 1000               # PID control epoch period (ms)
flags.Ki = 0.0                      # PID integral gain
flags.Kp = 0.0                      # PID proportional gain
flags.Kd = 0.0                      # PID derivative gain
flags.setPoint = 0.0                # PID setpoint (queue occupancy %)
flags.portRange = -1                # 2^portRange listening ports (-1 = auto)
flags.withLBHeader = False          # Expect LB header in packets (testing only)
flags.eventTimeout_ms = 500         # Timeout for incomplete events (ms)
flags.rcvSocketBufSize = 3*1024*1024  # Socket receive buffer size (3MB)
flags.weight = 1.0                  # Node processing power weight
flags.min_factor = 0.5              # Min slot allocation factor
flags.max_factor = 2.0              # Max slot allocation factor

# Load from INI file
flags = Reassembler.ReassemblerFlags.getFromINI("reassembler_config.ini")
```

**Key Flag Details:**
- `portRange`: If -1, number of ports matches CPU cores or threads. Valid range: [0, 14] for 2^portRange ports
- `eventTimeout_ms`: How long to wait for incomplete events before giving up
- `weight`, `min_factor`, `max_factor`: Used for load balancer slot allocation in PID control

## Core Methods

### **Worker Registration:**

Before starting, register with the control plane:

```python
result = reas.registerWorker("worker-node-1")
if result.has_error():
    error = result.error()
    print(f"Registration error: {error.message}")
```

### **Starting the Reassembler:**

```python
result = reas.openAndStart()
if result.has_error():
    error = result.error()
    print(f"Error: {error.message}")
```

### **Receiving Events:**

**1. Non-blocking receive with bytes:**

```python
event_buf = None
event_len = 0
event_num = 0
data_id = 0

# Returns tuple: (length, bytes, event_num, data_id)
result = reas.getEventBytes()
length, data, event_num, data_id = result

if length > 0:
    # Process event
    print(f"Received event {event_num} with {length} bytes")
elif length == -1:
    # Queue empty, no event available
    pass
elif length == -2:
    # Error occurred
    print("Error receiving event")
```

**2. Blocking receive with bytes:**

```python
# Returns tuple: (length, bytes, event_num, data_id)
# wait_ms=0 means wait forever
result = reas.recvEventBytes(wait_ms=1000)
length, data, event_num, data_id = result

if length > 0:
    # Process event
    print(f"Received event {event_num}: {data}")
elif length == -1:
    # Timeout or no event
    pass
elif length == -2:
    # Error occurred
    pass
```

**3. Non-blocking receive as NumPy array:**

```python
import numpy as np

# Returns tuple: (length, array, event_num, data_id)
result = reas.get1DNumpyArray(np.dtype('float32'))
length, array, event_num, data_id = result

if length > 0:
    # Process numpy array
    print(f"Received {len(array)} elements")
    # array is already typed as float32
elif length == -1:
    # Queue empty
    pass
elif length == -2:
    # Error occurred
    pass
```

**4. Blocking receive as NumPy array:**

```python
import numpy as np

# Returns tuple: (length, array, event_num, data_id)
result = reas.recv1DNumpyArray(np.dtype('uint8'), wait_ms=500)
length, array, event_num, data_id = result

if length > 0:
    # Process event as numpy array
    print(f"Event {event_num}: {array}")
```

**Return Values:**
- `length > 0`: Event received successfully (length in bytes)
- `length == -1`: No event available (non-blocking) or timeout (blocking)
- `length == -2`: Error occurred during receive

### **Statistics:**

```python
# Get reassembly statistics
stats = reas.getStats()
print(f"Events succeeded: {stats.eventSuccess}")
print(f"Enqueue losses: {stats.enqueueLoss}")
print(f"Reassembly losses: {stats.reassemblyLoss}")
print(f"Last errno: {stats.lastErrno}")
print(f"gRPC errors: {stats.grpcErrCnt}")
print(f"Data errors: {stats.dataErrCnt}")
print(f"Last E2SAR error: {stats.lastE2SARError}")
```

**ReportedStats fields:**
- `eventSuccess`: Number of events successfully reassembled
- `enqueueLoss`: Events lost because internal queue was full
- `reassemblyLoss`: Events lost due to missing segments (timeout)
- `lastErrno`: Last system errno (use `strerror()`)
- `grpcErrCnt`: Number of gRPC/control plane errors
- `dataErrCnt`: Number of dataplane socket errors
- `lastE2SARError`: Last E2SAR error code

### **Lost Event Tracking:**

```python
# Get information about lost events
result = reas.get_LostEvent()

if result.has_value():
    event_num, data_id, num_fragments = result.value()
    print(f"Lost event {event_num} (data_id={data_id}) had {num_fragments} fragments")
elif result.has_error():
    # Queue is empty - no lost events to report
    pass
```

### **Per-Port Statistics:**

```python
# Only call after stopThreads()
reas.stopThreads()

result = reas.get_FDStats()
if result.has_value():
    fd_stats = result.value()  # List of (port, fragment_count) tuples
    for port, count in fd_stats:
        print(f"Port {port}: {count} fragments received")
```

### **Configuration Queries:**

```python
# Get number of receive threads
num_threads = reas.get_numRecvThreads()

# Get listening port range (start_port, end_port)
start_port, end_port = reas.get_recvPorts()
print(f"Listening on ports {start_port}-{end_port}")

# Get port range value (2^portRange ports)
port_range = reas.get_portRange()

# Get data IP address as string
data_ip = reas.get_dataIP()
print(f"Listening on IP: {data_ip}")
```

### **Worker Deregistration:**

```python
# Deregister from control plane
result = reas.deregisterWorker()
if result.has_error():
    print(f"Deregistration error: {result.error().message}")
```

### **Cleanup:**

```python
reas.stopThreads()  # Stop all receive and control plane threads
# Destructor automatically calls deregisterWorker() if registered
```

## Supporting Classes

### **EjfatURI**

Same as for Segmenter (see segmenter_api.md):

```python
# Create from string
uri = e2sar_py.EjfatURI.get_from_string(
    "ejfat://192.168.1.1:12345?sync=192.168.1.2:12346&data=192.168.1.3:12347",
    tt=e2sar_py.EjfatURI.TokenType.instance
).value()

# Create from environment variable
uri = e2sar_py.EjfatURI.get_from_env("EJFAT_URI").value()

# Create from file
uri = e2sar_py.EjfatURI.get_from_file("/tmp/ejfat_uri").value()
```

### **Result Types**

All methods that can fail return a `result<T>` type:

```python
result = reas.openAndStart()

if result.has_value():
    value = result.value()
elif result.has_error():
    error = result.error()
    print(f"Error code: {error.code}")
    print(f"Message: {error.message}")
```

## Example Usage

### Basic Receiver

```python
import e2sar_py
from e2sar_py.DataPlane import Reassembler
import numpy as np

# Create URI
uri = e2sar_py.EjfatURI.get_from_env().value()

# Configure flags
flags = Reassembler.ReassemblerFlags()
flags.eventTimeout_ms = 1000
flags.rcvSocketBufSize = 10*1024*1024  # 10MB

# Create reassembler (auto-detect IP, 4 threads)
reas = Reassembler(uri, starting_port=19522,
                   num_recv_threads=4,
                   rflags=flags)

# Register worker
if reas.registerWorker("worker-1").has_error():
    print("Failed to register worker")
    exit(1)

# Start receiving
if reas.openAndStart().has_error():
    print("Failed to start reassembler")
    exit(1)

# Receive events
events_received = 0
try:
    while events_received < 1000:
        # Non-blocking receive as numpy array
        length, array, event_num, data_id = reas.get1DNumpyArray(np.dtype('uint8'))

        if length > 0:
            events_received += 1
            print(f"Event {event_num}: {length} bytes, data_id={data_id}")
            # Process array...
        elif length == -2:
            print("Error receiving event")
            break
        # If length == -1, queue empty, continue

except KeyboardInterrupt:
    print("Interrupted")

# Get statistics
stats = reas.getStats()
print(f"\nStatistics:")
print(f"  Events received: {stats.eventSuccess}")
print(f"  Enqueue losses: {stats.enqueueLoss}")
print(f"  Reassembly losses: {stats.reassemblyLoss}")

# Cleanup
reas.deregisterWorker()
reas.stopThreads()
```

### Blocking Receiver with Timeout

```python
import e2sar_py
from e2sar_py.DataPlane import Reassembler

uri = e2sar_py.EjfatURI.get_from_env().value()
reas = Reassembler(uri, starting_port=19522)

reas.registerWorker("blocking-worker")
reas.openAndStart()

# Blocking receive with 1 second timeout
while True:
    length, data, event_num, data_id = reas.recvEventBytes(wait_ms=1000)

    if length > 0:
        print(f"Received event {event_num}: {data[:100]}")  # Print first 100 bytes
    elif length == -1:
        print("Timeout waiting for event")
    else:
        print("Error")
        break

reas.stopThreads()
```

### CPU Affinity Example

```python
import e2sar_py
from e2sar_py.DataPlane import Reassembler

uri = e2sar_py.EjfatURI.get_from_env().value()

# Use specific CPU cores for NUMA affinity
cpu_cores = [0, 1, 2, 3]  # Cores on same NUMA node as NIC

flags = Reassembler.ReassemblerFlags()
flags.portRange = 2  # 2^2 = 4 ports (matches 4 threads)

reas = Reassembler(uri, starting_port=19522,
                   cpu_core_list=cpu_cores,
                   rflags=flags)

reas.registerWorker("numa-aware-worker")
reas.openAndStart()

print(f"Listening on {reas.get_numRecvThreads()} threads")
start, end = reas.get_recvPorts()
print(f"Port range: {start}-{end}")

# Receive events...
```

## Key Features

1. **Multiple receive threads** for high-throughput reassembly
2. **CPU core affinity** for NUMA-aware performance
3. **Automatic event reassembly** from UDP segments
4. **NumPy array support** for efficient data handling
5. **Blocking and non-blocking** receive modes
6. **Event timeout handling** for incomplete events
7. **Lost event tracking** with detailed statistics
8. **Control plane integration** with worker registration
9. **PID-based load balancing** for dynamic slot allocation
10. **Per-port statistics** for traffic analysis

## Threading Model

The Reassembler uses multiple internal threads:
- **Receive threads**: Listen on UDP ports and reassemble events (configurable count)
- **GC thread**: Garbage collects incomplete events that timeout
- **SendState thread**: Sends periodic state updates to control plane (if useCP=True)

Events are reassembled in receive threads and placed in a lock-free queue for retrieval via `getEvent()` or `recvEvent()`.

## Port Allocation

The number of listening ports is determined by:
1. `portRange` in ReassemblerFlags if >= 0 (opens 2^portRange ports)
2. Number of CPU cores if `cpu_core_list` is provided
3. Number of receive threads if `num_recv_threads` is specified

Ports are distributed evenly across receive threads for load balancing.

## Implementation Reference

This API is defined in the E2SAR repository:
- Python bindings: `/Users/yak/Projects/E2SAR/src/pybind/py_e2sarDP.cpp:246-487`
- C++ header: `/Users/yak/Projects/E2SAR/include/e2sarDPReassembler.hpp`
