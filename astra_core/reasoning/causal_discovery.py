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
Causal Discovery: Learn Causal Structure from Data

This module implements causal structure learning - discovering causal
relationships from observational and interventional data.

Key Features:
- PC algorithm (constraint-based discovery)
- Score-based structure learning (BIC/BDeu)
- Hybrid discovery combining both approaches
- Integration with V36 SymbolicCausalAbstraction

Why This Matters for AGI:
- STAN can now discover causal structure, not just assume it
- Enables autonomous theory building
- Connects observations to mechanisms

Date: 2025-12-10
Version: 39.0
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple, Set, FrozenSet
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from itertools import combinations, permutations
from collections import defaultdict
from scipy import stats


class EdgeType(Enum):
    """Types of edges in causal graph"""
    DIRECTED = "->"        # X -> Y
    UNDIRECTED = "--"      # X -- Y (unoriented)
    BIDIRECTED = "<->"     # X <-> Y (latent confounder)


@dataclass
class Edge:
    """An edge in a causal graph"""
    source: str
    target: str
    edge_type: EdgeType
    strength: float = 1.0   # Edge strength/confidence
    metadata: Dict = field(default_factory=dict)

    def __hash__(self):
        return hash((self.source, self.target, self.edge_type))

    def __eq__(self, other):
        return (self.source == other.source and
                self.target == other.target and
                self.edge_type == other.edge_type)


@dataclass
class CausalGraph:
    """A causal graph structure"""
    nodes: Set[str]
    edges: List[Edge]
    latent_variables: Set[str] = field(default_factory=set)
    metadata: Dict = field(default_factory=dict)

    def get_parents(self, node: str) -> Set[str]:
        """Get parent nodes of a node"""
        return {e.source for e in self.edges
                if e.target == node and e.edge_type == EdgeType.DIRECTED}

    def get_children(self, node: str) -> Set[str]:
        """Get child nodes of a node"""
        return {e.target for e in self.edges
                if e.source == node and e.edge_type == EdgeType.DIRECTED}

    def get_neighbors(self, node: str) -> Set[str]:
        """Get all connected nodes"""
        neighbors = set()
        for e in self.edges:
            if e.source == node:
                neighbors.add(e.target)
            if e.target == node:
                neighbors.add(e.source)
        return neighbors

    def get_adjacency_matrix(self) -> Tuple[np.ndarray, List[str]]:
        """Get adjacency matrix representation"""
        node_list = sorted(self.nodes)
        n = len(node_list)
        node_idx = {node: i for i, node in enumerate(node_list)}

        adj = np.zeros((n, n))
        for edge in self.edges:
            i, j = node_idx[edge.source], node_idx[edge.target]
            if edge.edge_type == EdgeType.DIRECTED:
                adj[i, j] = edge.strength
            elif edge.edge_type == EdgeType.UNDIRECTED:
                adj[i, j] = edge.strength
                adj[j, i] = edge.strength
            elif edge.edge_type == EdgeType.BIDIRECTED:
                adj[i, j] = edge.strength
                adj[j, i] = edge.strength

        return adj, node_list

    def has_edge(self, source: str, target: str) -> bool:
        """Check if edge exists"""
        return any(e.source == source and e.target == target for e in self.edges)

    def add_edge(self, edge: Edge):
        """Add an edge"""
        if edge not in self.edges:
            self.edges.append(edge)

    def remove_edge(self, source: str, target: str):
        """Remove edge between source and target"""
        self.edges = [e for e in self.edges
                      if not (e.source == source and e.target == target)]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'nodes': list(self.nodes),
            'edges': [
                {
                    'source': e.source,
                    'target': e.target,
                    'type': e.edge_type.value,
                    'strength': e.strength
                }
                for e in self.edges
            ],
            'latent_variables': list(self.latent_variables),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CausalGraph':
        """Construct from dictionary"""
        edges = [
            Edge(
                source=e['source'],
                target=e['target'],
                edge_type=EdgeType(e['type']),
                strength=e.get('strength', 1.0)
            )
            for e in data['edges']
        ]
        return cls(
            nodes=set(data['nodes']),
            edges=edges,
            latent_variables=set(data.get('latent_variables', [])),
            metadata=data.get('metadata', {})
        )


class IndependenceTest(ABC):
    """Abstract base for conditional independence tests"""

    @abstractmethod
    def test(self, X: str, Y: str, Z: Set[str], data: np.ndarray,
             var_names: List[str]) -> Tuple[float, bool]:
        """
        Test X ⊥ Y | Z (X independent of Y given Z).

        Args:
            X: First variable name
            Y: Second variable name
            Z: Conditioning set variable names
            data: Data matrix (n_samples x n_vars)
            var_names: Variable names corresponding to columns

        Returns:
            Tuple of (p_value, is_independent)
        """
        pass


