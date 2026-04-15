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
Base domain module interface for STAN-XI-ASTRO

Provides abstract base class and configuration for all domain modules.
Enables plug-and-play domain expansion with hot-swapping capabilities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


@dataclass
class DomainConfig:
    """
    Configuration for domain modules

    Attributes:
        domain_name: Unique identifier for the domain
        version: Domain module version
        dependencies: List of other domains this domain depends on
        keywords: Keywords for automatic domain detection
        task_types: Task types this domain can handle
        enabled: Whether the domain is enabled
        description: Human-readable description
        capabilities: List of specific capabilities provided
    """
    domain_name: str
    version: str
    dependencies: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    task_types: List[str] = field(default_factory=list)
    enabled: bool = True
    description: str = ""
    capabilities: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration"""
        if not self.domain_name:
            raise ValueError("domain_name cannot be empty")
        if not self.version:
            raise ValueError("version cannot be empty")


@dataclass
class DomainQueryResult:
    """
    Result from domain query processing

    Attributes:
        domain_name: Name of domain that processed the query
        answer: Generated answer
        confidence: Confidence in the answer (0-1)
        reasoning_trace: List of reasoning steps
        capabilities_used: Capabilities used in processing
        metadata: Additional metadata
    """
    domain_name: str
    answer: str
    confidence: float
    reasoning_trace: List[str] = field(default_factory=list)
    capabilities_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate result"""
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass
class CrossDomainConnection:
    """
    Represents a connection between two domains

    Attributes:
        source_domain: Source domain name
        target_domain: Target domain name
        connection_type: Type of connection (analogy, shared_concept, etc.)
        strength: Strength of connection (0-1)
        description: Description of the connection
        transferable_knowledge: Knowledge that can be transferred
    """
    source_domain: str
    target_domain: str
    connection_type: str
    strength: float
    description: str = ""
    transferable_knowledge: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate connection"""
        if not 0 <= self.strength <= 1:
            raise ValueError("strength must be between 0 and 1")


class BaseDomainModule(ABC):
    """
    Abstract base class for all domain modules

    All domain modules must inherit from this class and implement
    the required methods. This enables plug-and-play domain expansion.
    """

    def __init__(self, config: Optional[DomainConfig] = None):
        """
        Initialize domain module

        Args:
            config: Domain configuration. If None, uses get_default_config()
        """
        self.config = config or self.get_default_config()
        self._initialized = False

    @abstractmethod
    def get_default_config(self) -> DomainConfig:
        """
        Return default configuration for this domain

        Returns:
            DomainConfig with default values
        """
        pass

    def get_config(self) -> DomainConfig:
        """Return domain configuration"""
        return self.config

    @abstractmethod
    def initialize(self, global_config: Dict[str, Any]) -> None:
        """
        Initialize domain with global configuration

        Args:
            global_config: Global STAN configuration
        """
        self._initialized = True
        logger.info(f"Domain {self.config.domain_name} initialized")

    @abstractmethod
    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """
        Process domain-specific query

        Args:
            query: User query
            context: Additional context (parameters, metadata, etc.)

        Returns:
            DomainQueryResult with answer and metadata
        """
        if not self._initialized:
            raise RuntimeError(f"Domain {self.config.domain_name} not initialized")

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of domain capabilities

        Returns:
            List of capability names
        """
        pass

    def discover_cross_domain_connections(
        self,
        other_domains: List['BaseDomainModule']
    ) -> List[CrossDomainConnection]:
        """
        Discover connections to other domains

        Args:
            other_domains: List of other domain modules

        Returns:
            List of discovered connections
        """
        connections = []

        for other_domain in other_domains:
            if other_domain.config.domain_name == self.config.domain_name:
                continue

            # Look for shared keywords
            shared_keywords = set(self.config.keywords) & set(other_domain.config.keywords)

            # Look for shared capabilities
            shared_capabilities = set(self.config.capabilities) & set(other_domain.config.capabilities)

            # Create connection if significant overlap
            overlap_score = (len(shared_keywords) + len(shared_capabilities)) / max(
                len(self.config.keywords) + len(self.config.capabilities),
                len(other_domain.config.keywords) + len(other_domain.config.capabilities),
                1
            )

            if overlap_score > 0.1:  # 10% overlap threshold
                connection = CrossDomainConnection(
                    source_domain=self.config.domain_name,
                    target_domain=other_domain.config.domain_name,
                    connection_type="shared_concepts",
                    strength=overlap_score,
                    description=f"Shared {len(shared_keywords)} keywords and {len(shared_capabilities)} capabilities",
                    transferable_knowledge=list(shared_keywords | shared_capabilities)
                )
                connections.append(connection)

        return connections

    def can_handle_query(self, query: str) -> float:
        """
        Determine if this domain can handle a query

        Args:
            query: User query

        Returns:
            Confidence score (0-1) indicating how well this domain can handle the query
        """
        query_lower = query.lower()
        keyword_matches = sum(1 for kw in self.config.keywords if kw in query_lower)

        if not self.config.keywords:
            return 0.0

        return keyword_matches / len(self.config.keywords)

    def get_status(self) -> Dict[str, Any]:
        """
        Get domain status information

        Returns:
            Dictionary with status information
        """
        return {
            'domain_name': self.config.domain_name,
            'version': self.config.version,
            'initialized': self._initialized,
            'enabled': self.config.enabled,
            'capabilities': self.get_capabilities(),
            'dependencies': self.config.dependencies
        }

    def __repr__(self) -> str:
        return f"DomainModule({self.config.domain_name}, v{self.config.version})"


