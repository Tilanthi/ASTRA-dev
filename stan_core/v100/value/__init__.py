"""
V100 Value Components
=====================

Multi-dimensional scientific value assessment.

Author: STAN-XI ASTRO V100 Development Team
Version: 100.0.0
"""

from .scientific_value import (
    ScientificValueCalculator,
    ScientificValue,
    DiscoveryType,
    DomainImpact,
    ResourceBudget,
    ValueDimensions,
    create_scientific_value_calculator,
    assess_scientific_value,
)

__all__ = [
    'ScientificValueCalculator',
    'ScientificValue',
    'DiscoveryType',
    'DomainImpact',
    'ResourceBudget',
    'ValueDimensions',
    'create_scientific_value_calculator',
    'assess_scientific_value',
]
