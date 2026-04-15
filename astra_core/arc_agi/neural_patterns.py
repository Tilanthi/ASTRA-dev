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
Neural Pattern Recognition for ARC-AGI

Implements neural-inspired pattern recognition:
- Grid embeddings using hand-crafted features
- Similarity-based hypothesis transfer
- Pattern clustering for abstraction
- Learned transformation priorities
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import hashlib

from .grid_dsl import Grid, GridObject, empty_grid


@dataclass
class GridEmbedding:
    """Feature embedding for a grid"""
    # Structural features
    height: int
    width: int
    aspect_ratio: float

    # Color features
    num_colors: int
    color_histogram: np.ndarray  # 10-element histogram
    dominant_color: int
    background_ratio: float

    # Object features
    num_objects: int
    avg_object_size: float
    max_object_size: int
    min_object_size: int
    object_size_variance: float

    # Spatial features
    density: float  # Non-zero pixels / total
    edge_density: float  # Pixels on edges
    center_density: float  # Pixels in center

    # Symmetry features
    horizontal_symmetry: float
    vertical_symmetry: float
    diagonal_symmetry: float
    rotational_symmetry: float

    # Pattern features
    periodicity_h: Optional[int]
    periodicity_v: Optional[int]
    has_frame: bool
    has_grid_lines: bool

    # Connectivity features
    num_connected_regions: int
    largest_region_ratio: float

    def to_vector(self) -> np.ndarray:
        """Convert to fixed-size feature vector"""
        features = [
            self.height / 30.0,  # Normalize to [0, 1]
            self.width / 30.0,
            self.aspect_ratio,
            self.num_colors / 10.0,
            self.dominant_color / 10.0,
            self.background_ratio,
            self.num_objects / 20.0,
            self.avg_object_size / 100.0,
            self.max_object_size / 100.0,
            self.min_object_size / 100.0,
            self.object_size_variance / 100.0,
            self.density,
            self.edge_density,
            self.center_density,
            self.horizontal_symmetry,
            self.vertical_symmetry,
            self.diagonal_symmetry,
            self.rotational_symmetry,
            (self.periodicity_h or 0) / 10.0,
            (self.periodicity_v or 0) / 10.0,
            float(self.has_frame),
            float(self.has_grid_lines),
            self.num_connected_regions / 10.0,
            self.largest_region_ratio,
        ]
        # Add color histogram
        features.extend(self.color_histogram / max(1, self.color_histogram.sum()))

        return np.array(features, dtype=np.float32)


