#!/usr/bin/env python3
"""
Sensitivity Analysis: Orion B NN in Clustered vs. Isolated Environments

This script analyzes whether Orion B filaments in high-density (clustered) environments
show systematically different NN spacings compared to isolated filaments, testing whether
the Ophiuchus-style contamination affects Orion B results.

Author: ASTRA Agent System
Date: 2026-05-03
"""

import numpy as np
import json
from pathlib import Path

def load_per_filament_data():
    """Load per-filament validation results."""
    results = {}
    for region in ['OrionB', 'Ophiuchus', 'Perseus']:
        try:
            with open(f'per_filament_pm_validation_{region}.json') as f:
                results[region] = json.load(f)
        except FileNotFoundError:
            print(f"Warning: {region} data not found")
    return results

def analyze_core_density_distribution(filaments):
    """
    Analyze the distribution of core counts per filament to identify
    high-density filaments that may be in clustered environments.

    High-density filaments are defined as those with core counts > 75th percentile.
    """
    core_counts = [f['n_cores'] for f in filaments]
    p75 = np.percentile(core_counts, 75)

    high_density_filaments = [f for f in filaments if f['n_cores'] >= p75]
    low_density_filaments = [f for f in filaments if f['n_cores'] < p75]

    return high_density_filaments, low_density_filaments, p75

def compute_nn_statistics(filaments):
    """Compute NN statistics for a set of filaments."""
    if len(filaments) == 0:
        return None

    nn_values = [f['nn_median_pc'] for f in filaments if f['nn_median_pc'] > 0]
    if len(nn_values) == 0:
        return None

    return {
        'n_filaments': len(filaments),
        'n_cores': sum(f['n_cores'] for f in filaments),
        'nn_mean_pc': np.mean(nn_values),
        'nn_std_pc': np.std(nn_values),
        'nn_median_pc': np.median(nn_values),
        'nn_sem': np.std(nn_values) / np.sqrt(len(nn_values)),
        'nn_values': nn_values
    }