class DomainModuleRegistry:
    """
    Registry for domain module classes

    Enables automatic discovery and loading of domain modules.
    """
    _domain_classes: Dict[str, type] = {}

    @classmethod
    def register(cls, domain_class: type) -> None:
        """Register a domain module class"""
        domain_name = domain_class.__name__
        cls._domain_classes[domain_name] = domain_class
        logger.info(f"Registered domain class: {domain_name}")

    @classmethod
    def unregister(cls, domain_class: type) -> None:
        """Unregister a domain module class"""
        domain_name = domain_class.__name__
        if domain_name in cls._domain_classes:
            del cls._domain_classes[domain_name]

    @classmethod
    def get(cls, domain_name: str) -> Optional[type]:
        """Get registered domain class by name"""
        return cls._domain_classes.get(domain_name)

    @classmethod
    def list_domains(cls) -> List[str]:
        """List all registered domain class names"""
        return list(cls._domain_classes.keys())

    @classmethod
    def create(cls, domain_name: str, **kwargs) -> Optional['BaseDomainModule']:
        """Create instance of registered domain class"""
        domain_class = cls.get(domain_name)
        if domain_class:
            return domain_class(**kwargs)
        return None


def register_domain(cls: type) -> type:
    """
    Decorator to register a domain module class

    Usage:
        @register_domain
        class MyDomain(BaseDomainModule):
            pass
    """
    DomainModuleRegistry.register(cls)
    return cls


# Import DomainRegistry from registry module
from .registry import DomainRegistry

# Import new domain modules
from .ism import ISMDomain, create_ism_domain
from .star_formation import StarFormationDomain, create_star_formation_domain

# V47+ New domains
try:
    from .high_energy import HighEnergyDomain, create_high_energy_domain
except ImportError:
    HighEnergyDomain = None
    create_high_energy_domain = None

try:
    from .galactic_archaeology import GalacticArchaeologyDomain, create_galactic_archaeology_domain
except ImportError:
    GalacticArchaeologyDomain = None
    create_galactic_archaeology_domain = None

try:
    from .extragalactic import ExtragalacticDomain, create_extragalactic_domain
except ImportError:
    ExtragalacticDomain = None
    create_extragalactic_domain = None

# Import existing domain modules
try:
    from .exoplanets import ExoplanetDomain
except ImportError:
    ExoplanetDomain = None

try:
    from .gravitational_waves import GravitationalWavesDomain
