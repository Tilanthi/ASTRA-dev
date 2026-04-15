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
V100 Value Components
=====================

Multi-dimensional scientific value assessment.

Author: STAN-XI ASTRO V100 Development Team
Version: 100.0.0
"""

from .scientific_value import (
    ScientificValueCalculator,
    ScientificValue,
    DiscoveryType,
    DomainImpact,
    ResourceBudget,
    ValueDimensions,
    create_scientific_value_calculator,
    assess_scientific_value,
)

__all__ = [
    'ScientificValueCalculator',
    'ScientificValue',
    'DiscoveryType',
    'DomainImpact',
    'ResourceBudget',
    'ValueDimensions',
    'create_scientific_value_calculator',
    'assess_scientific_value',
]
