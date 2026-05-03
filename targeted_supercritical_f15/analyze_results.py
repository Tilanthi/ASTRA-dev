#!/usr/bin/env python3
"""
Analysis script for Targeted Supercritical f=1.5 Campaign

Classifies simulation results (BEADING/TRANSITIONAL/RADIAL_COLLAPSE) and
extracts λ/W measurements where applicable.

Author: ASTRA Agent System
Date: 2026-05-03
"""

import h5py
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d


def load_snapshot(snapshot_path):
    """Load HDF5 snapshot and return density field."""
    with h5py.File(snapshot_path, 'r') as f:
        # Load density field (assuming field name 'density')
        density = f['dens'][:]  # Shape: (Nx, Ny, Nz)

        # Get metadata
        time = f['Attributes'].get('time', 0.0)
        time_myr = time * 0.5  # Convert to Myr (approximate)

    return density, time


def extract_longitudinal_profile(density):
    """
    Extract longitudinal density profile by averaging over y-z plane.

    Parameters
    ----------
    density : ndarray
        3D density field (Nx, Ny, Nz)

    Returns
    -------
    profile : ndarray
        1D longitudinal profile (averaged over y-z)
    """
    # Average over y and z dimensions
    profile = np.mean(density, axis=(1, 2))

    # Normalize to background (first 10% of domain)
    background = np.mean(profile[:int(len(profile)*0.1)])
    profile_normalized = profile / background

    return profile_normalized


def detect_peaks(profile, min_amplitude=0.05, min_distance=20):
    """
    Detect peaks in longitudinal density profile.

    Parameters
    ----------
    profile : ndarray
        Normalized longitudinal density profile
    min_amplitude : float
        Minimum peak amplitude (above background)
    min_distance : int
        Minimum distance between peaks (in grid cells)

    Returns
    -------
    peaks : dict
        Dictionary with peak information
    """
    # Smooth profile slightly to reduce noise
    profile_smooth = gaussian_filter1d(profile, sigma=2)

    # Detect peaks
    peak_indices, properties = find_peaks(
        profile_smooth,
        height=min_amplitude + 1.0,  # +1.0 for background
        distance=min_distance
    )

    # Extract peak amplitudes
    peak_amplitudes = profile_smooth[peak_indices] - 1.0

    # Estimate wavelength (average distance between peaks)
    if len(peak_indices) >= 2:
        peak_distances = np.diff(peak_indices)
        wavelength_cells = np.mean(peak_distances)
        wavelength_lambdaJ = wavelength_cells * (24.0 / 1536)  # Convert to λ_J units

        # Convert to physical units (assuming W = 0.1 pc)
        wavelength_pc = wavelength_lambdaJ * 0.1  # Need to scale by actual units
        lambda_W = wavelength_pc / 0.1
    else:
        wavelength_lambdaJ = None
        wavelength_pc = None
        lambda_W = None

    return {
        'peak_indices': peak_indices,
        'peak_amplitudes': peak_amplitudes,
        'n_peaks': len(peak_indices),
        'max_amplitude': np.max(peak_amplitudes) if len(peak_amplitudes) > 0 else 0.0,
        'wavelength_lambdaJ': wavelength_lambdaJ,
        'wavelength_pc': wavelength_pc,
        'lambda_W': lambda_W
    }


def classify_simulation(snapshot_dir):
    """
    Classify simulation based on final snapshot analysis.

    Parameters
    ----------
    snapshot_dir : str or Path
        Path to simulation output directory

    Returns
    -------
    classification : dict
        Classification results
    """
    snapshot_dir = Path(snapshot_dir)

    # Find final snapshot
    snapshots = sorted(snapshot_dir.glob("*.hdf5")) + \
                 sorted(snapshot_dir.glob("*.athdf"))

    if len(snapshots) == 0:
        return {
            'category': 'NO_DATA',
            'lambda_W': None,
            'beading_amplitude': 0.0,
            'peak_count': 0,
            'error': 'No snapshots found'
        }

    final_snapshot = snapshots[-1]

    # Load and analyze
    try:
        density, time = load_snapshot(final_snapshot)
        profile = extract_longitudinal_profile(density)
        peaks = detect_peaks(profile)

        # Classification logic
        max_amp = peaks['max_amplitude']

        if max_amp > 0.15:
            category = 'BEADING'
        elif 0.05 < max_amp <= 0.15:
            category = 'TRANSITIONAL'
        else:
            category = 'RADIAL_COLLAPSE'

        return {
            'category': category,
            'lambda_W': peaks['lambda_W'],
            'beading_amplitude': max_amp,
            'peak_count': peaks['n_peaks'],
            'time': time,
            'snapshot_file': str(final_snapshot)
        }

    except Exception as e:
        return {
            'category': 'ERROR',
            'lambda_W': None,
            'beading_amplitude': 0.0,
            'peak_count': 0,
            'error': str(e)
        }


