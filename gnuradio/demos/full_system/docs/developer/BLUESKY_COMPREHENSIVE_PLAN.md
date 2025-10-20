# Comprehensive Bluesky Experiment Framework Plan

**Created:** 2025-10-08
**Purpose:** Build a production-ready Bluesky experiment framework for GNU Radio + EJFAT integration

## Overview

This plan outlines building a comprehensive Bluesky experiment framework in the `full_system` directory. The framework will leverage Bluesky's document model for metadata collection, support various scan types, and prepare for future high-speed sample recording integration.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Bluesky Experiment Layer                  │
│  ┌───────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │  Custom Plans │  │ Callbacks  │  │  Data Analysis   │  │
│  │  & Scans      │  │ & Handlers │  │  & Plotting      │  │
│  └───────┬───────┘  └─────┬──────┘  └────────┬─────────┘  │
│          └─────────────────┼──────────────────┘             │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         RunEngine + Document Model                    │ │
│  │  (start, descriptor, event, stop documents)           │ │
│  └────────────────────┬──────────────────────────────────┘ │
│                       ▼                                      │
│  ┌──────────────────────────────────┐  ┌────────────────┐ │
│  │  DataBroker (MongoDB/SQLite)     │  │ Live Callbacks │ │
│  │  - Persistent storage            │  │ - Live plots   │ │
│  │  - Metadata indexing             │  │ - Progress     │ │
│  │  - Data retrieval                │  │ - Alerts       │ │
│  └──────────────────────────────────┘  └────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Ophyd Device Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ GNU Radio    │  │   Custom     │  │  Future: EJFAT   │ │
│  │ Devices      │  │   Detectors  │  │  Data Sources    │ │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬────────┘ │
└─────────┼──────────────────┼────────────────────┼───────────┘
          ▼                  ▼                    ▼
    XML-RPC Server     Custom Signals      High-Speed Storage
   (GNU Radio FG)                           (Future Phase)
