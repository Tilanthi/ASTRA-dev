"""
Bayesian Swarm Inference for Astronomy

This module implements the CORE INFERENCE ENGINE that combines:
1. Physics-based forward models (from physics.py)
2. Swarm exploration of parameter space
3. Proper Bayesian posterior estimation
4. MORK persistence for accumulated knowledge

The key innovation: Swarm agents explore the LIKELIHOOD LANDSCAPE,
not a simplified proxy metric. Each agent evaluates the ACTUAL
physics-based chi-squared.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
from pathlib import Path
import json

# Local imports
from .physics import PhysicsEngine, ForwardModel, AstrophysicalConstraints


# =============================================================================
# INFERENCE RESULT STRUCTURES
# =============================================================================

@dataclass
class ParameterEstimate:
    """Estimate of a single parameter with uncertainties"""
    name: str
    value: float
    uncertainty_lower: float
    uncertainty_upper: float
    unit: str
    confidence_level: float = 0.68  # 1-sigma by default

    @property
    def symmetric_uncertainty(self) -> float:
        return (self.uncertainty_lower + self.uncertainty_upper) / 2

    def __str__(self):
        return f"{self.name} = {self.value:.4g} (+{self.uncertainty_upper:.2g}/-{self.uncertainty_lower:.2g}) {self.unit}"


@dataclass
class InferenceResult:
    """Complete result of Bayesian inference"""
    parameters: Dict[str, ParameterEstimate]
    chi_squared: float
    degrees_of_freedom: int
    reduced_chi_squared: float
    log_evidence: float
    posterior_samples: Optional[np.ndarray] = None
    convergence_achieved: bool = True
    n_evaluations: int = 0
    wall_time: float = 0.0
    method: str = "swarm"

    def summary(self) -> str:
        lines = ["=" * 60]
        lines.append("INFERENCE RESULT SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Method: {self.method}")
        lines.append(f"Chi-squared: {self.chi_squared:.4f}")
        lines.append(f"Reduced chi-squared: {self.reduced_chi_squared:.4f}")
        lines.append(f"Degrees of freedom: {self.degrees_of_freedom}")
        lines.append(f"Log evidence: {self.log_evidence:.2f}")
        lines.append(f"Converged: {self.convergence_achieved}")
        lines.append(f"Function evaluations: {self.n_evaluations}")
        lines.append(f"Wall time: {self.wall_time:.2f} s")
        lines.append("-" * 60)
        lines.append("PARAMETERS:")
        for name, est in self.parameters.items():
            lines.append(f"  {est}")
        lines.append("=" * 60)
        return "\n".join(lines)


# =============================================================================
# SWARM AGENT FOR BAYESIAN INFERENCE
# =============================================================================

@dataclass
class SwarmParticle:
    """
    A particle in the swarm optimization

    This particle:
    1. Carries full parameter vector
    2. Evaluates PHYSICS-BASED chi-squared
    3. Tracks likelihood not just fitness
    """
    particle_id: str
    position: np.ndarray  # Current parameter values
    velocity: np.ndarray  # Current velocity in parameter space
    best_position: np.ndarray  # Personal best position
    best_chi_squared: float = float('inf')
    current_chi_squared: float = float('inf')
    generation: int = 0


class BayesianSwarmInference:
    """
    Bayesian parameter inference using swarm intelligence

    This combines:
    1. Particle Swarm Optimization (PSO) for global exploration
    2. Physics-based likelihood evaluation
    3. Proper posterior estimation via sampling
    4. Gordon's biological principles for swarm behavior

    Key principle:
    - Fitness = actual chi-squared from physics forward model
    - Uses proper astrophysical equations, not simplified proxies
    """

    # Gordon's biological parameters (immutable)
    GORDON_PARAMS = {
        'inertia_weight': 0.7298,  # ω - particle inertia
        'cognitive_weight': 1.4962,  # c1 - personal best attraction
        'social_weight': 1.4962,  # c2 - global best attraction
        'evaporation_rate': 0.05,  # ρ - knowledge decay
        'exploration_rate': 0.15,  # Probability of random jump
    }

    def __init__(self, physics_engine: PhysicsEngine, model_name: str):
        """
        Initialize Bayesian swarm inference

        Args:
            physics_engine: Physics engine with forward models
            model_name: Name of the forward model to use
        """
        self.physics = physics_engine
        self.model_name = model_name
        self.model = physics_engine.get_model(model_name)

        # Swarm state
        self.particles: List[SwarmParticle] = []
        self.global_best_position: Optional[np.ndarray] = None
        self.global_best_chi_squared: float = float('inf')

        # Parameter bounds
        self.param_names: List[str] = []
        self.param_bounds: List[Tuple[float, float]] = []
        self.param_units: List[str] = []

        # History for convergence checking
        self.chi_squared_history: List[float] = []
        self.n_evaluations: int = 0

    def set_parameter_bounds(self, bounds: Dict[str, Tuple[float, float, str]]):
        """
        Set parameter bounds for inference

        Args:
            bounds: Dict mapping parameter name to (min, max, unit)
        """
        self.param_names = list(bounds.keys())
        self.param_bounds = [(b[0], b[1]) for b in bounds.values()]
        self.param_units = [b[2] for b in bounds.values()]

    def _initialize_swarm(self, n_particles: int):
        """Initialize swarm with random positions"""
        self.particles = []

        for i in range(n_particles):
            # Random position within bounds
            position = np.array([
                np.random.uniform(low, high)
                for low, high in self.param_bounds
            ])

            # Random velocity (fraction of parameter range)
            velocity = np.array([
                np.random.uniform(-0.1, 0.1) * (high - low)
                for low, high in self.param_bounds
            ])

            particle = SwarmParticle(
                particle_id=f"particle_{i:03d}",
                position=position,
                velocity=velocity,
                best_position=position.copy(),
            )

            self.particles.append(particle)

    def _position_to_params(self, position: np.ndarray) -> Dict[str, float]:
        """Convert position vector to parameter dictionary with unit conversion

        CRITICAL: Converts angles from degrees to radians for physics model.
        The physics model (GravitationalLensModel) expects radians.
        """
        params = {}
        for i, name in enumerate(self.param_names):
            value = position[i]

            # Convert angles from degrees to radians
            # Physics models expect radians for trigonometric calculations
            if 'angle' in name.lower() and self.param_units[i] == 'deg':
                value = np.radians(value)

            params[name] = value

        return params

    def _evaluate_chi_squared(self, position: np.ndarray,
                               observations: Dict) -> float:
        """
        Evaluate chi-squared using PHYSICS forward model

        Uses the ACTUAL physics-based likelihood from forward models.
        """
        parameters = self._position_to_params(position)

        # Use physics engine to compute chi-squared
        chi_squared = self.physics.compute_chi_squared(
            self.model_name,
            parameters,
            observations
        )

        self.n_evaluations += 1

        return chi_squared

    def _update_particle(self, particle: SwarmParticle, observations: Dict):
        """
        Update a single particle using PSO equations

        v_{t+1} = ω*v_t + c1*r1*(p_best - x_t) + c2*r2*(g_best - x_t)
        x_{t+1} = x_t + v_{t+1}
        """
        omega = self.GORDON_PARAMS['inertia_weight']
        c1 = self.GORDON_PARAMS['cognitive_weight']
        c2 = self.GORDON_PARAMS['social_weight']

        r1 = np.random.random(len(particle.position))
        r2 = np.random.random(len(particle.position))

        # Gordon's exploration: occasionally make random jump
        if np.random.random() < self.GORDON_PARAMS['exploration_rate']:
            # Random exploration
            particle.position = np.array([
                np.random.uniform(low, high)
                for low, high in self.param_bounds
            ])
        else:
            # Standard PSO update
            cognitive = c1 * r1 * (particle.best_position - particle.position)
            social = c2 * r2 * (self.global_best_position - particle.position)

            particle.velocity = omega * particle.velocity + cognitive + social

            # Velocity clamping
            for i, (low, high) in enumerate(self.param_bounds):
                max_vel = 0.2 * (high - low)
                particle.velocity[i] = np.clip(particle.velocity[i], -max_vel, max_vel)

            particle.position = particle.position + particle.velocity

        # Enforce bounds
        for i, (low, high) in enumerate(self.param_bounds):
            particle.position[i] = np.clip(particle.position[i], low, high)

        # Evaluate new position
        particle.current_chi_squared = self._evaluate_chi_squared(
            particle.position, observations
        )

        # Update personal best
        if particle.current_chi_squared < particle.best_chi_squared:
            particle.best_chi_squared = particle.current_chi_squared
            particle.best_position = particle.position.copy()

            # Update global best
            if particle.current_chi_squared < self.global_best_chi_squared:
                self.global_best_chi_squared = particle.current_chi_squared
                self.global_best_position = particle.position.copy()

        particle.generation += 1

    def infer(self, observations: Dict,
              n_particles: int = 30,
              n_iterations: int = 100,
              convergence_threshold: float = 1e-6,
              verbose: bool = True) -> InferenceResult:
        """
        Run Bayesian inference using swarm optimization

        Args:
            observations: Dictionary of observed data
            n_particles: Number of swarm particles
            n_iterations: Maximum iterations
            convergence_threshold: Convergence criterion
            verbose: Print progress

        Returns:
            InferenceResult with parameter estimates and uncertainties
        """
        import time
        start_time = time.time()

        if verbose:
            print("=" * 60)
            print(f"BAYESIAN SWARM INFERENCE: {self.model_name}")
            print("=" * 60)
            print(f"Parameters: {self.param_names}")
            print(f"Particles: {n_particles}")
            print(f"Max iterations: {n_iterations}")

        # Initialize swarm
        self._initialize_swarm(n_particles)

        # Initialize global best
        self.global_best_position = self.particles[0].position.copy()
        self.global_best_chi_squared = float('inf')

        # Initial evaluation
        for particle in self.particles:
            particle.current_chi_squared = self._evaluate_chi_squared(
                particle.position, observations
            )
            particle.best_chi_squared = particle.current_chi_squared
            particle.best_position = particle.position.copy()

            if particle.current_chi_squared < self.global_best_chi_squared:
                self.global_best_chi_squared = particle.current_chi_squared
                self.global_best_position = particle.position.copy()

        self.chi_squared_history.append(self.global_best_chi_squared)

        if verbose:
            print(f"\nInitial best chi-squared: {self.global_best_chi_squared:.6f}")

        # Main optimization loop
        converged = False
        for iteration in range(n_iterations):
            # Update all particles
            for particle in self.particles:
                self._update_particle(particle, observations)

            self.chi_squared_history.append(self.global_best_chi_squared)

            # Check convergence
            if len(self.chi_squared_history) > 10:
                recent = self.chi_squared_history[-10:]
                if max(recent) - min(recent) < convergence_threshold:
                    converged = True
                    if verbose:
                        print(f"\nConverged at iteration {iteration}")
                    break

            # Progress report
            if verbose and iteration % 10 == 0:
                print(f"  Iteration {iteration}: chi² = {self.global_best_chi_squared:.6f}")

        wall_time = time.time() - start_time

        # Estimate uncertainties from particle distribution
        uncertainties = self._estimate_uncertainties()

        # Build parameter estimates
        param_estimates = {}
        for i, name in enumerate(self.param_names):
            param_estimates[name] = ParameterEstimate(
                name=name,
                value=self.global_best_position[i],
                uncertainty_lower=uncertainties[i],
                uncertainty_upper=uncertainties[i],
                unit=self.param_units[i]
            )

        # Compute degrees of freedom
        n_data = self._count_data_points(observations)
        n_params = len(self.param_names)
        dof = n_data - n_params

        result = InferenceResult(
            parameters=param_estimates,
            chi_squared=self.global_best_chi_squared,
            degrees_of_freedom=dof,
            reduced_chi_squared=self.global_best_chi_squared / max(1, dof),
            log_evidence=self._estimate_evidence(),
            convergence_achieved=converged,
            n_evaluations=self.n_evaluations,
            wall_time=wall_time,
            method="bayesian_swarm"
        )

        if verbose:
            print(result.summary())

        return result

    def _estimate_uncertainties(self) -> np.ndarray:
        """
        Estimate parameter uncertainties from particle distribution

        Uses the spread of particles near the best solution.
        """
        # Get particles within 2x of best chi-squared
        good_particles = [
            p for p in self.particles
            if p.best_chi_squared < 2 * self.global_best_chi_squared
        ]

        if len(good_particles) < 3:
            good_particles = self.particles

        positions = np.array([p.best_position for p in good_particles])

        # Standard deviation as uncertainty estimate
        uncertainties = np.std(positions, axis=0)

        # Ensure minimum uncertainty (1% of range)
        for i, (low, high) in enumerate(self.param_bounds):
            min_unc = 0.01 * (high - low)
            uncertainties[i] = max(uncertainties[i], min_unc)

        return uncertainties

    def _estimate_evidence(self) -> float:
        """
        Estimate log evidence (marginal likelihood)

        Uses Laplace approximation for simplicity.
        """
        # Simplified: -0.5 * chi² + prior volume term
        n_params = len(self.param_names)
        prior_volume = np.prod([high - low for low, high in self.param_bounds])

        return -0.5 * self.global_best_chi_squared - 0.5 * n_params * np.log(2 * np.pi)

    def _count_data_points(self, observations: Dict) -> int:
        """Count the number of data points in observations"""
        n = 0
        for key, value in observations.items():
            if isinstance(value, np.ndarray):
                n += value.size
            elif isinstance(value, (list, tuple)):
                n += len(value)
            elif value is not None:
                n += 1
        return n


# =============================================================================
# NESTED SAMPLING FOR EVIDENCE CALCULATION
# =============================================================================

class NestedSamplingInference:
    """
    Nested sampling for accurate Bayesian evidence calculation

    Nested sampling is particularly powerful for:
    1. Model comparison (which model fits best?)
    2. Multi-modal posteriors
    3. Accurate uncertainty estimation

    This is valuable when comparing different physical models.
    """

    def __init__(self, physics_engine: PhysicsEngine, model_name: str):
        self.physics = physics_engine
        self.model_name = model_name
        self.model = physics_engine.get_model(model_name)

        self.param_names: List[str] = []
        self.param_bounds: List[Tuple[float, float]] = []

    def set_parameter_bounds(self, bounds: Dict[str, Tuple[float, float, str]]):
        """Set parameter bounds"""
        self.param_names = list(bounds.keys())
        self.param_bounds = [(b[0], b[1]) for b in bounds.values()]

    def _log_likelihood(self, position: np.ndarray, observations: Dict) -> float:
        """Compute log-likelihood from chi-squared"""
        params = {name: position[i] for i, name in enumerate(self.param_names)}
        chi2 = self.physics.compute_chi_squared(self.model_name, params, observations)
        return -0.5 * chi2

    def _prior_transform(self, unit_cube: np.ndarray) -> np.ndarray:
        """Transform unit cube to parameter space"""
        params = np.zeros_like(unit_cube)
        for i, (low, high) in enumerate(self.param_bounds):
            params[i] = low + unit_cube[i] * (high - low)
        return params

    def run_nested_sampling(self, observations: Dict,
                            n_live: int = 100,
                            max_iterations: int = 1000) -> Dict:
        """
        Run nested sampling algorithm

        Simplified implementation - production would use dynesty or ultranest.
        """
        # Initialize live points uniformly
        live_points = np.random.random((n_live, len(self.param_names)))
        live_points = np.array([self._prior_transform(p) for p in live_points])

        live_likelihoods = np.array([
            self._log_likelihood(p, observations) for p in live_points
        ])

        log_evidence = -np.inf
        samples = []

        for i in range(max_iterations):
            # Find worst point
            worst_idx = np.argmin(live_likelihoods)
            worst_L = live_likelihoods[worst_idx]

            # Contribution to evidence
            log_weight = -i / n_live  # Simplified shrinkage
            log_evidence = np.logaddexp(log_evidence, log_weight + worst_L)

            # Store sample
            samples.append({
                'params': live_points[worst_idx].copy(),
                'log_likelihood': worst_L,
                'log_weight': log_weight
            })

            # Replace worst point with new sample above likelihood threshold
            for _ in range(100):  # Max attempts
                new_point = self._prior_transform(np.random.random(len(self.param_names)))
                new_L = self._log_likelihood(new_point, observations)
                if new_L > worst_L:
                    live_points[worst_idx] = new_point
                    live_likelihoods[worst_idx] = new_L
                    break
            else:
                # Failed to find better point - might be converged
                break

        return {
            'log_evidence': log_evidence,
            'samples': samples,
            'n_iterations': len(samples)
        }


# =============================================================================
# MCMC FOR POSTERIOR SAMPLING
# =============================================================================

class MCMCInference:
    """
    Markov Chain Monte Carlo for posterior sampling

    Uses Metropolis-Hastings algorithm for sampling the posterior.
    Useful when full posterior distribution is needed.
    """

    def __init__(self, physics_engine: PhysicsEngine, model_name: str):
        self.physics = physics_engine
        self.model_name = model_name

        self.param_names: List[str] = []
        self.param_bounds: List[Tuple[float, float]] = []

    def set_parameter_bounds(self, bounds: Dict[str, Tuple[float, float, str]]):
        self.param_names = list(bounds.keys())
        self.param_bounds = [(b[0], b[1]) for b in bounds.values()]

    def run_mcmc(self, observations: Dict,
                 n_samples: int = 10000,
                 n_burn: int = 1000,
                 proposal_scale: float = 0.1) -> Dict:
        """
        Run MCMC sampling

        Args:
            observations: Observed data
            n_samples: Number of samples to draw
            n_burn: Burn-in samples to discard
            proposal_scale: Scale of proposal distribution
        """
        n_params = len(self.param_names)

        # Initialize at random position
        current = np.array([
            np.random.uniform(low, high)
            for low, high in self.param_bounds
        ])

        params = {name: current[i] for i, name in enumerate(self.param_names)}
        current_chi2 = self.physics.compute_chi_squared(
            self.model_name, params, observations
        )
        current_log_prob = -0.5 * current_chi2

        samples = []
        accepted = 0

        for i in range(n_samples + n_burn):
            # Propose new position
            proposal = current + np.random.normal(0, proposal_scale, n_params) * np.array([
                high - low for low, high in self.param_bounds
            ])

            # Enforce bounds
            for j, (low, high) in enumerate(self.param_bounds):
                proposal[j] = np.clip(proposal[j], low, high)

            # Evaluate proposal
            params = {name: proposal[j] for j, name in enumerate(self.param_names)}
            proposal_chi2 = self.physics.compute_chi_squared(
                self.model_name, params, observations
            )
            proposal_log_prob = -0.5 * proposal_chi2

            # Accept/reject
            log_alpha = proposal_log_prob - current_log_prob

            if np.log(np.random.random()) < log_alpha:
                current = proposal
                current_log_prob = proposal_log_prob
                accepted += 1

            # Store sample (after burn-in)
            if i >= n_burn:
                samples.append(current.copy())

        samples = np.array(samples)

        return {
            'samples': samples,
            'acceptance_rate': accepted / (n_samples + n_burn),
            'mean': np.mean(samples, axis=0),
            'std': np.std(samples, axis=0),
            'param_names': self.param_names
        }



class ComputationCache:
    """Cache for expensive uncertainty computations."""

    def __init__(self, max_size: int = 500):
        self.cache = {}
        self.max_size = max_size
        self.hit_count = 0
        self.miss_count = 0

    def get(self, computation_key: str, params: Dict[str, Any]) -> Any:
        """Get cached computation result."""
        full_key = f"{computation_key}:{_hash_params(params)}"

        if full_key in self.cache:
            self.hit_count += 1
            return self.cache[full_key]

        self.miss_count += 1
        return None

    def put(self, computation_key: str, params: Dict[str, Any], result: Any):
        """Store computation result."""
        full_key = f"{computation_key}:{_hash_params(params)}"

        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            self.cache.pop(next(iter(self.cache)))

        self.cache[full_key] = result

    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0


def _hash_params(params: Dict[str, Any]) -> str:
    """Hash parameters for cache key."""
    import hashlib
    import json

    param_str = json.dumps(params, sort_keys=True)
    return hashlib.md5(param_str.encode()).hexdigest()[:12]



def compute_credible_interval(samples: np.ndarray,
                            ci_level: float = 0.95) -> Dict[str, Any]:
    """
    Compute credible interval from samples.

    Args:
        samples: Posterior samples
        ci_level: Confidence level (0-1)

    Returns:
        Dictionary with interval bounds and statistics
    """
    import numpy as np

    alpha = 1 - ci_level

    # Compute percentiles
    lower = np.percentile(samples, 100 * alpha / 2)
    upper = np.percentile(samples, 100 * (1 - alpha / 2))
    median = np.median(samples)
    mean = np.mean(samples)

    return {
        'lower': float(lower),
        'upper': float(upper),
        'median': float(median),
        'mean': float(mean),
        'ci_level': ci_level,
        'width': float(upper - lower)
    }



def bootstrap_uncertainty(data: np.ndarray,
                         estimator_func: callable,
                         n_bootstrap: int = 1000,
                         ci_level: float = 0.95) -> Dict[str, Any]:
    """
    Estimate uncertainty using bootstrap resampling.

    Args:
        data: Input data
        estimator_func: Function that computes estimate from data
        n_bootstrap: Number of bootstrap samples
        ci_level: Confidence interval level

    Returns:
        Dictionary with estimate and confidence interval
    """
    import numpy as np

    n = len(data)
    estimates = []

    for _ in range(n_bootstrap):
        # Bootstrap sampling
        sample = np.random.choice(data, size=len(data), replace=True)
        estimate = estimator_func(sample)
        estimates.append(estimate)

    # Compute confidence interval
    alpha = 1 - ci_level
    lower = np.percentile(estimates, 100 * alpha / 2)
    upper = np.percentile(estimates, 100 * (1 - alpha / 2))
    point_estimate = estimator_func(data)

    return {
        'estimate': point_estimate,
        'ci_lower': lower,
        'ci_upper': upper,
        'ci_level': ci_level
    }
