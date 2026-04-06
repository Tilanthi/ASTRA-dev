"""
ASTRA Live — Tree Search Discovery with Numerical Feedback
Systematic exploration of theoretical space using tree search guided by numerical validation.

Inspired by Brenner et al.'s AI-assisted solution of cosmic string radiation problem:
- Neuro-symbolic system: LLM reasoning + systematic search + numerical feedback
- Discovered 6 different analytical methods for the same problem
- Most elegant: Gegenbauer polynomial expansion to handle singularities

Key innovation: Systematic exploration instead of random trial-and-error,
with automated numerical feedback guiding the search toward valid solutions.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import math


class ApproachType(Enum):
    """Types of analytical approaches."""
    ANALYTIC_EXACT = "analytic_exact"
    PERTURBATIVE = "perturbative"
    NUMERICAL = "numerical"
    SERIES_EXPANSION = "series_expansion"
    VARIATIONAL = "variational"
    INTEGRAL_TRANSFORM = "integral_transform"
    APPROXIMATION = "approximation"


@dataclass
class Approach:
    """A candidate analytical approach."""
    name: str
    description: str
    approach_type: ApproachType
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class TheoreticalResult:
    """Result from executing an analytical approach."""
    approach: Approach
    expression: str  # Mathematical expression (symbolic)
    numerical_prediction: Optional[np.ndarray]  # Numerical evaluation
    computation_time_ms: float
    generality_score: float
    intermediate_steps: List[str] = field(default_factory=list)
    validation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of numerical validation."""
    is_valid: bool
    confidence: float
    error_metrics: Dict[str, float]
    feedback: str  # Human-readable feedback for refinement
    numerical_agreement: float


@dataclass
class TreeNode:
    """Node in the search tree."""
    node_id: int
    approach: Approach
    depth: int
    parent_id: Optional[int] = None
    children: List[int] = field(default_factory=list)
    result: Optional[TheoreticalResult] = None
    validation: Optional[ValidationResult] = None
    score: float = 0.0
    visit_count: int = 0
    is_explored: bool = False
    is_pruned: bool = False


@dataclass
class SearchResults:
    """Results from tree search."""
    best_solution: Optional[TheoreticalResult]
    best_score: float
    all_solutions: List[TheoreticalResult]
    total_nodes_explored: int
    search_depth: int
    convergence_history: List[float]


