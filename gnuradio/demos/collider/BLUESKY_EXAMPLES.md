# Bluesky Examples Guide

## Overview

`bluesky_examples.py` provides 8 pre-built Bluesky scan examples demonstrating automated data acquisition and parameter scans for the particle collider simulation.

## Examples Summary

### Example 1: Simple Count
- **Purpose**: Monitor particle production over time
- **Duration**: 10 data points at 1-second intervals
- **Use case**: Basic data collection and system verification

### Example 2: Speed Scan
- **Parameters**: `speed_min` from 0.3 to 0.9 (7 points)
- **Duration**: ~7 seconds (1s delay per point)
- **Use case**: Study effect of particle speed on injection rate

### Example 3: Interval Scan
- **Parameters**: `interval_min` from 0.2 to 1.4 (8 points)
- **Duration**: ~8 seconds
- **Use case**: Study effect of injection timing on particle accumulation

### Example 4: 2D Grid Scan
- **Parameters**: `speed_min` (4 values) × `interval_min` (4 values)
- **Duration**: ~16 seconds (16 grid points)
- **Use case**: Parameter space mapping, find optimal settings

### Example 5: Custom Plan with Pause
- **Features**: Pause simulation, configure parameters, resume, collect data
- **Use case**: Demonstrate simulation control during scans

### Example 6: Timed Acquisition
- **Duration**: 30 seconds (15 points at 2-second intervals)
- **Features**: Live plotting of particle counts vs. time
- **Use case**: Long-duration stability measurements

### Example 7: Databroker Integration
- **Features**: Store scan data in databroker, retrieve and analyze
- **Duration**: 5 points with 1s delays
- **Use case**: Persistent data storage and post-analysis

### Example 8: Comprehensive Study
- **Features**: Full parameter sweep with experiment metadata
- **Parameters**: `speed_min` from 0.2 to 0.9 (9 points)
- **Duration**: ~9 seconds
- **Use case**: Best practices for documented experiments

## Key Implementation Details

### Scan Rate Control
All scans use **1 second delays** between parameter changes:
```python
yield from bps.sleep(1.0)  # Delay to see slider move
```

### Sequential Parameter Setting
Grid scans set parameters sequentially to avoid Ophyd state conflicts:
```python
yield from bps.mov(collider.speed_min, speed)
yield from bps.mov(collider.interval_min, interval)
```

### Constraint Validation
All scans ensure `min < max` by:
- Setting max values high enough before scanning
- Limiting scan ranges to stay below max values
- Example: `speed_max=1.2` allows `speed_min` to scan up to 0.9

## Running Examples

```bash
# Interactive menu
python bluesky_examples.py

# Run specific example
echo "2" | python bluesky_examples.py

# Run all examples
echo "all" | python bluesky_examples.py
```

## What's Recorded

**In Bluesky/Databroker:**
- Control parameters: `speed_min`, `speed_max`, `interval_min`, `interval_max`
- Measurements: `time_elapsed`, `active_particles`, `total_particles`

**NOT in Bluesky (saved separately by simulation):**
- Calorimeter hits → CSV/JSON files
- Pixel detector hits → CSV/JSON files
- Per-particle data → CSV files

## Custom Scan Template

```python
from bluesky_collider import create_collider_device
from bluesky import RunEngine
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp

RE = RunEngine({})
collider = create_collider_device()

@bpp.run_decorator()
def my_custom_scan():
    # Set parameters sequentially
    yield from bps.mov(collider.speed_min, 0.5)
    yield from bps.sleep(1.0)
    yield from bps.trigger_and_read([collider])

RE(my_custom_scan())
```
