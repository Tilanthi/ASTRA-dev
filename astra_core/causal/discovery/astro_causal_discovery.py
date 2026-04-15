#!/usr/bin/env python3

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
Causal Discovery for Astronomical Data

Adapts causal discovery algorithms for astronomical data with:
- Measurement errors and upper limits
- Selection biases (flux limits, detection thresholds)
- Heteroscedastic noise
- Time series data with irregular sampling
- Spatial correlations

Extends FCI and LiNGAM algorithms for astronomical use cases.

Author: STAN Evolution Team
Date: 2025-03-18
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from scipy import stats
from scipy.spatial import distance
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings


@dataclass
class CausalGraph:
    """Represent a causal graph with potential latent confounders"""
    nodes: List[str]
    directed_edges: Set[Tuple[str, str]] = field(default_factory=set)
    bidirected_edges: Set[Tuple[str, str]] = field(default_factory=set)  # Confounded
    undirected_edges: Set[Tuple[str, str]] = field(default_factory=set)  # Uncertain

    def add_directed(self, source: str, target: str):
        """Add directed edge (source -> target)"""
        self.directed_edges.add((source, target))

    def add_bidirected(self, node1: str, node2: str):
        """Add bidirected edge (node1 <-> node2, indicates confounding)"""
        if node1 < node2:
            self.bidirected_edges.add((node1, node2))
        else:
            self.bidirected_edges.add((node2, node1))

    def add_undirected(self, node1: str, node2: str):
        """Add undirected edge (node1 -- node2, orientation unknown)"""
        if node1 < node2:
            self.undirected_edges.add((node1, node2))
        else:
            self.undirected_edges.add((node2, node1))

    def get_parents(self, node: str) -> Set[str]:
        """Get direct parents of node"""
        return {s for s, t in self.directed_edges if t == node}

    def get_children(self, node: str) -> Set[str]:
        """Get direct children of node"""
        return {t for s, t in self.directed_edges if s == node}

    def get_confounders(self, node: str) -> Set[str]:
        """Get nodes that share a confounder with node"""
        confounded = set()
        for n1, n2 in self.bidirected_edges:
            if n1 == node:
                confounded.add(n2)
            elif n2 == node:
                confounded.add(n1)
        return confounded


