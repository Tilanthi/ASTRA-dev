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
Episodic Memory System

Stores specific experiences with temporal, spatial, and contextual information.
Enables retrieval of past experiences and learning from them.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from uuid import uuid4
import pickle
import json
import numpy as np


@dataclass
class Experience:
    """
    A single episodic experience.

    Attributes:
        id: Unique identifier
        timestamp: When the experience occurred
        content: The main content/experience
        context: Associated context information
        emotional_valence: Emotional significance (-1 to 1)
        importance: Importance/importance (0 to 1)
        tags: Searchable tags
        related_experiences: IDs of related experiences
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    emotional_valence: float = 0.0
    importance: float = 0.5
    tags: Set[str] = field(default_factory=set)
    related_experiences: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'content': self.content,
            'context': self.context,
            'emotional_valence': self.emotional_valence,
            'importance': self.importance,
            'tags': list(self.tags),
            'related_experiences': list(self.related_experiences)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Experience':
        """Create Experience from dictionary."""
        return cls(
            id=data['id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            content=data['content'],
            context=data['context'],
            emotional_valence=data['emotional_valence'],
            importance=data['importance'],
            tags=set(data['tags']),
            related_experiences=set(data['related_experiences'])
        )


class EpisodicMemory:
    """
    Episodic memory system for storing and retrieving experiences.

    Provides:
    - Experience storage with contextual information
    - Temporal retrieval (what happened when)
    - Contextual retrieval (what happened in similar contexts)
    - Association linking (related experiences)
    - Importance-based consolidation

    Example:
        >>> memory = EpisodicMemory()
        >>> exp = Experience(content="Analyzed market data")
        >>> memory.store(exp)
        >>> similar = memory.retrieve_similar("market analysis")
    """

    def __init__(self,
                 capacity: int = 10000,
                 consolidation_threshold: float = 0.8):
        """
        Initialize episodic memory.

        Args:
            capacity: Maximum number of experiences to store
            consolidation_threshold: Importance threshold for consolidation
        """
        self.capacity = capacity
        self.consolidation_threshold = consolidation_threshold

        self.experiences: Dict[str, Experience] = {}
        self.temporal_index: List[str] = []
        self.tag_index: Dict[str, Set[str]] = {}
        self.consolidated: Set[str] = set()

    def store(self, experience: Experience) -> str:
        """
        Store an experience in episodic memory.

        Args:
            experience: Experience to store

        Returns:
            Experience ID
        """
        # Check capacity
        if len(self.experiences) >= self.capacity:
            self._evict_least_important()

        # Store experience
        self.experiences[experience.id] = experience
        self.temporal_index.append(experience.id)

        # Update tag index
        for tag in experience.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(experience.id)

        # Check for consolidation
        if experience.importance >= self.consolidation_threshold:
            self.consolidated.add(experience.id)

        return experience.id

    def retrieve(self,
                 experience_id: str) -> Optional[Experience]:
        """Retrieve experience by ID."""
        return self.experiences.get(experience_id)

    def retrieve_temporal(self,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          limit: int = 100) -> List[Experience]:
        """
        Retrieve experiences from time period.

        Args:
            start_time: Start of time period
            end_time: End of time period
            limit: Maximum number to return

        Returns:
            List of experiences in temporal order
        """
        experiences = []

        for exp_id in reversed(self.temporal_index):
            exp = self.experiences[exp_id]

            # Filter by time
            if start_time and exp.timestamp < start_time:
                continue
            if end_time and exp.timestamp > end_time:
                continue

            experiences.append(exp)

            if len(experiences) >= limit:
                break

        return experiences

    def retrieve_similar(self,
                        query: str,
                        limit: int = 10) -> List[Experience]:
        """
        Retrieve experiences similar to query.

        Simple keyword-based similarity.
        For more advanced retrieval, use semantic memory.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of similar experiences
        """
        query_lower = query.lower()
        scored = []

        for exp in self.experiences.values():
            # Simple text matching
            score = 0.0

            if query_lower in exp.content.lower():
                score += 1.0

            for tag in exp.tags:
                if query_lower in tag.lower():
                    score += 0.5

            # Boost by importance
            score *= (1 + exp.importance)

            if score > 0:
                scored.append((exp, score))

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)

        return [exp for exp, score in scored[:limit]]

    def retrieve_by_tags(self,
                         tags: Set[str],
                         require_all: bool = False) -> List[Experience]:
        """
        Retrieve experiences by tags.

        Args:
            tags: Tags to search for
            require_all: True = must have all tags, False = any tag

        Returns:
            List of matching experiences
        """
        if not tags:
            return []

        # Get matching IDs
        if require_all:
            exp_ids = None
            for tag in tags:
                if tag in self.tag_index:
                    if exp_ids is None:
                        exp_ids = self.tag_index[tag].copy()
                    else:
                        exp_ids &= self.tag_index[tag]
                else:
                    return []
            exp_ids = exp_ids if exp_ids else set()
        else:
            exp_ids = set()
            for tag in tags:
                if tag in self.tag_index:
                    exp_ids |= self.tag_index[tag]

        return [self.experiences[eid] for eid in exp_ids]

    def associate(self,
                  exp_id1: str,
                  exp_id2: str,
                  strength: float = 1.0) -> None:
        """
        Create association between two experiences.

        Args:
            exp_id1: First experience ID
            exp_id2: Second experience ID
            strength: Association strength (not currently used)
        """
        if exp_id1 in self.experiences and exp_id2 in self.experiences:
            self.experiences[exp_id1].related_experiences.add(exp_id2)
            self.experiences[exp_id2].related_experiences.add(exp_id1)

    def get_related(self,
                    exp_id: str,
                    depth: int = 1) -> List[Experience]:
        """
        Get related experiences.

        Args:
            exp_id: Experience ID
            depth: How many hops to explore

        Returns:
            List of related experiences
        """
        if exp_id not in self.experiences:
            return []

        visited = {exp_id}
        current = {exp_id}

        for _ in range(depth):
            next_level = set()
            for eid in current:
                if eid in self.experiences:
                    next_level |= self.experiences[eid].related_experiences
            current = next_level - visited
            visited |= current

            if not current:
                break

        visited.remove(exp_id)

        return [self.experiences[eid] for eid in visited if eid in self.experiences]

    def _evict_least_important(self) -> None:
        """Evict least important experience when at capacity."""
        if not self.experiences:
            return

        # Don't evict consolidated experiences
        candidates = [
            (eid, exp)
            for eid, exp in self.experiences.items()
            if eid not in self.consolidated
        ]

        if not candidates:
            # All consolidated, evict lowest importance
            candidates = list(self.experiences.items())

        # Sort by importance
        candidates.sort(key=lambda x: x[1].importance)

        # Evict least important
        evict_id, evict_exp = candidates[0]

        del self.experiences[evict_id]
        self.temporal_index.remove(evict_id)

        # Clean up tag index
        for tag in evict_exp.tags:
            if tag in self.tag_index:
                self.tag_index[tag].discard(evict_id)
                if not self.tag_index[tag]:
                    del self.tag_index[tag]

    def save(self, filepath: str) -> None:
        """Save episodic memory to file."""
        data = {
            'experiences': {
                eid: exp.to_dict()
                for eid, exp in self.experiences.items()
            },
            'temporal_index': self.temporal_index,
            'tag_index': {
                tag: list(ids)
                for tag, ids in self.tag_index.items()
            },
            'consolidated': list(self.consolidated)
        }

        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

    def load(self, filepath: str) -> None:
        """Load episodic memory from file."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        self.experiences = {
            eid: Experience.from_dict(exp_data)
            for eid, exp_data in data['experiences'].items()
        }
        self.temporal_index = data['temporal_index']
        self.tag_index = {
            tag: set(ids)
            for tag, ids in data['tag_index'].items()
        }
        self.consolidated = set(data['consolidated'])

    def stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            'total_experiences': len(self.experiences),
            'consolidated_experiences': len(self.consolidated),
            'total_tags': len(self.tag_index),
            'average_importance': np.mean([
                exp.importance for exp in self.experiences.values()
            ]) if self.experiences else 0
        }