except ImportError:
    GravitationalWavesDomain = None

try:
    from .cosmology import CosmologyDomain
except ImportError:
    CosmologyDomain = None

try:
    from .solar_system import SolarSystemDomain
except ImportError:
    SolarSystemDomain = None

try:
    from .time_domain import TimeDomainDomain
except ImportError:
    TimeDomainDomain = None

# V80+ New specialist domains (17 new astronomy domains)
try:
    from .radio_extragalactic import RadioExtragalacticDomain, create_radio_extragalactic_domain
except ImportError:
    RadioExtragalacticDomain = None
    create_radio_extragalactic_domain = None

try:
    from .radio_galactic import RadioGalacticDomain, create_radio_galactic_domain
except ImportError:
    RadioGalacticDomain = None
    create_radio_galactic_domain = None

try:
    from .black_holes import BlackHolesDomain, create_black_holes_domain
except ImportError:
    BlackHolesDomain = None
    create_black_holes_domain = None

try:
    from .agn import AGNDomain, create_agn_domain
except ImportError:
    AGNDomain = None
    create_agn_domain = None

try:
    from .galaxy_evolution import GalaxyEvolutionDomain, create_galaxy_evolution_domain
except ImportError:
    GalaxyEvolutionDomain = None
    create_galaxy_evolution_domain = None

try:
    from .cmb import CMBDomain, create_cmb_domain
except ImportError:
    CMBDomain = None
    create_cmb_domain = None

try:
    from .astrochemical_surveys import AstrochemicalSurveysDomain, create_astrochemical_surveys_domain
except ImportError:
    AstrochemicalSurveysDomain = None
    create_astrochemical_surveys_domain = None

try:
    from .molecular_cloud_evolution import MolecularCloudEvolutionDomain, create_molecular_cloud_evolution_domain
except ImportError:
    MolecularCloudEvolutionDomain = None
    create_molecular_cloud_evolution_domain = None

try:
    from .molecular_cloud_collapse import MolecularCloudCollapseDomain, create_molecular_cloud_collapse_domain
except ImportError:
    MolecularCloudCollapseDomain = None
    create_molecular_cloud_collapse_domain = None

try:
    from .molecular_cloud_dynamics import MolecularCloudDynamicsDomain, create_molecular_cloud_dynamics_domain
except ImportError:
    MolecularCloudDynamicsDomain = None
    create_molecular_cloud_dynamics_domain = None

try:
    from .hii_regions import HIIRegionsDomain, create_hii_regions_domain
except ImportError:
    HIIRegionsDomain = None
    create_hii_regions_domain = None

try:
    from .infrared_astronomy import InfraredAstronomyDomain, create_infrared_astronomy_domain
except ImportError:
    InfraredAstronomyDomain = None
    create_infrared_astronomy_domain = None

try:
    from .millimetre_astronomy import MillimetreAstronomyDomain, create_millimetre_astronomy_domain
except ImportError:
    MillimetreAstronomyDomain = None
    create_millimetre_astronomy_domain = None

try:
    from .submillimeter_astronomy import SubmillimeterAstronomyDomain, create_submillimeter_astronomy_domain
except ImportError:
    SubmillimeterAstronomyDomain = None
    create_submillimeter_astronomy_domain = None

try:
    from .farinfrared_astronomy import FarInfraredAstronomyDomain, create_farinfrared_astronomy_domain
except ImportError:
    FarInfraredAstronomyDomain = None
    create_farinfrared_astronomy_domain = None

try:
    from .gravitational_lensing import GravitationalLensingDomain, create_gravitational_lensing_domain
except ImportError:
    GravitationalLensingDomain = None
    create_gravitational_lensing_domain = None

try:
    from .large_scale_structure import LargeScaleStructureDomain, create_large_scale_structure_domain
except ImportError:
    LargeScaleStructureDomain = None
    create_large_scale_structure_domain = None

try:
    from .galactic_structure import GalacticStructureDomain, create_galactic_structure_domain
