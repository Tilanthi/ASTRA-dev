"""
ASTRA Scientific Query Optimizer

Extracts and optimizes search queries from discovery claims for effective literature search.
The key insight is that discovery claims are often long, detailed descriptions while
literature search engines need concise, keyword-based queries.

Key Features:
- Extract key scientific terms from discovery claims
- Build effective search queries from titles and key concepts
- Remove problematic characters and formatting
- Handle equations, lists, and detailed descriptions
- Generate multiple query strategies for comprehensive search
"""

import re
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class OptimizedQuery:
    """Represents an optimized search query with metadata"""
    query: str
    strategy: str  # 'title', 'keywords', 'concepts', 'combined'
    terms: List[str]
    confidence: float  # 0-1 score of query quality
    category_specificity: int  # 0=broad, 1=moderate, 2=specific


class ScientificTermExtractor:
    """
    Extracts scientific terms and concepts from discovery claims
    """

    # Common scientific prefixes and suffixes to preserve
    SCIENTIFIC_PREFIXES = ['multi', 'inter', 'intra', 'sub', 'super', 'hyper', 'ultra']
    SCIENTIFIC_SUFFIXES = ['tion', 'ment', 'sis', 'ysis', 'scopy', 'metry', 'physics',
                           'dynamics', 'chemistry', 'ometry', 'nomy', 'genics']

    # Common stopwords in scientific contexts
    SCIENTIFIC_STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
        'with', 'from', 'by', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'it', 'its',
        'we', 'you', 'they', 'them', 'their', 'our', 'your', 'us', 'analysis', 'paper',
        'study', 'research', 'work', 'result', 'show', 'demonstrate', 'provide', 'give',
        'make', 'use', 'using', 'based', 'approach', 'method', 'technique'
    }

    def __init__(self):
        """Initialize the term extractor"""
        self.abbreviations = self._build_scientific_abbreviations()

    def _build_scientific_abbreviations(self) -> Dict[str, str]:
        """Build common scientific abbreviation mappings"""
        return {
            'ISM': 'Interstellar Medium',
            'CMB': 'Cosmic Microwave Background',
            'AGN': 'Active Galactic Nuclei',
            'SN': 'Supernovae',
            'SNe': 'Supernovae',
            'SFR': 'Star Formation Rate',
            'IMF': 'Initial Mass Function',
            'HII': 'H II',
            'HI': 'H I',
            'UV': 'ultraviolet',
            'IR': 'infrared',
            'X-ray': 'X-ray',
            'γ-ray': 'gamma-ray',
            'pc': 'parsec',
            'kpc': 'kiloparsec',
            'Mpc': 'megaparsec',
            'Gyr': 'billion years',
            'Myr': 'million years',
            'kyr': 'thousand years',
            'M_sun': 'solar mass',
            'L_sun': 'solar luminosity',
            'GHz': 'gigahertz',
            'kHz': 'kilohertz',
            'MHz': 'megahertz',
            'K': 'kelvin',
            'cm': 'centimeter',
            's': 'second',
            'yr': 'year'
        }

    def extract_title(self, discovery_claim: str) -> Optional[str]:
        """
        Extract the title/first line from a discovery claim

        Args:
            discovery_claim: Full discovery text

        Returns:
            Extracted title or None
        """
        lines = discovery_claim.strip().split('\n')
        if not lines:
            return None

        # Take first meaningful line
        first_line = lines[0].strip()

        # Remove common prefixes
        prefixes_to_remove = ['#', '*', '-', '•', '1.', '2.', 'Title:', 'Abstract:']
        for prefix in prefixes_to_remove:
            if first_line.startswith(prefix):
                first_line = first_line[len(prefix):].strip()

        # Clean up the title
        first_line = re.sub(r'\s+', ' ', first_line)  # Normalize whitespace
        first_line = re.sub(r'^[:#]+', '', first_line)  # Remove leading special chars

        # Return if it's a reasonable length (3-20 words)
        words = first_line.split()
        if 3 <= len(words) <= 20:
            return first_line

        return None

    def extract_key_terms(self, discovery_claim: str, top_n: int = 10) -> List[str]:
        """
        Extract the most important scientific terms from a discovery claim

        Args:
            discovery_claim: Full discovery text
            top_n: Number of top terms to extract

        Returns:
            List of key terms in order of importance
        """
        # Clean the text
        text = discovery_claim.lower()

        # Remove equations, numbers, and special characters
        text = re.sub(r'\([^)]*\)', ' ', text)  # Remove parenthetical content
        text = re.sub(r'\$[^$]*\$', ' ', text)  # Remove LaTeX equations
        text = re.sub(r'\d+\.?\d*', 'NUMBER', text)  # Normalize numbers
        text = re.sub(r'[^\w\s\-\+]', ' ', text)  # Keep only word chars, spaces, hyphens, plus

        # Split into words
        words = text.split()

        # Filter stopwords and short words
        significant_words = [
            word for word in words
            if len(word) > 2 and word not in self.SCIENTIFIC_STOPWORDS
        ]

        # Count word frequencies
        word_freq = Counter(significant_words)

        # Expand abbreviations
        expanded_terms = []
        for word, freq in word_freq.most_common(top_n * 2):
            if word in self.abbreviations:
                expanded = self.abbreviations[word].lower().split()
                expanded_terms.extend(expanded)
            else:
                expanded_terms.append(word)

        # Re-count with expanded terms
        expanded_freq = Counter(expanded_terms)

        # Get top terms
        top_terms = [word for word, _ in expanded_freq.most_common(top_n)]

        return top_terms

    def extract_concepts(self, discovery_claim: str) -> List[str]:
        """
        Extract key scientific concepts from discovery claim

        Args:
            discovery_claim: Full discovery text

        Returns:
            List of scientific concepts
        """
        # Look for key phrases and patterns
        concepts = []

        # Common astronomical concepts/phrases to look for
        concept_patterns = [
            r'(star formation|stellar evolution|molecular cloud)',
            r'(interstellar medium|ism|dust grain|gas dynamics)',
            r'(accretion disk|black hole|neutron star|pulsar)',
            r'(gravitational wave|gravitational lensing|dark matter)',
            r'(cosmic microwave background|cmb|inflation)',
            r'(exoplanet|planetary system|protoplanetary disk)',
            r'(galactic center|galaxy formation|large scale structure)',
            r'(supernova|nova|gamma-ray burst|x-ray binary)',
            r'(magnetic field|turbulence|shock wave)',
            r'(spectral line|emission line|absorption line)',
            r'(redshift|blueshift|doppler shift)',
            r'(jeans instability|hydrostatic equilibrium)',
            r'(nucleosynthesis|chemical evolution|metallicity)',
        ]

        text_lower = discovery_claim.lower()

        for pattern in concept_patterns:
            matches = re.findall(pattern, text_lower)
            concepts.extend(matches)

        # Remove duplicates while preserving order
        seen = set()
        unique_concepts = []
        for concept in concepts:
            if concept not in seen:
                seen.add(concept)
                unique_concepts.append(concept)

        return unique_concepts


