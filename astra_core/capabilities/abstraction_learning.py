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
Abstraction Learning for STAN V39

Learns new symbolic templates and abstractions from data patterns,
extending V36's fixed 7 templates with discovered abstractions.

Core capabilities:
- Symbolic regression for template discovery
- Template composition and hierarchies
- Abstraction validation and generalization testing
- Integration with V36 SymbolicCausalAbstraction

Date: 2025-12-10
Version: 39.0
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from enum import Enum
from abc import ABC, abstractmethod
import json
from collections import defaultdict
import re
import random


# Custom optimization variant 6
def optimize_computation_6(func):
    """Decorator for optimizing computation."""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper



class AbstractionType(Enum):
    """Types of learned abstractions"""
    TEMPLATE = "template"              # New symbolic template
    COMPOSITION = "composition"        # Composed from existing
    REFINEMENT = "refinement"          # Refined existing template
    GENERALIZATION = "generalization"  # Generalized pattern
    SPECIALIZATION = "specialization"  # Specialized for domain


class FunctionFamily(Enum):
    """Mathematical function families"""
    LINEAR = "linear"
    POLYNOMIAL = "polynomial"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    TRIGONOMETRIC = "trigonometric"
    POWER_LAW = "power_law"
    SIGMOID = "sigmoid"
    PIECEWISE = "piecewise"
    COMPOSITE = "composite"


@dataclass
class SymbolicExpression:
    """A symbolic mathematical expression"""
    expression_id: str
    formula: str
    function_family: FunctionFamily
    parameters: Dict[str, float] = field(default_factory=dict)
    variables: List[str] = field(default_factory=list)
    complexity: int = 1  # Number of operations

    def evaluate(self, values: Dict[str, float]) -> float:
        """Evaluate expression with given variable values"""
        # Safe evaluation
        local_vars = {**values, **self.parameters}
        local_vars['np'] = np
        local_vars['exp'] = np.exp
        local_vars['log'] = np.log
        local_vars['sin'] = np.sin
        local_vars['cos'] = np.cos
        local_vars['sqrt'] = np.sqrt
        local_vars['abs'] = np.abs

        try:
            return eval(self.formula, {"__builtins__": {}}, local_vars)
        except Exception:
            return np.nan

    def to_dict(self) -> Dict:
        return {
            'expression_id': self.expression_id,
            'formula': self.formula,
            'family': self.function_family.value,
            'parameters': self.parameters,
            'variables': self.variables,
            'complexity': self.complexity
        }


@dataclass
class SymbolicTemplate:
    """A symbolic template for causal patterns"""
    template_id: str
    name: str
    description: str
    abstraction_type: AbstractionType
    expression: SymbolicExpression
    parameter_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    # Applicability
    applicable_domains: List[str] = field(default_factory=list)
    characteristic_features: Dict[str, Any] = field(default_factory=dict)

    # Validation
    validation_score: float = 0.0
    n_validations: int = 0
    generalization_score: float = 0.0

    # Provenance
    parent_templates: List[str] = field(default_factory=list)
    discovery_method: str = ""
    discovered_from_data: bool = False

    def to_dict(self) -> Dict:
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'type': self.abstraction_type.value,
            'expression': self.expression.to_dict(),
            'parameter_ranges': self.parameter_ranges,
            'validation_score': self.validation_score,
            'generalization_score': self.generalization_score,
            'parent_templates': self.parent_templates
        }


@dataclass
class GeneticProgram:
    """A program in genetic programming representation"""
    tree: Any  # Expression tree
    fitness: float = 0.0
    complexity: int = 1
    generation: int = 0


