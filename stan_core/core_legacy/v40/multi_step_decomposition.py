"""
Multi-Step Decomposition Engine for STAN V40

Breaks complex problems into manageable sub-problems:
- Hierarchical decomposition with dependency tracking
- Independent sub-problem solving
- Answer composition with consistency checking

Target: +12-18% on Math, Physics, Engineering questions

Date: 2025-12-11
Version: 40.0
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from enum import Enum
from abc import ABC, abstractmethod
import hashlib


class DecompositionStrategy(Enum):
    """Strategies for problem decomposition"""
    SEQUENTIAL = "sequential"      # Steps depend on previous
    PARALLEL = "parallel"          # Independent sub-problems
    HIERARCHICAL = "hierarchical"  # Tree structure
    RECURSIVE = "recursive"        # Self-similar sub-problems
    CONDITIONAL = "conditional"    # Branch based on conditions
    HYBRID = "hybrid"              # Mix of strategies


class SubProblemStatus(Enum):
    """Status of sub-problem solving"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SOLVED = "solved"
    FAILED = "failed"
    BLOCKED = "blocked"  # Waiting on dependencies


@dataclass
class SubProblem:
    """A decomposed sub-problem"""
    id: str
    description: str
    parent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    # Problem characteristics
    problem_type: str = "unknown"  # math, logic, retrieval, computation
    estimated_difficulty: float = 0.5
    estimated_steps: int = 1

    # Solution state
    status: SubProblemStatus = SubProblemStatus.PENDING
    solution: Optional[str] = None
    confidence: float = 0.0
    reasoning_trace: List[str] = field(default_factory=list)

    # Metadata
    context: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)

    def is_ready(self, solved_ids: Set[str]) -> bool:
        """Check if all dependencies are satisfied"""
        return all(dep in solved_ids for dep in self.dependencies)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'description': self.description,
            'parent_id': self.parent_id,
            'dependencies': self.dependencies,
            'problem_type': self.problem_type,
            'status': self.status.value,
            'solution': self.solution,
            'confidence': self.confidence
        }


@dataclass
class ProblemDecomposition:
    """Complete decomposition of a problem"""
    original_problem: str
    strategy: DecompositionStrategy
    sub_problems: List[SubProblem]

    # Composition info
    composition_template: str = ""
    final_answer: Optional[str] = None
    overall_confidence: float = 0.0

    # Tracking
    total_steps: int = 0
    solved_count: int = 0

    def get_ready_subproblems(self) -> List[SubProblem]:
        """Get sub-problems ready to solve"""
        solved_ids = {sp.id for sp in self.sub_problems
                     if sp.status == SubProblemStatus.SOLVED}
        return [sp for sp in self.sub_problems
                if sp.status == SubProblemStatus.PENDING and sp.is_ready(solved_ids)]

    def get_solution_map(self) -> Dict[str, str]:
        """Get mapping of sub-problem IDs to solutions"""
        return {sp.id: sp.solution for sp in self.sub_problems
                if sp.solution is not None}

    def to_dict(self) -> Dict:
        return {
            'original_problem': self.original_problem,
            'strategy': self.strategy.value,
            'sub_problems': [sp.to_dict() for sp in self.sub_problems],
            'final_answer': self.final_answer,
            'overall_confidence': self.overall_confidence,
            'solved_count': self.solved_count,
            'total_steps': self.total_steps
        }


class DecompositionPattern(ABC):
    """Base class for decomposition patterns"""

    @abstractmethod
    def matches(self, problem: str, category: str) -> bool:
        """Check if this pattern applies"""
        pass

    @abstractmethod
    def decompose(self, problem: str, context: Dict) -> List[SubProblem]:
        """Decompose the problem"""
        pass


