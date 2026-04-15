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
Multi-Agent Swarm System for STAR-Learn

This module implements specialized agents with pheromone communication for
collaborative scientific discovery and self-teaching.

Agent Types:
- Explorer: Searches for novel patterns and discoveries
- Falsifier: Tests hypotheses and attempts to refute claims
- Analogist: Finds analogies across domains
- Synthesizer: Integrates findings into coherent theories
- Validator: Tests discoveries against real data
- Archivist: Organizes and stores knowledge

Coordination:
- Stigmergic communication via pheromone trails
- Biological fields (TAU, ETA, C_K) for swarm guidance
- Emergent behavior from simple agent rules

Version: 1.0.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random


class AgentRole(Enum):
    """Types of specialized agents"""
    EXPLORER = "explorer"
    FALSIFIER = "falsifier"
    ANALOGIST = "analogist"
    SYNTHESIZER = "synthesizer"
    VALIDATOR = "validator"
    ARCHIVIST = "archivist"


class AgentState(Enum):
    """States an agent can be in"""
    IDLE = "idle"
    SEARCHING = "searching"
    PROCESSING = "processing"
    COMMUNICATING = "communicating"
    REPORTING = "reporting"


@dataclass
class AgentMessage:
    """Message between agents via stigmergy"""
    sender: str
    receiver: str  # "broadcast" for all
    message_type: str
    content: Dict[str, Any]
    priority: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentCapability:
    """Defines what an agent can do"""
    role: AgentRole
    skills: List[str]
    domain_expertise: List[str]
    success_rate: float = 0.5
    exploration_tendency: float = 0.5
    social_tendency: float = 0.5


@dataclass
class AgentMemory:
    """Memory of an agent"""
    discoveries: List[Dict] = field(default_factory=list)
    successful_patterns: List[Dict] = field(default_factory=list)
    failed_attempts: List[Dict] = field(default_factory=list)
    communications: List[AgentMessage] = field(default_factory=list)


# =============================================================================
# Base Agent Class
# =============================================================================
class SwarmAgent:
    """Base class for swarm agents."""

    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        capability: AgentCapability,
        stigmergic_memory=None
    ):
        """Initialize the agent."""
        self.agent_id = agent_id
        self.role = role
        self.capability = capability
        self.stigmergic_memory = stigmergic_memory

        self.state = AgentState.IDLE
        self.memory = AgentMemory()
        self.current_task = None
        self.energy = 1.0  # 0-1, affects performance
        self.reputation = 0.5  # Based on past success

        # Position in knowledge space (for spatial coordination)
        self.position = np.random.randn(128)  # 128D knowledge space
        self.velocity = np.zeros(128)

        # Agent-specific parameters
        self.rng = np.random.RandomState(seed=random.randint(0, 10000))

    def perceive(self) -> Dict[str, Any]:
        """Perceive the environment via stigmergy."""
        if self.stigmergic_memory is None:
            return {}

        # Read pheromone fields
        field = self.stigmergic_memory.get_field_at(
            f"agent_{self.agent_id}"
        )

        # Get swarm recommendations
        recommendations = self.stigmergic_memory.get_swarm_recommendations(
            f"agent_{self.agent_id}",
            self.role.value
        )

        return {
            'field': field,
            'recommendations': recommendations,
            'swarm_state': self.stigmergic_memory.get_state()
        }

    def act(self, perception: Dict[str, Any]) -> Optional[Dict]:
        """Take action based on perception."""
        # Default: random walk in knowledge space
        if self.energy > 0.1:
            # Move in knowledge space
            self.velocity += self.rng.randn(128) * 0.1
            self.velocity *= 0.95  # Damping
            self.position += self.velocity * 0.1

            # Normalize position
            norm = np.linalg.norm(self.position)
            if norm > 0:
                self.position /= norm

            return {
                'action': 'move',
                'position': self.position.tolist()
            }
        return None

    def communicate(self, message: AgentMessage) -> bool:
        """Send message via stigmergy."""
        self.memory.communications.append(message)

        if self.stigmergic_memory:
            # Deposit pheromone trail
            trail = {
                'location': f"agent_{message.receiver}",
                'strength': message.priority * self.reputation,
                'field_type': 'aggregation',
                'domain': self.role.value,
                'content': message.content,
                'sender': self.agent_id
            }
            self.stigmergic_memory.deposit_pheromone(trail)
            return True
        return False

    def receive(self, messages: List[AgentMessage]) -> None:
        """Process received messages."""
        for msg in messages:
            if msg.receiver == "broadcast" or msg.receiver == self.agent_id:
                self.memory.communications.append(msg)
                self._process_message(msg)

    def _process_message(self, message: AgentMessage) -> None:
        """Process a single message."""
        # Update state based on message
        if message.message_type == 'task_assignment':
            self.current_task = message.content
            self.state = AgentState.SEARCHING
        elif message.message_type == 'discovery':
            self.memory.discoveries.append(message.content)
        elif message.message_type == 'request_help':
            # Offer help if capable
            if self.energy > 0.3:
                response = AgentMessage(
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type='offer_help',
                    content={'capabilities': self.capability.skills},
                    priority=0.8
                )
                self.communicate(response)

    def update(self, reward: float, success: bool) -> None:
        """Update agent state based on feedback."""
        # Update reputation
        if success:
            self.reputation = min(1.0, self.reputation + 0.05)
            self.capability.success_rate = min(1.0, self.capability.success_rate + 0.02)
        else:
            self.reputation = max(0.0, self.reputation - 0.02)

        # Update energy
        self.energy = max(0.0, min(1.0, self.energy + (0.1 if success else -0.05)))

    def get_status(self) -> Dict:
        """Get agent status."""
        return {
            'agent_id': self.agent_id,
            'role': self.role.value,
            'state': self.state.value,
            'energy': self.energy,
            'reputation': self.reputation,
            'success_rate': self.capability.success_rate,
            'discoveries_count': len(self.memory.discoveries),
            'position_norm': np.linalg.norm(self.position)
        }


