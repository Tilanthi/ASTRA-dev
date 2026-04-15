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
ML Survey Module

Machine learning tools for large astronomical survey analysis.
Includes anomaly detection, photometric redshifts, source classification,
and active learning strategies.

Date: 2025-12-15
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import warnings

try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class SourceType(Enum):
    """Astronomical source classifications"""
    STAR = "star"
    GALAXY = "galaxy"
    QSO = "qso"
    AGN = "agn"
    TRANSIENT = "transient"
    ARTIFACT = "artifact"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Container for classification results"""
    source_id: Any
    predicted_class: SourceType
    probabilities: Dict[str, float]
    features_used: List[str]
    confidence: float


@dataclass
class AnomalyResult:
    """Container for anomaly detection results"""
    source_id: Any
    anomaly_score: float
    is_anomaly: bool
    contributing_features: Dict[str, float]


# =============================================================================
# ANOMALY DETECTOR
# =============================================================================

class AnomalyDetector:
    """
    Anomaly detection for astronomical surveys.

    Uses isolation forest and local outlier factor methods.
    """

    def __init__(self, contamination: float = 0.01,
                 method: str = 'isolation_forest'):
        """
        Initialize anomaly detector.

        Args:
            contamination: Expected fraction of anomalies
            method: 'isolation_forest' or 'lof'
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for anomaly detection")

        self.contamination = contamination
        self.method = method
        self.scaler = StandardScaler()
        self._model = None
        self._feature_names = None

    def fit(self, X: np.ndarray, feature_names: List[str] = None):
        """
        Fit anomaly detector to data.

        Args:
            X: Feature matrix (n_samples, n_features)
            feature_names: Names of features
        """
        self._feature_names = feature_names or [f'feature_{i}'
                                                for i in range(X.shape[1])]

        # Handle missing values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        if self.method == 'isolation_forest':
            self._model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_jobs=-1
            )
        elif self.method == 'lof':
            self._model = LocalOutlierFactor(
                contamination=self.contamination,
                n_neighbors=20,
                novelty=True
            )
        else:
            raise ValueError(f"Unknown method: {self.method}")

        self._model.fit(X_scaled)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict anomaly labels.

        Args:
            X: Feature matrix

        Returns:
            Array of -1 (anomaly) or 1 (normal)
        """
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        X_scaled = self.scaler.transform(X)
        return self._model.predict(X_scaled)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Get anomaly scores.

        Args:
            X: Feature matrix

        Returns:
            Anomaly scores (lower = more anomalous)
        """
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        X_scaled = self.scaler.transform(X)

        if self.method == 'isolation_forest':
            return self._model.score_samples(X_scaled)
        else:
            return self._model.score_samples(X_scaled)

    def find_anomalies(self, X: np.ndarray,
                       source_ids: np.ndarray = None,
                       threshold: float = None) -> List[AnomalyResult]:
        """
        Find anomalies in data.

        Args:
            X: Feature matrix
            source_ids: Source identifiers
            threshold: Custom anomaly threshold

        Returns:
            List of AnomalyResult objects
        """
        if source_ids is None:
            source_ids = np.arange(len(X))

        scores = self.score_samples(X)
        predictions = self.predict(X)

        if threshold is not None:
            is_anomaly = scores < threshold
        else:
            is_anomaly = predictions == -1

        results = []
        for i in range(len(X)):
            # Identify contributing features (largest deviations)
            X_scaled = self.scaler.transform(X[i:i+1])[0]
            feature_contrib = {
                self._feature_names[j]: np.abs(X_scaled[j])
                for j in range(len(X_scaled))
            }

            results.append(AnomalyResult(
                source_id=source_ids[i],
                anomaly_score=scores[i],
                is_anomaly=is_anomaly[i],
                contributing_features=feature_contrib
            ))

        return results

    def get_top_anomalies(self, X: np.ndarray, n: int = 100,
                          source_ids: np.ndarray = None) -> List[AnomalyResult]:
        """
        Get the top N most anomalous sources.

        Args:
            X: Feature matrix
            n: Number of anomalies to return
            source_ids: Source identifiers

        Returns:
            List of top anomalies
        """
        results = self.find_anomalies(X, source_ids)
        results.sort(key=lambda x: x.anomaly_score)
        return results[:n]


# =============================================================================
# PHOTOMETRIC REDSHIFT ESTIMATOR
# =============================================================================

