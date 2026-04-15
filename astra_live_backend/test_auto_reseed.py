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
Test auto-reseed mechanism for empty queue.

This test verifies that when the hypothesis queue becomes empty
(no hypotheses in SCREENING, TESTING, or PROPOSED phases), the
system automatically seeds new hypotheses to prevent idle.
"""
import pytest
import time
from unittest.mock import patch, MagicMock

from astra_live_backend.engine import DiscoveryEngine
from astra_live_backend.hypotheses import HypothesisStore, Phase


class TestAutoReseed:
    """Tests for automatic hypothesis reseeding when queue is empty."""

    @pytest.fixture
    def engine(self):
        """Create an engine with minimal dependencies for testing."""
        # Import may fail if dependencies missing - skip test in that case
        try:
            engine = DiscoveryEngine()
            yield engine
            # Cleanup
            if engine.running:
                engine.stop()
        except Exception as e:
            pytest.skip(f"Could not create engine: {e}")

    def test_empty_queue_triggers_reseed(self, engine):
        """When queue becomes completely empty, auto-reseed should activate."""
        # Clear all hypotheses from the store
        engine.store.hypotheses.clear()

        # Verify queue is empty
        screening = engine.store.by_phase(Phase.SCREENING)
        testing = engine.store.by_phase(Phase.TESTING)
        proposed = engine.store.by_phase(Phase.PROPOSED)

        assert len(screening) == 0, "SCREENING should be empty"
        assert len(testing) == 0, "TESTING should be empty"
        assert len(proposed) == 0, "PROPOSED should be empty"

        # Run lifecycle management (which includes auto-reseed check)
        engine._manage_hypothesis_lifecycle()

        # After lifecycle management, new hypotheses should be seeded
        all_hypotheses = engine.store.all()
        active_hypotheses = [h for h in all_hypotheses if h.phase != Phase.ARCHIVED]

        assert len(active_hypotheses) > 0, "Auto-reseed should create new hypotheses when queue is empty"

    def test_non_empty_queue_does_not_reseed(self, engine):
        """When queue has hypotheses, auto-reseed should NOT activate."""
        # Start with initial hypotheses (seeded during engine init)
        initial_count = len([h for h in engine.store.all() if h.phase != Phase.ARCHIVED])

        # Run lifecycle management
        engine._manage_hypothesis_lifecycle()

        # Count should not have increased significantly
        # (might have some small changes from lifecycle management, but no reseed)
        final_count = len([h for h in engine.store.all() if h.phase != Phase.ARCHIVED])

        # Allow for small changes (archiving, etc.) but no wholesale reseeding
        assert abs(final_count - initial_count) < 5, "Non-empty queue should not trigger full reseed"

    def test_only_proposed_does_not_trigger_reseed(self, engine):
        """Having only PROPOSED hypotheses should not trigger reseed."""
        # Clear all hypotheses
        engine.store.hypotheses.clear()

        # Add one hypothesis in PROPOSED phase
        from astra_live_backend.hypotheses import Hypothesis
        h = Hypothesis(
            id="TEST-001",
            name="Test Hypothesis",
            domain="Astrophysics",
            description="Test",
            confidence=0.25,
            phase=Phase.PROPOSED,
        )
        engine.store.hypotheses[h.id] = h

        # Run lifecycle management
        engine._manage_hypothesis_lifecycle()

        # Should NOT reseed because PROPOSED exists
        # (queue_depth = 0 but proposed_count = 1)
        all_hypotheses = engine.store.all()
        assert len(all_hypotheses) == 1, "Should not reseed when PROPOSED exists"

    def test_reseed_adds_multiple_domains(self, engine):
        """Auto-reseed should add hypotheses across multiple domains."""
        # Clear all hypotheses
        engine.store.hypotheses.clear()

        # Run lifecycle management to trigger reseed
        engine._manage_hypothesis_lifecycle()

        # Check that hypotheses span multiple domains
        all_hypotheses = engine.store.all()
        domains = {h.domain for h in all_hypotheses if h.phase != Phase.ARCHIVED}

        assert len(domains) >= 2, "Reseeded hypotheses should span multiple domains"
        assert "Astrophysics" in domains, "Should include Astrophysics domain"

    def test_reseed_hypotheses_are_active(self, engine):
        """Auto-reseeded hypotheses should start in active phases."""
        # Clear all hypotheses
        engine.store.hypotheses.clear()

        # Run lifecycle management to trigger reseed
        engine._manage_hypothesis_lifecycle()

        # Check that seeded hypotheses are in active phases (not ARCHIVED)
        active_hypotheses = [h for h in engine.store.all() if h.phase != Phase.ARCHIVED]
        archived_hypotheses = [h for h in engine.store.all() if h.phase == Phase.ARCHIVED]

        # All newly seeded hypotheses should be active
        # (ARCHIVED only comes from stalemate detection of old hypotheses)
        assert len(active_hypotheses) > 0, "Should have active hypotheses after reseed"
        # All or most should be non-archived (newly seeded)
        assert len(archived_hypotheses) == 0, "Newly seeded hypotheses should not be archived"


def test_standalone_reseed():
    """Standalone test that can run without full engine."""
    from astra_live_backend.hypotheses import HypothesisStore, Phase, seed_initial_hypotheses

    store = HypothesisStore()

    # Should be empty initially
    assert len(store.all()) == 0, "New store should be empty"

    # Seed hypotheses
    seed_initial_hypotheses(store)

    # Should now have hypotheses
    all_hypotheses = store.all()
    assert len(all_hypotheses) > 0, "Seeding should add hypotheses"

    # Check domains
    domains = {h.domain for h in all_hypotheses}
    assert "Astrophysics" in domains, "Should include Astrophysics"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
