#!/usr/bin/env python3
"""
Improved ARC-AGI-2 Solver
Implements comprehensive transformation detection with composition support.
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import copy
import itertools


# ============================================================================
# Core Transformations
# ============================================================================

def rotate_90(grid):
    """Rotate grid 90 degrees clockwise."""
    return [list(row) for row in zip(*grid[::-1])]

def rotate_180(grid):
    """Rotate grid 180 degrees."""
    return [row[::-1] for row in grid[::-1]]

def rotate_270(grid):
    """Rotate grid 270 degrees clockwise."""
    return [list(row)[::-1] for row in zip(*grid)][::-1]

def reflect_h(grid):
    """Reflect horizontally (flip vertical)."""
    return grid[::-1]

def reflect_v(grid):
    """Reflect vertically (flip horizontal)."""
    return [row[::-1] for row in grid]

def transpose(grid):
    """Transpose grid."""
    return [list(row) for row in zip(*grid)]

def crop(grid, top, bottom, left, right):
    """Crop grid by removing borders."""
    return [row[left:len(row)-right] for row in grid[top:len(grid)-bottom]]

def pad(grid, val, top, bottom, left, right):
    """Pad grid with value."""
    h, w = len(grid), len(grid[0]) if grid else 0
    new_h = h + top + bottom
    new_w = w + left + right
    result = [[val] * new_w for _ in range(new_h)]
    for r in range(h):
        for c in range(w):
            result[r + top][c + left] = grid[r][c]
    return result

def subsample(grid, row_step, col_step):
    """Subsample grid by taking every row_step-th row and col_step-th column."""
    result = []
    for i in range(0, len(grid), row_step):
        row = []
        for j in range(0, len(grid[0]), col_step):
            row.append(grid[i][j])
        result.append(row)
    return result


# ============================================================================
# Color Transformation Detection
# ============================================================================

def learn_color_mapping(train_inputs, train_outputs) -> Optional[Dict[int, int]]:
    """Learn color mapping from training pairs."""
    color_map = {}

    for inp, out in zip(train_inputs, train_outputs):
        h = min(len(inp), len(out))
        w = min(len(inp[0]) if inp else 0, len(out[0]) if out else 0)
        for r in range(h):
            for c in range(w):
                inp_val = inp[r][c]
                out_val = out[r][c]
                if inp_val != out_val:
                    if inp_val in color_map:
                        if color_map[inp_val] != out_val:
                            return None  # Inconsistent mapping
                    else:
                        color_map[inp_val] = out_val

    return color_map if color_map else None

def apply_color_map(grid, color_map):
    """Apply color mapping to grid."""
    return [[color_map.get(cell, cell) for cell in row] for row in grid]


# ============================================================================
# Geometric Transformation Detection
# ============================================================================

def detect_geometric_transform(train_inputs, train_outputs) -> Optional[str]:
    """Detect if a simple geometric transformation applies to all pairs."""
    candidates = []

    # Test each transformation
    transforms = [
        ("identity", lambda g: g),
        ("rotate_90", rotate_90),
        ("rotate_180", rotate_180),
        ("rotate_270", rotate_270),
        ("reflect_h", reflect_h),
        ("reflect_v", reflect_v),
        ("transpose", transpose),
    ]

    for name, transform in transforms:
        if all(transform(inp) == out for inp, out in zip(train_inputs, train_outputs)):
            candidates.append(name)

    return candidates[0] if candidates else None
