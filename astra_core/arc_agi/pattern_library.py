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
Compositional Pattern Library for ARC-AGI

Contains reusable pattern primitives that can be composed to solve complex tasks.
Implements both analysis (pattern detection) and synthesis (pattern application).
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
import itertools

from .grid_dsl import Grid, GridObject, BoundingBox, empty_grid


# Performance optimization for pattern operations
import functools

@functools.lru_cache(maxsize=256)
def _cached_pattern_signature(data_hash):
    """Cache pattern signatures to avoid recomputation."""
    return data_hash

def vectorized_pattern_match(patterns, data):
    """Vectorized pattern matching for better performance."""
    import numpy as np
    patterns_arr = np.array(patterns)
    data_arr = np.array(data)
    correlations = np.corrcoef(patterns_arr, data_arr)
    return correlations



class PatternType(Enum):
    """Types of patterns that can be detected"""
    SOLID_RECTANGLE = auto()
    HOLLOW_RECTANGLE = auto()
    LINE_HORIZONTAL = auto()
    LINE_VERTICAL = auto()
    LINE_DIAGONAL = auto()
    CROSS = auto()
    PLUS = auto()
    L_SHAPE = auto()
    T_SHAPE = auto()
    GRID_LINES = auto()
    CHECKERBOARD = auto()
    SPIRAL = auto()
    FRAME = auto()
    SYMMETRIC = auto()
    REPEATING = auto()


@dataclass
class Pattern:
    """Detected pattern with metadata"""
    pattern_type: PatternType
    bbox: BoundingBox
    color: int
    pixels: Set[Tuple[int, int]]
    attributes: Dict[str, Any] = field(default_factory=dict)


