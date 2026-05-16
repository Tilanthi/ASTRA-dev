#!/usr/bin/env python3
"""
Generate Athena++ input files for CALIBRATION_EXTENSION campaign.

This script creates 36 simulation configurations across the parameter space:
- f = 1.3, 1.4, 1.5, 1.6, 1.8, 2.0
- beta = 0.3, 0.5, 1.0
- seeds = 42, 137

Each simulation is configured with longitudinal magnetic field (theta = 0)
and isothermal equation of state.

Usage:
    python run_campaign.py

Output:
    Creates 36 directories with Athena++ input files
"""

import json
import numpy as np
from pathlib import Path


def load_spec():
    """Load campaign specification from JSON."""
    with open('calibration_extension_spec.json', 'r') as f:
        return json.load(f)


def compute_alfven_velocity(beta, cs=1.0):
    """Compute Alfven velocity from plasma beta.

    beta = P_thermal / P_magnetic = (cs^2) / (v_A^2)
    v_A = cs / sqrt(beta)
    """
    return cs / np.sqrt(beta)


def compute_B0(f, beta, cs=1.0):
    """Compute initial magnetic field strength.

    For a cylindrical filament with line mass f * M_line,crit:
    B0 is set such that plasma beta matches desired value.

    beta = (2*cs^2) / (v_A^2) for cylindrical geometry
    v_A^2 = B^2 / (4*pi*rho)
    """
    rho_0 = 1.0  # Central density (normalized)
    v_A = compute_alfven_velocity(beta, cs)
    B0 = v_A * np.sqrt(4 * np.pi * rho_0)
    return B0


def generate_athena_input(sim_dir, f, beta, seed, spec):
    """Generate Athena++ input file for a single simulation."""

    # Compute physics parameters
    B0 = compute_B0(f, beta)

    # Athena++ input template
    input_content = f"""<job>
problem_id   = calib_f{f}_beta{beta}_s{seed}

<time>
tlim         = 6.0
nlim         = -1
dt           = 1e-4
cfl_number   = 0.3
tm_cycle     = 200
rst_interval = 1.0
dt_interval  = 0.01

<mesh>
nx1          = 256
nx2          = 64
nx3          = 64
frequencies  = 1.0 1.0 1.0
refinement   = none
x1min        = 0.0
x1max        = 8.0
x2min        = -1.0
x2max        = 1.0
x3min        = -1.0
x3max        = 1.0
bc_ix1       = periodic
bc_ox1       = periodic
bc_ix2       = periodic
bc_ox2       = periodic
bc_ix3       = periodic
bc_ox3       = periodic

<meshblock>
nx1          = 32
nx2          = 32
nx3          = 32
x2rat        = 1.0
x3rat        = 1.0

<hydro>
iso_sound_speed = 1.0
gamma           = 1.0

<mhd>
b_flag       = 1
beta         = {beta}

<gravity>
gravity_flag = 1
gr_type      = fft
four_pi_G   = 39.47841760435743
gnx1 fft    = 256
gnx2 fft    = 64
gnx3 fft    = 64

<problem>
problem_type = filament
f            = {f}
B0           = {B0:.6f}
theta_deg    = 0.0
turb_amp     = 1e-4
turb_type    = kolmogorov
turb_modes   = 8
seed         = {seed}

<output>
output      = hst
file_type   = hst
variable    = prim
dt          = 0.01

<output>
output      = rst
file_type   = rst
dt          = 1.0

<output>
output      = vtk
file_type   = vtk
dt          = 0.5
variable    = prim
"""

    # Write input file
    input_file = sim_dir / "athinput.calib_f{f}_beta{beta}_s{seed}"
    with open(input_file, 'w') as f_out:
        f_out.write(input_content)

    return input_file


