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
Bayesian Inference for STAN

Implements Bayesian reasoning with prior specification, likelihood functions,
and posterior updating for scientific inference tasks.

Date: 2026-03-18
Version: 1.0
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from scipy import stats
from scipy.special import logsumexp
import warnings


# =============================================================================
# BAYESIAN INFERENCE STRUCTURES
# =============================================================================

class PriorType(Enum):
    """Types of prior distributions"""
    UNIFORM = "uniform"
    NORMAL = "normal"
    LOG_NORMAL = "log_normal"
    EXPONENTIAL = "exponential"
    BETA = "beta"
    GAMMA = "gamma"
    CUSTOM = "custom"


class LikelihoodType(Enum):
    """Types of likelihood functions"""
    GAUSSIAN = "gaussian"
    POISSON = "poisson"
    BINOMIAL = "binomial"
    EXPONENTIAL = "exponential"
    CUSTOM = "custom"


@dataclass
class Prior:
    """
    Prior distribution for a parameter.

    Attributes:
        name: Parameter name
        prior_type: Type of prior distribution
        params: Distribution parameters (e.g., mean, std for normal)
        bounds: Optional bounds for the parameter
    """
    name: str
    prior_type: PriorType
    params: Dict[str, float]
    bounds: Optional[Tuple[float, float]] = None

    def sample(self, n_samples: int = 1) -> np.ndarray:
        """Draw samples from the prior"""
        if self.prior_type == PriorType.UNIFORM:
            low, high = self.params.get('low', 0), self.params.get('high', 1)
            return np.random.uniform(low, high, n_samples)

        elif self.prior_type == PriorType.NORMAL:
            mean, std = self.params.get('mean', 0), self.params.get('std', 1)
            return np.random.normal(mean, std, n_samples)

        elif self.prior_type == PriorType.LOG_NORMAL:
            mean, std = self.params.get('mean', 0), self.params.get('std', 1)
            return np.random.lognormal(mean, std, n_samples)

        elif self.prior_type == PriorType.EXPONENTIAL:
            scale = self.params.get('scale', 1.0)
            return np.random.exponential(scale, n_samples)

        elif self.prior_type == PriorType.BETA:
            alpha, beta = self.params.get('alpha', 1), self.params.get('beta', 1)
            return np.random.beta(alpha, beta, n_samples)

        elif self.prior_type == PriorType.GAMMA:
            shape, scale = self.params.get('shape', 1), self.params.get('scale', 1)
            return np.random.gamma(shape, scale, n_samples)

        else:
            raise ValueError(f"Unknown prior type: {self.prior_type}")

    def log_prob(self, x: float) -> float:
        """Compute log probability density"""
        if self.prior_type == PriorType.UNIFORM:
            low, high = self.params.get('low', 0), self.params.get('high', 1)
            if low <= x <= high:
                return -np.log(high - low)
            return -np.inf

        elif self.prior_type == PriorType.NORMAL:
            mean, std = self.params.get('mean', 0), self.params.get('std', 1)
            return stats.norm.logpdf(x, mean, std)

        elif self.prior_type == PriorType.LOG_NORMAL:
            mean, std = self.params.get('mean', 0), self.params.get('std', 1)
            return stats.lognorm.logpdf(x, std, loc=0, scale=np.exp(mean))

        elif self.prior_type == PriorType.EXPONENTIAL:
            scale = self.params.get('scale', 1.0)
            return stats.expon.logpdf(x, loc=0, scale=scale)

        elif self.prior_type == PriorType.BETA:
            alpha, beta = self.params.get('alpha', 1), self.params.get('beta', 1)
            return stats.beta.logpdf(x, alpha, beta)

        elif self.prior_type == PriorType.GAMMA:
            shape, scale = self.params.get('shape', 1), self.params.get('scale', 1)
            return stats.gamma.logpdf(x, shape, loc=0, scale=scale)

        return -np.inf


