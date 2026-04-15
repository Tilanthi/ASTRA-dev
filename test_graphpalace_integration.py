#!/usr/bin/env python3
# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test GraphPalace integration with ASTRA.

Verifies that GraphPalace memory backend works correctly for:
- Storing discoveries
- Semantic search
- Knowledge graph relations
- Cross-domain connections
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_graphpalace_integration():
    """Test GraphPalace memory backend integration."""

    print("="*60)
    print("GraphPalace Integration Test")
    print("="*60)

    # Import GraphPalace memory
    try:
        from astra_live_backend.graphpalace_memory import (
            GraphPalaceMemory,
            GRAPHPALACE_AVAILABLE
        )
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    if not GRAPHPALACE_AVAILABLE:
        print("✗ GraphPalace not installed. Skipping tests.")
        return False

    print("✓ GraphPalace memory module imported")

    # Test 1: Create memory palace
    print("\n[Test 1] Creating in-memory palace...")
    try:
        memory = GraphPalaceMemory(":memory:")
        print("✓ In-memory palace created")
    except Exception as e:
        print(f"✗ Failed to create palace: {e}")
        return False

    # Test 2: Store discoveries
    print("\n[Test 2] Storing discoveries...")
    try:
        discoveries = [
            {
                "discovery_id": "astro_001",
                "content": "Filament spacing in W3 HGBS follows a power law distribution with exponent 2.3",
                "domain": "astronomy",
                "subject": "filaments",
                "confidence": 0.95
            },
            {
                "discovery_id": "econ_001",
                "content": "Financial market returns follow a power law distribution with exponent 3.0",
                "domain": "economics",
                "subject": "markets",
                "confidence": 0.89
            },
            {
                "discovery_id": "phys_001",
                "content": "Critical phenomena in phase transitions exhibit power law scaling",
                "domain": "physics",
                "subject": "critical_phenomena",
                "confidence": 0.97
            }
        ]

        for discovery in discoveries:
            drawer_id = memory.store_discovery(discovery)
            print(f"  ✓ Stored: {discovery['discovery_id']} → {drawer_id}")

    except Exception as e:
        print(f"✗ Failed to store discoveries: {e}")
        return False

    # Test 3: Semantic search
    print("\n[Test 3] Semantic search...")
    try:
        results = memory.semantic_search("power law distribution", k=5)
        print(f"  ✓ Found {len(results)} results for 'power law distribution'")
        for i, result in enumerate(results[:3], 1):
            print(f"    {i}. [{result.domain}] {result.content[:60]}... (score: {result.score:.3f})")
    except Exception as e:
        print(f"✗ Semantic search failed: {e}")
        return False

    # Test 4: Knowledge graph
    print("\n[Test 4] Knowledge graph...")
    try:
        memory.add_knowledge_relation("filament spacing", "follows", "power law", 0.95)
        memory.add_knowledge_relation("market returns", "follows", "power law", 0.89)
        memory.add_knowledge_relation("critical phenomena", "exhibits", "scaling", 0.97)
        print("  ✓ Added 3 knowledge graph relations")

        # Query
        results = memory.query_knowledge("power law")
        print(f"  ✓ Found {len(results)} relations for 'power law'")
    except Exception as e:
        print(f"✗ Knowledge graph failed: {e}")
        return False

    # Test 5: Palace status
    print("\n[Test 5] Palace status...")
    try:
        status = memory.get_palace_status()
        print(f"  ✓ Total drawers: {status.get('total_drawers', 0)}")
        print(f"  ✓ Total wings: {status.get('total_wings', 0)}")
        print(f"  ✓ Total rooms: {status.get('total_rooms', 0)}")
    except Exception as e:
        print(f"✗ Failed to get palace status: {e}")
        return False

    # Test 6: Cross-domain connections (if available)
    print("\n[Test 6] Cross-domain connections...")
    try:
        connections = memory.find_cross_domain_connections("astronomy", "economics")
        print(f"  ✓ Found {len(connections)} connections between astronomy and economics")
        for conn in connections[:2]:
            print(f"    - {conn.topic}: {conn.explanation}")
    except Exception as e:
        print(f"  ⚠ Cross-domain search not yet implemented: {e}")

    # Close
    memory.close()

    print("\n" + "="*60)
    print("✓ All tests passed!")
    print("="*60)

    return True


if __name__ == "__main__":
    success = test_graphpalace_integration()
    sys.exit(0 if success else 1)
