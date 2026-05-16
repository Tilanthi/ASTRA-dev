#!/usr/bin/env python3
"""
Ray-based Athena++ Simulation Launcher
IC Sensitivity Test Campaign - May 2026

Launches 48 Athena++ MHD simulations to test fragmentation wavelength
sensitivity to initial condition choice (King profile vs uniform density)
in the near-critical regime (f = 1.0-1.3).
"""

import ray
import json
import subprocess
import os
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List

# Configuration
TIMEOUT_SECONDS = 10800  # 3 hours (near-critical runs may be slow)
MPI_RANKS_PER_SIM = 16
MAX_CONCURRENT = 16  # Optimized for 200 CPU cluster

def load_run_list() -> Dict:
    """Load simulation specifications from JSON file."""
    with open('run_list.json', 'r') as f:
        return json.load(f)

def create_athena_input(run_spec: Dict, template_path: str, output_dir: str) -> str:
    """Generate Athena++ input file from template for a specific run."""
    with open(template_path, 'r') as f:
        template = f.read()

    # Replace template variables
    config = template.replace("{{RUN_ID}}", run_spec['run_id'])
    config = config.replace("{{F}}", str(run_spec['f']))
    config = config.replace("{{BETA}}", str(run_spec['beta']))
    config = config.replace("{{BETA_VALUE}}", str(run_spec['beta']))
    config = config.replace("{{MACH}}", str(run_spec['mach']))
    config = config.replace("{{SEED}}", str(run_spec['seed']))
    config = config.replace("{{NX1}}", str(run_spec['nx1']))
    config = config.replace("{{NX2}}", str(run_spec['nx2']))
    config = config.replace("{{NX3}}", str(run_spec['nx3']))
    config = config.replace("{{FOUR_PI_G}}", run_spec['four_pi_G'])

    # Select appropriate problem generator
    ic_type = run_spec.get('ic_type', 'king')
    if ic_type == 'uniform':
        pgen_name = 'filament_uniform_ic'
    else:
        pgen_name = 'filament_king_ic'

    config = config.replace("{{PROBLEM_GENERATOR}}", pgen_name)

    # Write input file
    input_file_path = os.path.join(output_dir, f"athena_input_{run_spec['run_id']}.dat")
    with open(input_file_path, 'w') as f:
        f.write(config)

    return input_file_path

def get_athena_binary(run_spec: Dict, binary_dir: str) -> str:
    """Select appropriate Athena++ binary based on IC type."""
    ic_type = run_spec.get('ic_type', 'king')
    if ic_type == 'uniform':
        return os.path.join(binary_dir, "athena_uniform")
    else:
        return os.path.join(binary_dir, "athena_king")

