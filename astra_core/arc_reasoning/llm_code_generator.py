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
LLM-Based Code Generator for ARC Tasks
Uses the LLM to analyze tasks and generate specific transformation code.
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from collections import Counter
import ast
import sys


# ============================================================================
# Task Description Generation
# ============================================================================

def generate_task_description(task_id: str,
                           train_inputs: List[List[List[int]]],
                           train_outputs: List[List[List[int]]],
                           test_input: List[List[int]]) -> str:
    """Generate a detailed description of the task for LLM analysis."""
    description_parts = []

    # Basic info
    inp_h, inp_w = len(train_inputs[0]), len(train_inputs[0][0])
    out_h, out_w = len(train_outputs[0]), len(train_outputs[0][0])
    test_h, test_w = len(test_input), len(test_input[0])

    description_parts.append(f"Task {task_id}:")
    description_parts.append(f"  Input size: {inp_h}x{inp_w}")
    description_parts.append(f"  Output size: {out_h}x{out_w}")
    description_parts.append(f"  Test size: {test_h}x{test_w}")

    # Size change
    if inp_h != out_h or inp_w != out_w:
        ratio = (out_h * out_w) / (inp_h * inp_w)
        description_parts.append(f"  Size change: {ratio:.2%} compression/expansion")
    else:
        description_parts.append("  Size change: None (same size)")

    # Color analysis
    input_colors = set()
    output_colors = set()
    for inp in train_inputs:
        for row in inp:
            input_colors.update(row)
    for out in train_outputs:
        for row in out:
            output_colors.update(row)

    description_parts.append(f"  Input colors: {sorted([c for c in input_colors if c != 0])}")
    description_parts.append(f"  Output colors: {sorted([c for c in output_colors if c != 0])}")

    # Check for color mapping
    color_changes = set()
    for inp, out in zip(train_inputs, train_outputs):
        h = min(len(inp), len(out))
        w = min(len(inp[0]), len(out[0]))
        for r in range(h):
            for c in range(w):
                if inp[r][c] != out[r][c]:
                    color_changes.add((inp[r][c], out[r][c]))

    if color_changes:
        description_parts.append(f"  Color changes detected: {color_changes}")

    # Sample transformation (first pair)
    description_parts.append("\n  First training pair transformation:")
    inp_sample = train_inputs[0]
    out_sample = train_outputs[0]
    description_parts.append(f"    Input shape: {len(inp_sample)}x{len(inp_sample[0])}")
    description_parts.append(f"    Output shape: {len(out_sample)}x{len(out_sample[0])}")

    # Check for objects
    has_objects = any(c != 0 for inp in train_inputs for row in inp for c in row)
    if has_objects:
        description_parts.append("  Contains: Colored objects/regions")

    # Pattern hints
    patterns = []
    if inp_h == out_h and inp_w == out_w:
        patterns.append("same-size transformation")
    if (out_h * out_w) < (inp_h * inp_w):
        patterns.append("compression")
    if color_changes:
        patterns.append("color transformation")
    if has_objects:
        patterns.append("object manipulation")

    if patterns:
        description_parts.append(f"  Likely patterns: {', '.join(patterns)}")

    return "\n".join(description_parts)


# ============================================================================
# LLM-Generated Code Templates
# ============================================================================

CODE_TEMPLATES = {
    "color_map": """
# Color mapping transformation
def solve(grid):
    # Apply color mapping
    color_map = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}
    return [[color_map.get(cell, cell) for cell in row] for row in grid]
""",
    "rotation": """
# Rotation transformation
def solve(grid):
    # Rotate 90 degrees clockwise
    return [list(row) for row in zip(*grid[::-1])]
"""
}
