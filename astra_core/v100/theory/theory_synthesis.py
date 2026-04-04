"""
Universal Theory Synthesis Engine (UTSE)
========================================

Generates new physical theories by synthesizing multiple lines of evidence.
This is the core theoretical discovery component of V100.

Unlike V92's hypothesis generator (which creates simple causal claims),
UTSE generates complete theoretical frameworks with:
- Novel entities/mechanisms
- Mathematical formalism
- Testable predictions
- Unification of disparate phenomena

Author: STAN-XI ASTRO V100 Development Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Callable
from enum import Enum, auto
import numpy as np
import time
import json
from abc import ABC, abstractmethod
from collections import defaultdict
import hashlib
import networkx as nx


# =============================================================================
# Enumerations
# =============================================================================

class TheoryType(Enum):
    """Types of theories"""
    PHENOMENOLOGICAL = "phenomenological"  # Describes observations
    MECHANISTIC = "mechanistic"           # Describes mechanisms
    UNIFYING = "unifying"                 # Unifies phenomena
    FUNDAMENTAL = "fundamental"           # New fundamental physics
    EMERGENT = "emergent"                 # Emergent phenomena
    CORRECTIVE = "corrective"             # Corrects existing theory


class ConfidenceLevel(Enum):
    """Confidence in theory components"""
    SPECULATIVE = 0.2
    PLAUSIBLE = 0.5
    LIKELY = 0.7
    WELL_SUPPORTED = 0.9
    ESTABLISHED = 0.98


class NoveltyType(Enum):
    """Types of theoretical novelty"""
    NEW_ENTITY = "new_entity"             # New object/field/force
    NEW_RELATION = "new_relation"         # New relationship between entities
    NEW_MECHANISM = "new_mechanism"       # New causal mechanism
    NEW_FORMALISM = "new_formalism"       # New mathematical framework
    NEW_SCALE = "new_scale"               # New scale of description
    PARADIGM_SHIFT = "paradigm_shift"     # Fundamental rethinking


# =============================================================================
# Core Data Structures
# =============================================================================

@dataclass
class Evidence:
    """A single piece of evidence"""
    id: str
    description: str
    observation_type: str  # 'measurement', 'detection', 'non-detection', 'correlation'
    value: Optional[float] = None
    uncertainty: Optional[float] = None
    units: Optional[str] = None
    source: str = ""
    reliability: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceCluster:
    """A cluster of related evidence"""
    id: str
    name: str
    domain: str  # 'astrophysics', 'cosmology', 'ism', etc.
    evidence: List[Evidence] = field(default_factory=list)
    consistency: float = 1.0  # Internal consistency [0, 1]
    completeness: float = 0.5  # How completely characterized [0, 1]

    def add_evidence(self, evidence: Evidence):
        """Add evidence to cluster"""
        self.evidence.append(evidence)

    def get_summary(self) -> Dict[str, Any]:
        """Get cluster summary"""
        return {
            'id': self.id,
            'name': self.name,
            'domain': self.domain,
            'n_evidence': len(self.evidence),
            'consistency': self.consistency,
            'completeness': self.completeness,
        }


@dataclass
class Contradiction:
    """A contradiction between evidence clusters or theories"""
    id: str
    description: str
    severity: float  # [0, 1], how severe is the contradiction
    confidence: float  # [0, 1], how confident are we this is a real contradiction
    clusters: List[str] = field(default_factory=list)  # IDs of contradictory clusters
    resolution_strategy: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainBoundary:
    """A boundary between scientific domains"""
    id: str
    domain_a: str
    domain_b: str
    boundary_type: str  # 'scale', 'regime', 'formalism', 'conceptual'
    crossing_established: bool  # Are there established connections?
    potential_bridges: List[str] = field(default_factory=list)


@dataclass
class Entity:
    """A theoretical entity (object, field, force, property, etc.)"""
    id: str
    name: str
    entity_type: str  # 'particle', 'field', 'force', 'property', 'state'
    properties: Dict[str, Any] = field(default_factory=dict)
    novel: bool = True
    theoretical_motivation: str = ""
    observability: float = 0.5  # [0, 1], how easily can it be observed?


@dataclass
class Mechanism:
    """A causal mechanism"""
    id: str
    name: str
    description: str
    inputs: List[str] = field(default_factory=list)  # Entity IDs
    outputs: List[str] = field(default_factory=list)  # Entity IDs
    mathematical_form: Optional[str] = None
    strength: float = 1.0
    confidence: float = 0.5
    novel: bool = True


@dataclass
class Prediction:
    """A testable prediction"""
    id: str
    description: str
    observable: str
    predicted_value: Optional[float] = None
    predicted_range: Optional[Tuple[float, float]] = None
    qualitative_prediction: Optional[str] = None
    testability: float = 0.5  # [0, 1]
    timescale: Optional[str] = None  # 'immediate', 'future', 'eventual'
    required_facilities: List[str] = field(default_factory=list)


@dataclass
class TheoryFramework:
    """A complete theoretical framework"""
    id: str
    name: str
    description: str
    theory_type: TheoryType

    # Core components
    entities: Dict[str, Entity] = field(default_factory=dict)
    mechanisms: Dict[str, Mechanism] = field(default_factory=dict)
    predictions: Dict[str, Prediction] = field(default_factory=dict)

    # Evidence and consistency
    explained_evidence: List[str] = field(default_factory=list)  # Evidence IDs
    resolved_contradictions: List[str] = field(default_factory=list)  # Contradiction IDs
    unification_power: float = 0.0  # [0, 1], how many phenomena unified

    # Mathematical framework
    equations: List[str] = field(default_factory=list)
    formalism: str = "standard"  # 'standard', 'novel', 'revolutionary'

    # Meta-information
    confidence: float = 0.5
    novelty_score: float = 0.5  # [0, 1]
    testability: float = 0.5  # [0, 1]
    simplicity: float = 0.5  # [0, 1], Occam's razor
    created_at: float = field(default_factory=time.time)
    version: int = 1

    def get_summary(self) -> Dict[str, Any]:
        """Get theory summary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.theory_type.value,
            'entities': len(self.entities),
            'mechanisms': len(self.mechanisms),
            'predictions': len(self.predictions),
            'explained': len(self.explained_evidence),
            'confidence': self.confidence,
            'novelty': self.novelty_score,
            'testability': self.testability,
        }


