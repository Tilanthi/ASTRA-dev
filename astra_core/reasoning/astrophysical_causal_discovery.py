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
Astrophysical Causal Discovery for STAN V43

Physics-aware causal inference that accounts for observational biases,
conservation laws, and domain-specific mechanisms. Extends generic causal
discovery with astrophysical constraints and interpretation.

Author: STAN V43 Reasoning Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np


class ConservationLaw(Enum):
    """Fundamental conservation laws constraining causal relationships."""
    MASS = auto()              # Mass conservation
    ENERGY = auto()            # Energy conservation
    MOMENTUM = auto()          # Linear momentum
    ANGULAR_MOMENTUM = auto()  # Angular momentum
    CHARGE = auto()            # Electric charge
    BARYON_NUMBER = auto()     # Baryon number


class ObservationalBias(Enum):
    """Known observational biases in astronomical data."""
    MALMQUIST = auto()         # Flux-limited samples favor intrinsically bright
    EDDINGTON = auto()         # Noise scatters more objects up than down
    SELECTION = auto()         # Sample selection criteria
    EXTINCTION = auto()        # Dust obscuration
    RESOLUTION = auto()        # Spatial resolution limits
    SENSITIVITY = auto()       # Detection threshold
    COMPLETENESS = auto()      # Catalog incompleteness
    DISTANCE = auto()          # Distance-dependent effects


@dataclass
class CausalEdge:
    """A directed causal relationship between variables."""
    source: str
    target: str
    mechanism: str             # Physical mechanism
    strength: float            # Effect size (0-1)
    confidence: float          # Statistical confidence
    valid_conditions: str      # Conditions where relationship holds
    bidirectional: bool = False  # Feedback loop?
    time_lag: Optional[float] = None  # Characteristic timescale


@dataclass
class LatentVariable:
    """A proposed hidden variable."""
    name: str
    physical_meaning: str
    observed_proxies: List[str]
    indirect_evidence: str
    measurement_difficulty: str
    proposed_by: str           # What analysis suggested it


@dataclass
class CausalGraph:
    """A graph of causal relationships."""
    variables: List[str]
    edges: List[CausalEdge]
    latent_variables: List[LatentVariable]
    biases_accounted: List[ObservationalBias]
    conservation_laws: List[ConservationLaw]
    domain: str
    confidence: float

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'variables': self.variables,
            'edges': [(e.source, e.target, e.mechanism) for e in self.edges],
            'latent': [lv.name for lv in self.latent_variables],
            'biases': [b.name for b in self.biases_accounted],
            'domain': self.domain,
            'confidence': self.confidence
        }


@dataclass
class BiasCorrection:
    """A correction for observational bias."""
    bias_type: ObservationalBias
    affected_variables: List[str]
    correction_method: str
    correction_factor: Optional[float]
    residual_uncertainty: float


