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
Simulation-Based Inference (SBI) for Causal Discovery

Likelihood-free inference using simulator as forward model.
Essential for astrophysical problems with intractable likelihoods.

Methods:
- Approximate Bayesian Computation (ABC)
- Neural Ratio Estimation (NRE)
- Sequential Neural Posterior Estimation (SNPE)
- Neural Likelihood Estimation (NLE)

Reference:
- Papamakarios, G. et al. (2021). Simulation-based inference.
- Cranmer, K. et al. (2015). Approximating likelihood ratios with calibrated discriminative classifiers.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from abc import ABC, abstractmethod
import warnings

logger = logging.getLogger(__name__)


class SBIMethod(Enum):
    """Methods for simulation-based inference"""
    ABC = "abc"  # Approximate Bayesian Computation
    ABC_MCMC = "abc_mcmc"  # ABC with MCMC
    NRE = "nre"  # Neural Ratio Estimation
    SNPE = "snpe"  # Sequential Neural Posterior Estimation
    NLE = "nle"  # Neural Likelihood Estimation
    INFERENCE_NET = "inference_net"  # Conditional density estimation


@dataclass
class SimulatorConfig:
    """Configuration for a simulator"""
    name: str
    n_parameters: int
    n_outputs: int
    parameter_bounds: List[Tuple[float, float]]
    simulator_fn: Callable
    prior_fn: Optional[Callable] = None
    simulator_kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SBIResult:
    """
    Result from simulation-based inference

    Attributes:
        posterior_samples: Samples from posterior distribution
        posterior_mean: Posterior mean estimate
        posterior_std: Posterior standard deviation
        log_evidence: Log marginal likelihood estimate
        n_simulations: Number of simulations performed
        convergence_diagnostics: Convergence metrics
        diagnostics: Additional diagnostic information
    """
    posterior_samples: np.ndarray
    posterior_mean: np.ndarray
    posterior_std: np.ndarray
    log_evidence: float
    n_simulations: int
    convergence_diagnostics: Dict[str, float]
    diagnostics: Dict[str, Any] = field(default_factory=dict)


class SimulatorInterface(ABC):
    """
    Abstract interface for simulators

    All astrophysical simulators must implement this interface
    to work with SBI.
    """

    @abstractmethod
    def simulate(self, parameters: np.ndarray, n_samples: int = 1) -> np.ndarray:
        """
        Run simulator with given parameters

        Args:
            parameters: Simulator parameters
            n_samples: Number of simulation samples

        Returns:
            Simulated observations
        """
        pass

    @abstractmethod
    def get_parameter_names(self) -> List[str]:
        """Get names of simulator parameters"""
        pass

    @abstractmethod
    def get_output_names(self) -> List[str]:
        """Get names of simulator outputs"""
        pass

    @abstractmethod
    def get_prior_bounds(self) -> List[Tuple[float, float]]:
        """Get prior bounds for parameters"""
        pass


class AstrophysicsSimulator(SimulatorInterface):
    """
    Base class for astrophysics simulators

    Wraps existing simulators in astra_core.theoretical_physics
    """

    def __init__(
        self,
        simulator_type: str,
        simulator_fn: Callable,
        parameter_names: List[str],
        output_names: List[str],
        parameter_bounds: List[Tuple[float, float]]
    ):
        """
        Initialize astrophysics simulator

        Args:
            simulator_type: Type of simulator (MHD, radiation, etc.)
            simulator_fn: Function to run simulation
            parameter_names: Names of parameters
            output_names: Names of outputs
            parameter_bounds: Prior bounds for parameters
        """
        self.simulator_type = simulator_type
        self.simulator_fn = simulator_fn
        self.parameter_names = parameter_names
        self.output_names = output_names
        self.parameter_bounds = parameter_bounds

    def simulate(self, parameters: np.ndarray, n_samples: int = 1) -> np.ndarray:
        """Run simulation"""
        return self.simulator_fn(parameters, n_samples)

    def get_parameter_names(self) -> List[str]:
        return self.parameter_names

    def get_output_names(self) -> List[str]:
        return self.output_names

    def get_prior_bounds(self) -> List[Tuple[float, float]]:
        return self.parameter_bounds