def perform_sensitivity_analysis(orionb_data):
    """
    Perform sensitivity analysis for Orion B by testing different
    high-density filament exclusion thresholds.
    """

    filaments = orionb_data['individual_filaments']

    print("="*70)
    print("ORION B SENSITIVITY ANALYSIS: Clustered vs. Isolated Filaments")
    print("="*70)

    # Overall statistics
    all_stats = compute_nn_statistics(filaments)
    print(f"\nAll Orion B filaments (N={all_stats['n_filaments']}):")
    print(f"  NN = {all_stats['nn_mean_pc']:.4f} ± {all_stats['nn_sem']:.4f} pc (mean ± SEM)")
    print(f"  NN = {all_stats['nn_median_pc']:.4f} pc (median)")
    print(f"  Total cores: {all_stats['n_cores']}")

    # Analyze by core count density
    core_counts = [f['n_cores'] for f in filaments]
    print(f"\nCore count distribution:")
    print(f"  Min: {min(core_counts)}, Max: {max(core_counts)}")
    print(f"  25th: {np.percentile(core_counts, 25):.0f}")
    print(f"  50th (median): {np.percentile(core_counts, 50):.0f}")
    print(f"  75th: {np.percentile(core_counts, 75):.0f}")

    # Define high-density threshold at 75th percentile
    p75 = np.percentile(core_counts, 75)
    high_density = [f for f in filaments if f['n_cores'] >= p75]
    low_density = [f for f in filaments if f['n_cores'] < p75]

    print(f"\n--- High-density filaments (core count ≥ {p75:.0f}, 75th percentile) ---")
    high_stats = compute_nn_statistics(high_density)
    print(f"N = {len(high_density)} filaments, {sum(f['n_cores'] for f in high_density)} cores")
    if high_stats:
        print(f"  NN = {high_stats['nn_mean_pc']:.4f} ± {high_stats['nn_sem']:.4f} pc")
        print(f"  NN = {high_stats['nn_median_pc']:.4f} pc (median)")

    print(f"\n--- Low-density filaments (core count < {p75:.0f}) ---")
    low_stats = compute_nn_statistics(low_density)
    print(f"N = {len(low_density)} filaments, {sum(f['n_cores'] for f in low_density)} cores")
    if low_stats:
        print(f"  NN = {low_stats['nn_mean_pc']:.4f} ± {low_stats['nn_sem']:.4f} pc")
        print(f"  NN = {low_stats['nn_median_pc']:.4f} pc (median)")

    # Test different exclusion thresholds
    print(f"\n{'='*70}")
    print("SENSITIVITY TEST: Excluding High-Density Filaments")
    print(f"{'='*70}")

    thresholds = [50, 60, 70, 75, 80, 90]
    for percentile in thresholds:
        threshold = np.percentile(core_counts, percentile)
        excluded = [f for f in filaments if f['n_cores'] >= threshold]
        included = [f for f in filaments if f['n_cores'] < threshold]

        included_stats = compute_nn_statistics(included)
        if included_stats:
            nn_lambda_over_W = included_stats['nn_mean_pc'] / 0.10  # Assuming W = 0.10 pc

            print(f"\nExcluding top {100-percentile}% highest-density filaments:")
            print(f"  Threshold: ≥ {threshold:.0f} cores")
            print(f"  Excluded: {len(excluded)} filaments ({len(excluded)/len(filaments)*100:.1f}%)")
            print(f"  Included: {len(included)} filaments ({len(included)/len(filaments)*100:.1f}%)")
            print(f"  Remaining NN: {included_stats['nn_mean_pc']:.4f} ± {included_stats['nn_sem']:.4f} pc")
            print(f"  NN/W: {nn_lambda_over_W:.2f} ± {included_stats['nn_sem']/0.10:.2f}")

    # Compare with Ophiuchus
    print(f"\n{'='*70}")
    print("COMPARISON WITH OPHIUCHUS")
    print(f"{'='*70}")

    if 'Ophiuchus' in results:
        oph_filaments = results['Ophiuchus']['individual_filaments']
        oph_stats = compute_nn_statistics(oph_filaments)
        if oph_stats:
            print(f"\nOphiuchus (all filaments, N={oph_stats['n_filaments']}):")
            print(f"  NN = {oph_stats['nn_mean_pc']:.4f} ± {oph_stats['nn_sem']:.4f} pc")
            print(f"  NN/W = {oph_stats['nn_mean_pc']/0.10:.2f} ± {oph_stats['nn_sem']/0.10:.2f}")

    print(f"\nOrion B (all filaments, N={all_stats['n_filaments']}):")
    print(f"  NN = {all_stats['nn_mean_pc']:.4f} ± {all_stats['nn_sem']:.4f} pc")
    print(f"  NN/W = {all_stats['nn_mean_pc']/0.10:.2f} ± {all_stats['nn_sem']/0.10:.2f}")

    # Statistical test: do high-density filaments have significantly different NN?
    print(f"\n{'='*70}")
    print("STATISTICAL TEST: High-density vs. Low-density Filaments")
    print(f"{'='*70}")

    from scipy import stats

    high_nn = [f['nn_median_pc'] for f in high_density if f['nn_median_pc'] > 0]
    low_nn = [f['nn_median_pc'] for f in low_density if f['nn_median_pc'] > 0]

    # Mann-Whitney U test (non-parametric)
    u_stat, p_value = stats.mannwhitneyu(high_nn, low_nn, alternative='two-sided')

    print(f"\nMann-Whitney U test:")
    print(f"  High-density NN: {np.mean(high_nn):.4f} ± {np.std(high_nn):.4f} pc (N={len(high_nn)})")
    print(f"  Low-density NN: {np.mean(low_nn):.4f} ± {np.std(low_nn):.4f} pc (N={len(low_nn)})")
    print(f"  U-statistic: {u_stat:.1f}")
    print(f"  p-value: {p_value:.4f}")

    if p_value < 0.05:
        print(f"  ✗ Significant difference detected (p < 0.05)")
        print(f"    → High-density filaments have different NN than low-density")
    else:
        print(f"  ✓ No significant difference (p >= 0.05)")
        print(f"    → High-density filaments consistent with low-density")

    # Individual filament breakdown
    print(f"\n{'='*70}")
    print("INDIVIDUAL FILAMENT BREAKDOWN (Orion B)")
    print(f"{'='*70}")

    filaments_sorted = sorted(filaments, key=lambda f: f['n_cores'], reverse=True)
    print(f"\n{'Fil ID':<8} {'Cores':<8} {'NN (pc)':<12} {'L/3 (pc)':<12} {'PM/NN':<8}")
    print("-" * 60)
    for f in filaments_sorted:
        pm_nn_ratio = f.get('pm_nn_ratio', 0)
        print(f"{f['filament_id']:<8} {f['n_cores']:<8} {f['nn_median_pc']:<12.4f} "
              f"{f['L_over_3_pc']:<12.4f} {pm_nn_ratio:<8.2f}")

    return {
        'all_stats': all_stats,
        'high_density_stats': high_stats,
        'low_density_stats': low_stats,
        'u_stat': u_stat,
        'p_value': p_value
    }

def main():
    """Run the sensitivity analysis."""

    # Load data
    global results
    results = load_per_filament_data()

    if 'OrionB' not in results:
        print("Error: Orion B data not found!")
        return

    print("\nLoading Orion B per-filament validation data...")
    orionb_data = results['OrionB']
    print(f"Loaded {len(orionb_data['individual_filaments'])} filaments")

    # Perform analysis
    analysis_results = perform_sensitivity_analysis(orionb_data)

    # Save results
    output_file = 'orionb_sensitivity_analysis.json'
    with open(output_file, 'w') as f:
        json.dump({
            'analysis_date': '2026-05-03',
            'orionb_data': {
                'n_filaments_total': len(orionb_data['individual_filaments']),
                'all_stats': analysis_results['all_stats'],
                'high_density_stats': analysis_results['high_density_stats'],
                'low_density_stats': analysis_results['low_density_stats'],
                'statistical_test': {
                    'u_statistic': analysis_results['u_stat'],
                    'p_value': analysis_results['p_value']
                }
            }
        }, f, indent=2)

    print(f"\n{'='*70}")
    print(f"Results saved to {output_file}")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
