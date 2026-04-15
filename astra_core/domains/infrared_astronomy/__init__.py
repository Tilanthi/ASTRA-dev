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
Infrared Astronomy Domain Module for STAN-XI-ASTRO

Specializes in infrared observations and physics:
- Near-IR (1-5 μm)
- Mid-IR (5-40 μm)
- Far-IR (40-200 μm)
- IR emission mechanisms
- Dust properties and evolution
- Polycyclic aromatic hydrocarbons (PAHs)
- Reddening and extinction
- IR excess and disks
- Star-forming galaxies (IR luminous)
- AGN torus emission

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
class InfraredAstronomyDomain(BaseDomainModule):
    """Domain specializing in infrared astronomy"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="infrared_astronomy",
            version="1.0.0",
            dependencies=["astro_physics", "ism", "star_formation"],
            keywords=[
                "infrared", "ir", "near-ir", "nir", "mid-ir", "mir", "far-ir", "fir",
                "j band", "h band", "k band", "spitzer", "wise", "herschel", "jwst",
                "dust emission", "thermal dust", "modified blackbody", "dust temperature",
                "pah", "polycyclic aromatic", "aib", "aromatic", "uib",
                "extinction", "av", "reddening", "a_k", "a_v", "extinction law",
                "protostar", "class 0", "class i", "yso", "ir excess",
                "lirg", "ulirg", "starburst", "infrared luminosity", "l_ir/l_bol"
            ],
            task_types=["IR_SPECTROSCOPY", "DUST_MODELING", "REDDENING_ANALYSIS"],
            description="Infrared astronomy observations and analysis",
            capabilities=[
                "dust_temperature",
                "pah_modeling",
                "extinction_correction",
                "ir_luminosity",
                "sed_modeling",
                "disk_detection"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)
        logger.info("Infrared Astronomy domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['dust', 'temperature', 'modified blackbody']):
            return self._process_dust_query(query, context)
        elif 'pah' in query_lower or 'aromatic' in query_lower:
            return self._process_pah_query(query, context)
        elif any(kw in query_lower for kw in ['extinction', 'reddening', 'a_v']):
            return self._process_extinction_query(query, context)
        elif any(kw in query_lower for kw in ['protostar', 'yso', 'class', 'ir excess']):
            return self._process_yso_query(query, context)
        elif any(kw in query_lower for kw in ['lirg', 'ulirg', 'starburst']):
            return self._process_ir_galaxy_query(query, context)
        else:
            return self._process_general_ir_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_dust_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing dust emission query"]

        answer = (
            "Dust IR emission: thermal equilibrium for big grains, "
            "I_ν ∝ κ_ν B_ν(T_d). Modified blackbody: I_ν ∝ ν^β B_ν(T). "
            "Typical: T ~ 15-30 K (ISM), T ~ 50-100 K (warm component). "
            "Emissivity: β ~ 1.5-2, depends on dust composition. "
            "Dust mass: M_dust = F_ν D² / (κ_ν B_ν(T_d)). "
            "κ_ν ~ 10 cm²/g at 1 THz (300 μm). "
            "Two-component model: warm (PAH, small grains, T~50 K), cold (big grains, T~15 K). "
            "Observations: Spitzer (MIPS 24/70/160 μm), Herschel (PACS 70/160 μm, "
            "SPIRE 250/350/500 μm), SOFIA, JWST MIRI."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["dust_temperature", "sed_modeling"],
            metadata={"query_type": "DUST"}
        )

    def _process_pah_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing PAH query"]

        answer = (
            "PAHs: polycyclic aromatic hydrocarbons, ~50-200 C atoms. "
            "Emission bands: 3.3, 6.2, 7.7, 8.6, 11.2, 12.7, 17 μm (AIBs/UIBs). "
            "Excitation: UV photon absorption → fluorescence (IR), "
            "single-photon process. "
            "Charge: neutral (3.3, 8.6, 11.2 μm) vs ionized (6.2, 7.7, 8.6 μm). "
            "Size: correlation with 11.2/3.3 ratio. "
            "Environment: PDRs (strong PAH), HII regions (PAH destroyed by hard UV), "
            "AGN (PAH suppressed). "
            "Space-based: Spitzer IRS, JWST MIRI provide PAH spectra."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["pah_modeling"],
            metadata={"query_type": "PAH"}
        )

    def _process_extinction_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing extinction query"]

        answer = (
            "IR extinction law: A_λ/A_K smaller than optical. "
            "Near-IR power law: A_λ ∝ λ^{-α} with α ~ 1.6-1.8 (diffuse ISM), "
            "α ~ 1.0-1.3 (dense clouds). "
            "Draine law: A_λ/A_K ~ 0.1 at K (2.2 μm), ~0.6 at 3.6 μm (IRAC 1), "
            "~1.0 at 4.5 μm (IRAC 2). "
            "Near-IR color excess: E(J-H) vs H-K_s diagram for YSO classification. "
            "Reddening correction: using IR pairs less affected by extinction "
            "than optical. "
            "Relation: A_V ≈ 8-10 × A_K for diffuse ISM."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["extinction_correction"],
            metadata={"query_type": "EXTINCTION"}
        )

    def _process_yso_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing YSO IR query"]

        answer = (
            "YSO classification from SED slope (α = d log λF_λ / d log λ). "
            "Class I: α > 0.3 (embedded, disk+envelope), "
            "Flat: -0.3 < α < 0.3 (transition), "
            "Class II: α < -0.3 (disk, weak envelope), "
            "Class III: photosphere (debris disk). "
            "IR excess: K-[24] > 0 (disk), K-[8] > 0 (inner disk). "
            "Spitzer/IRAC colors: [3.6]-[4.5] vs [5.8]-[8.0] diagram. "
            "Disk indicators: 10 μm silicate feature (absorption/emission), "
            "IR excess (accretion luminosity L_acc ∝ L_disk)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["sed_modeling", "disk_detection"],
            metadata={"query_type": "YSO"}
        )

    def _process_ir_galaxy_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing IR galaxy query"]

        answer = (
            "IR-luminous galaxies: LIRGs (L_IR > 10¹¹ L☉), ULIRGs (L_IR > 10¹² L☉). "
            "Luminosity from dust-reprocessed starlight: L_IR ≈ L_bol (dust-obscured). "
            "Warm vs cold ULIRGs: f_25μm/f_60μm ratio. "
            "Starburst vs AGN: PAH (6.2, 7.7, 11.2 μm) indicates star formation, "
            "high-ionization lines ([Ne V] 14 μm, [O IV] 26 μm) indicate AGN. "
            "Merger sequence: early (separate disks), mid (interaction, bridges), "
            "late (coalescence, nucleus). "
            "Local ULIRGs: mostly mergers, starburst+AGN composite. "
            "Observations: Spitzer, WISE, Herschel, JWST."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["ir_luminosity", "sed_modeling"],
            metadata={"query_type": "IR_GALAXY"}
        )

    def _process_general_ir_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general IR query"]

        answer = (
            "Infrared astronomy: 1-300 μm. Divisions: near-IR (1-5 μm, stellar, "
            "extinction correction), mid-IR (5-40 μm, PAH, silicates, hot dust), "
            "far-IR (40-200 μm, cold dust, star formation). "
            "Facilities: Ground: 2MASS, UKIRT, VISTA (near), IRTF, IRTF. "
            "Space: Spitzer, WISE, Herschel, JWST (NIRSpec, MIRI), "
            "Romm (upcoming). Science: star formation (dust luminosity), "
            "AGN (torus), protostars (SED evolution), ISM dust properties, "
            "high-z universe (rest-frame optical/IR)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["sed_modeling"],
            metadata={"query_type": "GENERAL"}
        )


def create_infrared_astronomy_domain() -> InfraredAstronomyDomain:
    return InfraredAstronomyDomain()
