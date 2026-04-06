"""
Meta-Cognitive Monitoring System

Monitors cognitive processes, calibrates confidence,
and provides self-awareness capabilities.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time


class ProcessState(Enum):
    """States of cognitive processes."""
    IDLE = "idle"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessRecord:
    """Record of a cognitive process."""
    process_id: str
    name: str
    state: ProcessState
    start_time: float
    end_time: Optional[float] = None
    confidence: float = 0.5
    metadata: Dict[str, Any] = None


class CognitiveMonitor:
    """
    Monitor cognitive processes and system state.

    Provides:
    - Real-time process tracking
    - Confidence monitoring and calibration
    - Performance assessment
    - Resource monitoring
    """

    def __init__(self):
        self.processes: Dict[str, ProcessRecord] = {}
        self.process_counter = 0
        self.metrics: Dict[str, List[float]] = {}

    def start_process(self,
                      name: str,
                      metadata: Optional[Dict] = None) -> str:
        """Start monitoring a cognitive process."""
        pid = f"proc_{self.process_counter}"
        self.process_counter += 1

        record = ProcessRecord(
            process_id=pid,
            name=name,
            state=ProcessState.RUNNING,
            start_time=time.time(),
            metadata=metadata or {}
        )

        self.processes[pid] = record
        return pid

    def end_process(self,
                    pid: str,
                    state: ProcessState = ProcessState.COMPLETED,
                    confidence: float = 0.5) -> None:
        """End monitoring of a process."""
        if pid in self.processes:
            self.processes[pid].end_time = time.time()
            self.processes[pid].state = state
            self.processes[pid].confidence = confidence

    def update_process(self,
                       pid: str,
                       **kwargs) -> None:
        """Update process metadata."""
        if pid in self.processes:
            for key, value in kwargs.items():
                if hasattr(self.processes[pid], key):
                    setattr(self.processes[pid], key, value)

    def get_process(self, pid: str) -> Optional[ProcessRecord]:
        """Get process record."""
        return self.processes.get(pid)

    def get_active_processes(self) -> List[ProcessRecord]:
        """Get all currently active processes."""
        return [
            p for p in self.processes.values()
            if p.state == ProcessState.RUNNING
        ]

    def record_metric(self, name: str, value: float) -> None:
        """Record a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

    def get_metric_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        if name not in self.metrics or not self.metrics[name]:
            return {}

        values = self.metrics[name]
        import numpy as np

        return {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'count': len(values)
        }

    def calibrate_confidence(self,
                            predicted: List[float],
                            actual: List[bool]) -> Dict[str, float]:
        """
        Calibrate confidence estimates.

        Args:
            predicted: Predicted confidence values
            actual: Actual outcomes (True/False)

        Returns:
            Calibration metrics
        """
        import numpy as np
        from sklearn.metrics import brier_score_loss

        # Brier score
        brier = brier_score_loss(actual, predicted)

        # Calibration by binning
        n_bins = 10
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        observed_freq = []
        predicted_conf = []

        for i in range(n_bins):
            mask = (np.array(predicted) >= bin_edges[i]) & \
                   (np.array(predicted) < bin_edges[i + 1])

            if mask.sum() > 0:
                observed_freq.append(np.mean(np.array(actual)[mask]))
                predicted_conf.append(bin_centers[i])

        return {
            'brier_score': brier,
            'calibration_error': np.mean([
                abs(o - p) for o, p in zip(observed_freq, predicted_conf)
            ]) if observed_freq else 0,
            'reliability': len(observed_freq) / n_bins
        }

    def get_system_state(self) -> Dict[str, Any]:
        """Get current system state."""
        active = self.get_active_processes()

        return {
            'active_processes': len(active),
            'total_processes': len(self.processes),
            'metrics_tracked': len(self.metrics),
            'timestamp': time.time()
        }



def metacognitive_monitor(task_state: Dict[str, Any],
                         confidence_threshold: float = 0.7) -> Dict[str, Any]:
    """
    Monitor task progress and trigger strategy changes when needed.

    Implements metacognitive control: detect when current strategy
    is failing and switch approaches.

    Args:
        task_state: Current task state and progress
        confidence_threshold: Minimum confidence to continue current strategy

    Returns:
        Metacognitive recommendations
    """
    import numpy as np

    # Assess progress
    progress = task_state.get('progress', 0.0)
    confidence = task_state.get('confidence', 0.5)
    time_elapsed = task_state.get('time_elapsed', 0.0)
    time_budget = task_state.get('time_budget', 1.0)

    recommendations = {
        'continue_current': True,
        'strategy_change': None,
        'confidence_adjustment': 0.0
    }

    # Check if confidence is too low
    if confidence < confidence_threshold:
        recommendations['continue_current'] = False
        recommendations['strategy_change'] = 'increase_effort'

    # Check if time is running out with low progress
    time_fraction = time_elapsed / time_budget
    if time_fraction > 0.7 and progress < 0.3:
        recommendations['continue_current'] = False
        recommendations['strategy_change'] = 'switch_to_approximate'

    # Check for stagnation
    recent_progress = task_state.get('recent_progress', [])
    if len(recent_progress) > 3:
        if all(p < 0.01 for p in recent_progress[-3:]):
            recommendations['continue_current'] = False
            recommendations['strategy_change'] = 'try_alternative_approach'

    return recommendations


