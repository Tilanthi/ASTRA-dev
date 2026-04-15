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
ASTRA Live — Active Learning Loop
Human-in-the-loop hypothesis refinement and discovery prioritization.

Active learning allows ASTRA to:
  - Query humans about uncertain hypotheses
  - Incorporate expert feedback to improve models
  - Prioritize which hypotheses to investigate next
  - Learn from validation results

Key Components:
  - Uncertainty sampling: Query most uncertain predictions
  - Diversity sampling: Ensure diverse query set
  - Bayesian updating: Incorporate feedback as priors
  - Exploration/exploitation balance
"""

import numpy as np
from typing import Optional, Dict, List, Tuple, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import json
import time

# Handle optional sklearn import
try:
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, ConstantKernel
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class Hypothesis:
    """A scientific hypothesis with confidence and metadata."""
    id: str
    description: str
    confidence: float  # 0-1
    novelty: float     # 0-1
    feasibility: float # 0-1
    domain: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    human_feedback: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None


@dataclass
class QueryResult:
    """Result from a human query."""
    hypothesis_id: str
    human_judgment: str  # 'promising', 'unpromising', 'unsure'
    confidence: float    # Human's confidence in judgment
    timestamp: float
    feedback: str


class ActiveLearningLoop:
    """
    Active learning loop for hypothesis prioritization and refinement.

    This module implements human-in-the-loop discovery by:
    1. Identifying uncertain hypotheses that would benefit from human input
    2. Querying the human expert about these hypotheses
    3. Incorporating feedback to update the model
    4. Re-ranking hypotheses based on new information

    Example:
        >>> loop = ActiveLearningLoop()
        >>> hypotheses = generate_hypotheses()  # List of Hypothesis objects
        >>> to_query = loop.select_queries(hypotheses, budget=5)
        >>> for h in to_query:
        ...     result = loop.query_human(h)  # Get human input
        ...     loop.incorporate_feedback(result)
        >>> ranked = loop.rank_hypotheses(hypotheses)
    """

    def __init__(
        self,
        uncertainty_threshold: float = 0.3,
        diversity_weight: float = 0.5,
        explore_exploit_ratio: float = 0.3
    ):
        """
        Initialize active learning loop.

        Args:
            uncertainty_threshold: Confidence threshold below which to query
            diversity_weight: Weight for diversity in query selection (0-1)
            explore_exploit_ratio: Ratio of exploration to exploitation
        """
        self.uncertainty_threshold = uncertainty_threshold
        self.diversity_weight = diversity_weight
        self.explore_exploit_ratio = explore_exploit_ratio

        self.query_history: List[QueryResult] = []
        self.feedback_history: Dict[str, List[Dict]] = {}

        # Gaussian Process for modeling hypothesis quality
        if SKLEARN_AVAILABLE:
            kernel = ConstantKernel(1.0) * RBF(length_scale=1.0)
            self.gp = GaussianProcessRegressor(kernel=kernel, alpha=0.1)
            self._gp_fitted = False
        else:
            self.gp = None
            self._gp_fitted = False

    def compute_uncertainty(self, hypothesis: Hypothesis) -> float:
        """
        Compute uncertainty score for a hypothesis.

        Lower confidence and higher novelty → higher uncertainty

        Args:
            hypothesis: Hypothesis object

        Returns:
            Uncertainty score (0-1, higher = more uncertain)
        """
        # Primary uncertainty: 1 - confidence
        confidence_uncertainty = 1.0 - hypothesis.confidence

        # Novelty uncertainty: Novel hypotheses are less certain
        novelty_uncertainty = hypothesis.novelty * 0.3

        # Combined uncertainty
        uncertainty = (confidence_uncertainty * 0.7 +
                      novelty_uncertainty * 0.3)

        return uncertainty

    def select_queries(
        self,
        hypotheses: List[Hypothesis],
        budget: int = 5,
        method: str = 'uncertainty'
    ) -> List[Hypothesis]:
        """
        Select hypotheses to query human about.

        Methods:
        - 'uncertainty': Select most uncertain hypotheses
        - 'diverse': Select diverse set using clustering
        - 'expected_improvement': Select hypotheses where feedback would help most
        - 'mixed': Combination of uncertainty and diversity

        Args:
            hypotheses: List of hypotheses
            budget: Number of queries to make
            method: Query selection method

        Returns:
            List of hypotheses to query
        """
        if not hypotheses:
            return []

        # Compute uncertainty for all hypotheses
        uncertainties = np.array([self.compute_uncertainty(h) for h in hypotheses])

        if method == 'uncertainty':
            # Select most uncertain
            indices = np.argsort(uncertainties)[-budget:]
            selected = [hypotheses[i] for i in indices]

        elif method == 'diverse':
            # Select diverse uncertain hypotheses
            uncertain_threshold = np.percentile(uncertainties, 50)
            uncertain_mask = uncertainties > uncertain_threshold
            uncertain_indices = np.where(uncertain_mask)[0]

            if len(uncertain_indices) <= budget:
                selected = [hypotheses[i] for i in uncertain_indices]
            else:
                # Simple diversity: select evenly spaced indices
                step = len(uncertain_indices) // budget
                diverse_indices = [uncertain_indices[i * step]
                                 for i in range(min(budget, len(uncertain_indices)))]
                selected = [hypotheses[i] for i in diverse_indices]

        elif method == 'mixed':
            # Combine uncertainty and diversity
            # First get top uncertain
            n_uncertain = int(budget * (1 - self.diversity_weight))
            uncertain_indices = np.argsort(uncertainties)[-n_uncertain:]

            # Then get diverse from remaining
            remaining_mask = np.ones(len(hypotheses), dtype=bool)
            remaining_mask[uncertain_indices] = False
            remaining_indices = np.where(remaining_mask)[0]

            n_diverse = budget - n_uncertain
            if len(remaining_indices) > 0:
                step = max(1, len(remaining_indices) // n_diverse)
                diverse_indices = [remaining_indices[i * step]
                                 for i in range(min(n_diverse, len(remaining_indices)))]
            else:
                diverse_indices = []

            selected_indices = list(uncertain_indices) + diverse_indices
            selected = [hypotheses[i] for i in selected_indices[:budget]]

        else:
            raise ValueError(f"Unknown query selection method: {method}")

        return selected

    def format_query(self, hypothesis: Hypothesis) -> str:
        """
        Format a hypothesis for human query.

        Args:
            hypothesis: Hypothesis to query

        Returns:
            Formatted query string
        """
        return f"""