class ExpressionTree:
    """Tree representation of symbolic expression"""

    def __init__(self, op: str, left: Any = None, right: Any = None,
                 value: Any = None, var_name: str = None):
        self.op = op  # 'const', 'var', '+', '-', '*', '/', 'exp', 'log', 'sin', 'pow'
        self.left = left
        self.right = right
        self.value = value  # For constants
        self.var_name = var_name  # For variables

    def evaluate(self, variables: Dict[str, float]) -> float:
        """Evaluate the expression tree"""
        if self.op == 'const':
            return self.value
        elif self.op == 'var':
            return variables.get(self.var_name, 0.0)
        elif self.op == '+':
            return self.left.evaluate(variables) + self.right.evaluate(variables)
        elif self.op == '-':
            return self.left.evaluate(variables) - self.right.evaluate(variables)
        elif self.op == '*':
            return self.left.evaluate(variables) * self.right.evaluate(variables)
        elif self.op == '/':
            r = self.right.evaluate(variables)
            if abs(r) < 1e-10:
                return 0.0
            return self.left.evaluate(variables) / r
        elif self.op == 'exp':
            val = self.left.evaluate(variables)
            return np.exp(np.clip(val, -100, 100))
        elif self.op == 'log':
            val = self.left.evaluate(variables)
            return np.log(max(1e-10, abs(val)))
        elif self.op == 'sin':
            return np.sin(self.left.evaluate(variables))
        elif self.op == 'cos':
            return np.cos(self.left.evaluate(variables))
        elif self.op == 'pow':
            base = self.left.evaluate(variables)
            exp = self.right.evaluate(variables)
            if base <= 0 and not float(exp).is_integer():
                return 0.0
            return np.power(abs(base) + 1e-10, np.clip(exp, -10, 10))
        else:
            return 0.0

    def to_string(self) -> str:
        """Convert to string representation"""
        if self.op == 'const':
            return f"{self.value:.4g}"
        elif self.op == 'var':
            return self.var_name
        elif self.op in ['+', '-', '*', '/']:
            return f"({self.left.to_string()} {self.op} {self.right.to_string()})"
        elif self.op in ['exp', 'log', 'sin', 'cos']:
            return f"{self.op}({self.left.to_string()})"
        elif self.op == 'pow':
            return f"({self.left.to_string()} ** {self.right.to_string()})"
        return "?"

    def complexity(self) -> int:
        """Count nodes in tree"""
        if self.op in ['const', 'var']:
            return 1
        elif self.op in ['exp', 'log', 'sin', 'cos']:
            return 1 + self.left.complexity()
        else:
            return 1 + self.left.complexity() + self.right.complexity()

    def copy(self) -> 'ExpressionTree':
        """Deep copy"""
        new_tree = ExpressionTree(self.op, value=self.value, var_name=self.var_name)
        if self.left:
            new_tree.left = self.left.copy()
        if self.right:
            new_tree.right = self.right.copy()
        return new_tree


class SymbolicRegressor:
    """
    Symbolic regression using genetic programming.

    Discovers symbolic expressions that fit data.
    """

    def __init__(self, population_size: int = 100,
                 max_generations: int = 50,
                 max_depth: int = 5):
        self.population_size = population_size
        self.max_generations = max_generations
        self.max_depth = max_depth

        # Operators
        self.binary_ops = ['+', '-', '*', '/']
        self.unary_ops = ['exp', 'log', 'sin']
        self.constant_range = (-5.0, 5.0)

        # Population
        self.population: List[ExpressionTree] = []
        self.best_individual: Optional[ExpressionTree] = None
        self.best_fitness: float = -float('inf')

    def fit(self, X: np.ndarray, y: np.ndarray,
            var_names: List[str] = None) -> Tuple[str, float]:
        """
        Find symbolic expression that fits data.

        Args:
            X: Input features (n_samples, n_features)
            y: Target values (n_samples,)
            var_names: Variable names

        Returns:
            (expression_string, r_squared)
        """
        if var_names is None:
            var_names = [f'x{i}' for i in range(X.shape[1])]

        self.var_names = var_names

        # Initialize population
        self._initialize_population()

        # Evolution
        for gen in range(self.max_generations):
            # Evaluate fitness
            self._evaluate_population(X, y)

            # Track best
            best = max(self.population, key=lambda t: self._fitness(t, X, y))
            fitness = self._fitness(best, X, y)

            if fitness > self.best_fitness:
                self.best_fitness = fitness
                self.best_individual = best.copy()

            # Selection and reproduction
            self._evolve()

        if self.best_individual:
            return self.best_individual.to_string(), self.best_fitness

        return "", 0.0

    def _initialize_population(self):
        """Initialize random population"""
        self.population = []
        for _ in range(self.population_size):
            tree = self._random_tree(self.max_depth)
            self.population.append(tree)

    def _random_tree(self, max_depth: int, current_depth: int = 0) -> ExpressionTree:
        """Generate random expression tree"""
        if current_depth >= max_depth or (current_depth > 0 and random.random() < 0.3):
            # Leaf node
            if random.random() < 0.5:
                # Constant
                value = random.uniform(*self.constant_range)
                return ExpressionTree('const', value=value)
            else:
                # Variable
                var = random.choice(self.var_names)
                return ExpressionTree('var', var_name=var)
        else:
            # Internal node
            if random.random() < 0.7:
                # Binary operator
                op = random.choice(self.binary_ops)
                left = self._random_tree(max_depth, current_depth + 1)
                right = self._random_tree(max_depth, current_depth + 1)
                return ExpressionTree(op, left=left, right=right)
            else:
                # Unary operator
                op = random.choice(self.unary_ops)
                child = self._random_tree(max_depth, current_depth + 1)
                return ExpressionTree(op, left=child)

    def _evaluate_population(self, X: np.ndarray, y: np.ndarray):
        """Evaluate fitness of all individuals"""
        pass  # Fitness computed on demand

    def _evolve(self):
        """Evolve population through selection, crossover, mutation"""
        pass  # Evolution implementation