except ImportError:
    GalacticStructureDomain = None
    create_galactic_structure_domain = None


# Export all public classes
__all__ = [
    'DomainConfig',
    'DomainQueryResult',
    'CrossDomainConnection',
    'BaseDomainModule',
    'DomainModuleRegistry',
    'DomainRegistry',
    'register_domain',
    # ISM and Star Formation (V46)
    'ISMDomain',
    'create_ism_domain',
    'StarFormationDomain',
    'create_star_formation_domain',
    # V47+ New domains
    'HighEnergyDomain',
    'create_high_energy_domain',
    'GalacticArchaeologyDomain',
    'create_galactic_archaeology_domain',
    'ExtragalacticDomain',
    'create_extragalactic_domain',
    # Existing domains
    'ExoplanetDomain',
    'GravitationalWavesDomain',
    'CosmologyDomain',
    'SolarSystemDomain',
    'TimeDomainDomain',
    # V80+ New specialist domains (17 domains)
    'RadioExtragalacticDomain',
    'create_radio_extragalactic_domain',
    'RadioGalacticDomain',
    'create_radio_galactic_domain',
    'BlackHolesDomain',
    'create_black_holes_domain',
    'AGNDomain',
    'create_agn_domain',
    'GalaxyEvolutionDomain',
    'create_galaxy_evolution_domain',
    'CMBDomain',
    'create_cmb_domain',
    'AstrochemicalSurveysDomain',
    'create_astrochemical_surveys_domain',
    'MolecularCloudEvolutionDomain',
    'create_molecular_cloud_evolution_domain',
    'MolecularCloudCollapseDomain',
    'create_molecular_cloud_collapse_domain',
    'MolecularCloudDynamicsDomain',
    'create_molecular_cloud_dynamics_domain',
    'HIIRegionsDomain',
    'create_hii_regions_domain',
    'InfraredAstronomyDomain',
    'create_infrared_astronomy_domain',
    'MillimetreAstronomyDomain',
    'create_millimetre_astronomy_domain',
    'SubmillimeterAstronomyDomain',
    'create_submillimeter_astronomy_domain',
    'FarInfraredAstronomyDomain',
    'create_farinfrared_astronomy_domain',
    'GravitationalLensingDomain',
    'create_gravitational_lensing_domain',
    'LargeScaleStructureDomain',
    'create_large_scale_structure_domain',
    'GalacticStructureDomain',
    'create_galactic_structure_domain',
]


# ============================================================================
# V4.0 EXPANDED DOMAINS (48 New Domains)
# ============================================================================

# Major Contemporary Astrophysics Research Domains (24)
try:
    from .astroparticle import AstroparticlePhysicsDomain, create_astroparticle_domain
except ImportError:
    AstroparticlePhysicsDomain = None
    create_astroparticle_domain = None

try:
    from .gamma_ray import GammaRayAstronomyDomain, create_gamma_ray_domain
except ImportError:
    GammaRayAstronomyDomain = None
    create_gamma_ray_domain = None

try:
    from .xray_binaries import XrayBinariesDomain, create_xray_binaries_domain
except ImportError:
    XrayBinariesDomain = None
    create_xray_binaries_domain = None

try:
    from .gravitational_lensing import GravitationalLensingDomain, create_gravitational_lensing_domain
except ImportError:
    GravitationalLensingDomain = None
    create_gravitational_lensing_domain = None

try:
    from .exoplanet_atmospheres import ExoplanetAtmospheresDomain, create_exoplanet_atmospheres_domain
except ImportError:
    ExoplanetAtmospheresDomain = None
    create_exoplanet_atmospheres_domain = None

try:
    from .planetary_formation import PlanetaryFormationDomain, create_planetary_formation_domain
except ImportError:
    PlanetaryFormationDomain = None
    create_planetary_formation_domain = None

try:
    from .dwarf_galaxies import DwarfGalaxiesDomain, create_dwarf_galaxies_domain
except ImportError:
    DwarfGalaxiesDomain = None
    create_dwarf_galaxies_domain = None

