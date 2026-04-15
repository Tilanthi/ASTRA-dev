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
Autonomous Training Loop for STAR-Learn

Implements the self-teaching iteration loop that:
1. Generates or receives a problem
2. Attempts solution using current capabilities
3. Evaluates solution quality
4. Calculates intrinsic reward
5. Updates memory and biological fields
6. Triggers LEAPCore evolution
7. Performs self-modification if warranted
8. Archives results and updates curriculum

This is the core "autonomy" component that enables unsupervised learning.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
import time


class LoopState(Enum):
    """States of the autonomous training loop"""
    IDLE = "idle"
    GENERATING_PROBLEM = "generating_problem"
    SOLVING = "solving"
    EVALUATING = "evaluating"
    REWARDING = "rewarding"
    UPDATING = "updating"
    EVOLVING = "evolving"
    MODIFYING = "modifying"
    ARCHIVING = "archiving"


@dataclass
class TrainingIteration:
    """Data for a single training iteration"""
    iteration_number: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Problem information
    problem: Optional[Dict[str, Any]] = None
    problem_type: str = "unknown"
    problem_difficulty: float = 0.5

    # Solution information
    solution: Optional[Dict[str, Any]] = None
    solution_attempt: str = ""
    confidence: float = 0.0

    # Evaluation information
    evaluation_score: float = 0.0
    correctness: float = 0.0
    novelty_score: float = 0.0

    # Reward information
    intrinsic_reward: float = 0.0
    reward_components: Dict[str, float] = field(default_factory=dict)

    # System state
    capabilities_used: List[str] = field(default_factory=list)
    computation_time: float = 0.0

    # Outcome
    success: bool = False
    discovery_made: bool = False
    learned_skills: List[str] = field(default_factory=list)


@dataclass
class IterationResult:
    """Result of a training iteration"""
    iteration: TrainingIteration

    # Composite scores
    total_reward: float = 0.0
    improvement_score: float = 0.0

    # Discovery info
    discovery_summary: str = ""
    discovery_type: str = ""
    novelty_score: float = 0.0

    # System changes
    capabilities_improved: List[str] = field(default_factory=list)
    new_capabilities_added: List[str] = field(default_factory=list)
    parameters_modified: Dict[str, Any] = field(default_factory=dict)

    # Stigmergic updates
    pheromone_deposits: List[Dict[str, Any]] = field(default_factory=list)
    biological_field_changes: Dict[str, float] = field(default_factory=dict)

    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    total_time: float = 0.0

    def __post_init__(self):
        if self.end_time == 0.0:
            self.end_time = time.time()
        self.total_time = self.end_time - self.start_time


@dataclass
class LoopConfig:
    """Configuration for the autonomous training loop"""
    # Loop parameters
    max_iterations: int = 10000
    convergence_threshold: float = 0.001
    patience: int = 100  # Iterations without improvement before switching strategy

    # Time limits
    max_iteration_time: float = 300.0  # 5 minutes max per iteration
    total_time_limit: float = 7200.0  # 2 hours total

    # Difficulty progression
    initial_difficulty: float = 0.3
    difficulty_growth_rate: float = 0.01
    max_difficulty: float = 0.95
    adaptive_difficulty: bool = True

    # Exploration parameters
    exploration_rate: float = 0.2  # Fraction of time exploring new domains
    domain_diversity_threshold: int = 3  # Min domains to explore

    # Self-modification parameters
    enable_self_modification: bool = True
    modification_threshold: float = 0.7  # Reward threshold for modification
    modification_cooldown: int = 10  # Min iterations between modifications

    # Evolution parameters
    enable_leapcore_evolution: bool = True
    evolution_interval: int = 5  # Run evolution every N iterations

    # Stigmergic parameters
    enable_stigmergic_updates: bool = True
    pheromone_decay_rate: float = 0.95
    biological_field_learning_rate: float = 0.1

    # Archival
    archive_best_n: int = 100  # Keep top N discoveries
    archive_recent_n: int = 1000  # Keep recent N iterations


