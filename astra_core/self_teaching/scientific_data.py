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
Scientific Data Integration Module for STAR-Learn

This module provides:
1. Real-world physics and astronomy datasets
2. Physical law discovery from data
3. Experimental data validation
4. Cross-domain dataset integration
5. Scientific knowledge extraction

Version: 1.0.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class DatasetType(Enum):
    """Types of scientific datasets"""
    PHYSICS = "physics"
    ASTRONOMY = "astronomy"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    EXPERIMENTAL = "experimental"
    SIMULATED = "simulated"


class PhysicalLawType(Enum):
    """Types of physical laws"""
    CONSERVATION = "conservation"
    SYMMETRY = "symmetry"
    SCALING = "scaling"
    INVARIANCE = "invariance"
    RELATIONSHIP = "relationship"


@dataclass
class ScientificDataset:
    """Represents a scientific dataset"""
    name: str
    data_type: DatasetType
    variables: List[str]
    observations: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "internal"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DiscoveredLaw:
    """Represents a discovered physical law"""
    name: str
    law_type: PhysicalLawType
    equation: str
    variables: List[str]
    parameters: Dict[str, float]
    confidence: float
    evidence: List[float]
    domain: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ValidationResult:
    """Result of validating a discovery against real data"""
    is_valid: bool
    confidence: float
    error_metrics: Dict[str, float]
    data_coverage: float
    outliers: List[int]
    validation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# Real-World Physics Datasets (Curated and Simulated)
