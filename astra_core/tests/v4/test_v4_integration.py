"""
STAN-XI-ASTRO V4.0 Integration Tests

Tests for the integrated V4.0 system with all four capabilities.

Version: 4.0.0
Date: 2026-03-17
"""

import pytest
import sys
from pathlib import Path

# Add project root directory to path for imports
# Tests are in: astra_core/tests/v4/
# Project root is: ../ (from astra_core)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestV4Integration:
    """Test V4.0 integration coordinator."""

    def test_v4_coordinator_creation(self):
        """Test that V4 coordinator can be created."""
        from astra_core.v4_revolutionary import create_v4_coordinator

        coordinator = create_v4_coordinator()
        assert coordinator is not None
        assert coordinator.state is not None

    def test_v4_system_status(self):
        """Test getting system status."""
        from astra_core.v4_revolutionary import create_v4_coordinator

        coordinator = create_v4_coordinator()
        status = coordinator.get_system_status()

        assert "version" in status
        assert "capabilities" in status
        assert "total_processed" in status

    def test_v4_process_query(self):
        """Test processing a query."""
        from astra_core.v4_revolutionary import create_v4_coordinator, IntegrationMode

        coordinator = create_v4_coordinator()
        result = coordinator.process_query(
            "What is consciousness?",
            mode=IntegrationMode.MINIMAL
        )

        assert result is not None
        assert hasattr(result, "answer")
        assert hasattr(result, "confidence")
        assert hasattr(result, "used_capabilities")

    def test_v4_graceful_degradation(self):
        """Test graceful degradation."""
        from astra_core.v4_revolutionary import create_v4_coordinator

        coordinator = create_v4_coordinator()

        # Test graceful degradation for each capability
        for capability in ["mce", "asc", "crn", "mmol"]:
            result = coordinator.graceful_degradation(capability)
            assert result is True


class TestMCEIntegration:
    """Test Meta-Context Engine integration."""

    def test_mce_creation(self):
        """Test MCE can be created."""
        from astra_core.metacognitive.meta_context_engine import create_meta_context_engine

        mce = create_meta_context_engine()
        assert mce is not None

    def test_context_layering(self):
        """Test context layering."""
        from astra_core.metacognitive.meta_context_engine import create_meta_context_engine

        mce = create_meta_context_engine()
        result = mce.layer_context(
            query="What is consciousness?",
            dimensions=["temporal", "perceptual"],
            preferred_frames=["predictive"]
        )

        assert result is not None


class TestASCIntegration:
    """Test Autocatalytic Self-Compiler integration."""

    def test_asc_creation(self):
        """Test ASC can be created."""
        from astra_core.self_teaching.autocatalytic_compiler import create_autocatalytic_self_compiler

        asc = create_autocatalytic_self_compiler()
        assert asc is not None


class TestCRNIntegration:
    """Test Cognitive-Relativity Navigator integration."""

    def test_crn_creation(self):
        """Test CRN can be created."""
        from astra_core.reasoning.cognitive_relativity_navigator import create_cognitive_relativity_navigator

        crn = create_cognitive_relativity_navigator()
        assert crn is not None

    def test_abstraction_levels(self):
        """Test abstraction level management."""
        from astra_core.reasoning.cognitive_relativity_navigator import create_cognitive_relativity_navigator

        crn = create_cognitive_relativity_navigator()
        result = crn.adaptive_abstraction(50)

        assert result is not None
        assert hasattr(result, "height")


class TestMMOLIntegration:
    """Test Multi-Mind Orchestration Layer integration."""

    def test_mmol_creation(self):
        """Test MMOL can be created."""
        from astra_core.intelligence.multi_mind_orchestrator import create_multi_mind_orchestrator

        mmol = create_multi_mind_orchestrator()
        assert mmol is not None

    def test_specialized_minds(self):
        """Test specialized minds can be created."""
        from astra_core.intelligence.specialized_minds import (
            create_physics_mind, create_empathy_mind, create_political_mind,
            create_poetic_mind, create_mathematical_mind, create_causal_mind,
            create_creative_mind
        )

        minds = {
            "physics": create_physics_mind(),
            "empathy": create_empathy_mind(),
            "political": create_political_mind(),
            "poetic": create_poetic_mind(),
            "mathematical": create_mathematical_mind(),
            "causal": create_causal_mind(),
            "creative": create_creative_mind()
        }

        for mind_id, mind in minds.items():
            assert mind is not None
            assert hasattr(mind, "process")


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "What is the nature of consciousness?"


@pytest.fixture
def sample_context():
    """Sample context for testing."""
    return {
        "domain": "philosophy",
        "complexity": 0.7,
        "abstraction_preference": "high"
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
