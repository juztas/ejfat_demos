# Data Retrieval and Analysis Guide

**Document Version:** 1.0
**Last Updated:** 2025-10-18
**Framework:** Bluesky Experiment Framework for EJFAT GNU Radio

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Data Storage Architecture](#data-storage-architecture)
4. [CLI Tools](#cli-tools)
5. [Programmatic Data Access](#programmatic-data-access)
6. [Data Analysis](#data-analysis)
7. [Visualization](#visualization)
8. [Export Options](#export-options)
9. [Batch Processing](#batch-processing)
10. [Advanced Workflows](#advanced-workflows)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers how to retrieve, analyze, and visualize data from Bluesky experiments in the EJFAT GNU Radio framework. All experiment data is automatically captured in Bluesky's document model and stored persistently for later analysis.

### What Data is Captured?

Every experiment produces four types of documents:

1. **Start Document** - Metadata about the experiment (operator, purpose, parameters)
2. **Descriptor Document** - Data structure definition (what fields, units, types)
3. **Event Documents** - Actual measurement data (one per data point)
4. **Stop Document** - Summary and exit status

### Where is Data Stored?

```
data/
├── documents/          # Raw Bluesky documents (JSON Lines format)
│   └── <uid>_documents.jsonl
├── catalog/           # DataBroker catalog (msgpack files)
│   └── *.msgpack
└── exports/           # Exported data files
    ├── *.csv
    ├── *.h5
    └── *.xlsx
```

---

## Quick Start

### Retrieve Latest Run (CLI)

```bash
# Show summary of latest run
python retrieve_data.py --latest

# Show with data table
python retrieve_data.py --latest --table

# Show with statistics
python retrieve_data.py --latest --stats

# Show everything
python retrieve_data.py --latest --all
```

### List All Runs

```bash
python retrieve_data.py --list
```

Output:
```
======================================================================
SAVED RUNS
======================================================================
[  1] 85067302 | frequency_scan       | alice      | 85067302-b45c-4a1e-...
[  2] f3a2b8c1 | fm_band_survey       | bob        | f3a2b8c1-9e2d-4f...
[  3] 9bd2c1a4 | signal_quality_scan  | alice      | 9bd2c1a4-7ae9-4e...
======================================================================
Total runs: 3
```

### Quick Python Analysis

```python
from databroker import Broker

# Load catalog
db = Broker.named('ejfat_gnuradio')

# Get latest run
run = db[-1]

# Get data as DataFrame
table = run.table()
print(table.head())

# Basic statistics
print(table.describe())
```

---

## Data Storage Architecture

### Document Storage (JSON Lines)

Every run is saved as a `.jsonl` file in `data/documents/`:

```bash
data/documents/85067302-b45c-4a1e-8f6d-2c3e9a4b1d7e_documents.jsonl
```

Each line contains one document:
```json
{"start": {"uid": "85067302...", "plan_name": "frequency_scan", ...}}
{"descriptor": {"uid": "9bd2c1a4...", "data_keys": {...}, ...}}
{"event": {"seq_num": 1, "data": {"frequency": 88e6, ...}, ...}}
...
{"stop": {"exit_status": "success", "num_events": {...}, ...}}
```

### DataBroker Catalog

DataBroker provides a queryable interface to all runs:

- **Catalog location:** `data/catalog/*.msgpack`
- **Catalog name:** `ejfat_gnuradio` (configurable in config.py)
- **Format:** MessagePack (binary, efficient)

### Advantages of Dual Storage

1. **JSON Lines** - Human-readable, easy to parse, portable
2. **DataBroker** - Fast queries, indexed metadata, Python API

---

## CLI Tools

### retrieve_data.py

The primary tool for viewing saved experiment data.

#### Basic Usage

```bash
# List all runs
python retrieve_data.py --list

# Show latest run summary
python retrieve_data.py --latest

# Show specific run by UID (prefix matching)
python retrieve_data.py --uid 85067302
```

#### Display Options

```bash
# Show data table (first 20 rows)
python retrieve_data.py --latest --table

# Show more rows
python retrieve_data.py --latest --table --max-rows 50

# Show statistics
python retrieve_data.py --latest --stats

# Show everything (summary + table + stats)
python retrieve_data.py --latest --all
```

#### Example Output

```bash
$ python retrieve_data.py --latest --all

Loading: 85067302-b45c-4a1e-8f6d-2c3e9a4b1d7e_documents.jsonl

======================================================================
RUN SUMMARY
======================================================================

UID: 85067302-b45c-4a1e-8f6d-2c3e9a4b1d7e
Scan ID: 42
Plan: frequency_scan
Operator: alice
Purpose: FM frequency response characterization
Time: 1704741600.123

Plan Arguments:
  start: 88000000.0
  stop: 108000000.0
  num_points: 100

Metadata:
  experiment_id: EXP-2025-001
  facility: EJFAT
  beamline: gnuradio_testbed
  temperature: 22.5
  humidity: 45

Events collected: 100
Exit status: success
======================================================================

======================================================================
DATA TABLE
======================================================================
seq_num         | time            | frequency      | power
--------------------------------------------------------------------
              1 |   1704741601.12 |    88000000.00 |        -45.30
              2 |   1704741602.25 |    88200000.00 |        -44.80
              3 |   1704741603.38 |    88400000.00 |        -46.10
...
======================================================================

======================================================================
STATISTICS
======================================================================

frequency:
  Count:  100
  Mean:   98000000.000000
  Std:    5916079.783100
  Min:    88000000.000000
  Max:    108000000.000000
  Median: 98000000.000000

power:
  Count:  100
  Mean:   -42.345000
  Std:    3.456789
  Min:    -48.200000
  Max:    -35.100000
  Median: -42.000000
======================================================================
```

---

## Programmatic Data Access

### Using DataBroker

DataBroker provides a Python API for querying and retrieving experiment data.

#### Setup

```python
from databroker import Broker

# Load catalog (configured in config.py)
db = Broker.named('ejfat_gnuradio')

# Or use temporary catalog
db_temp = Broker.named('temp')
```

#### Retrieving Runs

```python
# Get most recent run
run = db[-1]

# Get second-most recent
run = db[-2]

# Get by UID (full or prefix)
run = db['85067302']
run = db['85067302-b45c-4a1e-8f6d-2c3e9a4b1d7e']

# Get by scan ID (if unique)
# Note: scan_id may not be unique across sessions
for r in db.v1():
    if r.metadata['start']['scan_id'] == 42:
        run = r
        break
```

#### Searching Runs

```python
# Search by plan name
runs = db.search(plan_name='frequency_scan')

# Search by operator
runs = db.search(operator='alice')

# Search by date
runs = db.search(since='2025-01-08')
runs = db.search(since='2025-01-08', until='2025-01-09')

# Search by custom metadata
runs = db.search(purpose='characterization')
runs = db.search(experiment_id='EXP-2025-001')

# Combine criteria
runs = db.search(plan_name='frequency_scan',
                 operator='alice',
                 since='2025-01-08')

# Convert to list and get specific number
recent_5 = list(db.search(plan_name='frequency_scan'))[-5:]
```

#### Accessing Metadata

```python
run = db[-1]

# Get start document (primary metadata)
start = run.metadata['start']

print(f"UID: {start['uid']}")
print(f"Scan ID: {start['scan_id']}")
print(f"Plan: {start['plan_name']}")
print(f"Operator: {start.get('operator', 'unknown')}")
print(f"Purpose: {start.get('purpose', 'N/A')}")
print(f"Time: {start['time']}")

# Plan arguments
if 'plan_args' in start:
    print("Plan arguments:")
    for key, value in start['plan_args'].items():
        print(f"  {key}: {value}")

# Custom metadata
print(f"Experiment ID: {start.get('experiment_id', 'N/A')}")
print(f"Temperature: {start.get('temperature', 'N/A')}")
```

#### Accessing Data

```python
# Get data as Pandas DataFrame
table = run.table()

# DataFrame operations
print(table.head())           # First 5 rows
print(table.tail())           # Last 5 rows
print(table.describe())       # Statistics
print(table.columns)          # Column names
print(table.shape)            # (rows, columns)

# Access specific columns
frequencies = table['frequency']
powers = table['power']

# Filter data
high_power = table[table['power'] > -40]
freq_range = table[(table['frequency'] >= 90e6) &
                   (table['frequency'] <= 100e6)]

# Compute on data
mean_power = table['power'].mean()
max_power = table['power'].max()
```

#### Iterating Over Documents

```python
# Get all documents
for name, doc in run.documents():
    print(f"{name}: {doc.keys()}")

# Output:
# start: dict_keys(['uid', 'time', 'scan_id', 'plan_name', ...])
# descriptor: dict_keys(['uid', 'time', 'run_start', 'data_keys', ...])
# event: dict_keys(['uid', 'time', 'seq_num', 'data', ...])
# event: dict_keys(['uid', 'time', 'seq_num', 'data', ...])
# ...
# stop: dict_keys(['uid', 'time', 'run_start', 'exit_status', ...])
```

---

## Data Analysis

The `analysis/` directory provides comprehensive analysis tools.

### Statistical Analysis

```python
from analysis.statistics import (
    analyze_run, find_peaks, compare_runs,
    compute_correlation, fit_polynomial,
    detect_outliers, compute_snr
)
from databroker import Broker

db = Broker.named('ejfat_gnuradio')
run = db[-1]
```

#### Basic Statistics

```python
# Comprehensive statistics for a signal
stats = analyze_run(run, 'power')

print(f"Mean: {stats['mean']:.2f}")
print(f"Std Dev: {stats['std']:.2f}")
print(f"Min: {stats['min']:.2f}")
print(f"Max: {stats['max']:.2f}")
print(f"Median: {stats['median']:.2f}")
print(f"Peak-to-Peak: {stats['peak_to_peak']:.2f}")
print(f"RMS: {stats['rms']:.2f}")
print(f"Skewness: {stats['skewness']:.3f}")
print(f"Kurtosis: {stats['kurtosis']:.3f}")
print(f"IQR: {stats['iqr']:.2f}")
```

#### Peak Finding

```python
# Find peaks in frequency scan
peaks = find_peaks(run, 'frequency', 'power',
                   prominence=5,  # Minimum peak prominence
                   distance=10)   # Min samples between peaks

print(f"Found {peaks['num_peaks']} peaks")
print(f"Peak frequencies: {peaks['peak_positions']/1e6} MHz")
print(f"Peak powers: {peaks['peak_values']} dBm")

# Access properties
if peaks['num_peaks'] > 0:
    print(f"Strongest peak: {peaks['peak_values'].max():.2f} dBm "
          f"at {peaks['peak_positions'][peaks['peak_values'].argmax()]/1e6:.1f} MHz")
```

#### Comparing Multiple Runs

```python
# Get recent frequency scans
recent_runs = list(db.search(plan_name='frequency_scan'))[-5:]

# Compare statistics
comparison = compare_runs(recent_runs, 'power')
print(comparison)

# Output (DataFrame):
#    scan_id       uid  mean   std   min   max  median  time
# 0       42  85067302 -42.3  3.45 -48.2 -35.1   -42.0  1704741600.123
# 1       43  f3a2b8c1 -41.8  3.12 -47.5 -36.2   -41.5  1704748200.456
# 2       44  9bd2c1a4 -43.1  3.78 -49.0 -34.8   -43.0  1704754800.789
# ...

# Analyze trends
print(f"Average power trend: {comparison['mean'].diff().mean():.2f} dBm per run")
print(f"Stability (std dev): {comparison['std'].mean():.2f} dBm")
```

#### Correlation Analysis

```python
# Compute correlation between signals
corr = compute_correlation(run, 'frequency', 'power')

print(f"Pearson correlation: {corr['pearson_r']:.3f} (p={corr['pearson_p']:.2e})")
print(f"Spearman correlation: {corr['spearman_r']:.3f} (p={corr['spearman_p']:.2e})")

# Interpret
if abs(corr['pearson_r']) > 0.7:
    print("Strong correlation detected!")
```

#### Polynomial Fitting

```python
# Fit 3rd-degree polynomial
fit = fit_polynomial(run, 'frequency', 'power', degree=3)

print(f"Coefficients: {fit['coefficients']}")
print(f"R-squared: {fit['r_squared']:.4f}")
print(f"RMSE: {fit['rmse']:.4f}")

# Use the fit for predictions
freq_new = 95e6
power_pred = fit['polynomial'](freq_new)
print(f"Predicted power at {freq_new/1e6:.1f} MHz: {power_pred:.2f} dBm")
```

#### Outlier Detection

```python
# Detect outliers using IQR method
outliers = detect_outliers(run, 'power', method='iqr', threshold=1.5)

print(f"Found {outliers['num_outliers']} outliers "
      f"({outliers['outlier_fraction']*100:.1f}%)")

if outliers['num_outliers'] > 0:
    print(f"Outlier values: {outliers['outlier_values']}")
    print(f"At indices: {outliers['outlier_indices']}")

# Or use z-score method
outliers_z = detect_outliers(run, 'power', method='zscore', threshold=3)
```

#### Signal-to-Noise Ratio

```python
# Compute SNR
snr = compute_snr(run, 'detector_signal')

print(f"SNR: {snr['snr_db']:.1f} dB")
print(f"Signal power: {snr['signal_power']:.2e}")
print(f"Noise power: {snr['noise_power']:.2e}")
```

#### Complete Run Summary

```python
from analysis.statistics import summarize_run

# Get comprehensive summary
summary = summarize_run(run)

print(f"Run {summary['scan_id']} ({summary['uid']})")
print(f"Plan: {summary['plan_name']}")
print(f"Operator: {summary['operator']}")
print(f"Events: {summary['num_events']}")

# Signal statistics
for key, stats in summary.items():
    if key.endswith('_stats'):
        signal_name = key.replace('_stats', '')
        print(f"\n{signal_name}:")
        print(f"  Mean: {stats['mean']:.2f}")
        print(f"  Std: {stats['std']:.2f}")
        print(f"  Range: [{stats['min']:.2f}, {stats['max']:.2f}]")
```

---

## Visualization

The `analysis/plotting.py` module provides visualization tools.

```python
from analysis.plotting import (
    plot_run, plot_multiple_runs, plot_heatmap,
    plot_time_series, plot_scatter, create_summary_figure
)
import matplotlib.pyplot as plt
from databroker import Broker

db = Broker.named('ejfat_gnuradio')
```

### Single Run Plot

```python
run = db[-1]

# Basic plot
fig, ax = plot_run(run, 'frequency', 'power')
plt.show()

# Save to file
plot_run(run, 'frequency', 'power',
         title='FM Band Frequency Response',
         save_path='data/exports/frequency_response.png')
```

### Compare Multiple Runs

```python
# Get recent runs
recent_runs = list(db.search(plan_name='frequency_scan'))[-3:]

# Plot comparison
fig, ax = plot_multiple_runs(recent_runs, 'frequency', 'power',
                              title='Frequency Response Comparison')
plt.show()

# Save
plot_multiple_runs(recent_runs, 'frequency', 'power',
                   save_path='data/exports/comparison.png')
```

### Heatmap (2D Grid Scans)

```python
# For 2D grid scan data
run = db['<grid_scan_uid>']

fig, ax = plot_heatmap(run, 'motor1', 'motor2', 'detector',
                       title='2D Parameter Sweep')
plt.show()
```

### Time Series

```python
# Plot multiple signals over time
run = db[-1]

fig, axes = plot_time_series(run,
                              y_keys=['power', 'buffer_fill', 'data_rate'],
                              title='Time Series Monitoring')
plt.show()
```

### Scatter Plot with Color

```python
# Scatter with color-coded third variable
fig, ax = plot_scatter(run, 'frequency', 'power',
                       color_key='signal_quality',
                       title='Frequency vs Power')
plt.show()
```

### Summary Figure

```python
# Automatic comprehensive summary figure
fig = create_summary_figure(run,
                            save_path='data/exports/run_summary.png')
plt.show()
```

### Custom Plotting

```python
import matplotlib.pyplot as plt

run = db[-1]
table = run.table()

# Create custom plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Top: Main data
ax1.plot(table['frequency']/1e6, table['power'], 'o-', linewidth=2)
ax1.set_xlabel('Frequency (MHz)')
ax1.set_ylabel('Power (dBm)')
ax1.set_title('Frequency Response')
ax1.grid(True, alpha=0.3)

# Bottom: Signal quality
ax2.plot(table['frequency']/1e6, table['signal_quality'], 'o-',
         color='green', linewidth=2)
ax2.set_xlabel('Frequency (MHz)')
ax2.set_ylabel('Signal Quality')
ax2.set_title('Signal Quality vs Frequency')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('data/exports/custom_analysis.png', dpi=150)
plt.show()
```

---

## Export Options

The `analysis/export.py` module provides data export in multiple formats.

```python
from analysis.export import (
    export_to_csv, export_to_hdf5, export_to_excel,
    export_metadata, export_all_documents,
    export_for_analysis, batch_export
)
from databroker import Broker

db = Broker.named('ejfat_gnuradio')
run = db[-1]
```

### Export to CSV

```python
# Export with metadata comments
export_to_csv(run, 'data/exports/scan_001.csv')

# Export without metadata
export_to_csv(run, 'data/exports/scan_001_data_only.csv',
              include_metadata=False)
```

**CSV Output:**
```csv
# Plan: frequency_scan
# Operator: alice
# Time: 1704741600.123
# UID: 85067302-b45c-4a1e-8f6d-2c3e9a4b1d7e
# Purpose: FM frequency response characterization
# Plan args: {'start': 88000000.0, 'stop': 108000000.0, 'num_points': 100}
#
seq_num,time,frequency,power
1,1704741601.12,88000000.0,-45.3
2,1704741602.25,88200000.0,-44.8
...
```

### Export to HDF5

```python
# Export with compression (recommended for large datasets)
export_to_hdf5(run, 'data/exports/scan_001.h5', compression=True)

# Read back in Python
import pandas as pd
table = pd.read_hdf('data/exports/scan_001.h5', 'data')
```

### Export to Excel

```python
# Creates multi-sheet Excel file
# - Sheet 1: Data
# - Sheet 2: Metadata
# - Sheet 3: Statistics
export_to_excel(run, 'data/exports/scan_001.xlsx')
```

### Export Metadata Only

```python
# Export metadata as JSON
export_metadata(run, 'data/exports/scan_001_metadata.json')
```

### Export All Documents

```python
# Export all Bluesky documents as separate JSON files
export_all_documents(run, output_dir='data/exports/run_85067302')

# Creates:
# - 85067302_start.json
# - 85067302_descriptor.json
# - 85067302_event.json (multiple)
# - 85067302_stop.json
```

### Multi-Format Export

```python
# Export in multiple formats at once
exported = export_for_analysis(
    run,
    output_dir='data/exports/experiment_001',
    formats=['csv', 'hdf5', 'excel', 'json']
)

# Returns dictionary of format: filepath
print(exported)
# {'csv': PosixPath('data/exports/.../run_42_85067302.csv'),
#  'hdf5': PosixPath('data/exports/.../run_42_85067302.h5'),
#  'excel': PosixPath('data/exports/.../run_42_85067302.xlsx'),
#  'json': PosixPath('data/exports/.../run_42_85067302_metadata.json')}
```

---

## Batch Processing

### Batch Export

```python
from analysis.export import batch_export
from databroker import Broker

db = Broker.named('ejfat_gnuradio')

# Get all runs from a specific day
runs = list(db.search(since='2025-01-08', until='2025-01-09'))

# Export all in multiple formats
batch_export(runs,
             output_dir='data/exports/batch_2025-01-08',
             formats=['csv', 'hdf5'])
```

**Output:**
```
Batch exporting 15 runs...

[1/15] Run 42 (85067302):
✅ Exported to CSV: data/exports/batch_2025-01-08/run_42_85067302/run_42_85067302.csv
✅ Exported to HDF5: data/exports/batch_2025-01-08/run_42_85067302/run_42_85067302.h5

[2/15] Run 43 (f3a2b8c1):
...

✅ Batch export complete: data/exports/batch_2025-01-08
```

### Batch Analysis

```python
from analysis.statistics import compare_runs
from analysis.plotting import plot_multiple_runs
import matplotlib.pyplot as plt

# Get all frequency scans from last week
runs = list(db.search(plan_name='frequency_scan',
                      since='2025-01-08'))

# Statistical comparison
comparison = compare_runs(runs, 'power')
print("\nStatistical Comparison:")
print(comparison[['scan_id', 'mean', 'std', 'min', 'max']])

# Visual comparison
plot_multiple_runs(runs, 'frequency', 'power',
                   title='All Frequency Scans - Last Week',
                   save_path='data/exports/weekly_comparison.png')

# Trend analysis
comparison['date'] = pd.to_datetime(comparison['time'], unit='s')
plt.figure(figsize=(12, 6))
plt.plot(comparison['date'], comparison['mean'], 'o-')
plt.xlabel('Date')
plt.ylabel('Mean Power (dBm)')
plt.title('Power Trend Over Time')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('data/exports/power_trend.png')
```

---

## Advanced Workflows

### Workflow 1: Daily Analysis Report

```python
#!/usr/bin/env python3
"""Generate daily analysis report."""

from databroker import Broker
from analysis.statistics import analyze_run, compare_runs
from analysis.plotting import plot_multiple_runs
from analysis.export import export_for_analysis
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Setup
db = Broker.named('ejfat_gnuradio')
today = datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

# Get today's runs
runs = list(db.search(since=yesterday, until=today))

print(f"Daily Report for {today}")
print(f"Total runs: {len(runs)}")

# Analyze each run
for run in runs:
    start = run.metadata['start']
    print(f"\nRun {start['scan_id']} - {start['plan_name']}")
    print(f"  Operator: {start.get('operator', 'N/A')}")
    print(f"  Purpose: {start.get('purpose', 'N/A')}")

    # Get numeric columns
    table = run.table()
    numeric_cols = table.select_dtypes(include=['number']).columns[:2]

    if len(numeric_cols) >= 2:
        stats = analyze_run(run, numeric_cols[1])
        print(f"  {numeric_cols[1]}: "
              f"mean={stats['mean']:.2f}, "
              f"std={stats['std']:.2f}")

# Export all runs
batch_export(runs, f'data/exports/daily_{today}', formats=['csv', 'excel'])

# Create comparison plot if multiple frequency scans
freq_scans = [r for r in runs
              if r.metadata['start']['plan_name'] == 'frequency_scan']
if len(freq_scans) > 1:
    plot_multiple_runs(freq_scans, 'frequency', 'power',
                       title=f'Frequency Scans - {today}',
                       save_path=f'data/exports/freq_comparison_{today}.png')

print(f"\n✅ Daily report complete!")
```

### Workflow 2: Automated Quality Check

```python
#!/usr/bin/env python3
"""Check data quality for recent runs."""

from databroker import Broker
from analysis.statistics import detect_outliers, compute_snr

db = Broker.named('ejfat_gnuradio')

# Check last 5 runs
recent_runs = list(db.v1())[-5:]

print("Data Quality Report")
print("=" * 70)

for run in recent_runs:
    start = run.metadata['start']
    table = run.table()

    print(f"\nRun {start['scan_id']} - {start['plan_name']}")

    # Check for outliers
    numeric_cols = table.select_dtypes(include=['number']).columns
    for col in numeric_cols[:2]:  # Check first 2 numeric columns
        outliers = detect_outliers(run, col, method='iqr', threshold=1.5)

        if outliers['num_outliers'] > 0:
            print(f"  ⚠️  {col}: {outliers['num_outliers']} outliers "
                  f"({outliers['outlier_fraction']*100:.1f}%)")
        else:
            print(f"  ✅ {col}: No outliers detected")

    # Check SNR if applicable
    if 'detector_signal' in table.columns:
        snr = compute_snr(run, 'detector_signal')
        if snr['snr_db'] < 10:
            print(f"  ⚠️  Low SNR: {snr['snr_db']:.1f} dB")
        else:
            print(f"  ✅ SNR: {snr['snr_db']:.1f} dB")

print("\n" + "=" * 70)
```

### Workflow 3: Interactive Analysis Session

```python
#!/usr/bin/env python3
"""Interactive analysis of experiment data."""

from databroker import Broker
from analysis.statistics import *
from analysis.plotting import *
from analysis.export import *
import matplotlib.pyplot as plt
import numpy as np

# Setup
db = Broker.named('ejfat_gnuradio')
plt.ion()  # Interactive mode

# Helper function to analyze any run
def analyze_and_plot(run_id):
    """Analyze and plot a run."""
    if isinstance(run_id, int):
        run = db[run_id]
    else:
        run = db[run_id]

    # Show metadata
    start = run.metadata['start']
    print(f"\nRun {start['scan_id']} - {start['plan_name']}")
    print(f"UID: {start['uid']}")
    print(f"Purpose: {start.get('purpose', 'N/A')}")

    # Get data
    table = run.table()
    print(f"Data shape: {table.shape}")
    print(f"Columns: {list(table.columns)}")

    # Plot
    numeric_cols = table.select_dtypes(include=['number']).columns.tolist()
    if len(numeric_cols) >= 2:
        plot_run(run, numeric_cols[0], numeric_cols[1])
        plt.show()

    # Statistics
    if len(numeric_cols) >= 2:
        stats = analyze_run(run, numeric_cols[1])
        print(f"\nStatistics for {numeric_cols[1]}:")
        for key, value in stats.items():
            print(f"  {key}: {value:.4f}")

    return run

# Example usage
print("Interactive Analysis Session")
print("Commands:")
print("  analyze_and_plot(-1)  - Analyze latest run")
print("  analyze_and_plot(42)  - Analyze run by index")
print("  analyze_and_plot('85067302')  - Analyze by UID")
print("\nReady for analysis!")
```

---

## Best Practices

### 1. Always Check Data After Experiments

```python
# After running an experiment, verify data was saved
from databroker import Broker
db = Broker.named('ejfat_gnuradio')

run = db[-1]
print(f"Latest run: {run.metadata['start']['plan_name']}")
print(f"Data points: {len(run.table())}")
```

### 2. Use Meaningful Metadata

When running experiments, provide detailed metadata:

```python
from bluesky_config.metadata import create_experiment_metadata

md = create_experiment_metadata(
    experiment_id='EXP-2025-042',
    purpose='Characterize frequency response under varying temperature',
    operator='alice',
    temperature=22.5,
    humidity=45,
    notes='First run after calibration'
)
```

### 3. Regular Backups

```bash
# Backup data directory
tar -czf ejfat_data_backup_$(date +%Y%m%d).tar.gz data/

# Backup to remote location
rsync -avz data/ user@backup-server:/backups/ejfat/
```

### 4. Export Critical Data

Don't rely solely on DataBroker - export important runs:

```python
from analysis.export import export_for_analysis

# Export critical runs in multiple formats
critical_run = db['85067302']
export_for_analysis(critical_run,
                    'data/exports/critical/EXP-2025-042',
                    formats=['csv', 'hdf5', 'excel', 'json'])
```

### 5. Document Analysis Scripts

Save your analysis scripts with comments:

```python
#!/usr/bin/env python3
"""
Analysis: FM Station Stability Study
Date: 2025-01-08
Operator: Alice
Purpose: Analyze stability of CHEZ 106.1 FM over 24 hours
"""

from databroker import Broker
from analysis.statistics import analyze_run
import matplotlib.pyplot as plt

# Load specific experiment
db = Broker.named('ejfat_gnuradio')
run = db['85067302-b45c-4a1e-8f6d-2c3e9a4b1d7e']

# Analysis code...
```

### 6. Use Version Control for Analysis

```bash
# Initialize git in analysis directory
cd data/exports
git init
git add *.py *.md
git commit -m "Initial analysis scripts"
```

---

## Troubleshooting

### Problem: "Catalog not found"

```python
from databroker import Broker
db = Broker.named('ejfat_gnuradio')
# KeyError: 'ejfat_gnuradio'
```

**Solution:**
```bash
# Initialize catalog
python init_databroker.py

# Or use temporary catalog
db = Broker.named('temp')
```

### Problem: "No runs found"

```python
runs = list(db.search(since='2025-01-08'))
print(len(runs))  # 0
```

**Solution:**
- Check if experiments were run with DataBroker subscription
- Verify data directory: `ls data/documents/`
- Check catalog directory: `ls data/catalog/`
- Try listing all runs: `list(db.v1())`

### Problem: "Column not found"

```python
table = run.table()
power = table['power']
# KeyError: 'power'
```

**Solution:**
```python
# Check available columns
print(table.columns.tolist())

# Use correct column name
# Column names come from device signals
```

### Problem: "Out of memory"

When processing many large runs:

**Solution:**
```python
# Process in chunks
runs = list(db.search(since='2025-01-01'))

for run in runs:
    # Process one at a time
    table = run.table()
    # ... analysis ...
    del table  # Free memory
```

### Problem: "Plot doesn't show"

```python
plot_run(run, 'frequency', 'power')
# Nothing appears
```

**Solution:**
```python
import matplotlib.pyplot as plt

plot_run(run, 'frequency', 'power')
plt.show()  # Must call show() for interactive plots

# Or save to file
plot_run(run, 'frequency', 'power',
         save_path='data/plot.png')
```

---

## Summary

### Quick Reference Card

```python
# Import everything
from databroker import Broker
from analysis.statistics import *
from analysis.plotting import *
from analysis.export import *
import matplotlib.pyplot as plt

# Load catalog
db = Broker.named('ejfat_gnuradio')

# Get data
run = db[-1]              # Latest
table = run.table()       # As DataFrame

# Analyze
stats = analyze_run(run, 'power')
peaks = find_peaks(run, 'frequency', 'power', prominence=5)

# Visualize
plot_run(run, 'frequency', 'power')
plt.show()

# Export
export_to_csv(run, 'data/results.csv')
export_to_hdf5(run, 'data/results.h5')
```

### Key Commands

```bash
# List runs
python retrieve_data.py --list

# View latest
python retrieve_data.py --latest --all

# View specific run
python retrieve_data.py --uid 85067302 --all

# Interactive Python
python -c "from databroker import Broker; db=Broker.named('ejfat_gnuradio'); print(len(list(db.v1())))"
```

---

## Additional Resources

### Related Documentation

- **README.md** - Framework overview
- **PHASE2_README.md** - Data persistence details
- **PHASE4_IMPLEMENTATION.md** - Analysis tools implementation

### External Resources

- [DataBroker Documentation](https://blueskyproject.io/databroker/)
- [Pandas Documentation](https://pandas.pydata.org/)
- [Matplotlib Gallery](https://matplotlib.org/stable/gallery/)
- [SciPy Stats](https://docs.scipy.org/doc/scipy/reference/stats.html)

---

**Document End** - Version 1.0 - 2025-10-18
