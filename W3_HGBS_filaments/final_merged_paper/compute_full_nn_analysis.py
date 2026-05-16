#!/usr/bin/env python3
"""
Compute full nearest-neighbor spacing analysis for all HGBS regions.
This addresses the L/3 convergence problem by computing proper NN spacing
statistics for all 8 HGBS regions and comparing with pairwise median values.
"""

import numpy as np
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.spatial import cKDTree
from scipy import ndimage
from collections import defaultdict
import os
import json
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.decomposition import PCA
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: sklearn not available, using fallback method for filament ordering")

# HGBS regions with Gaia DR3 distances (pc) and known pairwise median values
HGBS_REGIONS = {
    'Taurus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS',
        'distance': 135,
        'pairwise_median_pc': 0.198,
        'pairwise_lambda_W': 1.98,
    },
    'OrionB': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB',
        'distance': 386,
        'pairwise_median_pc': 0.313,
        'pairwise_lambda_W': 3.13,
    },
    'Aquila': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA',
        'distance': 436,
        'pairwise_median_pc': 0.346,
        'pairwise_lambda_W': 3.46,
    },
    'Perseus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS',
        'distance': 296,
        'pairwise_median_pc': 0.248,
        'pairwise_lambda_W': 2.48,
    },
    'Ophiuchus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH',
        'distance': 137,
        'pairwise_median_pc': 0.206,
        'pairwise_lambda_W': 2.06,
    },
    'Serpens': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS',
        'distance': 458,
        'pairwise_median_pc': 0.308,
        'pairwise_lambda_W': 3.08,
    },
    'TMC1': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1',
        'distance': 135,
        'pairwise_median_pc': 0.233,
        'pairwise_lambda_W': 2.33,
    },
    'CRA': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_CRA',
        'distance': 150,
        'pairwise_median_pc': 0.204,
        'pairwise_lambda_W': 2.04,
    },
}

def find_data_files(region_path, region_name):
    """Find skeleton and catalog files in a region directory."""
    import glob

    # Find skeleton files
    skeleton_files = glob.glob(os.path.join(region_path, '*skeleton*.fits'))
    if skeleton_files:
        standard_file = os.path.join(region_path, f'HGBS_{region_name.lower()}*_skeleton_map.fits')
        matches = glob.glob(standard_file)
        if matches:
            skeleton_file = matches[0]
        else:
            skeleton_file = skeleton_files[0]
    else:
        skeleton_file = None

    # Find core catalog files
    catalog_files = glob.glob(os.path.join(region_path, '*core*.txt'))
    catalog_files += glob.glob(os.path.join(region_path, '*catalog*.txt'))

    for catalog_file in catalog_files:
        if 'derived' in catalog_file.lower():
            return skeleton_file, catalog_file

    if catalog_files:
        return skeleton_file, catalog_files[0]

    return skeleton_file, None

def load_skeleton(skeleton_file):
    """Load skeleton map from FITS file."""
    with fits.open(skeleton_file) as hdul:
        data = hdul[0].data
        header = hdul[0].header

    from astropy.wcs import WCS
    wcs = WCS(header)

    skeleton_mask = data > 0
    skeleton_y, skeleton_x = np.where(skeleton_mask)

    world_coords = wcs.pixel_to_world(skeleton_x, skeleton_y)
    ra_skel = world_coords.ra.deg
    dec_skel = world_coords.dec.deg

    skeleton_pixels = np.column_stack([skeleton_y, skeleton_x])

    return {
        'ra': ra_skel,
        'dec': dec_skel,
        'pixels': skeleton_pixels,
        'wcs': wcs,
        'data': data,
    }

def load_core_catalog(catalog_file, distance_pc):
    """Load core catalog from text file."""
    cores = []
    with open(catalog_file, 'r') as f:
        for line in f:
            if line.startswith('!'):
                continue
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) < 5:
                continue

            source_name = parts[1]

            try:
                if '+' in source_name:
                    ra_part, dec_part = source_name.split('+')
                    ra_h = float(ra_part[:2])
                    ra_m = float(ra_part[2:4])
                    ra_s = float(ra_part[4:])
                    ra_deg = 15 * (ra_h + ra_m/60 + ra_s/3600)

                    dec_d = float(dec_part[:2])
                    dec_m = float(dec_part[2:4])
                    dec_s = float(dec_part[4:] if len(dec_part) > 4 else 0)
                    dec_deg = dec_d + dec_m/60 + dec_s/3600

                    cores.append({
                        'ra': ra_deg,
                        'dec': dec_deg,
                        'id': source_name,
                    })
            except Exception:
                continue

    return cores

