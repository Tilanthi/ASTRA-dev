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
ASTRA Live — SOM Discovery
Self-Organizing Maps for exploratory data analysis and discovery.

Self-Organizing Maps (SOMs) are neural networks that learn to represent
high-dimensional data on a low-dimensional (typically 2D) grid while
preserving topological properties.

Applications in Astronomy:
  - Discover natural groupings in survey data
  - Visualize high-dimensional parameter spaces
  - Identify transition objects and outliers
  - Explore filament sub-populations

Key Features:
  - Automatic clustering of multi-parameter data
  - Topology preservation (nearby points in input space are nearby on map)
  - Visualization of high-dimensional relationships
  - Anomaly detection via quantization error
"""

import numpy as np
import warnings
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

# Handle optional sklearn/minisom imports
try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available. Some features will be limited.")

try:
    from minisom import MiniSom
    MINISOM_AVAILABLE = True
except ImportError:
    MINISOM_AVAILABLE = False
    warnings.warn("minisom not available. Install with: pip install minisom")


@dataclass
class SOMResult:
    """Result from SOM analysis."""
    n_clusters: int
    cluster_labels: np.ndarray
    cluster_centers: np.ndarray
    quantization_error: float
    topographic_error: float
    u_matrix: np.ndarray
    cluster_map: np.ndarray
    anomaly_indices: np.ndarray
    explanation: str


class SOMDiscoverer:
    """
    Self-Organizing Maps for astronomical discovery.

    SOMs reduce high-dimensional data to a 2D grid while preserving
    topology, enabling visualization and discovery of natural groupings.

    Example:
        >>> discoverer = SOMDiscoverer(grid_size=(15, 15))
        >>> data = np.load('galaxy_features.npy')  # (n_samples, n_features)
        >>> result = discoverer.fit_predict(data, n_clusters=5)
        >>> print(f"Found {result.n_clusters} clusters of objects")
        >>> discoverer.visualize(result)  # Shows 2D map with clusters
    """

    def __init__(
        self,
        grid_size: Tuple[int, int] = (20, 20),
        sigma: float = 1.0,
        learning_rate: float = 0.5,
        random_state: int = 42
    ):
        """
        Initialize SOM Discoverer.

        Args:
            grid_size: Size of SOM grid (height, width)
            sigma: Spread of the neighborhood function
            learning_rate: Initial learning rate
            random_state: Random seed for reproducibility
        """
        if not MINISOM_AVAILABLE:
            raise ImportError("minisom is required for SOM discovery. "
                            "Install with: pip install minisom")

        self.grid_size = grid_size
        self.sigma = sigma
        self.learning_rate = learning_rate
        self.random_state = random_state

        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.som = None
        self._fitted = False
        self.feature_names = None

    def _preprocess(self, data: np.ndarray, fit: bool = True) -> np.ndarray:
        """Preprocess data with optional scaling."""
        if self.scaler is not None:
            if fit:
                return self.scaler.fit_transform(data)
            return self.scaler.transform(data)
        return data

    def fit(
        self,
        data: np.ndarray,
        feature_names: Optional[List[str]] = None,
        n_epochs: int = 1000,
        verbose: bool = False
    ) -> 'SOMDiscoverer':
        """
        Train the SOM on data.

        Args:
            data: Input data (n_samples, n_features)
            feature_names: Names of features
            n_epochs: Number of training epochs
            verbose: Whether to print progress

        Returns:
            Self (fitted SOM discoverer)
        """
        self.feature_names = feature_names

        # Preprocess
        X = self._preprocess(data, fit=True)
        n_features = X.shape[1]

        # Initialize SOM
        np.random.seed(self.random_state)
        self.som = MiniSom(
            x=self.grid_size[0],
            y=self.grid_size[1],
            input_len=n_features,
            sigma=self.sigma,
            learning_rate=self.learning_rate,
            neighborhood_function='gaussian',
            random_seed=self.random_state
        )

        # Train
        if verbose:
            print(f"Training {self.grid_size[0]}x{self.grid_size[1]} SOM "
                  f"on {data.shape[0]} samples with {n_features} features...")

        self.som.train_random(
            X,
            num_iteration=n_epochs,
            verbose=verbose
        )

        self._fitted = True
        return self

    def predict(self, data: np.ndarray) -> np.ndarray:
        """
        Find BMU (Best Matching Unit) coordinates for each sample.

        Args:
            data: Input data (n_samples, n_features)

        Returns:
            BMU coordinates (n_samples, 2)
        """
        if not self._fitted:
            raise RuntimeError("SOM not fitted. Call fit() first.")

        X = self._preprocess(data, fit=False)

        # Get coordinates for each sample
        coords = np.array([self.som.winner(x) for x in X])
        return coords

    def fit_predict(
        self,
        data: np.ndarray,
        feature_names: Optional[List[str]] = None,
        n_clusters: int = 5,
        n_epochs: int = 1000,
        verbose: bool = False
    ) -> SOMResult:
        """
        Fit SOM and assign cluster labels.

        This combines SOM dimensionality reduction with clustering
        on the SOM grid to discover natural groupings.

        Args:
            data: Input data (n_samples, n_features)
            feature_names: Names of features
            n_clusters: Number of clusters to identify
            n_epochs: Number of training epochs
            verbose: Whether to print progress

        Returns:
            SOMResult with clusters and analysis
        """
        # Train SOM
        self.fit(data, feature_names, n_epochs, verbose)

        # Get BMU coordinates
        coords = self.predict(data)

        # Convert to 1D indices for clustering
        coords_1d = coords[:, 0] * self.grid_size[1] + coords[:, 1]

        # Cluster on SOM grid
        if SKLEARN_AVAILABLE:
            kmeans = KMeans(n_clusters=n_clusters, random_state=self.random_state, n_init=10)
            cluster_labels = kmeans.fit_predict(coords)
            cluster_centers = kmeans.cluster_centers_
        else:
            # Fallback: simple quantization
            cluster_labels = (coords_1d * n_clusters / (self.grid_size[0] * self.grid_size[1])).astype(int)
            cluster_centers = None

        # Compute metrics
        quantization_error = self._compute_quantization_error(data)
        topographic_error = self._compute_topographic_error(data)

        # Compute U-matrix (distance map)
        u_matrix = self._compute_u_matrix()

        # Create cluster map
        cluster_map = self._create_cluster_map(cluster_labels, coords)

        # Detect anomalies (high quantization error)
        anomaly_indices = self._detect_anomalies(data, threshold=2.0)

        # Generate explanation
        n_samples_per_cluster = [np.sum(cluster_labels == i) for i in range(n_clusters)]
        explanation = (
            f"SOM discovered {n_clusters} clusters in {data.shape[0]} samples "
            f"with {data.shape[1]} features. Cluster sizes: {n_samples_per_cluster}. "
            f"Quantization error: {quantization_error:.4f}, "
            f"Topographic error: {topographic_error:.4f}. "
            f"Detected {len(anomaly_indices)} anomalies."
        )

        return SOMResult(
            n_clusters=n_clusters,
            cluster_labels=cluster_labels,
            cluster_centers=cluster_centers,
            quantization_error=quantization_error,
            topographic_error=topographic_error,
            u_matrix=u_matrix,
            cluster_map=cluster_map,
            anomaly_indices=anomaly_indices,
            explanation=explanation
        )

    def _compute_quantization_error(self, data: np.ndarray) -> float:
        """Compute average distance from each point to its BMU."""
        X = self._preprocess(data, fit=False)

        total_error = 0.0
        for x in X:
            winner = self.som.winner(x)
            weights = self.som.get_weights()[winner]
            total_error += np.linalg.norm(x - weights)

        return total_error / len(X)

    def _compute_topographic_error(self, data: np.ndarray) -> float:
        """
        Compute topographic error (proportion of samples where
        1st and 2nd BMUs are not adjacent on the map).
        """
        X = self._preprocess(data, fit=False)

        not_adjacent = 0
        for x in X:
            # Find distances to all neurons
            weights = self.som.get_weights()
            distances = np.array([[np.linalg.norm(x - w) for w in row] for row in weights])

            # Get 1st and 2nd BMU
            flat_idx = np.argsort(distances.flatten())[:2]
            bmu1 = (flat_idx[0] // self.grid_size[1], flat_idx[0] % self.grid_size[1])
            bmu2 = (flat_idx[1] // self.grid_size[1], flat_idx[1] % self.grid_size[1])

            # Check if adjacent
            if abs(bmu1[0] - bmu2[0]) + abs(bmu1[1] - bmu2[1]) > 1:
                not_adjacent += 1

        return not_adjacent / len(X)

    def _compute_u_matrix(self) -> np.ndarray:
        """
        Compute U-matrix (unified distance matrix).
        Shows distance between neighboring map units.
        """
        weights = self.som.get_weights()
        u_matrix = np.zeros(self.grid_size)

        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                # Get neighbors
                neighbors = []
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        if di == 0 and dj == 0:
                            continue
                        ni, nj = i + di, j + dj
                        if 0 <= ni < self.grid_size[0] and 0 <= nj < self.grid_size[1]:
                            neighbors.append(weights[ni, nj])

                if neighbors:
                    # Average distance to neighbors
                    u_matrix[i, j] = np.mean([np.linalg.norm(weights[i, j] - n) for n in neighbors])

        return u_matrix

    def _create_cluster_map(
        self,
        cluster_labels: np.ndarray,
        coords: np.ndarray
    ) -> np.ndarray:
        """Create a 2D map showing cluster assignments."""
        cluster_map = np.full(self.grid_size, -1, dtype=int)

        for label, (i, j) in zip(cluster_labels, coords):
            if cluster_map[i, j] == -1:
                cluster_map[i, j] = label
            elif cluster_map[i, j] != label:
                # Conflict: multiple clusters map to same neuron
                cluster_map[i, j] = -2

        return cluster_map

    def _detect_anomalies(
        self,
        data: np.ndarray,
        threshold: float = 2.0
    ) -> np.ndarray:
        """
        Detect anomalies based on quantization error.

        Anomalies are points with unusually high distance to their BMU.

        Args:
            data: Input data
            threshold: Z-score threshold for anomaly

        Returns:
            Indices of anomalous samples
        """
        X = self._preprocess(data, fit=False)

        # Compute quantization errors for each sample
        errors = np.array([np.linalg.norm(x - self.som.get_weights()[self.som.winner(x)])
                          for x in X])

        # Z-score normalization
        mean_error = np.mean(errors)
        std_error = np.std(errors)

        if std_error == 0:
            return np.array([])

        z_scores = (errors - mean_error) / std_error
        anomaly_indices = np.where(z_scores > threshold)[0]

        return anomaly_indices

    def get_cluster_profiles(
        self,
        data: np.ndarray,
        cluster_labels: np.ndarray
    ) -> Dict[int, Dict[str, float]]:
        """
        Compute feature profiles for each cluster.

        Args:
            data: Original data
            cluster_labels: Cluster assignments from SOM

        Returns:
            Dictionary mapping cluster ID to feature profiles
        """
        if self.feature_names is None:
            self.feature_names = [f"feature_{i}" for i in range(data.shape[1])]

        profiles = {}

        for cluster_id in np.unique(cluster_labels):
            mask = cluster_labels == cluster_id
            cluster_data = data[mask]

            profile = {}
            for i, name in enumerate(self.feature_names):
                if i >= data.shape[1]:
                    break

                profile[name] = {
                    'mean': float(np.mean(cluster_data[:, i])),
                    'std': float(np.std(cluster_data[:, i])),
                    'min': float(np.min(cluster_data[:, i])),
                    'max': float(np.max(cluster_data[:, i])),
                    'median': float(np.median(cluster_data[:, i]))
                }

            profiles[cluster_id] = profile

        return profiles

    def visualize(
        self,
        result: SOMResult,
        save_path: Optional[str] = None
    ) -> None:
        """
        Visualize SOM results.

        Creates a multi-panel figure showing:
        - U-matrix (distance between map units)
        - Cluster map
        - Sample hits (how many samples per neuron)
        - Component planes (feature visualization)

        Args:
            result: SOMResult from fit_predict
            save_path: Optional path to save figure
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib not available. Cannot visualize.")
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 12))

        # U-matrix
        im0 = axes[0, 0].imshow(result.u_matrix, cmap='viridis', origin='lower')
        axes[0, 0].set_title('U-Matrix (Distance Between Neighbors)')
        axes[0, 0].set_xlabel('X coordinate')
        axes[0, 0].set_ylabel('Y coordinate')
        plt.colorbar(im0, ax=axes[0, 0])

        # Cluster map
        im1 = axes[0, 1].imshow(result.cluster_map, cmap='tab10', origin='lower')
        axes[0, 1].set_title(f'Cluster Map ({result.n_clusters} clusters)')
        axes[0, 1].set_xlabel('X coordinate')
        axes[0, 1].set_ylabel('Y coordinate')

        # Sample hits
        if self._fitted and self.som is not None:
            # Get response map from SOM
            response_map = np.zeros(self.grid_size)
            # (This would need to be computed during fit_predict - simplified here)
            axes[1, 0].imshow(response_map, cmap='Blues', origin='lower')
            axes[1, 0].set_title('Sample Hits (Per Neuron)')
        else:
            axes[1, 0].text(0.5, 0.5, 'SOM not fitted',
                           ha='center', va='center', transform=axes[1, 0].transAxes)

        # Component planes (first 4 features)
        if self._fitted and self.som is not None:
            weights = self.som.get_weights()
            n_features_to_show = min(4, weights.shape[2])

            for i in range(n_features_to_show):
                ax = axes[1, 1] if i == 0 else None
                if ax is not None:
                    # Create composite of first 4 component planes
                    composite = weights[:, :, :4].reshape(self.grid_size[0], self.grid_size[1], 4)
                    composite = (composite - composite.min()) / (composite.max() - composite.min() + 1e-10)
                    axes[1, 1].imshow(composite, origin='lower')
                    axes[1, 1].set_title('Component Planes (First 4 Features)')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved visualization to {save_path}")
        else:
            plt.show()

        plt.close()


