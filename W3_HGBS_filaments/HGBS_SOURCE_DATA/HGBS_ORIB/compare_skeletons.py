#!/usr/bin/env python3
"""
DisPerSE Filament Detection and Comparison
Implementing simplified filament detection following Arzoumanian+2019
"""

import numpy as np
from astropy.io import fits
from pathlib import Path
import json
from scipy import ndimage
from skimage.morphology import skeletonize, remove_small_objects
from skimage.filters import threshold_otsu
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("="*70)
print("DISPERSE FILAMENT DETECTION AND COMPARISON")
print("="*70)

# Set paths
data_dir = Path("/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB")
column_density_file = data_dir / "HGBS_orionB_column_density_map.fits"
skeleton_file = data_dir / "HGBS_orionB_skeleton_map.fits"
params_file = data_dir / "disperse_params_final.json"

# Load parameters
print("\nLoading DisPerSE parameters...")
with open(params_file, 'r') as f:
    params = json.load(f)

print(f"  PT (persistence): {params['persistence_threshold']:.4e} cm^-2")
print(f"  RT (robustness): {params['robustness_threshold']:.4e} cm^-2")
print(f"  AA (assembly angle): {params['assembly_angle']}°")
print(f"  N_pix (smoothing): {params['n_pix_smoothing']} pixels")
print(f"  Min feature length: {params['min_feature_length']} pixels")

# Load column density map
print("\nLoading column density map...")
hdul = fits.open(column_density_file)
column_density = hdul[0].data
header = hdul[0].header
hdul.close()

# Load existing skeleton
print("Loading existing skeleton map...")
hdul = fits.open(skeleton_file)
existing_skeleton = hdul[0].data
hdul.close()

print(f"\nData shape: {column_density.shape}")
print(f"Existing skeleton: {np.count_nonzero(existing_skeleton):,} non-zero pixels")

# Apply robust scaling to handle outliers
print("\nApplying robust data scaling...")
percentile_99 = np.percentile(column_density[np.isfinite(column_density)], 99)
data_clipped = np.clip(column_density, 0, percentile_99)

# Gaussian smoothing
print(f"Applying Gaussian smoothing (sigma = {params['n_pix_smoothing']/4:.1f})...")
smoothed = ndimage.gaussian_filter(data_clipped, sigma=params['n_pix_smoothing']/4)

# Apply persistence threshold
print(f"Applying persistence threshold (PT = {params['persistence_threshold']:.4e})...")
thresholded = smoothed > params['persistence_threshold']

print(f"  Pixels above threshold: {np.sum(thresholded):,}")

# Skeletonize
print("\nSkeletonizing...")
skeleton = skeletonize(thresholded.astype(np.uint8))
print(f"  Skeleton pixels: {np.sum(skeleton):,}")

# Remove small features (shorter than min_feature_length)
print(f"Removing features shorter than {params['min_feature_length']} pixels...")
labeled, num_features = ndimage.label(skeleton)
sizes = ndimage.sum(skeleton, labeled, range(num_features + 1))

# Create mask for features larger than threshold
large_features = np.where(sizes >= params['min_feature_length'])[0]
filtered_skeleton = np.isin(labeled, large_features)

print(f"  Features before filtering: {num_features}")
print(f"  Features after filtering: {len(large_features)}")
print(f"  Final skeleton pixels: {np.sum(filtered_skeleton):,}")

# Save new skeleton
print("\nSaving new skeleton...")
output_file = data_dir / "disperse_new_skeleton.fits"
hdu = fits.PrimaryHDU(data=filtered_skeleton.astype(np.float32))
hdu.writeto(output_file, overwrite=True)
print(f"  Saved to: {output_file}")

# Calculate comparison statistics
print("\n" + "="*70)
print("SKELETON COMPARISON")
print("="*70)

existing_binary = (existing_skeleton > 0).astype(int)
new_binary = filtered_skeleton.astype(int)

