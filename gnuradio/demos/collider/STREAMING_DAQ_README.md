# Bluesky Streaming DAQ Integration

This directory contains a complete implementation of Bluesky's **Resource/Datum methodology** for streaming detector data to disk during experimental runs. This is the recommended approach for high-throughput DAQ systems where detector data streams directly to files rather than being stored in Bluesky's event documents.

## Overview

The implementation demonstrates how to:

1. **Stream detector data to disk** in real-time during a Bluesky run
2. **Synchronize DAQ files with Bluesky's document model** using Resource/Datum documents
3. **Maintain timestamps** in streaming data for post-run joining and analysis
4. **Separate data streams** for different detectors (pixel detector and calorimeter)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Bluesky Run Engine                                         │
│  - Emits Start, Event, Stop documents                       │
│  - Calls stage() at run start                               │
│  - Calls unstage() at run end                               │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ Controls
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  StreamingColliderDevice (Ophyd Device)                     │
│  - stage(): Creates DAQ files, emits Resource docs          │
│  - unstage(): Closes files, emits Datum docs                │
│  - Reads control parameters and status                      │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ XML-RPC
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Particle Collider Simulator (particle_collider.py)         │
│  - XML-RPC methods: start_daq_run(), stop_daq_run()        │
│  - Manages StreamingDAQManager                              │
│  - Logs detector hits to files in real-time                 │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ Writes to
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Data Files (CSV format)                                    │
│  - pixel_detector_<run_id>.csv                              │
│  - calorimeter_detector_<run_id>.csv                        │
│  - Timestamped for joining                                  │
└─────────────────────────────────────────────────────────────┘
```

## Document Flow

When a Bluesky run executes with the streaming device:

```
Time ────────────────────────────────────────────────────────▶

1. START DOCUMENT
   ├─ uid: "abc123-def456-..."
   ├─ time: 1234567890.0
   ├─ plan_name: "count"
   └─ metadata: {purpose: "...", operator: "...", ...}

2. BASELINE EVENT
   └─ Baseline readings: speed_min, speed_max, interval_min, interval_max

3. RESOURCE DOCUMENTS (emitted during staging)
   ├─ Pixel Detector Resource
   │  ├─ spec: "CSV"
   │  ├─ root: "/path/to/data"
   │  ├─ resource_path: "pixel_detector_e4f9b894.csv"
   │  └─ uid: "resource-pixel-xyz"
   └─ Calorimeter Resource
      ├─ spec: "CSV"
      ├─ root: "/path/to/data"
      ├─ resource_path: "calorimeter_detector_e4f9b894.csv"
      └─ uid: "resource-calo-xyz"

   [DAQ files are opened and streaming begins]

4. EVENT DOCUMENTS (periodic status readings)
   ├─ Event #1: time_elapsed=0.0, active_particles=0, total_particles=0
   ├─ Event #2: time_elapsed=1.0, active_particles=2, total_particles=2
   ├─ Event #3: time_elapsed=2.0, active_particles=4, total_particles=5
   └─ ... (continues)

   [Meanwhile, detector hits stream to CSV files with timestamps]

5. DATUM DOCUMENTS (emitted during unstaging/collection)
   ├─ Pixel Datum
   │  ├─ datum_id: "datum-pixel-abc"
   │  ├─ resource: "resource-pixel-xyz" ← Links to Resource
   │  └─ datum_kwargs: {}
   └─ Calorimeter Datum
      ├─ datum_id: "datum-calo-abc"
      ├─ resource: "resource-calo-xyz" ← Links to Resource
      └─ datum_kwargs: {}

   [DAQ files are closed]

6. STOP DOCUMENT
   ├─ run_start: "abc123-def456-..."  ← Links to Start
   ├─ time: 1234567900.0
   └─ exit_status: "success"
