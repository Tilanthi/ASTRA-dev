#!/usr/bin/env python3
"""
Complete Nearest-Neighbor Analysis for All HGBS Regions

This script addresses the referee's concern by performing a comprehensive
NN analysis for all available HGBS regions with skeleton and core catalog data.

Key improvements over previous versions:
1. Handles all catalog formats (derived, observed, various naming conventions)
2. Robust file finding in subdirectories
3. Proper distance handling for all regions
4. Comprehensive error handling and reporting
"""

import numpy as np
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import astropy.units as u
from scipy.spatial import cKDTree
from scipy import ndimage
from collections import defaultdict
import os
import glob
import json
import warnings
warnings.filterwarnings('ignore')

# HGBS regions with Gaia DR3 distances (pc)
HGBS_REGIONS = {
    'Taurus': {
        'distance': 135,
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS',
    },
    'OrionB': {
        'distance': 386,
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB',
    },
    'Aquila': {
        'distance': 436,
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA',
        'subdir': 'HGBS_AQUILA',
    },
    'Perseus': {
        'distance': 296,
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS',
        'subdir': 'HGBS_PERSEUS',
    },
    'Ophiuchus': {
        'distance': 137,
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH',
    },
    'Serpens': {
        'distance': 458,
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS',
    },
    'TMC1': {
        'distance': 135,
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1',
    },
    'CRA': {
        'distance': 150,
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_CRA',
    },
}


def find_data_files(region_name, region_info):
    """Find skeleton and catalog files in a region directory."""
    base_path = region_info['path']
    subdir = region_info.get('subdir')

    # Check subdirectory if specified
    if subdir:
        search_path = os.path.join(base_path, subdir)
    else:
        search_path = base_path

    # Find skeleton files
    skeleton_files = glob.glob(os.path.join(search_path, '*skeleton*.fits'))
    if not skeleton_files:
        # Try base path if not found in subdirectory
        skeleton_files = glob.glob(os.path.join(base_path, '*skeleton*.fits'))

    if skeleton_files:
        # Prefer standard skeleton file
        for f in skeleton_files:
            if 'skeleton_map.fits' in f and 'thresh' not in f:
                skeleton_file = f
                break
        else:
            skeleton_file = skeleton_files[0]
    else:
        skeleton_file = None

    # Find core catalog files (prefer derived catalog)
    catalog_files = glob.glob(os.path.join(search_path, '*derived*catalog*.txt'))
    if not catalog_files:
        catalog_files = glob.glob(os.path.join(search_path, '*catalog*.txt'))

    if not catalog_files:
        # Try base path if not found in subdirectory
        catalog_files = glob.glob(os.path.join(base_path, '*derived*catalog*.txt'))
    if not catalog_files:
        catalog_files = glob.glob(os.path.join(base_path, '*catalog*.txt'))

    # Also try observed catalog if derived not found
    if not catalog_files:
        catalog_files = glob.glob(os.path.join(search_path, '*observed*catalog*.txt'))
    if not catalog_files:
        catalog_files = glob.glob(os.path.join(base_path, '*observed*catalog*.txt'))

    if catalog_files:
        catalog_file = catalog_files[0]
    else:
        catalog_file = None

    return skeleton_file, catalog_file


def load_skeleton(skeleton_file):
    """Load skeleton map from FITS file and extract skeleton pixels."""
    try:
        with fits.open(skeleton_file) as hdul:
            data = hdul[0].data
            header = hdul[0].header

        # Get WCS for coordinate conversion
        wcs = WCS(header)

        # Find skeleton pixels (non-zero values)
        skeleton_mask = data > 0
        skeleton_y, skeleton_x = np.where(skeleton_mask)

        if len(skeleton_x) == 0:
            return None

        # Convert pixel coordinates to world coordinates (RA/Dec)
        world_coords = wcs.pixel_to_world(skeleton_x, skeleton_y)
        ra_skel = world_coords.ra.deg
        dec_skel = world_coords.dec.deg

        # Also store pixel coordinates for distance calculations
        skeleton_pixels = np.column_stack([skeleton_y, skeleton_x])

        return {
            'ra': ra_skel,
            'dec': dec_skel,
            'pixels': skeleton_pixels,
            'wcs': wcs,
            'data': data,
            'n_pixels': len(skeleton_x),
        }
    except Exception as e:
        print(f"    Error loading skeleton: {e}")
        return None


