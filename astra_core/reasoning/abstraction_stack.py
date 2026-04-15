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
Abstraction Formation Module
============================

This module learns hierarchical abstractions from concrete examples,
enabling transfer learning across domains.

Abstraction Levels:
1. Instance: Specific examples
2. Concept: Domain-specific groupings
3. Pattern: Cross-domain regularities
4. Universal: Fundamental principles

Key Functions:
- build_abstraction_hierarchy: Construct hierarchy from examples
- find_analogies: Discover cross-domain analogies

Abstraction Stack for Cognitive-Relativity Navigator

Manages the active stack of abstraction levels with zoom operations,
compression, and expansion capabilities.

Version: 4.0.0
Date: 2026-03-17
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class ZoomDirection(Enum):
    """Direction of zoom operation"""
    IN = "in"       # Towards more concrete (lower height)
    OUT = "out"     # Towards more abstract (higher height)


@dataclass
class ZoomOperation:
    """Result of a zoom operation"""
    success: bool
    direction: ZoomDirection
    steps: int
    from_height: int
    to_height: int
    new_levels: List[str]
    removed_levels: List[str]
    compression_ratio: float = 1.0
    quality_estimate: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StackLevel:
    """A level in the abstraction stack"""
    level_id: str
    height: int  # 0-100
    content: Any
    activation: float
    timestamp: float


