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
Phase 2: Analogical Reasoning Engine

Enables reasoning by analogy - finding structural similarities
between problems and transferring solutions across domains.

Key capabilities:
- Structure extraction from problems
- Analogy finding through structural matching
- Solution transfer with domain adaptation
- Abstract pattern learning from multiple examples
"""

import re
import math
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
from collections import defaultdict
import json


class RelationType(Enum):
    """Types of relations in problem structures"""
    CAUSAL = "causal"           # A causes B
    TEMPORAL = "temporal"       # A before/after B
    SPATIAL = "spatial"         # A contains/near B
    MATHEMATICAL = "mathematical"  # A = f(B)
    LOGICAL = "logical"         # A implies B
    COMPOSITIONAL = "compositional"  # A is part of B
    COMPARATIVE = "comparative"  # A > B, A similar to B
    FUNCTIONAL = "functional"   # A used for B


class EntityType(Enum):
    """Types of entities in problem structures"""
    OBJECT = "object"
    QUANTITY = "quantity"
    PROCESS = "process"
    STATE = "state"
    CONSTRAINT = "constraint"
    GOAL = "goal"
    AGENT = "agent"


@dataclass
class Entity:
    """An entity in a problem structure"""
    name: str
    entity_type: EntityType
    properties: Dict[str, Any] = field(default_factory=dict)
    role: str = ""  # Role in the problem (e.g., "input", "output", "constraint")


@dataclass
class Relation:
    """A relation between entities"""
    source: str  # Entity name
    target: str  # Entity name
    relation_type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProblemStructure:
    """Abstract structure of a problem"""
    entities: List[Entity]
    relations: List[Relation]
    goal: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    domain: str = ""
    complexity: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'entities': [{'name': e.name, 'type': e.entity_type.value,
                         'properties': e.properties, 'role': e.role}
                        for e in self.entities],
            'relations': [{'source': r.source, 'target': r.target,
                          'type': r.relation_type.value, 'properties': r.properties}
                         for r in self.relations],
            'goal': self.goal,
            'constraints': self.constraints,
            'domain': self.domain,
            'complexity': self.complexity
        }

    def get_signature(self) -> str:
        """Get a structural signature for matching"""
        # Count entity types
        entity_counts = defaultdict(int)
        for e in self.entities:
            entity_counts[e.entity_type.value] += 1

        # Count relation types
        relation_counts = defaultdict(int)
        for r in self.relations:
            relation_counts[r.relation_type.value] += 1

        signature = f"E:{dict(entity_counts)}_R:{dict(relation_counts)}"
        return signature


@dataclass
class Analogy:
    """An analogy between two problems"""
    source_problem: str
    target_problem: str
    source_structure: ProblemStructure
    target_structure: ProblemStructure
    entity_mapping: Dict[str, str]  # source entity -> target entity
    relation_mapping: Dict[Tuple[str, str], Tuple[str, str]]  # source rel -> target rel
    similarity_score: float
    structural_match: float
    semantic_match: float
    source_solution: Optional[str] = None


@dataclass
class AbstractPattern:
    """An abstract pattern extracted from multiple problems"""
    name: str
    description: str
    abstract_structure: ProblemStructure
    solution_template: str
    instances: List[str] = field(default_factory=list)  # Problem IDs
    success_rate: float = 0.0
    domains: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'structure': self.abstract_structure.to_dict(),
            'solution_template': self.solution_template,
            'instances': self.instances,
            'success_rate': self.success_rate,
            'domains': list(self.domains)
        }


class StructuralMapper:
    """
    Maps structures between source and target problems
    to find analogical correspondences.
    """

    def __init__(self):
        self.entity_similarity_cache = {}
        self.relation_similarity_cache = {}

    def compute_mapping(self, source: ProblemStructure,
                       target: ProblemStructure) -> Tuple[Dict[str, str], float]:
        """
        Compute optimal entity mapping between structures.

        Uses structural alignment based on relational correspondences.

        Returns:
            (entity_mapping, alignment_score)
        """
        # Build entity similarity matrix
        similarity_matrix = self._build_similarity_matrix(source, target)

        # Find optimal mapping using greedy assignment
        mapping, score = self._greedy_assignment(
            source.entities, target.entities, similarity_matrix
        )

        return mapping, score

    def _build_similarity_matrix(self, source: ProblemStructure,
                                target: ProblemStructure) -> Dict[Tuple[str, str], float]:
        """Build similarity matrix between source and target entities"""
        matrix = {}

        for s_entity in source.entities:
            for t_entity in target.entities:
                # Base similarity from entity type
                type_sim = 1.0 if s_entity.entity_type == t_entity.entity_type else 0.3

                # Similarity from role
                role_sim = 1.0 if s_entity.role == t_entity.role else 0.5

                # Similarity from relational position
                s_relations = self._get_entity_relations(s_entity.name, source)
                t_relations = self._get_entity_relations(t_entity.name, target)
                relational_sim = self._compare_relational_position(s_relations, t_relations)

                # Combined similarity
                similarity = 0.3 * type_sim + 0.3 * role_sim + 0.4 * relational_sim
                matrix[(s_entity.name, t_entity.name)] = similarity

        return matrix

    def _get_entity_relations(self, entity_name: str,
                             structure: ProblemStructure) -> List[Tuple[str, RelationType, str]]:
        """Get all relations involving an entity"""
        relations = []
        for r in structure.relations:
            if r.source == entity_name:
                relations.append(('outgoing', r.relation_type, r.target))
            elif r.target == entity_name:
                relations.append(('incoming', r.relation_type, r.source))
        return relations

    def _compare_relational_position(self, s_relations: List, t_relations: List) -> float:
        """Compare relational positions of two entities"""
        if not s_relations and not t_relations:
            return 1.0
        if not s_relations or not t_relations:
            return 0.3

        # Count matching relation types
        s_types = set((r[0], r[1]) for r in s_relations)
        t_types = set((r[0], r[1]) for r in t_relations)

        if not s_types or not t_types:
            return 0.5

        intersection = len(s_types & t_types)
        union = len(s_types | t_types)

        return intersection / union if union > 0 else 0.5

    def _greedy_assignment(self, s_entities: List[Entity],
                          t_entities: List[Entity],
                          similarity_matrix: Dict[Tuple[str, str], float]) -> Tuple[Dict[str, str], float]:
        """Greedy assignment of source to target entities"""
        mapping = {}
        used_targets = set()
        total_score = 0.0

        # Sort source entities by max potential similarity
        s_names = [e.name for e in s_entities]
        t_names = [e.name for e in t_entities]

        # Greedy: assign each source to best available target
        for s_name in s_names:
            best_target = None
            best_sim = -1

            for t_name in t_names:
                if t_name not in used_targets:
                    sim = similarity_matrix.get((s_name, t_name), 0)
                    if sim > best_sim:
                        best_sim = sim
                        best_target = t_name

            if best_target:
                mapping[s_name] = best_target
                used_targets.add(best_target)
                total_score += best_sim

        # Normalize score
        if mapping:
            total_score /= len(mapping)

        return mapping, total_score


class StructureExtractor:
    """
    Extracts abstract problem structures from natural language.
    """

    def __init__(self):
        # Patterns for entity extraction
        self.entity_patterns = {
            EntityType.QUANTITY: [
                r'(\d+(?:\.\d+)?)\s*(\w+)',  # "5 apples"
                r'(the|a|an)\s+(\w+)\s+(?:is|are|equals?)\s+(\d+)',  # "the sum is 10"
            ],
            EntityType.OBJECT: [
                r'(the|a|an)\s+(\w+)',  # "the ball"
                r'(\w+)\'s\s+(\w+)',  # "John's car"
            ],
            EntityType.PROCESS: [
                r'(\w+ing)\s+(?:the|a|an)?\s*(\w+)',  # "running the program"
            ],
            EntityType.CONSTRAINT: [
                r'must\s+(.+?)(?:\.|,|$)',
                r'(?:given|if|when)\s+(.+?)(?:\.|,|then)',
                r'such that\s+(.+?)(?:\.|$)',
            ],
            EntityType.GOAL: [
                r'find\s+(.+?)(?:\.|$)',
                r'determine\s+(.+?)(?:\.|$)',
                r'calculate\s+(.+?)(?:\.|$)',
                r'what is\s+(.+?)(?:\?|$)',
            ]
        }

        # Patterns for relation extraction
        self.relation_patterns = {
            RelationType.CAUSAL: [
                r'(\w+)\s+causes?\s+(\w+)',
                r'(\w+)\s+leads?\s+to\s+(\w+)',
                r'because\s+(\w+).*?(\w+)',
            ],
            RelationType.MATHEMATICAL: [
                r'(\w+)\s*[=]\s*(\w+)',
                r'(\w+)\s+(?:is|are|equals?)\s+(\w+)',
                r'(\w+)\s*[+\-*/]\s*(\w+)',
            ],
            RelationType.COMPARATIVE: [
                r'(\w+)\s+(?:is|are)\s+(?:greater|more|larger)\s+than\s+(\w+)',
                r'(\w+)\s+(?:is|are)\s+(?:less|smaller|fewer)\s+than\s+(\w+)',
                r'(\w+)\s+(?:is|are)\s+(?:equal|same|similar)\s+(?:to|as)\s+(\w+)',
            ],
            RelationType.TEMPORAL: [
                r'(\w+)\s+(?:before|after|during|while)\s+(\w+)',
                r'first\s+(\w+).*?then\s+(\w+)',
            ],
            RelationType.LOGICAL: [
                r'if\s+(\w+)\s+then\s+(\w+)',
                r'(\w+)\s+implies?\s+(\w+)',
            ],
            RelationType.COMPOSITIONAL: [
                r'(\w+)\s+(?:contains?|includes?|has)\s+(\w+)',
                r'(\w+)\s+(?:is|are)\s+(?:part|member)\s+of\s+(\w+)',
            ]
        }

        # Domain detection patterns
        self.domain_patterns = {
            'mathematics': ['equation', 'solve', 'calculate', 'prove', 'theorem', 'formula', 'integral', 'derivative'],
            'physics': ['force', 'energy', 'velocity', 'mass', 'momentum', 'wave', 'particle', 'field'],
            'chemistry': ['molecule', 'reaction', 'element', 'compound', 'bond', 'solution', 'acid', 'base'],
            'biology': ['cell', 'gene', 'protein', 'species', 'organism', 'evolution', 'enzyme'],
            'computer_science': ['algorithm', 'function', 'variable', 'loop', 'data', 'program', 'code'],
            'economics': ['price', 'market', 'supply', 'demand', 'cost', 'profit', 'utility'],
        }

    def extract(self, problem: str, category: str = "") -> ProblemStructure:
        """
        Extract problem structure from natural language.

        Args:
            problem: Problem text
            category: Optional category hint

        Returns:
            ProblemStructure with entities, relations, goal, constraints
        """
        problem_lower = problem.lower()

        # Extract entities
        entities = self._extract_entities(problem)

        # Extract relations
        relations = self._extract_relations(problem, entities)

        # Extract goal
        goal = self._extract_goal(problem)

        # Extract constraints
        constraints = self._extract_constraints(problem)

        # Detect domain
        domain = self._detect_domain(problem, category)

        # Calculate complexity
        complexity = self._estimate_complexity(entities, relations, constraints)

        return ProblemStructure(
            entities=entities,
            relations=relations,
            goal=goal,
            constraints=constraints,
            domain=domain,
            complexity=complexity
        )

    def _extract_entities(self, problem: str) -> List[Entity]:
        """Extract entities from problem text"""
        entities = []
        seen_names = set()

        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, problem, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        # Take the most meaningful part
                        name = match[-1] if len(match[-1]) > 2 else match[0]
                    else:
                        name = match

                    name = name.strip().lower()

                    # Filter out common words
                    if name in {'the', 'a', 'an', 'is', 'are', 'and', 'or'}:
                        continue

                    if name not in seen_names and len(name) > 1:
                        seen_names.add(name)

                        # Determine role
                        role = self._determine_entity_role(name, problem)

                        entities.append(Entity(
                            name=name,
                            entity_type=entity_type,
                            properties={},
                            role=role
                        ))

        return entities[:10]  # Limit entities

    def _extract_relations(self, problem: str, entities: List[Entity]) -> List[Relation]:
        """Extract relations between entities"""
        relations = []
        entity_names = {e.name for e in entities}

        for rel_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, problem, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 2:
                        source = match[0].lower().strip()
                        target = match[1].lower().strip()

                        # Check if both are known entities or close matches
                        source_match = self._find_entity_match(source, entity_names)
                        target_match = self._find_entity_match(target, entity_names)

                        if source_match and target_match and source_match != target_match:
                            relations.append(Relation(
                                source=source_match,
                                target=target_match,
                                relation_type=rel_type,
                                properties={}
                            ))

        return relations[:15]  # Limit relations

    def _find_entity_match(self, name: str, entity_names: Set[str]) -> Optional[str]:
        """Find matching entity name"""
        if name in entity_names:
            return name

        # Fuzzy match
        for entity_name in entity_names:
            if name in entity_name or entity_name in name:
                return entity_name

        return None

    def _determine_entity_role(self, name: str, problem: str) -> str:
        """Determine the role of an entity in the problem"""
        problem_lower = problem.lower()

        # Check for input indicators
        input_patterns = [f'given {name}', f'{name} is given', f'with {name}']
        for pattern in input_patterns:
            if pattern in problem_lower:
                return 'input'

        # Check for output indicators
        output_patterns = [f'find {name}', f'what is {name}', f'determine {name}']
        for pattern in output_patterns:
            if pattern in problem_lower:
                return 'output'

        # Check for constraint indicators
        constraint_patterns = [f'{name} must', f'{name} should', f'{name} cannot']
        for pattern in constraint_patterns:
            if pattern in problem_lower:
                return 'constraint'

        return 'unknown'

    def _extract_goal(self, problem: str) -> Optional[str]:
        """Extract the goal from the problem"""
        goal_patterns = [
            r'find\s+(.+?)(?:\.|$)',
            r'determine\s+(.+?)(?:\.|$)',
            r'calculate\s+(.+?)(?:\.|$)',
            r'what\s+is\s+(.+?)(?:\?|$)',
            r'prove\s+(?:that\s+)?(.+?)(?:\.|$)',
            r'show\s+(?:that\s+)?(.+?)(?:\.|$)',
        ]

        for pattern in goal_patterns:
            match = re.search(pattern, problem, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_constraints(self, problem: str) -> List[str]:
        """Extract constraints from the problem"""
        constraints = []

        constraint_patterns = [
            r'(?:given|if|when|assume)\s+(.+?)(?:\.|,|then)',
            r'such that\s+(.+?)(?:\.|$)',
            r'where\s+(.+?)(?:\.|$)',
            r'with\s+the\s+constraint\s+(?:that\s+)?(.+?)(?:\.|$)',
        ]

        for pattern in constraint_patterns:
            matches = re.findall(pattern, problem, re.IGNORECASE)
            constraints.extend([m.strip() for m in matches])

        return constraints[:5]

    def _detect_domain(self, problem: str, category: str) -> str:
        """Detect the domain of the problem"""
        if category:
            category_lower = category.lower()
            for domain in self.domain_patterns.keys():
                if domain in category_lower:
                    return domain

        problem_lower = problem.lower()
        domain_scores = {}

        for domain, keywords in self.domain_patterns.items():
            score = sum(1 for kw in keywords if kw in problem_lower)
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            return max(domain_scores, key=domain_scores.get)

        return 'general'

    def _estimate_complexity(self, entities: List[Entity],
                            relations: List[Relation],
                            constraints: List[str]) -> float:
        """Estimate problem complexity"""
        # Base complexity from structure size
        entity_complexity = min(1.0, len(entities) / 10)
        relation_complexity = min(1.0, len(relations) / 15)
        constraint_complexity = min(1.0, len(constraints) / 5)

        # Weighted combination
        complexity = (
            0.3 * entity_complexity +
            0.4 * relation_complexity +
            0.3 * constraint_complexity
        )

        return complexity


class AnalogyFinder:
    """
    Finds analogies between problems by matching structures.
    """

    def __init__(self):
        self.structure_extractor = StructureExtractor()
        self.structural_mapper = StructuralMapper()
        self.problem_library: Dict[str, Dict] = {}  # problem_id -> {problem, structure, solution}

    def add_problem(self, problem_id: str, problem: str,
                   structure: Optional[ProblemStructure] = None,
                   solution: Optional[str] = None,
                   category: str = ""):
        """Add a problem to the library"""
        if structure is None:
            structure = self.structure_extractor.extract(problem, category)

        self.problem_library[problem_id] = {
            'problem': problem,
            'structure': structure,
            'solution': solution,
            'category': category
        }

    def find_analogies(self, target_problem: str,
                      target_category: str = "",
                      k: int = 5) -> List[Analogy]:
        """
        Find analogous problems from the library.

        Args:
            target_problem: The problem to find analogies for
            target_category: Optional category hint
            k: Number of analogies to return

        Returns:
            List of analogies sorted by similarity
        """
        # Extract target structure
        target_structure = self.structure_extractor.extract(target_problem, target_category)

        analogies = []

        for problem_id, data in self.problem_library.items():
            source_structure = data['structure']

            # Compute structural mapping
            entity_mapping, structural_score = self.structural_mapper.compute_mapping(
                source_structure, target_structure
            )

            # Compute semantic similarity
            semantic_score = self._compute_semantic_similarity(
                data['problem'], target_problem
            )

            # Combined similarity
            similarity = 0.6 * structural_score + 0.4 * semantic_score

            if similarity > 0.3:  # Threshold
                # Build relation mapping from entity mapping
                relation_mapping = self._build_relation_mapping(
                    source_structure, target_structure, entity_mapping
                )

                analogies.append(Analogy(
                    source_problem=data['problem'],
                    target_problem=target_problem,
                    source_structure=source_structure,
                    target_structure=target_structure,
                    entity_mapping=entity_mapping,
                    relation_mapping=relation_mapping,
                    similarity_score=similarity,
                    structural_match=structural_score,
                    semantic_match=semantic_score,
                    source_solution=data['solution']
                ))

        # Sort by similarity
        analogies.sort(key=lambda a: a.similarity_score, reverse=True)

        return analogies[:k]

    def _compute_semantic_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between texts"""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Remove stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                    'have', 'has', 'had', 'do', 'does', 'did', 'and', 'or', 'but',
                    'if', 'then', 'else', 'when', 'where', 'what', 'which', 'who',
                    'this', 'that', 'these', 'those', 'to', 'of', 'in', 'for', 'on'}
        words1 -= stopwords
        words2 -= stopwords

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _build_relation_mapping(self, source: ProblemStructure,
                               target: ProblemStructure,
                               entity_mapping: Dict[str, str]) -> Dict[Tuple[str, str], Tuple[str, str]]:
        """Build relation mapping from entity mapping"""
        relation_mapping = {}

        for s_rel in source.relations:
            # Map source relation to target
            if s_rel.source in entity_mapping and s_rel.target in entity_mapping:
                mapped_source = entity_mapping[s_rel.source]
                mapped_target = entity_mapping[s_rel.target]

                # Find matching target relation
                for t_rel in target.relations:
                    if (t_rel.source == mapped_source and
                        t_rel.target == mapped_target and
                        t_rel.relation_type == s_rel.relation_type):
                        relation_mapping[(s_rel.source, s_rel.target)] = (t_rel.source, t_rel.target)
                        break

        return relation_mapping