def load_core_catalog(catalog_file):
    """Load core catalog from text file.

    Handles multiple HGBS catalog formats:
    1. Format 1 (Taurus, OrionB, Perseus, Serpens, TMC1): RA/Dec in source name (column 2)
    2. Format 2 (Aquila, Ophiuchus, CRA): RA/Dec in columns 3-4 (sexagesimal HH:MM:SS format)
    """
    cores = []

    # Try different encodings
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

    for encoding in encodings:
        try:
            with open(catalog_file, 'r', encoding=encoding) as f:
                # Skip header lines (start with !, #, or |)
                for line in f:
                    if line.startswith('!') or line.startswith('#') or line.startswith('|'):
                        continue
                    if not line.strip():
                        continue

                    # Try parsing as HGBS catalog format
                    parts = line.split()
                    if len(parts) < 5:
                        continue

                    # Try Format 2 first (Aquila/Ophiuchus/CRA style)
                    # Columns 3-4 contain RA/Dec in HH:MM:SS format
                    try:
                        ra_str = parts[2]
                        dec_str = parts[3]

                        # Check if this looks like HH:MM:SS format
                        if ':' in ra_str and ':' in dec_str:
                            # Parse RA from HH:MM:SS.ss format
                            ra_parts = ra_str.split(':')
                            if len(ra_parts) == 3:
                                ra_h = float(ra_parts[0])
                                ra_m = float(ra_parts[1])
                                ra_s = float(ra_parts[2])
                                ra_deg = 15 * (ra_h + ra_m/60 + ra_s/3600)

                                # Parse Dec from DD:MM:SS.ss format
                                dec_parts = dec_str.split(':')
                                if len(dec_parts) == 3:
                                    # Handle negative declination
                                    dec_d = float(dec_parts[0])
                                    dec_m = float(dec_parts[1])
                                    dec_s = float(dec_parts[2])
                                    dec_deg = abs(dec_d) + dec_m/60 + dec_s/3600
                                    if dec_d < 0:
                                        dec_deg = -dec_deg

                                    source_name = parts[1] if len(parts) > 1 else f"Core_{len(cores)}"

                                    cores.append({
                                        'ra': ra_deg,
                                        'dec': dec_deg,
                                        'id': source_name,
                                    })
                                    continue  # Successfully parsed, skip to next line
                    except Exception:
                        pass  # Not Format 2, try Format 1

                    # Try Format 1 (Taurus style): RA/Dec in source name (column 2)
                    # Format: HHMMSS.s+DDMMSS or HHMMSS.s-DDMMSS
                    try:
                        source_name = parts[1]

                        if '+' in source_name or '-' in source_name and source_name.count('-') == 1:
                            # Split on the sign
                            if '+' in source_name:
                                ra_part, dec_part = source_name.split('+')
                                dec_sign = 1
                            else:
                                ra_part, dec_part = source_name.split('-')
                                dec_sign = -1

                            # RA: HHMMSS.s -> hours:minutes:seconds
                            ra_h = float(ra_part[:2])
                            ra_m = float(ra_part[2:4])
                            ra_s = float(ra_part[4:])
                            ra_deg = 15 * (ra_h + ra_m/60 + ra_s/3600)

                            # Dec: DDMMSS -> degrees:minutes:seconds
                            dec_d = float(dec_part[:2])
                            dec_m = float(dec_part[2:4])
                            dec_s = float(dec_part[4:] if len(dec_part) > 4 else 0)
                            dec_deg = dec_sign * (dec_d + dec_m/60 + dec_s/3600)

                            cores.append({
                                'ra': ra_deg,
                                'dec': dec_deg,
                                'id': source_name,
                            })
                    except Exception:
                        # Skip problematic entries
                        continue

            # If we got here and loaded cores, success!
            if cores:
                return cores

        except (UnicodeDecodeError, UnicodeError):
            # Try next encoding
            continue
        except Exception as e:
            # Other error, try next encoding
            continue

    # All encodings failed
    return []