class PatternDetector:
    """Detects various patterns in grids"""

    def detect_all(self, grid: Grid, background: int = 0) -> List[Pattern]:
        """Detect all patterns in a grid"""
        patterns = []

        patterns.extend(self._detect_rectangles(grid, background))
        patterns.extend(self._detect_lines(grid, background))
        patterns.extend(self._detect_grid_structure(grid, background))
        patterns.extend(self._detect_symmetric_patterns(grid, background))

        return patterns

    def _detect_rectangles(self, grid: Grid, background: int) -> List[Pattern]:
        """Detect solid and hollow rectangles"""
        patterns = []
        objects = grid.find_objects(background)

        for obj in objects:
            bbox = obj.bbox

            # Check if solid rectangle
            is_solid = True
            for r in range(bbox.r1, bbox.r2 + 1):
                for c in range(bbox.c1, bbox.c2 + 1):
                    if (r, c) not in obj.pixels:
                        is_solid = False
                        break
                if not is_solid:
                    break

            if is_solid:
                patterns.append(Pattern(
                    pattern_type=PatternType.SOLID_RECTANGLE,
                    bbox=bbox,
                    color=obj.color,
                    pixels=obj.pixels,
                    attributes={'width': bbox.width, 'height': bbox.height}
                ))
            else:
                # Check if hollow rectangle (frame)
                is_hollow = True
                interior = set()
                for r in range(bbox.r1 + 1, bbox.r2):
                    for c in range(bbox.c1 + 1, bbox.c2):
                        if (r, c) in obj.pixels:
                            is_hollow = False
                            break
                        interior.add((r, c))
                    if not is_hollow:
                        break

                if is_hollow and bbox.width >= 3 and bbox.height >= 3:
                    patterns.append(Pattern(
                        pattern_type=PatternType.HOLLOW_RECTANGLE,
                        bbox=bbox,
                        color=obj.color,
                        pixels=obj.pixels,
                        attributes={
                            'width': bbox.width,
                            'height': bbox.height,
                            'interior': interior
                        }
                    ))

        return patterns

    def _detect_lines(self, grid: Grid, background: int) -> List[Pattern]:
        """Detect horizontal, vertical, and diagonal lines"""
        patterns = []

        # Horizontal lines
        for r in range(grid.height):
            c = 0
            while c < grid.width:
                if grid[r, c] != background:
                    color = grid[r, c]
                    start_c = c
                    while c < grid.width and grid[r, c] == color:
                        c += 1
                    end_c = c - 1

                    if end_c - start_c >= 2:  # At least 3 cells
                        pixels = {(r, ci) for ci in range(start_c, end_c + 1)}
                        patterns.append(Pattern(
                            pattern_type=PatternType.LINE_HORIZONTAL,
                            bbox=BoundingBox(r, start_c, r, end_c),
                            color=color,
                            pixels=pixels,
                            attributes={'length': end_c - start_c + 1}
                        ))
                else:
                    c += 1

        # Vertical lines
        for c in range(grid.width):
            r = 0
            while r < grid.height:
                if grid[r, c] != background:
                    color = grid[r, c]
                    start_r = r
                    while r < grid.height and grid[r, c] == color:
                        r += 1
                    end_r = r - 1

                    if end_r - start_r >= 2:
                        pixels = {(ri, c) for ri in range(start_r, end_r + 1)}
                        patterns.append(Pattern(
                            pattern_type=PatternType.LINE_VERTICAL,
                            bbox=BoundingBox(start_r, c, end_r, c),
                            color=color,
                            pixels=pixels,
                            attributes={'length': end_r - start_r + 1}
                        ))
                else:
                    r += 1

        return patterns

    def _detect_grid_structure(self, grid: Grid, background: int) -> List[Pattern]:
        """Detect grid/table structures with separating lines"""
        patterns = []

        # Find horizontal separating lines (full-width)
        h_separators = []
        for r in range(grid.height):
            row_colors = set(grid[r, c] for c in range(grid.width))
            non_bg = row_colors - {background}
            if len(non_bg) == 1 and all(grid[r, c] == list(non_bg)[0] for c in range(grid.width)):
                h_separators.append((r, list(non_bg)[0]))

        # Find vertical separating lines (full-height)
        v_separators = []
        for c in range(grid.width):
            col_colors = set(grid[r, c] for r in range(grid.height))
            non_bg = col_colors - {background}
            if len(non_bg) == 1 and all(grid[r, c] == list(non_bg)[0] for r in range(grid.height)):
                v_separators.append((c, list(non_bg)[0]))

        if h_separators or v_separators:
            patterns.append(Pattern(
                pattern_type=PatternType.GRID_LINES,
                bbox=BoundingBox(0, 0, grid.height - 1, grid.width - 1),
                color=h_separators[0][1] if h_separators else v_separators[0][1],
                pixels=set(),  # Complex to enumerate
                attributes={
                    'h_separators': h_separators,
                    'v_separators': v_separators,
                    'num_rows': len(h_separators) + 1,
                    'num_cols': len(v_separators) + 1
                }
            ))

        return patterns

    def _detect_symmetric_patterns(self, grid: Grid, background: int) -> List[Pattern]:
        """Detect symmetric patterns"""
        patterns = []
        symmetries = grid.detect_symmetry()

        if symmetries:
            patterns.append(Pattern(
                pattern_type=PatternType.SYMMETRIC,
                bbox=BoundingBox(0, 0, grid.height - 1, grid.width - 1),
                color=-1,  # Multiple colors
                pixels=set(),
                attributes={'symmetries': symmetries}
            ))

        return patterns


