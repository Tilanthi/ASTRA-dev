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
V50 Hierarchical Abstraction Learning
======================================

Learn concepts at multiple levels of abstraction and transfer across domains.

Levels:
1. Specific Instances - "Adding heat shifts equilibrium"
2. Domain Concepts - "Le Chatelier's Principle"
3. Cross-Domain Abstractions - "Chemical equilibrium ≈ Economic equilibrium"
4. Universal Patterns - "Conservation", "Equilibrium", "Feedback"

Key Capability: When encountering a novel problem, automatically find
the right level of abstraction and transfer knowledge from analogous domains.

Date: 2025-12-17
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
import random
import math
import time


class AbstractionLevel(Enum):
    """Levels of abstraction."""
    INSTANCE = 1  # Specific examples
    CONCEPT = 2   # Domain-specific concepts
    PATTERN = 3   # Cross-domain patterns
    UNIVERSAL = 4 # Universal principles


@dataclass
class Concept:
    """A concept at any abstraction level."""
    name: str
    level: AbstractionLevel
    description: str
    domain: str
    parent: Optional[str] = None  # Higher abstraction parent
    children: List[str] = field(default_factory=list)  # Lower abstraction children
    instances: List[str] = field(default_factory=list)  # Concrete instances
    related_concepts: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    usage_count: int = 0
    success_rate: float = 0.5


@dataclass
class Analogy:
    """An analogy between concepts."""
    source_concept: str
    target_concept: str
    source_domain: str
    target_domain: str
    mapping: Dict[str, str]  # Element mapping
    strength: float
    shared_structure: List[str]
    transferred_inferences: List[str]


@dataclass
class AbstractionResult:
    """Result of abstraction process."""
    original: str
    abstracted: str
    level: AbstractionLevel
    key_features: List[str]
    removed_details: List[str]
    confidence: float


@dataclass
class TransferResult:
    """Result of knowledge transfer."""
    source_domain: str
    target_domain: str
    analogy_used: Optional[Analogy]
    transferred_knowledge: List[str]
    adapted_solution: str
    confidence: float
    warnings: List[str]


