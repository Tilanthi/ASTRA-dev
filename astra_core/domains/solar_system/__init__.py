"""
Solar System domain module for STAN-XI-ASTRO

Specializes in solar system science including:
- Planetary science
- Small bodies (asteroids, comets, KBOs)
- Planetary atmospheres and surfaces
- Space mission data analysis
"""

import numpy as np
from typing import Dict, List, Any
import logging

from .. import BaseDomainModule, DomainConfig, DomainQueryResult, register_domain, CrossDomainConnection

logger = logging.getLogger(__name__)


class SolarSystemDomain(BaseDomainModule):
    """Domain specializing in solar system science"""

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="solar_system",
            version="1.0.0",
            dependencies=["astro_physics"],
            keywords=[
                "solar system", "planet", "mercury", "venus", "earth", "mars",
                "jupiter", "saturn", "uranus", "neptune", "asteroid", "comet",
                "kbo", "kuiper", "oort", "meteorite", "planetary", "moon",
                "satellite", "ring", "atmosphere", "surface", "geology"
            ],
            task_types=["PLANETARY_SCIENCE", "SMALL_BODY_ANALYSIS", "MISSION_DATA"],
            description="Solar system planets, small bodies, and space missions",
            capabilities=[
                "planetary_science",
                "atmospheric_modeling",
                "surface_analysis",
                "small_body_dynamics",
                "mission_data_analysis",
                "cometary_activity",
                "asteroid_characterization"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize solar system domain"""
        super().initialize(global_config)

        # Solar system parameters
        self._planets = {
            'Mercury': {'a': 0.387, 'e': 0.205, 'R': 0.38, 'M': 0.055},
            'Venus': {'a': 0.723, 'e': 0.007, 'R': 0.95, 'M': 0.815},
            'Earth': {'a': 1.000, 'e': 0.017, 'R': 1.00, 'M': 1.000},
            'Mars': {'a': 1.524, 'e': 0.094, 'R': 0.53, 'M': 0.107},
            'Jupiter': {'a': 5.203, 'e': 0.049, 'R': 11.2, 'M': 317.8},
            'Saturn': {'a': 9.537, 'e': 0.057, 'R': 9.45, 'M': 95.2},
            'Uranus': {'a': 19.191, 'e': 0.046, 'R': 4.00, 'M': 14.5},
            'Neptune': {'a': 30.069, 'e': 0.011, 'R': 3.88, 'M': 17.1},
        }

        logger.info("Solar system domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process solar system query"""
        query_lower = query.lower()

        if any(planet in query_lower for planet in ['mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune']):
            return self._process_planetary_query(query, context)
        elif 'asteroid' in query_lower or 'comet' in query_lower:
            return self._process_small_body_query(query, context)
        elif 'mission' in query_lower or 'spacecraft' in query_lower:
            return self._process_mission_query(query, context)
        else:
            return self._process_general_solar_system_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_planetary_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process planet-specific query"""
        reasoning_trace = ["Processing planetary query"]

        answer = (
            "Solar system planets show diverse characteristics: terrestrial "
            "planets (Mercury, Venus, Earth, Mars) with solid surfaces and "
            "thin/no atmospheres, and gas/ice giants (Jupiter, Saturn, Uranus, "
            "Neptune) with thick atmospheres and ring systems. Study methods include "
            "spacecraft missions (orbiters, landers, rovers), ground-based "
            "observations, and laboratory analysis of meteorites."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["planetary_science", "atmospheric_modeling"]
        )

    def _process_small_body_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process small body (asteroid/comet) query"""
        reasoning_trace = ["Processing small body query"]

        answer = (
            "Small bodies include asteroids (main belt, Trojans, NEOs) and comets "
            "(Kuiper belt, Oort cloud). Asteroids are rocky/metallic remnants of "
            "planet formation; comets are icy bodies from the outer solar system "
            "that display cometary activity (coma, tails) when near the Sun. "
            "They provide clues to early solar system conditions and delivery of "
            "water/organics to Earth."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=reasoning_trace,
            capabilities_used=["small_body_dynamics", "cometary_activity"]
        )

    def _process_mission_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process space mission query"""
        reasoning_trace = ["Processing mission data query"]

        answer = (
            "Solar system missions have transformed our understanding: "
            "MESSENGER (Mercury), Venus Express, Mars rovers (Curiosity, Perseverance), "
            "Juno (Jupiter), Cassini (Saturn), New Horizons (Pluto), and upcoming "
            "Europa Clipper and JUICE (icy moons). These missions provide in situ "
            "measurements of atmospheric composition, surface geology, magnetic fields, "
            "and interior structure."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["mission_data_analysis"]
        )

    def _process_general_solar_system_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process general solar system query"""
        reasoning_trace = ["Processing general solar system query"]

        answer = (
            "The solar system comprises the Sun, 8 planets, 5 dwarf planets, "
            "moons, asteroids, comets, and dust. Formed ~4.6 Gyr ago from a "
            "molecular cloud collapse. Key features: terrestrial inner planets, "
            "gas giant outer planets, asteroid belt between Mars and Jupiter, "
            "Kuiper belt beyond Neptune, and Oort cloud of comets extending "
            "to ~100,000 AU."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.85,
            reasoning_trace=reasoning_trace,
            capabilities_used=self.config.capabilities[:3]
        )

    def discover_cross_domain_connections(self, other_domains: List['BaseDomainModule']) -> List['CrossDomainConnection']:
        """Discover connections to other domains"""
        connections = super().discover_cross_domain_connections(other_domains)

        for other_domain in other_domains:
            other_name = other_domain.config.domain_name

            if 'atmos' in other_name or 'spectro' in other_name:
                connection = CrossDomainConnection(
                    source_domain=self.config.domain_name,
                    target_domain=other_name,
                    connection_type="collaborative",
                    strength=0.8,
                    description="Planetary atmospheres require spectroscopic analysis"
                )
                connections.append(connection)

        return connections


register_domain(SolarSystemDomain)