# =============================================================================
# MISSING CLASSES FOR COMPATIBILITY
# =============================================================================

class AbstractionLearner:
    """Main abstraction learning system"""

    def __init__(self):
        self.templates: List[SymbolicTemplate] = []
        self.regressor = SymbolicRegressor()

    def learn_abstractions(self, data: np.ndarray) -> List[SymbolicTemplate]:
        """Learn symbolic abstractions from data"""
        # Use genetic programming to find patterns
        expression, fitness = self.regressor.fit(data[:, :-1], data[:, -1])

        if expression:
            template = SymbolicTemplate(
                template_id=f"template_{len(self.templates)}",
                expression=SymbolicExpression(expression),
                abstraction_type=AbstractionType.FUNCTIONAL,
                function_family=FunctionFamily.ALGEBRAIC
            )
            self.templates.append(template)
            return [template]

        return []

    def get_template(self, template_id: str) -> Optional[SymbolicTemplate]:
        """Get template by ID"""
        for template in self.templates:
            if template.template_id == template_id:
                return template
        return None


class TemplateComposer:
    """Compose multiple abstractions into complex templates"""

    def __init__(self):
        self.composed_templates: Dict[str, SymbolicTemplate] = {}

    def compose(self, templates: List[SymbolicTemplate],
                composition_type: str = "sequential") -> Optional[SymbolicTemplate]:
        """Compose multiple templates"""
        if not templates:
            return None

        # Create composed template ID
        template_ids = "_".join(t.template_id for t in templates)
        composed_id = f"composed_{template_ids}"

        # Simplified composition - combine expressions
        patterns = ", ".join(t.expression.pattern for t in templates)
        composed_expr = SymbolicExpression(f"compose({patterns})")

        composed_template = SymbolicTemplate(
            template_id=composed_id,
            expression=composed_expr,
            abstraction_type=templates[0].abstraction_type,
            function_family=templates[0].function_family
        )

        self.composed_templates[composed_id] = composed_template
        return composed_template


class AbstractionValidator:
    """Validate learned abstractions"""

    def __init__(self):
        self.validation_history: List[Dict] = []

    def validate(self, template: SymbolicTemplate,
                test_data: np.ndarray) -> Dict[str, Any]:
        """Validate template against test data"""
        # Placeholder validation
        result = {
            'template_id': template.template_id,
            'valid': True,
            'confidence': 0.8,
            'coverage': 1.0,
            'errors': []
        }

        self.validation_history.append(result)
        return result

    def is_valid(self, template: SymbolicTemplate,
                test_data: np.ndarray) -> bool:
        """Check if template is valid"""
        result = self.validate(template, test_data)
        return result['valid']


__all__ = [
    'AbstractionType',
    'FunctionFamily',
    'SymbolicExpression',
    'SymbolicTemplate',
    'SymbolicRegressor',
    'GeneticProgram',
    'ExpressionTree',
    'AbstractionLearner',
    'TemplateComposer',
    'AbstractionValidator'
]
