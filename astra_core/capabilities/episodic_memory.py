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
Episodic Memory System for STAN V39

Stores and retrieves specific reasoning episodes for case-based reasoning
and learning from experience.

Core capabilities:
- Episode storage with full reasoning traces
- Similarity-based retrieval
- Pattern extraction across episodes
- Integration with RAG for semantic search

Date: 2025-12-10
Version: 39.0
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from enum import Enum
from abc import ABC, abstractmethod
import json
import hashlib
from collections import defaultdict
import time
from datetime import datetime


class EpisodeType(Enum):
    """Types of reasoning episodes"""
    PROBLEM_SOLVING = "problem_solving"
    HYPOTHESIS_TESTING = "hypothesis_testing"
    CAUSAL_INFERENCE = "causal_inference"
    ANALOGY_FINDING = "analogy_finding"
    EXPLANATION_GENERATION = "explanation_generation"
    EXPERIMENT_DESIGN = "experiment_design"
    PREDICTION = "prediction"
    DISCOVERY = "discovery"


class OutcomeType(Enum):
    """Outcome types for episodes"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    INCONCLUSIVE = "inconclusive"


@dataclass
class ReasoningStep:
    """A single step in a reasoning trace"""
    step_id: int
    action: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    reasoning: str
    confidence: float = 0.5
    duration_ms: float = 0.0
    tools_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'action': self.action,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'duration_ms': self.duration_ms,
            'tools_used': self.tools_used
        }


@dataclass
class Problem:
    """A problem that was solved"""
    problem_id: str
    description: str
    domain: str
    problem_type: str
    inputs: Dict[str, Any]
    constraints: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    difficulty: float = 0.5  # 0-1 scale
    features: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'problem_id': self.problem_id,
            'description': self.description,
            'domain': self.domain,
            'problem_type': self.problem_type,
            'inputs': self.inputs,
            'constraints': self.constraints,
            'goals': self.goals,
            'difficulty': self.difficulty,
            'features': self.features
        }


@dataclass
class Outcome:
    """Outcome of a reasoning episode"""
    outcome_type: OutcomeType
    solution: Any
    metrics: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    confidence: float = 0.5

    def to_dict(self) -> Dict:
        return {
            'outcome_type': self.outcome_type.value,
            'solution': str(self.solution) if self.solution else None,
            'metrics': self.metrics,
            'errors': self.errors,
            'insights': self.insights,
            'confidence': self.confidence
        }


@dataclass
class Episode:
    """A complete reasoning episode"""
    episode_id: str
    episode_type: EpisodeType
    problem: Problem
    reasoning_trace: List[ReasoningStep]
    outcome: Outcome
    timestamp: float = field(default_factory=time.time)

    # Metadata for retrieval
    duration_ms: float = 0.0
    n_steps: int = 0
    strategies_used: List[str] = field(default_factory=list)
    key_decisions: List[str] = field(default_factory=list)

    # Embedding for similarity search
    embedding: Optional[np.ndarray] = None

    # Links to related episodes
    similar_episodes: List[str] = field(default_factory=list)
    follow_up_episodes: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.n_steps = len(self.reasoning_trace)
        if self.reasoning_trace:
            self.duration_ms = sum(s.duration_ms for s in self.reasoning_trace)

    def to_dict(self) -> Dict:
        return {
            'episode_id': self.episode_id,
            'episode_type': self.episode_type.value,
            'problem': self.problem.to_dict(),
            'reasoning_trace': [s.to_dict() for s in self.reasoning_trace],
            'outcome': self.outcome.to_dict(),
            'timestamp': self.timestamp,
            'duration_ms': self.duration_ms,
            'n_steps': self.n_steps,
            'strategies_used': self.strategies_used,
            'key_decisions': self.key_decisions,
            'similar_episodes': self.similar_episodes
        }

    def get_text_representation(self) -> str:
        """Get text representation for embedding"""
        parts = [
            f"Problem: {self.problem.description}",
            f"Domain: {self.problem.domain}",
            f"Type: {self.problem.problem_type}",
            f"Outcome: {self.outcome.outcome_type.value}",
        ]

        # Add key reasoning steps
        for step in self.reasoning_trace[:5]:  # First 5 steps
            parts.append(f"Step {step.step_id}: {step.action} - {step.reasoning[:100]}")

        # Add insights
        for insight in self.outcome.insights[:3]:
            parts.append(f"Insight: {insight}")

        return "\n".join(parts)


@dataclass
class Pattern:
    """A pattern extracted from multiple episodes"""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    success_rate: float
    episode_ids: List[str]
    conditions: List[str]  # When this pattern applies
    actions: List[str]     # What to do
    expected_outcome: str

    def to_dict(self) -> Dict:
        return {
            'pattern_id': self.pattern_id,
            'pattern_type': self.pattern_type,
            'description': self.description,
            'frequency': self.frequency,
            'success_rate': self.success_rate,
            'n_episodes': len(self.episode_ids),
            'conditions': self.conditions,
            'actions': self.actions,
            'expected_outcome': self.expected_outcome
        }


class EpisodeEmbedder:
    """Creates embeddings for episodes"""

    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.vocabulary: Dict[str, int] = {}
        self.idf_scores: Dict[str, float] = {}
        self.vocab_counter = 0

    def embed(self, episode: Episode) -> np.ndarray:
        """Create embedding for an episode"""
        text = episode.get_text_representation()
        return self._text_to_embedding(text)

    def embed_problem(self, problem: Problem) -> np.ndarray:
        """Create embedding for a problem"""
        text = f"{problem.description} {problem.domain} {problem.problem_type}"
        return self._text_to_embedding(text)

    def _text_to_embedding(self, text: str) -> np.ndarray:
        """Convert text to embedding using TF-IDF + dimension reduction"""
        # Tokenize
        tokens = self._tokenize(text)

        # Build vocabulary
        for token in tokens:
            if token not in self.vocabulary:
                self.vocabulary[token] = self.vocab_counter
                self.vocab_counter += 1

        # Create TF vector
        tf = np.zeros(self.embedding_dim)
        for token in tokens:
            idx = self.vocabulary[token] % self.embedding_dim
            tf[idx] += 1

        # Normalize
        norm = np.linalg.norm(tf)
        if norm > 0:
            tf = tf / norm

        return tf

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        text = text.lower()
        # Remove punctuation and split
        for char in '.,;:!?()[]{}"\'-':
            text = text.replace(char, ' ')
        tokens = text.split()
        # Filter short tokens
        return [t for t in tokens if len(t) > 2]

    def similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between embeddings"""
        if emb1 is None or emb2 is None:
            return 0.0

        dot = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)


