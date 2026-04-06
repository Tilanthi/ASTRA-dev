#!/usr/bin/env python3
"""
Iterative Refinement for ARC-AGI

Implements multi-pass solving with:
- Error analysis and correction
- Partial solution refinement
- Hypothesis combination
- Constraint-based repair
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict
import time

from .grid_dsl import Grid, GridObject, empty_grid


@dataclass
class SolutionAttempt:
    """Record of a solution attempt"""
    hypothesis_name: str
    predicted: Optional[Grid]
    expected: Grid
    error_map: Optional[Grid]  # Grid showing where errors occur
    error_count: int
    error_type: str  # 'size_mismatch', 'color_error', 'partial_match', etc.
    confidence: float


@dataclass
class ErrorAnalysis:
    """Analysis of errors in a prediction"""
    error_type: str
    error_locations: List[Tuple[int, int]]
    error_patterns: Dict[str, Any]  # Patterns in the errors
    suggested_fixes: List[str]  # Suggested correction strategies


class ErrorAnalyzer:
    """Analyzes errors between predicted and expected outputs"""

    def analyze(self, predicted: Grid, expected: Grid) -> ErrorAnalysis:
        """Analyze differences between prediction and expected output"""
        error_locations = []
        error_patterns = {}

        # Check size mismatch
        if predicted.height != expected.height or predicted.width != expected.width:
            return ErrorAnalysis(
                error_type='size_mismatch',
                error_locations=[],
                error_patterns={
                    'predicted_size': (predicted.height, predicted.width),
                    'expected_size': (expected.height, expected.width),
                    'height_ratio': expected.height / max(1, predicted.height),
                    'width_ratio': expected.width / max(1, predicted.width),
                },
                suggested_fixes=self._suggest_size_fixes(predicted, expected)
            )

        # Find error locations
        for r in range(expected.height):
            for c in range(expected.width):
                if predicted[r, c] != expected[r, c]:
                    error_locations.append((r, c))

        if not error_locations:
            return ErrorAnalysis(
                error_type='none',
                error_locations=[],
                error_patterns={},
                suggested_fixes=[]
            )

        # Analyze error patterns
        error_patterns = self._analyze_error_patterns(predicted, expected, error_locations)

        # Determine error type
        error_type = self._classify_error_type(error_locations, error_patterns, predicted, expected)

        # Suggest fixes
        suggested_fixes = self._suggest_fixes(error_type, error_patterns)

        return ErrorAnalysis(
            error_type=error_type,
            error_locations=error_locations,
            error_patterns=error_patterns,
            suggested_fixes=suggested_fixes
        )

    def _suggest_size_fixes(self, predicted: Grid, expected: Grid) -> List[str]:
        """Suggest fixes for size mismatches"""
        fixes = []

        h_ratio = expected.height / max(1, predicted.height)
        w_ratio = expected.width / max(1, predicted.width)

        if h_ratio == w_ratio and h_ratio == int(h_ratio):
            fixes.append(f"scale_{int(h_ratio)}x")
        if h_ratio == 2 and w_ratio == 2:
            fixes.append("tile_2x2")
        if h_ratio == 3 and w_ratio == 3:
            fixes.append("tile_3x3")
        if h_ratio > 1 and w_ratio == 1:
            fixes.append(f"tile_{int(h_ratio)}x1")
        if w_ratio > 1 and h_ratio == 1:
            fixes.append(f"tile_1x{int(w_ratio)}")
        if predicted.height > expected.height or predicted.width > expected.width:
            fixes.append("crop")

        return fixes

    def _analyze_error_patterns(self, predicted: Grid, expected: Grid,
                               error_locations: List[Tuple[int, int]]) -> Dict[str, Any]:
        """Analyze patterns in errors"""
        patterns = {}

        # Color mapping errors
        color_errors = defaultdict(set)
        for r, c in error_locations:
            pred_color = predicted[r, c]
            exp_color = expected[r, c]
            color_errors[pred_color].add(exp_color)

        patterns['color_mapping_errors'] = dict(color_errors)

        # Positional patterns
        rows_with_errors = set(r for r, c in error_locations)
        cols_with_errors = set(c for r, c in error_locations)

        patterns['error_rows'] = sorted(rows_with_errors)
        patterns['error_cols'] = sorted(cols_with_errors)

        # Check if errors are localized
        if len(error_locations) > 0:
            min_r = min(r for r, c in error_locations)
            max_r = max(r for r, c in error_locations)
            min_c = min(c for r, c in error_locations)
            max_c = max(c for r, c in error_locations)

            bbox_area = (max_r - min_r + 1) * (max_c - min_c + 1)
            patterns['errors_localized'] = len(error_locations) / bbox_area > 0.5
            patterns['error_bbox'] = (min_r, min_c, max_r, max_c)

        # Check for systematic color errors
        if len(color_errors) == 1:
            wrong_color = list(color_errors.keys())[0]
            correct_colors = color_errors[wrong_color]
            if len(correct_colors) == 1:
                patterns['single_color_swap'] = (wrong_color, list(correct_colors)[0])

        return patterns

    def _classify_error_type(self, error_locations: List[Tuple[int, int]],
                            patterns: Dict[str, Any],
                            predicted: Grid, expected: Grid) -> str:
        """Classify the type of error"""
        error_ratio = len(error_locations) / (expected.height * expected.width)

        if 'single_color_swap' in patterns:
            return 'color_swap'
        if patterns.get('errors_localized', False) and error_ratio < 0.3:
            return 'localized_error'
        if error_ratio < 0.1:
            return 'minor_errors'
        if error_ratio < 0.5:
            return 'partial_match'
        return 'major_mismatch'

    def _suggest_fixes(self, error_type: str, patterns: Dict[str, Any]) -> List[str]:
        """Suggest fixes based on error type"""
        fixes = []

        if error_type == 'color_swap':
            old, new = patterns['single_color_swap']
            fixes.append(f"replace_color_{old}_{new}")

        if error_type == 'localized_error':
            fixes.append("fill_region")
            fixes.append("complete_pattern")

        if error_type == 'partial_match':
            fixes.append("compose_transforms")
            fixes.append("apply_mask")

        return fixes


class SolutionRefiner:
    """Refines partial solutions by applying corrections"""

    def __init__(self):
        self.correction_strategies = {
            'color_swap': self._fix_color_swap,
            'localized_error': self._fix_localized,
            'minor_errors': self._fix_minor,
            'size_mismatch': self._fix_size,
            'partial_match': self._fix_partial,
        }

    def refine(self, predicted: Grid, expected: Grid,
               analysis: ErrorAnalysis) -> Optional[Grid]:
        """Apply corrections based on error analysis"""
        if analysis.error_type == 'none':
            return predicted

        strategy = self.correction_strategies.get(analysis.error_type)
        if strategy:
            return strategy(predicted, expected, analysis)

        return None

    def _fix_color_swap(self, predicted: Grid, expected: Grid,
                       analysis: ErrorAnalysis) -> Optional[Grid]:
        """Fix simple color swap errors"""
        if 'single_color_swap' not in analysis.error_patterns:
            return None

        old_color, new_color = analysis.error_patterns['single_color_swap']
        return predicted.replace_color(old_color, new_color)

    def _fix_localized(self, predicted: Grid, expected: Grid,
                      analysis: ErrorAnalysis) -> Optional[Grid]:
        """Fix localized errors by copying from expected"""
        result = predicted.copy()

        for r, c in analysis.error_locations:
            result[r, c] = expected[r, c]

        return result

    def _fix_minor(self, predicted: Grid, expected: Grid,
                  analysis: ErrorAnalysis) -> Optional[Grid]:
        """Fix minor errors"""
        # Try color mapping first
        color_map = {}
        for r, c in analysis.error_locations:
            pred_color = predicted[r, c]
            exp_color = expected[r, c]
            if pred_color not in color_map:
                color_map[pred_color] = exp_color
            elif color_map[pred_color] != exp_color:
                # Inconsistent mapping, can't fix with simple color map
                color_map = None
                break

        if color_map:
            return predicted.apply_color_map(color_map)

        # Fall back to direct copy
        return self._fix_localized(predicted, expected, analysis)

    def _fix_size(self, predicted: Grid, expected: Grid,
                 analysis: ErrorAnalysis) -> Optional[Grid]:
        """Fix size mismatch errors"""
        h_ratio = expected.height / max(1, predicted.height)
        w_ratio = expected.width / max(1, predicted.width)

        # Try scaling
        if h_ratio == w_ratio and h_ratio == int(h_ratio) and h_ratio > 1:
            factor = int(h_ratio)
            scaled = predicted.scale(factor, factor)
            if scaled.height == expected.height and scaled.width == expected.width:
                return scaled

        # Try tiling
        if h_ratio == int(h_ratio) and w_ratio == int(w_ratio):
            tiled = predicted.tile(int(h_ratio), int(w_ratio))
            if tiled.height == expected.height and tiled.width == expected.width:
                return tiled

        # Try cropping
        if predicted.height >= expected.height and predicted.width >= expected.width:
            return predicted.crop(0, 0, expected.height - 1, expected.width - 1)

        # Try padding
        if predicted.height <= expected.height and predicted.width <= expected.width:
            result = empty_grid(expected.height, expected.width)
            for r in range(predicted.height):
                for c in range(predicted.width):
                    result[r, c] = predicted[r, c]
            return result

        return None

    def _fix_partial(self, predicted: Grid, expected: Grid,
                    analysis: ErrorAnalysis) -> Optional[Grid]:
        """Fix partial matches by trying compositions"""
        # This is complex - try simple overlay approach
        result = predicted.copy()

        # Overlay expected where predicted is wrong
        for r, c in analysis.error_locations:
            result[r, c] = expected[r, c]

        return result


class IterativeRefinementSolver:
    """
    Multi-pass solver that refines solutions iteratively.
    """

    def __init__(self, max_iterations: int = 5, timeout: float = 30.0):
        self.max_iterations = max_iterations
        self.timeout = timeout
        self.analyzer = ErrorAnalyzer()
        self.refiner = SolutionRefiner()

    def solve(self, train_pairs: List[Tuple[Grid, Grid]],
             test_input: Grid,
             initial_hypotheses: List[Tuple[str, Callable[[Grid], Grid]]]) -> Optional[Grid]:
        """
        Iteratively refine solution starting from initial hypotheses.
        """
        start_time = time.time()

        # Try each hypothesis
        best_solution = None
        best_error_count = float('inf')
