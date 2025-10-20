# Jupyter Notebooks for Data Analysis

This directory contains interactive Jupyter notebooks for analyzing Bluesky experiment data.

## Available Notebooks

### 1. **quick_start.ipynb** - Start Here! ⭐

**Purpose:** Get analyzing data in 5 minutes

**What it covers:**
- Load experiment data from DataBroker
- View data tables
- Create basic plots
- Calculate statistics
- Find peaks
- Export to CSV

**Who it's for:** Everyone starting with data analysis

**Time:** ~5 minutes

---

### 2. **data_retrieval_and_analysis_tutorial.ipynb** - Complete Guide 📚

**Purpose:** Comprehensive interactive tutorial covering all analysis capabilities

**What it covers:**
- DataBroker connection and catalog management
- Retrieving and searching runs
- Data access with Pandas DataFrames
- Statistical analysis (mean, std, peaks, outliers, correlation, SNR)
- Multiple visualization types (line plots, scatter, histograms, heatmaps)
- Comparing multiple runs
- Exporting data (CSV, HDF5, Excel, JSON)
- Advanced analysis workflows

**Who it's for:** Users wanting in-depth understanding

**Time:** ~30-45 minutes

---

## Getting Started

### Prerequisites

1. **Conda environment activated:**
   ```bash
   conda activate gnuradio
   ```

2. **Required packages:**
   ```bash
   pip install jupyter notebook ipykernel matplotlib pandas scipy
   ```

3. **Have some experiment data:**
   - Run at least one experiment first
   - Or use mock experiments for testing

### Starting Jupyter

From the `full_system/` directory:

```bash
# Start Jupyter Notebook
jupyter notebook

# Or start Jupyter Lab
jupyter lab
```

Your browser will open, navigate to `notebooks/` and open a notebook.

### Quick Test

```bash
# Run mock experiment to generate test data
cd ..
python run_experiment.py mock_experiment
cd notebooks

# Start Jupyter
jupyter notebook quick_start.ipynb
```

---

## Notebook Structure

### Quick Start Notebook

```
1. Setup (imports)
2. Load Data (connect to catalog, get latest run)
3. View Data (display table, statistics)
4. Plot Data (basic visualization)
5. Analyze Data (statistics, peaks)
6. Export Data (save to CSV)
```

### Full Tutorial Notebook

```
1. Setup & Imports
2. Connecting to DataBroker
3. Retrieving Runs (latest, search, list all)
4. Accessing Data (DataFrames, metadata)
5. Statistical Analysis (comprehensive stats, peaks, outliers, correlation)
6. Visualization (line plots, scatter, histograms, heatmaps)
7. Comparing Multiple Runs
8. Data Export (CSV, HDF5, Excel, JSON)
9. Advanced Analysis Examples
10. Custom Analysis Space
```

---

## Common Tasks

### Load Latest Run

```python
from databroker import Broker
db = Broker.named('ejfat_gnuradio')
run = db[-1]
table = run.table()
```

### Plot Data

```python
from analysis.plotting import plot_run
import matplotlib.pyplot as plt

plot_run(run, 'frequency', 'power')
plt.show()
```

### Get Statistics

```python
from analysis.statistics import analyze_run

stats = analyze_run(run, 'power')
print(f"Mean: {stats['mean']:.2f}")
print(f"Std: {stats['std']:.2f}")
```

### Export to CSV

```python
from analysis.export import export_to_csv

export_to_csv(run, '../data/exports/my_data.csv')
```

---

## Tips & Tricks

### 1. Keyboard Shortcuts

- `Shift + Enter` - Run cell and move to next
- `Ctrl + Enter` - Run cell and stay
- `A` - Insert cell above
- `B` - Insert cell below
- `DD` - Delete cell
- `M` - Convert to markdown
- `Y` - Convert to code

### 2. Useful Magic Commands

```python
%matplotlib inline    # Show plots in notebook
%load_ext autoreload  # Auto-reload modules
%autoreload 2         # Reload all modules

%%time                # Time cell execution
%pwd                  # Print working directory
%ls                   # List files
```

### 3. Debugging

```python
# Print variable info
?run                  # Documentation
??run                 # Source code

# Interactive debugging
%pdb                  # Enable debugger on error

# Display DataFrame nicely
from IPython.display import display
display(table.head())
```

