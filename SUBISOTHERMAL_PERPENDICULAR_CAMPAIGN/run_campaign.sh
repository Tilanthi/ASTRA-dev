#!/bin/bash
###############################################################################
# Sub-Isothermal Perpendicular Field Campaign - Ray Execution Script
#
# This script sets up and runs the 72-simulation campaign on a Ray cluster.
#
# Usage:
#   ./run_campaign.sh [--setup_only] [--dry_run]
#
# Options:
#   --setup_only    Set up Ray cluster but don't run simulations
#   --dry_run       Test setup without actually running simulations
#
###############################################################################

set -e  # Exit on error

# Script parameters
CAMPAIGN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${CAMPAIGN_DIR}/config/ray_cluster.yaml"
PARAM_FILE="${CAMPAIGN_DIR}/simulation_parameters.csv"
PYTHON_SCRIPT="${CAMPAIGN_DIR}/setup_ray_cluster.py"

# Ray parameters (configurable via environment)
RAY_NUM_WORKERS=${RAY_NUM_WORKERS:-220}
RAY_CPUS_PER_WORKER=${RAY_CPUS_PER_WORKER:-1}
RAY_MEMORY_GB=${RAY_MEMORY_GB:-8}
RAY_OBJECT_STORE_MEMORY_GB=${RAY_OBJECT_STORE_MEMORY_GB:-100}
RAY_TEMP_DIR=${RAY_TEMP_DIR:-/tmp/ray}
RAY_DASHBOARD_PORT=${RAY_DASHBOARD_PORT:-8265}

# Output directories
OUTPUT_BASE_DIR=${OUTPUT_BASE_DIR:-${CAMPAIGN_DIR}/simulation_output}
LOG_DIR="${OUTPUT_BASE_DIR}/logs"

# Create output directories
mkdir -p "${OUTPUT_BASE_DIR}"
mkdir -p "${LOG_DIR}"

echo "========================================================================"
echo "Sub-Isothermal Perpendicular Field Campaign"
echo "========================================================================"
echo "Campaign directory: ${CAMPAIGN_DIR}"
echo "Output directory: ${OUTPUT_BASE_DIR}"
echo "Ray workers: ${RAY_NUM_WORKERS}"
echo "CPUs per worker: ${RAY_CPUS_PER_WORKER}"
echo "Memory per worker: ${RAY_MEMORY_GB} GB"
echo "Object store memory: ${RAY_OBJECT_STORE_MEMORY_GB} GB"
echo "========================================================================"

# Check if Python and Ray are available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3.8+."
    exit 1
fi

echo "Checking Python installation..."
python3 --version

echo "Checking Ray installation..."
python3 -c "import ray; print(f'Ray version: {ray.__version__}')" || {
    echo "ERROR: Ray not installed. Install with: pip install ray[default]"
    exit 1
}

# Check required Python packages
echo "Checking required packages..."
python3 -c "import pandas, numpy, yaml" || {
    echo "ERROR: Required packages missing. Install with: pip install pandas numpy pyyaml"
    exit 1
}

# Parse command line arguments
SETUP_ONLY=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --setup_only)
            SETUP_ONLY=true
            shift
            ;;
        --dry_run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if simulation parameters file exists
if [ ! -f "${PARAM_FILE}" ]; then
    echo "ERROR: Simulation parameters file not found: ${PARAM_FILE}"
    exit 1
fi

# Count number of simulations
NUM_SIMS=$(tail -n +2 "${PARAM_FILE}" | wc -l)
echo "Number of simulations to run: ${NUM_SIMS}"

# Estimate walltime
# Assume ~6 hours per simulation with 220 vCPUs (36 concurrent)
HOURS_PER_SIM=6
CONCURRENT_JOBS=36
TOTAL_BATCHES=$(( ($NUM_SIMS + $CONCURRENT_JOBS - 1) / $CONCURRENT_JOBS ))
ESTIMATED_HOURS=$(( $TOTAL_BATCHES * $HOURS_PER_SIM ))
echo "Estimated walltime: ~${ESTIMATED_HOURS} hours"

# Confirm before running
if [ "$SETUP_ONLY" = false ] && [ "$DRY_RUN" = false ]; then
    echo ""
    echo "This will run ${NUM_SIMS} simulations on ${RAY_NUM_WORKERS} Ray workers."
    echo "Estimated walltime: ~${ESTIMATED_HOURS} hours"
    echo ""
    read -p "Do you want to continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Aborted by user."
        exit 0
    fi
fi

# Setup Ray cluster
echo ""
echo "========================================================================"
echo "Setting up Ray cluster..."
echo "========================================================================"

# Set environment variables
export RAY_NUM_WORKERS
export RAY_CPUS_PER_WORKER
export RAY_MEMORY_GB
export RAY_OBJECT_STORE_MEMORY_GB
export RAY_TEMP_DIR
export RAY_DASHBOARD_PORT
export OUTPUT_BASE_DIR

# Initialize Ray
echo "Starting Ray head node..."
ray start --head \
    --num-cpus=$((RAY_NUM_WORKERS * RAY_CPUS_PER_WORKER)) \
    --num-gpus=0 \
    --object-store-memory=$((RAY_OBJECT_STORE_MEMORY_GB * 1024 * 1024 * 1024)) \
    --temp-dir="${RAY_TEMP_DIR}" \
    --dashboard-port=${RAY_DASHBOARD_PORT} \
    --log-dir="${LOG_DIR}" || {
    echo "Note: Ray may already be running. Stopping and restarting..."
    ray stop
    ray start --head \
        --num-cpus=$((RAY_NUM_WORKERS * RAY_CPUS_PER_WORKER)) \
        --num-gpus=0 \
        --object-store-memory=$((RAY_OBJECT_STORE_MEMORY_GB * 1024 * 1024 * 1024)) \
        --temp-dir="${RAY_TEMP_DIR}" \
        --dashboard-port=${RAY_DASHBOARD_PORT} \
        --log-dir="${LOG_DIR}"
}

echo "Ray dashboard available at: http://localhost:${RAY_DASHBOARD_PORT}"

# Run Python setup script
if [ "$SETUP_ONLY" = true ]; then
    echo ""
    echo "Setup complete. Ray cluster ready."
    echo "Use 'python3 ${PYTHON_SCRIPT} --sim_params ${PARAM_FILE} --run' to start simulations."
    exit 0
fi

# Run simulations
echo ""
echo "========================================================================"
echo "Running simulations..."
echo "========================================================================"

if [ "$DRY_RUN" = true ]; then
    echo "Dry run mode - would run ${NUM_SIMS} simulations"
    python3 "${PYTHON_SCRIPT}" \
        --cluster_config "${CONFIG_FILE}" \
        --sim_params "${PARAM_FILE}" \
        --dry_run
else
    echo "Starting campaign execution..."
    python3 "${PYTHON_SCRIPT}" \
        --cluster_config "${CONFIG_FILE}" \
        --sim_params "${PARAM_FILE}" \
        --run 2>&1 | tee "${LOG_DIR}/campaign_execution.log"
fi

# Shutdown Ray cluster
echo ""
echo "========================================================================"
echo "Campaign complete. Shutting down Ray cluster..."
echo "========================================================================"

ray stop

echo ""
echo "========================================================================"
echo "All done!"
echo "========================================================================"
echo "Simulation outputs: ${OUTPUT_BASE_DIR}"
echo "Logs: ${LOG_DIR}"
echo "========================================================================"
