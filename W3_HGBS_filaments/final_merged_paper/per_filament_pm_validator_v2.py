#!/usr/bin/env python3
"""
Per-Filament PM Validation: Test if PM_filament ≈ L_filament/3 for HGBS filaments

This script validates the L/3 convergence relationship on individual HGBS filaments
by computing PM and NN statistics for each filament separately.

Author: ASTRA Agent System
Date: 2026-05-03
"""

import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy import ndimage
from scipy.spatial import cKDTree
import json
from pathlib import Path


class PerFilamentPMValidator:
    """Validate PM ≈ L/3 relationship on individual HGBS filaments."""

    def __init__(self, skeleton_file, catalog_file, distance_pc):
        """
        Initialize validator with HGBS skeleton and catalog data.

        Parameters
        ----------
        skeleton_file : str
            Path to DisPerSE skeleton FITS file
        catalog_file : str
            Path to HGBS core catalog
        distance_pc : float
            Distance to region in parsecs (for converting angular to physical distances)
        """
        self.skeleton_file = skeleton_file
        self.catalog_file = catalog_file
        self.distance_pc = distance_pc
        self.arcsec_to_pc = distance_pc / 206265.0

        # Load data
        self.skeleton_data = None
        self.skeleton_header = None
        self.cores = []
        self.filaments = []
        self.wcs = None
        self.has_wcs = False

        self.load_skeleton()
        self.load_catalog()

    def load_skeleton(self):
        """Load the DisPerSE skeleton map."""
        print(f"Loading skeleton: {self.skeleton_file}")
        hdul = fits.open(self.skeleton_file)
        self.skeleton_data = hdul[0].data.astype(np.float64)
        self.skeleton_header = hdul[0].header

        print(f"Skeleton shape: {self.skeleton_data.shape}")

        # Check if WCS is available and valid
        try:
            from astropy.wcs import WCS
            self.wcs = WCS(self.skeleton_header)
            # Check if WCS has valid coordinate system
            if self.wcs.wcs.ctype[0] and 'RA' in self.wcs.wcs.ctype[0].upper():
                self.has_wcs = True
                print(f"WCS available: {self.wcs.wcs.ctype}")
            else:
                self.has_wcs = False
                print("No valid WCS in skeleton header - will use pixel coordinates")
        except Exception as e:
            print(f"No WCS in header: {e}")
            self.has_wcs = False

        hdul.close()

    def load_catalog(self):
        """Load the HGBS core catalog."""
        print(f"Loading catalog: {self.catalog_file}")

        # Handle encoding - HGBS catalogs have special characters
        with open(self.catalog_file, 'r', encoding='latin-1', errors='replace') as f:
            lines = f.readlines()

        # Skip header until we find data lines (start with number as first column)
        data_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Data lines start with a number (core ID)
            if stripped and stripped[0].isdigit():
                data_start = i
                break

        print(f"Found data starting at line {data_start}")

        # Parse core data
        for line in lines[data_start:]:
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) < 4:
                continue

            try:
                # First column should be a number (core ID)
                core_id = parts[0]
                if not core_id.isdigit():
                    continue

                # RA/Dec are columns 3 and 4 (0-indexed: 2 and 3)
                ra_str = parts[2]
                dec_str = parts[3]

                # Parse coordinates
                coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))

                self.cores.append({
                    'id': int(core_id),
                    'ra': coord.ra.deg,
                    'dec': coord.dec.deg,
                    'coord': coord
                })
            except (ValueError, IndexError) as e:
                continue

        print(f"Loaded {len(self.cores)} cores from catalog")

        # Convert cores to pixel coordinates if WCS is available
        if self.has_wcs:
            print("Converting core coordinates to pixel space...")
            for core in self.cores:
                # Convert SkyCoord to pixel coordinates
                # world_to_pixel requires separate ra and dec arrays
                ra_array = np.array([core['ra']])
                dec_array = np.array([core['dec']])
                x_pixel, y_pixel = self.wcs.world_to_pixel_values(ra_array, dec_array)
                core['x_pixel'] = x_pixel[0]
                core['y_pixel'] = y_pixel[0]

    def extract_filament_spines(self, threshold=0.1, min_length=10, max_filaments=500):
        """
        Extract filament spines from the skeleton map.

        Parameters
        ----------
        threshold : float
            Minimum skeleton value to consider
        min_length : int
            Minimum number of pixels for a filament
        max_filaments : int
            Maximum number of filaments to extract (for performance)
        """
        print("Extracting filament spines from skeleton map...", flush=True)

        # Threshold the skeleton
        skeleton_mask = self.skeleton_data > threshold

        # Label connected components
        labeled, num_features = ndimage.label(skeleton_mask)

        print(f"Found {num_features} candidate filaments", flush=True)

        # Extract each filament as an ordered set of pixels
        filaments = []

        for i in range(1, min(num_features + 1, max_filaments + 1)):
            if i % 100 == 0:
                print(f"  Processing filament {i}/{min(num_features, max_filaments)}...", flush=True)

            filament_pixels = np.where(labeled == i)
            n_pixels = len(filament_pixels[0])

            if n_pixels < min_length:
                continue

            # Get the pixel coordinates
            y_coords = filament_pixels[0]
            x_coords = filament_pixels[1]

            # Order the pixels along the filament
            skeleton_values = self.skeleton_data[y_coords, x_coords]

            # Sort by position and use skeleton values as weights
            order = np.lexsort((x_coords, y_coords))
            ordered_y = y_coords[order]
            ordered_x = x_coords[order]
            ordered_values = skeleton_values[order]

            filaments.append({
                'id': i,
                'pixels_y': ordered_y,
                'pixels_x': ordered_x,
                'values': ordered_values,
                'length_pixels': n_pixels
            })

        # Sort filaments by length (descending)
        filaments.sort(key=lambda f: f['length_pixels'], reverse=True)

        self.filaments = filaments
        print(f"Extracted {len(filaments)} filaments with >= {min_length} pixels (max {max_filaments})", flush=True)

        return filaments

    def associate_cores_with_filaments(self, max_distance_pixels=30):
        """
        Associate cores with nearby filaments using pixel coordinates.

        Parameters
        ----------
        max_distance_pixels : float
            Maximum distance for core-filament association in pixels
        """
        print(f"Associating cores with filaments (max distance: {max_distance_pixels} pixels)...", flush=True)

        filament_core_map = {}

        if self.has_wcs:
            # Use pixel coordinates for both cores and filaments
            # Build cKDTree for each filament for faster nearest-neighbor search
            print("  Building spatial indexes for filaments...", flush=True)
            filament_trees = {}
            for filament in self.filaments:
                # Build tree from filament pixel coordinates
                points = np.column_stack((filament['pixels_x'], filament['pixels_y']))
                tree = cKDTree(points)
                filament_trees[filament['id']] = tree

            print(f"  Associating {len(self.cores)} cores with {len(self.filaments)} filaments...", flush=True)
            for i, core in enumerate(self.cores):
                if i % 50 == 0:
                    print(f"    Processed {i}/{len(self.cores)} cores...", flush=True)

                core_x = core['x_pixel']
                core_y = core['y_pixel']

                # Find nearest point on each filament spine using cKDTree
                for filament in self.filaments:
                    tree = filament_trees[filament['id']]
                    dist, idx = tree.query([[core_x, core_y]])  # Query returns array for [[x,y]] format
                    min_distance = dist[0]

                    if min_distance < max_distance_pixels:
                        if filament['id'] not in filament_core_map:
                            filament_core_map[filament['id']] = []
                        filament_core_map[filament['id']].append({
                            'core_id': core['id'],
                            'x': core_x,
                            'y': core_y,
                            'ra': core['ra'],
                            'dec': core['dec'],
                            'distance_pixels': min_distance,
                            'distance_pc': min_distance * self.arcsec_to_pc * 3600  # Convert pixels to pc
                        })

            print(f"    Processed all {len(self.cores)} cores", flush=True)
        else:
            print("WARNING: No WCS available - cannot reliably associate cores with filaments")
            print("         Using pixel-based association (may be inaccurate)")
            # Use rough pixel matching
            for core in self.cores:
                # For cores without WCS, try to find nearby filaments
                # This is a rough approximation
                for filament in self.filaments:
                    # Use bounding box check first
                    if (filament['pixels_x'].min() - max_distance_pixels <= core['ra'] <=
                        filament['pixels_x'].max() + max_distance_pixels and
                        filament['pixels_y'].min() - max_distance_pixels <= core['dec'] <=
                        filament['pixels_y'].max() + max_distance_pixels):

                        # More precise distance check
                        dx = filament['pixels_x'] - core['ra']
                        dy = filament['pixels_y'] - core['dec']
                        distances = np.sqrt(dx**2 + dy**2)
                        min_distance = distances.min()

                        if min_distance < max_distance_pixels:
                            if filament['id'] not in filament_core_map:
                                filament_core_map[filament['id']] = []
                            filament_core_map[filament['id']].append({
                                'core_id': core['id'],
                                'ra': core['ra'],
                                'dec': core['dec'],
                                'distance_pixels': min_distance
                            })

        # Report association statistics
        n_associated = sum(len(cores) for cores in filament_core_map.values())
        print(f"Associated {n_associated} core-filament pairs across {len(filament_core_map)} filaments")

        return filament_core_map

    def compute_per_filament_statistics(self, min_cores=2, max_distance_pixels=150):
        """
        Compute PM and NN statistics for each individual filament.

        Parameters
        ----------
        min_cores : int
            Minimum number of cores required for PM calculation
        max_distance_pixels : float
            Maximum distance for core-filament association in pixels

        Returns
        -------
        results : list
            List of per-filament statistics
        """
        print(f"\nComputing per-filament statistics (min {min_cores} cores, max distance {max_distance_pixels} pixels)...")

        # Associate cores with filaments
        filament_core_map = self.associate_cores_with_filaments(max_distance_pixels=max_distance_pixels)

        results = []

        for filament in self.filaments:
            filament_id = filament['id']
            associated_cores = filament_core_map.get(filament_id, [])

            n_cores = len(associated_cores)

            if n_cores < min_cores:
                continue  # Skip filaments with insufficient cores

            print(f"  Filament {filament_id}: {n_cores} cores")

            # Sort cores by position along filament (simplified: use x coordinate)
            core_positions = sorted(associated_cores, key=lambda c: c['ra'])

            # Compute NN (nearest-neighbor) distances
            nn_distances = []
            for i in range(len(core_positions) - 1):
                coord1 = SkyCoord(core_positions[i]['ra']*u.deg,
                                core_positions[i]['dec']*u.deg)
                coord2 = SkyCoord(core_positions[i+1]['ra']*u.deg,
                                core_positions[i+1]['dec']*u.deg)
                separation = coord1.separation(coord2)
                nn_distances.append(separation.arcsec * self.arcsec_to_pc)

            # Compute PM (pairwise median) for this filament
            pm_distances = []
            for i in range(len(core_positions)):
                for j in range(i+1, len(core_positions)):
                    coord1 = SkyCoord(core_positions[i]['ra']*u.deg,
                                    core_positions[i]['dec']*u.deg)
                    coord2 = SkyCoord(core_positions[j]['ra']*u.deg,
                                    core_positions[j]['dec']*u.deg)
                    separation = coord1.separation(coord2)
                    pm_distances.append(separation.arcsec * self.arcsec_to_pc)

            if len(nn_distances) == 0 or len(pm_distances) == 0:
                continue

            # Compute statistics
            nn_median = np.median(nn_distances)
            pm_median = np.median(pm_distances)

            # Estimate filament length
            # For a simple approximation, use the span of core positions plus end corrections
            if len(core_positions) >= 2:
                first_coord = SkyCoord(core_positions[0]['ra']*u.deg,
                                        core_positions[0]['dec']*u.deg)
                last_coord = SkyCoord(core_positions[-1]['ra']*u.deg,
                                        core_positions[-1]['dec']*u.deg)
                span_separation = first_coord.separation(last_coord)
                length_pc = span_separation.arcsec * self.arcsec_to_pc

                # Add end corrections (assuming cores are spaced at ~nn_median)
                estimated_length = length_pc + nn_median  # Add one NN spacing at each end
            else:
                estimated_length = None

            # Compute L/3 for this filament
            if estimated_length is not None:
                L_over_3 = estimated_length / 3.0
            else:
                L_over_3 = None

            # Compute ratios
            if L_over_3 is not None and L_over_3 > 0:
                pm_ratio = pm_median / L_over_3
            else:
                pm_ratio = None

            results.append({
                'filament_id': filament_id,
                'n_cores': n_cores,
                'length_pc': estimated_length,
                'L_over_3_pc': L_over_3,
                'pm_median_pc': pm_median,
                'nn_median_pc': nn_median,
                'pm_ratio': pm_ratio,
                'pm_nn_ratio': pm_median / nn_median if nn_median > 0 else None
            })

        print(f"Computed statistics for {len(results)} filaments with >= {min_cores} cores")

        return results

    def analyze_results(self, results, output_file):
        """Analyze and save results."""
        print("\n" + "="*70)
        print("PER-FILAMENT PM VALIDATION RESULTS")
        print("="*70)

        if len(results) == 0:
            print("No filaments with sufficient cores found!")
            return None

        # Filter valid ratios
        valid_results = [r for r in results if r['pm_ratio'] is not None]

        if len(valid_results) == 0:
            print("No valid PM ratios computed!")
            return None

        # Statistics
        pm_ratios = [r['pm_ratio'] for r in valid_results]
        pm_nn_ratios = [r['pm_nn_ratio'] for r in valid_results if r['pm_nn_ratio'] is not None]

        print(f"\nAnalyzed {len(valid_results)} filaments:")
        print(f"  PM/(L/3) ratios: mean = {np.mean(pm_ratios):.3f}, std = {np.std(pm_ratios):.3f}")
        print(f"  PM/NN ratios: mean = {np.mean(pm_nn_ratios):.3f}, std = {np.std(pm_nn_ratios):.3f}")

        # Test if PM ≈ L/3 (ratio close to 1)
        mean_ratio = np.mean(pm_ratios)
        std_ratio = np.std(pm_ratios)
        n_filaments = len(valid_results)

        # Standard error of the mean
        sem_ratio = std_ratio / np.sqrt(n_filaments)

        print(f"\n  PM/(L/3) = {mean_ratio:.3f} ± {sem_ratio:.3f} (mean ± SEM)")

        # Statistical test: is mean_ratio consistent with 1.0?
        from scipy import stats
        t_statistic = (mean_ratio - 1.0) / sem_ratio
        p_value_two_sided = 2 * (1 - stats.t.cdf(abs(t_statistic), df=n_filaments-1))

        print(f"\n  Statistical test (H0: PM/(L/3) = 1.0):")
        print(f"    t-statistic: {t_statistic:.3f}")
        print(f"    p-value: {p_value_two_sided:.4f}")

        if p_value_two_sided < 0.05:
            print(f"    ✗ Mean ratio differs significantly from 1.0 (p < 0.05)")
        elif p_value_two_sided < 0.10:
            print(f"    ~ Mean ratio shows marginal deviation from 1.0 (0.05 < p < 0.10)")
        else:
            print(f"    ✓ Mean ratio consistent with 1.0 (p >= 0.10)")

        # Classification
        if abs(mean_ratio - 1.0) < 0.1:
            interpretation = "✓ Strong support: PM ≈ L/3 for individual HGBS filaments"
        elif abs(mean_ratio - 1.0) < 0.2:
            interpretation = "~ Moderate support: PM roughly equals L/3 with some scatter"
        else:
            interpretation = "✗ No support: PM does not equal L/3 for HGBS filaments"

        print(f"\n  {interpretation}")

        # Distribution analysis
        print(f"\n  Distribution of PM/(L/3) ratios:")
        print(f"    25th percentile: {np.percentile(pm_ratios, 25):.3f}")
        print(f"    Median: {np.median(pm_ratios):.3f}")
        print(f"    75th percentile: {np.percentile(pm_ratios, 75):.3f}")

        # Count how many filaments have PM ≈ L/3 (within 20%)
        close_to_1 = sum(1 for r in pm_ratios if 0.8 <= r <= 1.2)
        percentage = 100 * close_to_1 / len(pm_ratios)
        print(f"    Filaments with 0.8 ≤ PM/(L/3) ≤ 1.2: {close_to_1}/{len(pm_ratios)} ({percentage:.1f}%)")

        # Save results
        output_data = {
            'region': Path(self.skeleton_file).parent.name,
            'distance_pc': self.distance_pc,
            'has_wcs': self.has_wcs,
            'n_filaments_analyzed': len(results),
            'n_filaments_valid': len(valid_results),
            'pm_ratio_mean': float(mean_ratio),
            'pm_ratio_std': float(std_ratio),
            'pm_ratio_sem': float(sem_ratio),
            'pm_ratio_median': float(np.median(pm_ratios)),
            'pm_ratio_p25': float(np.percentile(pm_ratios, 25)),
            'pm_ratio_p75': float(np.percentile(pm_ratios, 75)),
            'pm_nn_ratio_mean': float(np.mean(pm_nn_ratios)) if pm_nn_ratios else None,
            'interpretation': interpretation,
            'individual_filaments': results
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\nResults saved to {output_file}")

        return output_data


def analyze_region(region_name, skeleton_file, catalog_file, distance_pc, max_filaments=500, min_length=10):
    """Analyze a single HGBS region."""
    print("\n" + "="*70, flush=True)
    print(f"ANALYZING REGION: {region_name}", flush=True)
    print("="*70, flush=True)
    print(f"Distance: {distance_pc} pc", flush=True)
    print(f"Skeleton: {skeleton_file}", flush=True)
    print(f"Catalog: {catalog_file}", flush=True)

    validator = PerFilamentPMValidator(skeleton_file, catalog_file, distance_pc)

    # Extract filaments (with limit for performance)
    filaments = validator.extract_filament_spines(threshold=0.1, min_length=min_length, max_filaments=max_filaments)

    if len(filaments) == 0:
        print("No filaments found!", flush=True)
        return None

    # Compute statistics (lower min_cores for testing)
    results = validator.compute_per_filament_statistics(min_cores=2)

    if len(results) == 0:
        print("No filaments with sufficient cores!", flush=True)
        return None

    # Analyze and save results
    output_file = f"per_filament_pm_validation_{region_name}.json"
    data = validator.analyze_results(results, output_file)

    return data


def main():
    """Run per-filament PM validation for all HGBS regions."""

    # HGBS regions with their distances (in pc) and file paths
    regions = {
        'OrionB': {
            'distance': 386,
            'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB',
            'skeleton': 'HGBS_orionB_skeleton_map.fits',  # Official HGBS file with WCS
            'catalog': 'HGBS_orionB_observed_core_catalog.txt'
        },
        'Perseus': {
            'distance': 296,
            'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS/HGBS_PERSEUS',
            'skeleton': '../HGBS_perseus_skeleton_map.fits',
            'catalog': 'HGBS_perseus_observed_core_catalog.txt'
        },
        'TaurusL1495': {
            'distance': 135,
            'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS',
            'skeleton': 'HGBS_taurusL1495_skeleton_map.fits',
            'catalog': 'HGBS_taurusL1495_observed_core_catalog.txt'
        },
        'Ophiuchus': {
            'distance': 137,
            'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH',
            'skeleton': 'HGBS_oph_l1688_skeleton_map.fits',
            'catalog': 'HGBS_ophiuchus_observed_core_catalog.txt'
        },
    }

    all_results = {}

    for region_name, region_info in regions.items():
        skeleton_file = f"{region_info['path']}/{region_info['skeleton']}"
        catalog_file = f"{region_info['path']}/{region_info['catalog']}"

        # Check if files exist
        import os
        if not os.path.exists(skeleton_file):
            print(f"\nSkipping {region_name}: skeleton file not found ({skeleton_file})")
            continue

        if not os.path.exists(catalog_file):
            print(f"\nSkipping {region_name}: catalog file not found ({catalog_file})")
            continue

        try:
            # Use appropriate max_filaments for each region based on expected complexity
            if region_name == 'TaurusL1495':
                max_filaments = 1000  # Taurus has many small filaments
                min_length = 5  # Lower threshold for Taurus
            elif region_name == 'Perseus':
                max_filaments = 500
                min_length = 10
            elif region_name == 'OrionB':
                max_filaments = 500
                min_length = 10
            elif region_name == 'Ophiuchus':
                max_filaments = 500
                min_length = 10
            else:
                max_filaments = 500
                min_length = 10

            data = analyze_region(region_name, skeleton_file, catalog_file, region_info['distance'], max_filaments=max_filaments, min_length=min_length)
            if data:
                all_results[region_name] = data
        except Exception as e:
            print(f"\nError analyzing {region_name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary across all regions
    print("\n" + "="*70)
    print("SUMMARY ACROSS ALL REGIONS")
    print("="*70)

    if all_results:
        print(f"\nAnalyzed {len(all_results)} regions successfully")

        for region_name, data in all_results.items():
            print(f"\n{region_name}:")
            print(f"  Filaments analyzed: {data['n_filaments_valid']}")
            print(f"  PM/(L/3) mean: {data['pm_ratio_mean']:.3f} ± {data['pm_ratio_sem']:.3f}")
            print(f"  Interpretation: {data['interpretation']}")

        # Combined analysis
        all_ratios = []
        for data in all_results.values():
            all_ratios.extend([r['pm_ratio'] for r in data['individual_filaments']
                                  if r['pm_ratio'] is not None])

        if all_ratios:
            print(f"\nCombined across all regions:")
            print(f"  Mean PM/(L/3): {np.mean(all_ratios):.3f} ± {np.std(all_ratios):.3f}")
            print(f"  Median PM/(L/3): {np.median(all_ratios):.3f}")
            print(f"  N(filaments): {len(all_ratios)}")

            # Overall interpretation
            overall_mean = np.mean(all_ratios)
            if abs(overall_mean - 1.0) < 0.1:
                print(f"\n  ✓ STRONG SUPPORT: Individual HGBS filaments show PM ≈ L/3")
            elif abs(overall_mean - 1.0) < 0.2:
                print(f"\n  ~ MODERATE SUPPORT: Individual HGBS filaments show PM roughly equals L/3")
            else:
                print(f"\n  ✗ NO SUPPORT: Individual HGBS filaments do NOT show PM = L/3")

    print(f"\nAll results saved to per_filament_pm_validation_*.json files")


if __name__ == '__main__':
    main()