def update_confidence_based_on_feedback(current_confidence: float,
                                       feedback: float,
                                       learning_rate: float = 0.1) -> float:
    """
    Update confidence estimate based on outcome feedback.

    Implements Bayesian-inspired confidence updating.

    Args:
        current_confidence: Current confidence estimate
        feedback: Actual outcome (0-1, where 1 = success)
        learning_rate: How quickly to update

    Returns:
        Updated confidence
    """
    error = feedback - current_confidence
    new_confidence = current_confidence + learning_rate * error

    # Clip to valid range
    new_confidence = max(0.0, min(1.0, new_confidence))

    return new_confidence



def organize_semantic_memory(concepts: List[Dict[str, Any]],
                           similarity_threshold: float = 0.7) -> Dict[str, Any]:
    """
    Organize semantic memories into clusters.

    Args:
        concepts: List of concepts with embeddings
        similarity_threshold: Minimum similarity for clustering

    Returns:
        Dictionary with clusters and organization
    """
    import numpy as np
    from collections import defaultdict

    # Extract embeddings
    embeddings = []
    for concept in concepts:
        emb = concept.get('embedding', concept.get('features', []))
        if isinstance(emb, list):
            embeddings.append(np.array(emb))
        else:
            embeddings.append(emb)

    if not embeddings:
        return {'clusters': []}

    embeddings = np.array(embeddings)

    # Compute similarity matrix
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10
    normalized = embeddings / norms
    similarity = normalized @ normalized.T

    # Build clusters
    clusters = []
    assigned = set()

    for i in range(len(concepts)):
        if i in assigned:
            continue

        # Find similar concepts
        similar = [j for j in range(len(concepts))
                  if j not in assigned and similarity[i, j] > similarity_threshold]

        if similar:
            cluster = {
                'centroid': np.mean(embeddings[similar], axis=0).tolist(),
                'members': similar,
                'concepts': [concepts[j] for j in similar],
                'size': len(similar)
            }
            clusters.append(cluster)
            assigned.update(similar)

    return {
        'clusters': clusters,
        'num_clusters': len(clusters),
        'similarity_threshold': similarity_threshold
    }



def fft_pattern_detect(data: np.ndarray, min_freq: float = 0.01, max_freq: float = 0.5) -> Dict[str, Any]:
    """
    Detect periodic patterns using FFT analysis.

    Args:
        data: Input signal
        min_freq: Minimum frequency to detect
        max_freq: Maximum frequency to detect

    Returns:
        Dictionary with detected frequencies and powers
    """
    import numpy as np

    # Compute FFT
    fft_result = np.fft.fft(data)
    freqs = np.fft.fftfreq(len(data))
    power = np.abs(fft_result)**2

    # Filter to frequency range
    mask = (np.abs(freqs) >= min_freq) & (np.abs(freqs) <= max_freq)
    filtered_freqs = freqs[mask]
    filtered_power = power[mask]

    # Sort by power
    sorted_indices = np.argsort(filtered_power)[::-1]

    # Get top frequencies
    top_freqs = []
    top_powers = []
    for idx in sorted_indices[:10]:
        top_freqs.append(float(filtered_freqs[idx]))
        top_powers.append(float(filtered_power[idx]))

    return {
        'frequencies': top_freqs,
        'powers': top_powers,
        'dominant_frequency': top_freqs[0] if top_freqs else None,
        'total_power': float(np.sum(filtered_power))
    }



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """
    Detect patterns using autocorrelation analysis.

    Args:
        data: Input signal
        max_lag: Maximum lag to check (None for len(data)//4)

    Returns:
        Dictionary with autocorrelation results and detected periods
    """
    import numpy as np

    if max_lag is None:
        max_lag = len(data) // 4

    # Compute autocorrelation
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]

    # Normalize
    autocorr = autocorr / autocorr[0]

    # Find peaks
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(autocorr[:max_lag], height=0.2)

    # Estimate periods from peaks
    periods = []
    for peak in peaks:
        if peak > 0:
            periods.append(peak)

    return {
        'autocorrelation': autocorr[:max_lag],
        'peaks': peaks.tolist(),
        'periods': periods,
        'dominant_period': periods[0] if periods else None
    }



def direct_lingam(data: np.ndarray) -> Dict[str, Any]:
    """
    Apply DirectLiNGAM algorithm for causal discovery.

    Uses non-Gaussianity to estimate causal order and structure.

    Args:
        data: Data matrix (n_samples x n_variables)

    Returns:
        Dictionary with causal matrix and causal order
    """
    import numpy as np

    n_samples, n_vars = data.shape

    # Standardize data
    data = (data - np.mean(data, axis=0)) / (np.std(data, axis=0) + 1e-10)

    # Initialize
    causal_order = []
    remaining_vars = list(range(n_vars))
    B = np.zeros((n_vars, n_vars))  # Causal matrix

    for _ in range(n_vars):
        scores = []

        for var in remaining_vars:
            # Compute independence score using non-Gaussianity
            test_vars = [v for v in remaining_vars if v != var]

            if not test_vars:
                scores.append((var, 0))
                continue
