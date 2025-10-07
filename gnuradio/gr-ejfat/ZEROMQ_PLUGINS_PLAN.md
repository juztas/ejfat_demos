# Implementation Plan for ejfat_src_zmq and ejfat_sink_zmq

## Overview
The current plugins use file I/O to read/write complex64 samples. The ZeroMQ versions will replace file operations with ZeroMQ publish/subscribe messaging patterns.

## Architecture Analysis
**Current Structure:**
- `ejfat_source.py`: Reads complex64 samples from binary file with optional repeat
- `ejfat_sink.py`: Writes complex64 samples to binary file
- Both use GNU Radio's `sync_block` base class
- Both implement `start()`, `stop()`, and `work()` methods

## Plugin 1: ejfat_sink_zmq

**Purpose:** Publish complex64 samples to a ZeroMQ socket

**Key Design Decisions:**
1. **ZeroMQ Pattern:** PUB socket (one-to-many broadcast)
2. **Serialization:** Convert numpy complex64 arrays to bytes using `tobytes()`
3. **Parameters:**
   - `endpoint`: ZeroMQ endpoint (e.g., "tcp://*:5555" for server, "tcp://localhost:5555" for client)
   - `bind`: Boolean - True to bind (server), False to connect (client)
   - `hwm`: High water mark for buffering (default: 1000)

**Implementation Steps:**
1. Create `python/ejfat/ejfat_sink_zmq.py`
   - Import zmq library
   - Initialize ZMQ context and PUB socket in `__init__`
   - Bind or connect socket in `start()`
   - Serialize and publish data in `work()`
   - Clean up socket/context in `stop()`

2. Create GRC block definition `grc/ejfat_ejfat_sink_zmq.block.yml`
   - Parameters: endpoint (string), bind (bool), hwm (int)
   - Input: complex stream

3. Create unit test `python/ejfat/qa_ejfat_sink_zmq.py`
   - Test socket creation and binding
   - Test data transmission (using SUB socket to verify)

## Plugin 2: ejfat_src_zmq

**Purpose:** Receive complex64 samples from a ZeroMQ socket

**Key Design Decisions:**
1. **ZeroMQ Pattern:** SUB socket (subscribe to PUB)
2. **Deserialization:** Convert received bytes back to numpy complex64 arrays
3. **Buffering:** Use internal buffer to handle ZMQ message boundaries vs GNU Radio's requested samples
4. **Parameters:**
   - `endpoint`: ZeroMQ endpoint (e.g., "tcp://localhost:5555")
   - `bind`: Boolean - True to bind (unusual for SUB), False to connect (typical)
   - `hwm`: High water mark for buffering (default: 1000)
   - `timeout`: Socket receive timeout in ms (default: 100)

**Implementation Steps:**
1. Create `python/ejfat/ejfat_src_zmq.py`
   - Import zmq library
   - Initialize ZMQ context and SUB socket in `__init__`
   - Subscribe to all messages (empty filter)
   - Connect socket in `start()`, use non-blocking recv with timeout
   - Maintain internal buffer for partial message handling
   - Deserialize received data and fill output buffer in `work()`
   - Clean up socket/context in `stop()`

2. Create GRC block definition `grc/ejfat_ejfat_src_zmq.block.yml`
   - Parameters: endpoint (string), bind (bool), hwm (int), timeout (int)
   - Output: complex stream

3. Create unit test `python/ejfat/qa_ejfat_src_zmq.py`
   - Test socket creation and connection
   - Test data reception (using PUB socket to send test data)

## Build System Integration

**Files to Modify:**

1. **python/ejfat/CMakeLists.txt**
   - Add `ejfat_sink_zmq.py` and `ejfat_src_zmq.py` to `gr_python_install()`
   - Add `qa_ejfat_sink_zmq.py` and `qa_ejfat_src_zmq.py` test targets

2. **python/ejfat/__init__.py**
   - Import new classes: `from .ejfat_sink_zmq import ejfat_sink_zmq`
   - Import: `from .ejfat_src_zmq import ejfat_src_zmq`

3. **grc/CMakeLists.txt**
   - Add block YAML files to install list

4. **CMakeLists.txt (root)** - Check for ZeroMQ dependency
   - Add `find_package(cppzmq)` or equivalent Python dependency check

## Dependencies
- **pyzmq**: Python ZeroMQ bindings (add to requirements/documentation)

## Testing Strategy
1. Unit tests for individual blocks
2. Integration test with both blocks connected (loopback test)
3. Verify compatibility with different ZeroMQ transport types (tcp, ipc, inproc)

## Implementation Order
1. ejfat_sink_zmq (simpler - just publish)
2. ejfat_src_zmq (more complex - buffering logic)
3. GRC block definitions
4. Unit tests
5. CMakeLists.txt updates
6. Integration testing

## Potential Issues & Solutions
- **Message boundaries:** ZMQ sends complete messages; GNU Radio requests arbitrary sample counts
  - Solution: Buffer incomplete messages in source block
- **Blocking behavior:** ZMQ recv can block
  - Solution: Use timeout and return zeros if no data available
- **Startup synchronization:** SUB might miss early messages
  - Solution: Document "slow joiner" problem, consider using REQ/REP for handshake if needed
