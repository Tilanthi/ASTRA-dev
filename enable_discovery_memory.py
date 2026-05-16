#!/usr/bin/env python3
"""
Direct Memory Integration for ASTRA Autonomous Discovery

This script patches the autonomous daemon to store all discoveries
in ASTRA's persistent memory system (Graph Palace/Memory Palace).
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add ASTRA to path
ASTRA_DEV = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main")
sys.path.insert(0, str(ASTRA_DEV))

# Import memory system
from astra_core.memory.persistent.bootstrap_memory import (
    BootstrapMemory,
    MemoryCategory,
    MemoryPriority,
    PersistentMemoryItem
)

# Create global memory bridge
_discovery_memory = None


class DiscoveryMemoryBridge:
    """Bridge for storing autonomous discoveries in persistent memory"""

    def __init__(self):
        # Initialize bootstrap memory in standard location
        self.memory = BootstrapMemory()
        self.memory.initialize_session()
        print("[Memory Bridge] ✓ Initialized persistent memory")

    def store_discovery(self, discovery_data):
        """Store a discovery in persistent memory"""
        try:
            # Create memory item from discovery
            content = json.dumps({
                'discovery_id': discovery_data.get('id', 'unknown'),
                'statement': discovery_data.get('statement', ''),
                'hypothesis': discovery_data.get('finding', ''),
                'variables': discovery_data.get('variables', []),
                'statistics': discovery_data.get('statistics', {}),
                'domain': discovery_data.get('domain', 'astrophysics'),
                'timestamp': datetime.now().isoformat(),
                'confidence': discovery_data.get('confidence', 0.0),
                'significance': self._calculate_significance(discovery_data)
            })

            memory_item = PersistentMemoryItem(
                id=f"discovery_{discovery_data.get('id', 'unknown')}",
                category=MemoryCategory.CRITICAL_KNOWLEDGE,
                priority=MemoryPriority.HIGH,
                content=content,
                verified=False,
                source='autonomous_discovery_daemon',
                verification_trail=[],
                tags={'discovery', discovery_data.get('domain', 'astrophysics')},
                metadata={
                    'discovery_id': discovery_data.get('id'),
                    'variables': discovery_data.get('variables', []),
                    'confidence': discovery_data.get('confidence', 0.0)
                }
            )

            # Store in persistent memory
            self.memory.store_memory(memory_item)

            print(f"[Memory Bridge] ✓ Stored: {discovery_data.get('statement', 'Unknown')[:50]}...")

        except Exception as e:
            print(f"[Memory Bridge] ✗ Failed to store discovery: {e}")

    def _calculate_significance(self, discovery):
        """Calculate significance score"""
        statistics = discovery.get('statistics', {})
        confidence = discovery.get('confidence', 0.0)

        # P-value significance (lower is better)
        p_value = statistics.get('p', 1.0)
        p_sig = -np.log10(min(p_value, 1e-300)) / 10 if p_value > 0 else 0

        # Combined score
        return min(0.4 * confidence + 0.3 * p_sig + 0.3 * abs(statistics.get('r', 0)), 1.0)


# Initialize bridge on import
try:
    _discovery_memory = DiscoveryMemoryBridge()
    print("[Memory Bridge] ✓ Memory bridge ready for autonomous discoveries")
except Exception as e:
    print(f"[Memory Bridge] ✗ Failed to initialize: {e}")
    _discovery_memory = None


def store_all_discoveries_from_log():
    """
    Scan the daemon log and extract/store all discoveries that were made.
    This ensures past discoveries aren't lost.
    """
    if not _discovery_memory:
        print("[Memory Bridge] Not available, skipping log scan")
        return

    log_file = ASTRA_DEV / "logs" / "autonomous_daemon.log"

    if not log_file.exists():
        print(f"[Memory Bridge] No log file found at {log_file}")
        return

    print(f"[Memory Bridge] Scanning {log_file} for discoveries...")

    # Read log and extract discoveries
    discoveries_found = 0

    with open(log_file) as f:
        for line in f:
            if "[INFO] Discovery:" in line:
                try:
                    # Extract discovery info from log line
                    # Format: "2026-04-26 20:50:45,621 [INFO] Discovery: statement (r=X, p=Y)"
                    parts = line.split("Discovery:", 1)[1].strip()
                    statement = parts.split("(")[0].strip()

                    # Parse statistics if available
                    statistics = {}
                    if "r=" in parts:
                        r_val = parts.split("r=")[1].split(",")[0].strip()
                        statistics['r'] = float(r_val)
                    if "p=" in parts:
                        p_val = parts.split("p=")[1].split(")")[0].strip()
                        statistics['p'] = float(p_val)

                    # Store in memory
                    discovery_data = {
                        'id': f"log_{discoveries_found}",
                        'statement': statement,
                        'finding': statement,
                        'statistics': statistics,
                        'domain': 'astrophysics',
                        'confidence': statistics.get('r', 0.0)
                    }

                    _discovery_memory.store_discovery(discovery_data)
                    discoveries_found += 1

                except Exception as e:
                    print(f"[Memory Bridge] Failed to parse discovery: {e}")

    print(f"[Memory Bridge] ✓ Stored {discoveries_found} discoveries from log")

    # Also try to read from stats
    stats_file = ASTRA_DEV / "data" / "autonomous_stats.json"
    if stats_file.exists():
        try:
            with open(stats_file) as f:
                stats = json.load(f)
            total = stats.get('discoveries_made', 0)
            print(f"[Memory Bridge] Stats show {total} total discoveries made")
        except:
            pass


def monitor_and_store_continuously():
    """
    Continuously monitor the daemon log for new discoveries and store them.
    """
    import time

    if not _discovery_memory:
        print("[Memory Bridge] Cannot monitor without memory bridge")
        return

    log_file = ASTRA_DEV / "logs" / "autonomous_daemon.log"

    print("[Memory Bridge] Starting continuous discovery monitoring...")
    print("[Memory Bridge] Press Ctrl+C to stop\n")

    # Get current file size
    last_size = log_file.stat().st_size if log_file.exists() else 0

    try:
        while True:
            if log_file.exists():
                current_size = log_file.stat().st_size

                # If file grew, read new lines
                if current_size > last_size:
                    with open(log_file) as f:
                        f.seek(last_size)
                        new_lines = f.readlines()

                    for line in new_lines:
                        if "[INFO] Discovery:" in line:
                            try:
                                # Extract and store discovery
                                parts = line.split("Discovery:", 1)[1].strip()
                                statement = parts.split("(")[0].strip()

                                # Parse statistics
                                statistics = {}
                                if "r=" in parts:
                                    r_val = parts.split("r=")[1].split(",")[0].strip()
                                    statistics['r'] = float(r_val)
                                if "p=" in parts:
                                    p_val = parts.split("p=")[1].split(")")[0].strip()
                                    statistics['p'] = float(p_val)

                                discovery_data = {
                                    'id': f"auto_{int(datetime.now().timestamp())}",
                                    'statement': statement,
                                    'finding': statement,
                                    'statistics': statistics,
                                    'domain': 'astrophysics',
                                    'confidence': statistics.get('r', 0.0)
                                }

                                _discovery_memory.store_discovery(discovery_data)

                            except Exception as e:
                                print(f"[Memory Bridge] Failed to store: {e}")

                    last_size = current_size

            # Wait before next check
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[Memory Bridge] Monitoring stopped")


if __name__ == '__main__':
    print("ASTRA Discovery Memory Integration")
    print("=" * 60)

    # First, store any discoveries that were already made
    print("\n1. Storing past discoveries from log...")
    store_all_discoveries_from_log()

    # Then start continuous monitoring
    print("\n2. Starting continuous monitoring...")
    print("   (Autonomous discoveries will be stored as they happen)")

    # Start monitoring
    monitor_and_store_continuously()
