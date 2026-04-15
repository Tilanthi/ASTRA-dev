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
Meta-Cognitive Controller for STAN V40

Implements:
- Uncertainty estimation
- Strategy selection
- Resource allocation
- Self-monitoring and adaptation

Target: +10-15% through optimal strategy routing

Date: 2025-12-11
Version: 40.0
"""

import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum


class ReasoningStrategy(Enum):
    """Available reasoning strategies"""
    DIRECT = "direct"                   # Simple answer retrieval
    DECOMPOSITION = "decomposition"     # Multi-step decomposition
    HYPOTHESIS = "hypothesis"           # Hypothesis generation & testing
    FORMAL_LOGIC = "formal_logic"       # Z3/Prolog reasoning
    THEOREM_PROVING = "theorem_proving" # Neural-symbolic proof
    CAUSAL = "causal"                   # Causal world model
    RETRIEVAL = "retrieval"             # Knowledge retrieval
    SELF_CONSISTENCY = "self_consistency"  # Multiple samples + voting
    ENSEMBLE = "ensemble"               # Combine multiple strategies


class ConfidenceLevel(Enum):
    """Confidence levels"""
    VERY_LOW = "very_low"       # < 0.2
    LOW = "low"                 # 0.2 - 0.4
    MEDIUM = "medium"           # 0.4 - 0.6
    HIGH = "high"               # 0.6 - 0.8
    VERY_HIGH = "very_high"     # > 0.8


@dataclass
class ResourceBudget:
    """Resource budget for problem solving"""
    max_time_seconds: float = 30.0
    max_llm_calls: int = 5
    max_tool_calls: int = 10
    max_iterations: int = 3

    # Current usage
    time_used: float = 0.0
    llm_calls_used: int = 0
    tool_calls_used: int = 0
    iterations_used: int = 0

    def remaining_time(self) -> float:
        return max(0, self.max_time_seconds - self.time_used)

    def remaining_llm_calls(self) -> int:
        return max(0, self.max_llm_calls - self.llm_calls_used)

    def is_exhausted(self) -> bool:
        return (self.time_used >= self.max_time_seconds or
                self.llm_calls_used >= self.max_llm_calls)

    def to_dict(self) -> Dict:
        return {
            'time_remaining': self.remaining_time(),
            'llm_calls_remaining': self.remaining_llm_calls(),
            'tool_calls_remaining': self.max_tool_calls - self.tool_calls_used
        }


@dataclass
class StrategyResult:
    """Result from applying a strategy"""
    strategy: ReasoningStrategy
    answer: Any
    confidence: float
    reasoning_trace: List[str] = field(default_factory=list)
    resources_used: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'strategy': self.strategy.value,
            'answer': str(self.answer),
            'confidence': self.confidence,
            'trace_length': len(self.reasoning_trace)
        }


@dataclass
class ProblemCharacteristics:
    """Characteristics of a problem for strategy selection"""
    # Content type
    is_mathematical: bool = False
    is_logical: bool = False
    is_factual: bool = False
    is_causal: bool = False
    is_comparative: bool = False

    # Structure
    complexity: float = 0.5  # 0-1 scale
    has_multiple_parts: bool = False
    requires_precision: bool = False

    # Domain
    domain: str = "general"
    subdomain: str = ""

    # Format
    answer_type: str = "text"  # text, number, choice, yes_no

    def to_dict(self) -> Dict:
        return {
            'is_mathematical': self.is_mathematical,
            'is_logical': self.is_logical,
            'is_factual': self.is_factual,
            'is_causal': self.is_causal,
            'complexity': self.complexity,
            'domain': self.domain
        }


class ConfidenceEstimator:
    """
    Estimates confidence in answers.

    Uses multiple signals:
    - Self-consistency across samples
    - Strategy agreement
    - Knowledge coverage
    - Problem-answer alignment
    """

    def __init__(self):
        # Calibration data
        self.calibration_data: List[Tuple[float, bool]] = []
        self.calibration_bins: Dict[str, Tuple[int, int]] = {}

    def estimate(self, answer: Any,
                reasoning_trace: List[str],
                problem: ProblemCharacteristics,
                alternative_answers: List[Any] = None) -> float:
        """
        Estimate confidence in an answer.

        Returns:
            Confidence score 0-1
        """
        confidence = 0.5  # Base confidence

        # Factor 1: Reasoning trace quality
        trace_factor = self._evaluate_reasoning_trace(reasoning_trace)
        confidence = self._combine_factors(confidence, trace_factor, 0.2)

        # Factor 2: Self-consistency
        if alternative_answers:
            consistency = self._compute_consistency(answer, alternative_answers)
            confidence = self._combine_factors(confidence, consistency, 0.3)

        # Factor 3: Problem-answer alignment
        alignment = self._check_alignment(answer, problem)
        confidence = self._combine_factors(confidence, alignment, 0.2)

        # Factor 4: Domain-specific adjustments
        domain_factor = self._domain_adjustment(problem)
        confidence = self._combine_factors(confidence, domain_factor, 0.1)

        # Apply calibration if available
        confidence = self._apply_calibration(confidence)

        return min(0.99, max(0.01, confidence))

    def _evaluate_reasoning_trace(self, trace: List[str]) -> float:
        """Evaluate quality of reasoning trace"""
        if not trace:
            return 0.3

        score = 0.5

        # More steps generally better (up to a point)
        step_bonus = min(0.2, len(trace) * 0.05)
        score += step_bonus

        # Check for key reasoning indicators
        trace_text = ' '.join(trace).lower()

        if 'therefore' in trace_text or 'because' in trace_text:
            score += 0.1
        if 'given' in trace_text or 'assume' in trace_text:
            score += 0.05
        if 'verify' in trace_text or 'check' in trace_text:
            score += 0.1

        return min(1.0, score)

    def _compute_consistency(self, answer: Any,
                            alternatives: List[Any]) -> float:
        """Compute consistency across multiple answers"""
        if not alternatives:
            return 0.5

        answer_str = str(answer).lower().strip()
        matching = sum(1 for a in alternatives
                      if str(a).lower().strip() == answer_str)

        return (matching + 1) / (len(alternatives) + 1)

    def _check_alignment(self, answer: Any,
                        problem: ProblemCharacteristics) -> float:
        """Check if answer aligns with problem characteristics"""
        score = 0.5

        answer_str = str(answer)

        # Mathematical problem should have numeric answer
        if problem.is_mathematical:
            has_number = any(c.isdigit() for c in answer_str)
            score += 0.2 if has_number else -0.1

        # Yes/no answer type
        if problem.answer_type == 'yes_no':
            is_yesno = answer_str.lower() in ['yes', 'no', 'true', 'false']
            score += 0.3 if is_yesno else -0.2

        # Choice answer
        if problem.answer_type == 'choice':
            is_choice = len(answer_str) <= 3 or answer_str[0].isupper()
            score += 0.2 if is_choice else 0.0

        return min(1.0, max(0.0, score))

    def _domain_adjustment(self, problem: ProblemCharacteristics) -> float:
        """Domain-specific confidence adjustment"""
        # Some domains are inherently harder
        domain_difficulty = {
            'Math': 0.4,
            'Physics': 0.45,
            'Chemistry': 0.5,
            'Biology': 0.55,
            'CS': 0.5,
            'Humanities': 0.55,
            'general': 0.5
        }

        return domain_difficulty.get(problem.domain, 0.5)

    def _combine_factors(self, current: float,
                        factor: float, weight: float) -> float:
        """Combine confidence factors"""
        return current * (1 - weight) + factor * weight

    def _apply_calibration(self, raw_confidence: float) -> float:
        """Apply calibration based on historical data"""
        if not self.calibration_data:
            return raw_confidence

        # Simple Platt scaling would go here
        # For now, return raw
        return raw_confidence

    def update_calibration(self, confidence: float, correct: bool) -> None:
        """Update calibration with new data point"""
        self.calibration_data.append((confidence, correct))

        # Update bins
        bin_name = f"{int(confidence * 10) / 10:.1f}"
        if bin_name not in self.calibration_bins:
            self.calibration_bins[bin_name] = (0, 0)

        correct_count, total = self.calibration_bins[bin_name]
        self.calibration_bins[bin_name] = (correct_count + int(correct), total + 1)


class StrategySelector:
    """
    Selects optimal reasoning strategy for a problem.

    Uses problem characteristics to route to best strategy.
    """

    def __init__(self):
        # Strategy performance history
        self.performance_history: Dict[str, List[Tuple[float, float]]] = {}

        # Strategy weights by problem type
        self.strategy_weights: Dict[str, Dict[ReasoningStrategy, float]] = {
            'mathematical': {
                ReasoningStrategy.DECOMPOSITION: 0.3,
                ReasoningStrategy.FORMAL_LOGIC: 0.3,
                ReasoningStrategy.THEOREM_PROVING: 0.2,
                ReasoningStrategy.SELF_CONSISTENCY: 0.2
            },
            'logical': {
                ReasoningStrategy.FORMAL_LOGIC: 0.4,
                ReasoningStrategy.DECOMPOSITION: 0.3,
                ReasoningStrategy.THEOREM_PROVING: 0.3
            },
            'factual': {
                ReasoningStrategy.RETRIEVAL: 0.5,
                ReasoningStrategy.DIRECT: 0.3,
                ReasoningStrategy.SELF_CONSISTENCY: 0.2
            },
            'causal': {
                ReasoningStrategy.CAUSAL: 0.4,
                ReasoningStrategy.DECOMPOSITION: 0.3,
                ReasoningStrategy.HYPOTHESIS: 0.3
            },
            'general': {
                ReasoningStrategy.SELF_CONSISTENCY: 0.3,
                ReasoningStrategy.DECOMPOSITION: 0.3,
                ReasoningStrategy.RETRIEVAL: 0.2,
                ReasoningStrategy.DIRECT: 0.2
            }
        }

    def select(self, problem: ProblemCharacteristics,
              budget: ResourceBudget) -> List[ReasoningStrategy]:
        """
        Select strategies for a problem.

        Returns list of strategies to try in order.
        """
        # Determine problem type
        if problem.is_mathematical:
            problem_type = 'mathematical'
        elif problem.is_logical:
            problem_type = 'logical'
        elif problem.is_factual:
            problem_type = 'factual'
        elif problem.is_causal:
            problem_type = 'causal'
        else:
            problem_type = 'general'

        # Get weights for this problem type
        weights = self.strategy_weights.get(problem_type,
                                            self.strategy_weights['general'])

        # Adjust weights based on budget
        if budget.remaining_llm_calls() <= 1:
            # Prefer faster strategies
            weights = {
                ReasoningStrategy.DIRECT: weights.get(ReasoningStrategy.DIRECT, 0) + 0.3,
                ReasoningStrategy.RETRIEVAL: weights.get(ReasoningStrategy.RETRIEVAL, 0) + 0.2
            }
        elif budget.remaining_time() < 10:
            # Avoid slow strategies
            for s in [ReasoningStrategy.THEOREM_PROVING, ReasoningStrategy.ENSEMBLE]:
                if s in weights:
                    weights[s] *= 0.5

        # Adjust based on complexity
        if problem.complexity > 0.7:
            # Prefer sophisticated strategies for complex problems
            for s in [ReasoningStrategy.DECOMPOSITION, ReasoningStrategy.HYPOTHESIS]:
                if s in weights:
                    weights[s] *= 1.3

        # Sort by weight
        sorted_strategies = sorted(weights.items(), key=lambda x: -x[1])

        # Return top strategies
        return [s for s, _ in sorted_strategies[:3]]

    def update_performance(self, strategy: ReasoningStrategy,
                          problem_type: str,
                          confidence: float,
                          correct: bool) -> None:
        """Update strategy performance history"""
        key = f"{strategy.value}_{problem_type}"
        if key not in self.performance_history:
            self.performance_history[key] = []

        self.performance_history[key].append((confidence, float(correct)))

        # Update weights based on performance
        if len(self.performance_history[key]) >= 10:
            recent = self.performance_history[key][-10:]
            success_rate = sum(c for _, c in recent) / 10

            if problem_type in self.strategy_weights:
                current_weight = self.strategy_weights[problem_type].get(strategy, 0.2)
                # Adjust weight toward success rate
                new_weight = current_weight * 0.9 + success_rate * 0.1
                self.strategy_weights[problem_type][strategy] = new_weight


class MetaCognitiveController:
    """
    Main meta-cognitive controller.

    Orchestrates:
    - Problem analysis
    - Strategy selection
    - Resource allocation
    - Confidence estimation
    - Result aggregation
    """

    def __init__(self):
        self.confidence_estimator = ConfidenceEstimator()
        self.strategy_selector = StrategySelector()

        # Strategy executors (to be set by V40 system)
        self.executors: Dict[ReasoningStrategy, Callable] = {}

        # Statistics
        self.problems_solved = 0
        self.strategies_used: Dict[str, int] = {}
        self.avg_confidence = 0.0

    def analyze_problem(self, question: str,
                       category: str = "") -> ProblemCharacteristics:
        """Analyze a problem to determine its characteristics"""
        q_lower = question.lower()

        characteristics = ProblemCharacteristics()

        # Mathematical indicators
        math_patterns = [
            r'\d+\s*[\+\-\*\/\=]',
            r'calculate', r'compute', r'solve', r'evaluate',
            r'integral', r'derivative', r'equation', r'formula',
            r'prove', r'theorem'
        ]
        characteristics.is_mathematical = any(
            bool(__import__('re').search(p, q_lower)) for p in math_patterns
        )

        # Logical indicators
        logic_patterns = ['if and only if', 'implies', 'therefore',
                         'valid', 'syllogism', 'tautology']
        characteristics.is_logical = any(p in q_lower for p in logic_patterns)

        # Factual indicators
        factual_patterns = ['what is', 'who is', 'when did', 'where is',
                           'how many', 'name the', 'list']
        characteristics.is_factual = any(p in q_lower for p in factual_patterns)

        # Causal indicators
        causal_patterns = ['why', 'cause', 'because', 'leads to',
                          'effect of', 'result of', 'what would happen']
        characteristics.is_causal = any(p in q_lower for p in causal_patterns)

        # Comparative indicators
        compare_patterns = ['compare', 'contrast', 'difference', 'similar',
                           'versus', 'better', 'worse']
        characteristics.is_comparative = any(p in q_lower for p in compare_patterns)

        # Complexity estimation
        complexity = 0.3
        if len(question) > 200:
            complexity += 0.2
        if characteristics.is_mathematical:
            complexity += 0.2
        if '?' in question:
            parts = question.count('?')
            complexity += 0.1 * (parts - 1)

        characteristics.complexity = min(1.0, complexity)

        # Multiple parts
        characteristics.has_multiple_parts = (
            '(a)' in question or '(i)' in question or
            question.count('?') > 1
        )

        # Domain from category
        characteristics.domain = category if category else "general"

        # Answer type detection
        if 'yes or no' in q_lower:
            characteristics.answer_type = 'yes_no'
        elif '(A)' in question or '(a)' in question.lower():
            characteristics.answer_type = 'choice'
        elif characteristics.is_mathematical:
            characteristics.answer_type = 'number'
        else:
            characteristics.answer_type = 'text'

        return characteristics

    def allocate_budget(self, characteristics: ProblemCharacteristics,
                       base_budget: ResourceBudget = None) -> ResourceBudget:
        """Allocate resource budget based on problem characteristics"""
        if base_budget is None:
            base_budget = ResourceBudget()

        budget = ResourceBudget(
            max_time_seconds=base_budget.max_time_seconds,
            max_llm_calls=base_budget.max_llm_calls,
            max_tool_calls=base_budget.max_tool_calls,
            max_iterations=base_budget.max_iterations
        )

        # Adjust based on complexity
        if characteristics.complexity > 0.7:
            budget.max_time_seconds *= 1.5
            budget.max_llm_calls += 2
            budget.max_iterations += 1

        # Adjust based on type
        if characteristics.is_mathematical:
            budget.max_tool_calls += 5  # More symbolic computations
        if characteristics.is_factual:
            budget.max_llm_calls += 1  # May need retrieval

        return budget

    def solve(self, question: str,
             category: str = "",
             budget: ResourceBudget = None) -> StrategyResult:
        """
        Solve a problem using meta-cognitive control.

        Args:
            question: The problem to solve
            category: Problem category
            budget: Resource budget

        Returns:
            StrategyResult with answer and confidence
        """
        start_time = time.time()

        # 1. Analyze problem
        characteristics = self.analyze_problem(question, category)

        # 2. Allocate budget
        if budget is None:
            budget = self.allocate_budget(characteristics)

        # 3. Select strategies
        strategies = self.strategy_selector.select(characteristics, budget)

        # 4. Execute strategies
        results: List[StrategyResult] = []

        for strategy in strategies:
            # Allocate sub-budget for this strategy
            sub_budget = budget / len(strategies)

            # Execute strategy
            try:
                result = self.strategy_executor.execute(
                    strategy, question, category, sub_budget
                )
                results.append(result)
            except Exception as e:
                # Log error and continue with other strategies
                logger.warning(f"Strategy {strategy.name} failed: {e}")
                results.append(StrategyResult(
                    strategy=strategy.name,
                    success=False,
                    confidence=0.0,
                    answer=None,
                    error=str(e)
                ))

        # 5. Aggregate results
        final_result = self.result_aggregator.aggregate(results)

        return final_result
