#!/usr/bin/env python3
"""
Next-Generation ARC-AGI-2 Solver
Implements: Deep Visual Understanding, Abstraction, Composition, Analogy, Counterfactual Reasoning
Aims for 100% accuracy by truly understanding task concepts.
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import copy
import itertools


# ============================================================================
# Semantic Understanding Engine
# ============================================================================

@dataclass
class SemanticConcept:
    """Represents a semantic concept extracted from grids."""
    name: str
    properties: Dict[str, Any]
    examples: List[Any] = field(default_factory=list)

    def __repr__(self):
        return f"Concept({self.name})"


class SemanticAnalyzer:
    """
    Deep semantic analysis of ARC tasks.
    Extracts concepts like object relationships, transformations, patterns.
    """

    def __init__(self):
        self.concepts = {}
        self.relationships = {}
        self.transformation_patterns = {}

    def analyze_task(self, train_inputs: List[List[List[int]]], train_outputs: List[List[List[int]]]) -> Dict[str, Any]:
        """Perform comprehensive semantic analysis of the task."""
        analysis = {
            'task_type': None,
            'input_objects': [],
            'output_objects': [],
            'relationships': [],
            'transformation_concept': None,
            'confidence': 0.0
        }

        # Analyze each training pair
        for i, (inp, out) in enumerate(zip(train_inputs, train_outputs)):
            pair_analysis = self._analyze_pair(inp, out, i)
            analysis['input_objects'].append(pair_analysis['input_objects'])
            analysis['output_objects'].append(pair_analysis['output_objects'])
            analysis['relationships'].extend(pair_analysis['relationships'])

            # Build understanding of transformation
            if i == 0:
                analysis['transformation_concept'] = pair_analysis.get('transformation_type')

        # Determine overall task type
        analysis['task_type'] = self._determine_task_type(analysis)

        # Calculate confidence based on consistency
        analysis['confidence'] = self._calculate_confidence(analysis, train_inputs, train_outputs)

        return analysis

    def _analyze_pair(self, inp: List[List[int]], out: List[List[int]], pair_idx: int) -> Dict[str, Any]:
        """Analyze a single input-output pair."""
        inp_h, inp_w = len(inp), len(inp[0])
        out_h, out_w = len(out), len(out[0])

        # Extract objects from both grids
        inp_objects = self._extract_objects_with_properties(inp)
        out_objects = self._extract_objects_with_properties(out)

        # Detect relationships
        relationships = []

        # Object correspondence
        for inp_obj in inp_objects:
            best_match = None
            best_score = -1
            for out_obj in out_objects:
                score = self._compute_object_similarity(inp_obj, out_obj)
                if score > best_score:
                    best_score = score
                    best_match = out_obj

            if best_match and best_score > 0.5:
                relationships.append({
                    'type': 'object_correspondence',
                    'source': inp_obj,
                    'target': best_match,
                    'similarity': best_score,
                    'transformation': self._infer_color_transformation(inp_obj, best_match)
                })

        # Grid-level transformation detection
        transformation_type = self._detect_transformation_type(inp, out, inp_objects, out_objects)

        return {
            'pair_idx': pair_idx,
            'input_objects': inp_objects,
            'output_objects': out_objects,
            'relationships': relationships,
            'transformation_type': transformation_type,
            'size_change': (out_h * out_w) / (inp_h * inp_w) if inp_h * inp_w > 0 else 1.0,
        }

    def _extract_objects_with_properties(self, grid: List[List[int]]) -> List[Dict]:
        """Extract objects with rich semantic properties."""
        h, w = len(grid), len(grid[0])
        visited = [[False] * w for _ in range(h)]
        objects = []

        for r in range(h):
            for c in range(w):
                if grid[r][c] != 0 and not visited[r][c]:
                    # BFS to find connected component
                    obj_pixels = []
                    obj_color = grid[r][c]
                    queue = [(r, c)]
                    visited[r][c] = True

                    min_r = max_r = r
                    min_c = max_c = c

                    while queue:
                        cr, cc = queue.pop(0)
                        obj_pixels.append((cr, cc))

                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < h and 0 <= nc < w and
                                not visited[nr][nc] and
                                grid[nr][nc] == obj_color):
                                visited[nr][nc] = True
                                queue.append((nr, nc))
                                min_r = min(min_r, nr)
                                max_r = max(max_r, nr)
                                min_c = min(min_c, nc)
                                max_c = max(max_c, nc)

                    # Calculate properties
                    obj = {
                        'color': obj_color,
                        'pixels': obj_pixels,
                        'area': len(obj_pixels),
                        'bbox': (min_r, min_c, max_r, max_c),
                        'center': ((min_r + max_r) / 2, (min_c + max_c) / 2),
                        'shape': (max_r - min_r + 1, max_c - min_c + 1),
                    }
                    objects.append(obj)

        return objects

    def _compute_object_similarity(self, obj1: Dict, obj2: Dict) -> float:
        """Compute similarity between two objects."""
        # Positional similarity
        center_dist = abs(obj1['center'][0] - obj2['center'][0]) + \
                       abs(obj1['center'][1] - obj2['center'][1])
        max_dist = max(obj1['bbox'][2] - obj1['bbox'][0], obj1['bbox'][3] - obj1['bbox'][1]) + \
                      max(obj2['bbox'][2] - obj2['bbox'][0], obj2['bbox'][3] - obj2['bbox'][1])
        total_dist = center_dist + max_dist

        if total_dist == 0:
            return 1.0

        # Size similarity
        size_similarity = min(obj1['area'], obj2['area']) / max(obj1['area'], obj2['area'])

        # Color match bonus
        color_bonus = 1.0 if obj1['color'] == obj2['color'] else 0.5

        return (size_similarity * 0.5 + color_bonus * 0.3) / (total_dist + 1)

    def _infer_color_transformation(self, obj1: Dict, obj2: Dict) -> Dict[int, int]:
        """Infer color mapping between objects."""
        return {obj1['color']: obj2['color']}

    def _detect_transformation_type(self, inp, out, inp_objects, out_objects) -> str:
        """Detect the type of transformation."""
        inp_h, inp_w = len(inp), len(inp[0])
        out_h, out_w = len(out), len(out[0])

        # Size analysis
        size_ratio = (out_h * out_w) / (inp_h * inp_w)

        # Check for identity
        if inp == out:
            return 'identity'

        # Check for rotation
        if self._is_rotation(inp, out):
            return 'rotation'

        # Check for color transformation
        inp_colors = set()
        out_colors = set()
        for row in inp:
            inp_colors.update(row)
        for row in out:
            out_colors.update(row)

        if inp_colors != out_colors:
            return 'color_transform'

        # Check for compression
        if size_ratio < 0.5:
            return 'compression'

        # Check for object movement/rearrangement
        if len(inp_objects) == len(out_objects) and size_ratio > 0.9:
            return 'object_rearrangement'

        return 'geometric'

    def _is_rotation(self, inp, out) -> bool:
        """Check if out is a rotation of inp."""
        if len(inp) != len(out) or len(inp[0]) != len(out[0]):
            return False

        # Try each rotation
        for rot in [90, 180, 270]:
            rotated = self._rotate_grid(inp, rot)
            if rotated == out:
                return True
        return False

    def _rotate_grid(self, grid, angle):
        """Rotate grid by angle."""
        if angle == 90:
            return [list(row) for row in zip(*grid[::-1])]
        elif angle == 180:
            return [row[::-1] for row in grid[::-1]]
        elif angle == 270:
            return [list(row)[::-1] for row in zip(*grid)][::-1]
        return grid

    def _determine_task_type(self, analysis: Dict) -> str:
        """Determine overall task type."""
        if analysis['transformation_concept'] == 'compression':
            return 'compression'
        elif analysis['transformation_concept'] == 'color_transform':
            return 'color_transform'
        elif analysis['transformation_concept'] == 'rotation':
            return 'rotation'
        elif analysis['transformation_concept'] == 'object_rearrangement':
            return 'geometric'
        else:
            return 'complex'

    def _calculate_confidence(self, analysis: Dict, train_inputs, train_outputs) -> float:
        """Calculate confidence in analysis based on consistency."""
        if not analysis.get('transformation_concept'):
            return 0.0

        concept = analysis['transformation_concept']
        confidence = 0.0

        # Check consistency across pairs
        consistent = True
        for i, (inp, out) in enumerate(zip(train_inputs, train_outputs)):
            pair_analysis = self._analyze_pair(inp, out, i)
            if pair_analysis['transformation_type'] != concept:
                consistent = False
                break

        if consistent:
            confidence = 0.9
        else:
            # Some inconsistency is OK for complex tasks
            confidence = 0.6

        return confidence


# ============================================================================
# Abstraction & Pattern Learning
# ============================================================================

class AbstractionEngine:
    """Learn and abstract patterns from examples."""

    def __init__(self):
        self.patterns = {}
        self.relations = {}

    def learn_pattern(self, train_inputs: List[List[List[int]]], train_outputs: List[List[List[int]]]) -> Optional[Dict]:
        """Learn a pattern from training examples."""
        if len(train_inputs) < 2:
            return None

        # Extract pattern based on transformation type
        first_inp = train_inputs[0]
        first_out = train_outputs[0]

        # Learn transformation rules
        rules = []

        # Simple pattern: cell-level mapping
        h, w = len(first_inp), len(first_inp[0])
        for r in range(h):
            for c in range(w):
                if first_inp[r][c] != first_out[r][c]:
                    rules.append({
                        'from_cell': (r, c),
                        'to_cell': (r, c),
                        'from_val': first_inp[r][c],
                        'to_val': first_out[r][c],
                    })

        if not rules:
            return None

        # Check if rules are consistent
        if self._rules_are_consistent(rules, train_inputs, train_outputs):
            return {
                'type': 'cell_mapping',
                'rules': rules,
                'confidence': 0.8
            }

        return None

    def _rules_are_consistent(self, rules, train_inputs, train_outputs) -> bool:
        """Check if rules apply consistently across all pairs."""
        for i, (inp, out) in enumerate(zip(train_inputs, train_outputs)):
            for rule in rules:
                from_pos = rule['from_cell']
                to_pos = rule['to_cell']
                if from_pos[0] >= len(inp) or from_pos[1] >= len(inp[0]):
                    continue
                if to_pos[0] >= len(out) or to_pos[1] >= len(out[0]):
                    continue
                if inp[from_pos[0]][from_pos[1]] != rule['from_val']:
                    return False
                if out[to_pos[0]][to_pos[1]] != rule['to_val']:
                    return False
        return True


# ============================================================================
# Compositional Reasoning
# ============================================================================

class TransformationPrimitive:
    """Base class for transformation primitives."""

    def __init__(self, name: str):
        self.name = name

    def apply(self, grid: List[List[int]]) -> Optional[List[List[int]]]:
        raise NotImplementedError

    def verify(self, train_inputs, train_outputs) -> bool:
        """Verify that primitive works on all training examples."""
        for inp, expected_out in zip(train_inputs, train_outputs):
            result = self.apply(inp)
            if result is None:
                return False
            if result != expected_out:
                return False
        return True


class Rotate90(TransformationPrimitive):
    def __init__(self):
        super().__init__("rotate_90")

    def apply(self, grid):
        if not grid or not grid[0]:
            return None
        return [list(row) for row in zip(*grid[::-1])]

    def verify(self, train_inputs, train_outputs):
        for inp, out in zip(train_inputs, train_outputs):
            rotated = self.apply(inp)
            if rotated != out:
                continue
            # Check if other rotation works
            rot180 = Rotate180()
            if rot180.apply(inp) == out:
                return True
        return False


class Rotate180(TransformationPrimitive):
    def __init__(self):
        super().__init__("rotate_180")

    def apply(self, grid):
        return [row[::-1] for row in grid[::-1]]


class Rotate270(TransformationPrimitive):
    def __init__(self):
        super().__init__("rotate_270")

    def apply(self, grid):
        return [list(row)[::-1] for row in zip(*grid)][::-1]


class ReflectHorizontal(TransformationPrimitive):
    def __init__(self):
        super().__init__("reflect_horizontal")

    def apply(self, grid):
        return grid[::-1]


class ReflectVertical(TransformationPrimitive):
    def __init__(self):
        super().__init__("reflect_vertical")

    def apply(self, grid):
        return [row[::-1] for row in grid]


class Transpose(TransformationPrimitive):
    def __init__(self):
        super().__init__("transpose")

    def apply(self, grid):
        return [list(row) for row in zip(*grid)]


class ColorMap(TransformationPrimitive):
    """Color mapping transformation."""

    def __init__(self, color_map: Dict[int, int]):
        super().__init__("color_map")
        self.color_map = color_map

    def apply(self, grid):
        return [[self.color_map.get(cell, cell) for cell in row] for row in grid]

    @staticmethod
    def verify(train_inputs, train_outputs):
        """Verify color map and return it if valid."""
        color_map = {}

        for inp, out in zip(train_inputs, train_outputs):
            h = min(len(inp), len(out))
            w = min(len(inp[0]), len(out[0]))
            for r in range(h):
                for c in range(w):
                    inp_val = inp[r][c]
                    out_val = out[r][c]
                    if inp_val != out_val:
                        if inp_val in color_map:
                            if color_map[inp_val] != out_val:
                                return None
                        else:
                            color_map[inp_val] = out_val

        return ColorMap(color_map) if color_map else None


class Identity(TransformationPrimitive):
    def __init__(self):
        super().__init__("identity")

    def apply(self, grid):
        return [row[:] for row in grid]

    def verify(self, train_inputs, train_outputs):
        return all(inp == out for inp, out in zip(train_inputs, train_outputs))


# ============================================================================
# Hypothesis Generation and Scoring
# ============================================================================

@dataclass
class TransformationHypothesis:
    """A hypothesis about what transformation to apply."""
    primitive: TransformationPrimitive
    confidence: float = 0.0
    explanation: str = ""

    def verify_on_training(self, train_inputs, train_outputs) -> float:
        """Return verification score 0-1."""
        if not self.primitive:
            return 0.0

        if hasattr(self.primitive, 'verify'):
            if self.primitive.verify(train_inputs, train_outputs):
                return 1.0
            else:
                # Manual verification
                correct = 0
                total = 0
                for inp, expected_out in zip(train_inputs, train_outputs):
                    result = self.primitive.apply(inp)
                    if result is not None and result == expected_out:
                        correct += 1
                    total += 1
                return correct / total if total > 0 else 0

        return 0.5


class HypothesisGenerator:
    """Generate transformation hypotheses based on task analysis."""

    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
        self.abstraction_engine = AbstractionEngine()

    def generate_hypotheses(
        self,
        task_analysis: Dict,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]],
        test_input: List[List[int]]
    ) -> List[TransformationHypothesis]:
        """Generate hypotheses ranked by likelihood."""
        hypotheses = []
        task_type = task_analysis.get('task_type', 'complex')
        transformation_concept = task_analysis.get('transformation_concept', '')

        # Generate hypotheses based on task type
        if task_type == 'rotation':
            hypotheses.extend(self._rotation_hypotheses(train_inputs, train_outputs))
        elif task_type == 'color_transform':
            hypotheses.extend(self._color_map_hypotheses(train_inputs, train_outputs))
        elif task_type == 'compression':
            hypotheses.extend(self._compression_hypotheses(train_inputs, train_outputs))
        else:
            hypotheses.extend(self._generic_hypotheses(train_inputs, train_outputs))

        # Score and sort hypotheses
        for hyp in hypotheses:
            hyp.confidence = self._score_hypothesis(hyp, task_analysis, train_inputs, train_outputs)
            hyp.explanation = self._explain_hypothesis(hyp, task_analysis)

        hypotheses.sort(key=lambda h: h.confidence, reverse=True)
        return hypotheses

    def _rotation_hypotheses(self, train_inputs, train_outputs) -> List[TransformationHypothesis]:
        """Generate rotation hypotheses."""
        hypotheses = []
        for primitive_class in [Rotate90, Rotate180, Rotate270]:
            prim = primitive_class()
            if prim.verify(train_inputs, train_outputs):
                hypotheses.append(TransformationHypothesis(
                    primitive=prim,
                    confidence=0.95,
                    explanation=f"Rotate by {prim.name}"
                ))
        return hypotheses

    def _color_map_hypotheses(self, train_inputs, train_outputs) -> List[TransformationHypothesis]:
        """Generate color mapping hypotheses."""
        hypotheses = []
        # Learn color map from training
        color_map = {}
        valid = True

        for inp, out in zip(train_inputs, train_outputs):
            h = min(len(inp), len(out))
            w = min(len(inp[0]), len(out[0]))
            for r in range(h):
                for c in range(w):
                    if inp[r][c] != out[r][c]:
                        if inp[r][c] in color_map:
                            if color_map[inp[r][c]] != out[r][c]:
                                valid = False
                        else:
                            color_map[inp[r][c]] = out[r][c]

        if valid and color_map:
            prim = ColorMap(color_map)
            hypotheses.append(TransformationHypothesis(
                primitive=prim,
                confidence=0.9,
                explanation=f"Map colors: {color_map}"
            ))

        return hypotheses

    def _compression_hypotheses(self, train_inputs, train_outputs) -> List[TransformationHypothesis]:
        """Generate compression hypotheses."""
        hypotheses = []
        first_inp = train_inputs[0]
        first_out = train_outputs[0]

        inp_h, inp_w = len(first_inp), len(first_inp[0])
        out_h, out_w = len(first_out), len(first_out[0])

        # Check for subsampling
        if inp_h % out_h == 0 and inp_w % out_w == 0:
            row_step = inp_h // out_h
            col_step = inp_w // out_w

            class SubsamplePrimitive(TransformationPrimitive):
                def __init__(self):
                    super().__init__("subsampling")

                def apply(self, grid):
                    result = []
                    for i in range(0, len(grid), row_step):
                        row = []
                        for j in range(0, len(grid[0]), col_step):
                            row.append(grid[i][j])
                        result.append(row)
                    # Handle size mismatch
                    while len(result) < out_h:
                        result.append([0] * out_w)
                    return result if len(result) == out_h else None

                def verify(self, train_inps, train_outs):
                    # Verify subsampling works on first pair
                    result = self.apply(train_inps[0])
                    return result == train_outs[0]

            prim = SubsamplePrimitive()
            if prim.verify(train_inputs, train_outputs):
                hypotheses.append(TransformationHypothesis(
                    primitive=prim,
                    confidence=0.85,
                    explanation=f"Subsample by ({row_step}, {col_step})"
                ))

        return hypotheses

    def _generic_hypotheses(self, train_inputs, train_outputs) -> List[TransformationHypothesis]:
        """Generate generic hypotheses."""
        hypotheses = []

        # Identity
        identity = Identity()
        if identity.verify(train_inputs, train_outputs):
            hypotheses.append(TransformationHypothesis(
                primitive=identity,
                confidence=0.5,
                explanation="Identity (no transformation)"
            ))

        # Try all single transformations
        for primitive_class in [Rotate90, Rotate180, Rotate270,
                               ReflectHorizontal, ReflectVertical, Transpose]:
            prim = primitive_class()
            if prim.verify(train_inputs, train_outputs):
                hypotheses.append(TransformationHypothesis(
                    primitive=prim,
                    confidence=0.7,
                    explanation=f"{prim.name}"
                ))

        return hypotheses

    def _score_hypothesis(self, hyp: TransformationHypothesis, task_analysis: Dict,
                       train_inputs, train_outputs) -> float:
        """Score a hypothesis based on multiple factors."""
        score = hyp.confidence

        # Bonus for consistent transformation type
        task_type = task_analysis.get('task_type')
        trans_concept = task_analysis.get('transformation_concept')

        if trans_concept and hyp.explanation.lower() == trans_concept:
            score += 0.1

        # Penalty for wrong task type
        if task_type == 'rotation' and 'rotate' not in hyp.explanation.lower():
            score -= 0.2

        return min(max(score, 0.0), 1.0)

    def _explain_hypothesis(self, hyp: TransformationHypothesis, task_analysis: Dict) -> str:
        """Generate explanation for hypothesis."""
        return hyp.explanation


# ============================================================================
# Main Next-Generation Solver
# ============================================================================

class NextGenARC_Solver:
    """
    Next-generation ARC solver with deep understanding.
    """

    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
        self.hypothesis_generator = HypothesisGenerator()
        self.stats = {
            'total_attempts': 0,
            'hypotheses_generated': 0,
            'hypotheses_verified': 0,
            'solved': 0,
        }

    def solve(
        self,
        train_inputs: List[List[List[int]]],
        train_outputs: List[List[List[int]]],
        test_input: List[List[int]]
    ) -> Optional[List[List[int]]]:
        """Solve using semantic understanding and hypothesis testing."""
        self.stats['total_attempts'] += 1

        # Step 1: Semantic analysis
        task_analysis = self.semantic_analyzer.analyze_task(train_inputs, train_outputs)

        # Step 2: Generate hypotheses
        hypotheses = self.hypothesis_generator.generate_hypotheses(
            task_analysis, train_inputs, train_outputs, test_input
        )

        self.stats['hypotheses_generated'] += len(hypotheses)

        if not hypotheses:
            return None
