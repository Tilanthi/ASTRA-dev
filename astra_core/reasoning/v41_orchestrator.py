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
STAN V41 Orchestrator - Integrated AGI-like Reasoning System

The V41 Orchestrator is the central coordinator for all advanced reasoning
capabilities. It provides a unified interface for complex reasoning tasks
that automatically engages the appropriate combination of:

- Unified World Model: Shared belief state and knowledge representation
- Integration Bus: Cross-module communication and event handling
- Dynamic Replanning: Adaptive execution with real-time plan adjustment
- Counterfactual Reasoning: "What if" analysis and causal inference
- Analogical Reasoning: Cross-domain knowledge transfer
- Theory Synthesis: Pattern-to-law promotion and theory building
- Metacognition: Self-reflective reasoning quality monitoring
- Active Knowledge Acquisition: Goal-directed knowledge seeking
- Multi-Agent Deliberation: Internal debate and consensus building
- Continuous Learning: Experience-based improvement

This module represents a significant step toward AGI-like behavior by
enabling deep integration between previously independent reasoning modules.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Callable, Tuple
from enum import Enum, auto
from datetime import datetime
import uuid
import time
from collections import defaultdict

# Import all V41 components
from .unified_world_model import (
    get_world_model, UnifiedWorldModel, Belief, Hypothesis,
    CausalGraph, Constraint, Evidence
)
from .integration_bus import (
    get_integration_bus, IntegrationBus, EventType, EventPriority
)
from .dynamic_replanning import (
    DynamicExecutor, ReplanningEngine, ExecutionState
)
from .counterfactual_reasoning import (
    CounterfactualEngine, StructuralCausalModel, CounterfactualQuery
)
from .analogical_reasoning import (
    AnalogyFinder, StructureMapper, DomainRepresentation
)
from .theory_synthesis import (
    get_theory_synthesizer, TheorySynthesizer, Pattern, PatternType, Law
)
from .metacognition import (
    get_metacognitive_controller, MetacognitiveController,
    ReasoningStrategy, ReasoningTrace
)
from .active_knowledge_acquisition import (
    get_knowledge_acquirer, ActiveKnowledgeAcquirer, KnowledgeGap
)
from .multi_agent_deliberation import (
    get_deliberator, MultiAgentDeliberator, ConsensusLevel
)
from .continuous_learning import (
    get_continuous_learner, ContinuousLearner, Experience
)


class ReasoningMode(Enum):
    """Modes of reasoning"""
    ANALYTICAL = auto()        # Deep analysis, systematic
    CREATIVE = auto()          # Novel solutions, analogical
    CRITICAL = auto()          # Evaluation, falsification
    INTEGRATIVE = auto()       # Synthesis, unification
    ADAPTIVE = auto()          # Dynamic, responsive
    DELIBERATIVE = auto()      # Multi-perspective consideration


class TaskComplexity(Enum):
    """Task complexity levels"""
    TRIVIAL = auto()           # Direct lookup or simple inference
    SIMPLE = auto()            # Single-step reasoning
    MODERATE = auto()          # Multi-step, single domain
    COMPLEX = auto()           # Multi-step, multi-domain
    EXPERT = auto()            # Requires specialized knowledge
    FRONTIER = auto()          # At limits of capability


@dataclass
class ReasoningTask:
    """A reasoning task to be orchestrated"""
    task_id: str
    description: str
    domain: str

    # Task specification
    objective: str
    constraints: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    complexity: TaskComplexity = TaskComplexity.MODERATE
    preferred_mode: Optional[ReasoningMode] = None
    time_budget_seconds: float = 60.0

    # Status
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"TASK-{uuid.uuid4().hex[:8]}"


@dataclass
class ReasoningResult:
    """Result of orchestrated reasoning"""
    task_id: str
    success: bool

    # Main output
    conclusion: str
    confidence: float
    evidence: List[str]

    # Process information
    reasoning_trace: List[Dict[str, Any]]
    capabilities_used: List[str]
    time_taken_seconds: float

    # Quality metrics
    coherence: float = 0.0
    completeness: float = 0.0
    novelty: float = 0.0

    # Insights generated
    hypotheses_generated: List[str] = field(default_factory=list)
    knowledge_gaps_identified: List[str] = field(default_factory=list)
    patterns_discovered: List[str] = field(default_factory=list)

    # Metadata
    mode_used: Optional[ReasoningMode] = None
    consensus_level: Optional[str] = None


