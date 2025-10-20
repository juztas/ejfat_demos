# DataBroker Connection Issue - SOLVED ✅

## The Problem You Encountered

When you tried:
```python
db = Broker.named('ejfat_gnuradio')
```

You got:
```
⚠️  Using temporary catalog (data will not persist)
```

## Why This Happened

1. **No catalog exists** - The named catalog `'ejfat_gnuradio'` was never created
2. **Experiments don't subscribe to DataBroker** - They only save JSON documents
3. **Catalog directory is empty** - No `.msgpack` files were created

## Your Data IS Safe! ✅

Your experiment data was saved to:
- **Location:** `data/documents/*.jsonl`
- **Format:** JSON Lines (one document per line)
- **Accessible:** Yes! (See solutions below)

You have **25+ saved runs** in `data/documents/`!

---

## 🚀 Three Ways to Access Your Data

### Option 1: Use the Quick Access Script (Easiest!)

```bash
# Access your latest experiment data
python access_my_data.py
```

**What it does:**
- ✅ Loads data from JSON documents
- ✅ Shows metadata (UID, plan name, operator, etc.)
- ✅ Displays data table
- ✅ Calculates statistics
- ✅ Saves to CSV

**Output:**
```
📋 METADATA:
   UID: f74c7c44...
   Plan: frequency_scan
   Scan ID: 1
   Events: 10

📊 DATA TABLE:
   seq_num  time         det_value
   1        1.759970e+09  0.822754
   2        1.759970e+09  0.963739
   ...

💾 Saved to: data/exports/f74c7c44_data.csv
```

### Option 2: Use the Helper Functions (Programmatic Access)

```python
from setup_databroker_helper import load_from_documents
import pandas as pd

# Load latest run
run_data = load_from_documents()

# Extract data
events = run_data['events']
data = [event['data'] for event in events]
df = pd.DataFrame(data)

print(df)
```

**Load specific run by UID:**
```python
# Load specific run
run_data = load_from_documents(uid_prefix='f74c7c44')

# Access metadata
print(run_data['start']['plan_name'])
print(run_data['start']['experiment_id'])

# Access data
for event in run_data['events']:
    print(event['data'])
```

### Option 3: Manual JSON Parsing

```python
import json
from pathlib import Path

# Find latest run
doc_dir = Path('data/documents')
latest = sorted(doc_dir.glob('*_documents.jsonl'))[-1]

# Read documents
with open(latest, 'r') as f:
    for line in f:
        doc = json.loads(line)
        if 'event' in doc:
            print(doc['event']['data'])
```

---

## 🔧 Fix for Future Experiments

To make DataBroker work properly, update your experiments to use the helper:

### Updated Experiment Template

```python
#!/usr/bin/env python3
from bluesky_config.run_engine_setup import create_headless_run_engine
from setup_databroker_helper import get_databroker_with_persistence
from bluesky_config.callbacks import DocumentLogger
# ... other imports ...


def main():
    # Create RunEngine
    RE, bec = create_headless_run_engine()
    RE.subscribe(bec)

    # Set up DataBroker with persistence
    db, serializer = get_databroker_with_persistence()

    # Subscribe to RunEngine
    RE.subscribe(db.v1.insert)  # In-memory retrieval
    if serializer:
        RE.subscribe(serializer)  # Persistent storage to catalog/

    # Also save documents as backup
    doc_logger = DocumentLogger('data/documents')
    RE.subscribe(doc_logger)

    # ... your devices and plans ...

    # Run experiment
    uid = RE(your_plan, **metadata)

    # Now you can retrieve immediately!
    run = db[-1]
    table = run.table()
    print(table)

    return 0
```

### What This Does

1. **In-session retrieval** - `db.v1.insert` allows `db[-1]` to work
2. **Persistent catalog** - `serializer` saves to `data/catalog/*.msgpack`
3. **Document backup** - `DocumentLogger` still saves JSON files
4. **Cross-session access** - Future runs can load from catalog

---

## 📊 Complete Working Example

Here's a complete working example using your mock experiment:

