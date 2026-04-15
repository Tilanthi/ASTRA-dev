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
Grid DSL (Domain-Specific Language) for ARC-AGI

Provides a comprehensive set of grid transformation primitives that can be
composed to solve ARC-AGI tasks.
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
import copy


class Color(Enum):
    """ARC-AGI colors (0-9)"""
    BLACK = 0
    BLUE = 1
    RED = 2
    GREEN = 3
    YELLOW = 4
    GRAY = 5
    MAGENTA = 6
    ORANGE = 7
    CYAN = 8
    BROWN = 9


class Direction(Enum):
    """Cardinal and diagonal directions"""
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)
    UP_LEFT = (-1, -1)
    UP_RIGHT = (-1, 1)
    DOWN_LEFT = (1, -1)
    DOWN_RIGHT = (1, 1)


class Symmetry(Enum):
    """Types of symmetry"""
    HORIZONTAL = auto()
    VERTICAL = auto()
    DIAGONAL_MAIN = auto()
    DIAGONAL_ANTI = auto()
    ROTATIONAL_90 = auto()
    ROTATIONAL_180 = auto()


@dataclass
class BoundingBox:
    """Bounding box for a region"""
    r1: int
    c1: int
    r2: int
    c2: int

    @property
    def height(self) -> int:
        return self.r2 - self.r1 + 1

    @property
    def width(self) -> int:
        return self.c2 - self.c1 + 1

    @property
    def area(self) -> int:
        return self.height * self.width

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.r1 + self.r2) / 2, (self.c1 + self.c2) / 2)


@dataclass
class GridObject:
    """Represents a connected object in a grid"""
    pixels: Set[Tuple[int, int]]
    color: int
    bbox: BoundingBox

    @classmethod
    def from_pixels(cls, pixels: Set[Tuple[int, int]], color: int) -> 'GridObject':
        if not pixels:
            return cls(set(), color, BoundingBox(0, 0, 0, 0))
        rows = [p[0] for p in pixels]
        cols = [p[1] for p in pixels]
        bbox = BoundingBox(min(rows), min(cols), max(rows), max(cols))
        return cls(pixels, color, bbox)

    def to_grid(self) -> np.ndarray:
        """Extract object as a minimal grid"""
        grid = np.zeros((self.bbox.height, self.bbox.width), dtype=int)
        for r, c in self.pixels:
            grid[r - self.bbox.r1, c - self.bbox.c1] = self.color
        return grid

    @property
    def size(self) -> int:
        return len(self.pixels)


