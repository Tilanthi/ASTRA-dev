#!/usr/bin/env python3
"""
Robust Nearest-Neighbor Analysis for HGBS Regions

Handles multiple catalog formats and provides comprehensive statistics.
"""

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy.spatial import cKDTree
import json
from pathlib import Path
from typing import Dict, List, Tuple
import re


REGION_CONFIGS = {
    'Orion B': {
        'folder': 'HGBS_ORIB',
        'skeleton': 'HGBS_orionB_skeleton_map_thresh50.fits',
        'catalog': 'HGBS_orionb_derived_core_catalog.txt',
        'distance': 386,
        'paper_pairwise': 0.360,
        'paper_lambda_over_W': 2.84,
        'catalog_format': 'standard',  # RA/Dec in single columns
    },
    'Ophiuchus': {
        'folder': 'HGBS_OPH',
        'skeleton': 'HGBS_oph_l1688_skeleton_map_thresh50.fits',
        'catalog': 'HGBS_ophiuchus_derived_core_catalog.txt',
        'distance': 137,
        'paper_pairwise': 0.309,
        'paper_lambda_over_W': 3.09,
        'catalog_format': 'standard',
    },
    'Taurus': {
        'folder': 'HGBS_TAURUS',
        'skeleton': 'HGBS_taurusL1495_skeleton_map_thresh50.fits',
        'catalog': 'HGBS_taurusL1495_derived_core_catalog.txt',
        'distance': 145,
        'paper_pairwise': 0.326,
        'paper_lambda_over_W': 3.26,
        'catalog_format': 'split',  # RA/Dec split into multiple columns
    },
    'TMC1': {
        'folder': 'HGBS_TMC1',
        'skeleton': 'HGBS_taurusTMC1_skeleton_map_thresh50.fits',
        'catalog': 'HGBS_taurusTMC1_derived_core_catalog.txt',
        'distance': 145,
        'catalog_format': 'split',
    },
    'CRA': {
        'folder': 'HGBS_CRA',
        'skeleton': 'HGBS_craNS_skeleton_map_thresh50.fits',
        'catalog': 'HGBS_craNS_derived_core_catalog.txt',
        'distance': 260,
        'catalog_format': 'standard',
    },
    'Serpens': {
        'folder': 'HGBS_SERPENS',
        'skeleton': 'HGBS_serpens_skeleton_map_thresh50.fits',
        'catalog': 'HGBS_serpens_observed_core_catalog.txt',
        'distance': 436,
        'catalog_format': 'observed',  # Observed catalog format
    },
    'IC5146': {
        'folder': 'HGBS_IC5146',
        'skeleton': 'HGBS_ic5146_skeleton_map.fits',
        'catalog': 'core_catalog_ic5146.csv',
        'distance': 260,
        'paper_pairwise': 0.270,
        'paper_lambda_over_W': 2.70,
        'catalog_format': 'csv',
    },
}


def load_catalog_standard(catalog_file: str) -> List[Dict]:
    """
    Load standard HGBS catalog format (RA/Dec in single columns).
    Example: Orion B, Ophiuchus, CRA
    """
    cores = []
    with open(catalog_file, 'r', encoding='latin-1', errors='ignore') as f:
        lines = f.readlines()

    # Find data start
    data_start = None
    for i, line in enumerate(lines):
        if not line.strip() or line.startswith('|') or line.startswith('!') or \
           line.startswith('-') or 'TABLE' in line or 'Description' in line or 'runNO' in line:
            continue
        parts = line.split()
        if parts and parts[0].isdigit() and len(parts) >= 4:
            # Try to parse RA/Dec from columns 3 and 4
            try:
                ra_str = parts[2]
                dec_str = parts[3]
                coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
                data_start = i
                break
            except:
                continue

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


def load_catalog_split(catalog_file: str) -> List[Dict]:
    """
    Load split-format HGBS catalog (RA/Dec split into multiple columns).
    Example: Taurus, TMC1

    Format: ID  NAME  HH MM SS.S  +DD MM SS ...
    """
    cores = []
    with open(catalog_file, 'r', encoding='latin-1', errors='ignore') as f:
        lines = f.readlines()

    # Find data start
    data_start = None
    for i, line in enumerate(lines):
        if not line.strip() or line.startswith('|') or line.startswith('!') or \
           line.startswith('-') or 'TABLE' in line or 'Description' in line or 'runNO' in line:
            continue
        parts = line.split()
        if parts and parts[0].isdigit() and len(parts) >= 9:
            data_start = i
            break

    if data_start is None:
        return cores

    # Parse data
    for line in lines[data_start:]:
        if not line.strip() or line.startswith('|') or line.startswith('!'):
            continue

        parts = line.split()
        if len(parts) < 9:
            continue

        try:
            core_id = int(parts[0])

            # RA: HH MM SS.S
            ra_h = parts[2]
            ra_m = parts[3]
            ra_s = parts[4]
            ra_str = f"{ra_h}:{ra_m}:{ra_s}"

            # Dec: +DD MM SS or -DD MM SS
            dec_sign = parts[5]
            dec_d = parts[6]
            dec_m = parts[7]
            dec_s = parts[8]
            dec_str = f"{dec_sign}{dec_d}:{dec_m}:{dec_s}"

            coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))

            cores.append({
                'id': core_id,
                'ra': coord.ra.deg,
                'dec': coord.dec.deg,
            })
        except (ValueError, IndexError):
            continue

    return cores


