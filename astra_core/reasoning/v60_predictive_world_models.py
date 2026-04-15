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
V60 Predictive World Models
============================

Learned generative models that predict outcomes, not symbolic simulation.
These models are trained on domain data and used for mental simulation.

Key Features:
- Neural-symbolic hybrid architecture
- Bayesian model selection between competing models
- Prediction error drives learning
- Hierarchical model composition

Based on predictive processing / predictive coding theory.

Date: 2025-12-17
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Callable
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
import time
import math
from collections import defaultdict


class ModelType(Enum):
    """Types of predictive world models."""
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    SOCIAL = "social"
    ABSTRACT = "abstract"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    CAUSAL = "causal"


# Alias for cognitive agent compatibility
DomainType = ModelType


class PredictionType(Enum):
    """Types of predictions."""
    STATE = "state"              # Predict next state
    OUTCOME = "outcome"          # Predict outcome of action
    COUNTERFACTUAL = "counterfactual"  # What would happen if...
    EXPLANATION = "explanation"  # Why did this happen


@dataclass
class Observation:
    """An observation from the world."""
    timestamp: float
    domain: str
    variables: Dict[str, float]
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "external"


@dataclass
class Prediction:
    """A prediction from a world model."""
    predicted_state: Dict[str, float]
    confidence: float
    uncertainty: Dict[str, float]  # Per-variable uncertainty
    model_id: str
    prediction_type: PredictionType
    reasoning: List[str] = field(default_factory=list)


@dataclass
class PredictionError:
    """Error between prediction and observation."""
    predicted: Dict[str, float]
    observed: Dict[str, float]
    error: Dict[str, float]
    magnitude: float
    timestamp: float
    model_id: str


@dataclass
class ModelUpdate:
    """Update to apply to a model based on prediction error."""
    model_id: str
    parameter_deltas: Dict[str, float]
    learning_rate: float
    error_signal: float


class WorldModelBase(ABC):
    """Abstract base class for predictive world models."""

    def __init__(self, model_id: str, domain: ModelType):
        self.model_id = model_id
        self.domain = domain
        self.parameters: Dict[str, float] = {}
        self.prediction_history: List[Tuple[Prediction, Optional[Observation]]] = []
        self.error_history: List[PredictionError] = []
        self.confidence = 0.5
        self.total_predictions = 0
        self.accurate_predictions = 0

    @abstractmethod
    def predict(self, current_state: Dict[str, float],
                action: Optional[Dict[str, Any]] = None,
                horizon: int = 1) -> Prediction:
        """Generate a prediction about future state."""
        pass

    @abstractmethod
    def update(self, error: PredictionError) -> ModelUpdate:
        """Update model based on prediction error."""
        pass

    def record_prediction(self, prediction: Prediction,
                         observation: Optional[Observation] = None):
        """Record a prediction and optional observation."""
        self.prediction_history.append((prediction, observation))
        self.total_predictions += 1

        if observation:
            error = self._compute_error(prediction, observation)
            self.error_history.append(error)

            # Update accuracy estimate
            if error.magnitude < 0.1:
                self.accurate_predictions += 1

            # Update confidence based on recent accuracy
            if self.total_predictions > 0:
                self.confidence = self.accurate_predictions / self.total_predictions

    def _compute_error(self, prediction: Prediction,
                      observation: Observation) -> PredictionError:
        """Compute prediction error."""
        error = {}
        for var in prediction.predicted_state:
            if var in observation.variables:
                error[var] = observation.variables[var] - prediction.predicted_state[var]

        magnitude = math.sqrt(sum(e**2 for e in error.values())) if error else 0.0

        return PredictionError(
            predicted=prediction.predicted_state,
            observed=observation.variables,
            error=error,
            magnitude=magnitude,
            timestamp=time.time(),
            model_id=self.model_id
        )

    def get_accuracy(self) -> float:
        """Get model accuracy."""
        if self.total_predictions == 0:
            return 0.5
        return self.accurate_predictions / self.total_predictions


