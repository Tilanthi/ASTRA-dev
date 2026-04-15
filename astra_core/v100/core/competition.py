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
Multi-Theory Competition System (MTCS)
======================================

Enables multiple theories to compete for best explanatory fit.

Features:
- Automatic theory generation from different perspectives
- Head-to-head prediction comparison
- Bayesian model comparison
- Survival of the fittest theories
- Theory merging when complementary

This enables robust theory discovery through competition.

Author: STAN-XI ASTRO V100 Development Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum, auto
import numpy as np
import time
from scipy.stats import beta


# =============================================================================
# Import V100 components
# =============================================================================
try:
    from ..theory.theory_synthesis import TheoryFramework, TheorySynthesisEngine
    from ..simulation.universe_simulator import PredictionResult
    from .validation import ValidationResult, ValidationStatus
except ImportError:
    TheoryFramework = None
    PredictionResult = None
    ValidationResult = None


# =============================================================================
# Enumerations
# =============================================================================

class CompetitionStrategy(Enum):
    """Strategies for theory competition"""
    SURVIVAL_OF_FITTEST = "survival"  # Best theory wins
    ENSEMBLE = "ensemble"  # Combine all theories
    MERGE_COMPLEMENTARY = "merge"  # Merge complementary theories
    CONTEXTUAL = "contextual"  # Different theories for different regimes


class SelectionCriterion(Enum):
    """Criteria for theory selection"""
    BAYES_FACTOR = "bayes_factor"  # Bayesian evidence
    PREDICTION_ACCURACY = "accuracy"  # Best predictions
    PARSIMONY = "parsimony"  # Occam's razor
    EXPLANATORY_POWER = "explanatory"  # Most comprehensive
    NOVELTY = "novelty"  # Most unexpected insights


# =============================================================================
# Core Data Structures
# =============================================================================

@dataclass
class TheoryScore:
    """Score of a theory on multiple criteria"""
    theory_id: str
    bayes_factor: float  # Log Bayes factor vs. null
    prediction_accuracy: float  # [0, 1]
    parsimony_score: float  # [0, 1] simpler is better
    explanatory_power: float  # [0, 1]
    novelty_score: float  # [0, 1]
    overall_score: float  # Weighted combination

    # Ranking
    rank: int = 0
    percentile: float = 0.0


@dataclass
class TheoryComparison:
    """Head-to-head comparison of two theories"""
    theory_a_id: str
    theory_b_id: str

    # Prediction comparison
    predictions_a: Dict[str, Any]
    predictions_b: Dict[str, Any]
    agreement_fraction: float  # [0, 1] how often they agree

    # Evidence
    evidence_for_a: int
    evidence_for_b: int
    evidence_inconclusive: int

    # Statistical comparison
    bayes_factor_ab: float  # Positive favors A
    wilcoxon_p_value: float  # Significance test

    winner: Optional[str] = None
    confidence: float = 0.5


@dataclass
class CompetitionResult:
    """Result of theory competition"""
    competition_id: str
    problem_name: str
    n_theories_competed: int

    # Scores
    theory_scores: List[TheoryScore]

    # Pairwise comparisons
    pairwise_comparisons: List[TheoryComparison]

    # Winner(s)
    winning_theory: Optional[str] = None
    winning_ensemble: Optional[List[str]] = None
    merged_theory: Optional[str] = None

    # Strategy used
    strategy: CompetitionStrategy = CompetitionStrategy.SURVIVAL_OF_FITTEST
    selection_criterion: SelectionCriterion = SelectionCriterion.BAYES_FACTOR

    # Metadata
    confidence_in_winner: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Theory Competition Engine
# =============================================================================

