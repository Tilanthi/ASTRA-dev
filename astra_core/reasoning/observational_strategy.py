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
Observational Strategy for STAN V43

Design optimal observations to test hypotheses. Suggests telescope,
instrument, and exposure combinations. Finds discriminating tests
between rival theories.

Author: STAN V43 Reasoning Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np


class TelescopeType(Enum):
    """Major telescope types."""
    RADIO_SINGLE_DISH = auto()
    RADIO_INTERFEROMETER = auto()
    SUBMM_SINGLE_DISH = auto()
    SUBMM_INTERFEROMETER = auto()
    IR_GROUND = auto()
    IR_SPACE = auto()
    OPTICAL_GROUND = auto()
    OPTICAL_SPACE = auto()
    UV_SPACE = auto()
    XRAY = auto()


class ObservationType(Enum):
    """Types of observations."""
    IMAGING = auto()
    SPECTROSCOPY = auto()
    SPECTRAL_CUBE = auto()
    POLARIMETRY = auto()
    TIME_SERIES = auto()
    INTERFEROMETRY = auto()


@dataclass
class Telescope:
    """A telescope facility."""
    name: str
    telescope_type: TelescopeType
    diameter_m: float
    wavelength_range_um: Tuple[float, float]
    angular_resolution_arcsec: float
    spectral_resolution_max: float
    sensitivity_jy: float          # 5-sigma in 1 hour
    field_of_view_arcmin: float
    available_instruments: List[str]
    location: str
    typical_time_pressure: float   # Oversubscription factor


@dataclass
class Instrument:
    """An instrument on a telescope."""
    name: str
    telescope: str
    observation_type: ObservationType
    wavelength_range_um: Tuple[float, float]
    spectral_resolution: float
    spatial_resolution_arcsec: float
    sensitivity_improvement: float  # Over telescope baseline
    field_of_view_arcmin: float
    typical_overhead_minutes: float


@dataclass
class ObservationPlan:
    """A planned observation."""
    target: str
    telescope: str
    instrument: str
    observation_type: ObservationType
    wavelength_um: float
    integration_time_hours: float
    expected_snr: float
    angular_resolution_arcsec: float
    spectral_resolution: Optional[float]
    science_goal: str
    constraints: List[str]
    estimated_success_probability: float


@dataclass
class Hypothesis:
    """A scientific hypothesis to test."""
    name: str
    description: str
    predictions: Dict[str, float]  # observable -> predicted value
    uncertainties: Dict[str, float]
    required_observables: List[str]
    discriminating_observations: List[str]


@dataclass
class CriticalTest:
    """An observation that discriminates between theories."""
    description: str
    observable: str
    theory_a_prediction: float
    theory_b_prediction: float
    required_precision: float
    recommended_facility: str
    estimated_time_hours: float
    discriminating_power: float  # How well it distinguishes theories