class GridEncoder:
    """Encodes grids into feature embeddings"""

    def encode(self, g: Grid) -> GridEmbedding:
        """Extract comprehensive features from a grid"""
        # Basic structure
        height = g.height
        width = g.width
        aspect_ratio = height / width if width > 0 else 1.0

        # Color analysis
        colors = g.get_colors()
        num_colors = len(colors)

        color_histogram = np.zeros(10, dtype=np.float32)
        for r in range(height):
            for c in range(width):
                color_histogram[g[r, c]] += 1

        dominant_color = int(np.argmax(color_histogram))
        background_ratio = color_histogram[0] / (height * width) if height * width > 0 else 0

        # Object analysis
        objects = g.find_objects()
        num_objects = len(objects)

        if objects:
            sizes = [o.size for o in objects]
            avg_object_size = np.mean(sizes)
            max_object_size = max(sizes)
            min_object_size = min(sizes)
            object_size_variance = np.var(sizes) if len(sizes) > 1 else 0
        else:
            avg_object_size = 0
            max_object_size = 0
            min_object_size = 0
            object_size_variance = 0

        # Spatial density
        total_pixels = height * width
        non_zero = np.sum(g.data != 0)
        density = non_zero / total_pixels if total_pixels > 0 else 0

        # Edge density
        edge_pixels = 0
        for r in range(height):
            if g[r, 0] != 0:
                edge_pixels += 1
            if width > 1 and g[r, width - 1] != 0:
                edge_pixels += 1
        for c in range(1, width - 1):
            if g[0, c] != 0:
                edge_pixels += 1
            if height > 1 and g[height - 1, c] != 0:
                edge_pixels += 1
        edge_total = 2 * height + 2 * width - 4 if height > 1 and width > 1 else max(height, width)
        edge_density = edge_pixels / edge_total if edge_total > 0 else 0

        # Center density
        center_r = height // 4
        center_c = width // 4
        center_h = height // 2
        center_w = width // 2
        if center_h > 0 and center_w > 0:
            center_pixels = np.sum(g.data[center_r:center_r + center_h, center_c:center_c + center_w] != 0)
            center_density = center_pixels / (center_h * center_w)
        else:
            center_density = 0

        # Symmetry analysis
        horizontal_symmetry = self._compute_symmetry(g, 'horizontal')
        vertical_symmetry = self._compute_symmetry(g, 'vertical')
        diagonal_symmetry = self._compute_symmetry(g, 'diagonal')
        rotational_symmetry = self._compute_symmetry(g, 'rotational')

        # Periodicity
        v_period, h_period = g.detect_periodicity()

        # Frame detection
        has_frame = self._detect_frame(g)

        # Grid lines detection
        has_grid_lines = self._detect_grid_lines(g)

        # Connectivity
        regions = self._count_connected_regions(g)
        largest_region_ratio = max(regions) / sum(regions) if regions else 0

        return GridEmbedding(
            height=height,
            width=width,
            aspect_ratio=aspect_ratio,
            num_colors=num_colors,
            color_histogram=color_histogram,
            dominant_color=dominant_color,
            background_ratio=background_ratio,
            num_objects=num_objects,
            avg_object_size=avg_object_size,
            max_object_size=max_object_size,
            min_object_size=min_object_size,
            object_size_variance=object_size_variance,
            density=density,
            edge_density=edge_density,
            center_density=center_density,
            horizontal_symmetry=horizontal_symmetry,
            vertical_symmetry=vertical_symmetry,
            diagonal_symmetry=diagonal_symmetry,
            rotational_symmetry=rotational_symmetry,
            periodicity_h=h_period,
            periodicity_v=v_period,
            has_frame=has_frame,
            has_grid_lines=has_grid_lines,
            num_connected_regions=len(regions),
            largest_region_ratio=largest_region_ratio,
        )

    def _compute_symmetry(self, g: Grid, sym_type: str) -> float:
        """Compute symmetry score (0-1)"""
        total = g.height * g.width
        if total == 0:
            return 0

        matches = 0

        if sym_type == 'horizontal':
            for r in range(g.height):
                for c in range(g.width // 2):
                    if g[r, c] == g[r, g.width - 1 - c]:
                        matches += 2

        elif sym_type == 'vertical':
            for r in range(g.height // 2):
                for c in range(g.width):
                    if g[r, c] == g[g.height - 1 - r, c]:
                        matches += 2

        elif sym_type == 'diagonal' and g.height == g.width:
            for r in range(g.height):
                for c in range(g.width):
                    if g[r, c] == g[c, r]:
                        matches += 1

        elif sym_type == 'rotational' and g.height == g.width:
            for r in range(g.height):
                for c in range(g.width):
                    if g[r, c] == g[g.height - 1 - r, g.width - 1 - c]:
                        matches += 1

        return matches / total

    def _detect_frame(self, g: Grid) -> bool:
        """Detect if grid has a frame border"""
        if g.height < 3 or g.width < 3:
            return False

        # Check if edges have consistent non-zero color
        edge_colors = set()

        for c in range(g.width):
            edge_colors.add(g[0, c])
            edge_colors.add(g[g.height - 1, c])
        for r in range(g.height):
            edge_colors.add(g[r, 0])
            edge_colors.add(g[r, g.width - 1])

        edge_colors.discard(0)
        return len(edge_colors) == 1

    def _detect_grid_lines(self, g: Grid) -> bool:
        """Detect if grid has internal dividing lines"""
        # Check for full-row or full-column lines
        for r in range(1, g.height - 1):
            row_colors = set(g[r, c] for c in range(g.width))
            if len(row_colors) == 1 and 0 not in row_colors:
                return True

        for c in range(1, g.width - 1):
            col_colors = set(g[r, c] for r in range(g.height))
            if len(col_colors) == 1 and 0 not in col_colors:
                return True

        return False

    def _count_connected_regions(self, g: Grid) -> List[int]:
        """Count pixels in each connected region"""
        visited = set()
        region_sizes = []

        for r in range(g.height):
            for c in range(g.width):
                if (r, c) in visited or g[r, c] == 0:
                    continue

                # Flood fill
                size = 0
                color = g[r, c]
                stack = [(r, c)]

                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in visited:
                        continue
                    if cr < 0 or cr >= g.height or cc < 0 or cc >= g.width:
                        continue
                    if g[cr, cc] != color:
                        continue

                    visited.add((cr, cc))
                    size += 1
                    stack.extend([(cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)])

                region_sizes.append(size)

        return region_sizes


class TransformationEmbedding:
    """Embedding for input->output transformation"""

    def __init__(self, input_emb: GridEmbedding, output_emb: GridEmbedding):
        self.input_emb = input_emb
        self.output_emb = output_emb

        # Compute transformation features
        self.size_change = (output_emb.height / max(1, input_emb.height),
                           output_emb.width / max(1, input_emb.width))
        self.color_change = output_emb.num_colors - input_emb.num_colors
        self.object_change = output_emb.num_objects - input_emb.num_objects
        self.density_change = output_emb.density - input_emb.density
        self.symmetry_change = (
            output_emb.horizontal_symmetry - input_emb.horizontal_symmetry,
            output_emb.vertical_symmetry - input_emb.vertical_symmetry
        )

    def to_vector(self) -> np.ndarray:
        """Convert to feature vector"""
        input_vec = self.input_emb.to_vector()
        output_vec = self.output_emb.to_vector()
        diff_vec = output_vec - input_vec

        transform_features = np.array([
            self.size_change[0],
            self.size_change[1],
            self.color_change / 10.0,
            self.object_change / 10.0,
            self.density_change,
            self.symmetry_change[0],
            self.symmetry_change[1],
        ], dtype=np.float32)

        return np.concatenate([input_vec, output_vec, diff_vec, transform_features])


class PatternMatcher:
    """Neural-inspired pattern matching using embeddings"""

    def __init__(self):
        self.encoder = GridEncoder()
        self.pattern_library: Dict[str, Tuple[TransformationEmbedding, Any]] = {}

    def register_pattern(self, task_id: str, train_pairs: List[Tuple[Grid, Grid]],
                        solution: Any):
        """Register a solved pattern for future matching"""
        if not train_pairs:
            return

        # Compute average transformation embedding
        embeddings = []
        for inp, out in train_pairs:
            inp_emb = self.encoder.encode(inp)
            out_emb = self.encoder.encode(out)
            embeddings.append(TransformationEmbedding(inp_emb, out_emb))

        # Store first embedding as representative
        self.pattern_library[task_id] = (embeddings[0], solution)

    def find_similar(self, train_pairs: List[Tuple[Grid, Grid]],
                    top_k: int = 5) -> List[Tuple[str, float, Any]]:
        """Find similar patterns from library"""
        if not train_pairs or not self.pattern_library:
            return []

        # Compute query embedding
        inp, out = train_pairs[0]
        inp_emb = self.encoder.encode(inp)
        out_emb = self.encoder.encode(out)
        query_emb = TransformationEmbedding(inp_emb, out_emb)
        query_vec = query_emb.to_vector()

        # Compute similarities
        similarities = []
        for task_id, (stored_emb, solution) in self.pattern_library.items():
            stored_vec = stored_emb.to_vector()
            similarity = self._cosine_similarity(query_vec, stored_vec)
            similarities.append((task_id, similarity, solution))

        # Sort by similarity
        similarities.sort(key=lambda x: -x[1])
        return similarities[:top_k]

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))


