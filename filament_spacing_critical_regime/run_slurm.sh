#!/bin/bash
#SBATCH --job-name=filament_spacing
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=200
#SBATCH --cpus-per-task=1
#SBATCH --mem=200G
#SBATCH --time=168:00:00  # 7 days
#SBATCH --output=filament_spacing_%j.out
#SBATCH --error=filament_spacing_%j.err

# Filament Spacing Critical Regime Simulation Campaign
# Target: f ≈ 2-3 regime to measure λ/W for comparison with HGBS observations

echo "Starting filament spacing campaign at $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Running on $(hostname)"
echo "Allocated ${SLURM_NTASKS} cores"

# Load modules (adjust for your HPC cluster)
module purge
module load python/3.9
module load gcc/10.2
module list

# Set paths
export ATHENA_PATH=/path/to/athena/bin/athena  # UPDATE THIS PATH
export PYTHONPATH=${PYTHONPATH}:$(pwd)

# Check Athena++ exists
if [ ! -f "$ATHENA_PATH" ]; then
    echo "ERROR: Athena++ not found at $ATHENA_PATH"
    echo "Please update ATHENA_PATH in the job script"
    exit 1
fi

echo "Using Athena++ at: $ATHENA_PATH"

# Create output directory
WORK_DIR=./simulations_$(date +%Y%m%d_%H%M%S)
mkdir -p $WORK_DIR

echo "Working directory: $WORK_DIR"

# Check for Ray
python3 -c "import ray" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing Ray..."
    pip install --user ray
fi

# Run the campaign
# Test mode: 10 simulations
# Full campaign: remove --test flag
python3 run_campaign.py \
    --athena $ATHENA_PATH \
    --cores ${SLURM_NTASKS} \
    --work-dir $WORK_DIR \
    # REMOVE --test FLAG FOR FULL CAMPAIGN

echo "Campaign completed at $(date)"
echo "Results saved to: $WORK_DIR"

# Copy results back
if [ -f "$WORK_DIR/results_final.csv" ]; then
    cp $WORK_DIR/results_final.csv ./filament_spacing_results_${SLURM_JOB_ID}.csv
    echo "Results copied to: ./filament_spacing_results_${SLURM_JOB_ID}.csv"
fi
