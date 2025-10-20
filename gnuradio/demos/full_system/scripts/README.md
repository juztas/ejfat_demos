# Scripts Directory

This directory contains all Python scripts for the Bluesky experiment framework, organized by purpose.

## Directory Structure

```
scripts/
├── cli/                 # Command-line interface
│   └── run_experiment.py
├── config_setup/        # Configuration and environment setup
│   ├── config.py
│   ├── init_databroker.py
│   ├── register_catalog.py
│   ├── setup_databroker_helper.py
│   └── setup_environment.py
├── data_access/         # Data retrieval and analysis
│   ├── access_my_data.py
│   └── retrieve_data.py
├── demos/               # Example demonstrations
│   ├── comprehensive_scan_demo.py
│   └── quick_scan_test.py
└── testing/             # Test scripts
    ├── test_all_experiments.py
    ├── test_fm_beamline.py
    └── test_fm_plans_callbacks.py
```

## Categories

### CLI (Command-Line Interface)
**Purpose:** Main entry point for running experiments

- **run_experiment.py** - CLI for discovering and running experiments
  - Commands: `list`, `status`, `info <name>`, `<experiment_name>`
  - Automatically discovers experiments in the `experiments/` directory
  - Provides standardized data storage and retrieval

**Usage:**
```bash
# From project root
python scripts/cli/run_experiment.py list
python scripts/cli/run_experiment.py status
python scripts/cli/run_experiment.py mock_experiment
```

### Configuration & Setup
**Purpose:** Configure Bluesky environment, DataBroker, and devices

- **config.py** - Central configuration module
  - Defines project paths, DataBroker settings, device defaults
  - Used by all other scripts

- **setup_environment.py** - Setup RunEngine and DataBroker
  - Functions: `setup_databroker()`, `setup_runengine()`, `setup_environment()`
  - Creates standard devices

- **setup_databroker_helper.py** - DataBroker with persistent storage
  - Functions: `get_databroker_with_persistence()`, `load_data_from_catalog()`, `load_from_documents()`
  - Provides fallback methods for data access

- **init_databroker.py** - Initialize persistent DataBroker catalog
  - CLI tool with `--stats` and `--setup-serializer` options

- **register_catalog.py** - Register catalog with intake/databroker
  - Makes catalog accessible via `Broker.named('ejfat_gnuradio')`

**Usage:**
```python
# Import in your scripts
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "config_setup"))

from config import DATA_DIR, DOCUMENT_DIR
from setup_environment import setup_environment
```

### Data Access
**Purpose:** Retrieve and display saved experiment data

- **retrieve_data.py** - Comprehensive data retrieval tool
  - CLI with options: `--list`, `--uid`, `--latest`, `--table`, `--stats`, `--all`
  - Loads from JSONL document files
  - Displays summaries, data tables, and statistics

- **access_my_data.py** - Quick access to latest experiment data
  - Simple interface for non-technical users
  - Automatically generates statistics and exports to CSV

**Usage:**
```bash
# From project root
python scripts/data_access/retrieve_data.py --list
python scripts/data_access/retrieve_data.py --latest --all
python scripts/data_access/access_my_data.py
```

### Demonstrations
**Purpose:** Show example workflows and usage patterns

- **quick_scan_test.py** - Simple frequency scan demonstration
  - Minimal setup for quick testing
  - Uses real GNURadioSignalGenerator with MockDetector

- **comprehensive_scan_demo.py** - Full-featured experiment demonstration
  - Complete workflow: setup → scan → analysis → export → visualization
  - Generates CSV exports and matplotlib plots

**Usage:**
```bash
# From project root
python scripts/demos/quick_scan_test.py
python scripts/demos/comprehensive_scan_demo.py
```

### Testing
**Purpose:** Verify functionality of experiments, devices, and plans

- **test_all_experiments.py** - Test Phase 4 experiment types
  - Tests 6 experiment categories (basic, adaptive, time series, etc.)
  - Interactive mode or command-line options (`--basic`, `--adaptive`, etc.)
  - Supports `--mock` flag for testing without hardware

- **test_fm_beamline.py** - Test FM SHM beamline devices
  - 6 test functions covering configuration, devices, and flowgraph control

- **test_fm_plans_callbacks.py** - Test FM SHM plans and callbacks
  - Tests scan plans and callbacks
  - Uses simulated devices (no hardware needed)

**Usage:**
```bash
# From project root
python scripts/testing/test_all_experiments.py --all --mock
python scripts/testing/test_fm_beamline.py
python scripts/testing/test_fm_plans_callbacks.py
```

## Path References

All scripts have been updated to handle the new directory structure:

1. **Project Root Access:** Scripts use `Path(__file__).parent.parent.parent` to access the project root
2. **Config Module:** Scripts add `scripts/config_setup/` to `sys.path` to import config
3. **Data Paths:** All data paths use absolute paths via `config.py` which correctly references the project root

## Running Scripts

### From Project Root (Recommended)
```bash
# CLI
python scripts/cli/run_experiment.py list

# Data Access
python scripts/data_access/retrieve_data.py --list

# Demos
python scripts/demos/quick_scan_test.py

# Testing
python scripts/testing/test_all_experiments.py --all
```

### From Script Directory
Scripts can also be run directly from their subdirectories as they automatically locate the project root.

## Adding New Scripts

When adding new scripts to this directory:

1. **Choose the appropriate subdirectory** based on the script's purpose
2. **Add path setup at the top:**
   ```python
   import sys
   from pathlib import Path

   # Add project root to path
   project_root = Path(__file__).parent.parent.parent
   sys.path.insert(0, str(project_root))

   # If you need config module, also add:
   sys.path.insert(0, str(project_root / "scripts" / "config_setup"))
   ```
3. **Use absolute paths** via config module: `from config import DATA_DIR, DOCUMENT_DIR`
4. **Document the script** in this README

## Migration Notes

This directory structure was created to organize scripts by purpose. Previously, all scripts were in the project root directory. The reorganization:

- Makes the codebase easier to navigate
- Groups related functionality together
- Follows Python project best practices
- Maintains backward compatibility through proper path handling