class MathProofDecomposition(DecompositionPattern):
    """Decomposition for mathematical proofs"""

    PROOF_KEYWORDS = ['prove', 'show that', 'demonstrate', 'verify', 'establish']

    def matches(self, problem: str, category: str) -> bool:
        p_lower = problem.lower()
        return category == 'Math' and any(kw in p_lower for kw in self.PROOF_KEYWORDS)

    def decompose(self, problem: str, context: Dict) -> List[SubProblem]:
        sub_problems = []

        # Step 1: Identify what needs to be proved
        sub_problems.append(SubProblem(
            id="identify_goal",
            description="Identify the statement to be proved and its logical structure",
            problem_type="analysis",
            estimated_difficulty=0.3,
            estimated_steps=1
        ))

        # Step 2: List known facts and assumptions
        sub_problems.append(SubProblem(
            id="list_assumptions",
            description="List all given information, definitions, and applicable theorems",
            dependencies=["identify_goal"],
            problem_type="retrieval",
            estimated_difficulty=0.4,
            estimated_steps=1
        ))

        # Step 3: Determine proof strategy
        sub_problems.append(SubProblem(
            id="choose_strategy",
            description="Select proof strategy: direct, contradiction, induction, or construction",
            dependencies=["identify_goal", "list_assumptions"],
            problem_type="logic",
            estimated_difficulty=0.6,
            estimated_steps=1
        ))

        # Step 4: Execute proof steps
        sub_problems.append(SubProblem(
            id="execute_proof",
            description="Execute the proof step by step, justifying each step",
            dependencies=["choose_strategy"],
            problem_type="math",
            estimated_difficulty=0.8,
            estimated_steps=5
        ))

        # Step 5: Verify conclusion
        sub_problems.append(SubProblem(
            id="verify_conclusion",
            description="Verify that the proof establishes the required statement",
            dependencies=["execute_proof"],
            problem_type="verification",
            estimated_difficulty=0.4,
            estimated_steps=1
        ))

        return sub_problems


class CalculationDecomposition(DecompositionPattern):
    """Decomposition for multi-step calculations"""

    CALC_KEYWORDS = ['calculate', 'compute', 'find', 'determine', 'evaluate', 'solve']

    def matches(self, problem: str, category: str) -> bool:
        p_lower = problem.lower()
        return category in ['Math', 'Physics', 'Chemistry', 'Engineering'] and \
               any(kw in p_lower for kw in self.CALC_KEYWORDS)

    def decompose(self, problem: str, context: Dict) -> List[SubProblem]:
        sub_problems = []

        # Step 1: Identify quantities
        sub_problems.append(SubProblem(
            id="identify_quantities",
            description="Identify all given quantities, unknowns, and their units",
            problem_type="analysis",
            estimated_difficulty=0.3,
            estimated_steps=1
        ))

        # Step 2: Identify relevant formulas
        sub_problems.append(SubProblem(
            id="identify_formulas",
            description="Identify applicable formulas, laws, or equations",
            dependencies=["identify_quantities"],
            problem_type="retrieval",
            estimated_difficulty=0.5,
            estimated_steps=1
        ))

        # Step 3: Set up equations
        sub_problems.append(SubProblem(
            id="setup_equations",
            description="Set up the equations needed to solve for unknowns",
            dependencies=["identify_quantities", "identify_formulas"],
            problem_type="math",
            estimated_difficulty=0.6,
            estimated_steps=2
        ))

        # Step 4: Solve equations
        sub_problems.append(SubProblem(
            id="solve_equations",
            description="Solve the equations step by step",
            dependencies=["setup_equations"],
            problem_type="computation",
            estimated_difficulty=0.7,
            estimated_steps=3
        ))

        # Step 5: Check units and reasonableness
        sub_problems.append(SubProblem(
            id="verify_result",
            description="Verify units are correct and answer is reasonable",
            dependencies=["solve_equations"],
            problem_type="verification",
            estimated_difficulty=0.3,
            estimated_steps=1
        ))

        return sub_problems


