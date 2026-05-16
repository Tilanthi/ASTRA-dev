#!/usr/bin/env python3
"""
Comprehensive Nearest-Neighbor Analysis for All HGBS Regions

This script calculates nearest-neighbor (NN) spacing statistics for all available
HGBS regions to address the L/3 convergence concern in the filament spacing paper.

Key comparison: Pairwise median vs. NN median to validate the primary result.
"""

import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy.spatial import cKDTree
from scipy import ndimage
from collections import defaultdict
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class HGBSNearestNeighborAnalyzer:
    """Universal analyzer for HGBS regions with different catalog formats."""

    # Region distances (pc) from recent literature
    REGION_DISTANCES = {
        'Orion B': 386,      # Gaia DR3 (Kounkel et al. 2018)
        'Ophiuchus': 137,    # Gaia DR2 (Ortiz-León et al. 2018)
        'Taurus': 145,       # Gaia DR2 (Zucker et al. 2019)
        'TMC1': 145,         # Same as Taurus
        'CRA': 260,          # Aquila Rift complex (Dzib et al. 2020)
        'Serpens': 436,      # Gaia DR2 (Ortiz-León et al. 2018)
        'IC5146': 260,       # IC 5146 (Dame et al. 2020)
        'Perseus': 320,      # Gaia DR2 (Zucker et al. 2019)
        'Aquila': 260,       # Same as CRA (Aquila Rift)
    }

    def __init__(self, region_name: str, skeleton_file: str, catalog_file: str,
                 distance_pc: Optional[float] = None):
        """
        Initialize analyzer for a specific HGBS region.

        Parameters:
        -----------
        region_name : str
            Name of the HGBS region
        skeleton_file : str
            Path to DisPerSE skeleton FITS file
        catalog_file : str
            Path to core catalog (various formats supported)
        distance_pc : float, optional
            Distance in parsecs (uses default if not specified)
        """
        self.region_name = region_name
        self.skeleton_file = skeleton_file
        self.catalog_file = catalog_file
        self.distance_pc = distance_pc or self.REGION_DISTANCES.get(region_name, 200)

        # Data storage
        self.skeleton_data = None
        self.skeleton_header = None
        self.wcs = None
        self.cores = []
        self.filaments = []

    def load_skeleton(self):
        """Load the DisPerSE skeleton map."""
        print(f"Loading skeleton: {self.skeleton_file}")
        hdul = fits.open(self.skeleton_file)
        self.skeleton_data = hdul[0].data.astype(np.float64)
        self.skeleton_header = hdul[0].header

        try:
            from astropy.wcs import WCS
            self.wcs = WCS(self.skeleton_header)
        except Exception as e:
            print(f"Warning: No WCS in skeleton: {e}")
            self.wcs = None

        hdul.close()
        print(f"  Skeleton shape: {self.skeleton_data.shape}")

    def load_catalog(self):
        """Load core catalog (auto-detect format)."""
        print(f"Loading catalog: {self.catalog_file}")

        # Detect file type
        if self.catalog_file.endswith('.csv'):
            self._load_csv_catalog()
        else:
            self._load_hgbs_text_catalog()

        print(f"  Loaded {len(self.cores)} cores")

    def _load_csv_catalog(self):
        """Load CSV format catalog (e.g., IC5146)."""
        import csv
        with open(self.catalog_file, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                try:
                    self.cores.append({
                        'id': i,
                        'ra': float(row['ra_deg']),
                        'dec': float(row['dec_deg']),
                        'coord': SkyCoord(float(row['ra_deg']), float(row['dec_deg']), unit='deg')
                    })
                except (ValueError, KeyError) as e:
                    continue

    def _load_hgbs_text_catalog(self):
        """Load HGBS standard text catalog format."""
        with open(self.catalog_file, 'r', encoding='latin-1', errors='ignore') as f:
            lines = f.readlines()

        # Find data start (look for first numeric line)
        data_start = None
        for i, line in enumerate(lines):
            # Skip empty, comment, and header lines
            if not line.strip() or line.startswith('|') or line.startswith('!') or \
               line.startswith('-') or 'TABLE' in line or 'Description' in line:
                continue
            # Check if this looks like a data line (starts with number)
            parts = line.split()
            if parts and parts[0].isdigit():
                data_start = i
                break

        if data_start is None:
            print(f"  Warning: Could not find data in catalog")
            return

        # Parse core data
        for line in lines[data_start:]:
            if not line.strip() or line.startswith('|') or line.startswith('!'):
                continue

            parts = line.split()
            if len(parts) < 4:
                continue

            try:
                core_id = int(parts[0])

                # Extract RA/Dec from columns 3 and 4 (sexagesimal format)
                ra_str = parts[2]
                dec_str = parts[3]

                # Clean up the strings (remove colons for parsing)
                ra_clean = ra_str.replace(':', '')
                dec_clean = dec_str.replace(':', '').replace('+', '')

                # Convert to SkyCoord
                coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))

                self.cores.append({
                    'id': core_id,
                    'ra': coord.ra.deg,
                    'dec': coord.dec.deg,
                    'coord': coord
                })
            except (ValueError, IndexError) as e:
                continue

    def extract_filament_spines(self, threshold=0.1, min_length=50):
        """Extract filament spines from skeleton map."""
        print("Extracting filament spines...")

        skeleton_mask = self.skeleton_data > threshold
        labeled, num_features = ndimage.label(skeleton_mask)

        self.filaments = []
        for i in range(1, num_features + 1):
            filament_pixels = np.where(labeled == i)
            n_pixels = len(filament_pixels[0])

            if n_pixels < min_length:
                continue

            y_coords = filament_pixels[0]
            x_coords = filament_pixels[1]
            skeleton_values = self.skeleton_data[y_coords, x_coords]

            order = np.lexsort((x_coords, y_coords))
            ordered_y = y_coords[order]
            ordered_x = x_coords[order]
            ordered_values = skeleton_values[order]

            self.filaments.append({
                'id': i,
                'pixels_y': ordered_y,
                'pixels_x': ordered_x,
                'values': ordered_values,
                'length': n_pixels
            })

        self.filaments.sort(key=lambda f: f['length'], reverse=True)
        print(f"  Extracted {len(self.filaments)} filaments (min {min_length} pixels)")

    def associate_cores_with_filaments(self, max_distance_pixels=15):
        """Associate cores with filaments based on proximity."""
        if self.wcs is None:
            print("  Warning: No WCS, skipping core-filament association")
            return {i: None for i in range(len(self.cores))}

        print(f"Associating cores with filaments (max {max_distance_pixels} px)...")

        core_filament_assoc = {i: None for i in range(len(self.cores))}
        core_filament_distances = {i: np.inf for i in range(len(self.cores))}

        for i, core in enumerate(self.cores):
            try:
                from astropy.wcs import utils
                px, py = utils.skycoord_to_pixel(self.wcs, core['coord'])

                for fil in self.filaments:
                    dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                    min_dist = np.sqrt(np.min(dist_sq))

                    if min_dist < core_filament_distances[i] and min_dist < max_distance_pixels:
                        core_filament_distances[i] = min_dist
                        core_filament_assoc[i] = fil['id']
            except Exception:
                pass

        n_associated = sum(1 for f in core_filament_assoc.values() if f is not None)
        print(f"  Associated {n_associated}/{len(self.cores)} cores")

        return core_filament_assoc

    def compute_nearest_neighbor_spacing(self, max_association_distance=0.15):
        """
        Compute nearest-neighbor spacing for cores.

        Uses two methods:
        1. Simple NN: For all cores, find nearest neighbor
        2. Filament-ordered NN: For cores on filaments, find NN along filament

        Parameters:
        -----------
        max_association_distance : float
            Maximum distance (degrees) to consider cores as part of same filament
        """
        print("Computing nearest-neighbor spacings...")

        if len(self.cores) < 2:
            print("  Warning: Less than 2 cores, skipping NN calculation")
            return np.array([]), np.array([])

        # Method 1: All-pairs NN (simplest approach)
        coords = np.array([[c['ra'], c['dec']] for c in self.cores])
        tree = cKDTree(coords)

        # Query nearest neighbor (distance=2 returns self + NN)
        distances, indices = tree.query(coords, k=2)

        # Extract NN distances (skip self)
        nn_distances_deg = distances[:, 1]

        # Convert to physical distance (pc)
        nn_distances_pc = nn_distances_deg * (np.pi/180) * self.distance_pc

        # Method 2: Filament-ordered NN (if skeleton available)
        filament_nn_pc = []
        if self.filaments and self.wcs is not None:
            core_assoc = self.associate_cores_with_filaments()

            # Group cores by filament
            filament_cores = defaultdict(list)
            for i, fil_id in core_assoc.items():
                if fil_id is not None:
                    filament_cores[fil_id].append(i)

            # For each filament, order cores and compute NN along spine
            for fil_id, core_indices in filament_cores.items():
                if len(core_indices) < 2:
                    continue

                # Get core coordinates for this filament
                fil_coords = SkyCoord(
                    ra=[self.cores[i]['ra'] for i in core_indices] * u.deg,
                    dec=[self.cores[i]['dec'] for i in core_indices] * u.deg
                )

                # Compute separations between adjacent cores along filament
                for i in range(len(fil_coords) - 1):
                    sep = fil_coords[i].separation(fil_coords[i+1])
                    sep_pc = sep.radian * self.distance_pc
                    filament_nn_pc.append(sep_pc)

        return np.array(nn_distances_pc), np.array(filament_nn_pc)

    def analyze_spacing(self, nn_distances_pc, filament_nn_pc):
        """Compute statistics on nearest-neighbor spacings."""
        if len(nn_distances_pc) == 0:
            return {'error': 'No NN distances computed'}

        stats = {
            'region': self.region_name,
            'distance_pc': self.distance_pc,
            'n_cores': len(self.cores),
            'n_nn_spacings': len(nn_distances_pc),
            'nn_min_pc': float(np.min(nn_distances_pc)),
            'nn_max_pc': float(np.max(nn_distances_pc)),
            'nn_mean_pc': float(np.mean(nn_distances_pc)),
            'nn_median_pc': float(np.median(nn_distances_pc)),
            'nn_std_pc': float(np.std(nn_distances_pc)),
            'nn_sem_pc': float(np.std(nn_distances_pc) / np.sqrt(len(nn_distances_pc))),
            'nn_q25_pc': float(np.percentile(nn_distances_pc, 25)),
            'nn_q75_pc': float(np.percentile(nn_distances_pc, 75)),
        }

        # Filament-ordered statistics (if available)
        if len(filament_nn_pc) > 0:
            stats.update({
                'n_filament_cores': len(filament_nn_pc) + 1,  # n_spacings = n_cores - 1
                'n_filament_spacings': len(filament_nn_pc),
                'filament_nn_mean_pc': float(np.mean(filament_nn_pc)),
                'filament_nn_median_pc': float(np.median(filament_nn_pc)),
                'filament_nn_std_pc': float(np.std(filament_nn_pc)),
                'filament_nn_sem_pc': float(np.std(filament_nn_pc) / np.sqrt(len(filament_nn_pc))),
            })
        else:
            stats.update({
                'n_filament_cores': 0,
                'n_filament_spacings': 0,
                'filament_nn_mean_pc': np.nan,
                'filament_nn_median_pc': np.nan,
            })

        return stats

    def run_full_analysis(self):
        """Run the complete analysis pipeline."""
        print("=" * 70)
        print(f"Analyzing {self.region_name}")
        print("=" * 70)

        # Load data
        self.load_skeleton()
        self.load_catalog()

        # Extract filaments (optional, for filament-ordered NN)
        try:
            self.extract_filament_spines()
        except Exception as e:
            print(f"  Warning: Filament extraction failed: {e}")

        # Compute NN spacings
        nn_pc, filament_nn_pc = self.compute_nearest_neighbor_spacing()

        # Analyze
        stats = self.analyze_spacing(nn_pc, filament_nn_pc)

        # Print summary
        print("\nNEAREST-NEIGHBOR SPACING STATISTICS")
        print("-" * 50)
        print(f"N_cores: {stats['n_cores']}")
        print(f"NN median: {stats['nn_median_pc']:.4f} ± {stats['nn_sem_pc']:.4f} pc")
        print(f"NN mean:   {stats['nn_mean_pc']:.4f} ± {stats['nn_sem_pc']:.4f} pc")
        if stats['n_filament_spacings'] > 0:
            print(f"Filament NN median: {stats['filament_nn_median_pc']:.4f} ± {stats['filament_nn_sem_pc']:.4f} pc")
        print("=" * 70)

        return stats, nn_pc, filament_nn_pc


