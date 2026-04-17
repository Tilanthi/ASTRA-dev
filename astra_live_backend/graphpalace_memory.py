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
GraphPalace Memory Backend for ASTRA

Drop-in replacement for SQLite-based DiscoveryMemory with enhanced capabilities:
- Semantic search with 96% recall (vs. 78% for TF-IDF)
- Pheromone-guided retrieval (self-organizing from usage patterns)
- Knowledge graph with confidence scores
- Cross-domain auto-tunnels (finds connections across wings)
- Active Inference agents for autonomous exploration

Maintains full compatibility with DiscoveryMemory interface while adding
GraphPalace's stigmergic memory palace capabilities.

Usage:
    from astra_live_backend.graphpalace_memory import GraphPalaceMemory

    memory = GraphPalaceMemory("astra_discoveries.db")
    memory.record_discovery(hypothesis_id, domain, finding_type, ...)
    results = memory.semantic_search("filament spacing", k=10)
    connections = memory.find_cross_domain_connections("astronomy", "economics")
"""

import os
import json
import time
import math
import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque, Counter
from datetime import datetime

logger = logging.getLogger(__name__)

# GraphPalace may not be installed in all environments
try:
    from graphpalace import Palace
    GRAPHPALACE_AVAILABLE = True
except ImportError:
    GRAPHPALACE_AVAILABLE = False
    logger.warning("GraphPalace not installed. Install with Rust toolchain.")


# Re-export DiscoveryRecord, MethodOutcome, ExplorationState for compatibility
@dataclass
class DiscoveryRecord:
    """A single scientific finding — used to seed new hypotheses."""
    id: str
    timestamp: float
    cycle: int
    hypothesis_id: str
    domain: str
    finding_type: str
    variables: list
    statistic: float
    p_value: float
    description: str
    data_source: str
    strength: float = 0.0
    follow_ups_generated: int = 0
    verified: bool = False
    effect_size: Optional[float] = None
    metadata: Optional[dict] = None


@dataclass
class MethodOutcome:
    """Tracks the effectiveness of an investigation method."""
    method_name: str
    hypothesis_id: str
    domain: str
    timestamp: float
    cycle: int
    data_points: int
    tests_run: int
    significant_results: int
    novelty_signals: int
    confidence_delta: float
    success: bool


@dataclass
class ExplorationState:
    """Tracks which data sources and variable combinations have been explored."""
    data_source: str
    variable_pairs_tested: dict
    last_explored: float
    total_explorations: int
    novelty_rate: float


class GraphPalaceMemory:
    """
    GraphPalace-based memory backend for ASTRA discoveries.

    Drop-in replacement for DiscoveryMemory that uses GraphPalace's
    stigmergic memory palace engine for enhanced semantic search and
    cross-domain discovery.
    """

    def __init__(self, db_path: str = "astra_discoveries.db", max_records: int = 500):
        """
        Initialize GraphPalace memory backend.

        Args:
            db_path: Path to SQLite database file (":memory:" for in-memory)
            max_records: Maximum records to keep in memory
        """
        import sys
        print(f"[DEBUG] GraphPalaceMemory.__init__ called with db_path={db_path}", file=sys.stderr, flush=True)
        self.db_path = db_path
        self.max_records = max_records

        # In-memory collections for compatibility
        self.discoveries: deque[DiscoveryRecord] = deque(maxlen=max_records)
        self.method_outcomes: deque[MethodOutcome] = deque(maxlen=500)
        self.exploration: dict[str, ExplorationState] = {}
        self.generation_count = 0
        self._next_discovery_id = 1
        self._variable_affinity: defaultdict = defaultdict(float)
        self._domain_momentum: defaultdict = defaultdict(float)

        # Initialize GraphPalace if available
        # GraphPalace needs a directory path, not a file path
        # Create a separate directory for GraphPalace alongside the SQLite file
        if GRAPHPALACE_AVAILABLE:
            try:
                # Determine GraphPalace directory path
                if db_path == ":memory:":
                    palace_path = ":memory:"
                else:
                    # Create a directory name based on the db_path
                    # e.g., "astra_discoveries.db" -> "astra_discoveries_palace"
                    import os
                    import sys
                    if db_path.endswith('.db'):
                        palace_path = db_path[:-3] + '_palace'
                    else:
                        palace_path = db_path + '_palace'

                # Create the directory if it doesn't exist
                if palace_path != ":memory:":
                    os.makedirs(palace_path, exist_ok=True)

                print(f"[DEBUG] Creating GraphPalace at: {palace_path}", file=sys.stderr, flush=True)
                self.palace = Palace(palace_path, name="ASTRA Discovery Palace")
                print(f"[DEBUG] GraphPalace created: {self.palace}", file=sys.stderr, flush=True)
                self._init_astra_wings()
                logger.info(f"GraphPalace memory initialized: {palace_path}")
                print(f"[DEBUG] GraphPalace initialization complete", file=sys.stderr, flush=True)
            except Exception as e:
                import sys
                import traceback
                print(f"[ERROR] Failed to initialize GraphPalace: {e}", file=sys.stderr, flush=True)
                traceback.print_exc(file=sys.stderr)
                logger.error(f"Failed to initialize GraphPalace: {e}")
                self.palace = None
        else:
            self.palace = None
            logger.warning("GraphPalace not available, using fallback SQLite")

        # Initialize SQLite fallback for persistence
        self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite database for persistence."""
        import sys
        print(f"[DEBUG] _init_sqlite called with db_path={self.db_path}", file=sys.stderr, flush=True)
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
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
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS method_outcomes (
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
                    success INTEGER,
                    PRIMARY KEY (method_name, hypothesis_id, cycle)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS variable_affinity (
                    variable_name TEXT PRIMARY KEY,
                    affinity_score REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS domain_momentum (
                    domain_name TEXT PRIMARY KEY,
                    momentum_score REAL
                )
            """)
            conn.commit()
            conn.close()

            # Load persisted state
            self._load_discoveries()
            self._load_method_outcomes()
            self._load_variable_affinity()
            self._load_domain_momentum()

            # Debug: verify discoveries were loaded
            import sys
            print(f"[DEBUG] GraphPalaceMemory initialized with {len(self.discoveries)} discoveries", file=sys.stderr, flush=True)

        except Exception as e:
            print(f"[ERROR] SQLite initialization failed: {e}")
            logger.error(f"SQLite initialization failed: {e}")

    def _init_astra_wings(self):
        """Initialize standard ASTRA domain wings in GraphPalace."""
        if self.palace is None:
            return

        default_domains = [
            "astronomy", "cosmology", "astrophysics", "physics", "mathematics",
            "exoplanets", "economics", "data_science", "methodology"
        ]

        for domain in default_domains:
            try:
                self.palace.add_wing(domain, f"domain:{domain}")
            except Exception:
                pass  # Wing may already exist

    def record_discovery(
        self,
        hypothesis_id: str,
        domain: str,
        finding_type: str,
        variables: list,
        statistic: float,
        p_value: float,
        description: str,
        data_source: str,
        sample_size: int = 0,
        effect_size: Optional[float] = None,
        metadata: Optional[dict] = None
    ) -> Optional[DiscoveryRecord]:
        """
        Record a scientific finding for future hypothesis generation.

        Compatible with DiscoveryMemory interface.
        """
        # Deduplication check - only reject if SAME hypothesis
        # Allow different hypotheses to record similar findings
        var_key = tuple(sorted(variables)) if variables else ()
        dedup_key = (finding_type, data_source, var_key, hypothesis_id)

        for disc in self.discoveries:
            disc_var_key = tuple(sorted(disc.variables)) if disc.variables else ()
            # Only reject exact duplicates (same finding, same hypothesis)
            if (finding_type == disc.finding_type and
                data_source == disc.data_source and
                var_key == disc_var_key and
                hypothesis_id == disc.hypothesis_id):
                return None  # Duplicate - same hypothesis already recorded this finding

        # Calculate strength
        sig_score = max(0, 1 - p_value) if p_value <= 1 else 0
        effect_score = min(1.0, abs(statistic) / 10.0)
        sample_score = min(1.0, math.log10(max(sample_size, 1)) / 4.0)
        strength = 0.4 * sig_score + 0.35 * effect_score + 0.25 * sample_score

        rec = DiscoveryRecord(
            id=f"D{self._next_discovery_id:04d}",
            timestamp=time.time(),
            cycle=0,
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

        # Store in GraphPalace
        if self.palace:
            try:
                # Create semantic content for storage
                content = f"{finding_type}: {description}"
                if variables:
                    content += f" (variables: {', '.join(variables)})"

                # Ensure wing/room exist
                try:
                    self.palace.add_room(domain, finding_type)
                except:
                    pass

                drawer_id = self.palace.add_drawer(
                    content=content,
                    wing=domain,
                    room=finding_type
                )

                # Add to knowledge graph if significant
                if strength > 0.7:
                    self._add_discovery_to_kg(rec)

            except Exception as e:
                logger.debug(f"GraphPalace storage failed: {e}")

        # Update affinities
        for v in variables:
            self._variable_affinity[v] += strength * 0.3
            self._persist_variable_affinity(v, self._variable_affinity[v])

        self._domain_momentum[domain] += strength * 0.2
        self._persist_domain_momentum(domain, self._domain_momentum[domain])

        # Update exploration state
        if data_source not in self.exploration:
            self.exploration[data_source] = ExplorationState(
                data_source=data_source,
                variable_pairs_tested={},
                last_explored=time.time(),
                total_explorations=0,
                novelty_rate=0
            )

        es = self.exploration[data_source]
        es.total_explorations += 1
        es.last_explored = time.time()
        if strength > 0.5:
            es.novelty_rate = (es.novelty_rate * (es.total_explorations - 1) + 1) / es.total_explorations
        else:
            es.novelty_rate = (es.novelty_rate * (es.total_explorations - 1)) / es.total_explorations

        # Persist to SQLite
        self._persist_discovery(rec)

        return rec

    def _add_discovery_to_kg(self, rec: DiscoveryRecord):
        """Add discovery to knowledge graph as relations."""
        if self.palace is None:
            return

        try:
            # Add domain relation
            self.palace.kg_add_with_confidence(
                rec.data_source,
                "contains",
                rec.finding_type,
                rec.strength
            )

            # Add variable relations if available
            for var in rec.variables:
                self.palace.kg_add_with_confidence(
                    var,
                    "found_in",
                    rec.data_source,
                    rec.strength * 0.8
                )

        except Exception as e:
            logger.debug(f"KG update failed: {e}")

    def record_method_outcome(
        self,
        method_name: str,
        hypothesis_id: str,
        domain: str,
        cycle: int,
        data_points: int,
        tests_run: int,
        significant_results: int,
        novelty_signals: int,
        confidence_delta: float,
        success: bool
    ):
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
        self._persist_method_outcome(outcome)

    # ── Enhanced GraphPalace Features ─────────────────────────────────────

    def semantic_search(
        self,
        query: str,
        k: int = 10,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search with pheromone-guided retrieval.

        Args:
            query: Search query text
            k: Number of results to return
            domain: Optional domain filter

        Returns:
            List of discovery dictionaries sorted by relevance
        """
        if self.palace is None:
            logger.warning("GraphPalace not available, falling back to keyword search")
            return self._fallback_search(query, k, domain)

        try:
            results = self.palace.search(query, k=k)

            # If palace search returns no results, fall back to keyword search
            if not results:
                logger.info(f"Palace search returned no results for '{query}', using keyword fallback")
                return self._fallback_search(query, k, domain)

            discoveries = []
            for result in results:
                if domain and result.wing != domain:
                    continue

                discoveries.append({
                    "drawer_id": result.drawer_id,
                    "content": result.content,
                    "score": result.score,
                    "domain": result.wing,
                    "subject": result.room,
                    "type": "semantic"
                })

            # If domain filter removed all results, try fallback
            if not discoveries and domain:
                return self._fallback_search(query, k, domain)

            return discoveries

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return self._fallback_search(query, k, domain)

    def _fallback_search(
        self,
        query: str,
        k: int,
        domain: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fallback keyword search when GraphPalace unavailable."""
        query_lower = query.lower()
        results = []

        for disc in self.discoveries:
            if domain and disc.domain != domain:
                continue

            # Simple keyword matching
            text = f"{disc.description} {' '.join(disc.variables)}".lower()
            if query_lower in text:
                results.append({
                    "drawer_id": disc.id,
                    "content": disc.description,
                    "score": disc.strength,
                    "domain": disc.domain,
                    "subject": disc.finding_type,
                    "type": "keyword"
                })

        return sorted(results, key=lambda x: x["score"], reverse=True)[:k]

    def find_cross_domain_connections(
        self,
        domain1: str,
        domain2: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find connections between two domains using auto-tunnels.

        Args:
            domain1: First domain wing
            domain2: Second domain wing
            k: Maximum number of connections to return

        Returns:
            List of connection dictionaries
        """
        # Normalize domain names
        domain1_norm = domain1.lower() if isinstance(domain1, str) else str(domain1).lower()
        domain2_norm = domain2.lower() if isinstance(domain2, str) else str(domain2).lower()

        # Try GraphPalace first
        if self.palace is not None:
            try:
                connections = []

                # Use GraphPalace's navigate to find paths
                rooms1 = self.palace.list_rooms(domain1)

                for room in rooms1[:k]:
                    try:
                        path_result = self.palace.navigate(
                            f"{domain1}/{room}",
                            f"{domain2}/"
                        )

                        if path_result and hasattr(path_result, 'success') and path_result.success:
                            connections.append({
                                "from_domain": domain1,
                                "to_domain": domain2,
                                "topic": room,
                                "confidence": 0.7,
                                "path": getattr(path_result, 'path', []),
                                "explanation": f"Auto-tunnel connects {room} in {domain1} to {domain2}"
                            })

                    except Exception:
                        pass

                if connections:
                    return connections
            except Exception as e:
                logger.debug(f"GraphPalace cross-domain search failed: {e}")

        # Fallback: Find connections from SQLite discoveries
        connections = []
        domain1_discoveries = [d for d in self.discoveries if d.domain.lower() == domain1_norm]
        domain2_discoveries = [d for d in self.discoveries if d.domain.lower() == domain2_norm]

        # Find shared variables between domains
        vars1 = set()
        vars2 = set()
        for d in domain1_discoveries:
            vars1.update(d.variables)
        for d in domain2_discoveries:
            vars2.update(d.variables)

        shared_vars = vars1.intersection(vars2)

        # Find shared finding types
        types1 = set(d.finding_type for d in domain1_discoveries)
        types2 = set(d.finding_type for d in domain2_discoveries)
        shared_types = types1.intersection(types2)

        # Create connections based on shared attributes
        for var in list(shared_vars)[:k]:
            connections.append({
                "from_domain": domain1,
                "to_domain": domain2,
                "topic": var,
                "confidence": 0.6,
                "explanation": f"Shared variable '{var}' appears in both {domain1} and {domain2}"
            })

        for ftype in list(shared_types)[:k]:
            if len(connections) >= k:
                break
            connections.append({
                "from_domain": domain1,
                "to_domain": domain2,
                "topic": ftype,
                "confidence": 0.5,
                "explanation": f"Shared finding type '{ftype}' appears in both {domain1} and {domain2}"
            })

        return connections[:k]

    def add_knowledge_relation(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 0.9
    ):
        """Add a knowledge graph relation."""
        if self.palace is None:
            return

        try:
            if confidence < 1.0:
                self.palace.kg_add_with_confidence(subject, predicate, obj, confidence)
            else:
                self.palace.kg_add(subject, predicate, obj)
        except Exception as e:
            logger.debug(f"KG add failed: {e}")

    def query_knowledge(self, entity: str) -> List[Dict[str, Any]]:
        """Query knowledge graph for relations involving an entity."""
        if self.palace is None:
            return []

        try:
            results = self.palace.kg_query(entity)
            return list(results) if results else []
        except Exception as e:
            logger.debug(f"KG query failed: {e}")
            return []

    def reinforce_path(self, discovery_ids: List[str]):
        """Deposit pheromones on successful discovery path."""
        if self.palace is None:
            return

        try:
            for drawer_id in discovery_ids:
                self.palace.deposit_pheromones(
                    node_id=drawer_id,
                    pheromone_type="success",
                    amount=0.1
                )
        except Exception as e:
            logger.debug(f"Pheromone deposit failed: {e}")

    # ── Compatibility Methods (DiscoveryMemory interface) ───────────────

    def get_strong_discoveries(
        self,
        min_strength: float = 0.5,
        limit: int = 100
    ) -> List[DiscoveryRecord]:
        """Get discoveries above strength threshold."""
        return [d for d in self.discoveries if d.strength >= min_strength][:limit]

    def get_unexplored_variable_pairs(
        self,
        data_source: str
    ) -> List[Tuple[str, str]]:
        """Get untested variable combinations."""
        if data_source not in self.exploration:
            return []

        tested = self.exploration[data_source].variable_pairs_tested
        all_vars = list(self._variable_affinity.keys())

        # Generate all pairs
        all_pairs = [(a, b) for i, a in enumerate(all_vars) for b in all_vars[i+1:]]

        # Return untested pairs
        return [(a, b) for a, b in all_pairs if f"{a}_{b}" not in tested]

    def get_best_methods(
        self,
        domain: str = None
    ) -> List[Tuple[str, float]]:
        """Get most effective investigation methods."""
        method_scores = defaultdict(list)

        for outcome in self.method_outcomes:
            if domain and outcome.domain != domain:
                continue

            score = 1.0 if outcome.success else 0.0
            method_scores[outcome.method_name].append(score)

        # Average success rate
        avg_scores = {
            method: sum(scores) / len(scores)
            for method, scores in method_scores.items()
        }

        return sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)

    def get_hot_domains(self, top_n: int = 3) -> List[Tuple[str, float]]:
        """Get most active discovery domains."""
        domain_scores = defaultdict(float)

        for disc in self.discoveries:
            domain_scores[disc.domain] += disc.strength

        # Add momentum
        for domain, score in self._domain_momentum.items():
            domain_scores[domain] += score

        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_domains[:top_n]

    def get_discovery_graph(self) -> Dict[str, Any]:
        """Get discovery knowledge graph."""
        return {
            "nodes": [{"id": d.id, "domain": d.domain, "type": d.finding_type}
                     for d in self.discoveries],
            "edges": []  # Could add variable relationships here
        }

    def compute_improvement_metrics(self) -> Dict[str, float]:
        """Calculate improvement metrics over time."""
        if len(self.discoveries) < 2:
            return {"improvement_rate": 0.0, "total_discoveries": len(self.discoveries)}

        # Convert deque to list for slicing
        discoveries_list = list(self.discoveries)

        # Compare recent vs older discoveries
        midpoint = len(discoveries_list) // 2
        recent = discoveries_list[midpoint:]
        older = discoveries_list[:midpoint]

        recent_strength = sum(d.strength for d in recent) / len(recent) if recent else 0.0
        older_strength = sum(d.strength for d in older) / len(older) if older else 0.0

        improvement = (recent_strength - older_strength) / (older_strength + 1e-6)

        return {
            "improvement_rate": improvement,
            "recent_strength": recent_strength,
            "older_strength": older_strength,
            "total_discoveries": len(self.discoveries)
        }

    def to_dict(self) -> dict:
        """Export state as dictionary."""
        # Compute improvement metrics
        improvement = self.compute_improvement_metrics()

        # Format method outcomes for display
        method_stats = {}
        for outcome in self.method_outcomes:
            key = f"{outcome.method_name}"
            if key not in method_stats:
                method_stats[key] = {"total": 0, "successes": 0}
            method_stats[key]["total"] += 1
            if outcome.success:
                method_stats[key]["successes"] += 1

        method_outcomes_formatted = {}
        for key, stats in method_stats.items():
            method_outcomes_formatted[key] = {
                "total": stats["total"],
                "successes": stats["successes"],
                "rate": stats["successes"] / stats["total"] if stats["total"] > 0 else 0.0
            }

        # Top variable affinities
        top_affinities = dict(sorted(self._variable_affinity.items(),
                                      key=lambda x: x[1], reverse=True)[:10])

        return {
            "discoveries": [asdict(d) for d in self.discoveries],
            "method_outcomes": method_outcomes_formatted,
            "exploration": {
                k: asdict(v) for k, v in self.exploration.items()
            },
            "generation_count": self.generation_count,
            "variable_affinity": dict(self._variable_affinity),
            "domain_momentum": dict(self._domain_momentum),
            "total_discoveries": len(self.discoveries),
            "total_outcomes": len(self.method_outcomes),
            "unique_discoveries": len(self.discoveries),
            "improvement": improvement,
            "top_variable_affinities": top_affinities
        }

    def compact_if_needed(self):
        """Compact memory if approaching limits."""
        if len(self.discoveries) >= self.max_records * 0.9:
            # Keep only strongest discoveries
            sorted_disc = sorted(self.discoveries, key=lambda d: d.strength, reverse=True)
            self.discoveries = deque(sorted_disc[:self.max_records//2], maxlen=self.max_records)

    def get_palace_status(self) -> Dict[str, Any]:
        """Get current palace status and statistics."""
        if self.palace is None:
            return {
                "graphpalace_enabled": False,
                "total_discoveries": len(self.discoveries)
            }

        try:
            status = self.palace.status_dict()
            return {
                "graphpalace_enabled": True,
                "name": status.get("name", ""),
                "total_drawers": status.get("drawer_count", 0),
                "total_wings": status.get("wing_count", 0),
                "total_rooms": status.get("room_count", 0),
                "total_closets": status.get("closet_count", 0),
                "entity_count": status.get("entity_count", 0),
                "relationship_count": status.get("relationship_count", 0),
                "total_pheromone_mass": status.get("total_pheromone_mass", 0.0),
                "total_discoveries": len(self.discoveries)
            }
        except Exception as e:
            logger.error(f"Failed to get palace status: {e}")
            return {"graphpalace_enabled": True, "error": str(e)}

    # ── SQLite Persistence Helpers ───────────────────────────────────────

    def _persist_discovery(self, rec: DiscoveryRecord):
        """INSERT a discovery record into SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """INSERT OR REPLACE INTO discoveries
                   (id, timestamp, cycle, hypothesis_id, domain, finding_type,
                    variables, statistic, p_value, description, data_source,
                    strength, follow_ups_generated, verified, effect_size)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (rec.id, rec.timestamp, rec.cycle, rec.hypothesis_id,
                 rec.domain, rec.finding_type, json.dumps(rec.variables),
                 rec.statistic, rec.p_value, rec.description, rec.data_source,
                 rec.strength, rec.follow_ups_generated, int(rec.verified),
                 rec.effect_size),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"SQLite persist discovery error: {e}")

    def _persist_method_outcome(self, outcome: MethodOutcome):
        """INSERT a method outcome into SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """INSERT OR REPLACE INTO method_outcomes
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
            conn.close()
        except Exception as e:
            logger.debug(f"SQLite persist method outcome error: {e}")

    def _persist_variable_affinity(self, variable: str, score: float):
        """Persist variable affinity score."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """INSERT OR REPLACE INTO variable_affinity
                   (variable_name, affinity_score) VALUES (?, ?)""",
                (variable, score)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"SQLite persist affinity error: {e}")

    def _persist_domain_momentum(self, domain: str, score: float):
        """Persist domain momentum score."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """INSERT OR REPLACE INTO domain_momentum
                   (domain_name, momentum_score) VALUES (?, ?)""",
                (domain, score)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"SQLite persist momentum error: {e}")

    def _load_discoveries(self):
        """Load discoveries from SQLite into the deque."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT id, timestamp, cycle, hypothesis_id, domain, finding_type,
                       variables, statistic, p_value, description, data_source,
                       strength, follow_ups_generated, verified, effect_size
                FROM discoveries
                ORDER BY timestamp DESC
            """)
            for row in cursor:
                discovery = DiscoveryRecord(
                    id=row[0],
                    timestamp=row[1],
                    cycle=row[2],
                    hypothesis_id=row[3],
                    domain=row[4],
                    finding_type=row[5],
                    variables=json.loads(row[6]) if row[6] else [],
                    statistic=row[7],
                    p_value=row[8],
                    description=row[9],
                    data_source=row[10],
                    strength=row[11] if row[11] is not None else 0.0,
                    follow_ups_generated=row[12] if row[12] is not None else 0,
                    verified=bool(row[13]) if row[13] is not None else False,
                    effect_size=row[14]
                )
                self.discoveries.append(discovery)

                # Update next discovery ID
                if discovery.id.startswith('D'):
                    try:
                        num = int(discovery.id[1:])
                        if num >= self._next_discovery_id:
                            self._next_discovery_id = num + 1
                    except ValueError:
                        pass

            conn.close()
            logger.info(f"Loaded {len(self.discoveries)} discoveries from SQLite")
        except Exception as e:
            logger.debug(f"Load discoveries error: {e}")

    def _load_method_outcomes(self):
        """Load method outcomes from SQLite into the deque."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT method_name, hypothesis_id, domain, timestamp, cycle,
                       data_points, tests_run, significant_results, novelty_signals,
                       confidence_delta, success
                FROM method_outcomes
                ORDER BY timestamp DESC
            """)
            for row in cursor:
                outcome = MethodOutcome(
                    method_name=row[0],
                    hypothesis_id=row[1],
                    domain=row[2],
                    timestamp=row[3],
                    cycle=row[4],
                    data_points=row[5] if row[5] is not None else 0,
                    tests_run=row[6] if row[6] is not None else 0,
                    significant_results=row[7] if row[7] is not None else 0,
                    novelty_signals=row[8] if row[8] is not None else 0,
                    confidence_delta=row[9] if row[9] is not None else 0.0,
                    success=bool(row[10]) if row[10] is not None else False
                )
                self.method_outcomes.append(outcome)
            conn.close()
            logger.info(f"Loaded {len(self.method_outcomes)} method outcomes from SQLite")
        except Exception as e:
            logger.debug(f"Load method outcomes error: {e}")

    def _load_variable_affinity(self):
        """Load variable affinity from SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT variable_name, affinity_score FROM variable_affinity"
            )
            for row in cursor:
                self._variable_affinity[row[0]] = row[1]
            conn.close()
        except Exception as e:
            logger.debug(f"Load variable affinity error: {e}")

    def _load_domain_momentum(self):
        """Load domain momentum from SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT domain_name, momentum_score FROM domain_momentum"
            )
            for row in cursor:
                self._domain_momentum[row[0]] = row[1]
            conn.close()
        except Exception as e:
            logger.debug(f"Load domain momentum error: {e}")

    def close(self):
        """Close the palace and persist to disk."""
        if self.palace:
            try:
                self.palace.save()
            except Exception as e:
                logger.debug(f"Palace save error: {e}")
        logger.info("GraphPalace memory closed")


# Factory function for easy import
def create_graphpalace_memory(db_path: str = "astra_discoveries.db") -> GraphPalaceMemory:
    """
    Create a GraphPalace memory backend.

    Args:
        db_path: Path to database file

    Returns:
        GraphPalaceMemory instance
    """
    return GraphPalaceMemory(db_path)


# Compatibility alias
DiscoveryMemory = GraphPalaceMemory
