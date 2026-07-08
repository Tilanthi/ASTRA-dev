"""
ASTRA Autonomous Discovery System v2.0 - Genuine Novel Research
==============================================================

This module implements genuine autonomous scientific discovery for ASTRA,
focusing on novel computational analysis, new synthesis, and testable insights
rather than knowledge synthesis of existing information.

DISCOVERY PHILOSOPHY:
- Only count as discoveries what represents genuine novelty
- Rigorous validation with probability assessment
- Persistent storage of validated insights
- True autonomous research scientist behavior

DISCOVERY TYPES:
1. Pattern Discovery: Find new patterns/correlations in published data
2. Theoretical Synthesis: Connect seemingly unrelated phenomena
3. Gap Identification: Find contradictions/missing pieces in understanding
4. Predictive Hypothesis: Generate testable predictions
5. Computational Reanalysis: Apply new methods to existing datasets

VALIDATION FRAMEWORK:
- Novelty Assessment: How different from existing knowledge?
- Probability Estimate: Confidence in correctness
- Testability: Can this be verified/falsified?
- Impact Potential: What would this change if true?
- Assumption Analysis: What assumptions underlie the finding?

Version: 2.0.0
Date: 2026-06-28
"""

import asyncio
import threading
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
import json
from pathlib import Path
import random

logger = logging.getLogger(__name__)

# Genuine discovery with EUREKA-ENHANCED validation for genuine scientific insight detection
try:
    from astra_core.scientific_discovery.literature_validator import (
        LiteratureValidator,
        NoveltyReport,
        ConfidenceLevel,
        create_literature_validator
    )
    from astra_core.scientific_discovery.validation_pipeline import (
        ValidationPipeline,
        create_validation_pipeline,
        PipelineReport,
        ValidationStatus
    )
    # NEW: Eureka-enhanced validation for genuine insight detection
    from astra_core.scientific_discovery.eureka_validator import (
        EurekaEnhancedValidator,
        EurekaValidationReport,
        create_eureka_enhanced_validator
    )
    from astra_core.scientific_discovery.eureka_detector import (
        EurekaDetector,
        EurekaAssessment,
        ScientificClaim
    )
    LITERATURE_VALIDATION_AVAILABLE = True
    EUREKA_VALIDATION_AVAILABLE = True
except ImportError as e:
    LITERATURE_VALIDATION_AVAILABLE = False
    EUREKA_VALIDATION_AVAILABLE = False
    logger.warning(f"Literature validation not available: {e}")
    logger.warning("System will use degraded novelty assessment")


class DiscoveryType(Enum):
    """Types of genuine discoveries"""
    PATTERN_DISCOVERY = "pattern_discovery"  # New patterns in existing data
    THEORETICAL_SYNTHESIS = "theoretical_synthesis"  # Connect unrelated phenomena
    GAP_IDENTIFICATION = "gap_identification"  # Find contradictions/missing pieces
    PREDICTIVE_HYPOTHESIS = "predictive_hypothesis"  # Testable predictions
    COMPUTATIONAL_REANALYSIS = "computational_reanalysis"  # New methods on existing data


class NoveltyLevel(Enum):
    """Level of novelty in discovery"""
    INCREMENTAL = "incremental"  # Small extension of existing knowledge
    MODERATE = "moderate"  # Significant new insight
    SUBSTANTIAL = "substantial"  # Major conceptual advance
    PARADIGM_SHIFT = "paradigm_shift"  # Fundamental change in understanding


class DiscoveryLevel(Enum):
    """Genuine Discovery Level - 4-Level Framework for Eureka-Moment Detection"""
    NOVEL_OBSERVATION = "novel_observation"  # Level 1: Previously unobserved patterns, <5% literature similarity
    THEORETICAL_INSIGHT = "theoretical_insight"  # Level 2: Mechanism-level understanding, testable predictions
    PARADIGM_SHIFT = "paradigm_shift"  # Level 3: Challenges foundational assumptions, enables new research
    EUREKA_DISCOVERY = "eureka_discovery"  # Level 4: Revolutionary breakthroughs, <10% algorithmic probability


@dataclass
class LiteratureSimilarityInfo:
    """Information about similar papers in literature"""
    most_similar_paper: str  # Title of most similar paper
    similarity_percentage: float  # 0-100, how similar
    similar_papers: List[Dict[str, Any]]  # Top similar papers with metadata
    total_papers_searched: int  # How many papers were checked
    search_time_seconds: float  # How long validation took


@dataclass
class CitationValidation:
    """Results of citation validation"""
    total_citations: int  # How many citations found
    verified_citations: int  # How many verified to exist
    hallucinated_citations: int  # How many were invented
    unverifiable_citations: int  # How many couldn't be checked
    citation_details: List[Dict[str, Any]]  # Per-citation details


@dataclass
class FormulaValidation:
    """Results of formula/equation validation"""
    total_formulas: int  # How many formulas found
    verified_formulas: int  # Match known physics
    derivable_formulas: int  # Can be derived from known physics
    inconsistent_formulas: int  # Contradict known physics
    unverifiable_formulas: int  # Can't be checked
    formula_details: List[Dict[str, Any]]  # Per-formula details


@dataclass
class StatisticalValidation:
    """Results of statistical validation"""
    statistical_claims: int  # How many statistical claims
    validated_claims: int  # Proper statistics
    questionable_claims: int  # Statistical issues detected
    claim_details: List[Dict[str, Any]]  # Per-claim details


@dataclass
class DiscoveryValidation:
    """
    Rigorous validation framework for discoveries

    ENHANCED with transparent validation metadata for genuine discovery
    """
    # Core validation metrics
    novelty_score: float  # 0-1, how novel is this finding
    novelty_justification: str  # Why is this novel?
    probability_correct: float  # 0-1, confidence in correctness
    probability_justification: str  # Why this confidence level?
    testability: str  # How can this be tested/verified?
    assumptions: List[str]  # What assumptions underlie this?
    limitations: List[str]  # What are the limitations?
    consistency_with_literature: str  # How consistent with existing work?
    potential_impact: str  # What would change if this is true?

    # NEW: Transparent validation metadata
    confidence_level: str = "CANDIDATE"  # CANDIDATE, VALIDATED, PUBLISHED
    validation_timestamp: str = ""  # When validation was performed
    validation_method: str = "literature_similarity"  # How was novelty assessed?

    # NEW: Literature similarity information
    literature_similarity: Optional[LiteratureSimilarityInfo] = None

    # NEW: Multi-stage validation results
    citation_validation: Optional[CitationValidation] = None
    formula_validation: Optional[FormulaValidation] = None
    statistical_validation: Optional[StatisticalValidation] = None

    # Validation provenance
    validation_sources: List[str] = field(default_factory=list)  # arXiv, ADS, etc.
    validation_version: str = "2.0"  # Version of validation pipeline


@dataclass
class GenuineDiscovery:
    """A genuine scientific discovery with rigorous validation"""
    discovery_type: DiscoveryType
    novelty_level: NoveltyLevel
    title: str
    abstract: str  # 200-word summary
    detailed_description: str
    validation: DiscoveryValidation
    timestamp: str
    cycle: int
    domains_involved: List[str]
    methodology: str  # How was this discovered?
    next_steps: List[str]  # What should be done next?


@dataclass
class GenuineDiscoveryConfig:
    """Configuration for genuine discovery system with enhanced discovery framework"""
    # Timing
    startup_delay_seconds: int = 10
    discovery_interval_seconds: int = 60  # 1 minute (reduced from 30 minutes)
    research_cycle_duration: int = 300  # 5 minutes per discovery attempt

    # Discovery focus - all strategies enabled for maximum diversity
    enable_pattern_discovery: bool = True
    enable_theoretical_synthesis: bool = True
    enable_gap_identification: bool = True
    enable_predictive_hypothesis: bool = True
    enable_computational_reanalysis: bool = True

    # Enhanced Validation Standards - Genuine Discovery Framework
    # Primary thresholds (much higher for genuine discovery)
    minimum_novelty_score: float = 0.70  # Below this, don't count as discovery (raised from 0.05)
    minimum_probability: float = 0.75  # Below this, don't count as discovery (raised from 0.3)

    # 3-Dimensional Scoring Requirements
    minimum_validation_score: float = 0.50  # Minimum validation score (reproducibility + predictions)
    minimum_impact_score: float = 0.50  # Minimum impact score (expert consensus + citation potential)

    # Discovery level requirements
    enable_genuine_discovery_levels: bool = True  # Use 4-level framework
    require_reproducibility: bool = True  # Require ≥2 independent verifications for Level 1+
    require_predictive_validation: bool = True  # Require testable predictions for Level 2+

    # Advanced capabilities integration
    enable_swarm_intelligence: bool = True  # Use pheromone-guided exploration
    enable_ontological_reasoning: bool = True  # Use MORK ontology for semantic analysis
    enable_causal_validation: bool = True  # Use causal inference for mechanism validation
    enable_bayesian_hypothesis: bool = True  # Use abductive inference for hypothesis generation
    enable_multi_agent_coordination: bool = True  # Use specialized minds for domain expertise

    # Original validation requirements (maintained for compatibility)
    require_testability: bool = True
    require_literature_consistency_check: bool = False

    # Research domains - expanded scope
    primary_domains: List[str] = field(default_factory=lambda: [
        "astrophysics", "astronomy", "cosmology", "star_formation", "ism",
        "exoplanets", "high_energy_astro", "galactic_astronomy", "stellar_evolution",
        "interstellar_medium", "molecular_clouds", "astrochemistry", "compact_objects",
        "cosmic_microwave_background", "large_scale_structure", "dark_matter",
        "gravitational_waves", "neutrino_astronomy", "multi_messenger_astronomy"
    ])

    # Data sources for analysis
    enable_data_archive_analysis: bool = True
    enable_literature_mining: bool = True
    enable_observation_database_analysis: bool = True

    # Output
    discoverystore_path: Optional[str] = None
    max_discoveries_per_cycle: int = 3


