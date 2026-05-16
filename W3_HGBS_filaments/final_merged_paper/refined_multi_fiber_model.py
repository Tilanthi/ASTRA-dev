#!/usr/bin/env python3
"""
Refined Multi-Fiber Model: Find Configuration That Matches HGBS NN/PM ≈ 0.31-0.73
"""

import numpy as np
import json
from synthetic_filament_tests import SyntheticFilamentGenerator, MultiFilamentConfig


def test_sparsed_fibers():
    """Test with fibers that are more separated (less interwoven)"""
    print("=" * 70)
    print("TESTING SPARSED FIBER CONFIGURATIONS")
    print("=" * 70)

    gen = SyntheticFilamentGenerator(seed=42)

    results = []

    # Test with fewer fibers and different phase spreads
    for n_fibers in [2, 3, 4]:
        for phase_spread in [0.1, 0.3, 0.5, 1.0]:
            for spacing_spread in [0.0, 0.05, 0.1]:
                gen = SyntheticFilamentGenerator(seed=42 + n_fibers*10 + int(phase_spread*100))

                config = MultiFilamentConfig(
                    n_fibers=n_fibers,
                    filament_length=10.0,
                    fragmentation_wavelength=0.28,  # HGBS-like
                    phase_spread=phase_spread,
                    spacing_spread=spacing_spread,
                    n_cores_per_fiber=30,
                    label=f"{n_fibers}fibers_phase{phase_spread}_spread{spacing_spread}"
                )

                positions = gen.generate_multi_fiber_bundle(config)
                pm = gen.compute_pairwise_median(positions)
                nn = gen.compute_nearest_neighbor(positions)
                n_cores = len(positions)

                nn_pm_ratio = nn / pm if pm > 0 else np.nan

                results.append({
                    'n_fibers': n_fibers,
                    'phase_spread': phase_spread,
                    'spacing_spread': spacing_spread,
                    'n_cores': n_cores,
                    'pm': pm,
                    'nn': nn,
                    'nn_pm_ratio': nn_pm_ratio,
                    'matches_hgbs': 0.31 <= nn_pm_ratio <= 0.73
                })

    # Print results that match HGBS range
    print(f"\n{'Config':<50} {'N_cores':<8} {'PM':<8} {'NN':<8} {'NN/PM':<8} {'Match?':<8}")
    print("-" * 90)

    matches = []
    for r in results:
        match_mark = "✓" if r['matches_hgbs'] else ""
        label = f"{r['n_fibers']}f_phase{r['phase_spread']:.1f}_spr{r['spacing_spread']:.2f}"
        print(f"{label:<50} {r['n_cores']:<8} {r['pm']:<8.3f} {r['nn']:<8.3f} {r['nn_pm_ratio']:<8.3f} {match_mark:<8}")
        if r['matches_hgbs']:
            matches.append(r)

    print(f"\nFound {len(matches)} configurations matching HGBS NN/PM range")

    if matches:
        print("\nMatching configurations:")
        for m in matches:
            print(f"  {m['label']}: NN/PM = {m['nn_pm_ratio']:.3f}")
            print(f"    Phase spread: {m['phase_spread']:.2f}, Spacing spread: {m['spacing_spread']:.2f}")

    return results, matches


def test_asymmetric_fibers():
    """Test with asymmetric fiber distributions (fibers concentrated in different regions)"""
    print("\n" + "=" * 70)
    print("TESTING ASYMMETRIC FIBER DISTRIBUTIONS")
    print("=" * 70)

    gen = SyntheticFilamentGenerator(seed=42)

    results = []

    # Test with 2-3 fibers concentrated in different regions
    for n_fibers in [2, 3]:
        for separation in [0.2, 0.4, 0.6, 0.8]:  # Separation between fiber groups
            gen = SyntheticFilamentGenerator(seed=42 + n_fibers*100 + int(separation*1000))

            # Generate fibers in groups
            all_positions = []

            for fiber_idx in range(n_fibers):
                # Offset each fiber group
                group_offset = fiber_idx * separation

                # Generate positions for this fiber group
                wavelength = 0.28  # HGBS-like
                positions = []
                pos = group_offset
                while pos < group_offset + 5.0:  # Each fiber group is 5 pc long
                    positions.append(pos)
                    pos += wavelength

                all_positions.extend(positions)

            # Combine and sort
            all_positions = np.array(all_positions)
            all_positions = np.sort(all_positions)

            # Compute statistics
            pm = gen.compute_pairwise_median(all_positions)
            nn = gen.compute_nearest_neighbor(all_positions)
            n_cores = len(all_positions)

            nn_pm_ratio = nn / pm if pm > 0 else np.nan

            results.append({
                'n_fibers': n_fibers,
                'separation': separation,
                'n_cores': n_cores,
                'pm': pm,
                'nn': nn,
                'nn_pm_ratio': nn_pm_ratio,
                'matches_hgbs': 0.31 <= nn_pm_ratio <= 0.73
            })

    # Print results
    print(f"\n{'Config':<50} {'N_cores':<8} {'PM':<8} {'NN':<8} {'NN/PM':<8} {'Match?':<8}")
    print("-" * 90)

    matches = []
    for r in results:
        match_mark = "✓" if r['matches_hgbs'] else ""
        label = f"{r['n_fibers']}fibers_sep{r['separation']:.1f}"
        print(f"{label:<50} {r['n_cores']:<8} {r['pm']:<8.3f} {r['nn']:<8.3f} {r['nn_pm_ratio']:<8.3f} {match_mark:<8}")
        if r['matches_hgbs']:
            matches.append(r)

    print(f"\nFound {len(matches)} asymmetric configurations matching HGBS NN/PM range")

    return results, matches


