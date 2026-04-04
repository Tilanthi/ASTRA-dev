"""
ASTRA Live — Literature Integration (Phase 9.1+9.2)
TF-IDF based semantic similarity for paper matching and novelty scoring.
"""
import logging
import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try sklearn TF-IDF first; fall back to custom implementation
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.info("sklearn not available — using custom TF-IDF implementation")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# ═══════════════════════════════════════════════════════════════
# Custom TF-IDF fallback (no sklearn)
# ═══════════════════════════════════════════════════════════════

# Standard English stop words
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "this", "that",
    "these", "those", "it", "its", "we", "our", "they", "their", "them",
    "he", "she", "his", "her", "not", "no", "so", "if", "as", "than",
    "also", "such", "which", "who", "what", "when", "where", "how",
    "very", "more", "most", "about", "between", "through", "each",
    "both", "all", "some", "any", "other", "into", "over", "after",
})


def _tokenize(text: str) -> List[str]:
    """Lowercase, strip non-alpha, remove stop words."""
    tokens = re.findall(r'[a-z0-9]+', text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def _build_tfidf_matrix(documents: List[str]) -> Tuple[List[Dict[str, float]], Dict[str, float]]:
    """Build TF-IDF vectors for a list of documents. Returns (doc_vectors, idf_dict)."""
    n_docs = len(documents)
    if n_docs == 0:
        return [], {}

    # Tokenize all docs
    tokenized = [_tokenize(doc) for doc in documents]

    # Document frequency
    df: Counter = Counter()
    for tokens in tokenized:
        for word in set(tokens):
            df[word] += 1

    # IDF = log(N / df)
    idf = {word: math.log(n_docs / count) for word, count in df.items()}

    # TF-IDF vectors
    vectors = []
    for tokens in tokenized:
        tf: Counter = Counter(tokens)
        total = len(tokens) or 1
        vec = {word: (count / total) * idf.get(word, 0) for word, count in tf.items()}
        vectors.append(vec)

    return vectors, idf


def _cosine_similarity_dicts(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Cosine similarity between two sparse TF-IDF vectors (dicts)."""
    common = set(a.keys()) & set(b.keys())
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ═══════════════════════════════════════════════════════════════
# Paper dataclass
# ═══════════════════════════════════════════════════════════════

@dataclass
class Paper:
    """An arXiv paper record."""
    title: str
    abstract: str
    authors: List[str] = field(default_factory=list)
    arxiv_id: str = ""
    published: str = ""
    added_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "arxiv_id": self.arxiv_id,
            "published": self.published,
            "added_at": self.added_at,
        }


# ═══════════════════════════════════════════════════════════════
# LiteratureStore
# ═══════════════════════════════════════════════════════════════

class LiteratureStore:
    """
    Maintains a corpus of papers and provides TF-IDF similarity search
    and novelty scoring for discoveries/hypotheses.
    """

    def __init__(self):
        self._papers: Dict[str, Paper] = {}  # keyed by arxiv_id or title hash
        self._dirty: bool = True  # Index needs rebuild
        # sklearn objects (if available)
        self._vectorizer: Optional[object] = None
        self._tfidf_matrix: Optional[object] = None
        # Custom fallback objects
        self._custom_vectors: List[Dict[str, float]] = []
        self._custom_idf: Dict[str, float] = {}
        self._corpus_keys: List[str] = []  # Ordered keys matching matrix rows

    # ── Paper management ──────────────────────────────────────────

    def add_paper(self, title: str, abstract: str, authors: Optional[List[str]] = None,
                  arxiv_id: str = "", published: str = "") -> Paper:
        """Add a paper to the store. Deduplicates by arxiv_id or title."""
        key = arxiv_id if arxiv_id else str(hash(title))
        if key in self._papers:
            return self._papers[key]

        paper = Paper(
            title=title,
            abstract=abstract,
            authors=authors or [],
            arxiv_id=arxiv_id,
            published=published,
        )
        self._papers[key] = paper
        self._dirty = True
        return paper

    def add_papers_from_arxiv(self, papers: List[dict]) -> int:
        """Bulk-add papers from arXiv search results (data_fetcher format)."""
        added = 0
        for p in papers:
            title = p.get("title", "")
            abstract = p.get("abstract", "")
            if not title:
                continue
            key = p.get("arxiv_id", "") or str(hash(title))
            if key not in self._papers:
                self.add_paper(
                    title=title,
                    abstract=abstract,
                    authors=p.get("authors", []),
                    arxiv_id=p.get("arxiv_id", ""),
                    published=p.get("published", ""),
                )
                added += 1
        return added

    def get_papers(self) -> List[dict]:
        """Return all papers as dicts."""
        return [p.to_dict() for p in self._papers.values()]

    @property
    def paper_count(self) -> int:
        return len(self._papers)

    # ── Index building ────────────────────────────────────────────

    def _rebuild_index(self):
        """Rebuild TF-IDF index from all papers."""
        if not self._dirty or not self._papers:
            return

        self._corpus_keys = list(self._papers.keys())
        documents = [
            f"{self._papers[k].title} {self._papers[k].abstract}"
            for k in self._corpus_keys
        ]

        if HAS_SKLEARN:
            self._vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            self._tfidf_matrix = self._vectorizer.fit_transform(documents)
        else:
            self._custom_vectors, self._custom_idf = _build_tfidf_matrix(documents)

        self._dirty = False
        logger.info(f"Literature index rebuilt: {len(documents)} papers, "
                     f"backend={'sklearn' if HAS_SKLEARN else 'custom'}")

    # ── Similarity search ─────────────────────────────────────────

    def find_related_papers(self, text: str, top_k: int = 5) -> List[dict]:
        """
        Find the top-k most similar papers to the given text using TF-IDF
        cosine similarity.

        Returns list of dicts with paper info + similarity score.
        """
        if not self._papers:
            return []

        self._rebuild_index()

        if HAS_SKLEARN and self._vectorizer is not None and self._tfidf_matrix is not None:
            query_vec = self._vectorizer.transform([text])
            similarities = sklearn_cosine(query_vec, self._tfidf_matrix).flatten()
            top_indices = similarities.argsort()[::-1][:top_k]

            results = []
            for idx in top_indices:
                if idx < len(self._corpus_keys):
                    key = self._corpus_keys[idx]
                    paper = self._papers[key]
                    results.append({
                        **paper.to_dict(),
                        "similarity": float(similarities[idx]),
                    })
            return results
        else:
            # Custom fallback
            if not self._custom_vectors:
                return []

            # Build query vector using corpus IDF
            query_tokens = _tokenize(text)
            query_tf: Counter = Counter(query_tokens)
            total = len(query_tokens) or 1
            query_vec = {
                word: (count / total) * self._custom_idf.get(word, 0)
                for word, count in query_tf.items()
            }

            # Compute similarities
            scored = []
            for i, doc_vec in enumerate(self._custom_vectors):
                sim = _cosine_similarity_dicts(query_vec, doc_vec)
                scored.append((i, sim))

            scored.sort(key=lambda x: x[1], reverse=True)

            results = []
            for idx, sim in scored[:top_k]:
                if idx < len(self._corpus_keys):
                    key = self._corpus_keys[idx]
                    paper = self._papers[key]
                    results.append({
                        **paper.to_dict(),
                        "similarity": float(sim),
                    })
            return results

    # ── Novelty scoring ───────────────────────────────────────────

    def compute_novelty_score(self, discovery_text: str) -> float:
        """
        Compute a novelty score for a discovery/hypothesis description.

        Returns 0.0–1.0 where:
          - 1.0 = highly novel (no similar literature found)
          - 0.0 = well-established (very similar to existing papers)

        Method: 1 - max_similarity across all papers.
        If the corpus is empty, returns 0.5 (unknown).
        """
        if not self._papers:
            return 0.5  # No literature to compare against → unknown

        related = self.find_related_papers(discovery_text, top_k=5)
        if not related:
            return 0.5

        max_sim = max(r["similarity"] for r in related)
        # Novelty = 1 - max_similarity, clamped to [0, 1]
        novelty = max(0.0, min(1.0, 1.0 - max_sim))
        return round(novelty, 4)

    def novelty_report(self, text: str, top_k: int = 5) -> dict:
        """Full novelty report with similar papers and score."""
        related = self.find_related_papers(text, top_k=top_k)
        max_sim = max((r["similarity"] for r in related), default=0.0)
        novelty = max(0.0, min(1.0, 1.0 - max_sim)) if related else 0.5

        return {
            "novelty_score": round(novelty, 4),
            "max_similarity": round(max_sim, 4),
            "related_papers": related,
            "corpus_size": self.paper_count,
            "interpretation": _interpret_novelty(novelty),
        }

    def to_dict(self) -> dict:
        """Serializable summary."""
        return {
            "paper_count": self.paper_count,
            "backend": "sklearn" if HAS_SKLEARN else "custom",
            "index_dirty": self._dirty,
        }


def _interpret_novelty(score: float) -> str:
    """Human-readable interpretation of novelty score."""
    if score >= 0.9:
        return "Highly novel — no closely related literature found"
    elif score >= 0.7:
        return "Novel — limited related literature"
    elif score >= 0.5:
        return "Moderately novel — some related work exists"
    elif score >= 0.3:
        return "Incremental — substantial related literature"
    else:
        return "Well-established — closely matches existing literature"


# ═══════════════════════════════════════════════════════════════
# Singleton instance for the backend
# ═══════════════════════════════════════════════════════════════

_store: Optional[LiteratureStore] = None


def get_literature_store() -> LiteratureStore:
    """Get or create the singleton LiteratureStore."""
    global _store
    if _store is None:
        _store = LiteratureStore()
    return _store
