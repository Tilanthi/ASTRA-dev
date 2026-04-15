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
Real-Time Anomaly Detection for Astronomical Data Streams

Detects novel and anomalous phenomena in real-time data streams:
- Unusual light curves
- Novel spectral features
- Unexpected transient events
- Anomalous sources in catalogs
- Outlier detections in image streams

Uses online learning algorithms that adapt to changing data distributions
while maintaining sensitivity to true anomalies.

Author: STAN Evolution Team
Date: 2025-03-18
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import warnings


@dataclass
class AnomalyReport:
    """Report of detected anomaly"""
    anomaly_id: str
    timestamp: datetime
    source_id: str
    anomaly_type: str  # 'light_curve', 'spectrum', 'transient', 'source'
    anomaly_score: float  # [0, 1], higher = more anomalous
    confidence: float
    description: str
    features: Dict[str, float]
    suggested_observations: List[str]
    is_known_type: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class OnlineStandardScaler:
    """
    Online standardization of features.

    Maintains running mean and std without storing all data.
    """

    def __init__(self, epsilon: float = 1e-10):
        self.epsilon = epsilon
        self.count = 0
        self.mean = 0.0
        self.M2 = 0.0  # Sum of squared differences

    def update(self, value: float) -> float:
        """
        Update with new value and return standardized value.

        Args:
            value: New observation

        Returns:
            Standardized value (z-score)
        """
        self.count += 1

        # Online mean update
        delta = value - self.mean
        self.mean += delta / self.count

        # Online variance update (Welford's algorithm)
        delta2 = value - self.mean
        self.M2 += delta * delta2

        # Compute current std
        if self.count > 1:
            std = np.sqrt(self.M2 / self.count)
        else:
            std = 1.0

        # Return z-score
        return (value - self.mean) / (std + self.epsilon)

    def get_stats(self) -> Tuple[float, float]:
        """Get current mean and std."""
        if self.count > 1:
            std = np.sqrt(self.M2 / self.count)
        else:
            std = 0.0
        return self.mean, std


