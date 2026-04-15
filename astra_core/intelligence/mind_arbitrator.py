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
Mind Arbitrator for Multi-Mind Orchestration Layer

Handles anticipatory arbitration, conflict prediction, and
disagreement resolution between specialized minds.

Version: 4.0.0
Date: 2026-03-17
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class ArbitrationStrategy(Enum):
    """Strategies for arbitrating between minds"""
    WEIGHTED_CONFIDENCE = "weighted_confidence"  # Weight by confidence
    MAJORITY_VOTE = "majority_vote"             # Majority agreement
    EXPERTISE_WEIGHTED = "expertise_weighted"   # Weight by domain relevance
    CONSENSUS = "consensus"                     # Seek consensus
    META_COGNITIVE = "meta_cognitive"           # Use meta-cognitive judgment


class ConflictType(Enum):
    """Types of conflicts between minds"""
    FACTUAL = "factual"           # Disagreement on facts
    INTERPRETATION = "interpretation"  # Different interpretations
    VALUE = "value"               # Value-based disagreement
    UNCERTAINTY = "uncertainty"   # Different uncertainty estimates
    PRIORITY = "priority"         # Different priority rankings


@dataclass
class ConflictPrediction:
    """A predicted conflict between minds"""
    mind_1_id: str
    mind_2_id: str
    conflict_type: ConflictType
    probability: float
    severity: float  # 0.0 to 1.0
    suggested_resolution: str
    reasoning: List[str]


@dataclass
class ArbitrationResult:
    """Result of arbitration between minds"""
    final_result: Any
    selected_mind_id: Optional[str]  # If single mind selected
    aggregation_method: str
    confidence: float
    disagreement_level: float
    resolution_path: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MindDisagreement:
    """A disagreement between mind results"""
    mind_1_id: str
    mind_2_id: str
    issue: str
    mind_1_position: str
    mind_2_position: str
    conflict_type: ConflictType
    severity: float


