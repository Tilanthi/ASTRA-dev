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
Abstraction Learning Module for STAN (Capabilities Package)
===========================================================

This module re-exports the Abstraction Learning classes from the
reasoning package for backward compatibility and API consistency.

Provides hierarchical abstraction learning, concept hierarchies,
analogy finding, and knowledge transfer capabilities.

Date: 2025-12-17
Version: 1.0.0
"""

# Re-export from reasoning package
from astra_core.reasoning.v50_abstraction_learning import (
    AbstractionLevel,
    Concept,
    Analogy,
    AbstractionResult,
    TransferResult,
    ConceptHierarchy,
    AbstractionEngine,
    AnalogyFinder,
    KnowledgeTransferEngine,
    HierarchicalAbstractionLearner,
)

# Factory functions - assuming they exist or creating them
def create_abstraction_learner():
    """Create a hierarchical abstraction learner."""
    return HierarchicalAbstractionLearner()

def create_concept_hierarchy():
    """Create a concept hierarchy."""
    return ConceptHierarchy()

def create_analogy_finder():
    """Create an analogy finder."""
    return AnalogyFinder()

def create_transfer_engine():
    """Create a knowledge transfer engine."""
    return KnowledgeTransferEngine()

__all__ = [
    'HierarchicalAbstractionLearner',
    'ConceptHierarchy',
    'AbstractionEngine',
    'AnalogyFinder',
    'KnowledgeTransferEngine',
    'Concept',
    'Analogy',
    'AbstractionResult',
    'TransferResult',
    'AbstractionLevel',
    'create_abstraction_learner',
    'create_concept_hierarchy',
    'create_analogy_finder',
    'create_transfer_engine',
]