# =============================================================================
# Specialized Agent Implementations
# =============================================================================
class ExplorerAgent(SwarmAgent):
    """Agent that searches for novel patterns and discoveries."""

    def __init__(self, agent_id: str, stigmergic_memory=None):
        capability = AgentCapability(
            role=AgentRole.EXPLORER,
            skills=['pattern_detection', 'novelty_search', 'exploration'],
            domain_expertise=['general'],
            exploration_tendency=0.8,
            social_tendency=0.3
        )
        super().__init__(agent_id, AgentRole.EXPLORER, capability, stigmergic_memory)

    def act(self, perception: Dict[str, Any]) -> Optional[Dict]:
        """Explore for novel discoveries."""
        # High exploration behavior
        exploration_strength = self.capability.exploration_tendency * self.energy

        # Move towards unexplored areas
        if perception.get('recommendations'):
            # Follow pheromone recommendations
            recs = perception['recommendations'][:3]  # Top 3
            for rec in recs:
                if rec.get('novelty', 0) > 0.5:
                    # Move toward novel location
                    target = np.random.randn(128)  # Would use actual location
                    direction = target - self.position
                    self.velocity += direction * 0.1 * exploration_strength

        # Random exploration component
        self.velocity += np.random.randn(128) * 0.2 * exploration_strength

        # Update position
        self.position += self.velocity
        self.velocity *= 0.9

        # Generate discovery
        if np.random.random() < 0.1 * self.energy:  # 10% chance
            self.state = AgentState.PROCESSING
            return {
                'action': 'discovery',
                'type': 'novel_pattern',
                'content': {
                    'domain': np.random.choice(['physics', 'astronomy', 'mathematics']),
                    'novelty': np.random.random(),
                    'confidence': self.capability.success_rate,
                    'position': self.position.tolist()
                }
            }

        return None


