"""
ASTRA Astronomical Literature Integration System
=============================================

Phase 2.3: Literature integration and context for astronomical claims.

This system helps ASTRA connect discoveries with existing astronomical research,
identify conflicts with known science, and place findings in proper context.

Key Capabilities:
- Literature search and matching
- Known phenomenon identification
- Conflict detection with established science
- Novelty assessment
- Reference generation
- Scientific context building

Date: 2025-06-29
Phase: 2.3 - Astronomical Literature Integration
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from collections import defaultdict


class Literature_Relationship(Enum):
    """Types of relationships with existing literature"""
    SUPPORTS = "supports"           # Finding supports previous work
    CONTRADICTS = "contradicts"     # Finding contradicts established science
    EXTENDS = "extends"             # Finding extends previous work
    REFINES = "refines"             # Finding refines previous results
    INDEPENDENT = "independent"     # Finding independent of previous work
    CONFIRMS = "confirms"           # Finding confirms previous predictions
    NOVEL = "novel"                # Finding represents novel discovery


class Novelty_Level(Enum):
    """Level of novelty for astronomical findings"""
    ESTABLISHED = "established"     # Already known phenomenon
    INCREMENTAL = "incremental"     # Small advance over known
    SIGNIFICANT = "significant"     # Notable advance
    BREAKTHROUGH = "breakthrough"   # Major new discovery
    PARADIGM_SHIFT = "paradigm"    # Challenges fundamental understanding


@dataclass
class Literature_Reference:
    """Reference to astronomical literature"""
    authors: str
    title: str
    year: int
    journal: str
    arxiv_id: Optional[str] = None
    ads_bibcode: Optional[str] = None
    doi: Optional[str] = None
    relationship: Literature_Relationship = Literature_Relationship.INDEPENDENT
    relevance_score: float = 0.5  # 0.0 to 1.0


@dataclass
class Literature_Analysis_Result:
    """Result of literature analysis for an astronomical claim"""
    claim: str
    related_papers: List[Literature_Reference]
    known_phenomena: List[str]
    conflicting_results: List[str]
    supporting_results: List[str]
    novelty_assessment: Novelty_Level
    context_gaps: List[str]
    suggested_references: List[str]
    publication_context: str


class Astronomical_Literature_Integrator:
    """
    System for integrating astronomical claims with existing literature.

    This helps ASTRA place discoveries in scientific context and identify
    what is truly novel versus established knowledge.
    """

    def __init__(self):
        # Simulated astronomical literature database
        # In production, this would connect to real ADS/arXiv/SIMBAD databases
        self.astronomical_literature = self._initialize_literature_database()

        # Known astronomical phenomena database
        self.known_phenomena = {
            'stellar': [
                "Main sequence stars follow mass-luminosity relation L ∝ M^3.5",
                "HR diagram structure shows evolutionary sequences",
                "Stellar lifetimes scale as t ∝ M/L",
                "Stellar populations classified by metallicity and age"
            ],
            'galactic': [
                "Galaxy rotation curves show evidence for dark matter",
                "Star formation follows Kennicutt-Schmidt law",
                "Galaxy populations show mass-metallicity relation",
                "Galaxy formation occurs hierarchially"
            ],
            'cosmology': [
                "Universe age 13.8 Gyr in ΛCDM model",
                "Hubble constant ~70 km/s/Mpc",
                "Dark energy accelerates cosmic expansion",
                "CMB fluctuations seed large-scale structure"
            ],
            'exoplanets': [
                "Exoplanet occurrence rate correlates with stellar metallicity",
                "Hot Jupiters preferentially orbit metal-rich stars",
                "Super-Earths common in galaxy",
                "Planet formation requires >5 Myr timescales"
            ],
            'observational': [
                "Gaia provides microarcsecond astrometry",
                "JWST observes in infrared with unprecedented sensitivity",
                "LSST will survey billions of objects",
                "ALMA achieves sub-arcsecond resolution at mm wavelengths"
            ]
        }

    def _initialize_literature_database(self) -> Dict[str, List[Dict]]:
        """Initialize simulated literature database"""
        # Key papers in different astronomical domains
        literature_db = {
            'stellar_astrophysics': [
                {
                    'authors': 'Kepler et al.',
                    'title': 'The discovery of correlations in stellar spectra',
                    'year': 2019,
                    'journal': 'Astronomy & Astrophysics',
                    'key_finding': 'Correlations between stellar parameters used in classification',
                    'methodology': 'Statistical analysis of large stellar samples'
                },
                {
                    'authors': 'Hekker et al.',
                    'title': 'Stellar multiplicity and its impact on stellar classification',
                    'year': 2023,
                    'journal': 'Monthly Notices of the RAS',
                    'key_finding': 'Binary stars affect classification accuracy',
                    'methodology': 'Gaia data analysis'
                }
            ],
            'galactic_astronomy': [
                {
                    'authors': 'Bigiel et al.',
                    'title': 'The STARSMOUTH project: A high-resolution survey of nearby galaxies',
                    'year': 2023,
                    'journal': 'Astrophysical Journal',
                    'key_finding': 'Star formation laws vary with galactic environment',
                    'methodology': 'Multi-wavelength photometric analysis'
                },
                {
                    'authors': 'Mocz et al.',
                    'title': 'Beyond the Standard ΛCDM Model',
                    'year': 2024,
                    'journal': 'Annual Review of Astronomy and Astrophysics',
                    'key_finding': 'Alternative cosmological models test ΛCDM',
                    'methodology': 'Large-scale structure analysis'
                }
            ],
            'computational_methods': [
                {
                    'authors': 'Vasconcellos et al.',
                    'title': 'Computational performance optimizations for astronomical data analysis',
                    'year': 2023,
                    'journal': 'Astronomy and Computing',
                    'key_finding': 'Optimized algorithms improve analysis efficiency',
                    'methodology': 'Benchmarking of computational approaches'
                },
                {
                    'authors': 'Breiman et al.',
                    'title': 'Random forests and data mining in astronomical surveys',
                    'year': 2022,
                    'journal': 'Monthly Notices of the RAS',
                    'key_finding': 'Machine learning methods for automated classification',
                    'methodology': 'Data mining and machine learning'
                }
            ],
            'causal_discovery': [
                {
                    'authors': 'Runge et al.',
                    'title': 'Detecting causal associations in large time series datasets',
                    'year': 2019,
                    'journal': 'Proceedings of the National Academy of Sciences',
                    'key_finding': 'Causal discovery methods find associations in complex systems',
                    'methodology': 'PCMCI algorithm for causal discovery'
                },
                {
                    'authors': 'Scibior et al.',
                    'title': 'Bidirectional causal discovery and PC algorithm',
                    'year': 2024,
                    'journal': 'Advances in Neural Information Processing Systems',
                    'key_finding': 'Improved algorithms for bidirectional causal structure learning',
                    'methodology': 'Comparative algorithm analysis'
                }
            ]
        }

        return literature_db

    def analyze_literature_context(self, claim: str,
                                 claim_context: Optional[Dict[str, Any]] = None) -> Literature_Analysis_Result:
        """
        Analyze the literature context for an astronomical claim.

        This identifies related work, conflicts with established science, and
        assesses the novelty of the claim.
        """
        claim_context = claim_context or {}

        # Search for related literature
        related_papers = self._search_literature(claim, claim_context)

        # Identify known phenomena
        known_phenomena = self._identify_known_phenomena(claim)

        # Find conflicts with established science
        conflicting_results = self._find_conflicts(claim, related_papers)

        # Find supporting results
        supporting_results = self._find_support(claim, related_papers)

        # Assess novelty
        novelty_assessment = self._assess_novelty(claim, related_papers, known_phenomena)

        # Identify context gaps
        context_gaps = self._identify_context_gaps(claim, related_papers)

        # Suggest references
        suggested_references = self._suggest_references(claim, related_papers)

        # Generate publication context
        publication_context = self._generate_publication_context(claim, related_papers, novelty_assessment)

        return Literature_Analysis_Result(
            claim=claim,
            related_papers=related_papers,
            known_phenomena=known_phenomena,
            conflicting_results=conflicting_results,
            supporting_results=supporting_results,
            novelty_assessment=novelty_assessment,
            context_gaps=context_gaps,
            suggested_references=suggested_references,
            publication_context=publication_context
        )

    def _search_literature(self, claim: str, context: Dict[str, Any]) -> List[Literature_Reference]:
        """Search for related astronomical literature"""
        related_papers = []
        claim_lower = claim.lower()

        # Determine relevant domains
        relevant_domains = []
        if 'star' in claim_lower or 'stellar' in claim_lower:
            relevant_domains.extend(['stellar_astrophysics'])
        if 'galaxy' in claim_lower or 'galactic' in claim_lower:
            relevant_domains.extend(['galactic_astronomy'])
        if 'optimization' in claim_lower or 'speedup' in claim_lower or 'performance' in claim_lower:
            relevant_domains.extend(['computational_methods', 'causal_discovery'])
        if 'causal' in claim_lower or 'discovery' in claim_lower:
            relevant_domains.extend(['causal_discovery'])

        # Search each relevant domain
        for domain in relevant_domains:
            if domain in self.astronomical_literature:
                for paper in self.astronomical_literature[domain]:
                    # Check if paper is relevant
                    if self._is_paper_relevant(claim, paper):
                        reference = Literature_Reference(
                            authors=paper['authors'],
                            title=paper['title'],
                            year=paper['year'],
                            journal=paper['journal'],
                            relationship=self._determine_relationship(claim, paper),
                            relevance_score=self._calculate_relevance(claim, paper)
                        )
                        related_papers.append(reference)

        return related_papers

    def _is_paper_relevant(self, claim: str, paper: Dict[str, Any]) -> bool:
        """Determine if a paper is relevant to the claim"""
        claim_lower = claim.lower()
        paper_lower = str(paper).lower()

        # Check for keyword overlap
        claim_keywords = set(claim_lower.split())
        paper_keywords = set(paper_lower.split())

        # Calculate overlap
        overlap = claim_keywords.intersection(paper_keywords)

        # Sufficient overlap indicates relevance
        return len(overlap) >= 3

    def _determine_relationship(self, claim: str, paper: Dict[str, Any]) -> Literature_Relationship:
        """Determine relationship between claim and paper"""
        claim_lower = claim.lower()
        key_finding = paper.get('key_finding', '').lower()

        # Determine relationship based on claim type
        if 'discovered' in claim_lower or 'found' in claim_lower:
            if 'confirms' in key_finding or 'supports' in key_finding:
                return Literature_Relationship.SUPPORTS
            elif 'contradicts' in key_finding or 'challenges' in key_finding:
                return Literature_Relationship.CONTRADICTS
            elif 'extends' in key_finding or 'builds on' in key_finding:
                return Literature_Relationship.EXTENDS

        elif 'optimization' in claim_lower or 'speedup' in claim_lower:
            if 'optimization' in key_finding or 'performance' in key_finding:
                return Literature_Relationship.SUPPORTS
            elif 'benchmark' in key_finding:
                return Literature_Relationship.REFINES

        return Literature_Relationship.INDEPENDENT

    def _calculate_relevance(self, claim: str, paper: Dict[str, Any]) -> float:
        """Calculate relevance score between claim and paper"""
        claim_words = set(claim.lower().split())
        paper_content = f"{paper['title']} {paper.get('key_finding', '')} {paper.get('methodology', '')}"
        paper_words = set(paper_content.lower().split())

        # Calculate overlap
        overlap = claim_words.intersection(paper_words)

        # Calculate relevance based on overlap proportion
        if len(claim_words) > 0:
            relevance = len(overlap) / len(claim_words)
        else:
            relevance = 0.0

        return min(1.0, relevance * 2)  # Boost relevance score

    def _identify_known_phenomena(self, claim: str) -> List[str]:
        """Identify if claim describes known astronomical phenomena"""
        known = []
        claim_lower = claim.lower()

        # Check against known phenomena database
        for domain, phenomena in self.known_phenomena.items():
            for phenomenon in phenomena:
                # Check if claim describes known phenomenon
                if any(phrase in claim_lower for phrase in ['new', 'novel', 'first', 'unprecedented']):
                    # Claim suggests novelty
                    continue

                # Simple keyword matching for known phenomena
                phenomenon_lower = phenomenon.lower()
                if any(word in phenomenon_lower for word in claim_lower.split()):
                    known.append(phenomenon)

        return known

    def _find_conflicts(self, claim: str, related_papers: List[Literature_Reference]) -> List[str]:
        """Find conflicts with established astronomical science"""
        conflicts = []

        for paper in related_papers:
            if paper.relationship == Literature_Relationship.CONTRADICTS:
                conflicts.append(f"Conflicts with {paper.authors} ({paper.year}): {paper.title}")

        # Check for conflicts with known physical constraints
        claim_lower = claim.lower()

        # Temperature conflicts
        if any(word in claim_lower for word in ['200 k', '2000 k', 'below 3000k']):
            conflicts.append("Stellar temperatures below main sequence minimum (~3000 K)")

        # Mass conflicts
        if '0.05 m_sun' in claim_lower or 'below 0.08' in claim_lower:
            conflicts.append("Stellar mass below hydrogen burning limit (0.08 M_sun)")

        # Age conflicts
        if 'older than 13.8 gyr' in claim_lower or 'older than universe' in claim_lower:
            conflicts.append("Age exceeds universe age (13.8 Gyr)")

        return conflicts

    def _find_support(self, claim: str, related_papers: List[Literature_Reference]) -> List[str]:
        """Find supporting evidence in literature"""
        support = []

        for paper in related_papers:
            if paper.relationship in [Literature_Relationship.SUPPORTS, Literature_Relationship.CONFIRMS]:
                support.append(f"Supported by {paper.authors} ({paper.year}): {paper.title}")

        return support

    def _assess_novelty(self, claim: str, related_papers: List[Literature_Reference],
                       known_phenomena: List[str]) -> Novelty_Level:
        """Assess the novelty level of the claim"""
        claim_lower = claim.lower()

        # Check for novelty indicators
        novelty_indicators = ['new', 'novel', 'first', 'unprecedented', 'never before seen']
        has_novelty = any(indicator in claim_lower for indicator in novelty_indicators)

        # Check if conflicts with established science
        has_conflicts = any('conflict' in ref.lower() for ref in related_papers if ref.relationship == Literature_Relationship.CONTRADICTS)

        # Check extent of related work
        related_work_count = len(related_papers)

        # Assess novelty
        if has_conflicts:
            return Novelty_Level.PARADIGM_SHIFT  # Conflicts established science
        elif has_novelty and related_work_count == 0:
            return Novelty_Level.BREAKTHROUGH  # Very novel with no context
        elif has_novelty and related_work_count < 3:
            return Novelty_Level.SIGNIFICANT  # Notable advance
        elif related_work_count < 5:
            return Novelty_Level.INCREMENTAL  # Small advance
        else:
            return Novelty_Level.ESTABLISHED  # Well-established

    def _identify_context_gaps(self, claim: str, related_papers: List[Literature_Reference]) -> List[str]:
        """Identify gaps in astronomical context"""
        gaps = []
        claim_lower = claim.lower()

        # Check for missing context
        context_elements = [
            ('theoretical context', ['theory', 'model', 'framework', 'mechanism']),
            ('observational capabilities', ['telescope', 'instrument', 'detection', 'sensitivity']),
            ('statistical methods', ['statistics', 'uncertainty', 'error analysis', 'significance']),
            ('previous findings', ['previous', 'earlier', 'prior', 'known']),
            ('comparative analysis', ['compare', 'versus', 'relative to', 'similar to'])
        ]

        for context_name, context_keywords in context_elements:
            if not any(keyword in claim_lower for keyword in context_keywords):
                gaps.append(f"Missing {context_name}")

        return gaps

    def _suggest_references(self, claim: str, related_papers: List[Literature_Reference]) -> List[str]:
        """Suggest relevant astronomical references"""
        suggestions = []

        # Suggest fundamental references based on claim type
        claim_lower = claim.lower()

        if 'stellar' in claim_lower:
            suggestions.extend([
                "Kepler et al. (2019) for stellar correlations",
                "Hekker et al. (2023) for stellar multiplicity effects"
            ])

        if 'optimization' in claim_lower or 'performance' in claim_lower:
            suggestions.extend([
                "Vasconcellos et al. (2023) for computational optimizations",
                "Breiman et al. (2022) for machine learning methods"
            ])

        if 'causal' in claim_lower:
            suggestions.extend([
                "Runge et al. (2019) for causal discovery methods",
                "Scibior et al. (2024) for bidirectional causal discovery"
            ])

        return suggestions

    def _generate_publication_context(self, claim: str, related_papers: List[Literature_Reference],
                                   novelty: Novelty_Level) -> str:
        """Generate publication context summary"""
        context_parts = []

        if related_papers:
            context_parts.append(f"This work relates to {len(related_papers)} previous publications")

        if novelty == Novelty_Level.PARADIGM_SHIFT:
            context_parts.append("and challenges established astronomical understanding")
        elif novelty == Novelty_Level.BREAKTHROUGH:
            context_parts.append("and represents a potentially significant advance")
        elif novelty == Novelty_Level.ESTABLISHED:
            context_parts.append("and aligns with established astronomical knowledge")

        return " ".join(context_parts) if context_parts else "This work requires better astronomical context"


class Literature_Learning_System:
    """
    System for learning astronomical literature during idle moments.

    This helps ASTRA build knowledge of important astronomical papers
    and research findings systematically.
    """

    def __init__(self):
        self.literature_integrator = Astronomical_Literature_Integrator()
        self.read_papers = set()
        self.paper_summaries = {}

    def learn_key_paper(self, domain: str, paper_index: int) -> Dict[str, Any]:
        """Learn about a key astronomical paper"""
        # Get paper from literature database
        if domain in self.literature_integrator.astronomical_literature:
            papers = self.literature_integrator.astronomical_literature[domain]

            if 0 <= paper_index < len(papers):
                paper = papers[paper_index]

                # Store as read
                paper_id = f"{domain}_{paper_index}"
                self.read_papers.add(paper_id)

                # Create summary
                summary = {
                    'authors': paper['authors'],
                    'title': paper['title'],
                    'year': paper['year'],
                    'key_finding': paper['key_finding'],
                    'methodology': paper['methodology'],
                    'domain': domain
                }

                self.paper_summaries[paper_id] = summary

                return summary

        return None

    def get_learning_plan(self, time_available: int = 10) -> List[str]:
        """Get literature learning plan for idle moments"""
        plan = []
        time_per_paper = 3  # 3 minutes per paper

        papers_to_read = time_available // time_per_paper

        # Prioritize domains
        domain_priority = [
            'stellar_astrophysics',
            'galactic_astronomy',
            'computational_methods',
            'causal_discovery',
            'cosmology'
        ]

        papers_read = 0
        for domain in domain_priority:
            if papers_read >= papers_to_read:
                break

            if domain in self.literature_integrator.astronomical_literature:
                paper_count = len(self.literature_integrator.astronomical_literature[domain])
                papers_available = paper_count - sum(1 for pid in self.read_papers if pid.startswith(domain))

                if papers_available > 0:
                    papers_to_read = min(papers_available, papers_to_read - papers_read)
                    for i in range(papers_to_read):
                        plan.append(f"{domain}: paper {i}")

                    papers_read += papers_to_read

        return plan


# Convenience function
def analyze_literature_context(claim: str, context: Dict[str, Any] = None) -> Literature_Analysis_Result:
    """Analyze literature context for an astronomical claim"""
    integrator = Astronomical_Literature_Integrator()
    return integrator.analyze_literature_context(claim, context)


if __name__ == "__main__":
    # Example usage
    print("ASTRA Astronomical Literature Integrator - Phase 2.3")
    print("=" * 60)

    # Test with my BIODISC claim
    test_claim = "Our BIODISC optimizations achieve 3-10x speedup for astronomical discoveries"

    analysis = analyze_literature_context(test_claim)

    print(f"Claim: {analysis.claim}")
    print(f"Novelty Assessment: {analysis.novelty_assessment.value}")

    print(f"\nRelated Papers: {len(analysis.related_papers)}")
    for paper in analysis.related_papers:
        print(f"  {paper.authors} ({paper.year}): {paper.title[:50]}...")

    print(f"\nKnown Phenomena: {analysis.known_phenomena}")

    print(f"\nConflicting Results: {analysis.conflicting_results}")

    print(f"\nSupporting Results: {analysis.supporting_results}")

    print(f"\nContext Gaps: {analysis.context_gaps}")

    print(f"\nSuggested References: {analysis.suggested_references}")

    print(f"\nPublication Context: {analysis.publication_context}")

    print("\n" + "=" * 60)
    print("Phase 2.3 complete: Literature integration operational")