def associate_cores_with_skeleton(cores, skeleton):
    """Associate each core with its nearest point on the skeleton."""
    # Build KD-tree from skeleton pixels (using pixel coordinates)
    tree = cKDTree(skeleton['pixels'])

    core_associations = []
    for core in cores:
        # Convert core RA/Dec to pixel coordinates
        wcs = skeleton['wcs']

        world_coord = SkyCoord(core['ra']*u.deg, core['dec']*u.deg)
        pixel_coord = wcs.world_to_pixel(world_coord)

        # Find nearest skeleton pixel
        dist, idx = tree.query([pixel_coord[1], pixel_coord[0]], k=1)

        if dist < 50:  # Within 50 pixels of skeleton
            core_associations.append({
                'core': core,
                'skeleton_ra': skeleton['ra'][idx],
                'skeleton_dec': skeleton['dec'][idx],
                'skeleton_pixel_idx': idx,
                'distance_to_skeleton': dist,
            })

    return core_associations


def extract_filament_paths(skeleton):
    """Extract individual filament paths from the skeleton mask."""
    # Label connected components in the skeleton
    labeled_skeleton, num_filaments = ndimage.label(
        skeleton['data'] > 0, structure=np.ones((3,3))
    )

    filaments = []
    for i in range(1, num_filaments + 1):
        filament_mask = labeled_skeleton == i
        filament_y, filament_x = np.where(filament_mask)

        if len(filament_x) > 10:  # Only keep filaments with >10 pixels
            # Get RA/Dec for this filament
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

        # Find nearest filament
        min_dist = float('inf')
        nearest_filament = None

        for filament in filaments:
            # Calculate minimum distance to this filament
            dists = np.sqrt((filament['ra'] - core_ra)**2 +
                           (filament['dec'] - core_dec)**2 *
                           np.cos(np.radians(core_ra))**2)
            min_d = dists.min()

            if min_d < min_dist:
                min_dist = min_d
                nearest_filament = filament

        if nearest_filament is not None and min_dist < 0.5:  # Within 0.5 degree
            filament_associations[nearest_filament['id']].append({
                'core': assoc['core'],
                'ra': core_ra,
                'dec': core_dec,
            })

    # Filter filaments with at least 2 cores
    valid_filaments = {fid: cores for fid, cores in filament_associations.items()
                      if len(cores) >= 2}

    return valid_filaments


def compute_position_along_filament(core_list, filament):
    """Compute position of each core along the filament path using PCA."""
    coords = np.column_stack([filament['ra'], filament['dec']])

    # Use PCA to find the primary axis of the filament
    from sklearn.decomposition import PCA
    pca = PCA(n_components=1)
    projected = pca.fit_transform(coords)

    # Project each core onto this axis
    core_coords = np.array([[c['ra'], c['dec']] for c in core_list])
    core_positions = pca.transform(core_coords).flatten()

    # Sort cores by position along filament
    sorted_indices = np.argsort(core_positions)

    sorted_cores = [core_list[i] for i in sorted_indices]
    sorted_positions = core_positions[sorted_indices]

    return sorted_cores, sorted_positions


