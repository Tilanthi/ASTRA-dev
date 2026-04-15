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
V50 Self-Improving Meta-Learner
================================

The system learns to reason better over time.

Key Innovations:
1. Failure Analysis - When wrong, deeply analyze WHY
2. Strategy Abstraction - Extract generalizable strategies from success
3. Difficulty Curriculum - Generate progressively harder problems
4. Competence Boundaries - Know what it doesn't know

Components:
1. FailureAnalyzer - Analyze reasoning failures
2. StrategyAbstractor - Extract reusable strategies
3. CurriculumGenerator - Generate adaptive training problems
4. CompetenceTracker - Track and expand competence boundaries
5. MetaLearningSystem - Unified meta-learning

Date: 2025-12-17
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
import random
import math
import time
import json


class FailureType(Enum):
    """Types of reasoning failures."""
    KNOWLEDGE_GAP = "knowledge_gap"  # Missing required knowledge
    REASONING_ERROR = "reasoning_error"  # Logical/reasoning mistake
    STRATEGY_MISMATCH = "strategy_mismatch"  # Wrong approach for problem type
    CALCULATION_ERROR = "calculation_error"  # Mathematical/computational error
    COMPREHENSION_ERROR = "comprehension_error"  # Misunderstood the question
    OVERCONFIDENCE = "overconfidence"  # Too confident in wrong answer
    UNDERCONFIDENCE = "underconfidence"  # Not confident enough in right answer
    TIME_PRESSURE = "time_pressure"  # Ran out of compute/time
    DISTRACTOR_TRAP = "distractor_trap"  # Fell for misleading option


class CompetenceLevel(Enum):
    """Levels of competence."""
    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


@dataclass
class ReasoningAttempt:
    """Record of a single reasoning attempt."""
    question: str
    domain: str
    choices: List[str]
    predicted_answer: str
    predicted_index: int
    correct_answer: str
    correct_index: int
    confidence: float
    reasoning_trace: List[str]
    strategies_used: List[str]
    time_taken: float
    success: bool


@dataclass
class FailureAnalysis:
    """Analysis of a reasoning failure."""
    attempt: ReasoningAttempt
    failure_type: FailureType
    root_cause: str
    contributing_factors: List[str]
    missing_knowledge: List[str]
    reasoning_flaws: List[str]
    suggested_improvements: List[str]
    confidence: float


@dataclass
class Strategy:
    """A reasoning strategy."""
    name: str
    description: str
    applicable_domains: List[str]
    applicable_problem_types: List[str]
    steps: List[str]
    success_rate: float
    usage_count: int
    average_confidence: float


@dataclass
class CompetenceBoundary:
    """Boundary of competence in a domain."""
    domain: str
    level: CompetenceLevel
    confident_topics: List[str]
    uncertain_topics: List[str]
    unknown_topics: List[str]
    accuracy_by_difficulty: Dict[str, float]
    improvement_rate: float


@dataclass
class CurriculumProblem:
    """A curriculum-generated problem."""
    question: str
    domain: str
    difficulty: float
    target_skill: str
    choices: List[str]
    correct_index: int
    explanation: str


