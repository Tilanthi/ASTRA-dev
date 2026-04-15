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
Enhanced Transformation Detection for ARC-AGI-2
Based on analysis of evaluation task patterns
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Any, Callable
from dataclasses import dataclass
from collections import defaultdict, Counter
import copy


# ============================================================================
# Transformation Types
# ============================================================================

@dataclass
class TransformationHypothesis:
    """A hypothesis about what transformation applies."""
    name: str
    confidence: float
    apply_func: Callable
    params: Dict[str, Any]

    def __repr__(self):
        return f"{self.name} (conf={self.confidence:.2f})"


# ============================================================================
# Grid Analysis Utilities
# ============================================================================

class GridAnalyzer:
    """Deep analysis of grid structure and patterns."""

    def __init__(self):
        pass

    def analyze(self, grid: List[List[int]]) -> Dict[str, Any]:
        """Comprehensive grid analysis."""
        if not grid or not grid[0]:
            return {}

        h, w = len(grid), len(grid[0])

        # Basic properties
        colors = set()
        color_counts = Counter()
        for row in grid:
            for val in row:
                colors.add(val)
                color_counts[val] += 1

        # Spatial distribution
        color_positions = defaultdict(list)
        for r in range(h):
            for c in range(w):
                color_positions[grid[r][c]].append((r, c))

        # Detect patterns
        has_border = self._detect_border(grid)
        has_frame = self._detect_frame(grid)
        rows_unique = self._count_unique_rows(grid)
        cols_unique = self._count_unique_cols(grid)
        is_symmetric_h = self._check_symmetry_h(grid)
        is_symmetric_v = self._check_symmetry_v(grid)

        return {
            'height': h,
            'width': w,
            'size': h * w,
            'colors': sorted(colors),
            'num_colors': len(colors),
            'color_counts': dict(color_counts),
            'color_positions': {k: v for k, v in color_positions.items()},
            'has_border': has_border,
            'has_frame': has_frame,
            'unique_rows': rows_unique,
            'unique_cols': cols_unique,
            'symmetric_h': is_symmetric_h,
            'symmetric_v': is_symmetric_v,
        }

    def _detect_border(self, grid: List[List[int]]) -> Optional[Tuple[int, int, int, int]]:
        """Detect if grid has a colored border."""
        h, w = len(grid), len(grid[0])
        if h < 3 or w < 3:
            return None

        top_colors = set(grid[0])
        bottom_colors = set(grid[-1])
        left_colors = set(grid[r][0] for r in range(h))
        right_colors = set(grid[r][-1] for r in range(h))

        # Check if all edges have same color
        edge_colors = top_colors | bottom_colors | left_colors | right_colors
        if len(edge_colors) == 1:
            color = edge_colors.pop()
            return (color, color, color, color)  # top, bottom, left, right

        return None

    def _detect_frame(self, grid: List[List[int]]) -> bool:
        """Detect if grid has any kind of frame/border structure."""
        h, w = len(grid), len(grid[0])
        if h < 3 or w < 3:
            return False

        # Check outer border has uniform colors (could be different per side)
        top_uni = len(set(grid[0])) == 1
        bottom_uni = len(set(grid[-1])) == 1
        left_uni = len(set(grid[r][0] for r in range(h))) == 1
        right_uni = len(set(grid[r][-1] for r in range(h))) == 1

        return top_uni or bottom_uni or left_uni or right_uni

    def _count_unique_rows(self, grid: List[List[int]]) -> int:
        """Count unique rows."""
        return len(set(tuple(row) for row in grid))

    def _count_unique_cols(self, grid: List[List[int]]) -> int:
        """Count unique columns."""
        if not grid:
            return 0
        cols = [tuple(grid[r][c] for r in range(len(grid)))
                for c in range(len(grid[0]))]
        return len(set(cols))

    def _check_symmetry_h(self, grid: List[List[int]]) -> bool:
        """Check horizontal symmetry."""
        h = len(grid)
        for i in range(h // 2):
            if grid[i] != grid[h - 1 - i]:
                return False
        return True

    def _check_symmetry_v(self, grid: List[List[int]]) -> bool:
        """Check vertical symmetry."""
        h, w = len(grid), len(grid[0])
        for r in range(h):
            for c in range(w // 2):
                if grid[r][c] != grid[r][w - 1 - c]:
                    return False
        return True

    def find_objects(self, grid: List[List[int]]) -> List[Dict]:
        """Find connected components (objects) in grid."""
        h, w = len(grid), len(grid[0])
        visited = [[False] * w for _ in range(h)]
        objects = []

        for r in range(h):
            for c in range(w):
                if grid[r][c] != 0 and not visited[r][c]:
                    # BFS to find object
                    color = grid[r][c]
                    obj_pixels = []
                    queue = [(r, c)]
                    visited[r][c] = True

                    min_r = max_r = r
                    min_c = max_c = c

                    while queue:
                        cr, cc = queue.pop(0)
                        obj_pixels.append((cr, cc))

                        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < h and 0 <= nc < w and
                                not visited[nr][nc] and grid[nr][nc] == color):
                                visited[nr][nc] = True
                                queue.append((nr, nc))
                                min_r = min(min_r, nr)
                                max_r = max(max_r, nr)
                                min_c = min(min_c, nc)
                                max_c = max(max_c, nc)

                    objects.append({
                        'color': color,
                        'pixels': obj_pixels,
                        'area': len(obj_pixels),
                        'bbox': (min_r, min_c, max_r, max_c),
                        'center': ((min_r + max_r) / 2, (min_c + max_c) / 2)
                    })

        return objects


# ============================================================================
# Transformation Detector
# ============================================================================

class TransformationDetector:
    """
    Detect transformations from input-output pairs.
    Based on analysis of ARC-AGI-2 patterns.
    """

    def __init__(self):
        self.analyzer = GridAnalyzer()

    def detect_transformation(
        self,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]]
    ) -> List[TransformationHypothesis]:
        """Detect transformation from training pairs."""
        if not train_inputs or not train_outputs:
            return []

        hypotheses = []

        # Analyze all training pairs
        for inp, out in zip(train_inputs, train_outputs):
            inp_analysis = self.analyzer.analyze(inp)
            out_analysis = self.analyzer.analyze(out)

            # Detect by size change
            size_ratio = (out_analysis['size'] / inp_analysis['size']
                         if inp_analysis['size'] > 0 else 1.0)

            # Detect by pattern
            pair_hypotheses = []

            # Compression detection
            if size_ratio < 0.5:
                pair_hypotheses.extend(self._detect_compression(inp, out, inp_analysis, out_analysis))

            # Color transformation
            elif inp_analysis['colors'] != out_analysis['colors']:
                pair_hypotheses.extend(self._detect_color_transform(inp, out, inp_analysis, out_analysis))

            # Geometric/structural
            else:
                pair_hypotheses.extend(self._detect_geometric(inp, out, inp_analysis, out_analysis))

            hypotheses.extend(pair_hypotheses)

        # Rank and deduplicate hypotheses
        return self._rank_hypotheses(hypotheses)

    def _detect_compression(
        self,
        inp: List[List[int]],
        out: List[List[int]],
        inp_a: Dict,
        out_a: Dict
    ) -> List[TransformationHypothesis]:
        """Detect compression-type transformations."""
        hypotheses = []

        # Check for row extraction (common in compression)
        if self._is_row_extraction(inp, out, inp_a, out_a):
            hypotheses.append(TransformationHypothesis(
                name="row_extraction",
                confidence=0.8,
                apply_func=self._apply_row_extraction,
                params={'input': inp, 'output': out}
            ))

        # Check for column extraction
        if self._is_col_extraction(inp, out, inp_a, out_a):
            hypotheses.append(TransformationHypothesis(
                name="col_extraction",
                confidence=0.8,
                apply_func=self._apply_col_extraction,
                params={'input': inp, 'output': out}
            ))

        # Check for subsampling
        if self._is_subsampling(inp, out, inp_a, out_a):
            row_step = len(inp) // len(out) if out else 1
            col_step = len(inp[0]) // len(out[0]) if out and out[0] else 1
            hypotheses.append(TransformationHypothesis(
                name="subsampling",
                confidence=0.9,
                apply_func=self._apply_subsampling,
                params={'row_step': row_step, 'col_step': col_step}
            ))

        # Check for color summarization
        if self._is_color_summarization(inp, out, inp_a, out_a):
            hypotheses.append(TransformationHypothesis(
                name="color_summarization",
                confidence=0.7,
                apply_func=self._apply_color_summarization,
                params={'input': inp, 'output': out}
            ))

        return hypotheses

    def _is_row_extraction(self, inp, out, inp_a, out_a) -> bool:
        """Check if output is extracted rows from input."""
        # Output rows should be subset or transformed version of input rows
        if len(out) >= len(inp):
            return False

        # Check if output rows match some input rows
        inp_rows = [tuple(row) for row in inp]
        out_rows = [tuple(row) for row in out]

        matches = sum(1 for orow in out_rows if orow in inp_rows)
        return matches >= len(out) * 0.5

    def _is_col_extraction(self, inp, out, inp_a, out_a) -> bool:
        """Check if output is extracted columns from input."""
        if len(out[0]) >= len(inp[0]) if out else False:
            return False

        # Similar to row extraction but for columns
        return False  # Simplified

    def _is_subsampling(self, inp, out, inp_a, out_a) -> bool:
        """Check if output is regular subsampling of input."""
        if not inp or not out:
            return False

        inp_h, inp_w = len(inp), len(inp[0])
        out_h, out_w = len(out), len(out[0])

        # Check if dimensions divide evenly
        if inp_h % out_h != 0 or inp_w % out_w != 0:
            return False

        # Check if subsampling matches
        row_step = inp_h // out_h
        col_step = inp_w // out_w

        for i in range(out_h):
            for j in range(out_w):
                if inp[i * row_step][j * col_step] != out[i][j]:
                    return False

        return True

    def _is_color_summarization(self, inp, out, inp_a, out_a) -> bool:
        """Check if output summarizes colors by region."""
        # Output should have fewer colors or different arrangement
        return inp_a['num_colors'] > out_a['num_colors']

    def _apply_row_extraction(self, grid: List[List[int]], **kwargs) -> Optional[List[List[int]]]:
        """Apply row extraction (placeholder - needs learned indices)."""
        return None

    def _apply_col_extraction(self, grid: List[List[int]], **kwargs) -> Optional[List[List[int]]]:
        """Apply column extraction (placeholder)."""
        return None

    def _apply_subsampling(self, grid: List[List[int]], row_step: int, col_step: int, **kwargs) -> Optional[List[List[int]]]:
        """Apply subsampling."""
        if not grid:
            return None

        result = []
        for i in range(0, len(grid), row_step):
            row = []
            for j in range(0, len(grid[0]), col_step):
                row.append(grid[i][j])
            result.append(row)

        return result if result else None

    def _apply_color_summarization(self, grid: List[List[int]], **kwargs) -> Optional[List[List[int]]]:
        """Apply color summarization (placeholder)."""
        return None

    def _detect_color_transform(
        self,
        inp: List[List[int]],
        out: List[List[int]],
        inp_a: Dict,
        out_a: Dict
    ) -> List[TransformationHypothesis]:
        """Detect color transformation patterns."""
        hypotheses = []

        # Build color map
        color_map = self._infer_color_map(inp, out, inp_a, out_a)

        if color_map:
            hypotheses.append(TransformationHypothesis(
                name="color_mapping",
                confidence=0.9,
                apply_func=lambda grid, **kw: self._apply_color_map(grid, color_map),
                params={'color_map': color_map}
            ))

        return hypotheses

    def _infer_color_map(self, inp, out, inp_a, out_a) -> Optional[Dict[int, int]]:
        """Infer color mapping from input to output."""
        # Simple approach: track position-based color changes
        color_map = {}

        # Find cells where color changed
        for r in range(min(len(inp), len(out))):
            for c in range(min(len(inp[0]), len(out[0]))):
                if inp[r][c] != out[r][c]:
                    inp_color = inp[r][c]
                    out_color = out[r][c]

                    # Check consistency
                    if inp_color in color_map:
                        if color_map[inp_color] != out_color:
                            # Inconsistent mapping
                            return None
                    else:
                        color_map[inp_color] = out_color

        return color_map if color_map else None

    def _apply_color_map(self, grid: List[List[int]], color_map: Dict[int, int], **kwargs) -> Optional[List[List[int]]]:
        """Apply color mapping to grid."""
        result = []
        for row in grid:
            new_row = [color_map.get(val, val) for val in row]
            result.append(new_row)
        return result

    def _detect_geometric(
        self,
        inp: List[List[int]],
        out: List[List[int]],
        inp_a: Dict,
        out_a: Dict
    ) -> List[TransformationHypothesis]:
        """Detect geometric/structural transformations."""
        hypotheses = []

        # Check for simple operations
        # Rotation
        for angle in [90, 180, 270]:
            if self._is_rotation(inp, out, angle):
                hypotheses.append(TransformationHypothesis(
                    name=f"rotation_{angle}",
                    confidence=0.95,
                    apply_func=lambda grid, **kw: self._apply_rotation(grid, angle),
                    params={'angle': angle}
                ))
                break

        # Reflection
        if self._is_reflection_h(inp, out):
            hypotheses.append(TransformationHypothesis(
                name="reflection_horizontal",
                confidence=0.9,
                apply_func=self._apply_reflection_h,
                params={}
            ))

        if self._is_reflection_v(inp, out):
            hypotheses.append(TransformationHypothesis(
                name="reflection_vertical",
                confidence=0.9,
                apply_func=self._apply_reflection_v,
                params={}
            ))

        # Object operations (fill, extend, etc.)
        obj_hyps = self._detect_object_operations(inp, out, inp_a, out_a)
        hypotheses.extend(obj_hyps)

        return hypotheses

    def _is_rotation(self, inp, out, angle: int) -> bool:
        """Check if output is rotation of input."""
        if not inp or not out:
            return False

        rotated = self._apply_rotation(inp, angle)
        return rotated == out

    def _apply_rotation(self, grid: List[List[int]], angle: int) -> Optional[List[List[int]]]:
        """Apply rotation to grid."""
        if not grid:
            return None

        if angle == 90:
            # Rotate 90 degrees clockwise
            return [list(row) for row in zip(*grid[::-1])]
        elif angle == 180:
            # Rotate 180
            return [row[::-1] for row in grid[::-1]]
        elif angle == 270:
            # Rotate 270 (or 90 counter-clockwise)
            return [list(row) for row in zip(*grid)][::-1]
        return None

    def _is_reflection_h(self, inp, out) -> bool:
        """Check if output is horizontal reflection."""
        return inp[::-1] == out

    def _apply_reflection_h(self, grid: List[List[int]], **kwargs) -> Optional[List[List[int]]]:
        """Apply horizontal reflection."""
        return grid[::-1] if grid else None

    def _is_reflection_v(self, inp, out) -> bool:
        """Check if output is vertical reflection."""
        if not inp or not out:
            return False
        return [row[::-1] for row in inp] == out

    def _apply_reflection_v(self, grid: List[List[int]], **kwargs) -> Optional[List[List[int]]]:
        """Apply vertical reflection."""
        return [row[::-1] for row in grid] if grid else None

    def _detect_object_operations(
        self,
        inp: List[List[int]],
        out: List[List[int]],
        inp_a: Dict,
        out_a: Dict
    ) -> List[TransformationHypothesis]:
        """Detect object-level operations."""
        hypotheses = []

        inp_objects = self.analyzer.find_objects(inp)
        out_objects = self.analyzer.find_objects(out)

        # Check for fill/extend operations
        # (This is complex - simplified version)

        return hypotheses

    def _rank_hypotheses(self, hypotheses: List[TransformationHypothesis]) -> List[TransformationHypothesis]:
        """Rank and deduplicate hypotheses."""
        if not hypotheses:
            return []

        # Group by name and keep highest confidence
        by_name = {}
        for hyp in hypotheses:
            if hyp.name not in by_name or hyp.confidence > by_name[hyp.name].confidence:
                by_name[hyp.name] = hyp

        # Sort by confidence
        return sorted(by_name.values(), key=lambda h: -h.confidence)


# ============================================================================
# Main Solver Interface
# ============================================================================

class EnhancedTransformationSolver:
    """
    Enhanced solver using transformation detection.
    """

    def __init__(self):
        self.detector = TransformationDetector()
        self.analyzer = GridAnalyzer()

    def solve(
        self,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]],
        test_input: List[List[int]]
    ) -> Optional[List[List[int]]]:
        """Solve using transformation detection."""
        # Detect transformations from training pairs
        hypotheses = self.detector.detect_transformation(train_inputs, train_outputs)
