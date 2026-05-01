#!/usr/bin/env python3
"""
Ray-based Athena++ Simulation Launcher
Peer Review Validation Campaign - Targeted Re-runs

Launches 25 MHD simulations with extended (6-hour) timeouts using Ray distributed task scheduler.
Optimized for external computer with 200 CPUs (4 concurrent simulations x 16 MPI ranks each).
"""

import ray
import json
import subprocess
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# CRITICAL: 6-hour timeout in seconds
TIMEOUT_SECONDS = 21600
MPI_RANKS_PER_SIM = 16
MAX_CONCURRENT = 4

def load_run_list(run_list_path: str) -> Dict:
    """Load simulation specifications from JSON file."""
    with open(run_list_path, 'r') as f:
        return json.load(f)

def create_athena_input(run_spec: Dict, template_path: str, output_dir: str) -> str:
    """
    Generate Athena++ input file from template for a specific run.

    Parameters:
    -----------
    run_spec : dict
        Simulation specification from run_list.json
    template_path : str
        Path to Athena++ input file template
    output_dir : str
        Directory to write the input file

    Returns:
    --------
    input_file_path : str
        Path to generated input file
    """
    with open(template_path, 'r') as f:
        template = f.read()

    # Replace template variables
    config = template.replace("{{RUN_ID}}", run_spec['run_id'])
    config = config.replace("{{F}}", str(run_spec['f']))
    config = config.replace("{{BETA}}", str(run_spec['beta']))
    config = config.replace("{{MACH}}", str(run_spec['mach']))
    config = config.replace("{{SEED}}", str(run_spec['seed']))
    config = config.replace("{{NX1}}", str(run_spec['nx1']))
    config = config.replace("{{NX2}}", str(run_spec['nx2']))
    config = config.replace("{{NX3}}", str(run_spec['nx3']))

    # Write input file
    input_file_path = os.path.join(output_dir, f"athena_input_{run_spec['run_id']}.dat")
    with open(input_file_path, 'w') as f:
        f.write(config)

    return input_file_path

def run_single_simulation(run_spec: Dict, athena_binary: str, template_path: str, work_dir: str) -> Dict:
    """
    Execute a single Athena++ simulation with timeout.

    Parameters:
    -----------
    run_spec : dict
        Simulation specification
    athena_binary : str
        Path to Athena++ executable
    template_path : str
        Path to input file template
    work_dir : str
        Working directory for simulation

    Returns:
    --------
    result : dict
        Status dictionary with keys: run_id, status, t_frag, wall_time_seconds, etc.
    """
    run_id = run_spec['run_id']
    print(f"[{run_id}] Starting simulation...")

    # Create simulation directory
    sim_dir = os.path.join(work_dir, run_id)
    os.makedirs(sim_dir, exist_ok=True)

    # Generate input file
    input_file = create_athena_input(run_spec, template_path, sim_dir)

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
        # Look for t_frag in history output or log files
        history_file = os.path.join(sim_dir, f"{run_id}_hst.dat")

        if os.path.exists(history_file):
            # Parse history file to find t_frag
            with open(history_file, 'r') as f:
                lines = f.readlines()

            # Check for runaway collapse (dt_min < 1e-8)
            for line in reversed(lines[-100:]):  # Check last 100 lines
                if '#' not in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        final_time = float(parts[1])  # Time in code units
                        dt_min = float(parts[-1])     # Minimum timestep
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

    except subprocess.TimeoutExpired:
        wall_time = TIMEOUT_SECONDS
        status = "TIMEOUT"
        final_time = 0.0
        print(f"[{run_id}] Timed out after {TIMEOUT_SECONDS} seconds")

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
        "resolution": run_spec['resolution'],
        "status": status,
        "t_frag": t_frag if t_frag else final_time,
        "t_frag_units": "t_J",
        "t_final": final_time if final_time else 0.0,
        "dt_min": dt_min if dt_min else 0.0,
        "wall_time_seconds": wall_time,
        "mpi_ranks": MPI_RANKS_PER_SIM,
        "n_core_particles": 1 if status == "FRAG" else 0
    }

    # Write status file
    status_file = os.path.join(sim_dir, f"status_{run_id}.json")
    with open(status_file, 'w') as f:
        json.dump(result_dict, f, indent=2)

    # Copy to central status directory
    central_status_dir = os.path.join(os.path.dirname(work_dir), "output", "status")
    os.makedirs(central_status_dir, exist_ok=True)
    central_status_file = os.path.join(central_status_dir, f"status_{run_id}.json")
    with open(central_status_file, 'w') as f:
        json.dump(result_dict, f, indent=2)

    print(f"[{run_id}] Complete: {status} in {wall_time:.1f}s")
    return result_dict

