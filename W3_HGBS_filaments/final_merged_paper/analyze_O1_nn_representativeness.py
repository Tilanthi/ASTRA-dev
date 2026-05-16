#!/usr/bin/env python3
"""
O1: NN Regional Representativeness - Quantitative Bias Assessment

Analyzes how NN results might change if Taurus and Perseus (nearest,
best-resolved HGBS regions) had different NN measurements than Orion B
and Aquila (current NN-only regions).

Three scenarios:
1. Taurus/Perseus match current NN (λ/W = 1.67)
2. Taurus/Perseus match PM/NN ratio from Orion B/Aquila (PM/NN = 1.45)
3. Taurus/Perseus match theoretical predictions (λ/W = 2.84)

Weighted by core counts from Table 1:
- Aquila: 749 cores, distance = 436 pc
- Orion B: 732 cores, distance = 394 pc
- Taurus: 411 cores, distance = 135 pc
- Perseus: 316 cores, distance = 232 pc
"""

import numpy as np
import pandas as pd

# HGBS region data from Table 1 and paper
regions = {
    'Aquila': {
        'cores': 749,
        'distance_pc': 436,
        'nn_lambda_over_W': 1.67,  # From NN analysis
        'pm_lambda_over_W': 2.41,  # From Table 2
    },
    'Orion B': {
        'cores': 732,
        'distance_pc': 394,
        'nn_lambda_over_W': 1.67,  # From NN analysis
        'pm_lambda_over_W': 2.34,  # From Table 2
    },
    'Taurus': {
        'cores': 411,
        'distance_pc': 135,
        'nn_lambda_over_W': None,  # UNKNOWN - this is what we're testing
        'pm_lambda_over_W': 2.22,  # From Table 2
    },
    'Perseus': {
        'cores': 316,
        'distance_pc': 232,
        'nn_lambda_over_W': None,  # UNKNOWN - this is what we're testing
        'pm_lambda_over_W': 2.22,  # From Table 2
    },
}

# Calculate weighted statistics for current NN regions (Aquila + Orion B)
def calculate_weighted_nn(regions_subset, nn_values):
    """Calculate core-weighted mean NN λ/W."""
    total_cores = sum(regions[r]['cores'] for r in regions_subset)
    weighted_sum = sum(regions[r]['cores'] * nn_values[r] for r in regions_subset)
    return weighted_sum / total_cores

# Current NN result (Aquila + Orion B only)
current_nn_regions = ['Aquila', 'Orion B']
current_nn_values = {r: regions[r]['nn_lambda_over_W'] for r in current_nn_regions}
current_nn_weighted = calculate_weighted_nn(current_nn_regions, current_nn_values)

print("=" * 80)
print("O1: NN Regional Representativeness Analysis")
print("=" * 80)
print()

# Print current situation
print("CURRENT SITUATION (NN measurements only for Aquila + Orion B):")
print(f"  Aquila: {regions['Aquila']['cores']} cores, NN λ/W = {regions['Aquila']['nn_lambda_over_W']:.2f}")
print(f"  Orion B: {regions['Orion B']['cores']} cores, NN λ/W = {regions['Orion B']['nn_lambda_over_W']:.2f}")
print(f"  Weighted NN λ/W = {current_nn_weighted:.3f}")
print(f"  Total cores with NN: {sum(regions[r]['cores'] for r in current_nn_regions)}")
print()

# Calculate PM/NN ratio for current NN regions
def calculate_weighted_pm(regions_subset):
    """Calculate core-weighted mean PM λ/W."""
    total_cores = sum(regions[r]['cores'] for r in regions_subset)
    weighted_sum = sum(regions[r]['cores'] * regions[r]['pm_lambda_over_W'] for r in regions_subset)
    return weighted_sum / total_cores

current_pm_weighted = calculate_weighted_pm(current_nn_regions)
current_pm_over_nn = current_pm_weighted / current_nn_weighted

print(f"  Weighted PM λ/W = {current_pm_weighted:.3f}")
print(f"  PM/NN ratio = {current_pm_over_nn:.3f}")
print()

print("-" * 80)
print("SCENARIO ANALYSIS: Adding Taurus and Perseus")
print("-" * 80)
print()

