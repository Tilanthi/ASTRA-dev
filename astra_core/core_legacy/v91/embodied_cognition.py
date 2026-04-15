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
Embodied Cognition Module for V91
=================================

Implements physical grounding through embodied experience:
- Proprioception and body schema
- Sensorimotor coordination
- Physical interaction learning
- Affordance perception
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class Modality(Enum):
    """Sensory modalities for embodiment"""
    VISION = "vision"
    AUDITORY = "auditory"
    TACTILE = "tactile"
    PROPRIOCEPTIVE = "proprioceptive"
    INTEROCEPTIVE = "interoceptive"
    GUSTATORY = "gustatory"
    OLFACTORY = "olfactory"


@dataclass
class SensorReading:
    """A single sensor reading with metadata"""
    modality: Modality
    data: np.ndarray
    timestamp: float = field(default_factory=time.time)
    confidence: float = 1.0
    location: Optional[str] = None  # body location


@dataclass
class MotorCommand:
    """A motor command with execution parameters"""
    action: str
    parameters: Dict[str, Any]
    duration: float
    strength: float = 1.0
    target: Optional[str] = None


class BodySchema:
    """Internal model of the body's structure and capabilities"""

    def __init__(self):
        self.body_parts = {}
        self.joint_limits = {}
        self.sensory_maps = {}
        self.motor_capabilities = {}
        self.affordances = {}

    def add_body_part(self, part_name: str, properties: Dict[str, Any]):
        """Add a body part with its properties"""
        self.body_parts[part_name] = properties

    def update_joint_limits(self, joint: str, min_angle: float, max_angle: float):
        """Update joint angle limits"""
        self.joint_limits[joint] = (min_angle, max_angle)

    def learn_affordance(self, object_type: str, actions: List[str]):
        """Learn what actions are possible with objects"""
        if object_type not in self.affordances:
            self.affordances[object_type] = []
        self.affordances[object_type].extend(actions)


