# E2SAR Python Segmentation API (`e2sar_py`)

The E2SAR library provides Python bindings for segmenting data events into UDP packets that can be sent through the EJFAT load balancer. Here's a comprehensive overview:

## Module Structure

The Python module is organized as:
```python
import e2sar_py
from e2sar_py.DataPlane import Segmenter
```

## Main Classes

### 1. **Segmenter** (`e2sar_py.DataPlane.Segmenter`)

The Segmenter breaks up events into UDP segments consumable by the hardware load balancer.

**Constructor:**
```python
# Simple constructor
seg = Segmenter(uri, data_id, eventSrc_id, sflags=SegmenterFlags())

# With CPU core affinity
seg = Segmenter(uri, data_id, eventSrc_id, cpu_core_list, sflags=SegmenterFlags())
```

**Parameters:**
- `uri` (`EjfatURI`): EJFAT URI with sync and data addresses
- `data_id` (uint16): Unique identifier for the segmentation point (e.g., DAQ ID)
- `eventSrc_id` (uint32): Unique identifier for the transmitting host
- `cpu_core_list` (list of ints, optional): CPU cores to use for sending threads
- `sflags` (`SegmenterFlags`, optional): Configuration flags

### 2. **SegmenterFlags** (`Segmenter.SegmenterFlags`)

Configuration structure with sensible defaults:

```python
flags = Segmenter.SegmenterFlags()

# Configurable fields:
flags.dpV6 = False              # Use IPv6 dataplane
flags.connectedSocket = True    # Use connected sockets
flags.useCP = True              # Enable control plane (sync packets)
flags.syncPeriodMs = 1000       # Sync thread period (ms)
flags.syncPeriods = 2           # Number of sync periods for averaging
flags.mtu = 1500                # MTU size (0 = auto-detect)
flags.numSendSockets = 4        # Number of send sockets for LAG randomization
flags.sndSocketBufSize = 3*1024*1024  # Socket buffer size (3MB)
flags.rateGbps = -1.0           # Send rate in Gbps (-1 = unlimited)

# Load from INI file
flags = Segmenter.SegmenterFlags.getFromINI("segmenter_config.ini")
```

## Core Methods

### **Starting the Segmenter:**
```python
result = seg.openAndStart()
if result.has_error():
    error = result.error()
    print(f"Error: {error.message}")
```

### **Sending Events:**

**1. Immediate send with bytes:**
```python
data = b"your event data here"
result = seg.sendEvent(data, len(data),
                       _eventNum=0,      # Optional event number override
                       _dataId=0,         # Optional data ID override
                       entropy=0)         # Optional entropy for routing
```

**2. Send with NumPy array:**
```python
import numpy as np
array = np.array([1, 2, 3, 4], dtype=np.float32)
result = seg.sendNumpyArray(array, array.nbytes,
                            event_num=0,
                            data_id=0,
                            entropy=0)
```

**3. Queued send with callback (non-blocking):**
```python
def callback(arg):
    print(f"Event sent: {arg}")

# With buffer
result = seg.addToSendQueue(data, len(data),
                            _eventNum=0,
                            _dataId=0,
                            entropy=0,
                            callback=callback,
                            cbArg="event_info")

# With NumPy array
result = seg.addNumpyArrayToSendQueue(array, array.nbytes,
                                      _eventNum=0,
                                      _dataId=0,
                                      entropy=0,
                                      callback=callback,
                                      cbArg="event_info")
```

### **Statistics:**
```python
# Get send statistics
send_stats = seg.getSendStats()
print(f"Messages sent: {send_stats.msgCnt}")
print(f"Errors: {send_stats.errCnt}")
print(f"Last errno: {send_stats.lastErrno}")
print(f"Last E2SAR error: {send_stats.lastE2SARError}")

# Get sync statistics
sync_stats = seg.getSyncStats()
```

**ReportedStats fields:**
- `msgCnt`: Number of fragments/messages sent
- `errCnt`: Number of errors encountered
- `lastErrno`: Last system errno (use `strerror()`)
- `lastE2SARError`: Last E2SAR error code

### **Configuration Queries:**
```python
mtu = seg.getMTU()                # Get current MTU
max_payload = seg.getMaxPldLen()  # Get max payload length per packet
```

### **Cleanup:**
```python
seg.stopThreads()  # Stop all sending and sync threads
```

## Supporting Classes

### **EjfatURI**

```python
# Create from string
uri = e2sar_py.EjfatURI.get_from_string(
    "ejfat://192.168.1.1:12345?sync=192.168.1.2:12346&data=192.168.1.3:12347",
    tt=e2sar_py.EjfatURI.TokenType.admin
).value()

# Create from environment variable
uri = e2sar_py.EjfatURI.get_from_env("EJFAT_URI").value()

# Create from file
uri = e2sar_py.EjfatURI.get_from_file("/tmp/ejfat_uri").value()

# Query URI
cp_addr = uri.get_cp_addr()
data_addr = uri.get_data_addr_v4()
sync_addr = uri.get_sync_addr()
```

### **Result Types**

All methods that can fail return a `result<T>` type:

```python
result = seg.openAndStart()

if result.has_value():
    value = result.value()
elif result.has_error():
    error = result.error()
    print(f"Error code: {error.code}")
    print(f"Message: {error.message}")
```

## Example Usage

```python
import e2sar_py
from e2sar_py.DataPlane import Segmenter
import numpy as np

# Create URI
uri = e2sar_py.EjfatURI.get_from_env().value()

# Configure flags
flags = Segmenter.SegmenterFlags()
flags.mtu = 9000
flags.rateGbps = 10.0
flags.numSendSockets = 8

# Create segmenter
seg = Segmenter(uri, data_id=1, eventSrc_id=0x12345678, sflags=flags)

# Start
if seg.openAndStart().has_error():
    print("Failed to start segmenter")
    exit(1)

# Send events
for i in range(1000):
    data = np.random.randint(0, 255, 1024, dtype=np.uint8)
    result = seg.sendNumpyArray(data, data.nbytes, event_num=i)

    if result.has_error():
        print(f"Send error: {result.error().message}")
        break

# Get statistics
stats = seg.getSendStats()
print(f"Sent {stats.msgCnt} packets, {stats.errCnt} errors")

# Cleanup
seg.stopThreads()
```

## Key Features

1. **Thread-safe queued sending** with callbacks
2. **NumPy array support** for efficient data handling
3. **Rate limiting** and traffic shaping
4. **Multiple send sockets** for LAG randomization
5. **Automatic MTU detection** (Linux only)
6. **CPU core affinity** for performance
7. **Comprehensive statistics** tracking

## Implementation Reference

This API is defined in the E2SAR repository:
- Python bindings: `/Users/yak/Projects/E2SAR/src/pybind/py_e2sarDP.cpp:92-243`
- C++ header: `/Users/yak/Projects/E2SAR/include/e2sarDPSegmenter.hpp`