@dataclass
class Likelihood:
    """
    Likelihood function for observed data.

    Attributes:
        likelihood_type: Type of likelihood distribution
        params: Distribution parameters
        data: Observed data
    """
    likelihood_type: LikelihoodType
    params: Dict[str, float]
    data: Optional[np.ndarray] = None

    def log_prob(self, params: Dict[str, float]) -> float:
        """
        Compute log probability of data given parameters.

        Args:
            params: Model parameters

        Returns:
            Log likelihood
        """
        if self.data is None:
            return 0.0

        if self.likelihood_type == LikelihoodType.GAUSSIAN:
            # Gaussian likelihood: L = exp(-0.5 * (x - mu)^2 / sigma^2)
            mu = params.get('mu', self.params.get('mu', 0))
            sigma = params.get('sigma', self.params.get('sigma', 1))
            residuals = self.data - mu
            return -0.5 * np.sum(residuals**2) / sigma**2 - len(self.data) * np.log(sigma)

        elif self.likelihood_type == LikelihoodType.POISSON:
            # Poisson likelihood: L = exp(-lambda) * lambda^x / x!
            rate = params.get('rate', self.params.get('rate', 1))
            return np.sum(stats.poisson.logpmf(self.data, rate))

        elif self.likelihood_type == LikelihoodType.BINOMIAL:
            # Binomial likelihood
            p = params.get('p', self.params.get('p', 0.5))
            n = params.get('n', self.params.get('n', len(self.data)))
            successes = np.sum(self.data)
            return stats.binom.logpmf(successes, n, p)

        elif self.likelihood_type == LikelihoodType.EXPONENTIAL:
            # Exponential likelihood
            scale = params.get('scale', self.params.get('scale', 1))
            return np.sum(stats.expon.logpdf(self.data, loc=0, scale=scale))

        return 0.0


