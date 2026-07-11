"""
Test Script for Validation Pipeline Integration

This script tests the complete integration of the multi-stage ValidationPipeline
with the autonomous discovery system to ensure everything works correctly.

Version: 1.0.0
Date: 2026-07-01
"""

import asyncio
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_validation_pipeline():
    """Test the validation pipeline independently"""
    logger.info("Testing ValidationPipeline independently...")

    try:
        from astra_core.scientific_discovery.literature_validator import create_literature_validator
        from astra_core.scientific_discovery.validation_pipeline import create_validation_pipeline

        # Create validators
        logger.info("Creating literature validator...")
        lit_validator = create_literature_validator(
            enable_arxiv=True,
            enable_ads=True
        )

        logger.info("Creating validation pipeline...")
        pipeline = create_validation_pipeline(
            literature_validator=lit_validator,
            enable_citation_validation=True,
            enable_formula_validation=True,
            enable_statistical_validation=True,
            parallel_stages=True
        )

        # Test discovery with known results
        test_discovery = (
            "Molecular clouds exhibit a characteristic filament width of approximately 0.1 parsecs, "
            "as observed in Herschel surveys (Arzoumanian et al., 2011). This width is consistent "
            "across diverse environments with p < 0.001, suggesting a fundamental physical process "
            "regulating filament structure. The relationship between filament width and Jeans length "
            "suggests a connection to turbulent fragmentation (n = 150 clouds, r = 0.87)."
        )

        logger.info(f"Testing discovery: {test_discovery[:100]}...")

        # Run validation
        report = await pipeline.validate(
            discovery_claim=test_discovery,
            domains=["ism", "molecular_clouds"],
            discovery_type="pattern_discovery"
        )

        logger.info("✅ Validation pipeline test completed successfully!")
        logger.info(f"Overall Status: {report.overall_status.value}")
        logger.info(f"Confidence Level: {report.confidence_level.value}")
        logger.info(f"Total Time: {report.total_validation_time:.2f}s")

        # Print stage results
        logger.info("\nStage Results:")
        for result in report.stage_results:
            logger.info(f"  {result.stage.value}: passed={result.passed}, score={result.score:.3f}")

        # Print detailed reports
        if report.novelty_report:
            logger.info(f"\nNovelty Score: {report.novelty_report.novelty_score:.3f}")
            logger.info(f"Similar Papers Found: {len(report.novelty_report.similar_papers)}")

        if report.citation_report:
            logger.info(f"\nCitation Validation: {report.citation_report.verified_citations}/{report.citation_report.total_citations} verified")

        if report.formula_report:
            logger.info(f"\nFormula Validation: {report.formula_report.verified_formulas}/{report.formula_report.total_formulas} verified")

        if report.statistical_report:
            logger.info(f"\nStatistical Validation: {report.statistical_report}")

        return True

    except Exception as e:
        logger.error(f"❌ Validation pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_autonomous_integration():
    """Test the integration with autonomous discovery system"""
    logger.info("\nTesting autonomous discovery integration...")

    try:
        from astra_core.autonomous_startup_discovery_v2 import (
            GenuineDiscoverySystem,
            GenuineDiscoveryConfig,
            DiscoveryType
        )

        # Create discovery system
        logger.info("Creating GenuineDiscoverySystem...")
        config = GenuineDiscoveryConfig(
            discovery_interval_seconds=120,  # 2 minutes
            minimum_novelty_score=0.3,
            minimum_probability=0.5
        )

        discovery_system = GenuineDiscoverySystem(config=config)

        # Check if validation pipeline is initialized
        if discovery_system.validation_pipeline:
            logger.info("✅ Validation pipeline successfully integrated!")
            logger.info(f"Literature validator available: {discovery_system.literature_validator is not None}")

            # Test a simple validation
            test_result = (
                "Testing discovery integration: This is a test discovery about "
                "stellar formation in molecular clouds with observational evidence "
                "and statistical analysis (Smith et al., 2020, n=200, p<0.05)."
            )

            logger.info("Testing discovery validation...")
            validation = await discovery_system._validate_discovery(
                result_text=test_result,
                discovery_type=DiscoveryType.PATTERN_DISCOVERY,
                domains=["star_formation"]
            )

            logger.info("✅ Discovery validation completed!")
            logger.info(f"Novelty Score: {validation.novelty_score:.3f}")
            logger.info(f"Confidence Level: {validation.confidence_level}")
            logger.info(f"Validation Method: {validation.validation_method}")

            if validation.literature_similarity:
                logger.info(f"Literature Similarity: {validation.literature_similarity.most_similar_paper}")

            if validation.citation_validation:
                logger.info(f"Citation Validation: {validation.citation_validation.verified_citations}/{validation.citation_validation.total_citations} verified")

            return True
        else:
            logger.warning("❌ Validation pipeline not initialized in discovery system")
            return False

    except Exception as e:
        logger.error(f"❌ Autonomous integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_complete_workflow():
    """Test the complete workflow from discovery to validation"""
    logger.info("\nTesting complete discovery workflow...")

    try:
        from astra_core.autonomous_startup_discovery_v2 import (
            GenuineDiscoverySystem,
            GenuineDiscoveryConfig,
            DiscoveryType
        )

        # Create discovery system with validation
        config = GenuineDiscoveryConfig(
            discovery_interval_seconds=60,
            minimum_novelty_score=0.3,
            minimum_probability=0.4
        )

        discovery_system = GenuineDiscoverySystem(config=config)

        # Test the complete discovery cycle
        logger.info("Running discovery cycle test...")

        # Simulate a discovery result
        test_discovery_text = """
        Counterfactual Analysis: Arzoumanian et al. (2011) Filament Width Result

        Through reanalysis of Herschel field data, we find that the characteristic
        filament width of ~0.1 pc reported by Arzoumanian et al. (2011) shows
        systematic variation with local cloud environment. In high-density regions,
        the width narrows to 0.08±0.01 pc, while in low-density regions it broadens
        to 0.12±0.02 pc (n=85 filaments, p<0.01). This suggests that the universal
        width hypothesis may require refinement to account for environmental factors.

        The relationship between filament width (w) and cloud density (ρ) follows:
        w ∝ ρ^(-0.3±0.1), indicating a moderate dependence on environmental conditions.
        """

        logger.info("Processing discovery result...")
        discovery = await discovery_system._process_discovery_result(
            result_text=test_discovery_text,
            discovery_type=DiscoveryType.COMPUTATIONAL_REANALYSIS
        )

        if discovery:
            logger.info("✅ Discovery processed successfully!")
            logger.info(f"Title: {discovery.title}")
            logger.info(f"Novelty Level: {discovery.novelty_level.value}")
            logger.info(f"Novelty Score: {discovery.validation.novelty_score:.3f}")
            logger.info(f"Confidence Level: {discovery.validation.confidence_level}")

            if discovery.validation.literature_similarity:
                logger.info(f"Most Similar Paper: {discovery.validation.literature_similarity.most_similar_paper}")

            # Check if it meets genuine discovery standards
            meets_standards = discovery_system._meets_genuine_discovery_standards(discovery)
            logger.info(f"Meets Genuine Standards: {meets_standards}")

            return True
        else:
            logger.warning("❌ Discovery processing returned None")
            return False

    except Exception as e:
        logger.error(f"❌ Complete workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    logger.info("Starting Validation Pipeline Integration Tests")
    logger.info("="*60)

    results = []

    # Test 1: Validation Pipeline independently
    logger.info("\n📋 Test 1: Validation Pipeline")
    result1 = await test_validation_pipeline()
    results.append(("Validation Pipeline", result1))

    # Test 2: Autonomous Integration
    logger.info("\n📋 Test 2: Autonomous Integration")
    result2 = await test_autonomous_integration()
    results.append(("Autonomous Integration", result2))

    # Test 3: Complete Workflow
    logger.info("\n📋 Test 3: Complete Workflow")
    result3 = await test_complete_workflow()
    results.append(("Complete Workflow", result3))

    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed successfully!")
        return 0
    else:
        logger.error(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)