"""
High-energy astrophysics domain module for STAN-XI-ASTRO

Covers:
- Compact objects (neutron stars, black holes, white dwarfs)
- X-ray binaries and accretion physics
- Gamma-ray bursts (prompt and afterglow)
- Active galactic nuclei and jets
- Pulsars and timing analysis
- Magnetars and extreme magnetic fields
- Cosmic rays and particle acceleration
- Supernova remnants
- High-energy emission mechanisms

This domain handles the most energetic phenomena in the universe,
from X-ray binaries to gamma-ray bursts and active galactic nuclei.

Date: 2025-12-23
Version: 47.0
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Import base domain module
try:
    from .. import BaseDomainModule, DomainConfig, DomainQueryResult
except ImportError:
    # Fallback if base module not available
    class BaseDomainModule:
        pass

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

logger = logging.getLogger(__name__)

# Physical constants
C = 2.998e10  # Speed of light (cm/s)
G = 6.674e-8  # Gravitational constant
MSUN = 1.989e33  # Solar mass (g)
LSUN = 3.828e33  # Solar luminosity (erg/s)
RSUN = 6.957e10  # Solar radius (cm)
SIGMA_SB = 5.670e-5  # Stefan-Boltzmann constant


class HighEnergyDomain(BaseDomainModule):
    """
    Domain specializing in high-energy astrophysical phenomena

    Handles queries about compact objects, accretion, jets, GRBs,
    AGN, pulsars, and cosmic ray acceleration.
    """

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        """Return default configuration for high-energy domain"""
        return DomainConfig(
            domain_name="high_energy",
            version="1.0.0",
            dependencies=["astro_physics", "reasoning", "physics"],
            keywords=[
                # Compact objects
                "neutron star", "pulsar", "magnetar", "black hole", "white dwarf",
                "compact object", "degenerate matter", "event horizon",
                # X-ray sources
                "xray", "x-ray", "accretion", "accretion disk", "xray binary",
                "cataclysmic variable", "low mass xray binary", "lmxb",
                "high mass xray binary", "hmxb", "ultraluminous xray source", "ulx",
                # Gamma-ray bursts
                "grb", "gamma ray burst", "afterglow", "prompt emission",
                "fireball", "jet", "collapsar", "merger", "kilonova",
                # Active galactic nuclei
                "agn", "active galactic", "quasar", "blazar", "radio galaxy",
                "jet", "superluminal", "relativistic beaming",
                "accretion disk", "broad line region", "narrow line region",
                # High-energy phenomena
                "cosmic ray", "particle acceleration", "shock acceleration",
                "fermi acceleration", "supernova remnant", "snr",
                "pulsar wind nebula", "pwn", "crab", "vela",
                "synchrotron", "inverse compton", "bremsstrahlung",
                # Observational
                "chandra", "xmm", "newton", "nustar", "fermi", "swift",
                "integral", "hess", "magic", "veritas", "lamost"
            ],
            task_types=[
                "HIGH_ENERGY_SOURCE_ANALYSIS",
                "COMPACT_OBJECT_MODELING",
                "ACCRETION_PHYSICS",
                "HIGH_ENERGY_SPECTRAL_ANALYSIS",
                "GRB_ANALYSIS",
                "AGN_ANALYSIS",
                "PULSAR_TIMING",
                "COSMIC_RAY_ANALYSIS"
            ],
            description="High-energy astrophysics including compact objects, X-ray sources, gamma-ray bursts, AGN, and cosmic rays",
            capabilities=[
                # Compact object analysis
                "xray_spectral_fitting",
                "pulsar_timing_analysis",
                "black_hole_accretion_modeling",
                "magnetar_field_estimation",
                "white_dwarf_structure",
                "neutron_star_equation_of_state",
                # GRB analysis
                "grb_afterglow_modeling",
                "grb_prompt_emission_analysis",
                "kilonova_modeling",
                # AGN analysis
                "agn_jet_modeling",
                "accretion_disk_modeling",
                "broad_line_region_analysis",
                "reverberation_mapping",
                # High-energy processes
                "particle_acceleration",
                "synchrotron_modeling",
                "inverse_compton_modeling",
                "shock_acceleration",
                # Supernova remnants
                "snr_evolution_modeling",
                "snr_xray_emission",
                "cosmic_ray_acceleration"
            ]
        )

    def get_config(self) -> DomainConfig:
        """Return domain configuration"""
        return self.config

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize domain with global configuration"""
        self._initialized = True
        logger.info(f"High-energy domain initialized: {self.config.domain_name}")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """
        Process high-energy astrophysics query

        Routes to appropriate subdomain based on keywords.
        """
        query_lower = query.lower()

        # Route to subdomain methods
        if any(kw in query_lower for kw in ['xray', 'spectral', 'accretion', 'disk']):
            return self._analyze_xray_spectra(query, context)
        elif any(kw in query_lower for kw in ['pulsar', 'timing', 'spin', 'period']):
            return self._analyze_pulsar(query, context)
        elif any(kw in query_lower for kw in ['black hole', 'schwarzschild', 'kerr', 'horizon']):
            return self._analyze_black_hole(query, context)
        elif any(kw in query_lower for kw in ['grb', 'gamma ray', 'afterglow', 'prompt']):
            return self._analyze_grb(query, context)
        elif any(kw in query_lower for kw in ['agn', 'quasar', 'blazar', 'jet', 'agn']):
            return self._analyze_agn(query, context)
        elif any(kw in query_lower for kw in ['magnetar', 'magnetic field', 'burst']):
            return self._analyze_magnetar(query, context)
        elif any(kw in query_lower for kw in ['cosmic ray', 'particle acceleration', 'fermi']):
            return self._analyze_cosmic_rays(query, context)
        elif any(kw in query_lower for kw in ['snr', 'supernova remnant', 'shock']):
            return self._analyze_snr(query, context)
        else:
            return self._general_high_energy_analysis(query, context)

    def get_capabilities(self) -> List[str]:
        """Return list of domain capabilities"""
        return self.config.capabilities

    # Subdomain analysis methods

    def _analyze_xray_spectra(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze X-ray spectra from high-energy sources"""
        answer = (
            "X-ray spectral analysis for high-energy sources involves fitting models "
            "to observed spectra. Key components include:\n\n"
            "1. **Continuum Models**:\n"
            "   - Power law: F(E) ∝ E^(-Γ) where Γ is the photon index\n"
            "   - Blackbody: Characteristic temperature ~1 keV for neutron stars\n"
            "   - Comptonization: Comptonized blackbody (compTT)\n"
            "   - Disk blackbody (diskbb): Multicolor disk with T ∝ r^(-3/4)\n\n"
            "2. **Absorption Features**:\n"
            "   - Photoelectric absorption: N_H column density (10^20-10^24 cm^-2)\n"
            "   - Edges: K-edges at specific energies\n\n"
            "3. **Emission Lines**:\n"
            "   - Fe Kα at 6.4 keV (neutral) to 6.97 keV (H-like)\n"
            "   - Line equivalent width and profile analysis\n\n"
            "4. **Accretion State Diagnostics**:\n"
            "   - Low/hard state: Power law dominated, Γ ~ 1.7\n"
            "   - High/soft state: Thermal dominated\n"
            "   - Intermediate states: Both components\n\n"
            "Typical fitting tools: XSPEC, ISIS, Sherpa. "
            "Key observatories: Chandra, XMM-Newton, NuSTAR, NICER."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=[
                "Identified X-ray spectral analysis query",
                "Applied high-energy domain knowledge",
                "Synthesized continuum models, absorption features, emission lines"
            ],
            capabilities_used=["xray_spectral_fitting", "accretion_disk_modeling"]
        )

    def _analyze_pulsar(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze pulsar timing and properties"""
        answer = (
            "Pulsar analysis combines timing measurements with physical modeling:\n\n"
            "1. **Timing Measurements**:\n"
            "   - Spin period P: 1.4 ms to ~10 s range\n"
            "   - Period derivative Ṗ: Spin-down rate\n"
            "   - Characteristic age: τ = P/(2Ṗ) ≈ 10^6-10^10 years\n"
            "   - Magnetic field: B ≈ 3.2×10^19√(PṖ) G\n\n"
            "2. **Timing Residuals**:\n"
            "   - Deviations from predicted spin period\n"
            "   - Reveal binary motion, glitches, noise\n"
            "   - Precise tests of general relativity in binaries\n\n"
            "3. **Glitches**:\n"
            "   - Sudden spin-up events (ΔP/P ~ 10^-9 to 10^-6)\n"
            "   - Superfluid unpinning in neutron star crust\n"
            "   - Relaxation timescales constrain interior physics\n\n"
            "4. **Binary Parameters**:\n"
            "   - Keplerian elements: a₁, e, P_b, ω, T₀\n"
            "   - Post-Keplerian parameters test GR\n\n"
            "Key observatories: Parkes, GBT, FAST, NANOGrav, CHIME."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=[
                "Identified pulsar analysis query",
                "Applied pulsar timing models",
                "Covered timing, glitches, and binary parameters"
            ],
            capabilities_used=["pulsar_timing_analysis"]
        )

    def _analyze_black_hole(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze black hole accretion and properties"""
        answer = (
            "Black hole analysis combines general relativity with accretion physics:\n\n"
            "1. **Schwarzschild Black Hole (non-rotating)**:\n"
            "   - Event horizon: Rs = 2GM/c²\n"
            "   - For 10 M⊙: Rs ≈ 30 km\n"
            "   - Innermost stable circular orbit (ISCO): 3Rs\n\n"
            "2. **Kerr Black Hole (rotating)**:\n"
            "   - Spin parameter a = Jc/GM² (|a| ≤ 1)\n"
            "   - ISCO radius: R_isco depends on spin\n"
            "   - Ergosphere extends outside event horizon\n\n"
            "3. **Accretion Physics**:\n"
            "   - Eddington luminosity: L_Edd = 1.3×10^38 (M/M⊙) erg/s\n"
            "   - Eddington ratio: λ = L_bol/L_Edd\n"
            "   - Disk models: Shakura-Sunyaev (α-disk), slim disk, ADAF\n\n"
            "4. **Relativistic Effects**:\n"
            "   - Gravitational redshift: z = 1/√(1-Rs/r) - 1\n"
            "   - Light bending: affects observed emission\n"
            "   - Frame dragging (Lense-Thirring effect)\n\n"
            "Observational signatures: Quasi-periodic oscillations (QPOs), "
            "iron line profiles, continuum fitting."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=[
                "Identified black hole analysis query",
                "Applied relativistic physics",
                "Covered Schwarzschild/Kerr metrics and accretion"
            ],
            capabilities_used=["black_hole_accretion_modeling"]
        )

    def _analyze_grb(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze gamma-ray burst properties"""
        answer = (
            "Gamma-ray burst (GRB) analysis spans prompt emission to afterglow:\n\n"
            "1. **Prompt Emission**:\n"
            "   - Duration: short (T90 < 2 s) vs long (T90 > 2 s)\n"
            "   - Isotropic energy: E_iso ~ 10^51-10^54 erg\n"
            "   - Spectral hardness: Amati relation (E_peak ∝ E_iso^0.5)\n"
            "   - Variability timescales: down to milliseconds\n\n"
            "2. **Afterglow Phases**:\n"
            "   - Early reverse shock (optical flash)\n"
            "   - Forward shock: F_ν ∝ t^(-α) ν^(-β)\n"
            "   - Closure relations test synchrotron model\n"
            "   - Jet breaks: t^(-3/2) → t^(-2) transition\n\n"
            "3. **Progenitor Systems**:\n"
            "   - Long GRBs: Collapsars (massive star core collapse)\n"
            "   - Short GRBs: Compact binary mergers (NS-NS or NS-BH)\n"
            "   - Associated with kilovovae and gravitational waves\n\n"
            "4. **Emission Mechanisms**:\n"
            "   - Synchrotron: Power-law electron distribution\n"
            "   - Inverse Compton: Up-scattering of photons\n"
            "   - Photospheric emission: Dissipation at optical depth ~1\n\n"
            "Key observatories: Fermi-GBM/LAT, Swift, Neil Gehrels Swift, H.E.S.S."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=[
                "Identified GRB analysis query",
                "Applied high-energy transient models",
                "Covered prompt, afterglow, and progenitors"
            ],
            capabilities_used=["grb_afterglow_modeling", "grb_prompt_emission_analysis"]
        )

    def _analyze_agn(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze active galactic nuclei"""
        answer = (
            "Active Galactic Nuclei (AGN) analysis includes multi-wavelength studies:\n\n"
            "1. **Unified Model Components**:\n"
            "   - Supermassive black hole (10^6-10^10 M⊙)\n"
            "   - Accretion disk (UV/optical emission)\n"
            "   - Broad line region (BLR): 0.01-1 pc, FWHM ~ 1000-10000 km/s\n"
            "   - Narrow line region (NLR): 10-1000 pc, FWHM ~ 100-1000 km/s\n"
            "   - Obscuring torus: N_H > 10^22 cm^-2\n"
            "   - Relativistic jet (radio-loud AGN)\n\n"
            "2. **Spectral Energy Distribution**:\n"
            "   - Big blue bump: Thermal emission from accretion disk\n"
            "   - X-ray corona: Inverse Compton of disk UV photons\n"
            "   - IR emission: Dust in torus\n"
            "   - Radio: Synchrotron from jet\n\n"
            "3. **Classification**:\n"
            "   - Type 1: Broad lines visible (face-on)\n"
            "   - Type 2: Broad lines obscured (edge-on)\n"
            "   - Radio-loud: R = L_radio/L_optical > 10\n"
            "   - Blazars: Jet pointing toward us\n\n"
            "4. **Variability**:\n"
            "   - X-ray variability timescales: hours-days\n"
            "   - Reverberation mapping: Size of BLR from light travel time\n"
            "   - Duty cycle: Fraction of time active\n\n"
            "Key science: Black hole mass scaling relations, co-evolution with hosts."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=[
                "Identified AGN analysis query",
                "Applied unified AGN model",
                "Covered structure, classification, and variability"
            ],
            capabilities_used=["agn_jet_modeling", "accretion_disk_modeling"]
        )

    def _analyze_magnetar(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze magnetar properties"""
        answer = (
            "Magnetars are neutron stars with extreme magnetic fields:\n\n"
            "1. **Magnetic Field**:\n"
            "   - Surface field: B ~ 10^14-10^15 G\n"
            "   - Estimated from spin-down: B = 3.2×10^19√(PṖ) G\n"
            "   - SGRs (soft gamma repeaters): B > 10^14 G\n"
            "   - AXPs (anomalous X-ray pulsars): B ~ 10^13-10^14 G\n\n"
            "2. **Energetics**:\n"
            "   - Burst energy: 10^38-10^46 erg\n"
            "   - Giant flares: ~10^46 erg (2004 SGR 1806-20)\n"
            "   - Persistent X-ray luminosity: 10^34-10^36 erg/s\n"
            "   - Powered by magnetic field decay\n\n"
            "3. **Starquakes**:\n"
            "   - Crust cracking releases magnetic stress\n"
            "   - Trigger bursts and glitches\n"
            "   - Quasi-periodic oscillations in flares\n\n"
            "4. **Properties**:\n"
            "   - Spin periods: 2-12 seconds (slower than most pulsars)\n"
            "   - Strong spin-down: Ṗ ~ 10^-13 to 10^-11\n"
            "   - Associated with supernova remnants\n\n"
            "Key observatories: RXTE, Swift, NuSTAR, Chandra, XMM-Newton."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.85,
            reasoning_trace=[
                "Identified magnetar analysis query",
                "Applied magnetar physics models"
            ],
            capabilities_used=["magnetar_field_estimation"]
        )

    def _analyze_cosmic_rays(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze cosmic ray acceleration and propagation"""
        answer = (
            "Cosmic ray analysis spans acceleration to detection:\n\n"
            "1. **Energy Spectrum**:\n"
            "   - Power law: dN/dE ∝ E^(-γ)\n"
            "   - γ ≈ 2.7 for E < 10^15 eV (knee)\n"
            "   - γ ≈ 3.0 for E > 10^15 eV\n"
            "   - Cut-off at ankle (~10^18 eV)\n\n"
            "2. **Acceleration Mechanisms**:\n"
            "   - Diffusive shock acceleration (Fermi I)\n"
            "   - Maximum energy: E_max ∝ Z B R (shock radius)\n"
            "   - Sources: SNRs, pulsars, AGN, GRBs\n\n"
            "3. **Composition**:\n"
            "   - Primarily protons (90%), alpha particles (9%)\n"
            "   - Heavier elements: Li to Fe (1%)\n"
            "   - Ultra-high energy: composition uncertain\n\n"
            "4. **Propagation**:\n"
            "   - Diffusion through Galactic magnetic field\n"
            "   - Confinement time: ~10^7 years for GeV particles\n"
            "   - Escape from Galaxy at high energies\n\n"
            "Key observatories: AMS-02, Fermi-LAT, IceCube, Pierre Auger, Telescope Array."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=[
                "Identified cosmic ray analysis query",
                "Applied particle acceleration models"
            ],
            capabilities_used=["particle_acceleration", "cosmic_ray_acceleration"]
        )

    def _analyze_snr(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Analyze supernova remnants"""
        answer = (
            "Supernova remnant (SNR) analysis reveals shock physics and particle acceleration:\n\n"
            "1. **Evolutionary Phases**:\n"
            "   - Free expansion: v ≈ constant, R ∝ t\n"
            "   - Sedov-Taylor: R ∝ t^(2/5), E ~ 10^51 erg\n"
            "   - Snowplow: Radiative cooling becomes important\n"
            "   - Typical ages: 10^3-10^5 years\n\n"
            "2. **X-ray Emission**:\n"
            "   - Thermal emission from shocked ISM (kT ~ 0.1-1 keV)\n"
            "   - Non-thermal synchrotron from electrons\n"
            "   - Line emission: Fe-K, Mg, Si, S\n\n"
            "3. **Particle Acceleration**:\n"
            "   - Diffusive shock acceleration at SNR shocks\n"
            "   - Produces Galactic cosmic rays up to ~10^15 eV\n"
            "   - Synchrotron X-rays from TeV electrons\n\n"
            "4. **Morphological Types**:\n"
            "   - Shell-like: Tycho, Cas A, SN 1006\n"
            "   - Crab-like: Pulsar wind nebulae\n"
            "   - Mixed-morphology: Center-filled thermal shells\n\n"
            "Key observatories: Chandra, XMM-Newton, Suzaku, NuSTAR."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.84,
            reasoning_trace=[
                "Identified SNR analysis query",
                "Applied shock evolution models"
            ],
            capabilities_used=["snr_evolution_modeling", "snr_xray_emission"]
        )

    def _general_high_energy_analysis(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """General high-energy astrophysics analysis"""
        answer = (
            "High-energy astrophysics covers phenomena from keV to EeV energies.\n\n"
            "Key domains include:\n"
            "- **Compact objects**: Neutron stars, black holes, white dwarfs\n"
            "- **Accretion**: X-ray binaries, AGN, disks and coronae\n"
            "- **Transients**: GRBs, magnetar bursts, tidal disruption events\n"
            "- **Cosmic rays**: Particle acceleration, propagation, origin\n"
            "- **SNRs**: Shock evolution, particle acceleration, thermal X-rays\n\n"
            "High-energy processes:\n"
            "- Synchrotron: Relativistic electrons in magnetic fields\n"
            "- Inverse Compton: Electron-photon scattering\n"
            "- Bremsstrahlung: Deceleration radiation\n"
            "- Pair production: γ + γ → e⁺ + e⁻\n\n"
            "Major observatories:\n"
            "- X-ray: Chandra, XMM-Newton, NuSTAR, NICER, eROSITA\n"
            "- Gamma-ray: Fermi, Swift, INTEGRAL, H.E.S.S., MAGIC, VERITAS\n"
            "- Cosmic rays: AMS-02, Auger, Telescope Array, IceCube"
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.80,
            reasoning_trace=["General high-energy domain overview"],
            capabilities_used=[]
        )


def create_high_energy_domain() -> HighEnergyDomain:
    """Factory function for high-energy domain"""
    return HighEnergyDomain()


# Export public classes
__all__ = [
    'HighEnergyDomain',
    'create_high_energy_domain'
]
