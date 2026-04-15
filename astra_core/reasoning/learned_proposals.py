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
Learned Proposal Distributions for STAN V42

Implements adaptive proposal distributions for MCMC sampling that learn
from past runs to improve future sampling efficiency:

- Problem-type specific proposal learning
- Mixture proposal distributions
- Adaptation during burn-in
- Knowledge transfer between similar problems
- Optimal scaling and correlation learning

This dramatically improves sampling efficiency for astrophysical inference
where parameter degeneracies and multimodality are common.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum
import math
import random
import logging
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

class ProposalType(Enum):
    """Types of proposal distributions."""
    GAUSSIAN = "gaussian"           # Multivariate Gaussian
    STUDENT_T = "student_t"         # Heavy-tailed
    MIXTURE = "mixture"             # Mixture of Gaussians
    DIFFERENTIAL_EVOLUTION = "de"   # DE-MCMC
    AFFINE_INVARIANT = "affine"     # Affine-invariant (emcee-style)
    ADAPTIVE = "adaptive"           # Online adaptation


@dataclass
class ProposalState:
    """Current state of a proposal distribution."""
    type: ProposalType
    parameters: List[str]
    mean: Dict[str, float]
    covariance: Dict[str, Dict[str, float]]
    scale_factor: float
    acceptance_rate: float
    n_samples: int
    n_adaptations: int


@dataclass
class ProposalMemory:
    """Stored proposal parameters from past runs."""
    problem_type: str
    problem_signature: Dict[str, Any]
    proposal_state: ProposalState
    final_acceptance_rate: float
    effective_samples_per_second: float
    timestamp: float
    n_parameters: int


@dataclass
class MixtureComponent:
    """A component of a mixture proposal."""
    weight: float
    mean: Dict[str, float]
    covariance: Dict[str, Dict[str, float]]
    scale: float


@dataclass
class AdaptationConfig:
    """Configuration for proposal adaptation."""
    target_acceptance_rate: float = 0.234  # Optimal for Gaussian proposals
    adaptation_rate: float = 0.1
    min_samples_before_adapt: int = 100
    max_adaptations: int = 1000
    learn_covariance: bool = True
    use_past_runs: bool = True


# ============================================================================
# Proposal Distribution Base
# ============================================================================

class ProposalDistribution:
    """
    Base class for proposal distributions.
    """

    def __init__(self,
                 parameters: List[str],
                 bounds: Dict[str, Tuple[float, float]]):
        self.parameters = parameters
        self.bounds = bounds
        self.n_dim = len(parameters)

        # Statistics
        self.n_proposed = 0
        self.n_accepted = 0
        self.acceptance_history: List[float] = []

    def propose(self, current: Dict[str, float]) -> Dict[str, float]:
        """Generate proposal from current state."""
        raise NotImplementedError

    def log_proposal_ratio(self,
                          current: Dict[str, float],
                          proposed: Dict[str, float]) -> float:
        """Log ratio for asymmetric proposals: log q(current|proposed) - log q(proposed|current)"""
        return 0.0  # Symmetric by default

    def update_acceptance(self, accepted: bool):
        """Update acceptance statistics."""
        self.n_proposed += 1
        if accepted:
            self.n_accepted += 1

    def get_acceptance_rate(self) -> float:
        """Get current acceptance rate."""
        if self.n_proposed == 0:
            return 0.0
        return self.n_accepted / self.n_proposed

    def get_state(self) -> ProposalState:
        """Get current proposal state."""
        raise NotImplementedError


# ============================================================================
# Gaussian Proposal
# ============================================================================

