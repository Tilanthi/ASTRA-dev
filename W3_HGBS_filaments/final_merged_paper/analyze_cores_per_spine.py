#!/usr/bin/env python3
"""
Analyze the cores-per-spine distribution for Orion B NN analysis.

This script addresses OBS-1: The NN analysis covers only 10.2% of Orion B cores
with critically low cores-per-spine (~1.33 average).

Key task: Deduce the cores-per-spine distribution from summary statistics
and determine what happens when we apply a minimum spine membership criterion.
"""

import numpy as np
import json
from pathlib import Path

def analyze_spine_distribution():
    """
    Analyze the cores-per-spine distribution from summary statistics.

    From the JSON:
    - n_filament_groups: 141
    - n_cores_used: 188
    - n_spacings: 47

    Each spine with n cores contributes (n-1) spacings.
    We need to deduce the distribution of cores per spine.
    """

    print("="*80)
    print("ORION B NN ANALYSIS: CORES-PER-SPINE DISTRIBUTION")
    print("="*80)

    # Load the NN results
    results_file = Path('/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/nearest_neighbor_along_filaments_results.json')

    with open(results_file, 'r') as f:
        data = json.load(f)

    n_spines = data['statistics']['n_filament_groups']
    n_cores = data['statistics']['n_cores_used']
    n_spacings = data['statistics']['n_spacings']

    print(f"\nSummary Statistics:")
    print(f"  Total spines: {n_spines}")
    print(f"  Total cores: {n_cores}")
    print(f"  Total spacings: {n_spacings}")
    print(f"  Average cores per spine: {n_cores/n_spines:.2f}")
    print(f"  Average spacings per spine: {n_spacings/n_spines:.2f}")

    # Deduce the distribution
    # Let x = spines with 1 core, y = spines with 2 cores, z = spines with >=3 cores
    # We have:
    #   x + y + z = 141 (total spines)
    #   x + 2y + 3z_min = 188 (total cores, minimum for z spines)
    #   0*x + 1*y + 2*z = 47 (total spacings, assuming all z have exactly 3 cores)

    # From spacing equation: y + 2z = 47
    # From spine equation: x = 141 - y - z
    # From core equation: x + 2y + 3z = 188
    # Substitute x: (141 - y - z) + 2y + 3z = 188
    # 141 + y + 2z = 188
    # y + 2z = 47 (same as spacing equation, consistent)

    # So we have one equation with two unknowns (y and z)
    # Let's try different scenarios

    print(f"\n" + "="*80)
    print("DEDUCING CORES-PER-SPINE DISTRIBUTION")
    print("="*80)

    scenarios = []
    for z in range(0, 24):  # z can be at most 23 (if z=23, 2z=46, y=1)
        y = 47 - 2*z
        if y >= 0:
            x = 141 - y - z
            if x >= 0:
                # Check if core count matches
                total_cores = x + 2*y + 3*z
                if total_cores == 188:
                    scenarios.append({'x': x, 'y': y, 'z': z})

    print(f"\nPossible distributions (all consistent with summary statistics):")
    print(f"{'Scenario':<12} {'1-core':<10} {'2-core':<10} {'3+-core':<10} {'Total':<10}")
    print("-"*60)

    for i, s in enumerate(scenarios):
        print(f"{i+1:<12} {s['x']:<10} {s['y']:<10} {s['z']:<10} {141:<10}")

    # The actual distribution is likely somewhere in the middle
    # Let's pick a representative scenario: mostly 1-core spines, some 2-core, fewer 3+-core
    # Scenario with z=10 seems reasonable: 63 single-core, 27 two-core, 10 multi-core
    representative = scenarios[10] if len(scenarios) > 10 else scenarios[0]

    print(f"\n" + "="*80)
    print("REPRESENTATIVE DISTRIBUTION (Scenario ~10):")
    print("="*80)
    print(f"  Spines with 1 core (no spacing): {representative['x']} ({representative['x']/141*100:.1f}%)")
    print(f"  Spines with 2 cores (1 spacing): {representative['y']} ({representative['y']/141*100:.1f}%)")
    print(f"  Spines with 3+ cores (2+ spacings): {representative['z']} ({representative['z']/141*100:.1f}%)")

    # Now analyze what happens with minimum 3 cores per spine
    print(f"\n" + "="*80)
    print("APPLYING MINIMUM 3 CORES PER SPINE CRITERION")
    print("="*80)

    # With minimum 3 cores, we only keep the 'z' spines
    # Minimum cores in these spines: 3 * z
    # Minimum spacings from these spines: 2 * z

    min_cores_reliable = 3 * representative['z']
    min_spacings_reliable = 2 * representative['z']

    print(f"\nIf we require minimum 3 cores per spine:")
    print(f"  Reliable spines: {representative['z']} (vs {141} total)")
    print(f"  Reliable cores: {min_cores_reliable} (vs {n_cores} total, {min_cores_reliable/n_cores*100:.1f}%)")
    print(f"  Reliable spacings: {min_spacings_reliable} (vs {n_spacings} total)")

    # But wait - we need to actually look at the individual spacing data
    # to get the real distribution. Let me check the spacing data directly.

    all_spacings = np.array(data['all_spacings_pc'])
    print(f"\n" + "="*80)
    print("ANALYSIS OF ACTUAL SPACING DATA")
    print("="*80)

    print(f"\nAll {len(all_spacings)} spacings:")
    print(f"  Mean: {np.mean(all_spacings):.4f} pc")
    print(f"  Median: {np.median(all_spacings):.4f} pc")
    print(f"  Std: {np.std(all_spacings):.4f} pc")
    print(f"  Min: {np.min(all_spacings):.4f} pc")
    print(f"  Max: {np.max(all_spacings):.4f} pc")

    # The issue is that with only 47 spacings from 188 cores on 141 spines,
    # many spines contribute only 1 core (0 spacings) or 2 cores (1 spacing).
    # The reviewer is correct that we need to apply a minimum criterion.

    # However, we CANNOT determine the exact cores-per-spine distribution
    # from the summary statistics alone. We would need the full core-spine
    # association data, which is not in the JSON.

    # What we CAN do is:
    # 1. Acknowledge the limitation honestly
    # 2. Note that only 47 spacings from 141 spines suggests most spines have < 3 cores
    # 3. State that a proper analysis requires the full core-spine association data

    print(f"\n" + "="*80)
    print("CRITICAL LIMITATION")
    print("="*80)
    print(f"\nThe JSON contains only summary statistics, not the full")
    print(f"core-spine association data needed to determine the exact")
    print(f"distribution of cores per spine.")
    print(f"\nWhat we know:")
    print(f"  - 141 spines, 188 cores, 47 spacings")
    print(f"  - Average: {188/141:.2f} cores per spine")
    print(f"  - Average: {47/141:.2f} spacings per spine")
    print(f"\nThe low spacing count (47 vs 141 spines) confirms that")
    print(f"many spines have only 1-2 cores, making them unreliable for")
    print(f"NN analysis.")
    print(f"\nRecommendation:")
    print(f"  A full NN analysis with minimum 3 cores per spine criterion")
    print(f"  requires access to the original core-spine association data,")
    print(f"  which is not available in the current JSON file.")

    return {
        'n_spines': n_spines,
        'n_cores': n_cores,
        'n_spacings': n_spacings,
        'avg_cores_per_spine': n_cores / n_spines,
        'avg_spacings_per_spine': n_spacings / n_spines,
    }


if __name__ == '__main__':
    results = analyze_spine_distribution()

    print(f"\n" + "="*80)
    print("SUMMARY FOR PAPER UPDATE")
    print("="*80)
    print(f"\nKey findings to include in paper:")
    print(f"1. Only {results['n_spacings']} NN spacings from {results['n_spines']} spines")
    print(f"2. Average cores per spine: {results['avg_cores_per_spine']:.2f}")
    print(f"3. Average spacings per spine: {results['avg_spacings_per_spine']:.2f}")
    print(f"4. Many spines likely have only 1-2 cores, making NN unreliable")
    print(f"5. A proper analysis requires minimum 3 cores per spine criterion")
    print(f"6. This limitation should be acknowledged explicitly in the paper")
