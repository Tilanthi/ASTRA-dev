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
V36 Core System - Symbolic Causal Reasoning & Meta-Cognitive Scientific Discovery

This package contains all V36 core modules.
"""

from .v36_system import (
    V36CompleteSystem,
    ProhibitiveConstraintEngine,
    HybridWorldGenerator,
    DomainCompositionInference,
    DeepFalsificationEngine,
    SymbolicCausalAbstraction,
    CrossDomainAnalogyEngine,
    MechanismDiscoveryEngine
)

# Alias for backward compatibility
V36CoreSystem = V36CompleteSystem

__version__ = "36.0"
__all__ = [
    'V36CompleteSystem',
    'V36CoreSystem',
    'ProhibitiveConstraintEngine',
    'HybridWorldGenerator',
    'DomainCompositionInference',
    'DeepFalsificationEngine',
    'SymbolicCausalAbstraction',
    'CrossDomainAnalogyEngine',
    'MechanismDiscoveryEngine'
]