class Grid:
    """
    Core grid class with transformation methods.
    Wraps a numpy array and provides DSL operations.
    """

    def __init__(self, data: Any):
        if isinstance(data, list):
            self.data = np.array(data, dtype=int)
        elif isinstance(data, np.ndarray):
            self.data = data.astype(int)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

    @property
    def height(self) -> int:
        return self.data.shape[0]

    @property
    def width(self) -> int:
        return self.data.shape[1]

    @property
    def shape(self) -> Tuple[int, int]:
        return self.data.shape

    def copy(self) -> 'Grid':
        return Grid(self.data.copy())

    def __eq__(self, other: 'Grid') -> bool:
        if not isinstance(other, Grid):
            return False
        return np.array_equal(self.data, other.data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def to_list(self) -> List[List[int]]:
        return self.data.tolist()

    # ========== Color Operations ==========

    def get_colors(self) -> Set[int]:
        """Get all unique colors in grid"""
        return set(np.unique(self.data))

    def get_non_background_colors(self, background: int = 0) -> Set[int]:
        """Get colors excluding background"""
        return self.get_colors() - {background}

    def color_count(self, color: int) -> int:
        """Count pixels of a specific color"""
        return int(np.sum(self.data == color))

    def most_common_color(self, exclude: Set[int] = None) -> int:
        """Get most common color"""
        exclude = exclude or set()
        colors, counts = np.unique(self.data, return_counts=True)
        for color, count in sorted(zip(colors, counts), key=lambda x: -x[1]):
            if color not in exclude:
                return int(color)
        return 0

    def replace_color(self, old_color: int, new_color: int) -> 'Grid':
        """Replace all pixels of one color with another"""
        result = self.copy()
        result.data[result.data == old_color] = new_color
        return result

    def apply_color_map(self, color_map: Dict[int, int]) -> 'Grid':
        """Apply a color mapping to the entire grid"""
        result = self.copy()
        for old_color, new_color in color_map.items():
            result.data[self.data == old_color] = new_color
        return result

    # ========== Geometric Transformations ==========

    def rotate_90(self) -> 'Grid':
        """Rotate 90 degrees clockwise"""
        return Grid(np.rot90(self.data, k=-1))

    def rotate_180(self) -> 'Grid':
        """Rotate 180 degrees"""
        return Grid(np.rot90(self.data, k=2))

    def rotate_270(self) -> 'Grid':
        """Rotate 270 degrees clockwise (90 counter-clockwise)"""
        return Grid(np.rot90(self.data, k=1))

    def flip_horizontal(self) -> 'Grid':
        """Flip horizontally (left-right)"""
        return Grid(np.fliplr(self.data))

    def flip_vertical(self) -> 'Grid':
        """Flip vertically (up-down)"""
        return Grid(np.flipud(self.data))

    def transpose(self) -> 'Grid':
        """Transpose (swap rows and columns)"""
        return Grid(self.data.T)

    # ========== Scaling Operations ==========

    def scale(self, factor_h: int, factor_w: int) -> 'Grid':
        """Scale grid by integer factors"""
        return Grid(np.repeat(np.repeat(self.data, factor_h, axis=0), factor_w, axis=1))

    def tile(self, times_h: int, times_w: int) -> 'Grid':
        """Tile grid multiple times"""
        return Grid(np.tile(self.data, (times_h, times_w)))

    def crop(self, r1: int, c1: int, r2: int, c2: int) -> 'Grid':
        """Crop to bounding box (inclusive)"""
        return Grid(self.data[r1:r2+1, c1:c2+1])

    def crop_to_content(self, background: int = 0) -> 'Grid':
        """Crop to bounding box of non-background content"""
        rows, cols = np.where(self.data != background)
        if len(rows) == 0:
            return Grid(np.array([[background]]))
        return self.crop(rows.min(), cols.min(), rows.max(), cols.max())

    def pad(self, top: int, bottom: int, left: int, right: int, fill: int = 0) -> 'Grid':
        """Pad grid with specified amounts"""
        return Grid(np.pad(self.data, ((top, bottom), (left, right)),
                         mode='constant', constant_values=fill))

    def resize(self, new_h: int, new_w: int, fill: int = 0) -> 'Grid':
        """Resize grid (crop or pad as needed)"""
        result = np.full((new_h, new_w), fill, dtype=int)
        h = min(self.height, new_h)
        w = min(self.width, new_w)
        result[:h, :w] = self.data[:h, :w]
        return Grid(result)

    # ========== Object Detection ==========

    def find_objects(self, background: int = 0, connectivity: int = 4) -> List[GridObject]:
        """Find all connected objects (excluding background)"""
        objects = []
        visited = set()

        def flood_fill(start_r: int, start_c: int, color: int) -> Set[Tuple[int, int]]:
            pixels = set()
            stack = [(start_r, start_c)]

            while stack:
                r, c = stack.pop()
                if (r, c) in visited:
                    continue
                if r < 0 or r >= self.height or c < 0 or c >= self.width:
                    continue
                if self.data[r, c] != color:
                    continue

                visited.add((r, c))
                pixels.add((r, c))

                # Add neighbors based on connectivity
                stack.extend([(r-1, c), (r+1, c), (r, c-1), (r, c+1)])
                if connectivity == 8:
                    stack.extend([(r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1)])

            return pixels

        for r in range(self.height):
            for c in range(self.width):
                if (r, c) not in visited and self.data[r, c] != background:
                    color = self.data[r, c]
                    pixels = flood_fill(r, c, color)
                    if pixels:
                        objects.append(GridObject.from_pixels(pixels, color))

        return objects

    def find_rectangles(self, color: int = None) -> List[BoundingBox]:
        """Find all rectangular regions of a specific color (or any non-zero)"""
        rectangles = []
        visited = np.zeros_like(self.data, dtype=bool)

        for r in range(self.height):
            for c in range(self.width):
                if visited[r, c]:
                    continue

                cell_color = self.data[r, c]
                if color is not None and cell_color != color:
                    continue
                if color is None and cell_color == 0:
                    continue

                # Try to extend rectangle
                r2, c2 = r, c
                while r2 + 1 < self.height and self.data[r2 + 1, c] == cell_color:
                    r2 += 1
                while c2 + 1 < self.width:
                    valid = True
                    for ri in range(r, r2 + 1):
                        if self.data[ri, c2 + 1] != cell_color:
                            valid = False
                            break
                    if valid:
                        c2 += 1
                    else:
                        break

                # Mark as visited
                for ri in range(r, r2 + 1):
                    for ci in range(c, c2 + 1):
                        visited[ri, ci] = True

                rectangles.append(BoundingBox(r, c, r2, c2))

        return rectangles

    # ========== Pattern Detection ==========

    def detect_symmetry(self) -> List[Symmetry]:
        """Detect types of symmetry in the grid"""
        symmetries = []

        if np.array_equal(self.data, np.fliplr(self.data)):
            symmetries.append(Symmetry.HORIZONTAL)
        if np.array_equal(self.data, np.flipud(self.data)):
            symmetries.append(Symmetry.VERTICAL)
        if self.height == self.width:
            if np.array_equal(self.data, self.data.T):
                symmetries.append(Symmetry.DIAGONAL_MAIN)
            if np.array_equal(self.data, np.fliplr(self.data.T)):
                symmetries.append(Symmetry.DIAGONAL_ANTI)
            if np.array_equal(self.data, np.rot90(self.data, k=-1)):
                symmetries.append(Symmetry.ROTATIONAL_90)
        if np.array_equal(self.data, np.rot90(self.data, k=2)):
            symmetries.append(Symmetry.ROTATIONAL_180)

        return symmetries

    def detect_periodicity(self) -> Tuple[Optional[int], Optional[int]]:
        """Detect horizontal and vertical periodicity"""
        h_period = None
        v_period = None

        # Check horizontal periodicity
        for p in range(1, self.width // 2 + 1):
            if self.width % p == 0:
                is_periodic = True
                for c in range(self.width):
                    if not np.array_equal(self.data[:, c % p], self.data[:, c]):
                        is_periodic = False
                        break
                if is_periodic:
                    h_period = p
                    break

        # Check vertical periodicity
        for p in range(1, self.height // 2 + 1):
            if self.height % p == 0:
                is_periodic = True
                for r in range(self.height):
                    if not np.array_equal(self.data[r % p, :], self.data[r, :]):
                        is_periodic = False
                        break
                if is_periodic:
                    v_period = p
                    break

        return (v_period, h_period)

    def find_pattern_locations(self, pattern: 'Grid') -> List[Tuple[int, int]]:
        """Find all locations where a pattern appears"""
        locations = []
        ph, pw = pattern.shape

        for r in range(self.height - ph + 1):
            for c in range(self.width - pw + 1):
                if np.array_equal(self.data[r:r+ph, c:c+pw], pattern.data):
                    locations.append((r, c))

        return locations

    # ========== Drawing Operations ==========

    def draw_line(self, r1: int, c1: int, r2: int, c2: int, color: int) -> 'Grid':
        """Draw a line between two points"""
        result = self.copy()

        # Bresenham's line algorithm
        dr = abs(r2 - r1)
        dc = abs(c2 - c1)
        sr = 1 if r1 < r2 else -1
        sc = 1 if c1 < c2 else -1
        err = dr - dc

        r, c = r1, c1
        while True:
            if 0 <= r < self.height and 0 <= c < self.width:
                result.data[r, c] = color
            if r == r2 and c == c2:
                break
            e2 = 2 * err
            if e2 > -dc:
                err -= dc
                r += sr
            if e2 < dr:
                err += dr
                c += sc

        return result

    def draw_rectangle(self, r1: int, c1: int, r2: int, c2: int, color: int,
                       fill: bool = False) -> 'Grid':
        """Draw a rectangle (outline or filled)"""
        result = self.copy()

        if fill:
            result.data[r1:r2+1, c1:c2+1] = color
        else:
            result.data[r1, c1:c2+1] = color
            result.data[r2, c1:c2+1] = color
            result.data[r1:r2+1, c1] = color
            result.data[r1:r2+1, c2] = color

        return result

    def fill_region(self, r: int, c: int, new_color: int) -> 'Grid':
        """Flood fill from a point"""
        result = self.copy()
        old_color = result.data[r, c]

        if old_color == new_color:
            return result

        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if cr < 0 or cr >= self.height or cc < 0 or cc >= self.width:
                continue
            if result.data[cr, cc] != old_color:
                continue

            result.data[cr, cc] = new_color
            stack.extend([(cr-1, cc), (cr+1, cc), (cr, cc-1), (cr, cc+1)])

        return result

    def overlay(self, other: 'Grid', r_offset: int, c_offset: int,
                transparent: int = None) -> 'Grid':
        """Overlay another grid at specified position"""
        result = self.copy()

        for r in range(other.height):
            for c in range(other.width):
                tr, tc = r + r_offset, c + c_offset
                if 0 <= tr < self.height and 0 <= tc < self.width:
                    if transparent is None or other.data[r, c] != transparent:
                        result.data[tr, tc] = other.data[r, c]

        return result

    # ========== Masking Operations ==========

    def apply_mask(self, mask: 'Grid', value: int) -> 'Grid':
        """Set cells to value where mask is non-zero"""
        result = self.copy()
        result.data[mask.data != 0] = value
        return result

    def extract_by_mask(self, mask: 'Grid') -> 'Grid':
        """Extract grid values where mask is non-zero, else 0"""
        result = Grid(np.zeros_like(self.data))
        result.data[mask.data != 0] = self.data[mask.data != 0]
        return result

    def where(self, condition: Callable[[int], bool]) -> List[Tuple[int, int]]:
        """Find all cells matching a condition"""
        result = []
        for r in range(self.height):
            for c in range(self.width):
                if condition(self.data[r, c]):
                    result.append((r, c))
        return result

    # ========== Comparison Operations ==========

    def diff(self, other: 'Grid') -> 'Grid':
        """Return grid showing differences (XOR-like)"""
        result = Grid(np.zeros_like(self.data))
        diff_mask = self.data != other.data
        result.data[diff_mask] = 1  # Mark differences
        return result

    def intersection(self, other: 'Grid') -> 'Grid':
        """Return grid showing common non-zero elements"""
        result = Grid(np.zeros_like(self.data))
        common = (self.data != 0) & (other.data != 0) & (self.data == other.data)
        result.data[common] = self.data[common]
        return result

    def union(self, other: 'Grid', priority: str = 'self') -> 'Grid':
        """Combine two grids (union of non-zero elements)"""
        result = self.copy()
        if priority == 'other':
            mask = other.data != 0
            result.data[mask] = other.data[mask]
        else:  # priority == 'self'
            mask = (result.data == 0) & (other.data != 0)
            result.data[mask] = other.data[mask]
        return result


# ========== Grid Factory Functions ==========

def empty_grid(height: int, width: int, fill: int = 0) -> Grid:
    """Create an empty grid"""
    return Grid(np.full((height, width), fill, dtype=int))


def from_objects(objects: List[GridObject], height: int, width: int,
                background: int = 0) -> Grid:
    """Create grid from list of objects"""
    grid = empty_grid(height, width, background)
    for obj in objects:
        for r, c in obj.pixels:
            if 0 <= r < height and 0 <= c < width:
                grid.data[r, c] = obj.color
    return grid



# Utility: Computation Logging
def log_computation(*args, **kwargs):
    """Utility function for log_computation."""
    return None


