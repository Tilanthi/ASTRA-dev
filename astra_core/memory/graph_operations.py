"""
NetworkX Integration for ASTRA Memory Graph Operations

This module integrates NetworkX for advanced graph algorithms and operations
on ASTRA's knowledge graphs, including MORK Ontology and Context Graph.

Key capabilities:
- Centrality analysis (identify important concepts)
- Community detection (discover knowledge clusters)
- Shortest path queries (semantic navigation)
- Graph visualization support
- Efficient graph algorithms
"""

from typing import Dict, List, Set, Tuple, Optional, Any, Union
import logging

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

logger = logging.getLogger(__name__)


class NetworkXMemoryGraph:
    """
    NetworkX-backed memory graph for ASTRA's knowledge systems.

    Provides efficient graph algorithms for:
    - MORK Ontology operations
    - Context Graph navigation
    - Knowledge cluster discovery
    - Semantic relationship analysis
    """

    def __init__(self, graph_type: str = "directed"):
        """
        Initialize NetworkX graph.

        Args:
            graph_type: Type of graph ("directed", "undirected", "multi_directed", "multi_undirected")
        """
        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX not available. Memory graph operations will be limited.")
            self.graph = None
            self.available = False
            return

        self.available = True

        if graph_type == "directed":
            self.graph = nx.DiGraph()
        elif graph_type == "undirected":
            self.graph = nx.Graph()
        elif graph_type == "multi_directed":
            self.graph = nx.MultiDiGraph()
        elif graph_type == "multi_undirected":
            self.graph = nx.MultiGraph()
        else:
            raise ValueError(f"Unknown graph type: {graph_type}")

        self.graph_type = graph_type
        logger.info(f"Initialized NetworkX {graph_type} graph")

    def add_node(self, node_id: str, **attributes):
        """Add a node with optional attributes."""
        if self.available and self.graph is not None:
            self.graph.add_node(node_id, **attributes)

    def add_edge(self, source: str, target: str, relation: str = "related_to", **attributes):
        """Add an edge with optional attributes."""
        if self.available and self.graph is not None:
            self.graph.add_edge(source, target, relation=relation, **attributes)

    def get_neighbors(self, node_id: str) -> List[str]:
        """Get neighboring nodes."""
        if self.available and self.graph is not None:
            return list(self.graph.neighbors(node_id))
        return []

    def shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        Find shortest path between two nodes.

        Returns:
            List of node IDs forming the path, or None if no path exists.
        """
        if self.available and self.graph is not None:
            try:
                return nx.shortest_path(self.graph, source, target)
            except (nx.NodeNotFound, nx.NetworkXNoPath):
                return None
        return None

    def all_shortest_paths(self, source: str, target: str) -> List[List[str]]:
        """Get all shortest paths between two nodes."""
        if self.available and self.graph is not None:
            try:
                return list(nx.all_shortest_paths(self.graph, source, target))
            except (nx.NodeNotFound, nx.NetworkXNoPath):
                return []
        return []

    def centrality_measures(self, node: str) -> Dict[str, float]:
        """
        Calculate centrality measures for a node.

        Returns:
            Dict with 'degree', 'betweenness', 'closeness', 'pagerank' centrality
        """
        if not self.available or self.graph is None:
            return {}

        result = {}

        try:
            result['degree'] = self.graph.degree(node)
        except (nx.NodeNotFound, ValueError):
            result['degree'] = 0

        try:
            betweenness = nx.betweenness_centrality(self.graph)
            result['betweenness'] = betweenness.get(node, 0)
        except Exception:
            result['betweenness'] = 0

        try:
            closeness = nx.closeness_centrality(self.graph)
            result['closeness'] = closeness.get(node, 0)
        except Exception:
            result['closeness'] = 0

        try:
            pagerank = nx.pagerank(self.graph)
            result['pagerank'] = pagerank.get(node, 0)
        except Exception:
            result['pagerank'] = 0

        return result

    def community_detection(self, algorithm: str = "louvain") -> Dict[str, int]:
        """
        Detect communities in the graph.

        Args:
            algorithm: Community detection algorithm ("louvain", "label_propagation", "greedy")

        Returns:
            Dict mapping node_id to community_id
        """
        if not self.available or self.graph is None:
            return {}

        try:
            if algorithm == "louvain":
                import networkx.algorithms.community as nx_community
                communities = nx_community.louvain_communities(self.graph)
                return {node: i for i, community in enumerate(communities) for node in community}

            elif algorithm == "label_propagation":
                communities = nx.label_propagation_communities(self.graph)
                return {node: i for i, community in enumerate(communities) for node in community}

            elif algorithm == "greedy":
                from networkx.algorithms.community import greedy_modularity_communities
                communities = greedy_modularity_communities(self.graph)
                return {node: i for i, community in enumerate(communities) for node in community}

        except Exception as e:
            logger.warning(f"Community detection failed: {e}")

        return {}

    def connected_components(self) -> List[Set[str]]:
        """Get connected components of the graph."""
        if not self.available or self.graph is None:
            return []

        try:
            if isinstance(self.graph, nx.DiGraph):
                return list(nx.weakly_connected_components(self.graph))
            else:
                return list(nx.connected_components(self.graph))
        except Exception:
            return []

    def subgraph(self, nodes: List[str]) -> 'NetworkXMemoryGraph':
        """Extract subgraph containing specified nodes."""
        if not self.available or self.graph is None:
            return NetworkXMemoryGraph(self.graph_type)

        try:
            subgraph = self.graph.subgraph(nodes).copy()
            result = NetworkXMemoryGraph(self.graph_type)
            result.graph = subgraph
            return result
        except Exception:
            return NetworkXMemoryGraph(self.graph_type)

    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        if not self.available or self.graph is None:
            return {}

        stats = {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'is_directed': self.graph.is_directed(),
        }

        try:
            stats['density'] = nx.density(self.graph)
        except Exception:
            stats['density'] = 0

        try:
            if isinstance(self.graph, nx.DiGraph):
                stats['is_strongly_connected'] = nx.is_strongly_connected(self.graph)
                stats['num_weakly_connected_components'] = nx.number_weakly_connected_components(self.graph)
            else:
                stats['is_connected'] = nx.is_connected(self.graph)
                stats['num_connected_components'] = nx.number_connected_components(self.graph)
        except Exception:
            pass

        return stats


class MORKOntologyGraph(NetworkXMemoryGraph):
    """
    NetworkX-backed MORK Ontology for concept hierarchy operations.

    Extends NetworkXMemoryGraph with ontology-specific operations:
    - Concept hierarchy traversal
    - Ontology consistency checking
    - Taxonomic reasoning
    - Concept similarity metrics
    """

    def __init__(self):
        """Initialize MORK Ontology as a directed graph."""
        super().__init__(graph_type="directed")
        self.concept_hierarchy: Dict[str, List[str]] = {}

    def add_concept(self, concept: str, parent: Optional[str] = None, **attributes):
        """Add concept to ontology with optional parent."""
        self.add_node(concept, node_type="concept", **attributes)
        if parent:
            self.add_edge(parent, concept, relation="is_a")
            if parent not in self.concept_hierarchy:
                self.concept_hierarchy[parent] = []
            self.concept_hierarchy[parent].append(concept)

    def get_ancestors(self, concept: str) -> List[str]:
        """Get all ancestor concepts (transitive is_a relationships)."""
        if not self.available or self.graph is None:
            return []

        try:
            return list(nx.ancestors(self.graph, concept))
        except Exception:
            return []

    def get_descendants(self, concept: str) -> List[str]:
        """Get all descendant concepts."""
        if not self.available or self.graph is None:
            return []

        try:
            return list(nx.descendants(self.graph, concept))
        except Exception:
            return []

    def lowest_common_ancestor(self, concept1: str, concept2: str) -> Optional[str]:
        """Find lowest common ancestor of two concepts."""
        if not self.available or self.graph is None:
            return None

        try:
            ancestors1 = set(self.get_ancestors(concept1)) | {concept1}
            ancestors2 = set(self.get_ancestors(concept2)) | {concept2}
            common = ancestors1 & ancestors2

            if not common:
                return None

            # Find the one with maximum depth (furthest from root)
            depths = {}
            for node in common:
                depths[node] = len(list(nx.all_simple_paths(self.graph, node, concept1))[0])

            return max(depths, key=depths.get)
        except Exception:
            return None


class ContextGraphOperations(NetworkXMemoryGraph):
    """
    NetworkX-backed operations for ASTRA's Context Graph.

    Provides context-aware graph operations:
    - Temporal context tracking
    - Cross-domain linking
    - Relevance propagation
    - Context subgraph extraction
    """

    def __init__(self):
        """Initialize Context Graph as directed multigraph."""
        super().__init__(graph_type="multi_directed")

    def add_context_link(self, source: str, target: str,
                        context_type: str, strength: float = 1.0,
                        timestamp: Optional[float] = None, **attributes):
        """Add context-aware link between concepts."""
        self.add_edge(source, target, relation=context_type,
                     strength=strength, timestamp=timestamp, **attributes)

    def propagate_relevance(self, seed_nodes: List[str],
                           max_depth: int = 3,
                           decay_factor: float = 0.5) -> Dict[str, float]:
        """
        Propagate relevance from seed nodes through the graph.

        Returns:
            Dict mapping node_id to relevance score
        """
        if not self.available or self.graph is None:
            return {}

        relevance = {node: 1.0 for node in seed_nodes}
        visited = set(seed_nodes)

        for depth in range(max_depth):
            current_level = list(relevance.keys())

            for node in current_level:
                for neighbor in self.get_neighbors(node):
                    if neighbor not in visited:
                        edge_strength = self._get_edge_strength(node, neighbor)
                        relevance[neighbor] = relevance.get(neighbor, 0) + \
                                             relevance[node] * edge_strength * (decay_factor ** depth)
                        visited.add(neighbor)

        return relevance

    def _get_edge_strength(self, source: str, target: str) -> float:
        """Get strength of edge between source and target."""
        if not self.available or self.graph is None:
            return 1.0

        try:
            edge_data = self.graph.get_edge_data(source, target)
            if edge_data:
                if isinstance(edge_data, dict):
                    return edge_data.get('strength', 1.0)
                elif isinstance(edge_data, list):
                    return max(e.get('strength', 1.0) for e in edge_data)
        except Exception:
            pass

        return 1.0

    def extract_context_subgraph(self, seed_nodes: List[str],
                                radius: int = 2) -> 'NetworkXMemoryGraph':
        """Extract subgraph around seed nodes within given radius."""
        if not self.available or self.graph is None:
            return NetworkXMemoryGraph("multi_directed")

        nodes_to_include = set(seed_nodes)

        for _ in range(radius):
            new_nodes = set()
            for node in nodes_to_include:
                new_nodes.update(self.get_neighbors(node))
            nodes_to_include.update(new_nodes)

        return self.subgraph(list(nodes_to_include))


# Factory function
def create_memory_graph(graph_type: str = "directed") -> NetworkXMemoryGraph:
    """Create appropriate memory graph based on type."""
    if graph_type == "mork_ontology":
        return MORKOntologyGraph()
    elif graph_type == "context":
        return ContextGraphOperations()
    else:
        return NetworkXMemoryGraph(graph_type)


# Check availability
def is_networkx_available() -> bool:
    """Check if NetworkX is available and functional."""
    return NETWORKX_AVAILABLE
