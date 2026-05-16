#!/usr/bin/env python3
"""
Auto-Migrate Memory Wrapper (Auto-generated)

Called by autonomous agent to migrate new memory files to GraphPalace.
"""

import sys
from pathlib import Path

# Add project directory to path
project_dir = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main")
sys.path.insert(0, str(project_dir))

# Run migration
from migrate_memory_to_graphpalace import MemoryMigrator

def migrate():
    """Migrate any new memory files."""
    migrator = MemoryMigrator(
        memory_dir=Path("/Users/gjw255/.claude/projects/-Users-gjw255-astrodata-SWARM-ASTRA-dev-main/memory"),
        graphpalace_dir=Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/data/graph_palace")
    )

    # Get current memory files
    memory_files = list(migrator.memory_dir.glob("*.md"))

    # Track which files are already migrated
    registry_file = migrator.graphpalace_dir / ".migrated_files.json"
    migrated = {}

    if registry_file.exists():
        import json
        with open(registry_file) as f:
            migrated = json.load(f)

    # Migrate new files
    count = 0
    for filepath in memory_files:
        file_key = str(filepath)

        # Skip if already migrated
        if file_key in migrated:
            continue

        # Migrate file
        node = migrator.migrate_file(filepath)

        if node:
            migrated[file_key] = {}
            count += 1
            print(f"[AUTO-MIGRATE] {filepath.name} → {node['id']}")

    # Save registry if any migrations occurred
    if count > 0:
        import json
        with open(registry_file, 'w') as f:
            json.dump(migrated, f, indent=2)

        # Save GraphPalace files
        import json
        with open(migrator.nodes_file, 'w') as f:
            json.dump(migrator.nodes, f, indent=2)

        print(f"[AUTO-MIGRATE] Migrated {count} files to GraphPalace")

    return count

if __name__ == '__main__':
    migrate()