class EpisodicMemory:
    """
    Episodic memory system for storing and retrieving reasoning episodes.

    Supports:
    - Episode storage with full reasoning traces
    - Similarity-based retrieval
    - Pattern extraction
    - Case-based reasoning
    """

    def __init__(self, max_episodes: int = 10000):
        self.max_episodes = max_episodes
        self.episodes: Dict[str, Episode] = {}
        self.embedder = EpisodeEmbedder()

        # Indices for efficient retrieval
        self.by_type: Dict[EpisodeType, List[str]] = defaultdict(list)
        self.by_domain: Dict[str, List[str]] = defaultdict(list)
        self.by_outcome: Dict[OutcomeType, List[str]] = defaultdict(list)
        self.by_problem_type: Dict[str, List[str]] = defaultdict(list)

        # Extracted patterns
        self.patterns: Dict[str, Pattern] = {}

        # Statistics
        self.total_stored = 0
        self.total_retrieved = 0

    def store_episode(self, problem: Problem,
                      reasoning_trace: List[ReasoningStep],
                      outcome: Outcome,
                      episode_type: EpisodeType = EpisodeType.PROBLEM_SOLVING,
                      strategies: List[str] = None,
                      key_decisions: List[str] = None) -> str:
        """
        Store a new reasoning episode.

        Args:
            problem: The problem that was solved
            reasoning_trace: Steps taken to solve it
            outcome: The outcome
            episode_type: Type of episode
            strategies: Strategies used
            key_decisions: Key decisions made

        Returns:
            Episode ID
        """
        # Generate episode ID
        episode_id = f"ep_{self.total_stored}_{int(time.time())}"

        # Create episode
        episode = Episode(
            episode_id=episode_id,
            episode_type=episode_type,
            problem=problem,
            reasoning_trace=reasoning_trace,
            outcome=outcome,
            strategies_used=strategies or [],
            key_decisions=key_decisions or []
        )

        # Compute embedding
        episode.embedding = self.embedder.embed(episode)

        # Store episode
        self.episodes[episode_id] = episode
        self.total_stored += 1

        # Update indices
        self.by_type[episode_type].append(episode_id)
        self.by_domain[problem.domain].append(episode_id)
        self.by_outcome[outcome.outcome_type].append(episode_id)
        self.by_problem_type[problem.problem_type].append(episode_id)

        # Find similar episodes
        similar = self._find_similar_internal(episode, k=5)
        episode.similar_episodes = [ep_id for ep_id, _ in similar]

        # Enforce max size
        if len(self.episodes) > self.max_episodes:
            self._evict_oldest()

        return episode_id

    def retrieve_similar(self, current_problem: Problem,
                        k: int = 5,
                        filters: Dict[str, Any] = None) -> List[Tuple[Episode, float]]:
        """
        Retrieve episodes similar to current problem.

        Args:
            current_problem: Problem to find similar episodes for
            k: Number of episodes to retrieve
            filters: Optional filters (domain, outcome_type, etc.)

        Returns:
            List of (episode, similarity_score) tuples
        """
        self.total_retrieved += 1

        # Get candidate episodes
        candidates = self._get_candidates(filters)

        if not candidates:
            return []

        # Embed current problem
        query_embedding = self.embedder.embed_problem(current_problem)

        # Score candidates
        scores = []
        for ep_id in candidates:
            episode = self.episodes[ep_id]
            similarity = self.embedder.similarity(query_embedding, episode.embedding)

            # Boost score for matching domain/type
            if episode.problem.domain == current_problem.domain:
                similarity += 0.1
            if episode.problem.problem_type == current_problem.problem_type:
                similarity += 0.1

            scores.append((episode, similarity))

        # Sort and return top k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def retrieve_by_outcome(self, outcome_type: OutcomeType,
                           k: int = 10) -> List[Episode]:
        """Retrieve episodes by outcome type"""
        ep_ids = self.by_outcome.get(outcome_type, [])[-k:]
        return [self.episodes[ep_id] for ep_id in ep_ids]

    def retrieve_successful(self, domain: str = None,
                           k: int = 10) -> List[Episode]:
        """Retrieve successful episodes, optionally filtered by domain"""
        successful = self.by_outcome.get(OutcomeType.SUCCESS, [])

        if domain:
            domain_eps = set(self.by_domain.get(domain, []))
            successful = [ep_id for ep_id in successful if ep_id in domain_eps]

        ep_ids = successful[-k:]
        return [self.episodes[ep_id] for ep_id in ep_ids]

    def extract_pattern(self, episodes: List[Episode]) -> Optional[Pattern]:
        """
        Extract a common pattern from a set of similar episodes.

        Args:
            episodes: Episodes to extract pattern from

        Returns:
            Extracted pattern or None
        """
        if len(episodes) < 2:
            return None

        # Find common elements
        common_actions = self._find_common_actions(episodes)
        common_strategies = self._find_common_strategies(episodes)

        if not common_actions and not common_strategies:
            return None

        # Compute success rate
        successes = sum(1 for ep in episodes
                       if ep.outcome.outcome_type == OutcomeType.SUCCESS)
        success_rate = successes / len(episodes)

        # Extract conditions (from problem features)
        conditions = self._extract_conditions(episodes)

        # Generate pattern ID
        pattern_id = f"pat_{len(self.patterns)}_{int(time.time())}"

        pattern = Pattern(
            pattern_id=pattern_id,
            pattern_type=episodes[0].episode_type.value,
            description=f"Pattern from {len(episodes)} episodes",
            frequency=len(episodes),
            success_rate=success_rate,
            episode_ids=[ep.episode_id for ep in episodes],
            conditions=conditions,
            actions=common_actions,
            expected_outcome="success" if success_rate > 0.7 else "uncertain"
        )

        self.patterns[pattern_id] = pattern
        return pattern

    def get_applicable_patterns(self, problem: Problem) -> List[Pattern]:
        """Get patterns that might apply to a problem"""
        applicable = []

        for pattern in self.patterns.values():
            if self._pattern_matches(pattern, problem):
                applicable.append(pattern)

        # Sort by success rate
        applicable.sort(key=lambda p: p.success_rate, reverse=True)
        return applicable

    def get_strategy_effectiveness(self, strategy: str,
                                    domain: str = None) -> Dict[str, float]:
        """Get effectiveness statistics for a strategy"""
        relevant_episodes = []

        for episode in self.episodes.values():
            if strategy in episode.strategies_used:
                if domain is None or episode.problem.domain == domain:
                    relevant_episodes.append(episode)

        if not relevant_episodes:
            return {'n_uses': 0, 'success_rate': 0.0, 'avg_confidence': 0.0}

        successes = sum(1 for ep in relevant_episodes
                       if ep.outcome.outcome_type == OutcomeType.SUCCESS)
        avg_confidence = np.mean([ep.outcome.confidence for ep in relevant_episodes])

        return {
            'n_uses': len(relevant_episodes),
            'success_rate': successes / len(relevant_episodes),
            'avg_confidence': float(avg_confidence),
            'domains': list(set(ep.problem.domain for ep in relevant_episodes))
        }

    def learn_from_failure(self, episode_id: str) -> Dict[str, Any]:
        """
        Analyze a failed episode to learn what went wrong.

        Returns:
            Analysis with failure patterns and suggestions
        """
        if episode_id not in self.episodes:
            return {'error': 'Episode not found'}

        episode = self.episodes[episode_id]

        if episode.outcome.outcome_type == OutcomeType.SUCCESS:
            return {'error': 'Episode was successful'}

        # Find similar successful episodes
        similar = self.retrieve_similar(episode.problem, k=5)
        successful_similar = [ep for ep, _ in similar
                            if ep.outcome.outcome_type == OutcomeType.SUCCESS]

        # Identify differences
        differences = []
        if successful_similar:
            ref_episode = successful_similar[0]

            # Compare strategies
            failed_strategies = set(episode.strategies_used)
            success_strategies = set(ref_episode.strategies_used)

            if failed_strategies != success_strategies:
                differences.append({
                    'aspect': 'strategies',
                    'failed_used': list(failed_strategies - success_strategies),
                    'success_used': list(success_strategies - failed_strategies)
                })

            # Compare step counts
            if episode.n_steps < ref_episode.n_steps * 0.5:
                differences.append({
                    'aspect': 'thoroughness',
                    'observation': 'Failed episode had significantly fewer steps'
                })

        return {
            'episode_id': episode_id,
            'errors': episode.outcome.errors,
            'similar_successful': len(successful_similar),
            'differences': differences,
            'suggestions': self._generate_suggestions(episode, successful_similar)
        }

    def _find_similar_internal(self, episode: Episode,
                               k: int = 5) -> List[Tuple[str, float]]:
        """Internal method to find similar episodes"""
        if episode.embedding is None:
            return []

        scores = []
        for ep_id, ep in self.episodes.items():
            if ep_id == episode.episode_id:
                continue
            if ep.embedding is not None:
                sim = self.embedder.similarity(episode.embedding, ep.embedding)
                scores.append((ep_id, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def _get_candidates(self, filters: Dict[str, Any] = None) -> List[str]:
        """Get candidate episode IDs based on filters"""
        if filters is None:
            return list(self.episodes.keys())

        candidates = set(self.episodes.keys())

        if 'domain' in filters:
            domain_eps = set(self.by_domain.get(filters['domain'], []))
            candidates &= domain_eps

        if 'outcome_type' in filters:
            outcome_eps = set(self.by_outcome.get(filters['outcome_type'], []))
            candidates &= outcome_eps

        if 'episode_type' in filters:
            type_eps = set(self.by_type.get(filters['episode_type'], []))
            candidates &= type_eps

        return list(candidates)

    def _find_common_actions(self, episodes: List[Episode]) -> List[str]:
        """Find actions common to all episodes"""
        if not episodes:
            return []

        action_counts: Dict[str, int] = defaultdict(int)
        for episode in episodes:
            episode_actions = set(step.action for step in episode.reasoning_trace)
            for action in episode_actions:
                action_counts[action] += 1

        # Return actions present in majority of episodes
        threshold = len(episodes) * 0.6
        return [action for action, count in action_counts.items()
                if count >= threshold]

    def _find_common_strategies(self, episodes: List[Episode]) -> List[str]:
        """Find strategies common to episodes"""
        if not episodes:
            return []

        strategy_counts: Dict[str, int] = defaultdict(int)
        for episode in episodes:
            for strategy in episode.strategies_used:
                strategy_counts[strategy] += 1

        threshold = len(episodes) * 0.6
        return [strategy for strategy, count in strategy_counts.items()
                if count >= threshold]

    def _extract_conditions(self, episodes: List[Episode]) -> List[str]:
        """Extract common conditions from episodes"""
        conditions = []

        # Check domain consistency
        domains = set(ep.problem.domain for ep in episodes)
        if len(domains) == 1:
            conditions.append(f"domain == '{list(domains)[0]}'")

        # Check problem type consistency
        types = set(ep.problem.problem_type for ep in episodes)
        if len(types) == 1:
            conditions.append(f"problem_type == '{list(types)[0]}'")

        # Check difficulty range
        difficulties = [ep.problem.difficulty for ep in episodes]
        if max(difficulties) - min(difficulties) < 0.3:
            avg_diff = np.mean(difficulties)
            conditions.append(f"difficulty ~= {avg_diff:.2f}")

        return conditions

    def _pattern_matches(self, pattern: Pattern, problem: Problem) -> bool:
        """Check if pattern conditions match problem"""
        for condition in pattern.conditions:
            if 'domain ==' in condition:
                domain = condition.split("'")[1]
                if problem.domain != domain:
                    return False

            if 'problem_type ==' in condition:
                ptype = condition.split("'")[1]
                if problem.problem_type != ptype:
                    return False

        return True

    def _generate_suggestions(self, failed_episode: Episode,
                              successful_episodes: List[Episode]) -> List[str]:
        """Generate suggestions based on comparison"""
        suggestions = []

        if not successful_episodes:
            suggestions.append("No similar successful episodes found - try a different approach")
            return suggestions

        ref = successful_episodes[0]

        # Strategy suggestions
        for strategy in ref.strategies_used:
            if strategy not in failed_episode.strategies_used:
                suggestions.append(f"Try using strategy: {strategy}")

        # Step suggestions
        ref_actions = set(s.action for s in ref.reasoning_trace)
        failed_actions = set(s.action for s in failed_episode.reasoning_trace)

        missing_actions = ref_actions - failed_actions
        for action in list(missing_actions)[:3]:
            suggestions.append(f"Consider action: {action}")

        return suggestions

    def _evict_oldest(self, n: int = 100):
        """Evict oldest episodes to make room"""
        # Sort by timestamp
        sorted_eps = sorted(self.episodes.items(),
                           key=lambda x: x[1].timestamp)

        # Remove oldest n
        for ep_id, _ in sorted_eps[:n]:
            self._remove_episode(ep_id)

    def _remove_episode(self, episode_id: str):
        """Remove an episode from all indices"""
        if episode_id not in self.episodes:
            return

        episode = self.episodes[episode_id]

        # Remove from indices
        self.by_type[episode.episode_type].remove(episode_id)
        self.by_domain[episode.problem.domain].remove(episode_id)
        self.by_outcome[episode.outcome.outcome_type].remove(episode_id)
        self.by_problem_type[episode.problem.problem_type].remove(episode_id)

        del self.episodes[episode_id]

    def stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            'total_episodes': len(self.episodes),
            'total_stored': self.total_stored,
            'total_retrieved': self.total_retrieved,
            'n_patterns': len(self.patterns),
            'by_type': {t.value: len(eps) for t, eps in self.by_type.items()},
            'by_outcome': {o.value: len(eps) for o, eps in self.by_outcome.items()},
            'domains': list(self.by_domain.keys()),
            'success_rate': len(self.by_outcome.get(OutcomeType.SUCCESS, [])) /
                           max(1, len(self.episodes))
        }

    def to_dict(self) -> Dict:
        """Serialize memory state"""
        return {
            'episodes': {ep_id: ep.to_dict()
                        for ep_id, ep in self.episodes.items()},
            'patterns': {p_id: p.to_dict()
                        for p_id, p in self.patterns.items()},
            'stats': self.stats()
        }

    def save(self, filepath: str):
        """Save memory to file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'EpisodicMemory':
        """Load memory from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        memory = cls()

        # Reconstruct episodes (simplified - would need full reconstruction)
        # This is a placeholder for proper serialization
        return memory


class CasedBasedReasoner:
    """
    Case-based reasoning using episodic memory.

    Retrieves relevant past cases and adapts solutions.
    """

    def __init__(self, episodic_memory: EpisodicMemory):
        self.memory = episodic_memory
        self.adaptation_strategies: Dict[str, Callable] = {}

    def register_adaptation_strategy(self, name: str, strategy: Callable):
        """Register a strategy for adapting solutions"""
        self.adaptation_strategies[name] = strategy

    def solve_by_analogy(self, problem: Problem,
                         k: int = 3) -> Dict[str, Any]:
        """
        Solve a problem by analogy to past cases.

        Args:
            problem: Current problem to solve
            k: Number of cases to retrieve

        Returns:
            Solution proposal with reasoning
        """
        # Retrieve similar cases
        similar_cases = self.memory.retrieve_similar(problem, k=k)

        if not similar_cases:
            return {
                'success': False,
                'reason': 'No similar cases found',
                'suggestion': 'Try novel approach'
            }

        # Analyze retrieved cases
        successful_cases = [
            (ep, sim) for ep, sim in similar_cases
            if ep.outcome.outcome_type == OutcomeType.SUCCESS
        ]

        if not successful_cases:
            # Learn from failures
            return {
                'success': False,
                'reason': 'Similar cases failed',
                'cases': [ep.to_dict() for ep, _ in similar_cases],
                'lessons': self._extract_failure_lessons(similar_cases)
            }

        # Get best case
        best_case, similarity = successful_cases[0]

        # Adapt solution
        adapted_solution = self._adapt_solution(best_case, problem)

        return {
            'success': True,
            'source_case': best_case.episode_id,
            'similarity': similarity,
            'original_solution': best_case.outcome.solution,
            'adapted_solution': adapted_solution,
            'reasoning_template': [s.to_dict() for s in best_case.reasoning_trace],
            'confidence': similarity * best_case.outcome.confidence
        }

    def _adapt_solution(self, source_case: Episode,
                        target_problem: Problem) -> Any:
        """Adapt a solution from source case to target problem"""
        # Identify differences
        source_inputs = source_case.problem.inputs
        target_inputs = target_problem.inputs
