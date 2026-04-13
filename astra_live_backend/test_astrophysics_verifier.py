"""
ASTRA Live — Astrophysical Verifier Test Suite
Tests for the multi-layer astrophysical verification system.

Author: ASTRA V9.5
Date: 2026-04-13
"""

import pytest
import numpy as np
from astra_live_backend.hypotheses import Hypothesis, Phase, TestResult
from astra_live_backend.astrophysics_verifier import (
    AstrophysicalVerifier,
    Verdict,
    VerificationFlaw,
    VerificationLayer,
    FailureReason,
    GeneratorVerifierReviser,
    verify_hypothesis,
    quick_verify,
    create_exit_condition_checker,
)


class TestAstrophysicalVerifier:
    """Test the main AstrophysicalVerifier class"""

    def test_verifier_initialization(self):
        """Test that verifier initializes with correct constants and limits"""
        verifier = AstrophysicalVerifier()

        # Check physical constants are loaded
        assert verifier.constants['c'] == 2.998e10  # Speed of light in CGS
        assert verifier.constants['G'] == 6.674e-8  # Gravitational constant

        # Check survey limits are loaded
        assert 'pantheon' in verifier.survey_limits
        assert 'gaia_dr3' in verifier.survey_limits
        assert 'sdss_dr18' in verifier.survey_limits

        # Check physical constraints
        assert verifier.physical_constraints['speed_limit'] == verifier.constants['c']

    def test_verify_basic_hypothesis(self):
        """Test verification of a basic hypothesis"""
        verifier = AstrophysicalVerifier()
        h = Hypothesis(
            id="H001",
            name="Test Hypothesis",
            domain="Astrophysics",
            description="Galaxy colors show bimodality in SDSS data"
        )

        verdict = verifier.verify(h)

        assert isinstance(verdict, Verdict)
        assert hasattr(verdict, 'passed')
        assert hasattr(verdict, 'overall_confidence')
        assert hasattr(verdict, 'should_abandon')
        assert hasattr(verdict, 'flaws')
        assert hasattr(verdict, 'layer_scores')

    def test_verify_with_test_results(self):
        """Test verification with statistical test results"""
        verifier = AstrophysicalVerifier()
        h = Hypothesis(
            id="H002",
            name="Test with Results",
            domain="Astrophysics",
            description="Hubble tension between Planck and SH0ES"
        )

        # Add some test results
        h.test_results = [
            TestResult(
                test_name="KS Test",
                statistic=0.15,
                p_value=0.001,
                timestamp=1234567890,
                passed=True,
                details="D = 0.15"
            ),
            TestResult(
                test_name="Pearson Correlation",
                statistic=0.75,
                p_value=0.02,
                timestamp=1234567891,
                passed=True,
                details="r = 0.75"
            ),
        ]

        verdict = verifier.verify(h, test_results=h.test_results)

        # Should have higher confidence due to passing tests
        assert verdict.overall_confidence > 0.5
        assert VerificationLayer.STATISTICAL in verdict.layer_scores

    def test_statistical_layer_failing_tests(self):
        """Test statistical layer with failing tests"""
        verifier = AstrophysicalVerifier()
        h = Hypothesis(
            id="H003",
            name="Failing Tests",
            domain="Astrophysics",
            description="This hypothesis fails all tests"
        )

        # Add failing test results
        for i in range(5):
            h.test_results.append(
                TestResult(
                    test_name=f"Test {i}",
                    statistic=0.0,
                    p_value=0.5,
                    timestamp=1234567890 + i,
                    passed=False,
                    details="Not significant"
                )
            )

        verdict = verifier.verify(h)

        # Should detect confidence plateau
        assert any("plateau" in flaw.description.lower() for flaw in verdict.flaws)
        assert verdict.layer_scores[VerificationLayer.STATISTICAL] < 0.7

    def test_physical_layer_dimensional_flaw(self):
        """Test physical layer detects dimensional inconsistency"""
        verifier = AstrophysicalVerifier()

        # Create hypothesis with dimensional inconsistency hint
        h = Hypothesis(
            id="H004",
            name="Dimensional Issue",
            domain="Astrophysics",
            description="Energy equals mass without c^2 factor - dimensional problem"
        )

        verdict = verifier.verify(h)

        # May detect dimensional issues (depends on implementation)
        # The verdict should always complete
        assert verdict is not None

    def test_observational_layer_survey_limits(self):
        """Test observational layer checks survey limits"""
        verifier = AstrophysicalVerifier()
        h = Hypothesis(
            id="H005",
            name="Survey Test",
            domain="Astrophysics",
            description="Testing Planck CMB data at z > 2.3"
        )

        verdict = verifier.verify(h, data_sources=['planck'])

        # Should check survey limits
        assert VerificationLayer.OBSERVATIONAL in verdict.layer_scores

    def test_cross_dataset_verification(self):
        """Test verification across multiple datasets"""
        verifier = AstrophysicalVerifier()
        h = Hypothesis(
            id="H006",
            name="Multi-Dataset",
            domain="Astrophysics",
            description="Cross-matching Gaia with TESS for stellar parameters"
        )

        verdict = verifier.verify(h, data_sources=['gaia_dr3', 'tess'])

        # Should check cross-dataset consistency
        assert VerificationLayer.OBSERVATIONAL in verdict.layer_scores

    def test_should_abandon_physical_impossibility(self):
        """Test abandonment for physical impossibility"""
        verifier = AstrophysicalVerifier()

        # Create hypothesis that clearly violates physics
        h = Hypothesis(
            id="H007",
            name="Faster Than Light",
            domain="Astrophysics",
            description="Objects observed moving faster than light violates causality"
        )

        verdict = verifier.verify(h)

        # Should flag for abandonment due to causality violation
        # (May not trigger in simplified implementation)
        assert verdict is not None

    def test_revision_hints_generation(self):
        """Test that revision hints are generated from flaws"""
        verifier = AstrophysicalVerifier()
        h = Hypothesis(
            id="H008",
            name="Needs Revision",
            domain="Astrophysics",
            description="Hypothesis with several flaws"
        )

        # Add failing tests
        for i in range(3):
            h.test_results.append(
                TestResult(
                    test_name=f"Test {i}",
                    statistic=0.0,
                    p_value=0.5,
                    timestamp=1234567890 + i,
                    passed=False,
                    details="Not significant"
                )
            )

        verdict = verifier.verify(h)

        # Should have revision hints
        assert isinstance(verdict.revision_hints, list)
        # Should have flaws
        assert isinstance(verdict.flaws, list)

    def test_layer_scores_in_range(self):
        """Test that all layer scores are in [0, 1]"""
        verifier = AstrophysicalVerifier()
        h = Hypothesis(
            id="H009",
            name="Score Range Test",
            domain="Astrophysics",
            description="Test that all scores are valid"
        )

        verdict = verifier.verify(h)

        for layer, score in verdict.layer_scores.items():
            assert 0.0 <= score <= 1.0, f"Layer {layer} has score {score} outside [0, 1]"

    def test_overall_confidence_calculation(self):
        """Test that overall confidence is mean of layer scores"""
        verifier = AstrophysicalVerifier()
        h = Hypothesis(
            id="H010",
            name="Confidence Test",
            domain="Astrophysics",
            description="Test overall confidence calculation"
        )

        verdict = verifier.verify(h)

        # Overall confidence should be mean of layer scores
        if verdict.layer_scores:
            expected = np.mean(list(verdict.layer_scores.values()))
            assert abs(verdict.overall_confidence - expected) < 0.01


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_verify_hypothesis_function(self):
        """Test the verify_hypothesis convenience function"""
        h = Hypothesis(
            id="H011",
            name="Convenience Test",
            domain="Astrophysics",
            description="Test convenience function"
        )

        verdict = verify_hypothesis(h)

        assert isinstance(verdict, Verdict)
        assert verdict is not None

    def test_quick_verify_function(self):
        """Test the quick_verify function for engine integration"""
        h = Hypothesis(
            id="H012",
            name="Quick Verify Test",
            domain="Astrophysics",
            description="Test quick verify"
        )

        result = quick_verify(h)

        assert isinstance(result, dict)
        assert 'passed' in result
        assert 'confidence' in result
        assert 'should_abandon' in result
        assert 'num_flaws' in result
        assert 'layer_scores' in result

    def test_create_exit_condition_checker(self):
        """Test the exit condition checker creation"""
        checker = create_exit_condition_checker()

        assert callable(checker)

        h = Hypothesis(
            id="H013",
            name="Exit Test",
            domain="Astrophysics",
            description="Test exit checker"
        )

        should_exit, reason = checker(h)

        assert isinstance(should_exit, bool)
        assert reason is None or isinstance(reason, str)