def consolidate_memory(memory_store: Dict[str, Any],
                     importance_threshold: float = 0.5) -> Dict[str, Any]:
    """
    Consolidate memories by merging similar entries and strengthening important ones.

    Simulates hippocampal-neocortical memory consolidation.

    Args:
        memory_store: Dictionary with memory entries
        importance_threshold: Minimum importance for long-term storage

    Returns:
        Consolidated memory store
    """
    import numpy as np

    consolidated = {
        'long_term': [],
        'short_term': [],
        'discarded': []
    }

    # Get all memories
    memories = memory_store.get('memories', [])

    for memory in memories:
        importance = memory.get('importance', 0.5)
        access_count = memory.get('access_count', 0)
        age = memory.get('age', 0)

        # Compute consolidation score
        consolidation_score = importance * (1 + 0.1 * access_count) / (1 + 0.01 * age)

        if consolidation_score > importance_threshold:
            # Check for similar memories to merge
            merged = False
            for lt_mem in consolidated['long_term']:
                similarity = _compute_memory_similarity(memory, lt_mem)
                if similarity > 0.8:
                    # Merge memories
                    lt_mem['access_count'] += memory.get('access_count', 0)
                    lt_mem['importance'] = max(lt_mem['importance'], importance)
                    lt_mem['merge_count'] = lt_mem.get('merge_count', 1) + 1
                    merged = True
                    break

            if not merged:
                consolidated['long_term'].append(memory.copy())
        else:
            consolidated['short_term'].append(memory.copy())

    return consolidated


