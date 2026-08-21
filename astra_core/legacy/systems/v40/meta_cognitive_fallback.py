"""
Faithful fallback for meta_cognitive.py (STAN V40).

meta_cognitive.py is a BASELINED syntax-broken file
(astra_core/tests/known_broken_syntax.txt line 6: IndentationError at
line 544, mid-way through MetaCognitiveController.solve) and must never
be edited. Everything ABOVE the break is complete and is reproduced
here faithfully (ReasoningStrategy, ResourceBudget, StrategyResult,
ProblemCharacteristics, ConfidenceEstimator, StrategySelector, and
MetaCognitiveController's __init__/analyze_problem/allocate_budget).
Only MetaCognitiveController.solve — truncated at "results:
List[StrategyResult] = []" — is completed here, conservatively:

    select strategies via StrategySelector, run the first REGISTERED
    executor (the pattern v40_system._register_executors sets up),
    estimate confidence honestly, and — when no executor is
    registered — return an explicit no-answer result rather than a
    fabricated one.

Imported by v40/__init__.py and v40_system.py only when the real
module fails to load.
"""

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Tuple


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

    (Faithful fallback: everything above the baselined syntax break in
    meta_cognitive.py is reproduced verbatim; solve() below completes
    the truncated method conservatively — it runs the first REGISTERED
    executor chosen by StrategySelector and never fabricates an answer.)
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

    def register_executor(self, strategy: ReasoningStrategy,
                         executor: Callable) -> None:
        """
        Register an executor for a strategy.

        Executors take (question, budget) and return
        (answer, reasoning_trace).
        """
        self.executors[strategy] = executor

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
            bool(re.search(p, q_lower)) for p in math_patterns
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

        Conservative completion of the truncated original: analyze,
        allocate, select via StrategySelector, then run the first
        preferred strategy that has a REGISTERED executor. With no
        registered executors the result is an explicit no-answer —
        never a fabricated one.
        """
        start_time = time.time()

        # 1. Analyze problem
        characteristics = self.analyze_problem(question, category)

        # 2. Allocate budget
        if budget is None:
            budget = self.allocate_budget(characteristics)

        # 3. Select strategies
        strategies = self.strategy_selector.select(characteristics, budget)

        # 4. Execute: first registered executor in preference order,
        #    with any remaining registered strategies as fallback.
        order = [s for s in strategies if s in self.executors]
        order += [s for s in self.executors if s not in order]

        for strategy in order:
            if budget.is_exhausted():
                break

            executor = self.executors[strategy]
            budget.llm_calls_used += 1

            outcome = executor(question, budget)
            if isinstance(outcome, tuple) and len(outcome) == 2:
                answer, trace = outcome
                if trace is None:
                    trace = []
            else:
                answer, trace = outcome, []

            confidence = self.confidence_estimator.estimate(
                answer, trace, characteristics)

            # 5. Record statistics
            self.problems_solved += 1
            key = strategy.value
            self.strategies_used[key] = self.strategies_used.get(key, 0) + 1
            self.avg_confidence = (
                (self.avg_confidence * (self.problems_solved - 1) + confidence)
                / self.problems_solved)

            return StrategyResult(
                strategy=strategy,
                answer=answer,
                confidence=confidence,
                reasoning_trace=list(trace),
                resources_used={
                    'time_seconds': time.time() - start_time,
                    'llm_calls': 1
                }
            )

        # No executor available (or budget exhausted before one ran):
        # report that honestly.
        return StrategyResult(
            strategy=ReasoningStrategy.DIRECT,
            answer=None,
            confidence=0.0,
            reasoning_trace=[
                "No reasoning strategy executor available for this problem"
            ],
            resources_used={'time_seconds': time.time() - start_time}
        )

    def get_stats(self) -> Dict[str, Any]:
        """Controller statistics"""
        return {
            'problems_solved': self.problems_solved,
            'strategies_used': dict(self.strategies_used),
            'avg_confidence': self.avg_confidence,
            'fallback': True
        }
