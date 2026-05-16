"""
Adaptive Autonomous Discovery System

Fixed architecture that learns from previous discoveries and avoids redundancy.
Implements novelty detection, exploration planning, and convergence detection.
"""

import numpy as np
import sqlite3
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from collections import deque
import heapq

# from .types import Discovery, Hypothesis, ValidationResult  # Not used yet

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredRelationship:
    """A relationship that has been discovered"""
    var1: str
    var2: str
    relationship_type: str  # 'causal' or 'correlational'
    statistic: float
    p_value: float
    first_discovered: datetime
    confirmation_count: int = 1

    def __hash__(self):
        return hash((self.var1, self.var2, self.relationship_type))

    def __eq__(self, other):
        return (self.var1 == other.var1 and
                self.var2 == other.var2 and
                self.relationship_type == other.relationship_type)

    def to_tuple(self):
        """Return as tuple for set operations"""
        return (self.var1, self.var2, self.relationship_type)


class DiscoveryRegistry:
    """
    Registry of all discoveries to prevent redundancy.

    This component was MISSING in the original design, leading to
    99.9% redundancy in discoveries.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/data/discovery_registry.db"

        self.db_path = db_path
        self.conn = None
        self._connect()
        self._initialize_tables()

        # In-memory cache for fast lookups
        self.discovered_relationships: Set[Tuple[str, str, str]] = set()
        self._load_into_memory()

        logger.info(f"DiscoveryRegistry initialized with {len(self.discovered_relationships)} known relationships")

    def _connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def _initialize_tables(self):
        """Initialize database tables"""
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discoveries (
                var1 TEXT,
                var2 TEXT,
                relationship_type TEXT,
                statistic REAL,
                p_value REAL,
                first_discovered TEXT,
                confirmation_count INTEGER DEFAULT 1,
                PRIMARY KEY (var1, var2, relationship_type)
            )
        ''')

        self.conn.commit()

    def _load_into_memory(self):
        """Load existing discoveries into memory for fast lookup"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT var1, var2, relationship_type FROM discoveries')

        for row in cursor.fetchall():
            self.discovered_relationships.add((row['var1'], row['var2'], row['relationship_type']))

    def is_novel(self, var1: str, var2: str, relationship_type: str) -> bool:
        """Check if relationship is novel"""
        # Check both orderings for correlational relationships
        if relationship_type == 'correlational':
            return ((var1, var2, relationship_type) not in self.discovered_relationships and
                    (var2, var1, relationship_type) not in self.discovered_relationships)
        else:
            return (var1, var2, relationship_type) not in self.discovered_relationships

    def register_discovery(self, var1: str, var2: str, relationship_type: str,
                          statistic: float, p_value: float):
        """Register a new discovery"""
        now = datetime.now().isoformat()

        cursor = self.conn.cursor()

        # Check if already exists (maybe from different run)
        cursor.execute('''
            SELECT confirmation_count FROM discoveries
            WHERE var1 = ? AND var2 = ? AND relationship_type = ?
        ''', (var1, var2, relationship_type))

        row = cursor.fetchone()

        if row:
            # Update confirmation count
            cursor.execute('''
                UPDATE discoveries
                SET confirmation_count = confirmation_count + 1,
                    statistic = ?,
                    p_value = ?
                WHERE var1 = ? AND var2 = ? AND relationship_type = ?
            ''', (statistic, p_value, var1, var2, relationship_type))
        else:
            # Insert new discovery
            cursor.execute('''
                INSERT INTO discoveries (var1, var2, relationship_type, statistic, p_value, first_discovered)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (var1, var2, relationship_type, statistic, p_value, now))

            # Add to memory cache
            self.discovered_relationships.add((var1, var2, relationship_type))

        self.conn.commit()

    def get_statistics(self) -> Dict:
        """Get registry statistics"""
        cursor = self.conn.cursor()

        cursor.execute('SELECT COUNT(*) as total FROM discoveries')
        total = cursor.fetchone()[0]

        cursor.execute('''
            SELECT relationship_type, COUNT(*) as count
            FROM discoveries
            GROUP BY relationship_type
        ''')
        by_type = {row['relationship_type']: row['count'] for row in cursor.fetchall()}

        return {
            'total_discoveries': total,
            'by_type': by_type
        }


class NoveltyDetector:
    """
    Assess the novelty of potential discoveries.

    This component was MISSING in the original design, leading to
    storage of duplicate discoveries as if they were new.
    """

    def __init__(self, registry: DiscoveryRegistry):
        self.registry = registry

    def assess_novelty(self, var1: str, var2: str, relationship_type: str,
                      context: Optional[Dict] = None) -> float:
        """
        Assess novelty score (0.0 = known, 1.0 = completely novel)

        Returns 0.0 if relationship already discovered
        Returns 1.0 if completely new relationship
        Returns intermediate values for partial novelty
        """
        # Check if directly known
        if not self.registry.is_novel(var1, var2, relationship_type):
            return 0.0

        # Check if variables are involved in any known discoveries
        var1_known = any((var1, v, t) in self.registry.discovered_relationships or
                        (v, var1, t) in self.registry.discovered_relationships
                        for v in ['any'] for t in ['causal', 'correlational'])

        var2_known = any((var2, v, t) in self.registry.discovered_relationships or
                        (v, var2, t) in self.registry.discovered_relationships
                        for v in ['any'] for t in ['causal', 'correlational'])

        if var1_known and var2_known:
            # Both variables known but this specific relationship is new
            return 0.5
        elif var1_known or var2_known:
            # One variable known, one new
            return 0.75
        else:
            # Both variables new
            return 1.0


class ExplorationPlanner:
    """
    Plan systematic exploration of hypothesis space.

    This component was MISSING in the original design, leading to
    random repeated exploration of the same combinations.
    """

    def __init__(self, registry: DiscoveryRegistry, variables: List[str]):
        self.registry = registry
        self.all_variables = variables

        # Track which combinations have been explored
        self.explored_combinations: Set[Tuple[str, str]] = set()

        # Priority queue for unexplored combinations (novelty, var1, var2)
        self.frontier: List[Tuple[float, str, str]] = []

        # Initialize frontier with all combinations
        self._initialize_frontier()

    def _initialize_frontier(self):
        """Generate all possible variable combinations"""
        for i, var1 in enumerate(self.all_variables):
            for var2 in self.all_variables[i+1:]:
                # Check if already explored
                if (var1, var2) not in self.explored_combinations:
                    # Calculate initial priority (prefer novel combinations)
                    causal_novel = self.registry.is_novel(var1, var2, 'causal')
                    correl_novel = self.registry.is_novel(var1, var2, 'correlational')

                    if causal_novel or correl_novel:
                        priority = 1.0  # High priority for novel combinations
                        heapq.heappush(self.frontier, (-priority, var1, var2))

        logger.info(f"ExplorationPlanner initialized with {len(self.frontier)} unexplored combinations")

    def get_next_hypothesis(self) -> Optional[Tuple[str, str]]:
        """Get next hypothesis to explore"""
        while self.frontier:
            priority, var1, var2 = heapq.heappop(self.frontier)

            # Check if both causal and correlational have been explored
            causal_explored = not self.registry.is_novel(var1, var2, 'causal')
            correl_explored = not self.registry.is_novel(var2, var1, 'correlational')

            if causal_explored and correl_explored:
                # Both explored, mark combination as done
                self.explored_combinations.add((var1, var2))
                continue

            # Return this hypothesis for exploration
            return (var1, var2)

        # Frontier exhausted
        logger.info("Exploration frontier exhausted - all combinations explored")
        return None

    def mark_explored(self, var1: str, var2: str, relationship_type: str):
        """Mark a relationship as explored"""
        if relationship_type == 'causal':
            self.explored_combinations.add((var1, var2))
        else:  # correlational
            self.explored_combinations.add((var2, var1))

    def get_progress(self) -> Dict:
        """Get exploration progress statistics"""
        total_possible = len(self.all_variables) * (len(self.all_variables) - 1) // 2
        explored = len(self.explored_combinations)
        remaining = len(self.frontier)

        return {
            'total_combinations': total_possible,
            'explored': explored,
            'remaining_in_frontier': remaining,
            'progress_percent': (explored / total_possible * 100) if total_possible > 0 else 0
        }


class ConvergenceDetector:
    """
    Detect when exploration has converged or exhausted the space.

    This component was MISSING in the original design, leading to
    infinite running with no stopping criteria.
    """

    def __init__(self, window_size: int = 10, novelty_threshold: float = 0.05):
        self.window_size = window_size
        self.novelty_threshold = novelty_threshold
        self.novelty_history: deque = deque(maxlen=window_size)

    def update(self, novelty_score: float):
        """Update with latest discovery novelty"""
        self.novelty_history.append(novelty_score)

    def should_stop(self) -> bool:
        """Check if convergence criteria met"""
        if len(self.novelty_history) < self.window_size:
            return False

        recent_novelty = sum(self.novelty_history) / len(self.novelty_history)
        return recent_novelty < self.novelty_threshold

    def get_status(self) -> Dict:
        """Get convergence status"""
        if not self.novelty_history:
            return {'status': 'insufficient_data'}

        recent_novelty = sum(self.novelty_history) / len(self.novelty_history)

        if recent_novelty < self.novelty_threshold:
            return {
                'status': 'converged',
                'recent_novelty': recent_novelty,
                'threshold': self.novelty_threshold
            }
        else:
            return {
                'status': 'exploring',
                'recent_novelty': recent_novelty,
                'threshold': self.novelty_threshold
            }


class AdaptiveDiscoveryPipeline:
    """
    Improved discovery pipeline with learning and exploration.

    This addresses the critical flaws in the original design:
    1. DiscoveryRegistry prevents redundant discoveries
    2. NoveltyDetector assesses newness
    3. ExplorationPlanner systematically explores
    4. ConvergenceDetector detects when to stop
    """

    def __init__(self, variables: List[str]):
        # Core components
        self.registry = DiscoveryRegistry()
        self.novelty_detector = NoveltyDetector(self.registry)
        self.exploration_planner = ExplorationPlanner(self.registry, variables)
        self.convergence_detector = ConvergenceDetector()

        # Statistics
        self.cycles_run = 0
        self.novel_discoveries = 0
        self.redundant_discoveries = 0

        logger.info("AdaptiveDiscoveryPipeline initialized")

    def run_cycle(self, data: Dict[str, np.ndarray]) -> Optional[Dict]:
        """Run one adaptive discovery cycle - tries hypotheses until significant one found"""
        self.cycles_run += 1

        max_attempts = 100  # Prevent infinite loop
        attempts = 0

        while attempts < max_attempts:
            # Get next hypothesis to explore
            hypothesis = self.exploration_planner.get_next_hypothesis()

            if hypothesis is None:
                logger.info("No more hypotheses to explore - space exhausted")
                return None

            var1, var2 = hypothesis
            attempts += 1

            # Test the hypothesis
            result = self._test_relationship(data, var1, var2)

            if result['significant']:
                # Found a significant relationship - assess novelty for both types
                best_novelty = 0.0
                best_result = None

                for rel_type in ['causal', 'correlational']:
                    novelty = self.novelty_detector.assess_novelty(var1, var2, rel_type)

                    if novelty > 0.0:  # Novel discovery
                        # Register it
                        self.registry.register_discovery(
                            var1, var2, rel_type,
                            result['statistic'], result['p_value']
                        )

                        # Mark as explored
                        self.exploration_planner.mark_explored(var1, var2, rel_type)

                        if novelty >= 0.5:  # Truly novel
                            self.novel_discoveries += 1
                            logger.info(f"NOVEL DISCOVERY: {var1} {rel_type} {var2} (novelty={novelty:.2f})")
                        else:
                            self.redundant_discoveries += 1

                        # Update convergence detector
                        self.convergence_detector.update(novelty)

                        if novelty > best_novelty:
                            best_novelty = novelty
                            best_result = {
                                'var1': var1,
                                'var2': var2,
                                'type': rel_type,
                                'statistic': result['statistic'],
                                'p_value': result['p_value'],
                                'novelty': novelty,
                                'cycle': self.cycles_run
                            }

                # Return the best novel discovery found
                if best_result:
                    return best_result

            # Mark this combination as attempted (no significant relationship found)
            # Don't mark as fully explored since we might want to revisit with different data

        # Update convergence detector with zero novelty (exhausted attempts)
        self.convergence_detector.update(0.0)

        # Check if we should stop
        if self.convergence_detector.should_stop():
            logger.info("Convergence detected - stopping exploration")
            return None

        return None

    def _test_relationship(self, data: Dict[str, np.ndarray],
                          var1: str, var2: str) -> Dict:
        """Test relationship between two variables"""
        from scipy import stats

        try:
            x = data.get(var1)
            y = data.get(var2)

            if x is None or y is None:
                return {'significant': False}

            # Remove NaN
            mask = ~(np.isnan(x) | np.isnan(y))
            x, y = x[mask], y[mask]

            if len(x) < 10:
                return {'significant': False}

            # Pearson correlation
            corr, p_value = stats.pearsonr(x, y)

            # Significance criteria
            significant = p_value < 0.05 and abs(corr) > 0.3

            return {
                'significant': significant,
                'statistic': corr,
                'p_value': p_value,
                'n': len(x)
            }

        except Exception as e:
            logger.error(f"Error testing relationship {var1}-{var2}: {e}")
            return {'significant': False}

    def get_statistics(self) -> Dict:
        """Get pipeline statistics"""
        registry_stats = self.registry.get_statistics()
        progress_stats = self.exploration_planner.get_progress()
        convergence_status = self.convergence_detector.get_status()

        return {
            'cycles_run': self.cycles_run,
            'novel_discoveries': self.novel_discoveries,
            'redundant_discoveries': self.redundant_discoveries,
            'efficiency': (self.novel_discoveries / self.cycles_run * 100) if self.cycles_run > 0 else 0,
            'registry': registry_stats,
            'exploration_progress': progress_stats,
            'convergence': convergence_status
        }

    def should_continue(self) -> bool:
        """Check if exploration should continue"""
        # Check if frontier is exhausted
        hypothesis = self.exploration_planner.get_next_hypothesis()
        if hypothesis is None:
            return False

        # Check for convergence
        if self.convergence_detector.should_stop():
            return False

        return True
