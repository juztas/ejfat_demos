# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This directory implements a **Bluesky-based experiment control framework** for GNU Radio and EJFAT data acquisition experiments. It provides:

- **Ophyd device abstraction** for GNU Radio XML-RPC control and EJFAT shared memory interfaces
- **Standardized experiment workflows** via Bluesky plans and the RunEngine
- **Persistent data storage** using DataBroker with document-based architecture
- **Live feedback** through callbacks for monitoring and analysis
- **Comprehensive data analysis** tools (statistics, visualization, export)
- **Interactive Jupyter notebooks** for data exploration and analysis

### Quick Links for Data Analysis

- 🚀 **Quick Start**: `notebooks/quick_start.ipynb` (5 minutes)
- 📚 **Full Tutorial**: `notebooks/data_retrieval_and_analysis_tutorial.ipynb` (30-45 minutes)
- 📖 **Complete Reference**: `DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md`
- 🔬 **Implementation Status**: `IMPLEMENTATION_STATUS.md`

## Architecture

The framework follows Bluesky's layered architecture:

```
Experiment Scripts (experiments/*.py)
         ↓
Scan Plans (bluesky_config/plans.py, plans_fm_shm.py)
         ↓
RunEngine + Document Model (start/descriptor/event/stop)
         ↓
Ophyd Devices (bluesky_config/devices*.py) → Hardware (GNU Radio XML-RPC, EJFAT SHM)
         ↓
Callbacks (bluesky_config/callbacks*.py) → DataBroker Storage
```

### Key Components

