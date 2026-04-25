#!/usr/bin/env python3
"""
Monitor Ray jobs for MHD simulation campaigns.

This script provides real-time monitoring of Ray job progress,
including status tracking, resource utilization, and failure detection.

Usage:
    python monitor_jobs.py --results <results_dir>
"""

import ray
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import argparse


def load_job_list(results_dir: Path) -> List[Dict[str, Any]]:
    """Load job list from results directory."""
    job_list_file = results_dir / 'job_list.json'

    if not job_list_file.exists():
        print(f"Error: Job list file not found: {job_list_file}")
        return []

    with open(job_list_file, 'r') as f:
        return json.load(f)


def load_results(results_dir: Path) -> Dict[int, Dict[str, Any]]:
    """Load current results from results directory."""
    results_file = results_dir / 'campaign_results.json'

    if not results_file.exists():
        return {}

    with open(results_file, 'r') as f:
        results = json.load(f)

    return {r['sim_id']: r for r in results}


def check_simulation_status(sim_dir: Path) -> str:
    """Check status of a single simulation."""
    # Check for completion
    if (sim_dir / 'simulation_params.json').exists():
        with open(sim_dir / 'simulation_params.json', 'r') as f:
            params = json.load(f)
        return params.get('status', 'unknown')

    # Check for errors
    if (sim_dir / 'error.log').exists():
        return 'error'

    # Check if running
    if (sim_dir / 'athena.log').exists():
        return 'running'

    return 'pending'


def monitor_jobs(results_dir: Path, poll_interval: int = 30):
    """Monitor jobs in real-time."""
    jobs = load_job_list(results_dir)

    if not jobs:
        print("No jobs to monitor")
        return

    print(f"Monitoring {len(jobs)} jobs...")
    print(f"Poll interval: {poll_interval} seconds")
    print(f"Results directory: {results_dir}")
    print("-" * 80)

    try:
        while True:
            # Check status of all jobs
            status_counts = {'pending': 0, 'running': 0, 'completed': 0, 'failed': 0, 'error': 0}

            for job in jobs:
                sim_id = job['sim_id']
                sim_dir = results_dir / f"sim_{sim_id:04d}"

                if sim_dir.exists():
                    status = check_simulation_status(sim_dir)
                else:
                    status = 'pending'

                status_counts[status] = status_counts.get(status, 0) + 1

            # Display status
            print(f"\r[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                  f"Pending: {status_counts['pending']:3d} | "
                  f"Running: {status_counts['running']:3d} | "
                  f"Completed: {status_counts['completed']:3d} | "
                  f"Failed: {status_counts['failed']:3d} | "
                  f"Error: {status_counts['error']:3d}",
                  end='', flush=True)

            # Check if all jobs are complete
            total = len(jobs)
            completed = status_counts['completed'] + status_counts['failed'] + status_counts['error']

            if completed >= total:
                print(f"\n\nAll {total} jobs complete!")
                break

            # Wait before next poll
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")


def generate_summary_report(results_dir: Path):
    """Generate summary report of campaign results."""
    jobs = load_job_list(results_dir)

    if not jobs:
        return

    results = load_results(results_dir)

    print("\n" + "=" * 80)
    print("CAMPAIGN SUMMARY REPORT")
    print("=" * 80)

    # Status breakdown
    status_counts = {}

    for job in jobs:
        sim_id = job['sim_id']

        if sim_id in results:
            status = results[sim_id].get('status', 'unknown')
        else:
            sim_dir = results_dir / f"sim_{sim_id:04d}"
            if sim_dir.exists():
                status = check_simulation_status(sim_dir)
            else:
                status = 'pending'

        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"\nStatus Breakdown:")
    for status, count in sorted(status_counts.items()):
        pct = 100 * count / len(jobs) if jobs else 0
        print(f"  {status:15s}: {count:4d} ({pct:5.1f}%)")

    # Resource utilization (if Ray is available)
    try:
        cluster_resources = ray.cluster_resources()
        print(f"\nRay Cluster Resources:")
        print(f"  CPUs: {cluster_resources.get('CPU', 'N/A')}")
        print(f"  Memory: {cluster_resources.get('memory', 'N/A') / 1e9:.1f} GB")
    except:
        pass

    # Failed/failed jobs
    failed_jobs = [j for j in jobs if j['sim_id'] in results and results[j['sim_id']].get('status') in ['failed', 'error']]

    if failed_jobs:
        print(f"\nFailed Jobs ({len(failed_jobs)}):")
        for job in failed_jobs[:10]:  # Show first 10
            sim_id = job['sim_id']
            result = results[sim_id]
            error = result.get('error', 'Unknown error')
            print(f"  sim_{sim_id:04d}: {error}")

        if len(failed_jobs) > 10:
            print(f"  ... and {len(failed_jobs) - 10} more")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Monitor Ray MHD simulation jobs')
    parser.add_argument('--results', type=str, required=True,
                        help='Results directory containing simulation outputs')
    parser.add_argument('--poll-interval', type=int, default=30,
                        help='Polling interval in seconds (default: 30)')
    parser.add_argument('--report-only', action='store_true',
                        help='Generate summary report without monitoring')

    args = parser.parse_args()

    results_dir = Path(args.results)

    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        return

    if args.report_only:
        generate_summary_report(results_dir)
    else:
        # Initialize Ray
        try:
            ray.init(ignore_reinit_error=True)
        except:
            print("Warning: Could not connect to Ray cluster")

        # Start monitoring
        monitor_jobs(results_dir, args.poll_interval)

        # Generate summary report
        generate_summary_report(results_dir)


if __name__ == '__main__':
    main()
