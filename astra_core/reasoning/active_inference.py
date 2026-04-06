"""
Active Inference Framework for STAN V42

Unified perception-action loop where inference drives experiment design:
- Free energy minimization for belief updating
- Predictive coding for anomaly detection
- Optimal observation scheduling
- Detecting unexpected signals

Date: 2025-12-11
Version: 42.0
"""

import time
import uuid
import math
import copy
import random
from typing import Dict, List, Optional, Any, Tuple, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict


class ActionType(Enum):
    """Types of actions in active inference"""
    OBSERVE = "observe"           # Collect new observation
    EXPERIMENT = "experiment"     # Perform experiment
    COMPUTE = "compute"           # Run computation
    QUERY = "query"               # Query external knowledge
    REFINE = "refine"             # Refine model
    COMMUNICATE = "communicate"   # Output result


class BeliefUpdateMode(Enum):
    """Modes for belief updating"""
    BAYESIAN = "bayesian"
    VARIATIONAL = "variational"
    PREDICTIVE_CODING = "predictive_coding"
    FREE_ENERGY = "free_energy"


class PredictionType(Enum):
    """Types of predictions"""
    SENSORY = "sensory"           # Predicted observations
    PROPRIOCEPTIVE = "proprioceptive"  # Predicted internal states
    ACTIVE = "active"             # Predicted action outcomes


@dataclass
class GenerativeModel:
    """
    A generative model for active inference.

    Specifies:
    - Prior beliefs about hidden states
    - Likelihood mapping from states to observations
    - Transition dynamics
    """
    model_id: str
    name: str

    # State space
    hidden_states: List[str]
    observation_types: List[str]
    action_types: List[str]

    # Prior beliefs P(s)
    prior_mean: Dict[str, float] = field(default_factory=dict)
    prior_precision: Dict[str, float] = field(default_factory=dict)

    # Likelihood P(o|s) parameters
    likelihood_weights: Dict[str, Dict[str, float]] = field(default_factory=dict)
    observation_noise: Dict[str, float] = field(default_factory=dict)

    # Transition dynamics P(s'|s,a)
    transition_matrices: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Model uncertainty
    model_confidence: float = 0.5

    def __post_init__(self):
        if not self.model_id:
            self.model_id = f"gm_{uuid.uuid4().hex[:8]}"


@dataclass
class Belief:
    """Belief state in active inference"""
    belief_id: str

    # Posterior over hidden states
    state_means: Dict[str, float] = field(default_factory=dict)
    state_precisions: Dict[str, float] = field(default_factory=dict)

    # Prediction errors
    sensory_prediction_error: float = 0.0
    state_prediction_error: float = 0.0

    # Free energy components
    accuracy: float = 0.0  # -log P(o|s)
    complexity: float = 0.0  # KL[Q(s)||P(s)]

    # Temporal
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.belief_id:
            self.belief_id = f"bel_{uuid.uuid4().hex[:8]}"

    @property
    def free_energy(self) -> float:
        """Variational free energy F = -accuracy + complexity"""
        return -self.accuracy + self.complexity


@dataclass
class Prediction:
    """A prediction from the generative model"""
    prediction_id: str
    prediction_type: PredictionType

    # Predicted value
    predicted_value: Dict[str, float] = field(default_factory=dict)
    predicted_precision: Dict[str, float] = field(default_factory=dict)

    # Source
    source_state: str = ""
    source_action: str = ""

    # Temporal
    time_horizon: float = 0.0  # How far ahead
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.prediction_id:
            self.prediction_id = f"pred_{uuid.uuid4().hex[:8]}"


@dataclass
class PredictionError:
    """Prediction error signal"""
    error_id: str

    # Error type and magnitude
    error_type: str  # "sensory", "state", "action"
    error_magnitude: float = 0.0
    error_direction: Dict[str, float] = field(default_factory=dict)

    # Source
    predicted: Dict[str, float] = field(default_factory=dict)
    observed: Dict[str, float] = field(default_factory=dict)

    # Significance
    precision_weighted: float = 0.0  # Precision-weighted error
    is_anomaly: bool = False

    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.error_id:
            self.error_id = f"err_{uuid.uuid4().hex[:8]}"


@dataclass
class Action:
    """An action in active inference"""
    action_id: str
    action_type: ActionType

    # Action specification
    target: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Expected outcome
    expected_observation: Dict[str, float] = field(default_factory=dict)
    expected_information_gain: float = 0.0
    expected_free_energy: float = 0.0

    # Execution
    executed: bool = False
    actual_outcome: Dict[str, Any] = field(default_factory=dict)

    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.action_id:
            self.action_id = f"act_{uuid.uuid4().hex[:8]}"


