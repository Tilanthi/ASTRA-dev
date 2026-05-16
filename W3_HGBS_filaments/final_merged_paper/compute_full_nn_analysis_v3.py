#!/usr/bin/env python3
"""
Compute full nearest-neighbor spacing analysis for all HGBS regions.
Handles multiple catalog formats used by different HGBS regions.
"""

import numpy as np
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.spatial import cKDTree
import os
import json
import warnings
import re
warnings.filterwarnings('ignore')

# HGBS regions with Gaia DR3 distances (pc)
HGBS_REGIONS = {
    'Taurus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS',
        'skeleton_file': 'HGBS_taurusL1495_skeleton_map.fits',
        'catalog_file': 'HGBS_taurusL1495_observed_core_catalog.txt',
        'distance': 135,
        'pairwise_median_pc': 0.198,
        'pairwise_lambda_W': 1.98,
        'catalog_format': 'space',  # RA/Dec as separate HH MM SS columns
    },
    'OrionB': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB',
        'skeleton_file': 'HGBS_orionB_skeleton_map.fits',  # Try different file
        'catalog_file': 'HGBS_orionB_observed_core_catalog.txt',
        'distance': 386,
        'pairwise_median_pc': 0.313,
        'pairwise_lambda_W': 3.13,
        'catalog_format': 'pipe',  # Pipe-separated table
    },
    'Aquila': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA/HGBS_AQUILA',
        'skeleton_file': 'HGBS_aquilaM2_skeleton_map.fits',
        'catalog_file': 'HGBS_aquilaM2_observed_core_catalog.txt',
        'distance': 436,
        'pairwise_median_pc': 0.346,
        'pairwise_lambda_W': 3.46,
        'catalog_format': 'colon',  # RA/Dec in HH:MM:SS format
    },
    'Perseus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS',
        'skeleton_file': 'HGBS_perseus_skeleton_map.fits',
        'catalog_file': None,
        'distance': 296,
        'pairwise_median_pc': 0.248,
        'pairwise_lambda_W': 2.48,
        'catalog_format': 'auto',
    },
    'Ophiuchus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH',
        'skeleton_file': 'HGBS_oph_l1688_skeleton_map.fits',
        'catalog_file': 'HGBS_ophiuchus_observed_core_catalog.txt',
        'distance': 137,
        'pairwise_median_pc': 0.206,
        'pairwise_lambda_W': 2.06,
        'catalog_format': 'space',  # Can try both
    },
    'Serpens': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS',
        'skeleton_file': 'HGBS_serpens_skeleton_map.fits',
        'catalog_file': 'HGBS_serpens_observed_core_catalog.txt',
        'distance': 458,
        'pairwise_median_pc': 0.308,
        'pairwise_lambda_W': 3.08,
        'catalog_format': 'colon',  # RA/Dec in HH:MM:SS format
    },
    'TMC1': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1',
        'skeleton_file': 'HGBS_taurusTMC1_skeleton_map.fits',
        'catalog_file': 'HGBS_taurusTMC1_observed_core_catalog.txt',
        'distance': 135,
        'pairwise_median_pc': 0.233,
        'pairwise_lambda_W': 2.33,
        'catalog_format': 'colon',  # RA/Dec in HH:MM:SS format
    },
    'CRA': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_CRA',
        'skeleton_file': 'HGBS_craNS_skeleton_map.fits',
        'catalog_file': 'HGBS_craNS_observed_core_catalog.txt',
        'distance': 150,
        'pairwise_median_pc': 0.204,
        'pairwise_lambda_W': 2.04,
        'catalog_format': 'space',  # RA/Dec as separate HH MM SS columns
    },
}


def find_skeleton_file(region_path):
    """Find skeleton file if not specified."""
    import glob

    patterns = [
        '*skeleton*.fits',
        '*skeleton*.fits',
    ]

    for pattern in patterns:
        files = glob.glob(os.path.join(region_path, pattern))
        # Filter out threshold versions, prefer main skeleton
        for f in files:
            if 'thresh' not in f.lower():
                return f
        if files:
            return files[0]

    return None


