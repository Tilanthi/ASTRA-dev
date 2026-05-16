#!/usr/bin/env python3
"""
Simple Continuous Discovery Memory Monitor

Minimal version that avoids heavy domain loading.
Monitors the autonomous daemon log and stores discoveries in persistent memory.
"""

import sys
import os
import time
import re
import json
from pathlib import Path
from datetime import datetime

# Direct imports to avoid domain loading
ASTRA_DEV = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main")
sys.path.insert(0, str(ASTRA_DEV))

# Import only what we need
from astra_core.memory.persistent.bootstrap_memory import (
    BootstrapMemory,
    MemoryCategory,
    MemoryPriority,
    PersistentMemoryItem
)

print("[Monitor] Starting continuous discovery memory monitor...")

# Initialize memory
bootstrap = BootstrapMemory()
bootstrap.initialize_session()
print("[Monitor] ✓ Persistent memory initialized")

# Log file to monitor
log_file = ASTRA_DEV / "logs" / "autonomous_daemon.log"
print(f"[Monitor] Monitoring: {log_file}")

# Discovery pattern
discovery_pattern = re.compile(
    r'\[INFO\] Discovery: (.+?) \(r=([\d\.\-]+), p=([\d\.\-e]+)\)'
)

# Track position
last_position = 0
last_discovery_count = 0

def get_discovery_count():
    """Get current number of discoveries in memory"""
    try:
        discoveries = bootstrap.get_memories_by_category(MemoryCategory.CRITICAL_KNOWLEDGE)
        return len([d for d in discoveries if d.id.startswith('discovery_auto_')])
    except:
        return 0

def store_discovery(statement, r_val, p_val, index):
    """Store a discovery in persistent memory"""
    try:
        discovery_content = json.dumps({
            'statement': statement,
            'type': 'causal' if 'causes' in statement else 'correlational',
            'variables': [],
            'statistics': {'r': float(r_val), 'p': float(p_val)},
            'domain': 'astrophysics',
            'timestamp': datetime.now().isoformat(),
            'confidence': abs(float(r_val)),
            'significance': min(abs(float(r_val)) + 0.1, 1.0)
        })

        memory_item = PersistentMemoryItem(
            id=f"discovery_auto_{index}",
            category=MemoryCategory.CRITICAL_KNOWLEDGE,
            priority=MemoryPriority.HIGH,
            content=discovery_content,
            verified=False,
            source='autonomous_discovery_daemon',
            verification_trail=[],
            tags={'discovery', 'astrophysics'},
            metadata={'log_index': index}
        )

        bootstrap.store_memory(memory_item)
        return True
    except Exception as e:
        print(f"[Monitor] ✗ Storage failed: {e}")
        return False

def scan_existing_log():
    """Scan existing log for unprocessed discoveries"""
    if not log_file.exists():
        print("[Monitor] No log file found")
        return 0

    print("[Monitor] Scanning existing log...")

    with open(log_file, 'r') as f:
        content = f.read()

    matches = list(discovery_pattern.findall(content))
    current_count = get_discovery_count()

    new_discoveries = 0
    for i, (statement, r_val, p_val) in enumerate(matches):
        if i >= current_count:
            if store_discovery(statement, r_val, p_val, i):
                new_discoveries += 1
                print(f"[Monitor] ✓ Stored: {statement[:50]}...")

    print(f"[Monitor] ✓ Stored {new_discoveries} new discoveries")
    return new_discoveries

# Initial scan
initial_new = scan_existing_log()
last_discovery_count = get_discovery_count()
print(f"[Monitor] Total discoveries in memory: {last_discovery_count}")

# Get current file size
if log_file.exists():
    last_position = log_file.stat().st_size

# Start monitoring
print(f"\n[Monitor] Starting continuous monitoring (check every 5s)...")
print("[Monitor] Press Ctrl+C to stop\n")

try:
    while True:
        if log_file.exists():
            current_size = log_file.stat().st_size

            # If file grew, read new content
            if current_size > last_position:
                with open(log_file, 'r') as f:
                    f.seek(last_position)
                    new_content = f.read()

                # Look for discoveries
                matches = list(discovery_pattern.findall(new_content))

                if matches:
                    print(f"[Monitor] Found {len(matches)} new discoveries!")

                    for i, (statement, r_val, p_val) in enumerate(matches):
                        discovery_index = last_discovery_count + i
                        if store_discovery(statement, r_val, p_val, discovery_index):
                            print(f"[Monitor] ✓ Stored: {statement[:50]}...")

                    last_discovery_count += len(matches)

                last_position = current_size

        # Wait before next check
        time.sleep(5)

except KeyboardInterrupt:
    print("\n[Monitor] Stopped by user")
    final_count = get_discovery_count()
    print(f"[Monitor] Total discoveries in memory: {final_count}")
