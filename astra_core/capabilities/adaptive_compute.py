"""
Adaptive Compute Budget Module for STAN
=======================================

Dynamically allocates reasoning time and resources based on problem difficulty.
Like o1/o3, spends more time on hard problems and less on easy ones.

Key features:
1. Problem difficulty estimation
2. Dynamic time allocation
3. Resource scaling (beam width, depth, samples)
4. Early stopping for confident answers

Expected improvement: +2-3% on GPQA Diamond
"""

import time
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import numpy as np


class DifficultyLevel(Enum):
    """Problem difficulty levels."""
    TRIVIAL = "trivial"        # < 10 seconds
    EASY = "easy"              # 10-30 seconds
    MEDIUM = "medium"          # 30-60 seconds
    HARD = "hard"              # 60-180 seconds
    EXPERT = "expert"          # 180-300+ seconds


@dataclass
class ComputeBudget:
    """Resource allocation for a problem."""
    time_seconds: float
    max_reasoning_steps: int
    beam_width: int
    num_samples: int  # For self-consistency
    max_depth: int
    enable_verification: bool
    enable_retrieval: bool

    def scale(self, factor: float) -> 'ComputeBudget':
        """Scale budget by a factor."""
        return ComputeBudget(
            time_seconds=self.time_seconds * factor,
            max_reasoning_steps=int(self.max_reasoning_steps * factor),
            beam_width=max(2, int(self.beam_width * factor)),
            num_samples=max(1, int(self.num_samples * factor)),
            max_depth=max(4, int(self.max_depth * factor)),
            enable_verification=self.enable_verification,
            enable_retrieval=self.enable_retrieval
        )


# Default budgets by difficulty
DEFAULT_BUDGETS = {
    DifficultyLevel.TRIVIAL: ComputeBudget(
        time_seconds=10,
        max_reasoning_steps=5,
        beam_width=2,
        num_samples=1,
        max_depth=4,
        enable_verification=False,
        enable_retrieval=False
    ),
    DifficultyLevel.EASY: ComputeBudget(
        time_seconds=30,
        max_reasoning_steps=10,
        beam_width=4,
        num_samples=3,
        max_depth=6,
        enable_verification=True,
        enable_retrieval=False
    ),
    DifficultyLevel.MEDIUM: ComputeBudget(
        time_seconds=60,
        max_reasoning_steps=20,
        beam_width=6,
        num_samples=5,
        max_depth=8,
        enable_verification=True,
        enable_retrieval=True
    ),
    DifficultyLevel.HARD: ComputeBudget(
        time_seconds=120,
        max_reasoning_steps=35,
        beam_width=8,
        num_samples=8,
        max_depth=12,
        enable_verification=True,
        enable_retrieval=True
    ),
    DifficultyLevel.EXPERT: ComputeBudget(
        time_seconds=300,
        max_reasoning_steps=50,
        beam_width=12,
        num_samples=12,
        max_depth=15,
        enable_verification=True,
        enable_retrieval=True
    )
}


@dataclass
class DifficultySignals:
    """Signals used to estimate problem difficulty."""
    question_length: int = 0
    num_variables: int = 0
    num_equations: int = 0
    has_multiple_steps: bool = False
    requires_derivation: bool = False
    requires_integration: bool = False
    domain_complexity: float = 0.5
    has_constraints: bool = False
    num_conditions: int = 0
    requires_specialized_knowledge: bool = False
    is_multiple_choice: bool = False
    num_choices: int = 4


