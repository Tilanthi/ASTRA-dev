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
Multi-Mind Orchestration Layer (MMOL) for STAN_XI_ASTRO V4.0

Inspired by: Unified Intelligence Framework

Design Concept:
Instead of a monolithic intelligence, create a dynamic architecture of specialized
sub-minds (each trained for domains like physics, empathy, politics, poetry). The
MMOL acts like a conductor, orchestrating their outputs based on "relevance-tuning"
and predictive synergy between minds.

Novel Element:
Each sub-mind rates not just its own confidence, but also anticipates the confidence
other minds might have. MMOL uses this for anticipatory arbitration and re-balancing
focus.

Version: 4.0.0
Date: 2026-03-17
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from .specialized_minds import (
    SpecializedMind, Domain, ReasoningStyle,
    create_all_specialized_minds,
    MindResult, ConfidenceModel
)


class ArbitrationStrategy(Enum):
    """Strategies for arbitrating between minds"""
    WEIGHTED_AVERAGE = "weighted_average"
    CONFIDENCE_BASED = "confidence_based"
    RELEVANCE_BASED = "relevance_based"
    MAJORITY_VOTE = "majority_vote"
    ANTICIPATORY = "anticipatory"
    CONSENSUS_SEEKING = "consensus_seeking"
    EXPERT_DRIVEN = "expert_driven"


class ConflictType(Enum):
    """Types of conflicts between minds"""
    FACTUAL = "factual"           # Disagreement about facts
    INTERPRETIVE = "interpretive"  # Different interpretations
    VALUE_BASED = "value_based"  # Different values lead to different conclusions
    METHODOLOGICAL = "methodological"  # Different methods/approaches
    SCOPE = "scope"              # Different scope/focus


@dataclass
class ConflictPrediction:
    """Prediction of a conflict between minds"""
    mind1_id: str
    mind2_id: str
    conflict_type: ConflictType
    severity: float  # 0.0 to 1.0
    predicted_disagreement: str
    resolution_suggestion: str


@dataclass
class CollaborationRecord:
    """Record of a collaboration between minds"""
    mind1_id: str
    mind2_id: str
    query: str
    synergy_score: float
    timestamp: float
    outcome: str


@dataclass
class SynergyModel:
    """Model of how well two minds collaborate"""
    mind1_id: str
    mind2_id: str
    baseline_synergy: float
    domain_synergy: float  # How well domains complement
    style_compatibility: float  # How well reasoning styles match
    learning_rate: float  # How quickly synergy improves
    collaboration_count: int = 0


@dataclass
class ArbitrationResult:
    """Result of arbitration between minds"""
    selected_minds: List[str]
    arbitration_strategy: ArbitrationStrategy
    synthesized_result: Any
    confidence: float
    conflicts_resolved: List[ConflictPrediction]
    individual_results: Dict[str, MindResult]
    timestamp: float


@dataclass
class MultiMindResult:
    """Result of multi-mind processing"""
    query: str
    individual_results: Dict[str, MindResult]
    arbitration_result: ArbitrationResult
    collaboration_quality: float
    emergent_insights: List[str]
    consensus_confidence: float


