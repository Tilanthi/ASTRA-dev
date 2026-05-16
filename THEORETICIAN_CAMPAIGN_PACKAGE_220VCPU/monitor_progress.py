#!/usr/bin/env python3
"""
Monitor progress of Theoretician Peer Review Response Campaign.

Usage:
    python3 monitor_progress.py
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta


STATUS_FILE = Path("campaign_status.json")
CONFIGS_DIR = Path("configs")


def load_status():
    """Load campaign status."""
    if not STATUS_FILE.exists():
        print(f"Status file not found: {STATUS_FILE}")
        print("Has the campaign been started?")
        return None
    with open(STATUS_FILE) as f:
        return json.load(f)


def print_progress(status):
    """Print progress bar and statistics."""
    total = status['total_simulations']
    completed = status['status'].get('completed', 0)
    running = status['status'].get('running', 0)
    failed = status['status'].get('failed', 0)

    pct = 100 * completed / total if total > 0 else 0
    bar_length = 50
    filled = int(bar_length * pct / 100)
    bar = '█' * filled + '░' * (bar_length - filled)

    print(f"\r[{bar}] {pct:5.1f}% ({completed}/{total} complete) | Running: {running} | Failed: {failed}", end='', flush=True)


def print_detailed_status(status):
    """Print detailed status breakdown."""
    print("\n" + "=" * 70)
    print("DETAILED CAMPAIGN STATUS")
    print("=" * 70)

    # Overall status
    print(f"\nCampaign started: {status['start_time']}")

    # Calculate elapsed time
    start = datetime.fromisoformat(status['start_time'])
    elapsed = datetime.now() - start
    print(f"Elapsed time: {str(elapsed).split('.')[0]}")

    # Status breakdown
    print("\nStatus breakdown:")
    for state, count in sorted(status['status'].items()):
        if count > 0:
            pct = 100 * count / status['total_simulations']
            print(f"  {state:15s}: {count:4d} ({pct:5.1f}%)")

    # Per-campaign breakdown
    print("\nCampaign breakdown:")
    for campaign in ['STV', 'PFS', 'NCRI']:
        campaign_sims = [s for s in status['simulations'].values()
                        if s.get('campaign') == campaign]
        total = len(campaign_sims)
        if total == 0:
            continue

        completed = sum(1 for s in campaign_sims if s.get('status') == 'completed')
        running = sum(1 for s in campaign_sims if s.get('status') == 'running')
        failed = sum(1 for s in campaign_sims if s.get('status') == 'failed')

        print(f"  {campaign:5s}: {completed:3d} completed | {running:2d} running | {failed:2d} failed | {total:3d} total")

    # Recent completions
    print("\nRecent completions (last 10):")
    completions = [(sim_id, sim) for sim_id, sim in status['simulations'].items()
                   if sim.get('status') == 'completed']
    completions.sort(key=lambda x: x[1].get('end_time', ''), reverse=True)

    for sim_id, sim in completions[:10]:
        classification = sim.get('classification', 'UNKNOWN')
        wall_time = sim.get('wall_time_seconds', 0) / 60  # Convert to minutes
        print(f"  {sim_id:50s} {classification:10s} ({wall_time:5.1f} min)")

    # Failed simulations
    failed_sims = [(sim_id, sim) for sim_id, sim in status['simulations'].items()
                   if sim.get('status') == 'failed']
    if failed_sims:
        print(f"\nFailed simulations ({len(failed_sims)}):")
        for sim_id, sim in failed_sims:
            error = sim.get('error', 'UNKNOWN')
            print(f"  {sim_id}: {error}")

    print("=" * 70 + "\n")


def estimate_time_remaining(status):
    """Estimate time remaining based on completion rate."""
    completed = status['status'].get('completed', 0)
    total = status['total_simulations']

    if completed < 5:
        return None  # Not enough data

    start = datetime.fromisoformat(status['start_time'])
    elapsed = (datetime.now() - start).total_seconds()
    rate = completed / elapsed  # Completions per second

    remaining = total - completed
    seconds_remaining = remaining / rate if rate > 0 else 0

    return timedelta(seconds=int(seconds_remaining))


def main():
    """Main monitoring loop."""
    print("Monitoring Theoretician Peer Review Response Campaign")
    print("Press Ctrl+C to exit")
    print()

    try:
        while True:
            status = load_status()
            if status is None:
                time.sleep(5)
                continue

            # Check if campaign is complete
            total = status['total_simulations']
            completed = status['status'].get('completed', 0)
            failed = status['status'].get('failed', 0)

            # Print progress bar
            print_progress(status)

            # Print detailed status every 30 seconds
            if int(time.time()) % 30 < 1:
                print_detailed_status(status)

                # Estimate time remaining
                eta = estimate_time_remaining(status)
                if eta:
                    print(f"Estimated time remaining: {eta}")

            # Check if complete
            if completed + failed >= total:
                print("\n\nCampaign completed!")
                print_detailed_status(status)
                break

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        status = load_status()
        if status:
            print_detailed_status(status)


if __name__ == '__main__':
    main()