class MindArbitrator:
    """
    Arbitrates between specialized minds with anticipatory conflict detection.

    Features:
    - Predict conflicts before they occur
    - Resolve disagreements through multiple strategies
    - Track mind performance and bias
    - Learn optimal arbitration strategies
    """

    def __init__(self):
        self.arbitration_history: List[ArbitrationResult] = []
        self.conflict_predictions: List[ConflictPrediction] = []
        self.disagreement_history: List[MindDisagreement] = []
        self.mind_performance: Dict[str, Dict[str, float]] = {}
        self.strategy_success: Dict[ArbitrationStrategy, float] = {}

    def arbitrate(
        self,
        query: str,
        results: List[Any],
        strategy: ArbitrationStrategy = ArbitrationStrategy.WEIGHTED_CONFIDENCE,
        context: Optional[Dict[str, Any]] = None
    ) -> ArbitrationResult:
        """
        Arbitrate between mind results.

        Args:
            query: The original query
            results: List of MindResult objects
            strategy: Arbitration strategy to use
            context: Additional context

        Returns:
            ArbitrationResult with final decision
        """
        if not results:
            return ArbitrationResult(
                final_result=None,
                selected_mind_id=None,
                aggregation_method="none",
                confidence=0.0,
                disagreement_level=0.0,
                resolution_path=[]
            )

        if len(results) == 1:
            return ArbitrationResult(
                final_result=results[0].result,
                selected_mind_id=results[0].mind_id,
                aggregation_method="single",
                confidence=results[0].confidence,
                disagreement_level=0.0,
                resolution_path=[results[0].mind_id]
            )

        # Calculate disagreement level
        disagreement_level = self._calculate_disagreement(results)

        # Apply arbitration strategy
        if strategy == ArbitrationStrategy.WEIGHTED_CONFIDENCE:
            return self._weighted_confidence_arbitration(results, disagreement_level)
        elif strategy == ArbitrationStrategy.MAJORITY_VOTE:
            return self._majority_vote_arbitration(results, disagreement_level)
        elif strategy == ArbitrationStrategy.EXPERTISE_WEIGHTED:
            return self._expertise_weighted_arbitration(query, results, disagreement_level)
        elif strategy == ArbitrationStrategy.CONSENSUS:
            return self._consensus_arbitration(results, disagreement_level)
        elif strategy == ArbitrationStrategy.META_COGNITIVE:
            return self._meta_cognitive_arbitration(query, results, disagreement_level, context)
        else:
            return self._weighted_confidence_arbitration(results, disagreement_level)

    def anticipate_conflicts(
        self,
        query: str,
        minds: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[ConflictPrediction]:
        """
        Predict potential conflicts between minds before processing.

        Args:
            query: Query to be processed
            minds: List of available minds
            context: Additional context

        Returns:
            List of predicted conflicts
        """
        predictions = []

        # Analyze query characteristics
        query_lower = query.lower()

        # Check each pair of minds
        for i, mind_1 in enumerate(minds):
            for mind_2 in minds[i+1:]:
                # Check for domain overlap (potential for disagreement)
                overlap = self._calculate_domain_overlap(mind_1, mind_2)

                if overlap > 0.3:  # Significant overlap
                    # Predict conflict type based on domains
                    conflict_type = self._predict_conflict_type(mind_1, mind_2, query)

                    # Calculate probability
                    probability = overlap * self._get_disagreement_history(mind_1.mind_id, mind_2.mind_id)

                    if probability > 0.2:
                        prediction = ConflictPrediction(
                            mind_1_id=mind_1.mind_id,
                            mind_2_id=mind_2.mind_id,
                            conflict_type=conflict_type,
                            probability=probability,
                            severity=probability * 0.8,
                            suggested_resolution=self._suggest_resolution(conflict_type),
                            reasoning=[
                                f"Domain overlap: {overlap:.2f}",
                                f"Query triggers both {mind_1.domain.value} and {mind_2.domain.value}",
                                f"Previous disagreement rate: {self._get_disagreement_history(mind_1.mind_id, mind_2.mind_id):.2f}"
                            ]
                        )
                        predictions.append(prediction)

        self.conflict_predictions.extend(predictions)
        return predictions

    def resolve_disagreements(
        self,
        results: List[Any],
        disagreements: List[MindDisagreement]
    ) -> Any:
        """
        Resolve specific disagreements between mind results.

        Args:
            results: Mind results
            disagreements: List of disagreements to resolve

        Returns:
            Resolved final result
        """
        if not disagreements:
            # No disagreements, return weighted average
            return self._weighted_confidence_arbitration(results, 0.0)

        # Check if any disagreements are severe
        severe_disagreements = [d for d in disagreements if d.severity > 0.7]

        if severe_disagreements:
            # Need meta-cognitive resolution
            return self._meta_cognitive_resolution(results, severe_disagreements)

        # For minor disagreements, use weighted confidence
        return self._weighted_confidence_arbitration(results, sum(d.severity for d in disagreements) / len(disagreements))

    def _weighted_confidence_arbitration(
        self,
        results: List[Any],
        disagreement_level: float
    ) -> ArbitrationResult:
        """Arbitrate by weighting results by confidence."""
        total_weight = sum(r.confidence for r in results)

        if total_weight == 0:
            # Equal weights
            selected = results[0]
            confidence = 1.0 / len(results)
        else:
            # Find highest confidence
            selected = max(results, key=lambda r: r.confidence)
            confidence = selected.confidence / total_weight

        return ArbitrationResult(
            final_result=selected.result,
            selected_mind_id=selected.mind_id,
            aggregation_method="weighted_confidence",
            confidence=confidence,
            disagreement_level=disagreement_level,
            resolution_path=[selected.mind_id]
        )

    def _majority_vote_arbitration(
        self,
        results: List[Any],
        disagreement_level: float
    ) -> ArbitrationResult:
        """Arbitrate by majority vote."""
        # Group similar results
        result_groups = self._group_similar_results(results)

        # Find largest group
        largest_group = max(result_groups, key=lambda g: len(g))

        # Select highest confidence in largest group
        selected = max(largest_group, key=lambda r: r.confidence)

        return ArbitrationResult(
            final_result=selected.result,
            selected_mind_id=selected.mind_id,
            aggregation_method="majority_vote",
            confidence=len(largest_group) / len(results),
            disagreement_level=disagreement_level,
            resolution_path=[r.mind_id for r in largest_group]
        )

    def _expertise_weighted_arbitration(
        self,
        query: str,
        results: List[Any],
        disagreement_level: float
    ) -> ArbitrationResult:
        """Arbitrate by weighting by domain expertise relevance."""
        # Calculate relevance for each result
        relevance_scores = [r.relevance_score for r in results]

        # Combine relevance and confidence
        combined_scores = [
            r.confidence * rel * 2
            for r, rel in zip(results, relevance_scores)
        ]

        # Select best combined score
        best_idx = max(range(len(combined_scores)), key=lambda i: combined_scores[i])
        selected = results[best_idx]

        return ArbitrationResult(
            final_result=selected.result,
            selected_mind_id=selected.mind_id,
            aggregation_method="expertise_weighted",
            confidence=combined_scores[best_idx] / sum(combined_scores) if sum(combined_scores) > 0 else 0.5,
            disagreement_level=disagreement_level,
            resolution_path=[selected.mind_id]
        )

    def _consensus_arbitration(
        self,
        results: List[Any],
        disagreement_level: float
    ) -> ArbitrationResult:
        """Arbitrate by seeking consensus."""
        # Check for consensus
        result_groups = self._group_similar_results(results)

        if len(result_groups) == 1:
            # Full consensus
            selected = results[0]
            confidence = 1.0
        else:
            # Find group with highest average confidence
            best_group = max(
                result_groups,
                key=lambda g: sum(r.confidence for r in g) / len(g)
            )
            selected = max(best_group, key=lambda r: r.confidence)
            confidence = len(best_group) / len(results)

        return ArbitrationResult(
            final_result=selected.result,
            selected_mind_id=selected.mind_id,
            aggregation_method="consensus",
            confidence=confidence,
            disagreement_level=disagreement_level,
            resolution_path=[r.mind_id for r in result_groups[0]]
        )

    def _meta_cognitive_arbitration(
        self,
        query: str,
        results: List[Any],
        disagreement_level: float,
        context: Optional[Dict[str, Any]]
    ) -> ArbitrationResult:
        """Arbitrate using meta-cognitive judgment."""
        # This would interface with V93 MetacognitiveCore
        # For now, use expertise-weighted as fallback

        # Consider meta-cognitive factors
        selected = max(results, key=lambda r: r.confidence * r.relevance_score)

        return ArbitrationResult(
            final_result=selected.result,
            selected_mind_id=selected.mind_id,
            aggregation_method="meta_cognitive",
            confidence=selected.confidence,
            disagreement_level=disagreement_level,
            resolution_path=[selected.mind_id]
        )

    def _meta_cognitive_resolution(
        self,
        results: List[Any],
        disagreements: List[MindDisagreement]
    ) -> Any:
        """Resolve severe disagreements using meta-cognitive judgment."""
        # Apply penalties based on disagreement severity
        mind_penalties = {d.mind_1_id: 0.0 for d in disagreements}
        mind_penalties.update({d.mind_2_id: 0.0 for d in disagreements})

        for d in disagreements:
            mind_penalties[d.mind_1_id] += d.severity * 0.1
            mind_penalties[d.mind_2_id] += d.severity * 0.1

        # Adjust confidences
        adjusted_results = []
        for r in results:
            penalty = mind_penalties.get(r.mind_id, 0.0)
            adjusted_confidence = max(0.1, r.confidence - penalty)
            adjusted_results.append((r, adjusted_confidence))

        # Select best adjusted
        selected, adj_conf = max(adjusted_results, key=lambda x: x[1])

        return selected.result

    def _calculate_disagreement(self, results: List[Any]) -> float:
        """Calculate level of disagreement between results."""
        if len(results) < 2:
            return 0.0

        # Calculate variance in confidence
        confidences = [r.confidence for r in results]
        avg_confidence = sum(confidences) / len(confidences)
        variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)

        # Normalize to 0-1
        return min(1.0, variance * 4)

    def _group_similar_results(self, results: List[Any]) -> List[List[Any]]:
        """Group similar results together."""
        groups = []
        used = set()

        for i, result in enumerate(results):
            if i in used:
                continue

            group = [result]
            used.add(i)

            # Find similar results
            for j, other in enumerate(results):
                if j not in used and self._results_similar(result, other):
                    group.append(other)
                    used.add(j)

            groups.append(group)

        return groups

    def _results_similar(self, result1: Any, result2: Any) -> bool:
        """Check if two results are similar."""
        # Simple string similarity check
        str1 = str(result1.result).lower()
        str2 = str(result2.result).lower()

        # Check for keyword overlap
        words1 = set(str1.split())
        words2 = set(str2.split())

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2) / len(words1 | words2)
        return overlap > 0.5

    def _calculate_domain_overlap(self, mind1: Any, mind2: Any) -> float:
        """Calculate domain overlap between two minds."""
        # Base overlap from domain similarity
        if mind1.domain == mind2.domain:
            return 0.9

        # Complementary domains
        complementary_pairs = [
            ("physics", "mathematics"),
            ("empathy", "ethics"),
            ("politics", "philosophy"),
            ("poetry", "creative")
        ]

        pair = (mind1.domain.value, mind2.domain.value)
        if pair in complementary_pairs or (pair[1], pair[0]) in complementary_pairs:
            return 0.5

        return 0.1

    def _predict_conflict_type(self, mind1: Any, mind2: Any, query: str) -> ConflictType:
        """Predict the type of conflict between minds."""
        # Analytical minds might disagree on facts
        if mind1.reasoning_style.value == "formal" or mind2.reasoning_style.value == "formal":
            return ConflictType.FACTUAL

        # Creative minds might disagree on interpretations
        if mind1.domain.value in ["poetry", "creative"] or mind2.domain.value in ["poetry", "creative"]:
            return ConflictType.INTERPRETATION

        # Empathy and ethics might disagree on values
        if mind1.domain.value in ["empathy", "ethics"] and mind2.domain.value in ["empathy", "ethics"]:
            return ConflictType.VALUE

        return ConflictType.INTERPRETATION

    def _get_disagreement_history(self, mind1_id: str, mind2_id: str) -> float:
        """Get historical disagreement rate between two minds."""
        # Find past disagreements
        past_disagreements = [
            d for d in self.disagreement_history
            if (d.mind_1_id == mind1_id and d.mind_2_id == mind2_id) or
               (d.mind_1_id == mind2_id and d.mind_2_id == mind1_id)
        ]

        if not past_disagreements:
            return 0.1  # Base rate

        # Return average severity
        return sum(d.severity for d in past_disagreements) / len(past_disagreements)

    def _suggest_resolution(self, conflict_type: ConflictType) -> str:
        """Suggest resolution strategy for conflict type."""
        resolutions = {
            ConflictType.FACTUAL: "Verify with external sources or use formal logic",
            ConflictType.INTERPRETATION: "Accept multiple valid interpretations",
            ConflictType.VALUE: "Acknowledge value-based differences, present both perspectives",
            ConflictType.UNCERTAINTY: "Use probabilistic reasoning",
            ConflictType.PRIORITY: "Consider multi-criteria decision analysis"
        }
        return resolutions.get(conflict_type, "Use meta-cognitive judgment")

    def update_performance(self, mind_id: str, success: float) -> None:
        """Update mind performance tracking."""
        if mind_id not in self.mind_performance:
            self.mind_performance[mind_id] = {
                "successes": [],
                "avg_success": 0.0
            }

        self.mind_performance[mind_id]["successes"].append(success)

        # Keep last 100
        if len(self.mind_performance[mind_id]["successes"]) > 100:
            self.mind_performance[mind_id]["successes"].pop(0)

        # Update average
        successes = self.mind_performance[mind_id]["successes"]
        self.mind_performance[mind_id]["avg_success"] = sum(successes) / len(successes)


# =============================================================================
# Factory Functions
# =============================================================================

def create_mind_arbitrator() -> MindArbitrator:
    """Create a mind arbitrator."""
    return MindArbitrator()
