#!/bin/bash
# setup_environment.sh
# Environment setup for transonic turbulence campaign on Ray cluster

set -e  # Exit on error

echo "=== Transonic Turbulence Campaign Environment Setup ==="
echo ""

# Detect shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
    SHELL_NAME="bash"
else
    echo "WARNING: Unknown shell. Please manually set environment variables."
    SHELL_CONFIG=""
fi

echo "Detected shell: $SHELL_NAME"
echo "Shell config: $SHELL_CONFIG"
echo ""

# Python environment setup
echo "Setting up Python environment..."

# Check if python3 exists
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3.8 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
VENV_DIR="$(pwd)/venv_turbulence"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1

pip install numpy > /dev/null 2>&1
pip install scipy > /dev/null 2>&1
pip install h5py > /dev/null 2>&1
pip install matplotlib > /dev/null 2>&1
pip install pandas > /dev/null 2>&1
pip install astropy > /dev/null 2>&1

echo "Python packages installed successfully."
echo ""

# Set environment variables for Ray cluster
echo "Setting up environment variables for Ray cluster..."

cat >> environment_setup.tmp << 'EOF'
# Transonic Turbulence Campaign Environment Variables
# Add these to your shell configuration or source this file

# Athena++ installation path
export ATHENA_ROOT="${ATHENA_ROOT:-/path/to/athena-public-version}"
export ATHENA_BIN="${ATHENA_ROOT}/build/bin"

# HDF5 library path (adjust for your cluster)
export HDF5_DIR="${HDF5_DIR:-/usr/local/hdf5}"

# Campaign directories
export TURBULENCE_CAMPAIGN_ROOT="$(pwd)"
export TURBULENCE_INPUTS="${TURBULENCE_CAMPAIGN_ROOT}/inputs"
export TURBULENCE_SCRIPTS="${TURBULENCE_CAMPAIGN_ROOT}/scripts"
export TURBULENCE_RESULTS="${TURBULENCE_CAMPAIGN_ROOT}/results"

# Scratch directory on Ray cluster (adjust for your allocation)
export TURBULENCE_SCRATCH="${TURBULENCE_SCRATCH:-/scratch/$USER/turbulence_campaign}"

# MPI settings for Ray cluster
export MPI_NUM_PROCS="${MPI_NUM_PROCS:-220}"
export OMP_NUM_THREADS=1

# Python path for analysis scripts
export PYTHONPATH="${TURBULENCE_CAMPAIGN_ROOT}:${PYTHONPATH}"

echo "Transonic Turbulence Campaign environment variables set."
echo "Campaign root: $TURBULENCE_CAMPAIGN_ROOT"
EOF

# Add to shell config if requested
if [ -n "$SHELL_CONFIG" ]; then
    echo ""
    echo "To make these environment variables persistent, add this line to $SHELL_CONFIG:"
    echo "  source $(pwd)/environment_setup.tmp"
    echo ""
    read -p "Add to $SHELL_CONFIG now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "" >> "$SHELL_CONFIG"
        echo "# Transonic Turbulence Campaign" >> "$SHELL_CONFIG"
        echo "source $(pwd)/environment_setup.tmp" >> "$SHELL_CONFIG"
        echo "Added to $SHELL_CONFIG"
    fi
fi

# Source environment variables
source environment_setup.tmp

# Create directory structure
echo ""
echo "Creating campaign directory structure..."

mkdir -p inputs/turb_512.fiducial
mkdir -p inputs/turb_full_campaign
mkdir -p scripts
mkdir -p results/resolution_test
mkdir -p results/full_campaign
mkdir -p logs

echo "Directory structure created."
echo ""

# Verify installation
echo "=== Verifying Installation ==="

python3 << 'PYEOF'
import sys
print(f"Python version: {sys.version}")

required_packages = {
    'numpy': 'np',
    'scipy': 'sp',
    'h5py': 'h5py',
    'matplotlib': 'plt',
    'pandas': 'pd',
    'astropy': 'ap'
}

missing = []
for pkg, alias in required_packages.items():
    try:
        __import__(pkg)
        print(f"  ✓ {pkg}")
    except ImportError:
        print(f"  ✗ {pkg} (MISSING)")
        missing.append(pkg)

if missing:
    print(f"\nERROR: Missing packages: {', '.join(missing)}")
    print("Install with: pip install " + " ".join(missing))
    sys.exit(1)
else:
    print("\nAll required Python packages are installed.")
PYEOF

echo ""
echo "=== Environment Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Build Athena++: ./build_athena.sh"
echo "  2. Run resolution test: ./run_resolution_test.sh"
echo ""
echo "Virtual environment is active. Run 'deactivate' to exit."
echo ""

# Keep script session alive for manual commands
if [[ $- == *i* ]]; then
    echo "Press Ctrl+D to exit or type commands to continue..."
    exec bash --norc --noprofile
fi
