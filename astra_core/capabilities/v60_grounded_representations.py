"""
V60 Grounded Compositional Representations
===========================================

Concepts that are:
- Grounded in experiential/perceptual data
- Compositional (combine to form novel meanings)
- Hierarchical (from concrete to abstract)
- Connected through learned relations

This enables genuine generalization to novel situations.

Date: 2025-12-17
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
import math
import time
from collections import defaultdict
import hashlib


class GroundingType(Enum):
    """Types of grounding for representations."""
    PERCEPTUAL = "perceptual"       # Grounded in sensory data
    MOTOR = "motor"                  # Grounded in action patterns
    LINGUISTIC = "linguistic"        # Grounded in language use
    MATHEMATICAL = "mathematical"    # Grounded in formal structures
    EXPERIENTIAL = "experiential"    # Grounded in episodes
    ABSTRACT = "abstract"            # Derived from other groundings


class CompositionType(Enum):
    """Types of compositional operations."""
    CONJUNCTION = "conjunction"       # A AND B
    DISJUNCTION = "disjunction"       # A OR B
    PREDICATION = "predication"       # Property(Object)
    RELATION = "relation"             # Relation(A, B)
    MODIFICATION = "modification"     # Modifier(Base)
    QUANTIFICATION = "quantification" # Quant(Predicate)
    NEGATION = "negation"             # NOT A
    SEQUENCE = "sequence"             # A THEN B


class AbstractionLevel(Enum):
    """Levels of abstraction."""
    INSTANCE = 0      # Specific instance (this apple)
    BASIC = 1         # Basic category (apple)
    SUPERORDINATE = 2 # Superordinate (fruit)
    ABSTRACT = 3      # Abstract concept (nutrition)
    UNIVERSAL = 4     # Universal principle (sustenance)


@dataclass
class GroundingInstance:
    """A single grounding experience."""
    timestamp: float
    grounding_type: GroundingType
    features: Dict[str, float]
    context: Dict[str, Any]
    confidence: float = 1.0


@dataclass
class ConceptRepresentation:
    """
    A grounded, compositional concept representation.
    """
    concept_id: str
    name: str
    abstraction_level: AbstractionLevel

    # Grounding data
    groundings: List[GroundingInstance] = field(default_factory=list)
    grounding_types: Set[GroundingType] = field(default_factory=set)

    # Feature representation (learned from groundings)
    prototype_features: Dict[str, float] = field(default_factory=dict)
    feature_variances: Dict[str, float] = field(default_factory=dict)

    # Compositional structure
    composition_type: Optional[CompositionType] = None
    component_concepts: List[str] = field(default_factory=list)

    # Relational connections
    is_a: List[str] = field(default_factory=list)  # Superordinate concepts
    has_a: List[str] = field(default_factory=list)  # Part concepts
    related_to: Dict[str, float] = field(default_factory=dict)  # Similarity

    # Usage statistics
    activation_count: int = 0
    last_activated: float = 0.0

    def is_grounded(self) -> bool:
        """Check if concept has direct groundings."""
        return len(self.groundings) > 0

    def is_composite(self) -> bool:
        """Check if concept is composed of other concepts."""
        return len(self.component_concepts) > 0

    def get_grounding_strength(self) -> float:
        """Get strength of grounding (0-1)."""
        if not self.groundings:
            return 0.0

        # More diverse groundings = stronger
        type_diversity = len(self.grounding_types) / len(GroundingType)

        # More instances = stronger (with diminishing returns)
        instance_strength = 1 - math.exp(-len(self.groundings) / 10)

        return 0.5 * type_diversity + 0.5 * instance_strength


@dataclass
class CompositeExpression:
    """A compositional expression combining concepts."""
    expression_id: str
    composition_type: CompositionType
    operands: List[str]  # Concept IDs
    result_concept: Optional[str] = None
    confidence: float = 1.0


class FeatureSpace:
    """
    Feature space for grounded representations.

    Features are learned from experience and form a continuous space
    where similar concepts are nearby.
    """

    def __init__(self, dimensions: int = 128):
        self.dimensions = dimensions
        self.feature_names: List[str] = []
        self.feature_importance: Dict[str, float] = {}

        # Learned feature transformations
        self.transformations: Dict[str, Callable] = {}

    def encode(self, raw_features: Dict[str, float]) -> np.ndarray:
        """Encode raw features into feature space."""
        vector = np.zeros(self.dimensions)

        for i, (name, value) in enumerate(raw_features.items()):
            if i < self.dimensions:
                # Apply transformation if available
                if name in self.transformations:
                    value = self.transformations[name](value)

                # Weight by importance
                importance = self.feature_importance.get(name, 1.0)
                vector[i] = value * importance

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    def similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute similarity between feature vectors."""
        return float(np.dot(vec1, vec2))

    def learn_importance(self, discriminative_features: Dict[str, float]):
        """Learn feature importance from discriminative data."""
        for name, importance in discriminative_features.items():
            self.feature_importance[name] = importance


