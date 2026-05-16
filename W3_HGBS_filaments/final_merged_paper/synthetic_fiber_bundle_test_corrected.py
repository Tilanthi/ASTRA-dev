#!/usr/bin/env python3
"""
Synthetic Fiber Bundle Test: Critical Missing Validation (Corrected)

The referee correctly identified that we only tested simple periodic filaments,
but we claim HGBS filaments are hierarchical fiber bundles. This test creates
synthetic fiber bundles and tests whether PM or NN recovers the fiber-level spacing.

Key insight: For HGBS-like parameters, we need fibers that overlap spatially
within the same filament extent, not extending to different positions.

Author: G. J. White
Date: 2026-05-02
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman']
rcParams['font.size'] = 10

print("=" * 80)
print("SYNTHETIC FIBER BUNDLE TEST: Critical Missing Validation")
print("=" * 80)
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

def generate_fiber_bundle_v2(n_fibers, filament_length, lambda_fiber,
                             velocity_spread, scatter=0.0):
    """
    Generate a synthetic fiber bundle filament with CORRECT geometry.

    Key insight: Fibers should overlap spatially within the same filament extent,
    separated by small velocity offsets. They should NOT extend to different positions.

    Parameters:
    -----------
    n_fibers : int
        Number of fibers in the bundle
    filament_length : float
        Length of the overall filament (pc)
    lambda_fiber : float
        True fragmentation wavelength for individual fibers (pc)
    velocity_spread : float
        Spread of fiber centers in "velocity space" (pc) - this translates to
        positional offset along the filament
    scatter : float
        Positional scatter (pc)

    Returns:
    --------
    all_positions : ndarray
        All core positions mixed together
    """
    all_positions = []

    for fiber_id in range(n_fibers):
        # Calculate the center position of this fiber
        fiber_center = fiber_id * velocity_spread

        # Generate fragmentation positions along this fiber
        # Start from the fiber center and extend in both directions
        n_expected = int(filament_length / lambda_fiber) + 1
        positions = np.arange(n_expected) * lambda_fiber

        # Center the positions on the fiber center
        positions = positions - positions[len(positions)//2]
        positions = positions + fiber_center

        # Add scatter
        if scatter > 0:
            positions = positions + np.random.normal(0, scatter, len(positions))

        # Clip to filament extent
        positions = np.clip(positions, 0, filament_length)

        all_positions.extend(positions)

    all_positions = np.sort(all_positions)
    return all_positions

# Test parameters - HGBS-like
L_filament = 10.0  # pc (typical HGBS filament length)
lambda_fiber = 0.28  # pc (fiber-level fragmentation, λ/W ≈ 3 for W = 0.1 pc)
velocity_spread = 0.15  # pc (spread between fiber centers)
scatter = 0.04  # pc (~15% of lambda)
n_trials = 1000

print("Test Parameters (HGBS-like):")
print(f"  Filament length: {L_filament} pc")
print(f"  Fiber-level λ: {lambda_fiber} pc (λ/W ≈ 3 for W = 0.1 pc)")
print(f"  Velocity spread: {velocity_spread} pc (spacing between fiber centers)")
print(f"  Positional scatter: {scatter} pc")
print(f"  Trials: {n_trials}")
print()

print("=" * 80)
print("RESULTS: Synthetic Fiber Bundle Validation")
print("=" * 80)
print()

# Test different numbers of fibers
n_fibers_list = [1, 2, 3, 4, 5]

results = []

for n_fibers in n_fibers_list:
    pw_medians = []
    nn_medians = []

    for trial in range(n_trials):
        # Generate fiber bundle with correct geometry
        all_positions = generate_fiber_bundle_v2(
            n_fibers=n_fibers,
            filament_length=L_filament,
            lambda_fiber=lambda_fiber,
            velocity_spread=velocity_spread,
            scatter=scatter
        )

        if len(all_positions) > 1:
            pw_medians.append(pairwise_median(all_positions))
            nn_medians.append(nearest_neighbor_median(all_positions))

    pw_mean = np.mean(pw_medians)
    pw_std = np.std(pw_medians)
    nn_mean = np.mean(nn_medians)
    nn_std = np.std(nn_medians)

    # L/3 for comparison
    L_div_3 = L_filament / 3.0

    results.append({
        'n_fibers': n_fibers,
        'pw_mean': pw_mean,
        'pw_std': pw_std,
        'nn_mean': nn_mean,
        'nn_std': nn_std,
        'L_div_3': L_div_3,
    })

    print(f"N_fibers = {n_fibers}:")
    print(f"  PM: {pw_mean:.4f} ± {pw_std:.4f} pc")
    print(f"  NN: {nn_mean:.4f} ± {nn_std:.4f} pc")
    print(f"  True λ_fiber: {lambda_fiber:.4f} pc")
    print(f"  L/3: {L_div_3:.4f} pc")

    # Recovery analysis
    pw_error = 100 * abs(pw_mean - lambda_fiber) / lambda_fiber
    nn_error = 100 * abs(nn_mean - lambda_fiber) / lambda_fiber

    print(f"  PM recovery error: {pw_error:.1f}%")
    print(f"  NN recovery error: {nn_error:.1f}%")

    # Interpretation
    if abs(pw_mean - lambda_fiber) < 0.1:
        pm_interpretation = "✓ PM recovers λ_fiber"
    elif pw_mean > L_div_3 * 0.8:
        pm_interpretation = "✗ PM → L/3 (biased high)"
    else:
        pm_interpretation = "? PM measures intermediate scale"

    if abs(nn_mean - lambda_fiber) < 0.1:
        nn_interpretation = "✓ NN recovers λ_fiber"
    elif nn_mean < lambda_fiber * 0.5:
        nn_interpretation = "✗ NN compressed (<0.5×λ_fiber)"
    else:
        nn_interpretation = "? NN biased"

    print(f"  PM: {pm_interpretation}")
    print(f"  NN: {nn_interpretation}")
    print()

print("=" * 80)
print("COMPARISON TO HGBS OBSERVATIONS")
print("=" * 80)
print()

print("HGBS observations:")
print("  PM = 0.279 pc")
print("  NN = 0.101 pc")
print("  True λ_fiber (from Smith+2016): ≈ 0.25 pc")
print()

print("Synthetic test results (λ_fiber = 0.28 pc):")
for r in results:
    n_fibers = r['n_fibers']
    pw = r['pw_mean']
    nn = r['nn_mean']
    ratio = nn / pw if pw > 0 else 0

    print(f"  N_fibers = {n_fibers}: PM = {pw:.4f} pc, NN = {nn:.4f} pc, NN/PM = {ratio:.3f}")

print()

print("=" * 80)
print("KEY FINDINGS")
print("=" * 80)
print()

# Find closest match
for r in results:
    diff = abs(r['pw'] - 0.279)
    if diff < 1.0:  # Within 1 pc
        n_fibers = r['n_fibers']
        pw = r['pw_mean']
        nn = r['nn_mean']
        ratio = nn / pw

        print(f"Closest synthetic match to HGBS PM (0.279 pc): N_fibers = {n_fibers}")
        print(f"  Synthetic PM = {pw:.4f} pc")
        print(f"  Synthetic NN = {nn:.4f} pc")
        print(f"  Synthetic NN/PM = {ratio:.3f}")
        print()

        # Check if match
        if abs(ratio - 0.36) < 0.1:
            print("✓ NN/PM ratio matches HGBS (0.36)!")
        else:
            print(f"✗ NN/PM ratio differs: {ratio:.3f} vs 0.36")

        # Check PM
        if abs(pw - 0.279) < 0.05:
            print("✓ PM value matches HGBS!")
        else:
            print(f"✗ PM value differs: {pw:.4f} vs 0.279")

        print()
        break

print("=" * 80)
print("INTERPRETATION")
print("=" * 80)
print()

print("Critical analysis of results:")
print()

# Check single fiber case
single_fiber = results[0]
if single_fiber['pw_mean'] > single_fiber['L_div_3'] * 0.8:
    print("1. SINGLE FIBER (N_fibers = 1):")
    print("   ✓ PM → L/3 (as expected for simple periodic filaments)")
    print()

# Check fiber bundle cases
fiber_bundles = results[1:]
nn_recovers = sum([1 for r in fiber_bundles if abs(r['nn_mean'] - lambda_fiber) < 0.05])
total_bundles = len(fiber_bundles)

print(f"2. FIBER BUNDLES (N_fibers = 2-5):")
print(f"   NN recovers λ_fiber in {nn_recovers}/{total_bundles} cases")
print()

# Check PM behavior
pm_recovers = sum([1 for r in results if abs(r['pw_mean'] - lambda_fiber) < 0.1])
print(f"   PM recovers λ_fiber in {pm_recovers}/{len(results)} cases")
print()

print("=" * 80)
print("RECOMMENDATION FOR PAPER")
print("=" * 80)
print()

print("Add Section 3.3: 'Synthetic Fiber Bundle Validation Test'")
print()
print("Key findings to report:")
print()

# Based on what the test shows
if results[0]['pw_mean'] > results[0]['L_div_3'] * 0.8:
    print("1. For single fibers: PM → L/3, NN → λ_fiber (as expected)")

pm_matches = any([abs(r['pw_mean'] - lambda_fiber) < 0.1 for r in results])
nn_matches = any([abs(r['nn_mean'] - lambda_fiber) < 0.1 for r in results])

if pm_matches:
    print("2. For fiber bundles: PM recovers λ_fiber")
else:
    print("2. For fiber bundles: PM does NOT recover λ_fiber")

if nn_matches:
    print("3. For fiber bundles: NN recovers λ_fiber")
else:
    print("3. For fiber bundles: NN does NOT recover λ_fiber")

print()
print("4. HGBS observations (PM = 0.279 pc) are most consistent with")
print("   [analyze based on results]")
print()

print("This provides the quantitative demonstration the referee requested.")
print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)

# Create figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: PM and NN vs N_fibers
n_fibers_vals = [r['n_fibers'] for r in results]
pw_means = [r['pw_mean'] for r in results]
pw_stds = [r['pw_std'] for r in results]
nn_means = [r['nn_mean'] for r in results]
nn_stds = [r['nn_std'] for r in results]

ax1.errorbar(n_fibers_vals, pw_means, yerr=pw_stds, fmt='bo-', label='PM',
             linewidth=2, markersize=8, capsize=5)
ax1.errorbar(n_fibers_vals, nn_means, yerr=nn_stds, fmt='rs-', label='NN',
             linewidth=2, markersize=8, capsize=5)
ax1.axhline(y=lambda_fiber, color='gray', linestyle='--', label=f'True λ_fiber ({lambda_fiber} pc)',
             linewidth=2)
ax1.axhline(y=L_filament/3, color='orange', linestyle=':', label=f'L/3 ({L_filament/3:.2f} pc)',
             linewidth=2)
ax1.axhline(y=0.279, color='blue', linestyle='-.', label='HGBS PM (0.279 pc)', linewidth=2)
ax1.set_xlabel('Number of fibers in bundle', fontsize=12)
ax1.set_ylabel('Spacing (pc)', fontsize=12)
ax1.set_title('Synthetic Fiber Bundle Validation Test', fontsize=13, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# Plot 2: NN/PM ratio vs N_fibers
ratios = [r['nn_mean'] / r['pw_mean'] if r['pw_mean'] > 0 else 0 for r in results]

ax2.plot(n_fibers_vals, ratios, 'go-', linewidth=2, markersize=8)
ax2.axhline(y=0.36, color='blue', linestyle='--', label='HGBS NN/PM = 0.36',
             linewidth=2)
ax2.set_xlabel('Number of fibers in bundle', fontsize=12)
ax2.set_ylabel('NN/PM ratio', fontsize=12)
ax2.set_title('NN/PM Ratio vs. Fiber Bundle Complexity', fontsize=13, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
# ax2.set_ylim(0, max(ratios) * 1.1)

plt.tight_layout()
output_path = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/figures/fig_fiber_bundle_validation_v2.pdf'
plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
print(f"✓ Figure saved to {output_path}")

png_path = output_path.replace('.pdf', '.png')
plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
print(f"✓ Figure PNG saved to {png_path}")

plt.close()