def load_catalog_observed(catalog_file: str) -> List[Dict]:
    """
    Load observed catalog format (Serpens).
    Similar to standard but with different header format.
    """
    # Serpens observed catalog has similar format to standard
    # Let's try both standard and split methods
    cores = load_catalog_standard(catalog_file)
    if not cores:
        cores = load_catalog_split(catalog_file)
    return cores


def load_catalog_csv(catalog_file: str) -> List[Dict]:
    """Load CSV format catalog (IC5146)."""
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


def load_catalog_auto(catalog_file: str, format_hint: str = None) -> List[Dict]:
    """
    Auto-detect and load catalog format.

    Parameters:
    -----------
    catalog_file : str
        Path to catalog file
    format_hint : str, optional
        Hint for catalog format ('standard', 'split', 'observed', 'csv')

    Returns:
    --------
    List of core dictionaries with 'id', 'ra', 'dec' keys
    """
    if format_hint == 'csv':
        return load_catalog_csv(catalog_file)
    elif format_hint == 'split':
        return load_catalog_split(catalog_file)
    elif format_hint == 'observed':
        return load_catalog_observed(catalog_file)
    elif format_hint == 'standard':
        return load_catalog_standard(catalog_file)
    else:
        # Auto-detect: try CSV first, then standard, then split
        if catalog_file.endswith('.csv'):
            cores = load_catalog_csv(catalog_file)
            if cores:
                return cores

        cores = load_catalog_standard(catalog_file)
        if cores:
            return cores

        cores = load_catalog_split(catalog_file)
        if cores:
            return cores

        return load_catalog_observed(catalog_file)


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
    print(f"  Format: {config.get('catalog_format', 'auto-detect')}")

    cores = load_catalog_auto(str(catalog_file), config.get('catalog_format'))

    print(f"  Loaded {len(cores)} cores")

    if len(cores) == 0:
        print("ERROR: No cores loaded")
        return None

    # Verify coordinates are reasonable
    ra_vals = [c['ra'] for c in cores]
    dec_vals = [c['dec'] for c in cores]
    print(f"  RA range: {min(ra_vals):.2f} - {max(ra_vals):.2f} deg")
    print(f"  Dec range: {min(dec_vals):.2f} - {max(dec_vals):.2f} deg")

    # Compute NN spacing
    print("Computing nearest-neighbor spacing...")
    stats = compute_nn_spacing(cores, config['distance'])
    stats['region'] = region_name
    stats['distance_pc'] = config['distance']

    # Add paper comparison
    if 'paper_pairwise' in config:
        stats['paper_pairwise_pc'] = config['paper_pairwise']
        stats['paper_lambda_over_W'] = config['paper_lambda_over_W']
        W_pc = 0.127  # Characteristic filament width
        stats['nn_lambda_over_W'] = stats['nn_median_pc'] / W_pc
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
    print("ROBUST HGBS NEAREST-NEIGHBOR ANALYSIS")
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
        W_pc = 0.127  # Characteristic filament width
        print(f"\n{'Region':<12} {'N':>6} {'NN median':>14} {'Paper pairwise':>15} {'NN λ/W':>10} {'Paper λ/W':>10} {'Ratio':>8}")
        print("-" * 85)
        for region_name, stats in all_results.items():
            if 'paper_pairwise' in stats:
                print(f"{region_name:<12} {stats['n_cores']:>6} "
                      f"{stats['nn_median_pc']:>8.4f} ± {stats['nn_sem_pc']:.4f}  "
                      f"{stats['paper_pairwise_pc']:>10.4f}  "
                      f"{stats['nn_lambda_over_W']:>10.2f}  "
                      f"{stats['paper_lambda_over_W']:>10.2f}  "
                      f"{stats['nn_over_pairwise']:>8.3f}")
            else:
                print(f"{region_name:<12} {stats['n_cores']:>6} "
                      f"{stats['nn_median_pc']:>8.4f} ± {stats['nn_sem_pc']:.4f}  "
                      f"{'N/A':>10}  "
                      f"{stats['nn_median_pc']/W_pc:>10.2f}  "
                      f"{'N/A':>10}  {'N/A':>8}")

        # Analyze L/3 convergence concern
        print("\n" + "="*85)
        print("L/3 CONVERGENCE ANALYSIS")
        print("="*85)
        comparisons = [(name, s['nn_over_pairwise'], s['n_cores'], s['nn_median_pc'] > s['paper_pairwise_pc'])
                       for name, s in all_results.items() if 'paper_pairwise' in s]

        if comparisons:
            n_nn_larger = sum(c[3] for c in comparisons)
            print(f"Regions with NN > pairwise: {n_nn_larger}/{len(comparisons)}")
            print()
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
                print("The NN values are SMALLER than pairwise, contrary to L/3 convergence.")
                print("This suggests the pairwise median may be measuring a different quantity")
                print("(possibly filament-ordered cores vs. all-pairs).")

        print("="*85)

    return all_results


if __name__ == '__main__':
    main()
