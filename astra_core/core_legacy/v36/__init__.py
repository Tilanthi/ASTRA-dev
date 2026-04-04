"""
V36 Core System - Symbolic Causal Reasoning & Meta-Cognitive Scientific Discovery

This package contains all V36 core modules.
"""

from .v36_system import (
    V36CompleteSystem,
    ProhibitiveConstraintEngine,
    HybridWorldGenerator,
    DomainCompositionInference,
    DeepFalsificationEngine,
    SymbolicCausalAbstraction,
    CrossDomainAnalogyEngine,
    MechanismDiscoveryEngine
)

# Alias for backward compatibility
V36CoreSystem = V36CompleteSystem

__version__ = "36.0"
__all__ = [
    'V36CompleteSystem',
    'V36CoreSystem',
    'ProhibitiveConstraintEngine',
    'HybridWorldGenerator',
    'DomainCompositionInference',
    'DeepFalsificationEngine',
    'SymbolicCausalAbstraction',
    'CrossDomainAnalogyEngine',
    'MechanismDiscoveryEngine'
]