class SolutionTransfer:
    """
    Transfers solutions from source to target problems using analogies.
    """

    def __init__(self):
        pass

    def transfer(self, analogy: Analogy) -> Optional[str]:
        """
        Transfer solution from source to target problem.

        Args:
            analogy: The analogy to use for transfer

        Returns:
            Adapted solution for target problem
        """
        if not analogy.source_solution:
            return None

        # Adapt solution by replacing entity names
        adapted = analogy.source_solution

        for source_entity, target_entity in analogy.entity_mapping.items():
            # Replace entity references
            adapted = re.sub(
                rf'\b{re.escape(source_entity)}\b',
                target_entity,
                adapted,
                flags=re.IGNORECASE
            )

        # Add adaptation note
        adaptation_note = (
            f"\n[Adapted from analogous problem with "
            f"{analogy.similarity_score:.1%} structural similarity]"
        )

        return adapted + adaptation_note


class PatternExtractor:
    """
    Extracts abstract patterns from multiple similar problems.
    """

    def __init__(self):
        self.structure_extractor = StructureExtractor()
        self.structural_mapper = StructuralMapper()

    def extract_pattern(self, problems: List[Dict[str, Any]]) -> Optional[AbstractPattern]:
        """
        Extract abstract pattern from multiple similar problems.

        Args:
            problems: List of {problem, solution, structure, success}

        Returns:
            AbstractPattern if successful
        """
        if len(problems) < 2:
            return None

        # Find common structural elements
        structures = [p.get('structure') or
                     self.structure_extractor.extract(p['problem'])
                     for p in problems]

        # Find common entity types
        common_entity_types = self._find_common_entity_types(structures)

        # Find common relation patterns
        common_relation_patterns = self._find_common_relation_patterns(structures)

        # Build abstract structure
        abstract_structure = self._build_abstract_structure(
            common_entity_types, common_relation_patterns
        )

        # Extract solution template
        solution_template = self._extract_solution_template(problems)

        # Calculate success rate
        success_rate = sum(1 for p in problems if p.get('success', True)) / len(problems)

        # Collect domains
        domains = set(s.domain for s in structures if s.domain)

        # Generate pattern name
        name = self._generate_pattern_name(common_entity_types, common_relation_patterns)

        return AbstractPattern(
            name=name,
            description=f"Pattern with {len(common_entity_types)} entity types and {len(common_relation_patterns)} relation patterns",
            abstract_structure=abstract_structure,
            solution_template=solution_template,
            instances=[p.get('id', str(i)) for i, p in enumerate(problems)],
            success_rate=success_rate,
            domains=domains
        )

    def _find_common_entity_types(self, structures: List[ProblemStructure]) -> Dict[EntityType, int]:
        """Find entity types common across structures"""
        type_counts = defaultdict(int)

        for structure in structures:
            seen_types = set()
            for entity in structure.entities:
                if entity.entity_type not in seen_types:
                    type_counts[entity.entity_type] += 1
                    seen_types.add(entity.entity_type)

        # Keep types that appear in majority of problems
        threshold = len(structures) / 2
        return {t: c for t, c in type_counts.items() if c >= threshold}

    def _find_common_relation_patterns(self, structures: List[ProblemStructure]) -> Dict[RelationType, int]:
        """Find relation patterns common across structures"""
        pattern_counts = defaultdict(int)

        for structure in structures:
            seen_types = set()
            for relation in structure.relations:
                if relation.relation_type not in seen_types:
                    pattern_counts[relation.relation_type] += 1
                    seen_types.add(relation.relation_type)

        threshold = len(structures) / 2
        return {t: c for t, c in pattern_counts.items() if c >= threshold}

    def _build_abstract_structure(self, entity_types: Dict[EntityType, int],
                                  relation_patterns: Dict[RelationType, int]) -> ProblemStructure:
        """Build abstract structure from common elements"""
        entities = [
            Entity(name=f"${et.value}", entity_type=et, role="abstract")
            for et in entity_types.keys()
        ]

        relations = [
            Relation(source="$source", target="$target", relation_type=rt)
            for rt in relation_patterns.keys()
        ]

        return ProblemStructure(
            entities=entities,
            relations=relations,
            domain="abstract"
        )

    def _extract_solution_template(self, problems: List[Dict]) -> str:
        """Extract solution template from multiple solutions"""
        solutions = [p.get('solution', '') for p in problems if p.get('solution')]

        if not solutions:
            return "Apply analogous reasoning from similar problems"

        # Find common solution steps/patterns
        # Simple approach: use first successful solution as template
        for p in problems:
            if p.get('success', True) and p.get('solution'):
                return f"Template: {p['solution'][:200]}..."

        return solutions[0][:200] + "..."

    def _generate_pattern_name(self, entity_types: Dict, relation_patterns: Dict) -> str:
        """Generate descriptive name for pattern"""
        entity_str = '_'.join(sorted(et.value[:3] for et in entity_types.keys()))
        relation_str = '_'.join(sorted(rt.value[:3] for rt in relation_patterns.keys()))
        return f"Pattern_{entity_str}_{relation_str}"