# =============================================================================
# Theory Synthesis Engine
# =============================================================================

class TheorySynthesisEngine:
    """
    Generates new theoretical frameworks from evidence.

    The synthesis process:
    1. Analyze evidence clusters and contradictions
    2. Identify what needs explaining (explananda)
    3. Generate candidate mechanisms (abduction)
    4. Construct entities and relationships
    5. Formalize mathematically
    6. Derive predictions
    7. Assess unification power and novelty
    """

    def __init__(self):
        self.evidence_clusters: Dict[str, EvidenceCluster] = {}
        self.contradictions: Dict[str, Contradiction] = {}
        self.domain_boundaries: Dict[str, DomainBoundary] = {}
        self.generated_theories: Dict[str, TheoryFramework] = {}

        # Synthesis strategies
        self.strategies = {
            'abductive_inference': self._abductive_synthesis,
            'analogy_transfer': self._analogical_synthesis,
            'unification': self._unification_synthesis,
            'novel_entity': self._novel_entity_synthesis,
            'paradigm_shift': self._paradigm_shift_synthesis,
            'boundary_crossing': self._boundary_crossing_synthesis,
        }

        # Domain knowledge bases
        self.domain_knowledge: Dict[str, Dict] = defaultdict(dict)
        self._initialize_domain_knowledge()

    def _initialize_domain_knowledge(self):
        """Initialize domain-specific knowledge"""
        # Astrophysics domains
        self.domain_knowledge['ism'] = {
            'typical_scales': ['pc', 'kpc', '100pc'],
            'typical_densities': [1, 100, 1e4, 1e6],  # cm^-3
            'typical_temperatures': [10, 20, 100, 1e4],  # K
            'typical_magnetic_fields': [1e-6, 1e-5, 1e-4],  # G
            'known_entities': ['cloud', 'filament', 'core', 'protostar', 'HII_region'],
            'known_mechanisms': ['gravitational_collapse', 'turbulent_support',
                               'magnetic_support', 'thermal_pressure'],
        }

        self.domain_knowledge['star_formation'] = {
            'typical_scales': ['au', 'pc'],
            'typical_masses': [0.01, 1, 10, 100],  # M_sun
            'efficiency_range': [0.01, 0.3],
            'known_entities': ['molecular_cloud', 'prestellar_core', 'protostar',
                             'YSO', 'main_sequence_star'],
            'known_mechanisms': ['jeans_instability', 'fragmentation',
                               'accretion', 'outflow_feedback'],
        }

    def add_evidence_cluster(self, cluster: EvidenceCluster):
        """Add an evidence cluster"""
        self.evidence_clusters[cluster.id] = cluster

    def add_contradiction(self, contradiction: Contradiction):
        """Add a contradiction"""
        self.contradictions[contradiction.id] = contradiction

    def add_domain_boundary(self, boundary: DomainBoundary):
        """Add a domain boundary"""
        self.domain_boundaries[boundary.id] = boundary

    def synthesize_theory(
        self,
        evidence: Dict[str, EvidenceCluster],
        contradictions: List[Contradiction],
        domain_boundaries: List[DomainBoundary],
        target_domains: Optional[List[str]] = None,
        synthesis_strategy: Optional[str] = None,
        max_theories: int = 5
    ) -> List[TheoryFramework]:
        """
        Generate new theories explaining all evidence.

        Parameters
        ----------
        evidence : dict
            Evidence clusters by ID
        contradictions : list
            Contradictions to resolve
        domain_boundaries : list
            Domain boundaries to potentially cross
        target_domains : list, optional
            Domains to focus on
        synthesis_strategy : str, optional
            Specific strategy to use, or None for auto-selection
        max_theories : int
            Maximum number of theories to generate

        Returns
        -------
        List of generated theories, ranked by overall quality
        """
        print(f"UTSE: Synthesizing theories from {len(evidence)} evidence clusters, "
              f"{len(contradictions)} contradictions")

        # Update internal state
        for cluster_id, cluster in evidence.items():
            self.evidence_clusters[cluster_id] = cluster

        for contradiction in contradictions:
            self.contradictions[contradiction.id] = contradiction

        for boundary in domain_boundaries:
            self.domain_boundaries[boundary.id] = boundary

        # Identify what needs explaining
        explananda = self._identify_explananda(evidence, contradictions)
        print(f"  Identified {len(explananda)} phenomena to explain")

        # Select synthesis strategies
        if synthesis_strategy:
            strategies = {synthesis_strategy: self.strategies[synthesis_strategy]}
        else:
            strategies = self.strategies

        # Generate theories using each strategy
        all_theories = []
        for strategy_name, strategy_func in strategies.items():
            print(f"  Applying strategy: {strategy_name}")
            theories = strategy_func(
                explananda,
                evidence,
                contradictions,
                domain_boundaries,
                target_domains
            )
            all_theories.extend(theories)

        # Score and rank theories
        scored_theories = []
        for theory in all_theories:
            score = self._score_theory(theory, evidence, contradictions)
            theory.confidence = score
            scored_theories.append((theory, score))

        # Sort by score
        scored_theories.sort(key=lambda x: x[1], reverse=True)

        # Return top theories
        top_theories = [theory for theory, score in scored_theories[:max_theories]]

        # Store generated theories
        for theory in top_theories:
            self.generated_theories[theory.id] = theory

        print(f"  Generated {len(top_theories)} theories")
        return top_theories

    def _identify_explananda(
        self,
        evidence: Dict[str, EvidenceCluster],
        contradictions: List[Contradiction]
    ) -> List[Dict[str, Any]]:
        """Identify phenomena that need explanation"""
        explananda = []

        # Unexplained patterns in evidence
        for cluster_id, cluster in evidence.items():
            if cluster.completeness < 0.7:  # Incompletely characterized
                explananda.append({
                    'type': 'incomplete_characterization',
                    'cluster_id': cluster_id,
                    'description': f"{cluster.name} is incompletely characterized",
                    'priority': 0.7 * (1 - cluster.completeness),
                })

            if cluster.consistency < 0.9:  # Internal tension
                explananda.append({
                    'type': 'internal_tension',
                    'cluster_id': cluster_id,
                    'description': f"{cluster.name} shows internal inconsistency",
                    'priority': 0.8 * (1 - cluster.consistency),
                })

        # Contradictions
        for contradiction in contradictions:
            explananda.append({
                'type': 'contradiction',
                'contradiction_id': contradiction.id,
                'description': contradiction.description,
                'priority': contradiction.severity * contradiction.confidence,
                'resolution_needed': True,
            })

        # Sort by priority
        explananda.sort(key=lambda x: x.get('priority', 0), reverse=True)

        return explananda

    def _abductive_synthesis(
        self,
        explananda: List[Dict],
        evidence: Dict[str, EvidenceCluster],
        contradictions: List[Contradiction],
        domain_boundaries: List[DomainBoundary],
        target_domains: Optional[List[str]]
    ) -> List[TheoryFramework]:
        """Generate theories through abductive inference (inference to best explanation)"""
        theories = []

        # For each unexplained phenomenon, generate candidate explanations
        for explanandum in explananda[:5]:  # Limit to top 5
            if explanandum['type'] == 'contradiction':
                # Generate explanations that resolve contradictions
                contradiction = self.contradictions.get(explanandum['contradiction_id'])
                if contradiction:
                    theories.append(self._generate_contradiction_resolution(
                        contradiction, evidence
                    ))
            elif explanandum['type'] == 'incomplete_characterization':
                # Generate explanations for incomplete patterns
                cluster = self.evidence_clusters.get(explanandum['cluster_id'])
                if cluster:
                    theories.append(self._generate_pattern_completion(
                        cluster, evidence
                    ))

        return theories

    def _unification_synthesis(
        self,
        explananda: List[Dict],
        evidence: Dict[str, EvidenceCluster],
        contradictions: List[Contradiction],
        domain_boundaries: List[DomainBoundary],
        target_domains: Optional[List[str]]
    ) -> List[TheoryFramework]:
        """Generate theories that unify multiple phenomena"""
        theories = []

        # Look for evidence clusters in different domains that could be unified
        if len(evidence) >= 2:
            # Find patterns across domains
            cluster_ids = list(evidence.keys())

            # Try unifying pairs of clusters
            for i in range(min(3, len(cluster_ids))):
                for j in range(i+1, min(i+3, len(cluster_ids))):
                    cluster_a = evidence[cluster_ids[i]]
                    cluster_b = evidence[cluster_ids[j]]

                    # Generate unifying theory
                    theory = self._generate_unified_theory(cluster_a, cluster_b)
                    if theory:
                        theories.append(theory)

        return theories

    def _novel_entity_synthesis(
        self,
        explananda: List[Dict],
        evidence: Dict[str, EvidenceCluster],
        contradictions: List[Contradiction],
        domain_boundaries: List[DomainBoundary],
        target_domains: Optional[List[str]]
    ) -> List[TheoryFramework]:
        """Generate theories that postulate novel entities"""
        theories = []

        # Look for gaps that could be filled by novel entities
        for cluster_id, cluster in evidence.items():
            # Check if observations deviate from standard expectations
            for ev in cluster.evidence:
                if ev.value is not None and ev.unexpected:
                    # Postulate novel entity to explain unexpected observation
                    theory = self._generate_novel_entity_theory(ev, cluster)
                    if theory:
                        theories.append(theory)

        return theories

    def _boundary_crossing_synthesis(
        self,
        explananda: List[Dict],
        evidence: Dict[str, EvidenceCluster],
        contradictions: List[Contradiction],
        domain_boundaries: List[DomainBoundary],
        target_domains: Optional[List[str]]
    ) -> List[TheoryFramework]:
        """Generate theories that cross domain boundaries"""
        theories = []

        for boundary in domain_boundaries:
            # Find evidence in both domains
            evidence_a = [c for c in evidence.values() if c.domain == boundary.domain_a]
            evidence_b = [c for c in evidence.values() if c.domain == boundary.domain_b]

            if evidence_a and evidence_b:
                # Generate boundary-crossing theory
                theory = self._generate_boundary_crossing_theory(
                    boundary, evidence_a[0], evidence_b[0]
                )
                if theory:
                    theories.append(theory)

        return theories

    def _analogical_synthesis(self, *args):
        """Generate theories by analogy to known phenomena"""
        return []  # Placeholder

    def _paradigm_shift_synthesis(self, *args):
        """Generate paradigm-shifting theories"""
        return []  # Placeholder

    def _generate_contradiction_resolution(
        self,
        contradiction: Contradiction,
        evidence: Dict[str, EvidenceCluster]
    ) -> Optional[TheoryFramework]:
        """Generate a theory that resolves a contradiction"""

        # Create novel mechanism that can resolve contradiction
        mechanism = Mechanism(
            id=f"mech_res_{contradiction.id[:8]}",
            name=f"Resolution mechanism for {contradiction.id}",
            description=f"Novel mechanism that resolves: {contradiction.description}",
            confidence=0.4,
            novel=True
        )

        # Create theory framework
        theory = TheoryFramework(
            id=f"theory_res_{contradiction.id[:8]}_{int(time.time())}",
            name=f"Resolution of {contradiction.id}",
            description=f"Theory resolving {contradiction.description}",
            theory_type=TheoryType.CORRECTIVE,
            mechanisms={mechanism.id: mechanism},
            resolved_contradictions=[contradiction.id],
            confidence=0.5,
            novelty_score=0.7,
            testability=0.6,
        )

        # Generate testable prediction
        prediction = Prediction(
            id=f"pred_{theory.id}",
            description=f"Measurable signature of resolution mechanism",
            observable="testable_observable",
            testability=0.7,
            required_facilities=["general_purpose"]
        )
        theory.predictions[prediction.id] = prediction

        return theory

    def _generate_pattern_completion(
        self,
        cluster: EvidenceCluster,
        evidence: Dict[str, EvidenceCluster]
    ) -> Optional[TheoryFramework]:
        """Generate a theory that completes an incomplete pattern"""

        # Infer missing mechanism from existing evidence
        mechanism = Mechanism(
            id=f"mech_comp_{cluster.id[:8]}",
            name=f"Completion mechanism for {cluster.name}",
            description=f"Mechanism explaining pattern in {cluster.name}",
            confidence=0.5,
            novel=True
        )

        theory = TheoryFramework(
            id=f"theory_comp_{cluster.id[:8]}_{int(time.time())}",
            name=f"Theory of {cluster.name}",
            description=f"Explains observed pattern in {cluster.name}",
            theory_type=TheoryType.PHENOMENOLOGICAL,
            mechanisms={mechanism.id: mechanism},
            explained_evidence=[cluster.id],
            confidence=0.6,
            novelty_score=0.5,
            testability=0.7,
        )

        # Add predictions
        prediction = Prediction(
            id=f"pred_{theory.id}",
            description=f"Predicted behavior in untested regimes",
            observable="pattern_continuation",
            testability=0.8,
        )
        theory.predictions[prediction.id] = prediction

        return theory

    def _generate_unified_theory(
        self,
        cluster_a: EvidenceCluster,
        cluster_b: EvidenceCluster
    ) -> Optional[TheoryFramework]:
        """Generate a theory unifying two phenomena"""

        # Create unifying mechanism
        mechanism = Mechanism(
            id=f"mech_unif_{cluster_a.id[:4]}_{cluster_b.id[:4]}",
            name=f"Unified mechanism for {cluster_a.name} and {cluster_b.name}",
            description=f"Common mechanism underlying {cluster_a.name} and {cluster_b.name}",
            confidence=0.4,
            novel=True
        )

        theory = TheoryFramework(
            id=f"theory_unif_{cluster_a.id[:4]}_{cluster_b.id[:4]}_{int(time.time())}",
            name=f"Unified theory of {cluster_a.name} and {cluster_b.name}",
            description=f"Unifies {cluster_a.name} ({cluster_a.domain}) and "
                       f"{cluster_b.name} ({cluster_b.domain})",
            theory_type=TheoryType.UNIFYING,
            mechanisms={mechanism.id: mechanism},
            explained_evidence=[cluster_a.id, cluster_b.id],
            unification_power=0.7,
            confidence=0.5,
            novelty_score=0.8,
            testability=0.6,
        )

        return theory

    def _generate_novel_entity_theory(
        self,
        evidence_item: Evidence,
        cluster: EvidenceCluster
    ) -> Optional[TheoryFramework]:
        """Generate a theory postulating a novel entity"""

        # Create novel entity
        entity = Entity(
            id=f"entity_{evidence_item.id[:8]}",
            name=f"Novel entity explaining {evidence_item.id}",
            entity_type="unknown",
            novel=True,
            theoretical_motivation=f"Explains unexpected observation: {evidence_item.description}",
            observability=0.5
        )

        theory = TheoryFramework(
            id=f"theory_entity_{evidence_item.id[:8]}_{int(time.time())}",
            name=f"Theory of novel entity in {cluster.name}",
            description=f"Postulates novel entity to explain {evidence_item.description}",
            theory_type=TheoryType.MECHANISTIC,
            entities={entity.id: entity},
            explained_evidence=[cluster.id],
            confidence=0.3,
            novelty_score=0.9,
            testability=0.5,
        )

        return theory

    def _generate_boundary_crossing_theory(
        self,
        boundary: DomainBoundary,
        cluster_a: EvidenceCluster,
        cluster_b: EvidenceCluster
    ) -> Optional[TheoryFramework]:
        """Generate a theory that crosses a domain boundary"""

        mechanism = Mechanism(
            id=f"mech_bound_{boundary.id[:8]}",
            name=f"Boundary-crossing mechanism",
            description=f"Mechanism connecting {boundary.domain_a} to {boundary.domain_b}",
            confidence=0.4,
            novel=True
        )

        theory = TheoryFramework(
            id=f"theory_bound_{boundary.id[:8]}_{int(time.time())}",
            name=f"Bridge theory: {boundary.domain_a} ↔ {boundary.domain_b}",
            description=f"Theory connecting {boundary.domain_a} and {boundary.domain_b}",
            theory_type=TheoryType.UNIFYING,
            mechanisms={mechanism.id: mechanism},
            explained_evidence=[cluster_a.id, cluster_b.id],
            unification_power=0.8,
            confidence=0.5,
            novelty_score=0.9,
            testability=0.5,
        )

        return theory

    def _score_theory(
        self,
        theory: TheoryFramework,
        evidence: Dict[str, EvidenceCluster],
        contradictions: List[Contradiction]
    ) -> float:
        """Score a theory on multiple dimensions"""
        score = 0.0

        # Explanatory power (30%)
        explained = len(theory.explained_evidence)
        resolved = len(theory.resolved_contradictions)
        explanatory_score = (explained * 0.02 + resolved * 0.3) / (1 + explained * 0.02)
        score += 0.3 * explanatory_score

        # Unification power (20%)
        score += 0.2 * theory.unification_power

        # Testability (20%)
        score += 0.2 * theory.testability

        # Novelty (15%)
        score += 0.15 * theory.novelty_score

        # Simplicity (15%)
        # Penalize too many entities/mechanisms
        complexity = len(theory.entities) + len(theory.mechanisms)
        simplicity_score = 1.0 / (1.0 + 0.1 * complexity)
        score += 0.15 * simplicity_score

        return max(0, min(1, score))


