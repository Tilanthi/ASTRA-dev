"""
Three-Way Reciprocal Rank Fusion (RRF)

Combines results from MORK (ontological), Memory Graph (relational), and
Milvus (vector) into unified rankings for V36 queries.

RRF Formula: score(d) = Σ 1/(k + rank_i(d)) for each ranking source i

Integration with V36:
- Unified retrieval for CrossDomainAnalogyEngine
- Enhanced mechanism discovery via multi-source ranking
- Domain composition inference with hybrid evidence

Date: 2025-11-27
Version: 37.0
"""

from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

from .mork_ontology import MORKOntology
from .memory_graph import MemoryGraph, EdgeType
from .milvus_store import MilvusVectorStore


class RankingSource(Enum):
    """Sources for ranking in RRF"""
    MORK = "mork"           # Ontological distance
    GRAPH = "graph"         # Graph connectivity
    MILVUS = "milvus"       # Vector similarity


@dataclass
class RRFResult:
    """Result from RRF fusion"""
    entity_id: str
    fused_score: float
    source_scores: Dict[str, float]
    source_ranks: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RankingConfig:
    """Configuration for ranking weights and parameters"""
    k: int = 60                        # RRF constant (standard value)
    weights: Dict[str, float] = None   # Source weights
    min_sources: int = 1               # Minimum sources that must return results

    def __post_init__(self):
        if self.weights is None:
            # Default weights optimized for V36 causal reasoning
            self.weights = {
                RankingSource.MORK.value: 0.3,    # Ontological structure
                RankingSource.GRAPH.value: 0.4,   # Causal relationships (most important)
                RankingSource.MILVUS.value: 0.3   # Numerical similarity
            }


