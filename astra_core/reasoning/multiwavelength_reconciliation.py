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
Multiwavelength Reconciliation for STAN V43

Integrate information across wavelength domains (X-ray, optical, IR, radio)
to build consistent physical models. Detects tensions between domains
and suggests missing physics.

Author: STAN V43 Reasoning Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np


class WavelengthDomain(Enum):
    """Electromagnetic wavelength domains."""
    GAMMA_RAY = auto()      # < 0.01 nm
    XRAY_HARD = auto()      # 0.01-0.1 nm (10-100 keV)
    XRAY_SOFT = auto()      # 0.1-10 nm (0.1-10 keV)
    EUV = auto()            # 10-100 nm
    UV = auto()             # 100-400 nm
    OPTICAL = auto()        # 400-700 nm
    NIR = auto()            # 0.7-5 micron
    MIR = auto()            # 5-30 micron
    FIR = auto()            # 30-300 micron
    SUBMM = auto()          # 300-1000 micron
    MM = auto()             # 1-10 mm
    RADIO_CM = auto()       # 1-30 cm
    RADIO_M = auto()        # > 30 cm


class EmissionMechanism(Enum):
    """Physical emission mechanisms."""
    THERMAL_DUST = auto()          # Modified blackbody
    THERMAL_GAS = auto()           # Bremsstrahlung
    SYNCHROTRON = auto()           # Relativistic electrons
    INVERSE_COMPTON = auto()       # CMB upscattering
    LINE_EMISSION = auto()         # Atomic/molecular lines
    RECOMBINATION = auto()         # Free-bound transitions
    FREE_FREE = auto()             # Bremsstrahlung
    STELLAR_PHOTOSPHERE = auto()   # Blackbody-like
    PAH_EMISSION = auto()          # Polycyclic aromatic hydrocarbons
    SCATTERED_LIGHT = auto()       # Reflection nebulae


@dataclass
class Observation:
    """A single-domain observation."""
    domain: WavelengthDomain
    wavelength_um: float           # Central wavelength in microns
    bandwidth_um: float            # Bandwidth
    flux: float                    # Flux in appropriate units
    flux_error: float
    position_ra: float             # degrees
    position_dec: float            # degrees
    angular_resolution: float      # arcsec
    spectral_resolution: Optional[float]  # R = lambda/delta_lambda
    observation_date: str
    instrument: str
    likely_mechanism: Optional[EmissionMechanism] = None


@dataclass
class PhysicalComponent:
    """A physical component in the model."""
    name: str
    temperature: Optional[float]       # K
    column_density: Optional[float]    # cm^-2
    mass: Optional[float]              # M_sun
    luminosity: Optional[float]        # L_sun
    velocity: Optional[float]          # km/s
    magnetic_field: Optional[float]    # G
    size: Optional[float]              # pc
    parameters: Dict[str, float] = field(default_factory=dict)


@dataclass
class DomainBelief:
    """Belief about physical state from one domain."""
    domain: WavelengthDomain
    components: List[PhysicalComponent]
    confidence: float
    constraints: Dict[str, Tuple[float, float]]  # param -> (min, max)
    tensions_with: List[str]  # Other domains this conflicts with


@dataclass
class Tension:
    """A tension between wavelength domains."""
    description: str
    domain_a: WavelengthDomain
    domain_b: WavelengthDomain
    parameter: str
    value_a: float
    value_b: float
    discrepancy_sigma: float
    possible_resolutions: List[str]


@dataclass
class UnifiedModel:
    """A model consistent across all wavelength domains."""
    components: List[PhysicalComponent]
    domain_contributions: Dict[WavelengthDomain, List[str]]  # domain -> component names
    sed: Dict[float, float]  # wavelength_um -> flux
    total_luminosity: float
    chi_squared: float
    degrees_of_freedom: int
    tensions_resolved: List[str]
    remaining_tensions: List[Tension]


