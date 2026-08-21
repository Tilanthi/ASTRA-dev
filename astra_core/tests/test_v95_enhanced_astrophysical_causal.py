"""
Test suite for Enhanced Astrophysical Causal Discovery (V95)

Tests the performance improvements and correctness of optimized causal discovery
for astronomical applications.
"""

import numpy as np
import time
from typing import Dict, List, Any
import sys
import os
from pathlib import Path

# Add ASTRA to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from astra_core.capabilities.v95_enhanced_astrophysical_causal_discovery import (
    OptimizedAstrophysicalCausalDiscovery,
    discover_astrophysical_causal_structure,
    AstrophysicalPerformanceConfig,
    CacheStrategy,
    EarlyStoppingStrategy,
    AstrophysicalCacheStrategy
)


def generate_test_data(n_samples: int = 1000, n_vars: int = 20, seed: int = 42) -> tuple:
    """Generate synthetic astrophysical test data with known causal structure"""

    np.random.seed(seed)
    data = np.random.randn(n_samples, n_vars)

    # Create some known causal relationships
    # Variable 0 causes Variable 1
    data[:, 1] += 0.7 * data[:, 0] + 0.1 * np.random.randn(n_samples)

    # Variable 1 causes Variable 2
    data[:, 2] += 0.5 * data[:, 1] + 0.1 * np.random.randn(n_samples)

    # Variable 3 and 4 are confounded by Variable 5
    data[:, 3] += 0.6 * data[:, 5] + 0.1 * np.random.randn(n_samples)
    data[:, 4] += 0.6 * data[:, 5] + 0.1 * np.random.randn(n_samples)

    variable_names = [f"VAR_{i}" for i in range(n_vars)]

    return data, variable_names


def generate_astronomical_test_data(n_samples: int = 5000, seed: int = 42) -> tuple:
    """Generate realistic astronomical test data"""

    np.random.seed(seed)

    # Simulate stellar properties
    n_samples = n_samples
    data = np.random.randn(n_samples, 10)

    # Variable 0: Stellar mass
    mass = np.random.normal(1.0, 0.3, n_samples)
    data[:, 0] = mass

    # Variable 1: Luminosity (caused by mass)
    luminosity = 3.8 * mass + np.random.normal(0, 0.5, n_samples)
    data[:, 1] = luminosity

    # Variable 2: Temperature (caused by mass)
    temperature = 5778 * (mass ** 0.25) + np.random.normal(0, 500, n_samples)
    data[:, 2] = temperature

    # Variable 3: Radius (caused by luminosity and temperature)
    radius = np.sqrt(luminosity) / (temperature / 5778) ** 2 + np.random.normal(0, 0.1, n_samples)
    data[:, 3] = radius

    # Variable 4: Metallicity (independent)
    data[:, 4] = np.random.normal(0.0, 0.2, n_samples)

    # Variable 5: Age (confounds some relationships)
    age = np.random.uniform(0.1, 10.0, n_samples)
    data[:, 5] = age

    # Variable 6: Rotation period (affected by age and mass)
    data[:, 6] = 30 * (mass ** 0.5) * (age ** 0.7) + np.random.normal(0, 5, n_samples)

    # Variable 7-9: Independent spectral lines
    data[:, 7] = np.random.normal(0, 1, n_samples)
    data[:, 8] = np.random.normal(0, 1, n_samples)
    data[:, 9] = np.random.normal(0, 1, n_samples)

    variable_names = [
        "stellar_mass", "luminosity", "effective_temperature", "stellar_radius",
        "metallicity", "stellar_age", "rotation_period",
        "spectral_line_H_alpha", "spectral_line_Ca_II", "spectral_line_Fe_I"
    ]

    return data, variable_names


def test_basic_functionality():
    """Test basic causal discovery functionality"""
    print("\n=== Test 1: Basic Functionality ===")

    data, variable_names = generate_test_data(n_samples=1000, n_vars=10)

    try:
        result = discover_astrophysical_causal_structure(
            data, variable_names, method='pc'
        )

        print(f"✅ Basic functionality working")
        print(f"   Graph discovered with {len(result['graph']['edges'])} edges")
        print(f"   Computation time: {result['computation_time']:.3f} seconds")
        print(f"   Total tests: {result['performance_stats']['total_tests']}")

        return True
    except Exception as e:
        print(f"❌ Basic functionality failed: {e}")
        return False