# Scenario 1: Taurus/Perseus match current NN measurements
print("SCENARIO 1: Taurus/Perseus NN = current NN (λ/W = 1.67)")
print("  Assumption: Nearby regions have same NN as distant regions")
scenario1_nn = {'Aquila': 1.67, 'Orion B': 1.67, 'Taurus': 1.67, 'Perseus': 1.67}
scenario1_weighted = calculate_weighted_nn(regions.keys(), scenario1_nn)
all_regions_pm = calculate_weighted_pm(regions.keys())
print(f"  Global NN λ/W = {scenario1_weighted:.3f}")
print(f"  Global PM λ/W = {all_regions_pm:.3f}")
print(f"  PM/NN ratio = {all_regions_pm / scenario1_weighted:.3f}")
print(f"  Change from current: {((scenario1_weighted - current_nn_weighted) / current_nn_weighted) * 100:+.1f}%")
print()

# Scenario 2: Taurus/Perseus NN based on PM/NN ratio from Aquila/Orion B
print("SCENARIO 2: Taurus/Perseus NN from PM/NN ratio (PM/NN = 1.45)")
print("  Assumption: Nearby regions have same PM/NN ratio as distant regions")
pm_over_nn_ratio = current_pm_weighted / current_nn_weighted
scenario2_nn = {
    'Aquila': 1.67,
    'Orion B': 1.67,
    'Taurus': regions['Taurus']['pm_lambda_over_W'] / pm_over_nn_ratio,
    'Perseus': regions['Perseus']['pm_lambda_over_W'] / pm_over_nn_ratio,
}
scenario2_weighted = calculate_weighted_nn(regions.keys(), scenario2_nn)
print(f"  Taurus NN λ/W = {scenario2_nn['Taurus']:.3f} (PM = {regions['Taurus']['pm_lambda_over_W']:.2f})")
print(f"  Perseus NN λ/W = {scenario2_nn['Perseus']:.3f} (PM = {regions['Perseus']['pm_lambda_over_W']:.2f})")
print(f"  Global NN λ/W = {scenario2_weighted:.3f}")
print(f"  Change from current: {((scenario2_weighted - current_nn_weighted) / current_nn_weighted) * 100:+.1f}%")
print()

# Scenario 3: Taurus/Perseus match theoretical predictions
print("SCENARIO 3: Taurus/Perseus NN = theoretical prediction (λ/W = 2.84)")
print("  Assumption: Nearby regions match theoretical MHD prediction")
theoretical_lambda_over_W = 2.84
scenario3_nn = {
    'Aquila': 1.67,
    'Orion B': 1.67,
    'Taurus': theoretical_lambda_over_W,
    'Perseus': theoretical_lambda_over_W,
}
scenario3_weighted = calculate_weighted_nn(regions.keys(), scenario3_nn)
print(f"  Taurus NN λ/W = {scenario3_nn['Taurus']:.3f}")
print(f"  Perseus NN λ/W = {scenario3_nn['Perseus']:.3f}")
print(f"  Global NN λ/W = {scenario3_weighted:.3f}")
print(f"  Change from current: {((scenario3_weighted - current_nn_weighted) / current_nn_weighted) * 100:+.1f}%")
print()

# Summary statistics
print("=" * 80)
print("SUMMARY: Regional Sampling Uncertainty")
print("=" * 80)
print()

scenarios = {
    'Scenario 1 (NN=1.67)': scenario1_weighted,
    'Scenario 2 (PM/NN=1.45)': scenario2_weighted,
    'Scenario 3 (Theory=2.84)': scenario3_weighted,
}

nn_values = list(scenarios.values())
nn_min = min(nn_values)
nn_max = max(nn_values)
nn_mean = np.mean(nn_values)
nn_std = np.std(nn_values)

print(f"Current NN λ/W (Aquila+Orion B only): {current_nn_weighted:.3f}")
print(f"Global NN λ/W ranges from: {nn_min:.3f} to {nn_max:.3f}")
print(f"Mean across scenarios: {nn_mean:.3f} ± {nn_std:.3f}")
print()

# Calculate systematic uncertainty
systematic_uncertainty = (nn_max - nn_min) / 2
relative_uncertainty = (systematic_uncertainty / current_nn_weighted) * 100

print(f"Systematic uncertainty (half-range): ±{systematic_uncertainty:.3f}")
print(f"Relative systematic uncertainty: ±{relative_uncertainty:.1f}%")
print()