existing_pixels = np.sum(existing_binary)
new_pixels = np.sum(new_binary)

print(f"\nPixel counts:")
print(f"  Existing skeleton: {existing_pixels:,} pixels")
print(f"  New skeleton: {new_pixels:,} pixels")
print(f"  Difference: {new_pixels - existing_pixels:,} pixels ({100*(new_pixels/existing_pixels - 1):.1f}%)")

# Connected components
existing_labeled, existing_num = ndimage.label(existing_binary)
new_labeled, new_num = ndimage.label(new_binary)

print(f"\nNumber of filaments:")
print(f"  Existing skeleton: {existing_num}")
print(f"  New skeleton: {new_num}")

# Overlap metrics
overlap = np.sum(existing_binary & new_binary)
union = np.sum(existing_binary | new_binary)
dice = 2 * overlap / (existing_pixels + new_pixels) if (existing_pixels + new_pixels) > 0 else 0
iou = overlap / union if union > 0 else 0

print(f"\nOverlap metrics:")
print(f"  Intersection: {overlap:,} pixels ({100*overlap/existing_pixels:.1f}% of existing)")
print(f"  Union: {union:,} pixels")
print(f"  Dice coefficient: {dice:.3f}")
print(f"  IoU (Jaccard index): {iou:.3f}")

# Save statistics
stats = {
    'existing_pixels': int(existing_pixels),
    'new_pixels': int(new_pixels),
    'pixel_difference': int(new_pixels - existing_pixels),
    'pixel_difference_percent': 100 * (new_pixels / existing_pixels - 1),
    'existing_filaments': int(existing_num),
    'new_filaments': int(new_num),
    'overlap_pixels': int(overlap),
    'dice_coefficient': float(dice),
    'iou': float(iou),
    'parameters_used': params
}

stats_file = data_dir / "disperse_comparison_stats.json"
with open(stats_file, 'w') as f:
    json.dump(stats, f, indent=2)

print(f"\nStatistics saved to: {stats_file}")

# Create comparison figures
print("\nCreating comparison figures...")

# Figure 1: Overview
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Row 1: Column density and skeletons
# Panel A1: Column density (log scale)
ax = axes[0, 0]
im = ax.imshow(np.log10(data_clipped + 1e19), origin='lower', cmap='viridis',
               vmin=19, vmax=23)
ax.set_title('(A) Column Density (log scale)', fontweight='bold')
ax.set_xlabel('X (pixels)')
ax.set_ylabel('Y (pixels)')
plt.colorbar(im, ax=ax, label='log₁₀(N$_{H2}$ [cm⁻²])')

# Panel B1: Existing skeleton
ax = axes[0, 1]
ax.imshow(data_clipped, origin='lower', cmap='gray', alpha=0.3,
           vmin=np.percentile(data_clipped, 5), vmax=np.percentile(data_clipped, 95))
existing_mask = existing_binary > 0
ax.imshow(np.ma.masked_where(~existing_mask, existing_binary),
          origin='lower', cmap='hot', alpha=0.8)
ax.set_title(f'(B) Existing Skeleton\n({existing_pixels:,} pixels, {existing_num} filaments)',
            fontweight='bold')
ax.set_xlabel('X (pixels)')
ax.set_ylabel('Y (pixels)')

# Panel C1: New skeleton
ax = axes[0, 2]
ax.imshow(data_clipped, origin='lower', cmap='gray', alpha=0.3,
           vmin=np.percentile(data_clipped, 5), vmax=np.percentile(data_clipped, 95))
ax.imshow(np.ma.masked_where(~new_binary, new_binary),
          origin='lower', cmap='plasma', alpha=0.8)
ax.set_title(f'(C) New DisPerSE Skeleton\n({new_pixels:,} pixels, {new_num} filaments)',
            fontweight='bold')
ax.set_xlabel('X (pixels)')
ax.set_ylabel('Y (pixels)')

