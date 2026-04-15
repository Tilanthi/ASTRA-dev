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
Nested Sampling with Dynamic Allocation for STAN V42

Implements advanced nested sampling with:
- Dynamic live point allocation based on posterior complexity
- Multi-modal posterior detection and handling
- Evidence calculation with error estimates
- Automatic stopping criteria
- Integration with swarm exploration

Nested sampling is particularly powerful for:
- Model comparison via Bayesian evidence
- Multi-modal posteriors in astrophysics (e.g., lens parameter degeneracies)
- Robust uncertainty quantification
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum
import math
import random
import numpy as np
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

class SamplingPhase(Enum):
    """Phases of nested sampling."""
    EXPLORATION = "exploration"  # Initial broad exploration
    REFINEMENT = "refinement"    # Focus on high-likelihood regions
    CONVERGENCE = "convergence"  # Final convergence check
    COMPLETE = "complete"


@dataclass
class LivePoint:
    """A single live point in nested sampling."""
    parameters: Dict[str, float]
    log_likelihood: float
    log_prior: float
    birth_iteration: int
    cluster_id: Optional[int] = None

    @property
    def log_posterior(self) -> float:
        return self.log_likelihood + self.log_prior


@dataclass
class DeadPoint:
    """A dead point (replaced from live set)."""
    parameters: Dict[str, float]
    log_likelihood: float
    log_prior: float
    log_weight: float  # log(X_i - X_{i+1}) + log_likelihood
    iteration: int


@dataclass
class Cluster:
    """A cluster of live points (for multi-modal handling)."""
    cluster_id: int
    center: Dict[str, float]
    covariance: Dict[str, Dict[str, float]]
    n_points: int
    log_likelihood_range: Tuple[float, float]


@dataclass
class NestedSamplingResult:
    """Complete result from nested sampling."""
    log_evidence: float
    log_evidence_error: float
    posterior_samples: List[Dict[str, float]]
    posterior_weights: List[float]
    parameter_means: Dict[str, float]
    parameter_stds: Dict[str, float]
    n_iterations: int
    n_likelihood_calls: int
    n_clusters_detected: int
    information_gain: float  # H = log(Z) - <log L>
    effective_sample_size: float
    converged: bool
    convergence_reason: str


@dataclass
class SamplingState:
    """Current state of nested sampling run."""
    live_points: List[LivePoint]
    dead_points: List[DeadPoint]
    log_evidence: float
    log_evidence_squared: float  # For error estimation
    iteration: int
    n_likelihood_calls: int
    phase: SamplingPhase
    clusters: List[Cluster]
    target_n_live: int
    log_remaining_prior: float  # log(X) - remaining prior volume


# ============================================================================
# Dynamic Live Point Allocator
# ============================================================================

