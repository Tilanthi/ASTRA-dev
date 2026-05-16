#!/usr/bin/env python3
"""
HGBS Perseus Discovery Science - Phase 2: Core-Filament Association

This script performs core-filament association analysis:
1. Convert core RA/Dec to pixel coordinates
2. Project cores onto filament skeleton
3. Calculate distance from each core to nearest filament
4. Extract local filament properties at core locations
5. Analyze core spacing along filaments
6. Identify core formation preferences

Author: ASTRA Discovery System
Date: 18 April 2026
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.wcs import WCS
import os
import warnings
warnings.filterwarnings('ignore')

rcParams['figure.dpi'] = 120
rcParams['font.size'] = 9
rcParams['figure.facecolor'] = 'white'

# ============================================================================
# DATA PATHS
# ============================================================================
HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS/HGBS_PERSEUS'
HGBS_PARENT = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS'

# FITS files
COL_DEN_FILE = os.path.join(HGBS_DIR, 'HGBS_perseus_hires_column_density_map.fits')
TEMP_FILE = os.path.join(HGBS_DIR, 'HGBS_perseus_dust_temperature_map.fits')
SKELETON_FILE = os.path.join(HGBS_PARENT, 'HGBS_perseus_skeleton_map.fits')

# Catalog file
CAT_FILE = os.path.join(HGBS_DIR, 'HGBS_perseus_derived_core_catalog.txt')

# ============================================================================
# PHASE 2: CORE-FILAMENT ASSOCIATION
# ============================================================================

class CoreFilamentAnalyzer:
    """Analyze core-filament relationships in HGBS data."""

    def __init__(self):
        """Initialize the analyzer."""
        self.col_den_data = None
        self.col_den_header = None
        self.temp_data = None
        self.skel_data = None
        self.skel_header = None
        self.wcs = None
        self.cores = []
        self.cores_with_coords = []

        print("Initializing HGBS Core-Filament Analyzer...")

    def load_data(self):
        """Load FITS maps and core catalog."""
        print("\nLoading data...")

        # Load column density map
        print(f"  Loading column density map: {COL_DEN_FILE}")
        with fits.open(COL_DEN_FILE) as hdul:
            self.col_den_data = hdul[0].data
            self.col_den_header = hdul[0].header

        # Load temperature map
        print(f"  Loading temperature map: {TEMP_FILE}")
        with fits.open(TEMP_FILE) as hdul:
            self.temp_data = hdul[0].data
            self.temp_header = hdul[0].header

        # Load skeleton map
        print(f"  Loading skeleton map: {SKELETON_FILE}")
        with fits.open(SKELETON_FILE) as hdul:
            self.skel_data = hdul[0].data
            self.skel_header = hdul[0].header

        # Create WCS object for coordinate conversion
        self.wcs = WCS(self.col_den_header)

        print(f"  Data shapes: {self.col_den_data.shape}")
        print(f"  Coordinate system: {self.wcs}")
        print("  All maps loaded successfully")

    def parse_catalog(self):
        """Parse core catalog."""
        print(f"\nParsing core catalog: {CAT_FILE}")

        from parse_perseus_catalog import parse_perseus_catalog
        self.cores = parse_perseus_catalog(CAT_FILE)
        print(f"  Loaded {len(self.cores)} cores")

    def convert_coordinates(self):
        """Convert core RA/Dec to pixel coordinates."""
        print("\nConverting core coordinates to pixel space...")

        for core in self.cores:
            try:
                # Parse RA and Dec (format: "18:21:54.63" and "-02:55:57.2")
                ra_str = core.get('ra', '')
                dec_str = core.get('dec', '')

                if not ra_str or not dec_str:
                    continue

                # Create SkyCoord object
                coord = SkyCoord(ra=ra_str, dec=dec_str, unit=(u.hourangle, u.deg))

                # Convert to pixel coordinates
                x, y = self.wcs.world_to_pixel(coord)

                # Store in core
                core['x_pix'] = float(x)
                core['y_pix'] = float(y)
                core['ra_deg'] = coord.ra.deg
                core['dec_deg'] = coord.dec.deg

                self.cores_with_coords.append(core)

            except Exception as e:
                # Skip cores that fail coordinate conversion
                continue

        print(f"  Successfully converted {len(self.cores_with_coords)}/{len(self.cores)} cores")

    def calculate_filament_distances(self):
        """Calculate distance from each core to nearest filament."""
        print("\nCalculating core-filament distances...")

        # Create boolean mask of filament pixels
        filament_mask = self.skel_data > 0
        filament_pixels = np.argwhere(filament_mask)

        if len(filament_pixels) == 0:
            print("  ERROR: No filament pixels found!")
            return

        print(f"  Found {len(filament_pixels)} filament pixels")

        # For each core, find distance to nearest filament pixel
        distances = []
        on_filament = 0

        for core in self.cores_with_coords:
            x, y = core['x_pix'], core['y_pix']

            # Check if core is on filament (within 1 pixel)
            if (0 <= int(x) < self.skel_data.shape[1] and
                0 <= int(y) < self.skel_data.shape[0]):
                if filament_mask[int(y), int(x)]:
                    dist = 0.0
                    on_filament += 1
                else:
                    # Find nearest filament pixel
                    # Calculate distance to all filament pixels (can be slow)
                    # Optimized: use a subset or KDTree for large datasets
                    diffs = filament_pixels - np.array([int(y), int(x)])
                    dists = np.sqrt(diffs[:, 0]**2 + diffs[:, 1]**2)
                    dist = float(np.min(dists))
            else:
                dist = np.nan

            distances.append(dist)
            core['filament_distance_px'] = dist

            # Convert pixel distance to physical distance (using CDELT)
            try:
                cdelt1 = np.abs(self.col_den_header.get('CDELT1', 1.0/3600))
                cdelt2 = np.abs(self.col_den_header.get('CDELT2', 1.0/3600))
                # Average pixel size in degrees
                pix_size_deg = (cdelt1 + cdelt2) / 2
                # At 260 pc distance
                dist_pc = 230 * np.tan(np.deg2rad(pix_size_deg * 3600)) * dist
                core['filament_distance_pc'] = dist_pc
            except:
                core['filament_distance_pc'] = np.nan

        distances = np.array([d for d in distances if not np.isnan(d)])
        print(f"  Cores on filaments: {on_filament}/{len(self.cores_with_coords)} ({100*on_filament/len(self.cores_with_coords):.1f}%)")
        print(f"  Median distance to filament: {np.median(distances):.2f} pixels")

    def extract_local_properties(self):
        """Extract local filament properties at each core location."""
        print("\nExtracting local filament properties...")

        for core in self.cores_with_coords:
            x, y = int(core['x_pix']), int(core['y_pix'])

            # Ensure coordinates are within bounds
            if not (0 <= x < self.col_den_data.shape[1] and 0 <= y < self.col_den_data.shape[0]):
                core['local_nh2'] = np.nan
                core['local_temp'] = np.nan
                continue

            # Extract local column density
            core['local_nh2'] = float(self.col_den_data[y, x])
            core['local_nh2_21'] = core['local_nh2'] / 1e21  # Convert to 10^21 cm^-2

            # Extract local temperature
            core['local_temp'] = float(self.temp_data[y, x])

            # Extract skeleton value (if on filament)
            if self.skel_data[y, x] > 0:
                core['skeleton_value'] = float(self.skel_data[y, x])
                core['on_filament'] = True
            else:
                core['skeleton_value'] = 0.0
                core['on_filament'] = False

        # Print statistics
        on_filament = [c for c in self.cores_with_coords if c.get('on_filament', False)]
        print(f"  Cores on filament skeleton: {len(on_filament)}")

        # Filter out NaN values for statistics
        nh2_vals = [c['local_nh2_21'] for c in self.cores_with_coords if not np.isnan(c.get('local_nh2_21', np.nan))]
        temp_vals = [c['local_temp'] for c in self.cores_with_coords if not np.isnan(c.get('local_temp', np.nan))]

        if nh2_vals:
            print(f"  Median local N_H2: {np.median(nh2_vals):.2f}e21 cm^-2")
        if temp_vals:
            print(f"  Median local T: {np.median(temp_vals):.2f} K")

    def analyze_core_spacing(self):
        """Analyze core spacing along filaments."""
        print("\nAnalyzing core spacing along filaments...")

        # Get cores on filaments
        filament_cores = [c for c in self.cores_with_coords if c.get('on_filament', False)]

        if len(filament_cores) < 2:
            print("  ERROR: Need at least 2 cores on filaments for spacing analysis")
            return

        print(f"  Found {len(filament_cores)} cores on filaments")

        # Calculate pairwise distances
        from scipy.spatial.distance import pdist

        # Get pixel coordinates
        coords = np.array([[c['x_pix'], c['y_pix']] for c in filament_cores])

        # Calculate pairwise distances
        pair_dists = pdist(coords, metric='euclidean')
        pair_dists_pc = self._pixels_to_pc(pair_dists)

        print(f"  Pairwise distances:")
        print(f"    Median: {np.median(pair_dists_pc):.3f} pc")
        print(f"    Mean: {np.mean(pair_dists_pc):.3f} pc")
        print(f"    Min: {np.min(pair_dists_pc):.3f} pc")
        print(f"    Max: {np.max(pair_dists_pc):.3f} pc")

        # Calculate nearest-neighbor distances
        from scipy.spatial import cKDTree
        tree = cKDTree(coords)
        nn_dists, _ = tree.query(coords, k=2)  # k=2 because first match is self
        nn_dists = nn_dists[:, 1]  # Get second column (nearest neighbor)
        nn_dists_pc = self._pixels_to_pc(nn_dists)

        print(f"  Nearest-neighbor distances:")
        print(f"    Median: {np.median(nn_dists_pc):.3f} pc")
        print(f"    Mean: {np.mean(nn_dists_pc):.3f} pc")
        print(f"    Min: {np.min(nn_dists_pc):.3f} pc")
        print(f"    Max: {np.max(nn_dists_pc):.3f} pc")

        # Expected fragmentation scale (4 × filament width)
        # Filament width ~0.1 pc from literature
        expected_spacing = 4 * 0.1
        print(f"  Expected fragmentation scale (4 × width): ~{expected_spacing:.3f} pc")
        print(f"  Observed vs. expected ratio: {np.median(nn_dists_pc)/expected_spacing:.2f}")

        return {
            'pair_dists_pc': pair_dists_pc,
            'nn_dists_pc': nn_dists_pc,
            'expected_spacing': expected_spacing
        }

    def _pixels_to_pc(self, pixel_dist):
        """Convert pixel distance to parsecs at 260 pc."""
        try:
            # CDELT is in degrees/pixel
            cdelt1 = np.abs(self.col_den_header.get('CDELT1', 5.0/3600/3600))  # Default: 5 arcsec
            cdelt2 = np.abs(self.col_den_header.get('CDELT2', 5.0/3600/3600))  # Default: 5 arcsec
            # Average pixel size in radians
            pix_size_rad = (cdelt1 + cdelt2) / 2 * np.pi / 180
            # Distance to cloud (260 pc)
            # Physical size = distance × angle (small angle approximation)
            dist_pc = 230 * pix_size_rad * pixel_dist
            return dist_pc
        except:
            return pixel_dist * 0.006  # Approximate: 5 arcsec at 260 pc ≈ 0.006 pc

    def analyze_by_core_type(self):
        """Analyze core-filament relationship by core type."""
        print("\nAnalyzing core-filament relationship by type...")

        # Separate by type
        types = ['starless', 'prestellar', 'protostellar']

        for ctype in types:
            cores_of_type = [c for c in self.cores_with_coords if c.get('type') == ctype]
            on_filament = [c for c in cores_of_type if c.get('on_filament', False)]

            print(f"\n  {ctype.upper()} cores (N={len(cores_of_type)}):")

            if len(cores_of_type) == 0:
                continue

            # Fraction on filaments
            frac_on_fil = len(on_filament) / len(cores_of_type) if len(cores_of_type) > 0 else 0
            print(f"    On filaments: {len(on_filament)}/{len(cores_of_type)} ({100*frac_on_fil:.1f}%)")

            # Local properties
            nh2_vals = [c['local_nh2_21'] for c in cores_of_type if not np.isnan(c.get('local_nh2_21', np.nan))]
            temp_vals = [c['local_temp'] for c in cores_of_type if not np.isnan(c.get('local_temp', np.nan))]

            if nh2_vals:
                print(f"    Local N_H2: median = {np.median(nh2_vals):.2f}e21 cm^-2")
            if temp_vals:
                print(f"    Local T: median = {np.median(temp_vals):.2f} K")

    def analyze_massive_cores(self):
        """Analyze massive cores (M > 5 Msun) in detail."""
        print("\nAnalyzing massive cores (M > 5 Msun)...")

        massive = [c for c in self.cores_with_coords if c.get('mass', 0) > 5.0]

        print(f"  Found {len(massive)} massive cores")

        for core in massive:
            print(f"\n  Core: {core['name']}")
            print(f"    Mass: {core['mass']:.2f} Msun")
            print(f"    Type: {core.get('type', 'unknown')}")
            print(f"    On filament: {core.get('on_filament', False)}")
            print(f"    Local N_H2: {core.get('local_nh2_21', np.nan):.2f}e21 cm^-2")
            print(f"    Local T: {core.get('local_temp', np.nan):.1f} K")
            print(f"    Skeleton value: {core.get('skeleton_value', 0):.1f}")

    def run_analysis(self):
        """Run full Phase 2 analysis."""
        print("\n" + "="*70)
        print("HGBS PERSEUS - PHASE 2: CORE-FILAMENT ASSOCIATION")
        print("="*70)

        # Step 1: Load data
        self.load_data()

        # Step 2: Parse catalog
        self.parse_catalog()

        # Step 3: Convert coordinates
        self.convert_coordinates()

        # Step 4: Calculate filament distances
        self.calculate_filament_distances()

        # Step 5: Extract local properties
        self.extract_local_properties()

        # Step 6: Analyze core spacing
        spacing_results = self.analyze_core_spacing()

        # Step 7: Analyze by core type
        self.analyze_by_core_type()

        # Step 8: Analyze massive cores
        self.analyze_massive_cores()

        # Summary
        print("\n" + "="*70)
        print("PHASE 2 SUMMARY")
        print("="*70)
        print(f"Total cores with coordinates: {len(self.cores_with_coords)}")
        print(f"Cores on filaments: {sum(1 for c in self.cores_with_coords if c.get('on_filament', False))}")
        print(f"Median core spacing: {np.median(spacing_results['nn_dists_pc']):.3f} pc")
        print(f"Expected fragmentation scale: ~{spacing_results['expected_spacing']:.3f} pc")

        return self.cores_with_coords

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run Phase 2 analysis."""
    analyzer = CoreFilamentAnalyzer()
    results = analyzer.run_analysis()

    # Save results
    output_file = 'phase2_results.npz'
    np.savez(output_file, cores=results)

    print(f"\nResults saved to: {output_file}")
    print("Phase 2 analysis complete!")

if __name__ == '__main__':
    main()