### 4. Saving Outputs

```python
# Save plot
plt.savefig('../data/exports/my_plot.png', dpi=150, bbox_inches='tight')

# Save notebook output
# File → Download as → HTML/PDF
```

---

## Troubleshooting

### "No module named 'databroker'"

```bash
conda activate gnuradio
pip install databroker
```

### "Catalog not found"

```bash
# Initialize catalog
cd ..
python init_databroker.py
```

### "No runs found"

```bash
# Run an experiment first
python run_experiment.py mock_experiment
```

### "Plots don't show"

```python
# Add this at the top of notebook
%matplotlib inline

# Or explicitly show
import matplotlib.pyplot as plt
plt.show()
```

### "Kernel dies when loading data"

Large datasets may cause memory issues:

```python
# Load only what you need
table = run.table()
subset = table[['frequency', 'power']]  # Select specific columns
subset = table.iloc[:1000]  # First 1000 rows only
```

---

## Creating Your Own Notebooks

### Template Structure

```python
# ========== SETUP ==========
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))

from databroker import Broker
from analysis.statistics import *
from analysis.plotting import *
import matplotlib.pyplot as plt
%matplotlib inline

# ========== LOAD DATA ==========
db = Broker.named('ejfat_gnuradio')
run = db[-1]
table = run.table()

# ========== ANALYSIS ==========
# Your analysis code here

# ========== VISUALIZATION ==========
# Your plots here

# ========== EXPORT ==========
# Export results
```

### Best Practices

1. **Use markdown cells** for explanations
2. **Keep cells focused** - one task per cell
3. **Add comments** in code cells
4. **Save frequently** - Ctrl+S
5. **Clear output** before committing to git
6. **Use relative paths** for portability

---

## Example Workflows

### Workflow 1: Quick Check

```python
# Load latest run
run = db[-1]
table = run.table()

# Quick plot
plot_run(run, 'frequency', 'power')
plt.show()

# Basic stats
print(table['power'].describe())
```

### Workflow 2: Multi-Run Comparison

```python
# Get multiple runs
runs = list(db.search(plan_name='frequency_scan'))[-5:]

# Compare
from analysis.plotting import plot_multiple_runs
plot_multiple_runs(runs, 'frequency', 'power')
plt.show()

# Statistics
from analysis.statistics import compare_runs
comparison = compare_runs(runs, 'power')
display(comparison)
```

### Workflow 3: Detailed Analysis

```python
# Load run
run = db[-1]
table = run.table()

# Comprehensive stats
stats = analyze_run(run, 'power')
for key, val in stats.items():
    print(f"{key}: {val:.4f}")

# Find peaks
peaks = find_peaks(run, 'frequency', 'power', prominence=5)
print(f"Peaks: {peaks['num_peaks']}")

# Plot with peaks marked
fig, ax = plot_run(run, 'frequency', 'power')
if peaks['num_peaks'] > 0:
    ax.plot(peaks['peak_positions'], peaks['peak_values'],
            'r*', markersize=15, label='Peaks')
    ax.legend()
plt.show()

# Export
export_for_analysis(run, '../data/exports/detailed_analysis',
                   formats=['csv', 'hdf5', 'json'])
```

---

## Additional Resources

### Documentation

- **DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md** - Complete reference guide
- **README.md** - Framework documentation
- **CLAUDE.md** - Development guide

### External Resources

- [Jupyter Documentation](https://jupyter.org/documentation)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Gallery](https://matplotlib.org/stable/gallery/)
- [DataBroker Documentation](https://blueskyproject.io/databroker/)

### Getting Help

1. Check the notebook markdown cells for explanations
2. Read the DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md
3. Look at function docstrings: `?function_name`
4. Check the analysis/ source code
5. Run the test experiments to generate sample data

---

## Contributing

To add a new notebook:

1. Create `.ipynb` file in this directory
2. Follow the template structure above
3. Add clear markdown explanations
4. Test all cells execute without errors
5. Clear outputs before committing: `Cell → All Output → Clear`
6. Update this README with notebook description

---

**Last Updated:** 2025-10-18
**Framework Version:** 0.1.0
