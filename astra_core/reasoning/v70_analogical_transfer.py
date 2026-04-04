"""
V70 Deep Analogical Transfer Engine

A framework for finding deep structural analogies between domains, enabling
transfer of solutions and knowledge across seemingly unrelated fields through
relational mapping and structure-preserving transformations.

This module enables STAN to:
1. Find structural analogies between domains
2. Transfer solutions across problem spaces
3. Learn relational mappings between concepts
4. Perform analogical inference and reasoning
5. Generate novel insights through cross-domain transfer
6. Build abstraction hierarchies for analogical retrieval
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from enum import Enum, auto
from abc import ABC, abstractmethod
import logging
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# Enumerations
# =============================================================================

class AnalogicalRelationType(Enum):
    """Types of analogical relationships"""
    STRUCTURAL = auto()      # Same relational structure
    FUNCTIONAL = auto()      # Same function/purpose
    CAUSAL = auto()          # Same causal structure
    PROPORTIONAL = auto()    # A:B :: C:D relationships
    METAPHORICAL = auto()    # Abstract mapping
    ISOMORPHIC = auto()      # Perfect structural match


class MappingType(Enum):
    """Types of concept mappings"""
    ONE_TO_ONE = auto()      # Bijective mapping
    MANY_TO_ONE = auto()     # Abstraction
    ONE_TO_MANY = auto()     # Specialization
    PARTIAL = auto()         # Incomplete mapping


class DomainType(Enum):
    """Types of knowledge domains"""
    PHYSICAL = auto()        # Physical systems
    MATHEMATICAL = auto()    # Mathematical structures
    BIOLOGICAL = auto()      # Biological systems
    SOCIAL = auto()          # Social systems
    COMPUTATIONAL = auto()   # Computational systems
    ECONOMIC = auto()        # Economic systems
    ABSTRACT = auto()        # Abstract domains


class TransferStrategy(Enum):
    """Strategies for knowledge transfer"""
    DIRECT = auto()          # Direct mapping
    ADAPTED = auto()         # With modifications
    COMPOSITIONAL = auto()   # Combine multiple analogies
    GENERALIZED = auto()     # Through abstraction


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Concept:
    """A concept in a domain"""
    id: str
    name: str
    domain: DomainType
    attributes: Dict[str, Any] = field(default_factory=dict)
    relations: List[str] = field(default_factory=list)
    abstraction_level: int = 0
    embedding: Optional[np.ndarray] = None


@dataclass
class Relation:
    """A relation between concepts"""
    id: str
    name: str
    source: str  # Concept ID
    target: str  # Concept ID
    relation_type: str
    strength: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainStructure:
    """Structural representation of a domain"""
    id: str
    domain_type: DomainType
    concepts: Dict[str, Concept] = field(default_factory=dict)
    relations: Dict[str, Relation] = field(default_factory=dict)
    hierarchies: Dict[str, List[str]] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)


@dataclass
class AnalogicalMapping:
    """A mapping between two domains"""
    id: str
    source_domain: str
    target_domain: str
    mapping_type: MappingType
    relation_type: AnalogicalRelationType
    concept_mappings: Dict[str, str] = field(default_factory=dict)  # source -> target
    relation_mappings: Dict[str, str] = field(default_factory=dict)
    similarity_score: float = 0.0
    systematicity: float = 0.0  # How systematic/consistent the mapping is
    confidence: float = 0.0


@dataclass
class AnalogicalInference:
    """An inference made through analogy"""
    id: str
    source_fact: str
    inferred_fact: str
    mapping_used: str
    confidence: float = 0.0
    justification: List[str] = field(default_factory=list)
    validation_status: str = "unvalidated"


@dataclass
class AbstractPattern:
    """An abstract pattern that spans domains"""
    id: str
    name: str
    description: str
    structure: Dict[str, Any] = field(default_factory=dict)
    instances: List[Tuple[str, str]] = field(default_factory=list)  # (domain_id, mapping)
    abstraction_level: int = 0
    generality_score: float = 0.0


# =============================================================================
# Domain Modeler
# =============================================================================

class DomainModeler:
    """Models domain structure for analogical reasoning"""

    def __init__(self):
        self.domains: Dict[str, DomainStructure] = {}
        self.concept_embeddings: Dict[str, np.ndarray] = {}

    def create_domain(
        self,
        name: str,
        domain_type: DomainType,
        concepts: Optional[List[Dict[str, Any]]] = None,
        relations: Optional[List[Dict[str, Any]]] = None
    ) -> DomainStructure:
        """Create a new domain structure"""
        domain_id = f"domain_{name}_{len(self.domains)}"

        domain = DomainStructure(
            id=domain_id,
            domain_type=domain_type
        )

        if concepts:
            for c_dict in concepts:
                concept = Concept(
                    id=f"{domain_id}_{c_dict['name']}",
                    name=c_dict['name'],
                    domain=domain_type,
                    attributes=c_dict.get('attributes', {}),
                    abstraction_level=c_dict.get('level', 0)
                )
                domain.concepts[concept.id] = concept
                self._compute_concept_embedding(concept)

        if relations:
            for r_dict in relations:
                source_id = f"{domain_id}_{r_dict['source']}"
                target_id = f"{domain_id}_{r_dict['target']}"
                relation = Relation(
                    id=f"rel_{source_id}_{target_id}",
                    name=r_dict.get('name', 'relates_to'),
                    source=source_id,
                    target=target_id,
                    relation_type=r_dict.get('type', 'generic'),
                    strength=r_dict.get('strength', 1.0)
                )
                domain.relations[relation.id] = relation

                # Update concept relations
                if source_id in domain.concepts:
                    domain.concepts[source_id].relations.append(relation.id)

        self.domains[domain_id] = domain
        return domain

    def _compute_concept_embedding(self, concept: Concept, dim: int = 64):
        """Compute embedding for a concept"""
        # Create embedding from attributes
        embedding = np.zeros(dim)

        # Hash-based embedding from name
        name_hash = hashlib.md5(concept.name.encode()).digest()
        for i, b in enumerate(name_hash[:dim // 4]):
            embedding[i] = (b - 128) / 128.0

        # Attribute-based features
        attr_idx = dim // 4
        for key, value in concept.attributes.items():
            key_hash = hash(key) % (dim // 2)
            if isinstance(value, (int, float)):
                embedding[attr_idx + key_hash % (dim // 4)] = float(value) / (abs(float(value)) + 1)
            elif isinstance(value, bool):
                embedding[attr_idx + key_hash % (dim // 4)] = 1.0 if value else -1.0
            elif isinstance(value, str):
                str_hash = hash(value) % 256
                embedding[attr_idx + key_hash % (dim // 4)] = (str_hash - 128) / 128.0

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        concept.embedding = embedding
        self.concept_embeddings[concept.id] = embedding

    def get_domain_graph(self, domain_id: str) -> Dict[str, Any]:
        """Get graph representation of domain"""
        if domain_id not in self.domains:
            return {}

        domain = self.domains[domain_id]

        nodes = [
            {'id': c.id, 'name': c.name, 'level': c.abstraction_level}
            for c in domain.concepts.values()
        ]

        edges = [
            {'source': r.source, 'target': r.target, 'type': r.relation_type}
            for r in domain.relations.values()
        ]

        return {'nodes': nodes, 'edges': edges}

    def compute_structural_signature(self, domain_id: str) -> np.ndarray:
        """Compute structural signature for domain comparison"""
        if domain_id not in self.domains:
            return np.zeros(32)

        domain = self.domains[domain_id]

        signature = np.zeros(32)

        # Number of concepts
        signature[0] = len(domain.concepts) / 100.0

        # Number of relations
        signature[1] = len(domain.relations) / 100.0

        # Relation density
        max_relations = len(domain.concepts) * (len(domain.concepts) - 1)
        signature[2] = len(domain.relations) / max_relations if max_relations > 0 else 0

        # Degree distribution features
        degrees = defaultdict(int)
        for rel in domain.relations.values():
            degrees[rel.source] += 1
            degrees[rel.target] += 1

        if degrees:
            degree_values = list(degrees.values())
            signature[3] = np.mean(degree_values) / 10.0
            signature[4] = np.std(degree_values) / 10.0
            signature[5] = np.max(degree_values) / 20.0

        # Abstraction level distribution
        levels = [c.abstraction_level for c in domain.concepts.values()]
        if levels:
            signature[6] = np.mean(levels) / 5.0
            signature[7] = np.max(levels) / 5.0

        # Relation type diversity
        rel_types = set(r.relation_type for r in domain.relations.values())
        signature[8] = len(rel_types) / 10.0

        return signature


# =============================================================================
# Structural Aligner
# =============================================================================

class StructuralAligner:
    """Finds structural alignments between domains"""

    def __init__(self, domain_modeler: DomainModeler):
        self.domain_modeler = domain_modeler
        self.alignment_cache: Dict[Tuple[str, str], AnalogicalMapping] = {}

    def find_alignment(
        self,
        source_domain_id: str,
        target_domain_id: str,
        strategy: str = 'structural'
    ) -> AnalogicalMapping:
        """Find best alignment between domains"""
        cache_key = (source_domain_id, target_domain_id)
        if cache_key in self.alignment_cache:
            return self.alignment_cache[cache_key]

        source = self.domain_modeler.domains.get(source_domain_id)
        target = self.domain_modeler.domains.get(target_domain_id)

        if not source or not target:
            raise ValueError("Domain not found")

        if strategy == 'structural':
            mapping = self._align_structural(source, target)
        elif strategy == 'embedding':
            mapping = self._align_embedding(source, target)
        elif strategy == 'relational':
            mapping = self._align_relational(source, target)
        else:
            mapping = self._align_structural(source, target)

        self.alignment_cache[cache_key] = mapping
        return mapping

    def _align_structural(
        self,
        source: DomainStructure,
        target: DomainStructure
    ) -> AnalogicalMapping:
        """Structure Mapping Engine-inspired alignment"""
        mapping = AnalogicalMapping(
            id=f"map_{source.id}_{target.id}",
            source_domain=source.id,
            target_domain=target.id,
            mapping_type=MappingType.PARTIAL,
            relation_type=AnalogicalRelationType.STRUCTURAL
        )

        # Build relation structures
        source_rel_structure = self._build_relation_structure(source)
        target_rel_structure = self._build_relation_structure(target)

        # Find matching relations (same relation type)
        relation_matches = []
        for s_rel_id, s_rel in source.relations.items():
            for t_rel_id, t_rel in target.relations.items():
                if s_rel.relation_type == t_rel.relation_type:
                    relation_matches.append((s_rel_id, t_rel_id, 1.0))
                elif self._relation_similarity(s_rel, t_rel) > 0.5:
                    sim = self._relation_similarity(s_rel, t_rel)
                    relation_matches.append((s_rel_id, t_rel_id, sim))

        # Propagate matches to concepts (consistent mapping constraint)
        concept_scores: Dict[Tuple[str, str], float] = defaultdict(float)

        for s_rel_id, t_rel_id, score in relation_matches:
            s_rel = source.relations[s_rel_id]
            t_rel = target.relations[t_rel_id]

            # Source of relation maps to source
            concept_scores[(s_rel.source, t_rel.source)] += score
            # Target of relation maps to target
            concept_scores[(s_rel.target, t_rel.target)] += score

            mapping.relation_mappings[s_rel_id] = t_rel_id

        # Build consistent concept mapping (greedy)
        used_targets = set()
        for (s_concept, t_concept), score in sorted(
            concept_scores.items(), key=lambda x: -x[1]
        ):
            if s_concept not in mapping.concept_mappings and t_concept not in used_targets:
                mapping.concept_mappings[s_concept] = t_concept
                used_targets.add(t_concept)

        # Calculate scores
        mapping.similarity_score = self._calculate_similarity(mapping, source, target)
        mapping.systematicity = self._calculate_systematicity(mapping, source, target)
        mapping.confidence = (mapping.similarity_score + mapping.systematicity) / 2

        return mapping

    def _align_embedding(
        self,
        source: DomainStructure,
        target: DomainStructure
    ) -> AnalogicalMapping:
        """Embedding-based alignment"""
        mapping = AnalogicalMapping(
            id=f"map_emb_{source.id}_{target.id}",
            source_domain=source.id,
            target_domain=target.id,
            mapping_type=MappingType.ONE_TO_ONE,
            relation_type=AnalogicalRelationType.STRUCTURAL
        )

        # Compute concept similarity matrix
        source_concepts = list(source.concepts.values())
        target_concepts = list(target.concepts.values())

        if not source_concepts or not target_concepts:
            return mapping

        sim_matrix = np.zeros((len(source_concepts), len(target_concepts)))

        for i, s_concept in enumerate(source_concepts):
            for j, t_concept in enumerate(target_concepts):
                if s_concept.embedding is not None and t_concept.embedding is not None:
                    sim = np.dot(s_concept.embedding, t_concept.embedding)
                    sim_matrix[i, j] = sim

        # Greedy assignment (could use Hungarian algorithm for optimal)
        used_targets = set()
        for i in np.argsort(-sim_matrix.max(axis=1)):
            best_j = -1
            best_sim = -float('inf')
            for j in range(len(target_concepts)):
                if j not in used_targets and sim_matrix[i, j] > best_sim:
                    best_sim = sim_matrix[i, j]
                    best_j = j

            if best_j >= 0:
                mapping.concept_mappings[source_concepts[i].id] = target_concepts[best_j].id
                used_targets.add(best_j)

        mapping.similarity_score = np.mean([
            sim_matrix[i, list(target_concepts).index(
                target.concepts[mapping.concept_mappings[s.id]]
            )]
            for i, s in enumerate(source_concepts)
            if s.id in mapping.concept_mappings
        ]) if mapping.concept_mappings else 0

        return mapping

    def _align_relational(
        self,
        source: DomainStructure,
        target: DomainStructure
    ) -> AnalogicalMapping:
        """Relational alignment focusing on higher-order relations"""
        # First get structural alignment
        base_mapping = self._align_structural(source, target)

        # Enhance with higher-order pattern matching
        mapping = AnalogicalMapping(
            id=f"map_rel_{source.id}_{target.id}",
            source_domain=source.id,
            target_domain=target.id,
            mapping_type=base_mapping.mapping_type,
            relation_type=AnalogicalRelationType.STRUCTURAL,
            concept_mappings=base_mapping.concept_mappings.copy(),
            relation_mappings=base_mapping.relation_mappings.copy()
        )

        # Look for relation chains (A->B->C patterns)
        source_chains = self._find_relation_chains(source)
        target_chains = self._find_relation_chains(target)

        chain_matches = 0
        for s_chain in source_chains:
            for t_chain in target_chains:
                if self._chains_match(s_chain, t_chain, mapping):
                    chain_matches += 1

        # Boost systematicity for chain matches
        mapping.systematicity = base_mapping.systematicity
        if source_chains and target_chains:
            mapping.systematicity += 0.2 * chain_matches / max(len(source_chains), len(target_chains))

        mapping.similarity_score = base_mapping.similarity_score
        mapping.confidence = (mapping.similarity_score + mapping.systematicity) / 2

        return mapping

    def _build_relation_structure(self, domain: DomainStructure) -> Dict[str, Set[str]]:
        """Build relation structure for matching"""
        structure = defaultdict(set)
        for rel in domain.relations.values():
            structure[rel.relation_type].add(rel.id)
        return structure

    def _relation_similarity(self, r1: Relation, r2: Relation) -> float:
        """Compute similarity between relations"""
        # Type match
        type_sim = 1.0 if r1.relation_type == r2.relation_type else 0.3

        # Name similarity (simple)
        name_sim = 0.0
        if r1.name == r2.name:
            name_sim = 1.0
        elif r1.name in r2.name or r2.name in r1.name:
            name_sim = 0.5

        return 0.7 * type_sim + 0.3 * name_sim

    def _find_relation_chains(
        self,
        domain: DomainStructure,
        max_length: int = 3
    ) -> List[List[str]]:
        """Find relation chains in domain"""
        chains = []

        # Build adjacency from relations
        adj = defaultdict(list)
        for rel in domain.relations.values():
            adj[rel.source].append((rel.target, rel.id))

        # DFS to find chains
        def dfs(node: str, chain: List[str], visited: Set[str]):
            if len(chain) >= max_length:
                chains.append(chain.copy())
                return

            for next_node, rel_id in adj[node]:
                if next_node not in visited:
                    visited.add(next_node)
                    chain.append(rel_id)
                    dfs(next_node, chain, visited)
                    chain.pop()
                    visited.remove(next_node)

        for start in domain.concepts:
            dfs(start, [], {start})

        return chains

    def _chains_match(
        self,
        s_chain: List[str],
        t_chain: List[str],
        mapping: AnalogicalMapping
    ) -> bool:
        """Check if two relation chains match under mapping"""
        if len(s_chain) != len(t_chain):
            return False

        for s_rel, t_rel in zip(s_chain, t_chain):
            if mapping.relation_mappings.get(s_rel) != t_rel:
                return False

        return True

    def _calculate_similarity(
        self,
        mapping: AnalogicalMapping,
        source: DomainStructure,
        target: DomainStructure
    ) -> float:
        """Calculate overall similarity score"""
        if not mapping.concept_mappings:
            return 0.0

        # Coverage
        coverage = len(mapping.concept_mappings) / len(source.concepts)

        # Embedding similarity for mapped concepts
        emb_sims = []
        for s_id, t_id in mapping.concept_mappings.items():
            s_emb = self.domain_modeler.concept_embeddings.get(s_id)
            t_emb = self.domain_modeler.concept_embeddings.get(t_id)
            if s_emb is not None and t_emb is not None:
                emb_sims.append(np.dot(s_emb, t_emb))

        emb_sim = np.mean(emb_sims) if emb_sims else 0.5

        return 0.4 * coverage + 0.6 * emb_sim

    def _calculate_systematicity(
        self,
        mapping: AnalogicalMapping,
        source: DomainStructure,
        target: DomainStructure
    ) -> float:
        """Calculate systematicity (consistency of relational structure)"""
        if not mapping.relation_mappings:
            return 0.0

        # Check if mapped relations are consistent with concept mappings
        consistent = 0
        total = len(mapping.relation_mappings)

        for s_rel_id, t_rel_id in mapping.relation_mappings.items():
            s_rel = source.relations.get(s_rel_id)
            t_rel = target.relations.get(t_rel_id)

            if s_rel and t_rel:
                # Check if source concept mapping is consistent
                s_source_maps_to = mapping.concept_mappings.get(s_rel.source)
                s_target_maps_to = mapping.concept_mappings.get(s_rel.target)

                if s_source_maps_to == t_rel.source and s_target_maps_to == t_rel.target:
                    consistent += 1

        return consistent / total if total > 0 else 0.0


# =============================================================================
# Analogical Reasoner
# =============================================================================

class AnalogicalReasoner:
    """Performs reasoning and inference through analogy"""

    def __init__(self, domain_modeler: DomainModeler, structural_aligner: StructuralAligner):
        self.domain_modeler = domain_modeler
        self.structural_aligner = structural_aligner
        self.inferences: Dict[str, AnalogicalInference] = {}

    def make_inference(
        self,
        source_domain_id: str,
        target_domain_id: str,
        source_fact: str,
        mapping: Optional[AnalogicalMapping] = None
    ) -> AnalogicalInference:
        """Make inference in target domain based on source fact"""
        if mapping is None:
            mapping = self.structural_aligner.find_alignment(
                source_domain_id, target_domain_id
            )

        # Parse source fact and map to target
        inferred = self._transfer_fact(source_fact, mapping)

        inference = AnalogicalInference(
            id=f"inf_{len(self.inferences)}",
            source_fact=source_fact,
            inferred_fact=inferred,
            mapping_used=mapping.id,
            confidence=mapping.confidence,
            justification=self._generate_justification(source_fact, inferred, mapping)
        )

        self.inferences[inference.id] = inference
        return inference

    def _transfer_fact(self, source_fact: str, mapping: AnalogicalMapping) -> str:
        """Transfer a fact from source to target domain"""
        target_fact = source_fact

        # Replace concept references
        for s_concept, t_concept in mapping.concept_mappings.items():
            # Extract concept name from ID
            s_name = s_concept.split('_')[-1]
            t_name = t_concept.split('_')[-1]
            target_fact = target_fact.replace(s_name, t_name)

        return target_fact

    def _generate_justification(
        self,
        source_fact: str,
        target_fact: str,
        mapping: AnalogicalMapping
    ) -> List[str]:
        """Generate justification for inference"""
        justification = [
            f"Source domain: {mapping.source_domain}",
            f"Target domain: {mapping.target_domain}",
            f"Mapping type: {mapping.relation_type.name}",
            f"Mapping confidence: {mapping.confidence:.2f}",
            f"Systematicity: {mapping.systematicity:.2f}",
            f"Source fact: {source_fact}",
            f"Inferred fact: {target_fact}",
            f"Number of concept mappings: {len(mapping.concept_mappings)}",
            f"Number of relation mappings: {len(mapping.relation_mappings)}"
        ]
        return justification

    def solve_proportional_analogy(
        self,
        a: str,
        b: str,
        c: str,
        domain_id: str
    ) -> Tuple[str, float]:
        """Solve A:B :: C:? proportional analogy"""
        domain = self.domain_modeler.domains.get(domain_id)
        if not domain:
            return "", 0.0

        # Find relation between A and B
        a_concept = None
        b_concept = None
        c_concept = None

        for concept in domain.concepts.values():
            if concept.name.lower() == a.lower():
                a_concept = concept
            elif concept.name.lower() == b.lower():
                b_concept = concept
            elif concept.name.lower() == c.lower():
                c_concept = concept

        if not (a_concept and b_concept and c_concept):
            return "", 0.0

        # Find relation A->B
        ab_relation = None
        for rel in domain.relations.values():
            if rel.source == a_concept.id and rel.target == b_concept.id:
                ab_relation = rel
                break

        if not ab_relation:
            # Try embedding-based relation inference
            if a_concept.embedding is not None and b_concept.embedding is not None:
                relation_vector = b_concept.embedding - a_concept.embedding

                # Apply relation to C
                if c_concept.embedding is not None:
                    d_embedding = c_concept.embedding + relation_vector

                    # Find closest concept
                    best_match = None
                    best_sim = -float('inf')
                    for concept in domain.concepts.values():
                        if concept.id != c_concept.id and concept.embedding is not None:
                            sim = np.dot(concept.embedding, d_embedding)
                            if sim > best_sim:
                                best_sim = sim
                                best_match = concept.name

                    return best_match or "", (best_sim + 1) / 2

            return "", 0.0

        # Find concept D such that C->D has same relation type
        candidates = []
        for rel in domain.relations.values():
            if rel.source == c_concept.id and rel.relation_type == ab_relation.relation_type:
                d_concept = domain.concepts.get(rel.target)
                if d_concept:
                    candidates.append((d_concept.name, rel.strength))

        if candidates:
            # Return highest strength match
            candidates.sort(key=lambda x: -x[1])
            return candidates[0][0], candidates[0][1]

        return "", 0.0

    def find_analogies_for_concept(
        self,
        concept_id: str,
        target_domain_id: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find analogous concepts in target domain"""
        source_emb = self.domain_modeler.concept_embeddings.get(concept_id)
        if source_emb is None:
            return []

        target_domain = self.domain_modeler.domains.get(target_domain_id)
        if not target_domain:
            return []

        similarities = []
        for t_concept in target_domain.concepts.values():
            if t_concept.embedding is not None:
                sim = np.dot(source_emb, t_concept.embedding)
                similarities.append((t_concept.name, sim))

        similarities.sort(key=lambda x: -x[1])
        return similarities[:top_k]


