#!/usr/bin/env python3
"""
Campaign 9: Staged Fragmentation in Supercritical Regime
========================================================

Resolves the supercritical extrapolation gap by testing whether filaments
can show longitudinal beading if they start near-critical and fragment
before radial collapse dominates.

Key innovation: Use STAGED FRAGMENTATION - initialize with near-critical f,
then ramp to supercritical over time.

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

CAMPAIGN_ID = "C9_Staged_Fragmentation"
CAMPAIGN_NAME = "Staged Fragmentation in Supercritical Regime"

# Parameter space
F_INITIAL_VALUES = [0.9, 1.0, 1.1, 1.2]  # Near-critical start
F_FINAL_VALUES = [1.5, 2.0, 2.5, 3.0]    # Supercritical end
BETA_VALUES = [0.5, 1.0, 2.0]            # Representative beta values
MACH_VALUES = [1.0]                       # Fixed Mach number
SEEDS = [42, 137, 314, 527, 816]         # Random seeds for ensemble

# Grid dimensions
N1 = 512  # Longitudinal (along filament)
N2 = 64   # Transverse width
N3 = 64   # Transverse height

# Domain size
L1 = 16.0  # Longitudinal (in units of lambda_J)
L2 = 1.0   # Transverse width
L3 = 1.0   # Transverse height

# Staged evolution timing
T_START = 0.0
T_PHASE1_END = 1.2    # Evolve at f_initial until t = 1.2 t_J
T_RAMP_END = 1.5      # Ramp f to f_final over 0.3 t_J
T_FINAL = 2.0         # Evolve at f_final until t = 2.0 t_J or fragmentation

# Output configuration
OUTPUT_BASE = "/data/peer_response_runs/C9"
SNAPSHOT_INTERVAL = 0.1  # Save snapshots frequently during staged evolution

# =============================================================================
# ATHENA++ PROBLEM GENERATION
# =============================================================================

def generate_athena_config(sim_id):
    """Generate ATHENA++ problem configuration for one simulation."""

    # Parse sim_id to extract parameters
    # Format: C9_fi{fi}_ff{ff}_beta{beta}_seed{seed}
    params = sim_id.split('_')
    f_initial = float(params[1][2:])
    f_final = float(params[2][2:])
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

    # Time configuration (staged evolution)
    t_end = T_FINAL
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
            "t_end": t_end,
            "nstep": nstep,
            "dt": 0.0005,  # Will be CFL-limited
            "courant": 0.3,
        },

        "mhd": {
            "gamma": 1.0,  # Isothermal
            "cfl": 0.3,
        },

        "hydro": {
            "problem": "filament_staged",
            "refinement": "uniform",
            "tc": 0.0005,
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

        "staged_fragmentation": {
            "f_initial": f_initial,
            "f_final": f_final,
            "t_phase1_end": T_PHASE1_END,
            "t_ramp_end": T_RAMP_END,
            "ramp_type": "linear",
        },
    }

    # Add initial condition for filament
    config["hydro"]["filament"] = {
        "mass_to_jeans": f_initial,  # Start at f_initial
        "beta": beta_val,
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

    for f_initial in F_INITIAL_VALUES:
        for f_final in F_FINAL_VALUES:
            # Only include cases where f_final > f_initial
            if f_final <= f_initial:
                continue

            for beta in BETA_VALUES:
                for seed in SEEDS:
                    sim_id = f"C9_fi{f_initial}_ff{f_final}_beta{beta}_seed{seed}"
                    simulations.append({
                        'sim_id': sim_id,
                        'f_initial': f_initial,
                        'f_final': f_final,
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
    print(f"CAMPAIGN 9: Staged Fragmentation in Supercritical Regime")
    print("="*70)
    print()

    print(f"Objective: Test whether supercritical filaments can show")
    print(f"longitudinal beading if they fragment before radial collapse")
    print(f"Total simulations: {len(F_INITIAL_VALUES) * len(F_FINAL_VALUES) * len(BETA_VALUES) * len(SEEDS)}")
    print(f"Parameters:")
    print(f"  f_initial = {F_INITIAL_VALUES}")
    print(f"  f_final = {F_FINAL_VALUES}")
    print(f"  β = {BETA_VALUES}")
    print(f"  Seeds = {SEEDS}")
    print()
    print(f"Staged evolution:")
    print(f"  Phase 1: f = f_initial for t < {T_PHASE1_END} t_J")
    print(f"  Phase 2: Linear ramp to f_final from {T_PHASE1_END} to {T_RAMP_END} t_J")
    print(f"  Phase 3: f = f_final for t > {T_RAMP_END} t_J")
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
        "objective": "Test staged fragmentation: does early-time beading at near-critical f survive supercritical ramp?",
        "n_simulations": len(simulations),
        "staged_evolution": {
            "t_phase1_end": T_PHASE1_END,
            "t_ramp_end": T_RAMP_END,
            "t_final": T_FINAL,
        },
        "parameters": {
            "f_initial_values": F_INITIAL_VALUES,
            "f_final_values": F_FINAL_VALUES,
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
                'f_initial': s['f_initial'],
                'f_final': s['f_final'],
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
    runner_script = f"{OUTPUT_BASE}/run_campaign_9.py"
    with open(runner_script, 'w') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('"""')
        f.write(f'Campaign 9 Runner Script')
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
        f.write('    print(f"Campaign 9: {spec["n_simulations"]} simulations")\n')
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
        f.write('# Submit Campaign 9 to ray cluster\n')
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
        f.write('python -m ray.execute --num-cpus 200 run_campaign_9.py\n')
        f.write('\n')
        f.write('echo "Campaign 9 completed"\n')

    os.chmod(ray_script, 0o755)
    print(f"Ray submission script: {ray_script}")
    print()

    print("="*70)
    print("CAMPAIGN 9 SPECIFICATION COMPLETE")
    print("="*70)
    print()
    print(f"Specification file: {spec_file}")
    print(f"Runner script: {runner_script}")
    print(f"Ray submission: {ray_script}")
    print()
    print("Key innovation: Staged fragmentation with time-dependent f")
    print("Critical test: Does early-time beading survive supercritical ramp?")
    print()

if __name__ == "__main__":
    main()
