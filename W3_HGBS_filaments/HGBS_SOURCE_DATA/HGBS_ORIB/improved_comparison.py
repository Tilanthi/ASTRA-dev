#!/usr/bin/env python3
"""
Improved DisPerSE Skeleton Comparison
Analyzing the existing skeleton with different persistence thresholds
"""

import numpy as np
from astropy.io import fits
from pathlib import Path
import json
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("="*70)
print("IMPROVED SKELETON COMPARISON WITH PERSISTENCE THRESHOLDS")
print("="*70)

# Set paths
data_dir = Path("/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB")
column_density_file = data_dir / "HGBS_orionB_column_density_map.fits"
skeleton_file = data_dir / "HGBS_orionB_skeleton_map.fits"
params_file = data_dir / "disperse_params_final.json"

# Load data
print("\nLoading data...")
hdul = fits.open(column_density_file)
column_density = hdul[0].data
header = hdul[0].header
hdul.close()

hdul = fits.open(skeleton_file)
existing_skeleton = hdul[0].data
hdul.close()

with open(params_file, 'r') as f:
    params = json.load(f)

print(f"Column density shape: {column_density.shape}")
print(f"Existing skeleton shape: {existing_skeleton.shape}")

# Analyze existing skeleton persistence values
print("\n" + "="*70)
print("EXISTING SKELETON PERSISTENCE ANALYSIS")
print("="*70)

# Get non-zero persistence values
persistence_values = existing_skeleton[existing_skeleton > 0]

print(f"\nPersistence value statistics:")
print(f"  Min: {np.min(persistence_values):.1f}")
print(f"  Max: {np.max(persistence_values):.1f}")
print(f"  Median: {np.median(persistence_values):.1f}")
print(f"  Mean: {np.mean(persistence_values):.1f}")
print(f"  Std: {np.std(persistence_values):.1f}")

# Percentiles
percentiles = [10, 25, 50, 75, 90, 95, 99]
print(f"\nPersistence percentiles:")
for p in percentiles:
    val = np.percentile(persistence_values, p)
    count = np.sum(existing_skeleton >= val)
    print(f"  {p}th percentile: {val:.1f} ({count:,} pixels)")

# Test different persistence thresholds
print("\n" + "="*70)
print("TESTING DIFFERENT PERSISTENCE THRESHOLDS")
print("="*70)

thresholds_to_test = [1, 5, 10, 20, 50, 100, 150]

results = []
for threshold in thresholds_to_test:
    mask = existing_skeleton >= threshold
    pixel_count = int(np.sum(mask))
    labeled, num_features = ndimage.label(mask)

    results.append({
        'threshold': int(threshold),
        'pixels': pixel_count,
        'features': int(num_features)
    })

    print(f"\nThreshold >= {threshold}:")
    print(f"  Pixels: {pixel_count:,}")
    print(f"  Features: {num_features}")

# Find threshold that gives reasonable number of features
print("\n" + "="*70)
print("ANALYSIS")
print("="*70)

# Calculate our calculated PT in terms of persistence
# Our PT is in column density units, need to see what persistence level this corresponds to
pt_density = params['persistence_threshold']
print(f"\nOur calculated PT (density): {pt_density:.4e} cm^-2")
print(f"Our calculated RT (density): {params['robustness_threshold']:.4e} cm^-2")

# The existing skeleton uses arbitrary persistence units
# Let's find what threshold gives similar results to typical filament papers
# Usually, papers use thresholds that result in ~100-1000 major filaments

print("\nRecommended persistence thresholds based on feature count:")
for r in results:
    if 50 <= r['features'] <= 500:
        print(f"  Persistence >= {r['threshold']}: {r['features']} filaments ({r['pixels']:,} pixels)")

# Create comparison figure with different thresholds
print("\nCreating comparison figure with different thresholds...")

fig, axes = plt.subplots(2, 4, figsize=(20, 10))

# Row 1: Column density + persistence thresholds
thresholds_display = [1, 10, 50, 100]

for i, thresh in enumerate(thresholds_display):
    ax = axes[0, i]
    mask = existing_skeleton >= thresh

    # Show column density as background
    ax.imshow(np.log10(column_density + 1e19), origin='lower',
              cmap='gray', alpha=0.5, vmin=19, vmax=23)

    # Overlay skeleton
    ax.imshow(np.ma.masked_where(~mask, existing_skeleton),
              origin='lower', cmap='hot', alpha=0.7)

    labeled, num = ndimage.label(mask)
    pixels = np.sum(mask)

    ax.set_title(f'Persistence >= {thresh}\n({num} filaments, {pixels:,} px)',
                fontweight='bold')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')

# Row 2: Persistence histogram and threshold effects
ax = axes[1, 0]
ax.hist(persistence_values, bins=100, log=True, color='steelblue', edgecolor='black')
ax.axvline(10, color='r', linestyle='--', label='>= 10')
ax.axvline(50, color='g', linestyle='--', label='>= 50')
ax.axvline(100, color='orange', linestyle='--', label='>= 100')
ax.set_xlabel('Persistence Value')
ax.set_ylabel('Number of Pixels (log scale)')
ax.set_title('Persistence Distribution', fontweight='bold')
ax.legend()
ax.set_yscale('log')

