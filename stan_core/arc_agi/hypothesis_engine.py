#!/usr/bin/env python3
"""
Hypothesis Generation Engine for ARC-AGI

Generates and tests transformation hypotheses from training examples.
Uses a program synthesis approach with compositional primitives.
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
import itertools

from .grid_dsl import Grid, GridObject, BoundingBox, empty_grid


class TransformationType(Enum):
    """Categories of transformations"""
    IDENTITY = auto()
    COLOR = auto()
    GEOMETRIC = auto()
    SCALING = auto()
    OBJECT_MANIPULATION = auto()
    PATTERN = auto()
    COMPOSITIONAL = auto()
    CONDITIONAL = auto()


@dataclass
class TransformationHypothesis:
    """A hypothesis about the transformation rule"""
    name: str
    transform_type: TransformationType
    apply_fn: Callable[[Grid], Grid]
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    description: str = ""

    def apply(self, grid: Grid) -> Grid:
        return self.apply_fn(grid)

    def __repr__(self):
        return f"Hypothesis({self.name}, conf={self.confidence:.2f})"


class HypothesisGenerator:
    """
    Generates transformation hypotheses from input-output pairs.
    """

    def __init__(self):
        self.generators = [
            self._gen_identity,
            self._gen_color_mappings,
            self._gen_single_color_replace,
            self._gen_geometric_transforms,
            self._gen_scaling_transforms,
            self._gen_tiling_transforms,
            self._gen_crop_transforms,
            self._gen_object_operations,
            self._gen_fill_operations,
            self._gen_overlay_operations,
            self._gen_pattern_completion,
            self._gen_conditional_transforms,
        ]

    def generate(self, train_pairs: List[Tuple[Grid, Grid]]) -> List[TransformationHypothesis]:
        """Generate all possible hypotheses from training pairs"""
        all_hypotheses = []

        for generator in self.generators:
            try:
                hypotheses = generator(train_pairs)
                all_hypotheses.extend(hypotheses)
            except Exception:
                continue

        # Score and rank hypotheses
        scored = self._score_hypotheses(all_hypotheses, train_pairs)
        return sorted(scored, key=lambda h: -h.confidence)

    def _score_hypotheses(self, hypotheses: List[TransformationHypothesis],
                         train_pairs: List[Tuple[Grid, Grid]]) -> List[TransformationHypothesis]:
        """Score hypotheses by how many training pairs they correctly predict"""
        for h in hypotheses:
            correct = 0
            for inp, out in train_pairs:
                try:
                    predicted = h.apply(inp)
                    if predicted == out:
                        correct += 1
                except Exception:
                    pass
            h.confidence = correct / len(train_pairs) if train_pairs else 0.0
        return hypotheses

    # ========== Identity ==========

    def _gen_identity(self, train_pairs: List[Tuple[Grid, Grid]]) -> List[TransformationHypothesis]:
        """Check if transformation is identity"""
        return [TransformationHypothesis(
            name="identity",
            transform_type=TransformationType.IDENTITY,
            apply_fn=lambda g: g.copy(),
            description="No transformation"
        )]

    # ========== Color Operations ==========

    def _gen_color_mappings(self, train_pairs: List[Tuple[Grid, Grid]]) -> List[TransformationHypothesis]:
        """Generate color mapping hypotheses"""
        hypotheses = []

        # Learn color mapping from all pairs
        color_map = {}
        consistent = True

        for inp, out in train_pairs:
            if inp.shape != out.shape:
                consistent = False
                break

            for r in range(inp.height):
                for c in range(inp.width):
                    in_color = inp[r, c]
                    out_color = out[r, c]
                    if in_color in color_map:
                        if color_map[in_color] != out_color:
                            consistent = False
                            break
                    else:
                        color_map[in_color] = out_color

        if consistent and color_map:
            def apply_map(g: Grid, cm=color_map) -> Grid:
                return g.apply_color_map(cm)

            hypotheses.append(TransformationHypothesis(
                name="color_map",
                transform_type=TransformationType.COLOR,
                apply_fn=apply_map,
                params={'color_map': color_map},
                description=f"Color mapping: {color_map}"
            ))

        return hypotheses

    def _gen_single_color_replace(self, train_pairs: List[Tuple[Grid, Grid]]) -> List[TransformationHypothesis]:
        """Generate single color replacement hypotheses"""
        hypotheses = []

        # Find consistent single color changes
        changes = set()
        for inp, out in train_pairs:
            if inp.shape != out.shape:
                continue

            for r in range(inp.height):
                for c in range(inp.width):
                    if inp[r, c] != out[r, c]:
                        changes.add((inp[r, c], out[r, c]))

        for old_color, new_color in changes:
            def apply_replace(g: Grid, oc=old_color, nc=new_color) -> Grid:
                return g.replace_color(oc, nc)

            hypotheses.append(TransformationHypothesis(
                name=f"replace_{old_color}_with_{new_color}",
                transform_type=TransformationType.COLOR,
                apply_fn=apply_replace,
                params={'old_color': old_color, 'new_color': new_color},
                description=f"Replace color {old_color} with {new_color}"
            ))

        return hypotheses

    # ========== Geometric Transforms ==========

    def _gen_geometric_transforms(self, train_pairs: List[Tuple[Grid, Grid]]) -> List[TransformationHypothesis]:
        """Generate geometric transformation hypotheses"""
        hypotheses = []

        transforms = [
            ("rotate_90", lambda g: g.rotate_90()),
            ("rotate_180", lambda g: g.rotate_180()),
            ("rotate_270", lambda g: g.rotate_270()),
            ("flip_horizontal", lambda g: g.flip_horizontal()),
            ("flip_vertical", lambda g: g.flip_vertical()),
            ("transpose", lambda g: g.transpose()),
        ]

        for name, fn in transforms:
            hypotheses.append(TransformationHypothesis(
                name=name,
                transform_type=TransformationType.GEOMETRIC,
                apply_fn=fn,
                description=f"Geometric: {name}"
            ))

        return hypotheses

    # ========== Scaling ==========

    def _gen_scaling_transforms(self, train_pairs: List[Tuple[Grid, Grid]]) -> List[TransformationHypothesis]:
        """Generate scaling transformation hypotheses"""
        hypotheses = []

        for inp, out in train_pairs:
            if inp.height > 0 and inp.width > 0:
                if out.height % inp.height == 0 and out.width % inp.width == 0:
                    scale_h = out.height // inp.height
                    scale_w = out.width // inp.width

                    def apply_scale(g: Grid, sh=scale_h, sw=scale_w) -> Grid:
                        return g.scale(sh, sw)

                    hypotheses.append(TransformationHypothesis(
                        name=f"scale_{scale_h}x{scale_w}",
                        transform_type=TransformationType.SCALING,
                        apply_fn=apply_scale,
                        params={'scale_h': scale_h, 'scale_w': scale_w},
                        description=f"Scale by {scale_h}x{scale_w}"
                    ))
            break  # Only need one pair to detect scaling

        return hypotheses

    # ========== Tiling ==========

    def _gen_tiling_transforms(self, train_pairs: List[Tuple[Grid, Grid]]) -> List[TransformationHypothesis]:
        """Generate tiling transformation hypotheses"""
        hypotheses = []

        for inp, out in train_pairs:
            if inp.height > 0 and inp.width > 0:
                if out.height % inp.height == 0 and out.width % inp.width == 0:
                    tile_h = out.height // inp.height
                    tile_w = out.width // inp.width

                    # Simple tiling
                    def apply_tile(g: Grid, th=tile_h, tw=tile_w) -> Grid:
                        return g.tile(th, tw)

                    hypotheses.append(TransformationHypothesis(
                        name=f"tile_{tile_h}x{tile_w}",
                        transform_type=TransformationType.SCALING,
                        apply_fn=apply_tile,
                        params={'tile_h': tile_h, 'tile_w': tile_w},
                        description=f"Tile {tile_h}x{tile_w}"
                    ))

                    # Tiling with alternation (for task 00576224)
                    def apply_tile_alternating(g: Grid, th=tile_h, tw=tile_w) -> Grid:
                        result = empty_grid(g.height * th, g.width * tw)
                        for tr in range(th):
                            for tc in range(tw):
                                tile_grid = g if (tr + tc) % 2 == 0 else g.transpose()
                                for r in range(g.height):
                                    for c in range(g.width):
                                        result[tr * g.height + r, tc * g.width + c] = tile_grid[r, c]
                        return result

                    hypotheses.append(TransformationHypothesis(
                        name=f"tile_alternating_{tile_h}x{tile_w}",
                        transform_type=TransformationType.SCALING,
                        apply_fn=apply_tile_alternating,
                        params={'tile_h': tile_h, 'tile_w': tile_w},
                        description=f"Tile {tile_h}x{tile_w} with alternating transpose"
                    ))

                    # Tiling with row alternation
                    def apply_tile_row_alt(g: Grid, th=tile_h, tw=tile_w) -> Grid:
                        result = empty_grid(g.height * th, g.width * tw)
