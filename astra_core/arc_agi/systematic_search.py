#!/usr/bin/env python3
"""
Systematic Search Engine for ARC-AGI

Implements program synthesis via systematic search with:
- Beam search for hypothesis exploration
- Constraint propagation for pruning
- Analogical transfer from solved tasks
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
import heapq
import time

from .grid_dsl import Grid, GridObject, BoundingBox, empty_grid
from .hypothesis_engine import (
    TransformationHypothesis, TransformationType,
    HypothesisGenerator, HypothesisTester
)
from .pattern_library import (
    PatternDetector, PatternPrimitives, ObjectRelationships,
    CompositeTransform
)


@dataclass
class SearchState:
    """State in the search space"""
    hypothesis: TransformationHypothesis
    score: float
    depth: int
    parent: Optional['SearchState'] = None

    def __lt__(self, other):
        return self.score > other.score  # Max heap


@dataclass
class TaskAnalysis:
    """Analysis of a task's structure"""
    input_size_changes: List[Tuple[int, int, int, int]]  # (in_h, in_w, out_h, out_w)
    color_changes: Dict[int, Set[int]]  # input_color -> possible output colors
    object_count_changes: List[Tuple[int, int]]  # (in_count, out_count)
    detected_patterns: List[str]
    symmetry_info: Dict[str, bool]
    periodicity: Optional[Tuple[int, int]]


class ConstraintPropagator:
    """
    Propagates constraints from training examples to prune search space.
    """

    def analyze_task(self, train_pairs: List[Tuple[Grid, Grid]]) -> TaskAnalysis:
        """Analyze task to extract constraints"""
        size_changes = []
        color_changes = defaultdict(set)
        object_count_changes = []
        detected_patterns = []
        symmetry_info = {}
        periodicity = None

        for inp, out in train_pairs:
            # Size changes
            size_changes.append((inp.height, inp.width, out.height, out.width))

            # Color changes
            for r in range(min(inp.height, out.height)):
                for c in range(min(inp.width, out.width)):
                    color_changes[inp[r, c]].add(out[r, c])

            # Object count
            in_objs = inp.find_objects()
            out_objs = out.find_objects()
            object_count_changes.append((len(in_objs), len(out_objs)))

            # Patterns
            detector = PatternDetector()
            in_patterns = detector.detect_all(inp)
            for p in in_patterns:
                detected_patterns.append(p.pattern_type.name)

            # Symmetry
            in_sym = inp.detect_symmetry()
            out_sym = out.detect_symmetry()
            symmetry_info['input_has_symmetry'] = len(in_sym) > 0
            symmetry_info['output_has_symmetry'] = len(out_sym) > 0

            # Periodicity
            if periodicity is None:
                periodicity = inp.detect_periodicity()

        return TaskAnalysis(
            input_size_changes=size_changes,
            color_changes=dict(color_changes),
            object_count_changes=object_count_changes,
            detected_patterns=list(set(detected_patterns)),
            symmetry_info=symmetry_info,
            periodicity=periodicity
        )

    def filter_hypotheses(self, hypotheses: List[TransformationHypothesis],
                         analysis: TaskAnalysis) -> List[TransformationHypothesis]:
        """Filter hypotheses that are inconsistent with analysis"""
        filtered = []

        for h in hypotheses:
            keep = True

            # Check if size change pattern matches
            if h.transform_type == TransformationType.SCALING:
                expected_ratios = set()
                for in_h, in_w, out_h, out_w in analysis.input_size_changes:
                    if in_h > 0 and in_w > 0:
                        expected_ratios.add((out_h / in_h, out_w / in_w))

                if len(expected_ratios) > 1:
                    # Inconsistent size changes
                    keep = False

            # Check if color mapping is consistent
            if h.transform_type == TransformationType.COLOR:
                color_map = h.params.get('color_map', {})
                for in_color, out_colors in analysis.color_changes.items():
                    if in_color in color_map:
                        if color_map[in_color] not in out_colors:
                            keep = False
                            break

            if keep:
                filtered.append(h)

        return filtered


class ProgramSynthesizer:
    """
    Synthesizes transformation programs from primitives.
    Uses a DSL of grid operations composed into programs.
    """

    def __init__(self):
        self.primitives = self._build_primitive_library()

    def _build_primitive_library(self) -> List[Callable[[Grid], Grid]]:
        """Build library of primitive operations"""
        return [
            # Identity and basic transforms
            lambda g: g.copy(),
            lambda g: g.rotate_90(),
            lambda g: g.rotate_180(),
            lambda g: g.rotate_270(),
            lambda g: g.flip_horizontal(),
            lambda g: g.flip_vertical(),
            lambda g: g.transpose(),

            # Cropping
            lambda g: g.crop_to_content(),

            # Scaling (common factors)
            lambda g: g.scale(2, 2),
            lambda g: g.scale(3, 3),

            # Tiling (common patterns)
            lambda g: g.tile(2, 2),
            lambda g: g.tile(3, 3),

            # Gravity operations
            lambda g: PatternPrimitives.gravity_drop(g, 'down'),
            lambda g: PatternPrimitives.gravity_drop(g, 'up'),
            lambda g: PatternPrimitives.gravity_drop(g, 'left'),
            lambda g: PatternPrimitives.gravity_drop(g, 'right'),
        ]

    def synthesize(self, train_pairs: List[Tuple[Grid, Grid]],
                  max_depth: int = 3) -> Optional[List[Callable[[Grid], Grid]]]:
        """
        Synthesize a program (sequence of primitives) that transforms
        inputs to outputs.
        """
        # Try single primitives first
        for prim in self.primitives:
            if self._test_program([prim], train_pairs):
                return [prim]

        # Try compositions of two primitives
        if max_depth >= 2:
            for p1 in self.primitives:
                for p2 in self.primitives:
                    if self._test_program([p1, p2], train_pairs):
                        return [p1, p2]

        # Try compositions of three primitives
        if max_depth >= 3:
            for p1 in self.primitives:
                for p2 in self.primitives:
                    for p3 in self.primitives:
                        if self._test_program([p1, p2, p3], train_pairs):
                            return [p1, p2, p3]

        return None