class CausalReasoningDecomposition(DecompositionPattern):
    """Decomposition for causal/explanatory questions"""

    CAUSAL_KEYWORDS = ['why', 'cause', 'explain', 'reason', 'mechanism', 'how does']

    def matches(self, problem: str, category: str) -> bool:
        p_lower = problem.lower()
        return any(kw in p_lower for kw in self.CAUSAL_KEYWORDS)

    def decompose(self, problem: str, context: Dict) -> List[SubProblem]:
        sub_problems = []

        # Step 1: Identify phenomenon
        sub_problems.append(SubProblem(
            id="identify_phenomenon",
            description="Identify the phenomenon or effect to be explained",
            problem_type="analysis",
            estimated_difficulty=0.3,
            estimated_steps=1
        ))

        # Step 2: Identify causal factors
        sub_problems.append(SubProblem(
            id="identify_causes",
            description="Identify potential causal factors or mechanisms",
            dependencies=["identify_phenomenon"],
            problem_type="retrieval",
            estimated_difficulty=0.5,
            estimated_steps=2
        ))

        # Step 3: Trace causal chain
        sub_problems.append(SubProblem(
            id="trace_causation",
            description="Trace the causal chain from causes to effect",
            dependencies=["identify_causes"],
            problem_type="logic",
            estimated_difficulty=0.7,
            estimated_steps=3
        ))

        # Step 4: Validate explanation
        sub_problems.append(SubProblem(
            id="validate_explanation",
            description="Check if explanation is consistent with known facts",
            dependencies=["trace_causation"],
            problem_type="verification",
            estimated_difficulty=0.5,
            estimated_steps=1
        ))

        return sub_problems


class ComparisonDecomposition(DecompositionPattern):
    """Decomposition for comparison questions"""

    COMPARE_KEYWORDS = ['compare', 'contrast', 'difference', 'similar', 'versus', 'vs']

    def matches(self, problem: str, category: str) -> bool:
        p_lower = problem.lower()
        return any(kw in p_lower for kw in self.COMPARE_KEYWORDS)

    def decompose(self, problem: str, context: Dict) -> List[SubProblem]:
        sub_problems = []

        # Step 1: Identify items to compare
        sub_problems.append(SubProblem(
            id="identify_items",
            description="Identify the items, concepts, or entities being compared",
            problem_type="analysis",
            estimated_difficulty=0.3,
            estimated_steps=1
        ))

        # Step 2: Analyze first item
        sub_problems.append(SubProblem(
            id="analyze_item_1",
            description="Analyze characteristics of the first item",
            dependencies=["identify_items"],
            problem_type="retrieval",
            estimated_difficulty=0.5,
            estimated_steps=2
        ))

        # Step 3: Analyze second item
        sub_problems.append(SubProblem(
            id="analyze_item_2",
            description="Analyze characteristics of the second item",
            dependencies=["identify_items"],
            problem_type="retrieval",
            estimated_difficulty=0.5,
            estimated_steps=2
        ))

        # Step 4: Identify similarities and differences
        sub_problems.append(SubProblem(
            id="compare_items",
            description="Systematically compare and contrast the items",
            dependencies=["analyze_item_1", "analyze_item_2"],
            problem_type="logic",
            estimated_difficulty=0.6,
            estimated_steps=2
        ))

        # Step 5: Synthesize conclusion
        sub_problems.append(SubProblem(
            id="synthesize",
            description="Synthesize findings into a coherent comparison",
            dependencies=["compare_items"],
            problem_type="synthesis",
            estimated_difficulty=0.5,
            estimated_steps=1
        ))

        return sub_problems


