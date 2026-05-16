#!/usr/bin/env python3
"""
Simplified NN Analysis for Taurus and Perseus Only
"""

import numpy as np
import sys
from pathlib import Path
import json
from scipy import ndimage
from collections import defaultdict

try:
    from astropy.io import fits
    from astropy import units as u
    from astropy.coordinates import SkyCoord
    from astropy.wcs import WCS, utils
    ASTROPY_AVAILABLE = True
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(1)


def parse_hgbs_catalog_v2(catalog_file):
    """Parse HGBS catalog files - handles both space-separated and colon-separated formats."""
    cores = []
    with open(catalog_file, 'r', encoding='latin-1') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith(('|', '!', '#')):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            core_id = int(parts[0])
        except ValueError:
            continue
        try:
            # Check format by looking at parts[2] (RA column)
            ra_candidate = parts[2]
            dec_candidate = parts[3] if len(parts) > 3 else ""

            if ':' in ra_candidate:
                # Perseus format: "03:23:04.42" "+30:34:44.1"
                ra_str = ra_candidate
                dec_str = dec_candidate
            else:
                # Taurus format: "04" "09" "24.10" "+28" "47" "23"
                if len(parts) >= 8:
                    ra_str = f"{parts[2]} {parts[3]} {parts[4]}"
                    dec_str = f"{parts[5]} {parts[6]} {parts[7]}"
                else:
                    continue

            coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
            cores.append({'id': core_id, 'ra': coord.ra.deg, 'dec': coord.dec.deg, 'coord': coord})
        except Exception as e:
            continue
    print(f"    Parsed {len(cores)} cores")
    return cores


def load_skeleton_data(skeleton_file):
    """Load skeleton FITS file and extract WCS."""
    print(f"  Loading skeleton file: {skeleton_file}")
    with fits.open(skeleton_file) as hdul:
        data = hdul[0].data
        try:
            wcs = WCS(hdul[0].header)
        except Exception:
            wcs = None
    print(f"    Skeleton shape: {data.shape}")
    return data, wcs


def extract_filament_spines(skeleton_data, threshold=0.01, min_length=5):
    """Extract filament spines from skeleton data."""
    print(f"  Extracting filament spines (threshold={threshold}, min_length={min_length})...")
    binary = skeleton_data > threshold
    labeled, num_features = ndimage.label(binary)
    filaments = []

    for label in range(1, num_features + 1):
        mask = labeled == label
        pixels = np.argwhere(mask)
        if len(pixels) < min_length:
            continue
        y_coords, x_coords = pixels[:, 0], pixels[:, 1]
        filaments.append({
            'id': label,
            'pixels_y': y_coords,
            'pixels_x': x_coords,
            'bounds': {
                'y_min': int(y_coords.min()),
                'y_max': int(y_coords.max()),
                'x_min': int(x_coords.min()),
                'x_max': int(x_coords.max()),
            }
        })

    print(f"    Found {len(filaments)} filaments")
    return filaments


def associate_cores_with_filaments(cores, filaments, wcs, max_distance_pixels=50):
    """Associate cores with nearest filaments."""
    print(f"  Associating cores with filaments (max_distance={max_distance_pixels} pixels)...")
    core_filament_map = {}
    for core in cores:
        try:
            px, py = utils.skycoord_to_pixel(wcs, core['coord'])
            best_filament_id = None
            best_distance = float('inf')
            for fil in filaments:
                if (px < fil['bounds']['x_min'] - max_distance_pixels or
                    px > fil['bounds']['x_max'] + max_distance_pixels or
                    py < fil['bounds']['y_min'] - max_distance_pixels or
                    py > fil['bounds']['y_max'] + max_distance_pixels):
                    continue
                dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                min_dist = np.sqrt(np.min(dist_sq))
                if min_dist < best_distance and min_dist < max_distance_pixels:
                    best_distance = min_dist
                    best_filament_id = fil['id']
            if best_filament_id is not None:
                core_filament_map[core['id']] = best_filament_id
        except Exception as e:
            continue
    print(f"    Associated {len(core_filament_map)}/{len(cores)} cores")
    return core_filament_map


def order_cores_along_filaments(cores, filaments, core_filament_map, wcs):
    """Order cores along each filament."""
    print(f"  Ordering cores along filaments...")
    filament_cores = defaultdict(list)
    for core in cores:
        if core['id'] not in core_filament_map:
            continue
        fil_id = core_filament_map[core['id']]
        filament_cores[fil_id].append(core)

    ordered_filament_cores = {}
    for fil_id, core_list in filament_cores.items():
        if len(core_list) < 2:
            continue
        fil = next((f for f in filaments if f['id'] == fil_id), None)
        if fil is None:
            continue
        try:
            core_positions = []
            for core in core_list:
                px, py = utils.skycoord_to_pixel(wcs, core['coord'])
                dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                closest_idx = np.argmin(dist_sq)
                core_positions.append((closest_idx, core))
            core_positions.sort(key=lambda x: x[0])
            ordered_filament_cores[fil_id] = [c[1]['id'] for c in core_positions]
        except Exception as e:
            continue

    n_filaments = len(ordered_filament_cores)
    total_cores = sum(len(cores) for cores in ordered_filament_cores.values())
    print(f"    Ordered {total_cores} cores along {n_filaments} filaments")
    return ordered_filament_cores


