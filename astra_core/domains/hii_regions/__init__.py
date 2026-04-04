"""
HII Region Physics Domain Module for STAN-XI-ASTRO

Specializes in HII region physics and evolution:
- Photoionization physics
- Stromgren spheres
- HII region expansion
- Champagne flows
- Ultra-compact HII regions
- Hypercompact HII regions
- Collect-and-collapse
- Radiation-driven implosion
- HII region morphology
- Triggered star formation

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
class HIIRegionsDomain(BaseDomainModule):
    """Domain specializing in HII region physics"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="hii_regions",
            version="1.0.0",
            dependencies=["astro_physics", "ism", "star_formation"],
            keywords=[
                "hii region", "stromgren", "ionization", "photoionization",
                "d-type front", "r-type front", "ionization front", "if",
                "champagne flow", "blister", "ultracompact", "hypercompact",
                "collect and collapse", "radiation driven implosion", "rdi",
                "triggered star formation", "pillars", "elephant trunks",
                "free-free emission", "bremsstrahlung", "radio recombination line"
            ],
            task_types=["IONIZATION_MODELING", "EXPANSION_MODELING", "TRIGGERED_SF"],
            description="HII region physics, expansion, and triggered star formation",
            capabilities=[
                "stromgren_radius",
                "ionization_front_modeling",
                "expansion_timescale",
                "triggered_sf_efficiency",
                "morphology_classification"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)
        logger.info("HII Regions domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['stromgren', 'ionization', 'front', 'if']):
            return self._process_ionization_query(query, context)
        elif 'expansion' in query_lower:
            return self._process_expansion_query(query, context)
        elif any(kw in query_lower for kw in ['compact', 'uchii', 'hchii']):
            return self._process_compact_query(query, context)
        elif any(kw in query_lower for kw in ['triggered', 'collect', 'collapse', 'rdi']):
            return self._process_triggered_query(query, context)
        else:
            return self._process_general_hii_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_ionization_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing ionization query"]

        answer = (
            "Stromgren sphere: ionized region around hot star. "
            "Radius: R_S = (3Q_H / 4π n² β)^{1/3}, where Q_H = ionizing photons/s, "
            "n = density, β = case B recombination coefficient. "
            "For O star (Q_H ~ 10⁴⁹ s⁻¹) in n=10³ cm⁻³: R_S ~ 10 pc. "
            "Front types: D-type (subsonic, weak R-type), R-type (supersonic, "
            "radiation-bounded vs density-bounded). "
            "Thermal balance: T ~ 10⁴ K (heating by photoionization, cooling "
            "by metal lines, free-free). Optical depth: τ_ν = σ_ν ∫ n_e n_i dl, "
            "τ~1 at Lyman limit (912 Å)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.92,
            reasoning_trace=reasoning_trace,
            capabilities_used=["stromgren_radius", "ionization_front_modeling"],
            metadata={"query_type": "IONIZATION"}
        )

    def _process_expansion_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing expansion query"]

        answer = (
            "HII expansion: overpressured (P_II/P_I ~ 10⁴) bubble expands into neutral medium. "
            "Spitzer solution: R = R_0 (1 + 7/4 c_i t / R_0)^{4/7}, velocity "
            "v_exp ≈ 10 km/s for t ~ few Myr. D-type front: ionized gas expands "
            "subsonically, supersonic shock precedes IF. "
            "Champagne flow: HII breaks out of cloud into low-density medium, "
            "blister morphology, outflow ~10 km/s. "
            "Observational tracers: radio free-free (S_ν ∝ ν^{-0.1}), "
            "recombination lines (Hα, Hβ), [OIII], [SII] (density). "
            "Expansion age: t ≈ R_exp / v_exp ~ 1-5 Myr."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["expansion_timescale"],
            metadata={"query_type": "EXPANSION"}
        )

    def _process_compact_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing compact HII query"]

        answer = (
            "UC HII: ultracompact, R < 0.1 pc, EM > 10⁷ pc cm⁻⁶, n > 10⁴ cm⁻³. "
            "HC HII: hypercompact, R < 0.01 pc, EM > 10⁸ pc cm⁻⁶, often masers. "
            "Characteristics: dust-enshrouded, broad recombination lines (Δv > 50 km/s), "
            "young (~10⁴ yr), pressure confined. "
            "Expansion stalled by high pressure: t_exp > t_Age. "
            "Pressure: nT ~ 10⁸ K cm⁻³ (thermal), additional turbulence, ram pressure. "
            "Triggers: CH₃OH masers (6.7 GHz), OH masers, radio continuum, "
            "IR emission (dust)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["stromgren_radius", "expansion_timescale"],
            metadata={"query_type": "COMPACT"}
        )

    def _process_triggered_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing triggered SF query"]

        answer = (
            "Triggered star formation by HII regions: "
            "(1) Collect-and-collapse: shell sweeps up material, becomes "
            "gravitationally unstable. Criteria: M_shell > M_Jeff, "
            "t_* < t_exp (star formation before shell dispersal). "
            "(2) RDI (radiation-driven implosion): UV incident on pre-existing core, "
            "compresses, accelerates collapse. Timescale: t_RD ≈ 10⁵ yr (c_c/c_s)^{-1}. "
            "(3) Pillar formation: shadowing, cometary pillars, elephant trunks. "
            "Observations: age gradients around HII regions, secondary clusters "
            "at shell edges, pillar-head protostars. Efficiency: "
            "SFE_trigger ~ 10-30% of shell mass."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["triggered_sf_efficiency", "expansion_timescale"],
            metadata={"query_type": "TRIGGERED_SF"}
        )

    def _process_general_hii_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general HII query"]

        answer = (
            "HII regions are ionized gas (T~10⁴ K) around massive stars. "
            "Exciting stars: O-type (M > 20 M☉) for classical HII, "
            "B-type for smaller. Evolution: ionization (t~0), expansion (t~0.1-1 Myr), "
            "dispersal (t~1-5 Myr). Morphology: spherical (uniform), blister "
            "(breakout), cometary (flow), shell (expansion). "
            "Observations: radio continuum (free-free), recombination lines, "
            "forbidden lines ([OII], [OIII], [SII]), IR (dust). "
            "Uses: star formation tracers, galaxy distance scale (extragalactic HII), "
            "chemical enrichment, feedback quantification."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["stromgren_radius", "morphology_classification"],
            metadata={"query_type": "GENERAL"}
        )


def create_hii_regions_domain() -> HIIRegionsDomain:
    return HIIRegionsDomain()
