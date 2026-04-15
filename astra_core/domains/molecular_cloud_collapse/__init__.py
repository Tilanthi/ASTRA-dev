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
Molecular Cloud Collapse Physics Domain Module for STAN-XI-ASTRO

Specializes in the physics of molecular cloud collapse:
- Gravitational instability criteria
- Core collapse and fragmentation
- Bonnor-Ebert mass
- Jeans instability
- Magnetic critical mass
- Turbulent support vs collapse
- Protostellar collapse modeling
- Collapse timescales
- Mass reservoir and accretion
- Initial Mass Function (IMF) origins

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
class MolecularCloudCollapseDomain(BaseDomainModule):
    """Domain specializing in molecular cloud collapse physics"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="molecular_cloud_collapse",
            version="1.0.0",
            dependencies=["astro_physics", "ism", "star_formation"],
            keywords=[
                "collapse", "gravitational collapse", "core collapse", "fragmentation",
                "jeans instability", "jeans mass", "jeans length", "bonnor-ebert",
                "be sphere", "critical mass", "magnetic critical", "mass-to-flux",
                "turbulent support", "virial parameter", "free-fall time", "collapse time",
                "inside-out collapse", "shu collapse", " Larson-Penston",
                "protostar formation", "first core", "second core"
            ],
            task_types=["COLLAPSE_MODELING", "INSTABILITY_ANALYSIS", "TIMESCALE"],
            description="Physics of molecular cloud and core collapse",
            capabilities=[
                "jeans_analysis",
                "bonnor_ebert_mass",
                "magnetic_criticality",
                "collapse_timescale",
                "fragmentation_modeling",
                "imf_prediction"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)
        logger.info("Molecular Cloud Collapse domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['jeans', 'instability', 'bonnor', 'ebert']):
            return self._process_instability_query(query, context)
        elif any(kw in query_lower for kw in ['magnetic', 'flux', 'support']):
            return self._process_magnetic_query(query, context)
        elif any(kw in query_lower for kw in ['timescale', 'free-fall', 'ff']):
            return self._process_timescale_query(query, context)
        elif any(kw in query_lower for kw in ['fragmentation', 'imf', 'mass function']):
            return self._process_fragmentation_query(query, context)
        else:
            return self._process_general_collapse_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_instability_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing instability query"]

        answer = (
            "Jeans instability: collapse when gravity > pressure. "
            "Jeans mass: M_J = (πk_B T / G μ m_H)^{3/2} ρ^{-1/2}. "
            "Jeans length: λ_J = c_s (π / Gρ)^{1/2}. "
            "For T=10 K, n=10⁴ cm⁻³: M_J ~ 1 M☉. "
            "Bonnor-Ebert mass: M_BE = 1.18 c_s³ / (G^{3/2} ρ^{1/2}), critical for "
            "stable BE sphere (external pressure). Critical BE sphere: "
            "ξ_max = 6.5, ρ_c/ρ_surface = 14. Observed cores: "
            "α_vir = 5σ_v²R/GM, α_vir < 2 for collapsing cores. "
            "Non-thermal support: turbulence increases effective Jeans mass."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["jeans_analysis", "bonnor_ebert_mass"],
            metadata={"query_type": "INSTABILITY"}
        )

    def _process_magnetic_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing magnetic support query"]

        answer = (
            "Magnetic support: mass-to-flux ratio μ = (M/Φ) / (M/Φ)_crit. "
            "Critical value: (M/Φ)_crit = c_Φ / (2π√G) ≈ 1/(2π√G) with c_Φ ≈ 1. "
            "Subcritical: μ < 1 (magnetically subcritical, supported). "
            "Supercritical: μ > 1 (collapse proceeds). "
            "Observations: μ ≈ 1-3 (typically supercritical). "
            "Ambipolar diffusion: neutral particles slip past ions, "
            "timescale t_AD ~ 10 Myr (enhanced in cores). "
            "Magnetic critical mass: M_Φ = B R² / √G. For B=10 μG, R=0.1 pc: "
            "M_Φ ≈ 2 M☉."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["magnetic_criticality"],
            metadata={"query_type": "MAGNETIC"}
        )

    def _process_timescale_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing timescale query"]

        answer = (
            "Collapse timescales: Free-fall time t_ff = (3π/32Gρ)^{1/2}. "
            "For n = 10⁴ cm⁻³: t_ff ≈ 0.2 Myr. For n = 10⁶ cm⁻³: t_ff ≈ 0.02 Myr. "
            "Comparison: t_ff vs t_turb (crossing time), t_ADE (ambipolar diffusion). "
            "Collapse phases: (1) Isothermal collapse (T~10 K), r ∝ t^{2/3}, "
            "ρ ∝ t^{-2}. (2) First core (adiabatic, T~2000 K), r~5 AU. "
            "(3) Second core (H₂ dissociation, T~2000 K), r~5 R☉. "
            "Observational signatures: infall profiles (ρ ∝ r^{-2}), "
            "blue asymmetry (infall), line width increase."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["collapse_timescale"],
            metadata={"query_type": "TIMESCALE"}
        )

    def _process_fragmentation_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing fragmentation query"]

        answer = (
            "Fragmentation: cloud breaks into cores during collapse. "
            "Jeans fragmentation: fragments of size λ_J form. "
            "Turbulent fragmentation: hierarchical structure, "
            "mass spectrum from turbulent cascade. "
            "Competitive accretion: cores compete for mass from common reservoir. "
            "IMF origin: fragmentation + accretion → Salpeter IMF: "
            "dN/dM ∝ M^{-2.35} for M > 0.5 M☉, turnover at low mass. "
            "Observations: core mass function (CMF) resembles IMF (shifted "
            "by ε_ff ~ 0.3). Fragmentation regulated by: temperature "
            "(thermal Jeans), turbulence (non-thermal), magnetic fields."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["fragmentation_modeling", "imf_prediction"],
            metadata={"query_type": "FRAGMENTATION"}
        )

    def _process_general_collapse_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general collapse query"]

        answer = (
            "Molecular cloud collapse is governed by gravity vs support forces. "
            "Support mechanisms: thermal pressure (T~10 K), turbulence (σ_v ~ 1-2 km/s), "
            "magnetic fields (B~10 μG), cosmic rays. "
            "Collapse criteria: M > M_J (Jeans), M > M_BE (Bonnor-Ebert), "
            "μ > 1 (magnetic), α_vir < 2 (turbulent). "
            "Collapse models: Shu (inside-out), Larson-Penston (outside-in), "
            "Whitworth (turbulent). Observational tracers: infall profiles, "
            "velocity gradients, chemistry (depletion), dust continuum. "
            "ALMA and VLA observe collapse in Class 0 protostars."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["jeans_analysis", "collapse_timescale"],
            metadata={"query_type": "GENERAL"}
        )


def create_molecular_cloud_collapse_domain() -> MolecularCloudCollapseDomain:
    return MolecularCloudCollapseDomain()
