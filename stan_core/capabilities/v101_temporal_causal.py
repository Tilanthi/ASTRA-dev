"""
V101 Temporal Causal Discovery - For Time-Series Causal Inference
====================================================================

PROBLEM: Standard causal discovery (V98 FCI) assumes static causal structure.
Real astrophysical systems exhibit time-dependent causality:
- Time-lagged effects (X[t-k] → Y[t])
- Feedback loops (X → Y → X)
- Time-varying causality (causal structure changes)
- Temporal confounding (latent variables with time-delayed effects)

SOLUTION: Three complementary algorithms for temporal causal discovery:

1. TIME-VARYING FCI (TVFCI)
   - Extends FCI to handle time-indexed data
   - Discovers optimal causal lags
   - Builds Time-Lagged PAGs (TL-PAGs)

2. GRANGER-FCI HYBRID
   - Combines Granger causality (temporal precedence) with FCI (latent confounders)
   - VAR-based discovery for multi-variable time series
   - Detects feedback loops

3. CHANGE POINT DETECTION
   - Identifies when causal structures change
   - Segments time series into causally homogeneous periods
   - Links causal changes to physical events

INTEGRATION:
- Extends v98_fci_causal_discovery
- Compatible with v97_knowledge_isolation
- Integrates with v4_revolutionary systems

ASTROPHYSICAL APPLICATIONS:
- Stellar variability: Teff → R → L causal chain
- Accretion disks: dM/dt → L_X with hysteresis
- Star formation: Delayed triggering, feedback effects
- AGN feedback: BH accretion → outbursts → quenching

Date: 2026-04-14
Version: 1.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from enum import Enum
import numpy as np
from scipy import stats
from scipy.signal import correlate
from itertools import combinations, permutations
import warnings


class EdgeEndpointType(Enum):
    """Types of edge endpoints in PAGs"""
    ARROW = "arrow"       # >  (points to node: cause -> effect)
    CIRCLE = "circle"     # o  (uncertain: could be cause or effect)
    TAIL = "tail"         # -  (definitely not cause: confounder/mediator)


@dataclass
class TimeLaggedPAGEdge:
    """
    Time-lagged edge in a Partial Ancestral Graph.

    Notation:
    X --(k)--> Y: X causes Y with lag k time steps
    X --(k1,k2)--> Y: Bidirectional causal relationship with lags k1 and k2
    X o-(k)--> Y: X causes Y with lag k, but latent confounding possible
    """
    source: str
    target: str
    source_end: EdgeEndpointType
    target_end: EdgeEndpointType
    lag: int  # Optimal causal lag
    lag_uncertainty: float = 0.0
    confidence: float = 1.0
    granger_p_value: float = 1.0
    fci_p_value: float = 1.0

    def __str__(self):
        s_end = self.source_end.value[0]
        t_end = self.target_end.value[0]
        return f"{self.source} {s_end}-{self.t_end}({self.lag}) {self.target}"

    def is_bidirectional(self) -> bool:
        """Check if this is part of a feedback loop"""
        return (self.source_end == EdgeEndpointType.ARROW and
                self.target_end == EdgeEndpointType.ARROW)

    def is_directed(self) -> bool:
        """Check if this is a directed edge (causal)"""
        return (self.source_end == EdgeEndpointType.TAIL and
                self.target_end == EdgeEndpointType.ARROW)

    def has_latent_confounding(self) -> bool:
        """Check if this edge may involve latent confounders"""
        return (self.source_end == EdgeEndpointType.CIRCLE or
                self.target_end == EdgeEndpointType.CIRCLE)


@dataclass
class CausalChangePoint:
    """Represents a point where causal structure changes"""
    time_index: int
    confidence: float
    edges_added: List[str] = field(default_factory=list)
    edges_removed: List[str] = field(default_factory=list)
    edges_changed: List[str] = field(default_factory=list)
    physical_interpretation: str = ""


@dataclass
class TimeLaggedPAG:
    """
    Partial Ancestral Graph with temporal information.

    Extends v98 PAG with time lag information for each edge.
    """
    nodes: Set[str] = field(default_factory=set)
    edges: List[TimeLaggedPAGEdge] = field(default_factory=list)
    latent_variables: Set[str] = field(default_factory=set)
    change_points: List[CausalChangePoint] = field(default_factory=list)

    def add_edge(self, edge: TimeLaggedPAGEdge):
        if edge not in self.edges:
            self.edges.append(edge)
            self.nodes.add(edge.source)
            self.nodes.add(edge.target)

    def get_edge(self, source: str, target: str) -> Optional[TimeLaggedPAGEdge]:
        for edge in self.edges:
            if edge.source == source and edge.target == target:
                return edge
        return None

    def get_feedback_loops(self) -> List[Tuple[str, str]]:
        """Identify feedback loops (bidirectional causal relationships)"""
        loops = []
        for edge1 in self.edges:
            for edge2 in self.edges:
                if (edge1.source == edge2.target and
                    edge1.target == edge2.source and
                    edge1.is_directed() and edge2.is_directed()):
                    loops.append((edge1.source, edge1.target))
        return loops

    def get_optimal_lags(self) -> Dict[Tuple[str, str], int]:
        """Get optimal lag for each directed edge"""
        return {(e.source, e.target): e.lag for e in self.edges
                if e.is_directed()}

    def to_dict(self) -> Dict:
        return {
            'nodes': list(self.nodes),
            'edges': [
                {
                    'source': e.source,
                    'target': e.target,
                    'source_end': e.source_end.value,
                    'target_end': e.target_end.value,
                    'lag': e.lag,
                    'confidence': e.confidence,
                    'is_bidirectional': e.is_bidirectional(),
                    'has_latent': e.has_latent_confounding()
                }
                for e in self.edges
            ],
            'feedback_loops': self.get_feedback_loops(),
            'change_points': [
                {
                    'time_index': cp.time_index,
                    'confidence': cp.confidence,
                    'physical_interpretation': cp.physical_interpretation
                }
                for cp in self.change_points
            ],
            'n_edges': len(self.edges),
            'n_feedback_loops': len(self.get_feedback_loops())
        }


class TemporalFCIDiscovery:
    """
    Time-Varying FCI (Fast Causal Inference) for temporal data.

    Extends v98 FCI to handle:
    - Time-lagged causal relationships
    - Feedback loop detection
    - Time-varying causal structure
    """

    def __init__(self, max_lag: int = 10, alpha: float = 0.05):
        """
        Initialize TemporalFCIDiscovery.

        Args:
            max_lag: Maximum time lag to test
            alpha: Significance level for independence tests
        """
        self.max_lag = max_lag
        self.alpha = alpha

        # Try to import v98 FCI
        try:
            from stan_core.capabilities.v98_fci_causal_discovery import FCIDiscovery
            self.fci = FCIDiscovery(alpha=alpha)
            self.fci_available = True
            # CI test will be initialized as fallback since V98 doesn't export it
            self._init_fallback_methods()
        except ImportError:
            # V98 FCI is optional, silently use fallback
            self.fci_available = False
            self.fci = None
            self._init_fallback_methods()

    def _init_fallback_methods(self):
        """Initialize fallback methods when V98 is not available"""
        def fisher_z_test(x, y, z=None, alpha=0.05):
            """Fallback Fisher's Z test for conditional independence"""
            if z is None:
                # Partial correlation
                n = len(x)
                r = np.corrcoef(x, y)[0, 1]
                if np.isnan(r):
                    return True, 1.0
                z_score = np.abs(r * np.sqrt(n - 3) / np.sqrt(1 - r**2))
                p_value = 2 * (1 - stats.norm.cdf(z_score))
                return p_value > alpha, p_value
            else:
                # Conditional correlation (simplified)
                residual_x = x - np.mean(x)
                residual_y = y - np.mean(y)
                residual_z = z - np.mean(z)
                r_xz = np.corrcoef(residual_x, residual_z)[0, 1]
                r_yz = np.corrcoef(residual_y, residual_z)[0, 1]
                r_xy_given_z = np.corrcoef(
                    residual_x - r_xz * residual_z,
                    residual_y - r_yz * residual_z
                )[0, 1]
                if np.isnan(r_xy_given_z):
                    return True, 1.0
                n = len(x)
                z_score = np.abs(r_xy_given_z * np.sqrt(n - 4))
                p_value = 2 * (1 - stats.norm.cdf(z_score))
                return p_value > alpha, p_value

        # Create a simple class for the CI test
        class ConditionalIndependenceTest:
            def test(self, x, y, z=None, alpha=0.05):
                return fisher_z_test(x, y, z, alpha)

        self.ci_test = ConditionalIndependenceTest()

    def discover_temporal_causal_structure(
        self,
        data: np.ndarray,
        variable_names: List[str],
        detect_feedback_loops: bool = True
    ) -> TimeLaggedPAG:
        """
        Discover time-lagged causal structure.

        Args:
            data: (T, N) array - T time points, N variables
            variable_names: List of variable names
            detect_feedback_loops: Whether to detect feedback loops

        Returns:
            TimeLaggedPAG with discovered structure
        """
        T, N = data.shape

        # Normalize data
        data_norm = (data - np.mean(data, axis=0)) / np.std(data, axis=0)

        # Storage for results across lags
        lag_results = []

        # For each lag, test all variable pairs
        for lag in range(1, self.max_lag + 1):
            # Create lagged dataset
            data_lagged = np.zeros((T - lag, 2 * N))
            for i in range(N):
                data_lagged[:, i] = data_norm[lag:T, i]  # Effect (later time)
                data_lagged[:, N + i] = data_norm[:T-lag, i]  # Cause (earlier time)

            # Test conditional independence at this lag
            lag_edges = []
            for i in range(N):
                for j in range(N):
                    if i == j:
                        continue

                    x = data_lagged[:, N + i]  # Potential cause
                    y = data_lagged[:, i]      # Potential effect

                    # Condition on all other variables
                    z_indices = [k for k in range(N) if k not in [i, j]]
                    if z_indices:
                        z = data_lagged[:, N + z_indices[0]]  # First conditioning variable
                        # Simplified: condition on one variable
                        independent, p_value = self.ci_test.test(x, y, z, self.alpha)
                    else:
                        independent, p_value = self.ci_test.test(x, y, alpha=self.alpha)

                    if not independent:
                        lag_edges.append({
                            'source': variable_names[i],
                            'target': variable_names[j],
                            'lag': lag,
                            'p_value': p_value,
                            'correlation': np.corrcoef(x, y)[0, 1]
                        })

            lag_results.append({'lag': lag, 'edges': lag_edges})

        # Find optimal lag for each pair and build PAG
        return self._build_optimal_pag(lag_results, detect_feedback_loops)

    def _build_optimal_pag(
        self,
        lag_results: List[Dict],
        detect_feedback_loops: bool
    ) -> TimeLaggedPAG:
        """Build PAG with optimal lags for each causal relationship"""
        pag = TimeLaggedPAG()

        # Track best evidence for each (source, target, direction) combination
        edge_evidence = {}  # (source, target, direction) -> best_evidence

        for lag_result in lag_results:
            lag = lag_result['lag']
            for edge_info in lag_result['edges']:
                source = edge_info['source']
                target = edge_info['target']
                p_value = edge_info['p_value']
                correlation = edge_info['correlation']

                # Check if this is better than previous evidence
                key = (source, target, 'forward')
                if key not in edge_evidence or p_value < edge_evidence[key]['p_value']:
                    edge_evidence[key] = {
                        'lag': lag,
                        'p_value': p_value,
                        'correlation': correlation,
                        'direction': 'forward'
                    }

        # Add edges using best evidence
        for key, evidence in edge_evidence.items():
            source, target, direction = key

            # Determine endpoint types
            # Start with circle (uncertain), refine based on evidence
            if evidence['p_value'] < 0.01:
                source_end = EdgeEndpointType.TAIL
                target_end = EdgeEndpointType.ARROW
            elif evidence['p_value'] < 0.05:
                source_end = EdgeEndpointType.CIRCLE
                target_end = EdgeEndpointType.ARROW
            else:
                source_end = EdgeEndpointType.CIRCLE
                target_end = EdgeEndpointType.CIRCLE

            edge = TimeLaggedPAGEdge(
                source=source,
                target=target,
                source_end=source_end,
                target_end=target_end,
                lag=evidence['lag'],
                confidence=1.0 - evidence['p_value'],
                fci_p_value=evidence['p_value']
            )
            pag.add_edge(edge)

        # Detect feedback loops
        if detect_feedback_loops:
            self._detect_feedback_loops(pag)

        return pag

    def _detect_feedback_loops(self, pag: TimeLaggedPAG):
        """Detect feedback loops in the causal graph"""
        # Check for bidirectional relationships
        feedback_pairs = []

        for edge1 in pag.edges:
            if edge1.is_directed():
                # Check if reverse edge exists
                for edge2 in pag.edges:
                    if (edge2.source == edge1.target and
                        edge2.target == edge1.source and
                        edge2.is_directed()):
                        feedback_pairs.append((edge1.source, edge1.target))

                        # Mark as feedback loop
                        edge1.is_bidirectional = True
                        edge2.is_bidirectional = True
                        break

        return feedback_pairs

    def detect_change_points(
        self,
        data: np.ndarray,
        variable_names: List[str],
        window_size: int = 100,
        step_size: int = 50,
        threshold: float = 0.3
    ) -> List[CausalChangePoint]:
        """
        Detect points where causal structure changes over time.

        Args:
            data: (T, N) time series
            variable_names: Variable names
            window_size: Size of sliding window
            step_size: Step between windows
            threshold: Minimum change magnitude to flag

        Returns:
            List of CausalChangePoint objects
        """
        T, N = data.shape
        change_points = []

        # Analyze causal structure in each window
        prev_pag = None
        prev_time_idx = 0

        for t in range(0, T - window_size, step_size):
            window_data = data[t:t + window_size, :]

            # Discover causal structure in this window
            curr_pag = self.discover_temporal_causal_structure(
                window_data,
                variable_names,
                detect_feedback_loops=False
            )

            # Compare with previous window
            if prev_pag is not None:
                change_score = self._compute_graph_distance(prev_pag, curr_pag)

                if change_score > threshold:
                    change_point = CausalChangePoint(
                        time_index=t,
                        confidence=min(change_score, 1.0),
                        physical_interpretation=f"Causal structure changed at t={t}"
                    )
                    change_points.append(change_point)

            prev_pag = curr_pag
            prev_time_idx = t

        return change_points

    def _compute_graph_distance(
        self,
        pag1: TimeLaggedPAG,
        pag2: TimeLaggedPAG
    ) -> float:
        """Compute distance between two PAGs"""
        # Simple edge-based distance metric
        edges1 = set((e.source, e.target) for e in pag1.edges if e.is_directed())
        edges2 = set((e.source, e.target) for e in pag2.edges if e.is_directed())

        if not edges1 and not edges2:
            return 0.0

        union = edges1 | edges2
        intersection = edges1 & edges2

        if not union:
            return 0.0

        # Jaccard distance
        return 1.0 - len(intersection) / len(union)

    def compute_optimal_lags(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> Dict[Tuple[str, str], Dict]:
        """
        Compute optimal causal lags for all variable pairs.

        Returns:
            Dictionary mapping (source, target) to lag information
        """
        T, N = data.shape
        optimal_lags = {}

        for i in range(N):
            for j in range(N):
                if i == j:
                    continue

                # Test all lags
                correlations = []
                for lag in range(1, self.max_lag + 1):
                    if lag >= T:
                        break

                    x = data[:T-lag, i]
                    y = data[lag:T, j]

                    if len(x) > 10 and len(y) > 10:
                        corr, p_value = stats.pearsonr(x, y)
                        if not np.isnan(corr):
                            correlations.append({
                                'lag': lag,
                                'correlation': corr,
                                'p_value': p_value,
                                'abs_corr': abs(corr)
                            })

                if correlations:
                    # Find lag with maximum absolute correlation
                    best = max(correlations, key=lambda x: x['abs_corr'])
                    optimal_lags[(variable_names[i], variable_names[j])] = best

        return optimal_lags


class GrangerFCIHybrid:
    """
    Hybrid approach combining Granger causality with FCI.

    Granger causality provides temporal precedence (X[t-k] Granger-causes Y[t])
    FCI provides latent confounder detection
    Together they provide robust temporal causal discovery.
    """

    def __init__(self, max_lag: int = 5, alpha: float = 0.05):
        """
        Initialize GrangerFCIHybrid.

        Args:
            max_lag: Maximum lag for VAR model
            alpha: Significance level
        """
        self.max_lag = max_lag
        self.alpha = alpha

        # Try to import required libraries
        try:
            from statsmodels.tsa.api import VAR
            self.VAR_available = True
        except ImportError:
            warnings.warn("statsmodels not available, using fallback")
            self.VAR_available = False

        # Initialize temporal FCI
        self.tvfci = TemporalFCIDiscovery(max_lag=max_lag, alpha=alpha)

    def discover_hybrid(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> TimeLaggedPAG:
        """
        Discover causal structure using Granger-FCI hybrid.

        Args:
            data: (T, N) time series
            variable_names: Variable names

        Returns:
            TimeLaggedPAG with Granger-enhanced edges
        """
        # Step 1: Granger causality analysis
        granger_edges = self._granger_causality_analysis(data, variable_names)

        # Step 2: FCI on residuals to detect latent confounders
        fci_edges = self._fci_on_residuals(data, variable_names, granger_edges)

        # Step 3: Combine results
        return self._combine_granger_fci(granger_edges, fci_edges)

    def _granger_causality_analysis(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[Dict]:
        """Perform Granger causality analysis"""
        T, N = data.shape
        edges = []

        for i in range(N):
            for j in range(N):
                if i == j:
                    continue

                # Fit VAR model
                if self.VAR_available:
                    try:
                        from statsmodels.tsa.api import VAR
                        model = VAR(data[:, [i, j]])
                        results = model.fit(maxlags=self.max_lag, ic='aic')

                        # Test Granger causality
                        # i causes j if coefficients on i are significant
                        if results.coefs is not None:
                            # Check if i Granger-causes j
                            for lag in range(results.k_ar):
                                coef = results.coefs[lag, 1, 0]  # [i->j] coefficient
                                se = results.stderr[lag, 1, 0]
                                if se > 0:
                                    t_stat = coef / se
                                    p_value = 2 * (1 - stats.norm.cdf(abs(t_stat)))
                                    if p_value < self.alpha:
                                        edges.append({
                                            'source': variable_names[i],
                                            'target': variable_names[j],
                                            'lag': lag + 1,
                                            'p_value': p_value,
                                            'method': 'granger'
                                        })
                    except Exception as e:
                        # Fall back to correlation analysis
                        pass

        # Fallback: simple correlation-based lag detection
        if not edges:
            for i in range(N):
                for j in range(N):
                    if i == j:
                        continue

                    best_corr = 0
                    best_lag = 1

                    for lag in range(1, min(self.max_lag + 1, T // 2)):
                        if lag >= T:
                            break
                        x = data[:T-lag, i]
                        y = data[lag:T, j]

                        if len(x) > 10 and len(y) > 10:
                            corr, p_value = stats.pearsonr(x, y)
                            if abs(corr) > abs(best_corr):
                                best_corr = corr
                                best_lag = lag

                    if abs(best_corr) > 0.3:
                        edges.append({
                            'source': variable_names[i],
                            'target': variable_names[j],
                            'lag': best_lag,
                            'p_value': 2 * (1 - stats.norm.cdf(abs(best_corr) * np.sqrt(len(data) - 3))),
                            'method': 'correlation'
                        })

        return edges

    def _fci_on_residuals(
        self,
        data: np.ndarray,
        variable_names: List[str],
        granger_edges: List[Dict]
    ) -> List[Dict]:
        """Apply FCI to residuals to detect latent confounding"""
        # Simplified: mark edges as potentially confounded
        # if they don't meet strict significance threshold
        refined_edges = []

        for edge in granger_edges:
            if edge['p_value'] < 0.01:
                # Strong evidence - directed
                edge['has_latent'] = False
            elif edge['p_value'] < 0.05:
                # Moderate evidence - may have latent confounding
                edge['has_latent'] = True
            else:
                # Weak evidence - mark as uncertain
                edge['has_latent'] = True

            refined_edges.append(edge)

        return refined_edges

    def _combine_granger_fci(
        self,
        granger_edges: List[Dict],
        fci_edges: List[Dict]
    ) -> TimeLaggedPAG:
        """Combine Granger and FCI results into unified PAG"""
        pag = TimeLaggedPAG()

        for edge in granger_edges:
            if edge.get('has_latent', False):
                source_end = EdgeEndpointType.CIRCLE
            else:
                source_end = EdgeEndpointType.TAIL

            target_end = EdgeEndpointType.ARROW

            tl_edge = TimeLaggedPAGEdge(
                source=edge['source'],
                target=edge['target'],
                source_end=source_end,
                target_end=target_end,
                lag=edge['lag'],
                confidence=1.0 - edge['p_value'],
                granger_p_value=edge['p_value']
            )
            pag.add_edge(tl_edge)

        return pag


# Factory functions for easy integration

def create_temporal_fci_discovery(
    max_lag: int = 10,
    alpha: float = 0.05
) -> TemporalFCIDiscovery:
    """
    Factory function to create TemporalFCIDiscovery.

    Args:
        max_lag: Maximum time lag to test
        alpha: Significance level

    Returns:
        TemporalFCIDiscovery instance
    """
    return TemporalFCIDiscovery(max_lag=max_lag, alpha=alpha)


def create_granger_fci_hybrid(
    max_lag: int = 5,
    alpha: float = 0.05
) -> GrangerFCIHybrid:
    """
    Factory function to create GrangerFCIHybrid.

    Args:
        max_lag: Maximum lag for VAR model
        alpha: Significance level

    Returns:
        GrangerFCIHybrid instance
    """
    return GrangerFCIHybrid(max_lag=max_lag, alpha=alpha)


# Convenience functions for common workflows

def analyze_temporal_dynamics(
    data: np.ndarray,
    variable_names: List[str],
    max_lag: int = 10
) -> Dict[str, Any]:
    """
    Complete temporal causal analysis.

    This function:
    1. Discovers optimal lags for all variable pairs
    2. Identifies feedback loops
    3. Detects change points
    4. Generates interpretable summary

    Args:
        data: (T, N) time series
        variable_names: Variable names
        max_lag: Maximum lag to test

    Returns:
        Dictionary with analysis results
    """
    tvfci = create_temporal_fci_discovery(max_lag=max_lag)

    # Discover temporal causal structure
    pag = tvfci.discover_temporal_causal_structure(
        data, variable_names, detect_feedback_loops=True
    )

    # Compute optimal lags
    optimal_lags = tvfci.compute_optimal_lags(data, variable_names)

    # Detect change points
    change_points = tvfci.detect_change_points(data, variable_names)

    return {
        'pag': pag,
        'optimal_lags': optimal_lags,
        'feedback_loops': pag.get_feedback_loops(),
        'change_points': change_points,
        'summary': _generate_temporal_summary(pag, optimal_lags, change_points)
    }


def _generate_temporal_summary(
    pag: TimeLaggedPAG,
    optimal_lags: Dict,
    change_points: List
) -> str:
    """Generate human-readable summary of temporal analysis"""
    summary = []

    summary.append("=== TEMPORAL CAUSAL DISCOVERY RESULTS ===\n")

    # Optimal lags
    summary.append("OPTIMAL CAUSAL LAGS:")
    for (source, target), info in optimal_lags.items():
        summary.append(f"  {source} → {target} (lag: {info['lag']} time steps)")

    # Feedback loops
    loops = pag.get_feedback_loops()
    if loops:
        summary.append("\nFEEDBACK LOOPS DETECTED:")
        for source, target in loops:
            summary.append(f"  {source} ↔ {target}")

    # Change points
    if change_points:
        summary.append(f"\nCHANGE POINTS DETECTED: {len(change_points)}")
        for cp in change_points:
            summary.append(f"  t={cp.time_idx}: {cp.physical_interpretation}")

    return "\n".join(summary)


# Compatibility aliases for common naming patterns
TemporalCausalDiscovery = TemporalFCIDiscovery
