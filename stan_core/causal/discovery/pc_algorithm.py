"""
PC Algorithm for Causal Discovery

Peter-Clark (PC) algorithm for learning causal structure from
observational data using conditional independence tests.

Reference:
- Spirtes, P., Glymour, C., & Scheines, R. (2000). Causation,
  Prediction, and Search. MIT Press.
"""

import numpy as np
import pandas as pd
import networkx as nx
from itertools import combinations
from typing import Dict, Set, List, Optional, Tuple

from .independence import ConditionalIndependenceTest, TestType
from ..model.scm import StructuralCausalModel, Variable, VariableType, StructuralEquation


class PCAlgorithm:
    """
    PC Algorithm for causal discovery from observational data.

    Discovers causal graph skeleton and orients edges using:
    1. Conditional independence tests for skeleton discovery
    2. V-structure orientation for collider detection
    3. Meek's rules for propagating orientations

    Example:
        >>> data = pd.DataFrame({'X': x, 'Y': y, 'Z': z})
        >>> pc = PCAlgorithm(alpha=0.05)
        >>> scm = pc.discover(data, verbose=True)
        >>> scm.visualize()
    """

    def __init__(self,
                 alpha: float = 0.05,
                 ci_test: TestType = TestType.GAUSSIAN,
                 max_level: Optional[int] = None):
        """
        Initialize PC algorithm.

        Args:
            alpha: Significance level for independence tests
            ci_test: Type of conditional independence test
            max_level: Maximum conditioning set size (None = no limit)
        """
        self.alpha = alpha
        self.ci_test = ConditionalIndependenceTest(alpha=alpha)
        self.ci_test_type = ci_test
        self.max_level = max_level

        # For debugging
        self.sep_set = {}  # Separation sets

    def discover(self,
                 data: pd.DataFrame,
                 background_knowledge: Optional[Dict] = None,
                 verbose: bool = False) -> StructuralCausalModel:
        """
        Discover causal graph from observational data.

        Args:
            data: DataFrame with samples as rows, variables as columns
            background_knowledge: Optional prior knowledge
            verbose: Print progress information

        Returns:
            StructuralCausalModel with discovered causal graph
        """
        nodes = list(data.columns)
        n = len(nodes)

        if verbose:
            print(f"PC Algorithm on {n} variables, {len(data)} samples")
            print(f"Significance level: {self.alpha}")

        # Phase 0: Initialize complete undirected graph
        graph = nx.complete_graph(n, create_using=nx.Graph())
        node_to_idx = {node: i for i, node in enumerate(nodes)}
        idx_to_node = {i: node for i, node in enumerate(nodes)}

        # Reset separation sets
        self.sep_set = {}

        # Phase 1: Skeleton discovery
        if verbose:
            print("\n=== Phase 1: Skeleton Discovery ===")

        graph = self._discover_skeleton(
            graph, data, node_to_idx, idx_to_node, verbose
        )

        # Phase 2: Orient v-structures (colliders)
        if verbose:
            print("\n=== Phase 2: Orient V-Structures ===")

        digraph = self._orient_v_structures(
            graph, idx_to_node, verbose
        )

        # Phase 3: Propagate orientations
        if verbose:
            print("\n=== Phase 3: Propagate Orientations ===")

        digraph = self._propagate_orientations(
            digraph, idx_to_node, verbose
        )

        # Convert to StructuralCausalModel
        scm = self._graph_to_scm(
            digraph, data, idx_to_node, background_knowledge
        )

        if verbose:
            print(f"\nDiscovered {scm.graph.number_of_edges()} causal edges")

        return scm

    def _discover_skeleton(self,
                           graph: nx.Graph,
                           data: pd.DataFrame,
                           node_to_idx: Dict,
                           idx_to_node: Dict,
                           verbose: bool) -> nx.Graph:
        """Phase 1: Discover skeleton by removing independent edges."""
        nodes = list(data.columns)
        n = len(nodes)

        if self.max_level is None:
            max_level = n - 2
        else:
            max_level = min(self.max_level, n - 2)

        for level in range(max_level + 1):
            if verbose:
                print(f"  Level {level}: testing sets of size {level}")

            edges_to_remove = []

            for i in range(n):
                for j in range(i + 1, n):
                    if not graph.has_edge(i, j):
                        continue

                    # Find neighbors of i excluding j
                    adj_i = set(graph.neighbors(i)) - {j}

                    if len(adj_i) < level:
                        continue

                    # Test all subsets of size 'level'
                    removed = False
                    for sep_set_nodes in combinations(adj_i, level):
                        x = data.iloc[:, i].values
                        y = data.iloc[:, j].values

                        if level > 0:
                            z = data.iloc[:, list(sep_set_nodes)].values
                        else:
                            z = None

                        # Conditional independence test
                        is_independent, p_value = self._test_independence(
                            x, y, z
                        )

                        if is_independent:
                            edges_to_remove.append((i, j))
                            self.sep_set[(i, j)] = set(sep_set_nodes)
                            self.sep_set[(j, i)] = set(sep_set_nodes)

                            if verbose:
                                node_i = idx_to_node[i]
                                node_j = idx_to_node[j]
                                sep_str = ", ".join(idx_to_node[s]
                                                   for s in sep_set_nodes)
                                print(f"    {node_i} ⟂ {node_j} | {{{sep_str}}} "
                                      f"(p={p_value:.4f})")

                            removed = True
                            break

            # Remove independent edges
            graph.remove_edges_from(edges_to_remove)

            if not edges_to_remove:
                if verbose:
                    print("  No edges removed, stopping early")
                break

        return graph

    def _orient_v_structures(self,
                             graph: nx.Graph,
                             idx_to_node: Dict,
                             verbose: bool) -> nx.DiGraph:
        """Phase 2: Orient v-structures (colliders)."""
        nodes = list(graph.nodes())
        n = len(nodes)

        # Convert to directed graph with bidirectional edges
        digraph = nx.DiGraph()
        digraph.add_nodes_from(nodes)

        for (i, j) in graph.edges():
            digraph.add_edge(i, j)
            digraph.add_edge(j, i)

        # Orient v-structures
        for i in range(n):
            for j in range(i + 1, n):
                # Find common neighbors
                common = set(graph.neighbors(i)) & set(graph.neighbors(j))

                for k in common:
                    # Check if i-k-j is unshielded (i and j not adjacent)
                    if graph.has_edge(i, j):
                        continue

                    # Orient as collider if k not in separation set
                    if k not in self.sep_set.get((i, j), set()):
                        # Remove edges k → i and k → j, keep i → k ← j
                        if digraph.has_edge(k, i):
                            digraph.remove_edge(k, i)
                        if digraph.has_edge(k, j):
                            digraph.remove_edge(k, j)

                        if verbose:
                            node_i = idx_to_node[i]
                            node_j = idx_to_node[j]
                            node_k = idx_to_node[k]
                            print(f"  Orienting collider: {node_i} → {node_k} ← {node_j}")

        return digraph

    def _propagate_orientations(self,
                                graph: nx.DiGraph,
                                idx_to_node: Dict,
                                verbose: bool) -> nx.DiGraph:
        """Phase 3: Propagate orientations using Meek's rules."""
        nodes = list(graph.nodes())
        changed = True
        iterations = 0
        max_iterations = 100

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1

            # Rule 1: If X → Y - Z and X and Z not adjacent, orient Y → Z
            for x in nodes:
                for y in nodes:
                    for z in nodes:
                        if (graph.has_edge(x, y) and
                            self._is_undirected(graph, y, z) and
                            not graph.has_edge(x, z) and
                            not self._is_undirected(graph, x, z)):
                            if graph.has_edge(z, y):
                                graph.remove_edge(z, y)
                                changed = True
                                if verbose:
                                    print(f"    Rule 1: {idx_to_node[y]} → {idx_to_node[z]}")

            # Rule 2: If X → Y → Z and X - Z, orient X → Z
            for x in nodes:
                for y in nodes:
                    for z in nodes:
                        if (graph.has_edge(x, y) and
                            graph.has_edge(y, z) and
                            self._is_undirected(graph, x, z)):
                            if graph.has_edge(z, x):
                                graph.remove_edge(z, x)
                                changed = True
                                if verbose:
                                    print(f"    Rule 2: {idx_to_node[x]} → {idx_to_node[z]}")

            # Rule 3: If X → Y → Z and X → Z - W and Y - W,
            #          orient Z → W (prevents new v-structure)
            # (Simplified - full implementation more complex)

            if iterations > max_iterations:
                if verbose:
                    print(f"  Stopped after {max_iterations} iterations")

        return graph

    def _is_undirected(self, graph: nx.DiGraph, i: int, j: int) -> bool:
        """Check if edge between i and j is undirected (bidirectional)."""
        return graph.has_edge(i, j) and graph.has_edge(j, i)

    def _test_independence(self,
                           x: np.ndarray,
                           y: np.ndarray,
                           z: Optional[np.ndarray]) -> Tuple[bool, float]:
        """Perform conditional independence test."""
        if self.ci_test_type == TestType.GAUSSIAN:
            return self.ci_test.gaussian_ci_test(x, y, z)
        elif self.ci_test_type == TestType.DISCRETE:
            return self.ci_test.discrete_ci_test(x, y, z)
        else:
            return self.ci_test.kernel_ci_test(x, y, z)

    def _infer_variable_type(self, series: pd.Series) -> VariableType:
        """Infer variable type from data."""
        unique_count = series.nunique()

        if unique_count <= 2:
            return VariableType.BINARY
        elif unique_count <= 10:
            return VariableType.DISCRETE
        else:
            return VariableType.CONTINUOUS

    def _learn_equation(self,
                        data: pd.DataFrame,
                        effect: str,
                        causes: List[str]) -> StructuralEquation:
        """Learn structural equation from data."""
        if not causes:
            return StructuralEquation(
                function=lambda pa: np.random.normal(0, 1),
                noise_distribution='gaussian'
            )

        from sklearn.linear_model import LinearRegression

        X = data[causes].values
        y = data[effect].values

        model = LinearRegression()
        model.fit(X, y)

        def equation(parent_values):
            X_pred = np.array([[parent_values.get(c, 0) for c in causes]])
            return model.predict(X_pred)[0]

        y_pred = model.predict(X)
        noise_std = np.std(y - y_pred)

        return StructuralEquation(
            function=equation,
            parameters={'intercept': model.intercept_, 'coef': model.coef_},
            noise_distribution=f'gaussian({noise_std:.4f})',
            is_invertible=True
        )

    def _graph_to_scm(self,
                      graph: nx.DiGraph,
                      data: pd.DataFrame,
                      idx_to_node: Dict,
                      background_knowledge: Optional[Dict]) -> StructuralCausalModel:
        """Convert discovered graph to StructuralCausalModel."""
        scm = StructuralCausalModel(name="PC_Discovered")

        # Add variables
        for idx, node in idx_to_node.items():
            if node in data.columns:
                var = Variable(
                    name=node,
                    type=self._infer_variable_type(data[node])
                )
                scm.add_variable(var)

        # Add causal edges (only directed edges)
        for u, v in graph.edges():
            if not graph.has_edge(v, u):  # Only directed edges
                cause = idx_to_node[u]
                effect = idx_to_node[v]

                if cause in data.columns and effect in data.columns:
                    parents = list(graph.predecessors(v))
                    causes = [idx_to_node[p] for p in parents if p in idx_to_node]

                    equation = self._learn_equation(data, effect, causes)
                    scm.add_edge(cause, effect, equation, confidence=0.8)

        # Apply background knowledge if provided
        if background_knowledge:
            self._apply_background_knowledge(scm, background_knowledge)

        return scm

    def _apply_background_knowledge(self,
                                    scm: StructuralCausalModel,
                                    knowledge: Dict):
        """Apply background knowledge to constrain model."""
        # For example: mandatory edges, forbidden edges, temporal order
        # Implementation depends on knowledge format
        pass