def run_single_simulation(run_spec: Dict, athena_binary_dir: str, template_path: str, work_dir: str) -> Dict:
    """Execute a single Athena++ simulation with timeout."""
    run_id = run_spec['run_id']
    print(f"[{run_id}] Starting simulation...")

    # Create simulation directory
    sim_dir = os.path.join(work_dir, run_id)
    os.makedirs(sim_dir, exist_ok=True)

    # Generate input file
    input_file = create_athena_input(run_spec, template_path, sim_dir)

    # Get appropriate binary
    athena_binary = get_athena_binary(run_spec, athena_binary_dir)

    # Construct MPI command
    cmd = [
        "mpirun",
        "-np", str(MPI_RANKS_PER_SIM),
        athena_binary,
        "-i", input_file
    ]

    # Launch simulation with timeout
    start_time = time.time()
    status = "RUNNING"
    t_frag = None
    dt_min = None
    final_time = None
    hdf5_count = 0

    try:
        result = subprocess.run(
            cmd,
            cwd=sim_dir,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS
        )

        wall_time = time.time() - start_time
        return_code = result.returncode

        # Parse output for fragmentation detection
        history_file = os.path.join(sim_dir, f"{run_id}.hst")

        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                lines = f.readlines()

            for line in reversed(lines[-100:]):
                if '#' not in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        final_time = float(parts[1])
                        dt_min = float(parts[-1])
                        if dt_min < 1e-8:
                            t_frag = final_time
                            status = "FRAG"
                            break

            if status == "RUNNING" and wall_time >= TIMEOUT_SECONDS * 0.95:
                status = "TIMEOUT"
                final_time = final_time if final_time else 0.0
            elif status == "RUNNING":
                status = "STABLE"
                final_time = final_time if final_time else 0.0
        else:
            status = "FAILED"
            print(f"[{run_id}] History file not found")

        # Count HDF5 outputs
        hdf5_files = [f for f in os.listdir(sim_dir) if f.endswith('.hdf5')]
        hdf5_count = len(hdf5_files)

    except subprocess.TimeoutExpired:
        wall_time = TIMEOUT_SECONDS
        status = "TIMEOUT"
        final_time = 0.0
        print(f"[{run_id}] Timed out after {TIMEOUT_SECONDS} seconds (3 hours)")

    except Exception as e:
        wall_time = time.time() - start_time
        status = "FAILED"
        print(f"[{run_id}] Failed with error: {str(e)}")

    # Create status dictionary
    result_dict = {
        "run_id": run_id,
        "f": run_spec['f'],
        "beta": run_spec['beta'],
        "mach": run_spec['mach'],
        "seed": run_spec['seed'],
        "ic_type": run_spec.get('ic_type', 'king'),
        "status": status,
        "t_frag": t_frag if t_frag else final_time,
        "t_frag_units": "t_J",
        "t_final": final_time if final_time else 0.0,
        "dt_min": dt_min if dt_min else 0.0,
        "wall_time_seconds": wall_time,
        "mpi_ranks": MPI_RANKS_PER_SIM,
        "hdf5_snapshots": hdf5_count,
        "pgen": run_spec.get('ic_type', 'king')
    }

    # Write status file
    status_file = os.path.join(sim_dir, f"status_{run_id}.json")
    with open(status_file, 'w') as f:
        json.dump(result_dict, f, indent=2)

    # Copy to central status directory
    central_status_dir = os.path.join("output", "status")
    os.makedirs(central_status_dir, exist_ok=True)
    central_status_file = os.path.join(central_status_dir, f"status_{run_id}.json")
    with open(central_status_file, 'w') as f:
        json.dump(result_dict, f, indent=2)

    print(f"[{run_id}] Complete: {status} in {wall_time/60:.1f} minutes")
    return result_dict

@ray.remote
def remote_run_simulation(run_spec: Dict, athena_binary_dir: str, template_path: str, work_dir: str) -> Dict:
    """Ray remote task for running a single simulation."""
    return run_single_simulation(run_spec, athena_binary_dir, template_path, work_dir)