def compute_nearest_neighbor_spacing(sorted_cores, sorted_positions, distance_pc):
    """Compute nearest-neighbor (adjacent-core) spacings along a filament."""
    if len(sorted_cores) < 2:
        return []

    # Convert angular separations to physical distances (pc)
    spacings = []
    for i in range(len(sorted_positions) - 1):
        # Angular separation between adjacent cores
        ra1, dec1 = sorted_cores[i]['ra'], sorted_cores[i]['dec']
        ra2, dec2 = sorted_cores[i+1]['ra'], sorted_cores[i+1]['dec']

        coord1 = SkyCoord(ra1*u.deg, dec1*u.deg)
        coord2 = SkyCoord(ra2*u.deg, dec2*u.deg)

        # Separation in degrees
        sep_deg = coord1.separation(coord2).deg

        # Convert to physical distance at the region's distance
        # 1 degree at distance D pc = D * π/180 pc
        sep_pc = sep_deg * (np.pi / 180) * distance_pc

        spacings.append(sep_pc)

    return spacings


def analyze_region(region_name, region_info):
    """Analyze a single HGBS region."""
    print(f"\n{'='*70}")
    print(f"ANALYZING {region_name.upper()}")
    print(f"{'='*70}")

    # Find data files
    skeleton_file, catalog_file = find_data_files(region_name, region_info)

    if skeleton_file is None:
        print(f"  SKIPPED: No skeleton file found")
        return {'error': 'No skeleton file found', 'region': region_name}

    if catalog_file is None:
        print(f"  SKIPPED: No catalog file found")
        return {'error': 'No catalog file found', 'region': region_name}

    print(f"  Skeleton: {os.path.basename(skeleton_file)}")
    print(f"  Catalog: {os.path.basename(catalog_file)}")

    # Load data
    skeleton = load_skeleton(skeleton_file)
    if skeleton is None:
        print(f"  SKIPPED: Could not load skeleton")
        return {'error': 'Could not load skeleton', 'region': region_name}

    print(f"  Skeleton pixels: {skeleton['n_pixels']}")

    cores = load_core_catalog(catalog_file)
    if len(cores) < 2:
        print(f"  SKIPPED: Not enough cores ({len(cores)})")
        return {'error': f'Not enough cores ({len(cores)})', 'region': region_name}

    print(f"  Cores loaded: {len(cores)}")

    # Extract filaments
    filaments = extract_filament_paths(skeleton)
    print(f"  Filaments found: {len(filaments)}")

    # Associate cores with skeleton first
    core_associations = associate_cores_with_skeleton(cores, skeleton)
    print(f"  Cores associated with skeleton: {len(core_associations)}")

    # Associate cores with specific filaments
    filament_cores = associate_cores_with_filaments(core_associations, filaments)
    print(f"  Filaments with ≥2 cores: {len(filament_cores)}")

    if len(filament_cores) == 0:
        print(f"  SKIPPED: No filaments with ≥2 cores")
        return {'error': 'No filaments with ≥2 cores', 'region': region_name}

    # Compute spacings for each filament
    all_spacings = []
    filament_results = []

    for filament_id, core_list in filament_cores.items():
        # Find the filament object
        filament = next((f for f in filaments if f['id'] == filament_id), None)
        if filament is None:
            continue

        # Sort cores by position along filament
        sorted_cores, sorted_positions = compute_position_along_filament(
            core_list, filament)

        # Compute nearest-neighbor spacings
        spacings = compute_nearest_neighbor_spacing(
            sorted_cores, sorted_positions, region_info['distance'])

        if spacings:
            median_spacing = np.median(spacings)
            filament_results.append({
                'id': filament_id,
                'n_cores': len(sorted_cores),
                'spacings': spacings,
                'median_spacing': median_spacing,
            })
            all_spacings.extend(spacings)

    # Compute region-level statistics
    if all_spacings:
        region_median = np.median(all_spacings)
        region_std = np.std(all_spacings)
        region_sem = region_std / np.sqrt(len(all_spacings))

        # Compute lambda/W ratio (assuming W = 0.1 pc)
        lambda_over_W = region_median / 0.1

        result = {
            'region': region_name,
            'distance': region_info['distance'],
            'n_filaments': len(filament_results),
            'n_cores_total': sum(len(f['spacings']) + 1 for f in filament_results),
            'n_spacings': len(all_spacings),
            'nn_median_spacing': region_median,
            'nn_std_spacing': region_std,
            'nn_sem_spacing': region_sem,
            'lambda_over_W': lambda_over_W,
            'filament_results': filament_results,
        }

        print(f"\n  RESULTS:")
        print(f"    Distance: {region_info['distance']} pc")
        print(f"    Filaments with ≥2 cores: {len(filament_results)}")
        print(f"    Total spacings measured: {len(all_spacings)}")
        print(f"    Median NN spacing: {region_median:.4f} ± {region_sem:.4f} pc")
        print(f"    λ/W ratio: {lambda_over_W:.2f}")

        return result
    else:
        print(f"  SKIPPED: No spacings computed")
        return {'error': 'No spacings computed', 'region': region_name}