def parse_hmsra(ra_str):
    """Parse RA from various formats."""
    ra_str = str(ra_str).strip()

    # Format: HH:MM:SS.ss or HH MM SS.ss
    if ':' in ra_str:
        parts = ra_str.split(':')
        if len(parts) == 3:
            h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            return 15 * (h + m/60 + s/3600)
    else:
        # Try space-separated
        parts = ra_str.split()
        if len(parts) >= 3:
            try:
                h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
                return 15 * (h + m/60 + s/3600)
            except:
                pass

    return None


def parse_dmdec(dec_str):
    """Parse Dec from various formats."""
    dec_str = str(dec_str).strip()

    # Format: +/-DD:MM:SS.ss or +/-DD MM SS.ss
    if ':' in dec_str:
        parts = dec_str.split(':')
        if len(parts) == 3:
            d, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            if d < 0:
                return d - m/60 - s/3600
            else:
                return d + m/60 + s/3600
    else:
        # Try space-separated
        parts = dec_str.split()
        if len(parts) >= 3:
            try:
                d, m, s = float(parts[0]), float(parts[1]), float(parts[2])
                if d < 0:
                    return d - m/60 - s/3600
                else:
                    return d + m/60 + s/3600
            except:
                pass

    return None


def load_core_catalog_v3(catalog_file, catalog_format='auto'):
    """Load core catalog handling multiple formats."""
    print(f"  Loading catalog: {catalog_file}")

    cores = []

    # Try different encodings
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

    for encoding in encodings:
        try:
            with open(catalog_file, 'r', encoding=encoding) as f:
                lines = f.readlines()

            # Find first data line
            comment_chars = ['!', '|', '#']
            data_start = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not any(stripped.startswith(c) for c in comment_chars):
                    data_start = i
                    break

            # Detect format if auto
            if catalog_format == 'auto':
                first_line = lines[data_start]
                if '|' in first_line and '\t' not in first_line:
                    catalog_format = 'pipe'
                elif ':' in first_line or '\t' in first_line:
                    catalog_format = 'colon'
                else:
                    catalog_format = 'space'

            print(f"  Using format: {catalog_format}, encoding: {encoding}")

            # Parse based on format
            for line in lines[data_start:]:
                line = line.strip()
                if not line or any(line.startswith(c) for c in comment_chars):
                    continue

                try:
                    if catalog_format == 'space':
                        # Space-separated: RA and Dec as separate HH MM SS columns
                        parts = line.split()
                        if len(parts) < 8:
                            continue

                        source_name = parts[1]

                        # RA from columns 3-5 (indices 2-4): HH MM SS.ss
                        ra_deg = parse_hmsra(f"{parts[2]} {parts[3]} {parts[4]}")
                        dec_deg = parse_dmdec(f"{parts[5]} {parts[6]} {parts[7]}")

                    elif catalog_format == 'colon':
                        # Tab/space-separated with HH:MM:SS format
                        # Split by tabs first, then by spaces
                        parts = line.split('\t') if '\t' in line else line.split()

                        if len(parts) < 4:
                            continue

                        source_name = parts[1].strip()

                        # Find RA and Dec columns (containing ':')
                        ra_str, dec_str = None, None
                        for part in parts[2:]:
                            if ':' in part and '+' in part or '-' in part:
                                # Combined format like "182154.6-025557"
                                continue
                            elif ':' in part and not dec_str:
                                if ra_str is None:
                                    ra_str = part.strip()
                                else:
                                    dec_str = part.strip()

                        if not ra_str or not dec_str:
                            # Try looking at specific column positions
                            for i, part in enumerate(parts):
                                part = part.strip()
                                if ':' in part and i == 2:
                                    ra_str = part
                                elif ':' in part and i == 3:
                                    dec_str = part

                        if ra_str and dec_str:
                            ra_deg = parse_hmsra(ra_str)
                            dec_deg = parse_dmdec(dec_str)
                        else:
                            continue

                    elif catalog_format == 'pipe':
                        # Pipe-separated table format
                        parts = line.split('|')
                        # Clean up parts
                        parts = [p.strip() for p in parts if p.strip()]

                        if len(parts) < 4:
                            continue

                        source_name = parts[1].strip() if len(parts) > 1 else ""

                        # Find RA and Dec
                        ra_str, dec_str = None, None
                        for part in parts[2:]:
                            part = part.strip()
                            if ':' in part:
                                if ra_str is None:
                                    ra_str = part
                                else:
                                    dec_str = part

                        if ra_str and dec_str:
                            ra_deg = parse_hmsra(ra_str)
                            dec_deg = parse_dmdec(dec_str)
                        else:
                            continue

                    else:
                        continue

                    if ra_deg is not None and dec_deg is not None:
                        cores.append({
                            'ra': ra_deg,
                            'dec': dec_deg,
                            'id': source_name,
                        })

                except Exception as e:
                    continue

            print(f"  Loaded {len(cores)} cores")
            return cores

        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  Error: {e}")
            continue

    print(f"  ERROR: Could not read catalog")
    return []