class PatternCluster:
    """Clusters similar grids/transformations for abstraction"""

    def __init__(self, num_clusters: int = 10):
        self.num_clusters = num_clusters
        self.encoder = GridEncoder()
        self.centroids: List[np.ndarray] = []
        self.cluster_patterns: Dict[int, List[Any]] = defaultdict(list)

    def fit(self, grids: List[Grid]):
        """Cluster grids by their embeddings (k-means style)"""
        if len(grids) < self.num_clusters:
            return

        embeddings = [self.encoder.encode(g).to_vector() for g in grids]
        embeddings = np.array(embeddings)

        # Simple k-means
        # Initialize centroids randomly
        indices = np.random.choice(len(embeddings), self.num_clusters, replace=False)
        self.centroids = [embeddings[i] for i in indices]

        # Iterate
        for _ in range(10):
            # Assign to clusters
            assignments = []
            for emb in embeddings:
                distances = [np.linalg.norm(emb - c) for c in self.centroids]
                assignments.append(np.argmin(distances))

            # Update centroids
            for k in range(self.num_clusters):
                cluster_points = [embeddings[i] for i, a in enumerate(assignments) if a == k]
                if cluster_points:
                    self.centroids[k] = np.mean(cluster_points, axis=0)

    def predict(self, g: Grid) -> int:
        """Predict cluster for a grid"""
        if not self.centroids:
            return 0

        emb = self.encoder.encode(g).to_vector()
        distances = [np.linalg.norm(emb - c) for c in self.centroids]
        return int(np.argmin(distances))


