#!/usr/bin/env python3
"""
Submit peer review response campaign to Ray cluster.

This script manages the execution of Athena++ simulations on a distributed
Ray cluster with automatic resource allocation and progress monitoring.
"""

import ray
import json
import subprocess
import time
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np


# Athena++ binary path (configure for your system)
ATHENA_BINARY = "athena_pp"

# Resource allocation per simulation
CORES_PER_SIM = 64
MEMORY_PER_SIM_GB = 200
MAX_CONCURRENT = 3  # On 200-core cluster: 200/64 ≈ 3


def initialize_ray(cluster_address: Optional[str] = None):
    """
    Initialize Ray connection to cluster.

    Parameters
    ----------
    cluster_address : str, optional
        Ray cluster address. If None, starts local Ray instance.
    """
    if cluster_address:
        print(f"Connecting to Ray cluster at: {cluster_address}")
        ray.init(address=cluster_address)
    else:
        print("Starting local Ray instance...")
        ray.init(num_cpus=200)

    # Verify connection
    resources = ray.available_resources()
    print(f"\nConnected to Ray cluster:")
    print(f"  CPUs: {resources.get('CPU', 'N/A')}")
    print(f"  Memory: {resources.get('memory', 'N/A') / 1e9:.1f} GB" if 'memory' in resources else "  Memory: N/A")
    print()


def generate_athena_config(
    config_dict: Dict[str, Any],
    output_dir: Path
) -> Path:
    """
    Generate Athena++ input file from config dict.

    Parameters
    ----------
    config_dict : dict
        Simulation configuration
    output_dir : Path
        Output directory for simulation

    Returns
    -------
    Path
        Path to generated input file
    """
    output_dir.mkdir(exist_ok=True, parents=True)

    basename = config_dict['output']['basename']
    config_file = output_dir / f"{basename}.input"

    # Write Athena++ input file format
    with open(config_file, 'w') as f:
        f.write("<job>\n")
        f.write(f"problem_id      {config_dict['job']['problem_id']}\n")
        f.write(f"output_dir      {config_dict['job']['output_dir']}\n")
        f.write("\n")

        f.write("<mesh>\n")
        f.write(f"nx1              {config_dict['mesh']['nx1']}\n")
        f.write(f"nx2              {config_dict['mesh']['nx2']}\n")
        f.write(f"nx3              {config_dict['mesh']['nx3']}\n")
        f.write(f"x1min            {config_dict['mesh']['x1min']}\n")
        f.write(f"x1max            {config_dict['mesh']['x1max']}\n")
        f.write(f"x2min            {config_dict['mesh']['x2min']}\n")
        f.write(f"x2max            {config_dict['mesh']['x2max']}\n")
        f.write(f"x3min            {config_dict['mesh']['x3min']}\n")
        f.write(f"x3max            {config_dict['mesh']['x3max']}\n")
        f.write("\n")

        f.write("<hydro>\n")
        f.write(f"gamma            {config_dict['hydro']['gamma']}\n")
        f.write("\n")

        f.write("<field>\n")
        f.write(f"B1_initial       {config_dict['field']['b1_initial']}\n")
        f.write(f"B2_initial       {config_dict['field']['b2_initial']}\n")
        f.write(f"B3_initial       {config_dict['field']['b3_initial']}\n")
        f.write("\n")

        f.write("<gravity>\n")
        f.write(f"four_pi_G        {config_dict['gravity']['four_pi_G']}\n")
        f.write("\n")

        f.write("<problem>\n")
        f.write(f"line_mass_fraction  {config_dict['filament']['line_mass_fraction']}\n")
        f.write(f"W_core            {config_dict['filament']['W_core']}\n")
        f.write(f"profile           {config_dict['filament']['profile']}\n")
        f.write(f"perturbation_amplitude  {config_dict['filament']['perturbation_amplitude']}\n")
        f.write("\n")

        f.write("<time>\n")
        f.write(f"tlim              {config_dict['time']['tlim']}\n")
        f.write(f"dt_initial        {config_dict['time']['dt_initial']}\n")
        f.write(f"dt_min            {config_dict['time']['dt_min']}\n")
        f.write(f"cfl_number        {config_dict['time']['cfl_number']}\n")
        f.write("\n")

        f.write("<output>\n")
        f.write(f"basename          {basename}\n")
        f.write(f"file_type         {config_dict['output']['file_type']}\n")
        f.write(f"dt                {config_dict['output']['dt']}\n")
        f.write(f"variable          {config_dict['output']['variables'][0]}\n")
        for var in config_dict['output']['variables'][1:]:
            f.write(f"                  {var}\n")
        f.write("\n")

        f.write("<hst>\n")
        f.write(f"file_type         {config_dict['output']['file_type']}\n")
        f.write(f"dt                {config_dict['output']['hst_dt']}\n")
        f.write(f"variable          {config_dict['output']['variables'][0]}\n")
        for var in config_dict['output']['variables'][1:]:
            f.write(f"                  {var}\n")
        f.write("\n")

    return config_file


