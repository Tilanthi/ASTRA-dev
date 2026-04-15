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
Capability Orchestrator for STAN V40

Intelligently routes problems to appropriate capability modules,
manages execution order, and enables cross-module communication.

This addresses the integration gap where all 8 modules run
independently without coordination or result sharing.

Date: 2025-12-11
"""

import time
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import re


class CapabilityType(Enum):
    """Available capability modules"""
    ABDUCTIVE_INFERENCE = "abductive_inference"
    ACTIVE_EXPERIMENT = "active_experiment"
    EPISODIC_MEMORY = "episodic_memory"
    CAUSAL_DISCOVERY = "causal_discovery"
    META_LEARNING = "meta_learning"
    ABSTRACTION_LEARNING = "abstraction_learning"
    NEURAL_SYMBOLIC = "neural_symbolic"
    UNCERTAINTY_PLANNING = "uncertainty_planning"
    # V40 additions
    SYMBOLIC_MATH = "symbolic_math"
    PROOF_VALIDATOR = "proof_validator"
    QUANTITATIVE_REASONER = "quantitative_reasoner"
    # V40 external sources
    LLM_INFERENCE = "llm_inference"
    WOLFRAM_ALPHA = "wolfram_alpha"
    ARXIV = "arxiv"
    WIKIPEDIA = "wikipedia"
    PUBMED = "pubmed"


class ProblemCategory(Enum):
    """High-level problem categories"""
    MATHEMATICAL = "mathematical"
    SCIENTIFIC = "scientific"
    LOGICAL = "logical"
    CAUSAL = "causal"
    STATISTICAL = "statistical"
    OPTIMIZATION = "optimization"
    CLASSIFICATION = "classification"
    EXPLANATION = "explanation"
    PREDICTION = "prediction"
    ASTRONOMICAL = "astronomical"
    BIOMEDICAL = "biomedical"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    COMPUTER_SCIENCE = "computer_science"
    UNKNOWN = "unknown"


class ExecutionMode(Enum):
    """How to execute capabilities"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ITERATIVE = "iterative"


@dataclass
class CapabilityConfig:
    """Configuration for a capability"""
    capability_type: CapabilityType
    priority: int = 5  # 1-10, higher = more important
    timeout: float = 30.0  # seconds
    required_inputs: List[str] = field(default_factory=list)
    provides_outputs: List[str] = field(default_factory=list)
    dependencies: List[CapabilityType] = field(default_factory=list)


@dataclass
class TaskSignature:
    """Signature describing a task for routing"""
    task_id: str
    description: str
    category: ProblemCategory
    keywords: Set[str] = field(default_factory=set)
    requires_precision: bool = False
    requires_explanation: bool = False
    has_constraints: bool = False
    has_prior_knowledge: bool = False
    complexity_estimate: float = 0.5  # 0-1
    answer_type: str = "open"  # 'open', 'multiple_choice', 'exact_match'


@dataclass
class CapabilityResult:
    """Result from executing a capability"""
    capability_type: CapabilityType
    success: bool
    output: Any
    confidence: float
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """Plan for executing capabilities"""
    plan_id: str
    task_signature: TaskSignature
    capabilities: List[CapabilityType]
    execution_order: List[List[CapabilityType]]  # Groups can run in parallel
    execution_mode: ExecutionMode
    estimated_time: float
    rationale: str


@dataclass
class OrchestrationResult:
    """Complete result of orchestrated execution"""
    plan: ExecutionPlan
    results: Dict[CapabilityType, CapabilityResult]
    combined_output: Any
    combined_confidence: float
    total_time: float
    success: bool


