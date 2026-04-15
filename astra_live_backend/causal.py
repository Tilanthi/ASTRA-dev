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
ASTRA Live — Causal Inference Engine
Implements the PC algorithm and FCI algorithm for causal discovery
as described in White & Dey (2026), Section 4 and Test Case 6.

References:
- Spirtes, Glymour & Scheines (2000) "Causation, Prediction, and Search"
- Zhang (2008) "On the completeness of orientation rules for causal discovery"
"""
import numpy as np
from scipy import stats
from itertools import combinations, permutations
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field, asdict
import time


@dataclass
class CausalEdge:
    source: str
    target: str
    edge_type: str  # "-->", "<--", "o-o", "---", "x->"
    confidence: float
    p_value: float
    conditioning_set: List[str]
    test_statistic: float = 0.0

    def to_dict(self):
        return asdict(self)


@dataclass
class CausalGraph:
    variables: List[str]
    edges: List[CausalEdge]
    adjacencies: Dict[str, Set[str]]
    v_structures: List[Dict]
    uncertain_edges: List[CausalEdge]
    algorithm: str  # "PC" or "FCI"
    alpha: float
    timestamp: float = 0.0

    def to_dict(self):
        return {
            "variables": self.variables,
            "edges": [e.to_dict() for e in self.edges],
            "adjacencies": {k: list(v) for k, v in self.adjacencies.items()},
            "v_structures": self.v_structures,
            "uncertain_edges": [e.to_dict() for e in self.uncertain_edges],
            "algorithm": self.algorithm,
            "alpha": self.alpha,
            "timestamp": self.timestamp,
        }


def conditional_independence_test(data: np.ndarray, x_idx: int, y_idx: int,
                                    z_indices: List[int] = None,
                                    alpha: float = 0.05) -> Tuple[bool, float, float]:
    """
    Test conditional independence of X and Y given Z using partial correlation.
    Fisher's Z-test for continuous variables.

    Returns: (is_independent, p_value, correlation)
    """
    n = data.shape[0]
    x = data[:, x_idx]
    y = data[:, y_idx]

    if z_indices is None or len(z_indices) == 0:
        # Marginal independence
        r, p = stats.pearsonr(x, y)
        return p > alpha, p, r

    # Partial correlation: regress out Z from both X and Y
    Z = data[:, z_indices]
    if Z.ndim == 1:
        Z = Z.reshape(-1, 1)

    # Add intercept
    Z_aug = np.column_stack([np.ones(n), Z])

    # Residuals after regressing on Z
    beta_x = np.linalg.lstsq(Z_aug, x, rcond=None)[0]
    beta_y = np.linalg.lstsq(Z_aug, y, rcond=None)[0]
    resid_x = x - Z_aug @ beta_x
    resid_y = y - Z_aug @ beta_y

    # Partial correlation
    r_partial, _ = stats.pearsonr(resid_x, resid_y)

    # Fisher's Z-test
    k = len(z_indices)  # number of conditioning variables
    if abs(r_partial) >= 1.0:
        z_stat = 0.0
        p_value = 1.0
    else:
        z_stat = 0.5 * np.log((1 + r_partial) / (1 - r_partial)) * np.sqrt(n - k - 3)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    return p_value > alpha, p_value, r_partial


def pc_algorithm(data: np.ndarray, variable_names: List[str],
                  alpha: float = 0.05, max_depth: int = 3) -> CausalGraph:
    """
    PC Algorithm for causal structure discovery.

    Phase 1: Start with complete undirected graph, remove edges based on
             conditional independence tests
    Phase 2: Orient v-structures (colliders)
    Phase 3: Apply orientation rules to complete the DAG

    Returns CausalGraph with directed edges.
    """
    n_vars = len(variable_names)
    n = data.shape[0]

    # Phase 1: Adjacency discovery
    # Start with complete graph
    adjacencies = {name: set(variable_names) - {name} for name in variable_names}
    sep_sets = {}  # Separation sets

    # Test increasing conditioning set sizes
    for depth in range(max_depth + 1):
        edges_to_remove = []

        for x_name in variable_names:
            for y_name in list(adjacencies[x_name]):
                if y_name not in adjacencies[x_name]:
                    continue

                x_idx = variable_names.index(x_name)
                y_idx = variable_names.index(y_name)

                # Try all conditioning sets of current size
                neighbors = list(adjacencies[x_name] - {y_name})
                if len(neighbors) < depth:
                    continue

                for z_names in combinations(neighbors, depth):
                    z_indices = [variable_names.index(z) for z in z_names]
                    is_indep, p_val, r_val = conditional_independence_test(
                        data, x_idx, y_idx, z_indices, alpha)

                    if is_indep:
                        edges_to_remove.append((x_name, y_name, list(z_names)))
                        sep_sets[(x_name, y_name)] = list(z_names)
                        sep_sets[(y_name, x_name)] = list(z_names)
                        break

        for x_name, y_name, z_names in edges_to_remove:
            adjacencies[x_name].discard(y_name)
            adjacencies[y_name].discard(x_name)

    # Phase 2: Orient v-structures (colliders)
    # X - Y - Z where Y not in sep(X,Z) → X → Y ← Z
    directed = {}  # (source, target) → edge_type
    v_structures = []

    for y_name in variable_names:
        neighbors = list(adjacencies[y_name])
        for x_name, z_name in combinations(neighbors, 2):
            if z_name in adjacencies.get(x_name, set()):
                continue  # X and Z are adjacent — not a v-structure

            # Check if y is NOT in sep(x, z)
            sep = sep_sets.get((x_name, z_name), [])
            if y_name not in sep:
                # Orient as collider: X → Y ← Z
                directed[(x_name, y_name)] = "→"
                directed[(z_name, y_name)] = "→"
                v_structures.append({
                    "collider": y_name,
                    "parents": [x_name, z_name],
                    "p_value": sep_sets.get((x_name, z_name), [""])[0] if sep_sets.get((x_name, z_name)) else None,
                })

    # Phase 3: Apply Meek's orientation rules
    # Rule 1: X → Y - Z and X,Z not adjacent → Y → Z
    # Rule 2: X → Y → Z and X - Z → X → Z
    changed = True
    while changed:
        changed = False
        for y_name in variable_names:
            for x_name in adjacencies[y_name]:
                for z_name in adjacencies[y_name]:
                    if x_name == z_name:
                        continue
                    if (x_name, y_name) not in directed:
                        continue
                    # X → Y - Z
                    if (y_name, z_name) not in directed and (z_name, y_name) not in directed:
                        # Check if X and Z are not adjacent
                        if z_name not in adjacencies[x_name]:
                            # Orient Y → Z
                            directed[(y_name, z_name)] = "→"
                            changed = True

    # Build final edges
    edges = []
    for (src, tgt), arrow in directed.items():
        edges.append(CausalEdge(
            source=src, target=tgt,
            edge_type=arrow,
            confidence=1.0 - alpha,
            p_value=alpha,
            conditioning_set=sep_sets.get((src, tgt), []),
        ))

    # Undirected edges that remain
    for x_name in variable_names:
        for y_name in adjacencies[x_name]:
            if x_name < y_name:  # avoid duplicates
                if (x_name, y_name) not in directed and (y_name, x_name) not in directed:
                    edges.append(CausalEdge(
                        source=x_name, target=y_name,
                        edge_type="—",
                        confidence=1.0 - alpha,
                        p_value=alpha,
                        conditioning_set=sep_sets.get((x_name, y_name), []),
                    ))

    return CausalGraph(
        variables=variable_names,
        edges=edges,
        adjacencies={k: v for k, v in adjacencies.items()},
        v_structures=v_structures,
        uncertain_edges=[],
        algorithm="PC",
        alpha=alpha,
        timestamp=time.time(),
    )


def fci_algorithm(data: np.ndarray, variable_names: List[str],
                   alpha: float = 0.05, max_depth: int = 3) -> CausalGraph:
    """
    FCI (Fast Causal Inference) algorithm.
    Like PC but accounts for latent (unmeasured) confounders.
    Produces Partial Ancestral Graphs (PAGs) with circle-circle notation.
    """
    # Run PC first to get initial structure
    pc_graph = pc_algorithm(data, variable_names, alpha, max_depth)

    # FCI modification: all directed edges become uncertain (o-o or x->)
    fci_edges = []
    uncertain = []

    for edge in pc_graph.edges:
        if edge.edge_type == "→":
            # In FCI, directed edges may have hidden confounders
            fci_edge = CausalEdge(
                source=edge.source, target=edge.target,
                edge_type="x→",  # possibly direct, possibly confounded
                confidence=edge.confidence * 0.8,  # reduced confidence
                p_value=edge.p_value,
                conditioning_set=edge.conditioning_set,
            )
            fci_edges.append(fci_edge)
            uncertain.append(fci_edge)
        else:
            fci_edges.append(edge)

    # Add potential hidden confounders between non-adjacent nodes
    # that share common children (latent variable detection)
    for y_name in variable_names:
        parents_of_y = [e.source for e in fci_edges if e.target == y_name and e.edge_type in ("→", "x→")]
        for x1, x2 in combinations(parents_of_y, 2):
            if x2 not in pc_graph.adjacencies.get(x1, set()):
                # X1 → Y ← X2 but X1,X2 not adjacent
                # This could be a v-structure OR a hidden confounder
                confounder_edge = CausalEdge(
                    source=x1, target=x2,
                    edge_type="o—o",  # circle-circle: uncertain due to possible confounder
                    confidence=0.5,
                    p_value=alpha,
                    conditioning_set=[y_name],
                )
                fci_edges.append(confounder_edge)
                uncertain.append(confounder_edge)

    return CausalGraph(
        variables=variable_names,
        edges=fci_edges,
        adjacencies=pc_graph.adjacencies,
        v_structures=pc_graph.v_structures,
        uncertain_edges=uncertain,
        algorithm="FCI",
        alpha=alpha,
        timestamp=time.time(),
    )


def test_intervention(data: np.ndarray, variable_names: List[str],
                      cause: str, effect: str,
                      intervention_delta: float = 0.1) -> Dict:
    """
    Test a causal claim via intervention analysis.
    If X causes Y, changing X while holding other variables fixed should change Y.

    Uses the do-calculus inspired approach: regress Y on all variables,
    then simulate changing X by intervention_delta.
    """
    cause_idx = variable_names.index(cause)
    effect_idx = variable_names.index(effect)

    # Fit linear model: Y = β₀ + β₁X + β₂Z₁ + ... + ε
    X_all = data
    Y = data[:, effect_idx]

    # OLS
    X_aug = np.column_stack([np.ones(data.shape[0]), X_all])
    beta = np.linalg.lstsq(X_aug, Y, rcond=None)[0]

    # Predicted effect of intervention
    cause_coef = beta[cause_idx + 1]  # +1 for intercept
    predicted_change = cause_coef * intervention_delta

    # Bootstrap uncertainty
    n_boot = 1000
    boot_effects = []
    for _ in range(n_boot):
        idx = np.random.choice(data.shape[0], data.shape[0], replace=True)
        X_boot = data[idx]
        Y_boot = Y[idx]
        X_aug_boot = np.column_stack([np.ones(X_boot.shape[0]), X_boot])
        try:
            beta_boot = np.linalg.lstsq(X_aug_boot, Y_boot, rcond=None)[0]
            boot_effects.append(beta_boot[cause_idx + 1] * intervention_delta)
        except:
            pass

    boot_effects = np.array(boot_effects)
    se = np.std(boot_effects)
    ci_low, ci_high = np.percentile(boot_effects, [2.5, 97.5])

    # Test if effect is significant (CI doesn't include zero)
    significant = not (ci_low <= 0 <= ci_high)

    return {
        "cause": cause,
        "effect": effect,
        "intervention_delta": intervention_delta,
        "predicted_effect": float(predicted_change),
        "effect_std_error": float(se),
        "confidence_interval_95": [float(ci_low), float(ci_high)],
        "significant": significant,
        "causal_strength": float(abs(cause_coef)),
        "effect_direction": "positive" if cause_coef > 0 else "negative",
    }
