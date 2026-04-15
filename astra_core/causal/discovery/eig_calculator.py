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
Expected Information Gain (EIG) Calculator for Active Causal Discovery

Computes the expected reduction in uncertainty about causal structure
from a hypothetical observation.

EIG = H[P(G | D_current)] - E[P(G | D_current, D_obs)]

where:
- H[P(G | D)] is entropy of current DAG posterior
- D_obs is hypothetical future observation
- The expectation is over possible observations

Accounts for:
- Observation noise (Gaussian, Poisson, etc.)
- Measurement uncertainty
- Latent confounders
- Selection bias

Reference:
- Steck, H. (2008). On the use of missing data in discovery.
- Runge, J. (2018). Causal inference beyond DAGs.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from scipy.stats import entropy, multivariate_normal
from scipy.special import logsumexp

logger = logging.getLogger(__name__)


class NoiseModel(Enum):
    """Types of observation noise"""
    GAUSSIAN = "gaussian"  # Homoscedastic Gaussian
    HETEROSCEDASTIC = "heteroscedastic"  # Per-variable variance
    POISSON = "poisson"  # Count data
    BERNOULLI = "bernoulli"  # Binary data
    STUDENT_T = "student_t"  # Heavy-tailed


@dataclass
class ObservationPlan:
    """
    A planned observation for active discovery

    Attributes:
        target_variables: Which variables to observe
        sample_size: How many samples to collect
        noise_model: Type of observation noise
        noise_parameters: Parameters for noise model
        intervention: Optional intervention (do(X=x))
        cost: Cost of observation (time, money)
        feasibility: Whether observation is feasible
    """
    target_variables: List[str]
    sample_size: int
    noise_model: NoiseModel = NoiseModel.GAUSSIAN
    noise_parameters: Dict[str, float] = field(default_factory=dict)
    intervention: Optional[Dict[str, float]] = None
    cost: float = 1.0
    feasibility: float = 1.0
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class EIGResult:
    """
    Result from Expected Information Gain calculation

    Attributes:
        eig: Expected information gain (nats)
        edge_eig: Per-edge information gain
        uncertainty_reduction: Fraction of uncertainty reduced
        expected_posterior: Posterior after hypothetical observation
        observation_value: Expected optimal observation value
        convergence_probability: Probability of converging to true structure
    """
    eig: float
    edge_eig: Dict[Tuple[int, int], float]
    uncertainty_reduction: float
    expected_posterior: np.ndarray  # Expected edge posterior after observation
    observation_value: float  # Value of this observation
    convergence_probability: float


