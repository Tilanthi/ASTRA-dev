#!/usr/bin/env python3
"""
Main Ray execution script for Theoretician Peer Review Response Campaign.

Runs 225 Athena++ simulations across 3 sub-campaigns:
- STV: Supercritical Transition Validation (75 sims)
- PFS: Perpendicular-Field Systematics (60 sims)
- NCRI: Near-Critical Resolution Investigation (90 sims)

Usage:
    python3 run_campaign.py
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

import ray
from ray.util.queue import Queue


# Configuration
MAX_CONCURRENT = 12      # Number of simultaneous simulations
CORES_PER_SIM = 16       # MPI ranks per simulation
TOTAL_CPUS = 220         # Total available CPUs
ATHENA_BIN = "./athena-public-version/bin/athena"
CONFIGS_DIR = Path("configs")
OUTPUTS_DIR = Path("outputs")
STATUS_FILE = Path("campaign_status.json")


def load_configs():
    """Load all configuration files."""
    configs = []

    for campaign in ['STV', 'PFS', 'NCRI']:
        campaign_dir = CONFIGS_DIR / campaign
        config_files = list(campaign_dir.glob("config_*.json"))

        for config_file in config_files:
            with open(config_file) as f:
                config = json.load(f)
                configs.append({
                    'config_file': str(config_file),
                    'campaign': campaign,
                    'metadata': config['metadata']
                })

    print(f"Loaded {len(configs)} configuration files")
    return configs


def init_campaign_status():
    """Initialize campaign status tracking."""
    if STATUS_FILE.exists():
        with open(STATUS_FILE) as f:
            return json.load(f)

    # Count configs per campaign
    counts = {}
    for campaign in ['STV', 'PFS', 'NCRI']:
        campaign_dir = CONFIGS_DIR / campaign
        counts[campaign] = len(list(campaign_dir.glob("config_*.json")))

    return {
        'start_time': datetime.now().isoformat(),
        'total_simulations': sum(counts.values()),
        'campaigns': counts,
        'status': {
            'pending': sum(counts.values()),
            'running': 0,
            'completed': 0,
            'failed': 0
        },
        'simulations': {}
    }


def save_campaign_status(status):
    """Save campaign status to file."""
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)


def update_simulation_status(sim_id, new_status, status_data):
    """Update status for a single simulation."""
    with open(STATUS_FILE) as f:
        status = json.load(f)

    if sim_id not in status['simulations']:
        status['simulations'][sim_id] = {}

    old_status = status['simulations'][sim_id].get('status', 'pending')

    # Update counters
    if old_status in status['status']:
        status['status'][old_status] -= 1

    status['simulations'][sim_id]['status'] = new_status
    status['simulations'][sim_id].update(status_data)
    status['status'][new_status] = status['status'].get(new_status, 0) + 1

    save_campaign_status(status)
    return status


@ray.remote(num_cpus=CORES_PER_SIM)
def run_athena_simulation(config_file, sim_id, campaign):
    """
    Run a single Athena++ simulation.

    Parameters
    ----------
    config_file : str
        Path to configuration JSON file
    sim_id : str
        Unique simulation identifier
    campaign : str
        Campaign name (STV, PFS, or NCRI)

    Returns
    -------
    dict
        Simulation result with status and metadata
    """
    start_time = time.time()

    # Update status to running
    update_simulation_status(sim_id, 'running', {
        'start_time': datetime.now().isoformat()
    })

    try:
        # Load config
        with open(config_file) as f:
            config = json.load(f)

        # Create output directory
        output_dir = Path(config['job']['output_dir']) / campaign
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get basename for outputs
        basename = config['output']['basename']

        # Build Athena++ command
        cmd = [
            'mpirun', '-np', str(CORES_PER_SIM),
            ATHENA_BIN,
            '-i', config_file,
            f'>/{output_dir}/{basename}.log', '2>&1'
        ]

        # Run simulation
        result = subprocess.run(
            ' '.join(cmd),
            shell=True,
            cwd=str(output_dir),
            timeout=config.get('timeout_seconds', 7200),
            capture_output=True
        )

        elapsed = time.time() - start_time

        # Classify result
        if result.returncode == 0:
            # Check if fragmented
            status_file = output_dir / f"{basename}.status.json"
            if status_file.exists():
                with open(status_file) as f:
                    sim_status = json.load(f)
                final_status = sim_status.get('classification', 'UNKNOWN')
            else:
                # Basic classification from log
                log_content = (output_dir / f"{basename}.log").read_text()
                if 'fragmentation' in log_content.lower() or 'beading' in log_content.lower():
                    final_status = 'FRAG'
                else:
                    final_status = 'STABLE'
        else:
            final_status = 'FAILED'

        # Update status to completed
        update_simulation_status(sim_id, 'completed', {
            'end_time': datetime.now().isoformat(),
            'wall_time_seconds': elapsed,
            'classification': final_status,
            'return_code': result.returncode
        })

        return {
            'sim_id': sim_id,
            'status': final_status,
            'wall_time': elapsed,
            'config_file': config_file
        }

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        update_simulation_status(sim_id, 'failed', {
            'end_time': datetime.now().isoformat(),
            'wall_time_seconds': elapsed,
            'error': 'TIMEOUT'
        })
        return {
            'sim_id': sim_id,
            'status': 'TIMEOUT',
            'wall_time': elapsed,
            'config_file': config_file
        }

    except Exception as e:
        elapsed = time.time() - start_time
        update_simulation_status(sim_id, 'failed', {
            'end_time': datetime.now().isoformat(),
            'wall_time_seconds': elapsed,
            'error': str(e)
        })
        return {
            'sim_id': sim_id,
            'status': 'ERROR',
            'wall_time': elapsed,
            'error': str(e),
            'config_file': config_file
        }


def print_status_summary(status):
    """Print summary of campaign status."""
    print("\n" + "=" * 60)
    print("CAMPAIGN STATUS SUMMARY")
    print("=" * 60)
    print(f"Start time: {status['start_time']}")
    print(f"Total simulations: {status['total_simulations']}")
    print()
    print("Status breakdown:")
    for state, count in status['status'].items():
        pct = 100 * count / status['total_simulations'] if status['total_simulations'] > 0 else 0
        bar = '█' * int(pct / 2)
        print(f"  {state:12s}: {count:4d} ({pct:5.1f}%) {bar}")
    print()

    # Per-campaign breakdown
    print("Campaign breakdown:")
    for campaign in ['STV', 'PFS', 'NCRI']:
        campaign_sims = [s for s in status['simulations'].values()
                        if s.get('campaign') == campaign]
        total = len(campaign_sims)
        if total > 0:
            completed = sum(1 for s in campaign_sims if s.get('status') == 'completed')
            print(f"  {campaign}: {completed}/{total} completed")

    print("=" * 60 + "\n")


def main():
    """Main execution function."""
    print("=" * 60)
    print("THEORETICIAN PEER REVIEW RESPONSE CAMPAIGN")
    print("=" * 60)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Total CPUs: {TOTAL_CPUS}")
    print(f"Max concurrent: {MAX_CONCURRENT}")
    print(f"Cores per sim: {CORES_PER_SIM}")
    print()

    # Initialize Ray
    print("Initializing Ray...")
    ray.init(num_cpus=TOTAL_CPUS, dashboard_port=8265)
    print("Ray dashboard: http://localhost:8265")
    print()

    # Load configurations
    print("Loading configuration files...")
    configs = load_configs()
    print()

    # Initialize status
    status = init_campaign_status()
    save_campaign_status(status)

    # Create sim_id for each config
    sim_configs = []
    for i, config in enumerate(configs):
        metadata = config['metadata']
        sim_id = f"{config['campaign']}_f{metadata['f']}_beta{metadata['beta']}_theta{metadata['theta']}_s{metadata['seed']}"
        sim_configs.append({
            'sim_id': sim_id,
            'config_file': config['config_file'],
            'campaign': config['campaign']
        })
        status['simulations'][sim_id] = {
            'campaign': config['campaign'],
            'status': 'pending'
        }
    save_campaign_status(status)

    print(f"Queued {len(sim_configs)} simulations")
    print()

    # Run simulations in batches
    print("Starting simulation execution...")
    print()

    completed = 0
    failed = 0
    results = []

    for i in range(0, len(sim_configs), MAX_CONCURRENT):
        batch = sim_configs[i:i+MAX_CONCURRENT]

        print(f"Processing batch {i//MAX_CONCURRENT + 1}/{(len(sim_configs)+MAX_CONCURRENT-1)//MAX_CONCURRENT}")
        print(f"  Simulations: {len(batch)}")

        # Submit batch
        futures = []
        for sim in batch:
            future = run_athena_simulation.remote(
                sim['config_file'],
                sim['sim_id'],
                sim['campaign']
            )
            futures.append(future)

        # Wait for completion
        batch_results = ray.get(futures)
        results.extend(batch_results)

        # Update counters
        for result in batch_results:
            if result['status'] in ['FRAG', 'STABLE', 'COMPLETED']:
                completed += 1
            else:
                failed += 1

        # Print summary
        status = load_campaign_status()
        print_status_summary(status)

        # Brief pause between batches
        if i + MAX_CONCURRENT < len(sim_configs):
            time.sleep(5)

    # Final summary
    print("\n" + "=" * 60)
    print("CAMPAIGN COMPLETED")
    print("=" * 60)
    print(f"Total simulations: {len(results)}")
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print()

    # Status breakdown
    status_counts = {}
    for result in results:
        status_counts[result['status']] = status_counts.get(result['status'], 0) + 1

    print("Final status breakdown:")
    for state, count in sorted(status_counts.items()):
        print(f"  {state}: {count}")

    print()
    print(f"End time: {datetime.now().isoformat()}")
    print()
    print("Next steps:")
    print("  1. Check outputs/ directories for simulation results")
    print("  2. Run analysis scripts:")
    print("     python3 analyze_stv.py")
    print("     python3 analyze_pfs.py")
    print("     python3 analyze_ncri.py")
    print("     python3 analyze_integrated.py")
    print()

    # Shutdown Ray
    ray.shutdown()


if __name__ == '__main__':
    main()