def main():
    parser = argparse.ArgumentParser(description="Launch IC sensitivity test campaign")
    parser.add_argument("--athena-bin-dir", type=str, default="../athena/bin",
                       help="Directory containing Athena++ binaries")
    parser.add_argument("--template", type=str, default="athena_input_template.dat",
                       help="Path to input file template")
    parser.add_argument("--work-dir", type=str, default="output/simulations",
                       help="Working directory for simulations")
    parser.add_argument("--all", action="store_true",
                       help="Run all 48 simulations")
    parser.add_argument("--king-only", action="store_true",
                       help="Run only King profile IC simulations (24)")
    parser.add_argument("--uniform-only", action="store_true",
                       help="Run only uniform density IC simulations (24)")
    parser.add_argument("--test", action="store_true",
                       help="Run 2 test simulations first")
    args = parser.parse_args()

    # Load run list
    campaign = load_run_list()
    all_sims = campaign['simulations']

    # Filter simulations based on command line options
    if args.king_only:
        all_sims = [s for s in all_sims if s.get('ic_type', 'king') == 'king']
        print("Running King profile IC simulations only (24 total)")
    elif args.uniform_only:
        all_sims = [s for s in all_sims if s.get('ic_type', 'king') == 'uniform']
        print("Running uniform density IC simulations only (24 total)")
    elif args.test:
        # Run 2 test simulations (one of each IC type)
        king_test = [s for s in all_sims if s.get('ic_type', 'king') == 'king'][0]
        unif_test = [s for s in all_sims if s.get('ic_type', 'king') == 'uniform'][0]
        all_sims = [king_test, unif_test]
        print("Running 2 test simulations (one King IC, one Uniform IC)")
    elif not args.all:
        print("Error: Must specify --all, --king-only, --uniform-only, or --test")
        sys.exit(1)

    print(f"\nIC Sensitivity Test Campaign")
    print(f"Running {len(all_sims)} simulations")
    print(f"Max concurrent: {MAX_CONCURRENT}")
    print(f"Timeout: {TIMEOUT_SECONDS}s ({TIMEOUT_SECONDS/3600:.1f} hours)")
    print(f"Parameter space: f=1.00-1.30, beta=0.3-1.0, M=1.0-2.0")
    print(f"IC types: King profile, Uniform density")

    # Initialize Ray
    ray.init(ignore_reinit_error=True)

    # Create working directory
    os.makedirs(args.work_dir, exist_ok=True)

    # Check if Athena binaries exist
    king_binary = os.path.join(args.athena_bin_dir, "athena_king")
    uniform_binary = os.path.join(args.athena_bin_dir, "athena_uniform")

    if not os.path.exists(king_binary):
        print(f"Warning: King IC binary not found at {king_binary}")
        print("You may need to compile Athena++ with filament_king_ic.cpp")

    if not os.path.exists(uniform_binary):
        print(f"Warning: Uniform IC binary not found at {uniform_binary}")
        print("You may need to compile Athena++ with filament_uniform_ic.cpp")

    # Launch simulations
    results = []
    pending = []

    for sim in all_sims:
        result_future = remote_run_simulation.remote(
            sim, args.athena_bin_dir, args.template, args.work_dir
        )
        pending.append(result_future)

    print(f"\nLaunched {len(pending)} simulations")

    # Wait for all simulations to complete
    while pending:
        ready, pending = ray.wait(pending, num_returns=1)
        result = ray.get(ready[0])
        results.append(result)
        frag_count = sum(1 for r in results if r['status'] == 'FRAG')
        print(f"Completed {len(results)}/{len(all_sims)}: {result['run_id']} - {result['status']} (FRAG count: {frag_count})")

    # Summary
    print(f"\nCampaign Complete!")
    print(f"Total simulations: {len(results)}")
    frag_count = sum(1 for r in results if r['status'] == 'FRAG')
    stable_count = sum(1 for r in results if r['status'] == 'STABLE')
    timeout_count = sum(1 for r in results if r['status'] == 'TIMEOUT')
    failed_count = sum(1 for r in results if r['status'] == 'FAILED')

    print(f"FRAG: {frag_count}")
    print(f"STABLE: {stable_count}")
    print(f"TIMEOUT: {timeout_count}")
    print(f"FAILED: {failed_count}")

    # Breakdown by IC type
    king_results = [r for r in results if r.get('ic_type', 'king') == 'king']
    unif_results = [r for r in results if r.get('ic_type', 'king') == 'uniform']

    print(f"\nBy IC type:")
    print(f"King IC: {len(king_results)} simulations, {sum(1 for r in king_results if r['status'] == 'FRAG')} FRAG")
    print(f"Uniform IC: {len(unif_results)} simulations, {sum(1 for r in unif_results if r['status'] == 'FRAG')} FRAG")

    # Write campaign summary
    summary = {
        "campaign_name": campaign['campaign_name'],
        "total_simulations": len(results),
        "frag_count": frag_count,
        "stable_count": stable_count,
        "timeout_count": timeout_count,
        "failed_count": failed_count,
        "king_ic_frag": sum(1 for r in king_results if r['status'] == 'FRAG'),
        "uniform_ic_frag": sum(1 for r in unif_results if r['status'] == 'FRAG'),
        "results": results
    }

    summary_path = "output/campaign_summary.json"
    os.makedirs("output", exist_ok=True)
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary written to {summary_path}")
    print(f"Status files in output/status/")
    print(f"\nNext step: Run python3 analyze_lambda_W.py to measure fragmentation wavelengths")

    ray.shutdown()

if __name__ == "__main__":
    main()
