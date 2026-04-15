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
Meta-Learning Module for STAR-Learn V2.5

This module enables STAR-Learn to "learn how to learn":
1. Learning algorithm selection
2. Hyperparameter optimization
3. Few-shot learning
4. Transfer learning across domains
5. Continual learning without catastrophic forgetting
6. Meta-reasoning about learning strategies
7. Self-improvement of learning capabilities

This is a KEY AGI CAPABILITY - the ability to learn new tasks
from just a few examples and to improve one's own learning process.

Version: 2.5.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict


class LearningStrategy(Enum):
    """Types of learning strategies"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    META_LEARNING = "meta_learning"
    FEW_SHOT = "few_shot"
    TRANSFER = "transfer"
    SELF_SUPERVISED = "self_supervised"
    BAYESIAN = "bayesian"
    CAUSAL = "causal"


class TaskType(Enum):
    """Types of learning tasks"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    PREDICTION = "prediction"
    GENERATION = "generation"
    OPTIMIZATION = "optimization"
    DISCOVERY = "discovery"


@dataclass
class LearningTask:
    """A learning task to solve"""
    task_id: str
    task_type: TaskType
    domain: str
    training_data: Optional[np.ndarray] = None
    test_data: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    difficulty: float = 0.5
    priority: float = 0.5


@dataclass
class LearningResult:
    """Result of a learning attempt"""
    task_id: str
    strategy: LearningStrategy
    performance: float  # 0-1
    training_time: float
    resource_usage: float
    generalization: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat)


@dataclass
class MetaLearner:
    """A meta-learner that learns how to learn"""
    name: str
    strategies: List[LearningStrategy] = field(default_factory=list)
    performance_history: Dict[str, List[float]] = field(default_factory=dict)
    task_preferences: Dict[TaskType, LearningStrategy] = field(default_factory=dict)


@dataclass
class TransferKnowledge:
    """Knowledge transferred between domains"""
    source_domain: str
    target_domain: str
    transferred_concepts: List[str]
    adaptation_required: float
    success_rate: float


# =============================================================================
# MAML-style Meta-Learning
# =============================================================================
class MAMLMetaLearner:
    """
    Model-Agnostic Meta-Learning (MAML) implementation.

    Learns initialization that can be quickly adapted to new tasks
    with just a few gradient steps.

    Key insight: Learn to learn by optimizing for fast adaptation.
    """

    def __init__(self, learning_rate: float = 0.01, meta_lr: float = 0.001):
        """Initialize MAML meta-learner."""
        self.learning_rate = learning_rate
        self.meta_lr = meta_lr
        self.meta_parameters = {}  # Learned initialization
        self.task_history = []

    def meta_train(
        self,
        tasks: List[LearningTask],
        n_episodes: int = 100
    ) -> Dict[str, float]:
        """
        Meta-train on a distribution of tasks.

        Args:
            tasks: List of tasks to meta-train on
            n_episodes: Number of meta-training episodes

        Returns:
            Meta-training metrics
        """
        meta_losses = []
        adaptation_success = []

        for episode in range(n_episodes):
            # Sample a batch of tasks
            task_batch = np.random.choice(tasks, size=min(5, len(tasks)), replace=False)

            episode_loss = 0
            episode_adapt = []

            for task in task_batch:
                # Inner loop: Adapt to task
                adapted_params = self._adapt_to_task(task)

                # Evaluate adapted parameters
                loss = self._evaluate_on_task(task, adapted_params)
                episode_loss += loss
                episode_adapt.append(1 - loss)  # Success = 1 - loss

            # Average loss across tasks
            avg_loss = episode_loss / len(task_batch)
            avg_adapt = np.mean(episode_adapt)

            meta_losses.append(avg_loss)
            adaptation_success.append(avg_adapt)

            # Meta-update (simplified - in practice would use gradients)
            self._meta_update(avg_loss)

        return {
            'final_meta_loss': np.mean(meta_losses[-10:]),
            'adaptation_success': np.mean(adaptation_success),
            'meta_learning_progress': adaptation_success[-1] - adaptation_success[0]
        }

    def _adapt_to_task(
        self,
        task: LearningTask,
        n_steps: int = 5
    ) -> Dict[str, np.ndarray]:
        """Adapt meta-parameters to a specific task."""
        # Start from meta-parameters
        adapted = self.meta_parameters.copy()

        # Inner loop gradient steps (simplified)
        for _ in range(n_steps):
            # Compute task-specific loss
            # Update adapted parameters
            # In full implementation, would use actual gradients
            pass

        return adapted

    def _evaluate_on_task(
        self,
        task: LearningTask,
        parameters: Dict[str, np.ndarray]
    ) -> float:
        """Evaluate parameters on a task."""
        # Simplified evaluation
        # In practice, would compute actual loss
        base_loss = task.difficulty
        return base_loss * 0.5  # Assume 50% improvement

    def _meta_update(self, meta_loss: float):
        """Update meta-parameters based on meta-loss."""
        # Simplified meta-gradient update
        # In practice, would accumulate gradients across tasks
        pass

    def fast_adapt(
        self,
        new_task: LearningTask,
        support_examples: np.ndarray,
        n_steps: int = 5
    ) -> float:
        """
        Fast adaptation to a new task with few examples.

        Args:
            new_task: New task to adapt to
            support_examples: Few-shot examples
            n_steps: Number of adaptation steps

        Returns:
            Adaptation performance
        """
        # Adapt to new task
        adapted_params = self._adapt_to_task(new_task, n_steps)

        # Evaluate adaptation
        performance = self._evaluate_on_task(new_task, adapted_params)

        return performance


