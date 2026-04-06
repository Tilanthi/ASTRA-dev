"""
Cosmic-Specific Compositional Operations
======================================

Implements composition and transformation operations specialized
for astrophysical concepts and phenomena.

Key Features:
- Cosmic composition (galaxy mergers, binary systems)
- Astronomical transformations (stellar evolution, gravitational effects)
- Celestial comparison based on physical properties
- Cosmological reasoning about structure formation
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from .astro_grounding import AstroGroundedConcept, CelestialObject, ObservationalGrounding, PhysicalGrounding


class CosmicCompositionType(Enum):
    """Types of cosmic composition operations"""
    MERGE = "merge"  # Galaxy mergers, binary systems
    ACCRETE = "accrete"  # Accretion onto black holes
    FORM_SYSTEM = "form_system"  # Planetary systems
    CLUSTER = "cluster"  # Galaxy clusters


class CosmicTransform:
    """Transformation operations for astronomical objects"""

    @staticmethod
    def stellar_evolution(star: AstroGroundedConcept, time_gyr: float) -> AstroGroundedConcept:
        """Evolve a star forward in time"""
        return star.evolve(time_gyr)

    @staticmethod
    def gravitational_lensing(background_object: AstroGroundedConcept,
                           lens_mass: float) -> Dict[str, Any]:
        """Calculate gravitational lensing effect"""
        # Einstein radius
        # θ_E = sqrt(4GM/c² * D_ls/(D_l D_s))
        einstein_radius = 1.5 * np.sqrt(lens_mass / 1e12)  # arcseconds

        return {
            'einstein_radius': einstein_radius,
            'magnification': 2.0,  # Simplified
            'multiple_images': einstein_radius > 1.0
        }

    @staticmethod
    def tidal_disruption(star: AstroGroundedConcept,
                        black_hole: AstroGroundedConcept) -> Dict[str, Any]:
        """Simulate tidal disruption event"""
        # Roche limit
        roche_limit = 2.456 * (black_hole.physical.mass / star.physical.mass) ** (1/3)

        return {
            'disrupted': star.physical.radius < roche_limit,
            'accretion_rate': star.physical.mass / 1e6 if star.physical.radius < roche_limit else 0,
            'luminosity': 1e45 if star.physical.radius < roche_limit else 0  # erg/s
        }

    @staticmethod
    def supern_explosion(star: AstroGroundedConcept) -> AstroGroundedConcept:
        """Create supernova remnant from massive star"""
        if star.physical.mass < 8:
            return star  # Not massive enough

        remnant = CelestialObject.create_black_hole(
            f"{star.name}_remnant",
            star.physical.mass * 0.1  # 10% becomes black hole
        )

        remnant.observational = ObservationalGrounding(
            spectra=np.random.randn(1000) * 10,  # Bright spectrum
            light_curve=np.random.exponential(1, 100) * 1e10,  # Bright light curve
            position=star.observational.position,
            redshift=star.observational.redshift,
            magnitude={'V': -20},  # Very bright
            angular_size=0.1,
            proper_motion=(1000, 1000)  # High velocity
        )

        return remnant

    @staticmethod
    def planetary_accretion(disk: AstroGroundedConcept,
                          planet_mass: float) -> AstroGroundedConcept:
        """Accrete material onto a planet"""
        new_mass = disk.physical.mass + planet_mass

        # Create protoplanet
        protoplanet = CelestialObject.create_star(
            f"protoplanet_{disk.name}",
            new_mass,
            temperature=300  # K
        )
        protoplanet.object_type = 'protoplanet'

        return protoplanet


class CosmicCompose:
    """Composition operations for astronomical objects"""

    @staticmethod
    def merge_galaxies(galaxy1: AstroGroundedConcept,
                      galaxy2: AstroGroundedConcept) -> AstroGroundedConcept:
        """Merge two galaxies"""
        # Combined mass
        total_mass = galaxy1.physical.mass + galaxy2.physical.mass

        # Trigger starburst
        starburst_luminosity = (galaxy1.physical.luminosity + galaxy2.physical.luminosity) * 10

        # Create merged galaxy
        merged = CelestialObject.create_galaxy(
            f"{galaxy1.name}+{galaxy2.name}",
            'elliptical',  # Mergers often create ellipticals
            total_mass
        )

        # Update properties
        merged.physical.luminosity = starburst_luminosity
        merged.physical.age = min(galaxy1.physical.age, galaxy2.physical.age)
        merged.physical.metallicity = (
            galaxy1.physical.metallicity + galaxy2.physical.metallicity
        ) / 2 * 1.2  # Enrichment from starburst

        # Update observational properties
        merged.observational.magnitude['V'] = (
            galaxy1.observational.magnitude['V'] + galaxy2.observational.magnitude['V'] - 2.5
        )  # Brightening from starburst

        merged.composition_history = [
            ('merge', galaxy1.name, galaxy2.name, 'galaxy_merger')
        ]

        return merged

    @staticmethod
    def form_binary_system(star1: AstroGroundedConcept,
                          star2: AstroGroundedConcept) -> AstroGroundedConcept:
        """Form binary star system"""
        # Compute orbital properties
        total_mass = star1.physical.mass + star2.physical.mass
        separation = 1.0  # AU (simplified)

        # Create binary system
        binary = AstroGroundedConcept(
            f"{star1.name}_{star2.name}_binary",
            'binary_system'
        )

        # Binary has combined properties
        binary.physical.mass = total_mass
        binary.physical.luminosity = star1.physical.luminosity + star2.physical.luminosity
        binary.physical.temperature = (
            star1.physical.temperature * star1.physical.luminosity +
            star2.physical.temperature * star2.physical.luminosity
        ) / binary.physical.luminosity

        # Add orbital information
        binary.grounding.linguistic.update({
            'orbital_period': 2 * np.pi * np.sqrt(separation**3 / total_mass),  # years
            'separation': separation,
            'mass_ratio': star1.physical.mass / star2.physical.mass
        })

        binary.composition_history = [
            ('compose', star1.name, star2.name, 'binary_formation')
        ]

        return binary

    @staticmethod
    def create_galaxy_cluster(galaxies: List[AstroGroundedConcept]) -> AstroGroundedConcept:
        """Create galaxy cluster from multiple galaxies"""
        # Compute cluster properties
        total_mass = sum(g.physical.mass for g in galaxies)
        total_luminosity = sum(g.physical.luminosity for g in galaxies)

        # Find center of mass position
        positions = [g.observational.position for g in galaxies]
        center_ra = np.mean([p.ra.deg for p in positions])
        center_dec = np.mean([p.dec.deg for p in positions])

        # Create cluster
        cluster = AstroGroundedConcept(
            f"cluster_{len(galaxies)}_galaxies",
            'galaxy_cluster'
        )

        cluster.physical.mass = total_mass
        cluster.physical.luminosity = total_luminosity
        cluster.physical.radius = 1.0  # Mpc

        # Cluster-specific properties
        cluster.grounding.linguistic.update({
            'virial_radius': 1.5,  # Mpc
            'velocity_dispersion': np.sqrt(total_mass / 1e14) * 1000,  # km/s
            'dark_matter_fraction': 0.85,
            'galaxy_count': len(galaxies)
        })

        cluster.composition_history = [
            ('cluster', ','.join(g.name for g in galaxies), 'galaxy_cluster')
        ]

        return cluster

    @staticmethod
    def accrete_onto_black_hole(black_hole: AstroGroundedConcept,
                               accretion_disk: AstroGroundedConcept) -> AstroGroundedConcept:
        """Accrete material onto black hole"""
        # Eddington-limited accretion
        eddington_rate = 1.3e-8 * black_hole.physical.mass  # M☉/year
        actual_rate = min(accretion_disk.physical.mass / 1e6, eddington_rate)

        # Update black hole mass
        new_mass = black_hole.physical.mass + actual_rate * 1e6

        # Create updated black hole
        updated = CelestialObject.create_black_hole(
            f"{black_hole.name}_grown",
            new_mass
        )

        # Add accretion properties
        updated.grounding.linguistic.update({
            'accretion_rate': actual_rate,
            'luminosity': 0.1 * actual_rate / eddington_rate,  # Eddington ratio
            'jet_power': 0.1 * actual_rate * 3e8  # erg/s
        })

        updated.composition_history = [
            ('accrete', black_hole.name, accretion_disk.name, 'black_hole_accretion')
        ]

        return updated


class AstronomicalCompare:
    """Comparison operations specialized for astronomical objects"""

    @staticmethod
    def hubble_diagram(galaxy1: AstroGroundedConcept,
                      galaxy2: AstroGroundedConcept) -> Dict[str, Any]:
        """Compare galaxies on Hubble diagram"""
        z1 = galaxy1.observational.redshift
        z2 = galaxy2.observational.redshift

        d1 = galaxy1.compute_luminosity_distance()
        d2 = galaxy2.compute_luminosity_distance()

        return {
            'galaxy1': {'redshift': z1, 'distance': d1},
            'galaxy2': {'redshift': z2, 'distance': d2},
            'hubble_flow': abs(z1/d1 - z2/d2),
            'peculiar_velocity': abs(z1/d1 - z2/d2) * 3e5  # km/s
        }

    @staticmethod
    def stellar_classification(star1: AstroGroundedConcept,
                             star2: AstroGroundedConcept) -> Dict[str, Any]:
        """Classify and compare stars"""
        # HR diagram position
        hr1 = (star1.physical.temperature, star1.physical.luminosity)
        hr2 = (star2.physical.temperature, star2.physical.luminosity)

        return {
            'star1': {'temp': star1.physical.temperature, 'lum': star1.physical.luminosity},
            'star2': {'temp': star2.physical.temperature, 'lum': star2.physical.luminosity},
            'hr_distance': np.sqrt((hr1[0]-hr2[0])**2 + (np.log10(hr1[1])-np.log10(hr2[1]))**2),
            'evolution_stage_1': star1.get_evolutionary_stage(),
            'evolution_stage_2': star2.get_evolutionary_stage()
        }

    @staticmethod
    def spectroscopic_comparision(object1: AstroGroundedConcept,
                                object2: AstroGroundedConcept) -> Dict[str, Any]:
        """Compare spectral properties"""
        spec1 = object1.observational.spectra
        spec2 = object2.observational.spectra

        # Calculate spectral correlation
        correlation = np.corrcoef(spec1, spec2)[0, 1]

        # Find key spectral lines
        lines1 = np.where(spec1 > np.mean(spec1) + 2*np.std(spec1))[0]
        lines2 = np.where(spec2 > np.mean(spec2) + 2*np.std(spec2))[0]

        return {
            'spectral_correlation': correlation,
            'similarity': 'high' if correlation > 0.8 else 'medium' if correlation > 0.5 else 'low',
            'common_lines': len(set(lines1) & set(lines2)),
            'unique_lines_1': len(set(lines1) - set(lines2)),
            'unique_lines_2': len(set(lines2) - set(lines1))
        }

    @staticmethod
    def cosmological_evolution(object_z: AstroGroundedConcept,
                              object_local: AstroGroundedConcept) -> Dict[str, Any]:
        """Compare high-redshift object with local counterpart"""
        cosmic_time = 13.8 / (1 + object_z.observational.redshift)  # Gyr

        return {
            'cosmic_time': cosmic_time,
            'lookback_time': 13.8 - cosmic_time,
            'size_evolution': object_z.observational.angular_size / object_local.observational.angular_size,
            'luminosity_evolution': object_z.physical.luminosity / object_local.physical.luminosity,
            'metallicity_evolution': object_z.physical.metallicity / object_local.physical.metallicity
        }