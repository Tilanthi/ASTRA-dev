"""
Causal inference methods for STAN-XI-ASTRO

This module provides simulation-based inference methods for cases where
likelihoods are intractable, which is common in astrophysics.
"""

from .simulation_based_inference import (
    SBIMethod,
    SimulatorConfig,
    SBIResult,
    SimulatorInterface,
    AstrophysicsSimulator,
    MHDSimulator,
    StarFormationSimulator,
    CosmologySimulator,
    ApproximateBayesianComputation,
    SequentialNeuralPosteriorEstimation,
    SimulationBasedInferenceEngine,
    create_sbi_engine,
    default_summary_statistics,
)

__all__ = [
    'SBIMethod',
    'SimulatorConfig',
    'SBIResult',
    'SimulatorInterface',
    'AstrophysicsSimulator',
    'MHDSimulator',
    'StarFormationSimulator',
    'CosmologySimulator',
    'ApproximateBayesianComputation',
    'SequentialNeuralPosteriorEstimation',
    'SimulationBasedInferenceEngine',
    'create_sbi_engine',
    'default_summary_statistics',
]
