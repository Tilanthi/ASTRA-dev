"""
Meta-Context Engine (MCE) for STAN_XI_ASTRO V4.0

Inspired by: Large Contextual Models (LCMs) and dimensional perception

Design Concept:
Create a Meta-Context Engine that dynamically maps and weights context layers
across temporal and perceptual dimensions - like a "multi-threaded mind."

This engine doesn't just track what is relevant now, but predicts shifts in context
based on historical behavioral modeling (e.g., "In similar geopolitical scenarios,
economic models tend to become more relevant").

Use Case:
In a complex simulation the MCE allows superintelligence to shift between predictive,
analytical, and emotional modeling frames without hard switching logic trees.

Version: 4.0.0
Date: 2026-03-17
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from collections import deque


class TemporalScale(Enum):
    """Temporal scales for context layering (aligned with V70 hierarchy)"""
    TICK = "tick"           # Microsecond to second
    MICRO = "micro"         # Second to minute
    MESO = "meso"           # Minute to hour
    MACRO = "macro"         # Hour to day
    MEGA = "mega"           # Day to month
    EPOCH = "epoch"         # Month to year
    ERA = "era"             # Year to decade+
    ABSTRACT = "abstract"    # Timeless principles


class CognitiveFrame(Enum):
    """Types of cognitive frames for multi-threaded reasoning"""
    PREDICTIVE = "predictive"      # Future-oriented modeling and forecasting
    ANALYTICAL = "analytical"      # Decomposition, logic, and inference
    EMOTIONAL = "emotional"        # Affective, value-based, ethical reasoning
    CREATIVE = "creative"          # Generative, novel, imaginative
    CRITICAL = "critical"          # Evaluative, skeptical, falsification-focused
    NARRATIVE = "narrative"        # Story-based, contextual, historical
    MATHEMATICAL = "mathematical"  # Formal, quantitative, abstract
    INTUITIVE = "intuitive"        # Pattern-based, heuristic, fast


class ContextDimension(Enum):
    """Dimensions along which context can vary"""
    TEMPORAL = "temporal"          # Time scale focus
    PERCEPTUAL = "perceptual"      # Granularity (concrete ↔ abstract)
    DOMAIN = "domain"              # Subject matter domain
    MODALITY = "modality"          # Information type (visual, textual, etc.)
    CERTAINTY = "certainty"        # Confidence level required
    SOCIAL = "social"              # Individual vs collective perspective
    EPISTEMIC = "epistemic"        # Knowledge type (empirical, theoretical, etc.)


class TransitionStrategy(Enum):
    """Strategies for transitioning between contexts"""
    ABRUPT = "abrupt"              # Immediate switch, high disruption
    GRADUAL = "gradual"            # Slow fade, low disruption
    PARALLEL = "parallel"          # Both active temporarily, integrate
    PREDICTIVE = "predictive"      # Anticipate and pre-load next context
    EMERGENT = "emergent"          # Allow natural emergence
    META_GUIDED = "meta_guided"    # Metacognitive direction


@dataclass
class ContextMetadata:
    """Metadata associated with a context layer"""
    created_at: float
    last_accessed: float
    access_count: int = 0
    effectiveness_score: float = 0.5  # Historical effectiveness
    stability_score: float = 0.5       # Resistance to change
    novelty_score: float = 0.5         # Novelty of this context
    emotional_valence: float = 0.0     # Positive/negative association
    associated_minds: List[str] = field(default_factory=list)


@dataclass
class ContextLayer:
    """
    A single layer of cognitive context.

    Represents a specific "slice" of the cognitive space with defined
    temporal scale, perceptual granularity, and cognitive frame.
    """
    layer_id: str
    temporal_scale: TemporalScale
    perceptual_granularity: float  # 0.0 (abstract) to 1.0 (concrete)
    cognitive_frame: CognitiveFrame
    activation: float = 0.0  # 0.0 to 1.0
    contents: Dict[str, Any] = field(default_factory=dict)
    metadata: ContextMetadata = field(default_factory=lambda: ContextMetadata(
        created_at=0.0, last_accessed=0.0
    ))

    def similarity_to(self, other: 'ContextLayer') -> float:
        """Calculate similarity between this context and another."""
        # Temporal scale similarity
        temporal_match = 1.0 if self.temporal_scale == other.temporal_scale else 0.0

        # Perceptual granularity similarity
        gran_diff = abs(self.perceptual_granularity - other.perceptual_granularity)
        gran_sim = 1.0 - gran_diff

        # Cognitive frame similarity
        frame_match = 1.0 if self.cognitive_frame == other.cognitive_frame else 0.0

        # Overall similarity
        return (temporal_match + gran_sim + frame_match) / 3.0

    def merge_with(self, other: 'ContextLayer', weight: float = 0.5) -> 'ContextLayer':
        """Merge this context with another, weighted by given factor."""
        new_granularity = (self.perceptual_granularity * (1 - weight) +
                          other.perceptual_granularity * weight)
        new_activation = (self.activation * (1 - weight) + other.activation * weight)

        merged = ContextLayer(
            layer_id=f"{self.layer_id}+{other.layer_id}",
            temporal_scale=self.temporal_scale if weight < 0.5 else other.temporal_scale,
            perceptual_granularity=new_granularity,
            cognitive_frame=self.cognitive_frame if weight < 0.5 else other.cognitive_frame,
            activation=new_activation,
            contents={**self.contents, **other.contents}
        )
        return merged


@dataclass
class ContextShift:
    """A predicted or executed context shift"""
    from_layer: str
    to_layer: str
    trigger: str  # What triggered the shift
    probability: float  # Likelihood of this shift
    timing: float  # When this shift is predicted
    transition_strategy: TransitionStrategy
    disruption_cost: float = 0.0  # Cognitive cost of transition


@dataclass
class LayeredContext:
    """
    Multi-layered context representation.

    Contains multiple context layers active simultaneously,
    each representing a different cognitive perspective or temporal scale.
    """
    layers: List[ContextLayer]
    primary_layer: str
    coherence_score: float = 0.0  # How well layers cohere
    timestamp: float = 0.0

    def get_active_layers(self, threshold: float = 0.3) -> List[ContextLayer]:
        """Get layers with activation above threshold."""
        return [l for l in self.layers if l.activation >= threshold]

    def get_layer_by_frame(self, frame: CognitiveFrame) -> Optional[ContextLayer]:
        """Get the layer with a specific cognitive frame."""
        for layer in self.layers:
            if layer.cognitive_frame == frame:
                return layer
        return None

    def get_layer_by_scale(self, scale: TemporalScale) -> Optional[ContextLayer]:
        """Get the layer with a specific temporal scale."""
        for layer in self.layers:
            if layer.temporal_scale == scale:
                return layer
        return None


@dataclass
class MCEConfig:
    """Configuration for Meta-Context Engine"""
    max_context_layers: int = 8
    context_decay_rate: float = 0.1
    prediction_horizon: float = 100.0  # Time units for prediction
    min_activation_threshold: float = 0.1
    max_parallel_frames: int = 3
    enable_context_prediction: bool = True
    enable_multi_threaded_reasoning: bool = True


class ContextShiftPredictor:
    """
    Predicts context shifts based on behavioral modeling.

    Learns from historical patterns of context transitions to anticipate
    when context shifts are likely to occur.
    """

    def __init__(self, config: MCEConfig):
        self.config = config
        self.transition_history: deque = deque(maxlen=1000)
        self.behavioral_patterns: Dict[str, List[float]] = {}
        self.similarity_threshold = 0.7

    def record_transition(self, transition: ContextShift) -> None:
        """Record a context transition for learning."""
        self.transition_history.append(transition)
        self._update_patterns(transition)

    def _update_patterns(self, transition: ContextShift) -> None:
        """Update behavioral patterns from transition."""
        key = f"{transition.from_layer}->{transition.to_layer}"
        if key not in self.behavioral_patterns:
            self.behavioral_patterns[key] = []
        self.behavioral_patterns[key].append(transition.timing)

    def predict_shifts(
        self,
        current_context: LayeredContext,
        time_horizon: float
    ) -> List[ContextShift]:
        """
        Predict likely context shifts within time horizon.

        Returns:
            List of predicted shifts ordered by probability
        """
        predictions = []

        for layer in current_context.layers:
            # Check historical transitions from this layer
            for hist in self.transition_history:
                if hist.from_layer == layer.layer_id:
                    # Calculate similarity of conditions
                    similarity = self._calculate_similarity(
                        current_context, hist
                    )

                    if similarity > self.similarity_threshold:
                        predicted_timing = hist.timing * similarity
                        if predicted_timing <= time_horizon:
                            predictions.append(ContextShift(
                                from_layer=layer.layer_id,
                                to_layer=hist.to_layer,
                                trigger=f"Pattern similarity: {similarity:.2f}",
                                probability=hist.probability * similarity,
                                timing=predicted_timing,
                                transition_strategy=hist.transition_strategy
                            ))

        # Sort by probability
        predictions.sort(key=lambda x: x.probability, reverse=True)
        return predictions[:5]  # Top 5 predictions

    def _calculate_similarity(
        self,
        current: LayeredContext,
        historical: ContextShift
    ) -> float:
        """Calculate similarity between current and historical conditions."""
        # Simplified: check if similar layers are active
        current_active = {l.layer_id for l in current.get_active_layers()}
        historical_from = historical.from_layer

        if historical_from in current_active:
            return 0.8  # High similarity if same layer active
        return 0.2


class MultiThreadedReasoning:
    """
    Manages parallel cognitive frame processing.

    Enables simultaneous reasoning in predictive, analytical, and emotional
    frames without hard switching between logic trees.
    """

    def __init__(self, config: MCEConfig):
        self.config = config
        self.active_frames: Dict[CognitiveFrame, ContextLayer] = {}
        self.frame_weights: Dict[CognitiveFrame, float] = {}
        self.frame_outputs: Dict[CognitiveFrame, Any] = {}

    def activate_frame(
        self,
        frame: CognitiveFrame,
        layer: ContextLayer,
        weight: float = 1.0
    ) -> None:
        """Activate a cognitive frame with given layer and weight."""
        self.active_frames[frame] = layer
        self.frame_weights[frame] = weight
        layer.cognitive_frame = frame

    def deactivate_frame(self, frame: CognitiveFrame) -> None:
        """Deactivate a cognitive frame."""
        if frame in self.active_frames:
            del self.active_frames[frame]
            del self.frame_weights[frame]
        if frame in self.frame_outputs:
            del self.frame_outputs[frame]

    def process_query(
        self,
        query: str,
        context: LayeredContext
    ) -> Dict[CognitiveFrame, Any]:
        """
        Process query through all active cognitive frames in parallel.

        Returns:
            Dictionary mapping frame to its output
        """
        results = {}

        for frame, layer in self.active_frames.items():
            # Frame-specific processing
            if frame == CognitiveFrame.PREDICTIVE:
                results[frame] = self._predictive_processing(query, layer, context)
            elif frame == CognitiveFrame.ANALYTICAL:
                results[frame] = self._analytical_processing(query, layer, context)
            elif frame == CognitiveFrame.EMOTIONAL:
                results[frame] = self._emotional_processing(query, layer, context)
            elif frame == CognitiveFrame.CRITICAL:
                results[frame] = self._critical_processing(query, layer, context)
            elif frame == CognitiveFrame.CREATIVE:
                results[frame] = self._creative_processing(query, layer, context)
            else:
                results[frame] = self._default_processing(query, layer, context)

        self.frame_outputs = results
        return results

    def _predictive_processing(
        self,
        query: str,
        layer: ContextLayer,
        context: LayeredContext
    ) -> Dict[str, Any]:
        """Predictive frame: forecast and extrapolate"""
        return {
            "frame": "predictive",
            "focus": "future_outcomes",
            "time_horizon": layer.temporal_scale.value,
            "confidence": layer.activation * 0.8,
            "reasoning": "Based on patterns, this will likely lead to..."
        }

    def _analytical_processing(
        self,
        query: str,
        layer: ContextLayer,
        context: LayeredContext
    ) -> Dict[str, Any]:
        """Analytical frame: decompose and analyze"""
        return {
            "frame": "analytical",
            "focus": "logical_structure",
            "decomposition": ["assumptions", "inferences", "conclusions"],
            "confidence": layer.activation * 0.9,
            "reasoning": "Breaking down into components..."
        }

    def _emotional_processing(
        self,
        query: str,
        layer: ContextLayer,
        context: LayeredContext
    ) -> Dict[str, Any]:
        """Emotional frame: values, ethics, impact"""
        return {
            "frame": "emotional",
            "focus": "values_and_ethics",
            "valence": layer.metadata.emotional_valence,
            "confidence": layer.activation * 0.6,
            "reasoning": "From an ethical perspective, this suggests..."
        }

    def _critical_processing(
        self,
        query: str,
        layer: ContextLayer,
        context: LayeredContext
    ) -> Dict[str, Any]:
        """Critical frame: challenge and verify"""
        return {
            "frame": "critical",
            "focus": "potential_flaws",
            "challenges": ["assumptions", "logic", "evidence"],
            "confidence": layer.activation * 0.7,
            "reasoning": "Let's verify these claims..."
        }

    def _creative_processing(
        self,
        query: str,
        layer: ContextLayer,
        context: LayeredContext
    ) -> Dict[str, Any]:
        """Creative frame: novel alternatives"""
        return {
            "frame": "creative",
            "focus": "novel_possibilities",
            "alternatives": [],
            "confidence": layer.activation * 0.5,
            "reasoning": "Have we considered..."
        }

    def _default_processing(
        self,
        query: str,
        layer: ContextLayer,
        context: LayeredContext
    ) -> Dict[str, Any]:
        """Default processing for other frames"""
        return {
            "frame": layer.cognitive_frame.value,
            "focus": "standard_reasoning",
            "confidence": layer.activation * 0.7,
            "reasoning": query
        }

    def synthesize_outputs(self) -> Dict[str, Any]:
        """
        Synthesize outputs from all active frames.

        Returns integrated perspective combining insights from all frames.
        """
        if not self.frame_outputs:
            return {"error": "No frame outputs to synthesize"}

        synthesis = {
            "frames_used": list(self.frame_outputs.keys()),
            "primary_frame": max(self.frame_weights.items(), key=lambda x: x[1])[0].value,
            "insights": [],
            "confidence_range": [
                min(out.get("confidence", 0.5) for out in self.frame_outputs.values()),
                max(out.get("confidence", 0.5) for out in self.frame_outputs.values())
            ],
            "recommendations": []
        }

        # Extract insights from each frame
        for frame, output in self.frame_outputs.items():
            if "reasoning" in output:
                synthesis["insights"].append({
                    "frame": frame.value,
                    "insight": output["reasoning"],
                    "weight": self.frame_weights[frame]
                })

        return synthesis


class MetaContextEngine:
    """
    Main Meta-Context Engine orchestrator.

    Manages dynamic context layering across temporal and perceptual dimensions,
    enables multi-threaded reasoning through different cognitive frames, and
    predicts context shifts based on behavioral modeling.
    """

    def __init__(self, config: Optional[MCEConfig] = None):
        self.config = config or MCEConfig()

        # Core components
        self.context_layers: Dict[str, ContextLayer] = {}
        self.active_context: Optional[LayeredContext] = None
        self.shift_predictor = ContextShiftPredictor(self.config)
        self.multi_threaded = MultiThreadedReasoning(self.config)

        # Integration with existing systems
        self.working_memory = None  # Will connect to existing WorkingMemory
        self.metacognitive_core = None  # Will connect to V93 MetacognitiveCore

        # History tracking
        self.context_history: List[LayeredContext] = []
        self.shift_history: List[ContextShift] = []

        # State
        self.current_time = 0.0
        self.last_primary_layer = None

    def layer_context(
        self,
        query: str,
        dimensions: List[ContextDimension],
        preferred_frames: Optional[List[CognitiveFrame]] = None
    ) -> LayeredContext:
        """
        Create multi-layered context representation for a query.

        Args:
            query: The input query or situation
            dimensions: Which context dimensions to consider (can be enum or string values)
            preferred_frames: Preferred cognitive frames (can be enum or string values)

        Returns:
            LayeredContext with multiple context layers
        """
        # Normalize dimensions to enum values
        normalized_dimensions = []
        for dim in dimensions:
            if isinstance(dim, str):
                try:
                    normalized_dimensions.append(ContextDimension[dim.upper()])
                except KeyError:
                    # Use LITERAL as default for unrecognized string dimensions
                    normalized_dimensions.append(ContextDimension.LITERAL)
            else:
                normalized_dimensions.append(dim)

        # Normalize frames to enum values
        normalized_frames = []
        if preferred_frames:
            for frame in preferred_frames:
                if isinstance(frame, str):
                    try:
                        normalized_frames.append(CognitiveFrame[frame.upper()])
                    except KeyError:
                        normalized_frames.append(CognitiveFrame.PREDICTIVE)
                else:
                    normalized_frames.append(frame)
        else:
            normalized_frames = list(CognitiveFrame)

        layers = []
        for dim in normalized_dimensions:
            for frame in normalized_frames:
                layer = self._create_context_layer(query, dim, frame)
                layers.append(layer)

        return LayeredContext(
            query=query,
            layers=layers,
            primary_dimension=normalized_dimensions[0] if normalized_dimensions else ContextDimension.LITERAL,
            primary_frame=normalized_frames[0] if normalized_frames else CognitiveFrame.PREDICTIVE
        )

    def _create_context_layer(
        self,
        query: str,
        dimension: ContextDimension,
        frame: CognitiveFrame
    ) -> ContextLayer:
        """Create a single context layer."""
        # Generate context based on dimension and frame
        content = f"{dimension.value} context via {frame.value} frame: {query}"

        return ContextLayer(
            dimension=dimension,
            frame=frame,
            content=content,
            weight=1.0,
            metadata={"dimension": dimension.value, "frame": frame.value}
        )


# Factory functions
def create_meta_context_engine(config: Optional[Dict[str, Any]] = None) -> MetaContextEngine:
    """Create a meta-context engine."""
    return MetaContextEngine(config or {})