class MultiWavelengthBelief:
    """
    Belief state decomposed by observational domain.

    Tracks what each wavelength domain tells us and
    identifies tensions between them.
    """

    def __init__(self):
        """Initialize belief tracker."""
        self.domain_beliefs: Dict[WavelengthDomain, DomainBelief] = {}
        self.tensions: List[Tension] = []

    def add_domain_belief(
        self,
        domain: WavelengthDomain,
        components: List[PhysicalComponent],
        confidence: float = 0.5
    ):
        """Add belief from one wavelength domain."""
        constraints = {}
        for comp in components:
            if comp.temperature is not None:
                constraints[f'{comp.name}_T'] = (
                    comp.temperature * 0.8,
                    comp.temperature * 1.2
                )
            if comp.mass is not None:
                constraints[f'{comp.name}_M'] = (
                    comp.mass * 0.5,
                    comp.mass * 2.0
                )

        self.domain_beliefs[domain] = DomainBelief(
            domain=domain,
            components=components,
            confidence=confidence,
            constraints=constraints,
            tensions_with=[]
        )

    def check_tensions(self) -> List[Tension]:
        """Check for tensions between domains."""
        self.tensions = []

        domains = list(self.domain_beliefs.keys())

        for i, domain_a in enumerate(domains):
            for domain_b in domains[i+1:]:
                belief_a = self.domain_beliefs[domain_a]
                belief_b = self.domain_beliefs[domain_b]

                # Check overlapping constraints
                for param, (min_a, max_a) in belief_a.constraints.items():
                    if param in belief_b.constraints:
                        min_b, max_b = belief_b.constraints[param]

                        # Check for non-overlap
                        if max_a < min_b or max_b < min_a:
                            mid_a = (min_a + max_a) / 2
                            mid_b = (min_b + max_b) / 2
                            sigma = max(max_a - min_a, max_b - min_b) / 4

                            tension = Tension(
                                description=f'{param} disagrees between {domain_a.name} and {domain_b.name}',
                                domain_a=domain_a,
                                domain_b=domain_b,
                                parameter=param,
                                value_a=mid_a,
                                value_b=mid_b,
                                discrepancy_sigma=abs(mid_a - mid_b) / sigma if sigma > 0 else 0,
                                possible_resolutions=['calibration_error', 'missing_component', 'wrong_model']
                            )
                            self.tensions.append(tension)

                            belief_a.tensions_with.append(domain_b.name)
                            belief_b.tensions_with.append(domain_a.name)

        return self.tensions

    def get_consensus_constraints(self) -> Dict[str, Tuple[float, float]]:
        """Get constraints that all domains agree on."""
        all_params = set()
        for belief in self.domain_beliefs.values():
            all_params.update(belief.constraints.keys())

        consensus = {}

        for param in all_params:
            mins = []
            maxs = []

            for belief in self.domain_beliefs.values():
                if param in belief.constraints:
                    min_v, max_v = belief.constraints[param]
                    mins.append(min_v)
                    maxs.append(max_v)

            if mins and maxs:
                # Intersection of all constraints
                overall_min = max(mins)
                overall_max = min(maxs)

                if overall_min <= overall_max:
                    consensus[param] = (overall_min, overall_max)

        return consensus


