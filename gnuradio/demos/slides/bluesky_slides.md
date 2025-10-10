---
marp: true
theme: default
paginate: true
---

# Bluesky Integration with High-Rate Data Streams

Integrating Bluesky control plane with specialized low-latency data planes

---

## Big Idea

Keep control & metadata in **Bluesky** (RunEngine, Start/Descriptor/Event/Stop) and move the raw sample stream to a **specialized, low-latency data plane** (FPGA / RDMA / Kafka / custom C++/CUDA consumers).

**Key principle:** Bluesky emits references to batches, not each sample.

---

## Architecture Overview

Two parallel planes:
- **Data plane** (high-rate): handles raw sample streams
- **Control & provenance plane** (Bluesky): coordinates experiments & metadata

---

## Data Plane Components

### High-Rate Processing
- **Detector/FPGA**: digitizes signals, deterministic pre-processing (decimation, packetization)
- **Low-latency transport**: RDMA, DPDK-based UDP, or high-throughput Kafka cluster
- **Fast storage/buffer**: circular GPU/host memory, NVMe, or object store (S3/Zarr/HDF5)
- **Realtime DSP nodes**: C/C++/CUDA consumers for FFTs/filters, writing processed results

---

## Control & Provenance Plane

### Bluesky Integration
- **Bluesky RunEngine**: issues triggers, coordinates scans and metadata
- **AreaDetector/EPICS**: integrates detector control, publishes image references
- **Broker/Databroker**: stores RunEngine documents + pointers to batch files/metrics
- **Message bridge**: publishes minimal documents to Kafka/ZMQ or Databroker

---

## Observability & Operations

- **Metrics**: Prometheus monitoring
- **Logs**: structured logging for debugging
- **Health checks**: system status monitoring
- **Emergency slow-path**: throttled recording to local disk as fallback

---

## Key Pattern #1: Batching

**Never emit individual low-level samples as Bluesky events**

Choose batch size so Bluesky events are ≲ 1–1000 Hz

### Example: 1,000,000 samples/s

| Batch Size | Event Rate | Suitability |
|------------|------------|-------------|
| 1,000 | 1,000 events/s | Aggressive |
| 10,000 | 100 events/s | Safer |

**Tradeoff:** Larger batches → less control granularity but far higher throughput

---

## Key Pattern #2: Pointers Not Payloads

Event documents should contain:
- File/object URIs or memory buffer IDs
- Minimal summary stats (timestamps, checksums, ROI metrics)

Use `filled: {"det": False}` until a consumer fills the data

---

## Key Pattern #3: Split Responsibilities

- **FPGA/C-device**: keeps real-time loop
- **Bluesky**: handles experiment lifecycle, knobs, and provenance

Clear separation of concerns for reliability and performance

---

## Key Pattern #4: Zero-Copy Where Possible

- Use RDMA/shared memory
- Pass buffer IDs rather than copying arrays
- Minimize data movement overhead

---

## Key Pattern #5: Deterministic Timestamps

All samples must include precise timestamps

**Clock synchronization:**
- PTP (Precision Time Protocol)
- GPS
- NTP + offset correction

Critical for multi-detector correlation and data reconstruction

---

## Key Pattern #6: Backpressure & Throttling

Design throttling/overload strategy rather than letting system fail:

**Options:**
- Drop samples
- Downsample
- Route to archival storage

Graceful degradation under load

---

## Key Pattern #7: Validation & Checksums

Add quick-check validation in data plane:
- Min/max values
- RMS (root mean square)
- Data integrity checksums

Store validation results in Event documents

---

## Summary

### Architecture Benefits
✓ High-rate data processing isolated from control plane
✓ Bluesky maintains experiment provenance & metadata
✓ Scalable through batching and zero-copy techniques
✓ Robust with backpressure handling and validation

### Core Principle
**Separate concerns:** Real-time data acquisition vs. experiment control & metadata
