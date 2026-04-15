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
Causal Engine Module for STAN (Capabilities Package)
====================================================

This module re-exports the Causal Engine classes from the
reasoning package for backward compatibility and API consistency.

Provides causal inference, structure learning, mechanism discovery,
intervention planning, and counterfactual reasoning.

Date: 2025-12-17
Version: 1.0.0
"""

# Re-export from reasoning package
from astra_core.reasoning.v50_causal_engine import (
    CausalInferenceEngine,
    CausalStructureLearner,
    MechanismDiscovery,
    InterventionPlanner,
    CounterfactualReasoner,
    CausalGraph,
    CausalNode,
    CausalEdge,
    CausalEffect,
    Intervention,
    CounterfactualQuery,
    CounterfactualResult,
    CausalRelationType,
    InterventionType,
    create_causal_engine,
    create_structure_learner,
    create_counterfactual_reasoner,
    create_intervention_planner
)

# Aliases for V50 naming
CausalGraphV50 = CausalGraph
CausalEdgeV50 = CausalEdge

__all__ = [
    'CausalInferenceEngine',
    'CausalStructureLearner',
    'MechanismDiscovery',
    'InterventionPlanner',
    'CounterfactualReasoner',
    'CausalGraph',
    'CausalGraphV50',
    'CausalNode',
    'CausalEdge',
    'CausalEdgeV50',
    'CausalEffect',
    'Intervention',
    'CounterfactualQuery',
    'CounterfactualResult',
    'CausalRelationType',
    'InterventionType',
    'create_causal_engine',
    'create_structure_learner',
    'create_counterfactual_reasoner',
    'create_intervention_planner',
]