class DomainReconciler:
    """
    Find consistent physical model across wavelength domains.

    Uses optimization to find model that fits all domains.
    """

    # Expected emission by domain and mechanism
    DOMAIN_MECHANISMS = {
        WavelengthDomain.XRAY_SOFT: [EmissionMechanism.THERMAL_GAS, EmissionMechanism.INVERSE_COMPTON],
        WavelengthDomain.UV: [EmissionMechanism.STELLAR_PHOTOSPHERE, EmissionMechanism.LINE_EMISSION],
        WavelengthDomain.OPTICAL: [EmissionMechanism.STELLAR_PHOTOSPHERE, EmissionMechanism.LINE_EMISSION, EmissionMechanism.SCATTERED_LIGHT],
        WavelengthDomain.NIR: [EmissionMechanism.STELLAR_PHOTOSPHERE, EmissionMechanism.THERMAL_DUST],
        WavelengthDomain.MIR: [EmissionMechanism.PAH_EMISSION, EmissionMechanism.THERMAL_DUST],
        WavelengthDomain.FIR: [EmissionMechanism.THERMAL_DUST],
        WavelengthDomain.SUBMM: [EmissionMechanism.THERMAL_DUST],
        WavelengthDomain.MM: [EmissionMechanism.THERMAL_DUST, EmissionMechanism.FREE_FREE],
        WavelengthDomain.RADIO_CM: [EmissionMechanism.FREE_FREE, EmissionMechanism.SYNCHROTRON],
    }

    def __init__(self):
        """Initialize reconciler."""
        pass

    def reconcile(
        self,
        observations: Dict[WavelengthDomain, List[Observation]],
        initial_guess: Optional[List[PhysicalComponent]] = None
    ) -> UnifiedModel:
        """
        Find unified model consistent with all observations.

        Parameters
        ----------
        observations : dict
            Domain -> list of observations
        initial_guess : list, optional
            Initial component guess

        Returns
        -------
        UnifiedModel
        """
        # Start with initial components or guess
        if initial_guess is None:
            components = self._guess_components(observations)
        else:
            components = initial_guess

        # Build SED from components
        sed = self._build_sed(components)

        # Calculate chi-squared per domain
        total_chi2 = 0.0
        total_dof = 0
        domain_contributions = {}

        for domain, obs_list in observations.items():
            domain_contributions[domain] = []
            for obs in obs_list:
                model_flux = self._interpolate_sed(sed, obs.wavelength_um)
                if obs.flux_error > 0:
                    chi2 = ((obs.flux - model_flux) / obs.flux_error)**2
                    total_chi2 += chi2
                    total_dof += 1

                # Find which component dominates
                for comp in components:
                    if self._component_contributes(comp, obs.wavelength_um):
                        if comp.name not in domain_contributions[domain]:
                            domain_contributions[domain].append(comp.name)

        # Calculate total luminosity
        total_lum = sum(c.luminosity for c in components if c.luminosity)

        return UnifiedModel(
            components=components,
            domain_contributions=domain_contributions,
            sed=sed,
            total_luminosity=total_lum,
            chi_squared=total_chi2,
            degrees_of_freedom=max(1, total_dof - len(components) * 3),
            tensions_resolved=[],
            remaining_tensions=[]
        )

    def _guess_components(
        self,
        observations: Dict[WavelengthDomain, List[Observation]]
    ) -> List[PhysicalComponent]:
        """Guess initial components from observations."""
        components = []

        # Check for cold dust (FIR/submm)
        if WavelengthDomain.FIR in observations or WavelengthDomain.SUBMM in observations:
            components.append(PhysicalComponent(
                name='cold_dust',
                temperature=20.0,
                column_density=1e22,
                mass=100.0,
                luminosity=1e4,
                velocity=None,
                magnetic_field=None,
                size=1.0
            ))

        # Check for warm dust (MIR)
        if WavelengthDomain.MIR in observations:
            components.append(PhysicalComponent(
                name='warm_dust',
                temperature=100.0,
                column_density=1e21,
                mass=1.0,
                luminosity=1e3,
                velocity=None,
                magnetic_field=None,
                size=0.1
            ))

        # Check for stellar contribution (optical/NIR)
        if WavelengthDomain.OPTICAL in observations or WavelengthDomain.NIR in observations:
            components.append(PhysicalComponent(
                name='stellar',
                temperature=5000.0,
                column_density=None,
                mass=1.0,
                luminosity=1.0,
                velocity=None,
                magnetic_field=None,
                size=None
            ))

        # Check for ionized gas (radio/X-ray)
        if WavelengthDomain.RADIO_CM in observations or WavelengthDomain.XRAY_SOFT in observations:
            components.append(PhysicalComponent(
                name='ionized_gas',
                temperature=1e4,
                column_density=1e20,
                mass=10.0,
                luminosity=100.0,
                velocity=10.0,
                magnetic_field=None,
                size=0.5
            ))

        # Default if nothing found
        if not components:
            components.append(PhysicalComponent(
                name='generic',
                temperature=100.0,
                column_density=1e21,
                mass=10.0,
                luminosity=100.0,
                velocity=None,
                magnetic_field=None,
                size=1.0
            ))

        return components

    def _build_sed(
        self,
        components: List[PhysicalComponent]
    ) -> Dict[float, float]:
        """Build SED from components."""
        # Wavelength grid in microns
        wavelengths = np.logspace(-2, 4, 100)  # 0.01 to 10000 micron

        sed = {}
        for wav in wavelengths:
            total_flux = 0.0
            for comp in components:
                flux = self._component_flux(comp, wav)
                total_flux += flux
            sed[wav] = total_flux

        return sed

    def _component_flux(
        self,
        component: PhysicalComponent,
        wavelength_um: float
    ) -> float:
        """Calculate flux from component at wavelength."""
        if component.temperature is None:
            return 0.0

        # Planck function (simplified)
        h = 6.626e-27  # erg s
        c = 3e10       # cm/s
        k = 1.381e-16  # erg/K

        wav_cm = wavelength_um * 1e-4
        nu = c / wav_cm

        T = component.temperature

        # B_nu in cgs
        x = h * nu / (k * T)
        if x > 700:
            return 0.0
        elif x < 1e-3:
            B_nu = 2 * k * T * nu**2 / c**2
        else:
            B_nu = 2 * h * nu**3 / c**2 / (np.exp(x) - 1)

        # Scale by luminosity if available
        if component.luminosity:
            scale = component.luminosity * 3.828e33  # erg/s
            B_nu *= scale / 1e40  # Arbitrary normalization

        return B_nu

    def _interpolate_sed(self, sed: Dict[float, float], wavelength: float) -> float:
        """Interpolate SED at wavelength."""
        wavs = np.array(sorted(sed.keys()))
        fluxes = np.array([sed[w] for w in sorted(sed.keys())])

        if wavelength < wavs[0]:
            return fluxes[0]
        if wavelength > wavs[-1]:
            return fluxes[-1]

        return np.interp(wavelength, wavs, fluxes)

    def _component_contributes(
        self,
        component: PhysicalComponent,
        wavelength_um: float
    ) -> bool:
        """Check if component contributes at wavelength."""
        if component.temperature is None:
            return False

        # Wien peak wavelength
        peak_um = 2898.0 / component.temperature  # Wien's law

        # Component contributes within ~2 orders of magnitude of peak
        return 0.01 * peak_um < wavelength_um < 100 * peak_um