class BiasAwareCausalDiscovery:
    """
    Causal discovery accounting for astronomical observational biases.

    Key biases handled:
    - Malmquist bias: Flux-limited samples
    - Eddington bias: Noise asymmetry
    - Selection effects: Sample criteria
    """

    BIAS_SIGNATURES = {
        ObservationalBias.MALMQUIST: {
            'signature': 'correlation_with_distance',
            'affected': ['luminosity', 'flux', 'magnitude'],
            'correction': 'volume_limited_subsample'
        },
        ObservationalBias.EDDINGTON: {
            'signature': 'asymmetric_scatter_near_threshold',
            'affected': ['source_counts', 'number_density'],
            'correction': 'deconvolution_with_errors'
        },
        ObservationalBias.SELECTION: {
            'signature': 'truncation_in_parameter_space',
            'affected': ['any_derived_quantity'],
            'correction': 'survival_analysis'
        },
        ObservationalBias.EXTINCTION: {
            'signature': 'reddening_correlated_with_faintness',
            'affected': ['color', 'flux', 'column_density'],
            'correction': 'extinction_map_correction'
        }
    }

    def __init__(self):
        """Initialize bias-aware discovery."""
        self.identified_biases: List[BiasCorrection] = []

    def detect_malmquist_bias(
        self,
        flux: np.ndarray,
        distance: np.ndarray,
        flux_limit: float
    ) -> Tuple[bool, float]:
        """
        Detect Malmquist bias in a flux-limited sample.

        Returns (bias_present, bias_magnitude).
        """
        # Check for correlation between mean luminosity and distance
        luminosity = flux * distance**2 * 4 * np.pi

        # Bin by distance
        dist_bins = np.percentile(distance, [25, 50, 75])
        mean_lum_per_bin = []

        for i in range(4):
            if i == 0:
                mask = distance < dist_bins[0]
            elif i == 3:
                mask = distance >= dist_bins[2]
            else:
                mask = (distance >= dist_bins[i-1]) & (distance < dist_bins[i])

            if np.sum(mask) > 0:
                mean_lum_per_bin.append(np.mean(luminosity[mask]))

        if len(mean_lum_per_bin) < 2:
            return False, 0.0

        # If mean luminosity increases with distance, Malmquist bias
        trend = np.polyfit(range(len(mean_lum_per_bin)), mean_lum_per_bin, 1)[0]

        bias_present = trend > 0.1 * np.mean(luminosity)
        bias_magnitude = trend / np.mean(luminosity) if bias_present else 0.0

        return bias_present, bias_magnitude

    def detect_eddington_bias(
        self,
        values: np.ndarray,
        errors: np.ndarray,
        threshold: float
    ) -> Tuple[bool, float]:
        """
        Detect Eddington bias near detection threshold.

        Objects with true values below threshold scatter up more than
        objects above scatter down.
        """
        near_threshold = np.abs(values - threshold) < 2 * np.median(errors)

        if np.sum(near_threshold) < 10:
            return False, 0.0

        # Check for asymmetric distribution above threshold
        above = values[near_threshold] > threshold
        n_above = np.sum(above)
        n_below = np.sum(~above)

        # Expect ~50/50 if no bias
        total = n_above + n_below
        expected = total / 2

        asymmetry = (n_above - expected) / expected if expected > 0 else 0.0

        bias_present = asymmetry > 0.2  # >20% excess above threshold

        return bias_present, asymmetry

    def correct_malmquist(
        self,
        data: Dict[str, np.ndarray],
        distance_key: str,
        flux_key: str,
        max_distance: float
    ) -> Dict[str, np.ndarray]:
        """
        Create volume-limited subsample to correct Malmquist bias.
        """
        mask = data[distance_key] <= max_distance

        corrected = {}
        for key, values in data.items():
            corrected[key] = values[mask]

        self.identified_biases.append(BiasCorrection(
            bias_type=ObservationalBias.MALMQUIST,
            affected_variables=[flux_key, f'{flux_key}_derived'],
            correction_method='volume_limited_subsample',
            correction_factor=max_distance,
            residual_uncertainty=0.1
        ))

        return corrected

    def discover_with_bias_correction(
        self,
        data: Dict[str, np.ndarray],
        biases_to_check: List[ObservationalBias]
    ) -> Tuple[Dict[str, np.ndarray], List[BiasCorrection]]:
        """
        Apply bias corrections before causal discovery.
        """
        corrected_data = data.copy()
        corrections = []

        # Check and correct each bias type
        for bias in biases_to_check:
            if bias == ObservationalBias.MALMQUIST:
                if 'distance' in data and 'flux' in data:
                    present, mag = self.detect_malmquist_bias(
                        data['flux'], data['distance'],
                        flux_limit=np.percentile(data['flux'], 10)
                    )
                    if present:
                        max_d = np.percentile(data['distance'], 50)
                        corrected_data = self.correct_malmquist(
                            corrected_data, 'distance', 'flux', max_d
                        )
                        corrections.append(self.identified_biases[-1])

            elif bias == ObservationalBias.EDDINGTON:
                for key in ['flux', 'counts', 'intensity']:
                    if key in data and f'{key}_err' in data:
                        present, _ = self.detect_eddington_bias(
                            data[key], data[f'{key}_err'],
                            threshold=np.percentile(data[key], 20)
                        )
                        if present:
                            corrections.append(BiasCorrection(
                                bias_type=ObservationalBias.EDDINGTON,
                                affected_variables=[key],
                                correction_method='noted_but_not_corrected',
                                correction_factor=None,
                                residual_uncertainty=0.2
                            ))

        return corrected_data, corrections


