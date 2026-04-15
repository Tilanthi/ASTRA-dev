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
Analogical Reasoning Engine for STAN V41

Cross-domain structural mapping and solution transfer:
- Structure Mapping Theory implementation
- Cross-domain analogy detection
- Solution transfer from similar solved problems
- Semantic (not just syntactic) template composition

Date: 2025-12-11
Version: 41.0
"""

import time
import uuid
import math
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re

from .unified_world_model import (
    UnifiedWorldModel, Hypothesis, Evidence, EvidenceSource,
    AbstractionTemplate, get_world_model
)
from .integration_bus import IntegrationBus, EventType, get_integration_bus


class AnalogyType(Enum):
    """Types of analogies"""
    STRUCTURAL = "structural"  # Same relational structure
    SUPERFICIAL = "superficial"  # Surface feature similarity
    CAUSAL = "causal"  # Same causal mechanisms
    FUNCTIONAL = "functional"  # Same purpose/function
    MATHEMATICAL = "mathematical"  # Same mathematical form


class MappingConstraint(Enum):
    """Constraints on analogical mappings"""
    ONE_TO_ONE = "one_to_one"  # Each element maps to at most one
    PARALLEL_CONNECTIVITY = "parallel_connectivity"  # Preserve relations
    SYSTEMATICITY = "systematicity"  # Prefer deeper relational matches


@dataclass
class StructuralElement:
    """An element in a structural representation"""
    element_id: str
    element_type: str  # "entity", "relation", "attribute", "higher_order"
    name: str
    arguments: List[str] = field(default_factory=list)  # For relations
    attributes: Dict[str, Any] = field(default_factory=dict)
    domain: str = ""


@dataclass
class StructuralMapping:
    """A mapping between two structural representations"""
    mapping_id: str
    source_domain: str
    target_domain: str
    entity_mappings: Dict[str, str]  # source -> target
    relation_mappings: Dict[str, str]
    attribute_mappings: Dict[str, str]
    score: float = 0.0
    confidence: float = 0.0
    systematicity_score: float = 0.0
    inferences: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.mapping_id:
            self.mapping_id = f"map_{uuid.uuid4().hex[:8]}"


@dataclass
class Analogy:
    """A complete analogy between domains"""
    analogy_id: str
    source: 'DomainRepresentation'
    target: 'DomainRepresentation'
    mapping: StructuralMapping
    analogy_type: AnalogyType
    quality_score: float
    candidate_inferences: List[str]
    explanation: str

    def __post_init__(self):
        if not self.analogy_id:
            self.analogy_id = f"ana_{uuid.uuid4().hex[:8]}"


@dataclass
class DomainRepresentation:
    """Structured representation of a domain"""
    domain_id: str
    domain_name: str
    entities: Dict[str, StructuralElement]
    relations: Dict[str, StructuralElement]
    higher_order_relations: Dict[str, StructuralElement]
    attributes: Dict[str, Dict[str, Any]]
    causal_structure: List[Tuple[str, str]]  # (cause, effect) pairs

    def __post_init__(self):
        if not self.domain_id:
            self.domain_id = f"dom_{uuid.uuid4().hex[:8]}"


@dataclass
class SolutionTransfer:
    """A transferred solution from source to target problem"""
    transfer_id: str
    source_problem: str
    source_solution: str
    target_problem: str
    transferred_solution: str
    analogy: Analogy
    adaptation_steps: List[str]
    confidence: float
    warnings: List[str] = field(default_factory=list)


class StructureMapper:
    """
    Implements Structure Mapping Theory (Gentner, 1983).

    Maps structural correspondences between domains while
    respecting constraints of one-to-one mapping, parallel
    connectivity, and systematicity.
    """

    def __init__(self):
        self.similarity_cache: Dict[str, float] = {}

    def find_mapping(self,
                     source: DomainRepresentation,
                     target: DomainRepresentation) -> StructuralMapping:
        """
        Find the best structural mapping between domains.

        Uses greedy match with systematicity preference.
        """
        entity_mappings = {}
        relation_mappings = {}
        attribute_mappings = {}

        # Step 1: Find relation matches (most important for structural analogy)
        relation_matches = self._match_relations(source, target)
        relation_mappings = {m[0]: m[1] for m in relation_matches}

        # Step 2: Derive entity mappings from relation mappings
        entity_mappings = self._derive_entity_mappings(
            source, target, relation_mappings
        )

        # Step 3: Map attributes
        attribute_mappings = self._map_attributes(
            source, target, entity_mappings
        )

        # Step 4: Calculate scores
        systematicity = self._calculate_systematicity(
            source, target, relation_mappings
        )

        overall_score = self._calculate_mapping_score(
            entity_mappings, relation_mappings, attribute_mappings,
            source, target
        )

        # Step 5: Generate inferences
        inferences = self._generate_inferences(
            source, target, entity_mappings, relation_mappings
        )

        return StructuralMapping(
            mapping_id="",
            source_domain=source.domain_name,
            target_domain=target.domain_name,
            entity_mappings=entity_mappings,
            relation_mappings=relation_mappings,
            attribute_mappings=attribute_mappings,
            score=overall_score,
            confidence=min(0.95, overall_score),
            systematicity_score=systematicity,
            inferences=inferences
        )

    def _match_relations(self,
                         source: DomainRepresentation,
                         target: DomainRepresentation) -> List[Tuple[str, str, float]]:
        """Match relations between domains"""
        matches = []

        for src_rel_id, src_rel in source.relations.items():
            best_match = None
            best_score = 0

            for tgt_rel_id, tgt_rel in target.relations.items():
                score = self._relation_similarity(src_rel, tgt_rel)

                if score > best_score:
                    best_score = score
                    best_match = tgt_rel_id

            if best_match and best_score > 0.3:
                matches.append((src_rel_id, best_match, best_score))

        # Sort by score and enforce one-to-one
        matches.sort(key=lambda x: x[2], reverse=True)
        used_targets = set()
        final_matches = []

        for src, tgt, score in matches:
            if tgt not in used_targets:
                final_matches.append((src, tgt, score))
                used_targets.add(tgt)

        return final_matches

    def _relation_similarity(self, rel1: StructuralElement,
                              rel2: StructuralElement) -> float:
        """Calculate similarity between two relations"""
        cache_key = f"{rel1.element_id}_{rel2.element_id}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]

        # Same name = high similarity
        if rel1.name.lower() == rel2.name.lower():
            score = 0.9
        # Same arity
        elif len(rel1.arguments) == len(rel2.arguments):
            # Check for semantic similarity
            score = self._semantic_similarity(rel1.name, rel2.name)
        else:
            score = 0.1

        self.similarity_cache[cache_key] = score
        return score

    def _semantic_similarity(self, name1: str, name2: str) -> float:
        """Calculate semantic similarity between relation names"""
        # Simple word overlap similarity
        words1 = set(name1.lower().replace('_', ' ').split())
        words2 = set(name2.lower().replace('_', ' ').split())

        if not words1 or not words2:
            return 0.3

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        jaccard = len(intersection) / len(union) if union else 0

        # Boost for common relational terms
        relational_terms = {'cause', 'effect', 'increase', 'decrease', 'enable',
                          'prevent', 'similar', 'different', 'contain', 'part'}

        boost = 0.1 if (words1.intersection(relational_terms) and
                        words2.intersection(relational_terms)) else 0

        return min(0.8, jaccard + boost)

    def _derive_entity_mappings(self,
                                source: DomainRepresentation,
                                target: DomainRepresentation,
                                relation_mappings: Dict[str, str]) -> Dict[str, str]:
        """Derive entity mappings from relation mappings"""
        entity_mappings = {}
        votes = defaultdict(lambda: defaultdict(int))

        # For each mapped relation, the arguments should map
        for src_rel_id, tgt_rel_id in relation_mappings.items():
            src_rel = source.relations.get(src_rel_id)
            tgt_rel = target.relations.get(tgt_rel_id)

            if not src_rel or not tgt_rel:
                continue

            # Arguments in same position should map
            for i, src_arg in enumerate(src_rel.arguments):
                if i < len(tgt_rel.arguments):
                    tgt_arg = tgt_rel.arguments[i]
                    votes[src_arg][tgt_arg] += 1

        # Select highest-voted mappings
        used_targets = set()
        for src_entity in sorted(votes.keys()):
            if not votes[src_entity]:
                continue

            # Get best unassigned target
            sorted_targets = sorted(
                votes[src_entity].items(),
                key=lambda x: x[1],
                reverse=True
            )

            for tgt_entity, count in sorted_targets:
                if tgt_entity not in used_targets:
                    entity_mappings[src_entity] = tgt_entity
                    used_targets.add(tgt_entity)
                    break

        return entity_mappings

    def _map_attributes(self,
                        source: DomainRepresentation,
                        target: DomainRepresentation,
                        entity_mappings: Dict[str, str]) -> Dict[str, str]:
        """Map attributes between corresponding entities"""
        attr_mappings = {}

        for src_entity, tgt_entity in entity_mappings.items():
            src_attrs = source.attributes.get(src_entity, {})
            tgt_attrs = target.attributes.get(tgt_entity, {})

            for src_attr in src_attrs:
                # Find matching attribute in target
                if src_attr in tgt_attrs:
                    attr_mappings[f"{src_entity}.{src_attr}"] = f"{tgt_entity}.{src_attr}"
                else:
                    # Try semantic match
                    for tgt_attr in tgt_attrs:
                        if self._semantic_similarity(src_attr, tgt_attr) > 0.5:
                            attr_mappings[f"{src_entity}.{src_attr}"] = f"{tgt_entity}.{tgt_attr}"
                            break

        return attr_mappings

    def _calculate_systematicity(self,
                                  source: DomainRepresentation,
                                  target: DomainRepresentation,
                                  relation_mappings: Dict[str, str]) -> float:
        """
        Calculate systematicity score.

        Systematicity prefers mappings that preserve higher-order relations.
        """
        if not relation_mappings:
            return 0.0

        # Check if causal structure is preserved
        causal_preserved = 0
        causal_total = len(source.causal_structure)

        for src_cause, src_effect in source.causal_structure:
            tgt_cause = relation_mappings.get(src_cause)
            tgt_effect = relation_mappings.get(src_effect)

            if tgt_cause and tgt_effect:
                # Check if target has this causal relation
                if (tgt_cause, tgt_effect) in target.causal_structure:
                    causal_preserved += 1

        causal_score = causal_preserved / causal_total if causal_total > 0 else 0.5

        # Check higher-order relations
        ho_preserved = 0
        ho_total = len(source.higher_order_relations)

        for ho_rel_id, ho_rel in source.higher_order_relations.items():
            # Check if arguments are mapped
            args_mapped = all(
                arg in relation_mappings
                for arg in ho_rel.arguments
            )
            if args_mapped:
                ho_preserved += 1

        ho_score = ho_preserved / ho_total if ho_total > 0 else 0.5

        return 0.6 * causal_score + 0.4 * ho_score

    def _calculate_mapping_score(self,
                                  entity_mappings: Dict[str, str],
                                  relation_mappings: Dict[str, str],
                                  attribute_mappings: Dict[str, str],
                                  source: DomainRepresentation,
                                  target: DomainRepresentation) -> float:
        """Calculate overall mapping quality score"""
        # Coverage
        entity_coverage = len(entity_mappings) / max(1, len(source.entities))
        relation_coverage = len(relation_mappings) / max(1, len(source.relations))

        # Weight relations more heavily (structural analogy)
        coverage_score = 0.3 * entity_coverage + 0.7 * relation_coverage

        return coverage_score

    def _generate_inferences(self,
                              source: DomainRepresentation,
                              target: DomainRepresentation,
                              entity_mappings: Dict[str, str],
                              relation_mappings: Dict[str, str]) -> List[str]:
        """Generate candidate inferences from mapping"""
        inferences = []

        # For each unmapped source relation, suggest it might apply to target
        for src_rel_id, src_rel in source.relations.items():
            if src_rel_id not in relation_mappings:
                # Try to construct inference
                mapped_args = []
                can_infer = True

                for arg in src_rel.arguments:
                    if arg in entity_mappings:
                        mapped_args.append(entity_mappings[arg])
                    else:
                        can_infer = False
                        break

                if can_infer and mapped_args:
                    inference = f"{src_rel.name}({', '.join(mapped_args)}) [inferred from analogy]"
                    inferences.append(inference)

        return inferences[:10]  # Limit inferences


class AnalogyFinder:
    """
    Finds analogies between problems/domains.
    """

    def __init__(self,
                 world_model: Optional[UnifiedWorldModel] = None,
                 bus: Optional[IntegrationBus] = None):
        self.world_model = world_model or get_world_model()
        self.bus = bus or get_integration_bus()
        self.mapper = StructureMapper()

        # Knowledge base of known domains
        self.domain_library: Dict[str, DomainRepresentation] = {}

        # Cached analogies
        self.analogy_cache: Dict[str, Analogy] = {}

    def register_domain(self, domain: DomainRepresentation):
        """Register a domain representation in the library"""
        self.domain_library[domain.domain_id] = domain

    def find_analogies(self,
                       target: DomainRepresentation,
                       min_score: float = 0.4,
                       max_results: int = 5) -> List[Analogy]:
        """
        Find analogies to target from known domains.

        Args:
            target: Target domain to find analogies for
            min_score: Minimum analogy quality score
            max_results: Maximum number of analogies to return

        Returns:
            List of Analogy objects sorted by quality
        """
        analogies = []

        for source_id, source in self.domain_library.items():
            if source_id == target.domain_id:
                continue

            # Find mapping
            mapping = self.mapper.find_mapping(source, target)

            if mapping.score < min_score:
                continue

            # Determine analogy type
            analogy_type = self._classify_analogy(source, target, mapping)

            # Generate explanation
            explanation = self._generate_analogy_explanation(
                source, target, mapping, analogy_type
            )

            analogy = Analogy(
                analogy_id="",
                source=source,
                target=target,
                mapping=mapping,
                analogy_type=analogy_type,
                quality_score=mapping.score,
                candidate_inferences=mapping.inferences,
                explanation=explanation
            )

            analogies.append(analogy)

        # Sort by quality and return top results
        analogies.sort(key=lambda a: a.quality_score, reverse=True)

        # Publish best analogy
        if analogies:
            self.bus.publish(
                EventType.ANALOGY_FOUND,
                "analogy_finder",
                {
                    'target_domain': target.domain_name,
                    'best_source': analogies[0].source.domain_name,
                    'quality': analogies[0].quality_score
                }
            )

        return analogies[:max_results]

    def find_analogy_for_problem(self,
                                  problem_text: str,
                                  problem_domain: str) -> Optional[Analogy]:
        """
        Find analogy for a problem described in text.

        Args:
            problem_text: Natural language problem description
            problem_domain: Domain of the problem

        Returns:
            Best analogy if found, None otherwise
        """
        # Extract structural representation from problem
        target = self._extract_domain_representation(problem_text, problem_domain)

        # Find analogies
        analogies = self.find_analogies(target, min_score=0.3, max_results=1)

        return analogies[0] if analogies else None

    def transfer_solution(self,
                          source_problem: str,
                          source_solution: str,
                          target_problem: str,
                          analogy: Optional[Analogy] = None) -> SolutionTransfer:
        """
        Transfer a solution from source to target problem.

        Args:
            source_problem: Source problem description
            source_solution: Solution to source problem
            target_problem: Target problem description
            analogy: Pre-computed analogy (computed if not provided)

        Returns:
            SolutionTransfer with adapted solution
        """
        # Find analogy if not provided
        if not analogy:
            source_domain = self._extract_domain_representation(
                source_problem, "source"
            )
            target_domain = self._extract_domain_representation(
                target_problem, "target"
            )
            mapping = self.mapper.find_mapping(source_domain, target_domain)
            analogy = Analogy(
                analogy_id="",
                source=source_domain,
                target=target_domain,
                mapping=mapping,
                analogy_type=AnalogyType.STRUCTURAL,
                quality_score=mapping.score,
                candidate_inferences=mapping.inferences,
                explanation=""
            )

        # Transfer solution by substituting mapped entities
        transferred = self._substitute_entities(
            source_solution,
            analogy.mapping.entity_mappings
        )

        # Apply adaptations
        adaptation_steps, warnings = self._adapt_solution(
            transferred, analogy
        )

        confidence = analogy.quality_score * 0.8  # Slightly lower for transfer

        return SolutionTransfer(
            transfer_id=f"xfer_{uuid.uuid4().hex[:8]}",
            source_problem=source_problem,
            source_solution=source_solution,
            target_problem=target_problem,
            transferred_solution=transferred,
            analogy=analogy,
            adaptation_steps=adaptation_steps,
            confidence=confidence,
            warnings=warnings
        )

    def _extract_domain_representation(self,
                                        text: str,
                                        domain_name: str) -> DomainRepresentation:
        """Extract structured domain representation from text"""
        entities = {}
        relations = {}
        attributes = {}
        causal_structure = []

        # Simple extraction using patterns
        # (In practice, would use NLP/parsing)

        # Extract entities (capitalized words, quoted terms)
        entity_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Capitalized
            r'"([^"]+)"',  # Quoted
            r'the\s+(\w+)',  # "the X"
        ]

        entity_id = 0
        for pattern in entity_patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1)
                if name.lower() not in ['the', 'a', 'an', 'is', 'are']:
                    eid = f"e_{entity_id}"
                    entities[eid] = StructuralElement(
                        element_id=eid,
                        element_type="entity",
                        name=name,
                        domain=domain_name
                    )
                    entity_id += 1

        # Extract relations (verbs between entities)
        relation_patterns = [
            r'(\w+)\s+(causes?|leads?\s+to|results?\s+in)\s+(\w+)',
            r'(\w+)\s+(is|are)\s+(greater|less|equal)\s+(?:than|to)\s+(\w+)',
            r'(\w+)\s+(increases?|decreases?|affects?)\s+(\w+)',
        ]

        rel_id = 0
        for pattern in relation_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                groups = match.groups()
                rid = f"r_{rel_id}"
                relations[rid] = StructuralElement(
                    element_id=rid,
                    element_type="relation",
                    name=groups[1] if len(groups) > 1 else "relates",
                    arguments=[groups[0], groups[-1]],
                    domain=domain_name
                )

                # If causal, add to structure
                if any(c in groups[1].lower() for c in ['cause', 'lead', 'result']):
                    causal_structure.append((groups[0], groups[-1]))

                rel_id += 1

        return DomainRepresentation(
            domain_id="",
            domain_name=domain_name,
            entities=entities,
            relations=relations,
            higher_order_relations={},
            attributes=attributes,
            causal_structure=causal_structure
        )

    def _classify_analogy(self,
                          source: DomainRepresentation,
                          target: DomainRepresentation,
                          mapping: StructuralMapping) -> AnalogyType:
        """Classify the type of analogy"""
        # Check for causal analogy
        if source.causal_structure and mapping.systematicity_score > 0.6:
            return AnalogyType.CAUSAL

        # Check for mathematical analogy
        math_terms = {'equation', 'formula', 'function', 'variable'}
        if any(t in source.domain_name.lower() for t in math_terms):
            return AnalogyType.MATHEMATICAL

        # Default to structural
        if mapping.score > 0.5:
            return AnalogyType.STRUCTURAL

        return AnalogyType.SUPERFICIAL

    def _generate_analogy_explanation(self,
                                       source: DomainRepresentation,
                                       target: DomainRepresentation,
                                       mapping: StructuralMapping,
                                       analogy_type: AnalogyType) -> str:
        """Generate human-readable explanation of analogy"""
        entity_pairs = list(mapping.entity_mappings.items())[:3]
        relation_pairs = list(mapping.relation_mappings.items())[:2]

        entity_str = ", ".join([
            f"{s} ↔ {t}" for s, t in entity_pairs
        ])

        relation_str = ", ".join([
            f"{source.relations[s].name if s in source.relations else s} ↔ "
            f"{target.relations[t].name if t in target.relations else t}"
            for s, t in relation_pairs
        ])

        return (
            f"The {source.domain_name} domain is analogous to {target.domain_name} "
            f"({analogy_type.value} analogy, score: {mapping.score:.2f}). "
            f"Entity correspondences: {entity_str}. "
            f"Relation correspondences: {relation_str}."
        )

    def _substitute_entities(self,
                              solution: str,
                              entity_mappings: Dict[str, str]) -> str:
        """Substitute source entities with target entities in solution"""
        result = solution

        for src, tgt in entity_mappings.items():
            # Replace whole words only
            pattern = r'\b' + re.escape(src) + r'\b'
            result = re.sub(pattern, tgt, result, flags=re.IGNORECASE)

        return result

    def _adapt_solution(self,
                        transferred: str,
                        analogy: Analogy) -> Tuple[List[str], List[str]]:
        """Adapt transferred solution to target domain"""
        adaptations = []
        warnings = []

        # Check for unmapped entities
        for entity_id, entity in analogy.source.entities.items():
            if entity_id not in analogy.mapping.entity_mappings:
                if entity.name in transferred:
                    warnings.append(
                        f"'{entity.name}' from source domain has no mapping in target"
                    )

        # Add adaptation steps
        if analogy.mapping.inferences:
            adaptations.append("Applied analogical inferences:")
            adaptations.extend([f"  - {inf}" for inf in analogy.mapping.inferences[:3]])

        if analogy.analogy_type == AnalogyType.CAUSAL:
            adaptations.append("Preserved causal structure from source domain")

        return adaptations, warnings


class SemanticTemplateComposer:
    """
    Composes templates based on semantic relationships, not just syntax.
    """

    def __init__(self):
        self.semantic_relations = {
            'causes': ('causal', 1.0),
            'enables': ('enabling', 0.8),
            'prevents': ('preventive', -0.8),
            'opposes': ('oppositional', -1.0),
            'similar_to': ('similarity', 0.7),
            'instance_of': ('instantiation', 0.9),
            'part_of': ('compositional', 0.6),
        }

    def compose(self,
                template1: AbstractionTemplate,
                template2: AbstractionTemplate,
                relation: str) -> AbstractionTemplate:
        """
        Compose two templates based on semantic relation.

        Args:
            template1: First template
            template2: Second template
            relation: Semantic relation between them

        Returns:
            Composed template
        """
        rel_type, strength = self.semantic_relations.get(
            relation, ('generic', 0.5)
        )

        if rel_type == 'causal':
            return self._compose_causal(template1, template2, strength)
        elif rel_type == 'enabling':
            return self._compose_enabling(template1, template2, strength)
        elif rel_type == 'compositional':
            return self._compose_compositional(template1, template2)
        elif rel_type == 'instantiation':
            return self._compose_instantiation(template1, template2)
        else:
            return self._compose_generic(template1, template2, relation)

    def _compose_causal(self,
                        cause: AbstractionTemplate,
                        effect: AbstractionTemplate,
                        strength: float) -> AbstractionTemplate:
        """Compose templates with causal semantics"""
        # Combined expression: effect = f(cause, ...)
        combined_vars = list(set(cause.variables + effect.variables))

        expression = f"({effect.expression}) = f({cause.expression}, {strength})"

        return AbstractionTemplate(
            template_id="",
            name=f"{cause.name}_causes_{effect.name}",
            expression=expression,
            variables=combined_vars,
            domain=cause.domain,
            confidence=min(cause.confidence, effect.confidence) * 0.9,
            related_templates={cause.template_id, effect.template_id}
        )

    def _compose_enabling(self,
                          enabler: AbstractionTemplate,
                          enabled: AbstractionTemplate,
                          strength: float) -> AbstractionTemplate:
        """Compose templates with enabling semantics"""
        combined_vars = list(set(enabler.variables + enabled.variables))

        expression = f"({enabled.expression}) * indicator({enabler.expression} > 0)"

        return AbstractionTemplate(
            template_id="",
            name=f"{enabler.name}_enables_{enabled.name}",
            expression=expression,
            variables=combined_vars,
            domain=enabler.domain,
            confidence=min(enabler.confidence, enabled.confidence) * 0.85
        )

    def _compose_compositional(self,
                               part: AbstractionTemplate,
                               whole: AbstractionTemplate) -> AbstractionTemplate:
        """Compose templates with part-whole semantics"""
        expression = f"({whole.expression}) contains ({part.expression})"

        return AbstractionTemplate(
            template_id="",
            name=f"{part.name}_part_of_{whole.name}",
            expression=expression,
            variables=list(set(part.variables + whole.variables)),
            domain=whole.domain,
            confidence=min(part.confidence, whole.confidence) * 0.8
        )

    def _compose_instantiation(self,
                               instance: AbstractionTemplate,
                               general: AbstractionTemplate) -> AbstractionTemplate:
        """Compose templates with instantiation semantics"""
        # Instance is a specific case of general
        expression = f"({instance.expression}) satisfies ({general.expression})"

        return AbstractionTemplate(
            template_id="",
            name=f"{instance.name}_instance_of_{general.name}",
            expression=expression,
            variables=instance.variables,
            domain=instance.domain,
            confidence=instance.confidence * general.confidence
        )

    def _compose_generic(self,
                         template1: AbstractionTemplate,
                         template2: AbstractionTemplate,
                         relation: str) -> AbstractionTemplate:
        """Generic composition"""
        expression = f"({template1.expression}) {relation} ({template2.expression})"

        return AbstractionTemplate(
            template_id="",
            name=f"{template1.name}_{relation}_{template2.name}",
            expression=expression,
            variables=list(set(template1.variables + template2.variables)),
            domain=template1.domain,
            confidence=min(template1.confidence, template2.confidence) * 0.7
        )


# Export
__all__ = [
    'AnalogyFinder',
    'StructureMapper',
    'SemanticTemplateComposer',
    'Analogy',
    'AnalogyType',
    'StructuralMapping',
    'DomainRepresentation',
    'StructuralElement',
    'SolutionTransfer',
    'MappingConstraint'
]


