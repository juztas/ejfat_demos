# Tutorial: Running Experiments and Capturing Data

This tutorial provides step-by-step instructions for running experiments that capture data in the Bluesky-based experiment control framework.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Methods for Running Experiments](#methods-for-running-experiments)
4. [Understanding What Gets Captured](#understanding-what-gets-captured)
5. [Verifying Data Capture](#verifying-data-capture)
6. [Retrieving and Analyzing Captured Data](#retrieving-and-analyzing-captured-data)
7. [Practical Examples](#practical-examples)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Activate the Environment

```bash
conda activate gnuradio
```

### 2. Navigate to the Project Directory

```bash
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/full_system
```

### 3. Verify Installation

```bash
# Check that required packages are available
python -c "from bluesky import RunEngine; from databroker import Broker; print('✓ All dependencies available')"
```

---

## Quick Start (5 Minutes)

The fastest way to run an experiment and capture data:

### Step 1: Run a Mock Experiment (No Hardware Required)

```bash
python run_experiment.py mock_experiment
```

**What happens:**
- A scan is performed with mock devices (simulated data)
- Data is automatically captured to `data/documents/` directory
- You'll see output showing the scan progress
- At the end, you'll get a UID (unique identifier) for this run

**Expected output:**
```
======================================================================
RUNNING: mock_experiment
======================================================================

======================================================================
MOCK EXPERIMENT (No Hardware Required)
======================================================================
Experiment ID: MOCK-001
Operator: <your username>
Purpose: Test Bluesky framework with mock devices

Motor range: 0 - 10
Number of points: 20
======================================================================

Progress: 100% |████████████████████████████| 20/20 [Time: 0:00:01]

======================================================================
EXPERIMENT COMPLETE
======================================================================
Run UID: abc12345

Documents saved to: data/documents/abc12345_documents.jsonl

To analyze this data:
  from databroker import Broker
  db = Broker.named('temp')
  run = db['abc12345']
  table = run.table()
  print(table)
======================================================================
```

### Step 2: View the Captured Data

```bash
python retrieve_data.py --latest --all
```

**What you'll see:**
- Summary of the run (UID, timestamp, operator, purpose)
- Plan arguments (scan parameters)
- Event count (number of data points collected)
- Data table showing all captured values

### Step 3: Export Data to CSV

```bash
python retrieve_data.py --latest --export csv
```

**Result:**
- Creates `data/exports/run_<uid>.csv` with all data
- You can open this in Excel, Python pandas, etc.

**Congratulations!** You've just performed your first data-capturing run.

---

## Methods for Running Experiments

There are four main ways to run experiments:

### Method 1: CLI Tool (Recommended for Beginners)

**Best for:** Quick execution, exploring available experiments

```bash
# List all available experiments
python run_experiment.py list

# Get details about a specific experiment
python run_experiment.py info mock_experiment

# Run an experiment
python run_experiment.py <experiment_name>
```

**Examples:**
```bash
# Mock experiment (no hardware)
python run_experiment.py mock_experiment

# Frequency scan (requires GNU Radio running)
python run_experiment.py frequency_characterization

# FM monitoring (requires EJFAT SHM)
python run_experiment.py fm_station_monitor
```

**Pros:**
- Simple and fast
- Auto-discovery of experiments
- Built-in error handling
- No code editing needed

**Cons:**
- Limited customization
- Can't modify parameters without editing the experiment file

---

### Method 2: Direct Python Execution

**Best for:** Quick execution of a single experiment

```bash
cd experiments
python mock_experiment.py
```

**Pros:**
- Simple
- Direct access to experiment file

**Cons:**
- Must be in correct directory
- Less structured than CLI

---

### Method 3: Custom Python Script

**Best for:** Custom workflows, parameter variations, batch processing

**Create a file:** `my_custom_run.py`

```python
#!/usr/bin/env python3
"""Custom experiment runner with specific parameters."""

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from ophyd import Signal
from bluesky.plans import scan
from bluesky_config.devices import MockDetector
from bluesky_config.callbacks import StatisticsCallback, DocumentLogger
from bluesky_config.metadata import create_experiment_metadata

# Setup
RE = RunEngine({})
bec = BestEffortCallback()
RE.subscribe(bec)

# Add data storage callback
doc_logger = DocumentLogger('data/documents')
RE.subscribe(doc_logger)

# Add statistics callback
stats = StatisticsCallback(['det_value'])
RE.subscribe(stats)

# Create devices
motor = Signal(name='motor', value=0)
detector = MockDetector(name='det', noise_level=0.1)

# Define scan parameters (customize these!)
start = 0
stop = 20
num_points = 50

# Create metadata
md = create_experiment_metadata(
    experiment_id='CUSTOM-001',
    purpose='My custom parameter scan',
    plan_type='scan',
    start=start,
    stop=stop,
    num_points=num_points,
)

# Run the scan
print(f"Running scan: {start} to {stop} with {num_points} points")
uid = RE(scan([detector], motor, start, stop, num_points), **md)

print(f"\n✓ Complete! Run UID: {uid[0][:8]}")
print(f"Data saved to: data/documents/{uid[0][:8]}_documents.jsonl")
```

**Run it:**
```bash
python my_custom_run.py
```

**Pros:**
- Full control over parameters
- Can customize callbacks, metadata
- Easy to modify and iterate
- Can run multiple scans in sequence

**Cons:**
- Requires Python knowledge
- More verbose than CLI

---

### Method 4: Interactive Python Session

**Best for:** Exploration, debugging, iterative development

```bash
python
```

```python
# Import required modules
from bluesky import RunEngine
from ophyd import Signal
from bluesky.plans import scan
from bluesky_config.devices import MockDetector
from bluesky_config.callbacks import DocumentLogger
from databroker import Broker

# Setup RunEngine
RE = RunEngine({})

# Add data storage (CRITICAL for capturing data!)
doc_logger = DocumentLogger('data/documents')
RE.subscribe(doc_logger)

# Optional: also store in DataBroker catalog
db = Broker.named('temp')
RE.subscribe(db.v1.insert)

# Create devices
motor = Signal(name='motor', value=0)
det = MockDetector(name='det')

# Run a scan
uid = RE(scan([det], motor, 0, 10, 20))

# Immediately retrieve and view data
run = db[-1]
print(run.table())
```

**Pros:**
- Immediate feedback
- Can inspect variables
- Great for learning
- Quick iterations

**Cons:**
- Not reproducible (unless you save commands)
- Easy to lose track of what you did
- No persistent script

---

## Understanding What Gets Captured

When you run an experiment, the following data is automatically captured:

### 1. **Documents (Bluesky Data Model)**

Every run generates four types of documents:

#### **Start Document** (1 per run)
- Run UID (unique identifier)
- Timestamp
- Plan name and arguments
- Metadata (experiment_id, operator, purpose, etc.)
- Device configurations

#### **Descriptor Documents** (1+ per run)
- Data schema (what fields are captured)
- Data keys and their properties (shape, dtype, units)
- Object names (detectors, motors, etc.)

#### **Event Documents** (many per run)
- Actual measurement data
- One event per scan point
- Contains readings from all devices
- Timestamps for each reading

#### **Stop Document** (1 per run)
- Exit status (success/fail)
- Final timestamp
- Total number of events

### 2. **Storage Locations**

Data is stored in two places:

#### **Document Files** (`data/documents/`)
- Human-readable JSON Lines format
- One file per run: `<uid>_documents.jsonl`
- Can be opened in text editor
- Permanently stored (survives environment restart)

**Example file content:**
```json
{"start": {"uid": "abc123", "time": 1234567890.0, "plan_name": "scan", ...}}
{"descriptor": {"uid": "def456", "run_start": "abc123", "data_keys": {...}}}
{"event": {"uid": "ghi789", "data": {"motor": 0.0, "det_value": 1.23}, ...}}
{"event": {"uid": "jkl012", "data": {"motor": 0.5, "det_value": 1.45}, ...}}
...
{"stop": {"uid": "mno345", "run_start": "abc123", "exit_status": "success"}}
```

#### **DataBroker Catalog** (optional)
- Can use temp (in-memory), sqlite (persistent), or mongodb
- Configured in `config.py`
- Enables advanced querying and searching
- Can index by metadata

### 3. **What Data Gets Captured**

During each scan point (event), the following are captured:

- **Motor/parameter positions**: Current value of scanned parameter
- **Detector readings**: All detector values at this position
- **Timestamps**: Exact time of measurement
- **Metadata**: Any custom metadata you add

**Example event data:**
```python
{
    'motor': 5.0,           # Motor position
    'det_value': 2.34,      # Detector reading
    'det_timestamp': 1234567890.123,
    'motor_timestamp': 1234567890.122
}
```

---

## Verifying Data Capture

After running an experiment, verify that data was captured:

### Quick Verification

```bash
# Check that documents were saved
ls -lh data/documents/

# You should see: <uid>_documents.jsonl files
```

### Detailed Verification

#### **Method 1: Using retrieve_data.py**

```bash
# Show latest run summary
python retrieve_data.py --latest

# Show latest run with full data table
python retrieve_data.py --latest --all

# List all saved runs
python retrieve_data.py --list
```

#### **Method 2: Direct File Inspection**

```bash
# View the raw JSONL file
ls -t data/documents/*.jsonl | head -1 | xargs cat

# Or with jq for pretty printing (if installed)
ls -t data/documents/*.jsonl | head -1 | xargs cat | jq .
```

#### **Method 3: Python Interactive**

```python
from databroker import Broker

# Load catalog
db = Broker.named('temp')  # or 'sqlite' if using persistent

# Get latest run
run = db[-1]

# View metadata
print(f"UID: {run.metadata['start']['uid']}")
print(f"Plan: {run.metadata['start']['plan_name']}")
print(f"Time: {run.metadata['start']['time']}")

# View data
table = run.table()
print(table)

# Check data shape
print(f"\nData shape: {table.shape}")
print(f"Columns: {list(table.columns)}")
print(f"Number of events: {len(table)}")
```

---

## Retrieving and Analyzing Captured Data

### Using retrieve_data.py (Command Line)

```bash
# Show latest run with all details
python retrieve_data.py --latest --all

# Find run by UID prefix (first 6-8 characters)
python retrieve_data.py --uid abc123 --all

# List all runs
python retrieve_data.py --list

# Export to CSV
python retrieve_data.py --latest --export csv

# Export to HDF5
python retrieve_data.py --latest --export hdf5

# Export to Excel
python retrieve_data.py --latest --export excel
```

### Using Python Scripts

```python
from databroker import Broker
from analysis.statistics import analyze_run, find_peaks
from analysis.plotting import plot_run
from analysis.export import export_to_csv

# Load catalog
db = Broker.named('temp')

# Get latest run
run = db[-1]

# 1. View data as DataFrame
df = run.table()
print(df.head())
print(df.describe())

# 2. Statistical analysis
stats = analyze_run(run, 'det_value')
print(f"Mean: {stats['mean']:.3f}")
print(f"Std Dev: {stats['std']:.3f}")
print(f"Min: {stats['min']:.3f}")
print(f"Max: {stats['max']:.3f}")

# 3. Find peaks
peaks = find_peaks(run, 'motor', 'det_value', prominence=0.5)
print(f"Found {peaks['num_peaks']} peaks")
if peaks['num_peaks'] > 0:
    print(f"Peak positions: {peaks['peak_positions']}")
    print(f"Peak values: {peaks['peak_values']}")

# 4. Plot data
import matplotlib.pyplot as plt
fig, ax = plot_run(run, 'motor', 'det_value')
plt.show()

# 5. Export to CSV
export_to_csv(run, 'data/exports/my_analysis.csv')
```

### Using Jupyter Notebooks (Interactive)

**Best for:** Exploratory data analysis, visualization, reporting

```bash
# Start Jupyter
jupyter notebook

# Open one of:
# - notebooks/quick_start.ipynb (5-minute tutorial)
# - notebooks/data_retrieval_and_analysis_tutorial.ipynb (comprehensive)
```

**Jupyter workflow:**
1. Connect to DataBroker
2. Load run(s) by UID or search criteria
3. Visualize data interactively
4. Perform statistical analysis
5. Export in multiple formats
6. Save notebook as reproducible analysis

See `notebooks/README.md` for details.

---

## Practical Examples

### Example 1: Simple Mock Scan with Data Retrieval

```bash
# Run experiment
python run_experiment.py mock_experiment

# Retrieve and view data
python retrieve_data.py --latest --all

# Export to CSV
python retrieve_data.py --latest --export csv

# The CSV file is now at: data/exports/run_<uid>.csv
```

### Example 2: Custom Scan with Multiple Detectors

**Create:** `multi_detector_scan.py`

```python
#!/usr/bin/env python3
from bluesky import RunEngine
from ophyd import Signal
from bluesky.plans import scan
from bluesky_config.devices import MockDetector
from bluesky_config.callbacks import DocumentLogger, StatisticsCallback
from bluesky_config.metadata import create_experiment_metadata

# Setup
RE = RunEngine({})
doc_logger = DocumentLogger('data/documents')
RE.subscribe(doc_logger)

stats = StatisticsCallback(['det1_value', 'det2_value'])
RE.subscribe(stats)

# Create devices
motor = Signal(name='motor', value=0)
det1 = MockDetector(name='det1', noise_level=0.1)
det2 = MockDetector(name='det2', noise_level=0.2)

# Metadata
md = create_experiment_metadata(
    experiment_id='MULTI-DET-001',
    purpose='Compare two detectors',
    plan_type='scan',
)

# Run scan with TWO detectors
uid = RE(scan([det1, det2], motor, 0, 10, 50), **md)

print(f"\n✓ Complete! UID: {uid[0][:8]}")
```

**Run and analyze:**
```bash
python multi_detector_scan.py

# View data
python retrieve_data.py --latest --all

# Should show columns: motor, det1_value, det2_value
```

### Example 3: Batch Processing Multiple Runs

**Create:** `batch_scan.py`

```python
#!/usr/bin/env python3
from bluesky import RunEngine
from ophyd import Signal
from bluesky.plans import scan
from bluesky_config.devices import MockDetector
from bluesky_config.callbacks import DocumentLogger
from bluesky_config.metadata import create_experiment_metadata

# Setup
RE = RunEngine({})
doc_logger = DocumentLogger('data/documents')
RE.subscribe(doc_logger)

motor = Signal(name='motor', value=0)
det = MockDetector(name='det')

# Run 5 scans with different parameters
for i in range(5):
    noise = 0.1 * (i + 1)
    det.noise_level = noise

    md = create_experiment_metadata(
        experiment_id=f'BATCH-{i+1:03d}',
        purpose=f'Batch scan {i+1} with noise={noise}',
        plan_type='scan',
        batch_id=i+1,
        noise_level=noise,
    )

    uid = RE(scan([det], motor, 0, 10, 20), **md)
    print(f"Run {i+1}/5 complete: {uid[0][:8]}")

print("\n✓ All 5 runs complete!")
```

**Analyze batch:**
```python
from databroker import Broker
from analysis.statistics import compare_runs

db = Broker.named('temp')

# Get all runs from this batch
batch_runs = list(db.search(plan_type='scan'))[-5:]

# Compare them
comparison = compare_runs(batch_runs, 'det_value')
print(comparison)
```

### Example 4: Real-Time Peak Detection

**Create:** `peak_monitoring_scan.py`

```python
#!/usr/bin/env python3
from bluesky import RunEngine
from ophyd import Signal
from bluesky.plans import scan
from bluesky_config.devices import MockDetector
from bluesky_config.callbacks import DocumentLogger, PeakDetectorCallback
from bluesky_config.metadata import create_experiment_metadata

# Setup
RE = RunEngine({})
doc_logger = DocumentLogger('data/documents')
RE.subscribe(doc_logger)

# Peak detector callback (alerts in real-time)
peak_detector = PeakDetectorCallback('det_value', threshold=2.0)
RE.subscribe(peak_detector)

motor = Signal(name='motor', value=0)
det = MockDetector(name='det', noise_level=0.3)

md = create_experiment_metadata(
    experiment_id='PEAK-001',
    purpose='Monitor for peaks above threshold',
    plan_type='scan',
)

# Run scan - peaks will be printed in real-time
uid = RE(scan([det], motor, 0, 10, 50), **md)

# Access detected peaks
print(f"\n✓ Scan complete!")
print(f"Total peaks detected: {len(peak_detector.peaks)}")
if peak_detector.peaks:
    print("\nPeak positions:")
    for motor_pos, det_val in peak_detector.peaks:
        print(f"  Motor={motor_pos:.2f}, Detector={det_val:.3f}")
```

### Example 5: With GNU Radio Hardware

**Prerequisites:**
- GNU Radio flowgraph running
- XML-RPC server enabled on port 8080

```python
#!/usr/bin/env python3
from bluesky import RunEngine
from bluesky_config.devices import GNURadioSignalGenerator, PowerMeter
from bluesky_config.plans import frequency_scan
from bluesky_config.callbacks import DocumentLogger
from bluesky_config.metadata import create_experiment_metadata

# Setup
RE = RunEngine({})
doc_logger = DocumentLogger('data/documents')
RE.subscribe(doc_logger)

# Connect to GNU Radio
sig_gen = GNURadioSignalGenerator('', name='sig_gen',
                                   host='localhost', port=8080)
power_meter = PowerMeter(name='power')

# Connect to hardware
if not sig_gen.connect():
    print("Failed to connect to GNU Radio!")
    exit(1)

# Scan frequency range
md = create_experiment_metadata(
    experiment_id='FREQ-SCAN-001',
    purpose='Characterize frequency response',
    plan_type='frequency_scan',
)

# Frequency scan: 1 MHz to 10 MHz, 100 points
uid = RE(frequency_scan([power_meter], sig_gen, 1e6, 10e6, 100), **md)

print(f"\n✓ Frequency scan complete! UID: {uid[0][:8]}")
```

---

## Troubleshooting

### Problem: No data files created

**Symptoms:**
- `data/documents/` directory is empty
- No `<uid>_documents.jsonl` files

**Solutions:**

1. **Check that DocumentLogger is subscribed:**
```python
from bluesky_config.callbacks import DocumentLogger

doc_logger = DocumentLogger('data/documents')
RE.subscribe(doc_logger)  # CRITICAL!
```

2. **Verify directory exists:**
```bash
mkdir -p data/documents
```

3. **Check for errors during run:**
- Look for exceptions printed to console
- Check if run completed successfully

4. **Verify UID was returned:**
```python
uid = RE(scan(...))
print(f"UID: {uid}")  # Should print a list with UID
```

---

### Problem: Cannot retrieve data with DataBroker

**Symptoms:**
- `db[-1]` raises `IndexError`
- `db[uid]` raises `KeyError`

**Solutions:**

1. **Check catalog configuration:**
```python
from databroker import Broker
db = Broker.named('temp')  # or 'sqlite'
```

2. **Verify data was inserted:**
```python
# Make sure you subscribed to db.v1.insert
RE.subscribe(db.v1.insert)
```

3. **List available runs:**
```python
runs = list(db.search())
print(f"Total runs: {len(runs)}")
```

4. **Use document files instead:**
```bash
python retrieve_data.py --list
```

---

### Problem: retrieve_data.py shows no runs

**Symptoms:**
- `python retrieve_data.py --list` shows empty
- Latest run not found

**Solutions:**

1. **Check document directory:**
```bash
ls data/documents/
```

2. **Verify path in retrieve_data.py:**
- Default is `data/documents/`
- Make sure you're running from correct directory

3. **Check file permissions:**
```bash
ls -la data/documents/
```

---

### Problem: Data looks wrong or incomplete

**Symptoms:**
- Missing columns
- Fewer events than expected
- Strange values

**Solutions:**

1. **Check descriptor document:**
```python
run = db[-1]
desc = run.metadata['start']
print("Data keys:", desc.get('data_keys', {}))
```

2. **Verify devices were triggered:**
- Make sure all detectors are in the scan list
- Check device status/connection

3. **Check for exceptions during scan:**
```python
stop = run.metadata['stop']
print(f"Exit status: {stop.get('exit_status')}")
print(f"Reason: {stop.get('reason', 'N/A')}")
```

4. **Inspect event documents directly:**
```bash
cat data/documents/<uid>_documents.jsonl | grep event | head -5
```

---

### Problem: Experiment fails to run

**Symptoms:**
- Exception raised during RE(scan(...))
- Run aborts early

**Common causes and solutions:**

1. **Device not connected:**
```python
# Always check connection for hardware devices
if not device.connect():
    print("Connection failed!")
    exit(1)
```

2. **Invalid scan parameters:**
```python
# Make sure start < stop, num > 0
start, stop, num = 0, 10, 50  # Good
start, stop, num = 10, 0, 50  # Bad! start > stop
```

3. **Missing callbacks:**
```python
# Some callbacks require specific data fields
# Make sure detector names match what callbacks expect
```

4. **Import errors:**
```bash
# Make sure you're in the correct directory
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/full_system
```

---

## Next Steps

Now that you can run experiments and capture data, explore:

1. **Interactive Analysis**: Open `notebooks/quick_start.ipynb` for hands-on data exploration

2. **Advanced Callbacks**: See `bluesky_config/callbacks.py` for real-time processing

3. **Custom Plans**: Create your own scan patterns in `bluesky_config/plans.py`

4. **Integration with Hardware**: Connect GNU Radio or EJFAT devices

5. **Batch Processing**: Run multiple experiments with parameter variations

6. **Data Visualization**: Use `analysis/plotting.py` for publication-quality figures

7. **Export and Share**: Use `analysis/export.py` to share data in standard formats

---

## Additional Resources

- **README.md**: Comprehensive framework documentation
- **DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md**: Complete data analysis reference
- **notebooks/data_retrieval_and_analysis_tutorial.ipynb**: Interactive 30-minute tutorial
- **CLAUDE.md**: Development guidelines and architecture
- **Bluesky Documentation**: https://blueskyproject.io/
- **DataBroker Documentation**: https://blueskyproject.io/databroker/

---

**Questions or Issues?**

- Check the troubleshooting section above
- Review error messages carefully
- Inspect document files directly in `data/documents/`
- Try running `test_all_experiments.py` to verify framework functionality
- Consult CLAUDE.md for development guidance

**Happy experimenting!**
