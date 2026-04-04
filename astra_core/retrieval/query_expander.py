"""
Parallel Query Expansion (Priority 4)
=====================================

Multi-strategy query generation for maximum recall.

Problem Solved:
- Users rarely know precise keywords/jargon in specialized knowledge bases
- Simple query "make models bigger and faster" misses docs about "Mixture of Experts"
- Vocabulary mismatch causes poor retrieval

Benefits:
- 40-60% recall improvement for technical queries
- Bridges semantic gap between user language and domain terminology
- Parallel execution hides LLM latency

Based on: "Building the 14 Key Pillars of Agentic AI" - Pillar 10

Example Use:
    expander = QueryExpander()
    expanded = expander.expand("how to improve model performance")
    # Generates: hypothetical doc + sub-questions + keywords
    # Returns 7-9 query variations for parallel retrieval
"""

import time
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from abc import ABC, abstractmethod

from .hybrid_search import BaseRetriever, Document


@dataclass
class ExpandedQueries:
    """
    Multiple query variations for comprehensive retrieval.

    Contains diverse search strategies:
    - hypothetical_document: Semantic ideal answer
    - sub_questions: Decomposed specific questions
    - keywords: Exact domain terms
    """
    hypothetical_document: str
    sub_questions: List[str]
    keywords: List[str]

    def all_queries(self) -> List[str]:
        """Get all query variations for parallel retrieval."""
        return [self.hypothetical_document] + self.sub_questions + self.keywords


@dataclass
class QueryExpansionResult:
    """Result from query expansion with metrics."""
    original_query: str
    expanded_queries: ExpandedQueries
    all_queries: List[str]
    query_count: int
    execution_time: float
    strategy_breakdown: Dict[str, int] = field(default_factory=dict)


class QueryExpander(ABC):
    """Abstract base class for query expanders."""

    @abstractmethod
    def expand(self, query: str) -> ExpandedQueries:
        """Expand query into multiple variations."""
        pass


class RuleBasedExpander(QueryExpander):
    """
    Rule-based query expansion (no LLM required).

    Uses heuristics to generate:
    - Synonyms and related terms
    - Sub-question decomposition
    - Keyword extraction
    """

    def __init__(self):
        # Domain-specific term mappings
        self.term_mappings = {
            'ml': {
                'model': ['neural network', 'algorithm', 'classifier', 'predictor'],
                'performance': ['accuracy', 'f1 score', 'precision', 'recall', 'efficiency'],
                'improve': ['optimize', 'enhance', 'boost', 'increase', 'refine'],
                'big': ['large', 'scalable', 'high-capacity', 'massive', 'distributed'],
                'fast': ['efficient', 'optimized', 'low-latency', 'accelerated'],
            },
            'astronomy': {
                'star': ['stellar', 'sun', 'celestial body', 'main sequence'],
                'observe': ['detect', 'measure', 'image', 'survey'],
                'telescope': ['observatory', 'instrument', 'detector', 'array'],
            },
            'trading': {
                'profit': ['return', 'gain', 'alpha', 'excess return'],
                'risk': ['volatility', 'drawdown', 'variance', 'uncertainty'],
                'strategy': ['approach', 'method', 'system', 'algorithm'],
            }
        }

    def expand(self, query: str) -> ExpandedQueries:
        """Expand query using rules."""
        # Generate hypothetical document
        hypothetical = self._generate_hypothetical(query)

        # Generate sub-questions
        sub_questions = self._generate_sub_questions(query)

        # Extract keywords
        keywords = self._extract_keywords(query)

        return ExpandedQueries(
            hypothetical_document=hypothetical,
            sub_questions=sub_questions,
            keywords=keywords
        )

    def _generate_hypothetical(self, query: str) -> str:
        """Generate a hypothetical ideal answer."""
        # Convert question to statement format
        if query.startswith(('how', 'what', 'why', 'when', 'where', 'who')):
            # Remove question word and convert to declarative
            parts = query.split(maxsplit=1)
            if len(parts) > 1:
                core = parts[1].rstrip('?')
                return f"This document discusses methods and techniques for {core}."
        return f"This document addresses: {query}"

    def _generate_sub_questions(self, query: str) -> List[str]:
        """Decompose query into specific sub-questions."""
        sub_questions = []

        # Common patterns
        if 'how' in query.lower():
            # Add "what" version
            sub_questions.append(query.lower().replace('how', 'what'))

        if 'improve' in query.lower() or 'optimize' in query.lower():
            # Add technique-specific questions
            sub_questions.append(f"What techniques are available for {query.lower()}")
            sub_questions.append(f"What are best practices for {query.lower()}")

        if 'model' in query.lower() and 'performance' in query.lower():
            sub_questions.append("How to reduce training time")
            sub_questions.append("How to increase model accuracy")
            sub_questions.append("Mixture of Experts for model scaling")

        # Extract nouns and create specific questions
        words = query.lower().split()
        if 'model' in words:
            sub_questions.append("neural network optimization")
        if 'performance' in words:
            sub_questions.append("computational efficiency")

        return list(set(sub_questions))  # Deduplicate

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract key domain terms from query."""
        # Remove stop words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                    'to', 'of', 'in', 'on', 'at', 'for', 'with', 'by', 'from'}

        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        # Add synonyms from term mappings
        expanded = list(keywords)
        for domain, mappings in self.term_mappings.items():
            for term, synonyms in mappings.items():
                if term in keywords:
                    expanded.extend(synonyms[:2])  # Add top 2 synonyms

        return list(set(expanded))


class LLMQueryExpander(QueryExpander):
    """
    LLM-based query expansion for maximum quality.

    Uses structured output to force diverse query generation.
    In production, would use actual LLM API.
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model

    def expand(self, query: str) -> ExpandedQueries:
        """Expand query using LLM."""
        # For demo, fall back to rule-based
        # In production, would use LLM with structured output
        expander = RuleBasedExpander()
        return expander.expand(query)


