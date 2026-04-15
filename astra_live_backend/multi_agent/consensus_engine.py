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
ASTRA V9.0 — Consensus Engine
Aggregates agent opinions and reaches consensus through various voting schemes.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time

from .collaboration_protocol import AgentMessage, DiscussionContext, MessageType
from .agent_factory import AgentRole, AgentOpinion


class ConsensusMethod(Enum):
    """Methods for reaching consensus."""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_VOTE = "weighted_vote"
    EXPERTISE_WEIGHTED = "expertise_weighted"
    BAYESIAN_CONSENSUS = "bayesian_consensus"
    DELPHI_METHOD = "delphi_method"
    CONDORCET = "condorcet"
    Borda_COUNT = "borda_count"


@dataclass
class ConsensusResult:
    """Result of consensus calculation."""
    consensus_reached: bool
    consensus_position: str
    confidence: float
    agreement_level: float  # 0-1, how much agents agree
    voting_breakdown: Dict[str, int]
    agent_positions: Dict[str, str]
    reasoning_summary: str
    alternative_proposals: List[str]
    timestamp: float = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "consensus_reached": self.consensus_reached,
            "consensus_position": self.consensus_position,
            "confidence": self.confidence,
            "agreement_level": self.agreement_level,
            "voting_breakdown": self.voting_breakdown,
            "agent_positions": self.agent_positions,
            "reasoning_summary": self.reasoning_summary,
            "alternative_proposals": self.alternative_proposals,
            "timestamp": self.timestamp or time.time()
        }