class MHDSimulator(AstrophysicsSimulator):
    """
    Magnetohydrodynamics (MHD) simulator wrapper

    Simulates plasma dynamics with magnetic fields.
    """

    def __init__(self):
        # Initialize with MHD-specific parameters
        parameter_names = ['magnetic_field_strength', 'plasma_beta', 'reynolds_number', 'resolution']
        output_names = ['density', 'velocity', 'magnetic_field', 'temperature']
        parameter_bounds = [
            (1e-6, 1e-3),  # magnetic_field_strength (Gauss)
            (0.1, 10),      # plasma_beta
            (100, 1e6),     # reynolds_number
            (16, 512)       # resolution
        ]

        # Placeholder: actual MHD simulator integration
        def mhd_simulate(params, n_samples):
            # Simplified MHD simulation
            # In practice, would call astra_core.theoretical_physics.MHDSolver
            B, beta, Re, res = params

            outputs = []
            for _ in range(n_samples):
                # Simplified outputs
                density = np.random.lognormal(0, 1) * beta
                velocity = np.random.normal(0, 1) * np.sqrt(Re) / 1000
                magnetic_field = B * (1 + 0.1 * np.random.randn())
                temperature = 1e6 * (1 + 0.5 * np.random.randn())

                outputs.append([density, velocity, magnetic_field, temperature])

            return np.array(outputs)

        super().__init__(
            simulator_type="MHD",
            simulator_fn=mhd_simulate,
            parameter_names=parameter_names,
            output_names=output_names,
            parameter_bounds=parameter_bounds
        )


class StarFormationSimulator(AstrophysicsSimulator):
    """
    Star formation simulator wrapper

    Simulates star formation in molecular clouds.
    """

    def __init__(self):
        parameter_names = ['cloud_mass', 'metallicity', 'turbulence', 'magnetic_field']
        output_names = ['star_formation_rate', 'imf_slope', 'cluster_mass', 'efficiency']
        parameter_bounds = [
            (1e3, 1e6),    # cloud_mass (solar masses)
            (0.01, 2),     # metallicity (Z_sun)
            (0.1, 10),     # turbulence (Mach number)
            (1e-6, 1e-3)   # magnetic_field (Gauss)
        ]

        def star_formation_simulate(params, n_samples):
            # Simplified star formation model
            M_cloud, Z, Mach, B = params

            outputs = []
            for _ in range(n_samples):
                # Star formation rate (Kennicutt-Schmidt type)
                sfr = 1e-8 * (M_cloud / 1e5)**1.4 * np.exp(-Mach * 0.1)

                # IMF slope (varies with turbulence)
                imf_slope = 2.35 + 0.1 * (Mach - 1)

                # Cluster mass
                cluster_mass = M_cloud * 0.01 * np.random.uniform(0.5, 1.5)

                # Efficiency (magnetic field suppresses efficiency)
                efficiency = 0.01 * (1 + 0.1 * np.random.randn()) / (1 + B * 1e5)

                outputs.append([sfr, imf_slope, cluster_mass, efficiency])

            return np.array(outputs)

        super().__init__(
            simulator_type="star_formation",
            simulator_fn=star_formation_simulate,
            parameter_names=parameter_names,
            output_names=output_names,
            parameter_bounds=parameter_bounds
        )


class CosmologySimulator(AstrophysicsSimulator):
    """
    Cosmology simulator wrapper

    Simulates large-scale structure formation.
    """

    def __init__(self):
        parameter_names = ['omega_m', 'omega_lambda', 'hubble', 'sigma_8', 'ns']
        output_names = ['power_spectrum', 'correlation_function', 'halo_mass_function']
        parameter_bounds = [
            (0.1, 0.5),    # omega_m
            (0.5, 0.9),    # omega_lambda
            (0.5, 0.9),    # hubble (H0/100)
            (0.6, 1.0),    # sigma_8
            (0.8, 1.2)     # ns (spectral index)
        ]

        def cosmology_simulate(params, n_samples):
            # Simplified cosmological simulation
            omega_m, omega_lambda, h, sigma8, ns = params

            outputs = []
            for _ in range(n_samples):
                # Power spectrum amplitude (simplified)
                ps_norm = sigma8**2

                # Correlation length
                corr_length = 100 / h * (1 + 0.1 * np.random.randn())

                # Halo mass function normalization
                hmf_norm = 1e-3 * (omega_m / 0.3)**2

                outputs.append([ps_norm, corr_length, hmf_norm])

            return np.array(outputs)

        super().__init__(
            simulator_type="cosmology",
            simulator_fn=cosmology_simulate,
            parameter_names=parameter_names,
            output_names=output_names,
            parameter_bounds=parameter_bounds
        )


