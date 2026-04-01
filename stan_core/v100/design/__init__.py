"""
V100 Design Components
======================

Bayesian experimental design for optimal observation planning.

Author: STAN-XI ASTRO V100 Development Team
Version: 100.0.0
"""

from .bayesian_design import (
    BayesianExperimentalDesigner,
    ObservationSequence,
    ObservationPlan,
    InformationGain,
    ValueOfInformation,
    PosteriorDistribution,
    Theory,
    UtilityType,
    create_bayesian_designer,
    design_optimal_observations,
)

__all__ = [
    'BayesianExperimentalDesigner',
    'ObservationSequence',
    'ObservationPlan',
    'InformationGain',
    'ValueOfInformation',
    'PosteriorDistribution',
    'Theory',
    'UtilityType',
    'create_bayesian_designer',
    'design_optimal_observations',
]