@ray.remote
def remote_run_simulation(run_spec: Dict, athena_binary: str, template_path: str, work_dir: str) -> Dict:
    """Ray remote task for running a single simulation."""
    return run_single_simulation(run_spec, athena_binary, template_path, work_dir)

def main():
    parser = argparse.ArgumentParser(description="Launch peer review validation re-runs")
    parser.add_argument("--all", action="store_true", help="Run all 25 simulations")
    parser.add_argument("--priority", type=int, choices=[1, 2],
                       help="Run only Priority 1 (DTC) or Priority 2 (Resolution)")
    parser.add_argument("--run-id", type=str, help="Run specific simulation by ID")
    parser.add_argument("--athena-binary", type=str, default="../athena_reun",
                       help="Path to Athena++ binary")
    parser.add_argument("--template", type=str, default="../simulations/athena_input_template.dat",
                       help="Path to input file template")
    parser.add_argument("--work-dir", type=str, default="../output/simulations",
                       help="Working directory for simulations")
    args = parser.parse_args()

    # Load run list
    run_list_path = "../simulations/run_list.json"
    campaign = load_run_list(run_list_path)
    all_sims = campaign['simulations']

    # Filter simulations based on arguments
    if args.run_id:
        sims_to_run = [s for s in all_sims if s['run_id'] == args.run_id]
    elif args.priority:
        sims_to_run = [s for s in all_sims if s['priority'] == args.priority]
    elif args.all:
        sims_to_run = all_sims
    else:
        print("Error: Must specify --all, --priority, or --run-id")
        sys.exit(1)

    print(f"Peer Review Validation Campaign")
    print(f"Running {len(sims_to_run)} simulations")
    print(f"Max concurrent: {MAX_CONCURRENT}")
    print(f"Timeout: {TIMEOUT_SECONDS}s ({TIMEOUT_SECONDS/3600:.1f} hours)")

    # Initialize Ray
    ray.init(ignore_reinit_error=True)

    # Create working directory
    os.makedirs(args.work_dir, exist_ok=True)

    # Check if Athena binary exists
    if not os.path.exists(args.athena_binary):
        print(f"Warning: Athena binary not found at {args.athena_binary}")
        print("Please compile Athena++ first using: cd scripts && bash compile_athena.sh")

    # Launch simulations
    results = []
    pending = []

    for sim in sims_to_run:
        # Launch remote task
        result_future = remote_run_simulation.remote(
            sim, args.athena_binary, args.template, args.work_dir
        )
        pending.append(result_future)

        # Wait if we've reached max concurrent
        while len(pending) >= MAX_CONCURRENT:
            # Check for completed tasks
            ready, pending = ray.wait(pending, num_returns=1, timeout=1.0)
            if ready:
                result = ray.get(ready[0])
                results.append(result)
                print(f"Completed {len(results)}/{len(sims_to_run)}: {result['run_id']} - {result['status']}")

    # Wait for remaining simulations
    while pending:
        ready, pending = ray.wait(pending, num_returns=1)
        result = ray.get(ready[0])
        results.append(result)
        print(f"Completed {len(results)}/{len(sims_to_run)}: {result['run_id']} - {result['status']}")

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

    # Write campaign summary
    summary = {
        "campaign_name": campaign['campaign_name'],
        "total_simulations": len(results),
        "frag_count": frag_count,
        "stable_count": stable_count,
        "timeout_count": timeout_count,
        "failed_count": failed_count,
        "results": results
    }

    summary_path = "../output/campaign_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary written to {summary_path}")
    print(f"Status files in ../output/status/")

    ray.shutdown()

if __name__ == "__main__":
    main()