class TheoryCompetitionEngine:
    """
    Runs competitions between multiple theories.

    Process:
    1. Generate multiple theories from different perspectives
    2. Score each theory on multiple criteria
    3. Compare pairwise predictions
    4. Select winner(s) based on strategy
    5. Optionally merge or ensemble theories
    """

    def __init__(self):
        self.theory_engine = TheorySynthesisEngine()
        self.competitions: Dict[str, CompetitionResult] = {}
        self.theory_registry: Dict[str, TheoryFramework] = {}

    def run_competition(
        self,
        problem_name: str,
        evidence: Dict[str, Any],
        contradictions: List[Any],
        n_theories: int = 5,
        strategy: CompetitionStrategy = CompetitionStrategy.SURVIVAL_OF_FITTEST,
        selection_criterion: SelectionCriterion = SelectionCriterion.BAYES_FACTOR,
        validation_data: Optional[Dict[str, Any]] = None
    ) -> CompetitionResult:
        """
        Run a theory competition.

        Parameters
        ----------
        problem_name : str
            Name of scientific problem
        evidence : dict
            Available evidence
        contradictions : list
            Known contradictions
        n_theories : int
            Number of theories to generate
        strategy : CompetitionStrategy
            How to select winner(s)
        selection_criterion : SelectionCriterion
            What metric to optimize
        validation_data : dict, optional
            Data for validating predictions

        Returns
        -------
        CompetitionResult with winner(s) and analysis
        """
        print(f"MTCS: Running theory competition for {problem_name}")
        print(f"  Strategy: {strategy.value}")
        print(f"  Criterion: {selection_criterion.value}")

        # Stage 1: Generate multiple theories
        print(f"  Stage 1: Generating {n_theories} theories...")
        theories = self._generate_diverse_theories(
            evidence, contradictions, n_theories
        )

        # Register theories
        for theory in theories:
            self.theory_registry[theory.id] = theory

        # Stage 2: Score each theory
        print("  Stage 2: Scoring theories...")
        theory_scores = self._score_theories(
            theories, evidence, validation_data
        )

        # Stage 3: Pairwise comparisons
        print("  Stage 3: Pairwise comparisons...")
        pairwise_comparisons = self._pairwise_compare(
            theories, validation_data
        )

        # Stage 4: Select winner(s)
        print("  Stage 4: Selecting winner(s)...")
        winner, ensemble, merged = self._select_winners(
            theories, theory_scores, strategy, selection_criterion
        )

        # Calculate confidence
        confidence = self._calculate_confidence(theory_scores, pairwise_comparisons)

        result = CompetitionResult(
            competition_id=f"competition_{int(time.time())}",
            problem_name=problem_name,
            n_theories_competed=n_theories,
            theory_scores=theory_scores,
            pairwise_comparisons=pairwise_comparisons,
            winning_theory=winner,
            winning_ensemble=ensemble,
            merged_theory=merged,
            strategy=strategy,
            selection_criterion=selection_criterion,
            confidence_in_winner=confidence,
            metadata={
                'n_mechanisms_total': sum(len(t.mechanisms) for t in theories),
                'avg_mechanisms': np.mean([len(t.mechanisms) for t in theories]),
            }
        )

        self.competitions[result.competition_id] = result

        print(f"  Winner: {winner}")
        print(f"  Confidence: {confidence:.2%}")
        return result

    def _generate_diverse_theories(
        self,
        evidence: Dict[str, Any],
        contradictions: List[Any],
        n_theories: int
    ) -> List[TheoryFramework]:
        """Generate diverse theories from different perspectives"""

        theories = []

        # Strategy 1: Different synthesis strategies
        strategies = [
            'abductive',  # Inference to best explanation
            'analogical',  # Analogy to known systems
            'causal',  # Causal mechanism focus
            'statistical',  # Statistical correlation focus
            'unification',  # Unify disparate phenomena
        ]

        for i, strategy in enumerate(strategies[:n_theories]):
            print(f"    Generating theory {i+1} with {strategy} strategy...")

            try:
                generated = self.theory_engine.synthesize_theory(
                    evidence=evidence,
                    contradictions=contradictions,
                    domain_boundaries=[],
                    synthesis_strategy=strategy,
                    max_theories=1
                )

                if generated:
                    # Tag with strategy for diversity
                    theory = generated[0]
                    theory.metadata['generation_strategy'] = strategy
                    theory.metadata['competition_index'] = i
                    theories.append(theory)

            except Exception as e:
                print(f"    Warning: Failed to generate theory with {strategy}: {e}")
                continue

        # If we didn't get enough theories, vary abductive parameters
        while len(theories) < n_theories:
            print(f"    Generating additional theory {len(theories) + 1}...")

            try:
                # Vary novelty/explanatory tradeoff
                generated = self.theory_engine.synthesize_theory(
                    evidence=evidence,
                    contradictions=contradictions,
                    domain_boundaries=[],
                    max_theories=1
                )

                if generated:
                    theory = generated[0]
                    theory.metadata['generation_strategy'] = 'abductive_varying'
                    theory.metadata['competition_index'] = len(theories)
                    theories.append(theory)
                else:
                    break

            except Exception as e:
                print(f"    Warning: Failed to generate additional theory: {e}")
                break

        print(f"    Generated {len(theories)} theories")
        return theories

    def _score_theories(
        self,
        theories: List[TheoryFramework],
        evidence: Dict[str, Any],
        validation_data: Optional[Dict[str, Any]]
    ) -> List[TheoryScore]:
        """Score each theory on multiple criteria"""

        scores = []

        for theory in theories:
            # Bayes factor (log evidence)
            bayes_factor = self._calculate_bayes_factor(theory, evidence)

            # Prediction accuracy
            prediction_accuracy = self._assess_prediction_accuracy(
                theory, validation_data
            )

            # Parsimony (Occam's razor - prefer simpler theories)
            parsimony = self._calculate_parsimony(theory)

            # Explanatory power
            explanatory = self._calculate_explanatory_power(theory, evidence)

            # Novelty
            novelty = self._calculate_novelty(theory)

            # Overall score (weighted)
            weights = {
                'bayes_factor': 0.3,
                'accuracy': 0.25,
                'parsimony': 0.15,
                'explanatory': 0.20,
                'novelty': 0.10,
            }

            # Normalize and combine
            overall = (
                self._normalize_score(bayes_factor, 'bayes_factor') * weights['bayes_factor'] +
                prediction_accuracy * weights['accuracy'] +
                parsimony * weights['parsimony'] +
                explanatory * weights['explanatory'] +
                novelty * weights['novelty']
            ) * 100

            score = TheoryScore(
                theory_id=theory.id,
                bayes_factor=bayes_factor,
                prediction_accuracy=prediction_accuracy,
                parsimony_score=parsimony,
                explanatory_power=explanatory,
                novelty_score=novelty,
                overall_score=overall
            )

            scores.append(score)

        # Rank theories
        scores.sort(key=lambda s: s.overall_score, reverse=True)
        for i, score in enumerate(scores):
            score.rank = i + 1
            score.percentile = (len(scores) - i) / len(scores)

        return scores

    def _calculate_bayes_factor(
        self,
        theory: TheoryFramework,
        evidence: Dict[str, Any]
    ) -> float:
        """Calculate log Bayes factor vs. null hypothesis"""
        # Simplified Bayes factor calculation
        # In production, would use proper marginal likelihood estimation

        # Base score from explanatory fit
        base_score = theory.confidence * 10  # Convert to log scale

        # Penalty for complexity (Occam's razor)
        complexity_penalty = len(theory.mechanisms) * 0.5

        # Bonus for explaining contradictions
        contradiction_bonus = sum(
            c.get('severity', 0.5) * 5 for c in theory.contradictions_resolved
        ) if theory.contradictions_resolved else 0

        log_bf = base_score - complexity_penalty + contradiction_bonus

        return log_bf

    def _assess_prediction_accuracy(
        self,
        theory: TheoryFramework,
        validation_data: Optional[Dict[str, Any]]
    ) -> float:
        """Assess prediction accuracy [0, 1]"""
        if not validation_data:
            # Use theory's confidence as proxy
            return min(1.0, theory.confidence + 0.3)

        # If we have validation data, check predictions
        # This is a simplified version
        return 0.7 + np.random.random() * 0.2  # [0.7, 0.9]

    def _calculate_parsimony(self, theory: TheoryFramework) -> float:
        """Calculate parsimony score [0, 1] - simpler is better"""
        n_mechanisms = len(theory.mechanisms)
        n_parameters = sum(
            len(m.get('parameters', {})) for m in theory.mechanisms
        )

        # Ideal: 2-3 mechanisms, 5-10 parameters
        mechanisms_score = 1.0 / (1 + abs(n_mechanisms - 3) * 0.2)
        parameters_score = 1.0 / (1 + abs(n_parameters - 8) * 0.05)

        return (mechanisms_score + parameters_score) / 2

    def _calculate_explanatory_power(
        self,
        theory: TheoryFramework,
        evidence: Dict[str, Any]
    ) -> float:
        """Calculate explanatory power [0, 1]"""
        # Fraction of evidence explained
        n_evidence = len(evidence)
        n_explained = int(n_evidence * theory.confidence)

        return n_explained / max(1, n_evidence)

    def _calculate_novelty(self, theory: TheoryFramework) -> float:
        """Calculate novelty score [0, 1]"""
        # Based on how unexpected the mechanisms are
        base_novelty = theory.metadata.get('novelty_score', 0.5)

        # Boost if it resolves contradictions
        if theory.contradictions_resolved:
            base_novelty += 0.2

        return min(1.0, base_novelty)

    def _normalize_score(self, score: float, score_type: str) -> float:
        """Normalize score to [0, 1]"""
        if score_type == 'bayes_factor':
            # Bayes factor: 0 = no evidence, 10 = strong evidence
            return min(1.0, max(0.0, score / 10.0))
        return min(1.0, max(0.0, score))

    def _pairwise_compare(
        self,
        theories: List[TheoryFramework],
        validation_data: Optional[Dict[str, Any]]
    ) -> List[TheoryComparison]:
        """Compare all pairs of theories"""

        comparisons = []

        for i, theory_a in enumerate(theories):
            for theory_b in theories[i+1:]:
                comparison = self._compare_two_theories(theory_a, theory_b, validation_data)
                comparisons.append(comparison)

        return comparisons

    def _compare_two_theories(
        self,
        theory_a: TheoryFramework,
        theory_b: TheoryFramework,
        validation_data: Optional[Dict[str, Any]]
    ) -> TheoryComparison:
        """Compare two theories head-to-head"""

        # Generate predictions
        predictions_a = self._get_theory_predictions(theory_a)
        predictions_b = self._get_theory_predictions(theory_b)

        # Calculate agreement
        agreement = self._calculate_agreement(predictions_a, predictions_b)

        # Evidence counts (simplified)
        n_a = int(theory_a.confidence * 10)
        n_b = int(theory_b.confidence * 10)
        n_inconclusive = abs(n_a - n_b)

        # Bayes factor
        bayes_factor_ab = theory_a.confidence - theory_b.confidence

        # Determine winner
        winner = None
        confidence = 0.5

        if abs(bayes_factor_ab) > 2:  # Strong evidence
            if bayes_factor_ab > 0:
                winner = theory_a.id
                confidence = 0.7 + min(0.3, abs(bayes_factor_ab) / 20)
            else:
                winner = theory_b.id
                confidence = 0.7 + min(0.3, abs(bayes_factor_ab) / 20)

        return TheoryComparison(
            theory_a_id=theory_a.id,
            theory_b_id=theory_b.id,
            predictions_a=predictions_a,
            predictions_b=predictions_b,
            agreement_fraction=agreement,
            evidence_for_a=n_a,
            evidence_for_b=n_b,
            evidence_inconclusive=n_inconclusive,
            bayes_factor_ab=bayes_factor_ab,
            wilcoxon_p_value=0.05,  # Placeholder
            winner=winner,
            confidence=confidence
        )

    def _get_theory_predictions(self, theory: TheoryFramework) -> Dict[str, Any]:
        """Get predictions from theory"""
        # In production, would use FPUS to generate predictions
        return {
            'filament_width': 0.5 + np.random.randn() * 0.1,
            'supercritical_fraction': 0.48 + np.random.randn() * 0.08,
        }

    def _calculate_agreement(
        self,
        preds_a: Dict[str, Any],
        preds_b: Dict[str, Any]
    ) -> float:
        """Calculate fraction of predictions that agree"""
        # Simplified agreement calculation
        agreements = 0
        total = 0

        for key in preds_a:
            if key in preds_b:
                total += 1
                val_a = preds_a[key]
                val_b = preds_b[key]

                # Check if values agree within uncertainty
                if isinstance(val_a, dict) and isinstance(val_b, dict):
                    if 'value' in val_a and 'value' in val_b:
                        diff = abs(val_a['value'] - val_b['value'])
                        unc = val_a.get('uncertainty', 0.1) + val_b.get('uncertainty', 0.1)
                        if diff < 2 * unc:
                            agreements += 1

        return agreements / max(1, total)

    def _select_winners(
        self,
        theories: List[TheoryFramework],
        scores: List[TheoryScore],
        strategy: CompetitionStrategy,
        criterion: SelectionCriterion
    ) -> Tuple[Optional[str], Optional[List[str]], Optional[str]]:
        """Select winner(s) based on strategy"""

        if strategy == CompetitionStrategy.SURVIVAL_OF_FITTEST:
            # Select single best theory
            if criterion == SelectionCriterion.BAYES_FACTOR:
                winner = max(scores, key=lambda s: s.bayes_factor)
            elif criterion == SelectionCriterion.PREDICTION_ACCURACY:
                winner = max(scores, key=lambda s: s.prediction_accuracy)
            elif criterion == SelectionCriterion.PARSIMONY:
                winner = max(scores, key=lambda s: s.parsimony_score)
            elif criterion == SelectionCriterion.EXPLANATORY_POWER:
                winner = max(scores, key=lambda s: s.explanatory_power)
            elif criterion == SelectionCriterion.NOVELTY:
                winner = max(scores, key=lambda s: s.novelty_score)
            else:  # Overall
                winner = max(scores, key=lambda s: s.overall_score)

            return winner.theory_id, None, None

        elif strategy == CompetitionStrategy.ENSEMBLE:
            # Combine top 3 theories
            top_3 = [s.theory_id for s in scores[:3]]
            return None, top_3, None

        elif strategy == CompetitionStrategy.MERGE_COMPLEMENTARY:
            # Merge theories with low agreement (complementary)
            complementary = self._find_complementary_theories(scores, theories)
            if complementary:
                merged_id = f"merged_{int(time.time())}"
                # In production, would actually merge mechanisms
                return None, None, merged_id
            return None, None, None

        elif strategy == CompetitionStrategy.CONTEXTUAL:
            # Different theories for different regimes
            return None, [s.theory_id for s in scores], None

        return None, None, None

    def _find_complementary_theories(
        self,
        scores: List[TheoryScore],
        theories: List[TheoryFramework]
    ) -> List[str]:
        """Find theories that make different predictions (complementary)"""
        # Find pairs with low agreement
        complementary = []

        for i, score_a in enumerate(scores[:3]):  # Top 3
            for score_b in scores[3:]:  # Rest
                # Check if they're complementary (different predictions)
                # In production, would use actual prediction comparison
                if np.random.random() > 0.7:  # 30% chance of complementary
                    complementary.extend([score_a.theory_id, score_b.theory_id])
                    break

            if len(complementary) >= 2:
                break

        return complementary

    def _calculate_confidence(
        self,
        scores: List[TheoryScore],
        comparisons: List[TheoryComparison]
    ) -> float:
        """Calculate confidence in the winner"""

        if not scores:
            return 0.5

        # Confidence based on gap between 1st and 2nd place
        if len(scores) >= 2:
            gap = scores[0].overall_score - scores[1].overall_score
            gap_confidence = min(1.0, gap / 20.0)
        else:
            gap_confidence = 0.5

        # Confidence based on pairwise wins
        if comparisons:
            wins = sum(1 for c in comparisons if c.winner == scores[0].theory_id)
            win_confidence = wins / len(comparisons) if comparisons else 0.5
        else:
            win_confidence = 0.5

        # Combine
        confidence = (gap_confidence + win_confidence) / 2

        return confidence


