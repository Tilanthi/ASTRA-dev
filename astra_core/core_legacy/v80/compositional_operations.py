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
Compositional Operations for Grounded Concepts
============================================

This module implements the core operations that enable compositional
reasoning with grounded concepts, providing the foundation for
creative problem-solving and generative understanding.

Key Operations:
- Compose: Merge concepts while preserving structure
- Transform: Apply action concepts to object concepts
- Compare: Multi-modal similarity assessment
- Abstract: Create hierarchical abstractions
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from enum import Enum
import numpy.typing as npt

from .grounded_concept import GroundedConcept, MultiModalGrounding, ConceptSpace


class CompositionType(Enum):
    """Types of composition operations"""
    MERGE = "merge"  # Combine two concepts
    TRANSFORM = "transform"  # Apply action to object
    ABSTRACT = "abstract"  # Create abstraction
    SPECIALIZE = "specialize"  # Create specialization
    RELATE = "relate"  # Create relational concept


@dataclass
class CompositionRule:
    """Rule for how concepts can be composed"""
    input_types: Tuple[str, str]
    output_type: str
    operation: Callable
    constraints: Dict[str, Any]


class Compose:
    """Composition operations for grounded concepts"""

    def __init__(self, concept_space: ConceptSpace):
        self.concept_space = concept_space
        self.composition_rules = self._initialize_rules()
        self.composition_cache = {}

    def _initialize_rules(self) -> Dict[CompositionType, List[CompositionRule]]:
        """Initialize composition rules based on concept types"""
        rules = {
            CompositionType.MERGE: [
                CompositionRule(
                    input_types=("object", "property"),
                    output_type="object",
                    operation=self._merge_object_property,
                    constraints={"preserve_object_structure": True}
                ),
                CompositionRule(
                    input_types=("object", "object"),
                    output_type="composite_object",
                    operation=self._merge_objects,
                    constraints={"spatial_consistency": True}
                ),
                CompositionRule(
                    input_types=("action", "object"),
                    output_type="action_sequence",
                    operation=self._merge_action_object,
                    constraints={"action_applicability": True}
                )
            ],
            CompositionType.TRANSFORM: [
                CompositionRule(
                    input_types=("action", "object"),
                    output_type="transformed_object",
                    operation=self._apply_action,
                    constraints={"action_compatibility": True}
                ),
                CompositionRule(
                    input_types=("process", "object"),
                    output_type="processed_object",
                    operation=self._apply_process,
                    constraints={"process_applicability": True}
                )
            ],
            CompositionType.ABSTRACT: [
                CompositionRule(
                    input_types=("object", "object"),
                    output_type="abstract_property",
                    operation=self._extract_commonality,
                    constraints={"min_similarity": 0.7}
                ),
                CompositionRule(
                    input_types=("action", "action"),
                    output_type="abstract_action",
                    operation=self._abstract_action,
                    constraints={"structural_similarity": True}
                )
            ]
        }
        return rules

    def compose(self, concept1: GroundedConcept,
                concept2: GroundedConcept,
                composition_type: CompositionType = CompositionType.MERGE) -> Optional[GroundedConcept]:
        """
        Compose two concepts according to specified type
        """
        # Check cache first
        cache_key = (concept1.name, concept2.name, composition_type.value)
        if cache_key in self.composition_cache:
            return self.composition_cache[cache_key]

        # Determine concept types
        type1 = self._infer_concept_type(concept1)
        type2 = self._infer_concept_type(concept2)

        # Find applicable rule
        applicable_rules = [
            rule for rule in self.composition_rules.get(composition_type, [])
            if (type1, type2) == rule.input_types or (type2, type1) == rule.input_types
        ]

        if not applicable_rules:
            # Try general composition
            result = self._general_composition(concept1, concept2, composition_type)
        else:
            # Apply first applicable rule
            rule = applicable_rules[0]
            if self._check_constraints(concept1, concept2, rule.constraints):
                result = rule.operation(concept1, concept2)
            else:
                result = None

        # Cache result
        if result:
            self.composition_cache[cache_key] = result

        return result

    def _infer_concept_type(self, concept: GroundedConcept) -> str:
        """Infer concept type from its grounding"""
        # Check motor patterns for actions
        if concept.grounding.motor:
            return "action"

        # Check causal patterns for processes
        if len(concept.grounding.causal.sequence_structure) > 1:
            return "process"

        # Check mathematical structure
        if "property" in concept.grounding.mathematical.type_hierarchy:
            return "property"

        # Default to object
        return "object"

    def _check_constraints(self, concept1: GroundedConcept,
                          concept2: GroundedConcept,
                          constraints: Dict[str, Any]) -> bool:
        """Check if composition constraints are satisfied"""
        if "min_similarity" in constraints:
            similarity = concept1.compare(concept2)
            if similarity < constraints["min_similarity"]:
                return False

        if "action_applicability" in constraints:
            # Check if action can be applied to object
            action_concept = concept1 if self._infer_concept_type(concept1) == "action" else concept2
            object_concept = concept2 if self._infer_concept_type(concept2) == "object" else concept1
            return self._can_act_on(action_concept, object_concept)

        # Add more constraint checks as needed
        return True

    def _can_act_on(self, action: GroundedConcept, obj: GroundedConcept) -> bool:
        """Check if action can be applied to object"""
        # Simplified check - in practice would be more sophisticated
        if not action.grounding.motor:
            return False

        # Check object has relevant properties for action
        object_properties = set(obj.grounding.linguistic.keys())
        action_requirements = set(action.grounding.linguistic.keys())

        return bool(object_properties & action_requirements)

    def _merge_object_property(self, obj: GroundedConcept,
                              prop: GroundedConcept) -> GroundedConcept:
        """Merge property into object"""
        # Create new grounded representation
        new_grounding = MultiModalGrounding(
            perceptual=obj.grounding.perceptual * 0.7 + prop.grounding.perceptual * 0.3,
            motor=obj.grounding.motor,
            linguistic={**obj.grounding.linguistic, **prop.grounding.linguistic},
            mathematical=obj.grounding.mathematical,
            causal=obj.grounding.causal,
            affective=obj.grounding.affective + prop.grounding.affective * 0.2
        )

        new_concept = GroundedConcept(f"{prop.name}_{obj.name}", new_grounding)
        new_concept.composition_history = [
            ('compose', obj.name, prop.name, 'merge_object_property')
        ]

        return new_concept

    def _merge_objects(self, obj1: GroundedConcept,
                      obj2: GroundedConcept) -> GroundedConcept:
        """Merge two objects"""
        new_grounding = MultiModalGrounding(
            perceptual=(obj1.grounding.perceptual + obj2.grounding.perceptual) / 2,
            motor=obj1.grounding.motor + obj2.grounding.motor,
            linguistic={**obj1.grounding.linguistic, **obj2.grounding.linguistic},
            mathematical=self._merge_mathematical(
                obj1.grounding.mathematical,
                obj2.grounding.mathematical
            ),
            causal=self._merge_causal(
                obj1.grounding.causal,
                obj2.grounding.causal
            ),
            affective=(obj1.grounding.affective + obj2.grounding.affective) / 2
        )

        new_concept = GroundedConcept(f"{obj1.name}+{obj2.name}", new_grounding)
        new_concept.composition_history = [
            ('compose', obj1.name, obj2.name, 'merge_objects')
        ]

        return new_concept

    def _merge_action_object(self, action: GroundedConcept,
                            obj: GroundedConcept) -> GroundedConcept:
        """Merge action and object into action sequence"""
        new_grounding = MultiModalGrounding(
            perceptual=action.grounding.perceptual * 0.6 + obj.grounding.perceptual * 0.4,
            motor=action.grounding.motor,
            linguistic={**action.grounding.linguistic, **obj.grounding.linguistic},
            mathematical=action.grounding.mathematical,
            causal=action.grounding.causal,
            affective=action.grounding.affective * 0.7 + obj.grounding.affective * 0.3
        )

        new_concept = GroundedConcept(f"{action.name}_{obj.name}", new_grounding)
        new_concept.composition_history = [
            ('compose', action.name, obj.name, 'merge_action_object')
        ]

        return new_concept

    def _apply_action(self, action: GroundedConcept,
                     obj: GroundedConcept) -> GroundedConcept:
        """Apply action to object, creating transformed object"""
        # Transform object based on action
        transformed_grounding = MultiModalGrounding(
            perceptual=obj.grounding.perceptual * action.weights[0, 0] if hasattr(action, 'weights') else obj.grounding.perceptual,
            motor=[],  # Object after action is static
            linguistic={**obj.grounding.linguistic, 'transformed_by': action.name},
            mathematical=obj.grounding.mathematical,
            causal=action.grounding.causal,  # Inherit action's causal pattern
            affective=obj.grounding.affective * 0.8 + action.grounding.affective * 0.2
        )

        new_concept = GroundedConcept(f"{obj.name}_after_{action.name}", transformed_grounding)
        new_concept.composition_history = [
            ('transform', obj.name, action.name, 'apply_action')
        ]

        return new_concept

    def _apply_process(self, process: GroundedConcept,
                      obj: GroundedConcept) -> GroundedConcept:
        """Apply process to object"""
        # Similar to apply_action but for processes
        new_concept = self._apply_action(process, obj)
        new_concept.composition_history[0] = ('transform', obj.name, process.name, 'apply_process')
        return new_concept

    def _extract_commonality(self, concept1: GroundedConcept,
                           concept2: GroundedConcept) -> GroundedConcept:
        """Extract common abstract properties"""
        # Find shared linguistic features
        shared_words = set(concept1.grounding.linguistic.keys()) & set(concept2.grounding.linguistic.keys())
        shared_linguistic = {word: min(concept1.grounding.linguistic[word],
                                      concept2.grounding.linguistic[word])
                            for word in shared_words}

        # Average perceptual features
        avg_perceptual = (concept1.grounding.perceptual + concept2.grounding.perceptual) / 2

        new_grounding = MultiModalGrounding(
            perceptual=avg_perceptual,
            motor=[],
            linguistic=shared_linguistic,
            mathematical=concept1.grounding.mathematical,  # Simplified
            causal=concept1.grounding.causal,
            affective=(concept1.grounding.affective + concept2.grounding.affective) / 2
        )

        new_concept = GroundedConcept(f"abstract_{concept1.name}_{concept2.name}", new_grounding)
        new_concept.composition_history = [
            ('abstract', concept1.name, concept2.name, 'extract_commonality')
        ]

        return new_concept

    def _abstract_action(self, action1: GroundedConcept,
                        action2: GroundedConcept) -> GroundedConcept:
        """Create abstract action from two actions"""
        # Combine motor patterns
        combined_motor = action1.grounding.motor + action2.grounding.motor

        # Combine linguistic features
        combined_linguistic = {**action1.grounding.linguistic, **action2.grounding.linguistic}

        new_grounding = MultiModalGrounding(
            perceptual=(action1.grounding.perceptual + action2.grounding.perceptual) / 2,
            motor=combined_motor,
            linguistic=combined_linguistic,
            mathematical=action1.grounding.mathematical,
            causal=action1.grounding.causal,
            affective=(action1.grounding.affective + action2.grounding.affective) / 2
        )

        new_concept = GroundedConcept(f"abstract_{action1.name}_{action2.name}", new_grounding)
        new_concept.composition_history = [
            ('abstract', action1.name, action2.name, 'abstract_action')
        ]

        return new_concept

    def _general_composition(self, concept1: GroundedConcept,
                           concept2: GroundedConcept,
                           composition_type: CompositionType) -> Optional[GroundedConcept]:
        """General composition when no specific rule applies"""
        if composition_type == CompositionType.MERGE:
            return self._merge_objects(concept1, concept2)
        elif composition_type == CompositionType.TRANSFORM:
            return self._apply_action(concept1, concept2)
        else:
            return None

    def _merge_mathematical(self, m1, m2):
        """Merge mathematical structures"""
        # Simplified merge - would be more sophisticated in practice
        return m1  # Placeholder

    def _merge_causal(self, c1, c2):
        """Merge causal patterns"""
        # Combine causal sequences
        combined_sequence = c1.sequence_structure + c2.sequence_structure
        return type(c1)(
            duration_distribution=(
                (c1.duration_distribution[0] + c2.duration_distribution[0]) / 2,
                max(c1.duration_distribution[1], c2.duration_distribution[1])
            ),
            sequence_structure=combined_sequence,
            causal_strengths={**c1.causal_strengths, **c2.causal_strengths}
        )


