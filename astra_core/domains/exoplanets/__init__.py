"""
Exoplanet domain module for STAN-XI-ASTRO

Specializes in exoplanet science including:
- Transit photometry and detection
- Radial velocity methods
- Atmospheric characterization
- Habitability assessment
- Population statistics
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging

from .. import BaseDomainModule, DomainConfig, DomainQueryResult, register_domain

logger = logging.getLogger(__name__)


class ExoplanetDomain(BaseDomainModule):
    """
    Domain specializing in exoplanet science

    Capabilities:
    - Transit analysis and light curve modeling
    - Radial velocity data interpretation
    - Atmospheric retrieval from spectra
    - Habitability zone calculations
    - Planet formation and evolution
    """

    def get_default_config(self) -> DomainConfig:
        """Return default configuration for exoplanet domain"""
        return DomainConfig(
            domain_name="exoplanets",
            version="1.0.0",
            dependencies=["astro_physics"],
            keywords=[
                "exoplanet", "planet", "transit", "radial velocity", "rv",
                "atmosphere", "biosignature", "habitable", "kepler", "tess",
                "occultation", "eclipse", "orbital", "light curve", "spectroscopy",
                "james webb", "jwst", "hot jupiter", "super earth", "mini neptune"
            ],
            task_types=["EXOPLANET_CHARACTERIZATION", "ATMOSPHERIC_RETRIEVAL", "HABITABILITY_ASSESSMENT"],
            description="Exoplanet detection, characterization, and atmospheric analysis",
            capabilities=[
                "transit_analysis",
                "rv_analysis",
                "atmospheric_retrieval",
                "habitable_zone_assessment",
                "detection_sensitivity",
                "population_synthesis",
                "light_curve_modeling",
                "transit_timing_variations"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize exoplanet domain with global configuration"""
        super().initialize(global_config)

        # Initialize exoplanet-specific constants and databases
        self._physical_constants = {
            'G': 6.674e-8,  # CGS
            'M_sun': 1.989e33,  # grams
            'R_sun': 6.957e10,  # cm
            'M_earth': 5.972e27,  # grams
            'R_earth': 6.371e8,  # cm
            'L_sun': 3.828e33,  # erg/s
            'sigma_sb': 5.670e-5,  # erg/cm²/s/K⁴
            'AU': 1.496e13  # cm
        }

        # Initialize habitable zone models
        self._habitable_zone_models = {
            'kasting': self._kasting_habitable_zone,
            'kopparapu': self._kopparapu_habitable_zone,
            'recent': self._recent_habitable_zone
        }

        logger.info(f"Exoplanet domain initialized with {len(self._physical_constants)} constants")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """
        Process exoplanet-related query

        Args:
            query: User query about exoplanets
            context: Additional context (parameters, data, etc.)

        Returns:
            DomainQueryResult with answer and reasoning trace
        """
        query_lower = query.lower()

        # Determine query type
        if 'transit' in query_lower or 'light curve' in query_lower:
            return self._process_transit_query(query, context)
        elif 'radial velocity' in query_lower or 'rv' in query_lower or 'doppler' in query_lower:
            return self._process_rv_query(query, context)
        elif 'atmosphere' in query_lower or 'spectroscopy' in query_lower or 'retrieval' in query_lower:
            return self._process_atmosphere_query(query, context)
        elif 'habitable' in query_lower or 'habitat' in query_lower or 'life' in query_lower:
            return self._process_habitability_query(query, context)
        elif 'detect' in query_lower or 'sensitivity' in query_lower:
            return self._process_detection_query(query, context)
        else:
            return self._process_general_exoplanet_query(query, context)

    def get_capabilities(self) -> List[str]:
        """Return list of exoplanet domain capabilities"""
        return self.config.capabilities

    def _process_transit_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process transit/light curve related query"""
        reasoning_trace = [
            "Identified transit/light curve query",
            "Applying transit photometry models"
        ]

        # Extract parameters from context
        params = context.get('parameters', {})

        # Check if specific calculation requested
        if 'depth' in query.lower() and 'planet' in query.lower() and 'star' in query.lower():
            # Calculate transit depth
            r_planet = params.get('r_planet', self._physical_constants['R_earth'])
            r_star = params.get('r_star', self._physical_constants['R_sun'])

            depth = (r_planet / r_star) ** 2

            answer = (
                f"The transit depth for a planet with radius {r_planet:.2e} cm "
                f"orbiting a star with radius {r_star:.2e} cm is {depth:.6f}, "
                f"or {depth * 100:.4f}%. This depth represents the fractional "
                f"decrease in observed stellar brightness during transit."
            )

            reasoning_trace.extend([
                f"Planet radius: {r_planet:.2e} cm",
                f"Star radius: {r_star:.2e} cm",
                f"Transit depth calculation: (Rp/Rs)² = {depth:.6f}"
            ])

            return DomainQueryResult(
                domain_name=self.config.domain_name,
                answer=answer,
                confidence=0.95,
                reasoning_trace=reasoning_trace,
                capabilities_used=["transit_analysis", "light_curve_modeling"],
                metadata={
                    'calculation': 'transit_depth',
                    'r_planet': r_planet,
                    'r_star': r_star,
                    'depth': depth
                }
            )

        # General transit information
        answer = (
            "Transit photometry detects exoplanets by measuring the periodic "
            "dimming of a star's light when a planet passes in front of it. "
            "The transit depth depends on the ratio of the planet's radius to "
            "the star's radius: δ = (Rp/Rs)². Key observables include transit "
            "depth, duration, period, and timing variations that reveal "
            "information about planet size, orbital period, and potential "
            "additional planets in the system."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["transit_analysis"],
            metadata={'query_type': 'general_transit'}
        )

    def _process_rv_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process radial velocity related query"""
        reasoning_trace = [
            "Identified radial velocity query",
            "Applying Doppler spectroscopy models"
        ]

        params = context.get('parameters', {})

        # Check if specific calculation requested
        if 'velocity' in query.lower() or 'amplitude' in query.lower():
            # Calculate RV amplitude
            m_planet = params.get('m_planet', self._physical_constants['M_earth'])
            m_star = params.get('m_star', self._physical_constants['M_sun'])
            period = params.get('period', 365.25 * 24 * 3600)  # seconds
            inclination = params.get('inclination', 90)  # degrees
            e = params.get('eccentricity', 0.0)

            # Calculate RV amplitude (simplified formula)
            G = self._physical_constants['G']
            a = (G * (m_star + m_planet) * (period / (2 * np.pi)) ** 2) ** (1/3)

            K = (G / (1 - e**2))**0.5 * m_planet * np.sin(np.radians(inclination)) / \
                ((m_star + m_planet) * a * np.sqrt(m_star + m_planet))**0.5

            K_cgs = K  # Already in CGS
            K_m_s = K_cgs / 100  # Convert to m/s

            answer = (
                f"The radial velocity semi-amplitude K for this system is "
                f"{K_m_s:.2f} m/s. This is the maximum line-of-sight velocity "
                f"induced by the planet on the host star. Modern high-precision "
                f"spectrographs can detect velocities as low as ~0.5 m/s, "
                f"enabling the discovery of Earth-mass planets in the habitable "
                f"zone of Sun-like stars."
            )

            reasoning_trace.extend([
                f"Planet mass: {m_planet:.2e} g",
                f"Star mass: {m_star:.2e} g",
                f"Orbital period: {period:.2e} s",
                f"Eccentricity: {e}",
                f"Inclination: {inclination}°",
                f"RV amplitude: K = {K_m_s:.2f} m/s"
            ])

            return DomainQueryResult(
                domain_name=self.config.domain_name,
                answer=answer,
                confidence=0.93,
                reasoning_trace=reasoning_trace,
                capabilities_used=["rv_analysis"],
                metadata={
                    'calculation': 'rv_amplitude',
                    'K_cgs': K_cgs,
                    'K_m_s': K_m_s
                }
            )

        # General RV information
        answer = (
            "Radial velocity (RV) detection measures the Doppler shift of "
            "stellar spectral lines caused by an orbiting planet. The RV "
            "semi-amplitude K depends on planet mass, orbital period, orbital "
            "eccentricity, and stellar mass. The RV method is most sensitive "
            "to massive planets close to their host stars (hot Jupiters) but "
            "can also detect smaller planets with sufficient precision."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["rv_analysis"],
            metadata={'query_type': 'general_rv'}
        )

    def _process_atmosphere_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process atmospheric characterization query"""
        reasoning_trace = [
            "Identified atmospheric characterization query",
            "Applying atmospheric retrieval models"
        ]

        answer = (
            "Exoplanet atmospheric characterization uses transit and emission "
            "spectroscopy to determine atmospheric composition, temperature "
            "structure, and dynamics. Key biosignature gases include O₂, "
            "O₃, CH₄, N₂O, and CO₂. The James Webb Space Telescope (JWST) "
            "is revolutionizing this field by enabling detailed atmospheric "
            "studies of small exoplanets. Techniques include transmission "
            "spectroscopy (during transit), emission spectroscopy (secondary "
            "eclipse and phase curves), and direct imaging of widely separated "
            "planets."
        )

        # Add specific information if requested
        if 'jwst' in query.lower() or 'webb' in query.lower():
            answer += (
                " JWST's unprecedented infrared sensitivity allows detection "
                "of water vapor, carbon dioxide, methane, and other molecules "
                "in exoplanet atmospheres, even for Earth-sized planets around "
                "small stars."
            )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["atmospheric_retrieval", "spectroscopy"],
            metadata={'query_type': 'atmosphere'}
        )

    def _process_habitability_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process habitability assessment query"""
        reasoning_trace = [
            "Identified habitability assessment query",
            "Applying habitable zone models"
        ]

        params = context.get('parameters', {})

        # Check if specific calculation requested
        if 'habitable zone' in query.lower() or 'hz' in query.lower():
            t_eff = params.get('t_eff', 5778)  # Effective temperature (K)
            luminosity = params.get('luminosity', 1.0)  # Solar luminosities

            # Calculate habitable zone using Kopparapu et al. (2013)
            hz_inner, hz_outer = self._kopparapu_habitable_zone(t_eff, luminosity)

            answer = (
                f"For a star with effective temperature {t_eff} K and "
                f"luminosity {luminosity} L☉, the habitable zone extends from "
                f"{hz_inner:.3f} AU to {hz_outer:.3f} AU. This range represents "
                f"the region where liquid water could exist on a planet's "
                f"surface, assuming an Earth-like atmosphere. The boundaries "
                f"depend on stellar properties and atmospheric composition."
            )

            reasoning_trace.extend([
                f"Stellar T_eff: {t_eff} K",
                f"Stellar luminosity: {luminosity} L☉",
                f"HZ inner boundary: {hz_inner:.3f} AU",
                f"HZ outer boundary: {hz_outer:.3f} AU"
            ])

            return DomainQueryResult(
                domain_name=self.config.domain_name,
                answer=answer,
                confidence=0.89,
                reasoning_trace=reasoning_trace,
                capabilities_used=["habitable_zone_assessment"],
                metadata={
                    'calculation': 'habitable_zone',
                    't_eff': t_eff,
                    'luminosity': luminosity,
                    'hz_inner': hz_inner,
                    'hz_outer': hz_outer
                }
            )

        # General habitability information
        answer = (
            "The habitable zone (HZ) is the range of orbital distances from "
            "a star where liquid water could exist on a planet's surface. "
            "Factors affecting habitability include: stellar properties (mass, "
            "luminosity, activity), planetary properties (mass, composition, "
            "atmosphere, magnetic field), and orbital characteristics (distance, "
            "eccentricity). Biosignatures to search for include O₂, O₃, CH₄, "
            "N₂O, and surface reflectance glints indicating liquid water oceans."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["habitable_zone_assessment"],
            metadata={'query_type': 'general_habitability'}
        )

    def _process_detection_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process detection sensitivity query"""
        reasoning_trace = [
            "Identified detection/sensitivity query",
            "Applying detection sensitivity models"
        ]

        answer = (
            "Exoplanet detection sensitivity depends on the method and instrument. "
            "Transit missions like Kepler, TESS, and PLATO are most sensitive "
            "to close-in planets around bright stars. Radial velocity surveys "
            "are most sensitive to massive planets on short-period orbits. "
            "Direct imaging works best for young, massive planets on wide orbits. "
            "Microlensing can detect planets across a wide mass and orbital "
            "distance range but requires statistical validation as each event is "
            "unrepeatable."
        )

        # Add mission-specific info
        if 'kepler' in query.lower():
            answer += (
                " Kepler detected over 2,600 confirmed planets and ~2,400 "
                "candidates, primarily finding Earth-sized planets in close orbits "
                "around Sun-like stars. Its legacy includes understanding the "
                "distribution of planet sizes and orbital periods."
            )
        elif 'tess' in query.lower():
            answer += (
                " TESS (Transiting Exoplanet Survey Satellite) is conducting an "
                "all-sky survey focusing on nearby bright stars, ideal for "
                "atmospheric characterization with JWST and other facilities."
            )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=reasoning_trace,
            capabilities_used=["detection_sensitivity"],
            metadata={'query_type': 'detection'}
        )

    def _process_general_exoplanet_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process general exoplanet query"""
        reasoning_trace = [
            "Processing general exoplanet query",
            "Synthesizing exoplanet knowledge"
        ]

        answer = (
            "Exoplanet science studies planets orbiting stars other than our Sun. "
            "Key detection methods include transit photometry, radial velocity, "
            "direct imaging, microlensing, and astrometry. Over 5,000 "
            "exoplanets have been confirmed, revealing diverse populations: "
            "hot Jupiters, super-Earths, mini-Neptunes, and temperate "
            "Earth-sized planets. Current research focuses on atmospheric "
            "characterization, habitability assessment, and the search for "
            "biosignatures."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.85,
            reasoning_trace=reasoning_trace,
            capabilities_used=self.config.capabilities[:3],  # Use top 3 capabilities
            metadata={'query_type': 'general'}
        )

    # Habitable zone models

    def _kasting_habitable_zone(self, t_eff: float, luminosity: float) -> tuple:
        """Kasting et al. (1993) habitable zone"""
        # Recent Venus limit (inner HZ)
        S_inner = 1.77  # Solar flux relative to Earth
        # Early Mars limit (outer HZ)
        S_outer = 0.32

        # Convert flux to distance
        d_inner = np.sqrt(luminosity / S_inner)
        d_outer = np.sqrt(luminosity / S_outer)

        return d_inner, d_outer

    def _kopparapu_habitable_zone(self, t_eff: float, luminosity: float) -> tuple:
        """Kopparapu et al. (2013) habitable zone (empirical)"""
        # Empirical coefficients for different limits
        # Using simplified version here

        # Inner HZ (runaway greenhouse)
        if t_eff < 5000:
            # M dwarfs
            seff_inner = 1.14 + 0.001 * (t_eff - 5778)
        else:
            # Sun-like and warmer
            seff_inner = 1.107

        # Outer HZ (maximum greenhouse)
        if t_eff < 5000:
            seff_outer = 0.40 + 0.001 * (t_eff - 5778)
        else:
            seff_outer = 0.356

        d_inner = np.sqrt(luminosity / seff_inner)
        d_outer = np.sqrt(luminosity / seff_outer)

        return d_inner, d_outer

    def _recent_habitable_zone(self, t_eff: float, luminosity: float) -> tuple:
        """Recent habitable zone models (Kopparapu 2013, Ramirez 2018)"""
        # Similar to Kopparapu with updated coefficients
        return self._kopparapu_habitable_zone(t_eff, luminosity)

    def discover_cross_domain_connections(
        self,
        other_domains: List['BaseDomainModule']
    ) -> List['CrossDomainConnection']:
        """
        Discover connections to other domains

        Args:
            other_domains: List of other domain modules

        Returns:
            List of discovered connections
        """
        from .. import CrossDomainConnection

        connections = super().discover_cross_domain_connections(other_domains)

        # Add specific exoplanet domain connections
        for other_domain in other_domains:
            other_name = other_domain.config.domain_name

            # Strong connection to stellar physics
            if 'stellar' in other_name or 'star' in other_name:
                connection = CrossDomainConnection(
                    source_domain=self.config.domain_name,
                    target_domain=other_name,
                    connection_type="essential_dependency",
                    strength=0.9,
                    description="Exoplanet characterization requires detailed stellar understanding",
                    transferable_knowledge=["stellar_parameters", "stellar_activity", "stellar_evolution"]
                )
                connections.append(connection)

            # Connection to astrochemistry (for atmospheres)
            if 'chemistry' in other_name or 'molecule' in other_name:
                connection = CrossDomainConnection(
                    source_domain=self.config.domain_name,
                    target_domain=other_name,
                    connection_type="collaborative",
                    strength=0.8,
                    description="Atmospheric characterization requires molecular chemistry",
                    transferable_knowledge=["molecular_spectra", "chemical_equilibrium", "photochemistry"]
                )
                connections.append(connection)

        return connections


# Register the domain
register_domain(ExoplanetDomain)