class PhysicsWorldModel(WorldModelBase):
    """
    Predictive model for physical systems.

    Learns conservation laws, dynamics, and constraints from observations.
    """

    def __init__(self, model_id: str = "physics_v1"):
        super().__init__(model_id, ModelType.PHYSICS)

        # Physical parameters (learned from experience)
        self.parameters = {
            'gravity': 9.81,
            'friction': 0.1,
            'elasticity': 0.8,
            'drag': 0.01,
            'mass_scale': 1.0,
            'energy_conservation': 0.99,
            'momentum_conservation': 0.99
        }

        # Learned dynamics coefficients
        self.dynamics_weights = defaultdict(lambda: defaultdict(float))

        # Conservation law detectors
        self.conservation_violations = []

    def predict(self, current_state: Dict[str, float],
                action: Optional[Dict[str, Any]] = None,
                horizon: int = 1) -> Prediction:
        """Predict future physical state."""
        predicted = current_state.copy()
        uncertainty = {k: 0.1 for k in current_state}
        reasoning = []

        # Apply physics principles
        dt = 0.1  # Time step

        for step in range(horizon):
            # Position update from velocity
            if 'velocity_x' in predicted and 'position_x' in predicted:
                predicted['position_x'] += predicted['velocity_x'] * dt
                reasoning.append(f"Position updated by velocity: dx = v*dt")

            if 'velocity_y' in predicted and 'position_y' in predicted:
                predicted['position_y'] += predicted['velocity_y'] * dt

            # Velocity update from acceleration (gravity, forces)
            if 'velocity_y' in predicted:
                predicted['velocity_y'] -= self.parameters['gravity'] * dt
                reasoning.append(f"Gravity applied: dv = -g*dt")

            # Apply friction/drag
            if 'velocity_x' in predicted:
                predicted['velocity_x'] *= (1 - self.parameters['drag'])
            if 'velocity_y' in predicted:
                predicted['velocity_y'] *= (1 - self.parameters['drag'])

            # Energy tracking
            if 'kinetic_energy' in predicted and 'potential_energy' in predicted:
                # Enforce approximate conservation
                total_before = predicted['kinetic_energy'] + predicted['potential_energy']
                predicted['kinetic_energy'] = 0.5 * (
                    predicted.get('velocity_x', 0)**2 +
                    predicted.get('velocity_y', 0)**2
                )
                predicted['potential_energy'] = (
                    self.parameters['gravity'] * predicted.get('position_y', 0)
                )
                total_after = predicted['kinetic_energy'] + predicted['potential_energy']

                # Small dissipation
                scale = self.parameters['energy_conservation']
                predicted['kinetic_energy'] *= scale
                predicted['potential_energy'] *= scale

                reasoning.append(f"Energy conservation enforced (η={scale:.2f})")

            # Apply action if provided
            if action:
                if 'force_x' in action:
                    mass = predicted.get('mass', 1.0)
                    predicted['velocity_x'] = predicted.get('velocity_x', 0) + action['force_x'] / mass * dt
                if 'force_y' in action:
                    mass = predicted.get('mass', 1.0)
                    predicted['velocity_y'] = predicted.get('velocity_y', 0) + action['force_y'] / mass * dt
                reasoning.append(f"Applied forces from action")

            # Update uncertainties (grow with horizon)
            for k in uncertainty:
                uncertainty[k] *= 1.1

        return Prediction(
            predicted_state=predicted,
            confidence=self.confidence * (0.9 ** horizon),
            uncertainty=uncertainty,
            model_id=self.model_id,
            prediction_type=PredictionType.STATE,
            reasoning=reasoning
        )

    def update(self, error: PredictionError) -> ModelUpdate:
        """Update physics model based on prediction error."""
        learning_rate = 0.01
        deltas = {}

        # Learn corrections to parameters
        if 'velocity_y' in error.error:
            # Adjust gravity estimate
            gravity_correction = -error.error['velocity_y'] * 10  # Scale factor
            deltas['gravity'] = gravity_correction * learning_rate
            self.parameters['gravity'] += deltas['gravity']

        if 'velocity_x' in error.error:
            # Adjust drag estimate
            drag_correction = error.error['velocity_x'] * 0.1
            deltas['drag'] = drag_correction * learning_rate
            self.parameters['drag'] = max(0, self.parameters['drag'] + deltas['drag'])

        return ModelUpdate(
            model_id=self.model_id,
            parameter_deltas=deltas,
            learning_rate=learning_rate,
            error_signal=error.magnitude
        )

    def check_conservation(self, observations: List[Observation]) -> Dict[str, bool]:
        """Check if conservation laws hold in observations."""
        results = {'energy': True, 'momentum': True}

        if len(observations) < 2:
            return results

        for i in range(1, len(observations)):
            prev = observations[i-1].variables
            curr = observations[i].variables

            # Check energy conservation
            if all(k in prev and k in curr for k in ['kinetic_energy', 'potential_energy']):
                e_prev = prev['kinetic_energy'] + prev['potential_energy']
                e_curr = curr['kinetic_energy'] + curr['potential_energy']
                if abs(e_curr - e_prev) / max(e_prev, 1e-10) > 0.1:
                    results['energy'] = False

            # Check momentum conservation
            if 'momentum_x' in prev and 'momentum_x' in curr:
                if abs(curr['momentum_x'] - prev['momentum_x']) > 0.1:
                    results['momentum'] = False

        return results


