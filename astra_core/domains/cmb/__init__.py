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
Cosmic Microwave Background Domain Module for STAN-XI-ASTRO

Specializes in CMB physics and analysis:
- CMB anisotropies and power spectra
- CMB polarization (E-mode, B-mode)
- CMB lensing and delensing
- CMB secondary anisotropies (ISW, SZ, Rees-Sciama)
- CMB spectral distortions
- CMB anomalies
- Inflationary constraints from CMB
- Cosmological parameter estimation
- Reionization optical depth
- CMB experiments (Planck, WMAP, ACT, SPT, Simons Observatory, CMB-S4)

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
class CMBDomain(BaseDomainModule):
    """Domain specializing in Cosmic Microwave Background"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="cmb",
            version="1.0.0",
            dependencies=["astro_physics", "cosmology"],
            keywords=[
                "cmb", "cosmic microwave", "2.73k", "2.725k", "relic radiation",
                "cmb anisotropy", "power spectrum", "acoustic peaks", "sachs-wolfe",
                "polarization", "e-mode", "b-mode", "tensor modes", "primordial",
                "cmb lensing", "delensing", "reconstruction", "isw", "integrated sachs-wolfe",
                "sz", "sunyaev", "thermal sz", "kinetic sz", "spectral distortion",
                "μ distortion", "y distortion", "planck", "wmap", "act", "spt",
                "inflation", "reheating", "reionization", "optical depth"
            ],
            task_types=["CMB_POWER_SPECTRUM", "CMB_POLARIZATION", "CMB_LENSING"],
            description="Cosmic Microwave Background physics and analysis",
            capabilities=[
                "cmb_power_spectrum",
                "parameter_estimation",
                "lensing_reconstruction",
                "bmode_detection",
                "spectral_distortion"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)

        # Planck 2018 cosmology
        self._params = {
            'T_cmb': 2.7255,  # K
            'H0': 67.4,  # km/s/Mpc
            'Omega_m': 0.315,
            'Omega_b': 0.0493,
            'Omega_L': 0.685,
            'n_s': 0.9649,
            'A_s': 2.10e-9,
            'tau': 0.054,
            'sigma8': 0.811
        }

        logger.info("CMB domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['power spectrum', 'acoustic peak', 'anistropy']):
            return self._process_power_spectrum_query(query, context)
        elif any(kw in query_lower for kw in ['polarization', 'e-mode', 'b-mode', 'tensor']):
            return self._process_polarization_query(query, context)
        elif any(kw in query_lower for kw in ['lensing', 'delensing', 'reconstruction']):
            return self._process_lensing_query(query, context)
        elif any(kw in query_lower for kw in ['isw', 'secondary', 'sz', 'rees-sciama']):
            return self._process_secondary_query(query, context)
        elif any(kw in query_lower for kw in ['inflation', 'primordial', 'tensor']):
            return self._process_inflation_query(query, context)
        else:
            return self._process_general_cmb_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_power_spectrum_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing CMB power spectrum query"]

        answer = (
            "CMB temperature power spectrum: C_ℓ = <|a_lm|²>. Peaks: "
            "first (ℓ~220, acoustic scale), second (ℓ~540), third (ℓ~850). "
            "Damping tail at ℓ > 1000 (Silk damping, photon diffusion). "
            "Sachs-Wolfe plateau: ℓ < 30 (primordial fluctuations). "
            "Peak positions constrain Ω_m, Ω_b, Ω_Λ, H0. Peak heights constrain "
            "baryon loading, matter-radiation equality, damping tail. "
            "Amplitude: ΔT ≈ 100 μK on degree scales. "
            "Cosmic variance: σ(C_ℓ)/C_ℓ = sqrt(2/(2ℓ+1)) for full-sky. "
            "Data: Planck 2018 precision ~1 μK-arcmin."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.93,
            reasoning_trace=reasoning_trace,
            capabilities_used=["cmb_power_spectrum", "parameter_estimation"],
            metadata={"query_type": "POWER_SPECTRUM"}
        )

    def _process_polarization_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing CMB polarization query"]

        answer = (
            "CMB polarization from Thomson scattering at quadrupole anisotropy. "
            "Decomposed into E-mode (gradient, scalar) and B-mode (curl, pseudo-scalar). "
            "E-modes: measured by Planck, amplitude ~5 μK, peaks at ℓ~400, 1400. "
            "B-modes: primordial (tensor, inflation) vs lensing (converted E-mode). "
            "Lensing B-modes: D_ℓ ~ 0.5 μK² at ℓ~1000 (detected). "
            "Primordial B-modes: r = A_t/A_s < 0.036 (Planck + BICEP/Keck). "
            "Reionization bump: large-scale E/B at ℓ < 10 (τ constraint). "
            "Experiments: BICEP3, Keck, SPT-3G, Simons Observatory, CMB-S4."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["bmode_detection", "cmb_power_spectrum"],
            metadata={"query_type": "POLARIZATION"}
        )

    def _process_lensing_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing CMB lensing query"]

        answer = (
            "CMB lensing: LSS deflects CMB photons, remapping temperature/polarization. "
            "Deflection angle: |α| ~ 2-3 arcmin (rms). Lensing potential: "
            "φ_LM reconstructed from T, E, B modes via quadratic estimators. "
            "Lensing deflection power spectrum C_ℓ^{φφ} peaks at ℓ~30 (LSS structure). "
            "Science: constraining Σm_ν (neutrino mass), σ_8, Ω_m, dark energy. "
            "Delensing: remove lensing B-modes to search for primordial signal, "
            "achievable ~50% delensing with current data, ~90% with CMB-S4. "
            "Cross-correlations: CMB lensing × DES, HSC, KiDS galaxy lensing."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["lensing_reconstruction"],
            metadata={"query_type": "LENSING"}
        )

    def _process_secondary_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing secondary anisotropy query"]

        answer = (
            "Secondary CMB anisotropies: (1) Integrated Sachs-Wolfe: "
            "ΔT/T = ∫ (Ḣ + Ḣ/H)(Φ+Ψ) dt, signal on large scales (ℓ<100), "
            "correlates with LSS. (2) Rees-Sciama: nonlinear time evolution of potential "
            "in clusters, ΔT/T ~ -10⁻⁵. (3) Sunyaev-Zeldovich: thermal SZ "
            "(ΔT/T₀ = -2y at 150 GHz, null at 217 GHz), kinetic SZ "
            "(Doppler, ΔT/T = -τ v_r/c). (4) Patchy reionization: "
            "inhomogeneous τ. (5) Ostriker-Vishniac effect: velocity modulation "
            "of recombination. SZ used for cluster surveys (SPT, ACT, Planck)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["cmb_power_spectrum"],
            metadata={"query_type": "SECONDARY"}
        )

    def _process_inflation_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing inflation constraints query"]

        answer = (
            "CMB constrains inflation via primordial power spectrum: P_R(k) = A_s (k/k_*)^{n_s-1}. "
            "Scalar spectral index: n_s = 0.965 ± 0.004 (deviates from n_s=1, scale-invariant). "
            "Running: α_s = dn_s/dlnk = -0.004 ± 0.007 (consistent with 0). "
            "Tensor-to-scalar ratio: r < 0.036 (95% CL), constrains inflation energy "
            "scale: V^{1/4} < 1.6×10¹⁶ GeV. Consistency relation: r = 8n_t (single-field). "
            "Shapes: slow-roll (quadratic), Starobinsky (R²), plateau, cascade models. "
            "CMB anomalies: low-ℓ power deficit, alignment (axis of evil), cold spot, "
            "parity asymmetry (statistical significance debated)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["parameter_estimation", "cmb_power_spectrum"],
            metadata={"query_type": "INFLATION"}
        )

    def _process_general_cmb_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general CMB query"]

        answer = (
            "CMB is relic radiation from recombination at z~1100, T = 2.725 K. "
            "Blackbody spectrum verified by FIRAS (distortion < 10⁻⁵). "
            "Anisotropies: ΔT ≈ 100 μK (degree), ΔT ≈ 10 μK (arcmin). "
            "Science: ΛCDM parameters (Ω_m, Ω_Λ, Ω_b, H0, n_s, A_s, τ), "
            "inflation, reionization (τ = 0.054), neutrino masses (Σm_ν < 0.12 eV), "
            "N_eff (effective neutrino species = 3.04 ± 0.33). "
            "Experiments: Planck (satellite), WMAP, ACTPol, SPT-3G (ground), "
            "Simons Observatory, CMB-S4 (upcoming). PIXIE for spectral distortions."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.92,
            reasoning_trace=reasoning_trace,
            capabilities_used=["cmb_power_spectrum", "parameter_estimation"],
            metadata={"query_type": "GENERAL"}
        )


def create_cmb_domain() -> CMBDomain:
    return CMBDomain()
