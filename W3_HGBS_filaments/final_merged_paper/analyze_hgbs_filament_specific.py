#!/usr/bin/env python3
"""
Filament-Specific HGBS Core Spacing Analysis

This script computes NN and PM statistics ALONG FILAMENT SKELETONS for HGBS regions.
This is the correct methodology that matches the HGBS literature values.

Author: ASTRA Analysis System
Date: 2026-05-02
"""

import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from scipy.spatial import cKDTree
from scipy import ndimage
from collections import defaultdict
import json
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional


class FilamentSpecificAnalyzer:
    """Compute NN and PM statistics along HGBS filament skeletons."""

    def __init__(self, region_name: str, skeleton_file: str, catalog_file: str,
                 distance_pc: float, width_pc: float = 0.1):
        """
        Initialize analyzer for a specific region.

        Parameters:
        -----------
        region_name : str
            Name of the HGBS region
        skeleton_file : str
            Path to skeleton FITS file
        catalog_file : str
            Path to core catalog file
        distance_pc : float
            Distance to region in parsecs
        width_pc : float
            Characteristic filament width in parsecs
        """
        self.region_name = region_name
        self.skeleton_file = Path(skeleton_file)
        self.catalog_file = Path(catalog_file)
        self.distance_pc = distance_pc
        self.width_pc = width_pc

        # Data containers
        self.skeleton_data = None
        self.skeleton_header = None
        self.wcs = None
        self.cores = []
        self.filaments = []

        # Results
        self.nn_spacings = []
        self.pm_spacings = []
        self.results = {}

    def load_skeleton(self):
        """Load the skeleton map from FITS file."""
        print(f"\n[{self.region_name}] Loading skeleton: {self.skeleton_file.name}")

        if not self.skeleton_file.exists():
            raise FileNotFoundError(f"Skeleton file not found: {self.skeleton_file}")

        try:
            with fits.open(self.skeleton_file) as hdul:
                self.skeleton_data = hdul[0].data.astype(np.float64)
                self.skeleton_header = hdul[0].header

            # Handle NaN values
            self.skeleton_data = np.nan_to_num(self.skeleton_data, nan=0.0)

            print(f"  Skeleton shape: {self.skeleton_data.shape}")
            print(f"  Nonzero pixels: {np.count_nonzero(self.skeleton_data)}")

            # Extract WCS
            self.wcs = WCS(self.skeleton_header)
            print(f"  WCS extracted successfully")

        except Exception as e:
            raise RuntimeError(f"Error loading skeleton: {e}")

    def load_catalog(self):
        """Load core positions from catalog file."""
        print(f"[{self.region_name}] Loading catalog: {self.catalog_file.name}")

        if not self.catalog_file.exists():
            raise FileNotFoundError(f"Catalog file not found: {self.catalog_file}")

        # Try different encodings
        encodings = ['latin-1', 'utf-8', 'iso-8859-1']
        catalog_data = None

        for encoding in encodings:
            try:
                with open(self.catalog_file, 'r', encoding=encoding) as f:
                    catalog_data = f.readlines()
                print(f"  Opened with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue

        if catalog_data is None:
            raise RuntimeError("Could not read catalog file with any encoding")

        # Find data start (skip header lines)
        data_start = 0
        for i, line in enumerate(catalog_data):
            stripped = line.strip()
            # Skip empty lines, comments, and header markers
            if not stripped or stripped.startswith('#') or stripped.startswith('\\'):
                continue
            # Check if this looks like data (starts with number)
            parts = stripped.split()
            if len(parts) >= 5 and parts[0].isdigit():
                data_start = i
                break

        # Parse core data
        n_loaded = 0
        for line in catalog_data[data_start:]:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) < 5:
                continue

            try:
                # Different catalog formats may have different column orders
                # Try to find RA/Dec columns
                ra_str = None
                dec_str = None

                # Common formats:
                # Format 1: ID Name RA Dec ...
                # Format 2: ID RA Dec ...
                # Look for sexagesimal format (contains :)

                for i, part in enumerate(parts[2:6]):  # Check columns 2-5
                    if ':' in part:
                        if ra_str is None:
                            ra_str = part
                        elif dec_str is None:
                            dec_str = part
                            break

                if ra_str and dec_str:
                    coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))

                    self.cores.append({
                        'ra': coord.ra.deg,
                        'dec': coord.dec.deg,
                        'coord': coord
                    })
                    n_loaded += 1

            except (ValueError, IndexError):
                continue

        print(f"  Loaded {n_loaded} cores from catalog")

        if n_loaded == 0:
            raise RuntimeError("No cores loaded from catalog")

    def extract_filament_spines(self, threshold_percentile: float = 50.0,
                                min_length_pixels: int = 30):
        """
        Extract filament spines from skeleton map.

        Parameters:
        -----------
        threshold_percentile : float
            Percentile of skeleton values to use as threshold
        min_length_pixels : int
            Minimum filament length in pixels
        """
        print(f"[{self.region_name}] Extracting filament spines...")

        # Compute adaptive threshold
        nonzero_values = self.skeleton_data[self.skeleton_data > 0]
        if len(nonzero_values) == 0:
            raise RuntimeError("No nonzero values in skeleton map!")

        threshold = np.percentile(nonzero_values, threshold_percentile)
        print(f"  Threshold: {threshold:.4f} ({threshold_percentile}th percentile)")

        # Create binary mask
        skeleton_mask = self.skeleton_data > threshold

        # Label connected components
        labeled, num_features = ndimage.label(skeleton_mask)
        print(f"  Found {num_features} candidate filaments")

        # Extract each filament
        self.filaments = []

        for i in range(1, num_features + 1):
            filament_mask = labeled == i
            n_pixels = np.sum(filament_mask)

            if n_pixels < min_length_pixels:
                continue

            # Get pixel coordinates
            y_coords, x_coords = np.where(filament_mask)

            # Order along filament (simplified: use PCA direction)
            # Compute principal direction
            coords = np.column_stack([x_coords, y_coords])
            center = np.mean(coords, axis=0)

            # PCA to find primary direction
            cov = np.cov(coords.T)
            evals, evecs = np.linalg.eig(cov)
            primary_dir = evecs[:, np.argmax(evals)]

            # Project points onto primary direction for ordering
            projections = np.dot(coords - center, primary_dir)
            order = np.argsort(projections)

            self.filaments.append({
                'id': i,
                'pixels_y': y_coords[order],
                'pixels_x': x_coords[order],
                'length': n_pixels,
                'center': center
            })

        print(f"  Extracted {len(self.filaments)} filaments (>= {min_length_pixels} pixels)")

        # Sort by length
        self.filaments.sort(key=lambda f: f['length'], reverse=True)

    def associate_cores_with_filaments(self, max_distance_pixels: float = 15.0):
        """
        Associate cores with nearest filament.

        Parameters:
        -----------
        max_distance_pixels : float
            Maximum distance for core-filament association
        """
        print(f"[{self.region_name}] Associating cores with filaments...")

        filament_cores = defaultdict(list)

        for i, core in enumerate(self.cores):
            try:
                # Convert core position to pixels
                from astropy.wcs.utils import skycoord_to_pixel
                px, py = skycoord_to_pixel(self.wcs, core['coord'])

                # Find nearest filament
                min_dist = np.inf
                nearest_filament = None

                for fil in self.filaments:
                    # Compute minimum distance to this filament
                    dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                    dist = np.sqrt(np.min(dist_sq))

                    if dist < min_dist:
                        min_dist = dist
                        nearest_filament = fil

                if min_dist < max_distance_pixels and nearest_filament is not None:
                    filament_cores[nearest_filament['id']].append(i)

            except Exception:
                # Core outside skeleton map bounds
                continue

        n_associated = sum(len(cores) for cores in filament_cores.values())
        print(f"  Associated {n_associated}/{len(self.cores)} cores with filaments")

        return filament_cores

    def order_cores_along_filaments(self, filament_cores: Dict) -> Dict:
        """
        Order cores along each filament by projection onto spine.

        Parameters:
        -----------
        filament_cores : dict
            Mapping from filament ID to list of core indices
        """
        print(f"[{self.region_name}] Ordering cores along filaments...")

        ordered_filament_cores = {}

        for fil_id, core_indices in filament_cores.items():
            if len(core_indices) < 2:
                continue

            # Get filament
            fil = next(f for f in self.filaments if f['id'] == fil_id)

            # Project each core onto filament
            core_positions = []

            for core_idx in core_indices:
                core = self.cores[core_idx]
                try:
                    from astropy.wcs.utils import skycoord_to_pixel
                    px, py = skycoord_to_pixel(self.wcs, core['coord'])

                    # Find nearest point on filament
                    dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                    nearest_idx = np.argmin(dist_sq)

                    # Use index along ordered filament as position
                    core_positions.append((nearest_idx, core_idx))

                except Exception:
                    continue

            # Sort by position along filament
            core_positions.sort(key=lambda x: x[0])

            # Store ordered core indices
            ordered_filament_cores[fil_id] = [c[1] for c in core_positions]

        n_filaments_with_cores = len(ordered_filament_cores)
        print(f"  {n_filaments_with_cores} filaments have >= 2 cores")

        return ordered_filament_cores

    def compute_statistics(self, filament_cores: Dict):
        """
        Compute NN and PM statistics along filaments.

        Parameters:
        -----------
        filament_cores : dict
            Ordered cores along each filament
        """
        print(f"[{self.region_name}] Computing NN and PM statistics...")

        all_nn_spacings = []
        all_pm_spacings = []

        for fil_id, core_indices in filament_cores.items():
            if len(core_indices) < 2:
                continue

            # Get core coordinates
            coords = SkyCoord(
                ra=[self.cores[i]['ra'] for i in core_indices] * u.deg,
                dec=[self.cores[i]['dec'] for i in core_indices] * u.deg
            )

            # NN: adjacent core spacings
            for i in range(len(coords) - 1):
                sep = coords[i].separation(coords[i+1])
                sep_pc = sep.radian * self.distance_pc
                all_nn_spacings.append(sep_pc)

            # PM: all pairwise spacings within this filament
            for i in range(len(coords)):
                for j in range(i+1, len(coords)):
                    sep = coords[i].separation(coords[j])
                    sep_pc = sep.radian * self.distance_pc
                    all_pm_spacings.append(sep_pc)

        self.nn_spacings = np.array(all_nn_spacings)
        self.pm_spacings = np.array(all_pm_spacings)

        print(f"  NN spacings: {len(self.nn_spacings)}")
        print(f"  PM spacings: {len(self.pm_spacings)}")

    def analyze_results(self):
        """Analyze and summarize the results."""
        if len(self.nn_spacings) == 0 or len(self.pm_spacings) == 0:
            print(f"[{self.region_name}] ERROR: No spacings computed!")
            return

        # Compute statistics
        nn_median = np.median(self.nn_spacings)
        pm_median = np.median(self.pm_spacings)
        nn_pm_ratio = nn_median / pm_median if pm_median > 0 else np.nan

        # Compute lambda/W
        lambda_by_W_nn = nn_median / self.width_pc
        lambda_by_W_pm = pm_median / self.width_pc

        self.results = {
            'region': self.region_name,
            'distance_pc': self.distance_pc,
            'width_pc': self.width_pc,
            'n_cores_total': len(self.cores),
            'n_filaments': len(self.filaments),
            'n_nn_spacings': len(self.nn_spacings),
            'n_pm_spacings': len(self.pm_spacings),

            # NN statistics
            'nn_median_pc': nn_median,
            'nn_mean_pc': np.mean(self.nn_spacings),
            'nn_std_pc': np.std(self.nn_spacings),
            'nn_min_pc': np.min(self.nn_spacings),
            'nn_max_pc': np.max(self.nn_spacings),
            'nn_lambda_by_W': lambda_by_W_nn,

            # PM statistics
            'pm_median_pc': pm_median,
            'pm_mean_pc': np.mean(self.pm_spacings),
            'pm_std_pc': np.std(self.pm_spacings),
            'pm_min_pc': np.min(self.pm_spacings),
            'pm_max_pc': np.max(self.pm_spacings),
            'pm_lambda_by_W': lambda_by_W_pm,

            # Ratio
            'nn_pm_ratio': nn_pm_ratio,

            # Distribution shape
            'nn_cv': np.std(self.nn_spacings) / nn_median if nn_median > 0 else np.nan,
        }

        # Print summary
        print(f"\n{'='*70}")
        print(f"{self.region_name}: FILAMENT-SPECIFIC SPACING RESULTS")
        print(f"{'='*70}")
        print(f"Cores: {self.results['n_cores_total']}, Filaments: {self.results['n_filaments']}")
        print(f"\nNN (Nearest-Neighbor):")
        print(f"  Median: {nn_median:.4f} pc")
        print(f"  λ/W: {lambda_by_W_nn:.2f}")
        print(f"\nPM (Pairwise-Median):")
        print(f"  Median: {pm_median:.4f} pc")
        print(f"  λ/W: {lambda_by_W_pm:.2f}")
        print(f"\nRatio:")
        print(f"  NN/PM: {nn_pm_ratio:.3f}")
        print(f"{'='*70}")

    def run_full_analysis(self):
        """Run the complete analysis pipeline."""
        try:
            self.load_skeleton()
            self.load_catalog()
            self.extract_filament_spines()
            filament_cores = self.associate_cores_with_filaments()
            ordered_cores = self.order_cores_along_filaments(filament_cores)
            self.compute_statistics(ordered_cores)
            self.analyze_results()
            return True
        except Exception as e:
            print(f"[{self.region_name}] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


# Define HGBS regions with their data
HGBS_REGIONS = {
    'Ophiuchus': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH/HGBS_oph_l1688_skeleton_map.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH/HGBS_ophiuchus_observed_core_catalog.txt',
        'distance': 140,  # pc
        'width': 0.1,  # pc
    },
    'Perseus': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS/HGBS_perseus_skeleton_map.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS/HGBS_PERSEUS/HGBS_perseus_observed_core_catalog.txt',
        'distance': 280,  # pc
        'width': 0.1,  # pc
    },
    'Taurus': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1/HGBS_taurusTMC1_skeleton_map.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1/HGBS_taurusTMC1_observed_core_catalog.txt',
        'distance': 140,  # pc
        'width': 0.1,  # pc
    },
    'OrionB': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/HGBS_orionb_derived_core_catalog.txt',
        'distance': 386,  # pc
        'width': 0.1,  # pc
    },
}


