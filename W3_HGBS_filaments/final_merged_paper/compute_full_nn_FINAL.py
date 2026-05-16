#!/usr/bin/env python3
"""
Compute full nearest-neighbor spacing analysis for all 8 HGBS regions.
Final version with robust catalog format detection and parsing.
"""

import numpy as np
import re
import os
import json
import warnings
warnings.filterwarnings('ignore')

# HGBS regions configuration
HGBS_REGIONS = {
    'Taurus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS',
        'skeleton_file': 'HGBS_taurusL1495_skeleton_map.fits',
        'catalog_file': 'HGBS_taurusL1495_observed_core_catalog.txt',
        'distance': 135,
        'pairwise_median_pc': 0.198,
        'pairwise_lambda_W': 1.98,
        'catalog_encoding': 'utf-8',
    },
    'OrionB': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB',
        'skeleton_file': 'HGBS_orionB_skeleton_map.fits',
        'catalog_file': 'HGBS_orionB_observed_core_catalog.txt',
        'distance': 386,
        'pairwise_median_pc': 0.313,
        'pairwise_lambda_W': 3.13,
        'catalog_encoding': 'latin-1',
    },
    'Aquila': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA/HGBS_AQUILA',
        'skeleton_file': 'HGBS_aquilaM2_skeleton_map.fits',
        'catalog_file': 'HGBS_aquilaM2_observed_core_catalog.txt',
        'distance': 436,
        'pairwise_median_pc': 0.346,
        'pairwise_lambda_W': 3.46,
        'catalog_encoding': 'latin-1',
        'catalog_subdir': 'HGBS_AQUILA',
    },
    'Perseus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS/HGBS_PERSEUS',
        'skeleton_file': 'HGBS_perseus_skeleton_map.fits',
        'catalog_file': 'HGBS_perseus_observed_core_catalog.txt',
        'distance': 296,
        'pairwise_median_pc': 0.248,
        'pairwise_lambda_W': 2.48,
        'catalog_encoding': 'utf-8',
        'catalog_subdir': 'HGBS_PERSEUS',
    },
    'Ophiuchus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH',
        'skeleton_file': 'HGBS_oph_l1688_skeleton_map.fits',
        'catalog_file': 'HGBS_ophiuchus_observed_core_catalog.txt',
        'distance': 137,
        'pairwise_median_pc': 0.206,
        'pairwise_lambda_W': 2.06,
        'catalog_encoding': 'utf-8',
    },
    'Serpens': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS',
        'skeleton_file': 'HGBS_serpens_skeleton_map.fits',
        'catalog_file': 'HGBS_serpens_observed_core_catalog.txt',
        'distance': 458,
        'pairwise_median_pc': 0.308,
        'pairwise_lambda_W': 3.08,
        'catalog_encoding': 'latin-1',
    },
    'TMC1': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1',
        'skeleton_file': 'HGBS_taurusTMC1_skeleton_map.fits',
        'catalog_file': 'HGBS_taurusTMC1_observed_core_catalog.txt',
        'distance': 135,
        'pairwise_median_pc': 0.233,
        'pairwise_lambda_W': 2.33,
        'catalog_encoding': 'utf-8',
    },
    'CRA': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_CRA',
        'skeleton_file': 'HGBS_craNS_skeleton_map.fits',
        'catalog_file': 'HGBS_craNS_observed_core_catalog.txt',
        'distance': 150,
        'pairwise_median_pc': 0.204,
        'pairwise_lambda_W': 2.04,
        'catalog_encoding': 'utf-8',
    },
}


def parse_hms_to_deg(ra_str):
    """Parse RA from HH:MM:SS.ss format."""
    h, m, s = map(float, ra_str.split(':'))
    return 15 * (h + m/60 + s/3600)


def parse_dms_to_deg(dec_str):
    """Parse Dec from +/-DD:MM:SS.s format."""
    d, m, s = map(float, dec_str.split(':'))
    if d < 0:
        return d - m/60 - s/3600
    else:
        return d + m/60 + s/3600


def parse_space_format_catalog(line):
    """Parse Taurus/CRA format (RA/Dec as separate HH MM SS columns)."""
    parts = line.split()
    if len(parts) < 8:
        return None

    try:
        source_name = parts[1]
        # RA: columns 3-5 (indices 2-4)
        ra_deg = parse_hms_to_deg(f"{parts[2]} {parts[3]} {parts[4]}")
        # Dec: columns 6-8 (indices 5-7)
        dec_deg = parse_dms_to_deg(f"{parts[5]} {parts[6]} {parts[7]}")
        return {'ra': ra_deg, 'dec': dec_deg, 'id': source_name}
    except:
        return None


