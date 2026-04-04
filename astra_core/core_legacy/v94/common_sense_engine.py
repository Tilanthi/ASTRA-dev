"""
Common Sense Engine - Intuitive understanding of physical and social world

This implements common sense reasoning that humans develop through embodied experience,
including intuitive physics, social reasoning, and everyday knowledge about how the world works.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
import logging
from enum import Enum

from .sensorimotor_system import Experience, SensoryInput


class CommonSenseDomain(Enum):
    """Domains of common sense knowledge"""
    PHYSICS = "physics"
    PSYCHOLOGY = "psychology"
    SOCIAL = "social"
    SPATIAL = "spatial"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    MATERIAL = "material"


@dataclass
class CommonSenseRule:
    """Common sense rule about the world"""
    domain: CommonSenseDomain
    condition: str
    consequence: str
    confidence: float = 1.0
    experience_count: int = 0
    violations: int = 0

    def update_confidence(self, success: bool):
        """Update confidence based on experience"""
        self.experience_count += 1
        if not success:
            self.violations += 1

        # Update confidence using Bayesian updating
        prior = self.confidence
        likelihood = 0.9 if success else 0.1
        self.confidence = (prior * likelihood) / ((prior * likelihood) + ((1 - prior) * (1 - likelihood)))


@dataclass
class PhysicalIntuition:
    """Intuitive understanding of physical laws"""
    gravity_direction: np.ndarray = field(default_factory=lambda: np.array([0, -1, 0]))
    support_relation: bool = True  # Objects need support
    container_containment: bool = True  # Containers hold things
    solidity: bool = True  # Objects can't pass through each other
    continuity: bool = True  # Objects move continuously
    persistence: bool = True  # Objects continue to exist when unseen

    def predict_fall(self, object_pos: np.ndarray, support_surface: Optional[float] = None) -> bool:
        """Predict if object will fall"""
        if support_surface is None:
            return True
        return object_pos[1] <= support_surface

    def predict_collision(self, obj1_pos: np.ndarray, obj1_size: float,
                         obj2_pos: np.ndarray, obj2_size: float) -> bool:
        """Predict if objects will collide"""
        distance = np.linalg.norm(obj1_pos - obj2_pos)
        return distance < (obj1_size + obj2_size)


@dataclass
class SocialIntuition:
    """Intuitive understanding of social situations"""
    theory_of_mind: bool = True  # Others have beliefs and desires
    emotions: bool = True  # Others experience emotions
    intentions: bool = True  # Others act with intentions
    cooperation: bool = True  # People often cooperate
    fairness: bool = True  # People care about fairness

    def predict_emotional_response(self, action: str, context: Dict) -> str:
        """Predict emotional response to action"""
        # Simplified emotional prediction
        if action == "help":
            return "gratitude"
        elif action == "harm":
            return "anger"
        elif action == "share":
            return "happiness"
        else:
            return "neutral"


@dataclass
class WorldScenario:
    """Description of a world scenario for common sense reasoning"""
    objects: List[Dict[str, Any]]
    agents: List[Dict[str, Any]]
    environment: Dict[str, Any]
    initial_state: Dict[str, Any]
    actions: List[str]


class PhysicsIntuitionModule:
    """Module for intuitive physics reasoning"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.physics_intuition = PhysicalIntuition()
        self.material_properties = {}  # Material -> properties mapping
        self.force_predictions = {}
        self.mechanical_knowledge = {}

    def predict_motion(self, object_state: Dict, forces: List[Dict], time_horizon: float = 1.0) -> Dict:
        """Predict object motion under forces"""
        # Simplified physics prediction
        position = np.array(object_state.get("position", [0, 0, 0]))
        velocity = np.array(object_state.get("velocity", [0, 0, 0]))
        mass = object_state.get("mass", 1.0)

        # Apply forces (simplified)
        total_force = np.zeros(3)
        for force in forces:
            force_vec = np.array(force.get("vector", [0, 0, 0]))
            total_force += force_vec

        # Add gravity
        gravity_force = np.array([0, -9.81 * mass, 0])
        total_force += gravity_force

        # Update velocity and position
        acceleration = total_force / mass
        new_velocity = velocity + acceleration * time_horizon
        new_position = position + new_velocity * time_horizon

        return {
            "position": new_position.tolist(),
            "velocity": new_velocity.tolist(),
            "acceleration": acceleration.tolist(),
            "confidence": 0.8
        }

    def predict_stability(self, object_config: Dict) -> Dict[str, float]:
        """Predict if configuration is stable"""
        # Simplified stability prediction
        stability_score = 0.5  # Base uncertainty

        # Check for support
        if "support" in object_config:
            stability_score += 0.3

        # Check center of mass
        if "center_of_mass" in object_config:
            stability_score += 0.2

        return {
            "stability": np.clip(stability_score, 0.0, 1.0),
            "tipping_risk": 1.0 - stability_score
        }

    def predict_collision_outcome(self, obj1: Dict, obj2: Dict, collision_velocity: float) -> Dict:
        """Predict outcome of collision"""
        # Simplified collision prediction
        mass1 = obj1.get("mass", 1.0)
        mass2 = obj2.get("mass", 1.0)

        # Conservation of momentum (simplified)
        if mass1 > mass2:
            return {
                "obj1_outcome": "continues",
                "obj2_outcome": "moves_with_obj1",
                "damage_probability": 0.1
            }
        else:
            return {
                "obj1_outcome": "bounces_back",
                "obj2_outcome": "slightly_moves",
                "damage_probability": 0.3
            }