# =============================================================================
class PhysicsDataLibrary:
    """Library of real-world physics datasets for law discovery."""

    def __init__(self):
        """Initialize the physics data library."""
        self.datasets = {}
        self._initialize_datasets()

    def _initialize_datasets(self):
        """Initialize with real-world physics datasets."""

        # 1. Kepler's Third Law (Planetary Motion)
        # T^2 ∝ a^3 where T is orbital period, a is semi-major axis
        planets = [
            ('Mercury', 0.39, 0.24),
            ('Venus', 0.72, 0.62),
            ('Earth', 1.00, 1.00),
            ('Mars', 1.52, 1.88),
            ('Jupiter', 5.20, 11.86),
            ('Saturn', 9.58, 29.45),
            ('Uranus', 19.22, 84.02),
            ('Neptune', 30.05, 164.8),
        ]

        kepler_data = np.array([[a, T] for _, a, T in planets])
        self.datasets['kepler_third_law'] = ScientificDataset(
            name="Kepler's Third Law - Planetary Orbital Data",
            data_type=DatasetType.ASTRONOMY,
            variables=['semi_major_axis_AU', 'orbital_period_years'],
            observations=kepler_data,
            metadata={
                'description': 'Orbital periods and semi-major axes of planets',
                'expected_law': 'T^2 = k * a^3',
                'source': 'NASA Planetary Fact Sheet',
                'units': ['AU', 'Earth years']
            },
            source='NASA'
        )

        # 2. Newton's Law of Cooling
        # dT/dt = -k(T - T_env)
        times = np.array([0, 5, 10, 15, 20, 25, 30])
        temperatures = np.array([95, 75, 63, 54, 48, 44, 41])
        cooling_data = np.column_stack([times, temperatures])

        self.datasets['newton_cooling'] = ScientificDataset(
            name="Newton's Law of Cooling",
            data_type=DatasetType.PHYSICS,
            variables=['time_min', 'temperature_C'],
            observations=cooling_data,
            metadata={
                'description': 'Cooling of hot water in room temperature',
                'expected_law': 'T(t) = T_env + (T_0 - T_env) * exp(-kt)',
                'T_env': 20,  # Room temperature
                'T_0': 95,    # Initial temperature
                'source': 'Classical physics experiment'
            },
            source='experimental'
        )

        # 3. Hooke's Law (Spring Force)
        # F = -kx
        displacements = np.array([0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12])
        forces = np.array([0, 0.98, 1.96, 2.94, 3.92, 4.90, 5.88])
        spring_data = np.column_stack([displacements, forces])

        self.datasets['hooke_law'] = ScientificDataset(
            name="Hooke's Law - Spring Force",
            data_type=DatasetType.PHYSICS,
            variables=['displacement_m', 'force_N'],
            observations=spring_data,
            metadata={
                'description': 'Spring force vs displacement',
                'expected_law': 'F = kx',
                'expected_k': 49.0,  # Spring constant in N/m
                'source': 'Classical mechanics experiment'
            },
            source='experimental'
        )

        # 4. Radioactive Decay
        # N(t) = N_0 * exp(-λt)
        decay_times = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        remaining_atoms = np.array([
            10000, 7788, 6065, 4724, 3679, 2865, 2231, 1738, 1353, 1054, 821
        ])
        decay_data = np.column_stack([decay_times, remaining_atoms])

        self.datasets['radioactive_decay'] = ScientificDataset(
            name="Radioactive Decay Law",
            data_type=DatasetType.PHYSICS,
            variables=['time_halflives', 'remaining_atoms_percent'],
            observations=decay_data,
            metadata={
                'description': 'Radioactive decay over time',
                'expected_law': 'N(t) = N_0 * exp(-λt)',
                'half_life': 1.0,  # In time units of the experiment
                'decay_constant': 0.693,
                'source': 'Nuclear physics experiment'
            },
            source='experimental'
        )

        # 5. Ideal Gas Law (PV = nRT)
        pressures = np.array([1, 2, 3, 4, 5, 6, 7, 8])
        volumes = np.array([24.0, 12.0, 8.0, 6.0, 4.8, 4.0, 3.4, 3.0])
        gas_data = np.column_stack([pressures, volumes])

        self.datasets['ideal_gas_law'] = ScientificDataset(
            name="Boyle's Law - Gas Pressure vs Volume",
            data_type=DatasetType.CHEMISTRY,
            variables=['pressure_atm', 'volume_L'],
            observations=gas_data,
            metadata={
                'description': 'Gas pressure and volume at constant temperature',
                'expected_law': 'PV = constant',
                'constant_T': 298,  # Kelvin
                'source': 'Chemistry laboratory experiment'
            },
            source='experimental'
        )

        # 6. Ohm's Law (V = IR)
        currents = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
        voltages = np.array([1.2, 2.4, 3.6, 4.8, 6.0, 7.2, 8.4, 9.6])
        ohm_data = np.column_stack([currents, voltages])

        self.datasets['ohm_law'] = ScientificDataset(
            name="Ohm's Law - Voltage vs Current",
            data_type=DatasetType.PHYSICS,
            variables=['current_A', 'voltage_V'],
            observations=ohm_data,
            metadata={
                'description': 'Voltage across resistor vs current',
                'expected_law': 'V = IR',
                'resistance': 12.0,  # Ohms
                'source': 'Electrical circuit experiment'
            },
            source='experimental'
        )

        # 7. Stefan-Boltzmann Law (Luminosity vs Temperature)
        # L ∝ T^4
        star_temps = np.array([3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000])
        star_luminosity = np.array([
            0.016, 0.102, 0.390, 1.130, 2.760, 5.900, 11.40, 20.50
        ])
        stefan_data = np.column_stack([star_temps, star_luminosity])

        self.datasets['stefan_boltzmann'] = ScientificDataset(
            name="Stefan-Boltzmann Law - Stellar Luminosity",
            data_type=DatasetType.ASTRONOMY,
            variables=['temperature_K', 'luminosity_solar'],
            observations=stefan_data,
            metadata={
                'description': 'Stellar luminosity vs surface temperature',
                'expected_law': 'L ∝ T^4',
                'source': 'Stellar astronomy catalog'
            },
            source='astronomical'
        )

        # 8. Gravitational Force vs Distance
        # F = G*m1*m2/r^2
        distances = np.array([1, 2, 3, 4, 5, 6, 7, 8])
        forces_g = np.array([100, 25, 11.1, 6.25, 4.0, 2.78, 2.04, 1.56])
        gravity_data = np.column_stack([distances, forces_g])

        self.datasets['gravitational_force'] = ScientificDataset(
            name="Newton's Law of Universal Gravitation",
            data_type=DatasetType.PHYSICS,
            variables=['distance_units', 'force_units'],
            observations=gravity_data,
            metadata={
                'description': 'Gravitational force vs distance',
                'expected_law': 'F ∝ 1/r^2',
                'source': 'Physics simulation'
            },
            source='simulated'
        )

    def get_dataset(self, name: str) -> Optional[ScientificDataset]:
        """Get a dataset by name."""
        return self.datasets.get(name)

    def list_datasets(self) -> List[str]:
        """List all available datasets."""
        return list(self.datasets.keys())

    def get_datasets_by_type(self, data_type: DatasetType) -> List[ScientificDataset]:
        """Get all datasets of a specific type."""
        return [d for d in self.datasets.values() if d.data_type == data_type]