class ConsensusEngine:
    """
    Aggregates opinions from multiple agents and computes consensus.

    Supports multiple consensus methods with configurable parameters.
    """

    def __init__(self, default_method: ConsensusMethod = ConsensusMethod.WEIGHTED_VOTE):
        self.default_method = default_method
        self.consensus_threshold = 0.7  # Require 70% agreement
        self.agreement_tolerance = 0.3  # For quantitative agreement
        self.expertise_weights = {
            AgentRole.THEORIST: 1.0,
            AgentRole.EMPIRICIST: 1.0,
            AgentRole.EXPERIMENTALIST: 0.9,
            AgentRole.MATHEMATICIAN: 0.9,
            AgentRole.SKEPTIC: 0.8,  # Lower weight for skeptic
            AgentRole.SYNTHESIZER: 1.1  # Higher weight for synthesizer
        }

    def compute_consensus(self, opinions: List[AgentOpinion],
                          discussion_context: Optional[DiscussionContext] = None,
                          method: Optional[ConsensusMethod] = None) -> ConsensusResult:
        """Compute consensus from agent opinions using specified method."""
        if not opinions:
            return self._no_consensus_result("No opinions provided")

        method = method or self.default_method

        if method == ConsensusMethod.MAJORITY_VOTE:
            return self._majority_vote_consensus(opinions)
        elif method == ConsensusMethod.WEIGHTED_VOTE:
            return self._weighted_vote_consensus(opinions)
        elif method == ConsensusMethod.EXPERTISE_WEIGHTED:
            return self._expertise_weighted_consensus(opinions)
        elif method == ConsensusMethod.BAYESIAN_CONSENSUS:
            return self._bayesian_consensus(opinions)
        elif method == ConsensusMethod.DELPHI_METHOD:
            return self._delphi_consensus(opinions, discussion_context)
        else:
            return self._weighted_vote_consensus(opinions)

    def _majority_vote_consensus(self, opinions: List[AgentOpinion]) -> ConsensusResult:
        """Simple majority vote: position with most votes wins."""
        # Count votes
        position_counts = {}
        agent_positions = {}

        for opinion in opinions:
            position = opinion.position
            position_counts[position] = position_counts.get(position, 0) + 1
            agent_positions[opinion.agent_id] = position

        # Find winner
        total_votes = len(opinions)
        winning_position = max(position_counts.items(), key=lambda x: x[1])[0]
        winning_votes = position_counts[winning_position]

        # Check if consensus reached
        consensus_reached = (winning_votes / total_votes) >= self.consensus_threshold

        # Calculate agreement level
        agreement_level = winning_votes / total_votes

        # Generate reasoning summary
        summary = self._generate_reasoning_summary(opinions, winning_position)

        return ConsensusResult(
            consensus_reached=consensus_reached,
            consensus_position=winning_position,
            confidence=agreement_level,
            agreement_level=agreement_level,
            voting_breakdown=position_counts,
            agent_positions=agent_positions,
            reasoning_summary=summary,
            alternative_proposals=self._extract_alternatives(opinions),
            timestamp=time.time()
        )

    def _weighted_vote_consensus(self, opinions: List[AgentOpinion]) -> ConsensusResult:
        """Weighted vote: each agent's vote weighted by expertise and confidence."""
        position_scores = {}
        position_weights = {}
        agent_positions = {}

        for opinion in opinions:
            position = opinion.position
            agent_positions[opinion.agent_id] = position

            # Weight = expertise weight * confidence
            role = opinion.agent_role
            expertise_weight = self.expertise_weights.get(role, 1.0)
            weight = expertise_weight * opinion.confidence

            position_weights[position] = position_weights.get(position, 0) + weight

        # Find winner by weighted score
        winning_position = max(position_weights.items(), key=lambda x: x[1])[0]
        winning_weight = position_weights[winning_position]
        total_weight = sum(position_weights.values())

        # Check if consensus reached
        consensus_reached = (winning_weight / total_weight) >= self.consensus_threshold

        # Calculate agreement level
        agreement_level = winning_weight / total_weight if total_weight > 0 else 0

        # Generate reasoning summary
        summary = self._generate_reasoning_summary(opinions, winning_position)

        return ConsensusResult(
            consensus_reached=consensus_reached,
            consensus_position=winning_position,
            confidence=agreement_level,
            agreement_level=agreement_level,
            voting_breakdown=self._convert_weights_to_counts(opinions, position_weights),
            agent_positions=agent_positions,
            reasoning_summary=summary,
            alternative_proposals=self._extract_alternatives(opinions),
            timestamp=time.time()
        )

    def _expertise_weighted_consensus(self, opinions: List[AgentOpinion]) -> ConsensusResult:
        """Expertise-weighted consensus: domain expertise weights agent votes."""
        position_scores = {}
        agent_positions = {}

        # Get domain from first opinion (assuming single domain discussion)
        domain = opinions[0].reasoning.split()[0] if opinions else "general"

        for opinion in opinions:
            position = opinion.position
            agent_positions[opinion.agent_id] = position

            # Get domain-specific confidence
            role = opinion.agent_role
            domain_confidence = 0.5  # Default

            # Adjust based on role-domain match
            if role == AgentRole.THEORIST and "theoretical" in opinion.reasoning.lower():
                domain_confidence = 0.9
            elif role == AgentRole.EMPIRICIST and "data" in opinion.reasoning.lower():
                domain_confidence = 0.9
            elif role == AgentRole.EXPERIMENTALIST and "test" in opinion.reasoning.lower():
                domain_confidence = 0.9
            elif role == AgentRole.MATHEMATICIAN and "mathematical" in opinion.reasoning.lower():
                domain_confidence = 0.9

            # Combine expertise weight with domain confidence
            expertise_weight = self.expertise_weights.get(role, 1.0)
            weight = expertise_weight * domain_confidence * opinion.confidence

            position_scores[position] = position_scores.get(position, 0) + weight

        # Find winner
        if not position_scores:
            return self._no_consensus_result("No valid opinions")

        winning_position = max(position_scores.items(), key=lambda x: x[1])[0]
        winning_score = position_scores[winning_position]
        total_score = sum(position_scores.values())

        # Check consensus
        consensus_reached = (winning_score / total_score) >= self.consensus_threshold

        return ConsensusResult(
            consensus_reached=consensus_reached,
            consensus_position=winning_position,
            confidence=winning_score / total_score if total_score > 0 else 0,
            agreement_level=winning_score / total_score if total_score > 0 else 0,
            voting_breakdown=self._convert_scores_to_counts(opinions, position_scores),
            agent_positions=agent_positions,
            reasoning_summary=self._generate_reasoning_summary(opinions, winning_position),
            alternative_proposals=self._extract_alternatives(opinions),
            timestamp=time.time()
        )

    def _bayesian_consensus(self, opinions: List[AgentOpinion]) -> ConsensusResult:
        """
        Bayesian consensus: combine opinions as probabilistic beliefs.

        Treats each agent's opinion as a Bayesian belief update.
        """
        # Convert positions to numeric scores
        position_scores = {"support": 1.0, "oppose": -1.0, "neutral": 0.0, "abstain": 0.0}

        # Aggregate weighted scores
        total_score = 0.0
        total_weight = 0.0
        agent_positions = {}

        for opinion in opinions:
            position = opinion.position
            agent_positions[opinion.agent_id] = position

            if position not in position_scores:
                continue

            # Weight by confidence and expertise
            role = opinion.agent_role
            expertise_weight = self.expertise_weights.get(role, 1.0)
            weight = expertise_weight * opinion.confidence

            score = position_scores[position] * weight
            total_score += score
            total_weight += weight

        if total_weight == 0:
            return self._no_consensus_result("No valid weighted opinions")

        # Average score
        avg_score = total_score / total_weight

        # Convert back to position
        if avg_score > 0.5:
            consensus_position = "support"
        elif avg_score < -0.5:
            consensus_position = "oppose"
        else:
            consensus_position = "neutral"

        # Confidence based on distance from neutral
        confidence = abs(avg_score)

        # Agreement level based on variance
        variance = self._calculate_opinion_variance(opinions)
        agreement_level = 1.0 - min(variance, 1.0)

        # Count positions
        position_counts = {}
        for opinion in opinions:
            pos = opinion.position
            position_counts[pos] = position_counts.get(pos, 0) + 1

        return ConsensusResult(
            consensus_reached=confidence >= self.consensus_threshold,
            consensus_position=consensus_position,
            confidence=confidence,
            agreement_level=agreement_level,
            voting_breakdown=position_counts,
            agent_positions=agent_positions,
            reasoning_summary=self._generate_reasoning_summary(opinions, consensus_position),
            alternative_proposals=self._extract_alternatives(opinions),
            timestamp=time.time()
        )

    def _delphi_consensus(self, opinions: List[AgentOpinion],
                          discussion: Optional[DiscussionContext] = None) -> ConsensusResult:
        """
        Delphi method: iterative consensus with controlled feedback.

        Simulates multiple rounds of anonymous feedback and revision.
        """
        # Start with initial positions
        current_positions = {op.agent_id: op.position for op in opinions}
        confidences = {op.agent_id: op.confidence for op in opinions}

        # Simulate Delphi rounds (convergence process)
        max_rounds = 3
        for round_num in range(max_rounds):
            # Calculate median position
            position_values = {"support": 1.0, "oppose": -1.0, "neutral": 0.0}
            numeric_positions = [position_values.get(pos, 0) for pos in current_positions.values()]

            if not numeric_positions:
                break

            median_position = np.median(numeric_positions)

            # Agents update positions toward median
            for agent_id, position in current_positions.items():
                current_value = position_values.get(position, 0)
                # Move 30% toward median
                new_value = current_value + 0.3 * (median_position - current_value)

                # Convert back to position
                if new_value > 0.3:
                    current_positions[agent_id] = "support"
                elif new_value < -0.3:
                    current_positions[agent_id] = "oppose"
                else:
                    current_positions[agent_id] = "neutral"

            # Increase confidence through convergence
            for agent_id in confidences:
                confidences[agent_id] = min(0.95, confidences[agent_id] * 1.1)

        # Count final positions
        position_counts = {}
        for position in current_positions.values():
            position_counts[position] = position_counts.get(position, 0) + 1

        # Find consensus
        total_votes = len(current_positions)
        winning_position = max(position_counts.items(), key=lambda x: x[1])[0]
        winning_votes = position_counts[winning_position]

        consensus_reached = (winning_votes / total_votes) >= self.consensus_threshold
        agreement_level = winning_votes / total_votes

        # Use average confidence
        avg_confidence = np.mean(list(confidences.values()))

        return ConsensusResult(
            consensus_reached=consensus_reached,
            consensus_position=winning_position,
            confidence=avg_confidence,
            agreement_level=agreement_level,
            voting_breakdown=position_counts,
            agent_positions=current_positions,
            reasoning_summary=f"Delphi method (3 rounds): Convergence toward {winning_position}",
            alternative_proposals=self._extract_alternatives(opinions),
            timestamp=time.time()
        )

    def _calculate_opinion_variance(self, opinions: List[AgentOpinion]) -> float:
        """Calculate variance in opinions (0 = consensus, 1 = maximum disagreement)."""
        if not opinions:
            return 0.0

        # Convert positions to numeric
        position_values = {"support": 1.0, "oppose": -1.0, "neutral": 0.0, "abstain": 0.0}
        numeric_opinions = []

        for opinion in opinions:
            value = position_values.get(opinion.position, 0)
            numeric_opinions.append(value)

        if not numeric_opinions:
            return 0.0

        # Calculate variance
        mean = np.mean(numeric_opinions)
        variance = np.var(numeric_opinions)

        # Normalize to 0-1 range (maximum variance is when half support, half oppose)
        max_variance = 1.0  # Variance when values are -1 and 1
        normalized_variance = variance / max_variance

        return min(normalized_variance, 1.0)

    def _generate_reasoning_summary(self, opinions: List[AgentOpinion],
                                    consensus_position: str) -> str:
        """Generate summary of reasoning behind consensus."""
        # Get reasoning for agents in consensus
        consensus_reasoning = []
        other_reasoning = []

        for opinion in opinions:
            if opinion.position == consensus_position:
                consensus_reasoning.append(opinion.reasoning[:100])
            else:
                other_reasoning.append(opinion.reasoning[:100])

        summary = f"Consensus: {consensus_position}. "

        if consensus_reasoning:
            summary += f"Supporting arguments: {'; '.join(consensus_reasoning[:2])}. "

        if other_reasoning:
            summary += f"Counter-arguments: {'; '.join(other_reasoning[:2])}."

        # Add role-specific insights
        role_insights = self._get_role_insights(opinions)
        if role_insights:
            summary += f" Key insights: {role_insights}"

        return summary

    def _get_role_insights(self, opinions: List[AgentOpinion]) -> str:
        """Extract key insights from each role."""
        insights_by_role = {}

        for opinion in opinions:
            role = opinion.agent_role.value
            if role not in insights_by_role:
                # Extract key point from reasoning
                reasoning = opinion.reasoning
                if reasoning:
                    # Get first sentence or first 80 chars
                    if '.' in reasoning:
                        key_point = reasoning.split('.')[0] + '.'
                    else:
                        key_point = reasoning[:80] + '...'

                    insights_by_role[role] = key_point

        # Combine insights
        combined = "; ".join([f"{role}: {insight}" for role, insight in insights_by_role.items()])
        return combined

    def _extract_alternatives(self, opinions: List[AgentOpinion]) -> List[str]:
        """Extract alternative proposals from opinions."""
        alternatives = []

        for opinion in opinions:
            if opinion.alternative_proposals:
                alternatives.extend(opinion.alternative_proposals)

        # Deduplicate while preserving order
        seen = set()
        unique_alternatives = []
        for alt in alternatives:
            if alt not in seen:
                seen.add(alt)
                unique_alternatives.append(alt)

        return unique_alternatives[:5]  # Top 5 alternatives

    def _convert_weights_to_counts(self, opinions: List[AgentOpinion],
                                   weights: Dict[str, float]) -> Dict[str, int]:
        """Convert weighted votes to integer counts for display."""
        # Find minimum weight for normalization
        min_weight = min(weights.values()) if weights else 1.0

        counts = {}
        for position, weight in weights.items():
            # Round to nearest integer, minimum 1
            count = max(1, round(weight / min_weight))
            counts[position] = count

        return counts

    def _convert_scores_to_counts(self, opinions: List[AgentOpinion],
                                  scores: Dict[str, float]) -> Dict[str, int]:
        """Convert scores to integer counts for display."""
        if not scores:
            return {}

        # Find minimum absolute score
        min_score = min(abs(s) for s in scores.values() if s != 0)

        counts = {}
        for position, score in scores.items():
            if score != 0:
                count = max(1, round(abs(score) / min_score))
                counts[position] = count

        return counts

    def _no_consensus_result(self, reason: str) -> ConsensusResult:
        """Create a result indicating no consensus."""
        return ConsensusResult(
            consensus_reached=False,
            consensus_position="neutral",
            confidence=0.0,
            agreement_level=0.0,
            voting_breakdown={},
            agent_positions={},
            reasoning_summary=f"No consensus reached: {reason}",
            alternative_proposals=[],
            timestamp=time.time()
        )


