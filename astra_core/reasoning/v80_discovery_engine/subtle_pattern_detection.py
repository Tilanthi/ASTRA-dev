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
Subtle Pattern Detection Module

Detects subtle causal patterns across vast datasets:
- Multi-scale pattern detection
- High-dimensional correlation analysis
- Rare event detection
- Cross-survey pattern discovery
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from scipy.stats import zscore, pearsonr, spearmanr, norm
from scipy.signal import find_peaks, welch
from sklearn.decomposition import PCA
import warnings

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.cluster import DBSCAN
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available")


@dataclass
class DetectedPattern:
    """Represents a subtle pattern detected in data."""
    pattern_id: str
    pattern_type: str  # 'correlation', 'periodicity', 'anomaly', 'cluster', 'causal_chain'
    description: str
    locations: List[int]  # Indices where pattern occurs
    strength: float
    significance: float  # Statistical significance
    variables_involved: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class SubtlePatternDetection:
    """
    Detect subtle patterns across vast astronomical datasets.

    Methods:
    1. Multi-Scale Scanning: Look for patterns at different scales
    2. Rare Event Detection: Find anomalous but meaningful events
    3. Correlation Discovery: Find weak but real correlations
    4. Causal Chain Detection: Find indirect causal relationships
    5. Cross-Survey Integration: Find patterns across different datasets
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize subtle pattern detection engine.

        Args:
            config: Configuration dict with keys:
                - min_pattern_strength: Minimum correlation/strength (default: 0.1)
                - significance_threshold: Minimum p-value (default: 0.01)
                - max_scale_ratio: Ratio of largest to smallest scale (default: 100)
        """
        config = config or {}
        self.min_strength = config.get('min_pattern_strength', 0.1)
        self.significance_threshold = config.get('significance_threshold', 0.01)
        self.max_scale_ratio = config.get('max_scale_ratio', 100)

        self.detected_patterns: List[DetectedPattern] = []

    def scan_dataset(
        self,
        data: np.ndarray,
        variable_names: List[str],
        scan_types: Optional[List[str]] = None
    ) -> List[DetectedPattern]:
        """
        Comprehensively scan dataset for subtle patterns.

        Args:
            data: Shape (n_samples, n_variables)
            variable_names: Names of variables
            scan_types: Types of patterns to scan for

        Returns:
            List of detected patterns
        """
        if scan_types is None:
            scan_types = ['correlation', 'periodicity', 'anomaly', 'cluster']

        patterns = []

        # 1. Correlation scanning (including weak correlations)
        if 'correlation' in scan_types:
            correlation_patterns = self._detect_correlations(data, variable_names)
            patterns.extend(correlation_patterns)

        # 2. Periodicity detection
        if 'periodicity' in scan_types:
            periodicity_patterns = self._detect_periodicity(data, variable_names)
            patterns.extend(periodicity_patterns)

        # 3. Anomaly detection (rare but real events)
        if 'anomaly' in scan_types:
            anomaly_patterns = self._detect_anomalies(data, variable_names)
            patterns.extend(anomaly_patterns)

        # 4. Clustering patterns
        if 'cluster' in scan_types and SKLEARN_AVAILABLE:
            cluster_patterns = self._detect_clusters(data, variable_names)
            patterns.extend(cluster_patterns)

        # Filter by significance
        patterns = [p for p in patterns if p.significance < self.significance_threshold]

        self.detected_patterns.extend(patterns)
        return patterns

    def _detect_correlations(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[DetectedPattern]:
        """Detect correlations including weak/subtle ones."""
        patterns = []
        n_variables = len(variable_names)

        for i in range(n_variables):
            for j in range(i+1, n_variables):
                # Pearson correlation
                corr, p_value = pearsonr(data[:, i], data[:, j])

                # Also check Spearman for non-linear monotonic
                spearman_corr, spearman_p = spearmanr(data[:, i], data[:, j])

                # Consider both linear and non-linear correlations
                if abs(corr) > self.min_strength or abs(spearman_corr) > self.min_strength:
                    pattern_type = 'linear_correlation' if abs(corr) > abs(spearman_corr) else 'monotonic_correlation'

                    pattern = DetectedPattern(
                        pattern_id=f'{pattern_type}_{variable_names[i]}_{variable_names[j]}',
                        pattern_type=pattern_type,
                        description=f"{variable_names[i]} correlates with {variable_names[j]}",
                        locations=list(range(len(data))),
                        strength=max(abs(corr), abs(spearman_corr)),
                        significance=min(p_value, spearman_p),
                        variables_involved=[variable_names[i], variable_names[j]],
                        metadata={
                            'pearson_r': float(corr),
                            'spearman_rho': float(spearman_corr),
                            'p_value': float(p_value)
                        }
                    )
                    patterns.append(pattern)

        return patterns

    def _detect_periodicity(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[DetectedPattern]:
        """Detect periodic signals in data."""
        patterns = []

        for i, var_name in enumerate(variable_names):
            var_data = data[:, i]

            # Remove trend
            if len(var_data) > 10:
                # Compute power spectrum
                freqs, power = welch(var_data)

                # Find peaks
                peaks, properties = find_peaks(power, height=np.max(power) * 0.1)

                if len(peaks) > 0:
                    # Get dominant frequency
                    dominant_peak = peaks[np.argmax(power[peaks])]
                    dominant_freq = freqs[dominant_peak]
                    dominant_power = power[dominant_peak]

                    # Estimate significance
                    signal_power = dominant_power
                    noise_power = np.median(power)
                    snr = signal_power / (noise_power + 1e-10)

                    if snr > 3:  # Significant SNR threshold
                        pattern = DetectedPattern(
                            pattern_id=f'periodicity_{var_name}',
                            pattern_type='periodicity',
                            description=f"{var_name} shows periodicity at f={dominant_freq:.3f}",
                            locations=list(range(len(var_data))),
                            strength=float(snr / (1 + snr)),
                            significance=2.0 / (snr + 1),  # Approximate
                            variables_involved=[var_name],
                            metadata={
                                'frequency': float(dominant_freq),
                                'power': float(dominant_power),
                                'snr': float(snr)
                            }
                        )
                        patterns.append(pattern)

        return patterns

    def _detect_anomalies(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[DetectedPattern]:
        """Detect anomalous but potentially meaningful events."""
        patterns = []

        if not SKLEARN_AVAILABLE:
            return patterns

        # Use Isolation Forest for anomaly detection
        for i, var_name in enumerate(variable_names):
            var_data = data[:, i:i+1]

            # Fit isolation forest
            iso_forest = IsolationForest(contamination=0.05, random_state=42)
            anomaly_labels = iso_forest.fit_predict(var_data)

            # Find anomalies
            anomaly_indices = np.where(anomaly_labels == -1)[0]

            if len(anomaly_indices) > 0:
                # Compute z-scores
                z_scores = np.abs(zscore(data[:, i]))

                for idx in anomaly_indices:
                    pattern = DetectedPattern(
                        pattern_id=f'anomaly_{var_name}_{idx}',
                        pattern_type='anomaly',
                        description=f"{var_name} anomaly at index {idx}",
                        locations=[idx],
                        strength=float(z_scores[idx]),
                        significance=2.0 * (1.0 - norm.cdf(z_scores[idx])),  # Two-tailed p-value
                        variables_involved=[var_name],
                        metadata={
                            'value': float(data[idx, i]),
                            'z_score': float(z_scores[idx])
                        }
                    )
                    patterns.append(pattern)

        return patterns

    def _detect_clusters(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[DetectedPattern]:
        """Detect clustering patterns in data."""
        patterns = []

        if not SKLEARN_AVAILABLE:
            return patterns

        # Use DBSCAN for density-based clustering
        dbscan = DBSCAN(eps=1.0, min_samples=5)
        labels = dbscan.fit_predict(data)

        unique_labels = set(labels)
        unique_labels.discard(-1)  # Remove noise

        if len(unique_labels) > 1:
            # Found clusters
            for label in unique_labels:
                cluster_indices = np.where(labels == label)[0]

                pattern = DetectedPattern(
                    pattern_id=f'cluster_{label}',
                    pattern_type='cluster',
                    description=f"Cluster {label} contains {len(cluster_indices)} points",
                    locations=cluster_indices.tolist(),
                    strength=float(len(cluster_indices) / len(data)),
                    significance=0.05,  # Approximate
                    variables_involved=variable_names,
                    metadata={
                        'cluster_size': len(cluster_indices),
                        'cluster_label': int(label)
                    }
                )
                patterns.append(pattern)

        return patterns

    def detect_cross_survey_patterns(
        self,
        datasets: Dict[str, np.ndarray],
        variable_mappings: Dict[str, List[str]]
    ) -> List[DetectedPattern]:
        """
        Detect patterns that span multiple surveys/datasets.

        Args:
            datasets: Dictionary of dataset_name -> data array
            variable_mappings: How variables map between datasets

        Returns:
            List of cross-survey patterns
        """
        patterns = []

        # Find common variables across surveys
        all_vars = set()
        for var_list in variable_mappings.values():
            all_vars.update(var_list)

        for var in all_vars:
            # Find datasets that have this variable
            relevant_datasets = {
                name: (data[:, var_list.index(var)] if var in var_list else None)
                for name, data, var_list in zip(datasets.keys(), datasets.values(), variable_mappings.values())
                if var in var_list
            }

            if len(relevant_datasets) >= 2:
                # Check for consistency across surveys
                values = []
                for name, data in relevant_datasets.items():
                    if data is not None:
                        values.append(data)

                if len(values) >= 2:
                    # Check correlation between surveys
                    for i, (name1, vals1) in enumerate(relevant_datasets.items()):
                        for name2, vals2 in list(relevant_datasets.items())[i+1:]:
                            if vals1 is not None and vals2 is not None:
                                # Only compare overlapping indices
                                min_len = min(len(vals1), len(vals2))
                                corr, p_val = pearsonr(vals1[:min_len], vals2[:min_len])

                                if abs(corr) > self.min_strength:
                                    pattern = DetectedPattern(
                                        pattern_id=f'cross_survey_{var}_{name1}_{name2}',
                                        pattern_type='cross_survey_correlation',
                                        description=f"{var} correlates between {name1} and {name2}",
                                        locations=[],
                                        strength=float(abs(corr)),
                                        significance=float(p_val),
                                        variables_involved=[var],
                                        metadata={
                                            'surveys': [name1, name2],
                                            'correlation': float(corr)
                                        }
                                    )
                                    patterns.append(pattern)

        return patterns


def demo_subtle_pattern_detection():
    """Demonstrate subtle pattern detection."""
    print("=" * 60)
    print("Subtle Pattern Detection Module Demo")
    print("=" * 60)

    # Create synthetic data with subtle patterns
    np.random.seed(42)
    n_samples = 500

    # Variable 1: Periodic with weak signal
    t = np.linspace(0, 10, n_samples)
    var1 = 0.1 * np.sin(2 * np.pi * t) + np.random.randn(n_samples) * 0.5

    # Variable 2: Correlated with var1 but weakly
    var2 = 0.3 * var1 + np.random.randn(n_samples) * 0.8

    # Variable 3: Independent
    var3 = np.random.randn(n_samples)

    # Variable 4: Has some anomalies
    var4 = np.random.randn(n_samples)
    var4[100] = 5.0  # Anomaly
    var4[250] = -4.0  # Anomaly

    data = np.column_stack([var1, var2, var3, var4])
    variable_names = ['periodic_var', 'correlated_var', 'independent_var', 'anomalous_var']

    # Initialize detection engine
    detector = SubtlePatternDetection()

    # Scan for patterns
    patterns = detector.scan_dataset(data, variable_names)

    print(f"\nDetected {len(patterns)} subtle patterns:")
    for pattern in patterns[:10]:  # Show first 10
        print(f"\n  {pattern.pattern_id}")
        print(f"  Type: {pattern.pattern_type}")
        print(f"  Description: {pattern.description}")
        print(f"  Strength: {pattern.strength:.2f}")
        print(f"  Significance: {pattern.significance:.4f}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    demo_subtle_pattern_detection()
