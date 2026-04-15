#!/usr/bin/env python3

# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Create submission script for Athena++ simulations

Adapt this to your cluster scheduler (SLURM, PBS, LSF, etc.)
"""

import json
from pathlib import Path

# Load simulation design
design_file = Path(__file__).parent / 'moderate_supercriticality_design.json'
with open(design_file) as f:
    design = json.load(f)

# Athena++ executable path (modify this to your installation)
ATHENA_EXE = '/path/to/athena++/bin/athena'

# Number of cores per simulation
NCORES = 12

# Wall time estimate (hours)
WALL_TIME = 24

# Create SLURM submission script
slurm_content = f"""#!/bin/bash
#SBATCH --job-name=filament_mhd
#SBATCH --nodes=1
#SBATCH --ntasks-per-node={NCORES}
#SBATCH --cpus-per-task=1
#SBATCH --time={WALL_TIME}:00:00
#SBATCH --output=filament_mhd_%j.out
#SBATCH --error=filament_mhd_%j.err

# Load modules (modify for your cluster)
# module load openmpi
# module load hdf5

# Set variables
ATHENA_EXE={ATHENA_EXE}
INPUT_DIR=$(pwd)/athena_inputs
SIM_LIST=$INPUT_DIR/simulation_list.txt

# Function to run one simulation
run_simulation() {{
    local sim_name=$1
    local input_file=$INPUT_DIR/${{sim_name}}.athinput

    echo "Starting simulation: $sim_name"
    echo "Input file: $input_file"

    # Create output directory
    mkdir -p outputs/$sim_name

    # Run Athena++ with MPI
    mpirun -np {NCORES} $ATHENA_EXE -i $input_file

    if [ $? -eq 0 ]; then
        echo "Completed: $sim_name"
        # Optional: move to completed directory
        # mv $input_file athena_inputs/completed/
    else
        echo "FAILED: $sim_name" >&2
        return 1
    fi
}}

# Export function for parallel execution
export -f run_simulation

# Read simulation list and run in parallel
# Adjust parallel jobs based on your cluster's available resources
MAX_PARALLEL=1  # Change to run multiple sims concurrently

cat $SIM_LIST | xargs -P $MAX_PARALLEL -I {{}} bash -c 'run_simulation "{{}}"'

echo "All simulations complete!"
"""

# Create PBS submission script (alternative)
pbs_content = f"""#!/bin/bash
#PBS -N filament_mhd
#PBS -l nodes=1:ppn={NCORES}
#PBS -l walltime={WALL_TIME}:00:00
#PBS -o filament_mhd_${{PBS_JOBID}}.out
#PBS -e filament_mhd_${{PBS_JOBID}}.err

# Load modules (modify for your cluster)
# module load openmpi
# module load hdf5

# Set variables
ATHENA_EXE={ATHENA_EXE}
INPUT_DIR=$(pwd)/athena_inputs
SIM_LIST=$INPUT_DIR/simulation_list.txt

# Function to run one simulation
run_simulation() {{
    local sim_name=$1
    local input_file=$INPUT_DIR/${{sim_name}}.athinput

    echo "Starting simulation: $sim_name"
    echo "Input file: $input_file"

    # Create output directory
    mkdir -p outputs/$sim_name

    # Run Athena++ with MPI
    mpirun -np {NCORES} $ATHENA_EXE -i $input_file

    if [ $? -eq 0 ]; then
        echo "Completed: $sim_name"
    else
        echo "FAILED: $sim_name" >&2
        return 1
    fi
}}

# Read simulation list and run
while read sim_name; do
    run_simulation "$sim_name"
done < "$SIM_LIST"

echo "All simulations complete!"
"""

# Create a simple serial script (for local testing)
serial_content = f"""#!/bin/bash
# Simple serial execution script (for testing or local execution)

ATHENA_EXE={ATHENA_EXE}
INPUT_DIR=$(pwd)/athena_inputs
SIM_LIST=$INPUT_DIR/simulation_list.txt

echo "Running {len(design['simulations'])} simulations sequentially..."
echo

while read sim_name; do
    input_file=$INPUT_DIR/${{sim_name}}.athinput

    echo "========================================="
    echo "Starting: $sim_name"
    echo "Input: $input_file"
    echo "Time: $(date)"
    echo "========================================="

    mkdir -p outputs/$sim_name

    # Run Athena++ (adjust -np for your core count)
    mpirun -np {NCORES} $ATHENA_EXE -i $input_file

    if [ $? -eq 0 ]; then
        echo "✓ Completed: $sim_name"
    else
        echo "✗ FAILED: $sim_name"
        exit 1
    fi
    echo
done < "$SIM_LIST"

echo "========================================="
echo "All simulations complete!"
echo "Time: $(date)"
echo "========================================="
"""

# Write scripts
scripts_dir = Path(__file__).parent / 'submission_scripts'
scripts_dir.mkdir(exist_ok=True)

with open(scripts_dir / 'submit_slurm.sh', 'w') as f:
    f.write(slurm_content)
with open(scripts_dir / 'submit_pbs.sh', 'w') as f:
    f.write(pbs_content)
with open(scripts_dir / 'run_serial.sh', 'w') as f:
    f.write(serial_content)

# Make scripts executable
for script in scripts_dir.glob('*.sh'):
    script.chmod(0o755)

print("Created submission scripts:")
print(f"  {scripts_dir}/submit_slurm.sh  (SLURM scheduler)")
print(f"  {scripts_dir}/submit_pbs.sh    (PBS scheduler)")
print(f"  {scripts_dir}/run_serial.sh    (Serial/Local execution)")
print()
print("Choose the appropriate script for your cluster.")
print("Before submitting, edit the ATHENA_EXE path at the top of the script.")
