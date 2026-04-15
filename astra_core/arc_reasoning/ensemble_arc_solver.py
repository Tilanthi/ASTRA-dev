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
Ensemble ARC Solver - Combines multiple approaches for better coverage.
Uses lenient acceptance to allow more transformations to be tried.
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import copy

# Import geometric transformations
from .improved_solver import (
    rotate_90, rotate_180, rotate_270,
    reflect_h, reflect_v, transpose,
    crop, pad, subsample,
    learn_color_mapping,
    apply_color_map,
)


# ============================================================================
# Transformation Functions
# ============================================================================

class TransformationFunction:
    """A transformation function with metadata."""

    def __init__(self, name: str, func: callable, confidence: float):
        self.name = name
        self.func = func
        self.confidence = confidence

    def apply(self, grid):
        return self.func(grid)


# ============================================================================
# Comprehensive Transformation Library
# ============================================================================

TRANSFORMATION_LIBRARY = [
    # Geometric transformations
    TransformationFunction("identity", lambda g: [row[:] for row in g], 0.5),
    TransformationFunction("rotate_90", rotate_90, 0.9),
    TransformationFunction("rotate_180", rotate_180, 0.9),
    TransformationFunction("rotate_270", rotate_270, 0.9),
    TransformationFunction("reflect_h", reflect_h, 0.9),
    TransformationFunction("reflect_v", reflect_v, 0.9),
    TransformationFunction("transpose", transpose, 0.9),

    # Crop operations (common sizes)
    TransformationFunction("crop_1", lambda g: crop(g, 1, 1, 1, 1) if len(g) > 2 and len(g[0]) > 2 else g, 0.7),
    TransformationFunction("crop_2", lambda g: crop(g, 2, 2, 2, 2) if len(g) > 4 and len(g[0]) > 4 else g, 0.7),
]


# ============================================================================
# Ensemble Solver
# ============================================================================

@dataclass
class SolverPrediction:
    """A prediction from a solver with confidence."""
    prediction: Optional[List[List[int]]]
    confidence: float
    solver_name: str
    explanation: str