def plot_profile(snapshot_dir, output_file):
    """Generate diagnostic plot of longitudinal density profile."""

    # Load data
    snapshot_dir = Path(snapshot_dir)
    snapshots = sorted(snapshot_dir.glob("*.hdf5")) + \
                 sorted(snapshot_dir.glob("*.athdf"))

    if len(snapshots) == 0:
        print(f"No snapshots found in {snapshot_dir}")
        return

    final_snapshot = snapshots[-1]
    density, time = load_snapshot(final_snapshot)
    profile = extract_longitudinal_profile(density)
    peaks = detect_peaks(profile)

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 4))

    # Position along filament (in λ_J units)
    x_lambdaJ = np.linspace(0, 24, len(profile))

    # Plot profile
    ax.plot(x_lambdaJ, profile, 'b-', linewidth=2, label='Density profile')

    # Mark peaks
    if peaks['n_peaks'] > 0:
        ax.plot(x_lambdaJ[peaks['peak_indices']],
                profile[peaks['peak_indices']],
                'ro', markersize=8, label=f'Peaks (n={peaks["n_peaks"]})')

    # Reference line
    ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='Background')
    ax.axhline(y=1.15, color='red', linestyle=':', alpha=0.5, label='BEADING threshold')

    # Labels
    ax.set_xlabel('Position along filament ($\\lambda_J$)', fontsize=12)
    ax.set_ylabel('Normalized density $\\rho/\\rho_0$', fontsize=12)
    ax.set_title(f'Final Snapshot (t = {time:.2f} $t_{{\\rm J}}$)\n'
                 f'Category: {classify_simulation(snapshot_dir)["category"]}',
                 fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0.8, 2.0)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Plot saved: {output_file}")


def main():
    """Analyze all simulation results."""

    print("="*70)
    print("TARGETED SUPERCRITICAL F=1.5 CAMPAIGN: Analysis")
    print("="*70)

    # Results directory
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    # Simulation directories
    sim_dirs = sorted(Path(".").glob("targeted_f15_extended_seed*"))

    if len(sim_dirs) == 0:
        print("ERROR: No simulation directories found!")
        print("Looking for directories matching pattern: targeted_f15_extended_seed*")
        return

    print(f"Found {len(sim_dirs)} simulation directories")
    print()

    # Analyze each simulation
    all_results = []

    for sim_dir in sim_dirs:
        print(f"Analyzing: {sim_dir.name}")

        # Classify
        classification = classify_simulation(sim_dir)
        classification['sim_directory'] = str(sim_dir)

        all_results.append(classification)

        print(f"  Category: {classification['category']}")
        print(f"  Beading amplitude: {classification['beading_amplitude']:.3f}")
        if classification['lambda_W'] is not None:
            print(f"  λ/W: {classification['lambda_W']:.3f}")
        print()

        # Generate plot
        plot_file = results_dir / f"{sim_dir.name}_profile.pdf"
        plot_path = sim_dir / "outputs"  # Look in outputs subdirectory
        if plot_path.exists():
            plot_profile(plot_path, plot_file)

    # Summary statistics
    categories = [r['category'] for r in all_results]
    beading_count = sum(1 for c in categories if c == 'BEADING')
    trans_count = sum(1 for c in categories if c == 'TRANSITIONAL')
    radial_count = sum(1 for c in categories if c == 'RADIAL_COLLAPSE')

    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total simulations: {len(all_results)}")
    print(f"  BEADING: {beading_count}")
    print(f"  TRANSITIONAL: {trans_count}")
    print(f"  RADIAL_COLLAPSE: {radial_count}")
    print()

    # Extract λ/W values for beading simulations
    lambda_W_values = [r['lambda_W'] for r in all_results
                       if r['category'] in ['BEADING', 'TRANSITIONAL']
                       and r['lambda_W'] is not None]

    if len(lambda_W_values) > 0:
        print(f"λ/W measurements: {lambda_W_values}")
        print(f"  Mean: {np.mean(lambda_W_values):.3f}")
        print(f"  Std: {np.std(lambda_W_values):.3f}")
        print()

    # Save results
    output = {
        'campaign': 'targeted_supercritical_f15',
        'analysis_date': '2026-05-03',
        'n_simulations': len(all_results),
        'summary': {
            'BEADING': beading_count,
            'TRANSITIONAL': trans_count,
            'RADIAL_COLLAPSE': radial_count
        },
        'simulations': all_results
    }

    output_file = results_dir / "classification_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to: {output_file}")
    print()
    print("Next steps:")
    print("1. Review classification results")
    print("2. Integrate findings into paper")
    print()


if __name__ == '__main__':
    main()
