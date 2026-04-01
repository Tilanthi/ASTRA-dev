"""
Gravitational waves domain module for STAN-XI-ASTRO

Specializes in gravitational wave astronomy including:
- GW detection and data analysis
- Waveform modeling
- Parameter estimation
- Multi-messenger astronomy
- Compact object astrophysics
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging

from .. import BaseDomainModule, DomainConfig, DomainQueryResult, register_domain, CrossDomainConnection

logger = logging.getLogger(__name__)


class GravitationalWavesDomain(BaseDomainModule):
    """
    Domain specializing in gravitational wave astronomy

    Capabilities:
    - GW signal processing and detection
    - Waveform modeling (inspiral, merger, ringdown)
    - Parameter estimation for compact object mergers
    - Multi-messenger coordination (EM, neutrino)
    - Compact object population synthesis
    """

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="gravitational_waves",
            version="1.0.0",
            dependencies=["astro_physics", "relativity"],
            keywords=[
                "gravitational wave", "gw", "ligo", "virgo", "kagra", "ligo-virgo",
                "black hole merger", "neutron star merger", "compact binary",
                "waveform", "chirp", "inspiral", "merger", "ringdown",
                "multi-messenger", "gamma-ray burst", "kilonova", "bns", "bbh",
                "gravitational waves", "lisa", "space-based", "pulsar timing"
            ],
            task_types=["GW_DETECTION", "WAVEFORM_MODELING", "PARAMETER_ESTIMATION", "MULTI_MESSENGER"],
            description="Gravitational wave detection and compact object merger analysis",
            capabilities=[
                "gw_detection",
                "waveform_modeling",
                "parameter_estimation",
                "multi_messenger_coordination",
                "compact_object_physics",
                "data_analysis",
                "signal_processing",
                "population_inference"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize gravitational waves domain"""
        super().initialize(global_config)

        # Physical constants (CGS)
        self._constants = {
            'G': 6.674e-8,
            'c': 2.998e10,
            'M_sun': 1.989e33,
            'Mpc': 3.086e24,
        }

        # GW detectors
        self._detectors = {
            'LIGO_Hanford': {'sensitivity': '4e-23', 'frequency_range': (10, 5000)},
            'LIGO_Livingston': {'sensitivity': '4e-23', 'frequency_range': (10, 5000)},
            'Virgo': {'sensitivity': '8e-23', 'frequency_range': (20, 5000)},
            'KAGRA': {'sensitivity': '1e-22', 'frequency_range': (20, 5000)},
            'LISA': {'sensitivity': '1e-20', 'frequency_range': (0.0001, 0.1)},
        }

        logger.info("Gravitational waves domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process gravitational wave query"""
        query_lower = query.lower()

        if 'detect' in query_lower or 'sensitivity' in query_lower:
            return self._process_detection_query(query, context)
        elif 'waveform' in query_lower or 'chirp' in query_lower:
            return self._process_waveform_query(query, context)
        elif 'parameter' in query_lower or 'mass' in query_lower:
            return self._process_parameter_query(query, context)
        elif 'multi-messenger' in query_lower or 'kilonova' in query_lower or 'grb' in query_lower:
            return self._process_multi_messenger_query(query, context)
        else:
            return self._process_general_gw_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_detection_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process GW detection query"""
        reasoning_trace = ["Identified GW detection query"]

        answer = (
            "Gravitational wave detectors use laser interferometry to measure "
            "spacetime strain caused by passing GWs. Current ground-based detectors "
            "(LIGO, Virgo, KAGRA) operate in the 10-5000 Hz band and can detect "
            "strain amplitudes of ~10^-22. LISA, a planned space-based detector, "
            "will observe mHz GWs from massive black hole mergers, galactic "
            "binaries, and possibly cosmological sources."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.92,
            reasoning_trace=reasoning_trace,
            capabilities_used=["gw_detection", "signal_processing"]
        )

    def _process_waveform_query(self, str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process waveform modeling query"""
        reasoning_trace = ["Identified waveform query"]

        answer = (
            "GW waveforms have three phases: inspiral (well-modeled by PN theory), "
            "merger (requires numerical relativity), and ringdown (quasi-normal "
            "modes). For BBH systems, waveform models like IMRPhenom and SEOBNR "
            "provide accurate templates across all phases. BNS waveforms include "
            "tidal effects that probe the neutron star equation of state."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["waveform_modeling"]
        )

    def _process_parameter_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process parameter estimation query"""
        reasoning_trace = ["Identified parameter estimation query"]

        params = context.get('parameters', {})

        if 'chirp mass' in query.lower():
            # Chirp mass calculation
            m1 = params.get('m1', 30)  # Solar masses
            m2 = params.get('m2', 30)

            M_c = ((m1 * m2)**(3/5)) / ((m1 + m2)**(1/5))

            answer = (
                f"The chirp mass M_c = {(m1*m2)**(3/5) / (m1+m2)**(1/5):.2f} M☉ "
                f"for equal-mass {m1}+{m1} M☉ binaries. Chirp mass is the "
                f"mass parameter most precisely measured from GW observations, "
                f"determining the inspiral rate."
            )

            return DomainQueryResult(
                domain_name=self.config.domain_name,
                answer=answer,
                confidence=0.94,
                reasoning_trace=reasoning_trace + [f"M1={m1}, M2={m2}, Mc={M_c:.2f}"],
                capabilities_used=["parameter_estimation"]
            )

        answer = (
            "GW parameter estimation uses Bayesian inference to extract source "
            "parameters (masses, spins, distance, inclination, sky location) from "
            "the detected signal. Chirp mass is measured most precisely, followed "
            "by mass ratio and effective spin. Distance measurements are "
            "degenerate with inclination unless breaks from higher harmonics or "
            "precession are present."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["parameter_estimation"]
        )

    def _process_multi_messenger_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process multi-messenger query"""
        reasoning_trace = ["Identified multi-messenger query"]

        answer = (
            "Multi-messenger astronomy combines GWs with electromagnetic "
            "counterparts (gamma-ray bursts, kilonovae, afterglows), neutrinos, "
            "and cosmic rays. GW170817 marked the first BNS merger detected in GWs "
            "and EM radiation, confirming that BNS mergers produce heavy elements "
            "via r-process nucleosynthesis and serve as the engines of short GRBs."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.93,
            reasoning_trace=reasoning_trace,
            capabilities_used=["multi_messenger_coordination"]
        )

    def _process_general_gw_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process general GW query"""
        reasoning_trace = ["Processing general GW query"]

        answer = (
            "Gravitational wave astronomy studies ripples in spacetime from "
            "accelerating masses. Current ground-based detectors (LIGO, Virgo, "
            "KAGRA) detect GWs from merging compact objects in the 10-5000 Hz band. "
            "Over 90 GW events have been detected, including BBH mergers, BNS mergers, "
            "and NSBH mergers. These observations constrain stellar evolution, "
            "compact object populations, nuclear physics, and cosmology."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=self.config.capabilities[:3]
        )

    def discover_cross_domain_connections(
        self,
        other_domains: List['BaseDomainModule']
    ) -> List['CrossDomainConnection']:
        """Discover connections to other domains"""
        connections = super().discover_cross_domain_connections(other_domains)

        for other_domain in other_domains:
            other_name = other_domain.config.domain_name

            if 'relativ' in other_name or 'cosmolog' in other_name:
                connection = CrossDomainConnection(
                    source_domain=self.config.domain_name,
                    target_domain=other_name,
                    connection_type="essential_dependency",
                    strength=0.95,
                    description="GWs require GR and inform cosmology"
                )
                connections.append(connection)

            if 'neutrino' in other_name or 'electromagnet' in other_name:
                connection = CrossDomainConnection(
                    source_domain=self.config.domain_name,
                    target_domain=other_name,
                    connection_type="multi_messenger",
                    strength=0.85,
                    description="Multi-messenger coordination"
                )
                connections.append(connection)

        return connections


register_domain(GravitationalWavesDomain)
