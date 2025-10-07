# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This directory contains a GNU Radio conda environment setup designed for EJFAT demos, with strict compatibility requirements for E2SAR integration. The environment versions are carefully selected to satisfy E2SAR's dependency constraints - always check the E2SAR repository and current `environment.yml` for the actual versions in use.

## Locating E2SAR Repository

Before proceeding with dependency selection, **you must locate the E2SAR repository**:

1. **Default locations** (most likely):
   - `../../E2SAR` (above this git repository)
   - `./E2SAR` (cloned into this directory)

2. **If not at default locations**, ask the user where their E2SAR repository is located
   - Other common locations: `~/Projects/E2SAR`, `~/Projects/EJFAT/E2SAR`, `~/E2SAR`

3. **If no local copy exists**, offer to use the GitHub repository:
   - Repository URL: https://github.com/JeffersonLab/E2SAR
   - Offer to clone it into this directory: `./E2SAR/`

4. **If cloning into this directory**:
   - Clone with: `git clone --recurse-submodules --depth 1 https://github.com/JeffersonLab/E2SAR E2SAR`
   - Add `E2SAR/` to `.gitignore` in this directory (already done)
   - Reference files as `./E2SAR/meson.build`, etc.

**Note**: For the rest of this document, `$E2SAR_PATH` refers to wherever the E2SAR repository is located.

## Dependency Selection Process

When installing GNU Radio and its dependencies, **always ensure compatibility with E2SAR**.

### How to Select Compatible Dependencies

**CRITICAL**: Always check the E2SAR repository's actual current requirements. Do not rely on examples in this document - they may be outdated.

**CRITICAL**: Never rely on automatic dependency resolution. Always explicitly search conda-forge for available versions and pin specific versions that satisfy BOTH GNU Radio and E2SAR requirements. Automatic resolution may pull in incompatible versions.

#### Process Overview

For each dependency (Boost, gRPC, protobuf, Python):

1. **Locate the requirement** in E2SAR's build configuration files
2. **Extract the version constraint** (minimum, maximum, or exact version)
3. **Search conda-forge** for available versions: `conda search <package> -c conda-forge`
4. **Select a version** from the search results that satisfies both E2SAR and GNU Radio requirements
5. **Explicitly pin** the selected version in environment.yml (e.g., `libboost=1.86.0`)
6. **Verify** by checking both projects' documentation if needed

#### Step-by-Step Workflow

1. **Find Boost requirements**:
   - Search `$E2SAR_PATH/meson.build` for `boost_dep` or `dependency('boost')`
   - Look for version constraints like `version : '>= X.Y.Z'`
   - Also check `$E2SAR_PATH/conda/meta.yaml` under `requirements:`
   - **Example** (may be outdated): E2SAR once required `>=1.83.0, <=1.86.0`
   - **Search available versions**: `conda search libboost -c conda-forge | grep -E "1\.(83|84|85|86)\."` and `conda search libboost-devel -c conda-forge`
   - **Choose a version** from the search results that satisfies both E2SAR's range and GNU Radio's requirements
   - **CRITICAL**: E2SAR's Meson build uses CMake to find Boost, which requires `libboost-devel` package
   - **Pin explicitly** in environment.yml (e.g., `- libboost=1.86.0` and `- libboost-devel=1.86.0`)

2. **Find gRPC requirements**:
   - Search `$E2SAR_PATH/meson.build` for `grpc` or `grpc_dep` (typically `dependency('grpc++')`)
   - Look for minimum version constraints in the `version:` parameter
   - **CRITICAL**: Use a gRPC version that meets or exceeds E2SAR's minimum requirement
   - **WARNING**: Installing a version below E2SAR's minimum will cause build failures
   - **PACKAGE SELECTION**: Use `libgrpc` + `grpcio` instead of `grpc-cpp`
     - `grpc-cpp` (development package) often lags behind on certain platforms
     - `libgrpc` (runtime libraries) typically has newer versions available
     - `grpcio` (Python bindings) also has newer versions available
     - Both `libgrpc` and `grpcio` should meet or exceed E2SAR's minimum version requirement
   - **Search available versions**: `conda search libgrpc -c conda-forge` and `conda search grpcio -c conda-forge`
   - **Choose a version** from the search results that meets or exceeds E2SAR's minimum
   - **Pin explicitly** in environment.yml (e.g., `- libgrpc=1.75.1` and `- grpcio=1.75.1`)

