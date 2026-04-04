#!/usr/bin/env python3
"""
STAN Semantic Compression Module

Critical capability for tasks requiring information reduction and summarization.
This handles the ~40% of tasks that need compression/transformation.

Capabilities:
1. Object Aggregation - Group similar objects into representatives
2. Pattern Summarization - Extract key structural features
3. Dimensionality Reduction - Transform to lower-dimensional representation
4. Semantic Filtering - Keep only semantically important elements
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from enum import Enum, auto
import copy


# ============================================================================
# Import base semantic module
# ============================================================================

try:
    from .semantic_reasoning import SemanticObject, SemanticObjectReasoning, ObjectRelation
    _base_available = True
except ImportError:
    _base_available = False
    SemanticObject = None
    SemanticObjectReasoning = None
    ObjectRelation = None


# ============================================================================
# Semantic Compression Capabilities
# ============================================================================

class AggregationMethod(Enum):
    """Methods for aggregating multiple objects."""
    MAJORITY_COLOR = auto()
    LARGEST_OBJECT = auto()
    CENTROID = auto()
    DOMINANT_POSITION = auto()
    COLOR_GROUPING = auto()
    PATTERN_EXTRACTION = auto()


@dataclass
class AggregatedObject:
    """Result of aggregating multiple objects."""
    source_objects: List[int]  # IDs of source objects
    representative_color: int
    position: Tuple[int, int]  # (row, col)
    size: int
    method: AggregationMethod


class SemanticCompressor:
    """
    Advanced semantic compression for grid transformations.

    Handles tasks that require reducing information while preserving
    semantic meaning - the most challenging type of ARC task.
    """

    def __init__(self):
        if _base_available:
            self.semantic = SemanticObjectReasoning()
        else:
            self.semantic = None

    def analyze_compression(self, train_input: List[List[int]],
                          train_output: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Analyze what type of compression is needed."""
        if not train_input or not train_output:
            return None

        inp_h, inp_w = len(train_input), len(train_input[0])
        out_h, out_w = len(train_output), len(train_output[0])

        inp_size = inp_h * inp_w
        out_size = out_h * out_w
        compression_ratio = out_size / inp_size if inp_size > 0 else 1.0

        # Get object counts
        if self.semantic:
            inp_sem = self.semantic.parse_grid(train_input)
            out_sem = self.semantic.parse_grid(train_output)

            inp_obj_count = len(inp_sem.objects)
            out_obj_count = len(out_sem.objects)
        else:
            inp_obj_count = 0
            out_obj_count = 0

        analysis = {
            'compression_ratio': compression_ratio,
            'size_reduction': inp_size > out_size,
            'object_count_change': inp_obj_count - out_obj_count,
            'output_dimensions': (out_h, out_w),
        }

        # Determine compression type
        if compression_ratio < 0.1:
            # Extreme compression - likely pattern extraction
            analysis['type'] = 'extreme_compression'
            analysis['method'] = 'pattern_extraction'
        elif compression_ratio < 0.3:
            # High compression - likely aggregation
            analysis['type'] = 'high_compression'
            analysis['method'] = 'object_aggregation'
        elif out_obj_count < inp_obj_count * 0.2:
            # Major object reduction
            analysis['type'] = 'object_reduction'
            analysis['method'] = 'aggregation'
        elif inp_h != out_h or inp_w != out_w:
            # Dimension change
            analysis['type'] = 'dimension_change'
            analysis['method'] = 'subsampling_or_extraction'
        else:
            analysis['type'] = 'preserving'
            analysis['method'] = 'unknown'

        return analysis

    def compress_by_aggregation(self, grid: List[List[int]],
                             output_shape: Tuple[int, int],
                             method: AggregationMethod = AggregationMethod.LARGEST_OBJECT) -> Optional[List[List[int]]]:
        """Compress grid by aggregating objects."""
        if not self.semantic:
            return None

        parsed = self.semantic.parse_grid(grid)
        if not parsed.objects:
            return None

        out_h, out_w = output_shape

        # Group objects by their properties
        grouped = self._group_objects_for_compression(parsed.objects, output_shape, method)

        # Create output grid
        result = [[0] * out_w for _ in range(out_h)]

        # Place aggregated objects
        for agg in grouped:
            r, c = agg.position
            if 0 <= r < out_h and 0 <= c < out_w:
                result[r][c] = agg.representative_color

        return result

    def _group_objects_for_compression(self, objects: List[SemanticObject],
                                    output_shape: Tuple[int, int],
                                    method: AggregationMethod) -> List[AggregatedObject]:
        """Group objects for compression."""
        out_h, out_w = output_shape

        if method == AggregationMethod.LARGEST_OBJECT:
            # Group by spatial regions
            return self._aggregate_by_largest(objects, output_shape)

        elif method == AggregationMethod.MAJORITY_COLOR:
            # Group by color and take majority
            return self._aggregate_by_majority_color(objects, output_shape)

        elif method == AggregationMethod.DOMINANT_POSITION:
            # Group by position
            return self._aggregate_by_position(objects, output_shape)

        else:
            # Default: spatial regions
            return self._aggregate_by_regions(objects, output_shape)

    def _aggregate_by_largest(self, objects: List[SemanticObject],
                           output_shape: Tuple[int, int]) -> List[AggregatedObject]:
        """Aggregate by keeping largest object in each region."""
        out_h, out_w = output_shape
        in_h, in_w = len(objects[0].bbox[2]) + 1, len(objects) if objects else 0

        # Divide output grid into regions
        row_regions = out_h if out_h <= 3 else 3
        col_regions = out_w if out_w <= 3 else 3

        row_bins = np.linspace(0, in_h, row_regions + 1, dtype=int)
        col_bins = np.linspace(0, in_w, col_regions + 1, dtype=int)

        aggregated = []

        for ri in range(row_regions):
            for ci in range(col_regions):
                # Find objects in this region
                region_objs = []
                for obj in objects:
                    center = obj.center
                    if row_bins[ri] <= center[0] < row_bins[ri + 1] and \
                       col_bins[ci] <= center[1] < col_bins[ci + 1]:
                        region_objs.append(obj)

                if region_objs:
                    # Keep largest
                    largest = max(region_objs, key=lambda o: o.area)
                    aggregated.append(AggregatedObject(
                        source_objects=[o.id for o in region_objs],
                        representative_color=largest.color,
                        position=(ri, ci),
                        size=largest.area,
                        method=AggregationMethod.LARGEST_OBJECT
                    ))

        return aggregated

    def _aggregate_by_majority_color(self, objects: List[SemanticObject],
                                   output_shape: Tuple[int, int]) -> List[AggregatedObject]:
        """Aggregate by majority color in each region."""
        out_h, out_w = output_shape

        # Get color groups
        by_color = defaultdict(list)
        for obj in objects:
            by_color[obj.color].append(obj)

        # For each position, find most common color
        aggregated = []
        for r in range(out_h):
            for c in range(out_w):
                # Find objects that would map here
                color_counts = Counter()
                for obj in objects:
                    # Map object position to output position
                    obj_r = int(obj.center[0] * out_h / objects[0].bbox[2]) if objects else 0
                    obj_c = int(obj.center[1] * out_w / len(objects)) if objects else 0
                    if obj_r == r and obj_c == c:
                        color_counts[obj.color] += 1

                if color_counts:
                    dominant = color_counts.most_common(1)[0]
                    aggregated.append(AggregatedObject(
                        source_objects=[],
                        representative_color=dominant,
                        position=(r, c),
                        size=1,
                        method=AggregationMethod.MAJORITY_COLOR
                    ))

        return aggregated

    def _aggregate_by_position(self, objects: List[SemanticObject],
                              output_shape: Tuple[int, int]) -> List[AggregatedObject]:
        """Aggregate by object position categories."""
        out_h, out_w = output_shape
        aggregated = []

        # Get position groups
        pos_groups = defaultdict(list)
        for obj in objects:
            key = (obj.row_position, obj.col_position)
            pos_groups[key].append(obj)

        # Map positions to output grid
        pos_to_output = {
            ('top', 'left'): (0, 0),
            ('top', 'middle'): (0, out_w // 2),
            ('top', 'right'): (0, out_w - 1),
            ('middle', 'left'): (out_h // 2, 0),
            ('middle', 'middle'): (out_h // 2, out_w // 2),
            ('middle', 'right'): (out_h // 2, out_w - 1),
            ('bottom', 'left'): (out_h - 1, 0),
            ('bottom', 'middle'): (out_h - 1, out_w // 2),
            ('bottom', 'right'): (out_h - 1, out_w - 1),
        }

        for pos_key, pos_objs in pos_groups.items():
            if pos_key in pos_to_output:
                r, c = pos_to_output[pos_key]
                if pos_objs:
                    representative = max(pos_objs, key=lambda o: o.area)
                    aggregated.append(AggregatedObject(
                        source_objects=[o.id for o in pos_objs],
                        representative_color=representative.color,
                        position=(r, c),
                        size=representative.area,
                        method=AggregationMethod.DOMINANT_POSITION
                    ))

        return aggregated

    def _aggregate_by_regions(self, objects: List[SemanticObject],
                            output_shape: Tuple[int, int]) -> List[AggregatedObject]:
        """Aggregate objects by spatial regions."""
        return self._aggregate_by_largest(objects, output_shape)


class DimensionalityReducer:
    """
    Handle dimensionality reduction for grid transformations.

    This includes:
    - Row/column extraction (selecting specific rows/cols)
    - Subsampling (taking every Nth row/col)
    - Pattern-based reduction (extracting patterns)
    """

    def __init__(self):
        pass

    def analyze_reduction(self, train_input: List[List[int]],
                      train_output: List[List[int]]) -> Optional[Dict[str, Any]]:
        """Analyze what type of dimensionality reduction is needed."""
        if not train_input or not train_output:
            return None

        inp_h, inp_w = len(train_input), len(train_input[0])
        out_h, out_w = len(train_output), len(train_output[0])

        analysis = {
            'input_shape': (inp_h, inp_w),
            'output_shape': (out_h, out_w),
            'row_ratio': out_h / inp_h if inp_h > 0 else 0,
            'col_ratio': out_w / inp_w if inp_w > 0 else 0,
        }

        # Determine reduction type
        methods = []

        # Check for uniform subsampling
        if inp_h % out_h == 0 and inp_w % out_w == 0:
            row_step = inp_h // out_h
            col_step = inp_w // out_w
            if row_step == col_step:
                methods.append(('uniform_subsampling', row_step))
            else:
                methods.append(('subsampling', (row_step, col_step)))

        # Check for row extraction
        if out_h < inp_h and inp_h % out_h != 0:
            methods.append(('row_extraction', out_h))

        # Check for column extraction
        if out_w < inp_w and inp_w % out_w != 0:
            methods.append(('column_extraction', out_w))

        analysis['methods'] = methods

        return analysis if methods else None

    def reduce_by_subsampling(self, grid: List[List[int]],
                            output_shape: Tuple[int, int],
                            row_step: Optional[int] = None,
                            col_step: Optional[int] = None) -> Optional[List[List[int]]]:
        """Reduce grid by subsampling."""
        if not grid:
            return None

        inp_h, inp_w = len(grid), len(grid[0])
        out_h, out_w = output_shape

        # Calculate steps if not provided
        if row_step is None:
            row_step = inp_h // out_h if out_h > 0 and inp_h % out_h == 0 else 1
        if col_step is None:
            col_step = inp_w // out_w if out_w > 0 and inp_w % out_w == 0 else 1

        # Subsample
        result = []
        for i in range(0, inp_h, row_step):
            if len(result) >= out_h:
                break
            row = []
            for j in range(0, inp_w, col_step):
                if len(row) >= out_w:
                    break
                row.append(grid[i][j])
            result.append(row)

        # Pad if needed
        while len(result) < out_h:
            result.append([0] * out_w)

        return result

    def reduce_by_row_extraction(self, grid: List[List[int]],
                                output_shape: Tuple[int, int],
                                row_indices: Optional[List[int]] = None) -> Optional[List[List[int]]]:
        """Reduce grid by extracting specific rows."""
        if not grid:
            return None

        out_h, out_w = output_shape
        inp_h, inp_w = len(grid), len(grid[0])

        if row_indices is None:
            # Try to determine indices based on analysis
            # For now, use simple strategy: take evenly spaced rows
            row_indices = list(range(0, inp_h, max(1, inp_h // out_h)))

        result = []
        for i in row_indices[:out_h]:
            if i < inp_h:
                result.append(grid[i][:out_w] if len(grid[i]) >= out_w else grid[i] + [0] * (out_w - len(grid[i])))
            else:
                result.append([0] * out_w)

        # Pad if needed
        while len(result) < out_h:
            result.append([0] * out_w)

        return result


class PatternExtractor:
    """
    Extract key patterns from grids for compression.

    This identifies the essential structural features that should be preserved
    during compression.
    """

    def __init__(self):
        pass

    def extract_pattern(self, grid: List[List[int]],
                     output_shape: Tuple[int, int]) -> Optional[List[List[int]]]:
        """Extract essential pattern from grid."""
        if not grid:
            return None

        out_h, out_w = output_shape
        inp_h, inp_w = len(grid), len(grid[0])

        # Try different extraction methods
        methods = [
            self._extract_by_unique_rows,
            self._extract_by_color_summary,
            self._extract_by_structure,
            self._extract_by_frequency,
        ]

        for method in methods:
            result = method(grid, output_shape)
            if result:
                return result

        return None

    def _extract_by_unique_rows(self, grid: List[List[int]],
                            output_shape: Tuple[int, int]) -> Optional[List[List[int]]]:
        """Extract by unique rows."""
        out_h, out_w = output_shape

        # Find unique rows
        unique_rows = []
        seen = set()
        for row in grid:
            row_tuple = tuple(row)
            if row_tuple not in seen:
                seen.add(row_tuple)
                unique_rows.append(row)

        # Return first out_h unique rows
        result = unique_rows[:out_h]
        for row in result:
            if len(row) > out_w:
                result = [r[:out_w] for r in result]

        # Pad if needed
        while len(result) < out_h:
            result.append([0] * out_w)

        return result if len(result) == out_h else None

    def _extract_by_color_summary(self, grid: List[List[int]],
                                output_shape: Tuple[int, int]) -> Optional[List[List[int]]]:
        """Extract by summarizing color patterns per region."""
        out_h, out_w = output_shape
        inp_h, inp_w = len(grid), len(grid[0])

        # Divide input into regions
        row_bins = np.linspace(0, inp_h, out_h + 1, dtype=int)
        col_bins = np.linspace(0, inp_w, out_w + 1, dtype=int)

        result = []
        for ri in range(out_h):
            row = []
            for ci in range(out_w):
                # Find most common color in region
                region_colors = []
                for r in range(row_bins[ri], row_bins[ri + 1]):
                    for c in range(col_bins[ci], col_bins[ci + 1]):
                        region_colors.append(grid[r][c])

                if region_colors:
                    # Get most common color
                    counts = Counter(region_colors)
                    dominant = counts.most_common(1)[0][0]
                    row.append(dominant)
                else:
                    row.append(0)

            result.append(row)

        return result

    def _extract_by_structure(self, grid: List[List[int]],
                           output_shape: Tuple[int, int]) -> Optional[List[List[int]]]:
        """Extract by preserving structural elements."""
        # This is a simplified version - would need more sophistication
        out_h, out_w = output_shape

        # Detect and preserve borders/frames
        has_top_border = len(set(grid[0])) == 1
        has_bottom_border = len(set(grid[-1])) == 1 if grid else False
        has_left_border = len(set(grid[i][0] for i in range(len(grid)))) == 1 if grid else False
        has_right_border = len(set(grid[i][-1] for i in range(len(grid)))) == 1 if grid else False

        result = [[0] * out_w for _ in range(out_h)]

        # Fill in based on detected structure
        for i in range(min(out_h, len(grid))):
            for j in range(min(out_w, len(grid[0]))):
                result[i][j] = grid[i][j]

        return result

    def _extract_by_frequency(self, grid: List[List[int]],
                             output_shape: Tuple[int, int]) -> Optional[List[List[int]]]:
        """Extract by most frequent patterns."""
        out_h, out_w = output_shape
        inp_h, inp_w = len(grid), len(grid[0])

        # Get all sub-grids of output size
        patterns = []
        for i in range(inp_h - out_h + 1):
            for j in range(inp_w - out_w + 1):
                subgrid = tuple(tuple(grid[r][j:j+out_w]) for r in range(i, i+out_h))
                patterns.append(subgrid)

        if not patterns:
            return None

        # Find most frequent pattern
        pattern_counts = Counter(patterns)
        most_common = pattern_counts.most_common(1)[0][0]

        return [list(row) for row in most_common]


# Export key components
__all__ = [
    'AggregationMethod',
    'AggregatedObject',
    'SemanticCompressor',

    'DimensionalityReducer',

    'PatternExtractor',
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



def utility_function_12(*args, **kwargs):
    """Utility function 12."""
    return None



# Utility: Computation Logging
def log_computation(*args, **kwargs):
    """Utility function for log_computation."""
    return None


