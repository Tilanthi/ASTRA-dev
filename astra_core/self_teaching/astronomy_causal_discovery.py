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
Astronomy-Enhanced Causal Discovery for STAR-Learn V3.0

This module extends causal discovery for astronomical applications:
1. Radiative transfer causal models
2. Gas dynamics causal relationships
3. Time-series causal discovery for astronomical observations
4. Filament formation causal chains
5. Multi-wavelength causal inference

This is specialized for:
- Radio astronomy
- mm-wave astronomy
- sub-mm astronomy
- Infrared astronomy

Key astrophysics domains:
- Filament formation and physics
- Gas dynamics
- Interstellar chemistry
- Radiative transfer
- Stellar physics
- HII regions
- Star and planetary formation

Version: 3.0.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import itertools


class AstronomicalDomain(Enum):
    """Astronomical observation domains"""
    RADIO = "radio"  # ~GHz frequencies
    MM_WAVE = "mm_wave"  # ~30-300 GHz
    SUB_MM = "sub_mm"  # ~300-3000 GHz
    INFRARED = "infrared"  # ~1-300 THz
    OPTICAL = "optical"  # Visible light
    UV = "ultraviolet"
    XRAY = "xray"
    GAMMA = "gamma"


class AstrophysicsProcess(Enum):
    """Key astrophysical processes"""
    FILAMENT_FORMATION = "filament_formation"
    GAS_DYNAMICS = "gas_dynamics"
    INTERSTELLAR_CHEMISTRY = "interstellar_chemistry"
    SPH_SIMULATION = "sph_simulation"
    RADIATIVE_TRANSFER = "radiative_transfer"
    GRAIN_PHYSICS = "interstellar_grains"
    STELLAR_EVOLUTION = "stellar_evolution"
    HII_REGION = "hii_region"
    STAR_FORMATION = "star_formation"
    PLANETARY_FORMATION = "planetary_formation"


@dataclass
class AstronomicalObservation:
    """An astronomical observation dataset"""
    domain: AstronomicalDomain
    wavelength_range: Tuple[float, float]  # (min, max) in meters
    angular_resolution: float  # arcseconds
    spectral_resolution: float
    temporal_coverage: str  # time range
    coordinates: Dict[str, float]  # RA, Dec
    data: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_name: str = ""
    observation_type: str = ""


@dataclass
class CausalModel:
    """A causal model for an astrophysical process"""
    process: AstrophysicsProcess
    variables: List[str]
    causal_structure: Dict[str, List[str]]  # parent -> children
    parameters: Dict[str, float]
    confidence: float = 0.5
    domain_knowledge: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RadiativeTransferModel(CausalModel):
    """Causal model for radiative transfer"""
    temperature_field: np.ndarray = field(default_factory=lambda: np.array([]))  # K
    density_field: np.ndarray = field(default_factory=lambda: np.array([]))  # particles/m^3
    opacity_field: np.ndarray = field(default_factory=lambda: np.array([]))  # absorption coefficient
    velocity_field: np.ndarray = field(default_factory=lambda: np.array([]))  # m/s
    radiation_field: np.ndarray = field(default_factory=lambda: np.array([]))  # intensity
    emissivity: float = 1.0
    scattering_phase_function: str = "isotropic"


# =============================================================================
# Gas Dynamics Causal Discovery
# =============================================================================
class GasDynamicsCausalDiscovery:
    """
    Discover causal relationships in gas dynamics.

    Key causal relationships:
    - Pressure → Velocity (acceleration)
    - Density → Pressure (equation of state)
    - Temperature → Pressure (ideal gas law)
    - Gravity → Density collapse (Jeans instability)
    - Magnetic fields → Gas motion (Lorentz force)
    """

    def __init__(self):
        """Initialize gas dynamics causal discovery."""
        self.gas_laws = {
            'ideal_gas_law': ['pressure', 'density', 'temperature'],
            'jeans_instability': ['density', 'gravity', 'collapse'],
            'shock_waves': ['velocity', 'pressure_jump', 'density_jump'],
            'magnetic_pressure': ['magnetic_field', 'gas_pressure']
        }

    def discover_gas_dynamics_causality(
        self,
        simulation_data: np.ndarray,
        variables: List[str]
    ) -> CausalModel:
        """
        Discover causal relationships in gas dynamics simulation.

        Args:
            simulation_data: SPH or grid simulation data
            variables: ['density', 'pressure', 'velocity', 'temperature', 'magnetic_field']

        Returns:
            Causal model for gas dynamics
        """
        # Calculate correlation-based causal structure
        n_vars = len(variables)
        causal_structure = {}

        for i, var in enumerate(variables):
            # Find causes (variables that influence this one)
            causes = []
            for j, other_var in enumerate(variables):
                if i != j:
                    correlation = np.corrcoef(simulation_data[:, j], simulation_data[:, i])[0, 1]
                    if abs(correlation) > 0.3:  # Threshold
                        causes.append(variables[j])

            causal_structure[var] = causes

        # Add domain knowledge
        if 'density' in variables and 'temperature' in variables:
            causal_structure['pressure'] = ['density', 'temperature']

        if 'density' in variables and 'velocity' in variables:
            # Bernoulli's principle
            causal_structure['pressure'].append('velocity')

        model = CausalModel(
            process=AstrophysicsProcess.GAS_DYNAMICS,
            variables=variables,
            causal_structure=causal_structure,
            parameters=self._estimate_gas_dynamics_parameters(simulation_data, variables),
            confidence=0.75
        )

        return model

    def _estimate_gas_dynamics_parameters(
        self,
        data: np.ndarray,
        variables: List[str]
    ) -> Dict[str, float]:
        """Estimate parameters for gas dynamics model."""
        # Simplified parameter estimation
        params = {}

        if 'density' in variables:
            idx = variables.index('density')
            params['mean_density'] = np.mean(data[:, idx])

        if 'velocity' in variables:
            idx = variables.index('velocity')
            params['mean_velocity'] = np.mean(data[:, idx])

        return params

    def discover_causal_structure(self, data: np.ndarray,
                                   variables: List[str]) -> CausalModel:
        """
        Discover causal structure from observational data.

        Args:
            data: Observational data (n_samples x n_variables)
            variables: List of variable names

        Returns:
            Discovered causal model
        """
        # Try all domain-specific models
        models = []

        for process in AstrophysicsProcess:
            try:
                model = self._discover_for_process(data, variables, process)
                if model:
                    models.append(model)
            except Exception as e:
                continue

        # Select best model by confidence
        if models:
            models.sort(key=lambda m: m.confidence, reverse=True)
            return models[0]

        # Fallback: run PC algorithm
        return self._run_pc_algorithm(data, variables)

    def _run_pc_algorithm(self, data: np.ndarray,
                          variables: List[str]) -> CausalModel:
        """Run PC algorithm as fallback."""
        # Simplified implementation
        causal_structure = {v: [] for v in variables}

        # Compute correlations
        for i, var1 in enumerate(variables):
            for j, var2 in enumerate(variables):
                if i != j:
                    corr = np.corrcoef(data[:, i], data[:, j])[0, 1]
                    if abs(corr) > 0.5:
                        causal_structure[var1].append(var2)

        return CausalModel(
            process=AstrophysicsProcess.UNKNOWN,
            variables=variables,
            causal_structure=causal_structure,
            parameters={},
            confidence=0.5
        )