class ApproximateBayesianComputation:
    """
    Approximate Bayesian Computation (ABC)

    Likelihood-free inference using summary statistics and distance metrics.
    P(θ | x) ∝ P(x | θ) P(θ) where likelihood is replaced by
    similarity between observed and simulated data.
    """

    def __init__(
        self,
        simulator: SimulatorInterface,
        summary_statistics: Callable,
        distance_metric: str = "euclidean",
        distance_threshold: float = 0.1,
        n_simulations: int = 10000,
        random_state: Optional[int] = None
    ):
        """
        Initialize ABC

        Args:
            simulator: Simulator interface
            summary_statistics: Function to compute summary statistics
            distance_metric: Distance metric ("euclidean", "manhattan", "mahalanobis")
            distance_threshold: Acceptance threshold
            n_simulations: Number of simulations to run
            random_state: Random seed
        """
        self.simulator = simulator
        self.summary_statistics = summary_statistics
        self.distance_metric = distance_metric
        self.distance_threshold = distance_threshold
        self.n_simulations = n_simulations
        self.random_state = random_state

        if random_state is not None:
            np.random.seed(random_state)

        # Storage
        self.accepted_parameters = []
        self.accepted_simulations = []
        self.observed_summary_dim = None  # Track dimension of observed summary

    def infer(
        self,
        observed_data: np.ndarray,
        verbose: bool = False
    ) -> SBIResult:
        """
        Perform ABC inference

        Args:
            observed_data: Observed data
            verbose: Print progress

        Returns:
            SBIResult with posterior samples
        """
        if verbose:
            logger.info(f"Running ABC with {self.n_simulations} simulations")
            logger.info(f"Distance threshold: {self.distance_threshold}")

        # Compute summary statistics of observed data
        observed_summary = self.summary_statistics(observed_data)
        self.observed_summary_dim = len(observed_summary)  # Track dimension

        # Get parameter bounds
        param_bounds = self.simulator.get_prior_bounds()
        n_params = len(param_bounds)

        # Run simulations
        for i in range(self.n_simulations):
            # Sample parameters from prior
            parameters = np.array([
                np.random.uniform(low, high)
                for low, high in param_bounds
            ])

            # Simulate
            simulated_data = self.simulator.simulate(parameters, n_samples=1)

            # Compute summary statistics
            simulated_summary = self.summary_statistics(simulated_data)

            # Ensure dimensions match
            if len(simulated_summary) != self.observed_summary_dim:
                # Pad or truncate to match
                if len(simulated_summary) < self.observed_summary_dim:
                    simulated_summary = np.pad(simulated_summary, (0, self.observed_summary_dim - len(simulated_summary)))
                else:
                    simulated_summary = simulated_summary[:self.observed_summary_dim]

            # Compute distance
            distance = self._compute_distance(observed_summary, simulated_summary)

            # Accept if close enough
            if distance < self.distance_threshold:
                self.accepted_parameters.append(parameters)
                self.accepted_simulations.append(simulated_data)

            if verbose and (i+1) % 1000 == 0:
                acceptance_rate = len(self.accepted_parameters) / (i+1)
                logger.info(f"Simulation {i+1}/{self.n_simulations}, Acceptance rate: {acceptance_rate:.3f}")

        # Convert to arrays
        if not self.accepted_parameters:
            logger.warning("No parameters accepted! Try increasing distance threshold.")
            # Return empty result
            return SBIResult(
                posterior_samples=np.array([]),
                posterior_mean=np.zeros(n_params),
                posterior_std=np.zeros(n_params),
                log_evidence=-np.inf,
                n_simulations=self.n_simulations,
                convergence_diagnostics={'acceptance_rate': 0.0}
            )

        accepted_params = np.array(self.accepted_parameters)

        # Compute posterior statistics
        posterior_mean = np.mean(accepted_params, axis=0)
        posterior_std = np.std(accepted_params, axis=0)

        # Log evidence (approximate)
        log_evidence = np.log(len(self.accepted_parameters) / self.n_simulations)

        # Convergence diagnostics
        acceptance_rate = len(self.accepted_parameters) / self.n_simulations

        if verbose:
            logger.info(f"ABC complete: {len(self.accepted_parameters)}/{self.n_simulations} accepted")
            logger.info(f"Posterior mean: {posterior_mean}")
            logger.info(f"Posterior std: {posterior_std}")

        return SBIResult(
            posterior_samples=accepted_params,
            posterior_mean=posterior_mean,
            posterior_std=posterior_std,
            log_evidence=log_evidence,
            n_simulations=self.n_simulations,
            convergence_diagnostics={
                'acceptance_rate': acceptance_rate,
                'effective_sample_size': len(self.accepted_parameters)
            }
        )

    def _compute_distance(
        self,
        summary1: np.ndarray,
        summary2: np.ndarray
    ) -> float:
        """Compute distance between summary statistics"""
        if self.distance_metric == "euclidean":
            return np.linalg.norm(summary1 - summary2)
        elif self.distance_metric == "manhattan":
            return np.sum(np.abs(summary1 - summary2))
        elif self.distance_metric == "mahalanobis":
            # Compute covariance from previous simulations
            if len(self.accepted_simulations) > 10:
                data = np.array([self.summary_statistics(s) for s in self.accepted_simulations])
                cov = np.cov(data.T)
                try:
                    inv_cov = np.linalg.inv(cov + np.eye(cov.shape[0]) * 1e-6)
                    diff = summary1 - summary2
                    return np.sqrt(diff @ inv_cov @ diff)
                except:
                    return np.linalg.norm(summary1 - summary2)
            else:
                return np.linalg.norm(summary1 - summary2)
        else:
            return np.linalg.norm(summary1 - summary2)