class IsolationForestOnline:
    """
    Online approximation of Isolation Forest.

    Uses streaming isolation trees for anomaly detection.
    """

    def __init__(self, n_trees: int = 100, max_samples: int = 256,
                 subsample_size: int = 64):
        """
        Initialize online isolation forest.

        Args:
            n_trees: Number of trees in the forest
            max_samples: Maximum samples in window for each tree
            subsample_size: Size of subsample for tree splitting
        """
        self.n_trees = n_trees
        self.max_samples = max_samples
        self.subsample_size = subsample_size

        # Trees represented as random splits
        self.splits = []
        self.feature_indices = []

        # Data windows for each tree
        self.data_windows = [deque(maxlen=max_samples) for _ in range(n_trees)]

        self.is_fitted = False

    def partial_fit(self, X: np.ndarray) -> 'IsolationForestOnline':
        """
        Incrementally fit the model.

        Args:
            X: New data samples [n_samples, n_features]

        Returns:
            Self
        """
        n_samples, n_features = X.shape

        # Initialize splits if needed
        if not self.is_fitted:
            self.splits = []
            self.feature_indices = []

            for _ in range(self.n_trees):
                # Random feature to split on
                feat_idx = np.random.randint(0, n_features)
                self.feature_indices.append(feat_idx)

                # Initial split value (will adapt)
                self.splits.append({
                    'value': 0.0,
                    'left_value': -1.0,
                    'right_value': 1.0
                })

            self.is_fitted = True

        # Update data windows
        for i in range(self.n_trees):
            for sample in X:
                self.data_windows[i].append(sample)

        # Update splits based on current windows
        for i in range(self.n_trees):
            if len(self.data_windows[i]) > 10:
                window_data = np.array(self.data_windows[i])
                feat_idx = self.feature_indices[i]

                # Median split
                feat_values = window_data[:, feat_idx]
                split_value = np.median(feat_values)

                self.splits[i]['value'] = split_value

                # Update child node splits
                left_mask = feat_values <= split_value
                right_mask = feat_values > split_value

                if np.any(left_mask):
                    self.splits[i]['left_value'] = np.median(feat_values[left_mask])

                if np.any(right_mask):
                    self.splits[i]['right_value'] = np.median(feat_values[right_mask])

        return self

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Compute anomaly scores for samples.

        Args:
            X: Data samples [n_samples, n_features]

        Returns:
            Anomaly scores [n_samples], higher = more anomalous
        """
        if not self.is_fitted:
            return np.zeros(len(X))

        n_samples = X.shape[0]
        scores = np.zeros(n_samples)

        for i, sample in enumerate(X):
            path_length = 0.0

            # Average path length across trees
            for tree_idx in range(self.n_trees):
                feat_idx = self.feature_indices[tree_idx]
                split = self.splits[tree_idx]

                # Compute path length
                value = sample[feat_idx]
                depth = 1.0

                if value <= split['value']:
                    # Go left
                    depth += 0.5
                else:
                    # Go right
                    depth += 0.5

                path_length += depth

            # Average path length
            avg_path_length = path_length / self.n_trees

            # Convert to score (shorter path = more anomalous)
            # Normalize to [0, 1]
            max_path = np.log2(self.subsample_size)
            scores[i] = np.exp(-avg_path_length / max_path)

        return scores

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """
        Predict if samples are anomalies.

        Args:
            X: Data samples
            threshold: Anomaly score threshold

        Returns:
            Boolean array, True = anomaly
        """
        scores = self.score_samples(X)
        return scores > threshold


class LightCurveAnomalyDetector:
    """
    Detect anomalies in light curve data.

    Features:
    - Unusual variability patterns
    - Period changes
    - Amplitude changes
    - Shape novelties
    """

    def __init__(self, window_size: int = 50):
        """
        Initialize light curve anomaly detector.

        Args:
            window_size: Number of points in sliding window
        """
        self.window_size = window_size

        # Feature scalers
        self.scalers = {
            'amplitude': OnlineStandardScaler(),
            'period': OnlineStandardScaler(),
            'std': OnlineStandardScaler(),
            'skew': OnlineStandardScaler(),
        }

        # Anomaly model
        self.model = IsolationForestOnline(n_trees=50, subsample_size=32)

        # History
        self.light_curve_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))

        self.is_trained = False

    def update(self, source_id: str, time: float, magnitude: float,
               error: float = 0.0) -> Optional[AnomalyReport]:
        """
        Update with new photometric point and detect anomalies.

        Args:
            source_id: Source identifier
            time: Observation time (JD or MJD)
            magnitude: Magnitude measurement
            error: Magnitude error

        Returns:
            AnomalyReport if anomaly detected, None otherwise
        """
        # Add to history
        self.light_curve_history[source_id].append((time, magnitude, error))

        # Need enough data
        if len(self.light_curve_history[source_id]) < 10:
            return None

        # Extract features
        features = self._extract_features(source_id)

        # Standardize features
        standardized = {}
        for key, value in features.items():
            if key in self.scalers:
                standardized[key] = self.scalers[key].update(value)
            else:
                standardized[key] = value

        # Create feature vector
        feature_vector = np.array([[standardized['amplitude'],
                                    standardized['std'],
                                    standardized['skew']]])

        # Train if not yet trained
        if not self.is_trained:
            self.model.partial_fit(feature_vector)
            self.is_trained = True
            return None

        # Score
        score = self.model.score_samples(feature_vector)[0]

        # Check if anomaly
        if score > 0.7:  # Threshold
            return self._create_report(source_id, score, features, standardized)

        # Update model with normal data
        if score < 0.5:
            self.model.partial_fit(feature_vector)

        return None

    def _extract_features(self, source_id: str) -> Dict[str, float]:
        """Extract features from light curve history."""
        history = list(self.light_curve_history[source_id])

        times = np.array([h[0] for h in history])
        mags = np.array([h[1] for h in history])

        # Amplitude
        amplitude = np.max(mags) - np.min(mags)

        # Standard deviation
        std = np.std(mags)

        # Skewness
        skew = 0.0
        if std > 0:
            skew = np.mean(((mags - np.mean(mags)) / std) ** 3)

        # Estimate period (simplified)
        period = 0.0
        if len(times) > 20:
            # Use Lomb-Scargle for period estimation
            from scipy.signal import lombscargle
            # ... (simplified, real implementation would use astropy)

        return {
            'amplitude': amplitude,
            'std': std,
            'skew': skew,
            'period': period
        }

    def _create_report(self, source_id: str, score: float,
                       features: Dict, standardized: Dict) -> AnomalyReport:
        """Create anomaly report."""
        # Determine anomaly type
        if abs(standardized.get('amplitude', 0)) > 3:
            anomaly_type = "unusual_amplitude"
            description = f"Unusual amplitude: {features['amplitude']:.2f} mag"
        elif abs(standardized.get('std', 0)) > 3:
            anomaly_type = "unusual_variability"
            description = f"Unusual variability: {features['std']:.3f}"
        elif abs(standardized.get('skew', 0)) > 3:
            anomaly_type = "asymmetric_light_curve"
            description = f"Asymmetric light curve shape"
        else:
            anomaly_type = "novel_light_curve"
            description = "Novel light curve pattern"

        return AnomalyReport(
            anomaly_id=f"lc_{source_id}_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            source_id=source_id,
            anomaly_type=anomaly_type,
            anomaly_score=score,
            confidence=score,
            description=description,
            features=features,
            suggested_observations=self._generate_suggestions(anomaly_type, features)
        )

    def _generate_suggestions(self, anomaly_type: str,
                              features: Dict) -> List[str]:
        """Generate observation suggestions."""
        suggestions = []

        if anomaly_type == "unusual_amplitude":
            suggestions.append("Obtain spectrum to classify source")
            suggestions.append("Monitor for further changes")
        elif anomaly_type == "novel_light_curve":
            suggestions.append("High cadence monitoring")
            suggestions.append("Multi-wavelength follow-up")
        elif anomaly_type == "unusual_variability":
            suggestions.append("Check for instrumental issues")
            suggestions.append("Obtain comparison stars")

        return suggestions


class SpectralAnomalyDetector:
    """
    Detect anomalies in spectral data.

    Features:
    - Novel emission/absorption lines
    - Unusual line ratios
    - Peculiar continuum shapes
    - Unknown spectral types
    """

    def __init__(self, wavelength_grid: np.ndarray, n_components: int = 10):
        """
        Initialize spectral anomaly detector.

        Args:
            wavelength_grid: Wavelength grid for spectra (Angstroms)
            n_components: Number of PCA components
        """
        self.wavelength_grid = wavelength_grid
        self.n_components = n_components

        # PCA for dimensionality reduction
        self.components = np.random.randn(n_components, len(wavelength_grid))
        self.component_mean = np.zeros(len(wavelength_grid))
        self.component_std = np.ones(len(wavelength_grid))

        # Feature scalers
        self.scalers = {
            'continuum_slope': OnlineStandardScaler(),
            'line_equivalent_width': OnlineStandardScaler(),
            'line_ratio': OnlineStandardScaler(),
        }

        # Anomaly model
        self.model = IsolationForestOnline(n_trees=50, subsample_size=32)

        # Line templates
        self.line_templates = {
            'H_alpha': 6562.8,
            'H_beta': 4861.3,
            'OIII_5007': 5006.8,
            'NII_6583': 6583.5,
            'SII_6716': 6716.4,
            'SII_6731': 6730.8,
        }

        self.is_trained = False

    def update(self, source_id: str, spectrum: np.ndarray,
               error: Optional[np.ndarray] = None) -> Optional[AnomalyReport]:
        """
        Update with new spectrum and detect anomalies.

        Args:
            source_id: Source identifier
            spectrum: Flux values
            error: Flux errors

        Returns:
            AnomalyReport if anomaly detected
        """
        # Extract features
        features = self._extract_spectral_features(spectrum, error)

        # Standardize
        standardized = {}
        for key, value in features.items():
            if key in self.scalers:
                standardized[key] = self.scalers[key].update(value)
            else:
                standardized[key] = value

        # Create feature vector
        feature_vector = np.array([[standardized['continuum_slope'],
                                    standardized['line_equivalent_width'],
                                    standardized.get('line_ratio', 0)]])

        # Train if not yet trained
        if not self.is_trained:
            self.model.partial_fit(feature_vector)
            self.is_trained = True
            return None

        # Score
        score = self.model.score_samples(feature_vector)[0]

        # Check for novel lines
        novel_lines = self._detect_novel_lines(spectrum, error)

        if score > 0.7 or len(novel_lines) > 0:
            return self._create_spectral_report(
                source_id, score, features, standardized, novel_lines
            )

        # Update model
        if score < 0.5:
            self.model.partial_fit(feature_vector)

        return None

    def _extract_spectral_features(self, spectrum: np.ndarray,
                                    error: Optional[np.ndarray]) -> Dict[str, float]:
        """Extract features from spectrum."""
        features = {}

        # Continuum slope (simple linear fit)
        if len(spectrum) > 10:
            x = np.arange(len(spectrum))
            coeffs = np.polyfit(x, spectrum, 1)
            features['continuum_slope'] = coeffs[0]
        else:
            features['continuum_slope'] = 0.0

        # Line equivalent width (simplified)
        continuum = np.median(spectrum)
        features['line_equivalent_width'] = np.sum(np.abs(spectrum - continuum))

        # Line ratio (H-alpha / H-beta)
        h_alpha_idx = np.argmin(np.abs(self.wavelength_grid - self.line_templates['H_alpha']))
        h_beta_idx = np.argmin(np.abs(self.wavelength_grid - self.line_templates['H_beta']))

        if h_alpha_idx < len(spectrum) and h_beta_idx < len(spectrum):
            h_alpha = spectrum[h_alpha_idx]
            h_beta = spectrum[h_beta_idx]
            features['line_ratio'] = h_alpha / (h_beta + 1e-10)
        else:
            features['line_ratio'] = 0.0

        return features

    def _detect_novel_lines(self, spectrum: np.ndarray,
                            error: Optional[np.ndarray]) -> List[Dict]:
        """Detect novel emission/absorption lines."""
        novel_lines = []

        if error is None:
            error = np.ones_like(spectrum) * 0.1

        # Find significant peaks
        continuum = np.median(spectrum)
        threshold = continuum + 5 * np.median(error)

        peaks = np.where(spectrum > threshold)[0]

        for peak_idx in peaks:
            wavelength = self.wavelength_grid[peak_idx]

            # Check if matches known line
            is_known = False
            for line_name, line_wave in self.line_templates.items():
                if abs(wavelength - line_wave) < 10:  # Within 10 Angstroms
                    is_known = True
                    break

            if not is_known:
                novel_lines.append({
                    'wavelength': wavelength,
                    'flux': spectrum[peak_idx],
                    'significance': (spectrum[peak_idx] - continuum) / error[peak_idx]
                })

        return novel_lines

    def _create_spectral_report(self, source_id: str, score: float,
                                features: Dict, standardized: Dict,
                                novel_lines: List[Dict]) -> AnomalyReport:
        """Create spectral anomaly report."""
        if len(novel_lines) > 0:
            anomaly_type = "novel_emission_lines"
            description = f"Detected {len(novel_lines)} novel spectral lines"
        elif abs(standardized.get('line_ratio', 0)) > 3:
            anomaly_type = "unusual_line_ratio"
            description = f"Unusual line ratio: {features['line_ratio']:.2f}"
        else:
            anomaly_type = "peculiar_spectrum"
            description = "Peculiar spectrum shape"

        return AnomalyReport(
            anomaly_id=f"spec_{source_id}_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            source_id=source_id,
            anomaly_type=anomaly_type,
            anomaly_score=score,
            confidence=score,
            description=description,
            features=features,
            suggested_observations=[
                "Obtain higher resolution spectrum",
                "Multi-epoch spectroscopy to monitor changes",
                "Cross-match with other wavelengths"
            ],
            metadata={'novel_lines': novel_lines}
        )


class RealTimeAnomalyDetector:
    """
    Unified real-time anomaly detection system.

    Combines multiple anomaly detectors for different data types:
    - Light curves
    - Spectra
    - Transients
    - Catalog sources

    Example:
        >>> detector = RealTimeAnomalyDetector()
        >>>
        >>> # Add light curve data
        >>> report = detector.update_light_curve("source_1", 59000.5, 15.2)
        >>> if report:
        ...     print(f"Anomaly detected: {report.description}")
    """

    def __init__(self):
        """Initialize anomaly detection system."""
        # Light curve detector
        self.lc_detector = LightCurveAnomalyDetector()

        # Spectral detector (requires wavelength grid)
        # Will be initialized when first spectrum is received

        # History
        self.reports: List[AnomalyReport] = []

        # Statistics
        self.stats = defaultdict(int)

    def update_light_curve(self, source_id: str, time: float,
                           magnitude: float, error: float = 0.0) -> Optional[AnomalyReport]:
        """
        Update with light curve data.

        Args:
            source_id: Source identifier
            time: Observation time
            magnitude: Magnitude measurement
            error: Magnitude error

        Returns:
            AnomalyReport if anomaly detected
        """
        self.stats['lc_updates'] += 1

        report = self.lc_detector.update(source_id, time, magnitude, error)

        if report:
            self.reports.append(report)
            self.stats['lc_anomalies'] += 1

        return report

    def update_spectrum(self, source_id: str, wavelength: np.ndarray,
                        flux: np.ndarray, error: Optional[np.ndarray] = None) -> Optional[AnomalyReport]:
        """
        Update with spectral data.

        Args:
            source_id: Source identifier
            wavelength: Wavelength grid (Angstroms)
            flux: Flux values
            error: Flux errors

        Returns:
            AnomalyReport if anomaly detected
        """
        self.stats['spec_updates'] += 1

        # Initialize detector if needed
        if not hasattr(self, 'spec_detector'):
            self.spec_detector = SpectralAnomalyDetector(wavelength)

        report = self.spec_detector.update(source_id, flux, error)

        if report:
            self.reports.append(report)
            self.stats['spec_anomalies'] += 1

        return report

    def get_recent_anomalies(self, n: int = 10) -> List[AnomalyReport]:
        """Get n most recent anomaly reports."""
        return self.reports[-n:]

    def get_statistics(self) -> Dict[str, int]:
        """Get detection statistics."""
        return dict(self.stats)


def create_anomaly_detector(**kwargs) -> RealTimeAnomalyDetector:
    """
    Factory function to create anomaly detector.

    Args:
        **kwargs: Arguments (for future expansion)

    Returns:
        Configured anomaly detector
    """
    return RealTimeAnomalyDetector(**kwargs)


if __name__ == "__main__":
    print("="*70)
    print("Real-Time Anomaly Detection")
    print("="*70)
    print()
    print("Components:")
    print("  - RealTimeAnomalyDetector: Main detection system")
    print("  - LightCurveAnomalyDetector: Light curve anomalies")
    print("  - SpectralAnomalyDetector: Spectral anomalies")
    print("  - IsolationForestOnline: Online isolation forest")
    print("  - OnlineStandardScaler: Online feature standardization")
    print()
    print("Anomaly Types:")
    print("  - Unusual light curve variability")
    print("  - Novel emission/absorption lines")
    print("  - Peculiar spectral shapes")
    print("  - Period and amplitude changes")
    print()
    print("="*70)