class ConceptHierarchy:
    """
    Hierarchical organization of concepts.

    Organizes knowledge from specific to universal.
    """

    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
        self.hierarchy: Dict[AbstractionLevel, List[str]] = {
            level: [] for level in AbstractionLevel
        }
        self._initialize_base_hierarchy()

    def _initialize_base_hierarchy(self):
        """Initialize with foundational concepts."""
        # Universal principles (Level 4)
        universals = [
            Concept(
                name="conservation",
                level=AbstractionLevel.UNIVERSAL,
                description="Quantities that remain constant in closed systems",
                domain="universal",
                children=["energy_conservation", "mass_conservation", "momentum_conservation"],
                properties={"mathematical_form": "dX/dt = 0", "type": "invariant"}
            ),
            Concept(
                name="equilibrium",
                level=AbstractionLevel.UNIVERSAL,
                description="State where opposing forces/processes balance",
                domain="universal",
                children=["chemical_equilibrium", "mechanical_equilibrium", "economic_equilibrium"],
                properties={"mathematical_form": "F_net = 0", "type": "balance"}
            ),
            Concept(
                name="feedback",
                level=AbstractionLevel.UNIVERSAL,
                description="Output influences input",
                domain="universal",
                children=["negative_feedback", "positive_feedback"],
                properties={"types": ["positive", "negative"], "type": "control"}
            ),
            Concept(
                name="symmetry",
                level=AbstractionLevel.UNIVERSAL,
                description="Invariance under transformation",
                domain="universal",
                children=["rotational_symmetry", "translational_symmetry"],
                properties={"type": "invariance"}
            ),
            Concept(
                name="causality",
                level=AbstractionLevel.UNIVERSAL,
                description="Cause precedes and determines effect",
                domain="universal",
                properties={"type": "temporal_ordering"}
            )
        ]

        for concept in universals:
            self.add_concept(concept)

        # Cross-domain patterns (Level 3)
        patterns = [
            Concept(
                name="exponential_decay",
                level=AbstractionLevel.PATTERN,
                description="Quantity decreases proportionally to current value",
                domain="cross_domain",
                parent="conservation",
                instances=["radioactive_decay", "capacitor_discharge", "drug_metabolism"],
                properties={"equation": "dN/dt = -λN", "half_life": "t_1/2 = ln(2)/λ"}
            ),
            Concept(
                name="oscillation",
                level=AbstractionLevel.PATTERN,
                description="Periodic variation around equilibrium",
                domain="cross_domain",
                parent="equilibrium",
                instances=["pendulum", "LC_circuit", "population_cycles"],
                properties={"equation": "d²x/dt² = -ω²x", "period": "T = 2π/ω"}
            ),
            Concept(
                name="diffusion",
                level=AbstractionLevel.PATTERN,
                description="Spreading from high to low concentration",
                domain="cross_domain",
                instances=["heat_conduction", "molecular_diffusion", "information_spread"],
                properties={"equation": "∂c/∂t = D∇²c"}
            )
        ]

        for concept in patterns:
            self.add_concept(concept)

        # Domain-specific concepts (Level 2)
        domain_concepts = [
            # Physics
            Concept(
                name="energy_conservation",
                level=AbstractionLevel.CONCEPT,
                description="Total energy remains constant in isolated system",
                domain="Physics",
                parent="conservation",
                instances=["pendulum_energy", "collision_energy", "gravitational_potential"],
                properties={"forms": ["kinetic", "potential", "thermal"]}
            ),
            Concept(
                name="momentum_conservation",
                level=AbstractionLevel.CONCEPT,
                description="Total momentum constant without external forces",
                domain="Physics",
                parent="conservation",
                instances=["collision_momentum", "rocket_propulsion"],
                properties={"vector": True}
            ),
            Concept(
                name="mechanical_equilibrium",
                level=AbstractionLevel.CONCEPT,
                description="Net force and torque are zero",
                domain="Physics",
                parent="equilibrium",
                properties={"conditions": ["F_net = 0", "τ_net = 0"]}
            ),

            # Chemistry
            Concept(
                name="chemical_equilibrium",
                level=AbstractionLevel.CONCEPT,
                description="Forward and reverse reaction rates equal",
                domain="Chemistry",
                parent="equilibrium",
                instances=["le_chatelier", "buffer_systems"],
                properties={"K_eq": "K = [products]/[reactants]"}
            ),
            Concept(
                name="mass_conservation",
                level=AbstractionLevel.CONCEPT,
                description="Mass neither created nor destroyed in reactions",
                domain="Chemistry",
                parent="conservation",
                properties={"exception": "nuclear_reactions"}
            ),
            Concept(
                name="le_chatelier",
                level=AbstractionLevel.CONCEPT,
                description="System opposes changes to equilibrium",
                domain="Chemistry",
                parent="negative_feedback",
                instances=["temperature_change", "pressure_change", "concentration_change"]
            ),

            # Biology
            Concept(
                name="homeostasis",
                level=AbstractionLevel.CONCEPT,
                description="Maintaining stable internal conditions",
                domain="Biology",
                parent="negative_feedback",
                instances=["temperature_regulation", "blood_glucose", "pH_balance"],
                properties={"mechanism": "negative_feedback"}
            ),
            Concept(
                name="gene_regulation",
                level=AbstractionLevel.CONCEPT,
                description="Control of gene expression",
                domain="Biology",
                parent="feedback",
                instances=["lac_operon", "transcription_factors"],
                properties={"types": ["positive", "negative"]}
            ),
            Concept(
                name="natural_selection",
                level=AbstractionLevel.CONCEPT,
                description="Differential survival and reproduction",
                domain="Biology",
                instances=["antibiotic_resistance", "beak_adaptation"],
                properties={"mechanism": "variation + selection"}
            )
        ]

        for concept in domain_concepts:
            self.add_concept(concept)

    def add_concept(self, concept: Concept):
        """Add a concept to the hierarchy."""
        self.concepts[concept.name] = concept
        self.hierarchy[concept.level].append(concept.name)

    def get_concept(self, name: str) -> Optional[Concept]:
        """Get concept by name."""
        return self.concepts.get(name)

    def get_parent(self, concept_name: str) -> Optional[Concept]:
        """Get parent concept."""
        concept = self.concepts.get(concept_name)
        if concept and concept.parent:
            return self.concepts.get(concept.parent)
        return None

    def get_children(self, concept_name: str) -> List[Concept]:
        """Get child concepts."""
        concept = self.concepts.get(concept_name)
        if concept:
            return [self.concepts[c] for c in concept.children if c in self.concepts]
        return []

    def get_at_level(self, level: AbstractionLevel) -> List[Concept]:
        """Get all concepts at a level."""
        return [self.concepts[name] for name in self.hierarchy[level]
                if name in self.concepts]

    def find_common_ancestor(self, concept1: str, concept2: str) -> Optional[Concept]:
        """Find lowest common ancestor of two concepts."""
        ancestors1 = self._get_ancestors(concept1)
        ancestors2 = self._get_ancestors(concept2)

        # Find intersection
        common = ancestors1 & ancestors2

        if not common:
            return None

        # Return lowest (most specific) common ancestor
        for level in [AbstractionLevel.PATTERN, AbstractionLevel.UNIVERSAL]:
            for ancestor in common:
                concept = self.concepts.get(ancestor)
                if concept and concept.level == level:
                    return concept

        return None

    def _get_ancestors(self, concept_name: str) -> Set[str]:
        """Get all ancestors of a concept."""
        ancestors = set()
        current = concept_name

        while current:
            concept = self.concepts.get(current)
            if concept and concept.parent:
                ancestors.add(concept.parent)
                current = concept.parent
            else:
                break

        return ancestors

    def get_related_by_domain(self, concept_name: str) -> List[Concept]:
        """Get concepts in same domain."""
        concept = self.concepts.get(concept_name)
        if not concept:
            return []

        return [c for c in self.concepts.values()
                if c.domain == concept.domain and c.name != concept_name]


