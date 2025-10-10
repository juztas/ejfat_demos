# Bluesky Experiment Framework for EJFAT GNU Radio

A comprehensive Bluesky-based experiment control and data acquisition framework for GNU Radio and EJFAT experiments.

## Overview

This framework provides a production-ready environment for running controlled experiments with:

- **Ophyd devices** for hardware abstraction
- **Custom scan plans** for various experiment types
- **Live callbacks** for real-time feedback
- **Document-based data model** with full metadata capture
- **Persistent data storage** via DataBroker
- **Analysis and visualization tools**
- **Multiple export formats** (CSV, HDF5, Excel, JSON)

## Quick Start

### 1. Installation

Ensure you have the required packages:

```bash
conda activate gnuradio
pip install bluesky ophyd databroker matplotlib pandas scipy openpyxl h5py
```

### 2. Run Your First Experiment

**Without hardware** (using mock devices):

```bash
python run_experiment.py mock_experiment
```

**With GNU Radio** (requires flowgraph with XML-RPC server on port 8080):

```bash
# Terminal 1: Start GNU Radio flowgraph
cd ../widget
python sine_wave_demo.py

# Terminal 2: Run experiment
cd ../full_system
python run_experiment.py frequency_characterization
```

### 3. List Available Experiments

```bash
python run_experiment.py list
```

### 4. View Experiment Details

```bash
python run_experiment.py info mock_experiment
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Bluesky Experiment Layer                      │
│  ┌───────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │  Custom Plans │  │ Callbacks  │  │  Data Analysis   │  │
│  └───────┬───────┘  └─────┬──────┘  └────────┬─────────┘  │
│          └─────────────────┼──────────────────┘             │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │    RunEngine + Document Model (start/descriptor/      │ │
│  │                event/stop documents)                   │ │
│  └────────────────────┬──────────────────────────────────┘ │
│                       ▼                                      │
│  ┌──────────────────────────────────┐  ┌────────────────┐ │
│  │  DataBroker (Persistent Storage) │  │ Live Callbacks │ │
│  └──────────────────────────────────┘  └────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Ophyd Device Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ GNU Radio    │  │   Detectors  │  │  Future: EJFAT   │ │
│  │ (XML-RPC)    │  │   (Mock/Real)│  │  Data Sources    │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
full_system/
├── bluesky_config/          # Core Bluesky configuration
│   ├── devices.py           # Ophyd device definitions
│   ├── plans.py             # Custom scan plans
│   ├── callbacks.py         # Live data processing callbacks
│   └── metadata.py          # Metadata utilities
├── experiments/             # Experiment scripts
│   ├── frequency_characterization.py
│   ├── signal_quality_scan.py
│   └── mock_experiment.py
├── analysis/                # Analysis and visualization
│   ├── plotting.py          # Plotting functions
│   ├── export.py            # Data export utilities
│   └── statistics.py        # Statistical analysis
├── data/                    # Persistent data storage
│   ├── documents/           # Bluesky documents (JSON)
│   └── exports/             # Exported data files
├── notebooks/               # Jupyter notebooks
├── config.py                # Configuration settings
├── setup_environment.py     # Environment setup
├── run_experiment.py        # Main CLI
└── README.md               # This file
```

## Available Devices

### GNU Radio Devices

**GNURadioSignalGenerator** - Control GNU Radio signal generators via XML-RPC

```python
from bluesky_config.devices import GNURadioSignalGenerator

sig_gen = GNURadioSignalGenerator('', name='sig_gen',
                                   host='localhost', port=8080)
```

**FMTransmitter** - Specialized for FM transmitter control

```python
from bluesky_config.devices import FMTransmitter

fm_tx = FMTransmitter('', name='fm_tx', host='localhost', port=8080)
```

### Mock Devices (No Hardware Required)

**MockDetector** - Simulated detector for testing

```python
from bluesky_config.devices import MockDetector

detector = MockDetector(name='det', noise_level=0.15)
```

**PowerMeter** - Simulated RF power meter