class MultiStepDecomposer:
    """
    Main decomposition engine.

    Analyzes problems and breaks them into solvable sub-problems
    with dependency tracking.
    """

    def __init__(self):
        # Register decomposition patterns
        self.patterns: List[DecompositionPattern] = [
            MathProofDecomposition(),
            CalculationDecomposition(),
            CausalReasoningDecomposition(),
            ComparisonDecomposition(),
        ]

        # Statistics
        self.decompositions_performed = 0
        self.avg_sub_problems = 0.0

    def analyze_complexity(self, problem: str) -> Dict[str, Any]:
        """Analyze problem complexity"""
        # Count potential steps based on conjunctions, clauses
        sentences = problem.split('.')
        clauses = sum(len(s.split(',')) for s in sentences)

        # Check for mathematical content
        has_math = bool(re.search(r'[\d\+\-\*\/\=\^\(\)]', problem))
        has_equations = bool(re.search(r'\=.*\=|[a-z]\s*\=\s*[\d]', problem, re.I))

        # Check for multi-part questions
        parts = re.findall(r'\([a-z]\)|\b[a-z]\)', problem.lower())

        # Estimate complexity
        complexity = 0.3
        if len(sentences) > 2:
            complexity += 0.1
        if clauses > 4:
            complexity += 0.1
        if has_math:
            complexity += 0.2
        if has_equations:
            complexity += 0.1
        if len(parts) > 0:
            complexity += 0.1 * len(parts)

        return {
            'sentences': len(sentences),
            'clauses': clauses,
            'has_math': has_math,
            'has_equations': has_equations,
            'multi_part': len(parts),
            'estimated_complexity': min(1.0, complexity),
            'needs_decomposition': complexity > 0.5 or len(parts) > 1
        }

    def select_strategy(self, problem: str, category: str,
                       context: Dict = None) -> DecompositionStrategy:
        """Select appropriate decomposition strategy"""
        p_lower = problem.lower()

        # Check for explicit multi-part
        if re.search(r'\([a-z]\)|\b[ivx]+\)', p_lower):
            return DecompositionStrategy.SEQUENTIAL

        # Check for proof problems
        if 'prove' in p_lower or 'show that' in p_lower:
            return DecompositionStrategy.HIERARCHICAL

        # Check for recursive structure
        if 'recursively' in p_lower or 'induction' in p_lower:
            return DecompositionStrategy.RECURSIVE

        # Check for conditional branches
        if 'if' in p_lower and 'else' in p_lower:
            return DecompositionStrategy.CONDITIONAL

        # Check for parallel sub-problems
        compare_patterns = ['compare', 'both', 'each', 'respectively']
        if any(p in p_lower for p in compare_patterns):
            return DecompositionStrategy.PARALLEL

        # Default to sequential for most problems
        return DecompositionStrategy.SEQUENTIAL

    def decompose(self, problem: str, category: str = "unknown",
                 context: Dict = None) -> ProblemDecomposition:
        """
        Decompose a problem into sub-problems.

        Args:
            problem: The problem statement
            category: Problem category (Math, Physics, etc.)
            context: Additional context

        Returns:
            ProblemDecomposition with sub-problems
        """
        context = context or {}

        # Analyze complexity
        complexity = self.analyze_complexity(problem)

        # Select strategy
        strategy = self.select_strategy(problem, category, context)

        # Find matching pattern
        sub_problems = []
        for pattern in self.patterns:
            if pattern.matches(problem, category):
                sub_problems = pattern.decompose(problem, context)
                break

        # If no pattern matches, create generic decomposition
        if not sub_problems:
            sub_problems = self._generic_decomposition(problem, category, context)

        # Create decomposition object
        decomposition = ProblemDecomposition(
            original_problem=problem,
            strategy=strategy,
            sub_problems=sub_problems,
            total_steps=sum(sp.estimated_steps for sp in sub_problems)
        )

        # Generate composition template
        decomposition.composition_template = self._generate_composition_template(
            sub_problems, strategy
        )

        # Update statistics
        self.decompositions_performed += 1
        n = self.decompositions_performed
        self.avg_sub_problems = (self.avg_sub_problems * (n-1) + len(sub_problems)) / n

        return decomposition

    def _generic_decomposition(self, problem: str, category: str,
                               context: Dict) -> List[SubProblem]:
        """Generic decomposition for unmatched problems"""
        sub_problems = []

        # Step 1: Understand the question
        sub_problems.append(SubProblem(
            id="understand",
            description="Understand what the question is asking",
            problem_type="analysis",
            estimated_difficulty=0.3,
            estimated_steps=1
        ))

        # Step 2: Gather relevant knowledge
        sub_problems.append(SubProblem(
            id="gather_knowledge",
            description="Recall or retrieve relevant knowledge and facts",
            dependencies=["understand"],
            problem_type="retrieval",
            estimated_difficulty=0.5,
            estimated_steps=2
        ))

        # Step 3: Apply reasoning
        sub_problems.append(SubProblem(
            id="reason",
            description="Apply reasoning to derive the answer",
            dependencies=["gather_knowledge"],
            problem_type="logic",
            estimated_difficulty=0.7,
            estimated_steps=3
        ))

        # Step 4: Formulate answer
        sub_problems.append(SubProblem(
            id="formulate",
            description="Formulate and state the final answer",
            dependencies=["reason"],
            problem_type="synthesis",
            estimated_difficulty=0.4,
            estimated_steps=1
        ))

        return sub_problems

    def _generate_composition_template(self, sub_problems: List[SubProblem],
                                       strategy: DecompositionStrategy) -> str:
        """Generate template for composing final answer"""
        if strategy == DecompositionStrategy.SEQUENTIAL:
            return "Combine solutions in order: " + " -> ".join(
                f"[{sp.id}]" for sp in sub_problems
            )
        elif strategy == DecompositionStrategy.PARALLEL:
            return "Merge parallel solutions: " + " + ".join(
                f"[{sp.id}]" for sp in sub_problems if not sp.dependencies
            )
        elif strategy == DecompositionStrategy.HIERARCHICAL:
            # Find leaf nodes
            all_ids = {sp.id for sp in sub_problems}
            parent_ids = {dep for sp in sub_problems for dep in sp.dependencies}
            leaves = all_ids - parent_ids
            return "Compose from leaf solutions: " + ", ".join(f"[{lid}]" for lid in leaves)
        else:
            return "Compose all solutions: " + ", ".join(f"[{sp.id}]" for sp in sub_problems)


