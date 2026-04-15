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
GES Algorithm for Causal Discovery

Greedy Equivalence Search (GES) - score-based causal discovery.
Searches over equivalence classes (CPDAGs) for highest-scoring graph.

Reference:
- Chickering, D. M. (2002). Optimal structure identification with
  greedy search. JMLR.
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, Set, List, Optional

from .independence import ConditionalIndependenceTest
from ..model.scm import StructuralCausalModel, Variable, VariableType, StructuralEquation


class GESAlgorithm:
    """
    Greedy Equivalence Search for causal discovery.

    Score-based approach that searches over equivalence classes.

    Phases:
    1. Forward phase: Add edges that most increase score
    2. Backward phase: Remove edges that most increase score

    Example:
        >>> data = pd.DataFrame({'X': x, 'Y': y, 'Z': z})
        >>> ges = GESAlgorithm(score='BIC')
        >>> scm = ges.discover(data, verbose=True)
    """

    def __init__(self,
                 score: str = 'BIC',
                 max_degree: int = 10):
        """
        Initialize GES algorithm.

        Args:
            score: Scoring criterion ('BIC', 'BDeu')
            max_degree: Maximum node degree for efficiency
        """
        self.score_type = score
        self.max_degree = max_degree

    def discover(self,
                 data: pd.DataFrame,
                 verbose: bool = False) -> StructuralCausalModel:
        """
        Discover causal graph using GES.

        Args:
            data: Observational data
            verbose: Print progress

        Returns:
            StructuralCausalModel with discovered graph
        """
        nodes = list(data.columns)

        if verbose:
            print(f"GES Algorithm on {len(nodes)} variables")
            print(f"Score: {self.score_type}, Max degree: {self.max_degree}")

        # Start with empty graph
        current_graph = nx.DiGraph()
        current_graph.add_nodes_from(nodes)
        current_score = self._compute_score(current_graph, data)

        if verbose:
            print(f"\n=== Forward Phase ===")
            print(f"Initial score: {current_score:.2f}")

        # Forward phase
        current_graph, current_score = self._forward_phase(
            current_graph, current_score, data, verbose
        )

        if verbose:
            print(f"\n=== Backward Phase ===")
            print(f"Score after forward: {current_score:.2f}")

        # Backward phase
        current_graph, current_score = self._backward_phase(
            current_graph, current_score, data, verbose
        )

        if verbose:
            print(f"Final score: {current_score:.2f}")

        # Convert to SCM
        scm = self._graph_to_scm(current_graph, data)

        return scm

    def _forward_phase(self,
                       graph: nx.DiGraph,
                       current_score: float,
                       data: pd.DataFrame,
                       verbose: bool) -> tuple:
        """Forward phase: add edges that improve score."""
        nodes = list(graph.nodes())
        improved = True
        iteration = 0

        while improved:
            improved = False
            iteration += 1

            if verbose:
                print(f"  Forward iteration {iteration}")

            best_score_diff = -np.inf
            best_edge = None

            # Try all possible edge additions
            for x in nodes:
                for y in nodes:
                    if x == y:
                        continue

                    if graph.has_edge(x, y):
                        continue

                    # Check if adding edge creates cycle
                    if nx.has_path(graph, y, x):
                        continue

                    # Check degree constraint
                    if graph.in_degree(y) >= self.max_degree:
                        continue

                    # Try adding edge
                    test_graph = graph.copy()
                    test_graph.add_edge(x, y)
                    test_score = self._compute_score(test_graph, data)

                    score_diff = test_score - current_score

                    if score_diff > best_score_diff:
                        best_score_diff = score_diff
                        best_edge = (x, y)

            # Add best edge if it improves score
            if best_score_diff > 0:
                graph.add_edge(*best_edge)
                current_score += best_score_diff
                improved = True

                if verbose:
                    print(f"    Added {best_edge[0]} → {best_edge[1]} "
                          f"(Δ={best_score_diff:.2f})")

        return graph, current_score

    def _backward_phase(self,
                        graph: nx.DiGraph,
                        current_score: float,
                        data: pd.DataFrame,
                        verbose: bool) -> tuple:
        """Backward phase: remove edges that improve score."""
        nodes = list(graph.nodes())
        improved = True
        iteration = 0

        while improved:
            improved = False
            iteration += 1

            if verbose:
                print(f"  Backward iteration {iteration}")

            best_score_diff = -np.inf
            best_edge = None

            # Try all possible edge removals
            for (x, y) in list(graph.edges()):
                # Try removing edge
                test_graph = graph.copy()
                test_graph.remove_edge(x, y)
                test_score = self._compute_score(test_graph, data)

                score_diff = test_score - current_score

                if score_diff > best_score_diff:
                    best_score_diff = score_diff
                    best_edge = (x, y)

            # Remove best edge if it improves score
            if best_score_diff > 0:
                graph.remove_edge(*best_edge)
                current_score += best_score_diff
                improved = True

                if verbose:
                    print(f"    Removed {best_edge[0]} → {best_edge[1]} "
                          f"(Δ={best_score_diff:.2f})")

        return graph, current_score

    def _compute_score(self,
                       graph: nx.DiGraph,
                       data: pd.DataFrame) -> float:
        """Compute score for graph given data."""
        if self.score_type == 'BIC':
            return self._bic_score(graph, data)
        elif self.score_type == 'BDeu':
            return self._bdeu_score(graph, data)
        else:
            raise ValueError(f"Unknown score type: {self.score_type}")

    def _bic_score(self,
                   graph: nx.DiGraph,
                   data: pd.DataFrame) -> float:
        """
        Compute BIC score for graph.

        BIC = log(L) - (k/2) * log(n)

        where L is likelihood, k is parameters, n is samples.
        """
        n = len(data)
        k = 0  # Number of parameters
        log_lik = 0  # Log likelihood

        # For each node, compute score given its parents
        for node in graph.nodes():
            parents = list(graph.predecessors(node))

            if not parents:
                # Root node: estimate variance
                k += 2  # mean and variance
                # Simplified likelihood
