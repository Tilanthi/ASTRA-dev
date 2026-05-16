#!/usr/bin/env python3
"""
HGBS IC5146 Discovery Science - Filament Analysis (No Core Catalog)

Modified analysis focusing on filament and skeleton properties since IC5146
lacks the standard HGBS core catalog.

Analyzes:
1. Column density and temperature maps
2. Filament skeleton statistics
3. Mass-per-unit-length (M_line) distribution
4. Junction identification
5. Filament network characterization

Author: ASTRA Discovery System
Date: 19 April 2026
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from astropy.io import fits
from astropy.wcs import WCS
from scipy.signal import convolve2d
from scipy import stats
import os
import warnings
warnings.filterwarnings('ignore')

rcParams['figure.dpi'] = 150
rcParams['font.size'] = 10
rcParams['figure.facecolor'] = 'white'

# ============================================================================
# DATA PATHS
# ============================================================================
HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_IC5146'

# FITS files
COL_DEN_FILE = os.path.join(HGBS_DIR, 'HGBS_ic5146_column_density_map.fits')
TEMP_FILE = os.path.join(HGBS_DIR, 'HGBS_ic5146_dust_temperature_map.fits')
SKELETON_FILE = os.path.join(HGBS_DIR, 'HGBS_ic5146_skeleton_map.fits')

# Physical constants
DISTANCE_PC = 260.0  # Distance to IC5146 (approximate, similar to other HGBS regions)
M_LINE_CRIT_THEORY = 16.0  # Msun/pc

# ============================================================================
# FILAMENT ANALYZER
# ============================================================================

class FilamentAnalyzer:
    """Analyze filament properties for regions without core catalogs."""

    def __init__(self):
        """Initialize the analyzer."""
        self.col_den_data = None
        self.col_den_header = None
        self.temp_data = None
        self.temp_header = None
        self.skel_data = None
        self.skel_header = None
        self.wcs = None
        self.pixel_size_pc = None

        print("="*70)
        print("HGBS IC5146 - FILAMENT ANALYSIS")
        print("="*70)

    def load_data(self):
        """Load FITS maps."""
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

        # Create WCS object
        self.wcs = WCS(self.col_den_header)

        # Calculate pixel size in pc
        try:
            cdelt1 = np.abs(self.col_den_header.get('CDELT1', 5.0/3600/3600))
            cdelt2 = np.abs(self.col_den_header.get('CDELT2', 5.0/3600/3600))
            pix_size_rad = (cdelt1 + cdelt2) / 2 * np.pi / 180
            self.pixel_size_pc = DISTANCE_PC * pix_size_rad
            print(f"  Pixel size: {self.pixel_size_pc:.6f} pc")
        except:
            self.pixel_size_pc = 0.00378  # Default
            print(f"  Using default pixel size: {self.pixel_size_pc:.6f} pc")

        print("  Data loaded successfully")

    def analyze_column_density(self):
        """Analyze column density map."""
        print("\n" + "="*70)
        print("COLUMN DENSITY MAP ANALYSIS")
        print("="*70)

        valid_data = self.col_den_data[np.isfinite(self.col_den_data)]

        print(f"\nMap statistics:")
        print(f"  Shape: {self.col_den_data.shape}")
        print(f"  Median N_H2: {np.median(valid_data)/1e21:.2f}e21 cm^-2")
        print(f"  Mean N_H2: {np.mean(valid_data)/1e21:.2f}e21 cm^-2")
        print(f"  Range: {np.min(valid_data)/1e21:.2f} - {np.max(valid_data)/1e21:.2f} e21 cm^-2")
        print(f"  Standard deviation: {np.std(valid_data)/1e21:.2f}e21 cm^-2")

        # Calculate area
        area_deg2 = np.prod(self.col_den_data.shape) * (self.pixel_size_pc / DISTANCE_PC * 180/np.pi)**2
        print(f"\n  Map area: {area_deg2:.2f} square degrees")

        return valid_data

    def analyze_temperature(self):
        """Analyze temperature map."""
        print("\n" + "="*70)
        print("TEMPERATURE MAP ANALYSIS")
        print("="*70)

        valid_data = self.temp_data[np.isfinite(self.temp_data)]
        valid_data = valid_data[(valid_data > 0) & (valid_data < 100)]  # Filter unreasonable values

        if len(valid_data) == 0:
            print("  No valid temperature data found")
            return None

        print(f"\nMap statistics:")
        print(f"  Median T_dust: {np.median(valid_data):.2f} K")
        print(f"  Mean T_dust: {np.mean(valid_data):.2f} K")
        print(f"  Range: {np.min(valid_data):.2f} - {np.max(valid_data):.2f} K")

        return valid_data

    def analyze_skeleton(self):
        """Analyze filament skeleton."""
        print("\n" + "="*70)
        print("FILAMENT SKELETON ANALYSIS")
        print("="*70)

        # Get skeleton mask
        filament_mask = self.skel_data > 0
        filament_pixels = np.sum(filament_mask)
        total_pixels = np.sum(np.isfinite(self.skel_data))

        print(f"\nSkeleton statistics:")
        print(f"  Total pixels: {total_pixels}")
        print(f"  Filament pixels: {filament_pixels}")
        print(f"  Filament fraction: {100*filament_pixels/total_pixels:.2f}%")

        # Skeleton value statistics
        skeleton_values = self.skel_data[filament_mask]
        if len(skeleton_values) > 0:
            print(f"\n  Skeleton value range: {np.min(skeleton_values):.1f} - {np.max(skeleton_values):.1f}")
            print(f"  Mean skeleton value: {np.mean(skeleton_values):.2f}")
            print(f"  Median skeleton value: {np.median(skeleton_values):.2f}")

        # Estimate filament length
        filament_length_pc = filament_pixels * self.pixel_size_pc
        print(f"\n  Total filament length: {filament_length_pc:.1f} pc")

        return filament_mask, skeleton_values

    def calculate_m_line_distribution(self):
        """Calculate M_line along filament skeleton."""
        print("\n" + "="*70)
        print("MASS-PER-UNIT-LENGTH (M_line) ANALYSIS")
        print("="*70)

        # Get filament pixels and their column densities
        filament_mask = self.skel_data > 0

        # Extract column density at filament pixels
        filament_densities = self.col_den_data[filament_mask]
        filament_skeleton_values = self.skel_data[filament_mask]

        # Filter out invalid density values
        filament_densities = filament_densities[np.isfinite(filament_densities)]
        filament_densities = filament_densities[filament_densities > 0]

        print(f"\nFilament column density statistics:")
        print(f"  Median N_H2 on filaments: {np.median(filament_densities)/1e21:.2f}e21 cm^-2")
        print(f"  Range: {np.min(filament_densities)/1e21:.2f} - {np.max(filament_densities)/1e21:.2f} e21 cm^-2")
        print(f"  Valid pixels: {len(filament_densities)}")

        # Calculate M_line for each filament pixel
        # Assuming characteristic filament width ~0.1 pc
        filament_width_pc = 0.1

        # Convert N_H2 to surface density in Msun/pc^2
        # N_H2 [cm^-2] * (mass of H2 molecule) * (pc/cm)^2 / Msun
        MU_H2 = 2.8  # mean molecular weight
        M_H = 1.67e-24  # mass of hydrogen atom [g]
        MSUN_G = 1.989e33  # solar mass [g]
        PC_TO_CM = 3.086e18  # parsec to cm

        surface_density = filament_densities * 1e21 * MU_H2 * M_H * (PC_TO_CM**2) / MSUN_G

        # M_line = surface density * width
        m_line_values = surface_density * filament_width_pc

        # Filter out any remaining invalid values
        m_line_values = m_line_values[np.isfinite(m_line_values)]
        m_line_values = m_line_values[(m_line_values > 0) & (m_line_values < 500)]

        if len(m_line_values) == 0:
            print(f"\nM_line calculation: No valid values found")
            print(f"  Surface density range: {np.min(surface_density):.6f} - {np.max(surface_density):.6f} Msun/pc^2")
            print(f"  M_line range: {np.min(m_line_values):.6f} - {np.max(m_line_values):.6f} Msun/pc")
            return np.array([])

        print(f"\nM_line statistics (assuming width = {filament_width_pc} pc):")
        print(f"  Median M_line: {np.median(m_line_values):.2f} Msun/pc")
        print(f"  Mean M_line: {np.mean(m_line_values):.2f} Msun/pc")
        print(f"  Range: {np.min(m_line_values):.2f} - {np.max(m_line_values):.2f} Msun/pc")
        print(f"  Standard deviation: {np.std(m_line_values):.2f} Msun/pc")

        # Compare to critical threshold
        above_critical = np.sum(m_line_values > M_LINE_CRIT_THEORY)
        fraction_above = 100 * above_critical / len(m_line_values)

        print(f"\nCritical threshold comparison (M_crit = {M_LINE_CRIT_THEORY} Msun/pc):")
        print(f"  Pixels above threshold: {above_critical} / {len(m_line_values)} ({fraction_above:.1f}%)")

        if fraction_above > 50:
            print(f"  → Most filaments are SUPERCRITICAL (unstable, forming stars)")
        else:
            print(f"  → Many filaments are SUBCRITICAL (stable)")

        return m_line_values

    def identify_junctions(self):
        """Identify filament junctions."""
        print("\n" + "="*70)
        print("JUNCTION IDENTIFICATION")
        print("="*70)

        # Get skeleton mask
        filament_mask = self.skel_data > 0
        skeleton_binary = filament_mask.astype(np.uint8)

        # Find branching points using morphological operations
        kernel = np.array([[0, 1, 0],
                           [1, 0, 1],
                           [0, 1, 0]])

        neighbor_count = convolve2d(skeleton_binary, kernel, mode='same')
        junction_mask = (neighbor_count >= 3) & filament_mask

        junction_y, junction_x = np.where(junction_mask)
        junctions = list(zip(junction_y, junction_x))

        print(f"\nJunction statistics:")
        print(f"  Total junctions identified: {len(junctions)}")

        # Extract properties at junctions
        if len(junctions) > 0:
            junction_nh2 = self.col_den_data[junction_y, junction_x]
            junction_skel = self.skel_data[junction_y, junction_x]

            print(f"  Junction N_H2: median = {np.median(junction_nh2)/1e21:.2f}e21 cm^-2")
            print(f"  Junction skeleton values: median = {np.median(junction_skel):.2f}")

        # High-density zones (top 10% of skeleton values)
        filament_skel_values = self.skel_data[filament_mask]
        high_skel_threshold = np.percentile(filament_skel_values, 90)
        high_skel_mask = (self.skel_data >= high_skel_threshold) & filament_mask

        high_skel_y, high_skel_x = np.where(high_skel_mask)
        high_density_zones = list(zip(high_skel_y, high_skel_x))

        print(f"\nHigh-density zones (convergence regions):")
        print(f"  Total zones: {len(high_density_zones)}")
        print(f"  Skeleton threshold: {high_skel_threshold:.2f}")

        return junctions, high_density_zones

    def analyze_filament_network(self):
        """Analyze filament network topology."""
        print("\n" + "="*70)
        print("FILAMENT NETWORK CHARACTERIZATION")
        print("="*70)

        filament_mask = self.skel_data > 0
        skeleton_values = self.skel_data[filament_mask]

        # Skeleton value distribution
        percentiles = [10, 25, 50, 75, 90, 95]
        print(f"\nSkeleton value distribution:")
        for p in percentiles:
            val = np.percentile(skeleton_values, p)
            print(f"  {p}%: {val:.2f}")

        # Categorize skeleton by strength
        weak_filaments = np.sum(skeleton_values < np.percentile(skeleton_values, 33))
        medium_filaments = np.sum((skeleton_values >= np.percentile(skeleton_values, 33)) &
                                   (skeleton_values < np.percentile(skeleton_values, 66)))
        strong_filaments = np.sum(skeleton_values >= np.percentile(skeleton_values, 66))

        print(f"\nFilament strength categories:")
        print(f"  Weak (bottom 33%): {weak_filaments} pixels ({100*weak_filaments/len(skeleton_values):.1f}%)")
        print(f"  Medium (middle 33%): {medium_filaments} pixels ({100*medium_filaments/len(skeleton_values):.1f}%)")
        print(f"  Strong (top 33%): {strong_filaments} pixels ({100*strong_filaments/len(skeleton_values):.1f}%)")

    def create_summary_visualization(self, output_dir='.'):
        """Create a summary visualization of filament properties."""
        print("\n" + "="*70)
        print("CREATING SUMMARY VISUALIZATION")
        print("="*70)

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Plot 1: Column density histogram
        ax = axes[0, 0]
        valid_data = self.col_den_data[np.isfinite(self.col_den_data)]
        ax.hist(valid_data/1e21, bins=50, alpha=0.7, edgecolor='black')
        ax.set_xlabel(r'N$_{\rm H_2}$ (10$^{21}$ cm$^{-2}$)')
        ax.set_ylabel('Number of Pixels')
        ax.set_title('Column Density Distribution')
        ax.axvline(np.median(valid_data)/1e21, color='red', linestyle='--', label='Median')
        ax.legend()
        ax.grid(alpha=0.3)

        # Plot 2: Temperature histogram
        ax = axes[0, 1]
        temp_valid = self.temp_data[np.isfinite(self.temp_data)]
        temp_valid = temp_valid[(temp_valid > 0) & (temp_valid < 100)]
        if len(temp_valid) > 0:
            ax.hist(temp_valid, bins=50, alpha=0.7, color='orange', edgecolor='black')
            ax.set_xlabel('Dust Temperature (K)')
            ax.set_ylabel('Number of Pixels')
            ax.set_title('Temperature Distribution')
            ax.axvline(np.median(temp_valid), color='red', linestyle='--', label='Median')
            ax.legend()
            ax.grid(alpha=0.3)

        # Plot 3: Skeleton value histogram
        ax = axes[1, 0]
        filament_mask = self.skel_data > 0
        skeleton_values = self.skel_data[filament_mask]
        ax.hist(skeleton_values, bins=50, alpha=0.7, color='green', edgecolor='black')
        ax.set_xlabel('Skeleton Value')
        ax.set_ylabel('Number of Pixels')
        ax.set_title('Filament Strength Distribution')
        ax.axvline(np.median(skeleton_values), color='red', linestyle='--', label='Median')
        ax.legend()
        ax.grid(alpha=0.3)

        # Plot 4: Summary statistics
        ax = axes[1, 1]
        ax.axis('off')

        # Calculate statistics
        valid_col = self.col_den_data[np.isfinite(self.col_den_data)]
        valid_temp = self.temp_data[np.isfinite(self.temp_data)]
        valid_temp = valid_temp[(valid_temp > 0) & (valid_temp < 100)]

        stats_text = f"""
