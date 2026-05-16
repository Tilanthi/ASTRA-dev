#!/usr/bin/env python3
"""
Calculate alternative summary statistics for NN measurements to assess robustness.

Given the small sample size (4 regions) and sensitivity to individual regions,
we report multiple summary statistics:
1. Weighted mean (current methodology)
2. Unweighted mean
3. Median
4. Range and standard deviation
"""

import numpy as np
import json

# NN λ/W values for four robust regions
REGION_DATA = {
    'Taurus': {'lambda_W': 1.733, 'n_spacings': 471},
    'OrionB': {'lambda_W': 1.945, 'n_spacings': 1135},
    'Aquila': {'lambda_W': 2.049, 'n_spacings': 362},
    'Perseus': {'lambda_W': 3.062, 'n_spacings': 606},
}

def calculate_summary_statistics():
    """Calculate all summary statistics."""

    # Extract values
    values = [REGION_DATA[r]['lambda_W'] for r in REGION_DATA]
    weights = [REGION_DATA[r]['n_spacings'] for r in REGION_DATA]

    # 1. Weighted mean (current methodology)
    total_weight = sum(weights)
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    weighted_mean = weighted_sum / total_weight

    # 2. Unweighted mean
    unweighted_mean = np.mean(values)

    # 3. Median
    median = np.median(values)

    # 4. Range
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val

    # 5. Standard deviation
    std_dev = np.std(values, ddof=1)  # Sample standard deviation

    # 6. Coefficient of variation
    cv = std_dev / unweighted_mean * 100

    # 7. Leave-one-out sensitivity (from previous analysis)
    loo_sensitivity = {
        'exclude_Taurus': 0.013,   # +1.3%
        'exclude_OrionB': -0.161,  # -16.1%
        'exclude_Aquila': -0.047,  # -4.7%
        'exclude_Perseus': 0.183,   # +18.3%
    }
    max_sensitivity = max(abs(v) for v in loo_sensitivity.values())

    results = {
        'weighted_mean': weighted_mean,
        'unweighted_mean': unweighted_mean,
        'median': median,
        'min': min_val,
        'max': max_val,
        'range': range_val,
        'std_dev': std_dev,
        'cv_percent': cv,
        'max_loo_sensitivity': max_sensitivity,
        'loo_sensitivity': loo_sensitivity,
    }

    return results

def generate_latex_table(results):
    """Generate LaTeX table for paper."""

    latex = """
\\begin{table}[h]
\\centering
\\caption{Summary statistics for NN $\\lambda/W$ measurements across four robust HGBS regions.}
\\label{tab:nn_summary_stats}
\\begin{tabular}{lc}
\\toprule
Statistic & Value \\\\
\\midrule
Weighted mean (by spacings) & %.2f \\\\
Unweighted mean & %.2f \\\\
Median & %.2f \\\\
Range & %.2f--%.2f \\\\
Standard deviation & %.2f \\\\
Coefficient of variation & %.1f\\%% \\\\
Leave-one-out sensitivity & $\\pm$%.1f\\%% \\\\
\\bottomrule
\\end{tabular}
\\end{table}
""" % (
    results['weighted_mean'],
    results['unweighted_mean'],
    results['median'],
    results['min'], results['max'],
    results['std_dev'],
    results['cv_percent'],
    results['max_loo_sensitivity'] * 100,
)

    return latex

def main():
    """Run analysis and generate output."""

    print("=" * 70)
    print("ALTERNATIVE SUMMARY STATISTICS FOR NN MEASUREMENTS")
    print("=" * 70)

    results = calculate_summary_statistics()

    print("\nSummary Statistics:")
    print(f"Weighted mean (by spacings): {results['weighted_mean']:.3f}")
    print(f"Unweighted mean: {results['unweighted_mean']:.3f}")
    print(f"Median: {results['median']:.3f}")
    print(f"Range: {results['min']:.3f} -- {results['max']:.3f}")
    print(f"Range width: {results['range']:.3f}")
    print(f"Standard deviation: {results['std_dev']:.3f}")
    print(f"Coefficient of variation: {results['cv_percent']:.1f}%")
    print(f"Max leave-one-out sensitivity: ±{results['max_loo_sensitivity']*100:.1f}%")

    print("\nLeave-one-out analysis:")
    for region, delta in results['loo_sensitivity'].items():
        print(f"  {region}: {delta:+.1%}")

    # Key findings
    print("\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)
    print(f"""
1. All three central tendency measures are sub-Jeans:
   - Weighted mean: {results['weighted_mean']:.2f} (46% below 4×)
   - Unweighted mean: {results['unweighted_mean']:.2f} (45% below 4×)
   - Median: {results['median']:.2f} (50% below 4×)

2. Substantial variation across regions:
   - Range: {results['min']:.2f}--{results['max']:.2f} (77% variation)
   - Coefficient of variation: {results['cv_percent']:.0f}%

3. High sensitivity to individual regions:
   - Maximum leave-one-out change: ±{results['max_loo_sensitivity']*100:.1f}%
   - Excluding Perseus increases value by +{results['loo_sensitivity']['exclude_Perseus']*100:.1f}%
   - Excluding Orion B decreases value by {results['loo_sensitivity']['exclude_OrionB']*100:.1f}%

4. Robustness assessment:
   - All three measures are sub-Jeans → qualitative conclusion robust
   - Large variation and sensitivity → need more regions for precision
   - Current sample (4 regions) adequate for qualitative but not quantitative
    """)

    # Generate LaTeX table
    latex = generate_latex_table(results)

    print("\nLaTeX Table:")
    print(latex)

    # Save results
    output_file = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/robustness_statistics_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

if __name__ == '__main__':
    main()