class NumericalFeedbackLoop:
    """
    Provides automated numerical feedback to guide search.

    Key metrics (inspired by Brenner et al.):
    1. Numerical agreement with reference data (most important)
    2. Mathematical elegance (simpler expressions preferred)
    3. Computational efficiency
    4. Generality (does it apply to related problems?)
    """

    def __init__(self):
        self.validation_history = []

    def validate(self,
                 result: TheoreticalResult,
                 reference_data: Optional[np.ndarray] = None,
                 tolerance: float = 0.05) -> ValidationResult:
        """
        Returns validation result with score in [0, 1].
        """
        scores = {}

        # 1. Numerical agreement (50% weight - most important)
        if reference_data is not None and result.numerical_prediction is not None:
            numerical_score = self._compute_numerical_agreement(
                result.numerical_prediction,
                reference_data
            )
            scores['numerical_agreement'] = numerical_score
        else:
            scores['numerical_agreement'] = 0.0

        # 2. Mathematical elegance (20% weight)
        scores['elegance'] = self._elegance_score(result.expression)

        # 3. Computational efficiency (15% weight)
        scores['efficiency'] = min(1.0, 1000.0 / (result.computation_time_ms + 1.0))

        # 4. Generality (15% weight)
        scores['generality'] = result.generality_score

        # Overall score (weighted combination)
        weights = {
            'numerical_agreement': 0.50,
            'elegance': 0.20,
            'efficiency': 0.15,
            'generality': 0.15
        }

        overall_score = sum(scores[k] * weights[k] for k in scores)

        # Generate feedback
        if scores['numerical_agreement'] < 0.7:
            feedback = "Numerical agreement insufficient. Consider: "
            feedback += self._suggest_improvement(scores, result)
        elif scores['elegance'] < 0.3:
            feedback = "Expression is complex. Consider simplification or alternative formulation."
        else:
            feedback = "Approach shows promise. Refine parameters or extend to higher order."

        self.validation_history.append({
            'scores': scores,
            'overall': overall_score,
            'feedback': feedback
        })

        return ValidationResult(
            is_valid=overall_score > 0.6,
            confidence=overall_score,
            error_metrics=scores,
            feedback=feedback,
            numerical_agreement=scores.get('numerical_agreement', 0.0)
        )

    def _compute_numerical_agreement(self,
                                      prediction: np.ndarray,
                                      reference: np.ndarray) -> float:
        """Compute agreement score between prediction and reference."""
        # Ensure same length
        min_len = min(len(prediction), len(reference))
        pred = prediction[:min_len]
        ref = reference[:min_len]

        # Handle NaN/Inf
        valid = np.isfinite(pred) & np.isfinite(ref)
        if np.sum(valid) < 2:
            return 0.0

        pred = pred[valid]
        ref = ref[valid]

        # Correlation coefficient
        correlation = np.corrcoef(pred, ref)[0, 1]

        # Normalized RMS error
        rms_error = np.sqrt(np.mean((pred - ref)**2))
        ref_std = np.std(ref)

        if ref_std > 1e-10:
            normalized_rms = rms_error / ref_std
        else:
            normalized_rms = rms_error

        # Combine metrics
        # Correlation: 1.0 is perfect, 0.0 is no relationship
        # Normalized RMS: 0.0 is perfect, >1.0 is poor
        agreement = 0.5 * (1.0 + correlation) + 0.5 * np.exp(-normalized_rms)

        return np.clip(agreement, 0.0, 1.0)

    def _elegance_score(self, expression: str) -> float:
        """
        Score mathematical elegance (simpler is better).

        Heuristics:
        - Fewer operations = more elegant
        - Standard functions preferred over special functions
        - Compact expressions preferred
        """
        if not expression:
            return 0.0

        # Count operations
        n_ops = (expression.count('+') + expression.count('-') +
                expression.count('*') + expression.count('/') +
                expression.count('^'))

        # Count special functions
        special_funcs = ['exp', 'log', 'sin', 'cos', 'tan', 'sqrt', 'gamma', 'zeta']
        n_special = sum(expression.count(func) for func in special_funcs)

        # Length penalty
        length_penalty = min(1.0, len(expression) / 500.0)

        # Elegance decreases with complexity
        elegance = 1.0 / (1.0 + 0.1 * n_ops + 0.2 * n_special + length_penalty)

        return elegance

    def _suggest_improvement(self, scores: Dict, result: TheoreticalResult) -> str:
        """Suggest specific improvements based on validation scores."""
        suggestions = []

        if scores.get('numerical_agreement', 0) < 0.5:
            suggestions.append("different expansion basis")

        if scores.get('elegance', 0) < 0.3:
            suggestions.append("simpler analytical form")

        if scores.get('efficiency', 0) < 0.2:
            suggestions.append("more efficient numerical method")

        if not suggestions:
            suggestions.append("higher-order approximation")

        return ", ".join(suggestions)


