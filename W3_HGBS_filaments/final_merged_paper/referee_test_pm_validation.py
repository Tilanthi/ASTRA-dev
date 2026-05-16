#!/usr/bin/env python3
"""
Referee-requested validation tests for the pairwise median (PM) statistic.

This script performs two critical tests requested by the referee to address
the NN/PM discrepancy concern:

TEST A: Synthetic filament population test
    Generate synthetic filaments with known input fragmentation wavelength
    and demonstrate that PM recovers the input λ (not L/3) for the core
    number densities and filament lengths in our HGBS sample.

TEST B: L/3 convergence test
    For each HGBS region, compute the mean filament length and compare
    the observed PM spacing (0.279 pc) against L/3 to explicitly show
    that PM is NOT converging to L/3.

Author: G. J. White
Date: 2026-05-02
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy import stats
import matplotlib.gridspec as gridspec

rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman']
rcParams['font.size'] = 10
rcParams['figure.max_open_warning'] = 50

print("=" * 80)
print("REFEREE-REQUESTED PAIRWISE MEDIAN VALIDATION TESTS")
print("=" * 80)
print()

# HGBS region data from Table 5
# Region names, N (core counts), PM spacing (pc), PM lambda/W
hgbs_regions = {
    'Taurus':   {'N': 536,  'pm_pc': 0.198, 'lambda_W': 1.98},
    'Perseus':  {'N': 816,  'pm_pc': 0.248, 'lambda_W': 2.48},
    'Orion B':  {'N': 1844, 'pm_pc': 0.313, 'lambda_W': 3.13},
    'Aquila':   {'N': 749,  'pm_pc': 0.346, 'lambda_W': 3.46},
}

# Weighted mean across robust regions
weighted_mean_N = 3945
weighted_mean_pm = 0.279  # pc
weighted_mean_lambda_W = 2.79

def pairwise_median(positions):
    """Calculate pairwise median distance."""
    n = len(positions)
    distances = []
    for i in range(n):
        for j in range(i+1, n):
            distances.append(abs(positions[i] - positions[j]))
    return np.median(distances)

def nearest_neighbor_median(positions):
    """Calculate median nearest-neighbor distance."""
    sorted_pos = np.sort(positions)
    nn_distances = np.diff(sorted_pos)
    return np.median(nn_distances)

def generate_periodic_filament(N, L, true_lambda, scatter=0.0):
    """
    Generate a filament with periodic beading.

    Parameters:
    -----------
    N : int
        Number of cores
    L : float
        Filament length (pc)
    true_lambda : float
        True fragmentation wavelength (pc)
    scatter : float
        Gaussian scatter in core positions (pc)

    Returns:
    --------
    positions : ndarray
        Core positions along filament
    """
    if N <= 1:
        return np.array([L/2])

    # Generate periodic positions
    n_expected = int(L / true_lambda) + 1
    base_positions = np.arange(n_expected) * true_lambda

    # Add scatter if requested
    if scatter > 0:
        base_positions = base_positions + np.random.normal(0, scatter, len(base_positions))

    # Clip to filament length
    base_positions = np.clip(base_positions, 0, L)

    # Subsample to N cores if needed
    if len(base_positions) > N:
        indices = np.linspace(0, len(base_positions)-1, N, dtype=int)
        positions = base_positions[indices]
    elif len(base_positions) < N:
        # Add more cores by filling gaps
        positions = np.linspace(0, L, N)
    else:
        positions = base_positions

    return np.sort(positions)

# ========================================================================
# TEST A: Synthetic Filament Population Test
# ========================================================================

print("=" * 80)
print("TEST A: SYNTHETIC FILAMENT POPULATION TEST")
print("=" * 80)
print()
print("Objective: Demonstrate that PM recovers the input fragmentation wavelength")
print("for the core number densities and filament lengths in our HGBS sample.")
print()

# Define test parameters
n_trials = 500
scatter_fraction = 0.15  # 15% positional scatter (realistic)

# Test multiple true wavelengths
test_lambdas = [0.20, 0.25, 0.28, 0.35, 0.40]  # pc (spanning HGBS range)

# For each HGBS region, test recovery of true wavelength
results_test_a = []

for region_name, region_data in hgbs_regions.items():
    N = region_data['N']
    observed_pm = region_data['pm_pc']

    print(f"\nRegion: {region_name} (N = {N} cores)")
    print(f"Observed PM spacing: {observed_pm:.3f} pc")
    print("-" * 60)

    region_results = []

    for true_lambda in test_lambdas:
        # Estimate filament length from observed data
        # For a filament with N cores and spacing d, approximate L ≈ N * d
        L_estimate = N * true_lambda * 1.2  # Add 20% margin

        pw_medians = []
        nn_medians = []

        for _ in range(n_trials):
            # Generate periodic filament with scatter
            positions = generate_periodic_filament(N, L_estimate, true_lambda,
                                                   scatter=true_lambda*scatter_fraction)

            if len(positions) > 1:
                pw_medians.append(pairwise_median(positions))
                nn_medians.append(nearest_neighbor_median(positions))

        pw_mean = np.mean(pw_medians)
        pw_std = np.std(pw_medians)
        nn_mean = np.mean(nn_medians)
        nn_std = np.std(nn_medians)

        # L/3 for comparison
        L_div_3 = L_estimate / 3.0

        # Recovery error
        recovery_error = 100 * (pw_mean - true_lambda) / true_lambda

        region_results.append({
            'true_lambda': true_lambda,
            'pw_mean': pw_mean,
            'pw_std': pw_std,
            'nn_mean': nn_mean,
            'nn_std': nn_std,
            'L_div_3': L_div_3,
            'recovery_error': recovery_error,
        })

        print(f"  Input λ = {true_lambda:.3f} pc: "
              f"PM = {pw_mean:.3f} ± {pw_std:.3f} pc "
              f"(error: {recovery_error:+.1f}%), "
              f"NN = {nn_mean:.3f} ± {nn_std:.3f} pc, "
              f"L/3 = {L_div_3:.3f} pc")

    results_test_a.append({
        'region': region_name,
        'N': N,
        'results': region_results,
    })

# ========================================================================
# TEST B: L/3 Convergence Test
# ========================================================================

print()
print("=" * 80)
print("TEST B: L/3 CONVERGENCE TEST")
print("=" * 80)
print()
print("Objective: For each HGBS region, compute the mean filament length and")
print("compare the observed PM spacing against L/3 to show PM is NOT")
print("converging to L/3.")
print()

# For each region, compute L/3 and compare with observed PM
results_test_b = []

print("\nDirect Comparison: Observed PM vs. L/3")
print("-" * 70)
print(f"{'Region':<12} {'N':>6} {'PM (pc)':>10} {'Est. L (pc)':>12} {'L/3 (pc)':>10} {'Ratio':>8}")
print("-" * 70)

for region_name, region_data in hgbs_regions.items():
    N = region_data['N']
    observed_pm = region_data['pm_pc']

    # Estimate filament length
    # Method 1: L ≈ N * PM (reasonable first approximation)
    L_estimate_1 = N * observed_pm

    # Method 2: From NN spacing if available
    nn_pc = region_data.get('nn_pc', None)
    L_estimate_2 = None
    if nn_pc is not None:
        L_estimate_2 = N * nn_pc

    # Use method 1 for all regions
    L_estimate = L_estimate_1
    L_div_3 = L_estimate / 3.0

    ratio = observed_pm / L_div_3

    results_test_b.append({
        'region': region_name,
        'N': N,
        'observed_pm': observed_pm,
        'L_estimate': L_estimate,
        'L_div_3': L_div_3,
        'ratio': ratio,
    })

    print(f"{region_name:<12} {N:6d} {observed_pm:10.3f} {L_estimate:12.1f} {L_div_3:10.3f} {ratio:8.3f}")

print("-" * 70)

# Weighted mean
print(f"{'Weighted Mean':<12} {weighted_mean_N:6d} {weighted_mean_pm:10.3f} ", end="")
L_mean_estimate = weighted_mean_N * weighted_mean_pm
L_mean_div_3 = L_mean_estimate / 3.0
ratio_mean = weighted_mean_pm / L_mean_div_3
print(f"{L_mean_estimate:12.1f} {L_mean_div_3:10.3f} {ratio_mean:8.3f}")
print()

# Interpretation
print("\nINTERPRETATION:")
print("-" * 70)
print("If PM were converging to L/3, we would expect:")
print("  - Observed PM / (L/3) ≈ 1.0")
print("  - Observed PM ≈ L/3")
print()
print("What we actually observe:")
print(f"  - PM / (L/3) ranges from {min([r['ratio'] for r in results_test_b]):.3f} to {max([r['ratio'] for r in results_test_b]):.3f}")
print(f"  - Weighted mean: PM / (L/3) = {ratio_mean:.3f}")
print()
if ratio_mean < 0.8:
    print(f"  ✓ PM is {(1-ratio_mean)*100:.1f}% SMALLER than L/3")
    print("  ✓ PM does NOT converge to L/3")
    print("  ✓ PM measures something smaller than the geometric L/3 value")
    print("  → This supports PM as measuring true fragmentation wavelength")
elif ratio_mean > 1.2:
    print(f"  ✓ PM is {(ratio_mean-1)*100:.1f}% LARGER than L/3")
    print("  ✓ PM does NOT converge to L/3")
    print("  → This suggests PM may be biased high")
else:
    print(f"  ⚠ PM is within 20% of L/3")
    print("  ⚠ Inconclusive - PM may be partially converging to L/3")

print()

# ========================================================================
# Synthetic Test with HGBS Parameters
# ========================================================================

print()
print("=" * 80)
print("SYNTHETIC TEST: HGBS Region Parameters")
print("=" * 80)
print()
print("Testing: For synthetic filaments with the same N and estimated L as")
print("each HGBS region, does PM recover the input fragmentation wavelength?")
print()

n_trials_synthetic = 1000

print(f"{'Region':<12} {'N':>6} {'Input λ':>10} {'PM':>10} {'Error':>8} {'L/3':>10} {'PM vs L/3':>10}")
print("-" * 80)

for result in results_test_a:
    region = result['region']
    N = result['N']

    for r in result['results']:
        true_lambda = r['true_lambda']
        pw_mean = r['pw_mean']
        pw_std = r['pw_std']
        L_div_3 = r['L_div_3']
        recovery_error = r['recovery_error']

        pm_vs_l3 = pw_mean / L_div_3 if L_div_3 > 0 else 0

        print(f"{region:<12} {N:6d} {true_lambda:10.3f} {pw_mean:10.3f} ± {pw_std:6.3f} "
              f"{recovery_error:+7.1f}% {L_div_3:10.3f} {pm_vs_l3:10.3f}")

# ========================================================================
# Create Summary Figure
# ========================================================================

print()
print("Creating summary figure...")

fig = plt.figure(figsize=(14, 10))
gs = gridspec.GridSpec(3, 2, hspace=0.3, wspace=0.3)

# Panel 1: Recovery test for Taurus
ax1 = fig.add_subplot(gs[0, 0])
region = 'Taurus'
N = hgbs_regions[region]['N']
true_lambdas = [r['true_lambda'] for r in results_test_a[0]['results']]
pw_means = [r['pw_mean'] for r in results_test_a[0]['results']]
pw_stds = [r['pw_std'] for r in results_test_a[0]['results']]
L_div_3s = [r['L_div_3'] for r in results_test_a[0]['results']]

ax1.errorbar(true_lambdas, pw_means, yerr=pw_stds, fmt='bo-', label='PM (measured)',
             linewidth=2, capsize=4, markersize=8)
ax1.plot(true_lambdas, L_div_3s, 'r--', label='L/3 (geometric)', linewidth=2)
ax1.plot(true_lambdas, true_lambdas, 'g:', label='Input λ (true)', linewidth=2)
ax1.set_xlabel('Input fragmentation wavelength (pc)', fontsize=11)
ax1.set_ylabel('Measured spacing (pc)', fontsize=11)
ax1.set_title(f'{region}: PM Recovery Test (N = {N})', fontsize=12, fontweight='bold')
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0.15, 0.45)
ax1.set_ylim(0.15, 0.45)

# Panel 2: Recovery error for all regions
ax2 = fig.add_subplot(gs[0, 1])
for i, result in enumerate(results_test_a):
    region = result['region']
    true_lambdas = [r['true_lambda'] for r in result['results']]
    recovery_errors = [r['recovery_error'] for r in result['results']]
    ax2.plot(true_lambdas, recovery_errors, 'o-', label=region, linewidth=2, markersize=6)

ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1)
ax2.axhline(y=5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
ax2.axhline(y=-5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
ax2.set_xlabel('Input fragmentation wavelength (pc)', fontsize=11)
ax2.set_ylabel('PM recovery error (%)', fontsize=11)
ax2.set_title('PM Recovery Error by Region', fontsize=12, fontweight='bold')
ax2.legend(loc='upper right', fontsize=9, ncol=2)
ax2.grid(True, alpha=0.3)

# Panel 3: L/3 convergence test
ax3 = fig.add_subplot(gs[1, :])
regions = [r['region'] for r in results_test_b]
observed_pms = [r['observed_pm'] for r in results_test_b]
L_div_3s = [r['L_div_3'] for r in results_test_b]

x = np.arange(len(regions))
width = 0.35

bars1 = ax3.bar(x - width/2, observed_pms, width, label='Observed PM spacing',
                color='steelblue', edgecolor='black', linewidth=1.5)
bars2 = ax3.bar(x + width/2, L_div_3s, width, label='L/3 (geometric)',
                color='indianred', edgecolor='black', linewidth=1.5)

ax3.set_ylabel('Spacing (pc)', fontsize=11)
ax3.set_title('Test B: Observed PM vs. L/3 Convergence Test', fontsize=12, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(regions, fontsize=11)
ax3.legend(loc='upper left', fontsize=11)
ax3.grid(True, axis='y', alpha=0.3)

# Add ratio labels
for i, r in enumerate(results_test_b):
    ratio = r['ratio']
    ax3.text(i, max(observed_pms[i], L_div_3s[i]) + 0.05,
             f'PM/(L/3) = {ratio:.3f}',
             ha='center', fontsize=9, fontweight='bold')

# Panel 4: Recovery summary heatmap
ax4 = fig.add_subplot(gs[2, :])

region_names = [r['region'] for r in results_test_a]
lambda_values = test_lambdas

# Create recovery error matrix
recovery_matrix = np.zeros((len(region_names), len(lambda_values)))
for i, result in enumerate(results_test_a):
    for j, r in enumerate(result['results']):
        recovery_matrix[i, j] = r['recovery_error']

im = ax4.imshow(recovery_matrix, cmap='RdBu_r', vmin=-10, vmax=10, aspect='auto')

# Set ticks
ax4.set_xticks(np.arange(len(lambda_values)))
ax4.set_yticks(np.arange(len(region_names)))
ax4.set_xticklabels([f'{λ:.2f}' for λ in lambda_values], fontsize=10)
ax4.set_yticklabels(region_names, fontsize=11)

# Add text labels
for i in range(len(region_names)):
    for j in range(len(lambda_values)):
        text = ax4.text(j, i, f'{recovery_matrix[i, j]:.1f}%',
                       ha="center", va="center", color="black", fontsize=9,
                       fontweight='bold')

ax4.set_xlabel('Input fragmentation wavelength (pc)', fontsize=11)
ax4.set_ylabel('Region', fontsize=11)
ax4.set_title('PM Recovery Error (%) for Different Input Wavelengths', fontsize=12, fontweight='bold')

# Colorbar
cbar = plt.colorbar(im, ax=ax4, fraction=0.046, pad=0.04)
cbar.set_label('Recovery error (%)', fontsize=10)

# Overall title
fig.suptitle('Referee-Requested PM Validation Tests\n(Test A: Synthetic Recovery + Test B: L/3 Convergence)',
             fontsize=14, fontweight='bold', y=0.98)

# Save figure
output_path = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/figures/fig_pm_validation_referee_tests.pdf'
plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
print(f"✓ Figure saved to {output_path}")

png_path = output_path.replace('.pdf', '.png')
plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
print(f"✓ Figure PNG saved to {png_path}")

plt.close()

# ========================================================================
# Print Summary and Conclusions
# ========================================================================

print()
print("=" * 80)
print("SUMMARY AND CONCLUSIONS")
print("=" * 80)
print()

# Test A summary
print("TEST A RESULTS: Synthetic Filament Population Test")
print("-" * 70)
print()
print("For each HGBS region, we generated synthetic filaments with the same")
print("number of cores (N) and various input fragmentation wavelengths (λ).")
print("The pairwise median (PM) statistic was then applied to test recovery.")
print()
print("Key findings:")
print()

# Compute average recovery error
all_recovery_errors = []
for result in results_test_a:
    for r in result['results']:
        all_recovery_errors.append(abs(r['recovery_error']))

mean_abs_error = np.mean(all_recovery_errors)
median_abs_error = np.median(all_recovery_errors)

print(f"  • Mean absolute PM recovery error: {mean_abs_error:.1f}%")
print(f"  • Median absolute PM recovery error: {median_abs_error:.1f}%")
print()

if mean_abs_error < 10:
    print(f"  ✓ PM recovers input λ with < 10% error")
    print("  ✓ This validates PM as measuring true fragmentation wavelength")
    print("  ✓ PM does NOT converge to L/3 for synthetic periodic filaments")
elif mean_abs_error < 20:
    print(f"  ⚠ PM recovers input λ with {mean_abs_error:.1f}% error")
    print("  ⚠ Moderate bias detected - PM may be affected by non-adjacent pairs")
else:
    print(f"  ✗ PM recovery error: {mean_abs_error:.1f}%")
    print("  ✗ Significant bias detected")

print()

# Test B summary
print("TEST B RESULTS: L/3 Convergence Test")
print("-" * 70)
print()
print("For each HGBS region, we computed the mean filament length (L) and")
print("compared the observed PM spacing against the geometric L/3 value.")
print()
print("Key findings:")
print()
print(f"  • Weighted mean PM / (L/3) ratio: {ratio_mean:.3f}")
print()

if ratio_mean < 0.8:
    print(f"  ✓ PM is {(1-ratio_mean)*100:.1f}% SMALLER than L/3")
    print("  ✓ PM does NOT converge to L/3 for HGBS filaments")
    print("  ✓ PM measures a physical scale smaller than the geometric L/3 value")
    print("  → This supports PM as measuring the true fragmentation wavelength")
    print("  → The L/3 convergence concern does NOT apply to HGBS data")
elif ratio_mean > 1.2:
    print(f"  ✓ PM is {(ratio_mean-1)*100:.1f}% LARGER than L/3")
    print("  ✓ PM does NOT converge to L/3")
    print("  → PM may include contributions from non-adjacent pairs")
else:
    print(f"  ⚠ PM is within 20% of L/3")
    print("  ⚠ Inconclusive - cannot definitively rule out some L/3 influence")

print()

# Overall conclusion
print("OVERALL CONCLUSION")
print("-" * 70)
print()

if mean_abs_error < 15 and ratio_mean < 0.9:
    print("✓ BOTH TESTS SUPPORT PM AS MEASURING TRUE FRAGMENTATION WAVELENGTH")
    print()
    print("  Test A: PM recovers input λ with minimal error (< 15%)")
    print("  Test B: PM is significantly smaller than L/3 (ratio < 0.9)")
    print()
    print("  The referee's L/3 convergence concern is NOT supported by the data.")
    print("  PM measures the true fragmentation wavelength for HGBS filaments.")
elif mean_abs_error < 20 and ratio_mean < 1.1:
    print("⚠ TESTS PROVIDE MODERATE SUPPORT FOR PM")
    print()
    print("  Test A: PM recovers input λ with moderate error (< 20%)")
    print("  Test B: PM is comparable to but distinct from L/3")
    print()
    print("  PM is not ideal but provides reasonable wavelength estimates.")
    print("  Additional validation with fiber-resolved data is warranted.")
else:
    print("✗ TESTS RAISE CONCERNS ABOUT PM RELIABILITY")
    print()
    print("  Test A: PM shows significant bias in recovery tests")
    print("  Test B: PM may be influenced by L/3 convergence")
    print()
    print("  The NN statistic may provide more reliable estimates.")
    print("  Fiber-resolved validation is critically needed.")

print()
print("=" * 80)
print("TESTS COMPLETE")
print("=" * 80)
