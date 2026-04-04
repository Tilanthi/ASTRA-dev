"""
Abstraction Learning: Discover New Symbolic Templates

This module implements abstraction learning - the ability to discover
new symbolic templates from numerical patterns.

Key Features:
- Symbolic regression for equation discovery
- Template composition for hierarchical abstractions
- Validation of learned abstractions
- Integration with V36 SymbolicCausalAbstraction
- V40: Sympy-based expression simplification

Why This Matters for AGI:
- Goes beyond fixed templates to open-ended concept discovery
- Enables automatic theory building
- Compresses numerical patterns into symbolic knowledge

Date: 2025-12-11
Version: 40.0
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import re
from collections import defaultdict
from itertools import combinations, product


class OperationType(Enum):
    """Types of symbolic operations"""
    UNARY = "unary"      # f(x)
    BINARY = "binary"    # f(x, y)
    REDUCTION = "reduction"  # f(x1, x2, ..., xn)


@dataclass
class SymbolicOperation:
    """A symbolic operation"""
    name: str
    op_type: OperationType
    function: Callable
    derivative: Optional[Callable] = None
    complexity: int = 1

    def apply(self, *args) -> np.ndarray:
        """Apply operation"""
        return self.function(*args)


@dataclass
class LearnedTemplate:
    """A learned symbolic template"""
    template_id: str
    expression: str       # Human-readable expression
    operations: List[str]  # Operations used
    parameters: Dict[str, float]  # Fitted parameters
    variables: List[str]   # Variable names

    # Performance metrics
    fit_score: float = 0.0   # R² or similar
    complexity: int = 1       # Number of operations
    generalization_score: float = 0.0

    # Validation
    n_validations: int = 0
    validation_domains: List[str] = field(default_factory=list)

    # Origin
    source: str = "learned"  # 'learned', 'composed', 'inherited'
    parent_templates: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'template_id': self.template_id,
            'expression': self.expression,
            'operations': self.operations,
            'parameters': self.parameters,
            'variables': self.variables,
            'fit_score': self.fit_score,
            'complexity': self.complexity,
            'generalization_score': self.generalization_score,
            'n_validations': self.n_validations,
            'validation_domains': self.validation_domains,
            'source': self.source,
            'parent_templates': self.parent_templates
        }


class OperationLibrary:
    """Library of symbolic operations for regression"""

    def __init__(self):
        self.operations: Dict[str, SymbolicOperation] = {}
        self._build_default_operations()

    def _build_default_operations(self):
        """Build default operation library"""

        # Unary operations
        self.add_operation(SymbolicOperation(
            name='identity', op_type=OperationType.UNARY,
            function=lambda x: x,
            complexity=0
        ))

        self.add_operation(SymbolicOperation(
            name='neg', op_type=OperationType.UNARY,
            function=lambda x: -x,
            complexity=1
        ))

        self.add_operation(SymbolicOperation(
            name='sqrt', op_type=OperationType.UNARY,
            function=lambda x: np.sqrt(np.abs(x) + 1e-10),
            complexity=2
        ))

        self.add_operation(SymbolicOperation(
            name='square', op_type=OperationType.UNARY,
            function=lambda x: x ** 2,
            complexity=1
        ))

        self.add_operation(SymbolicOperation(
            name='cube', op_type=OperationType.UNARY,
            function=lambda x: x ** 3,
            complexity=2
        ))

        self.add_operation(SymbolicOperation(
            name='exp', op_type=OperationType.UNARY,
            function=lambda x: np.exp(np.clip(x, -20, 20)),
            complexity=3
        ))

        self.add_operation(SymbolicOperation(
            name='log', op_type=OperationType.UNARY,
            function=lambda x: np.log(np.abs(x) + 1e-10),
            complexity=3
        ))

        self.add_operation(SymbolicOperation(
            name='sin', op_type=OperationType.UNARY,
            function=lambda x: np.sin(x),
            complexity=2
        ))

        self.add_operation(SymbolicOperation(
            name='cos', op_type=OperationType.UNARY,
            function=lambda x: np.cos(x),
            complexity=2
        ))

        self.add_operation(SymbolicOperation(
            name='tanh', op_type=OperationType.UNARY,
            function=lambda x: np.tanh(x),
            complexity=3
        ))

        self.add_operation(SymbolicOperation(
            name='inv', op_type=OperationType.UNARY,
            function=lambda x: 1.0 / (x + 1e-10 * np.sign(x + 1e-10)),
            complexity=2
        ))

        # Binary operations
        self.add_operation(SymbolicOperation(
            name='add', op_type=OperationType.BINARY,
            function=lambda x, y: x + y,
            complexity=1
        ))

        self.add_operation(SymbolicOperation(
            name='sub', op_type=OperationType.BINARY,
            function=lambda x, y: x - y,
            complexity=1
        ))

        self.add_operation(SymbolicOperation(
            name='mul', op_type=OperationType.BINARY,
            function=lambda x, y: x * y,
            complexity=1
        ))

        self.add_operation(SymbolicOperation(
            name='div', op_type=OperationType.BINARY,
            function=lambda x, y: x / (y + 1e-10 * np.sign(y + 1e-10)),
            complexity=2
        ))

        self.add_operation(SymbolicOperation(
            name='pow', op_type=OperationType.BINARY,
            function=lambda x, y: np.power(np.abs(x) + 1e-10, np.clip(y, -5, 5)),
            complexity=3
        ))

    def add_operation(self, op: SymbolicOperation):
        """Add operation to library"""
        self.operations[op.name] = op

    def get_unary(self) -> List[SymbolicOperation]:
        """Get unary operations"""
        return [op for op in self.operations.values() if op.op_type == OperationType.UNARY]

    def get_binary(self) -> List[SymbolicOperation]:
        """Get binary operations"""
        return [op for op in self.operations.values() if op.op_type == OperationType.BINARY]


@dataclass
class ExpressionTree:
    """A symbolic expression tree"""
    operation: str
    children: List['ExpressionTree'] = field(default_factory=list)
    value: Optional[float] = None  # For constant nodes
    variable: Optional[str] = None  # For variable nodes

    def evaluate(self, variables: Dict[str, np.ndarray],
                 library: OperationLibrary) -> np.ndarray:
        """Evaluate expression tree"""
        if self.variable is not None:
            return variables[self.variable]

        if self.value is not None:
            # Return constant array
            any_var = list(variables.values())[0]
            return np.full_like(any_var, self.value)

        op = library.operations[self.operation]

        if op.op_type == OperationType.UNARY:
            child_val = self.children[0].evaluate(variables, library)
            return op.apply(child_val)

        elif op.op_type == OperationType.BINARY:
            left = self.children[0].evaluate(variables, library)
            right = self.children[1].evaluate(variables, library)
            return op.apply(left, right)

        return np.zeros_like(list(variables.values())[0])

    def to_expression(self) -> str:
        """Convert to human-readable expression"""
        if self.variable is not None:
            return self.variable

        if self.value is not None:
            return f"{self.value:.4f}"

        if len(self.children) == 1:
            child_expr = self.children[0].to_expression()
            return f"{self.operation}({child_expr})"

        elif len(self.children) == 2:
            left = self.children[0].to_expression()
            right = self.children[1].to_expression()

            if self.operation in ['add', 'sub', 'mul', 'div']:
                op_symbol = {
                    'add': '+', 'sub': '-', 'mul': '*', 'div': '/'
                }[self.operation]
                return f"({left} {op_symbol} {right})"
            else:
                return f"{self.operation}({left}, {right})"

        return self.operation

    def complexity(self, library: OperationLibrary) -> int:
        """Compute tree complexity"""
        if self.variable is not None or self.value is not None:
            return 0

        op = library.operations.get(self.operation)
        op_complexity = op.complexity if op else 1

        child_complexity = sum(c.complexity(library) for c in self.children)

        return op_complexity + child_complexity

    def copy(self) -> 'ExpressionTree':
        """Deep copy tree"""
        return ExpressionTree(
            operation=self.operation,
            children=[c.copy() for c in self.children],
            value=self.value,
            variable=self.variable
        )


class SymbolicRegressor:
    """
    Symbolic regression using genetic programming.

    Discovers symbolic expressions that fit numerical data.
    """

    def __init__(self, library: OperationLibrary = None,
                 population_size: int = 100,
                 max_generations: int = 50,
                 max_depth: int = 5):
        """
        Args:
            library: Operation library
            population_size: GP population size
            max_generations: Maximum generations
            max_depth: Maximum tree depth
        """
        self.library = library or OperationLibrary()
        self.pop_size = population_size
        self.max_gen = max_generations
        self.max_depth = max_depth

        # GP parameters
        self.crossover_prob = 0.7
        self.mutation_prob = 0.2
        self.tournament_size = 5

    def fit(self, X: np.ndarray, y: np.ndarray,
            var_names: List[str] = None) -> ExpressionTree:
        """
        Fit symbolic expression to data.

        Args:
            X: Input features (n_samples x n_features)
            y: Target values (n_samples,)
            var_names: Variable names

        Returns:
            Best expression tree found
        """
        if var_names is None:
            var_names = [f"x{i}" for i in range(X.shape[1])]

        # Convert to variable dict
        variables = {name: X[:, i] for i, name in enumerate(var_names)}

        # Initialize population
        population = self._initialize_population(var_names)

        # Evaluate fitness
        fitness = [self._fitness(tree, variables, y) for tree in population]

        best_tree = population[np.argmax(fitness)]
        best_fitness = max(fitness)

        # Evolution loop
        for gen in range(self.max_gen):
            # Selection
            new_population = []

            while len(new_population) < self.pop_size:
                # Tournament selection
                parent1 = self._tournament_select(population, fitness)
                parent2 = self._tournament_select(population, fitness)

                # Crossover
                if np.random.rand() < self.crossover_prob:
                    child = self._crossover(parent1, parent2)
                else:
                    child = parent1.copy()

                # Mutation
                if np.random.rand() < self.mutation_prob:
                    child = self._mutate(child, var_names)

                new_population.append(child)

            # Evaluate new population
            population = new_population
            fitness = [self._fitness(tree, variables, y) for tree in population]

            # Track best
            gen_best_idx = np.argmax(fitness)
            if fitness[gen_best_idx] > best_fitness:
                best_fitness = fitness[gen_best_idx]
                best_tree = population[gen_best_idx].copy()

        return best_tree

    def _initialize_population(self, var_names: List[str]) -> List[ExpressionTree]:
        """Initialize random population"""
        population = []

        for _ in range(self.pop_size):
            tree = self._random_tree(var_names, self.max_depth)
            population.append(tree)

        return population

    def _random_tree(self, var_names: List[str], max_depth: int,
                     current_depth: int = 0) -> ExpressionTree:
        """Generate random expression tree"""
        # Terminal nodes at max depth
        if current_depth >= max_depth or (current_depth > 1 and np.random.rand() < 0.3):
            if np.random.rand() < 0.7:
                # Variable
                var = np.random.choice(var_names)
                return ExpressionTree(operation='var', variable=var)
            else:
                # Constant
                const = np.random.uniform(-2, 2)
                return ExpressionTree(operation='const', value=const)

        # Internal nodes
        if np.random.rand() < 0.5:
            # Unary operation
            unary_ops = self.library.get_unary()
            op = np.random.choice(unary_ops)
            child = self._random_tree(var_names, max_depth, current_depth + 1)
            return ExpressionTree(operation=op.name, children=[child])
        else:
            # Binary operation
            binary_ops = self.library.get_binary()
            op = np.random.choice(binary_ops)
            left = self._random_tree(var_names, max_depth, current_depth + 1)
            right = self._random_tree(var_names, max_depth, current_depth + 1)
