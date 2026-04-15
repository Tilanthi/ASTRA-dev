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
V50 Causal Discovery & Intervention Engine
===========================================

Move beyond correlational patterns to causal mechanisms.

Level 1 (Current): "X is associated with Y"
Level 2 (Proposed): "X causes Y through mechanism M"
Level 3 (Proposed): "Intervening on X via action A produces effect E on Y"

Components:
1. CausalStructureLearner - Learn causal graphs from data
2. MechanismDiscovery - Identify causal mechanisms
3. InterventionPlanner - Plan interventions to achieve goals
4. CounterfactualReasoner - "What would Y be if X had been different?"
5. CausalInferenceEngine - Unified causal inference

Date: 2025-12-17
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
import random
import math
import time


class CausalRelationType(Enum):
    """Types of causal relationships."""
    DIRECT_CAUSE = "direct_cause"
    INDIRECT_CAUSE = "indirect_cause"
    COMMON_CAUSE = "common_cause"
    COMMON_EFFECT = "common_effect"
    MEDIATOR = "mediator"
    CONFOUNDER = "confounder"
    COLLIDER = "collider"
    INSTRUMENTAL = "instrumental"


class InterventionType(Enum):
    """Types of interventions."""
    DO = "do"  # do(X=x)
    SOFT = "soft"  # Soft intervention
    CONDITIONAL = "conditional"  # Conditional intervention
    COUNTERFACTUAL = "counterfactual"  # Counterfactual intervention


@dataclass
class CausalNode:
    """Node in a causal graph."""
    name: str
    node_type: str = "variable"
    domain: List[Any] = field(default_factory=list)
    observed: bool = True
    exogenous: bool = False
    structural_equation: Optional[Callable] = None


@dataclass
class CausalEdge:
    """Edge in a causal graph."""
    source: str
    target: str
    relation_type: CausalRelationType = CausalRelationType.DIRECT_CAUSE
    strength: float = 1.0
    mechanism: str = ""
    time_lag: float = 0.0
    confidence: float = 1.0


@dataclass
class CausalGraph:
    """Structural Causal Model (SCM)."""
    nodes: Dict[str, CausalNode] = field(default_factory=dict)
    edges: List[CausalEdge] = field(default_factory=list)
    exogenous_distributions: Dict[str, Callable] = field(default_factory=dict)

    def add_node(self, node: CausalNode):
        """Add a node to the graph."""
        self.nodes[node.name] = node

    def add_edge(self, edge: CausalEdge):
        """Add an edge to the graph."""
        self.edges.append(edge)

    def get_parents(self, node_name: str) -> List[str]:
        """Get parent nodes."""
        return [e.source for e in self.edges if e.target == node_name]

    def get_children(self, node_name: str) -> List[str]:
        """Get child nodes."""
        return [e.target for e in self.edges if e.source == node_name]

    def get_ancestors(self, node_name: str) -> Set[str]:
        """Get all ancestors."""
        ancestors = set()
        to_visit = self.get_parents(node_name)
        while to_visit:
            parent = to_visit.pop()
            if parent not in ancestors:
                ancestors.add(parent)
                to_visit.extend(self.get_parents(parent))
        return ancestors

    def get_descendants(self, node_name: str) -> Set[str]:
        """Get all descendants."""
        descendants = set()
        to_visit = self.get_children(node_name)
        while to_visit:
            child = to_visit.pop()
            if child not in descendants:
                descendants.add(child)
                to_visit.extend(self.get_children(child))
        return descendants

    def is_d_separated(self, x: str, y: str, z: Set[str]) -> bool:
        """Check d-separation between X and Y given Z."""
        # Simplified d-separation check
        # In full implementation, use Bayes-Ball algorithm

        # If Z blocks all paths, they are d-separated
        paths = self._find_all_paths(x, y)

        for path in paths:
            blocked = False
            for node in path[1:-1]:  # Intermediate nodes
                if node in z:
                    # Check if this is a collider on this path
                    idx = path.index(node)
                    if idx > 0 and idx < len(path) - 1:
                        # Is it a collider? (both neighbors point to it)
                        prev_edge = self._get_edge(path[idx-1], node)
                        next_edge = self._get_edge(node, path[idx+1])

                        if prev_edge and next_edge:
                            # Both edges point to node = collider
                            if prev_edge.target == node and next_edge.source == node:
                                # Conditioning on collider opens path
                                pass
                            else:
                                blocked = True
                                break
                        else:
                            blocked = True
                            break

            if not blocked:
                return False  # Found an unblocked path

        return True  # All paths blocked

    def _find_all_paths(self, start: str, end: str) -> List[List[str]]:
        """Find all paths between two nodes."""
        paths = []

        def dfs(current: str, target: str, path: List[str], visited: Set[str]):
            if current == target:
                paths.append(path.copy())
                return

            neighbors = set(self.get_parents(current)) | set(self.get_children(current))

            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(neighbor, target, path, visited)
                    path.pop()
                    visited.remove(neighbor)

        visited = {start}
        dfs(start, end, [start], visited)
        return paths

    def _get_edge(self, source: str, target: str) -> Optional[CausalEdge]:
        """Get edge between nodes."""
        for edge in self.edges:
            if edge.source == source and edge.target == target:
                return edge
            if edge.source == target and edge.target == source:
                return edge
        return None