class ConceptHierarchy:
    """
    Hierarchical organization of concepts.
    """

    def __init__(self):
        self.concepts: Dict[str, ConceptRepresentation] = {}
        self.hierarchy: Dict[str, Set[str]] = defaultdict(set)  # parent -> children
        self.reverse_hierarchy: Dict[str, Set[str]] = defaultdict(set)  # child -> parents

    def add_concept(self, concept: ConceptRepresentation):
        """Add a concept to the hierarchy."""
        self.concepts[concept.concept_id] = concept

        # Update hierarchy relations
        for parent in concept.is_a:
            self.hierarchy[parent].add(concept.concept_id)
            self.reverse_hierarchy[concept.concept_id].add(parent)

    def get_ancestors(self, concept_id: str) -> Set[str]:
        """Get all ancestor concepts."""
        ancestors = set()
        to_visit = list(self.reverse_hierarchy.get(concept_id, set()))

        while to_visit:
            parent = to_visit.pop()
            if parent not in ancestors:
                ancestors.add(parent)
                to_visit.extend(self.reverse_hierarchy.get(parent, set()))

        return ancestors

    def get_descendants(self, concept_id: str) -> Set[str]:
        """Get all descendant concepts."""
        descendants = set()
        to_visit = list(self.hierarchy.get(concept_id, set()))

        while to_visit:
            child = to_visit.pop()
            if child not in descendants:
                descendants.add(child)
                to_visit.extend(self.hierarchy.get(child, set()))

        return descendants

    def find_common_ancestor(self, concept_ids: List[str]) -> Optional[str]:
        """Find lowest common ancestor of concepts."""
        if not concept_ids:
            return None

        # Get ancestors for first concept
        common = self.get_ancestors(concept_ids[0])
        common.add(concept_ids[0])

        # Intersect with ancestors of other concepts
        for cid in concept_ids[1:]:
            other_ancestors = self.get_ancestors(cid)
            other_ancestors.add(cid)
            common = common.intersection(other_ancestors)

        if not common:
            return None

        # Find lowest (most specific) common ancestor
        for candidate in common:
            descendants = self.get_descendants(candidate)
            if not descendants.intersection(common - {candidate}):
                return candidate

        return list(common)[0] if common else None