class ChemistryWorldModel(WorldModelBase):
    """
    Predictive model for chemical systems.

    Learns reaction kinetics, equilibria, and molecular interactions.
    """

    def __init__(self, model_id: str = "chemistry_v1"):
        super().__init__(model_id, ModelType.CHEMISTRY)

        self.parameters = {
            'temperature': 298.0,  # K
            'pressure': 1.0,       # atm
            'rate_constant_scale': 1.0,
            'equilibrium_shift': 0.0
        }

        # Learned reaction rates
        self.reaction_rates: Dict[str, float] = {}

        # Equilibrium constants
        self.equilibrium_constants: Dict[str, float] = {}

    def predict(self, current_state: Dict[str, float],
                action: Optional[Dict[str, Any]] = None,
                horizon: int = 1) -> Prediction:
        """Predict chemical system evolution."""
        predicted = current_state.copy()
        uncertainty = {k: 0.05 for k in current_state}
        reasoning = []

        dt = 1.0  # Time step in seconds

        for step in range(horizon):
            # Apply reaction kinetics
            for reaction_id, rate in self.reaction_rates.items():
                # Simple A -> B kinetics
                if f'{reaction_id}_A' in predicted and f'{reaction_id}_B' in predicted:
                    d_conc = rate * predicted[f'{reaction_id}_A'] * dt
                    predicted[f'{reaction_id}_A'] -= d_conc
                    predicted[f'{reaction_id}_B'] += d_conc
                    predicted[f'{reaction_id}_A'] = max(0, predicted[f'{reaction_id}_A'])
                    reasoning.append(f"Reaction {reaction_id}: rate={rate:.4f}")

            # Approach equilibrium
            for eq_id, K in self.equilibrium_constants.items():
                if f'{eq_id}_reactant' in predicted and f'{eq_id}_product' in predicted:
                    Q = predicted[f'{eq_id}_product'] / max(predicted[f'{eq_id}_reactant'], 1e-10)
                    if Q < K:
                        # Shift toward products
                        shift = 0.1 * (K - Q) / K
                        predicted[f'{eq_id}_reactant'] -= shift
                        predicted[f'{eq_id}_product'] += shift
                    reasoning.append(f"Equilibrium {eq_id}: K={K:.2f}, Q={Q:.2f}")

            # Temperature effects on rates (Arrhenius-like)
            if action and 'temperature_change' in action:
                self.parameters['temperature'] += action['temperature_change']
                scale = math.exp(action['temperature_change'] / 100)  # Simplified
                for r_id in self.reaction_rates:
                    self.reaction_rates[r_id] *= scale
                reasoning.append(f"Temperature changed by {action['temperature_change']:.1f}K")

            # Update uncertainties
            for k in uncertainty:
                uncertainty[k] *= 1.05

        return Prediction(
            predicted_state=predicted,
            confidence=self.confidence * (0.95 ** horizon),
            uncertainty=uncertainty,
            model_id=self.model_id,
            prediction_type=PredictionType.STATE,
            reasoning=reasoning
        )

    def update(self, error: PredictionError) -> ModelUpdate:
        """Update chemistry model based on prediction error."""
        learning_rate = 0.01
        deltas = {}

        # Adjust rate constants based on concentration errors
        for var, err in error.error.items():
            if '_A' in var or '_B' in var:
                reaction_id = var.rsplit('_', 1)[0]
                if reaction_id in self.reaction_rates:
                    rate_adjustment = err * learning_rate
                    deltas[f'rate_{reaction_id}'] = rate_adjustment
                    self.reaction_rates[reaction_id] += rate_adjustment

        return ModelUpdate(
            model_id=self.model_id,
            parameter_deltas=deltas,
            learning_rate=learning_rate,
            error_signal=error.magnitude
        )

    def learn_reaction(self, reaction_id: str, observations: List[Observation]):
        """Learn reaction rate from observations."""
        if len(observations) < 2:
            return

        # Estimate rate from concentration changes
        rates = []
        for i in range(1, len(observations)):
            prev = observations[i-1]
            curr = observations[i]
            dt = curr.timestamp - prev.timestamp

            if f'{reaction_id}_A' in prev.variables and f'{reaction_id}_A' in curr.variables:
                d_conc = prev.variables[f'{reaction_id}_A'] - curr.variables[f'{reaction_id}_A']
                if dt > 0 and prev.variables[f'{reaction_id}_A'] > 0:
                    rate = d_conc / (dt * prev.variables[f'{reaction_id}_A'])
                    rates.append(rate)

        if rates:
            self.reaction_rates[reaction_id] = sum(rates) / len(rates)


