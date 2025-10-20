# Phase 2: Persistent Data Storage with DataBroker

## Overview

Phase 2 adds persistent data storage to the Bluesky framework. All experiment data and metadata are now automatically saved to disk and can be retrieved after the program exits.

## What's New in Phase 2

### 1. Persistent Document Storage

- **Documents saved to disk**: All Bluesky documents (start, descriptor, event, stop) are saved as JSON Lines files
- **Location**: `data/documents/` directory
- **Format**: One `.jsonl` file per run, named by UID (e.g., `85067302_documents.jsonl`)
- **Persistence**: Data survives program restarts

### 2. Configuration Updates

**Default catalog changed to 'sqlite'** (persistent storage):

```python
# config.py
DEFAULT_CATALOG = 'sqlite'  # Changed from 'temp'
```

**Document logging enabled by default**:

```python
# config.py
ENABLE_DOCUMENT_LOGGER = True
```

### 3. New Tools

#### Data Retrieval Script

**`retrieve_data.py`** - Command-line tool to access saved data:

```bash
# List all saved runs
python retrieve_data.py --list

# Show latest run (summary only)
python retrieve_data.py --latest

# Show latest run with data table
python retrieve_data.py --latest --table

# Show latest run with statistics
python retrieve_data.py --latest --stats

# Show everything
python retrieve_data.py --latest --all

# Show specific run by UID
python retrieve_data.py --uid 85067302

# Show data table with custom row limit
python retrieve_data.py --latest --table --max-rows 50
```

#### DataBroker Initialization

**`init_databroker.py`** - Initialize and manage catalog:

```bash
# Initialize catalog
python init_databroker.py

# Show catalog statistics
python init_databroker.py --stats

# Setup suitcase serializer (if available)
python init_databroker.py --setup-serializer
```

## How It Works

### Document Flow

```
┌──────────────┐
│  Experiment  │
│   (Run)      │
└──────┬───────┘
       │
       ▼
┌────────────────────┐
│   RunEngine        │
│  (emits documents) │
└────────┬───────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌──────────────────┐
│  DocumentLogger │  │  DataBroker      │
│  (saves to disk)│  │ (in-memory temp) │
└─────────┬───────┘  └──────────────────┘
          │
          ▼
┌──────────────────────────┐
│  data/documents/         │
│  ├── <uid>_documents.jsonl │
│  ├── <uid>_documents.jsonl │
│  └── ...                 │
└──────────────────────────┘
```

### Document Storage Format

Each run creates one `.jsonl` file containing all documents:

```jsonl
{"start": {...}}
{"descriptor": {...}}
{"event": {...}}
{"event": {...}}
...
{"stop": {...}}
```

## Viewing Saved Data

### Method 1: retrieve_data.py (Recommended)

```bash
# Quick view of latest run
python retrieve_data.py --latest

# Output:
# ======================================================================
# RUN SUMMARY
# ======================================================================
#
# UID: 85067302-191f-4d95-ab5f-8339edd5930c
# Scan ID: 1
# Plan: scan
# Operator: yak
# Purpose: Test Bluesky framework with mock devices
# Time: 1759967072.793602
#
# Metadata:
#   experiment_id: MOCK-001
#   facility: EJFAT
#   beamline: gnuradio_testbed
#
# Events collected: 20
# Exit status: success
# ======================================================================
```

### Method 2: Direct JSON Loading

```python
import json
from pathlib import Path

# Load latest document file
doc_files = sorted(Path('data/documents').glob('*.jsonl'))
latest = doc_files[-1]

# Read all documents
documents = []
with open(latest, 'r') as f:
    for line in f:
        documents.append(json.loads(line))

# Access start document
start = documents[0]['start']
print(f"Experiment: {start['experiment_id']}")
print(f"Purpose: {start['purpose']}")

# Access events
events = [d['event'] for d in documents if 'event' in d]
print(f"Collected {len(events)} data points")
```

### Method 3: Analysis with Pandas

```python
import json
import pandas as pd
from pathlib import Path

# Load documents
doc_file = Path('data/documents/85067302_documents.jsonl')

events = []
with open(doc_file, 'r') as f:
    for line in f:
        doc = json.loads(line)
        if 'event' in doc:
            events.append(doc['event'])

# Create DataFrame
data_rows = []
for event in events:
    row = {'seq_num': event['seq_num'], 'time': event['time']}
    row.update(event['data'])
    data_rows.append(row)

df = pd.DataFrame(data_rows)

# Analyze
print(df.describe())
print(df.head())

# Plot
import matplotlib.pyplot as plt
df.plot(x='motor', y='det_value')
plt.show()
```

## Experiment Examples

### Run Experiment with Persistence

```bash
# Run an experiment - data is automatically saved
python run_experiment.py mock_experiment

# View saved data
python retrieve_data.py --latest --all
```

### Programmatic Access