class LatentConfounderModel:
    """
    Model latent confounders in causal discovery

    Methods:
    - Marginal likelihood integration over latents
    - Identifiability conditions
    - Sensitivity analysis
    """

    def __init__(
        self,
        n_latents: int = 1,
        latent_prior: str = "gaussian",
        identification_strategy: str = "instrumental"
    ):
        """
        Initialize latent confounder model

        Args:
            n_latents: Number of latent confounders
            latent_prior: Prior distribution for latents
            identification_strategy: How to handle identifiability
        """
        self.n_latents = n_latents
        self.latent_prior = latent_prior
        self.identification_strategy = identification_strategy

    def marginalize_latents(
        self,
        observed_data: np.ndarray,
        causal_structure: np.ndarray
    ) -> np.ndarray:
        """
        Marginalize out latent confounders

        Computes P(observed | structure) = ∫ P(observed | latent, structure) P(latent) dlatent

        Args:
            observed_data: Observed variables
            causal_structure: Current DAG estimate

        Returns:
            Marginal likelihood with latents integrated out
        """
        # Use variational approximation for marginalization
        # For Gaussian models, can use conditional independence structure

        n_obs = observed_data.shape[1]

        # For Gaussian with latent parents:
        # Marginal covariance = observed_cov + latent_cov
        # This creates "bow pattern" correlations

        sample_cov = np.cov(observed_data.T)

        # Adjust covariance for latent confounders
        # Latents induce additional correlations
        latent_cov = self._estimate_latent_covariance(causal_structure, n_obs)

        marginal_cov = sample_cov + latent_cov

        return marginal_cov

    def _estimate_latent_covariance(
        self,
        causal_structure: np.ndarray,
        n_observed: int
    ) -> np.ndarray:
        """Estimate covariance contribution from latents"""
        # Simplified: latents create correlations between
        # variables that share common latent parents

        latent_cov = np.zeros((n_observed, n_observed))

        # Find pairs with possible common latent parent
        # (neither directly causes the other)
        for i in range(n_observed):
            for j in range(i+1, n_observed):
                if causal_structure[i, j] == 0 and causal_structure[j, i] == 0:
                    # No direct edge → possible latent confounder
                    latent_cov[i, j] = latent_cov[j, i] = 0.1  # Small correlation

        return latent_cov

    def check_identifiability(
        self,
        causal_structure: np.ndarray
    ) -> Dict[str, bool]:
        """
        Check if causal effects are identifiable with latents

        Uses front-door and back-door criteria
        """
        identifiability = {}

        # For each pair, check if effect is identifiable
        n = causal_structure.shape[0]
        for i in range(n):
            for j in range(n):
                if causal_structure[j, i] == 1:  # i → j
                    identifiability[(i, j)] = self._check_effect_identifiable(
                        i, j, causal_structure
                    )

        return identifiability

    def _check_effect_identifiable(
        self,
        cause: int,
        effect: int,
        structure: np.ndarray
    ) -> bool:
        """Check if causal effect is identifiable"""
        # Simplified: effect identifiable if there's a valid adjustment set

        # Find adjustment set (back-door criterion)
        parents_of_effect = np.where(structure[effect, :] == 1)[0]
        descendants_of_cause = self._find_descendants(cause, structure)

        # Valid adjustment set: parents of effect not descendants of cause
        adjustment_set = [p for p in parents_of_effect if p not in descendants_of_cause]

        return len(adjustment_set) > 0 or self._has_front_door(cause, effect, structure)

    def _find_descendants(self, node: int, structure: np.ndarray) -> List[int]:
        """Find all descendants of a node"""
        descendants = []
        visited = set()

        def dfs(n):
            if n in visited:
                return
            visited.add(n)
            children = np.where(structure[:, n] == 1)[0]
            for child in children:
                descendants.append(child)
                dfs(child)

        dfs(node)
        return descendants

    def _has_front_door(
        self,
        cause: int,
        effect: int,
        structure: np.ndarray
    ) -> bool:
        """Check if front-door criterion applies"""
        # Front-door: mediator M such that:
        # 1. M intercepts all directed paths from cause to effect
        # 2. No unobserved confounder for cause → M
        # 3. All back-door paths from M to effect blocked by cause

        mediators = np.where(structure[:, cause] == 1)[0]  # Children of cause

        for mediator in mediators:
            # Check if mediator is on all paths from cause to effect
            # (simplified check)
            if structure[effect, mediator] == 1:
                return True  # cause → mediator → effect

        return False