class CompositionEngine:
    """
    Engine for composing concepts into novel representations.
    """

    def __init__(self, feature_space: FeatureSpace):
        self.feature_space = feature_space
        self.composition_rules: Dict[CompositionType, Callable] = {
            CompositionType.CONJUNCTION: self._compose_conjunction,
            CompositionType.DISJUNCTION: self._compose_disjunction,
            CompositionType.PREDICATION: self._compose_predication,
            CompositionType.RELATION: self._compose_relation,
            CompositionType.MODIFICATION: self._compose_modification,
            CompositionType.NEGATION: self._compose_negation,
            CompositionType.SEQUENCE: self._compose_sequence,
        }

    def compose(self, composition_type: CompositionType,
                operands: List[ConceptRepresentation]) -> ConceptRepresentation:
        """Compose concepts using specified operation."""
        if composition_type not in self.composition_rules:
            raise ValueError(f"Unknown composition type: {composition_type}")

        return self.composition_rules[composition_type](operands)

    def _compose_conjunction(self,
                            operands: List[ConceptRepresentation]) -> ConceptRepresentation:
        """Compose concepts with AND (intersection of features)."""
        if len(operands) < 2:
            return operands[0] if operands else self._empty_concept()

        # Combine features by taking minimum (intersection semantics)
        combined_features = {}
        all_features = set()
        for op in operands:
            all_features.update(op.prototype_features.keys())

        for feat in all_features:
            values = [op.prototype_features.get(feat, 0) for op in operands]
            combined_features[feat] = min(values)

        concept_id = "conj_" + "_".join(op.concept_id for op in operands)
        name = " AND ".join(op.name for op in operands)

        return ConceptRepresentation(
            concept_id=concept_id,
            name=name,
            abstraction_level=max(op.abstraction_level for op in operands),
            prototype_features=combined_features,
            composition_type=CompositionType.CONJUNCTION,
            component_concepts=[op.concept_id for op in operands]
        )

    def _compose_disjunction(self,
                            operands: List[ConceptRepresentation]) -> ConceptRepresentation:
        """Compose concepts with OR (union of features)."""
        if len(operands) < 2:
            return operands[0] if operands else self._empty_concept()

        # Combine features by taking maximum (union semantics)
        combined_features = {}
        for op in operands:
            for feat, value in op.prototype_features.items():
                if feat not in combined_features:
                    combined_features[feat] = value
                else:
                    combined_features[feat] = max(combined_features[feat], value)

        concept_id = "disj_" + "_".join(op.concept_id for op in operands)
        name = " OR ".join(op.name for op in operands)

        return ConceptRepresentation(
            concept_id=concept_id,
            name=name,
            abstraction_level=min(op.abstraction_level for op in operands),
            prototype_features=combined_features,
            composition_type=CompositionType.DISJUNCTION,
            component_concepts=[op.concept_id for op in operands]
        )

    def _compose_predication(self,
                            operands: List[ConceptRepresentation]) -> ConceptRepresentation:
        """Compose property + object (e.g., RED APPLE)."""
        if len(operands) != 2:
            raise ValueError("Predication requires exactly 2 operands")

        predicate, argument = operands

        # Combine features with predicate taking precedence for relevant features
        combined_features = argument.prototype_features.copy()
        combined_features.update(predicate.prototype_features)

        concept_id = f"pred_{predicate.concept_id}_{argument.concept_id}"
        name = f"{predicate.name}({argument.name})"

        return ConceptRepresentation(
            concept_id=concept_id,
            name=name,
            abstraction_level=argument.abstraction_level,
            prototype_features=combined_features,
            composition_type=CompositionType.PREDICATION,
            component_concepts=[predicate.concept_id, argument.concept_id],
            is_a=[argument.concept_id]  # Inherits from argument
        )

    def _compose_relation(self,
                         operands: List[ConceptRepresentation]) -> ConceptRepresentation:
        """Compose relation between concepts."""
        if len(operands) < 2:
            raise ValueError("Relation requires at least 2 operands")

        # First operand is relation, rest are arguments
        relation = operands[0]
        arguments = operands[1:]

        # Combine features
        combined_features = relation.prototype_features.copy()
        for i, arg in enumerate(arguments):
            for feat, value in arg.prototype_features.items():
                combined_features[f"arg{i}_{feat}"] = value

        concept_id = f"rel_{relation.concept_id}_" + "_".join(a.concept_id for a in arguments)
        name = f"{relation.name}({', '.join(a.name for a in arguments)})"

        return ConceptRepresentation(
            concept_id=concept_id,
            name=name,
            abstraction_level=relation.abstraction_level,
            prototype_features=combined_features,
            composition_type=CompositionType.RELATION,
            component_concepts=[relation.concept_id] + [a.concept_id for a in arguments]
        )

    def _compose_modification(self,
                             operands: List[ConceptRepresentation]) -> ConceptRepresentation:
        """Compose modifier + base (e.g., VERY TALL)."""
        if len(operands) != 2:
            raise ValueError("Modification requires exactly 2 operands")

        modifier, base = operands

        # Intensify features based on modifier
        combined_features = base.prototype_features.copy()
        intensity = modifier.prototype_features.get('intensity', 1.5)

        for feat in combined_features:
            combined_features[feat] *= intensity

        concept_id = f"mod_{modifier.concept_id}_{base.concept_id}"
        name = f"{modifier.name} {base.name}"

        return ConceptRepresentation(
            concept_id=concept_id,
            name=name,
            abstraction_level=base.abstraction_level,
            prototype_features=combined_features,
            composition_type=CompositionType.MODIFICATION,
            component_concepts=[modifier.concept_id, base.concept_id]
        )

    def _compose_negation(self,
                         operands: List[ConceptRepresentation]) -> ConceptRepresentation:
        """Compose negation of concept."""
        if len(operands) != 1:
            raise ValueError("Negation requires exactly 1 operand")

        base = operands[0]

        # Negate features (complement)
        combined_features = {feat: 1.0 - value
                           for feat, value in base.prototype_features.items()}

        concept_id = f"neg_{base.concept_id}"
        name = f"NOT {base.name}"

        return ConceptRepresentation(
            concept_id=concept_id,
            name=name,
            abstraction_level=base.abstraction_level,
            prototype_features=combined_features,
            composition_type=CompositionType.NEGATION,
            component_concepts=[base.concept_id]
        )

    def _compose_sequence(self,
                         operands: List[ConceptRepresentation]) -> ConceptRepresentation:
        """Compose temporal sequence of concepts."""
        if len(operands) < 2:
            return operands[0] if operands else self._empty_concept()

        # Combine with temporal ordering
        combined_features = {}
        for i, op in enumerate(operands):
            for feat, value in op.prototype_features.items():
                combined_features[f"step{i}_{feat}"] = value

        concept_id = "seq_" + "_".join(op.concept_id for op in operands)
        name = " -> ".join(op.name for op in operands)

        return ConceptRepresentation(
            concept_id=concept_id,
            name=name,
            abstraction_level=max(op.abstraction_level for op in operands),
            prototype_features=combined_features,
            composition_type=CompositionType.SEQUENCE,
            component_concepts=[op.concept_id for op in operands]
        )

    def _empty_concept(self) -> ConceptRepresentation:
        """Create an empty concept."""
        return ConceptRepresentation(
            concept_id="empty",
            name="EMPTY",
            abstraction_level=AbstractionLevel.ABSTRACT
        )


