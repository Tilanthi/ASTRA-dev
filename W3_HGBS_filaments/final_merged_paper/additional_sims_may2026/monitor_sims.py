#!/usr/bin/env python3
"""
Campaign Progress Monitor

Real-time monitoring of resolution reference campaign progress.
"""

import json
import os
import time
from pathlib import Path

STATUS_DIR = "output/status"
RUN_LIST_PATH = "run_list.json"
POLL_INTERVAL = 10

def load_run_list():
    with open(RUN_LIST_PATH, 'r') as f:
        return json.load(f)

def load_status_files():
    status_files = {}
    status_dir = Path(STATUS_DIR)

    if not status_dir.exists():
        return status_files

    for status_file in status_dir.glob("status_*.json"):
        try:
            with open(status_file, 'r') as f:
                data = json.load(f)
                run_id = data['run_id']
                status_files[run_id] = data
        except Exception as e:
            print(f"Warning: Could not load {status_file}: {e}")

    return status_files

def display_dashboard():
    os.system('clear' if os.name == 'posix' else 'cls')

    print("=" * 80)
    print("RESOLUTION REFERENCE CAMPAIGN - MONITOR")
    print("=" * 80)
    print(f"Last update: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load data
    campaign = load_run_list()
    all_sims = campaign['simulations']
    status_files = load_status_files()

    # Count by status
    status_counts = {'PENDING': 0, 'RUNNING': 0, 'FRAG': 0, 'STABLE': 0, 'TIMEOUT': 0, 'FAILED': 0}

    for sim in all_sims:
        run_id = sim['run_id']
        if run_id in status_files:
            status_counts[status_files[run_id]['status']] += 1
        else:
            status_counts['PENDING'] += 1

    completed = status_counts['FRAG'] + status_counts['STABLE'] + status_counts['TIMEOUT'] + status_counts['FAILED']
    total = len(all_sims)

    # Progress bar
    n_complete = completed
    filled = int(n_complete / total * 50) if total > 0 else 0
    bar = "=" * filled + "-" * (50 - filled)
    percent = n_complete / total * 100 if total > 0 else 0
    print(f"Progress: [{bar}] {percent:.1f}%")
    print(f"Completed: {n_complete}/{total} simulations")
    print()

    # Status breakdown
    print("Status Breakdown:")
    print(f"  PENDING:  {status_counts['PENDING']:3d}")
    print(f"  RUNNING:  {status_counts['RUNNING']:3d}")
    print(f"  FRAG:     {status_counts['FRAG']:3d}")
    print(f"  STABLE:   {status_counts['STABLE']:3d}")
    print(f"  TIMEOUT:  {status_counts['TIMEOUT']:3d}")
    print(f"  FAILED:   {status_counts['FAILED']:3d}")
    print()

    # Time estimates
    frag_times = [s['t_frag'] for s in status_files.values() if s['status'] == 'FRAG']
    if frag_times:
        mean_time = sum(frag_times) / len(frag_times)
        print(f"Mean t_frag (FRAG cases): {mean_time:.3f} t_J")

    pending = total - completed
    if pending > 0:
        est_per_sim = 2700  # ~45 min in seconds
        est_total = pending * est_per_sim / 10 / 60  # 10 concurrent, convert to minutes
        print(f"Estimated time remaining: ~{est_total:.0f} minutes")

    print()
    print("Press Ctrl+C to exit")
    print("=" * 80)

def main():
    try:
        print("Starting resolution reference campaign monitor...")
        print("Press Ctrl+C to exit")
        time.sleep(2)

        while True:
            display_dashboard()
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")
        print(f"Final status files saved in {STATUS_DIR}/")

if __name__ == "__main__":
    main()
