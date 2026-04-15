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
V37 Enhanced System: V36 with Swarm Intelligence & Memory

This package provides the integrated V37CompleteSystem that extends
V36 with swarm intelligence and memory capabilities.

Version: 37.0
"""

from .v37_system import V37CompleteSystem

# Alias for backward compatibility
V37EnhancedSystem = V37CompleteSystem

__version__ = "37.0"

__all__ = ['V37CompleteSystem', 'V37EnhancedSystem']
