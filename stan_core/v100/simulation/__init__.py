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
