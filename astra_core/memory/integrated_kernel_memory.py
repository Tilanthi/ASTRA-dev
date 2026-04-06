"""
Integrated Kernel Memory System (IKMS)

Connects the kernel-based associative memory with astra_core's advanced capabilities:
- Causal reasoning (causal antecedents, counterfactuals)
- Swarm intelligence (collective importance signals)
- Metacognitive monitoring (uncertainty-weighted retention)
- Temporal context (context-aware compression)

This addresses the "apparently irrelevant" problem by:
1. Preserving causal antecedents even when effects aren't known yet
2. Reinforcing memory based on swarm collective intelligence
3. Using metacognitive uncertainty to preserve uncertain information
4. Context-aware compression that maintains cross-temporal coherence
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Union
from enum import Enum
import numpy as np
import time
from datetime import datetime, timedelta

# Import kernel memory
from .kernel_associative_memory import (
    KernelAssociativeMemory,
    ImportancePredictor,
    MultiScaleTemporalMemory,
    IntegratedPersistentMemory,
    MemoryTemporalScale,  # Renamed to avoid conflict with V4 MCE
    KernelType,
    MemoryItem,
    MemoryState,
    create_persistent_memory,
    # Backwards compatibility
    TemporalScale,  # Alias for MemoryTemporalScale
)

# Try to import astra_core components
try:
    from ..causal.model.scm import StructuralCausalModel
    from ..causal.model.counterfactual import CounterfactualQuery
    CAUSAL_AVAILABLE = True
except ImportError:
    CAUSAL_AVAILABLE = False
    StructuralCausalModel = None
    CounterfactualQuery = None

try:
    from ..intelligence.swarm_orchestrator import SwarmOrchestrator
    from ..intelligence.digital_pheromones import DigitalPheromoneField
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False
    SwarmOrchestrator = None
    DigitalPheromoneField = None

try:
    from ..metacognitive.monitoring.monitor import CognitiveMonitor
    METACOGNITIVE_AVAILABLE = True
except ImportError:
    METACOGNITIVE_AVAILABLE = False
    CognitiveMonitor = None


# =============================================================================
# CAUSAL-AWARE MEMORY EXTENSION
# =============================================================================

class CausalMemoryMode(Enum):
    """Modes for causal-aware memory"""
    PRESERVE_ANTECEDENTS = "preserve_antecedents"  # Keep all potential causes
    COUNTERFACTUAL_READY = "counterfactual_ready"  # Keep for counterfactual queries
    INTERVENTION_TRACKING = "intervention_tracking"  # Track interventions


@dataclass
class CausalMemoryTrace:
    """
    A causal trace linking memory items to causal relationships.

    Enables retrieval of "apparently irrelevant" information that
    becomes relevant when its causal consequences are discovered.
    """
    memory_id: str
    causal_role: str  # 'antecedent', 'consequent', 'mediator', 'collider'
    related_causes: Set[str] = field(default_factory=set)
    related_effects: Set[str] = field(default_factory=set)

    # Causal strength and confidence
    causal_strength: float = 0.5
    confidence: float = 0.5

    # For counterfactual queries
    intervention_results: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'memory_id': self.memory_id,
            'causal_role': self.causal_role,
            'related_causes': list(self.related_causes),
            'related_effects': list(self.related_effects),
            'causal_strength': self.causal_strength,
            'confidence': self.confidence,
            'intervention_results': self.intervention_results,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class CausalAwareMemory:
    """
    Extends kernel memory with causal reasoning capabilities.

    Key insight: Information that is apparently irrelevant NOW may
    become critical LATER when its causal consequences are discovered.

    This preserves antecedents even when we don't yet know their effects.
    """

    def __init__(self,
                 base_memory: IntegratedPersistentMemory,
                 mode: CausalMemoryMode = CausalMemoryMode.PRESERVE_ANTECEDENTS):
        """
        Args:
            base_memory: Base kernel memory system
            mode: Causal memory mode
        """
        self.base_memory = base_memory
        self.mode = mode

        # Causal traces
        self.causal_traces: Dict[str, CausalMemoryTrace] = {}

        # Causal graph for importance propagation
        self.causal_graph: Dict[str, Set[str]] = {}  # node -> children

        # Counterfactual cache
        self.counterfactual_cache: Dict[str, Any] = {}

    def remember_with_causality(self,
                               content: str,
                               embedding: np.ndarray,
                               causal_context: Optional[Dict[str, Any]] = None,
                               **kwargs) -> str:
        """
        Remember with causal context.

        Preserves information that might be causally relevant even if
        it doesn't seem immediately important.
        """
        causal_context = causal_context or {}

        # Store in base memory
        memory_id = self.base_memory.remember(
            content=content,
            embedding=embedding,
            context=causal_context,
            **kwargs
        )

        # Create causal trace
        causal_role = causal_context.get('causal_role', 'neutral')
        trace = CausalMemoryTrace(
            memory_id=memory_id,
            causal_role=causal_role,
            causal_strength=causal_context.get('causal_strength', 0.5),
            confidence=causal_context.get('confidence', 0.5)
        )

        # Link to related causes/effects
        if 'causes' in causal_context:
            for effect_id in causal_context['causes']:
                trace.related_effects.add(effect_id)

        if 'caused_by' in causal_context:
            for cause_id in causal_context['caused_by']:
                trace.related_causes.add(cause_id)

        self.causal_traces[memory_id] = trace

        # Update causal graph
        self._update_causal_graph(memory_id, causal_context)

        return memory_id

    def retrieve_antecedents(self,
                           effect_id: str,
                           max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve causal antecedents (causes) for an effect.

        This retrieves "apparently irrelevant" information that became
        relevant when the effect was discovered.
        """
        antecedents = []
        visited = set()

        def trace_causes(current_id: str, depth: int) -> None:
            if depth > max_depth or current_id in visited:
                return

            visited.add(current_id)

            if current_id in self.causal_traces:
                trace = self.causal_traces[current_id]

                for cause_id in trace.related_causes:
                    if cause_id not in visited:
                        # Retrieve from memory
                        results = self.base_memory.recall(
                            query=np.zeros(self.base_memory.embedding_dim),  # Placeholder
                            top_k=1
                        )

                        # Check if this cause is in results
                        for result in results:
                            if cause_id in result.get('id', ''):
                                antecedents.append({
                                    'id': cause_id,
                                    'depth': depth,
                                    'causal_strength': trace.causal_strength,
                                    'role': 'cause',
                                })

                        # Recurse
                        trace_causes(cause_id, depth + 1)

        trace_causes(effect_id, 0)

        return antecedents

    def prepare_counterfactual(self,
                              memory_id: str,
                              intervention: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare memory for counterfactual query.

        Ensures all relevant antecedents are preserved.
        """
        if memory_id not in self.causal_traces:
            return {'error': 'Memory ID not found'}

        trace = self.causal_traces[memory_id]

        # Boost importance of all antecedents
        for cause_id in trace.related_causes:
            if cause_id in self.causal_traces:
                cause_trace = self.causal_traces[cause_id]
                # Boost importance for counterfactual readiness
                cause_trace.causal_strength *= 1.5

        # Cache intervention
        cache_key = f"{memory_id}_{hash(str(intervention))}"
        self.counterfactual_cache[cache_key] = {
            'memory_id': memory_id,
            'intervention': intervention,
            'timestamp': time.time(),
            'antecedents': list(trace.related_causes),
        }

        return {
            'status': 'prepared',
            'cache_key': cache_key,
            'antecedents_count': len(trace.related_causes),
        }

    def reinforce_from_discovery(self,
                                newly_discovered_cause: str,
                                effect_id: str,
                                strength: float = 0.8) -> None:
        """
        Reinforce memory when a new causal relationship is discovered.

        This solves the "apparently irrelevant" problem by boosting
        the importance of information that was just a detail but
        turned out to be causally significant.
        """
        # Create or update trace
        if newly_discovered_cause not in self.causal_traces:
            self.causal_traces[newly_discovered_cause] = CausalMemoryTrace(
                memory_id=newly_discovered_cause,
                causal_role='antecedent',
                causal_strength=strength,
                confidence=0.8
            )

        trace = self.causal_traces[newly_discovered_cause]
        trace.related_effects.add(effect_id)
        trace.causal_strength = max(trace.causal_strength, strength)
        trace.updated_at = time.time()

        # Update base memory importance
        self.base_memory.importance_predictor.update_hindsight(
            newly_discovered_cause,
            actual_importance=strength
        )

    def _update_causal_graph(self,
                             memory_id: str,
                             causal_context: Dict[str, Any]) -> None:
        """Update internal causal graph"""
        if memory_id not in self.causal_graph:
            self.causal_graph[memory_id] = set()

        if 'causes' in causal_context:
            for effect_id in causal_context['causes']:
                self.causal_graph[memory_id].add(effect_id)

                if effect_id not in self.causal_graph:
                    self.causal_graph[effect_id] = set()

    def get_causal_stats(self) -> Dict[str, Any]:
        """Get causal memory statistics"""
        return {
            'traces_count': len(self.causal_traces),
            'graph_nodes': len(self.causal_graph),
            'graph_edges': sum(len(children) for children in self.causal_graph.values()),
            'counterfactual_cache_size': len(self.counterfactual_cache),
        }


# =============================================================================
# SWARM-INTEGRATED MEMORY
# =============================================================================

class SwarmMemoryIntegration:
    """
    Integrates kernel memory with swarm intelligence.

    Collective intelligence reinforces importance - if ANY agent
    finds something important, it's likely to be important to others.
    """

    def __init__(self,
                 base_memory: IntegratedPersistentMemory,
                 swarm_orchestrator: Optional[Any] = None):
        """
        Args:
            base_memory: Base kernel memory system
            swarm_orchestrator: Optional swarm orchestrator
        """
        self.base_memory = base_memory
        self.swarm_orchestrator = swarm_orchestrator

        # Collective importance signals
        self.collective_importance: Dict[str, List[float]] = {}

        # Agent-specific importance weights
        self.agent_weights: Dict[str, float] = {}

        # Cross-agent associations
        self.cross_agent_associations: Dict[str, Set[str]] = {}

    def report_importance(self,
                         agent_id: str,
                         memory_id: str,
                         importance: float,
                         context: Optional[Dict[str, Any]] = None) -> None:
        """
        Report importance signal from a swarm agent.

        When any agent finds something important, we boost its retention.
        """
        if memory_id not in self.collective_importance:
            self.collective_importance[memory_id] = []

        # Apply agent weight
        agent_weight = self.agent_weights.get(agent_id, 1.0)
        weighted_importance = importance * agent_weight

        self.collective_importance[memory_id].append(weighted_importance)

        # Keep only recent signals
        if len(self.collective_importance[memory_id]) > 20:
            self.collective_importance[memory_id] = \
                self.collective_importance[memory_id][-20:]

        # Add swarm signal to base memory
        self.base_memory.add_swarm_signal(memory_id, weighted_importance)

        # Track cross-agent associations
        if context and 'related_memories' in context:
            if memory_id not in self.cross_agent_associations:
                self.cross_agent_associations[memory_id] = set()

            for related_id in context['related_memories']:
                self.cross_agent_associations[memory_id].add(related_id)

    def get_collective_importance(self, memory_id: str) -> Tuple[float, int]:
        """
        Get collective importance for a memory.

        Returns:
            (average_importance, num_signals)
        """
        if memory_id not in self.collective_importance:
            return 0.0, 0

        signals = self.collective_importance[memory_id]

        # Use both mean and max
        avg_importance = np.mean(signals)
        max_importance = np.max(signals)

        # Max matters more (if ANY agent finds it important, it is)
        combined_importance = 0.7 * max_importance + 0.3 * avg_importance

        return combined_importance, len(signals)

    def propagate_importance(self, source_id: str) -> None:
        """
        Propagate importance to associated memories.

        If something becomes important, its associations might also
        become important.
        """
        if source_id not in self.cross_agent_associations:
            return

        source_importance, _ = self.get_collective_importance(source_id)

        # Boost importance of associations
        for associated_id in self.cross_agent_associations[source_id]:
            if associated_id in self.collective_importance:
                # Decay propagation
                propagated = source_importance * 0.5
                self.collective_importance[associated_id].append(propagated)

    def set_agent_weight(self, agent_id: str, weight: float) -> None:
        """
        Set weight for an agent's importance signals.

        Some agents are more reliable than others.
        """
        self.agent_weights[agent_id] = np.clip(weight, 0.0, 2.0)

    def get_swarm_stats(self) -> Dict[str, Any]:
        """Get swarm integration statistics"""
        return {
            'memories_with_signals': len(self.collective_importance),
            'total_signals': sum(len(signals) for signals in self.collective_importance.values()),
            'agents_tracked': len(self.agent_weights),
            'cross_agent_associations': sum(
                len(associations) for associations in self.cross_agent_associations.values()
            ),
        }


# =============================================================================
# METACOGNITIVE MEMORY
# =============================================================================

class MetacognitiveMemory:
    """
    Extends kernel memory with metacognitive monitoring.

    Uses uncertainty and confidence to modulate retention:
    - When uncertain, preserve more (better safe than sorry)
    - When confident, can compress more aggressively
    """

    def __init__(self,
                 base_memory: IntegratedPersistentMemory,
                 cognitive_monitor: Optional[Any] = None):
        """
        Args:
            base_memory: Base kernel memory system
            cognitive_monitor: Optional cognitive monitor
        """
        self.base_memory = base_memory
        self.cognitive_monitor = cognitive_monitor

        # Confidence tracking
        self.confidence_history: Dict[str, List[float]] = {}

        # Uncertainty-based importance adjustments
        self.uncertainty_boosts: Dict[str, float] = {}

        # Metacognitive triggers
        self.compression_triggers = {
            'low_confidence_threshold': 0.3,
            'high_confidence_threshold': 0.8,
        }

    def assess_memory_confidence(self,
                                 memory_id: str,
                                 context: Optional[Dict[str, Any]] = None) -> float:
        """
        Assess confidence in a memory.

        Lower confidence → higher importance (preserve when unsure)
        """
        context = context or {}

        # Base confidence
        confidence = 0.5

        # Context factors
        if 'source_reliability' in context:
            confidence *= context['source_reliability']

        if 'verification_count' in context:
            confidence += min(0.3, context['verification_count'] * 0.1)

        if 'contradictions' in context and context['contradictions']:
            confidence -= 0.2

        # Track history
        if memory_id not in self.confidence_history:
            self.confidence_history[memory_id] = []

        self.confidence_history[memory_id].append(confidence)

        # Keep limited history
        if len(self.confidence_history[memory_id]) > 10:
            self.confidence_history[memory_id].pop(0)

        return np.clip(confidence, 0.0, 1.0)

    def uncertainty_weighted_importance(self,
                                       memory_id: str,
                                       base_importance: float,
                                       uncertainty: float) -> float:
        """
        Adjust importance based on uncertainty.

        Higher uncertainty → higher importance (preserve when unsure)
        """
        # Uncertainty boost
        boost = uncertainty * 0.5

        # Adjust importance
        adjusted_importance = base_importance + boost

        # Store boost for reference
        self.uncertainty_boosts[memory_id] = boost

        return min(adjusted_importance, 1.0)

    def should_compress_aggressively(self, avg_confidence: float) -> bool:
        """
        Determine if we can compress aggressively.

        High confidence → can compress more
        Low confidence → preserve more
        """
        return avg_confidence > self.compression_triggers['high_confidence_threshold']

    def should_preserve_extra(self, avg_confidence: float) -> bool:
        """
        Determine if we should preserve extra information.

        Low confidence → preserve more
        """
        return avg_confidence < self.compression_triggers['low_confidence_threshold']

    def get_metacognitive_stats(self) -> Dict[str, Any]:
        """Get metacognitive statistics"""
        if not self.confidence_history:
            return {'confidence_tracked': 0}

        all_confidences = []
        for confidences in self.confidence_history.values():
            all_confidences.extend(confidences)

        return {
            'confidence_tracked': len(self.confidence_history),
            'avg_confidence': np.mean(all_confidences) if all_confidences else 0.0,
            'min_confidence': np.min(all_confidences) if all_confidences else 0.0,
            'max_confidence': np.max(all_confidences) if all_confidences else 0.0,
            'uncertainty_boosts': len(self.uncertainty_boosts),
            'avg_uncertainty_boost': np.mean(list(self.uncertainty_boosts.values()))
            if self.uncertainty_boosts else 0.0,
        }


# =============================================================================
# FULLY INTEGRATED MEMORY SYSTEM
# =============================================================================

class FullyIntegratedMemorySystem:
    """
    Complete integration of kernel memory with all astra_core capabilities.

    Combines:
    - Kernel-based associative memory
    - Causal-aware retention
    - Swarm intelligence reinforcement
    - Metacognitive monitoring
    - Multi-scale temporal memory

    This provides a robust solution to the "apparently irrelevant" problem
    by using multiple signals to determine what to preserve.
    """

    def __init__(self,
                 embedding_dim: int = 128,
                 value_dim: int = 128,
                 kernel_type: KernelType = KernelType.HOMOMORPHIC):
        """
        Args:
            embedding_dim: Embedding dimension
            value_dim: Value dimension
            kernel_type: Kernel function type
        """
        # Base kernel memory
        self.base_memory = create_persistent_memory(
            embedding_dim=embedding_dim,
            value_dim=value_dim,
            kernel_type=kernel_type
        )

        # Extensions
        self.causal_memory = CausalAwareMemory(self.base_memory)
        self.swarm_memory = SwarmMemoryIntegration(self.base_memory)
        self.metacognitive_memory = MetacognitiveMemory(self.base_memory)

        # Statistics
        self.operations_count = 0
        self.last_compression = time.time()

    def remember(self,
                content: str,
                embedding: np.ndarray,
                context: Optional[Dict[str, Any]] = None,
                causal_context: Optional[Dict[str, Any]] = None,
                uncertainty: Optional[float] = None,
                temporal_scale: MemoryTemporalScale = MemoryTemporalScale.IMMEDIATE) -> str:
        """
        Comprehensive memory storage with all integrations.

        This is the main interface for storing information.
        """
        self.operations_count += 1
        context = context or {}
        causal_context = causal_context or {}

        # Assess metacognitive confidence
        memory_id = f"mem_{time.time()}_{hash(content) % 1000000}"
        confidence = self.metacognitive_memory.assess_memory_confidence(
            memory_id, context
        )

        # Infer uncertainty if not provided
        if uncertainty is None:
            uncertainty = 1.0 - confidence

        # Update context with metacognitive info
        context['confidence'] = confidence
        context['uncertainty'] = uncertainty

        # Store with causal awareness
        if causal_context:
            memory_id = self.causal_memory.remember_with_causality(
                content=content,
                embedding=embedding,
                causal_context=causal_context,
                uncertainty=uncertainty,
                temporal_scale=temporal_scale
            )
        else:
            memory_id = self.base_memory.remember(
                content=content,
                embedding=embedding,
                context=context,
                uncertainty=uncertainty,
                temporal_scale=temporal_scale
            )

        return memory_id

    def recall(self,
              query: np.ndarray,
              top_k: int = 5,
              scales: Optional[List[MemoryTemporalScale]] = None) -> List[Dict[str, Any]]:
        """
        Comprehensive retrieval with all contexts.
        """
        results = self.base_memory.recall(query, top_k, scales)

        # Augment with causal context
        for result in results:
            memory_id = result.get('id', '')
            if memory_id in self.causal_memory.causal_traces:
                trace = self.causal_memory.causal_traces[memory_id]
                result['causal_role'] = trace.causal_role
                result['causal_strength'] = trace.causal_strength

            # Add swarm importance
            collective_importance, num_signals = \
                self.swarm_memory.get_collective_importance(memory_id)
            result['collective_importance'] = collective_importance
            result['num_signals'] = num_signals

        return results

    def report_swarm_importance(self,
                               agent_id: str,
                               memory_id: str,
                               importance: float,
                               context: Optional[Dict[str, Any]] = None) -> None:
        """Report importance from swarm agent"""
        self.swarm_memory.report_importance(agent_id, memory_id, importance, context)

    def reinforce_causal_discovery(self,
                                  newly_discovered_cause: str,
                                  effect_id: str,
                                  strength: float = 0.8) -> None:
        """Reinforce when causal relationship is discovered"""
        self.causal_memory.reinforce_from_discovery(
            newly_discovered_cause, effect_id, strength
        )

    def periodic_maintenance(self) -> Dict[str, Any]:
        """
        Perform periodic maintenance tasks.

        Call this periodically (e.g., every minute) to:
        - Cascade and compress temporal memory
        - Propagate swarm importance
        - Adjust metacognitive thresholds
        """
        current_time = time.time()

        # Cascade compression
        self.base_memory.cascade_and_compress()
        self.last_compression = current_time

        # Propagate importance from high-confidence memories
        for memory_id in list(self.swarm_memory.collective_importance.keys())[:10]:
            self.swarm_memory.propagate_importance(memory_id)


# Memory optimization utilities
import functools

@functools.lru_cache(maxsize=512)
def _memory_signature(content_hash):
    """Compute cached memory signatures for retrieval."""
    return content_hash

def vectorized_similarity(query, memories):
    """Vectorized similarity computation."""
    import numpy as np
    query_vec = np.array(query)
    memory_matrix = np.array(memories)
    similarities = np.dot(memory_matrix, query_vec)
    return similarities


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle

