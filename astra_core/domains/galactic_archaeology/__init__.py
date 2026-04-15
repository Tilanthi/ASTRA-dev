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
Galactic archaeology domain module for STAN-XI-ASTRO

Covers:
- Stellar populations and evolution
- Galactic chemical evolution
- Stellar kinematics and dynamics
- Milky Way structure and formation
- Stellar streams and substructure
- Galactic archaeology techniques
- Age-metallicity relation
- Stellar migration

This domain analyzes the fossil record of galaxy formation imprinted in
stellar populations, using stars as tracers of the assembly history.

Date: 2025-12-23
Version: 47.0
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Import base domain module
try:
    from .. import BaseDomainModule, DomainConfig, DomainQueryResult
except ImportError:
    class BaseDomainModule:
        pass

    class DomainConfig:
        def __init__(self, **kwargs):
            self.domain_name = kwargs.get('domain_name', '')
            self.version = kwargs.get('version', '1.0.0')
            self.dependencies = kwargs.get('dependencies', [])
            self.keywords = kwargs.get('keywords', [])
            self.task_types = kwargs.get('task_types', [])
            self.enabled = kwargs.get('enabled', True)
            self.description = kwargs.get('description', '')
            self.capabilities = kwargs.get('capabilities', [])

    class DomainQueryResult:
        def __init__(self, **kwargs):
            self.domain_name = kwargs.get('domain_name', '')
            self.answer = kwargs.get('answer', '')
            self.confidence = kwargs.get('confidence', 0.0)
            self.reasoning_trace = kwargs.get('reasoning_trace', [])
            self.capabilities_used = kwargs.get('capabilities_used', [])
            self.metadata = kwargs.get('metadata', {})

logger = logging.getLogger(__name__)

# Physical constants
G = 6.674e-8  # Gravitational constant
MSUN = 1.989e33  # Solar mass (g)
LSUN = 3.828e33  # Solar luminosity (erg/s)
RSUN = 6.957e10  # Solar radius (cm)
PC = 3.086e18  # Parsec (cm)
KPC = 3.086e21  # Kiloparsec (cm)


