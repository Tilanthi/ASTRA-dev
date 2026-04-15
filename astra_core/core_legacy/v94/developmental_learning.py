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
Developmental Learning System - Infant-like learning through play and exploration

This implements learning inspired by human cognitive development, progressing through
stages similar to infant learning: sensorimotor, preoperational, and concrete operational.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
import logging
from enum import Enum

from .sensorimotor_system import Experience, WorldAction, SensoryInput, MotorCommand


class DevelopmentalStage(Enum):
    """Piaget-inspired developmental stages"""
    SENSORIMOTOR = "sensorimotor"  # 0-2 years: Object permanence, basic causality
    PREOPERATIONAL = "preoperational"  # 2-7 years: Symbolic thinking, language
    CONCRETE_OPERATIONAL = "concrete"  # 7-11 years: Logic, conservation
    FORMAL_OPERATIONAL = "formal"  # 11+ years: Abstract reasoning


@dataclass
class LearningMilestone:
    """Developmental learning milestone"""
    name: str
    stage: DevelopmentalStage
    achieved: bool = False
    achievement_time: Optional[float] = None
    confidence: float = 0.0
    required_experiences: int = 10


@dataclass
class PlayfulActivity:
    """Playful learning activity"""
    name: str
    activity_type: str
    parameters: Dict[str, Any]
    curiosity_value: float
    learning_potential: float
    age_appropriate: List[DevelopmentalStage]


class CuriosityModel:
    """Model of intrinsic curiosity and exploration drive"""

    def __init__(self):
        self.information_gain_model = {}
        self.novelty_threshold = 0.1
        self.exploration_bonus = 1.0
        self.uncertainty_reduction = {}

    def compute_curiosity(self, context: Dict[str, Any], potential_action: MotorCommand) -> float:
        """Compute curiosity value for potential action"""
        # Information gain component
        info_gain = self._estimate_information_gain(context, potential_action)

        # Novelty component
        novelty = self._estimate_novelty(potential_action)

        # Uncertainty reduction component
        uncertainty_reduction = self._estimate_uncertainty_reduction(context, potential_action)

        # Combine with exploration bonus
        curiosity = (info_gain + novelty + uncertainty_reduction) * self.exploration_bonus

        return np.clip(curiosity, 0.0, 1.0)

    def _estimate_information_gain(self, context: Dict, action: MotorCommand) -> float:
        """Estimate expected information gain from action"""
        return np.random.beta(2, 5)  # Simplified

    def _estimate_novelty(self, action: MotorCommand) -> float:
        """Estimate novelty of action"""
        action_signature = f"{action.action_type}_{hash(str(action.parameters)) % 1000}"
        frequency = self.information_gain_model.get(action_signature, 0)
        return 1.0 / (1.0 + frequency)

    def _estimate_uncertainty_reduction(self, context: Dict, action: MotorCommand) -> float:
        """Estimate potential uncertainty reduction"""
        return np.random.beta(1, 3)  # Simplified


class ImitationLearning:
    """Learning through observation and imitation"""

    def __init__(self):
        self.observed_behaviors: List[Dict] = []
        self.imitation_skills: Dict[str, float] = {}
        self.social_learning_rate = 0.1

    def observe_behavior(self, demonstration: Dict[str, Any]) -> bool:
        """Observe and store demonstrated behavior"""
        self.observed_behaviors.append({
            "behavior": demonstration,
            "timestamp": time.time(),
            "imitated": False
        })
        return True

    def imitate_behavior(self, behavior_id: int) -> Optional[MotorCommand]:
        """Attempt to imitate observed behavior"""
        if 0 <= behavior_id < len(self.observed_behaviors):
            behavior = self.observed_behaviors[behavior_id]
            # Convert demonstration to motor command
            command = self._demonstration_to_command(behavior["behavior"])
            if command:
                behavior["imitated"] = True
                return command
        return None

    def _demonstration_to_command(self, demonstration: Dict) -> Optional[MotorCommand]:
        """Convert demonstration to motor command"""
        return MotorCommand(
            action_type=demonstration.get("action", "reach"),
            parameters=demonstration.get("parameters", {})
        )


