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
Ultra-Advanced ARC Solver with Strict Verification
Only accepts transformations that perfectly match training examples.
Aims for 100% accuracy by being extremely selective.
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import copy
import itertools


# ============================================================================
# Strict Verification
# ============================================================================

def verify_transformation_on_all_training(
    transform_func: Callable,
    train_inputs: List[List[List[int]]],
    train_outputs: List[List[List[int]]]
) -> bool:
    """
    Strictly verify that transform_func works on ALL training pairs.
    Returns True only if it produces exact output for every pair.
    """
    for inp, expected_out in zip(train_inputs, train_outputs):
        try:
            predicted_out = transform_func(inp)
            if predicted_out is None:
                return False

            # Check dimensions match
            if len(predicted_out) != len(expected_out):
                return False
            if any(len(pr) != len(ex) for pr, ex in zip(predicted_out, expected_out)):
                return False

            # Check exact match
            for pr_row, ex_row in zip(predicted_out, expected_out):
                if pr_row != ex_row:
                    return False

        except Exception:
            return False

    return True


# ============================================================================
# All Transformations to Try
# ============================================================================

def rotate_90(grid: List[List[int]]) -> List[List[int]]:
    return [list(row) for row in zip(*grid[::-1])]

def rotate_180(grid: List[List[int]]) -> List[List[int]]:
    return [row[::-1] for row in grid[::-1]]

def rotate_270(grid: List[List[int]]) -> List[List[int]]:
    return [list(row) for row in zip(*grid)][::-1]

def reflect_h(grid: List[List[int]]) -> List[List[int]]:
    return grid[::-1]

def reflect_v(grid: List[List[int]]) -> List[List[int]]:
    return [row[::-1] for row in grid]

def transpose(grid: List[List[int]]) -> List[List[int]]:
    return [list(row) for row in zip(*grid)]

def swap_colors(grid: List[List[int]], color1: int, color2: int) -> List[List[int]]:
    """Swap two colors in grid."""
    return [[color2 if cell == color1 else (color1 if cell == color2 else cell) for cell in row] for row in grid]

def invert_grid(grid: List[List[int]]) -> List[List[int]]:
    """Invert all non-zero colors."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    max_val = max(max(row) for row in grid)
    return [[max_val - cell if cell != 0 else 0 for cell in row] for row in grid]

def complement_grid(grid: List[List[int]]) -> List[List[int]]:
    """Complement all colors (keep 0 as 0)."""
    colors_used = set()
    for row in grid:
        colors_used.update(row)
    colors_used.discard(0)

    if not colors_used:
        return [row[:] for row in grid]

    max_color = max(colors_used)
    complement_map = {c: max_color - c if c != 0 else 0 for c in range(max_color + 1)}

    return [[complement_map.get(cell, cell) for cell in row] for row in grid]

def apply_same(grid: List[List[int]]) -> List[List[int]]:
    """Identity function - output equals input."""
    return [row[:] for row in grid]

def get_all_colors_used(grids: List[List[List[int]]]) -> Set[int]:
    """Get all colors used across all grids."""
    colors = set()
    for grid in grids:
        for row in grid:
            colors.update(row)
    return colors

def create_color_map_transform(train_inputs: List[List[List[int]]], train_outputs: List[List[List[int]]]) -> Optional[Callable]:
    """Create a color mapping transform based on training pairs."""
    color_map = {}

    for inp, out in zip(train_inputs, train_outputs):
        h = min(len(inp), len(out))
        w = min(len(inp[0]), len(out[0]))

        for r in range(h):
            for c in range(w):
                inp_val = inp[r][c]
                out_val = out[r][c]
                if inp_val != out_val:
                    if inp_val in color_map:
                        if color_map[inp_val] != out_val:
                            return None  # Inconsistent
                    else:
                        color_map[inp_val] = out_val

    if not color_map:
        return None

    return lambda grid: [[color_map.get(cell, cell) for cell in row] for row in grid]


# ============================================================================
# Main Ultra Solver
# ============================================================================

class UltraARCSolver:
    """
    Ultra-Advanced ARC Solver with strict verification.
    Only accepts transformations that perfectly match training data.
    """

    def __init__(self):
        self.stats = {
            'total_attempts': 0,
            'perfect_matches': 0,
            'candidates_tried': 0,
            'transformations_tried': defaultdict(int),
        }

    def solve(
        self,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]],
        test_input: List[List[int]]
    ) -> Optional[List[List[int]]]:
        """Solve using extensive search with strict verification."""
        self.stats['total_attempts'] += 1

        candidates = []

        # Get all transformation functions to try
        transforms = self._get_all_transforms(train_inputs, train_outputs)

        self.stats['transformations_tried']['total'] += len(transforms)

        # Try each transformation with strict verification
        for transform_name, transform_func in transforms:
            self.stats['transformations_tried'][transform_name] += 1
