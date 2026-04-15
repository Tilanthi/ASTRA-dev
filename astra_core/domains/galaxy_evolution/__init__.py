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
Galaxy Evolution Domain Module for STAN-XI-ASTRO

Specializes in galaxy evolution over cosmic time:
- Galaxy formation and assembly
- Morphological transformations
- Star formation histories
- Chemical evolution
- Galaxy mergers and interactions
- Quenching mechanisms
- Size evolution
- Tully-Fisher and mass-metallicity relations
- Environment effects (clusters vs field)
- Galaxy stellar mass functions

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
class GalaxyEvolutionDomain(BaseDomainModule):
    """Domain specializing in galaxy evolution over cosmic time"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="galaxy_evolution",
            version="1.0.0",
            dependencies=["astro_physics", "extragalactic", "star_formation", "ism"],
            keywords=[
                "galaxy evolution", "galaxy formation", "stellar population",
                "star formation history", "sfh", "quenching", "quenched",
                "blue cloud", "red sequence", "green valley", "morphology",
                "merger", "interaction", "major merger", "minor merger",
                "chemical evolution", "metallicity", "abundance", "alpha/fe",
                "size evolution", "compact galaxy", "progenitor bias",
                "downsizing", "inside-out", "environment", "cluster", "field"
            ],
            task_types=["SFH_MEASUREMENT", "QUENCHING_ANALYSIS", "CHEMICAL_EVOLUTION"],
            description="Galaxy evolution from high redshift to present",
            capabilities=[
                "stellar_population_modeling",
                "sfr_measurement",
                "quenching_timescale",
                "merger_timescale",
                "chemical_enrichment",
                "size_growth"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)
        logger.info("Galaxy Evolution domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['sfh', 'star formation history', 'stellar population']):
            return self._process_sfh_query(query, context)
        elif any(kw in query_lower for kw in ['quench', 'quenched', 'red sequence']):
            return self._process_quenching_query(query, context)
        elif 'merger' in query_lower or 'interaction' in query_lower:
            return self._process_merger_query(query, context)
        elif any(kw in query_lower for kw in ['metallicity', 'chemical', 'abundance']):
            return self._process_chemical_query(query, context)
        elif any(kw in query_lower for kw in ['size', 'compact', 'effective radius']):
            return self._process_size_query(query, context)
        else:
            return self._process_general_evolution_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_sfh_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing SFH query"]

        answer = (
            "Star formation history reconstruction via stellar population synthesis. "
            "Methods: full-spectrum fitting, Lick indices, CMD fitting (resolved). "
            "Parametric models: τ-model (exponential), delayed-τ, rising SFR. "
            "Non-parametric: piecewise constant, SFR at lookback times. "
            "Diagnostic: D4000 break (age-sensitive), HδA (recent burst). "
            "Cosmic SFR density: ρ_SFR(z) ∝ (1+z)^{2.7} at z<2, peaks at z~2, "
            "declines to z~0. Downsizing: massive galaxies form stars early, "
            "low-mass galaxies continue forming stars. "
            "Specific SFR: sSFR = SFR/M_★ ∝ M_★^{-0.3} (main sequence)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["stellar_population_modeling", "sfr_measurement"],
            metadata={"query_type": "SFH"}
        )

    def _process_quenching_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing quenching query"]

        answer = (
            "Galaxy quenching: transition from star-forming to passive. "
            "Bimodality: blue cloud (SF, sSFR > 10^{-11} yr⁻¹), red sequence (quenched). "
            "Quenching mechanisms: (1) Internal: mass quenching (AGN feedback, virial shock), "
            "morphological quenching (bulge stabilizes gas). (2) External: "
            "environmental quenching (ram pressure, strangulation, harassment). "
            "Timescales: rapid (starburst, <100 Myr) vs slow (strangulation, ~Gyr). "
            "Green valley: transition region, t_quench ~ 1-3 Gyr. "
            "Quenched fraction: f_Q ∝ M_★ (massive quenched first), f_Q ∝ density (clusters)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["quenching_timescale", "stellar_population_modeling"],
            metadata={"query_type": "QUENCHING"}
        )

    def _process_merger_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing merger query"]

        answer = (
            "Galaxy mergers drive evolution: gas-rich → starburst, dry → morphology change. "
            "Major merger: mass ratio < 3:1, triggers violent relaxation, elliptical formation. "
            "Minor merger: mass ratio > 3:1, contributes to size growth, ICL. "
            "Merger timescale: t_merge ≈ (r_p/r_vir)^{c} (V_c/σ) × T_dyn, "
            "typically ~0.5-1 Gyr for galaxy pairs. "
            "Merger rate: (1+z)^{2-3} increase to z~2. "
            "Signatures: tidal tails, shells, dual AGN, disturbed morphology, "
            "enhanced sSFR, central concentration growth. "
            "Simulations: Illustris, EAGLE, TNG for hierarchical assembly."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["merger_timescale"],
            metadata={"query_type": "MERGER"}
        )

    def _process_chemical_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing chemical evolution query"]

        answer = (
            "Chemical evolution: gas → stars → metals (SNe, AGB). "
            "Closed-box model: Z = y ln(μ^{-1}) with y ~ 0.02 (yield). "
            "Mass-metallicity relation: Z ∝ M_★^{0.3} locally, flatter at high-z. "
            "Fundamental metallicity relation: Z(M_★, SFR). "
            "α-enhancement: [α/Fe] traces SFH. High [α/Fe] = rapid quenching (<1 Gyr), "
            "solar [α/Fe] = extended SFH. SN II (α) produce on <40 Myr, SN Ia (Fe) on ~1 Gyr. "
            "Abundance ratios: [O/Fe], [Mg/Fe] decrease as SNe Ia contribute. "
            "Radial gradients: dZ/dR ~ -0.05 dex/kpc (negative gradients)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["chemical_enrichment", "stellar_population_modeling"],
            metadata={"query_type": "CHEMICAL"}
        )

    def _process_size_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing size evolution query"]

        answer = (
            "Galaxy size evolution: R_e ∝ (1+z)^{-0.75} for fixed mass (progenitor bias). "
            "Mass-size relation: R_e ∝ M_★^{0.25} (late-types), R_e ∝ M_★^{0.6} (early-types). "
            "Compact massive galaxies at z~2: R_e ~ 1 kpc (vs 5 kpc locally). "
            "Size growth mechanisms: minor mergers (add ex-situ stars), "
            "adiabatic expansion (mass loss), inside-out growth (new disks). "
            "Observations: Surface brightness profiles, Sérsic index n, "
            "R_e (half-light radius). Evolution: ΔR/R ~ factor 2-3 since z=2 "
            "for M_★ ~ 10¹¹ M☉. Compact cores: via dissipational (wet) mergers."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["size_growth"],
            metadata={"query_type": "SIZE"}
        )

    def _process_general_evolution_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general galaxy evolution query"]

        answer = (
            "Galaxies evolve from dense, turbulent, star-forming disks at z~3 "
            "to diverse population today: spirals, ellipticals, irregulars. "
            "Key processes: gas accretion (cold flows, mergers), star formation, "
            "feedback (SN, AGN), morphological transformation. "
            "Stellar mass function: Φ(M) ∝ M^{-α} with low-mass slope α ~ -1.3. "
            "Cosmic stellar mass density: ρ_★(z) increases to z~2, then declines "
            "due to quenching. Environment: clusters quench earlier, field galaxies "
            "continue forming. Tully-Fisher: L ∝ V_max^{4} (scaling relation). "
            "Observations: HST (high-z), SDSS (low-z), surveys (DESI, Euclid, LSST)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=reasoning_trace,
            capabilities_used=["stellar_population_modeling", "sfr_measurement"],
            metadata={"query_type": "GENERAL"}
        )


def create_galaxy_evolution_domain() -> GalaxyEvolutionDomain:
    return GalaxyEvolutionDomain()
