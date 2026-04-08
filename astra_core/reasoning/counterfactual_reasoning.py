"""
Counterfactual & Interventional Reasoning for STAN V41

Enables "what if" analysis using causal models:
- Counterfactual outcome prediction
- Do-calculus for interventional reasoning
- Contrastive explanations ("Why Y rather than Z?")
- Causal effect estimation
- Intervention planning

Date: 2025-12-11
Version: 41.0
"""

import time
import uuid
import math
import copy
from typing import Dict, List, Optional, Any, Tuple, Set, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# Try relative imports first, fall back to absolute imports for dynamic loading
try:
    from .unified_world_model import (
        UnifiedWorldModel, CausalGraph, CausalEdge,
        Hypothesis, Evidence, EvidenceSource, get_world_model
    )
except ImportError:
    try:
        from astra_core.reasoning.unified_world_model import (
            UnifiedWorldModel, CausalGraph, CausalEdge,
            Hypothesis, Evidence, EvidenceSource, get_world_model
        )
    except ImportError:
        # Last resort: try direct import
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        import unified_world_model
        UnifiedWorldModel = unified_world_model.UnifiedWorldModel
        CausalGraph = unified_world_model.CausalGraph
        CausalEdge = unified_world_model.CausalEdge
        Hypothesis = unified_world_model.Hypothesis
        Evidence = unified_world_model.Evidence
        EvidenceSource = unified_world_model.EvidenceSource
        get_world_model = unified_world_model.get_world_model

# Try to import integration bus, fall back to stub if not available
try:
    from .integration_bus import IntegrationBus, EventType, get_integration_bus
except ImportError:
    try:
        from astra_core.reasoning.integration_bus import IntegrationBus, EventType, get_integration_bus
    except ImportError:
        try:
            from .integration_bus_stub import IntegrationBus, EventType, get_integration_bus
        except ImportError:
            try:
                from astra_core.reasoning.integration_bus_stub import IntegrationBus, EventType, get_integration_bus
            except ImportError:
                # Last resort: direct import
                import sys
                import os
                sys.path.insert(0, os.path.dirname(__file__))
                import integration_bus_stub
                IntegrationBus = integration_bus_stub.IntegrationBus
                EventType = integration_bus_stub.EventType
                get_integration_bus = integration_bus_stub.get_integration_bus


class InterventionType(Enum):
    """Types of interventions"""
    DO = "do"  # do(X=x) - force variable to value
    OBSERVE = "observe"  # condition on observation
    SOFT = "soft"  # soft intervention (shift distribution)
    COUNTERFACTUAL = "counterfactual"  # what would have happened


class QueryType(Enum):
    """Types of causal queries"""
    ASSOCIATION = "association"  # P(Y|X)
    INTERVENTION = "intervention"  # P(Y|do(X))
    COUNTERFACTUAL = "counterfactual"  # P(Y_x|X', Y')


@dataclass
class Intervention:
    """Represents an intervention on a variable"""
    variable: str
    value: Any
    intervention_type: InterventionType = InterventionType.DO
    strength: float = 1.0  # For soft interventions
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CounterfactualQuery:
    """A counterfactual query"""
    query_id: str
    factual_world: Dict[str, Any]  # What actually happened
    hypothetical_intervention: Intervention  # What we're asking about
    target_variable: str  # What we want to know
    query_type: QueryType = QueryType.COUNTERFACTUAL

    def __post_init__(self):
        if not self.query_id:
            self.query_id = f"cf_{uuid.uuid4().hex[:8]}"


@dataclass
class CounterfactualResult:
    """Result of counterfactual reasoning"""
    query_id: str
    factual_outcome: Any
    counterfactual_outcome: Any
    probability: float
    confidence: float
    explanation: str
    causal_path: List[str]
    assumptions: List[str]
    sensitivity: Dict[str, float] = field(default_factory=dict)


@dataclass
class ContrastiveExplanation:
    """Explanation of why Y rather than Z"""
    fact: str  # What happened (Y)
    foil: str  # What didn't happen (Z)
    explanation: str  # Why Y and not Z
    causal_factors: List[str]
    counterfactual_conditions: List[str]  # What would need to change for Z
    confidence: float


@dataclass
class CausalEffect:
    """Estimated causal effect"""
    cause: str
    effect: str
    effect_size: float  # -1 to 1
    confidence: float
    effect_type: str  # "direct", "indirect", "total"
    mediators: List[str] = field(default_factory=list)
    confounders: List[str] = field(default_factory=list)
    bounds: Tuple[float, float] = (0.0, 0.0)