def compute_nn_spacing_2d(cores, distance_pc):
    """
    Compute NN spacing using 2D nearest neighbors in RA/Dec space.
    """
    if len(cores) < 2:
        return []

    coords = np.array([[c['ra'], c['dec']] for c in cores])
    tree = cKDTree(coords)

    # Query 2 nearest neighbors (first is self)
    distances, indices = tree.query(coords, k=2)

    # Second column is distance to nearest neighbor (in degrees)
    nn_distances_deg = distances[:, 1]

    # Convert to physical distance
    mean_dec = np.mean(coords[:, 1])
    cos_dec = np.cos(np.radians(mean_dec))

    nn_spacings_pc = []
    for dist_deg in nn_distances_deg:
        sep_pc = dist_deg * (np.pi / 180) * distance_pc / cos_dec
        nn_spacings_pc.append(sep_pc)

    return nn_spacings_pc


def analyze_region(region_name, region_info):
    """Analyze a single HGBS region."""

    print(f"\n{'='*70}")
    print(f"ANALYZING {region_name.upper()}")
    print(f"{'='*70}")

    # Find skeleton file
    if region_info['skeleton_file']:
        skeleton_path = os.path.join(region_info['path'], region_info['skeleton_file'])
    else:
        skeleton_path = find_skeleton_file(region_info['path'])

    if not skeleton_path or not os.path.exists(skeleton_path):
        print(f"  WARNING: Skeleton file not found, using catalog-only analysis")
        skeleton_path = None

    # Find catalog file
    catalog_file = region_info['catalog_file']
    if catalog_file is None:
        # Search for catalog
        import glob
        pattern = os.path.join(region_info['path'], '*catalog*.txt')
        files = glob.glob(pattern)
        if files:
            catalog_file = os.path.basename(files[0])
            skeleton_path = os.path.join(region_info['path'], catalog_file)
        else:
            print(f"  ERROR: No catalog file found")
            return None

    catalog_path = os.path.join(region_info['path'], catalog_file)

    # Load cores
    cores = load_core_catalog_v3(catalog_path, region_info['catalog_format'])

    if len(cores) < 10:
        print(f"  ERROR: Not enough cores ({len(cores)})")
        return None

    # Compute NN spacing
    spacings = compute_nn_spacing_2d(cores, region_info['distance'])

    if len(spacings) < 10:
        print(f"  ERROR: Not enough spacings computed")
        return None

    region_median = np.median(spacings)
    region_std = np.std(spacings)
    region_sem = region_std / np.sqrt(len(spacings))

    lambda_over_W = region_median / 0.1

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
            'p16': float(percentiles[0]),
            'p50': float(percentiles[1]),
            'p84': float(percentiles[2]),
        },
        'pairwise_median': region_info['pairwise_median_pc'],
        'pairwise_lambda_W': region_info['pairwise_lambda_W'],
        'bias_factor': region_info['pairwise_median_pc'] / region_median if region_median > 0 else None,
    }

    print(f"\n  RESULTS:")
    print(f"    Distance: {region_info['distance']} pc")
    print(f"    N_cores: {len(cores)}")
    print(f"    NN median spacing: {region_median:.4f} ± {region_sem:.4f} pc")
    print(f"    NN 16-84 percentiles: {percentiles[0]:.4f} - {percentiles[2]:.4f} pc")
    print(f"    NN λ/W: {lambda_over_W:.2f}")
    print(f"    Pairwise median: {region_info['pairwise_median_pc']:.3f} pc (λ/W = {region_info['pairwise_lambda_W']:.2f})")
    print(f"    Ratio (pairwise/NN): {result['bias_factor']:.2f}×")

    return result


