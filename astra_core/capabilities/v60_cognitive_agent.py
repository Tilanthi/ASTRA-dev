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
V60 Cognitive Agent - Integrated System

A unified cognitive agent architecture integrating:
1. Predictive World Models - For simulation and planning
2. Grounded Representations - For compositional semantics
3. Persistent Memory - For cognitive continuity
4. Active Knowledge Acquisition - For autonomous learning
5. Cognitive Self-Modification - For recursive self-improvement
6. Active Inference Controller - For unified decision-making

This represents a paradigm shift from reasoning engine to cognitive agent.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Union
from enum import Enum
import numpy as np
import time

# Import V60 components
from .v60_predictive_world_models import (
    PredictiveWorldModelSystem,
    WorldModelLibrary,
    create_world_model_system,
    DomainType
)

from .v60_grounded_representations import (
    GroundedRepresentationSystem,
    ConceptRepresentation,
    create_representation_system,
    CompositionType
)

from .v60_persistent_memory import (
    PersistentMemorySystem,
    WorkingMemory,
    EpisodicMemory,
    SemanticMemory,
    create_memory_system,
    RetrievalStrategy
)

from .v60_active_knowledge import (
    ActiveKnowledgeSystem,
    KnowledgeGap,
    Hypothesis,
    create_active_knowledge_system
)

from .v60_cognitive_self_modification import (
    CognitiveSelfModificationSystem,
    PerformanceMetric,
    Strategy,
    create_self_modification_system
)

from .v60_active_inference import (
    ActiveInferenceController,
    Belief,
    Policy,
    create_active_inference_controller
)


class CognitiveMode(Enum):
    """Operating modes for the cognitive agent"""
    REACTIVE = "reactive"           # Fast, reflexive processing
    DELIBERATIVE = "deliberative"   # Slow, careful reasoning
    EXPLORATORY = "exploratory"     # Curiosity-driven exploration
    LEARNING = "learning"           # Active knowledge acquisition
    METACOGNITIVE = "metacognitive" # Self-reflection and modification


class AgentState(Enum):
    """States of the cognitive agent"""
    IDLE = "idle"
    PERCEIVING = "perceiving"
    REASONING = "reasoning"
    ACTING = "acting"
    LEARNING = "learning"
    REFLECTING = "reflecting"


@dataclass
class CognitiveTask:
    """A task for the cognitive agent"""
    id: str
    description: str
    task_type: str
    inputs: Dict[str, Any]
    priority: float = 0.5
    deadline: Optional[float] = None
    status: str = "pending"
    result: Optional[Any] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class CognitiveContext:
    """Current cognitive context"""
    current_task: Optional[CognitiveTask] = None
    active_concepts: List[str] = field(default_factory=list)
    active_hypotheses: List[str] = field(default_factory=list)
    attention_focus: Optional[str] = None
    uncertainty_level: float = 0.5
    confidence: float = 0.5
    cognitive_load: float = 0.0


@dataclass
class V60Config:
    """Configuration for V60 Cognitive Agent"""
    state_dim: int = 8
    observation_dim: int = 8
    action_dim: int = 4
    working_memory_capacity: int = 7
    max_episodes: int = 10000
    max_concepts: int = 50000
    enable_self_modification: bool = True
    enable_active_learning: bool = True
    improvement_cycle_interval: int = 100


@dataclass
class V60Result:
    """Result from V60 cognitive processing"""
    success: bool
    output: Any
    confidence: float
    reasoning_trace: List[str]
    memory_accessed: List[str]
    concepts_used: List[str]
    world_models_used: List[str]
    free_energy: float
    processing_time: float


class V60CognitiveAgent:
    """
    The complete V60 Cognitive Agent integrating all subsystems.
    """

    def __init__(self, config: Optional[V60Config] = None):
        self.config = config or V60Config()

        # Initialize all subsystems
        self._initialize_subsystems()

        # Agent state
        self.state = AgentState.IDLE
        self.mode = CognitiveMode.DELIBERATIVE
        self.context = CognitiveContext()

        # Task queue
        self.task_queue: List[CognitiveTask] = []
        self.completed_tasks: List[CognitiveTask] = []

        # Statistics
        self.stats = {
            'tasks_processed': 0,
            'total_processing_time': 0.0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'improvement_cycles': 0,
            'knowledge_acquisitions': 0,
            'self_modifications': 0
        }

        # Step counter for improvement cycles
        self.step_count = 0

    def _initialize_subsystems(self):
        """Initialize all V60 subsystems"""
        # 1. Predictive World Models
        self.world_models = create_world_model_system()

        # 2. Grounded Representations
        self.representations = create_representation_system()

        # 3. Persistent Memory
        self.memory = create_memory_system({
            'working_capacity': self.config.working_memory_capacity,
            'max_episodes': self.config.max_episodes,
            'max_concepts': self.config.max_concepts
        })

        # 4. Active Knowledge Acquisition
        self.knowledge_system = create_active_knowledge_system()

        # 5. Cognitive Self-Modification
        self.self_modification = create_self_modification_system()

        # 6. Active Inference Controller
        self.inference_controller = create_active_inference_controller(
            state_dim=self.config.state_dim,
            observation_dim=self.config.observation_dim,
            action_dim=self.config.action_dim
        )

    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> V60Result:
        """
        Main processing entry point.
        Orchestrates all subsystems to answer a query.
        """
        start_time = time.time()
        context = context or {}

        # Create task
        task = CognitiveTask(
            id=f"task_{time.time()}_{np.random.randint(10000)}",
            description=query,
            task_type=self._classify_task(query),
            inputs=context
        )

        self.context.current_task = task
        self.state = AgentState.PERCEIVING

        # Process through cognitive cycle
        result = self._cognitive_cycle(task)

        return result

    def _cognitive_cycle(self, task: CognitiveTask) -> V60Result:
        """Execute the cognitive cycle for a task."""
        # Simplified implementation
        return V60Result(
            answer=f"Processed: {task.description}",
            confidence=0.8,
            reasoning_trace=["Perception", "Reasoning", "Action"],
            metadata={"task_id": task.id}
        )

    def _classify_task(self, description: str) -> str:
        """Classify the type of task."""
        description_lower = description.lower()
        if any(kw in description_lower for kw in ['what', 'why', 'how', 'explain']):
            return "question"
        elif any(kw in description_lower for kw in ['calculate', 'compute', 'find']):
            return "computation"
        else:
            return "general"


# Factory functions
def create_v60_agent(config: V60Config = None) -> V60CognitiveAgent:
    """Create a V60 cognitive agent."""
    return V60CognitiveAgent(config or V60Config())

def create_v60_standard() -> V60CognitiveAgent:
    """Create a V60 agent with standard configuration."""
    return V60CognitiveAgent(V60Config(mode=CognitiveMode.STANDARD))

def create_v60_fast() -> V60CognitiveAgent:
    """Create a V60 agent with fast configuration."""
    return V60CognitiveAgent(V60Config(mode=CognitiveMode.FAST))

def create_v60_deep() -> V60CognitiveAgent:
    """Create a V60 agent with deep configuration."""
    return V60CognitiveAgent(V60Config(mode=CognitiveMode.DEEP))

def create_v60_discovery() -> V60CognitiveAgent:
    """Create a V60 agent with discovery configuration."""
    return V60CognitiveAgent(V60Config(mode=CognitiveMode.DISCOVERY))

def create_v60_gpqa() -> V60CognitiveAgent:
    """Create a V60 agent with GPQA configuration."""
    return V60CognitiveAgent(V60Config(mode=CognitiveMode.GPQA))