```

## Phase 1: Core Infrastructure

### Directory Structure

```
full_system/
├── bluesky_config/
│   ├── __init__.py
│   ├── devices.py           # All Ophyd device definitions
│   ├── plans.py             # Custom scan plans
│   ├── callbacks.py         # Custom callbacks for live feedback
│   └── metadata.py          # Metadata collection utilities
├── experiments/
│   ├── __init__.py
│   ├── frequency_characterization.py    # Example experiment
│   ├── signal_quality_scan.py          # Example experiment
│   └── adaptive_tuning.py              # Example experiment
├── analysis/
│   ├── __init__.py
│   ├── plotting.py          # Data visualization
│   ├── export.py            # Export to various formats
│   └── statistics.py        # Statistical analysis
├── data/
│   └── .gitkeep             # Persistent data storage location
├── notebooks/
│   └── analysis_template.ipynb  # Jupyter notebook for analysis
├── config.py                # Configuration settings
├── setup_environment.py     # Initialize RunEngine, DataBroker
├── run_experiment.py        # Main CLI for running experiments
├── BLUESKY_COMPREHENSIVE_PLAN.md  # This document
└── README.md               # Documentation
```

### File Purposes

- **bluesky_config/** - Core Bluesky configuration and utilities
  - `devices.py` - Ophyd device wrappers for GNU Radio, detectors, motors
  - `plans.py` - Reusable scan plans and plan helpers
  - `callbacks.py` - Custom callbacks for live data processing
  - `metadata.py` - Metadata collection and organization utilities

- **experiments/** - Specific experiment implementations
  - Each file is a complete experiment script
  - Imports from bluesky_config
  - Can be run standalone or via run_experiment.py

- **analysis/** - Post-experiment data analysis
  - `plotting.py` - Visualization functions
  - `export.py` - Data export to CSV, HDF5, JSON
  - `statistics.py` - Statistical analysis tools

- **data/** - Persistent data storage
  - DataBroker SQLite databases
  - Metadata catalogs
  - References to external data files

- **notebooks/** - Jupyter notebooks for interactive analysis

## Phase 2: Bluesky Document Model

### Document Types

Bluesky's document model consists of four document types emitted during a run:

#### 1. Start Document
Emitted at the beginning of a run, contains metadata:

```python
{
    'uid': '7ae9b4e3-...',           # Unique run identifier
    'time': 1704741600.123,          # Unix timestamp
    'scan_id': 42,                   # Sequential scan number
    'plan_name': 'frequency_sweep',  # Name of the plan
    'plan_type': 'generator',

    # User-provided metadata
    'operator': 'username',
    'purpose': 'FM frequency characterization',
    'sample': 'Ottawa FM band',
    'experiment_id': 'EXP-2025-001',

    # Plan parameters
    'plan_args': {
        'start': 88.0e6,
        'stop': 108.0e6,
        'num_points': 100,
    },

    # Environmental/facility metadata
    'facility': 'EJFAT',
    'beamline': 'gnuradio_testbed',
    'temperature': 22.5,
    'notes': 'Clear weather, low interference',
}
```

#### 2. Descriptor Document
Describes the data structure, emitted before events:

```python
{
    'uid': '9bd2c1a4-...',
    'time': 1704741600.456,
    'run_start': '7ae9b4e3-...',    # Links to start document

    # Data keys (what will be in events)
    'data_keys': {
        'frequency': {
            'source': 'PV:FM:FREQ',
            'dtype': 'number',
            'shape': [],
            'units': 'Hz',
            'lower_ctrl_limit': 88.0e6,
            'upper_ctrl_limit': 108.0e6,
        },
        'signal_power': {
            'source': 'PV:DETECTOR:POWER',
            'dtype': 'number',
            'shape': [],
            'units': 'dBm',
        },
    },

    # Configuration (device settings snapshot)
    'configuration': {
        'fm_tx': {
            'data': {'sample_rate': 32000},
            'timestamps': {'sample_rate': 1704741600.0},
        },
    },
}
```

#### 3. Event Documents
Contain actual measurement data:

```python
{
    'uid': 'f3a2b8c1-...',
    'time': 1704741601.123,           # Event timestamp
    'descriptor': '9bd2c1a4-...',     # Links to descriptor
    'seq_num': 1,                     # Sequence number

    # Actual data
    'data': {
        'frequency': 88.0e6,
        'signal_power': -45.3,
    },

    # Timestamps for each reading
    'timestamps': {
        'frequency': 1704741601.120,
        'signal_power': 1704741601.122,
    },
}
```

#### 4. Stop Document
Emitted at the end of a run:

```python
{
    'uid': 'a7c3d2e1-...',
    'time': 1704741650.789,
    'run_start': '7ae9b4e3-...',     # Links to start document
    'exit_status': 'success',         # or 'abort', 'fail'
    'num_events': {
        'primary': 100,               # Number of events collected
    },

    # Optional summary statistics
    'summary': {
        'total_time': 50.666,
        'avg_signal_power': -42.1,
        'peak_frequency': 98.5e6,
    },
}
```

### Document Flow Example

```python
from bluesky import RunEngine
from bluesky.plans import scan
import bluesky.plan_stubs as bps

RE = RunEngine({})

# Subscribe to see documents
def print_document(name, doc):
    print(f"{name.upper()}: {doc}")

RE.subscribe(print_document)

# Run a scan - watch documents flow
RE(scan([detector], motor, 0, 10, 11))

# Output:
# START: {'uid': '...', 'time': ..., 'plan_name': 'scan', ...}
# DESCRIPTOR: {'uid': '...', 'data_keys': {...}, ...}
# EVENT: {'seq_num': 1, 'data': {'motor': 0, 'detector': ...}, ...}
# EVENT: {'seq_num': 2, 'data': {'motor': 1, 'detector': ...}, ...}
# ...
# STOP: {'exit_status': 'success', 'num_events': {...}, ...}
```

## Phase 3: DataBroker Setup

DataBroker stores and retrieves Bluesky documents.

### Storage Options

#### 1. Temporary (In-Memory) - For Testing

```python
from databroker import Broker