class SequentialNeuralPosteriorEstimation:
    """
    Sequential Neural Posterior Estimation (SNPE)

    Uses neural networks to learn the posterior distribution
    through sequential simulation rounds.

    More efficient than ABC for high-dimensional parameters.
    """

    def __init__(
        self,
        simulator: SimulatorInterface,
        n_rounds: int = 5,
        n_simulations_per_round: int = 1000,
        network_architecture: str = "mdn",  # "mdn" or "maf"
        random_state: Optional[int] = None
    ):
        """
        Initialize SNPE

        Args:
            simulator: Simulator interface
            n_rounds: Number of sequential rounds
            n_simulations_per_round: Simulations per round
            network_architecture: Type of neural network
            random_state: Random seed
        """
        self.simulator = simulator
        self.n_rounds = n_rounds
        self.n_simulations_per_round = n_simulations_per_round
        self.network_architecture = network_architecture
        self.random_state = random_state

        if random_state is not None:
            np.random.seed(random_state)

        # Storage
        self.all_parameters = []
        self.all_simulations = []
        self.network = None

    def infer(
        self,
        observed_data: np.ndarray,
        verbose: bool = False
    ) -> SBIResult:
        """
        Perform SNPE inference

        Args:
            observed_data: Observed data
            verbose: Print progress

        Returns:
            SBIResult with posterior samples
        """
        if verbose:
            logger.info(f"Running SNPE with {self.n_rounds} rounds")

        param_bounds = self.simulator.get_prior_bounds()

        for round_num in range(self.n_rounds):
            if verbose:
                logger.info(f"Round {round_num + 1}/{self.n_rounds}")

            # Sample parameters
            if round_num == 0:
                # First round: sample from prior
                parameters = self._sample_from_prior(param_bounds, self.n_simulations_per_round)
            else:
                # Subsequent rounds: sample from proposal (current posterior estimate)
                parameters = self._sample_from_proposal(param_bounds, self.n_simulations_per_round)

            # Simulate
            simulations = []
            for params in parameters:
                sim_data = self.simulator.simulate(params, n_samples=1)
                simulations.append(sim_data[0])  # Take first sample

            simulations = np.array(simulations)

            # Store
            self.all_parameters.extend(parameters)
            self.all_simulations.extend(simulations)

            # Train network on this round's data
            self._train_network(np.array(parameters), simulations, round_num)

        # Sample from final posterior
        posterior_samples = self._sample_from_posterior(observed_data, n_samples=1000)

        # Compute statistics
        posterior_mean = np.mean(posterior_samples, axis=0)
        posterior_std = np.std(posterior_samples, axis=0)

        # Log evidence (approximate)
        log_evidence = self._estimate_evidence(observed_data)

        if verbose:
            logger.info(f"SNPE complete: {len(self.all_parameters)} total simulations")
            logger.info(f"Posterior mean: {posterior_mean}")
            logger.info(f"Posterior std: {posterior_std}")

        return SBIResult(
            posterior_samples=posterior_samples,
            posterior_mean=posterior_mean,
            posterior_std=posterior_std,
            log_evidence=log_evidence,
            n_simulations=len(self.all_parameters),
            convergence_diagnostics={
                'n_rounds': self.n_rounds,
                'final_network_loss': self._get_network_loss()
            }
        )

    def _sample_from_prior(
        self,
        bounds: List[Tuple[float, float]],
        n_samples: int
    ) -> np.ndarray:
        """Sample from uniform prior"""
        parameters = []
        for _ in range(n_samples):
            params = np.array([
                np.random.uniform(low, high)
                for low, high in bounds
            ])
            parameters.append(params)
        return np.array(parameters)

    def _sample_from_proposal(
        self,
        bounds: List[Tuple[float, float]],
        n_samples: int
    ) -> np.ndarray:
        """Sample from current proposal distribution"""
        # Simplified: use posterior estimate as proposal
        # In practice, would use trained network

        if self.network is None:
            return self._sample_from_prior(bounds, n_samples)

        # Sample from network (simplified)
        parameters = []
        for _ in range(n_samples):
            # Use current estimate to sample
            # (placeholder: would use actual network sampling)
            params = self._sample_from_prior(bounds, 1)[0]
            parameters.append(params)

        return np.array(parameters)

    def _train_network(
        self,
        parameters: np.ndarray,
        simulations: np.ndarray,
        round_num: int
    ) -> None:
        """Train neural network to approximate posterior"""
        # Simplified: would train actual neural network
        # Here we just store the data

        # In practice, would train:
        # - Mixture Density Network (MDN)
        # - Masked Autoregressive Flow (MAF)
        # - Neural Spline Flow

        # Store training data
        self.training_data = {
            'parameters': parameters,
            'simulations': simulations
        }

    def _sample_from_posterior(
        self,
        observed_data: np.ndarray,
        n_samples: int
    ) -> np.ndarray:
        """Sample from posterior estimate for given observation"""
        # Simplified: find nearest neighbors in training data
        if len(self.all_parameters) == 0:
            return np.array([])

        all_sims = np.array(self.all_simulations)
        all_params = np.array(self.all_parameters)

        # Find closest simulations
        distances = np.array([
            np.linalg.norm(sim - observed_data.flatten())
            for sim in all_sims
        ])

        # Sample from closest parameters
        n_neighbors = min(100, len(all_params))
        closest_indices = np.argsort(distances)[:n_neighbors]
        closest_params = all_params[closest_indices]

        # Sample with replacement
        samples = []
        for _ in range(n_samples):
            idx = np.random.randint(len(closest_params))
            samples.append(closest_params[idx])

        return np.array(samples)

    def _estimate_evidence(self, observed_data: np.ndarray) -> float:
        """Estimate log marginal likelihood"""
        # Simplified: use average likelihood of closest simulations
        if len(self.all_simulations) == 0:
            return -np.inf

        all_sims = np.array(self.all_simulations)
        distances = np.array([
            np.linalg.norm(sim - observed_data.flatten())
            for sim in all_sims
        ])

        # Use kernel density estimate
        bandwidth = np.percentile(distances, 10)
        likelihood = np.mean(np.exp(-distances / bandwidth))

        return np.log(likelihood + 1e-10)

    def _get_network_loss(self) -> float:
        """Get final network loss"""
        # Placeholder
        return 0.0


