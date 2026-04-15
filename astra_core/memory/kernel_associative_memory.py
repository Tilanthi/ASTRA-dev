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
Kernel-Based Associative Memory (KAM) with Corrected Mathematics

Theoretical Corrections:
1. Linear attention uses OUTER PRODUCTS φ(k)v ∈ R^(d×d_v), not inner products
2. Complexity is O(N×d²) total, not O(N×d) - improvement is in constant memory, not time
3. Compression consequences: "apparently irrelevant" information is permanently lost

This implementation addresses these issues through:
- Hybrid compressed/uncompressed storage
- Context-aware relevance prediction
- Causal reinforcement of apparently irrelevant details
- Multi-scale temporal retention
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from collections import deque
import time
import hashlib
import json
from datetime import datetime, timedelta


# =============================================================================
# KERNEL FUNCTIONS
# =============================================================================

class KernelType(Enum):
    """Types of kernel functions for associative memory"""
    HOMOMORPHIC = "homomorphic"  # ELU + 1
    EXPONENTIAL = "exponential"  # exp
    RBF = "rbf"  # Radial basis function
    POLYNOMIAL = "polynomial"  # (x·y + c)^d
    SIGMOID = "sigmoid"  # tanh


def phi_homomorphic(x: np.ndarray) -> np.ndarray:
    """
    Homomorphic kernel feature map: ELU(x) + 1
    Properties: non-negative, preserves zero, roughly linear for positive

    Theoretical Note: PDF suggests this is "linear" but:
    - φ(k)v is an OUTER PRODUCT: (d×1) × (1×d_v) = d×d_v matrix
    - Each token requires O(d²) multiplications for the outer product
    - N tokens → O(N×d²) total, NOT O(N×d) as PDF claims
    - The improvement is O(1) memory vs O(N) for full attention
    """
    return np.maximum(x, 0) + 1.0


def phi_exponential(x: np.ndarray) -> np.ndarray:
    """
    Exponential kernel feature map: exp(x)
    Properties: highly non-linear, emphasizes large values
    """
    # Clip for numerical stability
    x_clipped = np.clip(x, -10, 10)
    return np.exp(x_clipped)


def phi_rbf(x: np.ndarray, centers: Optional[np.ndarray] = None) -> np.ndarray:
    """
    RBF kernel feature map using random Fourier features
    Approximates exp(-||x-y||²) in high dimensions
    """
    d = x.shape[-1]
    if centers is None:
        # Use random features (should be consistent across calls)
        np.random.seed(42)
        centers = np.random.randn(d * 2, d)

    # Compute RBF features: exp(-||x - c||²)
    features = []
    for center in centers:
        diff = x - center
        features.append(np.exp(-np.sum(diff ** 2, axis=-1, keepdims=True)))

    return np.concatenate(features, axis=-1)


# Kernel registry
KERNEL_FUNCTIONS: Dict[KernelType, Callable] = {
    KernelType.HOMOMORPHIC: phi_homomorphic,
    KernelType.EXPONENTIAL: phi_exponential,
    KernelType.RBF: lambda x: phi_rbf(x),
    KernelType.POLYNOMIAL: lambda x: np.power(x + 1.0, 2),
    KernelType.SIGMOID: lambda x: np.tanh(x),
}


# =============================================================================
# IMPORTANCE PREDICTION (SOLVING "APPARENTLY IRRELEVANT" PROBLEM)
# =============================================================================

