"""
V38 Enhanced: Complete STAN System with All Enhancement Modules

Extends V37 with:
- Bayesian Inference (+uncertainty quantification)
- Self-Consistency Engine (+3-5% accuracy)
- Expanded MORK Ontology (+2-3% accuracy)
- Tool Integration (+5-8% accuracy)
- Local RAG (+5-8% accuracy)

Total expected improvement: +15-24% accuracy

Date: 2025-12-10
Version: 38.0
"""

from .v38_system import V38CompleteSystem

# Re-export V37 for convenience
from ..v37 import V37CompleteSystem

# Alias for backward compatibility
V38EnhancedSystem = V38CompleteSystem

__version__ = "38.0"

__all__ = [
    'V38CompleteSystem',
    'V38EnhancedSystem',
    'V37CompleteSystem'
]
