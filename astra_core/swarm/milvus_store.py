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
Milvus Vector Store: Vector Similarity Search for V36 Embeddings

Provides vector similarity search over V36 embeddings, enabling fast retrieval
of similar SCMs, analogous latents, and related symbolic forms.

Supports two backends:
- In-memory (default): Pure Python implementation for development/testing
- Milvus: Real Milvus server connection for production

Integration with V36:
- Embeddings for SCMs, latents, symbolic equations, observations
- Enhances CrossDomainAnalogyEngine with vector similarity
- Speeds up MechanismDiscoveryEngine by finding similar mechanisms

Date: 2025-11-27
Version: 37.0
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from collections import defaultdict


class VectorBackend(Enum):
    """Available vector store backends"""
    MEMORY = "memory"
    MILVUS = "milvus"


class DistanceMetric(Enum):
    """Distance metrics for similarity search"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"


@dataclass
class VectorRecord:
    """A vector record in the store"""
    vector_id: str
    vector: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if isinstance(self.vector, list):
            self.vector = np.array(self.vector, dtype=np.float32)


@dataclass
class SearchResult:
    """Result from a similarity search"""
    vector_id: str
    score: float
    distance: float
    metadata: Dict[str, Any]


class InMemoryVectorIndex:
    """
    In-memory vector index with brute-force search.
    Used as default backend for development/testing.
    """

    def __init__(self, dimension: int, metric: DistanceMetric = DistanceMetric.COSINE):
        self.dimension = dimension
        self.metric = metric
        self.vectors: Dict[str, VectorRecord] = {}

    def insert(self, record: VectorRecord):
        """Insert a vector record"""
        if len(record.vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(record.vector)}")
        self.vectors[record.vector_id] = record

    def delete(self, vector_id: str) -> bool:
        """Delete a vector record"""
        if vector_id in self.vectors:
            del self.vectors[vector_id]
            return True
        return False

    def search(self, query_vector: np.ndarray, top_k: int = 10,
               filter_fn: Optional[callable] = None) -> List[SearchResult]:
        """Search for similar vectors"""
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query dimension mismatch: expected {self.dimension}, got {len(query_vector)}")

        results = []
        query_vector = np.array(query_vector, dtype=np.float32)

        for vid, record in self.vectors.items():
            if filter_fn and not filter_fn(record.metadata):
                continue

            distance = self._compute_distance(query_vector, record.vector)
            score = self._distance_to_score(distance)

            results.append(SearchResult(
                vector_id=vid,
                score=score,
                distance=distance,
                metadata=record.metadata
            ))

        # Sort by score (higher is better)
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _compute_distance(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Compute distance between two vectors"""
        if self.metric == DistanceMetric.COSINE:
            norm_a = np.linalg.norm(vec_a)
            norm_b = np.linalg.norm(vec_b)
            if norm_a == 0 or norm_b == 0:
                return 1.0
            return 1.0 - np.dot(vec_a, vec_b) / (norm_a * norm_b)

        elif self.metric == DistanceMetric.EUCLIDEAN:
            return np.linalg.norm(vec_a - vec_b)

        elif self.metric == DistanceMetric.DOT_PRODUCT:
            return -np.dot(vec_a, vec_b)  # Negative for sorting

        return 1.0

    def _distance_to_score(self, distance: float) -> float:
        """Convert distance to similarity score [0, 1]"""
        if self.metric == DistanceMetric.COSINE:
            return 1.0 - distance
        elif self.metric == DistanceMetric.EUCLIDEAN:
            return 1.0 / (1.0 + distance)
        elif self.metric == DistanceMetric.DOT_PRODUCT:
            return -distance  # Already negated
        return 0.0

    def count(self) -> int:
        """Get number of vectors in index"""
        return len(self.vectors)


