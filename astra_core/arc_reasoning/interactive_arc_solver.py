#!/usr/bin/env python3
"""
Interactive ARC Solver
Describes what it sees and asks for guidance on transformations.
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from collections import Counter
import json


# ============================================================================
# Task Visualization and Description
# ============================================================================

@dataclass
class TaskObservation:
    """What the solver observes about a task."""
    task_id: str
    input_size: Tuple[int, int]
    output_size: Tuple[int, int]
    size_change: str
    input_colors: List[int]
    output_colors: List[int]
    color_changes: Dict[int, int]
    has_objects: bool
    object_count: int
    patterns_detected: List[str]
    suggested_transformations: List[str]

    def to_description(self) -> str:
        """Generate a human-readable description."""
        lines = [
            f"Task {self.task_id} Analysis:",
            f"  Grid size: {self.input_size[0]}x{self.input_size[1]} -> {self.output_size[0]}x{self.output_size[1]}",
            f"  Size change: {self.size_change}",
            f"  Colors in input: {self.input_colors}",
            f"  Colors in output: {self.output_colors}",
        ]

        if self.color_changes:
            changes_str = ", ".join(f"{k}->{v}" for k, v in self.color_changes.items())
            lines.append(f"  Color changes detected: {changes_str}")

        lines.append(f"  Objects detected: {self.object_count}")

        if self.patterns_detected:
            lines.append(f"  Patterns detected: {', '.join(self.patterns_detected)}")

        if self.suggested_transformations:
            lines.append(f"  Suggested transformations to try:")
            for suggestion in self.suggested_transformations:
                lines.append(f"    - {suggestion}")

        return "\n".join(lines)


def observe_task(task_id: str,
                train_inputs: List[List[List[int]]],
                train_outputs: List[List[List[int]]],
                test_input: List[List[int]]) -> TaskObservation:
    """Carefully observe and describe a task."""
    inp_h, inp_w = len(train_inputs[0]), len(train_inputs[0][0])
    out_h, out_w = len(train_outputs[0]), len(train_outputs[0][0])

    # Size change
    inp_size = inp_h * inp_w
    out_size = out_h * out_w
    if inp_size == out_size:
        size_change = "same size"
    elif out_size < inp_size:
        ratio = out_size / inp_size
        size_change = f"compression ({ratio:.0%} of original)"
    else:
        ratio = out_size / inp_size
        size_change = f"expansion ({ratio:.0%} of original)"

    # Colors
    input_colors = sorted(set(c for inp in train_inputs for row in inp for c in row if c != 0))
    output_colors = sorted(set(c for out in train_outputs for row in out for c in row if c != 0))

    # Color changes
    color_changes = {}
    for inp, out in zip(train_inputs, train_outputs):
        h = min(len(inp), len(out))
        w = min(len(inp[0]), len(out[0]))
        for r in range(h):
            for c in range(w):
                if inp[r][c] != out[r][c]:
                    if inp[r][c] in color_changes:
                        if color_changes[inp[r][c]] != out[r][c]:
                            color_changes[inp[r][c]] = None  # Conflicting
                    else:
                        color_changes[inp[r][c]] = out[r][c]

    # Remove conflicting
    color_changes = {k: v for k, v in color_changes.items() if v is not None}

    # Object detection
    objects = extract_objects(train_inputs[0])
    object_count = len(objects)

    # Pattern detection
    patterns = []

    if inp_h == out_h and inp_w == out_w:
        patterns.append("same-size transformation")

    if out_size < inp_size:
        patterns.append("compression/reduction")
        if object_count > 1:
            patterns.append("object selection/extraction")

    if out_size > inp_size:
        patterns.append("expansion/tiling")

    if color_changes:
        patterns.append("color transformation")

    if any(len(inp) > 10 or len(inp[0]) > 10 for inp in train_inputs):
        patterns.append("large grid (may need cropping)")

    # Suggested transformations
    suggestions = []

    if color_changes:
        suggestions.append(f"Color map: {color_changes}")

    if inp_h == out_h and inp_w == out_w:
        suggestions.append("Geometric: rotation, reflection, or transpose")
        suggestions.append("Color-only transformation")

    if out_size < inp_size:
        suggestions.append("Crop to content bounds")
        if object_count > 1:
            suggestions.append("Extract specific objects")
            suggestions.append("Select subset of objects")

    if has_local_patterns(train_inputs, train_outputs):
        suggestions.append("Local pattern transformation (corners, edges, etc.)")

    if has_regular_structure(train_inputs[0]):
        suggestions.append("Structure-based transformation (find and replace patterns)")

    return TaskObservation(
        task_id=task_id,
        input_size=(inp_h, inp_w),
        output_size=(out_h, out_w),
        size_change=size_change,
        input_colors=input_colors,
        output_colors=output_colors,
        color_changes=color_changes,
        has_objects=object_count > 0,
        object_count=object_count,
        patterns_detected=patterns,
        suggested_transformations=suggestions,
    )


def extract_objects(grid):
    """Extract connected objects from grid."""
    if not grid or not grid[0]:
        return []

    h, w = len(grid), len(grid[0])
    visited = [[False] * w for _ in range(h)]
    objects = []

    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and not visited[r][c]:
                color = grid[r][c]
                cells = []
                queue = [(r, c)]
                visited[r][c] = True

                while queue:
                    cr, cc = queue.pop(0)
                    cells.append((cr, cc))

                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            if grid[nr][nc] == color and not visited[nr][nc]:
                                visited[nr][nc] = True
                                queue.append((nr, nc))

                objects.append({'color': color, 'cells': cells, 'count': len(cells)})

    return objects


def has_local_patterns(inputs, outputs):
    """Check if transformation seems to be based on local patterns."""
    for inp, out in zip(inputs, outputs):
        h = min(len(inp), len(out))
        w = min(len(inp[0]), len(out[0]))

        # Check if changes are localized
        changes = 0
        for r in range(h):
            for c in range(w):
                if inp[r][c] != out[r][c]:
                    changes += 1

        # If changes are sparse, might be local pattern
        if 0 < changes < (h * w) * 0.3:
            return True

    return False


def has_regular_structure(grid):
    """Check if grid has regular structure (stripes, checkerboard, etc.)."""
    if not grid or not grid[0]:
        return False

    h, w = len(grid), len(grid[0])

    # Check for horizontal stripes
    stripe_consistency = 0
    for r in range(h - 1):
        if grid[r] == grid[r + 1]:
            stripe_consistency += 1
    if stripe_consistency >= h / 3:
        return True

    # Check for vertical stripes
    stripe_consistency = 0
    for c in range(w - 1):
        col_same = True
        for r in range(h):
            if grid[r][c] != grid[r][c + 1]:
                col_same = False
                break
        if col_same:
            stripe_consistency += 1
    if stripe_consistency >= w / 3:
        return True

    return False


# ============================================================================
# Interactive Solver
# ============================================================================

class InteractiveARCSolver:
    """
    Interactive solver that observes tasks and can accept guidance.
    """

    def __init__(self, interactive_mode: bool = False):
        self.interactive_mode = interactive_mode
        self.stats = {
            'total_attempts': 0,
            'observations_made': 0,
            'solutions_found': 0,
            'solution_sources': Counter(),
            'patterns_detected': Counter(),
        }

    def solve(self, task_id: str, train_inputs: List[List[List[int]]],
              train_outputs: List[List[List[int]]],
              test_input: List[List[int]],
              guidance: Optional[str] = None) -> Optional[List[List[int]]]:
        """
        Solve task, optionally with human guidance.
        If guidance is provided, use it to generate solutions.
        """
        self.stats['total_attempts'] += 1

        # Observe task
        observation = observe_task(task_id, train_inputs, train_outputs, test_input)
        self.stats['observations_made'] += 1

        for pattern in observation.patterns_detected:
            self.stats['patterns_detected'][pattern] += 1

        # Generate candidates based on observation
        candidates = self._generate_candidates(observation, train_inputs, train_outputs, test_input)

        # If guidance provided, use it
        if guidance:
            guided_candidates = self._apply_guidance(guidance, observation, test_input)
            candidates.extend(guided_candidates)

        # Try each candidate
        for name, candidate in candidates:
            if candidate and self._validate_candidate(candidate, train_outputs):
                self.stats['solutions_found'] += 1
                self.stats['solution_sources'][name] += 1
                return candidate

        return None

    def _generate_candidates(self, observation: TaskObservation,
                           train_inputs, train_outputs, test_input):
        """Generate candidate solutions based on observation."""
        candidates = []

        # Color mapping
        if observation.color_changes:
            color_map = observation.color_changes
            candidate = [[color_map.get(c, c) for c in row] for row in test_input]
            candidates.append(('color_map', candidate))

        # Geometric transformations (same size)
        if observation.input_size == observation.output_size:
            transformations = [
                ('rotate_90', self._rotate_90(test_input)),
                ('rotate_180', self._rotate_180(test_input)),
                ('rotate_270', self._rotate_270(test_input)),
                ('reflect_h', test_input[::-1]),
                ('reflect_v', [row[::-1] for row in test_input]),
            ]
            candidates.extend(transformations)

        # Compression (crop to content)
        if observation.output_size[0] < observation.input_size[0]:
            cropped = self._crop_to_content(test_input)
            candidates.append(('crop', cropped))

            # Extract objects
            if observation.object_count > 1:
                extracted = self._extract_objects_compact(test_input)
                candidates.append(('extract_objects', extracted))

        return candidates

    def _apply_guidance(self, guidance: str, observation: TaskObservation, test_input):
        """Apply human guidance to generate candidates."""
        candidates = []
        guidance_lower = guidance.lower()

        # Parse guidance for transformation type
        if 'rotate' in guidance_lower or 'turn' in guidance_lower:
            if '90' in guidance or 'right' in guidance_lower:
                candidates.append(('guided_rotate_90', self._rotate_90(test_input)))
            elif '180' in guidance:
                candidates.append(('guided_rotate_180', self._rotate_180(test_input)))
            elif '270' in guidance or 'left' in guidance_lower:
                candidates.append(('guided_rotate_270', self._rotate_270(test_input)))

        if 'flip' in guidance_lower or 'mirror' in guidance_lower:
            if 'horizontal' in guidance_lower or 'top' in guidance_lower:
                candidates.append(('guided_flip_h', test_input[::-1]))
            elif 'vertical' in guidance_lower or 'side' in guidance_lower:
                candidates.append(('guided_flip_v', [row[::-1] for row in test_input]))

        if 'crop' in guidance_lower or 'trim' in guidance_lower:
            candidates.append(('guided_crop', self._crop_to_content(test_input)))

        if 'color' in guidance_lower or 'map' in guidance_lower:
            if observation.color_changes:
                color_map = observation.color_changes
                candidate = [[color_map.get(c, c) for c in row] for row in test_input]
                candidates.append(('guided_color_map', candidate))

        return candidates

    def _validate_candidate(self, candidate, train_outputs):
        """Check if candidate has expected properties."""
        if not candidate:
            return False

        expected_h, expected_w = len(train_outputs[0]), len(train_outputs[0][0])
        actual_h, actual_w = len(candidate), len(candidate[0]) if candidate else 0

        # Size should be reasonable
        if actual_h == expected_h and actual_w == expected_w:
            return True

        # Allow some flexibility
        if 0 < actual_h <= expected_h * 2 and 0 < actual_w <= expected_w * 2:
            return True

        return False

    def _rotate_90(self, grid):
        return [list(row) for row in zip(*grid[::-1])]

    def _rotate_180(self, grid):
        return [row[::-1] for row in grid[::-1]]

    def _rotate_270(self, grid):
        return [list(row)[::-1] for row in zip(*grid)][::-1]

    def _crop_to_content(self, grid):
        if not grid or not grid[0]:
            return grid

        min_r, max_r = len(grid), -1
        min_c, max_c = len(grid[0]), -1

        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                if cell != 0:
                    min_r = min(min_r, r)
                    max_r = max(max_r, r)
                    min_c = min(min_c, c)
                    max_c = max(max_c, c)

        if max_r < 0:
            return grid

        return [row[min_c:max_c+1] for row in grid[min_r:max_r+1]]

    def _extract_objects_compact(self, grid):
        """Extract and arrange objects compactly."""
        objects = extract_objects(grid)
        if not objects:
            return self._crop_to_content(grid)

        # Arrange by size (largest first)
        objects.sort(key=lambda o: o['count'], reverse=True)

        # Create compact arrangement
        result_rows = []
        current_row = []
        current_width = 0
        max_obj_width = max(
            max(c for r, c in o['cells']) - min(c for r, c in o['cells']) + 1
            for o in objects
        ) if objects else 1

        for obj in objects:
            # Calculate object bounds
            min_r = min(r for r, c in obj['cells'])
            max_r = max(r for r, c in obj['cells'])
            min_c = min(c for r, c in obj['cells'])
            max_c = max(c for r, c in obj['cells'])

            obj_width = max_c - min_c + 1
            obj_height = max_r - min_r + 1

            # Check if we need a new row
            if current_width + obj_width > 30:
                result_rows.append(current_row)
                current_row = []
                current_width = 0

            # Add object to current row
            for r, c in obj['cells']:
                row_idx = r - min_r
                col_idx = c - min_c + current_width
                while len(current_row) <= row_idx:
                    current_row.append([])
                while len(current_row[row_idx]) <= col_idx:
                    current_row[row_idx].append(0)
                current_row[row_idx][col_idx] = obj['color']

            current_width += obj_width + 1  # +1 for spacing

        if current_row:
            result_rows.append(current_row)

        return result_rows if result_rows else [[0]]


__all__ = ['InteractiveARCSolver', 'TaskObservation', 'observe_task']



def utility_function_12(*args, **kwargs):
    """Utility function 12."""
    return None


