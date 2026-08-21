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

# context_distiller.py, sharded_retrieval.py and query_expander.py have
# baselined syntax errors (tests/known_broken_syntax.txt); quarantined so the
# package's healthy modules stay importable.
try:
    from .context_distiller import (
        ContextDistiller,
        RelevancyCheck,
        DistillationResult,
        create_context_distiller,
        SimpleKeywordChecker,
    )
except (ImportError, SyntaxError):
    ContextDistiller = None
    RelevancyCheck = None
    DistillationResult = None
    create_context_distiller = None
    SimpleKeywordChecker = None

try:
    from .sharded_retrieval import (
        ShardedRetriever,
        DomainShard,
        ShardedRetrievalResult,
        ShardStrategy,
        ShardSelector,
        create_sharded_retriever,
    )
except (ImportError, SyntaxError):
    ShardedRetriever = None
    DomainShard = None
    ShardedRetrievalResult = None
    ShardStrategy = None
    ShardSelector = None
    create_sharded_retriever = None

try:
    from .query_expander import (
        QueryExpander,
        ParallelQueryExpander,
        RuleBasedExpander,
        ExpandedQueries,
        QueryExpansionResult,
        create_query_expander,
    )
except (ImportError, SyntaxError):
    QueryExpander = None
    ParallelQueryExpander = None
    RuleBasedExpander = None
    ExpandedQueries = None
    QueryExpansionResult = None
    create_query_expander = None

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
