#!/usr/bin/env python3
"""
Corrected Nearest-Neighbor Analysis for HGBS Regions

Fixes:
1. CRA catalog format (should be 'split' not 'standard')
2. Paper pairwise comparison table display
3. TMC1 catalog loading
"""

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy.spatial import cKDTree
import json
from pathlib import Path
from typing import Dict, List


REGION_CONFIGS = {
    'Orion B': {
        'folder': 'HGBS_ORIB',
        'catalog': 'HGBS_orionb_derived_core_catalog.txt',
        'distance': 386,
        'paper_pairwise_pc': 0.360,
        'paper_lambda_over_W': 2.84,
        'catalog_format': 'standard',
    },
    'Ophiuchus': {
        'folder': 'HGBS_OPH',
        'catalog': 'HGBS_ophiuchus_derived_core_catalog.txt',
        'distance': 137,
        'paper_pairwise_pc': 0.309,
        'paper_lambda_over_W': 3.09,
        'catalog_format': 'standard',
    },
    'Taurus': {
        'folder': 'HGBS_TAURUS',
        'catalog': 'HGBS_taurusL1495_derived_core_catalog.txt',
        'distance': 145,
        'paper_pairwise_pc': 0.326,
        'paper_lambda_over_W': 3.26,
        'catalog_format': 'split',
    },
    'IC5146': {
        'folder': 'HGBS_IC5146',
        'catalog': 'core_catalog_ic5146.csv',
        'distance': 260,
        'paper_pairwise_pc': 0.270,
        'paper_lambda_over_W': 2.70,
        'catalog_format': 'csv',
    },
    'Serpens': {
        'folder': 'HGBS_SERPENS',
        'catalog': 'HGBS_serpens_observed_core_catalog.txt',
        'distance': 436,
        'catalog_format': 'observed',
    },
    'CRA': {
        'folder': 'HGBS_CRA',
        'catalog': 'HGBS_craNS_derived_core_catalog.txt',
        'distance': 260,
        'catalog_format': 'split',  # FIXED: was 'standard'
    },
    'TMC1': {
        'folder': 'HGBS_TMC1',
        'catalog': 'HGBS_taurusTMC1_derived_core_catalog.txt',
        'distance': 145,
        'catalog_format': 'standard',  # TMC1 uses standard format (RA/Dec in single columns)
    },
}