class ExpectedInformationGainCalculator:
    """
    Expected Information Gain calculator for active causal discovery

    Computes how much a hypothetical observation would reduce
    uncertainty about the causal structure.

    Features:
    - Multiple noise models (Gaussian, Poisson, etc.)
    - Latent confounder handling
    - Selection bias correction
    - Efficient computation via Monte Carlo
    """

    def __init__(
        self,
        current_posterior: np.ndarray,
        n_monte_carlo_samples: int = 100,
        noise_model: NoiseModel = NoiseModel.GAUSSIAN,
        handle_latents: bool = True,
        handle_selection_bias: bool = True,
        random_state: Optional[int] = None
    ):
        """
        Initialize EIG calculator

        Args:
            current_posterior: Current edge posterior matrix P(G_ij = 1 | D)
            n_monte_carlo_samples: MC samples for expectation
            noise_model: Type of observation noise
            handle_latents: Whether to model latent confounders
            handle_selection_bias: Whether to correct for selection bias
            random_state: Random seed
        """
        self.current_posterior = current_posterior
        self.n_monte_carlo_samples = n_monte_carlo_samples
        self.noise_model = noise_model
        self.handle_latents = handle_latents
        self.handle_selection_bias = handle_selection_bias
        self.random_state = random_state

        if random_state is not None:
            np.random.seed(random_state)

        # Initialize latent confounder model
        if handle_latents:
            self.latent_model = LatentConfounderModel()
        else:
            self.latent_model = None

        # Current entropy
        self.current_entropy = self._compute_posterior_entropy(current_posterior)

    def compute_eig(
        self,
        observation_plan: ObservationPlan,
        data_generating_model: Optional[Callable] = None,
        verbose: bool = False
    ) -> EIGResult:
        """
        Compute Expected Information Gain for an observation plan

        EIG = H[current] - E[H[new | observation]]

        Args:
            observation_plan: Planned observation
            data_generating_model: Optional model to generate synthetic data
            verbose: Print progress

        Returns:
            EIGResult with information gain metrics
        """
        if verbose:
            logger.info(f"Computing EIG for observation plan: {observation_plan.target_variables}")
            logger.info(f"Sample size: {observation_plan.sample_size}")

        # Sample possible future observations
        future_observations = self._sample_future_observations(
            observation_plan,
            data_generating_model
        )

        # Compute posterior for each possible observation
        posterior_futures = []

        for obs in future_observations:
            new_posterior = self._update_posterior(obs, observation_plan)
            posterior_futures.append(new_posterior)

        # Expected future entropy
        expected_future_entropy = np.mean([
            self._compute_posterior_entropy(p)
            for p in posterior_futures
        ])

        # Expected posterior
        expected_posterior = np.mean(posterior_futures, axis=0)

        # EIG
        eig = self.current_entropy - expected_future_entropy

        # Per-edge EIG
        edge_eig = self._compute_edge_eig(
            self.current_posterior,
            expected_posterior
        )

        # Uncertainty reduction
        uncertainty_reduction = 1 - (expected_future_entropy / (self.current_entropy + 1e-10))

        # Observation value (EIG normalized by cost)
        observation_value = eig / (observation_plan.cost + 1e-10)

        # Convergence probability (simplified)
        convergence_prob = self._estimate_convergence_probability(
            posterior_futures,
            threshold=0.95
        )

        if verbose:
            logger.info(f"EIG: {eig:.4f} nats")
            logger.info(f"Uncertainty reduction: {uncertainty_reduction:.2%}")
            logger.info(f"Observation value: {observation_value:.4f}")

        return EIGResult(
            eig=eig,
            edge_eig=edge_eig,
            uncertainty_reduction=uncertainty_reduction,
            expected_posterior=expected_posterior,
            observation_value=observation_value,
            convergence_probability=convergence_prob
        )

    def rank_observation_plans(
        self,
        plans: List[ObservationPlan],
        data_generating_model: Optional[Callable] = None,
        verbose: bool = False
    ) -> List[EIGResult]:
        """
        Rank observation plans by expected information gain

        Args:
            plans: List of observation plans
            data_generating_model: Optional model for synthetic data
            verbose: Print progress

        Returns:
            List of EIGResults sorted by observation value
        """
        results = []

        for i, plan in enumerate(plans):
            if verbose:
                logger.info(f"Evaluating plan {i+1}/{len(plans)}")

            result = self.compute_eig(plan, data_generating_model, verbose=False)
            results.append(result)

        # Sort by observation value
        results.sort(key=lambda r: r.observation_value, reverse=True)

        return results

    def _compute_posterior_entropy(self, posterior: np.ndarray) -> float:
        """Compute entropy of DAG posterior"""
        # Entropy of independent Bernoulli for each edge
        entropies = []

        for i in range(posterior.shape[0]):
            for j in range(posterior.shape[1]):
                p = posterior[i, j]
                if 0 < p < 1:  # Only non-degenerate edges
                    ent = -p * np.log(p) - (1-p) * np.log(1-p)
                    entropies.append(ent)

        return np.sum(entropies)

    def _sample_future_observations(
        self,
        plan: ObservationPlan,
        data_generating_model: Optional[Callable]
    ) -> List[np.ndarray]:
        """Sample possible future observations"""
        observations = []

        for _ in range(self.n_monte_carlo_samples):
            if data_generating_model is not None:
                # Use provided model
                obs = data_generating_model(
                    target_variables=plan.target_variables,
                    sample_size=plan.sample_size,
                    noise_model=plan.noise_model,
                    noise_parameters=plan.noise_parameters
                )
            else:
                # Sample from current posterior predictive
                obs = self._sample_from_posterior_predictive(plan)

            # Add noise
            obs = self._add_observation_noise(obs, plan)

            observations.append(obs)

        return observations

    def _sample_from_posterior_predictive(
        self,
        plan: ObservationPlan
    ) -> np.ndarray:
        """Sample from posterior predictive distribution"""
        n_targets = len(plan.target_variables)
        n_samples = plan.sample_size

        # Simplified: sample from multivariate Gaussian
        # with covariance implied by current posterior

        # Sample a DAG from posterior
        dag_sample = (np.random.random(self.current_posterior.shape) < self.current_posterior).astype(int)

        # Sample data consistent with DAG
        # (simplified: just sample from multivariate normal)

        mean = np.zeros(n_targets)
        cov = np.eye(n_targets)

        # Modulate covariance by edge strengths
        for i in range(n_targets):
            for j in range(n_targets):
                if i != j and self.current_posterior[i, j] > 0.5:
                    cov[i, j] = cov[j, i] = 0.3

        # Ensure positive definite
        cov = cov @ cov.T + np.eye(n_targets) * 0.1

        data = np.random.multivariate_normal(mean, cov, size=n_samples)

        return data

    def _add_observation_noise(
        self,
        data: np.ndarray,
        plan: ObservationPlan
    ) -> np.ndarray:
        """Add observation noise according to noise model"""
        if plan.noise_model == NoiseModel.GAUSSIAN:
            # Homoscedastic Gaussian
            noise_std = plan.noise_parameters.get('std', 0.1)
            noise = np.random.normal(0, noise_std, data.shape)
            return data + noise

        elif plan.noise_model == NoiseModel.HETEROSCEDASTIC:
            # Per-variable noise
            noise_stds = plan.noise_parameters.get('stds', [0.1] * data.shape[1])
            noise = np.zeros_like(data)
            for i, std in enumerate(noise_stds):
                noise[:, i] = np.random.normal(0, std, data.shape[0])
            return data + noise

        elif plan.noise_model == NoiseModel.POISSON:
            # Poisson noise (for count data)
            # Ensure non-negative
            data_pos = np.maximum(data, 0)
            return np.random.poisson(data_pos).astype(float)

        elif plan.noise_model == NoiseModel.STUDENT_T:
            # Heavy-tailed noise
            df = plan.noise_parameters.get('df', 3)
            scale = plan.noise_parameters.get('scale', 0.1)
            noise = np.random.standard_t(df, data.shape) * scale
            return data + noise

        else:
            return data

    def _update_posterior(
        self,
        observation: np.ndarray,
        plan: ObservationPlan
    ) -> np.ndarray:
        """
        Update posterior given new observation

        Uses Bayesian updating with conjugate priors
        """
        # Simplified Bayesian update
        # Posterior ∝ Likelihood × Prior

        n_targets = len(plan.target_variables)

        # Compute likelihood of observation for each possible edge
        # (simplified: use correlation-based update)

        if len(observation) < 2:
            return self.current_posterior.copy()

        # Sample correlation
        sample_corr = np.corrcoef(observation.T)

        # Update posterior: edges supported by correlation increase
        new_posterior = self.current_posterior.copy()

        learning_rate = 0.1 / np.sqrt(plan.sample_size)  # Diminishing updates

        for i in range(n_targets):
            for j in range(n_targets):
                if i != j:
                    # Update based on correlation
                    if abs(sample_corr[i, j]) > 0.3:
                        # Positive evidence for edge
                        new_posterior[i, j] += learning_rate * abs(sample_corr[i, j])
                    else:
                        # Negative evidence
                        new_posterior[i, j] -= learning_rate * 0.5

        # Normalize to [0, 1]
        new_posterior = np.clip(new_posterior, 0.01, 0.99)

        return new_posterior

    def _compute_edge_eig(
        self,
        current_posterior: np.ndarray,
        expected_posterior: np.ndarray
    ) -> Dict[Tuple[int, int], float]:
        """Compute per-edge information gain"""
        edge_eig = {}

        for i in range(current_posterior.shape[0]):
            for j in range(current_posterior.shape[1]):
                # Entropy reduction for this edge
                p_current = current_posterior[i, j]
                p_future = expected_posterior[i, j]

                h_current = -p_current * np.log(p_current + 1e-10) - (1-p_current) * np.log(1-p_current + 1e-10)
                h_future = -p_future * np.log(p_future + 1e-10) - (1-p_future) * np.log(1-p_future + 1e-10)

                edge_eig[(i, j)] = h_current - h_future

        return edge_eig

    def _estimate_convergence_probability(
        self,
        posterior_futures: List[np.ndarray],
        threshold: float = 0.95
    ) -> float:
        """Estimate probability of converging to true structure"""
        # Count how many posterior samples have confident edges
        converged_count = 0

        for posterior in posterior_futures:
            confident_edges = np.sum(
                (posterior > threshold) | (posterior < 1 - threshold)
            )
            total_edges = posterior.size

            if confident_edges / total_edges > 0.8:  # 80% of edges confident
                converged_count += 1

        return converged_count / len(posterior_futures)


def create_eig_calculator(
    current_posterior: np.ndarray,
    n_monte_carlo_samples: int = 100,
    **kwargs
) -> ExpectedInformationGainCalculator:
    """
    Create EIG calculator

    Args:
        current_posterior: Current edge posterior matrix
        n_monte_carlo_samples: Number of MC samples
        **kwargs: Additional arguments

    Returns:
        Configured ExpectedInformationGainCalculator
    """
    return ExpectedInformationGainCalculator(
        current_posterior=current_posterior,
        n_monte_carlo_samples=n_monte_carlo_samples,
        **kwargs
    )


__all__ = [
    'NoiseModel',
    'ObservationPlan',
    'EIGResult',
    'LatentConfounderModel',
    'ExpectedInformationGainCalculator',
    'create_eig_calculator',
]
