#!/usr/bin/env python3
"""
Run Transition Mapping Campaign using Ray for distributed execution
Usage: python run_campaign.py [--num-workers N]
"""

import ray
import os
import subprocess
import json
from pathlib import Path
import time
from datetime import datetime

# Configuration
ATHENA_BINARY = "/path/to/athena/bin/athena"  # UPDATE THIS PATH
SIMULATION_BASE = "/path/to/simulations/transition_mapping_campaign_apr2026"  # UPDATE THIS
NUM_WORKERS_DEFAULT = 200  # Adjust based on your cluster

@ray.remote
def run_athena_simulation(sim_config, athena_binary):
    """
    Run a single Athena++ simulation
    """
    sim_name = sim_config['run_id']
    config_dir = sim_config['config_dir']

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting: {sim_name}")

    start_time = time.time()

    try:
        # Change to simulation directory
        os.chdir(config_dir)

        # Run Athena++
        result = subprocess.run(
            [athena_binary, "-i", "athena_input.dat"],
            capture_output=True,
            text=True,
            timeout=14400  # 4 hour timeout per simulation
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Completed: {sim_name} ({elapsed:.1f}s)")
            return {
                'run_id': sim_name,
                'status': 'completed',
                'elapsed_time': elapsed,
                'returncode': result.returncode
            }
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] FAILED: {sim_name}")
            return {
                'run_id': sim_name,
                'status': 'failed',
                'elapsed_time': elapsed,
                'returncode': result.returncode,
                'stderr': result.stderr[-500:]  # Last 500 chars of stderr
            }

    except subprocess.TimeoutExpired:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] TIMEOUT: {sim_name}")
        return {
            'run_id': sim_name,
            'status': 'timeout',
            'elapsed_time': 14400
        }
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {sim_name} - {str(e)}")
        return {
            'run_id': sim_name,
            'status': 'error',
            'error': str(e)
        }

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run Transition Mapping Campaign")
    parser.add_argument("--num-workers", type=int, default=NUM_WORKERS_DEFAULT,
                       help="Number of Ray workers (default: 200)")
    parser.add_argument("--athena-binary", type=str, default=ATHENA_BINARY,
                       help="Path to Athena++ binary")
    parser.add_argument("--simulation-base", type=str, default=SIMULATION_BASE,
                       help="Base directory for simulations")
    parser.add_argument("--resume", action="store_true",
                       help="Resume from previous run (skip completed)")

    args = parser.parse_args()

    # Check paths
    if not os.path.exists(args.athena_binary):
        print(f"ERROR: Athena++ binary not found: {args.athena_binary}")
        print("Please update the ATHENA_BINARY path in the script.")
        return 1

    # Load manifest
    manifest_path = os.path.join(args.simulation_base, "simulation_manifest.json")
    if not os.path.exists(manifest_path):
        print(f"ERROR: Manifest not found: {manifest_path}")
        print("Please run generate_simulations.py first.")
        return 1

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    print(f"Loaded {len(manifest)} simulations from manifest")

    # Filter completed simulations if resuming
    if args.resume:
        original_count = len(manifest)
        manifest = [s for s in manifest if s.get('status') != 'completed']
        print(f"Resuming: skipping {original_count - len(manifest)} completed simulations")
        print(f"Remaining: {len(manifest)} simulations")

    if not manifest:
        print("All simulations completed!")
        return 0

    # Initialize Ray
    print(f"\nInitializing Ray with {args.num_workers} workers...")
    ray.init(num_cpus=args.num_workers)

    print(f"Ray dashboard: http://localhost:{ray.cluster_resources().get('node', 0)}")
    print(f"Submitting {len(manifest)} simulations...")
    print(f"Estimated wall time: {len(manifest) * 3 * 64 / args.num_workers / 3600:.1f} hours")
    print()

    # Submit all simulations
    start_time = time.time()

    futures = [
        run_athena_simulation.remote(sim_config, args.athena_binary)
        for sim_config in manifest
    ]

    # Wait for completion and collect results
    print("Monitoring progress...")
    completed = 0
    results = []

    while futures:
        # Wait for at least one to complete
        ready_futures, futures = ray.wait(futures, num_returns=1, timeout=10.0)

        for future in ready_futures:
            result = ray.get(future)
            results.append(result)
            completed += 1

            # Update manifest
            for sim in manifest:
                if sim['run_id'] == result['run_id']:
                    sim['status'] = result['status']
                    break

            # Save updated manifest periodically
            if completed % 10 == 0:
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)

            status_symbol = "✓" if result['status'] == 'completed' else "✗"
            print(f"[{completed}/{len(manifest)+completed}] {status_symbol} {result['run_id']}: {result['status']}")

    # Final manifest save
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Summary statistics
    total_time = time.time() - start_time
    completed_count = sum(1 for r in results if r['status'] == 'completed')
    failed_count = sum(1 for r in results if r['status'] == 'failed')

    print("\n" + "="*60)
    print("CAMPAIGN COMPLETE")
    print("="*60)
    print(f"Total simulations: {len(results)}")
    print(f"Completed: {completed_count}")
    print(f"Failed: {failed_count}")
    print(f"Total wall time: {total_time/3600:.2f} hours")
    print(f"Throughput: {len(results)/total_time*3600:.1f} simulations/hour")
    print(f"\nResults saved to: {manifest_path}")

    # Save results summary
    summary_path = os.path.join(args.simulation_base, "campaign_summary.json")
    with open(summary_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_simulations': len(results),
            'completed': completed_count,
            'failed': failed_count,
            'wall_time_hours': total_time / 3600,
            'results': results
        }, f, indent=2)

    print(f"Summary saved to: {summary_path}")

    ray.shutdown()

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
