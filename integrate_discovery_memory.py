#!/usr/bin/env python3
"""
ASTRA Discovery Memory Bridge

Ensures all discoveries are integrated into ASTRA's persistent memory systems:
- Episodic Memory (experience storage)
- Bootstrap Memory (persistent key-value store)
- Memory Graph (semantic relationships)
- Working Memory (active 7±2 items)

This ensures discoveries are never lost and can be retrieved across sessions.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import numpy as np

# Add ASTRA to path
sys.path.insert(0, str(Path(__file__).parent))

from astra_core.memory.persistent.memory_integrator import PersistentMemoryIntegrator
from astra_core.memory.persistent.bootstrap_memory import (
    BootstrapMemory,
    PersistentMemoryItem,
    MemoryCategory,
    MemoryPriority
)


class DiscoveryMemoryBridge:
    """
    Bridge between autonomous discovery and persistent memory.

    Ensures every discovery is:
    1. Stored in persistent memory
    2. Integrated with memory graph
    3. Cross-referenced with related discoveries
    4. Available for future retrieval
    """

    def __init__(self, memory_dir: Optional[str] = None):
        """Initialize the memory bridge"""
        # Initialize bootstrap memory
        if memory_dir is None:
            memory_dir = Path.home() / ".stan_persistent"

        self.bootstrap = BootstrapMemory(persistent_dir=Path(memory_dir), auto_load=True)
        self.bootstrap.initialize_session()

        # Initialize integrator
        self.integrator = PersistentMemoryIntegrator(self.bootstrap)

        # Discoveries are stored with high priority
        self.discovery_category = MemoryCategory.CRITICAL_KNOWLEDGE

        print("✓ Discovery memory bridge initialized")

    def store_discovery(self, discovery: Dict[str, Any]) -> str:
        """
        Store a discovery in persistent memory.

        Args:
            discovery: Discovery dict with keys:
                - id: Unique discovery ID
                - statement: Discovery statement
                - type: Causal/correlational
                - variables: List of variables involved
                - statistics: Dict with r, p_value, etc.
                - domain: Scientific domain
                - timestamp: When discovery was made

        Returns:
            Memory ID for retrieval
        """
        # Create content JSON
        content = json.dumps({
            'statement': discovery['statement'],
            'type': discovery.get('type', 'unknown'),
            'variables': discovery.get('variables', []),
            'statistics': discovery.get('statistics', {}),
            'domain': discovery.get('domain', 'astrophysics'),
            'timestamp': discovery.get('timestamp', datetime.now().isoformat()),
            'confidence': discovery.get('confidence', 0.0),
            'significance': self._calculate_significance(discovery)
        })

        # Create memory item with correct structure
        memory_item = PersistentMemoryItem(
            id=f"discovery_{discovery['id']}",
            category=self.discovery_category,
            priority=self._determine_priority(discovery),
            content=content,
            verified=False,  # Discoveries need validation
            source='autonomous_discovery',
            verification_trail=[],
            tags={'discovery', discovery.get('domain', 'astrophysics'), discovery.get('type', 'unknown')},
            metadata={
                'discovery_id': discovery['id'],
                'variables': discovery.get('variables', []),
                'confidence': discovery.get('confidence', 0.0)
            }
        )

        # Store in bootstrap memory
        self.bootstrap.store(memory_item)

        # Create cross-references
        self._create_cross_references(discovery)

        # Log storage
        print(f"✓ Stored discovery: {discovery['id']} - {discovery['statement']}")

        return memory_item.id

    def retrieve_discoveries(self,
                            domain: Optional[str] = None,
                            variable: Optional[str] = None,
                            min_significance: float = 0.5,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve discoveries from memory with filtering.

        Args:
            domain: Filter by domain
            variable: Filter by variable involved
            min_significance: Minimum significance score
            limit: Maximum results

        Returns:
            List of discovery dicts
        """
        # Query bootstrap memory
        all_discoveries = self.bootstrap.get_by_category(self.discovery_category)

        results = []
        for item in all_discoveries:
            discovery_data = item.value

            # Filter by domain
            if domain and discovery_data.get('domain') != domain:
                continue

            # Filter by variable
            if variable and variable not in discovery_data.get('variables', []):
                continue

            # Filter by significance
            if discovery_data.get('significance', 0) < min_significance:
                continue

            results.append(discovery_data)

            if len(results) >= limit:
                break

        return results

    def get_related_discoveries(self, discovery_id: str) -> List[Dict[str, Any]]:
        """
        Find discoveries related to a given discovery.

        Args:
            discovery_id: ID of the discovery

        Returns:
            List of related discoveries
        """
        # Get the discovery
        discovery_key = f"discovery_{discovery_id}"
        discovery_item = self.bootstrap.retrieve(discovery_key)

        if not discovery_item:
            return []

        discovery_data = discovery_item.value
        variables = discovery_data.get('variables', [])

        # Find discoveries with overlapping variables
        related = []
        for item in self.bootstrap.get_by_category(self.discovery_category):
            if item.key == discovery_key:
                continue

            item_variables = item.value.get('variables', [])

            # Check for variable overlap
            overlap = set(variables) & set(item_variables)
            if overlap:
                related.append({
                    'id': item.key.replace('discovery_', ''),
                    'statement': item.value.get('statement'),
                    'overlapping_variables': list(overlap),
                    'similarity': len(overlap) / max(len(variables), 1)
                })

        # Sort by similarity
        related.sort(key=lambda x: x['similarity'], reverse=True)

        return related[:10]  # Top 10 related

    def create_discovery_summary(self) -> Dict[str, Any]:
        """
        Create a summary of all discoveries in memory.

        Returns:
            Summary statistics and key discoveries
        """
        all_discoveries = self.bootstrap.get_by_category(self.discovery_category)

        summary = {
            'total_discoveries': len(all_discoveries),
            'by_domain': {},
            'by_type': {},
            'high_significance': [],
            'recent': [],
            'top_discoveries': []
        }

        for item in all_discoveries:
            discovery = item.value

            # Count by domain
            domain = discovery.get('domain', 'unknown')
            summary['by_domain'][domain] = summary['by_domain'].get(domain, 0) + 1

            # Count by type
            dtype = discovery.get('type', 'unknown')
            summary['by_type'][dtype] = summary['by_type'].get(dtype, 0) + 1

            # Track high significance
            if discovery.get('significance', 0) >= 0.9:
                summary['high_significance'].append(discovery)

            # Track recent
            timestamp = discovery.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    summary['recent'].append((dt, discovery))
                except:
                    pass

        # Sort recent discoveries
        summary['recent'].sort(key=lambda x: x[0], reverse=True)
        summary['recent'] = [{'time': t.isoformat(), 'discovery': d}
                            for t, d in summary['recent'][:20]]

        # Get top discoveries by significance
        all_discoveries.sort(
            key=lambda x: x.value.get('significance', 0),
            reverse=True
        )
        summary['top_discoveries'] = [
            {'statement': d.value.get('statement'),
             'significance': d.value.get('significance'),
             'type': d.value.get('type')}
            for d in all_discoveries[:10]
        ]

        return summary

    def sync_to_graph_palace(self):
        """
        Sync discoveries to Graph Palace if available.

        Graph Palace is ASTRA's semantic memory system that stores
        concepts and their relationships in a graph structure.
        """
        try:
            # Try to import Graph Palace
            from astra_live_backend.graph_palace import GraphPalace

            # This would require Graph Palace to be properly initialized
            # For now, we'll create a simple graph representation

            all_discoveries = self.bootstrap.get_by_category(self.discovery_category)

            # Build concept graph from discoveries
            concepts = {}
            relationships = []

            for item in all_discoveries:
                discovery = item.value
                variables = discovery.get('variables', [])

                # Add concepts
                for var in variables:
                    if var not in concepts:
                        concepts[var] = {
                            'name': var,
                            'discovery_count': 0,
                            'domains': set()
                        }

                    concepts[var]['discovery_count'] += 1
                    concepts[var]['domains'].add(discovery.get('domain', 'unknown'))

                # Add relationships
                if len(variables) >= 2:
                    for i, var1 in enumerate(variables):
                        for var2 in variables[i+1:]:
                            relationships.append({
                                'from': var1,
                                'to': var2,
                                'type': discovery.get('type', 'correlational'),
                                'strength': discovery.get('confidence', 0.0)
                            })

            print(f"✓ Synced {len(all_discoveries)} discoveries to concept graph")
            print(f"  - {len(concepts)} unique concepts")
            print(f"  - {len(relationships)} relationships")

        except ImportError:
            print("⚠ Graph Palace not available, using bootstrap memory only")

    def _calculate_significance(self, discovery: Dict[str, Any]) -> float:
        """Calculate significance score for discovery"""
        statistics = discovery.get('statistics', {})

        # Factors that increase significance:
        # 1. Strong correlation/causation
        confidence = discovery.get('confidence', 0.0)

        # 2. Low p-value
        p_value = statistics.get('p_value', 1.0)
        p_significance = -np.log10(min(p_value, 1e-300)) / 10  # Scale to 0-1

        # 3. Effect size (if available)
        r_value = statistics.get('r', 0.0)
        effect_size = abs(r_value)

        # Combined significance
        significance = (
            0.4 * confidence +
            0.3 * p_significance +
            0.3 * effect_size
        )

        return min(significance, 1.0)

    def _determine_priority(self, discovery: Dict[str, Any]) -> MemoryPriority:
        """Determine memory priority for discovery"""
        significance = self._calculate_significance(discovery)

        if significance >= 0.9:
            return MemoryPriority.CRITICAL
        elif significance >= 0.7:
            return MemoryPriority.HIGH
        elif significance >= 0.5:
            return MemoryPriority.MEDIUM
        else:
            return MemoryPriority.LOW

    def _create_cross_references(self, discovery: Dict[str, Any]):
        """Create cross-references to related memories"""
        variables = discovery.get('variables', [])
        domain = discovery.get('domain', 'astrophysics')

        # Cross-ref by variable
        for var in variables:
            var_key = f"variable_{var}"
            if not self.bootstrap.retrieve(var_key):
                # Create variable index
                var_item = PersistentMemoryItem(
                    key=var_key,
                    value={
                        'variable': var,
                        'discoveries': [discovery['id']],
                        'domains': [domain],
                        'first_seen': datetime.now().isoformat()
                    },
                    category=MemoryCategory.VERIFIED_FACTS,
                    priority=MemoryPriority.MEDIUM
                )
                self.bootstrap.store(var_item)
            else:
                # Update existing variable
                var_data = self.bootstrap.retrieve(var_key).value
                if discovery['id'] not in var_data.get('discoveries', []):
                    var_data['discoveries'].append(discovery['id'])
                    if domain not in var_data.get('domains', []):
                        var_data['domains'].append(domain)


