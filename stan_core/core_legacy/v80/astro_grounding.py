"""
Astrophysics-Specific Grounding for V80
======================================

Implements grounded concepts specialized for astrophysical objects
and phenomena, integrating observational data with conceptual understanding.

Key Features:
- Celestial object grounding with spectra, position, magnitude
- Telescope observation patterns
- Cosmic evolutionary sequences
- Gravitational interaction patterns
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import astropy.units as u
from astropy.coordinates import SkyCoord

# Import base grounded concept (from same directory - core_legacy)
from .grounded_concept import (
    GroundedConcept, MultiModalGrounding, FormalStructure, TemporalPattern, ConceptSpace
)


@dataclass
class ObservationalGrounding:
    """Grounding specific to astronomical observations"""
    spectra: np.ndarray  # Spectral energy distribution
    light_curve: np.ndarray  # Time series brightness
    position: SkyCoord  # Sky coordinates (RA, Dec)
    redshift: float  # Cosmological redshift
    magnitude: Dict[str, float]  # Multi-band magnitudes
    angular_size: float  # Angular diameter in arcseconds
    proper_motion: Tuple[float, float]  # (RA, Dec) proper motion


@dataclass
class PhysicalGrounding:
    """Grounding for physical properties"""
    mass: float  # Solar masses
    radius: float  # Solar radii
    temperature: float  # Kelvin
    luminosity: float  # Solar luminosities
    composition: Dict[str, float]  # Elemental abundances
    age: float  # Billion years
    metallicity: float  # [Fe/H]


class AstroGroundedConcept(GroundedConcept):
    """
    Grounded concept specialized for astrophysical objects.

    Extends the base GroundedConcept with astronomical-specific
    grounding including observational and physical properties.
    """

    def __init__(self, name: str, object_type: str,
                 observational: Optional[ObservationalGrounding] = None,
                 physical: Optional[PhysicalGrounding] = None):
        # Initialize base grounding with astronomical features
        astro_grounding = self._create_astro_grounding(name, object_type, observational, physical)
        super().__init__(name, astro_grounding)

        # Add astronomical-specific properties
        self.object_type = object_type  # star, galaxy, nebula, etc.
        self.observational = observational or ObservationalGrounding(
            spectra=np.zeros(1000),
            light_curve=np.zeros(100),
            position=SkyCoord(0, 0, unit='deg'),
            redshift=0.0,
            magnitude={'V': 0.0},
            angular_size=0.0,
            proper_motion=(0.0, 0.0)
        )
        self.physical = physical or PhysicalGrounding(
            mass=1.0, radius=1.0, temperature=5800,
            luminosity=1.0, composition={'H': 0.7, 'He': 0.3},
            age=1.0, metallicity=0.0
        )

        # Astronomical knowledge graph connections
        self.astronomical_relations = {}

    def _create_astro_grounding(self, name: str, object_type: str,
                               observational: Optional[ObservationalGrounding],
                               physical: Optional[PhysicalGrounding]) -> MultiModalGrounding:
        """Create astronomical grounding from observational and physical data"""
        # Encode spectral features into perceptual grounding
        perceptual = self._encode_observational_data(observational) if observational else np.random.randn(512)

        # Motor patterns represent observation methods
        motor = self._create_observation_motor_patterns(object_type)

        # Linguistic context includes astronomical terminology
        linguistic = self._create_astronomical_linguistic(name, object_type)

        # Mathematical grounding includes physical laws
        mathematical = self._create_astronomical_mathematical(object_type, physical)

        # Causal patterns include evolutionary sequences
        causal = self._create_astronomical_causal(object_type)

        # Affective grounding represents scientific significance
        affective = self._create_astronomical_affective(object_type)

        return MultiModalGrounding(
            perceptual=perceptual,
            motor=motor,
            linguistic=linguistic,
            mathematical=mathematical,
            causal=causal,
            affective=affective
        )

    def _encode_observational_data(self, observational: ObservationalGrounding) -> np.ndarray:
        """Encode observational data into perceptual vector"""
        # Combine spectra, light curve, and other observational data
        features = np.concatenate([
            observational.spectra[:500],  # First 500 spectral bins
            observational.light_curve,
            [observational.redshift],
            list(observational.magnitude.values()),
            [observational.angular_size],
            list(observational.proper_motion)
        ])

        # Pad or truncate to 512 dimensions
        if len(features) < 512:
            features = np.pad(features, (0, 512 - len(features)))
        else:
            features = features[:512]

        return features

    def _create_observation_motor_patterns(self, object_type: str) -> List[Dict]:
        """Create motor patterns representing observation methods"""
        base_patterns = [
            {'action': 'observe', 'instrument': 'telescope'},
            {'action': 'measure', 'parameter': 'magnitude'},
            {'action': 'collect', 'data': 'spectrum'}
        ]

        if object_type == 'star':
            base_patterns.extend([
                {'action': 'measure', 'parameter': 'parallax'},
                {'action': 'analyze', 'parameter': 'spectral_lines'}
            ])
        elif object_type == 'galaxy':
            base_patterns.extend([
                {'action': 'measure', 'parameter': 'redshift'},
                {'action': 'resolve', 'structure': 'spiral_arms'},
                {'action': 'measure', 'parameter': 'rotation_curve'}
            ])
        elif object_type == 'nebula':
            base_patterns.extend([
                {'action': 'image', 'emission_lines': ['H-alpha', 'OIII']},
                {'action': 'measure', 'parameter': 'expansion_velocity'}
            ])

        return base_patterns

    def _create_astronomical_linguistic(self, name: str, object_type: str) -> Dict[str, float]:
        """Create astronomical linguistic associations"""
        base_linguistic = {
            name: 1.0,
            object_type: 0.95,
            'astronomical': 0.8,
            'celestial': 0.7,
            'observational': 0.6
        }

        # Add object-type specific terms
        if object_type == 'star':
            base_linguistic.update({
                'fusion': 0.8, 'hydrogen': 0.7, 'luminosity': 0.6,
                'main_sequence': 0.5, 'nuclear': 0.6
            })
        elif object_type == 'galaxy':
            base_linguistic.update({
                'gravitational': 0.8, 'dark_matter': 0.7, 'stellar_population': 0.6,
                'spiral': 0.5, 'elliptical': 0.5, 'rotation': 0.6
            })
        elif object_type == 'black_hole':
            base_linguistic.update({
                'event_horizon': 0.9, 'singularity': 0.8, 'gravity': 0.8,
                'spacetime': 0.7, 'accretion': 0.6
            })

        return base_linguistic

    def _create_astronomical_mathematical(self, object_type: str,
                                        physical: Optional[PhysicalGrounding]) -> FormalStructure:
        """Create mathematical structure with astronomical laws"""
        type_hierarchy = [object_type, 'celestial_object', 'astronomical_object']

        properties = {}

        if object_type == 'star':
            properties.update({
                'mass_luminosity_relation': 'L ∝ M^3.5',
                'stefan_boltzmann': 'L = 4πR²σT⁴',
                'hydrostatic_equilibrium': 'dP/dr = -GMρ/r²'
            })
        elif object_type == 'galaxy':
            properties.update({
                'hubble_law': 'v = H₀d',
                'rotation_curve': 'v² = GM(r)/r',
                'tidal_force': 'F = 2GMmd/r³'
            })
        elif object_type == 'black_hole':
            properties.update({
                'schwarzschild_radius': 'r_s = 2GM/c²',
                'hawking_radiation': 'T = ℏc³/(8πGMk_B)',
                'time_dilation': 't = t * sqrt(1 - r_s/r)'
            })

        if physical:
            properties.update({
                'mass': f"{physical.mass} M☉",
                'radius': f"{physical.radius} R☉",
                'temperature': f"{physical.temperature} K",
                'luminosity': f"{physical.luminosity} L☉"
            })

        return FormalStructure(
            type_hierarchy=type_hierarchy,
            properties=properties,
            relations={},
            invariants=['conservation_of_energy', 'conservation_of_momentum']
        )

    def _create_astronomical_causal(self, object_type: str) -> TemporalPattern:
        """Create causal patterns for astronomical evolution"""
        if object_type == 'star':
            sequence = ['nebula', 'protostar', 'main_sequence', 'red_giant', 'white_dwarf']
            duration = (10.0, 5.0)  # Billion years
        elif object_type == 'galaxy':
            sequence = ['primordial_fluctuation', 'dark_matter_halo', 'first_stars', 'disk_formation', 'spiral_structure']
            duration = (13.8, 2.0)  # Billion years
        elif object_type == 'black_hole':
            sequence = ['massive_star', 'core_collapse', 'supernova', 'remnant', 'black_hole']
            duration = (0.001, 0.0001)  # Billion years
        else:
            sequence = ['formation', 'evolution', 'end_state']
            duration = (1.0, 0.5)

        return TemporalPattern(
            duration_distribution=duration,
            sequence_structure=sequence,
            causal_strengths={}
        )

    def _create_astronomical_affective(self, object_type: str) -> np.ndarray:
        """Create affective grounding representing scientific importance"""
        # Different dimensions of scientific significance
        base_affective = np.array([0.5, 0.3, 0.4, 0.6])

        if object_type == 'black_hole':
            # High curiosity, medium understanding, high importance
            base_affective[0] = 0.9  # Curiosity
            base_affective[2] = 0.8  # Importance
        elif object_type == 'exoplanet':
            base_affective[0] = 0.8  # Curiosity
            base_affective[1] = 0.7  # Understanding
        elif object_type == 'supernova':
            base_affective[2] = 0.9  # Importance
            base_affective[3] = 0.8  # Discovery potential

        return base_affective

    def compute_luminosity_distance(self, h0: float = 70.0) -> float:
        """Compute luminosity distance from redshift"""
        if self.observational.redshift < 0.01:
            # Local approximation
            return self.observational.redshift * 3e5 / h0  # Mpc
        else:
            # Would use full cosmology here
            return self.observational.redshift * 3000  # Simplified

    def get_evolutionary_stage(self) -> str:
        """Get current evolutionary stage from causal pattern"""
        # In practice, would determine from physical properties
        if self.object_type == 'star':
            if self.physical.temperature > 10000:
                return 'main_sequence'
            elif self.physical.temperature < 4000:
                return 'red_giant'
            else:
                return 'subgiant'
        return 'unknown'

    def observe_with_telescope(self, telescope_type: str) -> Dict[str, Any]:
        """Simulate observation with specific telescope"""
        observation_result = {
            'telescope': telescope_type,
            'object': self.name,
            'observation_type': []
        }

        if telescope_type == 'optical':
            observation_result['observation_type'] = ['photometry', 'spectroscopy']
            observation_result['data'] = {
                'magnitude': self.observational.magnitude,
                'spectra': self.observational.spectra
            }
        elif telescope_type == 'radio':
            observation_result['observation_type'] = ['hi_21cm', 'continuum']
            observation_result['data'] = {
                'flux_density': np.random.exponential(1.0),
                'velocity_width': np.random.uniform(50, 300)
            }
        elif telescope_type == 'xray':
            observation_result['observation_type'] = ['xray_imaging', 'spectroscopy']
            observation_result['data'] = {
                'xray_luminosity': self.physical.luminosity * 0.001,
                'temperature': 1e7  # K
            }

        return observation_result

    def evolve(self, time_gyr: float) -> 'AstroGroundedConcept':
        """Evolve object forward in time"""
        if self.object_type == 'star':
            # Simple stellar evolution
            age = self.physical.age + time_gyr
            mass = self.physical.mass

            if age < 10 and mass > 0.8:
                # Main sequence evolution
                new_temp = self.physical.temperature * (age / 10) ** 0.2
                new_lum = self.physical.luminosity * (age / 10) ** 0.7
            elif age < 12:
                # Subgiant phase
                new_temp = self.physical.temperature * 0.8
                new_lum = self.physical.luminosity * 2.0
            else:
                # Red giant phase
                new_temp = self.physical.temperature * 0.5
                new_lum = self.physical.luminosity * 100.0

            # Create evolved object
            evolved = AstroGroundedConcept(
                f"{self.name}_evolved_{age:.1f}Gyr",
                self.object_type
            )
            evolved.physical = PhysicalGrounding(
                mass=mass,
                radius=self.physical.radius * (new_lum / new_temp**4) ** 0.5,
                temperature=new_temp,
                luminosity=new_lum,
                composition=self.physical.composition,
                age=age,
                metallicity=self.physical.metallicity
            )

            return evolved

        return self  # No evolution for other types in this simple model


class CelestialObject:
    """Factory class for creating specific types of astronomical objects"""

    @staticmethod
    def create_star(name: str, mass: float, temperature: float = None) -> AstroGroundedConcept:
        """Create a star object"""
        # Mass-luminosity relation
        luminosity = mass ** 3.5

        # Mass-radius relation
        radius = mass ** 0.8

        # Mass-temperature relation
        if temperature is None:
            temperature = 5800 * (mass ** 0.5)

        physical = PhysicalGrounding(
            mass=mass,
            radius=radius,
            temperature=temperature,
            luminosity=luminosity,
            composition={'H': 0.7, 'He': 0.28, 'metals': 0.02},
            age=np.random.uniform(0.1, 10),
            metallicity=0.0
        )

        return AstroGroundedConcept(name, 'star', physical=physical)

    @staticmethod
    def create_galaxy(name: str, galaxy_type: str = 'spiral', mass: float = 1e12) -> AstroGroundedConcept:
        """Create a galaxy object"""
        observational = ObservationalGrounding(
            spectra=np.random.randn(1000),
            light_curve=np.random.randn(100),
            position=SkyCoord(np.random.uniform(0, 360), np.random.uniform(-90, 90), unit='deg'),
            redshift=np.random.uniform(0.01, 0.1),
            magnitude={'V': np.random.uniform(8, 15)},
            angular_size=np.random.uniform(1, 10),
            proper_motion=(0.0, 0.0)
        )

        physical = PhysicalGrounding(
            mass=mass / 2e30,  # Convert to solar masses
            radius=30,  # kpc
            temperature=100,  # Average stellar temperature
            luminosity=1e10,
            composition={'H': 0.7, 'He': 0.28, 'metals': 0.02},
            age=10.0,
            metallicity=0.02
        )

        return AstroGroundedConcept(name, 'galaxy', observational, physical)

    @staticmethod
    def create_black_hole(name: str, mass: float) -> AstroGroundedConcept:
        """Create a black hole object"""
        # Schwarzschild radius
        rs = 2.95 * mass  # km

        physical = PhysicalGrounding(
            mass=mass,
            radius=rs / 696340,  # Convert to solar radii
            temperature=0,  # Classical black hole has no temperature
            luminosity=0,
            composition={},
            age=0,
            metallicity=0
        )

        return AstroGroundedConcept(name, 'black_hole', physical=physical)