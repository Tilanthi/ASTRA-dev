#!/usr/bin/env python3
"""
Orion B NN Analysis - processes skeleton without downsampling to preserve structure.
Uses morphological dilation to connect nearby skeleton pixels.
"""
import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS, utils
from scipy import ndimage
from collections import defaultdict
import json
import warnings
warnings.filterwarnings('ignore')

def load_catalog(catalog_path):
    """Load core catalog."""
    print(f"Loading catalog...")
    cores = []
    with open(catalog_path, 'r', encoding='latin-1', errors='ignore') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    int(parts[0])
                    ra_str, dec_str = None, None
                    for i, part in enumerate(parts[1:], 1):
                        if ':' in part and i < len(parts) - 1:
                            if ra_str is None:
                                ra_str = part
                            elif dec_str is None:
                                dec_str = part
                                break
                    if ra_str and dec_str:
                        coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
                        cores.append({'id': int(parts[0]), 'ra': coord.ra.deg, 'dec': coord.dec.deg})
                except:
                    pass
    print(f"  Loaded {len(cores)} cores")
    return cores

def load_skeleton(skeleton_path):
    """Load skeleton at full resolution."""
    print(f"Loading skeleton...")
    with fits.open(skeleton_path) as hdul:
        skeleton = hdul[0].data.astype(np.float64)
        wcs = WCS(hdul[0].header)
    print(f"  Shape: {skeleton.shape}")
    return skeleton, wcs

def extract_filaments(skeleton, threshold=50, min_size=50, dilate=2):
    """Extract filaments with dilation to connect thin structures."""
    print(f"Extracting filaments (threshold={threshold}, min_size={min_size}, dilate={dilate})...")

    # Create mask
    mask = skeleton > threshold

    # Dilate to connect nearby skeleton pixels
    if dilate > 0:
        mask = ndimage.binary_dilation(mask, iterations=dilate)

    # Label
    labeled, n_features = ndimage.label(mask)
    print(f"  Found {n_features} features")

    # Extract filaments above minimum size
    filaments = []
    for i in range(1, n_features + 1):
        count = np.sum(labeled == i)
        if count >= min_size:
            yp, xp = np.where(labeled == i)
            filaments.append({'id': i, 'y': yp, 'x': xp, 'size': count})

    print(f"  Extracted {len(filaments)} filaments (size >= {min_size})")
    return filaments

def associate_cores_direct(cores, skeleton, wcs, distance_pc=386, width_pc=0.1):
    """Associate cores directly with skeleton pixels using KDTree."""
    print(f"Associating cores with skeleton (direct method)...")

    # Build KDTree of skeleton pixels for fast distance lookup
    yp, xp = np.where(skeleton > 50)  # Use same threshold as filament extraction
    print(f"  Building KDTree from {len(xp)} skeleton pixels...")

    from scipy.spatial import cKDTree
    skeleton_pixels = np.column_stack((xp, yp))
    tree = cKDTree(skeleton_pixels)

    # 2W threshold in pixels (0.1 pc at 386 pc distance ≈ 17 pixels)
    assoc_threshold_px = 20

    core_assoc = {}
    skeleton_pixel_indices = {}  # Store which skeleton pixel each core associates with

    for i, core in enumerate(cores):
        if i % 100 == 0:
            print(f"  Processing core {i}/{len(cores)}...")

        try:
            px, py = wcs.all_world2pix(core['ra'], core['dec'], 1)

            # Query KDTree for nearest skeleton pixel
            dist, idx = tree.query([px, py])
            if dist < assoc_threshold_px:
                # Assign to filament group based on skeleton pixel location
                # We'll group by spatial proximity later
                core_assoc[i] = idx
                skeleton_pixel_indices[i] = int(idx)
        except:
            pass

    print(f"  Associated {len(core_assoc)}/{len(cores)} cores")
    return core_assoc, skeleton_pixel_indices, skeleton_pixels

