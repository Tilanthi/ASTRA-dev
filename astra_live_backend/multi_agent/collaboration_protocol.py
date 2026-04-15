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
ASTRA V9.0 — Multi-Agent Collaboration Protocol
Defines communication protocols and interaction patterns between specialized agents.
"""

import uuid
import time
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod


class MessageType(Enum):
    """Types of messages between agents."""
    OPINION = "opinion"
    QUESTION = "question"
    CHALLENGE = "challenge"
    SUPPORT = "support"
    SYNTHESIS = "synthesis"
    REQUEST_ANALYSIS = "request_analysis"
    PROVIDE_EVIDENCE = "provide_evidence"
    DEBATE_START = "debate_start"
    DEBATE_END = "debate_end"


class MessagePriority(Enum):
    """Priority levels for messages."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class AgentMessage:
    """Message between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.OPINION
    sender_id: str = ""
    receiver_id: str = ""  # Empty for broadcast
    priority: MessagePriority = MessagePriority.NORMAL
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    reply_to: Optional[str] = None
    context_id: Optional[str] = None  # Links messages in same discussion
    requires_response: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for transmission."""
        return {
            "id": self.id,
            "type": self.type.value,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "priority": self.priority.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "reply_to": self.reply_to,
            "context_id": self.context_id,
            "requires_response": self.requires_response
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=MessageType(data["type"]),
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            priority=MessagePriority(data["priority"]),
            content=data["content"],
            timestamp=data["timestamp"],
            reply_to=data.get("reply_to"),
            context_id=data.get("context_id"),
            requires_response=data.get("requires_response", False)
        )


@dataclass
class DiscussionContext:
    """Context for an ongoing discussion between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question: str = ""
    start_time: float = field(default_factory=time.time)
    messages: List[AgentMessage] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    status: str = "active"  # active, paused, concluded
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: AgentMessage):
        """Add message to discussion."""
        self.messages.append(message)
        if message.context_id is None:
            message.context_id = self.id

    def get_opinions(self) -> List[AgentMessage]:
        """Get all opinion messages in discussion."""
        return [m for m in self.messages if m.type == MessageType.OPINION]

    def get_participant_opinions(self, participant_id: str) -> List[AgentMessage]:
        """Get all opinions from a specific participant."""
        return [m for m in self.messages
                if m.type == MessageType.OPINION and m.sender_id == participant_id]


class CollaborationProtocol:
    """
    Manages communication protocols between agents.

    Implements structured debate, turn-taking, and evidence exchange.
    """

    def __init__(self):
        self.active_discussions: Dict[str, DiscussionContext] = {}
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.protocol_rules = {
            "max_debate_rounds": 5,
            "response_timeout": 60.0,  # seconds
            "min_participants": 3,
            "consensus_threshold": 0.7
        }
        self.communication_stats = {
            "total_messages": 0,
            "opinions_exchanged": 0,
            "debates_concluded": 0,
            "consensus_reached": 0
        }

    def create_discussion(self, question: str, participant_ids: List[str],
                         metadata: Optional[Dict[str, Any]] = None) -> DiscussionContext:
        """Create a new discussion context."""
        discussion = DiscussionContext(
            question=question,
            participants=participant_ids,
            metadata=metadata or {}
        )

        self.active_discussions[discussion.id] = discussion
        return discussion

    def broadcast_message(self, message: AgentMessage, discussion_id: str) -> List[AgentMessage]:
        """Broadcast message to all participants in discussion."""
        discussion = self.active_discussions.get(discussion_id)
        if not discussion:
            return []

        responses = []
        for participant_id in discussion.participants:
            # Don't send message back to sender
            if participant_id != message.sender_id:
                msg_copy = AgentMessage(
                    type=message.type,
                    sender_id=message.sender_id,
                    receiver_id=participant_id,
                    priority=message.priority,
                    content=message.content.copy(),
                    context_id=discussion_id,
                    reply_to=message.id
                )
                responses.append(msg_copy)

        # Add original message to discussion
        discussion.add_message(message)
        self.communication_stats["total_messages"] += 1

        return responses

    def send_message(self, message: AgentMessage, discussion_id: str) -> bool:
        """Send direct message to specific receiver."""
        discussion = self.active_discussions.get(discussion_id)
        if not discussion:
            return False

        discussion.add_message(message)
        self.communication_stats["total_messages"] += 1
        return True

    def get_discussion_status(self, discussion_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a discussion."""
        discussion = self.active_discussions.get(discussion_id)
        if not discussion:
            return None

        opinions = discussion.get_opinions()

        # Calculate discussion metrics
        support_count = sum(1 for o in opinions
                           if o.content.get("position") == "support")
        oppose_count = sum(1 for o in opinions
                          if o.content.get("position") == "oppose")
        neutral_count = sum(1 for o in opinions
                            if o.content.get("position") == "neutral")

        total_opinions = len(opinions)
        if total_opinions > 0:
            consensus_score = support_count / total_opinions
        else:
            consensus_score = 0.0

        return {
            "discussion_id": discussion.id,
            "question": discussion.question,
            "status": discussion.status,
            "participants": discussion.participants,
            "total_messages": len(discussion.messages),
            "opinions_exchanged": total_opinions,
            "support_count": support_count,
            "oppose_count": oppose_count,
            "neutral_count": neutral_count,
            "consensus_score": consensus_score,
            "consensus_reached": consensus_score >= self.protocol_rules["consensus_threshold"],
            "duration": time.time() - discussion.start_time
        }

    def conclude_discussion(self, discussion_id: str,
                           conclusion: Optional[str] = None) -> bool:
        """Conclude a discussion."""
        discussion = self.active_discussions.get(discussion_id)
        if not discussion:
            return False

        discussion.status = "concluded"

        if conclusion:
            discussion.metadata["conclusion"] = conclusion

        self.communication_stats["debates_concluded"] += 1

        # Check if consensus was reached
        status = self.get_discussion_status(discussion_id)
        if status and status["consensus_reached"]:
            self.communication_stats["consensus_reached"] += 1

        return True