class QueryBuilder:
    """
    Builds optimized search queries from extracted terms and concepts
    """

    def __init__(self):
        """Initialize the query builder"""
        self.term_extractor = ScientificTermExtractor()

    def build_title_query(self, discovery_claim: str) -> OptimizedQuery:
        """
        Build a query from the extracted title

        Args:
            discovery_claim: Full discovery text

        Returns:
            OptimizedQuery with title-based search
        """
        title = self.term_extractor.extract_title(discovery_claim)

        if not title:
            # Fallback to first few words
            words = discovery_claim.strip().split()[:5]
            title = ' '.join(words)

        # Clean up the title
        query = re.sub(r'[^\w\s\-]', ' ', title)
        query = re.sub(r'\s+', ' ', query).strip()

        # Extract terms
        terms = [t for t in query.split() if len(t) > 2]

        return OptimizedQuery(
            query=query,
            strategy='title',
            terms=terms,
            confidence=0.8 if title else 0.5,
            category_specificity=1
        )

    def build_keyword_query(self, discovery_claim: str, top_n: int = 6) -> OptimizedQuery:
        """
        Build a query from key terms

        Args:
            discovery_claim: Full discovery text
            top_n: Number of top terms to use

        Returns:
            OptimizedQuery with keyword-based search
        """
        key_terms = self.term_extractor.extract_key_terms(discovery_claim, top_n=top_n)

        if not key_terms:
            return OptimizedQuery(
                query="",
                strategy='keywords',
                terms=[],
                confidence=0.0,
                category_specificity=0
            )

        # Build query with AND/OR logic
        if len(key_terms) >= 3:
            # Use top 3 terms with AND for specificity
            main_terms = key_terms[:3]
            additional_terms = key_terms[3:top_n]

            if additional_terms:
                query = f"({' AND '.join(main_terms)}) AND ({' OR '.join(additional_terms)})"
            else:
                query = ' AND '.join(main_terms)
        else:
            query = ' AND '.join(key_terms)

        return OptimizedQuery(
            query=query,
            strategy='keywords',
            terms=key_terms,
            confidence=0.7,
            category_specificity=2
        )

    def build_concept_query(self, discovery_claim: str) -> OptimizedQuery:
        """
        Build a query from extracted scientific concepts

        Args:
            discovery_claim: Full discovery text

        Returns:
            OptimizedQuery with concept-based search
        """
        concepts = self.term_extractor.extract_concepts(discovery_claim)

        if not concepts:
            return OptimizedQuery(
                query="",
                strategy='concepts',
                terms=[],
                confidence=0.0,
                category_specificity=0
            )

        # Build query from concepts
        if len(concepts) >= 2:
            query = ' OR '.join(concepts[:4])  # Use OR to broaden search
        else:
            query = concepts[0]

        return OptimizedQuery(
            query=query,
            strategy='concepts',
            terms=concepts,
            confidence=0.6,
            category_specificity=1
        )

    def build_combined_query(self, discovery_claim: str) -> OptimizedQuery:
        """
        Build a combined query using title + key concepts

        Args:
            discovery_claim: Full discovery text

        Returns:
            OptimizedQuery with combined approach
        """
        title_query = self.build_title_query(discovery_claim)
        concept_query = self.build_concept_query(discovery_claim)

        if not title_query.query or not concept_query.query:
            # Fallback to whichever exists
            return title_query if title_query.query else concept_query

        # Combine title with top concept
        combined_query = f"{title_query.query} AND {concept_query.terms[0] if concept_query.terms else ''}"

        return OptimizedQuery(
            query=combined_query.strip(),
            strategy='combined',
            terms=title_query.terms + concept_query.terms,
            confidence=0.85,
            category_specificity=2
        )