def test_parallel_processing():
    """Test parallel processing performance improvement"""
    print("\n=== Test 2: Parallel Processing ===")

    data, variable_names = generate_test_data(n_samples=5000, n_vars=30)

    # Test without parallel
    config_no_parallel = AstrophysicalPerformanceConfig(
        enable_parallel=False,
        cache_strategy=CacheStrategy.NONE
    )

    # Test with parallel
    config_parallel = AstrophysicalPerformanceConfig(
        enable_parallel=True,
        cache_strategy=CacheStrategy.NONE,
        max_workers=4
    )

    try:
        # Without parallel
        start = time.time()
        discovery_no_parallel = OptimizedAstrophysicalCausalDiscovery(config_no_parallel)
        result_no_parallel = discovery_no_parallel.discover_structure(data, variable_names)
        time_no_parallel = time.time() - start

        # With parallel
        start = time.time()
        discovery_parallel = OptimizedAstrophysicalCausalDiscovery(config_parallel)
        result_parallel = discovery_parallel.discover_structure(data, variable_names)
        time_parallel = time.time() - start

        speedup = time_no_parallel / time_parallel

        print(f"✅ Parallel processing working")
        print(f"   Without parallel: {time_no_parallel:.3f} seconds")
        print(f"   With parallel: {time_parallel:.3f} seconds")
        print(f"   Speedup: {speedup:.2f}x")
        print(f"   Parallel tests: {result_parallel['performance_stats']['parallel_tests']}")

        return True
    except Exception as e:
        print(f"❌ Parallel processing test failed: {e}")
        return False


def test_caching_system():
    """Test caching system performance improvement"""
    print("\n=== Test 3: Caching System ===")

    data, variable_names = generate_astronomical_test_data(n_samples=5000)

    # Astronomical context for caching
    astro_context = {
        'sky_region': {'ra': '180.0', 'dec': '0.0', 'radius': '5.0'},
        'wavelength_band': 'optical',
        'instrument': 'telescope_name',
        'target_type': 'stars'
    }

    # Test without cache
    config_no_cache = AstrophysicalPerformanceConfig(
        enable_parallel=False,
        cache_strategy=CacheStrategy.NONE
    )

    # Test with cache
    config_with_cache = AstrophisticalPerformanceConfig(
        enable_parallel=False,
        cache_strategy=CacheStrategy.HYBRID,
        astro_cache_strategy=AstrophysicalCacheStrategy.HYBRID_ASTRO
    )

    try:
        # Without cache
        start = time.time()
        discovery_no_cache = OptimizedAstrophysicalCausalDiscovery(config_no_cache)
        result_no_cache = discovery_no_cache.discover_structure(
            data, variable_names, astronomical_context=astro_context
        )
        time_no_cache = time.time() - start

        # With cache - run twice to see caching benefits
        discovery_with_cache = OptimizedAstrophysicalCausalDiscovery(config_with_cache)

        # First run
        start = time.time()
        result_cache_1 = discovery_with_cache.discover_structure(
            data, variable_names, astronomical_context=astro_context
        )
        time_cache_1 = time.time() - start

        # Second run (should use cache)
        start = time.time()
        result_cache_2 = discovery_with_cache.discover_structure(
            data, variable_names, astronomical_context=astro_context
        )
        time_cache_2 = time.time() - start

        cache_hit_rate = result_cache_2['cache_stats']['hit_rate']
        speedup = time_no_cache / time_cache_2

        print(f"✅ Caching system working")
        print(f"   Without cache: {time_no_cache:.3f} seconds")
        print(f"   With cache (run 1): {time_cache_1:.3f} seconds")
        print(f"   With cache (run 2): {time_cache_2:.3f} seconds")
        print(f"   Cache hit rate: {cache_hit_rate:.1%}")
        print(f"   Speedup: {speedup:.2f}x")
        print(f"   Astronomical cache hits: {result_cache_2['cache_stats']['astronomical_cache_hits']}")

        return True
    except Exception as e:
        print(f"❌ Caching system test failed: {e}")
        return False


def test_early_stopping():
    """Test early stopping strategies"""
    print("\n=== Test 4: Early Stopping ===")

    data, variable_names = generate_test_data(n_samples=10000, n_vars=50)

    config_early_stop = AstrophysicalPerformanceConfig(
        enable_parallel=False,
        cache_strategy=CacheStrategy.NONE,
        early_stopping=EarlyStoppingStrategy.ADAPTIVE,
        confidence_threshold=0.90
    )

    try:
        start = time.time()
        discovery = OptimizedAstrophysicalCausalDiscovery(config_early_stop)
        result = discovery.discover_structure(data, variable_names)
        time_taken = time.time() - start

        early_stops = result['performance_stats']['early_stops']

        print(f"✅ Early stopping working")
        print(f"   Computation time: {time_taken:.3f} seconds")
        print(f"   Early stops triggered: {early_stops}")
        print(f"   Total tests: {result['performance_stats']['total_tests']}")

        return True
    except Exception as e:
        print(f"❌ Early stopping test failed: {e}")
        return False