class DevelopmentalLearning:
    """
    Developmental learning system inspired by human cognitive development.

    This implements infant-like learning through play, exploration, and
    social interaction, progressing through developmental stages.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Developmental stage management
        self.current_stage = DevelopmentalStage.SENSORIMOTOR
        self.stage_progress = {stage: 0.0 for stage in DevelopmentalStage}

        # Learning milestones
        self.milestones = self._initialize_milestones()

        # Learning systems
        self.curiosity_model = CuriosityModel()
        self.imitation_learning = ImitationLearning()

        # Play-based learning
        self.playful_activities = self._initialize_playful_activities()
        self.current_activity = None
        self.play_history: List[Dict] = []

        # Skill development
        self.developing_skills: Dict[str, float] = {}
        self.skill_practice_history: Dict[str, List[Experience]] = {}

        # Object and concept understanding
        self.object_permanence: Dict[str, bool] = {}
        self.conceptual_understanding: Dict[str, float] = {}

        # Social learning
        self.social_interactions: List[Dict] = []
        self.theory_of_mind_model: Dict[str, Any] = {}

        self.logger.info("Developmental learning system initialized")

    def process_experience(self, experience: Experience):
        """Process experience through developmental learning systems"""
        # Update stage progress
        self._update_developmental_stage(experience)

        # Check milestones
        self._check_milestones(experience)

        # Update skills
        self._update_skills_from_experience(experience)

        # Update object permanence
        self._update_object_permanence(experience)

        # Social learning if applicable
        if "social" in experience.context:
            self._process_social_experience(experience)

    def generate_curiosity_action(self, environment: Any) -> WorldAction:
        """Generate action based on intrinsic curiosity"""
        # Get current context
        context = self._get_learning_context()

        # Generate potential actions
        potential_actions = self._generate_potential_actions(environment)

        # Evaluate curiosity for each action
        curiosity_values = []
        for action in potential_actions:
            curiosity = self.curiosity_model.compute_curiosity(context, action)
            curiosity_values.append((action, curiosity))

        # Select action with highest curiosity
        if curiosity_values:
            best_action, max_curiosity = max(curiosity_values, key=lambda x: x[1])
            return self._create_curiosity_action(best_action, max_curiosity)

        # Fallback action
        return self._create_exploration_action()

    def generate_skill_action(self, skill_name: str, environment: Any) -> WorldAction:
        """Generate action for practicing specific skill"""
        skill_level = self.developing_skills.get(skill_name, 0.0)

        # Adjust difficulty based on skill level
        if skill_level < 0.3:
            return self._generate_beginner_skill_action(skill_name, environment)
        elif skill_level < 0.7:
            return self._generate_intermediate_skill_action(skill_name, environment)
        else:
            return self._generate_advanced_skill_action(skill_name, environment)

    def evaluate_performance(self, skill_name: str, experience: Experience) -> float:
        """Evaluate performance on a skill"""
        if not experience.success:
            return 0.0

        # Base performance on success and efficiency
        base_performance = 0.5

        # Consider execution time
        if hasattr(experience.result, 'execution_time'):
            time_bonus = np.exp(-experience.result.execution_time / 10.0)
            base_performance += 0.2 * time_bonus

        # Consider goal achievement
        if experience.action.goal == skill_name:
            base_performance += 0.3

        return np.clip(base_performance, 0.0, 1.0)

    def engage_in_play(self, environment: Any, duration: float = 60.0) -> List[Experience]:
        """Engage in playful learning activities"""
        experiences = []
        start_time = time.time()

        self.logger.info(f"Starting playful learning for {duration}s")

        while time.time() - start_time < duration:
            # Select age-appropriate activity
            activity = self._select_play_activity()

            # Execute playful action
            experience = self._execute_play_activity(activity, environment)
            experiences.append(experience)

            # Update activity based on experience
            self._update_play_activity(activity, experience)

            # Check for developmental transitions
            self._check_developmental_transitions()

        return experiences

    def get_developmental_status(self) -> Dict[str, Any]:
        """Get comprehensive developmental status"""
        return {
            "current_stage": self.current_stage.value,
            "stage_progress": self.stage_progress,
            "achieved_milestones": [m.name for m in self.milestones if m.achieved],
            "skill_levels": self.developing_skills,
            "object_permanence": self.object_permanence,
            "conceptual_understanding": self.conceptual_understanding,
            "social_interactions_count": len(self.social_interactions),
            "play_activities_completed": len(self.play_history)
        }

    # Private methods

    def _initialize_milestones(self) -> List[LearningMilestone]:
        """Initialize developmental milestones"""
        return [
            LearningMilestone("object_permanence", DevelopmentalStage.SENSORIMOTOR),
            LearningMilestone("cause_effect", DevelopmentalStage.SENSORIMOTOR),
            LearningMilestone("symbolic_thinking", DevelopmentalStage.PREOPERATIONAL),
            LearningMilestone("language_use", DevelopmentalStage.PREOPERATIONAL),
            LearningMilestone("logical_reasoning", DevelopmentalStage.CONCRETE_OPERATIONAL),
            LearningMilestone("conservation", DevelopmentalStage.CONCRETE_OPERATIONAL),
            LearningMilestone("abstract_thinking", DevelopmentalStage.FORMAL_OPERATIONAL),
        ]

    def _initialize_playful_activities(self) -> List[PlayfulActivity]:
        """Initialize playful learning activities"""
        return [
            PlayfulActivity(
                "object_exploration",
                "exploration",
                {"target": "objects", "action": "manipulate"},
                curiosity_value=0.8,
                learning_potential=0.7,
                age_appropriate=[DevelopmentalStage.SENSORIMOTOR]
            ),
            PlayfulActivity(
                "peekaboo",
                "social_game",
                {"target": "person", "action": "hide_reveal"},
                curiosity_value=0.9,
                learning_potential=0.6,
                age_appropriate=[DevelopmentalStage.SENSORIMOTOR]
            ),
            PlayfulActivity(
                "sorting_game",
                "cognitive",
                {"target": "objects", "action": "sort_by_property"},
                curiosity_value=0.6,
                learning_potential=0.8,
                age_appropriate=[DevelopmentalStage.PREOPERATIONAL]
            ),
            PlayfulActivity(
                "building_blocks",
                "construction",
                {"target": "blocks", "action": "build_structure"},
                curiosity_value=0.7,
                learning_potential=0.9,
                age_appropriate=[DevelopmentalStage.CONCRETE_OPERATIONAL]
            )
        ]

    def _update_developmental_stage(self, experience: Experience):
        """Update developmental stage progress based on experience"""
        if experience.success:
            # Increase progress in current stage
            self.stage_progress[self.current_stage] += 0.01

            # Check for stage transition
            if self.stage_progress[self.current_stage] >= 1.0:
                self._transition_to_next_stage()

    def _check_milestones(self, experience: Experience):
        """Check if experience achieves developmental milestones"""
        for milestone in self.milestones:
            if not milestone.achieved:
                if self._check_milestone_achievement(milestone, experience):
                    milestone.achieved = True
                    milestone.achievement_time = time.time()
                    self.logger.info(f"Achieved milestone: {milestone.name}")

    def _check_milestone_achievement(self, milestone: LearningMilestone, experience: Experience) -> bool:
        """Check if specific milestone is achieved"""
        if milestone.name == "object_permanence":
            # Check if system understands objects continue to exist
            return "object" in experience.action.goal and experience.success

        elif milestone.name == "cause_effect":
            # Check if system understands causal relationships
            return "cause" in experience.context or "effect" in experience.result.physical_changes

        elif milestone.name == "symbolic_thinking":
            # Check if system uses symbols
            return "symbol" in experience.context or "representation" in experience.action.decision

        return False

    def _transition_to_next_stage(self):
        """Transition to next developmental stage"""
        stages = list(DevelopmentalStage)
        current_index = stages.index(self.current_stage)
        if current_index < len(stages) - 1:
            self.current_stage = stages[current_index + 1]
            self.logger.info(f"Transitioned to developmental stage: {self.current_stage.value}")

    def _update_skills_from_experience(self, experience: Experience):
        """Update skills based on experience"""
        skill_name = experience.action.goal
        if skill_name not in self.developing_skills:
            self.developing_skills[skill_name] = 0.0

        if skill_name not in self.skill_practice_history:
            self.skill_practice_history[skill_name] = []

        self.skill_practice_history[skill_name].append(experience)

        # Update skill level based on success and recent performance
        if experience.success:
            self.developing_skills[skill_name] += 0.01
        else:
            self.developing_skills[skill_name] *= 0.99

        self.developing_skills[skill_name] = np.clip(self.developing_skills[skill_name], 0.0, 1.0)

    def _update_object_permanence(self, experience: Experience):
        """Update object permanence understanding"""
        if "object" in experience.action.goal:
            object_id = experience.action.goal
            self.object_permanence[object_id] = True

    def _process_social_experience(self, experience: Experience):
        """Process social learning experience"""
        self.social_interactions.append({
            "experience": experience,
            "timestamp": time.time()
        })

        # Update theory of mind model
        self._update_theory_of_mind(experience)

    def _update_theory_of_mind(self, experience: Experience):
        """Update theory of mind understanding"""
        # Simplified theory of mind update
        if "other_agent" in experience.context:
            self.theory_of_mind_model["understands_others"] = True

    def _get_learning_context(self) -> Dict[str, Any]:
        """Get current learning context"""
        return {
            "stage": self.current_stage,
            "skills": self.developing_skills,
            "milestones": [m.name for m in self.milestones if m.achieved]
        }

    def _generate_potential_actions(self, environment: Any) -> List[MotorCommand]:
        """Generate potential actions for evaluation"""
        actions = []

        # Basic exploration actions
        actions.append(MotorCommand(
            action_type="reach",
            parameters={"direction": np.random.randn(2)}
        ))

        actions.append(MotorCommand(
            action_type="grasp",
            parameters={}
        ))

        actions.append(MotorCommand(
            action_type="push",
            parameters={"force": 1.0}
        ))

        return actions

    def _create_curiosity_action(self, motor_command: MotorCommand, curiosity: float) -> WorldAction:
        """Create curiosity-driven action"""
        return WorldAction(
            action_id=f"curiosity_{int(time.time() * 1000)}",
            perception=[],
            decision={"type": "curiosity", "value": curiosity},
            motor_commands=[motor_command],
            goal="explore"
        )

    def _create_exploration_action(self) -> WorldAction:
        """Create default exploration action"""
        return WorldAction(
            action_id=f"explore_{int(time.time() * 1000)}",
            perception=[],
            decision={"type": "exploration"},
            motor_commands=[MotorCommand(action_type="reach", parameters={})],
            goal="explore"
        )

    def _generate_beginner_skill_action(self, skill_name: str, environment: Any) -> WorldAction:
        """Generate action for beginner skill practice"""
        return WorldAction(
            action_id=f"beginner_{skill_name}_{int(time.time() * 1000)}",
            perception=[],
            decision={"type": "skill_practice", "level": "beginner"},
            motor_commands=[MotorCommand(action_type="reach", parameters={})],
            goal=skill_name
        )

    def _generate_intermediate_skill_action(self, skill_name: str, environment: Any) -> WorldAction:
        """Generate action for intermediate skill practice"""
        return WorldAction(
            action_id=f"intermediate_{skill_name}_{int(time.time() * 1000)}",
            perception=[],
            decision={"type": "skill_practice", "level": "intermediate"},
            motor_commands=[MotorCommand(action_type="grasp", parameters={})],
            goal=skill_name
        )

    def _generate_advanced_skill_action(self, skill_name: str, environment: Any) -> WorldAction:
        """Generate action for advanced skill practice"""
        return WorldAction(
            action_id=f"advanced_{skill_name}_{int(time.time() * 1000)}",
            perception=[],
            decision={"type": "skill_practice", "level": "advanced"},
            motor_commands=[MotorCommand(action_type="push", parameters={"force": 2.0})],
            goal=skill_name
        )

    def _select_play_activity(self) -> PlayfulActivity:
        """Select age-appropriate playful activity"""
        appropriate_activities = [
            activity for activity in self.playful_activities
            if self.current_stage in activity.age_appropriate
        ]

        if appropriate_activities:
            # Select based on curiosity and learning potential
            weights = [activity.curiosity_value + activity.learning_potential
                      for activity in appropriate_activities]
            weights = np.array(weights) / sum(weights)
            return np.random.choice(appropriate_activities, p=weights)

        # Fallback to first activity
        return self.playful_activities[0]

    def _execute_play_activity(self, activity: PlayfulActivity, environment: Any) -> Experience:
        """Execute playful learning activity"""
        # Create play action
        action = WorldAction(
            action_id=f"play_{activity.name}_{int(time.time() * 1000)}",
            perception=[],
            decision={"type": "play", "activity": activity.name},
            motor_commands=[MotorCommand(
                action_type=activity.parameters.get("action", "reach"),
                parameters=activity.parameters
            )],
            goal=f"play_{activity.name}"
        )

        # Record play activity
        self.play_history.append({
            "activity": activity.name,
            "timestamp": time.time(),
            "action_id": action.action_id
        })

        # Return placeholder experience (would be executed by sensorimotor system)
        return Experience(
            action=action,
            result={"success": True, "changes": []},
            timestamp=time.time(),
            context={"play_activity": activity.name}
        )

    def _update_play_activity(self, activity: PlayfulActivity, experience: Experience):
        """Update activity based on experience"""
        if experience.success:
            activity.learning_potential *= 1.01
        else:
            activity.curiosity_value *= 1.05

    def _check_developmental_transitions(self):
        """Check for developmental stage transitions"""
        total_progress = sum(self.stage_progress.values()) / len(self.stage_progress)
        if total_progress > 0.5 and self.current_stage == DevelopmentalStage.SENSORIMOTOR:
            self._transition_to_next_stage()

class PlayfulExplorer:
    """Playful exploration and curiosity-driven learning system"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.curiosity_threshold = self.config.get('curiosity_threshold', 0.7)
        self.exploration_rate = self.config.get('exploration_rate', 0.1)
        self.play_activities = []
        self.exploration_history = []
        self.developmental_learning = DevelopmentalLearning(config)

    def explore(self, environment: Any, context: Dict[str, Any]) -> List[WorldAction]:
        """Generate playful exploration actions"""
        actions = []
        
        # Generate curiosity-driven actions
        if self._should_explore():
            playful_activity = self._select_play_activity(context)
            if playful_activity:
                action = self.developmental_learning.play(playful_activity, environment)
                actions.append(action)
        
        return actions

    def _should_explore(self) -> bool:
        """Determine if exploration should occur"""
        return np.random.rand() < self.exploration_rate

    def _select_play_activity(self, context: Dict[str, Any]) -> Optional[PlayfulActivity]:
        """Select appropriate play activity"""
        if not self.play_activities:
            self.play_activities = self._generate_default_activities()
        
        # Select activity based on curiosity value
        activities = [a for a in self.play_activities if a.curiosity_value > self.curiosity_threshold]
        if activities:
            return np.random.choice(activities)
        return None

    def _generate_default_activities(self) -> List[PlayfulActivity]:
        """Generate default playful activities"""
        return [
            PlayfulActivity(
                name="object_manipulation",
                activity_type="sensorimotor",
                parameters={"object_type": "block"},
                curiosity_value=0.8,
                learning_potential=0.7,
                age_appropriate=[DevelopmentalStage.SENSORIMOTOR]
            ),
            PlayfulActivity(
                name="pattern_exploration",
                activity_type="cognitive",
                parameters={"complexity": "simple"},
                curiosity_value=0.6,
                learning_potential=0.8,
                age_appropriate=[DevelopmentalStage.PREOPERATIONAL]
            ),
            PlayfulActivity(
                name="causal_discovery",
                activity_type="scientific",
                parameters={"experiment_type": "simple"},
                curiosity_value=0.9,
                learning_potential=0.9,
                age_appropriate=[DevelopmentalStage.CONCRETE_OPERATIONAL]
            )
        ]

    def update_exploration_success(self, action: WorldAction, outcome: Experience):
        """Update exploration based on outcome"""
        self.exploration_history.append({
            'action': action,
            'outcome': outcome,
            'success': outcome.success,
            'timestamp': outcome.timestamp
        })

        # Update play activities based on success
        for activity in self.play_activities:
            if activity.name == outcome.context.get('play_activity'):
                if outcome.success:
                    activity.learning_potential *= 1.1
                    activity.curiosity_value *= 0.95  # Decrease curiosity as we learn
                else:
                    activity.curiosity_value *= 1.1  # Increase curiosity to retry

    def get_exploration_stats(self) -> Dict[str, Any]:
        """Get exploration statistics"""
        if not self.exploration_history:
            return {'total_explorations': 0}
        
        successful_explorations = sum(1 for h in self.exploration_history if h['success'])
        return {
            'total_explorations': len(self.exploration_history),
            'successful_explorations': successful_explorations,
            'success_rate': successful_explorations / len(self.exploration_history),
            'curiosity_level': np.mean([a.curiosity_value for a in self.play_activities]),
            'learning_potential': np.mean([a.learning_potential for a in self.play_activities])
        }
