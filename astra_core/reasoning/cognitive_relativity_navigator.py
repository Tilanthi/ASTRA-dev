"""
Cognitive-Relativity Navigator (CRN) for STAN_XI_ASTRO V4.0

Inspired by: Cognitive relativity and perceptual dimensional modelling

Design Concept:
A modular system that lets AGI "zoom in/out" cognitively — switching between
atomic facts and abstract philosophy dynamically. This is built into a framework
of multi-layered inference stacks that can compress or expand their abstraction
range on demand.

Use Case:
In a philosophical debate about ethics, the CRN can switch between a moral philosophy
layer (Kantian vs utilitarian reasoning), a historical example layer, and a current
event layer, synthesizing new arguments without predefined rules.

Version: 4.0.0
Date: 2026-03-17
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class AbstractionHeight(Enum):
    """Standard abstraction levels"""
    ATOMIC_FACTS = 0          # Concrete, specific observations
    INSTANCE_DATA = 10        # Specific examples and cases
    PATTERNS = 20             # Regularities and correlations
    CONCEPTS = 30             # Domain-specific concepts
    PRINCIPLES = 40           # Domain principles and rules
    THEORIES = 50             # Coherent theoretical frameworks
    PARADIGMS = 60            # Worldview and foundational assumptions
    PHILOSOPHY = 70           # Philosophical frameworks
    METAPHYSICS = 80          # Existential and ontological questions
    PURE_ABSTRACTION = 100    # Maximum abstraction


class AbstractionContent:
    """Content at an abstraction level"""

    def __init__(self, content: Any, level: int, description: str = ""):
        self.content = content
        self.level = level
        self.description = description
        self.compression_ratio = 1.0  # Information preservation

    def compress(self, target_level: int) -> 'AbstractionContent':
        """Compress content to target abstraction level."""
        if target_level <= self.level:
            # Going to more concrete: expand (can't really do this without more data)
            return AbstractionContent(
                self.content,
                target_level,
                f"Compressed from level {self.level}"
            )
        else:
            # Going to more abstract: compress
            compressed = self._summarize(self.content, self.level, target_level)
            return AbstractionContent(
                compressed,
                target_level,
                f"Compressed from level {self.level}"
            )

    def _summarize(self, content: Any, from_level: int, to_level: int) -> str:
        """Summarize content when moving to higher abstraction."""
        compression_factor = (to_level - from_level) / 100.0

        if isinstance(content, dict):
            # Summarize dictionary
            n_items = len(content)
            return f"System with {n_items} components at {compression_factor:.1%} compression"
        elif isinstance(content, list):
            return f"Collection of {len(content)} items"
        elif isinstance(content, str):
            # Summarize text
            words = content.split()
            n_chars = min(len(words), int(len(words) * (1 - compression_factor)))
            return " ".join(words[:n_chars])
        else:
            return str(content)[:int(len(str(content)) * (1 - compression_factor))]


@dataclass
class AbstractionLevel:
    """A level in the abstraction hierarchy"""
    level_id: str
    height: int  # 0 (atomic) to 100 (philosophy)
    content: AbstractionContent
    children: List[str]  # IDs of lower-level abstractions
    parent: Optional[str]  # ID of higher-level abstraction
    compression_ratio: float = 1.0  # Information preservation (0-1)
    temporal_scale: Optional[str] = None  # Associated temporal scale
    domain: Optional[str] = None  # Associated domain

    def can_expand(self) -> bool:
        """Check if this level can be expanded (has children)."""
        return len(self.children) > 0

    def can_compress(self) -> bool:
        """Check if this level can be compressed (has parent)."""
        return self.parent is not None


@dataclass
class ZoomOperation:
    """A zoom operation between abstraction levels"""
    from_level: int
    to_level: int
    operation_type: str  # "zoom_in", "zoom_out", "compress", "expand"
    path: List[int]  # Levels traversed
    disruption_cost: float
    timestamp: float


@dataclass
class NavigationResult:
    """Result of navigating a query"""
    query: str
    target_abstraction: int
    actual_abstraction: int
    result: Any
    reasoning_trace: List[str]
    confidence: float
    levels_visited: List[int]


@dataclass
class MultiLevelResult:
    """Result of multi-level inference"""
    query: str
    results_by_level: Dict[int, Any]
    synthesized_result: Any
    coherence_score: float
    recommended_abstraction: int


class AbstractionStack:
    """
    Stack of abstraction levels for current reasoning.

    Manages the current focus and available zoom operations.
    """

    def __init__(self, max_levels: int = 10):
        self.levels: Dict[int, AbstractionLevel] = {}
        self.current_focus: int = 50  # Middle level (THEORIES)
        self.zoom_speed: float = 1.0
        self.max_levels = max_levels
        self.zoom_history: List[ZoomOperation] = []

    def add_level(self, level: AbstractionLevel) -> None:
        """Add an abstraction level to the stack."""
        self.levels[level.height] = level

    def zoom_in(self, steps: int) -> ZoomOperation:
        """
        Move to more concrete levels (decrease height).

        Args:
            steps: Number of abstraction levels to zoom in

        Returns:
            ZoomOperation describing the transition
        """
        target_level = max(0, self.current_focus - steps * 10)
        path = list(range(self.current_focus, target_level, -10 * np.sign(steps)))

        operation = ZoomOperation(
            from_level=self.current_focus,
            to_level=target_level,
            operation_type="zoom_in",
            path=path,
            disruption_cost=abs(steps) * 0.1,
            timestamp=datetime.now().timestamp()
        )

        self.current_focus = target_level
        self.zoom_history.append(operation)

        return operation

    def zoom_out(self, steps: int) -> ZoomOperation:
        """
        Move to more abstract levels (increase height).

        Args:
            steps: Number of abstraction levels to zoom out

        Returns:
            ZoomOperation describing the transition
        """
        target_level = min(100, self.current_focus + steps * 10)
        path = list(range(self.current_focus, target_level, 10 * np.sign(steps)))

        operation = ZoomOperation(
            from_level=self.current_focus,
            to_level=target_level,
            operation_type="zoom_out",
            path=path,
            disruption_cost=abs(steps) * 0.1,
            timestamp=datetime.now().timestamp()
        )

        self.current_focus = target_level
        self.zoom_history.append(operation)

        return operation

    def compress_range(
        self,
        start_level: int,
        end_level: int
    ) -> AbstractionLevel:
        """
        Compress multiple levels into single abstraction.

        Args:
            start_level: Starting height
            end_level: Ending height

        Returns:
            Compressed AbstractionLevel
        """
        # Collect all levels in range
        levels_in_range = [
            self.levels[h] for h in range(start_level, end_level + 1, 10)
            if h in self.levels
        ]

        if not levels_in_range:
            # Create placeholder
            return AbstractionLevel(
                level_id=f"compressed_{start_level}_{end_level}",
                height=(start_level + end_level) // 2,
                content=AbstractionContent(
                    f"Compression of empty range {start_level}-{end_level}",
                    (start_level + end_level) // 2
                ),
                children=[],
                parent=None
            )

        # Merge content
        merged_content = self._merge_content(levels_in_range)

        # Create compressed level
        compressed = AbstractionLevel(
            level_id=f"compressed_{start_level}_{end_level}",
            height=(start_level + end_level) // 2,
            content=merged_content,
            children=[str(l.height) for l in levels_in_range],
            parent=None,
            compression_ratio=0.7
        )

        return compressed

    def expand_level(self, level: AbstractionLevel) -> List[AbstractionLevel]:
        """
        Expand single level into multiple detailed levels.

        Args:
            level: Level to expand

        Returns:
            List of expanded AbstractionLevels
        """
        if not level.children:
            # Can't expand - return single level
            return [level]

        expanded = []
        for child_id in level.children:
            if int(child_id) in self.levels:
                expanded.append(self.levels[int(child_id)])
            else:
                # Create placeholder
                expanded.append(AbstractionLevel(
                    level_id=f"expanded_{child_id}",
                    height=int(child_id),
                    content=AbstractionContent(f"Expansion of {level.level_id}", int(child_id)),
                    children=[],
                    parent=level.level_id
                ))

        return expanded

    def _merge_content(
        self,
        levels: List[AbstractionLevel]
    ) -> AbstractionContent:
        """Merge content from multiple levels."""
        all_content = [l.content.content for l in levels]
        avg_height = sum(l.height for l in levels) / len(levels)

        return AbstractionContent(
            f"Merged content from {len(levels)} levels around height {avg_height:.0f}",
            int(avg_height),
            f"Compression of {len(levels)} levels"
        )

    def get_level_at_height(self, height: int) -> Optional[AbstractionLevel]:
        """Get abstraction level at specific height."""
        # Find closest level
        if height in self.levels:
            return self.levels[height]

        # Find nearest
        closest = min(self.levels.keys(), key=lambda h: abs(h - height))
        if abs(closest - height) <= 10:
            return self.levels[closest]

        return None

    def get_active_levels(self) -> List[AbstractionLevel]:
        """Get all currently active abstraction levels."""
        return list(self.levels.values())


class InferenceZoom:
    """
    Controls zooming between abstraction levels.

    Enables intelligent zoom based on query requirements.
    """

    def __init__(self, stack: AbstractionStack):
        self.stack = stack
        self.zoom_history: List[ZoomOperation] = []

    def intelligent_zoom(self, query: str) -> AbstractionLevel:
        """
        Determine optimal abstraction level for query.

        Args:
            query: Query to analyze

        Returns:
            Optimal AbstractionLevel for the query
        """
        # Analyze query characteristics
        query_lower = query.lower()

        # Keywords suggesting different abstraction levels
        if any(w in query_lower for w in ["specific", "concrete", "example", "instance", "what"]):
            target_height = 10  # INSTANCE_DATA
        elif any(w in query_lower for w in ["pattern", "trend", "correlation", "relationship"]):
            target_height = 20  # PATTERNS
        elif any(w in query_lower for w in ["concept", "definition", "meaning", "category"]):
            target_height = 30  # CONCEPTS
        elif any(w in query_lower for w in ["principle", "law", "rule", "theorem", "prove"]):
            target_height = 40  # PRINCIPLES
        elif any(w in query_lower for w in ["theory", "framework", "model", "hypothesis"]):
            target_height = 50  # THEORIES
        elif any(w in query_lower for w in ["paradigm", "worldview", "assumption", "foundational"]):
            target_height = 60  # PARADIGMS
        elif any(w in query_lower for w in ["ethics", "morality", "philosophy", "meaning of", "purpose"]):
            target_height = 70  # PHILOSOPHY
        elif any(w in query_lower for w in ["existence", "being", "consciousness", "reality"]):
            target_height = 80  # METAPHYSICS
        else:
            target_height = 50  # Default: THEORIES

        # Get or create level
        level = self.stack.get_level_at_height(target_height)
        if level is None:
            level = AbstractionLevel(
                level_id=f"level_{target_height}",
                height=target_height,
                content=AbstractionContent(f"Level {target_height}", target_height),
                children=[],
                parent=None
            )
            self.stack.add_level(level)

        return level

    def trace_path(
        self,
        from_level: int,
        to_level: int
    ) -> List[AbstractionLevel]:
        """
        Find path through abstraction space.

        Args:
            from_level: Starting height
            to_level: Target height

        Returns:
            List of AbstractionLevels along the path
        """
        path = []
        direction = 1 if to_level > from_level else -1

        for h in range(from_level, to_level + direction, direction * 10):
            level = self.stack.get_level_at_height(h)
            if level:
                path.append(level)

        return path


class AbstractionCompressor:
    """Compresses and expands abstraction ranges."""

    def __init__(self):
        self.compression_algorithms = {
            "semantic": self._semantic_compression,
            "statistical": self._statistical_compression,
            "hierarchical": self._hierarchical_compression
        }

    def compress(
        self,
        levels: List[AbstractionLevel],
        algorithm: str = "semantic"
    ) -> AbstractionLevel:
        """
        Compress multiple levels into single abstraction.

        Args:
            levels: Levels to compress
            algorithm: Compression algorithm to use

        Returns:
            Compressed AbstractionLevel
        """
        if algorithm in self.compression_algorithms:
            return self.compression_algorithms[algorithm](levels)
        else:
            return self._semantic_compression(levels)

    def _semantic_compression(self, levels: List[AbstractionLevel]) -> AbstractionLevel:
        """Semantic compression: extract key meanings."""
        # Extract semantic content
        meanings = []
        for level in levels:
            if isinstance(level.content.content, str):
                meanings.append(level.content.content)
            else:
                meanings.append(str(level.content.content))

        combined = " | ".join(meanings[:3])  # Top 3 meanings

        return AbstractionLevel(
            level_id=f"semantic_compressed_{datetime.now().timestamp()}",
            height=sum(l.height for l in levels) // len(levels),
            content=AbstractionContent(combined, 50),
            children=[str(l.height) for l in levels],
            compression_ratio=0.6
        )

    def _statistical_compression(self, levels: List[AbstractionLevel]) -> AbstractionLevel:
        """Statistical compression: extract patterns."""
        # Count patterns
        all_content = " ".join(str(l.content.content) for l in levels)
        words = all_content.split()

        # Most common words as summary
        from collections import Counter
        word_counts = Counter(words)
        top_words = [w for w, c in word_counts.most_common(5)]

        return AbstractionLevel(
            level_id=f"statistical_compressed_{datetime.now().timestamp()}",
            height=sum(l.height for l in levels) // len(levels),
            content=AbstractionContent(" ".join(top_words), 50),
            children=[str(l.height) for l in levels],
            compression_ratio=0.5
        )

    def _hierarchical_compression(self, levels: List[AbstractionLevel]) -> AbstractionLevel:
        """Hierarchical compression: preserve structure."""
        # Build hierarchical representation
        structure = {
            "num_levels": len(levels),
            "height_range": (min(l.height for l in levels), max(l.height for l in levels)),
            "domains": list(set(l.domain for l in levels if l.domain))
        }

        return AbstractionLevel(
            level_id=f"hierarchical_compressed_{datetime.now().timestamp()}",
            height=sum(l.height for l in levels) // len(levels),
            content=AbstractionContent(str(structure), 50),
            children=[str(l.height) for l in levels],
            compression_ratio=0.7
        )


class CognitiveRelativityNavigator:
    """
    Main CRN orchestrator.

    Manages multi-level abstraction reasoning with dynamic zoom
    between atomic facts and abstract philosophy.
    """

    def __init__(self):
        self.abstraction_stack = AbstractionStack()
        self.inference_zoom = InferenceZoom(self.abstraction_stack)
        self.compressor = AbstractionCompressor()
        self.current_query = None
        self.navigation_history: List[NavigationResult] = []

        # Initialize some standard levels
        self._initialize_standard_levels()

    def _initialize_standard_levels(self) -> None:
        """Initialize standard abstraction levels."""
        standard_levels = [
            (0, "atomic_facts", "Specific observations and data points"),
            (10, "instance_data", "Specific examples and cases"),
            (20, "patterns", "Regularities and correlations"),
            (30, "concepts", "Domain-specific concepts"),
            (40, "principles", "Domain principles and rules"),
            (50, "theories", "Coherent theoretical frameworks"),
            (60, "paradigms", "Worldview and foundational assumptions"),
            (70, "philosophy", "Philosophical frameworks"),
            (80, "metaphysics", "Existential and ontological questions"),
            (100, "pure_abstraction", "Maximum abstraction")
        ]

        for height, level_id, description in standard_levels:
            level = AbstractionLevel(
                level_id=level_id,
                height=height,
                content=AbstractionContent(description, height),
                children=[],
                parent=None
            )
            self.abstraction_stack.add_level(level)

    def navigate_query(
        self,
        query: str,
        target_abstraction: Optional[int] = None
    ) -> NavigationResult:
        """
        Process query at appropriate abstraction level.

        Args:
            query: Query to process
            target_abstraction: Specific target level (auto-detect if None)

        Returns:
            NavigationResult with answer and trace
        """
        self.current_query = query

        # Determine target abstraction
        if target_abstraction is None:
            target_level = self.inference_zoom.intelligent_zoom(query)
            target_abstraction = target_level.height

        # Zoom to target level
        current = self.abstraction_stack.current_focus
        if current != target_abstraction:
            if target_abstraction < current:
                self.abstraction_stack.zoom_in((current - target_abstraction) // 10)
            else:
                self.abstraction_stack.zoom_out((target_abstraction - current) // 10)

        # Process at target level
        result = self._process_at_level(query, target_abstraction)

        navigation = NavigationResult(
            query=query,
            target_abstraction=target_abstraction,
            actual_abstraction=self.abstraction_stack.current_focus,
            result=result,
            reasoning_trace=[f"Processed at abstraction level {target_abstraction}"],
            confidence=0.7,
            levels_visited=[target_abstraction]
        )

        self.navigation_history.append(navigation)

        return navigation

    def multi_level_inference(self, query: str) -> MultiLevelResult:
        """
        Perform inference across multiple abstraction levels simultaneously.

        Args:
            query: Query to process

        Returns:
            MultiLevelResult with results from all levels
        """
        # Process at multiple levels in parallel
        results_by_level = {}
        levels_to_try = [0, 20, 40, 60, 80]  # Atomic, Patterns, Principles, Paradigms, Metaphysics

        for level in levels_to_try:
            result = self._process_at_level(query, level)
            results_by_level[level] = result

        # Synthesize results
        synthesized = self._synthesize_multi_level(results_by_level)

        # Calculate coherence
        coherence = self._calculate_coherence(results_by_level)

        # Determine recommended abstraction
        recommended = self._recommend_abstraction(results_by_level, coherence)

        return MultiLevelResult(
            query=query,
            results_by_level=results_by_level,
            synthesized_result=synthesized,
            coherence_score=coherence,
            recommended_abstraction=recommended
        )

    def adaptive_abstraction(self, task_complexity: float) -> AbstractionLevel:
        """
        Dynamically adjust abstraction based on task demands.

        Args:
            task_complexity: 0.0 (simple) to 1.0 (complex)

        Returns:
            Appropriate AbstractionLevel
        """
        if task_complexity < 0.2:
            # Simple task: use concrete level
            target = 10
        elif task_complexity < 0.5:
            # Moderate task: use concepts
            target = 30
        elif task_complexity < 0.8:
            # Complex task: use theories
            target = 50
        else:
            # Very complex: use philosophy
            target = 70

        level = self.abstraction_stack.get_level_at_height(target)
        if level is None:
            level = AbstractionLevel(
                level_id=f"adaptive_{target}",
                height=target,
                content=AbstractionContent(f"Adaptive level {target}", target),
                children=[],
                parent=None
            )
            self.abstraction_stack.add_level(level)

        return level

    def _process_at_level(self, query: str, level: int) -> Any:
        """Process query at a specific abstraction level."""
        # Get level object
        level_obj = self.abstraction_stack.get_level_at_height(level)

        if level_obj and isinstance(level_obj.content.content, str):
            # Return the content at this level
            return f"At level {level} ({level_obj.level_id}): {level_obj.content.content}"

        # Default response
        return f"Processing '{query}' at abstraction level {level}"

    def _synthesize_multi_level(self, results: Dict[int, Any]) -> Any:
        """Synthesize results from multiple abstraction levels."""
        # Combine insights across levels
        synthesis = {
            "atomic": results.get(0),
            "patterns": results.get(20),
            "principles": results.get(40),
            "paradigms": results.get(60),
            "metaphysics": results.get(80)
        }
        return synthesis

    def _calculate_coherence(self, results: Dict[int, Any]) -> float:
        """Calculate coherence of multi-level results."""
        # Simplified: check if results are consistent
        # Higher coherence if results align across levels
        return 0.7  # Placeholder

    def _recommend_abstraction(
        self,
        results: Dict[int, Any],
        coherence: float
    ) -> int:
        """Recommend optimal abstraction level."""
        # If coherence is high, use middle level
        # If coherence is low, may need to explore different levels
        if coherence > 0.8:
            return 50  # Theories
        else:
            return 30  # Concepts

    def get_status(self) -> Dict[str, Any]:
        """Get current CRN status."""
        return {
            "current_focus": self.abstraction_stack.current_focus,
            "num_levels": len(self.abstraction_stack.levels),
            "zoom_history_length": len(self.abstraction_stack.zoom_history),
            "navigation_history_length": len(self.navigation_history)
        }


# =============================================================================
# Factory Functions
# =============================================================================

def create_cognitive_relativity_navigator() -> CognitiveRelativityNavigator:
    """Create a Cognitive-Relativity Navigator."""
    return CognitiveRelativityNavigator()


def create_abstraction_stack(max_levels: int = 10) -> AbstractionStack:
    """Create an AbstractionStack with given capacity."""
    return AbstractionStack(max_levels)


def create_inference_zoom(stack: AbstractionStack) -> InferenceZoom:
    """Create an InferenceZoom for given stack."""
    return InferenceZoom(stack)
