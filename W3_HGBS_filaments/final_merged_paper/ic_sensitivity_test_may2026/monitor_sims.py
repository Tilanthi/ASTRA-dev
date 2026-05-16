#!/usr/bin/env python3
"""
Monitor IC Sensitivity Test Campaign Progress

Real-time status monitoring for the 48-simulation campaign.
Shows completion status, fragmentation counts, and estimated time remaining.
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

def load_status_files():
    """Load all status JSON files from output/status directory."""
    status_dir = Path("output/status")
    if not status_dir.exists():
        print("No status files found. Campaign may not have started yet.")
        return []

    status_files = list(status_dir.glob("status_*.json"))
    results = []

    for sf in status_files:
        try:
            with open(sf, 'r') as f:
                results.append(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load {sf}: {e}")

    return results

def print_summary(results):
    """Print campaign summary."""
    if not results:
        print("No results found")
        return

    total = len(results)
    frag = sum(1 for r in results if r['status'] == 'FRAG')
    stable = sum(1 for r in results if r['status'] == 'STABLE')
    timeout = sum(1 for r in results if r['status'] == 'TIMEOUT')
    failed = sum(1 for r in results if r['status'] == 'FAILED')
    running = sum(1 for r in results if r['status'] == 'RUNNING')

    print(f"\n{'='*60}")
    print(f"IC Sensitivity Test Campaign Status")
    print(f"{'='*60}")
    print(f"Total simulations: {total}")
    print(f"\nStatus breakdown:")
    print(f"  FRAG:    {frag:3d} ({frag/total*100:.1f}%)")
    print(f"  STABLE:  {stable:3d} ({stable/total*100:.1f}%)")
    print(f"  TIMEOUT: {timeout:3d} ({timeout/total*100:.1f}%)")
    print(f"  FAILED:  {failed:3d} ({failed/total*100:.1f}%)")
    print(f"  RUNNING: {running:3d} ({running/total*100:.1f}%)")

    # Breakdown by IC type
    king_results = [r for r in results if r.get('ic_type', 'king') == 'king']
    unif_results = [r for r in results if r.get('ic_type', 'king') == 'uniform']

    print(f"\nBy IC type:")
    print(f"  King IC:    {len(king_results):2d} sims, {sum(1 for r in king_results if r['status']=='FRAG'):2d} FRAG")
    print(f"  Uniform IC: {len(unif_results):2d} sims, {sum(1 for r in unif_results if r['status']=='FRAG'):2d} FRAG")

    # Breakdown by f value
    f_groups = defaultdict(list)
    for r in results:
        f_groups[r['f']].append(r)

    print(f"\nBy mass-to-line-mass ratio (f):")
    for f_val in sorted(f_groups.keys()):
        group = f_groups[f_val]
        n_frag = sum(1 for r in group if r['status'] == 'FRAG')
        print(f"  f = {f_val:.2f}: {len(group):2d} sims, {n_frag:2d} FRAG ({n_frag/len(group)*100:.0f}%)")

    # Estimate time remaining
    completed = [r for r in results if r['status'] in ['FRAG', 'STABLE', 'TIMEOUT', 'FAILED']]
    if completed:
        avg_time = sum(r['wall_time_seconds'] for r in completed) / len(completed)
        remaining = total - len(completed)
        est_remaining = avg_time * remaining / MAX_CONCURRENT  # Assuming 16 concurrent

        print(f"\nTime estimates:")
        print(f"  Avg runtime per sim: {avg_time/60:.1f} minutes")
        print(f"  Est. time remaining: {est_remaining/3600:.1f} hours")

    print(f"{'='*60}\n")

def print_detailed_status(results):
    """Print detailed status for each simulation."""
    print("\nDetailed simulation status:")
    print("-" * 100)
    print(f"{'Run ID':<25} {'f':>4} {'beta':>4} {'M':>4} {'IC':<8} {'Status':<10} {'t_frag':>8} {'HDF5':>5}")
    print("-" * 100)

    # Sort by run_id for consistent display
    sorted_results = sorted(results, key=lambda x: x['run_id'])

    for r in sorted_results:
        run_id = r['run_id']
        f_val = r['f']
        beta = r['beta']
        mach = r['mach']
        ic_type = r.get('ic_type', 'king')[:8]
        status = r['status']
        t_frag = f"{r.get('t_frag', 0):.2f}" if r.get('t_frag') else "N/A"
        hdf5 = r.get('hdf5_snapshots', 0)

        print(f"{run_id:<25} {f_val:>4.2f} {beta:>4.1f} {mach:>4.1f} {ic_type:<8} {status:<10} {t_frag:>8} {hdf5:>5}")

    print("-" * 100)

def monitor_continuous():
    """Continuously monitor campaign progress."""
    print("Starting continuous monitoring (Ctrl+C to stop)...")
    print("Press Enter to refresh status immediately")

    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            results = load_status_files()
            print_summary(results)

            # Check if campaign is complete
            if results and all(r['status'] != 'RUNNING' for r in results):
                print("Campaign complete!")
                print_detailed_status(results)
                break

            # Wait for user input or timeout
            print("\nWaiting... (press Enter to refresh, Ctrl+C to exit)")
            time.sleep(30)  # Refresh every 30 seconds

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monitor IC sensitivity test campaign")
    parser.add_argument("--continuous", "-c", action="store_true",
                       help="Continuously monitor campaign progress")
    parser.add_argument("--detailed", "-d", action="store_true",
                       help="Show detailed per-simulation status")
    args = parser.parse_args()

    if args.continuous:
        monitor_continuous()
    else:
        results = load_status_files()
        print_summary(results)
        if args.detailed:
            print_detailed_status(results)

        if results and any(r['status'] == 'RUNNING' for r in results):
            print("\nCampaign still in progress. Use --continuous for live monitoring.")
