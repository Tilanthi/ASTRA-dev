#!/usr/bin/env python3
"""
RCE Campaign Launcher
Generates input files and submission scripts for the Radial Confinement Escalation campaign
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

class RCECampaignGenerator:
    """Generate RCE campaign simulation configurations."""

    def __init__(self, base_dir: str, athena_path: str):
        self.base_dir = Path(base_dir)
        self.athena_path = Path(athena_path)

        # Create output directories
        self.config_dir = self.base_dir / "config"
        self.script_dir = self.base_dir / "scripts"
        self.config_dir.mkdir(exist_ok=True)
        self.script_dir.mkdir(exist_ok=True)

    def generate_parameter_grid(self) -> List[Dict]:
        """Generate full parameter grid for RCE campaign."""

        parameters = []

        # Parameter ranges
        f_values = [1.2, 1.3, 1.4, 1.5]  # Line-mass ratio
        beta_values = [0.5, 1.0, 2.0]    # Plasma beta
        mach_values = [2.0, 3.0]         # Mach number
        p_ext_values = [0.0, 0.1, 0.3, 0.5, 1.0]  # External pressure (1.0 = rigid)
        seeds = [1, 2, 3]                # Random seeds

        # Generate all combinations
        for f in f_values:
            for beta in beta_values:
                for mach in mach_values:
                    for p_ext in p_ext_values:
                        for seed in seeds:

                            # Skip rigid wall for now (separate campaign)
                            if p_ext >= 1.0:
                                continue

                            # Calculate B-field from plasma beta
                            # β = 8πP/B² → B = sqrt(8πP/β)
                            # For P = ρc_s² = 1.0 (isothermal), B = sqrt(8π/β)
                            B_field = (8.0 * 3.14159 / beta) ** 0.5

                            params = {
                                'f': f,
                                'beta': beta,
                                'mach': mach,
                                'p_ext': p_ext,
                                'seed': seed,
                                'B_field': B_field,
                                'problem_id': f"RCE_f{f}_b{beta}_m{mach}_p{p_ext}_s{seed}"
                            }

                            parameters.append(params)

        return parameters

    def generate_input_file(self, params: Dict) -> str:
        """Generate Athena++ input file for a single simulation."""

        input_template = f"""# RCE Campaign Input File
# Parameters: f={params['f']}, β={params['beta']}, M={params['mach']}, P_ext={params['p_ext']}, seed={params['seed']}

<job>
    problem_id = {params['problem_id']}
</job>

<time>
    tlim = 3.0          # Simulation time (code units)
    nlim = 15000       # Maximum steps
    dt_out = 0.05      # Output frequency
</time>

<mesh>
    nx1 = 256          # Transverse resolution
    nx2 = 64           # Longitudinal resolution
    nx3 = 64           # Vertical resolution

    x1min = -0.5       # Transverse domain (pc)
    x1max = 0.5
    x2min = -0.125     # Longitudinal domain
    x2max = 0.125
    x3min = -0.125
    x3max = 0.125

    # Boundary conditions
    ix1_bc = outflow_with_pressure
    ix2_bc = outflow_with_pressure
    iy1_bc = outflow_with_pressure
    iy2_bc = outflow_with_pressure
    iz1_bc = periodic    # Infinite filament approximation
    iz2_bc = periodic
</mesh>

<boundary>
    p_ext_ratio = {params['p_ext']}  # External pressure level
</boundary>

<hydro>
    iso_sound_speed = 1.0
    gamma = 1.0           # Isothermal
</hydro>

<mhd>
    # Magnetic field configuration
    b_initial = {params['B_field']:.6f}  # Calculated from plasma beta
</mhd>

<problem>
    # Filament initial conditions
    rho_iso = 1.0        # Background density
    rho_0 = 10.0         # Central density enhancement
    w_core = 0.062       # Core width (pc)
    f_ratio = {params['f']}  # Line-mass ratio

    # Turbulence driving
    turb_mach = {params['mach']}
    turb_seed = {params['seed']}
    turb_cutoff = 2.0
    turb_correlation = 0.25
</problem>

