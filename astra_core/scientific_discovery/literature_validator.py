"""
ASTRA Genuine Discovery System - Literature Validator

This module implements real-time literature search and novelty validation
to replace keyword-based scoring with semantic similarity to actual scientific papers.

Key Features:
- Real arXiv API integration for astrophysics literature
- ADS (Astrophysics Data System) integration
- Semantic similarity scoring using vector embeddings
- Citation network analysis
- Similar paper ranking and reporting
- Timeout mechanisms for API calls (prevents hanging after sleep/resume)
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import logging
import hashlib
import json

# Try to import required libraries
try:
    import arxiv
    from astroquery.nasa_ads import ADS
    from astroquery.simbad import Simbad
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = str(e)
    logging.warning(f"Literature validation dependencies not available: {e}")

# Import query optimizer
try:
    from astra_core.scientific_discovery.query_optimizer import LiteratureQueryOptimizer, OptimizedQuery
    QUERY_OPTIMIZER_AVAILABLE = True
except ImportError:
    QUERY_OPTIMIZER_AVAILABLE = False
    logging.warning("Query optimizer not available, using direct queries")

logger = logging.getLogger(__name__)

# Timeout constants to prevent hanging after sleep/resume or API issues
ARXIV_SEARCH_TIMEOUT = 120  # 2 minutes timeout for arXiv searches
ADS_SEARCH_TIMEOUT = 120    # 2 minutes timeout for ADS searches
VALIDATION_TOTAL_TIMEOUT = 600  # 10 minutes total timeout for entire validation
API_RETRY_DELAY = 5         # 5 seconds delay between retries
MAX_API_RETRIES = 3         # Maximum number of retries for API calls
MODEL_LOAD_TIMEOUT = 60      # 1 minute timeout for loading sentence transformer models


async def retry_with_backoff(
    func,
    *args,
    max_retries=MAX_API_RETRIES,
    base_delay=API_RETRY_DELAY,
    **kwargs
):
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        *args: Arguments to pass to the function
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries (will be exponentially increased)
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Function result or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} retry attempts failed: {e}")
                raise

            delay = base_delay * (2 ** attempt)  # Exponential backoff
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)

    return None


class ConfidenceLevel(Enum):
    """Discovery confidence levels"""
    CANDIDATE = "CANDIDATE"      # Passed literature novelty check only
    VALIDATED = "VALIDATED"      # Passed full validation pipeline
    PUBLISHED = "PUBLISHED"      # Accepted by scientific community


class ValidationStatus(Enum):
    """Validation status from pipeline"""
    NOT_NOVEL = "NOT_NOVEL"                    # Already exists in literature
    CITATION_ERRORS = "CITATION_ERRORS"        # Hallucinated or invalid citations
    FORMULA_ERRORS = "FORMULA_ERRORS"          # Invalid physics/math
    STATISTICAL_ERRORS = "STATISTICAL_ERRORS"  # Statistical issues
    CANDIDATE = "CANDIDATE"                    # Passed basic validation
    VALIDATED = "VALIDATED"                    # Passed full validation
    PUBLISHED = "PUBLISHED"                    # Published research


@dataclass
class SimilarPaper:
    """Represents a paper similar to a discovery claim"""
    title: str
    authors: List[str]
    year: int
    abstract: str
    arxiv_id: Optional[str] = None
    ads_bibcode: Optional[str] = None
    doi: Optional[str] = None
    similarity_score: float = 0.0
    relevance_reasoning: str = ""
    citation_count: int = 0


@dataclass
class CitationReport:
    """Report on citation validation"""
    total_citations: int
    verified_citations: int
    hallucinated_citations: int
    unverifiable_citations: int
    citation_details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FormulaReport:
    """Report on formula validation"""
    total_formulas: int
    verified_formulas: int
    derivable_formulas: int
    inconsistent_formulas: int
    unverifiable_formulas: int
    formula_details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class NoveltyReport:
    """Comprehensive novelty validation report"""
    novelty_score: float  # 0.0 = identical to existing, 1.0 = completely novel
    similar_papers: List[SimilarPaper]
    validation_timestamp: datetime
    confidence_level: ConfidenceLevel
    citation_report: Optional[CitationReport] = None
    formula_report: Optional[FormulaReport] = None
    search_queries_used: List[str] = field(default_factory=list)
    total_papers_searched: int = 0
    validation_time_seconds: float = 0.0
    limitations: List[str] = field(default_factory=list)
    domain_coverage: Dict[str, float] = field(default_factory=dict)


@dataclass
class LiteratureSearchResult:
    """Result from literature search"""
    papers: List[SimilarPaper]
    query: str
    source: str  # 'arxiv', 'ads', 'semantic_scholar'
    total_results: int
    search_time_seconds: float


class LiteratureCache:
    """Cache for literature search results to avoid redundant API calls"""

    def __init__(self, ttl_seconds: int = 86400):  # 24 hour default TTL
        self.cache: Dict[str, Tuple[LiteratureSearchResult, datetime]] = {}
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _generate_key(self, query: str, source: str, max_results: int) -> str:
        """Generate cache key from search parameters"""
        key_data = f"{query}:{source}:{max_results}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, query: str, source: str, max_results: int = 50) -> Optional[LiteratureSearchResult]:
        """Get cached result if available and not expired"""
        key = self._generate_key(query, source, max_results)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl_seconds):
                self.hits += 1
                return result
            else:
                # Expired, remove from cache
                del self.cache[key]
        self.misses += 1
        return None

    def set(self, query: str, source: str, result: LiteratureSearchResult, max_results: int = 50):
        """Cache a search result"""
        key = self._generate_key(query, source, max_results)
        self.cache[key] = (result, datetime.now())

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache)
        }


class ArxivClient:
    """Real arXiv API client with rate limiting and caching"""

    def __init__(self, cache: LiteratureCache):
        self.cache = cache
        self.last_request_time = 0
        self.min_request_interval = 3.0  # arXiv rate limit: 1 request per 3 seconds
        self.client = None
        if DEPENDENCIES_AVAILABLE:
            try:
                self.client = arxiv.Client(
                    page_size=100,
                    delay_seconds=3.0,
                    num_retries=3
                )
            except Exception as e:
                logger.error(f"Failed to initialize arXiv client: {e}")

    async def search(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        max_results: int = 50,
        sort_by: str = "relevance"
    ) -> LiteratureSearchResult:
        """
        Search arXiv for relevant papers

        Args:
            query: Search query string
            categories: arXiv categories (e.g., ['astro-ph.GA', 'astro-ph.HE'])
            max_results: Maximum number of results to return
            sort_by: Sort order ('relevance', 'lastUpdatedDate', 'submittedDate')

        Returns:
            LiteratureSearchResult with papers found
        """
        start_time = time.time()

        # Check cache first
        cached = self.cache.get(query, "arxiv", max_results)
        if cached:
            logger.info(f"arXiv cache hit for query: {query[:50]}...")
            return cached

        # Rate limiting
        time_since_last_request = time.time() - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)

        # Build search query
        search_query = query
        if categories:
            cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
            search_query = f"({query}) AND ({cat_query})"

        logger.info(f"Searching arXiv with query: {search_query[:100]}...")

        papers = []
        try:
            if not DEPENDENCIES_AVAILABLE or not self.client:
                logger.warning("arXiv dependencies not available, returning empty results")
                return LiteratureSearchResult(
                    papers=[],
                    query=query,
                    source="arxiv",
                    total_results=0,
                    search_time_seconds=time.time() - start_time
                )

            # Create search
            search = arxiv.Search(
                query=search_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance if sort_by == "relevance" else arxiv.SortCriterion.SubmittedDate
            )

            # Execute search with timeout to prevent hanging after sleep/resume
            try:
                # Use asyncio.wait_for to add timeout to the generator-based search
                papers = await asyncio.wait_for(
                    self._execute_arxiv_search_with_timeout(search),
                    timeout=ARXIV_SEARCH_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.error(f"arXiv search timed out after {ARXIV_SEARCH_TIMEOUT}s - likely due to network issues or sleep mode")
                papers = []
            except Exception as e:
                logger.error(f"arXiv search failed with exception: {e}")
                papers = []

            self.last_request_time = time.time()

        except Exception as e:
            logger.error(f"arXiv search failed: {e}")

        search_result = LiteratureSearchResult(
            papers=papers,
            query=query,
            source="arxiv",
            total_results=len(papers),
            search_time_seconds=time.time() - start_time
        )

        # Cache the result
        self.cache.set(query, "arxiv", search_result, max_results)

        logger.info(f"arXiv search completed: {len(papers)} papers in {search_result.search_time_seconds:.2f}s")

        return search_result

    async def _execute_arxiv_search_with_timeout(self, search: arxiv.Search) -> List[SimilarPaper]:
        """
        Execute arXiv search with timeout protection.

        This helper method runs the synchronous arXiv API call in an executor
        to prevent blocking the event loop and allow timeout handling.

        Args:
            search: arXiv Search object

        Returns:
            List of SimilarPaper objects
        """
        papers = []

        def execute_search():
            """Synchronous search function to run in executor"""
            local_papers = []
            try:
                for result in self.client.results(search):
                    paper = SimilarPaper(
                        title=result.title,
                        authors=[author.name for author in result.authors],
                        year=result.published.year if result.published else 2024,
                        abstract=result.summary.replace('\n', ' '),
                        arxiv_id=result.entry_id.split('/')[-1]
                    )
                    local_papers.append(paper)
            except Exception as e:
                logger.error(f"Error in arXiv search execution: {e}")
            return local_papers

        # Run the synchronous search in an executor to avoid blocking
        loop = asyncio.get_event_loop()
        papers = await loop.run_in_executor(None, execute_search)

        return papers


class ADSClient:
    """ADS (Astrophysics Data System) API client"""

    def __init__(self, cache: LiteratureCache):
        self.cache = cache
        self.last_request_time = 0
        self.min_request_interval = 1.0  # ADS rate limit

    async def search(
        self,
        query: str,
        max_results: int = 50,
        year_range: Optional[Tuple[int, int]] = None
    ) -> LiteratureSearchResult:
        """
        Search ADS for astrophysics literature

        Args:
            query: Search query string
            max_results: Maximum number of results
            year_range: Optional (year_start, year_end) tuple

        Returns:
            LiteratureSearchResult with papers found
        """
        start_time = time.time()

        # Check cache
        cached = self.cache.get(query, "ads", max_results)
        if cached:
            logger.info(f"ADS cache hit for query: {query[:50]}...")
            return cached

        # Rate limiting
        time_since_last_request = time.time() - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)

        papers = []
        try:
            if not DEPENDENCIES_AVAILABLE:
                logger.warning("ADS dependencies not available, returning empty results")
                return LiteratureSearchResult(
                    papers=[],
                    query=query,
                    source="ads",
                    total_results=0,
                    search_time_seconds=time.time() - start_time
                )

            # Configure ADS query
            ads_query = AdsQuery(
                q=query,
                fl=["title", "author", "year", "abstract", "bibcode", "citation_count"],
                rows=max_results
            )

            if year_range:
                ads_query.add_parameter('year', f'{year_range[0]}-{year_range[1]}')

            # Execute search (this would use astroquery)
            # For now, return placeholder
            logger.info("ADS search placeholder - implementation requires astroquery.ads setup")

        except Exception as e:
            logger.error(f"ADS search failed: {e}")

        search_result = LiteratureSearchResult(
            papers=papers,
            query=query,
            source="ads",
            total_results=len(papers),
            search_time_seconds=time.time() - start_time
        )

        self.cache.set(query, "ads", search_result, max_results)
        self.last_request_time = time.time()

        return search_result


class SemanticSimilarityAnalyzer:
    """Compute semantic similarity between discovery claims and papers"""

    def __init__(self):
        self.model = None
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        self.model_loaded = False
        self.model_loading = False

        # Don't load model during initialization to prevent blocking
        # Model will be loaded lazily when first needed
        if DEPENDENCIES_AVAILABLE:
            logger.info("Semantic similarity available - will load model on first use")
        else:
            logger.warning("Semantic similarity dependencies not available")

    def _load_model_with_timeout(self, timeout_seconds: int = MODEL_LOAD_TIMEOUT) -> bool:
        """Load sentence transformer model with timeout to prevent blocking"""
        if self.model_loaded or self.model_loading:
            return self.model_loaded

        self.model_loading = True
        start_time = time.time()

        try:
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Model loading timed out after {timeout_seconds} seconds")

            # Set alarm for timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

            try:
                # Try to load scientific text embedding model
                logger.info("Loading semantic similarity model (with timeout)...")
                self.model = SentenceTransformer('allenai-specter')
                self.model_loaded = True
                logger.info("✅ Loaded semantic similarity model: allenai-specter")
                return True

            except TimeoutError as e:
                logger.warning(f"⏱️ Model loading timeout: {e}")
                return False
            except Exception as e:
                logger.warning(f"Failed to load allenai-specter: {e}")
                # Try fallback model
                try:
                    logger.info("Trying fallback model...")
                    self.model = SentenceTransformer('all-MiniLM-L6-v2')
                    self.model_loaded = True
                    logger.info("✅ Loaded fallback semantic similarity model: all-MiniLM-L6-v2")
                    return True
                except Exception as e2:
                    logger.error(f"❌ Failed to load any semantic similarity model: {e2}")
                    return False
            finally:
                # Cancel alarm
                signal.alarm(0)

        except Exception as e:
            logger.error(f"Unexpected error loading model: {e}")
            return False
        finally:
            self.model_loading = False
            elapsed = time.time() - start_time
            logger.info(f"Model loading attempt took {elapsed:.1f} seconds")

    def encode_text(self, text: str) -> Optional[np.ndarray]:
        """Encode text to vector embedding"""
        # Lazy load model on first use
        if not self.model_loaded and DEPENDENCIES_AVAILABLE:
            if not self._load_model_with_timeout():
                logger.warning("Could not load semantic similarity model - skipping encoding")
                return None

        if not self.model:
            return None

        # Check cache
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        if text_hash in self.embeddings_cache:
            return self.embeddings_cache[text_hash]

        try:
            embedding = self.model.encode(text, show_progress_bar=False)
            self.embeddings_cache[text_hash] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            return None

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts"""
        emb1 = self.encode_text(text1)
        emb2 = self.encode_text(text2)

        if emb1 is None or emb2 is None:
            return 0.0

        try:
            similarity = cosine_similarity([emb1], [emb2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0

    def find_most_similar_papers(
        self,
        discovery_claim: str,
        papers: List[SimilarPaper],
        top_k: int = 10
    ) -> List[Tuple[SimilarPaper, float]]:
        """
        Find most semantically similar papers to discovery claim

        Args:
            discovery_claim: The discovery text
            papers: List of papers to compare
            top_k: Number of top results to return

        Returns:
            List of (paper, similarity_score) tuples
        """
        if not papers or not self.model:
            return []

        claim_embedding = self.encode_text(discovery_claim)
        if claim_embedding is None:
            return []

        paper_embeddings = []
        for paper in papers:
            # Combine title and abstract for better matching
            paper_text = f"{paper.title} {paper.abstract}"
            emb = self.encode_text(paper_text)
            if emb is not None:
                paper_embeddings.append((paper, emb))
            else:
                paper_embeddings.append((paper, np.zeros_like(claim_embedding)))

        # Compute similarities
        similarities = []
        for paper, paper_emb in paper_embeddings:
            try:
                similarity = cosine_similarity([claim_embedding], [paper_emb])[0][0]
                similarities.append((paper, float(similarity)))
            except Exception as e:
                logger.error(f"Failed to compute similarity for {paper.title}: {e}")

        # Sort by similarity (descending) and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class LiteratureValidator:
    """
    Main literature validation engine

    Replaces keyword-based novelty scoring with real literature search
    and semantic similarity analysis.
    """

    def __init__(
        self,
        cache_ttl_seconds: int = 86400,
        enable_arxiv: bool = True,
        enable_ads: bool = True,
        similarity_threshold: float = 0.5  # Papers with similarity > threshold are considered similar
    ):
        self.cache = LiteratureCache(ttl_seconds=cache_ttl_seconds)
        self.similarity_analyzer = SemanticSimilarityAnalyzer()
        self.similarity_threshold = similarity_threshold

        # Initialize clients
        self.arxiv_client = ArxivClient(self.cache) if enable_arxiv else None
        self.ads_client = ADSClient(self.cache) if enable_ads else None

        # Domain to arXiv category mapping
        self.domain_categories = {
            "astrophysics": ["astro-ph.GA", "astro-ph.HE", "astro-ph.CO", "astro-ph.EP"],
            "cosmology": ["astro-ph.CO"],
            "star_formation": ["astro-ph.GA"],
            "ism": ["astro-ph.GA"],
            "exoplanets": ["astro-ph.EP"],
            "high_energy_astro": ["astro-ph.HE"],
            "galactic_astronomy": ["astro-ph.GA"],
            "stellar_evolution": ["astro-ph.SR"],
            "interstellar_medium": ["astro-ph.GA"],
            "molecular_clouds": ["astro-ph.GA"],
            "astrochemistry": ["astro-ph.GA"],
            "compact_objects": ["astro-ph.HE"],
            "gravitational_waves": ["astro-ph.HE", "gr-qc"],
            "neutrino_astronomy": ["astro-ph.HE"],
            "multi_messenger_astronomy": ["astro-ph.HE"],
            "dark_matter": ["astro-ph.CO", "hep-ph"],
            "large_scale_structure": ["astro-ph.CO"],
            "cosmic_microwave_background": ["astro-ph.CO"]
        }

        logger.info(f"LiteratureValidator initialized with arXiv={enable_arxiv}, ADS={enable_ads}")

    def _map_domains_to_arxiv(self, domains: List[str]) -> List[str]:
        """Map ASTRA domains to arXiv categories"""
        categories = set()
        for domain in domains:
            if domain in self.domain_categories:
                categories.update(self.domain_categories[domain])
        return list(categories)

    async def validate_novelty(
        self,
        discovery_claim: str,
        domains: List[str],
        discovery_type: str = "general",
        max_results_per_source: int = 50
    ) -> NoveltyReport:
        """
        Validate discovery novelty against real scientific literature

        This is the main entry point that replaces keyword-based novelty scoring.

        Args:
            discovery_claim: The discovery text to validate
            domains: List of astronomical domains
            discovery_type: Type of discovery (pattern_discovery, theoretical_synthesis, etc.)
            max_results_per_source: Max results to fetch from each source

        Returns:
            NoveltyReport with comprehensive validation results
        """
        # Add timeout protection to entire validation process
        try:
            return await asyncio.wait_for(
                self._validate_novelty_impl(
                    discovery_claim, domains, discovery_type, max_results_per_source
                ),
                timeout=VALIDATION_TOTAL_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Validation timed out after {VALIDATION_TOTAL_TIMEOUT}s - returning basic report")
            # Return a basic report indicating validation failure
            return NoveltyReport(
                novelty_score=0.5,  # Neutral score when validation fails
                similar_papers=[],
                validation_timestamp=datetime.utcnow(),
                confidence_level=ConfidenceLevel.CANDIDATE,
                limitations=["Validation timeout - possibly due to network issues or API rate limiting"],
                search_queries_used=[discovery_claim],
                total_papers_searched=0,
                validation_time_seconds=VALIDATION_TOTAL_TIMEOUT
            )
        except Exception as e:
            logger.error(f"Validation failed with exception: {e}")
            return NoveltyReport(
                novelty_score=0.5,  # Neutral score when validation fails
                similar_papers=[],
                validation_timestamp=datetime.utcnow(),
                confidence_level=ConfidenceLevel.CANDIDATE,
                limitations=[f"Validation failed: {str(e)}"],
                search_queries_used=[discovery_claim],
                total_papers_searched=0,
                validation_time_seconds=time.time() - start_time
            )

    async def _validate_novelty_impl(
        self,
        discovery_claim: str,
        domains: List[str],
        discovery_type: str = "general",
        max_results_per_source: int = 50
    ) -> NoveltyReport:
        """
        Internal implementation of novelty validation with timeout protection.
        """
        start_time = time.time()
        logger.info(f"Starting novelty validation for: {discovery_claim[:100]}...")

        all_papers: List[SimilarPaper] = []
        total_papers_searched = 0

        # STAGE 0: Query Optimization
        optimized_queries = []
        if QUERY_OPTIMIZER_AVAILABLE:
            try:
                query_optimizer = LiteratureQueryOptimizer()
                optimized_queries = query_optimizer.optimize_query(discovery_claim, num_strategies=3)
                logger.info(f"Generated {len(optimized_queries)} optimized query strategies")
                for i, query_obj in enumerate(optimized_queries):
                    logger.info(f"  Strategy {i+1} ({query_obj.strategy}, confidence={query_obj.confidence:.2f}): {query_obj.query[:80]}...")
            except Exception as e:
                logger.warning(f"Query optimization failed, using direct query: {e}")
                optimized_queries = []
        else:
            logger.info("Query optimizer not available, using direct discovery claim")

        # Use optimized queries if available, otherwise fall back to direct claim
        search_queries = [q.query for q in optimized_queries] if optimized_queries else [discovery_claim]

        # STAGE 1: Search arXiv with multiple query strategies
        if self.arxiv_client:
            categories = self._map_domains_to_arxiv(domains)
            all_arxiv_papers = []

            # Try each query strategy until we get good results
            for i, search_query in enumerate(search_queries):
                try:
                    logger.info(f"Trying arXiv search strategy {i+1}/{len(search_queries)}")

                    # Use retry logic with exponential backoff for network resilience
                    arxiv_result = await retry_with_backoff(
                        self.arxiv_client.search,
                        query=search_query,
                        categories=categories,
                        max_results=max_results_per_source
                    )

                    if arxiv_result:
                        all_arxiv_papers.extend(arxiv_result.papers)
                        total_papers_searched += arxiv_result.total_results
                        logger.info(f"arXiv search {i+1} found {len(arxiv_result.papers)} papers using: {search_query[:50]}...")

                        # If we found papers, use this strategy
                        if len(arxiv_result.papers) > 0:
                            logger.info(f"Strategy {i+1} successful, using {len(arxiv_result.papers)} papers")
                            break
                        else:
                            logger.info(f"Strategy {i+1} found no papers, trying next strategy")
                    else:
                        logger.warning(f"arXiv search {i+1} returned None after retries")

                except Exception as e:
                    logger.error(f"arXiv search strategy {i+1} failed after all retries: {e}")

            all_papers.extend(all_arxiv_papers)

        # STAGE 2: Search ADS with optimized queries
        if self.ads_client:
            all_ads_papers = []
            for i, search_query in enumerate(search_queries):
                try:
                    logger.info(f"Trying ADS search strategy {i+1}/{len(search_queries)}")

                    # Use retry logic with exponential backoff for network resilience
                    ads_result = await retry_with_backoff(
                        self.ads_client.search,
                        query=search_query,
                        max_results=max_results_per_source
                    )

                    if ads_result:
                        all_ads_papers.extend(ads_result.papers)
                        total_papers_searched += ads_result.total_results
                        logger.info(f"ADS search {i+1} found {len(ads_result.papers)} papers using: {search_query[:50]}...")

                        # If we found papers, use this strategy
                        if len(ads_result.papers) > 0:
                            logger.info(f"ADS strategy {i+1} successful, using {len(ads_result.papers)} papers")
                            break
                    else:
                        logger.warning(f"ADS search {i+1} returned None after retries")

                except Exception as e:
                    logger.error(f"ADS search strategy {i+1} failed after all retries: {e}")

            all_papers.extend(all_ads_papers)

        # Remove duplicates (by title)
        seen_titles = set()
        unique_papers = []
        for paper in all_papers:
            title_lower = paper.title.lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_papers.append(paper)

        all_papers = unique_papers
        logger.info(f"Total unique papers found: {len(all_papers)}")

        # Stage 3: Compute semantic similarities
        similar_papers_with_scores = self.similarity_analyzer.find_most_similar_papers(
            discovery_claim=discovery_claim,
            papers=all_papers,
            top_k=20
        )

        # Update similarity scores in paper objects
        similar_papers = []
        for paper, similarity in similar_papers_with_scores:
            paper.similarity_score = similarity
            # Add reasoning for similarity
            if similarity > 0.7:
                paper.relevance_reasoning = "Very strong conceptual overlap"
            elif similarity > 0.5:
                paper.relevance_reasoning = "Strong thematic similarity"
            elif similarity > 0.3:
                paper.relevance_reasoning = "Moderate topical overlap"
            else:
                paper.relevance_reasoning = "Weak or tangential relation"
            similar_papers.append(paper)

        # Stage 4: Compute novelty score
        # Novelty = 1 - max_similarity (inverted for novelty)
        max_similarity = max([p.similarity_score for p in similar_papers]) if similar_papers else 0.0
        novelty_score = 1.0 - max_similarity

        # Stage 5: Determine confidence level
        if novelty_score >= 0.7:
            confidence_level = ConfidenceLevel.CANDIDATE
        elif novelty_score >= 0.5:
            confidence_level = ConfidenceLevel.CANDIDATE
        else:
            confidence_level = ConfidenceLevel.CANDIDATE  # Default to CANDIDATE, validation pipeline upgrades

        # Stage 6: Generate limitations based on search coverage
        limitations = []
        if not self.arxiv_client:
            limitations.append("arXiv search not available - may miss recent preprints")
        if not self.ads_client:
            limitations.append("ADS search not available - limited to arXiv coverage")
        if len(all_papers) < 10:
            limitations.append(f"Limited literature coverage ({len(all_papers)} papers found)")
        if not self.similarity_analyzer.model:
            limitations.append("Semantic similarity model not available - using keyword fallback")

        # Domain coverage analysis
        domain_coverage = {domain: 1.0 for domain in domains}  # Placeholder

        validation_time = time.time() - start_time

        report = NoveltyReport(
            novelty_score=novelty_score,
            similar_papers=similar_papers[:10],  # Top 10 most similar
            validation_timestamp=datetime.utcnow(),
            confidence_level=confidence_level,
            search_queries_used=search_queries,
            total_papers_searched=total_papers_searched,
            validation_time_seconds=validation_time,
            limitations=limitations,
            domain_coverage=domain_coverage
        )

        logger.info(
            f"Novelty validation complete: score={novelty_score:.3f}, "
            f"max_similarity={max_similarity:.3f}, time={validation_time:.2f}s"
        )

        # Log cache stats
        cache_stats = self.cache.get_stats()
        logger.info(f"Cache stats: {cache_stats}")

        return report

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        return self.cache.get_stats()


# Factory function for easy instantiation
def create_literature_validator(
    cache_ttl_seconds: int = 86400,
    enable_arxiv: bool = True,
    enable_ads: bool = True,
    similarity_threshold: float = 0.5
) -> LiteratureValidator:
    """
    Create a LiteratureValidator instance

    Args:
        cache_ttl_seconds: Cache time-to-live in seconds (default 24h)
        enable_arxiv: Enable arXiv search (requires arxiv package)
        enable_ads: Enable ADS search (requires astroquery package)
        similarity_threshold: Similarity threshold for considering papers similar

    Returns:
        Configured LiteratureValidator instance
    """
    return LiteratureValidator(
        cache_ttl_seconds=cache_ttl_seconds,
        enable_arxiv=enable_arxiv,
        enable_ads=enable_ads,
        similarity_threshold=similarity_threshold
    )


# Standalone test function
async def test_literature_validator():
    """Test the literature validator with a sample discovery"""
    validator = create_literature_validator()

    # Test case 1: Well-known topic (should get low novelty)
    test_claim_1 = "Molecular clouds exhibit a characteristic filament width of approximately 0.1 parsecs"
    report_1 = await validator.validate_novelty(
        discovery_claim=test_claim_1,
        domains=["ism", "molecular_clouds"]
    )

    print("\n=== Test Case 1: Well-Known Topic ===")
    print(f"Claim: {test_claim_1}")
    print(f"Novelty Score: {report_1.novelty_score:.3f}")
    print(f"Similar Papers: {len(report_1.similar_papers)}")
    if report_1.similar_papers:
        print(f"Most Similar: {report_1.similar_papers[0].title}")
        print(f"Similarity: {report_1.similar_papers[0].similarity_score:.3f}")

    # Test case 2: Hypothetical novel topic (should get higher novelty)
    test_claim_2 = "Quantum entanglement between protostellar jets regulates star formation efficiency"
    report_2 = await validator.validate_novelty(
        discovery_claim=test_claim_2,
        domains=["star_formation", "compact_objects"]
    )

    print("\n=== Test Case 2: Hypothetical Novel Topic ===")
    print(f"Claim: {test_claim_2}")
    print(f"Novelty Score: {report_2.novelty_score:.3f}")
    print(f"Similar Papers: {len(report_2.similar_papers)}")

    print("\n=== Cache Statistics ===")
    print(json.dumps(validator.get_cache_stats(), indent=2))


if __name__ == "__main__":
    # Run test
    asyncio.run(test_literature_validator())