def analyze_all_regions():
    """Analyze all available HGBS regions."""

    print("="*80)
    print("FILAMENT-SPECIFIC HGBS CORE SPACING ANALYSIS")
    print("="*80)
    print("\nThis analysis computes NN and PM statistics ALONG FILAMENT SKELETONS")
    print("to resolve the PM vs NN discrepancy definitively.\n")

    results_list = []

    for region_name, config in HGBS_REGIONS.items():
        print(f"\n{'#'*80}")
        print(f"# ANALYZING {region_name.upper()}")
        print(f"{'#'*80}")

        try:
            analyzer = FilamentSpecificAnalyzer(
                region_name=region_name,
                skeleton_file=config['skeleton'],
                catalog_file=config['catalog'],
                distance_pc=config['distance'],
                width_pc=config['width']
            )

            success = analyzer.run_full_analysis()

            if success and analyzer.results:
                results_list.append(analyzer.results)

        except Exception as e:
            print(f"Failed to analyze {region_name}: {e}")
            continue

    return results_list


def generate_summary_report(results: List[Dict], output_dir: str):
    """Generate comprehensive summary report."""

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    if not results:
        print("\nNo results to report!")
        return

    print("\n" + "="*80)
    print("FINAL SUMMARY: ALL REGIONS")
    print("="*80)

    # Print table
    print(f"\n{'Region':<20} {'NN (pc)':<12} {'PM (pc)':<12} {'NN/PM':<10} {'NN λ/W':<10} {'PM λ/W':<10}")
    print("-"*80)

    for r in results:
        print(f"{r['region']:<20} {r['nn_median_pc']:<12.4f} {r['pm_median_pc']:<12.4f} "
             f"{r['nn_pm_ratio']:<10.3f} {r['nn_lambda_by_W']:<10.2f} {r['pm_lambda_by_W']:<10.2f}")

    # Compute averages
    avg_nn = np.mean([r['nn_median_pc'] for r in results])
    avg_pm = np.mean([r['pm_median_pc'] for r in results])
    avg_ratio = np.mean([r['nn_pm_ratio'] for r in results])
    avg_nn_lambda = np.mean([r['nn_lambda_by_W'] for r in results])
    avg_pm_lambda = np.mean([r['pm_lambda_by_W'] for r in results])

    print("-"*80)
    print(f"{'AVERAGE':<20} {avg_nn:<12.4f} {avg_pm:<12.4f} {avg_ratio:<10.3f} {avg_nn_lambda:<10.2f} {avg_pm_lambda:<10.2f}")
    print("="*80)

    # Compare with literature
    print("\nCOMPARISON WITH HGBS LITERATURE VALUES:")
    print("-"*80)

    literature_values = {
        'Taurus': {'nn': 0.062, 'pm': None, 'nn_pm_ratio': None},
        'Perseus': {'nn': 0.182, 'pm': None, 'nn_pm_ratio': None},
        'Aquila': {'nn': 0.161, 'pm': None, 'nn_pm_ratio': None},
    }

    for r in results:
        if r['region'] in literature_values:
            lit = literature_values[r['region']]
            print(f"\n{r['region']}:")
            print(f"  Literature NN: {lit['nn']:.3f} pc")
            print(f"  Measured NN: {r['nn_median_pc']:.3f} pc")
            if lit['nn'] > 0:
                ratio = r['nn_median_pc'] / lit['nn']
                print(f"  Ratio: {ratio:.2f}x")

    # Interpret results
    print("\n" + "="*80)
    print("INTERPRETATION")
    print("="*80)

    # Check NN/PM ratio
    if 0.31 <= avg_ratio <= 0.73:
        print(f"\n✓ Average NN/PM ratio ({avg_ratio:.3f}) is within HGBS range (0.31-0.73)")
        print("  → Results are consistent with HGBS measurements")
    else:
        print(f"\n✗ Average NN/PM ratio ({avg_ratio:.3f}) is outside HGBS range (0.31-0.73)")
        print("  → Possible differences in methodology or sample selection")

    # Check NN λ/W
    if avg_nn_lambda < 1.25:
        print(f"\n⚠ NN λ/W ({avg_nn_lambda:.2f}) is BELOW theoretical minimum (1.25)")
        print("  → Either: (a) Theoretical minimum needs revision")
        print("           (b) Width assumption (0.1 pc) is incorrect")
        print("           (c) Additional physics shortens wavelength")
    elif avg_nn_lambda > 4.0:
        print(f"\n⚠ NN λ/W ({avg_nn_lambda:.2f}) is ABOVE classical prediction (4.0)")
        print("  → Possible suppression of fragmentation")

    # Check PM λ/W
    if 2.5 <= avg_pm_lambda <= 3.5:
        print(f"\n✓ PM λ/W ({avg_pm_lambda:.2f}) is near HGBS reported value (2.79)")
        print("  → PM-based results appear consistent")
    else:
        print(f"\n✗ PM λ/W ({avg_pm_lambda:.2f}) differs from HGBS reported value (2.79)")

    # Save results
    output_file = output_path / 'filament_specific_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return results


def main():
    """Main execution."""

    # Run analysis
    results = analyze_all_regions()

    # Generate report
    output_dir = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/FILAMENT_SPECIFIC_ANALYSIS'
    generate_summary_report(results, output_dir)

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