class PhysicsConstrainedGraph:
    """
    Causal graph that forbids edges violating conservation laws.

    Implements physical constraints:
    - Energy cannot be created
    - Mass is conserved in non-relativistic processes
    - Angular momentum is conserved without external torques
    """

    # Forbidden edge patterns by conservation law
    FORBIDDEN_PATTERNS = {
        ConservationLaw.ENERGY: [
            # Cannot have output energy > input
            ('kinetic_energy', 'gravitational_energy', 'one_way'),
            ('thermal_energy', 'radiation', 'partial'),
        ],
        ConservationLaw.MASS: [
            # Mass cannot increase without source
            ('star_mass', 'disk_mass', 'requires_accretion'),
        ],
        ConservationLaw.ANGULAR_MOMENTUM: [
            # J conservation constrains rotation-orbit coupling
            ('rotation_rate', 'orbit_size', 'requires_torque'),
        ]
    }

    def __init__(self, conservation_laws: List[ConservationLaw]):
        """Initialize with applicable conservation laws."""
        self.laws = conservation_laws
        self.variables: Set[str] = set()
        self.edges: List[CausalEdge] = []
        self.forbidden_edges: List[Tuple[str, str, str]] = []

    def add_variable(self, name: str, category: str = 'observable'):
        """Add a variable to the graph."""
        self.variables.add(name)

    def is_edge_allowed(
        self,
        source: str,
        target: str,
        mechanism: str
    ) -> Tuple[bool, str]:
        """
        Check if edge is allowed by conservation laws.

        Returns (allowed, reason).
        """
        # Check against each conservation law
        for law in self.laws:
            forbidden = self.FORBIDDEN_PATTERNS.get(law, [])
            for pattern in forbidden:
                src_pattern, tgt_pattern, constraint = pattern

                # Check if edge matches forbidden pattern
                if src_pattern in source.lower() and tgt_pattern in target.lower():
                    if constraint == 'one_way':
                        return False, f'Violates {law.name}: {source}→{target} forbidden'
                    elif constraint == 'requires_accretion':
                        if 'accretion' not in mechanism.lower():
                            return False, f'{law.name}: requires accretion mechanism'
                    elif constraint == 'requires_torque':
                        if 'torque' not in mechanism.lower():
                            return False, f'{law.name}: requires external torque'

        return True, 'Allowed'

    def add_edge(
        self,
        source: str,
        target: str,
        mechanism: str,
        strength: float = 0.5,
        confidence: float = 0.5,
        conditions: str = 'general'
    ) -> bool:
        """
        Add edge if it doesn't violate conservation laws.

        Returns True if edge was added.
        """
        allowed, reason = self.is_edge_allowed(source, target, mechanism)

        if not allowed:
            self.forbidden_edges.append((source, target, reason))
            return False

        self.edges.append(CausalEdge(
            source=source,
            target=target,
            mechanism=mechanism,
            strength=strength,
            confidence=confidence,
            valid_conditions=conditions
        ))

        return True

    def get_descendants(self, variable: str) -> Set[str]:
        """Get all variables caused by this one."""
        descendants = set()
        to_visit = [variable]

        while to_visit:
            current = to_visit.pop()
            for edge in self.edges:
                if edge.source == current and edge.target not in descendants:
                    descendants.add(edge.target)
                    to_visit.append(edge.target)

        return descendants

    def get_ancestors(self, variable: str) -> Set[str]:
        """Get all variables that cause this one."""
        ancestors = set()
        to_visit = [variable]

        while to_visit:
            current = to_visit.pop()
            for edge in self.edges:
                if edge.target == current and edge.source not in ancestors:
                    ancestors.add(edge.source)
                    to_visit.append(edge.source)

        return ancestors


