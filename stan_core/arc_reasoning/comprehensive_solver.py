#!/usr/bin/env python3
"""
Comprehensive Ensemble Solver
Combines all solvers with intelligent selection based on task characteristics.
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from collections import Counter
import copy


# ============================================================================
# Task Categorization
# ============================================================================

@dataclass
class TaskCharacteristics:
    """Characteristics of an ARC task."""
    size_change: str  # "same", "compress", "expand"
    has_colors: bool
    has_multiple_colors: bool
    has_objects: bool
    has_regular_patterns: bool
    compress_ratio: float
    complexity: str  # "simple", "medium", "complex"


def categorize_task(train_inputs: List[List[List[int]]],
                  train_outputs: List[List[List[int]]]) -> TaskCharacteristics:
    """Categorize task to guide solver selection."""
    if not train_inputs or not train_outputs:
        return TaskCharacteristics("unknown", False, False, False, False, 1.0, "simple")

    inp_h, inp_w = len(train_inputs[0]), len(train_inputs[0][0])
    out_h, out_w = len(train_outputs[0]), len(train_outputs[0][0])

    # Size change
    if inp_h == out_h and inp_w == out_w:
        size_change = "same"
    else:
        size_change = "compress" if (inp_h * inp_w) > (out_h * out_w) else "expand"

    # Color analysis
    all_colors = set()
    for inp in train_inputs:
        for row in inp:
            all_colors.update(row)
    for out in train_outputs:
        for row in out:
            all_colors.update(row)

    has_colors = len(all_colors) > 1
    has_multiple_colors = len(all_colors) > 3

    # Object detection
    has_objects = any(c != 0 for inp in train_inputs for row in inp for c in row)

    # Regular patterns check (repeating structures)
    has_regular_patterns = _check_regular_patterns(train_inputs, train_outputs)

    # Complexity
    compress_ratio = (out_h * out_w) / (inp_h * inp_w) if inp_h * inp_w > 0 else 1.0
    complexity = "simple"
    if has_multiple_colors and size_change != "same":
        complexity = "complex"
    elif has_objects and size_change != "same":
        complexity = "medium"

    return TaskCharacteristics(
        size_change=size_change,
        has_colors=has_colors,
        has_multiple_colors=has_multiple_colors,
        has_objects=has_objects,
        has_regular_patterns=has_regular_patterns,
        compress_ratio=compress_ratio,
        complexity=complexity,
    )


def _check_regular_patterns(inputs, outputs) -> bool:
    """Check for regular repeating patterns."""
    if not inputs or not inputs[0]:
        return False

    grid = inputs[0]
    h, w = len(grid), len(grid[0])

    # Check for horizontal stripes
    stripe_count = 0
    for r in range(h - 1):
        if grid[r] == grid[r + 1]:
            stripe_count += 1
    if stripe_count > h / 3:
        return True

    # Check for vertical stripes
    stripe_count = 0
    for c in range(w - 1):
        col_same = all(grid[r][c] == grid[r][c + 1] for r in range(h))
        if col_same:
            stripe_count += 1
    if stripe_count > w / 3:
        return True

    return False


# ============================================================================
# Transformation Primitives (Comprehensive Set)
# ============================================================================

class TransformationPrimitives:
    """Collection of transformation primitives."""

    @staticmethod
    def identity(grid):
        return [row[:] for row in grid]

    @staticmethod
    def rotate_90(grid):
        return [list(row) for row in zip(*grid[::-1])]

    @staticmethod
    def rotate_180(grid):
        return [row[::-1] for row in grid[::-1]]

    @staticmethod
    def rotate_270(grid):
        return [list(row)[::-1] for row in zip(*grid)][::-1]

    @staticmethod
    def reflect_h(grid):
        return grid[::-1]

    @staticmethod
    def reflect_v(grid):
        return [row[::-1] for row in grid]

    @staticmethod
    def transpose(grid):
        return [list(row) for row in zip(*grid)]

    @staticmethod
    def color_invert(grid):
        return [[10 - c if c != 0 else 0 for c in row] for row in grid]

    @staticmethod
    def compress_to_content(grid):
        """Crop grid to content bounds."""
        if not grid or not grid[0]:
            return grid

        min_r, max_r = len(grid), -1
        min_c, max_c = len(grid[0]), -1

        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                if cell != 0:
                    min_r = min(min_r, r)
                    max_r = max(max_r, r)
                    min_c = min(min_c, c)
                    max_c = max(max_c, c)

        if max_r < 0:
            return grid

        return [row[min_c:max_c+1] for row in grid[min_r:max_r+1]]

    @staticmethod
    def apply_color_map(grid, color_map):
        return [[color_map.get(c, c) for c in row] for row in grid]

    @staticmethod
    def extract_colored_objects(grid):
        """Extract and compact colored objects."""
        if not grid or not grid[0]:
            return grid

        h, w = len(grid), len(grid[0])
        result = [[0] * w for _ in range(h)]

        # Extract each color's objects
        for color in range(1, 10):
            for r in range(h):
                for c in range(w):
                    if grid[r][c] == color:
                        result[r][c] = color

        return TransformationPrimitives.compress_to_content(result)


# ============================================================================
# Comprehensive Solver
# ============================================================================

class ComprehensiveEnsembleSolver:
    """
    Comprehensive ensemble solver that uses multiple approaches.
    """

    def __init__(self):
        self.stats = {
            'total_attempts': 0,
            'tasks_by_type': Counter(),
            'solutions_by_method': Counter(),
            'total_solved': 0,
        }
        self.primitives = TransformationPrimitives()

    def solve(self, task_id: str, train_inputs: List[List[List[int]]],
              train_outputs: List[List[List[int]]],
              test_input: List[List[int]]) -> Optional[List[List[int]]]:
        """Solve using comprehensive approach."""
        self.stats['total_attempts'] += 1

        # Categorize task
        char = categorize_task(train_inputs, train_outputs)
        self.stats['tasks_by_type'][char.complexity] += 1

        # Generate candidates from all methods
        candidates = []

        # Method 1: Direct geometric transformations (for same-size tasks)
        if char.size_change == "same":
            candidates.extend(self._geometric_candidates(train_inputs, train_outputs))

        # Method 2: Color mapping (for any task with color changes)
        color_map = self._learn_color_map(train_inputs, train_outputs)
        if color_map:
            candidates.append(('color_map', self.primitives.apply_color_map(test_input, color_map)))

        # Method 3: Compression/Extraction (for compress tasks)
        if char.size_change == "compress":
            candidates.append(('compress', self.primitives.compress_to_content(test_input)))
            candidates.append(('extract_objects', self.primitives.extract_colored_objects(test_input)))

        # Method 4: Compose transformations
        if color_map and char.size_change == "same":
            for geom_name, geom_func in [
                ('rotate_90', self.primitives.rotate_90),
                ('rotate_180', self.primitives.rotate_180),
                ('rotate_270', self.primitives.rotate_270),
                ('reflect_h', self.primitives.reflect_h),
                ('reflect_v', self.primitives.reflect_v),
            ]:
                composed = lambda g, gm=color_map, gf=geom_func: self.primitives.apply_color_map(gf(g), gm)
                candidates.append((f'{geom_name}_color', composed(test_input)))

        # Score candidates and return best
        best_candidate = None
        best_score = 0

        for method_name, candidate in candidates:
            if not candidate:
                continue

            score = self._score_candidate(candidate, train_inputs, train_outputs)
            if score > best_score:
                best_score = score
                best_candidate = candidate

        if best_candidate:
            self.stats['solutions_by_method'][method_name] += 1
            self.stats['total_solved'] += 1
            return best_candidate

        return None

    def _geometric_candidates(self, train_inputs, train_outputs):
        """Generate geometric transformation candidates."""
        candidates = []

        transformations = [
            ('identity', self.primitives.identity),
            ('rotate_90', self.primitives.rotate_90),
            ('rotate_180', self.primitives.rotate_180),
            ('rotate_270', self.primitives.rotate_270),
            ('reflect_h', self.primitives.reflect_h),
            ('reflect_v', self.primitives.reflect_v),
            ('transpose', self.primitives.transpose),
        ]

        for name, func in transformations:
            # Check if this transformation works on all training pairs
            works = all(
                self._grids_equal(func(inp), out)
                for inp, out in zip(train_inputs, train_outputs)
            )

            if works:
                candidates.append((name, func))

        return candidates

    def _learn_color_map(self, train_inputs, train_outputs):
        """Learn color mapping from training pairs."""
        color_map = {}

        for inp, out in zip(train_inputs, train_outputs):
            h = min(len(inp), len(out))
            w = min(len(inp[0]), len(out[0]))

            for r in range(h):
                for c in range(w):
                    if inp[r][c] != out[r][c]:
                        if inp[r][c] in color_map:
                            if color_map[inp[r][c]] != out[r][c]:
                                return None  # Conflicting
                        else:
                            color_map[inp[r][c]] = out[r][c]

        return color_map if color_map else None

    def _score_candidate(self, candidate, train_inputs, train_outputs):
        """Score a candidate by checking against training outputs."""
        # For simplicity, just check size match
        if not train_outputs:
            return 0.5

        expected_h, expected_w = len(train_outputs[0]), len(train_outputs[0][0])
        actual_h, actual_w = len(candidate), len(candidate[0])

        if actual_h == expected_h and actual_w == expected_w:
            # Size matches - check content similarity
            matches = sum(
                1 for inp, out in zip(train_inputs, train_outputs)
                if len(candidate) == len(out) and len(candidate[0]) == len(out[0])
            )
            return matches / len(train_outputs)

        return 0.0

    def _grids_equal(self, grid1, grid2):
        """Check if two grids are equal."""
        if len(grid1) != len(grid2):
            return False
        for row1, row2 in zip(grid1, grid2):
            if row1 != row2:
                return False
        return True


__all__ = ['ComprehensiveEnsembleSolver', 'TaskCharacteristics', 'TransformationPrimitives']



