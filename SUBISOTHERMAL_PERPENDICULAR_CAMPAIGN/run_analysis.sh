#!/bin/bash
###############################################################################
# Sub-Isothermal Perpendicular Field Campaign - Analysis Execution Script
#
# This script runs the analysis pipeline on completed simulation outputs.
#
# Usage:
#   ./run_analysis.sh [--sim_dir <directory>] [--output_dir <directory>]
#
# Options:
#   --sim_dir      Directory containing simulation outputs (default: ./simulation_output)
#   --output_dir   Directory for analysis outputs (default: ./analysis_results)
#
###############################################################################

set -e  # Exit on error

# Script parameters
CAMPAIGN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="${CAMPAIGN_DIR}/analysis"

# Default directories
SIM_ROOT_DEFAULT="${CAMPAIGN_DIR}/simulation_output"
OUTPUT_DIR_DEFAULT="${CAMPAIGN_DIR}/analysis_results"

# Parse command line arguments
SIM_ROOT="${SIM_ROOT_DEFAULT}"
OUTPUT_DIR="${OUTPUT_DIR_DEFAULT}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --sim_dir)
            SIM_ROOT="$2"
            shift 2
            ;;
        --output_dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "========================================================================"
echo "Sub-Isothermal Perpendicular Field Campaign - Analysis"
echo "========================================================================"
echo "Simulation root: ${SIM_ROOT}"
echo "Output directory: ${OUTPUT_DIR}"
echo "========================================================================"

# Check if simulation directory exists
if [ ! -d "${SIM_ROOT}" ]; then
    echo "ERROR: Simulation directory not found: ${SIM_ROOT}"
    exit 1
fi

# Check if analysis scripts exist
if [ ! -f "${SCRIPTS_DIR}/analyze_filament.py" ]; then
    echo "ERROR: Analysis script not found: ${SCRIPTS_DIR}/analyze_filament.py"
    exit 1
fi

if [ ! -f "${SCRIPTS_DIR}/batch_analysis.py" ]; then
    echo "ERROR: Batch analysis script not found: ${SCRIPTS_DIR}/batch_analysis.py"
    exit 1
fi

# Check Python and required packages
echo "Checking Python installation..."
python3 --version

echo "Checking required packages..."
python3 -c "import numpy, pandas, matplotlib, scipy" || {
    echo "ERROR: Required packages missing."
    echo "Install with: pip install numpy pandas matplotlib scipy h5py seaborn"
    exit 1
}

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Run batch analysis
echo ""
echo "========================================================================"
echo "Running batch analysis..."
echo "========================================================================"

python3 "${SCRIPTS_DIR}/batch_analysis.py" \
    --sim_root "${SIM_ROOT}" \
    --output_dir "${OUTPUT_DIR}"

echo ""
echo "========================================================================"
echo "Analysis complete!"
echo "========================================================================"
echo "Results database: ${OUTPUT_DIR}/campaign_results_database.csv"
echo "Summary: ${OUTPUT_DIR}/campaign_summary.txt"
echo "Mixture calculation: ${OUTPUT_DIR}/mixture_calculation.txt"
echo "Plots: ${OUTPUT_DIR}/*.png"
echo "========================================================================"