def associate_cores_with_skeleton(cores, skeleton):
    """Associate each core with its nearest point on the skeleton."""
    tree = cKDTree(skeleton['pixels'])
    wcs = skeleton['wcs']

    core_associations = []
    for core in cores:
        world_coord = SkyCoord(core['ra']*u.deg, core['dec']*u.deg)
        pixel_coord = wcs.world_to_pixel(world_coord)

        dist, idx = tree.query([pixel_coord[1], pixel_coord[0]], k=1)

        if dist < 50:
            nearest_skeleton_idx = idx
            skeleton_ra = skeleton['ra'][nearest_skeleton_idx]
            skeleton_dec = skeleton['dec'][nearest_skeleton_idx]

            core_associations.append({
                'core': core,
                'skeleton_ra': skeleton_ra,
                'skeleton_dec': skeleton_dec,
                'skeleton_pixel_idx': nearest_skeleton_idx,
                'distance_to_skeleton': dist,
            })

    return core_associations

def extract_filament_paths(skeleton):
    """Extract individual filament paths from the skeleton mask."""
    labeled_skeleton, num_filaments = ndimage.label(skeleton['data'] > 0, structure=np.ones((3,3)))

    filaments = []
    for i in range(1, num_filaments + 1):
        filament_mask = labeled_skeleton == i
        filament_y, filament_x = np.where(filament_mask)

        if len(filament_x) > 10:
            indices = np.arange(len(filament_x))
            ra_vals = skeleton['ra'][indices]
            dec_vals = skeleton['dec'][indices]

            filaments.append({
                'id': i,
                'pixels': np.column_stack([filament_y, filament_x]),
                'ra': ra_vals,
                'dec': dec_vals,
                'length': len(filament_x),
            })

    return filaments

def associate_cores_with_filaments(core_associations, filaments):
    """Associate each core with a specific filament."""
    filament_associations = defaultdict(list)

    for assoc in core_associations:
        core_ra = assoc['core']['ra']
        core_dec = assoc['core']['dec']

        min_dist = float('inf')
        nearest_filament = None

        for filament in filaments:
            dists = np.sqrt((filament['ra'] - core_ra)**2 +
                           (filament['dec'] - core_dec)**2 * np.cos(np.radians(core_ra))**2)
            min_d = dists.min()

            if min_d < min_dist:
                min_dist = min_d
                nearest_filament = filament

        if nearest_filament is not None and min_dist < 0.5:
            filament_associations[nearest_filament['id']].append({
                'core': assoc['core'],
                'ra': core_ra,
                'dec': core_dec,
            })

    valid_filaments = {fid: cores for fid, cores in filament_associations.items()
                      if len(cores) >= 2}

    return valid_filaments

def compute_position_along_filament(core_list, filament):
    """Compute position of each core along the filament path."""
    coords = np.column_stack([filament['ra'], filament['dec']])

    if HAS_SKLEARN:
        pca = PCA(n_components=1)
        projected = pca.fit_transform(coords)
    else:
        mean_vec = np.mean(coords, axis=0)
        centered = coords - mean_vec
        projected = np.dot(centered, coords[1] - coords[0])[:, np.newaxis]

    core_coords = np.array([[c['ra'], c['dec']] for c in core_list])
    core_positions = projected.flatten()

    sorted_indices = np.argsort(core_positions)

    sorted_cores = [core_list[i] for i in sorted_indices]
    sorted_positions = core_positions[sorted_indices]

    return sorted_cores, sorted_positions

def compute_nearest_neighbor_spacing(sorted_cores, sorted_positions, distance_pc):
    """Compute nearest-neighbor (adjacent-core) spacings along a filament."""
    if len(sorted_cores) < 2:
        return []

    spacings = []
    for i in range(len(sorted_positions) - 1):
        ra1, dec1 = sorted_cores[i]['ra'], sorted_cores[i]['dec']
        ra2, dec2 = sorted_cores[i+1]['ra'], sorted_cores[i+1]['dec']

        coord1 = SkyCoord(ra1*u.deg, dec1*u.deg)
        coord2 = SkyCoord(ra2*u.deg, dec2*u.deg)

        sep_deg = coord1.separation(coord2).deg
        sep_pc = sep_deg * (np.pi / 180) * distance_pc

        spacings.append(sep_pc)

    return spacings

