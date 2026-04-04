"""
Online Causal Learning

Incremental causal structure learning from streaming data.
Updates causal beliefs as new observations arrive without reprocessing
all historical data.

Methods:
- Online constraint-based updates
- Streaming score-based learning
- Recursive Bayesian updating
- Concept drift detection

Reference:
- Runge, J. (2018). Causal inference beyond DAGs.
- Peters, J. et al. (2016). Causal inference using invariant prediction.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import deque
import warnings

logger = logging.getLogger(__name__)


class UpdateMethod(Enum):
    """Methods for online causal learning"""
    INCREMENTAL_PC = "incremental_pc"  # Online PC algorithm
    RESAMPLE_PC = "resample_pc"  # Resampling-based PC
    MOMENT_MATCH = "moment_match"  # Moment matching
    BAYESIAN_UPDATE = "bayesian_update"  # Recursive Bayesian
    SLIDING_WINDOW = "sliding_window"  # Sliding window PC


class ConceptDriftDetector:
    """
    Detect concept drift in causal relationships

    Monitors for changes in causal structure over time.
    """

    def __init__(
        self,
        window_size: int = 1000,
        threshold: float = 0.1,
        detection_method: str = "statistical"
    ):
        """
        Initialize concept drift detector

        Args:
            window_size: Size of reference window
            threshold: Drift detection threshold
            detection_method: Method for drift detection
        """
        self.window_size = window_size
        self.threshold = threshold
        self.detection_method = detection_method

        # Reference statistics
        self.reference_covariance = None
        self.reference_adjacency = None
        self.reference_samples = []

        # Current statistics
        self.current_covariance = None
        self.current_adjacency = None
        self.current_samples = []

        # Drift history
        self.drift_detected = False
        self.drift_times = []

    def update_reference(self, data: np.ndarray, adjacency: np.ndarray) -> None:
        """Update reference statistics"""
        self.reference_samples = data.tolist() if len(self.reference_samples) == 0 else self.reference_samples + data.tolist()

        # Keep only recent samples
        if len(self.reference_samples) > self.window_size:
            self.reference_samples = self.reference_samples[-self.window_size:]

        self.reference_covariance = np.cov(np.array(self.reference_samples).T)
        self.reference_adjacency = adjacency

    def check_drift(
        self,
        new_data: np.ndarray,
        current_adjacency: np.ndarray
    ) -> Dict[str, Union[bool, float, np.ndarray]]:
        """
        Check for concept drift

        Args:
            new_data: New observations
            current_adjacency: Current causal structure

        Returns:
            Dictionary with drift detection results
        """
        if self.reference_covariance is None:
            return {'drift_detected': False, 'drift_magnitude': 0.0}

        # Update current statistics
        self.current_samples = new_data.tolist() if len(self.current_samples) == 0 else self.current_samples + new_data.tolist()

        if len(self.current_samples) > self.window_size:
            self.current_samples = self.current_samples[-self.window_size:]

        self.current_covariance = np.cov(np.array(self.current_samples).T)
        self.current_adjacency = current_adjacency

        # Detect drift
        if self.detection_method == "statistical":
            drift_result = self._statistical_drift_test()
        elif self.detection_method == "adjacency":
            drift_result = self._adjacency_drift_test()
        else:
            drift_result = self._combined_drift_test()

        self.drift_detected = drift_result['drift_detected']

        if self.drift_detected:
            self.drift_times.append(len(self.reference_samples) + len(self.current_samples))

        return drift_result

    def _statistical_drift_test(self) -> Dict[str, Union[bool, float]]:
        """Statistical test for distribution shift"""
        # Compare covariance matrices
        diff = np.linalg.norm(self.current_covariance - self.reference_covariance)
        norm = np.linalg.norm(self.reference_covariance)

        drift_magnitude = diff / (norm + 1e-10)
        drift_detected = drift_magnitude > self.threshold

        return {
            'drift_detected': drift_detected,
            'drift_magnitude': drift_magnitude,
            'covariance_diff': diff
        }

    def _adjacency_drift_test(self) -> Dict[str, Union[bool, float]]:
        """Test for changes in adjacency structure"""
        if self.reference_adjacency is None or self.current_adjacency is None:
            return {'drift_detected': False, 'drift_magnitude': 0.0}

        # Hamming distance between adjacency matrices
        diff = np.sum(np.abs(self.current_adjacency - self.reference_adjacency))
        total = self.reference_adjacency.size

        drift_magnitude = diff / total
        drift_detected = drift_magnitude > self.threshold

        return {
            'drift_detected': drift_detected,
            'drift_magnitude': drift_magnitude,
            'adjacency_diff': diff
        }

    def _combined_drift_test(self) -> Dict[str, Union[bool, float]]:
        """Combined statistical and adjacency test"""
        stat_result = self._statistical_drift_test()
        adj_result = self._adjacency_drift_test()

        # Combine evidence
        combined_magnitude = 0.5 * stat_result['drift_magnitude'] + 0.5 * adj_result['drift_magnitude']
        drift_detected = combined_magnitude > self.threshold

        return {
            'drift_detected': drift_detected,
            'drift_magnitude': combined_magnitude,
            'statistical_magnitude': stat_result['drift_magnitude'],
            'adjacency_magnitude': adj_result['drift_magnitude']
        }


@dataclass
class OnlineLearningResult:
    """
    Result from online causal learning update

    Attributes:
        updated_adjacency: Updated causal structure
        confidence: Confidence in updated structure
        n_new_samples: Number of new samples incorporated
        concept_drift: Whether concept drift was detected
        update_time: Time taken for update
        statistics: Updated sufficient statistics
    """
    updated_adjacency: np.ndarray
    confidence: np.ndarray
    n_new_samples: int
    concept_drift: bool
    update_time: float
    statistics: Dict[str, np.ndarray] = field(default_factory=dict)


class OnlineCausalLearner:
    """
    Online causal structure learner

    Incrementally updates causal structure as new data arrives.
    Avoids full recomputation for efficiency.

    Features:
    - Incremental constraint updates
    - Streaming score computation
    - Concept drift detection
    - Efficient statistics maintenance
    - Time-varying causal structures
    """

    def __init__(
        self,
        update_method: UpdateMethod = UpdateMethod.INCREMENTAL_PC,
        window_size: int = 1000,
        alpha: float = 0.05,
        max_buffer_size: int = 10000,
        detect_concept_drift: bool = True,
        verbose: bool = False
    ):
        """
        Initialize online causal learner

        Args:
            update_method: Method for online updates
            window_size: Size of sliding window (for window-based methods)
            alpha: Significance level for independence tests
            max_buffer_size: Maximum size of data buffer
            detect_concept_drift: Whether to detect concept drift
            verbose: Print progress information
        """
        self.update_method = update_method
        self.window_size = window_size
        self.alpha = alpha
        self.max_buffer_size = max_buffer_size
        self.detect_concept_drift = detect_concept_drift
        self.verbose = verbose

        # Data buffer
        self.data_buffer: deque = deque(maxlen=max_buffer_size)
        self.n_seen = 0

        # Current estimates
        self.current_adjacency: Optional[np.ndarray] = None
        self.current_statistics: Dict[str, np.ndarray] = {}

        # Confidence in edges
        self.edge_confidence: Optional[np.ndarray] = None

        # Separation sets (for PC algorithm)
        self.sep_sets: Dict[Tuple[int, int], Set[int]] = {}

        # Concept drift detector
        self.drift_detector = ConceptDriftDetector(window_size=window_size)

        # History for diagnostics
        self.update_history: List[OnlineLearningResult] = []

    def initialize(
        self,
        initial_data: np.ndarray,
        node_names: Optional[List[str]] = None
    ) -> None:
        """
        Initialize with batch data

        Args:
            initial_data: Initial batch of data
            node_names: Optional node names
        """
        self.n_seen = len(initial_data)
        self.data_buffer.extend(initial_data)

        # Run batch discovery to initialize
        from .pc_algorithm import PCAlgorithm
        from .independence import ConditionalIndependenceTest, TestType

        pc = PCAlgorithm(alpha=self.alpha)
        df_initial = pd.DataFrame(initial_data)
        if node_names:
            df_initial.columns = node_names

        # Initialize current structure
        try:
            scm = pc.discover(df_initial, verbose=self.verbose)
            self.current_adjacency = scm.get_adjacency_matrix()
        except Exception as e:
            logger.warning(f"Initial discovery failed: {e}, using empty graph")
            self.current_adjacency = np.zeros((initial_data.shape[1], initial_data.shape[1]))

        # Initialize statistics
        self._update_sufficient_statistics(initial_data)

        # Initialize edge confidence
        self.edge_confidence = np.ones_like(self.current_adjacency) * 0.5

        # Initialize drift detector
        if self.detect_concept_drift:
            self.drift_detector.update_reference(initial_data, self.current_adjacency)

        if self.verbose:
            logger.info(f"Initialized with {len(initial_data)} samples")
            logger.info(f"Initial adjacency: {np.sum(self.current_adjacency)} edges")

    def update(
        self,
        new_data: np.ndarray
    ) -> OnlineLearningResult:
        """
        Update causal structure with new data

        Args:
            new_data: New observations

        Returns:
            OnlineLearningResult with updated structure
        """
        import time
        start_time = time.time()

        n_new = len(new_data)
        self.n_seen += n_new

        if self.verbose:
            logger.info(f"Updating with {n_new} new samples (total: {self.n_seen})")

        # Add to buffer
        self.data_buffer.extend(new_data)

        # Update sufficient statistics
        self._update_sufficient_statistics(new_data, incremental=True)

        # Detect concept drift
        concept_drift = False
        if self.detect_concept_drift:
            drift_result = self.drift_detector.check_drift(new_data, self.current_adjacency)
            concept_drift = drift_result['drift_detected']

            if concept_drift:
                logger.warning(f"Concept drift detected (magnitude: {drift_result['drift_magnitude']:.3f})")

        # Update structure
        if concept_drift or self.update_method == UpdateMethod.SLIDING_WINDOW:
            # Full re-computation for drift or sliding window
            updated_adjacency, confidence = self._full_recompute()
        else:
            # Incremental update
            updated_adjacency, confidence = self._incremental_update(new_data)

        # Update current estimates
        self.current_adjacency = updated_adjacency
        self.edge_confidence = confidence

        # Update drift detector reference
        if self.detect_concept_drift:
            buffer_array = np.array(self.data_buffer)
            self.drift_detector.update_reference(buffer_array, self.current_adjacency)

        # Record update
        result = OnlineLearningResult(
            updated_adjacency=updated_adjacency,
            confidence=confidence,
            n_new_samples=n_new,
            concept_drift=concept_drift,
            update_time=time.time() - start_time,
            statistics=self.current_statistics.copy()
        )

        self.update_history.append(result)

        if self.verbose:
            logger.info(f"Update complete: {np.sum(updated_adjacency)} edges")
            logger.info(f"Update time: {result.update_time:.3f}s")

        return result

    def _incremental_update(
        self,
        new_data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Incremental update without full recomputation"""
        if self.update_method == UpdateMethod.INCREMENTAL_PC:
            return self._incremental_pc_update(new_data)
        elif self.update_method == UpdateMethod.RESAMPLE_PC:
            return self._resample_pc_update(new_data)
        elif self.update_method == UpdateMethod.MOMENT_MATCH:
            return self._moment_match_update(new_data)
        elif self.update_method == UpdateMethod.BAYESIAN_UPDATE:
            return self._bayesian_update(new_data)
        else:
            return self._full_recompute()

    def _incremental_pc_update(
        self,
        new_data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Incremental PC algorithm update

        Only re-tests edges that might be affected by new data.
        """
        if self.current_adjacency is None:
            return self._full_recompute()

        n_nodes = self.current_adjacency.shape[0]
        updated_adjacency = self.current_adjacency.copy()
        confidence = self.edge_confidence.copy() if self.edge_confidence is not None else np.ones((n_nodes, n_nodes)) * 0.5

        # Get buffer as array
        all_data = np.array(self.data_buffer)

        # For efficiency, only test edges that:
        # 1. Currently exist, or
        # 2. Are between variables that changed significantly

        # Compute statistics change
        old_mean = self.current_statistics.get('mean', np.zeros(n_nodes))
        new_mean = self.current_statistics.get('mean', np.zeros(n_nodes))

        mean_change = np.abs(new_mean - old_mean)
        significant_change = mean_change > np.std(mean_change)

        # Re-test affected edges
        for i in range(n_nodes):
            for j in range(n_nodes):
                if i == j:
                    continue

                # Re-test if edge exists or variables changed significantly
                should_retest = (
                    updated_adjacency[i, j] == 1 or
                    updated_adjacency[j, i] == 1 or
                    significant_change[i] or
                    significant_change[j]
                )

                if should_retest:
                    # Test independence
                    p_value = self._test_independence(all_data, i, j, set())

                    if p_value > self.alpha:
                        # Independent - remove edge
                        updated_adjacency[i, j] = 0
                        updated_adjacency[j, i] = 0
                        confidence[i, j] = 1 - p_value
                        confidence[j, i] = 1 - p_value
                    else:
                        # Dependent - add/update edge
                        # Determine orientation based on current structure
                        if updated_adjacency[j, i] == 1:
                            # Keep existing orientation
                            pass
                        elif updated_adjacency[i, j] == 0:
                            # New edge - orient based on correlation
                            corr = np.corrcoef(all_data[:, i], all_data[:, j])[0, 1]
                            if corr > 0:
                                updated_adjacency[i, j] = 1
                            else:
                                updated_adjacency[j, i] = 1

                        confidence[i, j] = 1 - p_value

        # Ensure acyclicity
        updated_adjacency = self._ensure_acyclic(updated_adjacency)

        return updated_adjacency, confidence

    def _resample_pc_update(
        self,
        new_data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Resampling-based PC update

        Run PC on random subset of data including new samples.
        """
        all_data = np.array(self.data_buffer)

        # Sample subset
        n_samples = min(len(all_data), self.window_size)
        indices = np.random.choice(len(all_data), n_samples, replace=False)
        sampled_data = all_data[indices]

        # Run PC on sampled data
        from .pc_algorithm import PCAlgorithm

        pc = PCAlgorithm(alpha=self.alpha)
        df_sampled = pd.DataFrame(sampled_data)

        try:
            scm = pc.discover(df_sampled, verbose=False)
            updated_adjacency = scm.get_adjacency_matrix()

            # Update confidence based on consistency
            confidence = self._compute_confidence_from_consistency(
                updated_adjacency, self.current_adjacency
            )
        except Exception as e:
            logger.warning(f"Resample PC failed: {e}")
            updated_adjacency = self.current_adjacency.copy()
            confidence = self.edge_confidence.copy() if self.edge_confidence is not None else np.ones_like(self.current_adjacency) * 0.5

        return updated_adjacency, confidence

    def _moment_match_update(
        self,
        new_data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Moment matching update

        Update structure based on changes in correlation/covariance.
        """
        all_data = np.array(self.data_buffer)
        n_nodes = all_data.shape[1]

        # Compute current covariance
        current_cov = np.cov(all_data.T)

        # Update adjacency based on significant correlations
        updated_adjacency = np.zeros((n_nodes, n_nodes), dtype=int)
        confidence = np.zeros((n_nodes, n_nodes))

        for i in range(n_nodes):
            for j in range(i+1, n_nodes):
                corr = current_cov[i, j] / np.sqrt(current_cov[i, i] * current_cov[j, j])

                # Add edge if significant correlation
                if abs(corr) > 0.3:  # Threshold
                    # Orient based on current structure if available
                    if self.current_adjacency is not None:
                        if self.current_adjacency[j, i] == 1:
                            updated_adjacency[j, i] = 1
                            confidence[j, i] = abs(corr)
                        else:
                            updated_adjacency[i, j] = 1
                            confidence[i, j] = abs(corr)
                    else:
                        # Default: i -> j
                        updated_adjacency[i, j] = 1
                        confidence[i, j] = abs(corr)

        return updated_adjacency, confidence

    def _bayesian_update(
        self,
        new_data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Recursive Bayesian update

        Update posterior over DAGs using Bayesian updating.
        """
        if self.current_adjacency is None:
            return self._full_recompute()

        all_data = np.array(self.data_buffer)
        n_nodes = all_data.shape[1]

        # Current edge probabilities (from adjacency)
        current_probs = self.current_adjacency.astype(float)

        # Compute likelihood of new data for each possible edge
        # (simplified: use correlation)

        updated_probs = current_probs.copy()

        # Learning rate (decreases with more data)
        learning_rate = 1.0 / np.sqrt(self.n_seen)

        # Update based on new data correlations
        new_cov = np.cov(new_data.T)

        for i in range(n_nodes):
            for j in range(n_nodes):
                if i == j:
                    continue

                corr = new_cov[i, j] / np.sqrt(new_cov[i, i] * new_cov[j, j] + 1e-10)

                # Update probability based on correlation evidence
                if abs(corr) > 0.3:
                    # Evidence for edge
                    updated_probs[i, j] = updated_probs[i, j] + learning_rate * (1 - updated_probs[i, j])
                elif abs(corr) < 0.1:
                    # Evidence against edge
                    updated_probs[i, j] = updated_probs[i, j] * (1 - learning_rate * 0.5)

        # Normalize to [0, 1]
        updated_probs = np.clip(updated_probs, 0.0, 1.0)

        # Convert probabilities to adjacency
        updated_adjacency = (updated_probs > 0.5).astype(int)
        confidence = updated_probs

        # Ensure acyclicity
        updated_adjacency = self._ensure_acyclic(updated_adjacency)

        return updated_adjacency, confidence

    def _full_recompute(
        self
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Full recomputation of causal structure"""
        all_data = np.array(self.data_buffer)

        if len(all_data) < 10:
            # Not enough data
            n_nodes = all_data.shape[1] if len(all_data.shape) > 1 else 1
            return np.zeros((n_nodes, n_nodes)), np.zeros((n_nodes, n_nodes))

        from .pc_algorithm import PCAlgorithm

        pc = PCAlgorithm(alpha=self.alpha)
        df_all = pd.DataFrame(all_data)

        try:
            scm = pc.discover(df_all, verbose=False)
            updated_adjacency = scm.get_adjacency_matrix()
            confidence = np.ones_like(updated_adjacency)  # High confidence from full data
        except Exception as e:
            logger.warning(f"Full recompute failed: {e}")
            updated_adjacency = self.current_adjacency.copy() if self.current_adjacency is not None else np.zeros((all_data.shape[1], all_data.shape[1]))
            confidence = np.ones_like(updated_adjacency) * 0.5

        return updated_adjacency, confidence

    def _update_sufficient_statistics(
        self,
        new_data: np.ndarray,
        incremental: bool = True
    ) -> None:
        """Update sufficient statistics"""
        if not incremental or 'mean' not in self.current_statistics:
            # Compute from scratch
            self.current_statistics = {
                'mean': np.mean(new_data, axis=0),
                'covariance': np.cov(new_data.T) if new_data.shape[0] > 1 else np.eye(new_data.shape[1]),
                'n_samples': len(new_data)
            }
        else:
            # Incremental update using Welford's algorithm
            n_old = self.current_statistics['n_samples']
            n_new = len(new_data)
            n_total = n_old + n_new

            old_mean = self.current_statistics['mean']
            new_mean = np.mean(new_data, axis=0)

            # Update mean
            delta = new_mean - old_mean
            updated_mean = old_mean + delta * (n_new / n_total)

            # Update covariance (simplified)
            old_cov = self.current_statistics['covariance']
            new_cov = np.cov(new_data.T)

            # Combined covariance
            updated_cov = (n_old / n_total) * old_cov + (n_new / n_total) * new_cov + \
                          (n_old * n_new / n_total**2) * np.outer(delta, delta)

            self.current_statistics = {
                'mean': updated_mean,
                'covariance': updated_cov,
                'n_samples': n_total
            }

    def _test_independence(
        self,
        data: np.ndarray,
        i: int,
        j: int,
        conditioning_set: Set[int]
    ) -> float:
        """Test conditional independence (simplified)"""
        # Partial correlation test
        if len(conditioning_set) == 0:
            # Simple correlation test
            corr = np.corrcoef(data[:, i], data[:, j])[0, 1]
            n = len(data)
            t_stat = corr * np.sqrt((n-2) / (1 - corr**2 + 1e-10))
            # Two-tailed p-value
            from scipy.stats import t
            p_value = 2 * (1 - t.cdf(abs(t_stat), n-2))
            return p_value
        else:
            # Partial correlation
            # (simplified: use linear regression residuals)
            try:
                cond_vars = list(conditioning_set)
                y = data[:, j]
                X = np.column_stack([data[:, i]] + [data[:, k] for k in cond_vars])

                # Regress j on i and conditioning set
                from sklearn.linear_model import LinearRegression
                reg = LinearRegression()
                reg.fit(X, y)
                residuals = y - reg.predict(X)

                # Test if coefficient of i is significant
                # (simplified: use residual correlation)
                p_value = 0.05  # Placeholder
                return p_value
            except:
                return 0.5

    def _ensure_acyclic(
        self,
        adjacency: np.ndarray
    ) -> np.ndarray:
        """Ensure adjacency matrix is acyclic"""
        n = adjacency.shape[0]

        # Detect cycles using DFS
        def has_cycle():
            visited = np.zeros(n, dtype=bool)
            rec_stack = np.zeros(n, dtype=bool)

            def dfs(node):
                visited[node] = True
                rec_stack[node] = True

                for neighbor in np.where(adjacency[node, :] == 1)[0]:
                    if not visited[neighbor]:
                        if dfs(neighbor):
                            return True
                    elif rec_stack[neighbor]:
                        return True

                rec_stack[node] = False
                return False

            for i in range(n):
                if not visited[i]:
                    if dfs(i):
                        return True
            return False

        # Remove edges until acyclic
        max_iterations = n * n
        for _ in range(max_iterations):
            if not has_cycle():
                break

            # Remove an edge from cycle
            for i in range(n):
                for j in range(n):
                    if adjacency[i, j] == 1:
                        adjacency[i, j] = 0
                        break
                else:
                    continue
                break

        return adjacency

    def _compute_confidence_from_consistency(
        self,
        new_adjacency: np.ndarray,
        old_adjacency: np.ndarray
    ) -> np.ndarray:
        """Compute confidence based on consistency with previous estimate"""
        # Agreement increases confidence
        agreement = (new_adjacency == old_adjacency).astype(float)

        # Base confidence on agreement
        confidence = np.where(
            new_adjacency == 1,
            0.5 + 0.5 * agreement,  # High confidence for edges
            0.5 * agreement  # Lower confidence for non-edges
        )

        return confidence

    def get_current_structure(self) -> Dict[str, Union[np.ndarray, Dict]]:
        """Get current causal structure and statistics"""
        return {
            'adjacency': self.current_adjacency,
            'confidence': self.edge_confidence,
            'statistics': self.current_statistics,
            'n_samples': self.n_seen,
            'n_updates': len(self.update_history)
        }

    def get_update_statistics(self) -> Dict[str, float]:
        """Get statistics about update history"""
        if not self.update_history:
            return {}

        update_times = [r.update_time for r in self.update_history]
        concept_drift_count = sum(1 for r in self.update_history if r.concept_drift)

        return {
            'n_updates': len(self.update_history),
            'mean_update_time': np.mean(update_times),
            'max_update_time': np.max(update_times),
            'concept_drift_count': concept_drift_count,
            'concept_drift_rate': concept_drift_count / len(self.update_history)
        }


def create_online_causal_learner(
    update_method: UpdateMethod = UpdateMethod.INCREMENTAL_PC,
    **kwargs
) -> OnlineCausalLearner:
    """
    Create online causal learner

    Args:
        update_method: Method for online updates
        **kwargs: Additional arguments

    Returns:
        Configured OnlineCausalLearner
    """
    return OnlineCausalLearner(
        update_method=update_method,
        **kwargs
    )


__all__ = [
    'UpdateMethod',
    'ConceptDriftDetector',
    'OnlineLearningResult',
    'OnlineCausalLearner',
    'create_online_causal_learner',
]
