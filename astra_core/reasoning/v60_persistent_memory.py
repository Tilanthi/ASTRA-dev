"""
V60 Persistent Memory Architecture

A three-tier memory system enabling cognitive continuity through:
- Working Memory: Limited capacity buffer for current cognitive focus
- Episodic Memory: Temporally-indexed experiences with retrieval
- Semantic Memory: Consolidated knowledge extracted from episodes

Key innovations:
1. Memory consolidation that extracts patterns from experiences
2. Interference-aware storage preventing catastrophic forgetting
3. Associative retrieval using similarity and spreading activation
4. Sleep-inspired offline consolidation cycles
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from collections import deque
import heapq
import time
import hashlib
import json


class MemoryType(Enum):
    """Types of memory items"""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class RetrievalStrategy(Enum):
    """Memory retrieval strategies"""
    DIRECT = "direct"           # Exact match retrieval
    SIMILARITY = "similarity"   # Similarity-based retrieval
    TEMPORAL = "temporal"       # Time-based retrieval
    SPREADING = "spreading"     # Spreading activation
    COMPOSITE = "composite"     # Combined strategies


class ConsolidationMode(Enum):
    """Memory consolidation modes"""
    ONLINE = "online"           # Continuous consolidation
    OFFLINE = "offline"         # Batch consolidation (sleep-like)
    TRIGGERED = "triggered"     # Event-triggered consolidation


@dataclass
class MemoryItem:
    """A single memory item"""
    id: str
    content: Any
    memory_type: MemoryType
    timestamp: float
    importance: float = 0.5
    access_count: int = 0
    last_access: float = 0.0
    embedding: Optional[np.ndarray] = None
    associations: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    decay_rate: float = 0.01

    def compute_activation(self, current_time: float) -> float:
        """Compute current activation level based on ACT-R model"""
        time_delta = max(current_time - self.last_access, 1.0)
        base_activation = np.log(self.access_count + 1)
        decay = -self.decay_rate * np.log(time_delta)
        return base_activation + decay + self.importance

    def update_access(self, current_time: float):
        """Update access statistics"""
        self.access_count += 1
        self.last_access = current_time


@dataclass
class Episode:
    """An episodic memory - a specific experience"""
    id: str
    events: List[Dict[str, Any]]
    context: Dict[str, Any]
    timestamp: float
    duration: float
    emotional_valence: float = 0.0
    importance: float = 0.5
    consolidated: bool = False
    extracted_patterns: List[str] = field(default_factory=list)

    def get_summary(self) -> Dict[str, Any]:
        """Generate episode summary"""
        return {
            'id': self.id,
            'event_count': len(self.events),
            'duration': self.duration,
            'importance': self.importance,
            'consolidated': self.consolidated
        }


@dataclass
class SemanticConcept:
    """A semantic memory - consolidated knowledge"""
    id: str
    name: str
    definition: str
    properties: Dict[str, Any]
    relations: Dict[str, List[str]]  # relation_type -> [target_ids]
    source_episodes: List[str]
    confidence: float = 0.5
    abstraction_level: int = 0
    embedding: Optional[np.ndarray] = None

    def update_confidence(self, evidence: float):
        """Bayesian update of concept confidence"""
        # Simple Bayesian update
        prior = self.confidence
        likelihood = 0.9 if evidence > 0.5 else 0.1
        posterior = (likelihood * prior) / (
            likelihood * prior + (1 - likelihood) * (1 - prior)
        )
        self.confidence = posterior


class WorkingMemory:
    """
    Limited capacity working memory buffer.
    Implements Miller's 7±2 capacity with chunking.
    """

    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.items: deque = deque(maxlen=capacity)
        self.focus_item: Optional[MemoryItem] = None
        self.chunk_registry: Dict[str, List[str]] = {}
        self.activation_threshold: float = 0.3

    def add(self, item: MemoryItem) -> bool:
        """Add item to working memory, possibly displacing lowest activation"""
        current_time = time.time()

        if len(self.items) >= self.capacity:
            # Find lowest activation item
            activations = [
                (i, it.compute_activation(current_time))
                for i, it in enumerate(self.items)
            ]
            min_idx, min_act = min(activations, key=lambda x: x[1])

            if item.importance > min_act:
                # Replace lowest activation item
                self.items[min_idx] = item
                return True
            return False

        self.items.append(item)
        return True

    def get_focus(self) -> Optional[MemoryItem]:
        """Get current focus of attention"""
        return self.focus_item

    def set_focus(self, item_id: str) -> bool:
        """Set focus to specific item"""
        for item in self.items:
            if item.id == item_id:
                self.focus_item = item
                item.update_access(time.time())
                return True
        return False

    def create_chunk(self, chunk_id: str, item_ids: List[str]) -> bool:
        """Create a chunk grouping multiple items"""
        valid_ids = [iid for iid in item_ids if any(it.id == iid for it in self.items)]
        if len(valid_ids) >= 2:
            self.chunk_registry[chunk_id] = valid_ids
            return True
        return False

    def get_active_items(self) -> List[MemoryItem]:
        """Get items above activation threshold"""
        current_time = time.time()
        return [
            item for item in self.items
            if item.compute_activation(current_time) > self.activation_threshold
        ]

    def clear(self):
        """Clear working memory"""
        self.items.clear()
        self.focus_item = None
        self.chunk_registry.clear()


class EpisodicMemory:
    """
    Long-term storage for specific experiences.
    Supports temporal and content-based retrieval.
    """

    def __init__(self, max_episodes: int = 10000):
        self.max_episodes = max_episodes
        self.episodes: Dict[str, Episode] = {}
        self.temporal_index: List[Tuple[float, str]] = []  # (timestamp, episode_id)
        self.context_index: Dict[str, Set[str]] = {}  # context_key -> episode_ids
        self.embedding_matrix: Optional[np.ndarray] = None
        self.episode_embeddings: Dict[str, int] = {}  # episode_id -> matrix_row

    def store(self, episode: Episode) -> bool:
        """Store an episode"""
        if len(self.episodes) >= self.max_episodes:
            self._forget_oldest()

        self.episodes[episode.id] = episode
        heapq.heappush(self.temporal_index, (episode.timestamp, episode.id))

        # Index by context
        for key, value in episode.context.items():
            context_key = f"{key}:{value}"
            if context_key not in self.context_index:
                self.context_index[context_key] = set()
            self.context_index[context_key].add(episode.id)

        return True

    def retrieve_by_time(
        self,
        start_time: float,
        end_time: Optional[float] = None
    ) -> List[Episode]:
        """Retrieve episodes within time range"""
        if end_time is None:
            end_time = time.time()

        results = []
        for ep_id, episode in self.episodes.items():
            if start_time <= episode.timestamp <= end_time:
                results.append(episode)

        return sorted(results, key=lambda e: e.timestamp)

    def retrieve_by_context(
        self,
        context: Dict[str, Any],
        max_results: int = 10
    ) -> List[Episode]:
        """Retrieve episodes matching context"""
        candidate_ids: Set[str] = set()

        for key, value in context.items():
            context_key = f"{key}:{value}"
            if context_key in self.context_index:
                if not candidate_ids:
                    candidate_ids = self.context_index[context_key].copy()
                else:
                    candidate_ids &= self.context_index[context_key]

        episodes = [self.episodes[eid] for eid in candidate_ids if eid in self.episodes]
        return sorted(episodes, key=lambda e: e.importance, reverse=True)[:max_results]

    def retrieve_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[Tuple[Episode, float]]:
        """Retrieve episodes by embedding similarity"""
        if self.embedding_matrix is None or len(self.episode_embeddings) == 0:
            return []

        # Compute cosine similarities
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        matrix_norms = self.embedding_matrix / (
            np.linalg.norm(self.embedding_matrix, axis=1, keepdims=True) + 1e-10
        )
        similarities = matrix_norms @ query_norm

        # Get top-k
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        id_to_row = {v: k for k, v in self.episode_embeddings.items()}
        for idx in top_indices:
            if idx in id_to_row:
                ep_id = id_to_row[idx]
                if ep_id in self.episodes:
                    results.append((self.episodes[ep_id], float(similarities[idx])))

        return results

    def _forget_oldest(self):
        """Forget oldest, least important episode"""
        if not self.episodes:
            return

        # Find candidate for forgetting (old + low importance)
        candidates = []
        current_time = time.time()

        for ep_id, episode in self.episodes.items():
            if not episode.consolidated:
                age = current_time - episode.timestamp
                score = age * (1 - episode.importance)
                candidates.append((score, ep_id))

        if candidates:
            _, forget_id = max(candidates, key=lambda x: x[0])
            self._remove_episode(forget_id)

    def _remove_episode(self, episode_id: str):
        """Remove episode from all indices"""
        if episode_id in self.episodes:
            episode = self.episodes[episode_id]

            # Remove from context index
            for key, value in episode.context.items():
                context_key = f"{key}:{value}"
                if context_key in self.context_index:
                    self.context_index[context_key].discard(episode_id)

            del self.episodes[episode_id]


class SemanticMemory:
    """
    Long-term storage for consolidated knowledge.
    Organized as a semantic network.
    """

    def __init__(self, max_concepts: int = 50000):
        self.max_concepts = max_concepts
        self.concepts: Dict[str, SemanticConcept] = {}
        self.name_index: Dict[str, str] = {}  # name -> concept_id
        self.relation_graph: Dict[str, Dict[str, List[str]]] = {}  # concept_id -> {relation -> targets}
        self.embedding_matrix: Optional[np.ndarray] = None
        self.concept_embeddings: Dict[str, int] = {}

    def store(self, concept: SemanticConcept) -> bool:
        """Store a semantic concept"""
        if len(self.concepts) >= self.max_concepts:
            self._prune_low_confidence()

        self.concepts[concept.id] = concept
        self.name_index[concept.name.lower()] = concept.id

        # Update relation graph
        if concept.id not in self.relation_graph:
            self.relation_graph[concept.id] = {}
        self.relation_graph[concept.id] = concept.relations.copy()

        return True

    def retrieve_by_name(self, name: str) -> Optional[SemanticConcept]:
        """Retrieve concept by name"""
        name_lower = name.lower()
        if name_lower in self.name_index:
            concept_id = self.name_index[name_lower]
            return self.concepts.get(concept_id)
        return None

    def retrieve_related(
        self,
        concept_id: str,
        relation_type: Optional[str] = None,
        max_hops: int = 2
    ) -> List[Tuple[SemanticConcept, str, int]]:
        """Retrieve related concepts via graph traversal"""
        results = []
        visited = {concept_id}
        frontier = [(concept_id, 0)]  # (concept_id, hop_count)

        while frontier:
            current_id, hops = frontier.pop(0)

            if hops >= max_hops:
                continue

            if current_id not in self.relation_graph:
                continue

            relations = self.relation_graph[current_id]

            for rel_type, targets in relations.items():
                if relation_type and rel_type != relation_type:
                    continue

                for target_id in targets:
                    if target_id not in visited and target_id in self.concepts:
                        visited.add(target_id)
                        results.append((self.concepts[target_id], rel_type, hops + 1))
                        frontier.append((target_id, hops + 1))

        return results

    def retrieve_by_property(
        self,
        property_name: str,
        property_value: Any
    ) -> List[SemanticConcept]:
        """Retrieve concepts with matching property"""
        results = []
        for concept in self.concepts.values():
            if property_name in concept.properties:
                if concept.properties[property_name] == property_value:
                    results.append(concept)
        return results

    def spreading_activation(
        self,
        source_ids: List[str],
        activation_strength: float = 1.0,
        decay: float = 0.5,
        threshold: float = 0.1,
        max_iterations: int = 3
    ) -> Dict[str, float]:
        """Spreading activation retrieval"""
        activations = {sid: activation_strength for sid in source_ids if sid in self.concepts}

        for _ in range(max_iterations):
            new_activations = activations.copy()

            for concept_id, activation in activations.items():
                if activation < threshold:
                    continue

                if concept_id not in self.relation_graph:
                    continue

                spread_activation = activation * decay

                for relation_type, targets in self.relation_graph[concept_id].items():
                    for target_id in targets:
                        if target_id in self.concepts:
                            current = new_activations.get(target_id, 0)
                            new_activations[target_id] = max(current, spread_activation)

            activations = new_activations

        return {k: v for k, v in activations.items() if v >= threshold}

    def _prune_low_confidence(self):
        """Remove lowest confidence concepts"""
        if not self.concepts:
            return

        # Sort by confidence
        sorted_concepts = sorted(
            self.concepts.items(),
            key=lambda x: x[1].confidence
        )

        # Remove bottom 10%
        num_to_remove = max(1, len(sorted_concepts) // 10)
        for concept_id, _ in sorted_concepts[:num_to_remove]:
            self._remove_concept(concept_id)

    def _remove_concept(self, concept_id: str):
        """Remove concept from all indices"""
        if concept_id in self.concepts:
            concept = self.concepts[concept_id]

            if concept.name.lower() in self.name_index:
                del self.name_index[concept.name.lower()]

            if concept_id in self.relation_graph:
                del self.relation_graph[concept_id]

            del self.concepts[concept_id]


class MemoryConsolidator:
    """
    Consolidates episodic memories into semantic knowledge.
    Implements sleep-inspired offline consolidation.
    """

    def __init__(
        self,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory,
        consolidation_threshold: int = 3
    ):
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory
        self.consolidation_threshold = consolidation_threshold
        self.pattern_registry: Dict[str, Dict[str, Any]] = {}

    def consolidate_online(self, episode: Episode) -> List[SemanticConcept]:
        """Online consolidation - extract patterns immediately"""
        extracted_concepts = []

        # Extract event patterns
        event_patterns = self._extract_event_patterns(episode)

        for pattern in event_patterns:
            pattern_key = self._pattern_key(pattern)

            if pattern_key not in self.pattern_registry:
                self.pattern_registry[pattern_key] = {
                    'pattern': pattern,
                    'count': 0,
                    'episodes': []
                }

            self.pattern_registry[pattern_key]['count'] += 1
            self.pattern_registry[pattern_key]['episodes'].append(episode.id)

            # Consolidate if threshold reached
            if self.pattern_registry[pattern_key]['count'] >= self.consolidation_threshold:
                concept = self._create_concept_from_pattern(
                    pattern,
                    self.pattern_registry[pattern_key]['episodes']
                )
                if concept:
                    self.semantic_memory.store(concept)
                    extracted_concepts.append(concept)
                    episode.extracted_patterns.append(concept.id)

        episode.consolidated = len(extracted_concepts) > 0
        return extracted_concepts

    def consolidate_offline(self, batch_size: int = 100) -> List[SemanticConcept]:
        """Offline consolidation - batch process unconsolidated episodes"""
        # Get unconsolidated episodes
        unconsolidated = [
            ep for ep in self.episodic_memory.episodes.values()
            if not ep.consolidated
        ]

        # Sort by importance
        unconsolidated.sort(key=lambda e: e.importance, reverse=True)
        batch = unconsolidated[:batch_size]

        all_concepts = []

        # Phase 1: Extract patterns from all episodes
        for episode in batch:
            patterns = self._extract_event_patterns(episode)
            for pattern in patterns:
                pattern_key = self._pattern_key(pattern)

                if pattern_key not in self.pattern_registry:
                    self.pattern_registry[pattern_key] = {
                        'pattern': pattern,
                        'count': 0,
                        'episodes': []
                    }

                self.pattern_registry[pattern_key]['count'] += 1
                self.pattern_registry[pattern_key]['episodes'].append(episode.id)

        # Phase 2: Create concepts from frequent patterns
        for pattern_key, registry in self.pattern_registry.items():
            if registry['count'] >= self.consolidation_threshold:
                concept = self._create_concept_from_pattern(
                    registry['pattern'],
                    registry['episodes']
                )
                if concept:
                    self.semantic_memory.store(concept)
                    all_concepts.append(concept)

                    # Mark episodes as having extracted this pattern
                    for ep_id in registry['episodes']:
                        if ep_id in self.episodic_memory.episodes:
                            self.episodic_memory.episodes[ep_id].extracted_patterns.append(concept.id)
                            self.episodic_memory.episodes[ep_id].consolidated = True

        return all_concepts

    def _extract_event_patterns(self, episode: Episode) -> List[Dict[str, Any]]:
        """Extract abstract patterns from episode events"""
        patterns = []

        # Sequence patterns
        if len(episode.events) >= 2:
            for i in range(len(episode.events) - 1):
                pattern = {
                    'type': 'sequence',
                    'first': self._abstract_event(episode.events[i]),
                    'second': self._abstract_event(episode.events[i + 1])
                }
                patterns.append(pattern)

        # Co-occurrence patterns
        event_types = set()
        for event in episode.events:
            if 'type' in event:
                event_types.add(event['type'])

        if len(event_types) >= 2:
            pattern = {
                'type': 'co_occurrence',
                'events': sorted(list(event_types))
            }
            patterns.append(pattern)

        # Causal patterns (if marked)
        for event in episode.events:
            if 'causes' in event:
                pattern = {
                    'type': 'causal',
                    'cause': self._abstract_event(event),
                    'effect': event['causes']
                }
                patterns.append(pattern)

        return patterns

    def _abstract_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Abstract an event to its essential structure"""
        abstract = {}

        if 'type' in event:
            abstract['type'] = event['type']

        if 'action' in event:
            abstract['action'] = event['action']

        if 'category' in event:
            abstract['category'] = event['category']

        return abstract

    def _pattern_key(self, pattern: Dict[str, Any]) -> str:
        """Generate unique key for pattern"""
        pattern_str = json.dumps(pattern, sort_keys=True)
        return hashlib.md5(pattern_str.encode()).hexdigest()

    def _create_concept_from_pattern(
        self,
        pattern: Dict[str, Any],
        source_episodes: List[str]
    ) -> Optional[SemanticConcept]:
        """Create semantic concept from pattern"""
        pattern_type = pattern.get('type', 'unknown')

        if pattern_type == 'sequence':
            name = f"sequence_{pattern['first'].get('type', 'x')}_to_{pattern['second'].get('type', 'y')}"
            definition = f"A temporal sequence where {pattern['first']} is followed by {pattern['second']}"
            relations = {
                'precedes': [pattern['first'].get('type', 'unknown')],
                'follows': [pattern['second'].get('type', 'unknown')]
            }
        elif pattern_type == 'co_occurrence':
            name = f"co_occurrence_{'_'.join(pattern['events'][:3])}"
            definition = f"Events that tend to occur together: {pattern['events']}"
            relations = {
                'co_occurs_with': pattern['events']
            }
        elif pattern_type == 'causal':
            name = f"causes_{pattern['cause'].get('type', 'x')}_to_{pattern['effect']}"
            definition = f"Causal relationship where {pattern['cause']} causes {pattern['effect']}"
            relations = {
                'causes': [pattern['effect']],
                'caused_by': [pattern['cause'].get('type', 'unknown')]
            }
        else:
            return None

        concept_id = f"concept_{self._pattern_key(pattern)}"

        return SemanticConcept(
            id=concept_id,
            name=name,
            definition=definition,
            properties={'pattern': pattern, 'frequency': len(source_episodes)},
            relations=relations,
            source_episodes=source_episodes,
            confidence=min(0.9, 0.5 + 0.1 * len(source_episodes)),
            abstraction_level=1
        )