# Main analysis
if __name__ == '__main__':
    print("=" * 70)
    print("FULL NEAREST-NEIGHBOR SPACING ANALYSIS - ALL 8 HGBS REGIONS")
    print("=" * 70)
    print()

    results = []
    successful_regions = []
    failed_regions = []

    for region_name, region_info in HGBS_REGIONS.items():
        try:
            result = analyze_region(region_name, region_info)
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
    print(f"Successful: {len(successful_regions)}/{len(HGBS_REGIONS)} regions")
    print(f"Failed: {len(failed_regions)} regions: {failed_regions}")
    print()

    if results:
        # Print table header
        print(f"{'Region':<12} {'N_cores':<8} {'NN_median':<14} {'NN_λ/W':<10} {'Pairwise':<10} {'Ratio':<8}")
        print("-"*70)

        for r in results:
            print(f"{r['region']:<12} {r['n_cores']:<8} "
                  f"{r['nn_median_spacing']:.4f}±{r['nn_sem']:.3f}  "
                  f"{r['nn_lambda_over_W']:<10.2f} "
                  f"{r['pairwise_median']:.3f}  {r['bias_factor']:<8.2f}×")

        print()
        print("COMBINED STATISTICS:")
        print("-"*40)

        # Separate robust and limited regions
        robust_regions = ['Taurus', 'OrionB', 'Aquila', 'Perseus']
        robust_results = [r for r in results if r['region'] in robust_regions]

        if robust_results:
            weights = np.array([1.0/(r['nn_sem']**2) for r in robust_results])
            weights = weights / np.sum(weights)

            weighted_mean_nn = np.sum([w * r['nn_median_spacing'] for w, r in zip(weights, robust_results)])
            weighted_mean_lambda_W = np.sum([w * r['nn_lambda_over_W'] for w, r in zip(weights, robust_results)])
            weighted_uncertainty = np.sqrt(1.0 / np.sum([1.0/(r['nn_sem']**2) for r in robust_results]))

            print(f"Robust regions (N={len(robust_results)}):")
            print(f"  Total cores: {sum(r['n_cores'] for r in robust_results)}")
            print(f"  Weighted NN spacing: {weighted_mean_nn:.4f} ± {weighted_uncertainty:.4f} pc")
            print(f"  Weighted NN λ/W: {weighted_mean_lambda_W:.2f} ± {weighted_uncertainty/0.1:.2f}")

        # Full sample
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

        # Save results
        output_file = "full_nn_spacing_results_final.json"
        output_data = {
            'analysis_date': '2026-05-01',
            'method': '2D nearest-neighbor spacing in RA/Dec coordinates',
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
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\nResults saved to: {output_file}")

    else:
        print("No successful analyses!")
