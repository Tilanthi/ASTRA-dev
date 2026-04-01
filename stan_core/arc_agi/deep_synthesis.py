#!/usr/bin/env python3
"""
Deep Program Synthesis for ARC-AGI

Implements program synthesis with:
- Depth-5 compositional search
- A* search with heuristic scoring
- Memoization for efficiency
- Typed DSL for constraint propagation
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Callable, Any, FrozenSet
from dataclasses import dataclass, field
from collections import defaultdict
import heapq
import hashlib
import time

from .grid_dsl import Grid, GridObject, empty_grid
from .pattern_library import PatternPrimitives


@dataclass
class ProgramNode:
    """Node in program search tree"""
    program: List[Callable[[Grid], Grid]]
    program_names: List[str]
    score: float
    depth: int
    g_score: float  # Cost so far
    h_score: float  # Heuristic estimate

    def __lt__(self, other):
        return (self.g_score + self.h_score) < (other.g_score + other.h_score)

    @property
    def hash_key(self) -> str:
        return "|".join(self.program_names)


class TypedPrimitive:
    """A primitive operation with input/output type constraints"""

    def __init__(self, name: str, fn: Callable[[Grid], Grid],
                 input_constraints: Dict[str, Any] = None,
                 output_effects: Dict[str, Any] = None):
        self.name = name
        self.fn = fn
        self.input_constraints = input_constraints or {}
        self.output_effects = output_effects or {}

    def can_apply(self, grid_props: Dict[str, Any]) -> bool:
        """Check if primitive can be applied given grid properties"""
        for key, constraint in self.input_constraints.items():
            if key not in grid_props:
                continue
            if callable(constraint):
                if not constraint(grid_props[key]):
                    return False
            elif grid_props[key] != constraint:
                return False
        return True

    def get_output_props(self, input_props: Dict[str, Any]) -> Dict[str, Any]:
        """Compute output properties based on input and effects"""
        output = input_props.copy()
        for key, effect in self.output_effects.items():
            if callable(effect):
                output[key] = effect(input_props)
            else:
                output[key] = effect
        return output


class DeepProgramSynthesizer:
    """
    Deep program synthesis with A* search and type-guided pruning.
    """

    def __init__(self, max_depth: int = 5, timeout_seconds: float = 30.0):
        self.max_depth = max_depth
        self.timeout = timeout_seconds
        self.primitives = self._build_typed_primitives()
        self.cache = {}  # Memoization cache

    def _build_typed_primitives(self) -> List[TypedPrimitive]:
        """Build library of typed primitive operations"""
        return [
            # Identity
            TypedPrimitive("identity", lambda g: g.copy()),

            # Rotations
            TypedPrimitive("rotate_90", lambda g: g.rotate_90(),
                          output_effects={'height': lambda p: p.get('width', 0),
                                        'width': lambda p: p.get('height', 0)}),
            TypedPrimitive("rotate_180", lambda g: g.rotate_180()),
            TypedPrimitive("rotate_270", lambda g: g.rotate_270(),
                          output_effects={'height': lambda p: p.get('width', 0),
                                        'width': lambda p: p.get('height', 0)}),

            # Flips
            TypedPrimitive("flip_h", lambda g: g.flip_horizontal()),
            TypedPrimitive("flip_v", lambda g: g.flip_vertical()),
            TypedPrimitive("transpose", lambda g: g.transpose(),
                          output_effects={'height': lambda p: p.get('width', 0),
                                        'width': lambda p: p.get('height', 0)}),

            # Cropping
            TypedPrimitive("crop", lambda g: g.crop_to_content()),

            # Scaling
            TypedPrimitive("scale_2x", lambda g: g.scale(2, 2),
                          output_effects={'height': lambda p: p.get('height', 0) * 2,
                                        'width': lambda p: p.get('width', 0) * 2}),
            TypedPrimitive("scale_3x", lambda g: g.scale(3, 3),
                          output_effects={'height': lambda p: p.get('height', 0) * 3,
                                        'width': lambda p: p.get('width', 0) * 3}),

            # Tiling
            TypedPrimitive("tile_2x2", lambda g: g.tile(2, 2),
                          output_effects={'height': lambda p: p.get('height', 0) * 2,
                                        'width': lambda p: p.get('width', 0) * 2}),
            TypedPrimitive("tile_3x3", lambda g: g.tile(3, 3),
                          output_effects={'height': lambda p: p.get('height', 0) * 3,
                                        'width': lambda p: p.get('width', 0) * 3}),
            TypedPrimitive("tile_2x1", lambda g: g.tile(2, 1),
                          output_effects={'height': lambda p: p.get('height', 0) * 2}),
            TypedPrimitive("tile_1x2", lambda g: g.tile(1, 2),
                          output_effects={'width': lambda p: p.get('width', 0) * 2}),
            TypedPrimitive("tile_3x1", lambda g: g.tile(3, 1),
                          output_effects={'height': lambda p: p.get('height', 0) * 3}),
            TypedPrimitive("tile_1x3", lambda g: g.tile(1, 3),
                          output_effects={'width': lambda p: p.get('width', 0) * 3}),

            # Gravity
            TypedPrimitive("gravity_down", lambda g: PatternPrimitives.gravity_drop(g, 'down')),
            TypedPrimitive("gravity_up", lambda g: PatternPrimitives.gravity_drop(g, 'up')),
            TypedPrimitive("gravity_left", lambda g: PatternPrimitives.gravity_drop(g, 'left')),
            TypedPrimitive("gravity_right", lambda g: PatternPrimitives.gravity_drop(g, 'right')),

            # Border operations
            TypedPrimitive("remove_border", lambda g: g.crop(1, 1, g.height - 2, g.width - 2)
                          if g.height > 2 and g.width > 2 else g.copy(),
                          input_constraints={'height': lambda h: h > 2, 'width': lambda w: w > 2},
                          output_effects={'height': lambda p: max(1, p.get('height', 0) - 2),
                                        'width': lambda p: max(1, p.get('width', 0) - 2)}),

            # Color operations
            TypedPrimitive("replace_0_with_1", lambda g: g.replace_color(0, 1)),
            TypedPrimitive("replace_1_with_0", lambda g: g.replace_color(1, 0)),
            TypedPrimitive("replace_1_with_2", lambda g: g.replace_color(1, 2)),
            TypedPrimitive("replace_2_with_1", lambda g: g.replace_color(2, 1)),

            # Extraction
            TypedPrimitive("extract_top_half", lambda g: g.crop(0, 0, g.height // 2 - 1, g.width - 1)
                          if g.height >= 2 else g.copy(),
                          input_constraints={'height': lambda h: h >= 2},
                          output_effects={'height': lambda p: p.get('height', 0) // 2}),
            TypedPrimitive("extract_bottom_half", lambda g: g.crop(g.height // 2, 0, g.height - 1, g.width - 1)
                          if g.height >= 2 else g.copy(),
                          input_constraints={'height': lambda h: h >= 2},
                          output_effects={'height': lambda p: p.get('height', 0) // 2}),
            TypedPrimitive("extract_left_half", lambda g: g.crop(0, 0, g.height - 1, g.width // 2 - 1)
                          if g.width >= 2 else g.copy(),
                          input_constraints={'width': lambda w: w >= 2},
                          output_effects={'width': lambda p: p.get('width', 0) // 2}),
            TypedPrimitive("extract_right_half", lambda g: g.crop(0, g.width // 2, g.height - 1, g.width - 1)
                          if g.width >= 2 else g.copy(),
                          input_constraints={'width': lambda w: w >= 2},
                          output_effects={'width': lambda p: p.get('width', 0) // 2}),

            # Symmetry completion
            TypedPrimitive("mirror_h", self._mirror_horizontal),
            TypedPrimitive("mirror_v", self._mirror_vertical),
        ]

    def _mirror_horizontal(self, g: Grid) -> Grid:
        """Mirror left half to right"""
        result = g.copy()
        mid = g.width // 2
        for r in range(g.height):
            for c in range(mid):
                result[r, g.width - 1 - c] = g[r, c]
        return result

    def _mirror_vertical(self, g: Grid) -> Grid:
        """Mirror top half to bottom"""
        result = g.copy()
        mid = g.height // 2
        for r in range(mid):
            for c in range(g.width):
                result[g.height - 1 - r, c] = g[r, c]
        return result

    def _get_grid_props(self, g: Grid) -> Dict[str, Any]:
        """Extract properties of a grid for type checking"""
        return {
            'height': g.height,
            'width': g.width,
            'num_colors': len(g.get_colors()),
            'num_objects': len(g.find_objects()),
            'has_symmetry': len(g.detect_symmetry()) > 0,
        }

    def _compute_heuristic(self, current: Grid, target: Grid) -> float:
        """Heuristic for A* search - estimate cost to reach target"""
        # Size difference
        size_diff = abs(current.height - target.height) + abs(current.width - target.width)

        # Color difference
        curr_colors = current.get_colors()
        targ_colors = target.get_colors()
        color_diff = len(curr_colors.symmetric_difference(targ_colors))

        # Pixel difference (if same size)
        pixel_diff = 0
        if current.height == target.height and current.width == target.width:
            for r in range(current.height):
                for c in range(current.width):
                    if current[r, c] != target[r, c]:
                        pixel_diff += 1
            pixel_diff = pixel_diff / (current.height * current.width)

        return size_diff * 0.5 + color_diff * 0.3 + pixel_diff * 0.2

    def _get_cache_key(self, g: Grid) -> str:
        """Get hash key for grid caching"""
        return hashlib.md5(g.data.tobytes()).hexdigest()

    def synthesize(self, train_pairs: List[Tuple[Grid, Grid]]) -> Optional[List[Callable[[Grid], Grid]]]:
        """
        Synthesize a program using A* search with heuristics.
        """
        start_time = time.time()

        if not train_pairs:
            return None

        # Initialize with empty program
        inp, out = train_pairs[0]
        initial_props = self._get_grid_props(inp)
        h_score = self._compute_heuristic(inp, out)

        initial_node = ProgramNode(
            program=[],
            program_names=[],
            score=0.0,
            depth=0,
            g_score=0.0,
            h_score=h_score
        )

        # Priority queue for A* search
        open_set = [initial_node]
        visited = set()
        best_solution = None
        best_score = float('inf')

        while open_set and (time.time() - start_time) < self.timeout:
            current = heapq.heappop(open_set)

            # Check if already visited
            if current.hash_key in visited:
                continue
            visited.add(current.hash_key)

            # Test current program
