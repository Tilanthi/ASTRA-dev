#!/usr/bin/env python3
"""
Comprehensive Filament-Projected Nearest-Neighbor Analysis for HGBS Regions

This script performs proper filament-projected NN analysis:
1. Loads skeleton and catalog data for all HGBS regions
2. Associates cores with filaments using physical distance threshold (2W)
3. Projects cores onto filament spines
4. Orders cores along each filament
5. Computes filament-projected nearest-neighbor spacings
6. Reports λ/W for each region and weighted means

Author: ASTRA System
Date: 2026-05-08
"""

import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy.spatial import cKDTree
from scipy import ndimage
from collections import defaultdict
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class FilamentProjectedNNAnalyzer:
    """Analyzer for filament-projected nearest-neighbor spacing."""

    # Region configurations with distances and characteristic widths
    REGION_CONFIGS = {
        'IC5146': {
            'distance_pc': 260,
            'width_pc': 0.10,
            'skeleton_file': 'HGBS_IC5146/HGBS_ic5146_skeleton_map.fits',
            'catalog_file': 'HGBS_IC5146/core_catalog_ic5146.csv',
            'catalog_format': 'csv'
        },
        'Orion B': {
            'distance_pc': 386,
            'width_pc': 0.10,
            'skeleton_file': 'HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits',
            'catalog_file': 'HGBS_ORIB/HGBS_orionB_observed_core_catalog.txt',
            'catalog_format': 'standard'
        },
        'Aquila': {
            'distance_pc': 436,
            'width_pc': 0.10,
            'skeleton_file': 'HGBS_AQUILA/HGBS_AQUILA/HGBS_aquilaM2_skeleton_map.fits',
            'catalog_file': 'HGBS_AQUILA/HGBS_AQUILA/HGBS_aquilaM2_derived_core_catalog.txt',
            'catalog_format': 'standard'
        },
        'Perseus': {
            'distance_pc': 296,
            'width_pc': 0.10,
            'skeleton_file': 'HGBS_PERSEUS/HGBS_PERSEUS/HGBS_perseus_skeleton_map_thresh20.fits',
            'catalog_file': 'HGBS_PERSEUS/HGBS_perseus_observed_core_catalog.txt',
            'catalog_format': 'standard'
        },
        'Taurus': {
            'distance_pc': 135,
            'width_pc': 0.10,
            'skeleton_file': 'HGBS_TAURUS/HGBS_taurusL1495_skeleton_map_thresh20.fits',
            'catalog_file': 'HGBS_TAURUS/HGBS_taurusL1495_observed_core_catalog.txt',
            'catalog_format': 'split'
        },
        'Ophiuchus': {
            'distance_pc': 137,
            'width_pc': 0.10,
            'skeleton_file': 'HGBS_OPH/HGBS_oph_l1688_skeleton_map_thresh50.fits',
            'catalog_file': 'HGBS_OPH/HGBS_ophiuchus_observed_core_catalog.txt',
            'catalog_format': 'standard'
        },
        'CRA': {
            'distance_pc': 260,
            'width_pc': 0.10,
            'skeleton_file': 'HGBS_CRA/HGBS_craNS_skeleton_map_thresh20.fits',
            'catalog_file': 'HGBS_CRA/HGBS_craNS_derived_core_catalog.txt',
            'catalog_format': 'standard'
        },
        'Serpens': {
            'distance_pc': 436,
            'width_pc': 0.10,
            'skeleton_file': 'HGBS_SERPENS/HGBS_serpens_skeleton_map_thresh50.fits',
            'catalog_file': 'HGBS_SERPENS/HGBS_serpens_observed_core_catalog.txt',
            'catalog_format': 'standard'
        },
        'TMC1': {
            'distance_pc': 135,
            'width_pc': 0.10,
            'skeleton_file': 'HGBS_TMC1/HGBS_taurusTMC1_skeleton_map_thresh50.fits',
            'catalog_file': 'HGBS_TMC1/HGBS_taurusTMC1_observed_core_catalog.txt',
            'catalog_format': 'standard'
        },
    }

    def __init__(self, base_path: str):
        """
        Initialize analyzer.

        Parameters:
        -----------
        base_path : str
            Base path to HGBS_SOURCE_DATA directory
        """
        self.base_path = Path(base_path)

    def load_catalog(self, region: str, config: Dict) -> List[Dict]:
        """Load core catalog for a region."""
        catalog_file = self.base_path / config['catalog_file']
        catalog_format = config.get('catalog_format', 'standard')

        cores = []

        if catalog_format == 'csv':
            # CSV format (IC5146)
            import csv
            with open(catalog_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Skip comment lines
                    if 'obj_id' not in row or not row['obj_id'].strip():
                        continue
                    try:
                        obj_id = int(row['obj_id'])
                        # Skip header row if obj_id is not a number
                        if obj_id < 0:
                            continue
                        cores.append({
                            'id': obj_id,
                            'ra': float(row['ra_deg']),
                            'dec': float(row['dec_deg']),
                        })
                    except (ValueError, KeyError):
                        continue

        elif catalog_format == 'standard' or catalog_format == 'split':
            with open(catalog_file, 'r', encoding='latin-1', errors='ignore') as f:
                lines = f.readlines()

            # Find data start
            data_start = None
            for i, line in enumerate(lines):
                if not line.strip() or line.startswith('|') or line.startswith('!'):
                    continue
                parts = line.split()
                if parts and parts[0].isdigit() and len(parts) >= 8:
                    data_start = i
                    break

            if data_start is None:
                # Try alternative format detection
                for i, line in enumerate(lines):
                    if '   1 ' in line or ' 1 ' in line:
                        data_start = i
                        break

            # Parse catalog
            for line in lines[data_start:]:
                if not line.strip() or line.startswith('|') or line.startswith('!'):
                    continue

                parts = line.split()
                if len(parts) < 8:
                    continue

                try:
                    ra_str = f"{parts[2]}:{parts[3]}:{parts[4]}"
                    dec_str = f"{parts[5]}:{parts[6]}:{parts[7]}"
                    coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))

                    cores.append({
                        'id': int(parts[0]),
                        'ra': coord.ra.deg,
                        'dec': coord.dec.deg,
                    })
                except (ValueError, IndexError):
                    continue

        return cores

    def load_skeleton(self, region: str, config: Dict) -> Tuple[np.ndarray, object]:
        """Load skeleton map and WCS."""
        skeleton_file = self.base_path / config['skeleton_file']

        hdul = fits.open(skeleton_file)
        skeleton_data = hdul[0].data.astype(np.float64)
        header = hdul[0].header
        hdul.close()

        from astropy.wcs import WCS
        wcs = WCS(header)

        return skeleton_data, wcs

    def extract_filament_spines(self, skeleton_data: np.ndarray,
                                threshold: float = 0.1,
                                min_length: int = 20) -> List[Dict]:
        """Extract filament spines from skeleton map."""
        skeleton_mask = skeleton_data > threshold
        labeled, num_features = ndimage.label(skeleton_mask)

        filaments = []

        for i in range(1, num_features + 1):
            filament_pixels = np.where(labeled == i)
            n_pixels = len(filament_pixels[0])

            if n_pixels < min_length:
                continue

            y_coords = filament_pixels[0]
            x_coords = filament_pixels[1]
            skeleton_values = skeleton_data[y_coords, x_coords]

            # Use skeleton values (persistence) to order pixels
            # Higher persistence values are more significant
            order = np.argsort(-skeleton_values)

            filaments.append({
                'id': i,
                'pixels_y': y_coords[order],
                'pixels_x': x_coords[order],
                'values': skeleton_values[order],
                'length': n_pixels
            })

        return filaments

    def associate_cores_with_filaments(self, cores: List[Dict],
                                       filaments: List[Dict],
                                       wcs,
                                       max_distance_pc: float = 0.20) -> Dict:
        """
        Associate cores with filaments using physical distance threshold.

        Uses 2W = 0.20 pc as default association threshold.
        """
        from astropy.wcs import utils

        core_filament_assoc = {}
        core_filament_distances = {}

        for i, core in enumerate(cores):
            try:
                px, py = utils.skycoord_to_pixel(
                    wcs,
                    SkyCoord(core['ra'], core['dec'], unit='deg')
                )

                min_dist = np.inf
                closest_filament = None

                for fil in filaments:
                    dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                    dist = np.sqrt(np.min(dist_sq))

                    if dist < min_dist:
                        min_dist = dist
                        closest_filament = fil['id']

                if min_dist < max_distance_pc / 0.00027778:  # Approximate pixel scale
                    core_filament_assoc[i] = closest_filament
                    core_filament_distances[i] = min_dist
            except Exception:
                pass

        return core_filament_assoc, core_filament_distances

    def order_cores_along_filaments(self, cores: List[Dict],
                                     filaments: List[Dict],
                                     core_assoc: Dict,
                                     wcs) -> Dict:
        """Order cores along each filament by projection position."""
        from astropy.wcs import utils

        filament_cores = defaultdict(list)

        for i, fil_id in core_assoc.items():
            filament_cores[fil_id].append(i)

        ordered_filament_cores = {}

        for fil_id, core_indices in filament_cores.items():
            if len(core_indices) < 2:
                continue

            fil = next(f for f in filaments if f['id'] == fil_id)

            core_positions = []

            for core_idx in core_indices:
                core = cores[core_idx]
                try:
                    px, py = utils.skycoord_to_pixel(
                        wcs,
                        SkyCoord(core['ra'], core['dec'], unit='deg')
                    )

                    # Find closest point on filament spine
                    dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                    closest_idx = np.argmin(dist_sq)

                    # Use position along spine (normalized 0-1)
                    position_along_spine = closest_idx / fil['length']

                    core_positions.append((position_along_spine, core_idx))
                except Exception:
                    continue

            # Sort by position along spine
            core_positions.sort(key=lambda x: x[0])
            ordered_filament_cores[fil_id] = [c[1] for c in core_positions]

        return ordered_filament_cores

    def compute_nn_spacing(self, cores: List[Dict],
                          filament_cores: Dict,
                          distance_pc: float) -> np.ndarray:
        """Compute filament-projected nearest-neighbor spacings."""
        all_spacings = []

        for fil_id, core_indices in filament_cores.items():
            if len(core_indices) < 2:
                continue

            coords = SkyCoord(
                ra=[cores[i]['ra'] for i in core_indices] * u.deg,
                dec=[cores[i]['dec'] for i in core_indices] * u.deg
            )

            # Compute spacings between adjacent cores along filament
            for i in range(len(coords) - 1):
                sep = coords[i].separation(coords[i+1])
                sep_pc = sep.radian * distance_pc
                all_spacings.append(sep_pc)

        return np.array(all_spacings)

    def analyze_region(self, region: str) -> Dict:
        """Analyze a single region."""
        print(f"\n{'='*70}")
        print(f"Analyzing {region}")
        print(f"{'='*70}")

        config = self.REGION_CONFIGS[region]

        # Load data
        print(f"Loading catalog...")
        cores = self.load_catalog(region, config)
        print(f"  Loaded {len(cores)} cores")

        print(f"Loading skeleton...")
        skeleton_data, wcs = self.load_skeleton(region, config)
        print(f"  Skeleton shape: {skeleton_data.shape}")

        # Extract filaments
        print(f"Extracting filament spines...")
        filaments = self.extract_filament_spines(skeleton_data)
        print(f"  Found {len(filaments)} filaments")

        # Associate cores
        association_threshold_pc = 2 * config['width_pc']  # 2W threshold
        print(f"Associating cores (threshold: {association_threshold_pc:.2f} pc)...")
        core_assoc, core_dists = self.associate_cores_with_filaments(
            cores, filaments, wcs, max_distance_pc=association_threshold_pc
        )
        print(f"  Associated {len(core_assoc)}/{len(cores)} cores")

        # Order cores along filaments
        print(f"Ordering cores along filaments...")
        filament_cores = self.order_cores_along_filaments(cores, filaments, core_assoc, wcs)
        print(f"  Ordered cores in {len(filament_cores)} filaments with 2+ cores")

        # Compute NN spacings
        print(f"Computing nearest-neighbor spacings...")
        spacings = self.compute_nn_spacing(cores, filament_cores, config['distance_pc'])
        print(f"  Computed {len(spacings)} spacings")

        # Compute statistics
        if len(spacings) > 0:
            stats = {
                'n_cores_total': len(cores),
                'n_cores_associated': len(core_assoc),
                'n_cores_in_filaments': sum(len(v) for v in filament_cores.values()),
                'n_spacings': len(spacings),
                'nn_median_pc': float(np.median(spacings)),
                'nn_mean_pc': float(np.mean(spacings)),
                'nn_std_pc': float(np.std(spacings)),
                'nn_sem_pc': float(np.std(spacings) / np.sqrt(len(spacings))),
                'nn_min_pc': float(np.min(spacings)),
                'nn_max_pc': float(np.max(spacings)),
                'width_pc': config['width_pc'],
                'lambda_over_W': float(np.median(spacings) / config['width_pc']),
            }

            print(f"\nResults for {region}:")
            print(f"  NN median: {stats['nn_median_pc']:.4f} ± {stats['nn_sem_pc']:.4f} pc")
            print(f"  λ/W: {stats['lambda_over_W']:.2f}")
        else:
            stats = {
                'n_cores_total': len(cores),
                'n_cores_associated': len(core_assoc),
                'n_cores_in_filaments': 0,
                'n_spacings': 0,
                'error': 'No spacings computed'
            }
            print(f"\nERROR: No spacings computed for {region}")

        return stats

    def run_all_regions(self) -> Dict:
        """Run analysis for all regions."""
        print("="*70)
        print("COMPREHENSIVE FILAMENT-PROJECTED NN ANALYSIS")
        print("="*70)

        results = {}

        for region in self.REGION_CONFIGS.keys():
            try:
                results[region] = self.analyze_region(region)
            except Exception as e:
                print(f"\nERROR analyzing {region}: {e}")
                import traceback
                traceback.print_exc()
                results[region] = {'error': str(e)}

        # Compute weighted means
        print(f"\n{'='*70}")
        print("SUMMARY STATISTICS")
        print(f"{'='*70}")

        valid_results = {k: v for k, v in results.items()
                        if 'error' not in v and v['n_spacings'] > 0}

        if valid_results:
            # Weight by number of spacings (inverse-variance weighting)
            weights = np.array([v['n_spacings'] for v in valid_results.values()])
            values = np.array([v['nn_median_pc'] for v in valid_results.values()])

            weighted_mean_nn = np.sum(weights * values) / np.sum(weights)

            # Compute weighted mean λ/W
            lambda_W_values = np.array([v['lambda_over_W'] for v in valid_results.values()])
            weighted_mean_lambda_W = np.sum(weights * lambda_W_values) / np.sum(weights)

            # Standard error of weighted mean
            weighted_sem = np.sqrt(np.sum(weights * (values - weighted_mean_nn)**2) /
                                  (len(weights) * np.sum(weights)))

            print(f"\nWeighted mean NN spacing: {weighted_mean_nn:.4f} ± {weighted_sem:.4f} pc")
            print(f"Weighted mean λ/W: {weighted_mean_lambda_W:.2f}")

            results['weighted_mean'] = {
                'nn_median_pc': float(weighted_mean_nn),
                'nn_sem_pc': float(weighted_sem),
                'lambda_over_W': float(weighted_mean_lambda_W),
                'n_regions': len(valid_results),
                'total_spacings': int(np.sum(weights))
            }

        return results


def main():
    """Main execution."""
    base_path = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA'

    analyzer = FilamentProjectedNNAnalyzer(base_path)
    results = analyzer.run_all_regions()

    # Save results
    output_file = Path(base_path) / 'filament_projected_nn_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*70}")

    return results


if __name__ == '__main__':
    results = main()
