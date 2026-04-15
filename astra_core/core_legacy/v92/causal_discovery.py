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
Causal Discovery Engine for V92
================================

Automated discovery of causal relationships from data.
This module implements state-of-the-art causal discovery algorithms
and causal inference methods for scientific reasoning.

Capabilities:
- Discover causal structure from observational data
- Distinguish correlation from causation
- Intervention reasoning (counterfactuals)
- Causal effect estimation
- Temporal causal discovery
- Confounder detection
- Mediation analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import time
import json
from collections import defaultdict
import networkx as nx
from abc import ABC, abstractmethod
import itertools


class CausalRelationshipType(Enum):
    """Types of causal relationships"""
    DIRECT = "direct"                    # X → Y
    INDIRECT = "indirect"               # X → Z → Y
    CONFOUNDING = "confounding"         # X ← Z → Y
    COLLIDER = "collider"               # X → Z ← Y
    MEDIATION = "mediation"             # X → Z → Y (Z is mediator)
    MODERATION = "moderation"           # Effect of X on Y depends on Z
    FEEDBACK = "feedback"               # X ↔ Y (bidirectional)


class DiscoveryMethod(Enum):
    """Causal discovery methods"""
    PC = "pc"                           # Peter-Clark algorithm
    GES = "ges"                         # Greedy Equivalence Search
    FCIT = "fcit"                       # Fast Conditional Independence Test
    NOTEARS = "notears"                 # Non-combinatorial approach
    LINGAM = "lingam"                   # Linear Non-Gaussian Model
    CBN = "cbn"                         # Continuous Bayesian Network
    ANM = "anm"                         # Additive Noise Model


class InterventionType(Enum):
    """Types of interventions"""
    PERFECT = "perfect"                 # Ideal intervention
    IMPERFECT = "imperfect"             # Noisy intervention
    CONDITIONAL = "conditional"         # Intervention depends on other variables
    STOCHASTIC = "stochastic"           # Randomized intervention
    SOFT = "soft"                       # Partial/dosage intervention


@dataclass
class CausalRelation:
    """Represents a causal relationship"""
    cause: str
    effect: str
    relationship_type: CausalRelationshipType
    strength: float = 0.0
    confidence: float = 0.0
    method: DiscoveryMethod = DiscoveryMethod.PC
    evidence: Dict[str, Any] = field(default_factory=dict)
    time_lag: int = 0  # For temporal causal discovery
    conditions: List[str] = field(default_factory=list)  # Conditional causality
    created_at: float = field(default_factory=time.time)


@dataclass
class CausalModel:
    """A complete causal model"""
    variables: Set[str] = field(default_factory=set)
    edges: List[CausalRelation] = field(default_factory=list)
    method: DiscoveryMethod = DiscoveryMethod.PC
    confidence: float = 0.0
    data_fitted: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass
class Intervention:
    """Represents a causal intervention"""
    target: str
    intervention_type: InterventionType
    value: Any
    conditions: Dict[str, Any] = field(default_factory=dict)
    expected_effects: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class Counterfactual:
    """Represents a counterfactual query"""
    variable: str
    factual_value: Any
    counterfactual_value: Any
    outcome: str
    estimated_result: Any
    confidence: float = 0.0