def compute_nn_spacing(cores, filaments, ordered_cores, distance_pc, filament_width_pc):
    """Compute NN spacings."""
    print(f"  Computing NN spacings...")
    nn_spacings = []
    pixel_scale_pc = distance_pc * np.tan(np.deg2rad(0.00444))

    core_dict = {c['id']: c for c in cores}

    for fil_id, core_ids in ordered_cores.items():
        for i in range(len(core_ids) - 1):
            core1 = core_dict[core_ids[i]]
            core2 = core_dict[core_ids[i + 1]]
            coord1 = SkyCoord(core1['ra'], core1['dec'], unit='deg')
            coord2 = SkyCoord(core2['ra'], core2['dec'], unit='deg')
            sep_pc = coord1.separation(coord2).to(u.pc).value
            nn_spacings.append(sep_pc)

    print(f"    Computed {len(nn_spacings)} NN spacings")
    return nn_spacings


def analyze_region(name, skeleton_file, catalog_file, distance_pc, filament_width_pc):
    """Analyze one region."""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {name}")
    print(f"{'='*80}")

    skeleton_data, wcs = load_skeleton_data(skeleton_file)
    filaments = extract_filament_spines(skeleton_data, threshold=0.01, min_length=5)
    cores = parse_hgbs_catalog_v2(catalog_file)
    print(f"  Total cores: {len(cores)}")

    if len(cores) == 0:
        return None

    core_filament_map = associate_cores_with_filaments(cores, filaments, wcs, max_distance_pixels=50)
    if len(core_filament_map) == 0:
        return None

    ordered_cores = order_cores_along_filaments(cores, filaments, core_filament_map, wcs)
    if len(ordered_cores) == 0:
        return None

    nn_spacings = compute_nn_spacing(cores, filaments, ordered_cores, distance_pc, filament_width_pc)
    if len(nn_spacings) == 0:
        return None

    nn_median = np.median(nn_spacings)
    nn_lambda_w = nn_median / filament_width_pc

    print(f"\n  RESULTS:")
    print(f"  N_cores: {len(cores)}")
    print(f"  N_associated: {len(core_filament_map)}")
    print(f"  N_spacings: {len(nn_spacings)}")
    print(f"  NN_median: {nn_median:.4f} pc")
    print(f"  NN λ/W: {nn_lambda_w:.2f}")

    return {
        'name': name,
        'n_cores_total': len(cores),
        'n_cores_associated': len(core_filament_map),
        'n_nn_pairs': len(nn_spacings),
        'distance_pc': distance_pc,
        'nn_median_pc': nn_median,
        'nn_lambda_w': nn_lambda_w,
    }


def main():
    base_path = Path('/Users/gjw255/astrodata/SWARM/ASTRA')

    regions = [
        {
            'name': 'Taurus',
            'skeleton': base_path / 'HGBS_TAURUS' / 'HGBS_taurusL1495_skeleton_map_thresh15.fits',
            'catalog': base_path / 'HGBS_TAURUS' / 'HGBS_taurusL1495_derived_core_catalog.txt',
            'distance_pc': 135,
        },
        {
            'name': 'Perseus',
            'skeleton': base_path / 'HGBS_PERSEUS' / 'HGBS_perseus_skeleton_map_thresh50.fits',
            'catalog': base_path / 'HGBS_PERSEUS' / 'HGBS_PERSEUS' / 'HGBS_perseus_derived_core_catalog.txt',
            'distance_pc': 296,
        },
    ]

    print("="*80)
    print("NN ANALYSIS: Taurus and Perseus Only")
    print("="*80)

    results = {}
    for region_config in regions:
        name = region_config['name']
        skeleton_file = region_config['skeleton']
        catalog_file = region_config['catalog']

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
            results[name] = result

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    if results:
        print(f"\n{'Region':<15} {'N_cores':>10} {'N_assoc':>10} {'N_spacings':>12} {'NN λ/W':>10}")
        print("-"*80)
        for name, res in results.items():
            print(f"{name:<15} {res['n_cores_total']:>10} {res['n_cores_associated']:>10} "
                  f"{res['n_nn_pairs']:>12} {res['nn_lambda_w']:>10.2f}")

        total_cores = sum(r['n_cores_associated'] for r in results.values())
        if total_cores > 0:
            weighted_nn = sum(r['n_cores_associated'] * r['nn_lambda_w'] for r in results.values()) / total_cores
            print(f"\nWeighted NN λ/W (Taurus + Perseus): {weighted_nn:.2f}")
            print(f"Total cores: {total_cores}")

    print("\nDone!")


if __name__ == '__main__':
    main()
