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
Recursive Improver for STAR-Learn

Implements metacognitive self-improvement through:
1. Performance monitoring and plateau detection
2. Strategy switching when diminishing returns
3. Self-modification within safety bounds
4. Architectural evolution
5. Capability enhancement

This enables the system to improve its own learning process
autonomously, creating a recursive self-improvement loop.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta
import time


class ImprovementStrategy(Enum):
    """Strategies for recursive self-improvement"""
    INCREASE_COMPLEXITY = "increase_complexity"
    SWITCH_DOMAIN = "switch_domain"
    ADAPTIVE_SAMPLING = "adaptive_sampling"
    ENSEMBLE_EXPANSION = "ensemble_expansion"
    CAPABILITY_ENHANCEMENT = "capability_enhancement"
    PARAMETER_TUNING = "parameter_tuning"
    ARCHITECTURE_MODIFICATION = "architecture_modification"
    MEMORY_OPTIMIZATION = "memory_optimization"
    CURRICULUM_REFINEMENT = "curriculum_refinement"
    META_LEARNING = "meta_learning"


class MetacognitiveState(Enum):
    """States of metacognitive monitoring"""
    LEARNING = "learning"  # Making good progress
    PLATEAUED = "plateaued"  # Stagnating, needs intervention
    RECOVERING = "recovering"  # Recovering from plateau
    DECLINING = "declining"  # Performance dropping
    PEAK = "peak"  # At maximum performance


@dataclass
class ImprovementResult:
    """Result of an improvement action"""
    strategy: ImprovementStrategy
    success: bool
    confidence: float

    # Changes made
    new_capabilities: List[str] = field(default_factory=list)
    improved_capabilities: List[str] = field(default_factory=list)
    parameter_changes: Dict[str, Any] = field(default_factory=dict)

    # Impact
    expected_improvement: float = 0.0
    measured_improvement: float = 0.0

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    reasoning: str = ""


@dataclass
class MetacognitiveMetrics:
    """Metrics for metacognitive monitoring"""
    # Performance metrics
    recent_rewards: List[float] = field(default_factory=list)
    long_term_rewards: List[float] = field(default_factory=list)
    reward_trend: float = 0.0  # Positive = improving, Negative = declining

    # Learning metrics
    learning_rate: float = 0.0
    convergence_rate: float = 0.0
    stability_score: float = 0.0

    # Diversity metrics
    domain_diversity: float = 0.0
    strategy_diversity: float = 0.0
    novelty_rate: float = 0.0

    # Efficiency metrics
    computation_efficiency: float = 0.0
    reward_per_computation: float = 0.0

    # State
    current_state: MetacognitiveState = MetacognitiveState.LEARNING
    plateau_duration: float = 0.0  # In iterations
    last_state_change: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ImproverConfig:
    """Configuration for the recursive improver"""
    # Monitoring parameters
    monitoring_window: int = 100  # Iterations to monitor
    trend_window: int = 20  # Window for trend calculation
    plateau_threshold: float = 0.01  # Improvement below this = plateau
    decline_threshold: float = -0.05  # Trend below this = declining

    # Improvement parameters
    enable_self_modification: bool = True
    modification_confidence_threshold: float = 0.7
    max_modifications_per_session: int = 3

    # Safety bounds
    max_parameter_change: float = 0.2  # Max 20% change per modification
    min_capability_addition_interval: int = 50  # Min iterations between new capabilities

    # Strategy selection
    strategy_selection_method: str = "ucb"  # "ucb" or "epsilon_greedy"
    exploration_rate: float = 0.2

    # Performance targets
    target_learning_rate: float = 0.01  # Target improvement per iteration
    min_reward_threshold: float = 0.3  # Minimum acceptable reward

    # Recovery parameters
    recovery_strategies: List[str] = field(default_factory=lambda: [
        "switch_domain", "increase_complexity", "adaptive_sampling"
    ])

    # Persistence
    persistence_interval: int = 200
    persistence_path: str = "recursive_improver_state.json"