class TensionDetector:
    """
    Detect contradictions between wavelength domain inferences.

    Identifies when different domains imply inconsistent physics.
    """

    # Known physical constraints
    PHYSICAL_CONSTRAINTS = {
        'dust_temperature': {
            'min': 2.7,    # CMB floor
            'max': 2000,   # Sublimation
            'related': ['luminosity', 'distance']
        },
        'gas_temperature': {
            'min': 10,     # Molecular cloud floor
            'max': 1e8,    # Relativistic limit
            'related': ['density', 'cooling_time']
        },
        'column_density': {
            'min': 1e18,   # Detectability
            'max': 1e26,   # Optical depth limit
            'related': ['mass', 'size']
        }
    }

    def __init__(self):
        """Initialize detector."""
        pass

    def detect_tensions(
        self,
        model: UnifiedModel,
        observations: Dict[WavelengthDomain, List[Observation]]
    ) -> List[Tension]:
        """
        Detect tensions in unified model.

        Parameters
        ----------
        model : UnifiedModel
            The current unified model
        observations : dict
            Original observations by domain

        Returns
        -------
        List of tensions found
        """
        tensions = []

        # Check temperature consistency
        for comp in model.components:
            if comp.temperature is not None:
                constraints = self.PHYSICAL_CONSTRAINTS.get('dust_temperature', {})
                if comp.temperature < constraints.get('min', 0):
                    tensions.append(Tension(
                        description=f'{comp.name} temperature below CMB',
                        domain_a=WavelengthDomain.FIR,
                        domain_b=WavelengthDomain.SUBMM,
                        parameter='temperature',
                        value_a=comp.temperature,
                        value_b=2.7,
                        discrepancy_sigma=10.0,
                        possible_resolutions=['calibration_error', 'wrong_redshift']
                    ))

        # Check flux ratio tensions
        for domain_a, obs_a_list in observations.items():
            for domain_b, obs_b_list in observations.items():
                if domain_a.value >= domain_b.value:
                    continue

                for obs_a in obs_a_list:
                    for obs_b in obs_b_list:
                        # Check if flux ratio is physically reasonable
                        if obs_a.flux > 0 and obs_b.flux > 0:
                            ratio = obs_a.flux / obs_b.flux
                            expected = self._expected_ratio(
                                model, obs_a.wavelength_um, obs_b.wavelength_um
                            )

                            if expected > 0:
                                discrepancy = abs(np.log10(ratio / expected))
                                if discrepancy > 1.0:  # Order of magnitude
                                    tensions.append(Tension(
                                        description=f'Flux ratio {domain_a.name}/{domain_b.name} unexpected',
                                        domain_a=domain_a,
                                        domain_b=domain_b,
                                        parameter='flux_ratio',
                                        value_a=ratio,
                                        value_b=expected,
                                        discrepancy_sigma=discrepancy,
                                        possible_resolutions=['missing_component', 'extinction', 'variability']
                                    ))

        return tensions

    def _expected_ratio(
        self,
        model: UnifiedModel,
        wav_a: float,
        wav_b: float
    ) -> float:
        """Calculate expected flux ratio from model."""
        flux_a = 0.0
        flux_b = 0.0

        for wav, flux in model.sed.items():
            if abs(wav - wav_a) < 0.1 * wav_a:
                flux_a = flux
            if abs(wav - wav_b) < 0.1 * wav_b:
                flux_b = flux

        if flux_b > 0:
            return flux_a / flux_b
        return 0.0