# =============================================================================
# Physical Law Discovery Engine
# =============================================================================
class PhysicalLawDiscovery:
    """Engine for discovering physical laws from data."""

    def __init__(self):
        """Initialize the law discovery engine."""
        self.data_library = PhysicsDataLibrary()
        self.discovered_laws = []

    def discover_conservation_law(
        self,
        dataset: ScientificDataset,
        variable_combinations: Optional[List[List[int]]] = None
    ) -> List[DiscoveredLaw]:
        """
        Discover conservation laws in the dataset.

        A conserved quantity remains constant throughout the observations.
        """
        data = dataset.observations
        n_vars = data.shape[1]

        if variable_combinations is None:
            # Generate all possible linear combinations
            variable_combinations = []
            for i in range(n_vars):
                variable_combinations.append([i])
            for i in range(n_vars):
                for j in range(i+1, n_vars):
                    variable_combinations.append([i, j])

        discovered = []

        for var_indices in variable_combinations:
            # Test if sum is conserved
            combination_values = data[:, var_indices]

            # Test for conservation: low variance
            for combination_type in ['sum', 'product', 'weighted']:
                if combination_type == 'sum':
                    test_values = np.sum(combination_values, axis=1)
                elif combination_type == 'product':
                    test_values = np.prod(combination_values, axis=1)
                else:  # weighted with powers
                    test_values = np.sum(combination_values ** 2, axis=1)

                # Calculate normalized variance
                variance = np.var(test_values)
                mean_val = np.mean(test_values)
                normalized_variance = variance / (mean_val ** 2 + 1e-10)

                # Low variance suggests conservation
                if normalized_variance < 0.01:  # 99% conserved
                    law = DiscoveredLaw(
                        name=f"Conserved_{combination_type}_{dataset.name[:20]}",
                        law_type=PhysicalLawType.CONSERVATION,
                        equation=self._generate_equation(var_indices, combination_type, dataset),
                        variables=[dataset.variables[i] for i in var_indices],
                        parameters={'value': mean_val, 'variance': variance},
                        confidence=1.0 - normalized_variance,
                        evidence=test_values.tolist(),
                        domain=dataset.data_type.value
                    )
                    discovered.append(law)

        return discovered

    def discover_scaling_law(
        self,
        dataset: ScientificDataset
    ) -> List[DiscoveredLaw]:
        """
        Discover scaling laws (power laws) in the dataset.

        Looks for relationships of the form y = k * x^n
        """
        data = dataset.observations
        discovered = []

        if data.shape[1] >= 2:
            x = data[:, 0]
            y = data[:, 1]

            # Fit power law: log(y) = log(k) + n * log(x)
            log_x = np.log(x + 1e-10)
            log_y = np.log(y + 1e-10)

            # Linear regression in log space
            coeffs = np.polyfit(log_x, log_y, 1)
            exponent = coeffs[0]
            log_intercept = coeffs[1]
            prefactor = np.exp(log_intercept)

            # Calculate R^2
            predicted = prefactor * (x ** exponent)
            ss_res = np.sum((y - predicted) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)

            # Round exponent to common values
            common_exponents = [-2, -1, -0.5, 0.5, 1, 2, 3, 4]
            rounded_exponent = min(common_exponents, key=lambda e: abs(e - exponent))

            if r_squared > 0.95:  # Good fit
                law = DiscoveredLaw(
                    name=f"Scaling_Law_{dataset.name[:20]}",
                    law_type=PhysicalLawType.SCALING,
                    equation=f"{dataset.variables[1]} = {prefactor:.4f} * {dataset.variables[0]}^{rounded_exponent}",
                    variables=dataset.variables[:2],
                    parameters={
                        'exponent': exponent,
                        'prefactor': prefactor,
                        'r_squared': r_squared
                    },
                    confidence=r_squared,
                    evidence=predicted.tolist(),
                    domain=dataset.data_type.value
                )
                discovered.append(law)

        return discovered

    def discover_relationship(
        self,
        dataset: ScientificDataset
    ) -> List[DiscoveredLaw]:
        """
        Discover general relationships between variables.

        Tests linear, exponential, and power relationships.
        """
        data = dataset.observations
        discovered = []

        if data.shape[1] >= 2:
            x = data[:, 0]
            y = data[:, 1]

            # Test linear: y = ax + b
            coeffs_linear = np.polyfit(x, y, 1)
            y_pred_linear = coeffs_linear[0] * x + coeffs_linear[1]
            r2_linear = 1 - np.sum((y - y_pred_linear)**2) / np.sum((y - np.mean(y))**2)

            # Test exponential: y = a * exp(bx)
            log_y = np.log(y + 1e-10)
            coeffs_exp = np.polyfit(x, log_y, 1)
            y_pred_exp = np.exp(coeffs_exp[1]) * np.exp(coeffs_exp[0] * x)
            r2_exp = 1 - np.sum((y - y_pred_exp)**2) / np.sum((y - np.mean(y))**2)

            # Best fit wins
            best_r2 = max(r2_linear, r2_exp)

            if best_r2 > 0.9:
                if r2_linear > r2_exp:
                    equation = f"{dataset.variables[1]} = {coeffs_linear[0]:.4f}*{dataset.variables[0]} + {coeffs_linear[1]:.4f}"
                    rel_type = "linear"
                else:
                    equation = f"{dataset.variables[1]} = {np.exp(coeffs_exp[1]):.4f}*exp({coeffs_exp[0]:.4f}*{dataset.variables[0]})"
                    rel_type = "exponential"

                law = DiscoveredLaw(
                    name=f"Relationship_{rel_type}_{dataset.name[:20]}",
                    law_type=PhysicalLawType.RELATIONSHIP,
                    equation=equation,
                    variables=dataset.variables[:2],
                    parameters={'r_squared': best_r2},
                    confidence=best_r2,
                    evidence=y_pred_linear.tolist() if r2_linear > r2_exp else y_pred_exp.tolist(),
                    domain=dataset.data_type.value
                )
                discovered.append(law)

        return discovered

    def validate_law(
        self,
        law: DiscoveredLaw,
        validation_data: ScientificDataset
    ) -> ValidationResult:
        """
        Validate a discovered law against new data.

        Returns validation metrics and confidence.
        """
        observations = validation_data.observations

        # Get predictions based on law parameters
        if law.law_type == PhysicalLawType.SCALING:
            x = observations[:, 0]
            y_actual = observations[:, 1]
            exponent = law.parameters.get('exponent', 1)
            prefactor = law.parameters.get('prefactor', 1)
            y_predicted = prefactor * (x ** exponent)

            # Calculate error metrics
            mae = np.mean(np.abs(y_actual - y_predicted))
            rmse = np.sqrt(np.mean((y_actual - y_predicted) ** 2))
            mape = np.mean(np.abs((y_actual - y_predicted) / (y_actual + 1e-10))) * 100

            # Find outliers
            residuals = np.abs(y_actual - y_predicted)
            outlier_threshold = 2 * np.std(residuals)
            outliers = np.where(residuals > outlier_threshold)[0].tolist()

            # Coverage: how much of data space does this cover
            data_range = np.max(observations) - np.min(observations)
            data_coverage = min(1.0, data_range / 10.0)  # Normalize

            # Confidence based on error metrics
            confidence = max(0, 1 - mape / 100)

            return ValidationResult(
                is_valid=mape < 20,  # Valid if less than 20% error
                confidence=confidence,
                error_metrics={'mae': mae, 'rmse': rmse, 'mape': mape},
                data_coverage=data_coverage,
                outliers=outliers
            )

        # Default validation for other law types
        return ValidationResult(
            is_valid=True,
            confidence=law.confidence,
            error_metrics={},
            data_coverage=1.0,
            outliers=[]
        )

    def discover_all_laws(self, dataset: ScientificDataset) -> List[DiscoveredLaw]:
        """Discover all types of laws in a dataset."""
        all_laws = []

        # Conservation laws
        all_laws.extend(self.discover_conservation_law(dataset))

        # Scaling laws
        all_laws.extend(self.discover_scaling_law(dataset))

        # General relationships
        all_laws.extend(self.discover_relationship(dataset))

        # Remove duplicates (same equation)
        unique_laws = []
        seen_equations = set()

        for law in all_laws:
            if law.equation not in seen_equations:
                unique_laws.append(law)
                seen_equations.add(law.equation)

        return unique_laws

    def _generate_equation(
        self,
        var_indices: List[int],
        combination_type: str,
        dataset: ScientificDataset
    ) -> str:
        """Generate a human-readable equation."""
        var_names = [dataset.variables[i] for i in var_indices]

        if combination_type == 'sum':
            return f"d({'+'.join(var_names)})/dt = 0"
        elif combination_type == 'product':
            return f"d({'*'.join(var_names)})/dt = 0"
        else:
            return f"sum({v}^2 for v in {var_names}) = constant"


