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
Galactic Structure Domain Module for STAN-XI-ASTRO

Specializes in the structure of the Milky Way:
- Galactic disk components (thin, thick)
- Galactic bulge and bar
- Galactic halo (stellar, dark)
- Spiral arms and structure
- Galactic rotation curve
- Solar neighborhood
- Galactic Center
- Metallicity gradients
- Stellar populations and age gradients
- Galactic archaeology (chemo-dynamics)

Date: 2026-03-20
Version: 1.0.0
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging

try:
    from .. import BaseDomainModule, DomainConfig, DomainQueryResult, register_domain
except ImportError:
    class BaseDomainModule:
        def __init__(self, config=None):
            self.config = config
            self._initialized = False

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

    def register_domain(cls):
        return cls

logger = logging.getLogger(__name__)


@register_domain
class GalacticStructureDomain(BaseDomainModule):
    """Domain specializing in Galactic structure"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="galactic_structure",
            version="1.0.0",
            dependencies=["astro_physics", "ism", "star_formation", "galactic_archaeology"],
            keywords=[
                "milky way", "galactic structure", "galactic disk", "thin disk", "thick disk",
                "bulge", "galactic bulge", "bar", "galactic bar", "boxy peanut",
                "halo", "stellar halo", "dark halo", "dark matter halo",
                "spiral arm", "arm", "perseus arm", "sagittarius arm", "scutum arm",
                "rotation curve", "galactic rotation", "differential rotation",
                "solar neighborhood", "local standard of rest", "lsr",
                "galactic center", "galactocentric distance", "r0",
                "metallicity gradient", "abundance gradient", "radial gradient"
            ],
            task_types=["DISK_STRUCTURE", "ROTATION_CURVE", "BULGE_BAR"],
            description="Structure of the Milky Way galaxy",
            capabilities=[
                "rotation_curve",
                "scale_height",
                "metallicity_gradient",
                "stellar_density",
                "kinematics"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)

        # Galactic parameters
        self._params = {
            'R0': 8.15,  # Galactocentric distance (kpc)
            'v0': 220,  # Circular velocity (km/s)
            'z0_thin': 0.1,  # Thin disk scale height (kpc)
            'z0_thick': 0.3,  # Thick disk scale height (kpc)
            'hR_thin': 2.5,  # Thin disk scale length (kpc)
            'hR_thick': 2.0,  # Thick disk scale length (kpc)
        }

        logger.info("Galactic Structure domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['disk', 'thin', 'thick', 'scale height']):
            return self._process_disk_query(query, context)
        elif any(kw in query_lower for kw in ['bulge', 'bar', 'boxy']):
            return self._process_bulge_query(query, context)
        elif any(kw in query_lower for kw in ['rotation', 'curve', 'v_c']):
            return self._process_rotation_query(query, context)
        elif any(kw in query_lower for kw in ['spiral', 'arm']):
            return self._process_spiral_query(query, context)
        elif any(kw in query_lower for kw in ['halo', 'dark matter']):
            return self._process_halo_query(query, context)
        else:
            return self._process_general_structure_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_disk_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing disk structure query"]
        answer = (
            "Galactic disk components: (1) Thin disk: scale height h_z ~ 100 pc, "
            "scale length h_R ~ 2.5 kpc, young stars, gas, ongoing SF. "
            "(2) Thick disk: h_z ~ 300-500 pc, h_R ~ 2 kpc, old stars, "
            "α-enhanced, heated by ancient mergers. "
            "(3) Gas disk: scale height varies (HI ~ 100 pc, CO ~ 50 pc). "
            "Flaring: h_z increases with R (thick disk flares more). "
            "Mass: thin ~ 4×10¹⁰ M☉, thick ~ 2×10¹⁰ M☉, gas ~ 1×10⁹ M☉. "
            "Tracers: star counts, kinematics, chemical abundances."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["scale_height", "stellar_density"],
            metadata={"query_type": "DISK"}
        )

    def _process_bulge_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing bulge/bar query"]
        answer = (
            "Galactic bulge: triaxial bar-in-disk, boxy/peanut X-shape. "
            "Size: ~2 kpc × 1 kpc × 0.6 kpc. "
            "Stellar population: old (10 Gyr), metal-rich ([Fe/H] ~ +0.3), "
            "α-enhanced ([α/Fe] ~ +0.3). "
            "Bar length: ~4-5 kpc, pattern speed Ω_p ~ 40-50 km/s/kpc. "
            "Structure: bar drives spiral arms, buckling creates X-shape. "
            "Formation: early collapse (classical), secular evolution (bar). "
            "Observations: COBE/DIRBE, Spitzer, VVV (IR), Gaia (kinematics), "
            "APOGEE (chemistry)."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["kinematics", "stellar_density"],
            metadata={"query_type": "BULGE_BAR"}
        )

    def _process_rotation_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing rotation curve query"]
        answer = (
            "Galactic rotation curve: v_c(R) ≈ 220 km/s for R = 3-15 kpc (flat). "
            "Components: (1) Bulge: v_c ∝ R for R < 1 kpc. "
            "(2) Disk: peaks at R ~ 2-3 kpc. (3) Halo: v_c ≈ constant at large R. "
            "Solar motion: v_⊙ ≈ 240 km/s (Gaia). "
            "Measurement: HI (21cm) for outer disk, CO/HII for inner, "
            "stellar kinematics. "
            "Rotation laws: v(R) = v_0 (flat), Brand curve (epicyclic). "
            "Oort constants: A ≈ 15 km/s/kpc, B ≈ -12 km/s/kpc."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.92,
            reasoning_trace=reasoning_trace,
            capabilities_used=["rotation_curve", "kinematics"],
            metadata={"query_type": "ROTATION"}
        )

    def _process_spiral_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing spiral arm query"]
        answer = (
            "Milky Way spiral structure: 4 major arms (Perseus, Sagittarius, "
            "Scutum-Centaurus, Norma) + smaller arms (Carina, Local spur). "
            "Pitch angle: i ~ 12° (tightly wound). "
            "Arm tracers: O/B associations, HII regions, GMCs, methanol masers. "
            "Arm properties: Perseus arm (R ~ 10 kpc, major SF), "
            "Local arm (R ~ 8 kpc, minor, Sun near inner edge). "
            "Spiral density waves: shock triggers SF, triggers star formation. "
            "Observations: VLBI masers (parallax + proper motion), "
            "GAIA (3D positions), surveys (WISE Spitzer)."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["stellar_density"],
            metadata={"query_type": "SPIRAL"}
        )

    def _process_halo_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing halo query"]
        answer = (
            "Galactic halo components: (1) Stellar halo: spheroidal distribution, "
            "ρ ∝ R^{-3} to R^{-4}, metal-poor ([Fe/H] ~ -1.5). "
            "Mass: ~10⁹ M☉ within 100 kpc. Includes halo stars, globular clusters, "
            "tidal streams. "
            "(2) Dark matter halo: NFW profile, ρ ∝ 1/[R(R_s)²], "
            "scale radius R_s ~ 20 kpc, virial radius ~200 kpc. "
            "Mass: ~10¹² M☉ within virial radius. "
            "Tracers: RR Lyrae, BHB stars, globular clusters, satellite galaxies, "
            "stellar streams (Gaia)."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["stellar_density", "kinematics"],
            metadata={"query_type": "HALO"}
        )

    def _process_general_structure_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general structure query"]
        answer = (
            "Milky Way structure: barred spiral galaxy (Hubble type SBbc). "
            "Mass: M_total ~ 10¹² M☉, M_stellar ~ 6×10¹⁰ M☉. "
            "Scale: diameter ~ 30 kpc, scale height ~ 300 pc. "
            "Components: thin disk (young stars), thick disk (old stars), "
            "bulge/bar (central), stellar halo (old stars, streams), "
            "dark matter halo (dominates mass). "
            "Sun's location: R_0 ≈ 8.15 kpc, z ≈ 20 pc (above midplane). "
            "Observational tools: Gaia (positions, kinematics), "
            "APOGEE/GALAH (chemistry), 2MASS/WISE (IR)."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["scale_height", "rotation_curve"],
            metadata={"query_type": "GENERAL"}
        )


def create_galactic_structure_domain() -> GalacticStructureDomain:
    return GalacticStructureDomain()
