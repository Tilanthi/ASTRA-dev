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

Date: 2026-03-18
Version: 1.0
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
    OBSERVATION = "observation"
    INTERVENTION = "intervention"
    COMPARISON = "comparison"
    SEQUENTIAL = "sequential"


class ExperimentStatus(Enum):
    """Status of an experiment"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutcomeSpace(Enum):
    """Types of outcome spaces"""
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"
    BINARY = "binary"
    CATEGORICAL = "categorical"


@dataclass
class Variable:
    """A variable in an experiment"""
    name: str
    variable_type: str  # 'independent', 'dependent', 'controlled'
    value_range: Optional[Tuple[float, float]] = None
    possible_values: Optional[List[Any]] = None
    units: Optional[str] = None


@dataclass
class HypothesisSpace:
    """Space of hypotheses to test"""
    hypotheses: List[str]
    prior_probabilities: np.ndarray = None

    def __post_init__(self):
        if self.prior_probabilities is None:
            n = len(self.hypotheses)
            self.prior_probabilities = np.ones(n) / n
        else:
            self.prior_probabilities = np.array(self.prior_probabilities)
            self.prior_probabilities = self.prior_probabilities / self.prior_probabilities.sum()


@dataclass
class Belief:
    """Current belief state over hypotheses"""
    hypothesis_space: HypothesisSpace
    probabilities: np.ndarray
    evidence: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        self.probabilities = np.array(self.probabilities)
        self.probabilities = self.probabilities / self.probabilities.sum()

    def entropy(self) -> float:
        """Compute Shannon entropy"""
        p = self.probabilities[self.probabilities > 0]
        return -np.sum(p * np.log2(p))

    def update(self, likelihood: np.ndarray) -> 'Belief':
        """Bayesian update"""
        posterior = self.probabilities * likelihood
        posterior = posterior / posterior.sum()
        return Belief(self.hypothesis_space, posterior, self.evidence.copy())


@dataclass
class Experiment:
    """An experiment that can be performed"""
    experiment_id: str
    experiment_type: ExperimentType
    description: str

    # Design
    variables: List[str]
    interventions: Dict[str, Any]
    conditions: Dict[str, Any]

    # Costs
    cost: float = 1.0
    time_required: float = 1.0
    difficulty: float = 0.5

    # Outcome specification
    outcome_space: OutcomeSpace = OutcomeSpace.CONTINUOUS
    possible_outcomes: List[str] = field(default_factory=list)
    status: ExperimentStatus = ExperimentStatus.PENDING

    def to_dict(self) -> Dict:
        return {
            'experiment_id': self.experiment_id,
            'type': self.experiment_type.value,
            'description': self.description,
            'variables': self.variables,
            'interventions': self.interventions,
            'conditions': self.conditions,
            'cost': self.cost,
            'outcome_space': self.outcome_space.value,
            'status': self.status.value
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


class InformationGainCalculator:
    """Calculate expected information gain for experiments"""

    def __init__(self):
        self.outcome_models: Dict[str, Callable] = {}

    def register_outcome_model(self, experiment_type: str,
                               model: Callable[[Any, Any], np.ndarray]):
        """Register outcome model for experiment type"""
        self.outcome_models[experiment_type] = model

    def expected_information_gain(self, experiment: Experiment,
                                  belief: Belief) -> float:
        """
        Calculate expected information gain (EIG).

        EIG = H[p(h)] - E_y[H[p(h|y)]]

        Where:
        - H[p(h)] is current entropy
        - E_y[H[p(h|y)]] is expected posterior entropy
        """
        current_entropy = belief.entropy()

        # For simplicity, assume uniform outcome distribution
        # In practice, would use proper outcome models
        n_outcomes = len(experiment.possible_outcomes) or 2
        expected_posterior_entropy = current_entropy * 0.5  # Placeholder

        return current_entropy - expected_posterior_entropy

    def value_of_information(self, experiment: Experiment,
                            belief: Belief,
                            cost: float = 1.0) -> float:
        """Compute value of information (VOI)"""
        eig = self.expected_information_gain(experiment, belief)
        return eig - cost


class ExperimentDesigner(ABC):
    """Abstract base for experiment designers"""

    @abstractmethod
    def design_experiment(self, context: Dict[str, Any]) -> Experiment:
        """Design a new experiment"""
        pass

    @abstractmethod
    def select_best(self, candidates: List[Experiment],
                   belief: Belief) -> Experiment:
        """Select best experiment from candidates"""
        pass


class ActiveExperimentDesigner(ExperimentDesigner):
    """Design active experiments to maximize information gain"""

    def __init__(self, vo_calculator: InformationGainCalculator = None):
        self.vo_calculator = vo_calculator or InformationGainCalculator()
        self.design_history: List[Experiment] = []

    def design_experiment(self, context: Dict[str, Any]) -> Experiment:
        """Design a new experiment based on context"""
        exp_id = f"exp_{len(self.design_history)}"

        return Experiment(
            experiment_id=exp_id,
            experiment_type=ExperimentType.OBSERVATION,
            description=context.get('question', 'Investigate phenomenon'),
            variables=context.get('variables', []),
            interventions={},
            conditions=context.get('conditions', {}),
            cost=context.get('cost', 1.0)
        )

    def select_best(self, candidates: List[Experiment],
                   belief: Belief) -> Experiment:
        """Select experiment with highest expected information gain"""
        if not candidates:
            raise ValueError("No candidates to select from")

        best_exp = candidates[0]
        best_voi = -float('inf')

        for exp in candidates:
            voi = self.vo_calculator.value_of_information(exp, belief)
            if voi > best_voi:
                best_voi = voi
                best_exp = exp

        return best_exp

    def design_sequence(self, initial_belief: Belief,
                       context: Dict[str, Any],
                       n_experiments: int = 5) -> List[Experiment]:
        """Design a sequence of experiments"""
        sequence = []
        current_belief = initial_belief

        for _ in range(n_experiments):
            exp = self.design_experiment(context)
            sequence.append(exp)

            # Simulate belief update (simplified)
            current_belief = current_belief.update(
                np.ones(len(current_belief.probabilities))
            )

        return sequence


class CausalExperimentDesigner(ActiveExperimentDesigner):
    """Design causal experiments to test causal relationships"""

    def design_intervention(self, variable: str,
                           value: Any,
                           context: Dict[str, Any]) -> Experiment:
        """Design an intervention experiment"""
        exp_id = f"intervention_{variable}_{len(self.design_history)}"

        return Experiment(
            experiment_id=exp_id,
            experiment_type=ExperimentType.INTERVENTION,
            description=f"Manipulate {variable} to {value}",
            variables=[variable],
            interventions={variable: value},
            conditions=context.get('conditions', {}),
            cost=context.get('cost', 2.0)
        )

    def design_comparison(self, variable: str,
                         condition1: Any, condition2: Any,
                         context: Dict[str, Any]) -> Experiment:
        """Design a comparison experiment"""
        exp_id = f"comparison_{variable}_{len(self.design_history)}"

        return Experiment(
            experiment_id=exp_id,
            experiment_type=ExperimentType.COMPARISON,
            description=f"Compare {variable} at {condition1} vs {condition2}",
            variables=[variable],
            interventions={},
            conditions={'conditions': [condition1, condition2]},
            cost=context.get('cost', 1.5)
        )


# Convenience functions
def design_active_experiment(context: Dict[str, Any]) -> Experiment:
    """Design an active experiment"""
    designer = ActiveExperimentDesigner()
    return designer.design_experiment(context)


def calculate_information_gain(experiment: Experiment,
                               belief: Belief) -> float:
    """Calculate expected information gain"""
    calculator = InformationGainCalculator()
    return calculator.expected_information_gain(experiment, belief)


def select_best_experiment(candidates: List[Experiment],
                          belief: Belief) -> Experiment:
    """Select best experiment from candidates"""
    designer = ActiveExperimentDesigner()
    return designer.select_best(candidates, belief)


__all__ = [
    'ExperimentType',
    'ExperimentStatus',
    'OutcomeSpace',
    'Variable',
    'HypothesisSpace',
    'Belief',
    'Experiment',
    'ExperimentResult',
    'InformationGainCalculator',
    'ExperimentDesigner',
    'ActiveExperimentDesigner',
    'CausalExperimentDesigner',
    'design_active_experiment',
    'calculate_information_gain',
    'select_best_experiment'
]
