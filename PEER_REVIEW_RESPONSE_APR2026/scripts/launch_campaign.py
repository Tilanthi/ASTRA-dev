#!/usr/bin/env python3
"""
Ray-based parallel execution script for Athena++ filament spacing campaign.

This script manages the execution of Athena++ simulations using Ray for
distributed parallel processing on a 200-CPU system.

Author: ASTRA System
Date: 2026-04-23
"""

import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Ray imports
try:
    import ray
    from ray.util.queue import Queue as RayQueue
except ImportError:
    print("ERROR: Ray not installed. Install with: pip install ray")
    sys.exit(1)

# ==============================================================================
# Configuration
# ==============================================================================

# Ray configuration
RAY_CPUS = 200
MAX_CONCURRENT = 12  # Number of simultaneous simulations
MPI_RANKS_PER_SIM = 16  # MPI ranks per simulation

# Simulation configuration
TIMEOUT_SECONDS = 14400  # 4 hours per simulation
ATHENA_BINARY = "./athena_filament_pr"  # Compiled Athena++ binary

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = PROJECT_ROOT / "config"
TEMPLATE_DIR = PROJECT_ROOT / "templates"
RUNS_DIR = PROJECT_ROOT / "runs"
STATUS_DIR = PROJECT_ROOT / "status"

# ==============================================================================
# Utility Functions
# ==============================================================================

def setup_directories():
    """Create necessary directories if they don't exist."""
    RUNS_DIR.mkdir(exist_ok=True)
    STATUS_DIR.mkdir(exist_ok=True)


def load_manifest(phase_filter: Optional[List[int]] = None) -> List[Dict]:
    """Load simulation manifest from JSON file."""
    manifest_file = CONFIG_DIR / "simulation_manifest.json"

    if not manifest_file.exists():
        print(f"ERROR: Manifest file not found: {manifest_file}")
        sys.exit(1)

    with open(manifest_file, 'r') as f:
        manifest = json.load(f)

    # Filter by phase if specified
    if phase_filter:
        manifest = [sim for sim in manifest if sim['phase'] in phase_filter]

    return manifest


def get_completed_sims() -> set:
    """Get set of already completed simulation IDs."""
    completed = set()
    for status_file in STATUS_DIR.glob("*.json"):
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
                if status.get('status') in ['FRAG', 'STABLE']:
                    completed.add(status['sim_id'])
        except:
            pass
    return completed


# ==============================================================================
# Simulation Execution
# ==============================================================================

@ray.remote(num_cpus=MPI_RANKS_PER_SIM)
def run_simulation(sim: Dict, sim_dir: Path) -> Dict:
    """
    Run a single Athena++ simulation.

    Parameters
    ----------
    sim : dict
        Simulation specification from manifest
    sim_dir : Path
        Base directory for simulation runs

    Returns
    -------
    dict
        Status report for the simulation
    """
    sim_id = sim['sim_id']
    phase = sim['phase']
    sim_run_dir = sim_dir / f"phase{phase}" / sim_id

    # Create simulation directory
    sim_run_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(sim_run_dir)

    # Generate Athena++ input file from template
    input_file = generate_athena_input(sim)

    # Record start time
    start_time = time.time()

    # Run Athena++ simulation
    try:
        cmd = [
            "mpirun", "-np", str(MPI_RANKS_PER_SIM),
            str(PROJECT_ROOT / ATHENA_BINARY),
            "-i", input_file
        ]

        print(f"[{sim_id}] Starting simulation...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS
        )

        end_time = time.time()
        wall_time = end_time - start_time

        # Check if simulation completed successfully
        if result.returncode == 0:
            status = "COMPLETED"
        else:
            status = "ERROR"

    except subprocess.TimeoutExpired:
        end_time = time.time()
        wall_time = end_time - start_time
        status = "TIMEOUT"
        print(f"[{sim_id}] Timed out after {wall_time:.1f}s")

    except Exception as e:
        end_time = time.time()
        wall_time = end_time - start_time
        status = "ERROR"
        print(f"[{sim_id}] Error: {e}")

    # Write status file
    status_data = {
        "sim_id": sim_id,
        "phase": phase,
        "status": status,
        "wall_time_seconds": wall_time,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC")
    }

    status_file = STATUS_DIR / f"{sim_id}.json"
    with open(status_file, 'w') as f:
        json.dump(status_data, f, indent=2)

    print(f"[{sim_id}] Status: {status}, Wall time: {wall_time:.1f}s")

    return status_data


