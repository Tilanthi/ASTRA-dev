"""
arXiv Integration Module for STAR-Learn

This module enables continuous learning from scientific literature through:
1. arXiv API integration for paper retrieval
2. Paper content extraction and summarization
3. Scientific concept extraction
4. Citation network analysis
5. Trend detection in scientific fields
6. Knowledge extraction from papers

Version: 1.0.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import re
import json


class PaperCategory(Enum):
    """arXiv paper categories"""
    PHYSICS = "physics"
    ASTRO_PH = "astro-ph"  # Astrophysics
    CS_AI = "cs.AI"  # Artificial Intelligence
    CS_LG = "cs.LG"  # Machine Learning
    MATH = "math"
    Q_BIO = "q-bio"  # Quantitative Biology
    STAT = "stat"
    HEPTH = "hep-th"  # High Energy Physics
    COND_MAT = "cond-mat"  # Condensed Matter


@dataclass
class ArxivPaper:
    """Represents an arXiv paper"""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: str
    updated: str
    pdf_url: str
    summary: str = ""
    key_concepts: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    extracted_knowledge: Dict = field(default_factory=dict)


@dataclass
class ScientificConcept:
    """A scientific concept extracted from literature"""
    name: str
    definition: str
    domain: str
    related_concepts: List[str]
    papers: List[str]  # arXiv IDs
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ResearchTrend:
    """Trend in scientific research"""
    topic: str
    growth_rate: float
    papers_count: int
    time_span: str
    emerging_concepts: List[str]


# =============================================================================
# Simulated arXiv API (for when real API unavailable)
# =============================================================================
class SimulatedArxivAPI:
    """Simulated arXiv API with curated papers for testing."""

    def __init__(self):
        """Initialize with simulated papers."""
        self.papers = self._initialize_papers()

    def _initialize_papers(self) -> Dict[str, ArxivPaper]:
        """Initialize with high-quality scientific papers."""
        papers = {}

        # Astrophysics Papers
        papers['2301.00001'] = ArxivPaper(
            arxiv_id='2301.00001',
            title='Observational Evidence for Dark Matter Distribution in Galaxy Clusters',
            authors=['J. Smith', 'A. Johnson', 'M. Williams'],
            abstract='We present new observational evidence for the distribution of dark matter in galaxy clusters using gravitational lensing techniques. Our analysis of 50 clusters shows that dark matter profiles follow Navarro-Frenk-White (NFW) distribution with concentration parameters correlated with cluster mass.',
            categories=['astro-ph.CO', 'astro-ph.GA'],
            published='2023-01-01',
            updated='2023-01-15',
            pdf_url='https://arxiv.org/pdf/2301.00001.pdf',
            key_concepts=['dark_matter', 'gravitational_lensing', 'galaxy_clusters', 'NFW_profile'],
            citations=['2101.00001', '2001.00002']
        )

        papers['2301.00002'] = ArxivPaper(
            arxiv_id='2301.00002',
            title='Machine Learning for Exoplanet Detection in Kepler Data',
            authors=['E. Chen', 'R. Kumar', 'S. Lopez'],
            abstract='We demonstrate improved exoplanet detection using deep neural networks on Kepler mission data. Our architecture achieves 99.2% precision in identifying transit signals, reducing false positives by 40% compared to traditional methods.',
            categories=['astro-ph.EP', 'cs.LG'],
            published='2023-01-02',
            updated='2023-01-10',
            pdf_url='https://arxiv.org/pdf/2301.00002.pdf',
            key_concepts=['exoplanets', 'machine_learning', 'transit_photometry', 'kepler_mission'],
            citations=['2201.00005']
        )

        papers['2301.00003'] = ArxivPaper(
            arxiv_id='2301.00003',
            title='Causal Inference for Gravitational Wave Parameter Estimation',
            authors=['P. Zhang', 'L. Garcia', 'D. Brown'],
            abstract='We apply causal inference methods to improve gravitational wave parameter estimation. By incorporating causal structure into the inference framework, we reduce degeneracies and improve mass and spin measurements by 35%.',
            categories=['astro-ph.HE', 'gr-qc', 'stat.ML'],
            published='2023-01-03',
            updated='2023-01-12',
            pdf_url='https://arxiv.org/pdf/2301.00003.pdf',
            key_concepts=['gravitational_waves', 'causal_inference', 'parameter_estimation', 'LIGO'],
            citations=['2105.00010']
        )

        # Physics Papers
        papers['2301.00004'] = ArxivPaper(
            arxiv_id='2301.00004',
            title='Conservation Laws in Quantum Field Theory: A New Approach',
            authors=['M. Anderson', 'K. Patel', 'T. Suzuki'],
            abstract='We present a novel framework for identifying conservation laws in quantum field theories using algebraic geometry. Our method discovers hidden symmetries that were previously unknown, leading to new conserved quantities.',
            categories=['hep-th', 'math-ph'],
            published='2023-01-04',
            updated='2023-01-14',
            pdf_url='https://arxiv.org/pdf/2301.00004.pdf',
            key_concepts=['conservation_laws', 'quantum_field_theory', 'symmetries', 'algebraic_geometry'],
            citations=['2201.00020', '2101.00030']
        )

        papers['2301.00005'] = ArxivPaper(
            arxiv_id='2301.00005',
            title='Neural Network Solutions for Schrödinger Equation',
            authors=['H. Kim', 'J. Lee', 'S. Park'],
            abstract='We demonstrate that neural networks can efficiently solve the time-dependent Schrödinger equation for complex quantum systems. Our approach achieves 10x speedup compared to traditional numerical methods while maintaining high accuracy.',
            categories=['physics.comp-ph', 'quant-ph', 'cs.NA'],
            published='2023-01-05',
            updated='2023-01-11',
            pdf_url='https://arxiv.org/pdf/2301.00005.pdf',
            key_concepts=['neural_networks', 'schrodinger_equation', 'quantum_mechanics', 'numerical_methods'],
            citations=['2201.00025']
        )

        # Machine Learning Papers
        papers['2301.00006'] = ArxivPaper(
            arxiv_id='2301.00006',
            title='Self-Supervised Learning for Scientific Discovery',
            authors=['A. Garcia', 'B. Martinez', 'C. Rodriguez'],
            abstract='We introduce a novel self-supervised learning approach specifically designed for scientific discovery tasks. Our method learns representations that capture causal structure and physical constraints, outperforming general-purpose SSL methods on scientific benchmarks.',
            categories=['cs.LG', 'cs.AI', 'stat.ML'],
            published='2023-01-06',
            updated='2023-01-13',
            pdf_url='https://arxiv.org/pdf/2301.00006.pdf',
            key_concepts=['self_supervised_learning', 'scientific_discovery', 'causal_structure', 'representation_learning'],
            citations=['2210.00015']
        )

        papers['2301.00007'] = ArxivPaper(
            arxiv_id='2301.00007',
            title='Meta-Learning for Rapid Adaptation to New Physical Systems',
            authors=['D. Wilson', 'F. Taylor', 'G. Harris'],
            abstract='We present a meta-learning framework that rapidly adapts to new physical systems with few examples. Our approach learns to learn physical laws, achieving state-of-the-art performance on system identification tasks.',
            categories=['cs.LG', 'physics.data-an'],
            published='2023-01-07',
            updated='2023-01-16',
            pdf_url='https://arxiv.org/pdf/2301.00007.pdf',
            key_concepts=['meta_learning', 'system_identification', 'physical_laws', 'few_shot_learning'],
            citations=['2211.00020']
        )

        # Mathematics Papers
        papers['2301.00008'] = ArxivPaper(
            arxiv_id='2301.00008',
            title='Topological Methods for Data Analysis',
            authors=['L. Brown', 'N. Davis', 'O. Miller'],
            abstract='We apply topological data analysis (TDA) methods to analyze complex scientific datasets. Our approach reveals persistent topological features that correspond to underlying physical phenomena.',
            categories=['math.AT', 'cs.LG', 'stat.ME'],
            published='2023-01-08',
            updated='2023-01-17',
            pdf_url='https://arxiv.org/pdf/2301.00008.pdf',
            key_concepts=['topological_data_analysis', 'persistent_homology', 'data_science', 'scientific_computing'],
            citations=['2205.00030']
        )

        return papers

    def search(self, query: str, max_results: int = 10) -> List[ArxivPaper]:
        """Search for papers by query."""
        results = []
        query_lower = query.lower()

        for paper in self.papers.values():
            # Search in title, abstract, and concepts
            text = f"{paper.title} {paper.abstract} {' '.join(paper.key_concepts)}".lower()
            if query_lower in text:
                results.append(paper)
                if len(results) >= max_results:
                    break

        return results

    def get_recent(self, category: str = None, days: int = 30) -> List[ArxivPaper]:
        """Get recent papers."""
        cutoff = datetime.now() - timedelta(days=days)
        results = []

        for paper in self.papers.values():
            pub_date = datetime.fromisoformat(paper.published)
            if pub_date >= cutoff:
                if category is None or any(cat.startswith(category) for cat in paper.categories):
                    results.append(paper)

        return results

    def get_paper(self, arxiv_id: str) -> Optional[ArxivPaper]:
        """Get a specific paper by ID."""
        return self.papers.get(arxiv_id)

    def get_citations(self, arxiv_id: str) -> List[ArxivPaper]:
        """Get papers that cite this paper."""
        paper = self.get_paper(arxiv_id)
        if not paper:
            return []

        # Find papers that cite this one
        citing_papers = []
        for other_paper in self.papers.values():
            if arxiv_id in other_paper.citations:
                citing_papers.append(other_paper)

        return citing_papers


# =============================================================================
# Real arXiv API Implementation (Production)
# =============================================================================
try:
    import arxiv
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False
    print("Warning: arxiv package not available. Install with: pip install arxiv")


class RealArxivAPI:
    """
    Real arXiv API client with rate limiting, caching, and retry logic.

    Replaces SimulatedArxivAPI for production use.
    """

    def __init__(
        self,
        delay_seconds: float = 3.0,
        page_size: int = 100,
        max_retries: int = 3,
        enable_cache: bool = True,
        cache_ttl_seconds: int = 86400  # 24 hours
    ):
        """
        Initialize real arXiv API client.

        Args:
            delay_seconds: Delay between requests (arXiv rate limit: 3 seconds)
            page_size: Number of results per page
            max_retries: Maximum retry attempts for failed requests
            enable_cache: Enable request caching
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        if not ARXIV_AVAILABLE:
            raise ImportError("arxiv package not available. Install with: pip install arxiv")

        self.client = arxiv.Client(
            page_size=page_size,
            delay_seconds=delay_seconds,
            num_retries=max_retries
        )

        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl_seconds
        self._cache = {}  # Simple in-memory cache
        self._cache_timestamps = {}

        self.last_request_time = 0
        self.min_request_interval = delay_seconds

        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'failed_requests': 0
        }

    def _cache_key(self, query: str, max_results: int, categories: List[str] = None) -> str:
        """Generate cache key from request parameters."""
        import hashlib
        key_data = f"{query}:{max_results}:{':'.join(categories or [])}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[List[ArxivPaper]]:
        """Get results from cache if available and not expired."""
        if not self.enable_cache:
            return None

        if cache_key in self._cache:
            # Check if expired
            import time
            if time.time() - self._cache_timestamps[cache_key] < self.cache_ttl:
                self.stats['cache_hits'] += 1
                return self._cache[cache_key]
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]

        self.stats['cache_misses'] += 1
        return None

    def _store_in_cache(self, cache_key: str, results: List[ArxivPaper]):
        """Store results in cache."""
        if not self.enable_cache:
            return

        import time
        self._cache[cache_key] = results
        self._cache_timestamps[cache_key] = time.time()

    def _arxiv_result_to_paper(self, result) -> ArxivPaper:
        """Convert arXiv API result to ArxivPaper object."""
        return ArxivPaper(
            arxiv_id=result.entry_id.split('/')[-1],
            title=result.title,
            authors=[author.name for author in result.authors],
            abstract=result.summary.replace('\n', ' '),
            categories=[cat for cat in result.categories],
            published=result.published.strftime('%Y-%m-%d') if result.published else '2024-01-01',
            updated=result.updated.strftime('%Y-%m-%d') if result.updated else '2024-01-01',
            pdf_url=result.pdf_url,
            summary=result.summary.replace('\n', ' ')[:500]  # First 500 chars as summary
        )

    def search(
        self,
        query: str,
        max_results: int = 50,
        categories: Optional[List[str]] = None,
        sort_by: str = 'relevance'
    ) -> List[ArxivPaper]:
        """
        Search arXiv for papers matching query.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            categories: Optional list of arXiv categories to filter by
            sort_by: Sort order ('relevance', 'lastUpdatedDate', 'submittedDate')

        Returns:
            List of ArxivPaper objects matching the query
        """
        import time

        self.stats['total_requests'] += 1

        # Check cache
        cache_key = self._cache_key(query, max_results, categories)
        cached_results = self._get_from_cache(cache_key)
        if cached_results is not None:
            return cached_results

        # Rate limiting
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        # Build search query
        search_query = query
        if categories:
            cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
            search_query = f"({query}) AND ({cat_query})"

        try:
            # Determine sort criterion
            sort_criterion = arxiv.SortCriterion.Relevance
            if sort_by == 'lastUpdatedDate':
                sort_criterion = arxiv.SortCriterion.LastUpdatedDate
            elif sort_by == 'submittedDate':
                sort_criterion = arxiv.SortCriterion.SubmittedDate

            # Create and execute search
            search = arxiv.Search(
                query=search_query,
                max_results=max_results,
                sort_by=sort_criterion
            )

            results = []
            for result in self.client.results(search):
                paper = self._arxiv_result_to_paper(result)
                results.append(paper)

            self.last_request_time = time.time()

            # Cache results
            self._store_in_cache(cache_key, results)

            return results

        except Exception as e:
            self.stats['failed_requests'] += 1
            print(f"arXiv search failed: {e}")
            return []

    def get_recent(
        self,
        category: Optional[str] = None,
        days: int = 30,
        max_results: int = 100
    ) -> List[ArxivPaper]:
        """
        Get recent papers from the last N days.

        Args:
            category: arXiv category filter (e.g., 'astro-ph')
            days: Number of days to look back
            max_results: Maximum results to return

        Returns:
            List of recent ArxivPaper objects
        """
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(days=days)
        cutoff_date = cutoff.strftime('%Y%m%d')

        # Build date-filtered query
        query = f"submittedDate:[{cutoff_date}0000 TO *]"
        if category:
            query = f"cat:{category} AND {query}"

        return self.search(query=query, max_results=max_results)

    def get_paper(self, arxiv_id: str) -> Optional[ArxivPaper]:
        """
        Get a specific paper by arXiv ID.

        Args:
            arxiv_id: arXiv ID (e.g., '2301.00001')

        Returns:
            ArxivPaper object or None if not found
        """
        # Search for specific ID
        query = f"id:{arxiv_id}"
        results = self.search(query=query, max_results=1)

        return results[0] if results else None

    def get_citations(self, arxiv_id: str, max_results: int = 50) -> List[ArxivPaper]:
        """
        Get papers that cite the given paper.

        Note: arXiv API doesn't directly support citation search.
        This is a placeholder that uses title-based search.

        For real citation data, use ADS or Semantic Scholar APIs.

        Args:
            arxiv_id: arXiv ID of the paper
            max_results: Maximum results to return

        Returns:
            List of citing papers (placeholder implementation)
        """
        # Get the original paper to extract title
        paper = self.get_paper(arxiv_id)
        if not paper:
            return []

        # Search for papers citing this title (approximate)
        # This is not accurate - use ADS/ Semantic Scholar for real citation data
        query = f'cit BibTeX {arxiv_id.replace("v1", "")}'
        return self.search(query=query, max_results=max_results)

    def get_by_category(
        self,
        category: str,
        max_results: int = 100,
        days: int = 30
    ) -> List[ArxivPaper]:
        """
        Get recent papers from a specific category.

        Args:
            category: arXiv category (e.g., 'astro-ph.GA')
            max_results: Maximum results to return
            days: Number of days to look back

        Returns:
            List of papers in the category
        """
        return self.get_recent(category=category, days=days, max_results=max_results)

    def get_statistics(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        cache_stats = {
            'cache_size': len(self._cache),
            'cache_hit_rate': (
                self.stats['cache_hits'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            )
        }

        return {**self.stats, **cache_stats}

    def clear_cache(self):
        """Clear the request cache."""
        self._cache.clear()
        self._cache_timestamps.clear()


# =============================================================================
# Paper Analysis and Knowledge Extraction
# =============================================================================
class PaperAnalyzer:
    """Analyze papers and extract scientific knowledge."""

    def __init__(self):
        """Initialize the paper analyzer."""
        self.concepts = {}
        self.concept_network = {}

    def extract_concepts(self, paper: ArxivPaper) -> List[ScientificConcept]:
        """Extract scientific concepts from a paper."""
        concepts = []

        # Extract from key concepts
        for concept_name in paper.key_concepts:
            # Create concept
            concept = ScientificConcept(
                name=concept_name.replace('_', ' ').title(),
                definition=self._generate_definition(concept_name, paper),
                domain=self._infer_domain(paper.categories),
                related_concepts=self._find_related_concepts(concept_name, paper),
                papers=[paper.arxiv_id],
                confidence=0.8
            )
            concepts.append(concept)

            # Store in concept network
            if concept_name not in self.concepts:
                self.concepts[concept_name] = []
            self.concepts[concept_name].append(paper.arxiv_id)

        return concepts

    def extract_knowledge(self, paper: ArxivPaper) -> Dict[str, Any]:
        """Extract structured knowledge from a paper."""
        knowledge = {
            'arxiv_id': paper.arxiv_id,
            'title': paper.title,
            'domain': self._infer_domain(paper.categories),
            'claims': self._extract_claims(paper),
            'methods': self._extract_methods(paper),
            'results': self._extract_results(paper),
            'concepts': [c.replace('_', ' ') for c in paper.key_concepts],
            'novelty': self._assess_novelty(paper),
            'importance': self._assess_importance(paper)
        }

        return knowledge

    def summarize_paper(self, paper: ArxivPaper) -> str:
        """Generate a concise summary of the paper."""
        summary = f"""
**{paper.title}**

**Authors**: {', '.join(paper.authors[:3])}
**Domain**: {self._infer_domain(paper.categories)}
**Published**: {paper.published}

**Abstract Summary**:
{paper.abstract[:300]}...

**Key Concepts**: {', '.join(paper.key_concepts[:5])}

**Key Contribution**:
{self._extract_contribution(paper)}
"""
        return summary.strip()

    def _generate_definition(self, concept: str, paper: ArxivPaper) -> str:
        """Generate a definition for a concept based on paper content."""
        # Simple template-based definition
        abstract_words = paper.abstract.split()
        context_start = paper.abstract.lower().find(concept.replace('_', ' '))
        if context_start >= 0:
            context = paper.abstract[max(0, context_start):context_start+100]
            return f"A concept in {self._infer_domain(paper.categories)}: {context[:80]}..."
        return f"A concept in {self._infer_domain(paper.categories)} discussed in {paper.arxiv_id}"

    def _infer_domain(self, categories: List[str]) -> str:
        """Infer scientific domain from categories."""
        for cat in categories:
            if cat.startswith('astro-ph'):
                return 'astrophysics'
            elif cat.startswith('hep-') or cat.startswith('gr-qc'):
                return 'high_energy_physics'
            elif cat.startswith('physics.comp-ph') or cat.startswith('quant-ph'):
                return 'computational_physics'
            elif cat.startswith('cs.AI') or cat.startswith('cs.LG'):
                return 'machine_learning'
            elif cat.startswith('math'):
                return 'mathematics'
            elif cat.startswith('q-bio'):
                return 'biology'
        return 'general'

    def _find_related_concepts(self, concept: str, paper: ArxivPaper) -> List[str]:
        """Find concepts related to the given concept."""
        related = []
        for other_concept in paper.key_concepts:
            if other_concept != concept:
                related.append(other_concept.replace('_', ' '))
        return related[:3]

    def _extract_claims(self, paper: ArxivPaper) -> List[str]:
        """Extract main claims from the paper."""
        claims = []
        abstract = paper.abstract

        # Look for claim indicators
        claim_indicators = ['we show', 'we demonstrate', 'we present', 'we prove', 'we find']
        for indicator in claim_indicators:
            if indicator in abstract.lower():
                start = abstract.lower().find(indicator)
                end = start + 200
                claim = abstract[start:end].strip()
                if claim:
                    claims.append(claim[:100])

        return claims[:3]

    def _extract_methods(self, paper: ArxivPaper) -> List[str]:
        """Extract methods used in the paper."""
        methods = []

        # Look for method keywords in abstract
        method_keywords = [
            'neural network', 'deep learning', 'bayesian', 'causal inference',
            'numerical simulation', 'analytical', 'experiment', 'observation'
        ]

        for keyword in method_keywords:
            if keyword in paper.abstract.lower():
                methods.append(keyword)

        return methods

    def _extract_results(self, paper: ArxivPaper) -> List[str]:
        """Extract main results from the paper."""
        results = []

        # Look for result indicators
        result_indicators = ['our results show', 'we find that', 'achieves', 'improves by']
        abstract = paper.abstract

        for indicator in result_indicators:
            if indicator in abstract.lower():
                start = abstract.lower().find(indicator)
                end = min(start + 150, len(abstract))
                result = abstract[start:end].strip()
                if result:
                    results.append(result[:80])

        return results[:2]

    def _extract_contribution(self, paper: ArxivPaper) -> str:
        """Extract the main contribution."""
        # Find first sentence with "we" verb
        sentences = paper.abstract.split('. ')
        for sent in sentences:
            if 'we ' in sent.lower()[:10]:
                return sent.strip()
        return paper.abstract[:100]

    def _assess_novelty(self, paper: ArxivPaper) -> float:
        """Assess the novelty of the paper."""
        # Check for novelty indicators
        novelty_words = ['new', 'novel', 'first', 'unique', 'innovative', 'unprecedented']
        score = 0.0
        for word in novelty_words:
            if word in paper.title.lower() or word in paper.abstract.lower()[:200]:
                score += 0.1
        return min(score, 1.0)

    def _assess_importance(self, paper: ArxivPaper) -> float:
        """Assess the importance of the paper."""
        # Based on citations and recency
        citation_score = min(len(paper.citations) * 0.1, 0.5)

        # Recency bonus
        pub_date = datetime.fromisoformat(paper.published)
        days_old = (datetime.now() - pub_date).days
        recency_score = max(0, 1 - days_old / 365) * 0.5

        return citation_score + recency_score


# =============================================================================
# Continuous Learning System
# =============================================================================
class ContinuousLearningSystem:
    """Continuously learn from scientific literature."""

    def __init__(self):
        """Initialize the continuous learning system."""
        self.arxiv_api = SimulatedArxivAPI()
        self.analyzer = PaperAnalyzer()

        self.read_papers = []
        self.extracted_knowledge = []
        self.concepts = {}
        self.learning_history = []

    def learn_from_literature(
        self,
        domains: List[str] = None,
        n_papers: int = 10
    ) -> Dict[str, Any]:
        """Learn from recent scientific literature."""
        if domains is None:
            domains = ['astro-ph', 'physics', 'cs.LG']

        all_papers = []
        all_concepts = []
        all_knowledge = []

        for domain in domains:
            # Get recent papers
            papers = self.arxiv_api.get_recent(category=domain, days=90)
            papers = papers[:n_papers // len(domains)]

            for paper in papers:
                if paper.arxiv_id not in [p.arxiv_id for p in self.read_papers]:
                    # Analyze paper
                    concepts = self.analyzer.extract_concepts(paper)
                    knowledge = self.analyzer.extract_knowledge(paper)
                    summary = self.analyzer.summarize_paper(paper)

                    all_papers.append(paper)
                    all_concepts.extend(concepts)
                    all_knowledge.append(knowledge)

                    # Store
                    self.read_papers.append(paper)
                    self.extracted_knowledge.append(knowledge)

                    # Store concepts
                    for concept in concepts:
                        name = concept.name
                        if name not in self.concepts:
                            self.concepts[name] = concept
                        else:
                            # Update existing concept
                            self.concepts[name].papers.extend(concept.papers)
                            self.concepts[name].confidence = max(
                                self.concepts[name].confidence,
                                concept.confidence
                            )

        # Record learning
        learning_record = {
            'timestamp': datetime.now().isoformat(),
            'papers_read': len(all_papers),
            'concepts_learned': len(all_concepts),
            'knowledge_extracted': len(all_knowledge),
            'domains': domains
        }
        self.learning_history.append(learning_record)

        return {
            'papers': all_papers,
            'concepts': all_concepts,
            'knowledge': all_knowledge,
            'summary': self._generate_learning_summary(all_papers, all_concepts)
        }

    def get_concept(self, name: str) -> Optional[ScientificConcept]:
        """Get a concept by name."""
        return self.concepts.get(name)

    def search_concepts(self, query: str) -> List[ScientificConcept]:
        """Search for concepts matching query."""
        query_lower = query.lower()
        matching = []

        for concept in self.concepts.values():
            if query_lower in concept.name.lower() or query_lower in concept.definition.lower():
                matching.append(concept)

        return matching

    def get_trending_topics(self, top_n: int = 5) -> List[ResearchTrend]:
        """Get trending research topics."""
        # Count concept occurrences
        concept_counts = {}
        for concept in self.concepts.values():
            count = len(concept.papers)
            if concept.name in concept_counts:
                concept_counts[concept.name] = max(concept_counts[concept.name], count)
            else:
                concept_counts[concept.name] = count

        # Sort by frequency
        sorted_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)

        trends = []
        for name, count in sorted_concepts[:top_n]:
            concept = self.concepts[name]
            trend = ResearchTrend(
                topic=name,
                growth_rate=count / 10.0,  # Normalized
                papers_count=count,
                time_span="last 90 days",
                emerging_concepts=concept.related_concepts
            )
            trends.append(trend)

        return trends

    def _generate_learning_summary(
        self,
        papers: List[ArxivPaper],
        concepts: List[ScientificConcept]
    ) -> str:
        """Generate a summary of learning session."""
        summary = f"""
# Literature Learning Summary

## Papers Read: {len(papers)}

### Top Papers by Domain:
"""
        # Group by domain
        by_domain = {}
        for paper in papers:
            domain = self.analyzer._infer_domain(paper.categories)
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(paper)

        for domain, domain_papers in by_domain.items():
            summary += f"\n**{domain}**: {len(domain_papers)} papers\n"
            for paper in domain_papers[:2]:
                summary += f"- {paper.title[:60]}...\n"

        summary += f"\n## Concepts Learned: {len(concepts)}\n\n"
        summary += "### Key Concepts:\n"

        for concept in concepts[:5]:
            summary += f"- **{concept.name}**: {concept.definition[:60]}...\n"

        return summary


# =============================================================================
# Integration with STAR-Learn
# =============================================================================
def get_literature_learning_reward(
    discovery: Dict[str, Any],
    learning_system: ContinuousLearningSystem
) -> Tuple[float, Dict]:
    """
    Calculate reward for discoveries based on literature alignment.

    High rewards for:
    - Discoveries consistent with literature (validation)
    - Discoveries that extend literature (novelty)
    - Discoveries that connect literature concepts (synthesis)
    """
    content = discovery.get('content', '').lower()
    domain = discovery.get('domain', 'unknown')

    details = {}
    reward = 0.0

    # Search for related concepts in literature
    related_concepts = learning_system.search_concepts(content)

    if related_concepts:
        # Found related concepts in literature
        best_match = max(related_concepts, key=lambda c: c.confidence)

        # Reward for consistency with literature
        reward += 0.3 * best_match.confidence
        details['literature_match'] = best_match.name
        details['match_confidence'] = best_match.confidence

        # Bonus for extending literature
        if 'novel' in content or 'new' in content:
            reward += 0.2
            details['extension_bonus'] = True

    # Bonus for discovering things mentioned in trending topics
    trending = learning_system.get_trending_topics(top_n=10)
    for trend in trending:
        if trend.topic.lower() in content:
            reward += 0.15
            details['trending_topic'] = trend.topic
            break

    # Domain-specific bonuses
    if domain in ['astrophysics', 'physics', 'mathematics']:
        # These are well-represented in arXiv
        reward += 0.1
        details['domain_coverage'] = True

    return min(reward, 1.0), details


# =============================================================================
# Factory Functions
# =============================================================================
def create_arxiv_api(
    use_real_api: bool = True,
    enable_cache: bool = True,
    cache_ttl_seconds: int = 86400
):
    """
    Create an arXiv API client (real or simulated).

    Args:
        use_real_api: If True, use real arXiv API. Falls back to simulated if unavailable.
        enable_cache: Enable request caching
        cache_ttl_seconds: Cache time-to-live in seconds

    Returns:
        Either RealArxivAPI or SimulatedArxivAPI instance
    """
    if use_real_api and ARXIV_AVAILABLE:
        try:
            return RealArxivAPI(
                enable_cache=enable_cache,
                cache_ttl_seconds=cache_ttl_seconds
            )
        except Exception as e:
            print(f"Failed to create real arXiv API: {e}")
            print("Falling back to simulated API")

    # Fallback to simulated API
    return SimulatedArxivAPI()


def create_arxiv_integration(
    use_real_api: bool = True,
    enable_cache: bool = True,
    cache_ttl_seconds: int = 86400
) -> ContinuousLearningSystem:
    """
    Create an arXiv integration system.

    Args:
        use_real_api: If True, use real arXiv API. Falls back to simulated if unavailable.
        enable_cache: Enable request caching
        cache_ttl_seconds: Cache time-to-live in seconds

    Returns:
        ContinuousLearningSystem with configured API
    """
    api_client = create_arxiv_api(use_real_api, enable_cache, cache_ttl_seconds)
    analyzer = PaperAnalyzer()
    return ContinuousLearningSystem(api=api_client, analyzer=analyzer)


def create_paper_analyzer() -> PaperAnalyzer:
    """Create a paper analyzer."""
    return PaperAnalyzer()


def get_arxiv_availability() -> Dict[str, bool]:
    """
    Check availability of arXiv integration components.

    Returns:
        Dict with availability status of different components
    """
    return {
        'arxiv_package': ARXIV_AVAILABLE,
        'real_api_available': ARXIV_AVAILABLE,
        'simulated_api_available': True,  # Always available
        'paper_analyzer_available': True
    }
