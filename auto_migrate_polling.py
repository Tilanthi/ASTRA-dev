#!/usr/bin/env python3
"""
Simple Polling Memory Migrator (No External Dependencies)

Periodically checks for new .md files in memory directory and
migrates them to GraphPalace. Simpler than watchdog version.

Usage:
    python3 auto_migrate_polling.py --daemon
    python3 auto_migrate_polling.py --once

Author: ASTRA System
Date: 2026-05-09
"""

import os
import sys
import json
import time
import signal
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Import from existing migration script
sys.path.insert(0, str(Path(__file__).parent))
from migrate_memory_to_graphpalace import MemoryMigrator


class PollingMemoryMigrator:
    """Poll for new memory files and migrate them."""

    def __init__(self, memory_dir: Path, graphpalace_dir: Path,
                 poll_interval: int = 5):
        self.migrator = MemoryMigrator(memory_dir, graphpalace_dir)
        self.poll_interval = poll_interval
        self.known_files = set()
        self.running = False
        self.stats = {
            "files_processed": 0,
            "start_time": None
        }

        # Get initial file list
        self._update_known_files()

    def _update_known_files(self):
        """Update list of known files."""
        memory_files = list(self.migrator.memory_dir.glob("*.md"))
        self.known_files = set(f.name for f in memory_files)

    def _check_for_new_files(self) -> List[Path]:
        """Check for new .md files."""
        memory_files = list(self.migrator.memory_dir.glob("*.md"))
        new_files = []

        for filepath in memory_files:
            if filepath.name not in self.known_files:
                new_files.append(filepath)
                self.known_files.add(filepath.name)

        return new_files

    def migrate_new_files(self) -> int:
        """Migrate any new files."""
        new_files = self._check_for_new_files()
        migrated_count = 0

        for filepath in new_files:
            try:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] "
                      f"New memory file: {filepath.name}")

                # Check if already migrated in GraphPalace
                file_key = str(filepath)
                if file_key in self.migrator.migrated_files:
                    print(f"  ✓ Already in GraphPalace")
                    continue

                # Migrate file
                node = self.migrator.migrate_file(filepath)

                if node:
                    print(f"  ✓ Migrated to: {node['id']}")
                    self.stats["files_processed"] += 1
                    migrated_count += 1
                else:
                    print(f"  - Skipped (error or already migrated)")

            except Exception as e:
                print(f"  ✗ Error: {e}")

        return migrated_count

    def run_once(self) -> int:
        """Run single migration pass."""
        print("="*80)
        print("POLLING MEMORY MIGRATOR")
        print("="*80)
        print(f"\nMemory directory: {self.migrator.memory_dir}")
        print(f"GraphPalace directory: {self.migrator.graphpalace_dir}")
        print(f"\nScanning for new files...\n")

        count = self.migrate_new_files()

        print(f"\n✓ Processed {count} new files")
        return count

    def run_daemon(self):
        """Run continuous polling daemon."""
        self.running = True
        self.stats["start_time"] = datetime.now()

        # Setup signal handlers
        def signal_handler(signum, frame):
            print("\n\nStopping daemon...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print("="*80)
        print("POLLING MEMORY MIGRATOR DAEMON")
        print("="*80)
        print(f"\nMemory directory: {self.migrator.memory_dir}")
        print(f"GraphPalace directory: {self.migrator.graphpalace_dir}")
        print(f"Poll interval: {self.poll_interval} seconds")
        print(f"PID: {os.getpid()}")
        print(f"\nWatching for new .md files...")
        print("Press Ctrl+C to stop\n")

        # Initial scan
        print("[INITIAL SCAN]")
        self.migrate_new_files()

        # Main polling loop
        while self.running:
            try:
                time.sleep(self.poll_interval)

                if self.running:  # Double-check after sleep
                    new_count = self.migrate_new_files()

                    if new_count > 0:
                        print(f"\n[SUMMARY] Migrated {new_count} files | "
                              f"Total: {self.stats['files_processed']} | "
                              f"Uptime: {self._get_uptime()}")

            except Exception as e:
                print(f"\n✗ Error in polling loop: {e}")
                time.sleep(5)  # Wait before retry

        # Shutdown
        self._shutdown()

    def _get_uptime(self) -> str:
        """Get uptime string."""
        if not self.stats["start_time"]:
            return "N/A"

        uptime = datetime.now() - self.stats["start_time"]
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _shutdown(self):
        """Clean shutdown."""
        print("\n" + "="*80)
        print("DAEMON SHUTDOWN")
        print("="*80)
        print(f"\nFiles processed: {self.stats['files_processed']}")
        print(f"Uptime: {self._get_uptime()}")
        print(f"\n✓ Daemon stopped cleanly")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Poll memory directory for new files to migrate"
    )
    parser.add_argument("--daemon", action="store_true",
                       help="Run as continuous daemon")
    parser.add_argument("--once", action="store_true",
                       help="Run single scan")
    parser.add_argument("--interval", type=int, default=5,
                       help="Polling interval in seconds (default: 5)")
    parser.add_argument("--memory-dir", type=str,
                       default="/Users/gjw255/.claude/projects/-Users-gjw255-astrodata-SWARM-ASTRA-dev-main/memory",
                       help="Memory directory path")
    parser.add_argument("--graphpalace-dir", type=str,
                       default="/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/data/graph_palace",
                       help="GraphPalace directory path")

    args = parser.parse_args()

    memory_dir = Path(args.memory_dir)
    graphpalace_dir = Path(args.graphpalace_dir)

    # Create directories if needed
    memory_dir.mkdir(parents=True, exist_ok=True)
    graphpalace_dir.mkdir(parents=True, exist_ok=True)

    # Create migrator
    migrator = PollingMemoryMigrator(memory_dir, graphpalace_dir,
                                     poll_interval=args.interval)

    # Run requested mode
    if args.daemon:
        return migrator.run_daemon()
    elif args.once:
        count = migrator.run_once()
        return 0 if count >= 0 else 1
    else:
        # Default: run once
        count = migrator.run_once()
        return 0 if count >= 0 else 1


if __name__ == '__main__':
    sys.exit(main())