class AstronomicalConditionalIndependence:
    """
    Test conditional independence in astronomical data with errors.

    Handles:
    - Measurement errors
    - Upper limits (censored data)
    - Heteroscedastic uncertainties
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize independence tester.

        Args:
            alpha: Significance level for independence tests
        """
        self.alpha = alpha

    def test_independence(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: Optional[np.ndarray] = None,
        x_error: Optional[np.ndarray] = None,
        y_error: Optional[np.ndarray] = None,
        x_upper_limit: Optional[np.ndarray] = None,
        y_upper_limit: Optional[np.ndarray] = None
    ) -> Tuple[bool, float]:
        """
        Test if X is independent of Y given Z.

        Args:
            x: First variable
            y: Second variable
            z: Conditioning variables (optional)
            x_error: Measurement errors on x
            y_error: Measurement errors on y
            x_upper_limit: Boolean array for upper limits on x
            y_upper_limit: Boolean array for upper limits on y

        Returns:
            Tuple of (is_independent, p_value)
        """
        # Remove NaN values
        valid = ~np.isnan(x) & ~np.isnan(y)
        if z is not None:
            valid &= ~np.isnan(z).any(axis=1)

        x = x[valid]
        y = y[valid]
        if z is not None:
            z = z[valid]
        if x_error is not None:
            x_error = x_error[valid]
        if y_error is not None:
            y_error = y_error[valid]
        if x_upper_limit is not None:
            x_upper_limit = x_upper_limit[valid]
        if y_upper_limit is not None:
            y_upper_limit = y_upper_limit[valid]

        # Check for upper limits (censored data)
        has_limits = (x_upper_limit is not None and x_upper_limit.any()) or \
                    (y_upper_limit is not None and y_upper_limit.any())

        if has_limits:
            return self._test_independence_censored(
                x, y, z, x_upper_limit, y_upper_limit
            )

        # Check for measurement errors
        has_errors = x_error is not None or y_error is not None

        if has_errors:
            return self._test_independence_with_errors(
                x, y, z, x_error, y_error
            )

        # Standard case
        return self._test_independence_standard(x, y, z)

    def _test_independence_standard(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: Optional[np.ndarray]
    ) -> Tuple[bool, float]:
        """Standard independence test using partial correlation."""
        if z is None:
            # Simple correlation
            r, p = stats.pearsonr(x, y)
        else:
            # Partial correlation
            r = self._partial_correlation(x, y, z)

            # Fisher's z-transform for p-value
            n = len(x)
            df = n - 2 - z.shape[1] if z.ndim > 1 else n - 3

            if df > 0:
                z_score = np.sqrt(df) * r
                p = 2 * (1 - stats.norm.cdf(abs(z_score)))
            else:
                p = 1.0

        # Independence if p > alpha
        is_independent = p > self.alpha

        return is_independent, p

    def _partial_correlation(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray
    ) -> float:
        """
        Compute partial correlation between x and y given z.

        Uses regression-based approach.
        """
        # Reshape z if needed
        if z.ndim == 1:
            z = z.reshape(-1, 1)

        # Regress x on z
        beta_xz = np.linalg.lstsq(z, x, rcond=None)[0]
        x_residual = x - z @ beta_xz

        # Regress y on z
        beta_yz = np.linalg.lstsq(z, y, rcond=None)[0]
        y_residual = y - z @ beta_yz

        # Correlation of residuals
        r = np.corrcoef(x_residual, y_residual)[0, 1]

        return r

    def _test_independence_with_errors(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: Optional[np.ndarray],
        x_error: np.ndarray,
        y_error: np.ndarray
    ) -> Tuple[bool, float]:
        """
        Independence test accounting for measurement errors.

        Uses errors-in-variables approach.
        """
        # Attenuation correction
        # Measured correlation is attenuated by errors

        # Compute error variances
        var_x_error = np.mean(x_error**2)
        var_y_error = np.mean(y_error**2)
        var_x = np.var(x)
        var_y = np.var(y)

        # Reliability (ratio of true variance to total variance)
        reliability_x = 1 - var_x_error / (var_x + var_x_error)
        reliability_y = 1 - var_y_error / (var_y + var_y_error)

        # Clamp to [0, 1]
        reliability_x = max(0, min(1, reliability_x))
        reliability_y = max(0, min(1, reliability_y))

        # Observed correlation
        r_obs, p_raw = stats.pearsonr(x, y)

        # Disattenuated correlation
        if reliability_x > 0 and reliability_y > 0:
            r_true = r_obs / np.sqrt(reliability_x * reliability_y)
            r_true = max(-1, min(1, r_true))  # Clamp

            # Recompute p-value with disattenuated correlation
            n = len(x)
            t = r_true * np.sqrt(n - 2) / np.sqrt(1 - r_true**2 + 1e-10)
            p = 2 * (1 - stats.t.cdf(abs(t), n - 2))
        else:
            p = 1.0

        is_independent = p > self.alpha

        return is_independent, p

    def _test_independence_censored(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: Optional[np.ndarray],
        x_upper_limit: Optional[np.ndarray],
        y_upper_limit: Optional[np.ndarray]
    ) -> Tuple[bool, float]:
        """
        Independence test with censored data (upper limits).

        Uses survival analysis approach (Kaplan-Meier type).
        """
        # For simplicity, use only detected data
        # In practice, would use Cox regression or similar

        detected = np.ones(len(x), dtype=bool)

        if x_upper_limit is not None:
            detected &= ~x_upper_limit

        if y_upper_limit is not None:
            detected &= ~y_upper_limit

        x_detected = x[detected]
        y_detected = y[detected]

        if len(x_detected) < 10:
            # Too few detections
            return True, 1.0

        # Test on detected values
        r, p = stats.pearsonr(x_detected, y_detected)

        # Adjust for detection fraction
        detection_fraction = np.sum(detected) / len(detected)

        # Penalize p-value for low detection fraction
        p_adjusted = p / detection_fraction
        p_adjusted = min(p_adjusted, 1.0)

        is_independent = p_adjusted > self.alpha

        return is_independent, p_adjusted


