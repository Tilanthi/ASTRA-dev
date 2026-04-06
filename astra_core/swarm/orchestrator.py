"""
Swarm Orchestrator: Agent Coordination for V36 Hypothesis Exploration

Coordinates multiple swarm agents using pheromones and evolution to collectively
explore V36's hypothesis space.

Integration with V36:
- Explorer agents use HybridWorldGenerator
- Falsifier agents use DeepFalsificationEngine
- Analogist agents use CrossDomainAnalogyEngine
- Evolver agents use LEAPCoreEvolution

Date: 2025-11-27
Version: 37.0
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import time
import json
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed

from .pheromone_dynamics import DigitalPheromoneField, PheromoneType
from .leapcore_evolution import LEAPCoreEvolution, Chromosome


class AgentType(Enum):
    """Types of swarm agents"""
    EXPLORER = "explorer"        # Generates hybrid worlds
    FALSIFIER = "falsifier"      # Tests hypotheses against constraints
    ANALOGIST = "analogist"      # Discovers cross-domain connections
    EVOLVER = "evolver"          # Proposes meta-theory refinements


class AgentState(Enum):
    """Agent operational states"""
    IDLE = "idle"
    EXPLORING = "exploring"
    PROCESSING = "processing"
    WAITING = "waiting"
    TERMINATED = "terminated"


@dataclass
class AgentMessage:
    """Message passed between agents"""
    message_id: str
    sender_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    priority: int = 0


@dataclass
class AgentConfig:
    """Configuration for a swarm agent"""
    agent_type: AgentType
    exploration_radius: float = 0.15
    pheromone_sensitivity: float = 1.0
    communication_range: float = 0.3
    energy_decay: float = 0.01
    max_steps_per_task: int = 100


class SwarmAgent(ABC):
    """
    Abstract base class for swarm agents.

    Each agent:
    - Has a position in hypothesis space
    - Senses and deposits pheromones
    - Communicates with nearby agents
    - Performs type-specific tasks
    """

    def __init__(self, agent_id: str, config: AgentConfig,
                 pheromone_field: DigitalPheromoneField):
        self.agent_id = agent_id
        self.config = config
        self.pheromone_field = pheromone_field

        # State
        self.state = AgentState.IDLE
        self.position = self._random_position()
        self.energy = 1.0
        self.steps = 0

        # Communication
        self.inbox: Queue = Queue()
        self.outbox: Queue = Queue()

        # Results
        self.discoveries: List[Dict] = []
        self.task_history: List[Dict] = []

    def _random_position(self) -> Dict[str, Any]:
        """Generate random position in hypothesis space"""
        # Domain mixture (must sum to 1)
        weights = np.random.dirichlet([1, 1, 1])
        return {
            'domain_mixture': {
                'CLD': float(weights[0]),
                'D1': float(weights[1]),
                'D2': float(weights[2])
            },
            'template': np.random.choice([
                'stable_autoregressive', 'responsive_autoregressive',
                'delayed_response', 'nonlinear_exponential'
            ]),
            'role': np.random.choice([
                'slow_driver', 'fast_responder', 'mid_mediator'
            ])
        }

    def sense_environment(self) -> Dict[str, float]:
        """Sense pheromones at current position"""
        return self.pheromone_field.sense(
            self.position,
            radius=self.config.exploration_radius
        )

    def move(self, direction: Dict[str, float] = None):
        """Move in hypothesis space"""
        if direction is None:
            # Random walk
            direction = {
                'CLD': np.random.normal(0, 0.1),
                'D1': np.random.normal(0, 0.1),
                'D2': np.random.normal(0, 0.1)
            }

        # Update domain mixture
        dm = self.position['domain_mixture']
        new_dm = {
            'CLD': max(0, dm['CLD'] + direction['CLD'] * 0.1),
            'D1': max(0, dm['D1'] + direction['D1'] * 0.1),
            'D2': max(0, dm['D2'] + direction['D2'] * 0.1)
        }

        # Normalize
        total = sum(new_dm.values())
        if total > 0:
            new_dm = {k: v/total for k, v in new_dm.items()}

        self.position['domain_mixture'] = new_dm
