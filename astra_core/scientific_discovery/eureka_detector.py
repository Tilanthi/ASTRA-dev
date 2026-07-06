"""
ASTRA Eureka Detector - Genuine Scientific Insight Detection

This module implements true novelty detection by identifying specific scientific claims
and validating whether they represent genuine new advances rather than just field activity.

Key Principles:
1. Extract SPECIFIC claims, not general topics
2. Search literature for similar claims, not similar topics
3. Identify Eureka moments - genuine advances in understanding
4. Distinguish between "field is active" vs "insight is novel"

Author: ASTRA Discovery System
Date: 2026-07-03
Version: 1.0
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set, Any
from datetime import datetime
from enum import Enum
import hashlib
import json
import time

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    logging.warning("NLP dependencies not available for Eureka detector")

logger = logging.getLogger(__name__)


class ClaimType(Enum):
    """Types of scientific claims"""
    NEW_PHENOMENON = "NEW_PHENOMENON"  # First observation of X
    NEW_MECHANISM = "NEW_MECHANISM"    # New explanation for known phenomenon
    NEW_METHOD = "NEW_METHOD"          # Novel way to measure/analyze X
    NEW_CONTEXT = "NEW_CONTEXT"        # Known method applied to new domain
    NEW_SCALE = "NEW_SCALE"            # First quantitative measurement of X
    NEW_RELATIONSHIP = "NEW_RELATIONSHIP"  # New correlation/pattern discovered
    NEW_CONSTRAINT = "NEW_CONSTRAINT"  # New theoretical/observational constraint
    CONTRADICTION = "CONTRADICTION"    # Contradicts established understanding


@dataclass
class ScientificClaim:
    """Represents a specific scientific claim"""
    claim_text: str
    claim_type: ClaimType
    confidence: float
    subject: str  # What is being claimed about
    predicate: str  # What is being claimed
    quantitative: bool  # Does it include numbers/measurements?
    references: List[str] = field(default_factory=list)
    context: str = ""
    extracted_from: str = ""  # Where this claim came from


@dataclass
class EurekaAssessment:
    """Assessment of whether a discovery represents a Eureka moment"""
    is_eureka: bool
    eureka_score: float  # 0-1, how strong the Eureka moment is
    claim_novelty: float  # 0-1, how novel the specific claim is
    insight_quality: float  # 0-1, quality of the scientific insight
    field_activity_level: float  # 0-1, how active the field is (context only)
    matching_claims: List[str]  # Similar claims found in literature
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    reasoning: str  # Human-readable explanation
    potential_impact: str  # Potential scientific impact
    suggested_validation: List[str]  # How to validate this discovery
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ClaimExtractor:
    """
    Extract specific scientific claims from verbose discovery text

    Principle: Most discovery text is context/methodology. The actual novel claim
    is usually 1-2 sentences that can be extracted and validated.
    """

    # Patterns that indicate specific claims
    CLAIM_INDICATORS = [
        r"we find (that )?",
        r"we show (that )?",
        r"we demonstrate (that )?",
        r"we report (that )?",
        r"results indicate (that )?",
        r"results suggest (that )?",
        r"results show (that )?",
        r"analysis reveals (that )?",
        r"observations reveal (that )?",
        r"we discover (that )?",
        r"we identify (that )?",
        r"we propose (that )?",
        r"evidence for",
        r"first (detection|observation|measurement) of",
        r"unprecedented",
        r"contrary to",
        r"unexpected",
        r"surprising",
    ]

    # Patterns that identify quantitative claims (more specific)
    QUANTITATIVE_PATTERNS = [
        r"p\s*[<]\s*0\.05",  # Statistical significance
        r"p\s*[<]\s*0\.01",
        r"n\s*[=]\s*\d+",  # Sample size
        r"r\s*[=]\s*[-+]?\d*\.?\d+",  # Correlation
        r"\d+\s*[±σ]\s*\d+",  # Measurements with uncertainty
        r"\d+\s*[±]\s*\d+",  # Simpler uncertainty notation
    ]

    # Patterns that identify relationship claims
    RELATIONSHIP_PATTERNS = [
        r"correlation (between|of)",
        r"anti-correlation",
        r"correlates with",
        r"anti-correlates with",
        r"depends on",
        r"scales with",
        r"varies with",
        r"increases with",
        r"decreases with",
    ]

    def __init__(self):
        self.compiled_indicators = [re.compile(pattern, re.IGNORECASE) for pattern in self.CLAIM_INDICATORS]
        self.compiled_quantitative = [re.compile(pattern, re.IGNORECASE) for pattern in self.QUANTITATIVE_PATTERNS]
        self.compiled_relationships = [re.compile(pattern, re.IGNORECASE) for pattern in self.RELATIONSHIP_PATTERNS]

    def extract_claims(self, discovery_text: str) -> List[ScientificClaim]:
        """
        Extract specific scientific claims from verbose discovery text

        Args:
            discovery_text: Full discovery text (usually 200-2000 words)

        Returns:
            List of extracted ScientificClaim objects
        """
        claims = []

        # Split into sentences
        sentences = self._split_into_sentences(discovery_text)

        for sentence in sentences:
            claim = self._extract_claim_from_sentence(sentence, discovery_text)
            if claim:
                claims.append(claim)

        logger.info(f"Extracted {len(claims)} claims from {len(sentences)} sentences")

        return claims

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences, handling common abbreviations"""
        # Protect common abbreviations
        text = text.replace('e.g.', 'EG__')
        text = text.replace('i.e.', 'IE__')
        text = text.replace('etc.', 'ETC__')
        text = text.replace('vs.', 'VS__')
        text = text.replace('Fig.', 'FIG__')
        text = text.replace('Sect.', 'SECT__')

        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+\s+', text)

        # Restore abbreviations
        sentences = [s.replace('EG__', 'e.g.').replace('IE__', 'i.e.')
                    .replace('ETC__', 'etc.').replace('VS__', 'vs.')
                    .replace('FIG__', 'Fig.').replace('SECT__', 'Sect.')
                    for s in sentences]

        return [s.strip() for s in sentences if len(s.strip()) > 20]

    def _extract_claim_from_sentence(self, sentence: str, full_context: str) -> Optional[ScientificClaim]:
        """Extract a claim from a single sentence"""

        # Check if this sentence contains claim indicators
        has_indicator = False
        indicator_match = None
        for pattern in self.compiled_indicators:
            match = pattern.search(sentence)
            if match:
                has_indicator = True
                indicator_match = match.group(0)
                break

        # Check if quantitative
        is_quantitative = any(pattern.search(sentence) for pattern in self.compiled_quantitative)

        # Check if relationship claim
        is_relationship = any(pattern.search(sentence) for pattern in self.compiled_relationships)

        # Prioritize sentences with claim indicators, quantitative content, or relationships
        if not (has_indicator or is_quantitative or is_relationship):
            return None

        # Determine claim type
        claim_type = self._determine_claim_type(sentence, has_indicator, is_quantitative, is_relationship)

        # Extract subject and predicate
        subject, predicate = self._extract_subject_predicate(sentence)

        # Calculate confidence based on specificity
        confidence = self._calculate_claim_confidence(sentence, is_quantitative, has_indicator)

        # Extract references if present
        references = self._extract_references(sentence, full_context)

        claim = ScientificClaim(
            claim_text=sentence,
            claim_type=claim_type,
            confidence=confidence,
            subject=subject,
            predicate=predicate,
            quantitative=is_quantitative,
            references=references,
            context=self._get_context(sentence, full_context),
            extracted_from=full_context[:100] + "..."
        )

        return claim

    def _determine_claim_type(self, sentence: str, has_indicator: bool,
                             is_quantitative: bool, is_relationship: bool) -> ClaimType:
        """Determine the type of claim"""

        sentence_lower = sentence.lower()

        # First observation/detection
        if any(word in sentence_lower for word in ['first', 'first time', 'unprecedented', 'novel']):
            return ClaimType.NEW_PHENOMENON

        # Contradiction to established understanding
        if any(word in sentence_lower for word in ['contrary', 'contradicts', 'unexpected', 'surprising', 'unlike']):
            return ClaimType.CONTRADICTION

        # Relationship claim
        if is_relationship:
            return ClaimType.NEW_RELATIONSHIP

        # New constraint
        if any(word in sentence_lower for word in ['constraint', 'limit', 'requires', 'demands']):
            return ClaimType.NEW_CONSTRAINT

        # Method claim
        if any(word in sentence_lower for word in ['method', 'technique', 'approach', 'analysis']):
            return ClaimType.NEW_METHOD

        # Default to mechanism
        return ClaimType.NEW_MECHANISM

    def _extract_subject_predicate(self, sentence: str) -> Tuple[str, str]:
        """Extract subject (what) and predicate (about what) from claim"""

        # Simple heuristic: split by common patterns
        for indicator in [' show that ', ' find that ', ' suggest that ', ' indicate that ',
                         ' reveals that ', ' demonstrates that ']:
            if indicator in sentence.lower():
                parts = sentence.lower().split(indicator)
                if len(parts) == 2:
                    subject = parts[0].strip()
                    predicate = parts[1].strip()
                    return subject, predicate

        # Fallback: first few words as subject, rest as predicate
        words = sentence.split()
        if len(words) > 5:
            subject = ' '.join(words[:5])
            predicate = ' '.join(words[5:])
        else:
            subject = sentence[:50]
            predicate = sentence[50:]

        return subject, predicate

    def _calculate_claim_confidence(self, sentence: str, is_quantitative: bool, has_indicator: bool) -> float:
        """Calculate confidence score for extracted claim (0-1)"""

        confidence = 0.5  # Base confidence

        # Quantitative claims are more specific
        if is_quantitative:
            confidence += 0.2

        # Claim indicators suggest genuine discovery
        if has_indicator:
            confidence += 0.15

        # Length check (too short or too long is suspicious)
        length = len(sentence)
        if 50 <= length <= 300:
            confidence += 0.1
        elif length < 30:
            confidence -= 0.2

        # Scientific terms increase confidence
        scientific_terms = ['analysis', 'observation', 'measurement', 'statistical',
                          'correlation', 'significant', 'hypothesis', 'theory', 'model']
        term_count = sum(1 for term in scientific_terms if term in sentence.lower())
        confidence += min(0.15, term_count * 0.03)

        return max(0.0, min(1.0, confidence))

    def _extract_references(self, sentence: str, full_context: str) -> List[str]:
        """Extract citation references from text"""

        # Find citation patterns like (Author et al. Year) or [Author et al. Year]
        patterns = [
            r'\(([A-Z][a-z]+(?:\s+et\s+al\.)?,\s*\d{4})\)',  # (Author et al., 2024)
            r'\[([A-Z][a-z]+(?:\s+et\s+al\.)?,\s*\d{4})\]',  # [Author et al., 2024]
            r'([A-Z][a-z]+\s+et\s+al\.\s*\(\d{4}\))',  # Author et al. (2024)
        ]

        references = []
        for pattern in patterns:
            matches = re.findall(pattern, full_context)
            references.extend(matches)

        return list(set(references))  # Remove duplicates

    def _get_context(self, sentence: str, full_context: str, context_window: int = 2) -> str:
        """Get surrounding sentences as context"""

        sentences = self._split_into_sentences(full_context)
        try:
            idx = sentences.index(sentence)
            start = max(0, idx - context_window)
            end = min(len(sentences), idx + context_window + 1)
            context = ' '.join(sentences[start:end])
            return context
        except ValueError:
            return full_context[:200] + "..."