class CausalDiscoveryEngine:
    """
    Automated causal discovery from data.

    This module implements multiple causal discovery algorithms
    and provides tools for causal inference and reasoning.
    """

    def __init__(self):
        self.discovery_methods = {
            DiscoveryMethod.PC: PCAlgorithm(),
            DiscoveryMethod.GES: GESAlgorithm(),
            DiscoveryMethod.FCIT: FCITAlgorithm(),
            DiscoveryMethod.LINGAM: LiNGAMAlgorithm(),
            DiscoveryMethod.ANM: ANMAlgorithm()
        }

        self.inference_methods = {
            'do_calculus': DoCalculus(),
            'backdoor_adjustment': BackdoorAdjustment(),
            'frontdoor_adjustment': FrontdoorAdjustment(),
            'instrumental_variables': InstrumentalVariable()
        }

        self.discovered_models = {}
        self.causal_assumptions = {}

    def discover_causal_structure(self,
                                data: pd.DataFrame,
                                method: DiscoveryMethod = DiscoveryMethod.PC,
                                assumptions: Optional[Dict[str, Any]] = None) -> CausalModel:
        """Discover causal structure from observational data"""
        print(f"Discovering causal structure using {method.value} method...")

        # Apply discovery algorithm
        discovery_algo = self.discovery_methods[method]
        causal_model = discovery_algo.discover(data, assumptions)

        # Validate and score model
        score = self._validate_model(causal_model, data)
        causal_model.confidence = score

        # Store model
        model_id = f"model_{int(time.time())}_{method.value}"
        self.discovered_models[model_id] = causal_model

        return causal_model

    def test_causal_relation(self,
                           data: pd.DataFrame,
                           cause: str,
                           effect: str,
                           method: DiscoveryMethod = DiscoveryMethod.PC) -> Optional[CausalRelation]:
        """Test specific causal relationship"""
        # Focus on subset of variables
        subset_data = data[[cause, effect]].copy()

        # Add potential confounders (simplified)
        other_vars = [col for col in data.columns if col not in [cause, effect]]
        for confounder in other_vars[:3]:  # Limit to first 3 potential confounders
            subset_data[confounder] = data[confounder]

        causal_model = self.discover_causal_structure(subset_data, method)

        # Find relationship between cause and effect
        for edge in causal_model.edges:
            if (edge.cause == cause and edge.effect == effect) or \
               (edge.cause == effect and edge.effect == cause):
                return edge

        return None

    def estimate_causal_effect(self,
                             model: CausalModel,
                             data: pd.DataFrame,
                             treatment: str,
                             outcome: str,
                             adjustment_set: Optional[List[str]] = None) -> Dict[str, Any]:
        """Estimate causal effect using appropriate method"""
        # Determine appropriate adjustment set if not provided
        if adjustment_set is None:
            adjustment_set = self._find_adjustment_set(model, treatment, outcome)

        # Choose estimation method
        if adjustment_set:
            effect = self.inference_methods['backdoor_adjustment'].estimate(
                data, treatment, outcome, adjustment_set
            )
        else:
            # Try frontdoor or instrumental variable
            effect = self._estimate_without_backdoor(model, data, treatment, outcome)

        return {
            'treatment': treatment,
            'outcome': outcome,
            'estimated_effect': effect['effect'],
            'confidence_interval': effect['confidence_interval'],
            'method': effect['method'],
            'adjustment_set': adjustment_set
        }

    def compute_counterfactual(self,
                             model: CausalModel,
                             data: pd.DataFrame,
                             query: Dict[str, Any]) -> Counterfactual:
        """Compute counterfactual query"""
        variable = query['variable']
        factual_value = query['factual']
        counterfactual_value = query['counterfactual']
        outcome = query['outcome']

        # Use causal model to estimate counterfactual
        do_calc = self.inference_methods['do_calculus']
        result = do_calc.counterfactual(model, data, query)

        return Counterfactual(
            variable=variable,
            factual_value=factual_value,
            counterfactual_value=counterfactual_value,
            outcome=outcome,
            estimated_result=result['value'],
            confidence=result['confidence']
        )

    def design_intervention(self,
                          model: CausalModel,
                          target: str,
                          goal: Dict[str, Any]) -> Intervention:
        """Design optimal intervention to achieve goal"""
        # Analyze causal paths to goal
        paths = self._find_causal_paths(model, target, goal['variable'])

        # Estimate intervention effects
        intervention_strength = self._calculate_optimal_intervention(
            model, paths, goal
        )

        return Intervention(
            target=target,
            intervention_type=InterventionType.PERFECT,
            value=intervention_strength,
            expected_effects=goal,
            confidence=0.7
        )

    def detect_confounders(self,
                         model: CausalModel,
                         treatment: str,
                         outcome: str) -> List[str]:
        """Detect potential confounders"""
        confounders = []

        for edge in model.edges:
            # Look for common causes (confounders)
            if edge.relationship_type == CausalRelationshipType.CONFOUNDING:
                if edge.cause == treatment or edge.effect == treatment:
                    if edge.cause == outcome or edge.effect == outcome:
                        # Find the confounding variable
                        other_vars = set([edge.cause, edge.effect]) - {treatment, outcome}
                        confounders.extend(other_vars)

        return list(set(confounders))

    def find_mediators(self,
                      model: CausalModel,
                      treatment: str,
                      outcome: str) -> List[str]:
        """Find mediating variables"""
        mediators = []

        for edge in model.edges:
            if edge.cause == treatment and edge.effect != outcome:
                # Check if this leads to outcome
                if self._has_path(model, edge.effect, outcome):
                    mediators.append(edge.effect)

        return mediators

    def simulate_intervention(self,
                            model: CausalModel,
                            intervention: Intervention,
                            data: pd.DataFrame) -> pd.DataFrame:
        """Simulate effects of intervention"""
        modified_data = data.copy()

        if intervention.intervention_type == InterventionType.PERFECT:
            # Perfect intervention: set variable to intervention value
            modified_data[intervention.target] = intervention.value
        elif intervention.intervention_type == InterventionType.STOCHASTIC:
            # Stochastic intervention: modify probabilities
            modified_data[intervention.target] = np.random.normal(
                intervention.value, 0.1, len(modified_data)
            )
        elif intervention.intervention_type == InterventionType.SOFT:
            # Soft intervention: shift distribution
            current_values = modified_data[intervention.target].values
            modified_data[intervention.target] = current_values * 0.7 + intervention.value * 0.3

        # Propagate effects through causal model
        modified_data = self._propagate_effects(model, intervention, modified_data)

        return modified_data

    def validate_causal_discovery(self,
                                model: CausalModel,
                                test_data: pd.DataFrame) -> Dict[str, Any]:
        """Validate discovered causal model"""
        validation_results = {
            'structure_score': 0.0,
            'predictive_score': 0.0,
            'independence_violations': [],
            'cycle_count': 0
        }

        # Check for cycles (should be acyclic for most methods)
        validation_results['cycle_count'] = self._count_cycles(model)

        # Test conditional independencies implied by model
        violations = self._test_conditional_independencies(model, test_data)
        validation_results['independence_violations'] = violations

        # Score based on violations and cycles
        validation_results['structure_score'] = max(0, 1.0 - len(violations) * 0.1 - validation_results['cycle_count'] * 0.2)

        return validation_results

    def _find_adjustment_set(self, model: CausalModel, treatment: str, outcome: str) -> List[str]:
        """Find minimal adjustment set for causal effect estimation"""
        # Simplified backdoor criterion
        adjustment_set = []

        # Find variables that satisfy backdoor criterion
        for var in model.variables:
            if var not in [treatment, outcome]:
                if self._satisfies_backdoor(model, var, treatment, outcome):
                    adjustment_set.append(var)

        return adjustment_set

    def _satisfies_backdoor(self, model: CausalModel, var: str, treatment: str, outcome: str) -> bool:
        """Check if variable satisfies backdoor criterion"""
        # Simplified implementation
        # Variable should not be descendant of treatment
        # Should block backdoor paths
        return var not in self._get_descendants(model, treatment)

    def _get_descendants(self, model: CausalModel, node: str) -> Set[str]:
        """Get all descendants of a node in causal graph"""
        descendants = set()
        for edge in model.edges:
            if edge.cause == node:
                descendants.add(edge.effect)
                descendants.update(self._get_descendants(model, edge.effect))
        return descendants

    def _has_path(self, model: CausalModel, source: str, target: str) -> bool:
        """Check if there's a path from source to target"""
        visited = set()
        return self._dfs_path(model, source, target, visited)

    def _dfs_path(self, model: CausalModel, current: str, target: str, visited: Set[str]) -> bool:
        """DFS to find path"""
        if current == target:
            return True
        if current in visited:
            return False

        visited.add(current)
        for edge in model.edges:
            if edge.cause == current:
                if self._dfs_path(model, edge.effect, target, visited):
                    return True

        return False

    def _find_causal_paths(self, model: CausalModel, source: str, target: str) -> List[List[str]]:
        """Find all causal paths from source to target"""
        paths = []
        self._find_all_paths(model, source, target, [], paths)
        return paths

    def _find_all_paths(self, model: CausalModel, current: str, target: str,
                       path: List[str], all_paths: List[List[str]]):
        """Find all paths using DFS"""
        if current == target:
            all_paths.append(path + [current])
            return

        if current in path:  # Avoid cycles
            return

        for edge in model.edges:
            if edge.cause == current:
                self._find_all_paths(model, edge.effect, target, path + [current], all_paths)

    def _calculate_optimal_intervention(self, model: CausalModel, paths: List[List[str]], goal: Dict[str, Any]) -> float:
        """Calculate optimal intervention strength"""
        # Simplified calculation
        # In practice, would use optimization and causal effect estimation
        base_effect = 0.5
        path_count = len(paths)

        if path_count > 0:
            # Stronger effect if multiple causal paths
            return base_effect * (1 + 0.2 * path_count)
        else:
            return base_effect

    def _propagate_effects(self, model: CausalModel, intervention: Intervention,
                          data: pd.DataFrame) -> pd.DataFrame:
        """Propagate intervention effects through causal model"""
        # Simplified propagation
        # In practice, would use structural equations
        modified_data = data.copy()

        for edge in model.edges:
            if edge.cause == intervention.target:
                # Apply causal effect
                effect_size = edge.strength * (modified_data[intervention.target] - data[intervention.target]).mean()
                modified_data[edge.effect] += effect_size

        return modified_data

    def _validate_model(self, model: CausalModel, data: pd.DataFrame) -> float:
        """Validate causal model against data"""
        # Simplified validation
        score = 0.5  # Base score

        # Bonus for acyclic structure
        if self._count_cycles(model) == 0:
            score += 0.2

        # Bonus for reasonable number of edges
        if len(model.edges) <= len(model.variables) * 2:
            score += 0.1

        return min(1.0, score)

    def _count_cycles(self, model: CausalModel) -> int:
        """Count cycles in causal graph"""
        # Build directed graph
