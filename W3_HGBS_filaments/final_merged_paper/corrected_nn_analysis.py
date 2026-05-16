#!/usr/bin/env python3
"""
Corrected Nearest-Neighbor Analysis for HGBS Regions

This script properly handles HGBS catalog format and computes accurate NN spacing.

Author: ASTRA Analysis System
Date: 2026-05-05
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.spatial import cKDTree
from pathlib import Path
import json
import sys

try:
    from astropy.io import fits
    from astropy import units as u
    from astropy.coordinates import SkyCoord
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False
    print("Error: astropy is required for this analysis")
    sys.exit(1)


def parse_hgbs_catalog(catalog_file):
    """
    Parse HGBS catalog file, handling the specific format.

    Returns list of cores with RA, Dec in degrees.
    """
    cores = []

    with open(catalog_file, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    # Skip header lines - look for lines starting with numbers
    # Data lines have format like:
    #   61   054058.0-020729   05:40:58.09   -02:07:29.5   3.7e-02  ...
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip comment lines
        if line.startswith('|') or line.startswith('#'):
            continue

        # Try to parse as data line
        parts = line.split()
        if len(parts) < 4:
            continue

        # First column should be a number (core ID)
        try:
            core_id = int(parts[0])
        except ValueError:
            continue

        # RA and Dec are in columns 3 and 4 (indices 2 and 3)
        # Format: HH:MM:SS.S or HH:MM:SS.ss
        #         DD:MM:SS.S or -DD:MM:SS.ss
        try:
            ra_str = parts[2]
            dec_str = parts[3]

            # Parse coordinates
            coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))

            cores.append({
                'id': core_id,
                'ra': coord.ra.deg,
                'dec': coord.dec.deg,
                'coord': coord
            })
        except Exception as e:
            # Skip problematic lines
            continue

    print(f"  Parsed {len(cores)} cores from catalog")
    return cores


def compute_nn_spacing(cores, distance_pc, max_separation_arcmin=5):
    """
    Compute nearest-neighbor spacing for cores.

    Parameters:
    -----------
    cores : list of dict
        List of cores with 'ra' and 'dec' in degrees
    distance_pc : float
        Distance to region in parsecs
    max_separation_arcmin : float
        Maximum separation to consider as valid NN pair (helps exclude
        cores on different filaments)

    Returns:
    --------
    nn_spacings : ndarray
        Array of NN spacings in parsecs
    """
    if len(cores) < 2:
        return np.array([])

    # Build coordinate array
    coords = np.array([[c['ra'], c['dec']] for c in cores])

    # Scale RA by cos(mean_dec) to account for spherical geometry
    mean_dec = np.mean(coords[:, 1])
    ra_scale = np.cos(np.radians(mean_dec))
    coords_scaled = coords * [ra_scale, 1.0]

    # Build KD-tree for efficient neighbor search
    tree = cKDTree(coords_scaled)

    # Find 2 nearest neighbors (first is self, second is true NN)
    dists, indices = tree.query(coords_scaled, k=2)

    # Get NN distances (second column)
    nn_distances_deg = dists[:, 1]

    # Convert to physical distance
    # Small angle approximation: distance ≈ angular_separation_rad * distance
    nn_distances_rad = np.radians(nn_distances_deg)
    nn_distances_pc = nn_distances_rad * distance_pc

    # Filter out excessively large separations (likely different filaments)
    max_sep_pc = (max_separation_arcmin / 60.0) * (np.pi / 180.0) * distance_pc
    valid_mask = nn_distances_pc < max_sep_pc

    nn_spacings = nn_distances_pc[valid_mask]

    return nn_spacings


def analyze_region(name, catalog_file, distance_pc, filament_width_pc=0.1,
                   published_pm_lambda_w=None, max_separation_arcmin=5):
    """
    Analyze a single HGBS region.

    Returns dictionary with analysis results.
    """
    print(f"\n{'='*70}")
    print(f"ANALYZING: {name}")
    print(f"{'='*70}")

    # Load catalog
    print(f"Loading catalog from: {catalog_file}")
    cores = parse_hgbs_catalog(catalog_file)

    if len(cores) == 0:
        print(f"ERROR: No cores loaded!")
        return None

    print(f"  N_cores = {len(cores)}")
    print(f"  Distance = {distance_pc} pc")

    # Compute NN spacing
    print(f"\nComputing NN spacing (max separation: {max_separation_arcmin} arcmin)...")
    nn_spacings = compute_nn_spacing(cores, distance_pc, max_separation_arcmin)

    if len(nn_spacings) == 0:
        print(f"  ERROR: No valid NN pairs found!")
        return None

    # Compute statistics
    nn_median = np.median(nn_spacings)
    nn_mean = np.mean(nn_spacings)
    nn_std = np.std(nn_spacings)
    nn_sem = nn_std / np.sqrt(len(nn_spacings))

    # Compute λ/W
    nn_lambda_w = nn_median / filament_width_pc

    print(f"  NN pairs = {len(nn_spacings)}")
    print(f"  NN median = {nn_median:.4f} pc")
    print(f"  NN mean = {nn_mean:.4f} pc")
    print(f"  NN std = {nn_std:.4f} pc")
    print(f"  NN SEM = {nn_sem:.4f} pc")
    print(f"  λ/W (NN) = {nn_lambda_w:.2f}")

    # Check for PM/L3 convergence problem
    if len(cores) >= 500:
        print(f"\n  *** PM/L3 CONVERGENCE WARNING ***")
        print(f"  N_cores = {len(cores)} ≥ 500: PM value likely unreliable")
        print(f"  Published PM λ/W = {published_pm_lambda_w if published_pm_lambda_w else 'N/A'}")
        print(f"  NN λ/W (this analysis) = {nn_lambda_w:.2f}")
        print(f"  *******************************")

    # Return results
    results = {
        'name': name,
        'n_cores': len(cores),
        'n_nn_pairs': len(nn_spacings),
        'distance_pc': distance_pc,
        'filament_width_pc': filament_width_pc,
        'nn_median_pc': nn_median,
        'nn_mean_pc': nn_mean,
        'nn_std_pc': nn_std,
        'nn_sem_pc': nn_sem,
        'nn_lambda_w': nn_lambda_w,
        'published_pm_lambda_w': published_pm_lambda_w,
        'nn_spacings': nn_spacings.tolist(),
    }

    return results


def run_all_regions():
    """
    Run NN analysis for all HGBS regions.
    """
    print("="*80)
    print("COMPREHENSIVE NN ANALYSIS FOR HGBS REGIONS")
    print("="*80)

    base_path = Path('/Users/gjw255/astrodata/SWARM/ASTRA')

    # Region configurations
    regions = [
        {
            'name': 'Orion B',
            'catalog': base_path / 'HGBS_ORIB' / 'HGBS_orionB_derived_core_catalog.txt',
            'distance_pc': 386,
            'published_pm_lambda_w': 3.13,
        },
        {
            'name': 'Taurus',
            'catalog': base_path / 'HGBS_TAURUS' / 'HGBS_taurusL1495_derived_core_catalog.txt',
            'distance_pc': 145,
            'published_pm_lambda_w': 1.98,
        },
        {
            'name': 'Serpens',
            'catalog': base_path / 'HGBS_SERPENS' / 'HGBS_serpens_observed_core_catalog.txt',
            'distance_pc': 436,
            'published_pm_lambda_w': 2.5,
        },
        {
            'name': 'IC5146',
            'catalog': base_path / 'HGBS_IC5146' / 'HGBS_ic5146_derived_core_catalog.txt',
            'distance_pc': 463,
            'published_pm_lambda_w': 2.8,
        },
    ]

    all_results = {}

    for region_config in regions:
        name = region_config['name']
        catalog_file = region_config['catalog']

        # Skip if catalog doesn't exist
        if not Path(catalog_file).exists():
            print(f"\nSkipping {name}: catalog file not found")
            continue

        result = analyze_region(
            name=name,
            catalog_file=str(catalog_file),
            distance_pc=region_config['distance_pc'],
            filament_width_pc=0.1,
            published_pm_lambda_w=region_config['published_pm_lambda_w'],
            max_separation_arcmin=5
        )

        if result:
            all_results[name] = result

    # Generate summary
    print(f"\n{'='*80}")
    print("SUMMARY RESULTS")
    print(f"{'='*80}")

    print(f"\n{'Region':<15} {'N':>6} {'NN λ/W':>10} {'NN SEM':>10} {'PM λ/W':>10} {'PM/NN':>8}")
    print("-"*80)

    for name, res in all_results.items():
        nn_lw = res['nn_lambda_w']
        nn_sem = res['nn_sem']
        pm_lw = res['published_pm_lambda_w']
        ratio = pm_lw / nn_lw if pm_lw else None

        print(f"{name:<15} {res['n_cores']:>6} {nn_lw:>10.2f} {nn_sem:>10.4f} "
              f"{pm_lw:>10.2f if pm_lw else 'N/A':>10} "
              f"{ratio:>8.2f if ratio else 'N/A':>8}")

    # Calculate weighted statistics
    print(f"\n{'='*80}")
    print("WEIGHTED STATISTICS")
    print(f"{'='*80}")

    # Separate large-N and small-N regions
    large_n = {n: r for n, r in all_results.items() if r['n_cores'] >= 500}
    small_n = {n: r for n, r in all_results.items() if r['n_cores'] < 500}

    if small_n:
        # Weighted NN for small-N regions only (reliable PM)
        total_cores_small = sum(r['n_cores'] for r in small_n.values())
        weighted_nn_small = sum(r['n_cores'] * r['nn_lambda_w'] for r in small_n.values()) / total_cores_small
        print(f"Weighted NN λ/W (N < 500): {weighted_nn_small:.2f}")

    # Weighted NN for all regions
    total_cores_all = sum(r['n_cores'] for r in all_results.values())
    weighted_nn_all = sum(r['n_cores'] * r['nn_lambda_w'] for r in all_results.values()) / total_cores_all
    print(f"Weighted NN λ/W (all regions): {weighted_nn_all:.2f}")

    # Published PM weighted mean
    weighted_pm = sum(r['n_cores'] * r['published_pm_lambda_w'] for r in all_results.values() if r['published_pm_lambda_w']) / total_cores_all
    print(f"Published PM λ/W (all regions): {weighted_pm:.2f}")

    print(f"\nPM/NN ratio: {weighted_pm/weighted_nn_all:.2f}")

    # Generate figure
    generate_figure(all_results, output_dir=Path('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/figures'))

    # Save results
    output_file = Path('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/nn_analysis_results.json')
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return all_results


def generate_figure(results, output_dir):
    """Generate comparison figure for paper."""
    output_dir.mkdir(exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Nearest-Neighbor Analysis: Addressing PM/L3 Convergence', fontsize=16, fontweight='bold')

    region_names = list(results.keys())
    nn_values = [results[r]['nn_lambda_w'] for r in region_names]
    nn_sems = [results[r]['nn_sem'] / 0.1 for r in region_names]  # Convert to λ/W units
    pm_values = [results[r]['published_pm_lambda_w'] for r in region_names]
    n_cores = [results[r]['n_cores'] for r in region_names]

    # Colors: red for N ≥ 500
    colors = ['red' if n >= 500 else 'steelblue' for n in n_cores]

    # Panel (a): NN vs PM comparison
    ax = axes[0, 0]
    x = np.arange(len(region_names))
    width = 0.35

    bars1 = ax.bar(x - width/2, nn_values, width, label='Nearest-Neighbor', color=colors, alpha=0.7, edgecolor='black')
    bars2 = ax.bar(x + width/2, pm_values, width, label='Pairwise Median', color='purple', alpha=0.7, edgecolor='black')

    ax.axhline(y=4.0, color='green', linestyle='--', linewidth=2, label='Classical IM92')
    ax.axhline(y=1.25, color='orange', linestyle='--', linewidth=2, label='Perpendicular-field min')

    ax.set_ylabel('$\\lambda/W$', fontsize=12)
    ax.set_title('(a) NN vs PM λ/W Comparison', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(region_names, rotation=45, ha='right')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim([0, 5])

    # Panel (b): NN with error bars
    ax = axes[0, 1]
    ax.errorbar(region_names, nn_values, yerr=nn_sems, fmt='o', color='steelblue',
                capsize=10, markersize=10, linewidth=2)

    ax.axhline(y=4.0, color='green', linestyle='--', linewidth=2, label='Classical IM92')
    ax.axhline(y=2.84, color='blue', linestyle=':', linewidth=2, label='Published PM mean')

    ax.set_ylabel('$\\lambda/W$', fontsize=12)
    ax.set_title('(b) NN λ/W with Uncertainties', fontsize=13, fontweight='bold')
    ax.set_xticklabels(region_names, rotation=45, ha='right')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim([0, 5])

    # Panel (c): PM/NN ratio
    ax = axes[1, 0]

    ratios = [pm/nn if (pm and nn) else 1.0 for pm, nn in zip(pm_values, nn_values)]

    bars = ax.bar(region_names, ratios, color=colors, alpha=0.7, edgecolor='black')
    ax.axhline(y=1.0, color='black', linestyle='--', linewidth=2, label='PM = NN')

    ax.set_ylabel('PM / NN Ratio', fontsize=12)
    ax.set_title('(c) PM Convergence Test', fontsize=13, fontweight='bold')
    ax.set_xticklabels(region_names, rotation=45, ha='right')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # Add ratio values and warnings
    for bar, val, n in zip(bars, ratios, n_cores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        if n >= 500:
            ax.text(bar.get_x() + bar.get_width()/2., height - 0.1,
                    'L/3\nartifact', ha='center', va='top', fontsize=8, color='red', fontweight='bold')

    # Panel (d): Summary text
    ax = axes[1, 1]
    ax.axis('off')

    # Calculate statistics
    total_cores = sum(n_cores)
    large_n_regions = [n for n, r in zip(region_names, n_cores) if r >= 500]

    small_n_regions_data = [(r['n_cores'], r['nn_lambda_w']) for r in results.values() if r['n_cores'] < 500]
    if small_n_regions_data:
        weighted_nn_small = sum(n * nn for n, nn in small_n_regions_data) / sum(n for n, _ in small_n_regions_data)
    else:
        weighted_nn_small = np.nan

    weighted_nn_all = sum(r['n_cores'] * r['nn_lambda_w'] for r in results.values()) / total_cores
    weighted_pm = sum(r['n_cores'] * r['published_pm_lambda_w'] for r in results.values() if r['published_pm_lambda_w']) / total_cores

    summary = f"""
