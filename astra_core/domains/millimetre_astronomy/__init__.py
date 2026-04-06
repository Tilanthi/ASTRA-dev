"""
Millimetre Wave Astronomy Domain Module for STAN-XI-ASTRO

Specializes in millimetre wave astronomy (~3 mm - 10 mm, 30-100 GHz):
- Radio continuum emission
- Molecular line surveys (3 mm band)
- Transition lines (CO J=1-0 at 3 mm)
- Polarization and synchrotron
- CMB observations
- Facilities: ALMA Band 3, VLA, GBT, IRAM 30m, NOEMA

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
class MillimetreAstronomyDomain(BaseDomainModule):
    """Domain specializing in millimetre wave astronomy"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="millimetre_astronomy",
            version="1.0.0",
            dependencies=["astro_physics", "ism", "radio_galactic"],
            keywords=[
                "millimetre", "mm", "3 mm", "7 mm", "1 cm", "3 mm band",
                "alma band 3", "alma band 4", "noema", "iram", "30m",
                "co j1-0", "115 ghz", "93 ghz", "co isotope", "13co", "c18o",
                "continuum", "synchrotron", "free-free", "dust emission",
                "polarization", "magnetic field", "cmb", "30 ghz", "90 ghz"
            ],
            task_types=["MM_CONTINUUM", "MM_LINESS", "MM_POLARIZATION"],
            description="Millimetre wave astronomy (30-100 GHz)",
            capabilities=[
                "continuum_modeling",
                "line_survey",
                "polarization_analysis",
                "gas_mass_measurement"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)
        logger.info("Millimetre Astronomy domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if 'co' in query_lower or 'line' in query_lower:
            return self._process_line_query(query, context)
        elif 'continuum' in query_lower:
            return self._process_continuum_query(query, context)
        elif 'polarization' in query_lower or 'magnetic' in query_lower:
            return self._process_polarization_query(query, context)
        else:
            return self._process_general_mm_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_line_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing mm line query"]
        answer = (
            "Key mm lines: CO J=1-0 (115 GHz), 13CO 1-0 (110 GHz), C¹⁸O 1-0 (109 GHz). "
            "CO traces molecular gas, 13CO and C¹⁸O trace column density. "
            "X_CO factor: N(H₂) = X_CO ∫ I_CO dv, X_CO ~ 2×10²⁰ cm⁻²/(K km/s). "
            "Other lines: HCN 1-0 (88.6 GHz, dense gas tracer), "
            "CS 2-1 (97.98 GHz, high density), SiO 2-1 (86.8 GHz, shocks). "
            "Facilities: ALMA Band 3 (84-116 GHz), NOEMA (3 mm), "
            "IRAM 30m (3 mm), GBT (3 mm receiver)."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["line_survey", "gas_mass_measurement"],
            metadata={"query_type": "LINE"}
        )

    def _process_continuum_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing mm continuum query"]
        answer = (
            "Millimetre continuum components: (1) Synchrotron: S_ν ∝ ν^{-α}, "
            "α ~ 0.7-1.0, non-thermal electrons in B-fields. "
            "(2) Free-free: S_ν ∝ ν^{-0.1}, optically thin, from HII regions. "
            "(3) Thermal dust: S_ν ∝ ν^{3-4} (Rayleigh-Jeans), modified blackbody. "
            "(4) Anomalous microwave emission: spinning dust, ~10-60 GHz. "
            "Uses: SED decomposition, radio spectral index, dust mass "
            "(low-frequency), CMB foreground removal."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["continuum_modeling"],
            metadata={"query_type": "CONTINUUM"}
        )

    def _process_polarization_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing polarization query"]
        answer = (
            "Polarization at mm: linear polarization from synchrotron, dust emission. "
            "Synchrotron polarization: fractional polarization p ~ 0.7×(α+1)/(α+5/3), "
            "typically p ~ 5-10%. Dust polarization: aligned grains, p ~ 1-10%, "
            "B-field orientation (E-mode perpendicular to B). "
            "Measurements: Stokes I, Q, U, V. Polarization angle: χ = 0.5 arctan(U/Q). "
            "Applications: B-field mapping, Faraday rotation (RM ∝ λ²), "
            "CMB E/B modes. Facilities: ALMA Band 3 polarization, "
            "JVLA (Ka, Q bands)."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["polarization_analysis"],
            metadata={"query_type": "POLARIZATION"}
        )

    def _process_general_mm_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general mm query"]
        answer = (
            "Millimetre wave astronomy: 30-100 GHz (λ = 3-10 mm). "
            "Key lines: CO isotopologues (J=1-0), dense gas tracers (HCN, HCO⁺). "
            "Continuum: synchrotron, free-free, dust emission. "
            "Facilities: ALMA (Band 3), NOEMA, IRAM 30m, GBT, "
            "VLA (Ka, Q bands), ACTPol, SPTpol (CMB). "
            "Science: molecular gas surveys, ISM structure, galaxy gas content, "
            "star formation laws, magnetic fields, CMB polarization."
        )
        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=reasoning_trace,
            capabilities_used=["line_survey", "continuum_modeling"],
            metadata={"query_type": "GENERAL"}
        )


def create_millimetre_astronomy_domain() -> MillimetreAstronomyDomain:
    return MillimetreAstronomyDomain()
