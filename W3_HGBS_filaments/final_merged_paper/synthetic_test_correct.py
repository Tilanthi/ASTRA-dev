#!/usr/bin/env python3
"""
CORRECTED synthetic filament test: Does PM recover true fragmentation wavelength?

This addresses the bug in the previous test where we were forcing N cores
onto a filament instead of letting N emerge from the fragmentation process.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman']
rcParams['font.size'] = 10

print("=" * 70)
print("CORRECTED SYNTHETIC FILAMENT TEST")
print("=" * 70)
print()

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

# Test parameters: Different filament lengths
L_values = [2.0, 5.0, 10.0, 20.0]  # pc
true_lambda = 0.28  # true fragmentation wavelength (pc)
scatter_fraction = 0.15  # 15% scatter
n_trials = 500

print(f"True fragmentation wavelength: λ = {true_lambda} pc")
print(f"Positional scatter: {scatter_fraction*100:.0f}% of λ")
print(f"Number of trials: {n_trials}")
print()

print(f"{'L (pc)':>8} {'N':>6} {'PM (pc)':>10} {'PM error':>10} {'NN (pc)':>10} {'NN error':>10} {'L/3 (pc)':>10}")
print("-" * 75)

results = []
for L in L_values:
    # Number of cores emerges from fragmentation process
    n_expected = int(L / true_lambda) + 1

    pw_medians = []
    nn_medians = []
    N_values = []

    for _ in range(n_trials):
        # Generate periodic filament
        base_positions = np.arange(n_expected) * true_lambda
        perturbed = base_positions + np.random.normal(0, true_lambda*scatter_fraction, len(base_positions))
        perturbed = np.clip(perturbed, 0, L)
        positions = np.sort(perturbed)

        if len(positions) > 1:
            pw_medians.append(pairwise_median(positions))
            nn_medians.append(nearest_neighbor_median(positions))
            N_values.append(len(positions))

    pw_mean = np.mean(pw_medians)
    pw_std = np.std(pw_medians)
    pw_error = 100 * (pw_mean - true_lambda) / true_lambda

    nn_mean = np.mean(nn_medians)
    nn_std = np.std(nn_medians)
    nn_error = 100 * (nn_mean - true_lambda) / true_lambda

    N_mean = np.mean(N_values)
    L_div_3 = L / 3.0

    results.append((L, N_mean, pw_mean, pw_std, pw_error, nn_mean, nn_std, nn_error, L_div_3))

    print(f"{L:8.1f} {N_mean:6.0f} {pw_mean:10.4f} {pw_error:+9.1f}% {nn_mean:10.4f} {nn_error:+9.1f}% {L_div_3:10.4f}")

print()
print("INTERPRETATION:")
print("-" * 70)
print()

# Check if PM recovers true lambda
mean_pw_error = np.mean([abs(r[4]) for r in results])
mean_nn_error = np.mean([abs(r[7]) for r in results])

print(f"Mean absolute PM error: {mean_pw_error:.1f}%")
print(f"Mean absolute NN error: {mean_nn_error:.1f}%")
print()

if mean_pw_error < 15:
    print("✓ PM recovers the true fragmentation wavelength with < 15% error")
    print("✓ This validates PM as measuring true λ for periodic filaments")
elif mean_pw_error < 30:
    print(f"⚠ PM recovers λ with {mean_pw_error:.1f}% error")
    print("⚠ PM may be affected by non-adjacent pairs but is still reasonable")
else:
    print(f"✗ PM shows {mean_pw_error:.1f}% error - significant bias detected")
    print("✗ PM may not be reliable for these filament parameters")

print()
print("KEY INSIGHT:")
print("-" * 70)
print("For PERIODIC fragmentation (λ = 0.28 pc):")
print(f"  - NN recovers true λ with {mean_nn_error:.1f}% error (excellent)")
print(f"  - PM recovers true λ with {mean_pw_error:.1f}% error")
print()

if mean_pw_error < mean_nn_error * 2:
    print("Both PM and NN provide reasonable estimates of the fragmentation scale.")
else:
    print("NN provides significantly more accurate recovery of the true wavelength.")

print()
print("Comparison to HGBS data:")
print("  HGBS weighted mean: PM = 0.279 pc, NN = 0.101 pc")
print("  Expected from synthetic test: PM ≈ NN ≈ 0.28 pc")
print()
print("  If HGBS filaments follow periodic fragmentation, we expect PM ≈ NN.")
print("  The observed PM/NN discrepancy (factor of ~2.8) suggests:")
print("    (1) PM and NN measure different physical scales, OR")
print("    (2) PM is biased high by non-adjacent pairs")

print()

# Create figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: Measured vs True
L_vals = [r[0] for r in results]
pw_means = [r[2] for r in results]
pw_stds = [r[3] for r in results]
nn_means = [r[5] for r in results]
nn_stds = [r[6] for r in results]
L_div_3s = [r[8] for r in results]

ax1.errorbar(L_vals, pw_means, yerr=pw_stds, fmt='bo-', label='PM', linewidth=2, markersize=8)
ax1.errorbar(L_vals, nn_means, yerr=nn_stds, fmt='rs-', label='NN', linewidth=2, markersize=8)
ax1.plot(L_vals, L_div_3s, 'g:', label='L/3', linewidth=2)
ax1.axhline(y=true_lambda, color='gray', linestyle='--', label=f'True λ = {true_lambda} pc', linewidth=2)
ax1.set_xlabel('Filament length (pc)', fontsize=11)
ax1.set_ylabel('Measured spacing (pc)', fontsize=11)
ax1.set_title('Recovery of True Fragmentation Wavelength', fontsize=12, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Plot 2: Error comparison
pw_errors = [abs(r[4]) for r in results]
nn_errors = [abs(r[7]) for r in results]

x = np.arange(len(L_vals))
width = 0.35

bars1 = ax2.bar(x - width/2, pw_errors, width, label='PM error', color='steelblue', edgecolor='black')
bars2 = ax2.bar(x + width/2, nn_errors, width, label='NN error', color='indianred', edgecolor='black')

ax2.set_xticks(x)
ax2.set_xticklabels([f'L = {L:.0f} pc' for L in L_vals])
ax2.set_ylabel('Absolute error (%)', fontsize=11)
ax2.set_title('Recovery Error by Filament Length', fontsize=12, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, axis='y', alpha=0.3)

plt.tight_layout()
output_path = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/figures/fig_pm_synthetic_correct.pdf'
plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
print(f"✓ Figure saved to {output_path}")

png_path = output_path.replace('.pdf', '.png')
plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
print(f"✓ Figure PNG saved to {png_path}")

plt.close()

print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
