#!/bin/bash
#SBATCH --job-name=filament_mhd
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=12
#SBATCH --cpus-per-task=1
#SBATCH --time=24:00:00
#SBATCH --output=filament_mhd_%j.out
#SBATCH --error=filament_mhd_%j.err

# Load modules (modify for your cluster)
# module load openmpi
# module load hdf5

# Set variables
ATHENA_EXE=/path/to/athena++/bin/athena
INPUT_DIR=$(pwd)/athena_inputs
SIM_LIST=$INPUT_DIR/simulation_list.txt

# Function to run one simulation
run_simulation() {
    local sim_name=$1
    local input_file=$INPUT_DIR/${sim_name}.athinput

    echo "Starting simulation: $sim_name"
    echo "Input file: $input_file"

    # Create output directory
    mkdir -p outputs/$sim_name

    # Run Athena++ with MPI
    mpirun -np 12 $ATHENA_EXE -i $input_file

    if [ $? -eq 0 ]; then
        echo "Completed: $sim_name"
        # Optional: move to completed directory
        # mv $input_file athena_inputs/completed/
    else
        echo "FAILED: $sim_name" >&2
        return 1
    fi
}

# Export function for parallel execution
export -f run_simulation

# Read simulation list and run in parallel
# Adjust parallel jobs based on your cluster's available resources
MAX_PARALLEL=1  # Change to run multiple sims concurrently

cat $SIM_LIST | xargs -P $MAX_PARALLEL -I {} bash -c 'run_simulation "{}"'

echo "All simulations complete!"