class DebateProtocol(CollaborationProtocol):
    """
    Implements structured debate protocol for scientific discussions.

    Debate phases:
    1. Opening: Each agent presents initial analysis
    2. Rebuttal: Agents respond to and challenge others
    3. Clarification: Agents request and provide additional evidence
    4. Synthesis: Synthesizer integrates all perspectives
    """

    def __init__(self):
        super().__init__()
        self.debate_phases = ["opening", "rebuttal", "clarification", "synthesis"]
        self.current_phase = "opening"

    def start_debate(self, question: str, participants: List[str],
                     moderator_id: Optional[str] = None) -> DiscussionContext:
        """Start a structured scientific debate."""
        discussion = self.create_discussion(
            question=question,
            participant_ids=participants,
            metadata={
                "type": "debate",
                "phase": "opening",
                "moderator": moderator_id,
                "round": 0
            }
        )

        # Send debate start message
        start_message = AgentMessage(
            type=MessageType.DEBATE_START,
            sender_id=moderator_id or "system",
            content={
                "question": question,
                "phase": "opening",
                "instructions": "Present your initial analysis of the question"
            }
        )

        self.broadcast_message(start_message, discussion.id)

        return discussion

    def advance_debate_phase(self, discussion_id: str) -> Optional[str]:
        """Advance debate to next phase."""
        discussion = self.active_discussions.get(discussion_id)
        if not discussion:
            return None

        current_round = discussion.metadata.get("round", 0)
        current_phase_idx = self.debate_phases.index(
            discussion.metadata.get("phase", "opening")
        )

        # Move to next phase
        if current_phase_idx < len(self.debate_phases) - 1:
            next_phase = self.debate_phases[current_phase_idx + 1]
            discussion.metadata["phase"] = next_phase

            # Broadcast phase change
            phase_message = AgentMessage(
                type=MessageType.QUESTION,
                sender_id=discussion.metadata.get("moderator", "system"),
                content={
                    "phase": next_phase,
                    "instructions": self._get_phase_instructions(next_phase)
                }
            )

            self.broadcast_message(phase_message, discussion_id)

            return next_phase
        else:
            # Debate complete, move to synthesis
            self._start_synthesis_phase(discussion_id)
            return "synthesis"

    def _get_phase_instructions(self, phase: str) -> str:
        """Get instructions for a debate phase."""
        instructions = {
            "opening": "Present your initial analysis of the question",
            "rebuttal": "Respond to and challenge other agents' analyses",
            "clarification": "Request additional evidence or clarification from other agents",
            "synthesis": "Synthesizer will integrate all perspectives"
        }
        return instructions.get(phase, "Continue discussion")

    def _start_synthesis_phase(self, discussion_id: str):
        """Start final synthesis phase of debate."""
        discussion = self.active_discussions.get(discussion_id)
        if not discussion:
            return

        discussion.metadata["phase"] = "synthesis"

        # Find synthesizer participant
        synthesizer_id = None
        for participant_id in discussion.participants:
            if "synthesizer" in participant_id.lower():
                synthesizer_id = participant_id
                break

        if synthesizer_id:
            synthesis_request = AgentMessage(
                type=MessageType.SYNTHESIS,
                sender_id=discussion.metadata.get("moderator", "system"),
                receiver_id=synthesizer_id,
                content={
                    "instruction": "Integrate all perspectives and provide final synthesis",
                    "discussion_id": discussion_id
                },
                priority=MessagePriority.HIGH,
                requires_response=True
            )

            self.send_message(synthesis_request, discussion_id)