3. **Find Protocol Buffers requirements**:
   - Search `$E2SAR_PATH/meson.build` for `protobuf` or `protoc`
   - Look for version constraints
   - **Example** (may be outdated): E2SAR once required `>=3.21.12`
   - **Search available versions**: `conda search protobuf -c conda-forge`
   - **Choose a version** from the search results that meets or exceeds E2SAR's minimum
   - **Pin explicitly** in environment.yml (e.g., `- protobuf>=3.21.12`)

4. **Find Python version support**:
   - Check `$E2SAR_PATH/conda/conda_build_config.yaml` for `python:`
   - This lists all Python versions E2SAR is tested against
   - **Example** (may be outdated): E2SAR once supported Python 3.9, 3.10, and 3.11
   - **Search GNU Radio compatibility**: Check GNU Radio documentation or conda packages
   - **Choose a version** supported by both E2SAR and GNU Radio (typically the highest common version)
   - **Pin explicitly** in environment.yml (e.g., `- python=3.11.*`)

### Key E2SAR Files to Reference

When doing a fresh install or updating dependencies, always check:

- **`$E2SAR_PATH/meson.build`**: Primary build configuration with version constraints
  - Search for `dependency('boost')`, `dependency('grpc++')`, and `find_program('protoc')`
  - These contain the actual version requirements
  - Example locations (may have moved): gRPC near line 89, Boost near lines 95-96, Protobuf near line 105

- **`$E2SAR_PATH/conda/meta.yaml`**: Conda package build specification
  - Check the `requirements:` section for both `build:` and `run:` dependencies
  - Look for Boost, gRPC, and protobuf entries with version pins
  - Example location (may have moved): requirements section often starts around line 20-30

- **`$E2SAR_PATH/conda/conda_build_config.yaml`**: Python version matrix
  - Look for the `python:` key near the top of the file
  - Lists all Python versions E2SAR is tested with
  - Example location (may have moved): typically at the very beginning of the file

### Environment Configuration

The `environment.yml` in this directory should be configured to:

1. **Explicitly pin Boost version** that satisfies both E2SAR's requirements and GNU Radio's needs (e.g., `libboost=1.86.0` and `libboost-devel=1.86.0`)
   - **CRITICAL**: `libboost-devel` is required for CMake config files that E2SAR's Meson build needs
   - Without `libboost-devel`, Meson will fail with "Dependency 'boost' not found" even if `libboost` is installed
2. **Explicitly pin gRPC versions** that meet or exceed E2SAR's minimum using `libgrpc` + `grpcio` packages (e.g., `libgrpc=1.75.1`, `grpcio=1.75.1`)
3. **Explicitly pin protobuf version** that meets or exceeds E2SAR's minimum (e.g., `protobuf>=3.21.12`)
4. **Explicitly pin Python version** supported by both E2SAR and GNU Radio (e.g., `python=3.11.*`)
5. Include a compatible GNU Radio version for signal processing
6. Include development tools needed for building OOT modules (meson, cmake, pybind11, etc.)

**CRITICAL**: Do NOT rely on automatic dependency resolution. Always search conda-forge for available versions and explicitly pin compatible versions in environment.yml.

**Note**: Check the actual `environment.yml` file to see current versions. The file should document why specific versions were chosen.

**Important**: Always use `libgrpc` and `grpcio` for gRPC dependencies, not `grpc-cpp`, as the development package often has limited version availability on certain platforms.

### Build Tools Compatibility

Since you may need to build custom GNU Radio modules that link against E2SAR, include these build dependencies:

- **meson**: E2SAR's build system
- **cmake**: For Boost detection and GNU Radio builds
- **ninja**: Meson's backend
- **pybind11**: For Python bindings
- **swig**: For legacy Python bindings
- **pkg-config**: For library discovery

### Migration Notes

This setup replaces the older `radioconda` environment. The setup script automatically:
1. Backs up any existing `radioconda` environment to `radioconda_backup_<timestamp>`
2. Creates the new `gnuradio` environment with E2SAR-compatible dependencies

## Installation Workflow

