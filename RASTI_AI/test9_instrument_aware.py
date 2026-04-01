#!/usr/bin/env python3
"""
Test 9: Instrument-Aware Analysis
Demonstrates ASTRA's capability to work with different telescope specifications,
understand instrumental effects, and combine data from multiple instruments.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import json
from pathlib import Path

print("="*70)
print("TEST 9: INSTRUMENT-AWARE ANALYSIS")
print("="*70)

# ============================================================================
# REAL TELESCOPE INSTRUMENT SPECIFICATIONS
# ============================================================================

print("\nLoading real instrument specifications...")

instruments = {
    'HST_ACS_WFC': {
        'name': 'Hubble Space Telescope ACS/WFC',
        'type': 'Space-based UV/Optical',
        'pixel_scale': 0.05,  # arcsec/pixel
        'psf_fwhm': 0.10,  # arcsec
        'wavelength_range': (2000, 11000),  # Angstrom
        'primary_filter': 'F606W',
        'filter_central': 6060,  # Angstrom
        'filter_width': 2300,  # Angstrom
        'quantum_efficiency': 0.4,
        'mirror_diameter': 2.4,  # meters
        'etendue': 0.068,  # m^2 arcsec^2 (collecting area × pixel area)
        'background': 0.1,  # electrons/sec (very low - space-based)
        'read_noise': 3.0,  # electrons
        'saturation': 80000,  # electrons
    },
    'JWST_NIRCam': {
        'name': 'James Webb Space Telescope NIRCam',
        'type': 'Space-based Near-Infrared',
        'pixel_scale': 0.031,  # arcsec/pixel
        'psf_fwhm': 0.07,  # arcsec (at 2 microns)
        'wavelength_range': (6000, 50000),  # Angstrom
        'primary_filter': 'F200W',
        'filter_central': 20000,  # Angstrom
        'filter_width': 4500,  # Angstrom
        'quantum_efficiency': 0.8,
        'mirror_diameter': 6.5,  # meters
        'etendue': 0.49,  # m^2 arcsec^2
        'background': 0.2,  # electrons/sec (low - space-based)
        'read_noise': 15.0,  # electrons (H2RG detector)
        'saturation': 60000,  # electrons
    },
    'VLT_HAWKI': {
        'name': 'VLT HAWK-I',
        'type': 'Ground-based Near-Infrared',
        'pixel_scale': 0.106,  # arcsec/pixel
        'psf_fwhm': 0.35,  # arcsec (typical seeing)
        'wavelength_range': (10000, 25000),  # Angstrom
        'primary_filter': 'Ks',
        'filter_central': 21600,  # Angstrom
        'filter_width': 3300,  # Angstrom
        'quantum_efficiency': 0.6,
        'mirror_diameter': 8.2,  # meters
        'etendue': 0.73,  # m^2 arcsec^2
        'background': 500,  # electrons/sec (high - ground-based IR)
        'read_noise': 25.0,  # electrons
        'saturation': 40000,  # electrons
    },
    'ALMA_Band6': {
        'name': 'ALMA Band 6',
        'type': 'Millimeter Interferometer',
        'pixel_scale': 0.02,  # arcsec (synthesized beam)
        'psf_fwhm': 0.04,  # arcsec (typical resolution)
        'wavelength_range': (1300, 1800),  # microns (1.3-1.8 mm)
        'primary_filter': 'Continuum',
        'filter_central': 1300,  # microns
        'filter_width': 800,  # microns (8 GHz bandwidth)
        'quantum_efficiency': 0.7,
        'mirror_diameter': 12.0,  # meters (effective per antenna)
        'n_antennas': 50,
        'etendue': 0.01,  # m^2 arcsec^2
        'background': 0.1,  # Jy/beam (system temperature)
        'read_noise': 0.001,  # Jy (rms sensitivity)
        'saturation': 10.0,  # Jy (dynamic range limit)
    },
    'Chandra_ACIS': {
        'name': 'Chandra X-ray Observatory ACIS',
        'type': 'Space-based X-ray',
        'pixel_scale': 0.492,  # arcsec/pixel
        'psf_fwhm': 0.5,  # arcsec (on-axis)
        'wavelength_range': (1, 100),  # Angstrom (0.1-10 keV)
        'primary_filter': 'Broad',
        'filter_central': 10,  # Angstrom (1 keV)
        'filter_width': 50,  # Angstrom (broad band)
        'quantum_efficiency': 0.9,
        'mirror_diameter': 1.2,  # meters (effective)
        'etendue': 0.004,  # m^2 arcsec^2
        'background': 0.001,  # counts/sec (very low)
        'read_noise': 0.1,  # counts
        'saturation': 0.1,  # counts/sec (pile-up limit)
    },
    'Gaia': {
        'name': 'Gaia Observatory',
        'type': 'Space-based Astrometry',
        'pixel_scale': 0.1,  # arcsec (CCD stripe)
        'psf_fwhm': 0.2,  # arcsec
        'wavelength_range': (3500, 10000),  # Angstrom (broad band)
        'primary_filter': 'G',
        'filter_central': 6300,  # Angstrom
        'filter_width': 4400,  # Angstrom
        'quantum_efficiency': 0.6,
        'mirror_diameter': 1.45,  # meters (two telescopes)
        'etendue': 0.019,  # m^2 arcsec^2
        'background': 0.01,  # electrons/sec
        'read_noise': 3.0,  # electrons
        'saturation': 100000,  # electrons
    }
}

print(f"\nLoaded {len(instruments)} instrument specifications:")
for key, inst in instruments.items():
    print(f"  {key}: {inst['name']}")

# ============================================================================
# SCIENTIFIC TARGETS
# ============================================================================

print("\nDefining scientific targets...")

targets = {
    'protostar': {
        'name': 'Class 0 Protostar',
        'size_arcsec': 1.0,  # 100 AU at 100 pc
        'surface_brightness': 20.0,  # mag/arcsec^2
        'peak_flux': 15.0,  # mag
        'variability_amp': 0.5,  # mag
        'spectral_index': -2.0,  # F_nu ~ nu^alpha
    },
    'galaxy': {
        'name': 'L* Spiral Galaxy',
        'size_arcsec': 30.0,  # ~10 kpc at 70 Mpc
        'surface_brightness': 23.0,  # mag/arcsec^2
        'peak_flux': 13.0,  # mag
        'variability_amp': 0.01,  # mag
        'spectral_index': -0.5,
    },
    'exoplanet_host': {
        'name': 'Exoplanet Host Star',
        'size_arcsec': 0.1,  # point source
        'surface_brightness': 10.0,  # mag/arcsec^2
        'peak_flux': 10.0,  # mag
        'variability_amp': 0.001,  # mag (transit depth)
        'spectral_index': 0.0,
    },
    'agn': {
        'name': 'Seyfert AGN',
        'size_arcsec': 0.5,  # nucleus
        'surface_brightness': 17.0,  # mag/arcsec^2
        'peak_flux': 14.0,  # mag
        'variability_amp': 1.0,  # mag
        'spectral_index': -1.0,
    },
    'disk': {
        'name': 'Protoplanetary Disk',
        'size_arcsec': 2.0,  # 200 AU at 100 pc
        'surface_brightness': 22.0,  # mag/arcsec^2
        'peak_flux': 16.0,  # mag
        'variability_amp': 0.1,  # mag
        'spectral_index': -3.0,
    }
}

print(f"\nDefined {len(targets)} target types:")
for key, tgt in targets.items():
    print(f"  {key}: {tgt['name']}")

# ============================================================================
# INSTRUMENT-TARGET COMPATIBILITY ANALYSIS
# ============================================================================

print("\n" + "="*70)
print("INSTRUMENT-TARGET COMPATIBILITY ANALYSIS")
print("="*70)

def calculate_snr(instrument, target, exposure_time=3600):
    """Calculate signal-to-noise ratio for a given instrument-target pair"""

    # Check wavelength compatibility
    tgt_min_lambda = 912e-3  # Lyman limit (912 Angstrom)
    tgt_max_lambda = 1e7  # 1 mm

    inst_min_lambda = instrument['wavelength_range'][0]
    inst_max_lambda = instrument['wavelength_range'][1]

    wavelength_ok = (inst_min_lambda <= tgt_max_lambda) and (inst_max_lambda >= tgt_min_lambda)

    if not wavelength_ok:
        return {
            'snr': 0,
            'compatible': False,
            'reason': 'Wavelength mismatch'
        }

    # Check resolution
    size_ok = target['size_arcsec'] >= instrument['psf_fwhm'] * 0.5

    # Calculate flux in instrument band
    # Simplified model based on filter transmission
    # Use a more realistic flux calculation
    flux_magnitude = target['peak_flux']
    # Zero point flux (approximately)
    flux_zero_point = 1e5  # counts/sec for mag=0
    flux_counts = flux_zero_point * 10**(-0.4 * flux_magnitude)

    # Calculate etendue-based flux
    collecting_area = np.pi * (instrument['mirror_diameter'] / 2)**2
    throughput = instrument['quantum_efficiency']

    # Signal rate (electrons/sec or counts/sec)
    signal_rate = flux_counts * (collecting_area / 10) * throughput

    # For extended sources, consider surface brightness
    if target['size_arcsec'] > 0:
        # Number of resolution elements
        n_pixels = (target['size_arcsec'] / instrument['pixel_scale'])**2
        signal_rate *= n_pixels

    # Background rate
    pixel_area = (instrument['pixel_scale'])**2
    background_rate = instrument['background'] * pixel_area * exposure_time

    # Noise calculation
    read_noise = instrument['read_noise']

    # Total noise (quadrature sum)
    noise = np.sqrt(signal_rate + background_rate + read_noise**2)

    # SNR
    snr = signal_rate / noise if noise > 0 else 0

    # Check for saturation
    saturation_ok = signal_rate < instrument['saturation']

    # Compatibility assessment
    compatible = wavelength_ok and snr > 5 and size_ok and saturation_ok

    reason = []
    if not wavelength_ok:
        reason.append('wavelength mismatch')
    if snr < 5:
        reason.append(f'low SNR ({snr:.1f})')
    if not size_ok:
        reason.append('insufficient resolution')
    if not saturation_ok:
        reason.append('saturation')

    return {
        'snr': float(snr),
        'compatible': compatible,
        'reason': ', '.join(reason) if reason else 'OK'
    }

def compare_instruments_for_target(target_name, instrument_names):
    """Compare all instruments for a specific target"""
    target = targets[target_name]
    results = {}

    for inst_name in instrument_names:
        inst = instruments[inst_name]
        result = calculate_snr(inst, target)
        results[inst_name] = result

    return results

# Analyze each target
compatibility_results = {}
for target_key in targets:
    print(f"\n{targets[target_key]['name']}:")
    results = compare_instruments_for_target(target_key, instruments.keys())

    compatible_instruments = []
    for inst_name, result in results.items():
        status = "✓" if result['compatible'] else "✗"
        print(f"  {status} {instruments[inst_name]['name']}: SNR = {result['snr']:.1f}")
        if result['compatible']:
            compatible_instruments.append(inst_name)

    compatibility_results[target_key] = {
        'target': targets[target_key],
        'results': results,
        'compatible': compatible_instruments
    }

# ============================================================================
# MULTI-INSTRUMENT DATA COMBINATION
# ============================================================================

print("\n" + "="*70)
print("MULTI-INSTRUMENT DATA COMBINATION")
print("="*70)

def estimate_combined_snr(instrument_list, target, exposure_time=3600):
    """Estimate combined SNR from multiple instruments"""

    total_signal = 0
    total_variance = 0

    valid_instruments = []
    for inst_name in instrument_list:
        inst = instruments[inst_name]
        result = calculate_snr(inst, target, exposure_time)

        if result['compatible']:
            # Weight by SNR
            snr = result['snr']
            total_signal += snr**2
            total_variance += 1
            valid_instruments.append(inst_name)

    if total_signal == 0:
        return {
            'combined_snr': 0,
            'instruments': [],
            'improvement': 0
        }

    combined_snr = np.sqrt(total_signal)
    single_snr = np.sqrt(total_signal / len(valid_instruments)) if valid_instruments else 0
    improvement = combined_snr / single_snr if single_snr > 0 else 0

    return {
        'combined_snr': float(combined_snr),
        'instruments': valid_instruments,
        'n_instruments': len(valid_instruments),
        'improvement': float(improvement)
    }

# Test combination for protostar (spanning UV to mm)
print("\nMulti-instrument analysis for Class 0 Protostar:")
target = targets['protostar']

all_sky_instruments = ['HST_ACS_WFC', 'JWST_NIRCam', 'VLT_HAWKI', 'ALMA_Band6']
combo_result = estimate_combined_snr(all_sky_instruments, target)

print(f"  Instruments: {', '.join([instruments[i]['name'] for i in combo_result['instruments']])}")
print(f"  Combined SNR: {combo_result['combined_snr']:.1f}")
print(f"  Improvement over single: {combo_result['improvement']:.2f}×")

# ============================================================================
# WAVELENGTH COVERAGE ANALYSIS
# ============================================================================

print("\n" + "="*70)
print("WAVELENGTH COVERAGE ANALYSIS")
print("="*70)

def get_wavelength_coverage(instrument_list):
    """Calculate total wavelength coverage"""
    min_wavelengths = []
    max_wavelengths = []

    for inst_name in instrument_list:
        inst = instruments[inst_name]
        min_wavelengths.append(inst['wavelength_range'][0])
        max_wavelengths.append(inst['wavelength_range'][1])

    return (min(min_wavelengths), max(max_wavelengths))

coverage = get_wavelength_coverage(list(instruments.keys()))
print(f"\nTotal wavelength coverage: {coverage[0]:.0f} - {coverage[1]:.0f} Angstrom")
print(f"  Range: {coverage[0]/1e3:.1f} nm - {coverage[1]/1e4:.1f} um - {coverage[1]/1e7:.2f} mm")

# ============================================================================
# INSTRUMENT SELECTION RECOMMENDATIONS
# ============================================================================

print("\n" + "="*70)
print("INSTRUMENT SELECTION RECOMMENDATIONS")
print("="*70)

def recommend_instruments(target_key, science_goal):
    """Recommend instruments based on target and science goal"""

    target = targets[target_key]
    recommendations = []

    for inst_name, inst in instruments.items():
        result = calculate_snr(inst, target)

        if not result['compatible']:
            continue

        score = result['snr']

        # Science goal modifiers
        if science_goal == 'resolution':
            if inst['psf_fwhm'] < target['size_arcsec']:
                score *= 2
        elif science_goal == 'sensitivity':
            score *= 1.5
        elif science_goal == 'wavelength':
            score *= 1.2

        recommendations.append({
            'instrument': inst_name,
            'score': score,
            'snr': result['snr'],
            'reason': result['reason']
        })

    # Sort by score
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    return recommendations[:3]  # Top 3

# Generate recommendations for each target
recommendations = {}
for target_key in targets:
    print(f"\n{targets[target_key]['name']}:")

    # General characterization
    recs = recommend_instruments(target_key, 'general')
    recommendations[target_key] = recs

    for i, rec in enumerate(recs, 1):
        inst_name = rec['instrument']
        print(f"  {i}. {instruments[inst_name]['name']}")
        print(f"     SNR: {rec['snr']:.1f}, Score: {rec['score']:.1f}")

# ============================================================================
# SAVE RESULTS
# ============================================================================

output = {
    'test_name': 'Instrument-Aware Analysis',
    'n_instruments': len(instruments),
    'n_targets': len(targets),
    'instruments': {
        key: {
            'name': inst['name'],
            'type': inst['type'],
            'wavelength_range_angstrom': inst['wavelength_range'],
            'psf_fwhm_arcsec': inst['psf_fwhm'],
            'mirror_diameter_m': inst['mirror_diameter']
        }
        for key, inst in instruments.items()
    },
    'compatibility': {
        target_key: {
            'target': targets[target_key]['name'],
            'compatible_instruments': compatibility_results[target_key]['compatible'],
            'n_compatible': len(compatibility_results[target_key]['compatible'])
        }
        for target_key in targets
    },
    'wavelength_coverage': {
        'min_angstrom': float(coverage[0]),
        'max_angstrom': float(coverage[1])
    },
    'multi_instrument_example': {
        'target': 'protostar',
        'combined_snr': combo_result['combined_snr'],
        'improvement_factor': combo_result['improvement']
    },
    'capabilities': [
        'Instrument specification knowledge',
        'Wavelength compatibility checking',
        'SNR estimation for different instruments',
        'Resolution requirement assessment',
        'Multi-instrument data combination',
        'Instrument selection recommendations',
        'Saturation and background consideration',
    ]
}

with open('test9_instrument_aware_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\nResults saved to test9_instrument_aware_results.json")

# ============================================================================
# CREATE FIGURE
# ============================================================================

print("\nGenerating instrument-aware analysis figure...")

fig = plt.figure(figsize=(20, 14))
gs = GridSpec(4, 4, figure=fig, hspace=0.4, wspace=0.4)

# Panel A: Instrument specifications comparison
ax1 = fig.add_subplot(gs[0, :2])
inst_names = list(instruments.keys())
mirror_sizes = [instruments[i]['mirror_diameter'] for i in inst_names]
psf_sizes = [instruments[i]['psf_fwhm'] for i in inst_names]

colors = ['steelblue', 'darkgreen', 'orange', 'purple', 'crimson', 'gold']
ax2_twin = ax1.twinx()

bars1 = ax1.bar([i - 0.2 for i in range(len(inst_names))], mirror_sizes,
                width=0.4, color='steelblue', alpha=0.7, label='Mirror Dia. (m)')
bars2 = ax2_twin.bar([i + 0.2 for i in range(len(inst_names))], psf_sizes,
                     width=0.4, color='coral', alpha=0.7, label='PSF FWHM (")')

ax1.set_xlabel('Instrument')
ax1.set_ylabel('Mirror Diameter (m)', color='steelblue')
ax2_twin.set_ylabel('PSF FWHM (arcsec)', color='coral')
ax1.set_title('A: Instrument Specifications')
ax1.set_xticks(range(len(inst_names)))
ax1.set_xticklabels([instruments[i]['name'].split()[0] for i in inst_names],
                     rotation=45, ha='right', fontsize=8)
ax1.tick_params(axis='y', labelcolor='steelblue')
ax2_twin.tick_params(axis='y', labelcolor='coral')
ax1.grid(True, alpha=0.3, axis='y')

# Panel B: Wavelength coverage
ax2 = fig.add_subplot(gs[0, 2:])
for i, (key, inst) in enumerate(instruments.items()):
    wl_range = inst['wavelength_range']
    ax2.barh(i, wl_range[1] - wl_range[0], left=wl_range[0],
             height=0.6, color=colors[i], alpha=0.7)
    ax2.text(np.mean(wl_range), i, inst['primary_filter'],
             ha='center', va='center', fontsize=7, fontweight='bold')

ax2.set_yticks(range(len(instruments)))
ax2.set_yticklabels([inst['name'].split()[0] for inst in instruments.values()],
                     fontsize=8)
ax2.set_xlabel('Wavelength (Angstrom)')
ax2.set_title('B: Wavelength Coverage')
ax2.set_xscale('log')
ax2.grid(True, alpha=0.3, axis='x')

# Panel C: SNR comparison across targets
ax3 = fig.add_subplot(gs[1, :2])
snr_matrix = np.zeros((len(targets), len(instruments)))

for i, (tgt_key, tgt) in enumerate(targets.items()):
    for j, (inst_key, inst) in enumerate(instruments.items()):
        result = calculate_snr(inst, tgt)
        snr_matrix[i, j] = result['snr'] if result['compatible'] else 0

im = ax3.imshow(snr_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=50)
ax3.set_xticks(range(len(instruments)))
ax3.set_yticks(range(len(targets)))
ax3.set_xticklabels([inst['name'].split()[0] for inst in instruments.values()],
                     rotation=45, ha='right', fontsize=8)
ax3.set_yticklabels([tgt['name'] for tgt in targets.values()], fontsize=8)
ax3.set_title('C: SNR Matrix (Target × Instrument)')
plt.colorbar(im, ax=ax3, label='SNR')

# Panel D: Resolution vs Wavelength
ax4 = fig.add_subplot(gs[1, 2:])
for key, inst in instruments.items():
    wl_center = inst['filter_central']
    psf = inst['psf_fwhm']
    ax4.scatter(wl_center, psf, s=200, alpha=0.7, color=colors[list(instruments.keys()).index(key)])
    ax4.annotate(inst['name'].split()[0], (wl_center, psf),
                fontsize=7, ha='center', va='bottom')

ax4.set_xlabel('Central Wavelength (Angstrom)')
ax4.set_ylabel('PSF FWHM (arcsec)')
ax4.set_title('D: Resolution vs Wavelength')
ax4.set_xscale('log')
ax4.set_yscale('log')
ax4.grid(True, alpha=0.3)

# Panel E: Sensitivity comparison (etendue)
ax5 = fig.add_subplot(gs[2, :2])
etendue_values = [instruments[i]['etendue'] for i in inst_names]
sorted_indices = np.argsort(etendue_values)[::-1]

for idx in sorted_indices:
    ax5.bar(idx, etendue_values[idx], color=colors[idx], alpha=0.7)
    ax5.text(idx, etendue_values[idx], f"{etendue_values[idx]:.3f}",
            ha='center', va='bottom', fontsize=7)

ax5.set_xticks(range(len(inst_names)))
ax5.set_xticklabels([instruments[inst_names[i]]['name'].split()[0] for i in range(len(inst_names))],
                     rotation=45, ha='right', fontsize=8)
ax5.set_ylabel('Etendue (m$^2$ arcsec$^2$)')
ax5.set_title('E: Sensitivity (Etendue)')
ax5.grid(True, alpha=0.3, axis='y')

# Panel F: Multi-instrument combination example
ax6 = fig.add_subplot(gs[2, 2:])
combo_insts = combo_result['instruments']
snr_values = [compatibility_results['protostar']['results'][i]['snr'] for i in combo_insts]

# Combined SNR
colors2 = ['steelblue', 'darkgreen', 'orange', 'purple']
bars = ax6.bar(range(len(combo_insts)), snr_values, color=colors2[:len(combo_insts)], alpha=0.7)
ax6.axhline(combo_result['combined_snr'], color='red', linestyle='--',
           label=f'Combined: {combo_result["combined_snr"]:.1f}')

ax6.set_xticks(range(len(combo_insts)))
ax6.set_xticklabels([instruments[i]['name'].split()[0] for i in combo_insts],
                     rotation=45, ha='right', fontsize=8)
ax6.set_ylabel('SNR')
ax6.set_title(f'F: Multi-Instrument Combination (Protostar)')
ax6.legend()
ax6.grid(True, alpha=0.3, axis='y')

# Panel G: Instrument recommendations
ax7 = fig.add_subplot(gs[3, :2])
ax7.axis('off')

rec_text = "INSTRUMENT RECOMMENDATIONS\n\n"
for target_key, recs in recommendations.items():
    rec_text += f"{targets[target_key]['name']}:\n"
    for i, rec in enumerate(recs[:3], 1):
        inst = instruments[rec['instrument']]
        rec_text += f"  {i}. {inst['name']}\n"
    rec_text += "\n"

ax7.text(0.05, 0.95, rec_text, transform=ax7.transAxes,
         verticalalignment='top', fontsize=8, family='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Panel H: ASTRA capabilities summary
ax8 = fig.add_subplot(gs[3, 2:])
ax8.axis('off')

capability_text = """
ASTRA INSTRUMENT-AWARE CAPABILITIES