def compute_spacings_direct(cores, core_assoc, skeleton_pixel_indices, skeleton_pixels, wcs, distance_pc=386):
    """Compute filament-projected NN spacings using spatial grouping."""
    print(f"Computing NN spacings (direct method)...")

    # Group associated cores by proximity to form filament groups
    from scipy.cluster import hierarchy

    if len(core_assoc) < 2:
        print(f"  ERROR: Only {len(core_assoc)} cores associated, need at least 2")
        return np.array([])

    # Get skeleton pixel positions for associated cores
    assoc_indices = [core_assoc[ci] for ci in core_assoc.keys()]
    unique_indices = list(set(assoc_indices))
    unique_positions = skeleton_pixels[unique_indices]

    # Cluster skeleton pixels into filament groups
    if len(unique_positions) > 1:
        linkage = hierarchy.linkage(unique_positions, method='single')
        clusters = hierarchy.fcluster(linkage, t=50, criterion='distance')
    else:
        clusters = np.array([1])

    # Map each core to its cluster
    core_clusters = {}
    for ci, skel_idx in core_assoc.items():
        unique_idx = unique_indices.index(skel_idx)
        core_clusters[ci] = clusters[unique_idx]

    # Group cores by cluster
    cluster_cores = defaultdict(list)
    for ci, cluster_id in core_clusters.items():
        cluster_cores[cluster_id].append(ci)

    print(f"  Formed {len(cluster_cores)} filament groups from {len(core_assoc)} cores")

    # Compute spacings within each cluster
    spacings = []
    for cluster_id, core_list in cluster_cores.items():
        if len(core_list) < 2:
            continue

        coords = SkyCoord(ra=[cores[ci]['ra'] for ci in core_list]*u.deg,
                         dec=[cores[ci]['dec'] for ci in core_list]*u.deg)

        # Project cluster onto 1D line using PCA
        if len(core_list) == 2:
            sep_pc = coords[0].separation(coords[1]).radian * distance_pc
            spacings.append(sep_pc)
        else:
            xyz = coords.cartesian
            xyz = np.vstack([xyz.x.value, xyz.y.value, xyz.z.value]).T

            mean = np.mean(xyz, axis=0)
            centered = xyz - mean
            cov = np.cov(centered.T)
            eigvals, eigvecs = np.linalg.eigh(cov)
            pc1 = eigvecs[:, -1]

            projections = np.dot(centered, pc1)
            sorted_indices = np.argsort(projections)
            sorted_coords = coords[sorted_indices]

            for j in range(len(sorted_coords) - 1):
                sep_pc = sorted_coords[j].separation(sorted_coords[j+1]).radian * distance_pc
                spacings.append(sep_pc)

    print(f"  Computed {len(spacings)} spacings")
    return np.array(spacings)

def main():
    base = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA'

    print("\n" + "="*60)
    print("ORION B NN ANALYSIS")
    print("="*60)

    # Load data
    skeleton_path = f'{base}/HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits'
    catalog_path = f'{base}/HGBS_ORIB/HGBS_orionB_observed_core_catalog.txt'

    cores = load_catalog(catalog_path)
    skeleton, wcs = load_skeleton(skeleton_path)

    # Associate cores directly with skeleton (faster method)
    core_assoc, skeleton_pixel_indices, skeleton_pixels = associate_cores_direct(cores, skeleton, wcs, distance_pc=386)

    if len(core_assoc) < 10:
        print("ERROR: Too few cores associated!")
        return

    # Compute spacings using spatial grouping
    spacings = compute_spacings_direct(cores, core_assoc, skeleton_pixel_indices, skeleton_pixels, wcs, distance_pc=386)

    if len(spacings) == 0:
        print("ERROR: No spacings computed!")
        return

    # Report results
    print(f"\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Total cores: {len(cores)}")
    print(f"Associated cores: {len(core_assoc)} ({100*len(core_assoc)/len(cores):.1f}%)")
    print(f"NN spacings: {len(spacings)}")
    print(f"\nNN Statistics:")
    print(f"  Median: {np.median(spacings):.4f} pc")
    print(f"  Mean:   {np.mean(spacings):.4f} pc")
    print(f"  Std:    {np.std(spacings):.4f} pc")
    print(f"  Min:    {np.min(spacings):.4f} pc")
    print(f"  Max:    {np.max(spacings):.4f} pc")
    print(f"\nλ/W: {np.median(spacings)/0.1:.2f}")

    # Save results
    result = {
        'region': 'Orion B',
        'n_cores_total': len(cores),
        'n_cores_associated': len(core_assoc),
        'n_spacings': len(spacings),
        'nn_median_pc': float(np.median(spacings)),
        'nn_mean_pc': float(np.mean(spacings)),
        'nn_std_pc': float(np.std(spacings)),
        'nn_min_pc': float(np.min(spacings)),
        'nn_max_pc': float(np.max(spacings)),
        'lambda_over_W': float(np.median(spacings) / 0.1),
        'association_threshold_px': 20,
        'clustering_threshold_px': 50,
        'skeleton_threshold': 50,
    }

    output_path = f'{base}/orionB_nn_result_v2.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to {output_path}")

if __name__ == '__main__':
    main()