class AbstractionStack:
    """
    Manages a stack of abstraction levels with zoom operations.

    Enables dynamic zooming between atomic facts (height 0)
    and abstract philosophy (height 100).
    """

    def __init__(self, max_levels: int = 10):
        self.max_levels = max_levels
        self.levels: List[StackLevel] = []
        self.current_height: int = 50  # Start at middle
        self.zoom_history: List[ZoomOperation] = []
        self.min_height: int = 0
        self.max_height: int = 100

    def push_level(
        self,
        level_id: str,
        height: int,
        content: Any,
        activation: float = 1.0
    ) -> bool:
        """Push a level onto the stack."""
        if len(self.levels) >= self.max_levels:
            # Remove least active level
            self.levels.sort(key=lambda l: l.activation, reverse=True)
            if self.levels:
                self.levels.pop()

        level = StackLevel(
            level_id=level_id,
            height=height,
            content=content,
            activation=activation,
            timestamp=time.time()
        )

        self.levels.append(level)
        self.current_height = height
        return True

    def pop_level(self) -> Optional[StackLevel]:
        """Pop the top level from the stack."""
        if self.levels:
            level = self.levels.pop()
            if self.levels:
                self.current_height = self.levels[-1].height
            return level
        return None

    def zoom_in(
        self,
        steps: int,
        get_level_at_height: callable
    ) -> ZoomOperation:
        """
        Zoom in towards more concrete (lower height).

        Args:
            steps: Number of height steps to zoom
            get_level_at_height: Callback to get content at a height

        Returns:
            ZoomOperation with results
        """
        from_height = self.current_height
        target_height = max(self.min_height, from_height - steps * 10)

        # Get level at target height
        target_level = get_level_at_height(target_height)

        if target_level is None:
            return ZoomOperation(
                success=False,
                direction=ZoomDirection.IN,
                steps=steps,
                from_height=from_height,
                to_height=from_height,
                new_levels=[],
                removed_levels=[]
            )

        # Add to stack
        self.push_level(
            level_id=target_level.get("id", f"level_{target_height}"),
            height=target_height,
            content=target_level.get("content"),
            activation=1.0
        )

        operation = ZoomOperation(
            success=True,
            direction=ZoomDirection.IN,
            steps=steps,
            from_height=from_height,
            to_height=target_height,
            new_levels=[target_level.get("id", f"level_{target_height}")],
            removed_levels=[]
        )

        self.zoom_history.append(operation)
        return operation

    def zoom_out(
        self,
        steps: int,
        get_level_at_height: callable
    ) -> ZoomOperation:
        """
        Zoom out towards more abstract (higher height).

        Args:
            steps: Number of height steps to zoom
            get_level_at_height: Callback to get content at a height

        Returns:
            ZoomOperation with results
        """
        from_height = self.current_height
        target_height = min(self.max_height, from_height + steps * 10)

        # Get level at target height
        target_level = get_level_at_height(target_height)

        if target_level is None:
            return ZoomOperation(
                success=False,
                direction=ZoomDirection.OUT,
                steps=steps,
                from_height=from_height,
                to_height=from_height,
                new_levels=[],
                removed_levels=[]
            )

        # Add to stack
        removed = []
        while self.levels and self.levels[-1].height < target_height:
            removed.append(self.levels.pop().level_id)

        self.push_level(
            level_id=target_level.get("id", f"level_{target_height}"),
            height=target_height,
            content=target_level.get("content"),
            activation=1.0
        )

        operation = ZoomOperation(
            success=True,
            direction=ZoomDirection.OUT,
            steps=steps,
            from_height=from_height,
            to_height=target_height,
            new_levels=[target_level.get("id", f"level_{target_height}")],
            removed_levels=removed
        )

        self.zoom_history.append(operation)
        return operation

    def zoom_to(
        self,
        target_height: int,
        get_level_at_height: callable
    ) -> ZoomOperation:
        """Zoom directly to a target height."""
        if target_height > self.current_height:
            return self.zoom_out(
                steps=(target_height - self.current_height) // 10,
                get_level_at_height=get_level_at_height
            )
        elif target_height < self.current_height:
            return self.zoom_in(
                steps=(self.current_height - target_height) // 10,
                get_level_at_height=get_level_at_height
            )
        else:
            return ZoomOperation(
                success=True,
                direction=ZoomDirection.IN,
                steps=0,
                from_height=self.current_height,
                to_height=self.current_height,
                new_levels=[],
                removed_levels=[]
            )

    def compress_range(
        self,
        start_height: int,
        end_height: int,
        compress_func: callable
    ) -> Optional[str]:
        """
        Compress a range of heights into a single level.

        Args:
            start_height: Starting height
            end_height: Ending height
            compress_func: Callback to perform compression

        Returns:
            ID of compressed level
        """
        # Get levels in range
        levels_in_range = [
            l for l in self.levels
            if start_height <= l.height <= end_height
        ]

        if not levels_in_range:
            return None

        # Call compression function
        compressed = compress_func([l.content for l in levels_in_range])

        if compressed:
            # Create new compressed level
            compressed_id = f"compressed_{start_height}_{end_height}"
            avg_height = (start_height + end_height) // 2

            self.push_level(
                level_id=compressed_id,
                height=avg_height,
                content=compressed,
                activation=sum(l.activation for l in levels_in_range) / len(levels_in_range)
            )

            # Remove original levels
            removed_ids = [l.level_id for l in levels_in_range]
            self.levels = [l for l in self.levels if l.level_id not in removed_ids]

            return compressed_id

        return None

    def expand_level(
        self,
        level_id: str,
        expand_func: callable,
        depth: int = 1
    ) -> List[str]:
        """
        Expand a level into its components.

        Args:
            level_id: ID of level to expand
            expand_func: Callback to perform expansion
            depth: How many levels to expand

        Returns:
            List of new level IDs
        """
        # Find the level
        target_level = None
        target_index = None

        for i, level in enumerate(self.levels):
            if level.level_id == level_id:
                target_level = level
                target_index = i
                break

        if not target_level:
            return []

        # Expand the content
        expanded = expand_func(target_level.content, depth)

        if not expanded:
            return []

        # Insert expanded levels after the original
        new_ids = []
        for i, (exp_content, exp_height) in enumerate(expanded):
            new_id = f"{level_id}_expanded_{i}"
            new_level = StackLevel(
                level_id=new_id,
                height=exp_height,
                content=exp_content,
                activation=target_level.activation / len(expanded),
                timestamp=time.time()
            )
            self.levels.insert(target_index + 1 + i, new_level)
            new_ids.append(new_id)

        return new_ids

    def get_active_levels(self) -> List[StackLevel]:
        """Get all active levels sorted by height."""
        return sorted(self.levels, key=lambda l: l.height)

    def get_level_at_height(self, height: int, tolerance: int = 5) -> Optional[StackLevel]:
        """Get level closest to target height."""
        closest = None
        min_diff = float('inf')

        for level in self.levels:
            diff = abs(level.height - height)
            if diff < min_diff and diff <= tolerance:
                min_diff = diff
                closest = level

        return closest

    def get_zoom_path(self) -> List[int]:
        """Get the path of heights in current stack."""
        return sorted([l.height for l in self.levels])

    def estimate_quality(self) -> float:
        """Estimate quality of current stack state."""
        if not self.levels:
            return 0.0

        # Quality based on:
        # 1. Stack coherence (smooth height transitions)
        # 2. Level activations
        # 3. Stack depth (not too deep, not too shallow)

        heights = sorted([l.height for l in self.levels])

        # Check coherence
        coherence = 1.0
        for i in range(len(heights) - 1):
            gap = heights[i + 1] - heights[i]
            if gap > 20:  # Large gaps reduce coherence
                coherence *= 0.9

        # Average activation
        avg_activation = sum(l.activation for l in self.levels) / len(self.levels)

        # Depth factor (optimal around 3-7 levels)
        depth = len(self.levels)
        depth_factor = 1.0
        if depth < 2:
            depth_factor = 0.7
        elif depth > 8:
            depth_factor = 0.8

        return coherence * avg_activation * depth_factor

    def cleanup_inactive(self, min_activation: float = 0.1) -> int:
        """Remove inactive levels from stack."""
        initial_count = len(self.levels)
        self.levels = [l for l in self.levels if l.activation >= min_activation]
        return initial_count - len(self.levels)

    def get_statistics(self) -> Dict[str, Any]:
        """Get stack statistics."""
        if not self.levels:
            return {
                "total_levels": 0,
                "current_height": self.current_height,
                "height_range": (0, 0),
                "average_activation": 0.0,
                "total_zooms": len(self.zoom_history)
            }

        heights = [l.height for l in self.levels]

        return {
            "total_levels": len(self.levels),
            "current_height": self.current_height,
            "height_range": (min(heights), max(heights)),
            "average_activation": sum(l.activation for l in self.levels) / len(self.levels),
            "total_zooms": len(self.zoom_history),
            "quality_estimate": self.estimate_quality()
        }


