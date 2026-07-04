"""
Adaptive Reasoning Controller for Scientific Discovery
======================================================

Manages dynamic reasoning mode switching based on discovery phase,
confidence levels, and metacognitive assessment. Integrates with
V41 Orchestrator for high-level reasoning control.

Key Components:
- AdaptiveReasoningController: Main mode selection logic
- MetacognitiveMonitor: Quality assessment using V41
- UncertaintyTracker: Confidence calibration
- ReasoningModeSelector: Phase → Mode mapping

Reasoning Modes (from V41):
- ANALYTICAL: Deep systematic analysis
- CREATIVE: Novel solutions via analogical reasoning
- CRITICAL: Evaluation and falsification
- INTEGRATIVE: Synthesis and unification
- ADAPTIVE: Dynamic responsive reasoning
- DELIBERATIVE: Multi-perspective consideration

Version: 1.0.0
Date: 2025-12-27
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum, auto
from collections import defaultdict

# Import V41 components (try both absolute and relative imports)
try:
    from ..reasoning.v41_orchestrator import (
        ReasoningMode, TaskComplexity, ReasoningTask, ReasoningResult
    )
    from ..reasoning.metacognition import (
        get_metacognitive_controller, ReasoningStrategy, ReasoningTrace
    )
    V41_AVAILABLE = True
except (ImportError, ValueError):
    try:
        # Fallback to absolute import (for when run from outside package)
        from astra_core.reasoning.v41_orchestrator import (
            ReasoningMode, TaskComplexity, ReasoningTask, ReasoningResult
        )
        from astra_core.reasoning.metacognition import (
            get_metacognitive_controller, ReasoningStrategy, ReasoningTrace
        )
        V41_AVAILABLE = True
    except ImportError as e:
        logging.warning(f"Could not import V41 components: {e}")
        V41_AVAILABLE = False
    # Define fallback enums if import fails
    class ReasoningMode(Enum):
        ANALYTICAL = auto()
        CREATIVE = auto()
        CRITICAL = auto()
        INTEGRATIVE = auto()
        ADAPTIVE = auto()
        DELIBERATIVE = auto()

logger = logging.getLogger(__name__)


# =============================================================================
# Discovery Phases
# =============================================================================

class DiscoveryPhase(Enum):
    """Phases of the scientific discovery cycle"""
    LITERATURE_REVIEW = "literature_review"
    DATA_GATHERING = "data_gathering"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    EXPERIMENTAL_DESIGN = "experimental_design"
    ANALYSIS_EXECUTION = "analysis_execution"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"


# Default phase-to-mode mappings
PHASE_TO_MODE_MAP = {
    DiscoveryPhase.LITERATURE_REVIEW: ReasoningMode.ANALYTICAL,
    DiscoveryPhase.DATA_GATHERING: ReasoningMode.ANALYTICAL,
    DiscoveryPhase.HYPOTHESIS_GENERATION: ReasoningMode.CREATIVE,
    DiscoveryPhase.EXPERIMENTAL_DESIGN: ReasoningMode.CREATIVE,
    DiscoveryPhase.ANALYSIS_EXECUTION: ReasoningMode.ANALYTICAL,
    DiscoveryPhase.SYNTHESIS: ReasoningMode.INTEGRATIVE,
    DiscoveryPhase.VALIDATION: ReasoningMode.CRITICAL,
}


# =============================================================================
# Reasoning State Tracking
# =============================================================================

@dataclass
class ReasoningState:
    """Current reasoning state"""
    phase: DiscoveryPhase
    mode: ReasoningMode
    confidence: float = 0.5
    quality_score: float = 0.5
    iterations: int = 0
    stuck_count: int = 0  # Times we've been stuck without progress

    # Performance metrics
    time_in_phase: float = 0.0
    phase_start_time: float = field(default_factory=time.time)

    # History
    mode_history: List[ReasoningMode] = field(default_factory=list)
    phase_history: List[DiscoveryPhase] = field(default_factory=list)

    def update_phase(self, new_phase: DiscoveryPhase):
        """Update to new phase"""
        self.phase_history.append(self.phase)
        self.phase = new_phase
        self.time_in_phase = 0.0
        self.phase_start_time = time.time()
        self.iterations = 0
        self.stuck_count = 0

    def update_mode(self, new_mode: ReasoningMode):
        """Update reasoning mode"""
        self.mode_history.append(self.mode)
        self.mode = new_mode

    def tick(self):
        """Update time tracking"""
        self.time_in_phase = time.time() - self.phase_start_time
        self.iterations += 1


# =============================================================================
# Uncertainty Tracker
# =============================================================================

class UncertaintyTracker:
    """
    Track and calibrate confidence levels across discovery process.

    Maintains running estimates of uncertainty and provides
    confidence-based decision support.
    """

    def __init__(self):
        self.confidence_history: List[float] = []
        self.calibration_data: Dict[str, List[Tuple[float, bool]]] = defaultdict(list)

    def update(self, confidence: float, phase: DiscoveryPhase):
        """Update confidence tracking"""
        self.confidence_history.append(confidence)

    def get_calibrated_confidence(self, raw_confidence: float,
                                  phase: DiscoveryPhase) -> float:
        """
        Calibrate raw confidence based on historical performance.

        If we consistently over/under-estimate, adjust accordingly.
        """
        # Simple calibration: if we have history, adjust
        if len(self.confidence_history) > 10:
            # Check if we're consistently over-confident
            avg_confidence = sum(self.confidence_history[-10:]) / 10
            if avg_confidence > 0.8:
                # Slightly reduce confidence (we might be over-confident)
                return raw_confidence * 0.9
            elif avg_confidence < 0.4:
                # Slightly increase (we might be under-confident)
                return raw_confidence * 1.1

        return raw_confidence

    def should_seek_validation(self, confidence: float) -> bool:
        """Determine if we need additional validation"""
        return confidence < 0.6

    def estimate_remaining_uncertainty(self, current_confidence: float,
                                      phase: DiscoveryPhase) -> float:
        """Estimate how much uncertainty remains to resolve"""
        return 1.0 - current_confidence


# =============================================================================
# Adaptive Reasoning Controller
# =============================================================================

class AdaptiveReasoningController:
    """
    Main controller for adaptive reasoning in scientific discovery.

    Manages reasoning mode selection based on discovery phase, confidence
    levels, and metacognitive assessment.
    """

    def __init__(self):
        self.current_phase = DiscoveryPhase.LITERATURE_REVIEW
        self.current_mode = ReasoningMode.ANALYTICAL
        self.uncertainty_tracker = UncertaintyTracker()
        self.metacognitive_monitor = MetacognitiveMonitor() if V41_AVAILABLE else None
        self.reasoning_history = []

    def select_reasoning_mode(self, phase: DiscoveryPhase,
                             confidence: float = 0.5) -> ReasoningMode:
        """Select appropriate reasoning mode for current phase and confidence"""
        # Use default phase-to-mode mapping
        mode = PHASE_TO_MODE_MAP.get(phase, ReasoningMode.ANALYTICAL)

        # Adjust based on confidence
        if confidence < 0.3:
            # Low confidence: switch to more analytical mode
            mode = ReasoningMode.ANALYTICAL
        elif confidence > 0.8:
            # High confidence: can be more creative
            if mode == ReasoningMode.ANALYTICAL:
                mode = ReasoningMode.CREATIVE

        self.current_mode = mode
        return mode

    def update_phase(self, new_phase: DiscoveryPhase):
        """Update current discovery phase"""
        self.current_phase = new_phase
        self.uncertainty_tracker.track_phase_transition(new_phase)

    def assess_reasoning_quality(self, reasoning_trace: Dict[str, Any]) -> float:
        """Assess quality of recent reasoning"""
        if self.metacognitive_monitor:
            return self.metacognitive_monitor.assess_quality(reasoning_trace)
        return 0.5  # Default assessment if V41 not available

    def get_reasoning_state(self) -> ReasoningState:
        """Get current reasoning state"""
        return ReasoningState(
            phase=self.current_phase,
            mode=self.current_mode,
            confidence=self.uncertainty_tracker.current_confidence,
            uncertainty_level=self.uncertainty_tracker.current_uncertainty
        )


def get_adaptive_reasoning_controller() -> AdaptiveReasoningController:
    """Factory function to create adaptive reasoning controller"""
    return AdaptiveReasoningController()


# =============================================================================
# Metacognitive Monitor
# =============================================================================

class MetacognitiveMonitor:
    """
    Monitor reasoning quality using V41 metacognition.

    Tracks reasoning patterns, confidence calibration, and discovery quality
    to improve future discovery cycles.
    """
