# EJFAT Shared Memory FIFO - Detailed Usage Guide

## Overview

The `ejfat_shm` library provides a high-performance, zero-copy FIFO queue using POSIX shared memory. It uses a single-writer, single-reader design with semaphore-based notifications for efficient inter-process communication.

## Installation

```bash
pip install -e .
```

## Architecture

- **Writer Process**: Creates shared memory and semaphores, writes data
- **Reader Process**: Opens existing shared memory, reads data
- **Communication**: Lock-free circular buffer with semaphore notifications
- **Data Format**: Each entry contains event_number (8 bytes) + data_size (8 bytes) + data payload

## Writer Process

### Basic Usage

```python
from ejfat_shm import ShmFIFO, WriteStatus

# Create FIFO (writer must create=True)
fifo = ShmFIFO(
    name="my_fifo",           # Unique identifier
    capacity=100,             # Number of entries in circular buffer
    entry_size=4096,          # Max bytes per entry (including 16-byte metadata)
    create=True               # Writer creates the shared memory
)

# Write data
event_number = 1000
data = b"your binary data here"

result = fifo.write_event(data, event_number)

# Check write status
if result.status == WriteStatus.SUCCESS:
    print(f"Write successful, total drops: {result.total_drops}")
elif result.status == WriteStatus.FIFO_FULL:
    print(f"FIFO full! Total drops: {result.total_drops}")
    # Handle backpressure (wait, drop, alert, etc.)
elif result.status == WriteStatus.DATA_TOO_LARGE:
    print(f"Data exceeds max size! Total drops: {result.total_drops}")

# Cleanup when done
fifo.close()
fifo.unlink()  # Remove shared memory (writer only!)
```

### Context Manager Pattern (Recommended)

```python
from ejfat_shm import ShmFIFO, WriteStatus

with ShmFIFO("my_fifo", capacity=100, entry_size=4096, create=True) as fifo:
    for i in range(100):
        data = f"event_{i}".encode()
        result = fifo.write_event(data, event_number=i)

        if result.status != WriteStatus.SUCCESS:
            print(f"Write failed: {result.status}")
# Automatically calls close() and unlink()
```

### Handling Binary Data

```python
import struct
from ejfat_shm import ShmFIFO, WriteStatus

fifo = ShmFIFO("my_fifo", capacity=100, entry_size=4096, create=True)

# Pack structured data
timestamp = 1234567890.123
sequence_num = 42
sensor_value = 3.14159

# Pack as: double + int + float
data = struct.pack('dif', timestamp, sequence_num, sensor_value)

result = fifo.write_event(data, event_number=sequence_num)
```

### Calculating Entry Size

The `entry_size` parameter determines the maximum size for each FIFO entry:

```python
# Entry format: [event_number (8 bytes)] [data_size (8 bytes)] [data payload]
METADATA_SIZE = 16  # bytes

# If you need to store 4080 bytes of data:
max_data_size = 4080
entry_size = METADATA_SIZE + max_data_size  # = 4096

fifo = ShmFIFO("my_fifo", entry_size=entry_size, create=True)
```

### Error Handling

```python
from ejfat_shm import ShmFIFO, ShmFIFOExistsError

try:
    fifo = ShmFIFO("my_fifo", create=True)
except ShmFIFOExistsError:
    print("FIFO already exists! Either:")
    print("1. Use create=False to open existing FIFO")
    print("2. Call unlink() first to remove old FIFO")
    print("3. Use a different name")
```

### Monitoring Statistics

```python
fifo = ShmFIFO("my_fifo", create=True)

# Get current statistics
stats = fifo.get_stats()
print(f"Total writes: {stats['total_writes']}")
print(f"Total drops: {stats['total_drops']}")
print(f"Entries available: {stats['entries_available']}")
print(f"Capacity: {stats['capacity']}")
print(f"Entry size: {stats['entry_size']}")
```

## Reader Process

### Basic Usage

