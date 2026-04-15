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
Mind Synergy for Multi-Mind Orchestration Layer

Enables predictive collaboration, cross-pollination, and
optimized teamwork between specialized minds.

Version: 4.0.0
Date: 2026-03-17
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import time


class SynergyType(Enum):
    """Types of synergy between minds"""
    COMPLEMENTARY = "complementary"    # Different strengths complement
    AMPLIFYING = "amplifying"          # Both amplify each other
    CROSS_POLLINATING = "cross_pollinating"  # Ideas transfer between
    CONFLICTING = "conflicting"        # Minds conflict (reduce synergy)
    INDEPENDENT = "independent"        # No significant synergy


@dataclass
class SynergyModel:
    """Model of synergy between two minds"""
    mind_1_id: str
    mind_2_id: str
    synergy_type: SynergyType
    strength: float  # 0.0 to 1.0
    success_rate: float
    last_updated: float
    collaboration_count: int
    examples: List[str] = field(default_factory=list)


@dataclass
class SynergyPrediction:
    """Prediction of synergy for a potential collaboration"""
    mind_1_id: str
    mind_2_id: str
    predicted_synergy: float
    confidence: float
    expected_benefit: str
    reasoning: List[str]


@dataclass
class CollaborationPlan:
    """Plan for mind collaboration"""
    participating_minds: List[str]
    coordination_strategy: str
    expected_synergy: float
    information_flow: List[Tuple[str, str]]  # (from, to)
    division_of_labor: Dict[str, str]
    quality_checks: List[str]


@dataclass
class CrossPollinationResult:
    """Result of cross-pollination between minds"""
    source_mind_id: str
    target_mind_id: str
    transferred_insights: List[str]
    new_synthesis: str
    quality_score: float