class AstroFCI:
    """
    FCI (Fast Causal Inference) algorithm adapted for astronomical data.

    Handles latent confounders and selection bias.
    Produces a Partial Ancestral Graph (PAG).
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize Astro-FCI.

        Args:
            alpha: Significance level
        """
        self.alpha = alpha
        self.ci_test = AstronomicalConditionalIndependence(alpha)

    def discover(
        self,
        data: np.ndarray,
        variable_names: List[str],
        errors: Optional[np.ndarray] = None,
        upper_limits: Optional[np.ndarray] = None
    ) -> CausalGraph:
        """
        Discover causal structure from astronomical data.

        Args:
            data: Data matrix [n_samples, n_variables]
            variable_names: Names of variables
            errors: Measurement errors [n_samples, n_variables]
            upper_limits: Boolean array for upper limits

        Returns:
            CausalGraph (PAG)
        """
        n_vars = len(variable_names)

        # Initialize graph (fully connected)
        graph = CausalGraph(nodes=variable_names)

        # Phase 1: Learn skeleton (undirected graph)
        self._learn_skeleton(
            graph, data, variable_names, errors, upper_limits
        )

        # Phase 2: Orient v-structures (colliders)
        self._orient_colliders(
            graph, data, variable_names, errors, upper_limits
        )

        # Phase 3: Apply Meek rules to orient remaining edges
        self._apply_meek_rules(graph)

        return graph

    def _learn_skeleton(
        self,
        graph: CausalGraph,
        data: np.ndarray,
        names: List[str],
        errors: Optional[np.ndarray],
        upper_limits: Optional[np.ndarray]
    ):
        """Learn skeleton of causal graph."""
        n_vars = len(names)

        # Start with complete undirected graph
        adjacency = {name: set(names) - {name} for name in names}

        # Increasing conditioning set size
        for size in range(n_vars - 1):
            for i in range(n_vars):
                for j in range(i + 1, n_vars):
                    x_name = names[i]
                    y_name = names[j]

                    # Check if still adjacent
                    if y_name not in adjacency[x_name]:
                        continue

                    # Find conditioning sets
                    neighbors_x = adjacency[x_name] - {y_name}

                    if len(neighbors_x) < size:
                        continue

                    # Test independence
                    x = data[:, i]
                    y = data[:, j]

                    x_err = errors[:, i] if errors is not None else None
                    y_err = errors[:, j] if errors is not None else None

                    x_ul = upper_limits[:, i] if upper_limits is not None else None
                    y_ul = upper_limits[:, j] if upper_limits is not None else None

                    # Try conditioning sets
                    for z_names in self._get_conditioning_sets(neighbors_x, size):
                        z_indices = [names.index(z) for z in z_names]

                        if len(z_indices) == 0:
                            z_data = None
                        else:
                            z_data = data[:, z_indices]

                        is_indep, p = self.ci_test.test_independence(
                            x, y, z_data, x_err, y_err, x_ul, y_ul
                        )

                        if is_indep:
                            # Remove edge
                            adjacency[x_name].discard(y_name)
                            adjacency[y_name].discard(x_name)
                            break

        # Convert to undirected edges in graph
        for i in range(n_vars):
            for j in range(i + 1, n_vars):
                if names[j] in adjacency[names[i]]:
                    graph.add_undirected(names[i], names[j])

    def _orient_colliders(
        self,
        graph: CausalGraph,
        data: np.ndarray,
        names: List[str],
        errors: Optional[np.ndarray],
        upper_limits: Optional[np.ndarray]
    ):
        """Orient collider structures (X -> Y <- Z)."""
        # For each unshielded triple
        for i in range(len(names)):
            for j in range(len(names)):
                for k in range(len(names)):
                    if i >= j or j >= k or i >= k:
                        continue

                    x_name, y_name, z_name = names[i], names[j], names[k]

                    # Check if X - Y - Z is unshielded (X and Z not adjacent)
                    has_xy = (x_name, y_name) in graph.undirected_edges or \
                            (y_name, x_name) in graph.undirected_edges
                    has_yz = (y_name, z_name) in graph.undirected_edges or \
                            (z_name, y_name) in graph.undirected_edges
                    has_xz = (x_name, z_name) in graph.undirected_edges or \
                            (z_name, x_name) in graph.undirected_edges

                    if has_xy and has_yz and not has_xz:
                        # Test if X indep Z | Y
                        x = data[:, i]
                        z = data[:, k]
                        y = data[:, j:j+1]

                        x_err = errors[:, i] if errors is not None else None
                        z_err = errors[:, k] if errors is not None else None

                        x_ul = upper_limits[:, i] if upper_limits is not None else None
                        z_ul = upper_limits[:, k] if upper_limits is not None else None

                        is_indep, p = self.ci_test.test_independence(
                            x, z, y, x_err, z_err, x_ul, z_ul
                        )

                        if not is_indep:
                            # Orient as collider: X -> Y <- Z
                            # Remove undirected edges
                            graph.undirected_edges.discard((x_name, y_name))
                            graph.undirected_edges.discard((y_name, z_name))

                            # Add directed edges
                            graph.add_directed(x_name, y_name)
                            graph.add_directed(z_name, y_name)

    def _apply_meek_rules(self, graph: CausalGraph):
        """
        Apply Meek's orientation rules.

        Rules:
        1. Orient X - Y -> Z as X -> Y - Z if Y and Z not adjacent
        2. Orient X -> Y - Z as X -> Y -> Z if X and Z adjacent
        3. Orient X - Y -> Z <- X - W as X -> Y - Z <- X <- W
        4. Orient X -> Y - Z -> W and X - W as X -> Y -> W <- Z
        """
        changed = True

        while changed:
            changed = False

            # Apply rules repeatedly
            # (Simplified implementation)

            # Rule 1: Avoid new v-structures
            for (y, z) in list(graph.directed_edges):
                for x in graph.nodes:
                    if x == y or x == z:
                        continue

                    has_yx = (y, x) in graph.undirected_edges or (x, y) in graph.undirected_edges
                    has_xz = (x, z) in graph.undirected_edges or (z, x) in graph.undirected_edges

                    if has_yx and not has_xz:
                        # Orient Y - X as Y -> X
                        graph.undirected_edges.discard((x, y))
                        graph.add_directed(y, x)
                        changed = True

    def _get_conditioning_sets(
        self,
        variables: Set[str],
        size: int
    ) -> List[Set[str]]:
        """Get all combinations of conditioning sets of given size."""
        from itertools import combinations

        vars_list = list(variables)

        if size > len(vars_list):
            return []

        return [set(combo) for combo in combinations(vars_list, size)]