class EurekaDetector:
    """
    Main Eureka detection system

    Identifies genuine new scientific insights by:
    1. Extracting specific claims from discovery text
    2. Searching literature for similar claims (not just topics)
    3. Assessing whether the claim represents genuine advance
    """

    # Timeout constants for model loading
    MODEL_LOAD_TIMEOUT = 60  # 1 minute timeout for loading models
    FALLBACK_MODEL = 'all-MiniLM-L6-v2'  # Smaller, faster fallback model

    def __init__(self):
        self.claim_extractor = ClaimExtractor()
        self.model = None
        self.model_loaded = False
        self.model_loading = False
        self.claim_embeddings_cache: Dict[str, Any] = {}

        # Don't load model during initialization - use lazy loading instead
        if NLP_AVAILABLE:
            logger.info("Eureka detector initialized - model will load on first use")

    def _load_model_with_timeout(self, timeout_seconds: int = MODEL_LOAD_TIMEOUT) -> bool:
        """
        Load sentence transformer model with timeout to prevent blocking

        Args:
            timeout_seconds: Maximum time to wait for model loading (default: 60 seconds)

        Returns:
            True if model loaded successfully, False otherwise
        """
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
                logger.info(f"Loading semantic similarity model (with {timeout_seconds}s timeout)...")
                self.model = SentenceTransformer('allenai-specter')
                self.model_loaded = True
                load_time = time.time() - start_time
                logger.info(f"✅ Loaded SPECTER model for claim comparison in {load_time:.1f}s")
                return True

            except TimeoutError as e:
                logger.warning(f"⏱️ Model loading timeout: {e}")
                return False
            except Exception as e:
                logger.warning(f"Failed to load allenai-specter: {e}")
                # Try fallback model
                try:
                    logger.info("Trying fallback model...")
                    self.model = SentenceTransformer(self.FALLBACK_MODEL)
                    self.model_loaded = True
                    load_time = time.time() - start_time
                    logger.info(f"✅ Loaded fallback model {self.FALLBACK_MODEL} in {load_time:.1f}s")
                    return True
                except Exception as e2:
                    logger.error(f"❌ Failed to load any semantic similarity model: {e2}")
                    return False
            finally:
                # Cancel alarm
                signal.alarm(0)

        except Exception as e:
            logger.error(f"Error in model loading mechanism: {e}")
            return False

    def detect_eureka_moment(
        self,
        discovery_text: str,
        literature_papers: List[Any],  # List of SimilarPaper objects
        field_activity_level: float = 0.5
    ) -> EurekaAssessment:
        """
        Detect whether a discovery represents a Eureka moment

        Args:
            discovery_text: Full discovery text
            literature_papers: Papers found in literature search
            field_activity_level: How active the field is (0-1)

        Returns:
            EurekaAssessment with comprehensive analysis
        """
        logger.info("Starting Eureka detection analysis...")

        # Step 1: Extract specific claims
        claims = self.claim_extractor.extract_claims(discovery_text)

        if not claims:
            return EurekaAssessment(
                is_eureka=False,
                eureka_score=0.0,
                claim_novelty=0.0,
                insight_quality=0.0,
                field_activity_level=field_activity_level,
                matching_claims=[],
                confidence="LOW",
                reasoning="No specific claims could be extracted from the discovery text",
                potential_impact="None - no clear claim identified",
                suggested_validation=["Refine the discovery to make a specific, testable claim"]
            )

        # Use the highest confidence claim
        primary_claim = max(claims, key=lambda c: c.confidence)

        logger.info(f"Primary claim: {primary_claim.claim_text}")
        logger.info(f"Claim type: {primary_claim.claim_type.value}")
        logger.info(f"Claim confidence: {primary_claim.confidence:.3f}")

        # Step 2: Search for similar claims in literature
        matching_claims = self._find_similar_claims_in_literature(
            primary_claim, literature_papers
        )

        # Step 3: Assess claim novelty
        claim_novelty = self._assess_claim_novelty(primary_claim, matching_claims)

        # Step 4: Assess insight quality
        insight_quality = self._assess_insight_quality(primary_claim, field_activity_level)

        # Step 5: Determine if it's a Eureka moment
        eureka_score, is_eureka = self._determine_eureka_status(
            claim_novelty, insight_quality, primary_claim
        )

        # Step 6: Generate reasoning
        reasoning = self._generate_reasoning(
            is_eureka, eureka_score, claim_novelty, insight_quality,
            primary_claim, len(matching_claims), field_activity_level
        )

        # Step 7: Assess potential impact
        potential_impact = self._assess_potential_impact(primary_claim, is_eureka)

        # Step 8: Suggest validation methods
        suggested_validation = self._suggest_validation_methods(primary_claim)

        assessment = EurekaAssessment(
            is_eureka=is_eureka,
            eureka_score=eureka_score,
            claim_novelty=claim_novelty,
            insight_quality=insight_quality,
            field_activity_level=field_activity_level,
            matching_claims=matching_claims,
            confidence=self._determine_confidence_level(eureka_score, primary_claim.confidence),
            reasoning=reasoning,
            potential_impact=potential_impact,
            suggested_validation=suggested_validation
        )

        logger.info(f"Eureka detection complete: is_eureka={is_eureka}, score={eureka_score:.3f}")

        return assessment

    def _find_similar_claims_in_literature(
        self,
        claim: ScientificClaim,
        literature_papers: List[Any]
    ) -> List[str]:
        """
        Find claims in literature that are similar to the extracted claim

        Key: This searches for similar CLAIMS, not similar topics
        """
        if not literature_papers:
            return []

        # Lazy load model on first use
        if not self.model_loaded and NLP_AVAILABLE:
            logger.info("Loading semantic similarity model for literature comparison...")
            if not self._load_model_with_timeout():
                logger.warning("Failed to load model - skipping semantic literature comparison")
                return []

        if not self.model:
            return []

        similar_claims = []

        # Embed the claim
        claim_embedding = self.model.encode(claim.claim_text, show_progress_bar=False)

        for paper in literature_papers:
            # Extract potential claims from paper abstract
            paper_claims = self._extract_claims_from_paper(paper)

            for paper_claim in paper_claims:
                # Compute semantic similarity
                claim_embedding = self.model.encode(claim.claim_text, show_progress_bar=False)
                paper_claim_embedding = self.model.encode(paper_claim, show_progress_bar=False)

                similarity = cosine_similarity([claim_embedding], [paper_claim_embedding])[0][0]

                # Only consider highly similar claims (>0.75 = very similar)
                if similarity > 0.75:
                    similar_claims.append(f"{paper.title}: {paper_claim} (similarity: {similarity:.2f})")

        return similar_claims

    def _extract_claims_from_paper(self, paper: Any) -> List[str]:
        """Extract potential claims from paper abstract"""

        # Use the same claim extractor on paper abstracts
        abstract_claims = []
        sentences = re.split(r'[.!?]+\s+', paper.abstract)

        for sentence in sentences:
            # Look for claim indicators in paper sentences
            if any(indicator in sentence.lower() for indicator in
                   ['show that', 'find that', 'demonstrate that', 'report that', 'suggest that']):
                abstract_claims.append(sentence.strip())

        return abstract_claims

    def _assess_claim_novelty(self, claim: ScientificClaim, matching_claims: List[str]) -> float:
        """
        Assess how novel the specific claim is

        Returns:
            Novelty score (0-1)
        """
        if not matching_claims:
            # No similar claims found - highly novel
            return 0.9

        # Check if any claim is VERY similar (>0.90) - likely not novel
        for match in matching_claims:
            if 'similarity:' in match:
                try:
                    similarity = float(match.split('similarity:')[1].split(')')[0].strip())
                    if similarity > 0.90:
                        return 0.1  # Claim likely already exists
                except:
                    pass

        # Some similar claims but not identical - partially novel
        return 0.5

    def _assess_insight_quality(self, claim: ScientificClaim, field_activity_level: float) -> float:
        """
        Assess the quality of the scientific insight

        Based on:
        - Claim specificity (quantitative > qualitative)
        - Claim type (contradictions > observations)
        - Claim confidence
        """
        quality = 0.5  # Base quality

        # Quantitative claims are higher quality
        if claim.quantitative:
            quality += 0.2

        # Certain claim types are higher quality
        if claim.claim_type in [ClaimType.CONTRADICTION, ClaimType.NEW_MECHANISM]:
            quality += 0.15
        elif claim.claim_type == ClaimType.NEW_PHENOMENON:
            quality += 0.1

        # Higher confidence claims are better
        quality += claim.confidence * 0.15

        # Active fields with new insights are valuable
        if field_activity_level > 0.7:
            quality += 0.1

        return min(1.0, quality)

    def _determine_eureka_status(
        self,
        claim_novelty: float,
        insight_quality: float,
        claim: ScientificClaim
    ) -> Tuple[float, bool]:
        """
        Determine if this is a Eureka moment

        Returns:
            (eureka_score, is_eureka)
        """
        # Eureka score combines novelty and quality
        eureka_score = (claim_novelty * 0.6) + (insight_quality * 0.4)

        # Is it a Eureka moment?
        is_eureka = (
            eureka_score > 0.7 and  # High overall score
            claim_novelty > 0.6 and  # Genuinely novel
            claim.confidence > 0.6  # High confidence claim
        )

        return eureka_score, is_eureka

    def _determine_confidence_level(self, eureka_score: float, claim_confidence: float) -> str:
        """Determine overall confidence level"""

        combined = (eureka_score + claim_confidence) / 2

        if combined > 0.8:
            return "HIGH"
        elif combined > 0.6:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_reasoning(
        self,
        is_eureka: bool,
        eureka_score: float,
        claim_novelty: float,
        insight_quality: float,
        claim: ScientificClaim,
        num_matching_claims: int,
        field_activity_level: float
    ) -> str:
        """Generate human-readable reasoning for the assessment"""

        parts = []

        # Overall assessment
        if is_eureka:
            parts.append(f"✅ This represents a genuine Eureka moment (score: {eureka_score:.2f})")
        else:
            parts.append(f"❌ This does not represent a Eureka moment (score: {eureka_score:.2f})")

        # Novelty assessment
        parts.append(f"\n📊 Claim Novelty: {claim_novelty:.2f}")
        if num_matching_claims == 0:
            parts.append("  • No similar claims found in literature - highly novel specific insight")
        elif num_matching_claims < 3:
            parts.append(f"  • {num_matching_claims} somewhat similar claims found - partially novel")
        else:
            parts.append(f"  • {num_matching_claims} similar claims found - low novelty")

        # Quality assessment
        parts.append(f"\n🎯 Insight Quality: {insight_quality:.2f}")
        if claim.quantitative:
            parts.append("  • Quantitative claim with measurements/statistics")
        else:
            parts.append("  • Qualitative claim - could be more specific")

        parts.append(f"  • Claim type: {claim.claim_type.value}")
        parts.append(f"  • Claim confidence: {claim.confidence:.2f}")

        # Field context
        parts.append(f"\n🔬 Field Activity Level: {field_activity_level:.2f}")
        if field_activity_level > 0.7:
            parts.append("  • Active research field - new insights are valuable")
        else:
            parts.append("  • Less active field - opportunity for new contributions")

        # Eureka criteria check
        parts.append(f"\n🎉 Eureka Criteria:")
        parts.append(f"  • Novel claim (not just active field): {'✅' if claim_novelty > 0.6 else '❌'}")
        parts.append(f"  • High quality insight: {'✅' if insight_quality > 0.7 else '❌'}")
        parts.append(f"  • Specific testable claim: {'✅' if claim.confidence > 0.6 else '❌'}")

        return '\n'.join(parts)

    def _assess_potential_impact(self, claim: ScientificClaim, is_eureka: bool) -> str:
        """Assess potential scientific impact"""

        if not is_eureka:
            return "Limited - claim does not represent significant advance"

        impact_factors = []

        if claim.claim_type == ClaimType.CONTRADICTION:
            impact_factors.append("Contradicts established understanding - high impact if validated")
        elif claim.claim_type == ClaimType.NEW_MECHANISM:
            impact_factors.append("New explanatory mechanism - contributes to theoretical understanding")
        elif claim.claim_type == ClaimType.NEW_PHENOMENON:
            impact_factors.append("First observation - opens new research direction")
        elif claim.claim_type == ClaimType.NEW_RELATIONSHIP:
            impact_factors.append("New correlation/pattern - may lead to new understanding")

        if claim.quantitative:
            impact_factors.append("Quantitative with statistical significance - testable and falsifiable")

        return ' | '.join(impact_factors) if impact_factors else "Moderate - incremental advance"

    def _suggest_validation_methods(self, claim: ScientificClaim) -> List[str]:
        """Suggest methods to validate the discovery"""

        methods = []

        # General validation
        methods.append("Search for papers that specifically address this claim")
        methods.append("Check if claim contradicts established results")

        # Type-specific validation
        if claim.claim_type == ClaimType.NEW_PHENOMENON:
            methods.append("Verify observation with independent datasets/instruments")
            methods.append("Check for alternative explanations")

        elif claim.claim_type == ClaimType.NEW_MECHANISM:
            methods.append("Test theoretical predictions")
            methods.append("Compare with existing models")

        elif claim.claim_type == ClaimType.NEW_RELATIONSHIP:
            methods.append("Test correlation with larger sample size")
            methods.append("Check for confounding variables")

        elif claim.claim_type == ClaimType.CONTRADICTION:
            methods.append("Reproduce contradictory result")
            methods.append("Verify methodology differs from prior work")

        # Quantitative claims
        if claim.quantitative:
            methods.append("Verify statistical significance and sample size")
            methods.append("Check measurement methodology and uncertainties")

        return methods


