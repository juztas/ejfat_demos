# Bluesky Quick Start Guide

## Files

- **`bluesky_collider.py`** - Ophyd device implementation for particle collider
- **`bluesky_examples.py`** - 8 example plans demonstrating Bluesky usage
- **`bluesky_requirements.txt`** - Python dependencies for Bluesky integration
- **`test_bluesky_connection.py`** - Test XML-RPC connection before installing Bluesky
- **`BLUESKY_README.md`** - Complete documentation (read this for details)

## Installation

```bash
# Test connection first (no dependencies needed)
python test_bluesky_connection.py

# If test passes, install Bluesky
pip install -r bluesky_requirements.txt
```

## Quick Start (3 Steps)

### Step 1: Start Simulation

```bash
python particle_collider.py
```

### Step 2: Verify Connection

```bash
python test_bluesky_connection.py
```

### Step 3: Run Bluesky Examples

```bash
python bluesky_examples.py
```

## Minimal Usage Example

```python
from bluesky import RunEngine
from bluesky.plans import count
from bluesky.callbacks import LiveTable
from bluesky_collider import create_collider_device

# Setup
RE = RunEngine({})
collider = create_collider_device()

# Create live table
table = LiveTable([
    collider.time_elapsed,
    collider.active_particles,
    collider.total_particles
])

# Collect 10 data points, 1 second apart
RE(count([collider], num=10, delay=1), table)
```

## What Gets Recorded

### In Bluesky (via ophyd signals)
- **Control**: speed_min, speed_max, interval_min, interval_max
- **Measurements**: time_elapsed, active_particles, total_particles

### NOT in Bluesky (saved separately by simulation)
- Calorimeter hits → `collider_data_*.csv`
- Pixel detector hits → `collider_data_*.csv`
- Per-particle data → `collider_data_*.csv`
- Summary statistics → `collider_data_*.json`

## Available Examples

Run `python bluesky_examples.py` and choose:

1. **Simple Count** - Monitor particle production
2. **Speed Scan** - Vary speed_min parameter
3. **Interval Scan** - Vary interval_min parameter
4. **2D Grid Scan** - Speed vs interval mapping
5. **Custom Plan** - Pause, configure, resume workflow
6. **Timed Acquisition** - 30-second monitoring with plots
7. **Databroker** - Persistent storage and retrieval
8. **Comprehensive Study** - Best practices with metadata

## Common Commands

```python
# Read current values
collider.speed_min.get()
collider.time_elapsed.get()

# Set parameters
collider.speed_min.put(0.7)
collider.interval_max.put(1.5)

# Control simulation
collider.pause()
collider.resume()
collider.reset()

# Get detailed statistics (includes detector data, not in Bluesky stream)
stats = collider.get_statistics()
```

## Parameter Scans

```python
from bluesky.plans import scan

# 1D scan
RE(scan([collider], collider.speed_min, 0.3, 0.9, 7))

# 2D grid scan
from bluesky.plans import grid_scan
RE(grid_scan(
    [collider],
    collider.speed_min, 0.3, 0.9, 4,
    collider.interval_min, 0.3, 1.2, 4
))
```

## Data Export

```python
from databroker import Broker

# Setup database
db = Broker.named('temp')
RE.subscribe(db.insert)

# Run experiment
uid = RE(scan([collider], collider.speed_min, 0.3, 0.9, 5))

# Retrieve data
header = db[uid]
table = header.table()

# Export to pandas DataFrame
df = table[['collider_speed_min', 'collider_total_particles']]
df.to_csv('bluesky_results.csv')
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'ophyd'"
```bash
pip install -r bluesky_requirements.txt
```

### "ConnectionRefusedError"
```bash
# Make sure particle_collider.py is running
python particle_collider.py
```

### Test connection without Bluesky
```bash
python test_bluesky_connection.py
```

## Next Steps

- Read `BLUESKY_README.md` for complete documentation
- Run examples: `python bluesky_examples.py`
- Create custom plans for your experiments
- Combine Bluesky data with simulation CSV files for complete analysis

## Key Concepts

**Ophyd Device** - Hardware abstraction layer (ParticleColliderDevice)
**Signals** - Individual control/readback points (speed_min, time_elapsed, etc.)
**Plans** - Experiment procedures (count, scan, custom plans)
**RunEngine** - Executes plans and manages data collection
**Callbacks** - Live visualization and data export (LiveTable, LivePlot)
**Databroker** - Persistent storage for experimental data

## Documentation

- Full docs: `BLUESKY_README.md`
- XML-RPC API: `XMLRPC_README.md`
- Simulation docs: `README.md`
- Bluesky project: https://blueskyproject.io/