```python
#!/usr/bin/env python3
"""
Fixed Mock Experiment with DataBroker
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bluesky_config.run_engine_setup import create_headless_run_engine
from setup_databroker_helper import get_databroker_with_persistence
from ophyd import Signal
from bluesky.plans import scan
from bluesky_config.devices import MockDetector
from bluesky_config.callbacks import (PeakDetectorCallback, StatisticsCallback,
                                      ProgressCallback, DocumentLogger)
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run mock experiment with DataBroker."""

    # Create RunEngine
    RE, bec = create_headless_run_engine()
    RE.subscribe(bec)

    # Set up DataBroker with persistence
    db, serializer = get_databroker_with_persistence()

    # Subscribe to RunEngine
    RE.subscribe(db.v1.insert)  # For in-session retrieval
    if serializer:
        RE.subscribe(serializer)  # For persistent catalog

    # Callbacks
    peak_detector = PeakDetectorCallback('det_value', threshold=1.2)
    RE.subscribe(peak_detector)

    stats = StatisticsCallback(['det_value'])
    RE.subscribe(stats)

    progress = ProgressCallback()
    RE.subscribe(progress)

    doc_logger = DocumentLogger('data/documents')
    RE.subscribe(doc_logger)

    # Create mock devices
    motor = Signal(name='motor', value=0)
    detector = MockDetector(name='det', noise_level=0.15)

    # Scan parameters
    start = 0
    stop = 10
    num_points = 20

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='MOCK-FIXED-001',
        purpose='Test DataBroker integration',
        plan_type='scan',
        start=start,
        stop=stop,
        num_points=num_points,
    )

    print("\n" + "="*70)
    print("MOCK EXPERIMENT WITH DATABROKER")
    print("="*70)
    print(f"Experiment ID: {md['experiment_id']}")
    print(f"Operator: {md['operator']}")
    print(f"\nMotor range: {start} - {stop}")
    print(f"Number of points: {num_points}")
    print("="*70 + "\n")

    # Run the scan
    uid = RE(scan([detector], motor, start, stop, num_points), **md)

    print("\n" + "="*70)
    print("EXPERIMENT COMPLETE")
    print("="*70)
    print(f"Run UID: {uid[0][:8]}")

    # Retrieve immediately
    print("\nRetrieving data from DataBroker...")
    run = db[-1]
    table = run.table()

    print("\nData Table:")
    print(table)

    print("\nStatistics:")
    print(table.describe())

    print("\n✅ Data saved to:")
    print(f"   - Catalog: data/catalog/{uid[0][:8]}.msgpack")
    print(f"   - Documents: data/documents/{uid[0][:8]}_documents.jsonl")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Save this as:** `experiments/mock_experiment_fixed.py`

**Run it:**
```bash
python experiments/mock_experiment_fixed.py
```

---

## 🎯 Verification Steps

After running the fixed experiment:

### 1. Check Catalog Files

```bash
ls -lh data/catalog/
# Should show *.msgpack files
```

### 2. Access via Helper

```python
from setup_databroker_helper import load_data_from_catalog

cat = load_data_from_catalog()
if cat:
    runs = list(cat)
    print(f"Total runs: {len(runs)}")
```

### 3. Check Status

```bash
python setup_databroker_helper.py
```

Expected output:
```
✅ DataBroker ready with persistent storage
✅ Found X catalog files
📊 Total runs: X
```

---

## 📚 Summary

| Method | Where Data Lives | Accessible Across Sessions? |
|--------|------------------|----------------------------|
| **Current** (broken) | `data/documents/*.jsonl` | ❌ No (must parse JSON) |
| **Fixed** | `data/catalog/*.msgpack` | ✅ Yes (via DataBroker) |
| **Both** | Both locations | ✅ Yes (belt and suspenders!) |

### Quick Commands

```bash
# Access your existing data
python access_my_data.py

# Check DataBroker status
python setup_databroker_helper.py

# Run a fixed experiment
python experiments/mock_experiment_fixed.py

# Verify catalog was created
ls data/catalog/
```

---

## 🐛 Troubleshooting

### "No catalog files found"

**Problem:** No `.msgpack` files in `data/catalog/`

**Solution:** Run a fixed experiment (with `serializer` subscription)

### "suitcase-msgpack not available"

**Problem:** Package not installed

**Solution:**
```bash
conda activate gnuradio
pip install suitcase-msgpack
```

### "I want to use named catalog 'ejfat_gnuradio'"

**Problem:** Named catalogs require configuration

**Solution:** For now, use `Broker.named('temp')` with `serializer` for persistence. Named catalogs require additional setup.

---

## 🎉 Next Steps

1. **Access your existing data**: `python access_my_data.py`
2. **Install suitcase-msgpack**: `pip install suitcase-msgpack`
3. **Update experiments**: Use the template above
4. **Run new experiments**: Data will be saved to catalog
5. **Verify**: Check `data/catalog/` for `.msgpack` files

Your data is safe and accessible! 🚀
