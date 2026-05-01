#!/usr/bin/env python3
"""
Run Definitive 2D Transition Campaign using Ray for distributed execution
OPTIMIZED for minimal disk space usage (128³, 5 snapshots)

Usage: python run_campaign_optimized.py [--phase PHASE] [--num-workers N]
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
SIMULATION_BASE = "/path/to/simulations/definitive_transition_campaign_apr2026"  # UPDATE THIS
NUM_WORKERS_DEFAULT = 200  # Adjust based on your cluster

@ray.remote
def run_athena_simulation(sim_config, athena_binary, sim_index, total_sims):
    """
    Run a single Athena++ simulation (OPTIMIZED: 128³, faster runtime)
    """
    sim_name = sim_config['run_id']
    config_dir = sim_config['config_dir']

    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{sim_index}/{total_sims}] Starting: {sim_name}")

    start_time = time.time()

    try:
        # Change to simulation directory
        os.chdir(config_dir)

        # Run Athena++ (OPTIMIZED: 128³, faster runtime)
        result = subprocess.run(
            [athena_binary, "-i", "athena_input.dat"],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per simulation (128³ is faster)
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{sim_index}/{total_sims}] ✓ Completed: {sim_name} ({elapsed/60:.1f}min)")
            return {
                'run_id': sim_name,
                'status': 'completed',
                'elapsed_time': elapsed,
                'returncode': result.returncode
            }
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{sim_index}/{total_sims}] ✗ FAILED: {sim_name}")
            return {
                'run_id': sim_name,
                'status': 'failed',
                'elapsed_time': elapsed,
                'returncode': result.returncode,
                'stderr': result.stderr[-500:]  # Last 500 chars of stderr
            }

    except subprocess.TimeoutExpired:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{sim_index}/{total_sims}] ⏱ TIMEOUT: {sim_name}")
        return {
            'run_id': sim_name,
            'status': 'timeout',
            'elapsed_time': 3600
        }
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{sim_index}/{total_sims}] ⚠ ERROR: {sim_name} - {str(e)}")
        return {
            'run_id': sim_name,
            'status': 'error',
            'error': str(e)
        }

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run Definitive 2D Transition Campaign (OPTIMIZED)")
    parser.add_argument("--phase", type=str, default="all",
                       choices=["primary", "extended", "all"],
                       help="Campaign phase to run")
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
        print("Please run generate_simulations_optimized.py first.")
        return 1

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # Filter by phase
    if args.phase == "primary":
        manifest = [s for s in manifest if s.get('campaign_phase') == 'primary']
        print(f"Running PRIMARY phase only: {len(manifest)} simulations")
    elif args.phase == "extended":
        manifest = [s for s in manifest if s.get('campaign_phase') == 'extended']
        print(f"Running EXTENDED phase only: {len(manifest)} simulations")
    else:
        print(f"Running ALL phases: {len(manifest)} simulations")

    # Print optimization info
    print("\nOPTIMIZED CONFIGURATION:")
    print("  Resolution: 128³ (vs. 256³) → 6-10x faster per simulation")
    print("  Snapshots: 5 (t = 0,1,2,3,4 t_J) → 8x less disk")
    print("  Outputs: TAB only (no VTK) → 2x less disk")
    print("  Expected runtime: 20-30 min per simulation on 32 cores")
    print(f"  Estimated wall time: {len(manifest) * 0.4 * 32 / args.num_workers / 3600:.1f} hours")
    print()

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
    print(f"Estimated completion: {(datetime.now().timestamp() + len(manifest) * 0.4 * 32 / args.num_workers):.0f}")
    print()

    # Submit all simulations
    start_time = time.time()

    # Create progress tracking
    total_sims = len(manifest)

    futures = [
        run_athena_simulation.remote(sim_config, args.athena_binary, i+1, total_sims)
        for i, sim_config in enumerate(manifest)
    ]

    # Wait for completion and collect results
    print("Monitoring progress...")
    completed = 0
    results = []
    start_timestamp = time.time()

    while futures:
        # Wait for at least one to complete
        ready_futures, futures = ray.wait(futures, num_returns=1, timeout=30.0)

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
            if completed % 20 == 0:
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)

                # Print progress summary
                elapsed = time.time() - start_timestamp
                rate = completed / elapsed * 3600  # sims per hour
                eta = (total_sims - completed) / rate * 3600 if rate > 0 else 0
                print(f"[{completed}/{total_sims}] Progress: {completed/total_sims*100:.1f}% | Rate: {rate:.1f} sims/h | ETA: {eta/60:.1f}min")

    # Final manifest save
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Summary statistics
    total_time = time.time() - start_time
    completed_count = sum(1 for r in results if r['status'] == 'completed')
    failed_count = sum(1 for r in results if r['status'] == 'failed')

    print("\n" + "="*70)
    print("CAMPAIGN COMPLETE (OPTIMIZED)")
    print("="*70)
    print(f"Total simulations: {len(results)}")
    print(f"Completed: {completed_count}")
    print(f"Failed: {failed_count}")
    print(f"Total wall time: {total_time/3600:.2f} hours ({total_time/86400:.2f} days)")
    print(f"Throughput: {len(results)/total_time*3600:.1f} simulations/hour")
    print(f"\nOPTIMIZATION RESULTS:")
    print(f"  Actual runtime: {total_time/len(results)/60:.1f} minutes per simulation")
    print(f"  Actual disk usage: ~{completed_count * 0.13:.1f} GB ({completed_count * 0.13/1024:.2f} TB)")
    print(f"\nResults saved to: {manifest_path}")

    # Save results summary
    summary_path = os.path.join(args.simulation_base, "campaign_summary.json")
    with open(summary_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'phase': args.phase,
            'total_simulations': len(results),
            'completed': completed_count,
            'failed': failed_count,
            'wall_time_hours': total_time / 3600,
            'wall_time_days': total_time / 86400,
            'optimization': '128³, 5 snapshots, TAB only',
            'results': results
        }, f, indent=2)

    print(f"Summary saved to: {summary_path}")

    ray.shutdown()

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