# Database of major facilities
TELESCOPE_DATABASE = {
    'ALMA': Telescope(
        name='ALMA',
        telescope_type=TelescopeType.SUBMM_INTERFEROMETER,
        diameter_m=12.0,  # Individual antenna
        wavelength_range_um=(300, 10000),
        angular_resolution_arcsec=0.01,  # Best case
        spectral_resolution_max=1e7,
        sensitivity_jy=0.1,
        field_of_view_arcmin=0.3,
        available_instruments=['Band_3', 'Band_6', 'Band_7', 'Band_9'],
        location='Chile',
        typical_time_pressure=5.0
    ),
    'VLA': Telescope(
        name='VLA',
        telescope_type=TelescopeType.RADIO_INTERFEROMETER,
        diameter_m=25.0,
        wavelength_range_um=(7000, 400000),
        angular_resolution_arcsec=0.04,
        spectral_resolution_max=1e6,
        sensitivity_jy=0.01,
        field_of_view_arcmin=30.0,
        available_instruments=['L_band', 'C_band', 'X_band', 'K_band', 'Q_band'],
        location='New Mexico',
        typical_time_pressure=3.0
    ),
    'JWST': Telescope(
        name='JWST',
        telescope_type=TelescopeType.IR_SPACE,
        diameter_m=6.5,
        wavelength_range_um=(0.6, 28.5),
        angular_resolution_arcsec=0.1,
        spectral_resolution_max=3000,
        sensitivity_jy=1e-6,
        field_of_view_arcmin=2.2,
        available_instruments=['NIRCam', 'NIRSpec', 'MIRI'],
        location='L2',
        typical_time_pressure=8.0
    ),
    'Chandra': Telescope(
        name='Chandra',
        telescope_type=TelescopeType.XRAY,
        diameter_m=1.2,
        wavelength_range_um=(1e-4, 1e-3),  # 0.1-10 keV
        angular_resolution_arcsec=0.5,
        spectral_resolution_max=1000,
        sensitivity_jy=1e-9,
        field_of_view_arcmin=8.0,
        available_instruments=['ACIS', 'HRC', 'HETG'],
        location='Earth orbit',
        typical_time_pressure=4.0
    ),
    'GBT': Telescope(
        name='GBT',
        telescope_type=TelescopeType.RADIO_SINGLE_DISH,
        diameter_m=100.0,
        wavelength_range_um=(3000, 1000000),
        angular_resolution_arcsec=7.0,
        spectral_resolution_max=1e8,
        sensitivity_jy=0.001,
        field_of_view_arcmin=0.5,
        available_instruments=['ARGUS', 'MUSTANG2', 'VEGAS'],
        location='West Virginia',
        typical_time_pressure=2.0
    ),
    'IRAM_30m': Telescope(
        name='IRAM_30m',
        telescope_type=TelescopeType.SUBMM_SINGLE_DISH,
        diameter_m=30.0,
        wavelength_range_um=(800, 4000),
        angular_resolution_arcsec=10.0,
        spectral_resolution_max=1e7,
        sensitivity_jy=0.01,
        field_of_view_arcmin=0.5,
        available_instruments=['EMIR', 'NIKA2'],
        location='Spain',
        typical_time_pressure=2.5
    ),
    'VLT': Telescope(
        name='VLT',
        telescope_type=TelescopeType.OPTICAL_GROUND,
        diameter_m=8.2,
        wavelength_range_um=(0.3, 25),
        angular_resolution_arcsec=0.05,
        spectral_resolution_max=100000,
        sensitivity_jy=1e-5,
        field_of_view_arcmin=1.0,
        available_instruments=['UVES', 'MUSE', 'KMOS', 'VISIR'],
        location='Chile',
        typical_time_pressure=4.0
    ),
    'HST': Telescope(
        name='HST',
        telescope_type=TelescopeType.OPTICAL_SPACE,
        diameter_m=2.4,
        wavelength_range_um=(0.1, 2.5),
        angular_resolution_arcsec=0.1,
        spectral_resolution_max=100000,
        sensitivity_jy=1e-6,
        field_of_view_arcmin=3.0,
        available_instruments=['WFC3', 'COS', 'STIS'],
        location='LEO',
        typical_time_pressure=6.0
    ),
}


