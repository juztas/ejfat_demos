# GNU Radio Conda Environment Setup

This directory contains configuration files for setting up a GNU Radio development environment using conda. The environment is configured to be compatible with the E2SAR project requirements.

## Environment Specifications

- **Python**: 3.11
- **Boost**: 1.86.x (compatible with E2SAR: >=1.83.0, <=1.86.0 and GNU Radio 3.10.12+)
- **GNU Radio**: 3.10.x
- **Key Dependencies**: gRPC, Protocol Buffers, UHD, various SDR hardware support libraries

## Prerequisites

- **Conda/Miniconda/Anaconda** must be installed
  - Download from: https://docs.conda.io/en/latest/miniconda.html
- **macOS** (Darwin 24.6.0 or compatible)

## Quick Start

### Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
./setup.sh
```

This script will:
1. Check if `radioconda` environment exists and rename it to `radioconda_backup_<timestamp>`
2. Check for existing `gnuradio` environment and prompt for removal
3. Create new conda environment from `environment.yml`
4. Verify the installation by running tests
5. Display activation instructions

**Estimated time**: 10-15 minutes

### Option 2: Manual Setup

If you prefer manual control:

```bash
# Create the environment
conda env create -f environment.yml

# Activate the environment
conda activate gnuradio

# Verify installation
python verify_installation.py
```

## Environment Contents

### Core Components
- **GNU Radio 3.10**: Complete signal processing framework
- **Boost 1.85**: C++ libraries (E2SAR compatible version)
- **Python 3.11**: Runtime environment

### Scientific Stack
- NumPy, SciPy, Matplotlib, Pandas
- Jupyter, IPython for interactive development

### SDR Hardware Support
- **UHD**: USRP devices
- **RTL-SDR**: RTL-SDR dongles
- **HackRF**: HackRF devices
- **gr-osmosdr**: OsmoSDR support

### Development Tools
- CMake, Meson, Ninja (build systems)
- SWIG, pybind11 (bindings)
- gRPC-CPP >=1.51.1, Protocol Buffers >=3.21.12
- ZeroMQ with C++ and Python bindings

## Usage

### Activating the Environment

```bash
conda activate gnuradio
```

### Launching GNU Radio Companion

```bash
gnuradio-companion
```

### Deactivating the Environment

```bash
conda deactivate
```

### Verifying Installation

Run the verification script anytime to check component health:

```bash
python verify_installation.py
```

This will test:
- GNU Radio core modules
- Python scientific libraries
- Networking libraries
- Available GNU Radio modules
- Display versions and status

## Environment Management

### Listing Conda Environments

```bash
conda env list
```

### Updating the Environment

If `environment.yml` is updated:

```bash
conda env update -f environment.yml --prune
```

### Removing the Environment

```bash
conda env remove -n gnuradio
```

### Exporting Current Environment

To share or backup your exact configuration:

```bash
conda env export > environment_snapshot.yml
```

## Migrating from radioconda

If you previously used `radioconda`, the setup script automatically:
1. Detects the existing `radioconda` environment
2. Creates a backup copy named `radioconda_backup_<timestamp>`
3. Removes the original `radioconda` environment
4. Creates the new `gnuradio` environment

Your old environment remains available as a backup if needed:

```bash
conda activate radioconda_backup_20251006_143022  # example name
```

## Compatibility Notes

### E2SAR Compatibility
This environment is designed to work with the [E2SAR project](https://github.com/JeffersonLab/E2SAR). Key compatibility points:

- **Boost version**: 1.86.x matches E2SAR's requirement (>=1.83.0, <=1.86.0)
- **gRPC-CPP**: >=1.51.1 as required by E2SAR
- **Protocol Buffers**: >=3.21.12 as required by E2SAR
- **Python**: 3.11 supported by both GNU Radio and E2SAR

**For developers**: See `CLAUDE.md` for detailed instructions on how to locate the E2SAR repository and verify compatibility when updating dependencies. The dependency versions are selected by inspecting:
- E2SAR's `meson.build` (lines 89, 95-96, 105)
- E2SAR's `conda/meta.yaml`
- E2SAR's `conda/conda_build_config.yaml`

If you don't have a local E2SAR copy, the dependency-checking process will offer to clone it into this directory.

### macOS-Specific Considerations

- Some SDR hardware drivers have limited macOS support
- Qt-based GUI may require additional system configuration
- Recommend testing with software-only examples first before connecting hardware

## Troubleshooting

### conda command not found
Ensure conda is properly initialized in your shell:
```bash
conda init bash  # or zsh, fish, etc.
```
Then restart your shell.

### Package conflicts during installation
If you encounter conflicts:
```bash
# Remove and recreate the environment
conda env remove -n gnuradio
./setup.sh
```

### Qt/GUI issues on macOS
If GNU Radio Companion fails to launch:
```bash
# Check Qt installation
python -c "from PyQt5 import QtCore; print(QtCore.PYQT_VERSION_STR)"

# May need to reinstall Qt
conda install --force-reinstall pyqt=5
```

### Hardware device not detected
Ensure device drivers are installed system-wide:
```bash
# For UHD devices
uhd_find_devices

# For RTL-SDR
rtl_test
```

## Files

- `environment.yml` - Conda environment specification
- `setup.sh` - Automated installation script
- `verify_installation.py` - Installation verification script
- `README.md` - This documentation file
- `CLAUDE.md` - Developer notes on E2SAR dependency compatibility (for Claude Code)
- `.gitignore` - Ignores local E2SAR clone if present

## Additional Resources

- GNU Radio Documentation: https://wiki.gnuradio.org/
- GNU Radio Tutorials: https://wiki.gnuradio.org/index.php/Tutorials
- Conda User Guide: https://docs.conda.io/projects/conda/en/latest/user-guide/
- E2SAR Project: ~/Projects/E2SAR

## Support

For issues specific to:
- **GNU Radio**: https://wiki.gnuradio.org/index.php/FAQ
- **Conda**: https://docs.conda.io/en/latest/
- **E2SAR**: See E2SAR project documentation
