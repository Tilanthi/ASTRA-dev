#!/usr/bin/env python3
"""
Campaign 11: Temporal Evolution Scenario Test
=============================================

Resolves the question: Were HGBS filaments near-critical at fragmentation time?

Tests whether HGBS filaments could have fragmented at near-critical mass per
unit length, then accreted to become supercritical while preserving the
fragmentation wavelength.

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

CAMPAIGN_ID = "C11_Temporal_Evolution"
CAMPAIGN_NAME = "Temporal Evolution Scenario - Near-Critical Fragmentation"

# Accretion scenarios
ACCRETION_SCENARIOS = {
    'A': {
        'name': 'No accretion (control)',
        'f_initial': 1.0,
        'f_final': 1.0,
        't_accrete': 0.0,
    },
    'B': {
        'name': 'Slow accretion',
        'f_initial': 1.0,
        'f_final': 1.5,
        't_accrete': 5.0,  # Accrete over 5 t_J
    },
    'C': {
        'name': 'Rapid accretion',
        'f_initial': 1.0,
        'f_final': 2.0,
        't_accrete': 2.0,  # Accrete over 2 t_J
    },
    'D': {
        'name': 'Very rapid accretion',
        'f_initial': 1.0,
        'f_final': 3.0,
        't_accrete': 1.0,  # Accrete over 1 t_J
    },
}

BETA_VALUES = [0.5, 1.0, 2.0]  # Representative beta values
MACH_VALUES = [1.0]             # Fixed Mach number
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
OUTPUT_BASE = "/data/peer_response_runs/C11"

# =============================================================================
# ATHENA++ PROBLEM GENERATION
# =============================================================================

def generate_athena_config(sim_id):
    """Generate ATHENA++ problem configuration for one simulation."""

    # Parse sim_id to extract parameters
    # Format: C11_scenario{scenario}_beta{beta}_seed{seed}
    params = sim_id.split('_')
    scenario = params[1][8:]  # Extract scenario letter
    beta_val = float(params[2][4:])
    seed_val = int(params[3][4:])

    # Get scenario parameters
    scenario_params = ACCRETION_SCENARIOS[scenario]
    f_initial = scenario_params['f_initial']
    f_final = scenario_params['f_final']
    t_accrete = scenario_params['t_accrete']

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
    if t_accrete > 0:
        t_end = t_accrete + 2.0  # Run 2 t_J after accretion completes
    else:
        t_end = 3.0  # Control case: run for 3 t_J
    nstep = 4000

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
            "dt": 0.0005,
            "courant": 0.3,
        },

        "mhd": {
            "gamma": 1.0,  # Isothermal
            "cfl": 0.3,
        },

        "hydro": {
            "problem": "filament_accretion",
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
            "dt": 0.1,  # Save snapshots every 0.1 t_J
            "summary": {
                "dt": 0.1,
            },
        },

        "accretion": {
            "f_initial": f_initial,
            "f_final": f_final,
            "t_accrete": t_accrete,
            "accretion_profile": "linear",  # Linear ramp of f
        },
    }

    # Add initial condition for filament
    config["hydro"]["filament"] = {
        "mass_to_jeans": f_initial,
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

    for scenario, scenario_params in ACCRETION_SCENARIOS.items():
        for beta in BETA_VALUES:
            for seed in SEEDS:
                sim_id = f"C11_scenario{scenario}_beta{beta}_seed{seed}"
                simulations.append({
                    'sim_id': sim_id,
                    'scenario': scenario,
                    'scenario_name': scenario_params['name'],
                    'f_initial': scenario_params['f_initial'],
                    'f_final': scenario_params['f_final'],
                    't_accrete': scenario_params['t_accrete'],
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
    print(f"CAMPAIGN 11: Temporal Evolution Scenario Test")
    print("="*70)
    print()

    print(f"Objective: Test whether HGBS filaments fragmented at near-critical")
    print(f"f, then accreted to supercritical while preserving λ")
    print()
    print(f"Total simulations: {len(ACCRETION_SCENARIOS) * len(BETA_VALUES) * len(SEEDS)}")
    print()
    print(f"Accretion scenarios:")
    for scenario, params in ACCRETION_SCENARIOS.items():
        print(f"  Scenario {scenario}: {params['name']}")
        print(f"    f: {params['f_initial']} → {params['f_final']} over {params['t_accrete']} t_J")
    print()
    print(f"Other parameters:")
    print(f"  β = {BETA_VALUES}")
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
        "objective": "Test whether near-critical fragmentation wavelength survives accretion",
        "n_simulations": len(simulations),
        "accretion_scenarios": ACCRETION_SCENARIOS,
        "parameters": {
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
                'scenario': s['scenario'],
                'scenario_name': s['scenario_name'],
                'f_initial': s['f_initial'],
                'f_final': s['f_final'],
                't_accrete': s['t_accrete'],
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
    runner_script = f"{OUTPUT_BASE}/run_campaign_11.py"
    with open(runner_script, 'w') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('"""')
        f.write(f'Campaign 11 Runner Script')
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
        f.write('    print(f"Campaign 11: {spec["n_simulations"]} simulations")\n')
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
        f.write('# Submit Campaign 11 to ray cluster\n')
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
        f.write('python -m ray.execute --num-cpus 200 run_campaign_11.py\n')
        f.write('\n')
        f.write('echo "Campaign 11 completed"\n')

    os.chmod(ray_script, 0o755)
    print(f"Ray submission script: {ray_script}")
    print()

    print("="*70)
    print("CAMPAIGN 11 SPECIFICATION COMPLETE")
    print("="*70)
    print()
    print(f"Specification file: {spec_file}")
    print(f"Runner script: {runner_script}")
    print(f"Ray submission: {ray_script}")
    print()
    print("Key measurements:")
    print("- λ/W at fragmentation time")
    print("- Beading persistence during accretion")
    print("- Final density profiles")
    print("- Classification: PERSISTENT_BEADING, BEADING_MERGER, RADIAL_COLLAPSE")
    print()

if __name__ == "__main__":
    main()