def _compute_memory_similarity(mem1: Dict[str, Any],
                               mem2: Dict[str, Any]) -> float:
    """Compute similarity between two memories."""
    # Simple similarity based on content overlap
    content1 = str(mem1.get('content', ''))
    content2 = str(mem2.get('content', ''))

    if not content1 or not content2:
        return 0.0

    # Jaccard similarity of word sets
    words1 = set(content1.lower().split())
    words2 = set(content2.lower().split())

    intersection = words1 & words2
    union = words1 | words2

    if not union:
        return 0.0

    return len(intersection) / len(union)


def memory_replay(memory_store: Dict[str, Any],
                 replay_count: int = 10) -> List[Dict[str, Any]]:
    """
    Select memories for replay to strengthen retention.

    Implements prioritized experience replay for memory systems.

    Args:
        memory_store: Dictionary with memory entries
        replay_count: Number of memories to select for replay

    Returns:
        List of memories selected for replay
    """
    import numpy as np

    memories = memory_store.get('memories', [])

    # Compute priority scores
    priorities = []
    for memory in memories:
        importance = memory.get('importance', 0.5)
        access_count = memory.get('access_count', 0)
        last_access = memory.get('last_access_time', 0)
        error_signal = memory.get('prediction_error', 0.0)

        # Priority: combination of importance, recency, and error
        priority = importance + 0.1 * error_signal - 0.01 * last_access

        # Boost under-accessed but important memories
        if access_count < 3 and importance > 0.7:
            priority += 0.5

        priorities.append((priority, memory))

    # Sort by priority and select top
    priorities.sort(key=lambda x: x[0], reverse=True)

    selected = [p[1] for p in priorities[:replay_count]]

    # Update access statistics
    for memory in selected:
        memory['access_count'] = memory.get('access_count', 0) + 1
        memory['last_access_time'] = time.time()

    return selected
