
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


# =============================================================================
# Sampling algorithms (Metropolis-Hastings, affine-invariant ensemble,
# nested sampling) and Fisher-matrix forecasting.
# =============================================================================

def _logsubexp(a: float, b: float) -> float:
    """log(exp(a) - exp(b)) for a > b, numerically stable."""
    return a + np.log1p(-np.exp(b - a))


class MetropolisHastings:
    """Random-walk Metropolis-Hastings MCMC.

    Args:
        log_posterior: callable(params) -> log posterior (unnormalised)
        n_dim: parameter dimension
        proposal_cov: (n_dim, n_dim) proposal covariance
    """

    def __init__(self, log_posterior, n_dim: int, proposal_cov=None, seed=None):
        self.log_post = log_posterior
        self.n_dim = n_dim
        self.cov = np.eye(n_dim) * 1e-2 if proposal_cov is None else np.asarray(proposal_cov, float)
        self.rng = np.random.default_rng(seed)
        self.accept_rate = 0.0

    def sample(self, x0, n_samples: int, burn_in: int = 1000) -> np.ndarray:
        x = np.asarray(x0, float)
        lp = self.log_post(x)
        L = np.linalg.cholesky(self.cov)
        chain = np.empty((n_samples, self.n_dim))
        n_acc = 0
        n_total = n_samples + burn_in
        for i in range(n_total):
            prop = x + L @ self.rng.standard_normal(self.n_dim)
            lp_prop = self.log_post(prop)
            if np.log(self.rng.random()) < lp_prop - lp:
                x, lp = prop, lp_prop
                if i >= burn_in:
                    n_acc += 1
            if i >= burn_in:
                chain[i - burn_in] = x
        self.accept_rate = n_acc / n_samples
        return chain


class EnsembleSampler:
    """Affine-invariant ensemble sampler (Goodman & Weare 2010; emcee stretch move).

    Args:
        log_posterior: callable(params) -> log posterior
        n_dim: parameter dimension
        n_walkers: number of walkers (>= 2*n_dim)
    """

    def __init__(self, log_posterior, n_dim: int, n_walkers=None, seed=None):
        self.log_post = log_posterior
        self.n_dim = n_dim
        self.n_walkers = n_walkers or max(2 * n_dim, 4)
        if self.n_walkers < 2 * n_dim:
            raise ValueError("n_walkers must be >= 2*n_dim for the stretch move")
        self.rng = np.random.default_rng(seed)
        self.accept_rate = 0.0

    def sample(self, p0, n_steps: int) -> np.ndarray:
        p = np.array(p0, float)              # (n_walkers, n_dim)
        W = self.n_walkers
        logp = np.array([self.log_post(pi) for pi in p])
        chain = np.empty((n_steps, W, self.n_dim))
        a = 2.0
        n_acc = 0
        for k in range(n_steps):
            for i in range(W):
                j = self.rng.integers(0, W)
                while j == i:
                    j = self.rng.integers(0, W)
                z = ((a - 1.0) * self.rng.random() + 1.0) ** 2 / a
                prop = p[j] + z * (p[i] - p[j])
                lp_prop = self.log_post(prop)
                log_accept = (self.n_dim - 1) * np.log(z) + lp_prop - logp[i]
                if np.log(self.rng.random()) < log_accept:
                    p[i], logp[i] = prop, lp_prop
                    n_acc += 1
            chain[k] = p
        self.accept_rate = n_acc / (n_steps * W)
        return chain


class NestedSampler:
    """Basic nested sampling (Skilling 2004) for the Bayesian evidence.

    Args:
        log_likelihood: callable(params) -> log likelihood
        prior_transform: callable(u in unit cube) -> params
        n_dim: parameter dimension
        n_active: number of live points
    """

    def __init__(self, log_likelihood, prior_transform, n_dim: int,
                 n_active: int = 50, seed=None):
        self.loglike = log_likelihood
        self.prior_transform = prior_transform
        self.n_dim = n_dim
        self.n_active = n_active
        self.rng = np.random.default_rng(seed)

    def _draw_above(self, logL_min):
        for _ in range(10000):
            u = self.rng.random(self.n_dim)
            p = self.prior_transform(u)
            if self.loglike(p) > logL_min:
                return p
        return self.prior_transform(self.rng.random(self.n_dim))

    def sample(self, n_iter: int = 1000) -> Dict[str, Any]:
        u0 = self.rng.random((self.n_active, self.n_dim))
        active = np.array([self.prior_transform(ui) for ui in u0])
        logL = np.array([self.loglike(p) for p in active])
        logX = 0.0
        logZ = -np.inf
        samples = np.empty((n_iter, self.n_dim))
        for i in range(n_iter):
            worst = int(np.argmin(logL))
            logLstar = float(logL[worst])
            logX_old = logX
            logX -= self.rng.exponential(1.0 / self.n_active)   # shrink prior volume
            logZ = np.logaddexp(logZ, logLstar + _logsubexp(logX_old, logX))
            samples[i] = active[worst]
            new = self._draw_above(logLstar)
            active[worst] = new
            logL[worst] = self.loglike(new)
        # final live-point contribution
        logLmax = float(np.max(logL))
        logZ = np.logaddexp(logZ, logLmax + logX)
        return {'log_evidence': float(logZ), 'samples': samples,
                'active_points': active}


class FisherMatrix:
    """Fisher information matrix forecasting for Gaussian data.

    F = J^T C^-1 J, where J = d(model)/d(params) (n_data x n_params) and
    C is the data covariance. Parameter covariance = F^-1.

    Args:
        jacobian_func: callable(params) -> (n_data, n_params) Jacobian matrix
        covariance: (n_data, n_data) data covariance
    """

    def __init__(self, jacobian_func, covariance):
        self.jac = jacobian_func
        self.C = np.asarray(covariance, float)

    def at(self, params) -> np.ndarray:
        J = np.atleast_2d(self.jac(params))
        Cinv = inv(self.C)
        return J.T @ Cinv @ J

    def covariance(self, params) -> np.ndarray:
        return inv(self.at(params))

    def uncertainties(self, params) -> np.ndarray:
        """1-sigma parameter uncertainties (sqrt of diagonal of F^-1)."""
        return np.sqrt(np.diag(self.covariance(params)))
