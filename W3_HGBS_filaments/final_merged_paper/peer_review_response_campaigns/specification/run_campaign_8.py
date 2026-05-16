#!/usr/bin/env python3
"""
Campaign 8: Mixed Field Geometry λ/W Calibration
=================================================

Resolves the central tension: perpendicular-field filaments produce λ/W ≈ 1.25,
but observations show λ/W = 2.79 for filaments that are mostly perpendicular
to the mean field (Planck 2016).

This campaign quantifies λ/W(θ) for oblique B-fields to determine:
1. What mixing fraction of longitudinal-field filaments is needed?
2. Is this fraction consistent with polarimetric observations?

Author: ASTRA Peer Review Response
Date: 2026-04-30
"""

import os
import json
import numpy as np
from datetime import datetime

# =============================================================================
# CAMPAIGN SPECIFICATION
# =============================================================================

CAMPAIGN_ID = "C8_Mixed_Geometry"
CAMPAIGN_NAME = "Mixed Field Geometry λ/W Calibration"

# Parameter space
F_VALUES = [1.5]  # Representative supercritical line mass
BETA_VALUES = [0.3, 0.5, 1.0, 1.5, 2.0]  # Full plasma beta range
THETA_DEG = [0, 15, 30, 45, 60, 75, 90]  # B-field angles (degrees)
MACH_VALUES = [1.0]  # Fixed Mach number
SEEDS = [42, 137, 314, 527, 816]  # Random seeds for ensemble

# Grid dimensions
N1 = 512  # Longitudinal (along filament)
N2 = 64   # Transverse width
N3 = 64   # Transverse height

# Domain size
L1 = 16.0  # Longitudinal (in units of lambda_J)
L2 = 1.0   # Transverse width
L3 = 1.0   # Transverse height

# Output configuration
OUTPUT_BASE = "/data/peer_response_runs/C8"
SNAPSHOT_INTERVAL = 0.5  # Save snapshots every 50% compression

# =============================================================================
# ATHENA++ PROBLEM GENERATION
# =============================================================================

def generate_athena_config(sim_id):
    """Generate ATHENA++ problem configuration for one simulation."""

    # Parse sim_id to extract parameters
    # Format: C8_f{f}_beta{beta}_theta{theta}_seed{seed}
    params = sim_id.split('_')
    f_val = float(params[1][1:])
    beta_val = float(params[2][4:])
    theta_deg = float(params[3][5:])
    seed_val = int(params[4][4:])

    # Convert theta to radians for calculations
    theta_rad = np.deg2rad(theta_deg)

    # Magnetic field configuration
    # B = B0 * (cos(theta), 0, sin(theta))
    # For isothermal MHD: B0^2/8π = β * c_s^2 * ρ0
    # We normalize such that B0 = 1, then β sets the field strength relative to thermal

    # Grid configuration
    nx1 = N1
    nx2 = N2
    nx3 = N3

    # Domain
    x1_min = 0.0
    x1_max = L1
    x2_min = -L2/2
    x2_max = L2/2
    x3_min = -L3/2
    x3_max = L3/2

    # Time configuration
    t_end = 3.0  # Run long enough to capture fragmentation
    nstep = 3000

    # Generate ATHENA++ input file
    config = {
        "problem": "mhd",
        "radiation": "no",
        "geometry": "cartesian",
        "x1min": x1_min,
        "x1max": x1_max,
        "x2min": x2_min,
        "x2max": x2_max,
        "x3min": x3_min,
        "x3max": x3_max,
        "nx1": nx1,
        "nx2": nx2,
        "nx3": nx3,

        "time": {
            "t_end": t_end,
            "nstep": nstep,
            "dt": 0.001,  # Will be CFL-limited
            "courant": 0.3,
        },

        "mhd": {
            "gamma": 1.0,  # Isothermal
            "cfl": 0.3,
        },

        "hydro": {
            "problem": "linear_wave",
            "refinement": "uniform",
            "tc": 0.001,
        },

        "field": {
            "problem": "uniform",
            "b0": {
                "b1": np.cos(theta_rad),
                "b2": 0.0,
                "b3": np.sin(theta_rad),
            },
        },

        "outputs": {
            "dt": 0.1,
            "summary": {
                "dt": 0.1,
            },
        },
    }

    # Add initial condition for filament
    config["hydro"]["problem"] = "filament"
    config["hydro"]["filament"] = {
        "mass_to_jeans": f_val,  # f = M_line/M_crit
        "beta": beta_val,           # Plasma beta
        "mach": 1.0,
        "perturbation": "random",
        "perturbation_amplitude": 0.01,
        "random_seed": seed_val,
    }

    return config

# =============================================================================
# SIMULATION JOB GENERATION
# =============================================================================

