#!/usr/bin/env python3
"""
Automatic Memory Migration to GraphPalace

Watches the memory directory for new .md files and automatically
migrates them to GraphPalace knowledge graph nodes.

This runs as a background daemon and integrates with the autonomous
research agent system.

Usage:
    python3 auto_migrate_memory_to_graphpalace.py --daemon
    python3 auto_migrate_memory_to_graphpalace.py --once
    python3 auto_migrate_memory_to_graphpalace.py --status

Author: ASTRA System
Date: 2026-05-09
"""

import os
import sys
import json
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Try to import watchdog for file watching
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. Install with: pip3 install watchdog")
    print("Falling back to polling mode (less efficient)")


class MemoryMigrationHandler:
    """Handle memory migration to GraphPalace."""

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

        # Track migrated files
        self.migrated_files = self._load_migration_registry()

        # Statistics
        self.stats = {
            "total_migrations": 0,
            "auto_migrations": 0,
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

    def _load_migration_registry(self) -> Dict[str, float]:
        """Load registry of migrated files."""
        registry_file = self.graphpalace_dir / ".migrated_files.json"
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_migration_registry(self):
        """Save registry of migrated files."""
        registry_file = self.graphpalace_dir / ".migrated_files.json"
        with open(registry_file, 'w') as f:
            json.dump(self.migrated_files, f, indent=2)

    def parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from markdown."""
        frontmatter = {}
        body_start = 0

        if content.startswith('---'):
            end_match = content.find('\n---\n', 4)
            if end_match > 0:
                frontmatter_text = content[4:end_match]
                body_start = end_match + 5

                for line in frontmatter_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()

        return frontmatter, content[body_start:] if body_start else content

    def extract_insights(self, body: str) -> List[str]:
        """Extract key insights from markdown content."""
        insights = []
        lines = body.split('\n')
        capture_next = False

        for line in lines:
            line = line.strip()

            # Look for insight/lesson/finding sections
            if any(keyword in line.lower() for keyword in
                   ["key insight", "lesson", "discovery", "finding", "learned"]):
                capture_next = True
                continue

            # Capture bullet points in insight sections
            if capture_next and line.startswith(('-', '*', '+')):
                insight = line.lstrip('-*+').strip()
                if insight and len(insight) > 10:
                    insights.append(insight)

            # Stop capturing at next section
            if line.startswith('#') and capture_next:
                capture_next = False

        return insights[:5]  # Top 5 insights

    def generate_node_id(self, memory_type: str, content: str) -> str:
        """Generate unique node ID."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        type_prefix = {
            'user': 'USER',
            'feedback': 'FEEDBACK',
            'project': 'PROJECT',
            'autonomous': 'SYSTEM'
        }.get(memory_type, 'MEMORY')
        return f"{type_prefix}_{content_hash}"

    def migrate_file(self, filepath: Path) -> Optional[str]:
        """Migrate a single memory file to GraphPalace."""
        try:
            # Check if already migrated
            file_key = str(filepath)
            if file_key in self.migrated_files:
                return None

            # Read file
            with open(filepath, 'r') as f:
                content = f.read()

            # Parse
            frontmatter, body = self.parse_frontmatter(content)
            memory_type = frontmatter.get('type', 'general')
            name = frontmatter.get('name', filepath.stem)
            description = frontmatter.get('description', '')

            # Extract insights
            insights = self.extract_insights(body)

            # Determine node type
            node_type_map = {
                'user': 'user_preference',
                'feedback': 'lesson_learned',
                'project': 'project_context',
                'autonomous': 'system_knowledge'
            }
            node_type = node_type_map.get(memory_type, 'memory')

            # Create node
            node_id = self.generate_node_id(memory_type, filepath.stem + body[:100])

            # Check if node exists
            if node_id in self.nodes:
                # Update existing node
                self.nodes[node_id]["metadata"]["updated_at"] = datetime.now().isoformat()
            else:
                # Create new node
                self.nodes[node_id] = {
                    "id": node_id,
                    "node_type": node_type,
                    "domain": "memory",
                    "category": memory_type,
                    "embedding": None,
                    "metadata": {
                        "name": name,
                        "description": description,
                        "source_file": filepath.name,
                        "memory_type": memory_type,
                        "key_insights": insights,
                        "auto_migrated": True,
                        "created_at": datetime.fromtimestamp(
                            filepath.stat().st_ctime
                        ).isoformat(),
                        "migrated_at": datetime.now().isoformat()
                    },
                    "created_at": datetime.now().timestamp(),
                    "updated_at": datetime.now().timestamp()
                }

            # Mark as migrated
            self.migrated_files[file_key] = datetime.now().timestamp()

            # Save GraphPalace files
            self._save_json(self.nodes_file, self.nodes)
            self._save_migration_registry()

            # Update metrics
            self._update_metrics(node_type, auto=True)

            return node_id

        except Exception as e:
            error_msg = f"{filepath.name}: {str(e)}"
            self.stats["errors"].append(error_msg)
            print(f"Error migrating {filepath.name}: {e}")
            return None

    def _update_metrics(self, node_type: str, auto: bool = True):
        """Update migration metrics."""
        if "memory_migration" not in self.metrics:
            self.metrics["memory_migration"] = {
                "last_migration": None,
                "total_memory_nodes": 0,
                "migration_stats": {
                    "migrated_nodes": 0,
                    "auto_migrations": 0,
                    "errors": []
                }
            }

        self.metrics["memory_migration"]["last_migration"] = datetime.now().isoformat()
        self.metrics["memory_migration"]["total_memory_nodes"] = sum(
            1 for n in self.nodes.values()
            if n.get("node_type") in ["user_preference", "lesson_learned",
                                      "project_context", "memory"]
        )
        self.metrics["memory_migration"]["migration_stats"]["migrated_nodes"] += 1

        if auto:
            self.metrics["memory_migration"]["migration_stats"]["auto_migrations"] += 1

        self._save_json(self.metrics_file, self.metrics)

    def migrate_existing_files(self):
        """Migrate any existing files that haven't been migrated yet."""
        memory_files = list(self.memory_dir.glob("*.md"))
        migrated_count = 0

        for filepath in memory_files:
            node_id = self.migrate_file(filepath)
            if node_id:
                print(f"✓ Auto-migrated: {filepath.name} → {node_id}")
                migrated_count += 1

        return migrated_count


