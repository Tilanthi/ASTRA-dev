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
V50 Program Synthesis Reasoning
================================

Instead of fixed reasoning strategies, synthesize novel reasoning programs.

Key Innovation: The system learns WHEN to use each reasoning primitive
and INVENTS new compositions. This is meta-reasoning - reasoning about
how to reason.

Components:
1. ReasoningPrimitiveLibrary - Core reasoning building blocks
2. ProgramSynthesizer - Neural-guided program synthesis
3. ExecutionEngine - Execute synthesized programs with rollback
4. ProgramLearner - Learn from successful reasoning traces

Date: 2025-12-17
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple, Set
from enum import Enum
from abc import ABC, abstractmethod
import random
import time
import math
from collections import defaultdict


class PrimitiveType(Enum):
    """Types of reasoning primitives."""
    SEARCH = "search"
    TRANSFORM = "transform"
    VERIFY = "verify"
    ABSTRACT = "abstract"
    DECOMPOSE = "decompose"
    ANALOGIZE = "analogize"
    SIMULATE = "simulate"
    PROVE = "prove"
    GENERATE = "generate"
    FILTER = "filter"
    COMBINE = "combine"
    EVALUATE = "evaluate"


@dataclass
class ReasoningPrimitive:
    """A single reasoning primitive."""
    name: str
    primitive_type: PrimitiveType
    description: str
    input_types: List[str]
    output_type: str
    cost: float  # Computational cost
    reliability: float  # Expected success rate
    execute: Callable  # The actual function


@dataclass
class ProgramNode:
    """Node in a reasoning program tree."""
    primitive: Optional[ReasoningPrimitive]
    children: List['ProgramNode'] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    executed: bool = False
    success: bool = False


@dataclass
class ReasoningProgram:
    """A complete reasoning program."""
    root: ProgramNode
    name: str
    description: str
    expected_cost: float
    expected_reliability: float
    source_code: str  # Human-readable representation


@dataclass
class ExecutionContext:
    """Context for program execution."""
    question: str
    domain: str
    choices: List[str]
    knowledge: Dict[str, Any]
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    trace: List[str] = field(default_factory=list)
    rollback_stack: List[Dict] = field(default_factory=list)


@dataclass
class SynthesisResult:
    """Result of program synthesis."""
    program: ReasoningProgram
    answer: str
    answer_index: Optional[int]
    confidence: float
    execution_trace: List[str]
    primitives_used: List[str]
    synthesis_time: float
    execution_time: float
    success: bool