class PartialCorrelationTest(IndependenceTest):
    """Conditional independence test using partial correlation"""

    def __init__(self, alpha: float = 0.05):
        """
        Args:
            alpha: Significance level for independence
        """
        self.alpha = alpha

    def test(self, X: str, Y: str, Z: Set[str], data: np.ndarray,
             var_names: List[str]) -> Tuple[float, bool]:
        """Test using partial correlation with Fisher's z-transform"""
        var_idx = {name: i for i, name in enumerate(var_names)}

        x_idx = var_idx[X]
        y_idx = var_idx[Y]
        z_idx = [var_idx[z] for z in Z] if Z else []

        n = data.shape[0]

        # Compute partial correlation
        if not z_idx:
            # Simple correlation
            r = np.corrcoef(data[:, x_idx], data[:, y_idx])[0, 1]
        else:
            # Partial correlation
            r = self._partial_correlation(data, x_idx, y_idx, z_idx)

        # Handle perfect correlation
        if abs(r) >= 1.0:
            return 0.0, False

        # Fisher's z-transform for p-value
        z_stat = 0.5 * np.log((1 + r) / (1 - r))
        se = 1.0 / np.sqrt(n - len(z_idx) - 3)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat / se)))

        is_independent = p_value > self.alpha

        return p_value, is_independent

    def _partial_correlation(self, data: np.ndarray, x: int, y: int,
                            z: List[int]) -> float:
        """Compute partial correlation"""
        # Residualize X and Y on Z
        X_data = data[:, x]
        Y_data = data[:, y]
        Z_data = data[:, z]

        # Linear regression residuals
        if Z_data.ndim == 1:
            Z_data = Z_data.reshape(-1, 1)


class StructuralCausalModel:
    """
    Structural Causal Model for causal discovery and reasoning

    This class provides a structural causal model (SCM) representation
    for discovering and reasoning about causal relationships in data.

    Based on Pearl's causal hierarchy and structural causal models.
    """

    def __init__(self):
        """Initialize an empty structural causal model"""
        self.variables = {}  # Dictionary mapping variable names to their types
        self.structural_equations = {}  # Structural equations for each variable
        self.exogenous_variables = {}  # Exogenous (noise) variables
        self.causal_graph = {}  # Adjacency representation of causal graph

    def add_variable(self, var_name: str, var_type: str = "continuous",
                     parents: List[str] = None, structural_eq: str = None):
        """
        Add a variable to the causal model

        Args:
            var_name: Name of the variable
            var_type: Type of variable ('continuous', 'binary', 'categorical')
            parents: List of parent variable names (causes)
            structural_eq: Structural equation as string
        """
        self.variables[var_name] = {
            'type': var_type,
            'parents': parents or [],
            'structural_eq': structural_eq
        }

        if parents:
            self.causal_graph[var_name] = parents

    def add_structural_equation(self, var_name: str, equation: str):
        """Add or update structural equation for a variable"""
        if var_name in self.variables:
            self.variables[var_name]['structural_eq'] = equation
        else:
            self.variables[var_name] = {
                'type': 'continuous',
                'parents': [],
                'structural_eq': equation
            }

    def get_causal_parents(self, var_name: str) -> List[str]:
        """Get direct causes (parents) of a variable"""
        if var_name in self.variables:
            return self.variables[var_name]['parents']
        return []

    def get_causal_children(self, var_name: str) -> List[str]:
        """Get direct effects (children) of a variable"""
        children = []
        for var, info in self.variables.items():
            if var_name in info.get('parents', []):
                children.append(var)
        return children

    def get_descendants(self, var_name: str, max_depth: int = 10) -> List[str]:
        """Get all descendants (causal effects) up to max_depth"""
        descendants = set()
        visited = set()
        queue = [(var_name, 0)]

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth or current in visited:
                continue

            visited.add(current)
            children = self.get_causal_children(current)

            for child in children:
                if child not in descendants:
                    descendants.add(child)
                    queue.append((child, depth + 1))

        return list(descendants)

    def has_causal_path(self, source: str, target: str) -> bool:
        """Check if there's a causal path from source to target"""
        # Use BFS to find path
        visited = set()
        queue = [source]

        while queue:
            current = queue.pop(0)
            if current == target:
                return True

            if current in visited:
                continue

            visited.add(current)
            queue.extend(self.get_causal_children(current))

        return False

    def get_causal_graph(self) -> Dict[str, List[str]]:
        """Get the causal graph as adjacency list"""
        return self.causal_graph.copy()
