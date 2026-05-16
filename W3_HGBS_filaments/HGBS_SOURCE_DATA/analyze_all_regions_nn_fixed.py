#!/usr/bin/env python3
"""
Fixed multi-region NN analysis for robust HGBS regions.
"""
import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from scipy.spatial import cKDTree
from scipy.cluster import hierarchy
from collections import defaultdict
import json
import warnings
warnings.filterwarnings('ignore')

def load_catalog_taurus(catalog_path):
    """Load Taurus catalog (different format)."""
    print(f"Loading Taurus catalog from {catalog_path}...")
    cores = []
    with open(catalog_path, 'r', encoding='latin-1', errors='ignore') as f:
        lines = f.readlines()

    # Skip header lines (starting with !)
    data_started = False
    for line in lines:
        if line.strip().startswith('!'):
            continue
        if not data_started and '---' in line:
            data_started = True
            continue

        parts = line.split()
        if len(parts) >= 10:  # Taurus format has many columns
            try:
                core_id = parts[0]
                # RA and Dec are in columns 9 and 10 (0-indexed)
                ra_str = parts[9]
                dec_str = parts[10]

                # Parse sexagesimal
                coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
                cores.append({'id': int(core_id), 'ra': coord.ra.deg, 'dec': coord.dec.deg})
            except:
                pass

    print(f"  Loaded {len(cores)} cores")
    return cores

def load_catalog_standard(catalog_path):
    """Load standard HGBS catalog format."""
    print(f"Loading catalog from {catalog_path}...")
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
    print(f"Loading skeleton from {skeleton_path}...")
    with fits.open(skeleton_path) as hdul:
        skeleton = hdul[0].data.astype(np.float64)
        wcs = WCS(hdul[0].header)
    print(f"  Shape: {skeleton.shape}, nonzero: {np.count_nonzero(skeleton)}")
    return skeleton, wcs

def analyze_region_nn(region_name, skeleton_path, catalog_path, distance_pc, skeleton_threshold=50):
    """Analyze NN spacing for a single region."""

    print(f"\n{'='*60}")
    print(f"{region_name.upper()} (d = {distance_pc} pc)")
    print(f"{'='*60}")

    # Load data
    if 'Taurus' in region_name:
        cores = load_catalog_taurus(catalog_path)
    else:
        cores = load_catalog_standard(catalog_path)

    skeleton, wcs = load_skeleton(skeleton_path)

    # Associate cores directly with skeleton
    yp, xp = np.where(skeleton > skeleton_threshold)
    print(f"  Skeleton pixels (threshold>{skeleton_threshold}): {len(xp)}")

    if len(xp) < 100:
        print(f"  WARNING: Very few skeleton pixels ({len(xp)})")

    if len(xp) == 0:
        return {'region': region_name, 'error': 'No skeleton pixels found'}

    skeleton_pixels = np.column_stack((xp, yp))
    tree = cKDTree(skeleton_pixels)

    assoc_threshold_px = 20
    core_assoc = {}
    skeleton_pixel_indices = {}

    for i, core in enumerate(cores):
        if i % 100 == 0 and len(cores) > 100:
            print(f"  Processing core {i}/{len(cores)}...")

        try:
            px, py = wcs.all_world2pix(core['ra'], core['dec'], 1)
            dist, idx = tree.query([px, py])
            if dist < assoc_threshold_px:
                core_assoc[i] = idx
                skeleton_pixel_indices[i] = int(idx)
        except:
            pass

    print(f"  Associated {len(core_assoc)}/{len(cores)} cores ({100*len(core_assoc)/len(cores):.1f}%)")

    if len(core_assoc) < 5:
        return {'region': region_name, 'error': 'Too few cores associated'}

    # Cluster and compute spacings
    assoc_indices = [core_assoc[ci] for ci in core_assoc.keys()]
    unique_indices = list(set(assoc_indices))
    unique_positions = skeleton_pixels[unique_indices]

    if len(unique_positions) > 1:
        linkage = hierarchy.linkage(unique_positions, method='single')
        clusters = hierarchy.fcluster(linkage, t=50, criterion='distance')
    else:
        clusters = np.array([1])

    core_clusters = {}
    for ci, skel_idx in core_assoc.items():
        unique_idx = unique_indices.index(skel_idx)
        core_clusters[ci] = clusters[unique_idx]

    cluster_cores = defaultdict(list)
    for ci, cluster_id in core_clusters.items():
        cluster_cores[cluster_id].append(ci)

    print(f"  Formed {len(cluster_cores)} filament groups")

    # Compute spacings
    spacings = []
    for cluster_id, core_list in cluster_cores.items():
        if len(core_list) < 2:
            continue

        coords = SkyCoord(ra=[cores[ci]['ra'] for ci in core_list]*u.deg,
                         dec=[cores[ci]['dec'] for ci in core_list]*u.deg)

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

    if len(spacings) < 3:
        return {'region': region_name, 'error': f'Too few spacings computed ({len(spacings)})'}

    # Report results
    print(f"\n  NN Statistics:")
    print(f"    Median: {np.median(spacings):.4f} pc")
    print(f"    Mean:   {np.mean(spacings):.4f} pc")
    print(f"    Std:    {np.std(spacings):.4f} pc")
    print(f"    λ/W:    {np.median(spacings)/0.1:.2f}")

    return {
        'region': region_name,
        'distance_pc': distance_pc,
        'n_cores_total': len(cores),
        'n_cores_associated': len(core_assoc),
        'n_filament_groups': len(cluster_cores),
        'n_spacings': len(spacings),
        'nn_median_pc': float(np.median(spacings)),
        'nn_mean_pc': float(np.mean(spacings)),
        'nn_std_pc': float(np.std(spacings)),
        'nn_min_pc': float(np.min(spacings)),
        'nn_max_pc': float(np.max(spacings)),
        'lambda_over_W': float(np.median(spacings) / 0.1),
    }

