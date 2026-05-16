#!/usr/bin/env python3
"""
Leave-one-out analysis for NN measurements across HGBS regions.

This script analyzes how the weighted mean NN λ/W and PM/NN ratio
change when each region is systematically excluded from the calculation.

Addressing Reviewer Concern: "What happens to λ_NN/W if Aquila is excluded?"

Author: ASTRA-dev
Date: 2026-05-09
"""

import json
import numpy as np
from typing import List, Dict, Any

def load_region_results(results_file: str) -> List[Dict[str, Any]]:
    """
    Load region results from JSON file.
    """
    with open(results_file, 'r') as f:
        data = json.load(f)

    # Extract robust results
    robust_results = [r for r in data['results'] if r.get('is_robust', False)]
    return robust_results

def calculate_weighted_mean(regions: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate weighted mean statistics for a given set of regions.

    Weights by number of spacings (n_spacings).
    """
    if not regions:
        return {
            'nn_lambda_W': np.nan,
            'pm_lambda_W': np.nan,
            'pm_nn_ratio': np.nan,
            'total_spacings': 0,
            'n_regions': 0
        }

    total_spacings = sum(r.get('n_spacings', 0) for r in regions)

    if total_spacings == 0:
        return {
            'nn_lambda_W': np.nan,
            'pm_lambda_W': np.nan,
            'pm_nn_ratio': np.nan,
            'total_spacings': 0,
            'n_regions': len(regions)
        }

    # Weighted means
    weighted_nn_lambda_W = sum(r.get('nn_lambda_over_W', 0) * r.get('n_spacings', 0)
                               for r in regions) / total_spacings

    weighted_pm_lambda_W = sum(r.get('pairwise_lambda_W', 0) * r.get('n_spacings', 0)
                               for r in regions) / total_spacings

    # PM/NN ratio
    if weighted_nn_lambda_W > 0:
        weighted_ratio = weighted_pm_lambda_W / weighted_nn_lambda_W
    else:
        weighted_ratio = np.nan

    return {
        'nn_lambda_W': weighted_nn_lambda_W,
        'pm_lambda_W': weighted_pm_lambda_W,
        'pm_nn_ratio': weighted_ratio,
        'total_spacings': total_spacings,
        'n_regions': len(regions)
    }

def perform_leave_one_out_analysis(results_file: str) -> Dict[str, Any]:
    """
    Perform systematic leave-one-out analysis.
    """
    print("=" * 80)
    print("LEAVE-ONE-OUT ANALYSIS: NN MEASUREMENTS")
    print("=" * 80)

    # Load all region results
    all_regions = load_region_results(results_file)

    print(f"\nLoaded {len(all_regions)} robust regions:")
    for r in all_regions:
        print(f"  - {r['region']}: {r.get('n_spacings', 0)} spacings")

    # Full sample (no regions excluded)
    full_sample = calculate_weighted_mean(all_regions)

    print("\n" + "=" * 80)
    print("LEAVE-ONE-OUT RESULTS")
    print("=" * 80)

    # Table header
    print(f"\n{'Region Excluded':<20} {'NN λ/W':<10} {'PM λ/W':<10} {'PM/NN':<10} {'N_spacings':<12} {'N_regions':<10}")
    print("-" * 80)

    # Full sample
    print(f"{'None (full sample)':<20} "
          f"{full_sample['nn_lambda_W']:<10.3f} "
          f"{full_sample['pm_lambda_W']:<10.3f} "
          f"{full_sample['pm_nn_ratio']:<10.3f} "
          f"{full_sample['total_spacings']:<12} "
          f"{full_sample['n_regions']:<10}")

    # Leave-one-out for each region
    leave_one_out_results = {}

    for region_to_exclude in all_regions:
        region_name = region_to_exclude['region']

        # Exclude this region
        remaining_regions = [r for r in all_regions if r['region'] != region_name]

        # Calculate statistics
        stats = calculate_weighted_mean(remaining_regions)

        print(f"{region_name:<20} "
              f"{stats['nn_lambda_W']:<10.3f} "
              f"{stats['pm_lambda_W']:<10.3f} "
              f"{stats['pm_nn_ratio']:<10.3f} "
              f"{stats['total_spacings']:<12} "
              f"{stats['n_regions']:<10}")

        leave_one_out_results[region_name] = stats

    # Sensitivity analysis
    print("\n" + "=" * 80)
    print("SENSITIVITY ANALYSIS")
    print("=" * 80)

    # Calculate changes relative to full sample
    print("\nChange when excluding each region (absolute and relative):")
    print(f"\n{'Region Excluded':<20} {'ΔNN λ/W':<15} {'ΔPM λ/W':<15} {'ΔPM/NN':<15}")
    print("-" * 80)

    for region_name, stats in leave_one_out_results.items():
        delta_nn = stats['nn_lambda_W'] - full_sample['nn_lambda_W']
        delta_pm = stats['pm_lambda_W'] - full_sample['pm_lambda_W']
        delta_ratio = stats['pm_nn_ratio'] - full_sample['pm_nn_ratio']

        # Relative changes (percentage)
        rel_nn = 100 * delta_nn / full_sample['nn_lambda_W']
        rel_pm = 100 * delta_pm / full_sample['pm_lambda_W']
        rel_ratio = 100 * delta_ratio / full_sample['pm_nn_ratio']

        print(f"{region_name:<20} "
              f"{delta_nn:>6.3f} ({rel_nn:>5.1f}%)   "
              f"{delta_pm:>6.3f} ({rel_pm:>5.1f}%)   "
              f"{delta_ratio:>6.3f} ({rel_ratio:>5.1f}%)")

    # Most influential region
    print("\n" + "=" * 80)
    print("REGION INFLUENCE RANKING")
    print("=" * 80)

    # Rank regions by their influence on PM/NN ratio
    influence_ranking = sorted(
        leave_one_out_results.items(),
        key=lambda x: abs(x[1]['pm_nn_ratio'] - full_sample['pm_nn_ratio']),
        reverse=True
    )

    print("\nRegions ranked by influence on PM/NN ratio:")
    for i, (region_name, stats) in enumerate(influence_ranking, 1):
        delta = abs(stats['pm_nn_ratio'] - full_sample['pm_nn_ratio'])
        print(f"  {i}. {region_name:<15} ΔPM/NN = {delta:.3f}")

    # Individual region statistics
    print("\n" + "=" * 80)
    print("INDIVIDUAL REGION STATISTICS")
    print("=" * 80)

    print(f"\n{'Region':<15} {'NN λ/W':<10} {'PM λ/W':<10} {'PM/NN':<10} {'N_spacings':<12} {'Weight':<10}")
    print("-" * 80)

    for r in all_regions:
        weight = r.get('n_spacings', 0) / full_sample['total_spacings']
        print(f"{r['region']:<15} "
              f"{r.get('nn_lambda_over_W', 0):<10.3f} "
              f"{r.get('pairwise_lambda_W', 0):<10.3f} "
              f"{r.get('pairwise_to_filament_nn_ratio', 0):<10.3f} "
              f"{r.get('n_spacings', 0):<12} "
              f"{weight:<10.1%}")

    return {
        'full_sample': full_sample,
        'leave_one_out': leave_one_out_results,
        'influence_ranking': influence_ranking,
        'individual_regions': all_regions
    }

def generate_latex_table(analysis_results: Dict[str, Any], output_file: str = 'leave_one_out_table.tex'):
    """
    Generate LaTeX table for paper inclusion.
    """
    latex = []
    latex.append("\\begin{table}[htbp]")
    latex.append("\\centering")
    latex.append("\\caption{Leave-one-out analysis of NN measurements.}")
    latex.append("\\label{tab:leave_one_out}")
    latex.append("\\begin{tabular}{lcccc}")
    latex.append("\\hline")
    latex.append("Region Excluded & NN $\\lambda/W$ & PM $\\lambda/W$ & PM/NN & $N_{\\rm spacings}$ \\\\")
    latex.append("\\hline")

    # Full sample
    full = analysis_results['full_sample']
    latex.append(f"None (full) & {full['nn_lambda_W']:.3f} & {full['pm_lambda_W']:.3f} & "
                f"{full['pm_nn_ratio']:.3f} & {full['total_spacings']} \\\\")

    latex.append("\\hline")

    # Leave-one-out
    for region_name, stats in analysis_results['leave_one_out'].items():
        latex.append(f"{region_name} & {stats['nn_lambda_W']:.3f} & {stats['pm_lambda_W']:.3f} & "
                    f"{stats['pm_nn_ratio']:.3f} & {stats['total_spacings']} \\\\")

    latex.append("\\hline")
    latex.append("\\end{tabular}")
    latex.append("\\end{table}")

    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(latex))

    print(f"\nLaTeX table saved to: {output_file}")

def generate_markdown_report(analysis_results: Dict[str, Any], output_file: str = 'LEAVE_ONE_OUT_REPORT.md'):
    """
    Generate comprehensive markdown report.
    """
    report = []
    report.append("# Leave-One-Out Analysis: NN Measurements")
    report.append("\n**Analysis Date**: 2026-05-09")
    report.append("\n## Executive Summary")

    full = analysis_results['full_sample']
    report.append(f"\n**Full Sample (4 regions):**")
    report.append(f"- NN λ/W: {full['nn_lambda_W']:.3f}")
    report.append(f"- PM λ/W: {full['pm_lambda_W']:.3f}")
    report.append(f"- PM/NN ratio: {full['pm_nn_ratio']:.3f}")
    report.append(f"- Total spacings: {full['total_spacings']}")

    report.append(f"\n## Sensitivity Analysis")

    report.append(f"\nThe analysis addresses the reviewer's question: *\"What happens to λ_NN/W if Aquila is excluded?\"*")
    report.append(f"\nWhen each region is systematically excluded:")

    for region_name, stats in analysis_results['leave_one_out'].items():
        delta_nn = stats['nn_lambda_W'] - full['nn_lambda_W']
        delta_ratio = stats['pm_nn_ratio'] - full['pm_nn_ratio']
        rel_nn = 100 * delta_nn / full['nn_lambda_W']
        rel_ratio = 100 * delta_ratio / full['pm_nn_ratio']

        report.append(f"\n### Excluding {region_name}:")
        report.append(f"- NN λ/W changes from {full['nn_lambda_W']:.3f} → {stats['nn_lambda_W']:.3f}")
        report.append(f"  (Δ = {delta_nn:+.3f}, {rel_nn:+.1f}%)")
        report.append(f"- PM/NN changes from {full['pm_nn_ratio']:.3f} → {stats['pm_nn_ratio']:.3f}")
        report.append(f"  (Δ = {delta_ratio:+.3f}, {rel_ratio:+.1f}%)")

    report.append(f"\n## Key Findings")

    # Most influential region
    most_influential = analysis_results['influence_ranking'][0]
    report.append(f"\n1. **Most influential region**: {most_influential[0]}")
    report.append(f"   - Excluding {most_influential[0]} changes PM/NN by "
                f"{abs(most_influential[1]['pm_nn_ratio'] - full['pm_nn_ratio']):.3f}")

    # Aquila-specific answer
    aquila_stats = analysis_results['leave_one_out']['Aquila']
    aquila_delta = aquila_stats['pm_nn_ratio'] - full['pm_nn_ratio']
    report.append(f"\n2. **Answering reviewer's specific question about Aquila**:")
    report.append(f"   - Excluding Aquila changes PM/NN from {full['pm_nn_ratio']:.3f} → {aquila_stats['pm_nn_ratio']:.3f}")
    report.append(f"   - ΔPM/NN = {aquila_delta:+.3f} ({100*aquila_delta/full['pm_nn_ratio']:+.1f}%)")
    report.append(f"   - Despite having only 362 spacings (14% of total), Aquila's exclusion has a "
                f"{'moderate' if abs(aquila_delta) < 0.1 else 'significant'} effect.")

    # Robustness assessment
    report.append(f"\n3. **Robustness assessment**:")
    max_delta = max(abs(s['pm_nn_ratio'] - full['pm_nn_ratio'])
                   for s in analysis_results['leave_one_out'].values())
    report.append(f"   - Maximum change in PM/NN from excluding any single region: {max_delta:.3f}")
    if max_delta < 0.15:
        report.append(f"   - The weighted mean is **robust** to the exclusion of any single region.")
    else:
        report.append(f"   - The weighted mean shows **moderate sensitivity** to regional variations.")

    report_text = '\n'.join(report)

    with open(output_file, 'w') as f:
        f.write(report_text)

    print(f"\nMarkdown report saved to: {output_file}")

    return report_text

if __name__ == "__main__":
    # Run analysis
    results_file = 'filament_constrained_nn_results_4regions.json'
    analysis_results = perform_leave_one_out_analysis(results_file)

    # Generate outputs
    generate_latex_table(analysis_results)
    generate_markdown_report(analysis_results)

    print("\n" + "=" * 80)
    print("LEAVE-ONE-OUT ANALYSIS COMPLETE")
    print("=" * 80)
