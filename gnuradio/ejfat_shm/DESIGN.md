# ejfat_shm: Shared Memory FIFO Design

## Overview

A high-performance FIFO queue implementation using POSIX shared memory (`shm_open()`) with semaphore-based notifications for inter-process communication. Designed for single-writer, single-reader scenarios with zero-copy data transfer.

## Architecture

### Memory Layout

```
[Header Section - 64 bytes]
- write_index: 8 bytes      (atomic counter for writer position)
- read_index: 8 bytes       (atomic counter for reader position)
- capacity: 8 bytes         (max number of entries in circular buffer)
- entry_size: 8 bytes       (max size per entry including metadata)
- total_writes: 8 bytes     (successful writes counter)
- total_reads: 8 bytes      (successful reads counter)
- total_drops: 8 bytes      (failed writes counter - atomically incremented)
- padding: 16 bytes         (reserved for future use)

[Entry Array - capacity * entry_size bytes]
- Entry 0: [event_number (8 bytes) | data_size (8 bytes) | data (variable, up to entry_size - 16)]
- Entry 1: [event_number (8 bytes) | data_size (8 bytes) | data (variable)]
- ...
- Entry N-1
```

### Synchronization Objects

**Single Semaphore Design:**
- **Data Semaphore:** `/ejfat_shm_<name>_data`
  - Signals data available for reader
  - Initial value: 0
  - Writer posts after successful write
  - Reader waits before reading

**Shared Memory:** `/ejfat_shm_<name>`
  - Holds the FIFO structure (header + entries)

## Core API

### Initialization

```python
class ShmFIFO:
    def __init__(self, name: str, capacity: int = 1024, entry_size: int = 4096, create: bool = True):
        """
        Initialize shared memory FIFO

        Args:
            name: unique identifier for this FIFO
            capacity: number of entries in circular buffer
            entry_size: max bytes per entry (including 16-byte header)
            create: True for writer (creates shm/sem), False for reader (opens existing)
        """
```

### Writer API

```python
from enum import Enum
from typing import NamedTuple

class WriteStatus(Enum):
    SUCCESS = 0
    FIFO_FULL = 1
    DATA_TOO_LARGE = 2

class WriteResult(NamedTuple):
    status: WriteStatus
    total_drops: int  # Cumulative count of all failed writes

def write_event(self, data: bytes, event_number: int) -> WriteResult:
    """
    Non-blocking write with status feedback

    Args:
        data: packed byte array to queue
        event_number: 64-bit event identifier

    Returns:
        WriteResult with:
        - status: SUCCESS, FIFO_FULL, or DATA_TOO_LARGE
        - total_drops: cumulative count of failed writes

    Steps:
        1. Validate data size <= (entry_size - 16)
           - If too large: return WriteResult(DATA_TOO_LARGE, drops)
        2. Check if FIFO full: (write_index - read_index) >= capacity
           - If full: atomically increment drops, return WriteResult(FIFO_FULL, drops)
        3. Calculate position: write_index % capacity
        4. Write [event_number | len(data) | data] to entry
        5. Atomically increment write_index
        6. data_sem.post() - notify reader
        7. Return WriteResult(SUCCESS, drops)
    """
```

### Reader API

```python
def read_event(self, timeout: float = None) -> tuple[int, bytes] | None:
    """
    Blocks until data available, then reads next entry

    Args:
        timeout: seconds to wait (None = block forever, 0 = non-blocking)

    Returns:
        (event_number, data) tuple or None if timeout/empty

    Steps:
        1. data_sem.wait(timeout) - blocks until data available
           - If timeout expires, return None
        2. Calculate position: read_index % capacity
        3. Read [event_number | data_size | data] from entry
        4. Atomically increment read_index
        5. Return (event_number, data)
    """
```

### Cleanup

```python
def close(self):
    """Unmap memory, close semaphore"""

def unlink(self):
    """Remove shared memory and semaphore (writer only)"""
```

## Implementation Details

### Dependencies

```
posix_ipc>=1.0.0  # For shm_open() and semaphores
```

Built-in modules:
- `mmap` - for memory mapping
- `struct` - for binary packing/unpacking
- `enum` - for status codes
- `typing` - for type hints

### Package Structure

```
ejfat_shm/
├── pyproject.toml
├── setup.py
├── README.md
├── DESIGN.md
├── ejfat_shm/
│   ├── __init__.py
│   ├── fifo.py          # ShmFIFO class implementation
│   ├── exceptions.py    # Custom exceptions
│   └── constants.py     # HEADER_SIZE, etc.
├── examples/
│   ├── writer_example.py
│   ├── reader_example.py
│   └── benchmark.py
└── tests/
    └── test_fifo.py
```

## Concurrency Guarantees

- **Single Writer, Single Reader:** Lock-free using atomic index operations
- **Notification-based:** Reader blocks on semaphore (zero CPU when idle)
- **Non-blocking Writer:** Returns immediately with status if FIFO full
- **Overflow Handling:** Writer fails and increments drop counter when full
- **Graceful Shutdown:** Reader timeout allows clean exit

## Usage Examples

### Writer Process

```python
from ejfat_shm import ShmFIFO, WriteStatus

# Create FIFO
fifo = ShmFIFO("my_fifo", capacity=100, entry_size=4096, create=True)

# Write data
data = b"some packed data"
event_num = 12345

result = fifo.write_event(data, event_num)

if result.status == WriteStatus.SUCCESS:
    print("Data written successfully")
elif result.status == WriteStatus.FIFO_FULL:
    print(f"FIFO full! Total drops: {result.total_drops}")
    # Handle backpressure: log, alert, shed load, etc.
elif result.status == WriteStatus.DATA_TOO_LARGE:
    print(f"Data too large! Total drops: {result.total_drops}")

# Cleanup when done
fifo.close()
fifo.unlink()  # Remove shared memory
```

### Reader Process

```python
from ejfat_shm import ShmFIFO

# Open existing FIFO
fifo = ShmFIFO("my_fifo", create=False)

# Read data (blocks until available)
while True:
    result = fifo.read_event(timeout=5.0)
    if result:
        event_num, data = result
        print(f"Event {event_num}: {len(data)} bytes")
        # Process data
    else:
        print("No data for 5 seconds")
        break

# Cleanup
fifo.close()
```

## Performance Characteristics

- **Zero-copy:** Data transferred via shared memory
- **Low latency:** Direct memory access, no kernel buffering
- **Efficient notification:** Semaphore blocks reader (no polling overhead)
- **Fast writer:** No blocking, immediate return with status
- **Circular buffer:** Constant-time operations for read/write

## Limitations

- Single writer, single reader only
- Fixed capacity and entry size (set at creation)
- POSIX systems only (Linux, macOS, BSD)
- No built-in data persistence (memory-only)
- Writer drops data when FIFO full (no backpressure blocking)

## Future Enhancements

- Multiple readers support
- Dynamic resizing
- Data persistence/recovery
- Additional statistics (latency, throughput)
- Optional writer blocking mode
- Memory barriers for non-x86 architectures
