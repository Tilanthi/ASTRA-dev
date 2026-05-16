#!/usr/bin/env python3
"""
HGBS Aquila Discovery Science - Phase 1: Data Exploration and Characterization

This script performs initial data exploration of the Herschel Gould Belt Survey
Aquila region data, including:
- Loading FITS maps (intensity, column density, temperature, skeleton)
- Loading core catalogs (observed and derived properties)
- Basic statistics and visualization
- Filament network characterization

Author: ASTRA Discovery System
Date: 17 April 2026
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from astropy.io import fits
from astropy.table import Table
from astropy import units as u
from astropy.coordinates import SkyCoord
import os
import warnings
warnings.filterwarnings('ignore')

# Set up plotting for publication quality
rcParams['figure.dpi'] = 150
rcParams['font.size'] = 10
rcParams['figure.facecolor'] = 'white'

# ============================================================================
# DATA PATHS
# ============================================================================
HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS/HGBS_AQUILA'

# FITS files
FITS_FILES = {
    '70_micron': os.path.join(HGBS_DIR, 'aquilaM2-070.fits'),
    '160_micron': os.path.join(HGBS_DIR, 'aquilaM2-160.fits'),
    '250_micron': os.path.join(HGBS_DIR, 'aquilaM2-250.fits'),
    '350_micron': os.path.join(HGBS_DIR, 'aquilaM2-350.fits'),
    '500_micron': os.path.join(HGBS_DIR, 'aquilaM2-500.fits'),
    'column_density': os.path.join(HGBS_DIR, 'HGBS_aquilaM2_column_density_map.fits'),
    'dust_temperature': os.path.join(HGBS_DIR, 'HGBS_aquilaM2_dust_temperature_map.fits'),
    'column_density_hires': os.path.join(HGBS_DIR, 'HGBS_aquilaM2_hires_column_density_map.fits'),
    'skeleton': os.path.join(HGBS_DIR, 'HGBS_aquilaM2_skeleton_map.fits'),
}

# Catalog files
CAT_FILES = {
    'derived': os.path.join(HGBS_DIR, 'HGBS_aquilaM2_derived_core_catalog.txt'),
    'observed': os.path.join(HGBS_DIR, 'HGBS_aquilaM2_observed_core_catalog.txt'),
}

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_fits_data(filename):
    """Load FITS image and return data, header."""
    with fits.open(filename) as hdul:
        data = hdul[0].data
        header = hdul[0].header
    return data, header

def load_core_catalog(filename):
    """Load HGBS core catalog from text file."""
    # Skip header lines (start after the separator line)
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Find where data starts (after the line with many dashes)
    data_start = 0
    for i, line in enumerate(lines):
        if '---' in line and i > 30:
            data_start = i + 1
            break

    # Parse the fixed-width format data
    # This is a simplified parser - may need adjustment
    cores = []
    for line in lines[data_start:]:
        if line.strip() and not line.startswith('|'):
            parts = line.split()
            if len(parts) > 5:
                cores.append(parts)

    return cores

def load_catalog_astropy(filename):
    """Load catalog using astropy (more robust)."""
    # Read as ASCII with fixed format
    # Skip header comments
    data = []
    with open(filename, 'r') as f:
        in_data = False
        for line in f:
            if '---' in line and 'runNO' in line:
                in_data = True
                continue
            if in_data:
                if line.strip() and not line.startswith('|'):
                    # Parse the fixed-width data
                    parts = line.split()
                    if len(parts) > 5 and parts[0].isdigit():
                        data.append(parts)

    return data

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def analyze_column_density_map(data, header):
    """Analyze column density map properties."""
    print("\n" + "="*60)
    print("COLUMN DENSITY MAP ANALYSIS")
    print("="*60)

    # Basic statistics
    valid_data = data[np.isfinite(data)]
    print(f"Shape: {data.shape}")
    print(f"Min value: {np.nanmin(data):.3e} cm^-2")
    print(f"Max value: {np.nanmax(data):.3e} cm^-2")
    print(f"Mean: {np.nanmean(valid_data):.3e} cm^-2")
    print(f"Median: {np.nanmedian(valid_data):.3e} cm^-2")
    print(f"Std dev: {np.nanstd(valid_data):.3e} cm^-2")

    # Convert to more convenient units (10^21 cm^-2)
    data_21 = data / 1e21
    print(f"\nIn units of 10^21 cm^-2:")
    print(f"Range: {np.nanmin(data_21):.2f} - {np.nanmax(data_21):.2f}")
    print(f"Median: {np.nanmedian(data_21):.2f}")

    # Count pixels above star formation threshold
    # Av > 7 mag corresponds to N_H2 > 7e21 cm^-2
    high_av_pixels = np.sum(data > 7e21)
    total_pixels = np.sum(np.isfinite(data))
    print(f"\nPixels above Av~7 mag (N_H2 > 7e21 cm^-2): {high_av_pixels} ({100*high_av_pixels/total_pixels:.1f}%)")

    return valid_data

def analyze_temperature_map(data, header):
    """Analyze dust temperature map properties."""
    print("\n" + "="*60)
    print("DUST TEMPERATURE MAP ANALYSIS")
    print("="*60)

    valid_data = data[np.isfinite(data)]
    print(f"Shape: {data.shape}")
    print(f"Min temperature: {np.nanmin(data):.2f} K")
    print(f"Max temperature: {np.nanmax(data):.2f} K")
    print(f"Mean: {np.nanmean(valid_data):.2f} K")
    print(f"Median: {np.nanmedian(valid_data):.2f} K")
    print(f"Std dev: {np.nanstd(valid_data):.2f} K")

    # Temperature distribution
    print(f"\nTemperature percentiles:")
    for p in [10, 25, 50, 75, 90]:
        print(f"  {p}%: {np.percentile(valid_data, p):.2f} K")

    return valid_data

def analyze_skeleton_map(data, header):
    """Analyze filament skeleton map."""
    print("\n" + "="*60)
    print("FILAMENT SKELETON MAP ANALYSIS")
    print("="*60)

    # Non-zero pixels are part of filaments
    filament_mask = data > 0
    filament_pixels = np.sum(filament_mask)
    total_pixels = np.sum(np.isfinite(data))

    print(f"Total pixels: {total_pixels}")
    print(f"Filament pixels: {filament_pixels} ({100*filament_pixels/total_pixels:.2f}%)")

    # Skeleton statistics
    skeleton_values = data[filament_mask]
    if len(skeleton_values) > 0:
        print(f"Skeleton value range: {np.min(skeleton_values)} - {np.max(skeleton_values)}")
        print(f"Mean skeleton value: {np.mean(skeleton_values):.2f}")

    return filament_mask

def analyze_derived_catalog(data_list):
    """Analyze derived core catalog."""
    print("\n" + "="*60)
    print("DERIVED CORE CATALOG ANALYSIS")
    print("="*60)

    n_cores = len(data_list)
    print(f"Number of cores: {n_cores}")

    # Parse core properties from catalog data
    # Columns based on catalog header:
    # (1) runNO, (2) Core_name, (3-4) RA/Dec, (5-6) R_core [pc],
    # (7-8) M_core [Msun], (9-10) T_dust [K],
    # (11) Nh2_peak, (12-13) Nh2_ave, (14-15) nh2_peak, (16-17) nh2_ave,
    # (18) alpha_BE, (19) Core_type, (20) Comments

    core_types = {'starless': 0, 'prestellar': 0, 'protostellar': 0}
    masses = []
    temps = []
    sizes = []
    nh2_peaks = []
    alpha_be = []

    for parts in data_list:
        if len(parts) > 18:
            try:
                # Core type
                if 'starless' in ' '.join(parts[-2:]):
                    core_types['starless'] += 1
                elif 'prestellar' in ' '.join(parts[-2:]):
                    core_types['prestellar'] += 1
                elif 'protostellar' in ' '.join(parts[-2:]):
                    core_types['protostellar'] += 1

                # Mass (column 7, first value)
                if len(parts) > 7:
                    try:
                        m = float(parts[7])
                        masses.append(m)
                    except:
                        pass

                # Temperature (column 9, first value)
                if len(parts) > 9:
                    try:
                        t = float(parts[9])
                        temps.append(t)
                    except:
                        pass

                # Size (column 5, first value)
                if len(parts) > 5:
                    try:
                        s = float(parts[5])
                        sizes.append(s)
                    except:
                        pass

                # Peak column density (column 11)
                if len(parts) > 11:
                    try:
                        n = float(parts[11])
                        nh2_peaks.append(n)
                    except:
                        pass

                # Bonnor-Eert ratio (column 18)
                if len(parts) > 18:
                    try:
                        a = float(parts[18])
                        alpha_be.append(a)
                    except:
                        pass
            except Exception as e:
                continue

    print(f"\nCore type distribution:")
    for ctype, count in core_types.items():
        print(f"  {ctype}: {count} ({100*count/n_cores if n_cores > 0 else 0:.1f}%)")

    if masses:
        print(f"\nCore mass statistics [Msun]:")
        print(f"  Range: {min(masses):.3f} - {max(masses):.3f}")
        print(f"  Median: {np.median(masses):.3f}")
        print(f"  Mean: {np.mean(masses):.3f}")

    if temps:
        print(f"\nCore temperature statistics [K]:")
        print(f"  Range: {min(temps):.2f} - {max(temps):.2f}")
        print(f"  Median: {np.median(temps):.2f}")
        print(f"  Mean: {np.mean(temps):.2f}")

    if sizes:
        print(f"\nCore size statistics [pc]:")
        print(f"  Range: {min(sizes):.4f} - {max(sizes):.4f}")
        print(f"  Median: {np.median(sizes):.4f}")

    if alpha_be:
        print(f"\nBonnor-Eert ratio statistics:")
        print(f"  Range: {min(alpha_be):.3f} - {max(alpha_be):.3f}")
        print(f"  Median: {np.median(alpha_be):.3f}")
        # Count potentially bound cores
        n_bound = sum(1 for a in alpha_be if a < 2.0)  # Approximate threshold
        print(f"  Potentially bound (alpha_BE < 2): {n_bound}/{len(alpha_be)} ({100*n_bound/len(alpha_be):.1f}%)")

    return {
        'n_cores': n_cores,
        'core_types': core_types,
        'masses': masses,
        'temps': temps,
        'sizes': sizes,
        'nh2_peaks': nh2_peaks,
        'alpha_be': alpha_be
    }

# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def main():
    """Run Phase 1 analysis."""
    print("\n" + "="*70)
    print("HGBS AQUILA - DISCOVERY SCIENCE PHASE 1")
    print("Data Exploration and Characterization")
    print("="*70)

    # Load column density map
    print("\nLoading column density map...")
    try:
        col_den_data, col_den_header = load_fits_data(FITS_FILES['column_density'])
        col_valid = analyze_column_density_map(col_den_data, col_den_header)
    except Exception as e:
        print(f"Error loading column density map: {e}")
        col_den_data = None

    # Load temperature map
    print("\nLoading dust temperature map...")
    try:
        temp_data, temp_header = load_fits_data(FITS_FILES['dust_temperature'])
        temp_valid = analyze_temperature_map(temp_data, temp_header)
    except Exception as e:
        print(f"Error loading temperature map: {e}")
        temp_data = None

    # Load skeleton map
    print("\nLoading filament skeleton map...")
    try:
        skel_data, skel_header = load_fits_data(FITS_FILES['skeleton'])
        filament_mask = analyze_skeleton_map(skel_data, skel_header)
    except Exception as e:
        print(f"Error loading skeleton map: {e}")
        filament_mask = None

    # Load derived core catalog
    print("\nLoading derived core catalog...")
    try:
        catalog_data = load_catalog_astropy(CAT_FILES['derived'])
        catalog_stats = analyze_derived_catalog(catalog_data)
    except Exception as e:
        print(f"Error loading core catalog: {e}")
        catalog_stats = None

    # Summary
    print("\n" + "="*70)
    print("PHASE 1 SUMMARY")
    print("="*70)
    print(f"Column density map: {'Loaded' if col_den_data is not None else 'Failed'}")
    print(f"Dust temperature map: {'Loaded' if temp_data is not None else 'Failed'}")
    print(f"Filament skeleton: {'Loaded' if filament_mask is not None else 'Failed'}")
    print(f"Core catalog: {'Loaded' if catalog_stats is not None else 'Failed'}")

    if catalog_stats:
        print(f"\nTotal cores identified: {catalog_stats['n_cores']}")
        print(f"  - Prestellar cores: {catalog_stats['core_types']['prestellar']}")
        print(f"  - Protostellar cores: {catalog_stats['core_types']['protostellar']}")

    print("\n" + "="*70)
    print("Phase 1 complete. Ready for Phase 2: Core-Filament Association")
    print("="*70)

if __name__ == '__main__':
    main()