```

## Key Components

### 1. Streaming DAQ Loggers (`streaming_daq_logger.py`)

Provides three classes:

- **`PixelDetectorLogger`**: Writes pixel hits to CSV in real-time
  - Format: `wall_time, simulation_time, particle_id, pixel_number, hit_time`

- **`CalorimeterDetectorLogger`**: Writes calorimeter hits to CSV in real-time
  - Format: `wall_time, simulation_time, particle_id, segment_number, hit_time, particle_speed, deflection_angle`

- **`StreamingDAQManager`**: Coordinates both loggers for a single run
  - Creates unique filenames using run ID
  - Thread-safe file writing
  - Provides statistics and file paths

### 2. Modified Simulator (`particle_collider.py`)

Enhanced with:

- **Streaming DAQ integration**: Logs detector hits when `daq_run_active` is True
- **XML-RPC methods** for run control:
  - `start_daq_run(run_id, data_dir)`: Creates new DAQ files
  - `stop_daq_run()`: Closes files and returns statistics
  - `get_daq_status()`: Returns current DAQ state
  - `get_daq_file_paths()`: Returns paths to current DAQ files

### 3. Streaming Bluesky Device (`bluesky_streaming_collider.py`)

Ophyd Device with Resource/Datum support:

- **`StreamingColliderDevice`**: Main device class
  - Inherits XML-RPC connectivity from base device
  - Implements `stage()` to start DAQ run and emit Resource documents
  - Implements `unstage()` to stop DAQ run
  - Implements `collect_asset_docs()` to emit Datum documents
  - Tracks Resource/Datum UIDs for linking

### 4. Example Experiments (`bluesky_streaming_examples.py`)

Five comprehensive examples:

1. **Simple Streaming Run**: Basic usage with status monitoring
2. **Parameter Scan**: Scan control parameter while streaming data
3. **Databroker Integration**: Store and retrieve runs with metadata
4. **Multi-Run Experiment**: Multiple runs with different parameters
5. **Post-Run Analysis**: How to join and analyze streaming data

## Usage

### Basic Example

```python
from bluesky import RunEngine
from bluesky.plans import count
from bluesky_streaming_collider import create_streaming_collider_device

# Create RunEngine and device
RE = RunEngine({})
collider = create_streaming_collider_device(data_dir='./my_data')

# Run experiment (streaming happens automatically)
RE(count([collider], num=10, delay=1))
```

### What Gets Recorded

**In Bluesky Documents:**
- Control parameters (speed_min, speed_max, interval_min, interval_max)
- Periodic status readings (time_elapsed, active_particles, total_particles)
- Run metadata (operator, purpose, notes, etc.)
- Links to external data files via Resource/Datum documents

**In DAQ Files:**
- **Pixel detector hits**: Every pixel hit with precise timestamps
- **Calorimeter hits**: Every calorimeter hit with energy and angle
- Both files include `wall_time` and `simulation_time` for joining

### Post-Run Analysis

```python
import pandas as pd
from databroker import Broker

# Load run from databroker
db = Broker.named('temp')
run = db[uid]

# Get metadata
metadata = run.start
speed_min = run.baseline.read()['speed_min']['value']

# Load streaming data files
pixel_data = pd.read_csv(f'./my_data/pixel_detector_{run_id}.csv')
calo_data = pd.read_csv(f'./my_data/calorimeter_detector_{run_id}.csv')

# Join data on particle_id
combined = pd.merge(pixel_data, calo_data,
                   on='particle_id',
                   suffixes=('_pixel', '_calo'))

# Analyze correlated measurements
correlation = combined[['pixel_number', 'segment_number']].corr()
```

## File Formats

### Pixel Detector CSV

```csv
wall_time,simulation_time,particle_id,pixel_number,hit_time
1761867163.023459,28.050000000000264,34,5242,28.050000000000264
1761867163.8166049,28.40000000000027,35,5248,28.40000000000027
...
```

### Calorimeter Detector CSV

```csv
wall_time,simulation_time,particle_id,segment_number,hit_time,particle_speed,deflection_angle
1761867163.8166049,28.40000000000027,34,52,28.40000000000027,0.7124719,87.4
1761867164.5233,28.75000000000028,35,53,28.75000000000028,0.6892341,92.1
...
```

## Testing

Run the integration test to verify everything works:

```bash
# Terminal 1: Start the simulator
python particle_collider.py