class TreeSearchDiscoveryEngine:
    """
    Systematic exploration of theoretical space using tree search.

    Inspired by Brenner et al.'s approach to discovering 6 different
    analytical methods for cosmic string gravitational radiation.
    """

    def __init__(self, max_depth: int = 5, max_iterations: int = 1000):
        self.max_depth = max_depth
        self.max_iterations = max_iterations
        self.numerical_feedback = NumericalFeedbackLoop()
        self.nodes: Dict[int, TreeNode] = {}
        self.root_id: Optional[int] = None
        self.next_node_id = 0

    def search_theoretical_space(self,
                                  problem: Dict[str, Any],
                                  approach_generator: Optional[Callable] = None) -> SearchResults:
        """
        Explore space of possible theoretical approaches using tree search.

        Args:
            problem: Dictionary describing the theoretical problem
                - 'description': Problem description
                - 'data': Numerical reference data (if available)
                - 'variables': Problem variables
                - 'constraints': Mathematical constraints
            approach_generator: Function that generates candidate approaches

        Returns:
            SearchResults containing best solution and all discovered methods
        """
        # Initialize root node
        root_approach = Approach(
            name="root",
            description="Initial problem statement",
            approach_type=ApproachType.ANALYTIC_EXACT
        )

        self.root_id = self._create_node(root_approach, depth=0)
        self.nodes[self.root_id].is_explored = True

        best_solution = None
        best_score = -np.inf
        all_solutions = []
        convergence_history = []

        for iteration in range(self.max_iterations):
            # Select promising node using UCB policy
            node_id = self._select_promising_node()

            if node_id is None:
                break  # No more nodes to explore

            node = self.nodes[node_id]

            # Generate candidate approaches
            if approach_generator is None:
                candidates = self._default_approach_generator(node, problem)
            else:
                candidates = approach_generator(node, problem)

            # Explore each candidate
            for candidate in candidates:
                if node.depth >= self.max_depth:
                    continue

                # Create child node
                child_id = self._create_node(candidate, depth=node.depth + 1)
                node.children.append(child_id)
                self.nodes[child_id].parent_id = node_id

                # Execute approach (symbolic)
                result = self._execute_approach(candidate, problem)

                if result is None:
                    continue

                self.nodes[child_id].result = result

                # Numerical validation
                validation = self.numerical_feedback.validate(
                    result,
                    problem.get('data')
                )

                self.nodes[child_id].validation = validation
                self.nodes[child_id].score = validation.confidence
                self.nodes[child_id].is_explored = True

                # Update best
                if validation.confidence > best_score:
                    best_solution = result
                    best_score = validation.confidence

                if validation.is_valid:
                    all_solutions.append(result)

                convergence_history.append(validation.confidence)

            # Check convergence
            if len(convergence_history) > 50:
                recent_std = np.std(convergence_history[-50:])
                if recent_std < 0.01:
                    break

        return SearchResults(
            best_solution=best_solution,
            best_score=best_score,
            all_solutions=all_solutions,
            total_nodes_explored=len(self.nodes),
            search_depth=self._get_max_depth(),
            convergence_history=convergence_history
        )

    def _create_node(self, approach: Approach, depth: int) -> int:
        """Create a new tree node."""
        node_id = self.next_node_id
        self.next_node_id += 1

        self.nodes[node_id] = TreeNode(
            node_id=node_id,
            approach=approach,
            depth=depth
        )

        return node_id

    def _select_promising_node(self) -> Optional[int]:
        """
        Select promising node using UCB (Upper Confidence Bound) policy.

        Balances exploration (nodes visited less) and exploitation (high-scoring nodes).
        """
        # Find unexplored nodes first
        for node_id, node in self.nodes.items():
            if not node.is_explored and not node.is_pruned:
                return node_id

        # If all explored, use UCB on leaf nodes
        leaf_nodes = [n for n in self.nodes.values()
                     if not n.children and not n.is_pruned]

        if not leaf_nodes:
            return None

        # UCB formula: score + c * sqrt(log(parent_visits) / visits)
        c = 1.41  # Exploration constant

        best_node = None
        best_ucb = -np.inf

        for node in leaf_nodes:
            if node.visit_count == 0:
                ucb = np.inf
            else:
                parent_visits = self.nodes[node.parent_id].visit_count if node.parent_id else 1
                ucb = node.score + c * np.sqrt(np.log(parent_visits) / node.visit_count)

            if ucb > best_ucb:
                best_ucb = ucb
                best_node = node

        return best_node.node_id if best_node else None

    def _default_approach_generator(self,
                                     node: TreeNode,
                                     problem: Dict) -> List[Approach]:
        """
        Generate candidate approaches at current search node.

        This implements domain knowledge about mathematical approaches.
        Inspired by the 6 methods discovered in cosmic string problem.
        """
        approaches = []
        depth = node.depth

        if depth == 0:
            # Root-level: major mathematical frameworks
            approaches = [
                Approach("analytic_exact", "Attempt exact analytical solution",
                        ApproachType.ANALYTIC_EXACT),
                Approach("perturbative", "Use perturbation theory",
                        ApproachType.PERTURBATIVE),
                Approach("series_expansion", "Expand in series",
                        ApproachType.SERIES_EXPANSION),
                Approach("integral_transform", "Use integral transforms",
                        ApproachType.INTEGRAL_TRANSFORM),
                Approach("variational", "Variational approach",
                        ApproachType.VARIATIONAL),
            ]

        elif depth == 1:
            # Refine based on parent approach
            parent_name = node.approach.name

            if parent_name == "series_expansion":
                # Different expansion bases (inspired by Gegenbauer discovery)
                approaches = [
                    Approach("power_series", "Taylor/power series expansion",
                            ApproachType.SERIES_EXPANSION),
                    Approach("fourier_series", "Fourier series expansion",
                            ApproachType.SERIES_EXPANSION),
                    Approach("gegenbauer_expansion", "Gegenbauer polynomial expansion",
                            ApproachType.SERIES_EXPANSION),
                    Approach("legendre_expansion", "Legendre polynomial expansion",
                            ApproachType.SERIES_EXPANSION),
                ]

            elif parent_name == "integral_transform":
                approaches = [
                    Approach("fourier_transform", "Fourier transform method",
                            ApproachType.INTEGRAL_TRANSFORM),
                    Approach("laplace_transform", "Laplace transform method",
                            ApproachType.INTEGRAL_TRANSFORM),
                    Approach("mellin_transform", "Mellin transform method",
                            ApproachType.INTEGRAL_TRANSFORM),
                ]

            elif parent_name == "perturbative":
                approaches = [
                    Approach("weak_coupling", "Weak coupling expansion",
                            ApproachType.PERTURBATIVE),
                    Approach("strong_coupling", "Strong coupling expansion",
                            ApproachType.PERTURBATIVE),
                    Approach("semiclassical", "Semiclassical approximation",
                            ApproachType.PERTURBATIVE),
                ]

        elif depth == 2:
            # Further refinement: numerical methods
            approaches = [
                Approach("numerical_integration", "Direct numerical integration",
                        ApproachType.NUMERICAL),
                Approach("monte_carlo", "Monte Carlo sampling",
                        ApproachType.NUMERICAL),
            ]

        return approaches

    def _execute_approach(self,
                          approach: Approach,
                          problem: Dict) -> Optional[TheoreticalResult]:
        """
        Execute an analytical approach.

        In a full implementation, this would:
        1. Use symbolic computation (SymPy) to derive expressions
        2. Generate numerical predictions
        3. Time the computation

        For now, this is a placeholder that simulates execution.
        """
        import time
        import random

        # Simulate computation time
        start_time = time.time()

        # Placeholder: generate synthetic result
        # In real implementation, this would use symbolic computation
        if "data" in problem and problem["data"] is not None:
            reference_data = problem["data"]

            # Simulate prediction with varying quality
            noise_level = 0.1 + 0.1 * approach.approach_type.value.count('_')
            prediction = reference_data * (1.0 + noise_level * np.random.randn(len(reference_data)) * 0.1)
            prediction = np.clip(prediction, np.min(reference_data), np.max(reference_data))
        else:
            prediction = None

        computation_time = (time.time() - start_time) * 1000  # ms

        # Generate expression (placeholder)
        expression = f"{approach.name}(x) = f(x; {approach.approach_type.value})"

        result = TheoreticalResult(
            approach=approach,
            expression=expression,
            numerical_prediction=prediction,
            computation_time_ms=computation_time,
            generality_score=0.7 + 0.2 * random.random(),
            intermediate_steps=[f"Applied {approach.name}"],
            validation_metadata={'approach_type': approach.approach_type.value}
        )

        return result

    def _get_max_depth(self) -> int:
        """Get maximum depth of explored tree."""
        return max((n.depth for n in self.nodes.values()), default=0)

    def get_all_solution_methods(self) -> List[str]:
        """
        Get names of all distinct solution methods discovered.

        This is how Brenner et al. identified 6 different methods.
        """
        methods = set()

        for node in self.nodes.values():
            if node.result is not None and node.validation is not None:
                if node.validation.is_valid:
                    methods.add(node.approach.name)

        return list(methods)