class MechanismIdentifier:
    """
    Identify physical mechanisms explaining observed correlations.

    Goes beyond correlation to physical explanation.
    """

    # Database of known mechanisms and their signatures
    MECHANISM_DATABASE = {
        'gravitational_collapse': {
            'variables': ['density', 'velocity_dispersion', 'mass'],
            'signature': 'density_velocity_anticorrelation',
            'timescale': 't_ff',
            'equation': 'M_jeans ~ T^(3/2) * rho^(-1/2)'
        },
        'photoionization': {
            'variables': ['ionization_fraction', 'UV_flux', 'density'],
            'signature': 'ionization_UV_correlation',
            'timescale': 't_recomb',
            'equation': 'x_e ~ sqrt(G/alpha * n_H)'
        },
        'shock_heating': {
            'variables': ['temperature', 'velocity', 'density'],
            'signature': 'temperature_velocity_squared',
            'timescale': 't_shock',
            'equation': 'T ~ mu * m_H * v^2 / k_B'
        },
        'turbulent_support': {
            'variables': ['velocity_dispersion', 'radius', 'density'],
            'signature': 'larson_linewidth_size',
            'timescale': 't_cross',
            'equation': 'sigma ~ R^0.5'
        },
        'magnetic_support': {
            'variables': ['magnetic_field', 'density', 'mass'],
            'signature': 'mass_flux_ratio',
            'timescale': 't_ambipolar',
            'equation': 'M/Phi ~ 1 / (2 * pi * sqrt(G))'
        },
        'radiative_cooling': {
            'variables': ['temperature', 'density', 'luminosity'],
            'signature': 'cooling_function',
            'timescale': 't_cool',
            'equation': 'Lambda ~ n^2 * cooling_coefficient(T)'
        },
        'accretion': {
            'variables': ['mass', 'accretion_rate', 'luminosity'],
            'signature': 'mass_luminosity',
            'timescale': 't_accretion',
            'equation': 'L_acc ~ G * M * Mdot / R'
        },
        'stellar_feedback': {
            'variables': ['mass_outflow_rate', 'stellar_luminosity', 'velocity'],
            'signature': 'momentum_injection',
            'timescale': 't_crossing',
            'equation': 'Mdot_out ~ L / (c * v_out)'
        }
    }

    def __init__(self):
        """Initialize mechanism identifier."""
        pass

    def identify_mechanism(
        self,
        source_var: str,
        target_var: str,
        data: Optional[Dict[str, np.ndarray]] = None
    ) -> List[Tuple[str, float]]:
        """
        Identify physical mechanisms that could explain source→target.

        Returns list of (mechanism_name, confidence).
        """
        candidates = []

        for mech_name, mech_info in self.MECHANISM_DATABASE.items():
            mech_vars = mech_info['variables']

            # Check if both variables are related to this mechanism
            source_match = any(
                sv.lower() in source_var.lower() or source_var.lower() in sv.lower()
                for sv in mech_vars
            )
            target_match = any(
                tv.lower() in target_var.lower() or target_var.lower() in tv.lower()
                for tv in mech_vars
            )

            if source_match and target_match:
                # Base confidence from variable match
                confidence = 0.5

                # Boost if we have data to test signature
                if data is not None:
                    signature = mech_info['signature']
                    if self._test_signature(signature, data, source_var, target_var):
                        confidence = 0.8

                candidates.append((mech_name, confidence))

        # Sort by confidence
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates

    def _test_signature(
        self,
        signature: str,
        data: Dict[str, np.ndarray],
        source: str,
        target: str
    ) -> bool:
        """Test if data shows mechanism signature."""
        if source not in data or target not in data:
            return False

        x = data[source]
        y = data[target]

        # Remove NaN
        valid = ~(np.isnan(x) | np.isnan(y))
        x, y = x[valid], y[valid]

        if len(x) < 10:
            return False

        if signature == 'density_velocity_anticorrelation':
            corr = np.corrcoef(x, y)[0, 1]
            return corr < -0.3

        elif signature == 'temperature_velocity_squared':
            # T ~ v^2
            corr = np.corrcoef(x, y**2 if 'velocity' in source else x**2)[0, 1]
            return corr > 0.5

        elif signature == 'larson_linewidth_size':
            # sigma ~ R^0.5
            log_corr = np.corrcoef(np.log10(x + 1e-10), np.log10(y + 1e-10))[0, 1]
            return log_corr > 0.3

        return False

    def get_mechanism_equation(self, mechanism: str) -> Optional[str]:
        """Get the governing equation for a mechanism."""
        if mechanism in self.MECHANISM_DATABASE:
            return self.MECHANISM_DATABASE[mechanism]['equation']
        return None

    def get_mechanism_timescale(self, mechanism: str) -> Optional[str]:
        """Get characteristic timescale for a mechanism."""
        if mechanism in self.MECHANISM_DATABASE:
            return self.MECHANISM_DATABASE[mechanism]['timescale']
        return None


