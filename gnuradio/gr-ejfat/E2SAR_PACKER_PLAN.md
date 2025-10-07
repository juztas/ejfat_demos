# Plan: GNU Radio E2SAR Packer Block

## Overview
Create a GNU Radio block that takes complex sample vectors and packs them into E2SAR-formatted UDP frames with monotonically increasing event IDs generated from a frame counter.

## E2SAR Frame Structure (based on EJFAT documentation)
The E2SAR header follows the UDP payload and contains:
- **Version** (4 bits): Protocol version
- **Reserved** fields for future use
- **Data-ID** (14 bits): Stream identifier
- **Tick/Event-ID** (64 bits): Monotonic event identifier (network byte order)
- **Entropy** (16 bits): Load balancer routing field
- **Buffer Offset** (32 bits): Offset within event
- **Buffer Length** (32 bits): Length of payload data

## Implementation Plan

### 1. Block Structure
- **Block type**: `gr.sync_block` or `gr.basic_block`
- **Input**: Complex float vectors (`np.complex64`)
- **Output**: UDP packets (network transmission) or Message PDUs
- **Name**: `e2sar_packer` or `e2sar_frame_sink`

### 2. Parameters
- **destination_ip**: Target IP address (string)
- **destination_port**: Target UDP port (int)
- **data_id**: 14-bit stream identifier (int, default: 0)
- **mtu**: Maximum transmission unit size (int, default: 1500 bytes)
- **samples_per_frame**: Number of complex samples per E2SAR frame (int)
- **version**: E2SAR protocol version (int, default: 2)
- **entropy**: 16-bit entropy value for load balancing (int, default: 0)

### 3. State Management
- **event_counter**: 64-bit monotonically increasing counter (starts at 0)
- **frame_counter**: Tracks frames within each event
- **udp_socket**: Socket for sending UDP packets

### 4. Core Functionality

#### a. Header Construction
- Create struct/class for E2SAR header with proper fields
- Implement network byte order conversion (big-endian)
- Pack header fields according to E2SAR specification:
  - First 4 bytes: Version, Protocol, Data-ID
  - Entropy field: 16-bit network byte order
  - Tick/Event-ID: 64-bit network byte order (from frame counter)
  - Buffer offset and length fields

#### b. Payload Packing
- Convert complex64 samples to bytes
- Calculate payload size considering MTU limits
- Fragment large vectors if needed across multiple frames

#### c. Frame Assembly
- Concatenate: E2SAR header + complex sample payload
- Update buffer offset and length fields
- Increment event_counter after each complete event

#### d. Network Transmission
- Create UDP socket in `start()` method
- Send frames via UDP to destination
- Handle socket errors gracefully
- Close socket in `stop()` method

### 5. File Structure
```
python/ejfat/
├── e2sar_packer.py          # Main block implementation
├── qa_e2sar_packer.py       # Unit tests
└── __init__.py              # Add import

grc/
└── ejfat_e2sar_packer.block.yml  # GRC block definition

examples/
└── test_e2sar_packer.py     # Example flowgraph
```

### 6. Implementation Steps

#### Step 1: Create E2SAR header structure class
- Define all header fields with proper types
- Implement `pack()` method with network byte ordering
- Add validation for field ranges (e.g., 14-bit Data-ID)

#### Step 2: Implement `e2sar_packer` block class
- Inherit from `gr.sync_block`
- Define `__init__()` with parameters
- Initialize event counter to 0

#### Step 3: Implement `start()` and `stop()` methods
- Create/close UDP socket
- Initialize state variables

#### Step 4: Implement `work()` method
- Read complex samples from input
- Pack samples into E2SAR frames
- Increment event counter
- Send UDP packets
- Return number of samples consumed

#### Step 5: Create GRC block definition YAML
- Define block appearance in GRC
- Specify parameters and their types
- Set input/output signatures

#### Step 6: Write unit tests
- Test header packing correctness
- Test event counter monotonicity
- Test frame fragmentation
- Verify byte ordering

#### Step 7: Create example flowgraph
- Signal source → E2SAR Packer
- Demonstrate parameter configuration
- Show network transmission

### 7. Key Technical Considerations

- **Byte Ordering**: All multi-byte fields must use network byte order (big-endian)
- **Event ID Management**: Event counter must be thread-safe if needed
- **MTU Handling**: Ensure total packet size (UDP header + E2SAR header + payload) fits within MTU
- **Error Handling**: Gracefully handle network errors, malformed inputs
- **Performance**: Minimize copying, use efficient byte packing
- **Compatibility**: Match E2SAR specification exactly for interoperability

### 8. Testing Strategy
- Unit tests for header packing
- Integration test with UDP receiver
- Wireshark packet capture verification
- Load testing with high sample rates
- Verify monotonic event IDs under various conditions

## Dependencies
- `numpy`: Array operations
- `struct`: Binary packing
- `socket`: UDP networking
- `gnuradio`: Core GR framework

## Documentation
- Docstrings for all classes and methods
- README with usage examples
- GRC block documentation
- E2SAR format specification reference

## References
- E2SAR GitHub: https://github.com/JeffersonLab/E2SAR
- EJFAT Project: https://github.com/JeffersonLab/ejfat
- EJFAT Wiki: https://wiki.jlab.org/epsciwiki/index.php/EJFAT

This plan provides a complete implementation path for an E2SAR packer block that integrates with the existing `gr-ejfat` module structure.
