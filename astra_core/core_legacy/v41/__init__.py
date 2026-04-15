# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
