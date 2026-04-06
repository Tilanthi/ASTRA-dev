"""
ASTRA Live — Checkpoint System
Periodically saves hypothesis state and can restore on restart.
"""
import json
import time
import sqlite3
import threading
from pathlib import Path
from dataclasses import asdict
from typing import Optional

from .hypotheses import HypothesisStore, Hypothesis, Phase


class CheckpointManager:
    """
    Manages periodic checkpointing of hypothesis state.
    Saves to SQLite for persistence across restarts.
    """

    def __init__(self, db_path: str = None, auto_checkpoint_interval: int = 300):
        """
        Args:
            db_path: Path to SQLite database (defaults to data/astra_discoveries.db)
            auto_checkpoint_interval: Seconds between automatic checkpoints (default: 5 min)
        """
        if db_path is None:
            from pathlib import Path
            base_dir = Path(__file__).parent.parent
            db_path = base_dir / "data" / "astra_discoveries.db"

        self.db_path = str(db_path)
        self.auto_interval = auto_checkpoint_interval
        self._lock = threading.Lock()
        self._last_checkpoint_time = 0.0
        self._checkpoint_count = 0
        self._auto_enabled = True

        self._init_db()

    def _init_db(self):
        """Create checkpoint table if it doesn't exist."""
        import os
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                cycle_count INTEGER,
                hypotheses_json TEXT NOT NULL,
                metadata TEXT,
                is_auto INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()

    def save_checkpoint(self, store: HypothesisStore, cycle_count: int = 0,
                       metadata: dict = None, is_auto: bool = False) -> dict:
        """
        Save current hypothesis state as a checkpoint.

        Args:
            store: The HypothesisStore to checkpoint
            cycle_count: Current engine cycle count
            metadata: Optional metadata (engine state, etc.)
            is_auto: True if this is an automatic checkpoint

        Returns:
            dict with checkpoint info
        """
        with self._lock:
            # Serialize all hypotheses
            hypotheses_data = []
            for h in store.all():
                h_dict = h.to_dict()
                # Convert Phase enum to string
                h_dict['phase'] = h.phase.value if isinstance(h.phase, Phase) else h.phase
                hypotheses_data.append(h_dict)

            checkpoint_json = json.dumps({
                'hypotheses': hypotheses_data,
                'next_id': store._next_id,
                'id_prefix_map': store._id_prefix_map,
                'timestamp': time.time()
            }, indent=2)

            metadata_json = json.dumps(metadata or {})

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO checkpoints (timestamp, cycle_count, hypotheses_json, metadata, is_auto)
                VALUES (?, ?, ?, ?, ?)
            """, (time.time(), cycle_count, checkpoint_json, metadata_json, 1 if is_auto else 0))
            checkpoint_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self._last_checkpoint_time = time.time()
            self._checkpoint_count += 1

            return {
                'checkpoint_id': checkpoint_id,
                'timestamp': time.time(),
                'cycle_count': cycle_count,
                'is_auto': is_auto,
                'hypotheses_saved': len(hypotheses_data)
            }

    def load_latest_checkpoint(self, store: HypothesisStore) -> Optional[dict]:
        """
        Load the most recent checkpoint into the hypothesis store.

        Args:
            store: The HypothesisStore to restore

        Returns:
            dict with checkpoint info, or None if no checkpoint found
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, cycle_count, hypotheses_json, metadata, is_auto
                FROM checkpoints
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            conn.close()

            if row is None:
                return None

            checkpoint_id, timestamp, cycle_count, hypotheses_json, metadata_json, is_auto = row

            # Parse and restore hypotheses
            data = json.loads(hypotheses_json)

            # Clear existing hypotheses
            store.hypotheses.clear()
            store._next_id = data.get('next_id', 1)
            store._id_prefix_map = data.get('id_prefix_map', {"H": 1, "CD": 1})

            # Restore each hypothesis
            for h_dict in data['hypotheses']:
                # Convert phase string back to Phase enum
                if isinstance(h_dict.get('phase'), str):
                    try:
                        h_dict['phase'] = Phase(h_dict['phase'])
                    except ValueError:
                        h_dict['phase'] = Phase.PROPOSED

                # Convert timestamps back to float
                for key in ['created_at', 'updated_at', 'last_tested_at', 'archived_at', 'pending_approval_at']:
                    if h_dict.get(key) is not None:
                        h_dict[key] = float(h_dict[key])

                # Restore test results
                test_results = h_dict.pop('test_results', [])
                cross_domain_links = h_dict.pop('cross_domain_links', [])

                h = Hypothesis(**h_dict)
                h.test_results = test_results
                h.cross_domain_links = cross_domain_links
                store.hypotheses[h.id] = h

            return {
                'checkpoint_id': checkpoint_id,
                'timestamp': timestamp,
                'cycle_count': cycle_count,
                'is_auto': is_auto,
                'hypotheses_restored': len(data['hypotheses']),
                'metadata': json.loads(metadata_json) if metadata_json else {}
            }

    def get_checkpoint_history(self, limit: int = 20) -> list:
        """Get recent checkpoint history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, cycle_count, is_auto,
                   json_array_length(hypotheses_json) as count
            FROM checkpoints
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'id': r[0],
                'timestamp': r[1],
                'cycle_count': r[2],
                'is_auto': bool(r[3]),
                'hypotheses_count': r[4]
            }
            for r in rows
        ]

    def prune_old_checkpoints(self, keep_count: int = 10):
        """Remove old checkpoints, keeping only the most recent ones."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM checkpoints
            WHERE id NOT IN (
                SELECT id FROM checkpoints
                ORDER BY timestamp DESC
                LIMIT ?
            )
        """, (keep_count,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def get_status(self) -> dict:
        """Get checkpoint system status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM checkpoints")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT MAX(timestamp) FROM checkpoints")
        latest_ts = cursor.fetchone()[0]
        conn.close()

        return {
            'total_checkpoints': total,
            'last_checkpoint_time': latest_ts or 0.0,
            'checkpoint_count': self._checkpoint_count,
            'auto_enabled': self._auto_enabled,
            'auto_interval': self.auto_interval
        }
