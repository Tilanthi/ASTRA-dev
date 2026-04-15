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
V94 Complete System - Embodied Learning and Grounded Cognition Architecture

This is the complete V94 system that integrates all embodied learning components
with previous STAN versions, representing the paradigm shift from simulated
intelligence to experienced intelligence.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Callable
import logging
import time
import numpy as np

# Import V94 components
from .embodied_learning_engine import EmbodiedLearningEngine, LearningState
from .sensorimotor_system import SensorimotorInterface, WorldAction, Experience
from .developmental_learning import DevelopmentalLearning, DevelopmentalStage
from .common_sense_engine import CommonSenseEngine
from .language_grounding import LanguageGroundingEngine

# Import previous versions for integration
from ..v80 import V80CompleteSystem
from ..v91 import V91CompleteSystem
from ..v92 import V92CompleteSystem
from ..v93 import V93CompleteSystem


@dataclass
class V94Config:
    """Configuration for V94 Embodied Learning System"""
    # Embodied learning parameters
    embodied_learning_rate: float = 0.01
    curiosity_drive_strength: float = 0.8
    exploration_tendency: float = 0.7

    # Developmental learning
    developmental_stage: str = "sensorimotor"
    play_based_learning: bool = True
    social_learning_enabled: bool = True

    # Common sense parameters
    common_sense_confidence_threshold: float = 0.7
    physics_intuition_enabled: bool = True
    social_reasoning_enabled: bool = True

    # Language grounding
    language_grounding_enabled: bool = True
    multimodal_integration: bool = True
    concept_confidence_threshold: float = 0.6

    # Integration with previous versions
    v80_integration_enabled: bool = True  # Neural-symbolic
    v91_integration_enabled: bool = True  # Social AGI
    v92_integration_enabled: bool = True  # Scientific discovery
    v93_integration_enabled: bool = True  # Self-modifying

    # Performance
    max_experience_buffer_size: int = 10000
    update_frequency: float = 1.0  # Hz
    enable_parallel_processing: bool = True


class V94CompleteSystem:
    """
    Complete V94 System implementing Embodied Learning and Grounded Cognition.

    This represents the paradigm shift from simulated intelligence to
    experienced intelligence through:
    - Sensorimotor interaction with the world
    - Developmental learning through play and exploration
    - Common sense reasoning from embodied experience
    - Language grounding in real-world experiences
    - Integration with all previous STAN versions
    """

    def __init__(self, config: Optional[V94Config] = None):
        self.config = config or V94Config()
        self.logger = logging.getLogger(__name__)

        # Core V94 components
        self.embodied_engine = EmbodiedLearningEngine(self.config.__dict__)
        self.sensorimotor_system = self.embodied_engine.sensorimotor_system
        self.developmental_learning = self.embodied_engine.developmental_learning
        self.common_sense_engine = self.embodied_engine.common_sense_engine
        self.language_grounding = self.embodied_engine.language_grounding

        # Integration with previous versions
        self.previous_versions = {}
        self._initialize_previous_versions()

        # Learning state tracking
        self.learning_state = LearningState()
        self.developmental_milestones = []
        self.grounded_concepts = {}

        # Performance metrics
        self.start_time = time.time()
        self.total_interactions = 0
        self.successful_groundings = 0
        self.discovery_count = 0

        # Mode-specific configurations
        self.current_mode = "standard"
        self.mode_configurations = {
            "standard": self._get_standard_config(),
            "exploration": self._get_exploration_config(),
            "learning": self._get_learning_config(),
            "social": self._get_social_config(),
            "scientific": self._get_scientific_config()
        }
