#!/usr/bin/env python3
"""
Distance revision correlation test.

Test whether spacing residuals correlate with distance revision magnitude.
If large distance revisions systematically bias spacing measurements, we would
expect to see a correlation between |ΔD/D_original| and spacing deviation from
the regional mean or expected value.
"""

import numpy as np
from scipy import stats

# HGBS region data from Table 1 of the paper
# Format: region, original_distance_pc, gaia_distance_pc, spacing_pc, spacing_err_pc, n_cores
region_data = [
    ("Orion B", 261, 386, 0.313, 0.047, 1844),
    ("Aquila", 260, 436, 0.346, 0.047, 749),
    ("Perseus", 247, 296, 0.248, 0.040, 816),
    ("Taurus", 140, 135, 0.198, 0.040, 536),
    ("Ophiuchus", 130, 137, 0.206, 0.053, 513),
    ("Serpens", 260, 458, 0.331, 0.097, 194),
    ("TMC1", 140, 135, 0.195, 0.056, 178),
    ("CRA", 130, 150, 0.248, 0.072, 239),
]

regions = np.array([d[0] for d in region_data])
d_orig = np.array([d[1] for d in region_data])
d_gaia = np.array([d[2] for d in region_data])
spacing = np.array([d[3] for d in region_data])
spacing_err = np.array([d[4] for d in region_data])
n_cores = np.array([d[5] for d in region_data])

# Calculate distance revision statistics
delta_d = d_gaia - d_orig
delta_d_frac = delta_d / d_orig  # Fractional change
abs_delta_d_frac = np.abs(delta_d_frac)

print("Distance Revision Correlation Test")
print("=" * 70)
print()

# Show distance revisions
print("Distance Revisions:")
print("-" * 70)
print(f"{'Region':<12} {'D_orig':<10} {'D_Gaia':<10} {'ΔD':>10} {'ΔD/D_orig':>12} {'N':>8}")
for i, region in enumerate(regions):
    print(f"{region:<12} {d_orig[i]:<10.0f} {d_gaia[i]:<10.0f} {delta_d[i]:>+10.0f} "
          f"{delta_d_frac[i]:>+11.1%} {n_cores[i]:>8}")
print()

# Test 1: Correlation between absolute distance revision and spacing
print("Test 1: Spacing vs. Absolute Distance Revision")
print("-" * 70)
corr1, pval1 = stats.pearsonr(abs_delta_d_frac, spacing)
print(f"Pearson r = {corr1:.3f}, p = {pval1:.3f}")
if pval1 < 0.05:
    print(f"Significant correlation detected (p < 0.05)")
else:
    print(f"No significant correlation (p >= 0.05)")
print()

# Test 2: Correlation between distance revision (signed) and spacing
print("Test 2: Spacing vs. Distance Revision (signed)")
print("-" * 70)
corr2, pval2 = stats.pearsonr(delta_d_frac, spacing)
print(f"Pearson r = {corr2:.3f}, p = {pval2:.3f}")
if pval2 < 0.05:
    print(f"Significant correlation detected (p < 0.05)")
    if corr2 > 0:
        print(f"Positive correlation: larger distance revisions → larger spacing")
    else:
        print(f"Negative correlation: larger distance revisions → smaller spacing")
else:
    print(f"No significant correlation (p >= 0.05)")
print()

# Test 3: Regression of spacing on distance
print("Test 3: Spacing vs. Distance (pc)")
print("-" * 70)
slope, intercept, r_value, p_value, std_err = stats.linregress(d_gaia, spacing)
print(f"λ = ({intercept:.3f} ± {std_err*intercept/slope:.3f}) + ({slope:.5f} ± {std_err:.5f}) × d")
print(f"r² = {r_value**2:.3f}, p = {p_value:.3f}")
if p_value < 0.05:
    print(f"Significant correlation detected (p < 0.05)")
else:
    print(f"No significant correlation (p >= 0.05)")
print()

# Test 4: Residuals analysis
# Calculate expected spacing from the regression
expected_spacing = intercept + slope * d_gaia
residuals = spacing - expected_spacing
residuals_normalized = residuals / spacing_err

print("Test 4: Spacing Residuals vs. Distance Revision Magnitude")
print("-" * 70)
print(f"{'Region':<12} {'λ_obs':<8} {'λ_exp':<8} {'Residual':<10} {'|ΔD/D|':<10}")
for i, region in enumerate(regions):
    print(f"{region:<12} {spacing[i]:<8.3f} {expected_spacing[i]:<8.3f} "
          f"{residuals[i]:>+9.3f} {abs_delta_d_frac[i]:<10.1%}")
print()

corr3, pval3 = stats.pearsonr(abs_delta_d_frac, residuals)
print(f"Correlation between |ΔD/D| and residuals: r = {corr3:.3f}, p = {pval3:.3f}")
if pval3 < 0.05:
    print(f"Significant correlation: distance revisions bias spacing measurements")
else:
    print(f"No significant correlation: no evidence of distance revision bias")
print()

# Test 5: Separate analysis for robust vs limited regions
robust_mask = np.array([True, True, True, True, False, False, False, False])
print("Test 5: Robust Regions Only (Orion B, Aquila, Perseus, Taurus)")
print("-" * 70)
corr4, pval4 = stats.pearsonr(abs_delta_d_frac[robust_mask], spacing[robust_mask])
print(f"Pearson r = {corr4:.3f}, p = {pval4:.3f}")
if pval4 < 0.05:
    print(f"Significant correlation detected (p < 0.05)")
else:
    print(f"No significant correlation (p >= 0.05)")
print()

# Test 6: Spearman rank correlation (non-parametric, robust to outliers)
print("Test 6: Spearman Rank Correlation (non-parametric)")
print("-" * 70)
spearman_corr, spearman_p = stats.spearmanr(abs_delta_d_frac, spacing)
print(f"Spearman ρ = {spearman_corr:.3f}, p = {spearman_p:.3f}")
if spearman_p < 0.05:
    print(f"Significant correlation detected (p < 0.05)")
else:
    print(f"No significant correlation (p >= 0.05)")
print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("Null hypothesis: No correlation between distance revisions and spacing")
print()
tests = [
    ("Abs revision vs spacing", pval1, corr1),
    ("Signed revision vs spacing", pval2, corr2),
    ("Distance vs spacing", p_value, slope),
    ("Abs revision vs residuals", pval3, corr3),
    ("Robust regions only", pval4, corr4),
    ("Spearman (non-param)", spearman_p, spearman_corr),
]

significant = [name for name, p, _ in tests if p < 0.05]
if significant:
    print(f"WARNING: {len(significant)}/{len(tests)} tests show significant correlations:")
    for name, p, val in tests:
        if p < 0.05:
            print(f"  - {name}: p = {p:.3f}")
else:
    print("No significant correlations detected across all tests.")
    print("Distance revisions do NOT appear to systematically bias spacing measurements.")
