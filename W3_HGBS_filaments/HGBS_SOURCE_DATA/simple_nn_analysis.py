#!/usr/bin/env python3
"""
Simplified Nearest-Neighbor Analysis for HGBS Regions

Processes one region at a time for incremental results.
"""

import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy.spatial import cKDTree
import json
from pathlib import Path
from typing import Dict, List


REGION_CONFIGS = {
    'Orion B': {
        'folder': 'HGBS_ORIB',
        'skeleton': 'HGBS_orionB_skeleton_map_thresh50.fits',
        'catalog': 'HGBS_orionb_derived_core_catalog.txt',
        'distance': 386,
        'paper_pairwise': 0.360,
        'paper_lambda_over_W': 2.84,
    },
    'Ophiuchus': {
        'folder': 'HGBS_OPH',
        'skeleton': 'HGBS_oph_l1688_skeleton_map_thresh50.fits',
        'catalog': 'HGBS_ophiuchus_derived_core_catalog.txt',
        'distance': 137,
        'paper_pairwise': 0.309,
        'paper_lambda_over_W': 3.09,
    },
    'Taurus': {
        'folder': 'HGBS_TAURUS',
        'skeleton': 'HGBS_taurusL1495_skeleton_map_thresh50.fits',
        'catalog': 'HGBS_taurusL1495_derived_core_catalog.txt',
        'distance': 145,
        'paper_pairwise': 0.326,
        'paper_lambda_over_W': 3.26,
    },
    'IC5146': {
        'folder': 'HGBS_IC5146',
        'skeleton': 'HGBS_ic5146_skeleton_map.fits',
        'catalog': 'core_catalog_ic5146.csv',
        'distance': 260,
        'paper_pairwise': 0.270,
        'paper_lambda_over_W': 2.70,
    },
}


def load_catalog_csv(catalog_file: str) -> List[Dict]:
    """Load CSV format catalog."""
    import csv
    cores = []
    with open(catalog_file, 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                cores.append({
                    'id': i,
                    'ra': float(row['ra_deg']),
                    'dec': float(row['dec_deg']),
                })
            except (ValueError, KeyError):
                continue
    return cores


def load_catalog_text(catalog_file: str) -> List[Dict]:
    """Load HGBS text format catalog."""
    cores = []
    with open(catalog_file, 'r', encoding='latin-1', errors='ignore') as f:
        lines = f.readlines()

    # Find data start
    data_start = None
    for i, line in enumerate(lines):
        if not line.strip() or line.startswith('|') or line.startswith('!') or \
           line.startswith('-') or 'TABLE' in line or 'Description' in line:
            continue
        parts = line.split()
        if parts and parts[0].isdigit():
            data_start = i
            break

    if data_start is None:
        return cores

    # Parse data
    for line in lines[data_start:]:
        if not line.strip() or line.startswith('|') or line.startswith('!'):
            continue

        parts = line.split()
        if len(parts) < 4:
            continue

        try:
            core_id = int(parts[0])
            ra_str = parts[2]
            dec_str = parts[3]

            coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))

            cores.append({
                'id': core_id,
                'ra': coord.ra.deg,
                'dec': coord.dec.deg,
            })
        except (ValueError, IndexError):
            continue

    return cores


def compute_nn_spacing(cores: List[Dict], distance_pc: float) -> Dict:
    """Compute nearest-neighbor spacing statistics."""
    if len(cores) < 2:
        return {'error': 'Less than 2 cores'}

    # Extract coordinates
    coords = np.array([[c['ra'], c['dec']] for c in cores])

    # Build k-d tree and query NN
    tree = cKDTree(coords)
    distances, _ = tree.query(coords, k=2)

    # Get NN distances (skip self)
    nn_distances_deg = distances[:, 1]

    # Convert to physical distance (pc)
    nn_distances_pc = nn_distances_deg * (np.pi/180) * distance_pc

    # Compute statistics
    stats = {
        'n_cores': len(cores),
        'nn_min_pc': float(np.min(nn_distances_pc)),
        'nn_max_pc': float(np.max(nn_distances_pc)),
        'nn_mean_pc': float(np.mean(nn_distances_pc)),
        'nn_median_pc': float(np.median(nn_distances_pc)),
        'nn_std_pc': float(np.std(nn_distances_pc)),
        'nn_sem_pc': float(np.std(nn_distances_pc) / np.sqrt(len(nn_distances_pc))),
        'nn_q25_pc': float(np.percentile(nn_distances_pc, 25)),
        'nn_q75_pc': float(np.percentile(nn_distances_pc, 75)),
    }

    return stats