@dataclass
class ActiveInferenceState:
    """Complete state of the active inference agent"""
    state_id: str

    # Generative model
    model: GenerativeModel

    # Current beliefs
    current_belief: Belief
    belief_history: List[Belief] = field(default_factory=list)

    # Predictions and errors
    active_predictions: List[Prediction] = field(default_factory=list)
    prediction_errors: List[PredictionError] = field(default_factory=list)

    # Action history
    planned_actions: List[Action] = field(default_factory=list)
    executed_actions: List[Action] = field(default_factory=list)

    # Performance metrics
    total_free_energy: float = 0.0
    cumulative_surprise: float = 0.0
    anomaly_count: int = 0

    def __post_init__(self):
        if not self.state_id:
            self.state_id = f"ais_{uuid.uuid4().hex[:8]}"


class FreeEnergyMinimizer:
    """
    Minimizes variational free energy through belief updating.

    F = -<log P(o,s)>_Q + <log Q(s)>_Q
      = -accuracy + complexity
    """

    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.max_iterations = 100
        self.convergence_threshold = 1e-6

    def update_beliefs(self,
                      model: GenerativeModel,
                      current_belief: Belief,
                      observation: Dict[str, float]) -> Belief:
        """
        Update beliefs to minimize free energy given observation.

        Uses gradient descent on free energy.
        """
        new_belief = copy.deepcopy(current_belief)
        new_belief.belief_id = ""
        new_belief.timestamp = time.time()

        # Initialize state means if needed
        for state in model.hidden_states:
            if state not in new_belief.state_means:
                new_belief.state_means[state] = model.prior_mean.get(state, 0.0)
            if state not in new_belief.state_precisions:
                new_belief.state_precisions[state] = model.prior_precision.get(state, 1.0)

        # Gradient descent on free energy
        prev_fe = float('inf')

        for iteration in range(self.max_iterations):
            # Compute prediction errors
            sensory_error = self._compute_sensory_error(model, new_belief, observation)

            # Compute free energy components
            accuracy = self._compute_accuracy(model, new_belief, observation)
            complexity = self._compute_complexity(model, new_belief)

            new_belief.accuracy = accuracy
            new_belief.complexity = complexity
            new_belief.sensory_prediction_error = sensory_error

            fe = new_belief.free_energy

            # Check convergence
            if abs(fe - prev_fe) < self.convergence_threshold:
                break
            prev_fe = fe

            # Compute gradients and update
            for state in model.hidden_states:
                grad = self._compute_state_gradient(model, new_belief, observation, state)
                new_belief.state_means[state] -= self.learning_rate * grad

        return new_belief

    def _compute_sensory_error(self,
                               model: GenerativeModel,
                               belief: Belief,
                               observation: Dict[str, float]) -> float:
        """Compute sensory prediction error"""
        total_error = 0.0

        for obs_type, obs_value in observation.items():
            # Get predicted observation from belief
            predicted = 0.0
            for state, mean in belief.state_means.items():
                weight = model.likelihood_weights.get(obs_type, {}).get(state, 0.0)
                predicted += weight * mean

            error = obs_value - predicted
            precision = 1.0 / (model.observation_noise.get(obs_type, 1.0) ** 2)
            total_error += precision * error ** 2

        return math.sqrt(total_error)

    def _compute_accuracy(self,
                         model: GenerativeModel,
                         belief: Belief,
                         observation: Dict[str, float]) -> float:
        """Compute log-likelihood of observations given beliefs"""
        log_lik = 0.0

        for obs_type, obs_value in observation.items():
            # Predicted mean
            predicted = 0.0
            for state, mean in belief.state_means.items():
                weight = model.likelihood_weights.get(obs_type, {}).get(state, 0.0)
                predicted += weight * mean

            # Gaussian likelihood
            noise = model.observation_noise.get(obs_type, 1.0)
            log_lik += -0.5 * ((obs_value - predicted) / noise) ** 2 - math.log(noise)

        return log_lik

    def _compute_complexity(self,
                           model: GenerativeModel,
                           belief: Belief) -> float:
        """Compute KL divergence from prior"""
        kl = 0.0

        for state in model.hidden_states:
            q_mean = belief.state_means.get(state, 0.0)
            q_prec = belief.state_precisions.get(state, 1.0)
            p_mean = model.prior_mean.get(state, 0.0)
            p_prec = model.prior_precision.get(state, 1.0)

            # KL for Gaussians
            q_var = 1.0 / q_prec
            p_var = 1.0 / p_prec

            kl += 0.5 * (
                math.log(p_var / q_var) +
                q_var / p_var +
                (q_mean - p_mean) ** 2 / p_var - 1
            )

        return kl

    def _compute_state_gradient(self,
                               model: GenerativeModel,
                               belief: Belief,
                               observation: Dict[str, float],
                               state: str) -> float:
        """Compute gradient of free energy w.r.t. state mean"""
        # Gradient from accuracy term
        grad_accuracy = 0.0
        for obs_type, obs_value in observation.items():
            predicted = 0.0
            for s, mean in belief.state_means.items():
                weight = model.likelihood_weights.get(obs_type, {}).get(s, 0.0)
                predicted += weight * mean

            weight = model.likelihood_weights.get(obs_type, {}).get(state, 0.0)
            noise = model.observation_noise.get(obs_type, 1.0)
            grad_accuracy += weight * (predicted - obs_value) / (noise ** 2)

        # Gradient from complexity term (KL from prior)
        q_mean = belief.state_means.get(state, 0.0)
        p_mean = model.prior_mean.get(state, 0.0)
        p_prec = model.prior_precision.get(state, 1.0)
        grad_complexity = p_prec * (q_mean - p_mean)

        return -grad_accuracy + grad_complexity