# Terminal 2: Run integration test
python test_streaming_integration.py
```

Expected output:
```
============================================================
Test Complete!
============================================================

Summary:
  ✓ Streaming DAQ loggers work
  ✓ XML-RPC start/stop DAQ run methods work
  ✓ Bluesky Device staging/unstaging works
  ✓ Resource/Datum documents are emitted correctly
  ✓ Data files are created and populated
```

## Comparison with Basic Integration

### Basic Integration (`bluesky_collider.py`)

- Records only control parameters and status in Bluesky
- Detector data saved separately by simulator (on exit)
- No Resource/Datum documents
- Files not linked to specific runs

### Streaming Integration (`bluesky_streaming_collider.py`)

- ✓ Creates separate DAQ files for each run
- ✓ Files linked to runs via Resource/Datum documents
- ✓ Data timestamped for joining in analysis
- ✓ Run-synchronized file creation/closure
- ✓ Suitable for high-throughput DAQ systems

## Best Practices

1. **Always use unique run IDs**: The device generates UUIDs automatically
2. **Specify a data directory**: Keep DAQ files organized
3. **Include metadata**: Use `md={}` parameter in plans for documentation
4. **Join data using timestamps**: Both wall_time and simulation_time are provided
5. **Archive DAQ files**: Resource/Datum documents preserve file locations

## Advanced Features

### Custom Metadata

```python
md = {
    'purpose': 'Speed sensitivity study',
    'operator': 'John Doe',
    'proposal_id': 'PROP-2025-001',
    'sample': 'High-energy particle collisions',
    'notes': 'Testing detector response at different speeds'
}

RE(count([collider], num=10, delay=1, md=md))
```

### Parameter Scans

```python
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp

@bpp.run_decorator(md={'scan_type': 'speed_study'})
def speed_scan():
    """Scan speed parameter while streaming data"""
    for speed in [0.4, 0.6, 0.8, 1.0]:
        yield from bps.mov(collider.speed_min, speed)
        yield from bps.sleep(5.0)  # Collect data
        yield from bps.trigger_and_read([collider])

RE(speed_scan())
```

### Multi-Detector Correlation

```python
# Load both detector streams
pixel = pd.read_csv('pixel_detector_xyz.csv')
calo = pd.read_csv('calorimeter_detector_xyz.csv')

# Merge on particle_id
data = pd.merge(pixel, calo, on='particle_id')

# Calculate time-of-flight
data['tof'] = data['hit_time_calo'] - data['hit_time_pixel']

# Correlate position with segment
import matplotlib.pyplot as plt
plt.scatter(data['pixel_number'], data['segment_number'],
           c=data['particle_speed'], cmap='viridis')
plt.colorbar(label='Particle Speed')
plt.xlabel('Pixel Number')
plt.ylabel('Calorimeter Segment')
plt.title('Detector Correlation Map')
```

## Troubleshooting

### "No DAQ run is active"

Make sure the device is staged before the run:
```python
# Staging happens automatically in Bluesky plans
RE(count([collider], num=5))  # Correct

# Manual staging (for testing)
collider.stage()
# ... do something ...
collider.unstage()
```

### Files not created

Check that:
1. Simulator is running (`python particle_collider.py`)
2. XML-RPC server is accessible (port 8000)
3. Data directory exists and is writable

### Empty data files

If files exist but have no data:
1. Increase collection time (more `delay` or `num` in count plan)
2. Check simulator is not paused
3. Verify particles are being created (check simulator GUI)

## Related Files

- `streaming_daq_logger.py`: Core DAQ logging classes
- `particle_collider.py`: Simulator with streaming integration
- `bluesky_streaming_collider.py`: Ophyd device with Resource/Datum support
- `bluesky_streaming_examples.py`: Example experiments
- `test_streaming_integration.py`: Integration test
- `BLUESKY_README.md`: Basic Bluesky integration (without streaming)

## References

- [Bluesky Event Model](https://blueskyproject.io/event-model/)
- [Resource and Datum Documents](https://blueskyproject.io/event-model/external.html)
- [Ophyd Signals and Devices](https://blueskyproject.io/ophyd/)
