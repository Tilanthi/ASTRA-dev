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
Clean duplicate discoveries from the database.

This script:
1. Identifies duplicate discoveries (same finding_type + data_source + variables)
2. Keeps only the most recent occurrence of each unique discovery
3. Updates the database and in-memory state
"""

import sqlite3
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Use the actual database location
DB_PATH = "astra_discoveries.db"


def identify_duplicates(conn: sqlite3.Connection) -> Dict[str, List[Tuple]]:
    """
    Identify duplicate discoveries in the database.

    Returns a dict mapping dedup_key to list of (rowid, timestamp, id) tuples.
    """
    # Fetch all discoveries
    cursor = conn.execute("""
        SELECT rowid, id, timestamp, finding_type, data_source, variables
        FROM discoveries
        ORDER BY timestamp ASC
    """).fetchall()

    # Group by dedup key
    groups = defaultdict(list)
    for rowid, disc_id, timestamp, finding_type, data_source, variables in cursor:
        try:
            var_list = json.loads(variables) if variables else []
            var_key = tuple(sorted(var_list))
        except:
            var_key = ()

        dedup_key = (finding_type, data_source, var_key)
        groups[dedup_key].append((rowid, timestamp, disc_id))

    return dict(groups)


def clean_duplicates(conn: sqlite3.Connection, dry_run: bool = False) -> Tuple[int, int]:
    """
    Remove duplicate discoveries, keeping only the most recent of each group.

    Args:
        conn: SQLite connection
        dry_run: If True, only report what would be deleted

    Returns:
        Tuple of (duplicates_removed, unique_remaining)
    """
    groups = identify_duplicates(conn)

    duplicates_to_delete = []
    unique_count = 0

    for dedup_key, records in groups.items():
        if len(records) > 1:
            # Sort by timestamp (ascending), keep only the most recent
            records.sort(key=lambda x: x[1])
            # Keep the last (most recent), mark others for deletion
            for rowid, _, disc_id in records[:-1]:
                duplicates_to_delete.append(rowid)
            unique_count += 1
        else:
            unique_count += 1

    if not dry_run and duplicates_to_delete:
        # Delete duplicates
        placeholders = ",".join("?" * len(duplicates_to_delete))
        conn.execute(f"DELETE FROM discoveries WHERE rowid IN ({placeholders})", duplicates_to_delete)
        conn.commit()

        # Vacuum to reclaim space (must be done outside transaction)
        conn.execute("VACUUM")
        conn.commit()

    return len(duplicates_to_delete), unique_count


def update_unique_discovery_count(conn: sqlite3.Connection) -> int:
    """
    Get the true unique discovery count.

    Uses the same deduplication logic as record_discovery().
    """
    cursor = conn.execute("""
        SELECT finding_type, data_source, variables
        FROM discoveries
    """)

    seen_keys = set()
    for finding_type, data_source, variables in cursor:
        try:
            var_list = json.loads(variables) if variables else []
            var_key = tuple(sorted(var_list))
        except:
            var_key = ()

        dedup_key = (finding_type, data_source, var_key)
        seen_keys.add(dedup_key)

    return len(seen_keys)


def get_discovery_summary(conn: sqlite3.Connection) -> Dict:
    """Get summary statistics for display."""
    total = conn.execute("SELECT COUNT(*) as count FROM discoveries").fetchone()["count"]
    unique = update_unique_discovery_count(conn)

    # Count by finding type
    by_type = conn.execute("""
        SELECT finding_type, COUNT(*) as count
        FROM discoveries
        GROUP BY finding_type
    """).fetchall()

    # Count by data source
    by_source = conn.execute("""
        SELECT data_source, COUNT(*) as count
        FROM discoveries
        GROUP BY data_source
    """).fetchall()

    return {
        "total_records": total,
        "unique_discoveries": unique,
        "duplicates": total - unique,
        "by_type": dict(by_type),
        "by_source": dict(by_source)
    }


def main():
    print("=" * 70)
    print("DISCOVERY DATABASE CLEANUP")
    print("=" * 70)

    # Change to correct directory
    import os
    os.chdir('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main')

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
    except Exception as e:
        print(f"Error opening database: {e}")
        print(f"DB path: {DB_PATH}")
        return

    # Current state
    print(f"\nDatabase: {DB_PATH}")

    # Get summary before cleanup
    summary_before = get_discovery_summary(conn)
    print(f"\nBefore cleanup:")
    print(f"  Total records: {summary_before['total_records']}")
    print(f"  Unique discoveries: {summary_before['unique_discoveries']}")
    print(f"  Duplicates: {summary_before['duplicates']}")

    if summary_before['by_type']:
        print(f"\n  By type:")
        for finding_type, count in summary_before['by_type'].items():
            print(f"    {finding_type}: {count}")

    # Show duplicate groups
    groups = identify_duplicates(conn)
    dup_groups = [(k, v) for k, v in groups.items() if len(v) > 1]
    dup_groups.sort(key=lambda x: len(x[1]), reverse=True)

    print(f"\nDuplicate groups: {len(dup_groups)}")

    if dup_groups:
        print("\nTop duplicate groups:")
        for i, (dedup_key, records) in enumerate(dup_groups[:5]):
            finding_type, data_source, var_key = dedup_key
            print(f"  {i+1}. {finding_type} from {data_source}: {len(records)} occurrences")

    # Dry run
    print("\n" + "=" * 70)
    print("DRY RUN: Identifying duplicates...")
    n_duplicates, n_unique = clean_duplicates(conn, dry_run=True)

    print(f"\nWould delete: {n_duplicates} duplicate records")
    print(f"Would keep: {n_unique} unique records")

    if n_duplicates > 0:
        print("\n" + "=" * 70)
        print("Proceeding with cleanup...")
        n_deleted, n_remaining = clean_duplicates(conn, dry_run=False)
        print(f"Deleted: {n_deleted} records")
        print(f"Remaining: {n_remaining} records")

        # Verify final state
        summary_after = get_discovery_summary(conn)
        print(f"\nFinal state:")
        print(f"  Total records: {summary_after['total_records']}")
        print(f"  Unique discoveries: {summary_after['unique_discoveries']}")

        if summary_after['by_type']:
            print(f"\n  By type:")
            for finding_type, count in summary_after['by_type'].items():
                print(f"    {finding_type}: {count}")

    conn.close()

    print("\n" + "=" * 70)
    print("CLEANUP COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