class CapabilityRouter:
    """Routes tasks to appropriate capabilities"""

    def __init__(self):
        self.routing_rules = {
            # Keywords -> capabilities
            "cause": ["counterfactual", "causal_inference"],
            "effect": ["counterfactual", "causal_inference"],
            "what if": ["counterfactual"],
            "alternative": ["counterfactual", "deliberation"],
            "similar": ["analogical"],
            "like": ["analogical"],
            "pattern": ["theory_synthesis", "continuous_learning"],
            "theory": ["theory_synthesis"],
            "law": ["theory_synthesis"],
            "uncertain": ["metacognition", "knowledge_acquisition"],
            "unknown": ["knowledge_acquisition"],
            "debate": ["deliberation"],
            "consensus": ["deliberation"],
            "learn": ["continuous_learning"],
            "improve": ["continuous_learning", "metacognition"],
        }

        self.mode_capabilities = {
            ReasoningMode.ANALYTICAL: ["counterfactual", "theory_synthesis", "metacognition"],
            ReasoningMode.CREATIVE: ["analogical", "theory_synthesis"],
            ReasoningMode.CRITICAL: ["counterfactual", "deliberation", "metacognition"],
            ReasoningMode.INTEGRATIVE: ["theory_synthesis", "deliberation", "world_model"],
            ReasoningMode.ADAPTIVE: ["dynamic_replanning", "continuous_learning"],
            ReasoningMode.DELIBERATIVE: ["deliberation", "metacognition"],
        }

    def route(
        self,
        task: ReasoningTask
    ) -> List[str]:
        """Determine which capabilities to engage"""
        capabilities = set()

        # Route based on keywords
        task_lower = (task.description + " " + task.objective).lower()
        for keyword, caps in self.routing_rules.items():
            if keyword in task_lower:
                capabilities.update(caps)

        # Route based on preferred mode
        if task.preferred_mode:
            capabilities.update(self.mode_capabilities.get(task.preferred_mode, []))

        # Always include core capabilities for complex tasks
        if task.complexity in [TaskComplexity.COMPLEX, TaskComplexity.EXPERT, TaskComplexity.FRONTIER]:
            capabilities.update(["world_model", "metacognition", "integration_bus"])

        # Default capabilities if none selected
        if not capabilities:
            capabilities = {"world_model", "metacognition"}

        return list(capabilities)


class V41Orchestrator:
    """
    Main STAN V41 Orchestrator.

    Coordinates all advanced reasoning capabilities for AGI-like behavior.
    """

    VERSION = "41.0"

    def __init__(self):
        # Core components (singletons)
        self.world_model: UnifiedWorldModel = get_world_model()
        self.bus: IntegrationBus = get_integration_bus()
        self.theory_synthesizer: TheorySynthesizer = get_theory_synthesizer()
        self.metacognition: MetacognitiveController = get_metacognitive_controller()
        self.knowledge_acquirer: ActiveKnowledgeAcquirer = get_knowledge_acquirer()
        self.deliberator: MultiAgentDeliberator = get_deliberator()
        self.learner: ContinuousLearner = get_continuous_learner()

        # Non-singleton components
        self.counterfactual_engine = CounterfactualEngine()
        self.analogy_finder = AnalogyFinder()
        self.dynamic_executor = DynamicExecutor()

        # Orchestration
        self.router = CapabilityRouter()
        self.active_tasks: Dict[str, ReasoningTask] = {}
        self.completed_results: Dict[str, ReasoningResult] = {}

        # Statistics
        self.tasks_completed = 0
        self.total_reasoning_time = 0.0
        self.capability_usage: Dict[str, int] = defaultdict(int)

        # Set up event handlers
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Set up cross-module event handlers"""
        # Log all events for debugging
        def log_event(event):
            pass  # Can be enabled for debugging

        self.bus.subscribe("orchestrator_logger", EventType.CAPABILITY_RESULT, log_event)

        # Connect metacognition to learning
        def on_insight(event):
            insight = event.payload
            if insight.get("actionable"):
                self.learner.add_knowledge(
                    content=insight.get("description", ""),
                    domain="metacognition",
                    knowledge_type="insight",
                    source="metacognition",
                    confidence=insight.get("confidence", 0.5)
                )

        self.bus.subscribe("orchestrator_insight", EventType.METACOGNITIVE_INSIGHT, on_insight)

    def reason(
        self,
        description: str,
        objective: str,
        domain: str = "general",
        context: Dict[str, Any] = None,
        mode: ReasoningMode = None,
        time_budget: float = 60.0
    ) -> ReasoningResult:
        """
        Main reasoning entry point.

        Orchestrates all V41 capabilities to address a reasoning task.
        """
        # Create task
        task = ReasoningTask(
            task_id="",
            description=description,
            objective=objective,
            domain=domain,
            context=context or {},
            complexity=self._assess_complexity(description, objective),
            preferred_mode=mode,
            time_budget_seconds=time_budget
        )

        self.active_tasks[task.task_id] = task
        task.status = "active"
        task.started_at = datetime.now()

        start_time = time.time()

        # Begin metacognitive tracking
