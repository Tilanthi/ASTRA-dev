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
HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA/HGBS_AQUILA'
PERSISTENCE_THRESHOLD = 50

# FITS files
FITS_FILES = {
    '70_micron': os.path.join(HGBS_DIR, 'HGBS_Aquila_070.fits'),
    '160_micron': os.path.join(HGBS_DIR, 'HGBS_Aquila_160.fits'),
    '250_micron': os.path.join(HGBS_DIR, 'HGBS_Aquila_250.fits'),
    '350_micron': os.path.join(HGBS_DIR, 'HGBS_Aquila_350.fits'),
    '500_micron': os.path.join(HGBS_DIR, 'HGBS_Aquila_500.fits'),
    'column_density': os.path.join(HGBS_DIR, 'HGBS_aquilaM2_hires_column_density_map.fits'),
    'dust_temperature': os.path.join(HGBS_DIR, 'HGBS_aquilaM2_dust_temperature_map.fits'),  # Using hires for temp
    'column_density_hires': os.path.join(HGBS_DIR, 'HGBS_aquilaM2_dust_temperature_map.fits'),
    'skeleton': os.path.join(HGBS_DIR, 'HGBS_orionB_skeleton_map.fits'),
}

# Catalog files
CAT_FILES = {
    'derived': os.path.join(HGBS_DIR, 'HGBS_orionb_derived_core_catalog.txt'),
    'observed': os.path.join(HGBS_DIR, 'HGBS_orionB_observed_core_catalog.txt'),
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

def load_catalog_with_encoding(filename, encoding='latin-1'):
    """Load catalog with specified encoding to handle special characters."""
    data = []
    with open(filename, 'r', encoding=encoding) as f:
        in_data = False
        for line in f:
            if '---' in line and 'runNO' in line:
                in_data = True
                continue
            if in_data:
                line = line.strip()
                if line and not line.startswith('|'):
                    # Parse the data
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

    # Estimate cloud mass (simplified)
    # Area calculation from header
    try:
        cdelt1 = header.get('CDELT1', -1.0/3600)  # deg/pixel
        cdelt2 = header.get('CDELT2', -1.0/3600)  # deg/pixel
        pixel_area_sr = abs(cdelt1 * cdelt2) * (np.pi/180)**2  # sr

        # Distance to Aquila (~260 pc)
        dist_pc = 260

        # Physical size per pixel
        pixel_size_pc = dist_pc * np.sqrt(pixel_area_sr) * 206265  # pc

        # Total mass (simplified, using mean column density)
        mean_n_h2 = np.nanmean(valid_data)  # cm^-2
        m_h2 = 1.67e-24 * 2.8  # g (mean molecular mass)
        total_mass = mean_n_h2 * pixel_area_sr * (dist_pc * 3.086e18)**2 * m_h2 / 1.989e33  # Msun

        print(f"\nCloud mass estimate (simplified): {total_mass:.0f} Msun")
    except:
        pass

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

    # Temperature distribution
    print(f"\nTemperature percentiles:")
    for p in [10, 25, 50, 75, 90, 95, 99]:
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
        print(f"Median skeleton value: {np.median(skeleton_values):.2f}")

    # Estimate filament length (simplified)
    # Each skeleton pixel is roughly one beam width (18.2")
    # At 260 pc, 18.2" = 0.023 pc
    beam_size_pc = 260 * 0.023 / 206265
    total_length = filament_pixels * beam_size_pc
    print(f"\nEstimated total filament length: {total_length:.1f} pc")

    return filament_mask

def analyze_derived_catalog(data_list):
    """Analyze derived core catalog."""
    print("\n" + "="*60)
    print("DERIVED CORE CATALOG ANALYSIS")
    print("="*60)

    n_cores = len(data_list)
    print(f"Number of cores: {n_cores}")

    # Parse core properties from catalog data
    # Based on HGBS catalog format:
    # Columns: runNO, Name, RA, Dec, R_core(deconv), R_core(obs), M_core, M_err,
    #          T_dust, T_err, Nh2_peak, Nh2_ave(obs), Nh2_ave(deconv),
    #          nh2_peak, nh2_ave(obs), nh2_ave(deconv), alpha_BE, Type, Comments

    core_types = {'starless': 0, 'prestellar': 0, 'protostellar': 0, 'unknown': 0}
    masses = []
    temps = []
    sizes = []
    nh2_peaks = []
    alpha_be = []

    for parts in data_list:
        if len(parts) >= 19:
            try:
                # Core type (column 19, index 18)
                type_str = ' '.join(parts[18:])
                if 'starless' in type_str.lower() and 'prestellar' not in type_str.lower():
                    core_types['starless'] += 1
                elif 'prestellar' in type_str.lower():
                    core_types['prestellar'] += 1
                elif 'protostellar' in type_str.lower():
                    core_types['protostellar'] += 1
                else:
                    core_types['unknown'] += 1

                # Mass (column 7, index 6) - first value
                if len(parts) > 6:
                    try:
                        m = float(parts[6])
                        if m > 0 and m < 100:  # Filter unreasonable values
                            masses.append(m)
                    except:
                        pass

                # Temperature (column 9, index 8) - first value
                if len(parts) > 8:
                    try:
                        t = float(parts[8])
                        if t > 0 and t < 50:
                            temps.append(t)
                    except:
                        pass

                # Size (column 5, index 4) - deconvolved radius in pc
                if len(parts) > 4:
                    try:
                        s = float(parts[4])
                        if s > 0 and s < 1:
                            sizes.append(s)
                    except:
                        pass

                # Peak column density (column 11, index 10)
                if len(parts) > 10:
                    try:
                        n = float(parts[10])
                        if n > 0:
                            nh2_peaks.append(n)
                    except:
                        pass

                # Bonnor-Ebert ratio (column 18, index 17)
                if len(parts) > 17:
                    try:
                        a = float(parts[17])
                        if a > 0 and a < 100:
                            alpha_be.append(a)
                    except:
                        pass
            except Exception as e:
                continue

    print(f"\nCore type distribution:")
    for ctype, count in core_types.items():
        if count > 0:
            print(f"  {ctype}: {count} ({100*count/n_cores:.1f}%)")

    if masses:
        masses = np.array(masses)
        print(f"\nCore mass statistics [Msun] (N={len(masses)}):")
        print(f"  Range: {np.min(masses):.3f} - {np.max(masses):.3f}")
        print(f"  Median: {np.median(masses):.3f}")
        print(f"  Mean: {np.mean(masses):.3f}")
        print(f"  Std: {np.std(masses):.3f}")

        # Mass distribution percentiles
        print(f"  Percentiles:")
        for p in [10, 25, 50, 75, 90, 95]:
            print(f"    {p}%: {np.percentile(masses, p):.3f} Msun")

    if temps:
        temps = np.array(temps)
        print(f"\nCore temperature statistics [K] (N={len(temps)}):")
        print(f"  Range: {np.min(temps):.2f} - {np.max(temps):.2f}")
        print(f"  Median: {np.median(temps):.2f}")
        print(f"  Mean: {np.mean(temps):.2f}")
        print(f"  Std: {np.std(temps):.2f}")

    if sizes:
        sizes = np.array(sizes)
        print(f"\nCore size statistics [pc] (N={len(sizes)}):")
        print(f"  Range: {np.min(sizes):.4f} - {np.max(sizes):.4f}")
        print(f"  Median: {np.median(sizes):.4f}")
        print(f"  Mean: {np.mean(sizes):.4f}")

    if nh2_peaks:
        nh2_peaks = np.array(nh2_peaks)
        print(f"\nPeak column density statistics [10^21 cm^-2] (N={len(nh2_peaks)}):")
        print(f"  Range: {np.min(nh2_peaks):.2f} - {np.max(nh2_peaks):.2f}")
        print(f"  Median: {np.median(nh2_peaks):.2f}")

    if alpha_be:
        alpha_be = np.array(alpha_be)
        print(f"\nBonnor-Ebert ratio statistics (N={len(alpha_be)}):")
        print(f"  Range: {np.min(alpha_be):.3f} - {np.max(alpha_be):.3f}")
        print(f"  Median: {np.median(alpha_be):.3f}")
        # Count potentially bound cores
        n_bound = sum(1 for a in alpha_be if a < 2.0)
        print(f"  Potentially bound (alpha_BE < 2): {n_bound}/{len(alpha_be)} ({100*n_bound/len(alpha_be):.1f}%)")

    return {
        'n_cores': n_cores,
        'core_types': core_types,
        'masses': masses if masses else [],
        'temps': temps if temps else [],
        'sizes': sizes if sizes else [],
        'nh2_peaks': nh2_peaks if nh2_peaks else [],
        'alpha_be': alpha_be if alpha_be else []
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
        import traceback
        traceback.print_exc()
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
        # Import the Aquila catalog parser
        import parse_orionb_catalog
        cores = parse_orionb_catalog.parse_orionb_catalog(CAT_FILES['derived'])

        # Analyze cores
        print(f"\nCore type distribution:")
        types = {}
        for core in cores:
            ctype = core.get('type', 'unknown')
            types[ctype] = types.get(ctype, 0) + 1

        for ctype, count in types.items():
            print(f"  {ctype}: {count} ({100*count/len(cores):.1f}%)")

        # Collect statistics
        masses = [c['mass'] for c in cores if 'mass' in c]
        temps = [c['temp'] for c in cores if 'temp' in c]
        nh2_peaks = [c['nh2_peak'] for c in cores if 'nh2_peak' in c]
        alpha_be = [c['alpha_be'] for c in cores if 'alpha_be' in c and c['alpha_be'] is not None]

        print(f"\nCore mass statistics [Msun] (N={len(masses)}):")
        print(f"  Range: {np.min(masses):.3f} - {np.max(masses):.3f}")
        print(f"  Median: {np.median(masses):.3f}")
        print(f"  Mean: {np.mean(masses):.3f}")

        print(f"\nCore temperature statistics [K] (N={len(temps)}):")
        print(f"  Range: {np.min(temps):.1f} - {np.max(temps):.1f}")
        print(f"  Median: {np.median(temps):.1f}")
        print(f"  Mean: {np.mean(temps):.1f}")

        if nh2_peaks:
            print(f"\nPeak column density statistics [10^21 cm^-2] (N={len(nh2_peaks)}):")
            print(f"  Range: {np.min(nh2_peaks):.1f} - {np.max(nh2_peaks):.1f}")
            print(f"  Median: {np.median(nh2_peaks):.1f}")

        if alpha_be:
            print(f"\nBonnor-Ebert ratio statistics (N={len(alpha_be)}):")
            print(f"  Range: {np.min(alpha_be):.2f} - {np.max(alpha_be):.2f}")
            print(f"  Median: {np.median(alpha_be):.2f}")

        # Save cores for next phases
        np.savez('phase2_results.npz', cores=cores)
        print(f"\nSaved {len(cores)} cores to phase2_results.npz")

    except Exception as e:
        print(f"Error loading core catalog: {e}")
        import traceback
        traceback.print_exc()
        cores = []
        types = {}

    # Summary
    print("\n" + "="*70)
    print("PHASE 1 SUMMARY - DATA INVENTORY")
    print("="*70)
    print(f"Column density map: {'Loaded' if col_den_data is not None else 'Failed'}")
    print(f"  - Shape: {col_den_data.shape if col_den_data is not None else 'N/A'}")
    print(f"  - Median N_H2: {np.median(col_valid)/1e21:.2f}e21 cm^-2" if col_den_data is not None else "")
    print(f"Dust temperature map: {'Loaded' if temp_data is not None else 'Failed'}")
    print(f"  - Shape: {temp_data.shape if temp_data is not None else 'N/A'}")
    print(f"  - Median T_dust: {np.median(temp_valid):.2f} K" if temp_data is not None else "")
    print(f"Filament skeleton: {'Loaded' if filament_mask is not None else 'Failed'}")
    print(f"  - Filament pixels: {np.sum(filament_mask) if filament_mask is not None else 'N/A'}")
    print(f"Core catalog: {'Loaded' if len(cores) > 0 else 'Failed'}")

    if len(cores) > 0:
        print(f"  - Total cores: {len(cores)}")
        print(f"  - Starless cores: {types.get('starless', 0)}")
        print(f"  - Prestellar cores: {types.get('prestellar', 0)}")
        print(f"  - Protostellar cores: {types.get('protostellar', 0)}")
        print(f"  - Mass range: {np.min(masses):.2f} - {np.max(masses):.2f} Msun")

    print("\n" + "="*70)
    print("DISCOVERY OPPORTUNITIES IDENTIFIED")
    print("="*70)
    print("1. Core-filament relationship: Map cores onto filament skeleton")
    print("2. Fragmentation analysis: Measure core spacing along filaments")
    print("3. Temperature-density evolution: Track core evolution")
    print("4. Local filament properties: Correlate core mass with local M_line")
    print("5. SED analysis: Two-parameter (T, beta) fitting")

    print("\n" + "="*70)
    print("Phase 1 complete. Ready for Phase 2: Core-Filament Association")
    print("="*70)

if __name__ == '__main__':
    main()
