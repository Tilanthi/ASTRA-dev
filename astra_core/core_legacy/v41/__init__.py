"""
STAN V41 AGI-Adjacent Reasoning System

Implements advanced cognitive capabilities:
- Phase 1: Self-Reflection Module
- Phase 2: Analogical Reasoning Engine
- Phase 3: Active Information Seeking
- Phase 4: Episodic Memory System
- Phase 5: Enhanced Swarm Integration

These systems work together to enable AGI-like reasoning,
learning, and problem-solving capabilities.
"""

from .self_reflection import (
    SelfReflectionModule,
    Contradiction,
    UncertaintyExplanation,
    ConfidenceCalibrator
)

from .analogical_reasoning import (
    AnalogicalReasoner,
    ProblemStructure,
    Analogy,
    AbstractPattern,
    StructuralMapper
)

from .active_information import (
    ActiveInformationSeeker,
    KnowledgeGap,
    InformationQuery,
    KnowledgeState,
    GapAnalyzer
)

from .episodic_memory import (
    EpisodicMemory,
    Episode,
    Pattern,
    MemoryIndex,
    PatternExtractor
)

from .swarm_reasoning import (
    SwarmReasoningOrchestrator,
    ReasoningAgent,
    StigmergicSignal,
    ConsensusBuilder,
    MultiPerspectiveIntegrator
)

from .v41_system import (
    V41CompleteSystem,
    V41Config,
    V41Mode,
    create_v41_standard,
    create_v41_fast,
    create_v41_deep,
    create_v41_reflective,
    create_v41_swarm
)

__version__ = "41.0.0"
__all__ = [
    # Self-Reflection
    'SelfReflectionModule',
    'Contradiction',
    'UncertaintyExplanation',
    'ConfidenceCalibrator',

    # Analogical Reasoning
    'AnalogicalReasoner',
    'ProblemStructure',
    'Analogy',
    'AbstractPattern',
    'StructuralMapper',

    # Active Information Seeking
    'ActiveInformationSeeker',
    'KnowledgeGap',
    'InformationQuery',
    'KnowledgeState',
    'GapAnalyzer',

    # Episodic Memory
    'EpisodicMemory',
    'Episode',
    'Pattern',
    'MemoryIndex',
    'PatternExtractor',

    # Swarm Reasoning
    'SwarmReasoningOrchestrator',
    'ReasoningAgent',
    'StigmergicSignal',
    'ConsensusBuilder',
    'MultiPerspectiveIntegrator',

    # Complete System
    'V41CompleteSystem',
    'V41Config',
    'V41Mode',

    # Factory Functions
    'create_v41_standard',
    'create_v41_fast',
    'create_v41_deep',
    'create_v41_reflective',
    'create_v41_swarm'
]