class PredictiveCoder:
    """
    Implements predictive coding for hierarchical inference.

    Each level predicts the level below, and prediction errors
    propagate upward to update beliefs.
    """

    def __init__(self):
        self.error_threshold = 2.0  # Std devs for anomaly

    def generate_predictions(self,
                            model: GenerativeModel,
                            belief: Belief,
                            time_horizon: float = 0.0) -> List[Prediction]:
        """Generate predictions from current beliefs"""
        predictions = []

        # Sensory predictions
        for obs_type in model.observation_types:
            predicted_value = 0.0
            predicted_var = model.observation_noise.get(obs_type, 1.0) ** 2

            for state, mean in belief.state_means.items():
                weight = model.likelihood_weights.get(obs_type, {}).get(state, 0.0)
                predicted_value += weight * mean

                # Propagate state uncertainty
                state_var = 1.0 / belief.state_precisions.get(state, 1.0)
                predicted_var += (weight ** 2) * state_var

            predictions.append(Prediction(
                prediction_id="",
                prediction_type=PredictionType.SENSORY,
                predicted_value={obs_type: predicted_value},
                predicted_precision={obs_type: 1.0 / predicted_var},
                time_horizon=time_horizon
            ))

        return predictions

    def compute_prediction_errors(self,
                                  predictions: List[Prediction],
                                  observations: Dict[str, float]) -> List[PredictionError]:
        """Compute prediction errors from observations"""
        errors = []

        for pred in predictions:
            if pred.prediction_type == PredictionType.SENSORY:
                for obs_type, pred_value in pred.predicted_value.items():
                    if obs_type in observations:
                        obs_value = observations[obs_type]
                        precision = pred.predicted_precision.get(obs_type, 1.0)

                        error_mag = abs(obs_value - pred_value)
                        precision_weighted = error_mag * math.sqrt(precision)

                        is_anomaly = precision_weighted > self.error_threshold

                        errors.append(PredictionError(
                            error_id="",
                            error_type="sensory",
                            error_magnitude=error_mag,
                            error_direction={obs_type: obs_value - pred_value},
                            predicted={obs_type: pred_value},
                            observed={obs_type: obs_value},
                            precision_weighted=precision_weighted,
                            is_anomaly=is_anomaly
                        ))

        return errors

    def detect_anomalies(self,
                        errors: List[PredictionError]) -> List[PredictionError]:
        """Filter for anomalous prediction errors"""
        return [e for e in errors if e.is_anomaly]


