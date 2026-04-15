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
V100 Simulation Components
===========================

Multi-scale simulation capabilities for astrophysical systems:

- TemporalPhysicsEngine: Time integration for differentiable physics
- UniverseSimulator: First-principles universe simulation

Author: STAN-XI ASTRO V100 Development Team
Version: 100.0.0
"""

from .temporal_physics import (
    TemporalPhysicsEngine,
    TimeIntegrationMethod,
    SimulationResult,
    TimeState,
    TimeParameters,
    create_temporal_physics_engine,
)

from .universe_simulator import (
    UniverseSimulator,
    MultiScaleSimulation,
    ScaleCoupling,
    PredictionResult,
    PhysicsDomain,
    SpatialScale,
    SimulationType,
    create_universe_simulator,
    simulate_filament_star_formation,
)

__all__ = [
    # Temporal Physics
    'TemporalPhysicsEngine',
    'TimeIntegrationMethod',
    'SimulationResult',
    'TimeState',
    'TimeParameters',
    'create_temporal_physics_engine',

    # Universe Simulator
    'UniverseSimulator',
    'MultiScaleSimulation',
    'ScaleCoupling',
    'PredictionResult',
    'PhysicsDomain',
    'SpatialScale',
    'SimulationType',
    'create_universe_simulator',
    'simulate_filament_star_formation',
]