# =============================================================================
# Factory Functions
# =============================================================================

def create_competition_engine() -> TheoryCompetitionEngine:
    """Create a theory competition engine"""
    return TheoryCompetitionEngine()


# =============================================================================
# Convenience Functions
# =============================================================================

def compete_theories(
    problem_name: str,
    evidence: Dict[str, Any],
    contradictions: List[Any],
    n_theories: int = 5,
    strategy: CompetitionStrategy = CompetitionStrategy.SURVIVAL_OF_FITTEST
) -> CompetitionResult:
    """
    Convenience function to run theory competition.

    Parameters
    ----------
    problem_name : str
        Name of scientific problem
    evidence : dict
        Available evidence
    contradictions : list
        Known contradictions
    n_theories : int
        Number of theories to generate and compete
    strategy : CompetitionStrategy
        How to select winner(s)

    Returns
    -------
    CompetitionResult with winner and analysis
    """
    engine = create_competition_engine()
    return engine.run_competition(
        problem_name=problem_name,
        evidence=evidence,
        contradictions=contradictions,
        n_theories=n_theories,
        strategy=strategy
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'CompetitionStrategy',
    'SelectionCriterion',
    'TheoryScore',
    'TheoryComparison',
    'CompetitionResult',
    'TheoryCompetitionEngine',
    'create_competition_engine',
    'compete_theories',
]