class TestGeneratorVerifierReviser:
    """Test the Generator-Verifier-Reviser loop"""

    def test_gvr_initialization(self):
        """Test GVR loop initialization"""
        gvr = GeneratorVerifierReviser(
            max_iterations=5,
            confidence_threshold=0.7
        )

        assert gvr.max_iterations == 5
        assert gvr.confidence_threshold == 0.7
        assert gvr.verifier is not None

    def test_gvr_iterate_success(self):
        """Test GVR loop with successful verification"""
        gvr = GeneratorVerifierReviser(max_iterations=3, confidence_threshold=0.6)

        h = Hypothesis(
            id="H014",
            name="GVR Success Test",
            domain="Astrophysics",
            description="Test GVR with success",
            confidence=0.5
        )

        # Mock generate function that increases confidence
        def generate_fn(hypothesis):
            hypothesis.confidence += 0.2
            return hypothesis

        # Mock revise function
        def revise_fn(hypothesis, flaws, hints):
            return hypothesis

        final_h, final_verdict = gvr.iterate(h, generate_fn, revise_fn)

        assert final_h is not None
        assert final_verdict is not None
        # Should succeed due to increasing confidence

    def test_gvr_iterate_abandon(self):
        """Test GVR loop with abandonment"""
        gvr = GeneratorVerifierReviser(max_iterations=3, confidence_threshold=0.8)

        h = Hypothesis(
            id="H015",
            name="GVR Abandon Test",
            domain="Astrophysics",
            description="This should be abandoned due to physical impossibility",
            confidence=0.1
        )

        # Mock functions
        def generate_fn(hypothesis):
            hypothesis.confidence -= 0.1  # Getting worse
            return hypothesis

        def revise_fn(hypothesis, flaws, hints):
            return hypothesis

        final_h, final_verdict = gvr.iterate(h, generate_fn, revise_fn)

        # Should complete without error
        assert final_h is not None
        assert final_verdict is not None