class SEDIntegrator:
    """
    Build unified SED from heterogeneous photometry.

    Handles different apertures, calibrations, and epochs.
    """

    def __init__(self):
        """Initialize integrator."""
        pass

    def integrate_photometry(
        self,
        observations: List[Observation],
        aperture_correction: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Integrate observations into unified SED.

        Returns (wavelengths, fluxes, errors).
        """
        # Sort by wavelength
        sorted_obs = sorted(observations, key=lambda o: o.wavelength_um)

        wavelengths = []
        fluxes = []
        errors = []

        # Group by wavelength (within 10%)
        groups = []
        current_group = [sorted_obs[0]] if sorted_obs else []

        for obs in sorted_obs[1:]:
            if current_group:
                ref_wav = current_group[0].wavelength_um
                if abs(obs.wavelength_um - ref_wav) / ref_wav < 0.1:
                    current_group.append(obs)
                else:
                    groups.append(current_group)
                    current_group = [obs]
            else:
                current_group = [obs]

        if current_group:
            groups.append(current_group)

        # Average each group
        for group in groups:
            wav = np.mean([o.wavelength_um for o in group])
            flux_vals = [o.flux for o in group]
            err_vals = [o.flux_error for o in group]

            # Weighted average
            weights = [1/e**2 if e > 0 else 1 for e in err_vals]
            avg_flux = np.average(flux_vals, weights=weights)
            avg_err = 1 / np.sqrt(sum(weights)) if sum(weights) > 0 else np.mean(err_vals)

            wavelengths.append(wav)
            fluxes.append(avg_flux)
            errors.append(avg_err)

        return np.array(wavelengths), np.array(fluxes), np.array(errors)

    def fit_modified_blackbody(
        self,
        wavelengths: np.ndarray,
        fluxes: np.ndarray,
        errors: np.ndarray
    ) -> Dict[str, float]:
        """
        Fit modified blackbody to FIR/submm SED.

        Returns {T_dust, beta, M_dust, chi2}.
        """
        # Filter to FIR/submm range (30-3000 micron)
        mask = (wavelengths > 30) & (wavelengths < 3000)

        if np.sum(mask) < 3:
            return {'T_dust': 20.0, 'beta': 2.0, 'M_dust': 1.0, 'chi2': -1}

        wav_fit = wavelengths[mask]
        flux_fit = fluxes[mask]
        err_fit = errors[mask]

        # Grid search for T and beta
        best_chi2 = float('inf')
        best_params = {'T_dust': 20.0, 'beta': 2.0}

        for T in np.linspace(10, 60, 20):
            for beta in np.linspace(1.0, 2.5, 10):
                model = self._modified_blackbody(wav_fit, T, beta)

                # Scale to match data
                scale = np.sum(flux_fit * model / err_fit**2) / np.sum(model**2 / err_fit**2)
                model_scaled = model * scale

                chi2 = np.sum(((flux_fit - model_scaled) / err_fit)**2)

                if chi2 < best_chi2:
                    best_chi2 = chi2
                    best_params = {'T_dust': T, 'beta': beta, 'scale': scale}

        best_params['chi2'] = best_chi2
        best_params['M_dust'] = best_params.get('scale', 1.0) * 100  # Rough mass estimate

        return best_params

    def _modified_blackbody(
        self,
        wavelength_um: np.ndarray,
        T: float,
        beta: float
    ) -> np.ndarray:
        """Calculate modified blackbody."""
        h = 6.626e-27
        c = 3e10
        k = 1.381e-16

        wav_cm = wavelength_um * 1e-4
        nu = c / wav_cm

        x = h * nu / (k * T)
        x = np.clip(x, 1e-10, 700)

        B_nu = 2 * h * nu**3 / c**2 / (np.exp(x) - 1)

        # Dust opacity ~ nu^beta
        kappa = (nu / 1e12)**beta

        return B_nu * kappa


class PhysicalStateInferrer:
    """
    Infer complete physical state from partial observations.

    Uses domain knowledge to fill in unobserved parameters.
    """

    # Scaling relations for inference
    SCALING_RELATIONS = {
        'mass_luminosity': {
            'equation': 'L ~ M^3.5',
            'applies_to': 'main_sequence_stars',
            'scatter': 0.2
        },
        'mass_temperature': {
            'equation': 'T ~ M^0.5',
            'applies_to': 'dust_clouds',
            'scatter': 0.3
        },
        'size_velocity': {
            'equation': 'sigma ~ R^0.5',
            'applies_to': 'molecular_clouds',
            'scatter': 0.2
        },
        'luminosity_temperature_radius': {
            'equation': 'L ~ T^4 * R^2',
            'applies_to': 'thermal_sources',
            'scatter': 0.1
        }
    }

    def __init__(self):
        """Initialize inferrer."""
        pass

    def infer_complete_state(
        self,
        partial_component: PhysicalComponent
    ) -> PhysicalComponent:
        """
        Infer missing parameters from known ones.

        Uses scaling relations and physical constraints.
        """
        inferred = PhysicalComponent(
            name=partial_component.name + '_inferred',
            temperature=partial_component.temperature,
            column_density=partial_component.column_density,
            mass=partial_component.mass,
            luminosity=partial_component.luminosity,
            velocity=partial_component.velocity,
            magnetic_field=partial_component.magnetic_field,
            size=partial_component.size
        )

        # Infer luminosity from temperature and size
        if inferred.luminosity is None and inferred.temperature and inferred.size:
            # Stefan-Boltzmann: L = 4*pi*R^2 * sigma * T^4
            sigma_sb = 5.67e-5  # erg/cm^2/s/K^4
            R_cm = inferred.size * 3.086e18  # pc to cm
            L_erg = 4 * np.pi * R_cm**2 * sigma_sb * inferred.temperature**4
            inferred.luminosity = L_erg / 3.828e33  # to L_sun

        # Infer size from luminosity and temperature
        if inferred.size is None and inferred.luminosity and inferred.temperature:
            sigma_sb = 5.67e-5
            L_erg = inferred.luminosity * 3.828e33
            R_cm = np.sqrt(L_erg / (4 * np.pi * sigma_sb * inferred.temperature**4))
            inferred.size = R_cm / 3.086e18  # to pc

        # Infer mass from size and velocity dispersion (virial)
        if inferred.mass is None and inferred.size and inferred.velocity:
            G = 6.674e-8
            R_cm = inferred.size * 3.086e18
            v_cm = inferred.velocity * 1e5  # km/s to cm/s
            M_g = v_cm**2 * R_cm / G
            inferred.mass = M_g / 1.989e33  # to M_sun

        # Infer velocity dispersion from mass and size
        if inferred.velocity is None and inferred.mass and inferred.size:
            G = 6.674e-8
            M_g = inferred.mass * 1.989e33
            R_cm = inferred.size * 3.086e18
            v_cm = np.sqrt(G * M_g / R_cm)
            inferred.velocity = v_cm / 1e5  # to km/s

        return inferred

    def check_physical_consistency(
        self,
        component: PhysicalComponent
    ) -> List[str]:
        """
        Check if inferred state is physically consistent.

        Returns list of warnings.
        """
        warnings = []

        # Temperature checks
        if component.temperature is not None:
            if component.temperature < 2.7:
                warnings.append('Temperature below CMB')
            if component.temperature > 1e8:
                warnings.append('Temperature exceeds typical ISM')

        # Mass-size consistency
        if component.mass and component.size:
            # Average density
            R_cm = component.size * 3.086e18
            M_g = component.mass * 1.989e33
            rho = M_g / (4/3 * np.pi * R_cm**3)
            n_H = rho / 1.67e-24  # cm^-3

            if n_H < 1e-3:
                warnings.append('Density below typical ISM')
            if n_H > 1e10:
                warnings.append('Density exceeds stellar interior')

        # Luminosity-mass check
        if component.luminosity and component.mass:
            L_M = component.luminosity / component.mass
            if L_M > 1e5:
                warnings.append('Luminosity/mass exceeds Eddington')

        return warnings


# Convenience functions

def reconcile_observations(
    observations: Dict[WavelengthDomain, List[Observation]]
) -> UnifiedModel:
    """
    Convenience function to reconcile multi-wavelength observations.
    """
    reconciler = DomainReconciler()
    return reconciler.reconcile(observations)


def detect_wavelength_tensions(
    observations: Dict[WavelengthDomain, List[Observation]]
) -> List[Tension]:
    """
    Detect tensions in multi-wavelength data.
    """
    reconciler = DomainReconciler()
    model = reconciler.reconcile(observations)

    detector = TensionDetector()
    return detector.detect_tensions(model, observations)


def build_sed_from_observations(
    observations: List[Observation]
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build unified SED from observations.
    """
    integrator = SEDIntegrator()
    return integrator.integrate_photometry(observations)


def infer_physical_state(
    partial_component: PhysicalComponent
) -> PhysicalComponent:
    """
    Infer complete physical state from partial observations.
    """
    inferrer = PhysicalStateInferrer()
    return inferrer.infer_complete_state(partial_component)


def get_domain_reconciler() -> DomainReconciler:
    """Get singleton-like reconciler instance."""
    return DomainReconciler()