class LatentPhysicsProposer:
    """
    Propose hidden variables to explain residual correlations.

    When observed variables don't fully explain patterns, suggests
    physically motivated latent variables.
    """

    # Known latent variables in ISM physics
    LATENT_VARIABLE_CANDIDATES = {
        'magnetic_field': {
            'proxies': ['polarization', 'faraday_rotation', 'zeeman'],
            'suggests_when': 'velocity_dispersion_excess',
            'difficulty': 'hard',
            'physics': 'magnetic_pressure_support'
        },
        'cosmic_ray_ionization': {
            'proxies': ['HCO+', 'N2H+', 'DCO+'],
            'suggests_when': 'ionization_fraction_anomaly',
            'difficulty': 'medium',
            'physics': 'chemistry_ionization_source'
        },
        'external_radiation': {
            'proxies': ['PDR_tracers', 'CII', 'OI'],
            'suggests_when': 'temperature_excess',
            'difficulty': 'medium',
            'physics': 'photoelectric_heating'
        },
        'dust_opacity': {
            'proxies': ['reddening', 'extinction', 'NIR_excess'],
            'suggests_when': 'flux_discrepancy',
            'difficulty': 'easy',
            'physics': 'dust_attenuation'
        },
        'turbulent_driving': {
            'proxies': ['velocity_structure_function', 'spectral_slope'],
            'suggests_when': 'linewidth_excess',
            'difficulty': 'hard',
            'physics': 'energy_injection_scale'
        },
        'protostellar_heating': {
            'proxies': ['IR_point_sources', 'outflows', 'temperature_gradient'],
            'suggests_when': 'localized_heating',
            'difficulty': 'medium',
            'physics': 'internal_luminosity_source'
        }
    }

    def __init__(self):
        """Initialize proposer."""
        pass

    def propose_latent_variables(
        self,
        residuals: Dict[str, np.ndarray],
        domain: str,
        observed_vars: List[str]
    ) -> List[LatentVariable]:
        """
        Propose latent variables to explain residuals.

        Parameters
        ----------
        residuals : dict
            Residual patterns not explained by observed variables
        domain : str
            Physical domain (e.g., 'molecular_cloud', 'HII_region')
        observed_vars : list
            Variables already in the model

        Returns
        -------
        List of proposed latent variables
        """
        proposals = []

        for latent_name, latent_info in self.LATENT_VARIABLE_CANDIDATES.items():
            # Skip if proxies already observed
            if any(p in observed_vars for p in latent_info['proxies']):
                continue

            # Check if residuals suggest this latent
            condition = latent_info['suggests_when']

            suggested = self._check_suggestion_condition(
                condition, residuals, observed_vars
            )

            if suggested:
                proposals.append(LatentVariable(
                    name=latent_name,
                    physical_meaning=latent_info['physics'],
                    observed_proxies=latent_info['proxies'],
                    indirect_evidence=condition,
                    measurement_difficulty=latent_info['difficulty'],
                    proposed_by='residual_analysis'
                ))

        return proposals

    def _check_suggestion_condition(
        self,
        condition: str,
        residuals: Dict[str, np.ndarray],
        observed_vars: List[str]
    ) -> bool:
        """Check if residuals suggest a latent variable."""

        if condition == 'velocity_dispersion_excess':
            if 'velocity_dispersion' in residuals:
                # Check for systematic positive residuals
                return np.mean(residuals['velocity_dispersion']) > 0.1

        elif condition == 'ionization_fraction_anomaly':
            if 'ionization_fraction' in residuals:
                # Check for unexpected ionization levels
                return np.std(residuals['ionization_fraction']) > 0.3

        elif condition == 'temperature_excess':
            if 'temperature' in residuals:
                return np.mean(residuals['temperature']) > 5.0  # K

        elif condition == 'flux_discrepancy':
            for key in residuals:
                if 'flux' in key.lower():
                    # Log-space discrepancy
                    return np.std(np.log10(np.abs(residuals[key]) + 1e-10)) > 0.3

        elif condition == 'linewidth_excess':
            if 'linewidth' in residuals or 'sigma_v' in residuals:
                key = 'linewidth' if 'linewidth' in residuals else 'sigma_v'
                return np.mean(residuals[key]) > 0.2  # km/s excess

        elif condition == 'localized_heating':
            if 'temperature' in residuals:
                # Check for spatial structure
                return np.std(residuals['temperature']) > np.mean(residuals['temperature'])

        return False

    def rank_proposals(
        self,
        proposals: List[LatentVariable],
        data_availability: Dict[str, bool]
    ) -> List[Tuple[LatentVariable, float]]:
        """
        Rank latent variable proposals by testability.

        Higher score = more easily testable.
        """
        ranked = []

        difficulty_scores = {'easy': 0.8, 'medium': 0.5, 'hard': 0.2}

        for prop in proposals:
            # Base score from difficulty
            score = difficulty_scores.get(prop.measurement_difficulty, 0.3)

            # Boost if proxies are available
            proxies_available = sum(
                1 for p in prop.observed_proxies
                if data_availability.get(p, False)
            )
            score += 0.1 * proxies_available

            ranked.append((prop, min(score, 1.0)))

        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked


class DynamicalCausalModel:
    """
    Time-varying causal relationships for evolving systems.

    Handles:
    - Time delays between cause and effect
    - Changing causal structure over evolution
    - Feedback loops
    """

    def __init__(self, time_points: np.ndarray):
        """Initialize with time grid."""
        self.times = time_points
        self.time_varying_edges: Dict[str, List[Tuple[float, CausalEdge]]] = {}

    def add_time_varying_edge(
        self,
        source: str,
        target: str,
        mechanism: str,
        strengths: np.ndarray,
        time_lag: float = 0.0
    ):
        """
        Add edge with time-varying strength.

        Parameters
        ----------
        source : str
            Source variable
        target : str
            Target variable
        mechanism : str
            Physical mechanism
        strengths : array
            Causal strength at each time point
        time_lag : float
            Delay between cause and effect
        """
        edge_key = f'{source}->{target}'

        if edge_key not in self.time_varying_edges:
            self.time_varying_edges[edge_key] = []

        for i, t in enumerate(self.times):
            if i < len(strengths):
                edge = CausalEdge(
                    source=source,
                    target=target,
                    mechanism=mechanism,
                    strength=strengths[i],
                    confidence=0.8,
                    valid_conditions='time_varying',
                    time_lag=time_lag
                )
                self.time_varying_edges[edge_key].append((t, edge))

    def get_causal_structure_at_time(self, t: float) -> List[CausalEdge]:
        """Get the causal graph structure at a specific time."""
        edges = []

        for edge_key, time_edges in self.time_varying_edges.items():
            # Find nearest time point
            best_edge = None
            best_dt = float('inf')

            for time_point, edge in time_edges:
                dt = abs(time_point - t)
                if dt < best_dt:
                    best_dt = dt
                    best_edge = edge

            if best_edge is not None and best_edge.strength > 0.1:
                edges.append(best_edge)

        return edges

    def detect_feedback_loops(self) -> List[Tuple[str, str, str]]:
        """Detect feedback loops in the causal structure."""
        loops = []

        # Build adjacency
        edges_by_source = {}
        for edge_key in self.time_varying_edges:
            source, target = edge_key.split('->')
            if source not in edges_by_source:
                edges_by_source[source] = []
            edges_by_source[source].append(target)

        # Find cycles
        for start in edges_by_source:
            visited = set()
            path = [start]

            def dfs(node):
                if node in visited:
                    if node == start and len(path) > 1:
                        loops.append(tuple(path))
                    return

                visited.add(node)

                for next_node in edges_by_source.get(node, []):
                    path.append(next_node)
                    dfs(next_node)
                    path.pop()

            dfs(start)

        return loops

    def estimate_time_lag(
        self,
        cause_data: np.ndarray,
        effect_data: np.ndarray,
        max_lag: int = 10
    ) -> Tuple[int, float]:
        """
        Estimate time lag between cause and effect using cross-correlation.

        Returns (lag_index, correlation).
        """
        if len(cause_data) != len(effect_data):
            return 0, 0.0

        best_lag = 0
        best_corr = 0.0

        for lag in range(-max_lag, max_lag + 1):
            if lag >= 0:
                c = cause_data[:-lag] if lag > 0 else cause_data
                e = effect_data[lag:] if lag > 0 else effect_data
            else:
                c = cause_data[-lag:]
                e = effect_data[:lag]

            if len(c) > 3:
                corr = np.corrcoef(c, e)[0, 1]
                if not np.isnan(corr) and abs(corr) > abs(best_corr):
                    best_corr = corr
                    best_lag = lag

        return best_lag, best_corr