class SocialReasoningModule:
    """Module for social common sense reasoning"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.social_intuition = SocialIntuition()
        self.social_norms = {}
        self.relationship_models = {}
        self.emotion_predictions = {}

    def predict_social_response(self, action: str, agent: Dict, context: Dict) -> Dict:
        """Predict social response to action"""
        # Consider agent's personality
        personality = agent.get("personality", "neutral")

        # Base response
        response = {"action": action, "agent": agent.get("id", "unknown")}

        # Adjust based on personality
        if personality == "friendly":
            response["emotional_response"] = "positive"
            response["cooperation_probability"] = 0.8
        elif personality == "aggressive":
            response["emotional_response"] = "negative"
            response["cooperation_probability"] = 0.2
        else:
            response["emotional_response"] = "neutral"
            response["cooperation_probability"] = 0.5

        # Consider social norms
        if self._violates_social_norms(action, context):
            response["social_approval"] = "low"
            response["cooperation_probability"] *= 0.5

        return response

    def infer_intentions(self, agent: Dict, actions: List[str], context: Dict) -> Dict:
        """Infer agent's intentions from actions"""
        intentions = {}

        # Simple intention inference
        if any("help" in action for action in actions):
            intentions["helpful"] = 0.8
        if any("take" in action for action in actions):
            intentions["selfish"] = 0.7
        if any("share" in action for action in actions):
            intentions["cooperative"] = 0.9

        return intentions

    def predict_group_dynamics(self, agents: List[Dict], situation: Dict) -> Dict:
        """Predict group dynamics in social situation"""
        # Count personality types
        friendly_count = sum(1 for a in agents if a.get("personality") == "friendly")
        aggressive_count = sum(1 for a in agents if a.get("personality") == "aggressive")

        # Predict group outcome
        if friendly_count > aggressive_count:
            return {
                "group_cohesion": "high",
                "cooperation_probability": 0.8,
                "conflict_probability": 0.1
            }
        elif aggressive_count > friendly_count:
            return {
                "group_cohesion": "low",
                "cooperation_probability": 0.3,
                "conflict_probability": 0.7
            }
        else:
            return {
                "group_cohesion": "medium",
                "cooperation_probability": 0.5,
                "conflict_probability": 0.4
            }

    def _violates_social_norms(self, action: str, context: Dict) -> bool:
        """Check if action violates social norms"""
        # Simplified social norm checking
        violations = ["steal", "harm", "deceive"]
        return any(violation in action for violation in violations)