class StructuralCausalModel:
    """
    Structural Causal Model for counterfactual reasoning.

    Represents causal relationships as structural equations:
    Y = f(Pa(Y), U_Y)

    where Pa(Y) are parents of Y and U_Y is exogenous noise.
    """

    def __init__(self, causal_graph: CausalGraph):
        self.graph = causal_graph
        self.equations: Dict[str, Callable] = {}
        self.exogenous: Dict[str, Any] = {}
        self.variable_values: Dict[str, Any] = {}

    def set_equation(self, variable: str, equation: Callable):
        """
        Set structural equation for a variable.

        equation: Function(parents_dict, exogenous) -> value
        """
        self.equations[variable] = equation

    def set_exogenous(self, variable: str, value: Any):
        """Set exogenous noise term for a variable"""
        self.exogenous[variable] = value

    def intervene(self, intervention: Intervention) -> 'StructuralCausalModel':
        """
        Apply intervention and return modified SCM.

        do(X=x) removes incoming edges to X and sets X=x.
        """
        # Create copy
        new_scm = StructuralCausalModel(copy.deepcopy(self.graph))
        new_scm.equations = dict(self.equations)
        new_scm.exogenous = dict(self.exogenous)
        new_scm.variable_values = dict(self.variable_values)

        if intervention.intervention_type == InterventionType.DO:
            # Remove incoming edges (make X exogenous)
            new_scm.equations[intervention.variable] = lambda p, u, v=intervention.value: v
            new_scm.variable_values[intervention.variable] = intervention.value

        elif intervention.intervention_type == InterventionType.SOFT:
            # Soft intervention - modify but don't replace equation
            if intervention.variable in new_scm.equations:
                original_eq = new_scm.equations[intervention.variable]
                strength = intervention.strength
                target = intervention.value

                def soft_eq(p, u, orig=original_eq, s=strength, t=target):
                    original_val = orig(p, u)
                    return (1 - s) * original_val + s * t

                new_scm.equations[intervention.variable] = soft_eq

        return new_scm

    def compute(self, target: str, evidence: Optional[Dict[str, Any]] = None) -> Any:
        """
        Compute value of target variable given evidence.

        Uses topological order to resolve dependencies.
        """
        evidence = evidence or {}
        computed = dict(evidence)
        computed.update(self.variable_values)

        # Topological sort
        order = self._topological_sort()

        for var in order:
            if var in computed:
                continue

            if var in self.equations:
                # Get parent values
                parents = self.graph.get_parents(var)
                parent_values = {p: computed.get(p, 0) for p in parents}

                # Compute
                exog = self.exogenous.get(var, 0)
                computed[var] = self.equations[var](parent_values, exog)
            else:
                computed[var] = self.exogenous.get(var, 0)

        return computed.get(target)

    def _topological_sort(self) -> List[str]:
        """Topological sort of variables"""
        in_degree = {n: 0 for n in self.graph.nodes}

        for node in self.graph.nodes:
            for child in self.graph.get_children(node):
                in_degree[child] = in_degree.get(child, 0) + 1

        queue = [n for n in self.graph.nodes if in_degree.get(n, 0) == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for child in self.graph.get_children(node):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        return result


class CounterfactualEngine:
    """
    Engine for counterfactual reasoning.

    Implements the three-step counterfactual procedure:
    1. Abduction: Infer exogenous variables from evidence
    2. Action: Apply intervention to SCM
    3. Prediction: Compute outcome in modified SCM
    """

    def __init__(self,
                 world_model: Optional[UnifiedWorldModel] = None,
                 bus: Optional[IntegrationBus] = None):
        self.world_model = world_model or get_world_model()
        self.bus = bus or get_integration_bus()

        # Cache of SCMs
        self.scm_cache: Dict[str, StructuralCausalModel] = {}

    def query_counterfactual(self, query: CounterfactualQuery) -> CounterfactualResult:
        """
        Answer a counterfactual query.

        "What would Y have been if we had done X=x, given that
        we actually observed X=x' and Y=y'?"
        """
        # Step 1: Build or retrieve SCM
        scm = self._get_or_build_scm()

        # Step 2: Abduction - infer exogenous variables from factual world
        exogenous = self._abduct_exogenous(scm, query.factual_world)

        # Update SCM with inferred exogenous
        for var, val in exogenous.items():
            scm.set_exogenous(var, val)

        # Step 3: Action - apply intervention
        modified_scm = scm.intervene(query.hypothetical_intervention)

        # Step 4: Prediction - compute counterfactual outcome
        counterfactual_outcome = modified_scm.compute(
            query.target_variable,
            query.factual_world
        )

        # Get factual outcome
        factual_outcome = query.factual_world.get(query.target_variable)

        # Find causal path
        causal_path = self._find_causal_path(
            query.hypothetical_intervention.variable,
            query.target_variable
        )

        # Calculate confidence
        confidence = self._calculate_confidence(query, causal_path)

        # Generate explanation
        explanation = self._generate_explanation(
            query, factual_outcome, counterfactual_outcome, causal_path
        )

        result = CounterfactualResult(
            query_id=query.query_id,
            factual_outcome=factual_outcome,
            counterfactual_outcome=counterfactual_outcome,
            probability=confidence,
            confidence=confidence,
            explanation=explanation,
            causal_path=causal_path,
            assumptions=self._list_assumptions(query)
        )

        # Publish result
        self.bus.publish(
            EventType.REASONING_STEP_COMPLETED,
            "counterfactual_engine",
            {
                'query_type': 'counterfactual',
                'result': explanation,
                'confidence': confidence
            }
        )

        return result

    def estimate_causal_effect(self,
                               cause: str,
                               effect: str,
                               effect_type: str = "total") -> CausalEffect:
        """
        Estimate the causal effect of cause on effect.

        Args:
            cause: Cause variable
            effect: Effect variable
            effect_type: "direct", "indirect", or "total"

        Returns:
            CausalEffect with estimated effect size
        """
        scm = self._get_or_build_scm()

        # Find path
        if not self.world_model.has_causal_path(cause, effect):
            return CausalEffect(
                cause=cause,
                effect=effect,
                effect_size=0.0,
                confidence=0.9,
                effect_type=effect_type,
                bounds=(0.0, 0.0)
            )

        # Estimate effect using intervention
        # E[Y|do(X=1)] - E[Y|do(X=0)]

        # Intervene X=1
        intervention_1 = Intervention(cause, 1.0, InterventionType.DO)
        scm_1 = scm.intervene(intervention_1)
        outcome_1 = scm_1.compute(effect) or 0

        # Intervene X=0
        intervention_0 = Intervention(cause, 0.0, InterventionType.DO)
        scm_0 = scm.intervene(intervention_0)
        outcome_0 = scm_0.compute(effect) or 0

        effect_size = outcome_1 - outcome_0

        # Find mediators and confounders
        mediators = self._find_mediators(cause, effect)
        confounders = self._find_confounders(cause, effect)

        # Calculate confidence based on graph structure
        confidence = self._calculate_effect_confidence(cause, effect, confounders)

        return CausalEffect(
            cause=cause,
            effect=effect,
            effect_size=effect_size,
            confidence=confidence,
            effect_type=effect_type,
            mediators=mediators,
            confounders=confounders,
            bounds=(effect_size - 0.1, effect_size + 0.1)  # Simple bounds
        )

    def generate_contrastive_explanation(self,
                                         fact: str,
                                         fact_value: Any,
                                         foil: str,
                                         foil_value: Any,
                                         context: Dict[str, Any]) -> ContrastiveExplanation:
        """
        Generate explanation for why fact rather than foil.

        "Why did Y=y happen rather than Y=y'?"
        """
        scm = self._get_or_build_scm()

        # Find what would need to change for foil to occur
        counterfactual_conditions = []
        causal_factors = []

        # Get parents of the outcome
        parents = self.world_model.get_causal_parents(fact)

        for parent in parents:
            # Check if changing parent would change outcome
            current_value = context.get(parent, 0)

            # Try different values
            for test_value in [0, 1, current_value * 0.5, current_value * 2]:
                if test_value == current_value:
                    continue

                intervention = Intervention(parent, test_value, InterventionType.DO)
                modified_scm = scm.intervene(intervention)
                outcome = modified_scm.compute(fact, context)

                if outcome == foil_value:
                    counterfactual_conditions.append(
                        f"If {parent} had been {test_value} instead of {current_value}"
                    )
                    causal_factors.append(parent)
                    break

        # Generate explanation
        if causal_factors:
            explanation = (
                f"{fact}={fact_value} occurred rather than {foil}={foil_value} because "
                f"the causal factors {', '.join(causal_factors)} had their actual values. "
                f"For {foil}={foil_value} to occur, {' or '.join(counterfactual_conditions)}."
            )
        else:
            explanation = (
                f"{fact}={fact_value} occurred rather than {foil}={foil_value}. "
                f"No single-factor counterfactual change identified."
            )

        confidence = 0.7 if causal_factors else 0.3

        return ContrastiveExplanation(
            fact=f"{fact}={fact_value}",
            foil=f"{foil}={foil_value}",
            explanation=explanation,
            causal_factors=causal_factors,
            counterfactual_conditions=counterfactual_conditions,
            confidence=confidence
        )

    def what_if(self,
                intervention: Intervention,
                targets: List[str],
                current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple "what if" analysis.

        Args:
            intervention: What to change
            targets: Variables to predict
            current_state: Current values

        Returns:
            Predicted values for targets
        """
        scm = self._get_or_build_scm()

        # Abduct exogenous
        exogenous = self._abduct_exogenous(scm, current_state)
        for var, val in exogenous.items():
            scm.set_exogenous(var, val)

        # Apply intervention
        modified_scm = scm.intervene(intervention)

        # Compute targets
        results = {}
        for target in targets:
            results[target] = modified_scm.compute(target, current_state)

        return results

    def identify_necessary_causes(self,
                                   effect_variable: str,
                                   effect_value: Any,
                                   context: Dict[str, Any]) -> List[Tuple[str, float]]:
        """
        Identify necessary causes for an effect.

        A cause C is necessary for E if:
        P(E would not have occurred | C did not occur) is high
        """
        necessary_causes = []
        scm = self._get_or_build_scm()

        # Get all ancestors of effect
        potential_causes = list(self.world_model.causal_graph.get_ancestors(effect_variable))

        for cause in potential_causes:
            if cause not in context:
                continue

            # Counterfactual: what if cause hadn't occurred?
            original_value = context[cause]

            # Define "not occurred" - typically negation or zero
            if isinstance(original_value, bool):
                counterfactual_value = not original_value
            elif isinstance(original_value, (int, float)):
                counterfactual_value = 0
            else:
                continue

            # Create counterfactual query
            intervention = Intervention(cause, counterfactual_value, InterventionType.DO)

            # Abduct and intervene
            exogenous = self._abduct_exogenous(scm, context)
            for var, val in exogenous.items():
                scm.set_exogenous(var, val)

            modified_scm = scm.intervene(intervention)
            counterfactual_outcome = modified_scm.compute(effect_variable, context)

            # Check if outcome would be different
            if counterfactual_outcome != effect_value:
                # Calculate probability of necessity
                pn = 0.8  # Simplified - would use proper probability calculation
                necessary_causes.append((cause, pn))

        # Sort by probability of necessity
        necessary_causes.sort(key=lambda x: x[1], reverse=True)

        return necessary_causes

    def identify_sufficient_causes(self,
                                    effect_variable: str,
                                    effect_value: Any,
                                    context: Dict[str, Any]) -> List[Tuple[str, float]]:
        """
        Identify sufficient causes for an effect.

        A cause C is sufficient for E if:
        P(E would have occurred | C occurred) is high
        """
        sufficient_causes = []
        scm = self._get_or_build_scm()

        potential_causes = list(self.world_model.causal_graph.get_ancestors(effect_variable))

        for cause in potential_causes:
            if cause not in context:
                continue

            # Check if this cause alone is sufficient
            # Set all other causes to neutral/zero and see if effect still occurs

            intervention = Intervention(cause, context[cause], InterventionType.DO)
            modified_scm = scm.intervene(intervention)

            # Zero out other causes
            modified_context = {cause: context[cause]}
            outcome = modified_scm.compute(effect_variable, modified_context)

            if outcome == effect_value:
                ps = 0.7  # Simplified probability of sufficiency
                sufficient_causes.append((cause, ps))

        sufficient_causes.sort(key=lambda x: x[1], reverse=True)

        return sufficient_causes

    def _get_or_build_scm(self) -> StructuralCausalModel:
        """Get or build structural causal model from world model"""
        # Use cached if available
        cache_key = f"scm_{self.world_model.update_count}"
        if cache_key in self.scm_cache:
            return self.scm_cache[cache_key]

        # Build from causal graph
        scm = StructuralCausalModel(self.world_model.causal_graph)

        # Create default linear equations for each variable
        for node in self.world_model.causal_graph.nodes:
            parents = self.world_model.causal_graph.get_parents(node)

            if parents:
                # Linear combination of parents plus noise
                def make_equation(ps):
                    def eq(parent_vals, exog):
                        return sum(parent_vals.get(p, 0) * 0.5 for p in ps) + exog
                    return eq

                scm.set_equation(node, make_equation(parents))
            else:
                # Exogenous variable
                scm.set_equation(node, lambda p, u: u)

        self.scm_cache[cache_key] = scm
        return scm

    def _abduct_exogenous(self, scm: StructuralCausalModel,
                          observations: Dict[str, Any]) -> Dict[str, Any]:
        """Infer exogenous variables from observations"""
        exogenous = {}

        for var, observed in observations.items():
            if var not in scm.graph.nodes:
                continue

            parents = scm.graph.get_parents(var)

            if not parents:
                # Root node - exogenous is the observed value
                exogenous[var] = observed
            else:
                # Compute expected value from parents
                parent_vals = {p: observations.get(p, 0) for p in parents}

                if var in scm.equations:
                    expected = scm.equations[var](parent_vals, 0)
                    # Exogenous is residual
                    exogenous[var] = observed - expected if isinstance(observed, (int, float)) else 0
                else:
                    exogenous[var] = 0

        return exogenous

    def _find_causal_path(self, source: str, target: str) -> List[str]:
        """Find causal path from source to target"""
        if source == target:
            return [source]

        # BFS for shortest path
        visited = {source}
        queue = [(source, [source])]

        while queue:
            current, path = queue.pop(0)

            for child in self.world_model.causal_graph.get_children(current):
                if child == target:
                    return path + [child]

                if child not in visited:
                    visited.add(child)
                    queue.append((child, path + [child]))

        return []

    def _find_mediators(self, cause: str, effect: str) -> List[str]:
        """Find mediating variables between cause and effect"""
        path = self._find_causal_path(cause, effect)
        return path[1:-1] if len(path) > 2 else []

    def _find_confounders(self, cause: str, effect: str) -> List[str]:
        """Find confounding variables"""
        # Common parents of cause and effect
        cause_ancestors = self.world_model.causal_graph.get_ancestors(cause)
        effect_ancestors = self.world_model.causal_graph.get_ancestors(effect)
        return list(cause_ancestors.intersection(effect_ancestors))

    def _calculate_confidence(self, query: CounterfactualQuery,
                              causal_path: List[str]) -> float:
        """Calculate confidence in counterfactual result"""
        if not causal_path:
            return 0.3

        # Base confidence from path length (shorter = more confident)
        path_confidence = 1.0 / (1 + 0.1 * len(causal_path))

        # Adjust for edge confidences
        edge_confidence = 1.0
        for i in range(len(causal_path) - 1):
            edge = self.world_model.causal_graph.get_edge_between(
                causal_path[i], causal_path[i+1]
            )
            if edge:
                edge_confidence *= edge.confidence

        return path_confidence * edge_confidence

    def _calculate_effect_confidence(self, cause: str, effect: str,
                                      confounders: List[str]) -> float:
        """Calculate confidence in causal effect estimate"""
        base = 0.8

        # Reduce for confounders
        base -= 0.1 * len(confounders)

        # Check edge confidence
        edge = self.world_model.causal_graph.get_edge_between(cause, effect)
        if edge:
            base = base * edge.confidence

        return max(0.2, min(0.95, base))

    def _generate_explanation(self, query: CounterfactualQuery,
                              factual: Any, counterfactual: Any,
                              causal_path: List[str]) -> str:
        """Generate human-readable explanation"""
        intervention = query.hypothetical_intervention

        if factual == counterfactual:
            return (
                f"If {intervention.variable} had been {intervention.value} "
                f"instead of its actual value, {query.target_variable} would "
                f"likely have remained {factual}."
            )
        else:
            path_str = " → ".join(causal_path) if causal_path else "unknown path"
            return (
                f"If {intervention.variable} had been {intervention.value}, "
                f"{query.target_variable} would have been {counterfactual} "
                f"instead of {factual}. Causal mechanism: {path_str}."
            )

    def _list_assumptions(self, query: CounterfactualQuery) -> List[str]:
        """List assumptions made in counterfactual reasoning"""
        return [
            "Causal graph is correctly specified",
            "No unmeasured confounders",
            "Structural equations are approximately linear",
            "Exogenous variables are independent",
            f"Intervention on {query.hypothetical_intervention.variable} does not affect exogenous factors"
        ]


# Export
__all__ = [
    'CounterfactualEngine',
    'CounterfactualQuery',
    'CounterfactualResult',
    'ContrastiveExplanation',
    'CausalEffect',
    'Intervention',
    'InterventionType',
    'QueryType',
    'StructuralCausalModel'
]
