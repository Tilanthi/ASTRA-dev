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
Radio Extragalactic Astronomy Domain Module for STAN-XI-ASTRO

Specializes in radio astronomical observations of extragalactic sources:
- Radio galaxies and AGN
- Radio-loud quasars
- Galaxy clusters (SZ effect, radio halos/relics)
- Extragalactic radio surveys
- HI imaging of external galaxies
- VLBI observations of distant sources
- Cosmic magnetism studies
- Epoch of Reionization (21cm)

Date: 2026-03-20
Version: 1.0.0
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Import base domain module
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

# Physical constants
C = 2.998e10  # Speed of light (cm/s)
K_B = 1.381e-16  # Boltzmann constant (erg/K)
HI_LINE_FREQ = 1.42040575177e9  # 21cm line (Hz)


@register_domain
class RadioExtragalacticDomain(BaseDomainModule):
    """
    Domain specializing in radio extragalactic astronomy

    Handles radio observations of galaxies, AGN, clusters, and the
    distant universe including HI surveys, continuum observations,
    and cosmological radio studies.
    """

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        """Return default configuration for radio extragalactic domain"""
        return DomainConfig(
            domain_name="radio_extragalactic",
            version="1.0.0",
            dependencies=["astro_physics", "extragalactic", "cosmology"],
            keywords=[
                # Radio sources
                "radio galaxy", "radio quasar", "blazar", "agn jet", "radio lobe",
                "radio core", "synchrotron", "spectral index", "curvature",
                # Galaxy clusters
                "sunyaev-zeldovich", "sz effect", "radio halo", "radio relic",
                "cluster radio", "diffuse radio",
                # HI observations
                "21cm", "hi imaging", "hi survey", "neutral hydrogen",
                "tis", "hi mass", "hi deficiency", "gas accretion",
                # VLBI and high resolution
                "vlbi", "vlbi mas", "very long baseline", "radio interferometry",
                "brightness temperature", "proper motion", "parallax",
                # Surveys
                "first", "nvss", "wiss", "lofar", "askap", "emu survey",
                "apertif", "meerkat", "ska", "radio survey",
                # Cosmology
                "epoch of reionization", "eor", "21cm cosmology", "dark ages",
                "global signal", "power spectrum", "tomography",
                # Magnetism
                "cosmic magnetism", "faraday rotation", "rm synthesis",
                "magnetic field", "faraday tomography",
                # General
                "extragalactic radio", "distant radio source", "high-z radio"
            ],
            task_types=[
                "RADIO_SOURCE_ANALYSIS",
                "HI_IMAGING",
                "SZ_MEASUREMENT",
                "VLBI_ANALYSIS",
                "EOR_STUDIES",
                "MAGNETISM_ANALYSIS"
            ],
            description="Radio astronomy of extragalactic sources, AGN, clusters, and cosmology",
            capabilities=[
                "radio_source_classification",
                "hi_mass_measurement",
                "sz_effect_analysis",
                "vlbi_imaging",
                "eor_power_spectrum",
                "faraday_rotation_analysis",
                "synchrotron_modeling",
                "radio_luminosity_calculation"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize radio extragalactic domain"""
        super().initialize(global_config)

        # Radio survey parameters
        self._surveys = {
            'NVSS': {'freq': 1.4e9, 'resolution': 45, 'depth': 2.5e-3},
            'FIRST': {'freq': 1.4e9, 'resolution': 5, 'depth': 1e-3},
            'LOFAR': {'freq': 150e6, 'resolution': 6, 'depth': 1e-5},
            'ASKAP/EMU': {'freq': 1.4e9, 'resolution': 10, 'depth': 1e-5},
            ' MeerKAT': {'freq': 1.4e9, 'resolution': 8, 'depth': 1e-5},
            'SKA1-MID': {'freq': 1.4e9, 'resolution': 1.5, 'depth': 1e-7},
            'SKA1-LOW': {'freq': 100e6, 'resolution': 3, 'depth': 1e-6}
        }

        logger.info("Radio Extragalactic domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process radio extragalactic query"""
        query_lower = query.lower()

        if 'hi' in query_lower or '21cm' in query_lower:
            return self._process_hi_query(query, context)
        elif any(kw in query_lower for kw in ['sz', 'sunyaev', 'cluster']):
            return self._process_sz_query(query, context)
        elif any(kw in query_lower for kw in ['vlbi', 'mas', 'baseline']):
            return self._process_vlbi_query(query, context)
        elif any(kw in query_lower for kw in ['eor', 'reionization', '21cm cosm']):
            return self._process_eor_query(query, context)
        elif any(kw in query_lower for kw in ['faraday', 'rotation', 'magnet']):
            return self._process_magnetism_query(query, context)
        elif any(kw in query_lower for kw in ['radio galaxy', 'agn', 'jet', 'lobe']):
            return self._process_radio_source_query(query, context)
        else:
            return self._process_general_radio_extragalactic_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_hi_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process HI-related query"""
        reasoning_trace = ["Processing HI imaging query"]

        answer = (
            "HI observations at 21cm (1.42 GHz) trace neutral hydrogen in galaxies. "
            "Key measurements: HI mass (M_HI = 2.356×10⁵ M☉ D² ∫S dv [M☉]), "
            "velocity field for kinematics, HI extent, and gas deficiency. "
            "Major surveys: ALFALFA (Arecibo), HIPASS (Parkes), WALLABY (ASKAP), "
            "and upcoming SKA shallow/deep surveys. HI studies reveal gas accretion, "
            "ram pressure stripping, and cosmic HI mass function evolution."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.92,
            reasoning_trace=reasoning_trace,
            capabilities_used=["hi_mass_measurement"],
            metadata={"query_type": "HI_IMAGING"}
        )

    def _process_sz_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process Sunyaev-Zeldovich effect query"""
        reasoning_trace = ["Processing SZ effect query"]

        answer = (
            "The Sunyaev-Zeldovich effect is CMB distortion by inverse Compton scattering "
            "off hot electrons in galaxy clusters. Thermal SZ: ΔT/T₀ = -2y at low freq, "
            "ΔT/T₀ = +y at high freq (null at 217 GHz). Compton y-parameter: "
            "y = ∫(kTₑ/mₑc²) nₑ σ_T dl. Kinetic SZ probes cluster peculiar velocity. "
            "SZ is redshift-independent, enabling cluster discovery to high-z. "
            "Surveys: SPT, ACT, Planck, and upcoming SPT-3G, Simons Observatory."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.93,
            reasoning_trace=reasoning_trace,
            capabilities_used=["sz_effect_analysis"],
            metadata={"query_type": "SZ_MEASUREMENT"}
        )

    def _process_vlbi_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process VLBI-related query"""
        reasoning_trace = ["Processing VLBI query"]

        answer = (
            "Very Long Baseline Interferometry achieves mas-scale resolution. "
            "Earth-scale baselines (VLBA, EVN, GMVA) resolve AGN jets, "
            "blazar cores, and measure proper motions. Space VLBI (RadioAstron) "
            "reaches ~10 μas brightness temperatures: T_b ∝ S/Ω ∝ Sθ². "
            "High-T_b sources require Doppler boosting: T_b,app = δ T_b,int. "
            "Applications: jet collimation, superluminal motion, BH shadow imaging (EHT)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["vlbi_imaging"],
            metadata={"query_type": "VLBI_ANALYSIS"}
        )

    def _process_eor_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process Epoch of Reionization query"""
        reasoning_trace = ["Processing EOR query"]

        answer = (
            "Epoch of Reionization (EoR) studied via 21cm line from z~6-30. "
            "Global signal: brightness temperature δT_b ~ 27(1+δ)(1- xₑ)√[(1+z)/10] "
            "mK relative to CMB. Power spectrum measurements: LOFAR, MWA, GMRT, "
            "HERA, and upcoming SKA-LOW. Challenges: foreground removal (~10⁴× brighter), "
            "ionospheric distortion, beam calibration. Science: timing of reionization, "
            "astrophysics of first sources, x-ray heating, spin temperature coupling."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["eor_power_spectrum"],
            metadata={"query_type": "EOR_STUDIES"}
        )

    def _process_magnetism_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process cosmic magnetism query"""
        reasoning_trace = ["Processing cosmic magnetism query"]

        answer = (
            "Cosmic magnetic fields studied via Faraday rotation: RM = 0.81 ∫ nₑ B_∥ dl [rad/m²]. "
            "RM synthesis: F(ϕ) = ∫ P(λ²) e^{-2iϕλ²} dλ² where ϕ = RM. "
            "Polarized synchrotron reveals B-field orientation: polarization angle "
            "χ = χ₀ + RMλ². Galactic field: ~few μG ordered component. "
            "Extragalactic fields: ~1 μG in galaxy clusters, ~μG in galaxies. "
            "Origins: dynamo amplification vs primordial. SKA will map magnetism "
            "through RM grids of millions of sources."
        )

        return DomainResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["faraday_rotation_analysis"],
            metadata={"query_type": "MAGNETISM_ANALYSIS"}
        )

    def _process_radio_source_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process radio galaxy/AGN query"""
        reasoning_trace = ["Processing radio source query"]

        answer = (
            "Radio-loud AGN classified by morphology: FR I (edge-darkened, lower power), "
            "FR II (edge-brightened, high power with hotspots). Blazars: BL Lac (featureless), "
            "FSRQ (broad lines). Spectral index α: S_ν ∝ ν^α with α ~ -0.7 for optically thin, "
            "α ~ +2.5 for self-absorbed (τ ~ 1 at turnover). Synchrotron peak: ν_peak ∝ Bδ²γ². "
            "Jet physics: Lorentz factor Γ ~ 10-30, Doppler factor δ = 1/[Γ(1-βcosθ)]. "
            "Blandford-Znajek mechanism extracts BH spin energy."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["radio_source_classification", "synchrotron_modeling"],
            metadata={"query_type": "RADIO_SOURCE_ANALYSIS"}
        )

    def _process_general_radio_extragalactic_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process general radio extragalactic query"""
        reasoning_trace = ["Processing general radio extragalactic query"]

        answer = (
            "Radio extragalactic astronomy studies the distant universe at radio wavelengths. "
            "Key facilities: VLA, ALMA, LOFAR, MeerKAT, ASKAP, KAT-7, GMRT, uGMRT, "
            "and upcoming SKA. Wavelengths from meter (low-freq arrays) to sub-mm (ALMA). "
            "Science includes: AGN physics, galaxy evolution via radio luminosity function, "
            "star formation (radio-FIR correlation), cluster physics (SZ effect, halos), "
            "cosmic magnetism, and reionization. Radio advantages: dust penetration, "
            "redshift-independent, high angular resolution (VLBI), and time domain capabilities."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.85,
            reasoning_trace=reasoning_trace,
            capabilities_used=["radio_luminosity_calculation"],
            metadata={"query_type": "GENERAL"}
        )


# Factory function
def create_radio_extragalactic_domain() -> RadioExtragalacticDomain:
    """Create a radio extragalactic domain instance"""
    return RadioExtragalacticDomain()


# Fix typo in _process_magnetism_query
DomainResult = DomainQueryResult