# Compare to theoretical prediction
print("COMPARISON TO THEORY:")
print(f"  Theoretical prediction: λ/W = {theoretical_lambda_over_W:.2f}")
print(f"  Current NN measurement: λ/W = {current_nn_weighted:.3f}")
print(f"  Discrepancy: {((theoretical_lambda_over_W - current_nn_weighted) / theoretical_lambda_over_W) * 100:.1f}%")
print()
print(f"  Under worst-case scenario (NN = {nn_min:.3f}):")
print(f"    Discrepancy: {((theoretical_lambda_over_W - nn_min) / theoretical_lambda_over_W) * 100:.1f}%")
print()
print(f"  Under best-case scenario (NN = {nn_max:.3f}):")
print(f"    Discrepancy: {((theoretical_lambda_over_W - nn_max) / theoretical_lambda_over_W) * 100:.1f}%")
print()

# Core count weighting analysis
print("=" * 80)
print("CORE COUNT WEIGHTING ANALYSIS")
print("=" * 80)
print()
print("Region core counts:")
total_cores = sum(regions[r]['cores'] for r in regions)
for region in regions:
    fraction = (regions[region]['cores'] / total_cores) * 100
    print(f"  {region}: {regions[region]['cores']:3d} cores ({fraction:.1f}%)")
print()

print("Current NN regions (Aquila + Orion B):")
current_cores = sum(regions[r]['cores'] for r in current_nn_regions)
current_fraction = (current_cores / total_cores) * 100
print(f"  Total cores: {current_cores} ({current_fraction:.1f}%)")
print()

missing_cores = total_cores - current_cores
missing_fraction = (missing_cores / total_cores) * 100
print(f"Missing NN measurements (Taurus + Perseus):")
print(f"  Total cores: {missing_cores} ({missing_fraction:.1f}%)")
print()

print("IMPLICATION: Missing NN data for")
print(f"  {missing_fraction:.1f}% of cores introduces regional sampling")
print(f"  uncertainty of ±{relative_uncertainty:.1f}% in NN λ/W.")
print()

# Text for paper
print("=" * 80)
print("SUGGESTED TEXT FOR PAPER")
print("=" * 80)
print()
print("Section 3.2 (NN Methodology) - Add after current limitations:")
print()
print(r"\textbf{Regional representativeness and sampling uncertainty.}")
print()
print("The current NN analysis is restricted to Orion B and Aquila due to")
print("skeleton data availability. To assess the potential bias introduced by")
print("this sampling, we construct three scenarios for Taurus and Perseus,")
print(f"the nearest and best-resolved HGBS regions ({missing_cores:.0f} cores,")
print(f"{missing_fraction:.0f}% of the total sample): (1) NN consistent with")
print(f"current measurements ($\\lambda/W = {current_nn_weighted:.2f}$); (2) NN")
print(f"consistent with the PM/NN ratio observed in Orion B and Aquila")
print(f"(${pm_over_nn_ratio:.2f}$); and (3) NN consistent with theoretical")
print(f"predictions ($\\lambda/W = {theoretical_lambda_over_W:.2f}$).")
print()
print(f"Weighting by core counts, we find that the global NN spacing would")
print(f"range from $\\lambda/W = {nn_min:.2f}$ to ${nn_max:.2f}$ across these")
print(f"scenarios, corresponding to a systematic uncertainty of $\\pm$")
print(f"{relative_uncertainty:.0f}\%$. This regional sampling uncertainty is")
print(f"incorporated into the systematic error budget (Table 5).")
print()

# Save results to file
results = {
    'current_nn_weighted': current_nn_weighted,
    'scenario1_weighted': scenario1_weighted,
    'scenario2_weighted': scenario2_weighted,
    'scenario3_weighted': scenario3_weighted,
    'nn_min': nn_min,
    'nn_max': nn_max,
    'nn_mean': nn_mean,
    'nn_std': nn_std,
    'systematic_uncertainty': systematic_uncertainty,
    'relative_uncertainty_percent': relative_uncertainty,
    'missing_cores': missing_cores,
    'missing_fraction_percent': missing_fraction,
}

print("Results saved to O1_nn_representativeness_results.txt")
with open('O1_nn_representativeness_results.txt', 'w') as f:
    for key, value in results.items():
        f.write(f"{key}: {value}\n")