<output>
    dt = 0.05
    variables = prim
    filetype = hst
    sum_x1 = 1           # Sum over transverse direction
    dump_vtk = false     # Disable VTK output (saves disk space)
</output>

<resample>
    # No resampling for this campaign
    resample_nsqrt = 1
</resample>
"""
        return input_template

    def generate_submission_script(self, params: Dict, queue: str = "slurm") -> str:
        """Generate job submission script."""

        if queue == "slurm":
            script = f"""#!/bin/bash
#SBATCH --job-name={params['problem_id']}
#SBATCH --output={params['problem_id']}.out
#SBATCH --error={params['problem_id']}.err
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --time=24:00:00
#SBATCH --mem=16G

# Load modules
module purge
module load openmpi/4.1.1
module load gcc/11.2.0

# Set paths
ATHENA_DIR={self.athena_path}
CONFIG_DIR={self.config_dir}
OUTPUT_DIR={self.base_dir / "outputs" / params['problem_id']}

# Create output directory
mkdir -p $OUTPUT_DIR

# Change to output directory
cd $OUTPUT_DIR

# Run simulation
mpirun -np 4 $ATHENA_DIR/bin/athena -m $CONFIG_DIR/{params['problem_id']}.in

# Check completion
if [ $? -eq 0 ]; then
    echo "Simulation completed successfully"
else
    echo "Simulation failed with exit code $?"
fi
"""
        elif queue == "pbs":
            script = f"""#!/bin/bash
#PBS -N {params['problem_id']}
#PBS -o {params['problem_id']}.out
#PBS -e {params['problem_id']}.err
#PBS -l nodes=1:ppn=4
#PBS -l walltime=24:00:00
#PBS -l mem=16gb

# Load modules
module purge
module load openmpi/4.1.1
module load gcc/11.2.0

# Set paths
ATHENA_DIR={self.athena_path}
CONFIG_DIR={self.base_dir / "config"}
OUTPUT_DIR={self.base_dir / "outputs" / params['problem_id']}

# Create output directory
mkdir -p $OUTPUT_DIR

# Change to output directory
cd $OUTPUT_DIR

# Run simulation
mpirun -np 4 $ATHENA_DIR/bin/athena -m $CONFIG_DIR/{params['problem_id']}.in

# Check completion
if [ $? -eq 0 ]; then
    echo "Simulation completed successfully"
else
    echo "Simulation failed with exit code $?"
fi
"""
        else:  # Local execution
            script = f"""#!/bin/bash
# Local execution script for {params['problem_id']}

ATHENA_DIR={self.athena_path}
CONFIG_DIR={self.config_dir}
OUTPUT_DIR={self.base_dir / "outputs" / params['problem_id']}

# Create output directory
mkdir -p $OUTPUT_DIR

# Change to output directory
cd $OUTPUT_DIR

# Run simulation
mpirun -np 4 $ATHENA_DIR/bin/athena -m $CONFIG_DIR/{params['problem_id']}.in

# Check completion
if [ $? -eq 0 ]; then
    echo "Simulation completed successfully"
else
    echo "Simulation failed with exit code $?"
