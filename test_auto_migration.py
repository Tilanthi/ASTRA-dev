#!/usr/bin/env python3
"""Test auto-migration by creating a memory file."""

import sys
from pathlib import Path
import time

project_dir = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main")
memory_dir = Path("/Users/gjw255/.claude/projects/-Users-gjw255-astrodata-SWARM-ASTRA-dev-main/memory")

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

print(f"Created test file: {test_file}")

# Run migration
sys.path.insert(0, str(project_dir))
from auto_migrate_memory import migrate

count = migrate()

# Verify
from query_memory_from_graphpalace import GraphPalaceMemoryQuery
query = GraphPalaceMemoryQuery(project_dir / "data/graph_palace")

results = query.search_by_keyword("test migration")
print(f"\nFound {len(results)} matching nodes in GraphPalace")

# Clean up
test_file.unlink()
print("\n✓ Test complete (file removed)")