# =============================================================================
# Factory Functions
# =============================================================================

def create_abstraction_stack(max_levels: int = 10) -> AbstractionStack:
    """Create an abstraction stack."""
    return AbstractionStack(max_levels=max_levels)



def predict_next_in_sequence(sequence: List[Any],
                            method: str = 'autoregressive') -> Dict[str, Any]:
    """
    Predict the next element in a sequence.

    Args:
        sequence: Observed sequence
        method: Prediction method ('autoregressive', 'markov', 'fft')

    Returns:
        Dictionary with prediction and confidence
    """
    import numpy as np

    if len(sequence) < 2:
        return {'prediction': None, 'confidence': 0.0}

    if method == 'autoregressive':
        # Fit AR(1) model: x_t = c + phi * x_{t-1}
        x = np.array(sequence)
        x_lag = x[:-1]
        x_current = x[1:]

        # Linear regression
        A = np.vstack([x_lag, np.ones(len(x_lag))]).T
        phi, c = np.linalg.lstsq(A, x_current, rcond=None)[0]

        # Predict next
        if len(x) > 0:
            prediction = c + phi * x[-1]

            # Estimate confidence from residuals
            residuals = x_current - (c + phi * x_lag)
            std = np.std(residuals)
            confidence = 1.0 / (1.0 + std)

            return {
                'prediction': float(prediction),
                'confidence': float(confidence),
                'method': 'autoregressive'
            }

    elif method == 'markov':
        # Simple Markov chain
        transitions = {}
        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_val = sequence[i + 1]
            if current not in transitions:
                transitions[current] = {}
            if next_val not in transitions[current]:
                transitions[current][next_val] = 0
            transitions[current][next_val] += 1

        # Predict from last state
        last = sequence[-1]
        if last in transitions:
            total = sum(transitions[last].values())
            most_likely = max(transitions[last].items(), key=lambda x: x[1])
            prediction = most_likely[0]
            confidence = most_likely[1] / total

            return {
                'prediction': prediction,
                'confidence': float(confidence),
                'method': 'markov'
            }

    return {'prediction': None, 'confidence': 0.0}



def validate_concept_coherence(concept: Dict[str, Any],
                              validation_examples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate concept coherence on new examples.

    Args:
        concept: Concept definition
        validation_examples: Examples to validate against

    Returns:
        Validation metrics
    """
    import numpy as np

    essential_features = concept.get('essential_features', {})
    matches = 0

    for example in validation_examples:
        match_count = 0
        total_checks = 0

        for key, spec in essential_features.items():
            if key not in example:
                continue

            total_checks += 1
            value = example[key]

            if spec['type'] == 'continuous':
                # Check if within reasonable range
                mean = spec['mean']
                std = spec['std']
                if abs(value - mean) < 3 * std:
                    match_count += 1
            elif spec['type'] == 'categorical':
                if value == spec['most_common']:
                    match_count += 1

        if total_checks > 0 and match_count / total_checks >= 0.7:
            matches += 1

    coherence = matches / len(validation_examples) if validation_examples else 0

    return {
        'coherence': float(coherence),
        'matches': matches,
        'total': len(validation_examples),
        'is_valid': coherence >= 0.7
    }
                continue