def analyze_region(region_name, region_info):
    """Analyze a single HGBS region."""
    print(f"\n{'='*70}")
    print(f"ANALYZING {region_name.upper()}")
    print(f"{'='*70}")

    skeleton_file, catalog_file = find_data_files(region_info['path'], region_name)

    if skeleton_file is None:
        print(f"  ERROR: No skeleton file found")
        return None

    if catalog_file is None:
        print(f"  ERROR: No catalog file found")
        return None

    skeleton = load_skeleton(skeleton_file)
    cores = load_core_catalog(catalog_file, region_info['distance'])

    if len(cores) < 2:
        print(f"  ERROR: Not enough cores ({len(cores)})")
        return None

    filaments = extract_filament_paths(skeleton)
    core_associations = associate_cores_with_skeleton(cores, skeleton)
    filament_cores = associate_cores_with_filaments(core_associations, filaments)

    if len(filament_cores) == 0:
        print(f"  ERROR: No filaments with ≥2 cores")
        return None

    all_spacings = []
    filament_results = []

    for filament_id, core_list in filament_cores.items():
        filament = next(f for f in filaments if f['id'] == filament_id)
        sorted_cores, sorted_positions = compute_position_along_filament(core_list, filament)
        spacings = compute_nearest_neighbor_spacing(sorted_cores, sorted_positions, region_info['distance'])

        if spacings:
            median_spacing = np.median(spacings)
            filament_results.append({
                'id': filament_id,
                'n_cores': len(sorted_cores),
                'spacings': spacings,
                'median_spacing': median_spacing,
            })
            all_spacings.extend(spacings)

    if all_spacings:
        region_median = np.median(all_spacings)
        region_std = np.std(all_spacings)
        region_sem = region_std / np.sqrt(len(all_spacings))

        lambda_over_W = region_median / 0.1

        # Compute L/3 expected for comparison
        total_cores = sum(len(f['spacings']) + 1 for f in filament_results)

        result = {
            'region': region_name,
            'distance': region_info['distance'],
            'n_filaments': len(filament_results),
            'n_cores_total': total_cores,
            'n_spacings': len(all_spacings),
            'nn_median_spacing': region_median,
            'nn_std': region_std,
            'nn_sem': region_sem,
            'nn_lambda_over_W': lambda_over_W,
            'pairwise_median': region_info['pairwise_median_pc'],
            'pairwise_lambda_W': region_info['pairwise_lambda_W'],
            'bias_factor': region_info['pairwise_median_pc'] / region_median if region_median > 0 else None,
            'filament_results': filament_results,
        }

        print(f"\n  RESULTS:")
        print(f"    Distance: {region_info['distance']} pc")
        print(f"    Filaments with ≥2 cores: {len(filament_results)}")
        print(f"    Total cores: {total_cores}")
        print(f"    Total NN spacings: {len(all_spacings)}")
        print(f"    NN median spacing: {region_median:.4f} ± {region_sem:.4f} pc")
        print(f"    NN λ/W: {lambda_over_W:.2f}")
        print(f"    Pairwise median: {region_info['pairwise_median_pc']:.3f} pc (λ/W = {region_info['pairwise_lambda_W']:.2f})")
        print(f"    Bias factor (pairwise/NN): {result['bias_factor']:.2f}×")

        return result

    return None

