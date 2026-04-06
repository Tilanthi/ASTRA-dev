"""
Cosmology domain module for STAN-XI-ASTRO

Specializes in cosmology including:
- Early universe physics
- Large scale structure
- Dark matter and dark energy
- CMB analysis
- Inflation and reheating
"""

import numpy as np
from typing import Dict, List, Any
import logging

from .. import BaseDomainModule, DomainConfig, DomainQueryResult, register_domain, CrossDomainConnection

logger = logging.getLogger(__name__)


class CosmologyDomain(BaseDomainModule):
    """Domain specializing in cosmology"""

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="cosmology",
            version="1.0.0",
            dependencies=["astro_physics", "relativity"],
            keywords=[
                "cosmology", "universe", "expansion", "hubble", "cmb", "cosmic microwave",
                "dark matter", "dark energy", "inflation", "big bang", "large scale structure",
                "galaxy cluster", "recombination", "nucleosynthesis", "redshift",
                "cosmological constant", "lamba", "friedmann", "accelerating"
            ],
            task_types=["COSMOLOGICAL_ANALYSIS", "CMB_INTERPRETATION", "LSS_ANALYSIS"],
            description="Early universe, expansion history, and large scale structure",
            capabilities=[
                "expansion_history",
                "cmb_analysis",
                "structure_formation",
                "dark_matter_modeling",
                "inflation_modeling",
                "parameter_estimation",
                "distance_measures"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize cosmology domain"""
        super().initialize(global_config)

        # Cosmological parameters (Planck 2018)
        self._params = {
            'H0': 67.4,  # km/s/Mpc
            'Omega_m': 0.315,
            'Omega_L': 0.685,
            'Omega_b': 0.049,
            'n_s': 0.965,
            'A_s': 2.1e-9,
            'tau': 0.054,
            'z_reio': 7.67,
        }

        logger.info("Cosmology domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process cosmology query"""
        query_lower = query.lower()

        if 'expansion' in query_lower or 'hubble' in query_lower:
            return self._process_expansion_query(query, context)
        elif 'cmb' in query_lower or 'microwave' in query_lower:
            return self._process_cmb_query(query, context)
        elif 'dark matter' in query_lower or 'dark energy' in query_lower:
            return self._process_dark_energy_query(query, context)
        elif 'inflation' in query_lower or 'early universe' in query_lower:
            return self._process_inflation_query(query, context)
        else:
            return self._process_general_cosmology_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_expansion_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process expansion-related query"""
        reasoning_trace = ["Processing expansion query"]

        answer = (
            "The universe's expansion is described by the Hubble parameter H(z). "
            "The current expansion rate H₀ = 67.4 km/s/Mpc (Planck 2018). "
            "Expansion accelerated ~5 billion years ago due to dark energy. "
            "The Friedmann equation describes expansion: H²(z) = H₀²[Ω_m(1+z)³ + Ω_Λ], "
            "where Ω_m is matter density and Ω_Λ is dark energy density."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["expansion_history"]
        )

    def _process_cmb_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process CMB query"""
        reasoning_trace = ["Processing CMB query"]

        answer = (
            "The Cosmic Microwave Background (CMB) is thermal radiation from "
            "recombination at z~1100, T=2.725 K. Its anisotropies reveal "
            "cosmological parameters: Ω_m=0.315, Ω_Λ=0.685, n_s=0.965. "
            "Polarization (E-mode and B-mode) probes inflation and primordial "
            "gravitational waves. The CMB power spectrum shows acoustic peaks "
            "from baryon-photon acoustic oscillations."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.93,
            reasoning_trace=reasoning_trace,
            capabilities_used=["cmb_analysis"]
        )

    def _process_dark_energy_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process dark energy/dark matter query"""
        reasoning_trace = ["Processing dark sector query"]

        answer = (
            "Dark matter (27% of universe) is non-baryonic, cold, and collisionless. "
            "Evidence: galaxy rotation curves, gravitational lensing, CMB, structure "
            "formation. Candidates: WIMPs, axions, primordial black holes. "
            "Dark energy (68% of universe) causes accelerated expansion. "
            "Simplest model: cosmological constant Λ (w=-1). Alternatives: "
            "quintessence, modified gravity (f(R), DGP)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["dark_matter_modeling", "parameter_estimation"]
        )

    def _process_inflation_query(self, str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process inflation query"""
        reasoning_trace = ["Processing inflation query"]

        answer = (
            "Inflation: exponential expansion in the early universe (10^-36 to 10^-32 s). "
            "Predicts: flat universe (Ω_k≈0), scale-invariant perturbations (n_s≈1), "
            "and small tensor modes. Supported by CMB data. Models: chaotic inflation, "
            "eternal inflation, multi-field inflation. The inflationary energy scale "
            "is ~10^16 GeV, potentially accessible through primordial B-mode polarization."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["inflation_modeling"]
        )

    def _process_general_cosmology_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """Process general cosmology query"""
        reasoning_trace = ["Processing general cosmology query"]

        answer = (
            "Cosmology studies the universe's origin, evolution, and large-scale "
            "structure. Key observations: CMB (2.725 K), Hubble expansion (v=H₀d), "
            "Big Bang nucleosynthesis (H/He/Li abundances), large-scale structure, "
            "Type Ia supernovae (accelerated expansion). Standard model: ΛCDM with "
            "Ω_m≈0.31, Ω_Λ≈0.69, H₀≈67 km/s/Mpc."
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

            if 'galaxy' in other_name or 'structure' in other_name:
                connection = CrossDomainConnection(
                    source_domain=self.config.domain_name,
                    target_domain=other_name,
                    connection_type="related",
                    strength=0.75,
                    description="Cosmology informs galaxy structure formation"
                )
                connections.append(connection)

        return connections


register_domain(CosmologyDomain)
