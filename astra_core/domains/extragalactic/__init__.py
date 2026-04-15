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
Extragalactic astrophysics domain module for STAN-XI-ASTRO

Covers:
- Galaxy evolution and populations
- Cosmology and large-scale structure
- Galaxy clusters and groups
- Intergalactic medium
- Dark matter and dark energy
- Galaxy formation simulations
- Reionization and first galaxies
- High-redshift universe

This domain analyzes galaxies beyond the Milky Way and the
large-scale structure and evolution of the universe.

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
C = 2.998e10  # Speed of light (cm/s)
G = 6.674e-8  # Gravitational constant
MSUN = 1.989e33  # Solar mass (g)
PC = 3.086e18  # Parsec (cm)
MPC = 3.086e24  # Megaparsec (cm)
H0_DEFAULT = 70.0  # Hubble constant (km/s/Mpc)


class ExtragalacticDomain(BaseDomainModule):
    """
    Domain specializing in extragalactic astrophysics

    Handles queries about galaxies, cosmology, large-scale structure,
    galaxy clusters, dark matter, dark energy, and high-redshift universe.
    """

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        """Return default configuration for extragalactic domain"""
        return DomainConfig(
            domain_name="extragalactic",
            version="1.0.0",
            dependencies=["astro_physics", "reasoning", "cosmology"],
            keywords=[
                # Galaxy properties
                "galaxy", "elliptical", "spiral", "irregular", "dwarf",
                "galaxy merger", "interacting galaxy", "starburst",
                "luminosity function", "mass function", "scaling relation",
                "tidal force", "galaxy cluster", "galaxy group",
                # Cosmology
                "cosmology", "expansion", "hubble", "redshift", "big bang",
                "inflation", "dark matter", "dark energy", "cosmological constant",
                " cmb", "cosmic microwave", "large scale structure",
                # Galaxy formation
                "galaxy formation", "hierarchical assembly", "merger tree",
                "reionization", "first stars", "first galaxies", "high redshift",
                "early universe", "primordial", "population iii",
                # Large-scale structure
                "filament", "void", "cosmic web", "supercluster", "wall",
                "clustering", "correlation function", "power spectrum",
                "baryon acoustic oscillation", "bao",
                # IGM and CGM
                "intergalactic medium", "igm", "circumgalactic", "cgm",
                "lyman alpha", "forest", "absorption", "quasar",
                # Dark matter
                "dark matter halo", "nfw profile", "subhalo", "halo mass",
                "weak lensing", "strong lensing", "gravitational lens",
                # Observational
                "hst", "jwst", "vlt", "alma", "ske", "vla", "ska",
                "des", "lsst", "euclid", "roman", "planck", "wmap"
            ],
            task_types=[
                "GALAXY_EVOLUTION",
                "COSMOLOGY",
                "LARGE_SCALE_STRUCTURE",
                "GALAXY_CLUSTER_ANALYSIS",
                "HIGH_REDSHIFT",
                "REIONIZATION",
                "DARK_MATTER_ANALYSIS"
            ],
            description="Extragalactic astrophysics including galaxy evolution, cosmology, large-scale structure, and high-redshift universe",
            capabilities=[
                # Galaxy evolution
                "galaxy_population_modeling",
                "merger_tree_construction",
                "stellar_population_synthesis",
                "luminosity_function_fitting",
                "scaling_relation_analysis",
                # Cosmology
                "expansion_history_modeling",
                "cosmological_parameter_estimation",
                "cmb_analysis",
                "distance_ladder",
                # Large-scale structure
                "correlation_function_analysis",
                "power_spectrum_estimation",
                "bao_detection",
                "void_identification",
                # Galaxy clusters
                "cluster_mass_estimation",
                "sunyaev_zeldovich_effect",
                "xray_cluster_analysis",
                "lensing_mass_mapping",
                # High-redshift
                "lyman_alpha_forest_analysis",
                "reionization_history",
                "high_z_galaxy_detection",
                "first_star_modeling"
            ]
        )

    def get_config(self) -> DomainConfig:
        """Return domain configuration"""
        return self.config

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize domain with global configuration"""
        self._initialized = True
        logger.info(f"Extragalactic domain initialized: {self.config.domain_name}")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process extragalactic astrophysics query"""
        query_lower = query.lower()

        # Route to subdomain methods
        if any(kw in query_lower for kw in ['galaxy evolution', 'galaxy formation', 'merger']):
            return self._analyze_galaxy_evolution(query, context)
        elif any(kw in query_lower for kw in ['cosmology', 'expansion', 'hubble', 'cmb']):
            return self._analyze_cosmology(query, context)
        elif any(kw in query_lower for kw in ['cluster', 'large scale', 'cosmic web']):
            return self._analyze_large_scale_structure(query, context)
        elif any(kw in query_lower for kw in ['redshift', 'high z', 'reionization', 'first']):
            return self._analyze_high_redshift(query, context)
        elif any(kw in query_lower for kw in ['dark matter', 'lensing', 'halo']):
            return self._analyze_dark_matter(query, context)
        elif any(kw in query_lower for kw in ['igm', 'intergalactic', 'lyman alpha']):
            return self._analyze_igm(query, context)
        else:
            return self._general_extragalactic(query, context)

    def get_capabilities(self) -> List[str]:
        """Return list of domain capabilities"""
        return self.config.capabilities

    # Subdomain analysis methods

    def _analyze_galaxy_evolution(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze galaxy evolution processes"""
        answer = (
            "Galaxy evolution is governed by both internal and external processes:\n\n"
            "1. **Internal Processes**:\n"
            "   - Star formation: Converts gas to stars\n"
            "   - Feedback: Supernovae and AGN regulate star formation\n"
            "   - Secular evolution: Slow, internal changes\n"
            "   - Morphological transformation: Late-type to early-type\n\n"
            "2. **External Processes**:\n"
            "   - Mergers: Major (1:3-1:10) and minor (>1:10)\n"
            "   - Interactions: Tidal tails, bridges, triggers\n"
            "   - Accretion: Consumption of satellites\n"
            "   - Ram pressure: Gas stripping in clusters\n\n"
            "3. **Galaxy Types**:\n"
            "   - Ellipticals: Little gas, old stars, supported by velocity dispersion\n"
            "   - Spirals: Gas-rich, ongoing star formation, disk+bulge\n"
            "   - Irregulars: Often disturbed, gas-rich, star-forming\n"
            "   - Dwarfs: Most numerous, dark matter dominated\n\n"
            "4. **Scaling Relations**:\n"
            "   - Tully-Fisher: L ∝ v_max^4 (spirals)\n"
            "   - Fundamental plane: R_e ∝ σ^(-1.24)I^(-0.82) (ellipticals)\n"
            "   - Size-luminosity: R_e ∝ L^0.25\n\n"
            "5. **Observational Probes**:\n"
            "   - Deep fields: Lookback to z > 6\n"
            "   - Spectroscopic surveys: Star formation histories\n"
            "   - Integral field units: Spatially resolved kinematics\n\n"
            "Key facilities: HST, JWST, ALMA, VLT, Keck, Subaru."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=[
                "Identified galaxy evolution query",
                "Covered internal/external processes and scaling relations"
            ],
            capabilities_used=["galaxy_population_modeling", "scaling_relation_analysis"]
        )

    def _analyze_cosmology(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze cosmological parameters and models"""
        answer = (
            "Modern cosmology is described by the ΛCDM model:\n\n"
            "1. **Cosmological Parameters**:\n"
            "   - H₀ = 67.4 ± 0.5 km/s/Mpc (Planck 2018)\n"
            "   - Ω_m = 0.315 (matter density)\n"
            "   - Ω_Λ = 0.685 (dark energy density)\n"
            "   - Ω_b = 0.049 (baryon density)\n"
            "   - n_s = 0.965 (scalar spectral index)\n"
            "   - σ₈ = 0.811 (matter fluctuation amplitude)\n\n"
            "2. **Expansion History**:\n"
            "   - Scale factor: a(t) = 1/(1+z)\n"
            "   - Friedmann equation: H² = H₀²[Ω_m(1+z)³ + Ω_Λ]\n"
            "   - Transition: a ~ 0.7 (z ~ 0.4) from decelerated to accelerated\n"
            "   - Cosmic acceleration: Confirmed by SNe Ia\n\n"
            "3. **CMB Measurements**:\n"
            "   - Planck: Anisotropy power spectrum\n"
            "   - Acoustic peaks: Baryon and DM effects\n"
            "   - Polarization: E-mode and B-mode\n"
            "   - Reionization bump: Optical depth τ ≈ 0.054\n\n"
            "4. **Distance Ladder**:\n"
            "   - Geometric distances: Masers, eclipsing binaries\n"
            "   - SNe Ia: Standardizable candles\n"
            "   - BAO: Standard rulers\n"
            "   - H₀ tension: Local vs. CMB (4-5 σ discrepancy)\n\n"
            "5. **Inflation**:\n"
            "   - Quantum fluctuations seeded structure\n"
            "   - Nearly scale-invariant spectrum\n"
            "   - Flatness: Ω_total = 1.00 ± 0.02\n"
            "   - Primordial non-gaussianity: f_NL < 1\n\n"
            "Key experiments: Planck, WMAP, ACTPol, SPT, DES."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=[
                "Identified cosmology query",
                "Provided ΛCDM parameters and expansion history"
            ],
            capabilities_used=["expansion_history_modeling", "cosmological_parameter_estimation"]
        )

    def _analyze_large_scale_structure(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze large-scale structure of the universe"""
        answer = (
            "Large-scale structure forms via gravitational instability:\n\n"
            "1. **Cosmic Web Components**:\n"
            "   - Voids: ~80% of volume, density δ < -0.8\n"
            "   - Sheets: Pancake structures, walls\n"
            "   - Filaments: Thread-like, connect clusters\n"
            "   - Clusters: Nodes in web, highest density\n\n"
            "2. **Power Spectrum**:\n"
            "   - P(k) ∝ k^n_s T²(k) (primordial × transfer)\n"
            "   - Peak at k_eq (matter-radiation equality)\n"
            "   - BAO wiggles: Sound horizon scale\n"
            "   - Redshift space distortions: fσ₈ measurement\n\n"
            "3. **Correlation Functions**:\n"
            "   - 2PCF: ξ(r) measures clustering\n"
            "   - 3PCF: ξ(r₁, r₂, r₃) breaks degeneracies\n"
            "   - Projected: w_p(r_p) integrates along line of sight\n"
            "   - Multipole expansion: monopole, quadrupole, hexapole\n\n"
            "4. **Galaxy Clusters**:\n"
            "   - Mass range: 10^13-10^15 M⊙\n"
            "   - Intracluster medium: T ~ 10^7-10^8 K\n"
            "   - SZ effect: CMB distortion\n"
            "   - Lensing: Mass reconstruction\n\n"
            "5. **Baryon Acoustic Oscillations**:\n"
            "   - Sound horizon: r_s ≈ 150 Mpc\n"
            "   - Standard ruler for distance\n"
            "   - Measurements: 6dF, SDSS, BOSS, eBOSS\n\n"
            "Key surveys: SDSS BOSS, DES, LSST, Euclid, SPHEREx."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=[
                "Identified large-scale structure query",
                "Covered cosmic web and clustering statistics"
            ],
            capabilities_used=["correlation_function_analysis", "power_spectrum_estimation"]
        )

    def _analyze_high_redshift(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze high-redshift universe and reionization"""
        answer = (
            "The high-redshift universe probes early galaxy formation:\n\n"
            "1. **Reionization**:\n"
            "   - Redshift range: z ≈ 6-20\n"
            "   - Sources: First stars, early galaxies, quasars\n"
            "   - Duration: Δz ≈ 6 (fast process)\n"
            "   - Optical depth: τ ≈ 0.054 (Planck)\n\n"
            "2. **First Stars (Population III)**:\n"
            "   - Formation: z ≈ 20-30\n"
            "   - Mass: 10-1000 M⊙ (no metals)\n"
            "   - Lifetime: ~2-3 Myr (very massive)\n"
            "   - Signature: Pair-instability SNe\n\n"
            "3. **First Galaxies**:\n"
            "   - Detected: Lyman-break galaxies, dropouts\n"
            "   - GN-z11: z = 11.09 (spectroscopically confirmed)\n"
            "   - JADES-GS-z14-0: z ≈ 14 (candidate)\n"
            "   - Properties: Low mass, compact, star-forming\n\n"
            "4. **Lyman Alpha Forest**:\n"
            "   - IGM absorption: Damped Lyα systems\n"
            "   - IGM temperature: T_IGM ∝ (1+z)²\n"
            "   - Metallicity evolution: [Z/H] → 0 at high-z\n"
            "   - Reionization: Damping tail at z > 6\n\n"
            "5. **21-cm Cosmology**:\n"
            "   - Global signal: EDGES detection at z ≈ 17\n"
            "   - Tomography: Mapping reionization\n"
            "   - Experiments: LOFAR, MWA, HERA, SKA\n\n"
            "Key facilities: JWST (NIRCam, NIRSpec), ALMA, VLT/MUSE, Keck/DEIMOS."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=[
                "Identified high-redshift query",
                "Covered reionization and first galaxies"
            ],
            capabilities_used=["reionization_history", "high_z_galaxy_detection"]
        )

    def _analyze_dark_matter(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze dark matter and gravitational lensing"""
        answer = (
            "Dark matter evidence comes from multiple independent probes:\n\n"
            "1. **Observational Evidence**:\n"
            "   - Galaxy rotation curves: Flat v(R) at large R\n"
            "   - Galaxy clusters: Velocity dispersion > luminous mass\n"
            "   - Gravitational lensing: Mass maps of clusters\n"
            "   - CMB anisotropies: Ω_m ≈ 0.27 (mostly DM)\n"
            "   - Large-scale structure: Growth requires DM\n\n"
            "2. **Dark Matter Halos**:\n"
            "   - NFW profile: ρ(r) ∝ r^(-1)(r + r_s)^(-2)\n"
            "   - Concentration: c ≈ 10 (virial radius/scale radius)\n"
            "   - Mass function: Sheth-Tormen (abundance)\n"
            "   - Subhalos: Abundance mismatch problem\n\n"
            "3. **Gravitational Lensing**:\n"
            "   - Strong lensing: Multiple images, arcs, Einstein rings\n"
            "   - Weak lensing: Shear field, convergence maps\n"
            "   - Cosmic shear: Correlated ellipticities\n"
            "   - Flexion: Higher-order distortion\n\n"
            "4. **Dark Matter Candidates**:\n"
            "   - WIMPs: Weakly Interacting Massive Particles\n"
            "   - Axions: Light bosons from QCD\n"
            "   - Primordial black holes: M ~ 10-100 M⊙\n"
            "   - Sterile neutrinos: Right-handed neutrinos\n\n"
            "5. **Detection Efforts**:\n"
            "   - Direct detection: LUX, XENON, PandaX\n"
            "   - Indirect detection: Fermi-LAT, AMS-02\n"
            "   - Collider production: LHC (missing energy)\n"
            "   - No confirmed detection yet\n\n"
            "Key experiments: DES, HSC, KiDS, LSST (upcoming)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=[
                "Identified dark matter query",
                "Covered evidence, halos, and detection efforts"
            ],
            capabilities_used=["cluster_mass_estimation", "lensing_mass_mapping"]
        )

    def _analyze_igm(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze intergalactic medium"""
        answer = (
            "The IGM fills the space between galaxies:\n\n"
            "1. **IGM Phases**:\n"
            "   - Virialized: T < 10^5 K (photoionized)\n"
            "   - Warm-hot: T ≈ 10^5-10^7 K (shock-heated)\n"
            "   - Clumpy: WHIM (warm-hot intergalactic medium)\n"
            "   - Most baryons (~50%) in WHIM\n\n"
            "2. **Lyman Alpha Forest**:\n"
            "   - Absorption lines in quasar spectra\n"
            "   - Column density: N_HI ≈ 10^12-10^17 cm^-2\n"
            "   - Probes: IGM density, temperature, velocity\n"
            "   - BAO peak: Sound horizon imprint\n\n"
            "3. **Metal Enrichment**:\n"
            "   - IGM metallicity: Z/Z_⊙ ≈ 10^-2 to 10^-4\n"
            "   - Enrichment: Winds from galaxies\n"
            "   - Inhomogeneous: Metals in bubbles\n\n"
            "4. **Damped Lyman Alpha Systems**:\n"
            "   - N_HI > 10^20 cm^-2 (neutral gas)\n"
            "   - Progenitors: Galactic disks, dwarfs\n"
            "   - Chemistry: Depletions, abundance patterns\n\n"
            "5. **Proximity Effect**:\n"
            "   - UV background attenuation near quasars\n"
            "   - He II reionization: z ≈ 3-4\n\n"
            "Key facilities: VLT/UVES, Keck/HIRES, HST/COS."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.84,
            reasoning_trace=[
                "Identified IGM query",
                "Covered IGM phases and Lyman alpha forest"
            ],
            capabilities_used=["lyman_alpha_forest_analysis"]
        )

    def _general_extragalactic(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """General extragalactic astrophysics analysis"""
        answer = (
            "Extragalactic astrophysics studies the universe beyond the Milky Way:\n\n"
            "**Galaxies**:\n"
            "- Types: Ellipticals, spirals, irregulars, dwarfs\n"
            "- Properties: Mass, size, luminosity, morphology\n"
            "- Evolution: Mergers, star formation, quenching\n"
            "- Environment: Field, groups, clusters, voids\n\n"
            "**Cosmology**:\n"
            "- ΛCDM model: Dark matter + dark energy\n"
            "- Expansion: Accelerating since z ≈ 0.7\n"
            "- CMB: Primordial fluctuations\n"
            "- Large-scale structure: Cosmic web\n\n"
            "**High-Redshift**:\n"
            "- First galaxies: z > 10\n"
            "- Reionization: z ≈ 6-20\n"
            "- Formation: Hierarchical assembly\n\n"
            "**Observations**:\n"
            "- Imaging: HST, JWST, Subaru, VISTA\n"
            "- Spectroscopy: VLT, Keck, Gemini\n"
            "- Surveys: SDSS, DES, LSST (upcoming)\n"
            "- Facilities: ALMA, VLA, SKA (upcoming)"
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.83,
            reasoning_trace=["General extragalactic overview"],
            capabilities_used=[]
        )


def create_extragalactic_domain() -> ExtragalacticDomain:
    """Factory function for extragalactic domain"""
    return ExtragalacticDomain()


# Export public classes
__all__ = [
    'ExtragalacticDomain',
    'create_extragalactic_domain'
]