def generate_simulation_list():
    """Generate list of all simulations to run."""

    simulations = []

    for f in F_VALUES:
        for beta in BETA_VALUES:
            for theta in THETA_DEG:
                for seed in SEEDS:
                    sim_id = f"C8_f{f}_beta{beta}_theta{theta}_seed{seed}"
                    simulations.append({
                        'sim_id': sim_id,
                        'f': f,
                        'beta': beta,
                        'theta': theta,
                        'seed': seed,
                        'config': generate_athena_config(sim_id),
                    })

    return simulations

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""

    print("="*70)
    print(f"CAMPAIGN 8: Mixed Field Geometry λ/W Calibration")
    print("="*70)
    print()

    print(f"Objective: Quantify λ/W(θ) for oblique B-fields")
    print(f"Total simulations: {len(F_VALUES) * len(BETA_VALUES) * len(THETA_DEG) * len(SEEDS)}")
    print(f"Parameters:")
    print(f"  f = {F_VALUES}")
    print(f"  β = {BETA_VALUES}")
    print(f"  θ = {THETA_DEG}°")
    print(f"  Seeds = {SEEDS}")
    print()

    # Generate simulation list
    simulations = generate_simulation_list()

    print(f"Generated {len(simulations)} simulation configurations")
    print()

    # Save specification
    spec_file = f"{OUTPUT_BASE}/campaign_specification.json"
    os.makedirs(OUTPUT_BASE, exist_ok=True)

    spec_data = {
        "campaign_id": CAMPAIGN_ID,
        "campaign_name": CAMPAIGN_NAME,
        "date": datetime.now().isoformat(),
        "objective": "Quantify λ/W(θ) for oblique B-fields to determine mixing fraction needed",
        "n_simulations": len(simulations),
        "parameters": {
            "f_values": F_VALUES,
            "beta_values": BETA_VALUES,
            "theta_degrees": THETA_DEG,
            "seeds": SEEDS,
        },
        "domain": {
            "n1": N1,
            "n2": N2,
            "n3": N3,
            "l1": L1,
            "l2": L2,
            "l3": L3,
        },
        "simulations": [
            {
                'sim_id': s['sim_id'],
                'f': s['f'],
                'beta': s['beta'],
                'theta': s['theta'],
                'seed': s['seed'],
            }
            for s in simulations
        ],
    }

    with open(spec_file, 'w') as f:
        json.dump(spec_data, f, indent=2)

    print(f"Specification saved to: {spec_file}")
    print()

    # Create runner script
    runner_script = f"{OUTPUT_BASE}/run_campaign_8.py"
    with open(runner_script, 'w') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('"""')
        f.write(f'Campaign 8 Runner Script')
        f.write(f'Generated: {datetime.now().isoformat()}\n')
        f.write('"""\n\n')
        f.write('import sys\n')
        f.write('import subprocess\n')
        f.write('import json\n\n')
        f.write('def run_simulation(sim_config):\n')
        f.write('    """Run a single ATHENA++ simulation."""\n')
        f.write('    sim_id = sim_config["sim_id"]\n')
        f.write('    print(f"Running {sim_id}...")\n\n')
        f.write('    # ATHENA++ command\n')
        f.write('    athena_cmd = [\n')
        f.write('        "athena",\n')
        f.write('        f"-i", sim_config["config_file"],\n')
        f.write('        f"-o", f"{OUTPUT_BASE}/output/{sim_id}",\n')
        f.write('    ]\n\n')
        f.write('    # Run simulation\n')
        f.write('    result = subprocess.run(athena_cmd, capture_output=True, text=True)\n')
        f.write('    \n')
        f.write('    if result.returncode != 0:\n')
        f.write('        print(f"ERROR in {sim_id}: {result.stderr}")\n')
        f.write('        return False\n')
        f.write('    \n')
        f.write('    print(f"Completed {sim_id}")\n')
        f.write('    return True\n\n')
        f.write('\n')
        f.write('if __name__ == "__main__":\n')
        f.write(f'    spec_file = "{spec_file}"\n')
        f.write('    \n')
        f.write('    with open(spec_file) as f:\n')
        f.write('        spec = json.load(f)\n')
        f.write('    \n')
        f.write('    print(f"Campaign 8: {spec["n_simulations"]} simulations")\n')
        f.write('    print()\n')
        f.write('    \n')
        f.write('    # Create output directory\n')
        f.write(f'    os.makedirs("{OUTPUT_BASE}/output", exist_ok=True)\n')
        f.write('    \n')
        f.write('    # Run simulations\n')
        f.write('    success_count = 0\n')
        f.write('    for sim in spec["simulations"]:\n')
        f.write('        if run_simulation(sim):\n')
        f.write('            success_count += 1\n')
        f.write('    \n')
        f.write('    print(f"\\nCompleted {success_count}/{len(spec["simulations"])} simulations")\n')

    os.chmod(runner_script, 0o755)
    print(f"Runner script created: {runner_script}")
    print()

    # Create ray cluster submission script
    ray_script = f"{OUTPUT_BASE}/submit_to_ray.sh"
    with open(ray_script, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('#\n')
        f.write('# Submit Campaign 8 to ray cluster\n')
        f.write(f'# Generated: {datetime.now().isoformat()}\n')
        f.write('#\n')
        f.write('module load astra/athena++\n')
        f.write('module load ray\n')
        f.write('\n')
        f.write(f'cd {OUTPUT_BASE}\n')
        f.write('\n')
        f.write('# Activate conda environment\n')
        f.write('conda activate astra\n')
        f.write('\n')
        f.write('# Run campaign on 200 CPUs\n')
        f.write('python -m ray.execute --num-cpus 200 run_campaign_8.py\n')
        f.write('\n')
        f.write('echo "Campaign 8 completed"\n')

    os.chmod(ray_script, 0o755)
    print(f"Ray submission script: {ray_script}")
    print()

    print("="*70)
    print("CAMPAIGN 8 SPECIFICATION COMPLETE")
    print("="*70)
    print()
    print(f"Specification file: {spec_file}")
    print(f"Runner script: {runner_script}")
    print(f"Ray submission: {ray_script}")
    print()
    print("Next steps:")
    print("1. Review specification")
    print("2. Generate ATHENA++ input files (python generate_inputs.py)")
    print("3. Submit to ray cluster")
    print("4. Monitor progress")
    print("5. Analyze results (python analyze_results.py)")
    print()

if __name__ == "__main__":
    main()