class MindSynergy:
    """
    Manages synergy and collaboration between specialized minds.

    Features:
    - Predict synergy between mind pairs
    - Optimize collaboration teams
    - Facilitate cross-pollination of ideas
    - Track collaboration success
    """

    def __init__(self):
        self.synergy_models: Dict[Tuple[str, str], SynergyModel] = {}
        self.collaboration_history: List[CollaborationPlan] = []
        self.cross_pollinations: List[CrossPollinationResult] = []
        self.mind_capabilities: Dict[str, Set[str]] = {}
        self.team_performance: Dict[str, float] = {}

    def predict_synergy(
        self,
        mind_1_id: str,
        mind_2_id: str,
        query: Optional[str] = None
    ) -> float:
        """
        Predict synergy level between two minds.

        Args:
            mind_1_id: First mind ID
            mind_2_id: Second mind ID
            query: Optional query to contextualize

        Returns:
            Predicted synergy score (0.0 to 1.0)
        """
        # Check existing model
        key = tuple(sorted([mind_1_id, mind_2_id]))
        if key in self.synergy_models:
            return self.synergy_models[key].strength

        # Predict based on domain complementarity
        base_synergy = self._calculate_base_synergy(mind_1_id, mind_2_id)

        return base_synergy

    def optimize_collaboration(
        self,
        query: str,
        available_minds: List[Any],
        target_count: int = 3,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Select optimal team of minds for a query.

        Args:
            query: Query to address
            available_minds: List of available SpecializedMind objects
            target_count: Desired team size
            context: Additional context

        Returns:
            List of selected mind IDs
        """
        if len(available_minds) <= target_count:
            return [m.mind_id for m in available_minds]

        # Calculate relevance and individual merit
        mind_scores = {}

        for mind in available_minds:
            relevance = mind.calculate_relevance(query)
            confidence = mind.confidence_model.base_confidence
            mind_scores[mind.mind_id] = {
                "mind": mind,
                "relevance": relevance,
                "confidence": confidence,
                "individual_score": relevance * confidence
            }

        # If target_count is 1, return best individual
        if target_count == 1:
            return [max(mind_scores.items(), key=lambda x: x[1]["individual_score"])[0]]

        # For teams, consider synergy
        best_team = None
        best_team_score = -1

        # Try combinations
        from itertools import combinations

        for team_minds in combinations(available_minds, target_count):
            team_ids = [m.mind_id for m in team_minds]

            # Calculate team score
            individual_sum = sum(mind_scores[mid]["individual_score"] for mid in team_ids)

            # Add synergy bonus
            synergy_bonus = 0.0
            for i, m1 in enumerate(team_ids):
                for m2 in team_ids[i+1:]:
                    synergy_bonus += self.predict_synergy(m1, m2, query)

            team_score = individual_sum + (synergy_bonus * 0.3)

            if team_score > best_team_score:
                best_team_score = team_score
                best_team = team_ids

        return best_team if best_team else [available_minds[0].mind_id]

    def create_collaboration_plan(
        self,
        query: str,
        selected_minds: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CollaborationPlan:
        """
        Create a detailed collaboration plan.

        Args:
            query: Query to address
            selected_minds: List of selected minds
            context: Additional context

        Returns:
            Collaboration plan
        """
        mind_ids = [m.mind_id for m in selected_minds]

        # Calculate overall synergy
        total_synergy = 0.0
        for i, m1 in enumerate(mind_ids):
            for m2 in mind_ids[i+1:]:
                total_synergy += self.predict_synergy(m1, m2, query)

        avg_synergy = total_synergy / (len(mind_ids) * (len(mind_ids) - 1) / 2) if len(mind_ids) > 1 else 0.5

        # Determine information flow
        info_flow = []
        for i, m1 in enumerate(selected_minds):
            for m2 in selected_minds:
                if m1.mind_id != m2.mind_id:
                    # Mind 1 provides input to Mind 2
                    if self._should_provide_input(m1, m2, query):
                        info_flow.append((m1.mind_id, m2.mind_id))

        # Determine division of labor
        division = {}
        for mind in selected_minds:
            role = self._assign_role(mind, query, selected_minds)
            division[mind.mind_id] = role

        # Quality checks
        quality_checks = [
            "Verify factual accuracy",
            "Check logical consistency",
            "Assess value alignment"
        ]

        plan = CollaborationPlan(
            participating_minds=mind_ids,
            coordination_strategy="parallel_processing",
            expected_synergy=avg_synergy,
            information_flow=info_flow,
            division_of_labor=division,
            quality_checks=quality_checks
        )

        self.collaboration_history.append(plan)
        return plan

    def facilitate_cross_pollination(
        self,
        results: List[Any],
        query: str
    ) -> List[CrossPollinationResult]:
        """
        Facilitate cross-pollination between mind results.

        Args:
            results: List of mind results
            query: Original query

        Returns:
            List of cross-pollination results
        """
        pollinations = []

        # Find complementary results
        for i, result1 in enumerate(results):
            for result2 in results[i+1:]:
                # Check if minds have complementary strengths
                synergy_score = self.predict_synergy(result1.mind_id, result2.mind_id, query)

                if synergy_score > 0.6:
                    # Create synthesis
                    synthesis = self._create_synthesis(result1, result2)

                    pollination = CrossPollinationResult(
                        source_mind_id=result1.mind_id,
                        target_mind_id=result2.mind_id,
                        transferred_insights=[
                            f"Insight from {result1.mind_id}",
                            f"Insight from {result2.mind_id}"
                        ],
                        new_synthesis=synthesis,
                        quality_score=synergy_score
                    )
                    pollinations.append(pollination)

        self.cross_pollinations.extend(pollinations)
        return pollinations

    def _calculate_base_synergy(self, mind_1_id: str, mind_2_id: str) -> float:
        """Calculate base synergy between two minds."""
        # Extract domains from IDs
        domain_1 = mind_1_id.split('_')[0] if '_' in mind_1_id else mind_1_id
        domain_2 = mind_2_id.split('_')[0] if '_' in mind_2_id else mind_2_id

        # Complementary pairs
        complementary_pairs = {
            ("physics", "mathematics"): 0.85,
            ("empathy", "ethics"): 0.80,
            ("politics", "philosophy"): 0.75,
            ("poetry", "creative"): 0.90,
            ("causal", "physics"): 0.70,
            ("causal", "mathematics"): 0.75,
        }

        # Check both orders
        key = (domain_1, domain_2)
        if key in complementary_pairs:
            return complementary_pairs[key]

        key_rev = (domain_2, domain_1)
        if key_rev in complementary_pairs:
            return complementary_pairs[key_rev]

        # Same domain - moderate synergy
        if domain_1 == domain_2:
            return 0.5

        # Default - low synergy
        return 0.3

    def _should_provide_input(self, mind1: Any, mind2: Any, query: str) -> bool:
        """Determine if mind1 should provide input to mind2."""
        # Analytical minds provide input to intuitive minds
        if mind1.reasoning_style.value == "formal" and mind2.reasoning_style.value == "intuitive":
            return True

        # Factual minds provide input to creative minds
        if mind1.domain.value in ["physics", "mathematics"] and mind2.domain.value in ["poetry", "creative"]:
            return True

        return False

    def _assign_role(self, mind: Any, query: str, team: List[Any]) -> str:
        """Assign role to a mind in the collaboration."""
        domain = mind.domain.value

        roles = {
            "physics": "Analyze physical mechanisms",
            "mathematics": "Provide formal structure",
            "empathy": "Consider human impact",
            "politics": "Analyze social dynamics",
            "poetry": "Explore metaphorical meaning",
            "causal": "Identify causal relationships",
            "creative": "Generate novel approaches"
        }

        return roles.get(domain, "Provide perspective")

    def _create_synthesis(self, result1: Any, result2: Any) -> str:
        """Create synthesis of two mind results."""
        return f"Synthesis of {result1.mind_id} and {result2.mind_id}: " + \
               f"Combining {result1.result} with {result2.result}"

    def update_synergy_model(
        self,
        mind_1_id: str,
        mind_2_id: str,
        success: float,
        collaboration_type: str
    ) -> None:
        """
        Update synergy model based on collaboration outcome.

        Args:
            mind_1_id: First mind ID
            mind_2_id: Second mind ID
            success: Success score (0.0 to 1.0)
            collaboration_type: Type of collaboration
        """
        key = tuple(sorted([mind_1_id, mind_2_id]))

        if key not in self.synergy_models:
            # Create new model
            self.synergy_models[key] = SynergyModel(
                mind_1_id=mind_1_id,
                mind_2_id=mind_2_id,
                synergy_type=SynergyType.COMPLEMENTARY,
                strength=0.5,
                success_rate=success,
                last_updated=time.time(),
                collaboration_count=1,
                examples=[collaboration_type]
            )
        else:
            # Update existing model
            model = self.synergy_models[key]
            model.collaboration_count += 1

            # Update success rate (moving average)
            model.success_rate = 0.9 * model.success_rate + 0.1 * success

            # Update strength based on success
            model.strength = 0.8 * model.strength + 0.2 * model.success_rate

            model.last_updated = time.time()
            if len(model.examples) < 10:
                model.examples.append(collaboration_type)

    def get_synergy_matrix(self, mind_ids: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Get synergy matrix for a set of minds.

        Args:
            mind_ids: List of mind IDs

        Returns:
            Dictionary mapping (mind_1, mind_2) to synergy score
        """
        matrix = {}

        for m1 in mind_ids:
            matrix[m1] = {}
            for m2 in mind_ids:
                if m1 != m2:
                    matrix[m1][m2] = self.predict_synergy(m1, m2)
                else:
                    matrix[m1][m2] = 1.0

        return matrix

    def get_team_composition_summary(
        self,
        mind_ids: List[str]
    ) -> Dict[str, Any]:
        """Get summary of team composition."""
        total_synergy = 0.0
        pair_count = 0

        for i, m1 in enumerate(mind_ids):
            for m2 in mind_ids[i+1:]:
                total_synergy += self.predict_synergy(m1, m2)
                pair_count += 1

        avg_synergy = total_synergy / pair_count if pair_count > 0 else 0.0

        return {
            "team_size": len(mind_ids),
            "average_pairwise_synergy": avg_synergy,
            "total_synergy": total_synergy,
            "coordination_complexity": len(mind_ids) * (len(mind_ids) - 1) / 2
        }

    def recommend_team_for_task(
        self,
        task_description: str,
        available_minds: List[Any],
        max_team_size: int = 5
    ) -> List[str]:
        """
        Recommend optimal team for a specific task.

        Args:
            task_description: Description of the task
            available_minds: Available minds
            max_team_size: Maximum team size

        Returns:
            Recommended team members
        """
        # Calculate task relevance
        mind_relevance = {}
        for mind in available_minds:
            mind_relevance[mind.mind_id] = mind.calculate_relevance(task_description)

        # Filter minds with minimum relevance
        relevant_minds = [
            m for m in available_minds
            if mind_relevance[m.mind_id] > 0.3
        ]

        if not relevant_minds:
            return [available_minds[0].mind_id]

        # Optimize team size (balance between coverage and complexity)
        optimal_size = min(len(relevant_minds), max_team_size, 4)

        return self.optimize_collaboration(
            query=task_description,
            available_minds=relevant_minds,
            target_count=optimal_size
        )


# =============================================================================
# Factory Functions
# =============================================================================

def create_mind_synergy() -> MindSynergy:
    """Create a mind synergy manager."""
    return MindSynergy()
