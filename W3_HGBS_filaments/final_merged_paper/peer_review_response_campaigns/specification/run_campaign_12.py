#!/usr/bin/env python3
"""
Campaign 12: DTC Boundary Reassessment
=======================================

Resolves the question: Do corrected DTC results shift the three-regime framework?

Remaps the stable-unstable boundary with:
1. Corrected timeout handling (6 hours wall-clock, not 600s)
2. Extended M range
3. Focus on β = 0.3 region where artifacts occurred

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

CAMPAIGN_ID = "C12_Refined_DTC"
CAMPAIGN_NAME = "Refined DTC with Extended Coverage"

# Parameter space - extended M range
MACH_VALUES = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
F_VALUES = [1.2, 1.4, 1.6, 1.8, 2.0, 2.2]
BETA_VALUES = [0.3]  # Focus on β = 0.3 region where artifacts occurred
SEEDS = [42, 137, 314, 527, 816]  # Random seeds for ensemble

# Grid dimensions
N1 = 256  # Longitudinal (smaller domain for DTC mapping)
N2 = 128  # Transverse width
N3 = 128  # Transverse height

# Domain size
L1 = 8.0   # Longitudinal (in units of lambda_J)
L2 = 1.0   # Transverse width
L3 = 1.0   # Transverse height

# Time configuration - corrected timeout
WALLCLOCK_TIMEOUT = 21600  # 6 hours in seconds (corrected from 600s)
T_END = 5.0                # Maximum simulation time

# Output configuration
OUTPUT_BASE = "/data/peer_response_runs/C12"
SNAPSHOT_INTERVAL = 0.5

# =============================================================================
# ATHENA++ PROBLEM GENERATION
# =============================================================================

def generate_athena_config(sim_id):
    """Generate ATHENA++ problem configuration for one simulation."""

    # Parse sim_id to extract parameters
    # Format: C12_f{f}_M{M}_beta{beta}_seed{seed}
    params = sim_id.split('_')
    f_val = float(params[1][1:])
    M_val = float(params[2][1:])
    beta_val = float(params[3][4:])
    seed_val = int(params[4][4:])

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
    nstep = 5000

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
            "t_end": T_END,
            "nstep": nstep,
            "dt": 0.001,
            "courant": 0.3,
            "wallclock_timeout": WALLCLOCK_TIMEOUT,  # Corrected timeout
        },

        "mhd": {
            "gamma": 1.0,  # Isothermal
            "cfl": 0.3,
        },

        "hydro": {
            "problem": "filament",
            "refinement": "uniform",
            "tc": 0.001,
        },

        "field": {
            "problem": "longitudinal_uniform",
            "b0": {
                "b1": 1.0,  # Longitudinal field
                "b2": 0.0,
                "b3": 0.0,
            },
        },

        "outputs": {
            "dt": SNAPSHOT_INTERVAL,
            "summary": {
                "dt": SNAPSHOT_INTERVAL,
            },
        },
    }

    # Add initial condition for filament
    config["hydro"]["filament"] = {
        "mass_to_jeans": f_val,
        "beta": beta_val,
        "mach": M_val,
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
        for M in MACH_VALUES:
            for beta in BETA_VALUES:
                for seed in SEEDS:
                    sim_id = f"C12_f{f}_M{M}_beta{beta}_seed{seed}"
                    simulations.append({
                        'sim_id': sim_id,
                        'f': f,
                        'M': M,
                        'beta': beta,
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
    print(f"CAMPAIGN 12: Refined DTC with Extended Coverage")
    print("="*70)
    print()

    print(f"Objective: Remap stable-unstable boundary with corrected timeout")
    print(f"and assess impact on three-regime framework")
    print()
    print(f"Focus on β = 0.3 region where artifacts occurred")
    print()
    print(f"Total simulations: {len(F_VALUES) * len(MACH_VALUES) * len(BETA_VALUES) * len(SEEDS)}")
    print(f"Parameters:")
    print(f"  f = {F_VALUES}")
    print(f"  M = {MACH_VALUES} (extended range)")
    print(f"  β = {BETA_VALUES}")
    print(f"  Seeds = {SEEDS}")
    print()
    print(f"CRITICAL FIX:")
    print(f"  Wall-clock timeout: {WALLCLOCK_TIMEOUT}s (6 hours)")
    print(f"  Previous value: 600s (incorrect)")
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
        "objective": "Remap stable-unstable boundary with corrected timeout handling",
        "n_simulations": len(simulations),
        "timeout_correction": {
            "previous_value": 600,  # seconds
            "corrected_value": WALLCLOCK_TIMEOUT,  # seconds (6 hours)
            "reason": "6-hour wall-clock timeout, not 600s simulation time",
        },
        "parameters": {
            "f_values": F_VALUES,
            "mach_values": MACH_VALUES,
            "beta_values": BETA_VALUES,
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
                'M': s['M'],
                'beta': s['beta'],
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
    runner_script = f"{OUTPUT_BASE}/run_campaign_12.py"
    with open(runner_script, 'w') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('"""')
        f.write(f'Campaign 12 Runner Script')
        f.write(f'Generated: {datetime.now().isoformat()}\n')
        f.write('"""\n\n')
        f.write('import sys\n')
        f.write('import subprocess\n')
        f.write('import json\n')
        f.write('import signal\n')
        f.write('import time\n\n')
        f.write('def timeout_handler(signum, frame):\n')
        f.write('    raise TimeoutError("Simulation exceeded wall-clock timeout")\n\n')
        f.write('def run_simulation(sim_config):\n')
        f.write('    """Run a single ATHENA++ simulation with timeout."""\n')
        f.write('    sim_id = sim_config["sim_id"]\n')
        f.write('    print(f"Running {sim_id}...")\n\n')
        f.write('    # Set wall-clock timeout\n')
        f.write(f'    signal.signal(signal.SIGALRM, timeout_handler)\n')
        f.write(f'    signal.alarm({WALLCLOCK_TIMEOUT})\n\n')
        f.write('    try:\n')
        f.write('        # ATHENA++ command\n')
        f.write('        athena_cmd = [\n')
        f.write('            "athena",\n')
        f.write('            f"-i", sim_config["config_file"],\n')
        f.write('            f"-o", f"{OUTPUT_BASE}/output/{sim_id}",\n')
        f.write('        ]\n\n')
        f.write('        # Run simulation\n')
        f.write('        result = subprocess.run(athena_cmd, capture_output=True, text=True)\n')
        f.write('        \n')
        f.write('        if result.returncode != 0:\n')
        f.write('            print(f"ERROR in {sim_id}: {result.stderr}")\n')
        f.write('            return False\n')
        f.write('        \n')
        f.write('        print(f"Completed {sim_id}")\n')
        f.write('        return True\n')
        f.write('    except TimeoutError:\n')
        f.write('        print(f"TIMEOUT in {sim_id} after {WALLCLOCK_TIMEOUT}s")\n')
        f.write('        return "TIMEOUT"\n')
        f.write('    finally:\n')
        f.write('        signal.alarm(0)  # Cancel timeout\n\n')
        f.write('\n')
        f.write('if __name__ == "__main__":\n')
        f.write(f'    spec_file = "{spec_file}"\n')
        f.write('    \n')
        f.write('    with open(spec_file) as f:\n')
        f.write('        spec = json.load(f)\n')
        f.write('    \n')
        f.write('    print(f"Campaign 12: {spec["n_simulations"]} simulations")\n')
        f.write('    print()\n')
        f.write('    \n')
        f.write('    # Create output directory\n')
        f.write(f'    os.makedirs("{OUTPUT_BASE}/output", exist_ok=True)\n')
        f.write('    \n')
        f.write('    # Run simulations\n')
        f.write('    success_count = 0\n')
        f.write('    timeout_count = 0\n')
        f.write('    for sim in spec["simulations"]:\n')
        f.write('        result = run_simulation(sim)\n')
        f.write('        if result == True:\n')
        f.write('            success_count += 1\n')
        f.write('        elif result == "TIMEOUT":\n')
        f.write('            timeout_count += 1\n')
        f.write('    \n')
        f.write('    print(f"\\nCompleted: {success_count} successful, {timeout_count} timeouts")\n')
        f.write('    print(f"Total: {success_count + timeout_count}/{len(spec["simulations"])}")\n')

    os.chmod(runner_script, 0o755)
    print(f"Runner script created: {runner_script}")
    print()

    # Create ray cluster submission script
    ray_script = f"{OUTPUT_BASE}/submit_to_ray.sh"
    with open(ray_script, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('#\n')
        f.write('# Submit Campaign 12 to ray cluster\n')
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
        f.write('python -m ray.execute --num-cpus 200 run_campaign_12.py\n')
        f.write('\n')
        f.write('echo "Campaign 12 completed"\n')

    os.chmod(ray_script, 0o755)
    print(f"Ray submission script: {ray_script}")
    print()

    print("="*70)
    print("CAMPAIGN 12 SPECIFICATION COMPLETE")
    print("="*70)
    print()
    print(f"Specification file: {spec_file}")
    print(f"Runner script: {runner_script}")
    print(f"Ray submission: {ray_script}")
    print()
    print("Key questions:")
    print("- Does extended M range shift the stability boundary?")
    print("- Does corrected timeout remove artifacts at β = 0.3?")
    print("- Does three-regime framework remain valid?")
    print()

if __name__ == "__main__":
    main()