def main():
    """Run complete NN analysis for all HGBS regions."""
    print("=" * 70)
    print("COMPLETE NEAREST-NEIGHBOR SPACING ANALYSIS FOR ALL HGBS REGIONS")
    print("=" * 70)
    print()
    print("This analysis addresses the referee's concern by performing")
    print("proper nearest-neighbor (adjacent-core) spacing analysis for")
    print("all available HGBS regions with skeleton and core catalog data.")
    print()

    results = []
    errors = []

    for region_name, region_info in HGBS_REGIONS.items():
        try:
            result = analyze_region(region_name, region_info)
            if 'error' in result:
                errors.append(result)
            else:
                results.append(result)
        except Exception as e:
            print(f"\n  ERROR during analysis: {e}")
            import traceback
            traceback.print_exc()
            errors.append({'error': str(e), 'region': region_name})

    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Regions analyzed successfully: {len(results)}")
    print(f"Regions with errors: {len(errors)}")
    print()

    if errors:
        print("Regions with errors:")
        for e in errors:
            print(f"  {e['region']}: {e.get('error', 'Unknown error')}")
        print()

    if results:
        print("Successful results:")
        print(f"{'Region':<15} {'Distance':<10} {'N_fil':<6} {'N_spac':<7} {'NN (pc)':<12} {'λ/W':<6}")
        print("-" * 70)
        for r in results:
            print(f"{r['region']:<15} {r['distance']:<10} "
                  f"{r['n_filaments']:<6} {r['n_spacings']:<7} "
                  f"{r['nn_median_spacing']:.4f}±{r['nn_sem_spacing']:.4f}  "
                  f"{r['lambda_over_W']:.2f}")

        # Compute weighted average
        if len(results) >= 2:
            # Use inverse-variance weighting
            weights = [1 / (r['nn_sem_spacing']**2) for r in results]
            weighted_mean = sum(w * r['nn_median_spacing'] for w, r in zip(weights, results)) / sum(weights)
            weighted_mean_lambda_W = weighted_mean / 0.1
            weighted_sem = 1 / np.sqrt(sum(weights))

            print()
            print(f"Weighted mean (inverse-variance):")
            print(f"  NN spacing: {weighted_mean:.4f} ± {weighted_sem:.4f} pc")
            print(f"  λ/W ratio: {weighted_mean_lambda_W:.2f}")

    # Save results to JSON
    output_file = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/complete_nn_results_all_regions.json'

    save_data = {
        'analysis_date': '2026-05-12',
        'description': 'Complete NN analysis for all HGBS regions',
        'successful_results': results,
        'errors': errors,
    }

    with open(output_file, 'w') as f:
        json.dump(save_data, f, indent=2, default=lambda x: float(x) if isinstance(x, np.floating) else x)

    print(f"\nResults saved to: {output_file}")


if __name__ == '__main__':
    main()
