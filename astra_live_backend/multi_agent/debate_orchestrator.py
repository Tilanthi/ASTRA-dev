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
ASTRA V9.0 — Debate Orchestrator
Orchestrates structured scientific debates between specialized agents.
"""

import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .agent_factory import ScientificAgent, AgentRole, AgentOpinion
from .collaboration_protocol import (
    CollaborationProtocol, DebateProtocol, DiscussionContext,
    AgentMessage, MessageType
)
from .consensus_engine import ConsensusEngine, ConsensusResult, ConflictResolver


class DebatePhase(Enum):
    """Phases of structured scientific debate."""
    OPENING = "opening"           # Initial positions
    REBUTTAL = "rebuttal"         # Challenge and respond
    CLARIFICATION = "clarification"  # Evidence and clarification
    SYNTHESIS = "synthesis"        # Final integration
    CONCLUDED = "concluded"


@dataclass
class DebateConfig:
    """Configuration for debate parameters."""
    max_rounds: int = 5
    phase_time_limit: float = 300.0  # seconds per phase
    response_timeout: float = 60.0     # seconds for response
    consensus_threshold: float = 0.7
    allow_interruptions: bool = False
    require_evidence: bool = True
    track_reasoning: bool = True


@dataclass
class DebateResult:
    """Result of completed debate."""
    debate_id: str
    question: str
    participants: List[str]
    phases_completed: List[str]
    final_consensus: ConsensusResult
    total_messages: int
    duration_seconds: float
    key_insights: List[str]
    conflicts_identified: List[Dict[str, Any]]
    resolutions_proposed: List[Dict[str, Any]]
    recommendation: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class DebateOrchestrator:
    """
    Orchestrates structured scientific debates between specialized agents.

    Manages debate flow, enforces protocols, tracks progress, and
    ensures productive scientific discussion.
    """

    def __init__(self, config: Optional[DebateConfig] = None):
        self.config = config or DebateConfig()
        self.protocol = DebateProtocol()
        self.consensus_engine = ConsensusEngine()
        self.conflict_resolver = ConflictResolver()

        self.active_debates: Dict[str, DiscussionContext] = {}
        self.debate_history: List[DebateResult] = []
        self.agent_registry: Dict[str, ScientificAgent] = {}

    def register_agent(self, agent: ScientificAgent) -> str:
        """Register an agent for participation in debates."""
        self.agent_registry[agent.id] = agent
        return agent.id

    def start_debate(self, question: str, participants: List[str],
                    moderator_id: Optional[str] = None) -> str:
        """Start a new structured scientific debate."""
        # Validate participants
        for participant_id in participants:
            if participant_id not in self.agent_registry:
                raise ValueError(f"Agent {participant_id} not registered")

        # Create debate discussion
        debate = self.protocol.start_debate(question, participants, moderator_id)
        self.active_debates[debate.id] = debate

        # Initialize opening statements
        self._initialize_opening_statements(debate)

        return debate.id

    def _initialize_opening_statements(self, debate: DiscussionContext):
        """Request opening statements from all participants."""
        for participant_id in debate.participants:
            agent = self.agent_registry[participant_id]

            # Request initial analysis
            context = {
                "data_sources": [],  # Will be populated from system
                "discussion_type": "debate_opening"
            }

            try:
                opinion = agent.analyze(debate.question, context)

                # Convert to message
                message = AgentMessage(
                    type=MessageType.OPINION,
                    sender_id=participant_id,
                    content={
                        "position": opinion.position,
                        "confidence": opinion.confidence,
                        "reasoning": opinion.reasoning,
                        "evidence": opinion.evidence,
                        "agent_role": opinion.agent_role.value
                    },
                    context_id=debate.id
                )

                self.protocol.send_message(message, debate.id)

            except Exception as e:
                # Handle error
                error_message = AgentMessage(
                    type=MessageType.OPINION,
                    sender_id=participant_id,
                    content={
                        "position": "neutral",
                        "confidence": 0.0,
                        "reasoning": f"Unable to provide analysis: {str(e)}",
                        "error": str(e)
                    },
                    context_id=debate.id
                )

                self.protocol.send_message(error_message, debate.id)

    def advance_debate(self, debate_id: str) -> Optional[str]:
        """Advance debate to next phase."""
        debate = self.active_debates.get(debate_id)
        if not debate:
            return None

        # Get current phase
        current_phase = debate.metadata.get("phase", "opening")
        current_round = debate.metadata.get("round", 0)

        # Check if debate should conclude
        if current_phase == "synthesis":
            return self.conclude_debate(debate_id)

        # Check round limit
        if current_round >= self.config.max_rounds:
            return self.conclude_debate(debate_id)

        # Advance phase
        new_phase = self.protocol.advance_debate_phase(debate_id)

        if new_phase:
            # Process phase-specific actions
            if new_phase == "rebuttal":
                self._process_rebuttal_phase(debate)
            elif new_phase == "clarification":
                self._process_clarification_phase(debate)
            elif new_phase == "synthesis":
                self._process_synthesis_phase(debate)

            # Increment round if completing full cycle
            if current_phase == "clarification":
                debate.metadata["round"] = current_round + 1

        return new_phase

    def _process_rebuttal_phase(self, debate: DiscussionContext):
        """Process rebuttal phase: agents respond to each other."""
        opinions = debate.get_opinions()

        # Have each agent respond to others' opinions
        for participant_id in debate.participants:
            agent = self.agent_registry[participant_id]

            # Get opinions from other agents
            other_opinions = [op for op in opinions if op.sender_id != participant_id]

            for other_opinion in other_opinions:
                try:
                    # Check if agent wants to respond
                    context = {
                        "agent_opinions": opinions,
                        "debate_phase": "rebuttal"
                    }

                    response = agent.respond_to_opinion(
                        AgentOpinion(
                            agent_id=other_opinion.content.get("sender_id", ""),
                            agent_role=AgentRole(other_opinion.content.get("agent_role", "synthesizer")),
                            position=other_opinion.content.get("position", "neutral"),
                            confidence=other_opinion.content.get("confidence", 0.5),
                            reasoning=other_opinion.content.get("reasoning", "")
                        ),
                        context
                    )

                    if response:
                        message = AgentMessage(
                            type=MessageType.OPINION,
                            sender_id=participant_id,
                            content={
                                "position": response.position,
                                "confidence": response.confidence,
                                "reasoning": response.reasoning,
                                "in_response_to": other_opinion.sender_id,
                                "agent_role": response.agent_role.value
                            },
                            reply_to=other_opinion.id,
                            context_id=debate.id
                        )

                        self.protocol.send_message(message, debate.id)

                except Exception as e:
                    # Continue with other agents
                    pass

    def _process_clarification_phase(self, debate: DiscussionContext):
        """Process clarification phase: agents request/provide evidence."""
        opinions = debate.get_opinions()

        # Identify claims needing evidence
        for opinion in opinions:
            position = opinion.content.get("position", "neutral")
            evidence = opinion.content.get("evidence", [])

            # If supporting with no evidence, request clarification
            if position == "support" and not evidence:
                # Have skeptic request evidence
                skeptic_id = self._find_agent_by_role(debate, AgentRole.SKEPTIC)

                if skeptic_id:
                    skeptic = self.agent_registry[skeptic_id]

                    try:
                        # Create evidence request
                        request = AgentMessage(
                            type=MessageType.REQUEST_ANALYSIS,
                            sender_id=skeptic_id,
                            receiver_id=opinion.sender_id,
                            content={
                                "request": "Please provide evidence supporting your position",
                                "target_claim": opinion.id
                            },
                            reply_to=opinion.id,
                            context_id=debate.id,
                            requires_response=True
                        )

                        self.protocol.send_message(request, debate.id)

                    except Exception as e:
                        pass

    def _process_synthesis_phase(self, debate: DiscussionContext):
        """Process synthesis phase: synthesizer integrates all perspectives."""
        # Find synthesizer
        synthesizer_id = self._find_agent_by_role(debate, AgentRole.SYNTHESIZER)

        if not synthesizer_id:
            return

        synthesizer = self.agent_registry[synthesizer_id]

        # Get all opinions for synthesis
        opinions = debate.get_opinions()
        agent_opinions = []

        for msg in opinions:
            try:
                agent_opinions.append(AgentOpinion(
                    agent_id=msg.sender_id,
                    agent_role=AgentRole(msg.content.get("agent_role", "synthesizer")),
                    position=msg.content.get("position", "neutral"),
                    confidence=msg.content.get("confidence", 0.5),
                    reasoning=msg.content.get("reasoning", "")
                ))
            except Exception:
                continue

        # Create synthesis context
        context = {
            "agent_opinions": agent_opinions,
            "debate_phase": "synthesis"
        }

        try:
            synthesis = synthesizer.analyze(debate.question, context)

            message = AgentMessage(
                type=MessageType.SYNTHESIS,
                sender_id=synthesizer_id,
                content={
                    "position": synthesis.position,
                    "confidence": synthesis.confidence,
                    "reasoning": synthesis.reasoning,
                    "synthesis": True,
                    "agent_role": synthesis.agent_role.value
                },
                context_id=debate.id,
                priority=9  # High priority
            )

            self.protocol.send_message(message, debate.id)

        except Exception as e:
            pass

    def conclude_debate(self, debate_id: str) -> Optional[DebateResult]:
        """Conclude debate and compute final result."""
        debate = self.active_debates.get(debate_id)
        if not debate:
            return None

        # Convert messages to opinions
        opinions = []
        for msg in debate.get_opinions():
            try:
                opinions.append(AgentOpinion(
                    agent_id=msg.sender_id,
                    agent_role=AgentRole(msg.content.get("agent_role", "synthesizer")),
                    position=msg.content.get("position", "neutral"),
                    confidence=msg.content.get("confidence", 0.5),
                    reasoning=msg.content.get("reasoning", "")
                ))
            except Exception:
                continue

        # Compute final consensus
        consensus = self.consensus_engine.compute_consensus(opinions)

        # Identify conflicts
        conflicts = self.conflict_resolver.identify_conflicts(opinions)

        # Propose resolutions
        resolutions = []
        for conflict in conflicts:
            resolution = self.conflict_resolver.propose_resolution(conflict, opinions)
            resolutions.append(resolution)

        # Extract key insights
        key_insights = self._extract_key_insights(opinions)

        # Generate recommendation
        recommendation = self._generate_recommendation(consensus, conflicts, resolutions)

        # Create result
        result = DebateResult(
            debate_id=debate_id,
            question=debate.question,
            participants=debate.participants,
            phases_completed=list(set(
                msg.content.get("phase", "opening")
                for msg in debate.messages
                if msg.type == MessageType.QUESTION
            )),
            final_consensus=consensus,
            total_messages=len(debate.messages),
            duration_seconds=time.time() - debate.start_time,
            key_insights=key_insights,
            conflicts_identified=conflicts,
            resolutions_proposed=resolutions,
            recommendation=recommendation,
            metadata={
                "consensus_method": "weighted_vote",
                "agreement_level": consensus.agreement_level,
                "debate_rounds": debate.metadata.get("round", 0)
            }
        )

        # Mark debate as concluded
        self.protocol.conclude_discussion(debate_id, {"recommendation": recommendation})

        # Move to history
        del self.active_debates[debate_id]
        self.debate_history.append(result)

        return result

    def _find_agent_by_role(self, debate: DiscussionContext, role: AgentRole) -> Optional[str]:
        """Find agent with specific role in debate."""
        for participant_id in debate.participants:
            agent = self.agent_registry.get(participant_id)
            if agent and agent.role == role:
                return participant_id
        return None

    def _extract_key_insights(self, opinions: List[AgentOpinion]) -> List[str]:
        """Extract key insights from debate opinions."""
        insights = []

        # Get insights from each role
        role_insights = {}

        for opinion in opinions:
            role = opinion.agent_role
            if role not in role_insights:
                # Extract first sentence or first 100 chars
                reasoning = opinion.reasoning
                if '.' in reasoning:
                    insight = reasoning.split('.')[0] + '.'
                else:
                    insight = reasoning[:100] + '...'

                role_insights[role] = insight

        # Convert to list
        insights = [f"{role.value}: {insight}" for role, insight in role_insights.items()]

        return insights[:5]  # Top 5 insights

    def _generate_recommendation(self, consensus: ConsensusResult,
                               conflicts: List[Dict[str, Any]],
                               resolutions: List[Dict[str, Any]]) -> str:
        """Generate recommendation based on debate outcome."""
        if consensus.consensus_reached:
            recommendation = f"Consensus reached on {consensus.consensus_position}. "
            recommendation += f"Recommend proceeding with {consensus.agreement_level:.0%} confidence. "

            if consensus.alternative_proposals:
                recommendation += f"Consider alternatives: {consensus.alternative_proposals[0]}."
        else:
            recommendation = "No consensus reached. "

            if conflicts:
                recommendation += f"Key conflict: {conflicts[0]['description']}. "
                recommendation += f"Proposed resolution: {resolutions[0]['strategy']}."
            else:
                recommendation += "Require further discussion or additional analysis."

        return recommendation

    def get_debate_status(self, debate_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of debate."""
        debate = self.active_debates.get(debate_id)
        if not debate:
            # Check history
            for result in self.debate_history:
                if result.debate_id == debate_id:
                    return {
                        "status": "concluded",
                        "result": result.to_dict() if hasattr(result, 'to_dict') else result
                    }
            return None

        status = self.protocol.get_discussion_status(debate_id)
        if status:
            status["current_round"] = debate.metadata.get("round", 0)
            status["max_rounds"] = self.config.max_rounds

        return status

    def get_debate_summary(self, debate_id: str) -> Optional[Dict[str, Any]]:
        """Get human-readable summary of debate."""
        # Check if debate is active
        status = self.get_debate_status(debate_id)

        if not status:
            return None

        if status.get("status") == "concluded":
            # Return summary of completed debate
            result = status.get("result")
            return {
                "debate_id": result.debate_id,
                "question": result.question,
                "status": "Concluded",
                "consensus": result.final_consensus.to_dict() if hasattr(result.final_consensus, 'to_dict') else result.final_consensus,
                "duration_minutes": result.duration_seconds / 60,
                "recommendation": result.recommendation,
                "key_insights": result.key_insights
            }

        # Active debate summary
        debate = self.active_debates.get(debate_id)
        if not debate:
            return None

        opinions = debate.get_opinions()

        # Count positions
        position_counts = {}
        agent_positions = {}

        for msg in opinions:
            position = msg.content.get("position", "unknown")
            position_counts[position] = position_counts.get(position, 0) + 1
            agent_positions[msg.sender_id] = position

        return {
            "debate_id": debate_id,
            "question": debate.question,
            "status": "In Progress",
            "current_phase": debate.metadata.get("phase", "opening"),
            "current_round": debate.metadata.get("round", 0),
            "max_rounds": self.config.max_rounds,
            "participants": debate.participants,
            "opinions_exchanged": len(opinions),
            "position_breakdown": position_counts,
            "agent_positions": agent_positions,
            "duration_minutes": (time.time() - debate.start_time) / 60
        }


