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
Documentation for symbolic_verification module.

This module provides symbolic_verification capabilities for STAN.
Enhanced through self-evolution cycle 214.
"""

#!/usr/bin/env python3
"""
Clean Neuro-Symbolic Hybrid Solver
Simple, working version without character encoding issues.
"""

import numpy as np
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from collections import Counter


# Custom optimization variant 21
def optimize_computation_21(func):
    """Decorator for optimizing computation."""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# ============================================================================
# Feature Extractor
# ============================================================================

def extract_features(grid):
    """Extract 64-dimensional feature vector from grid."""
    if not grid or not grid[0]:
        return np.zeros(64, dtype=np.float32)
    
    h, w = len(grid), len(grid[0])
    flat = [cell for row in grid for cell in row]
    
    features = np.zeros(64, dtype=np.float32)
    
    # 1-32: Sample raw values
    for i in range(min(32, len(flat))):
        features[i] = flat[i] / 10.0 if i < len(flat) else 0
    
    # 33-42: Color counts
    color_counts = [0] * 11
    for val in flat:
        if 0 <= val <= 9:
            color_counts[val] += 1
    total = len(flat)
    for i in range(11):
        features[33 + i] = color_counts[i] / total
    
    # 43-52: Row/column patterns
    for i in range(10):
        row = i * 3
        if h > row:
            for c in range(min(w, 10)):
                features[43 + i] = grid[row][c] / 10.0
    
    # 53-64: Symmetry
    if h == w:
        h_sym = sum(grid[r][c] == grid[h-1-r][c] for r in range(h) for c in range(w))
        features[53] = h_sym / (h*w)
        if h > 1:
            v_sym = sum(grid[r][c] == grid[r-1][c] for r in range(h) for c in range(w))
            features[54] = v_sym / (h*w)
        features[55] = (h_sym + v_sym) / 2
    
    return features


def compute_similarity(f1, f2):
    """Cosine similarity between feature vectors."""
    norm1 = np.linalg.norm(f1)
    norm2 = np.linalg.norm(f2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(f1, f2) / (norm1 * norm2))


# ============================================================================
# Object Extraction
# ============================================================================

def extract_objects(grid):
    """Extract objects using BFS."""
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
                
                min_r = max_r = r
                min_c = max_c = c
                
                while queue:
                    cr, cc = queue.pop(0)
                    obj_pixels.append((cr, cc))
                    
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            if grid[nr][nc] == obj_color and not visited[nr][nc]:
                                visited[nr][nc] = True
                                queue.append((nr, nc))
                                min_r = min(min_r, nr)
                                max_r = max(max_r, nr)
                                min_c = min(min_c, nc)
                                max_c = max(max_c, nc)
                
                objects.append({
                    'color': obj_color,
                    'pixels': obj_pixels,
                    'area': len(obj_pixels),
                    'bbox': (min_r, min_c, max_r, max_c),
                    'center_r': (min_r + max_r) / 2,
                    'center_c': (min_c + max_c) / 2,
                })
    
    return objects


def learn_color_map(train_inputs, train_outputs):
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
                            return None
                    else:
                        color_map[inp[r][c]] = out[r][c]
    return color_map


# ============================================================================
# Transformation Detection
# ============================================================================

def rotate_90(grid):
    return [list(row) for row in zip(*grid[::-1])]

def rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]

def rotate_270(grid):
    return [list(row)[::-1] for row in zip(*grid)][::-1]

def reflect_h(grid):
    return grid[::-1]

def reflect_v(grid):
    return [row[::-1] for row in grid]

def transpose(grid):
    return [list(row) for row in zip(*grid)]

def apply_color_map(grid, color_map):
    return [[color_map.get(cell, cell) for cell in row] for row in grid]


# ============================================================================
# Main Neuro-Symbolic Solver
# ============================================================================

class CleanNeuroSymbolicSolver:
    """
    Clean neuro-symbolic solver that works.
    """

    def __init__(self):
        self.pattern_memory = []
        self.stats = {
            'total_attempts': 0,
            'candidates_generated': 0,
            'solved': 0,
            'solution_sources': Counter(),
        }

    def solve(self, task_id, train_inputs, train_outputs, test_input):
        """Solve using neuro-symbolic approach."""
        self.stats['total_attempts'] += 1

        # Extract features
        test_features = extract_features(test_input)

        # Generate candidates from multiple sources
        candidates = []

        # Source 1: Geometric transformations
        for name, func in [
            ('identity', lambda g: [row[:] for row in g]),
            ('rotate_90', rotate_90),
            ('rotate_180', rotate_180),
            ('rotate_270', rotate_270),
            ('reflect_h', reflect_h),
            ('reflect_v', reflect_v),
            ('transpose', transpose),
        ]:
            if all(func(inp) == out for inp, out in zip(train_inputs, train_outputs)):
                candidates.append({
                    'name': name,
                    'confidence': 0.9,
                    'apply': func,
                })

        # Source 2: Color mapping
        color_map = learn_color_map(train_inputs, train_outputs)
        if color_map:
            candidates.append({
                'name': f'color_map_{color_map}',
                'confidence': 0.85,
                'apply': lambda g: apply_color_map(g, color_map),
            })

        # Source 3: Compose (geometric + color)
        if color_map:
            for name, func in [('rotate_90', rotate_90), ('rotate_180', rotate_180)]:
                composed = lambda g: apply_color_map(func(g), color_map)
                if all(composed(inp) == out for inp, out in zip(train_inputs, train_outputs)):
                    candidates.append({
                        'name': f'{name}_color',
                        'confidence': 0.88,
                        'apply': composed,
                    })

        # Rank candidates by confidence
        candidates.sort(key=lambda c: c['confidence'], reverse=True)