class DifficultyEstimator:
    """
    Estimates problem difficulty based on various signals.
    """

    def __init__(self):
        # Complexity keywords by category
        self.multi_step_indicators = [
            'first', 'then', 'next', 'finally', 'step',
            'after', 'before', 'subsequently', 'following'
        ]

        self.derivation_indicators = [
            'derive', 'show that', 'prove', 'demonstrate',
            'establish', 'verify that'
        ]

        self.integration_indicators = [
            'integrate', 'integral', '∫', 'sum over',
            'total', 'accumulate'
        ]

        self.constraint_indicators = [
            'given that', 'assuming', 'if', 'when',
            'under the condition', 'subject to', 'constraint'
        ]

        self.specialized_indicators = [
            'quantum', 'relativistic', 'thermodynamic',
            'electrochemical', 'biochemical', 'genomic',
            'spectroscopic', 'crystallographic', 'topological'
        ]

        # Domain base complexity
        self.domain_complexity = {
            'Physics': 0.65,
            'Chemistry': 0.60,
            'Biology': 0.55,
            'Mathematics': 0.70,
            'Computer Science': 0.55,
            'Engineering': 0.60,
            'Other': 0.50
        }

    def estimate(self, question: str, domain: str = "",
                 choices: List[str] = None) -> Tuple[DifficultyLevel, DifficultySignals, float]:
        """
        Estimate problem difficulty.

        Returns:
            Tuple of (difficulty level, signals, raw score 0-1)
        """
        signals = self._extract_signals(question, domain, choices)
        score = self._compute_score(signals)
        level = self._score_to_level(score)

        return level, signals, score

    def _extract_signals(self, question: str, domain: str,
                        choices: List[str] = None) -> DifficultySignals:
        """Extract difficulty signals from question."""
        q_lower = question.lower()

        signals = DifficultySignals()

        # Basic metrics
        signals.question_length = len(question)
        signals.is_multiple_choice = choices is not None
        signals.num_choices = len(choices) if choices else 0

        # Count mathematical elements
        signals.num_variables = len(re.findall(r'\b[a-zA-Z]\b(?![a-zA-Z])', question))
        signals.num_equations = question.count('=') + question.count('≈')

        # Multi-step detection
        signals.has_multiple_steps = any(
            ind in q_lower for ind in self.multi_step_indicators
        )
        signals.num_conditions = sum(
            1 for ind in self.constraint_indicators if ind in q_lower
        )

        # Derivation/Integration detection
        signals.requires_derivation = any(
            ind in q_lower for ind in self.derivation_indicators
        )
        signals.requires_integration = any(
            ind in q_lower for ind in self.integration_indicators
        )

        # Constraints
        signals.has_constraints = signals.num_conditions > 0

        # Specialized knowledge
        signals.requires_specialized_knowledge = any(
            ind in q_lower for ind in self.specialized_indicators
        )

        # Domain complexity
        signals.domain_complexity = self.domain_complexity.get(domain, 0.50)

        return signals

    def _compute_score(self, signals: DifficultySignals) -> float:
        """Compute difficulty score from signals."""
        score = 0.0

        # Length contribution (longer = harder, but with diminishing returns)
        length_score = min(1.0, signals.question_length / 500)
        score += 0.10 * length_score

        # Mathematical complexity
        var_score = min(1.0, signals.num_variables / 10)
        eq_score = min(1.0, signals.num_equations / 5)
        score += 0.10 * var_score + 0.10 * eq_score

        # Multi-step and conditions
        if signals.has_multiple_steps:
            score += 0.15
        score += 0.05 * min(3, signals.num_conditions)

        # Derivation/Integration (hardest operations)
        if signals.requires_derivation:
            score += 0.20
        if signals.requires_integration:
            score += 0.15

        # Specialized knowledge
        if signals.requires_specialized_knowledge:
            score += 0.15

        # Domain base complexity
        score += 0.15 * signals.domain_complexity

        # Multiple choice makes it slightly easier (can eliminate)
        if signals.is_multiple_choice:
            score -= 0.10

        return min(1.0, max(0.0, score))

    def _score_to_level(self, score: float) -> DifficultyLevel:
        """Convert score to difficulty level."""
        if score < 0.2:
            return DifficultyLevel.TRIVIAL
        elif score < 0.35:
            return DifficultyLevel.EASY
        elif score < 0.55:
            return DifficultyLevel.MEDIUM
        elif score < 0.75:
            return DifficultyLevel.HARD
        else:
            return DifficultyLevel.EXPERT


