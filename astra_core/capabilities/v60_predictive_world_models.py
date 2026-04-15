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
Predictive World Models Module for STAN (Capabilities Package)
=============================================================

This module re-exports the Predictive World Models classes from the
reasoning package for backward compatibility and API consistency.

Provides world modeling capabilities for physics, chemistry, biology,
and causal domains.

Date: 2025-12-17
Version: 1.0.0
"""

# Re-export from reasoning package
from astra_core.reasoning.v60_predictive_world_models import (
    ModelType,
    PredictionType,
    Observation,
    Prediction,
    PredictionError,
    ModelUpdate,
    WorldModelBase,
    PhysicsWorldModel,
    ChemistryWorldModel,
    BiologyWorldModel,
    CausalWorldModel,
    WorldModelLibrary,
    PredictiveWorldModelSystem,
)

# Aliases for V60 naming
V60ModelType = ModelType
DomainType = ModelType
V60Observation = Observation
V60Prediction = Prediction

# Factory functions
def create_world_model_system():
    """Create a predictive world model system."""
    return PredictiveWorldModelSystem()

def create_physics_model():
    """Create a physics world model."""
    return PhysicsWorldModel()

def create_chemistry_model():
    """Create a chemistry world model."""
    return ChemistryWorldModel()

def create_biology_model():
    """Create a biology world model."""
    return BiologyWorldModel()

def create_causal_model():
    """Create a causal world model."""
    return CausalWorldModel()

__all__ = [
    'PredictiveWorldModelSystem',
    'WorldModelLibrary',
    'PhysicsWorldModel',
    'ChemistryWorldModel',
    'BiologyWorldModel',
    'CausalWorldModel',
    'ModelType',
    'V60ModelType',
    'DomainType',
    'PredictionType',
    'Observation',
    'V60Observation',
    'Prediction',
    'V60Prediction',
    'create_world_model_system',
    'create_physics_model',
    'create_chemistry_model',
    'create_biology_model',
    'create_causal_model',
]