def analyze_region(region_name: str, config: Dict, base_path: Path) -> Dict:
    """Analyze a single region."""
    print(f"\n{'='*60}")
    print(f"Analyzing {region_name}")
    print(f"{'='*60}")

    folder = base_path / config['folder']
    catalog_file = folder / config['catalog']

    if not catalog_file.exists():
        print(f"ERROR: Catalog file not found: {catalog_file}")
        return None

    # Load catalog
    print(f"Loading catalog: {catalog_file.name}")
    if catalog_file.suffix == '.csv':
        cores = load_catalog_csv(str(catalog_file))
    else:
        cores = load_catalog_text(str(catalog_file))

    print(f"  Loaded {len(cores)} cores")

    if len(cores) == 0:
        print("ERROR: No cores loaded")
        return None

    # Compute NN spacing
    print("Computing nearest-neighbor spacing...")
    stats = compute_nn_spacing(cores, config['distance'])
    stats['region'] = region_name
    stats['distance_pc'] = config['distance']

    # Add paper comparison
    if 'paper_pairwise' in config:
        stats['paper_pairwise_pc'] = config['paper_pairwise']
        stats['paper_lambda_over_W'] = config['paper_lambda_over_W']
        stats['nn_lambda_over_W'] = stats['nn_median_pc'] / 0.127
        stats['nn_over_pairwise'] = stats['nn_median_pc'] / config['paper_pairwise']

    # Print summary
    print(f"\nResults:")
    print(f"  N_cores: {stats['n_cores']}")
    print(f"  NN median: {stats['nn_median_pc']:.4f} ± {stats['nn_sem_pc']:.4f} pc")
    print(f"  NN mean:   {stats['nn_mean_pc']:.4f} ± {stats['nn_sem_pc']:.4f} pc")
    if 'paper_pairwise' in config:
        print(f"  Paper pairwise: {config['paper_pairwise']:.4f} pc")
        print(f"  NN/pairwise ratio: {stats['nn_over_pairwise']:.3f}")

    return stats


def main():
    """Main execution."""
    base_path = Path('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA')

    print("="*80)
    print("SIMPLIFIED HGBS NEAREST-NEIGHBOR ANALYSIS")
    print("="*80)

    all_results = {}

    for region_name, config in REGION_CONFIGS.items():
        try:
            result = analyze_region(region_name, config, base_path)
            if result:
                all_results[region_name] = result
        except Exception as e:
            print(f"\nERROR analyzing {region_name}: {e}")
            import traceback
            traceback.print_exc()

    # Save results
    if all_results:
        output_file = base_path / 'nn_analysis_results.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n{'='*80}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*80}")

        # Print comparison table
        print(f"\n{'Region':<12} {'N':>6} {'NN median':>12} {'Paper pairwise':>15} {'NN λ/W':>10} {'Paper λ/W':>10} {'Ratio':>8}")
        print("-" * 80)
        for region_name, stats in all_results.items():
            if 'paper_pairwise' in stats:
                print(f"{region_name:<12} {stats['n_cores']:>6} "
                      f"{stats['nn_median_pc']:>12.4f} ± {stats['nn_sem_pc']:.4f}  "
                      f"{stats['paper_pairwise_pc']:>10.4f}  "
                      f"{stats['nn_lambda_over_W']:>10.2f}  "
                      f"{stats['paper_lambda_over_W']:>10.2f}  "
                      f"{stats['nn_over_pairwise']:>8.3f}")

        # Analyze L/3 convergence concern
        print("\n" + "="*80)
        print("L/3 CONVERGENCE ANALYSIS")
        print("="*80)
        comparisons = [(name, s['nn_over_pairwise'], s['n_cores'], s['nn_median_pc'] > s['paper_pairwise_pc'])
                       for name, s in all_results.items() if 'paper_pairwise' in s]

        if comparisons:
            n_nn_larger = sum(c[3] for c in comparisons)
            print(f"Regions with NN > pairwise: {n_nn_larger}/{len(comparisons)}")
            for name, ratio, n, nn_larger in comparisons:
                status = "✓ NN > Pairwise" if nn_larger else "✗ NN ≤ Pairwise"
                print(f"  {name:<12}: NN/pairwise = {ratio:.3f} ({status})")

            print()
            if n_nn_larger == len(comparisons):
                print("CONCLUSION: All regions show NN > pairwise median, consistent with")
                print("L/3 convergence bias. The pairwise median underestimates true spacing.")
            elif n_nn_larger > len(comparisons) / 2:
                print("CONCLUSION: Most regions show NN > pairwise median, suggesting")
                print("some L/3 convergence bias, particularly for high-N filaments.")
            else:
                print("CONCLUSION: No systematic NN > pairwise bias detected.")

        print("="*80)

    return all_results


if __name__ == '__main__':
    main()