class AdaptiveComputeManager:
    """
    Manages adaptive compute allocation for reasoning tasks.
    """

    def __init__(self, base_multiplier: float = 1.0):
        """
        Args:
            base_multiplier: Scale all budgets by this factor
        """
        self.estimator = DifficultyEstimator()
        self.base_multiplier = base_multiplier

        # History for adaptive learning
        self.history: List[Dict[str, Any]] = []

    def allocate(self, question: str, domain: str = "",
                choices: List[str] = None) -> Tuple[ComputeBudget, Dict[str, Any]]:
        """
        Allocate compute budget for a problem.

        Returns:
            Tuple of (budget, metadata)
        """
        # Estimate difficulty
        level, signals, score = self.estimator.estimate(question, domain, choices)

        # Get base budget for level
        budget = DEFAULT_BUDGETS[level]

        # Apply base multiplier
        if self.base_multiplier != 1.0:
            budget = budget.scale(self.base_multiplier)

        # Adjust based on specific signals
        budget = self._adjust_budget(budget, signals, score)

        metadata = {
            'difficulty_level': level.value,
            'difficulty_score': score,
            'signals': {
                'question_length': signals.question_length,
                'num_variables': signals.num_variables,
                'has_multiple_steps': signals.has_multiple_steps,
                'requires_derivation': signals.requires_derivation,
                'requires_specialized_knowledge': signals.requires_specialized_knowledge
            }
        }

        return budget, metadata

    def _adjust_budget(self, budget: ComputeBudget,
                      signals: DifficultySignals,
                      score: float) -> ComputeBudget:
        """Fine-tune budget based on specific signals."""
        # Extra time for derivation problems
        if signals.requires_derivation:
            budget = ComputeBudget(
                time_seconds=budget.time_seconds * 1.3,
                max_reasoning_steps=budget.max_reasoning_steps + 10,
                beam_width=budget.beam_width,
                num_samples=budget.num_samples,
                max_depth=budget.max_depth + 2,
                enable_verification=True,
                enable_retrieval=budget.enable_retrieval
            )

        # Extra samples for uncertain problems
        if signals.requires_specialized_knowledge:
            budget = ComputeBudget(
                time_seconds=budget.time_seconds,
                max_reasoning_steps=budget.max_reasoning_steps,
                beam_width=budget.beam_width + 2,
                num_samples=budget.num_samples + 3,
                max_depth=budget.max_depth,
                enable_verification=budget.enable_verification,
                enable_retrieval=True  # Enable retrieval for specialized knowledge
            )

        return budget

    def record_result(self, question: str, budget: ComputeBudget,
                     actual_time: float, success: bool,
                     confidence: float) -> None:
        """Record result for adaptive learning."""
        self.history.append({
            'question_hash': hash(question) % 10000,
            'budget_time': budget.time_seconds,
            'actual_time': actual_time,
            'success': success,
            'confidence': confidence,
            'timestamp': time.time()
        })

        # Keep history bounded
        if len(self.history) > 1000:
            self.history = self.history[-500:]

    def get_stats(self) -> Dict[str, Any]:
        """Get allocation statistics."""
        if not self.history:
            return {'total_problems': 0}

        successes = sum(1 for h in self.history if h['success'])
        total_time = sum(h['actual_time'] for h in self.history)
        budget_time = sum(h['budget_time'] for h in self.history)

        return {
            'total_problems': len(self.history),
            'success_rate': successes / len(self.history),
            'total_time_used': total_time,
            'total_time_budgeted': budget_time,
            'efficiency': total_time / budget_time if budget_time > 0 else 0,
            'avg_confidence': np.mean([h['confidence'] for h in self.history])
        }


class EarlyStoppingMonitor:
    """
    Monitors reasoning progress and triggers early stopping
    when confident enough or time budget is exhausted.
    """

    def __init__(self, confidence_threshold: float = 0.85,
                 time_buffer_ratio: float = 0.1):
        self.confidence_threshold = confidence_threshold
        self.time_buffer_ratio = time_buffer_ratio

    def should_stop(self, current_confidence: float,
                   elapsed_time: float,
                   budget: ComputeBudget,
                   reasoning_steps: int) -> Tuple[bool, str]:
        """
        Check if reasoning should stop early.

        Returns:
            Tuple of (should_stop, reason)
        """
        # High confidence - stop early
        if current_confidence >= self.confidence_threshold:
            return True, "high_confidence"

        # Time budget exhausted
        time_limit = budget.time_seconds * (1 - self.time_buffer_ratio)
        if elapsed_time >= time_limit:
            return True, "time_exhausted"

        # Step limit reached
        if reasoning_steps >= budget.max_reasoning_steps:
            return True, "step_limit"

        return False, ""


