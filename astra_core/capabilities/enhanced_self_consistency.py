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
Enhanced Self-Consistency Module for STAN (Capabilities Package)
================================================================

This module re-exports the Enhanced Self-Consistency classes from the
reasoning package for backward compatibility and API consistency.

Generates multiple independent reasoning chains and uses weighted
voting to select the final answer.

Date: 2025-12-17
Version: 1.0.0
"""

# Re-export from reasoning package
from astra_core.reasoning.enhanced_self_consistency import (
    EnhancedSelfConsistency,
    ConsistencyResult,
    ReasoningChain,
    DiverseChainGenerator,
    ChainQualityScorer,
    ReasoningStrategy
)

# Factory functions
def create_enhanced_self_consistency(num_samples: int = 8, temperature: float = 0.7) -> EnhancedSelfConsistency:
    """Create an enhanced self-consistency engine."""
    return EnhancedSelfConsistency(num_samples=num_samples, temperature=temperature)


def create_diverse_chain_generator() -> DiverseChainGenerator:
    """Create a diverse chain generator."""
    return DiverseChainGenerator()


def create_chain_quality_scorer() -> ChainQualityScorer:
    """Create a chain quality scorer."""
    return ChainQualityScorer()


__all__ = [
    'EnhancedSelfConsistency',
    'ConsistencyResult',
    'ReasoningChain',
    'DiverseChainGenerator',
    'ChainQualityScorer',
    'ReasoningStrategy',
    'create_enhanced_self_consistency',
    'create_diverse_chain_generator',
    'create_chain_quality_scorer',
]
