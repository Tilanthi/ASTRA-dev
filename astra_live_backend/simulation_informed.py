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
ASTRA Live — Simulation-Informed Discovery
Use MHD simulation results to guide and interpret observational discoveries.

This module bridges the gap between simulations and observations by:
  - Matching observations to simulation conditions
  - Predicting unobserved quantities from simulations
  - Using simulation parameter space to guide observational searches
  - Validating discoveries against simulation physics

Key Features:
  - Simulation database for MHD results
  - Parameter space interpolation
  - Observation-simulation matching
  - Simulation-driven hypothesis generation
"""

import numpy as np
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import json

# Handle optional sklearn imports
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, ConstantKernel, Matern
    from sklearn.neighbors import NearestNeighbors
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    from warnings import warn
    warn("scikit-learn not available. Simulation interpolation will be limited.")


@dataclass
class SimulationResult:
    """Result from an MHD simulation."""
    simulation_id: str
    parameters: Dict[str, float]  # e.g., mach, beta, rho_c, etc.
    metrics: Dict[str, float]     # e.g., lambda_W, n_cores, etc.
    metadata: Dict[str, Any] = None
    data_path: Optional[str] = None


@dataclass
class SimulationMatch:
    """Result from matching observation to simulation."""
    simulation_id: str
    match_score: float  # 0-1, higher = better match
    matched_parameters: Dict[str, float]
    predicted_metrics: Dict[str, float]
    explanation: str


class SimulationDatabase:
    """
    Database of MHD simulation results.

    Stores and queries simulation results for parameter space exploration.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize simulation database.

        Args:
            storage_path: Path to JSON file for persistent storage
        """
        self.storage_path = storage_path
        self.simulations: Dict[str, SimulationResult] = {}
        self.parameter_names: List[str] = []
        self.metric_names: List[str] = []

        # Load from file if exists
        if storage_path and Path(storage_path).exists():
            self.load()

    def add_simulation(self, result: SimulationResult) -> None:
        """Add a simulation result to the database."""
        self.simulations[result.simulation_id] = result

        # Update parameter/metric names
        if not self.parameter_names:
            self.parameter_names = list(result.parameters.keys())
        if not self.metric_names:
            self.metric_names = list(result.metrics.keys())

        # Save if path specified
        if self.storage_path:
            self.save()

    def load(self) -> None:
        """Load simulations from JSON file."""
        if not self.storage_path or not Path(self.storage_path).exists():
            return

        with open(self.storage_path, 'r') as f:
            data = json.load(f)

        for sim_data in data.get('simulations', []):
            result = SimulationResult(
                simulation_id=sim_data['simulation_id'],
                parameters=sim_data['parameters'],
                metrics=sim_data['metrics'],
                metadata=sim_data.get('metadata'),
                data_path=sim_data.get('data_path')
            )
            self.simulations[result.simulation_id] = result

        self.parameter_names = data.get('parameter_names', [])
        self.metric_names = data.get('metric_names', [])

    def save(self) -> None:
        """Save simulations to JSON file."""
        if not self.storage_path:
            return

        data = {
            'parameter_names': self.parameter_names,
            'metric_names': self.metric_names,
            'simulations': [
                {
                    'simulation_id': sim.simulation_id,
                    'parameters': sim.parameters,
                    'metrics': sim.metrics,
                    'metadata': sim.metadata,
                    'data_path': sim.data_path
                }
                for sim in self.simulations.values()
            ]
        }

        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_parameter_matrix(self) -> np.ndarray:
        """Get all simulation parameters as a matrix."""
        if not self.simulations:
            return np.array([])

        n_sims = len(self.simulations)
        n_params = len(self.parameter_names)

        matrix = np.zeros((n_sims, n_params))
        for i, sim in enumerate(self.simulations.values()):
            for j, param in enumerate(self.parameter_names):
                matrix[i, j] = sim.parameters.get(param, 0.0)

        return matrix

    def get_metric_matrix(self) -> np.ndarray:
        """Get all simulation metrics as a matrix."""
        if not self.simulations:
            return np.array([])

        n_sims = len(self.simulations)
        n_metrics = len(self.metric_names)

        matrix = np.zeros((n_sims, n_metrics))
        for i, sim in enumerate(self.simulations.values()):
            for j, metric in enumerate(self.metric_names):
                matrix[i, j] = sim.metrics.get(metric, 0.0)

        return matrix


class SimulationInformedDiscovery:
    """
    Use simulations to inform observational discovery.

    This class provides methods to:
    - Match observations to simulation conditions
    - Interpolate in parameter space
    - Predict quantities not yet observed
    - Generate simulation-based hypotheses

    Example:
        >>> discovery = SimulationInformedDiscovery()
        >>> discovery.load_simulation_results('fragmentation_results.json')
        >>> match = discovery.match_observation_to_simulation(obs_data)
        >>> print(f"Best match: {match.simulation_id}")
    """

    def __init__(self, db: Optional[SimulationDatabase] = None):
        """
        Initialize simulation-informed discovery.

        Args:
            db: SimulationDatabase (creates new if None)
        """
        self.db = db or SimulationDatabase()
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.gp_models = {}  # Gaussian Process models for interpolation
        self._fitted = False

    def load_simulation_results(
        self,
        results_path: str,
        parameter_names: List[str],
        metric_names: List[str]
    ) -> None:
        """
        Load simulation results from fragmentation analysis.

        Args:
            results_path: Path to JSON file with simulation results
            parameter_names: Names of simulation parameters
            metric_names: Names of output metrics
        """
        with open(results_path, 'r') as f:
            data = json.load(f)

        # Extract simulation data
        # (This depends on the structure of your results file)
        if 'simulations' in data:
            for sim_id, sim_data in data['simulations'].items():
                # Convert to our format
                parameters = {}
                metrics = {}

                # Extract parameters
                for param in parameter_names:
                    if param in sim_data:
                        parameters[param] = sim_data[param]

                # Extract metrics
                for metric in metric_names:
                    if metric in sim_data:
                        metrics[metric] = sim_data[metric]

                result = SimulationResult(
                    simulation_id=sim_id,
                    parameters=parameters,
                    metrics=metrics,
                    metadata=sim_data
                )

                self.db.add_simulation(result)

        self.db.parameter_names = parameter_names
        self.db.metric_names = metric_names

        print(f"Loaded {len(self.db.simulations)} simulations from {results_path}")

    def match_observation_to_simulation(
        self,
        observation: Dict[str, float],
        parameter_constraints: Optional[Dict[str, Tuple[float, float]]] = None,
        n_neighbors: int = 5
    ) -> SimulationMatch:
        """
        Match an observation to the most similar simulation(s).

        Args:
            observation: Dict of observed quantities
            parameter_constraints: Optional constraints on parameters (min, max)
            n_neighbors: Number of nearest neighbors to consider

        Returns:
            SimulationMatch with best matching simulation
        """
        if not self.db.simulations:
            raise ValueError("No simulations in database. Load simulations first.")

        # Get parameter matrix
        param_matrix = self.db.get_parameter_matrix()
        metric_matrix = self.db.get_metric_matrix()

        # Find matching parameters from observation
        # (Observation might contain metrics, not parameters)
        obs_vector = np.zeros(len(self.db.parameter_names))

        for i, param in enumerate(self.db.parameter_names):
            if param in observation:
                obs_vector[i] = observation[param]
            else:
                # Use mean value from simulations
                obs_vector[i] = np.mean(param_matrix[:, i])

        # Apply parameter constraints
        valid_mask = np.ones(len(self.db.simulations), dtype=bool)

        if parameter_constraints:
            for i, param in enumerate(self.db.parameter_names):
                if param in parameter_constraints:
                    min_val, max_val = parameter_constraints[param]
                    valid_mask &= (param_matrix[:, i] >= min_val) & \
                                 (param_matrix[:, i] <= max_val)

        if not valid_mask.any():
            # No simulations match constraints - relax and return best overall
            valid_mask = np.ones(len(self.db.simulations), dtype=bool)

        # Find nearest neighbors
        valid_indices = np.where(valid_mask)[0]
        valid_params = param_matrix[valid_indices]

        if SKLEARN_AVAILABLE:
            nn = NearestNeighbors(n_neighbors=min(n_neighbors, len(valid_indices)))
            nn.fit(valid_params)
            distances, indices = nn.kneighbors([obs_vector])

            # Convert back to original indices
            best_idx = valid_indices[indices[0][0]]
            best_distance = distances[0][0]
        else:
            # Simple Euclidean distance
            distances = np.linalg.norm(valid_params - obs_vector, axis=1)
            best_local_idx = np.argmin(distances)
            best_idx = valid_indices[best_local_idx]
            best_distance = distances[best_local_idx]

        # Get best simulation
        sim_ids = list(self.db.simulations.keys())
        best_sim_id = sim_ids[best_idx]
        best_sim = self.db.simulations[best_sim_id]

        # Compute match score (0-1)
        max_distance = np.linalg.norm(param_matrix.max(axis=0) - param_matrix.min(axis=0))
        match_score = 1.0 - (best_distance / (max_distance + 1e-10))
        match_score = max(0.0, min(1.0, match_score))

        # Predicted metrics from simulation
        predicted_metrics = best_sim.metrics.copy()

        explanation = (
            f"Observation matches simulation {best_sim_id} "
            f"with score {match_score:.2f}. "
            f"Simulation parameters: {best_sim.parameters}. "
            f"Predicted metrics: {predicted_metrics}."
        )

        return SimulationMatch(
            simulation_id=best_sim_id,
            match_score=match_score,
            matched_parameters=best_sim.parameters,
            predicted_metrics=predicted_metrics,
            explanation=explanation
        )

    def interpolate_in_parameter_space(
        self,
        target_parameters: Dict[str, float],
        target_metric: str
    ) -> Tuple[float, float]:
        """
        Interpolate to predict metric at target parameters.

        Uses Gaussian Process Regression for smooth interpolation.

        Args:
            target_parameters: Target parameter values
            target_metric: Metric to predict

        Returns:
            Tuple of (predicted_value, uncertainty)
        """
        if not SKLEARN_AVAILABLE:
            raise NotImplementedError("Interpolation requires scikit-learn")

        if not self.db.simulations:
            raise ValueError("No simulations in database")

        # Get data
        param_matrix = self.db.get_parameter_matrix()
        metric_idx = self.db.metric_names.index(target_metric)
        metric_values = self.db.get_metric_matrix()[:, metric_idx]

        # Fit GP if not already fitted for this metric
        if target_metric not in self.gp_models:
            kernel = ConstantKernel(1.0) * Matern(length_scale=1.0, nu=2.5)
            gp = GaussianProcessRegressor(kernel=kernel, alpha=0.1, normalize_y=True)
            gp.fit(param_matrix, metric_values)
            self.gp_models[target_metric] = gp

        gp = self.gp_models[target_metric]

        # Create target vector
        target_vector = np.array([target_parameters.get(p, 0.0)
                                 for p in self.db.parameter_names])

        # Predict
        predicted, std = gp.predict([target_vector], return_std=True)

        return float(predicted[0]), float(std[0])

    def generate_simulation_hypothesis(
        self,
        observation: Dict[str, float],
        target_metric: str = 'lambda_W'
    ) -> Dict[str, Any]:
        """
        Generate a hypothesis based on simulation matching.

        Args:
            observation: Observed quantities
            target_metric: Metric to focus on

        Returns:
            Hypothesis dict with description, confidence, etc.
        """
        # Match to simulation
        match = self.match_observation_to_simulation(observation)

        # Extract prediction
        if target_metric in match.predicted_metrics:
            predicted_value = match.predicted_metrics[target_metric]

            # Check if observation matches prediction
            observed_value = observation.get(target_metric)
            if observed_value is not None:
                difference = abs(predicted_value - observed_value)
                agreement = 1.0 - min(1.0, difference / (observed_value + 1e-10))
            else:
                agreement = match.match_score
        else:
            predicted_value = None
            agreement = match.match_score

        # Generate hypothesis
        hypothesis = {
            'description': (
                f"Based on simulation {match.simulation_id}, "
                f"{'expected' if predicted_value else 'predicted'} {target_metric} "
                f"{'= ' + str(predicted_value) if predicted_value else ''}"
            ),
            'confidence': match.match_score * agreement,
            'simulation_id': match.simulation_id,
            'matched_parameters': match.matched_parameters,
            'predicted_metrics': match.predicted_metrics,
            'match_score': match.match_score
        }

        return hypothesis

    def find_optimal_simulation_parameters(
        self,
        target_metrics: Dict[str, float],
        tolerance: float = 0.1
    ) -> List[SimulationMatch]:
        """
        Find simulation parameters that produce target metrics.

        Searches parameter space for simulations that match desired outputs.

        Args:
            target_metrics: Dict of desired metric values
            tolerance: Acceptable fractional tolerance

        Returns:
            List of matching simulations
        """
        matches = []

        for sim_id, sim in self.db.simulations.items():
            # Check if all target metrics match within tolerance
            all_match = True
            total_error = 0.0

            for metric, target_value in target_metrics.items():
                if metric in sim.metrics:
                    sim_value = sim.metrics[metric]
                    fractional_error = abs(sim_value - target_value) / (target_value + 1e-10)
                    total_error += fractional_error

                    if fractional_error > tolerance:
                        all_match = False
                        break

            if all_match:
                matches.append(SimulationMatch(
                    simulation_id=sim_id,
                    match_score=1.0 - total_error / len(target_metrics),
                    matched_parameters=sim.parameters,
                    predicted_metrics=sim.metrics,
                    explanation=f"Simulation matches target metrics within {tolerance*100:.0f}%"
                ))

        # Sort by match score
        matches.sort(key=lambda m: m.match_score, reverse=True)

        return matches


class FilamentSimulationGuide(SimulationInformedDiscovery):
    """
    Specialized guide for filament fragmentation simulations.

    Helps interpret observations in light of MHD simulation results.
    """

    FILAMENT_PARAMETERS = [
        'mach',           # Mach number
        'beta',           # Plasma beta
        'rho_c',          # Central density
        'supercriticality'  # f = mu/mu_crit
    ]

    FILAMENT_METRICS = [
        'lambda_W',       # Fragmentation scale / width
        'n_cores',        # Number of cores formed
        'spacing_pc',     # Core spacing in pc
        'density_max',    # Maximum density
    ]

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize filament simulation guide.

        Args:
            db_path: Path to simulation database JSON
        """
        db = SimulationDatabase(storage_path=db_path)
        super().__init__(db)

    def interpret_observed_spacing(
        self,
        observed_spacing_pc: float,
        filament_width_pc: float = 0.1
    ) -> Dict[str, Any]:
        """
        Interpret observed core spacing using simulation database.

        Args:
            observed_spacing_pc: Observed core spacing (pc)
            filament_width_pc: Filament width (pc)

        Returns:
            Interpretation with matching simulations and physics
        """
        lambda_W = observed_spacing_pc / filament_width_pc

        # Find matching simulations
        observation = {'lambda_W': lambda_W}

        # Add constraints to avoid highly supercritical simulations
        # (which don't match observations)
        constraints = {
            'supercriticality': (0.5, 5.0)  # Moderate supercriticality
        }

        match = self.match_observation_to_simulation(
            observation,
            parameter_constraints=constraints
        )

        # Generate interpretation
        interpretation = {
            'observed_lambda_W': lambda_W,
            'matched_simulation': match.simulation_id,
            'match_quality': match.match_score,
            'inferred_parameters': match.matched_parameters,
            'physics_interpretation': self._generate_physics_interpretation(
                lambda_W,
                match.matched_parameters
            )
        }

        return interpretation

    def _generate_physics_interpretation(
        self,
        lambda_W: float,
        parameters: Dict[str, float]
    ) -> str:
        """Generate physical interpretation of observed spacing."""
        parts = []

        # Supercriticality
        f = parameters.get('supercriticality', 0)
        if f < 1.0:
            parts.append("sub-critical filament")
        elif f < 3.0:
            parts.append("moderately supercritical filament")
        else:
            parts.append("highly supercritical filament")

        # Magnetic field
        beta = parameters.get('beta', 1.0)
        if beta < 0.5:
            parts.append("strong magnetic field (magnetic pressure dominated)")
        elif beta < 2.0:
            parts.append("moderate magnetic field (equipartition)")
        else:
            parts.append("weak magnetic field (gravity dominated)")

        # Spacing regime
        if lambda_W < 1.5:
            parts.append("Jeans-dominated fragmentation")
        elif lambda_W < 3.0:
            parts.append("transition regime with magnetic effects")
        else:
            parts.append("near-classical IM92 regime")

        return ", ".join(parts).capitalize()

    def suggest_simulation_tests(
        self,
        observed_lambda_W: float,
        n_suggestions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest simulation runs to test specific hypotheses.

        Args:
            observed_lambda_W: Observed spacing ratio
            n_suggestions: Number of suggestions

        Returns:
            List of suggested simulation parameters
        """
        suggestions = []

        # Suggestion 1: Test magnetic tension hypothesis
        if observed_lambda_W < 3.0:
            suggestions.append({
                'hypothesis': 'Magnetic tension reduces spacing',
                'parameters': {
                    'beta': 1.0,
                    'supercriticality': 2.0,
                    'mach': 2.0
                },
                'expected_lambda_W': observed_lambda_W,
                'rationale': 'Test if magnetic tension at equipartition can explain observed spacing'
            })

        # Suggestion 2: Test supercriticality dependence
        suggestions.append({
            'hypothesis': 'Supercriticality controls spacing',
            'parameters': {
                'beta': 1.0,
                'supercriticality': 1.5,
                'mach': 2.0
            },
            'expected_lambda_W': 2.5,
            'rationale': 'Test transition from IM92 to Jeans regime'
        })

        # Suggestion 3: Test turbulence effects
        suggestions.append({
            'hypothesis': 'Turbulent compression modifies spacing',
            'parameters': {
                'beta': 1.0,
                'supercriticality': 2.0,
                'mach': 4.0
            },
            'expected_lambda_W': 1.8,
            'rationale': 'Test if supersonic turbulence compresses spacing'
        })

        return suggestions[:n_suggestions]


# Convenience function
def interpret_with_simulations(
    observed_spacing_pc: float,
    sim_results_path: str = 'fragmentation_results.json'
) -> Dict[str, Any]:
    """
    Quick interpretation using simulation database.

    Args:
        observed_spacing_pc: Observed core spacing
        sim_results_path: Path to simulation results

    Returns:
        Interpretation dict
    """
    guide = FilamentSimulationGuide()
    guide.load_simulation_results(
        sim_results_path,
        parameter_names=FilamentSimulationGuide.FILAMENT_PARAMETERS,
        metric_names=FilamentSimulationGuide.FILAMENT_METRICS
    )

    return guide.interpret_observed_spacing(observed_spacing_pc)


if __name__ == '__main__':
    # Test simulation-informed discovery
    print("Testing Simulation-Informed Discovery...")

    # Create test database
    db = SimulationDatabase()

    # Add some test simulations
    test_simulations = [
        SimulationResult(
            simulation_id='test_beta1.0_f2.0',
            parameters={'beta': 1.0, 'supercriticality': 2.0, 'mach': 2.0},
            metrics={'lambda_W': 2.1, 'n_cores': 10, 'spacing_pc': 0.21}
        ),
        SimulationResult(
            simulation_id='test_beta0.5_f6.6',
            parameters={'beta': 0.5, 'supercriticality': 6.6, 'mach': 2.0},
            metrics={'lambda_W': 0.95, 'n_cores': 10, 'spacing_pc': 0.095}
        ),
        SimulationResult(
            simulation_id='test_beta2.0_f1.2',
            parameters={'beta': 2.0, 'supercriticality': 1.2, 'mach': 2.0},
            metrics={'lambda_W': 3.5, 'n_cores': 8, 'spacing_pc': 0.35}
        ),
    ]

    for sim in test_simulations:
        db.add_simulation(sim)

    db.parameter_names = ['beta', 'supercriticality', 'mach']
    db.metric_names = ['lambda_W', 'n_cores', 'spacing_pc']

    # Create discovery system
    discovery = SimulationInformedDiscovery(db)

    # Match observation
    observation = {'lambda_W': 2.1, 'supercriticality': 2.0}
    match = discovery.match_observation_to_simulation(observation)

    print(f"\n{match.explanation}")

    # Generate hypothesis
    hypothesis = discovery.generate_simulation_hypothesis(observation)
    print(f"\nGenerated hypothesis: {hypothesis['description']}")
    print(f"Confidence: {hypothesis['confidence']:.2f}")