class ObservationDesigner:
    """
    Design observations to test hypotheses.

    Suggests optimal telescope, instrument, and exposure.
    """

    def __init__(self, facilities: Optional[Dict[str, Telescope]] = None):
        """Initialize with available facilities."""
        self.facilities = facilities or TELESCOPE_DATABASE

    def design_observation(
        self,
        hypothesis: Hypothesis,
        target_coords: Tuple[float, float],
        constraints: Optional[List[str]] = None
    ) -> List[ObservationPlan]:
        """
        Design observations to test hypothesis.

        Parameters
        ----------
        hypothesis : Hypothesis
            Hypothesis to test
        target_coords : tuple
            (RA, Dec) in degrees
        constraints : list, optional
            Observational constraints

        Returns
        -------
        List of observation plans, ranked by information gain
        """
        plans = []
        constraints = constraints or []

        for observable in hypothesis.required_observables:
            # Find suitable facilities
            suitable = self._find_suitable_facilities(observable)

            for telescope_name in suitable:
                telescope = self.facilities[telescope_name]

                # Calculate required integration time
                predicted = hypothesis.predictions.get(observable, 1.0)
                uncertainty = hypothesis.uncertainties.get(observable, 0.1)

                # Need SNR ~ predicted / uncertainty
                required_snr = predicted / uncertainty if uncertainty > 0 else 10.0

                # Integration time scales as SNR^2
                base_time = 1.0  # 1 hour for baseline SNR
                integration_time = base_time * (required_snr / 10.0)**2

                # Check if achievable
                if integration_time > 100:  # Max 100 hours
                    continue

                # Determine observation type
                obs_type = self._determine_obs_type(observable)

                # Calculate expected SNR
                expected_snr = 10.0 * np.sqrt(integration_time / base_time)

                plan = ObservationPlan(
                    target=f'RA={target_coords[0]:.4f}, Dec={target_coords[1]:.4f}',
                    telescope=telescope_name,
                    instrument=telescope.available_instruments[0],
                    observation_type=obs_type,
                    wavelength_um=self._observable_to_wavelength(observable),
                    integration_time_hours=integration_time,
                    expected_snr=expected_snr,
                    angular_resolution_arcsec=telescope.angular_resolution_arcsec,
                    spectral_resolution=telescope.spectral_resolution_max if obs_type == ObservationType.SPECTROSCOPY else None,
                    science_goal=f'Test {hypothesis.name}: measure {observable}',
                    constraints=constraints,
                    estimated_success_probability=min(0.9, expected_snr / required_snr)
                )
                plans.append(plan)

        # Rank by success probability and time efficiency
        plans.sort(key=lambda p: p.estimated_success_probability / np.sqrt(p.integration_time_hours), reverse=True)

        return plans[:5]  # Return top 5

    def _find_suitable_facilities(self, observable: str) -> List[str]:
        """Find facilities suitable for observable."""
        suitable = []

        observable_lower = observable.lower()

        for name, telescope in self.facilities.items():
            # Match by wavelength domain
            if 'mm' in observable_lower or 'submm' in observable_lower:
                if telescope.telescope_type in [TelescopeType.SUBMM_SINGLE_DISH,
                                                 TelescopeType.SUBMM_INTERFEROMETER]:
                    suitable.append(name)

            elif 'radio' in observable_lower or 'cm' in observable_lower:
                if telescope.telescope_type in [TelescopeType.RADIO_SINGLE_DISH,
                                                 TelescopeType.RADIO_INTERFEROMETER]:
                    suitable.append(name)

            elif 'ir' in observable_lower or 'infrared' in observable_lower:
                if telescope.telescope_type in [TelescopeType.IR_GROUND,
                                                 TelescopeType.IR_SPACE]:
                    suitable.append(name)

            elif 'optical' in observable_lower or 'visual' in observable_lower:
                if telescope.telescope_type in [TelescopeType.OPTICAL_GROUND,
                                                 TelescopeType.OPTICAL_SPACE]:
                    suitable.append(name)

            elif 'xray' in observable_lower or 'x-ray' in observable_lower:
                if telescope.telescope_type == TelescopeType.XRAY:
                    suitable.append(name)

            # Match by molecular line
            elif any(mol in observable_lower for mol in ['co', 'hcn', 'n2h+', 'hco+']):
                if telescope.wavelength_range_um[1] > 300:  # mm/submm
                    suitable.append(name)

            # Match by specific observable
            elif 'temperature' in observable_lower or 'dust' in observable_lower:
                if telescope.wavelength_range_um[1] > 100:
                    suitable.append(name)

        # Default: return ALMA for molecular, JWST for IR
        if not suitable:
            suitable = ['ALMA', 'JWST']

        return suitable

    def _determine_obs_type(self, observable: str) -> ObservationType:
        """Determine observation type for observable."""
        observable_lower = observable.lower()

        if any(word in observable_lower for word in ['spectrum', 'line', 'velocity', 'linewidth']):
            return ObservationType.SPECTROSCOPY

        if any(word in observable_lower for word in ['cube', 'map', 'field']):
            return ObservationType.SPECTRAL_CUBE

        if any(word in observable_lower for word in ['polarization', 'magnetic']):
            return ObservationType.POLARIMETRY

        if any(word in observable_lower for word in ['variability', 'period', 'time']):
            return ObservationType.TIME_SERIES

        return ObservationType.IMAGING

    def _observable_to_wavelength(self, observable: str) -> float:
        """Estimate wavelength for observable."""
        observable_lower = observable.lower()

        # Common mappings
        if 'co' in observable_lower and '1-0' in observable_lower:
            return 2600  # um, CO(1-0)
        if 'co' in observable_lower and '2-1' in observable_lower:
            return 1300
        if 'co' in observable_lower and '3-2' in observable_lower:
            return 870
        if 'hcn' in observable_lower:
            return 3400
        if 'dust' in observable_lower or 'continuum' in observable_lower:
            return 850
        if 'halpha' in observable_lower or 'h_alpha' in observable_lower:
            return 0.656
        if 'xray' in observable_lower:
            return 1e-4

        return 100.0  # Default MIR


