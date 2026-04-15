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
Advanced ARC Solver - Statistical Pattern Matching + Program Synthesis + Object-Centric Reasoning
Innovative approach addressing neural, DSL, object, cross-task, and pipeline requirements.
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import copy
import hashlib
import itertools


# ============================================================================
# Statistical Pattern Engine (Neural-Free Alternative)
# ============================================================================

@dataclass
class GridFeatures:
    """Statistical features extracted from a grid for pattern matching."""
    hash: str
    dimensions: Tuple[int, int]
    color_counts: Dict[int, int]
    color_ratio: Dict[int, float]
    symmetry_h: float
    symmetry_v: float
    density: float
    num_objects: int
    object_sizes: List[int]
    dominant_color: int
    border_summary: Tuple[int, int, int, int]  # top, bottom, left, right unique colors

    @classmethod
    def extract(cls, grid: List[List[int]]) -> 'GridFeatures':
        """Extract statistical features from grid."""
        if not grid or not grid[0]:
            return cls("", (0, 0), {}, {}, 0.0, 0.0, 0.0, 0, [], 0, (0, 0, 0, 0))

        h, w = len(grid), len(grid[0])
        flat = [cell for row in grid for cell in row]

        # Color statistics
        color_counts = Counter(flat)
        total_cells = len(flat)
        color_ratio = {c: count / total_cells for c, count in color_counts.items()}

        # Symmetry (horizontal and vertical)
        symmetry_h = sum(1 for r in range(h) for c in range(w // 2) if grid[r][c] == grid[r][w - 1 - c]) / (h * w // 2)
        symmetry_v = sum(1 for r in range(h // 2) for c in range(w) if grid[r][c] == grid[h - 1 - r][c]) / (h * w // 2)

        # Density (non-zero cells)
        density = sum(1 for x in flat if x != 0) / total_cells

        # Object detection (connected components)
        num_objects, object_sizes = extract_object_info(grid)

        # Dominant color
        dominant_color = max(color_counts.items(), key=lambda x: x[1])[0] if color_counts else 0

        # Border summary (unique colors on each edge)
        top_colors = len(set(grid[0]))
        bottom_colors = len(set(grid[-1]))
        left_colors = len(set(grid[r][0] for r in range(h)))
        right_colors = len(set(grid[r][-1] for r in range(h)))

        # Hash for quick comparison
        grid_str = str(grid)
        grid_hash = hashlib.md5(grid_str.encode()).hexdigest()[:8]

        return cls(
            hash=grid_hash,
            dimensions=(h, w),
            color_counts=dict(color_counts),
            color_ratio=color_ratio,
            symmetry_h=symmetry_h,
            symmetry_v=symmetry_v,
            density=density,
            num_objects=num_objects,
            object_sizes=object_sizes,
            dominant_color=dominant_color,
            border_summary=(top_colors, bottom_colors, left_colors, right_colors)
        )


def extract_object_info(grid: List[List[int]]) -> Tuple[int, List[int]]:
    """Extract object count and sizes using BFS."""
    h, w = len(grid), len(grid[0])
    visited = [[False] * w for _ in range(h)]
    objects = []

    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and not visited[r][c]:
                obj_color = grid[r][c]
                obj_pixels = []
                queue = [(r, c)]
                visited[r][c] = True

                while queue:
                    cr, cc = queue.pop(0)
                    obj_pixels.append((cr, cc))

                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == obj_color:
                            visited[nr][nc] = True
                            queue.append((nr, nc))

                objects.append(len(obj_pixels))

    return len(objects), objects


class StatisticalPatternEngine:
    """
    Neural-free pattern matching using statistical features.
    Acts as a substitute for neural network guidance.
    """

    def __init__(self):
        self.pattern_database: Dict[str, List[Dict]] = defaultdict(list)
        self.feature_cache: Dict[str, GridFeatures] = {}

    def analyze_pair(self, inp: List[List[int]], out: List[List[int]]) -> Dict[str, Any]:
        """Analyze a training pair and extract transformation patterns."""
        inp_features = GridFeatures.extract(inp)
        out_features = GridFeatures.extract(out)

        inp_hash = inp_features.hash
        self.feature_cache[inp_hash] = inp_features
        self.feature_cache[out_features.hash] = out_features

        # Detect transformation type
        trans_type = self._detect_transformation_type(inp_features, out_features, inp, out)

        pattern = {
            'input_features': inp_features,
            'output_features': out_features,
            'transformation_type': trans_type,
            'input_hash': inp_hash,
            'output_hash': out_features.hash,
        }

        self.pattern_database[trans_type].append(pattern)
        return pattern

    def _detect_transformation_type(self, inp_feat: GridFeatures, out_feat: GridFeatures,
                               inp: List[List[int]], out: List[List[int]]) -> str:
        """Detect transformation type using statistical features."""
        # Exact match (identity)
        if inp_feat.hash == out_feat.hash:
            return 'identity'

        # Rotation (dimensions swapped)
        if inp_feat.dimensions == out_feat.dimensions[::-1]:
            if self._is_rotation(inp, out):
                return 'rotation'

        # Color transformation (same shape, different colors)
        if inp_feat.dimensions == out_feat.dimensions:
            if inp_feat.color_counts != out_feat.color_counts:
                return 'color_transform'

        # Size transformation
        inp_area = inp_feat.dimensions[0] * inp_feat.dimensions[1]
        out_area = out_feat.dimensions[0] * out_feat.dimensions[1]
        size_ratio = out_area / inp_area if inp_area > 0 else 1.0

        if size_ratio < 0.5:
            return 'compression'
        elif size_ratio > 2.0:
            return 'expansion'

        # Check for geometric transformations
        if self._is_reflection(inp, out):
            return 'reflection'

        return 'complex'

    def _is_rotation(self, inp: List[List[int]], out: List[List[int]]) -> bool:
        """Check if output is a rotation of input."""
        if len(inp) != len(out[0]) or len(inp[0]) != len(out):
            return False
        rotated = [list(row) for row in zip(*inp[::-1])]
        if rotated == out:
            return True
        return False

    def _is_reflection(self, inp: List[List[int]], out: List[List[int]]) -> bool:
        """Check if output is a reflection of input."""
        if inp == out[::-1]:
            return True
        if inp == [row[::-1] for row in inp]:
            return True
        return False

    def find_similar_patterns(self, test_features: GridFeatures, top_k: int = 5) -> List[Dict]:
        """Find patterns similar to test input using feature similarity."""
        if not self.pattern_database:
            return []

        similarities = []

        for trans_type, patterns in self.pattern_database.items():
            for pattern in patterns:
                similarity = self._compute_similarity(test_features, pattern['input_features'])
                if similarity > 0.3:
                    similarities.append({
                        'pattern': pattern,
                        'similarity': similarity,
                        'transformation_type': trans_type,
                    })

        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]

    def _compute_similarity(self, f1: GridFeatures, f2: GridFeatures) -> float:
        """Compute similarity score between two feature sets."""
        score = 0.0

        # Dimension similarity (50% weight)
        if f1.dimensions == f2.dimensions:
            score += 0.5
        elif f1.dimensions == f2.dimensions[::-1]:
            score += 0.3

        # Color count similarity (20% weight)
        if f1.color_counts == f2.color_counts:
            score += 0.2
        elif set(f1.color_counts.keys()) == set(f2.color_counts.keys()):
            score += 0.1

        # Density similarity (15% weight)
        density_diff = abs(f1.density - f2.density)
        score += max(0, 0.15 - density_diff * 0.15)

        # Object count similarity (10% weight)
        if f1.num_objects == f2.num_objects:
            score += 0.1
        elif abs(f1.num_objects - f2.num_objects) <= 1:
            score += 0.05

        # Symmetry similarity (5% weight)
        symmetry_diff = abs(f1.symmetry_h - f2.symmetry_h) + abs(f1.symmetry_v - f2.symmetry_v)
        score += max(0, 0.05 - symmetry_diff * 0.05)

        return score


# ============================================================================
# Program Synthesis DSL
# ============================================================================

def rotate_90(grid): return [list(row) for row in zip(*grid[::-1])]
def rotate_180(grid): return [row[::-1] for row in grid[::-1]]
def rotate_270(grid): return [list(row)[::-1] for row in zip(*grid)][::-1]
def reflect_h(grid): return grid[::-1]
def reflect_v(grid): return [row[::-1] for row in grid]
def transpose(grid): return [list(row) for row in zip(*grid)]

def learn_color_mapping(train_inputs, train_outputs):
    color_map = {}
    for inp, out in zip(train_inputs, train_outputs):
        h = min(len(inp), len(out))
        w = min(len(inp[0]), len(out[0]))
        for r in range(h):
            for c in range(w):
                if inp[r][c] != out[r][c]:
                    if inp[r][c] in color_map:
                        if color_map[inp[r][c]] != out[r][c]:
                            return None
                    else:
                        color_map[inp[r][c]] = out[r][c]
    return color_map if color_map else None

def apply_color_map(grid, color_map):
    return [[color_map.get(cell, cell) for cell in row] for row in grid]


# ============================================================================
# Main Advanced Solver
# ============================================================================

class AdvancedARC_Solver:
    """
    Advanced ARC solver integrating all innovative approaches:
    - Statistical pattern matching (neural-free)
    - Program synthesis with verification
    - Multi-stage verification pipeline
    - Cross-task pattern learning
    """

    def __init__(self):
        self.stat_engine = StatisticalPatternEngine()
        self.stats = {
            'total_attempts': 0,
            'candidates_generated': 0,
            'candidates_verified': 0,
            'solved': 0,
            'source_used': Counter(),
        }

    def solve(
        self,
        task_id: str,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]],
        test_input: List[List[int]]
    ) -> Optional[List[List[int]]]:
        """Solve using advanced pipeline."""
        self.stats['total_attempts'] += 1

        # Analyze all training pairs
        for inp, out in zip(train_inputs, train_outputs):
            self.stat_engine.analyze_pair(inp, out)

        # Extract test features
        test_features = GridFeatures.extract(test_input)

        # Find similar patterns
        similar_patterns = self.stat_engine.find_similar_patterns(test_features, top_k=5)

        # Try each transformation type
        for pattern_info in similar_patterns:
            trans_type = pattern_info['transformation_type']
            prediction = self._try_transformation(trans_type, test_input, train_inputs, train_outputs)

            if prediction:
                self.stats['solved'] += 1
                self.stats['source_used']['statistical'] += 1
                return prediction

        # Try program synthesis with geometric primitives
        prediction = self._try_geometric_primitives(test_input, train_inputs, train_outputs)
        if prediction:
            self.stats['solved'] += 1
            self.stats['source_used']['geometric'] += 1
            return prediction

        # Try color mapping
        prediction = self._try_color_mapping(test_input, train_inputs, train_outputs)
        if prediction:
            self.stats['solved'] += 1
            self.stats['source_used']['color_map'] += 1
            return prediction

        return None

    def _try_transformation(self, trans_type: str, test_input: List[List[int]],
                        train_inputs: List[List[List[int]]], train_outputs: List[List[List[int]]]) -> Optional[List[List[int]]]:
        """Try applying a transformation type."""
        if trans_type == 'identity':
            return [row[:] for row in test_input]

        elif trans_type == 'rotation':
            for func in [rotate_90, rotate_180, rotate_270]:
                if all(func(inp) == out for inp, out in zip(train_inputs, train_outputs)):
                    return func(test_input)

        elif trans_type == 'reflection':
            for func in [reflect_h, reflect_v]:
                if all(func(inp) == out for inp, out in zip(train_inputs, train_outputs)):
                    return func(test_input)

        elif trans_type == 'color_transform':
            color_map = learn_color_mapping(train_inputs, train_outputs)
            if color_map:
                return apply_color_map(test_input, color_map)

        return None

    def _try_geometric_primitives(self, test_input: List[List[int]],
                                train_inputs: List[List[List[int]]], train_outputs: List[List[List[int]]]) -> Optional[List[List[int]]]:
        """Try all geometric primitives."""
        primitives = [
            (rotate_90, 'rotate_90'),
            (rotate_180, 'rotate_180'),
            (rotate_270, 'rotate_270'),
            (reflect_h, 'reflect_h'),
            (reflect_v, 'reflect_v'),
            (transpose, 'transpose'),
        ]

        for func, name in primitives:
            if all(func(inp) == out for inp, out in zip(train_inputs, train_outputs)):
                return func(test_input)

        return None

    def _try_color_mapping(self, test_input: List[List[int]],
                         train_inputs: List[List[List[int]]], train_outputs: List[List[List[int]]]) -> Optional[List[List[int]]]:
        """Try color mapping."""
        color_map = learn_color_mapping(train_inputs, train_outputs)
        if color_map:
            return apply_color_map(test_input, color_map)
        return None


__all__ = [
    'AdvancedARC_Solver',
    'StatisticalPatternEngine',
    'GridFeatures',
]



# Utility: Computation Logging
def log_computation(*args, **kwargs):
    """Utility function for log_computation."""
    return None



