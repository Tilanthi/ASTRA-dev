#!/usr/bin/env python3
"""
Compare IC Sensitivity: King vs Uniform Initial Conditions

Performs statistical comparison of λ/W measurements between King profile
and uniform density initial conditions to quantify IC dependence in the
near-critical regime.
"""

import json
import numpy as np
from scipy import stats
from typing import Dict, List
import os

def load_lambda_W_measurements() -> List[Dict]:
    """Load λ/W measurements from analysis results."""
    measurements_path = "output/analysis/lambda_W_measurements.json"

    if not os.path.exists(measurements_path):
        raise FileNotFoundError(f"λ/W measurements not found. Run analyze_lambda_W.py first.")

    with open(measurements_path, 'r') as f:
        return json.load(f)

def filter_successful_measurements(measurements: List[Dict]) -> List[Dict]:
    """Filter for successful λ/W measurements only."""
    return [m for m in measurements if m['status'] == 'SUCCESS' and m['lambda_W'] is not None]

def group_by_ic_type(measurements: List[Dict]) -> Dict[str, List[Dict]]:
    """Group measurements by initial condition type."""
    king = [m for m in measurements if m.get('ic_type') == 'king']
    uniform = [m for m in measurements if m.get('ic_type') == 'uniform']

    return {'king': king, 'uniform': uniform}

def compute_statistics(values: List[float]) -> Dict:
    """Compute descriptive statistics for a list of values."""
    values = np.array(values)

    return {
        'mean': float(np.mean(values)),
        'median': float(np.median(values)),
        'std': float(np.std(values)),
        'sem': float(stats.sem(values)),  # Standard error of the mean
        'n': len(values),
        'min': float(np.min(values)),
        'max': float(np.max(values))
    }

def perform_statistical_tests(king_values: List[float], uniform_values: List[float]) -> Dict:
    """Perform statistical tests to compare King and Uniform IC results."""
    king_arr = np.array(king_values)
    unif_arr = np.array(uniform_values)

    results = {}

    # Two-sample t-test (assuming unequal variances)
    t_stat, t_pvalue = stats.ttest_ind(king_arr, unif_arr, equal_var=False)
    results['t_test'] = {
        'statistic': float(t_stat),
        'p_value': float(t_pvalue),
        'significant': t_pvalue < 0.05
    }

    # Kolmogorov-Smirnov test (distribution comparison)
    ks_stat, ks_pvalue = stats.ks_2samp(king_arr, unif_arr)
    results['ks_test'] = {
        'statistic': float(ks_stat),
        'p_value': float(ks_pvalue),
        'significant': ks_pvalue < 0.05
    }

    # Mann-Whitney U test (non-parametric comparison)
    u_stat, u_pvalue = stats.mannwhitneyu(king_arr, unif_arr, alternative='two-sided')
    results['mann_whitney'] = {
        'statistic': float(u_stat),
        'p_value': float(u_pvalue),
        'significant': u_pvalue < 0.05
    }

    # Cohen's d (effect size)
    pooled_std = np.sqrt(((len(king_arr) - 1) * np.var(king_arr) +
                          (len(unif_arr) - 1) * np.var(unif_arr)) /
                         (len(king_arr) + len(unif_arr) - 2))
    cohens_d = (np.mean(king_arr) - np.mean(unif_arr)) / pooled_std
    results['cohens_d'] = {
        'value': float(cohens_d),
        'interpretation': interpret_cohens_d(abs(cohens_d))
    }

    return results

def interpret_cohens_d(d: float) -> str:
    """Interpret Cohen's d effect size."""
    if d < 0.2:
        return "negligible"
    elif d < 0.5:
        return "small"
    elif d < 0.8:
        return "medium"
    else:
        return "large"