class MultiMethodDiscoveryEngine:
    """
    Discovers multiple independent methods for solving the same problem.

    Key insight from Brenner et al.: If 6 different approaches all lead to
    the same result, confidence in that result is much higher.
    """

    def __init__(self):
        self.tree_search = TreeSearchDiscoveryEngine()

    def discover_all_methods(self,
                             problem: Dict[str, Any],
                             num_runs: int = 3) -> Dict[str, Any]:
        """
        Run multiple tree searches to find all viable methods.
        """
        all_methods = []
        all_results = []

        for run in range(num_runs):
            # Run tree search with different random seeds
            search_results = self.tree_search.search_theoretical_space(problem)

            if search_results.best_solution:
                all_methods.extend(self.tree_search.get_all_solution_methods())
                all_results.extend(search_results.all_solutions)

        # Remove duplicates and group by method
        unique_methods = list(set(all_methods))

        method_results = {}
        for method in unique_methods:
            matching = [r for r in all_results if r.approach.name == method]
            if matching:
                # Get best result for this method
                # Score based on generality for TheoreticalResult
                best = max(matching, key=lambda r: r.generality_score)
                method_results[method] = best

        # Check convergence: do different methods agree?
        convergence_report = self._check_method_convergence(method_results, problem)

        return {
            'methods_discovered': unique_methods,
            'method_results': method_results,
            'n_methods': len(unique_methods),
            'convergence': convergence_report
        }

    def _check_method_convergence(self,
                                   method_results: Dict,
                                   problem: Dict) -> Dict[str, Any]:
        """
        Check if different methods converge to the same answer.
        """
        predictions = []

        for method, result in method_results.items():
            if result.numerical_prediction is not None:
                predictions.append(result.numerical_prediction)

        if len(predictions) < 2:
            return {'status': 'insufficient_methods'}

        # Pairwise correlations
        correlations = []
        for i, p1 in enumerate(predictions):
            for j, p2 in enumerate(predictions):
                if i < j:
                    # Ensure same length
                    min_len = min(len(p1), len(p2))
                    corr = np.corrcoef(p1[:min_len], p2[:min_len])[0, 1]
                    if np.isfinite(corr):
                        correlations.append(corr)

        if not correlations:
            return {'status': 'no_valid_correlations'}

        mean_correlation = np.mean(correlations)
        std_correlation = np.std(correlations)

        # Convergence threshold: high mean agreement, low std
        is_converged = mean_correlation > 0.90 and std_correlation < 0.10

        return {
            'status': 'converged' if is_converged else 'not_converged',
            'mean_agreement': mean_correlation,
            'agreement_std': std_correlation,
            'pairwise_correlations': correlations,
            'interpretation': (
                f"Methods {'CONVERGE' if is_converged else 'DIVERGE'}: "
                f"mean agreement = {mean_correlation:.3f}"
            )
        }


# Demonstration
if __name__ == "__main__":
    print("Tree Search Discovery with Numerical Feedback")
    print("=" * 80)
    print("\nInspired by Brenner et al.'s AI-assisted cosmic string solution:")
    print("  • Neuro-symbolic: LLM reasoning + systematic search + numerical feedback")
    print("  • Discovered 6 different analytical methods for the same problem")
    print("  • Most elegant: Gegenbauer polynomial expansion")
    print("\nKey capabilities:")
    print("  1. Systematic tree search through theoretical space")
    print("  2. Automated numerical validation guiding exploration")
    print("  3. Multi-method discovery for cross-validation")
    print("  4. Convergence checking: do different methods agree?")
    print("\nUsage:")
    print("  engine = TreeSearchDiscoveryEngine()")
    print("  results = engine.search_theoretical_space(problem)")
    print("  methods = engine.get_all_solution_methods()")