class GaussianProposal(ProposalDistribution):
    """
    Multivariate Gaussian proposal distribution.
    """

    def __init__(self,
                 parameters: List[str],
                 bounds: Dict[str, Tuple[float, float]],
                 initial_scale: Optional[float] = None,
                 initial_covariance: Optional[Dict[str, Dict[str, float]]] = None):
        super().__init__(parameters, bounds)

        # Initialize scale
        if initial_scale is None:
            # Roberts & Rosenthal optimal scaling
            self.scale = 2.38 / math.sqrt(self.n_dim)
        else:
            self.scale = initial_scale

        # Initialize covariance
        if initial_covariance is None:
            # Diagonal with range-based variance
            self.covariance = {}
            for p in parameters:
                self.covariance[p] = {}
                for q in parameters:
                    if p == q:
                        rng = bounds[p][1] - bounds[p][0]
                        self.covariance[p][q] = (rng / 10) ** 2
                    else:
                        self.covariance[p][q] = 0.0
        else:
            self.covariance = initial_covariance

        # Cholesky decomposition (for sampling)
        self._update_cholesky()

    def _update_cholesky(self):
        """Update Cholesky decomposition of covariance."""
        n = self.n_dim

        # Build matrix
        matrix = [[self.covariance[self.parameters[i]][self.parameters[j]]
                  for j in range(n)] for i in range(n)]

        # Simple Cholesky decomposition
        self.cholesky = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i + 1):
                if i == j:
                    sum_sq = sum(self.cholesky[i][k] ** 2 for k in range(j))
                    val = matrix[i][i] - sum_sq
                    self.cholesky[i][j] = math.sqrt(max(1e-10, val))
                else:
                    sum_prod = sum(self.cholesky[i][k] * self.cholesky[j][k]
                                  for k in range(j))
                    if self.cholesky[j][j] > 0:
                        self.cholesky[i][j] = (matrix[i][j] - sum_prod) / self.cholesky[j][j]
                    else:
                        self.cholesky[i][j] = 0.0

    def propose(self, current: Dict[str, float]) -> Dict[str, float]:
        """Generate Gaussian proposal."""
        # Sample standard normal
        z = [random.gauss(0, 1) for _ in range(self.n_dim)]

        # Transform by Cholesky
        y = [0.0] * self.n_dim
        for i in range(self.n_dim):
            y[i] = sum(self.cholesky[i][j] * z[j] for j in range(i + 1))

        # Apply scale and add to current
        proposed = {}
        for i, p in enumerate(self.parameters):
            proposed[p] = current[p] + self.scale * y[i]

            # Reflect at bounds
            low, high = self.bounds[p]
            while proposed[p] < low or proposed[p] > high:
                if proposed[p] < low:
                    proposed[p] = 2 * low - proposed[p]
                if proposed[p] > high:
                    proposed[p] = 2 * high - proposed[p]

        return proposed

    def adapt_scale(self, target_rate: float = 0.234, rate: float = 0.1):
        """Adapt scale factor based on acceptance rate."""
        current_rate = self.get_acceptance_rate()

        if self.n_proposed < 50:
            return

        # Log-linear adaptation
        log_scale = math.log(self.scale)
        log_scale += rate * (current_rate - target_rate)

        # Bounds on scale
        self.scale = math.exp(max(-5, min(5, log_scale)))

    def adapt_covariance(self, samples: List[Dict[str, float]], rate: float = 0.1):
        """Adapt covariance from samples."""
        n = len(samples)
        if n < 2 * self.n_dim:
            return

        # Compute sample covariance
        means = {p: sum(s[p] for s in samples) / n for p in self.parameters}

        sample_cov = {p: {q: 0.0 for q in self.parameters} for p in self.parameters}

        for s in samples:
            for p in self.parameters:
                for q in self.parameters:
                    sample_cov[p][q] += (s[p] - means[p]) * (s[q] - means[q])

        for p in self.parameters:
            for q in self.parameters:
                sample_cov[p][q] /= (n - 1)

        # Blend with current covariance
        for p in self.parameters:
            for q in self.parameters:
                self.covariance[p][q] = ((1 - rate) * self.covariance[p][q] +
                                         rate * sample_cov[p][q])

        # Regularize diagonal
        for p in self.parameters:
            self.covariance[p][p] = max(1e-10, self.covariance[p][p])

        self._update_cholesky()

    def get_state(self) -> ProposalState:
        """Get current proposal state."""
        means = {p: (self.bounds[p][0] + self.bounds[p][1]) / 2 for p in self.parameters}

        return ProposalState(
            type=ProposalType.GAUSSIAN,
            parameters=self.parameters.copy(),
            mean=means,
            covariance={p: self.covariance[p].copy() for p in self.parameters},
            scale_factor=self.scale,
            acceptance_rate=self.get_acceptance_rate(),
            n_samples=self.n_proposed,
            n_adaptations=0
        )