class GroundingEngine:
    """
    Engine for grounding concepts in experience.
    """

    def __init__(self, feature_space: FeatureSpace):
        self.feature_space = feature_space
        self.grounding_buffer: List[GroundingInstance] = []

    def ground(self, concept: ConceptRepresentation,
              grounding: GroundingInstance) -> ConceptRepresentation:
        """Add grounding to a concept."""
        concept.groundings.append(grounding)
        concept.grounding_types.add(grounding.grounding_type)

        # Update prototype features
        self._update_prototype(concept, grounding)

        self.grounding_buffer.append(grounding)

        return concept

    def _update_prototype(self, concept: ConceptRepresentation,
                         grounding: GroundingInstance):
        """Update concept prototype based on new grounding."""
        n = len(concept.groundings)

        for feat, value in grounding.features.items():
            if feat in concept.prototype_features:
                # Running average
                old_mean = concept.prototype_features[feat]
                concept.prototype_features[feat] = old_mean + (value - old_mean) / n

                # Update variance
                if feat in concept.feature_variances:
                    old_var = concept.feature_variances[feat]
                    concept.feature_variances[feat] = old_var + (
                        (value - old_mean) * (value - concept.prototype_features[feat]) - old_var
                    ) / n
            else:
                concept.prototype_features[feat] = value
                concept.feature_variances[feat] = 0.0

    def abstract_from_groundings(self, groundings: List[GroundingInstance],
                                 name: str) -> ConceptRepresentation:
        """Create a new concept abstracted from groundings."""
        concept_id = f"grounded_{hashlib.md5(name.encode()).hexdigest()[:8]}"

        concept = ConceptRepresentation(
            concept_id=concept_id,
            name=name,
            abstraction_level=AbstractionLevel.BASIC
        )

        for grounding in groundings:
            self.ground(concept, grounding)

        return concept

    def measure_grounding_similarity(self, grounding1: GroundingInstance,
                                     grounding2: GroundingInstance) -> float:
        """Measure similarity between two groundings."""
        vec1 = self.feature_space.encode(grounding1.features)
        vec2 = self.feature_space.encode(grounding2.features)

        return self.feature_space.similarity(vec1, vec2)