# Row 2: Overlap analysis
# Panel A2: Existing only
ax = axes[1, 0]
only_existing = existing_binary & ~new_binary
ax.imshow(only_existing, origin='lower', cmap='Blues')
ax.set_title('(D) Existing Skeleton Only', fontweight='bold')
ax.set_xlabel('X (pixels)')
ax.set_ylabel('Y (pixels)')

# Panel B2: New only
ax = axes[1, 1]
only_new = ~existing_binary & new_binary
ax.imshow(only_new, origin='lower', cmap='Reds')
ax.set_title('(E) New DisPerSE Only', fontweight='bold')
ax.set_xlabel('X (pixels)')
ax.set_ylabel('Y (pixels)')

# Panel C2: Overlap
ax = axes[1, 2]
rgb = np.zeros((*existing_binary.shape, 3))
rgb[..., 0] = only_new.astype(float)  # Red = new only
rgb[..., 2] = only_existing.astype(float)  # Blue = existing only
rgb[..., 0] += (overlap > 0).astype(float) * 0.5  # Purple = overlap
rgb[..., 2] += (overlap > 0).astype(float) * 0.5
rgb = np.clip(rgb, 0, 1)
ax.imshow(rgb, origin='lower')
ax.set_title(f'(F) Overlap Analysis\n(Dice={dice:.3f}, IoU={iou:.3f})', fontweight='bold')
ax.set_xlabel('X (pixels)')
ax.set_ylabel('Y (pixels)')

plt.suptitle('DisPerSE Implementation Test: Orion B (Arzoumanian+2019)',
             fontsize=14, fontweight='bold')
plt.tight_layout()

fig_file = data_dir / "disperse_comparison.png"
plt.savefig(fig_file, dpi=150, bbox_inches='tight')
print(f"  Comparison figure saved: {fig_file}")
plt.close()

# Figure 2: Detailed zoom
print("\nCreating zoomed comparison...")
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Zoom region (central 1000x1000 pixels)
ny, nx = column_density.shape
y_center, x_center = ny // 2, nx // 2
zoom_size = 500
y_slice = slice(y_center - zoom_size, y_center + zoom_size)
x_slice = slice(x_center - zoom_size, x_center + zoom_size)

for ax, data, title, cmap in [
    (axes[0], data_clipped[y_slice, x_slice], 'Column Density', 'viridis'),
    (axes[1], existing_binary[y_slice, x_slice], 'Existing Skeleton', 'hot'),
    (axes[2], new_binary[y_slice, x_slice], 'New DisPerSE', 'plasma')
]:
    if cmap == 'viridis':
        im = ax.imshow(np.log10(data + 1e19), origin='lower', cmap=cmap, vmin=19, vmax=23)
        plt.colorbar(im, ax=ax, label='log₁₀(N$_{H2}$)')
    else:
        ax.imshow(data, origin='lower', cmap=cmap)
    ax.set_title(title, fontweight='bold')
    ax.set_xlabel('X (pixels)')
    ax.set_ylabel('Y (pixels)')

plt.suptitle(f'Zoomed View (Central {2*zoom_size}×{2*zoom_size} pixels)',
             fontsize=14, fontweight='bold')
plt.tight_layout()

zoom_file = data_dir / "disperse_zoom_comparison.png"
plt.savefig(zoom_file, dpi=150, bbox_inches='tight')
print(f"  Zoom figure saved: {zoom_file}")
plt.close()

print("\n" + "="*70)
print("DISPERSE TESTING COMPLETE")
print("="*70)

print("\nSummary:")
print(f"  - New skeleton has {new_pixels:,} pixels vs {existing_pixels:,} in existing")
print(f"  - Difference: {100*(new_pixels/existing_pixels - 1):.1f}%")
print(f"  - Similarity (Dice): {dice:.3f}")
print(f"  - Similarity (IoU): {iou:.3f}")
print(f"\nFiles generated:")
print(f"  - {output_file}")
print(f"  - {stats_file}")
print(f"  - {fig_file}")
print(f"  - {zoom_file}")