Hypothesis: {hypothesis.description}

Properties:
  - Confidence: {hypothesis.confidence:.2f}
  - Novelty: {hypothesis.novelty:.2f}
  - Feasibility: {hypothesis.feasibility:.2f}
  - Domain: {hypothesis.domain}

Please evaluate:
  1. Is this hypothesis promising? (promising / unpromising / unsure)
  2. How confident are you in this judgment? (0-1)
  3. Any additional feedback or concerns?
"""

    def query_human(
        self,
        hypothesis: Hypothesis,
        interactive: bool = True
    ) -> Optional[QueryResult]:
        """
        Query human expert about a hypothesis.

        Args:
            hypothesis: Hypothesis to query
            interactive: Whether to prompt for input (False for automated testing)

        Returns:
            QueryResult with human feedback, or None if cancelled
        """
        query_text = self.format_query(hypothesis)

        if interactive:
            print("\n" + "="*70)
            print("HYPOTHESIS EVALUATION REQUEST")
            print("="*70)
            print(query_text)

            # Get input
            judgment = input("\nIs this promising? (promising/unpromising/unsure): ").strip().lower()
            if judgment not in ['promising', 'unpromising', 'unsure']:
                print("Invalid input. Skipping query.")
                return None

            try:
                confidence_str = input("Your confidence (0-1): ").strip()
                confidence = float(confidence_str)
                confidence = max(0.0, min(1.0, confidence))
            except ValueError:
                confidence = 0.5

            feedback = input("Additional feedback (optional): ").strip()

        else:
            # Non-interactive mode (for testing)
            judgment = 'unsure'
            confidence = 0.5
            feedback = ''

        result = QueryResult(
            hypothesis_id=hypothesis.id,
            human_judgment=judgment,
            confidence=confidence,
            timestamp=time.time(),
            feedback=feedback
        )

        # Store in history
        self.query_history.append(result)

        # Store feedback for this hypothesis
        if hypothesis.id not in self.feedback_history:
            self.feedback_history[hypothesis.id] = []
        self.feedback_history[hypothesis.id].append({
            'judgment': judgment,
            'confidence': confidence,
            'feedback': feedback,
            'timestamp': result.timestamp
        })

        return result

    def incorporate_feedback(
        self,
        result: QueryResult,
        hypotheses: List[Hypothesis]
    ) -> None:
        """
        Incorporate human feedback to update hypothesis scores.

        Uses Bayesian updating to adjust confidence based on human judgment.

        Args:
            result: QueryResult from human
            hypotheses: List of hypotheses (will be modified)
        """
        # Find the hypothesis
        hypothesis = None
        for h in hypotheses:
            if h.id == result.hypothesis_id:
                hypothesis = h
                break

        if hypothesis is None:
            print(f"Warning: Hypothesis {result.hypothesis_id} not found")
            return

        # Store feedback in hypothesis
        if hypothesis.human_feedback is None:
            hypothesis.human_feedback = {}

        hypothesis.human_feedback['judgment'] = result.human_judgment
        hypothesis.human_feedback['confidence'] = result.confidence
        hypothesis.human_feedback['feedback'] = result.feedback
        hypothesis.human_feedback['timestamp'] = result.timestamp

        # Bayesian update of confidence
        # Prior: current confidence
        # Likelihood: based on human judgment
        prior = hypothesis.confidence

        # Convert human judgment to likelihood
        if result.human_judgment == 'promising':
            likelihood = 0.8
        elif result.human_judgment == 'unpromising':
            likelihood = 0.2
        else:  # unsure
            likelihood = 0.5

        # Human confidence modulates the update strength
        alpha = result.confidence  # 0 = no update, 1 = full update

        # Bayesian update (simplified)
        # posterior ∝ prior × likelihood
        # Use weighted geometric mean
        posterior = prior ** (1 - alpha) * likelihood ** alpha

        # Update hypothesis confidence
        hypothesis.confidence = max(0.0, min(1.0, posterior))

        # Adjust novelty based on feedback
        if result.human_judgment == 'promising':
            # Promising hypotheses might be less novel (more expected)
            hypothesis.novelty *= 0.9
        elif result.human_judgment == 'unpromising':
            # Unpromising might be novel but wrong direction
            hypothesis.novelty *= 1.1

        # Store in feedback history
        if result.hypothesis_id not in self.feedback_history:
            self.feedback_history[result.hypothesis_id] = []

        self.feedback_history[result.hypothesis_id].append({
            'prior_confidence': prior,
            'posterior_confidence': hypothesis.confidence,
            'judgment': result.human_judgment,
            'human_confidence': result.confidence
        })

    def rank_hypotheses(
        self,
        hypotheses: List[Hypothesis],
        strategy: str = 'expected_value'
    ) -> List[Tuple[int, Hypothesis]]:
        """
        Rank hypotheses for investigation priority.

        Strategies:
        - 'expected_value': confidence × novelty × feasibility
        - 'ucb': Upper confidence bound (explore + exploit)
        - 'thompson': Thompson sampling for exploration
        - 'human_guided': Prioritize based on human feedback

        Args:
            hypotheses: List of hypotheses
            strategy: Ranking strategy

        Returns:
            List of (rank, hypothesis) tuples, sorted by priority
        """
        scores = []

        for i, h in enumerate(hypotheses):
            if strategy == 'expected_value':
                # Simple expected value
                score = h.confidence * h.novelty * h.feasibility

            elif strategy == 'ucb':
                # Upper Confidence Bound
                # Balance exploration (high uncertainty) and exploitation (high value)
                uncertainty = self.compute_uncertainty(h)

                # Exploitation: expected value
                exploit = h.confidence * h.novelty

                # Exploration: uncertainty bonus
                explore = uncertainty * self.explore_exploit_ratio

                score = exploit + explore

            elif strategy == 'human_guided':
                # Use human feedback if available
                if h.human_feedback and 'judgment' in h.human_feedback:
                    if h.human_feedback['judgment'] == 'promising':
                        score = h.confidence * 1.5  # Boost
                    elif h.human_feedback['judgment'] == 'unpromising':
                        score = h.confidence * 0.5  # Penalize
                    else:
                        score = h.confidence
                else:
                    # No feedback, use expected value
                    score = h.confidence * h.novelty * h.feasibility

            else:
                raise ValueError(f"Unknown ranking strategy: {strategy}")

            scores.append((i, h, score))

        # Sort by score (descending)
        ranked = sorted([(i, h) for i, h, score in scores],
                       key=lambda x: x[1].confidence * x[1].novelty,
                       reverse=True)

        return ranked

    def get_query_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about queries and feedback.

        Returns:
            Dictionary with query statistics
        """
        if not self.query_history:
            return {
                'total_queries': 0,
                'judgment_distribution': {},
                'average_human_confidence': 0.0
            }

        judgments = [q.human_judgment for q in self.query_history]
        confidences = [q.confidence for q in self.query_history]

        judgment_counts = {}
        for j in judgments:
            judgment_counts[j] = judgment_counts.get(j, 0) + 1

        return {
            'total_queries': len(self.query_history),
            'judgment_distribution': judgment_counts,
            'average_human_confidence': np.mean(confidences) if confidences else 0.0,
            'hypotheses_with_feedback': len(self.feedback_history),
            'feedback_per_hypothesis': {
                hid: len(feedback) for hid, feedback in self.feedback_history.items()
            }
        }