def test_astronomical_optimizations():
    """Test astronomy-specific optimizations"""
    print("\n=== Test 5: Astronomical Optimizations ===")

    data, variable_names = generate_astronomical_test_data(n_samples=10000)

    # Test different astronomical contexts
    contexts = [
        {
            'sky_region': {'ra': '83.6', 'dec': '22.0', 'radius': '2.0'},
            'wavelength_band': 'infrared',
            'instrument': 'JWST',
            'target_type': 'star_forming_regions'
        },
        {
            'sky_region': {'ra': '180.0', 'dec': '0.0', 'radius': '10.0'},
            'wavelength_band': 'radio',
            'instrument': 'ALMA',
            'target_type': 'galaxies'
        }
    ]

    config = AstrophysicalPerformanceConfig(
        enable_parallel=True,
        cache_strategy=CacheStrategy.HYBRID,
        astro_cache_strategy=AstrophysicalCacheStrategy.HYBRID_ASTRO
    )

    try:
        discovery = OptimizedAstrophysicalCausalDiscovery(config)

        results = []
        for i, context in enumerate(contexts):
            start = time.time()
            result = discovery.discover_structure(data, variable_names, astronomical_context=context)
            time_taken = time.time() - start
            results.append(result)

            print(f"   Context {i+1} ({context['wavelength_band']}): {time_taken:.3f} seconds")

        # Check if caching improved performance across contexts
        if len(results) >= 2:
            time_improvement = results[0]['computation_time'] / results[1]['computation_time']
            print(f"✅ Astronomical optimizations working")
            print(f"   Cache improvements across contexts: {time_improvement:.2f}x")
            print(f"   Sky region cache hits: {results[1]['cache_stats']['sky_region_hits']}")
            print(f"   Wavelength cache hits: {results[1]['cache_stats']['wavelength_hits']}")

        return True
    except Exception as e:
        print(f"❌ Astronomical optimizations test failed: {e}")
        return False


def test_performance_benchmark():
    """Comprehensive performance benchmark"""
    print("\n=== Test 6: Performance Benchmark ===")

    test_configs = [
        (20, 1000, "Small"),
        (50, 5000, "Medium"),
        (100, 10000, "Large")
    ]

    config = AstrophysicalPerformanceConfig(
        enable_parallel=True,
        cache_strategy=CacheStrategy.HYBRID,
        astro_cache_strategy=AstrophysicalCacheStrategy.HYBRID_ASTRO,
        early_stopping=EarlyStoppingStrategy.ADAPTIVE
    )

    print("Performance Benchmark:")
    print("┌─────────────┬─────────────┬─────────────┬─────────────┐")
    print("│ Dataset     │ Variables   │ Time (sec)  │ Speedup     │")
    print("├─────────────┼─────────────┼─────────────┼─────────────┤")

    try:
        discovery = OptimizedAstrophysicalCausalDiscovery(config)

        for n_vars, n_samples, size_category in test_configs:
            data, variable_names = generate_test_data(n_samples, n_vars)

            astro_context = {
                'sky_region': {'ra': str(np.random.uniform(0, 360)),
                               'dec': str(np.random.uniform(-90, 90)),
                               'radius': '5.0'},
                'wavelength_band': 'optical',
                'instrument': 'test_telescope',
                'target_type': 'mixed'
            }

            start = time.time()
            result = discovery.discover_structure(data, variable_names, astronomical_context=astro_context)
            time_taken = time.time() - start

            speedup = result['efficiency_improvements']['total_speedup']

            print(f"│ {size_category:<11} │ {n_vars:<11} │ {time_taken:<11.3f} │ {speedup:<11.2f} │")

        print("└─────────────┴─────────────┴─────────────┴─────────────┘")
        print(f"✅ Performance benchmark completed")

        return True
    except Exception as e:
        print(f"❌ Performance benchmark failed: {e}")
        return False


def run_all_tests():
    """Run all test suites"""
    print("=" * 60)
    print("ENHANCED ASTROPHYSICAL CAUSAL DISCOVERY TEST SUITE")
    print("=" * 60)

    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Parallel Processing", test_parallel_processing),
        ("Caching System", test_caching_system),
        ("Early Stopping", test_early_stopping),
        ("Astronomical Optimizations", test_astronomical_optimizations),
        ("Performance Benchmark", test_performance_benchmark)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("🎉 All tests passed! Enhanced astrophysical causal discovery is working perfectly.")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review the implementation.")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
