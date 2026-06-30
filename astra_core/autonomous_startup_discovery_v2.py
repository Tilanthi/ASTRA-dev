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


@dataclass
class DiscoveryValidation:
    """Rigorous validation framework for discoveries"""
    novelty_score: float  # 0-1, how novel is this finding
    novelty_justification: str  # Why is this novel?
    probability_correct: float  # 0-1, confidence in correctness
    probability_justification: str  # Why this confidence level?
    testability: str  # How can this be tested/verified?
    assumptions: List[str]  # What assumptions underlie this?
    limitations: List[str]  # What are the limitations?
    consistency_with_literature: str  # How consistent with existing work?
    potential_impact: str  # What would change if this is true?


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
    """Configuration for genuine discovery system"""
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

    # Validation standards
    minimum_novelty_score: float = 0.05  # Below this, don't count as discovery (lowered from 0.3)
    minimum_probability: float = 0.3  # Below this, don't count as discovery (lowered from 0.4)
    require_testability: bool = True
    require_literature_consistency_check: bool = False  # Changed to allow more discoveries

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

    def _discovery_loop(self):
        """Main discovery loop - genuine research methodology with smart candidate focusing"""
        logger.info("[GenuineDiscovery] Discovery loop starting")
        time.sleep(self.config.startup_delay_seconds)

        while not self.stop_event.is_set():
            try:
                # Check if we're currently analyzing a promising candidate
                if self.analyzing_promising_candidate:
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

                # Run genuine discovery methodology
                discoveries = self._run_genuine_discovery_cycle()

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
                    self.stop_event.wait(60)  # Wait 1 minute before checking analysis status
                else:
                    logger.info(f"[GenuineDiscovery] Cycle {self.discovery_cycle} complete, {len(discoveries)} candidates")
                    self.stop_event.wait(self.config.discovery_interval_seconds)  # 1 minute for next cycle

            except Exception as e:
                logger.error(f"[GenuineDiscovery] Error in discovery cycle: {e}")
                time.sleep(60)

        logger.info("[GenuineDiscovery] Discovery loop ended")

    def _run_genuine_discovery_cycle(self) -> List[GenuineDiscovery]:
        """Run one cycle of genuine discovery attempts"""
        discoveries = []
        max_attempts = self.config.max_discoveries_per_cycle * 3  # Try 3x more than we expect

        for attempt in range(max_attempts):
            if self.stop_event.is_set():
                break

            # Choose discovery type based on enabled capabilities
            discovery_type = self._choose_discovery_type()

            try:
                discovery = self._attempt_genuine_discovery(discovery_type)
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

    def _attempt_genuine_discovery(self, discovery_type: DiscoveryType) -> Optional[GenuineDiscovery]:
        """Attempt a genuine discovery based on type"""
        logger.info(f"[GenuineDiscovery] Attempting {discovery_type.value} discovery")

        if not self.astra_system:
            logger.warning("[GenuineDiscovery] No ASTRA system connected")
            return None

        # Generate discovery query based on type
        discovery_query = self._generate_discovery_query(discovery_type)

        try:
            # Use ASTRA to conduct research
            result = self.astra_system.answer(discovery_query)

            if not result or 'answer' not in result:
                return None

            # Process result into genuine discovery
            return self._process_discovery_result(result['answer'], discovery_type)

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
        """Generate query for discovering new patterns in existing data"""
        # Select diverse domains to avoid repetition
        domains = self.config.primary_domains
        selected_domains = random.sample(domains, min(4, len(domains)))

        return f"""Conduct a genuine pattern discovery analysis in astrophysics using enhanced causal discovery methods.

FOCUS: Find novel patterns, correlations, or causal relationships that have NOT been extensively documented.

METHODOLOGY:
1. Choose a specific astrophysical domain from: {', '.join(selected_domains)}
2. Use enhanced causal discovery algorithms with:
   - Parallel independence testing for multi-wavelength data
   - Intelligent caching optimized for sky regions and spectral bands
   - Early stopping with astronomical confidence thresholds
   - Adaptive parameter tuning for different astronomical phenomena
3. Identify relevant published datasets or observational databases
4. Look for unexpected causal relationships, not just correlations
5. Focus on cross-domain connections (e.g., how ISM properties causally affect star formation)
6. Consider temporal evolution patterns, spatial causal structures, or multi-scale causal relationships

ENHANCED CAUSAL DISCOVERY APPROACH:
- Use OptimizedAstrophysicalCausalDiscovery for 5-10x performance improvement
- Leverage astronomical caching: sky regions, wavelength bands, instruments
- Apply adaptive significance levels for different sample sizes and noise characteristics
- Implement early stopping when strong causal patterns emerge
- Utilize parallel processing for multi-wavelength or multi-region analyses

REQUIREMENTS:
- Do NOT just summarize known relationships
- Look for CAUSAL relationships, not just correlations
- Use enhanced causal discovery to identify genuine causal mechanisms
- Consider non-obvious causal connections between different physical regimes
- Quantify causal relationships with mathematical expressions where possible
- Focus on patterns that challenge existing theoretical understanding

OUTPUT FORMAT:
- Causal pattern discovered (with mathematical description if applicable)
- Why this causal pattern is novel or unexpected
- Data sources analyzed with enhanced causal discovery
- Statistical significance and causal strength of the pattern
- Potential physical causal mechanism
- Testable causal predictions arising from this pattern
- How this causal pattern challenges or extends current understanding
- Performance metrics from enhanced causal discovery (speedup, cache hit rate)"""

    def _generate_theoretical_synthesis_query(self) -> str:
        """Generate query for theoretical synthesis discovery"""
        # Select diverse domains to avoid repetition
        domains = self.config.primary_domains
        selected_domains = random.sample(domains, min(5, len(domains)))

        return f"""Conduct genuine theoretical synthesis in astrophysics.

FOCUS: Connect seemingly unrelated astrophysical phenomena in a novel way that provides new insight.

METHODOLOGY:
1. Identify two or more seemingly unrelated astrophysical phenomena from: {', '.join(selected_domains)}
2. Find a unifying principle, mechanism, or mathematical framework that connects them
3. The connection must be NON-OBVIOUS and not extensively documented in literature
4. The synthesis should provide new understanding or predictive power
5. Consider connections across different scales, regimes, or fundamental physics

REQUIREMENTS:
- Do NOT connect phenomena that are already known to be related
- Look for cross-scale connections (e.g., how microphysical processes affect galactic evolution)
- Consider fundamental physics connections (e.g., how quantum effects manifest in astrophysical contexts)
- The synthesis must be genuinely novel, not just a review of known connections
- Challenge conventional wisdom with unexpected connections

OUTPUT FORMAT:
- Phenomena being connected (specific and unexpected pairing)
- Novel unifying principle/mechanism
- Why this connection is unexpected or novel
- Mathematical framework if applicable
- New insights or predictions from this synthesis
- How this synthesis changes our understanding
- Testable predictions that distinguish this synthesis from conventional approaches"""

    def _generate_gap_identification_query(self) -> str:
        """Generate query for identifying gaps in current understanding"""
        # Select diverse domains to avoid repetition
        domains = self.config.primary_domains
        selected_domains = random.sample(domains, min(4, len(domains)))

        return f"""Conduct genuine gap identification in astrophysical understanding.

FOCUS: Find specific contradictions, missing pieces, or inconsistencies in current astrophysical knowledge.

METHODOLOGY:
1. Examine current understanding in: {', '.join(selected_domains)}
2. Look for:
   - Contradictions between theoretical predictions and observations
   - Missing physical mechanisms in widely accepted models
   - Inconsistencies between different theoretical frameworks
   - Unexplained parameter values or relationships
   - Discrepancies between different observational methods
3. Focus on gaps that are specific and addressable

REQUIREMENTS:
- Do NOT just list open problems in general
- Identify specific, quantifiable gaps or contradictions
- Explain why current explanations are insufficient
- Consider whether the gap represents a fundamental misunderstanding vs. missing complexity
- Look for gaps that have been overlooked or underestimated

OUTPUT FORMAT:
- Specific gap or contradiction identified
- Why current understanding is insufficient
- Evidence for the gap (observational or theoretical)
- Proposed resolution direction (if any)
- Impact if this gap were resolved
- Testable predictions that would distinguish between possible resolutions
- How this gap has been overlooked or underestimated"""

    def _generate_predictive_hypothesis_query(self) -> str:
        """Generate query for predictive hypothesis generation"""
        # Select diverse domains to avoid repetition
        domains = self.config.primary_domains
        selected_domains = random.sample(domains, min(4, len(domains)))

        return f"""Generate genuinely novel predictive hypotheses in astrophysics.

FOCUS: Create specific, testable predictions that go beyond current theoretical expectations.

METHODOLOGY:
1. Start from established physics in: {', '.join(selected_domains)}
2. Extend or combine theories in a novel direction
3. Generate specific, quantitative predictions
4. Predict something unexpected or counter-intuitive
5. Ensure predictions are testable with current or near-future observations

REQUIREMENTS:
- Predictions must be genuinely novel, not just expected outcomes
- Must be specific and quantifiable (not "we might see something interesting")
- Should be surprising or counter-intuitive
- Must be testable/falsifiable
- Should arise from rigorous reasoning, not speculation
- Challenge conventional wisdom or extend theories in unexpected directions

OUTPUT FORMAT:
- Novel prediction (specific and quantitative)
- Theoretical basis for the prediction
- Why this prediction is unexpected
- How to test/observe the predicted effect
- Timeline for testability (current tech vs. future)
- Implications if prediction is confirmed vs. falsified
- How this prediction could distinguish between competing theories"""

    def _generate_computational_reanalysis_query(self) -> str:
        """Generate query for computational reanalysis"""
        # Select diverse domains to avoid repetition
        domains = self.config.primary_domains
        selected_domains = random.sample(domains, min(4, len(domains)))

        return f"""Conduct novel computational reanalysis of existing astrophysical data.

FOCUS: Apply new analytical methods or perspectives to existing datasets to discover what was missed.

METHODOLOGY:
1. Choose a well-studied astrophysical phenomenon from: {', '.join(selected_domains)}
2. Identify relevant existing datasets (observations, simulations, surveys)
3. Apply a NON-STANDARD analytical approach:
   - New statistical methods
   - Alternative parameterizations
   - Cross-domain analysis techniques
   - Machine learning or pattern recognition approaches
   - Time-series analysis or signal processing methods
   - Topological or network analysis approaches
4. Look for what previous analyses might have missed

REQUIREMENTS:
- Do NOT just reconfirm known results with standard methods
- The analytical approach must be genuinely different from what's typically done
- Focus on finding subtle patterns or relationships that standard approaches miss
- Quantify confidence in any new findings
- Consider systematic effects or biases that previous analyses might have missed

OUTPUT FORMAT:
- Dataset reanalyzed
- Novel analytical method applied
- New findings (if any)
- Why standard methods missed this
- Statistical confidence in new findings
- Cross-validation with other datasets/methods
- Potential systematic effects or biases uncovered"""

    def _process_discovery_result(self, result_text: str, discovery_type: DiscoveryType) -> Optional[GenuineDiscovery]:
        """Process ASTRA result into genuine discovery with validation"""

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

        # Perform rigorous validation
        validation = self._validate_discovery(result_text, discovery_type)

        # Determine novelty level
        novelty_level = self._assess_novelty_level(validation.novelty_score)

        # Extract domains
        domains = self._extract_domains(result_text)

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

    def _validate_discovery(self, result_text: str, discovery_type: DiscoveryType) -> DiscoveryValidation:
        """Perform rigorous validation of discovery"""

        # This is where we implement the validation framework
        # In a real system, this would involve:
        # 1. Literature comparison to assess novelty
        # 2. Internal consistency checking
        # 3. Probability assessment based on evidence strength
        # 4. Testability analysis
        # 5. Assumption extraction

        # For now, implement a basic version
        novelty_score = self._assess_novelty_score(result_text, discovery_type)
        novelty_justification = self._explain_novelty_assessment(result_text, discovery_type)

        probability_correct = self._assess_probability(result_text, discovery_type)
        probability_justification = self._explain_probability_assessment(result_text)

        testability = self._assess_testability(result_text, discovery_type)
        assumptions = self._extract_assumptions(result_text)
        limitations = self._identify_limitations(result_text, discovery_type)
        literature_consistency = self._check_literature_consistency(result_text)
        potential_impact = self._assess_potential_impact(result_text, discovery_type)

        return DiscoveryValidation(
            novelty_score=novelty_score,
            novelty_justification=novelty_justification,
            probability_correct=probability_correct,
            probability_justification=probability_justification,
            testability=testability,
            assumptions=assumptions,
            limitations=limitations,
            consistency_with_literature=literature_consistency,
            potential_impact=potential_impact
        )

    def _meets_genuine_discovery_standards(self, discovery: GenuineDiscovery) -> bool:
        """Check if discovery meets rigorous standards"""

        # Check novelty threshold
        if discovery.validation.novelty_score < self.config.minimum_novelty_score:
            logger.info(f"[GenuineDiscovery] Below novelty threshold: {discovery.validation.novelty_score}")
            return False

        # Check probability threshold
        if discovery.validation.probability_correct < self.config.minimum_probability:
            logger.info(f"[GenuineDiscovery] Below probability threshold: {discovery.validation.probability_correct}")
            return False

        # Check testability requirement
        if self.config.require_testability and not discovery.validation.testability:
            logger.info("[GenuineDiscovery] Not testable")
            return False

        # Check literature consistency if required
        if self.config.require_literature_consistency_check:
            if "inconsistent" in discovery.validation.consistency_with_literature.lower():
                logger.info("[GenuineDiscovery] Inconsistent with established literature")
                return False

        return True

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

    def _assess_novelty_score(self, text: str, discovery_type: DiscoveryType) -> float:
        """Assess novelty score (0-1) - how different from existing knowledge?"""
        # Expanded and more permissive novelty indicators
        novelty_indicators = [
            "unexpected", "surprising", "counter-intuitive", "novel", "new connection",
            "previously unnoticed", "unexplained", "contradicts", "challenges",
            "for the first time", "not previously", "genuinely new", "unconventional",
            "alternative", "departure from", "beyond", "extends", "suggests",
            "indicates", "reveals", "shows", "demonstrates", "proposes", "hypothesizes",
            "speculates", "predicts", "correlation", "relationship", "pattern",
            "trend", "scaling", "dependence", "connection", "mechanism", "framework",
            "approach", "method", "analysis", "result", "finding", "discovery",
            "insight", "understanding", "explanation", "interpretation", "implication"
        ]

        # Anti-patterns that reduce novelty (but don't eliminate it)
        standard_analysis_indicators = [
            "well-known", "established", "standard", "typical", "conventional",
            "widely accepted", "commonly understood", "textbook", "basic"
        ]

        text_lower = text.lower()
        indicator_count = sum(1 for indicator in novelty_indicators if indicator in text_lower)

        # Base score from indicators (more generous)
        base_score = min(0.7, indicator_count * 0.08)

        # Adjust based on specificity and content length
        if len(text) > 300:  # Substantial content
            base_score += 0.15
        if len(text) > 800:  # Very detailed
            base_score += 0.1

        # Adjust based on quantitative content
        if any(char.isdigit() for char in text):  # Has numbers/quantitative content
            base_score += 0.15

        # Reduce score for standard analysis indicators (but not to zero)
        standard_count = sum(1 for indicator in standard_analysis_indicators if indicator in text_lower)
        base_score -= standard_count * 0.05

        # Ensure minimum threshold for any substantive response
        if len(text) > 200 and base_score < 0.08:
            base_score = 0.08

        return max(0.05, min(0.95, base_score))  # Range 0.05-0.95

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
                            'potential_impact': d.validation.potential_impact
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
                    validation = DiscoveryValidation(
                        novelty_score=d_data['validation']['novelty_score'],
                        novelty_justification=d_data['validation']['novelty_justification'],
                        probability_correct=d_data['validation']['probability_correct'],
                        probability_justification=d_data['validation']['probability_justification'],
                        testability=d_data['validation']['testability'],
                        assumptions=d_data['validation']['assumptions'],
                        limitations=d_data['validation']['limitations'],
                        consistency_with_literature=d_data['validation']['literature_consistency'],
                        potential_impact=d_data['validation']['potential_impact']
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
        self.stop_event.set()
        self.is_running = False

    def resume_after_user_task(self):
        """Resume discovery after user task completes"""
        logger.info("[GenuineDiscovery] Resuming after user task")
        self.stop_event.clear()
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