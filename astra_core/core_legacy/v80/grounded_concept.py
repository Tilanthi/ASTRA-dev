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
GroundedConcept - Multi-modal Neural-Symbolic Representations
============================================================

This module implements the core concept representation that grounds
knowledge in multi-modal experience rather than text correlations.

Key Innovation: Concepts are not embeddings or symbols but
compositional structures that can be directly manipulated.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json


@dataclass
class MultiModalGrounding:
    """Multi-modal grounding for a concept"""
    perceptual: np.ndarray  # Visual, auditory, tactile features
    motor: List['ActionSequence']  # How to interact with concept
    linguistic: Dict[str, float]  # Usage patterns in language
    mathematical: 'FormalStructure'  # Abstract properties
    causal: 'TemporalPattern'  # Causal interaction patterns
    affective: np.ndarray  # Emotional associations


@dataclass
class ActionSequence:
    """Sequence of motor actions for interaction"""
    preconditions: List[str]
    actions: List[Dict[str, Any]]
    effects: List[str]
    parameters: Dict[str, float]


@dataclass
class FormalStructure:
    """Mathematical properties of concept"""
    type_hierarchy: List[str]
    properties: Dict[str, Any]
    relations: Dict[str, 'FormalStructure']
    invariants: List[str]


@dataclass
class TemporalPattern:
    """Temporal causal patterns"""
    duration_distribution: Tuple[float, float]  # (mean, std)
    sequence_structure: List[str]  # Typical event sequences
    causal_strengths: Dict[str, float]