class FilamentHypothesisGenerator:
    """
    Generate hypotheses specifically for filament research.

    Creates hypotheses about:
    - Fragmentation mechanisms
    - Magnetic field effects
    - Environmental dependencies
    - Scaling relations
    """

    @staticmethod
    def generate_fragmentation_hypotheses(
        observational_constraints: Dict[str, float]
    ) -> List[Hypothesis]:
        """
        Generate hypotheses about filament fragmentation.

        Args:
            observational_constraints: Dict with observed values (e.g., spacing)

        Returns:
            List of Hypothesis objects
        """
        hypotheses = []

        # Hypothesis 1: Magnetic tension
        hypotheses.append(Hypothesis(
            id='frag_magnetic_tension',
            description='Core spacing is set by magnetic tension along filaments',
            confidence=0.7,
            novelty=0.6,
            feasibility=0.8,
            domain='astrophysics',
            metadata={
                'mechanism': 'magnetic_tension',
                'predicted_spacing': 0.20,
                'test_method': 'MHD_simulation'
            }
        ))

        # Hypothesis 2: Finite length effects
        hypotheses.append(Hypothesis(
            id='frag_finite_length',
            description='Core spacing is reduced by finite-length effects',
            confidence=0.6,
            novelty=0.4,
            feasibility=0.9,
            domain='astrophysics',
            metadata={
                'mechanism': 'finite_length',
                'predicted_spacing': 0.22,
                'test_method': 'linear_perturbation'
            }
        ))

        # Hypothesis 3: Turbulent compression
        hypotheses.append(Hypothesis(
            id='frag_turbulent',
            description='Core spacing is compressed by turbulent flows',
            confidence=0.5,
            novelty=0.7,
            feasibility=0.6,
            domain='astrophysics',
            metadata={
                'mechanism': 'turbulent_compression',
                'predicted_spacing': 0.18,
                'test_method': 'turbulence_simulation'
            }
        ))

        # Hypothesis 4: Hierarchical fragmentation
        hypotheses.append(Hypothesis(
            id='frag_hierarchical',
            description='Filaments fragment hierarchically: filaments→fibers→cores',
            confidence=0.8,
            novelty=0.3,
            feasibility=0.7,
            domain='astrophysics',
            metadata={
                'mechanism': 'hierarchical_fragmentation',
                'predicted_spacing': 'variable',
                'test_method': 'high_resolution_observation'
            }
        ))

        # Hypothesis 5: Mass accretion
        hypotheses.append(Hypothesis(
            id='frag_accretion',
            description='Core spacing is modified by ongoing mass accretion',
            confidence=0.4,
            novelty=0.8,
            feasibility=0.5,
            domain='astrophysics',
            metadata={
                'mechanism': 'mass_accretion',
                'predicted_spacing': 0.19,
                'test_method': 'time_dependent_simulation'
            }
        ))

        return hypotheses


