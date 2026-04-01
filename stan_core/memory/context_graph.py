"""
Context Graph for Meta-Context Engine

Maintains relationships between context layers, enabling efficient
context retrieval and shift prediction.

Version: 4.0.0
Date: 2026-03-17
"""

from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import time


class ContextRelationType(Enum):
    """Types of relationships between contexts"""
    TEMPORAL_CONTAINS = "temporal_contains"  # One context contains another temporally
    TEMPORAL_PRECEDES = "temporal_precedes"  # One context precedes another
    SEMANTIC_SIMILAR = "semantic_similar"   # Contexts are semantically similar
    FRAME_CONFLICT = "frame_conflict"       # Contexts have conflicting frames
    FRAME_COMPLEMENTARY = "frame_complementary"  # Contexts complement each other
    TRANSITION_PATH = "transition_path"     # Valid transition between contexts


@dataclass
class ContextRelation:
    """A relationship between two context layers"""
    source_layer_id: str
    target_layer_id: str
    relation_type: ContextRelationType
    strength: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ContextNode:
    """A node in the context graph"""
    layer_id: str
    temporal_scale: str
    cognitive_frame: str
    activation_history: List[float] = field(default_factory=list)
    transition_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_activation(self, activation: float) -> None:
        """Update activation history."""
        self.activation_history.append(activation)
        if len(self.activation_history) > 100:
            self.activation_history.pop(0)
        self.last_accessed = time.time()