class FailureAnalyzer:
    """
    Analyze reasoning failures to identify root causes.

    When wrong, deeply analyze WHY:
    - Was it a knowledge gap?
    - Reasoning error?
    - Wrong strategy?
    """

    def __init__(self):
        self.failure_patterns: Dict[FailureType, List[FailureAnalysis]] = defaultdict(list)
        self.common_mistakes: Dict[str, int] = defaultdict(int)

    def analyze_failure(self, attempt: ReasoningAttempt) -> FailureAnalysis:
        """
        Analyze why a reasoning attempt failed.

        Args:
            attempt: The failed reasoning attempt

        Returns:
            FailureAnalysis with root cause and suggestions
        """
        if attempt.success:
            return self._analyze_near_miss(attempt)

        # Determine failure type
        failure_type = self._classify_failure(attempt)

        # Find root cause
        root_cause = self._find_root_cause(attempt, failure_type)

        # Identify contributing factors
        contributing = self._find_contributing_factors(attempt, failure_type)

        # Identify missing knowledge
        missing_knowledge = self._identify_missing_knowledge(attempt)

        # Identify reasoning flaws
        reasoning_flaws = self._identify_reasoning_flaws(attempt)

        # Generate suggestions
        suggestions = self._generate_suggestions(failure_type, root_cause, missing_knowledge)

        analysis = FailureAnalysis(
            attempt=attempt,
            failure_type=failure_type,
            root_cause=root_cause,
            contributing_factors=contributing,
            missing_knowledge=missing_knowledge,
            reasoning_flaws=reasoning_flaws,
            suggested_improvements=suggestions,
            confidence=0.8
        )

        # Record pattern
        self.failure_patterns[failure_type].append(analysis)
        self.common_mistakes[root_cause] += 1

        return analysis

    def _classify_failure(self, attempt: ReasoningAttempt) -> FailureType:
        """Classify the type of failure."""
        trace = ' '.join(attempt.reasoning_trace).lower()
        question = attempt.question.lower()

        # Check for overconfidence
        if attempt.confidence > 0.8:
            return FailureType.OVERCONFIDENCE

        # Check for calculation errors
        if any(kw in trace for kw in ['calculate', 'compute', 'equals', '=']):
            if any(kw in trace for kw in ['error', 'mistake', 'wrong']):
                return FailureType.CALCULATION_ERROR

        # Check for comprehension errors
        predicted = attempt.predicted_answer.lower()
        correct = attempt.correct_answer.lower()
        if 'not' in question and 'not' not in predicted:
            return FailureType.COMPREHENSION_ERROR

        # Check for strategy mismatch
        if len(attempt.strategies_used) == 0:
            return FailureType.STRATEGY_MISMATCH

        # Check for knowledge gap
        if any(kw in trace for kw in ['unknown', 'unclear', 'uncertain', 'missing']):
            return FailureType.KNOWLEDGE_GAP

        # Check for distractor trap
        # If answer was close to correct but not quite
        if self._similarity(predicted, correct) > 0.5:
            return FailureType.DISTRACTOR_TRAP

        # Default to reasoning error
        return FailureType.REASONING_ERROR

    def _find_root_cause(self, attempt: ReasoningAttempt, failure_type: FailureType) -> str:
        """Find the root cause of failure."""
        causes = {
            FailureType.KNOWLEDGE_GAP: "Missing domain-specific knowledge",
            FailureType.REASONING_ERROR: "Logical inference error",
            FailureType.STRATEGY_MISMATCH: "Applied wrong reasoning strategy",
            FailureType.CALCULATION_ERROR: "Mathematical computation error",
            FailureType.COMPREHENSION_ERROR: "Misinterpreted question requirements",
            FailureType.OVERCONFIDENCE: "Insufficient verification of high-confidence answer",
            FailureType.UNDERCONFIDENCE: "Failed to commit to likely correct answer",
            FailureType.TIME_PRESSURE: "Insufficient time for thorough reasoning",
            FailureType.DISTRACTOR_TRAP: "Selected plausible but incorrect distractor"
        }

        base_cause = causes.get(failure_type, "Unknown cause")

        # Add specifics from trace
        if attempt.reasoning_trace:
            last_step = attempt.reasoning_trace[-1] if attempt.reasoning_trace else ""
            if 'error' in last_step.lower():
                base_cause += f" - occurred at: {last_step[:50]}"

        return base_cause

    def _find_contributing_factors(self, attempt: ReasoningAttempt,
                                    failure_type: FailureType) -> List[str]:
        """Find contributing factors to failure."""
        factors = []

        # Time pressure
        if attempt.time_taken < 1.0:
            factors.append("Insufficient reasoning time")

        # Low confidence but still wrong
        if attempt.confidence < 0.5:
            factors.append("Low confidence suggests uncertainty")

        # Limited strategies
        if len(attempt.strategies_used) < 2:
            factors.append("Limited reasoning strategies applied")

        # Short trace
        if len(attempt.reasoning_trace) < 3:
            factors.append("Shallow reasoning depth")

        # Domain-specific
        domain = attempt.domain.lower()
        if 'physics' in domain:
            factors.append("Physics requires quantitative verification")
        elif 'chemistry' in domain:
            factors.append("Chemistry requires stoichiometric checking")
        elif 'biology' in domain:
            factors.append("Biology requires pathway/mechanism analysis")

        return factors

    def _identify_missing_knowledge(self, attempt: ReasoningAttempt) -> List[str]:
        """Identify knowledge that was missing."""
        missing = []

        question = attempt.question.lower()
        correct = attempt.correct_answer.lower()

        # Domain-specific knowledge identification
        physics_concepts = ['momentum', 'energy', 'force', 'field', 'wave', 'quantum']
        chemistry_concepts = ['reaction', 'equilibrium', 'bond', 'orbital', 'redox']
        biology_concepts = ['enzyme', 'pathway', 'gene', 'protein', 'membrane']

        for concept in physics_concepts:
            if concept in question or concept in correct:
                missing.append(f"Physics: {concept} concepts")

        for concept in chemistry_concepts:
            if concept in question or concept in correct:
                missing.append(f"Chemistry: {concept} concepts")

        for concept in biology_concepts:
            if concept in question or concept in correct:
                missing.append(f"Biology: {concept} concepts")

        return missing[:5]  # Top 5 missing

    def _identify_reasoning_flaws(self, attempt: ReasoningAttempt) -> List[str]:
        """Identify flaws in the reasoning trace."""
        flaws = []

        trace = attempt.reasoning_trace

        # Check for incomplete reasoning
        if len(trace) < 3:
            flaws.append("Reasoning chain too short")

        # Check for missing verification
        trace_text = ' '.join(trace).lower()
        if 'verify' not in trace_text and 'check' not in trace_text:
            flaws.append("No verification step")

        # Check for missing domain principles
        if 'principle' not in trace_text and 'law' not in trace_text:
            flaws.append("No domain principles invoked")

        # Check for jumping to conclusions
        if len(trace) > 0 and 'answer' in trace[0].lower():
            flaws.append("Jumped to conclusion without analysis")

        return flaws

    def _generate_suggestions(self, failure_type: FailureType,
                               root_cause: str,
                               missing_knowledge: List[str]) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []

        # Type-specific suggestions
        type_suggestions = {
            FailureType.KNOWLEDGE_GAP: [
                "Retrieve relevant domain knowledge before answering",
                "Use external knowledge sources when uncertain"
            ],
            FailureType.REASONING_ERROR: [
                "Add step-by-step verification of logical inferences",
                "Use multiple reasoning paths and check consistency"
            ],
            FailureType.STRATEGY_MISMATCH: [
                "Analyze problem type before selecting strategy",
                "Maintain a repertoire of domain-specific strategies"
            ],
            FailureType.CALCULATION_ERROR: [
                "Double-check all numerical calculations",
                "Use dimensional analysis to verify results"
            ],
            FailureType.COMPREHENSION_ERROR: [
                "Re-read question for negations and qualifiers",
                "Paraphrase question before answering"
            ],
            FailureType.OVERCONFIDENCE: [
                "Increase verification threshold for high-confidence answers",
                "Consider alternative interpretations"
            ],
            FailureType.DISTRACTOR_TRAP: [
                "Analyze why each wrong answer is wrong",
                "Look for subtle differences between similar answers"
            ]
        }

        suggestions.extend(type_suggestions.get(failure_type, []))

        # Knowledge-specific suggestions
        for knowledge in missing_knowledge[:2]:
            suggestions.append(f"Review: {knowledge}")

        return suggestions

    def _analyze_near_miss(self, attempt: ReasoningAttempt) -> FailureAnalysis:
        """Analyze a successful but low-confidence attempt."""
        return FailureAnalysis(
            attempt=attempt,
            failure_type=FailureType.UNDERCONFIDENCE,
            root_cause="Correct answer but low confidence",
            contributing_factors=["Uncertainty despite correct reasoning"],
            missing_knowledge=[],
            reasoning_flaws=["Confidence calibration needed"],
            suggested_improvements=["Trust verified reasoning more"],
            confidence=0.7
        )

    def _similarity(self, s1: str, s2: str) -> float:
        """Compute string similarity."""
        if not s1 or not s2:
            return 0.0

        s1_words = set(s1.lower().split())
        s2_words = set(s2.lower().split())

        intersection = len(s1_words & s2_words)
        union = len(s1_words | s2_words)

        return intersection / max(union, 1)

    def get_common_failures(self, n: int = 10) -> List[Tuple[str, int]]:
        """Get most common failure patterns."""
        sorted_mistakes = sorted(self.common_mistakes.items(),
                                 key=lambda x: x[1], reverse=True)
        return sorted_mistakes[:n]