class DynamicLivePointAllocator:
    """
    Dynamically adjusts the number of live points based on
    posterior complexity and convergence requirements.
    """

    def __init__(self,
                 min_live_points: int = 50,
                 max_live_points: int = 2000,
                 target_efficiency: float = 0.5):
        self.min_live_points = min_live_points
        self.max_live_points = max_live_points
        self.target_efficiency = target_efficiency

        # History for adaptation
        self.efficiency_history: List[float] = []
        self.cluster_history: List[int] = []
        self.gradient_history: List[float] = []

    def compute_target_live_points(self,
                                   state: SamplingState,
                                   evidence_threshold: float = 0.1) -> int:
        """
        Compute optimal number of live points for current phase.

        Factors considered:
        - Number of detected modes (more modes = more points)
        - Evidence uncertainty (high uncertainty = more points)
        - Likelihood gradient (steep = more points for resolution)
        - Remaining prior volume (small = fewer points needed)
        """
        n_clusters = max(1, len(state.clusters))

        # Base allocation per cluster
        base_per_cluster = self.min_live_points
        cluster_allocation = base_per_cluster * n_clusters

        # Evidence uncertainty scaling
        if state.iteration > 10:
            # Estimate evidence error from current state
            log_evidence_var = self._estimate_evidence_variance(state)
            evidence_error = math.sqrt(log_evidence_var) if log_evidence_var > 0 else 1.0

            if evidence_error > evidence_threshold:
                # Need more points for accuracy
                error_scaling = min(2.0, evidence_error / evidence_threshold)
                cluster_allocation = int(cluster_allocation * error_scaling)

        # Likelihood gradient scaling
        if len(state.dead_points) >= 10:
            gradient = self._compute_likelihood_gradient(state)
            self.gradient_history.append(gradient)

            # Steep gradients need more points
            if gradient > 10.0:
                gradient_scaling = min(1.5, 1.0 + gradient / 50.0)
                cluster_allocation = int(cluster_allocation * gradient_scaling)

        # Phase-based adjustment
        if state.phase == SamplingPhase.EXPLORATION:
            # More points during exploration
            cluster_allocation = int(cluster_allocation * 1.5)
        elif state.phase == SamplingPhase.CONVERGENCE:
            # Fewer points during final convergence
            cluster_allocation = int(cluster_allocation * 0.7)

        # Apply bounds
        target = max(self.min_live_points,
                     min(self.max_live_points, cluster_allocation))

        self.cluster_history.append(n_clusters)

        return target

    def _estimate_evidence_variance(self, state: SamplingState) -> float:
        """Estimate variance in log evidence."""
        if state.iteration < 2:
            return 1.0

        # Variance from stochastic nested sampling
        # Var[log Z] ≈ H / n_live where H is information
        n_live = len(state.live_points)

        # Estimate information from log-likelihood range
        if state.dead_points:
            log_l_range = (state.dead_points[-1].log_likelihood -
                          state.dead_points[0].log_likelihood)
            info_estimate = max(1.0, log_l_range)
        else:
            info_estimate = 1.0

        return info_estimate / n_live

    def _compute_likelihood_gradient(self, state: SamplingState) -> float:
        """Compute recent gradient in log-likelihood."""
        recent = state.dead_points[-10:]
        if len(recent) < 2:
            return 0.0

        # Gradient per iteration
        delta_logl = recent[-1].log_likelihood - recent[0].log_likelihood
        delta_iter = len(recent)

        return abs(delta_logl / delta_iter)

    def update_efficiency(self, accepted: int, proposed: int):
        """Track sampling efficiency."""
        if proposed > 0:
            efficiency = accepted / proposed
            self.efficiency_history.append(efficiency)


# ============================================================================
# Multi-Modal Detector
# ============================================================================

