#!/usr/bin/env python3
"""
Jackknife uncertainty quantification for HGBS spacing measurements.

The jackknife is a resampling technique that estimates bias and variance
by systematically leaving out one observation at a time. For region-level
data, we perform leave-one-region-out jackknife.
"""

import numpy as np
from scipy import stats

# HGBS region data from Table 1
# Region, spacing_pc, spacing_err_pc, n_cores
region_data = [
    ("Orion B", 0.313, 0.047, 1844),
    ("Aquila", 0.346, 0.047, 749),
    ("Perseus", 0.248, 0.040, 816),
    ("Taurus", 0.198, 0.040, 536),
    ("Ophiuchus", 0.206, 0.053, 513),
    ("Serpens", 0.331, 0.097, 194),
    ("TMC1", 0.195, 0.056, 178),
    ("CRA", 0.248, 0.072, 239),
]

regions = np.array([d[0] for d in region_data])
spacing = np.array([d[1] for d in region_data])
spacing_err = np.array([d[2] for d in region_data])
n_cores = np.array([d[3] for d in region_data])

def weighted_mean(values, errors):
    """Calculate inverse-variance weighted mean."""
    weights = 1.0 / errors**2
    return np.sum(weights * values) / np.sum(weights)

def weighted_mean_error(values, errors):
    """Calculate standard error of weighted mean."""
    weights = 1.0 / errors**2
    weighted_sum = np.sum(weights * values)
    sum_weights = np.sum(weights)
    return np.sqrt(1.0 / sum_weights)

print("Jackknife Uncertainty Quantification")
print("=" * 70)
print()

# Full sample weighted mean (reference value)
full_mean = weighted_mean(spacing, spacing_err)
full_err = weighted_mean_error(spacing, spacing_err)
print(f"Full sample weighted mean: {full_mean:.4f} ± {full_err:.4f} pc")
print()

# Leave-one-region-out jackknife
print("Leave-One-Region-Out Jackknife:")
print("-" * 70)
print(f"{'Excluded':<12} {'Mean (pc)':<12} {'Δ from full':<15} {'N remaining'}")
print("-" * 70)

jackknife_means = []
for i, region in enumerate(regions):
    # Leave out region i
    mask = np.arange(len(regions)) != i
    spacing_jack = spacing[mask]
    err_jack = spacing_err[mask]
    
    mean_jack = weighted_mean(spacing_jack, err_jack)
    delta = mean_jack - full_mean
    jackknife_means.append(mean_jack)
    
    print(f"{region:<12} {mean_jack:<12.4f} {delta:>+11.4f} pc   {np.sum(mask)}")

print("-" * 70)
print()

# Jackknife bias estimate
jackknife_mean = np.mean(jackknife_means)
bias_estimate = (len(regions) - 1) * (jackknife_mean - full_mean)

# Jackknife variance estimate
pseudovalue_bias = []
for i in range(len(regions)):
    pseudovalue = len(regions) * full_mean - (len(regions) - 1) * jackknife_means[i]
    pseudovalue_bias.append(pseudovalue)

jackknife_variance = np.var(pseudovalue_bias, ddof=1) / len(regions)
jackknife_std = np.sqrt(jackknife_variance)

print("Jackknife Statistics:")
print("-" * 70)
print(f"Jackknife mean:          {jackknife_mean:.4f} pc")
print(f"Full sample mean:        {full_mean:.4f} pc")
print(f"Bias estimate:           {bias_estimate:+.4f} pc ({bias_estimate/full_mean*100:+.2f}%)")
print(f"Jackknife std error:     {jackknife_std:.4f} pc")
print(f"Formal std error:        {full_err:.4f} pc")
print()

# Bias-corrected estimate
bias_corrected = full_mean - bias_estimate
print(f"Bias-corrected mean:     {bias_corrected:.4f} pc")
print()

# Compare with bootstrap (from previous analysis)
print("Comparison with Bootstrap:")
print("-" * 70)
# Bootstrap 95% CI was [0.261, 0.298] pc
bootstrap_ci_halfwidth = (0.298 - 0.261) / 2
print(f"Bootstrap 95% CI half-width: ±{bootstrap_ci_halfwidth:.4f} pc")
print(f"Jackknife std error:        ±{jackknife_std:.4f} pc")
print(f"Ratio (jackknife/bootstrap): {jackknife_std/bootstrap_ci_halfwidth:.2f}")
print()

# Robust regions only
robust_mask = np.array([True, True, True, True, False, False, False, False])
spacing_robust = spacing[robust_mask]
err_robust = spacing_err[robust_mask]

robust_mean = weighted_mean(spacing_robust, err_robust)
robust_err = weighted_mean_error(spacing_robust, err_robust)

print("Robust Regions Only (Orion B, Aquila, Perseus, Taurus):")
print("-" * 70)
print(f"Weighted mean: {robust_mean:.4f} ± {robust_err:.4f} pc")

# Leave-one-out jackknife for robust regions
robust_jackknife_means = []
for i in range(np.sum(robust_mask)):
    mask = np.arange(np.sum(robust_mask)) != i
    mean_jack = weighted_mean(spacing_robust[mask], err_robust[mask])
    robust_jackknife_means.append(mean_jack)

robust_jackknife_mean = np.mean(robust_jackknife_means)
robust_pseudovalue_bias = []
for i in range(len(robust_jackknife_means)):
    pseudovalue = 4 * robust_mean - 3 * robust_jackknife_means[i]
    robust_pseudovalue_bias.append(pseudovalue)
robust_jackknife_variance = np.var(robust_pseudovalue_bias, ddof=1) / 4
robust_jackknife_std = np.sqrt(robust_jackknife_variance)

robust_bias_estimate = 3 * (robust_jackknife_mean - robust_mean)

print(f"Jackknife std error (robust): ±{robust_jackknife_std:.4f} pc")
print(f"Bias estimate (robust):       {robust_bias_estimate:+.4f} pc")
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("The jackknife analysis reveals:")
print(f"1. Negligible bias in the weighted mean estimate ({abs(bias_estimate/full_mean)*100:.1f}%)")
print(f"2. Jackknife std error ({jackknife_std:.4f} pc) is {jackknife_std/full_err:.2f}× larger than formal error")
print(f"3. Robust regions show similar pattern: jackknife error {robust_jackknife_std:.4f} vs formal {robust_err:.4f} pc")
print()
print("Conclusion: The formal statistical errors underestimate the true")
print("uncertainty. The jackknife confirms the bootstrap result that")
print("region-to-region variation contributes additional scatter.")
