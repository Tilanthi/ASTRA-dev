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
V60 Active Inference Controller

Implements free energy minimization as a unifying principle for cognition:
- Perception as inference about hidden causes
- Action as sampling to confirm predictions
- Learning as model parameter optimization
- Planning as inference about future policies

Key innovations:
1. Variational free energy minimization
2. Expected free energy for action selection
3. Hierarchical predictive processing
4. Precision-weighted prediction errors
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Union
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from scipy import special
from collections import defaultdict
import time


class InferenceMode(Enum):
    """Modes of inference"""
    PERCEPTION = "perception"       # Infer hidden states from observations
    ACTION = "action"              # Select actions to minimize expected FE
    PLANNING = "planning"          # Infer optimal policies
    LEARNING = "learning"          # Update model parameters


class BeliefType(Enum):
    """Types of beliefs"""
    STATE = "state"               # Beliefs about current state
    POLICY = "policy"             # Beliefs about actions
    PARAMETER = "parameter"       # Beliefs about model parameters
    PRECISION = "precision"       # Beliefs about precision


class HierarchyLevel(Enum):
    """Levels in predictive hierarchy"""
    SENSORY = 0
    PERCEPTUAL = 1
    CONCEPTUAL = 2
    CONTEXTUAL = 3
    METACOGNITIVE = 4


@dataclass
class Belief:
    """A probabilistic belief"""
    id: str
    belief_type: BeliefType
    mean: np.ndarray
    precision: np.ndarray  # Inverse variance
    prior_mean: Optional[np.ndarray] = None
    prior_precision: Optional[np.ndarray] = None
    entropy: float = 0.0
    last_updated: float = field(default_factory=time.time)

    def update_gaussian(
        self,
        observation: np.ndarray,
        likelihood_precision: np.ndarray
    ):
        """Bayesian update with Gaussian likelihood"""
        # Precision-weighted update
        posterior_precision = self.precision + likelihood_precision
        posterior_mean = (
            self.precision * self.mean + likelihood_precision * observation
        ) / posterior_precision

        self.mean = posterior_mean
        self.precision = posterior_precision
        self.entropy = 0.5 * np.log(2 * np.pi * np.e / np.mean(posterior_precision))
        self.last_updated = time.time()

    def kl_divergence_from_prior(self) -> float:
        """Compute KL divergence from prior"""
        if self.prior_mean is None or self.prior_precision is None:
            return 0.0

        # KL divergence for Gaussians
        k = len(self.mean)
        term1 = np.sum(self.prior_precision / self.precision)
        term2 = np.sum(
            self.prior_precision * (self.mean - self.prior_mean) ** 2
        )
        term3 = -k
        term4 = np.sum(np.log(self.precision / self.prior_precision))

        return 0.5 * (term1 + term2 + term3 - term4)


@dataclass
class PredictionError:
    """A prediction error signal"""
    level: HierarchyLevel
    source: str
    predicted: np.ndarray
    observed: np.ndarray
    error: np.ndarray
    precision: float
    weighted_error: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class Policy:
    """A policy (sequence of actions)"""
    id: str
    actions: List[np.ndarray]
    expected_free_energy: float = 0.0
    probability: float = 0.0
    epistemic_value: float = 0.0
    pragmatic_value: float = 0.0


@dataclass
class GenerativeModel:
    """A generative model component"""
    name: str
    transition_matrix: Optional[np.ndarray] = None  # P(s'|s,a)
    observation_matrix: Optional[np.ndarray] = None  # P(o|s)
    prior_states: Optional[np.ndarray] = None       # P(s)
    preferred_observations: Optional[np.ndarray] = None  # C (preferences)
    parameters: Dict[str, np.ndarray] = field(default_factory=dict)