```python
from ejfat_shm import ShmFIFO, ShmFIFONotFoundError

# Open existing FIFO (reader must create=False)
try:
    fifo = ShmFIFO("my_fifo", create=False)
except ShmFIFONotFoundError:
    print("FIFO not found! Make sure writer is running first.")
    exit(1)

# Read data (blocks until available)
result = fifo.read_event()
if result:
    event_number, data = result
    print(f"Event {event_number}: {data}")

# Cleanup
fifo.close()  # Reader should NOT call unlink()
```

### Reading with Timeout

```python
fifo = ShmFIFO("my_fifo", create=False)

# Block for up to 5 seconds
result = fifo.read_event(timeout=5.0)
if result:
    event_number, data = result
    print(f"Received event {event_number}")
else:
    print("No data received within 5 seconds")

# Non-blocking read (returns immediately if no data)
result = fifo.read_event(timeout=0)
if result is None:
    print("No data available")
```

### Continuous Reading Loop

```python
from ejfat_shm import ShmFIFO

fifo = ShmFIFO("my_fifo", create=False)

try:
    while True:
        result = fifo.read_event(timeout=1.0)

        if result:
            event_number, data = result
            # Process data
            print(f"Processing event {event_number}")
        else:
            # No data for 1 second
            # Could check if writer is still alive, log status, etc.
            pass

except KeyboardInterrupt:
    print("Shutting down...")
finally:
    fifo.close()
```

### Unpacking Binary Data

```python
import struct
from ejfat_shm import ShmFIFO

fifo = ShmFIFO("my_fifo", create=False)

result = fifo.read_event()
if result:
    event_number, data = result

    # Unpack structured data (must match writer format)
    timestamp, sequence_num, sensor_value = struct.unpack('dif', data)

    print(f"Event: {event_number}")
    print(f"Timestamp: {timestamp}")
    print(f"Sequence: {sequence_num}")
    print(f"Value: {sensor_value}")
```

### Context Manager for Reader

```python
from ejfat_shm import ShmFIFO

with ShmFIFO("my_fifo", create=False) as fifo:
    while True:
        result = fifo.read_event(timeout=5.0)
        if result:
            event_number, data = result
            # Process data
        else:
            break  # No more data
# Automatically calls close() (but not unlink())
```

## Complete Example

### Writer Process (writer.py)

```python
#!/usr/bin/env python3
import time
import struct
from ejfat_shm import ShmFIFO, WriteStatus

def main():
    # Create FIFO
    fifo = ShmFIFO("my_data_stream", capacity=100, entry_size=4096, create=True)

    try:
        for i in range(1000):
            # Create payload
            timestamp = time.time()
            data = struct.pack('dI', timestamp, i)  # double + unsigned int

            # Write to FIFO
            result = fifo.write_event(data, event_number=i)

            if result.status == WriteStatus.SUCCESS:
                if i % 100 == 0:
                    print(f"Written {i} events, drops: {result.total_drops}")
            elif result.status == WriteStatus.FIFO_FULL:
                print(f"FIFO full at event {i}, waiting...")
                time.sleep(0.1)  # Back off

            time.sleep(0.01)  # Simulate workload

        # Print final stats
        stats = fifo.get_stats()
        print(f"\nFinal: {stats['total_writes']} writes, {stats['total_drops']} drops")

    finally:
        fifo.close()
        fifo.unlink()
        print("Writer shutdown complete")

if __name__ == "__main__":
    main()
```

### Reader Process (reader.py)

```python
#!/usr/bin/env python3
import struct
from ejfat_shm import ShmFIFO, ShmFIFONotFoundError

def main():
    # Open existing FIFO
    try:
        fifo = ShmFIFO("my_data_stream", create=False)
    except ShmFIFONotFoundError:
        print("FIFO not found! Start writer first.")
        return

    print("Reading events (Ctrl+C to stop)...")

    try:
        events_read = 0
        while True:
            result = fifo.read_event(timeout=2.0)

            if result:
                event_number, data = result
                timestamp, sequence = struct.unpack('dI', data)
                events_read += 1

                if events_read % 100 == 0:
                    print(f"Read {events_read} events")
            else:
                print("No data for 2 seconds...")
                # Could exit here if expecting end of stream

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        stats = fifo.get_stats()
        print(f"\nRead {stats['total_reads']} events")
        print(f"Total drops in system: {stats['total_drops']}")
        fifo.close()

if __name__ == "__main__":
    main()
```

