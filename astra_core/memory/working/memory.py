"""
Working Memory System

Active maintenance and manipulation of information during reasoning.
Based on Baddeley's model of working memory.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from collections import deque


@dataclass
class ActivationRecord:
    """An active item in working memory."""
    id: str
    content: Any
    activation: float = 1.0  # Decays over time
    importance: float = 0.5
    tags: Set[str] = field(default_factory=set)


class WorkingMemory:
    """
    Working memory system for active reasoning.

    Provides:
    - Active maintenance of information
    - Attentional focus
    - Capacity-limited storage (7±2 items)
    - Activation decay
    - Manipulation operations
    """

    def __init__(self,
                 capacity: int = 7,
                 decay_rate: float = 0.1):
        self.capacity = capacity
        self.decay_rate = decay_rate

        self.active: Dict[str, ActivationRecord] = {}
        self.attention_set: Set[str] = set()
        self.operations: List[str] = []

    def add(self,
            item_id: str,
            content: Any,
            importance: float = 0.5,
            tags: Optional[Set[str]] = None) -> bool:
        """
        Add item to working memory.

        Args:
            item_id: Unique identifier
            content: Content to store
            importance: Importance (affects decay resistance)
            tags: Searchable tags

        Returns:
            True if added, False if at capacity
        """
        if len(self.active) >= self.capacity and item_id not in self.active:
            # Make room by removing lowest activation
            self._evict_lowest_activation()

        record = ActivationRecord(
            id=item_id,
            content=content,
            importance=importance,
            tags=tags or set()
        )
        self.active[item_id] = record
        self.operations.append(f"add:{item_id}")
        return True

    def get(self, item_id: str) -> Optional[Any]:
        """Get content from working memory."""
        if item_id in self.active:
            # Boost activation on access
            self.active[item_id].activation = min(1.0,
                self.active[item_id].activation + 0.2)
            return self.active[item_id].content
        return None

    def remove(self, item_id: str) -> bool:
        """Remove item from working memory."""
        if item_id in self.active:
            del self.active[item_id]
            self.attention_set.discard(item_id)
            self.operations.append(f"remove:{item_id}")
            return True
        return False

    def attend_to(self, item_id: str) -> None:
        """Bring item into attentional focus."""
        if item_id in self.active:
            self.attention_set.add(item_id)
            self.active[item_id].activation = 1.0
            self.operations.append(f"attend:{item_id}")

    def get_attention_set(self) -> List[Any]:
        """Get contents of attentional focus."""
        return [
            self.active[eid].content
            for eid in self.attention_set
            if eid in self.active
        ]

    def manipulate(self,
                   operation: str,
                   item_ids: List[str]) -> Any:
        """
        Perform manipulation operation on items.

        Args:
            operation: Operation type ('combine', 'compare', 'transform')
            item_ids: Items to manipulate

        Returns:
            Result of manipulation
        """
        items = [self.get(eid) for eid in item_ids if eid in self.active]

        if operation == 'combine':
            # Combine items
            result = {'combined': items}
        elif operation == 'compare':
            # Compare items
            result = {'compared': items}
        elif operation == 'transform':
            # Transform items
            result = {'transformed': items}
        else:
            result = None

        self.operations.append(f"{operation}:{item_ids}")
        return result

    def step(self) -> None:
        """Decay activations (called each reasoning step)."""
        to_remove = []

        for eid, record in self.active.items():
            # Decay activation
            decay = self.decay_rate * (1 - record.importance)
            record.activation -= decay

            # Mark for removal if activation too low
            if record.activation <= 0.1:
                to_remove.append(eid)

        # Remove decayed items (unless in attention)
        for eid in to_remove:
            if eid not in self.attention_set:
                self.remove(eid)

    def clear(self) -> None:
        """Clear working memory."""
        self.active.clear()
        self.attention_set.clear()
        self.operations = []

    def _evict_lowest_activation(self) -> None:
        """Remove item with lowest activation."""
        if not self.active:
            return

        # Don't evict items in attention
        candidates = [
            (eid, record)
            for eid, record in self.active.items()
            if eid not in self.attention_set
        ]

        if not candidates:
            return

        # Evict lowest activation
        candidates.sort(key=lambda x: x[1].activation)
        evict_id = candidates[0][0]
        self.remove(evict_id)

    def state(self) -> Dict[str, Any]:
        """Get current working memory state."""
        return {
            'active_count': len(self.active),
            'attention_count': len(self.attention_set),
            'capacity_remaining': self.capacity - len(self.active),
            'average_activation': np.mean([
                r.activation for r in self.active.values()
            ]) if self.active else 0,
            'operations_count': len(self.operations)
        }
