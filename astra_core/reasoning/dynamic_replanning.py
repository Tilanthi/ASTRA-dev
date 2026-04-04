"""
Dynamic Replanning Engine for STAN V41

Adaptive execution based on intermediate results.
Supports:
- Real-time plan adjustment based on confidence
- Early stopping when threshold reached
- Capability prioritization by expected information gain
- Graceful degradation on failures

Date: 2025-12-11
Version: 41.0
"""

import time
import uuid
import math
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import heapq

from .unified_world_model import UnifiedWorldModel, BeliefState, get_world_model
from .integration_bus import IntegrationBus, EventType, get_integration_bus


class ExecutionStatus(Enum):
    """Status of execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    REPLANNED = "replanned"


class StoppingReason(Enum):
    """Reasons for stopping execution"""
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    TIME_LIMIT = "time_limit"
    NO_INFORMATION_GAIN = "no_information_gain"
    ALL_COMPLETED = "all_completed"
    USER_INTERRUPT = "user_interrupt"
    FATAL_ERROR = "fatal_error"
    HYPOTHESIS_CONFIRMED = "hypothesis_confirmed"


@dataclass
class CapabilityExecution:
    """Tracks execution of a single capability"""
    capability_id: str
    capability_name: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    priority: float = 0.5
    expected_info_gain: float = 0.5
    expected_duration: float = 1.0
    actual_duration: float = 0.0
    result: Any = None
    confidence: float = 0.0
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    dependencies: Set[str] = field(default_factory=set)
    triggered_replanning: bool = False


@dataclass
class ExecutionState:
    """Current state of execution"""
    plan_id: str
    capabilities: Dict[str, CapabilityExecution]
    current_confidence: float = 0.0
    total_info_gain: float = 0.0
    elapsed_time: float = 0.0
    remaining_budget: float = 60.0  # seconds
    iteration: int = 0
    belief_snapshots: List[BeliefState] = field(default_factory=list)


@dataclass
class ReplanningDecision:
    """A decision about replanning"""
    should_replan: bool
    reason: str
    recommended_actions: List[str]
    priority_adjustments: Dict[str, float]
    capabilities_to_add: List[str]
    capabilities_to_skip: List[str]


class InformationGainEstimator:
    """Estimates expected information gain from capabilities"""

    def __init__(self, world_model: UnifiedWorldModel):
        self.world_model = world_model
        self.historical_gains: Dict[str, List[float]] = defaultdict(list)

    def estimate(self, capability: str, current_uncertainty: float) -> float:
        """
        Estimate expected information gain from running a capability.

        Args:
            capability: Name of capability
            current_uncertainty: Current entropy/uncertainty

        Returns:
            Expected information gain (0-1)
        """
        # Base estimates by capability type
        base_gains = {
            'symbolic_math': 0.7,
            'proof_validator': 0.8,
            'causal_discovery': 0.6,
            'abductive_inference': 0.5,
            'active_experiment': 0.7,
            'quantitative_reasoner': 0.6,
            'external_knowledge': 0.5,
            'llm_inference': 0.4,
            'episodic_memory': 0.3,
            'meta_learning': 0.3,
            'wolfram_alpha': 0.8,
            'arxiv': 0.4,
            'wikipedia': 0.3
        }

        base = base_gains.get(capability, 0.4)

        # Adjust based on current uncertainty
        # Higher uncertainty = more potential gain
        uncertainty_factor = current_uncertainty

        # Adjust based on historical performance
        if capability in self.historical_gains and self.historical_gains[capability]:
            historical_avg = sum(self.historical_gains[capability][-10:]) / min(10, len(self.historical_gains[capability]))
            base = 0.7 * base + 0.3 * historical_avg

        return base * uncertainty_factor

    def record_actual_gain(self, capability: str, gain: float):
        """Record actual information gain for learning"""
        self.historical_gains[capability].append(gain)
        # Keep only recent history
        if len(self.historical_gains[capability]) > 100:
            self.historical_gains[capability] = self.historical_gains[capability][-100:]


class ReplanningEngine:
    """
    Determines when and how to replan during execution.
    """

    def __init__(self,
                 confidence_threshold: float = 0.85,
                 min_info_gain: float = 0.05,
                 max_iterations: int = 10):
        self.confidence_threshold = confidence_threshold
        self.min_info_gain = min_info_gain
        self.max_iterations = max_iterations

    def should_replan(self, state: ExecutionState,
                      latest_result: CapabilityExecution) -> ReplanningDecision:
        """
        Determine if replanning is needed based on latest result.

        Args:
            state: Current execution state
            latest_result: Result from most recently executed capability

        Returns:
            ReplanningDecision with recommendations
        """
        recommendations = []
        priority_adjustments = {}
        to_add = []
        to_skip = []

        # Check if we should stop (high confidence)
        if state.current_confidence >= self.confidence_threshold:
            return ReplanningDecision(
                should_replan=False,
                reason=f"Confidence threshold reached: {state.current_confidence:.2f}",
                recommended_actions=["stop_execution"],
                priority_adjustments={},
                capabilities_to_add=[],
                capabilities_to_skip=list(
                    k for k, v in state.capabilities.items()
                    if v.status == ExecutionStatus.PENDING
                )
            )

        # Check for diminishing returns
        recent_gains = [
            c.confidence for c in state.capabilities.values()
            if c.status == ExecutionStatus.COMPLETED
        ][-3:]

        if len(recent_gains) >= 3 and max(recent_gains) < self.min_info_gain:
            return ReplanningDecision(
                should_replan=True,
                reason="Diminishing information gains",
                recommended_actions=["add_different_capabilities", "increase_exploration"],
                priority_adjustments={},
                capabilities_to_add=['active_experiment', 'external_knowledge'],
                capabilities_to_skip=[]
            )

        # Check for failure patterns
        failed = [
            c for c in state.capabilities.values()
            if c.status == ExecutionStatus.FAILED
        ]

        if len(failed) >= 2:
            recommendations.append("investigate_failures")
            # Deprioritize similar capabilities
            for f in failed:
                for cap_id, cap in state.capabilities.items():
                    if cap.capability_name == f.capability_name and cap.status == ExecutionStatus.PENDING:
                        priority_adjustments[cap_id] = -0.3

        # Check iteration limit
        if state.iteration >= self.max_iterations:
            return ReplanningDecision(
                should_replan=False,
                reason="Maximum iterations reached",
                recommended_actions=["stop_execution"],
                priority_adjustments={},
                capabilities_to_add=[],
                capabilities_to_skip=[]
            )

        # Check time budget
        if state.remaining_budget < 5.0:
            # Skip slow capabilities
            for cap_id, cap in state.capabilities.items():
                if cap.status == ExecutionStatus.PENDING and cap.expected_duration > state.remaining_budget:
                    to_skip.append(cap_id)

        # Suggest adding capabilities if uncertainty is high
        if state.current_confidence < 0.5:
            if 'external_knowledge' not in [c.capability_name for c in state.capabilities.values()]:
                to_add.append('external_knowledge')
            if 'llm_inference' not in [c.capability_name for c in state.capabilities.values()]:
                to_add.append('llm_inference')

        should_replan = bool(priority_adjustments or to_add or to_skip)

        return ReplanningDecision(
            should_replan=should_replan,
            reason="Optimization based on current results" if should_replan else "Continue current plan",
            recommended_actions=recommendations,
            priority_adjustments=priority_adjustments,
            capabilities_to_add=to_add,
            capabilities_to_skip=to_skip
        )


class DynamicExecutor:
    """
    Executes capabilities with dynamic replanning.

    The main execution loop that:
    1. Selects next capability by priority/info gain
    2. Executes capability
    3. Updates beliefs and confidence
    4. Checks for replanning needs
    5. Adjusts plan as needed
    6. Repeats until stopping condition
    """

    def __init__(self,
                 world_model: Optional[UnifiedWorldModel] = None,
                 bus: Optional[IntegrationBus] = None,
                 confidence_threshold: float = 0.85,
                 time_budget: float = 60.0):
        self.world_model = world_model or get_world_model()
        self.bus = bus or get_integration_bus()
        self.confidence_threshold = confidence_threshold
        self.time_budget = time_budget

        self.info_estimator = InformationGainEstimator(self.world_model)
        self.replanning_engine = ReplanningEngine(confidence_threshold)

        # Capability executors (to be registered)
        self.executors: Dict[str, Callable] = {}

        # Execution history
        self.execution_history: List[ExecutionState] = []

    def register_executor(self, capability_name: str, executor: Callable):
        """Register an executor function for a capability"""
        self.executors[capability_name] = executor

    def execute(self,
                problem: str,
                initial_capabilities: List[str],
                context: Optional[Dict] = None) -> Tuple[Any, ExecutionState]:
        """
        Execute capabilities with dynamic replanning.

        Args:
            problem: Problem description
            initial_capabilities: Initial set of capabilities to try
            context: Additional context

        Returns:
            Tuple of (result, final_state)
        """
        context = context or {}
        start_time = time.time()

        # Initialize execution state
        state = ExecutionState(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            capabilities={},
            remaining_budget=self.time_budget
        )

        # Initialize capabilities
        current_uncertainty = self.world_model.get_entropy()

        for cap_name in initial_capabilities:
            cap_id = f"{cap_name}_{uuid.uuid4().hex[:6]}"
            info_gain = self.info_estimator.estimate(cap_name, current_uncertainty)

            state.capabilities[cap_id] = CapabilityExecution(
                capability_id=cap_id,
                capability_name=cap_name,
                priority=info_gain,
                expected_info_gain=info_gain
            )

        # Take initial belief snapshot
        state.belief_snapshots.append(self.world_model.belief_state.snapshot())

        # Publish start event
        correlation_id = f"exec_{state.plan_id}"
        self.bus.publish(
            EventType.CAPABILITY_STARTED,
            "dynamic_executor",
            {'plan_id': state.plan_id, 'capabilities': initial_capabilities},
            correlation_id=correlation_id
        )

        # Main execution loop
        stopping_reason = None

        while True:
            state.iteration += 1
            state.elapsed_time = time.time() - start_time
            state.remaining_budget = self.time_budget - state.elapsed_time

            # Check stopping conditions
            if state.current_confidence >= self.confidence_threshold:
                stopping_reason = StoppingReason.CONFIDENCE_THRESHOLD
                break

            if state.remaining_budget <= 0:
                stopping_reason = StoppingReason.TIME_LIMIT
                break

            # Select next capability
            next_cap = self._select_next_capability(state)

            if not next_cap:
                stopping_reason = StoppingReason.ALL_COMPLETED
                break

            # Execute capability
            result = self._execute_capability(next_cap, problem, context, correlation_id)

            # Update state
            state.current_confidence = self._calculate_confidence(state)
            state.total_info_gain += result.confidence if result.status == ExecutionStatus.COMPLETED else 0

            # Check for replanning
            decision = self.replanning_engine.should_replan(state, result)

            if decision.should_replan:
                self._apply_replanning(state, decision, current_uncertainty)
                result.triggered_replanning = True

            # Take belief snapshot
            state.belief_snapshots.append(self.world_model.belief_state.snapshot())

            # Check for early stopping signals
            if "stop_execution" in decision.recommended_actions:
                stopping_reason = StoppingReason.CONFIDENCE_THRESHOLD
                break

        # Finalize
        final_result = self._aggregate_results(state)

        # Publish completion
        self.bus.publish(
            EventType.CAPABILITY_COMPLETED,
            "dynamic_executor",
            {
                'plan_id': state.plan_id,
                'result': final_result,
                'confidence': state.current_confidence,
                'stopping_reason': stopping_reason.value if stopping_reason else 'unknown',
                'iterations': state.iteration,
                'elapsed_time': state.elapsed_time
            },
            correlation_id=correlation_id
        )

        self.execution_history.append(state)

        return final_result, state

    def _select_next_capability(self, state: ExecutionState) -> Optional[CapabilityExecution]:
        """Select next capability to execute based on priority and info gain"""
        pending = [
            cap for cap in state.capabilities.values()
            if cap.status == ExecutionStatus.PENDING
        ]

        if not pending:
            return None

        # Check dependencies
        ready = []
        for cap in pending:
            deps_satisfied = all(
                state.capabilities.get(dep, CapabilityExecution("", "")).status == ExecutionStatus.COMPLETED
                for dep in cap.dependencies
            )
            if deps_satisfied:
                ready.append(cap)

        if not ready:
            return None

        # Select by priority (higher is better)
        return max(ready, key=lambda c: c.priority)

    def _execute_capability(self, cap: CapabilityExecution,
                            problem: str, context: Dict,
                            correlation_id: str) -> CapabilityExecution:
        """Execute a single capability"""
        cap.status = ExecutionStatus.RUNNING
        cap.started_at = time.time()

        # Publish start
        self.bus.publish(
            EventType.CAPABILITY_STARTED,
            {'capability': cap.name, 'correlation_id': correlation_id}
        )

        try:
            # Execute the capability
            result = self.capabilities[cap.name].execute(problem, context)
            cap.status = ExecutionStatus.COMPLETED
            cap.completed_at = time.time()
            cap.result = result

            # Publish completion
            self.bus.publish(
                EventType.CAPABILITY_COMPLETED,
                {'capability': cap.name, 'correlation_id': correlation_id, 'result': result}
            )
        except Exception as e:
            cap.status = ExecutionStatus.FAILED
            cap.error = str(e)
            cap.completed_at = time.time()

            # Publish failure
            self.bus.publish(
                EventType.CAPABILITY_FAILED,
                {'capability': cap.name, 'correlation_id': correlation_id, 'error': str(e)}
            )

        return cap