class Transform:
    """Transformation operations for grounded concepts"""

    def __init__(self, concept_space: ConceptSpace):
        self.concept_space = concept_space

    def apply_transformation(self, concept: GroundedConcept,
                           transformation: str,
                           parameters: Dict[str, Any] = None) -> GroundedConcept:
        """Apply a transformation to a concept"""
        if transformation == "scale":
            return self._scale(concept, parameters or {})
        elif transformation == "rotate":
            return self._rotate(concept, parameters or {})
        elif transformation == "abstract":
            return self._abstract_level(concept, parameters or {})
        elif transformation == "specialize":
            return self._specialize(concept, parameters or {})
        else:
            return concept  # No transformation

    def _scale(self, concept: GroundedConcept, params: Dict[str, Any]) -> GroundedConcept:
        """Scale concept properties"""
        scale_factor = params.get('factor', 1.0)

        new_grounding = MultiModalGrounding(
            perceptual=concept.grounding.perceptual * scale_factor,
            motor=concept.grounding.motor,
            linguistic=concept.grounding.linguistic,
            mathematical=concept.grounding.mathematical,
            causal=concept.grounding.causal,
            affective=concept.grounding.affective
        )

        new_concept = GroundedConcept(f"scaled_{concept.name}", new_grounding)
        new_concept.composition_history = [
            ('transform', concept.name, 'scale', f'factor={scale_factor}')
        ]

        return new_concept

    def _rotate(self, concept: GroundedConcept, params: Dict[str, Any]) -> GroundedConcept:
        """Rotate concept - primarily for spatial concepts"""
        angle = params.get('angle', 0)

        # Apply rotation to perceptual features
        new_perceptual = concept.grounding.perceptual.copy()
        if len(new_perceptual) >= 2:
            # Simple 2D rotation for first two dimensions
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            x, y = new_perceptual[0], new_perceptual[1]
            new_perceptual[0] = x * cos_a - y * sin_a
            new_perceptual[1] = x * sin_a + y * cos_a

        new_grounding = MultiModalGrounding(
            perceptual=new_perceptual,
            motor=concept.grounding.motor,
            linguistic={**concept.grounding.linguistic, 'rotated': angle},
            mathematical=concept.grounding.mathematical,
            causal=concept.grounding.causal,
            affective=concept.grounding.affective
        )

        new_concept = GroundedConcept(f"rotated_{concept.name}", new_grounding)
        new_concept.composition_history = [
            ('transform', concept.name, 'rotate', f'angle={angle}')
        ]

        return new_concept

    def _abstract_level(self, concept: GroundedConcept, params: Dict[str, Any]) -> GroundedConcept:
        """Create more abstract version of concept"""
        level = params.get('level', 1)

        # Move up in type hierarchy
        abstract_types = concept.grounding.mathematical.type_hierarchy[:-level] \
                        if len(concept.grounding.mathematical.type_hierarchy) > level \
                        else ['abstract']

        new_grounding = MultiModalGrounding(
            perceptual=concept.grounding.perceptual * 0.8,  # Less specific
            motor=[],  # Abstract concepts don't have direct motor actions
            linguistic={**concept.grounding.linguistic, 'abstract_level': level},
            mathematical=concept.grounding.mathematical,
            causal=concept.grounding.causal,
            affective=concept.grounding.affective * 0.7
        )

        new_concept = GroundedConcept(f"abstract_{concept.name}_lvl{level}", new_grounding)
        new_concept.composition_history = [
            ('transform', concept.name, 'abstract', f'level={level}')
        ]

        return new_concept

    def _specialize(self, concept: GroundedConcept, params: Dict[str, Any]) -> GroundedConcept:
        """Create more specialized version of concept"""
        specialization = params.get('property', 'specific')

        new_grounding = MultiModalGrounding(
            perceptual=concept.grounding.perceptual * 1.1,  # More specific
            motor=concept.grounding.motor,
            linguistic={**concept.grounding.linguistic, 'specialization': specialization},
            mathematical=concept.grounding.mathematical,
            causal=concept.grounding.causal,
            affective=concept.grounding.affective * 1.1
        )

        new_concept = GroundedConcept(f"specialized_{concept.name}_{specialization}", new_grounding)
        new_concept.composition_history = [
            ('transform', concept.name, 'specialize', f'property={specialization}')
        ]

        return new_concept


