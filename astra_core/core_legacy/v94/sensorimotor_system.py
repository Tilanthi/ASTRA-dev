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
Sensorimotor System - Interface for embodied interaction with the world

This system provides the bridge between abstract reasoning and physical interaction,
enabling the system to learn through sensorimotor experience.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
import logging
from enum import Enum

# Virtual simulation dependencies (would be real hardware in production)
try:
    import pygame
    import pymunk  # Physics engine
    PHYSICS_AVAILABLE = True
    logging.info("Physics engines (pygame, pymunk) successfully loaded")
except ImportError:
    PHYSICS_AVAILABLE = False
    # Only show warning if explicitly needed, not on general import
    pass


class ModalityType(Enum):
    """Types of sensory modalities"""
    VISION = "vision"
    AUDIO = "audio"
    TOUCH = "touch"
    PROPRIOCEPTION = "proprioception"
    CHEMICAL = "chemical"
    TEMPERATURE = "temperature"


@dataclass
class SensoryInput:
    """Structured sensory input from the environment"""
    modality: ModalityType
    data: np.ndarray
    timestamp: float
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MotorCommand:
    """Motor command for physical interaction"""
    action_type: str
    parameters: Dict[str, Any]
    target: Optional[Tuple[float, float, float]] = None
    duration: float = 1.0
    force: float = 1.0


@dataclass
class WorldAction:
    """Complete action combining perception, decision, and motor execution"""
    action_id: str
    perception: List[SensoryInput]
    decision: Dict[str, Any]
    motor_commands: List[MotorCommand]
    goal: str
    confidence: float = 1.0


@dataclass
class ActionResult:
    """Result of executing an action in the world"""
    success: bool
    sensory_feedback: List[SensoryInput]
    physical_changes: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class Experience:
    """Complete experience record for learning"""
    action: WorldAction
    result: ActionResult
    timestamp: float
    context: Dict[str, Any]
    success: bool = True

    def __post_init__(self):
        if isinstance(self.result, dict):  # Handle legacy format
            self.success = self.result.get("success", True)
            self.result = ActionResult(
                success=self.success,
                sensory_feedback=[],
                physical_changes=self.result
            )


class VirtualEnvironment:
    """Virtual environment for embodied learning simulation"""

    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.objects: List[Dict] = []
        self.physics_space = None

        if PHYSICS_AVAILABLE:
            self.physics_space = pymunk.Space()
            self.physics_space.gravity = (0, 981)  # Earth gravity

        self._initialize_environment()

    def _initialize_environment(self):
        """Initialize virtual environment with objects"""
        # Add ground
        if self.physics_space:
            ground = pymunk.Segment(self.physics_space.static_body, (0, self.height), (self.width, self.height), 5)
            ground.friction = 1.0
            self.physics_space.add(ground)

        # Add some objects
        self.objects = [
            {"type": "box", "pos": [400, 300], "size": [50, 50], "color": "red", "mass": 1},
            {"type": "sphere", "pos": [200, 200], "radius": 25, "color": "blue", "mass": 0.5},
            {"type": "box", "pos": [600, 400], "size": [30, 30], "color": "green", "mass": 0.8}
        ]

    def get_state(self) -> Dict[str, Any]:
        """Get current state of environment"""
        return {
            "objects": self.objects.copy(),
            "timestamp": time.time()
        }

    def apply_action(self, action: MotorCommand) -> Dict[str, Any]:
        """Apply motor command to environment"""
        # Simplified physics simulation
        result = {"success": True, "changes": []}

        if action.action_type == "push":
            # Find nearest object and apply force
            if self.objects:
                target = self.objects[0]  # Simplified
                target["pos"][0] += action.parameters.get("force", 10) * action.force
                result["changes"].append({"object": target, "change": "moved"})

        elif action.action_type == "grasp":
            # Attempt to grasp object
            if self.objects:
                target = self.objects[0]
                result["changes"].append({"object": target, "change": "grasped"})

        return result

    def get_sensory_feedback(self) -> List[SensoryInput]:
        """Get sensory input from environment"""
        feedback = []

        # Visual feedback
        visual_data = np.array(self.objects)  # Simplified
        feedback.append(SensoryInput(
            modality=ModalityType.VISION,
            data=visual_data,
            timestamp=time.time()
        ))

        # Proprioceptive feedback
        feedback.append(SensoryInput(
            modality=ModalityType.PROPRIOCEPTION,
            data=np.array([0.0, 0.0, 0.0]),  # Body position
            timestamp=time.time()
        ))

        return feedback


class SensorimotorInterface:
    """
    Interface for sensorimotor interaction with the world.

    This bridges the gap between abstract reasoning and physical interaction,
    enabling embodied learning through experience.
    """

    def __init__(self, environment: Optional[VirtualEnvironment] = None):
        self.logger = logging.getLogger(__name__)
        self.environment = environment or VirtualEnvironment()

        # Sensory processing
        self.sensory_processors: Dict[ModalityType, Any] = {}
        self._initialize_sensory_processors()

        # Motor execution
        self.motor_capabilities = {
            "reach": True,
            "grasp": True,
            "push": True,
            "lift": True,
            "rotate": True
        }

        # Body schema (internal model of body)
        self.body_schema = {
            "arm_length": 1.0,
            "reach_radius": 0.8,
            "max_force": 10.0,
            "precision": 0.01
        }

        # Sensorimotor memory
        self.action_history: List[WorldAction] = []
        self.perceptual_memory: List[SensoryInput] = []

        self.logger.info("Sensorimotor interface initialized")

    def _initialize_sensory_processors(self):
        """Initialize processors for different sensory modalities"""
        # Vision processor
        self.sensory_processors[ModalityType.VISION] = self._process_visual_input

        # Audio processor
        self.sensory_processors[ModalityType.AUDIO] = self._process_audio_input

        # Touch processor
        self.sensory_processors[ModalityType.TOUCH] = self._process_touch_input

        # Proprioception processor
        self.sensory_processors[ModalityType.PROPRIOCEPTION] = self._process_proprioceptive_input

    def execute(self, action: WorldAction) -> ActionResult:
        """
        Execute a complete action in the world.

        Args:
            action: Action to execute

        Returns:
            Result of the action execution
        """
        # Process sensory input for the action
        sensory_state = self.process_input(action.sensory_data)

        # Execute the motor command
        motor_output = self.motor_system.execute_command(action.motor_command)

        # Update internal state
        self.update_state(sensory_state, motor_output)

        return ActionResult(
            success=True,
            sensory_state=sensory_state,
            motor_output=motor_output
        )

    def update_state(self, sensory_state: SensoryState, motor_output: MotorOutput):
        """Update internal state based on sensory and motor information."""
        self.current_sensory_state = sensory_state
        self.current_motor_output = motor_output
