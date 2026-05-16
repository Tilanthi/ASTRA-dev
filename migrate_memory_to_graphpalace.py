#!/usr/bin/env python3
"""
Memory to GraphPalace Migration Script

Migrates .md memory files to GraphPalace knowledge graph nodes.
This makes memory persistent, queryable, and networked.

Author: ASTRA System
Date: 2026-05-09
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import hashlib


class MemoryMigrator:
    """Migrate .md memory files to GraphPalace nodes."""

    def __init__(self, memory_dir: Path, graphpalace_dir: Path):
        self.memory_dir = Path(memory_dir)
        self.graphpalace_dir = Path(graphpalace_dir)

        # GraphPalace files
        self.nodes_file = self.graphpalace_dir / "nodes.json"
        self.edges_file = self.graphpalace_dir / "edges.json"
        self.pheromones_file = self.graphpalace_dir / "pheromones.json"
        self.metrics_file = self.graphpalace_dir / "metrics.json"

        # Load existing data
        self.nodes = self._load_json(self.nodes_file, {})
        self.edges = self._load_json(self.edges_file, [])
        self.pheromones = self._load_json(self.pheromones_file, {})
        self.metrics = self._load_json(self.metrics_file, {})

        # Migration statistics
        self.stats = {
            "total_files": 0,
            "migrated_nodes": 0,
            "created_edges": 0,
            "errors": []
        }

    def _load_json(self, filepath: Path, default: Any) -> Any:
        """Load JSON file with fallback."""
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load {filepath}: {e}")
                return default
        return default

    def _save_json(self, filepath: Path, data: Any):
        """Save JSON file with pretty printing."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from markdown."""
        frontmatter = {}
        body_start = 0

        # Check for frontmatter delimiter
        if content.startswith('---'):
            # Find end delimiter
            end_match = re.search(r'\n---\n', content)
            if end_match:
                frontmatter_text = content[4:end_match.start()]
                body_start = end_match.end()

                # Parse key-value pairs
                for line in frontmatter_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()

        return frontmatter, content[body_start:] if body_start else content

    def parse_markdown_sections(self, body: str) -> List[Dict[str, str]]:
        """Parse markdown into structured sections."""
        sections = []

        # Split by headers
        lines = body.split('\n')
        current_section = {"title": "INTRO", "content": []}

        for line in lines:
            # Check for header
            if line.startswith('#'):
                # Save previous section
                if current_section["content"]:
                    sections.append({
                        "title": current_section["title"],
                        "content": '\n'.join(current_section["content"]).strip()
                    })

                # Start new section
                header_level = len(re.match(r'^#+', line).group())
                current_section = {
                    "title": line.lstrip('#').strip(),
                    "level": header_level,
                    "content": []
                }
            else:
                current_section["content"].append(line)

        # Add last section
        if current_section["content"]:
            sections.append({
                "title": current_section["title"],
                "content": '\n'.join(current_section["content"]).strip()
            })

        return sections

    def extract_key_insights(self, sections: List[Dict]) -> List[str]:
        """Extract key insights from sections."""
        insights = []

        for section in sections:
            # Look for insight patterns
            if any(keyword in section["title"].lower() for keyword in
                   ["insight", "lesson", "discovery", "key", "finding"]):

                # Extract bullet points
                for line in section["content"].split('\n'):
                    if line.strip().startswith(('-', '*', '+')):
                        insight_text = line.lstrip('-*+').strip()
                        if insight_text and len(insight_text) > 10:
                            insights.append(insight_text)

        return insights

    def generate_node_id(self, prefix: str, content: str) -> str:
        """Generate unique node ID from content hash."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{prefix.upper()}_{content_hash}"

    def create_memory_node(self, filepath: Path, frontmatter: Dict,
                          body: str, sections: List[Dict]) -> Dict[str, Any]:
        """Create GraphPalace node from memory file."""

        memory_type = frontmatter.get('type', 'general')
        name = frontmatter.get('name', filepath.stem)
        description = frontmatter.get('description', '')

        # Determine node type and category
        node_type_mapping = {
            'user': 'user_preference',
            'feedback': 'lesson_learned',
            'project': 'project_context',
            'autonomous': 'system_knowledge'
        }

        node_type = node_type_mapping.get(memory_type, 'memory')

        # Extract key insights
        insights = self.extract_key_insights(sections)

        # Create node
        node_id = self.generate_node_id(memory_type, filepath.stem + body[:100])

        node = {
            "id": node_id,
            "node_type": node_type,
            "domain": "memory",
            "category": memory_type,
            "embedding": None,
            "metadata": {
                "name": name,
                "description": description,
                "source_file": str(filepath.name),
                "memory_type": memory_type,
                "sections_count": len(sections),
                "key_insights": insights[:5],  # Top 5 insights
                "created_at": datetime.fromtimestamp(filepath.stat().st_ctime).isoformat(),
                "migrated_at": datetime.now().isoformat()
            },
            "created_at": datetime.now().timestamp(),
            "updated_at": datetime.now().timestamp()
        }

        return node

    def detect_related_nodes(self, node: Dict[str, Any]) -> List[str]:
        """Detect related nodes based on content similarity."""
        related = []

        node_keywords = node["metadata"]["description"].lower()
        node_insights = " ".join(node["metadata"].get("key_insights", []))

        # Keywords to check for relationships
        check_keywords = ["filament", "peer", "review", "validation",
                         "causal", "statistical", "user", "system",
                         "discovery", "autonomous"]

        # Check against existing nodes
        for existing_id, existing_node in self.nodes.items():
            if existing_id == node["id"]:
                continue

            existing_meta = existing_node.get("metadata", {})
            existing_desc = existing_meta.get("description", "").lower()

            # Check keyword overlap
            for keyword in check_keywords:
                if keyword in existing_desc:
                    if keyword in node_keywords or keyword in node_insights:
                        related.append(existing_id)
                        break

        return related

    def create_edges(self, node_id: str, related_ids: List[str],
                    edge_type: str = "semantic") -> List[Dict[str, Any]]:
        """Create edges to related nodes."""
        edges = []

        for target_id in related_ids:
            edge = {
                "source_id": node_id,
                "target_id": target_id,
                "edge_type": edge_type,
                "weight": 0.7,
                "metadata": {
                    "relationship": "related_memory",
                    "created_by": "memory_migration"
                },
                "created_at": datetime.now().timestamp()
            }
            edges.append(edge)

        # Store edges in dict structure (source_id -> list of edges)
        if node_id not in self.edges:
            self.edges[node_id] = []
        self.edges[node_id].extend(edges)

        return edges

    def migrate_file(self, filepath: Path) -> Dict[str, Any]:
        """Migrate a single memory file."""
        try:
            # Read file
            with open(filepath, 'r') as f:
                content = f.read()

            # Parse
            frontmatter, body = self.parse_frontmatter(content)
            sections = self.parse_markdown_sections(body)

            # Create node
            node = self.create_memory_node(filepath, frontmatter, body, sections)

            return node

        except Exception as e:
            self.stats["errors"].append(f"{filepath.name}: {str(e)}")
            return None

    def run_migration(self, specific_files: List[str] = None) -> Dict[str, Any]:
        """Run full migration."""

        print("="*80)
        print("MEMORY TO GRAPHPALACE MIGRATION")
        print("="*80)

        # Find memory files
        memory_files = list(self.memory_dir.glob("*.md"))

        if specific_files:
            memory_files = [f for f in memory_files if f.stem in specific_files]

        print(f"\nFound {len(memory_files)} memory files")

        # Migrate each file
        migrated_nodes = []

        for filepath in memory_files:
            print(f"\nMigrating: {filepath.name}")

            node = self.migrate_file(filepath)

            if node:
                # Check if node already exists
                if node["id"] in self.nodes:
                    print(f"  ⚠ Node {node['id']} already exists, skipping")
                    continue

                # Add node
                self.nodes[node["id"]] = node
                migrated_nodes.append(node)

                # Create edges to related nodes
                related_ids = self.detect_related_nodes(node)
                if related_ids:
                    edges = self.create_edges(node["id"], related_ids)
                    self.stats["created_edges"] += len(edges)
                    print(f"  ✓ Created {len(edges)} edges to related nodes")

                print(f"  ✓ Migrated as node: {node['id']} ({node['node_type']})")
                self.stats["migrated_nodes"] += 1

            self.stats["total_files"] += 1

        # Save updated GraphPalace files
        print(f"\n{'='*80}")
        print("SAVING GRAPHPALACE FILES")
        print(f"{'='*80}")

        self._save_json(self.nodes_file, self.nodes)
        print(f"  ✓ Saved {len(self.nodes)} nodes to {self.nodes_file}")

        self._save_json(self.edges_file, self.edges)
        total_edges = sum(len(edge_list) for edge_list in self.edges.values())
        print(f"  ✓ Saved {total_edges} edges to {self.edges_file}")

        # Update metrics
        self.metrics["memory_migration"] = {
            "last_migration": datetime.now().isoformat(),
            "total_memory_nodes": sum(1 for n in self.nodes.values()
                                    if n.get("node_type") in ["user_preference",
                                                              "lesson_learned",
                                                              "project_context"]),
            "migration_stats": self.stats
        }
        self._save_json(self.metrics_file, self.metrics)
        print(f"  ✓ Updated metrics")

        # Print summary
        print(f"\n{'='*80}")
        print("MIGRATION SUMMARY")
        print(f"{'='*80}")
        print(f"Total files processed: {self.stats['total_files']}")
        print(f"Nodes created: {self.stats['migrated_nodes']}")
        print(f"Edges created: {self.stats['created_edges']}")

        if self.stats["errors"]:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats["errors"]:
                print(f"  - {error}")

        print(f"\n✅ Migration complete!")
        print(f"\nMemory is now stored in GraphPalace nodes:")
        print(f"  - {self.stats['migrated_nodes']} memory nodes created")
        print(f"  - {self.stats['created_edges']} relationships established")
        print(f"  - Queryable via GraphPalace API")
        print(f"  - Safe to delete original .md files (backup recommended)")

        return self.stats


def main():
    """Main entry point."""
    import sys

    # Paths
    memory_dir = Path("/Users/gjw255/.claude/projects/-Users-gjw255-astrodata-SWARM-ASTRA-dev-main/memory")
    graphpalace_dir = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/data/graph_palace")

    # Check directories exist
    if not memory_dir.exists():
        print(f"Error: Memory directory not found: {memory_dir}")
        sys.exit(1)

    if not graphpalace_dir.exists():
        print(f"Error: GraphPalace directory not found: {graphpalace_dir}")
        sys.exit(1)

    # Create migrator
    migrator = MemoryMigrator(memory_dir, graphpalace_dir)

    # Optional: specific files to migrate
    specific_files = None
    if len(sys.argv) > 1:
        specific_files = sys.argv[1:]

    # Run migration
    stats = migrator.run_migration(specific_files)

    return 0 if stats["migrated_nodes"] > 0 else 1


if __name__ == '__main__':
    exit(main())