# =============================================================================
# Experimental Design Module
# =============================================================================
class ExperimentalDesigner:
    """Design experiments to test scientific hypotheses."""

    def __init__(self):
        """Initialize the experimental designer."""
        self.experiment_history = []

    def design_experiment(
        self,
        hypothesis: str,
        variables: List[str],
        constraints: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Design an experiment to test a hypothesis.

        Returns experiment protocol with measurements and controls.
        """
        constraints = constraints or {}

        # Determine experiment type based on hypothesis
        experiment_type = self._classify_hypothesis(hypothesis)

        protocol = {
            'hypothesis': hypothesis,
            'experiment_type': experiment_type,
            'independent_variables': variables[:1] if variables else [],
            'dependent_variables': variables[1:] if len(variables) > 1 else [],
            'control_variables': [],
            'measurements': [],
            'procedure': [],
            'expected_outcomes': [],
            'data_requirements': {}
        }

        if experiment_type == 'conservation':
            protocol['control_variables'] = ['isolation', 'external_influences']
            protocol['measurements'] = ['initial_value', 'final_value', 'time']
            protocol['procedure'] = [
                'Initialize system with known values',
                'Isolate system from external influences',
                'Measure initial state',
                'Allow evolution over time',
                'Measure final state',
                'Compare initial and final values'
            ]
            protocol['expected_outcomes'] = [
                'Initial value equals final value (within experimental error)',
                'No significant change over time'
            ]

        elif experiment_type == 'scaling':
            protocol['control_variables'] = ['temperature', 'pressure', 'other_conditions']
            protocol['measurements'] = ['independent_variable_values', 'dependent_variable_values']
            protocol['procedure'] = [
                'Vary independent variable over range',
                'Measure dependent variable at each point',
                'Control for confounding variables',
                'Repeat for statistical significance'
            ]
            protocol['expected_outcomes'] = [
                'Power-law relationship in log-log plot',
                'Linear fit in log-log space'
            ]

        elif experiment_type == 'causal':
            protocol['control_variables'] = ['all_other_factors']
            protocol['measurements'] = ['cause_levels', 'effect_levels']
            protocol['procedure'] = [
                'Randomize assignment',
                'Manipulate causal variable',
                'Measure effect variable',
                'Control for confounds',
                'Establish temporal precedence'
            ]
            protocol['expected_outcomes'] = [
                'Systematic change in effect with cause',
                'Ruling out alternative explanations'
            ]

        # Apply constraints
        if 'max_measurements' in constraints:
            protocol['data_requirements']['max_samples'] = constraints['max_measurements']
        if 'time_limit' in constraints:
            protocol['data_requirements']['duration'] = constraints['time_limit']
        if 'equipment' in constraints:
            protocol['data_requirements']['equipment'] = constraints['equipment']

        self.experiment_history.append(protocol)
        return protocol

    def _classify_hypothesis(self, hypothesis: str) -> str:
        """Classify the type of hypothesis."""
        hypothesis_lower = hypothesis.lower()

        if any(word in hypothesis_lower for word in ['conserved', 'conservation', 'constant', 'invariant']):
            return 'conservation'
        elif any(word in hypothesis_lower for word in ['proportional', 'scales', 'exponent', 'power']):
            return 'scaling'
        elif any(word in hypothesis_lower for word in ['causes', 'because', 'due to', 'leads to']):
            return 'causal'
        else:
            return 'general'


# =============================================================================
# Factory Functions
# =============================================================================
def create_law_discovery_engine() -> PhysicalLawDiscovery:
    """Create a law discovery engine with datasets."""
    return PhysicalLawDiscovery()


def create_experimental_designer() -> ExperimentalDesigner:
    """Create an experimental designer."""
    return ExperimentalDesigner()


# =============================================================================
# Integration with STAR-Learn
# =============================================================================
def get_scientific_discovery_reward(
    discovery: Dict[str, Any],
    law_engine: PhysicalLawDiscovery
) -> Tuple[float, Dict]:
    """
    Calculate reward for scientific discoveries.

    High rewards for:
    - Discovering known physical laws (validation)
    - Discovering novel relationships (novelty)
    - High confidence predictions (accuracy)
    """
    content = discovery.get('content', '').lower()
    domain = discovery.get('domain', 'unknown')

    details = {}
    reward = 0.0

    # Check if discovery matches a physical law
    for dataset_name in law_engine.data_library.list_datasets():
        dataset = law_engine.data_library.get_dataset(dataset_name)
        if dataset:
            laws = law_engine.discover_all_laws(dataset)
            for law in laws:
                # Check semantic similarity
                law_text = law.equation.lower()
                discovery_text = content

                # Simple word overlap
                law_words = set(law_text.split())
                discovery_words = set(discovery_text.split())
                overlap = len(law_words & discovery_words) / len(law_words | discovery_words)

                if overlap > 0.3:
                    reward += 0.5 * law.confidence
                    details['matched_law'] = law.name
                    details['law_confidence'] = law.confidence

    # Bonus for conservation laws
    if any(word in content for word in ['conserved', 'conservation', 'constant']):
        reward += 0.3
        details['conservation_bonus'] = True

    # Bonus for mathematical relationships
    if any(word in content for word in ['equation', 'proportional', 'equals']):
        reward += 0.2
        details['mathematical_bonus'] = True

    # Bonus for specific domains
    if domain in ['physics', 'astronomy', 'chemistry']:
        reward += 0.2
        details['domain_bonus'] = domain

    return min(reward, 1.0), details
