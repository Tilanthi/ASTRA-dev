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
Submillimeter Wave Astronomy Domain Module for STAN-XI-ASTRO

Specializes in submillimetre wave astronomy (~0.3-3 mm, 100-1000 GHz):
- Dust continuum emission
- High-J CO lines
- Atomic fine structure lines
- High-redshift galaxies
- Star formation tracers
- Facilities: ALMA Bands 6-10, JCMT, APEX, SMA, NOEMA

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
class SubmillimeterAstronomyDomain(BaseDomainModule):
    """Domain specializing in submillimeter wave astronomy"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="submillimeter_astronomy",
            version="1.0.0",
            dependencies=["astro_physics", "ism", "infrared_astronomy"],
            keywords=[
                "submillimeter", "submm", "850 micron", "450 micron", "350 micron",
                "scuba", "jcmt", "alma band 7", "alma band 9", "alma band 8",
                "apex", "laboca", "sma", "novacam", "high-j", "co high-j",
                "[ci]", "cii", "fine structure", "dust continuum", "submm galaxy",
                "high-z", "dsfg", "dusty star-forming galaxy"
            ],
            task_types=["SUBMM_CONTINUUM", "HIGH-J_LINESS", "HIGH-Z_SF"],
            description="Submillimeter wave astronomy (100-1000 GHz)",
            capabilities=[
                "dust_mass",
                "sfr_submm",
                "high-z_detection",
                "excitation_analysis",
                "gas_mass_submm"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)
        logger.info("Submillimeter Astronomy domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['dust', 'continuum', '850', '450']):
            return self._process_continuum_query(query, context)
        elif 'high-j' in query_lower or 'excitation' in query_lower:
            return self._process_excitation_query(query, context)
        elif any(kw in query_lower for kw in ['high-z', 'dsfg', 'submm galaxy']):
            return self._process_highz_query(query, context)
        else:
            return self._process_general_submm_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_continuum_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing submm continuum query"]
        answer = (
            "Submm continuum from dust: I_ν ∝ κ_ν B_ν(T_d). "
            "Key wavelengths: 450 μm (670 GHz), 850 μm (350 GHz), "
            "1.3 mm (230 GHz, ALMA Band 6). "
            "Dust mass: M_dust = F_ν D² / (κ_ν B_ν(T)), κ_850 ~ 1.5 cm²/g. "
            "Star formation rate: SFR ∝ L_IR, L_submm traces obscured SF. "
            "SCUBA-2 (JCMT): 850/450 μm, surveys COSMOS, S2CLS. "
            "ALMA Band 6/7: 1.3/0.87 mm, high-resolution imaging. "
            "Uses: prestellar cores, protostellar envelopes, galaxy dust mass, "
            "high-z SF."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["dust_mass", "sfr_submm"],
            metadata={"query_type": "CONTINUUM"}
        )

    def _process_excitation_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing excitation query"]
        answer = (
            "High-J CO lines: CO J=4-3 (461 GHz), J=6-5 (691 GHz), J=7-6 (807 GHz). "
            "Traces warm (T > 50 K), dense (n > 10⁴ cm⁻³) gas. "
            "Excitation temperature: T_ex from line ratio. "
            "Critical density: n_crit ~ 10⁴-10⁵ cm⁻³ for J=4-3. "
            "Fine structure lines: [CI] ³P₁-³P₀ (492 GHz), [CI] ³P₂-³P₁ (809 GHz), "
            "[CII] ²P₃/₂-²P₁/₂ (1.9 THz, 158 μm). "
            "[CII] major coolant of ISM, traces PDRs, CO-dark H₂. "
            "Observations: ALMA Bands 8-10 (400-950 GHz), APEX, SOFIA (upgraded)."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["excitation_analysis"],
            metadata={"query_type": "EXCITATION"}
        )

    def _process_highz_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing high-z query"]
        answer = (
            "Submm galaxies (SMGs/DSFGs): selected at 850 μm, S_850 > 2-4 mJy. "
            "Redshifts: z ~ 1-4, peak at z~2.5. "
            "Properties: SFR ~ 100-1000 M☉/yr, M_* ~ 10¹¹ M☉, dust T ~ 30-50 K. "
            "Selection: negative K-correction (S_ν × D_L(z) roughly flat to z~4). "
            "Counterparts: radio (VLA), mid-IR (Spitzer/IRAC), optical/NIR. "
            "ALMA follow-up: precise positions, redshifts (CO lines), multiplicity. "
            "Science: cosmic SF history, massive galaxy formation, "
            "AGN-starburst connection."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["high-z_detection", "sfr_submm"],
            metadata={"query_type": "HIGH-Z"}
        )

    def _process_general_submm_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general submm query"]
        answer = (
            "Submm astronomy: 100-1000 GHz (λ = 0.3-3 mm). "
            "Atmospheric windows: 450, 850 μm (ground-based), 350 μm (Mauna Kea). "
            "Space: Herschel (PACS/SPIRE), future Origins. "
            "Key facilities: ALMA (Bands 6-10, 211-950 GHz), "
            "JCMT SCUBA-2, APEX LABOCA/SABOCA, SMA, NOEMA. "
            "Science: cold dust emission, high-z star formation, "
            "protostellar envelopes, debris disks, PDRs, galaxy ISM. "
            "Advantages: dust optically thin, high spatial resolution (ALMA), "
            "redshift-independent selection."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["dust_mass", "high-z_detection"],
            metadata={"query_type": "GENERAL"}
        )


def create_submillimeter_astronomy_domain() -> SubmillimeterAstronomyDomain:
    return SubmillimeterAstronomyDomain()
