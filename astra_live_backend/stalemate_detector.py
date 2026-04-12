"""
ASTRA Live — Stalemate Detector

Automatically detects and removes stuck/stale hypotheses to prevent
the discovery pipeline from stagnating.

Based on analysis of historical discovery data:
- Active hypotheses generate discoveries within 500-1000 seconds
- Typical cycle interval: 25 seconds
- Most productive hypotheses show progress within 20 cycles (500s)

Conservative stalemate thresholds:
- PROPOSED → next phase: 1 hour (3600s, ~144 cycles)
- SCREENING → next phase: 30 minutes (1800s, ~72 cycles)
- TESTING → progress: 2 hours (7200s, ~288 cycles)
- No confidence growth: 30 minutes (1800s)
"""
import time
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class StalemateReason(Enum):
    """Reason why a hypothesis was flagged as stale."""
    STUCK_TOO_LONG = "stuck_too_long"           # In same phase beyond threshold
    NO_CONFIDENCE_GROWTH = "no_confidence_growth" # Confidence not increasing
    NO_TEST_PROGRESS = "no_test_progress"         # No tests being run
    LOW_CONFIDENCE_FLOOR = "low_confidence_floor" # Stuck at very low confidence
    DATA_UNAVAILABLE = "data_unavailable"         # Can't fetch required data


@dataclass
class StalemateVerdict:
    """A stalemate detection result."""
    hypothesis_id: str
    hypothesis_name: str
    is_stale: bool
    reason: Optional[StalemateReason]
    time_in_phase_seconds: float
    last_confidence: float
    confidence_delta: float
    time_since_last_test: float
    recommendation: str  # "archive", "monitor", "force_advance"
    details: str


