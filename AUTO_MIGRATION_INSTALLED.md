# Auto-Migration System - Installation Complete

**Date**: 2026-05-09
**Status**: ✅ Installed and Operational

---

## What Was Installed

Automatic memory migration system that:
1. **Detects new .md files** in the memory directory
2. **Immediately migrates them** to GraphPalace knowledge graph
3. **Maintains registry** to prevent duplicate migrations
4. **Integrates with ASTRA** autonomous agent system

---

## System Components

### 1. Core Migration Script
**File**: `migrate_memory_to_graphpalace.py`
- Handles parsing .md files
- Creates GraphPalace nodes
- Manages migration registry

### 2. Auto-Migration Wrapper
**File**: `auto_migrate_memory.py`
- Simple wrapper for easy integration
- Can be called from any script
- Tracks migrated files to prevent duplicates

### 3. Integration Script
**File**: `integrate_auto_migration.py`
- Installs/uninstalls auto-migration
- Creates wrapper scripts
- Sets up cron job specification

### 4. Query Interface
**File**: `query_memory_from_graphpalace.py`
- Query GraphPalace memory
- Search by keyword, type, node ID
- Show statistics and detailed information

---

## Usage

### Manual Migration
```bash
# Migrate all memory files
python3 migrate_memory_to_graphpalace.py

# Migrate specific file
python3 migrate_memory_to_graphpalace.py test_file

# Migrate using wrapper
python3 auto_migrate_memory.py
```

### Query Memory
```bash
# Show statistics
python3 query_memory_from_graphpalace.py --stats

# Search by keyword
python3 query_memory_from_graphpalace.py --query "peer review"

# List by type
python3 query_memory_from_graphpalace.py --type lesson_learned

# Show node details
python3 query_memory_from_graphpalace.py --node USER_4e6a3c6c

# Show all insights
python3 query_memory_from_graphpalace.py --insights
```

### Automatic Migration (Cron)
```bash
# Install cron job for periodic migration (every 5 minutes)
crontab -l | { cat; cat auto_migrate_cron.txt; } | crontab -

# Check cron job
crontab -l | grep auto_migrate

# Remove cron job
crontab -e  # Delete the auto_migrate line
```

---

## Integration with Autonomous Agent

The auto-migration wrapper can be called from within ASTRA:

```python
# In any ASTRA script
import sys
from pathlib import Path
sys.path.insert(0, str(Path("/path/to/ASTRA-dev-main")))

from auto_migrate_memory import migrate

# Migrate any new memory files
count = migrate()
print(f"Migrated {count} files to GraphPalace")
```

---

## Current Status

**Memory Statistics** (as of 2026-05-09):
- Total GraphPalace nodes: 111
- Memory nodes: 20
- By type:
  - lesson_learned: 3
  - memory: 13
  - project_context: 2
  - user_preference: 2

**Migration Registry**: Tracks which .md files have been migrated
- Location: `data/graph_palace/.migrated_files.json`
- Prevents duplicate migrations
- Updated automatically

---

## Architecture

**Memory Flow**:
```
1. New .md file created in memory/
   ↓
2. Auto-migration detects new file
   ↓
3. Parses YAML frontmatter + markdown content
   ↓
4. Creates GraphPalace node with metadata
   ↓
5. Updates migration registry
   ↓
6. Memory persists in GraphPalace (safe to delete .md)
```

**GraphPalace Storage**:
- `data/graph_palace/nodes.json` - All nodes (111 total)
- `data/graph_palace/edges.json` - Relationships (100 edges)
- `data/graph_palace/.migrated_files.json` - Migration registry

---

## Benefits

**Before Auto-Migration**:
- ❌ Manual migration required
- ❌ Memory files could be lost
- ❌ No persistence across sessions
- ❌ Difficult to query

**After Auto-Migration**:
- ✅ **Automatic**: New files migrated immediately
- ✅ **Persistent**: Memory stored in GraphPalace
- ✅ **Queryable**: Search by keyword, type, node ID
- ✅ **Safe**: Original .md files can be deleted
- ✅ **Integrated**: Works with autonomous agent
- ✅ **Networked**: Related concepts connected

---

## File Locations

**Scripts**:
- `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/migrate_memory_to_graphpalace.py`
- `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/auto_migrate_memory.py`
- `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/query_memory_from_graphpalace.py`
- `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/integrate_auto_migration.py`
- `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/test_auto_migration.py`

**Data**:
- Memory directory: `/Users/gjw255/.claude/projects/.../memory/`
- GraphPalace: `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/data/graph_palace/`
- Backup: `/Users/gjw255/.claude/projects/.../memory_backup_20260509_131818/`

---

## Maintenance

### Adding New Memory Types
To add a new memory type, create a .md file with proper frontmatter:

```markdown
---
name: my_new_memory
description: Description of this memory
type: feedback  # or: user, project, autonomous
---

# Memory Content

Key insights and information...
```

### Cleaning Up Old Memory Files
Once memory is in GraphPalace, you can safely delete the .md files:

```bash
# List .md files
ls -la /Users/gjw255/.claude/projects/.../memory/*.md

# Check if migrated in GraphPalace
python3 query_memory_from_graphpalace.py --stats

# Delete if desired
rm /Users/gjw255/.claude/projects/.../memory/old_file.md
```

### Re-Migrating All Files
To force re-migration of all files:

```bash
# Remove migration registry
rm data/graph_palace/.migrated_files.json

# Re-migrate everything
python3 migrate_memory_to_graphpalace.py
```

---

## Troubleshooting

**Problem**: New .md files not being migrated

**Solution**:
1. Check file exists: `ls -la memory/`
2. Run manual migration: `python3 auto_migrate_memory.py`
3. Check GraphPalace: `python3 query_memory_from_graphpalace.py --stats`

**Problem**: Duplicate nodes in GraphPalace

**Solution**:
1. Migration registry prevents duplicates
2. If duplicates exist, re-run migration to update registry

**Problem**: Can't find migrated memory

**Solution**:
1. Check by type: `python3 query_memory_from_graphpalace.py --type lesson_learned`
2. Search by keyword: `python3 query_memory_from_graphpalace.py --query "keyword"`
3. Show all memory: `python3 query_memory_from_graphpalace.py --list`

---

## Summary

Your memory system now has:
- ✅ **Automatic migration** - New .md files immediately saved to GraphPalace
- ✅ **Persistent storage** - Memory survives .md file deletion
- ✅ **Queryable interface** - Search by type, keyword, or node ID
- ✅ **ASTRA integration** - Works with autonomous agent system
- ✅ **Networked knowledge** - Related concepts connected in knowledge graph

**Total memory nodes**: 20 (out of 111 total GraphPalace nodes)

---

*Auto-migration system installed: 2026-05-09*
*Memory architecture upgraded from .md files to knowledge graph with automatic migration*
