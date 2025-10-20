# Tutorial Documentation Summary

## What's Been Created

I've created comprehensive tutorial documentation for running experiments and capturing data in your Bluesky framework:

### 📖 Main Tutorial: TUTORIAL_RUNNING_EXPERIMENTS.md
**A complete step-by-step guide (15-20 minutes)**

**Contents:**
- Prerequisites and setup
- Quick start (5 minutes to first data capture)
- Four methods for running experiments (CLI, direct, custom scripts, interactive)
- Understanding what data gets captured
- Verifying data capture
- Retrieving and analyzing data
- Seven practical examples
- Comprehensive troubleshooting section

**Best for:** New users learning the system, anyone wanting a thorough understanding

### ⚡ Quick Reference: QUICK_REFERENCE.md
**One-page cheat sheet for quick lookup**

**Contents:**
- Essential one-liner commands
- Core Python patterns for data capture and retrieval
- Common workflows (4 typical scenarios)
- File locations table
- Troubleshooting quick fixes
- Key points summary

**Best for:** Experienced users needing quick reminders, command lookup

### 🔄 Updated: README.md
**Added new "Documentation and Tutorials" section**

The main README now prominently features links to:
- The new tutorial for new users
- The quick reference for quick lookup
- Jupyter notebooks for interactive learning
- Data analysis guides
- Developer resources

Also updated the References section with better organization.

## How to Use These Resources

### If You're Just Starting
1. **Read:** [TUTORIAL_RUNNING_EXPERIMENTS.md](TUTORIAL_RUNNING_EXPERIMENTS.md)
2. **Try:** Follow the "Quick Start (5 Minutes)" section
3. **Practice:** Run through the practical examples
4. **Keep handy:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for command lookup

### If You Want Interactive Learning
1. **Start Jupyter:** `jupyter notebook`
2. **Open:** `notebooks/quick_start.ipynb`
3. **Run all cells:** Cell → Run All
4. **Experiment:** Modify code cells and try variations

### If You Want to Jump Right In
```bash
# Run a mock experiment (no hardware needed)
python run_experiment.py mock_experiment

# View the captured data
python retrieve_data.py --latest --all

# Export to CSV
python retrieve_data.py --latest --export csv
```

Then refer to the tutorial or quick reference as needed.

### If You Need Command Lookup
Open [QUICK_REFERENCE.md](QUICK_REFERENCE.md) and use the:
- One-liners section for commands
- Essential Python Pattern for coding
- Common Workflows for complete procedures
- Troubleshooting Quick Fixes for problems

## Key Features of the Tutorial

### ✅ Comprehensive Coverage
- All four methods of running experiments explained
- Data capture, verification, and retrieval covered
- Real-world practical examples included
- Common problems and solutions documented

### ✅ Hands-On Examples
Seven complete working examples:
1. Simple mock scan with data retrieval
2. Custom scan with multiple detectors
3. Batch processing multiple runs
4. Real-time peak detection
5. GNU Radio hardware integration

Each example includes:
- Complete working code
- Expected output
- How to analyze results
- What to look for

### ✅ Troubleshooting Guide
Six common problems covered:
- No data files created
- Cannot retrieve data with DataBroker
- retrieve_data.py shows no runs
- Data looks wrong or incomplete
- Experiment fails to run
- Each with multiple solution approaches

### ✅ Multiple Learning Styles
- **Step-by-step:** Main tutorial with progressive complexity
- **Reference:** Quick reference for command lookup
- **Interactive:** Jupyter notebooks for hands-on learning
- **Examples:** Seven practical scenarios to copy and modify

## File Organization

```
full_system/
├── TUTORIAL_RUNNING_EXPERIMENTS.md  ← Main comprehensive tutorial (NEW)
├── QUICK_REFERENCE.md               ← One-page cheat sheet (NEW)
├── README.md                        ← Updated with doc links (UPDATED)
├── DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md  ← Data analysis reference (EXISTING)
├── CLAUDE.md                        ← Developer guidelines (EXISTING)
├── notebooks/
│   ├── quick_start.ipynb            ← 5-minute interactive tutorial (EXISTING)
│   └── data_retrieval_and_analysis_tutorial.ipynb  ← Full tutorial (EXISTING)
└── experiments/                     ← Example experiments (EXISTING)
```

## Recommended Learning Path

### For Complete Beginners
1. **Read** Quick Start section in [README.md](README.md) (5 min)
2. **Run** your first experiment: `python run_experiment.py mock_experiment` (2 min)
3. **Read** [TUTORIAL_RUNNING_EXPERIMENTS.md](TUTORIAL_RUNNING_EXPERIMENTS.md) (15 min)
4. **Try** the practical examples from the tutorial (15-30 min)
5. **Bookmark** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for later

### For Hands-On Learners
1. **Start** Jupyter: `jupyter notebook` (1 min)
2. **Open** `notebooks/quick_start.ipynb` (1 min)
3. **Run** all cells: Cell → Run All (5 min)
4. **Experiment** with code cells (10-20 min)
5. **Refer** to [TUTORIAL_RUNNING_EXPERIMENTS.md](TUTORIAL_RUNNING_EXPERIMENTS.md) when needed

### For Experienced Users
1. **Skim** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (3 min)
2. **Run** an experiment: `python run_experiment.py mock_experiment` (2 min)
3. **Check** data: `python retrieve_data.py --latest --all` (1 min)
4. **Refer** to specific sections of tutorial as needed

## What Makes This Tutorial Effective

### 1. Progressive Complexity
- Starts with simplest possible example (5 min quick start)
- Gradually introduces more features
- Advanced topics at the end
- Can stop at any point and still be productive

### 2. Multiple Entry Points
- Quick start for immediate results
- Four different methods explained (choose what fits)
- Interactive and non-interactive options
- Hardware and non-hardware examples

### 3. Practical Focus
- Every concept demonstrated with working code
- Real command outputs shown
- Actual file locations specified
- Common problems anticipated and solved

### 4. Reference Value
- Quick reference for command lookup
- Troubleshooting section for problems
- File organization clearly documented
- Links between all documentation

## Testing the Tutorial

You can verify the tutorial works by following the Quick Start:

```bash
# Step 1: Run experiment
python run_experiment.py mock_experiment

# Step 2: View data
python retrieve_data.py --latest --all

# Step 3: Export
python retrieve_data.py --latest --export csv

# Should create: data/exports/run_<uid>.csv
```

If all three steps work, the tutorial is accurate for your system.

## Feedback and Updates

As you use these tutorials, note:
- Any steps that don't work as described
- Missing information you needed
- Confusing sections
- Additional examples that would help

These can be added to improve the documentation.

## Next Steps

1. **Start here:** [TUTORIAL_RUNNING_EXPERIMENTS.md](TUTORIAL_RUNNING_EXPERIMENTS.md)
2. **Quick lookup:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
3. **Interactive:** `jupyter notebook notebooks/quick_start.ipynb`
4. **Deep dive:** [DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md](DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md)

**Happy experimenting!**
