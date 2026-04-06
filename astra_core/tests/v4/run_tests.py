#!/usr/bin/env python3
"""
STAN-XI-ASTRO V4.0 Test Runner

Simple test runner for V4.0 capabilities.

Usage:
    python astra_core/tests/v4/run_tests.py              # Run all tests
    python astra_core/tests/v4/run_tests.py --mce        # Test MCE only
    python astra_core/tests/v4/run_tests.py --asc        # Test ASC only
    python astra_core/tests/v4/run_tests.py --crn        # Test CRN only
    python astra_core/tests/v4/run_tests.py --mmol       # Test MMOL only
    python astra_core/tests/v4/run_tests.py --integration # Test integration only

Version: 4.0.0
Date: 2026-03-17
"""

import sys
import argparse
from pathlib import Path

# Add project root directory to path for imports
# Tests are in: astra_core/tests/v4/
# Project root is: ../ (from astra_core)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def run_mce_tests():
    """Run MCE tests."""
    print("Testing Meta-Context Engine (MCE)...")
    try:
        from astra_core.metacognitive.meta_context_engine import create_meta_context_engine

        mce = create_meta_context_engine()
        print("✓ MCE created successfully")

        # Test context layering
        result = mce.layer_context(
            query="What is consciousness?",
            dimensions=["temporal", "perceptual"],
            preferred_frames=["predictive"]
        )
        print("✓ Context layering works")

        # Test statistics
        stats = mce.get_statistics()
        print(f"✓ MCE statistics: {stats.get('active_layers', 0)} active layers")

        print("\n✅ MCE tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ MCE tests failed: {e}")
        return False


def run_asc_tests():
    """Run ASC tests."""
    print("Testing Autocatalytic Self-Compiler (ASC)...")
    try:
        from astra_core.self_teaching.autocatalytic_compiler import create_autocatalytic_self_compiler

        asc = create_autocatalytic_self_compiler()
        print("✓ ASC created successfully")

        # Test version management
        current_version = asc.get_current_version()
        print(f"✓ Current version: {current_version}")

        print("\n✅ ASC tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ ASC tests failed: {e}")
        return False


def run_crn_tests():
    """Run CRN tests."""
    print("Testing Cognitive-Relativity Navigator (CRN)...")
    try:
        from astra_core.reasoning.cognitive_relativity_navigator import create_cognitive_relativity_navigator

        crn = create_cognitive_relativity_navigator()
        print("✓ CRN created successfully")

        # Test abstraction
        result = crn.adaptive_abstraction(50)
        print(f"✓ Adaptive abstraction: height={result.height}")

        print("\n✅ CRN tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ CRN tests failed: {e}")
        return False


def run_mmol_tests():
    """Run MMOL tests."""
    print("Testing Multi-Mind Orchestration Layer (MMOL)...")
    try:
        from astra_core.intelligence.multi_mind_orchestrator import create_multi_mind_orchestrator
        from astra_core.intelligence.specialized_minds import (
            create_physics_mind, create_empathy_mind, create_political_mind,
            create_poetic_mind, create_mathematical_mind, create_causal_mind,
            create_creative_mind
        )

        mmol = create_multi_mind_orchestrator()
        print("✓ MMOL created successfully")

        # Test specialized minds
        minds = {
            "physics": create_physics_mind(),
            "empathy": create_empathy_mind(),
            "political": create_political_mind(),
            "poetic": create_poetic_mind(),
            "mathematical": create_mathematical_mind(),
            "causal": create_causal_mind(),
            "creative": create_creative_mind()
        }
        print(f"✓ Created {len(minds)} specialized minds")

        print("\n✅ MMOL tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ MMOL tests failed: {e}")
        return False


def run_integration_tests():
    """Run integration tests."""
    print("Testing V4.0 Integration...")
    try:
        from astra_core.v4_revolutionary import create_v4_coordinator, IntegrationMode

        coordinator = create_v4_coordinator()
        print("✓ V4 coordinator created")

        # Test processing
        result = coordinator.process_query(
            "What is consciousness?",
            mode=IntegrationMode.MINIMAL
        )
        print(f"✓ Query processed: {len(result.used_capabilities)} capabilities used")

        # Test system status
        status = coordinator.get_system_status()
        print(f"✓ System status: {status['version']}")

        print("\n✅ Integration tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ Integration tests failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("STAN-XI-ASTRO V4.0 Test Suite")
    print("=" * 60)
    print()

    results = {
        "MCE": run_mce_tests(),
        "ASC": run_asc_tests(),
        "CRN": run_crn_tests(),
        "MMOL": run_mmol_tests(),
        "Integration": run_integration_tests()
    }

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for capability, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{capability:15s}: {status}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} test suites passed")

    return all(results.values())


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="STAN-XI-ASTRO V4.0 Test Runner")
    parser.add_argument("--mce", action="store_true", help="Test MCE only")
    parser.add_argument("--asc", action="store_true", help="Test ASC only")
    parser.add_argument("--crn", action="store_true", help="Test CRN only")
    parser.add_argument("--mmol", action="store_true", help="Test MMOL only")
    parser.add_argument("--integration", action="store_true", help="Test integration only")

    args = parser.parse_args()

    if args.mce:
        success = run_mce_tests()
        sys.exit(0 if success else 1)
    elif args.asc:
        success = run_asc_tests()
        sys.exit(0 if success else 1)
    elif args.crn:
        success = run_crn_tests()
        sys.exit(0 if success else 1)
    elif args.mmol:
        success = run_mmol_tests()
        sys.exit(0 if success else 1)
    elif args.integration:
        success = run_integration_tests()
        sys.exit(0 if success else 1)
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