@dataclass
class CausalEffect:
    """Estimated causal effect."""
    cause: str
    effect: str
    effect_size: float
    confidence_interval: Tuple[float, float]
    p_value: float
    mechanism: str
    confounders_adjusted: List[str]
    identification_strategy: str


@dataclass
class Intervention:
    """A causal intervention."""
    variable: str
    value: Any
    intervention_type: InterventionType
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CounterfactualQuery:
    """A counterfactual query."""
    factual_world: Dict[str, Any]
    intervention: Intervention
    query_variable: str
    query: str  # Natural language query


@dataclass
class CounterfactualResult:
    """Result of counterfactual reasoning."""
    query: CounterfactualQuery
    factual_value: Any
    counterfactual_value: Any
    effect: float
    explanation: str
    confidence: float


class CausalStructureLearner:
    """
    Learn causal structure from observational data.

    Methods:
    - Constraint-based (PC algorithm)
    - Score-based (BIC, BGe)
    - Hybrid methods
    - Domain knowledge integration
    """

    def __init__(self):
        self.learned_graphs: Dict[str, CausalGraph] = {}

    def learn_structure(self, data: Dict[str, List[float]],
                        domain_knowledge: Dict[str, Any] = None,
                        method: str = "pc") -> CausalGraph:
        """
        Learn causal structure from data.

        Args:
            data: Dictionary of variable_name -> values
            domain_knowledge: Prior knowledge about causal structure
            method: Learning method (pc, ges, hybrid)

        Returns:
            Learned CausalGraph
        """
        domain_knowledge = domain_knowledge or {}

        if method == "pc":
            return self._pc_algorithm(data, domain_knowledge)
        elif method == "ges":
            return self._ges_algorithm(data, domain_knowledge)
        else:
            return self._hybrid_algorithm(data, domain_knowledge)

    def _pc_algorithm(self, data: Dict[str, List[float]],
                      domain_knowledge: Dict) -> CausalGraph:
        """
        PC (Peter-Clark) algorithm for causal discovery.

        Phase 1: Start with complete undirected graph
        Phase 2: Remove edges based on conditional independence
        Phase 3: Orient edges using v-structures and rules
        """
        variables = list(data.keys())
        n = len(variables)

        # Initialize complete graph
        graph = CausalGraph()
        for var in variables:
            graph.add_node(CausalNode(name=var))

        # Phase 1: Add all edges
        adjacencies = {var: set(variables) - {var} for var in variables}

        # Phase 2: Test conditional independence
        for depth in range(n):
            for x in variables:
                for y in list(adjacencies[x]):
                    if y not in adjacencies[x]:
                        continue

                    # Find conditioning sets
                    neighbors = adjacencies[x] - {y}
                    if len(neighbors) < depth:
                        continue

                    # Test independence given conditioning sets
                    for z_set in self._subsets(neighbors, depth):
                        if self._test_independence(data, x, y, z_set):
                            adjacencies[x].discard(y)
                            adjacencies[y].discard(x)
                            break

        # Phase 3: Orient edges
        # First, find v-structures
        v_structures = self._find_v_structures(adjacencies, data)

        # Create directed edges
        for x in variables:
            for y in adjacencies[x]:
                # Check for v-structure orientation
                is_v_struct = False
                for (a, b, c) in v_structures:
                    if (x == a and y == b) or (x == c and y == b):
                        is_v_struct = True
                        break

                if is_v_struct:
                    # Already oriented by v-structure
                    pass
                else:
                    # Orient based on correlation strength
                    corr = self._correlation(data[x], data[y])
                    if corr > 0:
                        edge = CausalEdge(
                            source=x, target=y,
                            strength=abs(corr),
                            confidence=0.8
                        )
                        # Avoid duplicate edges
                        if not any(e.source == x and e.target == y for e in graph.edges):
                            if not any(e.source == y and e.target == x for e in graph.edges):
                                graph.add_edge(edge)

        # Apply domain knowledge
        self._apply_domain_knowledge(graph, domain_knowledge)

        return graph

    def _ges_algorithm(self, data: Dict[str, List[float]],
                       domain_knowledge: Dict) -> CausalGraph:
        """
        Greedy Equivalence Search algorithm.

        Score-based method that searches over equivalence classes.
        """
        variables = list(data.keys())
        graph = CausalGraph()

        for var in variables:
            graph.add_node(CausalNode(name=var))

        # Forward phase: add edges
        improved = True
        while improved:
            improved = False
            best_score = self._score_graph(graph, data)

            for x in variables:
                for y in variables:
                    if x != y:
                        # Try adding edge
                        test_edge = CausalEdge(source=x, target=y)
                        graph.edges.append(test_edge)
                        new_score = self._score_graph(graph, data)

                        if new_score > best_score:
                            best_score = new_score
                            improved = True
                        else:
                            graph.edges.remove(test_edge)

        # Backward phase: remove edges
        improved = True
        while improved:
            improved = False
            best_score = self._score_graph(graph, data)

            for edge in list(graph.edges):
                graph.edges.remove(edge)
                new_score = self._score_graph(graph, data)

                if new_score > best_score:
                    best_score = new_score
                    improved = True
                else:
                    graph.edges.append(edge)

        return graph

    def _hybrid_algorithm(self, data: Dict[str, List[float]],
                          domain_knowledge: Dict) -> CausalGraph:
        """Hybrid constraint + score-based algorithm."""
        # Use PC for skeleton
        pc_graph = self._pc_algorithm(data, domain_knowledge)

        # Use GES for orientation
        ges_graph = self._ges_algorithm(data, domain_knowledge)

        # Combine: use PC skeleton with GES orientations
        combined = CausalGraph()
        for node in pc_graph.nodes.values():
            combined.add_node(node)

        for edge in pc_graph.edges:
            # Check GES orientation
            for ges_edge in ges_graph.edges:
                if {ges_edge.source, ges_edge.target} == {edge.source, edge.target}:
                    combined.add_edge(ges_edge)
                    break
            else:
                combined.add_edge(edge)

        return combined

    def _test_independence(self, data: Dict[str, List[float]],
                           x: str, y: str, z_set: Set[str]) -> bool:
        """Test conditional independence X ⊥ Y | Z."""
        if not z_set:
            # Marginal independence
            corr = abs(self._correlation(data[x], data[y]))
            return corr < 0.1

        # Partial correlation
        # Simplified: check if correlation reduces when conditioning
        marginal_corr = abs(self._correlation(data[x], data[y]))

        # Residualize X and Y on Z
        x_resid = self._residualize(data[x], [data[z] for z in z_set])
        y_resid = self._residualize(data[y], [data[z] for z in z_set])

        partial_corr = abs(self._correlation(x_resid, y_resid))

        return partial_corr < 0.1

    def _correlation(self, x: List[float], y: List[float]) -> float:
        """Compute Pearson correlation."""
        n = len(x)
        if n < 2:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        var_x = sum((xi - mean_x)**2 for xi in x)
        var_y = sum((yi - mean_y)**2 for yi in y)
        cov_xy = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))

        if var_x == 0 or var_y == 0:
            return 0.0

        return cov_xy / (math.sqrt(var_x) * math.sqrt(var_y))

    def _residualize(self, y: List[float], x_list: List[List[float]]) -> List[float]:
        """Compute residuals of y regressed on x_list."""
        if not x_list:
            return y

        n = len(y)
        # Simple linear regression residuals
        # y = b0 + sum(bi * xi) + residual

        # Use mean-centering approximation
        mean_y = sum(y) / n
        residuals = [yi - mean_y for yi in y]

        for x in x_list:
            mean_x = sum(x) / n
            # Adjust residuals for x
            corr = self._correlation(y, x)
            for i in range(n):
                residuals[i] -= corr * (x[i] - mean_x)

        return residuals

    def _subsets(self, s: Set[str], size: int) -> List[Set[str]]:
        """Generate all subsets of given size."""
        if size == 0:
            return [set()]

        s_list = list(s)
        if size > len(s_list):
            return []

        result = []

        def generate(start: int, current: Set[str]):
            if len(current) == size:
                result.append(current.copy())
                return
            for i in range(start, len(s_list)):
                current.add(s_list[i])
                generate(i + 1, current)
                current.remove(s_list[i])

        generate(0, set())
        return result

    def _find_v_structures(self, adjacencies: Dict[str, Set[str]],
                           data: Dict[str, List[float]]) -> List[Tuple[str, str, str]]:
        """Find v-structures (X -> Z <- Y where X and Y not adjacent)."""
        v_structures = []
        variables = list(adjacencies.keys())

        for z in variables:
            neighbors = list(adjacencies[z])
            for i, x in enumerate(neighbors):
                for y in neighbors[i+1:]:
                    if y not in adjacencies[x]:
                        # X and Y not adjacent, both adjacent to Z
                        # Check if X -> Z <- Y (v-structure)
                        # Using correlation pattern
                        v_structures.append((x, z, y))

        return v_structures

    def _score_graph(self, graph: CausalGraph, data: Dict[str, List[float]]) -> float:
        """Score a graph using BIC."""
        n = len(list(data.values())[0]) if data else 0
        k = len(graph.edges)  # Number of parameters

        # Log-likelihood (simplified)
        log_lik = 0.0
        for var in data:
            parents = graph.get_parents(var)
            if parents:
                parent_data = [data[p] for p in parents if p in data]
                if parent_data:
                    residuals = self._residualize(data[var], parent_data)
                    var_residuals = sum(r**2 for r in residuals) / len(residuals)
                    log_lik -= n * math.log(max(var_residuals, 1e-10)) / 2

        # BIC = log_lik - k/2 * log(n)
        bic = log_lik - k / 2 * math.log(max(n, 1))

        return bic

    def _apply_domain_knowledge(self, graph: CausalGraph, knowledge: Dict):
        """Apply domain knowledge to constrain/orient edges."""
        if 'forbidden_edges' in knowledge:
            for (src, tgt) in knowledge['forbidden_edges']:
                graph.edges = [e for e in graph.edges
                              if not (e.source == src and e.target == tgt)]

        if 'required_edges' in knowledge:
            for (src, tgt) in knowledge['required_edges']:
                if not any(e.source == src and e.target == tgt for e in graph.edges):
                    graph.add_edge(CausalEdge(source=src, target=tgt))


