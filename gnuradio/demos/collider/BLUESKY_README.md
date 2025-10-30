# Bluesky Integration for Particle Collider

This directory contains a Bluesky control framework integration for the particle collider simulation, enabling automated data acquisition and parameter scans.

## Overview

The Bluesky integration provides:
- **Ophyd device abstraction** for the XML-RPC interface
- **Automatic data logging** of control parameters and measurements
- **Built-in scan plans** for parameter studies
- **Live visualization** during data acquisition
- **Databroker integration** for persistent storage

## What Gets Recorded in Bluesky

### Control Parameters (Configuration Data)
- `speed_min`, `speed_max` - Particle speed range [0.1, 1.5]
- `interval_min`, `interval_max` - Injection interval range [0.1, 2.0 seconds]

### Measurements (Primary Data Stream)
- `time_elapsed` - Simulation time in seconds
- `active_particles` - Number of currently active particles
- `total_particles` - Total number of particles created

### What is NOT Recorded in Bluesky
- **Calorimeter hits** - Recorded separately by the simulation
- **Pixel detector hits** - Recorded separately by the simulation
- Individual particle data - Saved in CSV files by the simulation

The simulation continues to save comprehensive per-particle data (including all detector hits) to timestamped CSV/JSON files. Bluesky records only the high-level control parameters and aggregate measurements.

## Installation

### Prerequisites

Ensure the particle collider simulation is installed and working:

```bash
pip install numpy matplotlib
```

### Install Bluesky

```bash
# Install Bluesky and ophyd
pip install bluesky ophyd

# Optional: For data persistence
pip install databroker

# Optional: For plotting
pip install matplotlib
```

Or use the provided requirements file:

```bash
pip install -r bluesky_requirements.txt
```

## Quick Start

### 1. Start the Particle Collider

In one terminal:

```bash
python particle_collider.py
```

This starts the simulation and XML-RPC server on port 8000.

### 2. Run Bluesky Examples

In another terminal:

```bash
# Interactive menu of examples
python bluesky_examples.py

# Or run specific examples directly
python -c "from bluesky_examples import simple_count_example; simple_count_example()"
```

### 3. Basic Usage in Python

```python
from bluesky import RunEngine
from bluesky.plans import count, scan
from bluesky.callbacks import LiveTable
from bluesky_collider import create_collider_device

# Create RunEngine and device
RE = RunEngine({})
collider = create_collider_device()

# Monitor particle production
live_table = LiveTable([
    collider.time_elapsed,
    collider.active_particles,
    collider.total_particles
])

RE(count([collider], num=10, delay=1), live_table)
```

## Architecture

```
┌─────────────────────────────────────────┐
│  Bluesky RunEngine                       │
│  - Plan execution                        │
│  - Data collection                       │
│  - Callback management                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  ParticleColliderDevice (ophyd)          │
│  - speed_min, speed_max (signals)        │
│  - interval_min, interval_max (signals)  │
│  - time_elapsed (readback)               │
│  - active_particles (readback)           │
│  - total_particles (readback)            │
└──────────────┬──────────────────────────┘
               │
               │ XML-RPC
               ▼
┌─────────────────────────────────────────┐
│  Particle Collider Simulation            │
│  (localhost:8000)                        │
│  - Physics simulation                    │
│  - Detector data (saved separately)      │
│  - CSV/JSON export                       │
└─────────────────────────────────────────┘
```

## Available Examples

### Example 1: Simple Count
Monitor particle production over time:

```python
from bluesky_examples import simple_count_example
simple_count_example()
```

Takes 10 readings at 1-second intervals.

### Example 2: Speed Scan
Vary `speed_min` and observe particle production:

```python
from bluesky_examples import speed_scan_example
speed_scan_example()
```

Scans speed from 0.3 to 0.9 in 7 steps.

### Example 3: Interval Scan
Vary injection timing:

```python
from bluesky_examples import interval_scan_example
interval_scan_example()
```

Scans `interval_min` from 0.2 to 1.5.

### Example 4: 2D Grid Scan
Parameter space mapping:

```python
from bluesky_examples import grid_scan_example
grid_scan_example()
```

Creates a 2D map of speed vs interval.

### Example 5: Custom Plan with Pause
Pause/configure/resume workflow:

```python
from bluesky_examples import custom_plan_with_pause
custom_plan_with_pause()
```

Demonstrates pausing simulation, changing parameters, and resuming.

### Example 6: Timed Acquisition
Long-duration monitoring:

```python
from bluesky_examples import timed_acquisition_example
timed_acquisition_example()
```

Runs for 30 seconds with live plotting.

### Example 7: Databroker Integration
Persistent data storage:

```python
from bluesky_examples import databroker_example
databroker_example()
```

Saves data to Databroker for later retrieval and analysis.

### Example 8: Comprehensive Parameter Study
Best practices with metadata:

```python
from bluesky_examples import comprehensive_parameter_study
comprehensive_parameter_study()
```

Demonstrates proper experiment documentation.

## Device API

### ParticleColliderDevice

