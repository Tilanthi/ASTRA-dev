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
Meta-Memory System

Monitoring and management of memory systems.
Provides confidence assessment, source monitoring, etc.
"""

from typing import Dict, List, Optional, Any
from enum import Enum


class MemoryType(Enum):
    """Types of memory systems."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"


class MetaMemory:
    """
    Meta-memory system for monitoring and managing memory.

    Provides:
    - Confidence assessment for memories
    - Source monitoring
    - Forgetting prediction
    - Memory consolidation management
    """

    def __init__(self):
        self.confidences: Dict[str, float] = {}  # item_id -> confidence
        self.sources: Dict[str, str] = {}  # item_id -> source
        self.access_counts: Dict[str, int] = {}
        self.last_access: Dict[str, float] = {}

    def assess_confidence(self,
                          item_id: str,
                          memory_type: MemoryType,
                          access_count: int = 1,
                          recency: float = 1.0) -> float:
        """
        Assess confidence in memory.

        Args:
            item_id: Memory item identifier
            memory_type: Type of memory
            access_count: Number of times accessed
            recency: How recent (0=old, 1=recent)

        Returns:
            Confidence score [0, 1]
        """
        # Base confidence
        confidence = 0.5

        # Boost by access frequency
        confidence += min(0.3, access_count * 0.05)

        # Boost by recency
        confidence += recency * 0.2

        # Cap at 1.0
        confidence = min(1.0, confidence)

        self.confidences[item_id] = confidence
        self.access_counts[item_id] = access_count

        return confidence

    def get_confidence(self, item_id: str) -> float:
        """Get confidence for memory item."""
        return self.confidences.get(item_id, 0.5)

    def monitor_source(self,
                       item_id: str,
                       source: str) -> None:
        """Record source of memory."""
        self.sources[item_id] = source

    def get_source(self, item_id: str) -> Optional[str]:
        """Get source of memory."""
        return self.sources.get(item_id)

    def predict_forgetting(self,
                          item_id: str,
                          time_since_access: float,
                          importance: float = 0.5) -> float:
        """
        Predict probability of forgetting.

        Args:
            item_id: Memory item
            time_since_access: Time since last access
            importance: Importance of memory

        Returns:
            Forgetting probability [0, 1]
        """
        # Simple exponential decay model
        base_rate = 0.1
        decay_rate = base_rate * (1 - importance * 0.5)

        forgetting_prob = 1 - np.exp(-decay_rate * time_since_access)

        return forgetting_prob

    def should_consolidate(self,
                          item_id: str,
                          importance: float = 0.5) -> bool:
        """Determine if memory should be consolidated."""
        confidence = self.get_confidence(item_id)
        return confidence > 0.7 and importance > 0.6

    def get_stats(self) -> Dict[str, Any]:
        """Get meta-memory statistics."""
        return {
            'tracked_items': len(self.confidences),
            'average_confidence': np.mean(list(self.confidences.values())) if self.confidences else 0,
            'sources_tracked': len(self.sources)
        }


import numpy as np



def encode_episodic_memory(event: Dict[str, Any],
                          context: Dict[str, Any],
                          importance: float = 0.5) -> Dict[str, Any]:
    """
    Encode an episodic memory with context and importance.

    Args:
        event: The event to remember
        context: Contextual information
        importance: Importance score (0-1)

    Returns:
        Encoded memory with retrieval cues
    """
    import hashlib
    import json
    import time

    # Generate unique ID
    event_id = hashlib.md5(json.dumps(event, sort_keys=True).encode()).hexdigest()[:12]

    memory = {
        'id': f"epi_{event_id}",
        'event': event,
        'context': context,
        'importance': importance,
        'timestamp': time.time(),
        'access_count': 0,
        'last_access': time.time(),
        'encoding_strength': importance,
        'retrieval_cues': _extract_retrieval_cues(event, context)
    }

    return memory


def _extract_retrieval_cues(event: Dict[str, Any],
                           context: Dict[str, Any]) -> List[str]:
    """Extract cues for memory retrieval."""
    cues = []

    # Add key terms from event
    for key, value in event.items():
        if isinstance(value, str):
            cues.extend(value.lower().split()[:5])
        elif isinstance(value, (int, float)):
            cues.append(f"{key}:{value}")

    # Add context terms
    for key, value in context.items():
        if isinstance(value, str):
            cues.extend(value.lower().split()[:3])

    return list(set(cues))



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



