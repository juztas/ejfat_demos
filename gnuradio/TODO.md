# TODO List

## ejfat_shm/daemon

### 1. Complete EJFAT SHM Sender Daemon

**Status**: ✅ Source code complete, ⚠️ Not yet built

The `ejfat_shm_daemon` sender is fully implemented but needs to be compiled and tested.

**Location**: `ejfat_shm/daemon/`

**What's Done**:
- C/C++ source code complete (`src/shm_reader.c`, `src/config.c`, `src/ejfat_shm_daemon.cpp`)
- Header files complete (`include/shm_reader.h`, `include/config.h`)
- Makefile with E2SAR integration
- Configuration examples and test scripts
- Full documentation (README_DAEMON.md, QUICKSTART.md)

**What's Needed**:
1. Build E2SAR library (prerequisite)
2. Compile daemon: `cd ejfat_shm/daemon && make`
3. Test with `test_writer.py` and `test_config.conf`
4. Validate EJFAT network transmission
5. Performance testing and tuning

---

### 2. Create EJFAT SHM Receiver Daemon

**Status**: ❌ Not yet implemented

**Location**: `ejfat_shm/daemon/` (add receiver implementation to existing daemon directory)

**Purpose**: Create a complementary daemon that **receives E2SAR events from the network** and writes them into a shared memory FIFO for local consumption.

**Architecture**:
```
Network (E2SAR/UDP) → ejfat_shm_receiver → SHM FIFO → Consumer Process
```

**What Needs to Be Built**:
- Receiver daemon using E2SAR Reassembler class
- SHM writer implementation (complement to existing shm_reader.c)
- Configuration and documentation
- Test scripts for end-to-end validation

**Implementation Notes**: See `ejfat_shm/daemon/` for sender implementation as reference. Receiver will use E2SAR Reassembler instead of Segmenter, and write to SHM FIFO instead of reading from it.

---

## Future Enhancements

### ejfat_shm Package
- Multiple readers support
- Dynamic resizing
- Data persistence/recovery
- Additional statistics (latency histograms, throughput)
- Optional writer blocking mode
- Memory barriers for non-x86 architectures

### gr-ejfat Module
- Additional GNU Radio blocks as needed
- Integration with more SDR hardware
- Performance optimizations
