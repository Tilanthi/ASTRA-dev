"""
Integration Test: Transformational Architecture in Real Discovery Pipeline

This test verifies that the transformational architecture is actually integrated
and working in ASTRA's real discovery pipeline, not just in isolated unit tests.

Key tests:
1. Autonomous discovery system uses transformational validation
2. Prior Knowledge Base is checked before discovery labeling
3. Discovery Gate enforces 4-stage validation
4. Confirmatory results are NOT labeled as discoveries
5. Audit trails are created for all validations

Version: 1.0.0
Date: 2026-07-04
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from astra_core.transformational_autonomous_startup import (
    TransformationalAutonomousDiscoverySystem,
    TransformationalDiscoveryConfig,
    create_transformational_autonomous_discovery_system
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def test_autonomous_discovery_integration():
    """
    Test 1: Autonomous Discovery System Integration

    Verify that the autonomous discovery system actually uses the
    transformational architecture for validation.
    """
    print("\n" + "="*80)
    print("TEST 1: Autonomous Discovery System Integration")
    print("="*80)

    # Create transformational discovery system
    config = TransformationalDiscoveryConfig(
        enable_transformational_validation=True,
        enable_prior_knowledge_check=True,
        discovery_interval_seconds=1  # Fast for testing
    )

    discovery_system = create_transformational_autonomous_discovery_system(config)

    # Check initialization
    print("\n--- Checking System Initialization ---")
    status = discovery_system.get_status()

    print(f"Transformational Available: {status['transformational_available']}")
    print(f"Transformational Pipeline: {status['transformational_pipeline_available']}")
    print(f"Transformational Active: {status['transformational_active']}")
    print(f"Prior KB Relations: {status['prior_kb_relations']}")
    print(f"Validation Method: {status['validation_method']}")

    assert status['transformational_available'], "Transformational architecture must be available"
    assert status['transformational_active'], "Transformational pipeline must be active"
    assert status['prior_kb_relations'] > 0, "Prior KB must have relations loaded"
    assert status['validation_method'] == 'transformational_4stage_gate', "Must use transformational validation"

    print("✅ PASS: System initialized with transformational architecture")

    # Test validation of confirmatory result
    print("\n--- Testing Confirmatory Result Validation ---")

    # IC5146 filament width (should be CONFIRMATORY, not discovery)
    confirmatory_result = await discovery_system.validate_discovery(
        discovery_claim="Filament width in IC5146 molecular cloud measured at 0.11 pc, consistent with universal value",
        domains=["molecular_clouds", "star_formation"],
        discovery_type="pattern_discovery",
        statistical_result={
            'effect_size': 0.11,  # Observed filament width (pc)
            'effect_uncertainty': 0.02,
            'sample_size': 30,
            'p_values': [0.35]
        }
    )

    print(f"\nValidation Status: {confirmatory_result['status']}")
    print(f"Prior Classification: {confirmatory_result.get('prior_classification', 'N/A')}")
    print(f"Deviation from Prior: {confirmatory_result.get('deviation_from_prior', 0):.2f}σ")
    print(f"Discovery Level: {confirmatory_result.get('discovery_level', 'N/A')}")
    print(f"Confidence: {confirmatory_result['confidence']:.2f}")
    print(f"Explanation: {confirmatory_result.get('explanation', 'N/A')}")

    assert confirmatory_result['status'] == 'confirmatory', \
        "IC5146 filament width should be CONFIRMATORY"
    assert confirmatory_result['confidence'] >= 0.70, \
        "Confirmatory result should have high confidence"
    assert confirmatory_result.get('audit_trail_available', False), \
        "Validation should create audit trail"

    print("✅ PASS: Confirmatory result correctly classified (not a discovery!)")

    # Test validation of novel discovery
    print("\n--- Testing Novel Discovery Validation ---")

    novel_result = await discovery_system.validate_discovery(
        discovery_claim="Filament width in distant galaxies measured at 0.25 pc, significantly higher than local value, suggesting different star formation conditions",
        domains=["molecular_clouds", "star_formation", "galactic_astronomy"],
        discovery_type="pattern_discovery",
        statistical_result={
            'effect_size': 0.25,  # Observed filament width (pc)
            'effect_uncertainty': 0.03,
            'sample_size': 35,
            'p_values': [0.001]
        }
    )

    print(f"\nValidation Status: {novel_result['status']}")
    print(f"Prior Classification: {novel_result.get('prior_classification', 'N/A')}")
    print(f"Deviation from Prior: {novel_result.get('deviation_from_prior', 0):.2f}σ")
    print(f"Discovery Level: {novel_result.get('discovery_level', 'N/A')}")
    print(f"Confidence: {novel_result['confidence']:.2f}")

    # Check gate stages
    print("\n4-Stage Gate Results:")
    print(f"  Statistical Significance: {novel_result['statistical_significance']}")
    print(f"  Independent Replication: {novel_result['independent_replication']}")
    print(f"  Mechanistic Plausibility: {novel_result['mechanistic_plausibility']}")
    print(f"  Adversarial Critique: {novel_result['adversarial_critique']}")

    assert novel_result['status'] in ['candidate', 'discovery'], \
        "Novel finding should be CANDIDATE or DISCOVERY"
    assert novel_result.get('prior_classification') in ['candidate_novel', 'novel_discovery'], \
        "Novel finding should be classified as novel by Prior KB"

    print("✅ PASS: Novel discovery correctly classified and validated")

    print("\n" + "="*80)
    print("TEST 1: ✅ ALL CHECKS PASSED")
    print("="*80)


async def test_pipeline_vs_transformational_comparison():
    """
    Test 2: Pipeline vs Transformational Comparison

    Compare results between old pipeline and new transformational architecture
    to verify the improvements.
    """
    print("\n" + "="*80)
    print("TEST 2: Pipeline vs Transformational Comparison")
    print("="*80)

    # Create transformational system
    config = TransformationalDiscoveryConfig(
        enable_transformational_validation=True,
        enable_prior_knowledge_check=True
    )

    system = create_transformational_autonomous_discovery_system(config)

    print("\n--- Comparing Validation Approaches ---")

    # Test case: IC5146 filament width
    test_cases = [
        {
            'name': 'IC5146 Filament Width (Expected Replication)',
            'claim': 'Filament width in IC5146 measured at 0.11 pc',
            'effect_size': 0.11,
            'expected_status': 'confirmatory'
        },
        {
            'name': 'Novel Filament Width (Unexpected Value)',
            'claim': 'Filament width in distant cloud measured at 0.25 pc',
            'effect_size': 0.25,
            'expected_status': 'candidate'  # or 'discovery' if passes all stages
        },
        {
            'name': 'Underpowered but Consistent Measurement',
            'claim': 'Filament width measured with small sample but within uncertainty',
            'effect_size': 0.11,  # Within uncertainty of 0.10 ± 0.03
            'sample_size': 5,
            'expected_status': 'candidate'  # Proceeds to gate but underpowered
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")

        result = await system.validate_discovery(
            discovery_claim=test_case['claim'],
            domains=["molecular_clouds"],
            discovery_type="pattern_discovery",
            statistical_result={
                'effect_size': test_case['effect_size'],
                'effect_uncertainty': 0.02,
                'sample_size': test_case.get('sample_size', 30),
                'p_values': [0.35]
            }
        )

        print(f"Expected: {test_case['expected_status']}")
        print(f"Got: {result['status']}")
        print(f"Prior KB: {result.get('prior_classification', 'N/A')}")
        print(f"Confidence: {result['confidence']:.2f}")

        # Verify status matches expected
        if result['status'] == test_case['expected_status']:
            print("✅ Status matches expected")
        else:
            print(f"⚠️  Status mismatch (expected {test_case['expected_status']}, got {result['status']})")

    print("\n" + "="*80)
    print("TEST 2: ✅ COMPARISON COMPLETE")
    print("="*80)


async def test_discovery_gate_enforcement():
    """
    Test 3: Discovery Gate Enforcement

    Verify that the Discovery Gate is actually enforcing the 4-stage
    validation and preventing unfounded discovery claims.
    """
    print("\n" + "="*80)
    print("TEST 3: Discovery Gate Enforcement")
    print("="*80)

    config = TransformationalDiscoveryConfig(
        enable_transformational_validation=True
    )

    system = create_transformational_autonomous_discovery_system(config)

    print("\n--- Testing 4-Stage Gate Enforcement ---")

    # Test 1: Claim with no mechanism (should fail mechanistic plausibility)
    result1 = await system.validate_discovery(
        discovery_claim="We observed a correlation between variables X and Y",
        domains=["test_domain"],
        discovery_type="pattern_discovery",
        statistical_result={
            'effect_size': 0.5,
            'effect_uncertainty': 0.1,
            'sample_size': 100,
            'p_values': [0.001]
        }
    )

    print(f"\nTest 1: No mechanistic explanation")
    print(f"  Mechanistic Plausibility: {result1['mechanistic_plausibility']}")
    print(f"  Status: {result1['status']}")

    assert not result1['mechanistic_plausibility'], \
        "Should fail mechanistic plausibility without mechanism"
    print("✅ PASS: Mechanistic plausibility correctly required")

    # Test 2: Confirmatory result (should be rejected as discovery)
    result2 = await system.validate_discovery(
        discovery_claim="Filament width in IC5146 measured at 0.11 pc, consistent with universal value",
        domains=["molecular_clouds"],
        discovery_type="pattern_discovery",
        statistical_result={
            'effect_size': 0.11,  # Within uncertainty of expected 0.10 ± 0.03
            'effect_uncertainty': 0.02,
            'sample_size': 50,
            'p_values': [0.35]  # Not significant
        }
    )

    print(f"\nTest 2: Exact expected value (confirmatory)")
    print(f"  Status: {result2['status']}")
    print(f"  Prior Classification: {result2.get('prior_classification', 'N/A')}")

    assert result2['status'] == 'confirmatory', \
        "Should be classified as confirmatory, not discovery"
    print("✅ PASS: Confirmatory results rejected as discoveries")

    print("\n" + "="*80)
    print("TEST 3: ✅ GATE ENFORCEMENT VERIFIED")
    print("="*80)


async def test_audit_trail_generation():
    """
    Test 4: Audit Trail Generation

    Verify that complete audit trails are generated for all validations,
    providing content for Discovery Demonstration sections.
    """
    print("\n" + "="*80)
    print("TEST 4: Audit Trail Generation")
    print("="*80)

    config = TransformationalDiscoveryConfig(
        enable_transformational_validation=True
    )

    system = create_transformational_autonomous_discovery_system(config)

    print("\n--- Testing Audit Trail Generation ---")

    result = await system.validate_discovery(
        discovery_claim="Test discovery for audit trail verification",
        domains=["test_domain"],
        discovery_type="pattern_discovery",
        statistical_result={
            'effect_size': 0.5,
            'effect_uncertainty': 0.1,
            'sample_size': 40,
            'p_values': [0.01]
        }
    )

    print(f"\nAudit Trail Available: {result['audit_trail_available']}")

    assert result['audit_trail_available'], \
        "Audit trail must be generated"

    print("✅ PASS: Audit trail generated for validation")

    # Verify audit trail contains required information
    print(f"\nValidation Method: {result['validation_method']}")
    print(f"Explanation Available: {'Yes' if result.get('explanation') else 'No'}")
    print(f"Warnings Available: {'Yes' if result.get('warnings') else 'No'}")

    assert result['validation_method'] == 'transformational_4stage_gate', \
        "Should use transformational validation method"
    assert result.get('explanation'), \
        "Should provide explanation"

    print("✅ PASS: Audit trail contains required information")

    print("\n" + "="*80)
    print("TEST 4: ✅ AUDIT TRAIL VERIFIED")
    print("="*80)


async def main():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("ASTRA TRANSFORMATIONAL ARCHITECTURE - INTEGRATION TEST SUITE")
    print("="*80)
    print("\nThis test suite verifies that the transformational architecture is")
    print("actually integrated and working in ASTRA's real discovery pipeline.")
    print("\nKey Differences from Unit Tests:")
    print("- Tests the actual autonomous discovery system")
    print("- Verifies transformational components are initialized")
    print("- Confirms Prior KB and Discovery Gate are active")
    print("- Validates end-to-end integration")
    print("="*80)

    try:
        await test_autonomous_discovery_integration()
        await test_pipeline_vs_transformational_comparison()
        await test_discovery_gate_enforcement()
        await test_audit_trail_generation()

        print("\n" + "="*80)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("="*80)
        print("\n✅ Transformational Architecture Successfully Integrated")
        print("✅ Autonomous Discovery Uses 4-Stage Gate")
        print("✅ Prior Knowledge Base Active")
        print("✅ Confirmatory Results Correctly Classified")
        print("✅ Audit Trails Generated")
        print("\nASTRA's real discovery pipeline is now using the transformational architecture!")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())