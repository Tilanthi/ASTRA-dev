#!/usr/bin/env python3
"""
Query Memory from GraphPalace

Demonstrates that migrated memory is now queryable from GraphPalace knowledge graph.

Usage:
    python query_memory_from_graphpalace.py --type lesson_learned
    python query_memory_from_graphpalace.py --query "peer review"
    python query_memory_from_graphpalace.py --stats
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any


class GraphPalaceMemoryQuery:
    """Query migrated memory from GraphPalace."""

    def __init__(self, graphpalace_dir: Path):
        self.graphpalace_dir = Path(graphpalace_dir)

        # Load data
        with open(self.graphpalace_dir / "nodes.json") as f:
            self.nodes = json.load(f)
        with open(self.graphpalace_dir / "edges.json") as f:
            self.edges = json.load(f)
        with open(self.graphpalace_dir / "metrics.json") as f:
            self.metrics = json.load(f)

    def list_memory_nodes(self) -> List[Dict]:
        """List all memory-type nodes."""
        memory_types = ["user_preference", "lesson_learned",
                       "project_context", "memory", "system_knowledge"]

        memory_nodes = []
        for node_id, node in self.nodes.items():
            if node.get("node_type") in memory_types:
                memory_nodes.append(node)

        return sorted(memory_nodes, key=lambda x: x["created_at"])

    def filter_by_type(self, node_type: str) -> List[Dict]:
        """Filter memory nodes by type."""
        return [n for n in self.nodes.values()
                if n.get("node_type") == node_type]

    def search_by_keyword(self, keyword: str) -> List[Dict]:
        """Search memory nodes by keyword."""
        keyword_lower = keyword.lower()
        results = []

        for node in self.nodes.values():
            # Search in metadata
            metadata = node.get("metadata", {})

            # Check description
            if keyword_lower in metadata.get("description", "").lower():
                results.append(node)
                continue

            # Check insights
            insights = metadata.get("key_insights", [])
            for insight in insights:
                if keyword_lower in insight.lower():
                    results.append(node)
                    break

        return results

    def get_node_connections(self, node_id: str) -> Dict[str, List]:
        """Get all connections for a node."""
        connections = {"outgoing": [], "incoming": []}

        # Outgoing edges
        if node_id in self.edges:
            for edge in self.edges[node_id]:
                target_id = edge["target_id"]
                if target_id in self.nodes:
                    connections["outgoing"].append({
                        "target": target_id,
                        "type": edge["edge_type"],
                        "weight": edge["weight"]
                    })

        # Incoming edges
        for source_id, edge_list in self.edges.items():
            for edge in edge_list:
                if edge["target_id"] == node_id:
                    connections["incoming"].append({
                        "source": source_id,
                        "type": edge["edge_type"],
                        "weight": edge["weight"]
                    })

        return connections

    def print_stats(self):
        """Print memory statistics."""
        memory_nodes = self.list_memory_nodes()

        print("="*80)
        print("GRAPHPALACE MEMORY STATISTICS")
        print("="*80)

        print(f"\nTotal nodes: {len(self.nodes)}")
        print(f"Memory nodes: {len(memory_nodes)}")

        # Count by type
        type_counts = {}
        for node in memory_nodes:
            node_type = node.get("node_type", "unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1

        print(f"\nMemory nodes by type:")
        for node_type, count in sorted(type_counts.items()):
            print(f"  {node_type}: {count}")

        print(f"\nMigration info:")
        migration = self.metrics.get("memory_migration", {})
        if migration:
            print(f"  Last migration: {migration.get('last_migration', 'Unknown')}")
            stats = migration.get("migration_stats", {})
            print(f"  Migrated: {stats.get('migrated_nodes', 0)} nodes")

    def print_memory_list(self, memory_type: str = None):
        """Print list of memory nodes."""
        memory_nodes = self.list_memory_nodes()

        if memory_type:
            memory_nodes = [n for n in memory_nodes
                          if n.get("node_type") == memory_type]
            print(f"\n{'='*80}")
            print(f"MEMORY NODES: {memory_type}")
            print(f"{'='*80}")
        else:
            print(f"\n{'='*80}")
            print("ALL MEMORY NODES")
            print(f"{'='*80}")

        for node in memory_nodes:
            metadata = node.get("metadata", {})
            name = metadata.get("name", node["id"])
            description = metadata.get("description", "")

            print(f"\n[{node['id']}] {name}")
            print(f"  Type: {node.get('node_type')}")
            print(f"  Description: {description}")

            insights = metadata.get("key_insights", [])
            if insights:
                print(f"  Key Insights:")
                for insight in insights[:3]:  # Show top 3
                    print(f"    - {insight[:80]}...")

    def print_search_results(self, keyword: str):
        """Print search results."""
        results = self.search_by_keyword(keyword)

        print(f"\n{'='*80}")
        print(f"SEARCH RESULTS: '{keyword}'")
        print(f"{'='*80}")
        print(f"Found {len(results)} matching nodes\n")

        for node in results:
            metadata = node.get("metadata", {})
            name = metadata.get("name", node["id"])
            description = metadata.get("description", "")

            print(f"[{node['id']}] {name}")
            print(f"  Description: {description}")

            insights = metadata.get("key_insights", [])
            matching_insights = [i for i in insights if keyword.lower() in i.lower()]
            if matching_insights:
                print(f"  Matching insights:")
                for insight in matching_insights:
                    print(f"    - {insight}")

    def print_node_detail(self, node_id: str):
        """Print detailed information about a node."""
        if node_id not in self.nodes:
            print(f"Error: Node {node_id} not found")
            return

        node = self.nodes[node_id]
        metadata = node.get("metadata", {})

        print(f"\n{'='*80}")
        print(f"NODE DETAIL: {node_id}")
        print(f"{'='*80}")

        print(f"\nName: {metadata.get('name', 'N/A')}")
        print(f"Type: {node.get('node_type')}")
        print(f"Description: {metadata.get('description', 'N/A')}")
        print(f"Created: {metadata.get('created_at', 'N/A')}")
        print(f"Migrated: {metadata.get('migrated_at', 'N/A')}")

        # Print sections count
        sections_count = metadata.get("sections_count", 0)
        print(f"Sections: {sections_count}")

        # Print insights
        insights = metadata.get("key_insights", [])
        if insights:
            print(f"\nKey Insights ({len(insights)}):")
            for i, insight in enumerate(insights, 1):
                print(f"  {i}. {insight}")

        # Print connections
        connections = self.get_node_connections(node_id)
        if connections["outgoing"]:
            print(f"\nConnected To:")
            for conn in connections["outgoing"]:
                target_node = self.nodes.get(conn["target"])
                target_name = target_node["metadata"]["name"] if target_node else conn["target"]
                print(f"  → {target_name} ({conn['type']}, weight={conn['weight']})")

        if connections["incoming"]:
            print(f"\nConnected From:")
            for conn in connections["incoming"]:
                source_node = self.nodes.get(conn["source"])
                source_name = source_node["metadata"]["name"] if source_node else conn["source"]
                print(f"  ← {source_name} ({conn['type']}, weight={conn['weight']})")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Query GraphPalace memory")
    parser.add_argument("--stats", action="store_true",
                       help="Show memory statistics")
    parser.add_argument("--list", action="store_true",
                       help="List all memory nodes")
    parser.add_argument("--type", type=str,
                       help="Filter by node type (lesson_learned, user_preference, etc.)")
    parser.add_argument("--query", type=str,
                       help="Search by keyword")
    parser.add_argument("--node", type=str,
                       help="Show detailed node information")
    parser.add_argument("--insights", action="store_true",
                       help="Show all key insights from memory")

    args = parser.parse_args()

    # Initialize query
    graphpalace_dir = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/data/graph_palace")
    query = GraphPalaceMemoryQuery(graphpalace_dir)

    # Execute query
    if args.stats:
        query.print_stats()
    elif args.type or args.list:
        query.print_memory_list(args.type)
    elif args.query:
        query.print_search_results(args.query)
    elif args.node:
        query.print_node_detail(args.node)
    elif args.insights:
        # Show all key insights
        memory_nodes = query.list_memory_nodes()
        print(f"\n{'='*80}")
        print("ALL KEY INSIGHTS FROM MIGRATED MEMORY")
        print(f"{'='*80}")

        for node in memory_nodes:
            metadata = node.get("metadata", {})
            name = metadata.get("name", node["id"])
            insights = metadata.get("key_insights", [])

            if insights:
                print(f"\n{name}:")
                for insight in insights:
                    print(f"  - {insight}")
    else:
        # Default: show stats
        query.print_stats()


if __name__ == '__main__':
    main()
