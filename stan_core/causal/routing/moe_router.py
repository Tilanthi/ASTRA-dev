#!/usr/bin/env python3
"""
Mixture-of-Experts (MoE) Inspired Capability Router for STAN_IX_ASTRO

This module implements a learned routing mechanism inspired by:
"Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Approach"
(Shazeer et al., 2017)

Key principles applied:
1. Conditional computation - only activate relevant capabilities per task
2. Learned routing with expert specialization scores
3. Top-k routing to limit computational overhead
4. Load balancing across capabilities
5. Adaptive routing based on task patterns
"""

from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
import numpy as np
from collections import defaultdict
import time


class TaskType(Enum):
    """Categories of tasks for routing decisions."""
    CAUSAL_ANALYSIS = "causal_analysis"
    DISCOVERY = "discovery"
    SIMULATION = "simulation"
    TRADING = "trading"
    ASTRONOMY = "astronomy"
    MEMORY = "memory"
    REASONING = "reasoning"
    METACOGNITIVE = "metacognitive"
    CREATIVE = "creative"
    GENERAL = "general"


@dataclass
class Expert:
    """Represents a specialized capability/expert in the system."""
    name: str
    module_path: str
    task_types: List[TaskType]
    specialization_keywords: List[str]
    base_score: float = 1.0
    current_load: float = 0.0
    avg_response_time: float = 0.0
    success_rate: float = 1.0
    usage_count: int = 0


@dataclass
class RoutingDecision:
    """Records a routing decision for transparency and learning."""
    task: str
    selected_experts: List[str]
    expert_scores: Dict[str, float]
    task_type: TaskType
    timestamp: float = field(default_factory=time.time)
    execution_time: float = 0.0