try:
    from .galaxy_clusters import GalaxyClustersDomain, create_galaxy_clusters_domain
except ImportError:
    GalaxyClustersDomain = None
    create_galaxy_clusters_domain = None

try:
    from .intergalactic_medium import IntergalacticMediumDomain, create_intergalactic_medium_domain
except ImportError:
    IntergalacticMediumDomain = None
    create_intergalactic_medium_domain = None

try:
    from .stellar_populations import StellarPopulationsDomain, create_stellar_populations_domain
except ImportError:
    StellarPopulationsDomain = None
    create_stellar_populations_domain = None

try:
    from .compact_binaries import CompactObjectBinariesDomain, create_compact_binaries_domain
except ImportError:
    CompactObjectBinariesDomain = None
    create_compact_binaries_domain = None

try:
    from .supernovae import SupernovaeDomain, create_supernovae_domain
except ImportError:
    SupernovaeDomain = None
    create_supernovae_domain = None

try:
    from .computational_astrophysics import ComputationalAstrophysicsDomain, create_computational_astrophysics_domain
except ImportError:
    ComputationalAstrophysicsDomain = None
    create_computational_astrophysics_domain = None

try:
    from .theoretical_astrophysics import TheoreticalAstrophysicsDomain, create_theoretical_astrophysics_domain
except ImportError:
    TheoreticalAstrophysicsDomain = None
    create_theoretical_astrophysics_domain = None

try:
    from .astrometry import AstrometryDomain, create_astrometry_domain
except ImportError:
    AstrometryDomain = None
    create_astrometry_domain = None

try:
    from .polarimetry import PolarimetryDomain, create_polarimetry_domain
except ImportError:
    PolarimetryDomain = None
    create_polarimetry_domain = None

try:
    from .interferometry import InterferometryDomain, create_interferometry_domain
except ImportError:
    InterferometryDomain = None
    create_interferometry_domain = None

try:
    from .frbs import FastRadioBurstsDomain, create_frbs_domain
except ImportError:
    FastRadioBurstsDomain = None
    create_frbs_domain = None

try:
    from .tidal_disruption import TidalDisruptionEventsDomain, create_tidal_disruption_domain
except ImportError:
    TidalDisruptionEventsDomain = None
    create_tidal_disruption_domain = None

try:
    from .kilonovae import KilonovaeDomain, create_kilonovae_domain
except ImportError:
    KilonovaeDomain = None
    create_kilonovae_domain = None

try:
    from .solar_physics import SolarPhysicsDomain, create_solar_physics_domain
except ImportError:
    SolarPhysicsDomain = None
    create_solar_physics_domain = None

try:
    from .heliospheric_physics import HeliosphericPhysicsDomain, create_heliospheric_physics_domain
except ImportError:
    HeliosphericPhysicsDomain = None
    create_heliospheric_physics_domain = None

try:
    from .dust_grain_physics import DustGrainPhysicsDomain, create_dust_grain_physics_domain
except ImportError:
    DustGrainPhysicsDomain = None
    create_dust_grain_physics_domain = None

try:
    from .prebiotic_chemistry import PrebioticChemistryDomain, create_prebiotic_chemistry_domain
except ImportError:
    PrebioticChemistryDomain = None
    create_prebiotic_chemistry_domain = None

# Foundational Theoretical & Observational Astrophysics (24)
try:
    from .radiative_transfer_theory import RadiativeTransferTheoryDomain, create_radiative_transfer_theory_domain
except ImportError:
    RadiativeTransferTheoryDomain = None
    create_radiative_transfer_theory_domain = None

try:
    from .plasma_physics import PlasmaPhysicsDomain, create_plasma_physics_domain
except ImportError:
    PlasmaPhysicsDomain = None
    create_plasma_physics_domain = None

try:
    from .mhd import MagnetohydrodynamicsDomain, create_mhd_domain
except ImportError:
    MagnetohydrodynamicsDomain = None
    create_mhd_domain = None

try:
    from .general_relativity import GeneralRelativityDomain, create_general_relativity_domain
