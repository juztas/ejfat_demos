# DataBroker Quick Reference

## ✅ DONE: Persistent DataBroker Now Active!

All experiments now automatically save to **persistent catalog** + **JSON backup**.

---

## 🚀 Quick Commands

```bash
# Run experiment (saves to catalog automatically)
python run_experiment.py mock_experiment

# Check catalog status
python run_experiment.py status

# View latest data
python access_my_data.py

# List all experiments
python run_experiment.py list
```

---

## 📊 Access Your Data

### Option 1: Quick Script
```bash
python access_my_data.py
```

### Option 2: Python (Same Session)
```python
# After running experiment:
run = db[-1]
table = run.table()
print(table)
```

### Option 3: Load from Catalog
```python
from setup_databroker_helper import load_data_from_catalog
cat = load_data_from_catalog()
```

### Option 4: Load from Documents
```python
from setup_databroker_helper import load_from_documents
run_data = load_from_documents()
```

---

## 💾 Where Data Lives

| Location | Format | Purpose |
|----------|--------|---------|
| `data/catalog/*.msgpack` | msgpack | Persistent catalog (cross-session) |
| `data/documents/*.jsonl` | JSON Lines | Backup & inspection |
| `data/exports/` | CSV/HDF5/Excel | Analysis & sharing |

---

## 🔧 For Experiment Developers

### Standard Setup Pattern

```python
from bluesky_config.experiment_setup import create_experiment_environment

def main():
    # One line gives you everything!
    env = create_experiment_environment(headless=True)

    RE = env['RE']    # RunEngine
    db = env['db']    # DataBroker

    # ... your experiment code ...

    uid = RE(your_plan, **metadata)

    # Retrieve immediately
    run = db[-1]
    table = run.table()
```

---

## 📖 Full Documentation

- **Quick Start:** `QUICK_START_DATABROKER.md`
- **Complete Guide:** `DATABROKER_FIX_GUIDE.md`
- **Update Details:** `PERSISTENT_DATABROKER_UPDATE.md`
- **Example Code:** `experiments/mock_experiment.py`

---

**Status:** ✅ Production Ready | **Updated:** 2025-10-19
