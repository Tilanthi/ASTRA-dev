"""
Temporal Context Memory for Meta-Context Engine

Stores and retrieves context history with temporal indexing,
enabling behavioral shift prediction.

Version: 4.0.0
Date: 2026-03-17
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import time
from datetime import datetime, timedelta


class ContextEventType(Enum):
    """Types of context events"""
    SHIFT = "shift"              # Context shifted
    ACTIVATION = "activation"    # Context activated
    DEACTIVATION = "deactivation"  # Context deactivated
    PREDICTION = "prediction"    # Context shift predicted
    CONFLICT = "conflict"        # Context conflict detected


@dataclass
class ContextEvent:
    """An event in context history"""
    event_type: ContextEventType
    layer_id: str
    timestamp: float
    temporal_scale: str
    cognitive_frame: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "layer_id": self.layer_id,
            "timestamp": self.timestamp,
            "temporal_scale": self.temporal_scale,
            "cognitive_frame": self.cognitive_frame,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


@dataclass
class BehaviorPattern:
    """A detected behavioral pattern"""
    pattern_id: str
    description: str
    temporal_period: float  # Seconds in pattern cycle
    confidence: float
    sequence: List[str]  # Ordered layer_ids
    last_occurrence: float
    occurrence_count: int


@dataclass
class ShiftPrediction:
    """A predicted context shift"""
    predicted_layer_id: str
    probability: float
    time_horizon: float  # Seconds until predicted
    confidence: float
    reasoning: List[str]
    based_on_pattern: Optional[str] = None


class TemporalContextMemory:
    """
    Stores context history with temporal indexing for
    behavioral analysis and shift prediction.
    """

    def __init__(self, max_events: int = 10000):
        self.events: List[ContextEvent] = []
        self.max_events = max_events
        self.patterns: Dict[str, BehaviorPattern] = {}
        self.layer_history: Dict[str, List[ContextEvent]] = defaultdict(list)
        self.time_index: Dict[float, ContextEvent] = {}

    def add_event(self, event: ContextEvent) -> None:
        """Add an event to memory."""
        self.events.append(event)
        self.layer_history[event.layer_id].append(event)
        self.time_index[event.timestamp] = event

        # Prune if over capacity
        if len(self.events) > self.max_events:
            oldest = self.events.pop(0)
            if oldest.layer_id in self.layer_history:
                self.layer_history[oldest.layer_id] = [
                    e for e in self.layer_history[oldest.layer_id]
                    if e.timestamp != oldest.timestamp
                ]
            del self.time_index[oldest.timestamp]

    def record_shift(
        self,
        from_layer_id: str,
        to_layer_id: str,
        temporal_scale: str,
        cognitive_frame: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a context shift."""
        shift_event = ContextEvent(
            event_type=ContextEventType.SHIFT,
            layer_id=to_layer_id,
            timestamp=time.time(),
            temporal_scale=temporal_scale,
            cognitive_frame=cognitive_frame,
            confidence=confidence,
            metadata=metadata or {"from_layer": from_layer_id}
        )
        self.add_event(shift_event)

    def record_activation(
        self,
        layer_id: str,
        temporal_scale: str,
        cognitive_frame: str,
        activation_level: float
    ) -> None:
        """Record a context activation."""
        activation_event = ContextEvent(
            event_type=ContextEventType.ACTIVATION,
            layer_id=layer_id,
            timestamp=time.time(),
            temporal_scale=temporal_scale,
            cognitive_frame=cognitive_frame,
            confidence=activation_level
        )
        self.add_event(activation_event)

    def get_events_in_range(
        self,
        start_time: float,
        end_time: float
    ) -> List[ContextEvent]:
        """Get all events within a time range."""
        return [
            e for e in self.events
            if start_time <= e.timestamp <= end_time
        ]

    def get_layer_history(
        self,
        layer_id: str,
        max_events: int = 100
    ) -> List[ContextEvent]:
        """Get history for a specific layer."""
        history = self.layer_history.get(layer_id, [])
        return history[-max_events:] if history else []

    def get_recent_events(
        self,
        duration: float = 3600.0,
        event_type: Optional[ContextEventType] = None
    ) -> List[ContextEvent]:
        """Get recent events within duration."""
        current_time = time.time()
        start_time = current_time - duration

        events = [
            e for e in self.events
            if e.timestamp >= start_time
        ]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events

    def analyze_behavioral_patterns(
        self,
        min_occurrences: int = 3,
        time_window: float = 86400.0
    ) -> List[BehaviorPattern]:
        """Detect behavioral patterns in context shifts."""
        current_time = time.time()
        start_time = current_time - time_window

        # Get shift events
        shifts = [
            e for e in self.events
            if e.event_type == ContextEventType.SHIFT
            and e.timestamp >= start_time
        ]

        # Build sequences
        sequences = self._extract_sequences(shifts)

        # Find repeating patterns
        patterns = []
        for sequence, occurrences in sequences.items():
            if len(occurrences) >= min_occurrences:
                # Calculate temporal period
                timestamps = [occ["timestamp"] for occ in occurrences]
                if len(timestamps) >= 2:
                    periods = [
                        timestamps[i] - timestamps[i-1]
                        for i in range(1, len(timestamps))
                    ]
                    avg_period = sum(periods) / len(periods) if periods else 0

                    pattern = BehaviorPattern(
                        pattern_id=f"pattern_{len(patterns)}",
                        description=f"Sequence: {' → '.join(sequence)}",
                        temporal_period=avg_period,
                        confidence=len(occurrences) / 10.0,  # More occurrences = higher confidence
                        sequence=list(sequence),
                        last_occurrence=max(timestamps),
                        occurrence_count=len(occurrences)
                    )
                    patterns.append(pattern)
                    self.patterns[pattern.pattern_id] = pattern

        return patterns

    def _extract_sequences(
        self,
        shifts: List[ContextEvent]
    ) -> Dict[Tuple[str, ...], List[Dict[str, Any]]]:
        """Extract repeating sequences from shift events."""
        sequences = defaultdict(list)

        # Look for sequences of length 2-4
        for seq_len in range(2, 5):
            for i in range(len(shifts) - seq_len + 1):
                sequence = tuple(
                    shifts[i + j].layer_id
                    for j in range(seq_len)
                )
                sequences[sequence].append({
                    "timestamp": shifts[i].timestamp,
                    "start_index": i
                })

        return sequences

    def predict_shifts(
        self,
        current_layer_id: str,
        time_horizon: float = 300.0
    ) -> List[ShiftPrediction]:
        """Predict likely context shifts."""
        predictions = []
        current_time = time.time()

        # 1. Pattern-based predictions
        for pattern in self.patterns.values():
            if current_layer_id in pattern.sequence:
                idx = pattern.sequence.index(current_layer_id)
                if idx < len(pattern.sequence) - 1:
                    next_layer = pattern.sequence[idx + 1]

                    # Time until next occurrence based on pattern period
                    time_since_last = current_time - pattern.last_occurrence
                    time_until = pattern.temporal_period - time_since_last

                    if 0 <= time_until <= time_horizon:
                        predictions.append(ShiftPrediction(
                            predicted_layer_id=next_layer,
                            probability=pattern.confidence,
                            time_horizon=time_until,
                            confidence=pattern.confidence * 0.8,
                            reasoning=[
                                f"Based on detected pattern: {pattern.description}",
                                f"Pattern has occurred {pattern.occurrence_count} times",
                                f"Expected in {time_until:.1f} seconds based on period"
                            ],
                            based_on_pattern=pattern.pattern_id
                        ))

        # 2. Frequency-based predictions
        recent_shifts = self.get_recent_events(duration=3600.0)
        shift_counts = defaultdict(int)

        for event in recent_shifts:
            if event.event_type == ContextEventType.SHIFT:
                if event.metadata.get("from_layer") == current_layer_id:
                    shift_counts[event.layer_id] += 1

        if shift_counts:
            total_shifts = sum(shift_counts.values())
            for target_layer, count in shift_counts.items():
                probability = count / total_shifts
                if probability > 0.1:  # Only predict if >10% frequency
                    predictions.append(ShiftPrediction(
                        predicted_layer_id=target_layer,
                        probability=probability,
                        time_horizon=time_horizon / 2,  # Mid-point estimate
                        confidence=probability * 0.6,
                        reasoning=[
                            f"Target layer follows current layer in {count}/{total_shifts} recent shifts",
                            f"Base probability: {probability:.2%}"
                        ]
                    ))

        # Sort by confidence
        predictions.sort(key=lambda p: p.confidence, reverse=True)

        return predictions[:5]  # Return top 5 predictions

    def get_context_statistics(
        self,
        layer_id: str
    ) -> Dict[str, Any]:
        """Get statistics for a specific context layer."""
        history = self.layer_history.get(layer_id, [])

        if not history:
            return {
                "layer_id": layer_id,
                "total_events": 0,
                "activation_count": 0,
                "shift_count": 0,
                "avg_confidence": 0.0,
                "last_seen": None
            }

        activations = [e for e in history if e.event_type == ContextEventType.ACTIVATION]
        shifts = [e for e in history if e.event_type == ContextEventType.SHIFT]

        avg_confidence = sum(e.confidence for e in history) / len(history)

        return {
            "layer_id": layer_id,
            "total_events": len(history),
            "activation_count": len(activations),
            "shift_count": len(shifts),
            "avg_confidence": avg_confidence,
            "last_seen": datetime.fromtimestamp(history[-1].timestamp).isoformat()
        }

    def cleanup_old_events(self, max_age: float = 604800.0) -> int:
        """Remove events older than max_age (default 7 days)."""
        current_time = time.time()
        cutoff_time = current_time - max_age

        initial_count = len(self.events)

        # Filter events
        self.events = [e for e in self.events if e.timestamp >= cutoff_time]

        # Update indexes
        self.layer_history = defaultdict(list)
        self.time_index = {}

        for event in self.events:
            self.layer_history[event.layer_id].append(event)
            self.time_index[event.timestamp] = event

        removed = initial_count - len(self.events)
        return removed

    def export_memory(self) -> Dict[str, Any]:
        """Export memory state for serialization."""
        return {
            "events": [e.to_dict() for e in self.events],
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "description": p.description,
                    "temporal_period": p.temporal_period,
                    "confidence": p.confidence,
                    "sequence": p.sequence,
                    "last_occurrence": p.last_occurrence,
                    "occurrence_count": p.occurrence_count
                }
                for p in self.patterns.values()
            ]
        }

    def import_memory(self, memory_data: Dict[str, Any]) -> None:
        """Import memory state from serialization."""
        # Import events
        for event_data in memory_data.get("events", []):
            event = ContextEvent(
                event_type=ContextEventType(event_data["event_type"]),
                layer_id=event_data["layer_id"],
                timestamp=event_data["timestamp"],
                temporal_scale=event_data["temporal_scale"],
                cognitive_frame=event_data["cognitive_frame"],
                confidence=event_data.get("confidence", 1.0),
                metadata=event_data.get("metadata", {})
            )
            self.add_event(event)

        # Import patterns
        for pattern_data in memory_data.get("patterns", []):
            pattern = BehaviorPattern(
                pattern_id=pattern_data["pattern_id"],
                description=pattern_data["description"],
                temporal_period=pattern_data["temporal_period"],
                confidence=pattern_data["confidence"],
                sequence=pattern_data["sequence"],
                last_occurrence=pattern_data["last_occurrence"],
                occurrence_count=pattern_data["occurrence_count"]
            )
            self.patterns[pattern.pattern_id] = pattern


# =============================================================================
# Factory Functions
# =============================================================================

def create_temporal_context_memory(max_events: int = 10000) -> TemporalContextMemory:
    """Create a temporal context memory."""
    return TemporalContextMemory(max_events=max_events)



# Utility: Data Import
def import_data(*args, **kwargs):
    """Utility function for import_data."""
    return None



def utility_function_17(*args, **kwargs):
    """Utility function 17."""
    return None
