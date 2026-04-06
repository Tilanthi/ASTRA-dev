"""
Minimal Integration Bus Stub for Counterfactual Reasoning

This is a minimal stub to allow counterfactual reasoning to work
without requiring the full integration bus infrastructure.

Date: 2025-12-11
Version: 1.0
"""

from enum import Enum
from typing import Dict, Any, Callable, List
from collections import defaultdict


class EventType(Enum):
    """Event types for integration bus"""
    REASONING_STEP_COMPLETED = "reasoning_step_completed"
    HYPOTHESIS_GENERATED = "hypothesis_generated"
    BELIEF_UPDATED = "belief_updated"
    WORLD_MODEL_UPDATED = "world_model_updated"


class IntegrationBus:
    """
    Minimal integration bus for inter-module communication.

    This is a stub implementation - the full version would have
    proper event routing, persistence, and distributed capabilities.
    """

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._event_log: List[Dict[str, Any]] = []

    def publish(self, event_type: EventType, source: str, data: Dict[str, Any]):
        """Publish an event to the bus"""
        event = {
            'type': event_type,
            'source': source,
            'data': data,
            'timestamp': None  # Would add real timestamp
        }
        self._event_log.append(event)

        # Notify subscribers
        for callback in self._subscribers[event_type]:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in subscriber callback: {e}")

    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to events"""
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from events"""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def get_event_log(self) -> List[Dict[str, Any]]:
        """Get log of all events"""
        return self._event_log.copy()


# Singleton instance
_integration_bus_instance: IntegrationBus = None


def get_integration_bus() -> IntegrationBus:
    """Get or create the singleton integration bus instance"""
    global _integration_bus_instance
    if _integration_bus_instance is None:
        _integration_bus_instance = IntegrationBus()
    return _integration_bus_instance
