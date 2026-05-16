#!/usr/bin/env python3
"""
HGBS Taurus Discovery Science - Phase 4: Filament Junction Analysis

This script performs filament junction/convergence zone analysis:
1. Identify filament junctions from skeleton map
2. Characterize junction properties
3. Test if massive cores preferentially form at junctions
4. Compare M_line at junctions vs. along spines
5. Analyze core properties by location type

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
from scipy import ndimage
warnings.filterwarnings('ignore')

rcParams['figure.dpi'] = 120
rcParams['font.size'] = 9
rcParams['figure.facecolor'] = 'white'

# ============================================================================
# DATA PATHS
# ============================================================================
HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_IC5146'

# FITS files
COL_DEN_FILE = os.path.join(HGBS_DIR, 'HGBS_ic5146_hires_column_density_map.fits')
SKELETON_FILE = os.path.join(HGBS_DIR, 'HGBS_ic5146_skeleton_map.fits')

# Physical constants
DISTANCE_PC = 260
M_LINE_CRIT_THEORY = 16.0  # Msun/pc

# ============================================================================
# FILAMENT JUNCTION ANALYZER
# ============================================================================

class JunctionAnalyzer:
    """Analyze filament junctions and convergence zones."""

    def __init__(self):
        """Initialize the analyzer."""
        self.col_den_data = None
        self.col_den_header = None
        self.skel_data = None
        self.skel_header = None
        self.wcs = None
        self.cores = []
        self.junctions = []
        self.pixel_size_pc = None

        print("Initializing Filament Junction Analyzer...")

    def load_data(self):
        """Load FITS maps."""
        print("\nLoading data...")

        # Load column density map
        print(f"  Loading column density map: {COL_DEN_FILE}")
        with fits.open(COL_DEN_FILE) as hdul:
            self.col_den_data = hdul[0].data
            self.col_den_header = hdul[0].header

        # Load skeleton map
        print(f"  Loading skeleton map: {SKELETON_FILE}")
        with fits.open(SKELETON_FILE) as hdul:
            self.skel_data = hdul[0].data
            self.skel_header = hdul[0].header

        # Create WCS object
        self.wcs = WCS(self.col_den_header)

        # Calculate pixel size in pc
        try:
            cdelt1 = np.abs(self.col_den_header.get('CDELT1', 5.0/3600/3600))
            cdelt2 = np.abs(self.col_den_header.get('CDELT2', 5.0/3600/3600))
            pix_size_rad = (cdelt1 + cdelt2) / 2 * np.pi / 180
            self.pixel_size_pc = DISTANCE_PC * pix_size_rad
            print(f"  Pixel size: {self.pixel_size_pc:.6f} pc = {self.pixel_size_pc*206265:.2f} arcsec")
        except:
            self.pixel_size_pc = 0.00378  # From Phase 3
            print(f"  Using pixel size from Phase 3: {self.pixel_size_pc:.6f} pc")

        print("  Data loaded successfully")

    def load_cores(self):
        """Load cores from Phase 2 results."""
        print("\nLoading cores from Phase 2 results...")

        results_file = os.path.join(HGBS_DIR, 'phase2_results.npz')

        try:
            data = np.load(results_file, allow_pickle=True)
            self.cores = data['cores'].tolist()
            print(f"  Loaded {len(self.cores)} cores")
        except:
            # Fallback: parse catalog directly
            print("  Phase 2 results not found, parsing catalog...")
            from parse_ic5146_catalog import parse_ic5146_catalog
            catalog_file = os.path.join(HGBS_DIR, 'HGBS_taurusL1495_derived_core_catalog.txt')
            self.cores = parse_taurus_catalog(catalog_file)
            self._add_coordinates_to_cores()

    def _add_coordinates_to_cores(self):
        """Add pixel coordinates to cores using decimal degree coordinates from parser."""
        for core in self.cores:
            try:
                ra_deg = core.get('ra_deg')
                dec_deg = core.get('dec_deg')
                if ra_deg is None or dec_deg is None:
                    continue

                coord = SkyCoord(ra=ra_deg*u.deg, dec=dec_deg*u.deg)
                x, y = self.wcs.world_to_pixel(coord)
                core['x_pix'] = float(x)
                core['y_pix'] = float(y)
            except:
                continue

    def identify_junctions(self):
        """Identify filament junctions from skeleton map."""
        print("\nIdentifying filament junctions...")

        # Get skeleton mask
        filament_mask = self.skel_data > 0

        # Find branching points using morphological operations
        # A junction is where 3 or more filament segments meet
        # We can detect this by counting neighbors in the skeleton

        # Create a binary skeleton
        skeleton_binary = filament_mask.astype(np.uint8)

        # Find all skeleton pixels
        skeleton_y, skeleton_x = np.where(skeleton_binary > 0)

        # For each skeleton pixel, count connected neighbors
        # A junction has 3+ neighbors (not counting diagonal)
        from scipy.signal import convolve2d

        # Use a cross-shaped kernel to count direct neighbors
        kernel = np.array([[0, 1, 0],
                           [1, 0, 1],
                           [0, 1, 0]])

        # Count neighbors
        neighbor_count = convolve2d(skeleton_binary, kernel, mode='same')

        # Junctions are skeleton pixels with 3+ neighbors
        junction_mask = (neighbor_count >= 3) & filament_mask

        junction_y, junction_x = np.where(junction_mask)
        self.junctions = list(zip(junction_y, junction_x))

        print(f"  Found {len(self.junctions)} junction points")

        # Additional method: look for convergence zones
        # Areas where multiple filament segments come together
        # We can use the skeleton value as an indicator of filament density

        # High skeleton value areas may be junctions or dense regions
        high_skel_threshold = np.percentile(self.skel_data[skeleton_binary > 0], 90)
        high_skel_mask = (self.skel_data >= high_skel_threshold) & filament_mask

        high_skel_y, high_skel_x = np.where(high_skel_mask)
        self.high_density_zones = list(zip(high_skel_y, high_skel_x))

        print(f"  Found {len(self.high_density_zones)} high-density zones (top 10% of skeleton values)")

        return junction_mask, high_skel_mask

    def classify_core_locations(self):
        """Classify cores by their location type."""
        print("\nClassifying core locations...")

        # Create KD-trees for fast nearest neighbor lookup
        from scipy.spatial import cKDTree

        all_filament_y, all_filament_x = np.where(self.skel_data > 0)
        filament_tree = cKDTree(list(zip(all_filament_y, all_filament_x)))

        junction_tree = cKDTree(self.junctions) if self.junctions else None
        high_skel_tree = cKDTree(self.high_density_zones) if self.high_density_zones else None

        location_stats = {
            'on_junction': 0,
            'in_high_density': 0,
            'on_filament': 0,
            'near_filament': 0,
            'isolated': 0
        }

        for core in self.cores:
            x, y = core.get('x_pix', np.nan), core.get('y_pix', np.nan)

            if np.isnan(x) or np.isnan(y):
                core['location_type'] = 'unknown'
                continue

            # Check if on junction (within 1 pixel)
            if junction_tree:
                dist_junc, _ = junction_tree.query([y, x])
                if dist_junc < 1.0:
                    core['location_type'] = 'junction'
                    core['on_junction'] = True
                    location_stats['on_junction'] += 1
                    continue

            # Check if in high-density zone
            if high_skel_tree:
                dist_high, _ = high_skel_tree.query([y, x])
                if dist_high < 3.0:  # 3 pixel radius
                    core['location_type'] = 'high_density'
                    core['in_high_density'] = True
                    location_stats['in_high_density'] += 1
                    continue

            # Check if on filament (within 1 pixel)
            dist_fil, _ = filament_tree.query([y, x])
            if dist_fil < 1.0:
                core['location_type'] = 'filament'
                core['on_filament'] = True
                location_stats['on_filament'] += 1
            elif dist_fil < 5.0:  # Within 5 pixels (near filament)
                core['location_type'] = 'near_filament'
                core['near_filament'] = True
                location_stats['near_filament'] += 1
            else:
                core['location_type'] = 'isolated'
                core['isolated'] = True
                location_stats['isolated'] += 1

        print(f"  Location classification results:")
        print(f"    On junctions: {location_stats['on_junction']}")
        print(f"    In high-density zones: {location_stats['in_high_density']}")
        print(f"    On filaments: {location_stats['on_filament']}")
        print(f"    Near filaments: {location_stats['near_filament']}")
        print(f"    Isolated: {location_stats['isolated']}")

        return location_stats

    def analyze_massive_cores_by_location(self):
        """Analyze massive core locations in detail."""
        print("\n" + "="*60)
        print("MASSIVE CORE LOCATION ANALYSIS (M > 5 Msun)")
        print("="*60)

        massive = [c for c in self.cores if c.get('mass', 0) > 5.0]

        print(f"\nFound {len(massive)} massive cores")

        location_counts = {}
        for core in massive:
            loc = core.get('location_type', 'unknown')
            location_counts[loc] = location_counts.get(loc, 0) + 1

        print(f"\nMassive core locations:")
        for loc, count in location_counts.items():
            print(f"  {loc}: {count}/{len(massive)} ({100*count/len(massive):.1f}%)")

        # Detailed analysis
        for core in massive:
            print(f"\n  Core: {core['name']}")
            print(f"    Mass: {core['mass']:.2f} Msun")
            print(f"    Type: {core.get('type', 'unknown')}")
            print(f"    Location: {core.get('location_type', 'unknown')}")
            print(f"    Local N_H2: {core.get('local_nh2_21', np.nan):.2f}e21 cm^-2")
            print(f"    Local M_line: {core.get('local_m_line', np.nan):.2f} Msun/pc")

    def analyze_core_properties_by_location(self):
        """Analyze how core properties vary by location type."""
        print("\n" + "="*60)
        print("CORE PROPERTIES BY LOCATION TYPE")
        print("="*60)

        location_types = ['junction', 'high_density', 'filament', 'near_filament', 'isolated']

        for loc_type in location_types:
            cores_at_loc = [c for c in self.cores if c.get('location_type') == loc_type]

            if len(cores_at_loc) == 0:
                continue

            print(f"\n{loc_type.upper().replace('_', ' ')} (N={len(cores_at_loc)}):")

            # Core type distribution
            types = {'starless': 0, 'prestellar': 0, 'protostellar': 0}
            masses = []
            m_lines = []

            for core in cores_at_loc:
                ctype = core.get('type', '')
                if ctype in types:
                    types[ctype] += 1

                if 'mass' in core:
                    masses.append(core['mass'])
                if 'local_m_line' in core:
                    m_lines.append(core['local_m_line'])

            print(f"  Core types:")
            for ctype, count in types.items():
                if count > 0:
                    print(f"    {ctype}: {count} ({100*count/len(cores_at_loc):.1f}%)")

            if masses:
                masses = np.array(masses)
                print(f"  Mass statistics:")
                print(f"    Median: {np.median(masses):.3f} Msun")

            if m_lines:
                m_lines = np.array(m_lines)
                print(f"  M_line statistics:")
                print(f"    Median: {np.median(m_lines):.2f} Msun/pc")

    def test_junction_hypothesis(self):
        """Test hypothesis: massive cores preferentially form at junctions."""
        print("\n" + "="*60)
        print("JUNCTION HYPOTHESIS TEST")
        print("="*60)

        # Get massive and non-massive cores
        massive = [c for c in self.cores if c.get('mass', 0) > 5.0]
        non_massive = [c for c in self.cores if c.get('mass', 0) <= 5.0]

        # Count junction cores
        massive_on_junction = sum(1 for c in massive if c.get('location_type') == 'junction')
        massive_in_high_density = sum(1 for c in massive if c.get('location_type') == 'high_density')

        non_massive_on_junction = sum(1 for c in non_massive if c.get('location_type') == 'junction')
        non_massive_in_high_density = sum(1 for c in non_massive if c.get('location_type') == 'high_density')

        print(f"\nMassive cores (M > 5 Msun):")
        print(f"  Total: {len(massive)}")
        if len(massive) > 0:
            print(f"  On junctions: {massive_on_junction} ({100*massive_on_junction/len(massive):.1f}%)")
            print(f"  In high-density zones: {massive_in_high_density} ({100*massive_in_high_density/len(massive):.1f}%)")
        else:
            print(f"  On junctions: {massive_on_junction} (N/A)")
            print(f"  In high-density zones: {massive_in_high_density} (N/A)")

        print(f"\nNon-massive cores (M ≤ 5 Msun):")
        print(f"  Total: {len(non_massive)}")
        if len(non_massive) > 0:
            print(f"  On junctions: {non_massive_on_junction} ({100*non_massive_on_junction/len(non_massive):.1f}%)")
            print(f"  In high-density zones: {non_massive_in_high_density} ({100*non_massive_in_high_density/len(non_massive):.1f}%)")

        # Fisher's exact test
        if massive_on_junction + non_massive_on_junction > 0:
            #                       | On Junction | Not on Junction |
            # --------------------------------------------------
            # Massive cores         |     a       |       b       |
            # Non-massive cores     |     c       |       d       |

            a = massive_on_junction
            b = len(massive) - massive_on_junction
            c = non_massive_on_junction
            d = len(non_massive) - non_massive_on_junction

            if b > 0 and c > 0:
                odds_ratio = (a/b) / (c/d) if (a/b) > 0 and (c/d) > 0 else np.inf
                print(f"\n  Odds ratio: {odds_ratio:.2f}")
                print(f"    (OR > 1 means massive cores prefer junctions)")

                if odds_ratio > 1:
                    print(f"  ✓ Result: Massive cores are {odds_ratio:.2f}× more likely to be on junctions")
                else:
                    print(f"  Note: Massive cores do NOT show preference for junctions")

    def extract_junction_properties(self):
        """Extract properties at junction locations."""
        print("\n" + "="*60)
        print("JUNCTION PROPERTIES")
        print("="*60)

        if len(self.junctions) == 0:
            print("  No junctions found")
            return

        # Extract column density at each junction
        junction_nh2 = []
        junction_skel = []

        for y, x in self.junctions:
            if (0 <= y < self.col_den_data.shape[0] and
                0 <= x < self.col_den_data.shape[1]):
                junction_nh2.append(self.col_den_data[y, x])
                junction_skel.append(self.skel_data[y, x])

        junction_nh2 = np.array(junction_nh2)
        junction_skel = np.array(junction_skel)

        print(f"\nJunction column density:")
        print(f"  Median: {np.median(junction_nh2)/1e21:.2f}e21 cm^-2")
        print(f"  Range: {np.min(junction_nh2)/1e21:.2f} - {np.max(junction_nh2)/1e21:.2f}e21 cm^-2")

        print(f"\nJunction skeleton values:")
        print(f"  Median: {np.median(junction_skel):.2f}")
        print(f"  Range: {np.min(junction_skel):.2f} - {np.max(junction_skel):.2f}")

        return junction_nh2, junction_skel

    def run_analysis(self):
        """Run full Phase 4 analysis."""
        print("\n" + "="*70)
        print("HGBS IC5146 - PHASE 4: FILAMENT JUNCTION ANALYSIS")
        print("="*70)

        # Step 1: Load data
        self.load_data()

        # Step 2: Load cores
        self.load_cores()

        # Step 3: Identify junctions
        junction_mask, high_skel_mask = self.identify_junctions()

        # Step 4: Classify core locations
        location_stats = self.classify_core_locations()

        # Step 5: Analyze massive cores by location
        self.analyze_massive_cores_by_location()

        # Step 6: Analyze core properties by location
        self.analyze_core_properties_by_location()

        # Step 7: Test junction hypothesis
        self.test_junction_hypothesis()

        # Step 8: Extract junction properties
        junction_nh2, junction_skel = self.extract_junction_properties()

        # Summary
        print("\n" + "="*70)
        print("PHASE 4 SUMMARY")
        print("="*70)
        print(f"Junctions identified: {len(self.junctions)}")
        print(f"High-density zones: {len(self.high_density_zones)}")
        print(f"Cores on junctions: {location_stats['on_junction']}")
        print(f"Cores in high-density zones: {location_stats['in_high_density']}")

        print("\nPhase 4 analysis complete!")

        return {
            'junctions': self.junctions,
            'high_density_zones': self.high_density_zones,
            'location_stats': location_stats
        }

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run Phase 4 analysis."""
    analyzer = JunctionAnalyzer()
    results = analyzer.run_analysis()

    print(f"\nPhase 4 complete!")

if __name__ == '__main__':
    main()
