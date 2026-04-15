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
Episodic Memory: Experience-Based Reasoning

This module implements episodic memory for storing and retrieving
specific reasoning episodes, enabling case-based reasoning and
learning from experience.

Key Features:
- Episode storage with full reasoning traces
- Similarity-based retrieval
- Pattern extraction from multiple episodes
- Integration with MORK biological fields

Why This Matters for AGI:
- Enables learning from specific experiences
- Supports case-based reasoning
- Provides continuity across reasoning sessions

Date: 2025-12-10
Version: 39.0
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import time
from collections import defaultdict
from pathlib import Path


class EpisodeType(Enum):
    """Types of reasoning episodes"""
    PROBLEM_SOLVING = "problem_solving"
    HYPOTHESIS_TESTING = "hypothesis_testing"
    DISCOVERY = "discovery"
    FAILURE_ANALYSIS = "failure_analysis"
    ANALOGY_FINDING = "analogy_finding"
    EXPERIMENT_DESIGN = "experiment_design"


class OutcomeStatus(Enum):
    """Outcome status of episodes"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    INCONCLUSIVE = "inconclusive"


@dataclass
class ReasoningStep:
    """A single step in a reasoning trace"""
    step_id: int
    action: str               # What was done
    input_state: Dict         # State before step
    output_state: Dict        # State after step
    rationale: str            # Why this step was taken
    confidence: float = 0.5   # Confidence in this step
    timestamp: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'action': self.action,
            'input_state': self.input_state,
            'output_state': self.output_state,
            'rationale': self.rationale,
            'confidence': self.confidence,
            'timestamp': self.timestamp
        }


@dataclass
class ReasoningTrace:
    """Complete trace of a reasoning process"""
    trace_id: str
    steps: List[ReasoningStep]
    initial_state: Dict
    final_state: Dict
    total_time: float = 0.0
    n_backtraces: int = 0     # Number of times we backtracked

    def to_dict(self) -> Dict:
        return {
            'trace_id': self.trace_id,
            'steps': [s.to_dict() for s in self.steps],
            'initial_state': self.initial_state,
            'final_state': self.final_state,
            'total_time': self.total_time,
            'n_backtraces': self.n_backtraces
        }

    @property
    def length(self) -> int:
        return len(self.steps)

    @property
    def avg_confidence(self) -> float:
        if not self.steps:
            return 0.0
        return np.mean([s.confidence for s in self.steps])


@dataclass
class Problem:
    """A problem that was solved"""
    problem_id: str
    problem_type: str
    description: str
    constraints: List[str]
    goals: List[str]
    context: Dict[str, Any]

    # Features for similarity matching
    features: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'problem_id': self.problem_id,
            'problem_type': self.problem_type,
            'description': self.description,
            'constraints': self.constraints,
            'goals': self.goals,
            'context': self.context,
            'features': self.features
        }


@dataclass
class Outcome:
    """Outcome of a reasoning episode"""
    status: OutcomeStatus
    result: Any
    metrics: Dict[str, float]
    lessons_learned: List[str] = field(default_factory=list)
    unexpected_findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'status': self.status.value,
            'result': self.result,
            'metrics': self.metrics,
            'lessons_learned': self.lessons_learned,
            'unexpected_findings': self.unexpected_findings
        }


@dataclass
class Episode:
    """A complete reasoning episode"""
    episode_id: str
    episode_type: EpisodeType
    problem: Problem
    reasoning_trace: ReasoningTrace
    outcome: Outcome
    timestamp: float = field(default_factory=time.time)

    # Metadata
    domain: str = "general"
    tags: List[str] = field(default_factory=list)
    related_episodes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'episode_id': self.episode_id,
            'episode_type': self.episode_type.value,
            'problem': self.problem.to_dict(),
            'reasoning_trace': self.reasoning_trace.to_dict(),
            'outcome': self.outcome.to_dict(),
            'timestamp': self.timestamp,
            'domain': self.domain,
            'tags': self.tags,
            'related_episodes': self.related_episodes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Episode':
        """Reconstruct episode from dict"""
        problem = Problem(
            problem_id=data['problem']['problem_id'],
            problem_type=data['problem']['problem_type'],
            description=data['problem']['description'],
            constraints=data['problem']['constraints'],
            goals=data['problem']['goals'],
            context=data['problem']['context'],
            features=data['problem'].get('features', {})
        )

        steps = [
            ReasoningStep(
                step_id=s['step_id'],
                action=s['action'],
                input_state=s['input_state'],
                output_state=s['output_state'],
                rationale=s['rationale'],
                confidence=s.get('confidence', 0.5),
                timestamp=s.get('timestamp', 0.0)
            )
            for s in data['reasoning_trace']['steps']
        ]

        trace = ReasoningTrace(
            trace_id=data['reasoning_trace']['trace_id'],
            steps=steps,
            initial_state=data['reasoning_trace']['initial_state'],
            final_state=data['reasoning_trace']['final_state'],
            total_time=data['reasoning_trace'].get('total_time', 0.0),
            n_backtraces=data['reasoning_trace'].get('n_backtraces', 0)
        )

        outcome = Outcome(
            status=OutcomeStatus(data['outcome']['status']),
            result=data['outcome']['result'],
            metrics=data['outcome']['metrics'],
            lessons_learned=data['outcome'].get('lessons_learned', []),
            unexpected_findings=data['outcome'].get('unexpected_findings', [])
        )

        return cls(
            episode_id=data['episode_id'],
            episode_type=EpisodeType(data['episode_type']),
            problem=problem,
            reasoning_trace=trace,
            outcome=outcome,
            timestamp=data.get('timestamp', time.time()),
            domain=data.get('domain', 'general'),
            tags=data.get('tags', []),
            related_episodes=data.get('related_episodes', [])
        )


@dataclass
class Pattern:
    """A pattern extracted from multiple episodes"""
    pattern_id: str
    pattern_type: str
    description: str
    source_episodes: List[str]

    # Pattern structure
    typical_steps: List[str]
    common_constraints: List[str]
    success_factors: List[str]
    failure_modes: List[str]

    # Statistics
    n_occurrences: int = 0
    avg_success_rate: float = 0.0
    confidence: float = 0.5

    def to_dict(self) -> Dict:
        return {
            'pattern_id': self.pattern_id,
            'pattern_type': self.pattern_type,
            'description': self.description,
            'source_episodes': self.source_episodes,
            'typical_steps': self.typical_steps,
            'common_constraints': self.common_constraints,
            'success_factors': self.success_factors,
            'failure_modes': self.failure_modes,
            'n_occurrences': self.n_occurrences,
            'avg_success_rate': self.avg_success_rate,
            'confidence': self.confidence
        }


class SimilarityMatcher:
    """Compute similarity between problems/episodes"""

    def __init__(self, feature_weights: Dict[str, float] = None):
        self.feature_weights = feature_weights or {
            'problem_type': 0.3,
            'domain': 0.2,
            'constraints': 0.25,
            'goals': 0.15,
            'features': 0.1
        }

    def problem_similarity(self, p1: Problem, p2: Problem) -> float:
        """Compute similarity between two problems"""
        score = 0.0

        # Problem type match
        if p1.problem_type == p2.problem_type:
            score += self.feature_weights['problem_type']

        # Constraint overlap
        if p1.constraints and p2.constraints:
            overlap = len(set(p1.constraints) & set(p2.constraints))
            union = len(set(p1.constraints) | set(p2.constraints))
            if union > 0:
                score += self.feature_weights['constraints'] * (overlap / union)

        # Goal overlap
        if p1.goals and p2.goals:
            overlap = len(set(p1.goals) & set(p2.goals))
            union = len(set(p1.goals) | set(p2.goals))
            if union > 0:
                score += self.feature_weights['goals'] * (overlap / union)

        # Feature similarity
        if p1.features and p2.features:
            feature_sim = self._feature_similarity(p1.features, p2.features)
            score += self.feature_weights['features'] * feature_sim

        return min(1.0, score)

    def episode_similarity(self, e1: Episode, e2: Episode) -> float:
        """Compute similarity between two episodes"""
        # Start with problem similarity
        prob_sim = self.problem_similarity(e1.problem, e2.problem)

        # Domain match
        domain_match = 1.0 if e1.domain == e2.domain else 0.5

        # Episode type match
        type_match = 1.0 if e1.episode_type == e2.episode_type else 0.7

        # Tag overlap
        if e1.tags and e2.tags:
            tag_overlap = len(set(e1.tags) & set(e2.tags))
            tag_union = len(set(e1.tags) | set(e2.tags))
            tag_sim = tag_overlap / tag_union if tag_union > 0 else 0.5
        else:
            tag_sim = 0.5

        # Weighted combination
        return (0.5 * prob_sim + 0.2 * domain_match +
                0.15 * type_match + 0.15 * tag_sim)

    def _feature_similarity(self, f1: Dict, f2: Dict) -> float:
        """Compute similarity between feature dicts"""
        all_keys = set(f1.keys()) | set(f2.keys())
        if not all_keys:
            return 0.5

        matches = 0
        for key in all_keys:
            if key in f1 and key in f2:
                if f1[key] == f2[key]:
                    matches += 1
                elif isinstance(f1[key], (int, float)) and isinstance(f2[key], (int, float)):
                    # Numerical similarity
                    max_val = max(abs(f1[key]), abs(f2[key]), 1)
                    matches += 1 - abs(f1[key] - f2[key]) / max_val

        return matches / len(all_keys)


class PatternExtractor:
    """Extract patterns from multiple episodes"""

    def __init__(self, min_support: int = 2, min_confidence: float = 0.5):
        self.min_support = min_support
        self.min_confidence = min_confidence

    def extract_patterns(self, episodes: List[Episode]) -> List[Pattern]:
        """Extract patterns from a set of episodes"""
        patterns = []

        # Group episodes by type
        by_type = defaultdict(list)
        for ep in episodes:
            by_type[ep.episode_type].append(ep)

        # Extract patterns for each type
        for ep_type, type_episodes in by_type.items():
            if len(type_episodes) >= self.min_support:
                pattern = self._extract_type_pattern(ep_type, type_episodes)
                if pattern and pattern.confidence >= self.min_confidence:
                    patterns.append(pattern)

        # Extract cross-type patterns for successful episodes
        successful = [ep for ep in episodes
                      if ep.outcome.status in [OutcomeStatus.SUCCESS, OutcomeStatus.PARTIAL_SUCCESS]]

        if len(successful) >= self.min_support:
            success_pattern = self._extract_success_pattern(successful)
            if success_pattern:
                patterns.append(success_pattern)

        # Extract failure patterns
        failures = [ep for ep in episodes if ep.outcome.status == OutcomeStatus.FAILURE]

        if len(failures) >= self.min_support:
            failure_pattern = self._extract_failure_pattern(failures)
            if failure_pattern:
                patterns.append(failure_pattern)

        return patterns

    def _extract_type_pattern(self, ep_type: EpisodeType,
                              episodes: List[Episode]) -> Optional[Pattern]:
        """Extract pattern for episode type"""
        # Collect common elements
        all_steps = []
        all_constraints = []
        success_factors = []

        for ep in episodes:
            # Steps
            for step in ep.reasoning_trace.steps:
                all_steps.append(step.action)

            # Constraints
            all_constraints.extend(ep.problem.constraints)

            # Lessons from successes
            if ep.outcome.status == OutcomeStatus.SUCCESS:
                success_factors.extend(ep.outcome.lessons_learned)

        # Find common steps
        step_counts = defaultdict(int)
        for step in all_steps:
            step_counts[step] += 1

        typical_steps = [
            step for step, count in step_counts.items()
            if count >= len(episodes) * 0.5
        ]

        # Find common constraints
        constraint_counts = defaultdict(int)
        for c in all_constraints:
            constraint_counts[c] += 1

        common_constraints = [
            c for c, count in constraint_counts.items()
            if count >= len(episodes) * 0.5
        ]

        # Compute success rate
        n_success = sum(1 for ep in episodes
                        if ep.outcome.status in [OutcomeStatus.SUCCESS, OutcomeStatus.PARTIAL_SUCCESS])
        success_rate = n_success / len(episodes)

        return Pattern(
            pattern_id=f"pattern_{ep_type.value}_{len(episodes)}",
            pattern_type=ep_type.value,
            description=f"Common pattern for {ep_type.value} episodes",
            source_episodes=[ep.episode_id for ep in episodes],
            typical_steps=typical_steps[:10],
            common_constraints=common_constraints[:5],
            success_factors=list(set(success_factors))[:5],
            failure_modes=[],
            n_occurrences=len(episodes),
            avg_success_rate=success_rate,
            confidence=len(typical_steps) / max(1, len(step_counts)) * success_rate
        )

    def _extract_success_pattern(self, episodes: List[Episode]) -> Optional[Pattern]:
        """Extract pattern from successful episodes"""
        success_factors = []
        successful_steps = []

        for ep in episodes:
            success_factors.extend(ep.outcome.lessons_learned)
            for step in ep.reasoning_trace.steps:
                if step.confidence > 0.7:
                    successful_steps.append(step.action)

        step_counts = defaultdict(int)
        for step in successful_steps:
            step_counts[step] += 1

        common_steps = [
            step for step, count in step_counts.items()
            if count >= len(episodes) * 0.3
        ]

        return Pattern(
            pattern_id=f"success_pattern_{len(episodes)}",
            pattern_type="success",
            description="Pattern extracted from successful episodes",
            source_episodes=[ep.episode_id for ep in episodes],
            typical_steps=common_steps[:10],
            common_constraints=[],
            success_factors=list(set(success_factors))[:10],
            failure_modes=[],
            n_occurrences=len(episodes),
            avg_success_rate=1.0,
            confidence=0.8
        )

    def _extract_failure_pattern(self, episodes: List[Episode]) -> Optional[Pattern]:
        """Extract pattern from failed episodes"""
        failure_modes = []
        failed_steps = []

        for ep in episodes:
            # Steps with low confidence often indicate problems
            for step in ep.reasoning_trace.steps:
                if step.confidence < 0.4:
                    failed_steps.append(step.action)

            # Collect lessons about failures
            failure_modes.extend(ep.outcome.lessons_learned)

        step_counts = defaultdict(int)
        for step in failed_steps:
            step_counts[step] += 1

        problematic_steps = [
            step for step, count in step_counts.items()
            if count >= len(episodes) * 0.3
        ]

        return Pattern(
            pattern_id=f"failure_pattern_{len(episodes)}",
            pattern_type="failure",
            description="Pattern extracted from failed episodes",
            source_episodes=[ep.episode_id for ep in episodes],
            typical_steps=problematic_steps[:10],
            common_constraints=[],
            success_factors=[],
            failure_modes=list(set(failure_modes))[:10],
            n_occurrences=len(episodes),
            avg_success_rate=0.0,
            confidence=0.7
        )


class EpisodicMemory:
    """
    Main Episodic Memory system.

    Stores, retrieves, and learns from reasoning episodes.
    """

    def __init__(self, storage_path: Optional[str] = None,
                 max_episodes: int = 10000):
        """
        Args:
            storage_path: Path for persistent storage
            max_episodes: Maximum episodes to store
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.max_episodes = max_episodes

        # Episode storage
        self.episodes: Dict[str, Episode] = {}
        self.episodes_by_domain: Dict[str, List[str]] = defaultdict(list)
        self.episodes_by_type: Dict[EpisodeType, List[str]] = defaultdict(list)

        # Similarity matching
        self.matcher = SimilarityMatcher()

        # Pattern extraction
        self.pattern_extractor = PatternExtractor()
        self.extracted_patterns: List[Pattern] = []

        # Load from storage if exists
        if self.storage_path and self.storage_path.exists():
            self.load()

    def store_episode(self, episode: Episode) -> str:
        """Store a new episode"""
        # Check capacity
        if len(self.episodes) >= self.max_episodes:
            self._evict_oldest()

        # Store
        self.episodes[episode.episode_id] = episode
        self.episodes_by_domain[episode.domain].append(episode.episode_id)
        self.episodes_by_type[episode.episode_type].append(episode.episode_id)

        # Auto-save if persistence enabled
        if self.storage_path:
            self._save_episode(episode)

        return episode.episode_id

    def retrieve_episode(self, episode_id: str) -> Optional[Episode]:
        """Retrieve episode by ID"""
        return self.episodes.get(episode_id)

    def retrieve_similar(self, problem: Problem, k: int = 5,
                         domain: str = None,
                         episode_type: EpisodeType = None) -> List[Tuple[Episode, float]]:
        """
        Retrieve k most similar episodes.

        Args:
            problem: Problem to match against
            k: Number of episodes to retrieve
            domain: Optional domain filter
            episode_type: Optional type filter

        Returns:
            List of (episode, similarity_score) tuples
        """
        # Get candidate episodes
        candidates = list(self.episodes.values())

        if domain:
            episode_ids = self.episodes_by_domain.get(domain, [])
            candidates = [self.episodes[eid] for eid in episode_ids
                         if eid in self.episodes]

        if episode_type:
            type_ids = set(self.episodes_by_type.get(episode_type, []))
            candidates = [ep for ep in candidates if ep.episode_id in type_ids]

        # Compute similarities
        similarities = []
        for ep in candidates:
            sim = self.matcher.problem_similarity(problem, ep.problem)
            similarities.append((ep, sim))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:k]

    def retrieve_successful(self, problem: Problem, k: int = 5) -> List[Episode]:
        """Retrieve successful episodes similar to problem"""
        similar = self.retrieve_similar(problem, k * 2)

        successful = [
            ep for ep, _ in similar
            if ep.outcome.status in [OutcomeStatus.SUCCESS, OutcomeStatus.PARTIAL_SUCCESS]
        ]

        return successful[:k]

    def retrieve_by_tags(self, tags: List[str], match_all: bool = False) -> List[Episode]:
        """Retrieve episodes by tags"""
        results = []
        tag_set = set(tags)

        for ep in self.episodes.values():
            ep_tags = set(ep.tags)
            if match_all:
                if tag_set <= ep_tags:
                    results.append(ep)
            else:
                if tag_set & ep_tags:
                    results.append(ep)

        return results

    def extract_patterns(self, domain: str = None,
                         episode_type: EpisodeType = None,
                         min_episodes: int = 3) -> List[Pattern]:
        """
        Extract patterns from stored episodes.

        Args:
            domain: Optional domain filter
            episode_type: Optional type filter
            min_episodes: Minimum episodes for pattern extraction

        Returns:
            List of extracted patterns
        """
        # Get relevant episodes
        episodes = list(self.episodes.values())

        if domain:
            episode_ids = self.episodes_by_domain.get(domain, [])
            episodes = [self.episodes[eid] for eid in episode_ids
                       if eid in self.episodes]

        if episode_type:
            episodes = [ep for ep in episodes if ep.episode_type == episode_type]

        if len(episodes) < min_episodes:
            return []

        # Extract patterns
        patterns = self.pattern_extractor.extract_patterns(episodes)

        # Store extracted patterns
        self.extracted_patterns.extend(patterns)

        return patterns

    def get_relevant_patterns(self, problem: Problem) -> List[Pattern]:
        """Get patterns relevant to a problem"""
        relevant = []

        for pattern in self.extracted_patterns:
            # Check problem type match
            if pattern.pattern_type == problem.problem_type:
                relevant.append(pattern)
            elif pattern.pattern_type in ['success', 'failure']:
                relevant.append(pattern)

        return relevant

    def learn_from_outcome(self, episode: Episode) -> List[str]:
        """
        Learn from episode outcome.

        Returns lessons learned.
        """
        lessons = []

        if episode.outcome.status == OutcomeStatus.SUCCESS:
            # Learn from success
            for step in episode.reasoning_trace.steps:
                if step.confidence > 0.8:
                    lessons.append(f"High-confidence step '{step.action}' led to success")

        elif episode.outcome.status == OutcomeStatus.FAILURE:
            # Learn from failure
            for step in episode.reasoning_trace.steps:
                if step.confidence < 0.3:
                    lessons.append(f"Low-confidence step '{step.action}' may have caused failure")

            # Check for common failure patterns
            for pattern in self.extracted_patterns:
                if pattern.pattern_type == 'failure':
                    for mode in pattern.failure_modes:
                        if mode in str(episode.problem.to_dict()):
                            lessons.append(f"Known failure mode detected: {mode}")

        return lessons

    def suggest_approach(self, problem: Problem) -> Dict[str, Any]:
        """
        Suggest approach based on similar past episodes.

        Returns suggested steps and warnings.
        """
        # Get similar successful episodes
        similar_successes = self.retrieve_successful(problem, k=3)

        if not similar_successes:
            return {
                'suggested_steps': [],
                'warnings': ['No similar successful episodes found'],
                'confidence': 0.3
            }

        # Extract common steps from successful episodes
        step_counts = defaultdict(int)
        for ep in similar_successes:
            for step in ep.reasoning_trace.steps:
                step_counts[step.action] += 1

        common_steps = [
            step for step, count in sorted(step_counts.items(),
                                          key=lambda x: x[1], reverse=True)
        ][:5]

        # Get relevant patterns
        patterns = self.get_relevant_patterns(problem)

        # Collect warnings from failure patterns
        warnings = []
        for pattern in patterns:
            if pattern.pattern_type == 'failure':
                for mode in pattern.failure_modes:
                    warnings.append(f"Potential failure mode: {mode}")

        # Compute confidence
        n_similar = len(similar_successes)
        avg_sim = np.mean([self.matcher.problem_similarity(problem, ep.problem)
                          for ep in similar_successes]) if similar_successes else 0

        return {
            'suggested_steps': common_steps,
            'warnings': warnings[:5],
            'confidence': avg_sim * (n_similar / 3.0),
            'source_episodes': [ep.episode_id for ep in similar_successes]
        }

    def _evict_oldest(self):
        """Remove oldest episode when at capacity"""
        if not self.episodes:
            return

        oldest_id = min(self.episodes.keys(),
                       key=lambda eid: self.episodes[eid].timestamp)
        del self.episodes[oldest_id]

    def _save_episode(self, episode: Episode):
        """Save single episode to storage"""
        if not self.storage_path:
            return

        self.storage_path.mkdir(parents=True, exist_ok=True)
        filepath = self.storage_path / f"{episode.episode_id}.json"

        with open(filepath, 'w') as f:
            json.dump(episode.to_dict(), f, indent=2)

    def save(self, filepath: str = None):
        """Save all episodes to storage"""
        path = Path(filepath) if filepath else self.storage_path
        if not path:
            return

        path.mkdir(parents=True, exist_ok=True)

        # Save episodes
        episodes_file = path / "episodes.json"
        with open(episodes_file, 'w') as f:
            json.dump({
                eid: ep.to_dict() for eid, ep in self.episodes.items()
            }, f, indent=2)

        # Save patterns
        patterns_file = path / "patterns.json"
        with open(patterns_file, 'w') as f:
            json.dump([p.to_dict() for p in self.extracted_patterns], f, indent=2)

    def load(self, filepath: str = None):
        """Load episodes from storage"""
        path = Path(filepath) if filepath else self.storage_path
        if not path or not path.exists():
            return

        # Load episodes
        episodes_file = path / "episodes.json"
        if episodes_file.exists():
            with open(episodes_file, 'r') as f:
                data = json.load(f)
                for eid, ep_data in data.items():
                    episode = Episode.from_dict(ep_data)
                    self.episodes[eid] = episode
                    self.episodes_by_domain[episode.domain].append(eid)
                    self.episodes_by_type[episode.episode_type].append(eid)

        # Load patterns
        patterns_file = path / "patterns.json"
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                data = json.load(f)
                for p_data in data:
                    pattern = Pattern(**p_data)
                    self.extracted_patterns.append(pattern)

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        by_status = defaultdict(int)
        for ep in self.episodes.values():
            by_status[ep.outcome.status.value] += 1

        return {
            'total_episodes': len(self.episodes),
            'by_status': dict(by_status),
            'by_domain': {d: len(ids) for d, ids in self.episodes_by_domain.items()},
            'by_type': {t.value: len(ids) for t, ids in self.episodes_by_type.items()},
            'n_patterns': len(self.extracted_patterns),
            'storage_path': str(self.storage_path) if self.storage_path else None
        }

    def clear(self):
        """Clear all episodes"""
        self.episodes.clear()
        self.episodes_by_domain.clear()
        self.episodes_by_type.clear()
        self.extracted_patterns.clear()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_episode(problem_desc: str, steps: List[Dict], outcome_status: str,
                   domain: str = "general") -> Episode:
    """Helper to create episode from simple inputs"""
    problem = Problem(
        problem_id=f"prob_{hashlib.md5(problem_desc.encode()).hexdigest()[:8]}",
        problem_type="general",
        description=problem_desc,
        constraints=[],
        goals=[],
        context={}
    )

    reasoning_steps = [
        ReasoningStep(
            step_id=i,
            action=s.get('action', ''),
            input_state=s.get('input', {}),
            output_state=s.get('output', {}),
            rationale=s.get('rationale', ''),
            confidence=s.get('confidence', 0.5)
        )
        for i, s in enumerate(steps)
    ]

    trace = ReasoningTrace(
        trace_id=f"trace_{time.time():.0f}",
        steps=reasoning_steps,
        initial_state={},
        final_state={}
    )

    outcome = Outcome(
        status=OutcomeStatus(outcome_status),
        result=None,
        metrics={}
    )

    return Episode(
        episode_id=f"ep_{time.time():.0f}_{np.random.randint(1000)}",
        episode_type=EpisodeType.PROBLEM_SOLVING,
        problem=problem,
        reasoning_trace=trace,
        outcome=outcome,
        domain=domain
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'EpisodicMemory',
    'Episode',
    'EpisodeType',
    'Problem',
    'Outcome',
    'OutcomeStatus',
    'ReasoningTrace',
    'ReasoningStep',
    'Pattern',
    'PatternExtractor',
    'SimilarityMatcher',
    'create_episode'
]