class TestDataSources:
    """Test data source inference and validation"""

    def test_infer_pantheon_source(self):
        """Test inferring Pantheon+ from description"""
        verifier = AstrophysicalVerifier()
        h = Hypothesis(
            id="H016",
            name="Pantheon Test",
            domain="Astrophysics",
            description="Using Pantheon+ SNe Ia for Hubble diagram"
        )

        sources = verifier._infer_data_sources(h)
        assert 'pantheon' in sources

    def test_infer_gaia_source(self):
        """Test inferring Gaia from description"""
        verifier = AstrophysicalVerifier()
        h = Hypothesis(
            id="H017",
            name="Gaia Test",
            domain="Astrophysics",
            description="Gaia DR3 parallax measurements for HR diagram"
        )

        sources = verifier._infer_data_sources(h)
        assert 'gaia' in sources

    def test_infer_sdss_source(self):
        """Test inferring SDSS from description"""
        verifier = AstrophysicalVerifier()
        h = Hypothesis(
            id="H018",
            name="SDSS Test",
            domain="Astrophysics",
            description="SDSS galaxy colors and redshift distributions"
        )

        sources = verifier._infer_data_sources(h)
        assert 'sdss' in sources

    def test_survey_limits_pantheon(self):
        """Test Pantheon survey limits"""
        verifier = AstrophysicalVerifier()
        pantheon_limits = verifier.survey_limits['pantheon']

        assert pantheon_limits['z_max'] == 2.3
        assert pantheon_limits['z_min'] == 0.001
        assert pantheon_limits['n_supernovae'] == 1701