@dataclass
class AstroCausalDiscoveryResult:
    """Result of astrophysical causal discovery."""
    graph: CausalGraph
    bias_corrections: List[BiasCorrection]
    identified_mechanisms: Dict[str, List[Tuple[str, float]]]
    proposed_latents: List[LatentVariable]
    dynamical_model: Optional[DynamicalCausalModel]
    summary: str


class AstrophysicalCausalDiscovery:
    """
    Main class for physics-aware causal discovery.

    Integrates bias correction, conservation constraints,
    mechanism identification, and latent variable proposal.
    """

    def __init__(
        self,
        conservation_laws: Optional[List[ConservationLaw]] = None,
        biases_to_check: Optional[List[ObservationalBias]] = None
    ):
        """Initialize causal discovery system."""
        self.conservation_laws = conservation_laws or [
            ConservationLaw.ENERGY,
            ConservationLaw.MASS
        ]
        self.biases_to_check = biases_to_check or [
            ObservationalBias.MALMQUIST,
            ObservationalBias.EDDINGTON,
            ObservationalBias.SELECTION
        ]

        self.bias_corrector = BiasAwareCausalDiscovery()
        self.mechanism_identifier = MechanismIdentifier()
        self.latent_proposer = LatentPhysicsProposer()

    def discover(
        self,
        data: Dict[str, np.ndarray],
        domain: str,
        time_series: bool = False
    ) -> AstroCausalDiscoveryResult:
        """
        Perform full astrophysical causal discovery.

        Parameters
        ----------
        data : dict
            Variable name -> data array mapping
        domain : str
            Physical domain for context
        time_series : bool
            Whether data is time series

        Returns
        -------
        AstroCausalDiscoveryResult with graph and analysis
        """
        # Step 1: Bias correction
        corrected_data, bias_corrections = self.bias_corrector.discover_with_bias_correction(
            data, self.biases_to_check
        )

        # Step 2: Build physics-constrained graph
        graph = PhysicsConstrainedGraph(self.conservation_laws)

        for var in corrected_data.keys():
            graph.add_variable(var)

        # Step 3: Discover edges via correlation + mechanism matching
        variables = list(corrected_data.keys())
        mechanisms_found = {}

        for i, source in enumerate(variables):
            for target in variables[i+1:]:
                # Compute correlation
                if len(corrected_data[source]) != len(corrected_data[target]):
                    continue

                valid = ~(np.isnan(corrected_data[source]) | np.isnan(corrected_data[target]))
                if np.sum(valid) < 10:
                    continue

                corr = np.corrcoef(
                    corrected_data[source][valid],
                    corrected_data[target][valid]
                )[0, 1]

                if np.isnan(corr) or abs(corr) < 0.3:
                    continue

                # Identify mechanism
                mechs = self.mechanism_identifier.identify_mechanism(
                    source, target, corrected_data
                )

                if mechs:
                    best_mech, conf = mechs[0]

                    # Try to add edge (will be blocked if violates physics)
                    added = graph.add_edge(
                        source, target, best_mech,
                        strength=abs(corr),
                        confidence=conf
                    )

                    if added:
                        mechanisms_found[f'{source}->{target}'] = mechs

        # Step 4: Propose latent variables
        # Simple residual estimation
        residuals = {}
        for var in corrected_data:
            residuals[var] = corrected_data[var] - np.mean(corrected_data[var])

        proposed_latents = self.latent_proposer.propose_latent_variables(
            residuals, domain, variables
        )

        # Step 5: Time-varying analysis if applicable
        dynamical_model = None
        if time_series and 'time' in corrected_data:
            dynamical_model = DynamicalCausalModel(corrected_data['time'])

        # Build final CausalGraph
        final_graph = CausalGraph(
            variables=variables,
            edges=graph.edges,
            latent_variables=proposed_latents,
            biases_accounted=[b.bias_type for b in bias_corrections],
            conservation_laws=self.conservation_laws,
            domain=domain,
            confidence=np.mean([e.confidence for e in graph.edges]) if graph.edges else 0.0
        )

        # Generate summary
        summary = self._generate_summary(
            final_graph, bias_corrections, mechanisms_found, proposed_latents
        )

        return AstroCausalDiscoveryResult(
            graph=final_graph,
            bias_corrections=bias_corrections,
            identified_mechanisms=mechanisms_found,
            proposed_latents=proposed_latents,
            dynamical_model=dynamical_model,
            summary=summary
        )

    def _generate_summary(
        self,
        graph: CausalGraph,
        bias_corrections: List[BiasCorrection],
        mechanisms: Dict,
        latents: List[LatentVariable]
    ) -> str:
        """Generate human-readable summary of discovery results."""
        lines = [f"Causal Discovery Results for {graph.domain}"]
        lines.append("=" * 50)

        # Biases
        if bias_corrections:
            lines.append(f"\nBias corrections applied ({len(bias_corrections)}):")
            for bc in bias_corrections:
                lines.append(f"  - {bc.bias_type.name}: {bc.correction_method}")

        # Edges
        lines.append(f"\nCausal relationships discovered ({len(graph.edges)}):")
        for edge in graph.edges:
            lines.append(f"  - {edge.source} → {edge.target}")
            lines.append(f"    Mechanism: {edge.mechanism} (strength={edge.strength:.2f})")

        # Latent variables
        if latents:
            lines.append(f"\nProposed latent variables ({len(latents)}):")
            for lv in latents:
                lines.append(f"  - {lv.name}: {lv.physical_meaning}")
                lines.append(f"    Evidence: {lv.indirect_evidence}")

        # Conservation laws
        lines.append(f"\nConservation laws enforced: {[l.name for l in graph.conservation_laws]}")

        return '\n'.join(lines)