class ImportancePredictor:
    """
    Predicts future importance of current information.

    Key insight: "Apparently irrelevant" information that becomes
    relevant later must be preserved based on PREDICTED importance,
    not just current relevance.

    Failure modes addressed:
    - Information that seems irrelevant now but causes effects later (causal antecedents)
    - Patterns that only emerge with longer temporal windows
    - Details that become relevant in different contexts
    """

    def __init__(self,
                 causal_weight: float = 0.3,
                 temporal_weight: float = 0.2,
                 swarm_weight: float = 0.2,
                 uncertainty_weight: float = 0.3):
        """
        Args:
            causal_weight: Weight for causal connection importance
            temporal_weight: Weight for temporal pattern importance
            swarm_weight: Weight for collective importance signals
            uncertainty_weight: Weight for metacognitive uncertainty
        """
        self.causal_weight = causal_weight
        self.temporal_weight = temporal_weight
        self.swarm_weight = swarm_weight
        self.uncertainty_weight = uncertainty_weight

        # Track what becomes important later (for learning)
        self.hindsight_importance: Dict[str, float] = {}

        # Causal graph of what influences what
        self.causal_graph: Dict[str, Set[str]] = {}

        # Temporal patterns
        self.temporal_patterns: Dict[str, List[float]] = {}

        # Collective importance from swarm
        self.collective_importance: Dict[str, float] = {}

    def predict_importance(self,
                          content: str,
                          embedding: np.ndarray,
                          context: Dict[str, Any],
                          causal_connections: Optional[Set[str]] = None,
                          temporal_context: Optional[Dict[str, Any]] = None,
                          swarm_signals: Optional[Dict[str, float]] = None,
                          uncertainty: Optional[float] = None) -> Tuple[float, Dict[str, float]]:
        """
        Predict the future importance of current information.

        Returns:
            (predicted_importance, component_scores)
        """
        scores = {}

        # 1. Causal importance: preserve antecedents that might cause effects
        causal_score = self._compute_causal_importance(
            content, context, causal_connections
        )
        scores['causal'] = causal_score

        # 2. Temporal importance: preserve periodic/sequential patterns
        temporal_score = self._compute_temporal_importance(
            content, context, temporal_context
        )
        scores['temporal'] = temporal_score

        # 3. Swarm importance: preserve what others find important
        swarm_score = self._compute_swarm_importance(
            content, swarm_signals
        )
        scores['swarm'] = swarm_score

        # 4. Uncertainty importance: preserve when unsure
        uncertainty_score = self._compute_uncertainty_importance(
            content, context, uncertainty
        )
        scores['uncertainty'] = uncertainty_score

        # Weighted combination
        predicted = (
            self.causal_weight * causal_score +
            self.temporal_weight * temporal_score +
            self.swarm_weight * swarm_score +
            self.uncertainty_weight * uncertainty_score
        )

        return predicted, scores

    def _compute_causal_importance(self,
                                   content: str,
                                   context: Dict[str, Any],
                                   causal_connections: Optional[Set[str]] = None) -> float:
        """
        Compute importance based on causal connections.

        Key insight: Information that appears to CAUSE other things
        should be preserved even if it seems irrelevant now.
        """
        score = 0.0

        # Check if this content mentions causal indicators
        causal_indicators = ['because', 'causes', 'leads to', 'results in',
                           'due to', 'since', 'therefore', 'consequent']
        content_lower = content.lower()

        for indicator in causal_indicators:
            if indicator in content_lower:
                score += 0.2

        # Boost if connected to important outcomes
        if causal_connections:
            for connection in causal_connections:
                if connection in self.hindsight_importance:
                    # If what I cause becomes important, I am important
                    score += 0.3 * self.hindsight_importance[connection]

        # Check context for causal role
        if context.get('is_cause', False):
            score += 0.4

        if context.get('is_antecedent', False):
            score += 0.3

        return min(score, 1.0)

    def _compute_temporal_importance(self,
                                     content: str,
                                     context: Dict[str, Any],
                                     temporal_context: Optional[Dict[str, Any]] = None) -> float:
        """
        Compute importance based on temporal patterns.

        Key insight: Information that fits temporal patterns
        (periodic, sequential, trending) should be preserved.
        """
        score = 0.0

        # Check for temporal indicators
        temporal_indicators = ['every', 'always', 'never', 'sometimes',
                             'usually', 'rarely', 'cycle', 'pattern']
        content_lower = content.lower()

        for indicator in temporal_indicators:
            if indicator in content_lower:
                score += 0.15

        # Check temporal context for patterns
        if temporal_context:
            if temporal_context.get('is_periodic', False):
                score += 0.3

            if temporal_context.get('is_part_of_sequence', False):
                score += 0.2

            if temporal_context.get('trend_direction'):
                score += 0.2

        # Check time-based importance
        timestamp = context.get('timestamp', time.time())
        hour = datetime.fromtimestamp(timestamp).hour

        # Some information is more important at certain times
        if 9 <= hour <= 17:  # Business hours
            if 'business' in content_lower or 'work' in content_lower:
                score += 0.2

        return min(score, 1.0)

    def _compute_swarm_importance(self,
                                  content: str,
                                  swarm_signals: Optional[Dict[str, float]] = None) -> float:
        """
        Compute importance based on collective signals.

        Key insight: If other agents/systems find something important,
        it's likely to be important to us too.
        """
        if not swarm_signals:
            return 0.0

        # Aggregate signals
        scores = list(swarm_signals.values())

        if not scores:
            return 0.0

        # Use maximum as the signal (anyone finding it important counts)
        return max(scores)

    def _compute_uncertainty_importance(self,
                                       content: str,
                                       context: Dict[str, Any],
                                       uncertainty: Optional[float] = None) -> float:
        """
        Compute importance based on metacognitive uncertainty.

        Key insight: When unsure, preserve information.
        Better to keep too much than lose something important.
        """
        if uncertainty is None:
            # Infer uncertainty from content
            uncertainty_indicators = ['maybe', 'perhaps', 'possibly',
                                    'uncertain', 'unclear', 'might']
            content_lower = content.lower()

            uncertainty = 0.0
            for indicator in uncertainty_indicators:
                if indicator in content_lower:
                    uncertainty += 0.2

        # Higher uncertainty → higher importance (preserve when unsure)
        return min(uncertainty, 1.0)

    def update_hindsight(self, item_id: str, actual_importance: float) -> None:
        """
        Update hindsight importance when something becomes important later.

        This allows learning what should have been preserved.
        """
        self.hindsight_importance[item_id] = actual_importance

    def get_stats(self) -> Dict[str, Any]:
        """Get predictor statistics"""
        return {
            'hindsight_entries': len(self.hindsight_importance),
            'avg_hindsight_importance': np.mean(list(self.hindsight_importance.values()))
            if self.hindsight_importance else 0.0,
            'causal_graph_nodes': len(self.causal_graph),
        }