```python
from bluesky_config.devices import PowerMeter

power_meter = PowerMeter(name='power_meter')
```

## Available Plans

### Basic Scans

```python
from bluesky_config.plans import frequency_scan, frequency_sweep

# Scan with data collection
RE(frequency_scan([detector], sig_gen, start=1e6, stop=10e6, num_points=100))

# Sweep without data collection (visual observation)
RE(frequency_sweep(sig_gen, start=1e6, stop=10e6, num_points=50, dwell_time=0.5))
```

### Characterization

```python
from bluesky_config.plans import frequency_characterization

# Multiple samples at each frequency
frequencies = [1e6, 2e6, 5e6, 10e6]
RE(frequency_characterization([detector], sig_gen, frequencies, num_samples=10))
```

### Adaptive Scans

```python
from bluesky_config.plans import adaptive_frequency_scan

# Variable step size based on signal derivative
RE(adaptive_frequency_scan([detector], sig_gen,
                            start=1e6, stop=10e6,
                            target_delta=0.05,
                            min_step=1e3, max_step=1e6))
```

### 2D Scans

```python
from bluesky_config.plans import grid_scan_2d

# Grid scan over two parameters
RE(grid_scan_2d([detector],
                 tx_gen, 88e6, 108e6, 20,
                 rx_gen, 88e6, 108e6, 20))
```

## Callbacks

### Built-in Callbacks

```python
from bluesky.callbacks.best_effort import BestEffortCallback

bec = BestEffortCallback()
RE.subscribe(bec)  # Automatic table and plots
```

### Custom Callbacks

**PeakDetectorCallback** - Detect and report peaks

```python
from bluesky_config.callbacks import PeakDetectorCallback

peak_detector = PeakDetectorCallback('detector_value', threshold=1.5)
RE.subscribe(peak_detector)
```

**StatisticsCallback** - Running statistics

```python
from bluesky_config.callbacks import StatisticsCallback

stats = StatisticsCallback(['detector_value', 'frequency'])
RE.subscribe(stats)
```

**DocumentLogger** - Save all documents to JSON

```python
from bluesky_config.callbacks import DocumentLogger

doc_logger = DocumentLogger('data/documents')
RE.subscribe(doc_logger)
```

**ProgressCallback** - Progress bar with ETA

```python
from bluesky_config.callbacks import ProgressCallback

progress = ProgressCallback()
RE.subscribe(progress)
```

## Metadata

### Automatic Metadata Collection

```python
from bluesky_config.metadata import create_experiment_metadata

md = create_experiment_metadata(
    experiment_id='EXP-2025-001',
    purpose='Frequency response characterization',
    plan_type='frequency_scan',
    temperature=22.5,
    humidity=45,
    sdr_type='USRP B210',
    start_freq=88e6,
    stop_freq=108e6,
)

# Use in scan
RE(frequency_scan([det], sig_gen, 88e6, 108e6, 100), **md)
```

### Predefined Metadata Helpers

```python
from bluesky_config.metadata import get_standard_fm_metadata

md = get_standard_fm_metadata(
    station_name='CHEZ 106.1 FM',
    carrier_freq=106.1e6,
)
```

## Data Analysis

### Retrieving Data

```python
from databroker import Broker

db = Broker.named('temp')

# Get recent run
run = db[-1]

# Search by metadata
runs = db.search(plan_name='frequency_scan', operator='alice')

# Get data as DataFrame
table = run.table()
print(table.head())
```

### Plotting

```python
from analysis.plotting import plot_run, plot_multiple_runs

# Plot single run
plot_run(run, 'frequency', 'power', save_path='data/plot.png')

# Compare multiple runs
recent_runs = list(db.search(since='2025-01-08'))
plot_multiple_runs(recent_runs, 'frequency', 'power')
```

### Statistics

