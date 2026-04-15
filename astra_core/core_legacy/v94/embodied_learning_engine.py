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
Embodied Learning Engine - Core component for V94

This engine implements learning through real-world interaction, moving beyond
simulation to true embodied experience and understanding.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
import logging

from ..v80.neural_symbolic_integration import NeuralSymbolicBridge
from ..v93.self_modifying_architecture import DynamicArchitecture
from .sensorimotor_system import SensorimotorInterface, WorldAction, Experience
from .developmental_learning import DevelopmentalLearning
from .common_sense_engine import CommonSenseEngine
from .language_grounding import LanguageGroundingEngine


@dataclass
class LearningState:
    """State of the embodied learning system"""
    experience_buffer: List[Experience] = field(default_factory=list)
    skill_level: Dict[str, float] = field(default_factory=dict)
    conceptual_understanding: Dict[str, float] = field(default_factory=dict)
    curiosity_drive: float = 1.0
    exploration_tendency: float = 0.8
    learning_rate: float = 0.01

    def update_skill(self, skill: str, delta: float):
        """Update skill level with experience"""
        current = self.skill_level.get(skill, 0.0)
        self.skill_level[skill] = np.clip(current + delta, 0.0, 1.0)

    def get_confidence(self, domain: str) -> float:
        """Get confidence level in a domain"""
        return self.skill_level.get(domain, 0.0)