IC5146 FILAMENT SUMMARY

Column Density:
  Median: {np.median(valid_col)/1e21:.2f}e21 cm^-2
  Range: {np.min(valid_col)/1e21:.1f} - {np.max(valid_col)/1e21:.1f} e21 cm^-2

Temperature:
  Median: {np.median(valid_temp):.1f} K (if available)

Filament Skeleton:
  Filament pixels: {np.sum(filament_mask)}
  Median skeleton value: {np.median(skeleton_values):.2f}

Total filament length: {np.sum(filament_mask) * self.pixel_size_pc:.1f} pc
        """

        ax.text(0.1, 0.5, stats_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='center',
               family='monospace',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        plt.tight_layout()
        plt.savefig(f'{output_dir}/ic5146_filament_analysis.png', dpi=150, bbox_inches='tight')
        plt.savefig(f'{output_dir}/ic5146_filament_analysis.pdf', bbox_inches='tight')
        plt.close()

        print(f"\n  Saved visualization to: {output_dir}/ic5146_filament_analysis.png")

    def run_analysis(self):
        """Run complete filament analysis."""
        # Load data
        self.load_data()

        # Analyze column density
        col_valid = self.analyze_column_density()

        # Analyze temperature
        temp_valid = self.analyze_temperature()

        # Analyze skeleton
        filament_mask, skeleton_values = self.analyze_skeleton()

        # Calculate M_line
        m_line_values = self.calculate_m_line_distribution()

        # Identify junctions
        junctions, high_density_zones = self.identify_junctions()

        # Analyze filament network
        self.analyze_filament_network()

        # Create visualization
        self.create_summary_visualization()

        # Summary
        print("\n" + "="*70)
        print("IC5146 FILAMENT ANALYSIS - SUMMARY")
        print("="*70)
        print(f"\nMap Properties:")
        print(f"  Region: IC5146")
        print(f"  Distance: {DISTANCE_PC} pc")
        print(f"  Map size: {self.col_den_data.shape[0]} x {self.col_den_data.shape[1]} pixels")
        print(f"  Median N_H2: {np.median(col_valid)/1e21:.2f}e21 cm^-2")

        print(f"\nFilament Properties:")
        print(f"  Total filament length: {np.sum(filament_mask) * self.pixel_size_pc:.1f} pc")
        print(f"  Junctions identified: {len(junctions)}")
        print(f"  High-density zones: {len(high_density_zones)}")

        print(f"\nM_line Properties:")
        print(f"  Median M_line: {np.median(m_line_values):.2f} Msun/pc")
        print(f"  Critical threshold (M_crit): {M_LINE_CRIT_THEORY} Msun/pc")
        print(f"  Above threshold: {100*np.sum(m_line_values > M_LINE_CRIT_THEORY)/len(m_line_values):.1f}%")

        # Save results
        results = {
            'distance_pc': DISTANCE_PC,
            'map_shape': self.col_den_data.shape,
            'median_nh2': np.median(col_valid),
            'median_temp': np.median(temp_valid) if temp_valid is not None else None,
            'filament_pixels': int(np.sum(filament_mask)),
            'filament_length_pc': float(np.sum(filament_mask) * self.pixel_size_pc),
            'junctions': len(junctions),
            'high_density_zones': len(high_density_zones),
            'median_m_line': float(np.median(m_line_values)),
            'm_line_values': m_line_values
        }

        np.savez('ic5146_filament_results.npz', **results)
        print(f"\nResults saved to: ic5146_filament_results.npz")

        return results


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run IC5146 filament analysis."""
    analyzer = FilamentAnalyzer()
    results = analyzer.run_analysis()

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print("\nNote: IC5146 lacks the standard HGBS core catalog.")
    print("This analysis focused on filament and skeleton properties only.")
    print("\nKey Findings:")
    print(f"  • {results['junctions']} filament junctions identified")
    print(f"  • {results['high_density_zones']} high-density zones")
    print(f"  • Median M_line: {results['median_m_line']:.2f} Msun/pc")
    print(f"  • Total filament length: {results['filament_length_pc']:.1f} pc")


if __name__ == '__main__':
    main()
