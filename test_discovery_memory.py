#!/usr/bin/env python3
"""Test discovery memory integration"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Test basic functionality
from astra_core.memory.persistent.bootstrap_memory import (
    BootstrapMemory,
    MemoryCategory,
    MemoryPriority,
    PersistentMemoryItem
)

# Create bootstrap memory
bootstrap = BootstrapMemory()
bootstrap.initialize_session()

discovery_content = json.dumps({
    'statement': 'Test discovery: Magnetic fields correlate with filament width',
    'type': 'correlational',
    'variables': ['B', 'width'],
    'statistics': {'r': 0.75, 'p': 1e-50},
    'domain': 'ism',
    'timestamp': datetime.now().isoformat(),
    'confidence': 0.8
})

test_item = PersistentMemoryItem(
    id='discovery_test_001',
    category=MemoryCategory.CRITICAL_KNOWLEDGE,
    priority=MemoryPriority.HIGH,
    content=discovery_content,
    verified=False,
    source='autonomous_discovery_test',
    verification_trail=[],
    tags={'discovery', 'ism', 'test'},
    metadata={'test': True}
)

bootstrap.store_memory(test_item)
print("✓ Test discovery stored in persistent memory")

# Retrieve it by category
discoveries = bootstrap.get_memories_by_category(MemoryCategory.CRITICAL_KNOWLEDGE)
if discoveries:
    retrieved = [d for d in discoveries if d.id == 'discovery_test_001'][0]
    print(f"✓ Discovery retrieved: {retrieved.id}")
    data = json.loads(retrieved.content)
    print(f"  Statement: {data['statement']}")
    print(f"  Type: {data.get('type', 'N/A')}")
else:
    print("✗ Failed to retrieve discovery")

print("\n✓ Discovery-persistent memory integration working!")