class FilamentSOMAnalyzer(SOMDiscoverer):
    """
    Specialized SOM analyzer for HGBS filament data.

    Discovers filament sub-populations based on physical properties:
    - Width, length, aspect ratio
    - Core spacing, number of cores
    - Density, temperature
    - Mass per unit length (supercriticality)

    Example:
        >>> analyzer = FilamentSOMAnalyzer(grid_size=(12, 12))
        >>> filament_data = load_hgbs_filaments()  # (n_filaments, n_features)
        >>> result = analyzer.fit_predict(filament_data, n_clusters=4)
        >>> print(result.explanation)
        >>> analyzer.visualize(result, save_path='filament_som.png')
    """

    FILAMENT_FEATURES = [
        'width_pc',           # Characteristic width
        'length_pc',          # Total length
        'spacing_pc',         # Core spacing
        'n_cores',            # Number of cores
        'density_mean',       # Mean column density
        'density_std',        # Density variability
        'mass_per_length',    # Line mass
        'aspect_ratio',       # Length/width
        'contrast',           # Density contrast
        'temperature'         # Dust temperature
    ]

    def analyze_filament_types(
        self,
        data: np.ndarray,
        n_clusters: int = 4,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of filament types using SOM.

        Args:
            data: Filament feature data (n_filaments, n_features)
            n_clusters: Number of filament types to discover
            feature_names: Names of features

        Returns:
            Comprehensive analysis including cluster profiles,
            physical interpretation, and visualization data
        """
        if feature_names is None:
            feature_names = self.FILAMENT_FEATURES[:data.shape[1]]

        # Fit SOM and predict clusters
        result = self.fit_predict(
            data,
            feature_names=feature_names,
            n_clusters=n_clusters,
            verbose=True
        )

        # Get cluster profiles
        profiles = self.get_cluster_profiles(data, result.cluster_labels)

        # Interpret clusters physically
        interpretations = self._interpret_filament_clusters(
            profiles,
            result.cluster_labels
        )

        return {
            'som_result': {
                'n_clusters': result.n_clusters,
                'quantization_error': result.quantization_error,
                'topographic_error': result.topographic_error,
                'n_anomalous': len(result.anomaly_indices),
                'explanation': result.explanation
            },
            'cluster_profiles': profiles,
            'interpretations': interpretations,
            'anomaly_indices': result.anomaly_indices.tolist(),
            'u_matrix': result.u_matrix.tolist(),
            'cluster_map': result.cluster_map.tolist()
        }

    def _interpret_filament_clusters(
        self,
        profiles: Dict[int, Dict[str, Dict[str, float]]],
        cluster_labels: np.ndarray
    ) -> Dict[int, str]:
        """
        Provide physical interpretation of filament clusters.

        Args:
            profiles: Cluster feature profiles
            cluster_labels: Cluster assignments

        Returns:
            Dictionary mapping cluster ID to interpretation
        """
        interpretations = {}

        for cluster_id, profile in profiles.items():
            # Key physical properties
            width = profile.get('width_pc', {}).get('mean', 0)
            spacing = profile.get('spacing_pc', {}).get('mean', 0)
            mass_per_length = profile.get('mass_per_length', {}).get('mean', 0)
            n_cores = profile.get('n_cores', {}).get('mean', 0)

            # Interpret
            parts = []

            # Width classification
            if width < 0.08:
                parts.append("narrow filaments")
            elif width > 0.15:
                parts.append("wide filaments")
            else:
                parts.append("typical-width filaments")

            # Core spacing
            if spacing < 0.15:
                parts.append("with dense core packing")
            elif spacing > 0.3:
                parts.append("with sparse core spacing")

            # Supercriticality (using mass_per_length as proxy)
            if mass_per_length > 20:
                parts.append("highly supercritical")
            elif mass_per_length < 10:
                parts.append("sub-critical")

            # Number of cores
            if n_cores > 15:
                parts.append("many cores")
            elif n_cores < 5:
                parts.append("few cores")

            # Combine
            interpretation = ", ".join(parts)
            interpretations[cluster_id] = interpretation.capitalize()

        return interpretations


# Convenience functions
def discover_clusters_som(
    data: np.ndarray,
    n_clusters: int = 5,
    grid_size: Tuple[int, int] = (20, 20)
) -> SOMResult:
    """
    Convenience function for SOM-based clustering.

    Args:
        data: Input data (n_samples, n_features)
        n_clusters: Number of clusters to discover
        grid_size: SOM grid size

    Returns:
        SOMResult with clusters and analysis
    """
    discoverer = SOMDiscoverer(grid_size=grid_size)
    return discoverer.fit_predict(data, n_clusters=n_clusters)


if __name__ == '__main__':
    # Test with synthetic filament data
    print("Testing SOM Discovery...")

    # Generate synthetic filament populations
    np.random.seed(42)
    n_per_cluster = 50
    n_features = 6

    # Cluster 1: Narrow, dense, closely-spaced
    cluster1 = np.random.randn(n_per_cluster, n_features) * 0.1
    cluster1[:, 0] += 0.07  # width
    cluster1[:, 2] += 0.15  # spacing

    # Cluster 2: Wide, sparse
    cluster2 = np.random.randn(n_per_cluster, n_features) * 0.2
    cluster2[:, 0] += 0.20  # width
    cluster2[:, 2] += 0.35  # spacing

    # Cluster 3: Intermediate
    cluster3 = np.random.randn(n_per_cluster, n_features) * 0.15
    cluster3[:, 0] += 0.12  # width
    cluster3[:, 2] += 0.22  # spacing

    # Combine
    data = np.vstack([cluster1, cluster2, cluster3])

    # Analyze with SOM
    analyzer = FilamentSOMAnalyzer(grid_size=(12, 12))
    result = analyzer.fit_predict(data, n_clusters=3, verbose=True)

    print(f"\n{result.explanation}")
    print(f"Cluster sizes: {[np.sum(result.cluster_labels == i) for i in range(3)]}")
    print(f"Anomalies: {len(result.anomaly_indices)}")