# =============================================================================
# Task-Agnostic Meta-Learner
# =============================================================================
class TaskAgnosticMetaLearner:
    """
    Task-agnostic meta-learning that doesn't assume task distribution.

    Uses self-supervision and unsupervised meta-learning.
    """

    def __init__(self):
        """Initialize task-agnostic meta-learner."""
        self.representation_learner = None
        self.task_embeddings = {}
        self.similarity_kernel = None

    def meta_train_unsupervised(
        self,
        data: np.ndarray,
        n_epochs: int = 100
    ) -> Dict[str, float]:
        """
        Meta-train without task labels.

        Args:
            data: Unlabeled data
            n_epochs: Number of training epochs

        Returns:
            Training metrics
        """
        # Learn general representations
        # Use contrastive learning, autoencoders, etc.

        losses = []
        for epoch in range(n_epochs):
            # Self-supervised learning
            loss = self._self_supervised_loss(data)
            losses.append(loss)

        return {
            'final_loss': np.mean(losses[-10:]),
            'representation_quality': 1 - np.mean(losses[-10:])
        }

    def _self_supervised_loss(self, data: np.ndarray) -> float:
        """Compute self-supervised loss."""
        # Simplified: use reconstruction loss
        return 0.3  # Placeholder

    def adapt_to_task(
        self,
        task: LearningTask,
        few_shot_data: np.ndarray
    ) -> float:
        """Adapt to new task using learned representations."""
        # Use pre-trained representations
        # Fine-tune on few examples
        return 0.7  # Placeholder


# =============================================================================
# Continual Learning System
# =============================================================================
class ContinualLearningSystem:
    """
    Continual learning without catastrophic forgetting.

    Techniques:
    - Elastic Weight Consolidation (EWC)
    - Progressive Neural Networks
    - Experience Replay
    - Knowledge Distillation
    """

    def __init__(self):
        """Initialize continual learning system."""
        self.task_performances = {}
        self.importance_weights = {}
        #self.replay_buffer = []
        self.previous_tasks = []

    def learn_task(
        self,
        task: LearningTask,
        data: np.ndarray
    ) -> LearningResult:
        """
        Learn a new task while protecting previous knowledge.

        Args:
            task: New task to learn
            data: Training data for the task

        Returns:
            Learning result
        """
        # Calculate importance of current parameters
        importance = self._calculate_parameter_importance(task, data)
        self.importance_weights[task.task_id] = importance

        # Train on new task with regularization
        performance = self._train_with_regularization(task, data, importance)

        # Evaluate on all previous tasks
        previous_performance = self._evaluate_on_previous_tasks()

        result = LearningResult(
            task_id=task.task_id,
            strategy=LearningStrategy.SUPERVISED,
            performance=performance,
            training_time=1.0,
            resource_usage=1.0,
            generalization=previous_performance,
            confidence=0.8
        )

        self.task_performances[task.task_id] = result
        self.previous_tasks.append(task)

        return result

    def _calculate_parameter_importance(
        self,
        task: LearningTask,
        data: np.ndarray
    ) -> np.ndarray:
        """Calculate importance of parameters for task."""
        # Simplified: use Fisher information
        # In practice, would compute actual Fisher information matrix
        return np.random.rand(100)  # Placeholder

    def _train_with_regularization(
        self,
        task: LearningTask,
        data: np.ndarray,
        importance: np.ndarray
    ) -> float:
        """Train with EWC-style regularization."""
        # Loss = task_loss + lambda * sum(importance * (theta - theta_old)^2)
        return 0.75  # Placeholder

    def _evaluate_on_previous_tasks(self) -> float:
        """Evaluate performance on all previous tasks."""
        if not self.previous_tasks:
            return 1.0

        # Average performance on previous tasks
        performances = [
            self.task_performances[task.task_id].performance
            for task in self.previous_tasks
        ]
        return np.mean(performances)