# Temporary catalog (lost on restart)
db = Broker.named('temp')
RE.subscribe(db.insert)

# Use it
RE(scan([det], motor, 0, 10, 11))
run = db[-1]  # Get most recent run
```

#### 2. SQLite - For Single-User Persistence

```python
from databroker import Broker

# SQLite-backed catalog
db = Broker.from_config({
    'description': 'EJFAT GNU Radio Experiments',
    'metadatastore': {
        'module': 'databroker.headersource.sqlite',
        'class': 'MDS',
        'config': {
            'directory': 'data/',
            'timezone': 'US/Eastern',
        }
    },
    'assets': {
        'module': 'databroker.assets.sqlite',
        'class': 'Registry',
        'config': {
            'dbpath': 'data/assets.db'
        }
    }
})

RE.subscribe(db.insert)
```

#### 3. MongoDB - For Production/Multi-User

```python
# Requires MongoDB server running
db = Broker.from_config({
    'description': 'EJFAT Production',
    'metadatastore': {
        'module': 'databroker.headersource.mongo',
        'class': 'MDS',
        'config': {
            'host': 'localhost',
            'port': 27017,
            'database': 'metadatastore',
            'timezone': 'US/Eastern',
        }
    },
    'assets': {
        'module': 'databroker.assets.mongo',
        'class': 'Registry',
        'config': {
            'host': 'localhost',
            'port': 27017,
            'database': 'filestore',
        }
    }
})
```

### Data Retrieval

```python
# Search by metadata
runs = db.search(plan_name='frequency_sweep')
runs = db.search(operator='alice', since='2025-01-01')

# Get specific run
run = db[-1]              # Most recent
run = db['7ae9b4e3-...']  # By UID

# Access metadata
start_doc = run.metadata['start']
print(start_doc['plan_args'])

# Get data as table
table = run.table()       # Pandas DataFrame
print(table.columns)
print(table['frequency'])

# Get raw documents
for name, doc in run.documents():
    print(name, doc)
```

## Phase 4: Experiment Types & Plans

### 1. Basic Scans

```python
from bluesky.plans import scan, grid_scan, list_scan

# Linear scan
RE(scan([detector], motor, start, stop, num_points))

# Grid scan (2D)
RE(grid_scan([det], motor1, start1, stop1, num1,
                     motor2, start2, stop2, num2))

# Arbitrary points
RE(list_scan([det], motor, [100, 250, 500, 1000, 2500]))
```

### 2. Adaptive Scans

```python
from bluesky.plans import adaptive_scan

# Adaptive step size based on derivative
RE(adaptive_scan([det], 'det', motor,
                 start, stop,
                 min_step=0.01, max_step=1.0,
                 target_delta=0.1,
                 backstep=True))
```

### 3. Time Series

```python
from bluesky.plans import count

# Repeated measurements
RE(count([det1, det2], num=100, delay=0.1))
```

### 4. Custom Plans

```python
import bluesky.plan_stubs as bps
from bluesky.preprocessors import run_decorator

@run_decorator(md={'plan_name': 'frequency_characterization'})
def characterize_frequency_response(signal_gen, detector,
                                     frequencies, num_samples=10):
    """
    Characterize signal response at specific frequencies.

    Takes multiple samples at each frequency for statistical analysis.
    """
    for freq in frequencies:
        # Set frequency
        yield from bps.abs_set(signal_gen.frequency, freq, wait=True)

        # Wait for settling
        yield from bps.sleep(0.1)

        # Take multiple samples
        for i in range(num_samples):
            yield from bps.trigger_and_read([detector])
            yield from bps.sleep(0.05)

# Usage
freqs = [88.0e6, 93.0e6, 98.0e6, 103.0e6, 108.0e6]
RE(characterize_frequency_response(fm_tx, power_meter, freqs, num_samples=10))
```

### 5. Multi-Device Coordination

```python
def synchronized_tx_rx_sweep(tx, rx, detector, start, stop, num):
    """Sweep TX and RX together while measuring."""

    @run_decorator(md={
        'plan_name': 'synchronized_sweep',
        'tx_range': (start, stop),
        'num_points': num,
    })
    def inner():
        import numpy as np
        frequencies = np.linspace(start, stop, num)

        for freq in frequencies:
            # Set both TX and RX
            yield from bps.abs_set(tx.frequency, freq, wait=True)
            yield from bps.abs_set(rx.frequency, freq, wait=True)

            # Measure
            yield from bps.trigger_and_read([detector])

    yield from inner()
```

## Phase 5: Metadata Strategy

### Hierarchical Organization

```python
# config.py - Facility-level metadata (constant)
FACILITY_MD = {
    'facility': 'EJFAT',
    'beamline': 'gnuradio_testbed',
    'location': 'Ottawa',
}

# Experiment-level (per session)
experiment_md = {
    'experiment_id': 'EXP-2025-001',
    'operator': 'username',
    'purpose': 'FM frequency characterization',
    'sample': 'Ottawa FM band',
    'project': 'EJFAT-DEMO',
}

# Scan-level (per run)
scan_md = {
    'scan_type': 'frequency_sweep',
    'start_freq': 88.0e6,
    'stop_freq': 108.0e6,
    'num_points': 100,
    'dwell_time': 0.5,
}

# Environmental (periodic or per-scan)
env_md = {
    'temperature': 22.5,
    'humidity': 45,
    'weather': 'clear',
    'notes': 'Low interference conditions',
}

# Combine all metadata
full_md = {**FACILITY_MD, **experiment_md, **scan_md, **env_md}

# Use in plan
RE(scan([det], motor, start, stop, num), **full_md)
```

### Metadata Utilities

```python
# bluesky_config/metadata.py

import datetime
import socket
import getpass

def get_session_metadata(experiment_id, purpose):
    """Generate standard session metadata."""
    return {
        'experiment_id': experiment_id,
        'purpose': purpose,
        'operator': getpass.getuser(),
        'hostname': socket.gethostname(),
        'session_start': datetime.datetime.now().isoformat(),
    }

def get_plan_metadata(plan_type, **kwargs):
    """Generate plan-specific metadata."""
    return {
        'plan_type': plan_type,
        'plan_args': kwargs,
        'timestamp': datetime.datetime.now().isoformat(),
    }

def add_environmental_metadata(temperature=None, humidity=None, notes=''):
    """Add environmental conditions."""
    md = {'notes': notes}
    if temperature is not None:
        md['temperature'] = temperature
    if humidity is not None:
        md['humidity'] = humidity
    return md
```

## Phase 6: Live Callbacks

### Built-in Callbacks

```python
from bluesky.callbacks import LiveTable, LivePlot
from bluesky.callbacks.best_effort import BestEffortCallback

# 1. LiveTable - Print progress to console
live_table = LiveTable(['motor', 'detector'])
RE.subscribe(live_table)

# 2. LivePlot - Real-time matplotlib plot
live_plot = LivePlot('detector', 'motor', marker='o')
RE.subscribe(live_plot)

# 3. BestEffortCallback - Automatic table + plots
bec = BestEffortCallback()
RE.subscribe(bec)

# Run scan - see live updates
RE(scan([det], motor, 0, 10, 11))
```

### Custom Callbacks

```python
# bluesky_config/callbacks.py

class PeakDetectorCallback:
    """Detect and report peaks during scan."""

    def __init__(self, signal_name, threshold=None):
        self.signal_name = signal_name
        self.threshold = threshold
        self.peak_value = None
        self.peak_position = None

    def start(self, doc):
        """Reset on new run."""
        self.peak_value = None
        self.peak_position = None

    def event(self, doc):
        """Check each event for peaks."""
        value = doc['data'][self.signal_name]

        if self.peak_value is None or value > self.peak_value:
            self.peak_value = value
            # Find motor position (first non-detector key)
            for key in doc['data']:
                if key != self.signal_name:
                    self.peak_position = doc['data'][key]
                    break

            if self.threshold and value > self.threshold:
                print(f"🔔 ALERT: Signal {value:.2f} exceeds threshold "
                      f"{self.threshold} at position {self.peak_position}")

    def stop(self, doc):
        """Report final peak."""
        if self.peak_value is not None:
            print(f"\n📊 Peak detected: {self.peak_value:.2f} "
                  f"at position {self.peak_position}")