def load_catalog_standard(catalog_file: str) -> List[Dict]:
    """Load standard HGBS catalog format (RA/Dec in single columns)."""
    cores = []
    with open(catalog_file, 'r', encoding='latin-1', errors='ignore') as f:
        lines = f.readlines()

    data_start = None
    for i, line in enumerate(lines):
        if not line.strip() or line.startswith('|') or line.startswith('!') or \
           line.startswith('-') or 'TABLE' in line or 'Description' in line or 'runNO' in line:
            continue
        parts = line.split()
        if parts and parts[0].isdigit() and len(parts) >= 4:
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
    Example: Taurus, TMC1, CRA

    Format: ID  NAME  HH MM SS.S  ±DD MM SS ...
    Dec has sign and degrees together: +DD or -DD
    """
    cores = []
    with open(catalog_file, 'r', encoding='latin-1', errors='ignore') as f:
        lines = f.readlines()

    data_start = None
    for i, line in enumerate(lines):
        if not line.strip() or line.startswith('|') or line.startswith('!') or \
           line.startswith('-') or 'TABLE' in line or 'Description' in line or 'runNO' in line:
            continue
        parts = line.split()
        if parts and parts[0].isdigit() and len(parts) >= 8:
            data_start = i
            break

    if data_start is None:
        return cores

    for line in lines[data_start:]:
        if not line.strip() or line.startswith('|') or line.startswith('!'):
            continue

        parts = line.split()
        if len(parts) < 8:
            continue

        try:
            core_id = int(parts[0])

            # RA: HH MM SS.S
            ra_h = parts[2]
            ra_m = parts[3]
            ra_s = parts[4]
            ra_str = f"{ra_h}:{ra_m}:{ra_s}"

            # Dec: ±DD MM SS (sign with degrees)
            dec_d = parts[5]
            dec_m = parts[6]
            dec_s = parts[7]
            dec_str = f"{dec_d}:{dec_m}:{dec_s}"

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
    """Load observed catalog format (Serpens)."""
    cores = load_catalog_standard(catalog_file)
    if not cores:
        cores = load_catalog_split(catalog_file)
    return cores


def load_catalog_csv(catalog_file: str) -> List[Dict]:
    """
    Load CSV format catalog (IC5146).

    Format: obj_id, mass_Msun, peak_N_cm2, npix, ra_deg, dec_deg, Tdust_median_K, type
    """
    import csv
    cores = []
    with open(catalog_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 0 or row[0].startswith('#'):
                continue

            try:
                if len(row) >= 6:
                    obj_id = int(row[0])
                    ra_deg = float(row[4])
                    dec_deg = float(row[5])

                    cores.append({
                        'id': obj_id,
                        'ra': ra_deg,
                        'dec': dec_deg,
                    })
            except (ValueError, IndexError):
                continue

    return cores


def compute_nn_spacing(cores: List[Dict], distance_pc: float) -> Dict:
    """Compute nearest-neighbor spacing statistics."""
    if len(cores) < 2:
        return {'error': 'Less than 2 cores'}

    coords = np.array([[c['ra'], c['dec']] for c in cores])
    tree = cKDTree(coords)
    distances, _ = tree.query(coords, k=2)

    nn_distances_deg = distances[:, 1]
    nn_distances_pc = nn_distances_deg * (np.pi/180) * distance_pc

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

    print(f"Loading catalog: {catalog_file.name}")
    print(f"  Format: {config.get('catalog_format', 'auto-detect')}")

    catalog_format = config.get('catalog_format')
    if catalog_format == 'csv':
        cores = load_catalog_csv(str(catalog_file))
    elif catalog_format == 'split':
        cores = load_catalog_split(str(catalog_file))
    elif catalog_format == 'observed':
        cores = load_catalog_observed(str(catalog_file))
    else:
        cores = load_catalog_standard(str(catalog_file))

    print(f"  Loaded {len(cores)} cores")

    if len(cores) == 0:
        print("ERROR: No cores loaded")
        return None

    ra_vals = [c['ra'] for c in cores]
    dec_vals = [c['dec'] for c in cores]
    print(f"  RA range: {min(ra_vals):.2f} - {max(ra_vals):.2f} deg")
    print(f"  Dec range: {min(dec_vals):.2f} - {max(dec_vals):.2f} deg")

    print("Computing nearest-neighbor spacing...")
    stats = compute_nn_spacing(cores, config['distance'])
    stats['region'] = region_name
    stats['distance_pc'] = config['distance']

    # Add paper comparison (using correct key)
    if 'paper_pairwise_pc' in config:
        stats['paper_pairwise_pc'] = config['paper_pairwise_pc']
        stats['paper_lambda_over_W'] = config['paper_lambda_over_W']
        W_pc = 0.127
        stats['nn_lambda_over_W'] = stats['nn_median_pc'] / W_pc
        stats['nn_over_pairwise'] = stats['nn_median_pc'] / config['paper_pairwise_pc']

    print(f"\nResults:")
    print(f"  N_cores: {stats['n_cores']}")
    print(f"  NN median: {stats['nn_median_pc']:.4f} ± {stats['nn_sem_pc']:.4f} pc")
    print(f"  NN mean:   {stats['nn_mean_pc']:.4f} ± {stats['nn_sem_pc']:.4f} pc")
    if 'paper_pairwise_pc' in config:
        print(f"  Paper pairwise: {config['paper_pairwise_pc']:.4f} pc")
        print(f"  NN/pairwise ratio: {stats['nn_over_pairwise']:.3f}")

    return stats


def main():
    """Main execution."""
    base_path = Path('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA')

    print("="*80)
    print("CORRECTED HGBS NEAREST-NEIGHBOR ANALYSIS")
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

    if all_results:
        output_file = base_path / 'nn_analysis_results_corrected.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n{'='*80}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*80}")

        W_pc = 0.127
        print(f"\n{'Region':<12} {'N':>6} {'NN median':>14} {'Paper pairwise':>15} {'NN λ/W':>10} {'Paper λ/W':>10} {'Ratio':>8}")
        print("-" * 90)

        for region_name, stats in all_results.items():
            if 'paper_pairwise_pc' in stats:
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

        print("\n" + "="*90)
        print("L/3 CONVERGENCE ANALYSIS")
        print("="*90)
        comparisons = [(name, s['nn_over_pairwise'], s['n_cores'], s['nn_median_pc'] > s['paper_pairwise_pc'])
                       for name, s in all_results.items() if 'paper_pairwise_pc' in s]

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
                print("some L/3 convergence bias.")
            else:
                print("CONCLUSION: No systematic NN > pairwise bias detected.")
                print("All regions show NN < pairwise (ratio < 1).")
                print()
                print("INTERPRETATION:")
                print("The NN (nearest-neighbor) values are consistently SMALLER than the")
                print("paper's pairwise median values. This suggests the paper is measuring")
                print("a different quantity than the simple NN distance.")
                print()
                print("Possible explanations:")
                print("1. Paper's 'pairwise median' may be filament-ordered (spacings along")
                print("   filaments), which would be larger than NN (closest neighbor in 2D)")
                print("2. The paper may have used a different core sample or selection criteria")
                print("3. The paper may have measured core-to-core distances only along identified")
                print("   filaments, not all nearest neighbors in the 2D plane")

        print("="*90)

    return all_results


if __name__ == '__main__':
    main()
