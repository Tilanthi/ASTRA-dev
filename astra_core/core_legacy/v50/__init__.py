"""
V50 Discovery Engine Module
============================

Transformative reasoning architecture with:
- Internal World Simulator
- Program Synthesis Reasoning
- Causal Discovery Engine
- Self-Improving Meta-Learner
- Multi-Agent Adversarial Debate
- Hierarchical Abstraction Learning

Version: 50.0.0
Date: 2025-12-17
"""

from .v50_discovery_engine import (
    V50DiscoveryEngine,
    V50Config,
    V50Mode,
    V50Result,
    create_v50_standard,
    create_v50_fast,
    create_v50_deep,
    create_v50_discovery,
    create_v50_gpqa
)

__all__ = [
    'V50DiscoveryEngine',
    'V50Config',
    'V50Mode',
    'V50Result',
    'create_v50_standard',
    'create_v50_fast',
    'create_v50_deep',
    'create_v50_discovery',
    'create_v50_gpqa'
]

__version__ = "50.0.0"
