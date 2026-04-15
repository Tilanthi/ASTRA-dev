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
ASTRA Live — Discovery Memory
Persistent learning memory that tracks what works, what's been found,
and guides future discovery directions. This is the core of self-improvement.

Every cycle the engine writes outcome signals here. On future cycles,
the memory feeds back into hypothesis generation, method selection, and
exploration strategy.
"""
import time
import json
import math
import sqlite3
import os
import queue
import numpy as np
import threading
import logging
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque, Counter
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryRecord:
    """A single scientific finding — used to seed new hypotheses."""
    id: str
    timestamp: float
    cycle: int
    hypothesis_id: str
    domain: str
    finding_type: str  # "scaling", "correlation", "bimodality", "anomaly", "causal", "intervention"
    variables: list  # e.g., ["log_period", "log_sma"]
    statistic: float
    p_value: float
    description: str
    data_source: str  # "exoplanets", "sdss", "gaia", "pantheon"
    strength: float  # 0-1, composite of significance, effect size, sample size
    follow_ups_generated: int = 0  # track how many hypotheses this spawned
    verified: bool = False  # did follow-up confirm?
    effect_size: Optional[float] = None  # Cohen's d, η², or domain-appropriate effect size
    metadata: Optional[dict] = None  # Additional structured data (e.g. confounder analysis)


@dataclass
class MethodOutcome:
    """Tracks the effectiveness of an investigation method."""
    method_name: str  # "_investigate_hubble", "run_causal_discovery", etc.
    hypothesis_id: str
    domain: str
    timestamp: float
    cycle: int
    data_points: int
    tests_run: int
    significant_results: int
    novelty_signals: int
    confidence_delta: float  # change in hypothesis confidence after evaluation
    success: bool  # did it produce actionable results?


@dataclass
class ExplorationState:
    """Tracks which data sources and variable combinations have been explored."""
    data_source: str
    variable_pairs_tested: dict  # "var1_var2" -> count
    last_explored: float
    total_explorations: int
    novelty_rate: float  # fraction of explorations that yielded novelty


class DiscoveryMemory:
    """
    Long-lived memory that enables self-improvement.

    Three feedback loops:
    1. Discovery → Hypothesis: Strong findings generate new hypotheses
    2. Method → Strategy: Track which investigation methods produce results
    3. Exploration → Coverage: Track what's been tried, prioritize unexplored
    """

    def __init__(self, max_records: int = 500,
                 db_path: str = "astra_discoveries.db"):
        self.discoveries: deque[DiscoveryRecord] = deque(maxlen=max_records)
        self.method_outcomes: deque[MethodOutcome] = deque(maxlen=500)
        self.exploration: dict[str, ExplorationState] = {}
        self.generation_count = 0  # hypotheses generated from memory
        self._next_discovery_id = 1

        # Derived knowledge: which variable pairs tend to yield results
        self._variable_affinity: dict[str, float] = defaultdict(float)
        # Domain momentum: which domains are currently "hot"
        self._domain_momentum: dict[str, float] = defaultdict(float)

        # ── Thread Safety ─────────────────────────────────────────
        self._affinity_lock = threading.Lock()  # Protect variable_affinity updates
        self._momentum_lock = threading.Lock()   # Protect domain_momentum updates
        self._memory_lock = threading.RLock()     # Protect in-memory deques

        # ── SQLite Connection Pool ─────────────────────────────────────
        self.db_path = db_path
        self._connection_pool = queue.Queue(maxsize=10)
        self._init_db()
        self._init_connection_pool(5)  # Start with 5 connections
        self._load_from_db(max_records)

    # ── Database init & load ─────────────────────────────────────

    def _init_db(self):
        """Create DB and tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS discoveries (
                id TEXT PRIMARY KEY,
                timestamp REAL,
                cycle INTEGER,
                hypothesis_id TEXT,
                domain TEXT,
                finding_type TEXT,
                variables TEXT,
                statistic REAL,
                p_value REAL,
                description TEXT,
                data_source TEXT,
                strength REAL,
                follow_ups_generated INTEGER DEFAULT 0,
                verified INTEGER DEFAULT 0,
                effect_size REAL
            );
            CREATE TABLE IF NOT EXISTS method_outcomes (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                method_name TEXT,
                hypothesis_id TEXT,
                domain TEXT,
                timestamp REAL,
                cycle INTEGER,
                data_points INTEGER,
                tests_run INTEGER,
                significant_results INTEGER,
                novelty_signals INTEGER,
                confidence_delta REAL,
                success INTEGER
            );
            CREATE TABLE IF NOT EXISTS generated_hypotheses (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                source_discovery_id TEXT,
                hypothesis_text TEXT,
                domain TEXT
            );
            -- Table for cross-session variable affinity persistence
            CREATE TABLE IF NOT EXISTS variable_affinity (
                variable_name TEXT PRIMARY KEY,
                affinity_score REAL DEFAULT 0.0,
                last_updated REAL DEFAULT 0.0,
                discovery_count INTEGER DEFAULT 0
            );
            -- Table for cross-session domain momentum persistence
            CREATE TABLE IF NOT EXISTS domain_momentum (
                domain_name TEXT PRIMARY KEY,
                momentum_score REAL DEFAULT 0.0,
                last_updated REAL DEFAULT 0.0,
                discovery_count INTEGER DEFAULT 0
            );
        """)
        conn.commit()
        conn.close()

    def _load_from_db(self, max_records: int):
        """Load existing records from DB into in-memory deques."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Load discoveries (most recent up to max_records)
        rows = conn.execute(
            "SELECT * FROM discoveries ORDER BY timestamp ASC LIMIT ?",
            (max_records,)
        ).fetchall()
        for row in rows:
            variables = json.loads(row["variables"]) if row["variables"] else []
            rec = DiscoveryRecord(
                id=row["id"],
                timestamp=row["timestamp"],
                cycle=row["cycle"],
                hypothesis_id=row["hypothesis_id"],
                domain=row["domain"],
                finding_type=row["finding_type"],
                variables=variables,
                statistic=row["statistic"],
                p_value=row["p_value"],
                description=row["description"],
                data_source=row["data_source"],
                strength=row["strength"],
                follow_ups_generated=row["follow_ups_generated"] or 0,
                verified=bool(row["verified"]),
                effect_size=row["effect_size"],
            )
            self.discoveries.append(rec)
            # Rebuild variable affinity from loaded discoveries
            for v in rec.variables:
                self._variable_affinity[v] += rec.strength * 0.3
            self._domain_momentum[rec.domain] += rec.strength * 0.2

        # Set _next_discovery_id based on max existing ID
        max_id_row = conn.execute(
            "SELECT id FROM discoveries ORDER BY CAST(SUBSTR(id, 2) AS INTEGER) DESC LIMIT 1"
        ).fetchone()
        if max_id_row:
            try:
                self._next_discovery_id = int(max_id_row["id"][1:]) + 1
            except (ValueError, IndexError):
                self._next_discovery_id = len(self.discoveries) + 1

        # Load method outcomes (most recent 500)
        rows = conn.execute(
            "SELECT * FROM method_outcomes ORDER BY timestamp ASC LIMIT 500"
        ).fetchall()
        for row in rows:
            self.method_outcomes.append(MethodOutcome(
                method_name=row["method_name"],
                hypothesis_id=row["hypothesis_id"],
                domain=row["domain"],
                timestamp=row["timestamp"],
                cycle=row["cycle"],
                data_points=row["data_points"],
                tests_run=row["tests_run"],
                significant_results=row["significant_results"],
                novelty_signals=row["novelty_signals"],
                confidence_delta=row["confidence_delta"],
                success=bool(row["success"]),
            ))

        # Load generation count
        gen_count = conn.execute(
            "SELECT COUNT(*) FROM generated_hypotheses"
        ).fetchone()[0]
        self.generation_count = gen_count

        # Load variable affinity from database (cross-session persistence)
        for row in conn.execute("SELECT * FROM variable_affinity").fetchall():
            self._variable_affinity[row["variable_name"]] = row["affinity_score"]

        # Load domain momentum from database (cross-session persistence)
        for row in conn.execute("SELECT * FROM domain_momentum").fetchall():
            self._domain_momentum[row["domain_name"]] = row["momentum_score"]

        conn.close()

    def _init_connection_pool(self, pool_size: int = 5):
        """Initialize SQLite connection pool for thread-safe concurrent access."""
        for _ in range(pool_size):
            try:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                self._connection_pool.put(conn)
            except Exception as e:
                logger.warning(f"Failed to create connection pool entry: {e}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool (blocking with timeout)."""
        try:
            conn = self._connection_pool.get(timeout=5.0)
            return conn
        except queue.Empty:
            # Fallback: create new connection if pool is exhausted
            logger.warning("Connection pool exhausted, creating fallback connection")
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            return conn

    def _return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool."""
        try:
            self._connection_pool.put_nowait(conn)
        except queue.Full:
            # Pool is full, just close the connection
            conn.close()

    # ── Recording ────────────────────────────────────────────────────

    def record_discovery(self, hypothesis_id: str, domain: str, finding_type: str,
                         variables: list, statistic: float, p_value: float,
                         description: str, data_source: str,
                         sample_size: int = 0,
                         effect_size: Optional[float] = None,
                         metadata: Optional[dict] = None) -> Optional[DiscoveryRecord]:
        """
        Record a scientific finding for future hypothesis generation.

        Returns None if discovery is a duplicate (same finding_type + data_source + variables
        already recorded within last 10 cycles).
        """
        # ── Deduplication: Check if similar discovery exists ──
        # Create a key from finding characteristics
        var_key = tuple(sorted(variables)) if variables else ()
        dedup_key = (finding_type, data_source, var_key)

        # Check ALL discoveries (not just recent) for duplicates
        # This prevents the same discovery from being recorded multiple times
        for disc in self.discoveries:
            # Compare key characteristics
            disc_var_key = tuple(sorted(disc.variables)) if disc.variables else ()
            if (finding_type == disc.finding_type and
                data_source == disc.data_source and
                var_key == disc_var_key):
                # Duplicate found! Skip recording.
                return None

        # Composite strength: significance × effect size proxy × log sample size
        sig_score = max(0, 1 - p_value) if p_value <= 1 else 0
        effect_score = min(1.0, abs(statistic) / 10.0)
        sample_score = min(1.0, math.log10(max(sample_size, 1)) / 4.0)  # log10(10000)=4
        strength = 0.4 * sig_score + 0.35 * effect_score + 0.25 * sample_score

        rec = DiscoveryRecord(
            id=f"D{self._next_discovery_id:04d}",
            timestamp=time.time(),
            cycle=0,  # set by caller
            hypothesis_id=hypothesis_id,
            domain=domain,
            finding_type=finding_type,
            variables=variables,
            statistic=statistic,
            p_value=p_value,
            description=description,
            data_source=data_source,
            strength=strength,
            effect_size=effect_size,
            metadata=metadata,
        )
        self._next_discovery_id += 1
        self.discoveries.append(rec)

        # Persist to SQLite
        self._persist_discovery(rec)

        # Update variable affinity (with cross-session persistence)
        for v in variables:
            self._variable_affinity[v] += strength * 0.3
            self._persist_variable_affinity(v, self._variable_affinity[v])

        # Update domain momentum (with cross-session persistence)
        self._domain_momentum[domain] += strength * 0.2
        self._persist_domain_momentum(domain, self._domain_momentum[domain])

        # Update exploration state
        key = data_source
        if key not in self.exploration:
            self.exploration[key] = ExplorationState(
                data_source=key, variable_pairs_tested={},
                last_explored=time.time(), total_explorations=0, novelty_rate=0)
        es = self.exploration[key]
        es.total_explorations += 1
        es.last_explored = time.time()
        if strength > 0.5:
            es.novelty_rate = (es.novelty_rate * (es.total_explorations - 1) + 1) / es.total_explorations
        else:
            es.novelty_rate = (es.novelty_rate * (es.total_explorations - 1)) / es.total_explorations

        return rec

    def record_method_outcome(self, method_name: str, hypothesis_id: str, domain: str,
                               cycle: int, data_points: int, tests_run: int,
                               significant_results: int, novelty_signals: int,
                               confidence_delta: float, success: bool):
        """Record how well an investigation method performed."""
        outcome = MethodOutcome(
            method_name=method_name,
            hypothesis_id=hypothesis_id,
            domain=domain,
            timestamp=time.time(),
            cycle=cycle,
            data_points=data_points,
            tests_run=tests_run,
            significant_results=significant_results,
            novelty_signals=novelty_signals,
            confidence_delta=confidence_delta,
            success=success,
        )
        self.method_outcomes.append(outcome)

        # Persist to SQLite
        self._persist_method_outcome(outcome)

    # ── SQLite persistence helpers ─────────────────────────────────

    def _persist_discovery(self, rec: DiscoveryRecord):
        """Thread-safe INSERT a discovery record into SQLite with deduplication using connection pool."""
        conn = None
        try:
            conn = self._get_connection()

            # Check for duplicate in database first (with connection lock)
            var_key = json.dumps(sorted(rec.variables)) if rec.variables else "[]"
            dedup_check = conn.execute(
                """SELECT id FROM discoveries
                   WHERE finding_type = ? AND data_source = ? AND variables = ?
                   LIMIT 1""",
                (rec.finding_type, rec.data_source, var_key)
            ).fetchone()

            if dedup_check:
                # Duplicate found - update existing record instead of inserting new one
                existing_id = dedup_check["id"]
                conn.execute(
                    """UPDATE discoveries
                       SET timestamp = ?, cycle = ?, hypothesis_id = ?, domain = ?,
                           statistic = ?, p_value = ?, description = ?,
                           strength = ?, verified = ?, effect_size = ?
                       WHERE id = ?""",
                    (rec.timestamp, rec.cycle, rec.hypothesis_id, rec.domain,
                     rec.statistic, rec.p_value, rec.description,
                     rec.strength, int(rec.verified), rec.effect_size,
                     existing_id)
                )
                logger.info(f"[DiscoveryMemory] Updated existing discovery {existing_id} instead of creating duplicate")
            else:
                # No duplicate - insert new record
                conn.execute(
                    """INSERT INTO discoveries
                       (id, timestamp, cycle, hypothesis_id, domain, finding_type,
                        variables, statistic, p_value, description, data_source,
                        strength, follow_ups_generated, verified, effect_size)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (rec.id, rec.timestamp, rec.cycle, rec.hypothesis_id,
                     rec.domain, rec.finding_type, var_key,
                     rec.statistic, rec.p_value, rec.description, rec.data_source,
                     rec.strength, rec.follow_ups_generated, int(rec.verified),
                     rec.effect_size),
                )

            conn.commit()
        except Exception as e:
            logger.error(f"[DiscoveryMemory] SQLite persist discovery error: {e}")
        finally:
            if conn:
                self._return_connection(conn)

    def _persist_method_outcome(self, outcome: MethodOutcome):
        """Thread-safe INSERT a method outcome into SQLite using connection pool."""
        conn = None
        try:
            conn = self._get_connection()
            conn.execute(
                """INSERT INTO method_outcomes
                   (method_name, hypothesis_id, domain, timestamp, cycle,
                    data_points, tests_run, significant_results, novelty_signals,
                    confidence_delta, success)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (outcome.method_name, outcome.hypothesis_id, outcome.domain,
                 outcome.timestamp, outcome.cycle, outcome.data_points,
                 outcome.tests_run, outcome.significant_results,
                 outcome.novelty_signals, outcome.confidence_delta,
                 int(outcome.success)),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"[DiscoveryMemory] SQLite persist outcome error: {e}")
        finally:
            if conn:
                self._return_connection(conn)

    def _persist_variable_affinity(self, variable: str, score: float):
        """Thread-safe UPDATE or INSERT variable affinity score using connection pool."""
        conn = None
        try:
            conn = self._get_connection()
            existing = conn.execute(
                "SELECT discovery_count FROM variable_affinity WHERE variable_name = ?",
                (variable,)
            ).fetchone()

            now = time.time()
            if existing:
                # Update existing record
                conn.execute(
                    """UPDATE variable_affinity
                       SET affinity_score = ?, last_updated = ?, discovery_count = discovery_count + 1
                       WHERE variable_name = ?""",
                    (score, now, variable),
                )
            else:
                # Insert new record
                conn.execute(
                    """INSERT INTO variable_affinity (variable_name, affinity_score, last_updated, discovery_count)
                       VALUES (?, ?, ?, 1)""",
                    (variable, score, now),
                )
            conn.commit()
        except Exception as e:
            logger.error(f"[DiscoveryMemory] SQLite persist affinity error: {e}")
        finally:
            if conn:
                self._return_connection(conn)

    def _persist_domain_momentum(self, domain: str, score: float):
        """Thread-safe UPDATE or INSERT domain momentum score using connection pool."""
        conn = None
        try:
            conn = self._get_connection()
            existing = conn.execute(
                "SELECT discovery_count FROM domain_momentum WHERE domain_name = ?",
                (domain,)
            ).fetchone()

            now = time.time()
            if existing:
                # Update existing record
                conn.execute(
                    """UPDATE domain_momentum
                       SET momentum_score = ?, last_updated = ?, discovery_count = discovery_count + 1
                       WHERE domain_name = ?""",
                    (score, now, domain),
                )
            else:
                # Insert new record
                conn.execute(
                    """INSERT INTO domain_momentum (domain_name, momentum_score, last_updated, discovery_count)
                       VALUES (?, ?, ?, 1)""",
                    (domain, score, now),
                )
            conn.commit()
        except Exception as e:
            logger.error(f"[DiscoveryMemory] SQLite persist momentum error: {e}")
        finally:
            if conn:
                self._return_connection(conn)

    def record_generated_hypothesis(self, source_discovery_id: str,
                                     hypothesis_text: str, domain: str):
        """Thread-safe record a hypothesis generated from a discovery using connection pool."""
        self.generation_count += 1
        conn = None
        try:
            conn = self._get_connection()
            conn.execute(
                """INSERT INTO generated_hypotheses
                   (timestamp, source_discovery_id, hypothesis_text, domain)
                   VALUES (?, ?, ?, ?)""",
                (time.time(), source_discovery_id, hypothesis_text, domain),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"[DiscoveryMemory] SQLite persist hypothesis error: {e}")
        finally:
            if conn:
                self._return_connection(conn)

    # ── Phase 10.5: Importance-Weighted Memory Compaction ──────────

    def _compute_importance(self, rec: 'DiscoveryRecord') -> float:
        """Compute importance score for a discovery record.

        importance = strength * (1 + effect_size_norm) * domain_diversity_bonus * recency_weight
        """
        # Base: discovery strength (0-1)
        base = rec.strength

        # Effect size normalization (0-1 range)
        effect_norm = 0.0
        if rec.effect_size is not None:
            effect_norm = min(1.0, abs(rec.effect_size) / 2.0)  # d=2.0 is max
        elif rec.statistic:
            effect_norm = min(1.0, abs(rec.statistic) / 10.0)

        # Domain diversity bonus: discoveries from underrepresented domains score 2x
        domain_counts = Counter(d.domain for d in self.discoveries)
        total = len(self.discoveries) or 1
        domain_frac = domain_counts.get(rec.domain, 0) / total
        domain_diversity_bonus = 2.0 if domain_frac < 0.2 else 1.0

        # Recency weight: more recent = higher weight (exponential decay)
        import math
        now = time.time()
        age_hours = (now - rec.timestamp) / 3600.0
        recency_weight = math.exp(-age_hours / 168.0)  # half-life ~1 week

        importance = base * (1.0 + effect_norm) * domain_diversity_bonus * recency_weight
        return importance

    def _compute_outcome_importance(self, outcome: 'MethodOutcome') -> float:
        """Compute importance score for a method outcome."""
        import math
        # Higher info outcomes: those with significant results or large confidence delta
        info_score = (0.5 if outcome.success else 0.1) + \
                     min(1.0, outcome.significant_results * 0.3) + \
                     min(1.0, abs(outcome.confidence_delta) * 5.0)

        now = time.time()
        age_hours = (now - outcome.timestamp) / 3600.0
        recency = math.exp(-age_hours / 168.0)

        return info_score * recency

    def compact_if_needed(self):
        """Importance-weighted compaction: evict lowest-importance records when at cap.

        Called after each cycle. Instead of FIFO (deque default), we replace the
        least important discovery with nothing, keeping the deque at maxlen.
        """
        max_disc = self.discoveries.maxlen or 500
        max_outcomes = self.method_outcomes.maxlen or 500

        compacted = False

        # Compact discoveries if at cap
        if len(self.discoveries) >= max_disc:
            # Score all discoveries
            scored = [(self._compute_importance(d), i, d)
                      for i, d in enumerate(self.discoveries)]
            scored.sort(key=lambda x: x[0])

            # Evict bottom 10% (by importance)
            n_evict = max(1, len(scored) // 10)
            evict_ids = {scored[i][2].id for i in range(n_evict)}

            # Remove from deque (rebuild without evicted)
            remaining = [d for d in self.discoveries if d.id not in evict_ids]
            self.discoveries.clear()
            for d in remaining:
                self.discoveries.append(d)

            # Remove from SQLite too
            conn = None
            try:
                conn = self._get_connection()
                placeholders = ",".join("?" * len(evict_ids))
                conn.execute(
                    f"DELETE FROM discoveries WHERE id IN ({placeholders})",
                    list(evict_ids)
                )
                conn.commit()
            except Exception as e:
                logger.error(f"[DiscoveryMemory] Compaction DB cleanup error: {e}")
            finally:
                if conn:
                    self._return_connection(conn)

            compacted = True

        # Compact method outcomes if at cap
        if len(self.method_outcomes) >= max_outcomes:
            scored = [(self._compute_outcome_importance(o), i, o)
                      for i, o in enumerate(self.method_outcomes)]
            scored.sort(key=lambda x: x[0])

            n_evict = max(1, len(scored) // 10)
            evict_indices = {scored[i][1] for i in range(n_evict)}

            remaining = [o for i, o in enumerate(self.method_outcomes)
                         if i not in evict_indices]
            self.method_outcomes.clear()
            for o in remaining:
                self.method_outcomes.append(o)

            compacted = True

        return compacted

    def get_persistence_stats(self) -> Dict:
        """Thread-safe return SQLite persistence statistics using connection pool."""
        conn = None
        try:
            conn = self._get_connection()
            disc_count = conn.execute("SELECT COUNT(*) FROM discoveries").fetchone()[0]
            out_count = conn.execute("SELECT COUNT(*) FROM method_outcomes").fetchone()[0]
            hyp_count = conn.execute("SELECT COUNT(*) FROM generated_hypotheses").fetchone()[0]
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        except Exception as e:
            return {"error": str(e), "db_path": self.db_path}
        finally:
            if conn:
                self._return_connection(conn)

        return {
            "db_path": self.db_path,
            "discoveries_persisted": disc_count,
            "outcomes_persisted": out_count,
            "hypotheses_persisted": hyp_count,
            "db_size_bytes": db_size,
        }

    # ── Querying for hypothesis generation ───────────────────────────

    def get_strong_discoveries(self, min_strength: float = 0.5,
                                max_age_cycles: int = 50,
                                current_cycle: int = 0) -> List[DiscoveryRecord]:
        """Get discoveries strong enough to generate follow-up hypotheses."""
        results = []
        for d in self.discoveries:
            age = current_cycle - d.cycle
            if d.strength >= min_strength and age <= max_age_cycles:
                if d.follow_ups_generated < 3:  # cap follow-ups per discovery
                    results.append(d)
        results.sort(key=lambda d: d.strength, reverse=True)
        return results

    def get_unexplored_variable_pairs(self, data_source: str) -> List[Tuple[str, str]]:
        """
        Suggest variable pairs that haven't been tested together.
        This drives genuine exploration rather than re-testing known pairs.
        """
        source_vars = {
            "exoplanets": ["period", "mass", "radius", "distance", "eccentricity",
                           "stellar_mass", "stellar_radius", "metallicity", "transit_depth"],
            "sdss": ["redshift", "u_g", "g_r", "r_i", "u", "g", "r", "i", "z",
                     "petroRad_r", "absMag_u", "absMag_r"],
            "gaia": ["parallax", "gmag", "bp_rp", "bp_g", "g_rp", "pmra", "pmdec",
                     "radial_velocity", "teff_val", "logg_val"],
            "pantheon": ["zHD", "m_b", "m_b_err", "biasCor", "is_calibrator"],
        }
        vars_available = source_vars.get(data_source, [])
        if not vars_available:
            return []

        es = self.exploration.get(data_source)
        tested = set()
        if es:
            for pair_key in es.variable_pairs_tested:
                parts = pair_key.split("__")
                if len(parts) == 2:
                    tested.add((parts[0], parts[1]))
                    tested.add((parts[1], parts[0]))

        untested = []
        for i, v1 in enumerate(vars_available):
            for v2 in vars_available[i+1:]:
                if (v1, v2) not in tested:
                    untested.append((v1, v2))
        return untested

    def get_best_methods(self, domain: str = None) -> List[Tuple[str, float]]:
        """
        Rank investigation methods by their historical success rate.
        Used to prioritize method selection in the INVESTIGATE phase.
        """
        method_scores = defaultdict(lambda: {"successes": 0, "total": 0, "avg_delta": 0.0})
        for m in self.method_outcomes:
            if domain and m.domain != domain:
                continue
            key = m.method_name
            s = method_scores[key]
            s["total"] += 1
            if m.success:
                s["successes"] += 1
            s["avg_delta"] += m.confidence_delta

        ranked = []
        for method, stats in method_scores.items():
            if stats["total"] < 2:
                continue
            success_rate = stats["successes"] / stats["total"]
            avg_delta = stats["avg_delta"] / stats["total"]
            score = 0.6 * success_rate + 0.4 * min(1.0, max(0, avg_delta * 5))
            ranked.append((method, score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def get_hot_domains(self, top_n: int = 3) -> List[Tuple[str, float]]:
        """Which domains have the most discovery momentum right now."""
        decayed = {}
        now = time.time()
        for domain, momentum in self._domain_momentum.items():
            # Decay by recent discoveries only
            recent = [d for d in self.discoveries
                      if d.domain == domain and now - d.timestamp < 3600 * 6]
            decayed[domain] = sum(d.strength for d in recent) if recent else momentum * 0.5
            self._domain_momentum[domain] = decayed[domain]

        ranked = sorted(decayed.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_n]

    def get_discovery_graph(self) -> Dict:
        """
        Build a graph of how discoveries relate to each other.
        Used for cross-domain linking based on shared structure, not randomness.
        """
        if len(self.discoveries) < 2:
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []
        discoveries = list(self.discoveries)

        for d in discoveries[-50:]:  # last 50
            nodes.append({
                "id": d.id, "domain": d.domain, "type": d.finding_type,
                "strength": d.strength, "variables": d.variables,
            })

        # Connect discoveries that share variables or finding types
        for i, d1 in enumerate(discoveries[-50:]):
            for d2 in discoveries[-50:][i+1:]:
                shared_vars = set(d1.variables) & set(d2.variables)
                shared_type = d1.finding_type == d2.finding_type
                cross_domain = d1.domain != d2.domain

                if shared_vars or (shared_type and cross_domain):
                    weight = len(shared_vars) * 0.3 + (0.2 if shared_type else 0) + (0.3 if cross_domain else 0)
                    if weight > 0.2:
                        edges.append({
                            "source": d1.id, "target": d2.id,
                            "weight": round(weight, 3),
                            "reason": "shared_vars" if shared_vars else "shared_type_cross_domain",
                        })

        return {"nodes": nodes, "edges": edges}

    # ── Self-improvement metrics ─────────────────────────────────────

    def compute_improvement_metrics(self) -> Dict:
        """
        Meta-analysis: how well is the system improving over time?
        Compare early vs recent performance.
        """
        if len(self.method_outcomes) < 10:
            return {"status": "insufficient_data", "total_outcomes": len(self.method_outcomes)}

        outcomes = list(self.method_outcomes)
        mid = len(outcomes) // 2
        early = outcomes[:mid]
        recent = outcomes[mid:]

        def metrics_batch(batch):
            success_rate = sum(1 for m in batch if m.success) / max(len(batch), 1)
            avg_sig = sum(m.significant_results for m in batch) / max(len(batch), 1)
            avg_novelty = sum(m.novelty_signals for m in batch) / max(len(batch), 1)
            avg_delta = sum(m.confidence_delta for m in batch) / max(len(batch), 1)
            return {
                "success_rate": round(success_rate, 3),
                "avg_significant_results": round(avg_sig, 2),
                "avg_novelty_signals": round(avg_novelty, 2),
                "avg_confidence_delta": round(avg_delta, 4),
            }

        early_m = metrics_batch(early)
        recent_m = metrics_batch(recent)

        improvement = {}
        for key in early_m:
            delta = recent_m[key] - early_m[key]
            improvement[key] = {
                "early": early_m[key],
                "recent": recent_m[key],
                "delta": round(delta, 4),
                "improving": delta > 0,
            }

        unique_count = self._get_unique_discovery_count()

        return {
            "status": "ok",
            "total_discoveries": len(self.discoveries),
            "unique_discoveries": unique_count,
            "total_outcomes": len(self.method_outcomes),
            "hypotheses_generated_from_memory": self.generation_count,
            "metrics": improvement,
        }

    def to_dict(self) -> dict:
        """Serialize for API response."""
        # Compute unique discovery count (excluding duplicates)
        unique_count = self._get_unique_discovery_count()

        return {
            "discovery_count": len(self.discoveries),
            "unique_discovery_count": unique_count,
            "method_outcome_count": len(self.method_outcomes),
            "exploration_sources": list(self.exploration.keys()),
            "generation_count": self.generation_count,
            "hot_domains": self.get_hot_domains(),
            "improvement": self.compute_improvement_metrics(),
            "top_variable_affinities": dict(sorted(
                self._variable_affinity.items(), key=lambda x: x[1], reverse=True
            )[:10]),
        }

    def _get_unique_discovery_count(self) -> int:
        """
        Get the count of unique discoveries (excluding duplicates).

        Uses the same deduplication logic as record_discovery().
        """
        seen_keys = set()
        for disc in self.discoveries:
            var_key = tuple(sorted(disc.variables)) if disc.variables else ()
            dedup_key = (disc.finding_type, disc.data_source, var_key)
            seen_keys.add(dedup_key)
        return len(seen_keys)