# =============================================================================
# KERNEL ASSOCIATIVE MEMORY
# =============================================================================

@dataclass
class MemoryState:
    """
    Compressed memory state using kernel-based associative memory.

    Theoretical correction: This stores outer products, not inner products.
    S = Σ φ(k_i) v_i where φ(k_i) is (d×1) and v_i is (d_v×1)
    Result: S is (d×d_v), built from O(N) outer products of O(d²) each
    """
    state: np.ndarray  # The compressed state matrix (d×d_v)
    kernel_type: KernelType
    timestamp: float
    token_count: int  # How many tokens contributed to this state

    # Metadata for retrieval
    item_ids: List[str] = field(default_factory=list)
    checksum: str = ""

    def compute_checksum(self) -> str:
        """Compute checksum for state verification"""
        return hashlib.md5(self.state.tobytes()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'state': self.state.tolist(),
            'kernel_type': self.kernel_type.value,
            'timestamp': self.timestamp,
            'token_count': self.token_count,
            'item_ids': self.item_ids,
            'checksum': self.checksum
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryState':
        """Create MemoryState from dictionary"""
        return cls(
            state=np.array(data['state']),
            kernel_type=KernelType(data['kernel_type']),
            timestamp=data['timestamp'],
            token_count=data['token_count'],
            item_ids=data['item_ids'],
            checksum=data.get('checksum', '')
        )


@dataclass
class MemoryItem:
    """
    A single memory item with kernel features.
    """
    id: str
    content: str
    embedding: np.ndarray  # Key embedding (k)
    value: np.ndarray  # Value embedding (v)
    importance: float = 0.5
    predicted_importance: float = 0.5
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Kernel features (computed)
    key_features: Optional[np.ndarray] = None  # φ(k)

    def compute_key_features(self, kernel_type: KernelType) -> np.ndarray:
        """Compute kernel features for key"""
        phi = KERNEL_FUNCTIONS[kernel_type]
        self.key_features = phi(self.embedding)
        return self.key_features


class KernelAssociativeMemory:
    """
    Kernel-based associative memory with corrected mathematics and
    solutions to the "apparently irrelevant" problem.

    Key Features:
    1. Hybrid storage: Compressed state + uncompressed buffer
    2. Context-aware importance prediction
    3. Elastic compression with fallback
    4. Multi-scale temporal retention
    """

    def __init__(self,
                 embedding_dim: int = 128,
                 value_dim: int = 128,
                 kernel_type: KernelType = KernelType.HOMOMORPHIC,
                 buffer_size: int = 100,
                 compression_threshold: int = 50,
                 importance_predictor: Optional[ImportancePredictor] = None):
        """
        Args:
            embedding_dim: Dimension of key embeddings
            value_dim: Dimension of value embeddings
            kernel_type: Type of kernel function to use
            buffer_size: Size of uncompressed buffer
            compression_threshold: Items in buffer before compression
            importance_predictor: Optional custom importance predictor
        """
        self.embedding_dim = embedding_dim
        self.value_dim = value_dim
        self.kernel_type = kernel_type
        self.buffer_size = buffer_size
        self.compression_threshold = compression_threshold

        # Importance prediction
        self.importance_predictor = importance_predictor or ImportancePredictor()

        # Storage
        self.buffer: Dict[str, MemoryItem] = {}  # Uncompressed recent items
        self.buffer_order: List[str] = []  # FIFO order

        self.compressed_state: Optional[MemoryState] = None

        # Metadata
        self.total_items_stored = 0
        self.total_compressions = 0

    def store(self,
              content: str,
              embedding: np.ndarray,
              value: Optional[np.ndarray] = None,
              context: Optional[Dict[str, Any]] = None,
              causal_connections: Optional[Set[str]] = None,
              temporal_context: Optional[Dict[str, Any]] = None,
              swarm_signals: Optional[Dict[str, float]] = None,
              uncertainty: Optional[float] = None) -> str:
        """
        Store an item in memory.

        Args:
            content: Text content
            embedding: Key embedding (query/key)
            value: Value embedding (optional, defaults to embedding)
            context: Additional context
            causal_connections: Items this causally influences
            temporal_context: Temporal context info
            swarm_signals: Collective importance signals
            uncertainty: Metacognitive uncertainty

        Returns:
            Item ID
        """
        # Generate ID
        item_id = f"mem_{int(time.time() * 1000000)}_{hash(content) % 1000000}"

        # Create value if not provided
        if value is None:
            value = embedding.copy()

        # Predict future importance
        predicted_importance, _ = self.importance_predictor.predict_importance(
            content, embedding, context or {},
            causal_connections, temporal_context, swarm_signals, uncertainty
        )

        # Create memory item
        item = MemoryItem(
            id=item_id,
            content=content,
            embedding=embedding,
            value=value,
            importance=predicted_importance,
            predicted_importance=predicted_importance,
            metadata=context or {}
        )
        item.compute_key_features(self.kernel_type)

        # Add to buffer
        self.buffer[item_id] = item
        self.buffer_order.append(item_id)
        self.total_items_stored += 1

        # Check if we should compress
        if len(self.buffer) >= self.compression_threshold:
            self._compress_buffer()

        return item_id

    def retrieve(self,
                 query: np.ndarray,
                 top_k: int = 5,
                 include_compressed: bool = True) -> List[Tuple[str, float, str]]:
        """
        Retrieve items by query.

        Args:
            query: Query embedding
            top_k: Number of results
            include_compressed: Whether to include compressed state in query

        Returns:
            List of (item_id, relevance, content_or_summary)
        """
        results = []

        # Query buffer (exact matches available)
        phi_query = KERNEL_FUNCTIONS[self.kernel_type](query)

        for item_id, item in self.buffer.items():
            # Compute similarity using kernel features
            # Standard: φ(q) · φ(k)
            similarity = np.dot(phi_query.flatten(), item.key_features.flatten())

            # Normalize
            norm_q = np.linalg.norm(phi_query)
            norm_k = np.linalg.norm(item.key_features)
            if norm_q > 0 and norm_k > 0:
                similarity /= (norm_q * norm_k)

            # Boost by importance
            similarity *= (1 + item.predicted_importance)

            results.append((item_id, similarity, item.content))

        # Query compressed state
        if include_compressed and self.compressed_state is not None:
            # Linear attention query: φ(q)^T · S
            # where S = Σ φ(k_i) v_i^T (outer products accumulated)
            # φ(q) is (d×1), S is (d×d_v), result is (1×d_v)
            compressed_result = np.dot(phi_query, self.compressed_state.state)

            # Aggregate to get a single relevance score
            # Use mean of absolute values as a measure of overall relevance
            compressed_relevance = np.mean(np.abs(compressed_result))

            # Normalize by query norm
            if norm_q > 0:
                compressed_relevance /= norm_q

            results.append((
                f"compressed_{self.compressed_state.timestamp}",
                compressed_relevance,
                f"[Compressed state: {self.compressed_state.token_count} tokens]"
            ))

        # Sort by relevance
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def _compress_buffer(self) -> None:
        """
        Compress buffer into kernel state.

        Theoretical note: This performs O(N) outer products:
        For each item: φ(k_i) v_i where φ(k_i) is (d×1) and v_i is (1×d_v)
        Result: (d×d_v) matrix
        Total complexity: O(N×d²), NOT O(N×d)

        The benefit is O(1) memory instead of O(N) for all items.
        """
        if not self.buffer:
            return

        # Initialize new state
        new_state = np.zeros((self.embedding_dim, self.value_dim))

        # Accumulate outer products: Σ φ(k_i) v_i
        # This is where the O(d²) per token comes from
        item_ids = []
        for item_id, item in self.buffer.items():
            # Outer product: φ(k) (d×1) × v^T (1×d_v) = d×d_v
            outer_product = np.outer(item.key_features, item.value)

            # Weight by importance
            weighted = outer_product * item.predicted_importance

            # Accumulate
            new_state += weighted
            item_ids.append(item_id)

        # Merge with existing compressed state
        if self.compressed_state is not None:
            new_state += self.compressed_state.state
            item_ids.extend(self.compressed_state.item_ids)

        # Create new compressed state
        self.compressed_state = MemoryState(
            state=new_state,
            kernel_type=self.kernel_type,
            timestamp=time.time(),
            token_count=len(item_ids),
            item_ids=item_ids
        )
        self.compressed_state.checksum = self.compressed_state.compute_checksum()

        # Keep important items in buffer
        self._retain_important_items()

        self.total_compressions += 1

    def _retain_important_items(self) -> None:
        """
        Keep important items uncompressed even after compression.

        This addresses the "apparently irrelevant" problem by
        retaining items with high predicted importance.
        """
        if not self.buffer:
            return

        # Sort by predicted importance
        sorted_items = sorted(
            self.buffer.items(),
            key=lambda x: x[1].predicted_importance,
            reverse=True
        )

        # Keep top items
        retain_count = min(self.buffer_size // 2, len(sorted_items))
        retained = dict(sorted_items[:retain_count])

        # Update buffer
        self.buffer = retained
        self.buffer_order = [item_id for item_id, _ in sorted_items[:retain_count]]

    def force_compression(self) -> None:
        """Force immediate compression of buffer"""
        self._compress_buffer()

    def get_state(self) -> MemoryState:
        """Get current compressed state"""
        if self.compressed_state is None:
            self._compress_buffer()
        return self.compressed_state

    def save_state(self, filepath: str) -> None:
        """Save compressed state to file"""
        if self.compressed_state is None:
            self._compress_buffer()

        data = {
            'compressed_state': self.compressed_state.to_dict(),
            'buffer_items': {
                item_id: {
                    'id': item.id,
                    'content': item.content,
                    'embedding': item.embedding.tolist(),
                    'value': item.value.tolist(),
                    'importance': item.importance,
                    'predicted_importance': item.predicted_importance,
                    'timestamp': item.timestamp,
                    'metadata': item.metadata
                }
                for item_id, item in self.buffer.items()
            },
            'stats': {
                'total_items_stored': self.total_items_stored,
                'total_compressions': self.total_compressions,
            }
        }

        with open(filepath, 'w') as f:
            json.dump(data, f)

    def load_state(self, filepath: str) -> None:
        """Load compressed state from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.compressed_state = MemoryState.from_dict(data['compressed_state'])

        self.buffer = {}
        for item_id, item_data in data['buffer_items'].items():
            item = MemoryItem(
                id=item_data['id'],
                content=item_data['content'],
                embedding=np.array(item_data['embedding']),
                value=np.array(item_data['value']),
                importance=item_data['importance'],
                predicted_importance=item_data['predicted_importance'],
                timestamp=item_data['timestamp'],
                metadata=item_data['metadata']
            )
            item.compute_key_features(self.kernel_type)
            self.buffer[item_id] = item

        stats = data['stats']
        self.total_items_stored = stats['total_items_stored']
        self.total_compressions = stats['total_compressions']

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            'buffer_size': len(self.buffer),
            'compressed_state_exists': self.compressed_state is not None,
            'compressed_token_count': self.compressed_state.token_count if self.compressed_state else 0,
            'total_items_stored': self.total_items_stored,
            'total_compressions': self.total_compressions,
            'compression_ratio': (
                self.compressed_state.token_count / len(self.buffer)
                if self.compressed_state and self.buffer else 0
            ),
            'avg_predicted_importance': np.mean([
                item.predicted_importance for item in self.buffer.values()
            ]) if self.buffer else 0.0,
        }


# =============================================================================
# MULTI-SCALE TEMPORAL MEMORY
# =============================================================================

class MemoryTemporalScale(Enum):
    """Temporal scales for memory retention (renamed to avoid conflict with V4 MCE)"""
    IMMEDIATE = "immediate"  # Seconds to minutes
    SHORT_TERM = "short_term"  # Minutes to hours
    MEDIUM_TERM = "medium_term"  # Hours to days
    LONG_TERM = "long_term"  # Days to weeks
    PERMANENT = "permanent"  # Indefinite

    # For backwards compatibility
    TEMPORAL_SCALE_IMMEDIATE = "immediate"
    TEMPORAL_SCALE_SHORT_TERM = "short_term"
    TEMPORAL_SCALE_MEDIUM_TERM = "medium_term"
    TEMPORAL_SCALE_LONG_TERM = "long_term"
    TEMPORAL_SCALE_PERMANENT = "permanent"


@dataclass
class TemporalMemoryLayer:
    """
    A single temporal layer of memory with specific retention characteristics.
    """
    scale: MemoryTemporalScale
    retention_duration: float  # Seconds
    memory: KernelAssociativeMemory
    last_update: float = field(default_factory=time.time)

    def should_update(self, current_time: float) -> bool:
        """Check if this layer should be updated"""
        return (current_time - self.last_update) >= (self.retention_duration / 10)

    def update_timestamp(self, current_time: float) -> None:
        """Update last update timestamp"""
        self.last_update = current_time


class MultiScaleTemporalMemory:
    """
    Multi-scale temporal memory system.

    Different information is relevant at different time scales:
    - Immediate: Working memory, current focus
    - Short-term: Recent conversations, current tasks
    - Medium-term: Ongoing projects, relationships
    - Long-term: Learned patterns, consolidated knowledge
    - Permanent: Core concepts, fundamental knowledge

    This cascades information between scales, with importance-based promotion.
    """

    def __init__(self,
                 embedding_dim: int = 128,
                 value_dim: int = 128):
        """
        Args:
            embedding_dim: Embedding dimension
            value_dim: Value dimension
        """
        self.embedding_dim = embedding_dim
        self.value_dim = value_dim

        # Create temporal layers
        self.layers = {
            MemoryTemporalScale.IMMEDIATE: TemporalMemoryLayer(
                MemoryTemporalScale.IMMEDIATE,
                retention_duration=300,  # 5 minutes
                memory=KernelAssociativeMemory(
                    embedding_dim=embedding_dim,
                    value_dim=value_dim,
                    buffer_size=50,
                    compression_threshold=20
                )
            ),
            MemoryTemporalScale.SHORT_TERM: TemporalMemoryLayer(
                MemoryTemporalScale.SHORT_TERM,
                retention_duration=3600,  # 1 hour
                memory=KernelAssociativeMemory(
                    embedding_dim=embedding_dim,
                    value_dim=value_dim,
                    buffer_size=200,
                    compression_threshold=50
                )
            ),
            MemoryTemporalScale.MEDIUM_TERM: TemporalMemoryLayer(
                MemoryTemporalScale.MEDIUM_TERM,
                retention_duration=86400,  # 1 day
                memory=KernelAssociativeMemory(
                    embedding_dim=embedding_dim,
                    value_dim=value_dim,
                    buffer_size=500,
                    compression_threshold=100
                )
            ),
            MemoryTemporalScale.LONG_TERM: TemporalMemoryLayer(
                MemoryTemporalScale.LONG_TERM,
                retention_duration=604800,  # 1 week
                memory=KernelAssociativeMemory(
                    embedding_dim=embedding_dim,
                    value_dim=value_dim,
                    buffer_size=1000,
                    compression_threshold=200
                )
            ),
            MemoryTemporalScale.PERMANENT: TemporalMemoryLayer(
                MemoryTemporalScale.PERMANENT,
                retention_duration=float('inf'),
                memory=KernelAssociativeMemory(
                    embedding_dim=embedding_dim,
                    value_dim=value_dim,
                    buffer_size=2000,
                    compression_threshold=500
                )
            ),
        }

    def store(self,
              content: str,
              embedding: np.ndarray,
              value: Optional[np.ndarray] = None,
              context: Optional[Dict[str, Any]] = None,
              target_scale: MemoryTemporalScale = MemoryTemporalScale.IMMEDIATE,
              **kwargs) -> str:
        """
        Store information at a specific temporal scale.

        Important information cascades to longer timescales.
        """
        layer = self.layers[target_scale]
        item_id = layer.memory.store(content, embedding, value, context, **kwargs)

        # Check if important enough for longer timescale
        if target_scale != MemoryTemporalScale.PERMANENT:
            item = layer.memory.buffer.get(item_id)
            if item and item.predicted_importance > 0.7:
                self._promote_to_longer_scale(item, target_scale)

        return item_id

    def _promote_to_longer_scale(self,
                                 item: MemoryItem,
                                 current_scale: MemoryTemporalScale) -> None:
        """Promote important item to longer temporal scale"""
        scales = list(MemoryTemporalScale)
        current_idx = scales.index(current_scale)

        if current_idx < len(scales) - 1:
            next_scale = scales[current_idx + 1]
            next_layer = self.layers[next_scale]

            # Re-store at next level
            next_layer.memory.store(
                item.content,
                item.embedding,
                item.value,
                item.metadata,
                importance=item.importance
            )

    def retrieve(self,
                 query: np.ndarray,
                 top_k: int = 5,
                 scales: Optional[List[MemoryTemporalScale]] = None) -> List[Tuple[str, float, str, MemoryTemporalScale]]:
        """
        Retrieve across multiple temporal scales.

        Returns:
            List of (item_id, relevance, content_or_summary, scale)
        """
        if scales is None:
            scales = list(MemoryTemporalScale)

        all_results = []

        for scale in scales:
            layer = self.layers[scale]
            results = layer.memory.retrieve(query, top_k, include_compressed=True)

            for item_id, relevance, content in results:
                all_results.append((item_id, relevance, content, scale))

        # Sort by relevance
        all_results.sort(key=lambda x: x[1], reverse=True)

        return all_results[:top_k]

    def cascade_compression(self) -> None:
        """
        Cascade compressed states to longer timescales.

        This implements temporal consolidation where information
        flows from shorter to longer timescales.
        """
        current_time = time.time()

        for scale in [MemoryTemporalScale.IMMEDIATE, MemoryTemporalScale.SHORT_TERM,
                     MemoryTemporalScale.MEDIUM_TERM, MemoryTemporalScale.LONG_TERM]:
            layer = self.layers[scale]

            if layer.should_update(current_time):
                # Compress current layer
                layer.memory.force_compression()

                # Get compressed state
                state = layer.memory.get_state()

                # Promote to next level if state is significant
                scales = list(MemoryTemporalScale)
                current_idx = scales.index(scale)

                if current_idx < len(scales) - 1:
                    next_scale = scales[current_idx + 1]
                    next_layer = self.layers[next_scale]

                    # Store compressed state summary
                    next_layer.memory.store(
                        content=f"[Compressed from {scale.value}]",
                        embedding=np.mean(state.state, axis=1),
                        value=np.mean(state.state, axis=0),
                        context={'source_scale': scale.value,
                                'token_count': state.token_count}
                    )

                layer.update_timestamp(current_time)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all temporal layers"""
        return {
            scale.value: layer.memory.get_stats()
            for scale, layer in self.layers.items()
        }


# =============================================================================
# INTEGRATED PERSISTENT MEMORY SYSTEM
# =============================================================================

class IntegratedPersistentMemory:
    """
    Complete persistent memory system integrating:
    - Kernel-based associative memory
    - Importance prediction
    - Multi-scale temporal retention
    - Causal reinforcement
    - Swarm integration
    - Metacognitive monitoring
    """

    def __init__(self,
                 embedding_dim: int = 128,
                 value_dim: int = 128,
                 kernel_type: KernelType = KernelType.HOMOMORPHIC):
        """
        Args:
            embedding_dim: Dimension of embeddings
            value_dim: Dimension of values
            kernel_type: Kernel function type
        """
        self.embedding_dim = embedding_dim
        self.value_dim = value_dim
        self.kernel_type = kernel_type

        # Core components
        self.importance_predictor = ImportancePredictor()
        self.temporal_memory = MultiScaleTemporalMemory(embedding_dim, value_dim)

        # Causal reinforcement tracking
        self.causal_antecedents: Dict[str, Set[str]] = {}  # effects -> causes
        self.causal_consequences: Dict[str, Set[str]] = {}  # causes -> effects

        # Swarm integration
        self.swarm_importance_signals: Dict[str, List[float]] = {}

        # Metacognitive monitoring
        self.uncertainty_tracker: Dict[str, float] = {}

    def remember(self,
                content: str,
                embedding: np.ndarray,
                context: Optional[Dict[str, Any]] = None,
                importance: Optional[float] = None,
                causal_role: Optional[str] = None,
                uncertainty: Optional[float] = None,
                temporal_scale: MemoryTemporalScale = MemoryTemporalScale.IMMEDIATE) -> str:
        """
        Store information with full context integration.

        Args:
            content: Text content
            embedding: Semantic embedding
            context: Additional context
            importance: Manual importance override
            causal_role: 'cause', 'effect', or None
            uncertainty: Metacognitive uncertainty (0-1)
            temporal_scale: Target temporal scale

        Returns:
            Memory item ID
        """
        context = context or {}

        # Track causal relationships
        if causal_role:
            self._track_causal_relationship(content, causal_role, context)

        # Track uncertainty
        if uncertainty is not None:
            item_id = f"uncertainty_{int(time.time())}"
            self.uncertainty_tracker[item_id] = uncertainty

        # Gather swarm signals
        swarm_signals = self._get_swarm_signals(content)

        # Get temporal context
        temporal_context = self._get_temporal_context(context)

        # Store in temporal memory
        item_id = self.temporal_memory.store(
            content=content,
            embedding=embedding,
            context=context,
            target_scale=temporal_scale,
            causal_connections=self.causal_consequences.get(content, set()),
            temporal_context=temporal_context,
            swarm_signals=swarm_signals,
            uncertainty=uncertainty
        )

        return item_id

    def recall(self,
              query: np.ndarray,
              top_k: int = 5,
              scales: Optional[List[MemoryTemporalScale]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve memories across all temporal scales.

        Returns:
            List of results with full context
        """
        raw_results = self.temporal_memory.retrieve(query, top_k, scales)

        results = []
        for item_id, relevance, content, scale in raw_results:
            results.append({
                'id': item_id,
                'content': content,
                'relevance': relevance,
                'temporal_scale': scale.value,
                'timestamp': time.time(),  # Approximate
            })

        return results

    def reinforce_causal(self, cause_id: str, effect_id: str) -> None:
        """
        Reinforce causal relationship between two memories.

        When something that seemed irrelevant causes an important effect,
        boost its importance for future retention.
        """
        if cause_id not in self.causal_consequences:
            self.causal_consequences[cause_id] = set()
        self.causal_consequences[cause_id].add(effect_id)

        if effect_id not in self.causal_antecedents:
            self.causal_antecedents[effect_id] = set()
        self.causal_antecedents[effect_id].add(cause_id)

        # Update hindsight importance
        self.importance_predictor.update_hindsight(cause_id, importance=0.8)

    def add_swarm_signal(self, item_id: str, importance: float) -> None:
        """Add importance signal from swarm/collective intelligence"""
        if item_id not in self.swarm_importance_signals:
            self.swarm_importance_signals[item_id] = []

        self.swarm_importance_signals[item_id].append(importance)

        # Keep only recent signals
        if len(self.swarm_importance_signals[item_id]) > 10:
            self.swarm_importance_signals[item_id].pop(0)

    def cascade_and_compress(self) -> None:
        """Cascade compressed states to longer timescales"""
        self.temporal_memory.cascade_compression()

    def _track_causal_relationship(self,
                                   content: str,
                                   role: str,
                                   context: Dict[str, Any]) -> None:
        """Track causal relationships"""
        item_id = f"causal_{hash(content)}"

        if role == 'cause' and 'causes' in context:
            for effect in context['causes']:
                effect_id = f"effect_{hash(effect)}"
                self.reinforce_causal(item_id, effect_id)

    def _get_swarm_signals(self, content: str) -> Dict[str, float]:
        """Get swarm importance signals for content"""
        signals = {}

        # Look up by content hash
        content_id = f"swarm_{hash(content)}"
        if content_id in self.swarm_importance_signals:
            recent_signals = self.swarm_importance_signals[content_id][-5:]
            signals['swarm_avg'] = np.mean(recent_signals) if recent_signals else 0.0
            signals['swarm_max'] = np.max(recent_signals) if recent_signals else 0.0

        return signals

    def _get_temporal_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get temporal context for importance prediction"""
        temporal_context = {}

        # Check for periodicity
        if 'period' in context:
            temporal_context['is_periodic'] = True

        # Check for sequences
        if 'sequence_position' in context:
            temporal_context['is_part_of_sequence'] = True

        # Check for trends
        if 'trend' in context:
            temporal_context['trend_direction'] = context['trend']

        return temporal_context

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        return {
            'importance_predictor': self.importance_predictor.get_stats(),
            'temporal_memory': self.temporal_memory.get_stats(),
            'causal_relationships': {
                'antecedents_tracked': len(self.causal_antecedents),
                'consequences_tracked': len(self.causal_consequences),
            },
            'swarm_integration': {
                'signals_tracked': len(self.swarm_importance_signals),
            },
            'metacognitive': {
                'uncertainties_tracked': len(self.uncertainty_tracker),
                'avg_uncertainty': np.mean(list(self.uncertainty_tracker.values()))
                if self.uncertainty_tracker else 0.0,
            }
        }

    def save(self, filepath: str) -> None:
        """Save memory system to file"""
        # This would save all components
        # Simplified for now
        pass

    def load(self, filepath: str) -> None:
        """Load memory system from file"""
        # This would load all components
        # Simplified for now
        pass


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_kernel_memory(embedding_dim: int = 128,
                        value_dim: int = 128,
                        kernel_type: KernelType = KernelType.HOMOMORPHIC) -> KernelAssociativeMemory:
    """Create a kernel-based associative memory"""
    return KernelAssociativeMemory(
        embedding_dim=embedding_dim,
        value_dim=value_dim,
        kernel_type=kernel_type
    )


def create_importance_predictor(
    causal_weight: float = 0.3,
    temporal_weight: float = 0.2,
    swarm_weight: float = 0.2,
    uncertainty_weight: float = 0.3
) -> ImportancePredictor:
    """Create an importance predictor"""
    return ImportancePredictor(
        causal_weight=causal_weight,
        temporal_weight=temporal_weight,
        swarm_weight=swarm_weight,
        uncertainty_weight=uncertainty_weight
    )


def create_temporal_memory(embedding_dim: int = 128,
                          value_dim: int = 128) -> MultiScaleTemporalMemory:
    """Create a multi-scale temporal memory"""
    return MultiScaleTemporalMemory(
        embedding_dim=embedding_dim,
        value_dim=value_dim
    )


def create_persistent_memory(embedding_dim: int = 128,
                            value_dim: int = 128,
                            kernel_type: KernelType = KernelType.HOMOMORPHIC) -> IntegratedPersistentMemory:
    """Create a complete integrated persistent memory system"""
    return IntegratedPersistentMemory(
        embedding_dim=embedding_dim,
        value_dim=value_dim,
        kernel_type=kernel_type
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Kernel types
    'KernelType',

    # Kernel functions
    'phi_homomorphic',
    'phi_exponential',
    'phi_rbf',
    'KERNEL_FUNCTIONS',

    # Importance prediction
    'ImportancePredictor',

    # Core memory components
    'MemoryState',
    'MemoryItem',
    'KernelAssociativeMemory',

    # Temporal memory
    'MemoryTemporalScale',  # Renamed from TemporalScale to avoid conflict with V4 MCE
    'TemporalMemoryLayer',
    'MultiScaleTemporalMemory',

    # Integrated system
    'IntegratedPersistentMemory',

    # Factory functions
    'create_kernel_memory',
    'create_importance_predictor',
    'create_temporal_memory',
    'create_persistent_memory',

    # Backwards compatibility aliases
    'TemporalScale',  # Alias for MemoryTemporalScale
]

# Backwards compatibility alias
TemporalScale = MemoryTemporalScale



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



def gaussian_process_predict(X_train: np.ndarray,
                            y_train: np.ndarray,
                            X_test: np.ndarray,
                            kernel: str = 'rbf',
                            length_scale: float = 1.0,
                            noise_variance: float = 0.1) -> Dict[str, Any]:
    """
    Make predictions with uncertainty using Gaussian Process.

    Args:
        X_train: Training inputs
        y_train: Training outputs
        X_test: Test inputs
        kernel: Kernel type ('rbf', 'matern')
        length_scale: Kernel length scale
        noise_variance: Observation noise variance

    Returns:
        Dictionary with predictions and uncertainties
    """
    import numpy as np

    # RBF kernel
    def rbf_kernel(x1, x2, length_scale):
        sq_dist = np.sum(x1**2, axis=1).reshape(-1, 1) +                    np.sum(x2**2, axis=1) - 2 * np.dot(x1, x2.T)
        return np.exp(-0.5 * sq_dist / length_scale**2)

    # Compute kernel matrices
    K = rbf_kernel(X_train, X_train, length_scale) + noise_variance * np.eye(len(X_train))
    K_s = rbf_kernel(X_train, X_test, length_scale)
    K_ss = rbf_kernel(X_test, X_test, length_scale)

    # Cholesky decomposition for stability
    L = np.linalg.cholesky(K)
    alpha = np.linalg.solve(L.T, np.linalg.solve(L, y_train))

    # Predictive mean
    y_mean = K_s.T @ alpha

    # Predictive variance
    v = np.linalg.solve(L, K_s)
    y_var = np.diag(K_ss) - np.sum(v**2, axis=0)

    return {
        'mean': y_mean,
        'std': np.sqrt(np.maximum(y_var, 0)),
        'covariance': K_ss - v.T @ v
    }
                scores.append((var, 0))
                continue