class CommonSenseEngine:
    """
    Common sense reasoning engine for intuitive understanding of the world.

    This provides the common sense knowledge that humans develop through
    embodied experience with the physical and social world.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Core modules
        self.physics_module = PhysicsIntuitionModule()
        self.social_module = SocialReasoningModule()

        # Common sense knowledge base
        self.rules: List[CommonSenseRule] = []
        self.experience_memory: List[Experience] = []
        self.conceptual_knowledge: Dict[str, Any] = {}

        # Initialize common sense rules
        self._initialize_common_sense_rules()

        # Learning rates
        self.rule_learning_rate = 0.1
        self.concept_learning_rate = 0.05

        self.logger.info("Common sense engine initialized")

    def _initialize_common_sense_rules(self):
        """Initialize basic common sense rules"""
        # Physics rules
        self.rules.append(CommonSenseRule(
            domain=CommonSenseDomain.PHYSICS,
            condition="object_falls_without_support",
            consequence="object_hits_ground",
            confidence=0.95
        ))

        self.rules.append(CommonSenseRule(
            domain=CommonSenseDomain.PHYSICS,
            condition="push_heavy_object",
            consequence="object_moves_slowly",
            confidence=0.8
        ))

        # Social rules
        self.rules.append(CommonSenseRule(
            domain=CommonSenseDomain.SOCIAL,
            condition="help_someone",
            consequence="they_appreciate_it",
            confidence=0.9
        ))

        self.rules.append(CommonSenseRule(
            domain=CommonSenseDomain.SOCIAL,
            condition="share_resources",
            consequence="social_bond_strengthens",
            confidence=0.85
        ))

        # Spatial rules
        self.rules.append(CommonSenseRule(
            domain=CommonSenseDomain.SPATIAL,
            condition="container_upside_down",
            consequence="contents_fall_out",
            confidence=0.95
        ))

    def predict_outcome(self, scenario: Union[Dict, WorldScenario]) -> Dict[str, float]:
        """
        Predict outcome of scenario using common sense reasoning.

        This is the core method that provides intuitive predictions about
        how the world works based on common sense knowledge.
        """
        if isinstance(scenario, dict):
            scenario = self._dict_to_scenario(scenario)

        predictions = {}

        # Physics predictions
        physics_predictions = self._predict_physics_outcomes(scenario)
        predictions.update(physics_predictions)

        # Social predictions
        if scenario.agents:
            social_predictions = self._predict_social_outcomes(scenario)
            predictions.update(social_predictions)

        # General common sense predictions
        general_predictions = self._predict_general_outcomes(scenario)
        predictions.update(general_predictions)

        return predictions

    def update_from_experience(self, experience: Experience):
        """Update common sense knowledge from experience"""
        # Add to experience memory
        self.experience_memory.append(experience)

        # Update relevant rules
        self._update_relevant_rules(experience)

        # Update conceptual knowledge
        self._update_conceptual_knowledge(experience)

        # Limit memory size
        if len(self.experience_memory) > 10000:
            self.experience_memory = self.experience_memory[-5000:]

    def evaluate_common_sense(self, statement: str, context: Dict) -> Dict[str, float]:
        """Evaluate if statement makes common sense"""
        evaluation = {
            "plausibility": 0.5,
            "confidence": 0.0,
            "violated_rules": [],
            "supporting_rules": []
        }

        # Check against rules
        for rule in self.rules:
            if self._rule_applies_to_statement(rule, statement):
                if rule.confidence > 0.7:
                    evaluation["plausibility"] += 0.1 * rule.confidence
                    evaluation["supporting_rules"].append(rule.condition)
                else:
                    evaluation["plausibility"] -= 0.1 * (1 - rule.confidence)
                    evaluation["violated_rules"].append(rule.condition)

        # Normalize plausibility
        evaluation["plausibility"] = np.clip(evaluation["plausibility"], 0.0, 1.0)
        evaluation["confidence"] = len(evaluation["supporting_rules"]) / (len(evaluation["supporting_rules"]) + len(evaluation["violated_rules"]) + 1)

        return evaluation

    def learn_common_sense_rule(self, condition: str, consequence: str, domain: CommonSenseDomain):
        """Learn new common sense rule from experience"""
        new_rule = CommonSenseRule(
            domain=domain,
            condition=condition,
            consequence=consequence,
            confidence=0.5  # Start with low confidence
        )

        self.rules.append(new_rule)
        self.logger.info(f"Learned new common sense rule: {condition} -> {consequence}")

    def get_common_sense_status(self) -> Dict[str, Any]:
        """Get comprehensive common sense knowledge status"""
        return {
            "total_rules": len(self.rules),
            "rules_by_domain": {
                domain.value: len([r for r in self.rules if r.domain == domain])
                for domain in CommonSenseDomain
            },
            "experience_count": len(self.experience_memory),
            "average_rule_confidence": np.mean([r.confidence for r in self.rules]) if self.rules else 0.0,
            "conceptual_knowledge_size": len(self.conceptual_knowledge)
        }

    # Private methods

    def _dict_to_scenario(self, scenario_dict: Dict) -> WorldScenario:
        """Convert dictionary to WorldScenario"""
        return WorldScenario(
            objects=scenario_dict.get("objects", []),
            agents=scenario_dict.get("agents", []),
            environment=scenario_dict.get("environment", {}),
            initial_state=scenario_dict.get("initial_state", {}),
            actions=scenario_dict.get("actions", [])
        )

    def _predict_physics_outcomes(self, scenario: WorldScenario) -> Dict[str, float]:
        """Predict physics-based outcomes"""
        predictions = {}

        for obj in scenario.objects:
            # Check for falling
            if "position" in obj:
                pos = np.array(obj["position"])
                if self.physics_module.physics_intuition.predict_fall(pos):
                    predictions[f"{obj.get('id', 'object')}_will_fall"] = 0.9

            # Check stability
            stability = self.physics_module.predict_stability(obj)
            predictions[f"{obj.get('id', 'object')}_stability"] = stability["stability"]

        return predictions

    def _predict_social_outcomes(self, scenario: WorldScenario) -> Dict[str, float]:
        """Predict social outcomes"""
        predictions = {}

        if len(scenario.agents) > 1:
            # Predict group dynamics
            dynamics = self.social_module.predict_group_dynamics(scenario.agents, scenario.environment)
            predictions["cooperation_probability"] = dynamics["cooperation_probability"]
            predictions["conflict_probability"] = dynamics["conflict_probability"]

        # Individual agent responses
        for agent in scenario.agents:
            for action in scenario.actions:
                response = self.social_module.predict_social_response(action, agent, scenario.environment)
                predictions[f"{agent.get('id', 'agent')}_response_to_{action}"] = response.get("cooperation_probability", 0.5)

        return predictions

    def _predict_general_outcomes(self, scenario: WorldScenario) -> Dict[str, float]:
        """Predict general outcomes using common sense rules"""
        predictions = {}

        for rule in self.rules:
            if self._rule_applies_to_scenario(rule, scenario):
                outcome_key = f"rule_{rule.condition}_{rule.consequence}"
                predictions[outcome_key] = rule.confidence

        return predictions

    def _rule_applies_to_scenario(self, rule: CommonSenseRule, scenario: WorldScenario) -> bool:
        """Check if rule applies to scenario"""
        # Simplified rule application
        condition = rule.condition.lower()
        scenario_str = str(scenario).lower()

        return condition in scenario_str

    def _rule_applies_to_statement(self, rule: CommonSenseRule, statement: str) -> bool:
        """Check if rule applies to statement"""
        return rule.condition.lower() in statement.lower()

    def _update_relevant_rules(self, experience: Experience):
        """Update rules based on experience"""
        for rule in self.rules:
            if self._experience_relevant_to_rule(experience, rule):
                # Determine if rule was successful
                success = self._evaluate_rule_success(experience, rule)
                rule.update_confidence(success)

    def _experience_relevant_to_rule(self, experience: Experience, rule: CommonSenseRule) -> bool:
        """Check if experience is relevant to rule"""
        experience_str = f"{experience.action.goal} {str(experience.result)}".lower()
        return rule.condition.lower() in experience_str

    def _evaluate_rule_success(self, experience: Experience, rule: CommonSenseRule) -> bool:
        """Evaluate if rule correctly predicted experience"""
        # Simplified evaluation
        return experience.success

    def _update_conceptual_knowledge(self, experience: Experience):
        """Update conceptual knowledge from experience"""
        # Extract concepts from experience
        concepts = self._extract_concepts(experience)

        for concept in concepts:
            if concept not in self.conceptual_knowledge:
                self.conceptual_knowledge[concept] = {"experience_count": 0, "confidence": 0.0}

            # Update concept
            self.conceptual_knowledge[concept]["experience_count"] += 1
            if experience.success:
                self.conceptual_knowledge[concept]["confidence"] += self.concept_learning_rate

            # Clip confidence
            self.conceptual_knowledge[concept]["confidence"] = np.clip(
                self.conceptual_knowledge[concept]["confidence"], 0.0, 1.0
            )

    def _extract_concepts(self, experience: Experience) -> List[str]:
        """Extract concepts from experience"""
        concepts = []

        # Extract from goal
        concepts.extend(experience.action.goal.split())

        # Extract from context
        if "objects" in experience.context:
            concepts.extend(experience.context["objects"])

        return [c for c in concepts if len(c) > 2]  # Filter out short terms