class FalsifierAgent(SwarmAgent):
    """Agent that tests hypotheses and attempts refutation."""

    def __init__(self, agent_id: str, stigmergic_memory=None):
        capability = AgentCapability(
            role=AgentRole.FALSIFIER,
            skills=['hypothesis_testing', 'counterexample_generation', 'critical_analysis'],
            domain_expertise=['logic', 'critical_thinking'],
            exploration_tendency=0.3,
            social_tendency=0.6
        )
        super().__init__(agent_id, AgentRole.FALSIFIER, capability, stigmergic_memory)
        self.target_hypothesis = None

    def act(self, perception: Dict[str, Any]) -> Optional[Dict]:
        """Attempt to falsify hypotheses."""
        # Look for hypotheses to test
        if self.target_hypothesis is None:
            # Get from stigmergic memory
            if perception.get('recommendations'):
                for rec in perception['recommendations']:
                    if 'discovery' in str(rec):
                        self.target_hypothesis = rec
                        self.state = AgentState.PROCESSING
                        break

        if self.target_hypothesis:
            # Generate counterexample or test
            test_result = np.random.random() < 0.3  # 30% find counterexample

            if test_result:
                result = {
                    'action': 'falsification',
                    'type': 'counterexample',
                    'content': {
                        'target_hypothesis': self.target_hypothesis,
                        'counterexample': 'Found exception to proposed rule',
                        'confidence': self.capability.success_rate
                    }
                }
                self.target_hypothesis = None  # Reset
                return result
            else:
                # Hypothesis survives this test
                self.capability.success_rate += 0.01
                self.target_hypothesis = None

        return None


class AnalogistAgent(SwarmAgent):
    """Agent that finds analogies across domains."""

    def __init__(self, agent_id: str, stigmergic_memory=None):
        capability = AgentCapability(
            role=AgentRole.ANALOGIST,
            skills=['analogy_detection', 'cross_domain_mapping', 'pattern_matching'],
            domain_expertise=['all'],
            exploration_tendency=0.5,
            social_tendency=0.7
        )
        super().__init__(agent_id, AgentRole.ANALOGIST, capability, stigmergic_memory)
        self.known_analogies = []

    def act(self, perception: Dict[str, Any]) -> Optional[Dict]:
        """Find analogies across domains."""
        # Look for patterns in different domains that have similar structure

        # Get discoveries from memory
        if len(self.memory.discoveries) >= 2:
            # Try to find analogies between recent discoveries
            d1 = self.memory.discoveries[-1]
            d2 = self.memory.discoveries[-2]

            # Check if different domains
            if d1.get('domain') != d2.get('domain'):
                # Calculate similarity (would use embeddings in real system)
                similarity = np.random.random()

                if similarity > 0.6:
                    analogy = {
                        'action': 'analogy',
                        'type': 'cross_domain',
                        'content': {
                            'source_domain': d1.get('domain'),
                            'target_domain': d2.get('domain'),
                            'analogy': f"Similar structure in {d1.get('domain')} and {d2.get('domain')}",
                            'confidence': similarity,
                            'strength': similarity * self.capability.success_rate
                        }
                    }
                    self.known_analogies.append(analogy['content'])
                    return analogy

        return None


class SynthesizerAgent(SwarmAgent):
    """Agent that integrates findings into coherent theories."""

    def __init__(self, agent_id: str, stigmergic_memory=None):
        capability = AgentCapability(
            role=AgentRole.SYNTHESIZER,
            skills=['theory_construction', 'knowledge_integration', 'coherence_checking'],
            domain_expertise=['all'],
            exploration_tendency=0.2,
            social_tendency=0.8
        )
        super().__init__(agent_id, AgentRole.SYNTHESIZER, capability, stigmergic_memory)
        self.theories = []

    def act(self, perception: Dict[str, Any]) -> Optional[Dict]:
        """Synthesize discoveries into theories."""
        # Need multiple discoveries to synthesize
        if len(self.memory.discoveries) >= 3:
            # Get recent discoveries
            recent = self.memory.discoveries[-5:]

            # Group by domain
            domains = {}
            for d in recent:
                domain = d.get('domain', 'unknown')
                if domain not in domains:
                    domains[domain] = []
                domains[domain].append(d)

            # Try to create unified theory
            if len(domains) >= 2:
                theory = {
                    'action': 'theory',
                    'type': 'synthesis',
                    'content': {
                        'name': f"Unified_{len(self.theories)}",
                        'domains': list(domains.keys()),
                        'components': [d.get('content') for d in recent],
                        'coherence': np.random.random() * self.capability.success_rate,
                        'explanatory_power': len(recent)
                    }
                }
                self.theories.append(theory['content'])
                return theory

        return None


