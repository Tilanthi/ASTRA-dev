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
ASTRA V9.0 — Multi-Agent Scientific Collaboration System
Provides specialized agents that collaborate on scientific problems.

This module implements Phase 1 of V9.0: Multi-Agent Foundation

Components:
- AgentFactory: Creates specialized scientific agents
- CollaborationProtocol: Manages agent communication
- ConsensusEngine: Computes consensus from agent opinions
- DebateOrchestrator: Orchestrates structured scientific debates
- ExpertiseTracker: Tracks agent specializations and performance

Example usage:
    from astra_live_backend.multi_agent import (
        AgentFactory, DebateOrchestrator, create_debate
    )

    # Create agents
    agents = AgentFactory.create_full_team()

    # Start debate
    orchestrator = create_debate()
    debate_id = orchestrator.start_debate(
        "What determines the characteristic width of interstellar filaments?",
        [agent.id for agent in agents]
    )

    # Advance debate through phases
    orchestrator.advance_debate(debate_id)

    # Get result
    result = orchestrator.conclude_debate(debate_id)
    print(result.recommendation)
"""

from .agent_factory import (
    AgentFactory,
    ScientificAgent,
    AgentRole,
    AgentStatus,
    AgentExpertise,
    AgentOpinion,
    TheoristAgent,
    EmpiricistAgent,
    ExperimentalistAgent,
    MathematicianAgent,
    SkepticAgent,
    SynthesizerAgent,
    get_agent_description,
    validate_agent_collaboration
)

from .collaboration_protocol import (
    CollaborationProtocol,
    DebateProtocol,
    EvidenceExchangeProtocol,
    DiscussionContext,
    AgentMessage,
    MessageType,
    MessagePriority,
    create_protocol,
    format_message_for_display,
    summarize_discussion
)

from .consensus_engine import (
    ConsensusEngine,
    ConsensusMethod,
    ConsensusResult,
    ConflictResolver,
    format_consensus_result,
    compare_consensus_methods
)

from .debate_orchestrator import (
    DebateOrchestrator,
    DebateConfig,
    DebatePhase,
    DebateResult,
    DebateMetrics,
    create_debate
)

from .expertise_tracker import (
    ExpertiseTracker,
    ExpertiseLevel,
    SpecializationProfile,
    TaskPerformance,
    create_expertise_tracker,
    compare_agent_performance
)

__all__ = [
    # Factory
    "AgentFactory",
    "create_debate",

    # Agents
    "ScientificAgent",
    "AgentRole",
    "AgentStatus",
    "TheoristAgent",
    "EmpiricistAgent",
    "ExperimentalistAgent",
    "MathematicianAgent",
    "SkepticAgent",
    "SynthesizerAgent",

    # Protocol
    "CollaborationProtocol",
    "DebateProtocol",
    "DiscussionContext",
    "AgentMessage",
    "MessageType",

    # Consensus
    "ConsensusEngine",
    "ConsensusMethod",
    "ConsensusResult",

    # Debate
    "DebateOrchestrator",
    "DebateConfig",
    "DebateResult",

    # Expertise
    "ExpertiseTracker",
    "ExpertiseLevel",

    # Utilities
    "format_message_for_display",
    "format_consensus_result",
    "summarize_discussion"
]