class MemoryFileWatcher(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """Watch for new memory files and auto-migrate them."""

    def __init__(self, migration_handler: MemoryMigrationHandler):
        self.handler = migration_handler
        self.cooldown = {}  # Prevent duplicate migrations

    def on_created(self, event):
        """Handle file creation event."""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Only process .md files
        if filepath.suffix != '.md':
            return

        # Cooldown: prevent processing same file twice quickly
        now = time.time()
        file_key = str(filepath)
        if file_key in self.cooldown and (now - self.cooldown[file_key]) < 2:
            return

        self.cooldown[file_key] = now

        # Wait a moment for file write to complete
        time.sleep(0.5)

        # Migrate file
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] New memory file detected: {filepath.name}")
        node_id = self.handler.migrate_file(filepath)

        if node_id:
            print(f"✓ Auto-migrated: {filepath.name} → {node_id}")
        else:
            print(f"- Skipped: {filepath.name} (already migrated)")


def run_once(memory_dir: Path, graphpalace_dir: Path):
    """Run single migration pass."""
    handler = MemoryMigrationHandler(memory_dir, graphpalace_dir)

    print("="*80)
    print("AUTO MIGRATE MEMORY TO GRAPHPALACE")
    print("="*80)
    print(f"\nMemory directory: {memory_dir}")
    print(f"GraphPalace directory: {graphpalace_dir}")

    print(f"\nMigrating existing files...")
    count = handler.migrate_existing_files()

    print(f"\n✓ Migrated {count} files")

    return 0