```python
from analysis.statistics import analyze_run, find_peaks, compare_runs

# Analyze single run
stats = analyze_run(run, 'power')
print(f"Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}")

# Find peaks
peaks = find_peaks(run, 'frequency', 'power', prominence=5)
print(f"Found {peaks['num_peaks']} peaks at: {peaks['peak_positions']}")

# Compare multiple runs
recent_runs = list(db.search(plan_name='frequency_scan'))[-5:]
comparison = compare_runs(recent_runs, 'power')
print(comparison)
```

### Exporting

```python
from analysis.export import export_to_csv, export_to_hdf5, export_for_analysis

# Single format
export_to_csv(run, 'data/scan_001.csv')
export_to_hdf5(run, 'data/scan_001.h5')

# Multiple formats at once
export_for_analysis(run, 'data/exp_001', formats=['csv', 'hdf5', 'excel'])

# Batch export
batch_export(recent_runs, 'data/batch', formats=['csv', 'hdf5'])
```

## Creating Custom Experiments

Create a new file in `experiments/` directory:

```python
#!/usr/bin/env python3
"""
My Custom Experiment

Description of what this experiment does.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky_config.devices import GNURadioSignalGenerator, MockDetector
from bluesky_config.plans import frequency_scan
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run the experiment."""
    # Setup
    RE = RunEngine({})
    bec = BestEffortCallback()
    RE.subscribe(bec)

    # Create devices
    sig_gen = GNURadioSignalGenerator('', name='sig_gen')
    detector = MockDetector(name='det')

    # Metadata
    md = create_experiment_metadata(
        experiment_id='CUSTOM-001',
        purpose='My custom experiment',
    )

    # Run experiment
    RE(frequency_scan([detector], sig_gen, 1e6, 10e6, 100), **md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Make it executable:

```bash
chmod +x experiments/my_experiment.py
```

Run it:

```bash
python run_experiment.py my_experiment
```

## Configuration

Edit `config.py` to customize:

### DataBroker Settings

```python
# Choose catalog type
DEFAULT_CATALOG = 'temp'  # or 'sqlite', 'mongodb'

# SQLite settings
DATABROKER_SQLITE_CONFIG = {
    'driver': 'sqlite',
    'config': {
        'directory': str(DATA_DIR / 'catalog'),
        'timezone': 'US/Eastern',
    }
}
```

### Device Defaults

```python
GNURADIO_DEFAULT_HOST = 'localhost'
GNURADIO_DEFAULT_PORT = 8080
```

### Callback Settings

```python
ENABLE_BEST_EFFORT_CALLBACK = True
ENABLE_DOCUMENT_LOGGER = True
ENABLE_LIVE_TABLE = False
```

## Bluesky Document Model

Every experiment produces four document types:

### 1. Start Document

```json
{
  "uid": "7ae9b4e3-...",
  "time": 1704741600.123,
  "scan_id": 42,
  "plan_name": "frequency_scan",
  "operator": "username",
  "purpose": "Frequency characterization",
  "plan_args": {"start": 88e6, "stop": 108e6, "num_points": 100}
}
```

### 2. Descriptor Document

```json
{
  "uid": "9bd2c1a4-...",
  "run_start": "7ae9b4e3-...",
  "data_keys": {
    "frequency": {"dtype": "number", "shape": [], "units": "Hz"},
    "power": {"dtype": "number", "shape": [], "units": "dBm"}
  }
}
```

### 3. Event Documents

```json
{
  "uid": "f3a2b8c1-...",
  "descriptor": "9bd2c1a4-...",
  "seq_num": 1,
  "time": 1704741601.123,
  "data": {"frequency": 88e6, "power": -45.3},
  "timestamps": {"frequency": 1704741601.120, "power": 1704741601.122}
}
```

### 4. Stop Document

```json
{
  "uid": "a7c3d2e1-...",
  "run_start": "7ae9b4e3-...",
  "time": 1704741650.789,
  "exit_status": "success",
  "num_events": {"primary": 100}
}
```

## Example Workflows

### Workflow 1: Quick Test

```bash
# Run mock experiment (no hardware needed)
python run_experiment.py mock_experiment