# Feature count vs threshold
ax = axes[1, 1]
thresholds_plot = [r['threshold'] for r in results]
features_plot = [r['features'] for r in results]
ax.plot(thresholds_plot, features_plot, 'o-', color='steelblue', linewidth=2, markersize=8)
ax.set_xlabel('Persistence Threshold')
ax.set_ylabel('Number of Filaments')
ax.set_title('Filament Count vs Threshold', fontweight='bold')
ax.set_xscale('log')
ax.set_yscale('log')
ax.grid(True, alpha=0.3)

# Pixel count vs threshold
ax = axes[1, 2]
pixels_plot = [r['pixels'] for r in results]
ax.plot(thresholds_plot, pixels_plot, 'o-', color='darkgreen', linewidth=2, markersize=8)
ax.set_xlabel('Persistence Threshold')
ax.set_ylabel('Number of Pixels')
ax.set_title('Skeleton Pixels vs Threshold', fontweight='bold')
ax.set_xscale('log')
ax.set_yscale('log')
ax.grid(True, alpha=0.3)

# Cumulative distribution
ax = axes[1, 3]
sorted_vals = np.sort(persistence_values)[::-1]
cumsum = np.cumsum(sorted_vals)
cumsum_pct = 100 * cumsum / cumsum[-1]

ax.plot(np.arange(len(cumsum_pct)), cumsum_pct, color='purple', linewidth=2)
ax.axhline(80, color='r', linestyle='--', alpha=0.5, label='80% of pixels')
ax.axhline(50, color='g', linestyle='--', alpha=0.5, label='50% of pixels')
ax.set_xlabel('Number of Pixels (ranked by persistence)')
ax.set_ylabel('Cumulative Percentage (%)')
ax.set_title('Cumulative Persistence Distribution', fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

plt.suptitle('DisPerSE Skeleton Analysis: Orion B\nArzoumanian+2019 Parameters',
             fontsize=14, fontweight='bold')
plt.tight_layout()

fig_file = data_dir / "disperse_persistence_analysis.png"
plt.savefig(fig_file, dpi=150, bbox_inches='tight')
print(f"  Saved: {fig_file}")
plt.close()

# Create detailed comparison with specific threshold
print("\nCreating detailed comparison with recommended threshold...")

# Use threshold that gives ~500-1000 filaments
recommended_threshold = 20  # Based on analysis

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Panel 1: Column density
ax = axes[0]
im = ax.imshow(np.log10(column_density + 1e19), origin='lower',
               cmap='viridis', vmin=19, vmax=23)
ax.set_title('Column Density (log scale)', fontweight='bold')
ax.set_xlabel('X (pixels)')
ax.set_ylabel('Y (pixels)')
plt.colorbar(im, ax=ax, label='log₁₀(N$_{H2}$)')

# Panel 2: Existing skeleton with threshold
ax = axes[1]
mask_thresh = existing_skeleton >= recommended_threshold
labeled, num_features = ndimage.label(mask_thresh)

ax.imshow(column_density, origin='lower', cmap='gray', alpha=0.3)
ax.imshow(np.ma.masked_where(~mask_thresh, existing_skeleton),
          origin='lower', cmap='hot', alpha=0.7)
ax.set_title(f'Existing Skeleton\n(Persistence >= {recommended_threshold})\n{num_features} filaments',
            fontweight='bold')
ax.set_xlabel('X (pixels)')
ax.set_ylabel('Y (pixels)')

# Panel 3: Persistence map
ax = axes[2]
im = ax.imshow(existing_skeleton, origin='lower', cmap='magma',
               vmin=0, vmax=np.percentile(persistence_values, 95))
ax.set_title('Persistence Map', fontweight='bold')
ax.set_xlabel('X (pixels)')
ax.set_ylabel('Y (pixels)')
plt.colorbar(im, ax=ax, label='Persistence')

plt.suptitle(f'DisPerSE Skeleton with Threshold = {recommended_threshold}',
             fontsize=14, fontweight='bold')
plt.tight_layout()

detail_file = data_dir / "disperse_threshold_detail.png"
plt.savefig(detail_file, dpi=150, bbox_inches='tight')
print(f"  Saved: {detail_file}")
plt.close()

# Save analysis results
analysis_results = {
    'persistence_statistics': {
        'min': float(np.min(persistence_values)),
        'max': float(np.max(persistence_values)),
        'median': float(np.median(persistence_values)),
        'mean': float(np.mean(persistence_values)),
        'std': float(np.std(persistence_values)),
        'percentiles': {str(p): float(np.percentile(persistence_values, p)) for p in percentiles}
    },
    'threshold_analysis': results,
    'recommended_threshold': int(recommended_threshold),
    'calculated_parameters': params
}

results_file = data_dir / "disperse_persistence_analysis.json"
with open(results_file, 'w') as f:
    json.dump(analysis_results, f, indent=2)

print(f"\nAnalysis results saved: {results_file}")

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)

print("\nKey Findings:")
print(f"  - Existing skeleton has persistence values from {np.min(persistence_values):.0f} to {np.max(persistence_values):.0f}")
print(f"  - Lower thresholds (>= 1) include many features: {results[0]['features']:,} filaments")
print(f"  - Higher thresholds (>= 100) select only major features: {results[5]['features']} filaments")
print(f"  - Recommended threshold for filament analysis: persistence >= {recommended_threshold}")
print(f"\nNote: The existing skeleton map contains persistence-weighted filament structures.")
print(f"      Lower persistence thresholds include fainter/smaller filaments.")
print(f"      Higher thresholds select only the most robust/long filaments.")