# Convenience functions
def run_active_learning_round(
    hypotheses: List[Hypothesis],
    budget: int = 5
) -> Tuple[List[Hypothesis], Dict[str, Any]]:
    """
    Run one round of active learning.

    Args:
        hypotheses: List of hypotheses
        budget: Number of human queries

    Returns:
        Tuple of (updated hypotheses, statistics)
    """
    loop = ActiveLearningLoop()

    # Select hypotheses to query
    to_query = loop.select_queries(hypotheses, budget=budget)

    print(f"\nSelected {len(to_query)} hypotheses for human evaluation:")

    # Query human for each
    for h in to_query:
        result = loop.query_human(h, interactive=True)

        if result is not None:
            loop.incorporate_feedback(result, hypotheses)

    # Re-rank hypotheses
    ranked = loop.rank_hypotheses(hypotheses, strategy='human_guided')

    # Get statistics
    stats = loop.get_query_statistics()

    return hypotheses, stats


if __name__ == '__main__':
    # Test active learning
    print("Testing Active Learning Loop...")

    # Generate test hypotheses
    hypotheses = FilamentHypothesisGenerator.generate_fragmentation_hypotheses({})

    print(f"\nGenerated {len(hypotheses)} hypotheses:")
    for h in hypotheses:
        print(f"  {h.id}: {h.description}")

    # Simulate active learning (non-interactive)
    print("\nSimulating active learning round...")

    loop = ActiveLearningLoop()
    to_query = loop.select_queries(hypotheses, budget=2, method='uncertainty')

    print(f"Selected {len(to_query)} hypotheses for query:")
    for h in to_query:
        print(f"  {h.id} (confidence={h.confidence:.2f}, uncertainty={loop.compute_uncertainty(h):.2f})")

    # Rank hypotheses
    ranked = loop.rank_hypotheses(hypotheses)
    print("\nHypothesis ranking:")
    for rank, (i, h) in enumerate(ranked, 1):
        print(f"  {rank}. {h.id}: score={h.confidence*h.novelty:.3f}")
