#!/usr/bin/env python3
"""
Proper Nearest-Neighbor Analysis Using Skeleton Data

This script performs the correct NN analysis by:
1. Loading DisPerSE skeleton FITS files
2. Loading HGBS core catalogs
3. Associating cores with filaments using skeleton data
4. Ordering cores along each filament spine
5. Computing proper NN spacings (not just spatial proximity)

Author: ASTRA Analysis System
Date: 2026-05-05
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json
from scipy import ndimage
from collections import defaultdict
import sys

try:
    from astropy.io import fits
    from astropy import units as u
    from astropy.coordinates import SkyCoord
    from astropy.wcs import WCS
    ASTROPY_AVAILABLE = True
except ImportError as e:
    print(f"Error: {e}")
    print("astropy is required for this analysis")
    sys.exit(1)


def parse_hgbs_catalog_v2(catalog_file):
    """
    Parse HGBS catalog files, handling multiple formats.

    Returns list of cores with RA, Dec in degrees.
    """
    cores = []

    with open(catalog_file, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    # Try different coordinate formats
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip comment lines
        if line.startswith(('|', '!', '#')):
            continue

        parts = line.split()
        if len(parts) < 4:
            continue

        # Try to parse first column as number
        try:
            core_id = int(parts[0])
        except ValueError:
            continue

        # RA and Dec are in columns 3 and 4 (indices 2 and 3)
        # Format can be: "05:40:58.09" (colon) or "04 09 24.10" (space)
        try:
            ra_str = parts[2]
            dec_str = parts[3]

            # Handle space-separated format (e.g., Taurus)
            if ':' not in ra_str:
                # Format: "04 09 24.10" -> "04:09:24.10"
                ra_parts = ra_str.split()
                if len(ra_parts) == 3:
                    ra_str = f"{ra_parts[0]}:{ra_parts[1]}:{ra_parts[2]}"

            # Handle space-separated declination
            if ':' not in dec_str:
                dec_parts = dec_str.split()
                if len(dec_parts) == 3:
                    dec_str = f"{dec_parts[0]}:{dec_parts[1]}:{dec_parts[2]}"

            # Parse coordinates
            coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))

            cores.append({
                'id': core_id,
                'ra': coord.ra.deg,
                'dec': coord.dec.deg,
                'coord': coord
            })
        except Exception as e:
            continue

    print(f"    Parsed {len(cores)} cores")
    return cores


def load_skeleton_data(skeleton_file):
    """
    Load DisPerSE skeleton FITS file.

    Returns skeleton data array and WCS.
    """
    print(f"    Loading skeleton: {skeleton_file}")

    hdul = fits.open(skeleton_file)
    skeleton_data = hdul[0].data.astype(np.float64)
    header = hdul[0].header

    # Get WCS
    try:
        wcs = WCS(header)
        print(f"    Skeleton shape: {skeleton_data.shape}")
        print(f"    WCS: {wcs}")
    except Exception as e:
        print(f"    Warning: No WCS in header: {e}")
        wcs = None

    hdul.close()

    return skeleton_data, wcs


def extract_filament_spines(skeleton_data, threshold=0.1, min_length=20):
    """
    Extract filament spines from skeleton data.

    Returns list of filaments, each with ordered pixel coordinates.
    """
    print(f"    Extracting filament spines (threshold={threshold}, min_length={min_length})...")

    # Threshold the skeleton
    skeleton_mask = skeleton_data > threshold

    # Label connected components
    labeled, num_features = ndimage.label(skeleton_mask)

    print(f"    Found {num_features} candidate filaments")

    # Extract each filament
    filaments = []

    for i in range(1, num_features + 1):
        filament_pixels = np.where(labeled == i)
        n_pixels = len(filament_pixels[0])

        if n_pixels < min_length:
            continue

        # Get pixel coordinates
        y_coords = filament_pixels[0]
        x_coords = filament_pixels[1]

        # Extract skeleton values
        values = skeleton_data[y_coords, x_coords]

        # Sort by position to get approximate ordering
        order = np.lexsort((x_coords, y_coords))
        ordered_y = y_coords[order]
        ordered_x = x_coords[order]
        ordered_values = values[order]

        filaments.append({
            'id': i,
            'pixels_y': ordered_y,
            'pixels_x': ordered_x,
            'values': ordered_values,
            'length': n_pixels,
            'bounds': {
                'y_min': np.min(ordered_y),
                'y_max': np.max(ordered_y),
                'x_min': np.min(ordered_x),
                'x_max': np.max(ordered_x),
            }
        })

    print(f"    Extracted {len(filaments)} filaments with >= {min_length} pixels")
    return filaments


def associate_cores_with_filaments(cores, filaments, wcs, max_distance_pixels=15):
    """
    Associate cores with filaments based on proximity.

    Returns dictionary mapping core_id -> filament_id
    """
    print(f"    Associating cores with filaments (max distance: {max_distance_pixels} pixels)...")

    if wcs is None:
        print("    Warning: No WCS available, skipping core-filament association")
        return {}

    core_filament_map = {}

    for core in cores:
        try:
            # Convert core position to pixel coordinates
            from astropy.wcs import utils
            px, py = utils.skycoord_to_pixel(wcs, core['coord'])

            # Find nearest filament
            best_filament_id = None
            best_distance = float('inf')

            for fil in filaments:
                # Check if core is within filament bounds (plus margin)
                if (px < fil['bounds']['x_min'] - max_distance_pixels or
                    px > fil['bounds']['x_max'] + max_distance_pixels or
                    py < fil['bounds']['y_min'] - max_distance_pixels or
                    py > fil['bounds']['y_max'] + max_distance_pixels):
                    continue

                # Calculate minimum distance to this filament
                dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                min_dist = np.sqrt(np.min(dist_sq))

                if min_dist < best_distance and min_dist < max_distance_pixels:
                    best_distance = min_dist
                    best_filament_id = fil['id']

            if best_filament_id is not None:
                core_filament_map[core['id']] = best_filament_id

        except Exception as e:
            continue

    n_associated = len(core_filament_map)
    print(f"    Associated {n_associated}/{len(cores)} cores with filaments")

    return core_filament_map


def order_cores_along_filaments(cores, filaments, core_filament_map, wcs):
    """
    Order cores along each filament spine.

    Returns dictionary mapping filament_id -> ordered list of core_ids
    """
    print(f"    Ordering cores along filaments...")

    if wcs is None:
        return {}

    filament_cores = defaultdict(list)

    # Group cores by filament
    for core in cores:
        if core['id'] not in core_filament_map:
            continue

        fil_id = core_filament_map[core['id']]
        filament_cores[fil_id].append(core)

    # Order cores along each filament
    ordered_filament_cores = {}

    for fil_id, core_list in filament_cores.items():
        if len(core_list) < 2:
            continue

        # Get filament data
        fil = next((f for f in filaments if f['id'] == fil_id), None)
        if fil is None:
            continue

        try:
            # Convert cores to pixel coordinates
            from astropy.wcs import utils
            core_positions = []

            for core in core_list:
                px, py = utils.skycoord_to_pixel(wcs, core['coord'])

                # Find position along filament (closest pixel index)
                dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                closest_idx = np.argmin(dist_sq)

                core_positions.append((closest_idx, core))

            # Sort by position along spine
            core_positions.sort(key=lambda x: x[0])

            # Store ordered core IDs
            ordered_filament_cores[fil_id] = [c[1]['id'] for c in core_positions]

        except Exception as e:
            continue

    n_filaments_with_cores = len(ordered_filament_cores)
    total_cores_ordered = sum(len(cores) for cores in ordered_filament_cores.values())

    print(f"    Ordered {total_cores_ordered} cores along {n_filaments_with_cores} filaments")

    return ordered_filament_cores


def compute_nn_spacing(cores, filaments, ordered_filament_cores, distance_pc, filament_width_pc=0.1):
    """
    Compute nearest-neighbor spacing for cores ordered along filaments.

    Returns array of NN spacings in parsecs.
    """
    print(f"    Computing NN spacing...")

    # Create core ID -> coordinate mapping
    core_coords = {core['id']: core for core in cores}

    all_spacings = []

    for fil_id, core_ids in ordered_filament_cores.items():
        if len(core_ids) < 2:
            continue

        # Get coordinates for cores on this filament
        filament_core_coords = [core_coords[cid] for cid in core_ids]

        # Compute spacings between adjacent cores
        for i in range(len(filament_core_coords) - 1):
            coord1 = filament_core_coords[i]['coord']
            coord2 = filament_core_coords[i + 1]['coord']

            # Compute angular separation
            sep = coord1.separation(coord2)

            # Convert to physical distance
            sep_pc = sep.radian * distance_pc
            all_spacings.append(sep_pc)

    all_spacings = np.array(all_spacings)

    if len(all_spacings) > 0:
        print(f"    Computed {len(all_spacings)} NN spacings")
        print(f"    Median: {np.median(all_spacings):.4f} pc")
        print(f"    Mean: {np.mean(all_spacings):.4f} pc")
        print(f"    Std: {np.std(all_spacings):.4f} pc")

    return all_spacings


def analyze_region(name, skeleton_file, catalog_file, distance_pc, filament_width_pc=0.1):
    """
    Analyze a single HGBS region with proper NN analysis using skeleton data.

    Returns dictionary with analysis results.
    """
    print(f"\n{'='*80}")
    print(f"ANALYZING: {name}")
    print(f"{'='*80}")
    print(f"Skeleton: {skeleton_file}")
    print(f"Catalog: {catalog_file}")
    print(f"Distance: {distance_pc} pc")

    # Load skeleton data
    skeleton_data, wcs = load_skeleton_data(skeleton_file)

    # Extract filament spines
    filaments = extract_filament_spines(skeleton_data, threshold=0.1, min_length=20)

    # Load core catalog
    print(f"  Loading catalog...")
    cores = parse_hgbs_catalog_v2(catalog_file)
    print(f"  Total cores: {len(cores)}")

    if len(cores) == 0:
        print(f"  ERROR: No cores loaded!")
        return None

    # Associate cores with filaments
    core_filament_map = associate_cores_with_filaments(cores, filaments, wcs, max_distance_pixels=15)

    if len(core_filament_map) == 0:
        print(f"  ERROR: No cores associated with filaments!")
        return None

    # Order cores along filaments
    ordered_filament_cores = order_cores_along_filaments(cores, filaments, core_filament_map, wcs)

    if len(ordered_filament_cores) == 0:
        print(f"  ERROR: No cores ordered along filaments!")
        return None

    # Compute NN spacing
    nn_spacings = compute_nn_spacing(cores, filaments, ordered_filament_cores, distance_pc, filament_width_pc)

    if len(nn_spacings) == 0:
        print(f"  ERROR: No NN spacings computed!")
        return None

    # Compute statistics
    nn_median = np.median(nn_spacings)
    nn_mean = np.mean(nn_spacings)
    nn_std = np.std(nn_spacings)
    nn_sem = nn_std / np.sqrt(len(nn_spacings))

    # Compute λ/W
    nn_lambda_w = nn_median / filament_width_pc

    print(f"\n  RESULTS:")
    print(f"  N_cores_total: {len(cores)}")
    print(f"  N_cores_associated: {len(core_filament_map)}")
    print(f"  N_filaments_with_cores: {len(ordered_filament_cores)}")
    print(f"  N_nn_pairs: {len(nn_spacings)}")
    print(f"  NN_median: {nn_median:.4f} pc")
    print(f"  NN_mean: {nn_mean:.4f} pc")
    print(f"  NN_std: {nn_std:.4f} pc")
    print(f"  NN_sem: {nn_sem:.4f} pc")
    print(f"  λ/W (NN): {nn_lambda_w:.2f}")

    # Check for PM/L3 convergence problem
    if len(cores) >= 500:
        print(f"\n  *** PM/L3 CONVERGENCE WARNING ***")
        print(f"  N_cores = {len(cores)} ≥ 500: PM value likely unreliable")
        print(f"  *******************************")

    # Return results
    results = {
        'name': name,
        'n_cores_total': len(cores),
        'n_cores_associated': len(core_filament_map),
        'n_filaments_with_cores': len(ordered_filament_cores),
        'n_nn_pairs': len(nn_spacings),
        'distance_pc': distance_pc,
        'filament_width_pc': filament_width_pc,
        'nn_median_pc': nn_median,
        'nn_mean_pc': nn_mean,
        'nn_std_pc': nn_std,
        'nn_sem_pc': nn_sem,
        'nn_lambda_w': nn_lambda_w,
        'nn_spacings': nn_spacings.tolist(),
    }

    return results


def run_all_regions():
    """
    Run proper NN analysis for all HGBS regions with skeleton data.
    """
    print("="*80)
    print("PROPER NN ANALYSIS USING SKELETON DATA")
    print("="*80)
    print("\nThis analysis performs the correct NN measurement by:")
    print("1. Loading DisPerSE skeleton FITS files")
    print("2. Associating cores with filaments using skeleton data")
    print("3. Ordering cores along each filament spine")
    print("4. Computing NN spacings for adjacent cores on each filament")
    print("="*80)

    base_path = Path('/Users/gjw255/astrodata/SWARM/ASTRA')

    # Region configurations with skeleton and catalog files
    regions = [
        {
            'name': 'Orion B',
            'skeleton': base_path / 'HGBS_ORIB' / 'HGBS_orionB_skeleton_map_thresh50.fits',
            'catalog': base_path / 'HGBS_ORIB' / 'HGBS_orionb_derived_core_catalog.txt',
            'distance_pc': 386,
        },
        {
            'name': 'Taurus',
            'skeleton': base_path / 'HGBS_TAURUS' / 'HGBS_taurusL1495_skeleton_map_thresh50.fits',
            'catalog': base_path / 'HGBS_TAURUS' / 'HGBS_taurusL1495_derived_core_catalog.txt',
            'distance_pc': 135,
        },
        {
            'name': 'Serpens',
            'skeleton': base_path / 'HGBS_SERPENS' / 'HGBS_serpens_skeleton_map_thresh50.fits',
            'catalog': base_path / 'HGBS_SERPENS' / 'HGBS_serpens_observed_core_catalog.txt',
            'distance_pc': 436,
        },
        {
            'name': 'Perseus',
            'skeleton': base_path / 'HGBS_PERSEUS' / 'HGBS_perseus_skeleton_map_thresh50.fits',
            'catalog': base_path / 'HGBS_PERSEUS' / 'HGBS_PERSEUS' / 'HGBS_perseus_derived_core_catalog.txt',
            'distance_pc': 296,
        },
        {
            'name': 'IC5146',
            'skeleton': base_path / 'HGBS_IC5146' / 'HGBS_ic5146_skeleton_map.fits',
            'catalog': base_path / 'HGBS_IC5146' / 'HGBS_ic5146_catalog.txt',  # May not exist
            'distance_pc': 463,
        },
    ]

    all_results = {}

    for region_config in regions:
        name = region_config['name']
        skeleton_file = region_config['skeleton']
        catalog_file = region_config['catalog']

        # Check if files exist
        if not Path(skeleton_file).exists():
            print(f"\nSkipping {name}: skeleton file not found")
            continue

        if not Path(catalog_file).exists():
            print(f"\nSkipping {name}: catalog file not found")
            continue

        result = analyze_region(
            name=name,
            skeleton_file=str(skeleton_file),
            catalog_file=str(catalog_file),
            distance_pc=region_config['distance_pc'],
            filament_width_pc=0.1,
        )

        if result:
            all_results[name] = result

    # Generate summary
    print(f"\n{'='*80}")
    print("SUMMARY RESULTS")
    print(f"{'='*80}")

    print(f"\n{'Region':<15} {'N_tot':>8} {'N_assoc':>8} {'N_fil':>8} {'N_nn':>8} {'NN λ/W':>10} {'NN SEM':>10}")
    print("-"*80)

    for name, res in all_results.items():
        print(f"{name:<15} {res['n_cores_total']:>8} {res['n_cores_associated']:>8} "
              f"{res['n_filaments_with_cores']:>8} {res['n_nn_pairs']:>8} "
              f"{res['nn_lambda_w']:>10.2f} {res['nn_sem_pc']:>10.4f}")

    # Calculate weighted statistics
    if all_results:
        print(f"\n{'='*80}")
        print("WEIGHTED STATISTICS")
        print(f"{'='*80}")

        total_cores = sum(r['n_cores_associated'] for r in all_results.values())
        weighted_nn = sum(r['n_cores_associated'] * r['nn_lambda_w'] for r in all_results.values()) / total_cores

        print(f"Weighted NN λ/W (all regions): {weighted_nn:.2f}")
        print(f"Total cores analyzed: {total_cores}")

        # Compare with published PM values
        print(f"\nComparison with published PM values:")
        for name, res in all_results.items():
            pm_values = {'Orion B': 3.13, 'Taurus': 1.98, 'Serpens': 2.5}
            if name in pm_values:
                pm_val = pm_values[name]
                nn_val = res['nn_lambda_w']
                ratio = pm_val / nn_val
                print(f"  {name}: PM={pm_val:.2f}, NN={nn_val:.2f}, PM/NN={ratio:.2f}")

    # Save results
    output_file = Path('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/nn_analysis_skeleton_based.json')
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return all_results


if __name__ == '__main__':
    results = run_all_regions()

    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