class ActionSelector:
    """
    Selects actions to minimize expected free energy.

    Expected free energy = Expected complexity - Expected accuracy
                        = Risk + Ambiguity
    """

    def __init__(self):
        self.planning_horizon = 5
        self.num_action_samples = 10

    def select_action(self,
                     model: GenerativeModel,
                     belief: Belief,
                     available_actions: List[Action]) -> Action:
        """Select action that minimizes expected free energy"""
        if not available_actions:
            return self._default_action()

        best_action = None
        best_efe = float('inf')

        for action in available_actions:
            efe = self._compute_expected_free_energy(model, belief, action)
            action.expected_free_energy = efe

            if efe < best_efe:
                best_efe = efe
                best_action = action

        return best_action if best_action else available_actions[0]

    def _compute_expected_free_energy(self,
                                      model: GenerativeModel,
                                      belief: Belief,
                                      action: Action) -> float:
        """
        Compute expected free energy for an action.

        G = E_Q[log Q(s') - log P(o',s')]
          = Risk (expected divergence from preferences)
          + Ambiguity (expected uncertainty about observations)
        """
        # Predict state after action
        predicted_state = self._predict_state(model, belief, action)

        # Risk: KL from preferred states (assume preferences = priors for now)
        risk = 0.0
        for state in model.hidden_states:
            q_mean = predicted_state.get(state, 0.0)
            p_mean = model.prior_mean.get(state, 0.0)
            p_prec = model.prior_precision.get(state, 1.0)

            risk += 0.5 * p_prec * (q_mean - p_mean) ** 2

        # Ambiguity: expected entropy of observations
        ambiguity = 0.0
        for obs_type in model.observation_types:
            # Observation variance given predicted state
            obs_var = model.observation_noise.get(obs_type, 1.0) ** 2

            # Add state uncertainty contribution
            for state, prec in belief.state_precisions.items():
                weight = model.likelihood_weights.get(obs_type, {}).get(state, 0.0)
                obs_var += (weight ** 2) / prec

            # Entropy of Gaussian
            ambiguity += 0.5 * math.log(2 * math.pi * math.e * obs_var)

        # Expected information gain (negative, as we want to maximize it)
        info_gain = self._estimate_information_gain(model, belief, action)
        action.expected_information_gain = info_gain

        return risk + ambiguity - info_gain

    def _predict_state(self,
                      model: GenerativeModel,
                      belief: Belief,
                      action: Action) -> Dict[str, float]:
        """Predict state after action using transition model"""
        predicted = {}

        for state in model.hidden_states:
            current = belief.state_means.get(state, 0.0)

            # Apply transition (simplified linear transition)
            trans_key = f"{state}_{action.action_type.value}"
            trans_effect = model.transition_matrices.get(trans_key, {}).get(state, 0.0)

            predicted[state] = current + trans_effect

        return predicted

    def _estimate_information_gain(self,
                                  model: GenerativeModel,
                                  belief: Belief,
                                  action: Action) -> float:
        """Estimate expected information gain from action"""
        # Information gain ≈ reduction in entropy of beliefs

        # Current entropy (approximate as sum of state entropies)
        current_entropy = 0.0
        for state, prec in belief.state_precisions.items():
            current_entropy += 0.5 * math.log(2 * math.pi * math.e / prec)

        # Expected posterior entropy after observation
        # Assumes observation reduces uncertainty
        expected_entropy = 0.0
        for state in model.hidden_states:
            current_prec = belief.state_precisions.get(state, 1.0)

            # Observation provides additional precision
            obs_precision_gain = 0.0
            for obs_type in model.observation_types:
                weight = model.likelihood_weights.get(obs_type, {}).get(state, 0.0)
                obs_noise = model.observation_noise.get(obs_type, 1.0)
                obs_precision_gain += (weight ** 2) / (obs_noise ** 2)

            expected_prec = current_prec + obs_precision_gain
            expected_entropy += 0.5 * math.log(2 * math.pi * math.e / expected_prec)

        return current_entropy - expected_entropy

    def _default_action(self) -> Action:
        """Return a default observation action"""
        return Action(
            action_id="",
            action_type=ActionType.OBSERVE,
            target="default"
        )


