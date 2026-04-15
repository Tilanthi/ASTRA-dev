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
Meta-Learning Layer: Learning to Learn

This module implements meta-learning capabilities - learning how to solve
problems more effectively across tasks.

Key Features:
- Strategy library for problem-solving approaches
- Domain-specific hyperparameter adaptation
- Transfer learning across problem types
- Integration with swarm intelligence for strategy evolution

Why This Matters for AGI:
- Each new problem benefits from past experience
- Automatic adaptation to problem characteristics
- Continual improvement in reasoning efficiency

Date: 2025-12-10
Version: 39.0
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import time
from collections import defaultdict
from pathlib import Path


class StrategyType(Enum):
    """Types of problem-solving strategies"""
    ANALOGY_FIRST = "analogy_first"           # Start by finding analogies
    CONSTRAINT_FIRST = "constraint_first"      # Start by checking constraints
    DECOMPOSITION = "decomposition"            # Break into subproblems
    HYPOTHESIS_DRIVEN = "hypothesis_driven"    # Generate and test hypotheses
    DATA_DRIVEN = "data_driven"                # Let data guide exploration
    EXPLORATORY = "exploratory"                # Broad exploration first
    FOCUSED = "focused"                        # Deep dive into likely solution


class ProblemClass(Enum):
    """Classes of problems"""
    INFERENCE = "inference"
    DISCOVERY = "discovery"
    OPTIMIZATION = "optimization"
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    VERIFICATION = "verification"


@dataclass
class TaskSignature:
    """Signature identifying task characteristics"""
    problem_class: ProblemClass
    domain: str
    n_variables: int
    complexity_estimate: float  # 0-1
    has_constraints: bool
    has_prior_knowledge: bool
    data_availability: str  # 'abundant', 'moderate', 'scarce'

    # Feature vector for matching
    features: Dict[str, float] = field(default_factory=dict)

    def to_vector(self) -> np.ndarray:
        """Convert to feature vector"""
        base_features = [
            list(ProblemClass).index(self.problem_class) / len(ProblemClass),
            hash(self.domain) % 100 / 100,  # Domain hash
            min(self.n_variables / 20, 1.0),
            self.complexity_estimate,
            float(self.has_constraints),
            float(self.has_prior_knowledge),
            {'abundant': 1.0, 'moderate': 0.5, 'scarce': 0.2}.get(self.data_availability, 0.5)
        ]
        return np.array(base_features)

    def to_dict(self) -> Dict:
        return {
            'problem_class': self.problem_class.value,
            'domain': self.domain,
            'n_variables': self.n_variables,
            'complexity_estimate': self.complexity_estimate,
            'has_constraints': self.has_constraints,
            'has_prior_knowledge': self.has_prior_knowledge,
            'data_availability': self.data_availability,
            'features': self.features
        }


@dataclass
class Strategy:
    """A problem-solving strategy"""
    strategy_id: str
    strategy_type: StrategyType
    description: str

    # Strategy parameters
    step_sequence: List[str]
    hyperparameters: Dict[str, Any]
    preconditions: List[str]

    # Performance metrics
    n_applications: int = 0
    success_rate: float = 0.5
    avg_steps_to_solution: float = 10.0
    avg_time: float = 1.0

    # Applicability
    applicable_domains: List[str] = field(default_factory=list)
    applicable_problem_classes: List[ProblemClass] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'strategy_id': self.strategy_id,
            'strategy_type': self.strategy_type.value,
            'description': self.description,
            'step_sequence': self.step_sequence,
            'hyperparameters': self.hyperparameters,
            'preconditions': self.preconditions,
            'n_applications': self.n_applications,
            'success_rate': self.success_rate,
            'avg_steps': self.avg_steps_to_solution,
            'avg_time': self.avg_time,
            'applicable_domains': self.applicable_domains,
            'applicable_problem_classes': [pc.value for pc in self.applicable_problem_classes]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Strategy':
        return cls(
            strategy_id=data['strategy_id'],
            strategy_type=StrategyType(data['strategy_type']),
            description=data['description'],
            step_sequence=data['step_sequence'],
            hyperparameters=data['hyperparameters'],
            preconditions=data.get('preconditions', []),
            n_applications=data.get('n_applications', 0),
            success_rate=data.get('success_rate', 0.5),
            avg_steps_to_solution=data.get('avg_steps', 10.0),
            avg_time=data.get('avg_time', 1.0),
            applicable_domains=data.get('applicable_domains', []),
            applicable_problem_classes=[ProblemClass(pc) for pc in data.get('applicable_problem_classes', [])]
        )