class AbstractionEngine:
    """
    Engine for abstracting specific instances to general patterns.
    """

    def __init__(self, hierarchy: ConceptHierarchy = None):
        self.hierarchy = hierarchy or ConceptHierarchy()

    def abstract(self, instance: str, domain: str,
                 target_level: AbstractionLevel = AbstractionLevel.PATTERN) -> AbstractionResult:
        """
        Abstract a specific instance to a higher level.

        Args:
            instance: Specific instance description
            domain: Domain of the instance
            target_level: Target abstraction level

        Returns:
            AbstractionResult with abstracted concept
        """
        # Extract key features
        key_features = self._extract_key_features(instance, domain)

        # Find matching concept
        matching_concept = self._find_matching_concept(key_features, domain, target_level)

        # Generate abstraction
        if matching_concept:
            abstracted = matching_concept.name
            confidence = 0.8
        else:
            # Create new abstraction
            abstracted = self._create_abstraction(key_features, target_level)
            confidence = 0.6

        # Identify removed details
        removed = self._identify_removed_details(instance, key_features)

        return AbstractionResult(
            original=instance,
            abstracted=abstracted,
            level=target_level,
            key_features=key_features,
            removed_details=removed,
            confidence=confidence
        )

    def _extract_key_features(self, instance: str, domain: str) -> List[str]:
        """Extract key features from instance."""
        features = []
        instance_lower = instance.lower()

        # Domain-agnostic features
        if any(kw in instance_lower for kw in ['constant', 'conserved', 'unchanged']):
            features.append('conservation')
        if any(kw in instance_lower for kw in ['balance', 'equilibrium', 'stable']):
            features.append('equilibrium')
        if any(kw in instance_lower for kw in ['cycle', 'oscillate', 'periodic']):
            features.append('oscillation')
        if any(kw in instance_lower for kw in ['decay', 'decrease', 'diminish']):
            features.append('decay')
        if any(kw in instance_lower for kw in ['feedback', 'regulate', 'control']):
            features.append('feedback')
        if any(kw in instance_lower for kw in ['spread', 'diffuse', 'distribute']):
            features.append('diffusion')

        # Domain-specific features
        if domain == 'Physics':
            if 'energy' in instance_lower:
                features.append('energy')
            if 'momentum' in instance_lower:
                features.append('momentum')
            if 'force' in instance_lower:
                features.append('force')
        elif domain == 'Chemistry':
            if 'reaction' in instance_lower:
                features.append('reaction')
            if 'concentration' in instance_lower:
                features.append('concentration')
            if 'rate' in instance_lower:
                features.append('kinetics')
        elif domain == 'Biology':
            if 'gene' in instance_lower or 'expression' in instance_lower:
                features.append('gene_regulation')
            if 'enzyme' in instance_lower:
                features.append('catalysis')
            if 'cell' in instance_lower:
                features.append('cellular')

        return features

    def _find_matching_concept(self, features: List[str], domain: str,
                                target_level: AbstractionLevel) -> Optional[Concept]:
        """Find concept matching features at target level."""
        candidates = self.hierarchy.get_at_level(target_level)

        best_match = None
        best_score = 0

        for concept in candidates:
            score = 0

            # Match by name
            for feature in features:
                if feature in concept.name.lower():
                    score += 2
                if feature in concept.description.lower():
                    score += 1

            # Match by properties
            for prop in concept.properties.values():
                if isinstance(prop, str):
                    for feature in features:
                        if feature in prop.lower():
                            score += 1

            # Domain match bonus
            if concept.domain == domain or concept.domain in ['universal', 'cross_domain']:
                score += 1

            if score > best_score:
                best_score = score
                best_match = concept

        return best_match if best_score >= 2 else None

    def _create_abstraction(self, features: List[str],
                             level: AbstractionLevel) -> str:
        """Create new abstraction from features."""
        if not features:
            return "general_process"

        # Combine features
        if len(features) == 1:
            return f"{features[0]}_pattern"
        else:
            return f"{features[0]}_{features[1]}_interaction"

    def _identify_removed_details(self, instance: str,
                                    kept_features: List[str]) -> List[str]:
        """Identify details removed during abstraction."""
        removed = []
        instance_lower = instance.lower()

        # Numbers are typically removed
        import re
        numbers = re.findall(r'\d+\.?\d*', instance)
        removed.extend([f"value: {n}" for n in numbers])

        # Specific entities
        if 'the ' in instance_lower:
            # Specific references
            removed.append("specific entity references")

        # Time references
        if any(kw in instance_lower for kw in ['when', 'after', 'before', 'during']):
            removed.append("temporal specifics")

        return removed

    def specialize(self, concept_name: str, domain: str) -> List[str]:
        """Specialize a concept to domain-specific instances."""
        concept = self.hierarchy.get_concept(concept_name)
        if not concept:
            return []

        instances = []

        # Get existing instances
        instances.extend(concept.instances)

        # Get instances from children
        for child in concept.children:
            child_concept = self.hierarchy.get_concept(child)
            if child_concept:
                instances.extend(child_concept.instances)

        # Filter by domain
        if domain:
            domain_concepts = self.hierarchy.get_related_by_domain(concept_name)
            for dc in domain_concepts:
                instances.extend(dc.instances)

        return list(set(instances))