class MoECapabilityRouter:
    """
    Mixture-of-Experts inspired router for dynamic capability selection.

    This router analyzes incoming tasks and routes them to the most relevant
    specialized capabilities, implementing:
    - Task type classification
    - Expert relevance scoring
    - Top-k selection (typically k=2-3 experts)
    - Load balancing
    - Adaptive learning from routing outcomes
    """

    def __init__(self, top_k: int = 3, min_score_threshold: float = 0.1):
        """
        Initialize the MoE router.

        Parameters
        ----------
        top_k : int
            Maximum number of experts to activate per task
        min_score_threshold : float
            Minimum relevance score for expert selection
        """
        self.top_k = top_k
        self.min_score_threshold = min_score_threshold
        self.experts: Dict[str, Expert] = {}
        self.routing_history: List[RoutingDecision] = []
        self.task_embeddings: Dict[str, np.ndarray] = {}
        self.expert_task_affinity: Dict[Tuple[str, TaskType], float] = defaultdict(float)

        self._initialize_default_experts()

    def _initialize_default_experts(self):
        """Initialize the default set of STAN experts with their specializations."""
        experts_config = [
            # Causal reasoning experts
            Expert(
                name="structural_causal_model",
                module_path="stan_core.causal.model.scm.StructuralCausalModel",
                task_types=[TaskType.CAUSAL_ANALYSIS, TaskType.REASONING],
                specialization_keywords=[
                    "causal", "causation", "intervention", "counterfactual",
                    "structural", "scm", "dag", "directed", "acyclic"
                ]
            ),
            Expert(
                name="pc_algorithm",
                module_path="stan_core.causal.discovery.pc_algorithm.PCAlgorithm",
                task_types=[TaskType.CAUSAL_ANALYSIS, TaskType.DISCOVERY],
                specialization_keywords=[
                    "pc algorithm", "causal discovery", "graph", "skeleton",
                    "orientation", "conditional independence"
                ]
            ),
            Expert(
                name="intervention_planning",
                module_path="stan_core.causal.intervention.planner",
                task_types=[TaskType.CAUSAL_ANALYSIS, TaskType.REASONING],
                specialization_keywords=[
                    "intervention", "action", "effect", "impact", "change"
                ]
            ),
            Expert(
                name="counterfactual_reasoning",
                module_path="stan_core.causal.counterfactual.engine",
                task_types=[TaskType.CAUSAL_ANALYSIS, TaskType.REASONING],
                specialization_keywords=[
                    "counterfactual", "what if", "would have", "had been"
                ]
            ),

            # Discovery experts
            Expert(
                name="scientific_discovery",
                module_path="stan_core.discovery.engine.DiscoveryEngine",
                task_types=[TaskType.DISCOVERY, TaskType.ASTRONOMY],
                specialization_keywords=[
                    "discover", "hypothesis", "experiment", "theory",
                    "pattern", "novel", "innovation"
                ]
            ),
            Expert(
                name="data_analyzer",
                module_path="stan_core.discovery.analysis.DataAnalyzer",
                task_types=[TaskType.DISCOVERY, TaskType.ASTRONOMY, TaskType.TRADING],
                specialization_keywords=[
                    "analyze data", "statistics", "distribution", "correlation",
                    "regression", "fit", "model"
                ]
            ),

            # Memory experts
            Expert(
                name="episodic_memory",
                module_path="stan_core.memory.episodic.memory.EpisodicMemory",
                task_types=[TaskType.MEMORY, TaskType.METACOGNITIVE],
                specialization_keywords=[
                    "remember", "recall", "past", "experience", "episodic",
                    "when did", "previous"
                ]
            ),
            Expert(
                name="semantic_memory",
                module_path="stan_core.memory.semantic.memory.SemanticMemory",
                task_types=[TaskType.MEMORY, TaskType.REASONING],
                specialization_keywords=[
                    "concept", "knowledge", "fact", "semantic", "definition",
                    "meaning", "relationship"
                ]
            ),
            Expert(
                name="working_memory",
                module_path="stan_core.memory.working.memory.WorkingMemory",
                task_types=[TaskType.MEMORY, TaskType.REASONING],
                specialization_keywords=[
                    "hold", "maintain", "current", "active", "focus",
                    "working", "short term"
                ]
            ),
            Expert(
                name="vector_search",
                module_path="stan_core.memory.vector.store.VectorStore",
                task_types=[TaskType.MEMORY],
                specialization_keywords=[
                    "search", "similar", "find", "retrieve", "vector",
                    "embedding", "nearest"
                ]
            ),

            # Metacognitive experts
            Expert(
                name="metacognitive_monitor",
                module_path="stan_core.metacognitive.monitoring.Monitor",
                task_types=[TaskType.METACOGNITIVE],
                specialization_keywords=[
                    "monitor", "reflect", "self-aware", "assess", "evaluate",
                    "confidence", "uncertainty"
                ]
            ),
            Expert(
                name="goal_manager",
                module_path="stan_core.metacognitive.goals.GoalManager",
                task_types=[TaskType.METACOGNITIVE, TaskType.REASONING],
                specialization_keywords=[
                    "goal", "objective", "target", "plan", "achieve",
                    "strategy"
                ]
            ),

            # Simulation experts
            Expert(
                name="physics_simulator",
                module_path="stan_core.simulation.physics.PhysicsSimulator",
                task_types=[TaskType.SIMULATION, TaskType.ASTRONOMY],
                specialization_keywords=[
                    "physics", "simulate", "gravity", "force", "motion",
                    "dynamics", "trajectory"
                ]
            ),
            Expert(
                name="astronomy_simulator",
                module_path="stan_core.simulation.astronomy.AstronomySimulator",
                task_types=[TaskType.SIMULATION, TaskType.ASTRONOMY],
                specialization_keywords=[
                    "astronomy", "stellar", "galactic", "cosmic", "orbit",
                    "observation", "telescope"
                ]
            ),
            Expert(
                name="market_simulator",
                module_path="stan_core.simulation.market.MarketSimulator",
                task_types=[TaskType.SIMULATION, TaskType.TRADING],
                specialization_keywords=[
                    "market", "price", "trading", "stock", "simulate market",
                    "order book"
                ]
            ),

            # Trading experts
            Expert(
                name="causal_trading",
                module_path="stan_core.trading.analysis.CausalTrading",
                task_types=[TaskType.TRADING, TaskType.CAUSAL_ANALYSIS],
                specialization_keywords=[
                    "trading", "market", "causal market", "price movement",
                    "trading signal", "entry", "exit"
                ]
            ),
            Expert(
                name="backtest_engine",
                module_path="stan_core.trading.backtest.BacktestEngine",
                task_types=[TaskType.TRADING],
                specialization_keywords=[
                    "backtest", "historical", "test strategy", "validate",
                    "performance"
                ]
            ),

            # Astronomy experts
            Expert(
                name="astro_analysis",
                module_path="stan_core.astronomy.analysis.Analyzer",
                task_types=[TaskType.ASTRONOMY],
                specialization_keywords=[
                    "astronomical data", "fits", "spectral", "photometry",
                    "analyze observation"
                ]
            ),

            # Creative experts
            Expert(
                name="analogy_engine",
                module_path="stan_core.creative.analogy.AnalogyEngine",
                task_types=[TaskType.CREATIVE, TaskType.REASONING],
                specialization_keywords=[
                    "analogy", "similar to", "like", "metaphor", "compare"
                ]
            ),
            Expert(
                name="insight_generator",
                module_path="stan_core.creative.insight.InsightGenerator",
                task_types=[TaskType.CREATIVE, TaskType.DISCOVERY],
                specialization_keywords=[
                    "insight", "realization", "aha", "breakthrough", "novel"
                ]
            ),

            # General reasoning
            Expert(
                name="bayesian_inference",
                module_path="stan_core.capabilities.bayesian_inference",
                task_types=[TaskType.REASONING, TaskType.GENERAL],
                specialization_keywords=[
                    "bayesian", "prior", "posterior", "likelihood", "probability",
                    "uncertainty", "belief"
                ]
            ),
            Expert(
                name="gpqa_solver",
                module_path="stan_core.capabilities.gpqa_strategies",
                task_types=[TaskType.REASONING, TaskType.DISCOVERY],
                specialization_keywords=[
                    "gpqa", "graduate level", "science", "physics", "chemistry",
                    "biology", "math", "complex reasoning"
                ]
            ),
        ]

        for expert in experts_config:
            self.experts[expert.name] = expert

    def classify_task(self, task: str) -> Tuple[TaskType, float]:
        """
        Classify the task type based on keyword matching and semantic patterns.

        Returns tuple of (task_type, confidence)
        """
        task_lower = task.lower()

        # Keyword-based scoring for each task type
        type_scores = {}

        for task_type in TaskType:
            # Check experts specializing in this type
            relevant_keywords = []
            for expert in self.experts.values():
                if task_type in expert.task_types:
                    relevant_keywords.extend(expert.specialization_keywords)

            # Count matches
            matches = sum(1 for kw in relevant_keywords if kw.lower() in task_lower)
            if matches > 0:
                type_scores[task_type] = matches

        if type_scores:
            # Normalize scores
            max_score = max(type_scores.values())
            normalized_scores = {k: v/max_score for k, v in type_scores.items()}
            best_type = max(normalized_scores, key=normalized_scores.get)
            return best_type, normalized_scores[best_type]

        return TaskType.GENERAL, 0.5

    def compute_expert_scores(
        self,
        task: str,
        task_type: TaskType,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Compute relevance scores for all experts based on task and context.

        Implements a gating mechanism similar to MoE:
        - Base score from keyword matching
        - Affinity score from historical performance
        - Load balancing penalty
        - Task-type compatibility
        """
        task_lower = task.lower()
        scores = {}

        for expert_name, expert in self.experts.items():
            # 1. Task type compatibility (binary: 1.0 if compatible, 0.0 if not)
            type_compatibility = 1.0 if task_type in expert.task_types else 0.3

            # 2. Keyword relevance
            keyword_score = sum(
                1.0 for kw in expert.specialization_keywords
                if kw.lower() in task_lower
            )
            keyword_score = min(keyword_score / 3.0, 1.0)  # Normalize to [0, 1]

            # 3. Historical affinity (learned from past routing success)
            affinity_key = (expert_name, task_type)
            affinity_score = self.expert_task_affinity.get(affinity_key, 0.5)

            # 4. Expert's success rate
            success_score = expert.success_rate

            # 5. Load balancing penalty (inverse of current load)
            load_penalty = 1.0 / (1.0 + expert.current_load)

            # Combine scores (gating function)
            gate_score = (
                type_compatibility * 0.3 +
                keyword_score * 0.3 +
                affinity_score * 0.2 +
                success_score * 0.1 +
                load_penalty * 0.1
            ) * expert.base_score

            scores[expert_name] = gate_score

        return scores

    def select_experts(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float]]:
        """
        Select the top-k most relevant experts for the given task.

        Returns list of (expert_name, score) tuples sorted by score.
        """
        # Classify task
        task_type, confidence = self.classify_task(task)

        # Compute scores for all experts
        scores = self.compute_expert_scores(task, task_type, context)

        # Filter by threshold and get top-k
        filtered_scores = {
            k: v for k, v in scores.items()
            if v >= self.min_score_threshold
        }

        top_experts = sorted(
            filtered_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.top_k]

        # Record routing decision
        decision = RoutingDecision(
            task=task[:100],  # Truncate for storage
            selected_experts=[e[0] for e in top_experts],
            expert_scores={e[0]: e[1] for e in top_experts},
            task_type=task_type
        )
        self.routing_history.append(decision)

        return top_experts

    def update_affinity(
        self,
        expert_name: str,
        task_type: TaskType,
        success: bool,
        response_time: float
    ):
        """
        Update expert-task affinity based on routing outcome.

        This implements the learning aspect of the MoE routing.
        """
        affinity_key = (expert_name, task_type)

        # Update success rate
        if expert_name in self.experts:
            expert = self.experts[expert_name]
            expert.usage_count += 1

            # Exponential moving average for success rate
            alpha = 0.1
            new_success = 1.0 if success else 0.0
            expert.success_rate = (1 - alpha) * expert.success_rate + alpha * new_success

            # Update response time
            expert.avg_response_time = (
                (1 - alpha) * expert.avg_response_time + alpha * response_time
            )

            # Update affinity score
            current_affinity = self.expert_task_affinity.get(affinity_key, 0.5)
            if success:
                # Increase affinity for successful routing
                self.expert_task_affinity[affinity_key] = min(1.0, current_affinity + 0.05)
            else:
                # Decrease affinity for failed routing
                self.expert_task_affinity[affinity_key] = max(0.1, current_affinity - 0.1)

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics about routing decisions."""
        if not self.routing_history:
            return {"total_routings": 0}

        expert_usage = defaultdict(int)
        task_type_counts = defaultdict(int)

        for decision in self.routing_history:
            for expert_name in decision.selected_experts:
                expert_usage[expert_name] += 1
            task_type_counts[decision.task_type] += 1

        return {
            "total_routings": len(self.routing_history),
            "expert_usage": dict(expert_usage),
            "task_type_distribution": {k.name: v for k, v in task_type_counts.items()},
            "avg_experts_per_task": np.mean([len(d.selected_experts) for d in self.routing_history]),
            "top_experts": sorted(expert_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    def explain_routing(self, task: str) -> str:
        """
        Provide a human-readable explanation of the routing decision.
        """
        task_type, confidence = self.classify_task(task)
        experts = self.select_experts(task)

        explanation = f"Task Classification: {task_type.value} (confidence: {confidence:.2f})\n\n"
        explanation += "Selected Experts:\n"

        for i, (expert_name, score) in enumerate(experts, 1):
            expert = self.experts[expert_name]
            explanation += f"  {i}. {expert_name} (score: {score:.3f})\n"
            explanation += f"     - Specializes in: {[tt.value for tt in expert.task_types]}\n"
            explanation += f"     - Success rate: {expert.success_rate:.2%}\n"
            explanation += f"     - Usage count: {expert.usage_count}\n"

        return explanation


class ConditionalComputationEngine:
    """
    Orchestrates conditional computation using MoE routing.

    This engine routes tasks to appropriate experts and manages execution,
    implementing the key MoE principle of conditional computation.
    """

    def __init__(self, router: Optional[MoECapabilityRouter] = None,
                 top_k: int = 3, min_score_threshold: float = 0.1):
        """
        Initialize the conditional computation engine.

        Parameters
        ----------
        router : MoECapabilityRouter, optional
            Custom router instance. If None, creates a new one.
        top_k : int, optional
            Maximum number of experts to activate per task.
            Only used if router is None.
        min_score_threshold : float, optional
            Minimum relevance score for expert selection.
            Only used if router is None.
        """
        if router is None:
            self.router = MoECapabilityRouter(top_k=top_k,
                                              min_score_threshold=min_score_threshold)
        else:
            self.router = router
        self.expert_instances: Dict[str, Any] = {}

    def route_and_execute(
        self,
        task: str,
        task_func_map: Dict[str, Callable],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route task to relevant experts and execute.

        Parameters
        ----------
        task : str
            Description of the task to route
        task_func_map : dict
            Mapping from expert names to callable functions
        context : dict, optional
            Additional context for routing

        Returns
        -------
        dict
            Results from executed experts
        """
        # Get routing decision
        selected_experts = self.router.select_experts(task, context)

        # Execute only selected experts (conditional computation!)
        results = {}
        execution_times = {}