@dataclass
class TaskResult:
    """Result of applying strategy to task"""
    task_signature: TaskSignature
    strategy_id: str
    success: bool
    steps_taken: int
    time_taken: float
    metrics: Dict[str, float]
    lessons: List[str] = field(default_factory=list)


class StrategyLibrary:
    """Library of problem-solving strategies"""

    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self._build_default_strategies()

    def _build_default_strategies(self):
        """Build default strategy library"""

        # Analogy-first strategy
        self.add_strategy(Strategy(
            strategy_id="analogy_first_v1",
            strategy_type=StrategyType.ANALOGY_FIRST,
            description="Start by finding analogous solved problems",
            step_sequence=[
                "retrieve_similar_problems",
                "extract_solution_patterns",
                "adapt_pattern_to_current",
                "verify_solution",
                "refine_if_needed"
            ],
            hyperparameters={
                'similarity_threshold': 0.6,
                'max_analogies': 5,
                'adaptation_iterations': 3
            },
            preconditions=["has_problem_database"],
            applicable_domains=["*"],
            applicable_problem_classes=[ProblemClass.INFERENCE, ProblemClass.DISCOVERY]
        ))

        # Constraint-first strategy
        self.add_strategy(Strategy(
            strategy_id="constraint_first_v1",
            strategy_type=StrategyType.CONSTRAINT_FIRST,
            description="Start by checking and enforcing constraints",
            step_sequence=[
                "collect_constraints",
                "check_consistency",
                "prune_invalid_solutions",
                "explore_valid_region",
                "optimize_within_constraints"
            ],
            hyperparameters={
                'constraint_strictness': 0.9,
                'early_pruning': True,
                'max_violations': 0
            },
            preconditions=["has_constraints"],
            applicable_domains=["*"],
            applicable_problem_classes=[ProblemClass.OPTIMIZATION, ProblemClass.VERIFICATION]
        ))

        # Decomposition strategy
        self.add_strategy(Strategy(
            strategy_id="decomposition_v1",
            strategy_type=StrategyType.DECOMPOSITION,
            description="Break problem into manageable subproblems",
            step_sequence=[
                "analyze_problem_structure",
                "identify_subproblems",
                "solve_subproblems_independently",
                "integrate_solutions",
                "verify_global_solution"
            ],
            hyperparameters={
                'min_subproblem_size': 2,
                'max_subproblems': 5,
                'parallel_solving': True
            },
            preconditions=["problem_decomposable"],
            applicable_domains=["*"],
            applicable_problem_classes=[ProblemClass.INFERENCE, ProblemClass.OPTIMIZATION]
        ))

        # Hypothesis-driven strategy
        self.add_strategy(Strategy(
            strategy_id="hypothesis_driven_v1",
            strategy_type=StrategyType.HYPOTHESIS_DRIVEN,
            description="Generate hypotheses and test systematically",
            step_sequence=[
                "generate_initial_hypotheses",
                "rank_by_plausibility",
                "design_discriminating_test",
                "execute_test",
                "update_beliefs",
                "iterate_until_confident"
            ],
            hyperparameters={
                'n_hypotheses': 10,
                'confidence_threshold': 0.8,
                'max_iterations': 20
            },
            preconditions=["can_generate_hypotheses", "can_test_hypotheses"],
            applicable_domains=["*"],
            applicable_problem_classes=[ProblemClass.DISCOVERY, ProblemClass.INFERENCE]
        ))

        # Data-driven strategy
        self.add_strategy(Strategy(
            strategy_id="data_driven_v1",
            strategy_type=StrategyType.DATA_DRIVEN,
            description="Let data patterns guide the solution",
            step_sequence=[
                "analyze_data_distribution",
                "identify_patterns",
                "build_model",
                "validate_model",
                "extract_insights"
            ],
            hyperparameters={
                'min_samples': 100,
                'model_complexity': 'adaptive',
                'validation_fraction': 0.2
            },
            preconditions=["has_data"],
            applicable_domains=["*"],
            applicable_problem_classes=[ProblemClass.CLASSIFICATION, ProblemClass.INFERENCE]
        ))

        # Exploratory strategy
        self.add_strategy(Strategy(
            strategy_id="exploratory_v1",
            strategy_type=StrategyType.EXPLORATORY,
            description="Broad exploration before commitment",
            step_sequence=[
                "map_solution_space",
                "identify_promising_regions",
                "sample_diverse_solutions",
                "evaluate_samples",
                "focus_on_best_region"
            ],
            hyperparameters={
                'exploration_breadth': 0.8,
                'samples_per_region': 10,
                'diversity_weight': 0.5
            },
            preconditions=[],
            applicable_domains=["*"],
            applicable_problem_classes=[ProblemClass.DISCOVERY, ProblemClass.GENERATION]
        ))

    def add_strategy(self, strategy: Strategy):
        """Add strategy to library"""
        self.strategies[strategy.strategy_id] = strategy

    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Get strategy by ID"""
        return self.strategies.get(strategy_id)

    def get_applicable_strategies(self, signature: TaskSignature) -> List[Strategy]:
        """Get strategies applicable to task signature"""
        applicable = []

        for strategy in self.strategies.values():
            # Check problem class
            if strategy.applicable_problem_classes:
                if signature.problem_class not in strategy.applicable_problem_classes:
                    continue

            # Check domain
            if strategy.applicable_domains and "*" not in strategy.applicable_domains:
                if signature.domain not in strategy.applicable_domains:
                    continue

            # Check preconditions
            preconditions_met = True
            for precond in strategy.preconditions:
                if precond == "has_constraints" and not signature.has_constraints:
                    preconditions_met = False
                elif precond == "has_data" and signature.data_availability == "scarce":
                    preconditions_met = False
                elif precond == "has_problem_database" and not signature.has_prior_knowledge:
                    preconditions_met = False

            if preconditions_met:
                applicable.append(strategy)

        return applicable

    def to_dict(self) -> Dict:
        return {sid: s.to_dict() for sid, s in self.strategies.items()}


class HyperparameterAdapter:
    """Adapt hyperparameters based on task characteristics"""

    def __init__(self):
        # Learned parameter adjustments
        self.adjustments: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Base parameters by strategy type
        self.base_params = {
            StrategyType.ANALOGY_FIRST: {
                'similarity_threshold': 0.6,
                'max_analogies': 5,
                'adaptation_iterations': 3
            },
            StrategyType.CONSTRAINT_FIRST: {
                'constraint_strictness': 0.9,
                'max_violations': 0
            },
            StrategyType.HYPOTHESIS_DRIVEN: {
                'n_hypotheses': 10,
                'confidence_threshold': 0.8,
                'max_iterations': 20
            }
        }

    def adapt(self, strategy: Strategy, signature: TaskSignature) -> Dict[str, Any]:
        """
        Adapt strategy hyperparameters to task signature.

        Returns adapted hyperparameters.
        """
        adapted = strategy.hyperparameters.copy()

        # Domain-specific adjustments
        domain_key = f"{signature.domain}_{strategy.strategy_type.value}"
        if domain_key in self.adjustments:
            for param, adjustment in self.adjustments[domain_key].items():
                if param in adapted:
                    adapted[param] = self._apply_adjustment(
                        adapted[param], adjustment
                    )

        # Complexity-based adjustments
        if signature.complexity_estimate > 0.7:
            # High complexity -> more exploration, more iterations
            if 'max_iterations' in adapted:
                adapted['max_iterations'] = int(adapted['max_iterations'] * 1.5)
            if 'n_hypotheses' in adapted:
                adapted['n_hypotheses'] = int(adapted['n_hypotheses'] * 1.3)

        # Data availability adjustments
        if signature.data_availability == 'scarce':
            if 'min_samples' in adapted:
                adapted['min_samples'] = max(10, adapted['min_samples'] // 2)
            if 'validation_fraction' in adapted:
                adapted['validation_fraction'] = 0.1  # Less validation data

        return adapted

    def learn_adjustment(self, strategy: Strategy, signature: TaskSignature,
                        result: TaskResult):
        """Learn parameter adjustments from task result"""
        domain_key = f"{signature.domain}_{strategy.strategy_type.value}"

        # Simple learning rule: adjust toward successful parameters
        learning_rate = 0.1

        for param, value in strategy.hyperparameters.items():
            if param not in self.adjustments[domain_key]:
                self.adjustments[domain_key][param] = 0.0

            if result.success:
                # Reinforce current adjustment
                pass
            else:
                # Try different direction
                current = self.adjustments[domain_key][param]
                self.adjustments[domain_key][param] = current + learning_rate * np.random.choice([-1, 1])

    def _apply_adjustment(self, base_value: Any, adjustment: float) -> Any:
        """Apply adjustment to parameter value"""
        if isinstance(base_value, (int, float)):
            return base_value * (1 + 0.1 * adjustment)
        elif isinstance(base_value, bool):
            return base_value if adjustment > 0 else not base_value
        else:
            return base_value


class StrategySelector:
    """Select best strategy for a task"""

    def __init__(self, library: StrategyLibrary):
        self.library = library

        # Performance history
        self.history: List[Tuple[TaskSignature, str, bool]] = []

        # Learned weights for strategy selection
        self.strategy_weights: Dict[str, float] = defaultdict(lambda: 1.0)

    def select(self, signature: TaskSignature, k: int = 3) -> List[Tuple[Strategy, float]]:
        """
        Select top-k strategies for task.

        Returns list of (strategy, confidence) tuples.
        """
        applicable = self.library.get_applicable_strategies(signature)

        if not applicable:
            # Return default exploratory strategy
            default = self.library.get_strategy("exploratory_v1")
            return [(default, 0.3)] if default else []

        # Score each strategy
        scored = []
        for strategy in applicable:
            score = self._score_strategy(strategy, signature)
            scored.append((strategy, score))

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)

        # Normalize to confidences
        total = sum(s for _, s in scored)
        if total > 0:
            scored = [(s, conf / total) for s, conf in scored]

        return scored[:k]

    def _score_strategy(self, strategy: Strategy, signature: TaskSignature) -> float:
        """Score strategy for task"""
        score = 1.0

        # Historical success rate
        score *= strategy.success_rate

        # Learned weight
        score *= self.strategy_weights[strategy.strategy_id]

        # Problem class match bonus
        if signature.problem_class in strategy.applicable_problem_classes:
            score *= 1.2

        # Data availability match
        if strategy.strategy_type == StrategyType.DATA_DRIVEN:
            if signature.data_availability == 'abundant':
                score *= 1.3
            elif signature.data_availability == 'scarce':
                score *= 0.5

        # Constraint match
        if strategy.strategy_type == StrategyType.CONSTRAINT_FIRST:
            if signature.has_constraints:
                score *= 1.5
            else:
                score *= 0.3

        return score

    def update_from_result(self, signature: TaskSignature, strategy_id: str,
                           success: bool):
        """Update selector based on result"""
        self.history.append((signature, strategy_id, success))

        # Update strategy weight
        learning_rate = 0.05
        if success:
            self.strategy_weights[strategy_id] *= (1 + learning_rate)
        else:
            self.strategy_weights[strategy_id] *= (1 - learning_rate)

        # Normalize weights
        max_weight = max(self.strategy_weights.values())
        if max_weight > 5.0:
            for sid in self.strategy_weights:
                self.strategy_weights[sid] /= max_weight


class MetaLearner:
    """
    Main Meta-Learning system.

    Learns how to solve problems more effectively across tasks.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Args:
            storage_path: Path for persistent storage
        """
        self.storage_path = Path(storage_path) if storage_path else None

        # Components
        self.strategy_library = StrategyLibrary()
        self.strategy_selector = StrategySelector(self.strategy_library)
        self.hyperparameter_adapter = HyperparameterAdapter()

        # Task history
        self.task_history: List[TaskResult] = []

        # Domain-specific statistics
        self.domain_stats: Dict[str, Dict] = defaultdict(lambda: {
            'n_tasks': 0,
            'success_rate': 0.5,
            'best_strategies': [],
            'avg_complexity': 0.5
        })

        # Load from storage
        if self.storage_path and self.storage_path.exists():
            self.load()

    def suggest_strategy(self, signature: TaskSignature) -> Tuple[Strategy, Dict[str, Any], float]:
        """
        Suggest best strategy and parameters for task.

        Args:
            signature: Task signature

        Returns:
            Tuple of (strategy, adapted_hyperparameters, confidence)
        """
        # Select strategies
        candidates = self.strategy_selector.select(signature, k=3)

        if not candidates:
            raise ValueError("No applicable strategies found")

        best_strategy, confidence = candidates[0]

        # Adapt hyperparameters
        adapted_params = self.hyperparameter_adapter.adapt(best_strategy, signature)

        return best_strategy, adapted_params, confidence

    def learn_from_task(self, signature: TaskSignature, strategy: Strategy,
                        result: TaskResult):
        """
        Learn from completed task.

        Updates strategy selection, hyperparameters, and statistics.
        """
        # Update strategy statistics
        strategy.n_applications += 1
        n = strategy.n_applications
        strategy.success_rate = ((n - 1) * strategy.success_rate + float(result.success)) / n
        strategy.avg_steps_to_solution = ((n - 1) * strategy.avg_steps_to_solution + result.steps_taken) / n
        strategy.avg_time = ((n - 1) * strategy.avg_time + result.time_taken) / n

        # Update strategy selector
        self.strategy_selector.update_from_result(signature, strategy.strategy_id, result.success)

        # Update hyperparameter adapter
        self.hyperparameter_adapter.learn_adjustment(strategy, signature, result)

        # Update domain statistics
        domain_stat = self.domain_stats[signature.domain]
        domain_stat['n_tasks'] += 1
        n = domain_stat['n_tasks']
        domain_stat['success_rate'] = ((n - 1) * domain_stat['success_rate'] + float(result.success)) / n
        domain_stat['avg_complexity'] = ((n - 1) * domain_stat['avg_complexity'] + signature.complexity_estimate) / n

        if result.success:
            if strategy.strategy_id not in domain_stat['best_strategies']:
                domain_stat['best_strategies'].append(strategy.strategy_id)

        # Store result
        self.task_history.append(result)

        # Auto-save
        if self.storage_path:
            self.save()

    def create_new_strategy(self, base_strategy: Strategy, modifications: Dict) -> Strategy:
        """
        Create new strategy variant from base strategy.

        Useful for strategy evolution.
        """
        new_id = f"{base_strategy.strategy_id}_variant_{len(self.strategy_library.strategies)}"

        new_strategy = Strategy(
            strategy_id=new_id,
            strategy_type=base_strategy.strategy_type,
            description=f"Variant of {base_strategy.description}",
            step_sequence=modifications.get('step_sequence', base_strategy.step_sequence.copy()),
            hyperparameters={**base_strategy.hyperparameters, **modifications.get('hyperparameters', {})},
            preconditions=modifications.get('preconditions', base_strategy.preconditions.copy()),
            applicable_domains=modifications.get('domains', base_strategy.applicable_domains.copy()),
            applicable_problem_classes=modifications.get('problem_classes', base_strategy.applicable_problem_classes.copy())
        )

        self.strategy_library.add_strategy(new_strategy)
        return new_strategy

    def get_domain_insights(self, domain: str) -> Dict[str, Any]:
        """Get insights for a specific domain"""
        if domain not in self.domain_stats:
            return {'status': 'no_data', 'domain': domain}

        stats = self.domain_stats[domain]

        # Get best strategies with details
        best_strategies = []
        for sid in stats['best_strategies'][:5]:
            strategy = self.strategy_library.get_strategy(sid)
            if strategy:
                best_strategies.append({
                    'id': sid,
                    'type': strategy.strategy_type.value,
                    'success_rate': strategy.success_rate
                })

        return {
            'domain': domain,
            'n_tasks': stats['n_tasks'],
            'success_rate': stats['success_rate'],
            'avg_complexity': stats['avg_complexity'],
            'best_strategies': best_strategies,
            'recommendation': self._generate_recommendation(domain, stats)
        }

    def _generate_recommendation(self, domain: str, stats: Dict) -> str:
        """Generate recommendation based on domain statistics"""
        if stats['n_tasks'] < 3:
            return "Insufficient data - continue exploring different strategies"

        if stats['success_rate'] > 0.8:
            return f"Domain {domain} well-handled. Continue with current strategies."
        elif stats['success_rate'] > 0.5:
            return f"Moderate success in {domain}. Consider hypothesis-driven approach for improvement."
        else:
            return f"Challenging domain {domain}. Try exploratory strategies with broader search."

    def adapt_swarm_parameters(self, signature: TaskSignature) -> Dict[str, Any]:
        """
        Adapt swarm intelligence parameters for task.

        Returns recommended swarm configuration.
        """
        base_params = {
            'n_explorers': 4,
            'n_falsifiers': 2,
            'n_analogists': 2,
            'n_evolvers': 1,
            'exploration_weight': 0.5,
            'exploitation_weight': 0.5
        }

        # Adjust based on task characteristics
        if signature.complexity_estimate > 0.7:
            # High complexity -> more exploration
            base_params['n_explorers'] = 6
            base_params['exploration_weight'] = 0.7

        if signature.has_constraints:
            # Constraints -> more falsification
            base_params['n_falsifiers'] = 4

        if signature.has_prior_knowledge:
            # Prior knowledge -> more analogy
            base_params['n_analogists'] = 4

        if signature.data_availability == 'abundant':
            # More data -> more exploitation
            base_params['exploitation_weight'] = 0.6

        # Domain-specific adjustments
        if signature.domain in self.domain_stats:
            stats = self.domain_stats[signature.domain]
            if stats['success_rate'] < 0.5:
                # Struggling domain -> more exploration
                base_params['exploration_weight'] = 0.7
                base_params['n_evolvers'] = 2

        return base_params

    def save(self, filepath: str = None):
        """Save meta-learner state"""
        path = Path(filepath) if filepath else self.storage_path
        if not path:
            return

        path.mkdir(parents=True, exist_ok=True)

        # Save strategies
        with open(path / "strategies.json", 'w') as f:
            json.dump(self.strategy_library.to_dict(), f, indent=2)

        # Save domain stats
        with open(path / "domain_stats.json", 'w') as f:
            json.dump(dict(self.domain_stats), f, indent=2)

        # Save selector weights
        with open(path / "selector_weights.json", 'w') as f:
            json.dump(dict(self.strategy_selector.strategy_weights), f, indent=2)

    def load(self, filepath: str = None):
        """Load meta-learner state"""
        path = Path(filepath) if filepath else self.storage_path
        if not path or not path.exists():
            return

        # Load strategies
        strategies_file = path / "strategies.json"
        if strategies_file.exists():
            with open(strategies_file, 'r') as f:
                data = json.load(f)
                for sid, sdata in data.items():
                    self.strategy_library.strategies[sid] = Strategy.from_dict(sdata)

        # Load domain stats
        stats_file = path / "domain_stats.json"
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                self.domain_stats.update(json.load(f))

        # Load selector weights
        weights_file = path / "selector_weights.json"
        if weights_file.exists():
            with open(weights_file, 'r') as f:
                self.strategy_selector.strategy_weights.update(json.load(f))

    def get_stats(self) -> Dict[str, Any]:
        """Get meta-learner statistics"""
        return {
            'n_strategies': len(self.strategy_library.strategies),
            'n_tasks_completed': len(self.task_history),
            'n_domains': len(self.domain_stats),
            'overall_success_rate': np.mean([r.success for r in self.task_history]) if self.task_history else 0.0,
            'domains': list(self.domain_stats.keys()),
            'strategy_types': [s.strategy_type.value for s in self.strategy_library.strategies.values()]
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'MetaLearner',
    'Strategy',
    'StrategyType',
    'TaskSignature',
    'ProblemClass',
    'TaskResult',
    'StrategyLibrary',
    'StrategySelector',
    'HyperparameterAdapter'
]
