"""
Language Grounding System - Grounding language in embodied experience

This system connects abstract symbols (words, concepts) to concrete embodied experiences,
providing the bridge between language and meaning through sensorimotor grounding.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
import logging
from enum import Enum

from .sensorimotor_system import Experience, SensoryInput, ModalityType


class GroundingType(Enum):
    """Types of grounding for concepts"""
    SENSORIMOTOR = "sensorimotor"  # Grounded in sensory-motor experience
    AFFECTIVE = "affective"  # Grounded in emotional experience
    SOCIAL = "social"  # Grounded in social interaction
    FUNCTIONAL = "functional"  # Grounded in function/use
    RELATIONAL = "relational"  # Grounded in relationships to other concepts


@dataclass
class GroundingExperience:
    """Experience that contributes to grounding a concept"""
    concept: str
    experience: Experience
    grounding_type: GroundingType
    relevance_score: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class MultimodalRepresentation:
    """Multimodal representation of a grounded concept"""
    concept: str
    visual_features: Optional[np.ndarray] = None
    auditory_features: Optional[np.ndarray] = None
    tactile_features: Optional[np.ndarray] = None
    motor_features: Optional[np.ndarray] = None
    affective_features: Optional[np.ndarray] = None
    functional_features: Optional[np.ndarray] = None
    context_features: Optional[np.ndarray] = None

    def get_feature_vector(self) -> np.ndarray:
        """Get combined feature vector"""
        features = []

        if self.visual_features is not None:
            features.append(self.visual_features.flatten())
        if self.auditory_features is not None:
            features.append(self.auditory_features.flatten())
        if self.tactile_features is not None:
            features.append(self.tactile_features.flatten())
        if self.motor_features is not None:
            features.append(self.motor_features.flatten())
        if self.affective_features is not None:
            features.append(self.affective_features.flatten())
        if self.functional_features is not None:
            features.append(self.functional_features.flatten())
        if self.context_features is not None:
            features.append(self.context_features.flatten())

        if features:
            return np.concatenate(features)
        else:
            return np.array([])


@dataclass
class SymbolGrounding:
    """Grounding of a linguistic symbol"""
    symbol: str
    word_class: str  # noun, verb, adjective, etc.
    grounded_meaning: MultimodalRepresentation
    grounding_experiences: List[GroundingExperience] = field(default_factory=list)
    confidence: float = 0.0
    last_updated: float = field(default_factory=time.time)


class ConceptGroundingEngine:
    """Engine for grounding concepts in embodied experience"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Grounded concepts database
        self.grounded_concepts: Dict[str, SymbolGrounding] = {}

        # Feature extraction
        self.feature_extractors: Dict[ModalityType, Any] = {}
        self._initialize_feature_extractors()

        # Grounding parameters
        self.grounding_threshold = 0.5
        self.experience_decay_rate = 0.99
        self.max_experiences_per_concept = 100

        # Statistics
        self.total_grounding_experiences = 0
        self.successful_groundings = 0

        self.logger.info("Concept grounding engine initialized")

    def _initialize_feature_extractors(self):
        """Initialize feature extractors for different modalities"""
        # Simplified feature extractors
        self.feature_extractors[ModalityType.VISION] = self._extract_visual_features
        self.feature_extractors[ModalityType.AUDIO] = self._extract_audio_features
        self.feature_extractors[ModalityType.TOUCH] = self._extract_tactile_features
        self.feature_extractors[ModalityType.PROPRIOCEPTION] = self._extract_motor_features

    def ground_concept(self, concept: str, experiences: List[Experience]) -> bool:
        """
        Ground a concept through embodied experiences.

        This is the core method that connects abstract concepts to
        concrete sensory-motor experiences.
        """
        if not experiences:
            return False

        # Filter relevant experiences
        relevant_experiences = self._filter_relevant_experiences(concept, experiences)
        if not relevant_experiences:
            return False

        # Create multimodal representation
        representation = self._build_multimodal_representation(relevant_experiences)

        # Create or update symbol grounding
        if concept in self.grounded_concepts:
            grounding = self.grounded_concepts[concept]
            self._update_grounding(grounding, representation, relevant_experiences)
        else:
            grounding = self._create_grounding(concept, representation, relevant_experiences)
            self.grounded_concepts[concept] = grounding

        # Update statistics
        self.total_grounding_experiences += len(relevant_experiences)
        self.successful_groundings += 1

        self.logger.info(f"Successfully grounded concept: {concept}")
        return True

    def get_concept_representation(self, concept: str) -> Optional[MultimodalRepresentation]:
        """Get grounded representation of concept"""
        if concept in self.grounded_concepts:
            return self.grounded_concepts[concept].grounded_meaning
        return None

    def compute_concept_similarity(self, concept1: str, concept2: str) -> float:
        """Compute similarity between two grounded concepts"""
        if concept1 not in self.grounded_concepts or concept2 not in self.grounded_concepts:
            return 0.0

        rep1 = self.grounded_concepts[concept1].grounded_meaning.get_feature_vector()
        rep2 = self.grounded_concepts[concept2].grounded_meaning.get_feature_vector()

        if len(rep1) == 0 or len(rep2) == 0:
            return 0.0

        # Cosine similarity
        similarity = np.dot(rep1, rep2) / (np.linalg.norm(rep1) * np.linalg.norm(rep2) + 1e-8)
        return float(similarity)

    def predict_from_description(self, description: str) -> Dict[str, float]:
        """Make predictions based on grounded understanding of description"""
        # Extract concepts from description
        concepts = self._extract_concepts_from_text(description)
        predictions = {}

        for concept in concepts:
            if concept in self.grounded_concepts:
                grounding = self.grounded_concepts[concept]
                # Use confidence as prediction score
                predictions[concept] = grounding.confidence

        return predictions

    def learn_new_word(self, word: str, word_class: str, examples: List[Experience]) -> bool:
        """Learn meaning of new word from examples"""
        # Determine grounding type from examples
        grounding_type = self._infer_grounding_type(examples)

        # Create grounding experiences
        grounding_experiences = [
            GroundingExperience(
                concept=word,
                experience=exp,
                grounding_type=grounding_type,
                relevance_score=self._compute_relevance(exp, word)
            )
            for exp in examples
        ]

        # Filter high-relevance experiences
        high_relevance = [ge for ge in grounding_experiences if ge.relevance_score > 0.5]

        if not high_relevance:
            return False

        return self.ground_concept(word, [ge.experience for ge in high_relevance])

    def process_experience(self, experience: Experience):
        """Process experience for potential concept grounding"""
        # Extract potential concepts from experience
        potential_concepts = self._extract_concepts_from_experience(experience)

        for concept in potential_concepts:
            # Check if concept should be grounded
            if self._should_ground_concept(concept, experience):
                if concept in self.grounded_concepts:
                    # Update existing grounding
                    self._update_existing_grounding(concept, experience)
                else:
                    # Create new grounding
                    self.ground_concept(concept, [experience])

    def get_grounding_statistics(self) -> Dict[str, Any]:
        """Get comprehensive grounding statistics"""
        return {
            "total_concepts": len(self.grounded_concepts),
            "well_grounded_concepts": len([c for c in self.grounded_concepts.values() if c.confidence > 0.7]),
            "total_experiences": self.total_grounding_experiences,
            "successful_groundings": self.successful_groundings,
            "average_confidence": np.mean([c.confidence for c in self.grounded_concepts.values()]) if self.grounded_concepts else 0.0,
            "grounding_types": self._get_grounding_type_distribution()
        }

    # Private methods

    def _filter_relevant_experiences(self, concept: str, experiences: List[Experience]) -> List[Experience]:
        """Filter experiences relevant to concept"""
        relevant = []

        for exp in experiences:
            relevance = self._compute_relevance(exp, concept)
            if relevance > self.grounding_threshold:
                relevant.append(exp)

        return relevant

    def _compute_relevance(self, experience: Experience, concept: str) -> float:
        """Compute relevance of experience to concept"""
        relevance = 0.0

        # Check goal relevance
        if concept.lower() in experience.action.goal.lower():
            relevance += 0.5

        # Check context relevance
        if concept.lower() in str(experience.context).lower():
            relevance += 0.3

        # Check result relevance
        if concept.lower() in str(experience.result).lower():
            relevance += 0.2

        return min(relevance, 1.0)

    def _build_multimodal_representation(self, experiences: List[Experience]) -> MultimodalRepresentation:
        """Build multimodal representation from experiences"""
        representation = MultimodalRepresentation(concept="")

        # Extract features from all experiences
        all_visual = []
        all_motor = []
        all_context = []

        for exp in experiences:
            # Visual features from sensory feedback
            for sensory in exp.result.sensory_feedback:
                if sensory.modality == ModalityType.VISION:
                    features = self._extract_visual_features(sensory)
                    if features is not None:
                        all_visual.append(features)

            # Motor features from action
            if exp.action.motor_commands:
                motor_features = self._extract_motor_features_from_action(exp.action)
                if motor_features is not None:
                    all_motor.append(motor_features)

            # Context features
            context_features = self._extract_context_features(exp.context)
            if context_features is not None:
                all_context.append(context_features)

        # Aggregate features
        if all_visual:
            representation.visual_features = np.mean(all_visual, axis=0)
        if all_motor:
            representation.motor_features = np.mean(all_motor, axis=0)
        if all_context:
            representation.context_features = np.mean(all_context, axis=0)

        return representation

    def _create_grounding(self, concept: str, representation: MultimodalRepresentation,
                         experiences: List[Experience]) -> SymbolGrounding:
        """Create new symbol grounding"""
        grounding_experiences = [
            GroundingExperience(
                concept=concept,
                experience=exp,
                grounding_type=self._infer_grounding_type([exp]),
                relevance_score=self._compute_relevance(exp, concept)
            )
            for exp in experiences
        ]

        return SymbolGrounding(
            symbol=concept,
            word_class=self._infer_word_class(concept),
            grounded_meaning=representation,
            grounding_experiences=grounding_experiences,
            confidence=self._compute_initial_confidence(experiences)
        )

    def _update_grounding(self, grounding: SymbolGrounding, representation: MultimodalRepresentation,
                         new_experiences: List[Experience]):
        """Update existing symbol grounding"""
        # Add new experiences
        for exp in new_experiences:
            grounding_experience = GroundingExperience(
                concept=grounding.symbol,
                experience=exp,
                grounding_type=self._infer_grounding_type([exp]),
                relevance_score=self._compute_relevance(exp, grounding.symbol)
            )
            grounding.grounding_experiences.append(grounding_experience)

        # Limit experience count
        if len(grounding.grounding_experiences) > self.max_experiences_per_concept:
            # Keep most relevant experiences
            grounding.grounding_experiences.sort(key=lambda x: x.relevance_score, reverse=True)
            grounding.grounding_experiences = grounding.grounding_experiences[:self.max_experiences_per_concept]

        # Update representation (weighted average)
        alpha = 0.3  # Learning rate
        if representation.visual_features is not None:
            if grounding.grounded_meaning.visual_features is None:
                grounding.grounded_meaning.visual_features = representation.visual_features
            else:
                grounding.grounded_meaning.visual_features = (
                    alpha * representation.visual_features +
                    (1 - alpha) * grounding.grounded_meaning.visual_features
                )

        # Update confidence
        grounding.confidence = min(1.0, grounding.confidence * 1.1)
        grounding.last_updated = time.time()

    def _infer_grounding_type(self, experiences: List[Experience]) -> GroundingType:
        """Infer grounding type from experiences"""
        # Check for sensory-motor content
        has_sensory = any(exp.result.sensory_feedback for exp in experiences)
        has_motor = any(exp.action.motor_commands for exp in experiences)

        if has_sensory and has_motor:
            return GroundingType.SENSORIMOTOR
        elif "social" in str(experiences):
            return GroundingType.SOCIAL
        elif "emotion" in str(experiences):
            return GroundingType.AFFECTIVE
        else:
            return GroundingType.FUNCTIONAL

    def _infer_word_class(self, concept: str) -> str:
        """Infer word class from concept"""
        # Simplified word class inference
        if concept.endswith("ing"):
            return "verb"
        elif concept.endswith("ly"):
            return "adverb"
        elif concept.endswith("able") or concept.endswith("ful"):
            return "adjective"
        else:
            return "noun"

    def _compute_initial_confidence(self, experiences: List[Experience]) -> float:
        """Compute initial confidence for new grounding"""
        if not experiences:
            return 0.0

        # Base confidence on number and relevance of experiences
        avg_relevance = np.mean([self._compute_relevance(exp, "") for exp in experiences])
        experience_bonus = min(len(experiences) / 10.0, 1.0)

        return avg_relevance * 0.7 + experience_bonus * 0.3

    def _extract_visual_features(self, sensory_input: SensoryInput) -> Optional[np.ndarray]:
        """Extract visual features from sensory input"""
        # Simplified feature extraction
        if len(sensory_input.data.shape) >= 2:
            # Use basic statistics as features
            return np.array([
                np.mean(sensory_input.data),
                np.std(sensory_input.data),
                np.min(sensory_input.data),
                np.max(sensory_input.data)
            ])
        return None

    def _extract_audio_features(self, sensory_input: SensoryInput) -> Optional[np.ndarray]:
        """Extract audio features from sensory input"""
        # Simplified audio feature extraction
        if len(sensory_input.data) > 0:
            return np.array([
                np.mean(np.abs(sensory_input.data)),
                np.std(sensory_input.data),
                np.max(np.abs(sensory_input.data))
            ])
        return None

    def _extract_tactile_features(self, sensory_input: SensoryInput) -> Optional[np.ndarray]:
        """Extract tactile features from sensory input"""
        return np.array(sensory_input.data.flatten()[:10])  # Simplified

    def _extract_motor_features(self, sensory_input: SensoryInput) -> Optional[np.ndarray]:
        """Extract motor features from sensory input"""
        return np.array(sensory_input.data.flatten()[:10])  # Simplified

    def _extract_motor_features_from_action(self, action: Any) -> Optional[np.ndarray]:
        """Extract motor features from action"""
        if not action.motor_commands:
            return None

        features = []
        for cmd in action.motor_commands:
            cmd_features = [
                float(cmd.action_type == "reach"),
                float(cmd.action_type == "grasp"),
                float(cmd.action_type == "push"),
                cmd.force,
                cmd.duration
            ]
            features.extend(cmd_features)

        return np.array(features)

    def _extract_context_features(self, context: Dict) -> Optional[np.ndarray]:
        """Extract context features"""
        # Simplified context feature extraction
        features = [
            len(str(context)),
            hash(str(context)) % 1000 / 1000.0,  # Normalized hash
            float("object" in str(context)),
            float("social" in str(context)),
            float("goal" in str(context))
        ]
        return np.array(features)

    def _extract_concepts_from_experience(self, experience: Experience) -> List[str]:
        """Extract potential concepts from experience"""
        concepts = []

        # From goal
        concepts.extend(experience.action.goal.split())

        # From context
        if isinstance(experience.context, dict):
            for key, value in experience.context.items():
                concepts.append(str(key))
                if isinstance(value, str):
                    concepts.extend(value.split())

        # Filter and clean
        concepts = [c.lower().strip() for c in concepts if len(c) > 2]
        return list(set(concepts))  # Remove duplicates

    def _extract_concepts_from_text(self, text: str) -> List[str]:
        """Extract concepts from text"""
        # Simplified concept extraction
        words = text.lower().split()
        return [w for w in words if len(w) > 2]

    def _should_ground_concept(self, concept: str, experience: Experience) -> bool:
        """Determine if concept should be grounded from this experience"""
        # Don't ground if already well-grounded
        if concept in self.grounded_concepts:
            if self.grounded_concepts[concept].confidence > 0.9:
                return False

        # Check relevance
        relevance = self._compute_relevance(experience, concept)
        return relevance > self.grounding_threshold

    def _update_existing_grounding(self, concept: str, experience: Experience):
        """Update existing concept grounding"""
        if concept in self.grounded_concepts:
            grounding = self.grounded_concepts[concept]

            # Add experience
            grounding_experience = GroundingExperience(
                concept=concept,
                experience=experience,
                grounding_type=self._infer_grounding_type([experience]),
                relevance_score=self._compute_relevance(experience, concept)
            )
            grounding.grounding_experiences.append(grounding_experience)

            # Update confidence
            if experience.success:
                grounding.confidence = min(1.0, grounding.confidence * 1.05)
            else:
                grounding.confidence *= 0.98

            grounding.last_updated = time.time()

    def _get_grounding_type_distribution(self) -> Dict[str, int]:
        """Get distribution of grounding types"""
        distribution = {gt.value: 0 for gt in GroundingType}

        for grounding in self.grounded_concepts.values():
            if grounding.grounding_experiences:
                # Use most common grounding type
                types = [ge.grounding_type for ge in grounding.grounding_experiences]
                most_common = max(set(types), key=types.count)
                distribution[most_common.value] += 1

        return distribution


class LanguageGroundingEngine:
    """
    Main language grounding engine that coordinates concept grounding
    and provides the bridge between language and embodied experience.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.concept_grounding = ConceptGroundingEngine()
        self.phrase_patterns = {}  # Common phrases and their meanings
        self.grounding_cache = {}

    def build_concept_representation(self, concept: str, sensory_patterns: Dict) -> MultimodalRepresentation:
