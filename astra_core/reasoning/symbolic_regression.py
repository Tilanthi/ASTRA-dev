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
Symbolic Regression with Physics Constraints for STAN V42

Discover governing equations from data while respecting:
- Dimensional analysis
- Conservation laws
- Known physics symmetries
- Find scaling relations
- Identify missing physics in models

Date: 2025-12-11
Version: 42.0
"""

import time
import uuid
import math
import copy
import random
from typing import Dict, List, Optional, Any, Tuple, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
import re


class DimensionType(Enum):
    """Physical dimensions"""
    LENGTH = "L"
    MASS = "M"
    TIME = "T"
    TEMPERATURE = "Θ"
    ELECTRIC_CURRENT = "I"
    LUMINOUS_INTENSITY = "J"
    AMOUNT = "N"
    DIMENSIONLESS = "1"


class OperatorType(Enum):
    """Mathematical operators in expressions"""
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    POWER = "^"
    SQRT = "sqrt"
    LOG = "log"
    EXP = "exp"
    SIN = "sin"
    COS = "cos"
    ABS = "abs"


class ConstraintType(Enum):
    """Types of physics constraints"""
    DIMENSIONAL = "dimensional"
    CONSERVATION = "conservation"
    SYMMETRY = "symmetry"
    POSITIVITY = "positivity"
    BOUNDEDNESS = "boundedness"
    MONOTONICITY = "monotonicity"


@dataclass
class Dimension:
    """Physical dimension representation"""
    length: int = 0
    mass: int = 0
    time: int = 0
    temperature: int = 0
    current: int = 0
    luminosity: int = 0
    amount: int = 0

    def __mul__(self, other: 'Dimension') -> 'Dimension':
        return Dimension(
            self.length + other.length,
            self.mass + other.mass,
            self.time + other.time,
            self.temperature + other.temperature,
            self.current + other.current,
            self.luminosity + other.luminosity,
            self.amount + other.amount
        )

    def __truediv__(self, other: 'Dimension') -> 'Dimension':
        return Dimension(
            self.length - other.length,
            self.mass - other.mass,
            self.time - other.time,
            self.temperature - other.temperature,
            self.current - other.current,
            self.luminosity - other.luminosity,
            self.amount - other.amount
        )

    def __pow__(self, n: int) -> 'Dimension':
        return Dimension(
            self.length * n,
            self.mass * n,
            self.time * n,
            self.temperature * n,
            self.current * n,
            self.luminosity * n,
            self.amount * n
        )

    def __eq__(self, other: 'Dimension') -> bool:
        return (self.length == other.length and
                self.mass == other.mass and
                self.time == other.time and
                self.temperature == other.temperature and
                self.current == other.current and
                self.luminosity == other.luminosity and
                self.amount == other.amount)

    def __hash__(self):
        return hash((self.length, self.mass, self.time, self.temperature,
                    self.current, self.luminosity, self.amount))

    def is_dimensionless(self) -> bool:
        return (self.length == 0 and self.mass == 0 and self.time == 0 and
                self.temperature == 0 and self.current == 0 and
                self.luminosity == 0 and self.amount == 0)

    def to_string(self) -> str:
        parts = []
        if self.length != 0:
            parts.append(f"L^{self.length}" if self.length != 1 else "L")
        if self.mass != 0:
            parts.append(f"M^{self.mass}" if self.mass != 1 else "M")
        if self.time != 0:
            parts.append(f"T^{self.time}" if self.time != 1 else "T")
        if self.temperature != 0:
            parts.append(f"Θ^{self.temperature}" if self.temperature != 1 else "Θ")

        return " ".join(parts) if parts else "1"


# Common dimensions
DIMENSIONLESS = Dimension()
LENGTH = Dimension(length=1)
MASS = Dimension(mass=1)
TIME = Dimension(time=1)
VELOCITY = Dimension(length=1, time=-1)
ACCELERATION = Dimension(length=1, time=-2)
FORCE = Dimension(mass=1, length=1, time=-2)
ENERGY = Dimension(mass=1, length=2, time=-2)
POWER = Dimension(mass=1, length=2, time=-3)
PRESSURE = Dimension(mass=1, length=-1, time=-2)
DENSITY = Dimension(mass=1, length=-3)
TEMPERATURE = Dimension(temperature=1)
LUMINOSITY = Dimension(mass=1, length=2, time=-3)  # Same as power


@dataclass
class Variable:
    """A variable in symbolic regression"""
    name: str
    dimension: Dimension
    values: List[float] = field(default_factory=list)
    uncertainty: float = 0.0
    is_target: bool = False
    bounds: Tuple[float, float] = field(default_factory=lambda: (-float('inf'), float('inf')))


@dataclass
class Constant:
    """A physical constant"""
    name: str
    symbol: str
    value: float
    dimension: Dimension
    uncertainty: float = 0.0


# Common physical constants (CGS)
PHYSICAL_CONSTANTS = {
    "G": Constant("Gravitational constant", "G", 6.674e-8,
                  Dimension(length=3, mass=-1, time=-2)),
    "c": Constant("Speed of light", "c", 2.998e10,
                  Dimension(length=1, time=-1)),
    "h": Constant("Planck constant", "h", 6.626e-27,
                  Dimension(mass=1, length=2, time=-1)),
    "k_B": Constant("Boltzmann constant", "k_B", 1.381e-16,
                    Dimension(mass=1, length=2, time=-2, temperature=-1)),
    "sigma_SB": Constant("Stefan-Boltzmann constant", "σ", 5.670e-5,
                         Dimension(mass=1, time=-3, temperature=-4)),
    "m_e": Constant("Electron mass", "m_e", 9.109e-28, MASS),
    "m_p": Constant("Proton mass", "m_p", 1.673e-24, MASS),
    "e": Constant("Elementary charge", "e", 4.803e-10,
                  Dimension(length=1.5, mass=0.5, time=-1)),  # esu
    "M_sun": Constant("Solar mass", "M_☉", 1.989e33, MASS),
    "L_sun": Constant("Solar luminosity", "L_☉", 3.828e33, LUMINOSITY),
    "pc": Constant("Parsec", "pc", 3.086e18, LENGTH),
    "AU": Constant("Astronomical unit", "AU", 1.496e13, LENGTH),
}


@dataclass
class ExpressionNode:
    """A node in an expression tree"""
    node_id: str
    node_type: str  # "variable", "constant", "operator", "number"
    value: Any = None  # Variable name, constant name, operator, or number
    children: List['ExpressionNode'] = field(default_factory=list)
    dimension: Optional[Dimension] = None

    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"expr_{uuid.uuid4().hex[:8]}"

    def to_string(self) -> str:
        """Convert to string representation"""
        if self.node_type == "variable":
            return str(self.value)
        elif self.node_type == "constant":
            return str(self.value)
        elif self.node_type == "number":
            if isinstance(self.value, float):
                if abs(self.value) < 0.01 or abs(self.value) > 1000:
                    return f"{self.value:.3e}"
                return f"{self.value:.4g}"
            return str(self.value)
        elif self.node_type == "operator":
            op = self.value
            if op in ["+", "-", "*", "/"]:
                if len(self.children) == 2:
                    left = self.children[0].to_string()
                    right = self.children[1].to_string()
                    return f"({left} {op} {right})"
            elif op == "^":
                if len(self.children) == 2:
                    base = self.children[0].to_string()
                    exp = self.children[1].to_string()
                    return f"({base})^({exp})"
            elif op in ["sqrt", "log", "exp", "sin", "cos", "abs"]:
                if len(self.children) == 1:
                    arg = self.children[0].to_string()
                    return f"{op}({arg})"
        return "?"

    def copy(self) -> 'ExpressionNode':
        """Create a deep copy"""
        return ExpressionNode(
            node_id="",
            node_type=self.node_type,
            value=self.value,
            children=[c.copy() for c in self.children],
            dimension=copy.copy(self.dimension)
        )


@dataclass
class DiscoveredEquation:
    """A discovered equation from symbolic regression"""
    equation_id: str
    expression: ExpressionNode
    target_variable: str

    # Quality metrics
    r_squared: float = 0.0
    rmse: float = float('inf')
    complexity: int = 0
    pareto_optimal: bool = False

    # Physics validity
    dimensionally_consistent: bool = False
    constraints_satisfied: List[str] = field(default_factory=list)
    constraints_violated: List[str] = field(default_factory=list)

    # Interpretation
    interpretation: str = ""
    similar_known_laws: List[str] = field(default_factory=list)

    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.equation_id:
            self.equation_id = f"eq_{uuid.uuid4().hex[:8]}"

    def to_string(self) -> str:
        return f"{self.target_variable} = {self.expression.to_string()}"


@dataclass
class PhysicsConstraint:
    """A physics constraint for symbolic regression"""
    constraint_id: str
    constraint_type: ConstraintType
    description: str

    # Constraint specification
    target_dimension: Optional[Dimension] = None
    conserved_quantity: str = ""
    symmetry_type: str = ""
    bounds: Tuple[float, float] = field(default_factory=lambda: (-float('inf'), float('inf')))
    monotonic_in: List[str] = field(default_factory=list)

    # Penalty weight
    weight: float = 1.0

    def __post_init__(self):
        if not self.constraint_id:
            self.constraint_id = f"con_{uuid.uuid4().hex[:8]}"


class DimensionalAnalyzer:
    """
    Performs dimensional analysis on expressions.
    """

    def __init__(self, variables: Dict[str, Variable]):
        self.variables = variables
        self.constants = PHYSICAL_CONSTANTS

    def compute_dimension(self, node: ExpressionNode) -> Optional[Dimension]:
        """Compute the dimension of an expression"""
        if node.node_type == "variable":
            var = self.variables.get(node.value)
            if var:
                node.dimension = var.dimension
                return var.dimension
            return None

        elif node.node_type == "constant":
            const = self.constants.get(node.value)
            if const:
                node.dimension = const.dimension
                return const.dimension
            return DIMENSIONLESS

        elif node.node_type == "number":
            node.dimension = DIMENSIONLESS
            return DIMENSIONLESS

        elif node.node_type == "operator":
            op = node.value

            if not node.children:
                return None

            child_dims = [self.compute_dimension(c) for c in node.children]

            if any(d is None for d in child_dims):
                return None

            if op == "+":
                # Addition requires same dimensions
                if len(child_dims) == 2 and child_dims[0] == child_dims[1]:
                    node.dimension = child_dims[0]
                    return child_dims[0]
                return None

            elif op == "-":
                if len(child_dims) == 2 and child_dims[0] == child_dims[1]:
                    node.dimension = child_dims[0]
                    return child_dims[0]
                return None

            elif op == "*":
                if len(child_dims) == 2:
                    result = child_dims[0] * child_dims[1]
                    node.dimension = result
                    return result
                return None

            elif op == "/":
                if len(child_dims) == 2:
                    result = child_dims[0] / child_dims[1]
                    node.dimension = result
                    return result
                return None

            elif op == "^":
                if len(child_dims) == 2:
                    # Exponent must be dimensionless
                    if child_dims[1].is_dimensionless():
                        # Get numeric exponent if possible
                        if node.children[1].node_type == "number":
                            exp = int(node.children[1].value)
                            result = child_dims[0] ** exp
                            node.dimension = result
                            return result
                    return None
                return None

            elif op in ["sqrt"]:
                if len(child_dims) == 1:
                    # Square root: divide all exponents by 2
                    d = child_dims[0]
                    if all(x % 2 == 0 for x in [d.length, d.mass, d.time,
                                                 d.temperature, d.current,
                                                 d.luminosity, d.amount]):
                        result = Dimension(
                            d.length // 2, d.mass // 2, d.time // 2,
                            d.temperature // 2, d.current // 2,
                            d.luminosity // 2, d.amount // 2
                        )
                        node.dimension = result
                        return result
                return None

            elif op in ["log", "exp", "sin", "cos"]:
                # Argument must be dimensionless
                if len(child_dims) == 1 and child_dims[0].is_dimensionless():
                    node.dimension = DIMENSIONLESS
                    return DIMENSIONLESS
                return None

            elif op == "abs":
                if len(child_dims) == 1:
                    node.dimension = child_dims[0]
                    return child_dims[0]
                return None

        return None

    def is_dimensionally_consistent(self,
                                   expression: ExpressionNode,
                                   target_dimension: Dimension) -> bool:
        """Check if expression has the correct dimensions"""
        expr_dim = self.compute_dimension(expression)
        if expr_dim is None:
            return False
        return expr_dim == target_dimension


class ExpressionEvaluator:
    """
    Evaluates expressions on data.
    """

    def __init__(self, variables: Dict[str, Variable]):
        self.variables = variables
        self.constants = PHYSICAL_CONSTANTS