class StrategyAbstractor:
    """
    Extract reusable strategies from successful reasoning.

    Learn WHAT works and WHEN to apply it.
    """

    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.strategy_performance: Dict[str, List[float]] = defaultdict(list)

    def extract_strategy(self, attempt: ReasoningAttempt) -> Optional[Strategy]:
        """
        Extract a strategy from a successful reasoning attempt.

        Args:
            attempt: Successful reasoning attempt

        Returns:
            Extracted strategy if novel and useful
        """
        if not attempt.success:
            return None

        # Generate strategy signature
        signature = self._compute_signature(attempt)

        # Check if strategy already exists
        if signature in self.strategies:
            # Update existing strategy
            self._update_strategy(signature, attempt)
            return self.strategies[signature]

        # Extract new strategy
        strategy = Strategy(
            name=f"strategy_{len(self.strategies)}",
            description=self._generate_description(attempt),
            applicable_domains=[attempt.domain],
            applicable_problem_types=self._infer_problem_types(attempt),
            steps=self._extract_steps(attempt),
            success_rate=1.0,  # First success
            usage_count=1,
            average_confidence=attempt.confidence
        )

        self.strategies[signature] = strategy
        return strategy

    def _compute_signature(self, attempt: ReasoningAttempt) -> str:
        """Compute a signature for the strategy."""
        # Based on strategies used and domain
        components = sorted(attempt.strategies_used)
        return f"{attempt.domain}:{':'.join(components)}"

    def _update_strategy(self, signature: str, attempt: ReasoningAttempt):
        """Update an existing strategy with new data."""
        strategy = self.strategies[signature]

        # Update success rate
        self.strategy_performance[signature].append(1.0 if attempt.success else 0.0)
        performances = self.strategy_performance[signature]
        strategy.success_rate = sum(performances) / len(performances)

        # Update usage count
        strategy.usage_count += 1

        # Update average confidence
        strategy.average_confidence = (
            strategy.average_confidence * 0.9 + attempt.confidence * 0.1
        )

        # Add domain if new
        if attempt.domain not in strategy.applicable_domains:
            strategy.applicable_domains.append(attempt.domain)

    def _generate_description(self, attempt: ReasoningAttempt) -> str:
        """Generate a description of the strategy."""
        strategies = attempt.strategies_used
        domain = attempt.domain

        if not strategies:
            return f"Direct reasoning for {domain} problems"

        return f"Combined {', '.join(strategies)} approach for {domain}"

    def _infer_problem_types(self, attempt: ReasoningAttempt) -> List[str]:
        """Infer problem types this strategy applies to."""
        types = []
        question = attempt.question.lower()

        # Detect problem types from question
        if any(kw in question for kw in ['calculate', 'compute', 'find the value']):
            types.append('calculation')
        if any(kw in question for kw in ['explain', 'why', 'how does']):
            types.append('explanation')
        if any(kw in question for kw in ['compare', 'difference', 'similar']):
            types.append('comparison')
        if any(kw in question for kw in ['predict', 'what will', 'expect']):
            types.append('prediction')
        if any(kw in question for kw in ['what if', 'would happen']):
            types.append('counterfactual')

        return types if types else ['general']

    def _extract_steps(self, attempt: ReasoningAttempt) -> List[str]:
        """Extract reasoning steps from trace."""
        steps = []

        for trace_item in attempt.reasoning_trace:
            # Generalize specific values
            generalized = self._generalize_step(trace_item)
            if generalized and generalized not in steps:
                steps.append(generalized)

        return steps[:10]  # Top 10 steps

    def _generalize_step(self, step: str) -> str:
        """Generalize a specific step to a reusable form."""
        # Remove specific values, keep structure
        import re

        # Replace numbers with [NUMBER]
        generalized = re.sub(r'\d+\.?\d*', '[VALUE]', step)

        # Replace quoted strings with [TEXT]
        generalized = re.sub(r'"[^"]*"', '[TEXT]', generalized)
        generalized = re.sub(r"'[^']*'", '[TEXT]', generalized)

        return generalized[:100]  # Limit length

    def get_strategy_for_problem(self, domain: str,
                                  problem_type: str) -> Optional[Strategy]:
        """Get best strategy for a problem type."""
        candidates = []

        for strategy in self.strategies.values():
            if domain in strategy.applicable_domains:
                if problem_type in strategy.applicable_problem_types:
                    candidates.append(strategy)

        if not candidates:
            return None

        # Return highest success rate
        return max(candidates, key=lambda s: s.success_rate * s.average_confidence)

    def get_all_strategies(self) -> List[Strategy]:
        """Get all learned strategies."""
        return list(self.strategies.values())


