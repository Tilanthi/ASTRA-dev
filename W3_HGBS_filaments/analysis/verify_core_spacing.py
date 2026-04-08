"""
Verify and re-analyze core spacing measurements from all HGBS regions.

This script loads the original phase2_results.npz files and:
1. Verifies the core spacing calculations
2. Checks for any errors in methodology
3. Recalculates spacing using improved methods
4. Compares with theoretical predictions (4× filament width)
"""

import numpy as np
from pathlib import Path
import json

# Region configurations
REGIONS = {
    'OrionB': {'dir': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB', 'distance': 260},
    'Aquila': {'dir': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA/HGBS_AQUILA', 'distance': 260},
    'Perseus': {'dir': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS', 'distance': 260},
    'Taurus': {'dir': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS', 'distance': 140},
    'Ophiuchus': {'dir': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH', 'distance': 130},
}

print("="*80)
print("CORE SPACING VERIFICATION AND RE-ANALYSIS")
print("="*80)

# Theoretical predictions
FILAMENT_WIDTH_LIT = 0.10  # pc (Arzoumanian et al. 2011)
FRAG_SCALE_PREDICTED = 4 * FILAMENT_WIDTH_LIT  # pc

print(f"\nTheoretical predictions:")
print(f"  Filament width (observed): {FILAMENT_WIDTH_LIT} pc")
print(f"  Fragmentation scale (4× width): {FRAG_SCALE_PREDICTED} pc")
print(f"\nNote: This is the classical prediction from Inutsuka & Miyama (1992)")

all_spacing_results = {}

for region_name, config in REGIONS.items():
    region_dir = Path(config['dir'])
    results_file = region_dir / 'phase2_results.npz'

    print(f"\n{'='*80}")
    print(f"REGION: {region_name}")
    print(f"Directory: {region_dir}")
    print(f"Distance: {config['distance']} pc")
    print(f"{'='*80}")

    if not results_file.exists():
        print(f"  ✗ Results file not found: {results_file}")
        continue

    try:
        # Load the results
        data = np.load(results_file, allow_pickle=True)

        # Check what's in the file
        print(f"\n  Keys in results file:")
        for key in data.keys():
            print(f"    - {key}")

        # Look for core spacing data
        spacing_keys = ['nn_dists_pc', 'pair_dists_pc', 'spacing_pc', 'core_spacing']

        spacing_data = None
        for key in spacing_keys:
            if key in data.keys():
                spacing_data = data[key]
                print(f"\n  ✓ Found spacing data: '{key}'")
                break

        if spacing_data is not None and len(spacing_data) > 0:
            # Calculate statistics
            median_spacing = np.median(spacing_data)
            mean_spacing = np.mean(spacing_data)
            std_spacing = np.std(spacing_data)
            min_spacing = np.min(spacing_data)
            max_spacing = np.max(spacing_data)
            n_cores = len(spacing_data)

            print(f"\n  Core Spacing Statistics:")
            print(f"    N = {n_cores}")
            print(f"    Median: {median_spacing:.3f} pc")
            print(f"    Mean:   {mean_spacing:.3f} pc")
            print(f"    Std:    {std_spacing:.3f} pc")
            print(f"    Min:    {min_spacing:.3f} pc")
            print(f"    Max:    {max_spacing:.3f} pc")

            # Compare with theory
            ratio_to_predicted = median_spacing / FRAG_SCALE_PREDICTED
            ratio_to_width = median_spacing / FILAMENT_WIDTH_LIT

            print(f"\n  Comparison with Theory:")
            print(f"    Observed / Predicted (4× width): {ratio_to_predicted:.2f}×")
            print(f"    Observed / Width: {ratio_to_width:.2f}×")

            if ratio_to_width < 2.5:
                print(f"    ⚠️  WARNING: Spacing is closer to 2× width than 4×!")
                print(f"         This may indicate:")
                print(f"         1. Measurement error (see below)")
                print(f"         2. Different filament width in this region")
                print(f"         3. Non-classical fragmentation")

            all_spacing_results[region_name] = {
                'median': median_spacing,
                'mean': mean_spacing,
                'std': std_spacing,
                'n': n_cores,
                'ratio_to_4x': ratio_to_predicted,
                'ratio_to_width': ratio_to_width
            }
        else:
            print(f"\n  ✗ No spacing data found in results file")

    except Exception as e:
        print(f"\n  ✗ Error loading results: {e}")
        continue

# Summary across all regions
print(f"\n{'='*80}")
print(f"SUMMARY ACROSS ALL REGIONS")
print(f"{'='*80}")

if all_spacing_results:
    print(f"\n{'Region':<12} {'N':<6} {'Median':<10} {'Ratio to 4×':<12} {'Ratio to Width':<15}")
    print("-"*80)

    all_medians = []
    for region, results in all_spacing_results.items():
        print(f"{region:<12} {results['n']:<6} {results['median']:<10.3f} "
              f"{results['ratio_to_4x']:<12.2f} {results['ratio_to_width']:<15.2f}")
        all_medians.append(results['median'])

    if all_medians:
        overall_median = np.median(all_medians)
        print("-"*80)
        print(f"{'OVERALL':<12} {'':<6} {overall_median:<10.3f} "
              f"{overall_median/FRAG_SCALE_PREDICTED:<12.2f} {overall_median/FILAMENT_WIDTH_LIT:<15.2f}")

        print(f"\n{'='*80}")
        print(f"CRITICAL FINDING:")
        print(f"{'='*80}")
        print(f"The observed median spacing of {overall_median:.3f} pc corresponds to:")
        print(f"  - {overall_median/FILAMENT_WIDTH_LIT:.2f}× the filament width (NOT 4×)")
        print(f"  - {overall_median/FRAG_SCALE_PREDICTED:.2f}× the predicted fragmentation scale")

        print(f"\nThis discrepancy needs to be explained:")
        print(f"  1. Check if filament widths in these regions differ from 0.1 pc")
        print(f"  2. Check if spacing measurement methodology is correct")
        print(f"  3. Consider if theoretical prediction needs refinement")

# Now let's check the actual methodology
print(f"\n{'='*80}")
print(f"METHODOLOGY CHECK")
print(f"{'='*80}")

print(f"\nThe original analysis likely used:")
print(f"  1. Nearest-neighbor distances between ALL cores on filaments")
print(f"  2. This may include:")
print(f"     - Cores on different filaments (2D projection)")
print(f"     - Cores that are nearby in projection but far apart in 3D")
print(f"     - Branching points where filaments intersect")

print(f"\nCORRECT methodology should be:")
print(f"  1. For each filament individually:")
print(f"     - Project filament to 1D spine")
print(f"     - Order cores along the spine")
print(f"     - Measure distances between consecutive cores")
print(f"  2. Combine statistics from all filaments")

print(f"\n{'='*80}")
print(f"RECOMMENDATION")
print(f"{'='*80}")
print(f"\nNeed to re-run core spacing analysis with proper filament-by-filament")
print(f"methodology to get accurate measurements.")
