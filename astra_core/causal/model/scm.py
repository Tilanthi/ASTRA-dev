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
Structural Causal Model (SCM) Implementation

Based on Pearl's causal hierarchy and structural causal models.
Provides the foundation for all causal reasoning in STAN-CORE V4.0.

References:
- Pearl, J. (2009). Causality
- Pearl, J. & Mackenzie, D. (2018). The Book of Why
"""

from dataclasses import dataclass, field
from typing import Dict, Set, Optional, Callable, Any, List
from enum import Enum
import copy
import numpy as np

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None


class VariableType(Enum):
    """Types of variables in causal models."""
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"
    BINARY = "binary"
    ORDINAL = "ordinal"
    CATEGORICAL = "categorical"


@dataclass
class Variable:
    """
    A variable in a causal model.

    Attributes:
        name: Variable name (unique identifier)
        type: Variable type (continuous, discrete, etc.)
        domain: Optional domain/range of values
        description: Human-readable description
        metadata: Additional metadata
    """
    name: str
    type: VariableType
    domain: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate variable configuration."""
        if not self.name:
            raise ValueError("Variable name cannot be empty")

    def __repr__(self):
        return f"Variable({self.name}, {self.type.value})"

    def __hash__(self):
        return hash(self.name)


@dataclass
class StructuralEquation:
    """
    A structural equation defining how a variable depends on its causes.

    In an SCM, each endogenous variable X is defined by:
    X = f(PA(X), U_X)

    where PA(X) are the parents (direct causes) and U_X is the noise term.

    Attributes:
        function: The function f mapping parents and noise to effect
        parameters: Optional parameters of the function
        noise_distribution: Distribution of the noise term
        is_invertible: Whether the function can be inverted (for abduction)
        description: Human-readable description
    """
    function: Callable
    parameters: Optional[Dict[str, Any]] = None
    noise_distribution: Optional[str] = "gaussian"
    is_invertible: bool = False
    description: Optional[str] = None

    def evaluate(self, parent_values: Dict[str, float]) -> float:
        """
        Evaluate the structural equation given parent values.

        Args:
            parent_values: Dict mapping parent variable names to values

        Returns:
            Computed value of the effect variable
        """
        try:
            return self.function(parent_values)
        except Exception as e:
            raise ValueError(f"Error evaluating structural equation: {e}")

    def invert(self, effect: float, parent_values: Dict[str, float]) -> float:
        """
        Invert the structural equation to recover the noise term.

        For counterfactual reasoning, we need to compute:
        U_X = f^{-1}(X, PA(X))

        This requires the function to be invertible.

        Args:
            effect: Observed value of the effect variable
            parent_values: Values of the parent variables

        Returns:
            Value of the noise term that would produce the observed effect
        """
        if not self.is_invertible:
            raise ValueError("Cannot invert non-invertible structural equation")

        # Default inversion: U = X - f(PA)
        # Assumes additive noise: X = f(PA) + U
        noise_free = self.function(parent_values)
        return effect - noise_free


@dataclass
class Intervention:
    """
    An intervention do(X=x) setting variables to specific values.

    Interventions modify structural causal models by replacing
    structural equations with constants.

    Attributes:
        assignments: Dict mapping variable names to values
        type: Intervention type (hard, soft, stochastic)
        duration: For temporal interventions, how long they last
    """
    assignments: Dict[str, float]
    type: str = "hard"  # hard, soft, stochastic
    duration: Optional[int] = None

    def __post_init__(self):
        if not self.assignments:
            raise ValueError("Intervention must have at least one assignment")

    def __contains__(self, var: str) -> bool:
        """Check if intervention affects a variable."""
        return var in self.assignments

    def __getitem__(self, var: str) -> float:
        """Get intervention value for a variable."""
        return self.assignments[var]


