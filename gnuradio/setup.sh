#!/bin/bash
# GNU Radio Conda Environment Setup Script

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_NAME="gnuradio"

echo "================================================"
echo "GNU Radio Conda Environment Setup"
echo "================================================"
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "ERROR: conda not found. Please install Anaconda or Miniconda first."
    echo "Download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "Step 1: Checking for existing 'radioconda' environment..."
if conda env list | grep -q "^radioconda "; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_NAME="radioconda_backup_${TIMESTAMP}"
    echo "Found existing 'radioconda' environment."
    echo "Renaming to '${BACKUP_NAME}'..."

    # Clone the environment with new name
    conda create -n ${BACKUP_NAME} --clone radioconda -y

    # Remove the old radioconda environment
    conda env remove -n radioconda -y

    echo "✓ Renamed radioconda → ${BACKUP_NAME}"
fi

echo ""
echo "Step 2: Checking for existing '${ENV_NAME}' environment..."
if conda env list | grep -q "^${ENV_NAME} "; then
    echo "WARNING: Environment '${ENV_NAME}' already exists."
    read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing environment..."
        conda env remove -n ${ENV_NAME} -y
    else
        echo "Aborting setup."
        exit 0
    fi
fi

echo ""
echo "Step 3: Creating conda environment from environment.yml..."
echo "This may take 10-15 minutes..."
cd "${SCRIPT_DIR}"
conda env create -f environment.yml

echo ""
echo "Step 4: Verifying installation..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate ${ENV_NAME}

# Run verification script if it exists
if [ -f "${SCRIPT_DIR}/verify_installation.py" ]; then
    python verify_installation.py
else
    echo "Note: verify_installation.py not found, skipping automated verification."
fi

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "To activate the environment, run:"
echo "  conda activate ${ENV_NAME}"
echo ""
echo "To launch GNU Radio Companion:"
echo "  gnuradio-companion"
echo ""
echo "To deactivate:"
echo "  conda deactivate"
echo ""
