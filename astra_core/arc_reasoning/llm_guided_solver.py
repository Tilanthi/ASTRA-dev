#!/usr/bin/env python3
"""
LLM-Guided ARC Solver
Uses LLM reasoning to understand tasks and generate transformation programs.
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from collections import Counter
import hashlib
import json


# ============================================================================
# LLM-Guided Program Synthesis
# ============================================================================

@dataclass
class TaskAnalysis:
    """Analysis of an ARC task."""
    task_id: str
    input_size: Tuple[int, int]
    output_size: Tuple[int, int]
    num_colors: int
    size_change: str  # "same", "compress", "expand"
    has_objects: bool
    dominant_colors: List[int]
    structural_hint: str


def analyze_task_structure(train_inputs, train_outputs) -> TaskAnalysis:
    """Analyze task structure to guide LLM reasoning."""
    if not train_inputs or not train_outputs:
        return TaskAnalysis("", (0, 0), (0, 0), 0, "unknown", False, [], "")

    inp_h, inp_w = len(train_inputs[0]), len(train_inputs[0][0])
    out_h, out_w = len(train_outputs[0]), len(train_outputs[0][0])

    # Detect size change pattern
    if inp_h == out_h and inp_w == out_w:
        size_change = "same"
    elif inp_h > out_h or inp_w > out_w:
        size_change = "compress"
    else:
        size_change = "expand"

    # Count colors
    all_colors = set()
    for inp in train_inputs:
        for row in inp:
            all_colors.update(row)
    for out in train_outputs:
        for row in out:
            all_colors.update(row)
    num_colors = len(all_colors) - (1 if 0 in all_colors else 0)

    # Find dominant colors
    color_counts = Counter()
    for inp in train_inputs:
        for row in inp:
            for cell in row:
                if cell != 0:
                    color_counts[cell] += 1
    dominant_colors = [c for c, _ in color_counts.most_common(3)]

    # Check for objects
    has_objects = any(c != 0 for inp in train_inputs for row in inp for c in row)

    # Generate structural hint
    if size_change == "compress":
        structural_hint = "Output is smaller than input - task may involve compression, selecting key elements, or summarizing patterns"
    elif size_change == "expand":
        structural_hint = "Output is larger than input - task may involve repetition, tiling, or expansion"
    elif num_colors <= 2:
        structural_hint = "Few colors - task may be about binary operations or simple transformations"
    else:
        structural_hint = "Complex color patterns - task likely involves color mapping or multi-color logic"

    return TaskAnalysis(
        task_id="",
        input_size=(inp_h, inp_w),
        output_size=(out_h, out_w),
        num_colors=num_colors,
        size_change=size_change,
        has_objects=has_objects,
        dominant_colors=dominant_colors,
        structural_hint=structural_hint
    )


# ============================================================================
# Analogy-Based Pattern Library
# ============================================================================

class PatternLibrary:
    """Library of known transformation patterns."""

    # Common ARC transformation patterns
    PATTERNS = {
        # Identity
        "identity": {
            "description": "No transformation - output equals input",
            "code": "lambda grid: [row[:] for row in grid]",
            "check": "inp == out",
        },

        # Rotation
        "rotate_90": {
            "description": "Rotate grid 90 degrees clockwise",
            "code": "lambda grid: [list(row) for row in zip(*grid[::-1])]",
            "check": "len(inp) == len(out[0]) and len(inp[0]) == len(out)",
        },
        "rotate_180": {
            "description": "Rotate grid 180 degrees",
            "code": "lambda grid: [row[::-1] for row in grid[::-1]]",
            "check": "len(inp) == len(out) and len(inp[0]) == len(out[0])",
        },
        "rotate_270": {
            "description": "Rotate grid 270 degrees clockwise",
            "code": "lambda grid: [list(row)[::-1] for row in zip(*grid)][::-1]",
            "check": "len(inp) == len(out[0]) and len(inp[0]) == len(out)",
        },

        # Reflection
        "reflect_horizontal": {
            "description": "Mirror grid horizontally (top-bottom)",
            "code": "lambda grid: grid[::-1]",
            "check": "len(inp) == len(out) and len(inp[0]) == len(out[0])",
        },
        "reflect_vertical": {
            "description": "Mirror grid vertically (left-right)",
            "code": "lambda grid: [row[::-1] for row in grid]",
            "check": "len(inp) == len(out) and len(inp[0]) == len(out[0])",
        },

        # Transposition
        "transpose": {
            "description": "Transpose grid (swap rows and columns)",
            "code": "lambda grid: [list(row) for row in zip(*grid)]",
            "check": "len(inp) == len(out[0]) and len(inp[0]) == len(out)",
        },

        # Color operations
        "color_invert": {
            "description": "Invert all non-zero colors",
            "code": "lambda grid: [[10 - c if c != 0 else 0 for c in row] for row in grid]",
            "check": "len(inp) == len(out) and len(inp[0]) == len(out[0])",
        },
        "color_to_gray": {
            "description": "Convert all non-zero colors to 1",
            "code": "lambda grid: [[1 if c != 0 else 0 for c in row] for row in grid]",
            "check": "all(c in (0, 1) for row in out for c in row)",
        },

        # Object operations
        "extract_objects": {
            "description": "Extract colored objects and arrange them",
            "code": None,  # Complex - requires special handling
            "check": "size_change == 'compress'",
        },
        "fill_holes": {
            "description": "Fill empty spaces between same-colored cells",
            "code": None,
            "check": "has_objects and len(out) == len(inp)",
        },

        # Grid operations
        "crop": {
            "description": "Crop grid to content boundaries",
            "code": None,
            "check": "size_change == 'compress'",
        },
        "pad": {
            "description": "Pad grid with borders",
            "code": None,
            "check": "size_change == 'expand'",
        },

        # Pattern operations
        "tile_center": {
            "description": "Tile the center 2x2 pattern",
            "code": None,
            "check": "size_change == 'expand'",
        },
    }

    @classmethod
    def find_matching_patterns(cls, analysis: TaskAnalysis) -> List[str]:
        """Find patterns that match the task analysis."""
        matches = []

        for pattern_name, pattern_info in cls.PATTERNS.items():
            if cls._pattern_matches(pattern_info, analysis):
                matches.append(pattern_name)

        return matches

    @classmethod
    def _pattern_matches(cls, pattern_info: Dict, analysis: TaskAnalysis) -> bool:
        """Check if a pattern matches the task analysis."""
        check_condition = pattern_info.get("check", "")

        # Parse simple conditions
        if "size_change" in check_condition:
            expected = check_condition.split("'")[1]
            if analysis.size_change != expected:
                return False

        if "has_objects" in check_condition:
            if not analysis.has_objects:
                return False

        return True


# ============================================================================
# Hierarchical Decomposition
# ============================================================================

class DecomposedTask:
    """A task broken down into sub-problems."""

    def __init__(self, original_task):
        self.original = original_task
        self.sub_problems = []
        self.solution_order = []

    def add_sub_problem(self, name: str, transform_func, priority: int):
        """Add a sub-problem to solve."""
        self.sub_problems.append({
            'name': name,
            'transform': transform_func,
            'priority': priority,
        })
        self.solution_order.append(name)

    def solve_sub_problems(self, grid):
        """Apply sub-problem solutions in order."""
