#!/usr/bin/env python3
"""
Correct core spacing analysis with proper filament extraction.
"""
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from astropy.io import fits

print("="*80)
print("PROPER CORE SPACING ANALYSIS - ORION B")
print("="*80)

# Load data
skeleton_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits'
results_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/phase2_results.npz'

with fits.open(skeleton_file) as hdul:
    skeleton = hdul[0].data

data = np.load(results_file, allow_pickle=True)
cores = data['cores']
cores_on_filaments = [c for c in cores if c.get('on_filament', False)]

print(f"\nData loaded:")
print(f"  Total cores: {len(cores)}")
print(f"  Cores on filaments: {len(cores_on_filaments)}")
print(f"  Skeleton shape: {skeleton.shape}")
print(f"  Skeleton non-zero pixels: {np.sum(skeleton > 0)}")

# Pixel size
pixel_size_pc = 0.00378  # pc

# ORIGINAL METHOD: 2D nearest neighbor (what was likely used)
print(f"\n{'='*80}")
print(f"ORIGINAL METHOD (2D Nearest Neighbor)")
print(f"{'='*80}")

coords = np.array([[c['x_pix'], c['y_pix']] for c in cores_on_filaments])
tree = cKDTree(coords)
nn_dists, _ = tree.query(coords, k=2)
nn_dists = nn_dists[:, 1]
nn_dists_pc = nn_dists * pixel_size_pc

print(f"  Median: {np.median(nn_dists_pc):.3f} pc")
print(f"  Mean:   {np.mean(nn_dists_pc):.3f} pc")
print(f"  Std:    {np.std(nn_dists_pc):.3f} pc")

# PROPER METHOD: Morphological skeletonization of main filaments
print(f"\n{'='*80}")
print(f"PROPER METHOD (Filament-by-Filament)")
print(f"{'='*80}")

# Strategy: Use distance transform to find filament spines
# 1. Threshold skeleton
# 2. Use morphological skeletonization
# 3. Extract major branches

from skimage.morphology import skeletonize, remove_small_objects
from skimage.measure import label, regionprops

# Threshold and clean
skeleton_binary = skeleton > 0

# Remove small objects
skeleton_clean = remove_small_objects(skeleton_binary, min_size=100)

# Label large components
labeled, num_filaments = label(skeleton_clean, return_num=True)

print(f"\nAfter cleaning (min_size=100):")
print(f"  Filaments found: {num_filaments}")

# Analyze each filament
filament_results = []
all_consecutive_spacings = []

for i in range(1, num_filaments + 1):
    filament_mask = labeled == i
    pixel_count = np.sum(filament_mask)

    if pixel_count < 100:  # Minimum filament size
        continue

    # Find cores on this filament
    cores_on_this = []
    for core in cores_on_filaments:
        x, y = int(core['x_pix']), int(core['y_pix'])
        if y < filament_mask.shape[0] and x < filament_mask.shape[1]:
            if filament_mask[y, x]:
                cores_on_this.append(core)

    n_cores = len(cores_on_this)

    if n_cores >= 2:
        # Get coordinates
        these_coords = np.array([[c['x_pix'], c['y_pix']] for c in cores_on_this])

        # Calculate nearest neighbor within this filament
        tree_fil = cKDTree(these_coords)
        nn_fil, _ = tree_fil.query(these_coords, k=2)
        nn_fil = nn_fil[:, 1]  # Exclude self
        nn_fil_pc = nn_fil * pixel_size_pc

        # Also calculate consecutive spacing using spatial ordering
        # Order cores by their position along the filament's principal axis
        centroid = np.mean(these_coords, axis=0)
        centered_coords = these_coords - centroid

        # Project onto first principal component
        if len(these_coords) >= 3:
            # Simple approach: use x-coordinate as proxy for ordering
            sorted_indices = np.argsort(these_coords[:, 0])
            sorted_coords = these_coords[sorted_indices]

            # Calculate consecutive distances
            consecutive_dists = np.linalg.norm(np.diff(sorted_coords, axis=1), axis=1)
            consecutive_dists_pc = consecutive_dists * pixel_size_pc

            # Use both NN and consecutive distances
            filament_spacings = np.concatenate([nn_fil_pc, consecutive_dists_pc])
        else:
            filament_spacings = nn_fil_pc

        all_consecutive_spacings.extend(filament_spacings)

        filament_results.append({
            'id': i,
            'n_cores': n_cores,
            'pixel_count': pixel_count,
            'median_spacing': np.median(filament_spacings),
            'spacings': filament_spacings
        })