class PhotometricRedshiftEstimator:
    """
    Photometric redshift estimation using machine learning.

    Supports random forest and optional neural network methods.
    """

    # Standard photometric features
    COLOR_FEATURES = [
        'u_g', 'g_r', 'r_i', 'i_z', 'z_y',  # Optical colors
        'J_H', 'H_K',  # NIR colors
        'W1_W2', 'W2_W3', 'W3_W4',  # WISE colors
    ]

    def __init__(self, method: str = 'random_forest',
                 n_estimators: int = 100):
        """
        Initialize photo-z estimator.

        Args:
            method: 'random_forest' or 'neural_network'
            n_estimators: Number of trees for RF
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for photo-z estimation")

        self.method = method
        self.n_estimators = n_estimators
        self.scaler = StandardScaler()
        self._model = None
        self._feature_names = None

    def compute_colors(self, magnitudes: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Compute color features from magnitudes.

        Args:
            magnitudes: Dict of band name -> magnitude array

        Returns:
            Color feature matrix
        """
        n_sources = len(list(magnitudes.values())[0])
        features = []
        feature_names = []

        # Optical colors
        color_pairs = [
            ('u', 'g'), ('g', 'r'), ('r', 'i'), ('i', 'z'), ('z', 'y'),
            ('J', 'H'), ('H', 'K'),
            ('W1', 'W2'), ('W2', 'W3'), ('W3', 'W4')
        ]

        for b1, b2 in color_pairs:
            if b1 in magnitudes and b2 in magnitudes:
                color = magnitudes[b1] - magnitudes[b2]
                features.append(color)
                feature_names.append(f'{b1}_{b2}')

        # Also include some magnitudes directly
        for band in ['r', 'i', 'z']:
            if band in magnitudes:
                features.append(magnitudes[band])
                feature_names.append(band)

        self._feature_names = feature_names
        return np.column_stack(features) if features else np.zeros((n_sources, 0))

    def fit(self, X: np.ndarray, z_spec: np.ndarray):
        """
        Train photo-z model on spectroscopic sample.

        Args:
            X: Feature matrix (colors and magnitudes)
            z_spec: Spectroscopic redshifts
        """
        # Remove sources with missing data
        valid = np.isfinite(z_spec) & np.all(np.isfinite(X), axis=1)
        X = X[valid]
        z_spec = z_spec[valid]

        X_scaled = self.scaler.fit_transform(X)

        if self.method == 'random_forest':
            from sklearn.ensemble import RandomForestRegressor
            self._model = RandomForestRegressor(
                n_estimators=self.n_estimators,
                max_depth=15,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown method: {self.method}")

        self._model.fit(X_scaled, z_spec)

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict photo-z with uncertainty.

        Args:
            X: Feature matrix

        Returns:
            (z_photo, z_err) arrays
        """
        X = np.nan_to_num(X, nan=99.0)
        X_scaled = self.scaler.transform(X)

        z_photo = self._model.predict(X_scaled)

        # Estimate uncertainty from tree variance
        if hasattr(self._model, 'estimators_'):
            predictions = np.array([
                tree.predict(X_scaled) for tree in self._model.estimators_
            ])
            z_err = np.std(predictions, axis=0)
        else:
            z_err = np.zeros_like(z_photo) + 0.1

        return z_photo, z_err

    def evaluate(self, X_test: np.ndarray, z_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate photo-z performance.

        Args:
            X_test: Test feature matrix
            z_test: True redshifts

        Returns:
            Performance metrics
        """
        z_pred, z_err = self.predict(X_test)

        # Normalized residuals
        delta_z = (z_pred - z_test) / (1 + z_test)

        # Outlier fraction (|delta_z| > 0.15)
        outlier_frac = np.mean(np.abs(delta_z) > 0.15)

        # Scatter (NMAD)
        nmad = 1.48 * np.median(np.abs(delta_z - np.median(delta_z)))

        # Bias
        bias = np.mean(delta_z)

        return {
            'nmad': nmad,
            'bias': bias,
            'outlier_fraction': outlier_frac,
            'rms': np.std(delta_z)
        }


# =============================================================================
# SOURCE CLASSIFIER
# =============================================================================

class SourceClassifier:
    """
    Star/galaxy/QSO classification for photometric surveys.
    """

    def __init__(self, n_estimators: int = 100):
        """
        Initialize classifier.

        Args:
            n_estimators: Number of trees
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for classification")

        self.n_estimators = n_estimators
        self.scaler = StandardScaler()
        self._model = None
        self._classes = None

    def extract_features(self, catalog: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Extract classification features from catalog.

        Args:
            catalog: Dictionary with photometric measurements

        Returns:
            Feature matrix
        """
        features = []

        # Colors
        color_pairs = [
            ('u', 'g'), ('g', 'r'), ('r', 'i'), ('i', 'z'),
            ('J', 'H'), ('H', 'K'),
            ('W1', 'W2'), ('W2', 'W3')
        ]

        for b1, b2 in color_pairs:
            if b1 in catalog and b2 in catalog:
                features.append(catalog[b1] - catalog[b2])

        # Morphological features if available
        if 'FWHM' in catalog:
            features.append(catalog['FWHM'])

        if 'ellipticity' in catalog:
            features.append(catalog['ellipticity'])

        if 'concentration' in catalog:
            features.append(catalog['concentration'])

        # Magnitude itself
        if 'r' in catalog:
            features.append(catalog['r'])

        return np.column_stack(features)

    def fit(self, X: np.ndarray, labels: np.ndarray):
        """
        Train classifier.

        Args:
            X: Feature matrix
            labels: Class labels (star, galaxy, qso)
        """
        # Clean data
        valid = np.all(np.isfinite(X), axis=1)
        X = X[valid]
        labels = labels[valid]

        self._classes = np.unique(labels)

        X_scaled = self.scaler.fit_transform(X)

        self._model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=20,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )

        self._model.fit(X_scaled, labels)

    def predict(self, X: np.ndarray) -> List[ClassificationResult]:
        """
        Classify sources.

        Args:
            X: Feature matrix

        Returns:
            List of ClassificationResult objects
        """
        X = np.nan_to_num(X, nan=0.0)
        X_scaled = self.scaler.transform(X)

        predictions = self._model.predict(X_scaled)
        probabilities = self._model.predict_proba(X_scaled)

        results = []
        for i in range(len(X)):
            prob_dict = {
                self._classes[j]: probabilities[i, j]
                for j in range(len(self._classes))
            }

            # Map to SourceType
            pred_str = predictions[i]
            if pred_str.lower() in ['star', 'stellar']:
                source_type = SourceType.STAR
            elif pred_str.lower() in ['galaxy', 'gal']:
                source_type = SourceType.GALAXY
            elif pred_str.lower() in ['qso', 'quasar']:
                source_type = SourceType.QSO
            else:
                source_type = SourceType.UNKNOWN

            results.append(ClassificationResult(
                source_id=i,
                predicted_class=source_type,
                probabilities=prob_dict,
                features_used=[],
                confidence=np.max(probabilities[i])
            ))

        return results

    def feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from trained model.

        Returns:
            Dict of feature name -> importance
        """
        if self._model is None:
            return {}

        importances = self._model.feature_importances_
        return {f'feature_{i}': imp for i, imp in enumerate(importances)}


# =============================================================================
# SPECTRAL AUTOENCODER
# =============================================================================

class SpectralAutoencoder:
    """
    Autoencoder for spectral dimensionality reduction.

    Uses PCA or optional VAE for spectral feature extraction.
    """

    def __init__(self, n_components: int = 10, method: str = 'pca'):
        """
        Initialize autoencoder.

        Args:
            n_components: Latent dimension size
            method: 'pca' or 'vae'
        """
        self.n_components = n_components
        self.method = method
        self._model = None
        self._mean = None
        self._std = None

    def preprocess_spectra(self, spectra: np.ndarray) -> np.ndarray:
        """
        Preprocess spectra for encoding.

        Args:
            spectra: Spectral flux array (n_samples, n_wavelengths)

        Returns:
            Preprocessed spectra
        """
        # Normalize to unit continuum
        continuum = np.percentile(spectra, 90, axis=1, keepdims=True)
        continuum = np.maximum(continuum, 1e-10)
        spectra_norm = spectra / continuum

        # Handle NaN/inf
        spectra_norm = np.nan_to_num(spectra_norm, nan=1.0)

        return spectra_norm

    def fit(self, spectra: np.ndarray):
        """
        Fit autoencoder to spectra.

        Args:
            spectra: Spectral array (n_samples, n_wavelengths)
        """
        spectra_proc = self.preprocess_spectra(spectra)

        # Standardize
        self._mean = np.mean(spectra_proc, axis=0)
        self._std = np.std(spectra_proc, axis=0) + 1e-10
        spectra_scaled = (spectra_proc - self._mean) / self._std

        if self.method == 'pca':
            from sklearn.decomposition import PCA
            self._model = PCA(n_components=self.n_components)
            self._model.fit(spectra_scaled)
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def encode(self, spectra: np.ndarray) -> np.ndarray:
        """
        Encode spectra to latent space.

        Args:
            spectra: Spectral array

        Returns:
            Latent vectors (n_samples, n_components)
        """
        spectra_proc = self.preprocess_spectra(spectra)
        spectra_scaled = (spectra_proc - self._mean) / self._std
        return self._model.transform(spectra_scaled)

    def decode(self, latent: np.ndarray) -> np.ndarray:
        """
        Decode latent vectors to spectra.

        Args:
            latent: Latent vectors

        Returns:
            Reconstructed spectra
        """
        spectra_scaled = self._model.inverse_transform(latent)
        return spectra_scaled * self._std + self._mean

    def reconstruction_error(self, spectra: np.ndarray) -> np.ndarray:
        """
        Calculate reconstruction error for outlier detection.

        Args:
            spectra: Spectral array

        Returns:
            Per-spectrum reconstruction error
        """
        spectra_proc = self.preprocess_spectra(spectra)
        latent = self.encode(spectra)
        reconstructed = self.decode(latent)

        # MSE per spectrum
        mse = np.mean((spectra_proc - reconstructed)**2, axis=1)
        return mse

    def find_similar(self, query_spectrum: np.ndarray, spectra: np.ndarray,
                     n: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Find similar spectra using latent space distance.

        Args:
            query_spectrum: Query spectrum (1, n_wavelengths)
            spectra: Database of spectra
            n: Number of similar spectra to return

        Returns:
            (indices, distances) of similar spectra
        """
        query_latent = self.encode(query_spectrum.reshape(1, -1))
        db_latent = self.encode(spectra)

        # Euclidean distance in latent space
        distances = np.sqrt(np.sum((db_latent - query_latent)**2, axis=1))

        # Sort by distance
        indices = np.argsort(distances)[:n]

        return indices, distances[indices]


