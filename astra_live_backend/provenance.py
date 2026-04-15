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
ASTRA Live — Provenance Tracking (Phase 11.1)
Full reproducibility chain for every discovery.
"""

import uuid
import sqlite3
import json
import time
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional, List


DB_PATH = "astra_discoveries.db"


@dataclass
class ProvenanceRecord:
    """Immutable record of how a discovery was produced."""
    discovery_id: str
    data_source: str
    data_query: str
    test_method: str
    test_inputs: dict
    code_version: str
    random_seed: Optional[int] = None
    parent_hypothesis_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    environment: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class ProvenanceTracker:
    """Stores and queries provenance records in SQLite."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create provenance table if it doesn't exist."""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS provenance (
                id TEXT PRIMARY KEY,
                discovery_id TEXT NOT NULL,
                data_source TEXT NOT NULL,
                data_query TEXT NOT NULL,
                test_method TEXT NOT NULL,
                test_inputs TEXT NOT NULL,
                code_version TEXT NOT NULL,
                random_seed INTEGER,
                parent_hypothesis_id TEXT,
                timestamp REAL NOT NULL,
                environment TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_provenance_discovery "
            "ON provenance(discovery_id)"
        )
        conn.commit()
        conn.close()

    # ── Environment & version helpers ──────────────────────────

    @staticmethod
    def _get_environment() -> dict:
        """Capture current Python + key library versions."""
        env = {"python": sys.version.split()[0]}
        for lib in ("numpy", "scipy", "sklearn"):
            try:
                mod = __import__(lib)
                env[lib] = getattr(mod, "__version__", "unknown")
            except ImportError:
                env[lib] = "not installed"
        return env

    @staticmethod
    def _get_code_version() -> str:
        """Get current git commit hash, or 'unknown'."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5,
                cwd="/shared/ASTRA",
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"

    # ── Recording ──────────────────────────────────────────────

    def record(
        self,
        discovery_id: str,
        data_source: str,
        data_query: str,
        test_method: str,
        test_inputs: dict,
        code_version: str = None,
        random_seed: int = None,
        parent_hypothesis_id: str = None,
    ) -> ProvenanceRecord:
        """Create and persist a new provenance record."""
        if code_version is None:
            code_version = self._get_code_version()

        rec = ProvenanceRecord(
            discovery_id=discovery_id,
            data_source=data_source,
            data_query=data_query,
            test_method=test_method,
            test_inputs=test_inputs if test_inputs else {},
            code_version=code_version,
            random_seed=random_seed,
            parent_hypothesis_id=parent_hypothesis_id,
            environment=self._get_environment(),
        )

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO provenance "
            "(id, discovery_id, data_source, data_query, test_method, "
            "test_inputs, code_version, random_seed, parent_hypothesis_id, "
            "timestamp, environment) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                rec.id, rec.discovery_id, rec.data_source, rec.data_query,
                rec.test_method, json.dumps(rec.test_inputs), rec.code_version,
                rec.random_seed, rec.parent_hypothesis_id, rec.timestamp,
                json.dumps(rec.environment),
            ),
        )
        conn.commit()
        conn.close()
        return rec

    # ── Querying ───────────────────────────────────────────────

    def _row_to_record(self, row) -> ProvenanceRecord:
        """Convert a SQLite row tuple to a ProvenanceRecord."""
        return ProvenanceRecord(
            id=row[0],
            discovery_id=row[1],
            data_source=row[2],
            data_query=row[3],
            test_method=row[4],
            test_inputs=json.loads(row[5]),
            code_version=row[6],
            random_seed=row[7],
            parent_hypothesis_id=row[8],
            timestamp=row[9],
            environment=json.loads(row[10]),
        )

    def get_by_discovery(self, discovery_id: str) -> List[ProvenanceRecord]:
        """Get all provenance records for a specific discovery."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT * FROM provenance WHERE discovery_id = ? ORDER BY timestamp",
            (discovery_id,),
        ).fetchall()
        conn.close()
        return [self._row_to_record(r) for r in rows]

    def get_lineage(self, discovery_id: str) -> List[ProvenanceRecord]:
        """Reconstruct full lineage chain by following parent_hypothesis_id links."""
        visited: set = set()
        result: List[ProvenanceRecord] = []
        queue = [discovery_id]

        conn = sqlite3.connect(self.db_path)
        while queue:
            did = queue.pop(0)
            if did in visited:
                continue
            visited.add(did)
            rows = conn.execute(
                "SELECT * FROM provenance WHERE discovery_id = ? ORDER BY timestamp",
                (did,),
            ).fetchall()
            for row in rows:
                rec = self._row_to_record(row)
                result.append(rec)
                if rec.parent_hypothesis_id and rec.parent_hypothesis_id not in visited:
                    queue.append(rec.parent_hypothesis_id)
        conn.close()

        result.sort(key=lambda r: r.timestamp)
        return result

    def get_all(self) -> List[dict]:
        """Get all provenance records as dicts (for API responses)."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT * FROM provenance ORDER BY timestamp DESC"
        ).fetchall()
        conn.close()
        return [asdict(self._row_to_record(r)) for r in rows]

    def count(self) -> int:
        """Return total number of provenance records."""
        conn = sqlite3.connect(self.db_path)
        n = conn.execute("SELECT COUNT(*) FROM provenance").fetchone()[0]
        conn.close()
        return n