class PatternPrimitives:
    """
    Library of primitive transformation patterns that can be composed.
    """

    @staticmethod
    def extend_pattern_vertically(grid: Grid, extension_rows: int,
                                  color_map: Dict[int, int] = None) -> Grid:
        """Extend a pattern vertically, optionally with color mapping"""
        new_height = grid.height + extension_rows
        result = empty_grid(new_height, grid.width)

        for r in range(grid.height):
            for c in range(grid.width):
                result[r, c] = grid[r, c]

        # Repeat pattern for extension
        for r in range(extension_rows):
            src_r = r % grid.height
            for c in range(grid.width):
                val = grid[src_r, c]
                if color_map and val in color_map:
                    val = color_map[val]
                result[grid.height + r, c] = val

        return result

    @staticmethod
    def gravity_drop(grid: Grid, direction: str = 'down',
                    background: int = 0) -> Grid:
        """Apply gravity to objects in specified direction"""
        result = empty_grid(grid.height, grid.width, background)

        if direction == 'down':
            for c in range(grid.width):
                non_bg = [(r, grid[r, c]) for r in range(grid.height)
                         if grid[r, c] != background]
                for i, (_, val) in enumerate(reversed(non_bg)):
                    result[grid.height - 1 - i, c] = val

        elif direction == 'up':
            for c in range(grid.width):
                non_bg = [(r, grid[r, c]) for r in range(grid.height)
                         if grid[r, c] != background]
                for i, (_, val) in enumerate(non_bg):
                    result[i, c] = val

        elif direction == 'left':
            for r in range(grid.height):
                non_bg = [(c, grid[r, c]) for c in range(grid.width)
                         if grid[r, c] != background]
                for i, (_, val) in enumerate(non_bg):
                    result[r, i] = val

        elif direction == 'right':
            for r in range(grid.height):
                non_bg = [(c, grid[r, c]) for c in range(grid.width)
                         if grid[r, c] != background]
                for i, (_, val) in enumerate(reversed(non_bg)):
                    result[r, grid.width - 1 - i] = val

        return result

    @staticmethod
    def mirror_complete(grid: Grid, axis: str = 'horizontal') -> Grid:
        """Complete a pattern by mirroring"""
        if axis == 'horizontal':
            # Mirror left half to right
            mid = grid.width // 2
            result = grid.copy()
            for r in range(grid.height):
                for c in range(mid):
                    result[r, grid.width - 1 - c] = grid[r, c]
            return result

        elif axis == 'vertical':
            # Mirror top half to bottom
            mid = grid.height // 2
            result = grid.copy()
            for r in range(mid):
                for c in range(grid.width):
                    result[grid.height - 1 - r, c] = grid[r, c]
            return result

        return grid.copy()

    @staticmethod
    def connect_same_color(grid: Grid, color: int = None,
                          background: int = 0) -> Grid:
        """Connect objects of the same color with lines"""
        result = grid.copy()
        objects = grid.find_objects(background)

        if color is not None:
            objects = [o for o in objects if o.color == color]

        # Group by color
        by_color = defaultdict(list)
        for obj in objects:
            by_color[obj.color].append(obj)

        for c, objs in by_color.items():
            if len(objs) >= 2:
                # Connect centers
                centers = [obj.bbox.center for obj in objs]
                for i in range(len(centers) - 1):
                    r1, c1 = int(centers[i][0]), int(centers[i][1])
                    r2, c2 = int(centers[i+1][0]), int(centers[i+1][1])
                    result = result.draw_line(r1, c1, r2, c2, c)

        return result

    @staticmethod
    def scale_by_count(grid: Grid, background: int = 0) -> Grid:
        """Scale output based on number of objects"""
        objects = grid.find_objects(background)
        count = len(objects)

        if count > 1:
            return grid.scale(count, count)
        return grid.copy()

    @staticmethod
    def extract_unique_pattern(grid: Grid, background: int = 0) -> Grid:
        """Extract the unique non-repeating part of a pattern"""
        h_period, v_period = grid.detect_periodicity()

        if h_period and v_period:
            return grid.crop(0, 0, h_period - 1, v_period - 1)
        elif h_period:
            return grid.crop(0, 0, h_period - 1, grid.width - 1)
        elif v_period:
            return grid.crop(0, 0, grid.height - 1, v_period - 1)

        return grid.copy()

    @staticmethod
    def complete_by_template(grid: Grid, template_positions: List[Tuple[int, int]],
                            templates: List[Grid]) -> Grid:
        """Complete grid by placing templates at specified positions"""
        result = grid.copy()

        for (r, c), template in zip(template_positions, templates):
            for tr in range(template.height):
                for tc in range(template.width):
                    if 0 <= r + tr < result.height and 0 <= c + tc < result.width:
                        if template[tr, tc] != 0:
                            result[r + tr, c + tc] = template[tr, tc]

        return result