class ConflictResolver:
    """
    Resolves conflicts between agent opinions.

    Identifies fundamental disagreements and proposes resolution strategies.
    """

    def __init__(self):
        self.resolution_strategies = {
            "theoretical_empirical": "Propose experimental test",
            "mathematical_consistency": "Verify dimensional analysis",
            "assumption_challenge": "Identify and test assumptions",
            "methodological": "Compare method performance"
        }

    def identify_conflicts(self, opinions: List[AgentOpinion]) -> List[Dict[str, Any]]:
        """Identify fundamental conflicts between opinions."""
        conflicts = []

        # Group by position
        supporters = [op for op in opinions if op.position == "support"]
        opposers = [op for op in opinions if op.position == "oppose"]

        # Check for theoretical-empirical conflict
        theorist_support = [op for op in supporters if op.agent_role == AgentRole.THEORIST]
        empiricist_oppose = [op for op in opposers if op.agent_role == AgentRole.EMPIRICIST]

        if theorist_support and empiricist_oppose:
            conflicts.append({
                "type": "theoretical_empirical",
                "description": "Theoretical support without empirical validation",
                "agents": [op.agent_id for op in theorist_support + empiricist_oppose],
                "severity": "high"
            })

        # Check for mathematical inconsistency
        mathematician_oppose = [op for op in opposers if op.agent_role == AgentRole.MATHEMATICIAN]
        if supporters and mathematician_oppose:
            conflicts.append({
                "type": "mathematical_consistency",
                "description": "Mathematical concerns with proposal",
                "agents": [op.agent_id for op in supporters + mathematician_oppose],
                "severity": "medium"
            })

        # Check for assumption challenges
        skeptic_oppose = [op for op in opposers if op.agent_role == AgentRole.SKEPTIC]
        if supporters and skeptic_oppose:
            conflicts.append({
                "type": "assumption_challenge",
                "description": "Unproven assumptions identified",
                "agents": [op.agent_id for op in supporters + skeptic_oppose],
                "severity": "low"
            })

        return conflicts

    def propose_resolution(self, conflict: Dict[str, Any],
                         opinions: List[AgentOpinion]) -> Dict[str, Any]:
        """Propose resolution strategy for a conflict."""
        conflict_type = conflict["type"]
        strategy = self.resolution_strategies.get(conflict_type, "Further discussion needed")

        resolution = {
            "conflict_type": conflict_type,
            "strategy": strategy,
            "actions": []
        }

        if conflict_type == "theoretical_empirical":
            resolution["actions"] = [
                "Design experimental test to validate theoretical prediction",
                "Estimate required observational sensitivity",
                "Assess feasibility with current instruments"
            ]

        elif conflict_type == "mathematical_consistency":
            resolution["actions"] = [
                "Perform dimensional analysis",
                "Check mathematical derivations",
                "Verify consistency with established theories"
            ]

        elif conflict_type == "assumption_challenge":
            resolution["actions"] = [
                "Identify all implicit assumptions",
                "Test sensitivity to assumption violations",
                "Consider alternative assumptions"
            ]

        return resolution

    def calculate_disagreement_score(self, opinions: List[AgentOpinion]) -> float:
        """Calculate overall disagreement score (0 = consensus, 1 = maximum disagreement)."""
        if not opinions:
            return 0.0

        # Calculate variance using consensus engine method
        consensus_engine = ConsensusEngine()
        variance = consensus_engine._calculate_opinion_variance(opinions)

        # Also consider role disagreement
        role_disagreement = 0.0
        unique_roles = set(op.agent_role for op in opinions)

        if len(unique_roles) > 1:
            # Check if roles disagree
            role_positions = {}
            for role in unique_roles:
                role_opinions = [op for op in opinions if op.agent_role == role]
                if role_opinions:
                    # Get majority position for this role
                    positions = [op.position for op in role_opinions]
                    role_positions[role] = max(set(positions), key=positions.count)

            # Count unique role positions
            unique_role_positions = set(role_positions.values())
            role_disagreement = len(unique_role_positions) / len(role_positions)

        # Combine variance and role disagreement
        disagreement_score = 0.7 * variance + 0.3 * role_disagreement

        return min(disagreement_score, 1.0)