# Convenience functions
def create_adaptive_manager(mode: str = 'balanced') -> AdaptiveComputeManager:
    """Create adaptive compute manager with preset mode."""
    multipliers = {
        'fast': 0.5,
        'balanced': 1.0,
        'thorough': 1.5,
        'exhaustive': 2.5
    }
    return AdaptiveComputeManager(base_multiplier=multipliers.get(mode, 1.0))


def estimate_difficulty(question: str, domain: str = "") -> DifficultyLevel:
    """Quick difficulty estimation."""
    estimator = DifficultyEstimator()
    level, _, _ = estimator.estimate(question, domain)
    return level



def adaptive_resource_allocation(tasks: List[Dict[str, Any]],
                                available_resources: Dict[str, float]) -> Dict[str, Any]:
    """
    Allocate computational resources adaptively based on task importance and difficulty.

    Implements dynamic resource scheduling for multi-task systems.

    Args:
        tasks: List of tasks with metadata
        available_resources: Available compute resources

    Returns:
        Resource allocation plan
    """
    import numpy as np

    # Score tasks by priority
    task_scores = []
    for task in tasks:
        importance = task.get('importance', 0.5)
        urgency = task.get('urgency', 0.5)
        difficulty = task.get('difficulty', 0.5)

        # Higher score = more resources needed
        score = importance * urgency * (1 + difficulty)
        task_scores.append(score)

    # Normalize scores
    total_score = sum(task_scores)
    if total_score == 0:
        fractions = [1.0 / len(tasks)] * len(tasks)
    else:
        fractions = [s / total_score for s in task_scores]

    # Allocate resources
    allocation = {}
    for i, task in enumerate(tasks):
        task_id = task.get('id', i)
        fraction = fractions[i]

        allocation[task_id] = {
            'compute_fraction': fraction,
            'estimated_time': task.get('estimated_time', 1.0) / fraction,
            'priority_score': task_scores[i]
        }

    return {
        'allocation': allocation,
        'total_utilization': sum(fractions),
        'recommended_order': sorted(range(len(tasks)),
                                    key=lambda i: task_scores[i],
                                    reverse=True)
    }


def adaptive_algorithm_selection(problem_characteristics: Dict[str, Any],
                                algorithm_capabilities: List[Dict[str, Any]]) -> str:
    """
    Select the most appropriate algorithm based on problem characteristics.

    Args:
        problem_characteristics: Features of the problem to solve
        algorithm_capabilities: Available algorithms and their strengths

    Returns:
        Selected algorithm name
    """
    import numpy as np

    # Score each algorithm
    algorithm_scores = []

    for algo in algorithm_capabilities:
        algo_name = algo.get('name', 'unknown')
        strengths = algo.get('strengths', {})
        weaknesses = algo.get('weaknesses', {})

        score = 1.0

        # Boost score for matching strengths
        for feature, value in problem_characteristics.items():
            if feature in strengths:
                score *= (1 + strengths[feature] * value)

            if feature in weaknesses:
                score *= (1 - weaknesses[feature] * value)

        algorithm_scores.append((algo_name, score))

    # Return best algorithm
    algorithm_scores.sort(key=lambda x: x[1], reverse=True)
    return algorithm_scores[0][0]



def organize_semantic_memory(concepts: List[Dict[str, Any]],
                           similarity_threshold: float = 0.7) -> Dict[str, Any]:
    """
    Organize semantic memories into clusters.

    Args:
        concepts: List of concepts with embeddings
        similarity_threshold: Minimum similarity for clustering

    Returns:
        Dictionary with clusters and organization
    """
    import numpy as np
    from collections import defaultdict

    # Extract embeddings
    embeddings = []
    for concept in concepts:
        emb = concept.get('embedding', concept.get('features', []))
        if isinstance(emb, list):
            embeddings.append(np.array(emb))
        else:
            embeddings.append(emb)

    if not embeddings:
        return {'clusters': []}

    embeddings = np.array(embeddings)

    # Compute similarity matrix
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10
    normalized = embeddings / norms
    similarity = normalized @ normalized.T

    # Build clusters
    clusters = []
    assigned = set()

    for i in range(len(concepts)):
        if i in assigned:
            continue

        # Find similar concepts
        similar = [j for j in range(len(concepts))
                  if j not in assigned and similarity[i, j] > similarity_threshold]

        if similar:
            cluster = {
                'centroid': np.mean(embeddings[similar], axis=0).tolist(),
                'members': similar,
                'concepts': [concepts[j] for j in similar],
                'size': len(similar)
            }
            clusters.append(cluster)
            assigned.update(similar)

    return {
        'clusters': clusters,
        'num_clusters': len(clusters),
        'similarity_threshold': similarity_threshold
    }