class ObjectRelationships:
    """
    Analyzes and applies relationships between objects.
    """

    @staticmethod
    def find_spatial_relationships(objects: List[GridObject]) -> Dict[str, List[Tuple[int, int]]]:
        """Find spatial relationships between objects"""
        relationships = defaultdict(list)

        for i, obj1 in enumerate(objects):
            for j, obj2 in enumerate(objects):
                if i >= j:
                    continue

                c1 = obj1.bbox.center
                c2 = obj2.bbox.center

                # Determine relative position
                if abs(c1[0] - c2[0]) < 2:  # Same row
                    if c1[1] < c2[1]:
                        relationships['left_of'].append((i, j))
                        relationships['right_of'].append((j, i))
                    else:
                        relationships['left_of'].append((j, i))
                        relationships['right_of'].append((i, j))

                if abs(c1[1] - c2[1]) < 2:  # Same column
                    if c1[0] < c2[0]:
                        relationships['above'].append((i, j))
                        relationships['below'].append((j, i))
                    else:
                        relationships['above'].append((j, i))
                        relationships['below'].append((i, j))

                # Check for containment
                if (obj1.bbox.r1 <= obj2.bbox.r1 and obj1.bbox.r2 >= obj2.bbox.r2 and
                    obj1.bbox.c1 <= obj2.bbox.c1 and obj1.bbox.c2 >= obj2.bbox.c2):
                    relationships['contains'].append((i, j))
                elif (obj2.bbox.r1 <= obj1.bbox.r1 and obj2.bbox.r2 >= obj1.bbox.r2 and
                      obj2.bbox.c1 <= obj1.bbox.c1 and obj2.bbox.c2 >= obj1.bbox.c2):
                    relationships['contains'].append((j, i))

        return dict(relationships)

    @staticmethod
    def sort_objects_by_size(objects: List[GridObject],
                            descending: bool = True) -> List[GridObject]:
        """Sort objects by size"""
        return sorted(objects, key=lambda o: o.size, reverse=descending)

    @staticmethod
    def sort_objects_by_position(objects: List[GridObject],
                                primary: str = 'row') -> List[GridObject]:
        """Sort objects by position (row-major or column-major)"""
        if primary == 'row':
            return sorted(objects, key=lambda o: (o.bbox.r1, o.bbox.c1))
        else:
            return sorted(objects, key=lambda o: (o.bbox.c1, o.bbox.r1))

    @staticmethod
    def group_objects_by_color(objects: List[GridObject]) -> Dict[int, List[GridObject]]:
        """Group objects by color"""
        groups = defaultdict(list)
        for obj in objects:
            groups[obj.color].append(obj)
        return dict(groups)


class CompositeTransform:
    """
    Composes multiple transformations into a single operation.
    """

    def __init__(self):
        self.transforms: List[Callable[[Grid], Grid]] = []

    def add(self, transform: Callable[[Grid], Grid]) -> 'CompositeTransform':
        """Add a transformation to the sequence"""
        self.transforms.append(transform)
        return self

    def apply(self, grid: Grid) -> Grid:
        """Apply all transformations in sequence"""
        result = grid
        for transform in self.transforms:
            result = transform(result)
        return result

    @classmethod
    def from_sequence(cls, transforms: List[Callable[[Grid], Grid]]) -> 'CompositeTransform':
        """Create composite from list of transforms"""
        ct = cls()
        ct.transforms = transforms
        return ct



def generate_test_pattern(pattern_type: str = 'sine',
                        n_points: int = 1000,
                        noise_level: float = 0.1) -> np.ndarray:
    """
    Generate synthetic test pattern for validation.

    Args:
        pattern_type: Type of pattern ('sine', 'square', 'sawtooth')
        n_points: Number of data points
        noise_level: Amount of noise to add

    Returns:
        Test pattern data
    """
    x = np.linspace(0, 4 * np.pi, n_points)

    if pattern_type == 'sine':
        y = np.sin(x)
    elif pattern_type == 'square':
        y = np.sign(np.sin(x))
    elif pattern_type == 'sawtooth':
        y = 2 * (x / (2 * np.pi) - np.floor(0.5 + x / (2 * np.pi)))
    else:
        y = np.sin(x)

    # Add noise
    y += noise_level * np.random.randn(n_points)

    return y
