# DataBroker Connection Guide

## ❓ "What is the name of the DataBroker I can connect to?"

### Short Answer

**There is NO persistent named catalog currently working.**

The config defines `'ejfat_gnuradio'`, but it's **not accessible** via `Broker.named()`.

---

## 🔍 Current Situation

### What EXISTS

✅ **Data files:** `data/catalog/*.msgpack` (2 runs)
✅ **JSON documents:** `data/documents/*.jsonl` (28 runs)
✅ **Temp catalog:** `Broker.named('temp')` (same session only)

### What DOESN'T Work

❌ `Broker.named('ejfat_gnuradio')` → Not registered
❌ Named catalog access → Needs setup
❌ Cross-session Broker → Use helpers instead

---

## ✅ How to Access Your Data

### Method 1: Helper Function (RECOMMENDED)

```python
from setup_databroker_helper import load_data_from_catalog

# Load catalog from msgpack files
cat = load_data_from_catalog()

if cat:
    # List all runs
    runs = list(cat.items())
    print(f"Total runs: {len(runs)}")

    # Get latest run
    latest_uid, latest_run = runs[-1]

    # Access metadata
    start = latest_run.metadata['start']
    print(f"UID: {latest_uid[:8]}")
    print(f"Plan: {start['plan_name']}")
    print(f"Experiment: {start.get('experiment_id')}")

    # Get data
    # Note: The API varies by databroker version
    # Check what methods are available:
    print(dir(latest_run))
```

### Method 2: Load from JSON Documents

```python
from setup_databroker_helper import load_from_documents
import pandas as pd

# Load latest run
run_data = load_from_documents()

# Or specific run by UID
run_data = load_from_documents(uid_prefix='3812f1d8')

# Access metadata
print(run_data['start']['uid'])
print(run_data['start']['plan_name'])
print(run_data['start']['experiment_id'])

# Extract data as DataFrame
events = run_data['events']
data = [event['data'] for event in events]
df = pd.DataFrame(data)

print(df)
```

### Method 3: Quick Access Script

```bash
python access_my_data.py
```

This automatically loads and displays your latest run.

### Method 4: Same Session Only (NOT Persistent)

```python
from databroker import Broker

# This ONLY works in the same Python session as the experiment
db = Broker.named('temp')
run = db[-1]
table = run.table()
```

⚠️ **Warning:** This won't work if you restart Python!

---

## 🛠️ Why Named Catalog Doesn't Work

The issue is that `Broker.named('ejfat_gnuradio')` requires:

1. ✅ Catalog config file → Created at `~/.intake/ejfat_gnuradio.yml`
2. ❌ Intake catalog driver → May need `intake-bluesky` package
3. ❌ Proper driver registration → DataBroker v1 vs v2 compatibility

### Attempted Solution

I created `register_catalog.py` which:
- ✅ Creates `~/.intake/ejfat_gnuradio.yml`
- ✅ Configures paths to your msgpack files
- ❌ But `Broker.named('ejfat_gnuradio')` still doesn't work

**Why:** The catalog system has compatibility issues between DataBroker v1 and v2.

---

## 🎯 Recommended Approach

**Don't use named catalogs.** Instead:

### For Same-Session Retrieval

```python
# In your experiment:
env = create_experiment_environment()
RE = env['RE']
db = env['db']  # This is Broker.named('temp')

# Run experiment
uid = RE(your_plan, **metadata)

# Retrieve immediately
run = db[-1]
table = run.table()
```

### For Cross-Session Retrieval

```python
# In a new Python session:
from setup_databroker_helper import load_data_from_catalog

cat = load_data_from_catalog()
runs = list(cat.items())

# Get latest
latest_uid, latest_run = runs[-1]
print(latest_run.metadata['start'])
```

---

## 📊 Complete Working Example

```python
#!/usr/bin/env python3
"""
Example: Access experiment data across sessions
"""

from setup_databroker_helper import load_data_from_catalog, load_from_documents
import pandas as pd

print("="*70)
print("ACCESSING EXPERIMENT DATA")
print("="*70)

# Method 1: From catalog (msgpack files)
print("\n1. Loading from catalog...")
cat = load_data_from_catalog(verbose=False)

if cat:
    runs = list(cat.items())
    print(f"   ✅ Found {len(runs)} runs in catalog")

    if runs:
        latest_uid, latest_run = runs[-1]
        start = latest_run.metadata['start']
        print(f"   Latest: {latest_uid[:8]}")
        print(f"   Plan: {start['plan_name']}")
else:
    print("   ⚠️  No catalog data")

# Method 2: From JSON documents (always works)
print("\n2. Loading from documents...")
run_data = load_from_documents(verbose=False)

if run_data:
    start = run_data['start']
    print(f"   ✅ Loaded: {start['uid'][:8]}")
    print(f"   Plan: {start['plan_name']}")
    print(f"   Events: {len(run_data['events'])}")

    # Extract data
    events = run_data['events']
    data = [event['data'] for event in events]
    df = pd.DataFrame(data)

    print("\n   Data columns:", list(df.columns))
    print(f"   Data shape: {df.shape}")

    print("\n   First 5 rows:")
    print(df.head())

print("\n" + "="*70)
print("✅ COMPLETE")
print("="*70)
```

**Save as:** `example_data_access.py`

**Run:**
```bash
python example_data_access.py
```

---

## 🔧 Advanced: Try to Enable Named Catalog

If you really want `Broker.named('ejfat_gnuradio')` to work:

### Step 1: Install Required Packages

```bash
conda activate gnuradio
pip install intake-bluesky
```

### Step 2: Register Catalog

```bash
python register_catalog.py --test
```

### Step 3: Restart Python

```bash
python -c "from databroker import Broker; db = Broker.named('ejfat_gnuradio'); print('Success!')"
```

### Step 4: If It Still Doesn't Work

Use the helper functions - they're more reliable:

```python
from setup_databroker_helper import load_data_from_catalog
cat = load_data_from_catalog()
```

---

## 📋 Summary Table

| Method | Command | Works Across Sessions? | Requires |
|--------|---------|----------------------|----------|
| **Temp Broker** | `Broker.named('temp')` | ❌ No | Nothing (built-in) |
| **Named Catalog** | `Broker.named('ejfat_gnuradio')` | ⚠️ Should, doesn't | Registration + packages |
| **Catalog Helper** | `load_data_from_catalog()` | ✅ Yes | suitcase-msgpack |
| **Documents Helper** | `load_from_documents()` | ✅ Yes | Nothing (built-in) |
| **Quick Script** | `python access_my_data.py` | ✅ Yes | Nothing (built-in) |

---

## 🎯 Bottom Line

### Question: "What DataBroker can I connect to?"

### Answer:

**There is no named DataBroker to connect to.**

Instead, use:

```python
# Option 1 (recommended)
from setup_databroker_helper import load_data_from_catalog
cat = load_data_from_catalog()

# Option 2 (always works)
from setup_databroker_helper import load_from_documents
run_data = load_from_documents()

# Option 3 (CLI)
python access_my_data.py
```

**These directly load your data from the saved files and work reliably across sessions.**

---

## 📖 Related Documentation

- **Quick Access:** `python access_my_data.py`
- **Helper Functions:** `setup_databroker_helper.py`
- **Quick Reference:** `DATABROKER_QUICK_REFERENCE.md`
- **Full Guide:** `DATABROKER_FIX_GUIDE.md`

---

**Last Updated:** 2025-10-19
**Status:** Use helper functions (recommended)