class EmbodiedLearningEngine:
    """
    Core engine for embodied learning through real-world interaction.

    This represents the paradigm shift from simulated intelligence to
    experienced intelligence through sensorimotor grounding.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Core components
        self.sensorimotor_system = SensorimotorInterface()
        self.developmental_learning = DevelopmentalLearning()
        self.common_sense_engine = CommonSenseEngine()
        self.language_grounding = LanguageGroundingEngine()

        # Integration with previous versions
        self.neural_symbolic_bridge = NeuralSymbolicBridge()
        self.dynamic_architecture = DynamicArchitecture()

        # Learning state
        self.learning_state = LearningState()
        self.current_goals: List[str] = []
        self.active_experiments: List[Dict] = []

        # Performance metrics
        self.interaction_count = 0
        self.successful_interactions = 0
        self.discovery_count = 0

        self.logger.info("V94 Embodied Learning Engine initialized")

    def interact_with_world(self, action: WorldAction) -> Experience:
        """
        Learn through interaction with the world.

        This is the core method that implements embodied learning through
        sensorimotor experience and feedback.
        """
        self.interaction_count += 1

        # Execute action through sensorimotor system
        try:
            result = self.sensorimotor_system.execute(action)
            self.successful_interactions += 1

            # Create experience record
            experience = Experience(
                action=action,
                result=result,
                timestamp=time.time(),
                context=self._get_current_context()
            )

            # Process experience through different learning systems
            self._process_experience(experience)

            # Update learning state
            self._update_learning_state(experience)

            # Check for discoveries
            discoveries = self._check_for_discoveries(experience)
            if discoveries:
                self.discovery_count += len(discoveries)
                self._handle_discoveries(discoveries)

            return experience

        except Exception as e:
            self.logger.error(f"Error in world interaction: {e}")
            # Create failure experience
            return Experience(
                action=action,
                result={"success": False, "error": str(e)},
                timestamp=time.time(),
                context=self._get_current_context(),
                success=False
            )

    def explore_environment(self, environment: Any, duration: float = 60.0) -> List[Experience]:
        """
        Autonomous exploration of environment through curiosity-driven learning.
        """
        experiences = []
        start_time = time.time()

        self.logger.info(f"Starting autonomous exploration for {duration}s")

        while time.time() - start_time < duration:
            # Generate curiosity-driven action
            action = self._generate_curiosity_action(environment)

            # Execute and learn
            experience = self.interact_with_world(action)
            experiences.append(experience)

            # Update exploration strategy
            self._update_exploration_strategy(experience)

            # Short pause to prevent overwhelming
            time.sleep(0.1)

        self.logger.info(f"Exploration completed: {len(experiences)} interactions")
        return experiences

    def learn_skill_through_practice(self, skill_name: str, target_environment: Any,
                                   practice_iterations: int = 100) -> Dict[str, float]:
        """
        Learn a specific skill through deliberate practice and feedback.
        """
        self.logger.info(f"Learning skill: {skill_name}")

        skill_progress = []
        initial_level = self.learning_state.get_confidence(skill_name)

        for iteration in range(practice_iterations):
            # Generate skill-specific action
            action = self._generate_skill_practice_action(skill_name, target_environment)

            # Execute and learn
            experience = self.interact_with_world(action)

            # Evaluate skill performance
            performance = self._evaluate_skill_performance(skill_name, experience)
            skill_progress.append(performance)

            # Adaptive difficulty adjustment
            if performance > 0.8:
                self._increase_skill_difficulty(skill_name)
            elif performance < 0.3:
                self._decrease_skill_difficulty(skill_name)

            # Update skill level
            improvement = performance - self.learning_state.get_confidence(skill_name)
            self.learning_state.update_skill(skill_name, improvement * 0.1)

        final_level = self.learning_state.get_confidence(skill_name)
        improvement = final_level - initial_level

        self.logger.info(f"Skill {skill_name} improved by {improvement:.3f}")

        return {
            "initial_level": initial_level,
            "final_level": final_level,
            "improvement": improvement,
            "progress_history": skill_progress
        }

    def ground_concept(self, concept: str, grounding_experiences: List[Experience]) -> bool:
        """
        Ground an abstract concept through embodied experience.
        """
        self.logger.info(f"Grounding concept: {concept}")

        # Extract sensory patterns from experiences
        sensory_patterns = self._extract_sensory_patterns(grounding_experiences)

        # Build multimodal representation
        representation = self.language_grounding.build_concept_representation(
            concept, sensory_patterns
        )

        # Integrate with existing knowledge
        success = self._integrate_grounded_concept(concept, representation)

        if success:
            self.learning_state.conceptual_understanding[concept] = len(grounding_experiences) / 10.0
            self.logger.info(f"Successfully grounded concept: {concept}")

        return success

    def predict_outcome(self, scenario: Any) -> Dict[str, float]:
        """
        Predict outcome using grounded common sense and physics understanding.
        """
        # Use common sense engine for intuitive prediction
        intuitive_prediction = self.common_sense_engine.predict_outcome(scenario)

        # Use neural-symbolic integration for analytical prediction
        analytical_prediction = self.neural_symbolic_bridge.predict(scenario)

        # Combine predictions with confidence weighting
        combined_prediction = self._combine_predictions(
            intuitive_prediction, analytical_prediction
        )

        return combined_prediction

    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        return {
            "interaction_count": self.interaction_count,
            "success_rate": self.successful_interactions / max(1, self.interaction_count),
            "discovery_count": self.discovery_count,
            "skill_levels": self.learning_state.skill_level,
            "conceptual_understanding": self.learning_state.conceptual_understanding,
            "curiosity_level": self.learning_state.curiosity_drive,
            "exploration_tendency": self.learning_state.exploration_tendency,
            "experience_buffer_size": len(self.learning_state.experience_buffer),
            "active_experiments": len(self.active_experiments)
        }

    # Private methods

    def _get_current_context(self) -> Dict[str, Any]:
        """Get current learning context."""
        return {
            "current_goals": self.current_goals.copy(),
            "skill_levels": self.learning_state.skill_level.copy(),
            "timestamp": time.time()
        }

    def _process_experience(self, experience: Experience):
        """Process experience through all learning systems."""
        # Add to experience buffer
        self.learning_state.experience_buffer.append(experience)

        # Limit buffer size
        if len(self.learning_state.experience_buffer) > 10000:
            self.learning_state.experience_buffer = self.learning_state.experience_buffer[-5000:]

        # Process through developmental learning
        self.developmental_learning.process_experience(experience)

        # Update common sense understanding
        self.common_sense_engine.update_from_experience(experience)

        # Ground language if applicable
        self.language_grounding.process_experience(experience)

    def _update_learning_state(self, experience: Experience):
        """Update learning state based on experience."""
        if experience.success:
            # Increase confidence
            self.learning_state.curiosity_drive *= 0.99

            # Update learning rate based on success
            self.learning_state.learning_rate *= 1.001
        else:
            # Increase curiosity and exploration
            self.learning_state.curiosity_drive = min(1.0, self.learning_state.curiosity_drive * 1.01)
            self.learning_state.exploration_tendency = min(1.0, self.learning_state.exploration_tendency * 1.005)

    def _check_for_discoveries(self, experience: Experience) -> List[Dict]:
        """Check if experience leads to new discoveries."""
        discoveries = []

        # Pattern discovery
        if self._is_novel_pattern(experience):
            discoveries.append({
                "type": "pattern",
                "description": "Novel pattern discovered",
                "experience": experience
            })

        # Causal discovery
        causal_relations = self._discover_causal_relations(experience)
        if causal_relations:
            discoveries.extend(causal_relations)

        return discoveries

    def _handle_discoveries(self, discoveries: List[Dict]):
        """Handle and integrate new discoveries."""
        for discovery in discoveries:
            self.logger.info(f"New discovery: {discovery['description']}")

            # Update architecture if significant
            if discovery["type"] == "causal":
                self.dynamic_architecture.integrate_discovery(discovery)

    def _generate_curiosity_action(self, environment: Any) -> WorldAction:
        """Generate action based on curiosity drive."""
        return self.developmental_learning.generate_curiosity_action(environment)

    def _generate_skill_practice_action(self, skill_name: str, environment: Any) -> WorldAction:
        """Generate action for skill practice."""
        return self.developmental_learning.generate_skill_action(skill_name, environment)

    def _evaluate_skill_performance(self, skill_name: str, experience: Experience) -> float:
        """Evaluate performance on a skill."""
        return self.developmental_learning.evaluate_performance(skill_name, experience)

    def _extract_sensory_patterns(self, experiences: List[Experience]) -> Dict:
        """Extract sensory patterns from experiences."""
        return self.sensorimotor_system.extract_patterns(experiences)

    def _integrate_grounded_concept(self, concept: str, representation: Dict) -> bool:
        """Integrate grounded concept into knowledge base."""
        return self.language_grounding.integrate_concept(concept, representation)

    def _combine_predictions(self, intuitive: Dict, analytical: Dict) -> Dict:
        """Combine different prediction methods."""
        combined = {}
        for key in intuitive:
            if key in analytical:
                # Weight by confidence
                weight = 0.6  # Prefer intuitive for common sense
                combined[key] = weight * intuitive[key] + (1 - weight) * analytical[key]
        return combined

    def _is_novel_pattern(self, experience: Experience) -> bool:
        """Check if experience contains novel patterns."""
        # Implementation would check against previous experiences
        return np.random.random() > 0.95  # Simplified

    def _discover_causal_relations(self, experience: Experience) -> List[Dict]:
        """Discover causal relations in experience."""
        # Implementation would identify cause-effect relationships
        return []  # Simplified

    def _update_exploration_strategy(self, experience: Experience):
        """Update exploration strategy based on experience."""
        if experience.success:
            self.learning_state.exploration_tendency *= 0.99
        else:
            self.learning_state.exploration_tendency = min(1.0, self.learning_state.exploration_tendency * 1.01)

    def _increase_skill_difficulty(self, skill_name: str):
        """Increase difficulty for skill practice."""
        pass  # Implementation would adjust parameters

    def _decrease_skill_difficulty(self, skill_name: str):
        """Decrease difficulty for skill practice."""
        pass  # Implementation would adjust parameters