# Usage
peak_detector = PeakDetectorCallback('detector', threshold=0.8)
RE.subscribe(peak_detector)
```

### Document Logger Callback

```python
import json
from pathlib import Path

class DocumentLogger:
    """Save all documents to JSON files."""

    def __init__(self, output_dir='data/documents'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_uid = None

    def __call__(self, name, doc):
        """Save each document."""
        if name == 'start':
            self.run_uid = doc['uid']

        if self.run_uid:
            filename = self.output_dir / f"{self.run_uid}_{name}.json"
            with open(filename, 'a') as f:
                json.dump({name: doc}, f, default=str, indent=2)
                f.write('\n')

# Usage
doc_logger = DocumentLogger('data/documents')
RE.subscribe(doc_logger)
```

## Phase 7: Data Retrieval & Analysis

### Basic Data Access

```python
# Get recent runs
runs = list(db.search(since='2025-01-08'))
print(f"Found {len(runs)} runs today")

# Get specific run
run = db[-1]  # Most recent

# Access metadata
print("Operator:", run.metadata['start']['operator'])
print("Plan:", run.metadata['start']['plan_name'])

# Get data as DataFrame
table = run.table()
print(table.head())
print(table.describe())
```

### Plotting Utilities

```python
# analysis/plotting.py

import matplotlib.pyplot as plt
import numpy as np

def plot_run(run, x_key, y_key, title=None):
    """Plot data from a run."""
    table = run.table()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(table[x_key], table[y_key], 'o-')

    ax.set_xlabel(x_key)
    ax.set_ylabel(y_key)

    if title is None:
        start = run.metadata['start']
        title = f"{start['plan_name']} - {start.get('purpose', 'No description')}"
    ax.set_title(title)

    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    return fig, ax

def plot_multiple_runs(runs, x_key, y_key):
    """Compare multiple runs."""
    fig, ax = plt.subplots(figsize=(12, 7))

    for run in runs:
        table = run.table()
        start = run.metadata['start']
        label = f"Run {start['scan_id']} - {start.get('sample', 'unknown')}"
        ax.plot(table[x_key], table[y_key], 'o-', label=label, alpha=0.7)

    ax.set_xlabel(x_key)
    ax.set_ylabel(y_key)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    return fig, ax

# Usage
from analysis.plotting import plot_run, plot_multiple_runs

run = db[-1]
plot_run(run, 'frequency', 'signal_power')
plt.show()

# Compare runs
recent_runs = list(db.search(plan_name='frequency_sweep'))[-5:]
plot_multiple_runs(recent_runs, 'frequency', 'signal_power')
plt.show()
```

### Export Utilities

```python
# analysis/export.py

def export_to_csv(run, filename):
    """Export run data to CSV."""
    table = run.table()

    # Add metadata as header comments
    with open(filename, 'w') as f:
        start = run.metadata['start']
        f.write(f"# Plan: {start['plan_name']}\n")
        f.write(f"# Operator: {start.get('operator', 'unknown')}\n")
        f.write(f"# Time: {start['time']}\n")
        f.write(f"# UID: {start['uid']}\n\n")

    # Append data
    table.to_csv(filename, mode='a', index=False)
    print(f"Exported to {filename}")

def export_to_hdf5(run, filename):
    """Export run data to HDF5."""
    table = run.table()

    # Save data
    table.to_hdf(filename, 'data', mode='w')

    # Save metadata separately
    import h5py
    with h5py.File(filename, 'a') as f:
        metadata_group = f.create_group('metadata')
        start = run.metadata['start']
        for key, value in start.items():
            metadata_group.attrs[key] = str(value)

    print(f"Exported to {filename}")

def export_metadata(run, filename):
    """Export metadata to JSON."""
    import json

    with open(filename, 'w') as f:
        json.dump(run.metadata['start'], f, indent=2, default=str)

    print(f"Exported metadata to {filename}")

# Usage
from analysis.export import export_to_csv, export_to_hdf5, export_metadata

run = db[-1]
export_to_csv(run, 'data/scan_001.csv')
export_to_hdf5(run, 'data/scan_001.h5')
export_metadata(run, 'data/scan_001_metadata.json')
```

### Statistical Analysis

```python
# analysis/statistics.py

import numpy as np
from scipy import stats

def analyze_run(run, signal_key):
    """Compute statistics for a run."""
    table = run.table()
    signal = table[signal_key].values

    result = {
        'mean': np.mean(signal),
        'std': np.std(signal),
        'min': np.min(signal),
        'max': np.max(signal),
        'median': np.median(signal),
        'peak_to_peak': np.ptp(signal),
    }

    return result

def find_peaks(run, x_key, y_key, height=None, prominence=None):
    """Find peaks in scan data."""
    from scipy.signal import find_peaks as scipy_find_peaks

    table = run.table()
    x = table[x_key].values
    y = table[y_key].values

    peaks, properties = scipy_find_peaks(y, height=height, prominence=prominence)

    return {
        'peak_indices': peaks,
        'peak_positions': x[peaks],
        'peak_values': y[peaks],
        'properties': properties,
    }

def compare_runs(runs, signal_key):
    """Compare statistics across multiple runs."""
    stats_list = []

    for run in runs:
        stats_dict = analyze_run(run, signal_key)
        stats_dict['scan_id'] = run.metadata['start']['scan_id']
        stats_dict['uid'] = run.metadata['start']['uid'][:8]
        stats_list.append(stats_dict)

    import pandas as pd
    return pd.DataFrame(stats_list)

# Usage
from analysis.statistics import analyze_run, find_peaks, compare_runs

run = db[-1]
stats = analyze_run(run, 'signal_power')
print("Statistics:", stats)

peaks = find_peaks(run, 'frequency', 'signal_power', prominence=5)
print(f"Found {len(peaks['peak_positions'])} peaks at:", peaks['peak_positions'])

recent_runs = list(db.search(plan_name='frequency_sweep'))[-5:]
comparison = compare_runs(recent_runs, 'signal_power')
print(comparison)
```

## Phase 8: Future Integration - High-Speed Sample Recording

### External Data References

Bluesky can reference external data files in metadata:

```python
@run_decorator(md={'plan_name': 'scan_with_samples'})
def scan_with_high_speed_recording(detectors, motor, start, stop, num,
                                    sample_dir='/mnt/highspeed'):
    """Scan with external high-speed sample recording."""
    import datetime
    from pathlib import Path

    # Generate unique filename for this scan
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    sample_file = Path(sample_dir) / f'samples_{timestamp}.bin'

    # Add file reference to metadata
    yield from bps.open_run(md={
        'sample_file': str(sample_file),
        'sample_format': 'complex64',
        'sample_rate': 32e6,
    })

    # Trigger external recorder (implementation-specific)
    yield from trigger_external_recorder(sample_file)

    # Run the scan
    yield from bp.scan(detectors, motor, start, stop, num)

    # Stop recorder
    yield from stop_external_recorder()

    # Add file size to stop document
    file_size = sample_file.stat().st_size
    yield from bps.close_run(md={'sample_file_size': file_size})
```

### Synchronized Timestamps

Align Bluesky event timestamps with sample data:

```python
class SampleRecorderDevice(Device):
    """Device that triggers sample recording."""

    def trigger(self):
        """Start recording with timestamp."""
        timestamp = time.time()

        # Start external recording process
        self.recorder.start(timestamp=timestamp)

        # Return status with timestamp
        status = DeviceStatus(self)
        status._finished(timestamp=timestamp)
        return status

    def read(self):
        """Return recording status."""
        return {
            'recorder_timestamp': {
                'value': self.recorder.current_timestamp,
                'timestamp': time.time(),
            },
            'sample_count': {
                'value': self.recorder.sample_count,
                'timestamp': time.time(),
            },
        }
```

### Parallel Acquisition Pattern

```python
def coordinated_scan_and_record(detectors, motor, start, stop, num,
                                  sample_recorder):
    """Run scan while recording samples in parallel."""

    @run_decorator(md={
        'plan_name': 'coordinated_acquisition',
        'parallel_recording': True,
    })
    def inner():
        # Start sample recording
        yield from bps.abs_set(sample_recorder.recording, True, wait=True)

        # Run scan (while recording continues in background)
        yield from bp.scan(detectors, motor, start, stop, num)

        # Stop recording
        yield from bps.abs_set(sample_recorder.recording, False, wait=True)

        # Read final statistics
        stats = yield from bps.read(sample_recorder)
        print(f"Recorded {stats['sample_count']['value']} samples")

    yield from inner()
```

## Implementation Order

### Recommended Steps

1. **Setup directory structure** (5 min)
   - Create all directories
   - Add __init__.py files
   - Create .gitkeep for data/

2. **Create basic device definitions** (15 min)
   - Copy from ../widget/gnuradio_bluesky/
   - Extend with custom devices
   - Add any new signal types

3. **Setup DataBroker with SQLite** (10 min)
   - Create config.py with database settings
   - Initialize database in setup_environment.py
   - Test basic storage/retrieval

4. **Create simple scan plans with metadata** (20 min)
   - Implement basic plans in bluesky_config/plans.py
   - Add metadata utilities in bluesky_config/metadata.py
   - Test with RunEngine

5. **Add live callbacks** (10 min)
   - Setup BestEffortCallback
   - Create custom callbacks in bluesky_config/callbacks.py
   - Test live feedback

6. **Write example experiment script** (15 min)
   - Create experiments/frequency_characterization.py
   - Demonstrate full workflow
   - Add CLI interface

7. **Create data retrieval and plotting utilities** (20 min)
   - Implement analysis/plotting.py
   - Implement analysis/export.py
   - Implement analysis/statistics.py

8. **Document everything in README** (15 min)
   - Installation instructions
   - Usage examples
   - Architecture overview
   - Troubleshooting

**Total time estimate: ~2 hours**

## Key Technologies

- **Bluesky** - Experiment orchestration framework
- **Ophyd** - Hardware abstraction layer
- **DataBroker** - Data storage and retrieval
- **GNU Radio** - Signal processing (existing)
- **XML-RPC** - Communication protocol (existing)
- **SQLite/MongoDB** - Persistent storage
- **Pandas** - Data analysis
- **Matplotlib** - Visualization
- **HDF5/CSV** - Data export formats

## Benefits of This Approach

1. **Reproducibility** - All metadata and parameters are captured
2. **Searchability** - Find runs by any metadata field
3. **Extensibility** - Easy to add new devices, plans, callbacks
4. **Analysis-Ready** - Data in standard formats (Pandas, HDF5)
5. **Real-Time Feedback** - Live plots and callbacks during runs
6. **Future-Proof** - Designed for high-speed data integration
7. **Standard Workflows** - Leverages Bluesky's proven patterns

## Related Documentation

- [Bluesky Documentation](https://blueskyproject.io/)
- [Ophyd Documentation](https://blueskyproject.io/ophyd/)
- [DataBroker Documentation](https://blueskyproject.io/databroker/)
- [Bluesky Tutorial](https://nsls-ii.github.io/bluesky/tutorial.html)
- [Example: widget/BLUESKY_INTEGRATION_PLAN.md](../widget/BLUESKY_INTEGRATION_PLAN.md)
- [Example: widget/README_BLUESKY.md](../widget/README_BLUESKY.md)

## Next Steps

After completing this plan:

1. Integrate with EJFAT data streaming
2. Add E2SAR reassembler as Ophyd device
3. Implement high-speed sample recording
4. Create visualization dashboard
5. Add automated analysis pipelines
6. Integrate with facility-wide data management