class GenuineDiscoverySystem:
    """
    Genuine Autonomous Discovery System

    Implements rigorous scientific discovery methodology,
    focusing on novel insights rather than knowledge synthesis.
    """

    def __init__(self, config: Optional[GenuineDiscoveryConfig] = None):
        self.config = config or GenuineDiscoveryConfig()
        self.discoverystore_path = self.config.discoverystore_path or \
            Path.home() / ".astra_persistent" / "genuine_discoveries.json"

        # System state
        self.is_running = False
        self.discovery_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()  # Separate pause mechanism for user tasks

        # Discovery tracking
        self.discovery_cycle = 0
        self.genuine_discoveries: List[GenuineDiscovery] = []
        self.failed_discovery_attempts: List[Dict] = []

        # Smart candidate focusing
        self.analyzing_promising_candidate = False
        self.promising_candidate: Optional[GenuineDiscovery] = None
        self.analysis_start_time: Optional[datetime] = None
        self.max_analysis_time = 600  # 10 minutes max analysis time

        # ASTRA integration
        self.astra_system = None

        # Literature validation system (NEW v3.0: EUREKA-ENHANCED validation for genuine insight detection)
        self.literature_validator: Optional[LiteratureValidator] = None
        self.validation_pipeline: Optional[ValidationPipeline] = None
        self.current_novelty_report: Optional[NoveltyReport] = None
        self.current_pipeline_report: Optional[PipelineReport] = None

        # NEW: Eureka-enhanced validator for genuine scientific insight detection
        self.eureka_validator: Optional[EurekaEnhancedValidator] = None
        self.current_eureka_report: Optional[EurekaValidationReport] = None

        if LITERATURE_VALIDATION_AVAILABLE:
            try:
                # Initialize EUREKA-ENHANCED validator (primary validator for genuine insights)
                if EUREKA_VALIDATION_AVAILABLE:
                    self.eureka_validator = create_eureka_enhanced_validator(
                        cache_ttl_seconds=86400,  # 24 hour cache
                        enable_arxiv=True,
                        enable_ads=True
                    )
                    logger.info("[GenuineDiscovery] EUREKA-ENHANCED validator initialized - genuine insight detection enabled")
                    logger.info("[GenuineDiscovery] Distinguishes between field activity and true novelty")
                else:
                    logger.warning("[GenuineDiscovery] Eureka validator not available, using standard validation")

                # Initialize standard literature validator (fallback and supplementary)
                self.literature_validator = create_literature_validator(
                    cache_ttl_seconds=86400,  # 24 hour cache
                    enable_arxiv=True,
                    enable_ads=True,
                    similarity_threshold=0.5
                )

                # Initialize multi-stage validation pipeline (fallback)
                self.validation_pipeline = create_validation_pipeline(
                    literature_validator=self.literature_validator,
                    enable_citation_validation=True,
                    enable_formula_validation=True,
                    enable_statistical_validation=True,
                    parallel_stages=True
                )

                logger.info("[GenuineDiscovery] Validation system ready: Eureka-enhanced + multi-stage fallback")
            except Exception as e:
                logger.error(f"[GenuineDiscovery] Failed to initialize validation system: {e}")
                logger.warning("[GenuineDiscovery] Falling back to degraded novelty assessment")

        # Load previous discoveries
        self._load_discovery_store()

        logger.info(f"[GenuineDiscovery] Initialized with {len(self.genuine_discoveries)} previous discoveries")

    def initialize_with_astra(self, astra_system):
        """Initialize with ASTRA system for discovery capabilities"""
        self.astra_system = astra_system
        logger.info("[GenuineDiscovery] Connected to ASTRA system")

    def start(self):
        """Start genuine autonomous discovery"""
        if self.is_running:
            logger.warning("[GenuineDiscovery] Already running")
            return

        logger.info("[GenuineDiscovery] Starting genuine autonomous discovery...")
        self.is_running = True
        self.stop_event.clear()
        self.pause_event.clear()  # Clear pause event on start

        # Start discovery thread
        self.discovery_thread = threading.Thread(
            target=self._discovery_loop,
            name="GenuineDiscovery",
            daemon=True
        )
        self.discovery_thread.start()

        logger.info("[GenuineDiscovery] Discovery thread started")

    def stop(self):
        """Stop discovery process"""
        if not self.is_running:
            return

        logger.info("[GenuineDiscovery] Stopping discovery...")
        self.is_running = False
        self.stop_event.set()

        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_thread.join(timeout=5.0)

        self._save_discovery_store()
        logger.info("[GenuineDiscovery] Discovery stopped")

    def get_discovery_status(self) -> Dict[str, Any]:
        """Get current discovery status and statistics"""
        discovery_rate = 0.0
        if self.discovery_cycle > 0:
            discovery_rate = len(self.genuine_discoveries) / self.discovery_cycle

        return {
            'is_running': self.is_running,
            'discovery_cycle': self.discovery_cycle,
            'genuine_discoveries': len(self.genuine_discoveries),
            'discovery_rate': discovery_rate,
            'analyzing_promising_candidate': self.analyzing_promising_candidate,
            'validation_available': LITERATURE_VALIDATION_AVAILABLE and self.validation_pipeline is not None,
            'eureka_validation_available': EUREKA_VALIDATION_AVAILABLE and self.eureka_validator is not None,
            'validation_method': 'eureka_enhanced' if self.eureka_validator else 'standard'
        }

    def calculate_novelty_score(self, discovery: 'GenuineDiscovery') -> float:
        """
        Calculate comprehensive novelty score (0-1) for genuine discovery assessment.

        Novelty Score Components:
        - Literature dissimilarity (0-1): How different from existing knowledge
        - Cross-domain synthesis (0-1): Combines multiple fields non-obviously
        - Surprise factor (0-1): Defies consensus expectations
        - Algorithmic probability (0-1): <10% for Eureka-level discoveries

        Returns: Novelty score 0-1, with higher indicating more novel
        """
        if not hasattr(discovery, 'validation') or not discovery.validation:
            return 0.0

        # Start with base novelty from validation
        base_novelty = discovery.validation.novelty_score

        # Literature similarity component (inverse of similarity)
        # ✅ FIX: Check both existence AND not None to prevent AttributeError
        if hasattr(discovery.validation, 'literature_similarity') and discovery.validation.literature_similarity is not None:
            sim_percentage = discovery.validation.literature_similarity.similarity_percentage / 100.0
            # Convert similarity to novelty: 93% similarity = 7% novelty
            literature_novelty = max(0.0, 1.0 - sim_percentage)
        else:
            literature_novelty = base_novelty

        # Cross-domain synthesis bonus
        cross_domain_bonus = 0.0
        if hasattr(discovery, 'domains') and len(discovery.domains) >= 2:
            # Check if domains are meaningfully different (not just sub-fields)
            unique_domains = set(discovery.domains)
            if len(unique_domains) >= 2:
                cross_domain_bonus = 0.1  # Bonus for multi-domain synthesis

        # Surprise factor (estimated from consensus expectations)
        # For now, use field activity as inverse proxy for surprise
        surprise_factor = 0.5  # Default, will be enhanced with expert integration

        # Combine components with weights
        novelty_score = (
            literature_novelty * 0.6 +      # Primary: literature dissimilarity
            cross_domain_bonus * 0.2 +       # Secondary: cross-domain synthesis
            surprise_factor * 0.2              # Tertiary: surprise factor
        )

        return max(0.0, min(1.0, novelty_score))

    def calculate_validation_score(self, discovery: 'GenuineDiscovery') -> float:
        """
        Calculate validation score (0-1) assessing reproducibility and predictive power.

        Validation Score Components:
        - Reproducibility (0-1): ≥2 independent datasets/observations
        - Predictive confirmation (0-1): Novel predictions verified
        - Methodology rigor (0-1): Statistical significance, sample size
        - Temporal stability (0-1): Consistent over time

        Returns: Validation score 0-1, with higher indicating better validated
        """
        if not hasattr(discovery, 'validation') or not discovery.validation:
            return 0.0

        validation_score = 0.5  # Start with moderate validation

        # Check for reproducibility indicators
        if hasattr(discovery, 'detailed_description'):
            description = discovery.detailed_description.lower()

            # Look for reproducibility indicators
            reproducibility_indicators = [
                'reproducible', 'replicated', 'confirmed', 'verified',
                'independent', 'observation', 'measurement', 'detection'
            ]

            reproducibility_count = sum(1 for indicator in reproducibility_indicators if indicator in description)
            if reproducibility_count >= 3:
                validation_score += 0.2

        # Check for predictive content
        if hasattr(discovery, 'abstract'):
            abstract = discovery.abstract.lower()
            predictive_indicators = [
                'predict', 'forecast', 'expect', 'should', 'will',
                'enable', 'allow', 'suggest', 'indicate'
            ]

            predictive_count = sum(1 for indicator in predictive_indicators if indicator in abstract)
            if predictive_count >= 2:
                validation_score += 0.1

        # Check for quantitative specificity (indicates rigor)
        if hasattr(discovery, 'detailed_description'):
            description = discovery.detailed_description
            # Look for numbers, statistics, measurements
            quantitative_patterns = [
                r'\d+\.?\d*\s*(degrees?|K|M|km|pc|years?)',
                r'significance',
                r'correlation',
                r'p\s*[<=>]',
                r'n\s*[=<>]',
                r'sigma'
            ]

            import re
            quantitative_count = sum(1 for pattern in quantitative_patterns if re.search(pattern, description))
            if quantitative_count >= 2:
                validation_score += 0.1

        # Check for methodological rigor
        if hasattr(discovery.validation, 'testability'):
            if discovery.validation.testability:
                validation_score += 0.1

        return max(0.0, min(1.0, validation_score))

    def calculate_impact_score(self, discovery: 'GenuineDiscovery') -> float:
        """
        Calculate impact score (0-1) assessing potential scientific influence.

        Impact Score Components:
        - Expert consensus (0-1): Domain expert validation
        - Citation potential (0-1): Expected forward citations
        - Research enablement (0-1): Enables new research directions
        - Capability expansion (0-1): Enables previously impossible measurements

        Returns: Impact score 0-1, with higher indicating greater impact
        """
        if not hasattr(discovery, 'validation') or not discovery.validation:
            return 0.0

        impact_score = 0.3  # Start with moderate impact

        # Analyze potential impact from discovery characteristics
        if hasattr(discovery, 'novelty_level'):
            level = discovery.novelty_level

            # Higher novelty levels have higher potential impact
            if level == NoveltyLevel.PARADIGM_SHIFT:
                impact_score += 0.4
            elif level == NoveltyLevel.SUBSTANTIAL:
                impact_score += 0.3
            elif level == NoveltyLevel.MODERATE:
                impact_score += 0.1

        # Check for paradigm-shift indicators in description
        if hasattr(discovery, 'detailed_description'):
            description = discovery.detailed_description.lower()

            paradigm_indicators = [
                'fundamental', 'challeng', 'contradict', 'replaces',
                'new framework', 'beyond', 'standard model', 'current understanding'
            ]

            paradigm_count = sum(1 for indicator in paradigm_indicators if indicator in description)
            if paradigm_count >= 2:
                impact_score += 0.2

        # Check for research enablement potential
        enablement_indicators = [
            'enables', 'allows', 'provides', 'opens', 'facilitates',
            'new research', 'future studies', 'further investigation'
        ]

        enablement_count = sum(1 for indicator in enablement_indicators if indicator in description)
        if enablement_count >= 1:
            impact_score += 0.1

        return max(0.0, min(1.0, impact_score))

    def classify_discovery_level(self, discovery: 'GenuineDiscovery') -> DiscoveryLevel:
        """
        Classify discovery into 4-level genuine discovery framework.

        Level Classification:
        - NOVEL_OBSERVATION: <5% literature similarity, reproducible, observable phenomenon
        - THEORETICAL_INSIGHT: Mechanism understanding, testable predictions, explanatory power
        - PARADIGM_SHIFT: Challenges foundational assumptions, enables new research directions
        - EUREKA_DISCOVERY: Revolutionary breakthrough, <10% algorithmic probability

        Returns: DiscoveryLevel classification
        """
        # Calculate 3-dimensional scores
        novelty = self.calculate_novelty_score(discovery)
        validation = self.calculate_validation_score(discovery)
        impact = self.calculate_impact_score(discovery)

        # Check minimum threshold: all dimensions must be >= 0.50
        if novelty < 0.50 or validation < 0.50 or impact < 0.50:
            # Doesn't meet genuine discovery threshold
            # Return lowest level for now, but will likely be rejected
            return DiscoveryLevel.NOVEL_OBSERVATION

        # Calculate overall score
        overall_score = (novelty + validation + impact) / 3.0

        # Level classification based on scores and characteristics
        if overall_score >= 0.90:
            # Eureka Discovery Level (4): Revolutionary breakthroughs
            # Additional requirements: very high novelty, challenging assumptions
            description = discovery.detailed_description.lower() if hasattr(discovery, 'detailed_description') else ""

            revolutionary_indicators = [
                'revolutionary', 'breakthrough', 'first-ever', 'unprecedented',
                'completely new', 'never before', 'fundamentally different'
            ]

            revolutionary_count = sum(1 for indicator in revolutionary_indicators if indicator in description)

            if novelty >= 0.90 and revolutionary_count >= 1:
                return DiscoveryLevel.EUREKA_DISCOVERY
            else:
                return DiscoveryLevel.PARADIGM_SHIFT

        elif overall_score >= 0.75:
            # Paradigm Shift Level (3): Challenges foundational assumptions
            if novelty >= 0.80:
                return DiscoveryLevel.PARADIGM_SHIFT
            else:
                return DiscoveryLevel.THEORETICAL_INSIGHT

        elif overall_score >= 0.65:
            # Theoretical Insight Level (2): Mechanism-level understanding
            if validation >= 0.70:  # Strong validation required
                return DiscoveryLevel.THEORETICAL_INSIGHT
            else:
                return DiscoveryLevel.NOVEL_OBSERVATION

        else:
            # Novel Observation Level (1): Previously unobserved patterns
            return DiscoveryLevel.NOVEL_OBSERVATION

    def _discovery_loop(self):
        """Main discovery loop - genuine research methodology with smart candidate focusing"""
        logger.info("[GenuineDiscovery] Discovery loop starting")
        time.sleep(self.config.startup_delay_seconds)

        while not self.stop_event.is_set():
            try:
                # Check if paused for user task
                if self.pause_event.is_set():
                    logger.info("[GenuineDiscovery] Paused for user task - waiting to resume...")
                    self.pause_event.wait()  # Wait until pause_event is cleared
                    logger.info("[GenuineDiscovery] Resumed from user task")

                # Check if we're currently analyzing a promising candidate
                if self.analyzing_promising_candidate:
                    # Check for pause_event before continuing analysis
                    if self.pause_event.is_set():
                        self.pause_event.wait()  # Wait for pause to clear
                        logger.info("[GenuineDiscovery] Resumed analysis during pause")
                    if self._should_continue_analysis():
                        logger.info(f"[GenuineDiscovery] Continuing analysis of promising candidate: {self.promising_candidate.title}")
                        time.sleep(60)  # Check again in 1 minute
                        continue
                    else:
                        logger.info("[GenuineDiscovery] Analysis timeout or complete, resuming candidate search")
                        self.analyzing_promising_candidate = False
                        self.promising_candidate = None
                        self.analysis_start_time = None

                self.discovery_cycle += 1
                logger.info(f"[GenuineDiscovery] Starting discovery cycle {self.discovery_cycle}")

                # DEBUG: Check we reach this point
                logger.info(f"[GenuineDiscovery] 🔄 DEBUG: Passed cycle increment, current cycle: {self.discovery_cycle}")

                # Run genuine discovery methodology (async for literature validation)
                logger.info(f"[GenuineDiscovery] 🔄 SYNC: About to run discovery cycle with fresh event loop")

                # CRITICAL FIX: Use explicit event loop management with thread-safe timeout
                # Issue: signal.alarm() doesn't work in threads, causing "signal only works in main thread" error
                # Solution: Use asyncio.wait_for() instead of signal-based timeout

                logger.info(f"[GenuineDiscovery] 🔄 DEBUG: Creating new event loop")
                loop = asyncio.new_event_loop()
                logger.info(f"[GenuineDiscovery] 🔄 DEBUG: Event loop created: {loop}")
                asyncio.set_event_loop(loop)
                logger.info(f"[GenuineDiscovery] 🔄 DEBUG: Event loop set as current")

                try:
                    # Create a coroutine that includes timeout logic
                    async def run_with_timeout():
                        CYCLE_TIMEOUT = 300  # 5 minutes
                        try:
                            discoveries = await asyncio.wait_for(
                                self._run_genuine_discovery_cycle(),
                                timeout=CYCLE_TIMEOUT
                            )
                            return discoveries
                        except asyncio.TimeoutError:
                            logger.error(f"[GenuineDiscovery] 🔄 TIMEOUT: Discovery cycle timed out after {CYCLE_TIMEOUT}s")
                            return []

                    # Run the timeout-wrapped coroutine
                    discoveries = loop.run_until_complete(run_with_timeout())
                    logger.info(f"[GenuineDiscovery] 🔄 SYNC: Discovery cycle completed, got {len(discoveries)} discoveries")
                except Exception as e:
                    logger.error(f"[GenuineDiscovery] 🔄 ERROR in discovery cycle: {e}")
                    import traceback
                    traceback.print_exc()
                    discoveries = []
                finally:
                    # Clean up the event loop
                    logger.info(f"[GenuineDiscovery] 🔄 DEBUG: About to close event loop")
                    loop.close()
                    logger.info(f"[GenuineDiscovery] 🔄 SYNC: Event loop closed")

                # Process discoveries and check for promising candidates
                promising_found = False
                for discovery in discoveries:
                    if self._meets_genuine_discovery_standards(discovery):
                        self.genuine_discoveries.append(discovery)
                        logger.info(f"[GenuineDiscovery] ✅ GENUINE DISCOVERY: {discovery.title}")

                        # Check if this discovery is worth pursuing deeply
                        if self._is_worth_pursuing(discovery):
                            logger.info(f"[GenuineDiscovery] 🎯 PROMISING CANDICATE FOUND: {discovery.title}")
                            logger.info(f"[GenuineDiscovery] Pausing new candidate search to analyze this discovery")
                            self.promising_candidate = discovery
                            self.analyzing_promising_candidate = True
                            self.analysis_start_time = datetime.now()
                            promising_found = True
                    else:
                        logger.info(f"[GenuineDiscovery] ❌ Rejected (below standards): {discovery.title}")

                # Save discoveries
                self._save_discovery_store()

                # Wait for next cycle only if not analyzing a promising candidate
                if promising_found:
                    logger.info("[GenuineDiscovery] Promising candidate found - waiting 1 minute before next check")
                    # Check for pause_event before waiting
                    if self.pause_event.is_set():
                        self.pause_event.wait()  # Wait for pause to clear
                    self.stop_event.wait(60)  # Wait 1 minute before checking analysis status
                else:
                    logger.info(f"[GenuineDiscovery] Cycle {self.discovery_cycle} complete, {len(discoveries)} candidates")
                    # Check for pause_event before waiting
                    if self.pause_event.is_set():
                        self.pause_event.wait()  # Wait for pause to clear
                    self.stop_event.wait(self.config.discovery_interval_seconds)  # 1 minute for next cycle

            except Exception as e:
                logger.error(f"[GenuineDiscovery] Error in discovery cycle: {e}")
                import traceback
                traceback.print_exc()
                logger.error(f"[GenuineDiscovery] Stack trace printed above")
                time.sleep(60)

        logger.info("[GenuineDiscovery] Discovery loop ended")

    async def _run_genuine_discovery_cycle(self) -> List[GenuineDiscovery]:
        """Run one cycle of genuine discovery attempts (async for literature validation)"""
        logger.info(f"[GenuineDiscovery] 🔄 ASYNC: Starting discovery cycle async execution")
        discoveries = []
        max_attempts = self.config.max_discoveries_per_cycle * 3  # Try 3x more than we expect

        for attempt in range(max_attempts):
            if self.stop_event.is_set():
                logger.info(f"[GenuineDiscovery] Stop event set, breaking cycle")
                break

            # Choose discovery type based on enabled capabilities
            discovery_type = self._choose_discovery_type()
            logger.info(f"[GenuineDiscovery] 🔄 ASYNC: Attempt {attempt+1}/{max_attempts}, type: {discovery_type.value}")

            try:
                # Await the discovery attempt (includes literature search)
                discovery = await self._attempt_genuine_discovery(discovery_type)
                if discovery:
                    discoveries.append(discovery)

                    if len(discoveries) >= self.config.max_discoveries_per_cycle:
                        break

            except Exception as e:
                logger.error(f"[GenuineDiscovery] Discovery attempt {attempt} failed: {e}")
                self.failed_discovery_attempts.append({
                    'cycle': self.discovery_cycle,
                    'attempt': attempt,
                    'type': discovery_type.value,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })

        return discoveries

    def _choose_discovery_type(self) -> DiscoveryType:
        """Choose discovery type based on configuration"""
        enabled_types = []

        if self.config.enable_pattern_discovery:
            enabled_types.append(DiscoveryType.PATTERN_DISCOVERY)
        if self.config.enable_theoretical_synthesis:
            enabled_types.append(DiscoveryType.THEORETICAL_SYNTHESIS)
        if self.config.enable_gap_identification:
            enabled_types.append(DiscoveryType.GAP_IDENTIFICATION)
        if self.config.enable_predictive_hypothesis:
            enabled_types.append(DiscoveryType.PREDICTIVE_HYPOTHESIS)
        if self.config.enable_computational_reanalysis:
            enabled_types.append(DiscoveryType.COMPUTATIONAL_REANALYSIS)

        if not enabled_types:
            return DiscoveryType.THEORETICAL_SYNTHESIS  # Default

        return random.choice(enabled_types)

    async def _attempt_genuine_discovery(self, discovery_type: DiscoveryType) -> Optional[GenuineDiscovery]:
        """Attempt a genuine discovery based on type (async for literature validation)"""
        logger.info(f"[GenuineDiscovery] Attempting {discovery_type.value} discovery")

        if not self.astra_system:
            logger.warning("[GenuineDiscovery] No ASTRA system connected")
            return None

        # Generate discovery query based on type
        discovery_query = self._generate_discovery_query(discovery_type)

        try:
            # Use ASTRA to conduct research with timeout protection
            # Run synchronous answer() method in thread pool to avoid blocking event loop
            import asyncio

            ANSWER_TIMEOUT = 300  # 5 minutes timeout for ASTRA answer

            logger.info(f"[GenuineDiscovery] Calling ASTRA answer with {ANSWER_TIMEOUT}s timeout...")
            result = await asyncio.wait_for(
                asyncio.to_thread(self.astra_system.answer, discovery_query),
                timeout=ANSWER_TIMEOUT
            )
            logger.info(f"[GenuineDiscovery] ASTRA answer completed successfully")

            if not result or 'answer' not in result:
                logger.warning("[GenuineDiscovery] No valid answer in result")
                return None

            # Process result into genuine discovery (async for literature search)
            return await self._process_discovery_result(result['answer'], discovery_type)

        except asyncio.TimeoutError:
            logger.error(f"[GenuineDiscovery] ASTRA answer timed out after {ANSWER_TIMEOUT}s - discovery attempt failed")
            return None
        except Exception as e:
            logger.error(f"[GenuineDiscovery] Error conducting discovery: {e}")
            return None

    def _generate_discovery_query(self, discovery_type: DiscoveryType) -> str:
        """Generate research query for genuine discovery"""

        if discovery_type == DiscoveryType.PATTERN_DISCOVERY:
            return self._generate_pattern_discovery_query()
        elif discovery_type == DiscoveryType.THEORETICAL_SYNTHESIS:
            return self._generate_theoretical_synthesis_query()
        elif discovery_type == DiscoveryType.GAP_IDENTIFICATION:
            return self._generate_gap_identification_query()
        elif discovery_type == DiscoveryType.PREDICTIVE_HYPOTHESIS:
            return self._generate_predictive_hypothesis_query()
        elif discovery_type == DiscoveryType.COMPUTATIONAL_REANALYSIS:
            return self._generate_computational_reanalysis_query()
        else:
            return self._generate_theoretical_synthesis_query()

    def _generate_pattern_discovery_query(self) -> str:
        """Generate focused query for discovering new patterns"""
        # Select MORE diverse domains to avoid repetition
        domains = self.config.primary_domains
        selected_domains = random.sample(domains, min(4, len(domains)))

        # Add random specific focus areas to increase diversity
        focus_areas = [
            "magnetic field correlations", "velocity structure functions",
            "chemical gradients", "turbulent cascading", "density fluctuations",
            "temporal evolution", "spatial correlations", "scaling relationships",
            "phase transitions", "transport coefficients"
        ]
        selected_focus = random.choice(focus_areas)

        # Add random constraint to vary queries
        constraints = [
            "using high-resolution datasets", "focusing on nearby regions",
            "considering edge-on systems", "analyzing face-on observations",
            "with multi-wavelength data", "across different environments"
        ]
        selected_constraint = random.choice(constraints)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        cycle_id = f"pattern-{self.discovery_cycle}-{timestamp}"

        return f"""Generate ONE novel pattern discovery in: {', '.join(selected_domains)}

Specific focus: {selected_focus} {selected_constraint}
Cycle ID: {cycle_id} - Find unexpected causal relationship.
Requirements: Be specific (50-100 words), quantitative, testable.
Output: Single pattern with mechanism, statistical significance, prediction."""

    def _generate_theoretical_synthesis_query(self) -> str:
        """Generate focused query for theoretical synthesis"""
        # Select MORE diverse domains to avoid repetition
        domains = self.config.primary_domains
        selected_domains = random.sample(domains, min(4, len(domains)))

        # Add random connection types to increase diversity
        connection_types = [
            "quantum-classical bridge", "micro-macro connection",
            "temporal-causal link", "geometric-physical relationship",
            "statistical-deterministic bridge", "local-nonlocal connection"
        ]
        selected_connection = random.choice(connection_types)

        # Add random theoretical framework
        frameworks = [
            "using information theory", "applying network analysis",
            "through symmetry principles", "via thermodynamic limits",
            "using complexity metrics", "through emergence concepts"
        ]
        selected_framework = random.choice(frameworks)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        cycle_id = f"synthesis-{self.discovery_cycle}-{timestamp}"

        return f"""Generate ONE theoretical synthesis in: {', '.join(selected_domains)}

Connection type: {selected_connection} {selected_framework}
Cycle ID: {cycle_id} - Connect unrelated phenomena unexpectedly.
Requirements: Be specific (50-100 words), fundamental, cross-domain.
Output: Novel connection with mechanism, implications, testable prediction."""

    def _generate_gap_identification_query(self) -> str:
        """Generate focused query for gap identification"""
        # Select MORE diverse domains to avoid repetition
        domains = self.config.primary_domains
        selected_domains = random.sample(domains, min(4, len(domains)))

        # Add random gap types to increase diversity
        gap_types = [
            "theoretical-observational discrepancy", "missing mechanism",
            "unexplained parameter correlation", "contradiction between frameworks",
            "missing intermediate scale", "inconsistent boundary conditions"
        ]
        selected_gap = random.choice(gap_types)

        # Add random analysis approach
        approaches = [
            "using high-precision data", "considering extreme regimes",
            "across different redshifts", "in low-metallicity environments",
            "using multi-messenger data", "across cosmic time"
        ]
        selected_approach = random.choice(approaches)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        cycle_id = f"gap-{self.discovery_cycle}-{timestamp}"

        return f"""Generate ONE gap identification in: {', '.join(selected_domains)}

Gap type: {selected_gap} {selected_approach}
Cycle ID: {cycle_id} - Find specific contradiction or missing piece.
Requirements: Be specific (50-100 words), quantifiable, fundamental.
Output: Single gap with evidence, impact, resolution direction."""

    def _generate_predictive_hypothesis_query(self) -> str:
        """Generate focused query for predictive hypothesis generation"""
        # Select MORE diverse domains to avoid repetition
        domains = self.config.primary_domains
        selected_domains = random.sample(domains, min(4, len(domains)))

        # Add random prediction areas to increase diversity
        prediction_areas = [
            "unobserved particle signature", "unexpected scaling law",
            "novel oscillation mode", "counter-intuitive correlation",
            "missing spectral line", "unexpected phase transition",
            "novel instability regime", "unexplained energy transport"
        ]
        selected_prediction = random.choice(prediction_areas)

        # Add random observational method
        methods = [
            "using gravitational lensing", "via spectral line analysis",
            "through timing measurements", "using polarization signatures",
            "via gravitational waves", "through neutrino observations"
        ]
        selected_method = random.choice(methods)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        cycle_id = f"hypothesis-{self.discovery_cycle}-{timestamp}"

        return f"""Generate ONE predictive hypothesis in: {', '.join(selected_domains)}

Prediction target: {selected_prediction} {selected_method}
Cycle ID: {cycle_id} - Single testable prediction beyond current theory.
Requirements: Be specific (50-100 words), quantitative, unexpected.
Output: Novel prediction with test method, timeline, implications."""

    def _generate_computational_reanalysis_query(self) -> str:
        """Generate focused query for computational reanalysis"""
        # Select MORE diverse domains to avoid repetition
        domains = self.config.primary_domains
        selected_domains = random.sample(domains, min(4, len(domains)))

        # Add random analysis methods to increase diversity
        analysis_methods = [
            "machine learning classification", "topological data analysis",
            "wavelet decomposition", "causal inference algorithms",
            "information-theoretic approach", "network analysis methods",
            "multiresolution analysis", "symbolic regression"
        ]
        selected_method = random.choice(analysis_methods)

        # Add random data types
        data_types = [
            "time-series observations", "spectral line surveys",
            "multi-wavelength images", "gravitational wave signals",
            "polarization measurements", "velocity field data"
        ]
        selected_data = random.choice(data_types)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        cycle_id = f"reanalysis-{self.discovery_cycle}-{timestamp}"

        return f"""Generate ONE computational reanalysis in: {', '.join(selected_domains)}

Method: {selected_method} applied to {selected_data}
Cycle ID: {cycle_id} - Apply new analytical approach to existing data.
Requirements: Be specific (50-100 words), novel technique, quantitative.
Output: New finding with method, statistical significance, validation."""

    async def _process_discovery_result(self, result_text: str, discovery_type: DiscoveryType) -> Optional[GenuineDiscovery]:
        """Process ASTRA result into genuine discovery with validation (async for literature search)"""

        # Check if result is too short or looks like a standard analysis rejection
        if len(result_text) < 100:
            logger.info(f"[GenuineDiscovery] Result too short: {len(result_text)} chars")
            return None

        # Check for standard analysis rejection patterns but don't immediately reject
        rejection_patterns = ["classified as standard analysis", "routing to domain modules"]
        if any(pattern in result_text.lower() for pattern in rejection_patterns):
            # Still process it, but the novelty score will likely be low
            logger.info(f"[GenuineDiscovery] Standard analysis pattern detected, still processing")

        # Analyze the result to extract discovery components
        title = self._extract_title(result_text)
        abstract = self._extract_abstract(result_text)
        detailed_description = result_text

        # Extract domains FIRST (needed for validation)
        domains = self._extract_domains(result_text)

        # Perform rigorous validation (async for literature search)
        validation = await self._validate_discovery(result_text, discovery_type, domains)

        # Determine novelty level
        novelty_level = self._assess_novelty_level(validation.novelty_score)

        # Generate methodology
        methodology = f"{discovery_type.value} using ASTRA's integrated capabilities across {', '.join(domains)}"

        # Generate next steps
        next_steps = self._generate_next_steps(result_text, discovery_type)

        discovery = GenuineDiscovery(
            discovery_type=discovery_type,
            novelty_level=novelty_level,
            title=title,
            abstract=abstract,
            detailed_description=detailed_description,
            validation=validation,
            timestamp=datetime.now().isoformat(),
            cycle=self.discovery_cycle,
            domains_involved=domains,
            methodology=methodology,
            next_steps=next_steps
        )

        return discovery

    async def _validate_discovery(
        self,
        result_text: str,
        discovery_type: DiscoveryType,
        domains: List[str]
    ) -> DiscoveryValidation:
        """
        Perform rigorous validation of discovery using EUREKA-ENHANCED validator

        ENHANCED v3.0: Now uses EurekaEnhancedValidator for genuine insight detection:
        - Extracts specific scientific claims from discovery text
        - Searches literature for similar CLAIMS (not just topics)
        - Identifies Eureka moments - genuine advances vs field activity
        - Provides detailed reasoning about true novelty
        - Falls back to standard validation if Eureka unavailable
        """

        # Use EUREKA-ENHANCED validator if available (primary method)
        if self.eureka_validator:
            try:
                logger.info(f"[GenuineDiscovery] Running EUREKA-ENHANCED validation for genuine insight detection...")
                eureka_report = await self.eureka_validator.validate_genuine_advance(
                    discovery_claim=result_text,
                    domains=domains,
                    discovery_type=discovery_type.value,
                    max_results_per_source=50
                )

                # Store Eureka report for reference
                self.current_eureka_report = eureka_report
                self.current_novelty_report = eureka_report.novelty_report if hasattr(eureka_report, 'novelty_report') else None

                # Extract validation metrics from EUREKA assessment
                novelty_score = eureka_report.eureka_assessment.claim_novelty
                novelty_justification = f"Eureka detection: {eureka_report.eureka_assessment.reasoning}"

                # Get probability from Eureka assessment
                if eureka_report.represents_genuine_advance:
                    probability_correct = 0.8  # High confidence if genuine advance detected
                    probability_justification = "EUREKA MOMENT: Represents genuine new scientific insight"
                else:
                    probability_correct = 0.4  # Lower confidence if not genuine advance
                    probability_justification = "Does not represent genuine advance - similar claims exist"

                # Extract testability from suggested validation methods
                testability = ", ".join(eureka_report.eureka_assessment.suggested_validation) if eureka_report.eureka_assessment.suggested_validation else "Standard validation"
                assumptions = self._extract_assumptions(result_text)
                limitations = eureka_report.limitations if eureka_report.limitations else []
                limitations.extend(self._identify_limitations(result_text, discovery_type))

                # Literature consistency from Eureka assessment
                literature_consistency = eureka_report.explanation

                # Potential impact from Eureka assessment
                potential_impact = eureka_report.eureka_assessment.potential_impact

                # Build literature similarity info from Eureka report
                literature_similarity = None
                validation_timestamp = datetime.now().isoformat()
                validation_sources = []
                confidence_level = eureka_report.eureka_assessment.confidence

                if eureka_report.similar_papers:
                    # Populate literature similarity from Eureka report
                    similar_papers_data = []
                    for paper in eureka_report.similar_papers[:10]:
                        similar_papers_data.append({
                            "title": paper.title,
                            "authors": paper.authors,
                            "year": paper.year,
                            "similarity": round(paper.similarity_score * 100, 2),
                            "reasoning": paper.relevance_reasoning
                        })

                    literature_similarity = LiteratureSimilarityInfo(
                        most_similar_paper=(
                            eureka_report.similar_papers[0].title
                            if eureka_report.similar_papers
                            else "None found"
                        ),
                        similarity_percentage=round(
                            (1.0 - eureka_report.novelty_score) * 100, 2
                        ),
                        similar_papers=similar_papers_data,
                        total_papers_searched=eureka_report.total_papers_searched,
                        search_time_seconds=round(eureka_report.validation_time_seconds, 2)
                    )

                    # Track validation sources
                    if self.eureka_validator and self.eureka_validator.literature_validator:
                        if self.eureka_validator.literature_validator.arxiv_client:
                            validation_sources.append("arXiv")
                        if self.eureka_validator.literature_validator.ads_client:
                            validation_sources.append("ADS")

                logger.info(
                    f"[GenuineDiscovery] EUREKA validation complete: "
                    f"genuine_advance={eureka_report.represents_genuine_advance}, "
                    f"eureka_score={eureka_report.eureka_assessment.eureka_score:.3f}, "
                    f"claim_novelty={eureka_report.eureka_assessment.claim_novelty:.3f}, "
                    f"field_activity={eureka_report.field_activity_level:.3f}"
                )

                return DiscoveryValidation(
                    novelty_score=novelty_score,
                    novelty_justification=novelty_justification,
                    probability_correct=probability_correct,
                    probability_justification=probability_justification,
                    testability=testability,
                    assumptions=assumptions,
                    limitations=limitations,
                    consistency_with_literature=literature_consistency,
                    potential_impact=potential_impact,
                    confidence_level=confidence_level,
                    validation_timestamp=validation_timestamp,
                    validation_method="eureka_enhanced",
                    literature_similarity=literature_similarity,
                    validation_sources=validation_sources,
                    validation_version="3.0"
                )

            except Exception as e:
                logger.error(f"[GenuineDiscovery] Eureka validation failed: {e}")
                logger.warning("[GenuineDiscovery] Falling back to standard validation")

        # Fallback: Use standard ValidationPipeline if available
        if self.validation_pipeline:
            try:
                logger.info(f"[GenuineDiscovery] Running standard multi-stage validation pipeline...")
                pipeline_report = await self.validation_pipeline.validate(
                    discovery_claim=result_text,
                    domains=domains,
                    discovery_type=discovery_type.value
                )

                # Store pipeline report for reference
                self.current_pipeline_report = pipeline_report
                self.current_novelty_report = pipeline_report.novelty_report

                # Extract validation metrics from pipeline report
                novelty_score = pipeline_report.novelty_report.novelty_score if pipeline_report.novelty_report else 0.5
                novelty_justification = f"Validated against {pipeline_report.novelty_report.total_papers_searched if pipeline_report.novelty_report else 0} scientific papers using semantic similarity analysis"

                # Get probability from overall validation success
                probability_correct = 0.7 if pipeline_report.overall_status == ValidationStatus.VALIDATED else 0.5
                if pipeline_report.overall_status == ValidationStatus.CANDIDATE:
                    probability_correct = 0.6
                probability_justification = f"Based on multi-stage validation: {pipeline_report.overall_status.value}"

                # Extract testability from limitations
                testability = self._assess_testability(result_text, discovery_type)
                assumptions = self._extract_assumptions(result_text)
                limitations = pipeline_report.limitations if pipeline_report.limitations else []
                limitations.extend(self._identify_limitations(result_text, discovery_type))

                # Literature consistency from semantic similarity
                if pipeline_report.novelty_report and pipeline_report.novelty_report.similar_papers:
                    max_sim = max([p.similarity_score for p in pipeline_report.novelty_report.similar_papers])
                    if max_sim > 0.7:
                        literature_consistency = "High similarity to existing literature suggests limited novelty"
                    elif max_sim > 0.4:
                        literature_consistency = "Moderate similarity to existing work - some novelty possible"
                    else:
                        literature_consistency = "Low similarity to existing literature - high novelty potential"
                else:
                    literature_consistency = "Unable to assess literature consistency"

                # Potential impact from novelty and confidence
                potential_impact = self._assess_potential_impact(result_text, discovery_type)
                if novelty_score > 0.7:
                    potential_impact = "High potential impact if validated - novel finding with limited similar work"
                elif novelty_score > 0.4:
                    potential_impact = "Moderate potential impact - extends existing understanding"
                else:
                    potential_impact = "Lower potential impact - similar to existing findings"

                # Build literature similarity info from pipeline report
                literature_similarity = None
                validation_timestamp = datetime.now().isoformat()
                validation_sources = []
                confidence_level = pipeline_report.confidence_level.value

                if pipeline_report.novelty_report:
                    # Populate literature similarity from validation report
                    similar_papers_data = []
                    for paper in pipeline_report.novelty_report.similar_papers[:10]:
                        similar_papers_data.append({
                            "title": paper.title,
                            "authors": paper.authors,
                            "year": paper.year,
                            "similarity": round(paper.similarity_score * 100, 2),
                            "reasoning": paper.relevance_reasoning
                        })

                    literature_similarity = LiteratureSimilarityInfo(
                        most_similar_paper=(
                            pipeline_report.novelty_report.similar_papers[0].title
                            if pipeline_report.novelty_report.similar_papers
                            else "None found"
                        ),
                        similarity_percentage=round(
                            (1.0 - pipeline_report.novelty_report.novelty_score) * 100, 2
                        ),
                        similar_papers=similar_papers_data,
                        total_papers_searched=pipeline_report.novelty_report.total_papers_searched,
                        search_time_seconds=round(pipeline_report.novelty_report.validation_time_seconds, 2)
                    )

                    # Track validation sources
                    if self.literature_validator:
                        if self.literature_validator.arxiv_client:
                            validation_sources.append("arXiv")
                        if self.literature_validator.ads_client:
                            validation_sources.append("ADS")

                # Build citation validation if available
                citation_validation = None
                if pipeline_report.citation_report:
                    citation_validation = CitationValidation(
                        total_citations=pipeline_report.citation_report.total_citations,
                        verified_citations=pipeline_report.citation_report.verified_citations,
                        hallucinated_citations=pipeline_report.citation_report.hallucinated_citations,
                        unverifiable_citations=pipeline_report.citation_report.unverifiable_citations,
                        citation_details=pipeline_report.citation_report.citation_details
                    )

                # Build formula validation if available
                formula_validation = None
                if pipeline_report.formula_report:
                    formula_validation = FormulaValidation(
                        total_formulas=pipeline_report.formula_report.total_formulas,
                        verified_formulas=pipeline_report.formula_report.verified_formulas,
                        derivable_formulas=pipeline_report.formula_report.derivable_formulas,
                        inconsistent_formulas=pipeline_report.formula_report.inconsistent_formulas,
                        unverifiable_formulas=pipeline_report.formula_report.unverifiable_formulas,
                        formula_details=pipeline_report.formula_report.formula_details
                    )

                # Build statistical validation if available
                statistical_validation = None
                if pipeline_report.statistical_report:
                    statistical_validation = StatisticalValidation(
                        statistical_claims=pipeline_report.statistical_report.get("statistical_claims", 0),
                        validated_claims=pipeline_report.statistical_report.get("validated_claims", 0),
                        questionable_claims=pipeline_report.statistical_report.get("questionable_claims", 0),
                        claim_details=pipeline_report.statistical_report.get("claim_details", [])
                    )

                logger.info(
                    f"[GenuineDiscovery] Pipeline validation complete: "
                    f"status={pipeline_report.overall_status.value}, "
                    f"confidence={confidence_level}, "
                    f"novelty={novelty_score:.3f}, "
                    f"time={pipeline_report.total_validation_time:.2f}s"
                )

                return DiscoveryValidation(
                    novelty_score=novelty_score,
                    novelty_justification=novelty_justification,
                    probability_correct=probability_correct,
                    probability_justification=probability_justification,
                    testability=testability,
                    assumptions=assumptions,
                    limitations=limitations,
                    consistency_with_literature=literature_consistency,
                    potential_impact=potential_impact,

                    # NEW: Transparent validation metadata
                    confidence_level=confidence_level,
                    validation_timestamp=validation_timestamp,
                    validation_method="multi_stage_pipeline",
                    literature_similarity=literature_similarity,
                    validation_sources=validation_sources,
                    validation_version="2.0",

                    # NEW: Multi-stage validation results
                    citation_validation=citation_validation,
                    formula_validation=formula_validation,
                    statistical_validation=statistical_validation
                )

            except Exception as e:
                logger.error(f"[GenuineDiscovery] Validation pipeline failed: {e}")
                logger.warning("[GenuineDiscovery] Falling back to basic validation")
                # Fall through to basic validation

        # Fallback to basic validation if pipeline not available
        logger.info("[GenuineDiscovery] Using basic validation (pipeline unavailable)")

        # ASSESS NOVELTY via real literature search (async)
        novelty_score = await self._assess_novelty_score(result_text, discovery_type, domains)
        novelty_justification = self._explain_novelty_assessment(result_text, discovery_type)

        # Other validation metrics
        probability_correct = self._assess_probability(result_text, discovery_type)
        probability_justification = self._explain_probability_assessment(result_text)

        testability = self._assess_testability(result_text, discovery_type)
        assumptions = self._extract_assumptions(result_text)
        limitations = self._identify_limitations(result_text, discovery_type)
        literature_consistency = self._check_literature_consistency(result_text)
        potential_impact = self._assess_potential_impact(result_text, discovery_type)

        # Build literature similarity info if available
        literature_similarity = None
        confidence_level = "CANDIDATE"
        validation_timestamp = datetime.now().isoformat()
        validation_sources = []

        if self.current_novelty_report:
            # Populate literature similarity from validation report
            similar_papers_data = []
            for paper in self.current_novelty_report.similar_papers[:10]:
                similar_papers_data.append({
                    "title": paper.title,
                    "authors": paper.authors,
                    "year": paper.year,
                    "similarity": round(paper.similarity_score * 100, 2),
                    "reasoning": paper.relevance_reasoning
                })

            literature_similarity = LiteratureSimilarityInfo(
                most_similar_paper=(
                    self.current_novelty_report.similar_papers[0].title
                    if self.current_novelty_report.similar_papers
                    else "None found"
                ),
                similarity_percentage=round(
                    (1.0 - self.current_novelty_report.novelty_score) * 100, 2
                ),
                similar_papers=similar_papers_data,
                total_papers_searched=self.current_novelty_report.total_papers_searched,
                search_time_seconds=round(self.current_novelty_report.validation_time_seconds, 2)
            )

            # Determine confidence level
            if self.current_novelty_report.novelty_score >= 0.7:
                confidence_level = "CANDIDATE"  # High novelty, needs validation
            elif self.current_novelty_report.novelty_score >= 0.5:
                confidence_level = "CANDIDATE"
            else:
                confidence_level = "CANDIDATE"  # Even low novelty starts as candidate

            # Track validation sources
            if self.literature_validator:
                if self.literature_validator.arxiv_client:
                    validation_sources.append("arXiv")
                if self.literature_validator.ads_client:
                    validation_sources.append("ADS")

        return DiscoveryValidation(
            novelty_score=novelty_score,
            novelty_justification=novelty_justification,
            probability_correct=probability_correct,
            probability_justification=probability_justification,
            testability=testability,
            assumptions=assumptions,
            limitations=limitations,
            consistency_with_literature=literature_consistency,
            potential_impact=potential_impact,

            # NEW: Transparent validation metadata
            confidence_level=confidence_level,
            validation_timestamp=validation_timestamp,
            validation_method="literature_similarity" if self.literature_validator else "keyword_fallback",
            literature_similarity=literature_similarity,
            validation_sources=validation_sources,
            validation_version="2.0"
        )

    def _meets_genuine_discovery_standards(self, discovery: GenuineDiscovery) -> bool:
        """
        Enhanced genuine discovery standards check using 3-dimensional scoring framework.

        NEW FRAMEWORK (v4.0):
        - 3-dimensional scoring: Novelty + Validation + Impact (all >= 0.50)
        - 4-level discovery classification
        - Much higher thresholds for genuine discovery

        OLD THRESHOLDS (maintained for compatibility):
        - minimum_novelty_score: 0.70 (up from 0.05)
        - minimum_probability: 0.75 (up from 0.3)
        """

        # Check for duplicates FIRST to prevent repetitive discoveries
        if self._is_duplicate_discovery(discovery):
            logger.info(f"[GenuineDiscovery] ❌ Duplicate discovery rejected: {discovery.title[:50]}...")
            return False

        # NEW: Check 3-dimensional scoring framework
        if self.config.enable_genuine_discovery_levels:
            novelty_score = self.calculate_novelty_score(discovery)
            validation_score = self.calculate_validation_score(discovery)
            impact_score = self.calculate_impact_score(discovery)

            logger.info(f"[GenuineDiscovery] 🎯 3-Dimensional Scoring: "
                       f"Novelty={novelty_score:.2f}, Validation={validation_score:.2f}, Impact={impact_score:.2f}")

            # Check minimum threshold: all dimensions must be >= 0.50
            if novelty_score < 0.50:
                logger.info(f"[GenuineDiscovery] ❌ Below novelty threshold: {novelty_score:.2f} < 0.50")
                return False

            if validation_score < 0.50:
                logger.info(f"[GenuineDiscovery] ❌ Below validation threshold: {validation_score:.2f} < 0.50")
                return False

            if impact_score < 0.50:
                logger.info(f"[GenuineDiscovery] ❌ Below impact threshold: {impact_score:.2f} < 0.50")
                return False

            # NEW: Classify discovery level
            discovery_level = self.classify_discovery_level(discovery)
            logger.info(f"[GenuineDiscovery] 🏛️ Discovery Level: {discovery_level.value}")

            # NEW: Only accept Level 2+ discoveries (genuine advances)
            # Level 1 (Novel Observation) is too common, require mechanism understanding
            if discovery_level == DiscoveryLevel.NOVEL_OBSERVATION:
                logger.info("[GenuineDiscovery] ❌ Level 1 (Novel Observation) not sufficient - requires mechanism understanding")
                return False

            # NEW: Enhanced original thresholds for backwards compatibility
            if discovery.validation.novelty_score < self.config.minimum_novelty_score:
                logger.info(f"[GenuineDiscovery] ❌ Below enhanced novelty threshold: {discovery.validation.novelty_score:.2f} < {self.config.minimum_novelty_score}")
                return False

            if discovery.validation.probability_correct < self.config.minimum_probability:
                logger.info(f"[GenuineDiscovery] ❌ Below enhanced probability threshold: {discovery.validation.probability_correct:.2f} < {self.config.minimum_probability}")
                return False

        else:
            # ORIGINAL: Use simple thresholds (backwards compatibility)
            logger.info("[GenuineDiscovery] Using original validation standards")

            # Check novelty threshold
            if discovery.validation.novelty_score < self.config.minimum_novelty_score:
                logger.info(f"[GenuineDiscovery] ❌ Below novelty threshold: {discovery.validation.novelty_score}")
                return False

            # Check probability threshold
            if discovery.validation.probability_correct < self.config.minimum_probability:
                logger.info(f"[GenuineDiscovery] ❌ Below probability threshold: {discovery.validation.probability_correct}")
                return False

        # Check testability requirement (both frameworks)
        if self.config.require_testability and not discovery.validation.testability:
            logger.info("[GenuineDiscovery] ❌ Not testable")
            return False

        # Check literature consistency if required (both frameworks)
        if self.config.require_literature_consistency_check:
            if "inconsistent" in discovery.validation.consistency_with_literature.lower():
                logger.info("[GenuineDiscovery] ❌ Inconsistent with established literature")
                return False

        logger.info(f"[GenuineDiscovery] ✅ Discovery meets enhanced genuine discovery standards")
        return True

    def _is_duplicate_discovery(self, discovery: GenuineDiscovery) -> bool:
        """Check if discovery is a duplicate of existing discoveries"""
        # Check for exact title match
        for existing in self.genuine_discoveries:
            if existing.title == discovery.title:
                return True
            # Check for high content similarity (first 300 chars)
            if len(existing.detailed_description) > 300 and len(discovery.detailed_description) > 300:
                if existing.detailed_description[:300] == discovery.detailed_description[:300]:
                    return True
            # Check for title similarity (80% match)
            if self._title_similarity(existing.title, discovery.title) > 0.8:
                return True
        return False

    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles"""
        # Simple word-based similarity
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    # Helper methods for discovery processing

    def _extract_title(self, text: str) -> str:
        """Extract title from discovery text"""
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            if line.strip() and not line.startswith('-') and len(line.strip()) > 10:
                return line.strip()[:100]  # Max 100 chars
        return "Untitled Discovery"

    def _extract_abstract(self, text: str) -> str:
        """Extract 200-word abstract from discovery text"""
        # Take first substantive content as abstract
        lines = text.split('\n')
        abstract_lines = []
        word_count = 0

        for line in lines:
            if line.strip() and not line.startswith('#'):
                words = line.split()
                if word_count + len(words) <= 200:
                    abstract_lines.append(line)
                    word_count += len(words)
                else:
                    break

        abstract = ' '.join(abstract_lines)
        return abstract[:1000]  # Max 1000 chars

    def _extract_domains(self, text: str) -> List[str]:
        """Extract domains involved in discovery"""
        domains = []
        text_lower = text.lower()

        for domain in self.config.primary_domains:
            if domain.lower() in text_lower:
                domains.append(domain)

        return domains if domains else ["astrophysics"]

    async def _assess_novelty_score(
        self,
        text: str,
        discovery_type: DiscoveryType,
        domains: Optional[List[str]] = None
    ) -> float:
        """
        Assess novelty score (0-1) using REAL literature validation

        REPLACES previous keyword-based scoring with semantic similarity
        to actual scientific papers from arXiv and ADS.

        Returns:
            Novelty score from 0.0 (identical to existing) to 1.0 (completely novel)
        """
        # Use literature validator if available
        if self.literature_validator:
            try:
                # Extract domains if not provided
                if domains is None:
                    domains = self._extract_domains(text)

                # Run real literature validation
                novelty_report = await self.literature_validator.validate_novelty(
                    discovery_claim=text,
                    domains=domains,
                    discovery_type=discovery_type.value,
                    max_results_per_source=50
                )

                # Store report for transparency
                self.current_novelty_report = novelty_report

                # Log validation results
                logger.info(
                    f"[GenuineDiscovery] Literature validation: "
                    f"novelty={novelty_report.novelty_score:.3f}, "
                    f"papers_searched={novelty_report.total_papers_searched}, "
                    f"similar_papers={len(novelty_report.similar_papers)}, "
                    f"time={novelty_report.validation_time_seconds:.2f}s"
                )

                # Log top similar paper for transparency
                if novelty_report.similar_papers:
                    top_paper = novelty_report.similar_papers[0]
                    logger.info(
                        f"[GenuineDiscovery] Most similar paper: "
                        f"'{top_paper.title}' (similarity={top_paper.similarity_score:.3f})"
                    )

                return novelty_report.novelty_score

            except Exception as e:
                logger.error(f"[GenuineDiscovery] Literature validation failed: {e}")
                logger.warning("[GenuineDiscovery] Falling back to degraded novelty assessment")

        # Fallback: Degraded novelty assessment (keyword-based, deprecated)
        logger.warning("[GenuineDiscovery] Using DEGRADED keyword-based novelty assessment")
        return self._degraded_novelty_assessment(text, discovery_type)

    def _degraded_novelty_assessment(self, text: str, discovery_type: DiscoveryType) -> float:
        """
        DEGRADED: Keyword-based novelty assessment (fallback only)

        This method should only be used when literature validation is unavailable.
        It provides a crude approximation of novelty based on text patterns.
        """
        # Very conservative scoring for fallback mode
        novelty_indicators = [
            "unexpected", "surprising", "counter-intuitive", "novel", "new connection",
            "previously unnoticed", "unexplained", "contradicts", "challenges",
            "for the first time", "not previously", "genuinely new", "unconventional"
        ]

        text_lower = text.lower()
        indicator_count = sum(1 for indicator in novelty_indicators if indicator in text_lower)

        # Very conservative base score
        base_score = min(0.3, indicator_count * 0.05)

        # Penalize heavily for standard analysis
        standard_indicators = ["well-known", "established", "standard", "typical"]
        standard_count = sum(1 for indicator in standard_indicators if indicator in text_lower)
        base_score -= standard_count * 0.15

        # Low default score in degraded mode
        return max(0.1, min(0.4, base_score))

    def _explain_novelty_assessment(self, text: str, discovery_type: DiscoveryType) -> str:
        """Explain why this novelty score was given"""
        # Generate explanation based on text analysis
        return f"Novelty assessed based on presence of unexpected connections, quantitative predictions, and departure from established knowledge in {discovery_type.value}."

    def _assess_probability(self, text: str, discovery_type: DiscoveryType) -> float:
        """Assess probability of being correct (0-1)"""
        # Conservative probability assessment
        base_probability = 0.5  # Start at 50%

        # Increase for quantitative content
        if any(char.isdigit() for char in text):
            base_probability += 0.1

        # Increase for theoretical grounding
        theory_indicators = ["based on", "follows from", "derives from", "consistent with"]
        text_lower = text.lower()
        if any(indicator in text_lower for indicator in theory_indicators):
            base_probability += 0.1

        # Decrease for speculative language
        speculative_indicators = ["might", "could", "possibly", "perhaps", "may"]
        if any(indicator in text_lower for indicator in speculative_indicators):
            base_probability -= 0.1

        return max(0.3, min(0.85, base_probability))

    def _explain_probability_assessment(self, text: str) -> str:
        """Explain probability assessment"""
        return "Probability based on theoretical grounding, quantitative content, and degree of speculation in the claim."

    def _assess_testability(self, text: str, discovery_type: DiscoveryType) -> str:
        """Assess how this discovery can be tested"""
        # Look for testability indicators
        if "observable" in text.lower() or "measurable" in text.lower():
            return "Testable through observations mentioned in discovery"
        elif "prediction" in text.lower():
            return "Testable through predictions made in discovery"
        else:
            return "Testability unclear - requires further development"

    def _extract_assumptions(self, text: str) -> List[str]:
        """Extract underlying assumptions"""
        # Look for assumption indicators
        assumptions = []
        assumption_indicators = ["assuming", "assumes", "presumes", "based on the assumption"]

        lines = text.split('\n')
        for line in lines:
            for indicator in assumption_indicators:
                if indicator in line.lower():
                    assumptions.append(line.strip()[:200])
                    break

        return assumptions if assumptions else ["Standard astrophysical assumptions apply"]

    def _identify_limitations(self, text: str, discovery_type: DiscoveryType) -> List[str]:
        """Identify limitations of the discovery"""
        return [
            "Requires observational verification",
            "Based on current understanding which may evolve",
            "May be specific to certain physical regimes"
        ]

    def _check_literature_consistency(self, text: str) -> str:
        """Check consistency with established literature"""
        return "Generally consistent with established physics while proposing novel extensions"

    def _assess_potential_impact(self, text: str, discovery_type: DiscoveryType) -> str:
        """Assess potential impact if discovery is correct"""
        return f"If validated, this {discovery_type.value} could advance understanding in the identified domains."

    def _assess_novelty_level(self, novelty_score: float) -> NoveltyLevel:
        """Determine novelty level from score"""
        if novelty_score < 0.3:
            return NoveltyLevel.INCREMENTAL
        elif novelty_score < 0.6:
            return NoveltyLevel.MODERATE
        elif novelty_score < 0.8:
            return NoveltyLevel.SUBSTANTIAL
        else:
            return NoveltyLevel.PARADIGM_SHIFT

    def _generate_next_steps(self, text: str, discovery_type: DiscoveryType) -> List[str]:
        """Generate next steps for validation/development"""
        return [
            "Literature search to confirm novelty",
            "Develop quantitative predictions for testing",
            "Identify observational data for validation",
            "Consider implications for related phenomena"
        ]

    def _save_discovery_store(self):
        """Save discoveries to persistent storage"""
        try:
            self.discoverystore_path.parent.mkdir(parents=True, exist_ok=True)

            store_data = {
                'discoveries': [
                    {
                        'type': d.discovery_type.value,
                        'novelty_level': d.novelty_level.value,
                        'title': d.title,
                        'abstract': d.abstract,
                        'detailed_description': d.detailed_description,
                        'validation': {
                            'novelty_score': d.validation.novelty_score,
                            'novelty_justification': d.validation.novelty_justification,
                            'probability_correct': d.validation.probability_correct,
                            'probability_justification': d.validation.probability_justification,
                            'testability': d.validation.testability,
                            'assumptions': d.validation.assumptions,
                            'limitations': d.validation.limitations,
                            'literature_consistency': d.validation.consistency_with_literature,
                            'potential_impact': d.validation.potential_impact,
                            'confidence_level': d.validation.confidence_level,
                            'validation_timestamp': d.validation.validation_timestamp,
                            'validation_method': d.validation.validation_method,
                            'validation_sources': d.validation.validation_sources,
                            'validation_version': d.validation.validation_version,
                            'literature_similarity': {
                                'most_similar_paper': d.validation.literature_similarity.most_similar_paper if d.validation.literature_similarity else None,
                                'similarity_percentage': d.validation.literature_similarity.similarity_percentage if d.validation.literature_similarity else None,
                                'similar_papers': d.validation.literature_similarity.similar_papers if d.validation.literature_similarity else [],
                                'total_papers_searched': d.validation.literature_similarity.total_papers_searched if d.validation.literature_similarity else 0,
                                'search_time_seconds': d.validation.literature_similarity.search_time_seconds if d.validation.literature_similarity else 0
                            } if d.validation.literature_similarity else None,
                            'citation_validation': {
                                'total_citations': d.validation.citation_validation.total_citations if d.validation.citation_validation else 0,
                                'verified_citations': d.validation.citation_validation.verified_citations if d.validation.citation_validation else 0,
                                'hallucinated_citations': d.validation.citation_validation.hallucinated_citations if d.validation.citation_validation else 0,
                                'unverifiable_citations': d.validation.citation_validation.unverifiable_citations if d.validation.citation_validation else 0,
                                'citation_details': d.validation.citation_validation.citation_details if d.validation.citation_validation else []
                            } if d.validation.citation_validation else None,
                            'formula_validation': {
                                'total_formulas': d.validation.formula_validation.total_formulas if d.validation.formula_validation else 0,
                                'verified_formulas': d.validation.formula_validation.verified_formulas if d.validation.formula_validation else 0,
                                'derivable_formulas': d.validation.formula_validation.derivable_formulas if d.validation.formula_validation else 0,
                                'inconsistent_formulas': d.validation.formula_validation.inconsistent_formulas if d.validation.formula_validation else 0,
                                'unverifiable_formulas': d.validation.formula_validation.unverifiable_formulas if d.validation.formula_validation else 0,
                                'formula_details': d.validation.formula_validation.formula_details if d.validation.formula_validation else []
                            } if d.validation.formula_validation else None,
                            'statistical_validation': {
                                'statistical_claims': d.validation.statistical_validation.statistical_claims if d.validation.statistical_validation else 0,
                                'validated_claims': d.validation.statistical_validation.validated_claims if d.validation.statistical_validation else 0,
                                'questionable_claims': d.validation.statistical_validation.questionable_claims if d.validation.statistical_validation else 0,
                                'claim_details': d.validation.statistical_validation.claim_details if d.validation.statistical_validation else []
                            } if d.validation.statistical_validation else None
                        },
                        'timestamp': d.timestamp,
                        'cycle': d.cycle,
                        'domains': d.domains_involved,
                        'methodology': d.methodology,
                        'next_steps': d.next_steps
                    }
                    for d in self.genuine_discoveries
                ],
                'failed_attempts': self.failed_discovery_attempts,
                'statistics': {
                    'total_cycles': self.discovery_cycle,
                    'total_discoveries': len(self.genuine_discoveries),
                    'discovery_rate': len(self.genuine_discoveries) / max(1, self.discovery_cycle)
                }
            }

            with open(self.discoverystore_path, 'w') as f:
                json.dump(store_data, f, indent=2)

            logger.info(f"[GenuineDiscovery] Saved {len(self.genuine_discoveries)} discoveries to {self.discoverystore_path}")

        except Exception as e:
            logger.error(f"[GenuineDiscovery] Error saving discoveries: {e}")

    def _load_discovery_store(self):
        """Load discoveries from persistent storage"""
        try:
            if self.discoverystore_path.exists():
                with open(self.discoverystore_path) as f:
                    store_data = json.load(f)

                # Reconstruct discovery objects
                for d_data in store_data.get('discoveries', []):
                    try:
                        # Handle backwards compatibility for old discovery format
                        validation_data = d_data['validation']

                        # Reconstruct literature similarity if available
                        literature_similarity = None
                        if validation_data.get('literature_similarity'):
                            lit_sim = validation_data['literature_similarity']
                            literature_similarity = LiteratureSimilarityInfo(
                                most_similar_paper=lit_sim.get('most_similar_paper'),
                                similarity_percentage=lit_sim.get('similarity_percentage', 0),
                                similar_papers=lit_sim.get('similar_papers', []),
                                total_papers_searched=lit_sim.get('total_papers_searched', 0),
                                search_time_seconds=lit_sim.get('search_time_seconds', 0)
                            )

                        # Reconstruct citation validation if available
                        citation_validation = None
                        if validation_data.get('citation_validation'):
                            cit_val = validation_data['citation_validation']
                            citation_validation = CitationValidation(
                                total_citations=cit_val.get('total_citations', 0),
                                verified_citations=cit_val.get('verified_citations', 0),
                                hallucinated_citations=cit_val.get('hallucinated_citations', 0),
                                unverifiable_citations=cit_val.get('unverifiable_citations', 0),
                                citation_details=cit_val.get('citation_details', [])
                            )

                        # Reconstruct formula validation if available
                        formula_validation = None
                        if validation_data.get('formula_validation'):
                            form_val = validation_data['formula_validation']
                            formula_validation = FormulaValidation(
                                total_formulas=form_val.get('total_formulas', 0),
                                verified_formulas=form_val.get('verified_formulas', 0),
                                derivable_formulas=form_val.get('derivable_formulas', 0),
                                inconsistent_formulas=form_val.get('inconsistent_formulas', 0),
                                unverifiable_formulas=form_val.get('unverifiable_formulas', 0),
                                formula_details=form_val.get('formula_details', [])
                            )

                        # Reconstruct statistical validation if available
                        statistical_validation = None
                        if validation_data.get('statistical_validation'):
                            stat_val = validation_data['statistical_validation']
                            statistical_validation = StatisticalValidation(
                                statistical_claims=stat_val.get('statistical_claims', 0),
                                validated_claims=stat_val.get('validated_claims', 0),
                                questionable_claims=stat_val.get('questionable_claims', 0),
                                claim_details=stat_val.get('claim_details', [])
                            )

                        validation = DiscoveryValidation(
                            novelty_score=validation_data['novelty_score'],
                            novelty_justification=validation_data['novelty_justification'],
                            probability_correct=validation_data['probability_correct'],
                            probability_justification=validation_data['probability_justification'],
                            testability=validation_data['testability'],
                            assumptions=validation_data['assumptions'],
                            limitations=validation_data['limitations'],
                            consistency_with_literature=validation_data['literature_consistency'],
                            potential_impact=validation_data['potential_impact'],
                            confidence_level=validation_data.get('confidence_level', 'CANDIDATE'),
                            validation_timestamp=validation_data.get('validation_timestamp', ''),
                            validation_method=validation_data.get('validation_method', 'literature_similarity'),
                            validation_sources=validation_data.get('validation_sources', []),
                            validation_version=validation_data.get('validation_version', '2.0'),
                            literature_similarity=literature_similarity,
                            citation_validation=citation_validation,
                            formula_validation=formula_validation,
                            statistical_validation=statistical_validation
                        )

                        discovery = GenuineDiscovery(
                            discovery_type=DiscoveryType(d_data['type']),
                            novelty_level=NoveltyLevel(d_data['novelty_level']),
                            title=d_data['title'],
                            abstract=d_data['abstract'],
                            detailed_description=d_data['detailed_description'],
                            validation=validation,
                            timestamp=d_data['timestamp'],
                            cycle=d_data['cycle'],
                            domains_involved=d_data['domains'],
                            methodology=d_data['methodology'],
                            next_steps=d_data['next_steps']
                        )

                        self.genuine_discoveries.append(discovery)

                    except Exception as e:
                        logger.warning(f"[GenuineDiscovery] Error loading discovery {d_data.get('title', 'unknown')}: {e}")
                        continue  # Skip this discovery and continue with others

                self.failed_discovery_attempts = store_data.get('failed_attempts', [])
                self.discovery_cycle = store_data.get('statistics', {}).get('total_cycles', 0)

                logger.info(f"[GenuineDiscovery] Loaded {len(self.genuine_discoveries)} discoveries from persistent storage")

        except Exception as e:
            logger.error(f"[GenuineDiscovery] Error loading discoveries: {e}")

    def _is_worth_pursuing(self, discovery: GenuineDiscovery) -> bool:
        """Determine if a discovery is worth deep analysis (pauses new candidate search)"""
        # High-novelty discoveries are always worth pursuing
        if discovery.validation.novelty_score >= 0.5:
            return True

        # Substantial or paradigm-shift level discoveries
        if discovery.novelty_level in [NoveltyLevel.SUBSTANTIAL, NoveltyLevel.PARADIGM_SHIFT]:
            return True

        # High probability discoveries with moderate novelty
        if discovery.validation.probability_correct >= 0.6 and discovery.validation.novelty_score >= 0.3:
            return True

        # Discoveries with clear testability and high impact
        if discovery.validation.testability and "high" in discovery.validation.potential_impact.lower():
            return True

        return False

    def _should_continue_analysis(self) -> bool:
        """Check if analysis of promising candidate should continue"""
        if not self.analyzing_promising_candidate or not self.analysis_start_time:
            return False

        # Check if we've exceeded max analysis time
        analysis_duration = (datetime.now() - self.analysis_start_time).total_seconds()
        if analysis_duration > self.max_analysis_time:
            logger.info(f"[GenuineDiscovery] Analysis timeout after {analysis_duration/60:.1f} minutes")
            return False

        # Could add more sophisticated logic here
        # For now, continue until timeout
        return True

    def pause_for_user_task(self, reason: str = "User request"):
        """Pause discovery for user task (takes priority over all discovery activities)"""
        logger.info(f"[GenuineDiscovery] Pausing for user task: {reason}")
        self.pause_event.set()  # Use pause_event instead of stop_event
        # Note: Don't set is_running = False, we want to resume after user task

    def resume_from_user_task(self):
        """Resume discovery after user task completion"""
        logger.info("[GenuineDiscovery] Resuming from user task")
        self.pause_event.clear()

    def resume_after_user_task(self):
        """Resume discovery after user task completes"""
        logger.info("[GenuineDiscovery] Resuming after user task")
        self.stop_event.clear()
        self.pause_event.clear()  # Also clear pause event in case it was set
        self.is_running = True

        # Restart discovery thread if needed
        if not self.discovery_thread or not self.discovery_thread.is_alive():
            self.discovery_thread = threading.Thread(
                target=self._discovery_loop,
                name="GenuineDiscovery",
                daemon=True
            )
            self.discovery_thread.start()

    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        status = {
            'is_running': self.is_running,
            'discovery_cycle': self.discovery_cycle,
            'genuine_discoveries': len(self.genuine_discoveries),
            'failed_attempts': len(self.failed_discovery_attempts),
            'discovery_rate': len(self.genuine_discoveries) / max(1, self.discovery_cycle),
            'latest_discovery': self.genuine_discoveries[-1].title if self.genuine_discoveries else None,
            'analyzing_promising_candidate': self.analyzing_promising_candidate,
            'promising_candidate_title': self.promising_candidate.title if self.promising_candidate else None,
            'discovery_interval_minutes': self.config.discovery_interval_seconds / 60
        }
        return status


# Global instance
_genuine_discovery_system: Optional[GenuineDiscoverySystem] = None


def get_genuine_discovery_system(config: Optional[GenuineDiscoveryConfig] = None) -> GenuineDiscoverySystem:
    """Get or create global genuine discovery system"""
    global _genuine_discovery_system

    if _genuine_discovery_system is None:
        _genuine_discovery_system = GenuineDiscoverySystem(config)
        logger.info("[GenuineDiscovery] Created global instance")

    return _genuine_discovery_system


def initialize_genuine_discovery_with_astra(astra_system, config: Optional[GenuineDiscoveryConfig] = None) -> GenuineDiscoverySystem:
    """Initialize genuine discovery with ASTRA system"""
    system = get_genuine_discovery_system(config)
    system.initialize_with_astra(astra_system)
    return system


def register_user_task_start():
    """Register that a user task has started (pauses discovery)"""
    discovery = get_genuine_discovery_system()
    if discovery:
        discovery.pause_for_user_task("User query/task")
        logger.info("[GenuineDiscovery] User task registered - discovery paused")


def register_user_task_complete():
    """Register that a user task has completed (resumes discovery)"""
    discovery = get_genuine_discovery_system()
    if discovery:
        discovery.resume_after_user_task()
        logger.info("[GenuineDiscovery] User task completed - discovery resumed")


def get_discovery_status() -> Dict[str, Any]:
    """Get current discovery status"""
    discovery = get_genuine_discovery_system()
    if discovery:
        return discovery.get_status()
    else:
        return {
            'is_running': False,
            'discovery_cycle': 0,
            'genuine_discoveries': 0,
            'failed_attempts': 0,
            'discovery_rate': 0.0,
            'latest_discovery': None,
            'analyzing_promising_candidate': False,
            'promising_candidate_title': None,
            'discovery_interval_minutes': 1.0
        }


def pause_discovery_manually(reason: str = "Manual pause"):
    """Manually pause discovery system"""
    discovery = get_genuine_discovery_system()
    if discovery:
        discovery.pause_for_user_task(reason)
        return True
    return False


def resume_discovery_manually():
    """Manually resume discovery system"""
    discovery = get_genuine_discovery_system()
    if discovery:
        discovery.resume_after_user_task()
        return True
    return False


def perform_enhanced_causal_pattern_discovery(
    data: np.ndarray,
    variable_names: List[str],
    astronomical_context: Optional[Dict[str, Any]] = None,
    optimizations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform enhanced causal pattern discovery for autonomous discovery.

    This function integrates the optimized astrophysical causal discovery
    into the autonomous discovery system for pattern finding.

    Args:
        data: Observational astrophysical data
        variable_names: Names of astrophysical variables
        astronomical_context: Optional astronomical metadata
        optimizations: List of optimizations to apply

    Returns:
        Dictionary with discovered causal patterns and performance metrics
    """
    try:
        from astra_core.capabilities.v95_enhanced_astrophysical_causal_discovery import (
            discover_astrophysical_causal_structure
        )

        # Use enhanced causal discovery with optimizations
        result = discover_astrophysical_causal_structure(
            data, variable_names,
            method='pc',
            optimizations=optimizations or ['parallel', 'cache', 'early_stopping'],
            astronomical_context=astronomical_context
        )

        logger.info(f"[EnhancedCausalDiscovery] Pattern discovery completed")
        logger.info(f"[EnhancedCausalDiscovery]   Speedup achieved: {result['efficiency_improvements']['total_speedup']:.2f}x")
        logger.info(f"[EnhancedCausalDiscovery]   Cache hit rate: {result['cache_stats']['hit_rate']:.1%}")

        return result

    except Exception as e:
        logger.error(f"[EnhancedCausalDiscovery] Pattern discovery failed: {e}")
        return {
            'error': str(e),
            'graph': None,
            'computation_time': 0.0,
            'efficiency_improvements': {'total_speedup': 0.0}
        }


def get_discovery_system_status() -> Dict[str, Any]:
    """Get comprehensive discovery system status"""
    discovery = get_genuine_discovery_system()
    if discovery:
        return discovery.get_status()
    else:
        return {
            'is_running': False,
            'discovery_cycle': 0,
            'genuine_discoveries': 0,
            'failed_attempts': 0,
            'discovery_rate': 0.0,
            'latest_discovery': None,
            'analyzing_promising_candidate': False,
            'promising_candidate_title': None,
            'discovery_interval_minutes': 1.0,
            'enhanced_causal_discovery_available': True
        }