class MilvusVectorStore:
    """
    Vector store for V36 embeddings.

    Provides:
    - Multiple collections for different entity types
    - V36-specific embedding functions
    - Similarity search with metadata filtering
    - Backend abstraction (memory or real Milvus)
    """

    # Embedding dimensions for different entity types
    DIMENSIONS = {
        "scm": 128,           # SCM structure embedding
        "latent": 64,         # Latent variable embedding
        "symbolic": 48,       # Symbolic equation embedding
        "observation": 64,    # Observation function embedding
        "functional_role": 32 # Functional role embedding
    }

    def __init__(self, backend: VectorBackend = VectorBackend.MEMORY,
                 milvus_host: str = "localhost", milvus_port: int = 19530):
        self.backend = backend
        self.collections: Dict[str, InMemoryVectorIndex] = {}

        if backend == VectorBackend.MEMORY:
            self._init_memory_backend()
        elif backend == VectorBackend.MILVUS:
            self._init_milvus_backend(milvus_host, milvus_port)

    def _init_memory_backend(self):
        """Initialize in-memory collections"""
        for name, dim in self.DIMENSIONS.items():
            self.collections[name] = InMemoryVectorIndex(dim, DistanceMetric.COSINE)

    def _init_milvus_backend(self, host: str, port: int):
        """Initialize Milvus connection (placeholder for real implementation)"""
        # For now, fall back to memory backend
        # Real implementation would use: from pymilvus import connections, Collection
        print(f"Note: Milvus backend requested but falling back to memory (host={host}, port={port})")
        self._init_memory_backend()

    # =========================================================================
    # EMBEDDING FUNCTIONS
    # =========================================================================

    def embed_scm(self, scm_data: Dict[str, Any]) -> np.ndarray:
        """
        Embed an SCM into a vector.

        Features:
        - Number of latents (normalized)
        - Number of observations (normalized)
        - Domain mixture proportions
        - Timescale distribution statistics
        - Structural complexity
        """
        dim = self.DIMENSIONS["scm"]
        embedding = np.zeros(dim, dtype=np.float32)

        # Basic counts (normalized)
        n_latents = len(scm_data.get('latents', {}))
        n_obs = len(scm_data.get('observations', {}))
        embedding[0] = n_latents / 10.0  # Normalize
        embedding[1] = n_obs / 10.0

        # Domain mixture
        mixture = scm_data.get('domain_mixture', {})
        embedding[2] = mixture.get('CLD', 0.0)
        embedding[3] = mixture.get('D1', 0.0)
        embedding[4] = mixture.get('D2', 0.0)

        # Functional roles distribution
        roles = scm_data.get('functional_roles', {})
        role_counts = defaultdict(int)
        for role_data in roles.values():
            if hasattr(role_data, 'role_type'):
                role_counts[role_data.role_type] += 1
            elif isinstance(role_data, dict):
                role_counts[role_data.get('role_type', 'unknown')] += 1

        role_types = ['slow_driver', 'fast_responder', 'mid_mediator', 'nested_mediator', 'regime_detector']
        for i, rt in enumerate(role_types):
            embedding[5 + i] = role_counts.get(rt, 0) / max(n_latents, 1)

        # Time series length
        embedding[10] = scm_data.get('T', 0) / 5000.0

        # Fill remaining with hash-based features for uniqueness
        data_str = json.dumps(scm_data, sort_keys=True, default=str)
        hash_val = hash(data_str)
        for i in range(11, dim):
            embedding[i] = ((hash_val >> (i % 32)) & 0xFF) / 255.0
            hash_val = (hash_val * 31) & 0xFFFFFFFF

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def embed_latent(self, latent_data: Dict[str, Any]) -> np.ndarray:
        """
        Embed a latent variable into a vector.

        Features:
        - Functional role encoding
        - Timescale category
        - Causal position
        - Regime sensitivity
        - AR coefficient statistics
        """
        dim = self.DIMENSIONS["latent"]
        embedding = np.zeros(dim, dtype=np.float32)

        # Role type one-hot (first 10 dimensions)
        role_mapping = {
            'slow_driver': 0, 'fast_responder': 1, 'mid_mediator': 2,
            'nested_mediator': 3, 'regime_detector': 4, 'transmission_driver': 5,
            'behaviour_moderator': 6, 'macro_sentiment': 7, 'policy_pressure': 8,
            'generic_latent': 9
        }
        role_type = latent_data.get('role_type', 'generic_latent')
        if role_type in role_mapping:
            embedding[role_mapping[role_type]] = 1.0

        # Timescale category
        timescale_map = {'slow': 0.9, 'mid': 0.5, 'fast': 0.1}
        embedding[10] = timescale_map.get(latent_data.get('timescale_category', 'mid'), 0.5)

        # Causal position
        position_map = {'driver': 0.0, 'mediator': 0.5, 'outcome': 1.0}
        embedding[11] = position_map.get(latent_data.get('causal_position', 'mediator'), 0.5)

        # Regime sensitivity
        embedding[12] = latent_data.get('regime_sensitivity', 0.0)

        # Intervention sensitivity
        embedding[13] = latent_data.get('intervention_sensitivity', 0.5)

        # AR coefficient if available
        embedding[14] = latent_data.get('ar_coefficient', 0.9)

        # Domain encoding
        domain = latent_data.get('domain', 'CLD')
        domain_map = {'CLD': [1, 0, 0], 'D1': [0, 1, 0], 'D2': [0, 0, 1]}
        embedding[15:18] = domain_map.get(domain, [0.33, 0.33, 0.33])

        # Fill remaining dimensions
        for i in range(18, dim):
            embedding[i] = np.random.uniform(0, 0.1)

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def embed_symbolic_equation(self, symbolic_data: Dict[str, Any]) -> np.ndarray:
        """
        Embed a symbolic equation into a vector.

        Features:
        - Template type encoding
        - Parameter values (normalized)
        - Complexity score
        """
        dim = self.DIMENSIONS["symbolic"]
        embedding = np.zeros(dim, dtype=np.float32)

        # Template one-hot (first 8 dimensions)
        template_mapping = {
            'STABLE_AUTOREGRESSIVE': 0, 'RESPONSIVE_AUTOREGRESSIVE': 1,
            'UNSTABLE_AUTOREGRESSIVE': 2, 'DELAYED_RESPONSE': 3,
            'NONLINEAR_EXPONENTIAL': 4, 'NONLINEAR_MULTIPLICATIVE': 5,
            'REGIME_DEPENDENT': 6, 'HYBRID_BLENDED': 7
        }

        template = symbolic_data.get('template', '')
        if hasattr(template, 'value'):
            template = template.value
        template = str(template).upper().replace(' ', '_')

        if template in template_mapping:
            embedding[template_mapping[template]] = 1.0

        # Parameter encodings
        params = symbolic_data.get('parameters', {})
        persistence_map = {'VERY_HIGH': 0.95, 'HIGH': 0.8, 'MODERATE': 0.5, 'LOW': 0.2}
        embedding[8] = persistence_map.get(params.get('persistence', 'MODERATE'), 0.5)

        forcing_map = {'STRONG': 0.9, 'MODERATE': 0.5, 'WEAK': 0.1}
        embedding[9] = forcing_map.get(params.get('forcing', 'MODERATE'), 0.5)

        noise_map = {'HIGH': 0.9, 'MODERATE': 0.5, 'LOW': 0.1}
        embedding[10] = noise_map.get(params.get('noise', 'MODERATE'), 0.5)

        # Canonical form hash for uniqueness
        canonical = symbolic_data.get('canonical_form', '')
        hash_val = hash(canonical)
        for i in range(11, dim):
            embedding[i] = ((hash_val >> (i % 32)) & 0xFF) / 255.0

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def embed_observation(self, observation_data: Dict[str, Any]) -> np.ndarray:
        """
        Embed an observation function into a vector.

        Features:
        - Function family encoding
        - Delay characteristics
        - Nonlinearity measures
        """
        dim = self.DIMENSIONS["observation"]
        embedding = np.zeros(dim, dtype=np.float32)

        # Function family one-hot
        family_mapping = {
            'linear': 0, 'polynomial': 1, 'exponential': 2,
            'multiplicative': 3, 'logarithmic': 4, 'trigonometric': 5,
            'blended': 6, 'novel': 7
        }
        family = observation_data.get('function_family', 'linear')
        if family in family_mapping:
            embedding[family_mapping[family]] = 1.0

        # Delay encoding
        delay = observation_data.get('delay', 0)
        embedding[8] = min(delay / 50.0, 1.0)  # Normalize delay

        # Complexity
        embedding[9] = observation_data.get('complexity', 1) / 10.0

        # Is novel?
        embedding[10] = 1.0 if observation_data.get('is_novel', False) else 0.0

        # Fill remaining
        for i in range(11, dim):
            embedding[i] = np.random.uniform(0, 0.1)

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def embed_functional_role(self, role_data: Dict[str, Any]) -> np.ndarray:
        """
        Embed a functional role into a vector.
        Compact embedding for fast role similarity search.
        """
        dim = self.DIMENSIONS["functional_role"]
        embedding = np.zeros(dim, dtype=np.float32)

        # Role type one-hot (first 10 dimensions)
        role_mapping = {
            'slow_driver': 0, 'fast_responder': 1, 'mid_mediator': 2,
            'nested_mediator': 3, 'regime_detector': 4, 'transmission_driver': 5,
            'behaviour_moderator': 6, 'macro_sentiment': 7, 'policy_pressure': 8,
            'generic_latent': 9
        }
        role_type = role_data.get('role_type', 'generic_latent')
        if role_type in role_mapping:
            embedding[role_mapping[role_type]] = 1.0

        # Continuous features
        timescale_map = {'slow': 0.9, 'mid': 0.5, 'fast': 0.1}
        embedding[10] = timescale_map.get(role_data.get('timescale_category', 'mid'), 0.5)

        position_map = {'driver': 0.0, 'mediator': 0.5, 'outcome': 1.0}
        embedding[11] = position_map.get(role_data.get('causal_position', 'mediator'), 0.5)

        embedding[12] = role_data.get('regime_sensitivity', 0.0)
        embedding[13] = role_data.get('intervention_sensitivity', 0.5)

        # Domain encoding
        domain_scope = role_data.get('domain_scope', ['ALL'])
        if 'CLD' in domain_scope or 'ALL' in domain_scope:
            embedding[14] = 1.0
        if 'D1' in domain_scope or 'ALL' in domain_scope:
            embedding[15] = 1.0
        if 'D2' in domain_scope or 'ALL' in domain_scope:
            embedding[16] = 1.0

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    def insert(self, collection_name: str, entity_id: str,
               entity_data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Insert an entity into a collection with automatic embedding"""
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")

        # Generate embedding based on collection type
        embed_fn = {
            "scm": self.embed_scm,
            "latent": self.embed_latent,
            "symbolic": self.embed_symbolic_equation,
            "observation": self.embed_observation,
            "functional_role": self.embed_functional_role
        }.get(collection_name)

        if not embed_fn:
            raise ValueError(f"No embedding function for collection: {collection_name}")

        embedding = embed_fn(entity_data)

        record = VectorRecord(
            vector_id=entity_id,
            vector=embedding,
            metadata={**(metadata or {}), "entity_data": entity_data}
        )

        self.collections[collection_name].insert(record)

    def insert_raw(self, collection_name: str, vector_id: str,
                   vector: np.ndarray, metadata: Dict[str, Any] = None):
        """Insert a raw vector (no automatic embedding)"""
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")

        record = VectorRecord(
            vector_id=vector_id,
            vector=vector,
            metadata=metadata or {}
        )

        self.collections[collection_name].insert(record)

    def delete(self, collection_name: str, entity_id: str) -> bool:
        """Delete an entity from a collection"""
        if collection_name not in self.collections:
            return False
        return self.collections[collection_name].delete(entity_id)

    def search(self, collection_name: str, query_data: Dict[str, Any],
               top_k: int = 10, filter_fn: Optional[callable] = None) -> List[SearchResult]:
        """Search for similar entities using automatic embedding"""
        if collection_name not in self.collections:
            return []

        embed_fn = {
            "scm": self.embed_scm,
            "latent": self.embed_latent,
            "symbolic": self.embed_symbolic_equation,
            "observation": self.embed_observation,
            "functional_role": self.embed_functional_role
        }.get(collection_name)

        if not embed_fn:
            return []

        query_vector = embed_fn(query_data)
        return self.collections[collection_name].search(query_vector, top_k, filter_fn)

    def search_raw(self, collection_name: str, query_vector: np.ndarray,
                   top_k: int = 10, filter_fn: Optional[callable] = None) -> List[SearchResult]:
        """Search using a raw vector"""
        if collection_name not in self.collections:
            return []
        return self.collections[collection_name].search(query_vector, top_k, filter_fn)

    # =========================================================================
    # V36 INTEGRATION
    # =========================================================================

    def find_similar_scms(self, scm_data: Dict[str, Any], top_k: int = 5) -> List[SearchResult]:
        """Find SCMs similar to the query SCM"""
        return self.search("scm", scm_data, top_k)

    def find_analogous_latents(self, latent_data: Dict[str, Any],
                                target_domain: Optional[str] = None,
                                top_k: int = 5) -> List[SearchResult]:
        """Find latents analogous to the query latent, optionally filtered by domain"""
        filter_fn = None
        if target_domain:
            filter_fn = lambda m: m.get("entity_data", {}).get("domain") == target_domain

        return self.search("latent", latent_data, top_k, filter_fn)

    def find_similar_mechanisms(self, observation_data: Dict[str, Any],
                                 top_k: int = 5) -> List[SearchResult]:
        """Find observation mechanisms similar to the query"""
        return self.search("observation", observation_data, top_k)

    def rank_by_vector_similarity(self, collection_name: str,
                                   query_data: Dict[str, Any],
                                   candidates: List[str]) -> List[Tuple[str, float]]:
        """
        Rank specific candidates by vector similarity.
        Used by RRF for vector-based ranking.
        """
        if collection_name not in self.collections:
            return [(c, 0.0) for c in candidates]

        embed_fn = {
            "scm": self.embed_scm,
            "latent": self.embed_latent,
            "symbolic": self.embed_symbolic_equation,
            "observation": self.embed_observation,
            "functional_role": self.embed_functional_role
        }.get(collection_name)

        if not embed_fn:
            return [(c, 0.0) for c in candidates]

        query_vector = embed_fn(query_data)
        collection = self.collections[collection_name]

        rankings = []
        for candidate_id in candidates:
            if candidate_id in collection.vectors:
                record = collection.vectors[candidate_id]
                distance = collection._compute_distance(query_vector, record.vector)
                score = collection._distance_to_score(distance)
                rankings.append((candidate_id, score))
            else:
                rankings.append((candidate_id, 0.0))

        return sorted(rankings, key=lambda x: x[1], reverse=True)

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            "backend": self.backend.value,
            "collections": {
                name: {
                    "count": idx.count(),
                    "dimension": idx.dimension
                }
                for name, idx in self.collections.items()
            }
        }

    def save(self, filepath: str):
        """Save vector store to file"""
        data = {
            "backend": self.backend.value,
            "collections": {}
        }

        for name, index in self.collections.items():
            data["collections"][name] = {
                "dimension": index.dimension,
                "metric": index.metric.value,
                "vectors": {
                    vid: {
                        "vector": record.vector.tolist(),
                        "metadata": record.metadata,
                        "created_at": record.created_at
                    }
                    for vid, record in index.vectors.items()
                }
            }

        with open(filepath, 'w') as f:
            json.dump(data, f)

    @classmethod
    def load(cls, filepath: str) -> 'MilvusVectorStore':
        """Load vector store from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        store = cls(backend=VectorBackend(data["backend"]))

        for name, coll_data in data["collections"].items():
            if name in store.collections:
                index = store.collections[name]
                for vid, vdata in coll_data["vectors"].items():
                    record = VectorRecord(
                        vector_id=vid,
                        vector=np.array(vdata["vector"], dtype=np.float32),
                        metadata=vdata["metadata"],
                        created_at=vdata.get("created_at", time.time())
                    )
                    index.vectors[vid] = record

        return store


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'MilvusVectorStore',
    'VectorBackend',
    'DistanceMetric',
    'VectorRecord',
    'SearchResult',
    'InMemoryVectorIndex'
]