```bash
# Step 1: Locate or clone E2SAR repository (see "Locating E2SAR Repository" section above)

# Step 2: Always check E2SAR requirements first
# (Replace $E2SAR_PATH with the actual path)
cat $E2SAR_PATH/meson.build | grep -A 2 "boost_dep\|grpc_dep\|protoc_cmd"

# Pay special attention to these version requirements:
# - boost_dep: Check the version range (e.g., >=1.83.0, <=1.86.0)
# - grpc_dep: Check minimum version (e.g., >=1.54.1) - CRITICAL!
# - protoc: Check minimum version (e.g., >=3.21.12)

# Step 3: Search conda-forge for available versions that satisfy requirements
# Example: If E2SAR requires Boost >=1.83.0, <=1.86.0:
conda search libboost -c conda-forge | grep -E "1\.(83|84|85|86)\."
# Choose the highest version that satisfies both E2SAR and GNU Radio

# Step 4: Update environment.yml with explicit version pins
# Make sure to pin specific versions for libgrpc, grpcio, libboost, and protobuf
# Use libgrpc + grpcio, not grpc-cpp
# Example: libboost=1.86.0, libgrpc=1.75.1, grpcio=1.75.1

# Step 5: Run the setup
./setup.sh

# Step 6: Verify compatibility
conda activate gnuradio
python verify_installation.py

# Step 7: Compare installed versions with E2SAR requirements
echo "Checking installed versions against E2SAR requirements:"
echo "Boost:" && conda list boost | grep boost
echo "gRPC (libgrpc):" && conda list libgrpc
echo "gRPC (grpcio):" && conda list grpcio
echo "Protobuf:" && conda list protobuf | grep protobuf
echo "Python:" && python --version

# Step 8: Build and install ejfat_shm Python package
cd ejfat_shm
pip install -e .
cd ..

# Step 9: Install GNU Radio out-of-tree module (gr-ejfat)
cd gr-ejfat

# Check if there are C++ blocks that require CMake build
if [ -f lib/CMakeLists.txt ] && grep -q "\.cc\|\.cpp" lib/CMakeLists.txt && ! grep -q "No C++ sources" lib/CMakeLists.txt; then
    # C++ blocks detected - use full CMake build
    echo "C++ blocks detected, using CMake build process..."
    mkdir -p build
    cd build
    cmake ..
    make
    sudo make install
    cd ..
else
    # Python-only blocks - use simple Makefile install
    echo "Python-only blocks, using Makefile install..."
    make install
fi

cd ..
```

## Testing E2SAR Integration

After installing the GNU Radio environment, test E2SAR compatibility:

```bash
conda activate gnuradio

# Step 1: Check installed versions
echo "=== Installed Versions ==="
echo "Boost:" && conda list boost | grep libboost
echo "gRPC (libgrpc):" && conda list libgrpc
echo "gRPC (grpcio):" && conda list grpcio
echo "Protobuf:" && conda list protobuf | grep protobuf
echo "Python:" && python --version

# Step 2: Check E2SAR requirements
echo ""
echo "=== E2SAR Requirements ==="
# (Replace $E2SAR_PATH with the actual path)
grep "boost_dep" $E2SAR_PATH/meson.build
grep "grpc_dep" $E2SAR_PATH/meson.build
grep "protoc" $E2SAR_PATH/meson.build | grep version

# Step 3: Verify versions meet requirements
# Manually compare the installed versions (Step 1) with requirements (Step 2)
# CRITICAL: Ensure BOTH libgrpc and grpcio versions >= E2SAR's minimum requirement!

# Step 4: Try building E2SAR in this environment (optional but recommended)
cd $E2SAR_PATH
export BOOST_ROOT=$CONDA_PREFIX
meson setup --wipe build_test
# If meson setup succeeds, the versions are compatible
# If it fails with "Dependency not found" errors, version mismatch is likely
meson compile -C build_test
```

## Common Issues

### Boost version mismatch or not found
If E2SAR's Meson setup fails with "Dependency 'boost' not found", check:
```bash
conda list | grep boost
# You need BOTH libboost AND libboost-devel
# libboost provides runtime libraries
# libboost-devel provides CMake config files that Meson needs

# If libboost-devel is missing:
conda install -c conda-forge libboost-devel=1.86.0

# If version is incompatible, search for a compatible version and update environment.yml:
conda search libboost -c conda-forge | grep -E "1\.(83|84|85|86)\."
conda search libboost-devel -c conda-forge | grep -E "1\.(83|84|85|86)\."
# Choose a version from the results, then update environment.yml with explicit pins
# Example:
#   - libboost=1.86.0
#   - libboost-devel=1.86.0
# Then recreate the environment (backup first!)
```

### gRPC version mismatch
**CRITICAL**: E2SAR requires a minimum gRPC version. Installing an older version will cause build failures.