## Best Practices

### 1. Capacity Planning

Choose `capacity` based on expected producer/consumer rate mismatch:

```python
# If writer produces 1000 events/sec and reader consumes 900 events/sec,
# you need buffer for the difference during bursts
burst_duration_seconds = 5
rate_difference = 100  # events/sec
capacity = burst_duration_seconds * rate_difference  # = 500

fifo = ShmFIFO("my_fifo", capacity=capacity, create=True)
```

### 2. Entry Size Optimization

Balance between memory usage and data needs:

```python
# Conservative: pad for future growth
max_expected_data = 1024
entry_size = 16 + (max_expected_data * 2)  # 2x headroom

# Tight: minimize memory footprint
entry_size = 16 + max_expected_data

# Memory usage = capacity * entry_size + 64 bytes header
```

### 3. Error Recovery

```python
from ejfat_shm import ShmFIFO, WriteStatus

fifo = ShmFIFO("my_fifo", create=True)
consecutive_failures = 0

for event in event_stream:
    result = fifo.write_event(event.data, event.number)

    if result.status != WriteStatus.SUCCESS:
        consecutive_failures += 1

        if consecutive_failures > 10:
            # Alert monitoring system
            send_alert("FIFO experiencing sustained backpressure")
            consecutive_failures = 0
    else:
        consecutive_failures = 0
```

### 4. Graceful Shutdown

```python
import signal
import sys

fifo = None

def signal_handler(sig, frame):
    print("\nShutdown signal received...")
    if fifo:
        fifo.close()
        if fifo.create:
            fifo.unlink()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Your main code here
```

### 5. Name Uniqueness

```python
import os

# Use process-specific or application-specific names
pid = os.getpid()
fifo = ShmFIFO(f"myapp_{pid}", create=True)

# Or use unique identifiers
import uuid
unique_id = uuid.uuid4().hex[:8]
fifo = ShmFIFO(f"myapp_{unique_id}", create=True)
```

## Troubleshooting

### Problem: "Shared memory already exists"

**Cause**: Previous writer didn't call `unlink()` or crashed

**Solution**:
```bash
# List shared memory objects
ls /dev/shm/

# Manually remove if needed (macOS)
rm /dev/shm/ejfat_shm_my_fifo

# Or in Python
from ejfat_shm import ShmFIFO
fifo = ShmFIFO("my_fifo", create=False)
fifo.close()
fifo.unlink()  # Careful! This removes it for everyone
```

### Problem: "Shared memory not found"

**Cause**: Writer hasn't started yet or used different name

**Solution**: Ensure writer starts first, or add retry logic:
```python
import time
from ejfat_shm import ShmFIFO, ShmFIFONotFoundError

for attempt in range(10):
    try:
        fifo = ShmFIFO("my_fifo", create=False)
        break
    except ShmFIFONotFoundError:
        print(f"Waiting for writer... (attempt {attempt+1}/10)")
        time.sleep(1)
else:
    print("Writer never started!")
    exit(1)
```

### Problem: High drop rate

**Cause**: Reader too slow or capacity too small

**Solutions**:
1. Increase capacity
2. Optimize reader processing
3. Use multiple readers with partitioning
4. Add backpressure handling in writer

### Problem: Memory usage concerns

**Check**: `capacity × entry_size` should fit in RAM

```python
fifo = ShmFIFO("my_fifo", capacity=10000, entry_size=4096, create=True)
# Memory: 10000 * 4096 = 40 MB
```

## Performance Considerations

- **Zero-copy**: Data is written directly to shared memory, no kernel copying
- **Lock-free**: Writer and reader don't block each other (single-writer/single-reader)
- **Semaphore overhead**: Reader blocks on semaphore, which is efficient kernel wait
- **Memory alignment**: Entries are naturally aligned on x86-64 for atomic operations

## Thread Safety

- **Single-writer, single-reader**: Safe across processes
- **Multiple writers**: Not supported (would need external synchronization)
- **Multiple readers**: Not supported (would corrupt read index)

For multiple readers, use multiple FIFOs or add external coordination.