class ThreeWayRRF:
    """
    Reciprocal Rank Fusion combining three retrieval sources.

    Provides:
    - Unified retrieval across MORK, Graph, and Milvus
    - Configurable weights for different query types
    - V36-specific query methods
    - Fallback handling when sources are unavailable
    """

    def __init__(self, mork: MORKOntology, graph: MemoryGraph,
                 milvus: MilvusVectorStore, config: RankingConfig = None):
        self.mork = mork
        self.graph = graph
        self.milvus = milvus
        self.config = config or RankingConfig()

    def _rrf_score(self, rank: int, k: int = None) -> float:
        """Compute RRF score for a given rank (1-indexed)"""
        k = k or self.config.k
        return 1.0 / (k + rank)

    def _fuse_rankings(self, rankings: Dict[str, List[Tuple[str, float]]],
                       weights: Dict[str, float] = None) -> List[RRFResult]:
        """
        Fuse multiple rankings using weighted RRF.

        Args:
            rankings: {source_name: [(entity_id, score), ...]}
            weights: {source_name: weight}

        Returns:
            List of RRFResult sorted by fused score
        """
        weights = weights or self.config.weights
        k = self.config.k

        # Collect all unique entities
        all_entities = set()
        for ranking in rankings.values():
            for entity_id, _ in ranking:
                all_entities.add(entity_id)

        # Compute RRF scores
        results = {}
        for entity_id in all_entities:
            source_scores = {}
            source_ranks = {}
            fused_score = 0.0

            for source_name, ranking in rankings.items():
                # Find rank (1-indexed)
                rank = None
                original_score = 0.0
                for i, (eid, score) in enumerate(ranking):
                    if eid == entity_id:
                        rank = i + 1
                        original_score = score
                        break

                if rank is not None:
                    source_scores[source_name] = original_score
                    source_ranks[source_name] = rank
                    weight = weights.get(source_name, 1.0)
                    fused_score += weight * self._rrf_score(rank, k)

            results[entity_id] = RRFResult(
                entity_id=entity_id,
                fused_score=fused_score,
                source_scores=source_scores,
                source_ranks=source_ranks
            )

        # Sort by fused score
        sorted_results = sorted(results.values(), key=lambda x: x.fused_score, reverse=True)
        return sorted_results

    # =========================================================================
    # MORK RANKING
    # =========================================================================

    def _rank_by_mork(self, query_concept: str,
                      candidates: List[str]) -> List[Tuple[str, float]]:
        """Get ontological ranking from MORK"""
        return self.mork.rank_by_ontology(query_concept, candidates)

    # =========================================================================
    # GRAPH RANKING
    # =========================================================================

    def _rank_by_graph(self, query_node: str, candidates: List[str],
                       edge_types: List[EdgeType] = None) -> List[Tuple[str, float]]:
        """Get graph-based ranking from Memory Graph"""
        return self.graph.rank_by_connectivity(query_node, candidates, edge_types)

    # =========================================================================
    # MILVUS RANKING
    # =========================================================================

    def _rank_by_milvus(self, collection: str, query_data: Dict[str, Any],
                        candidates: List[str]) -> List[Tuple[str, float]]:
        """Get vector similarity ranking from Milvus"""
        return self.milvus.rank_by_vector_similarity(collection, query_data, candidates)

    # =========================================================================
    # V36 QUERY METHODS
    # =========================================================================

    def find_analogous_latents(self, latent_data: Dict[str, Any],
                                candidates: List[str] = None,
                                target_domain: str = None,
                                top_k: int = 10) -> List[RRFResult]:
        """
        Find analogous latents using three-way fusion.

        Args:
            latent_data: Data about the query latent
            candidates: Optional list of candidate IDs to rank
            target_domain: Optional domain filter
            top_k: Number of results to return

        Returns:
            Fused ranking of analogous latents
        """
        # Get candidates if not provided
        if candidates is None:
            # Get all latent nodes from graph
            latent_nodes = self.graph.get_nodes_by_type(
                self.graph.nodes.get(list(self.graph.nodes.keys())[0]).node_type
                if self.graph.nodes else None
            )
            from .memory_graph import NodeType
            latent_nodes = self.graph.get_nodes_by_type(NodeType.LATENT)
            candidates = [n.node_id for n in latent_nodes]

            # Filter by domain if specified
            if target_domain:
                candidates = [
                    c for c in candidates
                    if self.graph.get_node(c) and
                       self.graph.get_node(c).data.get('domain') == target_domain
                ]

        if not candidates:
            return []

        rankings = {}

        # MORK ranking - by functional role ontology
        role_type = latent_data.get('role_type', 'generic_latent')
        mork_concept = self.mork.map_v36_functional_role(role_type)
        if mork_concept:
            # Map candidates to their ontology concepts
            candidate_concepts = []
            for c in candidates:
                node = self.graph.get_node(c)
                if node:
                    c_role = node.data.get('role_type', 'generic_latent')
                    c_concept = self.mork.map_v36_functional_role(c_role)
                    if c_concept:
                        candidate_concepts.append(c)

            if candidate_concepts:
                rankings[RankingSource.MORK.value] = self._rank_by_mork(
                    mork_concept, candidate_concepts
                )

        # Graph ranking - by analogy edges and connectivity
        query_id = latent_data.get('node_id', f"query_{time.time()}")
        rankings[RankingSource.GRAPH.value] = self._rank_by_graph(
            query_id, candidates, [EdgeType.ANALOGOUS_TO, EdgeType.HAS_ROLE]
        )

        # Milvus ranking - by vector similarity
        rankings[RankingSource.MILVUS.value] = self._rank_by_milvus(
            "latent", latent_data, candidates
        )

        # Fuse rankings
        results = self._fuse_rankings(rankings)

        return results[:top_k]

    def find_similar_scms(self, scm_data: Dict[str, Any],
                          candidates: List[str] = None,
                          top_k: int = 10) -> List[RRFResult]:
        """
        Find similar SCMs using three-way fusion.
        """
        from .memory_graph import NodeType

        if candidates is None:
            scm_nodes = self.graph.get_nodes_by_type(NodeType.SCM)
            candidates = [n.node_id for n in scm_nodes]

        if not candidates:
            return []

        rankings = {}

        # MORK ranking - not directly applicable to SCMs, use domain mixture
        # Skip MORK for SCM queries

        # Graph ranking
        query_id = scm_data.get('scm_id', f"query_{time.time()}")
        rankings[RankingSource.GRAPH.value] = self._rank_by_graph(
            query_id, candidates, [EdgeType.BLENDS_WITH, EdgeType.BELONGS_TO]
        )

        # Milvus ranking
        rankings[RankingSource.MILVUS.value] = self._rank_by_milvus(
            "scm", scm_data, candidates
        )

        # Adjust weights (no MORK for SCMs)
        weights = {
            RankingSource.GRAPH.value: 0.5,
            RankingSource.MILVUS.value: 0.5
        }

        results = self._fuse_rankings(rankings, weights)
        return results[:top_k]

    def find_relevant_constraints(self, theory_data: Dict[str, Any],
                                   top_k: int = 10) -> List[RRFResult]:
        """
        Find constraints relevant to a theory/SCM.
        """
        from .memory_graph import NodeType

        constraint_nodes = self.graph.get_nodes_by_type(NodeType.CONSTRAINT)
        candidates = [n.node_id for n in constraint_nodes]

        if not candidates:
            return []

        rankings = {}

        # MORK ranking - by constraint hierarchy
        rankings[RankingSource.MORK.value] = []
        for c in candidates:
            # Get constraint severity from MORK
            node = self.mork.get_node(c.replace("constraint_", ""))
            if node:
                severity_score = {"FATAL": 1.0, "STRONG": 0.8, "MODERATE": 0.5, "WEAK": 0.2}
                score = severity_score.get(node.properties.get("severity", "MODERATE"), 0.5)
                rankings[RankingSource.MORK.value].append((c, score))

        if not rankings[RankingSource.MORK.value]:
            rankings[RankingSource.MORK.value] = [(c, 0.5) for c in candidates]

        # Graph ranking - by violation edges
        query_id = theory_data.get('theory_id', f"query_{time.time()}")
        rankings[RankingSource.GRAPH.value] = self._rank_by_graph(
            query_id, candidates, [EdgeType.VIOLATES]
        )

        # Milvus not applicable for constraints
        rankings[RankingSource.MILVUS.value] = [(c, 0.5) for c in candidates]

        # Adjust weights
        weights = {
            RankingSource.MORK.value: 0.5,
            RankingSource.GRAPH.value: 0.4,
            RankingSource.MILVUS.value: 0.1
        }

        results = self._fuse_rankings(rankings, weights)
        return results[:top_k]

    def find_similar_mechanisms(self, observation_data: Dict[str, Any],
                                 candidates: List[str] = None,
                                 top_k: int = 10) -> List[RRFResult]:
        """
        Find observation mechanisms similar to the query.
        Useful for MechanismDiscoveryEngine to find known mechanisms
        before attempting symbolic regression.
        """
        from .memory_graph import NodeType

        if candidates is None:
            mech_nodes = self.graph.get_nodes_by_type(NodeType.MECHANISM)
            candidates = [n.node_id for n in mech_nodes]

        if not candidates:
            return []

        rankings = {}

        # MORK ranking - by function family ontology
        family = observation_data.get('function_family', 'linear')
        family_concept_map = {
            'linear': 'LINEAR', 'polynomial': 'POLYNOMIAL',
            'exponential': 'EXPONENTIAL', 'multiplicative': 'MULTIPLICATIVE',
            'logarithmic': 'LOGARITHMIC', 'blended': 'BLENDED'
        }
        query_concept = family_concept_map.get(family.lower())

        if query_concept and query_concept in self.mork.nodes:
            rankings[RankingSource.MORK.value] = self._rank_by_mork(
                query_concept, candidates
            )
        else:
            rankings[RankingSource.MORK.value] = [(c, 0.5) for c in candidates]

        # Graph ranking
        query_id = observation_data.get('obs_id', f"query_{time.time()}")
        rankings[RankingSource.GRAPH.value] = self._rank_by_graph(
            query_id, candidates, [EdgeType.OBSERVES]
        )

        # Milvus ranking
        rankings[RankingSource.MILVUS.value] = self._rank_by_milvus(
            "observation", observation_data, candidates
        )

        results = self._fuse_rankings(rankings)
        return results[:top_k]

    # =========================================================================
    # GENERIC QUERY
    # =========================================================================

    def query(self, query_type: str, query_data: Dict[str, Any],
              candidates: List[str] = None, top_k: int = 10,
              custom_weights: Dict[str, float] = None) -> List[RRFResult]:
        """
        Generic query interface.

        Args:
            query_type: Type of query (latent, scm, constraint, mechanism)
            query_data: Query entity data
            candidates: Optional candidate list
            top_k: Number of results
            custom_weights: Override default weights

        Returns:
            Fused ranking results
        """
        if query_type == "latent":
            return self.find_analogous_latents(query_data, candidates, top_k=top_k)
        elif query_type == "scm":
            return self.find_similar_scms(query_data, candidates, top_k=top_k)
        elif query_type == "constraint":
            return self.find_relevant_constraints(query_data, top_k=top_k)
        elif query_type == "mechanism":
            return self.find_similar_mechanisms(query_data, candidates, top_k=top_k)
        else:
            raise ValueError(f"Unknown query type: {query_type}")

    # =========================================================================
    # UTILITIES
    # =========================================================================

    def explain_ranking(self, result: RRFResult) -> str:
        """Generate human-readable explanation of a ranking result"""
        lines = [f"Entity: {result.entity_id}"]
        lines.append(f"Fused Score: {result.fused_score:.4f}")
        lines.append("\nSource Contributions:")

        for source in [RankingSource.MORK, RankingSource.GRAPH, RankingSource.MILVUS]:
            source_name = source.value
            if source_name in result.source_ranks:
                rank = result.source_ranks[source_name]
                score = result.source_scores.get(source_name, 0.0)
                weight = self.config.weights.get(source_name, 1.0)
                rrf_contrib = weight * self._rrf_score(rank)
                lines.append(f"  {source_name}: rank={rank}, score={score:.4f}, "
                           f"weight={weight:.2f}, RRF_contrib={rrf_contrib:.4f}")
            else:
                lines.append(f"  {source_name}: not ranked")

        return "\n".join(lines)

    def stats(self) -> Dict[str, Any]:
        """Get RRF system statistics"""
        return {
            "config": {
                "k": self.config.k,
                "weights": self.config.weights,
                "min_sources": self.config.min_sources
            },
            "sources": {
                "mork": {
                    "num_concepts": len(self.mork.nodes),
                    "num_relations": len(self.mork.relations)
                },
                "graph": self.graph.stats(),
                "milvus": self.milvus.stats()
            }
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ThreeWayRRF',
    'RRFResult',
    'RankingConfig',
    'RankingSource'
]



def utility_function_17(*args, **kwargs):
    """Utility function 17."""
    return None



# Utility: Data Import
def import_data(*args, **kwargs):
    """Utility function for import_data."""
    return None