def parse_colon_format_catalog(line):
    """Parse Aquila/Ophiuchus/TMC1 format (RA/Dec in HH:MM:SS format)."""
    parts = line.split('\t') if '\t' in line else line.split()
    if len(parts) < 4:
        return None

    try:
        # Look for RA and Dec columns containing ':'
        ra_str, dec_str = None, None
        source_name = parts[1].strip() if len(parts) > 1 else ""

        for part in parts[2:6]:
            part = part.strip()
            if ':' in part:
                if ra_str is None:
                    # Extract RA from combined string if needed
                    match = re.search(r'(\d{1,2}:\d{2}:\d{2}\.?\d*)', part)
                    if match:
                        ra_str = match.group(1)
                elif dec_str is None:
                    match = re.search(r'([+-]?\d{1,2}:\d{2}:\d{2}\.?\d*)', part)
                    if match:
                        dec_str = match.group(1)

        if not ra_str or not dec_str:
            return None

        ra_deg = parse_hms_to_deg(ra_str)
        dec_deg = parse_dms_to_deg(dec_str)
        return {'ra': ra_deg, 'dec': dec_deg, 'id': source_name}
    except:
        return None


def parse_serpens_format_catalog(line):
    """Parse Serpens format (combined source+RA+Dec in one field)."""
    parts = line.split('\t')
    if len(parts) < 2:
        return None

    try:
        part1 = parts[1].strip()

        # Extract RA and Dec using regex
        ra_match = re.search(r'(\d{1,2}:\d{2}:\d{2}\.?\d*)', part1)
        dec_match = re.search(r'([+-]\d{1,2}:\d{2}:\d{2}\.?\d*)', part1)

        if not ra_match or not dec_match:
            return None

        ra_deg = parse_hms_to_deg(ra_match.group(1))
        dec_deg = parse_dms_to_deg(dec_match.group(1))
        return {'ra': ra_deg, 'dec': dec_deg, 'id': parts[0].strip()}
    except:
        return None


def load_core_catalog(catalog_path, region_name):
    """Load core catalog with auto-detection of format."""
    print(f"  Loading catalog: {catalog_path}")

    encodings = ['utf-8', 'latin-1', 'iso-8859-1']
    comment_chars = ['!', '|', '#']

    for encoding in encodings:
        try:
            with open(catalog_path, 'r', encoding=encoding) as f:
                lines = f.readlines()

            # Find first data line
            data_start = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not any(stripped.startswith(c) for c in comment_chars):
                    data_start = i
                    break

            # Try different parsers
            parsers = [
                ('space', parse_space_format_catalog),
                ('colon', parse_colon_format_catalog),
                ('serpens', parse_serpens_format_catalog),
            ]

            cores = []
            parser_used = None

            for parser_name, parser_func in parsers:
                test_cores = []
                for line in lines[data_start:data_start+20]:
                    line = line.strip()
                    if not line or any(line.startswith(c) for c in comment_chars):
                        continue
                    try:
                        result = parser_func(line)
                        if result:
                            test_cores.append(result)
                    except:
                        pass

                if len(test_cores) > 5:
                    # This parser works, use it for all lines
                    parser_used = parser_name
                    for line in lines[data_start:]:
                        line = line.strip()
                        if not line or any(line.startswith(c) for c in comment_chars):
                            continue
                        try:
                            result = parser_func(line)
                            if result:
                                cores.append(result)
                        except:
                            pass
                    break

            if cores:
                print(f"  Loaded {len(cores)} cores using '{parser_used}' parser, encoding: {encoding}")
                return cores

        except UnicodeDecodeError:
            continue
        except Exception as e:
            continue

    print(f"  ERROR: Could not load catalog")
    return []


def compute_nn_spacing_2d(cores, distance_pc):
    """Compute NN spacing using 2D KD-tree."""
    if len(cores) < 2:
        return []

    coords = np.array([[c['ra'], c['dec']] for c in cores])
    from scipy.spatial import cKDTree
    tree = cKDTree(coords)

    distances, _ = tree.query(coords, k=2)
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

    # Build catalog path
    if 'catalog_subdir' in region_info:
        catalog_path = os.path.join(region_info['path'], region_info['catalog_file'])
    else:
        catalog_path = os.path.join(region_info['path'], region_info['catalog_file'])

    if not os.path.exists(catalog_path):
        # Try in parent directory
        parent_path = os.path.dirname(region_info['path'].rstrip('/'))
        catalog_path = os.path.join(parent_path, region_info['catalog_file'])

    # Load cores
    cores = load_core_catalog(catalog_path, region_name)

    if len(cores) < 10:
        print(f"  ERROR: Not enough cores ({len(cores)})")
        return None

    # Compute NN spacing
    spacings = compute_nn_spacing_2d(cores, region_info['distance'])

    if len(spacings) < 10:
        print(f"  ERROR: Not enough spacings")
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
        'nn_median_spacing': float(region_median),
        'nn_sem': float(region_sem),
        'nn_lambda_over_W': float(lambda_over_W),
        'nn_p16': float(percentiles[0]),
        'nn_p50': float(percentiles[1]),
        'nn_p84': float(percentiles[2]),
        'pairwise_median': region_info['pairwise_median_pc'],
        'pairwise_lambda_W': region_info['pairwise_lambda_W'],
        'bias_factor': region_info['pairwise_median_pc'] / region_median,
    }

    print(f"  N_cores: {len(cores)}")
    print(f"  NN median: {region_median:.4f} ± {region_sem:.4f} pc")
    print(f"  NN λ/W: {lambda_over_W:.2f}")
    print(f"  Pairwise: {region_info['pairwise_median_pc']:.3f} pc (λ/W = {region_info['pairwise_lambda_W']:.2f})")
    print(f"  Ratio: {result['bias_factor']:.2f}×")

    return result


