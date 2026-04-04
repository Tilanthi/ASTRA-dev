"""
Time domain astronomy module for STAN-XI-ASTRO

Specializes in time-domain phenomena including:
- Transient detection and classification
- Variable stars
- Supernovae
- Active galactic nuclei
- Tidal disruption events
"""

import numpy as np
from typing import Dict, List, Any
import logging

from .. import BaseDomainModule, DomainConfig, DomainQueryResult, register_domain, CrossDomainConnection

logger = logging.getLogger(__name__)


class TimeDomainDomain(BaseDomainModule):
    """Domain specializing in time-domain astronomy"""

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="time_domain",
            version="1.0.0",
            dependencies=["astro_physics"],
            keywords=[
                "transient", "variable star", "supernova", "nova", "sn", "agn",
                "quasar", "blazar", "tde", "tidal disruption", "grb",
                "gamma ray burst", "kilanova", "periodic", "eclipsing",
                "cepheid", "rr lyrae", "cataclysmic", "flare", "outburst"
            ],
            task_types=["TRANSIENT_DETECTION", "VARIABLE_STAR_ANALYSIS", "CLASSIFICATION"],
            description="Time-domain phenomena: transients, variables, explosions",
            capabilities=[
                "transient_detection",
                "light_curve_analysis",
                "classification",
                "periodicity_detection",
                "multi_band_modeling",
                "alert_processing",
                "follow_up_coordination"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize time domain astronomy"""
        super().initialize(global_config)

        # Transient types
        self._transient_types = {
            'SN_Ia': 'Type Ia supernova (thermonuclear white dwarf explosion)',
            'SN_II': 'Type II supernova (core-collapse, massive star)',
            'SN_Ib/c': 'Stripped-envelope core-collapse',
            'TDE': 'Tidal disruption event (star disrupted by BH)',
            'GRB': 'Gamma-ray burst (relativistic jet)',
            'KN': 'Kilonova (r-process nucleosynthesis)',
            'AGN_flare': 'AGN variability',
            'CV': 'Cataclysmic variable',
            'YSO': 'Young stellar object variability',
        }

        logger.info("Time domain astronomy initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process time-domain query"""
        query_lower = query.lower()

        if 'supernova' in query_lower or 'sn ' in query_lower:
            return self._process_supernova_query(query, context)
        elif 'transient' in query_lower:
            return self._process_transient_query(query, context)
        elif 'variable' in query_lower or 'period' in query_lower:
            return self._process_variable_star_query(query, context)
        elif 'grb' in query_lower or 'gamma ray' in query_lower:
            return self._process_grb_query(query, context)
        else:
            return self._process_general_time_domain_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_supernova_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process supernova query"""
        reasoning_trace = ["Processing supernova query"]

        answer = (
            "Supernovae are luminous stellar explosions: Type Ia (thermonuclear "
            "WD explosion, standardizable, used as distance indicators), Type II "
            "(core-collapse of massive stars >8 M☉, show hydrogen), Type Ib/c "
            "(stripped-envelope core-collapse). SN light curves rise in days-weeks "
            "and decline over months. Spectra reveal composition (H, He, Si, Ca). "
            "SN Ia cosmology led to discovery of dark energy."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["light_curve_analysis", "classification"]
        )

    def _process_transient_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process transient query"""
        reasoning_trace = ["Processing transient query"]

        answer = (
            "Time-domain surveys (ZTF, ATLAS, LSST) discover transients: "
            "supernovae, GRBs, TDEs, AGN flares, variable stars. Classification "
            "uses light curves (rise time, decline rate, colors), spectra (features, "
            "evolution), and host galaxy properties. Real-time alerts enable rapid "
            "follow-up for multi-wavelength/multi-messenger observations."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["transient_detection", "alert_processing"]
        )

    def _process_variable_star_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process variable star query"""
        reasoning_trace = ["Processing variable star query"]

        answer = (
            "Variable stars include: pulsating variables (Cepheids, RR Lyrae - "
            "period-luminosity relation), eclipsing binaries (periodic dips), "
            "rotating variables (starspots), eruptive variables (flare stars). "
            "Period analysis (Fourier, Lomb-Scargle) reveals periodicities. "
            "Cepheids are crucial distance indicators calibrating the cosmic distance scale."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["periodicity_detection", "light_curve_analysis"]
        )

    def _process_grb_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process GRB query"""
        reasoning_trace = ["Processing GRB query"]

        answer = (
            "Gamma-ray bursts are brief, intense gamma-ray flashes: long GRBs "
            "(>2 s, core-collapse supernovae, collapsars) and short GRBs "
            "(<2 s, compact binary mergers, kilonovae, GW170817 association). "
            "Afterglows (X-ray, optical, radio) result from interaction with "
            "circumburst material. Redshifts span z=0.009 to z=9.4, making them "
            "probes of the early universe."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["classification", "multi_band_modeling"]
        )

    def _process_general_time_domain_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process general time-domain query"""
        reasoning_trace = ["Processing general time-domain query"]

        answer = (
            "Time-domain astronomy studies variable and transient phenomena. "
            "Observational facilities: ZTF, ATLAS, LSST (optical), Swift "
            "(X-ray/UV), Fermi (gamma-ray), LIGO/Virgo (GW). Scientific goals: "
            "expansion history (SN Ia), compact object evolution (GRBs, TDEs), "
            "stellar structure (pulsating stars), and discovery of the unknown "
            "(new classes of transients)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=reasoning_trace,
            capabilities_used=self.config.capabilities[:3]
        )

    def discover_cross_domain_connections(self, other_domains: List['BaseDomainModule']) -> List['CrossDomainConnection']:
        """Discover connections to other domains"""
        connections = super().discover_cross_domain_connections(other_domains)

        for other_domain in other_domains:
            other_name = other_domain.config.domain_name

            if 'gravitational' in other_name or 'gw' in other_name:
                connection = CrossDomainConnection(
                    source_domain=self.config.domain_name,
                    target_domain=other_name,
                    connection_type="multi_messenger",
                    strength=0.85,
                    description="GW triggers electromagnetic follow-up"
                )
                connections.append(connection)

        return connections


register_domain(TimeDomainDomain)