class EmbodiedCognitionModule:
    """
    Implements embodied cognition through sensorimotor experience.

    This module provides:
    - Multimodal sensory integration
    - Body schema maintenance
    - Sensorimotor learning
    - Affordance perception
    - Physical intuition development
    """

    def __init__(self, num_sensors: int = 1000):
        self.num_sensors = num_sensors
        self.body_schema = BodySchema()
        self.sensory_buffer = []
        self.motor_history = []
        self.sensorimotor_patterns = {}
        self.physical_intuitions = {}

        # Initialize sensory modalities
        self.sensory_modules = {
            Modality.VISION: self._init_vision(),
            Modality.AUDITORY: self._init_auditory(),
            Modality.TACTILE: self._init_tactile(),
            Modality.PROPRIOCEPTIVE: self._init_proprioception(),
            Modality.INTEROCEPTIVE: self._init_interoception()
        }

    def _init_vision(self) -> Dict[str, Any]:
        """Initialize vision system"""
        return {
            'resolution': (640, 480),
            'fov': 120,  # degrees
            'depth_channels': True,
            'object_detection': True
        }

    def _init_auditory(self) -> Dict[str, Any]:
        """Initialize auditory system"""
        return {
            'frequency_range': (20, 20000),  # Hz
            'spatial_localization': True,
            'speech_recognition': True
        }

    def _init_tactile(self) -> Dict[str, Any]:
        """Initialize tactile system"""
        return {
            'pressure_sensors': True,
            'temperature_sensors': True,
            'texture_discrimination': True
        }

    def _init_proprioception(self) -> Dict[str, Any]:
        """Initialize proprioception (body position sense)"""
        return {
            'joint_angles': {},
            'muscle_tension': {},
            'body_configuration': {}
        }

    def _init_interoception(self) -> Dict[str, Any]:
        """Initialize interoception (internal body state)"""
        return {
            'energy_level': 1.0,
            'stress_level': 0.0,
            'pain_sensors': False,
            'homeostasis': True
        }

    def sense(self, modality: Modality, data: np.ndarray,
              location: Optional[str] = None) -> SensorReading:
        """Process sensory input"""
        reading = SensorReading(
            modality=modality,
            data=data,
            location=location
        )

        self.sensory_buffer.append(reading)

        # Update body schema based on sensory input
        self._update_body_schema(reading)

        # Learn sensorimotor patterns
        self._learn_sensorimotor_pattern(reading)

        return reading

    def _update_body_schema(self, reading: SensorReading):
        """Update internal body model from sensory feedback"""
        if reading.modality == Modality.PROPRIOCEPTIVE:
            # Update joint angles and body configuration
            if reading.location:
                self.body_schema.joint_limits[reading.location] = reading.data

        elif reading.modality == Modality.TACTILE:
            # Learn about touched objects
            if reading.location and 'pressure' in reading.data:
                # Record tactile interaction for affordance learning
                pass

    def _learn_sensorimotor_pattern(self, reading: SensorReading):
        """Learn patterns between sensory input and motor commands"""
        if self.motor_history:
            last_command = self.motor_history[-1]
            pattern_key = (reading.modality, last_command.action)

            if pattern_key not in self.sensorimotor_patterns:
                self.sensorimotor_patterns[pattern_key] = []

            self.sensorimotor_patterns[pattern_key].append({
                'sensory': reading.data,
                'motor': last_command.parameters,
                'outcome': self._evaluate_outcome(reading)
            })

    def _evaluate_outcome(self, reading: SensorReading) -> float:
        """Evaluate the outcome of a sensorimotor action"""
        # Simple heuristic based on sensory novelty and goal achievement
        novelty = np.std(reading.data) if len(reading.data) > 1 else 0
        return min(novelty, 1.0)

    def act(self, command: MotorCommand) -> bool:
        """Execute a motor command and learn from results"""
        # Simulate motor execution
        success = self._simulate_execution(command)

        if success:
            self.motor_history.append(command)

            # Update physical intuitions
            self._update_physical_intuitions(command)

        return success

    def _simulate_execution(self, command: MotorCommand) -> bool:
        """Simulate motor command execution"""
        # Check against body schema constraints
        if command.action in self.body_schema.motor_capabilities:
            capability = self.body_schema.motor_capabilities[command.action]

            # Check if within physical limits
            if 'max_strength' in capability:
                return command.strength <= capability['max_strength']

            if 'duration' in capability:
                return command.duration <= capability['duration']

        return True  # Assume success for now

    def _update_physical_intuitions(self, command: MotorCommand):
        """Update intuitions about physical world"""
        # Learn physical constraints and affordances
        if 'object' in command.parameters:
            obj = command.parameters['object']
            action = command.action

            # Learn affordance: what actions can be performed on objects
            self.body_schema.learn_affordance(obj, [action])

    def perceive_affordances(self, object_description: str) -> List[str]:
        """Perceive what actions are possible with an object"""
        # Check learned affordances
        if object_description in self.body_schema.affordances:
            return self.body_schema.affordances[object_description]

        # Infer affordances from object properties
        affordances = []

        if 'graspable' in object_description:
            affordances.extend(['grasp', 'hold', 'lift'])

        if 'container' in object_description:
            affordances.extend(['open', 'close', 'pour_from', 'pour_into'])

        if 'movable' in object_description:
            affordances.extend(['push', 'pull', 'slide'])

        return affordances

    def develop_physical_intuition(self, observations: List[Dict[str, Any]]):
        """Develop intuition about physical laws from experience"""
        for obs in observations:
            if 'objects' in obs and 'interactions' in obs:
                # Learn about gravity, momentum, etc.
                self._learn_physics(obs)

    def _learn_physics(self, observation: Dict[str, Any]):
        """Learn physics principles from observation"""
        # Extract physical relationships
        for interaction in observation.get('interactions', []):
            if 'collision' in interaction:
                # Learn conservation of momentum
                self.physical_intuitions['momentum_conservation'] = True

            if 'falling' in interaction:
                # Learn gravity
                self.physical_intuitions['gravity'] = True

    def get_embodied_state(self) -> Dict[str, Any]:
        """Get current embodied state"""
        return {
            'body_schema': {
                'num_parts': len(self.body_schema.body_parts),
                'joint_limits': len(self.body_schema.joint_limits),
                'learned_affordances': len(self.body_schema.affordances)
            },
            'sensorimotor_patterns': len(self.sensorimotor_patterns),
            'physical_intuitions': list(self.physical_intuitions.keys()),
            'sensory_buffer_size': len(self.sensory_buffer),
            'motor_commands': len(self.motor_history)
        }