class LiteratureQueryOptimizer:
    """
    Main query optimizer for literature search

    Coordinates term extraction and query building to generate
    optimized search queries from discovery claims.
    """

    def __init__(self):
        """Initialize the query optimizer"""
        self.query_builder = QueryBuilder()
        self.term_extractor = ScientificTermExtractor()

    def optimize_query(
        self,
        discovery_claim: str,
        num_strategies: int = 3
    ) -> List[OptimizedQuery]:
        """
        Generate optimized search queries from a discovery claim

        Args:
            discovery_claim: The full discovery text
            num_strategies: Number of query strategies to return

        Returns:
            List of OptimizedQuery objects, ranked by confidence
        """
        logger.info(f"Optimizing query for discovery claim: {discovery_claim[:50]}...")

        queries = []

        # Strategy 1: Title-based query (highest confidence)
        title_query = self.query_builder.build_title_query(discovery_claim)
        if title_query.query:
            queries.append(title_query)

        # Strategy 2: Combined query
        combined_query = self.query_builder.build_combined_query(discovery_claim)
        if combined_query.query and combined_query.query != title_query.query:
            queries.append(combined_query)

        # Strategy 3: Keyword query
        keyword_query = self.query_builder.build_keyword_query(discovery_claim)
        if keyword_query.query and keyword_query.query != title_query.query:
            queries.append(keyword_query)

        # Strategy 4: Concept query (lower priority)
        if num_strategies >= 4:
            concept_query = self.query_builder.build_concept_query(discovery_claim)
            if concept_query.query:
                queries.append(concept_query)

        # Sort by confidence and return top N
        queries.sort(key=lambda q: q.confidence, reverse=True)

        logger.info(f"Generated {len(queries)} optimized query strategies")
        for i, query in enumerate(queries[:num_strategies]):
            logger.info(f"  Query {i+1} ({query.strategy}): {query.query[:80]}...")

        return queries[:num_strategies]

    def get_best_query(self, discovery_claim: str) -> str:
        """
        Get the single best query for a discovery claim

        Args:
            discovery_claim: The full discovery text

        Returns:
            Optimized query string
        """
        queries = self.optimize_query(discovery_claim, num_strategies=1)
        return queries[0].query if queries else ""


def optimize_discovery_query(discovery_claim: str) -> str:
    """
    Convenience function to get the best optimized query

    Args:
        discovery_claim: The full discovery text

    Returns:
        Optimized query string
    """
    optimizer = LiteratureQueryOptimizer()
    return optimizer.get_best_query(discovery_claim)