def analyze_parameter_dependence(measurements: List[Dict]) -> Dict:
    """Analyze how IC dependence varies with (f, beta, M)."""
    results = {
        'by_f': {},
        'by_beta': {},
        'by_mach': {}
    }

    # Group by f value
    f_groups = {}
    for m in measurements:
        f_val = m['f']
        if f_val not in f_groups:
            f_groups[f_val] = {'king': [], 'uniform': []}
        f_groups[f_val][m['ic_type']].append(m['lambda_W'])

    for f_val, groups in sorted(f_groups.items()):
        if groups['king'] and groups['uniform']:
            king_mean = np.mean(groups['king'])
            unif_mean = np.mean(groups['uniform'])
            diff_pct = (unif_mean - king_mean) / king_mean * 100

            results['by_f'][f_val] = {
                'king': float(king_mean),
                'uniform': float(unif_mean),
                'difference_percent': float(diff_pct),
                'n_king': len(groups['king']),
                'n_uniform': len(groups['uniform'])
            }

    # Group by beta value
    beta_groups = {}
    for m in measurements:
        beta_val = m['beta']
        if beta_val not in beta_groups:
            beta_groups[beta_val] = {'king': [], 'uniform': []}
        beta_groups[beta_val][m['ic_type']].append(m['lambda_W'])

    for beta_val, groups in sorted(beta_groups.items()):
        if groups['king'] and groups['uniform']:
            king_mean = np.mean(groups['king'])
            unif_mean = np.mean(groups['uniform'])
            diff_pct = (unif_mean - king_mean) / king_mean * 100

            results['by_beta'][beta_val] = {
                'king': float(king_mean),
                'uniform': float(unif_mean),
                'difference_percent': float(diff_pct),
                'n_king': len(groups['king']),
                'n_uniform': len(groups['uniform'])
            }

    return results