- **bluesky_config/devices.py**: Ophyd device classes (GNURadioSignalGenerator, MockDetector, PowerMeter)
- **bluesky_config/devices_fm_shm.py**: EJFAT shared memory devices (FMReceiver, FMSHMSource)
- **bluesky_config/plans.py**: Standard scan plans (frequency_scan, adaptive_frequency_scan, grid_scan_2d)
- **bluesky_config/plans_fm_shm.py**: FM/SHM-specific plans (fm_shm_performance_test, fm_band_survey)
- **bluesky_config/callbacks.py**: Data processing callbacks (PeakDetectorCallback, StatisticsCallback, ProgressCallback)
- **bluesky_config/callbacks_fm_shm.py**: FM-specific callbacks (RDSMonitorCallback, AudioQualityCallback)
- **experiments/**: Individual experiment scripts (fm_station_monitor.py, signal_quality_scan.py, etc.)

## Running Experiments

### Quick Start

```bash
# Activate the GNU Radio conda environment first
conda activate gnuradio

# List all available experiments
python run_experiment.py list

# Get info about a specific experiment
python run_experiment.py info mock_experiment

# Run an experiment (no hardware required)
python run_experiment.py mock_experiment

# Run with GNU Radio hardware (requires flowgraph with XML-RPC on port 8080)
python run_experiment.py frequency_characterization
```

### Running with GNU Radio Integration

Most experiments require a GNU Radio flowgraph running with an XML-RPC server:

```bash
# Terminal 1: Start GNU Radio flowgraph
cd ../widget
python sine_wave_demo.py  # or gnuradio-companion <flowgraph>.grc

# Terminal 2: Run the Bluesky experiment
cd ../full_system
python run_experiment.py frequency_characterization
```

### Running FM/SHM Experiments

FM experiments require the EJFAT shared memory interface:

```bash
# Ensure ejfat_shm package is installed
cd ../../ejfat_shm
pip install -e .
cd ../demos/full_system

# Run FM experiments
python run_experiment.py fm_station_monitor
python run_experiment.py fm_band_survey
python run_experiment.py fm_shm_performance_test
```

## Common Development Commands

### Testing

```bash
# Test all experiments (mock mode, no hardware)
python test_all_experiments.py

# Test specific subsystems
python test_fm_plans_callbacks.py
python test_fm_beamline.py

# Quick scan test
python quick_scan_test.py

# Comprehensive scan demo
python comprehensive_scan_demo.py
```

### Data Retrieval and Analysis

#### CLI Tools

```bash
# List all stored runs
python retrieve_data.py --list

# Show latest run
python retrieve_data.py --latest --all

# Get specific run by UID prefix
python retrieve_data.py --uid abc123 --all

# Export to CSV
python retrieve_data.py --latest --export csv
```

#### Jupyter Notebooks (Interactive Analysis)

```bash
# Start Jupyter Notebook
jupyter notebook

# Open one of these notebooks:
# - notebooks/quick_start.ipynb (5-minute quick start)
# - notebooks/data_retrieval_and_analysis_tutorial.ipynb (comprehensive guide)
```

**Jupyter notebooks provide:**
- Interactive data exploration
- Live visualization
- Statistical analysis
- Export in multiple formats
- Reproducible workflows

See `notebooks/README.md` for complete guide.

### Interactive Python Session

```python
from databroker import Broker
from bluesky_config.devices import MockDetector
from bluesky_config.plans import frequency_scan
from bluesky import RunEngine

# Setup
db = Broker.from_config({'temp': {'driver': 'temp'}})
RE = RunEngine({})
RE.subscribe(db.v1.insert)

# Create devices
det = MockDetector(name='det')

# Run a simple scan
RE(frequency_scan([det], det, 1e6, 10e6, 50))

# Retrieve and analyze
run = db[-1]
table = run.table()
print(table.describe())
```

## Creating New Experiments

1. **Create a new experiment file** in `experiments/`:

```python
#!/usr/bin/env python3
"""
My Custom Experiment

Brief description of what this experiment does.
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
    # Setup RunEngine
    RE = RunEngine({})
    bec = BestEffortCallback()
    RE.subscribe(bec)

    # Create devices
    sig_gen = GNURadioSignalGenerator('', name='sig_gen',
                                       host='localhost', port=8080)
    detector = MockDetector(name='det')

    # Metadata
    md = create_experiment_metadata(
        experiment_id='MY-EXP-001',
        purpose='Custom experiment purpose',
        plan_type='frequency_scan',
    )

    # Run scan
    RE(frequency_scan([detector], sig_gen, 1e6, 10e6, 100), **md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

2. **Make it executable**:

```bash
chmod +x experiments/my_custom_experiment.py
```

3. **Run it via CLI**:

```bash
python run_experiment.py my_custom_experiment
```

## Creating New Ophyd Devices

When integrating new hardware, create Ophyd device classes in `bluesky_config/devices.py` or a new devices file:

```python
from ophyd import Device, Component as Cpt, Signal
import xmlrpc.client

class MyHardware(Device):
    """Ophyd device for My Hardware."""

    # Define signals (readable/writable attributes)
    parameter = Cpt(Signal, value=0.0, kind='hinted')
    status = Cpt(Signal, value='idle', kind='normal')

    def __init__(self, prefix, *, name, host='localhost', port=8080, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.host = host
        self.port = port
        self._client = None

    def connect(self):
        """Connect to hardware."""
        try:
            self._client = xmlrpc.client.ServerProxy(
                f"http://{self.host}:{self.port}"
            )
            self._client.system.listMethods()  # Test connection
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def set_parameter(self, value):
        """Set a parameter on the hardware."""
        if self._client:
            self._client.set_parameter(value)
            self.parameter.put(value)

    def read_status(self):
        """Read status from hardware."""
        if self._client:
            status = self._client.get_status()
            self.status.put(status)
            return status
```

### Device Integration Checklist

- [ ] Create Ophyd device class inheriting from `Device`
- [ ] Define `Component` signals for all readable/writable parameters
- [ ] Implement connection logic in `__init__` or dedicated method
- [ ] Add methods to interact with hardware (set parameters, read values)
- [ ] Test device standalone before using in plans
- [ ] Add device to appropriate experiment scripts

## Creating New Plans

Custom scan plans go in `bluesky_config/plans.py` or `bluesky_config/plans_fm_shm.py`:

```python
from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp

def my_custom_scan(detectors, motor, start, stop, num_points):
    """
    Custom scan plan.

    Parameters
    ----------
    detectors : list
        List of detector devices to read
    motor : Device
        Motor/parameter to scan
    start : float
        Starting position
    stop : float
        Ending position
    num_points : int
        Number of scan points

    Yields
    ------
    msg : Msg
        Bluesky messages
    """
    # Set up metadata
    _md = {
        'plan_name': 'my_custom_scan',
        'detectors': [det.name for det in detectors],
        'motor': motor.name,
        'plan_args': {
            'start': start,
            'stop': stop,
            'num_points': num_points,
        }
    }

    # Open the run
    yield from bps.open_run(md=_md)

    # Calculate positions
    positions = np.linspace(start, stop, num_points)

    # Scan loop
    for i, pos in enumerate(positions):
        # Move motor
        yield from bps.mv(motor, pos)

        # Trigger and read detectors
        yield from bps.trigger_and_read(detectors + [motor])

    # Close the run
    yield from bps.close_run()
```

### Plan Best Practices

- **Always use generators** with `yield from` for Bluesky messages
- **Include metadata** in `_md` dict with plan_name, plan_args, etc.
- **Use plan_stubs** (`bps.mv`, `bps.trigger_and_read`, etc.) for operations
- **Open and close runs** with `bps.open_run()` and `bps.close_run()`
- **Handle exceptions** appropriately (use `bpp.finalize_wrapper` for cleanup)
- **Document parameters** thoroughly in docstring

## Creating New Callbacks

Callbacks process data in real-time. Add them to `bluesky_config/callbacks.py`:

```python
from bluesky.callbacks import CallbackBase

class MyCustomCallback(CallbackBase):
    """Custom callback for real-time processing."""

    def __init__(self, field_name):
        self.field_name = field_name
        self.values = []

    def start(self, doc):
        """Called at run start."""
        self.values = []
        print(f"Starting run {doc['uid'][:8]}")

    def event(self, doc):
        """Called for each data event."""
        value = doc['data'][self.field_name]
        self.values.append(value)

        # Custom processing
        if value > threshold:
            print(f"Alert: {self.field_name} = {value} exceeds threshold")

    def stop(self, doc):
        """Called at run stop."""
        avg = sum(self.values) / len(self.values)
        print(f"Average {self.field_name}: {avg:.2f}")
```

### Callback Methods

- `start(doc)`: Called when run starts (receives start document)
- `descriptor(doc)`: Called when data schema is defined
- `event(doc)`: Called for each data point (receives event document)
- `stop(doc)`: Called when run completes (receives stop document)

## Configuration

Edit `config.py` to customize:

### DataBroker Storage

```python
# Choose catalog type: 'temp', 'sqlite', 'mongodb'
DEFAULT_CATALOG = 'sqlite'  # Persistent storage

# Catalog directory (for sqlite)
CATALOG_DIR = DATA_DIR / 'catalog'
```

### GNU Radio Defaults

```python
GNURADIO_DEFAULT_HOST = 'localhost'
GNURADIO_DEFAULT_PORT = 8080
```

### Callback Settings

```python
ENABLE_BEST_EFFORT_CALLBACK = True  # Auto-plots and tables
ENABLE_DOCUMENT_LOGGER = True       # Save to data/documents/
ENABLE_LIVE_TABLE = False           # Can be verbose
```

## Data Storage and Retrieval

### Document Storage Layout

```
data/
├── documents/              # JSON Lines format (.jsonl)
│   ├── <uid>_documents.jsonl
│   └── ...
├── catalog/               # DataBroker msgpack catalog
│   └── *.msgpack
└── exports/              # Exported data files
    ├── *.csv
    ├── *.h5
    └── *.xlsx
```

### Retrieving Data Programmatically

```python
from databroker import Broker
from analysis.plotting import plot_run
from analysis.export import export_to_csv

# Load catalog
db = Broker.named('temp')  # or use config.DEFAULT_CATALOG

# Get recent run
run = db[-1]

# Search by metadata
runs = list(db.search(plan_name='frequency_scan', operator='alice'))

# Get data as DataFrame
table = run.table()

# Plot
plot_run(run, 'frequency', 'power', save_path='data/plot.png')

# Export
export_to_csv(run, 'data/results.csv')
```

## Data Analysis Tools

The `analysis/` directory provides comprehensive data analysis capabilities.

### Statistical Analysis (analysis/statistics.py)

```python
from analysis.statistics import (
    analyze_run,        # Comprehensive statistics (mean, std, median, IQR, skewness, kurtosis)
    find_peaks,         # Peak detection with scipy
    compare_runs,       # Multi-run comparison
    compute_correlation,# Pearson and Spearman correlation
    fit_polynomial,     # Polynomial curve fitting
    detect_outliers,    # IQR and z-score outlier detection
    compute_snr,        # Signal-to-noise ratio
)

# Example: Analyze a signal
stats = analyze_run(run, 'power')
print(f"Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}")

# Find peaks
peaks = find_peaks(run, 'frequency', 'power', prominence=5)
print(f"Found {peaks['num_peaks']} peaks")

# Compare multiple runs
runs = list(db.search(plan_name='frequency_scan'))[-5:]
comparison = compare_runs(runs, 'power')
print(comparison)
```

### Visualization (analysis/plotting.py)

```python
from analysis.plotting import (
    plot_run,           # Single run line plot
    plot_multiple_runs, # Compare multiple runs
    plot_heatmap,       # 2D heatmap for grid scans
    plot_time_series,   # Time series with multiple signals
    plot_scatter,       # Scatter plot with color
    create_summary_figure, # Automatic comprehensive summary
)

# Plot single run
plot_run(run, 'frequency', 'power')

# Compare multiple runs
plot_multiple_runs(runs, 'frequency', 'power',
                   save_path='data/comparison.png')

# Create automatic summary
create_summary_figure(run, save_path='data/summary.png')
```

### Data Export (analysis/export.py)

```python
from analysis.export import (
    export_to_csv,      # CSV with metadata headers
    export_to_hdf5,     # HDF5 with compression
    export_to_excel,    # Multi-sheet Excel file
    export_metadata,    # JSON metadata
    export_for_analysis,# Multiple formats at once
    batch_export,       # Process multiple runs
)

# Single format export
export_to_csv(run, 'data/scan.csv')
export_to_hdf5(run, 'data/scan.h5', compression=True)

# Multi-format export
export_for_analysis(run, 'data/analysis',
                   formats=['csv', 'hdf5', 'excel', 'json'])

# Batch export multiple runs
recent_runs = list(db.search(since='2025-01-08'))
batch_export(recent_runs, 'data/batch', formats=['csv', 'hdf5'])
```

### Complete Analysis Example

```python
from databroker import Broker
from analysis.statistics import analyze_run, find_peaks
from analysis.plotting import plot_run
from analysis.export import export_for_analysis
import matplotlib.pyplot as plt

# Load data
db = Broker.named('ejfat_gnuradio')
run = db[-1]

# Statistical analysis
stats = analyze_run(run, 'power')
peaks = find_peaks(run, 'frequency', 'power', prominence=5)

print(f"Statistics: mean={stats['mean']:.2f}, std={stats['std']:.2f}")
print(f"Peaks: {peaks['num_peaks']} found")

# Visualization
fig, ax = plot_run(run, 'frequency', 'power')
if peaks['num_peaks'] > 0:
    ax.plot(peaks['peak_positions'], peaks['peak_values'],
            'r*', markersize=15, label='Peaks')
    ax.legend()
plt.show()

# Export
export_for_analysis(run, 'data/results',
                   formats=['csv', 'hdf5', 'excel'])
```

## Common Issues

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'bluesky_config'`

**Solution**: Always run experiments from the `full_system/` directory, or use the CLI:
```bash
cd full_system
python run_experiment.py <experiment_name>
```

### GNU Radio Connection Failures

**Problem**: `ConnectionError: Failed to connect to GNU Radio XML-RPC server`

**Solution**:
1. Ensure GNU Radio flowgraph is running
2. Check XML-RPC server block is in flowgraph (from gr-xmlrpc)
3. Verify host/port match (default: localhost:8080)
4. Check firewall settings

### Missing Dependencies

**Problem**: `ModuleNotFoundError: No module named 'bluesky'`

**Solution**:
```bash
conda activate gnuradio
pip install bluesky ophyd databroker matplotlib pandas scipy openpyxl h5py
```

### EJFAT SHM Issues

**Problem**: `ImportError: cannot import name 'EjfatSHMReader'`

**Solution**: Install the ejfat_shm package:
```bash
cd ../../ejfat_shm
pip install -e .
```

## Jupyter Notebooks for Interactive Analysis

The `notebooks/` directory provides interactive Jupyter notebooks for data analysis.

### Quick Start Notebook (5 minutes)

**File:** `notebooks/quick_start.ipynb`

**Purpose:** Get started with data analysis quickly

**What it does:**
1. Connect to DataBroker catalog
2. Load latest experiment run
3. Display data table and statistics
4. Create basic plot
5. Find peaks
6. Export to CSV

**Usage:**
```bash
# Generate some test data first
python run_experiment.py mock_experiment

# Start Jupyter
jupyter notebook

# Open notebooks/quick_start.ipynb
# Run all cells (Cell → Run All)
```

### Comprehensive Tutorial (30-45 minutes)

**File:** `notebooks/data_retrieval_and_analysis_tutorial.ipynb`

**Purpose:** Complete interactive guide to all analysis capabilities

**Topics covered:**
- DataBroker connection and searching
- Data retrieval and metadata access
- Statistical analysis (mean, std, peaks, outliers, correlation)
- Multiple visualization types
- Comparing multiple runs
- Exporting in multiple formats (CSV, HDF5, Excel, JSON)
- Advanced analysis workflows

**Features:**
- 40+ executable code cells
- Comprehensive examples
- Progressive complexity
- Error handling for missing data
- Real output examples

### Benefits of Jupyter Notebooks

✅ **Interactive Learning**
- Run code step-by-step
- See immediate results
- Experiment safely
- Modify and retry

✅ **Reproducible Analysis**
- Document entire workflow
- Share with collaborators
- Save results inline
- Track methodology

✅ **Flexible Environment**
- Mix code, text, and plots
- Try different approaches
- Quick prototyping
- Publication-ready figures

### Requirements

```bash
conda activate gnuradio
pip install jupyter notebook matplotlib pandas scipy
```

See `notebooks/README.md` for complete documentation.

## Testing Before Committing

Always run these checks before committing changes:

```bash
# 1. Test all mock experiments (no hardware)
python test_all_experiments.py

# 2. Check imports and basic functionality
python -c "from bluesky_config import devices, plans, callbacks; print('OK')"

# 3. Run quick scan test
python quick_scan_test.py

# 4. Test data retrieval
python retrieve_data.py --list

# 5. Test Jupyter notebooks (optional)
jupyter nbconvert --execute --to notebook notebooks/quick_start.ipynb
```

## Related Documentation

### Getting Started
- **README.md**: Comprehensive user guide and API reference
- **notebooks/README.md**: Jupyter notebook usage guide
- **notebooks/quick_start.ipynb**: 5-minute interactive tutorial (Jupyter)
- **DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md**: Complete data analysis reference

### Design & Implementation
- **BLUESKY_COMPREHENSIVE_PLAN.md**: Original design document and architecture
- **IMPLEMENTATION_STATUS.md**: Detailed status of all planned features
- **PHASE1_COMPLETE.md**: Basic Bluesky integration completion notes
- **PHASE2_README.md**: Persistent storage implementation details
- **PHASE3_COMPLETE.md**: Advanced callbacks and metadata
- **PHASE4_IMPLEMENTATION.md**: Data export and visualization features
- **FM_SHM_INTEGRATION_PLAN.md**: EJFAT shared memory integration plan

### Interactive Tutorials
- **notebooks/quick_start.ipynb**: Quick start (5 minutes)
- **notebooks/data_retrieval_and_analysis_tutorial.ipynb**: Comprehensive tutorial (30-45 minutes)

### External Resources
- Bluesky Documentation: https://blueskyproject.io/
- Ophyd Documentation: https://blueskyproject.io/ophyd/
- DataBroker Documentation: https://blueskyproject.io/databroker/
- Jupyter Documentation: https://jupyter.org/documentation

## Development Workflow

### Adding a New Feature

1. **Plan**: Review existing architecture in README.md and design docs
2. **Implement**: Add code to appropriate module (devices, plans, callbacks)
3. **Test**: Create test experiment in `experiments/` or add to `test_all_experiments.py`
4. **Document**: Update README.md with usage examples
5. **Commit**: Run test suite before committing

### Working with Real Hardware

1. **Mock first**: Always implement and test with mock devices first
2. **Incremental integration**: Test one hardware component at a time
3. **Error handling**: Add proper connection checks and error messages
4. **Document**: Note hardware requirements in experiment docstrings

### Data Analysis Workflow

#### Option 1: Jupyter Notebook (Recommended for Interactive Analysis)

1. **Run experiment**: Use `run_experiment.py` CLI
2. **Start Jupyter**: `jupyter notebook`
3. **Open notebook**: `notebooks/quick_start.ipynb` or `notebooks/data_retrieval_and_analysis_tutorial.ipynb`
4. **Run cells**: Execute code cells step-by-step
5. **Explore interactively**: Modify code, create visualizations, export results

#### Option 2: Command-Line Tools

1. **Run experiment**: Use `run_experiment.py` CLI or custom script
2. **Verify storage**: Check `data/documents/` for saved documents
3. **Retrieve data**: Use `retrieve_data.py --latest --all`
4. **Quick export**: `retrieve_data.py --latest --export csv`

#### Option 3: Python Scripts

1. **Run experiment**: Use `run_experiment.py` CLI
2. **Write analysis script**: Use tools from `analysis/` directory
3. **Execute**: `python my_analysis.py`
4. **Export**: Save results in multiple formats

**See DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md for complete workflows and examples.**