class ProblemClassifier:
    """Classify problems to determine required capabilities"""

    def __init__(self):
        self.category_keywords = {
            ProblemCategory.MATHEMATICAL: {
                'solve', 'equation', 'calculate', 'derive', 'integral',
                'derivative', 'prove', 'theorem', 'algebraic', 'formula',
                'polynomial', 'matrix', 'vector', 'sum', 'product',
                'limit', 'series', 'convergence', 'eigenvalue', 'determinant'
            },
            ProblemCategory.SCIENTIFIC: {
                'experiment', 'hypothesis', 'observe', 'measure',
                'energy', 'force', 'reaction', 'law', 'theory',
                'molecule', 'atom', 'wave', 'particle', 'field'
            },
            ProblemCategory.PHYSICS: {
                'physics', 'mechanics', 'thermodynamics', 'electromagnetism',
                'quantum', 'relativity', 'momentum', 'velocity', 'acceleration',
                'gravity', 'electromagnetic', 'photon', 'electron', 'proton'
            },
            ProblemCategory.CHEMISTRY: {
                'chemistry', 'chemical', 'bond', 'molecule', 'compound',
                'reaction', 'element', 'periodic', 'organic', 'inorganic',
                'acid', 'base', 'oxidation', 'reduction', 'catalyst'
            },
            ProblemCategory.ASTRONOMICAL: {
                'star', 'galaxy', 'planet', 'cosmology', 'telescope',
                'black hole', 'supernova', 'redshift', 'dark matter',
                'universe', 'nebula', 'quasar', 'pulsar', 'exoplanet',
                'astronomical', 'celestial', 'orbit', 'solar', 'lunar'
            },
            ProblemCategory.BIOMEDICAL: {
                'disease', 'treatment', 'drug', 'gene', 'protein',
                'cell', 'patient', 'clinical', 'therapy', 'diagnosis',
                'medicine', 'medical', 'biology', 'biological', 'genetic',
                'virus', 'bacteria', 'immune', 'cancer', 'pharmaceutical'
            },
            ProblemCategory.COMPUTER_SCIENCE: {
                'algorithm', 'complexity', 'data structure', 'programming',
                'computer', 'software', 'machine learning', 'neural network',
                'artificial intelligence', 'database', 'network', 'security'
            },
            ProblemCategory.LOGICAL: {
                'if', 'then', 'therefore', 'implies', 'deduce', 'infer',
                'valid', 'fallacy', 'argument', 'premise', 'conclusion',
                'contradiction', 'necessary', 'sufficient'
            },
            ProblemCategory.CAUSAL: {
                'cause', 'effect', 'because', 'lead to', 'result in',
                'influence', 'impact', 'consequence', 'mechanism',
                'intervention', 'counterfactual'
            },
            ProblemCategory.STATISTICAL: {
                'probability', 'distribution', 'sample', 'population',
                'mean', 'variance', 'test', 'significant', 'correlation',
                'regression', 'hypothesis', 'p-value', 'confidence'
            },
            ProblemCategory.OPTIMIZATION: {
                'maximize', 'minimize', 'optimize', 'best', 'optimal',
                'constraint', 'objective', 'feasible', 'efficient'
            },
            ProblemCategory.CLASSIFICATION: {
                'classify', 'categorize', 'identify', 'which type',
                'belongs to', 'kind of', 'species', 'class'
            },
            ProblemCategory.EXPLANATION: {
                'why', 'explain', 'reason', 'understand', 'clarify',
                'describe', 'how does', 'what causes'
            },
            ProblemCategory.PREDICTION: {
                'predict', 'forecast', 'expect', 'will', 'future',
                'estimate', 'project', 'anticipate'
            }
        }

        # Capability relevance by category
        self.category_capabilities = {
            ProblemCategory.MATHEMATICAL: [
                CapabilityType.SYMBOLIC_MATH,
                CapabilityType.PROOF_VALIDATOR,
                CapabilityType.WOLFRAM_ALPHA,  # External: Wolfram for computation
                CapabilityType.ABSTRACTION_LEARNING,
                CapabilityType.NEURAL_SYMBOLIC,
                CapabilityType.LLM_INFERENCE  # LLM for reasoning
            ],
            ProblemCategory.SCIENTIFIC: [
                CapabilityType.CAUSAL_DISCOVERY,
                CapabilityType.ACTIVE_EXPERIMENT,
                CapabilityType.ABDUCTIVE_INFERENCE,
                CapabilityType.QUANTITATIVE_REASONER,
                CapabilityType.ARXIV,  # External: arXiv for literature
                CapabilityType.WIKIPEDIA,  # External: Wikipedia for facts
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.PHYSICS: [
                CapabilityType.SYMBOLIC_MATH,
                CapabilityType.WOLFRAM_ALPHA,  # External: Wolfram for physics
                CapabilityType.ARXIV,  # External: arXiv physics papers
                CapabilityType.QUANTITATIVE_REASONER,
                CapabilityType.CAUSAL_DISCOVERY,
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.CHEMISTRY: [
                CapabilityType.SYMBOLIC_MATH,
                CapabilityType.WOLFRAM_ALPHA,  # External: Wolfram for chemistry
                CapabilityType.ARXIV,  # External: arXiv for chemistry papers
                CapabilityType.WIKIPEDIA,  # External: Wikipedia for elements/compounds
                CapabilityType.QUANTITATIVE_REASONER,
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.ASTRONOMICAL: [
                CapabilityType.ARXIV,  # External: arXiv astro-ph
                CapabilityType.WOLFRAM_ALPHA,  # External: Wolfram for calculations
                CapabilityType.WIKIPEDIA,  # External: Wikipedia for astronomy
                CapabilityType.CAUSAL_DISCOVERY,
                CapabilityType.QUANTITATIVE_REASONER,
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.BIOMEDICAL: [
                CapabilityType.PUBMED,  # External: PubMed for medical literature
                CapabilityType.WIKIPEDIA,  # External: Wikipedia for medical info
                CapabilityType.CAUSAL_DISCOVERY,
                CapabilityType.ABDUCTIVE_INFERENCE,
                CapabilityType.QUANTITATIVE_REASONER,
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.COMPUTER_SCIENCE: [
                CapabilityType.ARXIV,  # External: arXiv cs papers
                CapabilityType.WIKIPEDIA,  # External: Wikipedia for CS concepts
                CapabilityType.META_LEARNING,
                CapabilityType.NEURAL_SYMBOLIC,
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.LOGICAL: [
                CapabilityType.PROOF_VALIDATOR,
                CapabilityType.NEURAL_SYMBOLIC,
                CapabilityType.ABDUCTIVE_INFERENCE,
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.CAUSAL: [
                CapabilityType.CAUSAL_DISCOVERY,
                CapabilityType.ABDUCTIVE_INFERENCE,
                CapabilityType.ACTIVE_EXPERIMENT,
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.STATISTICAL: [
                CapabilityType.QUANTITATIVE_REASONER,
                CapabilityType.WOLFRAM_ALPHA,  # External: Wolfram for stats
                CapabilityType.UNCERTAINTY_PLANNING,
                CapabilityType.META_LEARNING,
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.OPTIMIZATION: [
                CapabilityType.META_LEARNING,
                CapabilityType.UNCERTAINTY_PLANNING,
                CapabilityType.WOLFRAM_ALPHA,  # External: Wolfram for optimization
                CapabilityType.ABSTRACTION_LEARNING,
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.CLASSIFICATION: [
                CapabilityType.META_LEARNING,
                CapabilityType.EPISODIC_MEMORY,
                CapabilityType.NEURAL_SYMBOLIC,
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.EXPLANATION: [
                CapabilityType.ABDUCTIVE_INFERENCE,
                CapabilityType.CAUSAL_DISCOVERY,
                CapabilityType.EPISODIC_MEMORY,
                CapabilityType.WIKIPEDIA,  # External: Wikipedia for explanations
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.PREDICTION: [
                CapabilityType.META_LEARNING,
                CapabilityType.CAUSAL_DISCOVERY,
                CapabilityType.UNCERTAINTY_PLANNING,
                CapabilityType.LLM_INFERENCE
            ],
            ProblemCategory.UNKNOWN: [
                CapabilityType.META_LEARNING,
                CapabilityType.ABDUCTIVE_INFERENCE,
                CapabilityType.EPISODIC_MEMORY,
                CapabilityType.WIKIPEDIA,  # External: General knowledge
                CapabilityType.LLM_INFERENCE
            ]
        }

    def classify(self, problem_text: str) -> TaskSignature:
        """Classify a problem and create task signature"""
        text_lower = problem_text.lower()

        # Extract keywords
        words = set(re.findall(r'\b\w+\b', text_lower))

        # Score each category
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = len(words.intersection(keywords))
            category_scores[category] = score

        # Get best category
        best_category = max(category_scores, key=category_scores.get)
        if category_scores[best_category] == 0:
            best_category = ProblemCategory.UNKNOWN

        # Determine other properties
        requires_precision = any(kw in text_lower for kw in
            ['exact', 'precise', 'calculate', 'compute', 'numerical'])
        requires_explanation = any(kw in text_lower for kw in
            ['why', 'explain', 'reason', 'justify', 'show work'])
        has_constraints = any(kw in text_lower for kw in
            ['constraint', 'condition', 'given that', 'assuming', 'such that'])

        # Estimate complexity
        complexity = min(1.0, len(problem_text) / 500)
        if any(kw in text_lower for kw in ['complex', 'difficult', 'advanced']):
            complexity = min(1.0, complexity + 0.2)

        # Determine answer type
        if any(kw in text_lower for kw in ['which of the following', 'choose', 'select']):
            answer_type = 'multiple_choice'
        elif any(kw in text_lower for kw in ['exact', 'precise', 'value of']):
            answer_type = 'exact_match'
        else:
            answer_type = 'open'

        return TaskSignature(
            task_id=f"task_{hash(problem_text) % 10000}",
            description=problem_text[:200],
            category=best_category,
            keywords=words.intersection(set().union(*self.category_keywords.values())),
            requires_precision=requires_precision,
            requires_explanation=requires_explanation,
            has_constraints=has_constraints,
            has_prior_knowledge=False,  # Will be updated based on memory
            complexity_estimate=complexity,
            answer_type=answer_type
        )

    def get_relevant_capabilities(self, signature: TaskSignature) -> List[CapabilityType]:
        """Get capabilities relevant to the task signature"""
        base_capabilities = self.category_capabilities.get(
            signature.category,
            self.category_capabilities[ProblemCategory.UNKNOWN]
        )

        capabilities = list(base_capabilities)

        # Add based on properties
        if signature.requires_precision:
            if CapabilityType.SYMBOLIC_MATH not in capabilities:
                capabilities.append(CapabilityType.SYMBOLIC_MATH)
            if CapabilityType.QUANTITATIVE_REASONER not in capabilities:
                capabilities.append(CapabilityType.QUANTITATIVE_REASONER)

        if signature.requires_explanation:
            if CapabilityType.ABDUCTIVE_INFERENCE not in capabilities:
                capabilities.append(CapabilityType.ABDUCTIVE_INFERENCE)

        if signature.has_constraints:
            if CapabilityType.NEURAL_SYMBOLIC not in capabilities:
                capabilities.append(CapabilityType.NEURAL_SYMBOLIC)

        # Always include episodic memory for experience-based learning
        if CapabilityType.EPISODIC_MEMORY not in capabilities:
            capabilities.append(CapabilityType.EPISODIC_MEMORY)

        return capabilities


class ExecutionPlanner:
    """Plan execution order for capabilities"""

    def __init__(self):
        # Define dependencies between capabilities
        self.dependencies = {
            CapabilityType.ACTIVE_EXPERIMENT: [CapabilityType.CAUSAL_DISCOVERY],
            CapabilityType.PROOF_VALIDATOR: [CapabilityType.NEURAL_SYMBOLIC],
            CapabilityType.ABSTRACTION_LEARNING: [CapabilityType.SYMBOLIC_MATH],
        }

        # Define which capabilities can run in parallel
        self.parallel_groups = {
            'analysis': [
                CapabilityType.CAUSAL_DISCOVERY,
                CapabilityType.ABDUCTIVE_INFERENCE,
                CapabilityType.QUANTITATIVE_REASONER
            ],
            'memory': [
                CapabilityType.EPISODIC_MEMORY,
                CapabilityType.META_LEARNING
            ],
            'symbolic': [
                CapabilityType.SYMBOLIC_MATH,
                CapabilityType.NEURAL_SYMBOLIC
            ],
            'planning': [
                CapabilityType.UNCERTAINTY_PLANNING,
                CapabilityType.ACTIVE_EXPERIMENT
            ]
        }

    def create_plan(self, signature: TaskSignature,
                    capabilities: List[CapabilityType]) -> ExecutionPlan:
        """Create execution plan for given capabilities"""
        # Resolve dependencies
        all_capabilities = set(capabilities)
        for cap in capabilities:
            if cap in self.dependencies:
                all_capabilities.update(self.dependencies[cap])

        capabilities = list(all_capabilities)

        # Determine execution order using topological sort
        execution_order = self._topological_sort(capabilities)

        # Group parallel capabilities
        grouped_order = self._group_parallel(execution_order)

        # Determine execution mode
        if len(grouped_order) == 1:
            mode = ExecutionMode.PARALLEL
        elif signature.complexity_estimate > 0.7:
            mode = ExecutionMode.ITERATIVE
        else:
            mode = ExecutionMode.SEQUENTIAL

        # Estimate time
        estimated_time = len(capabilities) * 0.5  # 0.5s per capability average

        rationale = self._generate_rationale(signature, capabilities)

        return ExecutionPlan(
            plan_id=f"plan_{signature.task_id}",
            task_signature=signature,
            capabilities=capabilities,
            execution_order=grouped_order,
            execution_mode=mode,
            estimated_time=estimated_time,
            rationale=rationale
        )

    def _topological_sort(self, capabilities: List[CapabilityType]) -> List[CapabilityType]:
        """Sort capabilities respecting dependencies"""
        # Build adjacency list
        in_degree = {cap: 0 for cap in capabilities}
        graph = {cap: [] for cap in capabilities}

        for cap in capabilities:
            if cap in self.dependencies:
                for dep in self.dependencies[cap]:
                    if dep in capabilities:
                        graph[dep].append(cap)
                        in_degree[cap] += 1

        # Kahn's algorithm
        queue = [cap for cap in capabilities if in_degree[cap] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Handle cycles (shouldn't happen, but fallback)
        remaining = [cap for cap in capabilities if cap not in result]
        result.extend(remaining)

        return result

    def _group_parallel(self, ordered: List[CapabilityType]) -> List[List[CapabilityType]]:
        """Group capabilities that can run in parallel"""
        groups = []
        current_group = []
        used = set()

        for cap in ordered:
            if cap in used:
                continue

            # Check if this can be grouped with current
            can_group = True
            for existing in current_group:
                # Check if any dependency exists between them
                if cap in self.dependencies.get(existing, []):
                    can_group = False
                    break
                if existing in self.dependencies.get(cap, []):
                    can_group = False
                    break

            if can_group:
                current_group.append(cap)
                used.add(cap)
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [cap]
                used.add(cap)

        if current_group:
            groups.append(current_group)

        return groups

    def _generate_rationale(self, signature: TaskSignature,
                           capabilities: List[CapabilityType]) -> str:
        """Generate explanation for the execution plan"""
        parts = [f"For {signature.category.value} problem:"]

        capability_descriptions = {
            CapabilityType.SYMBOLIC_MATH: "Symbolic math for algebraic manipulation",
            CapabilityType.PROOF_VALIDATOR: "Proof validator for logical verification",
            CapabilityType.QUANTITATIVE_REASONER: "Quantitative reasoner for statistical analysis",
            CapabilityType.CAUSAL_DISCOVERY: "Causal discovery for relationship analysis",
            CapabilityType.ABDUCTIVE_INFERENCE: "Abductive inference for hypothesis generation",
            CapabilityType.EPISODIC_MEMORY: "Episodic memory for past experience",
            CapabilityType.META_LEARNING: "Meta-learning for strategy selection",
            CapabilityType.NEURAL_SYMBOLIC: "Neural-symbolic bridge for constraint handling",
            CapabilityType.UNCERTAINTY_PLANNING: "Uncertainty planning for decision making",
            CapabilityType.ACTIVE_EXPERIMENT: "Active experiment design for information gathering",
            CapabilityType.ABSTRACTION_LEARNING: "Abstraction learning for pattern discovery",
            # External sources
            CapabilityType.LLM_INFERENCE: "LLM inference for chain-of-thought reasoning",
            CapabilityType.WOLFRAM_ALPHA: "Wolfram Alpha for computational knowledge",
            CapabilityType.ARXIV: "arXiv for scientific literature search",
            CapabilityType.WIKIPEDIA: "Wikipedia for factual knowledge retrieval",
            CapabilityType.PUBMED: "PubMed for biomedical literature search"
        }

        for cap in capabilities:
            desc = capability_descriptions.get(cap, f"{cap.value}")
            parts.append(f"- {desc}")

        return "\n".join(parts)


class ResultCombiner:
    """Combine results from multiple capabilities"""

    def __init__(self):
        pass

    def combine(self, results: Dict[CapabilityType, CapabilityResult],
                signature: TaskSignature) -> Tuple[Any, float]:
        """
        Combine results from multiple capabilities.

        Returns combined output and confidence.
        """
        if not results:
            return None, 0.0

        # Filter successful results
        successful = {k: v for k, v in results.items() if v.success}

        if not successful:
            # Return best failed result
            best_failed = max(results.values(), key=lambda x: x.confidence)
            return best_failed.output, best_failed.confidence * 0.5

        # Weight results by capability type relevance and confidence
        weights = self._get_weights(successful.keys(), signature)

        combined_confidence = sum(
            results[cap].confidence * weights[cap]
            for cap in successful
        ) / sum(weights.values())

        # Combine outputs based on problem category
        if signature.category == ProblemCategory.MATHEMATICAL:
            combined_output = self._combine_math_outputs(successful, weights)
        elif signature.category == ProblemCategory.STATISTICAL:
            combined_output = self._combine_statistical_outputs(successful, weights)
        else:
            combined_output = self._combine_general_outputs(successful, weights)

        return combined_output, combined_confidence

    def _get_weights(self, capabilities: Set[CapabilityType],
                    signature: TaskSignature) -> Dict[CapabilityType, float]:
        """Get weights for each capability based on relevance"""
        weights = {}

        for cap in capabilities:
            # Base weight
            weight = 1.0

            # Adjust based on category
            if signature.category == ProblemCategory.MATHEMATICAL:
                if cap == CapabilityType.SYMBOLIC_MATH:
                    weight = 2.0
                elif cap == CapabilityType.PROOF_VALIDATOR:
                    weight = 1.5

            elif signature.category == ProblemCategory.STATISTICAL:
                if cap == CapabilityType.QUANTITATIVE_REASONER:
                    weight = 2.0

            elif signature.category == ProblemCategory.CAUSAL:
                if cap == CapabilityType.CAUSAL_DISCOVERY:
                    weight = 2.0
                elif cap == CapabilityType.ABDUCTIVE_INFERENCE:
                    weight = 1.5

            # Adjust based on answer type
            if signature.answer_type == 'exact_match':
                if cap == CapabilityType.SYMBOLIC_MATH:
                    weight *= 1.5
                elif cap == CapabilityType.QUANTITATIVE_REASONER:
                    weight *= 1.3

            weights[cap] = weight

        return weights

    def _combine_math_outputs(self, results: Dict[CapabilityType, CapabilityResult],
                             weights: Dict[CapabilityType, float]) -> Any:
        """Combine outputs for mathematical problems"""
        # Prioritize symbolic math result if available
        if CapabilityType.SYMBOLIC_MATH in results:
            return results[CapabilityType.SYMBOLIC_MATH].output

        # Fall back to highest weighted result
        best_cap = max(results.keys(), key=lambda x: weights.get(x, 1.0))
        return results[best_cap].output

    def _combine_statistical_outputs(self, results: Dict[CapabilityType, CapabilityResult],
                                    weights: Dict[CapabilityType, float]) -> Any:
        """Combine outputs for statistical problems"""
        if CapabilityType.QUANTITATIVE_REASONER in results:
            return results[CapabilityType.QUANTITATIVE_REASONER].output

        best_cap = max(results.keys(), key=lambda x: weights.get(x, 1.0))
        return results[best_cap].output

    def _combine_general_outputs(self, results: Dict[CapabilityType, CapabilityResult],
                                weights: Dict[CapabilityType, float]) -> Any:
        """Combine outputs for general problems"""
        # Create combined output dict
        combined = {
            'sources': {},
            'primary_answer': None,
            'confidence_breakdown': {}
        }

        best_confidence = 0
        best_output = None

        for cap, result in results.items():
            combined['sources'][cap.value] = result.output
            combined['confidence_breakdown'][cap.value] = result.confidence

            weighted_conf = result.confidence * weights.get(cap, 1.0)
            if weighted_conf > best_confidence:
                best_confidence = weighted_conf
                best_output = result.output

        combined['primary_answer'] = best_output
        return combined


class CapabilityOrchestrator:
    """
    Main orchestrator for STAN capabilities.

    Routes problems to appropriate modules, manages execution,
    and combines results.
    """

    def __init__(self):
        self.classifier = ProblemClassifier()
        self.planner = ExecutionPlanner()
        self.combiner = ResultCombiner()

        # Registry of capability executors
        self.executors: Dict[CapabilityType, Callable] = {}

        # Execution history for learning
        self.execution_history: List[OrchestrationResult] = []

    def register_executor(self, capability_type: CapabilityType,
                         executor: Callable):
        """Register an executor function for a capability"""
        self.executors[capability_type] = executor

    def orchestrate(self, problem: str,
                    context: Optional[Dict] = None) -> OrchestrationResult:
        """
        Orchestrate capability execution for a problem.

        Args:
            problem: The problem description
            context: Optional additional context

        Returns:
            OrchestrationResult with combined outputs
        """
        start_time = time.time()
        context = context or {}

        # 1. Classify the problem
        signature = self.classifier.classify(problem)

        # Update signature with context
        if 'has_prior_knowledge' in context:
            signature.has_prior_knowledge = context['has_prior_knowledge']

        # 2. Get relevant capabilities
        capabilities = self.classifier.get_relevant_capabilities(signature)

        # 3. Create execution plan
        plan = self.planner.create_plan(signature, capabilities)

        # 4. Execute capabilities
        results = self._execute_plan(plan, problem, context)

        # 5. Combine results
        combined_output, combined_confidence = self.combiner.combine(results, signature)

        total_time = time.time() - start_time

        # Create result
        orchestration_result = OrchestrationResult(
            plan=plan,
            results=results,
            combined_output=combined_output,
            combined_confidence=combined_confidence,
            total_time=total_time,
            success=any(r.success for r in results.values())
        )

        # Store for learning
        self.execution_history.append(orchestration_result)

        return orchestration_result

    def _execute_plan(self, plan: ExecutionPlan, problem: str,
                     context: Dict) -> Dict[CapabilityType, CapabilityResult]:
        """Execute the capabilities according to the plan"""
        results = {}
        shared_context = dict(context)

        for group in plan.execution_order:
            # Execute capabilities in this group (can be parallel)
            for capability_type in group:
                if capability_type in self.capabilities:
                    result = self.capabilities[capability_type].execute(
                        problem, shared_context
                    )
                    results[capability_type] = result
                    # Update shared context with results
                    if result.output:
                        shared_context.update(result.output)

        return results