class FreeEnergyComputer:
    """
    Computes variational and expected free energy.
    """

    def __init__(self):
        self.eps = 1e-10  # Numerical stability

    def variational_free_energy(
        self,
        beliefs: Dict[str, Belief],
        observations: np.ndarray,
        generative_model: GenerativeModel
    ) -> float:
        """
        Compute variational free energy:
        F = E_q[log q(s) - log p(o,s)]
          = -E_q[log p(o|s)] + KL[q(s)||p(s)]
        """
        # Get state beliefs
        state_belief = beliefs.get('state')
        if state_belief is None:
            return 0.0

        # Accuracy term: -E_q[log p(o|s)]
        # Simplified: using negative log likelihood
        if generative_model.observation_matrix is not None:
            predicted_obs = generative_model.observation_matrix @ state_belief.mean
            accuracy = -np.sum(
                observations * np.log(predicted_obs + self.eps)
            )
        else:
            accuracy = np.sum((observations - state_belief.mean) ** 2)

        # Complexity term: KL divergence from prior
        complexity = state_belief.kl_divergence_from_prior()

        return accuracy + complexity

    def expected_free_energy(
        self,
        policy: Policy,
        beliefs: Dict[str, Belief],
        generative_model: GenerativeModel,
        horizon: int = 3
    ) -> float:
        """
        Compute expected free energy for a policy:
        G = E_q[log q(s) - log p(o,s) | policy]
          = -epistemic_value - pragmatic_value
        """
        epistemic = self._epistemic_value(policy, beliefs, generative_model, horizon)
        pragmatic = self._pragmatic_value(policy, beliefs, generative_model, horizon)

        policy.epistemic_value = epistemic
        policy.pragmatic_value = pragmatic

        # EFE is negative of value (we minimize EFE)
        return -epistemic - pragmatic

    def _epistemic_value(
        self,
        policy: Policy,
        beliefs: Dict[str, Belief],
        model: GenerativeModel,
        horizon: int
    ) -> float:
        """
        Epistemic value: expected information gain
        = E[H[q(s)] - H[q(s|o)]]
        """
        state_belief = beliefs.get('state')
        if state_belief is None:
            return 0.0

        # Current entropy
        current_entropy = state_belief.entropy

        # Expected entropy reduction from future observations
        # Simplified: assume observations reduce entropy proportionally
        expected_entropy_reduction = 0.0

        for t in range(horizon):
            # Future uncertainty grows with time
            future_uncertainty = current_entropy * (1 + 0.1 * t)
            # Expected reduction from observation
            expected_entropy_reduction += future_uncertainty * 0.3

        return expected_entropy_reduction

    def _pragmatic_value(
        self,
        policy: Policy,
        beliefs: Dict[str, Belief],
        model: GenerativeModel,
        horizon: int
    ) -> float:
        """
        Pragmatic value: expected preference satisfaction
        = E[log p(o | preferred)]
        """
        if model.preferred_observations is None:
            return 0.0

        state_belief = beliefs.get('state')
        if state_belief is None:
            return 0.0

        # Simulate future states under policy
        value = 0.0
        current_state = state_belief.mean.copy()

        for t, action in enumerate(policy.actions[:horizon]):
            # Transition to next state
            if model.transition_matrix is not None:
                # Action-conditioned transition
                next_state = model.transition_matrix @ current_state
            else:
                next_state = current_state + action

            # Expected observation
            if model.observation_matrix is not None:
                expected_obs = model.observation_matrix @ next_state
            else:
                expected_obs = next_state

            # Value from preferences
            value += np.sum(
                model.preferred_observations * np.log(expected_obs + self.eps)
            )

            current_state = next_state

        return value / max(1, horizon)