class ContextGraph:
    """
    Graph structure maintaining context relationships.

    Enables efficient context retrieval, shift prediction, and
    transition path finding.
    """

    def __init__(self):
        self.nodes: Dict[str, ContextNode] = {}
        self.edges: Dict[str, List[ContextRelation]] = defaultdict(list)
        self.relation_index: Dict[Tuple[str, str], ContextRelation] = {}
        self.transition_history: List[Tuple[str, str, float]] = []

    def add_context_node(
        self,
        layer_id: str,
        temporal_scale: str,
        cognitive_frame: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextNode:
        """Add a context node to the graph."""
        if layer_id in self.nodes:
            return self.nodes[layer_id]

        node = ContextNode(
            layer_id=layer_id,
            temporal_scale=temporal_scale,
            cognitive_frame=cognitive_frame,
            metadata=metadata or {}
        )
        self.nodes[layer_id] = node
        return node

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: ContextRelationType,
        strength: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextRelation:
        """Add a relationship between two context nodes."""
        relation = ContextRelation(
            source_layer_id=source_id,
            target_layer_id=target_id,
            relation_type=relation_type,
            strength=strength,
            metadata=metadata or {}
        )

        self.edges[source_id].append(relation)
        self.relation_index[(source_id, target_id)] = relation
        return relation

    def get_related_contexts(
        self,
        layer_id: str,
        relation_type: Optional[ContextRelationType] = None,
        min_strength: float = 0.0
    ) -> List[Tuple[str, float]]:
        """Get contexts related to the given layer."""
        if layer_id not in self.edges:
            return []

        related = []
        for relation in self.edges[layer_id]:
            if relation_type is None or relation.relation_type == relation_type:
                if relation.strength >= min_strength:
                    related.append((relation.target_layer_id, relation.strength))

        return sorted(related, key=lambda x: x[1], reverse=True)

    def find_transition_path(
        self,
        from_layer_id: str,
        to_layer_id: str
    ) -> Optional[List[str]]:
        """Find a path between two context layers."""
        if from_layer_id not in self.nodes or to_layer_id not in self.nodes:
            return None

        if from_layer_id == to_layer_id:
            return [from_layer_id]

        # BFS for shortest path
        from queue import Queue
        queue = Queue()
        queue.put(from_layer_id)

        visited = {from_layer_id}
        parent = {from_layer_id: None}

        while not queue.empty():
            current = queue.get()

            # Check transition edges
            for relation in self.edges.get(current, []):
                if relation.relation_type == ContextRelationType.TRANSITION_PATH:
                    neighbor = relation.target_layer_id

                    if neighbor == to_layer_id:
                        # Reconstruct path
                        path = [to_layer_id]
                        while current is not None:
                            path.append(current)
                            current = parent.get(current)
                        return list(reversed(path))

                    if neighbor not in visited:
                        visited.add(neighbor)
                        parent[neighbor] = current
                        queue.put(neighbor)

        return None

    def record_transition(
        self,
        from_layer_id: str,
        to_layer_id: str,
        confidence: float = 1.0
    ) -> None:
        """Record a context transition."""
        self.transition_history.append((from_layer_id, to_layer_id, time.time()))

        # Update transition counts
        if from_layer_id in self.nodes:
            self.nodes[from_layer_id].transition_count += 1

        # Strengthen transition relation
        key = (from_layer_id, to_layer_id)
        if key in self.relation_index:
            self.relation_index[key].strength = min(
                0.9 * self.relation_index[key].strength + 0.1 * confidence,
                1.0
            )
        else:
            # Create new transition relation
            self.add_relation(
                from_layer_id,
                to_layer_id,
                ContextRelationType.TRANSITION_PATH,
                strength=confidence
            )

    def get_transition_probability(
        self,
        from_layer_id: str,
        to_layer_id: str
    ) -> float:
        """Get probability of transition between contexts."""
        key = (from_layer_id, to_layer_id)
        if key in self.relation_index:
            return self.relation_index[key].strength
        return 0.0

    def get_frequent_transitions(
        self,
        min_count: int = 3
    ) -> List[Tuple[str, str, int]]:
        """Get most frequent context transitions."""
        from collections import Counter

        transition_pairs = [(f, t) for f, t, _ in self.transition_history]
        counts = Counter(transition_pairs)

        return [(f, t, c) for (f, t), c in counts.most_common() if c >= min_count]

    def get_context_clusters(
        self,
        min_similarity: float = 0.7
    ) -> List[List[str]]:
        """Cluster contexts by semantic similarity."""
        clusters = []
        visited = set()

        for layer_id in self.nodes:
            if layer_id in visited:
                continue

            # Start new cluster
            cluster = [layer_id]
            visited.add(layer_id)

            # Find similar contexts
            for relation in self.edges.get(layer_id, []):
                if (relation.relation_type == ContextRelationType.SEMANTIC_SIMILAR
                    and relation.strength >= min_similarity
                    and relation.target_layer_id not in visited):
                    cluster.append(relation.target_layer_id)
                    visited.add(relation.target_layer_id)

            if len(cluster) > 1:
                clusters.append(cluster)

        return clusters

    def update_semantic_similarity(
        self,
        layer_id_1: str,
        layer_id_2: str,
        similarity: float
    ) -> None:
        """Update semantic similarity between two contexts."""
        key = (layer_id_1, layer_id_2)

        if key in self.relation_index:
            # Smooth update
            old_similarity = self.relation_index[key].strength
            new_similarity = 0.8 * old_similarity + 0.2 * similarity
            self.relation_index[key].strength = new_similarity
        else:
            # Create new similarity relation (bidirectional)
            self.add_relation(
                layer_id_1,
                layer_id_2,
                ContextRelationType.SEMANTIC_SIMILAR,
                strength=similarity
            )
            self.add_relation(
                layer_id_2,
                layer_id_1,
                ContextRelationType.SEMANTIC_SIMILAR,
                strength=similarity
            )

    def get_context_statistics(self) -> Dict[str, Any]:
        """Get statistics about the context graph."""
        total_transitions = len(self.transition_history)
        active_nodes = sum(1 for n in self.nodes.values() if n.activation_history)

        avg_activation = 0.0
        if active_nodes > 0:
            avg_activation = sum(
                n.activation_history[-1] for n in self.nodes.values()
                if n.activation_history
            ) / active_nodes

        return {
            "total_nodes": len(self.nodes),
            "total_edges": sum(len(e) for e in self.edges.values()),
            "total_transitions": total_transitions,
            "active_nodes": active_nodes,
            "average_activation": avg_activation,
            "transition_pairs": len(set((f, t) for f, t, _ in self.transition_history))
        }

    def cleanup_old_nodes(self, max_age: float = 86400.0) -> int:
        """Remove nodes that haven't been accessed recently."""
        current_time = time.time()
        to_remove = []

        for layer_id, node in self.nodes.items():
            if current_time - node.last_accessed > max_age:
                # Check if node has low activity
                if not node.activation_history or node.activation_history[-1] < 0.1:
                    to_remove.append(layer_id)

        for layer_id in to_remove:
            self.remove_context_node(layer_id)

        return len(to_remove)

    def remove_context_node(self, layer_id: str) -> None:
        """Remove a context node and its relations."""
        if layer_id not in self.nodes:
            return

        # Remove edges where this node is source
        if layer_id in self.edges:
            del self.edges[layer_id]

        # Remove edges where this node is target
        for source_id, relations in list(self.edges.items()):
            self.edges[source_id] = [
                r for r in relations if r.target_layer_id != layer_id
            ]

        # Remove from relation index
        keys_to_remove = [k for k in self.relation_index if layer_id in k]
        for key in keys_to_remove:
            del self.relation_index[key]

        # Remove node
        del self.nodes[layer_id]

    def export_graph(self) -> Dict[str, Any]:
        """Export graph structure for serialization."""
        return {
            "nodes": {
                lid: {
                    "temporal_scale": n.temporal_scale,
                    "cognitive_frame": n.cognitive_frame,
                    "transition_count": n.transition_count,
                    "metadata": n.metadata
                }
                for lid, n in self.nodes.items()
            },
            "edges": [
                {
                    "source": r.source_layer_id,
                    "target": r.target_layer_id,
                    "type": r.relation_type.value,
                    "strength": r.strength,
                    "metadata": r.metadata
                }
                for relations in self.edges.values()
                for r in relations
            ]
        }

    def import_graph(self, graph_data: Dict[str, Any]) -> None:
        """Import graph structure from serialization."""
        # Import nodes
        for lid, node_data in graph_data.get("nodes", {}).items():
            self.add_context_node(
                layer_id=lid,
                temporal_scale=node_data["temporal_scale"],
                cognitive_frame=node_data["cognitive_frame"],
                metadata=node_data.get("metadata", {})
            )
            self.nodes[lid].transition_count = node_data.get("transition_count", 0)

        # Import edges
        for edge_data in graph_data.get("edges", []):
            self.add_relation(
                source_id=edge_data["source"],
                target_id=edge_data["target"],
                relation_type=ContextRelationType(edge_data["type"]),
                strength=edge_data["strength"],
                metadata=edge_data.get("metadata", {})
            )



def utility_function_17(*args, **kwargs):
    """Utility function 17."""
    return None



# Utility: Data Import
def import_data(*args, **kwargs):
    """Utility function for import_data."""
    return None