class MemoryRetriever:
    """
    Unified memory retrieval across all memory systems.
    Implements multiple retrieval strategies.
    """

    def __init__(
        self,
        working_memory: WorkingMemory,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory
    ):
        self.working = working_memory
        self.episodic = episodic_memory
        self.semantic = semantic_memory

    def retrieve(
        self,
        query: Dict[str, Any],
        strategy: RetrievalStrategy = RetrievalStrategy.COMPOSITE,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Unified retrieval across memory systems"""
        results = []

        if strategy == RetrievalStrategy.DIRECT:
            results = self._direct_retrieval(query, max_results)
        elif strategy == RetrievalStrategy.SIMILARITY:
            results = self._similarity_retrieval(query, max_results)
        elif strategy == RetrievalStrategy.TEMPORAL:
            results = self._temporal_retrieval(query, max_results)
        elif strategy == RetrievalStrategy.SPREADING:
            results = self._spreading_retrieval(query, max_results)
        else:  # COMPOSITE
            results = self._composite_retrieval(query, max_results)

        return results

    def _direct_retrieval(
        self,
        query: Dict[str, Any],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Direct/exact match retrieval"""
        results = []

        # Check working memory
        for item in self.working.items:
            if self._matches_query(item.content, query):
                results.append({
                    'source': 'working',
                    'item': item,
                    'relevance': 1.0
                })

        # Check semantic memory by name
        if 'name' in query:
            concept = self.semantic.retrieve_by_name(query['name'])
            if concept:
                results.append({
                    'source': 'semantic',
                    'item': concept,
                    'relevance': concept.confidence
                })

        return results[:max_results]

    def _similarity_retrieval(
        self,
        query: Dict[str, Any],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Similarity-based retrieval using embeddings"""
        results = []

        if 'embedding' in query:
            embedding = query['embedding']

            # Episodic similarity
            similar_episodes = self.episodic.retrieve_similar(embedding, max_results)
            for episode, similarity in similar_episodes:
                results.append({
                    'source': 'episodic',
                    'item': episode,
                    'relevance': similarity
                })

        return sorted(results, key=lambda x: x['relevance'], reverse=True)[:max_results]

    def _temporal_retrieval(
        self,
        query: Dict[str, Any],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Time-based retrieval"""
        results = []

        start_time = query.get('start_time', 0)
        end_time = query.get('end_time', time.time())

        episodes = self.episodic.retrieve_by_time(start_time, end_time)
        for episode in episodes[:max_results]:
            results.append({
                'source': 'episodic',
                'item': episode,
                'relevance': episode.importance
            })

        return results

    def _spreading_retrieval(
        self,
        query: Dict[str, Any],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Spreading activation retrieval"""
        results = []

        if 'concept_ids' in query:
            activations = self.semantic.spreading_activation(
                query['concept_ids'],
                decay=query.get('decay', 0.5),
                threshold=query.get('threshold', 0.1)
            )

            for concept_id, activation in sorted(
                activations.items(),
                key=lambda x: x[1],
                reverse=True
            )[:max_results]:
                if concept_id in self.semantic.concepts:
                    results.append({
                        'source': 'semantic',
                        'item': self.semantic.concepts[concept_id],
                        'relevance': activation
                    })

        return results

    def _composite_retrieval(
        self,
        query: Dict[str, Any],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Composite retrieval combining multiple strategies"""
        all_results = []

        # Get results from each strategy
        all_results.extend(self._direct_retrieval(query, max_results))
        all_results.extend(self._similarity_retrieval(query, max_results))
        all_results.extend(self._temporal_retrieval(query, max_results))
        all_results.extend(self._spreading_retrieval(query, max_results))

        # Deduplicate and rank
        seen = set()
        unique_results = []

        for result in all_results:
            item_id = getattr(result['item'], 'id', str(id(result['item'])))
            if item_id not in seen:
                seen.add(item_id)
                unique_results.append(result)

        # Sort by relevance
        unique_results.sort(key=lambda x: x['relevance'], reverse=True)

        return unique_results[:max_results]

    def _matches_query(self, content: Any, query: Dict[str, Any]) -> bool:
        """Check if content matches query"""
        if not isinstance(content, dict):
            return False

        for key, value in query.items():
            if key in ['embedding', 'start_time', 'end_time', 'concept_ids']:
                continue
            if key in content and content[key] == value:
                return True

        return False


class PersistentMemorySystem:
    """
    Complete persistent memory architecture integrating all components.
    """

    def __init__(
        self,
        working_capacity: int = 7,
        max_episodes: int = 10000,
        max_concepts: int = 50000,
        consolidation_mode: ConsolidationMode = ConsolidationMode.ONLINE
    ):
        self.working = WorkingMemory(capacity=working_capacity)
        self.episodic = EpisodicMemory(max_episodes=max_episodes)
        self.semantic = SemanticMemory(max_concepts=max_concepts)
        self.consolidator = MemoryConsolidator(
            self.episodic,
            self.semantic
        )
        self.retriever = MemoryRetriever(
            self.working,
            self.episodic,
            self.semantic
        )
        self.consolidation_mode = consolidation_mode
        self.stats = {
            'episodes_stored': 0,
            'concepts_created': 0,
            'consolidations_run': 0,
            'retrievals': 0
        }

    def attend(self, content: Any, importance: float = 0.5) -> MemoryItem:
        """Add item to working memory (attention)"""
        item = MemoryItem(
            id=f"wm_{time.time()}_{hash(str(content)) % 10000}",
            content=content,
            memory_type=MemoryType.WORKING,
            timestamp=time.time(),
            importance=importance,
            last_access=time.time()
        )
        self.working.add(item)
        return item

    def experience(
        self,
        events: List[Dict[str, Any]],
        context: Dict[str, Any],
        importance: float = 0.5,
        emotional_valence: float = 0.0
    ) -> Episode:
        """Record an experience as episodic memory"""
        episode = Episode(
            id=f"ep_{time.time()}_{np.random.randint(10000)}",
            events=events,
            context=context,
            timestamp=time.time(),
            duration=0.0,
            emotional_valence=emotional_valence,
            importance=importance
        )

        self.episodic.store(episode)
        self.stats['episodes_stored'] += 1

        # Online consolidation if enabled
        if self.consolidation_mode == ConsolidationMode.ONLINE:
            concepts = self.consolidator.consolidate_online(episode)
            self.stats['concepts_created'] += len(concepts)
            self.stats['consolidations_run'] += 1

        return episode

    def learn(
        self,
        name: str,
        definition: str,
        properties: Dict[str, Any],
        relations: Optional[Dict[str, List[str]]] = None
    ) -> SemanticConcept:
        """Directly learn a semantic concept"""
        concept = SemanticConcept(
            id=f"sem_{time.time()}_{hash(name) % 10000}",
            name=name,
            definition=definition,
            properties=properties,
            relations=relations or {},
            source_episodes=[],
            confidence=0.7,
            abstraction_level=0
        )

        self.semantic.store(concept)
        self.stats['concepts_created'] += 1

        return concept

    def recall(
        self,
        query: Dict[str, Any],
        strategy: RetrievalStrategy = RetrievalStrategy.COMPOSITE,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve from memory"""
        self.stats['retrievals'] += 1
        return self.retriever.retrieve(query, strategy, max_results)

    def consolidate(self, batch_size: int = 100) -> List[SemanticConcept]:
        """Run offline consolidation"""
        concepts = self.consolidator.consolidate_offline(batch_size)
        self.stats['concepts_created'] += len(concepts)
        self.stats['consolidations_run'] += 1
        return concepts

    def focus(self, item_id: str) -> bool:
        """Set focus of attention"""
        return self.working.set_focus(item_id)

    def get_focus(self) -> Optional[MemoryItem]:
        """Get current focus"""
        return self.working.get_focus()

    def get_working_contents(self) -> List[MemoryItem]:
        """Get all working memory contents"""
        return list(self.working.items)

    def get_active_concepts(
        self,
        source_concepts: List[str],
        threshold: float = 0.1
    ) -> Dict[str, float]:
        """Get activated concepts via spreading activation"""
        return self.semantic.spreading_activation(
            source_concepts,
            threshold=threshold
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            **self.stats,
            'working_memory_size': len(self.working.items),
            'episodic_count': len(self.episodic.episodes),
            'semantic_count': len(self.semantic.concepts),
            'pattern_count': len(self.consolidator.pattern_registry)
        }


# Factory functions
def create_memory_system(
    config: Optional[Dict[str, Any]] = None
) -> PersistentMemorySystem:
    """Create configured memory system"""
    config = config or {}

    return PersistentMemorySystem(
        working_capacity=config.get('working_capacity', 7),
        max_episodes=config.get('max_episodes', 10000),
        max_concepts=config.get('max_concepts', 50000),
        consolidation_mode=ConsolidationMode(
            config.get('consolidation_mode', 'online')
        )
    )


def create_standard_memory() -> PersistentMemorySystem:
    """Create standard memory system"""
    return PersistentMemorySystem(
        working_capacity=7,
        max_episodes=10000,
        max_concepts=50000,
        consolidation_mode=ConsolidationMode.ONLINE
    )


def create_large_memory() -> PersistentMemorySystem:
    """Create large-scale memory system"""
    return PersistentMemorySystem(
        working_capacity=9,
        max_episodes=100000,
        max_concepts=500000,
        consolidation_mode=ConsolidationMode.TRIGGERED
    )


def create_fast_memory() -> PersistentMemorySystem:
    """Create fast memory system with smaller capacity"""
    return PersistentMemorySystem(
        working_capacity=5,
        max_episodes=1000,
        max_concepts=5000,
        consolidation_mode=ConsolidationMode.OFFLINE
    )


# Exports
__all__ = [
    # Enums
    'MemoryType',
    'RetrievalStrategy',
    'ConsolidationMode',

    # Data classes
    'MemoryItem',
    'Episode',
    'SemanticConcept',

    # Memory systems
    'WorkingMemory',
    'EpisodicMemory',
    'SemanticMemory',

    # Processing
    'MemoryConsolidator',
    'MemoryRetriever',

    # Main system
    'PersistentMemorySystem',

    # Factory functions
    'create_memory_system',
    'create_standard_memory',
    'create_large_memory',
    'create_fast_memory',
]