class StalemateDetector:
    """
    Detects stuck hypotheses to prevent pipeline stagnation.

    Thresholds (conservative based on historical analysis):
    - PROPOSED phase: 1 hour max (theoretical hypotheses with no data)
    - SCREENING phase: 30 minutes max (should move to testing quickly)
    - TESTING phase: 2 hours max (should generate results or be archived)
    - No confidence growth: 30 minutes (stagnating confidence)
    """

    # Phase-specific time thresholds (seconds)
    PHASE_THRESHOLDS = {
        "proposed": 3600,    # 1 hour - theoretical hypotheses shouldn't wait forever
        "screening": 1800,   # 30 minutes - screening should be quick
        "testing": 7200,     # 2 hours - testing should show progress
        "validated": 86400,  # 24 hours - validated hypotheses are fine
        "published": float('inf'),  # Never stale
        "archived": float('inf'),   # Never stale
    }

    # Confidence thresholds
    MIN_CONFIDENCE_FOR_PROGRESS = {
        "proposed": 0.30,   # Below this, unlikely to ever advance
        "screening": 0.40,  # Should reach this to move to testing
        "testing": 0.50,    # Should be increasing with tests
    }

    # Time without confidence growth to flag as stale
    NO_GROWTH_THRESHOLD = 1800  # 30 minutes

    def __init__(self):
        self.detection_history: List[StalemateVerdict] = []
        self.stats = {
            "total_detections": 0,
            "stale_found": 0,
            "auto_archived": 0,
        }

    def check_hypothesis(self, hypothesis, current_cycle: int) -> StalemateVerdict:
        """
        Check if a hypothesis is stale.

        Returns a StalemateVerdict with recommendation.
        """
        now = time.time()
        phase = hypothesis.phase.value if hasattr(hypothesis.phase, 'value') else str(hypothesis.phase)

        # Calculate metrics
        time_in_phase = now - max(hypothesis.updated_at, hypothesis.created_at)
        time_since_creation = now - hypothesis.created_at
        time_since_last_test = now - hypothesis.last_tested_at if hypothesis.last_tested_at > 0 else float('inf')

        # Confidence growth (need to track this externally or estimate)
        confidence = hypothesis.confidence
        confidence_delta = 0.0  # Would need historical tracking

        # Determine if stale
        is_stale = False
        reason = None
        recommendation = "monitor"
        details = ""

        # Check 1: Stuck in phase too long
        threshold = self.PHASE_THRESHOLDS.get(phase, float('inf'))
        if threshold < float('inf') and time_in_phase > threshold:
            is_stale = True

            # Determine specific reason based on phase and confidence
            if phase == "proposed" and confidence < self.MIN_CONFIDENCE_FOR_PROGRESS["proposed"]:
                reason = StalemateReason.LOW_CONFIDENCE_FLOOR
                recommendation = "archive"
                details = (
                    f"Stuck in PROPOSED for {time_in_phase:.0f}s ({threshold}s threshold) "
                    f"with confidence {confidence:.2f} < {self.MIN_CONFIDENCE_FOR_PROGRESS['proposed']}. "
                    f"Unlikely to advance without new data or different approach."
                )
            elif time_since_last_test > 3600 and phase == "testing":
                reason = StalemateReason.NO_TEST_PROGRESS
                recommendation = "archive"
                details = (
                    f"Stuck in TESTING for {time_in_phase:.0f}s with no tests for "
                    f"{time_since_last_test:.0f}s. Investigation may be blocked."
                )
            else:
                reason = StalemateReason.STUCK_TOO_LONG
                if confidence > 0.6:
                    recommendation = "force_advance"
                    details = f"Strong hypothesis (conf={confidence:.2f}) stuck too long in {phase.upper()}. Consider force-advancing."
                else:
                    recommendation = "archive"
                    details = f"Hypothesis stuck in {phase.upper()} for {time_in_phase:.0f}s. Removing to free capacity."

        # Check 2: Low confidence with no signs of improvement
        elif phase == "proposed" and confidence < 0.30:
            # Give more time for very new hypotheses, but flag old ones
            if time_since_creation > 1800:  # 30 minutes old
                is_stale = True
                reason = StalemateReason.LOW_CONFIDENCE_FLOOR
                recommendation = "archive"
                details = (
                    f"Low confidence ({confidence:.2f}) with no progress after "
                    f"{time_since_creation:.0f}s. Theoretical hypotheses without data sources "
                    f"should be archived to free resources for testable hypotheses."
                )

        # Check 3: No recent test activity in testing phase
        elif phase == "testing" and time_since_last_test > 1800:
            is_stale = True
            reason = StalemateReason.NO_TEST_PROGRESS
            recommendation = "archive"
            details = (
                f"No tests run for {time_since_last_test:.0f}s. "
                f"Investigation may be blocked or data unavailable."
            )

        # Create verdict
        verdict = StalemateVerdict(
            hypothesis_id=hypothesis.id,
            hypothesis_name=hypothesis.name,
            is_stale=is_stale,
            reason=reason,
            time_in_phase_seconds=time_in_phase,
            last_confidence=confidence,
            confidence_delta=confidence_delta,
            time_since_last_test=time_since_last_test,
            recommendation=recommendation,
            details=details,
        )

        # Track statistics
        self.stats["total_detections"] += 1
        if is_stale:
            self.stats["stale_found"] += 1

        self.detection_history.append(verdict)

        return verdict

    def check_all_hypotheses(self, hypotheses: List, current_cycle: int) -> List[StalemateVerdict]:
        """
        Check all hypotheses for stalemate.

        Returns list of verdicts, with stale ones first.
        """
        verdicts = []

        for h in hypotheses:
            try:
                verdict = self.check_hypothesis(h, current_cycle)
                verdicts.append(verdict)
            except Exception as e:
                logger.error(f"Error checking hypothesis {h.id}: {e}")

        # Sort: stale hypotheses first
        verdicts.sort(key=lambda v: (not v.is_stale, -v.time_in_phase_seconds))

        return verdicts

    def get_stale_hypotheses(self, verdicts: List[StalemateVerdict]) -> List[StalemateVerdict]:
        """Get only the stale verdicts."""
        return [v for v in verdicts if v.is_stale]

    def apply_verdict(self, hypothesis, verdict: StalemateVerdict) -> bool:
        """
        Apply the stalemate verdict to a hypothesis.

        Returns True if action was taken (e.g., archived).
        """
        if not verdict.is_stale or verdict.recommendation != "archive":
            return False

        try:
            from .hypotheses import Phase

            # Archive the hypothesis
            hypothesis.phase = Phase.ARCHIVED
            hypothesis.updated_at = time.time()
            hypothesis.archived_at = time.time()

            self.stats["auto_archived"] += 1

            logger.info(
                f"Auto-archived stale hypothesis {verdict.hypothesis_id}: "
                f"{verdict.reason.value} - {verdict.details}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to archive hypothesis {verdict.hypothesis_id}: {e}")
            return False

    def cleanup_stale_hypotheses(self, hypotheses: List, current_cycle: int) -> Dict:
        """
        Check all hypotheses and automatically archive stale ones.

        Returns summary of actions taken.
        """
        verdicts = self.check_all_hypotheses(hypotheses, current_cycle)
        stale = self.get_stale_hypotheses(verdicts)

        archived_count = 0
        for verdict in stale:
            if verdict.recommendation == "archive":
                # Find the hypothesis object
                for h in hypotheses:
                    if h.id == verdict.hypothesis_id:
                        if self.apply_verdict(h, verdict):
                            archived_count += 1
                        break

        return {
            "checked": len(hypotheses),
            "stale_found": len(stale),
            "auto_archived": archived_count,
            "retained": len(stale) - archived_count,
        }

    def get_summary(self) -> Dict:
        """Get summary of stalemate detection activity."""
        return {
            "total_detections": self.stats["total_detections"],
            "stale_found": self.stats["stale_found"],
            "auto_archived": self.stats["auto_archived"],
            "recent_detections": [
                {
                    "hypothesis_id": v.hypothesis_id,
                    "hypothesis_name": v.hypothesis_name,
                    "reason": v.reason.value if v.reason else None,
                    "recommendation": v.recommendation,
                    "details": v.details,
                }
                for v in self.detection_history[-20:]  # Last 20
            ],
        }


def create_stalemate_detector() -> StalemateDetector:
    """Factory function for stalemate detector."""
    return StalemateDetector()
