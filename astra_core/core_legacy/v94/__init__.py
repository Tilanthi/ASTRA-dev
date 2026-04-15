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
STAN V94: Embodied Learning and Grounded Cognition Architecture (ASTRO Version)

This module implements the paradigm shift from simulated intelligence to experienced intelligence
through embodied learning, sensorimotor integration, and grounded cognition.
Enhanced for astrophysics applications with cosmic-scale embodied understanding.
"""

from .embodied_learning_engine import EmbodiedLearningEngine
from .sensorimotor_system import SensorimotorInterface, WorldAction, Experience
from .developmental_learning import DevelopmentalLearning, PlayfulExplorer
from .common_sense_engine import CommonSenseEngine, PhysicsIntuitionModule
from .language_grounding import LanguageGroundingEngine, ConceptGroundingEngine
from .v94_complete import V94CompleteSystem, V94Config
from .astro_embodied_integration import AstroEmbodiedIntegrator

__all__ = [
    'EmbodiedLearningEngine',
    'SensorimotorInterface',
    'WorldAction',
    'Experience',
    'DevelopmentalLearning',
    'PlayfulExplorer',
    'CommonSenseEngine',
    'PhysicsIntuitionModule',
    'LanguageGroundingEngine',
    'ConceptGroundingEngine',
    'V94CompleteSystem',
    'V94Config',
    'AstroEmbodiedIntegrator'
]