if __name__ == '__main__':
    print("=" * 70)
    print("FULL NN SPACING ANALYSIS - ALL 8 HGBS REGIONS")
    print("=" * 70)

    results = []
    successful = []
    failed = []

    for region_name, region_info in HGBS_REGIONS.items():
        try:
            result = analyze_region(region_name, region_info)
            if result:
                results.append(result)
                successful.append(region_name)
            else:
                failed.append(region_name)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed.append(region_name)

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Successful: {len(successful)}/8 regions: {successful}")
    print(f"Failed: {len(failed)} regions: {failed}")

    if results:
        print(f"\n{'Region':<12} {'N_cores':<8} {'NN_median':<14} {'NN_λ/W':<10} {'Pairwise':<10} {'Ratio':<8}")
        print("-"*70)

        for r in results:
            print(f"{r['region']:<12} {r['n_cores']:<8} "
                  f"{r['nn_median_spacing']:.4f}±{r['nn_sem']:.3f}  "
                  f"{r['nn_lambda_over_W']:<10.2f} "
                  f"{r['pairwise_median']:.3f}  {r['bias_factor']:<8.2f}×")

        # Combined statistics
        robust_names = ['Taurus', 'OrionB', 'Aquila', 'Perseus']
        robust_results = [r for r in results if r['region'] in robust_names]

        if robust_results:
            weights = np.array([1.0/(r['nn_sem']**2) for r in robust_results])
            weights = weights / np.sum(weights)

            weighted_nn = np.sum([w * r['nn_median_spacing'] for w, r in zip(weights, robust_results)])
            weighted_lambda_W = np.sum([w * r['nn_lambda_over_W'] for w, r in zip(weights, robust_results)])
            weighted_unc = np.sqrt(1.0 / np.sum([1.0/(r['nn_sem']**2) for r in robust_results]))

            print(f"\nROBUST REGIONS (N={len(robust_results)}):")
            print(f"  Total cores: {sum(r['n_cores'] for r in robust_results)}")
            print(f"  Weighted NN spacing: {weighted_nn:.4f} ± {weighted_unc:.4f} pc")
            print(f"  Weighted NN λ/W: {weighted_lambda_W:.2f} ± {weighted_unc/0.1:.2f}")

        # Full sample
        if len(results) >= 4:
            all_weights = np.array([1.0/(r['nn_sem']**2) for r in results])
            all_weights = all_weights / np.sum(all_weights)

            all_nn = np.sum([w * r['nn_median_spacing'] for w, r in zip(all_weights, results)])
            all_lambda_W = np.sum([w * r['nn_lambda_over_W'] for w, r in zip(all_weights, results)])
            all_unc = np.sqrt(1.0 / np.sum([1.0/(r['nn_sem']**2) for r in results]))

            print(f"\nFULL SAMPLE (N={len(results)}):")
            print(f"  Total cores: {sum(r['n_cores'] for r in results)}")
            print(f"  Weighted NN spacing: {all_nn:.4f} ± {all_unc:.4f} pc")
            print(f"  Weighted NN λ/W: {all_lambda_W:.2f} ± {all_unc/0.1:.2f}")

        # Save results
        output = {
            'analysis_date': '2026-05-01',
            'method': '2D nearest-neighbor spacing',
            'successful_regions': successful,
            'failed_regions': failed,
            'results': results,
            'robust_weighted_nn_pc': float(weighted_nn) if robust_results else None,
            'robust_weighted_lambda_W': float(weighted_lambda_W) if robust_results else None,
            'robust_uncertainty_pc': float(weighted_unc) if robust_results else None,
            'full_weighted_nn_pc': float(all_nn) if len(results) >= 4 else None,
            'full_weighted_lambda_W': float(all_lambda_W) if len(results) >= 4 else None,
            'full_uncertainty_pc': float(all_unc) if len(results) >= 4 else None,
        }

        with open('full_nn_spacing_results_FINAL.json', 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\nResults saved to: full_nn_spacing_results_FINAL.json")