Specification Knowledge
  • Real telescope parameters
  • Filter properties
  • Detector characteristics

Compatibility Analysis
  • Wavelength matching
  • Resolution requirements
  • SNR estimation

Data Combination
  • Multi-instrument fusion
  • Wavelength coverage
  • Sensitivity optimization

Recommendations
  • Science goal driven
  • Constraint aware
  • Multi-wavelength strategy

vs. LLMs: "Use a big telescope"
vs. ML: Single instrument only
"""

ax8.text(0.05, 0.95, capability_text, transform=ax8.transAxes,
         verticalalignment='top', fontsize=9,
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
         family='monospace')

plt.suptitle('Test 9: Instrument-Aware Analysis',
             fontsize=16, fontweight='bold')

plt.savefig('test9_instrument_aware_analysis.png', dpi=150, bbox_inches='tight')
print("Figure saved to test9_instrument_aware_analysis.png")
plt.close()

print("\n" + "="*70)
print("TEST 9 COMPLETE: Instrument-Aware Analysis")
print("="*70)
print(f"\nAnalyzed {len(instruments)} instruments and {len(targets)} targets")
print(f"Wavelength coverage: {coverage[0]/1e3:.1f} nm - {coverage[1]/1e4:.1f} μm")
print(f"\nCompatible instrument pairs:")
for target_key, result in compatibility_results.items():
    print(f"  {targets[target_key]['name']}: {len(result['compatible'])} instruments")
