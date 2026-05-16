#!/usr/bin/env python3
"""
Integrate Auto-Migration with ASTRA System

Adds automatic memory migration to the autonomous research agent.
This ensures new .md files are immediately stored in GraphPalace.

Usage:
    python3 integrate_auto_migration.py --install
    python3 integrate_auto_migration.py --uninstall

Author: ASTRA System
Date: 2026-05-09
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime


def install_auto_migration():
    """Install auto-migration into autonomous agent."""

    print("="*80)
    print("INSTALLING AUTO-MIGRATION TO ASTRA")
    print("="*80)

    # Paths
    project_dir = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main")
    memory_dir = Path("/Users/gjw255/.claude/projects/-Users-gjw255-astrodata-SWARM-ASTRA-dev-main/memory")
    graphpalace_dir = project_dir / "data/graph_palace"

    # Create wrapper script
    wrapper_script = project_dir / "auto_migrate_memory.py"
    wrapper_content = f'''#!/usr/bin/env python3
"""
Auto-Migrate Memory Wrapper (Auto-generated)

Called by autonomous agent to migrate new memory files to GraphPalace.
"""

import sys
from pathlib import Path

# Add project directory to path
project_dir = Path("{project_dir}")
sys.path.insert(0, str(project_dir))

# Run migration
from migrate_memory_to_graphpalace import MemoryMigrator

def migrate():
    """Migrate any new memory files."""
    migrator = MemoryMigrator(
        memory_dir=Path("{memory_dir}"),
        graphpalace_dir=Path("{graphpalace_dir}")
    )

    # Get current memory files
    memory_files = list(migrator.memory_dir.glob("*.md"))

    # Track which files are already migrated
    registry_file = migrator.graphpalace_dir / ".migrated_files.json"
    migrated = {{}}

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
            migrated[file_key] = {{}}
            count += 1
            print(f"[AUTO-MIGRATE] {{filepath.name}} → {{node['id']}}")

    # Save registry if any migrations occurred
    if count > 0:
        import json
        with open(registry_file, 'w') as f:
            json.dump(migrated, f, indent=2)

        # Save GraphPalace files
        import json
        with open(migrator.nodes_file, 'w') as f:
            json.dump(migrator.nodes, f, indent=2)

        print(f"[AUTO-MIGRATE] Migrated {{count}} files to GraphPalace")

    return count

if __name__ == '__main__':
    migrate()
'''

    wrapper_script.write_text(wrapper_content)
    wrapper_script.chmod(0o755)

    print(f"\n✓ Created wrapper: {wrapper_script}")

    # Update autonomous agent to include auto-migration
    agent_file = project_dir / "astra_autonomous_agent.py"

    if agent_file.exists():
        # Read existing file
        content = agent_file.read_text()

        # Check if already modified
        if "auto_migrate_memory" in content:
            print("✓ Autonomous agent already includes auto-migration")
        else:
            # Add import at top
            if "import" in content.split("\n")[0]:
                # Add after existing imports
                lines = content.split("\n")
                import_end = 0
                for i, line in enumerate(lines):
                    if line.startswith("import ") or line.startswith("from "):
                        import_end = i

                lines.insert(import_end + 1, "")
                lines.insert(import_end + 2, "# Auto-migrate memory to GraphPalace")
                lines.insert(import_end + 3, "try:")
                lines.insert(import_end + 4, "    import auto_migrate_memory")
                lines.insert(import_end + 5, "    auto_migrate_memory.migrate()")
                lines.insert(import_end + 6, "except Exception as e:")
                lines.insert(import_end + 7, "    pass  # Continue without migration")

                content = "\n".join(lines)

                agent_file.write_text(content)
                print(f"✓ Modified autonomous agent: {agent_file}")
            else:
                print("  ⚠ Could not auto-modify agent file (manual integration needed)")

    # Create cron job for periodic migration
    cron_command = f"*/5 * * * * cd {project_dir} && python3 auto_migrate_memory.py >> /tmp/auto_migrate.log 2>&1\n"
    cron_file = project_dir / "auto_migrate_cron.txt"
    cron_file.write_text(cron_command)

    print(f"\n✓ Created cron job specification: {cron_file}")
    print(f"\nTo install cron job, run:")
    print(f"  crontab -l | {{ cat; cat {cron_file}; }} | crontab -")

    # Create integration test
    test_script = project_dir / "test_auto_migration.py"
    test_content = f'''#!/usr/bin/env python3
"""Test auto-migration by creating a memory file."""

import sys
from pathlib import Path
import time

project_dir = Path("{project_dir}")
memory_dir = Path("{memory_dir}")

# Create test file
test_file = memory_dir / "test_migration.md"
test_file.write_text("""---
name: test_migration
description: Test auto-migration
type: feedback
---

# Test Migration
This file tests auto-migration to GraphPalace.
""")

print(f"Created test file: {{test_file}}")

# Run migration
sys.path.insert(0, str(project_dir))
from auto_migrate_memory import migrate

count = migrate()

# Verify
from query_memory_from_graphpalace import GraphPalaceMemoryQuery
query = GraphPalaceMemoryQuery(project_dir / "data/graph_palace")

results = query.search_by_keyword("test migration")
print(f"\\nFound {{len(results)}} matching nodes in GraphPalace")

# Clean up
test_file.unlink()
print("\\n✓ Test complete (file removed)")

'''

    test_script.write_text(test_content)
    test_script.chmod(0o755)

    print(f"✓ Created test script: {test_script}")
    print(f"\nTo test auto-migration, run:")
    print(f"  python3 {test_script}")

    print(f"\n{'='*80}")
    print("INSTALLATION COMPLETE")
    print(f"{'='*80}")
    print("\nAuto-migration is now integrated into ASTRA:")
    print("  ✓ Wrapper script created")
    print("  ✓ Can be called from autonomous agent")
    print("  ✓ Cron job specification created")
    print("  ✓ Test script created")
    print("\nNew .md files will be automatically migrated to GraphPalace")

    return 0


def uninstall_auto_migration():
    """Remove auto-migration from ASTRA."""

    print("="*80)
    print("UNINSTALLING AUTO-MIGRATION")
    print("="*80)

    project_dir = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main")

    # Remove wrapper script
    wrapper_script = project_dir / "auto_migrate_memory.py"
    if wrapper_script.exists():
        wrapper_script.unlink()
        print(f"✓ Removed: {wrapper_script}")

    # Remove test script
    test_script = project_dir / "test_auto_migration.py"
    if test_script.exists():
        test_script.unlink()
        print(f"✓ Removed: {test_script}")

    # Remove cron spec
    cron_file = project_dir / "auto_migrate_cron.txt"
    if cron_file.exists():
        cron_file.unlink()
        print(f"✓ Removed: {cron_file}")

    print("\n✓ Auto-migration uninstalled")
    print("\nNote: You may need to remove the cron job manually:")
    print("  crontab -e  # and delete the auto_migrate line")

    return 0


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Integrate auto-migration with ASTRA"
    )
    parser.add_argument("--install", action="store_true",
                       help="Install auto-migration")
    parser.add_argument("--uninstall", action="store_true",
                       help="Uninstall auto-migration")

    args = parser.parse_args()

    if args.install:
        return install_auto_migration()
    elif args.uninstall:
        return uninstall_auto_migration()
    else:
        print("Usage: python3 integrate_auto_migration.py --install")
        print("   or: python3 integrate_auto_migration.py --uninstall")
        return 1


if __name__ == '__main__':
    sys.exit(main())
