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
STAN Self-Evolution Framework

An autonomous self-improvement system that evolves astra_core's reasoning
and discovery capabilities through iterative mutation, evaluation, and selection.

Core Principles:
1. Objective-driven: Metrics based on reasoning quality, not human supervision
2. Domain-focused: Optimized for astrophysics discovery and inference
3. Code-aware: Mutates and evaluates actual code changes
4. Safe: Maintains working baseline, can rollback
5. Transparent: Logs all mutations and evaluations

Architecture:
- MutationGenerator: Creates code modifications
- CapabilityEvaluator: Tests reasoning capabilities
- EvolutionOrchestrator: Manages evolution cycles
- CapabilityBaseline: Defines what "better" means
"""

from .mutation_engine import MutationEngine, MutationType, MutationResult
from .capability_evaluator import CapabilityEvaluator, EvaluationResult, CapabilityDomain
from .evolution_orchestrator import EvolutionOrchestrator, EvolutionConfig, EvolutionCycle
from .capability_baseline import CapabilityBaseline, ReasoningMetric
from .code_analyzer import CodeAnalyzer, AnalysisResult

__all__ = [
    'MutationEngine',
    'MutationType',
    'MutationResult',
    'CapabilityEvaluator',
    'EvaluationResult',
    'CapabilityDomain',
    'EvolutionOrchestrator',
    'EvolutionConfig',
    'EvolutionCycle',
    'CapabilityBaseline',
    'ReasoningMetric',
    'CodeAnalyzer',
    'AnalysisResult',
]