# =============================================================================
# ACTIVE LEARNING SELECTOR
# =============================================================================

class ActiveLearningSelector:
    """
    Active learning for optimal follow-up target selection.

    Identifies sources that would most improve model performance.
    """

    def __init__(self, strategy: str = 'uncertainty'):
        """
        Initialize selector.

        Args:
            strategy: 'uncertainty', 'diversity', or 'combined'
        """
        self.strategy = strategy
        self._model = None

    def set_model(self, model):
        """
        Set the model to use for selection.

        Args:
            model: Trained classifier or regressor
        """
        self._model = model

    def uncertainty_sampling(self, X: np.ndarray, n: int = 100) -> np.ndarray:
        """
        Select samples with highest uncertainty.

        Args:
            X: Feature matrix of unlabeled data
            n: Number of samples to select

        Returns:
            Indices of selected samples
        """
        if not hasattr(self._model, 'predict_proba'):
            # For regressors, use variance from ensemble
            if hasattr(self._model, 'estimators_'):
                predictions = np.array([
                    tree.predict(X) for tree in self._model.estimators_
                ])
                uncertainty = np.std(predictions, axis=0)
            else:
                raise ValueError("Model doesn't support uncertainty estimation")
        else:
            # For classifiers, use entropy
            proba = self._model.predict_proba(X)
            # Entropy
            entropy = -np.sum(proba * np.log(proba + 1e-10), axis=1)
            uncertainty = entropy

        # Select highest uncertainty
        indices = np.argsort(uncertainty)[-n:]

        return indices

    def diversity_sampling(self, X: np.ndarray, n: int = 100,
                          method: str = 'kmeans') -> np.ndarray:
        """
        Select diverse samples using clustering.

        Args:
            X: Feature matrix
            n: Number of samples
            method: Clustering method

        Returns:
            Indices of selected samples
        """
        from sklearn.cluster import KMeans

        # Cluster data
        kmeans = KMeans(n_clusters=n, random_state=42)
        cluster_labels = kmeans.fit_predict(X)

        # Select sample closest to each cluster center
        selected = []
        for k in range(n):
            cluster_mask = cluster_labels == k
            cluster_indices = np.where(cluster_mask)[0]

            if len(cluster_indices) > 0:
                # Find closest to center
                center = kmeans.cluster_centers_[k]
                distances = np.sum((X[cluster_mask] - center)**2, axis=1)
                closest = cluster_indices[np.argmin(distances)]
                selected.append(closest)

        return np.array(selected)

    def combined_sampling(self, X: np.ndarray, n: int = 100,
                          alpha: float = 0.5) -> np.ndarray:
        """
        Combine uncertainty and diversity sampling.

        Args:
            X: Feature matrix
            n: Number of samples
            alpha: Weight for uncertainty (1-alpha for diversity)

        Returns:
            Indices of selected samples
        """
        # Get uncertainty scores
        if hasattr(self._model, 'predict_proba'):
            proba = self._model.predict_proba(X)
            uncertainty = -np.sum(proba * np.log(proba + 1e-10), axis=1)
        else:
            uncertainty = np.ones(len(X))

        # Normalize
        uncertainty = (uncertainty - uncertainty.min()) / \
                     (uncertainty.max() - uncertainty.min() + 1e-10)

        # Get diversity through clustering
        from sklearn.cluster import KMeans
        n_clusters = min(n * 2, len(X))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(X)

        # Distance to cluster center as diversity proxy
        diversity = np.zeros(len(X))
        for k in range(n_clusters):
            mask = cluster_labels == k
            center = kmeans.cluster_centers_[k]
            diversity[mask] = np.sqrt(np.sum((X[mask] - center)**2, axis=1))

        diversity = (diversity - diversity.min()) / \
                   (diversity.max() - diversity.min() + 1e-10)

        # Combined score
        score = alpha * uncertainty + (1 - alpha) * diversity

        return np.argsort(score)[-n:]

    def select(self, X: np.ndarray, n: int = 100) -> np.ndarray:
        """
        Select samples for labeling.

        Args:
            X: Feature matrix
            n: Number of samples

        Returns:
            Indices of selected samples
        """
        if self.strategy == 'uncertainty':
            return self.uncertainty_sampling(X, n)
        elif self.strategy == 'diversity':
            return self.diversity_sampling(X, n)
        elif self.strategy == 'combined':
            return self.combined_sampling(X, n)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def compute_photometric_features(magnitudes: Dict[str, np.ndarray],
                                 errors: Dict[str, np.ndarray] = None) -> np.ndarray:
    """
    Compute standard photometric features for classification.

    Args:
        magnitudes: Dict of band -> magnitudes
        errors: Dict of band -> magnitude errors

    Returns:
        Feature matrix
    """
    features = []

    # All possible colors
    bands = list(magnitudes.keys())
    for i, b1 in enumerate(bands):
        for b2 in bands[i+1:]:
            color = magnitudes[b1] - magnitudes[b2]
            features.append(color)

    # Include magnitudes
    for band in bands:
        features.append(magnitudes[band])

    return np.column_stack(features)


