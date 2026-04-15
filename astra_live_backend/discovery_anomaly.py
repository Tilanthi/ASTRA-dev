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
ASTRA Live — Discovery Anomaly Detection
Multi-method anomaly detection for astronomical discovery.

Enhances the system's anomaly.py (which monitors ASTRA's internal state)
by providing outlier detection for observational and simulation data.

Methods:
  - Isolation Forest: Efficient for high-dimensional data
  - One-Class SVM: Boundary-based anomaly detection
  - Local Outlier Factor: Density-based local anomalies
  - Ensemble: Combines multiple methods for robustness

Use Cases:
  - Discover unusual filaments in HGBS data
  - Find outlier galaxies in survey catalogs
  - Detect novel spectral patterns
  - Identify anomalous simulation results
"""

import numpy as np
import warnings
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import json

# Handle optional sklearn import
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.svm import OneClassSVM
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available. Anomaly detection will be limited.")


@dataclass
class AnomalyReport:
    """Report from anomaly detection analysis."""
    method: str
    n_anomalies: int
    anomaly_indices: np.ndarray
    anomaly_scores: np.ndarray
    threshold: float
    feature_importance: Optional[Dict[str, float]] = None
    explanation: Optional[str] = None


class DiscoveryAnomalyDetector:
    """
    Multi-method anomaly detection for astronomical discovery.

    Unlike anomaly.py (which monitors ASTRA's internal state),
    this module detects outliers in external data.

    Example:
        >>> detector = DiscoveryAnomalyDetector()
        >>> data = np.load('filament_features.npy')  # shape: (n_samples, n_features)
        >>> report = detector.detect_isolation_forest(data, contamination=0.1)
        >>> print(f"Found {report.n_anomalies} anomalous filaments")
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize anomaly detector.

        Args:
            random_state: Random seed for reproducibility
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for anomaly detection. "
                            "Install with: pip install scikit-learn")

        self.random_state = random_state
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% variance
        self._fitted = False

    def _preprocess(self, data: np.ndarray, fit: bool = True) -> np.ndarray:
        """
        Preprocess data: scaling and optional PCA.

        Args:
            data: Input data (n_samples, n_features)
            fit: Whether to fit scaler/PCA (True for training)

        Returns:
            Preprocessed data
        """
        if fit:
            scaled = self.scaler.fit_transform(data)
            reduced = self.pca.fit_transform(scaled)
            self._fitted = True
        else:
            if not self._fitted:
                raise RuntimeError("Detector not fitted. Call with fit=True first.")
            scaled = self.scaler.transform(data)
            reduced = self.pca.transform(scaled)

        return reduced

    def detect_isolation_forest(
        self,
        data: np.ndarray,
        contamination: float = 0.1,
        feature_names: Optional[List[str]] = None
    ) -> AnomalyReport:
        """
        Detect anomalies using Isolation Forest.

        Isolation Forest is particularly effective for:
        - High-dimensional data
        - Large datasets
        - Global anomalies (points far from the main distribution)

        Args:
            data: Input data (n_samples, n_features)
            contamination: Expected proportion of outliers
            feature_names: Names of features for interpretability

        Returns:
            AnomalyReport with results
        """
        # Preprocess
        X = self._preprocess(data, fit=True)

        # Fit Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=self.random_state,
            n_jobs=-1  # Use all cores
        )
        iso_forest.fit(X)

        # Get predictions and scores
        predictions = iso_forest.predict(X)  # -1 for anomalies, 1 for normal
        scores = iso_forest.score_samples(X)  # Lower = more anomalous

        # Extract anomalies
        anomaly_mask = predictions == -1
        anomaly_indices = np.where(anomaly_mask)[0]
        anomaly_scores = scores[anomaly_mask]

        # Feature importance (based on decision paths)
        # This is a simplified approach
        feature_importance = None
        if feature_names is not None and len(feature_names) == data.shape[1]:
            # Use PCA loadings as proxy for feature importance
            loadings = np.abs(self.pca.components_[0])  # First PC
            importance = dict(zip(feature_names, loadings / loadings.sum()))
            feature_importance = importance

        explanation = (
            f"Isolation Forest detected {len(anomaly_indices)} anomalies "
            f"({100*len(anomaly_indices)/len(data):.1f}%) using {X.shape[1]} "
            f"principal components (from {data.shape[1]} original features). "
            f"Contamination threshold: {contamination}."
        )

        return AnomalyReport(
            method="isolation_forest",
            n_anomalies=len(anomaly_indices),
            anomaly_indices=anomaly_indices,
            anomaly_scores=anomaly_scores,
            threshold=iso_forest.threshold_,
            feature_importance=feature_importance,
            explanation=explanation
        )

    def detect_one_class_svm(
        self,
        data: np.ndarray,
        nu: float = 0.1,
        feature_names: Optional[List[str]] = None
    ) -> AnomalyReport:
        """
        Detect anomalies using One-Class SVM.

        One-Class SVM is useful for:
        - Complex, non-linear decision boundaries
        - Moderate-sized datasets
        - When the normal data has a specific distribution

        Args:
            data: Input data (n_samples, n_features)
            nu: Upper bound on fraction of outliers (similar to contamination)
            feature_names: Names of features for interpretability

        Returns:
            AnomalyReport with results
        """
        # Preprocess
        X = self._preprocess(data, fit=True)

        # Fit One-Class SVM
        svm = OneClassSVM(
            nu=nu,
            kernel='rbf',
            gamma='scale',
            random_state=self.random_state
        )
        svm.fit(X)

        # Get predictions and scores
        predictions = svm.predict(X)
        scores = svm.score_samples(X)

        # Extract anomalies
        anomaly_mask = predictions == -1
        anomaly_indices = np.where(anomaly_mask)[0]
        anomaly_scores = scores[anomaly_indices]

        explanation = (
            f"One-Class SVM detected {len(anomaly_indices)} anomalies "
            f"({100*len(anomaly_indices)/len(data):.1f}%) using RBF kernel. "
            f"nu parameter: {nu}."
        )

        return AnomalyReport(
            method="one_class_svm",
            n_anomalies=len(anomaly_indices),
            anomaly_indices=anomaly_indices,
            anomaly_scores=anomaly_scores,
            threshold=0.0,  # SVM doesn't have a simple threshold
            feature_importance=None,
            explanation=explanation
        )

    def detect_local_outlier_factor(
        self,
        data: np.ndarray,
        contamination: float = 0.1,
        n_neighbors: int = 20
    ) -> AnomalyReport:
        """
        Detect anomalies using Local Outlier Factor.

        LOF is effective for:
        - Detecting local anomalies (points in low-density regions)
        - Clusters with varying density
        - When anomalies are context-dependent

        Args:
            data: Input data (n_samples, n_features)
            contamination: Expected proportion of outliers
            n_neighbors: Number of neighbors for LOF calculation

        Returns:
            AnomalyReport with results
        """
        # Preprocess
        X = self._preprocess(data, fit=True)

        # Fit LOF
        lof = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination,
            n_jobs=-1
        )
        predictions = lof.fit_predict(X)

        # LOF doesn't have score_samples for new data, only fit_predict
        # Negative outlier factor means anomaly
        anomaly_mask = predictions == -1
        anomaly_indices = np.where(anomaly_mask)[0]

        # Get LOF scores (negative)
        lof_scores = lof.negative_outlier_factor_

        explanation = (
            f"LOF detected {len(anomaly_indices)} local anomalies "
            f"({100*len(anomaly_indices)/len(data):.1f}%) using {n_neighbors} neighbors. "
            f"LOF is particularly good at finding local outliers in clusters."
        )

        return AnomalyReport(
            method="local_outlier_factor",
            n_anomalies=len(anomaly_indices),
            anomaly_indices=anomaly_indices,
            anomaly_scores=lof_scores[anomaly_indices],
            threshold=0.0,
            feature_importance=None,
            explanation=explanation
        )

    def detect_ensemble(
        self,
        data: np.ndarray,
        contamination: float = 0.1,
        voting: str = 'hard'
    ) -> AnomalyReport:
        """
        Ensemble anomaly detection combining multiple methods.

        Voting strategies:
        - 'hard': Point is anomaly if all methods agree
        - 'soft': Point is anomaly if majority of methods agree
        - 'union': Point is anomaly if any method flags it

        Args:
            data: Input data (n_samples, n_features)
            contamination: Expected proportion of outliers
            voting: Voting strategy ('hard', 'soft', 'union')

        Returns:
            AnomalyReport with ensemble results
        """
        n_samples = data.shape[0]

        # Run all methods
        iso_report = self.detect_isolation_forest(data, contamination)
        svm_report = self.detect_one_class_svm(data, nu=contamination)

        # Create binary masks
        iso_mask = np.zeros(n_samples, dtype=bool)
        iso_mask[iso_report.anomaly_indices] = True

        svm_mask = np.zeros(n_samples, dtype=bool)
        svm_mask[svm_report.anomaly_indices] = True

        # Combine based on voting strategy
        if voting == 'hard':
            # All methods must agree
            ensemble_mask = iso_mask & svm_mask
        elif voting == 'soft':
            # Majority must agree (2 out of 2 in this case)
            ensemble_mask = iso_mask | svm_mask
        elif voting == 'union':
            # Any method flags it
            ensemble_mask = iso_mask | svm_mask
        else:
            raise ValueError(f"Unknown voting strategy: {voting}")

        anomaly_indices = np.where(ensemble_mask)[0]

        # Compute ensemble scores (average of normalized scores)
        iso_scores_norm = (iso_report.anomaly_scores - iso_report.anomaly_scores.min()) / \
                         (iso_report.anomaly_scores.max() - iso_report.anomaly_scores.min() + 1e-10)
        svm_scores_norm = (svm_report.anomaly_scores - svm_report.anomaly_scores.min()) / \
                         (svm_report.anomaly_scores.max() - svm_report.anomaly_scores.min() + 1e-10)

        explanation = (
            f"Ensemble detection ({voting} voting) found {len(anomaly_indices)} anomalies "
            f"({100*len(anomaly_indices)/len(data):.1f}%) by combining "
            f"Isolation Forest and One-Class SVM."
        )

        return AnomalyReport(
            method="ensemble",
            n_anomalies=len(anomaly_indices),
            anomaly_indices=anomaly_indices,
            anomaly_scores=np.array([]),  # Ensemble scores would need careful handling
            threshold=contamination,
            feature_importance=iso_report.feature_importance,
            explanation=explanation
        )

    def compare_methods(
        self,
        data: np.ndarray,
        contamination: float = 0.1
    ) -> Dict[str, AnomalyReport]:
        """
        Compare all anomaly detection methods.

        Args:
            data: Input data (n_samples, n_features)
            contamination: Expected proportion of outliers

        Returns:
            Dictionary with method names as keys, AnomalyReports as values
        """
        results = {}

        # Isolation Forest
        try:
            results['isolation_forest'] = self.detect_isolation_forest(
                data, contamination
            )
        except Exception as e:
            warnings.warn(f"Isolation Forest failed: {e}")

        # One-Class SVM
        try:
            results['one_class_svm'] = self.detect_one_class_svm(
                data, nu=contamination
            )
        except Exception as e:
            warnings.warn(f"One-Class SVM failed: {e}")

        # LOF
        try:
            results['local_outlier_factor'] = self.detect_local_outlier_factor(
                data, contamination
            )
        except Exception as e:
            warnings.warn(f"LOF failed: {e}")

        # Ensemble
        if len(results) >= 2:
            try:
                results['ensemble'] = self.detect_ensemble(
                    data, contamination, voting='soft'
                )
            except Exception as e:
                warnings.warn(f"Ensemble failed: {e}")

        return results


