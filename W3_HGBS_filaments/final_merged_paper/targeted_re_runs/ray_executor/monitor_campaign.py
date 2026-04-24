#!/usr/bin/env python3
"""
Campaign Progress Monitor

Real-time monitoring of peer review validation campaign progress.
Displays completion status, estimated time remaining, and per-simulation details.
"""

import json
import os
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Configuration
STATUS_DIR = "../output/status"
RUN_LIST_PATH = "../simulations/run_list.json"
POLL_INTERVAL = 10  # seconds between checks

def load_run_list() -> Dict:
    """Load simulation specifications."""
    with open(RUN_LIST_PATH, 'r') as f:
        return json.load(f)

def load_status_files() -> Dict[str, Dict]:
    """Load all available status files."""
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

def get_sim_status(run_spec: Dict, status_files: Dict[str, Dict]) -> str:
    """Get current status of a simulation."""
    run_id = run_spec['run_id']

    if run_id in status_files:
        return status_files[run_id]['status']
    else:
        return "PENDING"

def estimate_time_remaining(pending_count: int, avg_time_per_sim: float) -> str:
    """Estimate time to campaign completion."""
    if pending_count == 0:
        return "0:00:00"

    total_seconds = pending_count * avg_time_per_sim / 4  # Divide by 4 concurrent
    return str(timedelta(seconds=int(total_seconds)))

def print_progress_bar(completed: int, total: int, width: int = 50) -> str:
    """Generate ASCII progress bar."""
    fraction = completed / total if total > 0 else 0
    filled = int(fraction * width)
    bar = "=" * filled + "-" * (width - filled)
    percent = fraction * 100
    return f"[{bar}] {percent:.1f}%"

def display_dashboard():
    """Display real-time campaign progress dashboard."""
    # Clear screen
    os.system('clear' if os.name == 'posix' else 'cls')

    # Load data
    campaign = load_run_list()
    all_sims = campaign['simulations']
    status_files = load_status_files()

    # Count by status
    status_counts = {
        'PENDING': 0,
        'RUNNING': 0,
        'FRAG': 0,
        'STABLE': 0,
        'TIMEOUT': 0,
        'FAILED': 0
    }

    wall_times = []

    for sim in all_sims:
        status = get_sim_status(sim, status_files)
        status_counts[status] += 1

        if status in ['FRAG', 'STABLE', 'TIMEOUT'] and sim['run_id'] in status_files:
            wall_times.append(status_files[sim['run_id']]['wall_time_seconds'])

    completed = status_counts['FRAG'] + status_counts['STABLE'] + status_counts['TIMEOUT'] + status_counts['FAILED']
    total = len(all_sims)
    pending = status_counts['PENDING'] + status_counts['RUNNING']

    # Calculate average wall time
    avg_wall_time = sum(wall_times) / len(wall_times) if wall_times else 5400  # Default 1.5 hours

    # Header
    print("=" * 80)
    print("PEER REVIEW VALIDATION CAMPAIGN - MONITOR")
    print("=" * 80)
    print(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Progress bar
    print(f"Progress: {print_progress_bar(completed, total)}")
    print(f"Completed: {completed}/{total} simulations")
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
    print(f"Average wall time: {avg_wall_time/3600:.2f} hours per simulation")
    print(f"Est. time remaining: {estimate_time_remaining(pending, avg_wall_time)}")
    print()

    # Priority breakdown
    print("Priority Breakdown:")
    p1_sims = [s for s in all_sims if s['priority'] == 1]
    p2_sims = [s for s in all_sims if s['priority'] == 2]

    p1_completed = sum(1 for s in p1_sims if get_sim_status(s, status_files) in ['FRAG', 'STABLE', 'TIMEOUT', 'FAILED'])
    p2_completed = sum(1 for s in p2_sims if get_sim_status(s, status_files) in ['FRAG', 'STABLE', 'TIMEOUT', 'FAILED'])

    print(f"  Priority 1 (DTC):        {p1_completed}/{len(p1_sims)} complete")
    print(f"  Priority 2 (Resolution): {p2_completed}/{len(p2_sims)} complete")
    print()

    # Recent activity (last 5 completed)
    completed_sims = []
    for sim in all_sims:
        status = get_sim_status(sim, status_files)
        if status in ['FRAG', 'STABLE', 'TIMEOUT', 'FAILED'] and sim['run_id'] in status_files:
            completed_sims.append((sim['run_id'], status, status_files[sim['run_id']]['wall_time_seconds']))

    completed_sims.sort(key=lambda x: x[2], reverse=True)

    if completed_sims:
        print("Recent Activity:")
        for run_id, status, wall_time in completed_sims[:5]:
            print(f"  {run_id:20s} {status:8s} ({wall_time/3600:.2f}h)")
    else:
        print("No simulations completed yet.")

    print()
    print("Press Ctrl+C to exit")
    print("=" * 80)

def display_detailed_status():
    """Display detailed status for all simulations."""
    print("\nDETAILED SIMULATION STATUS")
    print("-" * 80)

    campaign = load_run_list()
    all_sims = campaign['simulations']
    status_files = load_status_files()

    print(f"{'Run ID':<20} {'Priority':<3} {'f':<5} {'beta':<5} {'M':<5} {'Res':<6} {'Status':<10} {'t_frag':<10}")
    print("-" * 80)

    for sim in all_sims:
        run_id = sim['run_id']
        priority = sim['priority']
        f = sim['f']
        beta = sim['beta']
        mach = sim['mach']
        res = sim['resolution']

        status = get_sim_status(sim, status_files)
        t_frag_str = "-"

        if run_id in status_files:
            t_frag = status_files[run_id].get('t_frag', 0)
            if t_frag and t_frag > 0:
                t_frag_str = f"{t_frag:.3f}"

        print(f"{run_id:<20} {priority:<3} {f:<5.2f} {beta:<5.2f} {mach:<5.1f} {res:<6} {status:<10} {t_frag_str:<10}")

def main():
    """Main monitoring loop."""
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--detail":
            display_detailed_status()
        else:
            print("Starting campaign monitor...")
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
