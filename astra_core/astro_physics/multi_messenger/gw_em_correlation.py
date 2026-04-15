#!/usr/bin/env python3

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
Gravitational Wave - Electromagnetic Correlation Analysis

Joint analysis of gravitational wave and electromagnetic observations
for multi-messenger astrophysics.

Applications:
- Kilonova identification and characterization
- Gamma-ray burst association with GW mergers
- Supernova GW emission
- Compact merger progenitor identification
- Multi-messenger parameter estimation
- Host galaxy identification

Author: STAN Evolution Team
Date: 2025-03-18
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from scipy import stats
from scipy.spatial import cKDTree
from scipy.optimize import minimize
import warnings


@dataclass
class GWTrigger:
    """Gravitational wave trigger information"""
    event_id: str
    time: float  # GPS time or similar
    ra: float  # Right ascension (degrees)
    dec: float  # Declination (degrees)
    error_radius: float  # Localization error (degrees)
    distance: float  # Luminosity distance (Mpc)
    distance_error: float  # Mpc
    chirp_mass: float  # Chirp mass (solar masses)
    mass_ratio: float  # q = m2/m1 <= 1
    network_snr: float  # Signal-to-noise ratio
    false_alarm_rate: float  # Hz
    far_is_hierarchical: bool = False
    classification: Dict[str, float] = field(default_factory=dict)
    # {'BNS': probability, 'NSBH': probability, 'BBH': probability}
    detectors: List[str] = field(default_factory=list)


@dataclass
class EMCounterpart:
    """Electromagnetic counterpart observation"""
    source_id: str
    observation_time: float  # Same time system as GW
    ra: float
    dec: float
    error_radius: float
    magnitude: float
    filter: str
    transient_type: Optional[str] = None
    redshift: Optional[float] = None
    host_distance: Optional[float] = None  # Mpc
    features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JointGWEMDetection:
    """Joint GW-EM detection result"""
    gw_event: GWTrigger
    em_counterparts: List[EMCounterpart]
    association_probability: float
    temporal_offset: float  # EM time - GW time
    angular_separation: float  # degrees
    distance_consistency: float  # [0, 1]
    classification: str  # 'confident', 'likely', 'possible', 'unlikely'
    joint_parameters: Dict[str, Any] = field(default_factory=dict)


class TemporalCorrelation:
    """
    Analyze temporal correlations between GW and EM events.

    Accounts for:
    - Light travel time differences
    - GW propagation delays
    - EM emission delays (kilonova rise time)
    """

    def __init__(self):
        # Expected time delays for different source types
        self.expected_delays = {
            'BNS': {  # Binary neutron star
                'gamma_prompt': (1.7, 0.1),  # Short GRB (mean, std) in seconds
                'kilonova_early': (0.1, 0.05),  # Hours
                'kilonova_peak': (1.0, 0.3),  # Days
                'kilonova_late': (7.0, 2.0),  # Days
            },
            'NSBH': {  # Neutron star - black hole
                'gamma_prompt': (1.5, 0.2),
                'kilonova_early': (0.05, 0.02),
                'kilonova_peak': (0.5, 0.2),
                'kilonova_late': (5.0, 1.5),
            },
            'BBH': {  # Binary black hole
                # Usually no EM counterpart expected
                'any': (None, None),
            }
        }

    def compute_temporal_probability(
        self,
        gw_time: float,
        em_time: float,
        source_type: str = 'BNS',
        emission_type: str = 'kilonova_peak'
    ) -> Tuple[float, float]:
        """
        Compute probability of temporal correlation.

        Args:
            gw_time: GW merger time
            em_time: EM detection time
            source_type: 'BNS', 'NSBH', or 'BBH'
            emission_type: Type of EM emission

        Returns:
            Tuple of (probability, time_offset_days)
        """
        time_diff = (em_time - gw_time) / 86400.0  # Convert to days

        # Get expected delay
        if source_type in self.expected_delays:
            if emission_type in self.expected_delays[source_type]:
                mean_delay, std_delay = self.expected_delays[source_type][emission_type]
            else:
                mean_delay, std_delay = self.expected_delays[source_type].get('kilonova_peak', (1.0, 1.0))
        else:
            mean_delay, std_delay = 1.0, 1.0

        if mean_delay is None:
            # No emission expected
            return 0.0, time_diff

        # Compute probability using Gaussian
        if std_delay > 0:
            z_score = abs(time_diff - mean_delay) / std_delay
            prob = 2 * (1 - stats.norm.cdf(z_score))
        else:
            prob = 1.0 if time_diff == mean_delay else 0.0

        return prob, time_diff