# =============================================================================
# Factory Functions
# =============================================================================

def create_theory_synthesis_engine() -> TheorySynthesisEngine:
    """Create a theory synthesis engine"""
    return TheorySynthesisEngine()


# =============================================================================
# Convenience Functions
# =============================================================================

def synthesize_theory(
    evidence: Dict[str, EvidenceCluster],
    contradictions: List[Contradiction],
    domain_boundaries: Optional[List[DomainBoundary]] = None
) -> List[TheoryFramework]:
    """
    Convenience function to synthesize theories.

    Parameters
    ----------
    evidence : dict
        Evidence clusters
    contradictions : list
        Contradictions to resolve
    domain_boundaries : list, optional
        Domain boundaries

    Returns
    -------
    List of synthesized theories
    """
    engine = create_theory_synthesis_engine()
    return engine.synthesize_theory(
        evidence=evidence,
        contradictions=contradictions,
        domain_boundaries=domain_boundaries or [],
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enumerations
    'TheoryType',
    'ConfidenceLevel',
    'NovelType',

    # Data structures
    'Evidence',
    'EvidenceCluster',
    'Contradiction',
    'DomainBoundary',
    'Entity',
    'Mechanism',
    'Prediction',
    'TheoryFramework',

    # Main class
    'TheorySynthesisEngine',
    'create_theory_synthesis_engine',
    'synthesize_theory',
]
