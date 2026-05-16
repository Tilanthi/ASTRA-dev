#!/usr/bin/env python3
"""
Synthetic Fiber Bundle Test: Parameter Exploration to Match HGBS

Goal: Find fiber bundle parameters that reproduce HGBS observations (PM = 0.279 pc, NN = 0.101 pc)
This will help us understand whether HGBS filaments could be fiber bundles.
"""

import numpy as np

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
    if len(sorted_pos) <= 1:
        return 0
    nn_distances = np.diff(sorted_pos)
    return np.median(nn_distances)

def generate_fiber_bundle(n_fibers, filament_length, lambda_fiber,
                             fiber_offset, scatter=0.0, n_cores_range=(5, 12)):
    """Generate synthetic fiber bundle."""
    all_positions = []

    for fiber_id in range(n_fibers):
        fiber_center = fiber_id * fiber_offset

        # Generate fragmentation positions
        n_expected = int(filament_length / lambda_fiber) + 1
        positions = np.arange(n_expected) * lambda_fiber

        # Center on fiber center
        positions = positions - positions[len(positions)//2] + fiber_center

        # Add scatter
        if scatter > 0:
            positions = positions + np.random.normal(0, scatter, len(positions))

        # Clip to filament extent
        positions = np.clip(positions, 0, filament_length)

        # Subsample to random number of cores
        n_cores = np.random.randint(*n_cores_range)
        if len(positions) > n_cores:
            indices = np.random.choice(len(positions), n_cores, replace=False)
            positions = np.sort(positions[indices])

        all_positions.extend(positions)

    all_positions = np.sort(all_positions)
    return all_positions

# HGBS target values
target_pm = 0.279
target_nn = 0.101
target_ratio = 0.36

print("=" * 80)
print("PARAMETER EXPLORATION: Match HGBS Observations")
print("=" * 80)
print()

print("Target HGBS values:")
print(f"  PM = {target_pm} pc")
print(f"  NN = {target_nn} pc")
print(f"  NN/PM = {target_ratio:.3f}")
print()

# Fixed parameters
L_filament = 10.0
lambda_fiber = 0.28
scatter = 0.04
n_trials = 500

# Parameter grid
n_fibers_list = [2, 3, 4, 5]
fiber_offset_list = [0.10, 0.15, 0.20, 0.25, 0.30]

print("Searching parameter space...")
print()

best_matches = []

for n_fibers in n_fibers_list:
    for fiber_offset in fiber_offset_list:
        pw_means = []
        nn_means = []

        for trial in range(n_trials):
            positions = generate_fiber_bundle(
                n_fibers=n_fibers,
                filament_length=L_filament,
                lambda_fiber=lambda_fiber,
                fiber_offset=fiber_offset,
                scatter=scatter
            )

            if len(positions) > 1:
                pw_means.append(pairwise_median(positions))
                nn_means.append(nearest_neighbor_median(positions))

        if pw_means and nn_means:
            pw_mean = np.mean(pw_means)
            nn_mean = np.mean(nn_means)
            ratio = nn_mean / pw_mean

            # Check match quality
            pm_diff = abs(pw_mean - target_pm)
            nn_diff = abs(nn_mean - target_nn)
            ratio_diff = abs(ratio - target_ratio)

            # Combined score
            score = pm_diff + nn_diff + ratio_diff * 0.1

            if score < 0.15:  # Within tolerance
                best_matches.append({
                    'n_fibers': n_fibers,
                    'fiber_offset': fiber_offset,
                    'pm': pw_mean,
                    'nn': nn_mean,
                    'ratio': ratio,
                    'score': score
                })

print("=" * 80)
print("BEST MATCHES")
print("=" * 80)
print()

# Sort by score and show top 10
best_matches.sort(key=lambda x: x['score'])

for i, match in enumerate(best_matches[:10]):
    print(f"Rank {i+1}:")
    print(f"  N_fibers = {match['n_fibers']}")
    print(f"  Fiber offset = {match['fiber_offset']:.3f} pc")
    print(f"  PM = {match['pm']:.4f} pc (target: {target_pm:.4f} pc)")
    print(f"  NN = {match['nn']:.4f} pc (target: {target_nn:.4f} pc)")
    print(f"  NN/PM = {match['ratio']:.3f} (target: {target_ratio:.3f})")
    print(f"  Score = {match['score']:.4f}")
    print()

print("=" * 80)
print("KEY FINDING")
print("=" * 80)
print()

if best_matches:
    best = best_matches[0]
    print(f"Closest match found:")
    print(f"  N_fibers = {best['n_fibers']}")
    print(f"  Fiber offset = {best['fiber_offset']:.3f} pc")
    print(f"  PM = {best['pm']:.4f} pc (target: {target_pm:.4f} pc, error: {abs(best['pm']-target_pm):.4f} pc)")
    print(f"  NN = {best['nn']:.4f} pc (target: {target_nn:.4f} pc, error: {abs(best['nn']-target_nn):.4f} pc)")
    print()

    # Interpretation
    print("Interpretation:")
    print(f"  ✓ A fiber bundle with {best['n_fibers']} fibers and {best['fiber_offset']:.3f} pc")
    print(f"    offset between fibers reproduces HGBS PM/NN observations.")
    print()
    print("  This suggests HGBS filaments could be fiber bundles with:")
    print(f"    - {best['n_fibers']} velocity-coherent fibers")
    print(f"    - Fiber centers separated by ~{best['fiber_offset']*100:.0f} cm")
    print(f"    - Each fiber fragmenting at λ ≈ {lambda_fiber} pc")
else:
    print("✗ No good matches found in parameter space.")
    print("  HGBS observations may not be explained by simple fiber bundle model.")

print()
print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print()

print("1. Add this quantitative analysis to Section 3.3")
print("2. Report whether synthetic fiber bundles can reproduce HGBS observations")
print("3. If yes: This supports fiber bundle hypothesis")
print("4. If no: This challenges fiber bundle hypothesis")
print()
print("=" * 80)