class DiscriminatingTestFinder:
    """
    Find observations that discriminate between rival theories.

    Identifies critical tests with maximum distinguishing power.
    """

    def __init__(self):
        """Initialize finder."""
        pass

    def find_discriminating_test(
        self,
        theory_a: Dict[str, Any],
        theory_b: Dict[str, Any]
    ) -> CriticalTest:
        """
        Find observation that best discriminates theories.

        Parameters
        ----------
        theory_a : dict
            First theory with predictions
        theory_b : dict
            Second theory with predictions

        Returns
        -------
        CriticalTest with best discriminating observation
        """
        preds_a = theory_a.get('predictions', {})
        preds_b = theory_b.get('predictions', {})
        errs_a = theory_a.get('uncertainties', {})
        errs_b = theory_b.get('uncertainties', {})

        best_test = None
        best_power = 0.0

        # Find shared observables
        shared = set(preds_a.keys()) & set(preds_b.keys())

        for observable in shared:
            pred_a = preds_a[observable]
            pred_b = preds_b[observable]
            err_a = errs_a.get(observable, 0.1 * abs(pred_a))
            err_b = errs_b.get(observable, 0.1 * abs(pred_b))

            # Discriminating power = separation / combined_error
            combined_err = np.sqrt(err_a**2 + err_b**2)
            if combined_err > 0:
                separation = abs(pred_a - pred_b)
                power = separation / combined_err
            else:
                power = 0.0

            if power > best_power:
                best_power = power
                required_precision = combined_err / 3  # Need 3-sigma precision

                # Recommend facility
                facility = self._recommend_facility(observable)

                best_test = CriticalTest(
                    description=f'Measure {observable} to distinguish {theory_a.get("name", "A")} vs {theory_b.get("name", "B")}',
                    observable=observable,
                    theory_a_prediction=pred_a,
                    theory_b_prediction=pred_b,
                    required_precision=required_precision,
                    recommended_facility=facility,
                    estimated_time_hours=self._estimate_time(observable, required_precision),
                    discriminating_power=power
                )

        if best_test is None:
            best_test = CriticalTest(
                description='No discriminating test found',
                observable='none',
                theory_a_prediction=0.0,
                theory_b_prediction=0.0,
                required_precision=0.0,
                recommended_facility='none',
                estimated_time_hours=0.0,
                discriminating_power=0.0
            )

        return best_test

    def _recommend_facility(self, observable: str) -> str:
        """Recommend facility for observable."""
        obs_lower = observable.lower()

        if any(mol in obs_lower for mol in ['co', 'hcn', 'n2h+', 'molecular']):
            return 'ALMA'
        if 'radio' in obs_lower or 'synchrotron' in obs_lower:
            return 'VLA'
        if 'ir' in obs_lower or 'dust' in obs_lower:
            return 'JWST'
        if 'xray' in obs_lower:
            return 'Chandra'
        if 'optical' in obs_lower:
            return 'VLT'

        return 'ALMA'

    def _estimate_time(self, observable: str, precision: float) -> float:
        """Estimate integration time for precision."""
        # Very rough estimate: better precision needs longer time
        base_time = 2.0  # hours for typical observation

        # Time scales as precision^-2
        if precision > 0:
            time = base_time / (precision / 0.1)**2
        else:
            time = base_time

        return max(0.5, min(time, 50.0))