def test_mixed_single_multi():
    """Test combination of single dominant filament + minor fibers"""
    print("\n" + "=" * 70)
    print("TESTING MIXED CONFIGURATION: Dominant Fiber + Minor Fibers")
    print("=" * 70)

    gen = SyntheticFilamentGenerator(seed=42)

    results = []

    # Test with 1 dominant filament + N minor fibers
    for n_minor_fibers in [1, 2, 3, 4]:
        for minor_fiber_strength in [0.2, 0.3, 0.4, 0.5]:  # Fraction of cores in minor fibers
            gen = SyntheticFilamentGenerator(seed=42 + n_minor_fibers*10 + int(minor_fiber_strength*100))

            # Dominant filament: 70% of cores
            n_dominant = int(70 / (n_minor_fibers + 1) * minor_fiber_strength / 0.3)
            wavelength = 0.28  # HGBS-like

            dominant_positions = []
            pos = 0.0
            while pos < 8.0:
                dominant_positions.append(pos)
                pos += wavelength

            # Minor fibers: 30% of cores, randomly positioned
            all_positions = list(dominant_positions)

            for _ in range(n_minor_fibers):
                n_minor = int(n_dominant * (1 - minor_fiber_strength) / n_minor_fibers)
                minor_start = gen.rng.uniform(0, 8.0 - n_minor * wavelength)
                minor_positions = []
                pos = minor_start
                while len(minor_positions) < n_minor and pos < 10.0:
                    minor_positions.append(pos)
                    pos += wavelength + gen.rng.uniform(-0.02, 0.02)  # Add small jitter

                all_positions.extend(minor_positions)

            # Sort and compute statistics
            all_positions = np.array(all_positions)
            all_positions = np.sort(all_positions)

            pm = gen.compute_pairwise_median(all_positions)
            nn = gen.compute_nearest_neighbor(all_positions)
            n_cores = len(all_positions)

            nn_pm_ratio = nn / pm if pm > 0 else np.nan

            results.append({
                'n_minor_fibers': n_minor_fibers,
                'minor_strength': minor_fiber_strength,
                'n_cores': n_cores,
                'pm': pm,
                'nn': nn,
                'nn_pm_ratio': nn_pm_ratio,
                'matches_hgbs': 0.31 <= nn_pm_ratio <= 0.73
            })

    # Print results
    print(f"\n{'Config':<50} {'N_cores':<8} {'PM':<8} {'NN':<8} {'NN/PM':<8} {'Match?':<8}")
    print("-" * 90)

    matches = []
    for r in results:
        match_mark = "✓" if r['matches_hgbs'] else ""
        label = f"{r['n_minor_fibers']}minor_str{r['minor_strength']:.2f}"
        print(f"{label:<50} {r['n_cores']:<8} {r['pm']:<8.3f} {r['nn']:<8.3f} {r['nn_pm_ratio']:<8.3f} {match_mark:<8}")
        if r['matches_hgbs']:
            matches.append(r)

    print(f"\nFound {len(matches)} mixed configurations matching HGBS NN/PM range")

    return results, matches


def main():
    """Run all refined multi-fiber tests"""

    # Test 1: Sparsed fibers
    sparse_results, sparse_matches = test_sparsed_fibers()

    # Test 2: Asymmetric fibers
    asymmetric_results, asymmetric_matches = test_asymmetric_fibers()

    # Test 3: Mixed single-multi
    mixed_results, mixed_matches = test_mixed_single_multi()

    # Combine all results
    all_matches = sparse_matches + asymmetric_matches + mixed_matches

    print("\n" + "=" * 70)
    print("SUMMARY OF ALL TESTS")
    print("=" * 70)
    print(f"Total matching configurations found: {len(all_matches)}")

    if all_matches:
        print("\nAll configurations that reproduce HGBS NN/PM range (0.31-0.73):")
        for m in all_matches:
            # Create readable label for each match
            if 'n_fibers' in m and 'phase_spread' in m:
                label = f"Sparsed: {m['n_fibers']} fibers, phase={m['phase_spread']:.1f}"
            elif 'n_fibers' in m and 'separation' in m:
                label = f"Asymmetric: {m['n_fibers']} fibers, separation={m['separation']:.1f}"
            elif 'n_minor_fibers' in m:
                label = f"Mixed: {m['n_minor_fibers']} minor fibers, strength={m['minor_strength']:.2f}"
            else:
                label = str(m)
            print(f"  {label}: NN/PM = {m['nn_pm_ratio']:.3f}")

    # Save results
    all_results = {
        'sparsed_fibers': sparse_results,
        'asymmetric_fibers': asymmetric_results,
        'mixed_configurations': mixed_results,
        'all_matches': all_matches
    }

    output_file = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/refined_multi_fiber_results.json'

    def convert_types(obj):
        if isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(item) for item in obj]
        elif isinstance(obj, (bool, np.bool_)):
            return bool(obj)
        elif isinstance(obj, (str,)) or obj is None:
            return obj
        else:
            return str(obj)

    with open(output_file, 'w') as f:
        json.dump(convert_types(all_results), f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == '__main__':
    main()
