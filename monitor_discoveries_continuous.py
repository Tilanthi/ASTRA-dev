#!/usr/bin/env python3
"""
Continuous Discovery Memory Monitor

This script runs in the background and continuously monitors the autonomous
daemon log file for new discoveries. When discoveries are found, they are
automatically stored in ASTRA's persistent memory (BootstrapMemory).

This ensures that ALL autonomous discoveries are permanently remembered
in ASTRA's memory palace, surviving across sessions and available for
future retrieval and analysis.
"""

import sys
import os
import time
import re
import json
from pathlib import Path
from datetime import datetime

# Add ASTRA to path
ASTRA_DEV = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main")
sys.path.insert(0, str(ASTRA_DEV))

from astra_core.memory.persistent.bootstrap_memory import (
    BootstrapMemory,
    MemoryCategory,
    MemoryPriority,
    PersistentMemoryItem
)


class ContinuousDiscoveryMonitor:
    """Monitor and store autonomous discoveries in persistent memory"""

    def __init__(self):
        # Initialize bootstrap memory
        self.bootstrap = BootstrapMemory()
        self.bootstrap.initialize_session()

        # Log file to monitor
        self.log_file = ASTRA_DEV / "logs" / "autonomous_daemon.log"

        # Track what we've already processed
        self.last_position = 0
        self.processed_discoveries = set()

        # Discovery pattern for log parsing
        self.discovery_pattern = re.compile(
            r'\[INFO\] Discovery: (.+?) \(r=([\d\.\-]+), p=([\d\.\-e]+)\)'
        )

        print("[Discovery Monitor] ✓ Initialized persistent memory")
        print(f"[Discovery Monitor] Monitoring: {self.log_file}")

    def get_existing_discoveries(self):
        """Load existing discoveries from memory to avoid duplicates"""
        try:
            discoveries = self.bootstrap.get_memories_by_category(
                MemoryCategory.CRITICAL_KNOWLEDGE
            )
            return {d.id for d in discoveries if d.id.startswith('discovery_auto_')}
        except:
            return set()

    def process_discovery(self, statement, r_val, p_val, index):
        """Store a discovery in persistent memory"""
        try:
            # Create discovery content
            discovery_content = json.dumps({
                'statement': statement,
                'type': 'causal' if 'causes' in statement else 'correlational',
                'variables': self._extract_variables(statement),
                'statistics': {'r': float(r_val), 'p': float(p_val)},
                'domain': 'astrophysics',
                'timestamp': datetime.now().isoformat(),
                'confidence': abs(float(r_val)),
                'significance': self._calculate_significance(float(r_val), float(p_val))
            })

            # Create memory item
            discovery_id = f"discovery_auto_{index}"
            memory_item = PersistentMemoryItem(
                id=discovery_id,
                category=MemoryCategory.CRITICAL_KNOWLEDGE,
                priority=MemoryPriority.HIGH,
                content=discovery_content,
                verified=False,
                source='autonomous_discovery_daemon',
                verification_trail=[],
                tags={'discovery', 'astrophysics'},
                metadata={'log_index': index}
            )

            # Store in persistent memory
            self.bootstrap.store_memory(memory_item)

            return True

        except Exception as e:
            print(f"[Discovery Monitor] ✗ Failed to store discovery: {e}")
            return False

    def _extract_variables(self, statement):
        """Extract variable names from discovery statement"""
        # Simple extraction - split by common words
        parts = re.split(r'\s+(causes|correlates with)\s+', statement)
        if len(parts) >= 3:
            return [parts[0].strip(), parts[2].strip()]
        return []

    def _calculate_significance(self, r_val, p_val):
        """Calculate significance score"""
        # Combine correlation strength and p-value significance
        r_sig = abs(r_val)
        p_sig = -1 * (min(p_val, 1e-300) ** 0.1)  # Scale p-value
        return min(r_sig * 0.6 + p_sig * 0.4, 1.0)

    def scan_existing_log(self):
        """Scan existing log for discoveries we haven't processed"""
        if not self.log_file.exists():
            print(f"[Discovery Monitor] No log file found")
            return 0

        print("[Discovery Monitor] Scanning existing log...")

        # Get existing discoveries to avoid duplicates
        existing = self.get_existing_discoveries()
        print(f"[Discovery Monitor] Found {len(existing)} existing discoveries in memory")

        # Read entire log
        with open(self.log_file, 'r') as f:
            content = f.read()

        # Find all discoveries
        matches = list(self.discovery_pattern.findall(content))
        new_discoveries = 0

        for i, (statement, r_val, p_val) in enumerate(matches):
            discovery_id = f"discovery_auto_{i}"

            if discovery_id not in existing:
                if self.process_discovery(statement, r_val, p_val, i):
                    new_discoveries += 1
                    self.processed_discoveries.add(discovery_id)
                    print(f"[Discovery Monitor] ✓ New: {statement[:60]}...")

        # Update position
        self.last_position = self.log_file.stat().st_size

        print(f"[Discovery Monitor] ✓ Stored {new_discoveries} new discoveries")
        return new_discoveries

    def monitor_continuously(self, interval=5):
        """Monitor log file for new discoveries"""
        print(f"\n[Discovery Monitor] Starting continuous monitoring...")
        print(f"[Discovery Monitor] Check interval: {interval} seconds")
        print("[Discovery Monitor] Press Ctrl+C to stop\n")

        try:
            while True:
                if self.log_file.exists():
                    current_size = self.log_file.stat().st_size

                    # If file grew, read new content
                    if current_size > self.last_position:
                        with open(self.log_file, 'r') as f:
                            f.seek(self.last_position)
                            new_content = f.read()

                        # Look for discoveries in new content
                        matches = list(self.discovery_pattern.findall(new_content))

                        if matches:
                            print(f"[Discovery Monitor] Found {len(matches)} new discoveries!")

                            # Get current total count
                            existing = self.get_existing_discoveries()
                            base_index = len(existing)

                            for i, (statement, r_val, p_val) in enumerate(matches):
                                discovery_index = base_index + i

                                if self.process_discovery(statement, r_val, p_val, discovery_index):
                                    print(f"[Discovery Monitor] ✓ Stored: {statement[:60]}...")

                        # Update position
                        self.last_position = current_size

                # Wait before next check
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n[Discovery Monitor] Monitoring stopped")
            print(f"[Discovery Monitor] Processed {len(self.processed_discoveries)} discoveries")


def main():
    """Main entry point"""
    print("=" * 70)
    print("ASTRA Continuous Discovery Memory Monitor")
    print("=" * 70)
    print("\nThis monitor ensures ALL autonomous discoveries are stored in")
    print("ASTRA's persistent memory (Memory Palace/Graph Palace).\n")

    # Create monitor
    monitor = ContinuousDiscoveryMonitor()

    # First, scan existing log
    new_count = monitor.scan_existing_log()

    # Get total count
    total = len(monitor.get_existing_discoveries())
    print(f"\n[Discovery Monitor] Total discoveries in memory: {total}")
    print("[Discovery Monitor] ✓ All discoveries are now permanently remembered\n")

    # Start continuous monitoring
    monitor.monitor_continuously(interval=5)


if __name__ == '__main__':
    main()