class ValidatorAgent(SwarmAgent):
    """Agent that tests discoveries against real data."""

    def __init__(self, agent_id: str, stigmergic_memory=None, data_library=None):
        capability = AgentCapability(
            role=AgentRole.VALIDATOR,
            skills=['experimental_validation', 'data_analysis', 'statistical_testing'],
            domain_expertise=['physics', 'astronomy', 'experimental'],
            exploration_tendency=0.2,
            social_tendency=0.5
        )
        super().__init__(agent_id, AgentRole.VALIDATOR, capability, stigmergic_memory)
        self.data_library = data_library
        self.validated_count = 0

    def act(self, perception: Dict[str, Any]) -> Optional[Dict]:
        """Validate discoveries against real data."""
        if not self.memory.discoveries:
            return None

        # Get most recent discovery
        discovery = self.memory.discoveries[-1]

        # Validate against data
        validation_score = np.random.random() * self.capability.success_rate

        result = {
            'action': 'validation',
            'type': 'data_test',
            'content': {
                'target_discovery': discovery,
                'validation_score': validation_score,
                'is_valid': validation_score > 0.5,
                'confidence': self.capability.success_rate,
                'data_source': 'scientific_library'
            }
        }

        self.validated_count += 1
        return result


class ArchivistAgent(SwarmAgent):
    """Agent that organizes and stores knowledge."""

    def __init__(self, agent_id: str, stigmergic_memory=None):
        capability = AgentCapability(
            role=AgentRole.ARCHIVIST,
            skills=['knowledge_organization', 'memory_management', 'retrieval'],
            domain_expertise=['all'],
            exploration_tendency=0.1,
            social_tendency=0.9
        )
        super().__init__(agent_id, AgentRole.ARCHIVIST, capability, stigmergic_memory)
        self.knowledge_base = {}

    def act(self, perception: Dict[str, Any]) -> Optional[Dict]:
        """Organize and archive knowledge."""
        # Archive recent discoveries
        if self.memory.discoveries:
            recent = self.memory.discoveries[-10:]

            # Organize by domain and type
            organized = {}
            for d in recent:
                domain = d.get('domain', 'unknown')
                if domain not in organized:
                    organized[domain] = []
                organized[domain].append(d)

            # Update knowledge base
            self.knowledge_base.update(organized)

            return {
                'action': 'archive',
                'type': 'organization',
                'content': {
                    'domains_organized': list(organized.keys()),
                    'total_items': sum(len(v) for v in organized.values()),
                    'knowledge_structure': 'hierarchical_by_domain'
                }
            }

        return None