def main():
    base = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA'

    regions = [
        ('Orion B', f'{base}/HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits',
                   f'{base}/HGBS_ORIB/HGBS_orionB_observed_core_catalog.txt', 386, 50),
        ('Aquila', f'{base}/HGBS_AQUILA/HGBS_AQUILA/HGBS_aquilaM2_skeleton_map_thresh50.fits',
                  f'{base}/HGBS_AQUILA/HGBS_AQUILA/HGBS_aquilaM2_observed_core_catalog.txt', 436, 50),
        ('Perseus', f'{base}/HGBS_PERSEUS/HGBS_perseus_skeleton_map_thresh20.fits',
                   f'{base}/HGBS_PERSEUS/HGBS_PERSEUS/HGBS_perseus_observed_core_catalog.txt', 296, 30),
        ('Taurus', f'{base}/HGBS_TAURUS/HGBS_taurusL1495_skeleton_map_thresh50.fits',
                   f'{base}/HGBS_TAURUS/HGBS_taurusL1495_observed_core_catalog.txt', 135, 30),
    ]

    results = []
    for name, skel, cat, dist, threshold in regions:
        try:
            result = analyze_region_nn(name, skel, cat, dist, skeleton_threshold=threshold)
            results.append(result)
        except Exception as e:
            print(f"ERROR analyzing {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append({'region': name, 'error': str(e)})

    # Save results
    output_path = f'{base}/all_regions_nn_results_fixed.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print("ALL REGIONS SUMMARY")
    print(f"{'='*60}")

    for r in results:
        if 'error' not in r:
            print(f"\n{r['region']}:")
            print(f"  Associated: {r['n_cores_associated']}/{r['n_cores_total']} ({100*r['n_cores_associated']/r['n_cores_total']:.1f}%)")
            print(f"  Spacings: {r['n_spacings']}")
            print(f"  λ/W: {r['lambda_over_W']:.2f}")
        else:
            print(f"\n{r['region']}: {r['error']}")

    # Compute PM vs NN comparison
    valid = [r for r in results if 'error' not in r]
    if len(valid) >= 2:
        print(f"\n{'='*60}")
        print("PM vs NN COMPARISON")
        print(f"{'='*60}")

        pm_values = {
            'Orion B': 3.13,
            'Aquila': 3.07,
            'Perseus': 2.56,
            'Taurus': 2.10
        }

        nn_smaller_pct = []
        for r in valid:
            pm_val = pm_values.get(r['region'], None)
            if pm_val:
                nn_val = r['lambda_over_W']
                diff_pct = 100 * (pm_val - nn_val) / pm_val
                nn_smaller_pct.append(diff_pct)
                print(f"\n{r['region']}:")
                print(f"  PM: λ/W = {pm_val:.2f}")
                print(f"  NN: λ/W = {nn_val:.2f}")
                print(f"  NN is {diff_pct:.1f}% smaller than PM")

        if nn_smaller_pct:
            print(f"\n{'='*60}")
            print(f"MEAN NN vs PM DIFFERENCE: {np.mean(nn_smaller_pct):.1f}%")
            print(f"RANGE: {np.min(nn_smaller_pct):.1f}% - {np.max(nn_smaller_pct):.1f}%")
            print(f"{'='*60}")

    print(f"\nResults saved to {output_path}")

if __name__ == '__main__':
    main()
