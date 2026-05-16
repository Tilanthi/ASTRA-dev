#!/usr/bin/env python3
"""
ASTRA Discovery Monitor and Tracker

Real-time monitoring of ASTRA's autonomous discoveries with:
- Live discovery feed
- Statistics tracking
- Domain coverage analysis
- Discovery quality scoring
"""

import json
import time
import sqlite3
from datetime import datetime
from pathlib import Path

# Configuration
ASTRA_DIR = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main")
STATS_FILE = ASTRA_DIR / "data" / "autonomous_stats.json"
DISCOVERIES_DB = ASTRA_DIR / "astra_discoveries.db"
LOG_FILE = ASTRA_DIR / "logs" / "autonomous_daemon.log"


class DiscoveryMonitor:
    """Monitor and track ASTRA discoveries"""

    def __init__(self):
        self.discoveries = []
        self.stats = {}
        self._load_stats()

    def _load_stats(self):
        """Load current statistics"""
        if STATS_FILE.exists():
            with open(STATS_FILE) as f:
                self.stats = json.load(f)

    def print_status(self):
        """Print current status"""
        print("=" * 70)
        print("ASTRA AUTONOMOUS DISCOVERY STATUS")
        print("=" * 70)
        print(f"Start time: {self.stats.get('start_time', 'Unknown')}")
        print(f"Cycles completed: {self.stats.get('cycles_completed', 0)}")
        print(f"Total discoveries: {self.stats.get('discoveries_made', 0)}")
        print(f"Hypotheses tested: {self.stats.get('hypotheses_tested', 0)}")
        print(f"Last cycle: {self.stats.get('last_cycle_time', 'Never')}")
        print(f"Last discovery: {self.stats.get('last_discovery', 'None')}")
        print("=" * 70)

    def watch_logs(self, n_lines=20):
        """Watch recent log entries"""
        if LOG_FILE.exists():
            print(f"\nRecent activity (last {n_lines} lines):")
            print("-" * 70)

            with open(LOG_FILE) as f:
                lines = f.readlines()
                for line in lines[-n_lines:]:
                    if any(word in line for word in ['Discovery:', 'Cycle', 'Stage', 'ERROR']):
                        print(line.rstrip())
        else:
            print("\nNo log file found yet")

    def monitor_continuous(self, interval=60):
        """Continuously monitor discoveries"""
        print(f"\nMonitoring ASTRA discoveries (update every {interval}s)...")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                # Reload stats
                self._load_stats()

                # Print timestamp and stats
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                      f"Cycles: {self.stats.get('cycles_completed', 0)} | "
                      f"Discoveries: {self.stats.get('discoveries_made', 0)}")

                # Sleep for interval
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped")
            self.print_status()


def main():
    """Main entry point"""
    import sys

    monitor = DiscoveryMonitor()

    if len(sys.argv) > 1 and sys.argv[1] == 'watch':
        # Continuous monitoring mode
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        monitor.monitor_continuous(interval)
    else:
        # Status mode
        monitor.print_status()
        monitor.watch_logs()


if __name__ == '__main__':
    main()
