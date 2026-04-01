"""
Cross-Module Integration Bus for STAN V41

Event-based communication system enabling inter-module knowledge sharing.
Modules publish discoveries and subscribe to relevant events, enabling:
- Causal discoveries to trigger hypothesis refinement
- Experiment results to update belief states
- Learning feedback to propagate across capabilities

Date: 2025-12-11
Version: 41.0
"""

import time
import uuid
import queue
import threading
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import weakref
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events in the integration bus"""
    # Discovery events
    CAUSAL_EDGE_DISCOVERED = "causal_edge_discovered"
    HYPOTHESIS_GENERATED = "hypothesis_generated"
    HYPOTHESIS_UPDATED = "hypothesis_updated"
    HYPOTHESIS_CONFIRMED = "hypothesis_confirmed"
    HYPOTHESIS_REFUTED = "hypothesis_refuted"
    PATTERN_DISCOVERED = "pattern_discovered"
    ABSTRACTION_LEARNED = "abstraction_learned"

    # Evidence events
    EVIDENCE_ADDED = "evidence_added"
    EXPERIMENT_RESULT = "experiment_result"
    EXTERNAL_KNOWLEDGE_RETRIEVED = "external_knowledge_retrieved"
    PROOF_VALIDATED = "proof_validated"
    CALCULATION_COMPLETED = "calculation_completed"

    # Reasoning events
    REASONING_STEP_COMPLETED = "reasoning_step_completed"
    CONFIDENCE_UPDATED = "confidence_updated"
    BELIEF_STATE_CHANGED = "belief_state_changed"
    CONSTRAINT_VIOLATED = "constraint_violated"
    ANALOGY_FOUND = "analogy_found"

    # Control events
    CAPABILITY_STARTED = "capability_started"
    CAPABILITY_COMPLETED = "capability_completed"
    CAPABILITY_FAILED = "capability_failed"
    REPLANNING_REQUESTED = "replanning_requested"
    EARLY_STOPPING_TRIGGERED = "early_stopping_triggered"

    # Learning events
    FEEDBACK_RECEIVED = "feedback_received"
    PARAMETER_ADJUSTED = "parameter_adjusted"
    STRATEGY_UPDATED = "strategy_updated"

    # Meta events
    WORLD_MODEL_UPDATED = "world_model_updated"
    UNCERTAINTY_HIGH = "uncertainty_high"
    KNOWLEDGE_GAP_IDENTIFIED = "knowledge_gap_identified"

    # V41 Additional events
    CAUSAL_DISCOVERY = "causal_discovery"
    THEORY_UPDATE = "theory_update"
    METACOGNITIVE_INSIGHT = "metacognitive_insight"
    UNCERTAINTY_UPDATE = "uncertainty_update"
    CAPABILITY_RESULT = "capability_result"
    KNOWLEDGE_ACQUIRED = "knowledge_acquired"
    INFORMATION_NEED = "information_need"
    CONSENSUS_REACHED = "consensus_reached"
    EVALUATION_REQUEST = "evaluation_request"
    HYPOTHESIS_EVALUATED = "hypothesis_evaluated"
    EXPERIENCE_RECORDED = "experience_recorded"
    PATTERNS_DISCOVERED = "patterns_discovered"
    SKILL_ACQUIRED = "skill_acquired"


class EventPriority(Enum):
    """Priority levels for events"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class Event:
    """An event in the integration bus"""
    event_id: str
    event_type: EventType
    source: str  # Module that published the event
    payload: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    correlation_id: Optional[str] = None  # For tracking related events
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"evt_{uuid.uuid4().hex[:12]}"

    def __lt__(self, other):
        """Enable priority queue ordering"""
        return self.priority.value < other.priority.value


@dataclass
class Subscription:
    """A subscription to events"""
    subscription_id: str
    subscriber: str  # Module subscribing
    event_types: Set[EventType]
    callback: Callable[[Event], None]
    filter_fn: Optional[Callable[[Event], bool]] = None
    priority: EventPriority = EventPriority.NORMAL

    def __post_init__(self):
        if not self.subscription_id:
            self.subscription_id = f"sub_{uuid.uuid4().hex[:8]}"