To check installed gRPC version vs E2SAR requirements:
```bash
# Check installed versions
conda activate gnuradio
conda list | grep grpc
# Look for both libgrpc and grpcio versions

# Check E2SAR's required minimum version
grep "grpc_dep" $E2SAR_PATH/meson.build

# If version is too old, search for a compatible version and update environment.yml:
# 1. Search conda-forge for available versions:
conda search libgrpc -c conda-forge
conda search grpcio -c conda-forge
# 2. Choose versions that meet or exceed E2SAR's minimum requirement
# 3. Update environment.yml with explicit pins for BOTH libgrpc and grpcio
#    Example: - libgrpc=1.75.1 and - grpcio=1.75.1
# 4. Do NOT use grpc-cpp (often has limited versions on some platforms)
# 5. Backup and recreate environment (see Environment Management section)
```

Common error message when gRPC is too old:
```
meson.build:XX:X: ERROR: Dependency "grpc++" found: NO found X.Y.Z but need: '>= A.B.C'
```

### gRPC not found
Ensure pkg-config can find it:
```bash
pkg-config --cflags grpc++
export PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig:$PKG_CONFIG_PATH
```

### Python version conflicts
Check E2SAR and GNU Radio compatibility:
```bash
python --version  # Should be a version supported by both E2SAR and GNU Radio
```

## Common Commands

### Environment Setup
```bash
# Initial setup (automated)
./setup.sh

# Manual environment creation
conda env create -f environment.yml

# Activate environment
conda activate gnuradio

# Build and install ejfat_shm
cd ejfat_shm
pip install -e .
cd ..

# Install GNU Radio out-of-tree module (gr-ejfat)
cd gr-ejfat

# Check if there are C++ blocks that require CMake build
if [ -f lib/CMakeLists.txt ] && grep -q "\.cc\|\.cpp" lib/CMakeLists.txt && ! grep -q "No C++ sources" lib/CMakeLists.txt; then
    # C++ blocks detected - use full CMake build
    echo "C++ blocks detected, using CMake build process..."
    mkdir -p build
    cd build
    cmake ..
    make
    sudo make install
    cd ..
else
    # Python-only blocks - use simple Makefile install
    echo "Python-only blocks, using Makefile install..."
    make install
fi

cd ..

# Deactivate environment
conda deactivate

# Verify installation
python verify_installation.py
```

### GNU Radio Usage
```bash
# Launch GNU Radio Companion (graphical flowgraph editor)
gnuradio-companion

# Run a flowgraph from command line
python <flowgraph_name>.py

# Test gr-ejfat blocks
cd gr-ejfat

# Run unit tests
python python/ejfat/qa_ejfat_sink.py
python python/ejfat/qa_ejfat_source.py
python python/ejfat/qa_ejfat_shm_sink.py
python python/ejfat/qa_ejfat_shm_source.py

# Run example flowgraphs
python examples/test_ejfat_shm_blocks.py

cd ..
```

### Environment Management
```bash
# List all conda environments
conda env list

# Update environment from environment.yml
conda env update -f environment.yml --prune

# Backup existing environment before recreating (RECOMMENDED)
# This is safer than removal - preserves old environment if something goes wrong
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
conda create -n gnuradio_backup_${TIMESTAMP} --clone gnuradio -y

# Remove environment (only after backing up!)
conda env remove -n gnuradio

# Export current environment snapshot
conda env export > environment_snapshot.yml

# Check installed packages
conda list
conda list | grep boost
conda list | grep grpc  # Shows both libgrpc and grpcio
```

### Troubleshooting
```bash
# Check Python version (should match environment.yml)
python --version

# Check GNU Radio version
python -c "from gnuradio import gr; print(gr.version())"

# Check if Qt/GUI is working
python -c "from PyQt5 import QtCore; print(QtCore.PYQT_VERSION_STR)"

# Test UHD devices
uhd_find_devices

# Test RTL-SDR
rtl_test

# Check pkg-config for gRPC
pkg-config --cflags grpc++
export PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig:$PKG_CONFIG_PATH
```

## Future Updates

When updating this environment:

1. **Before changing any versions**, check E2SAR's requirements haven't changed
2. **After updating environment.yml**, test that E2SAR still compiles
3. **Document any version changes** and why they were necessary
4. **Update this file** with new learnings

## Related Documentation

- E2SAR GitHub Repository: https://github.com/JeffersonLab/E2SAR
- E2SAR README: `$E2SAR_PATH/README.md`
- E2SAR Build Config: `$E2SAR_PATH/meson.build`
- E2SAR Conda Recipe: `$E2SAR_PATH/conda/meta.yaml`
- GNU Radio Wiki: https://wiki.gnuradio.org/
- GNU Radio Tutorials: https://wiki.gnuradio.org/index.php/Tutorials
- GNU Radio Conda Guide: https://wiki.gnuradio.org/index.php/CondaInstall