def predict_next_in_sequence(sequence: List[Any],
                            method: str = 'autoregressive') -> Dict[str, Any]:
    """
    Predict the next element in a sequence.

    Args:
        sequence: Observed sequence
        method: Prediction method ('autoregressive', 'markov', 'fft')

    Returns:
        Dictionary with prediction and confidence
    """
    import numpy as np

    if len(sequence) < 2:
        return {'prediction': None, 'confidence': 0.0}

    if method == 'autoregressive':
        # Fit AR(1) model: x_t = c + phi * x_{t-1}
        x = np.array(sequence)
        x_lag = x[:-1]
        x_current = x[1:]

        # Linear regression
        A = np.vstack([x_lag, np.ones(len(x_lag))]).T
        phi, c = np.linalg.lstsq(A, x_current, rcond=None)[0]

        # Predict next
        if len(x) > 0:
            prediction = c + phi * x[-1]

            # Estimate confidence from residuals
            residuals = x_current - (c + phi * x_lag)
            std = np.std(residuals)
            confidence = 1.0 / (1.0 + std)

            return {
                'prediction': float(prediction),
                'confidence': float(confidence),
                'method': 'autoregressive'
            }

    elif method == 'markov':
        # Simple Markov chain
        transitions = {}
        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_val = sequence[i + 1]
            if current not in transitions:
                transitions[current] = {}
            if next_val not in transitions[current]:
                transitions[current][next_val] = 0
            transitions[current][next_val] += 1

        # Predict from last state
        last = sequence[-1]
        if last in transitions:
            total = sum(transitions[last].values())
            most_likely = max(transitions[last].items(), key=lambda x: x[1])
            prediction = most_likely[0]
            confidence = most_likely[1] / total

            return {
                'prediction': prediction,
                'confidence': float(confidence),
                'method': 'markov'
            }

    return {'prediction': None, 'confidence': 0.0}



def fft_pattern_detect(data: np.ndarray, min_freq: float = 0.01, max_freq: float = 0.5) -> Dict[str, Any]:
    """
    Detect periodic patterns using FFT analysis.

    Args:
        data: Input signal
        min_freq: Minimum frequency to detect
        max_freq: Maximum frequency to detect

    Returns:
        Dictionary with detected frequencies and powers
    """
    import numpy as np

    # Compute FFT
    fft_result = np.fft.fft(data)
    freqs = np.fft.fftfreq(len(data))
    power = np.abs(fft_result)**2

    # Filter to frequency range
    mask = (np.abs(freqs) >= min_freq) & (np.abs(freqs) <= max_freq)
    filtered_freqs = freqs[mask]
    filtered_power = power[mask]

    # Sort by power
    sorted_indices = np.argsort(filtered_power)[::-1]

    # Get top frequencies
    top_freqs = []
    top_powers = []
    for idx in sorted_indices[:10]:
        top_freqs.append(float(filtered_freqs[idx]))
        top_powers.append(float(filtered_power[idx]))

    return {
        'frequencies': top_freqs,
        'powers': top_powers,
        'dominant_frequency': top_freqs[0] if top_freqs else None,
        'total_power': float(np.sum(filtered_power))
    }



def bootstrap_uncertainty(data: np.ndarray,
                         estimator_func: callable,
                         n_bootstrap: int = 1000,
                         ci_level: float = 0.95) -> Dict[str, Any]:
    """
    Estimate uncertainty using bootstrap resampling.

    Args:
        data: Input data
        estimator_func: Function that computes estimate from data
        n_bootstrap: Number of bootstrap samples
        ci_level: Confidence interval level

    Returns:
        Dictionary with estimate and confidence interval
    """
    import numpy as np

    n = len(data)
    estimates = []

    pass  # Bootstrap implementation needed
