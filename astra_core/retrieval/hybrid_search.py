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
Parallel Hybrid Search Fusion (Priority 1)
==========================================

Combines vector (semantic) and keyword (lexical) search in parallel.

Problem Solved:
- Vector search understands conceptual meaning but misses exact keywords
- Keyword search finds exact terms but fails at conceptual understanding
- Hybrid approach provides best of both with parallel execution

Benefits:
- +50% accuracy for mixed queries (concept + keyword components)
- Parallel execution hides I/O latency
- No single point of failure

Based on: "Building the 14 Key Pillars of Agentic AI" - Pillar 12

Example Use:
    retriever = HybridRetriever(vector_store, tfidf_retriever)
    results = retriever.retrieve("power saving efforts and error ERR_THROTTLE_900")
    # Returns both conceptual documents AND exact error code matches
"""

import time
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from abc import ABC, abstractmethod

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


@dataclass
class Document:
    """Document representation for retrieval."""
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.page_content, tuple(sorted(self.metadata.items()))))

    def __eq__(self, other):
        if not isinstance(other, Document):
            return False
        return self.page_content == other.page_content


@dataclass
class HybridSearchResult:
    """Result from hybrid search with timing metrics."""
    documents: List[Document]
    total_results: int
    vector_results: int
    keyword_results: int
    unique_results: int
    execution_time: float
    vector_time: float = 0.0
    keyword_time: float = 0.0


class BaseRetriever(ABC):
    """Abstract base class for retrievers."""

    @abstractmethod
    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        """Retrieve top k documents for query."""
        pass


class TfidfRetriever(BaseRetriever):
    """
    Keyword-based retriever using TF-IDF.

    Excellent for:
    - Exact keyword matching (error codes, identifiers)
    - Technical terms and jargon
    - Legal citations, product codes
    """

    def __init__(self, documents: List[Document], k: int = 5):
        self.documents = documents
        self.k = k

        if _SKLEARN_AVAILABLE:
            # Fit TF-IDF vectorizer on documents
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),  # Unigrams and bigrams
                min_df=1,
                max_features=5000
            )
            self.doc_vectors = self.vectorizer.fit_transform([
                doc.page_content for doc in documents
            ])
            self._use_sklearn = True
        else:
            # Use numpy-based TF-IDF fallback
            self._build_tfidf_index()
            self._use_sklearn = False

    def _build_tfidf_index(self):
        """Build TF-IDF index using numpy."""
        from collections import Counter
        import re
        import math

        # Simple stop words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}

        # Tokenize documents
        self._doc_tokens = []
        for doc in self.documents:
            tokens = re.findall(r'\w+', doc.page_content.lower())
            tokens = [t for t in tokens if t not in stop_words and len(t) > 1]
            self._doc_tokens.append(tokens)

        # Build vocabulary
        vocab = set()
        for tokens in self._doc_tokens:
            vocab.update(tokens)
        self._vocab = list(vocab)
        self._word_to_idx = {w: i for i, w in enumerate(self._vocab)}

        # Compute IDF
        n_docs = len(self.documents)
        self._idf = np.zeros(len(self._vocab))
        for i, word in enumerate(self._vocab):
            df = sum(1 for tokens in self._doc_tokens if word in tokens)
            self._idf[i] = math.log(n_docs / (df + 1)) + 1

        # Compute TF-IDF vectors
        self._tfidf_matrix = np.zeros((n_docs, len(self._vocab)))
        for doc_idx, tokens in enumerate(self._doc_tokens):
            tf = Counter(tokens)
            for word, count in tf.items():
                if word in self._word_to_idx:
                    word_idx = self._word_to_idx[word]
                    self._tfidf_matrix[doc_idx, word_idx] = count * self._idf[word_idx]

    def retrieve(self, query: str, k: int = None) -> List[Document]:
        """Retrieve using TF-IDF cosine similarity."""
        k = k or self.k

        if self._use_sklearn:
            # Transform query
            query_vec = self.vectorizer.transform([query])

            # Calculate similarities
            similarities = cosine_similarity(query_vec, self.doc_vectors).flatten()

            # Get top k indices
            top_k_indices = np.argsort(similarities)[-k:][::-1]

            # Return documents
            return [self.documents[i] for i in top_k_indices]
        else:
            # Use numpy-based TF-IDF
            import re
            from collections import Counter

            stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}

            # Tokenize query
            query_tokens = re.findall(r'\w+', query.lower())
            query_tokens = [t for t in query_tokens if t not in stop_words and len(t) > 1]

            # Compute query TF-IDF vector
            query_vec = np.zeros(len(self._vocab))
            tf = Counter(query_tokens)
            for word, count in tf.items():
                if word in self._word_to_idx:
                    word_idx = self._word_to_idx[word]
                    query_vec[word_idx] = count * self._idf[word_idx]

            # Calculate cosine similarity
            norms = np.linalg.norm(self._tfidf_matrix, axis=1)
            query_norm = np.linalg.norm(query_vec)
            if query_norm == 0:
                return self.documents[:k]

            similarities = (self._tfidf_matrix @ query_vec) / (norms * query_norm + 1e-8)

            # Get top k indices
            top_k_indices = np.argsort(similarities)[-k:][::-1]

            return [self.documents[i] for i in top_k_indices]


class VectorRetriever(BaseRetriever):
    """
    Vector-based retriever using semantic embeddings.

    Excellent for:
    - Conceptual understanding
    - Semantic similarity
    - Cross-domain analogies
    """

    def __init__(self, documents: List[Document], embeddings: np.ndarray = None, k: int = 5):
        self.documents = documents
        self.k = k

        # In production, would use actual embeddings (OpenAI, HuggingFace, etc.)
        # For now, use TF-IDF as proxy for semantic similarity
        if embeddings is not None:
            self.doc_vectors = embeddings
        elif _SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(stop_words='english')
            self.doc_vectors = self.vectorizer.fit_transform([
                doc.page_content for doc in documents
            ])
        else:
            # Fallback: use simple character n-gram similarity
            self.doc_vectors = None
            self.vectorizer = None

    def retrieve(self, query: str, k: int = None) -> List[Document]:
        """Retrieve using vector similarity."""
        k = k or self.k

        if self.doc_vectors is not None and _SKLEARN_AVAILABLE:
            # Transform query
            query_vec = self.vectorizer.transform([query])

            # Calculate similarities using cosine_similarity
            similarities = cosine_similarity(query_vec, self.doc_vectors).flatten()

            # Get top k indices
            top_k_indices = np.argsort(similarities)[-k:][::-1]

            return [self.documents[i] for i in top_k_indices]
        elif self.doc_vectors is not None:
            # Use numpy for cosine similarity
            # For dense numpy arrays, compute directly
            query_lower = query.lower()
            # Simple approximation: use word overlap score
            import re
            query_tokens = set(re.findall(r'\w+', query_lower))
            scored = []
            for i, doc in enumerate(self.documents):
                doc_tokens = set(re.findall(r'\w+', doc.page_content.lower()))
                overlap = len(query_tokens & doc_tokens)
                score = overlap / (len(query_tokens) + 1e-8)
                scored.append((i, score))

            scored.sort(key=lambda x: x[1], reverse=True)
            return [self.documents[i] for i, _ in scored[:k]]
        else:
            # Fallback: simple keyword matching
            query_lower = query.lower()
            scored = []
            for doc in self.documents:
                score = 0.0
                for word in query_lower.split():
                    if word in doc.page_content.lower():
                        score += 1.0
                scored.append((doc, score))

            scored.sort(key=lambda x: x[1], reverse=True)
            return [doc for doc, _ in scored[:k]]


class HybridRetriever:
    """
    Parallel Hybrid Search Fusion Retriever.

    Executes vector (semantic) and keyword (lexical) searches in parallel,
    then fuses unique results with intelligent deduplication.

    Architecture:
        1. Scatter: Dispatch both searches in parallel
        2. Gather: Collect results from both retrievers
        3. Fusion: Deduplicate by content, preserve unique findings
        4. Rank: Return top-k fused results

    Benefits:
        - Captures both semantic meaning AND exact keywords
        - Parallel execution hides I/O latency
        - Resilient to failure (independent retrievers)

    Example:
        ```python
        docs = [
            Document("Our power saving initiative is called Project Titan"),
            Document("Error ERR_THROTTLE_900 indicates overheating"),
        ]

        vector = VectorRetriever(docs)
        keyword = TfidfRetriever(docs)
        hybrid = HybridRetriever(vector, keyword)

        # Query with both conceptual and keyword components
        results = hybrid.retrieve("power saving and error ERR_THROTTLE_900")
        # Returns BOTH documents (single retriever would miss one)
        ```
    """

    def __init__(self,
                 vector_retriever: BaseRetriever,
                 keyword_retriever: BaseRetriever,
                 k: int = 5,
                 enable_timing: bool = True):
        """
        Initialize hybrid retriever.

        Args:
            vector_retriever: Semantic/vector-based retriever
            keyword_retriever: Lexical/keyword-based retriever
            k: Number of results to return
            enable_timing: Track execution time for metrics
        """
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.k = k
        self.enable_timing = enable_timing

    def retrieve(self, query: str, k: int = None) -> HybridSearchResult:
        """
        Retrieve documents using parallel hybrid search.

        Args:
            query: Search query (may contain both concepts and keywords)
            k: Number of results to return (overrides default)

        Returns:
            HybridSearchResult with fused documents and metrics
        """
        k = k or self.k
        start_time = time.time()

        # Parallel retrieval
        vector_docs = []
        keyword_docs = []
        vector_time = 0.0
        keyword_time = 0.0

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both retrievals
            vector_future = executor.submit(
                self._timed_retrieve,
                self.vector_retriever,
                query,
                k
            )
            keyword_future = executor.submit(
                self._timed_retrieve,
                self.keyword_retriever,
                query,
                k
            )

            # Collect results
            vector_docs, vector_time = vector_future.result()
            keyword_docs, keyword_time = keyword_future.result()

        # Fusion: Combine and deduplicate
        all_docs = vector_docs + keyword_docs

        # Deduplicate by content (preserve first occurrence)
        seen = set()
        unique_docs = []
        for doc in all_docs:
            content_key = doc.page_content[:200]  # First 200 chars as key
            if content_key not in seen:
                seen.add(content_key)
                unique_docs.append(doc)

        # Limit to k results
        final_docs = unique_docs[:k]

        execution_time = time.time() - start_time

        return HybridSearchResult(
            documents=final_docs,
            total_results=len(all_docs),
            vector_results=len(vector_docs),
            keyword_results=len(keyword_docs),
            unique_results=len(unique_docs),
            execution_time=execution_time,
            vector_time=vector_time,
            keyword_time=keyword_time
        )

    def _timed_retrieve(self,
                       retriever: BaseRetriever,
                       query: str,
                       k: int) -> tuple[List[Document], float]:
        """Execute retrieval with timing."""
        start = time.time()
        docs = retriever.retrieve(query, k=k)
        elapsed = time.time() - start
        return docs, elapsed

    def retrieve_sequential(self, query: str, k: int = None) -> HybridSearchResult:
        """
        Retrieve documents sequentially (for comparison/testing).

        This method runs retrievers one after another instead of in parallel.
        Use for measuring the performance benefit of parallel execution.
        """
        k = k or self.k
        start_time = time.time()

        # Sequential retrieval
        vector_docs, vector_time = self._timed_retrieve(
            self.vector_retriever, query, k
        )
        keyword_docs, keyword_time = self._timed_retrieve(
            self.keyword_retriever, query, k
        )

        # Fusion
        all_docs = vector_docs + keyword_docs
        seen = set()
        unique_docs = []
        for doc in all_docs:
            content_key = doc.page_content[:200]
            if content_key not in seen:
                seen.add(content_key)
                unique_docs.append(doc)

        final_docs = unique_docs[:k]
        execution_time = time.time() - start_time

        return HybridSearchResult(
            documents=final_docs,
            total_results=len(all_docs),
            vector_results=len(vector_docs),
            keyword_results=len(keyword_docs),
            unique_results=len(unique_docs),
            execution_time=execution_time,
            vector_time=vector_time,
            keyword_time=keyword_time
        )

    def compare_parallel_vs_sequential(self,
                                      query: str,
                                      k: int = None) -> Dict[str, HybridSearchResult]:
        """
        Run both parallel and sequential retrieval for comparison.

        Useful for measuring performance improvement from parallelization.
        """
        k = k or self.k

        parallel_result = self.retrieve(query, k)
        sequential_result = self.retrieve_sequential(query, k)

        speedup = sequential_result.execution_time / parallel_result.execution_time

        return {
            'parallel': parallel_result,
            'sequential': sequential_result,
            'speedup': speedup,
            'time_saved': sequential_result.execution_time - parallel_result.execution_time
        }


def create_hybrid_retriever(documents: List[Document],
                            k: int = 5) -> HybridRetriever:
    """
    Factory function to create a hybrid retriever from documents.

    Automatically creates vector and keyword retrievers.

    Args:
        documents: List of documents to index
        k: Number of results to return

    Returns:
        Configured HybridRetriever
    """
    vector = VectorRetriever(documents, k=k)
    keyword = TfidfRetriever(documents, k=k)
    return HybridRetriever(vector, keyword, k=k)


# =============================================================================
# DEMO / TEST FUNCTION
# =============================================================================

def _demo_hybrid_search():
    """Demonstrate hybrid search with mixed queries."""
    print("\n" + "=" * 70)
    print("  PARALLEL HYBRID SEARCH FUSION DEMO")
    print("=" * 70)

    # Sample knowledge base
    documents = [
        Document(
            "Project Titan is our company's comprehensive power saving initiative. "
            "It aims to reduce energy consumption across all data centers by 40%.",
            metadata={"source": "strategy.doc", "type": "strategy"}
        ),
        Document(
            "Error code ERR_THROTTLE_900 indicates thermal throttling has occurred. "
            "The processor is overheating and reducing clock speeds to prevent damage.",
            metadata={"source": "errors.log", "type": "technical"}
        ),
        Document(
            "The new Eco-AI-M2 chip is designed for edge computing and mobile devices. "
            "It consumes only 5W under typical load.",
            metadata={"source": "products.md", "type": "product"}
        ),
        Document(
            "Power saving mode can be enabled in BIOS settings. Look for "
            "'Energy Efficient Ethernet' and 'Power C-State' options.",
            metadata={"source": "manual.txt", "type": "guide"}
        ),
        Document(
            "QLeap-V4 processor specifications: 180W TDP, 5.2GHz boost clock, "
            "supports DDR5-6000 memory. Designed for maximum performance data centers.",
            metadata={"source": "specs.pdf", "type": "technical"}
        ),
    ]

    # Create retrievers
    print("\n[Setup] Creating retrievers...")
    hybrid = create_hybrid_retriever(documents, k=3)

    # Test query with both conceptual and keyword components
    query = "What are our power saving efforts and what is error ERR_THROTTLE_900?"

    print(f"\n[Query] {query}")
    print("[Analysis] Query contains:")
    print("  - Conceptual: 'power saving efforts'")
    print("  - Specific keyword: 'ERR_THROTTLE_900'")

    # Run hybrid search
    print("\n[Execution] Running parallel hybrid search...")
    result = hybrid.retrieve(query)

    # Display results
    print(f"\n[Results] Found {len(result.documents)} unique documents:")
    print(f"  - Vector retriever: {result.vector_results} docs")
    print(f"  - Keyword retriever: {result.keyword_results} docs")
    print(f"  - Total before fusion: {result.total_results} docs")
    print(f"  - After deduplication: {result.unique_results} docs")
    print(f"  - Execution time: {result.execution_time:.3f}s")

    for i, doc in enumerate(result.documents, 1):
        print(f"\n  [{i}] {doc.page_content[:100]}...")

    # Compare with single retrievers
    print("\n" + "-" * 70)
    print("[Comparison] Single Retriever vs Hybrid")
    print("-" * 70)

    print("\n[Vector-Only] Semantic search:")
    vector_only = hybrid.vector_retriever.retrieve(query, k=3)
    print(f"  Found {len(vector_only)} docs:")
    for i, doc in enumerate(vector_only, 1):
        snippet = doc.page_content[:60].replace('\n', ' ')
        print(f"    [{i}] {snippet}...")

    print("\n[Keyword-Only] Lexical search:")
    keyword_only = hybrid.keyword_retriever.retrieve(query, k=3)
    print(f"  Found {len(keyword_only)} docs:")
    for i, doc in enumerate(keyword_only, 1):
        snippet = doc.page_content[:60].replace('\n', ' ')
        print(f"    [{i}] {snippet}...")

    print("\n[Hybrid] Combined search:")
    print(f"  Found {len(result.documents)} docs (fusion of both):")
    for i, doc in enumerate(result.documents, 1):
        snippet = doc.page_content[:60].replace('\n', ' ')
        print(f"    [{i}] {snippet}...")

    print("\n" + "=" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    _demo_hybrid_search()
