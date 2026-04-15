# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
# Metacognitive Monitor
# =============================================================================

class MetacognitiveMonitor:
    """
    Monitor reasoning quality using V41 metacognition.

    Tracks confidence, uncertainty, and reasoning quality metrics.
    """

    def __init__(self):
        self.confidence_history = []
        self.uncertainty_history = []

    def update(self, confidence: float, uncertainty: float):
        """Update monitoring metrics."""
        self.confidence_history.append(confidence)
        self.uncertainty_history.append(uncertainty)

    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        if not self.confidence_history:
            return {
                'current_confidence': 0.0,
                'avg_confidence': 0.0,
                'current_uncertainty': 0.0,
                'trend': 'unknown'
            }

        return {
            'current_confidence': self.confidence_history[-1],
            'avg_confidence': sum(self.confidence_history) / len(self.confidence_history),
            'current_uncertainty': self.uncertainty_history[-1],
            'trend': 'improving' if len(self.confidence_history) > 1 and self.confidence_history[-1] > self.confidence_history[-2] else 'stable'
        }
