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
V50 World Simulator - Capabilities Package Re-Export
====================================================

This module re-exports the WorldModelInterface and related classes
from the reasoning package for backward compatibility.

The actual implementation is in: astra_core/reasoning/v50_world_simulator.py

Date: 2026-03-20
Version: 1.0
"""

# Import from reasoning package
from astra_core.reasoning.v50_world_simulator import (
    WorldModelInterface,
    PhysicsEngine,
    ChemistryReactor,
    BiologicalPathwaySimulator,
    CounterfactualEngine,
    SimulationDomain,
    PhysicalState,
    ChemicalState,
    BiologicalState,
    SimulationResult,
    WorldModelQuery,
    WorldModelResponse,
    # Factory functions
    create_world_simulator,
    create_physics_engine,
    create_chemistry_reactor,
    create_biology_simulator,
    create_counterfactual_engine
)

# Re-export all
__all__ = [
    'WorldModelInterface',
    'PhysicsEngine',
    'ChemistryReactor',
    'BiologicalPathwaySimulator',
    'CounterfactualEngine',
    'SimulationDomain',
    'PhysicalState',
    'ChemicalState',
    'BiologicalState',
    'SimulationResult',
    'WorldModelQuery',
    'WorldModelResponse',
    'create_world_simulator',
    'create_physics_engine',
    'create_chemistry_reactor',
    'create_biology_simulator',
    'create_counterfactual_engine'
]