class GroundedConcept:
    """
    A grounded concept that combines neural representations with
    symbolic manipulability.

    This is the fundamental building block that enables STAN to
    move beyond text correlations to genuine understanding.
    """

    def __init__(self, name: str, grounding: Optional[MultiModalGrounding] = None):
        self.name = name
        self.grounding = grounding or MultiModalGrounding(
            perceptual=np.random.randn(512),
            motor=[],
            linguistic={},
            mathematical=FormalStructure([], {}, {}, []),
            causal=TemporalPattern((0, 1), [], {}),
            affective=np.random.randn(64)
        )

        # Neural network weights that define the concept
        self.weights = np.random.randn(512, 256)
        self.biases = np.random.randn(256)

        # Symbolic properties extracted from neural structure
        self.symbolic_form = self._extract_symbolic_form()

        # Composition history for tracking concept evolution
        self.composition_history = []

        # Usage statistics for meta-learning
        self.usage_count = 0
        self.success_rate = 0.5

    def _extract_symbolic_form(self) -> Dict[str, Any]:
        """Extract symbolic representation from neural weights"""
        # In practice, this would use more sophisticated extraction
        # Here we simulate the process
        return {
            'type': self._infer_concept_type(),
            'properties': self._extract_properties(),
            'relations': self._extract_relations(),
            'constraints': self._extract_constraints()
        }

    def _infer_concept_type(self) -> str:
        """Infer concept type from neural structure"""
        # Analyze weight patterns to determine type
        if np.mean(self.weights) > 0:
            return 'object'
        elif np.std(self.weights) > 0.5:
            return 'action'
        elif len(self.grounding.causal.sequence_structure) > 0:
            return 'process'
        else:
            return 'property'

    def _extract_properties(self) -> Dict[str, Any]:
        """Extract properties from neural representation"""
        # Simulate property extraction
        return {
            'tangible': bool(np.random.random() > 0.5),
            'mobile': bool(np.random.random() > 0.5),
            'abstract': bool(np.random.random() > 0.7)
        }

    def _extract_relations(self) -> List[str]:
        """Extract relational structure"""
        # In practice, would find related concepts in memory
        return []

    def _extract_constraints(self) -> List[str]:
        """Extract constraints that apply to this concept"""
        return []

    def compose(self, other: 'GroundedConcept',
                operation: str = 'merge') -> 'GroundedConcept':
        """
        Compose this concept with another to create a new concept.

        This is the key operation that enables generativity and
        understanding of novel combinations.
        """
        if operation == 'merge':
            # Merge groundings
            new_grounding = MultiModalGrounding(
                perceptual=(self.grounding.perceptual +
                          other.grounding.perceptual) / 2,
                motor=self.grounding.motor + other.grounding.motor,
                linguistic={**self.grounding.linguistic,
                           **other.grounding.linguistic},
                mathematical=self._merge_mathematical(
                    self.grounding.mathematical,
                    other.grounding.mathematical
                ),
                causal=self._merge_causal(
                    self.grounding.causal,
                    other.grounding.causal
                ),
                affective=(self.grounding.affective +
                          other.grounding.affective) / 2
            )

            # Compose neural representations
            new_weights = (self.weights + other.weights) / 2
            new_biases = (self.biases + other.biases) / 2

            # Create new concept
            new_name = f"{self.name}+{other.name}"
            new_concept = GroundedConcept(new_name, new_grounding)
            new_concept.weights = new_weights
            new_concept.biases = new_biases

            # Track composition
            new_concept.composition_history = [
                ('compose', self.name, other.name, operation)
            ]

            return new_concept

        elif operation == 'transform':
            # Apply transformation from other concept
            new_grounding = self._apply_transformation(other)
            new_concept = GroundedConcept(
                f"{other.name}({self.name})",
                new_grounding
            )
            new_concept.composition_history = [
                ('transform', self.name, other.name, operation)
            ]
            return new_concept

        else:
            raise ValueError(f"Unknown composition operation: {operation}")

    def _merge_mathematical(self, m1: FormalStructure,
                           m2: FormalStructure) -> FormalStructure:
        """Merge mathematical structures"""
        return FormalStructure(
            type_hierarchy=list(set(m1.type_hierarchy + m2.type_hierarchy)),
            properties={**m1.properties, **m2.properties},
            relations={**m1.relations, **m2.relations},
            invariants=list(set(m1.invariants + m2.invariants))
        )

    def _merge_causal(self, c1: TemporalPattern,
                     c2: TemporalPattern) -> TemporalPattern:
        """Merge causal patterns"""
        return TemporalPattern(
            duration_distribution=(
                (c1.duration_distribution[0] + c2.duration_distribution[0]) / 2,
                max(c1.duration_distribution[1], c2.duration_distribution[1])
            ),
            sequence_structure=c1.sequence_structure + c2.sequence_structure,
            causal_strengths={**c1.causal_strengths, **c2.causal_strengths}
        )

    def _apply_transformation(self, transformer: 'GroundedConcept') -> MultiModalGrounding:
        """Apply transformation from another concept"""
        # Simulate transformation effect
        new_grounding = MultiModalGrounding(
            perceptual=self.grounding.perceptual * transformer.weights[0, 0],
            motor=self.grounding.motor,  # Preserved
            linguistic={**self.grounding.linguistic,
                       **transformer.grounding.linguistic},
            mathematical=self.grounding.mathematical,
            causal=self.grounding.causal,
            affective=self.grounding.affective + transformer.grounding.affective * 0.1
        )
        return new_grounding

    def compare(self, other: 'GroundedConcept') -> float:
        """
        Compare this concept with another and return similarity.

        Uses multi-modal similarity rather than just embedding distance.
        """
        # Perceptual similarity
        perceptual_sim = np.dot(
            self.grounding.perceptual,
            other.grounding.perceptual
        ) / (
            np.linalg.norm(self.grounding.perceptual) *
            np.linalg.norm(other.grounding.perceptual)
        )

        # Motor similarity
        motor_sim = self._compare_motor_sequences(other)

        # Linguistic similarity
        linguistic_sim = self._compare_linguistic_patterns(other)

        # Mathematical similarity
        mathematical_sim = self._compare_mathematical_structure(other)

        # Weighted combination
        total_sim = (
            0.3 * perceptual_sim +
            0.2 * motor_sim +
            0.2 * linguistic_sim +
            0.3 * mathematical_sim
        )

        return float(total_sim)

    def _compare_motor_sequences(self, other: 'GroundedConcept') -> float:
        """Compare motor action sequences"""
        if not self.grounding.motor or not other.grounding.motor:
            return 0.5

        # Simple overlap measure
        self_actions = set(str(a) for a in self.grounding.motor)
        other_actions = set(str(a) for a in other.grounding.motor)

        if not self_actions or not other_actions:
            return 0.5

        intersection = len(self_actions & other_actions)
        union = len(self_actions | other_actions)

        return intersection / union if union > 0 else 0

    def _compare_linguistic_patterns(self, other: 'GroundedConcept') -> float:
        """Compare linguistic usage patterns"""
        self_words = set(self.grounding.linguistic.keys())
        other_words = set(other.grounding.linguistic.keys())

        if not self_words or not other_words:
            return 0.5

        intersection = len(self_words & other_words)
        union = len(self_words | other_words)

        return intersection / union if union > 0 else 0

    def _compare_mathematical_structure(self, other: 'GroundedConcept') -> float:
        """Compare mathematical structures"""
        # Compare type hierarchies
        self_types = set(self.grounding.mathematical.type_hierarchy)
        other_types = set(other.grounding.mathematical.type_hierarchy)

        if not self_types or not other_types:
            return 0.5

        intersection = len(self_types & other_types)
        union = len(self_types | other_types)

        return intersection / union if union > 0 else 0

    def apply_to_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply this concept to a context and predict outcomes.

        This is where grounded reasoning happens - the concept
        actively shapes predictions based on its grounding.
        """
        # Use neural weights to transform context
        context_vector = self._encode_context(context)
        transformed = np.dot(context_vector, self.weights) + self.biases

        # Decode back to context
        prediction = self._decode_to_context(transformed)

        # Add causal constraints from grounding
        if self.grounding.causal.sequence_structure:
            prediction['causal_constraints'] = self.grounding.causal.sequence_structure

        return prediction

    def _encode_context(self, context: Dict[str, Any]) -> np.ndarray:
        """Encode context to vector representation"""
        # Simplified encoding
        vector = np.zeros(512)
        for i, (key, value) in enumerate(context.items()):
            if i < 512:
                vector[i] = hash(str(value)) % 1000 / 1000
        return vector

    def _decode_to_context(self, vector: np.ndarray) -> Dict[str, Any]:
        """Decode vector back to context representation"""
        # Simplified decoding
        return {
            'prediction_confidence': float(np.mean(vector)),
            'expected_outcomes': [],
            'relevant_properties': self.symbolic_form['properties']
        }

    def learn_from_interaction(self, interaction: Dict[str, Any]):
        """
        Update concept based on interaction with environment.

        This enables continuous learning and grounding refinement.
        """
        # Update neural weights based on interaction
        if 'outcome' in interaction:
            reward = 1.0 if interaction['outcome'] == 'success' else -0.1
            self.weights += reward * np.random.randn(*self.weights.shape) * 0.01

        # Update grounding
        if 'perceptual' in interaction:
            self.grounding.perceptual = 0.9 * self.grounding.perceptual + \
                                      0.1 * interaction['perceptual']

        # Update usage statistics
        self.usage_count += 1
        if 'outcome' in interaction and interaction['outcome'] == 'success':
            self.success_rate = (self.success_rate * (self.usage_count - 1) + 1.0) / self.usage_count

    def to_json(self) -> Dict[str, Any]:
        """Serialize concept to JSON"""
        return {
            'name': self.name,
            'grounding': {
                'perceptual': self.grounding.perceptual.tolist(),
                'motor': [],  # Would serialize action sequences
                'linguistic': self.grounding.linguistic,
                'mathematical': {
                    'type_hierarchy': self.grounding.mathematical.type_hierarchy,
                    'properties': self.grounding.mathematical.properties
                },
                'causal': {
                    'sequence_structure': self.grounding.causal.sequence_structure,
                    'causal_strengths': self.grounding.causal.causal_strengths
                },
                'affective': self.grounding.affective.tolist()
            },
            'symbolic_form': self.symbolic_form,
            'composition_history': self.composition_history,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'GroundedConcept':
        """Deserialize concept from JSON"""
        concept = cls(data['name'])
        concept.symbolic_form = data['symbolic_form']
        concept.composition_history = data['composition_history']
        concept.usage_count = data['usage_count']
        concept.success_rate = data['success_rate']
        return concept


class ConceptSpace:
    """Manages a space of grounded concepts and their relationships"""

    def __init__(self):
        self.concepts: Dict[str, GroundedConcept] = {}
        self.relations: Dict[str, Dict[str, float]] = {}
        self.composition_cache: Dict[Tuple[str, str, str], GroundedConcept] = {}

    def add_concept(self, concept: GroundedConcept):
        """Add a concept to the space"""
        self.concepts[concept.name] = concept

        # Update relations with existing concepts
        for other_name, other_concept in self.concepts.items():
            if other_name != concept.name:
                similarity = concept.compare(other_concept)
                if concept.name not in self.relations:
                    self.relations[concept.name] = {}
                if other_name not in self.relations:
                    self.relations[other_name] = {}

                self.relations[concept.name][other_name] = similarity
                self.relations[other_name][concept.name] = similarity

    def get_concept(self, name: str) -> Optional[GroundedConcept]:
        """Get a concept by name"""
        return self.concepts.get(name)

    def find_similar(self, concept: GroundedConcept,
                    threshold: float = 0.7) -> List[Tuple[GroundedConcept, float]]:
        """Find concepts similar to given concept"""
        similar = []
        for other_concept in self.concepts.values():
            if other_concept.name != concept.name:
                similarity = concept.compare(other_concept)
                if similarity >= threshold:
                    similar.append((other_concept, similarity))

        return sorted(similar, key=lambda x: x[1], reverse=True)

    def compose_concepts(self, name1: str, name2: str,
                        operation: str = 'merge') -> Optional[GroundedConcept]:
        """Compose two concepts"""
        # Check cache first
        cache_key = (name1, name2, operation)
        if cache_key in self.composition_cache:
            return self.composition_cache[cache_key]

        # Get concepts
        concept1 = self.get_concept(name1)
        concept2 = self.get_concept(name2)

        if not concept1 or not concept2:
            return None

        # Compose
        new_concept = concept1.compose(concept2, operation)

        # Cache and add to space
        self.composition_cache[cache_key] = new_concept
        self.add_concept(new_concept)

        return new_concept