class GalacticArchaeologyDomain(BaseDomainModule):
    """
    Domain specializing in galactic archaeology and stellar populations

    Handles queries about stellar ages, metallicities, kinematics,
    chemical evolution, Milky Way structure, and stellar streams.
    """

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        """Return default configuration for galactic archaeology domain"""
        return DomainConfig(
            domain_name="galactic_archaeology",
            version="1.0.0",
            dependencies=["astro_physics", "reasoning", "stellar_evolution"],
            keywords=[
                # Stellar populations
                "stellar population", "isochrone", "hr diagram", "main sequence",
                "giant branch", "turnoff", "stellar age", "stellar evolution",
                # Chemical evolution
                "metallicity", "abundance", "alpha elements", "iron peak",
                "s-process", "r-process", "chemical evolution", "enrichment",
                "age metallicity", "metal poor", "metal rich",
                # Kinematics and dynamics
                "kinematics", "velocity dispersion", "rotation curve",
                "orbital parameters", "eccentricity", "inclination",
                "phase space", "action angles", "integrals of motion",
                # Milky Way structure
                "milky way", "galaxy structure", "disk", "bulge", "halo",
                "thick disk", "thin disk", "stellar halo", "galactic center",
                "spiral arms", "bar", "galactic plane",
                # Stellar streams
                "stellar stream", "tidal stream", "dwarf galaxy", "satellite",
                "sagittarius", "gaia", "proper motion", "parallax",
                "radial velocity", "phase mixing",
                # Archaeology techniques
                "archaeology", "fossil record", "tagging", "chemical tagging",
                "dynamics", "chronometry", "nucleocosmochronology",
                # Observational
                "gaia", "sdss", "apogee", "galah", "lamost", "hess",
                "eso", "vlt", "keck", "hubble"
            ],
            task_types=[
                "STELLAR_POPULATION_ANALYSIS",
                "CHEMICAL_EVOLUTION_MODELING",
                "KINEMATICS_ANALYSIS",
                "MILKY_WAY_STRUCTURE",
                "STELLAR_STREAM_ANALYSIS",
                "AGE_DETERMINATION",
                "GALACTIC_FORMATION"
            ],
            description="Galactic archaeology including stellar populations, chemical evolution, Milky Way structure, and stellar streams",
            capabilities=[
                # Stellar populations
                "isochrone_fitting",
                "stellar_age_dating",
                "population_synthesis",
                "initial_mass_function",
                "stellar_population_synthesis",
                # Chemical evolution
                "chemical_evolution_modeling",
                "abundance_analysis",
                "alpha_enhancement",
                "nucleocosmochronology",
                "metallicity_distribution",
                # Kinematics
                "orbital_parameter_calculation",
                "action_angle_computation",
                "integrals_of_motion",
                "velocity_dispersion_analysis",
                "rotation_curve_fitting",
                # Milky Way structure
                "disk_structure_analysis",
                "halo_characterization",
                "bulge_properties",
                "spiral_arm_tracing",
                # Stellar streams
                "stream_identification",
                "tidal_debris_modeling",
                "satellite_galaxy_analysis",
                "phase_mixing_modeling",
                # Chemical tagging
                "chemical_tagging",
                "stellar_groups",
                "common_origin_detection"
            ]
        )

    def get_config(self) -> DomainConfig:
        """Return domain configuration"""
        return self.config

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize domain with global configuration"""
        self._initialized = True
        logger.info(f"Galactic archaeology domain initialized: {self.config.domain_name}")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process galactic archaeology query"""
        query_lower = query.lower()

        # Route to subdomain methods
        if any(kw in query_lower for kw in ['age', 'stellar age', 'dating', 'isochrone']):
            return self._analyze_stellar_ages(query, context)
        elif any(kw in query_lower for kw in ['metallicity', 'abundance', 'chemical', 'metal']):
            return self._analyze_chemical_evolution(query, context)
        elif any(kw in query_lower for kw in ['kinematic', 'velocity', 'orbit', 'dynamics']):
            return self._analyze_kinematics(query, context)
        elif any(kw in query_lower for kw in ['stream', 'tidal', 'satellite', 'sagittarius']):
            return self._analyze_stellar_streams(query, context)
        elif any(kw in query_lower for kw in ['milky way', 'galaxy structure', 'disk', 'halo']):
            return self._analyze_milky_way_structure(query, context)
        elif any(kw in query_lower for kw in ['chemical tagging', 'stellar group', 'cluster']):
            return self._analyze_chemical_tagging(query, context)
        else:
            return self._general_galactic_archaeology(query, context)

    def get_capabilities(self) -> List[str]:
        """Return list of domain capabilities"""
        return self.config.capabilities

    # Subdomain analysis methods

    def _analyze_stellar_ages(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze stellar age determination techniques"""
        answer = (
            "Stellar age determination combines multiple methods:\n\n"
            "1. **Isochrone Fitting**:\n"
            "   - Compare star positions in HR diagram to isochrones\n"
            "   - Requires: effective temperature, luminosity, metallicity\n"
            "   - Precision: 10-30% for main sequence stars\n"
            "   - Models: PARSEC, MIST, Yonsei-Yale, Dartmouth\n\n"
            "2. **Turnoff Age**:\n"
            "   - Age ~ stellar lifetime of turnoff mass\n"
            "   - τ ≈ 10 Gyr (M/M⊙)^(-2.5) for M > 0.7 M⊙\n"
            "   - Most precise for globular clusters\n\n"
            "3. **Nucleocosmochronology**:\n"
            "   - Radioactive decay of Th/U in stars\n"
            "   - Age from abundance ratios: Th/Eu, U/Th\n"
            "   - Precision: ~2-3 Gyr for metal-poor stars\n\n"
            "4. **Gyrochronology**:\n"
            "   - Age from rotation period and color\n"
            "   - P ∝ t^(-1/2) for main sequence stars\n"
            "   - Calibration from clusters\n\n"
            "5. **Asteroseismology**:\n"
            "   - Age from oscillation frequencies (Kepler, TESS)\n"
            "   - Δν ∝ ρ^(1/2), ν_max ∝ g/T_eff^(1/2)\n"
            "   - Precision: ~5-10% for solar-like stars\n\n"
            "Key data: Gaia (luminosity), spectroscopic surveys (T_eff, [Fe/H]), "
            "Kepler/TESS (seismology)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=[
                "Identified stellar age analysis query",
                "Synthesized multiple dating methods"
            ],
            capabilities_used=["isochrone_fitting", "stellar_age_dating"]
        )

    def _analyze_chemical_evolution(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze chemical evolution of galaxies"""
        answer = (
            "Galactic chemical evolution tracks enrichment history:\n\n"
            "1. **Metallicity Scales**:\n"
            "   - [Fe/H] = log10(N_Fe/N_H) - log10(N_Fe/N_H)⊙\n"
            "   - Solar: [Fe/H]⊙ = 0\n"
            "   - Metal-poor halo: [Fe/H] < -2\n"
            "   - Disk: [Fe/H] ≈ -0.5 to +0.3\n\n"
            "2. **α-Elements**:\n"
            "   - O, Mg, Si, S, Ca from core-collapse SNe\n"
            "   - Time scale: ~10^6-10^7 years\n"
            "   - [α/Fe] enhancement in metal-poor stars\n"
            "   - Kink at [Fe/H] ≈ -1 from SN Ia onset\n\n"
            "3. **Evolution Models**:\n"
            "   - Closed-box: dZ/dt = y(1 - Z)SFR\n"
            "   - Infall: Gas accretion onto disk\n"
            "   - Outflow: Galactic fountain, winds\n"
            "   - G-dwarf problem: Need pre-enriched or infall\n\n"
            "4. **Neutron-Capture Elements**:\n"
            "   - s-process: AGB stars (Ba, La, Ce)\n"
            "   - r-process: Neutron star mergers (Eu, Au, U)\n"
            "   - Actinide boost: r-process variations\n\n"
            "5. **Age-Metallicity Relation**:\n"
            "   - Disk: Correlation with scatter\n"
            "   - Halo: Large scatter at fixed age\n"
            "   - Thick disk: Enhanced [α/Fe]\n\n"
            "Key surveys: APOGEE, GALAH, LAMOST, SDSS, Gaia-ESO."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=[
                "Identified chemical evolution query",
                "Covered metallicity, α-elements, and evolution models"
            ],
            capabilities_used=["chemical_evolution_modeling", "abundance_analysis"]
        )

    def _analyze_kinematics(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze stellar kinematics and dynamics"""
        answer = (
            "Stellar kinematics reveal dynamical history:\n\n"
            "1. **Velocity Components**:\n"
            "   - U: Radial velocity (toward Galactic center)\n"
            "   - V: Rotational velocity (in direction of rotation)\n"
            "   - W: Vertical velocity (north of Galactic plane)\n"
            "   - LSR: Local standard of rest correction\n\n"
            "2. **Orbital Parameters**:\n"
            "   - Eccentricity: e = (apo - peri)/(apo + peri)\n"
            "   - Perigalacticon: Minimum distance to center\n"
            "   - Apogalacticon: Maximum distance to center\n"
            "   - Z_max: Maximum height above plane\n\n"
            "3. **Action-Angle Variables**:\n"
            "   - J_R: Radial action (epicyclic motion)\n"
            "   - J_φ: Azimuthal action (angular momentum)\n"
            "   - J_z: Vertical action (vertical oscillation)\n"
            "   - Integrals of motion for axisymmetric potentials\n\n"
            "4. **Stellar Populations**:\n"
            "   - Thin disk: Low eccentricity, low scale height\n"
            "   - Thick disk: Higher e, higher scale height\n"
            "   - Halo: Isotropic, high e, retrograde orbits\n"
            "   - Stream stars: Coherent in action space\n\n"
            "5. **Rotation Curve**:\n"
            "   - V(R) ≈ 220 km/s for R ≈ 8 kpc\n"
            "   - Flat at large R (dark matter halo)\n"
            "   - Oort constants: A, B from shear\n\n"
            "Key data: Gaia DR3 (astrometry), spectroscopic radial velocities."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=[
                "Identified kinematics analysis query",
                "Covered velocity components and orbital parameters"
            ],
            capabilities_used=["orbital_parameter_calculation", "action_angle_computation"]
        )

    def _analyze_stellar_streams(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze stellar streams and tidal debris"""
        answer = (
            "Stellar streams are fossil records of accretion events:\n\n"
            "1. **Stream Formation**:\n"
            "   - Tidal disruption of satellite galaxies\n"
            "   - Strip stars at Lagrange points L1/L2\n"
            "   - Stretch along satellite orbit\n"
            "   - Phase mixing spreads stars in orbit\n\n"
            "2. **Identified Streams**:\n"
            "   - Sagittarius: Prograde, wrapping 3+ times\n"
            "   - Gaia-Enceladus: Radial merger, metal-poor\n"
            "   - Helmi streams: Retrograde, high energy\n"
            "   - Palomar 5, GD-1, Orphan: Faint streams\n\n"
            "3. **Stream Dynamics**:\n"
            "   - Tails: Leading and trailing arms\n"
            "   - Density contrast: δρ/ρ ~ 10-100\n"
            "   - Velocity dispersion: σ_v ~ 1-10 km/s\n"
            "   - Length: 10-100 degrees on sky\n\n"
            "4. **Detection Methods**:\n"
            "   - Overdensity in position (Gaia)\n"
            "   - Clustering in velocity (V_rad, proper motion)\n"
            "   - Metallicity coherence (APOGEE, GALAH)\n"
            "   - Action-space clustering\n\n"
            "5. **Constraints from Streams**:\n"
            "   - Milky Way mass profile\n"
            "   - Dark matter halo shape\n"
            "   - Accretion history\n"
            "   - Satellite galaxy progenitors\n\n"
            "Key data: Gaia DR3, SDSS, DES, Pan-STARRS."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=[
                "Identified stellar stream analysis query",
                "Covered stream formation and detection"
            ],
            capabilities_used=["stream_identification", "tidal_debris_modeling"]
        )

    def _analyze_milky_way_structure(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze Milky Way structure"""
        answer = (
            "Milky Way structure revealed by multi-component approach:\n\n"
            "1. **Disk Components**:\n"
            "   - Thin disk: Scale height ~300 pc, mass ~4×10^10 M⊙\n"
            "   - Thick disk: Scale height ~1 kpc, mass ~10^9-10^10 M⊙\n"
            "   - Stellar disk radius: ~15 kpc (break at ~10 kpc)\n"
            "   - Gas disk: HI extends to ~30 kpc\n\n"
            "2. **Bulge/Bar**:\n"
            "   - Box/peanut bulge from bar buckling\n"
            "   - Bar length: ~5 kpc\n"
            "   - Bulge mass: ~1-2×10^10 M⊙\n"
            "   - Triaxial shape\n\n"
            "3. **Halo**:\n"
            "   - Stellar halo: ~10^9 M⊙, r_eff ~20 kpc\n"
            "   - Dark matter halo: ~10^12 M⊙ within 200 kpc\n"
            "   - NFW profile: ρ ∝ r^(-1)(1 + r/rs)^(-2)\n"
            "   - Scale radius: rs ~ 20 kpc\n\n"
            "4. **Spiral Structure**:\n"
            "   - Number of arms: 2-4 (pitch angle ~12°)\n"
            "   - Pattern speed: ~25 km/s/kpc\n"
            "   - Spiral arm tracers: HII regions, young stars\n\n"
            "5. **Sun's Position**:\n"
            "   - Galactocentric radius: R₀ ≈ 8.2 kpc\n"
            "   - Height above plane: z ≈ 20 pc\n"
            "   - Local rotation velocity: v₀ ≈ 220 km/s\n\n"
            "Key data: Gaia (positions), 2MASS (near-IR structure), HI surveys."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=[
                "Identified Milky Way structure query",
                "Covered all major components"
            ],
            capabilities_used=["disk_structure_analysis", "halo_characterization"]
        )

    def _analyze_chemical_tagging(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze chemical tagging techniques"""
        answer = (
            "Chemical tagging identifies stars born together:\n\n"
            "1. **Principle**:\n"
            "   - Stars born in same cluster share chemistry\n"
            "   - Chemical abundances are preserved after gas dispersal\n"
            "   - Orbital phase mixing obscures common origin\n"
            "   - Chemistry is a robust tag\n\n"
            "2. **Abundance Space**:\n"
            "   - Multi-dimensional: [Fe/H], [α/Fe], [Eu/Fe], etc.\n"
            "   - ~15-20 elements measured for precision tagging\n"
            "   - APOGEE, GALAH, LAMOST provide abundances\n\n"
            "3. **Clustering Algorithms**:\n"
            "   - Dimensionality reduction (PCA, t-SNE, UMAP)\n"
            "   - Density-based clustering (DBSCAN, HDBSCAN)\n"
            "   - Hierarchical clustering\n"
            "   - Machine learning approaches\n\n"
            "4. **Recovered Groups**:\n"
            "   - Moving groups: Local Association, Pleiades\n"
            "   - Dissolved clusters: NGC 6791 remnants\n"
            "   - Accreted groups: Gaia-Enceladus, Sequoia\n\n"
            "5. **Limitations**:\n"
            "   - Abundance precision needed: σ < 0.05 dex\n"
            "   - Confusion from chemical homogeneity\n"
            "   - Incomplete orbital information\n"
            "   - Selection effects in surveys\n\n"
            "Future: WEAVE, 4MOST, MSE will expand chemical tagging."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.85,
            reasoning_trace=[
                "Identified chemical tagging query",
                "Covered principles and techniques"
            ],
            capabilities_used=["chemical_tagging", "stellar_groups"]
        )

    def _general_galactic_archaeology(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """General galactic archaeology analysis"""
        answer = (
            "Galactic archaeology reconstructs Milky Way formation:\n\n"
            "**Key Approaches**:\n"
            "- **Fossil record**: Stars preserve formation conditions\n"
            "- **Chronometric dating**: Age-metallicity relation\n"
            "- **Chemical tagging**: Group stars by origin\n"
            "- **Dynamical tagging**: Group stars by orbits\n"
            "- **Spatial distribution**: Trace substructure\n\n"
            "**Milky Way Assembly**:\n"
            "- Early halo: Accretion of dwarf galaxies\n"
            "- Disk formation: Gas-rich mergers, secular evolution\n"
            "- Recent accretion: Sagittarius, LMC/SMC\n"
            "- Ongoing accretion: Streams and satellites\n\n"
            "**Major Surveys**:\n"
            "- Gaia: Astrometry (positions, velocities)\n"
            "- APOGEE: IR spectroscopy (disk stars)\n"
            "- GALAH: Optical spectroscopy (southern sky)\n"
            "- LAMOST: Low-resolution spectroscopy\n\n"
            "**Key Science**:\n"
            "- Star formation histories\n"
            "- Merger tree reconstruction\n"
            "- Dark matter distribution\n"
            "- Initial mass function variations"
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.82,
            reasoning_trace=["General galactic archaeology overview"],
            capabilities_used=[]
        )


def create_galactic_archaeology_domain() -> GalacticArchaeologyDomain:
    """Factory function for galactic archaeology domain"""
    return GalacticArchaeologyDomain()


# Export public classes
__all__ = [
    'GalacticArchaeologyDomain',
    'create_galactic_archaeology_domain'
]