@ray.remote(num_cpus=CORES_PER_SIM, memory=MEMORY_PER_SIM_GB * 1e9)
def run_athena_simulation(
    config_path: str,
    athena_binary: str = ATHENA_BINARY
) -> Dict[str, Any]:
    """
    Execute Athena++ simulation on remote Ray worker.

    Parameters
    ----------
    config_path : str
        Path to Athena++ input file
    athena_binary : str
        Path to Athena++ executable

    Returns
    -------
    dict
        Simulation result with status and output path
    """
    import os
    from pathlib import Path

    start_time = time.time()

    # Extract simulation info
    config_path = Path(config_path)
    sim_dir = config_path.parent
    sim_name = config_path.stem

    log_file = sim_dir / f"{sim_name}.log"

    try:
        # Build Athena++ command
        cmd = [
            athena_binary,
            '-i', str(config_path),
            f'> {log_file}',
            '2>&1'
        ]

        # Run simulation
        cmd_str = ' '.join(cmd)
        exit_code = os.system(cmd_str)

        elapsed = time.time() - start_time

        if exit_code == 0:
            # Check for expected outputs
            output_dir = Path(config_path).parent.parent / 'outputs'
            sim_outputs = list(output_dir.glob(f"{sim_name}*.h5"))

            if sim_outputs:
                return {
                    'status': 'completed',
                    'simulation': sim_name,
                    'config_file': str(config_path),
                    'log_file': str(log_file),
                    'output_dir': str(output_dir),
                    'n_outputs': len(sim_outputs),
                    'wall_time_hours': elapsed / 3600.0,
                    'exit_code': exit_code
                }
            else:
                return {
                    'status': 'completed_no_outputs',
                    'simulation': sim_name,
                    'config_file': str(config_path),
                    'log_file': str(log_file),
                    'wall_time_hours': elapsed / 3600.0,
                    'exit_code': exit_code,
                    'error': 'No output files found'
                }
        else:
            return {
                'status': 'failed',
                'simulation': sim_name,
                'config_file': str(config_path),
                'log_file': str(log_file),
                'wall_time_hours': elapsed / 3600.0,
                'exit_code': exit_code,
                'error': f'Non-zero exit code: {exit_code}'
            }

    except Exception as e:
        elapsed = time.time() - start_time
        return {
            'status': 'error',
            'simulation': sim_name,
            'config_file': str(config_path),
            'wall_time_hours': elapsed / 3600.0,
            'error': str(e)
        }


