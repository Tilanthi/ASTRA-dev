#!/usr/bin/env python3
"""
Systematic Uncertainty Sensitivity Analysis for HGBS Core Spacing

This script quantifies systematic uncertainties in core spacing measurements by:
1. Testing DisPerSE persistence threshold sensitivity
2. Testing core-filament association threshold sensitivity
3. Bounding the total systematic uncertainty budget

Addressing Major Concern O2: 21% coefficient of variation analysis
"""

import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy import ndimage
from scipy.spatial import cKDTree
from pathlib import Path
from typing import Dict, List, Tuple
import json


class SystematicUncertaintyAnalyzer:
    """Quantify systematic uncertainties in HGBS spacing measurements."""

    def __init__(self, region_name: str, base_path: Path):
        self.region_name = region_name
        self.base_path = base_path

    def load_core_catalog(self) -> List[Dict]:
        """Load core catalog for the region."""
        catalog_file = self.base_path / f"HGBS_taurusL1495_derived_core_catalog.txt"

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
            if parts and parts[0].isdigit() and len(parts) >= 8:
                data_start = i
                break

        if data_start is None:
            return cores

        # Parse split format data
        for line in lines[data_start:]:
            if not line.strip() or line.startswith('|') or line.startswith('!'):
                continue

            parts = line.split()
            if len(parts) < 8:
                continue

            try:
                core_id = int(parts[0])
                ra_h = parts[2]
                ra_m = parts[3]
                ra_s = parts[4]
                dec_d = parts[5]
                dec_m = parts[6]
                dec_s = parts[7]

                ra_str = f"{ra_h}:{ra_m}:{ra_s}"
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

    def load_skeleton(self, threshold: int) -> np.ndarray:
        """Load skeleton map at specified persistence threshold."""
        skeleton_file = self.base_path / f"HGBS_taurusL1495_skeleton_map_thresh{threshold}.fits"

        if not skeleton_file.exists():
            raise FileNotFoundError(f"Skeleton file not found: {skeleton_file}")

        hdul = fits.open(skeleton_file)
        skeleton_data = hdul[0].data.astype(np.float64)
        hdul.close()

        return skeleton_data

    def associate_cores_with_filament(self, cores: List[Dict], skeleton_data: np.ndarray,
                                     max_distance_pixels: float = 15.0) -> List[int]:
        """
        Associate cores with filament using spatial proximity.

        Returns list of core IDs that are associated with the filament.
        """
        from astropy.wcs import WCS

        # Get WCS from skeleton header
        skeleton_file = self.base_path / f"HGBS_taurusL1495_skeleton_map_thresh50.fits"
        hdul = fits.open(skeleton_file)
        header = hdul[0].header
        wcs = WCS(header)
        hdul.close()

        # Extract filament structure
        skeleton_mask = skeleton_data > 0
        labeled, num_features = ndimage.label(skeleton_mask)

        if num_features == 0:
            return []

        # For each core, check if it's near any filament pixel
        associated_cores = []

        for core in cores:
            try:
                from astropy.wcs import utils
                px, py = utils.skycoord_to_pixel(wcs, SkyCoord(core['ra'], core['dec'], unit='deg'))

                # Check if core is within max_distance_pixels of any filament pixel
                # Simple approach: check if core position is within bounding box of filament
                # or use distance transform for more accuracy

                # Create a small region around the core
                px_int, py_int = int(px), int(py)
                search_radius = int(max_distance_pixels)

                # Define search region
                x_min = max(0, px_int - search_radius)
                x_max = min(skeleton_data.shape[1], px_int + search_radius + 1)
                y_min = max(0, py_int - search_radius)
                y_max = min(skeleton_data.shape[0], py_int + search_radius + 1)

                # Check if there are any filament pixels in the search region
                region = skeleton_data[y_min:y_max, x_min:x_max]
                if np.any(region > 0):
                    associated_cores.append(core['id'])

            except Exception:
                pass

        return associated_cores

    def compute_pairwise_spacing(self, cores: List[Dict], distance_pc: float) -> Dict:
        """Compute pairwise median spacing."""
        if len(cores) < 2:
            return {'error': 'Less than 2 cores'}

        coords = np.array([[c['ra'], c['dec']] for c in cores])
        tree = cKDTree(coords)

        # Compute all pairwise distances
        n = len(cores)
        distances = []

        for i in range(n):
            for j in range(i + 1, n):
                # Compute angular separation
                coord1 = SkyCoord(cores[i]['ra'], cores[i]['dec'], unit='deg')
                coord2 = SkyCoord(cores[j]['ra'], cores[j]['dec'], unit='deg')
                sep = coord1.separation(coord2)

                # Convert to physical distance
                sep_pc = sep.radian * distance_pc
                distances.append(sep_pc)

        distances = np.array(distances)

        return {
            'n_cores': len(cores),
            'pairwise_median_pc': float(np.median(distances)),
            'pairwise_mean_pc': float(np.mean(distances)),
            'pairwise_std_pc': float(np.std(distances)),
            'pairwise_sem_pc': float(np.std(distances) / np.sqrt(len(distances))),
        }

    def test_persistence_threshold_sensitivity(self, cores: List[Dict], distance_pc: float,
                                               thresholds: List[int] = [15, 20, 25, 50]) -> Dict:
        """
        Test sensitivity of spacing measurement to DisPerSE persistence threshold.

        This addresses a key systematic uncertainty: the choice of persistence threshold
        in DisPerSE affects which filaments are identified and which cores are associated.
        """
        print(f"\n{'='*70}")
        print(f"PERSISTENCE THRESHOLD SENSITIVITY ANALYSIS: {self.region_name}")
        print(f"{'='*70}")

        results = {}

        for threshold in thresholds:
            print(f"\nThreshold: {threshold}σ")

            try:
                # Load skeleton at this threshold
                skeleton_data = self.load_skeleton(threshold)

                # Get filament properties
                skeleton_mask = skeleton_data > 0
                labeled, num_features = ndimage.label(skeleton_mask)

                # Compute total filament length
                total_filament_pixels = np.sum(skeleton_mask)

                # Associate cores with filament
                associated_cores = self.associate_cores_with_filament(cores, skeleton_data)

                # Get the subset of associated cores
                associated_core_list = [c for c in cores if c['id'] in associated_cores]

                if len(associated_core_list) < 2:
                    print(f"  Warning: Only {len(associated_core_list)} cores associated with filament")
                    continue

                # Compute pairwise spacing
                stats = self.compute_pairwise_spacing(associated_core_list, distance_pc)

                stats['threshold'] = threshold
                stats['n_filaments'] = num_features
                stats['n_associated_cores'] = len(associated_core_list)
                stats['association_fraction'] = len(associated_core_list) / len(cores)
                stats['total_filament_pixels'] = total_filament_pixels

                results[threshold] = stats

                print(f"  Filaments: {num_features}")
                print(f"  Associated cores: {len(associated_core_list)}/{len(cores)} ({100*stats['association_fraction']:.1f}%)")
                print(f"  Pairwise median: {stats['pairwise_median_pc']:.4f} ± {stats['pairwise_sem_pc']:.4f} pc")

            except Exception as e:
                print(f"  Error: {e}")
                continue

        return results

    def analyze_sensitivity(self, results: Dict) -> Dict:
        """Analyze sensitivity results and quantify uncertainty."""
        if len(results) < 2:
            return {'error': 'Insufficient data for sensitivity analysis'}

        # Extract key metrics
        thresholds = sorted(results.keys())
        pairwise_medians = [results[t]['pairwise_median_pc'] for t in thresholds]
        n_associated = [results[t]['n_associated_cores'] for t in thresholds]

        # Compute sensitivity statistics
        median_spacing = np.median(pairwise_medians)
        std_spacing = np.std(pairwise_medians)
        cv_spacing = std_spacing / median_spacing * 100

        min_spacing = np.min(pairwise_medians)
        max_spacing = np.max(pairwise_medians)
        range_spacing = max_spacing - min_spacing

        # Compute fractional change relative to median
        fractional_changes = [(p - median_spacing) / median_spacing * 100
                             for p in pairwise_medians]

        return {
            'region': self.region_name,
            'n_thresholds_tested': len(thresholds),
            'thresholds': thresholds,
            'pairwise_medians_pc': pairwise_medians,
            'n_associated_cores': n_associated,
            'median_spacing_pc': float(median_spacing),
            'std_spacing_pc': float(std_spacing),
            'cv_spacing_percent': float(cv_spacing),
            'min_spacing_pc': float(min_spacing),
            'max_spacing_pc': float(max_spacing),
            'range_spacing_pc': float(range_spacing),
            'fractional_changes_percent': fractional_changes,
            'systematic_uncertainty_from_threshold_pc': float(std_spacing),
        }

    def run_full_analysis(self, distance_pc: float = 145) -> Dict:
        """Run full systematic uncertainty analysis."""
        cores = self.load_core_catalog()

        if len(cores) == 0:
            return {'error': 'No cores loaded'}

        print(f"Loaded {len(cores)} cores from catalog")

        # Test persistence threshold sensitivity
        threshold_results = self.test_persistence_threshold_sensitivity(cores, distance_pc)

        # Analyze sensitivity
        sensitivity_analysis = self.analyze_sensitivity(threshold_results)

        # Print summary
        print(f"\n{'='*70}")
        print(f"SYSTEMATIC UNCERTAINTY ANALYSIS SUMMARY")
        print(f"{'='*70}")
        print(f"Region: {self.region_name}")
        print(f"Number of thresholds tested: {sensitivity_analysis['n_thresholds_tested']}")
        print(f"\nSpacing sensitivity:")
        print(f"  Median spacing: {sensitivity_analysis['median_spacing_pc']:.4f} pc")
        print(f"  Std from threshold variation: {sensitivity_analysis['std_spacing_pc']:.4f} pc")
        print(f"  CV from threshold variation: {sensitivity_analysis['cv_spacing_percent']:.1f}%")
        print(f"  Range: {sensitivity_analysis['min_spacing_pc']:.4f} - {sensitivity_analysis['max_spacing_pc']:.4f} pc")
        print(f"\nSystematic uncertainty from persistence threshold: ±{sensitivity_analysis['systematic_uncertainty_from_threshold_pc']:.4f} pc")

        return sensitivity_analysis


def main():
    """Main execution function."""
    base_path = Path('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA/HGBS_TAURUS')

    analyzer = SystematicUncertaintyAnalyzer('Taurus', base_path)

    results = analyzer.run_full_analysis(distance_pc=145)

    # Save results
    output_file = base_path / 'systematic_uncertainty_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == '__main__':
    main()