class Compare:
    """Comparison operations for grounded concepts"""

    def __init__(self, concept_space: ConceptSpace):
        self.concept_space = concept_space

    def multi_modal_similarity(self, concept1: GroundedConcept,
                              concept2: GroundedConcept) -> Dict[str, float]:
        """Compute similarity across multiple modalities"""
        return {
            'perceptual': self._perceptual_similarity(concept1, concept2),
            'motor': self._motor_similarity(concept1, concept2),
            'linguistic': self._linguistic_similarity(concept1, concept2),
            'mathematical': self._mathematical_similarity(concept1, concept2),
            'causal': self._causal_similarity(concept1, concept2),
            'affective': self._affective_similarity(concept1, concept2),
            'overall': concept1.compare(concept2)
        }

    def _perceptual_similarity(self, concept1: GroundedConcept, concept2: GroundedConcept) -> float:
        """Compute perceptual similarity"""
        return float(np.dot(
            concept1.grounding.perceptual,
            concept2.grounding.perceptual
        ) / (
            np.linalg.norm(concept1.grounding.perceptual) *
            np.linalg.norm(concept2.grounding.perceptual)
        ))

    def _motor_similarity(self, concept1: GroundedConcept, concept2: GroundedConcept) -> float:
        """Compute motor pattern similarity"""
        if not concept1.grounding.motor or not concept2.grounding.motor:
            return 0.0

        # Simple overlap of action types
        actions1 = {action.get('action', '') for action in concept1.grounding.motor}
        actions2 = {action.get('action', '') for action in concept2.grounding.motor}

        intersection = len(actions1 & actions2)
        union = len(actions1 | actions2)

        return intersection / union if union > 0 else 0.0

    def _linguistic_similarity(self, concept1: GroundedConcept, concept2: GroundedConcept) -> float:
        """Compute linguistic similarity"""
        words1 = set(concept1.grounding.linguistic.keys())
        words2 = set(concept2.grounding.linguistic.keys())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _mathematical_similarity(self, concept1: GroundedConcept, concept2: GroundedConcept) -> float:
        """Compute mathematical structure similarity"""
        types1 = set(concept1.grounding.mathematical.type_hierarchy)
        types2 = set(concept2.grounding.mathematical.type_hierarchy)

        if not types1 or not types2:
            return 0.0

        intersection = len(types1 & types2)
        union = len(types1 | types2)

        return intersection / union if union > 0 else 0.0

    def _causal_similarity(self, concept1: GroundedConcept, concept2: GroundedConcept) -> float:
        """Compute causal pattern similarity"""
        seq1 = concept1.grounding.causal.sequence_structure
        seq2 = concept2.grounding.causal.sequence_structure

        if not seq1 or not seq2:
            return 0.0

        # Use sequence similarity
        common = len(set(seq1) & set(seq2))
        total = len(set(seq1) | set(seq2))

        return common / total if total > 0 else 0.0

    def _affective_similarity(self, concept1: GroundedConcept, concept2: GroundedConcept) -> float:
        """Compute affective similarity"""
        return float(np.dot(
            concept1.grounding.affective,
            concept2.grounding.affective
        ) / (
            np.linalg.norm(concept1.grounding.affective) *
            np.linalg.norm(concept2.grounding.affective)
        ))

    def find_analogies(self, concept: GroundedConcept,
                      threshold: float = 0.5) -> List[Tuple[GroundedConcept, float]]:
        """Find analogical concepts"""
        analogies = []

        for other_concept in self.concept_space.concepts.values():
            if other_concept.name != concept.name:
                similarity = concept.compare(other_concept)
                if similarity >= threshold:
                    # Check for structural similarity (analogies are structural)
                    structural_sim = self._structural_similarity(concept, other_concept)
                    if structural_sim > 0.3:  # Threshold for analogy
                        analogies.append((other_concept, similarity))

        return sorted(analogies, key=lambda x: x[1], reverse=True)

    def _structural_similarity(self, concept1: GroundedConcept, concept2: GroundedConcept) -> float:
        """Compute structural similarity for analogies"""
        # Compare composition histories
        hist1 = set(tuple(h) for h in concept1.composition_history)
        hist2 = set(tuple(h) for h in concept2.composition_history)

        if not hist1 or not hist2:
            return 0.0

        # Extract operation types
        ops1 = {h[0] for h in hist1 if len(h) > 0}
        ops2 = {h[0] for h in hist2 if len(h) > 0}

        intersection = len(ops1 & ops2)
        union = len(ops1 | ops2)

        return intersection / union if union > 0 else 0.0