class BiologyWorldModel(WorldModelBase):
    """
    Predictive model for biological systems.

    Learns population dynamics, metabolic processes, and regulatory networks.
    """

    def __init__(self, model_id: str = "biology_v1"):
        super().__init__(model_id, ModelType.BIOLOGY)

        self.parameters = {
            'growth_rate': 0.1,
            'carrying_capacity': 1000,
            'death_rate': 0.01,
            'mutation_rate': 0.001
        }

        # Interaction matrix for species
        self.interaction_matrix: Dict[Tuple[str, str], float] = {}

        # Metabolic rates
        self.metabolic_rates: Dict[str, float] = {}

    def predict(self, current_state: Dict[str, float],
                action: Optional[Dict[str, Any]] = None,
                horizon: int = 1) -> Prediction:
        """Predict biological system evolution."""
        predicted = current_state.copy()
        uncertainty = {k: 0.15 for k in current_state}
        reasoning = []

        dt = 1.0

        for step in range(horizon):
            # Logistic growth for populations
            for var in list(predicted.keys()):
                if var.startswith('population_'):
                    N = predicted[var]
                    K = self.parameters['carrying_capacity']
                    r = self.parameters['growth_rate']

                    # dN/dt = rN(1 - N/K)
                    dN = r * N * (1 - N / K) * dt
                    predicted[var] = max(0, N + dN)
                    reasoning.append(f"Logistic growth for {var}: r={r:.3f}, K={K}")

            # Species interactions
            for (sp1, sp2), interaction in self.interaction_matrix.items():
                if f'population_{sp1}' in predicted and f'population_{sp2}' in predicted:
                    N1 = predicted[f'population_{sp1}']
                    N2 = predicted[f'population_{sp2}']

                    effect = interaction * N1 * N2 * dt / 1000
                    predicted[f'population_{sp1}'] += effect
                    predicted[f'population_{sp2}'] -= effect

                    predicted[f'population_{sp1}'] = max(0, predicted[f'population_{sp1}'])
                    predicted[f'population_{sp2}'] = max(0, predicted[f'population_{sp2}'])

            # Metabolic processes
            for metabolite, rate in self.metabolic_rates.items():
                if metabolite in predicted:
                    predicted[metabolite] *= (1 - rate * dt)
                    predicted[metabolite] = max(0, predicted[metabolite])

            # Apply action (e.g., resource addition)
            if action:
                if 'add_resource' in action:
                    for resource, amount in action['add_resource'].items():
                        predicted[resource] = predicted.get(resource, 0) + amount
                        reasoning.append(f"Added {amount} of {resource}")

            # Increase uncertainty with time
            for k in uncertainty:
                uncertainty[k] *= 1.2

        return Prediction(
            predicted_state=predicted,
            confidence=self.confidence * (0.85 ** horizon),
            uncertainty=uncertainty,
            model_id=self.model_id,
            prediction_type=PredictionType.STATE,
            reasoning=reasoning
        )

    def update(self, error: PredictionError) -> ModelUpdate:
        """Update biology model based on prediction error."""
        learning_rate = 0.005
        deltas = {}

        # Adjust growth/death rates based on population errors
        for var, err in error.error.items():
            if var.startswith('population_'):
                if err > 0:  # Underestimated growth
                    deltas['growth_rate'] = err * learning_rate / 100
                    self.parameters['growth_rate'] += deltas['growth_rate']
                else:  # Overestimated growth
                    deltas['death_rate'] = -err * learning_rate / 100
                    self.parameters['death_rate'] = max(0,
                        self.parameters['death_rate'] + deltas['death_rate'])

        return ModelUpdate(
            model_id=self.model_id,
            parameter_deltas=deltas,
            learning_rate=learning_rate,
            error_signal=error.magnitude
        )