class AnalogicalReasoner:
    """
    Main analogical reasoning engine.

    Combines structure extraction, analogy finding, solution transfer,
    and pattern learning.
    """

    def __init__(self):
        self.structure_extractor = StructureExtractor()
        self.analogy_finder = AnalogyFinder()
        self.solution_transfer = SolutionTransfer()
        self.pattern_extractor = PatternExtractor()

        # Pattern library
        self.patterns: Dict[str, AbstractPattern] = {}

        # Statistics
        self.stats = {
            'structures_extracted': 0,
            'analogies_found': 0,
            'solutions_transferred': 0,
            'patterns_extracted': 0
        }

    def extract_structure(self, problem: str, category: str = "") -> ProblemStructure:
        """Extract structure from a problem"""
        self.stats['structures_extracted'] += 1
        return self.structure_extractor.extract(problem, category)

    def find_analogies(self, problem: str, category: str = "", k: int = 5) -> List[Analogy]:
        """Find analogous problems"""
        analogies = self.analogy_finder.find_analogies(problem, category, k)
        self.stats['analogies_found'] += len(analogies)
        return analogies

    def transfer_solution(self, analogy: Analogy) -> Optional[str]:
        """Transfer solution using analogy"""
        solution = self.solution_transfer.transfer(analogy)
        if solution:
            self.stats['solutions_transferred'] += 1
        return solution

    def learn_pattern(self, problems: List[Dict]) -> Optional[AbstractPattern]:
        """Learn pattern from multiple problems"""
        pattern = self.pattern_extractor.extract_pattern(problems)
        if pattern:
            self.patterns[pattern.name] = pattern
            self.stats['patterns_extracted'] += 1
        return pattern

    def add_to_library(self, problem_id: str, problem: str,
                      solution: Optional[str] = None,
                      category: str = ""):
        """Add problem to analogy library"""
        structure = self.extract_structure(problem, category)
        self.analogy_finder.add_problem(problem_id, problem, structure, solution, category)

    def reason_by_analogy(self, problem: str, category: str = "") -> Dict[str, Any]:
        """
        Full analogical reasoning pipeline.

        Args:
            problem: The problem to solve
            category: Optional category hint

        Returns:
            Results including analogies, transferred solutions, applicable patterns
        """
        # Extract structure
        structure = self.extract_structure(problem, category)

        # Find analogies
        analogies = self.find_analogies(problem, category)

        # Try to transfer solutions
        transferred_solutions = []
        for analogy in analogies[:3]:  # Top 3 analogies
            solution = self.transfer_solution(analogy)
            if solution:
                transferred_solutions.append({
                    'solution': solution,
                    'similarity': analogy.similarity_score,
                    'source': analogy.source_problem[:100] + '...'
                })

        # Find applicable patterns
        applicable_patterns = self._find_applicable_patterns(structure)

        return {
            'structure': structure.to_dict(),
            'analogies': [
                {
                    'source': a.source_problem[:100] + '...',
                    'similarity': a.similarity_score,
                    'entity_mapping': a.entity_mapping
                }
                for a in analogies
            ],
            'transferred_solutions': transferred_solutions,
            'applicable_patterns': [p.to_dict() for p in applicable_patterns],
            'recommendation': self._generate_recommendation(
                analogies, transferred_solutions, applicable_patterns
            )
        }

    def _find_applicable_patterns(self, structure: ProblemStructure) -> List[AbstractPattern]:
        """Find patterns applicable to a problem structure"""
        applicable = []

        for pattern in self.patterns.values():
            # Check if structure matches pattern
            match_score = self._pattern_match_score(pattern, structure)
            if match_score > 0.5:
                applicable.append(pattern)

        return applicable

    def _pattern_match_score(self, pattern: AbstractPattern,
                            structure: ProblemStructure) -> float:
        """Calculate how well a pattern matches a structure"""
        pattern_entity_types = set(e.entity_type for e in pattern.abstract_structure.entities)
        structure_entity_types = set(e.entity_type for e in structure.entities)

        pattern_relation_types = set(r.relation_type for r in pattern.abstract_structure.relations)
        structure_relation_types = set(r.relation_type for r in structure.relations)

        entity_overlap = len(pattern_entity_types & structure_entity_types) / max(len(pattern_entity_types), 1)
        relation_overlap = len(pattern_relation_types & structure_relation_types) / max(len(pattern_relation_types), 1)

        return 0.5 * entity_overlap + 0.5 * relation_overlap

    def _generate_recommendation(self, analogies: List[Analogy],
                                transferred_solutions: List[Dict],
                                patterns: List[AbstractPattern]) -> str:
        """Generate recommendation based on analogical analysis"""
        if transferred_solutions:
            best = transferred_solutions[0]
            return f"Use transferred solution with {best['similarity']:.1%} confidence"
        elif analogies:
            return f"Consider {len(analogies)} analogous problems for guidance"
        elif patterns:
            return f"Apply pattern '{patterns[0].name}' with template solution"
        else:
            return "No strong analogies found; use direct reasoning"

    def get_stats(self) -> Dict[str, Any]:
        """Get reasoning statistics"""
        return {
            **self.stats,
            'library_size': len(self.analogy_finder.problem_library),
            'patterns_count': len(self.patterns)
        }