fi
"""

        return script

    def generate_tier1_subset(self) -> List[Dict]:
        """Generate Tier 1 high-priority parameter subset."""

        tier1_params = []

        # Tier 1: f=[1.3, 1.4], β=1.0, M=2.0, P_ext=[0.1, 0.3, 0.5], seeds=[1,2,3]
        for f in [1.3, 1.4]:
            for p_ext in [0.1, 0.3, 0.5]:
                for seed in [1, 2, 3]:
                    B_field = (8.0 * 3.14159 / 1.0) ** 0.5

                    tier1_params.append({
                        'f': f,
                        'beta': 1.0,
                        'mach': 2.0,
                        'p_ext': p_ext,
                        'seed': seed,
                        'B_field': B_field,
                        'problem_id': f"RCE_f{f}_b1.0_m2.0_p{p_ext}_s{seed}"
                    })

        return tier1_params

    def generate_all_campaign_files(self, tier1_only: bool = False):
        """Generate all campaign files."""

        if tier1_only:
            print("Generating Tier 1 high-priority subset (18 simulations)...")
            parameters = self.generate_tier1_subset()
        else:
            print("Generating full RCE campaign...")
            parameters = self.generate_parameter_grid()

        print(f"Total simulations: {len(parameters)}")

        # Generate input files and scripts
        for i, params in enumerate(parameters):
            print(f"Generating files for simulation {i+1}/{len(parameters)}: {params['problem_id']}")

            # Generate input file
            input_file = self.config_dir / f"{params['problem_id']}.in"
            with open(input_file, 'w') as f:
                f.write(self.generate_input_file(params))

            # Generate submission scripts for multiple queues
            for queue in ['slurm', 'pbs', 'local']:
                script_file = self.script_dir / f"{params['problem_id']}_{queue}.sh"
                with open(script_file, 'w') as f:
                    f.write(self.generate_submission_script(params, queue))
                os.chmod(script_file, 0o755)

        # Save parameter list
        param_file = self.base_dir / "campaign_parameters.json"
        with open(param_file, 'w') as f:
            json.dump(parameters, f, indent=2)

        print(f"\nCampaign generation complete!")
        print(f"  Input files: {self.config_dir}")
        print(f"  Scripts: {self.script_dir}")
        print(f"  Parameters: {param_file}")

        return parameters

    def generate_launch_script(self, queue: str = 'slurm'):
        """Generate master launch script."""

        script = f"""#!/bin/bash
# RCE Campaign Launch Script
# Queue: {queue}

CONFIG_DIR="{self.config_dir}"
SCRIPT_DIR="{self.script_dir}"
PARAM_FILE="{self.base_dir / 'campaign_parameters.json'}"

# Read parameters
PARAMS=$(cat $PARAM_FILE)

# Count simulations
TOTAL=$(echo "$PARAMS" | jq 'length')
echo "Launching $TOTAL simulations"

# Launch all simulations
for i in $(seq 0 $(($TOTAL - 1))); do
    PROBLEM_ID=$(echo "$PARAMS" | jq -r ".[$i].problem_id")
    SCRIPT="$SCRIPT_DIR/${{PROBLEM_ID}}_{queue}.sh"

    if [ -f "$SCRIPT" ]; then
        echo "Launching $PROBLEM_ID..."
"""

        if queue == 'slurm':
            script += """        sbatch $SCRIPT
"""
        elif queue == 'pbs':
            script += """        qsub $SCRIPT
"""
        else:  # Local
            script += """        $SCRIPT &
"""

        script += """    else
        echo "Warning: Script not found: $SCRIPT"
    fi
done

echo "Campaign launch complete"
echo "Monitor with: squeue (slurm) or qstat (pbs)"
"""

        # Write launch script
        launch_file = self.base_dir / f"launch_campaign_{queue}.sh"
        with open(launch_file, 'w') as f:
            f.write(script)
        os.chmod(launch_file, 0o755)

        print(f"Launch script created: {launch_file}")
        return launch_file


def main():
    """Main execution function."""

    import argparse

    parser = argparse.ArgumentParser(description='Generate RCE campaign files')
    parser.add_argument('--base-dir', type=str, default='.',
                        help='Base directory for campaign files')
    parser.add_argument('--athena-path', type=str,
                        default='../../athena++',
                        help='Path to Athena++ installation')
    parser.add_argument('--tier1-only', action='store_true',
                        help='Generate only Tier 1 high-priority subset')
    parser.add_argument('--queue', type=str, default='slurm',
                        choices=['slurm', 'pbs', 'local'],
                        help='Job queue type')

    args = parser.parse_args()

    # Create generator
    generator = RCECampaignGenerator(
        base_dir=args.base_dir,
        athena_path=args.athena_path
    )

    # Generate campaign files
    parameters = generator.generate_all_campaign_files(tier1_only=args.tier1_only)

    # Generate launch script
    generator.generate_launch_script(queue=args.queue)

    print(f"\nCampaign ready to launch!")
    print(f"  Total simulations: {len(parameters)}")
    print(f"  Configuration directory: {generator.config_dir}")
    print(f"  Script directory: {generator.script_dir}")


if __name__ == '__main__':
    main()