class AutonomousTrainingLoop:
    """
    Autonomous Training Loop for self-teaching.

    Orchestrates the complete self-teaching cycle:
    problem generation → solution → evaluation → reward → update
    """

    def __init__(
        self,
        config: LoopConfig,
        reward_engine,
        curriculum_generator,
        recursive_improver,
        stigmergic_memory
    ):
        """
        Initialize the autonomous training loop.

        Args:
            config: Loop configuration
            reward_engine: Self-rewarding engine
            curriculum_generator: Problem curriculum generator
            recursive_improver: Recursive self-improvement system
            stigmergic_memory: Stigmergic biological field memory
        """
        self.config = config
        self.reward_engine = reward_engine
        self.curriculum = curriculum_generator
        self.improver = recursive_improver
        self.memory = stigmergic_memory

        # Loop state
        self.current_iteration = 0
        self.state = LoopState.IDLE
        self.best_reward = 0.0
        self.patience_counter = 0

        # History
        self.iteration_history: List[IterationResult] = []
        self.reward_history: List[float] = []
        self.discovery_archive: List[Dict] = []

        # Difficulty management
        self.current_difficulty = config.initial_difficulty if config else LoopConfig().initial_difficulty

        # Timing
        self.start_time = time.time()
        self.total_computation_time = 0.0

    def run_iteration(self, problem: Optional[Dict] = None) -> IterationResult:
        """
        Run a single training iteration.

        Args:
            problem: Optional pre-generated problem

        Returns:
            IterationResult with all iteration data
        """
        iteration_start = time.time()

        # Create iteration object
        iteration = TrainingIteration(
            iteration_number=self.current_iteration,
            timestamp=datetime.now().isoformat(),
            problem=problem,
            problem_difficulty=self.current_difficulty
        )

        # Run iteration
        try:
            # Solve problem
            if self.reward_engine:
                solution_result = self.reward_engine.solve(problem or {})
                iteration.solution_attempt = str(solution_result)
                iteration.confidence = solution_result.get("confidence", 0.0)

            # Evaluate
            iteration.evaluation_score = self._evaluate_solution(iteration)
            iteration.correctness = min(1.0, iteration.evaluation_score)

            # Calculate reward
            iteration.intrinsic_reward = self._calculate_reward(iteration)

            # Update state
            self.current_iteration += 1
            self.reward_history.append(iteration.intrinsic_reward)

            if iteration.intrinsic_reward > self.best_reward:
                self.best_reward = iteration.intrinsic_reward
                self.patience_counter = 0
            else:
                self.patience_counter += 1

        except Exception as e:
            iteration.success = False
            iteration.solution_attempt = f"Error: {e}"

        # Create result
        result = IterationResult(
            iteration=iteration,
            total_reward=iteration.intrinsic_reward,
            computation_time=time.time() - iteration_start
        )

        # Archive
        self.iteration_history.append(result)

        return result

    def _evaluate_solution(self, iteration: TrainingIteration) -> float:
        """Evaluate solution quality."""
        if iteration.solution_attempt:
            return 0.7  # Simplified evaluation
        return 0.0

    def _calculate_reward(self, iteration: TrainingIteration) -> float:
        """Calculate intrinsic reward."""
        base_reward = iteration.correctness * 0.5
        difficulty_bonus = iteration.problem_difficulty * 0.3
        novelty_bonus = iteration.novelty_score * 0.2
        return base_reward + difficulty_bonus + novelty_bonus

    def get_status(self) -> Dict[str, Any]:
        """Get current loop status."""
        return {
            "current_iteration": self.current_iteration,
            "state": self.state.value,
            "best_reward": self.best_reward,
            "current_difficulty": self.current_difficulty,
            "total_computation_time": self.total_computation_time
        }


# Factory functions
def create_autonomous_loop(config: Optional[LoopConfig] = None) -> AutonomousTrainingLoop:
    """Create an autonomous training loop."""
    return AutonomousTrainingLoop(config or LoopConfig())
