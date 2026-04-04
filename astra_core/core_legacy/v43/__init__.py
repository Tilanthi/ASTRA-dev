"""
STAN V43 - Beyond GPT-5
========================

V43 integrates advanced reasoning techniques to surpass GPT-5.2 Pro
on graduate-level scientific reasoning benchmarks.

Key Enhancements:
- MCTS Reasoning: Monte Carlo Tree Search over reasoning paths
- Verification-Guided Search: Multi-candidate verification
- Chain-of-Verification: Self-consistency verification
- Multi-Expert Ensemble: Domain specialist routing
- Iterative Self-Critique: Generate-critique-refine loop
- Symbolic Verification: Physics/chemistry/biology constraints

Target: 95%+ on GPQA Diamond (surpassing GPT-5.2 Pro at 93.2%)
"""

from .v43_system import (
    V43CompleteSystem,
    V43Config,
    V43Mode,
    V43Result,
    create_v43_standard,
    create_v43_fast,
    create_v43_deep,
    create_v43_gpqa
)

__version__ = "43.0.0"
__all__ = [
    'V43CompleteSystem',
    'V43Config',
    'V43Mode',
    'V43Result',
    'create_v43_standard',
    'create_v43_fast',
    'create_v43_deep',
    'create_v43_gpqa'
]
