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
STAN Core Systems for Astro (V36-V93)
====================================

Versions:
- V50: Discovery Engine
- V90-V92: Consciousness, Embodiment, Scientific Discovery
- V93: Recursive Self-Modifying Metacognitive Architecture
"""

import logging

# V50 Discovery Engine (primary system)
try:
    from .v50 import (
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
    _V50_AVAILABLE = True
except Exception as e:
    logging.warning(f"V50 import failed: {type(e).__name__}: {e}")
    _V50_AVAILABLE = False

# V80 Grounded Neural-Symbolic Architecture
try:
    from .v80 import (
        V80CompleteSystem, V80Config, V80System,
        create_v80_standard, create_v80_fast, create_v80_deep
    )
    _V80_AVAILABLE = True
except Exception as e:
    logging.warning(f"V80 import failed: {type(e).__name__}: {e}")
    _V80_AVAILABLE = False

# V90 Metacognitive Architecture
try:
    from .v90 import (
        V90CompleteSystem, V90Config, V90MetacognitiveState,
        create_v90_system, create_v90_conscious, create_v90_insightful
    )
    _V90_AVAILABLE = True
except Exception as e:
    logging.warning(f"V90 import failed: {type(e).__name__}: {e}")
    _V90_AVAILABLE = False

# V91 Embodied Social AGI Architecture
try:
    from .v91 import (
        V91CompleteSystem, V91Config, V91MetacognitiveState, AGIReadinessLevel,
        create_v91_system, create_v91_embodied, create_v91_social, create_v91_ethical
    )
    _V91_AVAILABLE = True
except Exception as e:
    logging.warning(f"V91 import failed: {type(e).__name__}: {e}")
    _V91_AVAILABLE = False

# V42 and V43 (optional - may have missing dependencies)
try:
    from .v42 import (
        V42CompleteSystem,
        V42Config,
        V42Mode,
        create_v42_standard,
        create_v42_fast,
        create_v42_deep,
        create_v42_gpqa
    )
    _V42_AVAILABLE = True
except Exception as e:
    logging.warning(f"V42 import failed: {type(e).__name__}: {e}")
    _V42_AVAILABLE = False

try:
    from .v43 import (
        V43CompleteSystem,
        V43Config,
        V43Mode,
        create_v43_standard,
        create_v43_fast,
        create_v43_deep,
        create_v43_gpqa
    )
    _V43_AVAILABLE = True
except Exception as e:
    logging.warning(f"V43 import failed: {type(e).__name__}: {e}")
    _V43_AVAILABLE = False

__all__ = []

# Add V50 exports if available
if _V50_AVAILABLE:
    __all__.extend([
        'V50DiscoveryEngine',
        'V50Config',
        'V50Mode',
        'V50Result',
        'create_v50_standard',
        'create_v50_fast',
        'create_v50_deep',
        'create_v50_discovery',
        'create_v50_gpqa',
    ])

# Add V80 exports if available
if _V80_AVAILABLE:
    __all__.extend([
        'V80CompleteSystem', 'V80Config', 'V80System',
        'create_v80_standard', 'create_v80_fast', 'create_v80_deep'
    ])

# Add V90 exports if available
if _V90_AVAILABLE:
    __all__.extend([
        'V90CompleteSystem', 'V90Config', 'V90MetacognitiveState',
        'create_v90_system', 'create_v90_conscious', 'create_v90_insightful'
    ])

# Add V42 exports if available
if _V42_AVAILABLE:
    __all__.extend([
        'V42CompleteSystem',
        'V42Config',
        'V42Mode',
        'create_v42_standard',
        'create_v42_fast',
        'create_v42_deep',
        'create_v42_gpqa',
    ])

# Add V43 exports if available
if _V43_AVAILABLE:
    __all__.extend([
        'V43CompleteSystem',
        'V43Config',
        'V43Mode',
        'create_v43_standard',
        'create_v43_fast',
        'create_v43_deep',
        'create_v43_gpqa',
    ])

# Add V91 exports if available
if '_V91_AVAILABLE' in globals() and _V91_AVAILABLE:
    __all__.extend([
        'V91CompleteSystem', 'V91Config', 'V91MetacognitiveState', 'AGIReadinessLevel',
        'create_v91_system', 'create_v91_embodied', 'create_v91_social', 'create_v91_ethical'
    ])