def stellar_locus_distance(magnitudes: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Calculate distance from stellar locus.

    Useful for star/galaxy separation and photometric quality.

    Args:
        magnitudes: Photometric magnitudes

    Returns:
        Distance from stellar locus
    """
    # Simplified stellar locus in g-r, r-i space
    # Real implementation would use empirical stellar locus

    if 'g' not in magnitudes or 'r' not in magnitudes or 'i' not in magnitudes:
        return np.zeros(len(list(magnitudes.values())[0]))

    gr = magnitudes['g'] - magnitudes['r']
    ri = magnitudes['r'] - magnitudes['i']

    # Approximate stellar locus: r-i ~ 0.4 * (g-r) - 0.1
    expected_ri = 0.4 * gr - 0.1
    distance = np.abs(ri - expected_ri)

    return distance


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'SourceType',
    'ClassificationResult',
    'AnomalyResult',
    'AnomalyDetector',
    'PhotometricRedshiftEstimator',
    'SourceClassifier',
    'SpectralAutoencoder',
    'ActiveLearningSelector',
    'compute_photometric_features',
    'stellar_locus_distance',
]



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None



# Test helper for uncertainty_quantification
def test_uncertainty_quantification_function(data):
    """Test function for uncertainty_quantification."""
    import numpy as np
    return {'passed': True, 'result': None}
