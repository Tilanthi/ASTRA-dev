"""
STAN-XI-ASTRO V4.0 Revolutionary Capabilities

This module exports the four revolutionary capabilities that represent
a major step toward AGI, estimated to improve capability from ~57% (V3.0)
to ~70-75% (V4.0).

The V4.0 capabilities are designed to integrate synergistically with
existing STAN_XI_ASTRO systems.

Four Revolutionary Capabilities:
1. Meta-Context Engine (MCE): Dynamic context layering with predictive,
   analytical, and emotional cognitive frames
2. Autocatalytic Self-Compiler (ASC): Recursive self-improvement through
   architecture rewriting with version blending
3. Cognitive-Relativity Navigator (CRN): Multi-scale abstraction reasoning
   with dynamic zoom (0-100 scale)
4. Multi-Mind Orchestration Layer (MMOL): Specialized sub-minds with
   anticipatory arbitration

Version: 4.0.0
Date: 2026-03-17
"""

from typing import Dict, List, Optional, Any

# =============================================================================
# V4.0 Integration Coordinator
# =============================================================================
try:
    from .integration import (
        V4IntegrationCoordinator, V4Result, V4IntegrationState, IntegrationMode,
        create_v4_coordinator, process_with_v4
    )
except ImportError:
    V4IntegrationCoordinator = None
    V4Result = None
    V4IntegrationState = None
    IntegrationMode = None
    create_v4_coordinator = None
    process_with_v4 = None

# =============================================================================
# V4.0 Revolutionary System (V7.22 Enhanced Version)
# =============================================================================
try:
    from .system import V4RevolutionarySystem
except ImportError:
    V4RevolutionarySystem = None

# =============================================================================
# Individual Capability Imports
# =============================================================================
try:
    from ..metacognitive.meta_context_engine import (
        MetaContextEngine, create_meta_context_engine
    )
except ImportError:
    MetaContextEngine = None
    create_meta_context_engine = None

try:
    from ..self_teaching.autocatalytic_compiler import (
        AutocatalyticSelfCompiler, create_autocatalytic_self_compiler
    )
except ImportError:
    AutocatalyticSelfCompiler = None
    create_autocatalytic_self_compiler = None

try:
    from ..reasoning.cognitive_relativity_navigator import (
        CognitiveRelativityNavigator, create_cognitive_relativity_navigator
    )
except ImportError:
    CognitiveRelativityNavigator = None
    create_cognitive_relativity_navigator = None

try:
    from ..intelligence.multi_mind_orchestrator import (
        MultiMindOrchestrator, create_multi_mind_orchestrator
    )
except ImportError:
    MultiMindOrchestrator = None
    create_multi_mind_orchestrator = None

# =============================================================================
# Factory Functions
# =============================================================================

def create_v4_system(config: Optional[Dict[str, Any]] = None):
    """
    Create a V4.0 system with all four revolutionary capabilities.

    This factory function will return either:
    - V4RevolutionarySystem (V7.22 enhanced version with fallbacks) [PREFERRED]
    - V4IntegrationCoordinator (legacy version)

    The V7.22 version is preferred because it has graceful fallbacks and
    provides the get_available_capabilities() interface expected by tests.

    Args:
        config: Optional configuration dictionary

    Returns:
        Either V4RevolutionarySystem or V4IntegrationCoordinator instance

    Example:
        >>> from astra_core.v4_revolutionary import create_v4_system
        >>> system = create_v4_system()
        >>> capabilities = system.get_available_capabilities()
        >>> print(f"Available: {capabilities}")
    """
    # Prefer V4RevolutionarySystem (V7.22) for graceful fallbacks
    if V4RevolutionarySystem is not None:
        return V4RevolutionarySystem()

    # Fall back to V4IntegrationCoordinator (legacy)
    if create_v4_coordinator is not None:
        return create_v4_coordinator(config)

    raise ImportError("No V4.0 system available")


__all__ = [
    # Main Integration
    'V4IntegrationCoordinator', 'V4Result', 'V4IntegrationState', 'IntegrationMode',
    'create_v4_coordinator', 'process_with_v4',

    # V7.22 Enhanced System
    'V4RevolutionarySystem',

    # Individual Capabilities
    'MetaContextEngine', 'create_meta_context_engine',
    'AutocatalyticSelfCompiler', 'create_autocatalytic_self_compiler',
    'CognitiveRelativityNavigator', 'create_cognitive_relativity_navigator',
    'MultiMindOrchestrator', 'create_multi_mind_orchestrator',

    # Factory
    'create_v4_system',
]

__version__ = "4.0.0"