# =============================================================================
# Transfer Engine
# =============================================================================

class TransferEngine:
    """Transfers solutions and knowledge across domains"""

    def __init__(
        self,
        domain_modeler: DomainModeler,
        structural_aligner: StructuralAligner,
        analogical_reasoner: AnalogicalReasoner
    ):
        self.domain_modeler = domain_modeler
        self.structural_aligner = structural_aligner
        self.analogical_reasoner = analogical_reasoner
        self.transfer_history: List[Dict[str, Any]] = []

    def transfer_solution(
        self,
        source_domain_id: str,
        target_domain_id: str,
        source_solution: Dict[str, Any],
        strategy: TransferStrategy = TransferStrategy.ADAPTED
    ) -> Dict[str, Any]:
        """Transfer a solution from source to target domain"""
        # Get mapping
        mapping = self.structural_aligner.find_alignment(
            source_domain_id, target_domain_id
        )

        if strategy == TransferStrategy.DIRECT:
            transferred = self._direct_transfer(source_solution, mapping)
        elif strategy == TransferStrategy.ADAPTED:
            transferred = self._adapted_transfer(source_solution, mapping)
        elif strategy == TransferStrategy.GENERALIZED:
            transferred = self._generalized_transfer(source_solution, mapping)
        else:
            transferred = self._direct_transfer(source_solution, mapping)

        # Record transfer
        transfer_record = {
            'source_domain': source_domain_id,
            'target_domain': target_domain_id,
            'strategy': strategy.name,
            'mapping_confidence': mapping.confidence,
            'source_solution': source_solution,
            'transferred_solution': transferred
        }
        self.transfer_history.append(transfer_record)

        return transferred

    def _direct_transfer(
        self,
        source_solution: Dict[str, Any],
        mapping: AnalogicalMapping
    ) -> Dict[str, Any]:
        """Direct transfer using concept mappings"""
        transferred = {}

        for key, value in source_solution.items():
            # Map key if it's a concept reference
            new_key = key
            for s_concept, t_concept in mapping.concept_mappings.items():
                s_name = s_concept.split('_')[-1]
                t_name = t_concept.split('_')[-1]
                if s_name in key:
                    new_key = key.replace(s_name, t_name)

            # Map value if it's a concept reference or string
            if isinstance(value, str):
                new_value = value
                for s_concept, t_concept in mapping.concept_mappings.items():
                    s_name = s_concept.split('_')[-1]
                    t_name = t_concept.split('_')[-1]
                    new_value = new_value.replace(s_name, t_name)
                transferred[new_key] = new_value
            elif isinstance(value, dict):
                transferred[new_key] = self._direct_transfer(value, mapping)
            else:
                transferred[new_key] = value

        return transferred

    def _adapted_transfer(
        self,
        source_solution: Dict[str, Any],
        mapping: AnalogicalMapping
    ) -> Dict[str, Any]:
        """Transfer with adaptation based on target domain characteristics"""
        # Start with direct transfer
        transferred = self._direct_transfer(source_solution, mapping)

        # Add adaptation metadata
        transferred['_adaptation'] = {
            'mapping_confidence': mapping.confidence,
            'systematicity': mapping.systematicity,
            'unmapped_concepts': [
                k for k in source_solution
                if not any(s.split('_')[-1] in k for s in mapping.concept_mappings)
            ],
            'requires_validation': mapping.confidence < 0.7
        }

        return transferred

    def _generalized_transfer(
        self,
        source_solution: Dict[str, Any],
        mapping: AnalogicalMapping
    ) -> Dict[str, Any]:
        """Transfer through abstraction and re-specialization"""
        # Abstract the solution
        abstract_solution = self._abstract_solution(source_solution)

        # Re-specialize for target
        transferred = self._specialize_solution(abstract_solution, mapping)

        return transferred

    def _abstract_solution(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Abstract a solution to domain-independent form"""
        abstract = {}
        for key, value in solution.items():
            # Replace specific concept names with generic placeholders
            abstract_key = f"element_{len(abstract)}"
            if isinstance(value, dict):
                abstract[abstract_key] = self._abstract_solution(value)
            else:
                abstract[abstract_key] = {
                    'original_key': key,
                    'value': value,
                    'type': type(value).__name__
                }
        return abstract

    def _specialize_solution(
        self,
        abstract_solution: Dict[str, Any],
        mapping: AnalogicalMapping
    ) -> Dict[str, Any]:
        """Specialize abstract solution for target domain"""
        specialized = {}

        for key, value in abstract_solution.items():
            if isinstance(value, dict) and 'original_key' in value:
                # Map original key to target domain
                original_key = value['original_key']
                new_key = original_key
                for s_concept, t_concept in mapping.concept_mappings.items():
                    s_name = s_concept.split('_')[-1]
                    t_name = t_concept.split('_')[-1]
                    new_key = new_key.replace(s_name, t_name)
                specialized[new_key] = value['value']
            elif isinstance(value, dict):
                specialized[key] = self._specialize_solution(value, mapping)
            else:
                specialized[key] = value

        return specialized

    def evaluate_transfer_quality(
        self,
        source_solution: Dict[str, Any],
        transferred_solution: Dict[str, Any],
        mapping: AnalogicalMapping
    ) -> Dict[str, float]:
        """Evaluate quality of solution transfer"""
        quality = {}

        # Coverage: how much of source was transferred
        source_keys = set(self._flatten_keys(source_solution))
        transferred_keys = set(self._flatten_keys(transferred_solution))
        quality['coverage'] = len(transferred_keys) / len(source_keys) if source_keys else 0

        # Confidence from mapping
        quality['mapping_confidence'] = mapping.confidence

        # Systematicity
        quality['systematicity'] = mapping.systematicity

        # Overall quality
        quality['overall'] = (
            0.4 * quality['coverage'] +
            0.3 * quality['mapping_confidence'] +
            0.3 * quality['systematicity']
        )

        return quality

    def _flatten_keys(self, d: Dict, prefix: str = '') -> List[str]:
        """Flatten dictionary keys"""
        keys = []
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.append(full_key)
            if isinstance(v, dict):
                keys.extend(self._flatten_keys(v, full_key))
        return keys


# =============================================================================
# Abstract Pattern Library
# =============================================================================

class AbstractPatternLibrary:
    """Library of abstract patterns spanning multiple domains"""

    def __init__(self):
        self.patterns: Dict[str, AbstractPattern] = {}
        self._init_common_patterns()

    def _init_common_patterns(self):
        """Initialize common abstract patterns"""
        patterns = [
            AbstractPattern(
                id="feedback_loop",
                name="Feedback Loop",
                description="Output affects input, creating circular causation",
                structure={
                    'nodes': ['input', 'process', 'output', 'feedback'],
                    'edges': [
                        ('input', 'process'),
                        ('process', 'output'),
                        ('output', 'feedback'),
                        ('feedback', 'input')
                    ]
                },
                abstraction_level=2,
                generality_score=0.9
            ),
            AbstractPattern(
                id="hierarchy",
                name="Hierarchical Structure",
                description="Elements organized in levels with control/containment",
                structure={
                    'nodes': ['top', 'middle', 'bottom'],
                    'edges': [
                        ('top', 'middle', 'contains'),
                        ('middle', 'bottom', 'contains')
                    ]
                },
                abstraction_level=2,
                generality_score=0.85
            ),
            AbstractPattern(
                id="competition",
                name="Competition for Resources",
                description="Multiple agents competing for limited resources",
                structure={
                    'nodes': ['agent_1', 'agent_2', 'resource'],
                    'edges': [
                        ('agent_1', 'resource', 'competes_for'),
                        ('agent_2', 'resource', 'competes_for'),
                        ('agent_1', 'agent_2', 'competes_with')
                    ]
                },
                abstraction_level=2,
                generality_score=0.8
            ),
            AbstractPattern(
                id="flow",
                name="Flow Network",
                description="Movement of entities through connected nodes",
                structure={
                    'nodes': ['source', 'intermediate', 'sink'],
                    'edges': [
                        ('source', 'intermediate', 'flows_to'),
                        ('intermediate', 'sink', 'flows_to')
                    ]
                },
                abstraction_level=1,
                generality_score=0.85
            ),
            AbstractPattern(
                id="equilibrium",
                name="Equilibrium System",
                description="Forces balancing to stable state",
                structure={
                    'nodes': ['force_1', 'force_2', 'balance_point'],
                    'edges': [
                        ('force_1', 'balance_point', 'pushes'),
                        ('force_2', 'balance_point', 'pushes')
                    ],
                    'constraints': ['force_1 + force_2 = 0 at balance']
                },
                abstraction_level=2,
                generality_score=0.8
            )
        ]

        for p in patterns:
            self.patterns[p.id] = p

    def find_matching_patterns(
        self,
        domain: DomainStructure,
        min_match_score: float = 0.5
    ) -> List[Tuple[AbstractPattern, float]]:
        """Find abstract patterns that match a domain"""
        matches = []

        for pattern in self.patterns.values():
            score = self._compute_pattern_match(pattern, domain)
            if score >= min_match_score:
                matches.append((pattern, score))

        matches.sort(key=lambda x: -x[1])
        return matches

    def _compute_pattern_match(
        self,
        pattern: AbstractPattern,
        domain: DomainStructure
    ) -> float:
        """Compute how well a pattern matches a domain"""
        structure = pattern.structure

        # Check node count compatibility
        pattern_nodes = len(structure.get('nodes', []))
        domain_nodes = len(domain.concepts)

        if domain_nodes < pattern_nodes:
            return 0.0

        # Check edge pattern compatibility
        pattern_edges = structure.get('edges', [])
        domain_edge_types = set()
        for rel in domain.relations.values():
            domain_edge_types.add(rel.relation_type)

        # Simple heuristic: check if domain has similar edge types
        edge_match = 0
        for edge in pattern_edges:
            edge_type = edge[2] if len(edge) > 2 else 'generic'
            if edge_type in domain_edge_types or edge_type == 'generic':
                edge_match += 1

        edge_score = edge_match / len(pattern_edges) if pattern_edges else 1.0

        # Node coverage
        node_score = min(1.0, domain_nodes / pattern_nodes)

        return 0.5 * edge_score + 0.5 * node_score

    def register_pattern_instance(
        self,
        pattern_id: str,
        domain_id: str,
        mapping_id: str
    ):
        """Register a domain as instance of pattern"""
        if pattern_id in self.patterns:
            self.patterns[pattern_id].instances.append((domain_id, mapping_id))


# =============================================================================
# Deep Analogical Transfer Engine (Main Class)
# =============================================================================

class DeepAnalogicalTransferEngine:
    """
    Main orchestrator for deep analogical transfer.
    Integrates all components for cross-domain reasoning and transfer.
    """

    def __init__(self):
        self.domain_modeler = DomainModeler()
        self.structural_aligner = StructuralAligner(self.domain_modeler)
        self.analogical_reasoner = AnalogicalReasoner(
            self.domain_modeler, self.structural_aligner
        )
        self.transfer_engine = TransferEngine(
            self.domain_modeler,
            self.structural_aligner,
            self.analogical_reasoner
        )
        self.pattern_library = AbstractPatternLibrary()

        logger.info("DeepAnalogicalTransferEngine initialized")

    def create_domain(
        self,
        name: str,
        domain_type: str,
        concepts: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ) -> str:
        """Create a new domain and return its ID"""
        type_map = {
            'physical': DomainType.PHYSICAL,
            'mathematical': DomainType.MATHEMATICAL,
            'biological': DomainType.BIOLOGICAL,
            'social': DomainType.SOCIAL,
            'computational': DomainType.COMPUTATIONAL,
            'economic': DomainType.ECONOMIC,
            'abstract': DomainType.ABSTRACT
        }

        domain = self.domain_modeler.create_domain(
            name=name,
            domain_type=type_map.get(domain_type.lower(), DomainType.ABSTRACT),
            concepts=concepts,
            relations=relations
        )

        return domain.id

    def find_analogy(
        self,
        source_domain_id: str,
        target_domain_id: str,
        strategy: str = 'structural'
    ) -> Dict[str, Any]:
        """Find analogical mapping between domains"""
        mapping = self.structural_aligner.find_alignment(
            source_domain_id, target_domain_id, strategy
        )

        return {
            'mapping_id': mapping.id,
            'similarity': mapping.similarity_score,
            'systematicity': mapping.systematicity,
            'confidence': mapping.confidence,
            'concept_mappings': {
                k.split('_')[-1]: v.split('_')[-1]
                for k, v in mapping.concept_mappings.items()
            },
            'relation_type': mapping.relation_type.name
        }

    def transfer_knowledge(
        self,
        source_domain_id: str,
        target_domain_id: str,
        knowledge: Dict[str, Any],
        strategy: str = 'adapted'
    ) -> Dict[str, Any]:
        """Transfer knowledge between domains"""
        strategy_map = {
            'direct': TransferStrategy.DIRECT,
            'adapted': TransferStrategy.ADAPTED,
            'generalized': TransferStrategy.GENERALIZED,
            'compositional': TransferStrategy.COMPOSITIONAL
        }

        transferred = self.transfer_engine.transfer_solution(
            source_domain_id,
            target_domain_id,
            knowledge,
            strategy_map.get(strategy.lower(), TransferStrategy.ADAPTED)
        )

        return transferred

    def make_analogical_inference(
        self,
        source_domain_id: str,
        target_domain_id: str,
        source_fact: str
    ) -> Dict[str, Any]:
        """Make inference in target domain based on source fact"""
        inference = self.analogical_reasoner.make_inference(
            source_domain_id, target_domain_id, source_fact
        )

        return {
            'source_fact': inference.source_fact,
            'inferred_fact': inference.inferred_fact,
            'confidence': inference.confidence,
            'justification': inference.justification
        }

    def solve_analogy(
        self,
        a: str,
        b: str,
        c: str,
        domain_id: str
    ) -> Dict[str, Any]:
        """Solve A:B :: C:? analogy"""
        answer, confidence = self.analogical_reasoner.solve_proportional_analogy(
            a, b, c, domain_id
        )

        return {
            'a': a,
            'b': b,
            'c': c,
            'd': answer,
            'confidence': confidence,
            'analogy': f"{a}:{b} :: {c}:{answer}"
        }

    def find_cross_domain_patterns(
        self,
        domain_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Find patterns that span multiple domains"""
        results = []

        for pattern in self.pattern_library.patterns.values():
            matching_domains = []

            for domain_id in domain_ids:
                domain = self.domain_modeler.domains.get(domain_id)
                if domain:
                    score = self.pattern_library._compute_pattern_match(pattern, domain)
                    if score > 0.5:
                        matching_domains.append((domain_id, score))

            if len(matching_domains) >= 2:
                results.append({
                    'pattern': pattern.name,
                    'description': pattern.description,
                    'matching_domains': matching_domains,
                    'generality': pattern.generality_score
                })

        return results

    def get_domain_summary(self, domain_id: str) -> Dict[str, Any]:
        """Get summary of a domain"""
        domain = self.domain_modeler.domains.get(domain_id)
        if not domain:
            return {}

        return {
            'id': domain.id,
            'type': domain.domain_type.name,
            'n_concepts': len(domain.concepts),
            'n_relations': len(domain.relations),
            'concepts': [c.name for c in domain.concepts.values()],
            'relation_types': list(set(r.relation_type for r in domain.relations.values()))
        }


# =============================================================================
# Factory Functions
# =============================================================================

def create_analogical_transfer_engine() -> DeepAnalogicalTransferEngine:
    """Create a configured analogical transfer engine"""
    return DeepAnalogicalTransferEngine()


def find_structural_analogy(
    source_concepts: List[Dict],
    source_relations: List[Dict],
    target_concepts: List[Dict],
    target_relations: List[Dict]
) -> Dict[str, Any]:
    """Convenience function for finding structural analogy"""
    engine = create_analogical_transfer_engine()

    source_id = engine.create_domain(
        "source", "abstract", source_concepts, source_relations
    )
    target_id = engine.create_domain(
        "target", "abstract", target_concepts, target_relations
    )

    return engine.find_analogy(source_id, target_id)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Enums
    'AnalogicalRelationType',
    'MappingType',
    'DomainType',
    'TransferStrategy',

    # Data classes
    'Concept',
    'Relation',
    'DomainStructure',
    'AnalogicalMapping',
    'AnalogicalInference',
    'AbstractPattern',

    # Core classes
    'DomainModeler',
    'StructuralAligner',
    'AnalogicalReasoner',
    'TransferEngine',
    'AbstractPatternLibrary',
    'DeepAnalogicalTransferEngine',

    # Factory functions
    'create_analogical_transfer_engine',
    'find_structural_analogy'
]