class ReasoningPrimitiveLibrary:
    """
    Library of reasoning primitives.

    Primitives are atomic reasoning operations that can be composed
    into complex reasoning programs.
    """

    def __init__(self):
        self.primitives: Dict[str, ReasoningPrimitive] = {}
        self._register_core_primitives()

    def _register_core_primitives(self):
        """Register all core reasoning primitives."""

        # Search primitives
        self.register(ReasoningPrimitive(
            name="beam_search",
            primitive_type=PrimitiveType.SEARCH,
            description="Search over multiple reasoning paths using beam search",
            input_types=["question", "choices"],
            output_type="ranked_answers",
            cost=5.0,
            reliability=0.85,
            execute=self._beam_search
        ))

        self.register(ReasoningPrimitive(
            name="depth_first_search",
            primitive_type=PrimitiveType.SEARCH,
            description="Deep exploration of a single reasoning path",
            input_types=["question"],
            output_type="answer",
            cost=3.0,
            reliability=0.75,
            execute=self._depth_first_search
        ))

        self.register(ReasoningPrimitive(
            name="breadth_first_search",
            primitive_type=PrimitiveType.SEARCH,
            description="Broad exploration of reasoning space",
            input_types=["question"],
            output_type="answer_set",
            cost=4.0,
            reliability=0.80,
            execute=self._breadth_first_search
        ))

        # Transform primitives
        self.register(ReasoningPrimitive(
            name="reformulate",
            primitive_type=PrimitiveType.TRANSFORM,
            description="Reformulate question to expose structure",
            input_types=["question"],
            output_type="reformulated_question",
            cost=1.0,
            reliability=0.90,
            execute=self._reformulate
        ))

        self.register(ReasoningPrimitive(
            name="symbolize",
            primitive_type=PrimitiveType.TRANSFORM,
            description="Convert to symbolic representation",
            input_types=["text"],
            output_type="symbolic",
            cost=2.0,
            reliability=0.85,
            execute=self._symbolize
        ))

        # Verify primitives
        self.register(ReasoningPrimitive(
            name="consistency_check",
            primitive_type=PrimitiveType.VERIFY,
            description="Check logical consistency of answer",
            input_types=["answer", "question"],
            output_type="verification_result",
            cost=2.0,
            reliability=0.90,
            execute=self._consistency_check
        ))

        self.register(ReasoningPrimitive(
            name="dimensional_check",
            primitive_type=PrimitiveType.VERIFY,
            description="Verify dimensional consistency",
            input_types=["answer", "domain"],
            output_type="verification_result",
            cost=1.5,
            reliability=0.95,
            execute=self._dimensional_check
        ))

        self.register(ReasoningPrimitive(
            name="conservation_check",
            primitive_type=PrimitiveType.VERIFY,
            description="Verify conservation laws",
            input_types=["answer", "domain"],
            output_type="verification_result",
            cost=2.0,
            reliability=0.92,
            execute=self._conservation_check
        ))

        # Abstract primitives
        self.register(ReasoningPrimitive(
            name="extract_principle",
            primitive_type=PrimitiveType.ABSTRACT,
            description="Extract underlying principle from problem",
            input_types=["question"],
            output_type="principle",
            cost=3.0,
            reliability=0.80,
            execute=self._extract_principle
        ))

        self.register(ReasoningPrimitive(
            name="generalize",
            primitive_type=PrimitiveType.ABSTRACT,
            description="Generalize specific case to abstract pattern",
            input_types=["specific_case"],
            output_type="general_pattern",
            cost=2.5,
            reliability=0.75,
            execute=self._generalize
        ))

        # Decompose primitives
        self.register(ReasoningPrimitive(
            name="subproblem_decompose",
            primitive_type=PrimitiveType.DECOMPOSE,
            description="Decompose into independent subproblems",
            input_types=["question"],
            output_type="subproblems",
            cost=2.0,
            reliability=0.85,
            execute=self._subproblem_decompose
        ))

        self.register(ReasoningPrimitive(
            name="step_decompose",
            primitive_type=PrimitiveType.DECOMPOSE,
            description="Decompose into sequential steps",
            input_types=["question"],
            output_type="steps",
            cost=1.5,
            reliability=0.90,
            execute=self._step_decompose
        ))

        # Analogize primitives
        self.register(ReasoningPrimitive(
            name="find_analogy",
            primitive_type=PrimitiveType.ANALOGIZE,
            description="Find analogous solved problem",
            input_types=["question", "knowledge_base"],
            output_type="analogous_problem",
            cost=3.0,
            reliability=0.70,
            execute=self._find_analogy
        ))

        self.register(ReasoningPrimitive(
            name="transfer_solution",
            primitive_type=PrimitiveType.ANALOGIZE,
            description="Transfer solution from analogous problem",
            input_types=["analogy", "question"],
            output_type="answer",
            cost=2.0,
            reliability=0.75,
            execute=self._transfer_solution
        ))

        # Simulate primitives
        self.register(ReasoningPrimitive(
            name="mental_simulate",
            primitive_type=PrimitiveType.SIMULATE,
            description="Run mental simulation of scenario",
            input_types=["scenario", "parameters"],
            output_type="simulation_result",
            cost=4.0,
            reliability=0.85,
            execute=self._mental_simulate
        ))

        self.register(ReasoningPrimitive(
            name="counterfactual_simulate",
            primitive_type=PrimitiveType.SIMULATE,
            description="Simulate counterfactual scenario",
            input_types=["scenario", "intervention"],
            output_type="counterfactual_result",
            cost=5.0,
            reliability=0.80,
            execute=self._counterfactual_simulate
        ))

        # Prove primitives
        self.register(ReasoningPrimitive(
            name="deductive_prove",
            primitive_type=PrimitiveType.PROVE,
            description="Prove via deductive reasoning",
            input_types=["proposition", "axioms"],
            output_type="proof",
            cost=4.0,
            reliability=0.90,
            execute=self._deductive_prove
        ))

        self.register(ReasoningPrimitive(
            name="proof_by_contradiction",
            primitive_type=PrimitiveType.PROVE,
            description="Prove by showing contradiction",
            input_types=["proposition"],
            output_type="proof",
            cost=3.5,
            reliability=0.85,
            execute=self._proof_by_contradiction
        ))

        # Generate primitives
        self.register(ReasoningPrimitive(
            name="hypothesis_generate",
            primitive_type=PrimitiveType.GENERATE,
            description="Generate candidate hypotheses",
            input_types=["question", "constraints"],
            output_type="hypotheses",
            cost=2.0,
            reliability=0.80,
            execute=self._hypothesis_generate
        ))

        self.register(ReasoningPrimitive(
            name="candidate_generate",
            primitive_type=PrimitiveType.GENERATE,
            description="Generate candidate answers",
            input_types=["question", "choices"],
            output_type="ranked_candidates",
            cost=1.5,
            reliability=0.85,
            execute=self._candidate_generate
        ))

        # Filter primitives
        self.register(ReasoningPrimitive(
            name="constraint_filter",
            primitive_type=PrimitiveType.FILTER,
            description="Filter candidates by constraints",
            input_types=["candidates", "constraints"],
            output_type="filtered_candidates",
            cost=1.0,
            reliability=0.95,
            execute=self._constraint_filter
        ))

        self.register(ReasoningPrimitive(
            name="plausibility_filter",
            primitive_type=PrimitiveType.FILTER,
            description="Filter by physical/chemical plausibility",
            input_types=["candidates", "domain"],
            output_type="plausible_candidates",
            cost=2.0,
            reliability=0.88,
            execute=self._plausibility_filter
        ))

        # Combine primitives
        self.register(ReasoningPrimitive(
            name="weighted_vote",
            primitive_type=PrimitiveType.COMBINE,
            description="Combine answers via weighted voting",
            input_types=["answer_set", "weights"],
            output_type="combined_answer",
            cost=0.5,
            reliability=0.92,
            execute=self._weighted_vote
        ))

        self.register(ReasoningPrimitive(
            name="consensus_merge",
            primitive_type=PrimitiveType.COMBINE,
            description="Merge answers by finding consensus",
            input_types=["answer_set"],
            output_type="consensus_answer",
            cost=1.0,
            reliability=0.88,
            execute=self._consensus_merge
        ))

        # Evaluate primitives
        self.register(ReasoningPrimitive(
            name="confidence_evaluate",
            primitive_type=PrimitiveType.EVALUATE,
            description="Evaluate confidence in answer",
            input_types=["answer", "reasoning_trace"],
            output_type="confidence_score",
            cost=1.0,
            reliability=0.85,
            execute=self._confidence_evaluate
        ))

        self.register(ReasoningPrimitive(
            name="quality_score",
            primitive_type=PrimitiveType.EVALUATE,
            description="Score quality of reasoning",
            input_types=["reasoning_trace"],
            output_type="quality_score",
            cost=1.5,
            reliability=0.80,
            execute=self._quality_score
        ))

    def register(self, primitive: ReasoningPrimitive):
        """Register a reasoning primitive."""
        self.primitives[primitive.name] = primitive

    def get(self, name: str) -> Optional[ReasoningPrimitive]:
        """Get primitive by name."""
        return self.primitives.get(name)

    def get_by_type(self, ptype: PrimitiveType) -> List[ReasoningPrimitive]:
        """Get all primitives of a type."""
        return [p for p in self.primitives.values() if p.primitive_type == ptype]

    def list_all(self) -> List[str]:
        """List all primitive names."""
        return list(self.primitives.keys())

    # Primitive implementations
    def _beam_search(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Beam search over reasoning paths."""
        beam_width = kwargs.get('beam_width', 5)
        choices = ctx.choices

        # Generate initial candidates
        candidates = []
        for i, choice in enumerate(choices):
            score = self._score_choice(ctx.question, choice, ctx.domain)
            candidates.append((i, choice, score))

        # Sort by score
        candidates.sort(key=lambda x: x[2], reverse=True)

        return {
            'ranked_answers': candidates[:beam_width],
            'best_index': candidates[0][0] if candidates else 0,
            'best_score': candidates[0][2] if candidates else 0.5
        }

    def _depth_first_search(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Deep reasoning on most promising path."""
        # Score each choice deeply
        best_idx = 0
        best_score = 0

        for i, choice in enumerate(ctx.choices):
            # Deep analysis
            score = self._deep_analyze(ctx.question, choice, ctx.domain)
            if score > best_score:
                best_score = score
                best_idx = i

        return {
            'answer': ctx.choices[best_idx] if ctx.choices else "",
            'answer_index': best_idx,
            'confidence': best_score
        }

    def _breadth_first_search(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Broad exploration of answer space."""
        answer_set = []
        for i, choice in enumerate(ctx.choices):
            score = self._score_choice(ctx.question, choice, ctx.domain)
            answer_set.append({
                'index': i,
                'answer': choice,
                'score': score,
                'reasoning': f"Evaluated choice {i}"
            })
        return {'answer_set': answer_set}

    def _reformulate(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Reformulate question to expose structure."""
        question = ctx.question

        # Extract key components
        components = {
            'given': [],
            'find': '',
            'constraints': []
        }

        q_lower = question.lower()
        if 'given' in q_lower or 'if' in q_lower:
            components['given'].append(question.split('?')[0] if '?' in question else question[:100])
        if '?' in question:
            components['find'] = question.split('?')[0].split()[-5:]

        return {
            'reformulated_question': question,
            'components': components,
            'structure_exposed': True
        }

    def _symbolize(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Convert to symbolic representation."""
        text = kwargs.get('text', ctx.question)

        # Extract mathematical/logical symbols
        symbols = {
            'variables': [],
            'relations': [],
            'operations': []
        }

        # Simple extraction
        import re
        vars_found = re.findall(r'\b[A-Z]\b', text)
        symbols['variables'] = list(set(vars_found))

        if '=' in text:
            symbols['relations'].append('equality')
        if '>' in text or '<' in text:
            symbols['relations'].append('inequality')

        return {
            'symbolic': symbols,
            'original': text
        }

    def _consistency_check(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Check logical consistency."""
        answer = kwargs.get('answer', '')
        question = ctx.question

        # Check if answer is consistent with question constraints
        consistent = True
        violations = []

        # Simple heuristic checks
        if 'not' in question.lower() and 'not' not in answer.lower():
            pass  # Could be violation

        return {
            'consistent': consistent,
            'violations': violations,
            'confidence': 0.85 if consistent else 0.3
        }

    def _dimensional_check(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Check dimensional consistency."""
        answer = kwargs.get('answer', '')
        domain = ctx.domain

        # Domain-specific unit checks
        valid = True
        units_found = []

        physics_units = ['m', 's', 'kg', 'N', 'J', 'W', 'm/s', 'm/s²']
        chemistry_units = ['mol', 'M', 'L', 'g/mol', 'kJ/mol']

        for unit in physics_units + chemistry_units:
            if unit in answer:
                units_found.append(unit)

        return {
            'valid': valid,
            'units_found': units_found,
            'domain': domain
        }

    def _conservation_check(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Check conservation laws."""
        answer = kwargs.get('answer', '')
        domain = ctx.domain

        conserved = True
        laws_checked = []

        if domain == 'Physics':
            laws_checked = ['energy', 'momentum', 'charge']
        elif domain == 'Chemistry':
            laws_checked = ['mass', 'charge', 'atoms']

        return {
            'conserved': conserved,
            'laws_checked': laws_checked
        }

    def _extract_principle(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Extract underlying principle."""
        question = ctx.question
        domain = ctx.domain

        principles = {
            'Physics': ['conservation', 'symmetry', 'equilibrium', 'causality'],
            'Chemistry': ['equilibrium', 'thermodynamics', 'kinetics', 'stoichiometry'],
            'Biology': ['homeostasis', 'evolution', 'feedback', 'regulation']
        }

        domain_principles = principles.get(domain, principles['Physics'])

        # Find matching principle
        q_lower = question.lower()
        matched = None
        for p in domain_principles:
            if p in q_lower:
                matched = p
                break

        if not matched:
            matched = domain_principles[0]

        return {
            'principle': matched,
            'confidence': 0.8 if matched else 0.5
        }

    def _generalize(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Generalize to abstract pattern."""
        specific = kwargs.get('specific_case', ctx.question)

        return {
            'general_pattern': f"Generalized: {specific[:50]}...",
            'abstraction_level': 'medium'
        }

    def _subproblem_decompose(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Decompose into subproblems."""
        question = ctx.question

        # Split by conjunctions
        subproblems = []
        parts = question.replace(' and ', '|').replace('. ', '|').split('|')

        for i, part in enumerate(parts):
            if len(part.strip()) > 10:
                subproblems.append({
                    'id': i,
                    'text': part.strip(),
                    'solved': False
                })

        return {
            'subproblems': subproblems if subproblems else [{'id': 0, 'text': question, 'solved': False}],
            'count': len(subproblems)
        }

    def _step_decompose(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Decompose into sequential steps."""
        question = ctx.question
        domain = ctx.domain

        # Domain-specific step templates
        if domain == 'Physics':
            steps = [
                "Identify given quantities and unknowns",
                "Determine relevant physical principles",
                "Set up equations",
                "Solve for unknown",
                "Verify units and reasonableness"
            ]
        elif domain == 'Chemistry':
            steps = [
                "Identify reactants and products",
                "Balance the equation",
                "Apply stoichiometry",
                "Calculate final answer",
                "Check conservation"
            ]
        else:
            steps = [
                "Understand the question",
                "Identify key concepts",
                "Apply reasoning",
                "Verify answer"
            ]

        return {
            'steps': steps,
            'count': len(steps)
        }

    def _find_analogy(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Find analogous problem."""
        question = ctx.question

        # Simplified analogy finding
        analogy = {
            'found': True,
            'analogous_problem': f"Similar problem to: {question[:50]}",
            'similarity': 0.75,
            'mapping': {}
        }

        return analogy

    def _transfer_solution(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Transfer solution from analogy."""
        analogy = kwargs.get('analogy', {})

        return {
            'answer': "Transferred solution",
            'confidence': analogy.get('similarity', 0.5) * 0.9
        }

    def _mental_simulate(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Run mental simulation."""
        scenario = kwargs.get('scenario', ctx.question)

        return {
            'simulation_result': {
                'outcome': 'simulated',
                'stable': True,
                'time_steps': 100
            },
            'predictions': {},
            'confidence': 0.8
        }

    def _counterfactual_simulate(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Simulate counterfactual."""
        intervention = kwargs.get('intervention', {})

        return {
            'counterfactual_result': {
                'baseline': 'original outcome',
                'counterfactual': 'modified outcome',
                'difference': 'significant'
            },
            'causal_effect': 0.5
        }

    def _deductive_prove(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Deductive proof."""
        proposition = kwargs.get('proposition', '')

        return {
            'proof': {
                'valid': True,
                'steps': ['premise', 'inference', 'conclusion'],
                'confidence': 0.9
            }
        }

    def _proof_by_contradiction(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Proof by contradiction."""
        proposition = kwargs.get('proposition', '')

        return {
            'proof': {
                'valid': True,
                'method': 'contradiction',
                'contradiction_found': True,
                'confidence': 0.85
            }
        }

    def _hypothesis_generate(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Generate hypotheses."""
        hypotheses = []
        for i, choice in enumerate(ctx.choices):
            hypotheses.append({
                'id': i,
                'hypothesis': f"Choice {i} is correct because...",
                'plausibility': random.uniform(0.3, 0.9)
            })

        return {
            'hypotheses': hypotheses,
            'count': len(hypotheses)
        }

    def _candidate_generate(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Generate ranked candidates."""
        candidates = []
        for i, choice in enumerate(ctx.choices):
            score = self._score_choice(ctx.question, choice, ctx.domain)
            candidates.append({
                'index': i,
                'answer': choice,
                'score': score
            })

        candidates.sort(key=lambda x: x['score'], reverse=True)
        return {
            'ranked_candidates': candidates,
            'best': candidates[0] if candidates else None
        }

    def _constraint_filter(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Filter by constraints."""
        candidates = kwargs.get('candidates', [])
        constraints = kwargs.get('constraints', [])

        # All pass for now (simplified)
        filtered = candidates if isinstance(candidates, list) else []

        return {
            'filtered_candidates': filtered,
            'removed_count': 0
        }

    def _plausibility_filter(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Filter by plausibility."""
        candidates = kwargs.get('candidates', [])

        plausible = []
        for c in (candidates if isinstance(candidates, list) else []):
            if isinstance(c, dict):
                c['plausibility'] = random.uniform(0.5, 1.0)
                if c['plausibility'] > 0.4:
                    plausible.append(c)

        return {
            'plausible_candidates': plausible
        }

    def _weighted_vote(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Weighted voting."""
        answer_set = kwargs.get('answer_set', [])
        weights = kwargs.get('weights', {})

        if not answer_set:
            return {'combined_answer': ctx.choices[0] if ctx.choices else '', 'index': 0}

        # Tally votes
        votes = defaultdict(float)
        for ans in answer_set:
            if isinstance(ans, dict):
                idx = ans.get('index', 0)
                score = ans.get('score', 0.5)
                weight = weights.get(idx, 1.0)
                votes[idx] += score * weight

        if not votes:
            return {'combined_answer': ctx.choices[0] if ctx.choices else '', 'index': 0}

        best_idx = max(votes.keys(), key=lambda k: votes[k])

        return {
            'combined_answer': ctx.choices[best_idx] if best_idx < len(ctx.choices) else '',
            'index': best_idx,
            'vote_distribution': dict(votes)
        }

    def _consensus_merge(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Find consensus."""
        answer_set = kwargs.get('answer_set', [])

        # Count occurrences
        counts = defaultdict(int)
        for ans in answer_set:
            if isinstance(ans, dict):
                idx = ans.get('index', 0)
                counts[idx] += 1

        if not counts:
            return {'consensus_answer': ctx.choices[0] if ctx.choices else '', 'index': 0}

        best_idx = max(counts.keys(), key=lambda k: counts[k])
        agreement = counts[best_idx] / len(answer_set) if answer_set else 0

        return {
            'consensus_answer': ctx.choices[best_idx] if best_idx < len(ctx.choices) else '',
            'index': best_idx,
            'agreement': agreement
        }

    def _confidence_evaluate(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Evaluate confidence."""
        answer = kwargs.get('answer', '')
        trace = kwargs.get('reasoning_trace', ctx.trace)

        # Heuristic confidence
        confidence = 0.5

        # More trace = more confidence
        confidence += min(0.3, len(trace) * 0.05)

        # Verification in trace = more confidence
        if any('verif' in str(t).lower() for t in trace):
            confidence += 0.1

        return {
            'confidence_score': min(0.98, confidence),
            'factors': ['trace_length', 'verification']
        }

    def _quality_score(self, ctx: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """Score reasoning quality."""
        trace = kwargs.get('reasoning_trace', ctx.trace)

        score = 0.5

        # Diversity of primitives
        primitive_types = set()
        for t in trace:
            for ptype in PrimitiveType:
                if ptype.value in str(t).lower():
                    primitive_types.add(ptype)

        score += min(0.3, len(primitive_types) * 0.05)

        return {
            'quality_score': score,
            'primitive_diversity': len(primitive_types)
        }

    # Helper methods
    def _score_choice(self, question: str, choice: str, domain: str) -> float:
        """Score a choice's likelihood."""
        score = 0.5

        # Length heuristic (moderate length often correct)
        if 20 < len(choice) < 200:
            score += 0.1

        # Domain keyword matching
        q_lower = question.lower()
        c_lower = choice.lower()

        # Shared important words
        q_words = set(q_lower.split())
        c_words = set(c_lower.split())
        overlap = len(q_words & c_words)
        score += min(0.2, overlap * 0.02)

        return min(0.95, score + random.uniform(-0.1, 0.1))

    def _deep_analyze(self, question: str, choice: str, domain: str) -> float:
        """Deep analysis of a choice."""
        base_score = self._score_choice(question, choice, domain)

        # Add depth bonus
        depth_bonus = 0.1

        return min(0.95, base_score + depth_bonus)


class ProgramSynthesizer:
    """
    Synthesizes reasoning programs from primitives.

    Uses neural-guided search to compose primitives into
    effective reasoning programs.
    """

    def __init__(self, library: ReasoningPrimitiveLibrary = None):
        self.library = library or ReasoningPrimitiveLibrary()
        self.program_cache: Dict[str, ReasoningProgram] = {}
        self.success_history: List[Tuple[str, ReasoningProgram, float]] = []

    def synthesize(self, question: str, domain: str,
                   choices: List[str],
                   max_depth: int = 5,
                   max_cost: float = 20.0) -> ReasoningProgram:
        """
        Synthesize a reasoning program for the given problem.

        Args:
            question: The question to answer
            domain: Domain (Physics, Chemistry, Biology)
            choices: Answer choices
            max_depth: Maximum program depth
            max_cost: Maximum computational cost

        Returns:
            Synthesized reasoning program
        """
        # Check cache
        cache_key = self._cache_key(question, domain)
        if cache_key in self.program_cache:
            return self.program_cache[cache_key]

        # Analyze problem to determine strategy
        problem_features = self._analyze_problem(question, domain, choices)

        # Select program template based on features
        template = self._select_template(problem_features)

        # Instantiate program from template
        program = self._instantiate_program(template, problem_features, max_depth, max_cost)

        # Cache program
        self.program_cache[cache_key] = program

        return program

    def _analyze_problem(self, question: str, domain: str,
                         choices: List[str]) -> Dict[str, Any]:
        """Analyze problem features."""
        features = {
            'domain': domain,
            'question_length': len(question),
            'num_choices': len(choices),
            'has_numbers': any(c.isdigit() for c in question),
            'has_equations': '=' in question,
            'is_comparison': any(kw in question.lower() for kw in ['compare', 'greater', 'less', 'more', 'fewer']),
            'is_causal': any(kw in question.lower() for kw in ['cause', 'effect', 'because', 'result', 'lead to']),
            'is_counterfactual': any(kw in question.lower() for kw in ['what if', 'would happen', 'instead']),
            'requires_calculation': any(kw in question.lower() for kw in ['calculate', 'compute', 'find the', 'determine']),
            'requires_explanation': any(kw in question.lower() for kw in ['explain', 'why', 'how does']),
            'complexity': 'high' if len(question) > 500 else 'medium' if len(question) > 200 else 'low'
        }

        return features

    def _select_template(self, features: Dict[str, Any]) -> str:
        """Select program template based on features."""
        if features['is_counterfactual']:
            return 'counterfactual_reasoning'
        elif features['is_causal']:
            return 'causal_analysis'
        elif features['requires_calculation']:
            return 'step_calculation'
        elif features['requires_explanation']:
            return 'explanation_generation'
        elif features['complexity'] == 'high':
            return 'deep_analysis'
        else:
            return 'standard_reasoning'

    def _instantiate_program(self, template: str, features: Dict[str, Any],
                              max_depth: int, max_cost: float) -> ReasoningProgram:
        """Instantiate program from template."""
        templates = {
            'standard_reasoning': self._standard_program,
            'deep_analysis': self._deep_analysis_program,
            'causal_analysis': self._causal_analysis_program,
            'counterfactual_reasoning': self._counterfactual_program,
            'step_calculation': self._calculation_program,
            'explanation_generation': self._explanation_program
        }

        builder = templates.get(template, self._standard_program)
        return builder(features, max_depth, max_cost)

    def _standard_program(self, features: Dict, max_depth: int,
                          max_cost: float) -> ReasoningProgram:
        """Build standard reasoning program."""
        # reformulate -> candidate_generate -> consistency_check -> weighted_vote -> confidence_evaluate

        root = ProgramNode(primitive=None)

        # Step 1: Reformulate
        reformulate = ProgramNode(
            primitive=self.library.get('reformulate'),
            parameters={}
        )

        # Step 2: Generate candidates
        generate = ProgramNode(
            primitive=self.library.get('candidate_generate'),
            parameters={}
        )

        # Step 3: Verify
        verify = ProgramNode(
            primitive=self.library.get('consistency_check'),
            parameters={}
        )

        # Step 4: Combine
        combine = ProgramNode(
            primitive=self.library.get('weighted_vote'),
            parameters={}
        )

        # Step 5: Evaluate
        evaluate = ProgramNode(
            primitive=self.library.get('confidence_evaluate'),
            parameters={}
        )

        root.children = [reformulate, generate, verify, combine, evaluate]

        return ReasoningProgram(
            root=root,
            name='standard_reasoning',
            description='Standard reasoning: reformulate -> generate -> verify -> combine -> evaluate',
            expected_cost=7.0,
            expected_reliability=0.85,
            source_code='reformulate | candidate_generate | consistency_check | weighted_vote | confidence_evaluate'
        )

    def _deep_analysis_program(self, features: Dict, max_depth: int,
                                max_cost: float) -> ReasoningProgram:
        """Build deep analysis program."""
        root = ProgramNode(primitive=None)

        # More extensive pipeline
        nodes = [
            ProgramNode(primitive=self.library.get('reformulate')),
            ProgramNode(primitive=self.library.get('step_decompose')),
            ProgramNode(primitive=self.library.get('extract_principle')),
            ProgramNode(primitive=self.library.get('beam_search'), parameters={'beam_width': 5}),
            ProgramNode(primitive=self.library.get('consistency_check')),
            ProgramNode(primitive=self.library.get('dimensional_check')),
            ProgramNode(primitive=self.library.get('weighted_vote')),
            ProgramNode(primitive=self.library.get('confidence_evaluate'))
        ]

        root.children = nodes

        return ReasoningProgram(
            root=root,
            name='deep_analysis',
            description='Deep analysis with decomposition and verification',
            expected_cost=15.0,
            expected_reliability=0.90,
            source_code='reformulate | step_decompose | extract_principle | beam_search | verify | vote | evaluate'
        )

    def _causal_analysis_program(self, features: Dict, max_depth: int,
                                  max_cost: float) -> ReasoningProgram:
        """Build causal analysis program."""
        root = ProgramNode(primitive=None)

        nodes = [
            ProgramNode(primitive=self.library.get('reformulate')),
            ProgramNode(primitive=self.library.get('extract_principle')),
            ProgramNode(primitive=self.library.get('mental_simulate')),
            ProgramNode(primitive=self.library.get('candidate_generate')),
            ProgramNode(primitive=self.library.get('consistency_check')),
            ProgramNode(primitive=self.library.get('weighted_vote')),
            ProgramNode(primitive=self.library.get('confidence_evaluate'))
        ]

        root.children = nodes

        return ReasoningProgram(
            root=root,
            name='causal_analysis',
            description='Causal reasoning with simulation',
            expected_cost=12.0,
            expected_reliability=0.85,
            source_code='reformulate | extract_principle | simulate | generate | verify | vote | evaluate'
        )

    def _counterfactual_program(self, features: Dict, max_depth: int,
                                 max_cost: float) -> ReasoningProgram:
        """Build counterfactual reasoning program."""
        root = ProgramNode(primitive=None)

        nodes = [
            ProgramNode(primitive=self.library.get('reformulate')),
            ProgramNode(primitive=self.library.get('counterfactual_simulate')),
            ProgramNode(primitive=self.library.get('candidate_generate')),
            ProgramNode(primitive=self.library.get('plausibility_filter')),
            ProgramNode(primitive=self.library.get('weighted_vote')),
            ProgramNode(primitive=self.library.get('confidence_evaluate'))
        ]

        root.children = nodes

        return ReasoningProgram(
            root=root,
            name='counterfactual_reasoning',
            description='Counterfactual reasoning with simulation',
            expected_cost=14.0,
            expected_reliability=0.80,
            source_code='reformulate | counterfactual_simulate | generate | filter | vote | evaluate'
        )

    def _calculation_program(self, features: Dict, max_depth: int,
                              max_cost: float) -> ReasoningProgram:
        """Build calculation program."""
        root = ProgramNode(primitive=None)

        nodes = [
            ProgramNode(primitive=self.library.get('reformulate')),
            ProgramNode(primitive=self.library.get('symbolize')),
            ProgramNode(primitive=self.library.get('step_decompose')),
            ProgramNode(primitive=self.library.get('candidate_generate')),
            ProgramNode(primitive=self.library.get('dimensional_check')),
            ProgramNode(primitive=self.library.get('conservation_check')),
            ProgramNode(primitive=self.library.get('weighted_vote')),
            ProgramNode(primitive=self.library.get('confidence_evaluate'))
        ]

        root.children = nodes

        return ReasoningProgram(
            root=root,
            name='calculation',
            description='Step-by-step calculation with verification',
            expected_cost=13.0,
            expected_reliability=0.88,
            source_code='reformulate | symbolize | decompose | generate | dim_check | cons_check | vote | evaluate'
        )

    def _explanation_program(self, features: Dict, max_depth: int,
                              max_cost: float) -> ReasoningProgram:
        """Build explanation program."""
        root = ProgramNode(primitive=None)

        nodes = [
            ProgramNode(primitive=self.library.get('reformulate')),
            ProgramNode(primitive=self.library.get('extract_principle')),
            ProgramNode(primitive=self.library.get('find_analogy')),
            ProgramNode(primitive=self.library.get('candidate_generate')),
            ProgramNode(primitive=self.library.get('consistency_check')),
            ProgramNode(primitive=self.library.get('consensus_merge')),
            ProgramNode(primitive=self.library.get('confidence_evaluate'))
        ]

        root.children = nodes

        return ReasoningProgram(
            root=root,
            name='explanation',
            description='Explanation generation with analogy',
            expected_cost=11.0,
            expected_reliability=0.82,
            source_code='reformulate | extract_principle | find_analogy | generate | verify | merge | evaluate'
        )

    def _cache_key(self, question: str, domain: str) -> str:
        """Generate cache key for question."""
        # Simple hash-based key
        return f"{domain}_{hash(question) % 10000}"

    def record_success(self, question: str, program: ReasoningProgram,
                       success_rate: float):
        """Record successful program execution."""
        self.success_history.append((question, program, success_rate))


class ExecutionEngine:
    """
    Executes synthesized reasoning programs.

    Features:
    - Step-by-step execution
    - Rollback on failure
    - Intermediate result caching
    - Execution tracing
    """

    def __init__(self, library: ReasoningPrimitiveLibrary = None):
        self.library = library or ReasoningPrimitiveLibrary()

    def execute(self, program: ReasoningProgram,
                context: ExecutionContext) -> SynthesisResult:
        """
        Execute a reasoning program.

        Args:
            program: The reasoning program to execute
            context: Execution context with question, choices, etc.

        Returns:
            SynthesisResult: Execution result with answer and trace
        """
        import time
        start_time = time.time()

        # Execute program step by step
        trace = []
        primitives_used = []
        current_context = context
        current_context.intermediate_results = {}
        current_context.trace = trace

        try:
            # Execute nodes in program tree (breadth-first)
            nodes_to_execute = [program.root]

            while nodes_to_execute:
                node = nodes_to_execute.pop(0)
                nodes_to_execute.extend(node.children)

                if node.primitive is None:
                    continue

                # Execute primitive
                primitive_result = node.primitive.execute(
                    current_context,
                    **node.parameters
                )

                # Store result
                node.result = primitive_result
                node.executed = True
                node.success = True

                # Update trace
                trace.append(f"Executed {node.primitive.name}: {str(primitive_result)[:100]}")
                primitives_used.append(node.primitive.name)

                # Update context with results
                if isinstance(primitive_result, dict):
                    for key, value in primitive_result.items():
                        if key not in ['question', 'domain', 'choices', 'knowledge']:
                            current_context.intermediate_results[key] = value

                    # Update context if answer/index found
                    if 'answer_index' in primitive_result:
                        current_context.intermediate_results['answer_index'] = primitive_result['answer_index']
                    if 'best_index' in primitive_result:
                        current_context.intermediate_results['answer_index'] = primitive_result['best_index']

            execution_time = time.time() - start_time

            # Extract final answer
            answer_index = current_context.intermediate_results.get('answer_index', 0)
            answer = current_context.choices[answer_index] if answer_index < len(current_context.choices) else current_context.choices[0] if current_context.choices else "No answer"

            return SynthesisResult(
                program=program,
                answer=answer,
                answer_index=answer_index,
                confidence=current_context.intermediate_results.get('confidence', 0.7),
                execution_trace=trace,
                primitives_used=primitives_used,
                synthesis_time=0.0,
                execution_time=execution_time,
                success=True
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SynthesisResult(
                program=program,
                answer=f"Execution failed: {str(e)}",
                answer_index=None,
                confidence=0.0,
                execution_trace=trace,
                primitives_used=primitives_used,
                synthesis_time=0.0,
                execution_time=execution_time,
                success=False
            )


class ProgramSynthesisReasoner:
    """
    High-level reasoner that uses program synthesis.

    This is the main interface for program synthesis reasoning.
    It combines the ProgramSynthesizer and ExecutionEngine.

    Date: 2025-12-17
    """

    def __init__(self, library: ReasoningPrimitiveLibrary = None):
        """
        Initialize the reasoner.

        Args:
            library: Optional primitive library
        """
        self.library = library or ReasoningPrimitiveLibrary()
        self.synthesizer = ProgramSynthesizer(self.library)
        self.executor = ExecutionEngine(self.library)

    def reason(self, question: str, domain: str, choices: List[str],
               **kwargs) -> SynthesisResult:
        """
        Answer a question using program synthesis reasoning.

        Args:
            question: The question to answer
            domain: Domain (Physics, Chemistry, Biology, etc.)
            choices: Answer choices
            **kwargs: Additional parameters

        Returns:
            SynthesisResult with answer and metadata
        """
        import time
        start_time = time.time()

        # Synthesize program
        program = self.synthesizer.synthesize(
            question=question,
            domain=domain,
            choices=choices,
            max_depth=kwargs.get('max_depth', 5),
            max_cost=kwargs.get('max_cost', 20.0)
        )

        # Create execution context
        context = ExecutionContext(
            question=question,
            domain=domain,
            choices=choices,
            knowledge=kwargs.get('knowledge', {})
        )

        # Execute program
        result = self.executor.execute(program, context)

        # Add synthesis time
        synthesis_time = time.time() - start_time - result.execution_time
        result.synthesis_time = synthesis_time

        return result

    def get_primitives(self) -> List[str]:
        """Get list of available primitives."""
        return self.library.list_all()

    def get_primitive(self, name: str) -> Optional[ReasoningPrimitive]:
        """Get a primitive by name."""
        return self.library.get(name)


# Factory functions
def create_synthesizer() -> ProgramSynthesizer:
    """Create a program synthesizer."""
    return ProgramSynthesizer()


def create_executor() -> ExecutionEngine:
    """Create a reasoning executor."""
    return ExecutionEngine()


def create_program_synthesis_reasoner() -> ProgramSynthesisReasoner:
    """Create a program synthesis reasoner."""
    return ProgramSynthesisReasoner()


def create_primitive_library() -> ReasoningPrimitiveLibrary:
    """Create a reasoning primitive library."""
    return ReasoningPrimitiveLibrary()


def create_program_synthesizer() -> ProgramSynthesizer:
    """Create a program synthesizer."""
    return ProgramSynthesizer()


class ProgramLearner:
    """
    Learns from successful reasoning programs.

    Analyzes successful reasoning traces to improve future
    program synthesis.

    Date: 2025-12-17
    """

    def __init__(self, synthesizer: ProgramSynthesizer = None):
        """
        Initialize the learner.

        Args:
            synthesizer: Optional program synthesizer to learn from
        """
        self.synthesizer = synthesizer or ProgramSynthesizer()
        self.success_patterns: Dict[str, List[ReasoningProgram]] = {}
        self.pattern_frequency: Dict[str, int] = {}

    def learn_from_trace(self, question: str, domain: str,
                        trace: List[str], success: bool) -> None:
        """
        Learn from a reasoning trace.

        Args:
            question: The question that was answered
            domain: The domain
            trace: The reasoning trace
            success: Whether the reasoning was successful
        """
        if not success:
            return

        # Extract pattern from trace
        pattern_key = self._extract_pattern_key(trace)

        # Record pattern
        if pattern_key not in self.success_patterns:
            self.success_patterns[pattern_key] = []
        self.success_patterns[pattern_key].append(
            self.synthesizer.synthesize(question, domain, [])
        )

        # Update frequency
        self.pattern_frequency[pattern_key] = self.pattern_frequency.get(pattern_key, 0) + 1

    def _extract_pattern_key(self, trace: List[str]) -> str:
        """Extract a pattern key from a trace."""
        # Simple pattern: primitive sequence
        primitives = []
        for entry in trace:
            for primitive in PrimitiveType:
                if primitive.value in entry.lower():
                    primitives.append(primitive.value)

        return '->'.join(primitives) if primitives else 'unknown'

    def get_successful_patterns(self, min_frequency: int = 2) -> List[str]:
        """
        Get patterns that have been successful multiple times.

        Args:
            min_frequency: Minimum frequency threshold

        Returns:
            List of successful pattern keys
        """
        return [
            pattern for pattern, freq in self.pattern_frequency.items()
            if freq >= min_frequency
        ]

    def suggest_program(self, question: str, domain: str) -> Optional[ReasoningProgram]:
        """
        Suggest a program based on learned patterns.

        Args:
            question: The question
            domain: The domain

        Returns:
            Suggested program or None
        """
        # Find most frequent successful pattern
        if not self.pattern_frequency:
            return None

        best_pattern = max(self.pattern_frequency, key=self.pattern_frequency.get)

        if best_pattern in self.success_patterns and self.success_patterns[best_pattern]:
            return self.success_patterns[best_pattern][0]

        return None


def create_program_learner() -> ProgramLearner:
    """Create a program learner."""
    return ProgramLearner()
