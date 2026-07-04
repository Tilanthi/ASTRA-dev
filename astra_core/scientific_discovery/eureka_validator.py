"""
Eureka-Enhanced Literature Validator

This module integrates the Eureka detection system with literature validation
to identify genuine scientific advances rather than just field activity.

Key Changes from Standard Validator:
1. Extracts specific claims from discovery text
2. Searches for similar CLAIMS in literature, not similar topics
3. Uses Eureka detection to identify genuine advances
4. Provides detailed reasoning about novelty vs field activity

Author: ASTRA Discovery System
Date: 2026-07-03
Version: 2.0
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum

from .eureka_detector import EurekaDetector, EurekaAssessment, ScientificClaim, ClaimType
from .literature_validator import (
    LiteratureValidator, SimilarPaper, LiteratureSearchResult,
    NoveltyReport, ConfidenceLevel, ArxivClient, ADSClient,
    LiteratureCache, QUERY_OPTIMIZER_AVAILABLE
)

logger = logging.getLogger(__name__)


@dataclass
class EurekaValidationReport:
    """Comprehensive report combining literature search and Eureka detection"""
    # Original novelty report
    novelty_score: float
    similar_papers: List[SimilarPaper]
    validation_timestamp: datetime

    # Eureka detection results
    eureka_assessment: EurekaAssessment
    extracted_claims: List[ScientificClaim]

    # Search context
    search_queries_used: List[str]
    total_papers_searched: int
    field_activity_level: float  # How active the field is

    # Combined assessment
    represents_genuine_advance: bool  # True novelty vs just field activity
    potential_impact_score: float  # 0-1

    # Validation details
    validation_time_seconds: float
    limitations: List[str]
    domain_coverage: Dict[str, float]

    # Human-readable explanation
    explanation: str  # Clear explanation of why this is/isn't novel


class EurekaEnhancedValidator:
    """
    Enhanced literature validator that distinguishes between
    genuine scientific advances and mere field activity
    """

    def __init__(
        self,
        cache_ttl_seconds: int = 86400,
        enable_arxiv: bool = True,
        enable_ads: bool = True
    ):
        # Initialize standard literature validator
        self.literature_validator = LiteratureValidator(
            cache_ttl_seconds=cache_ttl_seconds,
            enable_arxiv=enable_arxiv,
            enable_ads=enable_ads
        )

        # Initialize Eureka detector
        self.eureka_detector = EurekaDetector()

        logger.info("EurekaEnhancedValidator initialized with claim extraction and Eureka detection")

    async def validate_genuine_advance(
        self,
        discovery_claim: str,
        domains: List[str],
        discovery_type: str = "general",
        max_results_per_source: int = 50
    ) -> EurekaValidationReport:
        """
        Validate whether a discovery represents a genuine scientific advance

        Key difference from standard validation:
        - Checks if SPECIFIC claim is novel, not just if field is active
        - Uses Eureka detection to identify genuine advances

        Args:
            discovery_claim: The discovery text
            domains: Astronomical domains
            discovery_type: Type of discovery
            max_results_per_source: Papers to fetch per source

        Returns:
            EurekaValidationReport with comprehensive analysis
        """
        start_time = time.time()
        logger.info(f"Starting Eureka-enhanced validation for: {discovery_claim[:100]}...")

        # Phase 1: Search literature (standard)
        logger.info("Phase 1: Searching literature...")
        literature_report = await self.literature_validator.validate_novelty(
            discovery_claim=discovery_claim,
            domains=domains,
            discovery_type=discovery_type,
            max_results_per_source=max_results_per_source
        )

        # Phase 2: Assess field activity level
        field_activity_level = self._assess_field_activity(literature_report)

        # Phase 3: Extract claims from discovery
        logger.info("Phase 2: Extracting scientific claims...")
        claims = self.eureka_detector.claim_extractor.extract_claims(discovery_claim)
        primary_claim = max(claims, key=lambda c: c.confidence) if claims else None

        # Phase 4: Eureka detection
        logger.info("Phase 3: Running Eureka detection...")
        eureka_assessment = self.eureka_detector.detect_eureka_moment(
            discovery_text=discovery_claim,
            literature_papers=literature_report.similar_papers,
            field_activity_level=field_activity_level
        )

        # Phase 5: Determine if this represents genuine advance
        represents_genuine_advance = self._is_genuine_advance(
            eureka_assessment, field_activity_level
        )

        # Phase 6: Assess potential impact
        potential_impact_score = self._assess_impact_score(
            eureka_assessment, represents_genuine_advance
        )

        # Phase 7: Generate human-readable explanation
        explanation = self._generate_explanation(
            represents_genuine_advance,
            eureka_assessment,
            literature_report,
            field_activity_level,
            len(claims)
        )

        # Compile limitations
        limitations = literature_report.limitations.copy()
        if not primary_claim:
            limitations.append("No specific claims could be extracted - low specificity")
        if len(literature_report.similar_papers) < 5:
            limitations.append(f"Limited literature coverage ({len(literature_report.similar_papers)} papers)")

        validation_time = time.time() - start_time

        report = EurekaValidationReport(
            # Original novelty metrics
            novelty_score=literature_report.novelty_score,
            similar_papers=literature_report.similar_papers,
            validation_timestamp=literature_report.validation_timestamp,

            # Eureka detection
            eureka_assessment=eureka_assessment,
            extracted_claims=claims,

            # Search context
            search_queries_used=literature_report.search_queries_used,
            total_papers_searched=literature_report.total_papers_searched,
            field_activity_level=field_activity_level,

            # Combined assessment
            represents_genuine_advance=represents_genuine_advance,
            potential_impact_score=potential_impact_score,

            # Details
            validation_time_seconds=validation_time,
            limitations=limitations,
            domain_coverage=literature_report.domain_coverage,

            # Explanation
            explanation=explanation
        )

        logger.info(
            f"Eureka-enhanced validation complete: "
            f"genuine_advance={represents_genuine_advance}, "
            f"eureka_score={eureka_assessment.eureka_score:.3f}, "
            f"field_activity={field_activity_level:.3f}"
        )

        return report

    def _assess_field_activity(self, literature_report: NoveltyReport) -> float:
        """
        Assess how active the research field is

        Returns:
            Field activity level (0-1, where 1 = very active)
        """
        # Based on number of papers found
        num_papers = len(literature_report.similar_papers)

        # More papers = more active field
        if num_papers > 50:
            return 0.9
        elif num_papers > 30:
            return 0.7
        elif num_papers > 15:
            return 0.5
        elif num_papers > 5:
            return 0.3
        else:
            return 0.1

    def _is_genuine_advance(
        self,
        eureka_assessment: EurekaAssessment,
        field_activity_level: float
    ) -> bool:
        """
        Determine if this represents a genuine advance vs just field activity

        Key: Even in active fields, specific new insights can be genuine advances
        """
        # Eureka detection already accounts for field activity
        if eureka_assessment.is_eureka:
            return True

        # Additional check: High claim novelty even in active field
        if (eureka_assessment.claim_novelty > 0.7 and
            field_activity_level > 0.6 and
            eureka_assessment.insight_quality > 0.7):
            return True

        return False

    def _assess_impact_score(
        self,
        eureka_assessment: EurekaAssessment,
        is_genuine_advance: bool
    ) -> float:
        """
        Assess potential scientific impact (0-1)
        """
        if not is_genuine_advance:
            return 0.2  # Low impact

        # Base impact from Eureka score
        impact = eureka_assessment.eureka_score * 0.6

        # Boost for certain claim types
        if eureka_assessment.matching_claims:  # Has extracted claims
            primary_claim = max(eureka_assessment.matching_claims, key=len) if isinstance(eureka_assessment.matching_claims[0], str) else None
            # This is simplified - in reality would check claim types

        return min(1.0, impact + 0.2)

    def _generate_explanation(
        self,
        represents_genuine_advance: bool,
        eureka_assessment: EurekaAssessment,
        literature_report: NoveltyReport,
        field_activity_level: float,
        num_claims: int
    ) -> str:
        """
        Generate clear human-readable explanation

        This is crucial for users to understand WHY something is/isn't novel
        """
        explanation_parts = []

        # Overall verdict
        if represents_genuine_advance:
            explanation_parts.append("✅ GENUINE SCIENTIFIC ADVANCE DETECTED")
        else:
            explanation_parts.append("❌ DOES NOT REPRESENT GENUINE ADVANCE")

        explanation_parts.append("\n" + "="*60 + "\n")

        # Key distinction: Field activity vs Claim novelty
        explanation_parts.append("KEY ANALYSIS:\n")

        explanation_parts.append(f"Field Activity Level: {field_activity_level:.2f}\n")
        if field_activity_level > 0.7:
            explanation_parts.append("  → This is a VERY ACTIVE research area\n")
            explanation_parts.append("  → Many papers on this general topic exist\n")
        else:
            explanation_parts.append("  → This is a LESS ACTIVE research area\n")
            explanation_parts.append("  → Fewer papers on this general topic\n")

        explanation_parts.append(f"\nClaim Novelty: {eureka_assessment.claim_novelty:.2f}\n")
        if eureka_assessment.claim_novelty > 0.7:
            explanation_parts.append("  → This SPECIFIC claim appears to be NOVEL\n")
            explanation_parts.append("  → Even though the field is active, this insight is new\n")
        elif eureka_assessment.claim_novelty > 0.4:
            explanation_parts.append("  → This claim appears to be PARTIALLY novel\n")
            explanation_parts.append("  → Some similar claims exist in literature\n")
        else:
            explanation_parts.append("  → This claim likely already exists in literature\n")
            explanation_parts.append("  → Similar claims have been made before\n")

        # Eureka assessment
        explanation_parts.append(f"\nEureka Score: {eureka_assessment.eureka_score:.2f}\n")
        explanation_parts.append(f"Insight Quality: {eureka_assessment.insight_quality:.2f}\n")

        # Claim extraction
        explanation_parts.append(f"\nClaim Extraction: {num_claims} claims identified\n")

        # Literature context
        num_papers = len(literature_report.similar_papers)
        explanation_parts.append(f"\nLiterature Context: {num_papers} papers found\n")

        if represents_genuine_advance and num_papers > 20:
            explanation_parts.append("  → ✅ PASS: Found novel insight DESPITE active field\n")
            explanation_parts.append("  → This represents genuine contribution to active area\n")
        elif not represents_genuine_advance and num_papers < 5:
            explanation_parts.append("  → ✅ PASS: Insufficient literature to assess\n")
            explanation_parts.append("  → May be novel but needs more literature comparison\n")
        elif not represents_genuine_advance:
            explanation_parts.append("  → ❌ FAIL: Claim does not represent new insight\n")
            explanation_parts.append("  → Similar claims already exist in literature\n")

        # Final verdict
        explanation_parts.append("\n" + "="*60 + "\n")
        explanation_parts.append("FINAL VERDICT:\n")
        if represents_genuine_advance:
            explanation_parts.append(f"CONFIDENCE: {eureka_assessment.confidence}\n")
            explanation_parts.append(f"This discovery represents a GENUINE NEW INSIGHT\n")
            explanation_parts.append(f"Potential Impact: {eureka_assessment.potential_impact}\n")
        else:
            explanation_parts.append(f"This discovery does NOT represent genuine advance\n")
            if len(eureka_assessment.matching_claims) > 0:
                explanation_parts.append(f"\nSimilar claims found:\n")
                for claim in eureka_assessment.matching_claims[:3]:
                    explanation_parts.append(f"  • {claim}\n")

        return ''.join(explanation_parts)


def create_eureka_enhanced_validator(
    cache_ttl_seconds: int = 86400,
    enable_arxiv: bool = True,
    enable_ads: bool = True
) -> EurekaEnhancedValidator:
    """
    Create Eureka-enhanced validator instance

    Args:
        cache_ttl_seconds: Cache TTL for literature searches
        enable_arxiv: Enable arXiv searches
        enable_ads: Enable ADS searches

    Returns:
        Configured EurekaEnhancedValidator
    """
    return EurekaEnhancedValidator(
        cache_ttl_seconds=cache_ttl_seconds,
        enable_arxiv=enable_arxiv,
        enable_ads=enable_ads
    )


# Test function
async def test_eureka_enhanced_validator():
    """Test the Eureka-enhanced validator"""

    validator = create_eureka_enhanced_validator()

    # Test case 1: Genuine advance in active field
    genuine_advance = """
    Analysis of 500 filamentary structures in molecular clouds reveals that
    filament widths are NOT constant at 0.1 pc as previously established, but
    instead vary systematically from 0.08±0.02 pc in high-density regions to
    0.15±0.03 pc in low-density regions. This variation strongly correlates
    with local turbulent velocity dispersion (r=0.82, p<0.001), contradicting
    the fixed-width hypothesis of Arzoumanian et al. (2011). We propose that
    filament width is regulated by sonic Mach number rather than being a
    universal constant.
    """

    print("=== Test Case 1: Genuine Advance in Active Field ===")
    report1 = await validator.validate_genuine_advance(
        discovery_claim=genuine_advance,
        domains=["ism", "molecular_clouds"],
        discovery_type="pattern_discovery"
    )

    print(f"\nRepresents Genuine Advance: {report1.represents_genuine_advance}")
    print(f"Potential Impact Score: {report1.potential_impact_score:.3f}")
    print(f"Field Activity Level: {report1.field_activity_level:.3f}")
    print(f"\nEureka Assessment:")
    print(f"  Is Eureka: {report1.eureka_assessment.is_eureka}")
    print(f"  Eureka Score: {report1.eureka_assessment.eureka_score:.3f}")
    print(f"  Claim Novelty: {report1.eureka_assessment.claim_novelty:.3f}")
    print(f"  Insight Quality: {report1.eureka_assessment.insight_quality:.3f}")

    print(f"\nExplanation:\n{report1.explanation}")

    # Test case 2: Known result in active field
    known_result = """
    Molecular cloud filaments exhibit a characteristic width of approximately
    0.1 parsecs, as observed in Herschel surveys. This width is consistent
    across diverse environments and represents a fundamental scale in
    the interstellar medium.
    """

    print("\n\n=== Test Case 2: Known Result in Active Field ===")
    report2 = await validator.validate_genuine_advance(
        discovery_claim=known_result,
        domains=["ism", "molecular_clouds"],
        discovery_type="pattern_discovery"
    )

    print(f"\nRepresents Genuine Advance: {report2.represents_genuine_advance}")
    print(f"Potential Impact Score: {report2.potential_impact_score:.3f}")
    print(f"Field Activity Level: {report2.field_activity_level:.3f}")

    print(f"\nExplanation:\n{report2.explanation}")


if __name__ == "__main__":
    asyncio.run(test_eureka_enhanced_validator())
