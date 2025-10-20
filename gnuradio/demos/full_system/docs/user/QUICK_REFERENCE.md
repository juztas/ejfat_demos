# Quick Reference: Running Experiments

## One-Liners

```bash
# List all experiments
python run_experiment.py list

# Run mock experiment (no hardware)
python run_experiment.py mock_experiment

# View latest run
python retrieve_data.py --latest --all

# Export latest to CSV
python retrieve_data.py --latest --export csv

# List all captured runs
python retrieve_data.py --list

# Start Jupyter for interactive analysis
jupyter notebook notebooks/quick_start.ipynb
```

## Essential Python Pattern

```python
from bluesky import RunEngine
from ophyd import Signal
from bluesky.plans import scan
from bluesky_config.devices import MockDetector
from bluesky_config.callbacks import DocumentLogger

# Setup (REQUIRED for data capture)
RE = RunEngine({})
doc_logger = DocumentLogger('data/documents')
RE.subscribe(doc_logger)  # ← CRITICAL!

# Create devices
motor = Signal(name='motor', value=0)
det = MockDetector(name='det')

# Run scan
uid = RE(scan([det], motor, 0, 10, 20))

# UID is saved to: data/documents/<uid>_documents.jsonl
```

## Data Retrieval Pattern

```python
from databroker import Broker
from analysis.plotting import plot_run
from analysis.export import export_to_csv

# Load catalog
db = Broker.named('temp')

# Get latest run
run = db[-1]

# View data
print(run.table())

# Plot
plot_run(run, 'motor', 'det_value')

# Export
export_to_csv(run, 'data/my_data.csv')
```

## Common Workflows

### Workflow 1: Quick Test
```bash
python run_experiment.py mock_experiment
python retrieve_data.py --latest --all
```

### Workflow 2: Custom Scan
```python
# Edit parameters in experiments/mock_experiment.py
# Then run:
python experiments/mock_experiment.py
```

### Workflow 3: Interactive Analysis
```bash
jupyter notebook notebooks/quick_start.ipynb
# Run all cells (Cell → Run All)
```

### Workflow 4: Batch Processing
```bash
# Run multiple experiments
for i in {1..5}; do
    python run_experiment.py mock_experiment
done

# Export all
python retrieve_data.py --list
# Note UIDs, then export each
```

## File Locations

| What | Where |
|------|-------|
| Captured data | `data/documents/<uid>_documents.jsonl` |
| Exported CSV | `data/exports/run_<uid>.csv` |
| Exported HDF5 | `data/exports/run_<uid>.h5` |
| Exported Excel | `data/exports/run_<uid>.xlsx` |
| Experiments | `experiments/*.py` |
| Jupyter notebooks | `notebooks/*.ipynb` |

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| No data captured | Check `RE.subscribe(DocumentLogger('data/documents'))` |
| Can't find run | Check `data/documents/` has files, use `retrieve_data.py --list` |
| Import error | Run from `full_system/` directory: `cd full_system` |
| Missing packages | `conda activate gnuradio` then `pip install bluesky ophyd databroker` |

## Key Points

1. **Always subscribe DocumentLogger** to capture data
2. **Data is saved** in `data/documents/<uid>_documents.jsonl`
3. **retrieve_data.py** is your friend for quick viewing
4. **Jupyter notebooks** for interactive analysis
5. **UID** identifies each run uniquely

## Next Steps

📖 **Full Tutorial**: [TUTORIAL_RUNNING_EXPERIMENTS.md](TUTORIAL_RUNNING_EXPERIMENTS.md)

🚀 **Quick Start Notebook**: `notebooks/quick_start.ipynb`

📚 **Complete Guide**: [DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md](DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md)