class FilamentAnomalyDetector(DiscoveryAnomalyDetector):
    """
    Specialized anomaly detector for HGBS filament data.

    Features expected:
    - width: Filament width (pc)
    - length: Filament length (pc)
    - spacing: Core spacing (pc)
    - n_cores: Number of cores
    - density_mean: Mean density
    - density_std: Density variability
    - ...

    Example:
        >>> detector = FilamentAnomalyDetector()
        >>> filament_data = load_hgbs_data()
        >>> anomalies = detector.detect_isolation_forest(filament_data)
        >>> print(f"Found {anomalies.n_anomalies} unusual filaments")
    """

    FILAMENT_FEATURES = [
        'width_pc', 'length_pc', 'spacing_pc', 'n_cores',
        'density_mean', 'density_std', 'temperature',
        'mass_per_length', 'aspect_ratio', 'contrast'
    ]

    def analyze_filament_population(
        self,
        data: np.ndarray,
        feature_names: List[str] = None,
        contamination: float = 0.05
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of filament population for anomalies.

        Args:
            data: Filament feature data (n_filaments, n_features)
            feature_names: Names of features
            contamination: Expected proportion of outliers

        Returns:
            Comprehensive analysis report
        """
        if feature_names is None:
            feature_names = self.FILAMENT_FEATURES[:data.shape[1]]

        # Compare methods
        comparison = self.compare_methods(data, contamination)

        # Extract ensemble result
        ensemble = comparison.get('ensemble', list(comparison.values())[0])

        # Analyze feature distribution for anomalies
        anomaly_idx = ensemble.anomaly_indices
        normal_idx = np.setdiff1d(np.arange(data.shape[0]), anomaly_idx)

        feature_analysis = {}
        for i, name in enumerate(feature_names):
            if i >= data.shape[1]:
                break

            normal_vals = data[normal_idx, i]
            anomaly_vals = data[anomaly_idx, i]

            feature_analysis[name] = {
                'normal_mean': float(np.mean(normal_vals)),
                'normal_std': float(np.std(normal_vals)),
                'anomaly_mean': float(np.mean(anomaly_vals)) if len(anomaly_vals) > 0 else 0.0,
                'anomaly_std': float(np.std(anomaly_vals)) if len(anomaly_vals) > 0 else 0.0,
                'effect_size': float((np.mean(anomaly_vals) - np.mean(normal_vals)) / np.std(normal_vals))
                                   if len(anomaly_vals) > 0 and np.std(normal_vals) > 0 else 0.0
            }

        return {
            'total_filaments': data.shape[0],
            'n_anomalous': ensemble.n_anomalies,
            'anomaly_fraction': ensemble.n_anomalies / data.shape[0],
            'anomaly_indices': ensemble.anomaly_indices.tolist(),
            'method_comparison': {
                method: {
                    'n_anomalies': report.n_anomalies,
                    'explanation': report.explanation
                }
                for method, report in comparison.items()
            },
            'feature_analysis': feature_analysis,
            'feature_importance': ensemble.feature_importance
        }


# Convenience functions
def detect_anomalies_in_data(
    data: np.ndarray,
    method: str = 'isolation_forest',
    contamination: float = 0.1
) -> AnomalyReport:
    """
    Convenience function for quick anomaly detection.

    Args:
        data: Input data (n_samples, n_features)
        method: Detection method ('isolation_forest', 'one_class_svm', 'lof', 'ensemble')
        contamination: Expected proportion of outliers

    Returns:
        AnomalyReport
    """
    detector = DiscoveryAnomalyDetector()

    if method == 'isolation_forest':
        return detector.detect_isolation_forest(data, contamination)
    elif method == 'one_class_svm':
        return detector.detect_one_class_svm(data, nu=contamination)
    elif method == 'lof':
        return detector.detect_local_outlier_factor(data, contamination)
    elif method == 'ensemble':
        return detector.detect_ensemble(data, contamination)
    else:
        raise ValueError(f"Unknown method: {method}")


if __name__ == '__main__':
    # Test with synthetic data
    print("Testing Discovery Anomaly Detection...")

    # Generate synthetic filament data
    np.random.seed(42)
    n_normal = 100
    n_anomaly = 10
    n_features = 6

    # Normal filaments
    normal_data = np.random.randn(n_normal, n_features)

    # Anomalous filaments (shifted distribution)
    anomaly_data = np.random.randn(n_anomaly, n_features) + 3

    # Combine
    data = np.vstack([normal_data, anomaly_data])

    # Detect anomalies
    detector = FilamentAnomalyDetector()
    report = detector.detect_isolation_forest(data, contamination=0.08)

    print(f"\n{report.explanation}")
    print(f"Found {report.n_anomalies} anomalies out of {data.shape[0]} filaments")
    print(f"Anomaly indices: {report.anomaly_indices}")

    # Comprehensive analysis
    analysis = detector.analyze_filament_population(data)
    print(f"\nFeature analysis:")
    for feature, stats in analysis['feature_analysis'].items():
        if stats['effect_size'] > 0.5:  # Large effect
            print(f"  {feature}: effect size = {stats['effect_size']:.2f}")