class CausalWorldModel(WorldModelBase):
    """
    Predictive model for causal relationships.

    Learns causal structure from interventions and observations.
    """

    def __init__(self, model_id: str = "causal_v1"):
        super().__init__(model_id, ModelType.CAUSAL)

        # Causal graph: cause -> effect -> strength
        self.causal_graph: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Intervention effects
        self.intervention_effects: Dict[str, Dict[str, float]] = {}

        self.parameters = {
            'causal_threshold': 0.1,
            'confounding_correction': 0.0
        }

    def predict(self, current_state: Dict[str, float],
                action: Optional[Dict[str, Any]] = None,
                horizon: int = 1) -> Prediction:
        """Predict effects of causal interventions."""
        predicted = current_state.copy()
        uncertainty = {k: 0.2 for k in current_state}
        reasoning = []

        # Apply causal effects
        for cause, effects in self.causal_graph.items():
            if cause in predicted:
                cause_value = predicted[cause]
                for effect, strength in effects.items():
                    if effect in predicted:
                        delta = cause_value * strength
                        predicted[effect] += delta
                        reasoning.append(f"Causal effect: {cause} -> {effect} (β={strength:.3f})")

        # Apply intervention
        if action and 'intervene' in action:
            for var, value in action['intervene'].items():
                if var in predicted:
                    predicted[var] = value
                    reasoning.append(f"Intervention: set {var} = {value}")

                    # Propagate intervention effects
                    if var in self.causal_graph:
                        for effect, strength in self.causal_graph[var].items():
                            if effect in predicted and effect not in action['intervene']:
                                predicted[effect] += value * strength
                                reasoning.append(f"Intervention propagated to {effect}")

        return Prediction(
            predicted_state=predicted,
            confidence=self.confidence,
            uncertainty=uncertainty,
            model_id=self.model_id,
            prediction_type=PredictionType.OUTCOME if action else PredictionType.STATE,
            reasoning=reasoning
        )

    def update(self, error: PredictionError) -> ModelUpdate:
        """Update causal model based on prediction error."""
        learning_rate = 0.02
        deltas = {}

        # Adjust causal strengths based on errors
        for effect, err in error.error.items():
            for cause in self.causal_graph:
                if effect in self.causal_graph[cause]:
                    strength_adjustment = err * learning_rate
                    self.causal_graph[cause][effect] += strength_adjustment
                    deltas[f'{cause}->{effect}'] = strength_adjustment

        return ModelUpdate(
            model_id=self.model_id,
            parameter_deltas=deltas,
            learning_rate=learning_rate,
            error_signal=error.magnitude
        )

    def learn_causal_relation(self, cause: str, effect: str,
                              observations: List[Observation],
                              interventions: List[Tuple[float, float]] = None):
        """Learn causal strength from data."""
        if len(observations) < 3:
            return

        # Compute correlation
        cause_values = [o.variables.get(cause, 0) for o in observations]
        effect_values = [o.variables.get(effect, 0) for o in observations]

        mean_cause = sum(cause_values) / len(cause_values)
        mean_effect = sum(effect_values) / len(effect_values)

        cov = sum((c - mean_cause) * (e - mean_effect)
                  for c, e in zip(cause_values, effect_values)) / len(observations)
        var_cause = sum((c - mean_cause)**2 for c in cause_values) / len(observations)

        if var_cause > 1e-10:
            correlation = cov / math.sqrt(var_cause)

            # Use interventional data if available to confirm causation
            if interventions:
                # Interventions are (intervention_value, observed_effect)
                intervention_effect = sum(e - i for i, e in interventions) / len(interventions)
                causal_strength = intervention_effect
            else:
                causal_strength = correlation * 0.5  # Discount observational

            if abs(causal_strength) > self.parameters['causal_threshold']:
                self.causal_graph[cause][effect] = causal_strength