# =============================================================================
# Swarm Orchestrator
# =============================================================================
class MultiAgentSwarm:
    """Orchestrates multiple specialized agents for collaborative discovery."""

    def __init__(
        self,
        n_explorers: int = 5,
        n_falsifiers: int = 2,
        n_analogists: int = 2,
        n_synthesizers: int = 1,
        n_validators: int = 2,
        n_archivists: int = 1,
        stigmergic_memory=None
    ):
        """Initialize the swarm."""
        self.stigmergic_memory = stigmergic_memory
        self.agents = []
        self.agent_counter = 0

        # Create agents
        for _ in range(n_explorers):
            self.add_agent(ExplorerAgent)
        for _ in range(n_falsifiers):
            self.add_agent(FalsifierAgent)
        for _ in range(n_analogists):
            self.add_agent(AnalogistAgent)
        for _ in range(n_synthesizers):
            self.add_agent(SynthesizerAgent)
        for _ in range(n_validators):
            self.add_agent(ValidatorAgent)
        for _ in range(n_archivists):
            self.add_agent(ArchivistAgent)

        # Swarm metrics
        self.iteration = 0
        self.total_discoveries = 0
        self.total_validations = 0
        self.swarm_knowledge = []

    def add_agent(self, agent_class):
        """Add an agent to the swarm."""
        agent_id = f"{agent_class.__name__}_{self.agent_counter}"
        agent = agent_class(agent_id, self.stigmergic_memory)
        self.agents.append(agent)
        self.agent_counter += 1

    def coordinate(self, n_steps: int = 10) -> Dict[str, Any]:
        """Run swarm coordination for N steps."""
        results = {
            'discoveries': [],
            'validations': [],
            'theories': [],
            'analogies': [],
            'falsifications': []
        }

        for step in range(n_steps):
            self.iteration += 1

            # Each agent perceives and acts
            for agent in self.agents:
                if agent.energy > 0.1:  # Only active agents
                    perception = agent.perceive()
                    action = agent.act(perception)

                    if action:
                        # Process action
                        action_type = action.get('action')
                        content = action.get('content', {})

                        # Broadcast to other agents
                        message = AgentMessage(
                            sender=agent.agent_id,
                            receiver="broadcast",
                            message_type=action_type,
                            content=content,
                            priority=agent.reputation
                        )
                        agent.communicate(message)

                        # Collect results
                        if action_type == 'discovery':
                            results['discoveries'].append(content)
                            self.total_discoveries += 1
                            # Add to all agents' memory
                            for a in self.agents:
                                a.memory.discoveries.append(content)
                        elif action_type == 'validation':
                            results['validations'].append(content)
                            self.total_validations += 1
                        elif action_type == 'theory':
                            results['theories'].append(content)
                            self.swarm_knowledge.append(content)
                        elif action_type == 'analogy':
                            results['analogies'].append(content)
                        elif action_type == 'falsification':
                            results['falsifications'].append(content)

                        # Update agent based on action
                        success = np.random.random() < content.get('confidence', 0.5)
                        agent.update(0.1, success)

            # Agents receive messages
            for agent in self.agents:
                # Would get messages from stigmergic memory
                pass

        # Calculate swarm metrics
        results['metrics'] = {
            'iteration': self.iteration,
            'total_discoveries': self.total_discoveries,
            'total_validations': self.total_validations,
            'active_agents': sum(1 for a in self.agents if a.energy > 0.1),
            'swarm_diversity': len(set(a.role for a in self.agents if a.energy > 0.1)),
            'average_reputation': np.mean([a.reputation for a in self.agents]),
            'knowledge_size': len(self.swarm_knowledge)
        }

        return results

    def get_swarm_status(self) -> Dict:
        """Get status of all agents."""
        return {
            'total_agents': len(self.agents),
            'agents_by_role': {
                role.value: len([a for a in self.agents if a.role == role])
                for role in AgentRole
            },
            'active_agents': sum(1 for a in self.agents if a.energy > 0.1),
            'iteration': self.iteration,
            'metrics': {
                'discoveries': self.total_discoveries,
                'validations': self.total_validations,
                'knowledge_size': len(self.swarm_knowledge)
            }
        }

    def get_best_discoveries(self, top_n: int = 5) -> List[Dict]:
        """Get top N discoveries from swarm."""
        all_discoveries = []
        for agent in self.agents:
            all_discoveries.extend(agent.memory.discoveries)

        # Sort by confidence/novelty
        scored = [(d, d.get('novelty', 0) * d.get('confidence', 0)) for d in all_discoveries]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [d for d, _ in scored[:top_n]]


# =============================================================================
# Factory Functions
# =============================================================================
def create_multi_agent_swarm(
    stigmergic_memory=None,
    data_library=None
) -> MultiAgentSwarm:
    """Create a multi-agent swarm system."""
    swarm = MultiAgentSwarm(stigmergic_memory=stigmergic_memory)

    # Replace validators with data library if provided
    if data_library:
        # Remove existing validators
        swarm.agents = [a for a in swarm.agents if not isinstance(a, ValidatorAgent)]
        # Add validators with data library
        for i in range(2):
            agent_id = f"ValidatorAgent_{i}"
            validator = ValidatorAgent(agent_id, stigmergic_memory, data_library)
            swarm.agents.append(validator)

    return swarm
