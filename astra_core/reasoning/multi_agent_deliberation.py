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
Multi-Agent Deliberation System for STAN V41

Implements internal debate and consensus-building between multiple
reasoning perspectives. Different "agents" represent different viewpoints,
methodologies, or stakeholder perspectives that deliberate to reach
well-considered conclusions.

Key capabilities:
- Perspective generation: Create diverse reasoning viewpoints
- Structured debate: Facilitate argument and counter-argument
- Consensus building: Aggregate to reach well-grounded conclusions
- Devil's advocate: Ensure robust challenge of conclusions
- Stakeholder representation: Consider multiple interests
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Callable, Tuple
from enum import Enum, auto
from datetime import datetime
import uuid
from collections import defaultdict
import math


class AgentRole(Enum):
    """Roles that deliberation agents can take"""
    ADVOCATE = auto()          # Argues for a position
    CRITIC = auto()            # Challenges positions
    SYNTHESIZER = auto()       # Combines viewpoints
    EMPIRICIST = auto()        # Focuses on evidence
    THEORIST = auto()          # Focuses on principles
    PRAGMATIST = auto()        # Focuses on practicality
    DEVIL_ADVOCATE = auto()    # Argues against consensus
    MEDIATOR = auto()          # Facilitates agreement
    SPECIALIST = auto()        # Domain expert
    GENERALIST = auto()        # Cross-domain perspective


class ArgumentType(Enum):
    """Types of arguments in deliberation"""
    CLAIM = auto()             # Statement to be evaluated
    EVIDENCE = auto()          # Supporting data
    WARRANT = auto()           # Reasoning connecting evidence to claim
    BACKING = auto()           # Support for the warrant
    QUALIFIER = auto()         # Conditions/limitations
    REBUTTAL = auto()          # Counter-argument
    CONCESSION = auto()        # Acknowledged weakness
    SYNTHESIS = auto()         # Combined position


class DeliberationPhase(Enum):
    """Phases of the deliberation process"""
    OPENING = auto()           # Initial positions stated
    EXPLORATION = auto()       # Clarifying questions
    ARGUMENTATION = auto()     # Main arguments exchanged
    CHALLENGE = auto()         # Critical examination
    SYNTHESIS = auto()         # Building consensus
    CONCLUSION = auto()        # Final position reached


class ConsensusLevel(Enum):
    """Level of consensus achieved"""
    UNANIMOUS = auto()         # All agents agree
    STRONG = auto()            # Clear majority with weak dissent
    MODERATE = auto()          # Majority with notable dissent
    WEAK = auto()              # Slight majority
    DEADLOCK = auto()          # No clear consensus
    POLARIZED = auto()         # Strong opposing camps


@dataclass
class DeliberationAgent:
    """An agent participating in deliberation"""
    agent_id: str
    name: str
    role: AgentRole

    # Perspective
    methodology: str           # How this agent reasons
    priorities: List[str]      # What this agent values
    expertise: List[str]       # Domain knowledge

    # Behavior
    assertiveness: float = 0.5      # How strongly positions are stated
    flexibility: float = 0.5        # Willingness to change position
    collaboration: float = 0.5      # Focus on group outcome vs own position

    # State
    current_position: Optional[str] = None
    confidence: float = 0.5
    arguments_made: int = 0

    def __post_init__(self):
        if not self.agent_id:
            self.agent_id = f"AGT-{uuid.uuid4().hex[:8]}"


@dataclass
class Argument:
    """An argument made during deliberation"""
    argument_id: str
    agent_id: str              # Who made this argument
    argument_type: ArgumentType

    # Content
    content: str
    target: Optional[str] = None  # Argument this responds to

    # Support
    evidence: List[str] = field(default_factory=list)
    reasoning: str = ""

    # Strength
    strength: float = 0.5      # Logical strength
    novelty: float = 0.5       # New information added
    relevance: float = 0.5     # Connection to main question

    # Reception
    supporters: List[str] = field(default_factory=list)  # Agent IDs
    challengers: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.argument_id:
            self.argument_id = f"ARG-{uuid.uuid4().hex[:8]}"

    @property
    def net_support(self) -> int:
        """Net support for this argument"""
        return len(self.supporters) - len(self.challengers)