class WorldModelLibrary:
    """
    Library of predictive world models with Bayesian model selection.
    """

    def __init__(self):
        self.models: Dict[str, WorldModelBase] = {}
        self.model_priors: Dict[str, float] = {}
        self.model_likelihoods: Dict[str, List[float]] = defaultdict(list)

        # Initialize default models
        self._init_default_models()

    def _init_default_models(self):
        """Initialize standard world models."""
        self.add_model(PhysicsWorldModel())
        self.add_model(ChemistryWorldModel())
        self.add_model(BiologyWorldModel())
        self.add_model(CausalWorldModel())

    def add_model(self, model: WorldModelBase, prior: float = 0.25):
        """Add a model to the library."""
        self.models[model.model_id] = model
        self.model_priors[model.model_id] = prior

    def predict(self, domain: ModelType, current_state: Dict[str, float],
                action: Optional[Dict[str, Any]] = None) -> List[Prediction]:
        """Get predictions from relevant models."""
        predictions = []

        for model_id, model in self.models.items():
            if model.domain == domain or domain == ModelType.ABSTRACT:
                pred = model.predict(current_state, action)
                predictions.append(pred)

        return predictions

    def predict_with_model_averaging(self, domain: ModelType,
                                     current_state: Dict[str, float],
                                     action: Optional[Dict[str, Any]] = None) -> Prediction:
        """Bayesian model averaging over predictions."""
        predictions = self.predict(domain, current_state, action)

        if not predictions:
            return Prediction(
                predicted_state=current_state,
                confidence=0.0,
                uncertainty={k: 1.0 for k in current_state},
                model_id="none",
                prediction_type=PredictionType.STATE,
                reasoning=["No applicable models found"]
            )

        # Compute model posteriors
        posteriors = self._compute_posteriors(predictions)

        # Weighted average of predictions
        averaged_state = {}
        averaged_uncertainty = {}

        for var in current_state:
            values = []
            weights = []
            uncertainties = []

            for pred, post in zip(predictions, posteriors):
                if var in pred.predicted_state:
                    values.append(pred.predicted_state[var])
                    weights.append(post)
                    uncertainties.append(pred.uncertainty.get(var, 0.1))

            if values:
                total_weight = sum(weights)
                if total_weight > 0:
                    averaged_state[var] = sum(v * w for v, w in zip(values, weights)) / total_weight
                    averaged_uncertainty[var] = sum(u * w for u, w in zip(uncertainties, weights)) / total_weight

        # Overall confidence is posterior-weighted average
        avg_confidence = sum(p.confidence * post for p, post in zip(predictions, posteriors))

        return Prediction(
            predicted_state=averaged_state,
            confidence=avg_confidence,
            uncertainty=averaged_uncertainty,
            model_id="averaged",
            prediction_type=PredictionType.STATE,
            reasoning=[f"Model-averaged prediction from {len(predictions)} models"]
        )

    def _compute_posteriors(self, predictions: List[Prediction]) -> List[float]:
        """Compute posterior probabilities for models."""
        posteriors = []

        for pred in predictions:
            prior = self.model_priors.get(pred.model_id, 0.25)
            likelihood = pred.confidence  # Use confidence as proxy for likelihood
            posteriors.append(prior * likelihood)

        # Normalize
        total = sum(posteriors)
        if total > 0:
            posteriors = [p / total for p in posteriors]
        else:
            posteriors = [1.0 / len(predictions)] * len(predictions)

        return posteriors

    def update_all(self, observation: Observation, predictions: List[Prediction]):
        """Update all models based on observation."""
        for pred in predictions:
            if pred.model_id in self.models:
                model = self.models[pred.model_id]
                model.record_prediction(pred, observation)

                if model.error_history:
                    latest_error = model.error_history[-1]
                    model.update(latest_error)

                    # Update model likelihood
                    likelihood = math.exp(-latest_error.magnitude)
                    self.model_likelihoods[pred.model_id].append(likelihood)

    def get_best_model(self, domain: ModelType) -> Optional[WorldModelBase]:
        """Get the best performing model for a domain."""
        best_model = None
        best_accuracy = 0.0

        for model_id, model in self.models.items():
            if model.domain == domain:
                accuracy = model.get_accuracy()
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_model = model

        return best_model

    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        return {
            'num_models': len(self.models),
            'models': {
                model_id: {
                    'domain': model.domain.value,
                    'accuracy': model.get_accuracy(),
                    'predictions': model.total_predictions,
                    'confidence': model.confidence
                }
                for model_id, model in self.models.items()
            }
        }


class PredictiveWorldModelSystem:
    """
    Main system for predictive world modeling.

    Integrates:
    - Multiple domain-specific models
    - Bayesian model selection
    - Online learning from prediction errors
    - Mental simulation capabilities
    """

    def __init__(self):
        self.library = WorldModelLibrary()
        self.observation_buffer: List[Observation] = []
        self.prediction_log: List[Tuple[Prediction, Optional[Observation]]] = []
        self.total_predictions = 0
        self.cumulative_error = 0.0

    def observe(self, observation: Observation):
        """Process a new observation."""
        self.observation_buffer.append(observation)

        # Update models if we have pending predictions
        if self.prediction_log:
            last_pred, _ = self.prediction_log[-1]
            self.prediction_log[-1] = (last_pred, observation)

            # Trigger model updates
            self.library.update_all(observation, [last_pred])