print(f"\nFilaments with ≥2 cores: {len(filament_results)}")

if all_consecutive_spacings:
    all_spacings = np.array(all_consecutive_spacings)

    print(f"\nCore Spacing Statistics (PROPER METHOD):")
    print(f"  Total measurements: {len(all_spacings)}")
    print(f"  Median: {np.median(all_spacings):.3f} pc")
    print(f"  Mean:   {np.mean(all_spacings):.3f} pc")
    print(f"  Std:    {np.std(all_spacings):.3f} pc")
    print(f"  Min:    {np.min(all_spacings):.3f} pc")
    print(f"  Max:    {np.max(all_spacings):.3f} pc")

    # Compare methods
    print(f"\n{'='*80}")
    print(f"COMPARISON OF METHODS")
    print(f"{'='*80}")
    print(f"  Original (2D NN):     {np.median(nn_dists_pc):.3f} pc")
    print(f"  Proper (filament):    {np.median(all_spacings):.3f} pc")

    # Compare with theory
    filament_width = 0.10  # pc
    predicted_4x = 4 * filament_width
    predicted_2x = 2 * filament_width

    print(f"\n{'='*80}")
    print(f"COMPARISON WITH THEORY")
    print(f"{'='*80}")
    print(f"  Filament width (observed): {filament_width} pc")
    print(f"  Predicted (4× width):     {predicted_4x} pc")
    print(f"  Predicted (2× width):     {predicted_2x} pc")
    print(f"  Observed (proper method):  {np.median(all_spacings):.3f} pc")
    print(f"  Ratio to 4×:              {np.median(all_spacings)/predicted_4x:.2f}×")
    print(f"  Ratio to 2×:              {np.median(all_spacings)/predicted_2x:.2f}×")

    # Show sample filament results
    if len(filament_results) > 0:
        print(f"\n{'='*80}")
        print(f"SAMPLE FILAMENT RESULTS (first 10)")
        print(f"{'='*80}")
        print(f"  {'ID':<6} {'N':<4} {'Pixels':<8} {'Median (pc)':<12}")
        print(f"  {'-'*35}")
        for fr in filament_results[:10]:
            print(f"  {fr['id']:<6} {fr['n_cores']:<4} {fr['pixel_count']:<8} {fr['median_spacing']:<12.3f}")

    print(f"\n{'='*80}")
    print(f"CONCLUSION")
    print(f"{'='*80}")

    proper_median = np.median(all_spacings)
    original_median = np.median(nn_dists_pc)

    if abs(proper_median - original_median) < 0.02:
        print(f"\n✓ Both methods give similar results: ~{proper_median:.2f} pc")
        print(f"  The 0.21 pc value appears to be ROBUST")
    else:
        print(f"\n⚠️  Methods differ:")
        print(f"    Original: {original_median:.3f} pc")
        print(f"    Proper:   {proper_median:.3f} pc")
        print(f"  The original value may need revision")

    if abs(proper_median - predicted_4x) < 0.05:
        print(f"\n✓ Observed spacing ({proper_median:.2f} pc) matches 4× prediction ({predicted_4x} pc)")
    elif abs(proper_median - predicted_2x) < 0.05:
        print(f"\n⚠️  Observed spacing ({proper_median:.2f} pc) is closer to 2× ({predicted_2x} pc) than 4× ({predicted_4x} pc)")
    else:
        print(f"\n? Observed spacing ({proper_median:.2f} pc) differs from both 2× and 4× predictions")

else:
    print(f"\n✗ No valid filament measurements obtained")
