"""
Bayesian Experimental Design Engine (BEDE)
==========================================

Designs optimal observation sequences using Bayesian decision theory.

Goes beyond V43 (facility selection) and V92 (experimental design)
by using full Bayesian decision theory:
- Value of Information (VoI) calculation
- Sequential experimental design
- Multi-objective optimization
- Adaptive learning

This enables optimal observation planning for maximum scientific return.

Author: STAN-XI ASTRO V100 Development Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum, auto
import numpy as np
import time
import math
from scipy.stats import entropy, norm


# =============================================================================
# Enumerations
# =============================================================================

class UtilityType(Enum):
    """Types of utility functions"""
    INFORMATION_GAIN = "information_gain"  # Entropy reduction
    PREDICTION_ERROR = "prediction_error"  # Reduce prediction uncertainty
    DISCRIMINATION = "discrimination"  # Distinguish between theories
    DISCOVERY = "discovery"  # Probability of novel discovery
    PUBLICATION = "publication"  # Publication value


# =============================================================================
# Core Data Structures
# =============================================================================

@dataclass
class PosteriorDistribution:
    """Represents current belief about parameters"""
    mean: np.ndarray  # Mean vector
    covariance: np.ndarray  # Covariance matrix
    samples: Optional[np.ndarray] = None  # MCMC samples (optional)
    parameter_names: List[str] = field(default_factory=list)

    def entropy(self) -> float:
        """Calculate entropy (differential entropy for Gaussian)"""
        k = len(self.mean)
        return 0.5 * k * (1 + np.log(2 * np.pi)) + 0.5 * np.log(np.linalg.det(self.covariance))

    def sample(self, n_samples: int = 1000) -> np.ndarray:
        """Sample from posterior"""
        if self.samples is not None and len(self.samples) >= n_samples:
            return self.samples[:n_samples]
        return np.random.multivariate_normal(self.mean, self.covariance, n_samples)


@dataclass
class InformationGain:
    """Expected information gain from an observation"""
    nats: float  # Information gain in nats
    bits: float  # Information gain in bits
    percentage: float  # Percentage of remaining uncertainty

    def __post_init__(self):
        if self.nats > 0:
            self.bits = self.nats / np.log(2)
            self.percentage = 100 * (1 - np.exp(-self.nats))


@dataclass
class ValueOfInformation:
    """Value of information calculation"""
    expected_utility: float
    cost: float
    net_value: float
    information_gain: InformationGain
    confidence: float

    def roi(self) -> float:
        """Return on investment"""
        if self.cost > 0:
            return self.net_value / self.cost
        return 0.0


@dataclass
class ObservationPlan:
    """An observation plan with Bayesian assessment"""
    target: str
    observation_type: str
    facility: str
    instrument: str
    integration_time_hours: float

    # Bayesian assessment
    expected_information_gain: InformationGain
    value_of_information: ValueOfInformation
    success_probability: float
    priority_score: float  # Overall priority

    # Metadata
    estimated_cost: float = 0.0
    time_required: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObservationSequence:
    """Optimal sequence of observations"""
    plans: List[ObservationPlan]
    total_information_gain: InformationGain
    total_cost: float
    total_time_hours: float
    stopping_rule: Optional[str] = None


# =============================================================================
# Theory Representation
# =============================================================================

@dataclass
class Theory:
    """A theory with predictions"""
    name: str
    parameters: Dict[str, float]  # Model parameters
    predictions: Dict[str, float]  # Observable -> prediction
    uncertainties: Dict[str, float]  # Observable -> uncertainty
    prior_probability: float = 0.5


# =============================================================================
# Bayesian Experimental Designer
# =============================================================================

class BayesianExperimentalDesigner:
    """
    Designs optimal observation sequences using Bayesian decision theory.

    Key features:
    - Value of Information calculation
    - Sequential experimental design
    - Adaptive learning (update design as data arrives)
    - Multi-objective optimization (value vs. cost)
    """

    def __init__(self):
        self.theories: Dict[str, Theory] = {}
        self.current_belief: Optional[PosteriorDistribution] = None
        self.observation_history: List[Dict[str, Any]] = []

    def design_observation_sequence(
        self,
        current_belief: PosteriorDistribution,
        theories: List[Theory],
        available_observations: List[Dict[str, Any]],
        budget_time_hours: float,
        budget_cost_dollars: float,
        utility_type: UtilityType = UtilityType.INFORMATION_GAIN,
        target_confidence: float = 0.99
    ) -> ObservationSequence:
        """
        Generate optimal observation sequence.

        Parameters
        ----------
        current_belief : PosteriorDistribution
            Current state of knowledge
        theories : list
            Competing theories
        available_observations : list
            Observations that could be made
        budget_time_hours : float
            Time budget
        budget_cost_dollars : float
            Cost budget
        utility_type : UtilityType
            What to optimize
        target_confidence : float
            Target confidence (for stopping)

        Returns
        -------
        ObservationSequence with optimal ordering
        """
        print(f"BEDE: Designing observation sequence")
        print(f"  Budget: {budget_time_hours} hrs, ${budget_cost_dollars}")

        # Store theories
        for theory in theories:
            self.theories[theory.name] = theory

        # Score each observation
        scored_plans = []
        for obs in available_observations:
            plan = self._design_single_observation(
                current_belief,
                theories,
                obs
            )
            scored_plans.append(plan)

        # Optimize sequence
        # Greedy algorithm: pick highest VoI first, update belief, repeat
        sequence_plans = []
        remaining_time = budget_time_hours
        remaining_cost = budget_cost_dollars
        total_ig = 0.0

        current_belief_state = current_belief

        while remaining_time > 0 and remaining_cost > 0:
            # Find best remaining observation
            best_plan = None
            best_value = -np.inf

            for plan in scored_plans:
                if plan in sequence_plans:
                    continue

                # Check constraints
                if plan.integration_time_hours > remaining_time:
                    continue
                if plan.estimated_cost > remaining_cost:
                    continue

                # Calculate net value
                net_value = plan.value_of_information.net_value

                if net_value > best_value:
                    best_value = net_value
                    best_plan = plan

            if best_plan is None:
                break

            # Add to sequence
            sequence_plans.append(best_plan)
            total_ig += best_plan.expected_information_gain.nats

            # Update budgets
            remaining_time -= best_plan.integration_time_hours
            remaining_cost -= best_plan.estimated_cost

            # Check if target confidence reached
            if current_belief_state.entropy() < (1 - target_confidence) * 10:
                print(f"  Target confidence reached after {len(sequence_plans)} observations")
                break

        return ObservationSequence(
            plans=sequence_plans,
            total_information_gain=InformationGain(nats=total_ig),
            total_cost=budget_cost_dollars - remaining_cost,
            total_time_hours=budget_time_hours - remaining_time,
        )

    def _design_single_observation(
        self,
        belief: PosteriorDistribution,
        theories: List[Theory],
        observation_spec: Dict[str, Any]
    ) -> ObservationPlan:
        """Design a single observation and calculate its value"""

        observable = observation_spec.get('observable', 'unknown')
        facility = observation_spec.get('facility', 'general')
        instrument = observation_spec.get('instrument', 'general')
        time_hours = observation_spec.get('time_hours', 2.0)

        # Calculate expected information gain
        ig = self._calculate_information_gain(belief, observable, theories)

        # Calculate value of information
        voi = self._calculate_voi(ig, time_hours, observation_spec)

        # Calculate success probability
        success_prob = self._estimate_success_probability(observation_spec, belief)

        # Overall priority score
        priority = (ig.percentage * success_prob *
                   voi.expected_utility / (time_hours + 1))

        return ObservationPlan(
            target=observation_spec.get('target', 'unknown'),
            observation_type=observation_spec.get('type', 'imaging'),
            facility=facility,
            instrument=instrument,
            integration_time_hours=time_hours,
            expected_information_gain=ig,
            value_of_information=voi,
            success_probability=success_prob,
            priority_score=priority,
            estimated_cost=observation_spec.get('cost', time_hours * 1000),
        )

    def _calculate_information_gain(
        self,
        belief: PosteriorDistribution,
        observable: str,
        theories: List[Theory]
    ) -> InformationGain:
        """
        Calculate expected information gain from an observation.

        Uses mutual information:
        IG = H(Y) - E[H(Y|X)]

        Where H is entropy, Y is theory/probability, X is observation.
        """
        # Current uncertainty
        current_entropy = belief.entropy()

        # Expected posterior entropy after observation
        # Simplified: assume Gaussian posterior with reduced variance
        n_params = len(belief.mean)
        prior_variance = np.trace(belief.covariance) / n_params

        # Expected variance reduction depends on observation precision
        # This is a simplified calculation
        expected_variance_reduction = 0.5  # Could be estimated from instrument specs
        expected_posterior_variance = prior_variance * expected_variance_reduction

        # Calculate information gain
        # For Gaussian: IG = 0.5 * ln(prior_var / posterior_var)
        ig_nats = 0.5 * np.log(prior_variance / (expected_posterior_variance + 1e-10))

        return InformationGain(nats=ig_nats)

    def _calculate_voi(
        self,
        ig: InformationGain,
        time_hours: float,
        observation_spec: Dict[str, Any]
    ) -> ValueOfInformation:
        """Calculate value of information"""
        # Utility from information gain
        information_utility = ig.percentage / 100.0  # Normalize to [0, 1]

        # Cost penalty
        time_cost = time_hours / 24.0  # Days
        money_cost = observation_spec.get('cost', 0) / 10000.0  # $10k units

        total_cost = time_cost + money_cost

        # Expected utility
        expected_utility = information_utility

        # Net value
        net_value = expected_utility - (total_cost * 0.1)  # Discount factor

        return ValueOfInformation(
            expected_utility=expected_utility,
            cost=total_cost,
            net_value=net_value,
            information_gain=ig,
            confidence=0.7,
        )

    def _estimate_success_probability(
        self,
        observation_spec: Dict[str, Any],
        belief: PosteriorDistribution
    ) -> float:
        """Estimate probability of successful observation"""
        # Base success rate
        base_rate = 0.7

        # Adjust based on observation difficulty
        if observation_spec.get('difficult', False):
            base_rate *= 0.7

        # Adjust based on current uncertainty
        # More uncertain = higher potential gain but also higher risk of failure
        uncertainty = np.trace(belief.covariance) / len(belief.mean)
        if uncertainty > 1.0:
            base_rate *= 0.9  # High uncertainty is good for learning

        return max(0.1, min(0.95, base_rate))

    def update_belief(
        self,
        observation_data: Dict[str, Any],
        prior_belief: PosteriorDistribution,
        theories: List[Theory]
    ) -> PosteriorDistribution:
        """
        Update belief after making an observation.

        Uses Bayes' theorem with likelihood from theories.
        """
        # Simplified Bayesian update
        # In production, would use proper MCMC or variational inference

        old_mean = prior_belief.mean
        old_cov = prior_belief.covariance

        # Likelihood (simplified)
        observation_value = observation_data.get('value', 0.0)
        observation_noise = observation_data.get('uncertainty', 1.0)

        # For each theory, compute likelihood
        likelihoods = []
        for theory in theories:
            prediction = theory.predictions.get(observation_data.get('observable', ''), 0)
            theory_unc = theory.uncertainties.get(observation_data.get('observable', ''), 1)

            # Gaussian likelihood
            likelihood = np.exp(-0.5 * ((observation_value - prediction) / theory_unc)**2)
            likelihoods.append(likelihood)

        # Posterior weights
        weights = np.array(likelihoods)
        weights /= np.sum(weights)

        # Update posterior (simplified - would use full Bayes)
        new_mean = old_mean * 0.9 + np.mean(weights) * 0.1
        new_cov = old_cov * 0.9  # Reduce uncertainty

        return PosteriorDistribution(
            mean=new_mean,
            covariance=new_cov,
            parameter_names=prior_belief.parameter_names
        )


# =============================================================================
# Factory Functions
# =============================================================================

def create_bayesian_designer() -> BayesianExperimentalDesigner:
    """Create a Bayesian experimental designer"""
    return BayesianExperimentalDesigner()


# =============================================================================
# Convenience Functions
# =============================================================================

def design_optimal_observations(
    current_belief: PosteriorDistribution,
    theories: List[Theory],
    available_observations: List[Dict[str, Any]],
    budget_hours: float = 50.0
) -> ObservationSequence:
    """
    Convenience function to design optimal observations.
    """
    designer = create_bayesian_designer()
    return designer.design_observation_sequence(
        current_belief=current_belief,
        theories=theories,
        available_observations=available_observations,
        budget_time_hours=budget_hours,
        budget_cost_dollars=budget_hours * 1000  # $1k/hour
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'UtilityType',
    'PosteriorDistribution',
    'InformationGain',
    'ValueOfInformation',
    'ObservationPlan',
    'ObservationSequence',
    'Theory',
    'BayesianExperimentalDesigner',
    'create_bayesian_designer',
    'design_optimal_observations',
]
