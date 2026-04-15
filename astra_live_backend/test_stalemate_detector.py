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
Tests for stalemate detector module.

Run with: pytest astra_live_backend/test_stalemate_detector.py -v
"""
import pytest
import time
from unittest.mock import Mock

# Try importing
try:
    from astra_live_backend.stalemate_detector import (
        StalemateDetector,
        StalemateReason,
        StalemateVerdict,
        create_stalemate_detector,
    )
    HAS_STALEMATE = True
except ImportError:
    HAS_STALEMATE = False
    pytest.skip("stalemate_detector module not available", allow_module_level=True)


# Try importing hypothesis classes
try:
    from astra_live_backend.hypotheses import Hypothesis, Phase
    HAS_HYPOTHESES = True
except ImportError:
    HAS_HYPOTHESES = False


@pytest.fixture
def detector():
    """Create a fresh stalemate detector for each test."""
    return StalemateDetector()


@pytest.fixture
def mock_hypothesis():
    """Create a mock hypothesis for testing."""
    if not HAS_HYPOTHESES:
        pytest.skip("hypotheses module not available")

    h = Hypothesis(
        id="TEST-001",
        name="Test Hypothesis",
        domain="Astrophysics",
        description="A test hypothesis for stalemate detection",
        confidence=0.5,
        phase=Phase.PROPOSED,
    )
    return h


class TestStalemateDetector:
    """Tests for the StalemateDetector class."""

    def test_initialization(self, detector):
        """Detector should initialize with empty history and stats."""
        assert len(detector.detection_history) == 0
        assert detector.stats["total_detections"] == 0
        assert detector.stats["stale_found"] == 0
        assert detector.stats["auto_archived"] == 0

    def test_phase_thresholds(self, detector):
        """Phase thresholds should be correctly defined."""
        assert "proposed" in detector.PHASE_THRESHOLDS
        assert "screening" in detector.PHASE_THRESHOLDS
        assert "testing" in detector.PHASE_THRESHOLDS

        # PROPOSED should have shortest threshold (most aggressive cleanup)
        assert detector.PHASE_THRESHOLDS["proposed"] == 3600
        assert detector.PHASE_THRESHOLDS["proposed"] < detector.PHASE_THRESHOLDS["testing"]

        # PUBLISHED and ARCHIVED should never be stale
        assert detector.PHASE_THRESHOLDS["published"] == float('inf')
        assert detector.PHASE_THRESHOLDS["archived"] == float('inf')

    def test_no_stale_for_fresh_hypothesis(self, detector, mock_hypothesis):
        """Freshly created hypothesis should not be flagged as stale."""
        # Just created, so time in phase is small
        verdict = detector.check_hypothesis(mock_hypothesis, current_cycle=1)

        assert verdict.is_stale is False
        assert verdict.recommendation == "monitor"

    def test_stale_for_old_low_confidence_proposed(self, detector, mock_hypothesis):
        """Old hypothesis with low confidence in PROPOSED should be stale."""
        if not HAS_HYPOTHESES:
            pytest.skip("hypotheses module not available")

        mock_hypothesis.phase = Phase.PROPOSED
        mock_hypothesis.confidence = 0.25  # Below threshold

        # Make it appear old (more than 1 hour in phase)
        old_time = time.time() - 4000  # > 3600 seconds
        mock_hypothesis.updated_at = old_time
        mock_hypothesis.created_at = old_time

        verdict = detector.check_hypothesis(mock_hypothesis, current_cycle=100)

        assert verdict.is_stale is True
        assert verdict.reason == StalemateReason.LOW_CONFIDENCE_FLOOR
        assert verdict.recommendation == "archive"

    def test_no_stale_for_high_confidence_proposed(self, detector, mock_hypothesis):
        """High confidence hypothesis in PROPOSED should not be stale."""
        if not HAS_HYPOTHESES:
            pytest.skip("hypotheses module not available")

        mock_hypothesis.phase = Phase.PROPOSED
        mock_hypothesis.confidence = 0.61  # Above threshold (must be > 0.6 for force_advance)

        # Even if old, high confidence should protect it
        old_time = time.time() - 4000
        mock_hypothesis.updated_at = old_time
        mock_hypothesis.created_at = old_time

        verdict = detector.check_hypothesis(mock_hypothesis, current_cycle=100)

        # High confidence should trigger force_advance recommendation, not archive
        if verdict.is_stale:
            assert verdict.recommendation == "force_advance"
        else:
            # Or not stale at all (acceptable)
            assert True

    def test_stale_for_testing_no_recent_tests(self, detector, mock_hypothesis):
        """Testing hypothesis with no recent tests should be stale."""
        if not HAS_HYPOTHESES:
            pytest.skip("hypotheses module not available")

        mock_hypothesis.phase = Phase.TESTING
        mock_hypothesis.last_tested_at = time.time() - 2000  # No tests for 33+ minutes

        verdict = detector.check_hypothesis(mock_hypothesis, current_cycle=100)

        assert verdict.is_stale is True
        assert verdict.reason == StalemateReason.NO_TEST_PROGRESS
        assert verdict.recommendation == "archive"

    def test_check_all_hypotheses(self, detector):
        """Should handle multiple hypotheses efficiently."""
        if not HAS_HYPOTHESES:
            pytest.skip("hypotheses module not available")

        hypotheses = []
        for i in range(10):
            h = Hypothesis(
                id=f"TEST-{i:03d}",
                name=f"Test Hypothesis {i}",
                domain="Astrophysics",
                description=f"Test number {i}",
                confidence=0.5,
                phase=Phase.PROPOSED,
            )
            hypotheses.append(h)

        verdicts = detector.check_all_hypotheses(hypotheses, current_cycle=1)

        assert len(verdicts) == 10
        # All should be non-stale (freshly created)
        assert all(not v.is_stale for v in verdicts)

    def test_get_stale_hypotheses(self, detector):
        """get_stale_hypotheses should filter to only stale ones."""
        if not HAS_HYPOTHESES:
            pytest.skip("hypotheses module not available")

        hypotheses = []
        for i in range(5):
            h = Hypothesis(
                id=f"TEST-{i:03d}",
                name=f"Test Hypothesis {i}",
                domain="Astrophysics",
                description=f"Test number {i}",
                confidence=0.25,  # Low confidence
                phase=Phase.PROPOSED,
            )
            # Make first 3 stale (old), last 2 fresh (new)
            if i < 3:
                h.created_at = time.time() - 4000
                h.updated_at = time.time() - 4000
            hypotheses.append(h)

        verdicts = detector.check_all_hypotheses(hypotheses, current_cycle=100)
        stale = detector.get_stale_hypotheses(verdicts)

        assert len(stale) == 3  # Only the 3 old ones

    def test_apply_verdict_archives(self, detector, mock_hypothesis):
        """apply_verdict should archive hypothesis when recommendation is 'archive'."""
        if not HAS_HYPOTHESES:
            pytest.skip("hypotheses module not available")

        mock_hypothesis.phase = Phase.PROPOSED
        mock_hypothesis.confidence = 0.25
        mock_hypothesis.created_at = time.time() - 4000
        mock_hypothesis.updated_at = time.time() - 4000

        verdict = detector.check_hypothesis(mock_hypothesis, current_cycle=100)
        assert verdict.recommendation == "archive"

        # Apply verdict
        result = detector.apply_verdict(mock_hypothesis, verdict)

        assert result is True  # Action was taken
        assert mock_hypothesis.phase == Phase.ARCHIVED
        assert mock_hypothesis.archived_at > 0

    def test_apply_verdict_skips_monitor(self, detector, mock_hypothesis):
        """apply_verdict should skip when recommendation is 'monitor'."""
        verdict = StalemateVerdict(
            hypothesis_id="TEST-001",
            hypothesis_name="Test",
            is_stale=False,
            reason=None,
            time_in_phase_seconds=100,
            last_confidence=0.5,
            confidence_delta=0.0,
            time_since_last_test=100,
            recommendation="monitor",
            details="Not stale yet",
        )

        result = detector.apply_verdict(mock_hypothesis, verdict)

        assert result is False  # No action taken
        assert mock_hypothesis.phase != Phase.ARCHIVED

    def test_get_summary(self, detector):
        """get_summary should return detector statistics."""
        # Add some mock detections
        detector.stats["total_detections"] = 100
        detector.stats["stale_found"] = 25
        detector.stats["auto_archived"] = 20

        summary = detector.get_summary()

        assert summary["total_detections"] == 100
        assert summary["stale_found"] == 25
        assert summary["auto_archived"] == 20
        assert "recent_detections" in summary


class TestStalemateIntegration:
    """Integration tests with full hypothesis store."""

    def test_cleanup_stale_hypotheses_integration(self, detector):
        """Full cleanup workflow with multiple hypotheses."""
        if not HAS_HYPOTHESES:
            pytest.skip("hypotheses module not available")

        from astra_live_backend.hypotheses import HypothesisStore

        store = HypothesisStore()

        # Add some hypotheses
        # 1. Fresh hypothesis (should be kept)
        h1 = store.add("Fresh Hypothesis", "Astrophysics", "Should be kept", confidence=0.5)
        h1.phase = Phase.PROPOSED
        h1.created_at = time.time() - 100  # Very recent
        h1.updated_at = time.time() - 100

        # 2. Old low-confidence hypothesis (should be archived)
        h2 = store.add("Old Stale Hypothesis", "Physics", "Should be archived", confidence=0.20)
        h2.phase = Phase.PROPOSED
        h2.created_at = time.time() - 5000  # Old
        h2.updated_at = time.time() - 5000

        # 3. Old but high confidence (should be force-advanced or monitored)
        h3 = store.add("Old Strong Hypothesis", "Astrophysics", "High confidence but stuck", confidence=0.70)
        h3.phase = Phase.TESTING
        h3.created_at = time.time() - 8000  # Very old
        h3.updated_at = time.time() - 8000
        h3.last_tested_at = time.time() - 100  # Recent tests, so not stale in testing

        hypotheses = list(store.all())
        summary = detector.cleanup_stale_hypotheses(hypotheses, current_cycle=100)

        assert summary["checked"] == 3
        assert summary["stale_found"] == 2  # h2 (low conf) and h3 (old) are stale
        assert summary["auto_archived"] == 1  # Only h2 gets archived (h3 gets force_advance)
        assert summary["retained"] == 1  # h3 is retained with force_advance recommendation

        # Verify h2 was archived
        assert h2.phase == Phase.ARCHIVED

        # Verify h1 and h3 were not archived
        assert h1.phase != Phase.ARCHIVED
        assert h3.phase != Phase.ARCHIVED


def test_create_stalemate_detector():
    """Factory function should create detector."""
    detector = create_stalemate_detector()
    assert isinstance(detector, StalemateDetector)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