class ActiveInferenceAgent:
    """
    Main active inference agent for STAN.

    Implements the perception-action loop:
    1. Generate predictions from generative model
    2. Receive observations
    3. Compute prediction errors
    4. Update beliefs to minimize free energy
    5. Select actions to minimize expected free energy
    6. Execute actions
    """

    def __init__(self, model: Optional[GenerativeModel] = None):
        self.model = model or self._create_default_model()

        # Components
        self.free_energy_minimizer = FreeEnergyMinimizer()
        self.predictive_coder = PredictiveCoder()
        self.action_selector = ActionSelector()

        # State
        self.state = ActiveInferenceState(
            state_id="",
            model=self.model,
            current_belief=Belief(belief_id="")
        )

        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def perceive(self, observation: Dict[str, float]) -> Belief:
        """
        Process an observation and update beliefs.

        Returns updated belief state.
        """
        # Generate predictions before observation
        predictions = self.predictive_coder.generate_predictions(
            self.model, self.state.current_belief
        )
        self.state.active_predictions = predictions

        # Compute prediction errors
        errors = self.predictive_coder.compute_prediction_errors(
            predictions, observation
        )
        self.state.prediction_errors.extend(errors)

        # Check for anomalies
        anomalies = self.predictive_coder.detect_anomalies(errors)
        if anomalies:
            self.state.anomaly_count += len(anomalies)
            self._emit("anomaly_detected", {
                "count": len(anomalies),
                "errors": [e.error_magnitude for e in anomalies]
            })

        # Update beliefs to minimize free energy
        new_belief = self.free_energy_minimizer.update_beliefs(
            self.model, self.state.current_belief, observation
        )

        # Update state
        self.state.belief_history.append(self.state.current_belief)
        self.state.current_belief = new_belief
        self.state.total_free_energy = new_belief.free_energy
        self.state.cumulative_surprise += new_belief.sensory_prediction_error

        self._emit("belief_updated", {
            "free_energy": new_belief.free_energy,
            "prediction_error": new_belief.sensory_prediction_error
        })

        return new_belief

    def act(self, available_actions: Optional[List[Action]] = None) -> Action:
        """
        Select and return the best action.

        Action is selected to minimize expected free energy.
        """
        if available_actions is None:
            available_actions = self._generate_default_actions()

        selected_action = self.action_selector.select_action(
            self.model, self.state.current_belief, available_actions
        )

        self.state.planned_actions.append(selected_action)

        self._emit("action_selected", {
            "action_type": selected_action.action_type.value,
            "expected_info_gain": selected_action.expected_information_gain,
            "expected_free_energy": selected_action.expected_free_energy
        })

        return selected_action

    def execute_action(self, action: Action, outcome: Dict[str, Any]):
        """Record the outcome of an executed action"""
        action.executed = True
        action.actual_outcome = outcome
        self.state.executed_actions.append(action)

        # If outcome includes observation, process it
        if "observation" in outcome:
            self.perceive(outcome["observation"])

    def plan_observations(self,
                         observation_options: List[Dict[str, Any]],
                         budget: int = 5) -> List[Action]:
        """
        Plan a sequence of observations to maximize information gain.

        Args:
            observation_options: List of possible observations with costs
            budget: Maximum number of observations

        Returns:
            Ordered list of recommended observations
        """
        planned = []
        remaining_budget = budget

        # Greedy selection by information gain
        available = list(observation_options)

        while remaining_budget > 0 and available:
            best_action = None
            best_gain = -float('inf')

            for option in available:
                # Create action for this option
                action = Action(
                    action_id="",
                    action_type=ActionType.OBSERVE,
                    target=option.get("target", ""),
                    parameters=option
                )

                # Estimate information gain
                gain = self.action_selector._estimate_information_gain(
                    self.model, self.state.current_belief, action
                )
                action.expected_information_gain = gain

                cost = option.get("cost", 1)
                if cost <= remaining_budget and gain > best_gain:
                    best_gain = gain
                    best_action = action

            if best_action:
                planned.append(best_action)
                remaining_budget -= best_action.parameters.get("cost", 1)

                # Remove from available
                available = [o for o in available
                           if o.get("target") != best_action.target]
            else:
                break

        return planned

    def get_anomalies(self) -> List[PredictionError]:
        """Get all detected anomalies"""
        return [e for e in self.state.prediction_errors if e.is_anomaly]

    def get_state_estimate(self) -> Dict[str, Tuple[float, float]]:
        """Get current state estimates with uncertainties"""
        estimates = {}
        belief = self.state.current_belief

        for state in self.model.hidden_states:
            mean = belief.state_means.get(state, 0.0)
            precision = belief.state_precisions.get(state, 1.0)
            std = 1.0 / math.sqrt(precision)
            estimates[state] = (mean, std)

        return estimates

    def get_predictions(self) -> List[Prediction]:
        """Get current active predictions"""
        return self.predictive_coder.generate_predictions(
            self.model, self.state.current_belief
        )

    def update_model(self,
                    new_likelihood_weights: Optional[Dict] = None,
                    new_priors: Optional[Dict] = None):
        """Update the generative model"""
        if new_likelihood_weights:
            self.model.likelihood_weights.update(new_likelihood_weights)
        if new_priors:
            self.model.prior_mean.update(new_priors.get("mean", {}))
            self.model.prior_precision.update(new_priors.get("precision", {}))

    def reset(self):
        """Reset agent state"""
        self.state = ActiveInferenceState(
            state_id="",
            model=self.model,
            current_belief=Belief(belief_id="")
        )

    def on(self, event: str, callback: Callable):
        """Register event callback"""
