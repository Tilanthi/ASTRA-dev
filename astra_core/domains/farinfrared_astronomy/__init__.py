"""
Far-Infrared Astronomy Domain Module for STAN-XI-ASTRO

Specializes in far-infrared astronomy (~30-300 μm, 1-10 THz):
- Cold dust emission
- Star formation rates from FIR
- Infrared cirrus
- ISM dust properties
- Facilities: Herschel, SOFIA (upgraded), SPICA (proposed)

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
class FarInfraredAstronomyDomain(BaseDomainModule):
    """Domain specializing in far-infrared astronomy"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="farinfrared_astronomy",
            version="1.0.0",
            dependencies=["astro_physics", "ism", "infrared_astronomy"],
            keywords=[
                "far-infrared", "fir", "60 micron", "70 micron", "100 micron",
                "160 micron", "250 micron", "350 micron", "500 micron",
                "herschel", "pacs", "spire", "sofia", "cirrus", "infrared cirrus",
                "cold dust", "warm dust", "dust temperature", "modified blackbody",
                "star formation", "sfr", "l_fir", "l_tir"
            ],
            task_types=["FIR_SED", "COLD_DUST", "SFR_FIR"],
            description="Far-infrared astronomy (30-300 μm)",
            capabilities=[
                "fir_sed_modeling",
                "dust_temperature_fir",
                "sfr_calibration",
                "cirrus_modeling",
                "gas_mass_fir"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)
        logger.info("Far-Infrared Astronomy domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['dust', 'temperature', 'mbb']):
            return self._process_dust_query(query, context)
        elif any(kw in query_lower for kw in ['sfr', 'star formation']):
            return self._process_sfr_query(query, context)
        elif 'cirrus' in query_lower:
            return self._process_cirrus_query(query, context)
        else:
            return self._process_general_fir_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_dust_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing FIR dust query"]
        answer = (
            "FIR dust emission: modified blackbody I_ν ∝ κ_ν B_ν(T_d) ν^β. "
            "Herschel bands: 70, 100, 160 μm (PACS), 250, 350, 500 μm (SPIRE). "
            "Dust components: warm (T~30-50 K, β~1.5), cold (T~15-25 K, β~1.5-2). "
            "Dust mass: M_dust = F_ν D² / (κ_ν B_ν(T_d)), κ_250 ~ 0.89 cm²/g. "
            "β parameter: relates to dust composition/size, β~2 (silicate/graphite), "
            "β~1.5 (amorphous, fluffy). "
            "Gas-to-dust ratio: δ_GDR ~ 100 (Milky Way), higher in metal-poor galaxies."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["dust_temperature_fir", "gas_mass_fir"],
            metadata={"query_type": "DUST"}
        )

    def _process_sfr_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing FIR SFR query"]
        answer = (
            "FIR traces recent star formation (dust heated by UV from young stars). "
            "TIR (8-1000 μm) luminosity: SFR [M☉/yr] = 4.5×10⁻⁴⁴ L_TIR [L☉] (Kennicutt). "
            "FIR-specific: SFR ∝ L_FIR, with L_FIR = 4πν L_ν (42.5-122.5 μm). "
            "Herschel relations: SFR ∝ L_250 for obscured SF. "
            "Caveats: AGN heating (overestimate), cirrus heating (overestimate), "
            "old stars cirrus. Calibrations: galaxy-integrated, resolved "
            "star-forming regions. Used for high-z galaxies (rest-frame FIR)."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["sfr_calibration", "fir_sed_modeling"],
            metadata={"query_type": "SFR"}
        )

    def _process_cirrus_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing cirrus query"]
        answer = (
            "Infrared cirrus: diffuse, filamentary dust emission observed in FIR. "
            "Properties: T_dust ~ 15-20 K, optical depth τ_100 ~ 0.1-1. "
            "Origins: widespread ISM dust heated by interstellar radiation field. "
            "Correlations: FIR emission with HI (N_HI ~ 10²⁰ cm⁻²), "
            "with 100 μm opacity. "
            "Impact: foreground for high-z observations, confusion source, "
            "studies of diffuse ISM structure. "
            "Tracers: IRAS 100 μm, Herschel 100/160 μm, Planck HFI."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["cirrus_modeling"],
            metadata={"query_type": "CIRRUS"}
        )

    def _process_general_fir_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general FIR query"]
        answer = (
            "Far-infrared astronomy: 30-300 μm. Key tracers: cold dust, star formation. "
            "Facilities: Herschel (PACS 70-160 μm, SPIRE 250-500 μm), "
            "SOFIA (upgraded FORCAST, GREAT), future: Origins (proposed). "
            "Science: ISM dust properties, star formation laws, galaxy SEDs, "
            "cirrus structure, high-z star formation (rest-frame FIR). "
            "Advantages: dust optically thin, sensitive to cold dust, "
            "spatial resolution (20″ at 250 μm for Herschel)."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=reasoning_trace,
            capabilities_used=["fir_sed_modeling"],
            metadata={"query_type": "GENERAL"}
        )


def create_farinfrared_astronomy_domain() -> FarInfraredAstronomyDomain:
    return FarInfraredAstronomyDomain()