def create_eureka_detector() -> EurekaDetector:
    """Factory function to create EurekaDetector instance"""
    return EurekaDetector()


# Test function
async def test_eureka_detector():
    """Test the Eureka detector with sample discoveries"""

    detector = create_eureka_detector()

    # Test case 1: Genuine Eureka moment (contradiction to established result)
    eureka_discovery = """
    Analysis of Herschel filament observations reveals that filament widths
    are NOT constant at 0.1 pc as previously claimed, but instead vary
    systematically from 0.08 pc in high-density regions to 0.15 pc in
    low-density regions (p<0.001, n=500 filaments). This variation correlates
    strongly with local turbulent velocity dispersion (r=0.82), contradicting
    the fixed-width hypothesis of Arzoumanian et al. (2011).
    """

    # Mock literature papers (one supporting the established view)
    from dataclasses import dataclass

    @dataclass
    class MockPaper:
        title: str
        abstract: str
        authors: List[str]
        year: int

    literature = [
        MockPaper(
            title="The narrow width of interstellar filaments",
            abstract="We show that filaments in molecular clouds have a characteristic "
                     "width of 0.1 pc, independent of their column density and environment. "
                     "This result is based on Herschel observations...",
            authors=["Arzoumanian", "Andre", "Pety"],
            year=2011
        ),
        MockPaper(
            title="Filament width variations in star-forming regions",
            abstract="We investigate filament widths across different environments...",
            authors=["Smith", "Jones"],
            year=2022
        )
    ]

    print("=== Test Case 1: Contradiction to Established Result ===")
    assessment1 = detector.detect_eureka_moment(eureka_discovery, literature, field_activity_level=0.8)
    print(f"Is Eureka: {assessment1.is_eureka}")
    print(f"Eureka Score: {assessment1.eureka_score:.3f}")
    print(f"Claim Novelty: {assessment1.claim_novelty:.3f}")
    print(f"Reasoning:\n{assessment1.reasoning}")

    # Test case 2: Not a Eureka (already known)
    known_result = """
    Molecular cloud filaments exhibit a characteristic width of approximately
    0.1 parsecs, as observed in Herschel surveys. This width is consistent
    across diverse environments.
    """

    print("\n=== Test Case 2: Already Known Result ===")
    assessment2 = detector.detect_eureka_moment(known_result, literature, field_activity_level=0.9)
    print(f"Is Eureka: {assessment2.is_eureka}")
    print(f"Eureka Score: {assessment2.eureka_score:.3f}")
    print(f"Claim Novelty: {assessment2.claim_novelty:.3f}")
    print(f"Reasoning:\n{assessment2.reasoning}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_eureka_detector())
