"""
Test script to validate Phase 2-4 enhancements

This script tests the new domain system, physics engine, and validation framework.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_domain_system():
    """Test domain system"""
    print("\n=== Testing Domain System ===")

    try:
        from astra_core.domains import DomainRegistry
        from astra_core.domains.exoplanets import ExoplanetDomain

        # Create registry
        registry = DomainRegistry()

        # Create and register domain
        exoplanet_domain = ExoplanetDomain()
        registry.register_domain(exoplanet_domain)

        # Test query
        result = exoplanet_domain.process_query(
            "What determines the transit depth of an exoplanet?",
            {
                'parameters': {
                    'r_planet': 6.371e8,  # Earth radius in cm
                    'r_star': 6.957e10   # Sun radius in cm
                }
            }
        )

        print(f"✓ Domain system initialized")
        print(f"✓ Exoplanet domain registered")
        print(f"✓ Query processed: {result.answer[:80]}...")
        print(f"✓ Confidence: {result.confidence:.2f}")
        print(f"✓ Capabilities used: {result.capabilities_used}")

        # Test domain registry
        domains = registry.list_domains()
        print(f"✓ Registered domains: {domains}")

        # Test domain discovery
        status = registry.get_registry_status()
        print(f"✓ Registry status: {status['total_domains']} domains loaded")

        return True

    except Exception as e:
        print(f"✗ Domain system test failed: {e}")
        return False


def test_meta_learning():
    """Test cross-domain meta-learning"""
    print("\n=== Testing Cross-Domain Meta-Learning ===")

    try:
        from astra_core.reasoning.cross_domain_meta_learner import (
            CrossDomainMetaLearner,
            DomainFeatures,
            DomainSimilarity
        )

        # Create meta-learner
        learner = CrossDomainMetaLearner()

        # Register domain features
        exoplanet_features = DomainFeatures(
            domain_name="exoplanets",
            temporal_scale=(1e3, 1e8),  # Seconds to years
            spatial_scale=(1e8, 1e13),  # Planet to system
            physical_processes=["transit", "orbital_motion", "atmospheric_physics"],
            observational_techniques=["photometry", "spectroscopy", "timing"],
            theoretical_frameworks=["kepler_laws", "radiative_transfer"],
            keywords=["exoplanet", "transit", "orbit", "planet"]
        )

        gw_features = DomainFeatures(
            domain_name="gravitational_waves",
            temporal_scale=(1e-3, 1e2),  # Milliseconds to minutes
            spatial_scale=(1e6, 1e12),  # Compact objects to galaxies
            physical_processes=["inspiral", "merger", "ringdown"],
            observational_techniques=["interferometry", "timing"],
            theoretical_frameworks=["general_relativity", "black_holes"],
            keywords=["gravitational wave", "gw", "merger", "black_hole"]
        )

        learner.register_domain_features("exoplanets", exoplanet_features)
        learner.register_domain_features("gravitational_waves", gw_features)

        # Test similarity computation
        similarity = learner.compute_domain_similarity("exoplanets", "gravitational_waves")

        print(f"✓ Meta-learner initialized")
        print(f"✓ Domain features registered")
        print(f"✓ Similarity computed: {similarity.similarity_score:.3f}")
        print(f"✓ Transferable concepts: {similarity.transferable_concepts}")

        # Test adaptation prediction
        prediction = learner.predict_adaptation_performance("exoplanets", "gravitational_waves", n_examples=5)
        print(f"✓ Adaptation performance prediction: {prediction['expected_performance']:.3f}")
        print(f"✓ Recommended strategy: {prediction['recommended_strategy']}")

        return True

    except Exception as e:
        print(f"✗ Meta-learning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_physics_engine():
    """Test unified physics engine"""
    print("\n=== Testing Unified Physics Engine ===")

    try:
        from astra_core.physics import (
            UnifiedPhysicsEngine,
            PhysicsDomain,
            PhysicsResult
        )

        # Create physics engine
        engine = UnifiedPhysicsEngine()

        # Test basic computation
        result = engine.compute(
            model_name='newtonian_gravity',
            parameters={'mass': 1.989e33, 'distance': 1.496e13},
            compute_gradient=True,
            enforce_constraints=True
        )

        print(f"✓ Physics engine initialized")
        print(f"✓ Models available: {list(engine.models.keys())[:5]}...")
        print(f"✓ Computed gravity: {result.value:.6e} dyne/cm")
        print(f"✓ Constraints: {len(engine.constraints)} constraints registered")
        print(f"✓ Constraint violations: {result.constraint_violations}")

        # Test multiple models
        bb_result = engine.compute(
            model_name='blackbody',
            parameters={'wavelength': 5e-5, 'temperature': 5778}
        )
        print(f"✓ Blackbody spectrum computed: {bb_result.value:.6e} erg/cm²/s/cm")

        return True

    except Exception as e:
        print(f"✗ Physics engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_physics_curriculum():
    """Test physics curriculum learning"""
    print("\n=== Testing Physics Curriculum Learning ===")

    try:
        from astra_core.physics import PhysicsCurriculum, ComplexityLevel

        # Create curriculum
        curriculum = PhysicsCurriculum()

        # Learn at basic mechanics stage
        progress = curriculum.learn_at_stage("basic_mechanics", n_problems=5)

        print(f"✓ Physics curriculum initialized")
        print(f"✓ Stages available: {list(curriculum.stages.keys())}")
        print(f"✓ Learning progress at basic_mechanics:")
        print(f"  - Performance: {progress.performance:.3f}")
        print(f"  - Mastery: {progress.mastery:.3f}")
        print(f"  - Ready for next: {progress.ready_for_next}")

        # Get intuition assessment
        intuition = curriculum.get_intuition_assessment()
        print(f"✓ Intuition assessment: {intuition['overall_mastery']:.3f}")

        return True

    except Exception as e:
        print(f"✗ Physics curriculum test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_benchmarks():
    """Test validation benchmarks"""
    print("\n=== Testing Validation Benchmarks ===")

    try:
        from astra_core.tests.validation_benchmarks import (
            ValidationSuite,
            BenchmarkResult,
            run_validation_suite
        )

        # Run validation suite
        summary = run_validation_suite()

        print(f"✓ Validation suite initialized")
        print(f"✓ Benchmarks run: {summary['total_benchmarks']}")
        print(f"✓ Passed: {summary['passed']}")
        print(f"✓ Failed: {summary['failed']}")
        print(f"✓ Pass rate: {summary['pass_rate']:.1%}")
        print(f"✓ Average score: {summary['average_score']:.3f}")

        # Show individual results
        for name, result in summary['individual_results'].items():
            status = "PASS" if result['passed'] else "FAIL"
            print(f"  {name}: {status} (score: {result['score']:.3f}, threshold: {result['threshold']:.3f})")

        return summary['pass_rate'] >= 0.6

    except Exception as e:
        print(f"✗ Validation benchmarks failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_system():
    """Test enhanced unified system"""
    print("\n=== Testing Enhanced Unified System ===")

    try:
        from astra_core.core.unified_enhanced import (
            EnhancedUnifiedSTANSystem,
            EnhancedUnifiedConfig,
            create_enhanced_stan_system
        )

        # Create enhanced system
        system = create_enhanced_stan_system()

        print(f"✓ Enhanced system created")

        # Get system status
        status = system.get_system_status()

        print(f"✓ System status retrieved:")
        print(f"  - Base system: {status['base_system']}")
        print(f"  - Domains enabled: {status['domains']['enabled']}")
        print(f"  - Domains loaded: {status['domains']['loaded']}")
        print(f"  - Available domains: {status['domains']['available']}")
        print(f"  - Meta-learning: {status['meta_learning']['enabled']}")
        print(f"  - Physics engine: {status['physics']['engine']}")
        print(f"  - Physics curriculum: {status['physics']['curriculum']}")
        print(f"  - Analogical reasoner: {status['physics']['analogical']}")

        # Test query processing
        result = system.process_query(
            "Calculate the orbital velocity of Earth around the Sun",
            context={'parameters': {'mass': 1.989e33, 'radius': 1.496e13}}
        )

        print(f"✓ Query processed successfully")
        print(f"  - Mode: {result['mode']}")
        print(f"  - Answer: {result['answer'][:80]}...")
        print(f"  - Confidence: {result['confidence']:.2f}")

        return True

    except Exception as e:
        print(f"✗ Enhanced system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("=" * 70)
    print("STAN-XI-ASTRO Phase 2-4 Enhancement Validation")
    print("=" * 70)

    tests = [
        ("Domain System", test_domain_system),
        ("Cross-Domain Meta-Learning", test_meta_learning),
        ("Unified Physics Engine", test_physics_engine),
        ("Physics Curriculum", test_physics_curriculum),
        ("Validation Benchmarks", test_validation_benchmarks),
        ("Enhanced Unified System", test_enhanced_system),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            logger.error(f"Test {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\nTotal: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%)")

    if passed_count == total_count:
        print("\n✓ All Phase 2-4 enhancements validated successfully!")
        return 0
    else:
        print(f"\n⚠ {total_count - passed_count} test(s) failed - please review")
        return 1


if __name__ == "__main__":
    exit(main())
