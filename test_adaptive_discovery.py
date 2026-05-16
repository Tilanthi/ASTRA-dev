#!/usr/bin/env python3
"""
Test the Adaptive Discovery Pipeline

Demonstrates that the fixed architecture:
1. Doesn't repeat discoveries
2. Detects novelty properly
3. Explores systematically
4. Stops when appropriate
"""

import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from astra_core.discovery.adaptive_discovery import (
    AdaptiveDiscoveryPipeline,
    DiscoveryRegistry,
    NoveltyDetector,
    ExplorationPlanner,
    ConvergenceDetector
)

def create_test_data():
    """Create synthetic astronomical data with strong correlations"""
    np.random.seed(42)

    n = 1000

    # Create base variables
    g_mag = np.random.normal(15, 2, n)
    bp_mag = np.random.normal(16, 2, n)
    rp_mag = np.random.normal(15, 2, n)

    data = {
        'g_mag': g_mag,
        'absolute_g': 0.9 * g_mag + np.random.normal(0, 0.5, n),  # Very strong correlation
        'parallax': np.random.normal(10, 3, n),
        'bp_mag': bp_mag,
        'rp_mag': rp_mag,
        'bp_rp': 0.8 * (bp_mag - rp_mag) + np.random.normal(0, 0.2, n),  # Strong correlation
        'u_g': np.random.normal(1, 0.3, n),
        'g_r': np.random.normal(0.8, 0.4, n),
        'r_i': np.random.normal(0.5, 0.3, n),
        'distance': np.random.normal(100, 20, n)
    }

    return data

def test_adaptive_discovery():
    """Test the adaptive discovery pipeline"""

    print("=" * 70)
    print("ADAPTIVE DISCOVERY PIPELINE TEST")
    print("=" * 70)
    print()

    # Create test data with limited variables to ensure discoveries are found
    np.random.seed(42)
    n = 1000
    g_mag = np.random.normal(15, 2, n)
    bp_mag = np.random.normal(16, 2, n)
    rp_mag = np.random.normal(15, 2, n)

    data = {
        'g_mag': g_mag,
        'absolute_g': 0.9 * g_mag + np.random.normal(0, 0.5, n),  # Strong correlation
        'parallax': np.random.normal(10, 3, n),
        'bp_mag': bp_mag,
        'rp_mag': rp_mag,
        'bp_rp': 0.8 * (bp_mag - rp_mag) + np.random.normal(0, 0.2, n)  # Strong correlation
    }

    variables = list(data.keys())

    print(f"Test data created with {len(variables)} variables")
    print(f"Variables: {', '.join(variables)}")
    print()

    # Verify correlations exist
    from scipy import stats
    print("Verifying correlations in test data:")
    print("-" * 70)
    test_pairs = [('g_mag', 'absolute_g'), ('bp_mag', 'bp_rp')]
    for var1, var2 in test_pairs:
        x, y = data[var1], data[var2]
        corr, p_value = stats.pearsonr(x, y)
        print(f"{var1} ↔ {var2}: r={corr:.3f}, p={p_value:.2e} (significant={p_value < 0.05 and abs(corr) > 0.3})")
    print()

    # Clear any existing registry for clean test
    import os
    test_db_path = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/data/discovery_registry.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("Cleared existing discovery registry for clean test")
        print()

    # Initialize pipeline with the same variables
    pipeline = AdaptiveDiscoveryPipeline(variables)

    print("INITIAL STATE:")
    print("-" * 70)
    stats = pipeline.get_statistics()
    print(f"Total possible combinations: {stats['exploration_progress']['total_combinations']}")
    print(f"Already in registry: {stats['registry']['total_discoveries']}")
    print()

    # Run exploration cycles
    print("RUNNING EXPLORATION CYCLES:")
    print("-" * 70)

    max_cycles = 50
    discoveries_made = []

    for cycle in range(max_cycles):
        result = pipeline.run_cycle(data)

        if result is None:
            print(f"Cycle {cycle + 1}: Exploration stopped")
            break

        if result['novelty'] > 0:
            discoveries_made.append(result)
            print(f"Cycle {cycle + 1}: NOVEL - {result['var1']} {result['type']} {result['var2']} "
                  f"(novelty={result['novelty']:.2f})")
        else:
            print(f"Cycle {cycle + 1}: Skipped (already known)")

        # Check if we should continue
        if not pipeline.should_continue():
            print(f"\nStopping criterion met after {cycle + 1} cycles")
            break

    print()
    print("FINAL STATISTICS:")
    print("-" * 70)
    stats = pipeline.get_statistics()

    print(f"Cycles run: {stats['cycles_run']}")
    print(f"Novel discoveries: {stats['novel_discoveries']}")
    print(f"Redundant discoveries: {stats['redundant_discoveries']}")
    print(f"Efficiency: {stats['efficiency']:.1f}% (novel discoveries per cycle)")
    print()

    print("Exploration Progress:")
    prog = stats['exploration_progress']
    print(f"  Total combinations: {prog['total_combinations']}")
    print(f"  Explored: {prog['explored']}")
    print(f"  Progress: {prog['progress_percent']:.1f}%")
    print()

    print("Registry:")
    reg = stats['registry']
    print(f"  Total discoveries: {reg['total_discoveries']}")
    print(f"  By type: {reg['by_type']}")
    print()

    print("Convergence:")
    conv = stats['convergence']
    print(f"  Status: {conv['status']}")
    if 'recent_novelty' in conv:
        print(f"  Recent novelty: {conv['recent_novelty']:.3f}")
        print(f"  Threshold: {conv['threshold']:.3f}")
    print()

    print("=" * 70)
    print("TEST RESULTS:")
    print("-" * 70)

    # Verify key improvements
    tests_passed = []

    # Test 1: No redundant discoveries stored
    if stats['redundant_discoveries'] == 0:
        print("✓ PASS: No redundant discoveries stored")
        tests_passed.append(True)
    else:
        print("✗ FAIL: Redundant discoveries were stored")
        tests_passed.append(False)

    # Test 2: System stopped appropriately
    if stats['cycles_run'] < max_cycles:
        print("✓ PASS: System stopped before max cycles (intelligent stopping)")
        tests_passed.append(True)
    else:
        print("✗ FAIL: System ran for all cycles without stopping")
        tests_passed.append(False)

    # Test 3: Novelty detection working
    if stats['efficiency'] > 0:
        print("✓ PASS: Novelty detection is working")
        tests_passed.append(True)
    else:
        print("✗ FAIL: No novel discoveries detected")
        tests_passed.append(False)

    # Test 4: Progress tracking
    if prog['progress_percent'] > 0:
        print("✓ PASS: Exploration progress is being tracked")
        tests_passed.append(True)
    else:
        print("✗ FAIL: No exploration progress made")
        tests_passed.append(False)

    print()
    if all(tests_passed):
        print("✓ ALL TESTS PASSED - Adaptive discovery is working correctly")
    else:
        print(f"✗ {sum(not t for t in tests_passed)} TESTS FAILED")

    print("=" * 70)

    return all(tests_passed)


if __name__ == '__main__':
    success = test_adaptive_discovery()
    sys.exit(0 if success else 1)