class ParallelQueryExpander:
    """
    Parallel Query Expansion with Retrieval.

    Expands query into multiple variations, then executes parallel
    retrieval for all variations, fusing results.

    Architecture:
        1. Expand: Generate 7-9 query variations
        2. Scatter: Dispatch all queries in parallel
        3. Gather: Collect results from all queries
        4. Fusion: Combine and deduplicate results

    Benefits:
        - 40-60% recall improvement for technical queries
        - Bridges vocabulary mismatch gap
        - Parallel execution hides latency

    Example:
        ```python
        expander = ParallelQueryExpander(retriever)

        # User's vague query
        query = "how to make models bigger and faster"

        # Expands and retrieves comprehensive results
        result = expander.expand_and_retrieve(query)
        # Finds docs about "Mixture of Experts", "FlashAttention", etc.
        ```
    """

    def __init__(self,
                 retriever: BaseRetriever,
                 expander: QueryExpander = None,
                 k_per_query: int = 3,
                 max_workers: int = 5):
        """
        Initialize parallel query expander.

        Args:
            retriever: Base retriever for document lookup
            expander: Query expander (defaults to RuleBasedExpander)
            k_per_query: Documents to retrieve per query variation
            max_workers: Max parallel workers
        """
        self.retriever = retriever
        self.expander = expander or RuleBasedExpander()
        self.k_per_query = k_per_query
        self.max_workers = max_workers

    def expand_and_retrieve(self,
                           query: str,
                           k: int = None) -> QueryExpansionResult:
        """
        Expand query and retrieve documents in parallel.

        Args:
            query: Original user query
            k: Total results to return (None = k_per_query * num_queries)

        Returns:
            QueryExpansionResult with expanded queries and retrieved documents
        """
        start_time = time.time()

        # Step 1: Expand query
        expanded = self.expander.expand(query)
        all_queries = expanded.all_queries()

        # Step 2: Parallel retrieval for all queries
        all_docs = []
        query_times = {}

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(all_queries))) as executor:
            future_to_query = {
                executor.submit(self._timed_retrieve, q, self.k_per_query): q
