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
V100 Core Components
====================

Core V100 components for autonomous scientific discovery:

- V100DiscoveryEngine: Main unified system
- ValidationEngine: Theory validation and paper generation
- TheoryCompetitionEngine: Multi-theory competition
- HumanInterfaceManager: Human-AI collaboration

Author: STAN-XI ASTRO V100 Development Team
Version: 100.0.0
"""

from .v100_system import (
    V100DiscoveryEngine,
    V100Config,
    V100SystemState,
    DiscoveryCycle,
    DiscoveryPhase,
    SystemMode,
    StoppingCriterion,
    create_v100_system,
    discover_autonomously,
)

from .validation import (
    ValidationEngine,
    ValidationResult,
    ValidationStatus,
    PredictionTest,
    ScientificPaper,
    PaperSection,
    create_validation_engine,
    validate_on_cygnus,
)

from .competition import (
    TheoryCompetitionEngine,
    CompetitionResult,
    TheoryScore,
    TheoryComparison,
    CompetitionStrategy,
    SelectionCriterion,
    create_competition_engine,
    compete_theories,
)

from .human_interface import (
    HumanInterfaceManager,
    CollaborationSession,
    HumanFeedback,
    ExpertKnowledge,
    InteractionMode,
    FeedbackType,
    FeedbackChannel,
    create_human_interface,
    collaborate_with_human,
)

__all__ = [
    # Main system
    'V100DiscoveryEngine',
    'V100Config',
    'V100SystemState',
    'DiscoveryCycle',
    'DiscoveryPhase',
    'SystemMode',
    'StoppingCriterion',
    'create_v100_system',
    'discover_autonomously',

    # Validation
    'ValidationEngine',
    'ValidationResult',
    'ValidationStatus',
    'PredictionTest',
    'ScientificPaper',
    'PaperSection',
    'create_validation_engine',
    'validate_on_cygnus',

    # Competition
    'TheoryCompetitionEngine',
    'CompetitionResult',
    'TheoryScore',
    'TheoryComparison',
    'CompetitionStrategy',
    'SelectionCriterion',
    'create_competition_engine',
    'compete_theories',

    # Human Interface
    'HumanInterfaceManager',
    'CollaborationSession',
    'HumanFeedback',
    'ExpertKnowledge',
    'InteractionMode',
    'FeedbackType',
    'FeedbackChannel',
    'create_human_interface',
    'collaborate_with_human',
]
