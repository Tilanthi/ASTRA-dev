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
Lifelong Continuous Learning Module for V91
==========================================

Implements autonomous self-improvement through:
- Continual knowledge acquisition
- Catastrophic forgetting prevention
- Curriculum learning
- Self-directed exploration
- Meta-learning of learning strategies
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import time
from collections import deque
import json


class LearningStrategy(Enum):
    """Different learning strategies the system can employ"""
    SUPERVISED = "supervised"
    REINFORCEMENT = "reinforcement"
    UNSUPERVISED = "unsupervised"
    SELF_SUPERVISED = "self_supervised"
    CURIOSITY_DRIVEN = "curiosity_driven"
    ACTIVE_LEARNING = "active_learning"


class KnowledgeType(Enum):
    """Types of knowledge the system can acquire"""
    DECLARATIVE = "declarative"  # Facts, concepts
    PROCEDURAL = "procedural"    # Skills, procedures
    EPISODIC = "episodic"        # Experiences, events
    METACOGNITIVE = "metacognitive"  # Learning about learning
    CAUSAL = "causal"            # Causal relationships


@dataclass
class KnowledgeItem:
    """A single piece of knowledge with metadata"""
    content: Any
    knowledge_type: KnowledgeType
    domain: str
    confidence: float = 0.5
    importance: float = 0.5
    creation_time: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    related_items: Set[str] = field(default_factory=set)
    source: Optional[str] = None
    verification_status: str = "unverified"


@dataclass
class LearningTask:
    """A learning task for the system"""
    task_id: str
    description: str
    domain: str
    difficulty: float
    prerequisites: List[str] = field(default_factory=list)
    learning_strategy: LearningStrategy = LearningStrategy.SUPERVISED
    expected_outcome: str = ""
    priority: float = 0.5