class AnalogyFinder:
    """
    Find analogies between domains for knowledge transfer.
    """

    def __init__(self, hierarchy: ConceptHierarchy = None):
        self.hierarchy = hierarchy or ConceptHierarchy()
        self.known_analogies: List[Analogy] = []
        self._initialize_base_analogies()

    def _initialize_base_analogies(self):
        """Initialize known cross-domain analogies."""
        self.known_analogies = [
            Analogy(
                source_concept="mechanical_equilibrium",
                target_concept="chemical_equilibrium",
                source_domain="Physics",
                target_domain="Chemistry",
                mapping={
                    "force": "concentration gradient",
                    "position": "reaction progress",
                    "potential_energy": "gibbs_energy"
                },
                strength=0.85,
                shared_structure=["balance", "minimum_energy", "stability"],
                transferred_inferences=[
                    "Perturbations cause restoring response",
                    "System settles at energy minimum"
                ]
            ),
            Analogy(
                source_concept="electrical_circuit",
                target_concept="fluid_flow",
                source_domain="Physics",
                target_domain="Physics",
                mapping={
                    "voltage": "pressure",
                    "current": "flow_rate",
                    "resistance": "fluid_resistance"
                },
                strength=0.90,
                shared_structure=["Ohm's law analog", "conservation"],
                transferred_inferences=[
                    "V=IR ≈ ΔP=QR",
                    "Series/parallel rules apply"
                ]
            ),
            Analogy(
                source_concept="population_dynamics",
                target_concept="chemical_kinetics",
                source_domain="Biology",
                target_domain="Chemistry",
                mapping={
                    "population": "concentration",
                    "birth_rate": "forward_rate",
                    "death_rate": "reverse_rate",
                    "carrying_capacity": "equilibrium_concentration"
                },
                strength=0.75,
                shared_structure=["exponential_growth", "equilibrium", "rate_equations"],
                transferred_inferences=[
                    "Logistic growth ≈ equilibrium approach",
                    "Rate depends on current amount"
                ]
            ),
            Analogy(
                source_concept="gene_regulation",
                target_concept="market_regulation",
                source_domain="Biology",
                target_domain="Economics",
                mapping={
                    "transcription_factor": "regulator",
                    "gene_expression": "production",
                    "feedback_inhibition": "price_feedback"
                },
                strength=0.65,
                shared_structure=["negative_feedback", "threshold_effects"],
                transferred_inferences=[
                    "Feedback maintains homeostasis/stability",
                    "Multiple regulators can combine"
                ]
            ),
            Analogy(
                source_concept="diffusion",
                target_concept="heat_conduction",
                source_domain="Chemistry",
                target_domain="Physics",
                mapping={
                    "concentration": "temperature",
                    "diffusion_coefficient": "thermal_diffusivity",
                    "flux": "heat_flux"
                },
                strength=0.95,
                shared_structure=["Fick's_law_analog", "gradient_driven", "diffusion_equation"],
                transferred_inferences=[
                    "Same mathematical form",
                    "Steady-state = linear gradient"
                ]
            )
        ]

    def find_analogy(self, source_concept: str, source_domain: str,
                     target_domain: str) -> Optional[Analogy]:
        """
        Find analogy from source concept to target domain.

        Args:
            source_concept: Source concept name
            source_domain: Source domain
            target_domain: Target domain for transfer

        Returns:
            Best matching analogy if found
        """
        # Search known analogies
        for analogy in self.known_analogies:
            if analogy.source_domain == source_domain:
                if analogy.target_domain == target_domain:
                    if source_concept in analogy.source_concept or \
                       source_concept in analogy.mapping:
                        return analogy

        # Try to construct new analogy
        return self._construct_analogy(source_concept, source_domain, target_domain)

    def _construct_analogy(self, source_concept: str, source_domain: str,
                           target_domain: str) -> Optional[Analogy]:
        """Construct new analogy through common ancestor."""
        # Find common ancestor
        source = self.hierarchy.get_concept(source_concept)
        if not source:
            return None

        # Find target domain concepts
        target_concepts = [c for c in self.hierarchy.concepts.values()
                         if c.domain == target_domain]

        # Find best structural match
        best_match = None
        best_score = 0

        for target in target_concepts:
            # Check for common ancestor
            ancestor = self.hierarchy.find_common_ancestor(source_concept, target.name)
            if ancestor:
                # Score based on shared properties
                score = self._compute_structural_similarity(source, target)
                if score > best_score:
                    best_score = score
                    best_match = target

        if best_match and best_score > 0.5:
            return Analogy(
                source_concept=source_concept,
                target_concept=best_match.name,
                source_domain=source_domain,
                target_domain=target_domain,
                mapping=self._generate_mapping(source, best_match),
                strength=best_score,
                shared_structure=self._find_shared_structure(source, best_match),
                transferred_inferences=[]
            )

        return None

    def _compute_structural_similarity(self, source: Concept,
                                        target: Concept) -> float:
        """Compute structural similarity between concepts."""
        score = 0.0

        # Same level
        if source.level == target.level:
            score += 0.2

        # Same parent
        if source.parent and source.parent == target.parent:
            score += 0.3

        # Property overlap
        source_props = set(source.properties.keys())
        target_props = set(target.properties.keys())
        if source_props and target_props:
            overlap = len(source_props & target_props)
            total = len(source_props | target_props)
            score += 0.3 * (overlap / total)

        # Related concepts overlap
        source_related = set(source.related_concepts)
        target_related = set(target.related_concepts)
        if source_related and target_related:
            overlap = len(source_related & target_related)
            total = len(source_related | target_related)
            score += 0.2 * (overlap / total)

        return min(1.0, score)

    def _generate_mapping(self, source: Concept, target: Concept) -> Dict[str, str]:
        """Generate element mapping between concepts."""
        mapping = {}

        # Map by property names
        for s_prop in source.properties:
            for t_prop in target.properties:
                if self._are_analogous_properties(s_prop, t_prop):
                    mapping[s_prop] = t_prop

        return mapping

    def _are_analogous_properties(self, prop1: str, prop2: str) -> bool:
        """Check if properties are analogous."""
        # Simple similarity check
        p1_words = set(prop1.lower().split('_'))
        p2_words = set(prop2.lower().split('_'))
        return len(p1_words & p2_words) > 0

    def _find_shared_structure(self, source: Concept, target: Concept) -> List[str]:
        """Find shared structural elements."""
        shared = []

        # Check parent chain
        if source.parent and source.parent == target.parent:
            parent = self.hierarchy.get_concept(source.parent)
            if parent:
                shared.append(f"common_parent: {parent.name}")

        # Check property types
        for prop in source.properties:
            if prop in target.properties:
                shared.append(f"shared_property: {prop}")

        return shared