# Performance optimization
def cached(func):
    """Simple caching decorator for expensive computations"""
    import functools

    @functools.lru_cache(maxsize=128)
    def wrapper(*args, **kwargs):
        # Convert mutable args to hashable form
        hashable_args = []
        for arg in args:
            if isinstance(arg, (list, dict)):
                hashable_args.append(json.dumps(arg, sort_keys=True))
            elif isinstance(arg, np.ndarray):
                hashable_args.append(arg.tobytes())
            else:
                hashable_args.append(arg)

        hashable_kwargs = {}
        for k, v in kwargs.items():
            if isinstance(v, (list, dict)):
                hashable_kwargs[k] = json.dumps(v, sort_keys=True)
            elif isinstance(v, np.ndarray):
                hashable_kwargs[k] = v.tobytes()
            else:
                hashable_kwargs[k] = v

        return func(*args, **kwargs)

    return wrapper


def vectorize_operations(func):
    """Decorator to vectorize operations for better performance"""
    import numpy as np

    def wrapper(*args, **kwargs):
        # Convert arrays to numpy
        np_args = []
        for arg in args:
            if isinstance(arg, list):
                np_args.append(np.array(arg))
            else:
                np_args.append(arg)

        return func(*np_args, **kwargs)

    return wrapper



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None