NN ANALYSIS SUMMARY

Total cores: {total_cores}
Regions with N ≥ 500: {len(large_n_regions)}
Large-N regions: {', '.join(large_n_regions)}

KEY RESULTS:

NN λ/W (small N only): {weighted_nn_small:.2f}
NN λ/W (all regions): {weighted_nn_all:.2f}
Published PM λ/W: {weighted_pm:.2f}

PM/NN ratio: {weighted_pm/weighted_nn_all:.2f}

INTERPRETATION:

• Regions with N ≥ 500 cores have PM values
  that likely reflect the L/3 convergence
  artifact rather than true spacing

• The NN analysis provides the true
  fragmentation wavelength

• The "true" observational λ/W from NN
  analysis is {weighted_nn_all:.2f}, compared to
  the PM-derived value of {weighted_pm:.2f}

• This {((weighted_pm-weighted_nn_all)/4*100):+.0f}% discrepancy from the
  classical IM92 prediction (4×)
    """

    ax.text(0.05, 0.95, summary, transform=ax.transAxes,
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    ax.set_title('(d) Summary and Interpretation', fontsize=13, fontweight='bold', pad=20)

    plt.tight_layout()

    # Save
    pdf_file = output_dir / 'nn_vs_pm_comparison.pdf'
    png_file = output_dir / 'nn_vs_pm_comparison.png'

    plt.savefig(pdf_file, dpi=300, bbox_inches='tight')
    plt.savefig(png_file, dpi=300, bbox_inches='tight')

    print(f"\nFigure saved: {pdf_file}")
    print(f"Figure saved: {png_file}")

    return pdf_file, png_file


if __name__ == '__main__':
    results = run_all_regions()

    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