class KnowledgeTransferEngine:
    """
    Transfer knowledge between domains using analogies.
    """

    def __init__(self, hierarchy: ConceptHierarchy = None,
                 analogy_finder: AnalogyFinder = None):
        self.hierarchy = hierarchy or ConceptHierarchy()
        self.analogy_finder = analogy_finder or AnalogyFinder(self.hierarchy)
        self.transfer_history: List[TransferResult] = []

    def transfer(self, problem: str, source_domain: str,
                 target_domain: str,
                 solution_hint: str = "") -> TransferResult:
        """
        Transfer solution approach from source to target domain.

        Args:
            problem: Problem description
            source_domain: Domain where solution is known
            target_domain: Domain where problem exists
            solution_hint: Optional hint about source solution

        Returns:
            TransferResult with adapted solution
        """
        # Extract key concepts from problem
        concepts = self._extract_concepts(problem, target_domain)

        # Find relevant analogy
        best_analogy = None
        for concept in concepts:
            analogy = self.analogy_finder.find_analogy(
                concept, source_domain, target_domain
            )
            if analogy and (not best_analogy or analogy.strength > best_analogy.strength):
                best_analogy = analogy

        # Transfer knowledge
        if best_analogy:
            transferred = self._apply_analogy(problem, best_analogy, solution_hint)
            warnings = self._check_transfer_validity(best_analogy, problem)
        else:
            transferred = ["No direct analogy found - using abstract pattern matching"]
            warnings = ["Transfer without direct analogy may be unreliable"]

            # Try pattern-based transfer
            pattern_transfer = self._pattern_based_transfer(problem, source_domain, target_domain)
            transferred.extend(pattern_transfer)

        # Generate adapted solution
        adapted = self._generate_adapted_solution(problem, transferred, target_domain)

        result = TransferResult(
            source_domain=source_domain,
            target_domain=target_domain,
            analogy_used=best_analogy,
            transferred_knowledge=transferred,
            adapted_solution=adapted,
            confidence=best_analogy.strength if best_analogy else 0.4,
            warnings=warnings
        )

        self.transfer_history.append(result)
        return result

    def _extract_concepts(self, problem: str, domain: str) -> List[str]:
        """Extract relevant concepts from problem."""
        concepts = []
        problem_lower = problem.lower()

        # Search hierarchy for matching concepts
        for name, concept in self.hierarchy.concepts.items():
            # Check if concept name appears
            if name.lower().replace('_', ' ') in problem_lower:
                concepts.append(name)
                continue

            # Check if description keywords appear
            desc_words = concept.description.lower().split()
            matches = sum(1 for w in desc_words if len(w) > 4 and w in problem_lower)
            if matches >= 2:
                concepts.append(name)

        return concepts

    def _apply_analogy(self, problem: str, analogy: Analogy,
                       solution_hint: str) -> List[str]:
        """Apply analogy to transfer knowledge."""
        transferred = []

        # Add mapping-based transfers
        for source_elem, target_elem in analogy.mapping.items():
            transferred.append(f"Map {source_elem} → {target_elem}")

        # Add structural inferences
        transferred.extend(analogy.transferred_inferences)

        # Add shared structure insights
        for struct in analogy.shared_structure:
            transferred.append(f"Shared structure: {struct}")

        return transferred

    def _check_transfer_validity(self, analogy: Analogy, problem: str) -> List[str]:
        """Check validity of transfer."""
        warnings = []

        # Strength warning
        if analogy.strength < 0.7:
            warnings.append(f"Analogy strength is moderate ({analogy.strength:.2f})")

        # Domain-specific warnings
        if analogy.target_domain == 'Chemistry' and 'quantum' in problem.lower():
            warnings.append("Quantum effects may not transfer from classical analogy")

        if analogy.target_domain == 'Biology' and 'evolution' in problem.lower():
            warnings.append("Evolutionary processes have unique properties")

        return warnings

    def _pattern_based_transfer(self, problem: str, source: str,
                                 target: str) -> List[str]:
        """Transfer based on abstract patterns."""
        transfers = []

        # Find universal patterns
        universals = self.hierarchy.get_at_level(AbstractionLevel.UNIVERSAL)

        for pattern in universals:
            if pattern.name.lower() in problem.lower():
                transfers.append(
                    f"Universal pattern '{pattern.name}' applies: {pattern.description}"
                )

        return transfers

    def _generate_adapted_solution(self, problem: str,
                                    transferred: List[str],
                                    domain: str) -> str:
        """Generate adapted solution from transferred knowledge."""
        if not transferred:
            return "Insufficient knowledge for solution adaptation"

        solution_parts = []

        solution_parts.append(f"Applying transferred knowledge to {domain} problem:")

        for i, knowledge in enumerate(transferred[:5], 1):
            solution_parts.append(f"  {i}. {knowledge}")

        solution_parts.append("\nAdapted approach:")
        solution_parts.append("  - Apply domain-specific constraints")
        solution_parts.append("  - Verify transferred inferences hold")
        solution_parts.append("  - Adjust for domain-specific effects")

        return "\n".join(solution_parts)


