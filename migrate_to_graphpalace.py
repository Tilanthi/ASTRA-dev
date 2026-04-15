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
Migrate existing ASTRA discoveries from SQLite to GraphPalace.

This script reads all discoveries from the SQLite database and imports them
into GraphPalace, creating wings for each domain and rooms for each finding type.

Usage:
    python3 migrate_to_graphpalace.py [--db-path PATH] [--backup]
"""

import os
import sys
import sqlite3
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def migrate_sqlite_to_graphpalace(
    sqlite_path: str = "astra_discoveries.db",
    backup: bool = True
) -> Dict[str, Any]:
    """
    Migrate discoveries from SQLite to GraphPalace.

    Args:
        sqlite_path: Path to SQLite database
        backup: Create backup before migration

    Returns:
        Migration statistics
    """
    print("="*70)
    print("ASTRA Discovery Migration: SQLite → GraphPalace")
    print("="*70)

    # Backup SQLite database
    if backup:
        backup_path = f"{sqlite_path}.backup_{int(time.time())}"
        print(f"\n[Backup] Creating backup: {backup_path}")
        import shutil
        try:
            shutil.copy2(sqlite_path, backup_path)
            print(f"  ✓ Backup created: {backup_path}")
        except Exception as e:
            print(f"  ✗ Backup failed: {e}")
            return {"error": "Backup failed", "details": str(e)}

    # Import GraphPalace
    try:
        from astra_live_backend.graphpalace_memory import (
            GraphPalaceMemory,
            GRAPHPALACE_AVAILABLE
        )
    except ImportError as e:
        return {"error": "GraphPalace not available", "details": str(e)}

    if not GRAPHPALACE_AVAILABLE:
        return {"error": "GraphPalace not installed"}

    # Initialize GraphPalace
    print(f"\n[Init] Creating GraphPalace memory...")
    try:
        memory = GraphPalaceMemory(sqlite_path)
        print(f"  ✓ GraphPalace initialized")
    except Exception as e:
        return {"error": "GraphPalace init failed", "details": str(e)}

    # Read discoveries from SQLite
    print(f"\n[Read] Loading discoveries from SQLite...")
    discoveries = []
    method_outcomes = []

    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()

        # Check if discoveries table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='discoveries'"
        )
        if not cursor.fetchone():
            print("  ⚠ No discoveries table found (fresh database)")
            conn.close()
            return {"migrated": 0, "discoveries": 0, "method_outcomes": 0}

        # Read discoveries
        cursor.execute("SELECT * FROM discoveries")
        columns = [desc[0] for desc in cursor.description]

        for row in cursor.fetchall():
            discovery = dict(zip(columns, row))

            # Parse JSON fields
            if 'variables' in discovery and discovery['variables']:
                try:
                    discovery['variables'] = json.loads(discovery['variables'])
                except:
                    discovery['variables'] = []

            discoveries.append(discovery)

        print(f"  ✓ Found {len(discoveries)} discoveries")

        # Read method outcomes
        cursor.execute("SELECT * FROM method_outcomes")
        columns = [desc[0] for desc in cursor.description]

        for row in cursor.fetchall():
            outcome = dict(zip(columns, row))
            method_outcomes.append(outcome)

        print(f"  ✓ Found {len(method_outcomes)} method outcomes")

        conn.close()

    except Exception as e:
        print(f"  ✗ Failed to read SQLite: {e}")
        return {"error": "SQLite read failed", "details": str(e)}

    # Migrate to GraphPalace
    print(f"\n[Migrate] Importing discoveries into GraphPalace...")

    migrated_count = 0
    skipped_count = 0
    domain_counts: Dict[str, int] = {}
    finding_type_counts: Dict[str, int] = {}

    for discovery in discoveries:
        try:
            # Check if already in memory
            already_exists = any(
                d.id == discovery['id'] for d in memory.discoveries
            )

            if already_exists:
                skipped_count += 1
                continue

            # Record discovery in GraphPalace
            rec = memory.record_discovery(
                hypothesis_id=discovery.get('hypothesis_id', ''),
                domain=discovery.get('domain', 'general'),
                finding_type=discovery.get('finding_type', 'unknown'),
                variables=discovery.get('variables', []),
                statistic=discovery.get('statistic', 0.0),
                p_value=discovery.get('p_value', 1.0),
                description=discovery.get('description', ''),
                data_source=discovery.get('data_source', ''),
                sample_size=0,  # Not stored in original schema
                effect_size=discovery.get('effect_size'),
                metadata=json.loads(discovery['metadata']) if discovery.get('metadata') else None
            )

            if rec:
                migrated_count += 1

                # Track statistics
                domain = discovery.get('domain', 'general')
                finding_type = discovery.get('finding_type', 'unknown')
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
                finding_type_counts[finding_type] = finding_type_counts.get(finding_type, 0) + 1

                if migrated_count % 10 == 0:
                    print(f"  Progress: {migrated_count}/{len(discoveries)}")

        except Exception as e:
            print(f"  ✗ Failed to migrate discovery {discovery.get('id')}: {e}")

    print(f"  ✓ Migrated {migrated_count} discoveries")
    print(f"  ℹ Skipped {skipped_count} (already in memory)")

    # Migrate method outcomes
    print(f"\n[Migrate] Importing method outcomes...")
    outcomes_migrated = 0

    for outcome in method_outcomes:
        try:
            memory.record_method_outcome(
                method_name=outcome['method_name'],
                hypothesis_id=outcome['hypothesis_id'],
                domain=outcome['domain'],
                cycle=outcome['cycle'],
                data_points=outcome['data_points'],
                tests_run=outcome['tests_run'],
                significant_results=outcome['significant_results'],
                novelty_signals=outcome['novelty_signals'],
                confidence_delta=outcome['confidence_delta'],
                success=bool(outcome['success'])
            )
            outcomes_migrated += 1
        except Exception as e:
            print(f"  ✗ Failed to migrate outcome: {e}")

    print(f"  ✓ Migrated {outcomes_migrated} method outcomes")

    # Build auto-tunnels
    if memory.palace:
        print(f"\n[Tunnels] Building auto-tunnels between domains...")
        try:
            memory.palace.build_tunnels()
            print(f"  ✓ Auto-tunnels built")
        except Exception as e:
            print(f"  ⚠ Auto-tunnel build failed: {e}")

    # Get final statistics
    print(f"\n[Stats] Migration complete!")
    print(f"\n  Discoveries by domain:")
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    • {domain}: {count}")

    print(f"\n  Discoveries by type:")
    for ftype, count in sorted(finding_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    • {ftype}: {count}")

    # Palace status
    print(f"\n  GraphPalace status:")
    status = memory.get_palace_status()
    print(f"    Wings: {status.get('total_wings', 0)}")
    print(f"    Rooms: {status.get('total_rooms', 0)}")
    print(f"    Drawers: {status.get('total_drawers', 0)}")
    print(f"    Entities: {status.get('entity_count', 0)}")
    print(f"    Relationships: {status.get('relationship_count', 0)}")

    # Find cross-domain connections
    print(f"\n[Connections] Discovering cross-domain links...")
    domains = list(domain_counts.keys())

    if len(domains) >= 2:
        for i, domain1 in enumerate(domains[:3]):  # Check first 3 domains
            for domain2 in domains[i+1:4]:  # Against next 3 domains
                try:
                    connections = memory.find_cross_domain_connections(domain1, domain2)
                    if connections:
                        print(f"  • {domain1} ↔ {domain2}: {len(connections)} connections")
                except Exception as e:
                    pass

    # Save and close
    memory.close()

    print(f"\n" + "="*70)
    print("✓ Migration complete!")
    print("="*70)

    return {
        "migrated": migrated_count,
        "skipped": skipped_count,
        "discoveries": len(discoveries),
        "method_outcomes": outcomes_migrated,
        "domains": domain_counts,
        "finding_types": finding_type_counts
    }


def main():
    """Main migration entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate ASTRA discoveries from SQLite to GraphPalace"
    )
    parser.add_argument(
        "--db-path",
        default="astra_discoveries.db",
        help="Path to SQLite database (default: astra_discoveries.db)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup before migration"
    )

    args = parser.parse_args()

    # Check if database exists
    if not os.path.exists(args.db_path):
        print(f"Database not found: {args.db_path}")
        print("Creating fresh GraphPalace instance...")
        from astra_live_backend.graphpalace_memory import GraphPalaceMemory
        memory = GraphPalaceMemory(args.db_path)
        memory.close()
        print("✓ Fresh GraphPalace instance created")
        return

    # Run migration
    result = migrate_sqlite_to_graphpalace(
        sqlite_path=args.db_path,
        backup=not args.no_backup
    )

    if "error" in result:
        print(f"\n✗ Migration failed: {result['error']}")
        if "details" in result:
            print(f"  Details: {result['details']}")
        sys.exit(1)

    print(f"\n✓ Successfully migrated {result.get('migrated', 0)} discoveries")


if __name__ == "__main__":
    main()
