"""
Radio Galactic Astronomy Domain Module for STAN-XI-ASTRO

Specializes in radio astronomical observations of the Milky Way:
- Galactic synchrotron emission
- Supernova remnants
- Pulsars and radio transients
- Galactic HI structure and dynamics
- Radio recombination lines
- Star-forming regions in radio
- Galactic center at radio wavelengths
- Magnetospheres and radio stars

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


@register_domain
class RadioGalacticDomain(BaseDomainModule):
    """
    Domain specializing in radio galactic astronomy

    Handles radio observations of Milky Way sources including SNRs,
    pulsars, masers, star formation, and Galactic structure.
    """

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        """Return default configuration for radio galactic domain"""
        return DomainConfig(
            domain_name="radio_galactic",
            version="1.0.0",
            dependencies=["astro_physics", "ism", "star_formation"],
            keywords=[
                # SNRs
                "supernova remnant", "snr", "radio snr", "shell", "plerion",
                "crab", "cassiopeia a", "tycho", "kepler", "sn 1006",
                # Pulsars
                "pulsar", "radio pulsar", "magnetar", "rrat", "fast radio burst",
                "frb", "pulsar timing", "dispersion measure", "pulsar wind nebula",
                # Masers
                "maser", "oh maser", "h2o maser", "ch3oh maser", "megalaser",
                "star-forming maser", "evolved star maser",
                # HI in Galaxy
                "galactic hi", "hi structure", "hi map", "per/tay association",
                "galactic rotation", "hi hole", "hi shell", "hi self-absorption",
                # Radio continuum
                "galactic synchrotron", "radio spur", "north polar spur",
                "galactic ridge", "non-thermal emission", "cosmic ray electron",
                # Recombination lines
                "radio recombination line", "rrl", "carbon rr", "hydrogen rr",
                # Galactic center
                "sgr a*", "galactic center radio", "sgr a", "radio arc",
                "non-thermal filaments", "gc magnetosphere",
                # Radio stars
                "radio star", "flare star", "binary radio", "rs cvn",
                # General
                "galactic radio", "milky way radio", "galactic plane survey"
            ],
            task_types=[
                "SNR_ANALYSIS",
                "PULSAR_ANALYSIS",
                "MASER_ANALYSIS",
                "GALACTIC_HI",
                "RRL_ANALYSIS",
                "GC_RADIO"
            ],
            description="Radio astronomy of the Milky Way galaxy",
            capabilities=[
                "snr_classification",
                "pulsar_timing",
                "maser_magnitude",
                "hi_kinematics",
                "rrl_temperature",
                "gc_imaging",
                "radio_morphology"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize radio galactic domain"""
        super().initialize(global_config)

        # Galactic parameters
        self._galactic_params = {
            'R0': 8.15,  # Galactocentric distance (kpc)
            'v0': 220,  # Circular velocity (km/s)
            'z0': 0.1,  # Scale height of thin disk (kpc)
            'HI_scale_height': 0.15  # HI scale height (kpc)
        }

        logger.info("Radio Galactic domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process radio galactic query"""
        query_lower = query.lower()

        if 'snr' in query_lower or 'supernova' in query_lower:
            return self._process_snr_query(query, context)
        elif 'pulsar' in query_lower or 'frb' in query_lower:
            return self._process_pulsar_query(query, context)
        elif 'maser' in query_lower:
            return self._process_maser_query(query, context)
        elif 'hi' in query_lower and 'galactic' in query_lower:
            return self._process_galactic_hi_query(query, context)
        elif 'rrl' in query_lower or 'recombination line' in query_lower:
            return self._process_rrl_query(query, context)
        elif 'gc' in query_lower or 'galactic center' in query_lower or 'sgr' in query_lower:
            return self._process_gc_query(query, context)
        else:
            return self._process_general_radio_galactic_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_snr_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process supernova remnant query"""
        reasoning_trace = ["Processing SNR query"]

        answer = (
            "Radio SNRs classified by morphology: shell-like (e.g., Kepler, Tycho), "
            "plerionic/Crab-like (filled-center, e.g., Crab, 3C58), and composite. "
            "Spectral index α ~ -0.5 for shells, α ~ -0.3 to -0.4 for plerions. "
            "Surface brightness-to-diameter (Σ-D) relation estimates distance: "
            "Σ ∝ D^{-β} with β ~ 2-3. Radio emission from synchrotron: "
            "cosmic ray electrons accelerated at shock via Fermi mechanism. "
            "Galactic SNR rate ~ 2-3 per century. ~380 known Galactic SNRs."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.92,
            reasoning_trace=reasoning_trace,
            capabilities_used=["snr_classification", "radio_morphology"],
            metadata={"query_type": "SNR_ANALYSIS"}
        )

    def _process_pulsar_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process pulsar query"""
        reasoning_trace = ["Processing pulsar query"]

        answer = (
            "Pulsars are rotating neutron stars emitting beams of radio emission. "
            "Periods: 1.4 ms to ~12 s. Timing: P(t) = P₀ + Ṗt with Ṗ ~ 10^{-15} to 10^{-11}. "
            "Characteristic age: τ = P/(2Ṗ) ~ 10⁶-10¹⁰ years. Magnetic field: "
            "B ~ 3.2×10¹⁹√(PṖ) G. Dispersion measure: DM = ∫ nₑ dl [pc cm⁻³] "
            "gives distance and IGM electron density. FRBs: millisecond bursts, "
            "DM ~ 100-3000 pc cm⁻³, some repeating. Pulsar timing arrays test "
            "nanohertz gravitational waves via PTAs (NANOGrav, EPTA, PPTA)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["pulsar_timing"],
            metadata={"query_type": "PULSAR_ANALYSIS"}
        )

    def _process_maser_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process maser query"""
        reasoning_trace = ["Processing maser query"]

        answer = (
            "Masers are microwave stimulated emission from molecular transitions. "
            "OH masers: 1.665, 1.667 GHz (main lines), 1.61, 1.72 GHz (satellite). "
            "Associated with evolved stars (OH/IR stars) and star formation (type II). "
            "H₂O maser: 22.235 GHz, traces outflows, accretion disks, megamasers "
            "in AGN. CH₃OH masers: 6.7 GHz (class II), 12.2 GHz, star-forming regions. "
            "SiO masers: 43, 86 GHz, evolved star envelopes. Masers probe "
            "magnetic fields via Zeeman splitting, kinematics via VLBI, "
            "and excitation conditions (T, n)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["maser_magnitude"],
            metadata={"query_type": "MASER_ANALYSIS"}
        )

    def _process_galactic_hi_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process Galactic HI query"""
        reasoning_trace = ["Processing Galactic HI query"]

        answer = (
            "Galactic HI traced by 21cm line: T_b ∝ (1 - e^{-τ}) T_s (1 - T_bg/T_s). "
            "Structure: spiral arms (Perseus, Sagittarius, Scutum-Centaurus, Norma), "
            "HI holes from stellar feedback, self-absorption from cold neutral medium. "
            "Rotation curve: v(R) from Doppler: v(R) = v_LSR + (R₀/R)(v_LSR - v_sun). "
            "HI scale height ~150 pc, flares with radius. HI mass ~ 5×10⁹ M☉, "
            "~1% of Galactic baryons. Major surveys: VGPS, THOR, GASKAP, "
            "and upcoming SKA-GAL."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["hi_kinematics"],
            metadata={"query_type": "GALACTIC_HI"}
        )

    def _process_rrl_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process radio recombination line query"""
        reasoning_trace = ["Processing RRL query"]

        answer = (
            "Radio recombination lines: transitions between high-n Rydberg states, "
            "ν ∝ 1/n³ (hydrogen-like). Lines: Hnα (Δn=1), Hnβ (Δn=2), etc. "
            "Frequencies: ~500 MHz to ~100 GHz. Line width: thermal (Δν ~ 20 km/s), "
            "pressure broadened, stimulated emission. Optical depth τ < 0.1 typically. "
            "Electron temperature: T_e ∝ (T_L/T_C)^{-1} for LTE. Carbon RRLs trace "
            "photodissociation regions (C⁺). Applications: ionized gas temperature, "
            "EM, kinematics, abundance gradients. Major surveys: GLOSTAR, WISH."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["rrl_temperature"],
            metadata={"query_type": "RRL_ANALYSIS"}
        )

    def _process_gc_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process Galactic Center query"""
        reasoning_trace = ["Processing Galactic Center query"]

        answer = (
            "Sgr A* is our Galaxy's central supermassive black hole, M = 4.1×10⁶ M☉, "
            "D = 8.15 kpc. Radio emission: 10-100 mJy at GHz, variable on minutes-hours. "
            "Size: < 10 R_s at 1.3 mm (EHT). Non-thermal filaments: Radio Arc, "
            "G0.18-0.41, G359.1-0.5 with ordered B-fields. Sgr A complex: SNR Sgr A East, "
            "Sgr A West (mini-spiral HII). G1 and G2 clouds: tidal disruption events. "
            "Radio imaging: VLA, ALMA, EHT. Polarimetry: B-fields ~ mG in filaments, "
            "ordered near Sgr A*."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["gc_imaging"],
            metadata={"query_type": "GC_RADIO"}
        )

    def _process_general_radio_galactic_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process general radio galactic query"""
        reasoning_trace = ["Processing general radio galactic query"]

        answer = (
            "Radio galactic astronomy studies Milky Way emission from 10 MHz to 1 THz. "
            "Components: synchrotron (cosmic ray electrons in B-fields), free-free "
            "(HII regions), masers, spectral lines (21cm HI, RRLs). Facilities: "
            "VLA (cm), GBT (10 cm - 3 mm), ALMA (mm), LOFAR/MWA/SKA-low (m), "
            "uGMRT (10 cm - 1 m). Galactic plane surveys: VGPS, MAGPIS, THOR, "
            "CORNISH, GLOSTAR. Science: SNR population, pulsar census, magnetism, "
            "star formation feedback, ISM structure, Galactic dynamics, "
            "and time domain (transients)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=reasoning_trace,
            capabilities_used=["radio_morphology"],
            metadata={"query_type": "GENERAL"}
        )


def create_radio_galactic_domain() -> RadioGalacticDomain:
    """Create a radio galactic domain instance"""
    return RadioGalacticDomain()