# ============================================================================
# Mixture Proposal
# ============================================================================

class MixtureProposal(ProposalDistribution):
    """
    Mixture of Gaussians proposal for multimodal posteriors.
    """

    def __init__(self,
                 parameters: List[str],
                 bounds: Dict[str, Tuple[float, float]],
                 n_components: int = 3):
        super().__init__(parameters, bounds)

        self.n_components = n_components
        self.components: List[MixtureComponent] = []

        # Initialize with spread components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize mixture components."""
        self.components = []

        for i in range(self.n_components):
            # Spread means across parameter space
            mean = {}
            for p in self.parameters:
                low, high = self.bounds[p]
                frac = (i + 0.5) / self.n_components
                mean[p] = low + frac * (high - low)

            # Diagonal covariance
            covariance = {}
            for p in self.parameters:
                covariance[p] = {}
                for q in self.parameters:
                    if p == q:
                        rng = self.bounds[p][1] - self.bounds[p][0]
                        covariance[p][q] = (rng / (2 * self.n_components)) ** 2
                    else:
                        covariance[p][q] = 0.0

            component = MixtureComponent(
                weight=1.0 / self.n_components,
                mean=mean,
                covariance=covariance,
                scale=2.38 / math.sqrt(self.n_dim)
            )
            self.components.append(component)

    def propose(self, current: Dict[str, float]) -> Dict[str, float]:
        """Generate proposal from mixture."""
        # Select component
        r = random.random()
        cumsum = 0.0
        selected = self.components[0]

        for comp in self.components:
            cumsum += comp.weight
            if r < cumsum:
                selected = comp
                break

        # Sample from selected Gaussian
        z = [random.gauss(0, 1) for _ in range(self.n_dim)]

        # Cholesky of selected component (simplified diagonal)
        proposed = {}
        for i, p in enumerate(self.parameters):
            std = math.sqrt(selected.covariance[p][p])
            proposed[p] = current[p] + selected.scale * std * z[i]

            # Reflect at bounds
            low, high = self.bounds[p]
            while proposed[p] < low or proposed[p] > high:
                if proposed[p] < low:
                    proposed[p] = 2 * low - proposed[p]
                if proposed[p] > high:
                    proposed[p] = 2 * high - proposed[p]

        return proposed

    def update_components(self, samples: List[Dict[str, float]], weights: Optional[List[float]] = None):
        """
        Update mixture components using EM-like procedure.
        """
        n = len(samples)
        if n < 10 * self.n_components:
            return

        if weights is None:
            weights = [1.0 / n] * n

        # E-step: assign samples to components
        responsibilities = [[0.0] * self.n_components for _ in range(n)]

        for i, sample in enumerate(samples):
            total_resp = 0.0

            for k, comp in enumerate(self.components):
                # Gaussian likelihood (simplified)
                log_prob = 0.0
                for p in self.parameters:
                    std = math.sqrt(comp.covariance[p][p])
                    diff = sample[p] - comp.mean[p]
                    log_prob -= 0.5 * (diff / std) ** 2 - math.log(std)

                responsibilities[i][k] = comp.weight * math.exp(log_prob)
                total_resp += responsibilities[i][k]

            if total_resp > 0:
                for k in range(self.n_components):
                    responsibilities[i][k] /= total_resp

        # M-step: update components
        for k, comp in enumerate(self.components):
            # Effective count
            n_k = sum(weights[i] * responsibilities[i][k] for i in range(n))

            if n_k < 1:
                continue

            # Update weight
            comp.weight = n_k / sum(weights)

            # Update mean
            for p in self.parameters:
                comp.mean[p] = sum(weights[i] * responsibilities[i][k] * samples[i][p]
                                  for i in range(n)) / n_k

            # Update covariance (diagonal only)
            for p in self.parameters:
                var = sum(weights[i] * responsibilities[i][k] * (samples[i][p] - comp.mean[p]) ** 2
                         for i in range(n)) / n_k
                comp.covariance[p][p] = max(1e-10, var)

        # Normalize weights
        total_weight = sum(comp.weight for comp in self.components)
        for comp in self.components:
            comp.weight /= total_weight

    def get_state(self) -> ProposalState:
        """Get current proposal state."""
        # Return state of dominant component
        dominant = max(self.components, key=lambda c: c.weight)

        return ProposalState(
            type=ProposalType.MIXTURE,
            parameters=self.parameters.copy(),
            mean=dominant.mean.copy(),
            covariance={p: dominant.covariance[p].copy() for p in self.parameters},
            scale_factor=dominant.scale,
            acceptance_rate=self.get_acceptance_rate(),
            n_samples=self.n_proposed,
            n_adaptations=0
        )