@dataclass
class Position:
    """A position taken by an agent"""
    position_id: str
    agent_id: str
    statement: str

    # Basis
    supporting_arguments: List[str]    # Argument IDs
    key_evidence: List[str]

    # Confidence
    confidence: float = 0.5
    uncertainty_factors: List[str] = field(default_factory=list)

    # Evolution
    revisions: int = 0
    previous_positions: List[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.position_id:
            self.position_id = f"POS-{uuid.uuid4().hex[:8]}"


@dataclass
class Consensus:
    """A consensus reached through deliberation"""
    consensus_id: str
    statement: str
    level: ConsensusLevel

    # Support
    supporting_agents: List[str]       # Agent IDs
    dissenting_agents: List[str]
    abstaining_agents: List[str]

    # Basis
    key_arguments: List[str]           # Argument IDs
    resolved_disagreements: List[str]
    remaining_disagreements: List[str]

    # Quality
    confidence: float = 0.5
    robustness: float = 0.5            # How well it withstood challenge

    # Conditions
    qualifications: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)

    reached_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.consensus_id:
            self.consensus_id = f"CON-{uuid.uuid4().hex[:8]}"


@dataclass
class DeliberationSession:
    """A deliberation session"""
    session_id: str
    question: str              # What's being deliberated
    context: str               # Background context

    # Participants
    agents: List[str]          # Agent IDs

    # Progress
    phase: DeliberationPhase = DeliberationPhase.OPENING
    rounds_completed: int = 0
    max_rounds: int = 5

    # Content
    arguments: List[str] = field(default_factory=list)  # Argument IDs
    positions: Dict[str, str] = field(default_factory=dict)  # Agent ID -> Position ID

    # Outcome
    consensus: Optional[str] = None  # Consensus ID
    is_concluded: bool = False

    started_at: datetime = field(default_factory=datetime.now)
    concluded_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.session_id:
            self.session_id = f"DLB-{uuid.uuid4().hex[:8]}"


class AgentFactory:
    """Creates deliberation agents with different perspectives"""

    def __init__(self):
        self.role_templates = {
            AgentRole.ADVOCATE: {
                "methodology": "Build strongest case for position",
                "priorities": ["clarity", "persuasion", "evidence support"],
                "assertiveness": 0.8,
                "flexibility": 0.3
            },
            AgentRole.CRITIC: {
                "methodology": "Identify weaknesses and gaps",
                "priorities": ["rigor", "completeness", "consistency"],
                "assertiveness": 0.7,
                "flexibility": 0.4
            },
            AgentRole.SYNTHESIZER: {
                "methodology": "Find common ground and integration",
                "priorities": ["coherence", "inclusion", "pragmatism"],
                "assertiveness": 0.5,
                "flexibility": 0.8
            },
            AgentRole.EMPIRICIST: {
                "methodology": "Ground in observable evidence",
                "priorities": ["data", "measurement", "reproducibility"],
                "assertiveness": 0.6,
                "flexibility": 0.5
            },
            AgentRole.THEORIST: {
                "methodology": "Apply principled frameworks",
                "priorities": ["consistency", "elegance", "generality"],
                "assertiveness": 0.6,
                "flexibility": 0.4
            },
            AgentRole.PRAGMATIST: {
                "methodology": "Focus on practical outcomes",
                "priorities": ["feasibility", "impact", "efficiency"],
                "assertiveness": 0.5,
                "flexibility": 0.7
            },
            AgentRole.DEVIL_ADVOCATE: {
                "methodology": "Challenge prevailing view",
                "priorities": ["robustness", "overlooked factors", "edge cases"],
                "assertiveness": 0.9,
                "flexibility": 0.2
            },
            AgentRole.MEDIATOR: {
                "methodology": "Facilitate understanding between positions",
                "priorities": ["fairness", "clarity", "progress"],
                "assertiveness": 0.3,
                "flexibility": 0.9
            }
        }

    def create_agent(
        self,
        role: AgentRole,
        name: str = None,
        expertise: List[str] = None
    ) -> DeliberationAgent:
        """Create an agent with specified role"""
        template = self.role_templates.get(role, {})

        return DeliberationAgent(
            agent_id="",
            name=name or f"{role.name.title()} Agent",
            role=role,
            methodology=template.get("methodology", "General reasoning"),
            priorities=template.get("priorities", ["accuracy"]),
            expertise=expertise or [],
            assertiveness=template.get("assertiveness", 0.5),
            flexibility=template.get("flexibility", 0.5),
            collaboration=0.6
        )

    def create_diverse_panel(
        self,
        domain: str,
        panel_size: int = 5
    ) -> List[DeliberationAgent]:
        """Create a diverse panel of agents"""
        # Essential roles
        essential = [AgentRole.ADVOCATE, AgentRole.CRITIC, AgentRole.SYNTHESIZER]

        # Additional roles based on panel size
        optional = [
            AgentRole.EMPIRICIST, AgentRole.THEORIST,
            AgentRole.PRAGMATIST, AgentRole.DEVIL_ADVOCATE
        ]

        roles = essential[:min(panel_size, len(essential))]
        remaining = panel_size - len(roles)
        roles.extend(optional[:remaining])

        agents = []
        for role in roles:
            agent = self.create_agent(role, expertise=[domain])
            agents.append(agent)

        return agents


