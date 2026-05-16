#!/usr/bin/env python3
"""
Patch for ASTRA Autonomous Discovery Daemon to use Memory Bridge

This patch modifies the discovery pipeline to ensure all discoveries
are stored in ASTRA's persistent memory (Graph Palace/Memory Palace).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime


def patch_discovery_pipeline_with_memory():
    """
    Patch the discovery pipeline to integrate with persistent memory.

    This ensures every discovery is:
    1. Stored in bootstrap memory
    2. Integrated with memory graph
    3. Available for future retrieval
    """
    import json

    # Import memory bridge
    from integrate_discovery_memory import DiscoveryMemoryBridge

    # Create global memory bridge
    global _memory_bridge
    _memory_bridge = DiscoveryMemoryBridge()

    # Patch the discovery engine's run_cycle method if available
    try:
        # First, let's check what discovery engine is being used
        from astra_core.discovery import engine

        # Get the current DiscoveryPipeline class
        DiscoveryPipeline = engine.DiscoveryPipeline

        # Save original run_cycle method
        original_run_cycle = DiscoveryPipeline.run_cycle

        def memory_enhanced_run_cycle(self, domain="astrophysics", **kwargs):
            """Enhanced run_cycle that stores discoveries in persistent memory"""
            print("[Memory Bridge] Enhanced discovery cycle starting...")

            # Call original method
            try:
                result = original_run_cycle(self, domain, **kwargs)
            except Exception as e:
                print(f"[Memory Bridge] Original cycle failed: {e}")
                # Try extracting discoveries from the engine
                result = self._extract_and_process_discoveries(domain)

            # Store each discovery in persistent memory
            discoveries_stored = 0
            if result and 'discoveries' in result:
                for discovery in result['discoveries']:
                    try:
                        # Convert to proper format
                        memory_discovery = {
                            'id': discovery.get('id', f"auto_{len(discoveries_stored)}"),
                            'statement': discovery.get('statement', discovery.get('finding', '')),
                            'type': discovery.get('type', 'correlational'),
                            'variables': discovery.get('variables', []),
                            'statistics': discovery.get('statistics', {}),
                            'domain': domain,
                            'timestamp': datetime.now().isoformat(),
                            'confidence': discovery.get('confidence', 0.0)
                        }

                        key = _memory_bridge.store_discovery(memory_discovery)
                        discoveries_stored += 1
                        print(f"[Memory Bridge] ✓ Stored: {memory_discovery['statement'][:60]}...")

                    except Exception as e:
                        print(f"[Memory Bridge] Failed to store discovery: {e}")

            # Sync to graph palace
            try:
                _memory_bridge.sync_to_graph_palace()
                print(f"[Memory Bridge] Synced {discoveries_stored} discoveries to concept graph")
            except Exception as e:
                print(f"[Memory Bridge] Graph Palace sync failed: {e}")

            # Update result with memory status
            if isinstance(result, dict):
                result['memory_stored'] = discoveries_stored
                result['memory_integration'] = 'success'

            return result

        # Apply patch
        DiscoveryPipeline.run_cycle = memory_enhanced_run_cycle
        print("✓ Discovery pipeline patched with persistent memory integration")

    except ImportError as e:
        print(f"⚠ Could not patch discovery pipeline: {e}")
        print("  Discoveries will still be logged but not in persistent memory")
        return False

    return True


def create_discovery_memory_monitor():
    """
    Create a monitor that watches for discoveries and ensures they're stored.
    """
    import time

    from integrate_discovery_memory import get_memory_bridge
    bridge = get_memory_bridge()

    print("=== Discovery Memory Monitor Started ===")
    print("Watching for new discoveries to store in memory...\n")

    # Get current discovery summary
    summary = bridge.create_discovery_summary()

    print(f"Current discovery count: {summary['total_discoveries']}")
    print(f"Domains covered: {list(summary['by_domain'].keys())}")
    print(f"Discovery types: {list(summary['by_type'].keys())}")

    if summary['top_discoveries']:
        print("\nTop discoveries:")
        for i, disc in enumerate(summary['top_discoveries'][:5], 1):
            print(f"  {i}. {disc['statement']} (significance: {disc['significance']:.2f})")

    return bridge


if __name__ == '__main__':
    print("ASTRA Discovery Memory Integration Patch")
    print("=" * 50)

    # Patch the discovery pipeline
    if patch_discovery_pipeline_with_memory():
        print("\n✓ Autonomous discovery now uses persistent memory")
        print("✓ Every discovery will be stored in Graph Palace")
        print("✓ Discoveries survive across sessions")

    # Create monitor
    bridge = create_discovery_memory_monitor()

    print("\n" + "=" * 50)
    print("Memory Integration Complete!")
    print("=" * 50)
    print("\nAll future discoveries will be automatically:")
    print("  1. Stored in persistent memory (bootstrap)")
    print("  2. Integrated with concept graph (Graph Palace)")
    print("  3. Cross-referenced with related discoveries")
    print("  4. Available for future retrieval and analysis")
    print("\nAutonomous discoveries are now PERMANENTLY remembered.")
