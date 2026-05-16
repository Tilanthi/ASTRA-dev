#!/usr/bin/env python3
"""
Analyze Real HGBS Core Spacing Distributions

This script analyzes actual HGBS core catalog data to determine:
1. What is the actual core spacing distribution (not just medians)?
2. Do HGBS filaments show single-filament or multi-fiber signatures?
3. Which statistic (PM or NN) correctly measures fragmentation wavelength?

Author: ASTRA Analysis System
Date: 2026-05-02
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple
import json


class HGBSCoreCatalog:
    """Parse and analyze HGBS core catalog files"""

    def __init__(self, catalog_path: str):
        self.catalog_path = Path(catalog_path)
        self.region_name = self._extract_region_name()
        self.cores = []
        self.load_catalog()

    def _extract_region_name(self) -> str:
        """Extract region name from catalog path"""
        path_str = str(self.catalog_path)
        if 'HGBS_TAURUS' in path_str or 'taurus' in path_str.lower():
            return 'Taurus'
        elif 'HGBS_PERSEUS' in path_str or 'perseus' in path_str.lower():
            return 'Perseus'
        elif 'HGBS_AQUILA' in path_str or 'aquila' in path_str.lower():
            return 'Aquila'
        elif 'HGBS_ORIB' in path_str or 'orion' in path_str.lower():
            return 'OrionB'
        elif 'HGBS_OPH' in path_str or 'ophiuchus' in path_str.lower():
            return 'Ophiuchus'
        elif 'HGBS_CRA' in path_str or 'corona' in path_str.lower():
            return 'CoronaAustralis'
        elif 'HGBS_SERPENS' in path_str or 'serpens' in path_str.lower():
            return 'Serpens'
        elif 'W3' in path_str.upper() or 'IC1848' in path_str.upper():
            return 'W3'
        else:
            return 'Unknown'

    def load_catalog(self):
        """Load core positions from catalog file"""
        if not self.catalog_path.exists():
            print(f"Warning: Catalog not found: {self.catalog_path}")
            return

        try:
            with open(self.catalog_path, 'r') as f:
                lines = f.readlines()

            # Find data start (skip header lines starting with # or \)
            data_start = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if not stripped or stripped.startswith('#') or stripped.startswith('\\'):
                    continue
                data_start = i
                break

            # Parse data lines
            for line in lines[data_start:]:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if len(parts) < 4:
                    continue

                try:
                    # Extract RA and Dec (typically columns 3-4 in HGBS catalogs)
                    # Format: HH:MM:SS.s DD:MM:SS.s
                    ra_str = parts[2]
                    dec_str = parts[3]

                    # Convert to degrees
                    ra_deg = self._hms_to_degrees(ra_str)
                    dec_deg = self._dms_to_degrees(dec_str)

                    self.cores.append({
                        'ra': ra_deg,
                        'dec': dec_deg,
                        'ra_str': ra_str,
                        'dec_str': dec_str
                    })
                except (ValueError, IndexError) as e:
                    continue

            print(f"Loaded {len(self.cores)} cores from {self.region_name}")

        except Exception as e:
            print(f"Error loading catalog {self.catalog_path}: {e}")

    def _hms_to_degrees(self, hms_str: str) -> float:
        """Convert HH:MM:SS.s to degrees"""
        parts = hms_str.split(':')
        if len(parts) != 3:
            raise ValueError(f"Invalid RA format: {hms_str}")

        h = float(parts[0])
        m = float(parts[1])
        s = float(parts[2])

        return 15.0 * (h + m/60.0 + s/3600.0)

    def _dms_to_degrees(self, dms_str: str) -> float:
        """Convert DD:MM:SS.s to degrees"""
        # Handle sign
        sign = 1
        if dms_str.startswith('-'):
            sign = -1
            dms_str = dms_str[1:]

        parts = dms_str.split(':')
        if len(parts) != 3:
            raise ValueError(f"Invalid Dec format: {dms_str}")

        d = float(parts[0])
        m = float(parts[1])
        s = float(parts[2])

        return sign * (d + m/60.0 + s/3600.0)

    def compute_angular_separations(self) -> Tuple[np.ndarray, np.ndarray]:
        """Compute angular separations between cores in arcminutes"""
        n_cores = len(self.cores)
        if n_cores < 2:
            return np.array([]), np.array([])

        # Compute all pairwise angular separations
        ra = np.array([c['ra'] for c in self.cores])
        dec = np.array([c['dec'] for c in self.cores])

        pairwise_seps = []
        adjacent_seps = []

        # Sort by RA to get ordering along filament (approximate)
        sort_idx = np.argsort(ra)
        ra_sorted = ra[sort_idx]
        dec_sorted = dec[sort_idx]

        # Adjacent spacings (nearest-neighbor along sorted order)
        for i in range(n_cores - 1):
            sep = self._angular_separation(ra_sorted[i], dec_sorted[i],
                                          ra_sorted[i+1], dec_sorted[i+1])
            adjacent_seps.append(sep * 60)  # Convert to arcmin

        # Pairwise spacings
        for i in range(n_cores):
            for j in range(i+1, n_cores):
                sep = self._angular_separation(ra[i], dec[i], ra[j], dec[j])
                pairwise_seps.append(sep * 60)  # Convert to arcmin

        return np.array(adjacent_seps), np.array(pairwise_seps)

    def _angular_separation(self, ra1, dec1, ra2, dec2) -> float:
        """Compute angular separation in degrees"""
        # Convert to radians
        ra1_rad = np.radians(ra1)
        dec1_rad = np.radians(dec1)
        ra2_rad = np.radians(ra2)
        dec2_rad = np.radians(dec2)

        # Haversine formula
        dra = ra2_rad - ra1_rad
        ddec = dec2_rad - dec1_rad

        a = np.sin(ddec/2)**2 + np.cos(dec1_rad) * np.cos(dec2_rad) * np.sin(dra/2)**2
        sep = 2 * np.arcsin(np.sqrt(a))

        return np.degrees(sep)

    def compute_statistics(self) -> Dict:
        """Compute PM and NN statistics"""
        adjacent_seps, pairwise_seps = self.compute_angular_separations()

        if len(adjacent_seps) == 0 or len(pairwise_seps) == 0:
            return {
                'region': self.region_name,
                'n_cores': len(self.cores),
                'nn_arcmin': np.nan,
                'pm_arcmin': np.nan,
                'nn_pm_ratio': np.nan
            }

        nn = np.median(adjacent_seps)
        pm = np.median(pairwise_seps)

        return {
            'region': self.region_name,
            'n_cores': len(self.cores),
            'nn_arcmin': nn,
            'pm_arcmin': pm,
            'nn_pm_ratio': nn / pm if pm > 0 else np.nan,
            'adjacent_separations': adjacent_seps.tolist(),
            'pairwise_separations': pairwise_seps.tolist()
        }


def analyze_all_hgbs_regions():
    """Analyze all available HGBS core catalogs"""

    # Search for HGBS catalog files
    base_paths = [
        '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_CRA',
        '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS',
        '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB',
        '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH',
        '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS',
        '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA',
        '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS',
        '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1',
        '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_W3',
    ]

    catalogs = []

    for base_path in base_paths:
        base = Path(base_path)
        if not base.exists():
            continue

        # Look for catalog files
        catalog_files = list(base.glob('*catalog*.txt'))
        for cat_file in catalog_files:
            print(f"Found catalog: {cat_file}")
            try:
                catalog = HGBSCoreCatalog(str(cat_file))
                if len(catalog.cores) > 0:
                    catalogs.append(catalog)
            except Exception as e:
                print(f"Error loading {cat_file}: {e}")

    # Also check directly in ASTRA directory
    astra_base = Path('/Users/gjw255/astrodata/SWARM/ASTRA')
    for catalog_file in astra_base.glob('HGBS_*/**/*catalog*.txt'):
        print(f"Found catalog: {catalog_file}")
        try:
            catalog = HGBSCoreCatalog(str(catalog_file))
            if len(catalog.cores) > 0:
                catalogs.append(catalog)
        except Exception as e:
            print(f"Error loading {catalog_file}: {e}")

    print(f"\nTotal catalogs loaded: {len(catalogs)}")

    return catalogs


def plot_spacing_distributions(catalogs: List[HGBSCoreCatalog], output_dir: str):
    """Generate spacing distribution plots for all regions"""

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Filter to catalogs with enough cores
    valid_catalogs = [c for c in catalogs if len(c.cores) >= 5]

    if len(valid_catalogs) == 0:
        print("ERROR: No catalogs with sufficient cores found!")
        return

    print(f"\nGenerating plots for {len(valid_catalogs)} regions with sufficient cores...")

    # Create combined plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('HGBS Core Spacing Distributions: NN vs PM', fontsize=14, fontweight='bold')

    colors = plt.cm.tab10(np.linspace(0, 1, len(valid_catalogs)))

    # Plot 1: Adjacent spacing distributions (NN)
    ax = axes[0, 0]
    for i, catalog in enumerate(valid_catalogs):
        adj, _ = catalog.compute_angular_separations()
        if len(adj) > 0:
            ax.hist(adj, bins=15, alpha=0.5, label=catalog.region_name, color=colors[i])
    ax.set_xlabel('Adjacent Spacing (arcmin)', fontsize=11)
    ax.set_ylabel('Number of Core Pairs', fontsize=11)
    ax.set_title('Nearest-Neighbor (Adjacent) Spacing Distributions', fontsize=11, fontweight='bold')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    # Plot 2: Pairwise spacing distributions (PM)
    ax = axes[0, 1]
    for i, catalog in enumerate(valid_catalogs):
        _, pair = catalog.compute_angular_separations()
        if len(pair) > 0:
            ax.hist(pair, bins=30, alpha=0.5, label=catalog.region_name, color=colors[i])
    ax.set_xlabel('Pairwise Spacing (arcmin)', fontsize=11)
    ax.set_ylabel('Number of Core Pairs', fontsize=11)
    ax.set_title('Pairwise-Median Spacing Distributions', fontsize=11, fontweight='bold')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    # Plot 3: NN vs PM comparison
    ax = axes[1, 0]
    regions = []
    nn_values = []
    pm_values = []

    for catalog in valid_catalogs:
        stats = catalog.compute_statistics()
        if not np.isnan(stats['nn_arcmin']) and not np.isnan(stats['pm_arcmin']):
            regions.append(stats['region'])
            nn_values.append(stats['nn_arcmin'])
            pm_values.append(stats['pm_arcmin'])

    x_pos = np.arange(len(regions))
    width = 0.35

    ax.bar(x_pos - width/2, nn_values, width, label='NN (Adjacent)', alpha=0.8, color='steelblue')
    ax.bar(x_pos + width/2, pm_values, width, label='PM (Pairwise)', alpha=0.8, color='coral')
    ax.set_xlabel('Region', fontsize=11)
    ax.set_ylabel('Median Spacing (arcmin)', fontsize=11)
    ax.set_title('NN vs PM Comparison by Region', fontsize=11, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(regions, rotation=45, ha='right', fontsize=9)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, axis='y')

    # Plot 4: NN/PM ratio
    ax = axes[1, 1]
    nn_pm_ratios = []

    for catalog in valid_catalogs:
        stats = catalog.compute_statistics()
        if not np.isnan(stats['nn_pm_ratio']):
            nn_pm_ratios.append(stats['nn_pm_ratio'])

    if nn_pm_ratios:
        ax.bar(regions, nn_pm_ratios, color='mediumseagreen', alpha=0.8)
        ax.axhline(y=0.31, color='red', linestyle='--', label='HGBS lower bound (0.31)')
        ax.axhline(y=0.73, color='red', linestyle='--', label='HGBS upper bound (0.73)')
        ax.axhline(y=0.125, color='blue', linestyle=':', label='Single-filament prediction (0.125)')
        ax.set_xlabel('Region', fontsize=11)
        ax.set_ylabel('NN / PM Ratio', fontsize=11)
        ax.set_title('NN/PM Ratio by Region', fontsize=11, fontweight='bold')
        ax.set_xticklabels(regions, rotation=45, ha='right', fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3, axis='y')
        ax.set_ylim(0, max(max(nn_pm_ratios) * 1.2, 1.0))

    plt.tight_layout()
    plt.savefig(output_path / 'hgbs_spacing_distributions.png', dpi=150, bbox_inches='tight')
    plt.savefig(output_path / 'hgbs_spacing_distributions.pdf', bbox_inches='tight')
    print(f"Saved combined plot to: {output_path / 'hgbs_spacing_distributions.pdf'}")

    # Generate individual region plots
    for catalog in valid_catalogs:
        adj, pair = catalog.compute_angular_separations()

        if len(adj) == 0 or len(pair) == 0:
            continue

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        fig.suptitle(f'{catalog.region_name}: Core Spacing Distribution (N={len(catalog.cores)})',
                    fontsize=13, fontweight='bold')

        # Adjacent spacing histogram
        axes[0].hist(adj, bins=max(5, len(adj)//3), color='steelblue', alpha=0.7, edgecolor='black')
        axes[0].axvline(np.median(adj), color='red', linestyle='--', linewidth=2,
                       label=f'Median (NN): {np.median(adj):.2f}\'')
        axes[0].set_xlabel('Adjacent Spacing (arcmin)', fontsize=11)
        axes[0].set_ylabel('Frequency', fontsize=11)
        axes[0].set_title('Nearest-Neighbor Spacing Distribution', fontsize=11)
        axes[0].legend()
        axes[0].grid(alpha=0.3)

        # Pairwise spacing histogram
        axes[1].hist(pair, bins=max(10, len(pair)//5), color='coral', alpha=0.7, edgecolor='black')
        axes[1].axvline(np.median(pair), color='red', linestyle='--', linewidth=2,
                       label=f'Median (PM): {np.median(pair):.2f}\'')
        axes[1].set_xlabel('Pairwise Spacing (arcmin)', fontsize=11)
        axes[1].set_ylabel('Frequency', fontsize=11)
        axes[1].set_title('Pairwise-Median Spacing Distribution', fontsize=11)
        axes[1].legend()
        axes[1].grid(alpha=0.3)

        plt.tight_layout()
        safe_name = catalog.region_name.replace(' ', '_')
        plt.savefig(output_path / f'{safe_name}_spacing_distribution.png', dpi=150, bbox_inches='tight')
        plt.savefig(output_path / f'{safe_name}_spacing_distribution.pdf', bbox_inches='tight')
        plt.close()

    print(f"Generated individual plots for {len(valid_catalogs)} regions")


def generate_statistics_summary(catalogs: List[HGBSCoreCatalog], output_dir: str):
    """Generate summary statistics table"""

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Collect statistics
    all_stats = []
    for catalog in catalogs:
        stats = catalog.compute_statistics()
        all_stats.append(stats)

    # Filter to valid results
    valid_stats = [s for s in all_stats if not np.isnan(s['nn_arcmin'])]

    if len(valid_stats) == 0:
        print("ERROR: No valid statistics found!")
        return

    # Sort by region name
    valid_stats.sort(key=lambda x: x['region'])

    # Print table
    print("\n" + "=" * 90)
    print("HGBS CORE SPACING STATISTICS SUMMARY")
    print("=" * 90)
    print(f"{'Region':<20} {'N_cores':<10} {'NN (arcmin)':<15} {'PM (arcmin)':<15} {'NN/PM':<10}")
    print("-" * 90)

    for stats in valid_stats:
        print(f"{stats['region']:<20} {stats['n_cores']:<10} "
             f"{stats['nn_arcmin']:<15.3f} {stats['pm_arcmin']:<15.3f} {stats['nn_pm_ratio']:<10.3f}")

    print("-" * 90)

    # Compute averages
    avg_nn = np.mean([s['nn_arcmin'] for s in valid_stats])
    avg_pm = np.mean([s['pm_arcmin'] for s in valid_stats])
    avg_ratio = np.mean([s['nn_pm_ratio'] for s in valid_stats])

    print(f"{'AVERAGE':<20} {'':<10} {avg_nn:<15.3f} {avg_pm:<15.3f} {avg_ratio:<10.3f}")
    print("=" * 90)

    # Compare with literature values
    print("\nCOMPARISON WITH LITERATURE VALUES:")
    print("-" * 90)

    # Literature values from paper (in pc, assuming distance ~ 140 pc for typical regions)
    # Convert arcmin to pc at 140 pc: 1 arcmin = 0.0408 pc
    dist_pc = 140.0
    arcmin_to_pc = np.pi / (180 * 60) * dist_pc

    print(f"(Assuming typical distance {dist_pc} pc, 1 arcmin = {arcmin_to_pc:.4f} pc)")
    print()

    for stats in valid_stats:
        nn_pc = stats['nn_arcmin'] * arcmin_to_pc
        pm_pc = stats['pm_arcmin'] * arcmin_to_pc

        print(f"{stats['region']}:")
        print(f"  NN = {nn_pc:.3f} pc, PM = {pm_pc:.3f} pc")

        # Compare with literature values if available
        if stats['region'] == 'Taurus':
            print(f"    Literature: NN = 0.062 pc (expected), Measured = {nn_pc:.3f} pc")
        elif stats['region'] == 'Perseus':
            print(f"    Literature: NN = 0.182 pc (expected), Measured = {nn_pc:.3f} pc")
        elif stats['region'] == 'Aquila':
            print(f"    Literature: NN = 0.161 pc (expected), Measured = {nn_pc:.3f} pc")

    # Save to JSON
    output_file = output_path / 'hgbs_spacing_statistics.json'
    with open(output_file, 'w') as f:
        json.dump(valid_stats, f, indent=2)

    print(f"\nStatistics saved to: {output_file}")


def analyze_distribution_shape(catalogs: List[HGBSCoreCatalog], output_dir: str):
    """Analyze the shape of spacing distributions to infer filament structure"""

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print("\n" + "=" * 90)
    print("DISTRIBUTION SHAPE ANALYSIS: Single vs Multi-Fiber Signatures")
    print("=" * 90)

    results = []

    for catalog in catalogs:
        adj, _ = catalog.compute_angular_separations()

        if len(adj) < 5:
            continue

        # Compute shape metrics
        median = np.median(adj)
        std = np.std(adj)
        cv = std / median if median > 0 else np.nan  # Coefficient of variation

        # Test for multimodality (Hartigan's Dip Test approximation)
        # Simple version: count peaks in histogram
        hist, bins = np.histogram(adj, bins=max(5, len(adj)//3))
        n_peaks = 0
        for i in range(1, len(hist)-1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1]:
                n_peaks += 1

        # Assess distribution shape
        # Single-filament prediction: narrow distribution (CV < 0.3), single peak
        # Multi-fiber prediction: broad distribution (CV > 0.5), multiple peaks

        is_single_filament = cv < 0.4 and n_peaks <= 2
        is_multi_fiber = cv > 0.5 or n_peaks >= 3

        result = {
            'region': catalog.region_name,
            'n_cores': len(catalog.cores),
            'n_spacings': len(adj),
            'median_arcmin': median,
            'std_arcmin': std,
            'cv': cv,
            'n_peaks': n_peaks,
            'single_filament_signature': is_single_filament,
            'multi_fiber_signature': is_multi_fiber,
            'interpretation': 'Single filament' if is_single_filament else 'Multi-fiber' if is_multi_fiber else 'Ambiguous'
        }

        results.append(result)

        print(f"\n{catalog.region_name}:")
        print(f"  Median spacing: {median:.3f} arcmin")
        print(f"  Std deviation: {std:.3f} arcmin")
        print(f"  Coefficient of variation: {cv:.3f}")
        print(f"  Number of peaks: {n_peaks}")
        print(f"  Signature: {result['interpretation']}")

    # Save results
    output_file = output_path / 'distribution_shape_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nShape analysis saved to: {output_file}")

    return results


def main():
    """Main analysis pipeline"""

    print("=" * 90)
    print("HGBS CORE SPACING DISTRIBUTION ANALYSIS")
    print("=" * 90)
    print("\nLoading HGBS core catalogs...")

    # Load all catalogs
    catalogs = analyze_all_hgbs_regions()

    if len(catalogs) == 0:
        print("\nERROR: No HGBS catalogs found!")
        print("\nPlease check that HGBS data files exist in:")
        print("  /Users/gjw255/astrodata/SWARM/ASTRA/HGBS_*/")
        return

    # Create output directory
    output_dir = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/HGBS_analysis_results'

    # Generate plots
    print("\nGenerating spacing distribution plots...")
    plot_spacing_distributions(catalogs, output_dir)

    # Generate statistics summary
    print("\nGenerating statistics summary...")
    generate_statistics_summary(catalogs, output_dir)

    # Analyze distribution shapes
    print("\nAnalyzing distribution shapes...")
    shape_results = analyze_distribution_shape(catalogs, output_dir)

    # Final summary
    print("\n" + "=" * 90)
    print("ANALYSIS COMPLETE")
    print("=" * 90)
    print(f"\nResults saved to: {output_dir}")
    print("\nKey files:")
    print(f"  - hgbs_spacing_distributions.pdf: Combined visualization")
    print(f"  - hgbs_spacing_statistics.json: Numerical results")
    print(f"  - distribution_shape_analysis.json: Single vs multi-fiber assessment")
    print(f"  - *_spacing_distribution.pdf: Individual region plots")

    print("\nInterpretation:")
    single_count = sum(1 for r in shape_results if r.get('single_filament_signature', False))
    multi_count = sum(1 for r in shape_results if r.get('multi_fiber_signature', False))
    print(f"  Single-filament signatures: {single_count} regions")
    print(f"  Multi-fiber signatures: {multi_count} regions")
    print(f"  Ambiguous: {len(shape_results) - single_count - multi_count} regions")

    if single_count > multi_count:
        print("\nCONCLUSION: Most HGBS filaments show SINGLE-FILAMENT signatures")
        print("  This supports NN as the correct statistic for measuring fragmentation wavelength")
    elif multi_count > single_count:
        print("\nCONCLUSION: Most HGBS filaments show MULTI-FIBER signatures")
        print("  This supports PM as measuring the true filament-scale fragmentation")
    else:
        print("\nCONCLUSION: Mixed or ambiguous results")
        print("  Further analysis needed to resolve PM vs NN")


if __name__ == '__main__':
    main()
