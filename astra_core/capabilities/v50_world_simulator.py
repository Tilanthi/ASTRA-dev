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