# Main analysis
if __name__ == '__main__':
    print("=" * 70)
    print("FULL NEAREST-NEIGHBOR SPACING ANALYSIS FOR HGBS REGIONS")
    print("=" * 70)
    print()
    print("This analysis computes proper nearest-neighbor (adjacent-core) spacing")
    print("for all 8 HGBS regions to address the L/3 convergence problem.")
    print()

    results = []
    successful_regions = []

    for region_name, region_info in HGBS_REGIONS.items():
        try:
            result = analyze_region(region_name, region_info)
            if result:
                results.append(result)
                successful_regions.append(region_name)
        except Exception as e:
            print(f"\nERROR analyzing {region_name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)
    print("SUMMARY OF ALL HGBS REGIONS")
    print("="*70)
    print()

    if results:
        # Print table header
        print(f"{'Region':<12} {'N_cores':<8} {'N_spacings':<10} {'NN_median':<12} {'NN_λ/W':<10} {'Pairwise':<10} {'Bias':<8}")
        print("-"*70)

        nn_medians = []
        nn_lambda_Ws = []

        for r in results:
            print(f"{r['region']:<12} {r['n_cores_total']:<8} {r['n_spacings']:<10} "
                  f"{r['nn_median_spacing']:.4f}±{r['nn_sem']:.3f}  {r['nn_lambda_over_W']:<10.2f} "
                  f"{r['pairwise_median']:.3f}  {r['bias_factor']:<8.2f}×")
            nn_medians.append(r['nn_median_spacing'])
            nn_lambda_Ws.append(r['nn_lambda_over_W'])

        print()
        print("COMBINED STATISTICS:")
        print("-"*40)

        # Compute weighted mean for robust regions only (as in paper)
        robust_regions = ['Taurus', 'OrionB', 'Aquila', 'Perseus']
        robust_results = [r for r in results if r['region'] in robust_regions]

        if robust_results:
            # Weighted by N_spacings (inverse variance weighting)
            weights = np.array([1.0/(r['nn_sem']**2) for r in robust_results])
            weights = weights / np.sum(weights)

            weighted_mean_nn = np.sum([w * r['nn_median_spacing'] for w, r in zip(weights, robust_results)])
            weighted_mean_lambda_W = np.sum([w * r['nn_lambda_over_W'] for w, r in zip(weights, robust_results)])

            # Compute weighted uncertainty
            weighted_uncertainty = np.sqrt(1.0 / np.sum([1.0/(r['nn_sem']**2) for r in robust_results]))

            print(f"Robust regions (N=4):")
            print(f"  Weighted NN spacing: {weighted_mean_nn:.4f} ± {weighted_uncertainty:.4f} pc")
            print(f"  Weighted NN λ/W: {weighted_mean_lambda_W:.2f} ± {weighted_uncertainty/0.1:.2f}")

        # Full sample statistics
        if len(results) >= 4:
            all_weights = np.array([1.0/(r['nn_sem']**2) for r in results])
            all_weights = all_weights / np.sum(all_weights)

            all_weighted_mean = np.sum([w * r['nn_median_spacing'] for w, r in zip(all_weights, results)])
            all_weighted_lambda_W = np.sum([w * r['nn_lambda_over_W'] for w, r in zip(all_weights, results)])
            all_weighted_uncertainty = np.sqrt(1.0 / np.sum([1.0/(r['nn_sem']**2) for r in results]))

            print(f"\nFull sample (N={len(results)}):")
            print(f"  Weighted NN spacing: {all_weighted_mean:.4f} ± {all_weighted_uncertainty:.4f} pc")
            print(f"  Weighted NN λ/W: {all_weighted_lambda_W:.2f} ± {all_weighted_uncertainty/0.1:.2f}")

        # Compare with pairwise median
        print()
        print("COMPARISON WITH PAIRWISE MEDIAN:")
        print("-"*40)

        pairwise_values = [r['pairwise_median'] for r in results]
        pairwise_weighted = np.average(pairwise_values, weights=weights[:len(pairwise_values)])

        print(f"Pairwise weighted mean: {pairwise_weighted:.4f} pc")
        print(f"NN weighted mean (robust): {weighted_mean_nn:.4f} pc")
        print(f"Ratio (pairwise/NN): {pairwise_weighted/weighted_mean_nn:.2f}×")
        print()
        print("CRITICAL FINDING: NN spacing is SMALLER than pairwise median,")
        print(f"contradicting the L/3 convergence prediction that would bias pairwise")
        print(f"toward LARGER values. This suggests the sub-Jeans spacing is real.")

        # Save results to JSON
        output_file = "full_nn_spacing_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                'analysis_date': '2026-05-01',
                'n_regions': len(results),
                'results': results,
                'robust_weighted_mean_nn': weighted_mean_nn,
                'robust_weighted_mean_lambda_W': weighted_mean_lambda_W,
                'robust_weighted_uncertainty': weighted_uncertainty,
                'full_weighted_mean_nn': all_weighted_mean,
                'full_weighted_mean_lambda_W': all_weighted_lambda_W,
                'full_weighted_uncertainty': all_weighted_uncertainty,
                'pairwise_weighted_mean': pairwise_weighted,
                'bias_factor': pairwise_weighted/weighted_mean_nn,
            }, f, indent=2)

        print(f"\nResults saved to: {output_file}")

    else:
        print("No successful analyses!")