class MindArbitrator:
    """
    Coordinates multiple minds with anticipatory arbitration.

    Uses predicted confidences to optimize coordination before processing.
    """

    def __init__(self):
        self.minds: Dict[str, SpecializedMind] = {}
        self.arbitration_strategy = ArbitrationStrategy.ANTICIPATORY
        self.conflict_history: List[ConflictPrediction] = []
        self.resolution_methods: Dict[ConflictType, List[str]] = {
            ConflictType.FACTUAL: ["verify", "consensus", "weight_by_reliability"],
            ConflictType.INTERPRETIVE: ["synthesize", "compare", "seek_overlap"],
            ConflictType.VALUE_BASED: ["acknowledge_difference", "report_both", "synthesize"],
            ConflictType.METHODOLOGICAL: ["compare_methods", "combine_approaches"],
            ConflictType.SCOPE: ["clarify_scopes", "expand_both", "integrate"]
        }

    def register_mind(self, mind: SpecializedMind) -> None:
        """Add a new specialized mind."""
        self.minds[mind.mind_id] = mind

    def arbitrate(
        self,
        query: str,
        results: Dict[str, MindResult]
    ) -> ArbitrationResult:
        """
        Determine which minds should contribute and how much.

        Args:
            query: The query being processed
            results: Results from each mind

        Returns:
            ArbitrationResult with selection and synthesis
        """
        # Get anticipatory confidences
        anticipatory_confidences = self._gather_anticipatory_confidences(query, results)

        # Select arbitration strategy based on situation
        strategy = self._select_strategy(results, anticipatory_confidences)

        # Apply strategy
        if strategy == ArbitrationStrategy.ANTICIPATORY:
            return self._anticipatory_arbitration(query, results, anticipatory_confidences)
        elif strategy == ArbitrationStrategy.CONFIDENCE_BASED:
            return self._confidence_based_arbitration(query, results)
        elif strategy == ArbitrationStrategy.RELEVANCE_BASED:
            return self._relevance_based_arbitration(query, results)
        elif strategy == ArbitrationStrategy.MAJORITY_VOTE:
            return self._majority_vote_arbitration(query, results)
        else:
            return self._weighted_average_arbitration(query, results)

    def anticipate_conflicts(
        self,
        query: str,
        minds: List[SpecializedMind]
    ) -> List[ConflictPrediction]:
        """
        Predict which minds will disagree.

        Args:
            query: Query to analyze
            minds: Minds to analyze

        Returns:
            List of predicted conflicts
        """
        conflicts = []

        for i, mind1 in enumerate(minds):
            for mind2 in minds[i+1:]:
                # Check for domain conflicts
                if self._domains_conflict(mind1.domain, mind2.domain):
                    conflict = ConflictPrediction(
                        mind1_id=mind1.mind_id,
                        mind2_id=mind2.mind_id,
                        conflict_type=ConflictType.INTERPRETIVE,
                        severity=0.6,
                        predicted_disagreement=f"{mind1.domain} and {mind2.domain} may interpret differently",
                        resolution_suggestion="Synthesize both perspectives"
                    )
                    conflicts.append(conflict)

                # Check for style conflicts
                if self._styles_conflict(mind1.reasoning_style, mind2.reasoning_style):
                    conflict = ConflictPrediction(
                        mind1_id=mind1.mind_id,
                        mind2_id=mind2.mind_id,
                        conflict_type=ConflictType.METHODOLOGICAL,
                        severity=0.4,
                        predicted_disagreement=f"{mind1.reasoning_style} and {mind2.reasoning_style} may use different approaches",
                        resolution_suggestion="Combine methodological insights"
                    )
                    conflicts.append(conflict)

        return conflicts

    def resolve_disagreements(
        self,
        results: List[MindResult]
    ) -> Any:
        """
        Combine conflicting perspectives into synthesized result.

        Args:
            results: Conflicting mind results

        Returns:
            Synthesized result
        """
        # Collect all reasoning processes
        all_reasoning = []
        for result in results:
            all_reasoning.extend(result.reasoning_process)

        # Find common ground
        common_themes = self._find_common_themes(all_reasoning)

        # Build synthesis
        synthesis = {
            "conflicting_views": len(results),
            "common_ground": common_themes,
            "synthesis": self._create_synthesis(results, common_themes),
            "confidence": np.mean([r.confidence for r in results])
        }

        return synthesis

    def _gather_anticipatory_confidences(
        self,
        query: str,
        results: Dict[str, MindResult]
    ) -> Dict[str, Dict[str, float]]:
        """
        Gather anticipatory confidences (minds predicting other minds' confidence).

        Returns:
            Dictionary mapping mind_id to its predictions of others
        """
        anticipatory = {}

        for mind_id, mind in self.minds.items():
            if mind_id in results:
                # Get other minds
                other_minds = [m for m in self.minds.values() if m.mind_id != mind_id]

                # Predict their confidences
                predictions = mind.predict_confidence(query, other_minds)
                anticipatory[mind_id] = predictions

        return anticipatory

    def _select_strategy(
        self,
        results: Dict[str, MindResult],
        anticipatory: Dict[str, Dict[str, float]]
    ) -> ArbitrationStrategy:
        """Select optimal arbitration strategy."""
        # Check if there's high conflict
        confidences = [r.confidence for r in results.values()]
        confidence_variance = np.var(confidences) if len(confidences) > 1 else 0

        if confidence_variance > 0.1:
            return ArbitrationStrategy.CONSENSUS_SEEKING
        elif len(results) > 5:
            return ArbitrationStrategy.RELEVANCE_BASED
        else:
            return ArbitrationStrategy.ANTICIPATORY

    def _anticipatory_arbitration(
        self,
        query: str,
        results: Dict[str, MindResult],
        anticipatory: Dict[str, Dict[str, float]]
    ) -> ArbitrationResult:
        """Anticipatory arbitration: use predicted confidences."""
        # Weight minds by how well others predict their confidence
        weights = {}

        for mind_id in results.keys():
            # How well do others predict this mind?
            predictions_of_this = [pred[mind_id] for pred in anticipatory.values() if mind_id in pred]

            if predictions_of_this:
                # Higher weight if predictions are accurate
                # (we don't have actual accuracy, so use prediction variance)
                weights[mind_id] = 1.0 / (1.0 + np.std(predictions_of_this))
            else:
                weights[mind_id] = 1.0

        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return ArbitrationResult(
            selected_minds=list(results.keys()),
            arbitration_strategy=ArbitrationStrategy.ANTICIPATORY,
            synthesized_result=self._weighted_synthesis(results, weights),
            confidence=np.mean([r.confidence for r in results.values()]),
            conflicts_resolved=[],
            individual_results=results,
            timestamp=datetime.now().timestamp()
        )

    def _confidence_based_arbitration(
        self,
        query: str,
        results: Dict[str, MindResult]
    ) -> ArbitrationResult:
        """Confidence-based arbitration: weight by confidence."""
        weights = {k: r.confidence for k, r in results.items()}

        return ArbitrationResult(
            selected_minds=list(results.keys()),
            arbitration_strategy=ArbitrationStrategy.CONFIDENCE_BASED,
            synthesized_result=self._weighted_synthesis(results, weights),
            confidence=np.mean([r.confidence for r in results.values()]),
            conflicts_resolved=[],
            individual_results=results,
            timestamp=datetime.now().timestamp()
        )

    def _relevance_based_arbitration(
        self,
        query: str,
        results: Dict[str, MindResult]
    ) -> ArbitrationResult:
        """Relevance-based arbitration: weight by relevance."""
        weights = {k: r.relevance_score for k, r in results.items()}

        return ArbitrationResult(
            selected_minds=list(results.keys()),
            arbitration_strategy=ArbitrationStrategy.RELEVANCE_BASED,
            synthesized_result=self._weighted_synthesis(results, weights),
            confidence=np.mean([r.confidence for r in results.values()]),
            conflicts_resolved=[],
            individual_results=results,
            timestamp=datetime.now().timestamp()
        )

    def _majority_vote_arbitration(
        self,
        query: str,
        results: Dict[str, MindResult]
    ) -> ArbitrationResult:
        """Majority vote arbitration."""
        # Simplified: all minds selected
        return ArbitrationResult(
            selected_minds=list(results.keys()),
            arbitration_strategy=ArbitrationStrategy.MAJORITY_VOTE,
            synthesized_result=[r.result for r in results.values()],
            confidence=np.mean([r.confidence for r in results.values()]),
            conflicts_resolved=[],
            individual_results=results,
            timestamp=datetime.now().timestamp()
        )

    def _weighted_average_arbitration(
        self,
        query: str,
        results: Dict[str, MindResult]
    ) -> ArbitrationResult:
        """Weighted average arbitration."""
        # Equal weights
        weights = {k: 1.0 for k in results.keys()}

        return ArbitrationResult(
            selected_minds=list(results.keys()),
            arbitration_strategy=ArbitrationStrategy.WEIGHTED_AVERAGE,
            synthesized_result=self._weighted_synthesis(results, weights),
            confidence=np.mean([r.confidence for r in results.values()]),
            conflicts_resolved=[],
            individual_results=results,
            timestamp=datetime.now().timestamp()
        )

    def _weighted_synthesis(
        self,
        results: Dict[str, MindResult],
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Create weighted synthesis of results."""
        return {
            "results": {k: v.result for k, v in results.items()},
            "weights": weights,
            "synthesis": "Weighted combination of perspectives"
        }

    def _domains_conflict(self, domain1: Domain, domain2: Domain) -> bool:
        """Check if two domains tend to conflict."""
        conflicting_pairs = [
            (Domain.EMPATHY, Domain.PHYSICS),
            (Domain.POLITICS, Domain.MATHEMATICS),
            (Domain.POETRY, Domain.CAUSAL),
        ]
        return (domain1, domain2) in conflicting_pairs or (domain2, domain1) in conflicting_pairs

    def _styles_conflict(self, style1: ReasoningStyle, style2: ReasoningStyle) -> bool:
        """Check if reasoning styles tend to conflict."""
        conflicting_pairs = [
            (ReasoningStyle.FORMAL, ReasoningStyle.INTUITIVE),
            (ReasoningStyle.ANALYTICAL, ReasoningStyle.HOLISTIC),
            (ReasoningStyle.CRITICAL, ReasoningStyle.SYNTHETIC),
        ]
        return (style1, style2) in conflicting_pairs or (style2, style1) in conflicting_pairs

    def _find_common_themes(self, reasoning_processes: List[str]) -> List[str]:
        """Find common themes across reasoning processes."""
        # Simplified: look for common words
        word_counts = {}
        for process in reasoning_processes:
            words = process.lower().split()
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1

        # Return most common themes
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:5] if count > 1]

    def _create_synthesis(self, results: List[MindResult], themes: List[str]) -> str:
        """Create synthesis from results."""
        return f"Synthesis of {len(results)} perspectives around themes: {', '.join(themes)}"


class MindSynergy:
    """
    Manages predictive collaboration between minds.

    Models how well minds work together and optimizes collaboration.
    """

    def __init__(self):
        self.collaboration_history: List[CollaborationRecord] = []
        self.synergy_models: Dict[Tuple[str, str], SynergyModel] = {}
        self.min_collaborations_for_model = 3

    def predict_synergy(
        self,
        mind1_id: str,
        mind2_id: str,
        query: str
    ) -> float:
        """
        Predict how well two minds will collaborate.

        Args:
            mind1_id: First mind
            mind2_id: Second mind
            query: Query to collaborate on

        Returns:
            Predicted synergy score (0.0 to 1.0)
        """
        key = tuple(sorted([mind1_id, mind2_id]))

        if key not in self.synergy_models:
            # Create new model with default synergy
            self.synergy_models[key] = SynergyModel(
                mind1_id=mind1_id,
                mind2_id=mind2_id,
                baseline_synergy=0.5,
                domain_synergy=0.5,
                style_compatibility=0.5,
                learning_rate=0.1
            )

        model = self.synergy_models[key]

        # Predict synergy based on model
        synergy = (
            model.baseline_synergy * 0.3 +
            model.domain_synergy * 0.3 +
            model.style_compatibility * 0.4
        )

        # Adjust based on collaboration history
        if model.collaboration_count > 0:
            # Recent collaborations more indicative
            recent_collaborations = [
                c for c in self.collaboration_history[-10:]
                if c.mind1_id == mind1_id and c.mind2_id == mind2_id
            ]
            if recent_collaborations:
                avg_synergy = np.mean([c.synergy_score for c in recent_collaborations])
                synergy = 0.7 * synergy + 0.3 * avg_synergy

        return synergy

    def optimize_collaboration(
        self,
        query: str,
        available_minds: List[str],
        target_count: int = 3
    ) -> List[str]:
        """
        Determine optimal mind combination for a query.

        Args:
            query: Query to address
            available_minds: Minds that can participate
            target_count: How many minds to select

        Returns:
            List of selected mind IDs
        """
        if len(available_minds) <= target_count:
            return available_minds

        # Calculate pairwise synergy matrix
        synergy_matrix = {}
        for i, mind1 in enumerate(available_minds):
            for mind2 in available_minds[i+1:]:
                synergy = self.predict_synergy(mind1, mind2, query)
                synergy_matrix[(mind1, mind2)] = synergy
                synergy_matrix[(mind2, mind1)] = synergy

        # Select minds with highest total synergy
        mind_scores = {mind: 0.0 for mind in available_minds}

        for mind in available_minds:
            # Sum synergy with all other minds
            total_synergy = 0.0
            for other in available_minds:
                if mind != other:
                    key = tuple(sorted([mind, other]))
                    total_synergy += synergy_matrix.get(key, 0.5)

            mind_scores[mind] = total_synergy

        # Select top minds
        sorted_minds = sorted(mind_scores.items(), key=lambda x: x[1], reverse=True)
        return [mind for mind, score in sorted_minds[:target_count]]

    def facilitate_cross_pollination(
        self,
        results: List[MindResult]
    ) -> Dict[str, List[str]]:
        """
        Enable minds to learn from each other.

        Args:
            results: Results from multiple minds

        Returns:
            Dictionary mapping mind_id to insights learned from others
        """
        insights = {}

        for i, result1 in enumerate(results):
            learned_insights = []

            for j, result2 in enumerate(results):
                if i != j:
                    # What can mind1 learn from mind2?
                    insight = self._extract_insight(result1, result2)
                    if insight:
                        learned_insights.append(insight)

            insights[result1.mind_id] = learned_insights

        return insights

    def update_synergy_model(
        self,
        collaboration: CollaborationRecord
    ) -> None:
        """Update synergy model based on collaboration outcome."""
        key = tuple(sorted([collaboration.mind1_id, collaboration.mind2_id]))

        if key not in self.synergy_models:
            self.synergy_models[key] = SynergyModel(
                mind1_id=collaboration.mind1_id,
                mind2_id=collaboration.mind2_id,
                baseline_synergy=0.5,
                domain_synergy=0.5,
                style_compatibility=0.5,
                learning_rate=0.1
            )

        model = self.synergy_models[key]

        # Update based on collaboration outcome
        if collaboration.synergy_score > 0.7:
            # Successful collaboration: increase synergy
            model.baseline_synergy = (
                0.9 * model.baseline_synergy +
                0.1 * collaboration.synergy_score
            )
        else:
            # Poor collaboration: decrease slightly
            model.baseline_synergy *= 0.95

        model.collaboration_count += 1
        self.collaboration_history.append(collaboration)

    def _extract_insight(self, result1: MindResult, result2: MindResult) -> Optional[str]:
        """Extract what result1 can learn from result2."""
        # Simplified: extract from reasoning process
        if result1.reasoning_process and result2.reasoning_process:
            # Find unique aspects in result2
            unique_aspects = set(result2.reasoning_process) - set(result1.reasoning_process)
            if unique_aspects:
                return f"Consider: {', '.join(list(unique_aspects)[:2])}"
        return None


class MultiMindOrchestrator:
    """
    Main MMOL orchestrator.

    Coordinates multiple specialized minds with anticipatory arbitration,
    relevance tuning, and predictive synergy.
    """

    def __init__(self):
        self.minds: Dict[str, SpecializedMind] = {}
        self.arbitrator = MindArbitrator()
        self.synergy = MindSynergy()
        self.global_workspace = None  # Will connect to existing GlobalWorkspace
        self.swarm_orchestrator = None  # Will connect to existing SwarmOrchestrator

        # Initialize with specialized minds
        self._initialize_minds()

    def _initialize_minds(self) -> None:
        """Initialize specialized minds."""
        all_minds = create_all_specialized_minds()

        for mind_id, mind in all_minds.items():
            self.register_mind(mind)

    def register_mind(self, mind: SpecializedMind) -> None:
        """Register a new specialized mind."""
        self.minds[mind.mind_id] = mind
        self.arbitrator.register_mind(mind)

    def multi_mind_processing(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> MultiMindResult:
        """
        Process query through multiple minds.

        Args:
            query: Query to process
            context: Additional context

        Returns:
            MultiMindResult with individual and synthesized results
        """
        context = context or {}

        # Anticipate conflicts
        mind_list = list(self.minds.values())
        predicted_conflicts = self.arbitrator.anticipate_conflicts(query, mind_list)

        # Select minds for this query
        selected_mind_ids = self.synergy.optimize_collaboration(query, list(self.minds.keys()))

        # Process through selected minds
        individual_results = {}
        for mind_id in selected_mind_ids:
            mind = self.minds[mind_id]
            result = mind.process(query, context)
            individual_results[mind_id] = result

        # Arbitrate between minds
        arbitration_result = self.arbitrator.arbitrate(query, individual_results)

        # Calculate collaboration quality
        collab_quality = self._calculate_collaboration_quality(individual_results)

        # Extract emergent insights
        emergent_insights = self._extract_emergent_insights(individual_results)

        # Calculate consensus confidence
        consensus_confidence = np.mean([r.confidence for r in individual_results.values()])

        return MultiMindResult(
            query=query,
            individual_results=individual_results,
            arbitration_result=arbitration_result,
            collaboration_quality=collab_quality,
            emergent_insights=emergent_insights,
            consensus_confidence=consensus_confidence
        )

    def adaptive_mind_selection(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> List[SpecializedMind]:
        """
        Select relevant minds based on query and context.

        Args:
            query: Query to analyze
            context: Context information

        Returns:
            List of selected minds
        """
        selected = []

        for mind in self.minds.values():
            relevance = mind.calculate_relevance(query)

            # Select if relevance is above threshold
            if relevance > 0.3:
                selected.append(mind)

        # If no minds highly relevant, use top 3
        if not selected:
            sorted_minds = sorted(
                self.minds.values(),
                key=lambda m: m.calculate_relevance(query),
                reverse=True
            )
            selected = sorted_minds[:3]

        return selected

    def anticipatory_coordination(
        self,
        query: str
    ) -> Dict[str, Any]:
        """
        Plan coordination before minds process.

        Args:
            query: Query to coordinate on

        Returns:
            Coordination plan
        """
        # Select minds
        selected_minds = self.adaptive_mind_selection(query, {})

        # Predict conflicts
        conflicts = self.arbitrator.anticipate_conflicts(query, selected_minds)

        # Plan collaboration
        collaboration_plan = {
            "query": query,
            "selected_minds": [m.mind_id for m in selected_minds],
            "predicted_conflicts": [
                {
                    "mind1": c.mind1_id,
                    "mind2": c.mind2_id,
                    "type": c.conflict_type.value,
                    "severity": c.severity
                }
                for c in conflicts
            ],
            "synergy_predictions": {}
        }

        # Add synergy predictions
        for i, mind1 in enumerate(selected_minds):
            for mind2 in selected_minds[i+1:]:
                synergy = self.synergy.predict_synergy(mind1.mind_id, mind2.mind_id, query)
                collaboration_plan["synergy_predictions"][f"{mind1.mind_id}_{mind2.mind_id}"] = synergy

        return collaboration_plan

    def get_status(self) -> Dict[str, Any]:
        """Get current MMOL status."""
        return {
            "num_minds": len(self.minds),
            "mind_ids": list(self.minds.keys()),
            "synergy_models": len(self.synergy.synergy_models),
            "collaboration_history": len(self.synergy.collaboration_history),
            "recent_conflicts": len(self.arbitrator.conflict_history)
        }

    def _calculate_collaboration_quality(self, results: Dict[str, MindResult]) -> float:
        """Calculate quality of collaboration."""
        if not results:
            return 0.0

        # Check diversity of perspectives
        confidence_variance = np.var([r.confidence for r in results.values()])
        diversity = min(confidence_variance, 1.0)

        # Check if minds learned from each other
        cross_learning = 0.0
        for result in results.values():
            if result.predicted_confidences:
                cross_learning += 0.1

        return (diversity + cross_learning) / 2.0

    def _extract_emergent_insights(self, results: Dict[str, MindResult]) -> List[str]:
        """Extract insights that emerge from multiple minds."""
        insights = []

        # Look for common themes across results
        all_reasoning = []
        for result in results.values():
            all_reasoning.extend(result.reasoning_process)

        # Find patterns
        from collections import Counter
        word_counts = Counter(all_reasoning)
        for word, count in word_counts.items():
            if count >= 2:  # Mentioned by multiple minds
                insights.append(f"Common theme: {word}")

        return insights


# =============================================================================
# Factory Functions
# =============================================================================

def create_multi_mind_orchestrator() -> MultiMindOrchestrator:
    """Create a Multi-Mind Orchestrator with all specialized minds."""
    return MultiMindOrchestrator()