class HierarchicalAbstractionLearner:
    """
    Main interface for hierarchical abstraction learning.

    Combines hierarchy, abstraction, analogy, and transfer.
    """

    def __init__(self):
        self.hierarchy = ConceptHierarchy()
        self.abstraction_engine = AbstractionEngine(self.hierarchy)
        self.analogy_finder = AnalogyFinder(self.hierarchy)
        self.transfer_engine = KnowledgeTransferEngine(self.hierarchy, self.analogy_finder)

    def learn_from_instance(self, instance: str, domain: str,
                             correct: bool = True) -> Dict[str, Any]:
        """
        Learn from a specific instance.

        Args:
            instance: Instance description
            domain: Domain of instance
            correct: Whether instance was handled correctly

        Returns:
            Learning outcomes
        """
        # Abstract to patterns
        abstraction = self.abstraction_engine.abstract(instance, domain)

        # Update concept usage
        if abstraction.abstracted in self.hierarchy.concepts:
            concept = self.hierarchy.concepts[abstraction.abstracted]
            concept.usage_count += 1
            if correct:
                concept.success_rate = concept.success_rate * 0.9 + 0.1
            else:
                concept.success_rate = concept.success_rate * 0.9

        return {
            'instance': instance,
            'abstracted_to': abstraction.abstracted,
            'level': abstraction.level.name,
            'key_features': abstraction.key_features,
            'confidence': abstraction.confidence
        }

    def reason_with_abstraction(self, question: str, domain: str,
                                 choices: List[str]) -> Dict[str, Any]:
        """
        Reason about a question using abstraction hierarchy.

        Args:
            question: Question to answer
            domain: Domain hint
            choices: Answer choices

        Returns:
            Answer with abstraction-based reasoning
        """
        # Extract concepts from question
        question_concepts = self._extract_question_concepts(question, domain)

        # Find applicable patterns
        patterns = self._find_applicable_patterns(question_concepts)

        # Score choices based on patterns
        scored_choices = self._score_choices_with_patterns(
            choices, patterns, question, domain
        )

        # Find best choice
        best_idx = max(range(len(scored_choices)),
                       key=lambda i: scored_choices[i]['score'])

        # Generate reasoning trace
        trace = self._generate_reasoning_trace(
            question_concepts, patterns, scored_choices
        )

        return {
            'answer': choices[best_idx] if choices else "",
            'answer_index': best_idx,
            'confidence': scored_choices[best_idx]['score'] if scored_choices else 0.5,
            'concepts_identified': question_concepts,
            'patterns_applied': [p.name for p in patterns],
            'reasoning_trace': trace
        }

    def transfer_knowledge(self, question: str, source_domain: str,
                           target_domain: str,
                           choices: List[str]) -> Dict[str, Any]:
        """
        Answer using cross-domain knowledge transfer.

        Args:
            question: Question in target domain
            source_domain: Domain to transfer from
            target_domain: Domain of question
            choices: Answer choices

        Returns:
            Answer with transfer reasoning
        """
        # Perform transfer
        transfer_result = self.transfer_engine.transfer(
            question, source_domain, target_domain
        )

        # Use transferred knowledge to score choices
        scored = []
        for i, choice in enumerate(choices):
            score = self._score_with_transfer(choice, transfer_result)
            scored.append((i, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        best_idx, best_score = scored[0] if scored else (0, 0.5)

        return {
            'answer': choices[best_idx] if choices else "",
            'answer_index': best_idx,
            'confidence': min(0.95, best_score * transfer_result.confidence),
            'analogy_used': transfer_result.analogy_used.source_concept if transfer_result.analogy_used else None,
            'transferred_knowledge': transfer_result.transferred_knowledge,
            'warnings': transfer_result.warnings
        }

    def _extract_question_concepts(self, question: str, domain: str) -> List[str]:
        """Extract concepts from question."""
        concepts = []
        q_lower = question.lower()

        for name, concept in self.hierarchy.concepts.items():
            # Direct match
            name_normalized = name.replace('_', ' ')
            if name_normalized in q_lower:
                concepts.append(name)
                continue

            # Description match
            if concept.domain == domain or concept.domain in ['universal', 'cross_domain']:
                keywords = [w for w in concept.description.lower().split() if len(w) > 4]
                matches = sum(1 for kw in keywords if kw in q_lower)
                if matches >= 2:
                    concepts.append(name)

        return concepts

    def _find_applicable_patterns(self, concepts: List[str]) -> List[Concept]:
        """Find patterns applicable to concepts."""
        patterns = []

        for concept_name in concepts:
            concept = self.hierarchy.get_concept(concept_name)
            if not concept:
                continue

            # Get parent patterns
            parent = self.hierarchy.get_parent(concept_name)
            while parent:
                if parent.level in [AbstractionLevel.PATTERN, AbstractionLevel.UNIVERSAL]:
                    if parent not in patterns:
                        patterns.append(parent)
                parent = self.hierarchy.get_parent(parent.name)

        return patterns

    def _score_choices_with_patterns(self, choices: List[str],
                                      patterns: List[Concept],
                                      question: str, domain: str) -> List[Dict]:
        """Score choices using identified patterns."""
        scored = []

        for choice in choices:
            choice_lower = choice.lower()
            score = 0.5

            # Pattern consistency
            for pattern in patterns:
                # Check if choice is consistent with pattern
                if self._is_consistent_with_pattern(choice_lower, pattern):
                    score += 0.1 * pattern.success_rate

                # Check for pattern violations
                if self._violates_pattern(choice_lower, pattern):
                    score -= 0.15

            # Domain keyword bonus
            domain_concepts = [c for c in self.hierarchy.concepts.values()
                              if c.domain == domain]
            for concept in domain_concepts:
                if concept.name.replace('_', ' ') in choice_lower:
                    score += 0.05

            scored.append({
                'choice': choice,
                'score': max(0.1, min(0.95, score)),
                'pattern_matches': len([p for p in patterns
                                       if self._is_consistent_with_pattern(choice_lower, p)])
            })

        return scored

    def _is_consistent_with_pattern(self, choice: str, pattern: Concept) -> bool:
        """Check if choice is consistent with pattern."""
        # Check properties
        for prop_name, prop_value in pattern.properties.items():
            if isinstance(prop_value, str):
                if prop_value.lower() in choice:
                    return True

        # Check description keywords
        desc_keywords = [w for w in pattern.description.lower().split() if len(w) > 4]
        matches = sum(1 for kw in desc_keywords if kw in choice)
        return matches >= 1

    def _violates_pattern(self, choice: str, pattern: Concept) -> bool:
        """Check if choice violates pattern."""
        # Conservation violation
        if pattern.name == 'conservation':
            if any(kw in choice for kw in ['created', 'destroyed', 'appears', 'disappears']):
                return True

        # Equilibrium violation
        if pattern.name == 'equilibrium':
            if 'never reaches' in choice or 'infinite' in choice:
                return True

        return False

    def _generate_reasoning_trace(self, concepts: List[str],
                                   patterns: List[Concept],
                                   scored: List[Dict]) -> List[str]:
        """Generate reasoning trace."""
        trace = []

        if concepts:
            trace.append(f"Identified concepts: {', '.join(concepts)}")

        if patterns:
            trace.append(f"Applied patterns: {', '.join(p.name for p in patterns)}")

        for i, s in enumerate(scored):
            trace.append(f"Choice {i}: score={s['score']:.2f}, pattern_matches={s['pattern_matches']}")

        return trace

    def _score_with_transfer(self, choice: str, transfer: TransferResult) -> float:
        """Score choice using transferred knowledge."""
        score = 0.5

        # Check consistency with transferred inferences
        choice_lower = choice.lower()
        for knowledge in transfer.transferred_knowledge:
            # Simple keyword matching
            knowledge_keywords = [w for w in knowledge.lower().split() if len(w) > 4]
            matches = sum(1 for kw in knowledge_keywords if kw in choice_lower)
            score += 0.02 * matches

        return min(0.95, score)

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            'concepts': len(self.hierarchy.concepts),
            'by_level': {
                level.name: len(concepts)
                for level, concepts in self.hierarchy.hierarchy.items()
            },
            'known_analogies': len(self.analogy_finder.known_analogies),
            'transfers_performed': len(self.transfer_engine.transfer_history)
        }


# Factory functions
def create_abstraction_learner() -> HierarchicalAbstractionLearner:
    """Create a hierarchical abstraction learner."""
    return HierarchicalAbstractionLearner()


def create_concept_hierarchy() -> ConceptHierarchy:
    """Create a concept hierarchy."""
    return ConceptHierarchy()


def create_analogy_finder() -> AnalogyFinder:
    """Create an analogy finder."""
    return AnalogyFinder()


def create_transfer_engine() -> KnowledgeTransferEngine:
    """Create a knowledge transfer engine."""
    return KnowledgeTransferEngine()
