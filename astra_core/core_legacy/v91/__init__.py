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
STAN V91 - Embodied Social AGI Architecture
============================================

This version implements the final bottlenecks to AGI:
- Embodied cognition with physical grounding
- Lifelong continuous learning
- Robust value alignment and ethical reasoning
- Multi-agent coordination at scale

V91 represents the most complete AGI implementation to date,
addressing all bottlenecks identified in AGI research.
"""

from .v91_system import (
    V91CompleteSystem, V91Config, V91MetacognitiveState,
    AGIReadinessLevel,
    create_v91_system, create_v91_embodied, create_v91_social, create_v91_ethical
)

from .embodied_cognition import (
    EmbodiedCognitionModule, BodySchema, SensorReading, MotorCommand, Modality
)

from .lifelong_learning import (
    ContinualLearner, KnowledgeItem, LearningTask,
    LearningStrategy, KnowledgeType
)

from .value_alignment import (
    EthicalReasoner, EthicalConstraint, Value, EthicalPrinciple
)

__version__ = "91.0.0"
__description__ = "Embodied Social AGI with Value Alignment"