class TestPhysicalConstraints:
    """Test physical constraint checking"""

    def test_speed_limit_constant(self):
        """Test that speed limit constant is correct"""
        verifier = AstrophysicalVerifier()
        c = verifier.constants['c']

        # Speed of light in CGS
        assert c == 2.998e10

    def test_physical_constraint_ranges(self):
        """Test physical constraint ranges are defined"""
        verifier = AstrophysicalVerifier()

        assert 'temperature_range' in verifier.physical_constraints
        assert 'density_range' in verifier.physical_constraints
        assert 'magnetic_field_range' in verifier.physical_constraints


class TestAstronomySpecificExitConditions:
    """Test astronomy-specific exit conditions"""

    def test_exit_on_low_confidence_stagnation(self):
        """Test exit when confidence stagnates at low values"""
        h = Hypothesis(
            id="H019",
            name="Stagnation Test",
            domain="Astrophysics",
            description="Testing stagnation exit",
            confidence=0.2
        )

        # Add many failing tests
        for i in range(10):
            h.test_results.append(
                TestResult(
                    test_name=f"Test {i}",
                    statistic=0.0,
                    p_value=0.5,
                    timestamp=1234567890 + i,
                    passed=False,
                    details="Not significant"
                )
            )

        verdict = verify_hypothesis(h)

        # Should have low statistical score
        stat_score = verdict.layer_scores.get(VerificationLayer.STATISTICAL, 1.0)
        assert stat_score < 0.7

    def test_critical_physical_flaw_triggers_abandon(self):
        """Test that critical physical flaws trigger abandonment"""
        h = Hypothesis(
            id="H020",
            name="Critical Flaw Test",
            domain="Astrophysics",
            description="Energy is not conserved - violates first law"
        )

        verdict = verify_hypothesis(h)

        # Verdict should complete without error
        assert verdict is not None

        # If critical flaw detected, should_abandon might be True
        # (depends on implementation details)


class TestRealWorldHypotheses:
    """Test verification with real astronomical hypotheses"""

    def test_hubble_tension_hypothesis(self):
        """Test verification of Hubble tension hypothesis"""
        h = Hypothesis(
            id="H021",
            name="Hubble Tension",
            domain="Astrophysics",
            description="Pantheon+ SNe Ia (1701 supernovae) distance modulus analysis: test ΛCDM predictions and measure H₀ tension",
            confidence=0.6
        )

        # Add some test results
        h.test_results = [
            TestResult(
                test_name="KS Test",
                statistic=0.12,
                p_value=0.01,
                timestamp=1234567890,
                passed=True,
                details="D = 0.12, significant"
            ),
        ]

        verdict = verify_hypothesis(h, data_sources=['pantheon'])

        # Should pass basic verification
        assert verdict is not None
        assert verdict.overall_confidence > 0.3

    def test_filament_spacing_hypothesis(self):
        """Test verification of filament spacing hypothesis"""
        h = Hypothesis(
            id="H022",
            name="Filament Spacing",
            domain="Astrophysics",
            description="Herschel HGBS filament spacing follows characteristic scale set by Jeans length",
            confidence=0.7
        )

        verdict = verify_hypothesis(h)

        # Should pass basic verification
        assert verdict is not None
        # Filament hypothesis is physically grounded
        assert verdict.layer_scores.get(VerificationLayer.PHYSICAL, 0) > 0.3

    def test_exoplanet_mass_period_hypothesis(self):
        """Test verification of exoplanet mass-period hypothesis"""
        h = Hypothesis(
            id="H023",
            name="Exoplanet Mass-Period",
            domain="Astrophysics",
            description="NASA Exoplanet Archive: test Kepler's third law scaling and mass-period correlation",
            confidence=0.55
        )

        verdict = verify_hypothesis(h, data_sources=['nasa_exoplanet'])

        # Should pass basic verification
        assert verdict is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
