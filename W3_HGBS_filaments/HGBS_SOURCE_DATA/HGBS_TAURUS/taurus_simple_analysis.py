#!/usr/bin/env python3
"""
HGBS Taurus (L1495) Discovery Science - Simplified Analysis

Author: ASTRA Discovery System
Date: 19 April 2026

Note: Taurus lacks a standard filament skeleton map, so this analysis
focuses on core catalog properties and available FITS data.
"""

import numpy as np
from astropy.io import fits
import os

# ============================================================================
# DATA PATHS
# ============================================================================
HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS'

COL_DEN_FILE = os.path.join(HGBS_DIR, 'HGBS_tauN3_hires_column_density_map.fits')
TEMP_FILE = os.path.join(HGBS_DIR, 'HGBS_taurus_L1495_dust_temperature_map.fits')
CAT_FILE = os.path.join(HGBS_DIR, 'HGBS_taurusL1495_derived_core_catalog.txt')

DISTANCE_PC = 140.0  # Distance to Taurus (pc)
M_LINE_CRIT = 16.0  # Msun/pc

print("="*70)
print("HGBS TAURUS (L1495) - DISCOVERY SCIENCE ANALYSIS")
print("="*70)

# ============================================================================
# LOAD AND PARSE CORE CATALOG
# ============================================================================
print("\nLoading core catalog...")
from parse_taurus_catalog import parse_taurus_catalog
cores = parse_taurus_catalog(CAT_FILE)
print(f"Loaded {len(cores)} cores")

# ============================================================================
# COLUMN DENSITY ANALYSIS
# ============================================================================
print("\n" + "="*70)
print("COLUMN DENSITY MAP ANALYSIS")
print("="*70)

try:
    with fits.open(COL_DEN_FILE) as hdul:
        col_data = hdul[0].data
        col_header = hdul[0].header

    valid_col = col_data[np.isfinite(col_data)]
    print(f"Shape: {col_data.shape}")
    print(f"Median N_H2: {np.median(valid_col)/1e21:.2f}e21 cm^-2")
    print(f"Range: {np.min(valid_col)/1e21:.2f} - {np.max(valid_col)/1e21:.2f} e21 cm^-2")
except Exception as e:
    print(f"Error loading column density: {e}")

# ============================================================================
# CORE POPULATION STATISTICS
# ============================================================================
print("\n" + "="*70)
print("CORE POPULATION ANALYSIS")
print("="*70)

# Count core types
type_counts = {}
for core in cores:
    ctype = core['type']
    type_counts[ctype] = type_counts.get(ctype, 0) + 1

print(f"\nCore type distribution:")
for ctype, count in type_counts.items():
    print(f"  {ctype}: {count} ({100*count/len(cores):.1f}%)")

# Mass statistics
masses = [c['mass'] for c in cores if c['mass'] > 0]
masses = np.array(masses)
print(f"\nCore mass statistics [Msun] (N={len(masses)}):")
print(f"  Range: {np.min(masses):.3f} - {np.max(masses):.3f}")
print(f"  Median: {np.median(masses):.3f}")
print(f"  Mean: {np.mean(masses):.3f}")
print(f"  Std: {np.std(masses):.3f}")

# Temperature statistics
temps = [c['temp'] for c in cores if c['temp'] > 0]
temps = np.array(temps)
print(f"\nCore temperature statistics [K] (N={len(temps)}):")
print(f"  Range: {np.min(temps):.1f} - {np.max(temps):.1f}")
print(f"  Median: {np.median(temps):.1f}")
print(f"  Mean: {np.mean(temps):.1f}")

# Peak column density
nh2_peaks = [c['nh2_peak'] for c in cores if c['nh2_peak'] > 0]
nh2_peaks = np.array(nh2_peaks)
print(f"\nPeak column density statistics [10^21 cm^-2] (N={len(nh2_peaks)}):")
print(f"  Range: {np.min(nh2_peaks):.2f} - {np.max(nh2_peaks):.2f}")
print(f"  Median: {np.median(nh2_peaks):.2f}")

# Bonnor-Ebert analysis
alpha_be_values = [c['alpha_be'] for c in cores if c['alpha_be'] is not None and c['alpha_be'] > 0]
alpha_be_values = np.array(alpha_be_values)
if len(alpha_be_values) > 0:
    print(f"\nBonnor-Ebert ratio statistics (N={len(alpha_be_values)}):")
    print(f"  Range: {np.min(alpha_be_values):.2f} - {np.max(alpha_be_values):.2f}")
    print(f"  Median: {np.median(alpha_be_values):.2f}")
    n_bound = sum(1 for a in alpha_be_values if a < 2.0)
    print(f"  Potentially bound (alpha_BE < 2): {n_bound}/{len(alpha_be_values)} ({100*n_bound/len(alpha_be_values):.1f}%)")