```python
from bluesky_collider import create_collider_device

# Create device
collider = create_collider_device(
    name='collider',
    rpc_url='http://localhost:8000/'
)

# Read values
speed_min = collider.speed_min.get()
time_elapsed = collider.time_elapsed.get()

# Set values
collider.speed_min.put(0.7)
collider.interval_max.put(1.5)

# Control simulation
collider.pause()
collider.resume()
collider.reset()

# Get statistics (includes detector data, but not recorded in Bluesky)
stats = collider.get_statistics()
```

### Signal Kinds

- **`config`** - Control parameters (speed_min, speed_max, interval_min, interval_max)
  - Recorded once per run in configuration metadata
  - Logged when changed during scans

- **`hinted`** - Primary measurements (time_elapsed, active_particles, total_particles)
  - Recorded at every data point
  - Automatically plotted by BestEffortCallback
  - Included in primary data stream

## Custom Plans

Create custom plans for specific experimental workflows:

```python
import bluesky.plan_stubs as bps
from bluesky import RunEngine
from bluesky_collider import create_collider_device

RE = RunEngine({})
collider = create_collider_device()

def my_custom_plan():
    """Custom experimental procedure"""
    # Pause simulation
    collider.pause()

    # Configure parameters
    yield from bps.mv(collider.speed_min, 0.6)
    yield from bps.mv(collider.speed_max, 1.2)

    # Resume and collect data
    collider.resume()
    yield from bps.sleep(2)  # Let simulation stabilize

    # Take measurements
    for i in range(5):
        yield from bps.trigger_and_read([collider])
        yield from bps.sleep(1)

# Run the plan
RE(my_custom_plan())
```

## Data Analysis

### Using Databroker

```python
from databroker import Broker

# Create or connect to databroker
db = Broker.named('temp')

# Retrieve last run
header = db[-1]
table = header.table()

# Access data
print(table['collider_total_particles'])
print(table['collider_time_elapsed'])

# Plot data
import matplotlib.pyplot as plt
plt.plot(
    table['collider_speed_min'],
    table['collider_total_particles'],
    'o-'
)
plt.xlabel('Speed Min')
plt.ylabel('Total Particles')
plt.show()
```

### Combining with Simulation Data

Bluesky records high-level measurements. For detailed analysis including detector hits:

```python
import pandas as pd
import glob

# Load Bluesky data
header = db[-1]
bluesky_data = header.table()

# Find corresponding simulation CSV file
# (match by timestamp from metadata)
sim_files = glob.glob('collider_data_*.csv')
sim_data = pd.read_csv(sim_files[-1])

# Now you have:
# - bluesky_data: Time series of control parameters and aggregate measurements
# - sim_data: Per-particle data with detector hits

# Example: Correlate Bluesky parameters with detector statistics
# (Implementation depends on your analysis needs)
```

## Integration with Other Tools

### IPython/Jupyter

```python
# In IPython or Jupyter notebook
from bluesky_collider import create_collider_device
from bluesky import RunEngine
from bluesky.plans import scan

%matplotlib inline

RE = RunEngine({})
collider = create_collider_device()

# Live plotting in notebook
from bluesky.callbacks import LivePlot
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
lp = LivePlot('collider_total_particles', x='collider_speed_min', ax=ax)

RE(scan([collider], collider.speed_min, 0.3, 0.9, 7), lp)
```

### Automated Experiments

```python
# Script for automated overnight runs
from bluesky import RunEngine
from bluesky.plans import scan, grid_scan
from databroker import Broker
from bluesky_collider import create_collider_device

RE = RunEngine({})
db = Broker.named('production')
RE.subscribe(db.insert)

collider = create_collider_device()

# Run multiple parameter studies
for interval_max in [0.5, 1.0, 1.5, 2.0]:
    collider.interval_max.put(interval_max)
    collider.reset()  # Start fresh for each study

    RE(scan(
        [collider],
        collider.speed_min, 0.3, 0.9, 10
    ), purpose=f'Speed scan at interval_max={interval_max}')
```

## Troubleshooting

### Connection Issues

```python
# Verify XML-RPC connection
import xmlrpc.client
proxy = xmlrpc.client.ServerProxy("http://localhost:8000/")
print(proxy.get_status())  # Should return status dict

# If connection fails:
# 1. Make sure particle_collider.py is running
# 2. Check that port 8000 is not blocked
# 3. Verify localhost connectivity
```

### Device Not Reading Values

```python
# Test individual signals
collider = create_collider_device()

# This should work:
print(collider.speed_min.get())

# If it returns stale data, check XML-RPC connection
# If it errors, check signal configuration
```

### Slow Performance

- Reduce `delay` parameter in plans for faster scans
- Increase `delay` if simulation needs time to stabilize
- Consider using `count([collider], num=1)` for single readings

## References

- [Bluesky Documentation](https://blueskyproject.io/)
- [Ophyd Documentation](https://blueskyproject.io/ophyd/)
- [Databroker Documentation](https://blueskyproject.io/databroker/)
- Particle Collider XML-RPC API: `XMLRPC_README.md`
