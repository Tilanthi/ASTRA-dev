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
STAN V42 Enhanced Reasoning System
===================================

Integrates all GPQA-optimized improvements:
- Test-Time Search (beam search over reasoning paths)
- Adaptive Compute (dynamic resource allocation)
- Enhanced Self-Consistency (diverse strategy voting)
- Step-wise Retrieval (RAISE-style fact retrieval)
- Contrastive Explanation (why wrong answers are wrong)
- GPQA Domain Strategies (domain-specific optimization)
- Enhanced Math Engine (symbolic + numerical)

Target: 90%+ on GPQA Diamond (up from 76.8%)
"""

from .v42_system import (
    V42CompleteSystem,
    V42Config,
    V42Mode,
    create_v42_standard,
    create_v42_fast,
    create_v42_deep,
    create_v42_gpqa
)

__version__ = "42.0.0"
__all__ = [
    'V42CompleteSystem',
    'V42Config',
    'V42Mode',
    'create_v42_standard',
    'create_v42_fast',
    'create_v42_deep',
    'create_v42_gpqa'
]