class SpatialCorrelation:
    """
    Analyze spatial correlations between GW localizations and EM positions.

    Uses:
    - GW sky localization probability maps
    - EM position uncertainties
    - Host galaxy positions and redshifts
    """

    def __init__(self):
        pass

    def compute_angular_separation(
        self,
        ra1: float, dec1: float,
        ra2: float, dec2: float
    ) -> float:
        """
        Compute angular separation between two positions.

        Args:
            ra1, dec1: First position (degrees)
            ra2, dec2: Second position (degrees)

        Returns:
            Separation in degrees
        """
        # Convert to radians
        ra1_rad, dec1_rad = np.radians([ra1, dec1])
        ra2_rad, dec2_rad = np.radians([ra2, dec2])

        # Haversine formula
        dra = ra2_rad - ra1_rad
        ddec = dec2_rad - dec1_rad

        a = np.sin(ddec/2)**2 + np.cos(dec1_rad) * np.cos(dec2_rad) * np.sin(dra/2)**2
        sep_rad = 2 * np.arcsin(np.sqrt(a))

        return np.degrees(sep_rad)

    def compute_spatial_probability(
        self,
        gw_localization: Dict,  # Sky probability map
        em_ra: float,
        em_dec: float,
        em_error: float
    ) -> Tuple[float, float]:
        """
        Compute spatial correlation probability.

        Args:
            gw_localization: GW sky map (healpix or grid)
            em_ra: EM source RA
            em_dec: EM source Dec
            em_error: EM position error (degrees)

        Returns:
            Tuple of (probability, separation_degrees)
        """
        # Simplified - would use full probability map in production
        # For now, assume circular Gaussian GW localization

        gw_ra = gw_localization.get('ra', 0.0)
        gw_dec = gw_localization.get('dec', 0.0)
        gw_sigma = gw_localization.get('sigma', 10.0)  # degrees

        # Compute separation
        separation = self.compute_angular_separation(gw_ra, gw_dec, em_ra, em_dec)

        # Combined uncertainty
        combined_sigma = np.sqrt(gw_sigma**2 + em_error**2)

        # Probability using 2D Gaussian
        prob = np.exp(-0.5 * (separation / combined_sigma)**2)

        # Normalize (simplified)
        prob = prob / (2 * np.pi * combined_sigma**2)

        return prob, separation