def run_daemon(memory_dir: Path, graphpalace_dir: Path, pidfile: Path = None):
    """Run continuous file watcher daemon."""

    if not WATCHDOG_AVAILABLE:
        print("Error: watchdog library not available for daemon mode")
        print("Install with: pip3 install watchdog")
        return 1

    handler = MemoryMigrationHandler(memory_dir, graphpalace_dir)

    # Migrate existing files first
    print("Migrating existing files...")
    handler.migrate_existing_files()

    # Setup file watcher
    observer = Observer()
    watcher = MemoryFileWatcher(handler)
    observer.schedule(watcher, str(memory_dir), recursive=False)
    observer.start()

    # Write PID file
    if pidfile:
        pidfile.write_text(str(os.getpid()))

    print("="*80)
    print("AUTO MIGRATE DAEMON RUNNING")
    print("="*80)
    print(f"Memory directory: {memory_dir}")
    print(f"GraphPalace directory: {graphpalace_dir}")
    print(f"PID: {os.getpid()}")
    print("\nWatching for new .md files...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping daemon...")
        observer.stop()
        if pidfile and pidfile.exists():
            pidfile.unlink()
        print("✓ Daemon stopped")

    observer.join()
    return 0


def show_status(memory_dir: Path, graphpalace_dir: Path):
    """Show migration status."""

    print("="*80)
    print("MEMORY MIGRATION STATUS")
    print("="*80)

    # Check GraphPalace
    nodes_file = graphpalace_dir / "nodes.json"
    if not nodes_file.exists():
        print("❌ GraphPalace not initialized")
        return 1

    with open(nodes_file) as f:
        nodes = json.load(f)

    memory_nodes = [n for n in nodes.values()
                   if n.get("node_type") in ["user_preference", "lesson_learned",
                                             "project_context", "memory"]]

    print(f"\nGraphPalace nodes: {len(nodes)}")
    print(f"Memory nodes: {len(memory_nodes)}")

    # Count by type
    type_counts = {}
    auto_count = 0
    for node in memory_nodes:
        node_type = node.get("node_type")
        type_counts[node_type] = type_counts.get(node_type, 0) + 1
        if node["metadata"].get("auto_migrated"):
            auto_count += 1

    print(f"\nBy type:")
    for node_type, count in sorted(type_counts.items()):
        print(f"  {node_type}: {count}")

    print(f"\nAuto-migrated: {auto_count}")
    print(f"Manual migration: {len(memory_nodes) - auto_count}")

    # Check migration registry
    registry_file = graphpalace_dir / ".migrated_files.json"
    if registry_file.exists():
        with open(registry_file) as f:
            registry = json.load(f)
        print(f"\nMigration registry: {len(registry)} files")

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Auto-migrate memory .md files to GraphPalace"
    )
    parser.add_argument("--daemon", action="store_true",
                       help="Run as continuous daemon")
    parser.add_argument("--once", action="store_true",
                       help="Run single migration pass")
    parser.add_argument("--status", action="store_true",
                       help="Show migration status")
    parser.add_argument("--memory-dir", type=str,
                       default="/Users/gjw255/.claude/projects/-Users-gjw255-astrodata-SWARM-ASTRA-dev-main/memory",
                       help="Memory directory path")
    parser.add_argument("--graphpalace-dir", type=str,
                       default="/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/data/graph_palace",
                       help="GraphPalace directory path")
    parser.add_argument("--pidfile", type=str,
                       default="/tmp/auto_migrate_memory.pid",
                       help="PID file for daemon")

    args = parser.parse_args()

    memory_dir = Path(args.memory_dir)
    graphpalace_dir = Path(args.graphpalace_dir)

    # Verify directories exist
    if not memory_dir.exists():
        # Create memory directory if it doesn't exist
        memory_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created memory directory: {memory_dir}")

    if not graphpalace_dir.exists():
        print(f"Error: GraphPalace directory not found: {graphpalace_dir}")
        return 1

    # Run requested mode
    if args.status:
        return show_status(memory_dir, graphpalace_dir)
    elif args.daemon:
        return run_daemon(memory_dir, graphpalace_dir, Path(args.pidfile))
    elif args.once:
        return run_once(memory_dir, graphpalace_dir)
    else:
        # Default: run once
        return run_once(memory_dir, graphpalace_dir)


if __name__ == '__main__':
    sys.exit(main())