# Analyze in Python
python
>>> from databroker import Broker
>>> db = Broker.named('temp')
>>> run = db[-1]
>>> table = run.table()
>>> print(table.describe())
```

### Workflow 2: GNU Radio Experiment

```bash
# Terminal 1: Start GNU Radio
cd ../widget
python sine_wave_demo.py

# Terminal 2: Run experiment
cd ../full_system
python run_experiment.py frequency_characterization

# Analyze and export
python
>>> from databroker import Broker
>>> from analysis.plotting import plot_run
>>> from analysis.export import export_to_csv
>>>
>>> db = Broker.named('temp')
>>> run = db[-1]
>>>
>>> plot_run(run, 'sig_gen_frequency', 'det_value')
>>> export_to_csv(run, 'data/results.csv')
```

### Workflow 3: Batch Analysis

```python
from databroker import Broker
from analysis.statistics import compare_runs
from analysis.plotting import plot_multiple_runs

db = Broker.named('temp')

# Get all runs from today
runs = list(db.search(since='2025-01-08'))

# Statistical comparison
comparison = compare_runs(runs, 'power')
print(comparison)

# Visual comparison
plot_multiple_runs(runs, 'frequency', 'power',
                   save_path='data/comparison.png')
```

## Troubleshooting

### GNU Radio Connection Issues

```
ConnectionError: Failed to connect to GNU Radio XML-RPC server
```

**Solution:**
- Ensure GNU Radio flowgraph is running
- Check XML-RPC server block is configured in flowgraph
- Verify port number (default: 8080)
- Check firewall settings

### DataBroker Errors

```
ModuleNotFoundError: No module named 'databroker'
```

**Solution:**
```bash
pip install databroker
```

### Import Errors

```
ModuleNotFoundError: No module named 'bluesky_config'
```

**Solution:** Run experiments from the `full_system/` directory or use the CLI:
```bash
cd full_system
python run_experiment.py <experiment_name>
```

## Future Enhancements

Planned features for Phase 2:

1. **High-Speed Sample Recording**
   - Parallel data acquisition paths
   - External file references in documents
   - Synchronized timestamps

2. **EJFAT Integration**
   - E2SAR reassembler as Ophyd device
   - Packet flow monitoring
   - Multi-node coordination

3. **Advanced Analysis**
   - Real-time FFT analysis
   - Machine learning integration
   - Automated anomaly detection

4. **Web Dashboard**
   - Live experiment monitoring
   - Historical data browser
   - Plot gallery

## References

- [Bluesky Documentation](https://blueskyproject.io/)
- [Ophyd Documentation](https://blueskyproject.io/ophyd/)
- [DataBroker Documentation](https://blueskyproject.io/databroker/)
- [Comprehensive Plan](BLUESKY_COMPREHENSIVE_PLAN.md)
- [GNU Radio Integration](../widget/README_BLUESKY.md)

## License

This code is part of the EJFAT demos and follows the same license as the main project.

## Support

For issues or questions:
- EJFAT GitHub: https://github.com/JeffersonLab/E2SAR
- Bluesky Discussions: https://github.com/bluesky/bluesky/discussions

---

## Phase 2: Persistent Data Storage (COMPLETE ✅)

All experiment data is now automatically saved to disk for persistence. See [PHASE2_README.md](PHASE2_README.md) for details.

### Key Features

- **Automatic document saving** to `data/documents/`
- **JSON Lines format** for easy parsing
- **Data retrieval tool**: `retrieve_data.py`
- **Complete metadata preservation**
- **Survives program restarts**

### Quick Start with Persistence

```bash
# Run experiment (data automatically saved)
python run_experiment.py mock_experiment

# View saved data
python retrieve_data.py --latest --all

# List all runs
python retrieve_data.py --list

# Access specific run
python retrieve_data.py --uid <uid_prefix>
```

### Document Storage

```
data/
├── documents/          # All Bluesky documents saved here
│   ├── <uid>_documents.jsonl
│   └── ...
```

See [PHASE2_README.md](PHASE2_README.md) for complete documentation.