class RecursiveImprover:
    """
    Recursive Improver for metacognitive self-improvement.

    Monitors performance, detects plateaus, and triggers
    appropriate improvement strategies.
    """

    def __init__(
        self,
        config: Optional[ImproverConfig] = None,
        memory=None,
        reward_engine=None
    ):
        """
        Initialize the recursive improver.

        Args:
            config: Improver configuration
            memory: Stigmergic memory for learning from history
            reward_engine: Self-rewarding engine for reward prediction
        """
        self.config = config or ImproverConfig()
        self.memory = memory
        self.reward_engine = reward_engine

        # Metacognitive state
        self.metrics = MetacognitiveMetrics()
        self.improvement_history: List[ImprovementResult] = []

        # Strategy performance tracking
        self.strategy_performance: Dict[str, float] = {}
        self.strategy_usage_count: Dict[str, int] = {}

        # Safety tracking
        self.last_capability_addition = 0
        self.modifications_this_session = 0

        # Timing
        self.start_time = time.time()
        self.last_improvement_time = time.time()

    def monitor_performance(
        self,
        recent_results: List[Any]
    ) -> MetacognitiveMetrics:
        """
        Monitor performance and update metacognitive metrics.

        Args:
            recent_results: Recent iteration results

        Returns:
            Updated metacognitive metrics
        """
        if not recent_results:
            return self.metrics

        # Extract rewards
        rewards = [r.total_reward for r in recent_results]

        # Update reward history
        self.metrics.recent_rewards = rewards[-self.config.monitoring_window:]
        self.metrics.long_term_rewards.extend(rewards)

        # Limit long-term history
        if len(self.metrics.long_term_rewards) > 1000:
            self.metrics.long_term_rewards = self.metrics.long_term_rewards[-1000:]

        # Calculate trend
        if len(rewards) >= self.config.trend_window:
            recent_avg = np.mean(rewards[-self.config.trend_window:])
            older_avg = np.mean(rewards[-2*self.config.trend_window:-self.config.trend_window])
            self.metrics.reward_trend = (recent_avg - older_avg) / max(older_avg, 1e-6)

        # Calculate learning rate
        self.metrics.learning_rate = self._calculate_learning_rate()

        # Calculate convergence rate
        self.metrics.convergence_rate = self._calculate_convergence_rate()

        # Calculate stability
        self.metrics.stability_score = self._calculate_stability()

        # Calculate diversity metrics
        self.metrics.domain_diversity = self._calculate_domain_diversity(recent_results)
        self.metrics.strategy_diversity = self._calculate_strategy_diversity(recent_results)
        self.metrics.novelty_rate = self._calculate_novelty_rate(recent_results)

        # Calculate efficiency
        self.metrics.computation_efficiency = self._calculate_computation_efficiency(recent_results)
        self.metrics.reward_per_computation = self._calculate_reward_per_computation(recent_results)

        # Update state
        self._update_metacognitive_state()

        return self.metrics

    def _calculate_learning_rate(self) -> float:
        """Calculate current learning rate."""
        if len(self.metrics.recent_rewards) < 2:
            return 0.0

        # Slope of reward over recent iterations
        rewards = self.metrics.recent_rewards
        x = np.arange(len(rewards))
        slope, _ = np.polyfit(x, rewards, 1)

        return slope

    def _calculate_convergence_rate(self) -> float:
        """Calculate convergence rate (how quickly variance decreases)."""
        if len(self.metrics.recent_rewards) < 10:
            return 0.0

        rewards = self.metrics.recent_rewards
        recent_var = np.var(rewards[-10:])
        older_var = np.var(rewards[-20:-10]) if len(rewards) >= 20 else recent_var

        if older_var > 0:
            return 1.0 - (recent_var / older_var)
        return 0.0

    def _calculate_stability(self) -> float:
        """Calculate stability score (inverse of variance)."""
        if len(self.metrics.recent_rewards) < 5:
            return 0.5

        rewards = self.metrics.recent_rewards
        var = np.var(rewards)
        mean = np.mean(rewards)

        if mean > 0:
            # Coefficient of variation
            cv = np.sqrt(var) / mean
            return 1.0 / (1.0 + cv)
        return 0.5

    def _calculate_domain_diversity(self, results: List[Any]) -> float:
        """Calculate domain diversity."""
        if not results:
            return 0.0

        domains = [r.discovery_type for r in results]
        unique_domains = set(domains)

        return len(unique_domains) / len(domains)

    def _calculate_strategy_diversity(self, results: List[Any]) -> float:
        """Calculate strategy (capability) diversity."""
        if not results:
            return 0.0

        all_capabilities = set()
        for r in results:
            all_capabilities.update(r.capabilities_improved or [])

        return min(len(all_capabilities) / 20, 1.0)  # Normalize to ~20 capabilities

    def _calculate_novelty_rate(self, results: List[Any]) -> float:
        """Calculate rate of novel discoveries."""
        if not results:
            return 0.0

        novel_count = sum(1 for r in results if r.novelty_score > 0.5)
        return novel_count / len(results)

    def _calculate_computation_efficiency(self, results: List[Any]) -> float:
        """Calculate computation efficiency."""
        if not results:
            return 0.5

        # Efficiency = reward / time (inverse of time per reward)
        times = [r.total_time for r in results if r.total_time > 0]

        if not times:
            return 0.5

        avg_time = np.mean(times)
        # Normalize: 1 second = 1.0 efficiency (baseline)
        return min(1.0 / avg_time, 1.0)

    def _calculate_reward_per_computation(self, results: List[Any]) -> float:
        """Calculate reward per unit computation."""
        if not results:
            return 0.0

        total_reward = sum(r.total_reward for r in results)
        total_time = sum(r.total_time for r in results)

        if total_time > 0:
            return total_reward / total_time
        return 0.0

    def _update_metacognitive_state(self):
        """Update metacognitive state based on metrics."""
        old_state = self.metrics.current_state

        # Determine new state
        if self.metrics.reward_trend < self.config.decline_threshold:
            new_state = MetacognitiveState.DECLINING
        elif abs(self.metrics.reward_trend) < self.config.plateau_threshold:
            # Check if plateaued for a while
            if self.metrics.plateau_duration > 20:
                new_state = MetacognitiveState.PLATEAUED
            else:
                new_state = MetacognitiveState.PLATEAUED
                self.metrics.plateau_duration += 1
        elif self.metrics.learning_rate > self.config.target_learning_rate * 2:
            new_state = MetacognitiveState.PEAK
        elif self.metrics.reward_trend > 0:
            new_state = MetacognitiveState.LEARNING
            self.metrics.plateau_duration = 0
        else:
            new_state = MetacognitiveState.LEARNING

        # Check for recovery
        if old_state in [MetacognitiveState.PLATEAUED, MetacognitiveState.DECLINING]:
            if new_state == MetacognitiveState.LEARNING:
                new_state = MetacognitiveState.RECOVERING

        # Update state if changed
        if new_state != old_state:
            self.metrics.current_state = new_state
            self.metrics.last_state_change = datetime.now().isoformat()

    def suggest_improvement(
        self,
        problem: Dict,
        solution: Dict,
        reward
    ) -> Optional[ImprovementResult]:
        """
        Suggest an improvement based on current state.

        Args:
            problem: Current problem
            solution: Current solution
            reward: Reward received

        Returns:
            ImprovementResult with suggestion, or None if no improvement needed
        """
        # Only suggest if not already in peak/learning state
        if self.metrics.current_state in [MetacognitiveState.LEARNING, MetacognitiveState.PEAK]:
            return None

        # Select strategy based on state
        strategy = self._select_strategy()

        if not strategy:
            return None

        # Generate improvement result
        result = self._generate_improvement(strategy, problem, solution, reward)

        # Track strategy performance
        self._track_strategy(result)

        return result

    def _select_strategy(self) -> Optional[ImprovementStrategy]:
        """Select an improvement strategy."""
        state = self.metrics.current_state

        # State-specific strategies
        if state == MetacognitiveState.PLATEAUED:
            candidates = [
                ImprovementStrategy.INCREASE_COMPLEXITY,
                ImprovementStrategy.SWITCH_DOMAIN,
                ImprovementStrategy.ADAPTIVE_SAMPLING,
                ImprovementStrategy.CURRICULUM_REFINEMENT
            ]
        elif state == MetacognitiveState.DECLINING:
            candidates = [
                ImprovementStrategy.SWITCH_DOMAIN,
                ImprovementStrategy.PARAMETER_TUNING,
                ImprovementStrategy.CAPABILITY_ENHANCEMENT
            ]
        elif state == MetacognitiveState.RECOVERING:
            candidates = [
                ImprovementStrategy.ADAPTIVE_SAMPLING,
                ImprovementStrategy.META_LEARNING
            ]
        else:
            return None

        # Select using UCB (Upper Confidence Bound)
        if self.config.strategy_selection_method == "ucb":
            return self._ucb_select(candidates)
        else:
            return self._epsilon_greedy_select(candidates)

    def _ucb_select(
        self,
        candidates: List[ImprovementStrategy]
    ) -> Optional[ImprovementStrategy]:
        """Select strategy using UCB algorithm."""
        if not candidates:
            return None

        best_strategy = None
        best_value = -float('inf')

        total_usage = sum(
            self.strategy_usage_count.get(s.value, 0)
            for s in candidates
        ) + 1

        for strategy in candidates:
            strategy_name = strategy.value

            # Average performance
            avg_perf = self.strategy_performance.get(strategy_name, 0.5)

            # Exploration bonus
            usage = self.strategy_usage_count.get(strategy_name, 0)
            exploration_bonus = np.sqrt(2 * np.log(total_usage) / (usage + 1))

            # UCB value
            ucb_value = avg_perf + exploration_bonus

            if ucb_value > best_value:
                best_value = ucb_value
                best_strategy = strategy

        return best_strategy

    def _epsilon_greedy_select(
        self,
        candidates: List[ImprovementStrategy]
    ) -> Optional[ImprovementStrategy]:
        """Select strategy using epsilon-greedy."""
        if not candidates:
            return None

        if np.random.random() < self.config.exploration_rate:
            # Explore: random strategy
            return np.random.choice(candidates)
        else:
            # Exploit: best performing strategy
            best_strategy = None
            best_perf = -float('inf')

            for strategy in candidates:
                perf = self.strategy_performance.get(strategy.value, 0.5)
                if perf > best_perf:
                    best_perf = perf
                    best_strategy = strategy

            return best_strategy

    def _generate_improvement(
        self,
        strategy: ImprovementStrategy,
        problem: Dict,
        solution: Dict,
        reward
    ) -> ImprovementResult:
        """Generate specific improvement for a strategy."""
        result = ImprovementResult(
            strategy=strategy,
            success=False,
            confidence=0.5,
            reasoning=f"Applied {strategy.value} strategy"
        )

        if strategy == ImprovementStrategy.INCREASE_COMPLEXITY:
            result = self._improve_increase_complexity(problem, solution)
        elif strategy == ImprovementStrategy.SWITCH_DOMAIN:
            result = self._improve_switch_domain(problem, solution)
        elif strategy == ImprovementStrategy.ADAPTIVE_SAMPLING:
            result = self._improve_adaptive_sampling(problem, solution)
        elif strategy == ImprovementStrategy.CAPABILITY_ENHANCEMENT:
            result = self._improve_capability_enhancement(problem, solution)
        elif strategy == ImprovementStrategy.PARAMETER_TUNING:
            result = self._improve_parameter_tuning(problem, solution)
        elif strategy == ImprovementStrategy.CURRICULUM_REFINEMENT:
            result = self._improve_curriculum_refinement(problem, solution)

        result.strategy = strategy
        return result

    def _improve_increase_complexity(
        self,
        problem: Dict,
        solution: Dict
    ) -> ImprovementResult:
        """Generate improvement: increase problem complexity."""
        current_difficulty = problem.get('difficulty', 0.5)
        new_difficulty = min(current_difficulty + 0.1, 0.95)

        return ImprovementResult(
            strategy=ImprovementStrategy.INCREASE_COMPLEXITY,
            success=True,
            confidence=0.7,
            parameter_changes={
                'difficulty': new_difficulty,
                'reasoning_depth': 'increase'
            },
            expected_improvement=0.05,
            reasoning="Increase problem complexity to challenge current capabilities"
        )

    def _improve_switch_domain(
        self,
        problem: Dict,
        solution: Dict
    ) -> ImprovementResult:
        """Generate improvement: switch to different domain."""
        current_domain = problem.get('domain', 'unknown')

        # Get alternative domains
        alternative_domains = ['astrophysics', 'causality', 'mathematics', 'physics']
        alternative_domains = [d for d in alternative_domains if d != current_domain]

        if alternative_domains:
            new_domain = np.random.choice(alternative_domains)

            return ImprovementResult(
                strategy=ImprovementStrategy.SWITCH_DOMAIN,
                success=True,
                confidence=0.6,
                parameter_changes={
                    'target_domain': new_domain,
                    'switch_reason': 'plateau_recovery'
                },
                expected_improvement=0.1,
                reasoning=f"Switch from {current_domain} to {new_domain} for fresh challenges"
            )

        return ImprovementResult(
            strategy=ImprovementStrategy.SWITCH_DOMAIN,
            success=False,
            confidence=0.0,
            reasoning="No alternative domains available"
        )

    def _improve_adaptive_sampling(
        self,
        problem: Dict,
        solution: Dict
    ) -> ImprovementResult:
        """Generate improvement: adaptive sampling strategy."""
        return ImprovementResult(
            strategy=ImprovementStrategy.ADAPTIVE_SAMPLING,
            success=True,
            confidence=0.6,
            parameter_changes={
                'sampling_strategy': 'adaptive',
                'exploration_rate': 0.3,
                'exploitation_rate': 0.7
            },
            expected_improvement=0.03,
            reasoning="Switch to adaptive sampling to balance exploration and exploitation"
        )

    def _improve_capability_enhancement(
        self,
        problem: Dict,
        solution: Dict
    ) -> ImprovementResult:
        """Generate improvement: enhance existing capabilities."""
        current_caps = solution.get('capabilities_used', [])

        # Suggest strengthening weak capabilities
        improvements = []
        for cap in current_caps:
            if np.random.random() < 0.3:  # 30% chance to suggest improvement
                improvements.append(f"enhance_{cap}")

        if improvements:
            return ImprovementResult(
                strategy=ImprovementStrategy.CAPABILITY_ENHANCEMENT,
                success=True,
                confidence=0.5,
                improved_capabilities=improvements,
                expected_improvement=0.08,
                reasoning=f"Enhance capabilities: {', '.join(improvements[:3])}"
            )

        return ImprovementResult(
            strategy=ImprovementStrategy.CAPABILITY_ENHANCEMENT,
            success=False,
            confidence=0.0,
            reasoning="No capabilities to enhance"
        )

    def _improve_parameter_tuning(
        self,
        problem: Dict,
        solution: Dict
    ) -> ImprovementResult:
        """Generate improvement: tune hyperparameters."""
        # Suggest parameter changes within safety bounds
        changes = {}

        # Learning rate adjustment
        if np.random.random() < 0.5:
            current_lr = 0.01
            new_lr = current_lr * (1 + np.random.uniform(-0.1, 0.1))
            changes['learning_rate'] = new_lr

        # Exploration rate adjustment
        if np.random.random() < 0.5:
            new_exploration = np.random.uniform(0.1, 0.4)
            changes['exploration_rate'] = new_exploration

        if changes:
            return ImprovementResult(
                strategy=ImprovementStrategy.PARAMETER_TUNING,
                success=True,
                confidence=0.6,
                parameter_changes=changes,
                expected_improvement=0.04,
                reasoning=f"Fine-tune parameters: {list(changes.keys())}"
            )

        return ImprovementResult(
            strategy=ImprovementStrategy.PARAMETER_TUNING,
            success=False,
            confidence=0.0,
            reasoning="No parameters to tune"
        )

    def _improve_curriculum_refinement(
        self,
        problem: Dict,
        solution: Dict
    ) -> ImprovementResult:
        """Generate improvement: refine curriculum."""
        return ImprovementResult(
            strategy=ImprovementStrategy.CURRICULUM_REFINEMENT,
            success=True,
            confidence=0.5,
            parameter_changes={
                'curriculum_strategy': 'adaptive',
                'difficulty_adjustment': 'dynamic'
            },
            expected_improvement=0.06,
            reasoning="Refine curriculum to better match current skill level"
        )

    def _track_strategy(self, result: ImprovementResult):
        """Track strategy performance."""
        strategy_name = result.strategy.value

        # Update usage count
        self.strategy_usage_count[strategy_name] = \
            self.strategy_usage_count.get(strategy_name, 0) + 1

        # Update performance (will be updated when results come back)
        # For now, use expected improvement as proxy
        current_perf = self.strategy_performance.get(strategy_name, 0.5)
        self.strategy_performance[strategy_name] = \
            0.9 * current_perf + 0.1 * result.expected_improvement

    def apply_improvement(
        self,
        improvement: ImprovementResult
    ) -> bool:
        """
        Apply an improvement to the system.

        Args:
            improvement: Improvement to apply

        Returns:
            Success status
        """
        if not improvement.success:
            return False