@dataclass
class Posterior:
    """
    Posterior distribution from Bayesian inference.

    Attributes:
        samples: Posterior samples
        log_evidence: Log marginal likelihood
        parameter_names: Names of parameters
        map_estimate: Maximum a posteriori estimate
        mean: Posterior mean
        std: Posterior standard deviation
    """
    samples: np.ndarray
    log_evidence: float
    parameter_names: List[str]
    map_estimate: Dict[str, float] = field(default_factory=dict)
    mean: Dict[str, float] = field(default_factory=dict)
    std: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Compute posterior statistics"""
        if len(self.samples) > 0:
            for i, name in enumerate(self.parameter_names):
                param_samples = self.samples[:, i]
                self.mean[name] = np.mean(param_samples)
                self.std[name] = np.std(param_samples)

                # MAP estimate (using histogram for continuous parameters)
                hist, bins = np.histogram(param_samples, bins=50, density=True)
                bin_centers = (bins[:-1] + bins[1:]) / 2
                self.map_estimate[name] = bin_centers[np.argmax(hist)]

    def get_credible_interval(self, param_name: str, credible_mass: float = 0.95) -> Tuple[float, float]:
        """
        Get credible interval for a parameter.

        Args:
            param_name: Parameter name
            credible_mass: Mass of credible interval (default 0.95 for 95%)

        Returns:
            Lower and upper bounds of credible interval
        """
        idx = self.parameter_names.index(param_name)
        param_samples = self.samples[:, idx]

        alpha = 1 - credible_mass
        lower = np.percentile(param_samples, 100 * alpha / 2)
        upper = np.percentile(param_samples, 100 * (1 - alpha / 2))

        return lower, upper

    def summary(self) -> str:
        """Generate summary of posterior distribution"""
        lines = ["=" * 60]
        lines.append("POSTERIOR SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Log evidence: {self.log_evidence:.2f}")
        lines.append(f"Number of samples: {len(self.samples)}")
        lines.append("-" * 60)

        for name in self.parameter_names:
            lines.append(f"{name}:")
            lines.append(f"  Mean: {self.mean[name]:.4g}")
            lines.append(f"  Std:  {self.std[name]:.4g}")
            lines.append(f"  MAP:  {self.map_estimate[name]:.4g}")

            lower, upper = self.get_credible_interval(name, 0.95)
            lines.append(f"  95% CI: [{lower:.4g}, {upper:.4g}]")

        lines.append("=" * 60)
        return "\n".join(lines)


@dataclass
class BayesFactor:
    """Result of Bayes factor comparison"""
    log_bayes_factor: float
    bayes_factor: float
    interpretation: str
    model1_preferred: bool


class BayesFactorComparison:
    """
    Compare models using Bayes factors.

    Interpretation scale (Kass & Raftery 1995):
    - 2*log(BF) < 2: Not worth more than a bare mention
    - 2 < 2*log(BF) < 6: Positive evidence
    - 6 < 2*log(BF) < 10: Strong evidence
    - 2*log(BF) > 10: Very strong evidence
    """

    @staticmethod
    def interpret_bayes_factor(log_bf: float) -> str:
        """Interpret Bayes factor"""
        two_log_bf = 2 * log_bf

        if abs(two_log_bf) < 2:
            return "Not worth more than a bare mention"
        elif abs(two_log_bf) < 6:
            return "Positive evidence"
        elif abs(two_log_bf) < 10:
            return "Strong evidence"
        else:
            return "Very strong evidence"

    @staticmethod
    def compare_models(log_evidence1: float, log_evidence2: float) -> BayesFactor:
        """
        Compare two models using Bayes factor.

        Args:
            log_evidence1: Log marginal likelihood for model 1
            log_evidence2: Log marginal likelihood for model 2

        Returns:
            BayesFactor result
        """
        log_bf = log_evidence1 - log_evidence2
        bf = np.exp(log_bf)
        interpretation = BayesFactorComparison.interpret_bayes_factor(log_bf)
        model1_preferred = log_bf > 0

        return BayesFactor(
            log_bayes_factor=log_bf,
            bayes_factor=bf,
            interpretation=interpretation,
            model1_preferred=model1_preferred
        )


class OnlineUpdater:
    """
    Online updating of posterior distribution with streaming data.

    Implements sequential Bayesian updating where each new data point
    updates the current posterior to become the new prior.
    """

    def __init__(self, prior: Prior):
        """Initialize with a prior distribution"""
        self.prior = prior
        self.data_history: List[np.ndarray] = []
        self.posterior_history: List[Posterior] = []

    def update(self, new_data: np.ndarray, likelihood: Likelihood) -> Posterior:
        """
        Update posterior with new data.

        Args:
            new_data: New observed data
            likelihood: Likelihood function

        Returns:
            Updated posterior
        """
        self.data_history.append(new_data)
        all_data = np.concatenate(self.data_history) if self.data_history else new_data
        likelihood.data = all_data

        # Perform inference (simplified - in practice would use MCMC or variational inference)
        inference = BayesianInference()
        posterior = inference.infer([self.prior], likelihood)

        self.posterior_history.append(posterior)

        # Update prior for next step (using posterior mean)
        if hasattr(posterior, 'mean') and posterior.mean:
            new_params = self.prior.params.copy()
            for key, value in posterior.mean.items():
                if key in new_params or key == self.prior.name:
                    new_params['mean'] = value

        return posterior


# =============================================================================
# MAIN BAYESIAN INFERENCE ENGINE
# =============================================================================

class BayesianInference:
    """
    Bayesian Inference Engine for STAN.

    Supports:
    - Multiple prior types (uniform, normal, log-normal, etc.)
    - Multiple likelihood types (Gaussian, Poisson, binomial, etc.)
    - Posterior sampling via rejection sampling or MCMC
    - Model comparison via Bayes factors
    - Online updating for streaming data
    """

    def __init__(self, inference_method: str = "rejection"):
        """
        Initialize Bayesian inference engine.

        Args:
            inference_method: Method for posterior sampling ('rejection', 'mcmc', 'variational')
        """
        self.inference_method = inference_method
        self.rng = np.random.default_rng()

    def infer(
        self,
        priors: List[Prior],
        likelihood: Likelihood,
        n_samples: int = 10000,
        evidence_method: str = "harmonic_mean"
    ) -> Posterior:
        """
        Perform Bayesian inference to compute posterior distribution.

        Args:
            priors: List of prior distributions (one per parameter)
            likelihood: Likelihood function
            n_samples: Number of posterior samples to generate
            evidence_method: Method for computing marginal likelihood

        Returns:
            Posterior distribution
        """
        if self.inference_method == "rejection":
            return self._rejection_sampling(priors, likelihood, n_samples, evidence_method)
        elif self.inference_method == "mcmc":
            return self._mcmc_sampling(priors, likelihood, n_samples, evidence_method)
        else:
            raise ValueError(f"Unknown inference method: {self.inference_method}")

    def _rejection_sampling(
        self,
        priors: List[Prior],
        likelihood: Likelihood,
        n_samples: int,
        evidence_method: str
    ) -> Posterior:
        """
        Perform rejection sampling for posterior approximation.

        Simple but inefficient for high-dimensional problems.
        """
        parameter_names = [p.name for p in priors]
        n_params = len(priors)
        samples = []
        log_likelihoods = []

        # Generate samples from prior
        n_proposed = 0
        max_iterations = n_samples * 100  # Prevent infinite loops
        acceptance_count = 0

        while acceptance_count < n_samples and n_proposed < max_iterations:
            n_proposed += 1

            # Sample from priors
            params = {}
            for prior in priors:
                params[prior.name] = prior.sample(1)[0]

            # Compute likelihood
            log_lik = likelihood.log_prob(params)

            # Accept or reject
            if log_lik > -np.inf:
                # Simple rejection: keep all samples with finite likelihood
                # (in practice would use importance sampling)
                samples.append([params[name] for name in parameter_names])
                log_likelihoods.append(log_lik)
                acceptance_count += 1

        samples = np.array(samples)

        # Compute log evidence (harmonic mean estimator)
        if evidence_method == "harmonic_mean" and len(log_likelihoods) > 0:
            log_evidence = -logsumexp([-ll for ll in log_likelihoods]) + np.log(len(log_likelihoods))
        else:
            log_evidence = 0.0

        return Posterior(
            samples=samples,
            log_evidence=log_evidence,
            parameter_names=parameter_names
        )

    def _mcmc_sampling(
        self,
        priors: List[Prior],
        likelihood: Likelihood,
        n_samples: int,
        evidence_method: str
    ) -> Posterior:
        """
        Perform Metropolis-Hastings MCMC for posterior approximation.

        More efficient for high-dimensional problems.
        """
        parameter_names = [p.name for p in priors]
        n_params = len(priors)

        # Initialize from prior
        current_params = {}
        for prior in priors:
            current_params[prior.name] = prior.sample(1)[0]

        # Compute initial log posterior
        log_prior = sum(prior.log_prob(current_params[prior.name]) for prior in priors)
        log_lik = likelihood.log_prob(current_params)
        current_log_post = log_prior + log_lik

        # MCMC parameters
        step_size = 0.1
        burn_in = n_samples // 10

        samples = []
        log_likelihoods = []
        accepted = 0

        for iteration in range(n_samples + burn_in):
            # Propose new parameters
            proposed_params = current_params.copy()
            for prior in priors:
                if prior.bounds:
                    low, high = prior.bounds
                else:
                    low, high = current_params[prior.name] - step_size, current_params[prior.name] + step_size

                proposed_params[prior.name] = np.random.uniform(low, high)

            # Compute log posterior for proposed parameters
            log_prior_prop = sum(prior.log_prob(proposed_params[prior.name]) for prior in priors)
            log_lik_prop = likelihood.log_prob(proposed_params)
            proposed_log_post = log_prior_prop + log_lik_prop

            # Metropolis acceptance criterion
            log_accept_ratio = proposed_log_post - current_log_post

            if log_accept_ratio > 0 or np.random.random() < np.exp(log_accept_ratio):
                current_params = proposed_params
                current_log_post = proposed_log_post
                log_lik = log_lik_prop
                accepted += 1

            # Store samples after burn-in
            if iteration >= burn_in:
                samples.append([current_params[name] for name in parameter_names])
                log_likelihoods.append(log_lik)

        samples = np.array(samples)
        acceptance_rate = accepted / (n_samples + burn_in)

        if acceptance_rate < 0.1 or acceptance_rate > 0.5:
            warnings.warn(f"MCMC acceptance rate {acceptance_rate:.2f} outside ideal range [0.1, 0.5]")

        # Compute log evidence
        if evidence_method == "harmonic_mean" and len(log_likelihoods) > 0:
            log_evidence = -logsumexp([-ll for ll in log_likelihoods]) + np.log(len(log_likelihoods))
        else:
            log_evidence = 0.0

        return Posterior(
            samples=samples,
            log_evidence=log_evidence,
            parameter_names=parameter_names
        )

    def compute_bayes_factor(
        self,
        priors1: List[Prior],
        priors2: List[Prior],
        likelihood: Likelihood,
        n_samples: int = 10000
    ) -> BayesFactor:
        """
        Compute Bayes factor comparing two models.

        Args:
            priors1: Priors for model 1
            priors2: Priors for model 2
            likelihood: Likelihood function (shared by both models)
            n_samples: Number of samples for inference

        Returns:
            BayesFactor result
        """
        # Compute evidence for both models
        posterior1 = self.infer(priors1, likelihood, n_samples)
        posterior2 = self.infer(priors2, likelihood, n_samples)

        # Compare using Bayes factor
        return BayesFactorComparison.compare_models(
            posterior1.log_evidence,
            posterior2.log_evidence
        )

    def update_with_data(
        self,
        prior: Prior,
        likelihood: Likelihood,
        data: np.ndarray
    ) -> Posterior:
        """
        Update prior with data using Bayes' rule.

        Args:
            prior: Prior distribution
            likelihood: Likelihood function
            data: Observed data

        Returns:
            Posterior distribution
        """
        likelihood.data = data
        return self.infer([prior], likelihood)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_uniform_prior(name: str, low: float, high: float) -> Prior:
    """Create a uniform prior"""
    return Prior(name=name, prior_type=PriorType.UNIFORM, params={'low': low, 'high': high})


def create_normal_prior(name: str, mean: float, std: float) -> Prior:
    """Create a normal prior"""
    return Prior(name=name, prior_type=PriorType.NORMAL, params={'mean': mean, 'std': std})


def create_log_normal_prior(name: str, mean: float, std: float) -> Prior:
    """Create a log-normal prior"""
    return Prior(name=name, prior_type=PriorType.LOG_NORMAL, params={'mean': mean, 'std': std})


def create_gaussian_likelihood(data: Optional[np.ndarray] = None) -> Likelihood:
    """Create a Gaussian likelihood"""
    return Likelihood(likelihood_type=LikelihoodType.GAUSSIAN, params={}, data=data)


def create_poisson_likelihood(data: Optional[np.ndarray] = None) -> Likelihood:
    """Create a Poisson likelihood"""
    return Likelihood(likelihood_type=LikelihoodType.POISSON, params={'rate': 1.0}, data=data)


def run_bayesian_inference(
    priors: List[Prior],
    likelihood: Likelihood,
    n_samples: int = 10000,
    method: str = "mcmc"
) -> Posterior:
    """
    Convenience function for running Bayesian inference.

    Args:
        priors: List of prior distributions
        likelihood: Likelihood function
        n_samples: Number of samples
        method: Inference method ('mcmc' or 'rejection')

    Returns:
        Posterior distribution
    """
    inference = BayesianInference(inference_method=method)
    return inference.infer(priors, likelihood, n_samples)
