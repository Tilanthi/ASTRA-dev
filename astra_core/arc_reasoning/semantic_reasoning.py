#!/usr/bin/env python3
"""
STAN Semantic Object Reasoning Module

Advanced visual-abstract reasoning capabilities for ARC-AGI-2 tasks.
This module implements the core capabilities identified as needed to exceed 84.6% accuracy.

Capabilities:
1. Semantic Object Reasoning (86% of tasks)
2. Arithmetic Reasoning (51% of tasks)
3. Executive Function for strategy selection
4. Vision-Language Integration

This is a major architectural enhancement that goes beyond simple geometric
transformations to true semantic understanding of visual patterns.
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict, Counter
import copy


# ============================================================================
# Capability 1: Semantic Object Reasoning
# ============================================================================

class ObjectRelation(Enum):
    """Types of relationships between objects."""
    ADJACENT = auto()
    OVERLAPPING = auto()
    CONTAINING = auto()
    SEPARATED = auto()
    ALIGNED_H = auto()
    ALIGNED_V = auto()
    ABOVE = auto()
    BELOW = auto()
    LEFT_OF = auto()
    RIGHT_OF = auto()


@dataclass
class SemanticObject:
    """
    Rich semantic representation of a grid object.
    Goes beyond just pixels to capture meaningful properties.
    """
    id: int
    color: int
    pixels: Set[Tuple[int, int]]
    bbox: Tuple[int, int, int, int]  # (min_r, min_c, max_r, max_c)
    shape: Tuple[int, int]  # (height, width)

    # Semantic properties
    area: int = field(init=False)
    density: float = field(init=False)
    aspect_ratio: float = field(init=False)
    center: Tuple[float, float] = field(init=False)

    # Structural properties
    has_holes: bool = False
    is_filled: bool = True
    is_connected: bool = True

    # Positional properties
    row_position: str = "middle"  # top, middle, bottom
    col_position: str = "middle"  # left, middle, right

    def __post_init__(self):
        self.area = len(self.pixels)
        h, w = self.shape
        self.density = self.area / (h * w) if h * w > 0 else 0
        self.aspect_ratio = w / h if h > 0 else 1.0
        min_r, min_c, max_r, max_c = self.bbox
        self.center = ((min_r + max_r) / 2, (min_c + max_c) / 2)

    def to_grid(self, grid_h: int, grid_w: int) -> List[List[int]]:
        """Convert object back to grid coordinates."""
        grid = [[0] * grid_w for _ in range(grid_h)]
        for r, c in self.pixels:
            if 0 <= r < grid_h and 0 <= c < grid_w:
                grid[r][c] = self.color
        return grid

    def distance_to(self, other: 'SemanticObject') -> float:
        """Calculate Euclidean distance between centers."""
        c1 = self.center
        c2 = other.center
        return np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

    def relative_position(self, other: 'SemanticObject') -> ObjectRelation:
        """Determine positional relationship."""
        my_center = self.center
        other_center = other.center

        dr = my_center[0] - other_center[0]
        dc = my_center[1] - other_center[1]

        # Check for alignment
        if abs(dr) < 2 and abs(dc) < 2:
            return ObjectRelation.OVERLAPPING

        if abs(dr) < 2:
            return ObjectRelation.ALIGNED_H
        if abs(dc) < 2:
            return ObjectRelation.ALIGNED_V

        # Cardinal directions
        if abs(dr) > abs(dc) * 2:
            return ObjectRelation.ABOVE if dr < 0 else ObjectRelation.BELOW
        elif abs(dc) > abs(dr) * 2:
            return ObjectRelation.LEFT_OF if dc < 0 else ObjectRelation.RIGHT_OF
        else:
            return ObjectRelation.SEPARATED


class SemanticObjectReasoning:
    """
    Advanced semantic understanding of grid objects.

    Goes beyond simple connected components to understand:
    - Object properties and relationships
    - Semantic roles and functions
    - Transformational patterns
    """

    def __init__(self):
        self.objects: List[SemanticObject] = []
        self.relationships: Dict[Tuple[int, int], ObjectRelation] = {}

    def parse_grid(self, grid: List[List[int]]) -> 'SemanticObjectReasoning':
        """Parse grid into semantic objects."""
        h, w = len(grid), len(grid[0]) if grid else (0, 0)

        # Find connected components
        visited = [[False] * w for _ in range(h)]
        objects = []

        obj_id = 0
        for i in range(h):
            for j in range(w):
                if grid[i][j] != 0 and not visited[i][j]:
                    obj = self._extract_object(grid, i, j, visited, obj_id)
                    if obj:
                        objects.append(obj)
                        obj_id += 1

        # Analyze relationships
        relationships = {}
        for i, obj1 in enumerate(objects):
            for j, obj2 in enumerate(objects):
                if i < j:
                    relationships[(obj1.id, obj2.id)] = obj1.relative_position(obj2)

        # Create new instance with parsed objects
        result = SemanticObjectReasoning()
        result.objects = objects
        result.relationships = relationships
        return result

    def _extract_object(self, grid: List[List[int]],
                     start_r: int, start_c: int,
                     visited: List[List[bool]],
                     obj_id: int) -> Optional[SemanticObject]:
        """Extract a single semantic object using BFS."""
        h, w = len(grid), len(grid[0])
        color = grid[start_r][start_c]

        pixels = set()
        queue = [(start_r, start_c)]
        visited[start_r][start_c] = True

        min_r = max_r = start_r
        min_c = max_c = start_c

        while queue:
            r, c = queue.pop(0)
            pixels.add((r, c))

            min_r = min(min_r, r)
            max_r = max(max_r, r)
            min_c = min(min_c, c)
            max_c = max(max_c, c)

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    if not visited[nr][nc] and grid[nr][nc] == color:
                        visited[nr][nc] = True
                        queue.append((nr, nc))

        # Calculate semantic properties
        obj_h = max_r - min_r + 1
        obj_w = max_c - min_c + 1

        # Determine row position
        grid_h = len(grid)
        if min_r < grid_h * 0.25:
            row_pos = "top"
        elif max_r > grid_h * 0.75:
            row_pos = "bottom"
        else:
            row_pos = "middle"

        # Determine column position
        grid_w = len(grid[0])
        if min_c < grid_w * 0.25:
            col_pos = "left"
        elif max_c > grid_w * 0.75:
            col_pos = "right"
        else:
            col_pos = "middle"

        return SemanticObject(
            id=obj_id,
            color=color,
            pixels=pixels,
            bbox=(min_r, min_c, max_r, max_c),
            shape=(obj_h, obj_w),
            row_position=row_pos,
            col_position=col_pos
        )

    def find_by_properties(self,
                        color: Optional[int] = None,
                        position: Optional[str] = None,
                        min_area: Optional[int] = None,
                        max_area: Optional[int] = None) -> List[SemanticObject]:
        """Find objects matching semantic properties."""
        matches = []

        for obj in self.objects:
            if color is not None and obj.color != color:
                continue
            if position is not None and position not in (obj.row_position, obj.col_position):
                continue
            if min_area is not None and obj.area < min_area:
                continue
            if max_area is not None and obj.area > max_area:
                continue

            matches.append(obj)

        return matches

    def get_largest_object(self) -> Optional[SemanticObject]:
        """Get the largest object by area."""
        if not self.objects:
            return None
        return max(self.objects, key=lambda o: o.area)

    def get_smallest_object(self) -> Optional[SemanticObject]:
        """Get the smallest object by area."""
        if not self.objects:
            return None
        return min(self.objects, key=lambda o: o.area)

    def sort_objects_by(self, key: str = "area") -> List[SemanticObject]:
        """Sort objects by a property."""
        if key == "area":
            return sorted(self.objects, key=lambda o: o.area)
        elif key == "color":
            return sorted(self.objects, key=lambda o: o.color)
        elif key == "row":
            return sorted(self.objects, key=lambda o: o.center[0])
        elif key == "col":
            return sorted(self.objects, key=lambda o: o.center[1])
        else:
            return list(self.objects)

    def count_objects_by_color(self) -> Dict[int, int]:
        """Count objects by their color."""
        counts = defaultdict(int)
        for obj in self.objects:
            counts[obj.color] += 1
        return dict(counts)

    def get_color_pattern(self) -> str:
        """Get semantic description of color pattern."""
        if not self.objects:
            return "empty"

        color_counts = self.count_objects_by_color()

        if len(color_counts) == 1:
            color = next(iter(color_counts))
            return f"uniform_{color}"
        elif len(color_counts) == 2:
            c1, c2 = sorted(color_counts.keys())
            return f"two_color_{c1}_{c2}"
        else:
            return f"multi_color_{len(color_counts)}"


# ============================================================================
# Capability 2: Arithmetic Reasoning
# ============================================================================

class ArithmeticOperation(Enum):
    """Types of arithmetic operations."""
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    MODULO = auto()
    COUNT = auto()
    SUM = auto()
    AVERAGE = auto()
    PROGRESSION = auto()


@dataclass
class ArithmeticHypothesis:
    """Hypothesis about arithmetic pattern in the grid."""
    operation: ArithmeticOperation
    confidence: float
    description: str

    # Parameters for the operation
    operand: Optional[int] = None  # For single-operand operations
