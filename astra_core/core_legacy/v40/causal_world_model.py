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
Causal World Model for STAN V40

Implements:
- Do-calculus for interventional reasoning
- Counterfactual inference
- Causal mechanism identification
- Structural causal models (SCM)

Target: +15-20% on causal reasoning questions

Date: 2025-12-11
Version: 40.0
"""

import re
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from enum import Enum
from abc import ABC, abstractmethod


class CausalRelationType(Enum):
    """Types of causal relationships"""
    DIRECT = "direct"           # X -> Y
    INDIRECT = "indirect"       # X -> Z -> Y
    CONFOUNDED = "confounded"   # X <- Z -> Y
    COLLIDER = "collider"       # X -> Z <- Y
    MEDIATOR = "mediator"       # X -> Z -> Y (Z mediates)
    UNKNOWN = "unknown"


class InterventionType(Enum):
    """Types of causal interventions"""
    DO = "do"           # do(X=x) - set X to x
    OBSERVE = "observe" # observe X=x
    SOFT = "soft"       # soft intervention - modify P(X)
    ATOMIC = "atomic"   # atomic intervention - single variable
    COMPOUND = "compound"  # compound - multiple variables


@dataclass
class CausalVariable:
    """A variable in a causal model"""
    name: str
    domain: str = "continuous"  # continuous, discrete, binary
    possible_values: List[Any] = field(default_factory=list)
    observed: bool = True  # Observable or latent
    exogenous: bool = False  # External to system

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'domain': self.domain,
            'observed': self.observed,
            'exogenous': self.exogenous
        }


@dataclass
class CausalMechanism:
    """A causal mechanism linking variables"""
    effect: str  # Variable being affected
    causes: List[str]  # Variables causing the effect
    mechanism_type: CausalRelationType = CausalRelationType.DIRECT
    strength: float = 1.0  # Causal strength

    # Functional form (if known)
    functional_form: Optional[str] = None  # e.g., "Y = a*X + b*Z + noise"

    # Structural parameters
    parameters: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'effect': self.effect,
            'causes': self.causes,
            'type': self.mechanism_type.value,
            'strength': self.strength,
            'formula': self.functional_form
        }


@dataclass
class Intervention:
    """A causal intervention"""
    variable: str
    value: Any
    intervention_type: InterventionType = InterventionType.DO

    def to_dict(self) -> Dict:
        return {
            'variable': self.variable,
            'value': self.value,
            'type': self.intervention_type.value
        }


@dataclass
class Counterfactual:
    """A counterfactual query"""
    factual: Dict[str, Any]  # What actually happened
    intervention: Intervention  # What if this was different
    query_variable: str  # What would have happened to this

    # Result
    result: Optional[Any] = None
    confidence: float = 0.0
    reasoning: str = ""

    def to_dict(self) -> Dict:
        return {
            'factual': self.factual,
            'intervention': self.intervention.to_dict(),
            'query': self.query_variable,
            'result': self.result,
            'confidence': self.confidence
        }


@dataclass
class CausalQuery:
    """A causal inference query"""
    query_type: str  # identification, estimation, counterfactual
    target: str  # Variable of interest
    conditions: Dict[str, Any] = field(default_factory=dict)
    interventions: List[Intervention] = field(default_factory=list)

    # Result
    identifiable: bool = False
    estimate: Optional[float] = None
    formula: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'type': self.query_type,
            'target': self.target,
            'conditions': self.conditions,
            'identifiable': self.identifiable,
            'estimate': self.estimate
        }


class CausalGraph:
    """
    Directed Acyclic Graph for causal structure.

    Supports:
    - d-separation queries
    - Path analysis
    - Adjustment set identification
    """

    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: Dict[str, Set[str]] = {}  # parent -> children
        self.reverse_edges: Dict[str, Set[str]] = {}  # child -> parents

    def add_node(self, node: str) -> None:
        """Add a node to the graph"""
        self.nodes.add(node)
        if node not in self.edges:
            self.edges[node] = set()
        if node not in self.reverse_edges:
            self.reverse_edges[node] = set()

    def add_edge(self, cause: str, effect: str) -> None:
        """Add directed edge cause -> effect"""
        self.add_node(cause)
        self.add_node(effect)
        self.edges[cause].add(effect)
        self.reverse_edges[effect].add(cause)

    def parents(self, node: str) -> Set[str]:
        """Get parent nodes"""
        return self.reverse_edges.get(node, set())

    def children(self, node: str) -> Set[str]:
        """Get child nodes"""
        return self.edges.get(node, set())

    def ancestors(self, node: str) -> Set[str]:
        """Get all ancestor nodes"""
        result = set()
        queue = list(self.parents(node))

        while queue:
            current = queue.pop(0)
            if current not in result:
                result.add(current)
                queue.extend(self.parents(current))

        return result

    def descendants(self, node: str) -> Set[str]:
        """Get all descendant nodes"""
        result = set()
        queue = list(self.children(node))

        while queue:
            current = queue.pop(0)
            if current not in result:
                result.add(current)
                queue.extend(self.children(current))

        return result

    def is_d_separated(self, x: str, y: str, z: Set[str]) -> bool:
        """
        Check if X and Y are d-separated given Z.

        Uses Bayes ball algorithm.
        """
        # Simple implementation: check all paths
        paths = self._find_all_paths(x, y)

        for path in paths:
            if not self._is_path_blocked(path, z):
                return False

        return True

    def _find_all_paths(self, start: str, end: str,
                       max_depth: int = 10) -> List[List[str]]:
        """Find all undirected paths between nodes"""
        paths = []

        def dfs(current: str, target: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            if current == target:
                paths.append(path[:])
                return

            # Try all neighbors (ignoring direction)
            neighbors = self.children(current) | self.parents(current)
            for neighbor in neighbors:
                if neighbor not in path:
                    path.append(neighbor)
                    dfs(neighbor, target, path, depth + 1)
                    path.pop()

        dfs(start, end, [start], 0)
        return paths

    def _is_path_blocked(self, path: List[str], z: Set[str]) -> bool:
        """Check if path is blocked by conditioning on Z"""
        if len(path) < 3:
            return False

        for i in range(1, len(path) - 1):
            prev_node = path[i - 1]
            curr_node = path[i]
            next_node = path[i + 1]

            # Determine structure at curr_node
            prev_to_curr = curr_node in self.children(prev_node)
            curr_to_next = next_node in self.children(curr_node)

            # Chain: -> curr ->
            if prev_to_curr and curr_to_next:
                if curr_node in z:
                    return True

            # Fork: <- curr ->
            if not prev_to_curr and curr_to_next:
                if curr_node in z:
                    return True

            # Collider: -> curr <-
            if prev_to_curr and not curr_to_next:
                # Collider blocks unless conditioned on
                curr_descendants = self.descendants(curr_node)
                if curr_node not in z and not (z & curr_descendants):
                    return True

        return False

    def find_adjustment_set(self, x: str, y: str) -> Optional[Set[str]]:
        """
        Find adjustment set for estimating causal effect X -> Y.

        Uses backdoor criterion.
        """
        # Find all backdoor paths
        x_parents = self.parents(x)

        if not x_parents:
            return set()  # No confounding

        # Simple: adjust for all parents of X
        adjustment = x_parents - {y}

        # Verify adjustment is valid (doesn't open new paths)
        # This is a simplification - full algorithm is more complex
        return adjustment


class StructuralCausalModel:
    """
    Structural Causal Model implementation.

    Supports:
    - Structural equations
    - Interventions
    - Counterfactuals
    """

    def __init__(self):
        self.graph = CausalGraph()
        self.variables: Dict[str, CausalVariable] = {}
        self.mechanisms: Dict[str, CausalMechanism] = {}

        # Structural equations: variable -> function
        self.equations: Dict[str, Callable] = {}

        # Noise distributions
        self.noise: Dict[str, Callable] = {}

    def add_variable(self, var: CausalVariable) -> None:
        """Add variable to model"""
        self.variables[var.name] = var
        self.graph.add_node(var.name)

    def add_mechanism(self, mechanism: CausalMechanism) -> None:
        """Add causal mechanism"""
        self.mechanisms[mechanism.effect] = mechanism

        for cause in mechanism.causes:
            self.graph.add_edge(cause, mechanism.effect)

    def set_equation(self, variable: str,
                    equation: Callable[[Dict[str, float]], float]) -> None:
        """Set structural equation for variable"""
        self.equations[variable] = equation

    def intervene(self, intervention: Intervention) -> 'StructuralCausalModel':
        """
        Create intervened model (do-calculus).

        Returns new SCM with intervention applied.
        """
        # Create copy of model
        intervened = StructuralCausalModel()
        intervened.variables = dict(self.variables)
        intervened.noise = dict(self.noise)

        # Copy mechanisms except for intervened variable
        for var, mech in self.mechanisms.items():
            if var != intervention.variable:
                intervened.add_mechanism(mech)

        # Set intervened variable to constant
        intervened.equations = dict(self.equations)
        intervened.equations[intervention.variable] = lambda _: intervention.value

        return intervened

    def compute_value(self, variable: str,
                     values: Dict[str, float] = None) -> float:
        """Compute value of variable given parent values"""
        values = values or {}

        if variable in self.equations:
            return self.equations[variable](values)

        return values.get(variable, 0.0)

    def sample(self, interventions: List[Intervention] = None) -> Dict[str, float]:
        """Sample from the model"""
        import random

        interventions = interventions or []

        # Create intervened model if needed
        model = self
        for intervention in interventions:
            model = model.intervene(intervention)

        # Topological sort for evaluation order
        order = self._topological_sort()
        values = {}

        for var in order:
            # Check if intervened
            intervention_value = None
            for interv in interventions:
                if interv.variable == var:
                    intervention_value = interv.value
                    break

            if intervention_value is not None:
                values[var] = intervention_value
            elif var in model.equations:
                values[var] = model.compute_value(var, values)
            else:
                # Use noise if defined
                if var in self.noise:
                    values[var] = self.noise[var]()
                else:
                    values[var] = random.gauss(0, 1)

        return values

    def _topological_sort(self) -> List[str]:
        """Topological sort of variables"""
        visited = set()
        result = []

        def dfs(node):
            if node in visited:
                return
            visited.add(node)

            for parent in self.graph.parents(node):
                dfs(parent)

            result.append(node)

        for var in self.variables:
            dfs(var)

        return result


class CounterfactualReasoner:
    """
    Counterfactual reasoning engine.

    Implements the three-step process:
    1. Abduction: Infer noise given observations
    2. Action: Intervene in model
    3. Prediction: Compute counterfactual outcome
    """

    def __init__(self, scm: StructuralCausalModel):
        self.scm = scm

    def evaluate(self, counterfactual: Counterfactual) -> Counterfactual:
        """
        Evaluate a counterfactual query.

        Args:
            counterfactual: The counterfactual to evaluate

        Returns:
            Updated counterfactual with result
        """
        # Step 1: Abduction - infer noise from factual
        noise = self._abduct_noise(counterfactual.factual)

        # Step 2: Action - create intervened model
        intervened = self.scm.intervene(counterfactual.intervention)

        # Step 3: Prediction - compute with inferred noise
        result = self._predict_with_noise(intervened,
                                          counterfactual.query_variable,
                                          noise,
                                          counterfactual.factual)

        counterfactual.result = result
        counterfactual.confidence = self._estimate_confidence(noise)
        counterfactual.reasoning = self._generate_reasoning(counterfactual)

        return counterfactual

    def _abduct_noise(self, factual: Dict[str, Any]) -> Dict[str, float]:
        """Infer noise terms from factual observations"""
        noise = {}

        # For each observed variable, infer noise
        for var, observed_value in factual.items():
            if var in self.scm.equations:
                # Compute expected value
                expected = self.scm.compute_value(var, factual)
                # Noise is difference
                noise[var] = observed_value - expected
            else:
                noise[var] = 0.0

        return noise

    def _predict_with_noise(self, model: StructuralCausalModel,
                           query_var: str,
                           noise: Dict[str, float],
                           factual: Dict[str, Any]) -> float:
        """Predict counterfactual value using inferred noise"""
        # Compute values in intervened world
        values = dict(factual)

        # Topological order
        order = model._topological_sort()

        for var in order:
            if var in model.equations:
                base_value = model.compute_value(var, values)
                # Add back noise
                values[var] = base_value + noise.get(var, 0.0)

        return values.get(query_var, 0.0)

    def _estimate_confidence(self, noise: Dict[str, float]) -> float:
        """Estimate confidence based on noise magnitude"""
        if not noise:
            return 0.5

        # Lower confidence if noise is large
        avg_noise = sum(abs(n) for n in noise.values()) / len(noise)
        confidence = 1.0 / (1.0 + avg_noise)

        return min(0.95, max(0.1, confidence))

    def _generate_reasoning(self, cf: Counterfactual) -> str:
        """Generate explanation of counterfactual reasoning"""
        parts = [
            f"Factual: {cf.factual}",
            f"Intervention: do({cf.intervention.variable}={cf.intervention.value})",
            f"Query: What would {cf.query_variable} be?",
            f"Result: {cf.result}"
        ]
        return " | ".join(parts)


class CausalWorldModel:
    """
    Main causal world model for reasoning.

    Integrates:
    - Causal graph structure
    - Structural causal model
    - Do-calculus
    - Counterfactual reasoning
    """

    def __init__(self):
        self.scm = StructuralCausalModel()
        self.counterfactual_reasoner = CounterfactualReasoner(self.scm)

        # Domain-specific causal templates
        self.templates: Dict[str, Dict] = {}

        # Statistics
        self.queries_answered = 0
        self.counterfactuals_evaluated = 0

    def add_variable(self, name: str,
                    domain: str = "continuous",
                    exogenous: bool = False) -> None:
        """Add a variable to the world model"""
        var = CausalVariable(name=name, domain=domain, exogenous=exogenous)
        self.scm.add_variable(var)

    def add_cause(self, cause: str, effect: str,
                 strength: float = 1.0,
                 functional_form: str = None) -> None:
        """Add causal relationship"""
        # Ensure variables exist
        if cause not in self.scm.variables:
            self.add_variable(cause)
        if effect not in self.scm.variables:
            self.add_variable(effect)

        mechanism = CausalMechanism(
            effect=effect,
            causes=[cause],
            strength=strength,
            functional_form=functional_form
        )
        self.scm.add_mechanism(mechanism)

    def query_causal_effect(self, treatment: str,
                           outcome: str,
                           adjustment: Set[str] = None) -> CausalQuery:
        """
        Query causal effect of treatment on outcome.

        Args:
            treatment: Treatment variable
            outcome: Outcome variable
            adjustment: Variables to adjust for

        Returns:
            CausalQuery with identification result
        """
        self.queries_answered += 1

        # Check identifiability
        if adjustment is None:
            adjustment = self.scm.graph.find_adjustment_set(treatment, outcome)

        query = CausalQuery(
            query_type="identification",
            target=outcome,
            interventions=[Intervention(treatment, None, InterventionType.DO)]
        )

        if adjustment is not None:
            query.identifiable = True
            query.formula = f"E[{outcome} | do({treatment}=t)] = " \
                           f"Sum over {adjustment} of P({outcome}|{treatment},{adjustment})*P({adjustment})"
        else:
            query.identifiable = False

        return query

    def compute_counterfactual(self, factual: Dict[str, Any],
                              intervention_var: str,
                              intervention_value: Any,
                              query_var: str) -> Counterfactual:
        """
        Compute counterfactual.

        Args:
            factual: What actually happened
            intervention_var: What to intervene on
            intervention_value: Value to set
            query_var: What to query

        Returns:
            Evaluated counterfactual
        """
        self.counterfactuals_evaluated += 1

        cf = Counterfactual(
            factual=factual,
            intervention=Intervention(intervention_var, intervention_value),
            query_variable=query_var
        )

        return self.counterfactual_reasoner.evaluate(cf)

    def answer_causal_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a causal question in natural language.

        Supports patterns:
        - "What causes X?"
        - "Does X cause Y?"
        - "What would happen if X?"
        - "What is the effect of X on Y?"
        """
        q_lower = question.lower()

        # "What causes X?"
        match = re.search(r'what\s+causes?\s+(\w+)', q_lower)
        if match:
            var = match.group(1)
            causes = self.scm.graph.parents(var)
            return {
                'question_type': 'causes_of',
                'variable': var,
                'causes': list(causes),
                'answer': f"The causes of {var} are: {', '.join(causes) or 'unknown'}"
            }

        # "Does X cause Y?"
        match = re.search(r'does\s+(\w+)\s+cause\s+(\w+)', q_lower)
        if match:
            x, y = match.group(1), match.group(2)
            is_cause = y in self.scm.graph.descendants(x)
            return {
                'question_type': 'causal_relation',
                'treatment': x,
                'outcome': y,
                'is_cause': is_cause,
                'answer': f"{'Yes' if is_cause else 'No'}, {x} {'does' if is_cause else 'does not'} cause {y}"
            }

        # "What is the effect of X on Y?"
        match = re.search(r'effect\s+of\s+(\w+)\s+on\s+(\w+)', q_lower)
        if match:
            x, y = match.group(1), match.group(2)
            query = self.query_causal_effect(x, y)
            return {
                'question_type': 'causal_effect',
                'treatment': x,
                'outcome': y,
                'identifiable': query.identifiable,
                'formula': query.formula,
                'answer': f"The causal effect is {'identifiable' if query.identifiable else 'not identifiable'}: {query.formula or 'unknown'}"
            }

        # "What would happen if X?"
        match = re.search(r'what\s+would\s+happen\s+if\s+(\w+)\s*=?\s*(\d+)?', q_lower)
        if match:
            var = match.group(1)
            value = float(match.group(2)) if match.group(2) else 1.0

            descendants = self.scm.graph.descendants(var)
            return {
                'question_type': 'intervention',
                'variable': var,
                'value': value,
                'affected': list(descendants),
                'answer': f"If {var}={value}, then these variables would be affected: {', '.join(descendants) or 'none'}"
            }

        return {
            'question_type': 'unknown',
            'answer': "Could not parse causal question"
        }

    def load_template(self, domain: str) -> None:
        """Load domain-specific causal template"""
        if domain == "epidemiology":
            self.add_variable("exposure", "binary")
            self.add_variable("outcome", "binary")
            self.add_variable("confounder", "continuous")
            self.add_cause("confounder", "exposure")
            self.add_cause("confounder", "outcome")
            self.add_cause("exposure", "outcome")

        elif domain == "economics":
            self.add_variable("supply", "continuous")
            self.add_variable("demand", "continuous")
            self.add_variable("price", "continuous")
            self.add_cause("supply", "price", strength=-1.0)
            self.add_cause("demand", "price", strength=1.0)

        elif domain == "physics":
            self.add_variable("force", "continuous")
            self.add_variable("mass", "continuous")
            self.add_variable("acceleration", "continuous")
            self.add_cause("force", "acceleration")
            self.add_cause("mass", "acceleration", strength=-1.0)

        self.templates[domain] = {'loaded': True}

    def get_stats(self) -> Dict:
        """Get model statistics"""
        return {
            'variables': len(self.scm.variables),
            'mechanisms': len(self.scm.mechanisms),
            'queries_answered': self.queries_answered,
            'counterfactuals_evaluated': self.counterfactuals_evaluated
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'CausalWorldModel',
    'CausalMechanism',
    'CausalVariable',
    'CausalRelationType',
    'Intervention',
    'InterventionType',
    'Counterfactual',
    'CausalQuery',
    'CausalGraph',
    'StructuralCausalModel',
    'CounterfactualReasoner',
]


