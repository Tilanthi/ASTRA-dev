"""
V70 Predictive Information Geometry
====================================

A unified framework where all data types live on the same manifold:
- Information-theoretic distance metrics
- Cross-modal prediction (predict price from order flow topology)
- Automatic representation learning
- Compression for insight extraction

Key Innovation: All data becomes comparable through information geometry,
enabling cross-domain prediction and transfer.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Union
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from collections import defaultdict
import time


class DataModality(Enum):
    """Types of data modalities"""
    SCALAR = "scalar"
    VECTOR = "vector"
    TIME_SERIES = "time_series"
    GRAPH = "graph"
    DISTRIBUTION = "distribution"
    SEQUENCE = "sequence"
    TENSOR = "tensor"
    CATEGORICAL = "categorical"
    MIXED = "mixed"


class DistanceMetric(Enum):
    """Information-geometric distance metrics"""
    EUCLIDEAN = "euclidean"
    FISHER_RAO = "fisher_rao"
    KL_DIVERGENCE = "kl_divergence"
    WASSERSTEIN = "wasserstein"
    HELLINGER = "hellinger"
    MAHALANOBIS = "mahalanobis"
    GEODESIC = "geodesic"


class ManifoldType(Enum):
    """Types of statistical manifolds"""
    GAUSSIAN = "gaussian"
    EXPONENTIAL = "exponential"
    SIMPLEX = "simplex"
    SPHERE = "sphere"
    HYPERBOLIC = "hyperbolic"
    PRODUCT = "product"


@dataclass
class InformationPoint:
    """A point on the information manifold"""
    id: str
    coordinates: np.ndarray  # Coordinates on manifold
    modality: DataModality
    original_data: Any
    sufficient_statistics: Dict[str, float] = field(default_factory=dict)
    natural_parameters: Dict[str, float] = field(default_factory=dict)
    information_content: float = 0.0
    uncertainty: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def distance_to(
        self,
        other: 'InformationPoint',
        metric: DistanceMetric = DistanceMetric.EUCLIDEAN
    ) -> float:
        """Compute distance to another point"""
        if metric == DistanceMetric.EUCLIDEAN:
            return np.linalg.norm(self.coordinates - other.coordinates)
        elif metric == DistanceMetric.FISHER_RAO:
            # Fisher-Rao metric for distributions
            return fisher_rao_distance(self.coordinates, other.coordinates)
        elif metric == DistanceMetric.KL_DIVERGENCE:
            return kl_divergence(self.coordinates, other.coordinates)
        elif metric == DistanceMetric.HELLINGER:
            return hellinger_distance(self.coordinates, other.coordinates)
        else:
            return np.linalg.norm(self.coordinates - other.coordinates)


@dataclass
class ManifoldRegion:
    """A region on the information manifold"""
    id: str
    center: InformationPoint
    radius: float
    points: List[str] = field(default_factory=list)  # Point IDs
    semantic_label: Optional[str] = None
    predictive_features: Dict[str, float] = field(default_factory=dict)


@dataclass
class GeodesicPath:
    """A geodesic path between points on the manifold"""
    start_id: str
    end_id: str
    waypoints: List[np.ndarray]
    path_length: float
    curvature: float = 0.0
    predictive_gradient: Optional[np.ndarray] = None


@dataclass
class PredictiveRelation:
    """A predictive relationship between manifold regions"""
    source_region: str
    target_region: str
    prediction_function: Callable
    mutual_information: float
    confidence: float
    lag: int = 0  # Time lag for temporal prediction


# Distance functions
def fisher_rao_distance(p: np.ndarray, q: np.ndarray) -> float:
    """Fisher-Rao distance between distributions"""
    # For probability vectors
    p = np.clip(p, 1e-10, 1)
    q = np.clip(q, 1e-10, 1)
    p = p / np.sum(p)
    q = q / np.sum(q)
    return 2 * np.arccos(np.clip(np.sum(np.sqrt(p * q)), -1, 1))


def kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """KL divergence D(p||q)"""
    p = np.clip(p, 1e-10, 1)
    q = np.clip(q, 1e-10, 1)
    p = p / np.sum(p)
    q = q / np.sum(q)
    return np.sum(p * np.log(p / q))


def hellinger_distance(p: np.ndarray, q: np.ndarray) -> float:
    """Hellinger distance"""
    p = np.clip(p, 1e-10, 1)
    q = np.clip(q, 1e-10, 1)
    p = p / np.sum(p)
    q = q / np.sum(q)
    return np.sqrt(0.5 * np.sum((np.sqrt(p) - np.sqrt(q)) ** 2))


def wasserstein_1d(p: np.ndarray, q: np.ndarray) -> float:
    """1D Wasserstein distance"""
    p_sorted = np.sort(p)
    q_sorted = np.sort(q)
    n = min(len(p_sorted), len(q_sorted))
    return np.mean(np.abs(p_sorted[:n] - q_sorted[:n]))


class DataEncoder(ABC):
    """Abstract encoder for converting data to manifold coordinates"""

    @abstractmethod
    def encode(self, data: Any) -> np.ndarray:
        """Encode data to manifold coordinates"""
        pass

    @abstractmethod
    def decode(self, coordinates: np.ndarray) -> Any:
        """Decode coordinates back to data"""
        pass

    @abstractmethod
    def get_modality(self) -> DataModality:
        """Get the modality this encoder handles"""
        pass


class ScalarEncoder(DataEncoder):
    """Encoder for scalar values"""

    def __init__(self, dimension: int = 8):
        self.dimension = dimension
        self.scale = 1.0
        self.offset = 0.0

    def encode(self, data: float) -> np.ndarray:
        """Encode scalar to coordinate vector"""
        normalized = (data - self.offset) / (self.scale + 1e-10)
        # Create multi-scale representation
        coords = np.array([
            normalized,
            np.sin(normalized * np.pi),
            np.cos(normalized * np.pi),
            np.tanh(normalized),
            np.sign(normalized) * np.log(abs(normalized) + 1),
            normalized ** 2,
            normalized ** 3 if abs(normalized) < 10 else np.sign(normalized) * 10,
            np.exp(-normalized ** 2)
        ])[:self.dimension]
        return coords

    def decode(self, coordinates: np.ndarray) -> float:
        """Decode to scalar"""
        return coordinates[0] * self.scale + self.offset

    def get_modality(self) -> DataModality:
        return DataModality.SCALAR

    def fit(self, data: List[float]):
        """Fit encoder to data"""
        self.scale = np.std(data) + 1e-10
        self.offset = np.mean(data)


class TimeSeriesEncoder(DataEncoder):
    """Encoder for time series data"""

    def __init__(self, dimension: int = 32, window: int = 20):
        self.dimension = dimension
        self.window = window
        self.mean = 0.0
        self.std = 1.0

    def encode(self, data: np.ndarray) -> np.ndarray:
        """Encode time series to coordinate vector"""
        # Normalize
        normalized = (data - self.mean) / (self.std + 1e-10)

        # Extract features
        features = []

        # Statistical features
        features.append(np.mean(normalized))
        features.append(np.std(normalized))
        features.append(np.min(normalized))
        features.append(np.max(normalized))

        # Trend features
        if len(normalized) > 1:
            diff = np.diff(normalized)
            features.append(np.mean(diff))
            features.append(np.std(diff))
        else:
            features.extend([0, 0])

        # Autocorrelation features
        for lag in [1, 2, 5, 10]:
            if len(normalized) > lag:
                ac = np.corrcoef(normalized[:-lag], normalized[lag:])[0, 1]
                features.append(ac if not np.isnan(ac) else 0)
            else:
                features.append(0)

        # Spectral features (simplified FFT)
        if len(normalized) >= 4:
            fft = np.abs(np.fft.fft(normalized))[:len(normalized)//2]
            features.append(np.argmax(fft) / len(fft))  # Dominant frequency
            features.append(np.sum(fft[:len(fft)//4]) / (np.sum(fft) + 1e-10))  # Low freq ratio
        else:
            features.extend([0, 0])

        # Pad or truncate to dimension
        coords = np.array(features[:self.dimension])
        if len(coords) < self.dimension:
            coords = np.pad(coords, (0, self.dimension - len(coords)))

        return coords

    def decode(self, coordinates: np.ndarray) -> np.ndarray:
        """Decode to time series (reconstruction)"""
        # Simplified reconstruction using mean and std
        length = self.window
        mean_val = coordinates[0] * self.std + self.mean
        std_val = abs(coordinates[1]) * self.std

        return np.random.normal(mean_val, std_val + 0.01, length)

    def get_modality(self) -> DataModality:
        return DataModality.TIME_SERIES

    def fit(self, data: List[np.ndarray]):
        """Fit encoder to data"""
        all_values = np.concatenate(data)
        self.mean = np.mean(all_values)
        self.std = np.std(all_values) + 1e-10


class DistributionEncoder(DataEncoder):
    """Encoder for probability distributions"""

    def __init__(self, dimension: int = 16):
        self.dimension = dimension

    def encode(self, data: np.ndarray) -> np.ndarray:
        """Encode distribution to coordinate vector"""
        # Normalize to probability
        p = np.clip(data, 1e-10, None)
        p = p / np.sum(p)

        # Natural parameters (log probabilities)
        log_p = np.log(p)

        # Sufficient statistics
        features = [
            np.sum(p * np.log(p + 1e-10)),  # Negative entropy
            np.max(p),  # Mode probability
            np.sum(p ** 2),  # Gini coefficient related
            len(p[p > 0.01]) / len(p),  # Effective support
        ]

        # Add distribution moments
        indices = np.arange(len(p))
        mean_idx = np.sum(p * indices)
        var_idx = np.sum(p * (indices - mean_idx) ** 2)
        features.extend([mean_idx / len(p), var_idx / len(p)])

        # Add log probabilities (truncated)
        features.extend(log_p[:self.dimension - len(features)].tolist())

        coords = np.array(features[:self.dimension])
        if len(coords) < self.dimension:
            coords = np.pad(coords, (0, self.dimension - len(coords)))

        return coords

    def decode(self, coordinates: np.ndarray) -> np.ndarray:
        """Decode to distribution"""
        # Use stored log probabilities
        log_p = coordinates[6:self.dimension]
        p = np.exp(log_p - np.max(log_p))  # Softmax-like
        return p / np.sum(p)

    def get_modality(self) -> DataModality:
        return DataModality.DISTRIBUTION


class GraphEncoder(DataEncoder):
    """Encoder for graph-structured data"""

    def __init__(self, dimension: int = 24):
        self.dimension = dimension

    def encode(self, data: Dict[str, Any]) -> np.ndarray:
        """Encode graph to coordinate vector"""
        # Expect data = {'adjacency': np.ndarray, 'features': np.ndarray}
        adj = data.get('adjacency', np.array([[0]]))
        features = data.get('features', np.array([[0]]))

        n_nodes = adj.shape[0]
        n_edges = np.sum(adj > 0) / 2  # Undirected

        # Graph statistics
        graph_features = [
            n_nodes,
            n_edges,
            n_edges / (n_nodes * (n_nodes - 1) / 2 + 1e-10),  # Density
            np.mean(np.sum(adj, axis=1)),  # Avg degree
            np.std(np.sum(adj, axis=1)),  # Std degree
            np.sum(adj.diagonal()),  # Self-loops
        ]

        # Pad to dimension
        encoding = np.zeros(self.dimension)
        encoding[:len(graph_features)] = graph_features[:self.dimension]

        return encoding