class ContinualLearner:
    """
    Implements lifelong learning with automatic curriculum generation
    and catastrophic forgetting prevention.
    """

    def __init__(self, knowledge_capacity: int = 100000):
        self.knowledge_capacity = knowledge_capacity
        self.knowledge_base = {}
        self.knowledge_graph = {}  # relationships between knowledge items
        self.learning_history = deque(maxlen=10000)
        self.forgetting_rates = {}
        self.replay_buffer = []
        self.learning_strategies = {}
        self.curriculum = []
        self.performance_metrics = {}
        self.meta_learning_state = {
            'best_strategies': {},
            'difficulty_progression': {},
            'transfer_performance': {}
        }

        # Initialize learning components
        self._init_memory_systems()
        self._init_curriculum_generator()
        self._init_forgetting_prevention()

    def _init_memory_systems(self):
        """Initialize specialized memory systems"""
        self.short_term_memory = deque(maxlen=100)
        self.working_memory = set()
        self.long_term_memory = {}
        self.episodic_memory = deque(maxlen=10000)
        self.procedural_memory = {}

    def _init_curriculum_generator(self):
        """Initialize automatic curriculum generation"""
        self.curriculum_generator = {
            'difficulty_estimator': self._estimate_difficulty,
            'prerequisite_analyzer': self._analyze_prerequisites,
            'sequencing_algorithm': self._generate_sequence
        }

    def _init_forgetting_prevention(self):
        """Initialize mechanisms to prevent catastrophic forgetting"""
        self.replay_scheduler = {
            'frequency': 0.1,  # replay 10% of old knowledge
            'selection_method': 'importance_weighted',
            'consolidation_threshold': 0.8
        }

    def learn(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn from a new experience and update knowledge base.

        Args:
            experience: Dictionary containing the learning experience

        Returns:
            Dictionary with learning outcomes
        """
        start_time = time.time()

        # Extract knowledge from experience
        new_knowledge = self._extract_knowledge(experience)

        # Update knowledge base
        updates = self._update_knowledge_base(new_knowledge)

        # Prevent forgetting
        self._schedule_replay()

        # Update learning strategies
        self._update_learning_strategies(experience, updates)

        # Record learning
        self.learning_history.append({
            'timestamp': start_time,
            'experience_id': experience.get('id', 'unknown'),
            'knowledge_gained': len(new_knowledge),
            'strategy_used': experience.get('strategy', 'default'),
            'success': updates.get('success', False)
        })

        # Generate new curriculum items if needed
        self._update_curriculum()

        return {
            'knowledge_added': len(updates['added']),
            'knowledge_updated': len(updates['updated']),
            'confidence_improvement': updates.get('confidence_delta', 0),
            'learning_time': time.time() - start_time
        }

    def _extract_knowledge(self, experience: Dict[str, Any]) -> List[KnowledgeItem]:
        """Extract knowledge items from an experience"""
        knowledge_items = []

        # Extract declarative knowledge
        if 'facts' in experience:
            for fact in experience['facts']:
                item = KnowledgeItem(
                    content=fact,
                    knowledge_type=KnowledgeType.DECLARATIVE,
                    domain=experience.get('domain', 'general'),
                    source=experience.get('source', 'experience')
                )
                knowledge_items.append(item)

        # Extract procedural knowledge
        if 'procedures' in experience:
            for procedure in experience['procedures']:
                item = KnowledgeItem(
                    content=procedure,
                    knowledge_type=KnowledgeType.PROCEDURAL,
                    domain=experience.get('domain', 'general'),
                    source=experience.get('source', 'experience')
                )
                knowledge_items.append(item)

        # Extract causal knowledge
        if 'causal_relations' in experience:
            for relation in experience['causal_relations']:
                item = KnowledgeItem(
                    content=relation,
                    knowledge_type=KnowledgeType.CAUSAL,
                    domain=experience.get('domain', 'general'),
                    source=experience.get('source', 'experience')
                )
                knowledge_items.append(item)

        # Extract episodic memory
        episodic_item = KnowledgeItem(
            content=experience,
            knowledge_type=KnowledgeType.EPISODIC,
            domain=experience.get('domain', 'general'),
            source='direct_experience'
        )
        knowledge_items.append(episodic_item)

        return knowledge_items

    def _update_knowledge_base(self, new_knowledge: List[KnowledgeItem]) -> Dict[str, Any]:
        """Update knowledge base with new knowledge"""
        updates = {'added': [], 'updated': [], 'confidence_delta': 0}

        for item in new_knowledge:
            item_id = self._generate_knowledge_id(item)

            if item_id in self.knowledge_base:
                # Update existing knowledge
                old_item = self.knowledge_base[item_id]
                old_confidence = old_item.confidence

                # Merge or update based on consistency
                if self._is_consistent(old_item, item):
                    # Increase confidence for consistent information
                    item.confidence = min(1.0, old_confidence * 1.1)
                    updates['updated'].append(item_id)
                else:
                    # Handle inconsistency
                    item.confidence = (old_confidence + item.confidence) / 2
                    item.verification_status = "conflict"

                self.knowledge_base[item_id] = item
                updates['confidence_delta'] += item.confidence - old_confidence
            else:
                # Add new knowledge
                self.knowledge_base[item_id] = item
                updates['added'].append(item_id)

            # Update knowledge graph
            self._update_knowledge_graph(item_id, item)

            # Add to appropriate memory system
            self._store_in_memory(item)

        return updates

    def _generate_knowledge_id(self, item: KnowledgeItem) -> str:
        """Generate unique ID for knowledge item"""
        content_str = str(item.content)[:100]  # Limit length
        import hashlib
        return hashlib.md5(content_str.encode()).hexdigest()

    def _is_consistent(self, old_item: KnowledgeItem, new_item: KnowledgeItem) -> bool:
        """Check if two knowledge items are consistent"""
        # Simple consistency check - can be made more sophisticated
        if old_item.knowledge_type != new_item.knowledge_type:
            return True  # Different types are not inconsistent

        # For same type, check content similarity
        if isinstance(old_item.content, str) and isinstance(new_item.content, str):
            similarity = self._text_similarity(old_item.content, new_item.content)
            return similarity > 0.7

        return True

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0

    def _update_knowledge_graph(self, item_id: str, item: KnowledgeItem):
        """Update knowledge graph with new relationships"""
        if item_id not in self.knowledge_graph:
            self.knowledge_graph[item_id] = {
                'connections': {},
                'domains': set(),
                'types': set()
            }

        # Update domains and types
        self.knowledge_graph[item_id]['domains'].add(item.domain)
        self.knowledge_graph[item_id]['types'].add(item.knowledge_type.value)

        # Find related items
        related_items = self._find_related_items(item)
        for related_id, strength in related_items:
            self.knowledge_graph[item_id]['connections'][related_id] = strength

    def _find_related_items(self, item: KnowledgeItem) -> List[Tuple[str, float]]:
        """Find knowledge items related to the given item"""
        related = []

        for existing_id, existing_item in self.knowledge_base.items():
            if existing_id == self._generate_knowledge_id(item):
                continue

            # Calculate relatedness
            if item.domain == existing_item.domain:
                similarity = 0.3
            else:
                similarity = 0.1

            if item.knowledge_type == existing_item.knowledge_type:
                similarity += 0.2

            # Check content similarity
            if hasattr(item.content, 'keys') and hasattr(existing_item.content, 'keys'):
                common_keys = set(item.content.keys()) & set(existing_item.content.keys())
                similarity += len(common_keys) * 0.1

            if similarity > 0.5:
                related.append((existing_id, similarity))

        return related

    def _store_in_memory(self, item: KnowledgeItem):
        """Store knowledge item in appropriate memory system"""
        if item.knowledge_type == KnowledgeType.EPISODIC:
            self.episodic_memory.append(item)
        elif item.knowledge_type == KnowledgeType.PROCEDURAL:
            self.procedural_memory[item.content] = item
        else:
            self.long_term_memory[self._generate_knowledge_id(item)] = item

    def _schedule_replay(self):
        """Schedule replay of important old knowledge to prevent forgetting"""
        if len(self.knowledge_base) > self.knowledge_capacity * 0.8:
            # Select knowledge for replay
            candidates = self._select_replay_candidates()
            self.replay_buffer.extend(candidates)

    def _select_replay_candidates(self) -> List[str]:
        """Select knowledge items for replay"""
        candidates = []

        for item_id, item in self.knowledge_base.items():
            # Select based on importance and time since last access
            importance = item.importance
            time_factor = time.time() - item.last_accessed
            score = importance * (time_factor / (24 * 3600))  # Days since last access

            if score > 1.0:
                candidates.append(item_id)

        return candidates[:10]  # Limit number of candidates

    def _update_learning_strategies(self, experience: Dict[str, Any], updates: Dict[str, Any]):
        """Update meta-learning about learning strategies"""
        strategy = experience.get('strategy', 'default')
        success = updates.get('success', False)
        domain = experience.get('domain', 'general')

        # Update strategy performance
        if domain not in self.meta_learning_state['best_strategies']:
            self.meta_learning_state['best_strategies'][domain] = {}

        if strategy not in self.meta_learning_state['best_strategies'][domain]:
            self.meta_learning_state['best_strategies'][domain][strategy] = {
                'successes': 0,
                'attempts': 0
            }

        self.meta_learning_state['best_strategies'][domain][strategy]['attempts'] += 1
        if success:
            self.meta_learning_state['best_strategies'][domain][strategy]['successes'] += 1

    def _estimate_difficulty(self, task: LearningTask) -> float:
        """Estimate difficulty of a learning task"""
        # Base difficulty from task specification
        difficulty = task.difficulty

        # Adjust based on prerequisites
        for prereq in task.prerequisites:
            if not self._has_knowledge(prereq):
                difficulty += 0.2

        # Adjust based on domain familiarity
        domain_knowledge = self._count_domain_knowledge(task.domain)
        if domain_knowledge < 10:
            difficulty += 0.3

        return min(1.0, difficulty)

    def _analyze_prerequisites(self, task: LearningTask) -> List[str]:
        """Analyze what prerequisites are needed for a task"""
        # Use knowledge graph to infer prerequisites
        prerequisites = []

        # Look for related knowledge in the same domain
        for item_id, item_info in self.knowledge_graph.items():
            if task.domain in item_info['domains']:
                # Add as potential prerequisite
                prerequisites.append(item_id)

        return prerequisites[:5]  # Limit number of prerequisites

    def _generate_sequence(self, tasks: List[LearningTask]) -> List[LearningTask]:
        """Generate optimal learning sequence for tasks"""
        # Sort by difficulty and dependencies
        sequenced = []
        remaining = tasks.copy()

        while remaining:
            # Find tasks with all prerequisites met
            ready = []
            for task in remaining:
                if all(self._has_knowledge(prereq) for prereq in task.prerequisites):
                    ready.append(task)

            if not ready:
                # If no ready tasks, pick the one with fewest missing prerequisites
                ready = [min(remaining, key=lambda t: len(t.prerequisites))]

            # Select easiest ready task
            next_task = min(ready, key=lambda t: self._estimate_difficulty(t))
            sequenced.append(next_task)
            remaining.remove(next_task)

        return sequenced

    def _has_knowledge(self, knowledge_id: str) -> bool:
        """Check if system has specific knowledge"""
        return knowledge_id in self.knowledge_base

    def _count_domain_knowledge(self, domain: str) -> int:
        """Count knowledge items in a domain"""
        count = 0
        for item in self.knowledge_base.values():
            if item.domain == domain:
                count += 1
        return count

    def _update_curriculum(self):
        """Update learning curriculum based on current state"""
        # Identify knowledge gaps
        gaps = self._identify_knowledge_gaps()

        # Generate tasks to fill gaps
        for gap in gaps:
            task = LearningTask(
                task_id=f"gap_{gap}_{time.time()}",
                description=f"Learn about {gap}",
                domain=gap,
                difficulty=0.5,
                priority=0.7
            )
            self.curriculum.append(task)

        # Prioritize curriculum
        self.curriculum.sort(key=lambda t: t.priority, reverse=True)

    def _identify_knowledge_gaps(self) -> List[str]:
        """Identify areas where knowledge is lacking"""
        gaps = []

        # Find domains with low knowledge
        domain_counts = {}
        for item in self.knowledge_base.values():
            domain_counts[item.domain] = domain_counts.get(item.domain, 0) + 1

        # Domains with less than 5 items are considered gaps
        for domain, count in domain_counts.items():
            if count < 5:
                gaps.append(domain)

        return gaps

    def select_next_learning_task(self) -> Optional[LearningTask]:
        """Select the next learning task from curriculum"""
        if not self.curriculum:
            return None

        # Select highest priority ready task
        ready_tasks = [
            task for task in self.curriculum
            if all(self._has_knowledge(prereq) for prereq in task.prerequisites)
        ]

        if not ready_tasks:
            return None

        return max(ready_tasks, key=lambda t: t.priority)

    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics"""
        return {
            'total_knowledge': len(self.knowledge_base),
            'knowledge_by_type': {
                ktype.value: sum(1 for item in self.knowledge_base.values()
                               if item.knowledge_type == ktype)
                for ktype in KnowledgeType
            },
            'knowledge_by_domain': {
                domain: sum(1 for item in self.knowledge_base.values()
                           if item.domain == domain)
                for domain in set(item.domain for item in self.knowledge_base.values())
            },
            'learning_efficiency': {
                'items_per_day': len(self.learning_history) / max(1, (time.time() - self.learning_history[0]['timestamp']) / 86400) if self.learning_history else 0,
                'average_confidence': np.mean([item.confidence for item in self.knowledge_base.values()]) if self.knowledge_base else 0,
                'forgetting_rate': self._calculate_forgetting_rate()
            },
            'curriculum_status': {
                'pending_tasks': len(self.curriculum),
                'next_task': self.select_next_learning_task().description if self.select_next_learning_task() else None
            },
            'meta_learning': self.meta_learning_state
        }

    def _calculate_forgetting_rate(self) -> float:
        """Calculate rate of knowledge forgetting"""
        if len(self.learning_history) < 100:
            return 0

        # Calculate how often previously learned knowledge is accessed
        recent_accesses = sum(1 for item in self.knowledge_base.values()
                            if (time.time() - item.last_accessed) < 7 * 24 * 3600)  # Last week

        total_items = len(self.knowledge_base)
        return 1 - (recent_accesses / total_items) if total_items > 0 else 0