# Utility functions
def format_consensus_result(result: ConsensusResult) -> str:
    """Format consensus result for display."""
    status = "✓ CONSENSUS" if result.consensus_reached else "✗ NO CONSENSUS"

    output = f"{status}: {result.consensus_position.upper()}\n"
    output += f"Confidence: {result.confidence:.2f} | Agreement: {result.agreement_level:.2f}\n"
    output += f"Vote breakdown: {result.voting_breakdown}\n"
    output += f"\nReasoning: {result.reasoning_summary[:200]}..."

    if result.alternative_proposals:
        output += f"\n\nAlternatives: {'; '.join(result.alternative_proposals[:3])}"

    return output


def compare_consensus_methods(opinions: List[AgentOpinion]) -> Dict[str, ConsensusResult]:
    """Compare results from different consensus methods."""
    engine = ConsensusEngine()

    results = {}
    for method in ConsensusMethod:
        try:
            result = engine.compute_consensus(opinions, method=method)
            results[method.value] = result
        except Exception as e:
            # Create error result
            results[method.value] = ConsensusResult(
                consensus_reached=False,
                consensus_position="error",
                confidence=0.0,
                agreement_level=0.0,
                voting_breakdown={},
                agent_positions={},
                reasoning_summary=f"Error: {str(e)}",
                alternative_proposals=[],
                timestamp=time.time()
            )

    return results
