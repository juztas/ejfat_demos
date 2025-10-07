# EJFAT Shared Memory FIFO - Quick Reference

## Installation
```bash
pip install -e .
```

## Writer (Producer)

### Basic Pattern
```python
from ejfat_shm import ShmFIFO, WriteStatus

# Create FIFO (writer must use create=True)
fifo = ShmFIFO("my_fifo", capacity=100, entry_size=4096, create=True)

# Write data
result = fifo.write_event(data=b"binary_data", event_number=123)

# Check status
if result.status == WriteStatus.SUCCESS:
    print(f"Success! Drops: {result.total_drops}")
elif result.status == WriteStatus.FIFO_FULL:
    print("FIFO full - handle backpressure")
elif result.status == WriteStatus.DATA_TOO_LARGE:
    print("Data exceeds entry_size")

# Cleanup
fifo.close()
fifo.unlink()  # Writer must unlink
```

### Context Manager (Recommended)
```python
with ShmFIFO("my_fifo", capacity=100, entry_size=4096, create=True) as fifo:
    result = fifo.write_event(b"data", event_number=1)
# Auto cleanup
```

### Binary Data Example
```python
import struct
from ejfat_shm import ShmFIFO, WriteStatus

fifo = ShmFIFO("my_fifo", capacity=100, entry_size=4096, create=True)
data = struct.pack('dif', 123.456, 42, 3.14)  # double, int, float
result = fifo.write_event(data, event_number=1)
fifo.close()
fifo.unlink()
```

## Reader (Consumer)

### Basic Pattern
```python
from ejfat_shm import ShmFIFO

# Open existing FIFO (reader must use create=False)
fifo = ShmFIFO("my_fifo", create=False)

# Read data (blocks until available)
result = fifo.read_event()
if result:
    event_number, data = result
    print(f"Event {event_number}: {data}")

# Cleanup
fifo.close()  # Reader does NOT unlink
```

### With Timeout
```python
fifo = ShmFIFO("my_fifo", create=False)

# Block for max 5 seconds
result = fifo.read_event(timeout=5.0)

# Non-blocking (returns immediately)
result = fifo.read_event(timeout=0)

if result:
    event_number, data = result
else:
    print("No data available")
```

### Continuous Reading
```python
with ShmFIFO("my_fifo", create=False) as fifo:
    while True:
        result = fifo.read_event(timeout=1.0)
        if result:
            event_number, data = result
            # Process data
        else:
            # No data timeout
            pass
```

### Binary Data Example
```python
import struct
from ejfat_shm import ShmFIFO

fifo = ShmFIFO("my_fifo", create=False)
result = fifo.read_event()
if result:
    event_number, data = result
    timestamp, seq, value = struct.unpack('dif', data)
fifo.close()
```

## Key Parameters

- **name**: Unique identifier (string)
- **capacity**: Number of entries in circular buffer (default: 1024)
- **entry_size**: Max bytes per entry including 16-byte metadata (default: 4096)
- **create**: `True` for writer (creates), `False` for reader (opens existing)

## Entry Size Calculation

```python
METADATA_SIZE = 16  # event_number (8) + data_size (8)
max_data_size = 4080
entry_size = METADATA_SIZE + max_data_size  # = 4096
```

## Statistics

```python
stats = fifo.get_stats()
# Returns: {
#   'write_index': int,
#   'read_index': int,
#   'entries_available': int,
#   'capacity': int,
#   'entry_size': int,
#   'total_writes': int,
#   'total_reads': int,
#   'total_drops': int
# }
```

## Error Handling

```python
from ejfat_shm import ShmFIFO, ShmFIFOExistsError, ShmFIFONotFoundError

# Writer
try:
    fifo = ShmFIFO("my_fifo", create=True)
except ShmFIFOExistsError:
    # FIFO already exists - unlink old one or use create=False

# Reader
try:
    fifo = ShmFIFO("my_fifo", create=False)
except ShmFIFONotFoundError:
    # Writer hasn't created FIFO yet
```

## Common Patterns

### Writer with Error Recovery
```python
from ejfat_shm import ShmFIFO, WriteStatus

with ShmFIFO("data", capacity=100, entry_size=4096, create=True) as fifo:
    for i, event in enumerate(event_stream):
        result = fifo.write_event(event, event_number=i)

        if result.status == WriteStatus.FIFO_FULL:
            time.sleep(0.1)  # Backoff
```

### Reader with Timeout Loop
```python
from ejfat_shm import ShmFIFO

with ShmFIFO("data", create=False) as fifo:
    try:
        while True:
            result = fifo.read_event(timeout=5.0)
            if result:
                process(result)
            else:
                break  # Timeout - no more data
    except KeyboardInterrupt:
        print("Stopped")
```

## Important Notes

1. **Writer creates, reader opens**: Writer uses `create=True`, reader uses `create=False`
2. **Writer unlinks**: Only writer should call `unlink()` for cleanup
3. **Start order**: Writer must start before reader
4. **Single-writer/single-reader**: Not thread-safe for multiple writers/readers
5. **Data size**: Must be ≤ (entry_size - 16) bytes
6. **Capacity planning**: Choose capacity to handle producer/consumer rate differences
7. **Memory usage**: `capacity × entry_size + 64` bytes

## Quick Troubleshooting

- **"Already exists"**: Previous writer didn't unlink - manually remove or use create=False
- **"Not found"**: Start writer first
- **High drops**: Increase capacity or optimize reader speed
- **Data too large**: Increase entry_size or reduce data payload

## Complete Minimal Example

**writer.py**:
```python
from ejfat_shm import ShmFIFO
with ShmFIFO("test", capacity=10, entry_size=1024, create=True) as f:
    for i in range(100):
        f.write_event(f"msg_{i}".encode(), i)
```

**reader.py**:
```python
from ejfat_shm import ShmFIFO
with ShmFIFO("test", create=False) as f:
    while True:
        result = f.read_event(timeout=1.0)
        if result:
            print(result)
        else:
            break
```
