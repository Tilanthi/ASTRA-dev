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
Active Experiment Design: Information-Theoretic Experiment Selection

This module implements optimal experiment selection based on expected
information gain - choosing experiments that maximally reduce uncertainty.

Key Features:
- Information gain computation using entropy reduction
- Sequential experiment design with belief updating
- Integration with Bayesian inference for uncertainty quantification
- Support for intervention design (causal experiments)

Why This Matters for AGI:
- Enables autonomous scientific discovery
- Efficient hypothesis discrimination
- Resource-optimal learning

Date: 2025-12-10
Version: 39.0
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import hashlib
from scipy import stats


class ExperimentType(Enum):
    """Types of experiments"""
    OBSERVATION = "observation"      # Passive observation
    INTERVENTION = "intervention"    # Active manipulation
    COMPARISON = "comparison"        # A/B comparison
    SEQUENTIAL = "sequential"        # Multi-step experiment


class OutcomeSpace(Enum):
    """Types of outcome spaces"""
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"
    BINARY = "binary"
    CATEGORICAL = "categorical"


@dataclass
class Experiment:
    """An experiment that can be performed"""
    experiment_id: str
    experiment_type: ExperimentType
    description: str

    # Design
    variables: List[str]          # Variables to measure/manipulate
    interventions: Dict[str, Any]  # For intervention experiments
    conditions: Dict[str, Any]     # Experimental conditions

    # Costs
    cost: float = 1.0             # Resource cost
    time_required: float = 1.0     # Time cost
    difficulty: float = 0.5        # Implementation difficulty

    # Outcome specification
    outcome_space: OutcomeSpace = OutcomeSpace.CONTINUOUS
    possible_outcomes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'experiment_id': self.experiment_id,
            'type': self.experiment_type.value,
            'description': self.description,
            'variables': self.variables,
            'interventions': self.interventions,
            'conditions': self.conditions,
            'cost': self.cost,
            'outcome_space': self.outcome_space.value
        }


@dataclass
class ExperimentResult:
    """Result of an experiment"""
    experiment: Experiment
    outcome: Any
    observed_values: Dict[str, float]
    uncertainty: Dict[str, float]
    timestamp: float = 0.0

    # Analysis
    information_gained: float = 0.0
    hypotheses_eliminated: List[str] = field(default_factory=list)
    hypotheses_supported: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'experiment_id': self.experiment.experiment_id,
            'outcome': self.outcome,
            'observed_values': self.observed_values,
            'uncertainty': self.uncertainty,
            'information_gained': self.information_gained,
            'hypotheses_eliminated': self.hypotheses_eliminated,
            'hypotheses_supported': self.hypotheses_supported
        }


@dataclass
class BeliefDistribution:
    """Probability distribution over hypotheses"""
    hypotheses: List[str]
    probabilities: np.ndarray
    entropy: float = 0.0

    def __post_init__(self):
        # Normalize
        self.probabilities = np.array(self.probabilities)
        self.probabilities = self.probabilities / self.probabilities.sum()
        self.entropy = self._compute_entropy()

    def _compute_entropy(self) -> float:
        """Compute Shannon entropy"""
        # Filter out zero probabilities
        p = self.probabilities[self.probabilities > 0]
        return -np.sum(p * np.log2(p))

    def update(self, likelihood: np.ndarray) -> 'BeliefDistribution':
        """Bayesian update with likelihood"""
        posterior = self.probabilities * likelihood
        posterior = posterior / posterior.sum()
        return BeliefDistribution(self.hypotheses, posterior)

    def to_dict(self) -> Dict:
        return {
            'hypotheses': self.hypotheses,
            'probabilities': self.probabilities.tolist(),
            'entropy': self.entropy
        }


class InformationGainEstimator:
    """Estimate information gain for experiments"""

    def __init__(self):
        self.outcome_models: Dict[str, Callable] = {}

    def register_outcome_model(self, experiment_type: str,
                               model: Callable[[Any, Any], np.ndarray]):
        """
        Register outcome model for experiment type.

        Args:
            experiment_type: Type of experiment
            model: Function(hypothesis, experiment) -> outcome_probability
        """
        self.outcome_models[experiment_type] = model

    def compute_expected_information_gain(self,
                                          experiment: Experiment,
                                          belief: BeliefDistribution,
                                          n_samples: int = 100) -> float:
        """
        Compute expected information gain for an experiment.

        Uses the formula:
        E[IG] = H(prior) - E[H(posterior)]

        Where the expectation is over possible outcomes.
        """
        prior_entropy = belief.entropy

        # Get outcome model
        outcome_model = self.outcome_models.get(
            experiment.experiment_type.value,
            self._default_outcome_model
        )

        # Sample possible outcomes and compute expected posterior entropy
        expected_posterior_entropy = 0.0

        if experiment.outcome_space == OutcomeSpace.BINARY:
            outcomes = [0, 1]
        elif experiment.outcome_space == OutcomeSpace.DISCRETE:
            outcomes = list(range(len(experiment.possible_outcomes)))
        else:
            outcomes = np.linspace(-3, 3, n_samples)  # Standardized continuous

        for outcome in outcomes:
            # Compute likelihood for each hypothesis given this outcome
            likelihoods = np.array([
                self._likelihood(outcome_model, h, experiment, outcome)
                for h in belief.hypotheses
            ])

            # Compute outcome probability (marginal)
            outcome_prob = np.sum(belief.probabilities * likelihoods)

            if outcome_prob > 1e-10:
                # Compute posterior
                posterior = belief.update(likelihoods)

                # Weight posterior entropy by outcome probability
                expected_posterior_entropy += outcome_prob * posterior.entropy

        # Expected information gain
        eig = prior_entropy - expected_posterior_entropy