def submit_campaign(
    campaign_name: str,
    config_dir: str,
    max_concurrent: int = MAX_CONCURRENT,
    athena_binary: str = ATHENA_BINARY
) -> List[Dict[str, Any]]:
    """
    Submit campaign to Ray cluster with concurrent execution control.

    Parameters
    ----------
    campaign_name : str
        Campaign identifier
    config_dir : str
        Directory containing simulation config JSON files
    max_concurrent : int
        Maximum concurrent simulations
    athena_binary : str
        Path to Athena++ executable

    Returns
    -------
    list
        List of simulation results
    """
    config_path = Path(config_dir)
    config_files = sorted(config_path.glob('*.json'))

    if not config_files:
        raise ValueError(f"No config files found in {config_dir}")

    print(f"Submitting {campaign_name} campaign")
    print(f"  Config directory: {config_dir}")
    print(f"  Config files: {len(config_files)}")
    print(f"  Max concurrent: {max_concurrent}")
    print(f"  Athena binary: {athena_binary}")
    print()

    # Generate Athena++ input files and submit
    submission_dir = Path('submissions') / campaign_name
    submission_dir.mkdir(exist_ok=True, parents=True)

    all_results = []
    pending_configs = []

    for config_file in config_files:
        with open(config_file) as f:
            config_dict = json.load(f)

        # Generate Athena++ input file
        athena_input = generate_athena_config(config_dict, submission_dir)
        pending_configs.append(athena_input)

    print(f"Generated {len(pending_configs)} Athena++ input files")
    print(f"Submission directory: {submission_dir}")
    print()

    # Submit in batches
    completed = 0
    failed = 0
    total = len(pending_configs)

    # Active futures
    active_futures = {}
    pending_queue = pending_configs.copy()

    start_time = time.time()

    while completed + failed < total:
        # Fill up to max_concurrent
        while len(active_futures) < max_concurrent and pending_queue:
            config_file = pending_queue.pop(0)
            sim_name = config_file.stem
            print(f"[{completed+failed+1}/{total}] Starting: {sim_name}")

            future = run_athena_simulation.remote(str(config_file), athena_binary)
            active_futures[future] = {
                'config': str(config_file),
                'start_time': time.time(),
                'sim_name': sim_name
            }

        # Wait for at least one to complete
        if active_futures:
            ready_futures, _ = ray.wait(list(active_futures.keys()), num_returns=1, timeout=10.0)

            for future in ready_futures:
                try:
                    result = ray.get(future)
                    all_results.append(result)

                    sim_name = active_futures[future]['sim_name']
                    elapsed_hours = (time.time() - active_futures[future]['start_time']) / 3600.0

                    if result['status'] == 'completed':
                        completed += 1
                        print(f"  ✓ Completed: {sim_name} ({elapsed_hours:.2f}h, {result['n_outputs']} outputs)")
                    else:
                        failed += 1
                        print(f"  ✗ Failed: {sim_name} ({elapsed_hours:.2f}h) - {result.get('error', 'Unknown error')}")

                except Exception as e:
                    failed += 1
                    sim_name = active_futures[future]['sim_name']
                    print(f"  ✗ Error: {sim_name} - {e}")
                    all_results.append({
                        'status': 'error',
                        'simulation': sim_name,
                        'error': str(e)
                    })

                del active_futures[future]

        # Progress update
        wall_time = (time.time() - start_time) / 3600.0
        print(f"Progress: {completed+failed}/{total} ({(completed+failed)/total*100:.1f}%) | "
              f"Wall time: {wall_time:.2f}h | "
              f"Active: {len(active_futures)}")
        print()

    # Final summary
    wall_time = (time.time() - start_time) / 3600.0

    print("="*70)
    print("CAMPAIGN COMPLETION SUMMARY")
    print("="*70)
    print(f"Campaign: {campaign_name}")
    print(f"Total simulations: {total}")
    print(f"Completed: {completed} ({completed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"Total wall time: {wall_time:.2f} hours")

    if completed > 0:
        cpu_hours = sum(r.get('wall_time_hours', 0) * CORES_PER_SIM for r in all_results if 'wall_time_hours' in r)
        print(f"Total CPU-hours: {cpu_hours:.0f}")

    print("="*70)
    print()

    # Save results
    results_file = submission_dir / f"{campaign_name}_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'campaign': campaign_name,
            'completed': datetime.now().isoformat(),
            'wall_time_hours': wall_time,
            'total': total,
            'completed_count': completed,
            'failed_count': failed,
            'results': all_results
        }, f, indent=2)

    print(f"Results saved to: {results_file}")
    print()

    return all_results


def main():
    """Command-line interface for campaign submission."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Submit peer review response campaign to Ray cluster'
    )
    parser.add_argument(
        'campaign',
        help='Campaign name (e.g., SUPERCRITICAL_LONG)'
    )
    parser.add_argument(
        '--config-dir',
        help='Directory containing config JSON files',
        default='peer_review_simulation_configs'
    )
    parser.add_argument(
        '--concurrent',
        help='Maximum concurrent simulations',
        type=int,
        default=MAX_CONCURRENT
    )
    parser.add_argument(
        '--athena',
        help='Path to Athena++ binary',
        default=ATHENA_BINARY
    )
    parser.add_argument(
        '--ray-address',
        help='Ray cluster address (if None, starts local)',
        default=None
    )

    args = parser.parse_args()

    # Initialize Ray
    initialize_ray(args.ray_address)

    # Determine config directory for this campaign
    campaign_config_dir = Path(args.config_dir) / args.campaign.lower()

    if not campaign_config_dir.exists():
        # Try direct path
        campaign_config_dir = Path(args.config_dir) / args.campaign

    if not campaign_config_dir.exists():
        print(f"Error: Config directory not found: {campaign_config_dir}")
        print(f"Available directories:")
        base_dir = Path(args.config_dir)
        if base_dir.exists():
            for d in base_dir.iterdir():
                if d.is_dir():
                    print(f"  {d}")
        sys.exit(1)

    # Submit campaign
    try:
        results = submit_campaign(
            args.campaign,
            str(campaign_config_dir),
            max_concurrent=args.concurrent,
            athena_binary=args.athena
        )

        print("\nCampaign submission complete!")

    except Exception as e:
        print(f"\nError submitting campaign: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