class SensitivityCalculator:
    """
    Estimate detection limits for proposed observations.

    Accounts for telescope, weather, source properties.
    """

    def __init__(self, facilities: Optional[Dict[str, Telescope]] = None):
        """Initialize with facilities."""
        self.facilities = facilities or TELESCOPE_DATABASE

    def calculate_sensitivity(
        self,
        telescope: str,
        integration_time_hours: float,
        weather_conditions: str = 'average'
    ) -> float:
        """
        Calculate point source sensitivity.

        Parameters
        ----------
        telescope : str
            Telescope name
        integration_time_hours : float
            Integration time
        weather_conditions : str
            'excellent', 'average', 'poor'

        Returns
        -------
        5-sigma sensitivity in Jy
        """
        if telescope not in self.facilities:
            return 1.0  # Default 1 Jy

        tel = self.facilities[telescope]
        base_sensitivity = tel.sensitivity_jy

        # Sensitivity improves as sqrt(time)
        time_factor = 1.0 / np.sqrt(integration_time_hours)

        # Weather factor
        weather_factors = {
            'excellent': 0.7,
            'average': 1.0,
            'poor': 1.5
        }
        weather_factor = weather_factors.get(weather_conditions, 1.0)

        return base_sensitivity * time_factor * weather_factor

    def calculate_line_sensitivity(
        self,
        telescope: str,
        integration_time_hours: float,
        spectral_resolution: float,
        weather_conditions: str = 'average'
    ) -> float:
        """
        Calculate spectral line sensitivity.

        Parameters
        ----------
        telescope : str
            Telescope name
        integration_time_hours : float
            Integration time
        spectral_resolution : float
            R = lambda/delta_lambda
        weather_conditions : str
            Weather conditions

        Returns
        -------
        5-sigma line sensitivity in K km/s or Jy km/s
        """
        continuum_sens = self.calculate_sensitivity(
            telescope, integration_time_hours, weather_conditions
        )

        # Line sensitivity scales with channel width
        # Assume baseline R=1000
        channel_factor = np.sqrt(spectral_resolution / 1000)

        return continuum_sens * channel_factor

    def will_detect(
        self,
        telescope: str,
        source_flux: float,
        integration_time_hours: float,
        required_snr: float = 5.0
    ) -> Tuple[bool, float]:
        """
        Check if source will be detected.

        Returns (detected, achieved_snr).
        """
        sensitivity = self.calculate_sensitivity(telescope, integration_time_hours)

        achieved_snr = source_flux / sensitivity * 5.0  # Base is 5-sigma

        detected = achieved_snr >= required_snr

        return detected, achieved_snr