class MechanismDiscovery:
    """
    Discover causal mechanisms underlying relationships.

    Not just "X causes Y" but "X causes Y through mechanism M".
    """

    def __init__(self):
        self.mechanism_templates = self._load_mechanism_templates()

    def _load_mechanism_templates(self) -> Dict[str, Dict]:
        """Load templates for common mechanisms."""
        return {
            'physics': {
                'force_acceleration': {
                    'description': 'Force causes acceleration via F=ma',
                    'equation': 'a = F/m',
                    'variables': ['force', 'mass', 'acceleration']
                },
                'energy_transfer': {
                    'description': 'Energy transfer via work or heat',
                    'equation': 'dE = W + Q',
                    'variables': ['energy', 'work', 'heat']
                },
                'field_interaction': {
                    'description': 'Field mediates interaction',
                    'equation': 'F = qE',
                    'variables': ['field', 'charge', 'force']
                }
            },
            'chemistry': {
                'collision_reaction': {
                    'description': 'Molecular collision leads to reaction',
                    'equation': 'rate = k[A][B]',
                    'variables': ['concentration', 'temperature', 'rate']
                },
                'equilibrium_shift': {
                    'description': 'Le Chatelier principle',
                    'equation': 'K = [products]/[reactants]',
                    'variables': ['concentration', 'equilibrium', 'temperature']
                },
                'electron_transfer': {
                    'description': 'Electron transfer in redox',
                    'equation': 'E = E° - (RT/nF)ln(Q)',
                    'variables': ['potential', 'concentration', 'temperature']
                }
            },
            'biology': {
                'gene_regulation': {
                    'description': 'Transcription factor regulates gene',
                    'equation': 'expression = f(TF)',
                    'variables': ['transcription_factor', 'gene_expression', 'time']
                },
                'enzyme_catalysis': {
                    'description': 'Enzyme catalyzes reaction',
                    'equation': 'v = Vmax[S]/(Km + [S])',
                    'variables': ['substrate', 'enzyme', 'rate']
                },
                'signal_transduction': {
                    'description': 'Signal cascades through pathway',
                    'equation': 'signal_out = f(signal_in)',
                    'variables': ['signal', 'receptor', 'response']
                }
            }
        }

    def discover_mechanism(self, cause: str, effect: str,
                           data: Dict[str, List[float]],
                           domain: str = "") -> Dict[str, Any]:
        """
        Discover mechanism by which cause produces effect.

        Args:
            cause: Cause variable
            effect: Effect variable
            data: Observational data
            domain: Domain hint

        Returns:
            Mechanism description
        """
        # Find intermediate variables
        intermediates = self._find_mediators(cause, effect, data)

        # Match against mechanism templates
        template_match = self._match_template(cause, effect, domain)

        # Estimate mechanism strength
        total_effect = self._estimate_total_effect(cause, effect, data)
        direct_effect = self._estimate_direct_effect(cause, effect, intermediates, data)
        indirect_effect = total_effect - direct_effect

        return {
            'cause': cause,
            'effect': effect,
            'mechanism_type': template_match.get('type', 'unknown'),
            'description': template_match.get('description', 'Direct causal path'),
            'mediators': intermediates,
            'total_effect': total_effect,
            'direct_effect': direct_effect,
            'indirect_effect': indirect_effect,
            'equation': template_match.get('equation', ''),
            'confidence': 0.8 if template_match else 0.6
        }

    def _find_mediators(self, cause: str, effect: str,
                        data: Dict[str, List[float]]) -> List[str]:
        """Find mediating variables."""
        mediators = []

        for var in data:
            if var != cause and var != effect:
                # Check if var is correlated with both cause and effect
                corr_cause = abs(self._correlation(data[cause], data[var]))
                corr_effect = abs(self._correlation(data[var], data[effect]))

                if corr_cause > 0.3 and corr_effect > 0.3:
                    mediators.append(var)

        return mediators

    def _match_template(self, cause: str, effect: str, domain: str) -> Dict:
        """Match against mechanism templates."""
        domain_lower = domain.lower()

        templates = {}
        if 'physics' in domain_lower:
            templates = self.mechanism_templates.get('physics', {})
        elif 'chem' in domain_lower:
            templates = self.mechanism_templates.get('chemistry', {})
        elif 'bio' in domain_lower:
            templates = self.mechanism_templates.get('biology', {})

        # Simple keyword matching
        cause_lower = cause.lower()
        effect_lower = effect.lower()

        for name, template in templates.items():
            vars_in_template = [v.lower() for v in template.get('variables', [])]
            if any(kw in cause_lower for kw in vars_in_template):
                if any(kw in effect_lower for kw in vars_in_template):
                    return {
                        'type': name,
                        'description': template['description'],
                        'equation': template['equation']
                    }

        return {}

    def _estimate_total_effect(self, cause: str, effect: str,
                                data: Dict[str, List[float]]) -> float:
        """Estimate total causal effect."""
        return abs(self._correlation(data[cause], data[effect]))

    def _estimate_direct_effect(self, cause: str, effect: str,
                                 mediators: List[str],
                                 data: Dict[str, List[float]]) -> float:
        """Estimate direct effect controlling for mediators."""
        if not mediators:
            return self._estimate_total_effect(cause, effect, data)

        # Partial correlation controlling for mediators
        cause_resid = self._residualize(data[cause],
                                        [data[m] for m in mediators if m in data])
        effect_resid = self._residualize(data[effect],
                                         [data[m] for m in mediators if m in data])

        return abs(self._correlation(cause_resid, effect_resid))

    def _correlation(self, x: List[float], y: List[float]) -> float:
        """Compute Pearson correlation."""
        n = len(x)
        if n < 2:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        var_x = sum((xi - mean_x)**2 for xi in x)
        var_y = sum((yi - mean_y)**2 for yi in y)
        cov_xy = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))

        if var_x == 0 or var_y == 0:
            return 0.0

        return cov_xy / (math.sqrt(var_x) * math.sqrt(var_y))

    def _residualize(self, y: List[float], x_list: List[List[float]]) -> List[float]:
        """Compute residuals."""
        if not x_list:
            return y

        n = len(y)
        mean_y = sum(y) / n
        residuals = [yi - mean_y for yi in y]

        for x in x_list:
            mean_x = sum(x) / n
            corr = self._correlation(y, x)
            for i in range(n):
                residuals[i] -= corr * (x[i] - mean_x)

        return residuals


