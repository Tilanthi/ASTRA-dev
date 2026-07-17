"""
Bayesian Swarm Inference (Sequential Monte Carlo) for ASTRA.

A swarm of particles anneals from the prior to the posterior through a
temperature ladder beta: 0 (prior) -> 1 (full posterior), using importance
reweighting, effective-sample-size (ESS) resampling, and Metropolis-Hastings
rejuvenation moves. Returns posterior samples and the model evidence
(marginal likelihood) -- the natural quantities for Bayesian model comparison
in a discovery system.

References:
  Del Moral, Doucet & Jasra (2006), "Sequential Monte Carlo samplers",
    JRSS B 68, 411.
  Chopin (2002), "A sequential particle filter method for static models",
    JASA 97, 1363.
  Doucet & Johansen (2009), "A tutorial on particle filtering and smoothing".
"""

import numpy as np
from dataclasses import dataclass
from typing import Callable, Optional, List


@dataclass
class InferenceResult:
    """Outcome of a swarm-inference run."""
    samples: np.ndarray               # (N, dim) posterior particle ensemble
    log_evidence: float               # log marginal likelihood log Z
    posterior_mean: np.ndarray        # (dim,)
    posterior_cov: np.ndarray         # (dim, dim)
    ess_history: List[float]          # ESS after each tempering step
    beta_history: List[float]         # inverse-temperature ladder used
    n_particles: int


class BayesianSwarmInference:
    """Sequential Monte Carlo (particle-swarm) Bayesian inference.

    Args:
        log_likelihood: callable(theta) -> float (log L; need not be normalised)
        log_prior:      callable(theta) -> float (log prior density)
        prior_sampler:  callable(rng, n) -> (n, dim) array of prior draws
        n_dim:          parameter dimension
        n_particles:    swarm size
        proposal_scale: MH rejuvenation proposal sigma (scalar or per-dim)
        seed:           RNG seed
    """

    def __init__(self, log_likelihood: Callable, log_prior: Callable,
                 prior_sampler: Callable, n_dim: int, n_particles: int = 500,
                 proposal_scale=None, seed: Optional[int] = None):
        self.loglik = log_likelihood
        self.logprior = log_prior
        self.prior_sampler = prior_sampler
        self.n_dim = n_dim
        self.N = n_particles
        self.rng = np.random.default_rng(seed)
        self.scale = (np.ones(n_dim) * 0.5 if proposal_scale is None
                      else np.asarray(proposal_scale, float))

    def _target_logdens(self, theta, beta: float) -> float:
        """Tempered target log density: log prior + beta * log likelihood."""
        lp = self.logprior(theta)
        if not np.isfinite(lp):
            return -np.inf
        return lp + beta * self.loglik(theta)

    def _rejuvenate(self, particles, beta: float, n_steps: int):
        """Metropolis-Hastings moves targeting the tempered posterior."""
        for _ in range(n_steps):
            for i in range(len(particles)):
                prop = particles[i] + self.scale * self.rng.standard_normal(self.n_dim)
                log_acc = (self._target_logdens(prop, beta)
                           - self._target_logdens(particles[i], beta))
                if np.log(self.rng.random()) < log_acc:
                    particles[i] = prop
        return particles

    @staticmethod
    def _systematic_resample(particles, weights, rng):
        n = len(particles)
        positions = (rng.random() + np.arange(n)) / n
        cum = np.cumsum(weights)
        cum[-1] = 1.0
        idx = np.clip(np.searchsorted(cum, positions), 0, n - 1)
        return particles[idx].copy()

    def run(self, ess_threshold: float = 0.5, rejuvenation_steps: int = 3,
            max_beta: float = 1.0) -> InferenceResult:
        N, dim = self.N, self.n_dim
        particles = np.asarray(self.prior_sampler(self.rng, N), float)
        logL = np.array([self.loglik(p) for p in particles])
        beta = 0.0
        logZ = 0.0
        ess_history: List[float] = []
        beta_history = [0.0]
        guard = 0
        while beta < max_beta - 1e-6 and guard < 1000:
            guard += 1
            logLc = logL - logL.max()                       # stabilise

            def ess_of(delta):
                w = np.exp(delta * logLc)
                return float((w.sum() ** 2) / (w ** 2).sum())

            # adaptive step: largest delta keeping ESS >= threshold * N
            hi = max_beta - beta
            if ess_of(hi) >= ess_threshold * N:
                delta = hi
            else:
                lo = 0.0
                for _ in range(50):
                    mid = 0.5 * (lo + hi)
                    if ess_of(mid) >= ess_threshold * N:
                        lo = mid
                    else:
                        hi = mid
                delta = lo
            if delta < 1e-9:
                delta = max_beta - beta
            new_beta = min(beta + delta, max_beta)

            # evidence increment: log mean(exp(delta * logL)) (stable form)
            logZ += delta * logL.max() + np.log(np.mean(np.exp(delta * logLc)))

            w = np.exp(delta * logLc)
            w /= w.sum()
            ess_history.append(1.0 / np.sum(w ** 2))
            particles = self._systematic_resample(particles, w, self.rng)
            logL = np.array([self.loglik(p) for p in particles])
            beta = new_beta
            beta_history.append(beta)
            particles = self._rejuvenate(particles, beta, rejuvenation_steps)
            logL = np.array([self.loglik(p) for p in particles])

        pm = particles.mean(axis=0)
        if dim > 1:
            pcov = np.cov(particles.T)
        else:
            pcov = np.array([[particles[:, 0].std() ** 2]])
        return InferenceResult(samples=particles, log_evidence=float(logZ),
                               posterior_mean=pm, posterior_cov=np.atleast_2d(pcov),
                               ess_history=ess_history, beta_history=beta_history,
                               n_particles=N)


__all__ = ['BayesianSwarmInference', 'InferenceResult']
