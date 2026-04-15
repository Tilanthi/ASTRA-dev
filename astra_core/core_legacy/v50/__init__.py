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
V50 Discovery Engine Module
============================

Transformative reasoning architecture with:
- Internal World Simulator
- Program Synthesis Reasoning
- Causal Discovery Engine
- Self-Improving Meta-Learner
- Multi-Agent Adversarial Debate
- Hierarchical Abstraction Learning

Version: 50.0.0
Date: 2025-12-17
"""

from .v50_discovery_engine import (
    V50DiscoveryEngine,
    V50Config,
    V50Mode,
    V50Result,
    create_v50_standard,
    create_v50_fast,
    create_v50_deep,
    create_v50_discovery,
    create_v50_gpqa
)

__all__ = [
    'V50DiscoveryEngine',
    'V50Config',
    'V50Mode',
    'V50Result',
    'create_v50_standard',
    'create_v50_fast',
    'create_v50_deep',
    'create_v50_discovery',
    'create_v50_gpqa'
]

__version__ = "50.0.0"