class CurriculumGenerator:
    """
    Generate progressively harder problems.

    Adaptive curriculum that targets weaknesses.
    """

    def __init__(self):
        self.problem_templates: Dict[str, List[Dict]] = self._load_templates()
        self.difficulty_history: Dict[str, List[float]] = defaultdict(list)

    def _load_templates(self) -> Dict[str, List[Dict]]:
        """Load problem templates by domain."""
        return {
            'Physics': [
                {
                    'template': "A {object} with mass {mass} kg moves with velocity {velocity} m/s. What is its {quantity}?",
                    'variables': ['object', 'mass', 'velocity', 'quantity'],
                    'difficulty_factors': ['mass_magnitude', 'concept_complexity'],
                    'skills': ['mechanics', 'kinematics']
                },
                {
                    'template': "In a {system_type} system, if {condition}, what happens to {variable}?",
                    'variables': ['system_type', 'condition', 'variable'],
                    'difficulty_factors': ['system_complexity', 'multi_step'],
                    'skills': ['thermodynamics', 'equilibrium']
                }
            ],
            'Chemistry': [
                {
                    'template': "For the reaction {reaction}, calculate the {quantity} when {conditions}.",
                    'variables': ['reaction', 'quantity', 'conditions'],
                    'difficulty_factors': ['reaction_complexity', 'calculation_steps'],
                    'skills': ['stoichiometry', 'equilibrium']
                },
                {
                    'template': "What is the {property} of {compound} under {conditions}?",
                    'variables': ['property', 'compound', 'conditions'],
                    'difficulty_factors': ['property_type', 'compound_complexity'],
                    'skills': ['thermochemistry', 'bonding']
                }
            ],
            'Biology': [
                {
                    'template': "In the {pathway} pathway, what is the role of {component}?",
                    'variables': ['pathway', 'component'],
                    'difficulty_factors': ['pathway_complexity', 'mechanism_depth'],
                    'skills': ['metabolism', 'signaling']
                },
                {
                    'template': "How does {factor} affect {process} in {organism_type}?",
                    'variables': ['factor', 'process', 'organism_type'],
                    'difficulty_factors': ['interaction_complexity', 'regulation_type'],
                    'skills': ['regulation', 'physiology']
                }
            ]
        }

    def generate_problem(self, domain: str, target_difficulty: float,
                         target_skill: str = "") -> CurriculumProblem:
        """
        Generate a problem at specified difficulty.

        Args:
            domain: Target domain
            target_difficulty: Difficulty level (0.0 to 1.0)
            target_skill: Specific skill to target

        Returns:
            Generated curriculum problem
        """
        templates = self.problem_templates.get(domain, self.problem_templates['Physics'])

        # Select template matching skill
        if target_skill:
            matching = [t for t in templates if target_skill in t.get('skills', [])]
            template = random.choice(matching) if matching else random.choice(templates)
        else:
            template = random.choice(templates)

        # Generate problem from template
        question = self._instantiate_template(template, target_difficulty)

        # Generate choices
        choices, correct_idx = self._generate_choices(domain, target_difficulty)

        # Generate explanation
        explanation = self._generate_explanation(template, domain)

        return CurriculumProblem(
            question=question,
            domain=domain,
            difficulty=target_difficulty,
            target_skill=target_skill or template.get('skills', ['general'])[0],
            choices=choices,
            correct_index=correct_idx,
            explanation=explanation
        )

    def _instantiate_template(self, template: Dict, difficulty: float) -> str:
        """Instantiate a template with appropriate values."""
        question_template = template['template']
        variables = template['variables']

        # Generate values based on difficulty
        import random
        values = {}
        for var_name, var_range in variables.items():
            if isinstance(var_range, list):
                values[var_name] = random.choice(var_range)
            elif isinstance(var_range, dict):
                if 'range' in var_range:
                    start, end = var_range['range']
                    values[var_name] = random.uniform(start, end)
                else:
                    values[var_name] = var_range.get('default', 0)
            else:
                values[var_name] = var_range

        return question_template.format(**values)