def detect_change_points(data: np.ndarray, min_size: int = 10, penalty: float = 1.0) -> List[int]:
    """
    Detect change points in time series data.

    Args:
        data: Input time series
        min_size: Minimum segment size between change points
        penalty: Penalty for additional change points

    Returns:
        List of change point indices
    """
    import numpy as np

    n = len(data)
    change_points = []

    # Compute cumulative statistics
    cumsum = np.cumsum(data)
    cumsum_sq = np.cumsum(data**2)

    # Scan for change points
    i = min_size
    while i < n - min_size:
        # Check if there's a significant change at position i
        before_mean = cumsum[i] / i
        after_mean = (cumsum[n-1] - cumsum[i]) / (n - i)

        before_var = (cumsum_sq[i] / i) - before_mean**2
        after_var = ((cumsum_sq[n-1] - cumsum_sq[i]) / (n - i)) - after_mean**2

        # Test for significant change
        if abs(before_mean - after_mean) > penalty * np.sqrt(before_var + after_var + 1e-10):
            change_points.append(i)
            i += min_size  # Skip ahead
        else:
            i += 1

    return change_points



def form_concept_from_examples(examples: List[Dict[str, Any]],
                              concept_name: str = None) -> Dict[str, Any]:
    """
    Form a concept from concrete examples.

    Args:
        examples: List of examples
        concept_name: Optional name for the concept

    Returns:
        Concept definition with essential features
    """
    import numpy as np
    from collections import Counter

    if not examples:
        return None

    # Extract common features
    all_features = {}
    feature_counts = Counter()

    for example in examples:
        for key, value in example.items():
            if key not in all_features:
                all_features[key] = []
            all_features[key].append(value)
            feature_counts[key] += 1

    # Identify essential features (present in most examples)
    essential_features = {}
    for key, values in all_features.items():
        if feature_counts[key] >= len(examples) * 0.7:  # Present in 70%+ examples
            # For continuous: compute mean
            if all(isinstance(v, (int, float)) for v in values):
                essential_features[key] = {
                    'type': 'continuous',
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'range': [float(np.min(values)), float(np.max(values))]
                }
            # For categorical: most common
            else:
                counter = Counter(values)
                essential_features[key] = {
                    'type': 'categorical',
                    'most_common': counter.most_common(1)[0][0],
                    'frequency': counter.most_common(1)[0][1] / len(values)
                }

    concept = {
        'name': concept_name or f"concept_{id(examples)}",
        'essential_features': essential_features,
        'num_examples': len(examples),
        'coverage': len(essential_features) / len(all_features) if all_features else 0,
        'examples': examples[:3]  # Keep representative examples
    }

    return concept



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



def gaussian_process_predict(X_train: np.ndarray,
                            y_train: np.ndarray,
                            X_test: np.ndarray,
                            kernel: str = 'rbf',
                            length_scale: float = 1.0,
                            noise_variance: float = 0.1) -> Dict[str, Any]:
    """
    Make predictions with uncertainty using Gaussian Process.

    Args:
        X_train: Training inputs
        y_train: Training outputs
        X_test: Test inputs
        kernel: Kernel type ('rbf', 'matern')
        length_scale: Kernel length scale
        noise_variance: Observation noise variance

    Returns:
        Dictionary with predictions and uncertainties
    """
    import numpy as np

    # RBF kernel
    def rbf_kernel(x1, x2, length_scale):
        sq_dist = np.sum(x1**2, axis=1).reshape(-1, 1) +                    np.sum(x2**2, axis=1) - 2 * np.dot(x1, x2.T)
        return np.exp(-0.5 * sq_dist / length_scale**2)

    # Compute kernel matrices
    K = rbf_kernel(X_train, X_train, length_scale) + noise_variance * np.eye(len(X_train))
    K_s = rbf_kernel(X_train, X_test, length_scale)
    K_ss = rbf_kernel(X_test, X_test, length_scale)

    # Cholesky decomposition for stability
    L = np.linalg.cholesky(K)
    alpha = np.linalg.solve(L.T, np.linalg.solve(L, y_train))

    # Predictive mean
    y_mean = K_s.T @ alpha

    # Predictive variance
    v = np.linalg.solve(L, K_s)
    y_var = np.diag(K_ss) - np.sum(v**2, axis=0)

    return {
        'mean': y_mean,
        'std': np.sqrt(np.maximum(y_var, 0)),
        'covariance': K_ss - v.T @ v
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