class DistanceConsistency:
    """
    Check consistency between GW distance and EM distance estimates.

    Uses:
    - GW luminosity distance
    - EM redshift (via cosmology)
    - Host galaxy distances
    """

    def __init__(self, h0: float = 70.0, omega_m: float = 0.3):
        """
        Initialize distance consistency checker.

        Args:
            h0: Hubble constant (km/s/Mpc)
            omega_m: Matter density parameter
        """
        self.h0 = h0
        self.omega_m = omega_m
        self.omega_lambda = 1.0 - omega_m

    def redshift_to_distance(self, z: float) -> float:
        """
        Convert redshift to luminosity distance.

        Uses simplified Lambda-CDM cosmology.

        Args:
            z: Redshift

        Returns:
            Luminosity distance (Mpc)
        """
        # Low-z approximation (Hubble's law)
        if z < 0.1:
            # d_L = (c/H0) * z * (1 + z/2)
            c = 299792.458  # km/s
            d_L = (c / self.h0) * z * (1 + z/2) / 1e6  # Mpc
            return d_L

        # For higher z, would need full cosmological integral
        # Simplified here
        c = 299792.458  # km/s
        d_L = (c / self.h0) * z * (1 + z) / 1e6  # Rough approximation
        return d_L

    def compute_distance_consistency(
        self,
        gw_distance: float,
        gw_error: float,
        em_redshift: Optional[float] = None,
        em_distance: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Compute distance consistency score.

        Args:
            gw_distance: GW luminosity distance (Mpc)
            gw_error: GW distance error (Mpc)
            em_redshift: EM source redshift (optional)
            em_distance: EM source distance (Mpc, optional)

        Returns:
            Tuple of (consistency_score [0,1], distance_diff_sigma)
        """
        if em_redshift is not None:
            em_dist = self.redshift_to_distance(em_redshift)
            em_error = em_dist * 0.1  # 10% uncertainty from peculiar velocity
        elif em_distance is not None:
            em_dist = em_distance
            em_error = em_distance * 0.1  # Assumed uncertainty
        else:
            return 0.0, 0.0

        # Compute difference in sigma
        diff = abs(gw_distance - em_dist)
        combined_error = np.sqrt(gw_error**2 + em_error**2)

        sigma_diff = diff / combined_error

        # Consistency score using Gaussian
        consistency = np.exp(-0.5 * sigma_diff**2)

        return consistency, sigma_diff


class GWEMCorrelator:
    """
    Main GW-EM correlation system.

    Combines temporal, spatial, and distance information to identify
    and characterize GW-EM associations.

    Example:
        >>> correlator = GWEMCorrelator()
        >>>
        >>> gw_trigger = GWTrigger(
        ...     event_id="GW190814",
        ...     time=1249852257.0,
        ...     ra=310.23,
        ...     dec=-28.89,
        ...     error_radius=15.0,
        ...     distance=300.0,
        ...     distance_error=50.0,
        ...     chirp_mass=10.0,
        ...     mass_ratio=0.8,
        ...     network_snr=20.0,
        ...     false_alarm_rate=1e-6
        ... )
        >>>
        >>> em_sources = [EMCounterpart(...)]
        >>>
        >>> detections = correlator.find_associations(gw_trigger, em_sources)
    """

    def __init__(self, h0: float = 70.0):
        """
        Initialize GW-EM correlator.

        Args:
            h0: Hubble constant for distance-redshift conversion
        """
        self.temporal = TemporalCorrelation()
        self.spatial = SpatialCorrelation()
        self.distance = DistanceConsistency(h0=h0)

        # Association thresholds
        self.temporal_threshold = 0.1  # Minimum temporal probability
        self.spatial_threshold = 0.01  # Minimum spatial probability
        self.combined_threshold = 0.5  # Minimum combined probability

    def find_associations(
        self,
        gw_trigger: GWTrigger,
        em_candidates: List[EMCounterpart],
        source_type: str = 'BNS'
    ) -> List[JointGWEMDetection]:
        """
        Find EM counterparts to GW trigger.

        Args:
            gw_trigger: GW trigger information
            em_candidates: List of EM counterpart candidates
            source_type: Expected source type

        Returns:
            List of joint detections, ranked by association probability
        """
        detections = []

        for em in em_candidates:
            # Temporal correlation
            temp_prob, time_offset = self.temporal.compute_temporal_probability(
                gw_trigger.time,
                em.observation_time,
                source_type,
                'kilonova_peak'  # Assume kilonova
            )

            # Spatial correlation
            gw_localization = {
                'ra': gw_trigger.ra,
                'dec': gw_trigger.dec,
                'sigma': gw_trigger.error_radius
            }
            spat_prob, separation = self.spatial.compute_spatial_probability(
                gw_localization,
                em.ra,
                em.dec,
                em.error_radius
            )

            # Distance consistency
            dist_consistency, dist_sigma = self.distance.compute_distance_consistency(
                gw_trigger.distance,
                gw_trigger.distance_error,
                em.redshift,
                em.host_distance
            )

            # Combined probability
            # Use product of independent probabilities
            combined_prob = temp_prob * spat_prob

            # Boost if distances are consistent
            if dist_consistency > 0.5:
                combined_prob *= (1 + dist_consistency)

            # Normalize
            combined_prob = min(combined_prob, 1.0)

            # Classification
            if combined_prob > 0.8:
                classification = 'confident'
            elif combined_prob > 0.5:
                classification = 'likely'
            elif combined_prob > 0.1:
                classification = 'possible'
            else:
                classification = 'unlikely'

            # Create detection
            detection = JointGWEMDetection(
                gw_event=gw_trigger,
                em_counterparts=[em],
                association_probability=combined_prob,
                temporal_offset=time_offset,
                angular_separation=separation,
                distance_consistency=dist_consistency,
                classification=classification,
                joint_parameters={}
            )

            detections.append(detection)

        # Sort by association probability
        detections.sort(key=lambda d: d.association_probability, reverse=True)

        return detections

    def rank_host_galaxies(
        self,
        gw_trigger: GWTrigger,
        galaxy_catalog: List[Dict],
        max_galaxies: int = 100
    ) -> List[Dict]:
        """
        Rank galaxies in GW localization by probability of being host.

        Args:
            gw_trigger: GW trigger
            galaxy_catalog: List of galaxies with ra, dec, distance/redshift
            max_galaxies: Maximum number to return

        Returns:
            Ranked list of galaxies with host probabilities
        """
        ranked_galaxies = []

        for galaxy in galaxy_catalog:
            # Spatial offset
            separation = self.spatial.compute_angular_separation(
                gw_trigger.ra, gw_trigger.dec,
                galaxy['ra'], galaxy['dec']
            )

            # Distance consistency
            dist_consistency, _ = self.distance.compute_distance_consistency(
                gw_trigger.distance,
                gw_trigger.distance_error,
                galaxy.get('redshift'),
                galaxy.get('distance')
            )

            # Host probability (simplified)
            # Combines spatial offset and distance consistency
            spatial_prob = np.exp(-0.5 * (separation / gw_trigger.error_radius)**2)

            host_prob = spatial_prob * dist_consistency

            galaxy_info = galaxy.copy()
            galaxy_info['host_probability'] = host_prob
            galaxy_info['angular_separation'] = separation
            galaxy_info['distance_consistency'] = dist_consistency

            ranked_galaxies.append(galaxy_info)

        # Sort and return top
        ranked_galaxies.sort(key=lambda g: g['host_probability'], reverse=True)

        return ranked_galaxies[:max_galaxies]


class KilonovaModel:
    """
    Model kilonova light curves from GW parameters.

    Predicts kilonova emission based on:
    - Chirp mass and mass ratio
    - Ejecta mass
    - Viewing angle
    """

    def __init__(self):
        # Simplified kilonova model parameters
        self.diffusion_timescale = 3.0  # days
        self.palomer_constant = 0.5  # mag

    def predict_light_curve(
        self,
        ejecta_mass: float,  # Solar masses
        velocity: float,  # c
        viewing_angle: float,  # radians from pole
        times: np.ndarray  # Days post-merger
    ) -> np.ndarray:
        """
        Predict kilonova light curve.

        Args:
            ejecta_mass: Ejecta mass
            velocity: Ejecta velocity (fraction of c)
            viewing_angle: Viewing angle from polar axis
            times: Time points (days)

        Returns:
            Absolute magnitude at each time
        """
        # Simplified Arnett-like model

        # Characteristic timescale
        t0 = self.diffusion_timescale * (ejecta_mass / 0.01)**0.25 * (velocity / 0.1)**-0.5

        # Peak luminosity (simplified)
        M_peak = -16.0 - 2.5 * np.log10(ejecta_mass / 0.01)

        # Light curve shape
        # Rise: (t/t0)^2
        # Fall: exp(-(t-t0)/t0)

        light_curve = np.zeros_like(times)

        for i, t in enumerate(times):
            if t < t0:
                # Rising phase
                light_curve[i] = M_peak - 2.5 * np.log10((t / t0)**2 + 1e-10)
            else:
                # Declining phase
                light_curve[i] = M_peak - (t - t0) / 1.5  # ~0.67 mag/day decline

        # Viewing angle dependence
        # Brighter towards pole
        cos_theta = np.cos(viewing_angle)
        angle_factor = 1.0 + 0.3 * cos_theta**2
        light_curve -= 2.5 * np.log10(angle_factor)

        return light_curve

    def estimate_ejecta_mass(
        self,
        chirp_mass: float,
        mass_ratio: float,
        is_bns: bool = True
    ) -> float:
        """
        Estimate kilonova ejecta mass from merger parameters.

        Args:
            chirp_mass: Chirp mass
            mass_ratio: Mass ratio q = m2/m1
            is_bns: Whether this is BNS (vs NSBH)

        Returns:
            Ejecta mass (solar masses)
        """
        if is_bns:
            # Simplified BNS ejecta model
            # More asymmetric systems produce more dynamical ejecta
            symmetric_factor = 4 * mass_ratio / (1 + mass_ratio)**2

            # Typical values: 0.001 - 0.05 Msun
            ejecta_mass = 0.01 * symmetric_factor
        else:
            # NSBH produces more ejecta
            ejecta_mass = 0.05

        return ejecta_mass


class MultiEpochCorrelation:
    """
    Track and correlate multi-epoch GW-EM observations.

    Useful for:
    - Monitoring kilonova evolution
    - Detecting late-time emission
    - Identifying orphan afterglows
    """

    def __init__(self):
        self.associations: Dict[str, List[EMCounterpart]] = {}

    def add_observation(
        self,
        gw_event_id: str,
        em_observation: EMCounterpart
    ):
        """Add EM observation for a GW event."""
        if gw_event_id not in self.associations:
            self.associations[gw_event_id] = []

        self.associations[gw_event_id].append(em_observation)

    def get_light_curve(
        self,
        gw_event_id: str,
        filter: str = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extract light curve from associated observations.

        Args:
            gw_event_id: GW event identifier
            filter: Photometric filter (optional)

        Returns:
            Tuple of (times, magnitudes, errors)
        """
        if gw_event_id not in self.associations:
            return np.array([]), np.array([]), np.array([])

        observations = self.associations[gw_event_id]

        if filter:
            observations = [obs for obs in observations if obs.filter == filter]

        times = np.array([obs.observation_time for obs in observations])
        mags = np.array([obs.magnitude for obs in observations])
        errors = np.array([obs.features.get('magnitude_error', 0.1)
                          for obs in observations])

        # Sort by time
        sort_idx = np.argsort(times)
        times = times[sort_idx]
        mags = mags[sort_idx]
        errors = errors[sort_idx]

        return times, mags, errors


def create_gw_em_correlator(**kwargs) -> GWEMCorrelator:
    """
    Factory function to create GW-EM correlator.

    Args:
        **kwargs: Arguments to pass to GWEMCorrelator

    Returns:
        Configured correlator
    """
    return GWEMCorrelator(**kwargs)


if __name__ == "__main__":
    print("="*70)
    print("Gravitational Wave - EM Correlation Analysis")
    print("="*70)
    print()
    print("Components:")
    print("  - GWEMCorrelator: Main correlation system")
    print("  - TemporalCorrelation: Time coincidence analysis")
    print("  - SpatialCorrelation: Sky localization matching")
    print("  - DistanceConsistency: Distance-redshift consistency")
    print("  - KilonovaModel: Kilonova light curve prediction")
    print("  - MultiEpochCorrelation: Multi-epoch tracking")
    print()
    print("Applications:")
    print("  - Kilonova identification")
    print("  - Short GRB association")
    print("  - Host galaxy ranking")
    print("  - Joint parameter estimation")
    print("="*70)