class EvidenceExchangeProtocol(CollaborationProtocol):
    """
    Manages exchange of evidence between agents.

    Agents can:
    - Request evidence from other agents
    - Provide evidence with claims
    - Challenge evidence quality
    - Validate evidence sources
    """

    def __init__(self):
        super().__init__()
        self.evidence_registry: Dict[str, List[Dict]] = {}  # claim_id -> [evidence_items]

    def request_evidence(self, discussion_id: str, requestor_id: str,
                        target_id: str, claim_id: str) -> AgentMessage:
        """Create evidence request message."""
        return AgentMessage(
            type=MessageType.REQUEST_ANALYSIS,
            sender_id=requestor_id,
            receiver_id=target_id,
            content={
                "claim_id": claim_id,
                "request": "Please provide evidence supporting your claim",
                "evidence_types": ["empirical", "theoretical", "mathematical"]
            },
            context_id=discussion_id,
            priority=MessagePriority.NORMAL,
            requires_response=True
        )

    def provide_evidence(self, discussion_id: str, provider_id: str,
                        claim_id: str, evidence: List[Dict[str, Any]]) -> AgentMessage:
        """Create evidence provision message."""
        # Register evidence
        if claim_id not in self.evidence_registry:
            self.evidence_registry[claim_id] = []

        self.evidence_registry[claim_id].extend(evidence)

        return AgentMessage(
            type=MessageType.PROVIDE_EVIDENCE,
            sender_id=provider_id,
            receiver_id="",  # Broadcast to all
            content={
                "claim_id": claim_id,
                "evidence": evidence,
                "count": len(evidence)
            },
            context_id=discussion_id,
            priority=MessagePriority.NORMAL
        )

    def validate_evidence(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quality and relevance of evidence."""
        validation = {
            "valid": True,
            "strength": 0.5,
            "concerns": []
        }

        # Check evidence type
        evidence_type = evidence.get("type", "")
        if evidence_type == "empirical":
            # Validate empirical evidence
            data_points = evidence.get("data_points", 0)
            if data_points < 10:
                validation["concerns"].append("Small sample size")
                validation["strength"] = 0.3
            else:
                validation["strength"] = min(1.0, 0.5 + data_points / 1000)

        elif evidence_type == "theoretical":
            # Validate theoretical evidence
            principles = evidence.get("principles", [])
            if not principles:
                validation["concerns"].append("No theoretical principles specified")
                validation["strength"] = 0.3
            else:
                validation["strength"] = min(1.0, 0.5 + len(principles) * 0.1)

        elif evidence_type == "mathematical":
            # Validate mathematical evidence
            consistent = evidence.get("consistent", True)
            validation["strength"] = 0.9 if consistent else 0.3

        # Set overall validity
        validation["valid"] = len(validation["concerns"]) == 0

        return validation

    def get_evidence_summary(self, claim_id: str) -> Dict[str, Any]:
        """Get summary of evidence for a claim."""
        evidence_items = self.evidence_registry.get(claim_id, [])

        if not evidence_items:
            return {"claim_id": claim_id, "total_evidence": 0}

        # Validate all evidence
        validations = [self.validate_evidence(e) for e in evidence_items]

        # Calculate aggregate strength
        total_strength = sum(v["strength"] for v in validations)
        avg_strength = total_strength / len(validations) if validations else 0

        # Count by type
        by_type = {}
        for evidence in evidence_items:
            evidence_type = evidence.get("type", "unknown")
            by_type[evidence_type] = by_type.get(evidence_type, 0) + 1

        return {
            "claim_id": claim_id,
            "total_evidence": len(evidence_items),
            "average_strength": avg_strength,
            "strongest_evidence": max(validations, key=lambda v: v["strength"]) if validations else None,
            "evidence_by_type": by_type,
            "concerns": [c for v in validations for c in v["concerns"]]
        }


def create_protocol(protocol_type: str = "collaboration") -> CollaborationProtocol:
    """Factory function to create protocol instances."""
    if protocol_type == "debate":
        return DebateProtocol()
    elif protocol_type == "evidence":
        return EvidenceExchangeProtocol()
    else:
        return CollaborationProtocol()


# Utility functions
def format_message_for_display(message: AgentMessage) -> str:
    """Format message for human-readable display."""
    sender = message.sender_id[:12] + "..." if len(message.sender_id) > 12 else message.sender_id

    if message.type == MessageType.OPINION:
        position = message.content.get("position", "unknown")
        confidence = message.content.get("confidence", 0)
        return f"[{sender}] OPINION: {position} (confidence: {confidence:.2f})"

    elif message.type == MessageType.CHALLENGE:
        return f"[{sender}] CHALLENGE: {message.content.get('reasoning', '')[:50]}..."

    elif message.type == MessageType.PROVIDE_EVIDENCE:
        count = message.content.get("count", 0)
        return f"[{sender}] EVIDENCE: Provided {count} evidence items"

    else:
        return f"[{sender}] {message.type.value}: {str(message.content)[:50]}..."


def summarize_discussion(discussion: DiscussionContext) -> Dict[str, Any]:
    """Summarize discussion for human review."""
    opinions = discussion.get_opinions()

    # Group by position
    by_position = {}
    for opinion in opinions:
        position = opinion.content.get("position", "unknown")
        if position not in by_position:
            by_position[position] = []
        by_position[position].append(opinion)

    # Extract key points
    key_points = []
    for opinion in opinions:
        reasoning = opinion.content.get("reasoning", "")
        if reasoning:
            key_points.append({
                "agent": opinion.sender_id,
                "role": opinion.content.get("agent_role", "unknown"),
                "point": reasoning[:200]  # First 200 chars
            })

    return {
        "discussion_id": discussion.id,
        "question": discussion.question,
        "duration_seconds": time.time() - discussion.start_time,
        "participants": discussion.participants,
        "total_opinions": len(opinions),
        "positions": {k: len(v) for k, v in by_position.items()},
        "key_points": key_points[:5],  # Top 5 points
        "status": discussion.status
    }