```python
from pathlib import Path
import json

def load_run(uid_prefix):
    """Load run by UID prefix."""
    doc_dir = Path('data/documents')
    matches = list(doc_dir.glob(f'{uid_prefix}*_documents.jsonl'))

    if not matches:
        print(f"No run found with UID: {uid_prefix}")
        return None

    # Load all documents
    docs = {'start': [], 'descriptor': [], 'event': [], 'stop': []}

    with open(matches[0], 'r') as f:
        for line in f:
            doc_dict = json.loads(line)
            for name, doc in doc_dict.items():
                docs[name].append(doc)

    return docs

# Use it
run = load_run('85067302')
start = run['start'][0]
print(f"Plan: {start['plan_name']}")
print(f"Events: {len(run['event'])}")
```

## Data Organization

### Directory Structure

```
data/
├── documents/          # Persisted Bluesky documents
│   ├── 85067302_documents.jsonl
│   ├── a1b2c3d4_documents.jsonl
│   └── ...
├── catalog/            # Catalog directory (for future use)
├── exports/            # Exported data (CSV, HDF5, etc.)
└── logs/              # Log files
```

### Document Lifecycle

1. **Start Document**: Created when experiment begins
   - Contains all metadata (operator, purpose, plan args, etc.)
   - Saved immediately to disk

2. **Descriptor Documents**: Created for each data stream
   - Describes data structure (keys, types, units)
   - Saved when first detector is read

3. **Event Documents**: Created for each data point
   - Contains actual measurements
   - Saved in real-time

4. **Stop Document**: Created when experiment completes
   - Exit status, number of events, summary stats
   - Saved at experiment end

## Comparing Runs

### Find Related Experiments

```bash
# List all runs
python retrieve_data.py --list

# Output:
# ======================================================================
# SAVED RUNS
# ======================================================================
# [  1] 85067302 | scan                 | yak        | 85067302_documents.jsonl
# [  2] a1b2c3d4 | frequency_scan       | alice      | a1b2c3d4_documents.jsonl
# ======================================================================
```

### Compare Multiple Runs

```python
import json
import matplotlib.pyplot as plt
from pathlib import Path

# Load multiple runs
doc_dir = Path('data/documents')
runs = []

for doc_file in sorted(doc_dir.glob('*.jsonl'))[-3:]:  # Last 3 runs
    with open(doc_file, 'r') as f:
        docs = [json.loads(line) for line in f]
        runs.append(docs)

# Plot comparison
fig, ax = plt.subplots()

for docs in runs:
    start = docs[0]['start']
    events = [d['event'] for d in docs if 'event' in d]

    # Extract data
    x = [e['data']['motor'] for e in events]
    y = [e['data']['det_value'] for e in events]

    ax.plot(x, y, 'o-', label=f"Run {start['scan_id']}")

ax.legend()
ax.set_xlabel('Motor Position')
ax.set_ylabel('Detector Value')
ax.set_title('Run Comparison')
plt.show()
```

## Troubleshooting

### No Documents Found

```
No saved runs found in: data/documents
```

**Solution**: Run an experiment first:
```bash
python run_experiment.py mock_experiment
```

### Corrupt Document File

```
Error loading <file>: JSONDecodeError
```

**Solution**: Delete corrupted file and re-run experiment:
```bash
rm data/documents/<corrupt_file>.jsonl
python run_experiment.py <experiment_name>
```

### GUI Threading Issues (macOS)

If experiments crash with matplotlib/NSWindow errors:

```python
# Disable BestEffortCallback in config.py
ENABLE_BEST_EFFORT_CALLBACK = False

# Or disable in experiment script
# Don't subscribe BestEffortCallback
```

The data will still be saved via DocumentLogger.

## Migrating from Phase 1

If you have experiments from Phase 1 (temp catalog), they were not saved to disk. To enable persistence:

1. **Update config.py** (already done in Phase 2):
   ```python
   DEFAULT_CATALOG = 'sqlite'
   ```

2. **Re-run experiments**: Previous runs won't be recovered, but new runs will be saved

3. **Verify persistence**:
   ```bash
   python run_experiment.py mock_experiment
   python retrieve_data.py --list
   ```

## Next Steps

### Phase 3 (Future): Enhanced Data Broker

- Integration with databroker v2 catalog system
- Search by metadata (operator, date, plan type)
- Automatic data indexing
- MongoDB support for multi-user

### Phase 4 (Future): High-Speed Data Integration

- Link Bluesky documents to external binary data files
- Synchronized timestamps with high-speed recorders
- Parallel data acquisition paths

## Summary

Phase 2 provides:

✅ **Persistent storage** - All data saved automatically
✅ **JSON format** - Human-readable, easy to parse
✅ **Complete metadata** - Full experiment context preserved
✅ **Retrieval tools** - Easy access to saved data
✅ **No database required** - Simple file-based storage

All experiments now automatically save data that can be retrieved and analyzed after the program exits!