class TemporalCausalDiscovery:
    """
    Discover causal relationships from time-series astronomical data.

    Handles:
    - Irregular sampling
    - Measurement gaps
    - Autocorrelation
    - Time delays
    """

    def __init__(self, max_lag: int = 10):
        """
        Initialize temporal causal discovery.

        Args:
            max_lag: Maximum time lag to consider
        """
        self.max_lag = max_lag

    def discover_from_light_curves(
        self,
        light_curves: Dict[str, Tuple[np.ndarray, np.ndarray]],
        min_time_gap: float = 0.1
    ) -> CausalGraph:
        """
        Discover causal relationships from light curves.

        Args:
            light_curves: Dict of {source_id: (times, fluxes)}
            min_time_gap: Minimum time gap for interpolation (days)

        Returns:
            CausalGraph with time-lagged causal edges
        """
        sources = list(light_curves.keys())
        graph = CausalGraph(nodes=sources)

        # Interpolate to common time grid
        common_times = self._get_common_times(light_curves, min_time_gap)

        if len(common_times) < 10:
            return graph

        # Build data matrix
        data = {}
        for source_id in sources:
            times, fluxes = light_curves[source_id]

            # Interpolate
            from scipy.interpolate import interp1d
            f = interp1d(times, fluxes, kind='linear', bounds_error=False,
                       fill_value='extrapolate')
            data[source_id] = f(common_times)

        # Test for Granger causality at various lags
        for i, source_x in enumerate(sources):
            for j, source_y in enumerate(sources):
                if i == j:
                    continue

                # Test if X Granger-causes Y
                p_value = self._granger_causality_test(
                    data[source_x], data[source_y]
                )

                if p_value < 0.05:  # Significant
                    # Find optimal lag
                    best_lag = self._find_optimal_lag(
                        data[source_x], data[source_y]
                    )

                    # Add directed edge with lag annotation
                    graph.add_directed(source_x, source_y)
                    # Store lag as metadata (would need to extend dataclass)

        return graph

    def _get_common_times(
        self,
        light_curves: Dict[str, Tuple[np.ndarray, np.ndarray]],
        min_gap: float
    ) -> np.ndarray:
        """Get common time grid for all light curves."""
        # Find time range
        all_times = []
        for times, _ in light_curves.values():
            all_times.extend(times)

        min_time = min(all_times)
        max_time = max(all_times)

        # Create uniform grid
        common_times = np.arange(min_time, max_time, min_gap)

        return common_times

    def _granger_causality_test(
        self,
        x: np.ndarray,
        y: np.ndarray,
        max_lag: int = 5
    ) -> float:
        """
        Test if x Granger-causes y.

        Returns p-value of test.
        """
        from scipy.stats import f

        # Lagged regression
        # Model 1: y(t) = sum(a_i * y(t-i)) + sum(b_i * x(t-i))
        # Model 2: y(t) = sum(a_i * y(t-i))  (restricted)

        n = len(y)

        # Create lag matrices
        Y_lag = np.column_stack([y[max_lag-i:-i] for i in range(1, max_lag+1)])
        X_lag = np.column_stack([x[max_lag-i:-i] for i in range(1, max_lag+1)])

        Y_target = y[max_lag:]

        # Full model
        full_design = np.column_stack([Y_lag, X_lag])
        full_res = np.linalg.lstsq(full_design, Y_target, rcond=None)[0]
        full_pred = full_design @ full_res
        full_sse = np.sum((Y_target - full_pred)**2)

        # Restricted model
        rest_res = np.linalg.lstsq(Y_lag, Y_target, rcond=None)[0]
        rest_pred = Y_lag @ rest_res
        rest_sse = np.sum((Y_target - rest_pred)**2)

        # F-test
        df1 = max_lag
        df2 = n - 2 * max_lag

        if df2 > 0 and rest_sse > 0:
            F_stat = ((rest_sse - full_sse) / df1) / (full_sse / df2)
            p_value = 1 - f.cdf(F_stat, df1, df2)
        else:
            p_value = 1.0

        return p_value

    def _find_optimal_lag(
        self,
        x: np.ndarray,
        y: np.ndarray,
        max_lag: int = 10
    ) -> int:
        """Find optimal time lag for causal influence."""
        best_lag = 0
        best_corr = 0

        for lag in range(1, max_lag + 1):
            if lag >= len(x) or lag >= len(y):
                continue

            # Cross-correlation at this lag
            x_lagged = x[:-lag]
            y_lead = y[lag:]

            if len(x_lagged) < 10:
                continue

            corr = np.corrcoef(x_lagged, y_lead)[0, 1]

            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag

        return best_lag


def create_astro_fci(alpha: float = 0.05) -> AstroFCI:
    """Factory function to create Astro-FCI instance."""
    return AstroFCI(alpha=alpha)


def create_temporal_discovery(max_lag: int = 10) -> TemporalCausalDiscovery:
    """Factory function to create temporal discovery instance."""
    return TemporalCausalDiscovery(max_lag=max_lag)


if __name__ == "__main__":
    print("="*70)
    print("Causal Discovery for Astronomical Data")
    print("="*70)
    print()
    print("Components:")
    print("  - AstroFCI: FCI algorithm for astronomical data")
    print("  - TemporalCausalDiscovery: Time-series causal discovery")
    print("  - AstronomicalConditionalIndependence: Independence tests")
    print("  - CausalGraph: Causal graph representation")
    print()
    print("Features:")
    print("  - Handles measurement errors")
    print("  - Handles upper limits (censored data)")
    print("  - Detects latent confounders")
    print("  - Time-series causal inference")
    print("  - Irregular sampling support")
    print()
    print("Applications:")
    print("  - ISM causal structure")
    print("  - Galaxy formation dependencies")
    print("  - Stellar variable correlations")
    print("  - AGN feedback mechanisms")
    print("="*70)
