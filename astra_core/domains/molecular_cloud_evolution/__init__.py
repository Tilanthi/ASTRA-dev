"""
Molecular Cloud Evolution Domain Module for STAN-XI-ASTRO

Specializes in molecular cloud evolution over time:
- Cloud formation and dissolution
- Cloud lifetimes and lifecycles
- Cloud dispersal mechanisms
- Feedback impacts on clouds
- Cloud-to-cloud variations
- Galactic environmental effects
- Star formation efficiency across clouds
- Hierarchical structure evolution
- Cloud scaling relations

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
class MolecularCloudEvolutionDomain(BaseDomainModule):
    """Domain specializing in molecular cloud evolution"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="molecular_cloud_evolution",
            version="1.0.0",
            dependencies=["astro_physics", "ism", "star_formation"],
            keywords=[
                "cloud evolution", "cloud formation", "cloud dissolution", "cloud lifetime",
                "molecular cloud lifecycle", "gmc", "giant molecular cloud", "cloud dispersal",
                "feedback dispersal", "stellar feedback", "supernova feedback", "radiation feedback",
                "sfe", "star formation efficiency", "efficiency per free-fall",
                "cloud scaling", "larson's relations", "mass-size", "velocity-size"
            ],
            task_types=["CLOUD_LIFETIME", "FEEDBACK_ANALYSIS", "SME_ANALYSIS"],
            description="Molecular cloud evolution and lifecycles",
            capabilities=[
                "lifetime_estimation",
                "dispersal_modeling",
                "sfe_measurement",
                "scaling_relations",
                "feedback_impact"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)
        logger.info("Molecular Cloud Evolution domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['lifetime', 'lifecycle', 'formation', 'dissolution']):
            return self._process_lifetime_query(query, context)
        elif 'feedback' in query_lower:
            return self._process_feedback_query(query, context)
        elif any(kw in query_lower for kw in ['sfe', 'efficiency', 'sfr']):
            return self._process_sfe_query(query, context)
        elif any(kw in query_lower for kw in ['scaling', 'larson', 'mass-size']):
            return self._process_scaling_query(query, context)
        else:
            return self._process_general_evolution_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_lifetime_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing cloud lifetime query"]

        answer = (
            "Molecular cloud lifetimes: debated, estimates range 10-30 Myr. "
            "Methods: cloud crossing time (t_cross = R/σ_v), stellar age dating, "
            "cloud dispersal timescales, chemical evolution. "
            "Short lifetime (~10 Myr): rapid feedback dispersal, cloud evolution "
            "dominated by feedback. Long lifetime (~30 Myr): slow evolution, "
            "clouds survive multiple feedback cycles. "
            "Formation scenarios: HI-H2 transition, gravitational instability, "
            "spiral arm shock, cloud-cloud collisions. Dissipation: stellar feedback "
            "(OB winds, SNe, HII expansion), shear, tidal forces."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["lifetime_estimation"],
            metadata={"query_type": "LIFETIME"}
        )

    def _process_feedback_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing feedback query"]

        answer = (
            "Stellar feedback disperses clouds: (1) Photoionization: HII region expansion, "
            "D-type ionization front, t_expand ~ few Myr. (2) Stellar winds: "
            "collective winds from clusters, momentum injection, wind bubbles. "
            "(3) Radiation pressure: UV/optical on dust, IR trapped radiation, "
            "Eddington-limited outflows. (4) Supernovae: shock sweeps gas, "
            "t_SNR ~ few × 10⁴ yr, energy E_SN = 10⁵¹ erg. "
            "Observations: cloud dispersal around HII regions, gas removal "
            "efficiency ε = M_ejected/M_initial ~ 0.1-1. Momentum injection: "
            "p_mom/m_★ ~ 10³-10⁵ km/s (Murray et al.)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["feedback_impact", "dispersal_modeling"],
            metadata={"query_type": "FEEDBACK"}
        )

    def _process_sfe_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing SFE query"]

        answer = (
            "Star formation efficiency: ε_ff = SFR × t_ff / M_gas (efficiency per free-fall). "
            "Observed: ε_ff ~ 0.01-0.1 (median ~0.02). Cloud-scale SFE: "
            "ε_cloud = M_*/(M_* + M_gas) ~ 0.01-0.3 (Galactic clouds), "
            "up to 0.5 in extreme starbursts. "
            "Variation: depends on gas surface density (Σ_gas), turbulence, "
            "magnetic field strength. Kennicutt-Schmidt: Σ_SFR ∝ Σ_gas^N "
            "with N ~ 1.4 (galaxy-scale), N ~ 0.5-1 (cloud-scale). "
            "Low efficiency: feedback regulated, magnetic support, turbulent support."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["sfe_measurement"],
            metadata={"query_type": "SFE"}
        )

    def _process_scaling_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing scaling relations query"]

        answer = (
            "Larson's relations (1981): (1) σ_v ∝ R^{0.38} (velocity-size), "
            "(2) Σ ∝ R^{-0.2} (constant surface density), (3) "
            "M ∝ R² (M ∝ R for subregions). Modern results: "
            "σ_v ∝ R^{0.5±0.05} for GMCs, Σ varies more than Larson found. "
            "Virial parameter: α_vir = 5σ_v²R/GM ~ 1-2 (near virial balance). "
            "Size-linewidth: σ_v = (Σ/π)^{0.5} R^{0.5} (gravitational binding). "
            "Implications: clouds are marginally bound, hierarchical structure, "
            "turbulent cascade from large scales."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["scaling_relations"],
            metadata={"query_type": "SCALING"}
        )

    def _process_general_evolution_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general cloud evolution query"]

        answer = (
            "Molecular clouds evolve from diffuse gas to star-forming regions. "
            "Stages: (1) Formation: HI → H₂, self-gravity, external compression. "
            "(2) Early evolution: turbulent decay, magnetic support, filamentary structure. "
            "(3) Star formation onset: core formation, localized collapse. "
            "(4) Feedback phase: HII regions, winds, SNe dispersing gas. "
            "(5) Dissolution: cloud destroyed, returns to diffuse ISM or recycled. "
            "Timescales: t_form ~ 5-10 Myr, t_SF ~ 5-15 Myr, t_disrupt ~ 1-5 Myr. "
            "Environmental dependence: spiral arms (compression), bar (shear), "
            "center (high pressure), outskirts (quiescent)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=reasoning_trace,
            capabilities_used=["lifetime_estimation", "dispersal_modeling"],
            metadata={"query_type": "GENERAL"}
        )


def create_molecular_cloud_evolution_domain() -> MolecularCloudEvolutionDomain:
    return MolecularCloudEvolutionDomain()
