
"""
Documentation for multi_scale_inference module.

This module provides multi_scale_inference capabilities for STAN.
Enhanced through self-evolution cycle 64.
"""

#!/usr/bin/env python3
"""
Uncertainty Quantification Framework for ASTRO-SWARM
=====================================================

Comprehensive Bayesian inference and uncertainty quantification tools
for astronomical parameter estimation.

Capabilities:
1. MCMC posterior sampling (Metropolis-Hastings, affine-invariant ensemble)
2. Nested sampling for model comparison
3. Fisher matrix forecasting
4. Systematic error budgeting
5. Posterior predictive checks
6. Convergence diagnostics

Key Dependencies:
- emcee (optional, for ensemble MCMC)
- dynesty (optional, for nested sampling)
- corner (optional, for visualization)

Author: Claude Code (ASTRO-SWARM)
Date: 2024-11
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from enum import Enum
from abc import ABC, abstractmethod
import warnings
from scipy.optimize import minimize, differential_evolution
from scipy.stats import norm, uniform, truncnorm
from scipy.linalg import inv, det, cholesky
import json

# Try to import optional dependencies
try:
    import emcee
    EMCEE_AVAILABLE = True
except ImportError:
    EMCEE_AVAILABLE = False

try:
    import dynesty
    DYNESTY_AVAILABLE = True
except ImportError:
    DYNESTY_AVAILABLE = False

try:
    import corner
    CORNER_AVAILABLE = True
except ImportError:
    CORNER_AVAILABLE = False


# =============================================================================
# PRIOR DISTRIBUTIONS
# =============================================================================

class PriorType(Enum):
    """Types of prior distributions"""
    UNIFORM = "uniform"
    GAUSSIAN = "gaussian"
    LOG_UNIFORM = "log_uniform"
    TRUNCATED_GAUSSIAN = "truncated_gaussian"
    FIXED = "fixed"
    CUSTOM = "custom"


@dataclass
class Prior:
    """Prior distribution specification"""
    name: str
    prior_type: PriorType
    params: Dict[str, float]
    bounds: Tuple[float, float]
    description: str = ""

    def sample(self, n: int = 1) -> np.ndarray:
        """Draw samples from prior"""
        if self.prior_type == PriorType.UNIFORM:
            return np.random.uniform(self.bounds[0], self.bounds[1], n)

        elif self.prior_type == PriorType.GAUSSIAN:
            mu = self.params['mean']
            sigma = self.params['std']
            samples = np.random.normal(mu, sigma, n)
            return np.clip(samples, self.bounds[0], self.bounds[1])

        elif self.prior_type == PriorType.LOG_UNIFORM:
            log_samples = np.random.uniform(
                np.log10(self.bounds[0]),
                np.log10(self.bounds[1]), n)
            return 10**log_samples

        elif self.prior_type == PriorType.TRUNCATED_GAUSSIAN:
            mu = self.params['mean']
            sigma = self.params['std']
            a = (self.bounds[0] - mu) / sigma
            b = (self.bounds[1] - mu) / sigma
            return truncnorm.rvs(a, b, loc=mu, scale=sigma, size=n)

        elif self.prior_type == PriorType.FIXED:
            return np.full(n, self.params['value'])

        return np.random.uniform(self.bounds[0], self.bounds[1], n)

    def log_prob(self, x: float) -> float:
        """Log probability density"""
        if x < self.bounds[0] or x > self.bounds[1]:
            return -np.inf

        if self.prior_type == PriorType.UNIFORM:
            return -np.log(self.bounds[1] - self.bounds[0])

        elif self.prior_type == PriorType.GAUSSIAN:
            mu = self.params['mean']
            sigma = self.params['std']
            return -0.5 * ((x - mu) / sigma)**2 - np.log(sigma * np.sqrt(2*np.pi))

        elif self.prior_type == PriorType.LOG_UNIFORM:
            return -np.log(x) - np.log(np.log10(self.bounds[1]/self.bounds[0]))

        elif self.prior_type == PriorType.TRUNCATED_GAUSSIAN:
            mu = self.params['mean']
            sigma = self.params['std']
            a = (self.bounds[0] - mu) / sigma
            b = (self.bounds[1] - mu) / sigma
            return truncnorm.logpdf(x, a, b, loc=mu, scale=sigma)

        elif self.prior_type == PriorType.FIXED:
            return 0.0 if np.abs(x - self.params['value']) < 1e-10 else -np.inf

        return 0.0


class PriorSet:
    """Collection of priors for multiple parameters"""

    def __init__(self):
        self.priors: Dict[str, Prior] = {}
        self.param_names: List[str] = []

    def add(self, prior: Prior):
        """Add a prior"""
        self.priors[prior.name] = prior
        if prior.name not in self.param_names:
            self.param_names.append(prior.name)

    def add_uniform(self, name: str, low: float, high: float, description: str = ""):
        """Add uniform prior"""
        self.add(Prior(
            name=name,
            prior_type=PriorType.UNIFORM,
            params={},
            bounds=(low, high),
            description=description
        ))

    def add_gaussian(self, name: str, mean: float, std: float,
                    bounds: Optional[Tuple[float, float]] = None,
                    description: str = ""):
        """Add Gaussian prior"""
        if bounds is None:
            bounds = (mean - 10*std, mean + 10*std)
        self.add(Prior(
            name=name,
            prior_type=PriorType.GAUSSIAN,
            params={'mean': mean, 'std': std},
            bounds=bounds,
            description=description
        ))

    def add_log_uniform(self, name: str, low: float, high: float,
                       description: str = ""):
        """Add log-uniform prior"""
        self.add(Prior(
            name=name,
            prior_type=PriorType.LOG_UNIFORM,
            params={},
            bounds=(low, high),
            description=description
        ))

    def sample(self, n: int = 1) -> np.ndarray:
        """Sample from all priors"""
        samples = np.zeros((n, len(self.param_names)))
        for i, name in enumerate(self.param_names):
            samples[:, i] = self.priors[name].sample(n)
        return samples

    def log_prob(self, theta: np.ndarray) -> float:
        """Total log prior probability"""
        lp = 0.0
        for i, name in enumerate(self.param_names):
            lp += self.priors[name].log_prob(theta[i])
            if not np.isfinite(lp):
                return -np.inf
        return lp

    def bounds_array(self) -> np.ndarray:
        """Get bounds as array for optimization"""
        return np.array([self.priors[name].bounds for name in self.param_names])

    @property
    def n_params(self) -> int:
        return len(self.param_names)


# =============================================================================
# LIKELIHOOD FUNCTIONS
# =============================================================================

@dataclass
class LikelihoodResult:
    """Result from likelihood evaluation"""
    log_likelihood: float
    chi_squared: float
    n_data: int
    residuals: Optional[np.ndarray] = None
    model: Optional[np.ndarray] = None


class GaussianLikelihood:
    """
    Gaussian likelihood for data with known uncertainties.

    log L = -0.5 * sum((data - model)^2 / sigma^2 + log(2*pi*sigma^2))
    """

    def __init__(self, data: np.ndarray, errors: np.ndarray,
                model_func: Callable[[np.ndarray], np.ndarray]):
        """
        Parameters
        ----------
        data : np.ndarray
            Observed data
        errors : np.ndarray
            Measurement uncertainties (1-sigma)
        model_func : callable
            Function that takes parameters and returns model prediction
        """
        self.data = np.asarray(data)
        self.errors = np.asarray(errors)