class EventHistory:
    """Maintains history of events for replay and analysis"""

    def __init__(self, max_size: int = 10000):
        self.events: List[Event] = []
        self.max_size = max_size
        self.by_type: Dict[EventType, List[Event]] = defaultdict(list)
        self.by_source: Dict[str, List[Event]] = defaultdict(list)
        self.by_correlation: Dict[str, List[Event]] = defaultdict(list)
        self._lock = threading.Lock()

    def add(self, event: Event):
        """Add event to history"""
        with self._lock:
            self.events.append(event)
            self.by_type[event.event_type].append(event)
            self.by_source[event.source].append(event)
            if event.correlation_id:
                self.by_correlation[event.correlation_id].append(event)

            # Trim if needed
            if len(self.events) > self.max_size:
                self._trim()

    def _trim(self):
        """Remove oldest events"""
        to_remove = len(self.events) - self.max_size
        removed = self.events[:to_remove]
        self.events = self.events[to_remove:]

        # Clean up indices
        for event in removed:
            self.by_type[event.event_type].remove(event)
            self.by_source[event.source].remove(event)
            if event.correlation_id and event in self.by_correlation[event.correlation_id]:
                self.by_correlation[event.correlation_id].remove(event)

    def get_recent(self, n: int = 100) -> List[Event]:
        """Get recent events"""
        return self.events[-n:]

    def get_by_type(self, event_type: EventType, n: int = 100) -> List[Event]:
        """Get events by type"""
        return self.by_type[event_type][-n:]

    def get_by_correlation(self, correlation_id: str) -> List[Event]:
        """Get all events with same correlation ID"""
        return self.by_correlation.get(correlation_id, [])

    def get_causal_chain(self, event_id: str) -> List[Event]:
        """Get causal chain of events leading to given event"""
        # Find the event
        target = None
        for event in reversed(self.events):
            if event.event_id == event_id:
                target = event
                break

        if not target or not target.correlation_id:
            return [target] if target else []

        return self.get_by_correlation(target.correlation_id)


class IntegrationBus:
    """
    Cross-Module Integration Bus for STAN V41.

    Enables event-based communication between all capability modules.
    Supports:
    - Publish/subscribe pattern
    - Event filtering
    - Priority handling
    - Async processing
    - Event history and replay
    """

    def __init__(self, async_mode: bool = False):
        self.subscriptions: Dict[str, Subscription] = {}
        self.type_subscriptions: Dict[EventType, List[str]] = defaultdict(list)
        self.history: EventHistory = EventHistory()
        self.async_mode = async_mode

        # Async processing
        self._event_queue: queue.PriorityQueue = queue.PriorityQueue()
        self._processing_thread: Optional[threading.Thread] = None
        self._running = False

        # Statistics
        self.stats = {
            'events_published': 0,
            'events_delivered': 0,
            'events_filtered': 0,
            'delivery_failures': 0,
            'by_type': defaultdict(int)
        }

        # Thread safety
        self._lock = threading.RLock()

        # World model integration
        self._world_model = None

        if async_mode:
            self._start_processing()

    def set_world_model(self, world_model):
        """Set the world model for automatic updates"""
        self._world_model = world_model

    def subscribe(self,
                  subscriber: str,
                  event_types,  # Can be single EventType or List[EventType]
                  callback: Callable[[Event], None],
                  filter_fn: Optional[Callable[[Event], bool]] = None,
                  priority: EventPriority = EventPriority.NORMAL) -> str:
        """
        Subscribe to events.

        Args:
            subscriber: Name of subscribing module
            event_types: Type(s) of events to receive (single EventType or list)
            callback: Function to call when event received
            filter_fn: Optional filter function
            priority: Subscription priority

        Returns:
            Subscription ID
        """
        # Handle single event type or list
        if isinstance(event_types, EventType):
            event_types = [event_types]

        with self._lock:
            subscription = Subscription(
                subscription_id="",
                subscriber=subscriber,
                event_types=set(event_types),
                callback=callback,
                filter_fn=filter_fn,
                priority=priority
            )

            self.subscriptions[subscription.subscription_id] = subscription

            for event_type in event_types:
                self.type_subscriptions[event_type].append(subscription.subscription_id)

            logger.debug(f"Subscription created: {subscriber} -> {[e.value for e in event_types]}")
            return subscription.subscription_id

    def unsubscribe(self, subscription_id: str):
        """Unsubscribe from events"""
        with self._lock:
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]

                for event_type in subscription.event_types:
                    if subscription_id in self.type_subscriptions[event_type]:
                        self.type_subscriptions[event_type].remove(subscription_id)

                del self.subscriptions[subscription_id]
                logger.debug(f"Unsubscribed: {subscription_id}")

    def publish(self,
                event_type: EventType,
                source: str,
                payload: Dict[str, Any],
                priority: EventPriority = EventPriority.NORMAL,
                correlation_id: Optional[str] = None) -> str:
        """
        Publish an event to the bus.

        Args:
            event_type: Type of event
            source: Publishing module
            payload: Event data
            priority: Event priority
            correlation_id: ID for tracking related events

        Returns:
            Event ID
        """
        event = Event(
            event_id="",
            event_type=event_type,
            source=source,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id or f"corr_{uuid.uuid4().hex[:8]}"
        )

        with self._lock:
            self.stats['events_published'] += 1
            self.stats['by_type'][event_type.value] += 1
            self.history.add(event)

        if self.async_mode:
            self._event_queue.put((event.priority.value, event))
        else:
            self._deliver_event(event)

        # Update world model if connected
        if self._world_model:
            self._update_world_model(event)

        logger.debug(f"Event published: {event_type.value} from {source}")
        return event.event_id

    def _deliver_event(self, event: Event):
        """Deliver event to subscribers"""
        subscription_ids = self.type_subscriptions.get(event.event_type, [])

        for sub_id in subscription_ids:
            subscription = self.subscriptions.get(sub_id)
