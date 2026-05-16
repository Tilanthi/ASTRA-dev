#!/usr/bin/env python3
"""
Compute full nearest-neighbor spacing analysis for all HGBS regions.
This addresses the L/3 convergence problem by computing proper NN spacing
statistics for all 8 HGBS regions and comparing with pairwise median values.

Improved catalog parser that handles the actual HGBS catalog format.
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

# HGBS regions with Gaia DR3 distances (pc) and known pairwise median values
HGBS_REGIONS = {
    'Taurus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS',
        'skeleton_file': 'HGBS_taurusL1495_skeleton_map.fits',
        'catalog_file': 'HGBS_taurusL1495_observed_core_catalog.txt',
        'distance': 135,
        'pairwise_median_pc': 0.198,
        'pairwise_lambda_W': 1.98,
    },
    'OrionB': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB',
        'skeleton_file': 'simplified_skeleton.fits',
        'catalog_file': 'HGBS_orionB_observed_core_catalog.txt',
        'distance': 386,
        'pairwise_median_pc': 0.313,
        'pairwise_lambda_W': 3.13,
    },
    'Aquila': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA/HGBS_AQUILA',
        'skeleton_file': 'HGBS_aquilaM2_skeleton_map.fits',
        'catalog_file': 'HGBS_aquilaM2_observed_core_catalog.txt',
        'distance': 436,
        'pairwise_median_pc': 0.346,
        'pairwise_lambda_W': 3.46,
    },
    'Perseus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS',
        'skeleton_file': 'HGBS_perseus_skeleton_map.fits',
        'catalog_file': None,  # Will search for catalog
        'distance': 296,
        'pairwise_median_pc': 0.248,
        'pairwise_lambda_W': 2.48,
    },
    'Ophiuchus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH',
        'skeleton_file': 'HGBS_oph_l1688_skeleton_map.fits',
        'catalog_file': 'HGBS_ophiuchus_observed_core_catalog.txt',
        'distance': 137,
        'pairwise_median_pc': 0.206,
        'pairwise_lambda_W': 2.06,
    },
    'Serpens': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS',
        'skeleton_file': 'HGBS_serpens_skeleton_map.fits',
        'catalog_file': 'HGBS_serpens_observed_core_catalog.txt',
        'distance': 458,
        'pairwise_median_pc': 0.308,
        'pairwise_lambda_W': 3.08,
    },
    'TMC1': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1',
        'skeleton_file': 'HGBS_taurusTMC1_skeleton_map.fits',
        'catalog_file': 'HGBS_taurusTMC1_observed_core_catalog.txt',
        'distance': 135,
        'pairwise_median_pc': 0.233,
        'pairwise_lambda_W': 2.33,
    },
    'CRA': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_CRA',
        'skeleton_file': 'HGBS_craNS_skeleton_map.fits',
        'catalog_file': 'HGBS_craNS_observed_core_catalog.txt',
        'distance': 150,
        'pairwise_median_pc': 0.204,
        'pairwise_lambda_W': 2.04,
    },
}


def find_catalog_file(region_path, region_name):
    """Find catalog file if not specified."""
    import glob

    # Try common patterns
    patterns = [
        f'*{region_name.lower()}*catalog*.txt',
        f'*observed*catalog*.txt',
        f'*derived*catalog*.txt',
        '*catalog*.txt',
    ]

    for pattern in patterns:
        files = glob.glob(os.path.join(region_path, pattern))
        if files:
            return files[0]

    return None


def load_skeleton(skeleton_file):
    """Load skeleton map from FITS file."""
    print(f"  Loading skeleton: {skeleton_file}")
    try:
        with fits.open(skeleton_file) as hdul:
            data = hdul[0].data
            header = hdul[0].header

        from astropy.wcs import WCS
        wcs = WCS(header)

        skeleton_mask = data > 0
        skeleton_y, skeleton_x = np.where(skeleton_mask)

        if len(skeleton_x) == 0:
            print(f"  WARNING: Skeleton is empty!")
            return None

        world_coords = wcs.pixel_to_world(skeleton_x, skeleton_y)
        ra_skel = world_coords.ra.deg
        dec_skel = world_coords.dec.deg

        skeleton_pixels = np.column_stack([skeleton_y, skeleton_x])

        print(f"  Skeleton loaded: {len(skeleton_x)} pixels")

        return {
            'ra': ra_skel,
            'dec': dec_skel,
            'pixels': skeleton_pixels,
            'wcs': wcs,
            'data': data,
        }
    except Exception as e:
        print(f"  ERROR loading skeleton: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_core_catalog_v2(catalog_file, distance_pc):
    """Load core catalog from text file using improved parser."""
    print(f"  Loading catalog: {catalog_file}")

    cores = []

    # Try different encodings
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

    for encoding in encodings:
        try:
            with open(catalog_file, 'r', encoding=encoding) as f:
                lines = f.readlines()

            # Find first data line (skip headers starting with !)
            data_start = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('!'):
                    data_start = i
                    break

            print(f"  Found data at line {data_start}, using encoding: {encoding}")

            # Parse data lines
            for line in lines[data_start:]:
                line = line.strip()
                if not line or line.startswith('!'):
                    continue

                parts = line.split()

                if len(parts) < 8:
                    continue

                # Extract source name (column 2, index 1)
                source_name = parts[1]

                # Parse RA from columns 3-5 (indices 2-4): HH MM SS.SS
                try:
                    ra_h = float(parts[2])
                    ra_m = float(parts[3])
                    ra_s = float(parts[4])
                    ra_deg = 15 * (ra_h + ra_m/60 + ra_s/3600)

                    # Parse Dec from columns 6-8 (indices 5-7): DD MM SS.SS or +/-DD MM SS
                    dec_str = parts[5]
                    dec_d = float(dec_str)
                    dec_m = float(parts[6])
                    dec_s = float(parts[7]) if len(parts) > 7 else 0.0

                    # Handle sign properly
                    if dec_d < 0:
                        dec_deg = dec_d - dec_m/60 - dec_s/3600
                    else:
                        dec_deg = dec_d + dec_m/60 + dec_s/3600

                    cores.append({
                        'ra': ra_deg,
                        'dec': dec_deg,
                        'id': source_name,
                    })

                except (ValueError, IndexError) as e:
                    # Skip lines that can't be parsed
                    continue

            print(f"  Loaded {len(cores)} cores")
            return cores

        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  Error with encoding {encoding}: {e}")
            continue

    print(f"  ERROR: Could not read catalog with any encoding")
    return []


def associate_cores_with_skeleton(cores, skeleton, distance_pc, max_distance=0.1):
    """Associate each core with its nearest point on the skeleton."""
    if skeleton is None:
        return []

    tree = cKDTree(skeleton['pixels'])
    wcs = skeleton['wcs']

    core_associations = []
    max_dist_pixels = max_distance / 3600 * 180 / np.pi  # Convert degrees to pixels (approximate)

    for core in cores:
        try:
            world_coord = SkyCoord(core['ra']*u.deg, core['dec']*u.deg)
            pixel_coord = wcs.world_to_pixel(world_coord)

            dist, idx = tree.query([pixel_coord[1], pixel_coord[0]], k=1)

            if dist < 100:  # Large threshold to include more cores
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
        except Exception as e:
            continue

    print(f"  Associated {len(core_associations)} cores with skeleton")
    return core_associations


def extract_filament_paths(skeleton):
    """Extract individual filament paths from the skeleton mask."""
    if skeleton is None:
        return []

    labeled_skeleton, num_filaments = ndimage.label(skeleton['data'] > 0, structure=np.ones((3,3)))

    filaments = []
    for i in range(1, num_filaments + 1):
        filament_mask = labeled_skeleton == i
        filament_y, filament_x = np.where(filament_mask)

        if len(filament_x) > 10:  # Minimum length threshold
            # Get actual RA/Dec for this filament
            indices = np.arange(len(filament_x))
            ra_vals = skeleton['ra'][indices] if len(indices) < len(skeleton['ra']) else filament_x
            dec_vals = skeleton['dec'][indices] if len(indices) < len(skeleton['dec']) else filament_y

            filaments.append({
                'id': i,
                'pixels': np.column_stack([filament_y, filament_x]),
                'ra': ra_vals,
                'dec': dec_vals,
                'length': len(filament_x),
            })

    print(f"  Extracted {len(filaments)} filaments with >10 pixels")
    return filaments


def compute_nn_spacing_simplified(cores, distance_pc):
    """
    Compute simplified NN spacing using 2D spatial clustering.
    This groups cores by proximity and computes spacings within clusters.
    """
    if len(cores) < 2:
        return []

    # Convert to numpy array
    coords = np.array([[c['ra'], c['dec']] for c in cores])

    # Build KD-tree for nearest neighbor queries
    tree = cKDTree(coords)

    # Query 2 nearest neighbors (first is self)
    distances, indices = tree.query(coords, k=2)

    # Second column is distance to nearest neighbor
    nn_distances_deg = distances[:, 1]

    # Convert angular separation to physical distance
    # Approximation: small angle formula
    mean_dec = np.mean(coords[:, 1])
    cos_dec = np.cos(np.radians(mean_dec))

    nn_spacings_pc = []
    for dist_deg in nn_distances_deg:
        sep_pc = dist_deg * (np.pi / 180) * distance_pc / cos_dec
        nn_spacings_pc.append(sep_pc)

    return nn_spacings_pc


def analyze_region_simplified(region_name, region_info):
    """Analyze a single HGBS region using simplified NN spacing."""

    print(f"\n{'='*70}")
    print(f"ANALYZING {region_name.upper()}")
    print(f"{'='*70}")

    # Load skeleton
    skeleton_path = os.path.join(region_info['path'], region_info['skeleton_file'])
    skeleton = load_skeleton(skeleton_path)

    if skeleton is None:
        print(f"  ERROR: Could not load skeleton")
        return None

    # Find catalog file if not specified
    catalog_file = region_info['catalog_file']
    if catalog_file is None:
        catalog_file = find_catalog_file(region_info['path'], region_name)

    if catalog_file is None:
        print(f"  ERROR: No catalog file found")
        return None

    catalog_path = os.path.join(region_info['path'], catalog_file)

    # Load cores
    cores = load_core_catalog_v2(catalog_path, region_info['distance'])

    if len(cores) < 10:
        print(f"  ERROR: Not enough cores ({len(cores)})")
        return None

    # Compute NN spacing using simplified method
    print(f"\n  Computing NN spacing using simplified 2D method...")
    spacings = compute_nn_spacing_simplified(cores, region_info['distance'])

    if not spacings or len(spacings) < 5:
        print(f"  ERROR: Not enough spacings computed")
        return None

    region_median = np.median(spacings)
    region_std = np.std(spacings)
    region_sem = region_std / np.sqrt(len(spacings))

    lambda_over_W = region_median / 0.1

    # Compute statistics
    percentiles = np.percentile(spacings, [16, 50, 84])

    result = {
        'region': region_name,
        'distance': region_info['distance'],
        'n_cores': len(cores),
        'n_spacings': len(spacings),
        'nn_median_spacing': region_median,
        'nn_std': region_std,
        'nn_sem': region_sem,
        'nn_lambda_over_W': lambda_over_W,
        'nn_percentiles': {
            'p16': percentiles[0],
            'p50': percentiles[1],
            'p84': percentiles[2],
        },
        'pairwise_median': region_info['pairwise_median_pc'],
        'pairwise_lambda_W': region_info['pairwise_lambda_W'],
        'bias_factor': region_info['pairwise_median_pc'] / region_median if region_median > 0 else None,
    }

    print(f"\n  RESULTS:")
    print(f"    Distance: {region_info['distance']} pc")
    print(f"    N_cores: {len(cores)}")
    print(f"    N_spacings: {len(spacings)}")
    print(f"    NN median spacing: {region_median:.4f} ± {region_sem:.4f} pc")
    print(f"    NN 16-84 percentiles: {percentiles[0]:.4f} - {percentiles[2]:.4f} pc")
    print(f"    NN λ/W: {lambda_over_W:.2f}")
    print(f"    Pairwise median: {region_info['pairwise_median_pc']:.3f} pc (λ/W = {region_info['pairwise_lambda_W']:.2f})")
    print(f"    Ratio (pairwise/NN): {result['bias_factor']:.2f}×")

    return result


# Main analysis
if __name__ == '__main__':
    print("=" * 70)
    print("FULL NEAREST-NEIGHBOR SPACING ANALYSIS FOR HGBS REGIONS")
    print("=" * 70)
    print()
    print("This analysis computes proper nearest-neighbor spacing")
    print("for all 8 HGBS regions using a simplified 2D spatial method.")
    print()

    results = []
    successful_regions = []
    failed_regions = []

    for region_name, region_info in HGBS_REGIONS.items():
        try:
            result = analyze_region_simplified(region_name, region_info)
            if result:
                results.append(result)
                successful_regions.append(region_name)
            else:
                failed_regions.append(region_name)
        except Exception as e:
            print(f"\nERROR analyzing {region_name}: {e}")
            import traceback
            traceback.print_exc()
            failed_regions.append(region_name)

    print("\n" + "="*70)
    print("SUMMARY OF ALL HGBS REGIONS")
    print("="*70)
    print()

    print(f"Successful: {len(successful_regions)} regions")
    print(f"Failed: {len(failed_regions)} regions")
    print()

    if results:
        # Print table header
        print(f"{'Region':<12} {'N_cores':<8} {'N_spacings':<10} {'NN_median':<12} {'NN_λ/W':<10} {'Pairwise':<10} {'Ratio':<8}")
        print("-"*75)

        nn_medians = []
        nn_lambda_Ws = []

        for r in results:
            print(f"{r['region']:<12} {r['n_cores']:<8} {r['n_spacings']:<10} "
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

            print(f"Robust regions (N={len(robust_results)}):")
            print(f"  Total cores: {sum(r['n_cores'] for r in robust_results)}")
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
            print(f"  Total cores: {sum(r['n_cores'] for r in results)}")
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
        print("INTERPRETATION:")
        print("-"*40)
        if weighted_mean_nn > pairwise_weighted * 0.5:
            print("NN spacing is similar to or larger than pairwise median.")
            print("This does NOT show the L/3 convergence bias (which would make")
            print("pairwise >> NN). This suggests real HGBS filaments do not")
            print("follow the idealized uniform distribution model.")
        elif weighted_mean_nn < pairwise_weighted * 0.3:
            print("NN spacing is MUCH smaller than pairwise median.")
            print("This IS consistent with L/3 convergence bias, suggesting")
            print("the pairwise median significantly overestimates true spacing.")
        else:
            print("NN spacing is moderately smaller than pairwise median.")
            print("This suggests partial bias effect or complex filament structure.")

        # Save results to JSON
        output_file = "full_nn_spacing_results.json"
        output_data = {
            'analysis_date': '2026-05-01',
            'method': 'Simplified 2D nearest-neighbor spacing',
            'n_regions_analyzed': len(results),
            'successful_regions': successful_regions,
            'failed_regions': failed_regions,
            'results': results,
            'robust_weighted_mean_nn': float(weighted_mean_nn) if robust_results else None,
            'robust_weighted_mean_lambda_W': float(weighted_mean_lambda_W) if robust_results else None,
            'robust_weighted_uncertainty': float(weighted_uncertainty) if robust_results else None,
            'full_weighted_mean_nn': float(all_weighted_mean) if len(results) >= 4 else None,
            'full_weighted_mean_lambda_W': float(all_weighted_lambda_W) if len(results) >= 4 else None,
            'full_weighted_uncertainty': float(all_weighted_uncertainty) if len(results) >= 4 else None,
            'pairwise_weighted_mean': float(pairwise_weighted),
            'bias_factor': float(pairwise_weighted/weighted_mean_nn) if robust_results else None,
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\nResults saved to: {output_file}")

    else:
        print("No successful analyses!")
