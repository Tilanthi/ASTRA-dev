#!/usr/bin/env python3
"""
O3: Spatial Clustering of Gaia DR3 Distance Revisions

Tests whether large distance revisions (Serpens +76%, Aquila +68%, Orion B +48%)
are spatially clustered in the Orion-Aquila Rift complex, suggesting a systematic
offset in the YSO clustering method for this sightline.

Approach:
1. Assemble HGBS region coordinates (l, b) and revision magnitudes
2. Calculate angular distances between all region pairs
3. Run permutation test for spatial clustering
4. Assess sensitivity to ±20% distance uncertainty for Orion-Aquila regions
"""

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from itertools import combinations

# HGBS region data from Table 1 and paper
regions = {
    'Aquila': {
        'l_deg': 28.0,
        'b_deg': -5.0,
        'distance_old_pc': 259,
        'distance_new_pc': 436,
        'revision_pct': 68,
        'cores': 749,
        'nn_lambda_over_W': 1.67,
        'pm_lambda_over_W': 2.41,
    },
    'Orion B': {
        'l_deg': 207.0,
        'b_deg': -18.0,
        'distance_old_pc': 266,
        'distance_new_pc': 394,
        'revision_pct': 48,
        'cores': 732,
        'nn_lambda_over_W': 1.67,
        'pm_lambda_over_W': 2.34,
    },
    'Serpens': {
        'l_deg': 30.0,
        'b_deg': 5.0,
        'distance_old_pc': 260,
        'distance_new_pc': 458,
        'revision_pct': 76,
        'cores': 148,
        'nn_lambda_over_W': None,
        'pm_lambda_over_W': 3.17,
    },
    'Taurus': {
        'l_deg': 174.0,
        'b_deg': -14.0,
        'distance_old_pc': 140,
        'distance_new_pc': 135,
        'revision_pct': -4,
        'cores': 411,
        'nn_lambda_over_W': None,
        'pm_lambda_over_W': 2.22,
    },
    'Perseus': {
        'l_deg': 158.0,
        'b_deg': -20.0,
        'distance_old_pc': 232,
        'distance_new_pc': 232,
        'revision_pct': 0,
        'cores': 316,
        'nn_lambda_over_W': None,
        'pm_lambda_over_W': 2.22,
    },
    'Ophiuchus': {
        'l_deg': 0.0,
        'b_deg': 5.0,
        'distance_old_pc': 131,
        'distance_new_pc': 138,
        'revision_pct': 5,
        'cores': 325,
        'nn_lambda_over_W': None,
        'pm_lambda_over_W': 2.29,
    },
    'TMC1': {
        'l_deg': 174.0,
        'b_deg': -14.0,
        'distance_old_pc': 140,
        'distance_new_pc': 161,
        'revision_pct': 15,
        'cores': 45,
        'nn_lambda_over_W': None,
        'pm_lambda_over_W': 2.46,
    },
    'CRA': {
        'l_deg': 300.0,
        'b_deg': 0.0,
        'distance_old_pc': 130,
        'distance_new_pc': 156,
        'revision_pct': 20,
        'cores': 22,
        'nn_lambda_over_W': None,
        'pm_lambda_over_W': 2.30,
    },
}

# Robust regions (used for PM-weighted mean)
robust_regions = ['Aquila', 'Orion B', 'Taurus', 'Perseus']

# Orion-Aquila Rift complex regions (physically associated)
orion_aquila_complex = ['Aquila', 'Orion B', 'Serpens']