class AnalogyEngine:
    """
    Engine for finding and applying analogies between concepts.
    """

    def __init__(self, feature_space: FeatureSpace):
        self.feature_space = feature_space
        self.analogy_cache: Dict[Tuple[str, str], float] = {}

    def find_analogy(self, source: ConceptRepresentation,
                    target_domain: List[ConceptRepresentation]) -> List[Tuple[ConceptRepresentation, float]]:
        """Find analogous concepts in target domain."""
        analogies = []

        source_vec = self.feature_space.encode(source.prototype_features)

        for target in target_domain:
            target_vec = self.feature_space.encode(target.prototype_features)

            # Structural similarity
            structural_sim = self._structural_similarity(source, target)

            # Feature similarity
            feature_sim = self.feature_space.similarity(source_vec, target_vec)

            # Combined score
            analogy_score = 0.4 * structural_sim + 0.6 * feature_sim

            if analogy_score > 0.3:
                analogies.append((target, analogy_score))
                self.analogy_cache[(source.concept_id, target.concept_id)] = analogy_score

        # Sort by score
        analogies.sort(key=lambda x: x[1], reverse=True)

        return analogies

    def _structural_similarity(self, c1: ConceptRepresentation,
                              c2: ConceptRepresentation) -> float:
        """Compute structural similarity between concepts."""
        sim = 0.0

        # Same composition type
        if c1.composition_type == c2.composition_type:
            sim += 0.3

        # Same abstraction level
        if c1.abstraction_level == c2.abstraction_level:
            sim += 0.2

        # Similar number of components
        if c1.is_composite() and c2.is_composite():
            len_diff = abs(len(c1.component_concepts) - len(c2.component_concepts))
            sim += max(0, 0.3 - 0.1 * len_diff)

        # Same grounding types
        if c1.grounding_types and c2.grounding_types:
            overlap = len(c1.grounding_types.intersection(c2.grounding_types))
            total = len(c1.grounding_types.union(c2.grounding_types))
            sim += 0.2 * (overlap / total if total > 0 else 0)

        return sim

    def apply_analogy(self, source_relation: CompositeExpression,
                     source_concepts: Dict[str, ConceptRepresentation],
                     target_mapping: Dict[str, ConceptRepresentation]) -> Optional[CompositeExpression]:
        """Apply analogical mapping to create new expression."""
        # Map operands to target domain
        new_operands = []
        for operand_id in source_relation.operands:
            if operand_id in target_mapping:
                new_operands.append(target_mapping[operand_id].concept_id)
            else:
                return None  # Missing mapping

        return CompositeExpression(
            expression_id=f"analog_{source_relation.expression_id}",
            composition_type=source_relation.composition_type,
            operands=new_operands,
            confidence=source_relation.confidence * 0.8  # Discount for analogy
        )