class ArgumentEvaluator:
    """Evaluates the quality and impact of arguments"""

    def __init__(self):
        self.evaluation_criteria = {
            "logical_validity": 0.25,
            "evidence_support": 0.25,
            "relevance": 0.2,
            "novelty": 0.15,
            "clarity": 0.15
        }

    def evaluate(self, argument: Argument, context: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate an argument"""
        scores = {}

        scores["logical_validity"] = self._assess_logic(argument)
        scores["evidence_support"] = self._assess_evidence(argument)
        scores["relevance"] = self._assess_relevance(argument, context)
        scores["novelty"] = self._assess_novelty(argument, context)
        scores["clarity"] = self._assess_clarity(argument)

        scores["overall"] = sum(
            scores[c] * w for c, w in self.evaluation_criteria.items()
        )

        return scores

    def _assess_logic(self, argument: Argument) -> float:
        """Assess logical structure"""
        score = 0.5

        # Has reasoning
        if argument.reasoning:
            score += 0.2

        # Has warrant for claims
        if argument.argument_type == ArgumentType.CLAIM and argument.evidence:
            score += 0.2

        # Rebuttals are stronger if they address specific points
        if argument.argument_type == ArgumentType.REBUTTAL and argument.target:
            score += 0.1

        return min(1.0, score)

    def _assess_evidence(self, argument: Argument) -> float:
        """Assess evidence support"""
        if not argument.evidence:
            return 0.3

        # More evidence is generally better (with diminishing returns)
        evidence_score = min(1.0, len(argument.evidence) * 0.25)
        return evidence_score

    def _assess_relevance(self, argument: Argument, context: Dict[str, Any]) -> float:
        """Assess relevance to the question"""
        question = context.get("question", "")
        if not question:
            return 0.5

        # Simple word overlap
        arg_words = set(argument.content.lower().split())
        q_words = set(question.lower().split())
        overlap = len(arg_words & q_words) / max(len(q_words), 1)

        return min(1.0, 0.3 + overlap)

    def _assess_novelty(self, argument: Argument, context: Dict[str, Any]) -> float:
        """Assess novel contribution"""
        previous_args = context.get("previous_arguments", [])

        if not previous_args:
            return 0.8  # First argument is novel

        # Check for overlap with previous arguments
        arg_content = argument.content.lower()
        for prev in previous_args:
            prev_content = prev.get("content", "").lower()
            if self._jaccard_similarity(arg_content, prev_content) > 0.6:
                return 0.3  # Too similar

        return 0.7

    def _assess_clarity(self, argument: Argument) -> float:
        """Assess clarity of expression"""
        # Heuristics based on length and structure
        words = argument.content.split()
        word_count = len(words)

        # Too short or too long is less clear
        if word_count < 10:
            length_score = 0.5
        elif word_count > 200:
            length_score = 0.6
        else:
            length_score = 0.8

        return length_score

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)


class ConsensusBuilder:
    """Builds consensus from agent positions"""

    def __init__(self):
        self.consensus_thresholds = {
            ConsensusLevel.UNANIMOUS: 1.0,
            ConsensusLevel.STRONG: 0.8,
            ConsensusLevel.MODERATE: 0.6,
            ConsensusLevel.WEAK: 0.5,
        }

    def build_consensus(
        self,
        agents: List[DeliberationAgent],
        positions: Dict[str, Position],
        arguments: List[Argument]
    ) -> Consensus:
        """Build consensus from positions"""
        if not agents or not positions:
            return self._no_consensus(agents)

        # Group positions by similarity
        position_groups = self._cluster_positions(positions)

        # Find majority position
        largest_group = max(position_groups, key=lambda g: len(g))
        majority_size = len(largest_group)
        total = len(agents)

        ratio = majority_size / total

        # Determine consensus level
        level = self._determine_level(ratio, position_groups)

        # Extract key arguments supporting majority
        key_args = self._extract_key_arguments(largest_group, arguments)

        # Identify dissent
        dissenters = [a.agent_id for a in agents if a.agent_id not in
                      [p.agent_id for p in largest_group]]

        # Build consensus statement
        if level != ConsensusLevel.DEADLOCK:
            statement = self._synthesize_statement(largest_group)
        else:
            statement = "No clear consensus reached"

        return Consensus(
            consensus_id="",
            statement=statement,
            level=level,
            supporting_agents=[p.agent_id for p in largest_group],
            dissenting_agents=dissenters,
            abstaining_agents=[],
            key_arguments=[a.argument_id for a in key_args],
            resolved_disagreements=[],
            remaining_disagreements=[],
            confidence=ratio,
            robustness=self._assess_robustness(largest_group, arguments)
        )

    def _cluster_positions(
        self,
        positions: Dict[str, Position]
    ) -> List[List[Position]]:
        """Cluster similar positions"""
        position_list = list(positions.values())
        if len(position_list) <= 1:
            return [position_list]

        # Simple clustering by statement similarity
        clusters = []
        used = set()

        for pos in position_list:
            if pos.position_id in used:
                continue

            cluster = [pos]
            used.add(pos.position_id)

            for other in position_list:
                if other.position_id in used:
                    continue

                sim = self._position_similarity(pos, other)
                if sim > 0.5:  # Similarity threshold
                    cluster.append(other)
                    used.add(other.position_id)

            clusters.append(cluster)

        return clusters

    def _position_similarity(self, p1: Position, p2: Position) -> float:
        """Compute similarity between positions"""
        words1 = set(p1.statement.lower().split())
        words2 = set(p2.statement.lower().split())
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)

    def _determine_level(
        self,
        ratio: float,
        groups: List[List[Position]]
    ) -> ConsensusLevel:
        """Determine consensus level"""
        if ratio >= 1.0:
            return ConsensusLevel.UNANIMOUS
        elif ratio >= 0.8:
            return ConsensusLevel.STRONG
        elif ratio >= 0.6:
            return ConsensusLevel.MODERATE
        elif ratio >= 0.5:
            return ConsensusLevel.WEAK
        elif len(groups) == 2 and abs(len(groups[0]) - len(groups[1])) <= 1:
            return ConsensusLevel.POLARIZED
        else:
            return ConsensusLevel.DEADLOCK

    def _extract_key_arguments(
        self,
        position_group: List[Position],
        all_arguments: List[Argument]
    ) -> List[Argument]:
        """Extract key supporting arguments"""
        supporting_ids = set()
        for pos in position_group:
            supporting_ids.update(pos.supporting_arguments)

        key_args = [a for a in all_arguments if a.argument_id in supporting_ids]
        # Sort by strength
        return sorted(key_args, key=lambda a: a.strength, reverse=True)[:5]

    def _synthesize_statement(self, positions: List[Position]) -> str:
        """Synthesize a consensus statement from positions"""
        if len(positions) == 1:
            return positions[0].statement

        # Find common elements
        common_words = None
        for pos in positions:
            words = set(pos.statement.lower().split())
            if common_words is None:
                common_words = words
            else:
                common_words &= words

        # Use the shortest position as base
        base = min(positions, key=lambda p: len(p.statement))
        return f"Consensus: {base.statement}"

    def _assess_robustness(
        self,
        positions: List[Position],
        arguments: List[Argument]
    ) -> float:
        """Assess how robust the consensus is"""
        if not positions:
            return 0.0

        # Based on confidence and argument support
        avg_confidence = sum(p.confidence for p in positions) / len(positions)

        # Count rebuttals that weren't successfully countered
        supporting_ids = set()
        for pos in positions:
            supporting_ids.update(pos.supporting_arguments)

        rebuttals = [a for a in arguments
                     if a.argument_type == ArgumentType.REBUTTAL
                     and a.target not in supporting_ids]

        rebuttal_penalty = min(0.3, len(rebuttals) * 0.1)

        return max(0.1, avg_confidence - rebuttal_penalty)

    def _no_consensus(self, agents: List[DeliberationAgent]) -> Consensus:
        """Return a deadlock consensus"""
        return Consensus(
            consensus_id="",
            statement="No consensus could be reached",
            level=ConsensusLevel.DEADLOCK,
            supporting_agents=[],
            dissenting_agents=[a.agent_id for a in agents],
            abstaining_agents=[],
            key_arguments=[],
            resolved_disagreements=[],
            remaining_disagreements=["All positions remain contested"],
            confidence=0.0,
            robustness=0.0
        )


class DeliberationFacilitator:
    """Facilitates the deliberation process"""

    def __init__(self):
        self.phase_handlers = {
            DeliberationPhase.OPENING: self._handle_opening,
            DeliberationPhase.EXPLORATION: self._handle_exploration,
            DeliberationPhase.ARGUMENTATION: self._handle_argumentation,
            DeliberationPhase.CHALLENGE: self._handle_challenge,
            DeliberationPhase.SYNTHESIS: self._handle_synthesis,
            DeliberationPhase.CONCLUSION: self._handle_conclusion,
        }

    def advance_phase(self, session: DeliberationSession) -> DeliberationPhase:
        """Advance to next phase"""
        phase_order = list(DeliberationPhase)
        current_idx = phase_order.index(session.phase)

        if current_idx < len(phase_order) - 1:
            session.phase = phase_order[current_idx + 1]

        return session.phase

    def should_advance(
        self,
        session: DeliberationSession,
        arguments: List[Argument]
    ) -> bool:
        """Determine if phase should advance"""
        handler = self.phase_handlers.get(session.phase)
        if handler:
            return handler(session, arguments)
        return True

    def _handle_opening(
        self,
        session: DeliberationSession,
        arguments: List[Argument]
    ) -> bool:
        """Check if opening phase is complete"""
        # All agents should have stated initial positions
        return len(session.positions) >= len(session.agents) * 0.8

    def _handle_exploration(
        self,
        session: DeliberationSession,
        arguments: List[Argument]
    ) -> bool:
        """Check if exploration is complete"""
        # Some clarifying exchanges should have happened
        return session.rounds_completed >= 1

    def _handle_argumentation(
        self,
        session: DeliberationSession,
        arguments: List[Argument]
    ) -> bool:
        """Check if main argumentation is complete"""
        claims = [a for a in arguments if a.argument_type == ArgumentType.CLAIM]
        rebuttals = [a for a in arguments if a.argument_type == ArgumentType.REBUTTAL]

        # Need substantive exchange
        return len(claims) >= len(session.agents) and len(rebuttals) >= 2

    def _handle_challenge(
        self,
        session: DeliberationSession,
        arguments: List[Argument]
    ) -> bool:
        """Check if challenge phase is complete"""
        return session.rounds_completed >= 2

    def _handle_synthesis(
        self,
        session: DeliberationSession,
        arguments: List[Argument]
    ) -> bool:
        """Check if synthesis is complete"""
        syntheses = [a for a in arguments if a.argument_type == ArgumentType.SYNTHESIS]
        return len(syntheses) >= 1

    def _handle_conclusion(
        self,
        session: DeliberationSession,
        arguments: List[Argument]
    ) -> bool:
        """Always conclude"""
        return True


class MultiAgentDeliberator:
    """
    Main multi-agent deliberation engine.
    Coordinates agents, facilitates debate, and builds consensus.
    """

    def __init__(self):
        self.agent_factory = AgentFactory()
        self.argument_evaluator = ArgumentEvaluator()
        self.consensus_builder = ConsensusBuilder()
        self.facilitator = DeliberationFacilitator()

        # Storage
        self.agents: Dict[str, DeliberationAgent] = {}
        self.arguments: Dict[str, Argument] = {}
        self.positions: Dict[str, Position] = {}
        self.consensuses: Dict[str, Consensus] = {}
        self.sessions: Dict[str, DeliberationSession] = {}

        # Event callbacks
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable):
        """Register callback"""
        self._callbacks[event].append(callback)

    def _emit(self, event: str, data: Any):
        """Emit event"""
        for callback in self._callbacks[event]:
            callback(data)

    def create_session(
        self,
        question: str,
        context: str,
        domain: str = "general",
        panel_size: int = 5,
        max_rounds: int = 5
    ) -> DeliberationSession:
        """Create a new deliberation session"""
        # Create diverse panel
        agents = self.agent_factory.create_diverse_panel(domain, panel_size)

        for agent in agents:
            self.agents[agent.agent_id] = agent

        session = DeliberationSession(
            session_id="",
            question=question,
            context=context,
            agents=[a.agent_id for a in agents],
            max_rounds=max_rounds
        )

        self.sessions[session.session_id] = session
        self._emit("session_created", session)
        return session

    def add_argument(
        self,
        session_id: str,
        agent_id: str,
        argument_type: ArgumentType,
        content: str,
        evidence: List[str] = None,
        target: str = None
    ) -> Argument:
        """Add an argument to the deliberation"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        argument = Argument(
            argument_id="",
            agent_id=agent_id,
            argument_type=argument_type,
            content=content,
            target=target,
            evidence=evidence or [],
            reasoning=""
        )

        # Evaluate argument
        eval_context = {
            "question": session.question,
            "previous_arguments": [
                {"content": self.arguments[aid].content}
                for aid in session.arguments
                if aid in self.arguments
            ]
        }
        scores = self.argument_evaluator.evaluate(argument, eval_context)
        argument.strength = scores["overall"]
        argument.novelty = scores["novelty"]
        argument.relevance = scores["relevance"]

        self.arguments[argument.argument_id] = argument
        session.arguments.append(argument.argument_id)

        # Update agent state
        agent = self.agents.get(agent_id)
        if agent:
            agent.arguments_made += 1

        self._emit("argument_added", argument)
        return argument

    def update_position(
        self,
        session_id: str,
        agent_id: str,
        statement: str,
        supporting_arguments: List[str],
        confidence: float
    ) -> Position:
        """Update an agent's position"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        # Check for existing position
        existing = None
        if agent_id in session.positions:
            existing = self.positions.get(session.positions[agent_id])

        position = Position(
            position_id="",
            agent_id=agent_id,
            statement=statement,
            supporting_arguments=supporting_arguments,
            key_evidence=[],
            confidence=confidence
        )

        if existing:
            position.revisions = existing.revisions + 1
            position.previous_positions = existing.previous_positions + [existing.statement]

        self.positions[position.position_id] = position
        session.positions[agent_id] = position.position_id

        # Update agent
        agent = self.agents.get(agent_id)
        if agent:
            agent.current_position = statement
            agent.confidence = confidence

        self._emit("position_updated", position)
        return position

    def generate_response(
        self,
        session_id: str,
        agent_id: str,
        responding_to: str = None
    ) -> Optional[Argument]:
        """Generate an agent's response"""
        session = self.sessions.get(session_id)
        agent = self.agents.get(agent_id)

        if not session or not agent:
            return None

        # Determine response type based on role and phase
        arg_type, content = self._generate_response_content(
            agent, session, responding_to
        )

        if content:
            return self.add_argument(
                session_id, agent_id, arg_type, content, target=responding_to
            )
        return None

    def _generate_response_content(
        self,
        agent: DeliberationAgent,
        session: DeliberationSession,
        responding_to: str = None
    ) -> Tuple[ArgumentType, str]:
        """Generate response content based on agent role"""
        # Get context
        question = session.question
        target_arg = self.arguments.get(responding_to) if responding_to else None

        # Role-based response generation
        if agent.role == AgentRole.ADVOCATE:
            return ArgumentType.CLAIM, f"From {agent.methodology}: {question} suggests... [advocating position]"

        elif agent.role == AgentRole.CRITIC:
            if target_arg:
                return ArgumentType.REBUTTAL, f"Challenging: {target_arg.content[:50]}... [identifying weakness]"
            return ArgumentType.REBUTTAL, f"The argument overlooks... [critical examination]"

        elif agent.role == AgentRole.SYNTHESIZER:
            return ArgumentType.SYNTHESIS, f"Integrating perspectives: {question}... [finding common ground]"

        elif agent.role == AgentRole.EMPIRICIST:
            return ArgumentType.EVIDENCE, f"The data shows: {question}... [empirical basis]"

        elif agent.role == AgentRole.THEORIST:
            return ArgumentType.WARRANT, f"Based on principles: {question}... [theoretical framework]"

        elif agent.role == AgentRole.PRAGMATIST:
            return ArgumentType.QUALIFIER, f"In practice: {question}... [practical constraints]"

        elif agent.role == AgentRole.DEVIL_ADVOCATE:
            return ArgumentType.REBUTTAL, f"However, consider: {question}... [contrarian view]"

        elif agent.role == AgentRole.MEDIATOR:
            return ArgumentType.SYNTHESIS, f"Both sides agree that: {question}... [common ground]"

        return ArgumentType.CLAIM, f"Regarding {question}..."

    def run_round(self, session_id: str) -> Dict[str, Any]:
        """Run one round of deliberation"""
        session = self.sessions.get(session_id)
        if not session or session.is_concluded:
            return {"status": "inactive"}

        # Each agent responds
        round_arguments = []
        for agent_id in session.agents:
            # Find most recent argument to potentially respond to
            recent = session.arguments[-1] if session.arguments else None

            # Generate response
            arg = self.generate_response(session_id, agent_id, recent)
            if arg:
                round_arguments.append(arg)

        session.rounds_completed += 1

        # Check for phase advancement
        all_args = [self.arguments[aid] for aid in session.arguments if aid in self.arguments]
        if self.facilitator.should_advance(session, all_args):
            self.facilitator.advance_phase(session)

        # Check for conclusion
        if session.phase == DeliberationPhase.CONCLUSION or session.rounds_completed >= session.max_rounds:
            self._conclude_session(session_id)

        self._emit("round_completed", {
            "session_id": session_id,
            "round": session.rounds_completed,
            "phase": session.phase.name,
            "arguments": len(round_arguments)
        })

        return {
            "round": session.rounds_completed,
            "phase": session.phase.name,
            "arguments_this_round": len(round_arguments)
        }

    def _conclude_session(self, session_id: str) -> Consensus:
        """Conclude a deliberation session"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        # Get all participants and their positions
        agents = [self.agents[aid] for aid in session.agents if aid in self.agents]
        positions = {
            aid: self.positions[pid]
            for aid, pid in session.positions.items()
            if pid in self.positions
        }
        arguments = [
            self.arguments[aid]
            for aid in session.arguments
            if aid in self.arguments
        ]

        # Build consensus
        consensus = self.consensus_builder.build_consensus(agents, positions, arguments)

        self.consensuses[consensus.consensus_id] = consensus
        session.consensus = consensus.consensus_id
        session.is_concluded = True
        session.concluded_at = datetime.now()

        self._emit("session_concluded", {
            "session_id": session_id,
            "consensus": consensus
        })

        return consensus

    def deliberate(
        self,
        question: str,
        context: str = "",
        domain: str = "general",
        max_rounds: int = 5
    ) -> Consensus:
        """Run a complete deliberation and return consensus"""
        session = self.create_session(question, context, domain, max_rounds=max_rounds)

        while not session.is_concluded:
            self.run_round(session.session_id)

        return self.consensuses.get(session.consensus)

    def get_deliberation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of a deliberation session"""
        session = self.sessions.get(session_id)
        if not session:
            return {}

        return {
            "question": session.question,
            "phase": session.phase.name,
            "rounds": session.rounds_completed,
            "agents": len(session.agents),
            "arguments": len(session.arguments),
            "positions": len(session.positions),
            "concluded": session.is_concluded,
            "consensus": self.consensuses.get(session.consensus).__dict__ if session.consensus else None
        }


# Singleton instance
_deliberator: Optional[MultiAgentDeliberator] = None


def get_deliberator() -> MultiAgentDeliberator:
    """Get or create the global deliberator"""
    global _deliberator
    if _deliberator is None:
        _deliberator = MultiAgentDeliberator()
    return _deliberator
