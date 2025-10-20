# DataBroker Quick Start Guide ✅

## TL;DR - Just Show Me My Data!

```bash
# Access your latest experiment data
python access_my_data.py
```

**That's it!** Your data is displayed and saved to CSV.

---

## What Happened (The Full Story)

### The Problem
When you ran:
```bash
python run_experiment.py mock_experiment
```

The data was saved to **JSON documents only**, not to a DataBroker catalog. That's why:
```python
db = Broker.named('ejfat_gnuradio')  # ❌ Catalog doesn't exist
```

Didn't work.

### The Solution
Your data IS safe in `data/documents/`. I've created tools to access it easily.

---

## 🚀 Three Quick Solutions

### Solution 1: Use the Access Script (Easiest!)

```bash
python access_my_data.py
```

**Output:**
```
📂 Loading: 020e19e5_documents.jsonl
✅ Loaded run: 020e19e5

📋 METADATA:
   UID: 020e19e5-5e6b-43bd-b216-8aca90297ba7
   Plan: scan
   Experiment ID: MOCK-DB-001

📊 DATA: 20 data points

   seq_num  time         det_value  motor
   1        ...          1.158894   0.000000
   2        ...          1.133830   0.526316
   ...

💾 Saved to: data/exports/020e19e5_data.csv
```

### Solution 2: Load from Documents in Python

```python
from setup_databroker_helper import load_from_documents
import pandas as pd

# Load latest run
run_data = load_from_documents()

# Extract metadata
print(run_data['start']['uid'])
print(run_data['start']['plan_name'])
print(run_data['start']['experiment_id'])

# Extract data
events = run_data['events']
data = [event['data'] for event in events]
df = pd.DataFrame(data)

print(df)
```

### Solution 3: Run Fixed Experiment (For Future Runs)

```bash
# This creates a proper DataBroker catalog
python experiments/mock_experiment_with_databroker.py
```

After this runs, your data will be in **BOTH**:
- ✅ `data/catalog/*.msgpack` (DataBroker catalog)
- ✅ `data/documents/*.jsonl` (JSON backup)

---

## 🎯 How to Access Data from Catalog

After running the **fixed** experiment:

```python
from setup_databroker_helper import load_data_from_catalog

# Load catalog
cat = load_data_from_catalog()

# Get all runs
runs = list(cat.items())
print(f"Total runs: {len(runs)}")

# Get latest run
latest_uid, latest_run = runs[-1]
print(f"UID: {latest_uid}")

# Access metadata
print(latest_run.metadata['start']['plan_name'])
print(latest_run.metadata['start']['experiment_id'])

# Get data as DataFrame
# (API may vary - check catalog type)
```

**Or use the simple approach:**

```python
from setup_databroker_helper import load_from_documents

# Works regardless of catalog!
run_data = load_from_documents()  # Latest
table = pd.DataFrame([e['data'] for e in run_data['events']])
print(table)
```

---

## 📊 Verify Everything Works

### Step 1: Check Your Existing Data

```bash
# See all your past experiments
ls -lh data/documents/

# Access latest
python access_my_data.py
```

### Step 2: Run Fixed Experiment

```bash
# Run new experiment with catalog
python experiments/mock_experiment_with_databroker.py

# Check catalog was created
ls -lh data/catalog/
# Should show: *.msgpack files
```

### Step 3: Check Status

```bash
python setup_databroker_helper.py
```

**Expected output:**
```
✅ DataBroker ready with persistent storage
✅ Found X catalog files
📊 Total runs: X
✅ Loaded run: 020e19e5
   Plan: scan
   Events: 20
```

---

## 🔧 What the Fix Does

The original `mock_experiment.py`:
```python
RE = RunEngine({})
RE.subscribe(bec)
RE.subscribe(doc_logger)  # Only saves JSON
# ❌ Missing: DataBroker subscription!
```

The fixed `mock_experiment_with_databroker.py`:
```python
RE = RunEngine({})
RE.subscribe(bec)

db, serializer = get_databroker_with_persistence()  # ← NEW
RE.subscribe(db.v1.insert)     # ← In-memory retrieval
RE.subscribe(serializer)        # ← Persistent catalog
RE.subscribe(doc_logger)        # ← JSON backup
```