# Convenience functions

def discover_causal_structure(
    data: Dict[str, np.ndarray],
    domain: str = 'ism'
) -> AstroCausalDiscoveryResult:
    """
    Convenience function for causal discovery.

    Parameters
    ----------
    data : dict
        Variable name -> data array
    domain : str
        Physical domain

    Returns
    -------
    AstroCausalDiscoveryResult
    """
    discoverer = AstrophysicalCausalDiscovery()
    return discoverer.discover(data, domain)


def identify_mechanism_for_correlation(
    source_var: str,
    target_var: str,
    data: Optional[Dict[str, np.ndarray]] = None
) -> List[Tuple[str, float]]:
    """
    Identify physical mechanisms for observed correlation.

    Returns list of (mechanism_name, confidence).
    """
    identifier = MechanismIdentifier()
    return identifier.identify_mechanism(source_var, target_var, data)


def propose_hidden_variables(
    residuals: Dict[str, np.ndarray],
    observed_vars: List[str],
    domain: str = 'molecular_cloud'
) -> List[LatentVariable]:
    """
    Propose latent variables to explain residuals.
    """
    proposer = LatentPhysicsProposer()
    return proposer.propose_latent_variables(residuals, domain, observed_vars)


def get_astrophysical_causal_discovery() -> AstrophysicalCausalDiscovery:
    """Get singleton-like causal discovery instance."""
    return AstrophysicalCausalDiscovery()



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """Detect patterns using autocorrelation analysis."""
    import numpy as np
    if max_lag is None:
        max_lag = len(data) // 4
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]
    return {'autocorrelation': autocorr[:max_lag], 'peaks': []}



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None


