
"""
Documentation for multi_scale_inference module.

This module provides multi_scale_inference capabilities for STAN.
Enhanced through self-evolution cycle 124.
"""

#!/usr/bin/env python3
"""
V36 Causal Reasoning for Molecular Clouds
==========================================

Symbolic causal reasoning for molecular cloud physics using
the V36 framework. Implements:

1. Causal DAGs for cloud evolution
2. Mechanism discovery for physical processes
3. Cross-domain analogies for cloud physics
4. Hypothesis generation and testing

Physical Mechanisms Modeled:
- Thermal balance (heating/cooling)
- Gravitational collapse
- Turbulent support
- Magnetic support
- Chemical evolution
- Star formation triggers

Author: Claude Code (ASTRO-SWARM)
Date: 2024-11
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
from datetime import datetime

# Import V36 core (if available)
try:
    from ..core_legacy.v36.v36_system import (
        MechanismDiscoveryEngine, SymbolicCausalAbstraction,
        CrossDomainAnalogyEngine
    )
    V36_AVAILABLE = True
except ImportError:
    V36_AVAILABLE = False


# =============================================================================
# CAUSAL GRAPH STRUCTURES
# =============================================================================

class CloudPhysicsNode(Enum):
    """Nodes in the molecular cloud causal graph"""
    # Observable quantities
    COLUMN_DENSITY = "N_H2"
    TEMPERATURE_DUST = "T_dust"
    TEMPERATURE_GAS = "T_gas"
    VELOCITY_DISPERSION = "sigma_v"
    LINE_WIDTH = "delta_v"
    DENSITY = "n_H2"
    MAGNETIC_FIELD = "B"
    LUMINOSITY = "L"
    MASS = "M"

    # Derived quantities
    VIRIAL_PARAMETER = "alpha_vir"
    JEANS_MASS = "M_J"
    MACH_NUMBER = "mach"
    MASS_TO_FLUX = "M_Phi"
    STAR_FORMATION_RATE = "SFR"

    # Physical processes
    GRAVITY = "gravity"
    TURBULENCE = "turbulence"
    MAGNETIC_SUPPORT = "magnetic_support"
    THERMAL_PRESSURE = "thermal_pressure"
    RADIATION_FIELD = "radiation"
    COSMIC_RAYS = "cosmic_rays"
    COOLING = "cooling"
    HEATING = "heating"

    # Evolutionary states
    DIFFUSE = "diffuse"
    COLLAPSING = "collapsing"
    STAR_FORMING = "star_forming"
    DISPERSING = "dispersing"


@dataclass
class CausalEdge:
    """Directed edge in causal graph"""
    source: CloudPhysicsNode
    target: CloudPhysicsNode
    mechanism: str
    strength: float  # -1 to 1 (negative = inhibits)
    uncertainty: float
    equation: Optional[str] = None  # Mathematical relationship


@dataclass
class CausalMechanism:
    """A physical mechanism connecting cause and effect"""
    mechanism_id: str
    name: str
    description: str
    causes: List[CloudPhysicsNode]
    effects: List[CloudPhysicsNode]
    equations: List[str]
    timescale: str  # e.g., "t_ff", "t_cool", "t_dyn"
    conditions: List[str]  # When mechanism is active
    references: List[str]


# =============================================================================
# MOLECULAR CLOUD CAUSAL GRAPH
# =============================================================================

class MolecularCloudCausalGraph:
    """
    Causal graph for molecular cloud physics

    Encodes the physical relationships between cloud properties
    and the mechanisms that drive cloud evolution.
    """

    def __init__(self):
        self.nodes: Set[CloudPhysicsNode] = set()
        self.edges: List[CausalEdge] = []
        self.mechanisms: Dict[str, CausalMechanism] = {}

        self._build_default_graph()

    def _build_default_graph(self):
        """Build the standard molecular cloud causal graph"""

        # =====================================================================
        # GRAVITATIONAL COLLAPSE MECHANISM
        # =====================================================================
        self.add_mechanism(CausalMechanism(
            mechanism_id="grav_collapse",
            name="Gravitational Collapse",
            description="""
            Self-gravity causes cloud to contract when mass exceeds Jeans mass.
            Collapse proceeds on free-fall timescale t_ff = sqrt(3π/32Gρ).
            Counteracted by thermal, turbulent, and magnetic pressure.
            """,
            causes=[CloudPhysicsNode.MASS, CloudPhysicsNode.DENSITY],
            effects=[CloudPhysicsNode.COLLAPSING, CloudPhysicsNode.STAR_FORMATION_RATE],
            equations=[
                "M_J = (π^(5/2) / 6) × c_s³ / (G^(3/2) × ρ^(1/2))",
                "t_ff = sqrt(3π / 32Gρ)",
                "α_vir = 5σ²R / GM"
            ],
            timescale="t_ff ~ 0.5 Myr × (n/10⁴ cm⁻³)^(-1/2)",
            conditions=["α_vir < 2", "M > M_J"],
            references=["Jeans 1902", "Larson 1981"]
        ))

        self.add_edge(CausalEdge(
            source=CloudPhysicsNode.MASS,
            target=CloudPhysicsNode.GRAVITY,
            mechanism="grav_collapse",
            strength=1.0,
            uncertainty=0.1,
            equation="F_grav ∝ GM²/R²"
        ))

        self.add_edge(CausalEdge(
            source=CloudPhysicsNode.GRAVITY,
            target=CloudPhysicsNode.COLLAPSING,
            mechanism="grav_collapse",
            strength=0.8,
            uncertainty=0.2,
            equation="collapse if α_vir < 2"
        ))

        # =====================================================================
        # TURBULENT SUPPORT MECHANISM
        # =====================================================================
        self.add_mechanism(CausalMechanism(
            mechanism_id="turb_support",
            name="Turbulent Support",
            description="""
            Supersonic turbulence provides non-thermal pressure support.
            Turbulence decays on crossing time t_cross = L/σ unless driven.
            Creates density structure (filaments, cores) via shocks.
            """,
            causes=[CloudPhysicsNode.VELOCITY_DISPERSION],
            effects=[CloudPhysicsNode.VIRIAL_PARAMETER, CloudPhysicsNode.MACH_NUMBER],
            equations=[
                "P_turb = ρσ_nt²",
                "M = σ_nt / c_s",
                "t_cross = L / σ"
            ],
            timescale="t_cross ~ 1 Myr × (L/1pc) × (σ/1 km/s)^(-1)",
            conditions=["M > 1 (supersonic)"],
            references=["Mac Low & Klessen 2004", "Federrath 2013"]
        ))

        self.add_edge(CausalEdge(
            source=CloudPhysicsNode.VELOCITY_DISPERSION,
            target=CloudPhysicsNode.TURBULENCE,
            mechanism="turb_support",
            strength=1.0,
            uncertainty=0.1
        ))

        self.add_edge(CausalEdge(
            source=CloudPhysicsNode.TURBULENCE,
            target=CloudPhysicsNode.GRAVITY,
            mechanism="turb_support",
            strength=-0.6,  # Opposes gravity
            uncertainty=0.2,
            equation="α_vir ∝ σ²"
        ))

        # =====================================================================
        # THERMAL BALANCE MECHANISM
        # =====================================================================
        self.add_mechanism(CausalMechanism(
            mechanism_id="thermal_balance",
            name="Thermal Balance",
            description="""
            Cloud temperature set by balance of heating and cooling.
            Heating: cosmic rays, photoelectric, turbulent dissipation.
            Cooling: molecular lines (CO, C+), dust emission.
            Phase transition: WNM (8000K) ↔ CNM (50K) at n ~ 1-100 cm⁻³.
            """,
            causes=[CloudPhysicsNode.COSMIC_RAYS, CloudPhysicsNode.RADIATION_FIELD,
                    CloudPhysicsNode.DENSITY],
            effects=[CloudPhysicsNode.TEMPERATURE_GAS, CloudPhysicsNode.TEMPERATURE_DUST],
            equations=[
                "Γ_CR = ζ × n × E_dep",
                "Λ_CO = n² × Λ(T)",
                "T_eq: Γ = Λ"
            ],
            timescale="t_cool ~ 0.1 Myr × (T/50K) × (n/10³ cm⁻³)^(-1)",
            conditions=["optically thin to cooling radiation"],
            references=["Koyama & Inutsuka 2002", "Glover & Clark 2012"]
        ))

        self.add_edge(CausalEdge(
            source=CloudPhysicsNode.DENSITY,
            target=CloudPhysicsNode.COOLING,
            mechanism="thermal_balance",
            strength=1.0,
            uncertainty=0.1,
            equation="Λ ∝ n²"
        ))

        self.add_edge(CausalEdge(
            source=CloudPhysicsNode.COOLING,
            target=CloudPhysicsNode.TEMPERATURE_GAS,
            mechanism="thermal_balance",
            strength=-0.8,
            uncertainty=0.2
        ))

        # =====================================================================
        # MAGNETIC SUPPORT MECHANISM
        # =====================================================================
        self.add_mechanism(CausalMechanism(
            mechanism_id="mag_support",
            name="Magnetic Support",
            description="""
            Magnetic pressure and tension provide support against gravity.
            Critical mass-to-flux ratio determines if magnetically supercritical.
            Ambipolar diffusion allows slow contraction in subcritical clouds.
            """,
            causes=[CloudPhysicsNode.MAGNETIC_FIELD],
            effects=[CloudPhysicsNode.MASS_TO_FLUX, CloudPhysicsNode.GRAVITY],
            equations=[
                "P_B = B² / 8π",
                "M_Φ = M / Φ_B",
                "(M/Φ)_crit = c₁ / √G"
            ],
            timescale="t_AD ~ 10 Myr × (n/10³ cm⁻³)^(-1) × (x_i/10⁻⁷)",
            conditions=["M/Φ < (M/Φ)_crit for subcritical"],
            references=["Mouschovias & Spitzer 1976", "Crutcher 2012"]
        ))

        self.add_edge(CausalEdge(
            source=CloudPhysicsNode.MAGNETIC_FIELD,
            target=CloudPhysicsNode.MAGNETIC_SUPPORT,
            mechanism="mag_support",
            strength=1.0,
            uncertainty=0.2
        ))

        self.add_edge(CausalEdge(
            source=CloudPhysicsNode.MAGNETIC_SUPPORT,
            target=CloudPhysicsNode.GRAVITY,
            mechanism="mag_support",
            strength=-0.5,
            uncertainty=0.3
        ))

        # =====================================================================
        # STAR FORMATION MECHANISM
        # =====================================================================
        self.add_mechanism(CausalMechanism(
            mechanism_id="star_formation",
            name="Star Formation",
            description="""
            Dense cores collapse to form protostars.
            Threshold: A_V > 7-8 mag, n > 10⁴ cm⁻³.
            SFR follows Kennicutt-Schmidt relation.
            Efficiency per free-fall time ε_ff ~ 1%.
            """,
            causes=[CloudPhysicsNode.COLLAPSING, CloudPhysicsNode.DENSITY],
            effects=[CloudPhysicsNode.STAR_FORMATION_RATE, CloudPhysicsNode.DISPERSING],
            equations=[
                "SFR = ε_ff × M / t_ff",
                "Σ_SFR ∝ Σ_gas^1.4",
                "ε_ff ~ 0.01"
            ],
            timescale="t_ff ~ 0.5 Myr (for cores)",
            conditions=["n > 10⁴ cm⁻³", "A_V > 7 mag", "α_vir < 1"],
            references=["Lada et al. 2010", "Krumholz & McKee 2005"]
        ))

        self.add_edge(CausalEdge(
            source=CloudPhysicsNode.COLLAPSING,
            target=CloudPhysicsNode.STAR_FORMING,
            mechanism="star_formation",
            strength=0.7,
            uncertainty=0.2,
            equation="SFE ~ 1-10%"
        ))

    def add_mechanism(self, mechanism: CausalMechanism):
        """Add a mechanism to the graph"""
        self.mechanisms[mechanism.mechanism_id] = mechanism
        for node in mechanism.causes + mechanism.effects:
            self.nodes.add(node)

    def add_edge(self, edge: CausalEdge):
        """Add a causal edge"""
        self.edges.append(edge)
        self.nodes.add(edge.source)
        self.nodes.add(edge.target)

    def get_causal_path(self, source: CloudPhysicsNode,
                         target: CloudPhysicsNode) -> List[CausalEdge]:
        """Find causal path from source to target"""
        # Simple BFS for now
        from collections import deque

        visited = set()
        queue = deque([(source, [])])

        while queue:
            current, path = queue.popleft()
            if current == target:
                return path

            if current in visited:
                continue
            visited.add(current)

            for edge in self.edges:
                if edge.source == current and edge.target not in visited:
                    queue.append((edge.target, path + [edge]))

        return []

    def get_effects_of(self, node: CloudPhysicsNode) -> List[Tuple[CloudPhysicsNode, float]]:
        """Get all effects of a node with their strengths"""
        effects = []
        for edge in self.edges:
            if edge.source == node:
                effects.append((edge.target, edge.strength))
        return effects

    def get_causes_of(self, node: CloudPhysicsNode) -> List[Tuple[CloudPhysicsNode, float]]:
        """Get all causes of a node with their strengths"""
        causes = []
        for edge in self.edges:
            if edge.target == node:
                causes.append((edge.source, edge.strength))
        return causes


# =============================================================================
# V36 MOLECULAR CLOUD ANALYZER
# =============================================================================

class MolecularCloudV36Analyzer:
    """
    V36 causal analyzer for molecular clouds

    Provides:
    - Causal inference about cloud states
    - Mechanism identification from observables
    - Predictions about cloud evolution
    - Hypothesis generation for missing data
    """

    def __init__(self):
        self.causal_graph = MolecularCloudCausalGraph()

        # V36 engines if available
        if V36_AVAILABLE:
            self.mechanism_engine = MechanismDiscoveryEngine()
            self.causal_engine = SymbolicCausalAbstraction()
            self.analogy_engine = CrossDomainAnalogyEngine()
        else:
            self.mechanism_engine = None
            self.causal_engine = None
            self.analogy_engine = None

    def infer_cloud_state(self, observations: Dict) -> Dict:
        """
        Infer cloud evolutionary state from observations

        Uses causal reasoning to determine:
        - Current state (diffuse, collapsing, star-forming, dispersing)
        - Dominant support mechanism
        - Likely evolution trajectory
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'observations': observations,
            'inferred_state': None,
            'dominant_mechanism': None,
            'causal_chain': [],
            'predictions': [],
            'confidence': 0.0
        }

        # Extract key observables
        alpha_vir = observations.get('alpha_virial', 2.0)
        mach = observations.get('mach_number', 1.0)
        n_H2 = observations.get('n_H2', 1e3)
        T_kin = observations.get('T_kin', 15)
        B_field = observations.get('B_field', 0)
        has_ysos = observations.get('n_YSOs', 0) > 0

        # State inference rules
        if has_ysos or observations.get('has_outflows', False):
            state = "star_forming"
            confidence = 0.9
        elif alpha_vir < 1 and n_H2 > 1e4:
            state = "collapsing"
            confidence = 0.8
        elif alpha_vir < 2:
            state = "bound_turbulent"
            confidence = 0.7
        elif n_H2 < 100:
            state = "diffuse"
            confidence = 0.8
        else:
            state = "marginally_bound"
            confidence = 0.5

        results['inferred_state'] = state
        results['confidence'] = confidence

        # Identify dominant support mechanism
        support_scores = {
            'thermal': 1.0 / (mach + 0.1),  # Dominates if subsonic
            'turbulent': mach / (mach + 1),  # Dominates if supersonic
            'magnetic': 0.5 if B_field > 0 else 0.0,  # If measured
            'gravity': 2.0 / (alpha_vir + 0.1) if alpha_vir < 2 else 0.0
        }

        dominant = max(support_scores, key=support_scores.get)
        results['dominant_mechanism'] = dominant
        results['support_scores'] = support_scores

        # Build causal chain for current state
        if state == "collapsing":
            results['causal_chain'] = [
                "high_mass → gravity_dominant",
                "gravity > pressure_support → contraction",
                "contraction → density_increase → faster_collapse"
            ]
        elif state == "star_forming":
            results['causal_chain'] = [
                "collapse → core_formation",
                "core_density > 10⁵ cm⁻³ → protostar",
                "protostar → outflow → feedback"
            ]

        # Predictions based on current state
        results['predictions'] = self._predict_evolution(state, observations)

        return results

    def _predict_evolution(self, current_state: str, observations: Dict) -> List[Dict]:
        """Predict future evolution based on current state"""
        predictions = []

        alpha_vir = observations.get('alpha_virial', 2.0)
        t_ff = observations.get('t_ff_myr', 0.5)

        if current_state == "bound_turbulent":
            predictions.append({
                'outcome': 'collapse_begins',
                'probability': 0.7 if alpha_vir < 1.5 else 0.3,
                'timescale': f"{t_ff:.1f} Myr",
                'mechanism': 'turbulent_decay → gravity_wins'
            })

        elif current_state == "collapsing":
            predictions.append({
                'outcome': 'star_formation',
                'probability': 0.9,
                'timescale': f"{t_ff:.1f} Myr",
                'mechanism': 'free_fall_collapse → protostar'
            })

        elif current_state == "star_forming":
            predictions.append({
                'outcome': 'cloud_dispersal',
                'probability': 0.5,
                'timescale': f"{3*t_ff:.1f} Myr",
                'mechanism': 'stellar_feedback → gas_ejection'
            })
            predictions.append({
                'outcome': 'cluster_formation',
                'probability': 0.4,
                'timescale': f"{5*t_ff:.1f} Myr",
                'mechanism': 'continued_accretion → stellar_cluster'
            })

        return predictions

    def identify_missing_mechanism(self, observations: Dict,
                                    expected_outcome: str) -> Dict:
        """
        Identify what mechanism might explain unexpected observations

        If observations don't match expected causal model, identify
        potential missing mechanisms.
        """
        results = {
            'observations': observations,
            'expected': expected_outcome,
            'missing_mechanisms': [],
            'hypotheses': []
        }

        alpha_vir = observations.get('alpha_virial', 2.0)
        is_collapsing = observations.get('is_collapsing', False)

        # Example: Should be collapsing but isn't
        if alpha_vir < 1 and not is_collapsing:
            results['missing_mechanisms'].append({
                'mechanism': 'magnetic_support',
                'explanation': 'B-field may provide additional support not accounted for',
                'test': 'Measure Zeeman splitting or polarization'
            })
            results['missing_mechanisms'].append({
                'mechanism': 'external_pressure',
                'explanation': 'External pressure may be confining without collapse',
                'test': 'Measure velocity gradient at cloud boundary'
            })

        # Example: High SFR but low density
        sfr = observations.get('sfr', 0)
        n_H2 = observations.get('n_H2', 1e3)

        if sfr > 0 and n_H2 < 1e3:
            results['hypotheses'].append({
                'hypothesis': 'cloud_caught_post_SF',
                'explanation': 'May be seeing late-stage cloud being dispersed',
                'prediction': 'Should see expanding velocity structure'
            })

        return results

    def cross_domain_analogy(self, cloud_properties: Dict) -> List[Dict]:
        """
        Find analogies to other astrophysical systems

        Molecular clouds share physics with:
        - Protoplanetary disks (gravitational instability)
        - Stellar interiors (thermal balance)
        - Galaxy clusters (virial equilibrium)
        """
        analogies = []

        # Gravitational instability analogy with disks
        if cloud_properties.get('mach_number', 1) > 1:
            analogies.append({
                'domain': 'protoplanetary_disks',
                'analogy': 'Toomre instability in disks ~ Jeans instability in clouds',
                'shared_physics': 'gravity vs pressure in rotating/turbulent medium',
                'insight': 'Disk Q parameter ~ cloud α_vir for stability criterion'
            })

        # Virial equilibrium analogy with clusters
        if cloud_properties.get('virial_parameter', 2) < 3:
            analogies.append({
                'domain': 'galaxy_clusters',
                'analogy': 'Hydrostatic equilibrium in ICM ~ virial equilibrium in clouds',
                'shared_physics': 'pressure support against gravity',
                'insight': 'β_plasma (gas/magnetic pressure) matters in both'
            })

        return analogies

    def generate_observational_test(self, hypothesis: str) -> Dict:
        """
        Generate observational tests for a hypothesis
        """
        tests = {
            'magnetic_support': {
                'observable': 'Zeeman splitting of OH, CN',
                'instrument': 'Arecibo, ALMA',
                'prediction': 'B > 30 μG × (n/10³ cm⁻³)^0.65 for support',
                'discriminator': 'M/Φ > (M/Φ)_crit means supercritical'
            },
            'turbulent_driving': {
                'observable': 'Velocity power spectrum',
                'instrument': 'ALMA, NOEMA',
                'prediction': 'E(k) ∝ k^(-5/3) for Kolmogorov, k^(-2) for shocks',
                'discriminator': 'Solenoidal vs compressive ratio'
            },
            'thermal_instability': {
                'observable': 'Temperature distribution from NH3 or CH3CCH',
                'instrument': 'GBT, VLA',
                'prediction': 'Bimodal T distribution (50K and 8000K)',
                'discriminator': 'Presence of thermally unstable gas (100-5000K)'
            }
        }

        return tests.get(hypothesis, {
            'observable': 'Unknown',
            'note': f'No standard test defined for hypothesis: {hypothesis}'
        })


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'CloudPhysicsNode',
    'CausalEdge',
    'CausalMechanism',
    'MolecularCloudCausalGraph',
    'MolecularCloudV36Analyzer',
]



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None
