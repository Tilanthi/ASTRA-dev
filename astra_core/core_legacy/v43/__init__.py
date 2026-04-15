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
