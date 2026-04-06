"""
MORK: Modular Ontology Reasoning Kernel

Provides hierarchical ontological structure for organizing V36's symbolic knowledge,
enabling semantic search and reasoning over causal concepts.

Integration with V36:
- Maps SymbolicTemplate enum to ontology nodes
- Provides semantic distance for FunctionalRole comparisons
- Enables inheritance-based reasoning for constraint propagation

Date: 2025-11-27
Version: 37.0
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
import json


class SemanticRelationType(Enum):
    """Types of semantic relations in the ontology"""
    IS_A = "is_a"                    # Subsumption (child IS_A parent)
    HAS_PART = "has_part"            # Mereological (whole HAS_PART part)
    CAUSES = "causes"                # Causal (A CAUSES B)
    PRECEDES = "precedes"            # Temporal (A PRECEDES B)
    INCOMPATIBLE = "incompatible"    # Mutual exclusion
    ANALOGOUS = "analogous"          # Functional similarity
    INSTANCE_OF = "instance_of"      # Class membership


@dataclass
class OntologyNode:
    """A node in the MORK ontology hierarchy"""
    concept_id: str
    concept_name: str
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    domain_scope: List[str] = field(default_factory=lambda: ["ALL"])

    def __hash__(self):
        return hash(self.concept_id)


@dataclass
class SemanticRelation:
    """A semantic relation between two concepts"""
    source_id: str
    relation_type: SemanticRelationType
    target_id: str
    strength: float = 1.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MORKOntology:
    """
    Modular Ontology Reasoning Kernel

    Provides:
    - Hierarchical concept organization for V36 symbolic templates
    - Semantic relations (IS_A, CAUSES, INCOMPATIBLE, etc.)
    - Ontological distance for similarity computation
    - Inheritance of properties down the hierarchy
    - V36-specific mappings for templates and functional roles
    """

    def __init__(self):
        self.nodes: Dict[str, OntologyNode] = {}
        self.relations: List[SemanticRelation] = []
        self.root_id = "ROOT"

        # Build V36-compatible ontology
        self._build_core_hierarchy()
        self._build_v36_template_mappings()
        self._build_v36_functional_roles()
        self._build_semantic_relations()

    def _build_core_hierarchy(self):
        """Build the core concept hierarchy"""
        # Root concept
        self._add_node("ROOT", "CausalConcept", None, {
            "description": "Root of all causal concepts"
        })

        # Level 1: Major categories
        self._add_node("TEMPORAL_DYNAMIC", "TemporalDynamic", "ROOT", {
            "description": "Concepts with temporal evolution"
        })
        self._add_node("NONLINEAR_TRANSFORM", "NonlinearTransform", "ROOT", {
            "description": "Nonlinear observation functions"
        })
        self._add_node("REGIME_DYNAMIC", "RegimeDynamic", "ROOT", {
            "description": "Regime-dependent behavior"
        })
        self._add_node("FUNCTIONAL_ROLE", "FunctionalRole", "ROOT", {
            "description": "Functional roles of latent variables"
        })
        self._add_node("CONSTRAINT", "Constraint", "ROOT", {
            "description": "Prohibitive constraints and exclusions"
        })
        self._add_node("DOMAIN", "Domain", "ROOT", {
            "description": "Scientific domains"
        })

    def _build_v36_template_mappings(self):
        """Build nodes for V36 SymbolicTemplate enum"""
        # Autoregressive subcategory
        self._add_node("AUTOREGRESSIVE", "Autoregressive", "TEMPORAL_DYNAMIC", {
            "description": "Autoregressive dynamics"
        })

        # V36 SymbolicTemplate mappings
        self._add_node("STABLE_AR", "StableAutoregressive", "AUTOREGRESSIVE", {
            "ar_coefficient_min": 0.95,
            "ar_coefficient_max": 1.0,
            "v36_template": "STABLE_AUTOREGRESSIVE",
            "persistence": "VERY_HIGH"
        })

        self._add_node("RESPONSIVE_AR", "ResponsiveAutoregressive", "AUTOREGRESSIVE", {
            "ar_coefficient_min": 0.7,
            "ar_coefficient_max": 0.95,
            "v36_template": "RESPONSIVE_AUTOREGRESSIVE",
            "persistence": "MODERATE"
        })

        self._add_node("UNSTABLE_AR", "UnstableAutoregressive", "AUTOREGRESSIVE", {
            "ar_coefficient_min": 0.0,
            "ar_coefficient_max": 0.7,
            "v36_template": "UNSTABLE_AUTOREGRESSIVE",
            "persistence": "LOW"
        })

        self._add_node("DELAYED_RESPONSE", "DelayedResponse", "TEMPORAL_DYNAMIC", {
            "min_delay": 5,
            "v36_template": "DELAYED_RESPONSE"
        })

        # Nonlinear transforms
        self._add_node("EXPONENTIAL", "Exponential", "NONLINEAR_TRANSFORM", {
            "v36_template": "NONLINEAR_EXPONENTIAL",
            "function_family": "exp"
        })

        self._add_node("MULTIPLICATIVE", "Multiplicative", "NONLINEAR_TRANSFORM", {
            "v36_template": "NONLINEAR_MULTIPLICATIVE",
            "function_family": "product"
        })

        self._add_node("LOGARITHMIC", "Logarithmic", "NONLINEAR_TRANSFORM", {
            "function_family": "log"
        })

        self._add_node("POLYNOMIAL", "Polynomial", "NONLINEAR_TRANSFORM", {
            "function_family": "polynomial"
        })

        # Regime dynamics
        self._add_node("REGIME_DEPENDENT", "RegimeDependent", "REGIME_DYNAMIC", {
            "v36_template": "REGIME_DEPENDENT",
            "structure": "PIECEWISE"
        })

        # Blended (V36 L7)
        self._add_node("BLENDED", "BlendedObservation", "NONLINEAR_TRANSFORM", {
            "v36_law": "L7",
            "description": "Blended observation functions (polynomial + exponential, etc.)"
        })

    def _build_v36_functional_roles(self):
        """Build nodes for V36 FunctionalRole types"""
        # Functional roles
        self._add_node("SLOW_DRIVER", "SlowDriver", "FUNCTIONAL_ROLE", {
            "timescale_category": "slow",
            "causal_position": "driver",
            "ar_coefficient_typical": 0.995
        })

        self._add_node("FAST_RESPONDER", "FastResponder", "FUNCTIONAL_ROLE", {
            "timescale_category": "fast",
            "causal_position": "outcome",
            "ar_coefficient_typical": 0.7
        })

        self._add_node("MID_MEDIATOR", "MidMediator", "FUNCTIONAL_ROLE", {
            "timescale_category": "mid",
            "causal_position": "mediator",
            "ar_coefficient_typical": 0.93
        })

        self._add_node("NESTED_MEDIATOR", "NestedMediator", "FUNCTIONAL_ROLE", {
            "timescale_category": "mid",
            "causal_position": "mediator"
        })

        self._add_node("REGIME_DETECTOR", "RegimeDetector", "FUNCTIONAL_ROLE", {
            "regime_sensitivity_min": 0.5
        })

        self._add_node("TRANSMISSION_DRIVER", "TransmissionDriver", "FUNCTIONAL_ROLE", {
            "timescale_category": "slow",
            "domain_scope": ["D1"]
        })

        self._add_node("BEHAVIOUR_MODERATOR", "BehaviourModerator", "FUNCTIONAL_ROLE", {
            "timescale_category": "mid",
            "domain_scope": ["D1"]
        })

        self._add_node("MACRO_SENTIMENT", "MacroSentiment", "FUNCTIONAL_ROLE", {
            "timescale_category": "slow",
            "domain_scope": ["D2"]
        })

        self._add_node("POLICY_PRESSURE", "PolicyPressure", "FUNCTIONAL_ROLE", {
            "timescale_category": "mid",
            "domain_scope": ["D2"]
        })

    def _build_semantic_relations(self):
        """Build semantic relations between concepts"""
        # Incompatibility relations (from V36 mutual exclusions)
        self._add_relation("STABLE_AR", SemanticRelationType.INCOMPATIBLE, "UNSTABLE_AR")
        self._add_relation("EXPONENTIAL", SemanticRelationType.INCOMPATIBLE, "LOGARITHMIC",
                          strength=0.5)  # Weak incompatibility

        # Causal relations
        self._add_relation("SLOW_DRIVER", SemanticRelationType.CAUSES, "FAST_RESPONDER")
        self._add_relation("SLOW_DRIVER", SemanticRelationType.CAUSES, "MID_MEDIATOR")
        self._add_relation("MID_MEDIATOR", SemanticRelationType.CAUSES, "FAST_RESPONDER")

        # Analogous relations (cross-domain)
        self._add_relation("SLOW_DRIVER", SemanticRelationType.ANALOGOUS, "MACRO_SENTIMENT",
                          metadata={"domains": ["CLD", "D2"]})
        self._add_relation("SLOW_DRIVER", SemanticRelationType.ANALOGOUS, "TRANSMISSION_DRIVER",
                          metadata={"domains": ["CLD", "D1"]})
        self._add_relation("FAST_RESPONDER", SemanticRelationType.ANALOGOUS, "POLICY_PRESSURE",
                          metadata={"domains": ["CLD", "D2"]})

        # Build domains
        for domain_id, domain_name in [("CLD", "CausalLabDomain"),
                                        ("D1", "Epidemiology"),
                                        ("D2", "Economics")]:
            self._add_node(domain_id, domain_name, "DOMAIN", {
                "domain_id": domain_id
            })

        # Build constraints (from V36 prohibitive constraints)
        self._add_node("N1", "NoInstantaneousFeedback", "CONSTRAINT", {
            "severity": "FATAL",
            "statement": "No X_t → Y_t → X_t without delay"
        })
        self._add_node("N2", "NoRegimeTimescaleJumps", "CONSTRAINT", {
            "severity": "MODERATE",
            "statement": "AR coefficients cannot jump discontinuously across regimes"
        })
        self._add_node("N3", "NoUnboundedGrowthStationary", "CONSTRAINT", {
            "severity": "STRONG",
            "statement": "Cannot have exp(λt) with λ>0 in stationary domain"
        })

    def _add_node(self, concept_id: str, concept_name: str,
                  parent_id: Optional[str], properties: Dict[str, Any] = None):
        """Add a node to the ontology"""
        node = OntologyNode(
            concept_id=concept_id,
            concept_name=concept_name,
            parent_id=parent_id,
            properties=properties or {}
        )
        self.nodes[concept_id] = node

        # Update parent's children list
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children_ids.append(concept_id)

    def _add_relation(self, source_id: str, relation_type: SemanticRelationType,
                      target_id: str, strength: float = 1.0,
                      metadata: Dict[str, Any] = None):
        """Add a semantic relation"""
        relation = SemanticRelation(
            source_id=source_id,
            relation_type=relation_type,
            target_id=target_id,
            strength=strength,
            metadata=metadata or {}
        )
        self.relations.append(relation)

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    def get_node(self, concept_id: str) -> Optional[OntologyNode]:
        """Get a node by ID"""
        return self.nodes.get(concept_id)

    def get_ancestors(self, concept_id: str) -> List[str]:
        """Get all ancestors of a concept (path to root)"""
        ancestors = []
        current = concept_id
        while current and current in self.nodes:
            node = self.nodes[current]
            if node.parent_id:
                ancestors.append(node.parent_id)
                current = node.parent_id
            else:
                break
        return ancestors

    def get_descendants(self, concept_id: str) -> List[str]:
        """Get all descendants of a concept"""
        descendants = []
        to_visit = [concept_id]
        while to_visit:
            current = to_visit.pop(0)
            if current in self.nodes:
                children = self.nodes[current].children_ids
                descendants.extend(children)
                to_visit.extend(children)
        return descendants

    def get_siblings(self, concept_id: str) -> List[str]:
        """Get sibling concepts (same parent)"""
        if concept_id not in self.nodes:
            return []
        parent_id = self.nodes[concept_id].parent_id
        if not parent_id or parent_id not in self.nodes:
            return []
        return [c for c in self.nodes[parent_id].children_ids if c != concept_id]

    def ontological_distance(self, concept_a: str, concept_b: str) -> float:
        """
        Compute ontological distance between two concepts.

        Distance = path length through lowest common ancestor
        Normalized to [0, 1] where 0 = same concept, 1 = maximally distant
        """
        if concept_a == concept_b:
            return 0.0

        if concept_a not in self.nodes or concept_b not in self.nodes:
            return 1.0

        # Get ancestors including self
        ancestors_a = [concept_a] + self.get_ancestors(concept_a)
        ancestors_b = [concept_b] + self.get_ancestors(concept_b)

        # Find lowest common ancestor
        lca = None
        lca_depth_a = 0
        lca_depth_b = 0

        for i, anc_a in enumerate(ancestors_a):
            if anc_a in ancestors_b:
                lca = anc_a
                lca_depth_a = i
                lca_depth_b = ancestors_b.index(anc_a)
                break

        if lca is None:
            return 1.0

        # Distance = sum of depths to LCA, normalized
        path_length = lca_depth_a + lca_depth_b
        max_depth = max(len(ancestors_a), len(ancestors_b))

        return min(1.0, path_length / (2 * max_depth)) if max_depth > 0 else 0.0

    def semantic_similarity(self, concept_a: str, concept_b: str) -> float:
        """
        Compute semantic similarity (1 - distance).
        Accounts for both hierarchy and explicit ANALOGOUS relations.
        """
        base_similarity = 1.0 - self.ontological_distance(concept_a, concept_b)

        # Boost similarity if explicit ANALOGOUS relation exists
        for rel in self.relations:
            if rel.relation_type == SemanticRelationType.ANALOGOUS:
                if (rel.source_id == concept_a and rel.target_id == concept_b) or \
                   (rel.source_id == concept_b and rel.target_id == concept_a):
                    base_similarity = max(base_similarity, 0.8 * rel.strength)

        return base_similarity

    def are_incompatible(self, concept_a: str, concept_b: str) -> Tuple[bool, float]:
        """
        Check if two concepts are incompatible.
        Returns (is_incompatible, strength)
        """
        for rel in self.relations:
            if rel.relation_type == SemanticRelationType.INCOMPATIBLE:
                if (rel.source_id == concept_a and rel.target_id == concept_b) or \
                   (rel.source_id == concept_b and rel.target_id == concept_a):
                    return True, rel.strength
        return False, 0.0

    def get_related(self, concept_id: str,
                    relation_type: Optional[SemanticRelationType] = None) -> List[Tuple[str, SemanticRelation]]:
        """Get all concepts related to a given concept"""
        related = []
        for rel in self.relations:
            if rel.source_id == concept_id:
                if relation_type is None or rel.relation_type == relation_type:
                    related.append((rel.target_id, rel))
            elif rel.target_id == concept_id:
                if relation_type is None or rel.relation_type == relation_type:
                    related.append((rel.source_id, rel))
        return related

    def inherit_properties(self, concept_id: str) -> Dict[str, Any]:
        """
        Get all properties for a concept, including inherited from ancestors.
        Child properties override parent properties.
        """
        if concept_id not in self.nodes:
            return {}

        # Get ancestors from root to node
        ancestors = self.get_ancestors(concept_id)
        ancestors.reverse()  # Root first

        # Merge properties (later overrides earlier)
        merged = {}
        for anc_id in ancestors:
            if anc_id in self.nodes:
                merged.update(self.nodes[anc_id].properties)
        merged.update(self.nodes[concept_id].properties)

        return merged

    # =========================================================================
    # V36 INTEGRATION METHODS
    # =========================================================================

    def map_v36_template(self, template_name: str) -> Optional[str]:
        """Map V36 SymbolicTemplate name to ontology concept ID"""
        template_mapping = {
            "STABLE_AUTOREGRESSIVE": "STABLE_AR",
            "RESPONSIVE_AUTOREGRESSIVE": "RESPONSIVE_AR",
            "UNSTABLE_AUTOREGRESSIVE": "UNSTABLE_AR",
            "DELAYED_RESPONSE": "DELAYED_RESPONSE",
            "NONLINEAR_EXPONENTIAL": "EXPONENTIAL",
            "NONLINEAR_MULTIPLICATIVE": "MULTIPLICATIVE",
            "REGIME_DEPENDENT": "REGIME_DEPENDENT"
        }
        return template_mapping.get(template_name)

    def map_v36_functional_role(self, role_type: str) -> Optional[str]:
        """Map V36 FunctionalRole type to ontology concept ID"""
        role_mapping = {
            "slow_driver": "SLOW_DRIVER",
            "fast_responder": "FAST_RESPONDER",
            "mid_mediator": "MID_MEDIATOR",
            "nested_mediator": "NESTED_MEDIATOR",
            "regime_detector": "REGIME_DETECTOR",
            "transmission_driver": "TRANSMISSION_DRIVER",
            "behaviour_moderator": "BEHAVIOUR_MODERATOR",
            "macro_sentiment": "MACRO_SENTIMENT",
            "policy_pressure": "POLICY_PRESSURE"
        }
        return role_mapping.get(role_type)

    def find_analogous_roles(self, role_type: str, target_domain: str) -> List[Tuple[str, float]]:
        """
        Find analogous functional roles in a target domain.
        Returns list of (role_concept_id, similarity_score).
        """
        source_concept = self.map_v36_functional_role(role_type)
        if not source_concept:
            return []

        analogous = []
        for rel in self.relations:
            if rel.relation_type == SemanticRelationType.ANALOGOUS:
                if rel.source_id == source_concept:
                    target = rel.target_id
                elif rel.target_id == source_concept:
                    target = rel.source_id
                else:
                    continue

                # Check if target is in desired domain
                if target in self.nodes:
                    target_domains = self.nodes[target].properties.get("domain_scope", ["ALL"])
                    if target_domain in target_domains or "ALL" in target_domains:
                        analogous.append((target, rel.strength))

        return sorted(analogous, key=lambda x: x[1], reverse=True)

    def rank_by_ontology(self, query_concept: str,
                         candidates: List[str]) -> List[Tuple[str, float]]:
        """
        Rank candidates by ontological similarity to query.
        Used by RRF for ontology-based ranking.
        """
        rankings = []
        for candidate in candidates:
            similarity = self.semantic_similarity(query_concept, candidate)
            rankings.append((candidate, similarity))
        return sorted(rankings, key=lambda x: x[1], reverse=True)

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict:
        """Serialize ontology to dictionary"""
        return {
            "nodes": {
                nid: {
                    "concept_id": n.concept_id,
                    "concept_name": n.concept_name,
                    "parent_id": n.parent_id,
                    "children_ids": n.children_ids,
                    "properties": n.properties,
                    "domain_scope": n.domain_scope
                }
                for nid, n in self.nodes.items()
            },
            "relations": [
                {
                    "source_id": r.source_id,
                    "relation_type": r.relation_type.value,
                    "target_id": r.target_id,
                    "strength": r.strength,
                    "metadata": r.metadata
                }
                for r in self.relations
            ]
        }

    def save(self, filepath: str):
        """Save ontology to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'MORKOntology':
        """Load ontology from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        ontology = cls.__new__(cls)
        ontology.nodes = {}
        ontology.relations = []
        ontology.root_id = "ROOT"

        for nid, ndata in data["nodes"].items():
            ontology.nodes[nid] = OntologyNode(
                concept_id=ndata["concept_id"],
                concept_name=ndata["concept_name"],
                parent_id=ndata["parent_id"],
                children_ids=ndata["children_ids"],
                properties=ndata["properties"],
                domain_scope=ndata.get("domain_scope", ["ALL"])
            )

        for rdata in data["relations"]:
            ontology.relations.append(SemanticRelation(
                source_id=rdata["source_id"],
                relation_type=SemanticRelationType(rdata["relation_type"]),
                target_id=rdata["target_id"],
                strength=rdata["strength"],
                metadata=rdata["metadata"]
            ))

        return ontology


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'MORKOntology',
    'OntologyNode',
    'SemanticRelation',
    'SemanticRelationType'
]
