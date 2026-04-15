#!/bin/bash
#PBS -N filament_mhd
#PBS -l nodes=1:ppn=12
#PBS -l walltime=24:00:00
#PBS -o filament_mhd_${PBS_JOBID}.out
#PBS -e filament_mhd_${PBS_JOBID}.err

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
    else
        echo "FAILED: $sim_name" >&2
        return 1
    fi
}

# Read simulation list and run
while read sim_name; do
    run_simulation "$sim_name"
done < "$SIM_LIST"

echo "All simulations complete!"