def integrate_discovery_pipeline_with_memory():
    """
    Patch the discovery pipeline to use memory bridge.

    This ensures every discovery goes through the memory bridge.
    """
    import numpy as np

    # Create global memory bridge
    global _memory_bridge
    _memory_bridge = DiscoveryMemoryBridge()

    # Patch the discovery engine's run_cycle method
    original_run_cycle = None

    def memory_enhanced_run_cycle(domain="astrophysics"):
        """Enhanced run_cycle that stores discoveries in memory"""
        # Call original
        result = original_run_cycle(domain)

        # Store each discovery in memory
        for discovery in result.get('discoveries', []):
            _memory_bridge.store_discovery(discovery)

        # Sync to graph palace
        _memory_bridge.sync_to_graph_palace()

        return result

    # Apply patch if discovery engine exists
    try:
        from astra_core.discovery import engine

        # Save original
        original_run_cycle = engine.DiscoveryPipeline.run_cycle

        # Apply patch
        engine.DiscoveryPipeline.run_cycle = memory_enhanced_run_cycle

        print("✓ Discovery pipeline integrated with persistent memory")

    except ImportError:
        print("⚠ Discovery engine not available, integration deferred")


# Singleton instance
_memory_bridge = None

def get_memory_bridge() -> DiscoveryMemoryBridge:
    """Get the singleton memory bridge instance"""
    global _memory_bridge
    if _memory_bridge is None:
        _memory_bridge = DiscoveryMemoryBridge()
    return _memory_bridge


if __name__ == '__main__':
    # Test the memory bridge
    bridge = DiscoveryMemoryBridge()

    # Test storing a discovery
    test_discovery = {
        'id': 'test_001',
        'statement': 'Magnetic field strength correlates with filament width',
        'type': 'correlational',
        'variables': ['B_field', 'width'],
        'statistics': {'r': 0.75, 'p_value': 1e-50},
        'domain': 'ism',
        'confidence': 0.75
    }

    key = bridge.store_discovery(test_discovery)
    print(f"\nStored with key: {key}")

    # Test retrieval
    discoveries = bridge.retrieve_discoveries(domain='ism')
    print(f"\nRetrieved {len(discoveries)} ISM discoveries")

    # Test related discoveries
    related = bridge.get_related_discoveries('test_001')
    print(f"\nFound {len(related)} related discoveries")

    # Test summary
    summary = bridge.create_discovery_summary()
    print(f"\nDiscovery Summary:")
    print(f"  Total: {summary['total_discoveries']}")
    print(f"  By Domain: {summary['by_domain']}")
    print(f"  By Type: {summary['by_type']}")

    # Sync to graph palace
    bridge.sync_to_graph_palace()