def generate_athena_input(sim: Dict) -> str:
    """Generate Athena++ input file from simulation parameters."""
    filename = f"athena_input_{sim['sim_id']}.dat"

    # Read template
    template_file = TEMPLATE_DIR / "athena_input_template.dat"

    with open(template_file, 'r') as f:
        template = f.read()

    # Replace parameters
    params = {
        '<SIM_ID>': sim['sim_id'],
        '<F>': str(sim['f']),
        '<BETA>': str(sim['beta']),
        '<MACH>': str(sim['mach']),
        '<SEED>': str(sim['seed']),
        '<EOS>': 'adiabatic' if sim['eos'] == 'adiabatic' else 'isothermal',
        '<GAMMA>': '5.0/3.0' if sim['eos'] == 'adiabatic' else '1.0001',
        '<BFIELD>': sim['bfield'],
        '<THETA>': str(sim.get('theta', 0.0)),
        '<PROFILE>': sim.get('profile', 'king'),
        '<RESOLUTION>': str(sim['resolution']),
        '<DOMAIN>': sim.get('domain', '8x2x2'),
    }

    for key, value in params.items():
        template = template.replace(key, value)

    # Write input file
    with open(filename, 'w') as f:
        f.write(template)

    return filename


# ==============================================================================
# Main Execution
# ==============================================================================

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Launch Athena++ filament spacing campaign using Ray"
    )
    parser.add_argument(
        '--phase',
        type=int,
        nargs='+',
        help='Phase(s) to run (1-4). Default: all phases'
    )
    parser.add_argument(
        '--sim',
        type=str,
        help='Run specific simulation by ID'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume campaign, skipping completed simulations'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all phases'
    )

    args = parser.parse_args()

    # Setup
    setup_directories()

    # Initialize Ray
    print(f"Initializing Ray with {RAY_CPUS} CPUs...")
    ray.init(num_cpus=RAY_CPUS, ignore_reinit_error=True)

    # Load manifest
    phase_filter = None
    if args.phase:
        phase_filter = args.phase
    elif args.all:
        phase_filter = [1, 2, 3, 4]

    manifest = load_manifest(phase_filter)

    # Filter by specific simulation if requested
    if args.sim:
        manifest = [sim for sim in manifest if sim['sim_id'] == args.sim]
        if not manifest:
            print(f"ERROR: Simulation {args.sim} not found in manifest")
            sys.exit(1)

    # Filter out completed simulations if resuming
    if args.resume:
        completed = get_completed_sims()
        print(f"Resuming: {len(completed)} simulations already completed")
        manifest = [sim for sim in manifest if sim['sim_id'] not in completed]

    print(f"\nCampaign Summary:")
    print(f"  Total simulations: {len(manifest)}")
    print(f"  Concurrent sims: {MAX_CONCURRENT}")
    print(f"  MPI ranks per sim: {MPI_RANKS_PER_SIM}")
    print(f"  Timeout per sim: {TIMEOUT_SECONDS}s ({TIMEOUT_SECONDS/3600:.1f}h)")
    print()

    if not manifest:
        print("No simulations to run. Exiting.")
        return

    # Execute simulations in batches
    remaining = manifest.copy()
    completed_sims = []

    start_time = time.time()

    while remaining:
        # Get next batch
        batch = remaining[:MAX_CONCURRENT]
        remaining = remaining[MAX_CONCURRENT:]

        print(f"\nLaunching batch of {len(batch)} simulations...")

        # Run batch in parallel
        results = ray.get([
            run_simulation.remote(sim, RUNS_DIR)
            for sim in batch
        ])

        completed_sims.extend(results)

        # Print progress
        total_completed = len(completed_sims)
        total_sims = len(manifest)
        progress = total_completed / total_sims * 100
        print(f"Progress: {total_completed}/{total_sims} ({progress:.1f}%)")

    # Shutdown Ray
    ray.shutdown()

    # Final summary
    wall_time = time.time() - start_time
    print(f"\n{'='*60}")
    print("Campaign Complete!")
    print(f"Total simulations: {len(manifest)}")
    print(f"Total wall time: {wall_time/3600:.1f} hours")
    print(f"\nNext steps:")
    print(f"  1. Check results: ls status/*.json | wc -l")
    print(f"  2. Analyze campaign: python3 scripts/analyze_campaign.py")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