class MultiModalDetector:
    """
    Detects and tracks multiple modes in the posterior.
    Uses clustering on live points to identify separated regions.
    """

    def __init__(self,
                 min_cluster_size: int = 5,
                 separation_threshold: float = 3.0):
        self.min_cluster_size = min_cluster_size
        self.separation_threshold = separation_threshold

    def detect_clusters(self,
                        live_points: List[LivePoint],
                        parameter_bounds: Dict[str, Tuple[float, float]]) -> List[Cluster]:
        """
        Detect clusters in live points using hierarchical clustering.
        """
        if len(live_points) < 2 * self.min_cluster_size:
            # Not enough points for meaningful clustering
            return [self._single_cluster(live_points, 0)]

        # Extract parameter arrays
        param_names = list(live_points[0].parameters.keys())
        n_points = len(live_points)
        n_params = len(param_names)

        # Normalize parameters to [0, 1]
        points_array = []
        for point in live_points:
            normalized = []
            for name in param_names:
                bounds = parameter_bounds[name]
                val = (point.parameters[name] - bounds[0]) / (bounds[1] - bounds[0])
                normalized.append(val)
            points_array.append(normalized)

        # Simple distance-based clustering
        clusters = self._hierarchical_cluster(points_array, live_points)

        # Convert to Cluster objects
        result = []
        for cluster_id, indices in enumerate(clusters):
            if len(indices) >= self.min_cluster_size:
                cluster_points = [live_points[i] for i in indices]
                result.append(self._build_cluster(cluster_points, cluster_id, param_names))

        # Assign cluster IDs to points
        for cluster_id, indices in enumerate(clusters):
            for i in indices:
                live_points[i].cluster_id = cluster_id

        return result if result else [self._single_cluster(live_points, 0)]

    def _hierarchical_cluster(self,
                              points: List[List[float]],
                              live_points: List[LivePoint]) -> List[List[int]]:
        """Simple agglomerative clustering."""
        n = len(points)

        # Compute distance matrix
        distances = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                d = self._distance(points[i], points[j])
                distances[i][j] = d
                distances[j][i] = d

        # Start with each point in its own cluster
        cluster_assignments = list(range(n))

        # Merge until separation threshold
        while True:
            # Find closest pair of clusters
            min_dist = float('inf')
            merge_pair = None

            cluster_ids = list(set(cluster_assignments))
            if len(cluster_ids) <= 1:
                break

            for i, c1 in enumerate(cluster_ids):
                for c2 in cluster_ids[i + 1:]:
                    # Average linkage distance
                    points_c1 = [j for j, c in enumerate(cluster_assignments) if c == c1]
                    points_c2 = [j for j, c in enumerate(cluster_assignments) if c == c2]

                    total_dist = 0.0
                    count = 0
                    for p1 in points_c1:
                        for p2 in points_c2:
                            total_dist += distances[p1][p2]
                            count += 1

                    avg_dist = total_dist / count if count > 0 else float('inf')

                    if avg_dist < min_dist:
                        min_dist = avg_dist
                        merge_pair = (c1, c2)

            # Check if should merge
            if min_dist > self.separation_threshold / math.sqrt(len(points[0])):
                break

            # Merge clusters
            if merge_pair:
                c1, c2 = merge_pair
                for i in range(n):
                    if cluster_assignments[i] == c2:
                        cluster_assignments[i] = c1

        # Group by cluster
        clusters_dict = defaultdict(list)
        for i, c in enumerate(cluster_assignments):
            clusters_dict[c].append(i)

        return list(clusters_dict.values())

    def _distance(self, p1: List[float], p2: List[float]) -> float:
        """Euclidean distance."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

    def _single_cluster(self, points: List[LivePoint], cluster_id: int) -> Cluster:
        """Create single cluster from all points."""
        param_names = list(points[0].parameters.keys())
        return self._build_cluster(points, cluster_id, param_names)

    def _build_cluster(self,
                       points: List[LivePoint],
                       cluster_id: int,
                       param_names: List[str]) -> Cluster:
        """Build Cluster object from points."""
        n = len(points)

        # Compute center
        center = {}
        for name in param_names:
            center[name] = sum(p.parameters[name] for p in points) / n

        # Compute covariance
        covariance = {name: {name2: 0.0 for name2 in param_names} for name in param_names}
        for p in points:
            for name1 in param_names:
                for name2 in param_names:
                    covariance[name1][name2] += (
                        (p.parameters[name1] - center[name1]) *
                        (p.parameters[name2] - center[name2])
                    )

        for name1 in param_names:
            for name2 in param_names:
                covariance[name1][name2] /= n

        # Likelihood range
        log_likes = [p.log_likelihood for p in points]

        return Cluster(
            cluster_id=cluster_id,
            center=center,
            covariance=covariance,
            n_points=n,
            log_likelihood_range=(min(log_likes), max(log_likes))
        )


# ============================================================================
# Constrained Prior Sampler
# ============================================================================

class ConstrainedPriorSampler:
    """
    Samples from prior subject to likelihood constraint.
    Uses multiple strategies for efficient sampling.
    """

    def __init__(self,
                 parameter_bounds: Dict[str, Tuple[float, float]],
                 prior_transform: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None):
        self.parameter_bounds = parameter_bounds
        self.prior_transform = prior_transform or self._uniform_prior_transform

        # Sampling statistics
        self.n_accepted = 0
        self.n_proposed = 0

    def _uniform_prior_transform(self, unit_cube: Dict[str, float]) -> Dict[str, float]:
        """Transform unit cube to parameter space (uniform prior)."""
        params = {}
        for name, u in unit_cube.items():
            low, high = self.parameter_bounds[name]
            params[name] = low + u * (high - low)
        return params

    def sample_constrained(self,
                           log_likelihood_fn: Callable[[Dict[str, float]], float],
                           log_prior_fn: Callable[[Dict[str, float]], float],
                           log_likelihood_threshold: float,
                           clusters: Optional[List[Cluster]] = None,
                           max_attempts: int = 10000) -> Optional[LivePoint]:
        """
        Sample a new point with log_likelihood > threshold.
        """
        # Choose sampling strategy based on available information
        if clusters and len(clusters) > 0 and clusters[0].n_points >= 5:
            # Use ellipsoidal sampling around clusters
            return self._ellipsoidal_sample(
                log_likelihood_fn, log_prior_fn,
                log_likelihood_threshold, clusters, max_attempts
            )
        else:
            # Fall back to rejection sampling
            return self._rejection_sample(
                log_likelihood_fn, log_prior_fn,
                log_likelihood_threshold, max_attempts
            )

    def _rejection_sample(self,
                          log_likelihood_fn: Callable,
                          log_prior_fn: Callable,
                          threshold: float,
                          max_attempts: int) -> Optional[LivePoint]:
        """Simple rejection sampling from prior."""
        param_names = list(self.parameter_bounds.keys())

        for _ in range(max_attempts):
            self.n_proposed += 1

            # Sample from unit cube
            unit_cube = {name: random.random() for name in param_names}
            params = self.prior_transform(unit_cube)

            # Compute likelihood
            log_l = log_likelihood_fn(params)

            if log_l > threshold:
                self.n_accepted += 1
                log_p = log_prior_fn(params)
                return LivePoint(
                    parameters=params,
                    log_likelihood=log_l,
                    log_prior=log_p,
                    birth_iteration=0
                )

        return None

    def _ellipsoidal_sample(self,
                            log_likelihood_fn: Callable,
                            log_prior_fn: Callable,
                            threshold: float,
                            clusters: List[Cluster],
                            max_attempts: int) -> Optional[LivePoint]:
        """Sample from ellipsoids around clusters."""
        param_names = list(self.parameter_bounds.keys())
        n_params = len(param_names)

        # Expansion factor for ellipsoid
        expansion = 1.5

        for _ in range(max_attempts):
            self.n_proposed += 1

            # Choose cluster proportional to number of points
            total_points = sum(c.n_points for c in clusters)
            r = random.random() * total_points
            cumsum = 0
            chosen_cluster = clusters[0]
            for cluster in clusters:
                cumsum += cluster.n_points
                if r < cumsum:
                    chosen_cluster = cluster
                    break

            # Sample from ellipsoid around cluster
            # Use Cholesky decomposition of covariance
            params = self._sample_from_ellipsoid(
                chosen_cluster, param_names, expansion
            )

            # Check bounds
            in_bounds = all(
                self.parameter_bounds[name][0] <= params[name] <= self.parameter_bounds[name][1]
                for name in param_names
            )

            if not in_bounds:
                continue

            # Compute likelihood
            log_l = log_likelihood_fn(params)

            if log_l > threshold:
                self.n_accepted += 1
                log_p = log_prior_fn(params)
                return LivePoint(
                    parameters=params,
                    log_likelihood=log_l,
                    log_prior=log_p,
                    birth_iteration=0
                )

        # Fall back to rejection sampling
        return self._rejection_sample(
            log_likelihood_fn, log_prior_fn, threshold, max_attempts // 2
        )

    def _sample_from_ellipsoid(self,
                               cluster: Cluster,
                               param_names: List[str],
                               expansion: float) -> Dict[str, float]:
        """Sample uniformly from ellipsoid."""
        n = len(param_names)

        # Sample direction (uniform on sphere)
        direction = [random.gauss(0, 1) for _ in range(n)]
        norm = math.sqrt(sum(d * d for d in direction))
        direction = [d / norm for d in direction]

        # Sample radius (uniform in volume)
        radius = random.random() ** (1.0 / n)

        # Scale by eigenvalues of covariance (simplified)
        params = {}
        for i, name in enumerate(param_names):
            # Use diagonal of covariance as scale
            scale = math.sqrt(abs(cluster.covariance[name][name])) * expansion
            params[name] = cluster.center[name] + radius * direction[i] * scale * 3.0

        return params

    def get_efficiency(self) -> float:
        """Return sampling efficiency."""
        if self.n_proposed == 0:
            return 0.0
        return self.n_accepted / self.n_proposed


# ============================================================================
# Evidence Calculator
# ============================================================================

class EvidenceCalculator:
    """
    Computes Bayesian evidence (marginal likelihood) and uncertainty.
    """

    def __init__(self):
        self.log_evidence_history: List[float] = []

    def compute_evidence(self,
                         dead_points: List[DeadPoint],
                         live_points: List[LivePoint],
                         log_remaining_prior: float) -> Tuple[float, float]:
        """
        Compute log evidence and error estimate.

        log Z = log(sum_i w_i L_i) where w_i = X_{i-1} - X_i
        """
        if not dead_points:
            return -float('inf'), float('inf')

        # Contribution from dead points
        log_weights = [dp.log_weight for dp in dead_points]
        log_z_dead = self._log_sum_exp(log_weights)

        # Contribution from remaining live points
        if live_points:
            n_live = len(live_points)
            avg_log_l = self._log_sum_exp(
                [lp.log_likelihood for lp in live_points]
            ) - math.log(n_live)

            log_z_live = log_remaining_prior + avg_log_l
        else:
            log_z_live = -float('inf')

        # Total evidence
        log_z = self._log_sum_exp([log_z_dead, log_z_live])

        # Error estimate (simplified Skilling approximation)
        # sigma(log Z) ≈ sqrt(H/n_live) where H is information
        if live_points:
            info = self._compute_information(dead_points, log_z)
            n_live = len(live_points)
            log_z_error = math.sqrt(max(1.0, info) / n_live)
        else:
            log_z_error = 1.0

        self.log_evidence_history.append(log_z)

        return log_z, log_z_error

    def _compute_information(self,
                             dead_points: List[DeadPoint],
                             log_z: float) -> float:
        """Compute information gain H = <log L> - log Z."""
        if not dead_points:
            return 1.0

        # Weighted average of log likelihood
        log_weights = [dp.log_weight for dp in dead_points]
        log_z_dead = self._log_sum_exp(log_weights)

        # <log L> weighted by posterior
        total = 0.0
        for dp in dead_points:
            weight = math.exp(dp.log_weight - log_z_dead)
            total += weight * dp.log_likelihood

        return total - log_z

    def _log_sum_exp(self, log_values: List[float]) -> float:
        """Numerically stable log-sum-exp."""
        if not log_values:
            return -float('inf')

        max_log = max(log_values)
        if max_log == -float('inf'):
            return -float('inf')

        return max_log + math.log(sum(math.exp(lv - max_log) for lv in log_values))


# ============================================================================
# Stopping Criterion
# ============================================================================

class StoppingCriterion:
    """
    Determines when nested sampling has converged.
    """

    def __init__(self,
                 evidence_tolerance: float = 0.5,
                 max_iterations: int = 100000,
                 min_iterations: int = 100):
        self.evidence_tolerance = evidence_tolerance
        self.max_iterations = max_iterations
        self.min_iterations = min_iterations

    def should_stop(self,
                    state: SamplingState,
                    log_evidence: float,
                    log_evidence_error: float) -> Tuple[bool, str]:
        """
        Check if sampling should stop.

        Returns (should_stop, reason)
        """
        # Minimum iterations
        if state.iteration < self.min_iterations:
            return False, ""

        # Maximum iterations
        if state.iteration >= self.max_iterations:
            return True, f"Maximum iterations ({self.max_iterations}) reached"

        # Evidence convergence
        if state.live_points:
            n_live = len(state.live_points)
            max_remaining_log_l = max(lp.log_likelihood for lp in state.live_points)

            # Maximum possible remaining evidence
            log_remaining_evidence = state.log_remaining_prior + max_remaining_log_l

            # Stop if remaining evidence is negligible
            log_frac = log_remaining_evidence - log_evidence

            if log_frac < math.log(self.evidence_tolerance):
                return True, f"Evidence converged (remaining fraction < {self.evidence_tolerance})"

        # Error criterion
        if log_evidence_error < self.evidence_tolerance / 10:
            return True, f"Evidence error converged ({log_evidence_error:.4f})"

        return False, ""


# ============================================================================
# Main Nested Sampler
# ============================================================================

class NestedSampler:
    """
    Main nested sampling engine with dynamic allocation.
    """

    def __init__(self,
                 parameter_bounds: Dict[str, Tuple[float, float]],
                 log_likelihood_fn: Callable[[Dict[str, float]], float],
                 log_prior_fn: Optional[Callable[[Dict[str, float]], float]] = None,
                 prior_transform: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None,
                 initial_live_points: int = 100,
                 evidence_tolerance: float = 0.5,
                 max_iterations: int = 100000):
        """
        Initialize nested sampler.

        Args:
            parameter_bounds: Dict mapping parameter names to (min, max) bounds
            log_likelihood_fn: Function computing log-likelihood
            log_prior_fn: Function computing log-prior (default: uniform)
            prior_transform: Function transforming unit cube to parameters
            initial_live_points: Initial number of live points
            evidence_tolerance: Stopping criterion for evidence
            max_iterations: Maximum number of iterations
        """
        self.parameter_bounds = parameter_bounds
        self.log_likelihood_fn = log_likelihood_fn
        self.log_prior_fn = log_prior_fn or self._default_log_prior
        self.prior_transform = prior_transform
        self.initial_live_points = initial_live_points

        # Components
        self.allocator = DynamicLivePointAllocator(
            min_live_points=max(20, initial_live_points // 5),
            max_live_points=initial_live_points * 10
        )
        self.modal_detector = MultiModalDetector()
        self.sampler = ConstrainedPriorSampler(
            parameter_bounds, prior_transform
        )
        self.evidence_calculator = EvidenceCalculator()
        self.stopping = StoppingCriterion(
            evidence_tolerance=evidence_tolerance,
            max_iterations=max_iterations
        )

        # Event bus integration
        self._event_bus = None

    def _default_log_prior(self, params: Dict[str, float]) -> float:
        """Uniform prior over parameter bounds."""
        log_p = 0.0
        for name, val in params.items():
            low, high = self.parameter_bounds[name]
            if val < low or val > high:
                return -float('inf')
            log_p -= math.log(high - low)
        return log_p

    def set_event_bus(self, event_bus):
        """Set event bus for integration."""
        self._event_bus = event_bus

    def run(self,
            callback: Optional[Callable[[SamplingState], None]] = None) -> NestedSamplingResult:
        """
        Run nested sampling.

        Args:
            callback: Optional function called each iteration

        Returns:
            NestedSamplingResult with evidence and posterior samples
        """
        # Initialize live points
        state = self._initialize(self.initial_live_points)

        # Main loop
        while True:
            # Detect clusters
            state.clusters = self.modal_detector.detect_clusters(
                state.live_points, self.parameter_bounds
            )

            # Update target live points
            state.target_n_live = self.allocator.compute_target_live_points(state)

            # Adjust live point count
            self._adjust_live_points(state)

            # Find worst point
            worst_idx = min(range(len(state.live_points)),
                           key=lambda i: state.live_points[i].log_likelihood)
            worst_point = state.live_points[worst_idx]

            # Compute weight for dead point
            n_live = len(state.live_points)
            log_weight = (state.log_remaining_prior -
                         math.log(n_live) +
                         worst_point.log_likelihood)

            # Move worst to dead points
            dead_point = DeadPoint(
                parameters=worst_point.parameters.copy(),
                log_likelihood=worst_point.log_likelihood,
                log_prior=worst_point.log_prior,
                log_weight=log_weight,
                iteration=state.iteration
            )
            state.dead_points.append(dead_point)

            # Update remaining prior volume
            state.log_remaining_prior -= 1.0 / n_live

            # Sample new point above threshold
            new_point = self.sampler.sample_constrained(
                self.log_likelihood_fn,
                self.log_prior_fn,
                worst_point.log_likelihood,
                state.clusters
            )

            if new_point is None:
                logger.warning(f"Failed to sample new point at iteration {state.iteration}")
                # Remove worst without replacement
                state.live_points.pop(worst_idx)
            else:
                new_point.birth_iteration = state.iteration
                state.live_points[worst_idx] = new_point
                state.n_likelihood_calls += self.sampler.n_proposed - state.n_likelihood_calls

            state.n_likelihood_calls = self.sampler.n_proposed
            state.iteration += 1

            # Update efficiency tracking
            self.allocator.update_efficiency(
                self.sampler.n_accepted, self.sampler.n_proposed
            )

            # Compute evidence
            log_z, log_z_error = self.evidence_calculator.compute_evidence(
                state.dead_points, state.live_points, state.log_remaining_prior
            )
            state.log_evidence = log_z

            # Update phase
            state.phase = self._determine_phase(state)

            # Callback
            if callback:
                callback(state)

            # Check stopping
            should_stop, reason = self.stopping.should_stop(
                state, log_z, log_z_error
            )

            if should_stop:
                state.phase = SamplingPhase.COMPLETE
                return self._finalize(state, log_z, log_z_error, reason)

            # Safety: stop if no live points
            if not state.live_points:
                return self._finalize(state, log_z, log_z_error,
                                     "No live points remaining")

    def _initialize(self, n_live: int) -> SamplingState:
        """Initialize live points from prior."""
        param_names = list(self.parameter_bounds.keys())
        live_points = []

        for _ in range(n_live):
            # Sample from prior
            unit_cube = {name: random.random() for name in param_names}
            if self.prior_transform:
                params = self.prior_transform(unit_cube)
            else:
                params = {}
                for name in param_names:
                    low, high = self.parameter_bounds[name]
                    params[name] = low + unit_cube[name] * (high - low)

            log_l = self.log_likelihood_fn(params)
            log_p = self.log_prior_fn(params)

            live_points.append(LivePoint(
                parameters=params,
                log_likelihood=log_l,
                log_prior=log_p,
                birth_iteration=0
            ))

        self.sampler.n_proposed = n_live
        self.sampler.n_accepted = n_live

        return SamplingState(
            live_points=live_points,
            dead_points=[],
            log_evidence=-float('inf'),
            log_evidence_squared=0.0,
            iteration=0,
            n_likelihood_calls=n_live,
            phase=SamplingPhase.EXPLORATION,
            clusters=[],
            target_n_live=n_live,
            log_remaining_prior=0.0  # log(1) = 0
        )

    def _adjust_live_points(self, state: SamplingState):
        """Add or remove live points to match target."""
        current = len(state.live_points)
        target = state.target_n_live

        if current < target:
            # Need to add points
            n_add = target - current
            threshold = min(lp.log_likelihood for lp in state.live_points)

            for _ in range(n_add):
                new_point = self.sampler.sample_constrained(
                    self.log_likelihood_fn,
                    self.log_prior_fn,
                    threshold,
                    state.clusters
                )
                if new_point:
                    new_point.birth_iteration = state.iteration
                    state.live_points.append(new_point)

        elif current > target:
            # Need to remove points (remove lowest likelihood ones)
            n_remove = current - target
            state.live_points.sort(key=lambda p: p.log_likelihood, reverse=True)

            for _ in range(n_remove):
                if len(state.live_points) > self.allocator.min_live_points:
                    removed = state.live_points.pop()
                    # Add to dead points with appropriate weight
                    log_weight = (state.log_remaining_prior -
                                 math.log(len(state.live_points) + 1) +
                                 removed.log_likelihood)
                    state.dead_points.append(DeadPoint(
                        parameters=removed.parameters,
                        log_likelihood=removed.log_likelihood,
                        log_prior=removed.log_prior,
                        log_weight=log_weight,
                        iteration=state.iteration
                    ))

    def _determine_phase(self, state: SamplingState) -> SamplingPhase:
        """Determine current sampling phase."""
        if state.iteration < 100:
            return SamplingPhase.EXPLORATION

        # Check if likelihood is still increasing rapidly
        if len(state.dead_points) >= 20:
            recent = state.dead_points[-20:]
            delta = recent[-1].log_likelihood - recent[0].log_likelihood

            if delta > 10.0:
                return SamplingPhase.EXPLORATION
            elif delta > 1.0:
                return SamplingPhase.REFINEMENT
            else:
                return SamplingPhase.CONVERGENCE

        return SamplingPhase.REFINEMENT

    def _finalize(self,
                  state: SamplingState,
                  log_z: float,
                  log_z_error: float,
                  reason: str) -> NestedSamplingResult:
        """Finalize and compute posterior samples."""
        # Combine dead and live points for posterior
        all_points = list(state.dead_points)

        # Add remaining live points with equal weight
        if state.live_points:
            n_live = len(state.live_points)
            log_weight_live = state.log_remaining_prior - math.log(n_live)

            for lp in state.live_points:
                all_points.append(DeadPoint(
                    parameters=lp.parameters,
                    log_likelihood=lp.log_likelihood,
                    log_prior=lp.log_prior,
                    log_weight=log_weight_live + lp.log_likelihood,
                    iteration=state.iteration
                ))

        # Normalize weights
        log_weights = [p.log_weight for p in all_points]
        log_z_samples = self.evidence_calculator._log_sum_exp(log_weights)

        weights = [math.exp(lw - log_z_samples) for lw in log_weights]

        # Compute posterior statistics
        param_names = list(self.parameter_bounds.keys())

        means = {}
        variances = {}

        for name in param_names:
            mean = sum(w * p.parameters[name] for w, p in zip(weights, all_points))
            var = sum(w * (p.parameters[name] - mean) ** 2 for w, p in zip(weights, all_points))
            means[name] = mean
            variances[name] = var

        # Effective sample size
        ess = 1.0 / sum(w * w for w in weights) if weights else 0.0

        # Information gain
        info = sum(w * (p.log_likelihood - log_z) for w, p in zip(weights, all_points))

        # Emit result event
        if self._event_bus:
            self._event_bus.publish(
                "nested_sampling_complete",
                "nested_sampler",
                {
                    "log_evidence": log_z,
                    "log_evidence_error": log_z_error,
                    "n_iterations": state.iteration,
                    "n_clusters": len(state.clusters),
                    "effective_sample_size": ess
                }
            )

        return NestedSamplingResult(
            log_evidence=log_z,
            log_evidence_error=log_z_error,
            posterior_samples=[p.parameters for p in all_points],
            posterior_weights=weights,
            parameter_means=means,
            parameter_stds={k: math.sqrt(v) for k, v in variances.items()},
            n_iterations=state.iteration,
            n_likelihood_calls=state.n_likelihood_calls,
            n_clusters_detected=max(1, len(state.clusters)),
            information_gain=info,
            effective_sample_size=ess,
            converged=True,
            convergence_reason=reason
        )


# ============================================================================
# Astrophysics-Specific Helpers
# ============================================================================

def create_lens_parameter_bounds() -> Dict[str, Tuple[float, float]]:
    """Standard bounds for gravitational lens parameters."""
    return {
        "einstein_radius": (0.1, 5.0),      # arcsec
        "ellipticity": (0.0, 0.9),
        "position_angle": (0.0, 180.0),     # degrees
        "center_x": (-1.0, 1.0),            # arcsec
        "center_y": (-1.0, 1.0),            # arcsec
        "shear_strength": (0.0, 0.3),
        "shear_angle": (0.0, 180.0)         # degrees
    }


def create_stellar_parameter_bounds() -> Dict[str, Tuple[float, float]]:
    """Standard bounds for stellar parameters."""
    return {
        "effective_temperature": (3000.0, 50000.0),  # K
        "surface_gravity": (0.0, 6.0),               # log g [cgs]
        "metallicity": (-4.0, 0.5),                  # [Fe/H]
        "mass": (0.1, 100.0),                        # solar masses
        "radius": (0.1, 1000.0)                      # solar radii
    }


def create_cosmology_parameter_bounds() -> Dict[str, Tuple[float, float]]:
    """Standard bounds for cosmological parameters."""
    return {
        "H0": (50.0, 100.0),                # km/s/Mpc
        "omega_m": (0.1, 0.5),              # matter density
        "omega_lambda": (0.5, 0.9),         # dark energy density
        "omega_b": (0.01, 0.1),             # baryon density
        "sigma_8": (0.5, 1.2),              # clustering amplitude
        "n_s": (0.8, 1.1)                   # scalar spectral index
    }


# ============================================================================
# Singleton Access
# ============================================================================

_nested_sampler_instances: Dict[str, NestedSampler] = {}


def create_nested_sampler(name: str,
                          parameter_bounds: Dict[str, Tuple[float, float]],
                          log_likelihood_fn: Callable,
                          **kwargs) -> NestedSampler:
    """Create and register a named nested sampler."""
    sampler = NestedSampler(parameter_bounds, log_likelihood_fn, **kwargs)
    _nested_sampler_instances[name] = sampler
    return sampler


def get_nested_sampler(name: str) -> Optional[NestedSampler]:
    """Get a registered nested sampler by name."""
    return _nested_sampler_instances.get(name)


# ============================================================================
# Integration with STAN Event Bus
# ============================================================================

def setup_nested_sampling_integration(event_bus) -> None:
    """Set up nested sampling integration with STAN event bus."""

    def on_inference_request(event):
        """Handle inference request events."""
        payload = event.get("payload", {})

        if payload.get("method") == "nested_sampling":
            bounds = payload.get("parameter_bounds", {})
            likelihood_fn = payload.get("likelihood_fn")

            if bounds and likelihood_fn:
                sampler = create_nested_sampler(
                    payload.get("name", "default"),
                    bounds,
                    likelihood_fn,
                    initial_live_points=payload.get("n_live", 100),
                    evidence_tolerance=payload.get("tolerance", 0.5)
                )
                sampler.set_event_bus(event_bus)

                result = sampler.run()

                event_bus.publish(
                    "inference_result",
                    "nested_sampling",
                    {"result": result}
                )

    event_bus.subscribe("inference_request", on_inference_request)
    logger.info("Nested sampling integration configured")