except ImportError:
    GeneralRelativityDomain = None
    create_general_relativity_domain = None

try:
    from .quantum_applications import QuantumApplicationsDomain, create_quantum_applications_domain
except ImportError:
    QuantumApplicationsDomain = None
    create_quantum_applications_domain = None

try:
    from .stellar_structure import StellarStructureDomain, create_stellar_structure_domain
except ImportError:
    StellarStructureDomain = None
    create_stellar_structure_domain = None

try:
    from .stellar_atmospheres import StellarAtmospheresDomain, create_stellar_atmospheres_domain
except ImportError:
    StellarAtmospheresDomain = None
    create_stellar_atmospheres_domain = None

try:
    from .nuclear_astrophysics import NuclearAstrophysicsDomain, create_nuclear_astrophysics_domain
except ImportError:
    NuclearAstrophysicsDomain = None
    create_nuclear_astrophysics_domain = None

try:
    from .fluid_dynamics import FluidDynamicsDomain, create_fluid_dynamics_domain
except ImportError:
    FluidDynamicsDomain = None
    create_fluid_dynamics_domain = None

try:
    from .shock_physics_extended import ShockPhysicsExtendedDomain, create_shock_physics_extended_domain
except ImportError:
    ShockPhysicsExtendedDomain = None
    create_shock_physics_extended_domain = None

try:
    from .radiative_processes import RadiativeProcessesDomain, create_radiative_processes_domain
except ImportError:
    RadiativeProcessesDomain = None
    create_radiative_processes_domain = None

try:
    from .photoionization import PhotoionizationDomain, create_photoionization_domain
except ImportError:
    PhotoionizationDomain = None
    create_photoionization_domain = None

try:
    from .dust_formation import DustFormationDomain, create_dust_formation_domain
except ImportError:
    DustFormationDomain = None
    create_dust_formation_domain = None

try:
    from .solid_state_astro import SolidStateAstrophysicsDomain, create_solid_state_astro_domain
except ImportError:
    SolidStateAstrophysicsDomain = None
    create_solid_state_astro_domain = None

try:
    from .dynamical_systems import DynamicalSystemsDomain, create_dynamical_systems_domain
except ImportError:
    DynamicalSystemsDomain = None
    create_dynamical_systems_domain = None

try:
    from .orbital_dynamics import OrbitalDynamicsDomain, create_orbital_dynamics_domain
except ImportError:
    OrbitalDynamicsDomain = None
    create_orbital_dynamics_domain = None

try:
    from .accretion_disk_theory import AccretionDiskTheoryDomain, create_accretion_disk_theory_domain
except ImportError:
    AccretionDiskTheoryDomain = None
    create_accretion_disk_theory_domain = None

try:
    from .statistical_mechanics import StatisticalMechanicsDomain, create_statistical_mechanics_domain
except ImportError:
    StatisticalMechanicsDomain = None
    create_statistical_mechanics_domain = None

try:
    from .signal_processing import SignalProcessingDomain, create_signal_processing_domain
except ImportError:
    SignalProcessingDomain = None
    create_signal_processing_domain = None

try:
    from .inverse_problems import InverseProblemsDomain, create_inverse_problems_domain
except ImportError:
    InverseProblemsDomain = None
    create_inverse_problems_domain = None

try:
    from .atomic_physics import AtomicPhysicsDomain, create_atomic_physics_domain
except ImportError:
    AtomicPhysicsDomain = None
    create_atomic_physics_domain = None

try:
    from .molecular_spectroscopy import MolecularSpectroscopyDomain, create_molecular_spectroscopy_domain
except ImportError:
    MolecularSpectroscopyDomain = None
    create_molecular_spectroscopy_domain = None

try:
    from .numerical_methods import NumericalMethodsDomain, create_numerical_methods_domain
except ImportError:
    NumericalMethodsDomain = None
    create_numerical_methods_domain = None

try:
    from .hpc import HPCDomain, create_hpc_domain
except ImportError:
    HPCDomain = None
    create_hpc_domain = None
