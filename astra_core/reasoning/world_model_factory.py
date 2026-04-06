"""
World Model Factory for STAN

Provides singleton instances of world models for counterfactual reasoning.
This is the missing piece that breaks counterfactual reasoning.

Date: 2025-12-11
Version: 1.0
"""

from typing import Optional, Dict, Any
from astra_core.reasoning.unified_world_model import UnifiedWorldModel, CausalGraph, CausalEdge, Belief, BeliefType, Hypothesis


# Singleton instances
_world_model: Optional[UnifiedWorldModel] = None
_integration_bus = None


def get_world_model(config: Optional[Dict[str, Any]] = None) -> UnifiedWorldModel:
    """
    Get or create the singleton world model instance.

    This is the factory function that counterfactual reasoning expects.
    """
    global _world_model

    if _world_model is None:
        _world_model = UnifiedWorldModel()

        # Initialize with basic ISM physics knowledge
        _initialize_ism_knowledge(_world_model)

    return _world_model


def _initialize_ism_knowledge(world_model: UnifiedWorldModel):
    """Initialize world model with ISM/filament physics knowledge"""

    # Add causal knowledge about filament formation
    causal_knowledge = [
        # Turbulence -> filament properties
        CausalEdge(
            edge_id="turbulence_to_width",
            cause="turbulent_velocity_dispersion",
            effect="filament_width",
            strength=0.8,
            mechanism="turbulent_cascade",
            confidence=0.9
        ),
        CausalEdge(
            edge_id="magnetic_to_width",
            cause="magnetic_field_strength",
            effect="filament_width",
            strength=0.6,
            mechanism="magnetic_support",
            confidence=0.85
        ),
        CausalEdge(
            edge_id="thermal_to_width",
            cause="thermal_pressure",
            effect="filament_width",
            strength=0.5,
            mechanism="jeans_instability",
            confidence=0.95
        ),
        # Sonic scale causality
        CausalEdge(
            edge_id="injection_to_sonic",
            cause="turbulent_injection_scale",
            effect="sonic_scale",
            strength=0.95,
            mechanism="turbulent_cascade",
            confidence=0.9
        ),
        CausalEdge(
            edge_id="sonic_to_width",
            cause="sonic_scale",
            effect="filament_width",
            strength=0.9,
            mechanism="characteristic_scale_formation",
            confidence=0.92
        ),
    ]

    for edge in causal_knowledge:
        world_model.causal_graph.add_edge(edge)

    # Add key hypothesis about Arzoumanian result
    hypothesis = Hypothesis(
        hypothesis_id="arzoumanian_2011_filament_width",
        statement="Interstellar filaments have a characteristic width of ~0.1 pc corresponding to the sonic scale of turbulence",
        confidence=0.92,
        status="active",
        evidence_for=[],  # Changed from 'evidence' to 'evidence_for'
        predictions=["Characteristic width of ~0.1 pc across diverse environments"],
        tests_performed=["Herschel observations", "Filament width measurements"]
    )

    world_model.add_hypothesis(hypothesis, notify=False)

    # Add physical constraints
    constraints = {
        "jeans_length": {
            "formula": "lambda_J = cs * sqrt(pi / (G * rho))",
            "parameters": {"cs": "sound_speed", "G": "gravitational_constant", "rho": "density"},
            "typical_value": "0.1 pc",
            "confidence": 0.95
        },
        "sonic_scale": {
            "formula": "lambda_sonic = cs^3 / (epsilon * v_injection^2)",
            "parameters": {"cs": "sound_speed", "epsilon": "energy_dissipation_rate", "v_injection": "injection_velocity"},
            "typical_value": "0.1 pc",
            "confidence": 0.9
        },
        "alfven_scale": {
            "formula": "lambda_A = v_A * L / v_injection",
            "parameters": {"v_A": "alfven_velocity", "L": "injection_scale", "v_injection": "injection_velocity"},
            "typical_value": "variable",
            "confidence": 0.85
        }
    }

    for name, constraint_data in constraints.items():
        world_model.constraints[name] = constraint_data


def reset_world_model():
    """Reset the world model (useful for testing)"""
    global _world_model
    _world_model = None