class PredictiveProcessor:
    """
    Implements hierarchical predictive processing.
    """

    def __init__(self, num_levels: int = 5):
        self.num_levels = num_levels
        self.levels: Dict[int, Dict[str, Any]] = {}
        self.prediction_errors: List[PredictionError] = []

        for level in range(num_levels):
            self.levels[level] = {
                'belief': None,
                'prediction': None,
                'precision': 1.0,
                'learning_rate': 0.1 * (0.5 ** level)  # Slower at higher levels
            }

    def process(
        self,
        observation: np.ndarray,
        top_down_prediction: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Run predictive processing iteration
        """
        results = {
            'beliefs': {},
            'prediction_errors': [],
            'total_error': 0.0
        }

        # Bottom-up processing
        current_input = observation

        for level in range(self.num_levels):
            level_data = self.levels[level]

            # Get top-down prediction for this level
            if level < self.num_levels - 1:
                higher_belief = self.levels[level + 1].get('belief')
                if higher_belief is not None:
                    prediction = self._generate_prediction(higher_belief, level)
                else:
                    prediction = current_input  # No prediction, use input
            elif top_down_prediction is not None:
                prediction = top_down_prediction
            else:
                prediction = current_input

            level_data['prediction'] = prediction

            # Compute prediction error
            error = current_input - prediction
            precision = level_data['precision']
            weighted_error = precision * np.sum(error ** 2)

            pe = PredictionError(
                level=HierarchyLevel(level),
                source=f"level_{level}",
                predicted=prediction,
                observed=current_input,
                error=error,
                precision=precision,
                weighted_error=weighted_error
            )
            self.prediction_errors.append(pe)
            results['prediction_errors'].append(pe)
            results['total_error'] += weighted_error

            # Update belief at this level
            if level_data['belief'] is None:
                level_data['belief'] = Belief(
                    id=f"belief_level_{level}",
                    belief_type=BeliefType.STATE,
                    mean=current_input,
                    precision=np.ones_like(current_input) * precision
                )
            else:
                # Gradient descent on prediction error
                lr = level_data['learning_rate']
                level_data['belief'].mean += lr * error * precision

            results['beliefs'][level] = level_data['belief']

            # Transform for next level (abstraction)
            current_input = self._abstract(current_input, level)

        return results

    def _generate_prediction(
        self,
        higher_belief: Belief,
        target_level: int
    ) -> np.ndarray:
        """Generate prediction for lower level from higher belief"""
        # Simplified: identity mapping with noise
        prediction = higher_belief.mean.copy()
        # Add level-appropriate transformation here
        return prediction

    def _abstract(
        self,
        input_data: np.ndarray,
        level: int
    ) -> np.ndarray:
        """Abstract input for next hierarchical level"""
        # Simplified: dimensionality reduction
        if len(input_data) > 1:
            # Simple averaging to reduce dimension
            return np.array([np.mean(input_data)])
        return input_data

    def update_precisions(self, learning_rate: float = 0.01):
        """Update precision estimates based on prediction errors"""
        for level in range(self.num_levels):
            level_data = self.levels[level]

            # Get recent errors for this level
            recent_errors = [
                pe.error for pe in self.prediction_errors[-100:]
                if pe.level.value == level
            ]

            if recent_errors:
                # Precision is inverse variance
                error_variance = np.var(recent_errors)
                new_precision = 1.0 / (error_variance + 1e-6)
                level_data['precision'] = (
                    (1 - learning_rate) * level_data['precision'] +
                    learning_rate * new_precision
                )


class ActionSelector:
    """
    Selects actions based on expected free energy.
    """

    def __init__(
        self,
        free_energy_computer: FreeEnergyComputer,
        softmax_temperature: float = 1.0
    ):
        self.fe_computer = free_energy_computer
        self.temperature = softmax_temperature
        self.policy_cache: Dict[str, Policy] = {}

    def select_action(
        self,
        policies: List[Policy],
        beliefs: Dict[str, Belief],
        model: GenerativeModel
    ) -> Tuple[np.ndarray, Policy]:
        """Select action by minimizing expected free energy"""
        # Compute EFE for each policy
        for policy in policies:
            policy.expected_free_energy = self.fe_computer.expected_free_energy(
                policy, beliefs, model
            )

        # Convert to probabilities (softmax of negative EFE)
        efes = np.array([p.expected_free_energy for p in policies])
        probs = special.softmax(-efes / self.temperature)

        for policy, prob in zip(policies, probs):
            policy.probability = prob

        # Sample policy
        selected_idx = np.random.choice(len(policies), p=probs)
        selected_policy = policies[selected_idx]

        # Return first action of selected policy
        if selected_policy.actions:
            return selected_policy.actions[0], selected_policy
        else:
            return np.zeros(1), selected_policy

    def generate_policies(
        self,
        num_actions: int,
        horizon: int,
        action_space: Optional[List[np.ndarray]] = None
    ) -> List[Policy]:
        """Generate candidate policies"""
        if action_space is None:
            action_space = [np.array([i]) for i in range(num_actions)]

        policies = []

        # Generate random policies
        for i in range(min(50, num_actions ** horizon)):
            actions = [
                action_space[np.random.randint(len(action_space))]
                for _ in range(horizon)
            ]
            policy = Policy(
                id=f"policy_{i}_{time.time()}",
                actions=actions
            )
            policies.append(policy)

        return policies


class BeliefUpdater:
    """
    Updates beliefs based on observations and actions.
    """

    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.beliefs: Dict[str, Belief] = {}

    def initialize_belief(
        self,
        belief_id: str,
        belief_type: BeliefType,
        dimension: int,
        prior_mean: Optional[np.ndarray] = None,
        prior_precision: Optional[float] = None
    ) -> Belief:
        """Initialize a belief"""
        if prior_mean is None:
            prior_mean = np.zeros(dimension)
        if prior_precision is None:
            prior_precision = 1.0

        belief = Belief(
            id=belief_id,
            belief_type=belief_type,
            mean=prior_mean.copy(),
            precision=np.ones(dimension) * prior_precision,
            prior_mean=prior_mean,
            prior_precision=np.ones(dimension) * prior_precision
        )

        self.beliefs[belief_id] = belief
        return belief

    def update_from_observation(
        self,
        belief_id: str,
        observation: np.ndarray,
        likelihood_precision: float = 1.0
    ) -> Optional[Belief]:
        """Update belief from observation"""
        if belief_id not in self.beliefs:
            return None

        belief = self.beliefs[belief_id]
        precision_array = np.ones_like(observation) * likelihood_precision
        belief.update_gaussian(observation, precision_array)

        return belief

    def update_from_action(
        self,
        belief_id: str,
        action: np.ndarray,
        transition_noise: float = 0.1
    ) -> Optional[Belief]:
        """Update belief after taking action"""
        if belief_id not in self.beliefs:
            return None

        belief = self.beliefs[belief_id]

        # Simple transition model: state += action + noise
        belief.mean = belief.mean + action
        belief.precision = belief.precision / (1 + transition_noise)

        return belief

    def get_belief(self, belief_id: str) -> Optional[Belief]:
        """Get belief by ID"""
        return self.beliefs.get(belief_id)


class ModelLearner:
    """
    Learns generative model parameters.
    """

    def __init__(self, learning_rate: float = 0.01):
        self.learning_rate = learning_rate
        self.experience_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 1000

    def store_experience(
        self,
        state: np.ndarray,
        action: np.ndarray,
        next_state: np.ndarray,
        observation: np.ndarray
    ):
        """Store experience for learning"""
        self.experience_buffer.append({
            'state': state,
            'action': action,
            'next_state': next_state,
            'observation': observation,
            'timestamp': time.time()
        })

        if len(self.experience_buffer) > self.max_buffer_size:
            self.experience_buffer = self.experience_buffer[-self.max_buffer_size:]

    def update_model(
        self,
        model: GenerativeModel,
        batch_size: int = 32
    ) -> Dict[str, float]:
        """Update model parameters from experience"""
        if len(self.experience_buffer) < batch_size:
            return {'error': 'Insufficient experience'}

        # Sample batch
        indices = np.random.choice(
            len(self.experience_buffer),
            size=min(batch_size, len(self.experience_buffer)),
            replace=False
        )
        batch = [self.experience_buffer[i] for i in indices]

        losses = {}

        # Update transition model
        if model.transition_matrix is not None:
            trans_loss = self._update_transition_model(model, batch)
            losses['transition_loss'] = trans_loss

        # Update observation model
        if model.observation_matrix is not None:
            obs_loss = self._update_observation_model(model, batch)
            losses['observation_loss'] = obs_loss

        return losses

    def _update_transition_model(
        self,
        model: GenerativeModel,
        batch: List[Dict[str, Any]]
    ) -> float:
        """Update transition matrix"""
        total_loss = 0.0

        for experience in batch:
            state = experience['state']
            action = experience['action']
            next_state = experience['next_state']

            # Predicted next state
            predicted = model.transition_matrix @ state

            # Error
            error = next_state - predicted
            total_loss += np.sum(error ** 2)

            # Gradient update (simplified)
            gradient = np.outer(error, state)
            model.transition_matrix += self.learning_rate * gradient

        return total_loss / len(batch)

    def _update_observation_model(
        self,
        model: GenerativeModel,
        batch: List[Dict[str, Any]]
    ) -> float:
        """Update observation matrix"""
        total_loss = 0.0

        for experience in batch:
            state = experience['state']
            observation = experience['observation']

            # Predicted observation
            predicted = model.observation_matrix @ state

            # Error
            error = observation - predicted
            total_loss += np.sum(error ** 2)

            # Gradient update
            gradient = np.outer(error, state)
            model.observation_matrix += self.learning_rate * gradient

        return total_loss / len(batch)


class ActiveInferenceController:
    """
    Complete active inference controller integrating all components.
    """

    def __init__(
        self,
        state_dim: int = 4,
        observation_dim: int = 4,
        action_dim: int = 2,
        num_hierarchy_levels: int = 3
    ):
        self.state_dim = state_dim
        self.observation_dim = observation_dim
        self.action_dim = action_dim

        # Components
        self.free_energy_computer = FreeEnergyComputer()
        self.predictive_processor = PredictiveProcessor(num_hierarchy_levels)
        self.action_selector = ActionSelector(self.free_energy_computer)
        self.belief_updater = BeliefUpdater()
        self.model_learner = ModelLearner()

        # Initialize generative model
        self.generative_model = self._initialize_model()

        # Initialize beliefs
        self._initialize_beliefs()

        # Statistics
        self.stats = {
            'steps': 0,
            'total_free_energy': 0.0,
            'actions_taken': 0,
            'beliefs_updated': 0,
            'model_updates': 0
        }

        self.history: List[Dict[str, Any]] = []

    def _initialize_model(self) -> GenerativeModel:
        """Initialize the generative model"""
        return GenerativeModel(
            name="active_inference_model",
            transition_matrix=np.eye(self.state_dim) + 0.1 * np.random.randn(
                self.state_dim, self.state_dim
            ),
            observation_matrix=np.eye(self.observation_dim, self.state_dim) + 0.1 * np.random.randn(
                self.observation_dim, self.state_dim
            ),
            prior_states=np.ones(self.state_dim) / self.state_dim,
            preferred_observations=np.zeros(self.observation_dim)
        )

    def _initialize_beliefs(self):
        """Initialize belief states"""
        self.belief_updater.initialize_belief(
            'state',
            BeliefType.STATE,
            self.state_dim,
            prior_precision=1.0
        )
        self.belief_updater.initialize_belief(
            'policy',
            BeliefType.POLICY,
            self.action_dim,
            prior_precision=0.5
        )

    def step(
        self,
        observation: np.ndarray,
        learning: bool = True
    ) -> Dict[str, Any]:
        """
        Execute one step of active inference:
        1. Perception (update beliefs from observation)
        2. Action selection (minimize expected free energy)
        3. Learning (update model parameters)
        """
        result = {
            'observation': observation,
            'action': None,
            'free_energy': 0.0,
            'prediction_errors': [],
            'selected_policy': None
        }

        # 1. PERCEPTION: Update beliefs from observation
        # Run predictive processing
        pp_result = self.predictive_processor.process(observation)
        result['prediction_errors'] = pp_result['prediction_errors']

        # Update state belief
        self.belief_updater.update_from_observation(
            'state',
            observation,
            likelihood_precision=1.0
        )
        self.stats['beliefs_updated'] += 1

        # 2. Compute free energy
        beliefs = {k: v for k, v in self.belief_updater.beliefs.items()}
        fe = self.free_energy_computer.variational_free_energy(
            beliefs,
            observation,
            self.generative_model
        )
        result['free_energy'] = fe
        self.stats['total_free_energy'] += fe

        # 3. ACTION: Select action minimizing expected free energy
        policies = self.action_selector.generate_policies(
            num_actions=self.action_dim,
            horizon=3
        )

        action, selected_policy = self.action_selector.select_action(
            policies,
            beliefs,
            self.generative_model
        )

        result['action'] = action
        result['selected_policy'] = selected_policy
        self.stats['actions_taken'] += 1

        # Update belief for action
        self.belief_updater.update_from_action('state', action)

        # 4. LEARNING: Update model if enabled
        if learning and len(self.history) > 0:
            prev = self.history[-1]
            self.model_learner.store_experience(
                state=prev.get('state_belief', np.zeros(self.state_dim)),
                action=prev.get('action', np.zeros(self.action_dim)),
                next_state=beliefs['state'].mean if 'state' in beliefs else np.zeros(self.state_dim),
                observation=observation
            )

            if len(self.model_learner.experience_buffer) >= 32:
                losses = self.model_learner.update_model(
                    self.generative_model,
                    batch_size=32
                )
                result['learning_losses'] = losses
                self.stats['model_updates'] += 1

        # Update precision estimates
        self.predictive_processor.update_precisions()

        # Store for history
        result['state_belief'] = beliefs.get('state', Belief(
            id='none', belief_type=BeliefType.STATE,
            mean=np.zeros(self.state_dim),
            precision=np.ones(self.state_dim)
        )).mean.copy()

        self.history.append(result)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

        self.stats['steps'] += 1

        return result

    def set_preferences(self, preferred_observations: np.ndarray):
        """Set preferred observations (goals)"""
        self.generative_model.preferred_observations = preferred_observations

    def get_beliefs(self) -> Dict[str, Belief]:
        """Get current beliefs"""
        return dict(self.belief_updater.beliefs)

    def get_free_energy(self) -> float:
        """Get current free energy"""
        beliefs = self.get_beliefs()
        if not beliefs or 'state' not in beliefs:
            return 0.0

        # Get most recent observation from history
        if self.history:
            observation = self.history[-1].get('observation', np.zeros(self.observation_dim))
        else:
            observation = np.zeros(self.observation_dim)

        return self.free_energy_computer.variational_free_energy(
            beliefs,
            observation,
            self.generative_model
        )

    def get_prediction_errors(self) -> List[PredictionError]:
        """Get recent prediction errors"""
        return self.predictive_processor.prediction_errors[-100:]

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            **self.stats,
            'average_free_energy': (
                self.stats['total_free_energy'] / max(1, self.stats['steps'])
            ),
            'experience_buffer_size': len(self.model_learner.experience_buffer),
            'history_length': len(self.history)
        }


# Factory functions
def create_active_inference_controller(
    state_dim: int = 4,
    observation_dim: int = 4,
    action_dim: int = 2
) -> ActiveInferenceController:
    """Create active inference controller"""
    return ActiveInferenceController(
        state_dim=state_dim,
        observation_dim=observation_dim,
        action_dim=action_dim
    )


def create_generative_model(
    name: str,
    state_dim: int,
    observation_dim: int
) -> GenerativeModel:
    """Create a generative model"""
    return GenerativeModel(
        name=name,
        transition_matrix=np.eye(state_dim),
        observation_matrix=np.eye(observation_dim, state_dim),
        prior_states=np.ones(state_dim) / state_dim,
        preferred_observations=np.zeros(observation_dim)
    )


def create_belief(
    belief_id: str,
    belief_type: BeliefType,
    dimension: int
) -> Belief:
    """Create a belief"""
    return Belief(
        id=belief_id,
        belief_type=belief_type,
        mean=np.zeros(dimension),
        precision=np.ones(dimension)
    )


def create_policy(
    policy_id: str,
    actions: List[np.ndarray]
) -> Policy:
    """Create a policy"""
    return Policy(
        id=policy_id,
        actions=actions
    )


# Exports
__all__ = [
    # Enums
    'InferenceMode',
    'BeliefType',
    'HierarchyLevel',

    # Data classes
    'Belief',
    'PredictionError',
    'Policy',
    'GenerativeModel',

    # Components
    'FreeEnergyComputer',
    'PredictiveProcessor',
    'ActionSelector',
    'BeliefUpdater',
    'ModelLearner',

    # Main system
    'ActiveInferenceController',

    # Factory functions
    'create_active_inference_controller',
    'create_generative_model',
    'create_belief',
    'create_policy',
]
