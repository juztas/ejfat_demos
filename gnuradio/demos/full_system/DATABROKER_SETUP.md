# DataBroker Setup Complete

**Date:** 2025-10-08
**Version:** DataBroker v1.2.5
**Status:** ✅ Installed and tested

## Installation Summary

DataBroker and all dependencies have been successfully installed:

```bash
pip install databroker
```

### Installed Packages
- **databroker** (1.2.5) - Main package
- **bluesky-live** (0.0.8) - Live data streaming
- **pymongo** (4.15.3) - MongoDB backend support
- **dask** (2025.9.1) - Parallel computing
- **xarray** (2025.10.1) - Multi-dimensional arrays
- **intake** (0.6.4) - Data cataloging
- **suitcase-mongo** (0.7.0) - MongoDB export
- Plus many other dependencies

## Basic Usage

### 1. Create a DataBroker Catalog

```python
from databroker import Broker

# Temporary in-memory catalog (lost on restart)
db = Broker.named('temp')
```

### 2. Subscribe RunEngine to DataBroker

```python
from bluesky import RunEngine

RE = RunEngine({})
RE.subscribe(db.insert)  # ← This stores all documents automatically!
```

### 3. Run Scans (Data Automatically Stored)

```python
from bluesky_config.plans import frequency_scan
from bluesky_config.devices import GNURadioSignalGenerator, PowerMeter

sig_gen = GNURadioSignalGenerator('', name='sig_gen', host='localhost', port=8080)
detector = PowerMeter(name='power')

# Run scan - data automatically saved to DataBroker
uid = RE(frequency_scan([detector], sig_gen, 88e6, 108e6, 50))
```

### 4. Retrieve Data

```python
# By UID
header = db[uid[0]]
start_doc = header.start
table = db.get_table(header)

# By search
results = db(plan_name='frequency_scan')
results = db(experiment_id='EXP-2025-001')
results = db(operator='alice', since='2025-01-01')

# Get most recent
header = db[-1]
```

### 5. Analyze Data

```python
import matplotlib.pyplot as plt

# Get data as Pandas DataFrame
table = db.get_table(header)

# Statistics
print(table.describe())

# Plot
table.plot(x='sig_gen_frequency', y='power_meter_power')
plt.show()
```

## DataBroker API (v1.2.5)

### Accessing Metadata

```python
header = db[uid]
start_doc = header.start       # Start document
stop_doc = header.stop         # Stop document
descriptors = header.descriptors  # Descriptor documents

# Metadata fields
print(start_doc['uid'])
print(start_doc['plan_name'])
print(start_doc['experiment_id'])
print(start_doc['operator'])
```

### Getting Data Tables

```python
# Primary data stream
table = db.get_table(header)

# Specific stream
table = db.get_table(header, stream_name='primary')

# All data (including configuration)
events = list(header.events())
```

### Search Queries

```python
# By plan name
results = db(plan_name='frequency_scan')

# By metadata field
results = db(experiment_id='EXP-001')
results = db(operator='alice')
results = db(purpose='FM station scan')

# By date range
results = db(since='2025-01-01')
results = db(since='2025-01-01', until='2025-01-31')

# Combined criteria
results = db(plan_name='frequency_scan', operator='alice', since='today')
```

## Storage Backends

### 1. Temporary (In-Memory)

```python
db = Broker.named('temp')
# Data lost when Python session ends
# Good for: Testing, development
```

### 2. SQLite (Persistent, Single-User)

```python
from databroker import Broker

config = {
    'description': 'EJFAT GNU Radio Experiments',
    'metadatastore': {
        'module': 'databroker.headersource.sqlite',
        'class': 'MDS',
        'config': {
            'directory': 'data/databroker',
            'timezone': 'US/Eastern',
        }
    },
    'assets': {
        'module': 'databroker.assets.sqlite',
        'class': 'Registry',
        'config': {
            'dbpath': 'data/databroker/assets.db'
        }
    }
}

db = Broker.from_config(config)
# Data persists across sessions
# Good for: Single-user workstations, long-term storage
```

### 3. MongoDB (Production, Multi-User)

```python
# Requires MongoDB server running
config = {
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
}

db = Broker.from_config(config)
# Good for: Multi-user facilities, production environments
```

## Integration with Experiments

All experiment scripts should now include DataBroker:

```python
#!/usr/bin/env python3
from databroker import Broker
from bluesky import RunEngine
from bluesky_config.plans import frequency_scan
# ... other imports ...

# Setup DataBroker
db = Broker.named('temp')  # or use SQLite/MongoDB config

# Setup RunEngine with DataBroker
RE = RunEngine({})
RE.subscribe(db.insert)  # ← KEY: This enables automatic storage

# Run experiments
# ... your experiment code ...

# Later: retrieve and analyze
header = db[-1]
table = db.get_table(header)
```

## Testing DataBroker

Test script included:

```bash
# Run test to verify DataBroker is working
python << 'TESTEOF'
from databroker import Broker
from bluesky import RunEngine
from bluesky_config.devices import MockDetector
from bluesky_config.plans import frequency_scan
from bluesky_config.metadata import create_experiment_metadata

class MockSignalGenerator:
    def __init__(self, name):
        from ophyd import Signal
        self.name = name
        self.frequency = Signal(name=f'{name}_frequency', value=98.5e6)

db = Broker.named('temp')
RE = RunEngine({})
RE.subscribe(db.insert)

sig_gen = MockSignalGenerator('sig_gen')
detector = MockDetector(name='det', noise_level=0.1)

md = create_experiment_metadata(
    experiment_id='TEST-001',
    purpose='DataBroker test',
    plan_type='frequency_scan',
)

uid = RE(frequency_scan([detector], sig_gen, 88e6, 92e6, 5), **md)
header = db[uid[0]]
table = db.get_table(header)

print(f"✅ DataBroker test successful!")
print(f"   Stored run: {header.start['uid'][:8]}")
print(f"   Data points: {len(table)}")
print(f"   Columns: {list(table.columns)}")
TESTEOF
```

## Common Patterns

### Export to CSV

```python
header = db[-1]
table = db.get_table(header)
table.to_csv('scan_data.csv')
```

### Export to HDF5

```python
table.to_hdf('scan_data.h5', 'data')
```

### Compare Multiple Runs

```python
import matplotlib.pyplot as plt

runs = db(plan_name='frequency_scan', since='today')

for header in runs:
    table = db.get_table(header)
    label = f"Run {header.start['scan_id']}"
    plt.plot(table.index, table['power'], label=label)

plt.legend()
plt.show()
```

## Next Steps

1. **Update experiment scripts** to use DataBroker (add `db.insert` subscription)
2. **Choose storage backend** (temp for testing, SQLite for persistence)
3. **Create analysis notebooks** that leverage DataBroker search capabilities
4. **Setup SQLite persistent storage** for long-term data retention

## Documentation

- **DataBroker Docs:** https://blueskyproject.io/databroker/
- **Bluesky Project:** https://blueskyproject.io/
- **Tutorial:** https://nsls-ii.github.io/bluesky/tutorial.html

---

**Status:** ✅ Ready for production use
**Tested:** 2025-10-08
**Test UID:** 462c572e