class FollowupPrioritizer:
    """
    Rank targets for follow-up based on information gain.

    Prioritizes targets that maximize scientific return.
    """

    def __init__(self):
        """Initialize prioritizer."""
        pass

    def prioritize_targets(
        self,
        targets: List[Dict[str, Any]],
        science_goal: str,
        available_time_hours: float
    ) -> List[Tuple[Dict, float, str]]:
        """
        Prioritize targets for follow-up.

        Parameters
        ----------
        targets : list
            List of target dictionaries with properties
        science_goal : str
            Scientific goal (e.g., 'star_formation', 'agn')
        available_time_hours : float
            Total available observation time

        Returns
        -------
        List of (target, priority_score, justification)
        """
        scored_targets = []

        for target in targets:
            score, justification = self._score_target(target, science_goal)
            scored_targets.append((target, score, justification))

        # Sort by score
        scored_targets.sort(key=lambda x: x[1], reverse=True)

        # Select targets fitting in time budget
        selected = []
        remaining_time = available_time_hours

        for target, score, justification in scored_targets:
            est_time = target.get('estimated_time', 2.0)
            if est_time <= remaining_time:
                selected.append((target, score, justification))
                remaining_time -= est_time

        return selected

    def _score_target(
        self,
        target: Dict[str, Any],
        science_goal: str
    ) -> Tuple[float, str]:
        """Score a single target."""
        score = 0.0
        reasons = []

        # Check relevance to science goal
        goal_lower = science_goal.lower()
        target_type = target.get('type', '').lower()

        if 'star_formation' in goal_lower:
            if any(sf in target_type for sf in ['protostar', 'core', 'yso', 'outflow']):
                score += 0.3
                reasons.append('Relevant to star formation')

        elif 'agn' in goal_lower:
            if any(a in target_type for a in ['agn', 'quasar', 'seyfert']):
                score += 0.3
                reasons.append('AGN target')

        # Brightness bonus (brighter = easier)
        flux = target.get('flux', 0.0)
        if flux > 1.0:
            score += 0.2
            reasons.append('Bright source')
        elif flux > 0.1:
            score += 0.1
            reasons.append('Moderate brightness')

        # Uniqueness bonus
        if target.get('unique_properties', False):
            score += 0.2
            reasons.append('Unique properties')

        # Previous data bonus
        if target.get('archival_data', False):
            score += 0.1
            reasons.append('Archival data available')

        # Accessibility penalty
        dec = target.get('dec', 0.0)
        if abs(dec) > 60:
            score -= 0.1
            reasons.append('Limited accessibility')

        justification = '; '.join(reasons) if reasons else 'Standard priority'

        return max(0, score), justification

    def calculate_information_gain(
        self,
        target: Dict[str, Any],
        current_knowledge: Dict[str, Any]
    ) -> float:
        """
        Calculate expected information gain from observing target.

        Uses entropy reduction estimate.
        """
        # Current uncertainty
        current_entropy = 0.0
        for param, uncertainty in current_knowledge.get('uncertainties', {}).items():
            if uncertainty > 0:
                current_entropy += np.log(uncertainty)

        # Expected uncertainty after observation
        target_snr = target.get('expected_snr', 10.0)
        improvement_factor = 1.0 / np.sqrt(target_snr / 10.0)

        expected_entropy = 0.0
        for param, uncertainty in current_knowledge.get('uncertainties', {}).items():
            if uncertainty > 0:
                expected_entropy += np.log(uncertainty * improvement_factor)

        # Information gain is entropy reduction
        info_gain = current_entropy - expected_entropy

        return max(0, info_gain)


# Convenience functions

def design_observation_for_hypothesis(
    hypothesis: Hypothesis,
    target_ra: float,
    target_dec: float
) -> List[ObservationPlan]:
    """
    Design observations to test hypothesis.
    """
    designer = ObservationDesigner()
    return designer.design_observation(hypothesis, (target_ra, target_dec))


def find_critical_test(
    theory_a: Dict[str, Any],
    theory_b: Dict[str, Any]
) -> CriticalTest:
    """
    Find observation that discriminates between theories.
    """
    finder = DiscriminatingTestFinder()
    return finder.find_discriminating_test(theory_a, theory_b)


def calculate_detection_limit(
    telescope: str,
    integration_hours: float
) -> float:
    """
    Calculate 5-sigma detection limit.
    """
    calculator = SensitivityCalculator()
    return calculator.calculate_sensitivity(telescope, integration_hours)


def prioritize_followup(
    targets: List[Dict[str, Any]],
    science_goal: str,
    available_hours: float
) -> List[Tuple[Dict, float, str]]:
    """
    Prioritize targets for follow-up observation.
    """
    prioritizer = FollowupPrioritizer()
    return prioritizer.prioritize_targets(targets, science_goal, available_hours)


def get_observation_designer() -> ObservationDesigner:
    """Get singleton-like observation designer."""
    return ObservationDesigner()


def get_telescope_database() -> Dict[str, Telescope]:
    """Get the telescope database."""
    return TELESCOPE_DATABASE