def analyze_all_regions(base_path: str) -> Dict:
    """
    Analyze all available HGBS regions.

    Returns:
    --------
    Dictionary with results for all regions
    """
    base_path = Path(base_path)

    # Define region configurations
    regions = [
        {
            'name': 'Orion B',
            'folder': 'HGBS_ORIB',
            'skeleton': 'HGBS_orionB_skeleton_map_thresh50.fits',
            'catalog': 'HGBS_orionb_derived_core_catalog.txt',
            'distance': 386,
        },
        {
            'name': 'Ophiuchus',
            'folder': 'HGBS_OPH',
            'skeleton': 'HGBS_oph_l1688_skeleton_map_thresh50.fits',
            'catalog': 'HGBS_ophiuchus_derived_core_catalog.txt',
            'distance': 137,
        },
        {
            'name': 'Taurus',
            'folder': 'HGBS_TAURUS',
            'skeleton': 'HGBS_taurusL1495_skeleton_map_thresh50.fits',
            'catalog': 'HGBS_taurusL1495_derived_core_catalog.txt',
            'distance': 145,
        },
        {
            'name': 'TMC1',
            'folder': 'HGBS_TMC1',
            'skeleton': 'HGBS_taurusTMC1_skeleton_map_thresh50.fits',
            'catalog': 'HGBS_taurusTMC1_derived_core_catalog.txt',
            'distance': 145,
        },
        {
            'name': 'CRA',
            'folder': 'HGBS_CRA',
            'skeleton': 'HGBS_craNS_skeleton_map_thresh50.fits',
            'catalog': 'HGBS_craNS_derived_core_catalog.txt',
            'distance': 260,
        },
        {
            'name': 'Serpens',
            'folder': 'HGBS_SERPENS',
            'skeleton': 'HGBS_serpens_skeleton_map_thresh50.fits',
            'catalog': 'HGBS_serpens_observed_core_catalog.txt',
            'distance': 436,
        },
        {
            'name': 'IC5146',
            'folder': 'HGBS_IC5146',
            'skeleton': 'HGBS_ic5146_skeleton_map.fits',
            'catalog': 'core_catalog_ic5146.csv',
            'distance': 260,
        },
    ]

    all_results = {}
    all_nn_distances = {}

    for region_config in regions:
        region_name = region_config['name']
        folder = base_path / region_config['folder']
        skeleton_file = folder / region_config['skeleton']
        catalog_file = folder / region_config['catalog']

        # Skip if files don't exist
        if not skeleton_file.exists():
            print(f"\nSkipping {region_name}: skeleton file not found")
            continue
        if not catalog_file.exists():
            print(f"\nSkipping {region_name}: catalog file not found")
            continue

        try:
            analyzer = HGBSNearestNeighborAnalyzer(
                region_name=region_name,
                skeleton_file=str(skeleton_file),
                catalog_file=str(catalog_file),
                distance_pc=region_config['distance']
            )

            stats, nn_pc, filament_nn_pc = analyzer.run_full_analysis()
            all_results[region_name] = stats
            all_nn_distances[region_name] = nn_pc

        except Exception as e:
            print(f"\nError analyzing {region_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    return all_results, all_nn_distances


def compare_with_paper_data(nn_results: Dict) -> None:
    """
    Compare NN results with paper's pairwise median values.

    Prints comparison table and analyzes L/3 convergence concern.
    """
    print("\n" + "=" * 80)
    print("COMPARISON WITH PAPER PAIRWISE MEDIAN VALUES")
    print("=" * 80)

    # Paper values from Table 3 (pairwise median, width-normalized)
    paper_values = {
        'Orion B': {'pairwise_pc': 0.360, 'lambda_over_W': 2.84},
        'Ophiuchus': {'pairwise_pc': 0.309, 'lambda_over_W': 3.09},
        'Taurus': {'pairwise_pc': 0.326, 'lambda_over_W': 3.26},
        'IC5146': {'pairwise_pc': 0.270, 'lambda_over_W': 2.70},
        # Note: Some regions might have different values
    }

    # Characteristic filament width (Herschel resolution)
    W_pc = 0.127  # ~18 arcsec at typical distances

    print(f"\n{'Region':<12} {'N':>6} {'NN median':>12} {'Paper pairwise':>15} {'NN λ/W':>10} {'Paper λ/W':>10} {'Ratio':>8}")
    print("-" * 80)

    for region_name, stats in nn_results.items():
        nn_median = stats['nn_median_pc']
        n_cores = stats['n_cores']
        nn_lambda_over_W = nn_median / W_pc

        if region_name in paper_values:
            paper_pairwise = paper_values[region_name]['pairwise_pc']
            paper_lambda_over_W = paper_values[region_name]['lambda_over_W']
            ratio = nn_median / paper_pairwise if paper_pairwise > 0 else np.nan

            print(f"{region_name:<12} {n_cores:>6} {nn_median:>12.4f} ± {stats['nn_sem_pc']:.4f}  "
                  f"{paper_pairwise:>10.4f}  {nn_lambda_over_W:>10.2f}  {paper_lambda_over_W:>10.2f}  "
                  f"{ratio:>8.3f}")
        else:
            print(f"{region_name:<12} {n_cores:>6} {nn_median:>12.4f} ± {stats['nn_sem_pc']:.4f}  "
                  f"{'N/A':>10}  {nn_lambda_over_W:>10.2f}  {'N/A':>10}  {'N/A':>8}")

    print("=" * 80)

    # Analyze L/3 convergence concern
    print("\nL/3 CONVERGENCE ANALYSIS")
    print("-" * 80)
    print("The L/3 convergence concern posits that for filaments with many cores,")
    print("the pairwise median statistic converges to ~L/3, which may bias the result.")
    print()

    # Check if NN > pairwise (expected if L/3 bias exists)
    comparisons = []
    for region_name, stats in nn_results.items():
        if region_name in paper_values:
            nn_median = stats['nn_median_pc']
            paper_pairwise = paper_values[region_name]['pairwise_pc']
            ratio = nn_median / paper_pairwise
            n_cores = stats['n_cores']

            comparisons.append({
                'region': region_name,
                'ratio': ratio,
                'n_cores': n_cores,
                'nn_larger': nn_median > paper_pairwise
            })

    if comparisons:
        print(f"{'Region':<12} {'N_cores':>8} {'NN/Pairwise':>12} {'NN > Pairwise?':>15}")
        print("-" * 50)
        for comp in comparisons:
            print(f"{comp['region']:<12} {comp['n_cores']:>8} {comp['ratio']:>12.3f}  "
                  f"{'Yes' if comp['nn_larger'] else 'No':>15}")

        print()

        # Summary
        n_nn_larger = sum(c['nn_larger'] for c in comparisons)
        print(f"Summary: {n_nn_larger}/{len(comparisons)} regions show NN > pairwise median")
        print()

        if n_nn_larger == len(comparisons):
            print("CONCLUSION: All regions show NN > pairwise median, consistent with")
            print("the expected L/3 convergence bias. The pairwise median underestimates")
            print("true core spacing, particularly for high-N filaments like Orion B.")
        elif n_nn_larger > len(comparisons) / 2:
            print("CONCLUSION: Most regions show NN > pairwise median, suggesting some")
            print("L/3 convergence bias exists. The effect is most significant for")
            print("high-N filaments.")
        else:
            print("CONCLUSION: No systematic NN > pairwise bias detected. The pairwise")
            print("median appears robust against L/3 convergence concerns.")

    print("=" * 80)


def main():
    """Main execution function."""
    # Set base path
    base_path = Path('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA')

    print("COMPREHENSIVE HGBS NEAREST-NEIGHBOR ANALYSIS")
    print("=" * 80)
    print(f"Base path: {base_path}")
    print()

    # Analyze all regions
    all_results, all_nn_distances = analyze_all_regions(base_path)

    # Save results
    output_file = base_path / 'nn_analysis_results.json'
    with open(output_file, 'w') as f:
        # Convert numpy types for JSON serialization
        serializable_results = {}
        for region, stats in all_results.items():
            serializable_results[region] = {
                k: (float(v) if isinstance(v, (np.floating, np.integer)) else
                    int(v) if isinstance(v, np.integer) else v)
                for k, v in stats.items()
            }
        json.dump(serializable_results, f, indent=2)
    print(f"\nResults saved to: {output_file}")

    # Compare with paper values
    if all_results:
        compare_with_paper_data(all_results)

        # Generate summary statistics
        print("\n" + "=" * 80)
        print("OVERALL SUMMARY")
        print("=" * 80)

        total_cores = sum(r['n_cores'] for r in all_results.values())
        print(f"Total cores analyzed: {total_cores}")

        # Compute weighted mean of NN spacings
        nn_means = [r['nn_mean_pc'] for r in all_results.values()]
        nn_weights = [r['n_cores'] for r in all_results.values()]
        weighted_nn_mean = np.average(nn_means, weights=nn_weights)
        weighted_nn_sem = np.sqrt(sum((w**2) * (r['nn_sem_pc']**2)
                                      for w, r in zip(nn_weights, all_results.values())) /
                                 sum(nn_weights)**2)

        print(f"Weighted NN mean: {weighted_nn_mean:.4f} ± {weighted_nn_sem:.4f} pc")
        print(f"λ/W (NN-based): {weighted_nn_mean / 0.127:.2f}")
        print()

        return all_results

    return None


if __name__ == '__main__':
    results = main()