class InterventionPlanner:
    """
    Plan interventions to achieve goals.

    Given a causal model and a goal, find interventions
    that will achieve the goal with high probability.
    """

    def __init__(self):
        self.intervention_history: List[Dict] = []

    def plan_intervention(self, graph: CausalGraph,
                          target: str,
                          goal_value: Any,
                          constraints: Dict[str, Any] = None) -> List[Intervention]:
        """
        Plan interventions to achieve goal.

        Args:
            graph: Causal graph
            target: Target variable to change
            goal_value: Desired value
            constraints: Constraints on interventions

        Returns:
            List of recommended interventions
        """
        constraints = constraints or {}

        # Find all causes of target
        causes = graph.get_ancestors(target)
        direct_causes = set(graph.get_parents(target))

        interventions = []

        # Strategy 1: Direct intervention on target
        interventions.append(Intervention(
            variable=target,
            value=goal_value,
            intervention_type=InterventionType.DO
        ))

        # Strategy 2: Intervene on direct causes
        for cause in direct_causes:
            if cause not in constraints.get('forbidden', []):
                edge = graph._get_edge(cause, target)
                if edge:
                    # Compute required intervention value
                    required_value = self._compute_required_value(
                        cause, target, goal_value, edge
                    )
                    interventions.append(Intervention(
                        variable=cause,
                        value=required_value,
                        intervention_type=InterventionType.DO
                    ))

        # Strategy 3: Intervene on root causes
        for cause in causes - direct_causes:
            if cause not in constraints.get('forbidden', []):
                if graph.nodes[cause].exogenous:
                    interventions.append(Intervention(
                        variable=cause,
                        value=goal_value,  # Simplified
                        intervention_type=InterventionType.SOFT
                    ))

        # Rank by expected effectiveness and cost
        ranked = self._rank_interventions(interventions, graph, constraints)

        return ranked

    def _compute_required_value(self, cause: str, effect: str,
                                 goal: Any, edge: CausalEdge) -> Any:
        """Compute value of cause needed to achieve goal."""
        # Simplified: assume linear relationship
        # goal = strength * cause_value
        if edge.strength != 0:
            return goal / edge.strength
        return goal

    def _rank_interventions(self, interventions: List[Intervention],
                             graph: CausalGraph,
                             constraints: Dict) -> List[Intervention]:
        """Rank interventions by effectiveness and feasibility."""
        scored = []

        for intervention in interventions:
            score = 1.0

            # Prefer interventions on variables with high causal strength
            children = graph.get_children(intervention.variable)
            for child in children:
                edge = graph._get_edge(intervention.variable, child)
                if edge:
                    score *= edge.strength

            # Penalize interventions on constrained variables
            if intervention.variable in constraints.get('costly', []):
                score *= 0.5

            # Prefer direct interventions
            if intervention.intervention_type == InterventionType.DO:
                score *= 1.2

            scored.append((intervention, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [i for i, _ in scored]

    def simulate_intervention(self, graph: CausalGraph,
                               intervention: Intervention,
                               current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate the effect of an intervention.

        Args:
            graph: Causal graph
            intervention: Intervention to apply
            current_state: Current state of all variables

        Returns:
            New state after intervention
        """
        new_state = current_state.copy()

        # Apply intervention
        new_state[intervention.variable] = intervention.value

        # Propagate effects through graph
        # Topological sort
        visited = set()
        order = []

        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for child in graph.get_children(node):
                dfs(child)
            order.append(node)

        dfs(intervention.variable)

        # Propagate in reverse topological order
        for node in reversed(order[:-1]):  # Skip intervention variable
            parents = graph.get_parents(node)
            if parents:
                # Compute new value based on parents
                value = 0
                for parent in parents:
                    edge = graph._get_edge(parent, node)
                    if edge and parent in new_state:
                        value += edge.strength * new_state[parent]
                new_state[node] = value

        return new_state


class CounterfactualReasoner:
    """
    Reason about counterfactuals.

    "What would Y have been if X had been different?"
    """

    def __init__(self):
        self.planner = InterventionPlanner()

    def evaluate_counterfactual(self, graph: CausalGraph,
                                 query: CounterfactualQuery) -> CounterfactualResult:
        """
        Evaluate a counterfactual query.

        Uses three-step procedure:
        1. Abduction: Infer exogenous variables from factual world
        2. Action: Apply intervention
        3. Prediction: Compute counterfactual outcome

        Args:
            graph: Causal graph
            query: Counterfactual query

        Returns:
            CounterfactualResult
        """
        # Step 1: Abduction - infer exogenous variables
        exogenous_values = self._abduction(graph, query.factual_world)

        # Step 2: Action - apply intervention
        modified_state = query.factual_world.copy()
        modified_state[query.intervention.variable] = query.intervention.value

        # Step 3: Prediction - compute outcome
        counterfactual_state = self.planner.simulate_intervention(
            graph, query.intervention, modified_state
        )

        # Get query variable values
        factual_value = query.factual_world.get(query.query_variable, 0)
        counterfactual_value = counterfactual_state.get(query.query_variable, 0)

        # Compute effect
        effect = counterfactual_value - factual_value

        # Generate explanation
        explanation = self._generate_explanation(
            query, factual_value, counterfactual_value, graph
        )

        return CounterfactualResult(
            query=query,
            factual_value=factual_value,
            counterfactual_value=counterfactual_value,
            effect=effect,
            explanation=explanation,
            confidence=0.8
        )

    def _abduction(self, graph: CausalGraph,
                    factual: Dict[str, Any]) -> Dict[str, Any]:
        """Infer exogenous variable values from factual world."""
        exogenous = {}

        for name, node in graph.nodes.items():
            if node.exogenous:
                # If observed, use observed value
                if name in factual:
                    exogenous[name] = factual[name]
                else:
                    # Infer from children
                    children = graph.get_children(name)
                    if children:
                        child = children[0]
                        if child in factual:
                            edge = graph._get_edge(name, child)
                            if edge and edge.strength != 0:
                                exogenous[name] = factual[child] / edge.strength
                            else:
                                exogenous[name] = 0
                        else:
                            exogenous[name] = 0
                    else:
                        exogenous[name] = 0

        return exogenous

    def _generate_explanation(self, query: CounterfactualQuery,
                               factual: Any, counterfactual: Any,
                               graph: CausalGraph) -> str:
        """Generate natural language explanation."""
        effect = counterfactual - factual if isinstance(factual, (int, float)) else "changed"

        explanation = (
            f"In the factual world, {query.query_variable} was {factual}. "
            f"If {query.intervention.variable} had been {query.intervention.value}, "
            f"then {query.query_variable} would have been {counterfactual} "
            f"(a change of {effect})."
        )

        # Add mechanism explanation
        path = graph._find_all_paths(query.intervention.variable, query.query_variable)
        if path:
            explanation += f" This effect operates through the path: {' -> '.join(path[0])}."

        return explanation


class CausalInferenceEngine:
    """
    Unified causal inference engine.

    Combines structure learning, mechanism discovery,
    intervention planning, and counterfactual reasoning.
    """

    def __init__(self):
        self.structure_learner = CausalStructureLearner()
        self.mechanism_discovery = MechanismDiscovery()
        self.intervention_planner = InterventionPlanner()
        self.counterfactual_reasoner = CounterfactualReasoner()
        self.learned_graphs: Dict[str, CausalGraph] = {}

    def analyze(self, question: str, domain: str = "",
                data: Dict[str, List[float]] = None,
                choices: List[str] = None) -> Dict[str, Any]:
        """
        Perform causal analysis on a question.

        Args:
            question: Question to analyze
            domain: Domain hint
            data: Optional observational data
            choices: Answer choices

        Returns:
            Causal analysis results
        """
        choices = choices or []
        data = data or {}

        # Extract causal structure from question
        causal_info = self._extract_causal_info(question)

        # Build or retrieve causal graph
        if data:
            graph = self.structure_learner.learn_structure(data)
        else:
            graph = self._build_graph_from_question(question, domain)

        # Analyze causal relationships
        effects = []
        for cause in causal_info.get('causes', []):
            for effect in causal_info.get('effects', []):
                mechanism = self.mechanism_discovery.discover_mechanism(
                    cause, effect, data if data else {cause: [0], effect: [0]}, domain
                )
                effects.append(mechanism)

        # Handle counterfactual questions
        counterfactual_result = None
        if causal_info.get('is_counterfactual'):
            query = self._build_counterfactual_query(question, causal_info)
            if query:
                counterfactual_result = self.counterfactual_reasoner.evaluate_counterfactual(
                    graph, query
                )

        # Rank answer choices based on causal analysis
        ranked_choices = self._rank_choices_causally(choices, effects, counterfactual_result)

        return {
            'causal_graph': graph,
            'causal_effects': effects,
            'counterfactual': counterfactual_result,
            'ranked_choices': ranked_choices,
            'answer_index': ranked_choices[0][0] if ranked_choices else 0,
            'answer': choices[ranked_choices[0][0]] if ranked_choices and choices else "",
            'confidence': ranked_choices[0][1] if ranked_choices else 0.5,
            'causal_explanation': self._generate_causal_explanation(effects, counterfactual_result)
        }

    def _extract_causal_info(self, question: str) -> Dict[str, Any]:
        """Extract causal information from question."""
        q_lower = question.lower()

        info = {
            'causes': [],
            'effects': [],
            'is_counterfactual': False,
            'intervention': None
        }

        # Detect counterfactual
        if any(kw in q_lower for kw in ['what if', 'would have', 'had been', 'instead of']):
            info['is_counterfactual'] = True

        # Extract cause/effect keywords
        causal_keywords = {
            'causes': ['causes', 'leads to', 'results in', 'produces', 'induces'],
            'effects': ['effect', 'result', 'outcome', 'consequence', 'impact']
        }

        # Simple extraction (would use NLP in production)
        words = question.split()
        for i, word in enumerate(words):
            word_lower = word.lower()
            if any(kw in word_lower for kw in causal_keywords['causes']):
                if i > 0:
                    info['causes'].append(words[i-1])
                if i < len(words) - 1:
                    info['effects'].append(words[i+1])

        return info

    def _build_graph_from_question(self, question: str, domain: str) -> CausalGraph:
        """Build causal graph from question context."""
        graph = CausalGraph()

        # Domain-specific default graphs
        if 'physics' in domain.lower():
            # Basic physics causal structure
            graph.add_node(CausalNode(name='force'))
            graph.add_node(CausalNode(name='mass'))
            graph.add_node(CausalNode(name='acceleration'))
            graph.add_node(CausalNode(name='velocity'))
            graph.add_node(CausalNode(name='position'))

            graph.add_edge(CausalEdge(source='force', target='acceleration', strength=1.0))
            graph.add_edge(CausalEdge(source='mass', target='acceleration', strength=-1.0))
            graph.add_edge(CausalEdge(source='acceleration', target='velocity', strength=1.0))
            graph.add_edge(CausalEdge(source='velocity', target='position', strength=1.0))

        elif 'chem' in domain.lower():
            graph.add_node(CausalNode(name='concentration'))
            graph.add_node(CausalNode(name='temperature'))
            graph.add_node(CausalNode(name='rate'))
            graph.add_node(CausalNode(name='equilibrium'))

            graph.add_edge(CausalEdge(source='concentration', target='rate', strength=1.0))
            graph.add_edge(CausalEdge(source='temperature', target='rate', strength=1.0))
            graph.add_edge(CausalEdge(source='rate', target='equilibrium', strength=1.0))

        elif 'bio' in domain.lower():
            graph.add_node(CausalNode(name='gene'))
            graph.add_node(CausalNode(name='mrna'))
            graph.add_node(CausalNode(name='protein'))
            graph.add_node(CausalNode(name='phenotype'))

            graph.add_edge(CausalEdge(source='gene', target='mrna', strength=1.0))
            graph.add_edge(CausalEdge(source='mrna', target='protein', strength=1.0))
            graph.add_edge(CausalEdge(source='protein', target='phenotype', strength=1.0))

        return graph

    def _build_counterfactual_query(self, question: str,
                                     causal_info: Dict) -> Optional[CounterfactualQuery]:
        """Build counterfactual query from question."""
        if not causal_info.get('is_counterfactual'):
            return None

        # Extract intervention and query variable
        # Simplified extraction
        intervention_var = causal_info['causes'][0] if causal_info['causes'] else 'X'
        query_var = causal_info['effects'][0] if causal_info['effects'] else 'Y'

        return CounterfactualQuery(
            factual_world={intervention_var: 1.0, query_var: 1.0},
            intervention=Intervention(
                variable=intervention_var,
                value=2.0,  # Counterfactual value
                intervention_type=InterventionType.COUNTERFACTUAL
            ),
            query_variable=query_var,
            query=question
        )

    def _rank_choices_causally(self, choices: List[str],
                                effects: List[Dict],
                                counterfactual: Optional[CounterfactualResult]) -> List[Tuple[int, float]]:
        """Rank choices based on causal analysis."""
        scores = []

        for i, choice in enumerate(choices):
            score = 0.5
            choice_lower = choice.lower()

            # Check consistency with causal effects
            for effect in effects:
                if effect.get('mechanism_type') in choice_lower:
                    score += 0.2
                if 'cause' in choice_lower and effect.get('total_effect', 0) > 0:
                    score += 0.1

            # Check consistency with counterfactual
            if counterfactual:
                if str(counterfactual.effect) in choice:
                    score += 0.2
                if counterfactual.counterfactual_value and str(counterfactual.counterfactual_value) in choice:
                    score += 0.15

            scores.append((i, min(0.98, score)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _generate_causal_explanation(self, effects: List[Dict],
                                      counterfactual: Optional[CounterfactualResult]) -> str:
        """Generate causal explanation."""
        explanation = "Causal analysis: "

        if effects:
            for effect in effects[:2]:
                explanation += f"{effect.get('cause', '?')} causes {effect.get('effect', '?')} "
                explanation += f"(effect size: {effect.get('total_effect', 0):.2f}). "

        if counterfactual:
            explanation += counterfactual.explanation

        return explanation


# Factory functions
def create_causal_engine() -> CausalInferenceEngine:
    """Create a causal inference engine."""
    return CausalInferenceEngine()


def create_structure_learner() -> CausalStructureLearner:
    """Create a causal structure learner."""
    return CausalStructureLearner()


def create_counterfactual_reasoner() -> CounterfactualReasoner:
    """Create a counterfactual reasoner."""
    return CounterfactualReasoner()


def create_intervention_planner() -> InterventionPlanner:
    """Create an intervention planner."""
    return InterventionPlanner()
