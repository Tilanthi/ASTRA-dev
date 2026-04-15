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
MoE-inspired Routing Module for STAN_IX_ASTRO

This module implements Mixture-of-Experts (MoE) style routing for dynamic
capability selection and conditional computation.

Key components:
- MoECapabilityRouter: Routes tasks to relevant specialized experts
- ConditionalComputationEngine: Orchestrates execution with routing
"""

from .moe_router import (
    MoECapabilityRouter,
    ConditionalComputationEngine,
    TaskType,
    Expert,
    RoutingDecision,
    create_moe_router,
    create_conditional_engine,
)

__all__ = [
    'MoECapabilityRouter',
    'ConditionalComputationEngine',
    'TaskType',
    'Expert',
    'RoutingDecision',
    'create_moe_router',
    'create_conditional_engine',
]