# ============================================================================
# MASSIVE CORE ANALYSIS
# ============================================================================
print("\n" + "="*70)
print("MASSIVE CORE ANALYSIS (M > 5 Msun)")
print("="*70)

massive_cores = [c for c in cores if c['mass'] > 5.0]
print(f"Found {len(massive_cores)} massive cores")

if len(massive_cores) > 0:
    for i, core in enumerate(massive_cores[:10]):  # Show first 10
        print(f"  {i+1}. {core['name']}: {core['mass']:.2f} Msun, T={core['temp']:.1f} K, type={core['type']}")
    if len(massive_cores) > 10:
        print(f"  ... and {len(massive_cores) - 10} more")

# ============================================================================
# M_LINE ANALYSIS (Simplified)
# ============================================================================
print("\n" + "="*70)
print("M_LINE ANALYSIS (Simplified)")
print("="*70)

# Use peak column density as proxy for M_line
# M_line ≈ N_H2 [10^21 cm^-2] × 2.5 for typical filament width
m_line_approx = nh2_peaks * 2.5

print(f"Approximate M_line at core locations:")
print(f"  Median: {np.median(m_line_approx):.2f} Msun/pc")
print(f"  Range: {np.min(m_line_approx):.2f} - {np.max(m_line_approx):.2f} Msun/pc")

above_crit = np.sum(m_line_approx > M_LINE_CRIT)
fraction = 100 * above_crit / len(m_line_approx)
print(f"\nAbove critical threshold ({M_LINE_CRIT} Msun/pc):")
print(f"  {above_crit} / {len(m_line_approx)} ({fraction:.1f}%)")

# By core type
print("\nBy core type:")
for ctype in ['starless', 'prestellar', 'protostellar']:
    type_cores = [c for c in cores if c['type'] == ctype and c['nh2_peak'] > 0]
    if type_cores:
        type_m_line = np.array([c['nh2_peak'] * 2.5 for c in type_cores])
        type_above = np.sum(type_m_line > M_LINE_CRIT)
        print(f"  {ctype}: median M_line = {np.median(type_m_line):.2f} Msun/pc, {type_above}/{len(type_m_line)} ({100*type_above/len(type_m_line):.1f}%) above critical")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*70)
print("TAURUS (L1495) ANALYSIS SUMMARY")
print("="*70)

results = {
    'distance_pc': DISTANCE_PC,
    'n_cores': len(cores),
    'n_starless': type_counts.get('starless', 0),
    'n_prestellar': type_counts.get('prestellar', 0),
    'n_protostellar': type_counts.get('protostellar', 0),
    'median_mass': float(np.median(masses)),
    'max_mass': float(np.max(masses)),
    'median_temp': float(np.median(temps)),
    'median_nh2': float(np.median(nh2_peaks)),
    'median_m_line': float(np.median(m_line_approx)),
    'fraction_above_critical': float(fraction),
    'n_massive': len(massive_cores)
}

print(f"\nTaurus Region Properties:")
print(f"  Distance: {results['distance_pc']} pc")
print(f"  Total cores: {results['n_cores']}")
print(f"  Core types: {results['n_starless']} starless, {results['n_prestellar']} prestellar, {results['n_protostellar']} protostellar")
print(f"  Mass range: {np.min(masses):.3f} - {results['max_mass']:.3f} Msun")
print(f"  Median M_line: {results['median_m_line']:.2f} Msun/pc")
print(f"  Above critical threshold: {results['fraction_above_critical']:.1f}%")
print(f"  Massive cores (M > 5 Msun): {results['n_massive']}")

# Save results
np.savez('taurus_results.npz', **results)
print(f"\nResults saved to: taurus_results.npz")

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print(f"\nKey Findings for Taurus L1495:")
print(f"  • {results['n_cores']} cores catalogued")
print(f"  • {results['n_prestellar']} prestellar cores ({100*results['n_prestellar']/results['n_cores']:.1f}%)")
print(f"  • Median mass: {results['median_mass']:.3f} Msun")
print(f"  • {results['n_massive']} massive cores (>5 Msun)")
print(f"  • {results['fraction_above_critical']:.1f}% of cores above M_line critical threshold")
print(f"\nNote: Filament skeleton map not available - limited to core catalog analysis")