def generate_summary_report(comparison: Dict, parameter_dependence: Dict) -> str:
    """Generate a human-readable summary report."""
    report = []
    report.append("="*70)
    report.append("IC SENSITIVITY TEST SUMMARY REPORT")
    report.append("="*70)
    report.append("")

    # Overall comparison
    king_stats = comparison['king_statistics']
    unif_stats = comparison['uniform_statistics']

    report.append("OVERALL COMPARISON")
    report.append("-"*70)
    report.append(f"King IC:    λ/W = {king_stats['mean']:.3f} ± {king_stats['sem']:.3f} (N={king_stats['n']})")
    report.append(f"Uniform IC: λ/W = {unif_stats['mean']:.3f} ± {unif_stats['sem']:.3f} (N={unif_stats['n']})")

    diff = unif_stats['mean'] - king_stats['mean']
    diff_pct = diff / king_stats['mean'] * 100

    report.append(f"\nDifference: {diff:+.3f} ({diff_pct:+.1f}%)")
    report.append("")

    # Statistical tests
    tests = comparison['statistical_tests']
    report.append("STATISTICAL TESTS")
    report.append("-"*70)

    t_test = tests['t_test']
    report.append(f"Two-sample t-test: statistic={t_test['statistic']:.3f}, p={t_test['p_value']:.4f}")
    report.append(f"  Result: {'Significant' if t_test['significant'] else 'Not significant'} at α=0.05")

    ks_test = tests['ks_test']
    report.append(f"KS test: statistic={ks_test['statistic']:.3f}, p={ks_test['p_value']:.4f}")
    report.append(f"  Result: {'Significant' if ks_test['significant'] else 'Not significant'} at α=0.05")

    mw_test = tests['mann_whitney']
    report.append(f"Mann-Whitney U: statistic={mw_test['statistic']:.1f}, p={mw_test['p_value']:.4f}")
    report.append(f"  Result: {'Significant' if mw_test['significant'] else 'Not significant'} at α=0.05")

    cohens_d = tests['cohens_d']
    report.append(f"Cohen's d: {cohens_d['value']:.3f} ({cohens_d['interpretation']} effect size)")
    report.append("")

    # Parameter dependence
    report.append("PARAMETER DEPENDENCE")
    report.append("-"*70)

    if parameter_dependence['by_f']:
        report.append("By mass-to-line-mass ratio (f):")
        for f_val, data in sorted(parameter_dependence['by_f'].items()):
            report.append(f"  f={f_val:.2f}: King={data['king']:.3f}, Uniform={data['uniform']:.3f}, "
                         f"Diff={data['difference_percent']:+.1f}%")
        report.append("")

    if parameter_dependence['by_beta']:
        report.append("By plasma beta (β):")
        for beta_val, data in sorted(parameter_dependence['by_beta'].items()):
            report.append(f"  β={beta_val:.1f}: King={data['king']:.3f}, Uniform={data['uniform']:.3f}, "
                         f"Diff={data['difference_percent']:+.1f}%")
        report.append("")

    # Interpretation
    report.append("INTERPRETATION")
    report.append("-"*70)

    if abs(diff_pct) < 10:
        interpretation = "NO IC DEPENDENCE"
        explanation = "The fragmentation wavelength λ/W shows minimal dependence on initial condition choice (<10% difference). This strengthens confidence in the robustness of theoretical predictions for near-critical filament fragmentation."
    elif abs(diff_pct) < 30:
        interpretation = "WEAK IC DEPENDENCE"
        explanation = "The fragmentation wavelength λ/W shows mild dependence on initial condition choice (10-30% difference). Results suggest IC choice introduces some uncertainty but the overall trend is robust."
    else:
        interpretation = "STRONG IC DEPENDENCE"
        explanation = "The fragmentation wavelength λ/W shows significant dependence on initial condition choice (>30% difference). Near-critical fragmentation is sensitive to IC details, and theoretical predictions should be interpreted with caution."

    report.append(f"{interpretation}")
    report.append("")
    report.append(explanation)
    report.append("")

    report.append("="*70)

    return "\n".join(report)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compare IC sensitivity")
    parser.add_argument("--measurements", type=str, default="output/analysis/lambda_W_measurements.json",
                       help="Path to λ/W measurements JSON")
    parser.add_argument("--output", type=str, default="output/analysis/ic_sensitivity_summary.json",
                       help="Output JSON file")
    parser.add_argument("--report", type=str, default="output/analysis/ic_sensitivity_report.md",
                       help="Output report file")
    args = parser.parse_args()

    print("IC Sensitivity Test: Statistical Comparison")
    print("="*60)

    # Load measurements
    with open(args.measurements, 'r') as f:
        all_measurements = json.load(f)

    # Filter for successful measurements
    successful = filter_successful_measurements(all_measurements)
    print(f"Loaded {len(successful)} successful λ/W measurements")

    # Group by IC type
    grouped = group_by_ic_type(successful)

    print(f"King IC: {len(grouped['king'])} measurements")
    print(f"Uniform IC: {len(grouped['uniform'])} measurements")

    if not grouped['king'] or not grouped['uniform']:
        print("Error: Insufficient data for comparison")
        return

    # Extract λ/W values
    king_values = [m['lambda_W'] for m in grouped['king']]
    unif_values = [m['lambda_W'] for m in grouped['uniform']]

    # Compute statistics
    king_stats = compute_statistics(king_values)
    unif_stats = compute_statistics(unif_values)

    print(f"\nKing IC:    λ/W = {king_stats['mean']:.3f} ± {king_stats['sem']:.3f}")
    print(f"Uniform IC: λ/W = {unif_stats['mean']:.3f} ± {unif_stats['sem']:.3f}")

    diff = unif_stats['mean'] - king_stats['mean']
    diff_pct = diff / king_stats['mean'] * 100
    print(f"Difference: {diff:+.3f} ({diff_pct:+.1f}%)")

    # Perform statistical tests
    print("\nPerforming statistical tests...")
    statistical_tests = perform_statistical_tests(king_values, unif_values)

    print(f"  t-test: p={statistical_tests['t_test']['p_value']:.4f}")
    print(f"  KS test: p={statistical_tests['ks_test']['p_value']:.4f}")
    print(f"  Mann-Whitney: p={statistical_tests['mann_whitney']['p_value']:.4f}")
    print(f"  Cohen's d: {statistical_tests['cohens_d']['value']:.3f}")

    # Analyze parameter dependence
    print("\nAnalyzing parameter dependence...")
    parameter_dependence = analyze_parameter_dependence(successful)

    # Compile comparison summary
    comparison = {
        'king_statistics': king_stats,
        'uniform_statistics': unif_stats,
        'difference': {
            'absolute': float(diff),
            'percent': float(diff_pct)
        },
        'statistical_tests': statistical_tests,
        'parameter_dependence': parameter_dependence
    }

    # Write JSON output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(comparison, f, indent=2)

    print(f"\nJSON output written to {args.output}")

    # Generate and write report
    report_text = generate_summary_report(comparison, parameter_dependence)
    with open(args.report, 'w') as f:
        f.write(report_text)

    print(f"Report written to {args.report}")
    print("\n" + report_text)

    print("\nNext step: Run python3 generate_ic_comparison_figures.py")

if __name__ == "__main__":
    main()