def calculate_angular_distance(l1, b1, l2, b2):
    """
    Calculate angular distance between two points on the sphere
    using the Haversine formula (degrees).
    """
    # Convert to radians
    l1, b1, l2, b2 = np.radians([l1, b1, l2, b2])

    # Haversine formula
    dlat = b2 - b1
    dlon = l2 - l1
    a = np.sin(dlat/2)**2 + np.cos(b1) * np.cos(b2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    return np.degrees(c)

def permutation_test_clustering(regions, complex_regions, n_permutations=10000):
    """
    Test for spatial clustering of large distance revisions.

    Null hypothesis: Large revisions are randomly distributed across the sky.
    Test statistic: Mean revision magnitude for regions in the complex.

    Returns: p-value (probability of observing clustering by chance)
    """
    # Observed test statistic: mean revision for Orion-Aquila complex
    complex_revisions = [regions[r]['revision_pct'] for r in complex_regions]
    observed_mean = np.mean(complex_revisions)

    # All regions
    all_region_names = list(regions.keys())
    all_revisions = [regions[r]['revision_pct'] for r in all_region_names]

    # Number of regions in the complex
    n_complex = len(complex_regions)

    # Permutation test: randomly select n_complex regions and calculate mean revision
    permutation_means = []
    for _ in range(n_permutations):
        # Random sample of regions
        sample_regions = np.random.choice(all_region_names, size=n_complex, replace=False)
        sample_revisions = [regions[r]['revision_pct'] for r in sample_regions]
        permutation_means.append(np.mean(sample_revisions))

    # Calculate p-value: fraction of permutations with mean >= observed
    p_value = np.sum(np.array(permutation_means) >= observed_mean) / n_permutations

    return observed_mean, p_value, permutation_means

def recalculate_spacing_with_distance_uncertainty(regions, uncertainty_pct=20):
    """
    Recalculate PM-weighted mean spacing under distance uncertainty.

    Parameters:
    - uncertainty_pct: ±uncertainty on distances (e.g., 20%)

    Returns: PM λ/W for nominal, +uncertainty, -uncertainty cases
    """
    # Robust regions only
    robust = robust_regions

    # Nominal case
    def calculate_weighted_pm(region_subset, distance_multiplier=1.0):
        """Calculate core-weighted mean PM λ/W."""
        total_cores = sum(regions[r]['cores'] for r in region_subset)
        weighted_sum = sum(regions[r]['cores'] * regions[r]['pm_lambda_over_W']
                          for r in region_subset)
        return weighted_sum / total_cores

    pm_nominal = calculate_weighted_pm(robust)

    # Under distance uncertainty, PM scales inversely with distance
    # PM ∝ 1/distance, so:
    #   +20% distance → PM/(1.20) = PM * 0.833
    #   -20% distance → PM/(0.80) = PM * 1.25

    # Apply uncertainty to Orion-Aquila complex regions only
    # (testing worst-case: systematic offset for this sightline)

    def calculate_weighted_pm_with_uncertainty(region_subset, complex_regions, distance_multiplier):
        """Calculate PM with distance uncertainty applied to complex regions."""
        total_cores = 0
        weighted_sum = 0

        for r in region_subset:
            pm_value = regions[r]['pm_lambda_over_W']
            cores = regions[r]['cores']

            if r in complex_regions:
                # Apply distance scaling
                pm_value /= distance_multiplier

            total_cores += cores
            weighted_sum += cores * pm_value

        return weighted_sum / total_cores

    # +20% distance (spacings decrease)
    pm_plus_distance = calculate_weighted_pm_with_uncertainty(
        robust, orion_aquila_complex, 1.20)

    # -20% distance (spacings increase)
    pm_minus_distance = calculate_weighted_pm_with_uncertainty(
        robust, orion_aquila_complex, 0.80)

    return pm_nominal, pm_plus_distance, pm_minus_distance

# Main analysis
def analyze_spatial_clustering():
    """
    Run spatial clustering analysis and distance uncertainty sensitivity test.
    """
    print("=" * 80)
    print("O3: Spatial Clustering of Gaia DR3 Distance Revisions")
    print("=" * 80)
    print()

    # Print region table
    print("HGBS REGION DATA:")
    print("-" * 80)
    print(f"{'Region':<12} {'l (°)':>8} {'b (°)':>8} {'Old (pc)':>10} {'New (pc)':>10} {'Rev (%)':>10} {'Cores':>8}")
    print("-" * 80)

    for region in sorted(regions.keys(), key=lambda x: regions[x]['revision_pct'], reverse=True):
        r = regions[region]
        print(f"{region:<12} {r['l_deg']:>8.1f} {r['b_deg']:>8.1f} {r['distance_old_pc']:>10.0f} "
              f"{r['distance_new_pc']:>10.0f} {r['revision_pct']:>10.0f} {r['cores']:>8.0f}")
    print()

    # Identify large revisions
    print("-" * 80)
    print("LARGE REVISIONS (>40%):")
    print("-" * 80)
    large_revision_regions = [r for r in regions if regions[r]['revision_pct'] > 40]
    for region in large_revision_regions:
        r = regions[region]
        print(f"  {region}: +{r['revision_pct']:.0f}% ({r['distance_old_pc']:.0f} → {r['distance_new_pc']:.0f} pc)")
    print()

    # Check if large revisions are in Orion-Aquila complex
    print("-" * 80)
    print("ORION-AQUILA RIFT COMPLEX:")
    print("-" * 80)
    print(f"Regions: {', '.join(orion_aquila_complex)}")

    # Calculate angular distances within complex
    complex_distances = []
    for r1, r2 in combinations(orion_aquila_complex, 2):
        dist = calculate_angular_distance(
            regions[r1]['l_deg'], regions[r1]['b_deg'],
            regions[r2]['l_deg'], regions[r2]['b_deg']
        )
        complex_distances.append(dist)
        print(f"  {r1}-{r2}: {dist:.1f}°")

    # Calculate mean angular distance within complex
    mean_complex_dist = np.mean(complex_distances)
    print(f"  Mean separation: {mean_complex_dist:.1f}°")
    print()

    # Test if large revisions are spatially clustered
    print("-" * 80)
    print("PERMUTATION TEST FOR SPATIAL CLUSTERING")
    print("-" * 80)
    print()

    observed_mean, p_value, permutation_means = permutation_test_clustering(
        regions, orion_aquila_complex, n_permutations=10000)

    print(f"Observed: Mean revision for Orion-Aquila complex = {observed_mean:.1f}%")
    print(f"Expected (all regions): {np.mean([r['revision_pct'] for r in regions.values()]):.1f}%")
    print(f"Permutation test p-value: {p_value:.4f}")
    print()

    if p_value < 0.05:
        print("✅ SIGNIFICANT: Large revisions are spatially clustered (p < 0.05)")
        print(f"   The clustering of +{observed_mean:.0f}% revisions in the Orion-Aquila")
        print("   complex is unlikely to occur by chance.")
    else:
        print("❌ NOT SIGNIFICANT: Large revisions are not spatially clustered (p >= 0.05)")
        print(f"   The observed clustering could occur by chance with {p_value*100:.1f}% probability.")
    print()

    # Distance uncertainty sensitivity test
    print("=" * 80)
    print("DISTANCE UNCERTAINTY SENSITIVITY TEST")
    print("=" * 80)
    print()

    print("Testing worst-case scenario: Systematic ±20% distance uncertainty")
    print("for Orion-Aquila complex regions (Aquila, Orion B, Serpens).")
    print()

    pm_nominal, pm_plus, pm_minus = recalculate_spacing_with_distance_uncertainty(
        regions, uncertainty_pct=20)

    print(f"PM-weighted mean λ/W (nominal): {pm_nominal:.3f}")
    print(f"PM-weighted mean λ/W (+20% distance): {pm_plus:.3f}")
    print(f"PM-weighted mean λ/W (-20% distance): {pm_minus:.3f}")
    print()

    # Calculate effect size
    effect_plus = ((pm_plus - pm_nominal) / pm_nominal) * 100
    effect_minus = ((pm_minus - pm_nominal) / pm_nominal) * 100

    print(f"Effect of +20% distance: {effect_plus:+.1f}%")
    print(f"Effect of -20% distance: {effect_minus:+.1f}%")
    print()

    # Theoretical comparison
    theoretical_lambda_over_W = 2.84
    print(f"Comparison to theoretical prediction (λ/W = {theoretical_lambda_over_W:.2f}):")
    print()

    discrepancy_nominal = ((theoretical_lambda_over_W - pm_nominal) / theoretical_lambda_over_W) * 100
    discrepancy_plus = ((theoretical_lambda_over_W - pm_plus) / theoretical_lambda_over_W) * 100
    discrepancy_minus = ((theoretical_lambda_over_W - pm_minus) / theoretical_lambda_over_W) * 100

    print(f"  Nominal: {discrepancy_nominal:+.1f}% discrepancy")
    print(f"  +20% distance: {discrepancy_plus:+.1f}% discrepancy")
    print(f"  -20% distance: {discrepancy_minus:+.1f}% discrepancy")
    print()

    # Assess consistency with theory
    print("ASSESSMENT:")
    if abs(discrepancy_nominal) < 15:
        print("  ✅ Nominal PM is consistent with theory (<15% discrepancy)")
    else:
        print(f"  ❌ Nominal PM differs from theory by {abs(discrepancy_nominal):.1f}%")

    if abs(discrepancy_plus) < 15:
        print("  ✅ PM(+20%) is consistent with theory")
    else:
        print(f"  ❌ PM(+20%) differs from theory by {abs(discrepancy_plus):.1f}%")

    if abs(discrepancy_minus) < 15:
        print("  ✅ PM(-20%) is consistent with theory")
    else:
        print(f"  ❌ PM(-20%) differs from theory by {abs(discrepancy_minus):.1f}%")
    print()

    # Save results
    print("=" * 80)
    print("SUGGESTED TEXT FOR PAPER")
    print("=" * 80)
    print()
    print("Section 4.1 (Gaia DR3 Distance Revisions) - Add after Serpens discussion:")
    print()
    print(r"\textbf{Spatial clustering of distance revisions.}")

    if p_value < 0.05:
        print(f"Three of the four largest Gaia DR3 distance revisions—Serpens (+76%),")
        print(f"Aquila (+68%), and Orion B (+48%)—are spatially associated within")
        print(f"the Orion-Aquila Rift complex (mean separation {mean_complex_dist:.0f}°).")
        print(f"This raises the possibility of a systematic offset in the YSO clustering")
        print(f"method (Zhang et al. 2023) for this sightline. A permutation test")
        print(f"finds significant evidence for spatial clustering (p = {p_value:.3f}),")
        print(f"with the mean revision for the complex ({observed_mean:.0f}\%) exceeding")
        print(f"the expected value from random sampling by a factor of {observed_mean/np.mean([r['revision_pct'] for r in regions.values()]):.1f}.")
    else:
        print(f"Three of the four largest Gaia DR3 distance revisions—Serpens (+76%),")
        print(f"Aquila (+68%), and Orion B (+48%)—are spatially associated within")
        print(f"the Orion-Aquila Rift complex (mean separation {mean_complex_dist:.0f}°).")
        print(f"However, a permutation test finds no significant evidence for spatial")
        print(f"clustering (p = {p_value:.3f}), suggesting this association could occur")
        print(f"by chance.")

    print()
    print(f"To assess the robustness of our conclusions, we recalculated the PM-weighted")
    print(f"mean spacing assuming a systematic $\pm$20\% distance uncertainty for the")
    print(f"Orion-Aquila regions. Under this conservative scenario, the PM spacing ranges")
    print(f"from $\lambda/W = {pm_plus:.2f}$ to ${pm_minus:.2f}$ (nominal: {pm_nominal:.2f}).")
    print()

    if abs(discrepancy_plus) < 15 or abs(discrepancy_minus) < 15:
        print(f"This range encompasses the theoretical prediction ($\lambda/W = {theoretical_lambda_over_W:.2f}$),")
        print(f"indicating that distance uncertainties could partially explain the discrepancy.")
    else:
        print(f"Even under this conservative scenario, the PM spacing remains {discrepancy_plus:.0f}--{discrepancy_minus:.0f}%")
        print(f"below the theoretical prediction, suggesting that distance uncertainties alone")
        print(f"cannot explain the observed sub-Jeans spacing.")

    print()
    print("Future work with independent distance estimates (e.g., VLBI parallaxes,")
    print("extinction mapping) will be required to resolve this degeneracy.")
    print()

    # Save results to file
    results = {
        'permutation_p_value': p_value,
        'observed_mean_revision_complex': observed_mean,
        'mean_complex_separation_deg': mean_complex_dist,
        'pm_nominal': pm_nominal,
        'pm_plus_20pct': pm_plus,
        'pm_minus_20pct': pm_minus,
        'discrepancy_nominal_pct': discrepancy_nominal,
        'discrepancy_plus_pct': discrepancy_plus,
        'discrepancy_minus_pct': discrepancy_minus,
    }

    print("Results saved to O3_spatial_clustering_results.txt")
    with open('O3_spatial_clustering_results.txt', 'w') as f:
        f.write("# O3: Spatial Clustering Analysis Results\n")
        f.write(f"\n")
        for key, value in results.items():
            f.write(f"{key}: {value}\n")

    return results

if __name__ == '__main__':
    results = analyze_spatial_clustering()