def generate_run_script(sim_dir, f, beta, seed):
    """Generate shell script to run a single simulation."""

    run_script = f"""#!/bin/bash
# Run script for calib_f{f}_beta{beta}_s{seed}

SIM_NAME="calib_f{f}_beta{beta}_s{seed}"
NP=24
TIMEOUT=3600

echo "Starting simulation $SIM_NAME at $(date)"

mpirun -np $NP athena -i athinput.$SIM_NAME \\
    > stdout.txt 2>&1

# Check for timeout or error
if [ $? -ne 0 ]; then
    echo "ERROR: Simulation failed with exit code $?"
    exit 1
fi

# Check if simulation completed
if grep -q "time=" output.txt; then
    FINAL_T=$(grep "time=" output.txt | tail -1 | awk '{{print $2}}')
    echo "Simulation completed at t = $FINAL_T"
else
    echo "WARNING: Completion marker not found in output.txt"
fi

echo "Finished simulation $SIM_NAME at $(date)"
"""

    script_file = sim_dir / "run.sh"
    with open(script_file, 'w') as f_out:
        f_out.write(run_script)

    # Make executable
    script_file.chmod(0o755)

    return script_file


def main():
    """Generate all simulation files."""

    spec = load_spec()

    print("="*70)
    print("CALIBRATION_EXTENSION Campaign Generator")
    print("="*70)
    print(f"Total simulations: {spec['total_simulations']}")
    print(f"Parameter space:")
    print(f"  f: {spec['parameter_grid']['f_values']}")
    print(f"  beta: {spec['parameter_grid']['beta_values']}")
    print(f"  seeds: {spec['parameter_grid']['seeds']}")
    print("="*70)

    sim_count = 0

    # Iterate over parameter grid
    for f in spec['parameter_grid']['f_values']:
        for beta in spec['parameter_grid']['beta_values']:
            for seed in spec['parameter_grid']['seeds']:

                sim_name = f"calib_f{f}_beta{beta}_s{seed}"
                sim_dir = Path(sim_name)

                # Create simulation directory
                sim_dir.mkdir(exist_ok=True)

                # Generate Athena++ input file
                input_file = generate_athena_input(sim_dir, f, beta, seed, spec)
                print(f"Created: {input_file}")

                # Generate run script
                run_script = generate_run_script(sim_dir, f, beta, seed)
                print(f"Created: {run_script}")

                sim_count += 1

    print("="*70)
    print(f"Generated {sim_count} simulation configurations")
    print("="*70)

    # Generate master run script (for all simulations)
    master_script = generate_master_run_script(spec)
    print(f"Created: {master_script}")

    print("\nTo run all simulations:")
    print("  bash run_all.sh")


def generate_master_run_script(spec):
    """Generate master script to run all simulations."""

    sim_names = []
    for f in spec['parameter_grid']['f_values']:
        for beta in spec['parameter_grid']['beta_values']:
            for seed in spec['parameter_grid']['seeds']:
                sim_names.append(f"calib_f{f}_beta{beta}_s{seed}")

    script_content = f"""#!/bin/bash
# Master run script for CALIBRATION_EXTENSION campaign
# 36 simulations total
# Expected runtime: ~5 hours on 200 CPUs with 8 concurrent jobs

MAX_CONCURRENT=8
TIMEOUT=3600

echo "Starting CALIBRATION_EXTENSION campaign at $(date)"
echo "Total simulations: {len(sim_names)}"
echo "Max concurrent jobs: $MAX_CONCURRENT"
echo ""

run_sim() {{
    local sim_dir="$1"
    cd "$sim_dir" || return 1
    bash run.sh
    cd ..
}}

# Queue of simulations
SIM_QUEUE=({" ".join(sim_names)})

# Run simulations with concurrency limit
running=0
for sim in "${{SIM_QUEUE[@]}}"; do
    # Wait if we've hit the concurrency limit
    while [ $running -ge $MAX_CONCURRENT ]; do
        wait -n 2>/dev/null || true
        running=$(jobs -r | wc -l)
    done

    # Run this simulation
    (
        if [ -d "$sim" ]; then
            run_sim "$sim"
            if [ $? -eq 0 ]; then
                echo "SUCCESS: $sim completed"
            else
                echo "FAILED: $sim failed"
            fi
        else
            echo "ERROR: Directory $sim not found"
        fi
    ) &

    running=$((running + 1))
done

# Wait for all remaining jobs to complete
wait

echo ""
echo "Campaign completed at $(date)"
"""

    script_file = Path("run_all.sh")
    with open(script_file, 'w') as f_out:
        f_out.write(script_content)

    script_file.chmod(0o755)
    return script_file


if __name__ == '__main__':
    main()