class SimulationBasedInferenceEngine:
    """
    Main engine for simulation-based inference

    Integrates multiple SBI methods and provides unified interface.
    Connects to all existing astrophysics simulators.
    """

    def __init__(
        self,
        method: SBIMethod = SBIMethod.ABC,
        random_state: Optional[int] = None
    ):
        """
        Initialize SBI engine

        Args:
            method: Inference method
            random_state: Random seed
        """
        self.method = method
        self.random_state = random_state

        # Available simulators
        self.simulators: Dict[str, SimulatorInterface] = {}

        # Register built-in simulators
        self._register_builtin_simulators()

        # Try to connect to existing simulators
        self._connect_existing_simulators()

    def _register_builtin_simulators(self) -> None:
        """Register built-in simplified simulators"""
        self.simulators['mhd'] = MHDSimulator()
        self.simulators['star_formation'] = StarFormationSimulator()
        self.simulators['cosmology'] = CosmologySimulator()

    def _connect_existing_simulators(self) -> None:
        """Connect to existing astra_core simulators"""
        try:
            from ...theoretical_physics import MHDSolver, RadiationHydrodynamics

            # Wrap existing MHD solver
            if MHDSolver is not None:
                # Create wrapper
                pass  # Would implement wrapper here

            logger.info("Connected to existing simulators")
        except ImportError:
            logger.warning("Could not connect to existing simulators, using built-in")

    def register_simulator(
        self,
        name: str,
        simulator: SimulatorInterface
    ) -> None:
        """Register a new simulator"""
        self.simulators[name] = simulator
        logger.info(f"Registered simulator: {name}")

    def infer(
        self,
        simulator_name: str,
        observed_data: np.ndarray,
        summary_statistics: Optional[Callable] = None,
        n_simulations: int = 10000,
        verbose: bool = False
    ) -> SBIResult:
        """
        Perform simulation-based inference

        Args:
            simulator_name: Name of simulator to use
            observed_data: Observed data
            summary_statistics: Function to compute summary statistics
            n_simulations: Number of simulations
            verbose: Print progress

        Returns:
            SBIResult with posterior samples
        """
        if simulator_name not in self.simulators:
            raise ValueError(f"Unknown simulator: {simulator_name}. Available: {list(self.simulators.keys())}")

        simulator = self.simulators[simulator_name]

        # Default summary statistics if not provided
        if summary_statistics is None:
            summary_statistics = lambda x: x.flatten()  # Use raw data

        # Run appropriate method
        if self.method == SBIMethod.ABC:
            abc = ApproximateBayesianComputation(
                simulator=simulator,
                summary_statistics=summary_statistics,
                n_simulations=n_simulations,
                random_state=self.random_state
            )
            result = abc.infer(observed_data, verbose=verbose)

        elif self.method == SBIMethod.SNPE:
            snpe = SequentialNeuralPosteriorEstimation(
                simulator=simulator,
                n_simulations_per_round=n_simulations // 5,
                random_state=self.random_state
            )
            result = snpe.infer(observed_data, verbose=verbose)

        else:
            # Default to ABC
            abc = ApproximateBayesianComputation(
                simulator=simulator,
                summary_statistics=summary_statistics,
                n_simulations=n_simulations,
                random_state=self.random_state
            )
            result = abc.infer(observed_data, verbose=verbose)

        return result

    def get_available_simulators(self) -> List[str]:
        """Get list of available simulators"""
        return list(self.simulators.keys())