**Now data is saved to BOTH places!**

---

## 📚 Complete Example

```python
#!/usr/bin/env python3
"""Complete example showing data access."""

from setup_databroker_helper import load_from_documents
import pandas as pd
import matplotlib.pyplot as plt

# Load latest experiment
print("Loading latest experiment...")
run_data = load_from_documents()

# Show metadata
start = run_data['start']
print(f"\n📋 Experiment: {start.get('experiment_id')}")
print(f"   Plan: {start['plan_name']}")
print(f"   UID: {start['uid'][:8]}")
print(f"   Purpose: {start.get('purpose', 'N/A')}")

# Extract data
events = run_data['events']
data = [event['data'] for event in events]
df = pd.DataFrame(data)

# Statistics
print(f"\n📊 Data Statistics:")
print(df.describe())

# Plot
if 'motor' in df.columns and 'det_value' in df.columns:
    plt.figure(figsize=(10, 6))
    plt.plot(df['motor'], df['det_value'], 'o-')
    plt.xlabel('Motor Position')
    plt.ylabel('Detector Value')
    plt.title(f"Experiment: {start.get('experiment_id')}")
    plt.grid(True)
    plt.savefig('data/exports/latest_plot.png', dpi=150)
    print("\n💾 Plot saved: data/exports/latest_plot.png")

# Save to CSV
output_file = f"data/exports/{start['uid'][:8]}_analysis.csv"
df.to_csv(output_file, index=False)
print(f"💾 Data saved: {output_file}")

print("\n✅ Analysis complete!")
```

**Save as:** `analyze_latest.py`

**Run:**
```bash
python analyze_latest.py
```

---

## 🎯 Summary Table

| Method | File Location | Works Now? | Persists? |
|--------|---------------|------------|-----------|
| **JSON Documents** | `data/documents/*.jsonl` | ✅ Yes | ✅ Yes |
| **DataBroker Catalog** | `data/catalog/*.msgpack` | ⚠️ After running fixed experiment | ✅ Yes |
| **CSV Exports** | `data/exports/*.csv` | ✅ Via `access_my_data.py` | ✅ Yes |

---

## 🔍 Quick Commands Reference

```bash
# Access existing data
python access_my_data.py

# Check DataBroker status
python setup_databroker_helper.py

# Run fixed experiment (creates catalog)
python experiments/mock_experiment_with_databroker.py

# List all your experiments
ls -lh data/documents/

# Check catalog
ls -lh data/catalog/

# Analyze latest
python analyze_latest.py  # (create this from example above)
```

---

## 🐛 Troubleshooting

### "No runs found"
**Solution:** Run an experiment first
```bash
python experiments/mock_experiment_with_databroker.py
```

### "suitcase-msgpack not available"
**Solution:** Install it
```bash
conda activate gnuradio
pip install suitcase-msgpack
```

### "Catalog not found"
**Solution:** This is normal! Your data is still in `data/documents/`. Use:
```bash
python access_my_data.py
```

### "Want to use named catalog 'ejfat_gnuradio'"
**Solution:** Named catalogs require additional configuration. For now:
- Use `Broker.named('temp')` with `serializer` subscription (persistent storage)
- Or access data from documents directly (always works)

---

## 🎉 Next Steps

1. ✅ **Access your existing data**: `python access_my_data.py`
2. ✅ **Install suitcase-msgpack**: `pip install suitcase-msgpack`
3. ✅ **Run fixed experiment**: Creates proper catalog
4. ✅ **Update other experiments**: Use the template in `DATABROKER_FIX_GUIDE.md`
5. ✅ **Analyze data**: Create custom analysis scripts

Your data is safe, accessible, and ready for analysis! 🚀

---

## 📖 Additional Resources

- **DATABROKER_FIX_GUIDE.md** - Complete technical guide
- **setup_databroker_helper.py** - Helper functions
- **access_my_data.py** - Quick data access script
- **experiments/mock_experiment_with_databroker.py** - Fixed experiment template

**Questions?** Read the full guide: `DATABROKER_FIX_GUIDE.md`