class DebateMetrics:
    """Tracks metrics for debate evaluation and improvement."""

    def __init__(self):
        self.metrics = {
            "total_debates": 0,
            "consensus_reached": 0,
            "avg_debate_duration": 0.0,
            "avg_agreement_level": 0.0,
            "most_active_role": None,
            "role_participation": {}
        }

    def record_debate(self, result: DebateResult):
        """Record metrics from completed debate."""
        self.metrics["total_debates"] += 1

        if result.final_consensus.consensus_reached:
            self.metrics["consensus_reached"] += 1

        # Update average duration
        total_duration = self.metrics["avg_debate_duration"] * (self.metrics["total_debates"] - 1)
        total_duration += result.duration_seconds
        self.metrics["avg_debate_duration"] = total_duration / self.metrics["total_debates"]

        # Update average agreement level
        total_agreement = self.metrics["avg_agreement_level"] * (self.metrics["total_debates"] - 1)
        total_agreement += result.final_consensus.agreement_level
        self.metrics["avg_agreement_level"] = total_agreement / self.metrics["total_debates"]

        # Track role participation
        for participant_id in result.participants:
            role = participant_id.split('_')[0]  # Extract role from ID
            self.metrics["role_participation"][role] = \
                self.metrics["role_participation"].get(role, 0) + 1

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of debate metrics."""
        if self.metrics["total_debates"] == 0:
            return {"message": "No debates recorded yet"}

        consensus_rate = (self.metrics["consensus_reached"] /
                          self.metrics["total_debates"])

        return {
            "total_debates": self.metrics["total_debates"],
            "consensus_rate": f"{consensus_rate:.1%}",
            "avg_duration_minutes": self.metrics["avg_debate_duration"] / 60,
            "avg_agreement_level": self.metrics["avg_agreement_level"],
            "most_participatory_role": max(
                self.metrics["role_participation"].items(),
                key=lambda x: x[1]
            )[0] if self.metrics["role_participation"] else "N/A",
            "role_participation": self.metrics["role_participation"]
        }


# Factory function
def create_debate(config: Optional[DebateConfig] = None) -> DebateOrchestrator:
    """Create a new debate orchestrator with optional configuration."""
    return DebateOrchestrator(config)