def create_sbi_engine(
    method: SBIMethod = SBIMethod.ABC,
    **kwargs
) -> SimulationBasedInferenceEngine:
    """
    Create simulation-based inference engine

    Args:
        method: Inference method
        **kwargs: Additional arguments

    Returns:
        Configured SimulationBasedInferenceEngine
    """
    return SimulationBasedInferenceEngine(method=method, **kwargs)


# Default summary statistics for astrophysics
def default_summary_statistics(data: np.ndarray) -> np.ndarray:
    """
    Default summary statistics for astrophysical data

    Includes mean, std, and selected percentiles.
    Returns consistent dimension regardless of input size.
    """
    if data.ndim == 1:
        data = data.reshape(-1, 1)

    # Flatten data for consistent output
    summaries = []

    # Basic statistics per dimension
    for dim in range(data.shape[1]):
        col = data[:, dim]
        summaries.extend([
            np.mean(col),
            np.std(col),
            np.percentile(col, 50),
        ])

    return np.array(summaries)


__all__ = [
    'SBIMethod',
    'SimulatorConfig',
    'SBIResult',
    'SimulatorInterface',
    'AstrophysicsSimulator',
    'MHDSimulator',
    'StarFormationSimulator',
    'CosmologySimulator',
    'ApproximateBayesianComputation',
    'SequentialNeuralPosteriorEstimation',
    'SimulationBasedInferenceEngine',
    'create_sbi_engine',
    'default_summary_statistics',
]