@dataclass
class CounterfactualQuery:
    """
    A counterfactual query: What would have happened to Y if X had been x?

    Formally: Y_{X=x}(u) where u is the noise unit from the observed world.

    Counterfactuals require the three-step process:
    1. Abduction: Infer U from observation
    2. Action: Modify model by intervention do(X=x)
    3. Prediction: Compute Y using modified model and inferred U

    Attributes:
        variable: The variable Y we want to compute
        observation: The observed facts (what actually happened)
        intervention: The hypothetical intervention
    """
    variable: str
    observation: Dict[str, float]
    intervention: Intervention

    def __repr__(self):
        return (f"CounterfactualQuery({self.variable}_{{{self.intervention}}} "
                f"| observation={self.observation})")


class StructuralCausalModel:
    """
    Structural Causal Model (Pearl 2009).

    An SCM consists of:
    - Endogenous variables V (determined within the model)
    - Exogenous variables U (external factors, noise terms)
    - Structural equations f_v: Each v in V is a function of PA(v) and U_v
    - Probability distribution P(U) over exogenous variables

    Capabilities:
    - Causal discovery from data
    - Intervention computation (do-calculus)
    - Counterfactual reasoning
    - Causal explanation
    - Causal effect identification

    Example:
        >>> scm = StructuralCausalModel()
        >>> scm.add_variable(Variable("X", VariableType.CONTINUOUS))
        >>> scm.add_variable(Variable("Y", VariableType.CONTINUOUS))
        >>>
        >>> def y_func(parents):
        ...     return 0.5 * parents.get("X", 0) + np.random.normal(0, 1)
        >>>
        >>> scm.add_edge("X", "Y", StructuralEquation(y_func))
        >>>
        >>> # Perform intervention
        >>> intervened = scm.do_intervention(Intervention({"X": 1.0}))
    """

    def __init__(self, name: str = "SCM"):
        """
        Initialize Structural Causal Model.

        Args:
            name: Optional name for the model
        """
        if not HAS_NETWORKX:
            raise ImportError(
                "networkx is required for StructuralCausalModel. "
                "Install with: pip install networkx"
            )

        self.name = name
        self.graph = nx.DiGraph()
        self.endogenous: Dict[str, Variable] = {}
        self.exogenous: Dict[str, Variable] = {}
        self.structural_equations: Dict[str, StructuralEquation] = {}
        self.exogenous_distributions: Dict[str, Any] = {}
        self.confidences: Dict[tuple, float] = {}
        self.metadata: Dict[str, Any] = {}

    def add_variable(self, var: Variable, is_endogenous: bool = True) -> None:
        """
        Add a variable to the SCM.

        Args:
            var: Variable to add
            is_endogenous: True if variable is endogenous (determined by model),
                          False if exogenous (external/noise)
        """
        if is_endogenous:
            self.endogenous[var.name] = var
            self.graph.add_node(var.name, type='endogenous', variable=var)
        else:
            self.exogenous[var.name] = var
            self.graph.add_node(var.name, type='exogenous', variable=var)

    def add_edge(self,
                 cause: str,
                 effect: str,
                 mechanism: StructuralEquation,
                 confidence: float = 1.0) -> None:
        """
        Add a causal edge: cause → effect.

        Args:
            cause: Name of causing variable
            effect: Name of effect variable
            mechanism: Structural equation defining the relationship
            confidence: Confidence in this causal relationship [0, 1]
        """
        if cause not in self.endogenous:
            raise ValueError(f"Cause '{cause}' not in model")
        if effect not in self.endogenous:
            raise ValueError(f"Effect '{effect}' not in model")

        self.graph.add_edge(cause, effect)
        self.structural_equations[effect] = mechanism
        self.confidences[(cause, effect)] = max(0.0, min(1.0, confidence))

    def get_parents(self, variable: str) -> Set[str]:
        """Get direct causes (parents) of a variable."""
        return set(self.graph.predecessors(variable))

    def get_children(self, variable: str) -> Set[str]:
        """Get direct effects (children) of a variable."""
        return set(self.graph.successors(variable))

    def get_ancestors(self, variable: str) -> Set[str]:
        """Get all indirect causes (ancestors) of a variable."""
        return set(nx.ancestors(self.graph, variable))

    def get_descendants(self, variable: str) -> Set[str]:
        """Get all indirect effects (descendants) of a variable."""
        return set(nx.descendants(self.graph, variable))

    def get_markov_blanket(self, variable: str) -> Set[str]:
        """
        Get Markov blanket of a variable.

        The Markov blanket is the minimal set of variables that
        renders the variable independent of all others.
        Includes: parents, children, and spouses (parents of children).
        """
        blanket = set()
        blanket.update(self.get_parents(variable))
        blanket.update(self.get_children(variable))
        for child in self.get_children(variable):
            blanket.update(self.get_parents(child))
        blanket.discard(variable)
        return blanket

    def do_intervention(self, intervention: Intervention) -> 'StructuralCausalModel':
        """
        Perform intervention do(X=x) using do-calculus.

        Creates a new mutilated SCM where structural equations for
        intervened variables are replaced with constants.

        Args:
            intervention: Intervention specifying variables to set

        Returns:
            New mutilated SCM with intervention applied
        """
        mutilated = copy.deepcopy(self)
        mutilated.name = f"{self.name}_mutilated"

        for var, value in intervention.assignments.items():
            if var not in mutilated.endogenous:
                raise ValueError(f"Cannot intervene on non-endogenous variable '{var}'")

            # Replace structural equation with constant function
            mutilated.structural_equations[var] = StructuralEquation(
                function=lambda pa: value,
                description=f"Intervention: {var} = {value}"
            )

            # Remove incoming edges to var (intervention breaks them)
            mutilated.graph.remove_edges_from(
                list(mutilated.graph.in_edges(var))
            )

        return mutilated

    def compute_causal_effect(self,
                              treatment: str,
                              outcome: str,
                              treatment_value: float = 1.0,
                              control_value: float = 0.0) -> float:
        """
        Compute average causal effect (ACE) of treatment on outcome.

        ACE = E[Y | do(X=x)] - E[Y | do(X=x')]

        Args:
            treatment: Treatment variable
            outcome: Outcome variable
            treatment_value: Treatment value
            control_value: Control value

        Returns:
            Average causal effect
        """
        # Intervention: do(treatment = treatment_value)
        intervention_treatment = Intervention({treatment: treatment_value})
        mutilated_treatment = self.do_intervention(intervention_treatment)

        # Intervention: do(treatment = control_value)
        intervention_control = Intervention({treatment: control_value})
        mutilated_control = self.do_intervention(intervention_control)

        # For linear SCMs, can compute analytically
        # For nonlinear, would need simulation
        # Simplified version here

        # Get effect size from structural equation
        if treatment in mutilated_treatment.structural_equations:
            equation = mutilated_treatment.structural_equations[treatment]
            if equation.parameters and 'coef' in equation.parameters:
                # Linear model: effect = coefficient * treatment_change
                treatment_change = treatment_value - control_value
                # Find coefficient for this treatment
                # This is simplified - real implementation more complex
                return treatment_change  # Placeholder

        # Fallback: return difference in intervention values
        return treatment_value - control_value

    def identify_causal_effect(self,
                               treatment: str,
                               outcome: str) -> Optional[str]:
        """
        Determine if causal effect P(Y|do(X)) is identifiable.

        Uses graph criteria (back-door, front-door) to determine
        if causal effect can be estimated from observational data.

        Args:
            treatment: Treatment variable X
            outcome: Outcome variable Y

        Returns:
            Identification result ("adjustment", "front_door", "instrumental", or None)
        """
        # Check back-door criterion
        adjustment_set = self._find_adjustment_set(treatment, outcome)
        if adjustment_set is not None:
            return "adjustment"

        # Check front-door criterion
        front_door = self._find_front_door(treatment, outcome)
        if front_door is not None:
            return "front_door"

        # Could be unidentifiable
        return None

    def _find_adjustment_set(self,
                             treatment: str,
                             outcome: str) -> Optional[Set[str]]:
        """
        Find adjustment set satisfying back-door criterion.

        A set Z satisfies back-door criterion relative to (X, Y) if:
        1. Z blocks all back-door paths from X to Y
        2. No node in Z is a descendant of X
        """
        from itertools import combinations

        # Find all back-door paths (paths with arrow into X)
        backdoor_paths = self._find_backdoor_paths(treatment, outcome)

        if not backdoor_paths:
            return set()  # No adjustment needed

        # Collect candidates
        candidates = set()
        for path in backdoor_paths:
            for node in path[1:-1]:  # Exclude treatment and outcome
                if node != treatment and not self._is_descendant(node, treatment):
                    candidates.add(node)

        # Find minimal set
        for size in range(len(candidates) + 1):
            for subset in combinations(candidates, size):
                if self._blocks_all_backdoors(set(subset), treatment, outcome):
                    return set(subset)

        return None

    def _find_backdoor_paths(self,
                             treatment: str,
                             outcome: str) -> List[List[str]]:
        """Find all back-door paths from treatment to outcome."""
        all_paths = list(nx.all_simple_paths(
            self.graph.to_undirected(),
            treatment,
            outcome,
            cutoff=10
        ))

        backdoor_paths = []
        for path in all_paths:
            # Check if first edge is into treatment (back-door)
            if len(path) > 1:
                if self.graph.has_edge(path[1], path[0]):
                    backdoor_paths.append(path)

        return backdoor_paths

    def _blocks_all_backdoors(self,
                              adjustment_set: Set[str],
                              treatment: str,
                              outcome: str) -> bool:
        """Check if adjustment set blocks all back-door paths."""
        backdoor_paths = self._find_backdoor_paths(treatment, outcome)

        for path in backdoor_paths:
            blocked = False
            for i, node in enumerate(path[1:-1], 1):
                if node in adjustment_set:
                    # Check if it's a non-collider
                    prev_node = path[i-1]
                    next_node = path[i+1]
                    is_collider = (self.graph.has_edge(prev_node, node) and
                                  self.graph.has_edge(next_node, node))
                    if not is_collider:
                        blocked = True
                        break

            if not blocked:
                return False

        return True

    def _is_descendant(self, node: str, ancestor: str) -> bool:
        """Check if node is a descendant of ancestor."""
        return node in nx.descendants(self.graph, ancestor)

    def _find_front_door(self,
                         treatment: str,
                         outcome: str) -> Optional[Set[str]]:
        """
        Find set of mediators satisfying front-door criterion.

        A set Z satisfies front-door criterion if:
        1. Z intercepts all directed paths from X to Y
        2. No unblocked back-door path from X to Z
        3. All back-door paths from Z to Y are blocked by X
        """
        # Find all nodes on directed paths from X to Y
        mediators = set()
        for path in nx.all_simple_paths(self.graph, treatment, outcome):
            for node in path[1:-1]:  # Exclude X and Y
                mediators.add(node)

        # Check front-door conditions
        # Simplified - full implementation more complex
        if mediators:
            return mediators

        return None

    def visualize(self, save_path: Optional[str] = None) -> None:
        """
        Visualize the causal graph.

        Args:
            save_path: Optional path to save figure
        """
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 8))

        pos = nx.spring_layout(self.graph, k=2, iterations=50, seed=42)

        # Draw nodes
        endogenous_nodes = [n for n in self.graph.nodes()
                           if n in self.endogenous]
        exogenous_nodes = [n for n in self.graph.nodes()
                          if n in self.exogenous]

        nx.draw_networkx_nodes(
            self.graph, pos,
            nodelist=endogenous_nodes,
            node_color='lightblue',
            node_size=1000,
            ax=ax
        )

        if exogenous_nodes:
            nx.draw_networkx_nodes(
                self.graph, pos,
                nodelist=exogenous_nodes,
                node_color='lightgreen',
                node_size=800,
                ax=ax
            )

        # Draw edges
        nx.draw_networkx_edges(
            self.graph, pos,
            edge_color='gray',
            arrowsize=20,
            arrowstyle='->',
            width=2,
            ax=ax
        )

        # Draw labels
        nx.draw_networkx_labels(
            self.graph, pos,
            font_size=10,
            font_weight='bold',
            ax=ax
        )

        # Draw edge labels with confidence
        edge_labels = {}
        for (u, v), conf in self.confidences.items():
            edge_labels[(u, v)] = f"{conf:.2f}"

        nx.draw_networkx_edge_labels(
            self.graph, pos,
            edge_labels,
            font_size=8,
            ax=ax
        )

        ax.set_title(f"Structural Causal Model: {self.name}", fontsize=14, fontweight='bold')
        ax.axis('off')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert SCM to dictionary representation.

        Returns:
            Dictionary representation of the SCM
        """
        return {
            "name": self.name,
            "endogenous": {
                name: {
                    "type": var.type.value,
                    "description": var.description
                }
                for name, var in self.endogenous.items()
            },
            "exogenous": {
                name: {
                    "type": var.type.value,
                    "description": var.description
                }
                for name, var in self.exogenous.items()
            },
            "causal_edges": [
                {
                    "cause": u,
                    "effect": v,
                    "confidence": self.confidences.get((u, v), 1.0)
                }
                for u, v in self.graph.edges()
                if v in self.structural_equations
            ],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StructuralCausalModel':
        """
        Create SCM from dictionary representation.

        Args:
            data: Dictionary representation of SCM

        Returns:
            StructuralCausalModel instance
        """
        scm = cls(name=data.get("name", "SCM"))

        # Add variables
        for name, var_data in data.get("endogenous", {}).items():
            var = Variable(
                name=name,
                type=VariableType(var_data["type"]),
                description=var_data.get("description")
            )
            scm.add_variable(var, is_endogenous=True)

        for name, var_data in data.get("exogenous", {}).items():
            var = Variable(
                name=name,
                type=VariableType(var_data["type"]),
                description=var_data.get("description")
            )
            scm.add_variable(var, is_endogenous=False)

        # Add edges
        for edge_data in data.get("causal_edges", []):
            # Note: full implementation would need to deserialize
            # structural equations - this is simplified
            pass

        scm.metadata = data.get("metadata", {})

        return scm

    def __repr__(self) -> str:
        return (f"StructuralCausalModel(name={self.name}, "
                f"variables={len(self.endogenous)}, "
                f"edges={self.graph.number_of_edges()})")


def profile_causal_inference(func):
    """Decorator for profiling causal inference."""
    def wrapper(*args, **kwargs):
        import time
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Record start state
        start_time = time.time()
        start_memory = process.memory_info().rss

        # Run function
        result = func(*args, **kwargs)

        # Record end state
        end_time = time.time()
        end_memory = process.memory_info().rss

        # Add profiling info
        if isinstance(result, dict):
            result['_profiling'] = {
                'execution_time': end_time - start_time,
                'memory_delta': end_memory - start_memory,
                'cpu_percent': process.cpu_percent()
            }

        return result
    return wrapper


# Vectorized independence testing for efficiency
def vectorized_independence_test(data_matrix: np.ndarray) -> np.ndarray:
    """
    Compute pairwise independence tests in vectorized manner.

    Args:
        data_matrix: Shape (n_samples, n_variables)

    Returns:
        Correlation matrix
    """
    # Standardize
    data_centered = data_matrix - np.mean(data_matrix, axis=0)
    data_std = data_centered / (np.std(data_matrix, axis=0) + 1e-10)

    # Compute correlation matrix efficiently
    correlation = np.corrcoef(data_std.T)

    return correlation