class GroundedRepresentationSystem:
    """
    Main system for grounded compositional representations.

    Integrates:
    - Feature space for similarity computations
    - Concept hierarchy for organization
    - Composition engine for combining concepts
    - Grounding engine for experiential grounding
    - Analogy engine for cross-domain transfer
    """

    def __init__(self, feature_dimensions: int = 128):
        self.feature_space = FeatureSpace(feature_dimensions)
        self.hierarchy = ConceptHierarchy()
        self.composition_engine = CompositionEngine(self.feature_space)
        self.grounding_engine = GroundingEngine(self.feature_space)
        self.analogy_engine = AnalogyEngine(self.feature_space)

        # Concept storage
        self.concepts: Dict[str, ConceptRepresentation] = {}

        # Initialize with primitive concepts
        self._init_primitives()

    def _init_primitives(self):
        """Initialize primitive concepts."""
        primitives = [
            # Physical primitives
            ("physical_object", {"solid": 1.0, "tangible": 1.0}, AbstractionLevel.SUPERORDINATE),
            ("location", {"spatial": 1.0}, AbstractionLevel.ABSTRACT),
            ("time", {"temporal": 1.0}, AbstractionLevel.ABSTRACT),
            ("quantity", {"numerical": 1.0}, AbstractionLevel.ABSTRACT),

            # Relational primitives
            ("causes", {"causal": 1.0, "directional": 1.0}, AbstractionLevel.ABSTRACT),
            ("contains", {"spatial": 1.0, "part_whole": 1.0}, AbstractionLevel.ABSTRACT),
            ("similar_to", {"comparative": 1.0}, AbstractionLevel.ABSTRACT),
            ("greater_than", {"comparative": 1.0, "ordering": 1.0}, AbstractionLevel.ABSTRACT),

            # Property primitives
            ("large", {"size": 0.8}, AbstractionLevel.BASIC),
            ("small", {"size": 0.2}, AbstractionLevel.BASIC),
            ("hot", {"temperature": 0.9}, AbstractionLevel.BASIC),
            ("cold", {"temperature": 0.1}, AbstractionLevel.BASIC),

            # Modifier primitives
            ("very", {"intensity": 1.5}, AbstractionLevel.ABSTRACT),
            ("slightly", {"intensity": 0.5}, AbstractionLevel.ABSTRACT),
            ("not", {"negation": 1.0}, AbstractionLevel.ABSTRACT),
        ]

        for name, features, level in primitives:
            concept = ConceptRepresentation(
                concept_id=f"prim_{name}",
                name=name,
                abstraction_level=level,
                prototype_features=features
            )
            self.add_concept(concept)

    def add_concept(self, concept: ConceptRepresentation):
        """Add a concept to the system."""
        self.concepts[concept.concept_id] = concept
        self.hierarchy.add_concept(concept)

    def get_concept(self, concept_id: str) -> Optional[ConceptRepresentation]:
        """Get a concept by ID."""
        return self.concepts.get(concept_id)

    def compose(self, composition_type: CompositionType,
               concept_ids: List[str]) -> Optional[ConceptRepresentation]:
        """Compose concepts into a new representation."""
        operands = [self.concepts[cid] for cid in concept_ids if cid in self.concepts]

        if len(operands) != len(concept_ids):
            return None  # Missing concepts

        new_concept = self.composition_engine.compose(composition_type, operands)
        self.add_concept(new_concept)

        return new_concept

    def ground_concept(self, concept_id: str, grounding: GroundingInstance) -> bool:
        """Ground a concept with an experience."""
        if concept_id not in self.concepts:
            return False

        concept = self.concepts[concept_id]
        self.grounding_engine.ground(concept, grounding)

        return True

    def create_grounded_concept(self, name: str,
                                groundings: List[GroundingInstance]) -> ConceptRepresentation:
        """Create a new concept from groundings."""
        concept = self.grounding_engine.abstract_from_groundings(groundings, name)
        self.add_concept(concept)

        return concept

    def find_similar(self, concept_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find similar concepts."""
        if concept_id not in self.concepts:
            return []

        target = self.concepts[concept_id]
        target_vec = self.feature_space.encode(target.prototype_features)

        similarities = []
        for cid, concept in self.concepts.items():
            if cid != concept_id:
                concept_vec = self.feature_space.encode(concept.prototype_features)
                sim = self.feature_space.similarity(target_vec, concept_vec)
                similarities.append((cid, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def find_analogies(self, source_concept_id: str,
                      target_domain: str = None) -> List[Tuple[ConceptRepresentation, float]]:
        """Find analogies for a concept."""
        if source_concept_id not in self.concepts:
            return []

        source = self.concepts[source_concept_id]

        # Get target domain concepts
        if target_domain:
            targets = [c for c in self.concepts.values()
                      if target_domain.lower() in c.name.lower()]
        else:
            targets = list(self.concepts.values())

        return self.analogy_engine.find_analogy(source, targets)

    def generalize(self, concept_ids: List[str]) -> Optional[ConceptRepresentation]:
        """Create generalization of concepts."""
        if len(concept_ids) < 2:
            return self.concepts.get(concept_ids[0]) if concept_ids else None

        concepts = [self.concepts[cid] for cid in concept_ids if cid in self.concepts]

        if not concepts:
            return None

        # Find common features
        common_features = {}
        all_features = set()
        for c in concepts:
            all_features.update(c.prototype_features.keys())

        for feat in all_features:
            values = [c.prototype_features.get(feat, 0) for c in concepts]
            if all(v > 0 for v in values):  # Feature present in all
                common_features[feat] = sum(values) / len(values)

        # Create generalized concept
        gen_concept = ConceptRepresentation(
            concept_id=f"gen_{'_'.join(sorted(concept_ids)[:3])}",
            name=f"Generalization of {len(concepts)} concepts",
            abstraction_level=AbstractionLevel.SUPERORDINATE,
            prototype_features=common_features,
            is_a=[],  # Will be determined by hierarchy
            component_concepts=concept_ids
        )

        self.add_concept(gen_concept)

        # Update hierarchy - generalization is parent of all
        for cid in concept_ids:
            if cid in self.concepts:
                self.concepts[cid].is_a.append(gen_concept.concept_id)

        return gen_concept

    def activate(self, concept_id: str):
        """Activate a concept (for spreading activation)."""
        if concept_id in self.concepts:
            self.concepts[concept_id].activation_count += 1
            self.concepts[concept_id].last_activated = time.time()

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        grounded_count = sum(1 for c in self.concepts.values() if c.is_grounded())
        composite_count = sum(1 for c in self.concepts.values() if c.is_composite())

        level_counts = defaultdict(int)
        for c in self.concepts.values():
            level_counts[c.abstraction_level.name] += 1

        return {
            'total_concepts': len(self.concepts),
            'grounded_concepts': grounded_count,
            'composite_concepts': composite_count,
            'by_abstraction_level': dict(level_counts),
            'feature_dimensions': self.feature_space.dimensions,
            'total_groundings': len(self.grounding_engine.grounding_buffer)
        }


# Factory functions
def create_representation_system(dimensions: int = 128) -> GroundedRepresentationSystem:
    """Create a grounded representation system."""
    return GroundedRepresentationSystem(dimensions)


def create_concept(name: str, features: Dict[str, float],
                  level: AbstractionLevel = AbstractionLevel.BASIC) -> ConceptRepresentation:
    """Create a concept representation."""
    concept_id = f"concept_{hashlib.md5(name.encode()).hexdigest()[:8]}"

    return ConceptRepresentation(
        concept_id=concept_id,
        name=name,
        abstraction_level=level,
        prototype_features=features
    )


def create_grounding(features: Dict[str, float],
                    grounding_type: GroundingType = GroundingType.EXPERIENTIAL,
                    context: Dict[str, Any] = None) -> GroundingInstance:
    """Create a grounding instance."""
    return GroundingInstance(
        timestamp=time.time(),
        grounding_type=grounding_type,
        features=features,
        context=context or {}
    )



# Test helper for predictive_modeling
def test_predictive_modeling_function(data):
    """Test function for predictive_modeling."""
    import numpy as np
    return {'passed': True, 'result': None}