class CompetenceTracker:
    """
    Tracks competence across domains and skills.

    Date: 2025-12-17
    """

    def __init__(self):
        self.competence_boundaries: Dict[str, CompetenceBoundary] = {}
        self.attempt_history: List[ReasoningAttempt] = []
        self.skill_levels: Dict[str, CompetenceLevel] = {}

    def record_attempt(self, attempt: ReasoningAttempt) -> None:
        """Record a reasoning attempt."""
        self.attempt_history.append(attempt)

        # Update skill level
        domain = attempt.domain
        if domain not in self.skill_levels:
            self.skill_levels[domain] = CompetenceLevel.NOVICE

        # Promote based on success
        if attempt.success:
            current = self.skill_levels[domain]
            levels = list(CompetenceLevel)
            idx = levels.index(current)
            if idx < len(levels) - 1:
                self.skill_levels[domain] = levels[idx + 1]

    def get_competence(self, domain: str) -> CompetenceBoundary:
        """Get competence boundary for a domain."""
        if domain not in self.competence_boundaries:
            level = self.skill_levels.get(domain, CompetenceLevel.NOVICE)
            self.competence_boundaries[domain] = CompetenceBoundary(
                domain=domain,
                level=level,
                threshold=0.5
            )
        return self.competence_boundaries[domain]

    def is_within_competence(self, domain: str, difficulty: float) -> bool:
        """Check if a problem is within competence."""
        boundary = self.get_competence(domain)
        return difficulty <= boundary.threshold


