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
Pattern Extension Module for ARC-AGI-2
Handles tasks that involve extending/filling patterns horizontally or vertically
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Any
from dataclasses import dataclass
from collections import defaultdict, Counter


# ============================================================================
# Pattern Extension Analyzer
# ============================================================================

class PatternExtensionAnalyzer:
    """
    Analyze and detect pattern extension transformations.
    These are common in ARC-AGI-2: extending colored regions
    horizontally or vertically with regular spacing.
    """

    def __init__(self):
        pass

    def detect_pattern_extension(
        self,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if task involves pattern extension.
        Returns pattern info if detected, None otherwise.
        """
        if not train_inputs or not train_outputs:
            return None

        patterns = []

        for inp, out in zip(train_inputs, train_outputs):
            pattern = self._analyze_single_pair(inp, out)
            if pattern:
                patterns.append(pattern)

        if not patterns:
            return None

        # Check if pattern is consistent across all pairs
        return self._unify_patterns(patterns)

    def _analyze_single_pair(
        self,
        inp: List[List[int]],
        out: List[List[int]]
    ) -> Optional[Dict[str, Any]]:
        """Analyze a single input-output pair for extension patterns."""
        if not inp or not out:
            return None

        h, w = len(inp), len(inp[0])

        # Find differences
        diffs = self._find_differences(inp, out)

        if not diffs:
            return None  # No transformation

        # Check if differences suggest extension
        # Pattern: colors appear on one side of a separator/boundary
        # and extend to the other side

        # Find potential separator column
        sep_col = self._find_separator(inp, diffs)

        if sep_col is None:
            # Try horizontal separator
            return self._analyze_vertical_extension(inp, out, diffs)

        return self._analyze_horizontal_extension(inp, out, diffs, sep_col)

    def _find_differences(
        self,
        inp: List[List[int]],
        out: List[List[int]]
    ) -> List[Tuple[int, int, int, int]]:
        """Find cells where input and output differ."""
        diffs = []
        h, w = len(inp), len(inp[0])

        for r in range(h):
            for c in range(w):
                if inp[r][c] != out[r][c]:
                    diffs.append((r, c, inp[r][c], out[r][c]))

        return diffs

    def _find_separator(
        self,
        inp: List[List[int]],
        diffs: List[Tuple[int, int, int, int]]
    ) -> Optional[int]:
        """
        Find separator column based on:
        1. Column with uniform non-zero value in input
        2. Differences appear primarily on one side
        """
        h, w = len(inp), len(inp[0])

        # Look for columns with uniform non-zero value
        for c in range(w):
            col_vals = [inp[r][c] for r in range(h)]
            unique_vals = set(col_vals)

            # Find separator: uniform column that's non-zero (or could be zero)
            # and has differences on only one side
            if len(unique_vals) == 1:
                col_val = list(unique_vals)[0]

                # Check if differences are on one side
                left_diffs = sum(1 for r, cc, _, _ in diffs if cc < c)
                right_diffs = sum(1 for r, cc, _, _ in diffs if cc > c)

                # If all differences are on one side, this could be a separator
                if left_diffs == 0 and right_diffs > 0:
                    return c

        return None

    def _analyze_horizontal_extension(
        self,
        inp: List[List[int]],
        out: List[List[int]],
        diffs: List[Tuple[int, int, int, int]],
        sep_col: int
    ) -> Optional[Dict[str, Any]]:
        """Analyze horizontal extension pattern."""
        h, w = len(inp), len(inp[0])

        # For each row, find the color on left of separator
        # and the pattern on the right
        row_patterns = []

        for r in range(h):
            # Find color on left side
            left_colors = [inp[r][c] for c in range(sep_col) if inp[r][c] != 0]
            left_color = left_colors[0] if left_colors else None

            if left_color is None:
                continue

            # Find positions of this color in output (right of separator)
            right_positions = [c for c in range(sep_col, w) if out[r][c] == left_color]

            if right_positions:
                row_patterns.append({
                    'row': r,
                    'color': left_color,
                    'positions': right_positions,
                    'start_col': sep_col
                })

        if not row_patterns:
            return None

        # Analyze spacing pattern
        return {
            'type': 'horizontal_extension',
            'separator_col': sep_col,
            'row_patterns': row_patterns
        }

    def _analyze_vertical_extension(
        self,
        inp: List[List[int]],
        out: List[List[int]],
        diffs: List[Tuple[int, int, int, int]]
    ) -> Optional[Dict[str, Any]]:
        """Analyze vertical extension pattern."""
        # Similar to horizontal but transposed
        # For now, return None as it's less common
        return None

    def _unify_patterns(
        self,
        patterns: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Unify patterns from multiple training pairs."""
        if not patterns:
            return None

        # All patterns should have same type
        pattern_type = patterns[0]['type']
        if not all(p['type'] == pattern_type for p in patterns):
            return None

        # For horizontal extension, try to find pattern even with different separators
        if pattern_type == 'horizontal_extension':
            sep_cols = [p['separator_col'] for p in patterns]

            # Use the most common separator, or the first one
            from collections import Counter