class CompositionEngine:
    """
    Composes solutions from solved sub-problems.

    Handles dependency resolution, consistency checking,
    and final answer synthesis.
    """

    def __init__(self):
        self.compositions_performed = 0

    def compose(self, decomposition: ProblemDecomposition,
               solver: Callable[[SubProblem], Tuple[str, float]] = None) -> str:
        """
        Compose final answer from sub-problem solutions.

        Args:
            decomposition: The problem decomposition
            solver: Function to solve individual sub-problems

        Returns:
            Composed final answer
        """
        # Solve sub-problems in dependency order
        if solver:
            self._solve_in_order(decomposition, solver)

        # Get solution map
        solutions = decomposition.get_solution_map()

        # Check if all sub-problems solved
        unsolved = [sp for sp in decomposition.sub_problems
                   if sp.status != SubProblemStatus.SOLVED]
        if unsolved:
            return f"[Incomplete: {len(unsolved)} sub-problems unsolved]"

        # Compose based on strategy
        if decomposition.strategy == DecompositionStrategy.SEQUENTIAL:
            final = self._compose_sequential(decomposition, solutions)
        elif decomposition.strategy == DecompositionStrategy.PARALLEL:
            final = self._compose_parallel(decomposition, solutions)
        elif decomposition.strategy == DecompositionStrategy.HIERARCHICAL:
            final = self._compose_hierarchical(decomposition, solutions)
        else:
            final = self._compose_generic(decomposition, solutions)

        # Calculate overall confidence
        confidences = [sp.confidence for sp in decomposition.sub_problems]
        decomposition.overall_confidence = min(confidences) if confidences else 0.0

        decomposition.final_answer = final
        decomposition.solved_count = len(solutions)

        self.compositions_performed += 1

        return final

    def _solve_in_order(self, decomposition: ProblemDecomposition,
                       solver: Callable) -> None:
        """Solve sub-problems respecting dependencies"""
        solved_ids: Set[str] = set()
        max_iterations = len(decomposition.sub_problems) * 2
        iterations = 0

        while len(solved_ids) < len(decomposition.sub_problems):
            iterations += 1
            if iterations > max_iterations:
                break

            # Get ready sub-problems
            ready = decomposition.get_ready_subproblems()
            if not ready:
                break
            
            # Process ready sub-problems
            for sub_problem in ready:
                if sub_problem.id not in solved_ids:
                    # Solve sub-problem
                    solution = self._solve_sub_problem(sub_problem)
                    if solution:
                        decomposition.mark_solved(sub_problem.id, solution)
                        solved_ids.append(sub_problem.id)
            
            # Update dependencies
            decomposition.update_dependencies()
        
        return decomposition.get_solution()
