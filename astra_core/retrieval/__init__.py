"""
Agentic Retrieval Module for STAN
==================================

Implements advanced parallel retrieval patterns from "Building the 14 Key Pillars of Agentic AI":

Priority 1: Parallel Hybrid Search Fusion - Combine vector (semantic) and keyword (lexical) search
Priority 2: Parallel Context Pre-processing - Filter documents in parallel for relevance
Priority 3: Sharded & Scattered Retrieval - Parallel search across domain-scoped indexes
Priority 4: Parallel Query Expansion - Multi-strategy query generation for maximum recall
Priority 5: Redundant Execution (in intelligence/) - Fault-tolerant parallel execution

Expected Improvements:
- Accuracy: +25-50% on retrieval-augmented tasks
- Cost: -90% token usage for final generation
- Latency: -28% retrieval, -73% generation
- Reliability: +33% success rate for critical operations
- Scalability: Linear vs monolithic degradation

Version: 1.0
Date: 2026-01-04
"""

from .hybrid_search import (
    HybridRetriever,
    TfidfRetriever,
    VectorRetriever,
    HybridSearchResult,
    create_hybrid_retriever,
    Document,
)

from .context_distiller import (
    ContextDistiller,
    RelevancyCheck,
    DistillationResult,
    create_context_distiller,
    SimpleKeywordChecker,
)

from .sharded_retrieval import (
    ShardedRetriever,
    DomainShard,
    ShardedRetrievalResult,
    ShardStrategy,
    ShardSelector,
    create_sharded_retriever,
)

from .query_expander import (
    QueryExpander,
    ParallelQueryExpander,
    RuleBasedExpander,
    ExpandedQueries,
    QueryExpansionResult,
    create_query_expander,
)

from .parallel_rag import (
    ParallelRAGOrchestrator,
    ParallelRAGConfig,
    ParallelRAGResult,
    RetrievalMode,
    create_parallel_rag,
)

__all__ = [
    # Priority 1: Hybrid Search
    'HybridRetriever',
    'TfidfRetriever',
    'VectorRetriever',
    'HybridSearchResult',
    'create_hybrid_retriever',
    'Document',

    # Priority 2: Context Distillation
    'ContextDistiller',
    'RelevancyCheck',
    'DistillationResult',
    'create_context_distiller',
    'SimpleKeywordChecker',

    # Priority 3: Sharded Retrieval
    'ShardedRetriever',
    'DomainShard',
    'ShardedRetrievalResult',
    'ShardStrategy',
    'ShardSelector',
    'create_sharded_retriever',

    # Priority 4: Query Expansion
    'QueryExpander',
    'ParallelQueryExpander',
    'RuleBasedExpander',
    'ExpandedQueries',
    'QueryExpansionResult',
    'create_query_expander',

    # Unified Parallel RAG
    'ParallelRAGOrchestrator',
    'ParallelRAGConfig',
    'ParallelRAGResult',
    'RetrievalMode',
    'create_parallel_rag',
]