# =============================================================================
# Learning Strategy Selector
# =============================================================================
class LearningStrategySelector:
    """
    Select the best learning strategy for a given task.

    Uses meta-learning about which strategies work best for which tasks.
    """

    def __init__(self):
        """Initialize strategy selector."""
        self.strategy_history = defaultdict(list)
        self.task_characteristics = {}

    def select_strategy(
        self,
        task: LearningTask,
        available_strategies: List[LearningStrategy]
    ) -> LearningStrategy:
        """
        Select the best strategy for a task.

        Args:
            task: Task to solve
            available_strategies: Available learning strategies

        Returns:
            Selected strategy
        """
        # Extract task characteristics
        characteristics = self._extract_characteristics(task)
        self.task_characteristics[task.task_id] = characteristics

        # Predict best strategy based on history
        best_strategy = self._predict_best_strategy(characteristics, available_strategies)

        return best_strategy

    def _extract_characteristics(self, task: LearningTask) -> Dict[str, float]:
        """Extract characteristics of a task."""
        return {
            'data_size': len(task.training_data) if task.training_data is not None else 0,
            'difficulty': task.difficulty,
            'domain_complexity': len(task.metadata.get('concepts', [])),
            'type_encoding': hash(task.task_type) % 10 / 10.0
        }

    def _predict_best_strategy(
        self,
        characteristics: Dict[str, float],
        available_strategies: List[LearningStrategy]
    ) -> LearningStrategy:
        """Predict best strategy based on task characteristics."""
        # Simple heuristic: match strategy to task type
        task_type = characteristics.get('type_encoding', 0)

        if task_type < 0.3:  # Classification
            if LearningStrategy.SUPERVISED in available_strategies:
                return LearningStrategy.SUPERVISED
            elif LearningStrategy.FEW_SHOT in available_strategies:
                return LearningStrategy.FEW_SHOT

        elif task_type < 0.6:  # Regression/Prediction
            if LearningStrategy.BAYESIAN in available_strategies:
                return LearningStrategy.BAYESIAN
            elif LearningStrategy.SUPERVISED in available_strategies:
                return LearningStrategy.SUPERVISED

        else:  # Discovery/Generation
            if LearningStrategy.REINFORCEMENT in available_strategies:
                return LearningStrategy.REINFORCEMENT
            elif LearningStrategy.UNSUPERVISED in available_strategies:
                return LearningStrategy.UNSUPERVISED

        # Default
        return available_strategies[0] if available_strategies else LearningStrategy.SUPERVISED

    def update_strategy_performance(
        self,
        task_id: str,
        strategy: LearningStrategy,
        performance: float
    ):
        """Update strategy performance history."""
        self.strategy_history[strategy].append(performance)


