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
V80 Discovery Engine - Advanced Architectural Improvements

This module implements comprehensive improvements to address STAN's limitations:

1. First Principles Discovery Module - For novel phenomena without clear analogies
2. Physics-Grounded Analogical Reasoning - Validating analogies by physical mechanisms
3. Automatic Constraint Discovery - Deriving constraints from data
4. Scalable Causal Inference - Variational Bayesian methods for large variable sets
5. Active Experimentation Engine - Hypothesis generation and autonomous testing
6. Subtle Pattern Detection - Multi-scale pattern detection across vast datasets

Author: STAN Development Team
Version: 8.0.0
Date: March 20, 2026
"""

from .first_principles_discovery import FirstPrinciplesDiscovery
from .physics_grounded_analogy import PhysicsGroundedAnalogy
from .constraint_discovery import AutomaticConstraintDiscovery
from .scalable_causal_inference import ScalableCausalInference
from .active_experimentation import ActiveExperimentationEngine
from .subtle_pattern_detection import SubtlePatternDetection
from .discovery_orchestrator import DiscoveryOrchestrator

__all__ = [
    'FirstPrinciplesDiscovery',
    'PhysicsGroundedAnalogy',
    'AutomaticConstraintDiscovery',
    'ScalableCausalInference',
    'ActiveExperimentationEngine',
    'SubtlePatternDetection',
    'DiscoveryOrchestrator',
]