class EnsembleARC_Solver:
    """
    Ensemble solver that tries multiple approaches.
    Lenient acceptance allows more transformations to be attempted.
    """

    def __init__(self):
        self.stats = {
            'total_attempts': 0,
            'predictions_made': 0,
            'solved': 0,
            'best_method_used': defaultdict(int),
        }

    def solve(
        self,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]],
        test_input: List[List[int]]
    ) -> Optional[List[List[int]]]:
        """Solve using ensemble of approaches."""
        self.stats['total_attempts'] += 1

        predictions = []

        # 1. Try exact geometric transformations
        predictions.extend(self._try_geometric_transforms(train_inputs, train_outputs, test_input))

        # 2. Try color mapping
        predictions.extend(self._try_color_mapping(train_inputs, train_outputs, test_input))

        # 3. Try library transformations
        predictions.extend(self._try_library_transforms(train_inputs, train_outputs, test_input))

        # 4. Try composition (transform + color map)
        predictions.extend(self._try_composition(train_inputs, train_outputs, test_input))

        # Select best prediction
        if not predictions:
            return None

        # Sort by confidence
        predictions.sort(key=lambda p: p.confidence, reverse=True)

        best = predictions[0]
        self.stats['predictions_made'] += 1
        self.stats['best_method_used'][best.solver_name] += 1

        return best.prediction

    def _try_geometric_transforms(
        self,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]],
        test_input: List[List[int]]
    ) -> List[SolverPrediction]:
        """Try exact geometric transformations."""
        predictions = []

        transforms = [
            ("identity", lambda g: g),
            ("rotate_90", rotate_90),
            ("rotate_180", rotate_180),
            ("rotate_270", rotate_270),
            ("reflect_h", reflect_h),
            ("reflect_v", reflect_v),
            ("transpose", transpose),
        ]

        for name, func in transforms:
            # Check if it works on all training pairs
            matches = 0
            for inp, out in zip(train_inputs, train_outputs):
                result = func(inp)
                if result == out:
                    matches += 1

            if matches == len(train_inputs):
                prediction = func(test_input)
                predictions.append(SolverPrediction(
                    prediction=prediction,
                    confidence=0.95,
                    solver_name=f"geometric_{name}",
                    explanation=f"Exact {name} transformation"
                ))

        return predictions

    def _try_color_mapping(
        self,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]],
        test_input: List[List[int]]
    ) -> List[SolverPrediction]:
        """Try color mapping transformations."""
        predictions = []

        color_map = learn_color_mapping(train_inputs, train_outputs)

        if color_map:
            prediction = apply_color_map(test_input, color_map)
            predictions.append(SolverPrediction(
                prediction=prediction,
                confidence=0.85,
                solver_name="color_map",
                explanation=f"Color mapping {color_map}"
            ))

        return predictions

    def _try_library_transforms(
        self,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]],
        test_input: List[List[int]]
    ) -> List[SolverPrediction]:
        """Try transformations from library."""
        predictions = []

        for trans in TRANSFORMATION_LIBRARY:
            # Test on first training pair
            result = trans.apply(train_inputs[0])
            if result == train_outputs[0]:
                # Verify on other pairs
                verified = True
                for inp, out in zip(train_inputs[1:], train_outputs[1:]):
                    if trans.apply(inp) != out:
                        verified = False
                        break

                if verified:
                    predictions.append(SolverPrediction(
                        prediction=trans.apply(test_input),
                        confidence=trans.confidence,
                        solver_name=f"library_{trans.name}",
                        explanation=f"Library transformation: {trans.name}"
                    ))

        return predictions

    def _try_composition(
        self,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]],
        test_input: List[List[int]]
    ) -> List[SolverPrediction]:
        """Try composition of transformation + color mapping."""
        predictions = []

        # Get color map
        color_map = learn_color_mapping(train_inputs, train_outputs)

        if not color_map:
            return predictions

        # Try applying geometric transform first, then color map
        transforms = [
            ("identity", lambda g: g),
            ("rotate_90", rotate_90),
            ("rotate_180", rotate_180),
            ("rotate_270", rotate_270),
            ("reflect_h", reflect_h),
            ("reflect_v", reflect_v),
            ("transpose", transpose),
        ]

        for trans_name, trans_func in transforms:
            # Test if trans_func + color_map works on training pairs
            matches = 0
            for inp, out in zip(train_inputs, train_outputs):
                transformed = trans_func(inp)
                colored = apply_color_map(transformed, color_map)
                if colored == out:
                    matches += 1

            if matches == len(train_inputs):
                # Apply composition to test input
                prediction = apply_color_map(trans_func(test_input), color_map)
                predictions.append(SolverPrediction(
                    prediction=prediction,
                    confidence=0.88,
                    solver_name=f"composed_{trans_name}_color",
                    explanation=f"{trans_name} + color mapping {color_map}"
                ))

        return predictions


__all__ = [
    'EnsembleARC_Solver',
    'SolverPrediction',
    'TRANSFORMATION_LIBRARY',
]



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """Detect patterns using autocorrelation analysis."""
    import numpy as np
    if max_lag is None:
        max_lag = len(data) // 4
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]
    return {'autocorrelation': autocorr[:max_lag], 'peaks': []}



# Utility: Computation Logging
def log_computation(*args, **kwargs):
    """Utility function for log_computation."""
    return None



def utility_function_12(*args, **kwargs):
    """Utility function 12."""
    return None



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """Detect patterns using autocorrelation analysis."""
    import numpy as np
    if max_lag is None:
        max_lag = len(data) // 4
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]
    return {'autocorrelation': autocorr[:max_lag], 'peaks': []}


