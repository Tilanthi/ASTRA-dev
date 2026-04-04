"""
Memory Graph: Graph-Based Relational Memory for V36 Entities

Stores relationships between V36 entities (SCMs, latents, observations, analogies)
as a graph structure enabling relational queries and path-based reasoning.

Integration with V36:
- Nodes represent V36 entities (SCMs, latents, observables, symbolic equations)
- Edges represent causal, observational, and analogical relationships
- Supports path queries for causal chain discovery
- Integrates with CrossDomainAnalogyEngine for analogy storage

Date: 2025-11-27
Version: 37.0
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
import json
import time
from collections import defaultdict


class NodeType(Enum):
    """Types of nodes in the memory graph"""
    SCM = "scm"                          # Structural Causal Model
    LATENT = "latent"                    # Latent variable
    OBSERVABLE = "observable"            # Observable variable
    SYMBOLIC_EQUATION = "symbolic_eq"    # Symbolic canonical form
    DOMAIN = "domain"                    # Scientific domain (CLD, D1, D2)
    CONSTRAINT = "constraint"            # Prohibitive constraint
    ANALOGY = "analogy"                  # Cross-domain analogy
    MECHANISM = "mechanism"              # Discovered observation mechanism
    THEORY = "theory"                    # Meta-theory (T_U')
    FUNCTIONAL_ROLE = "functional_role"  # Functional role assignment


class EdgeType(Enum):
    """Types of edges in the memory graph"""
    CAUSES = "causes"                    # Causal relationship (A → B)
    OBSERVES = "observes"                # Latent → Observable
    ANALOGOUS_TO = "analogous_to"        # Cross-domain analogy
    BLENDS_WITH = "blends_with"          # Hybrid world composition
    VIOLATES = "violates"                # Constraint violation
    BELONGS_TO = "belongs_to"            # Domain membership
    HAS_ROLE = "has_role"                # Latent has functional role
    GENERATES = "generates"              # SCM generates observations
    CONTAINS = "contains"                # SCM contains latent/observable
    EVOLVES_TO = "evolves_to"            # Theory evolution
    INSTANTIATES = "instantiates"        # Template instantiation
    DISCOVERED_BY = "discovered_by"      # Mechanism discovery provenance


@dataclass
class GraphNode:
    """A node in the memory graph"""
    node_id: str
    node_type: NodeType
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.node_id)

    def update(self, data: Dict[str, Any]):
        """Update node data"""
        self.data.update(data)
        self.updated_at = time.time()


@dataclass
class GraphEdge:
    """An edge in the memory graph"""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __hash__(self):
        return hash(self.edge_id)


class MemoryGraph:
    """
    Graph-based memory for V36 entities and relationships.

    Provides:
    - CRUD operations for nodes and edges
    - Path queries for causal chain discovery
    - Similarity queries based on graph structure
    - Integration with V36 modules
    - Efficient indexing for common query patterns
    """

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}

        # Indexes for efficient queries
        self._outgoing: Dict[str, List[str]] = defaultdict(list)  # node_id -> [edge_ids]
        self._incoming: Dict[str, List[str]] = defaultdict(list)  # node_id -> [edge_ids]
        self._by_type: Dict[NodeType, Set[str]] = defaultdict(set)  # node_type -> {node_ids}
        self._by_edge_type: Dict[EdgeType, Set[str]] = defaultdict(set)  # edge_type -> {edge_ids}

        self._edge_counter = 0

    # =========================================================================
    # NODE OPERATIONS
    # =========================================================================

    def add_node(self, node_id: str, node_type: NodeType,
                 data: Dict[str, Any] = None,
                 metadata: Dict[str, Any] = None) -> GraphNode:
        """Add a node to the graph"""
        if node_id in self.nodes:
            # Update existing node
            self.nodes[node_id].update(data or {})
            return self.nodes[node_id]

        node = GraphNode(
            node_id=node_id,
            node_type=node_type,
            data=data or {},
            metadata=metadata or {}
        )
        self.nodes[node_id] = node
        self._by_type[node_type].add(node_id)
        return node

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges"""
        if node_id not in self.nodes:
            return False

        node = self.nodes[node_id]

        # Remove all connected edges
        edge_ids_to_remove = list(self._outgoing[node_id]) + list(self._incoming[node_id])
        for edge_id in edge_ids_to_remove:
            self.remove_edge(edge_id)

        # Remove from indexes
        self._by_type[node.node_type].discard(node_id)
        del self._outgoing[node_id]
        del self._incoming[node_id]

        # Remove node
        del self.nodes[node_id]
        return True

    def get_nodes_by_type(self, node_type: NodeType) -> List[GraphNode]:
        """Get all nodes of a specific type"""
        return [self.nodes[nid] for nid in self._by_type[node_type] if nid in self.nodes]

    # =========================================================================
    # EDGE OPERATIONS
    # =========================================================================

    def add_edge(self, source_id: str, target_id: str, edge_type: EdgeType,
                 weight: float = 1.0, properties: Dict[str, Any] = None) -> Optional[GraphEdge]:
        """Add an edge to the graph"""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        self._edge_counter += 1
        edge_id = f"e_{self._edge_counter}"

        edge = GraphEdge(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
            properties=properties or {}
        )

        self.edges[edge_id] = edge
        self._outgoing[source_id].append(edge_id)
        self._incoming[target_id].append(edge_id)
        self._by_edge_type[edge_type].add(edge_id)

        return edge

    def get_edge(self, edge_id: str) -> Optional[GraphEdge]:
        """Get an edge by ID"""
        return self.edges.get(edge_id)

    def remove_edge(self, edge_id: str) -> bool:
        """Remove an edge"""
        if edge_id not in self.edges:
            return False

        edge = self.edges[edge_id]

        # Remove from indexes
        self._outgoing[edge.source_id].remove(edge_id)
        self._incoming[edge.target_id].remove(edge_id)
        self._by_edge_type[edge.edge_type].discard(edge_id)

        # Remove edge
        del self.edges[edge_id]
        return True

    def get_edges_by_type(self, edge_type: EdgeType) -> List[GraphEdge]:
        """Get all edges of a specific type"""
        return [self.edges[eid] for eid in self._by_edge_type[edge_type] if eid in self.edges]

    def get_outgoing_edges(self, node_id: str,
                           edge_type: Optional[EdgeType] = None) -> List[GraphEdge]:
        """Get all outgoing edges from a node"""
        edges = [self.edges[eid] for eid in self._outgoing.get(node_id, []) if eid in self.edges]
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return edges

    def get_incoming_edges(self, node_id: str,
                           edge_type: Optional[EdgeType] = None) -> List[GraphEdge]:
        """Get all incoming edges to a node"""
        edges = [self.edges[eid] for eid in self._incoming.get(node_id, []) if eid in self.edges]
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return edges

    # =========================================================================
    # PATH QUERIES
    # =========================================================================

    def find_path(self, source_id: str, target_id: str,
                  max_depth: int = 10,
                  edge_types: Optional[List[EdgeType]] = None) -> Optional[List[str]]:
        """
        Find shortest path between two nodes.
        Returns list of node IDs in the path, or None if no path exists.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        if source_id == target_id:
            return [source_id]

        # BFS
        visited = {source_id}
        queue = [(source_id, [source_id])]

        while queue and len(queue[0][1]) <= max_depth:
            current, path = queue.pop(0)

            for edge in self.get_outgoing_edges(current):
                if edge_types and edge.edge_type not in edge_types:
                    continue

                neighbor = edge.target_id
                if neighbor == target_id:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def find_all_paths(self, source_id: str, target_id: str,
                       max_depth: int = 5,
                       edge_types: Optional[List[EdgeType]] = None) -> List[List[str]]:
        """Find all paths between two nodes up to max_depth"""
        if source_id not in self.nodes or target_id not in self.nodes:
            return []

        all_paths = []

        def dfs(current: str, path: List[str], visited: Set[str]):
            if len(path) > max_depth:
                return
            if current == target_id:
                all_paths.append(path.copy())
                return

            for edge in self.get_outgoing_edges(current):
                if edge_types and edge.edge_type not in edge_types:
                    continue

                neighbor = edge.target_id
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(neighbor, path, visited)
                    path.pop()
                    visited.remove(neighbor)

        dfs(source_id, [source_id], {source_id})
        return all_paths

    def find_causal_chains(self, source_id: str,
                           max_depth: int = 5) -> List[List[Tuple[str, GraphEdge]]]:
        """
        Find all causal chains starting from a source node.
        Returns list of chains, where each chain is [(node_id, edge), ...]
        """
        chains = []

        def dfs(current: str, chain: List[Tuple[str, GraphEdge]], visited: Set[str]):
            if len(chain) >= max_depth:
                if chain:
                    chains.append(chain.copy())
                return

            causal_edges = self.get_outgoing_edges(current, EdgeType.CAUSES)
            if not causal_edges:
                if chain:
                    chains.append(chain.copy())
                return

            for edge in causal_edges:
                neighbor = edge.target_id
                if neighbor not in visited:
                    visited.add(neighbor)
                    chain.append((neighbor, edge))
                    dfs(neighbor, chain, visited)
                    chain.pop()
                    visited.remove(neighbor)

        dfs(source_id, [], {source_id})
        return chains

    # =========================================================================
    # SIMILARITY & RANKING QUERIES
    # =========================================================================

    def get_neighbors(self, node_id: str, depth: int = 1,
                      edge_types: Optional[List[EdgeType]] = None) -> Set[str]:
        """Get all neighbors within depth hops"""
        if node_id not in self.nodes:
            return set()

        current_level = {node_id}
        all_neighbors = set()

        for _ in range(depth):
            next_level = set()
            for nid in current_level:
                for edge in self.get_outgoing_edges(nid):
                    if edge_types is None or edge.edge_type in edge_types:
                        next_level.add(edge.target_id)
                for edge in self.get_incoming_edges(nid):
                    if edge_types is None or edge.edge_type in edge_types:
                        next_level.add(edge.source_id)
            all_neighbors.update(next_level)
            current_level = next_level - all_neighbors

        all_neighbors.discard(node_id)
        return all_neighbors

    def jaccard_similarity(self, node_a: str, node_b: str,
                           depth: int = 1) -> float:
        """Compute Jaccard similarity based on shared neighbors"""
        neighbors_a = self.get_neighbors(node_a, depth)
        neighbors_b = self.get_neighbors(node_b, depth)

        if not neighbors_a and not neighbors_b:
            return 0.0

        intersection = len(neighbors_a & neighbors_b)
        union = len(neighbors_a | neighbors_b)

        return intersection / union if union > 0 else 0.0

    def rank_by_connectivity(self, query_node: str,
                             candidates: List[str],
                             edge_types: Optional[List[EdgeType]] = None) -> List[Tuple[str, float]]:
        """
        Rank candidates by graph connectivity to query node.
        Used by RRF for graph-based ranking.
        """
        rankings = []

        query_neighbors = self.get_neighbors(query_node, depth=2, edge_types=edge_types)

        for candidate in candidates:
            if candidate == query_node:
                rankings.append((candidate, 1.0))
                continue

            # Check direct connection
            path = self.find_path(query_node, candidate, max_depth=3, edge_types=edge_types)
            if path:
                # Closer = higher score
                score = 1.0 / len(path)
            else:
                # Fall back to Jaccard
                score = self.jaccard_similarity(query_node, candidate) * 0.5

            rankings.append((candidate, score))

        return sorted(rankings, key=lambda x: x[1], reverse=True)

    # =========================================================================
    # V36 INTEGRATION METHODS
    # =========================================================================

    def add_scm(self, scm_id: str, scm_data: Dict[str, Any],
                domain: str = None) -> GraphNode:
        """Add an SCM node with its structure"""
        node = self.add_node(scm_id, NodeType.SCM, scm_data)

        # Add domain edge if specified
        if domain:
            domain_node = self.add_node(f"domain_{domain}", NodeType.DOMAIN, {"name": domain})
            self.add_edge(scm_id, domain_node.node_id, EdgeType.BELONGS_TO)

        # Add latent nodes
        for latent_name, latent_data in scm_data.get('latents', {}).items():
            latent_id = f"{scm_id}_{latent_name}"
            latent_node = self.add_node(latent_id, NodeType.LATENT, {
                "name": latent_name,
                "scm_id": scm_id,
                **({} if isinstance(latent_data, (list, type(None))) else {"timeseries_length": len(latent_data) if hasattr(latent_data, '__len__') else 0})
            })
            self.add_edge(scm_id, latent_id, EdgeType.CONTAINS)

        # Add observable nodes
        for obs_name, obs_data in scm_data.get('observations', {}).items():
            obs_id = f"{scm_id}_{obs_name}"
            obs_node = self.add_node(obs_id, NodeType.OBSERVABLE, {
                "name": obs_name,
                "scm_id": scm_id
            })
            self.add_edge(scm_id, obs_id, EdgeType.CONTAINS)

        return node

    def add_analogy(self, analogy_data: Dict[str, Any]) -> GraphNode:
        """Add a cross-domain analogy from V36 CrossDomainAnalogyEngine"""
        analogy_id = f"analogy_{analogy_data['var_A_domain']}_{analogy_data['var_A_name']}_{analogy_data['var_B_domain']}_{analogy_data['var_B_name']}"

        node = self.add_node(analogy_id, NodeType.ANALOGY, analogy_data)

        # Create analogous edge between the variables
        var_a_id = f"{analogy_data['var_A_domain']}_{analogy_data['var_A_name']}"
        var_b_id = f"{analogy_data['var_B_domain']}_{analogy_data['var_B_name']}"

        # Add variable nodes if they don't exist
        if var_a_id not in self.nodes:
            self.add_node(var_a_id, NodeType.LATENT, {
                "name": analogy_data['var_A_name'],
                "domain": analogy_data['var_A_domain']
            })
        if var_b_id not in self.nodes:
            self.add_node(var_b_id, NodeType.LATENT, {
                "name": analogy_data['var_B_name'],
                "domain": analogy_data['var_B_domain']
            })

        self.add_edge(var_a_id, var_b_id, EdgeType.ANALOGOUS_TO,
                     weight=analogy_data.get('similarity_score', 1.0),
                     properties={"evidence": analogy_data.get('evidence', [])})

        return node

    def add_constraint_violation(self, entity_id: str, constraint_id: str,
                                  severity: str, description: str):
        """Record a constraint violation"""
        # Ensure constraint node exists
        if f"constraint_{constraint_id}" not in self.nodes:
            self.add_node(f"constraint_{constraint_id}", NodeType.CONSTRAINT, {
                "constraint_id": constraint_id
            })

        self.add_edge(entity_id, f"constraint_{constraint_id}", EdgeType.VIOLATES,
                     properties={"severity": severity, "description": description})

    def get_analogies_for_variable(self, var_id: str) -> List[Dict[str, Any]]:
        """Get all analogies involving a variable"""
        analogies = []

        for edge in self.get_outgoing_edges(var_id, EdgeType.ANALOGOUS_TO):
            analogies.append({
                "analogous_to": edge.target_id,
                "similarity": edge.weight,
                "evidence": edge.properties.get("evidence", [])
            })

        for edge in self.get_incoming_edges(var_id, EdgeType.ANALOGOUS_TO):
            analogies.append({
                "analogous_to": edge.source_id,
                "similarity": edge.weight,
                "evidence": edge.properties.get("evidence", [])
            })

        return analogies

    def get_violations_for_entity(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all constraint violations for an entity"""
        violations = []
        for edge in self.get_outgoing_edges(entity_id, EdgeType.VIOLATES):
            constraint_node = self.get_node(edge.target_id)
            violations.append({
                "constraint_id": edge.target_id,
                "severity": edge.properties.get("severity"),
                "description": edge.properties.get("description"),
                "constraint_data": constraint_node.data if constraint_node else {}
            })
        return violations

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict:
        """Serialize graph to dictionary"""
        return {
            "nodes": {
                nid: {
                    "node_id": n.node_id,
                    "node_type": n.node_type.value,
                    "data": n.data,
                    "created_at": n.created_at,
                    "updated_at": n.updated_at,
                    "metadata": n.metadata
                }
                for nid, n in self.nodes.items()
            },
            "edges": {
                eid: {
                    "edge_id": e.edge_id,
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "edge_type": e.edge_type.value,
                    "weight": e.weight,
                    "properties": e.properties,
                    "created_at": e.created_at
                }
                for eid, e in self.edges.items()
            },
            "edge_counter": self._edge_counter
        }

    def save(self, filepath: str):
        """Save graph to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'MemoryGraph':
        """Load graph from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        graph = cls()
        graph._edge_counter = data.get("edge_counter", 0)

        # Load nodes
        for nid, ndata in data["nodes"].items():
            node = GraphNode(
                node_id=ndata["node_id"],
                node_type=NodeType(ndata["node_type"]),
                data=ndata["data"],
                created_at=ndata.get("created_at", time.time()),
                updated_at=ndata.get("updated_at", time.time()),
                metadata=ndata.get("metadata", {})
            )
            graph.nodes[nid] = node
            graph._by_type[node.node_type].add(nid)

        # Load edges
        for eid, edata in data["edges"].items():
            edge = GraphEdge(
                edge_id=edata["edge_id"],
                source_id=edata["source_id"],
                target_id=edata["target_id"],
                edge_type=EdgeType(edata["edge_type"]),
                weight=edata.get("weight", 1.0),
                properties=edata.get("properties", {}),
                created_at=edata.get("created_at", time.time())
            )
            graph.edges[eid] = edge
            graph._outgoing[edge.source_id].append(eid)
            graph._incoming[edge.target_id].append(eid)
            graph._by_edge_type[edge.edge_type].add(eid)

        return graph

    def stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "nodes_by_type": {t.value: len(ids) for t, ids in self._by_type.items()},
            "edges_by_type": {t.value: len(ids) for t, ids in self._by_edge_type.items()}
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'MemoryGraph',
    'GraphNode',
    'GraphEdge',
    'NodeType',
    'EdgeType'
]



# Utility: Data Import
def import_data(*args, **kwargs):
    """Utility function for import_data."""
    return None



def utility_function_17(*args, **kwargs):
    """Utility function 17."""
    return None