class MetaLearningSystem:
    """
    Unified meta-learning system.

    Integrates failure analysis, strategy abstraction,
    curriculum generation, and competence tracking.

    Date: 2025-12-17
    """

    def __init__(self):
        self.failure_analyzer = FailureAnalyzer()
        self.strategy_abstractor = StrategyAbstractor()
        self.curriculum_generator = CurriculumGenerator()
        self.competence_tracker = CompetenceTracker()
        self.learned_strategies: Dict[str, Strategy] = {}

    def analyze_failure(self, attempt: ReasoningAttempt) -> FailureAnalysis:
        """Analyze a failed reasoning attempt."""
        return self.failure_analyzer.analyze_failure(attempt)

    def extract_strategy(self, successful_attempt: ReasoningAttempt) -> Optional[Strategy]:
        """Extract strategy from successful reasoning."""
        strategy = self.strategy_abstractor.extract_strategy(
            [successful_attempt.reasoning_trace]
        )
        if strategy:
            self.learned_strategies[strategy.name] = strategy
        return strategy

    def generate_curriculum(self, domain: str, target_skills: List[str] = None) -> List[CurriculumProblem]:
        """Generate curriculum for learning."""
        competence = self.competence_tracker.get_competence(domain)
        return self.curriculum_generator.generate_sequence(
            domain,
            competence.level,
            target_skills
        )

    def update_competence(self, attempt: ReasoningAttempt) -> None:
        """Update competence model."""
        self.competence_tracker.record_attempt(attempt)


# Factory functions
def create_meta_learner() -> MetaLearningSystem:
    """Create a meta-learning system."""
    return MetaLearningSystem()


def create_failure_analyzer() -> FailureAnalyzer:
    """Create a failure analyzer."""
    return FailureAnalyzer()


def create_strategy_abstractor() -> StrategyAbstractor:
    """Create a strategy abstractor."""
    return StrategyAbstractor()


def create_curriculum_generator() -> CurriculumGenerator:
    """Create a curriculum generator."""
    return CurriculumGenerator()


def create_competence_tracker() -> CompetenceTracker:
    """Create a competence tracker."""
    return CompetenceTracker()


# Aliases for V50 naming
StrategyV50 = Strategy