# ============================================================================
# Differential Evolution Proposal
# ============================================================================

class DifferentialEvolutionProposal(ProposalDistribution):
    """
    Differential evolution proposal for MCMC.
    Uses chain history for proposals.
    """

    def __init__(self,
                 parameters: List[str],
                 bounds: Dict[str, Tuple[float, float]],
                 gamma: float = 2.38,
                 b: float = 0.001):
        super().__init__(parameters, bounds)

        self.gamma = gamma / math.sqrt(2 * self.n_dim)
        self.b = b  # Small perturbation

        # Chain history for DE proposals
        self.chain_history: List[Dict[str, float]] = []
        self.max_history = 10000

    def propose(self, current: Dict[str, float]) -> Dict[str, float]:
        """Generate DE proposal."""
        if len(self.chain_history) < 10:
            # Fall back to random walk
            proposed = {}
            for p in self.parameters:
                rng = self.bounds[p][1] - self.bounds[p][0]
                proposed[p] = current[p] + random.gauss(0, rng / 100)
                proposed[p] = max(self.bounds[p][0], min(self.bounds[p][1], proposed[p]))
            return proposed

        # Select two random chain states
        idx1, idx2 = random.sample(range(len(self.chain_history)), 2)
        state1 = self.chain_history[idx1]
        state2 = self.chain_history[idx2]

        # DE proposal
        proposed = {}
        for p in self.parameters:
            diff = state1[p] - state2[p]
            noise = random.gauss(0, self.b)
            proposed[p] = current[p] + self.gamma * diff + noise

            # Reflect at bounds
            low, high = self.bounds[p]
            while proposed[p] < low or proposed[p] > high:
                if proposed[p] < low:
                    proposed[p] = 2 * low - proposed[p]
                if proposed[p] > high:
                    proposed[p] = 2 * high - proposed[p]

        return proposed

    def add_to_history(self, state: Dict[str, float]):
        """Add state to chain history."""
        self.chain_history.append(state.copy())

        if len(self.chain_history) > self.max_history:
            self.chain_history.pop(0)

    def get_state(self) -> ProposalState:
        """Get current proposal state."""
        # Compute covariance from history
        covariance = {p: {q: 0.0 for q in self.parameters} for p in self.parameters}

        if len(self.chain_history) > 10:
            means = {p: sum(s[p] for s in self.chain_history) / len(self.chain_history)
                    for p in self.parameters}

            for s in self.chain_history:
                for p in self.parameters:
                    for q in self.parameters:
                        covariance[p][q] += (s[p] - means[p]) * (s[q] - means[q])

            n = len(self.chain_history)
            for p in self.parameters:
                for q in self.parameters:
                    covariance[p][q] /= (n - 1)
        else:
            for p in self.parameters:
                rng = self.bounds[p][1] - self.bounds[p][0]
                covariance[p][p] = (rng / 10) ** 2

        means = {p: sum(s[p] for s in self.chain_history) / len(self.chain_history)
                if self.chain_history else (self.bounds[p][0] + self.bounds[p][1]) / 2
                for p in self.parameters}

        return ProposalState(
            type=ProposalType.DIFFERENTIAL_EVOLUTION,
            parameters=self.parameters.copy(),
            mean=means,
            covariance=covariance,
            scale_factor=self.gamma,
            acceptance_rate=self.get_acceptance_rate(),
            n_samples=self.n_proposed,
            n_adaptations=0
        )


# ============================================================================
# Proposal Memory Bank
# ============================================================================

class ProposalMemoryBank:
    """
    Stores and retrieves learned proposals from past runs.
    """

    def __init__(self, memory_file: Optional[str] = None):
        self.memories: List[ProposalMemory] = []
        self.memory_file = memory_file