class TransformationPrioritizer:
    """Learn which transformations to try first based on input features"""

    def __init__(self):
        self.encoder = GridEncoder()
        self.feature_to_transform: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self.transform_success_rate: Dict[str, float] = defaultdict(float)
        self.transform_count: Dict[str, int] = defaultdict(int)

    def record_success(self, g: Grid, transform_name: str, success: bool):
        """Record whether a transformation succeeded for a grid"""
        emb = self.encoder.encode(g)

        # Extract key features
        key_features = self._extract_key_features(emb)

        for feature in key_features:
            self.feature_to_transform[feature].append((transform_name, 1.0 if success else 0.0))

        # Update global success rate
        self.transform_count[transform_name] += 1
        if success:
            self.transform_success_rate[transform_name] += 1

    def get_priority(self, g: Grid, transform_names: List[str]) -> List[str]:
        """Get prioritized order of transformations to try"""
        emb = self.encoder.encode(g)
        key_features = self._extract_key_features(emb)

        scores = defaultdict(float)

        # Score based on input features
        for feature in key_features:
            if feature in self.feature_to_transform:
                for transform, success in self.feature_to_transform[feature]:
                    if transform in transform_names:
                        scores[transform] += success

        # Add global success rate
        for transform in transform_names:
            if self.transform_count[transform] > 0:
                global_rate = self.transform_success_rate[transform] / self.transform_count[transform]
                scores[transform] += global_rate * 0.5

        # Sort by score
        sorted_transforms = sorted(transform_names, key=lambda t: -scores[t])
        return sorted_transforms

    def _extract_key_features(self, emb: GridEmbedding) -> List[str]:
        """Extract key features for indexing"""
        features = []

        # Size features
        if emb.height == emb.width:
            features.append("square")
        if emb.height == 1:
            features.append("single_row")
        if emb.width == 1:
            features.append("single_col")

        # Color features
        features.append(f"colors_{emb.num_colors}")
        features.append(f"dominant_{emb.dominant_color}")

        # Object features
        features.append(f"objects_{min(emb.num_objects, 10)}")

        # Symmetry features
        if emb.horizontal_symmetry > 0.9:
            features.append("h_symmetric")
        if emb.vertical_symmetry > 0.9:
            features.append("v_symmetric")

        # Pattern features
        if emb.periodicity_h:
            features.append(f"h_period_{emb.periodicity_h}")
        if emb.periodicity_v:
            features.append(f"v_period_{emb.periodicity_v}")
        if emb.has_frame:
            features.append("has_frame")
        if emb.has_grid_lines:
            features.append("has_grid")

        return features



def neural_symbolic_integration(neural_output: Dict[str, Any],
                               symbolic_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Integrate neural network predictions with symbolic reasoning.

    Combines the pattern recognition of neural networks with the
    explainability and consistency of symbolic systems.

    Args:
        neural_output: Raw neural network predictions
        symbolic_rules: List of symbolic constraints/rules

    Returns:
        Integrated predictions satisfying both neural and symbolic components
    """
    import numpy as np

    # Start with neural prediction
    prediction = neural_output.get('prediction', 0.0)
    confidence = neural_output.get('confidence', 0.5)

    # Apply symbolic constraints
    adjusted_prediction = prediction
    adjustments = []

    for rule in symbolic_rules:
        rule_type = rule.get('type')

        if rule_type == 'bounds':
            # Ensure prediction within bounds
            lower = rule.get('lower', -float('inf'))
            upper = rule.get('upper', float('inf'))

            if prediction < lower:
                adjusted_prediction = lower
                adjustments.append(f'lower_bound: {lower}')
            elif prediction > upper:
                adjusted_prediction = upper
                adjustments.append(f'upper_bound: {upper}')

        elif rule_type == 'monotonicity':
            # Ensure monotonic relationship with input
            input_val = neural_output.get('input_value', 0.0)
            comparison_val = rule.get('comparison_value', 0.0)

            if rule.get('direction') == 'increasing':
                if input_val < comparison_val and prediction > comparison_val:
                    adjusted_prediction = comparison_val * 0.95
                    adjustments.append('monotonic_constraint')

        elif rule_type == 'consistency':
            # Check consistency with related predictions
            related = neural_output.get('related_predictions', [])
            if related:
                avg_related = np.mean(related)
                if abs(prediction - avg_related) > rule.get('max_variance', 1.0):
                    adjusted_prediction = prediction * 0.9 + avg_related * 0.1
                    adjustments.append('consistency_adjustment')

    # Update confidence based on number of adjustments
    if adjustments:
        confidence *= 0.9  # Reduce confidence when adjustments needed

    return {
        'prediction': adjusted_prediction,
        'confidence': confidence,
        'adjustments': adjustments,
        'original_prediction': prediction
    }


def symbolic_explain(neural_features: Dict[str, float],
                   rule_base: List[Dict[str, Any]]) -> List[str]:
    """
    Generate symbolic explanations for neural network decisions.

    Args:
        neural_features: Feature importance/values from neural network
        rule_base: Symbolic rules for explanation

    Returns:
        List of explanatory statements
    """
    explanations = []

    for feature, value in neural_features.items():
        if abs(value) < 0.1:
            continue

        # Find relevant rules
        for rule in rule_base:
            if rule.get('feature') == feature:
                direction = "increases" if value > 0 else "decreases"
                strength = "strongly" if abs(value) > 0.5 else "moderately"

                explanations.append(
                    f"{feature} {direction} outcome ({strength})"
                )

    return explanations



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
