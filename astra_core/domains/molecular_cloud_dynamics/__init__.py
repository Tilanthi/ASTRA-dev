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
Molecular Cloud Dynamics and Shocks Domain Module for STAN-XI-ASTRO

Specializes in molecular cloud dynamics and shock physics:
- Supersonic turbulence
- Shock fronts and jump conditions
- C-type and J-type shocks
- Turbulent cascades
- Cloud-cloud collisions
- Outflow interactions
- Shock chemistry
- Magnetic field dynamics
- Turbulent dissipation
- Velocity coherent structures (fibers)

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
class MolecularCloudDynamicsDomain(BaseDomainModule):
    """Domain specializing in molecular cloud dynamics and shocks"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="molecular_cloud_dynamics",
            version="1.0.0",
            dependencies=["astro_physics", "ism", "star_formation"],
            keywords=[
                "turbulence", "supersonic", "mach number", "turbulent cascade",
                "shock", "c-shock", "j-shock", "jump conditions", "dissociation",
                "mhd shock", "magnetic precursor", "ion-neutral drift",
                "cloud collision", "cloud-cloud collision", "collisional product",
                "outflow", "protostellar outflow", "jet interaction", "bow shock",
                "velocity structure", "coherent structure", "filament", "fiber",
                "turbulent driving", "large-scale driving", "stellar feedback"
            ],
            task_types=["TURBULENCE_ANALYSIS", "SHOCK_MODELING", "DYNAMICAL_MODELING"],
            description="Molecular cloud dynamics, turbulence, and shock physics",
            capabilities=[
                "turbulent_spectrum",
                "shock_modeling",
                "outflow_modeling",
                "collision_timescale",
                "magnetic_dynamics",
                "velocity_decomposition"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)
        logger.info("Molecular Cloud Dynamics domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['turbulence', 'mach', 'cascade', 'power spectrum']):
            return self._process_turbulence_query(query, context)
        elif any(kw in query_lower for kw in ['shock', 'c-shock', 'j-shock']):
            return self._process_shock_query(query, context)
        elif any(kw in query_lower for kw in ['collision', 'merger', 'interaction']):
            return self._process_collision_query(query, context)
        elif any(kw in query_lower for kw in ['outflow', 'jet', 'bow shock']):
            return self._process_outflow_query(query, context)
        else:
            return self._process_general_dynamics_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_turbulence_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing turbulence query"]

        answer = (
            "Molecular clouds are supersonically turbulent: ℳ = σ_v/c_s ~ 5-50. "
            "Kolmogorov cascade: E(k) ∝ k^{-5/3}, modified for supersonic "
            "(Burgers: E(k) ∝ k^{-2}). "
            "Velocity power spectrum: P(k) ∝ k^{-α} with α ~ 1.5-2.0. "
            "Density spectrum: ρ spectrum steeper due to shocks. "
            "Driving: large-scale (solenoidal) vs small-scale (compressive). "
            "Dissipation: viscous (ion) scale ~ 0.01 pc, ambipolar diffusion scale ~ 0.1 pc. "
            "Structure: filaments (velocity-coherent), cores (dissipation), "
            "hierarchical (self-similar). Timescales: t_cross = R/σ_v, "
            "t_decay ~ t_cross (turbulence decays in ~1 crossing time)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.91,
            reasoning_trace=reasoning_trace,
            capabilities_used=["turbulent_spectrum", "velocity_decomposition"],
            metadata={"query_type": "TURBULENCE"}
        )

    def _process_shock_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing shock query"]

        answer = (
            "Shock types in MCs: (1) J-type: jump discontinuity, T jumps to "
            "10⁴-10⁶ K, molecules dissociated. (2) C-type: continuous if B-field "
            "present, ions + neutrals slip, T stays < 10⁴ K, molecules survive. "
            "Critical speed: v_crit ≈ B/√(4πρ) ≈ 2-4 km/s (magnetic). "
            "Shock tracers: SiO (sputtered from grains), H₂O (ice mantle), "
            "SO, SO₂, CH₃OH (grain chemistry). Shock signatures: "
            "broad line wings (Δv ~ 10-50 km/s), SiO emission, hot H₂ (IR). "
            "Outflow shocks: v_sh ~ 10-100 km/s, driving turbulence and chemistry."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["shock_modeling"],
            metadata={"query_type": "SHOCK"}
        )

    def _process_collision_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing collision query"]

        answer = (
            "Cloud-cloud collisions: two MCs collide, trigger star formation. "
            "Collision types: (1) Head-on: shock-compressed layer forms, "
            "triggers local collapse. (2) Oblique: shear flows, turbulence generation. "
            "Collision timescale: t_coll ~ (v_rel/collisonal cross-section). "
            "Observational signatures: bridge emission (connecting clouds), "
            "broad CO lines, enhanced SiO, compact dust emission, young clusters "
            "at collision interface. Examples: Serpens South, Westerlund 2. "
            "Criteria for SF: enough mass, compressed layer (Toomre Q < 1), "
            "turbulence dissipation. Simulations: colliding flows produce "
            "filamentary networks."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["collision_timescale"],
            metadata={"query_type": "COLLISION"}
        )

    def _process_outflow_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing outflow query"]

        answer = (
            "Protostellar outflows interact with surrounding cloud: "
            "Jet bow shocks: working surface, jet head velocity v_h ≈ v_j/3. "
            "Outflow cavity: excavated by jet, walls illuminated (scattered light). "
            "Shocked gas: SiO jet (inner), CO outflow (entrained), H₂ shock "
            "front (molecular). Momentum injection: p_out ~ 1-100 M☉ km/s, "
            "p_protostar/p_* ~ 10-100. Entrainment: jet mass loading, "
            "entrainment efficiency η = Ṁ_out/Ṁ_acc ~ 0.01-1. "
            "Impact: drives turbulence, creates cavities, disrupts cores, "
            "triggers secondary SF (collect-and-collapse)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["outflow_modeling"],
            metadata={"query_type": "OUTFLOW"}
        )

    def _process_general_dynamics_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general dynamics query"]

        answer = (
            "Molecular cloud dynamics governed by supersonic turbulence, gravity, "
            "magnetic fields, and stellar feedback. "
            "Energy injection: large-scale (galactic shear, spiral arms), "
            "local (SN, outflows, HII regions). "
            "Velocity structure: hierarchical, filaments (coherent), "
            "cores (dissipation scale). "
            "Dense gas tracers: N₂H⁺, NH₃ (thermalized), HCO⁺, HCN (high dipole). "
            "Observations: spectral line imaging (CO isotopologues), "
            "velocity centroid, velocity dispersion, structure function, "
            "principal component analysis (PCA), spectral correlation function. "
            "Simulations: AMR (ORION), moving-mesh (AREPO), SPH (GADGET), "
            "MHD including ambipolar diffusion."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["turbulent_spectrum", "velocity_decomposition"],
            metadata={"query_type": "GENERAL"}
        )


def create_molecular_cloud_dynamics_domain() -> MolecularCloudDynamicsDomain:
    return MolecularCloudDynamicsDomain()
