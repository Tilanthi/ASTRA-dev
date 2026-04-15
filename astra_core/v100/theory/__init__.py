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
V100 Theory Synthesis Module
"""

from .theory_synthesis import (
    TheorySynthesisEngine,
    TheoryFramework,
    EvidenceCluster,
    Evidence,
    Contradiction,
    DomainBoundary,
    Entity,
    Mechanism,
    Prediction,
    TheoryType,
    ConfidenceLevel,
    NoveltyType,
    create_theory_synthesis_engine,
    synthesize_theory,
)

__all__ = [
    'TheorySynthesisEngine',
    'TheoryFramework',
    'EvidenceCluster',
    'Evidence',
    'Contradiction',
    'DomainBoundary',
    'Entity',
    'Mechanism',
    'Prediction',
    'TheoryType',
    'ConfidenceLevel',
    'NovelType',
    'create_theory_synthesis_engine',
    'synthesize_theory',
]