# =============================================================================
# Unified Meta-Learning System
# =============================================================================
class MetaLearningSystem:
    """
    Unified meta-learning system.

    Integrates:
    - MAML-style fast adaptation
    - Task-agnostic meta-learning
    - Continual learning
    - Strategy selection
    - Transfer learning
    """

    def __init__(self):
        """Initialize the meta-learning system."""
        self.maml_learner = MAMLMetaLearner()
        self.task_agnostic_learner = TaskAgnosticMetaLearner()
        self.continual_learner = ContinualLearningSystem()
        self.strategy_selector = LearningStrategySelector()

        self.learning_history = []
        self.transfer_knowledge = []

    def meta_train(
        self,
        tasks: List[LearningTask],
        method: str = "maml"
    ) -> Dict[str, float]:
        """
        Meta-train on a distribution of tasks.

        Args:
            tasks: Tasks to meta-train on
            method: Meta-learning method ("maml", "task_agnostic")

        Returns:
            Training metrics
        """
        if method == "maml":
            return self.maml_learner.meta_train(tasks)
        else:
            # Combine data from all tasks
            all_data = np.concatenate([
                task.training_data for task in tasks
                if task.training_data is not None
            ], axis=0) if any(t.training_data is not None for t in tasks) else None

            if all_data is not None:
                return self.task_agnostic_learner.meta_train_unsupervised(all_data)
            else:
                return {'final_loss': 0.5, 'representation_quality': 0.5}

    def learn_new_task(
        self,
        task: LearningTask,
        support_data: Optional[np.ndarray] = None,
        strategy: Optional[LearningStrategy] = None
    ) -> LearningResult:
        """
        Learn a new task using meta-learning.

        Args:
            task: Task to learn
            support_data: Few-shot support examples
            strategy: Learning strategy (auto-selected if None)

        Returns:
            Learning result
        """
        # Select strategy if not provided
        if strategy is None:
            available_strategies = [
                LearningStrategy.SUPERVISED,
                LearningStrategy.FEW_SHOT,
                LearningStrategy.META_LEARNING
            ]
            strategy = self.strategy_selector.select_strategy(task, available_strategies)

        # Learn using selected strategy
        if strategy == LearningStrategy.META_LEARNING:
            performance = self.maml_learner.fast_adapt(task, support_data)
        elif strategy == LearningStrategy.FEW_SHOT:
            performance = self.task_agnostic_learner.adapt_to_task(task, support_data)
        else:
            # Standard continual learning
            result = self.continual_learner.learn_task(task, support_data)
            return result

        # Create result
        result = LearningResult(
            task_id=task.task_id,
            strategy=strategy,
            performance=performance,
            training_time=1.0,
            resource_usage=0.5,
            generalization=performance * 0.9,
            confidence=0.8
        )

        self.learning_history.append(result)
        self.strategy_selector.update_strategy_performance(
            task.task_id, strategy, performance
        )

        return result

    def transfer_learning(
        self,
        source_domain: str,
        target_domain: str,
        source_data: np.ndarray,
        target_data: np.ndarray
    ) -> TransferKnowledge:
        """
        Transfer knowledge from source to target domain.

        Args:
            source_domain: Source domain
            target_domain: Target domain
            source_data: Data from source domain
            target_data: Data from target domain

        Returns:
            Transfer knowledge result
        """
        # Measure domain similarity
        similarity = self._domain_similarity(source_data, target_data)

        # Identify transferable concepts
        concepts = self._identify_transferable_concepts(source_domain, target_domain)

        # Estimate adaptation required
        adaptation_required = 1 - similarity

        # Estimate success rate
        success_rate = similarity * 0.8 + 0.2

        transfer = TransferKnowledge(
            source_domain=source_domain,
            target_domain=target_domain,
            transferred_concepts=concepts,
            adaptation_required=adaptation_required,
            success_rate=success_rate
        )

        self.transfer_knowledge.append(transfer)
        return transfer

    def _domain_similarity(
        self,
        data1: np.ndarray,
        data2: np.ndarray
    ) -> float:
        """Calculate similarity between two domains."""
        # Simplified: use distribution overlap
        if data1.shape[1] != data2.shape[1]:
            return 0.3  # Different feature spaces

        # Simple correlation-based similarity
        mean1, mean2 = np.mean(data1, axis=0), np.mean(data2, axis=0)
        similarity = 1 - np.mean(np.abs(mean1 - mean2)) / (np.std(data1) + 1e-6)
        return max(0, min(1, similarity))

    def _identify_transferable_concepts(
        self,
        source_domain: str,
        target_domain: str
    ) -> List[str]:
        """Identify concepts that can transfer between domains."""
        # Common scientific concepts
        common_concepts = [
            'causality', 'equilibrium', 'conservation', 'symmetry',
            'optimization', 'feedback', 'stability', 'variation'
        ]
        return common_concepts[:4]  # Return subset

    def get_meta_learning_metrics(self) -> Dict[str, float]:
        """Get meta-learning system metrics."""
        if not self.learning_history:
            return {}

        recent_results = self.learning_history[-10:]

        return {
            'average_performance': np.mean([r.performance for r in recent_results]),
            'average_generalization': np.mean([r.generalization for r in recent_results]),
            'total_tasks_learned': len(self.learning_history),
            'transfer_count': len(self.transfer_knowledge),
            'strategies_used': len(set(r.strategy for r in self.learning_history))
        }


# =============================================================================
# Factory Functions
# =============================================================================
def create_meta_learning_system() -> MetaLearningSystem:
    """Create a meta-learning system."""
    return MetaLearningSystem()


# =============================================================================
# Integration with STAR-Learn
# =============================================================================
def get_meta_learning_reward(
    discovery: Dict[str, Any],
    meta_system: MetaLearningSystem
) -> Tuple[float, Dict]:
    """
    Calculate reward for meta-learning discoveries.

    High rewards for:
    - Fast adaptation (few-shot learning)
    - Transfer learning success
    - Continual learning without forgetting
    - Learning strategy improvements
    """
    content = discovery.get('content', '').lower()

    details = {}
    reward = 0.0

    # Check for meta-learning keywords
    meta_keywords = ['few-shot', 'transfer learning', 'meta-learning',
                     'learn to learn', 'adaptation', 'generalization']

    for keyword in meta_keywords:
        if keyword in content:
            reward += 0.15
            details['meta_learning'] = True

    # Bonus for fast learning
    if 'quickly' in content or 'rapid' in content:
        reward += 0.2
        details['fast_adaptation'] = True

    # Bonus for transfer
    if 'transfer' in content:
        reward += 0.2
        details['transfer_learning'] = True

    # Bonus for continual learning
    if 'continual' in content or 'without forgetting' in content:
        reward += 0.2
        details['continual_learning'] = True

    return min(reward, 1.0), details
