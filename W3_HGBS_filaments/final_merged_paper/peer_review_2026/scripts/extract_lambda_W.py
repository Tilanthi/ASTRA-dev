#!/usr/bin/env python3
"""
Extract λ/W measurements from Athena++ HDF5 output files.

This script analyzes filament fragmentation simulations to measure the characteristic
fragmentation spacing (λ) relative to the filament width (W).

Usage:
    python extract_lambda_W.py --simulation_dir <path> --output <output.json>

Output:
    JSON file containing λ/W measurements and diagnostic information
"""

import numpy as np
import h5py
import json
import argparse
from pathlib import Path
from scipy import ndimage
from scipy.signal import find_peaks
from scipy.fft import fft, fftfreq


def extract_longitudinal_profile(density, axis=0):
    """
    Extract longitudinal density profile by averaging over transverse dimensions.

    Parameters:
    -----------
    density : 3D array
        Density field from simulation
    axis : int
        Axis along which to extract profile (default: 0 = longitudinal)

    Returns:
    --------
    profile : 1D array
        Longitudinal density profile
    """
    # Average over transverse dimensions
    profile = np.mean(density, axis=(1, 2))
    return profile


def measure_pairwise_spacing(peaks):
    """
    Measure pairwise median spacing between peaks.

    Parameters:
    -----------
    peaks : array
        Peak positions

    Returns:
    --------
    spacing : float
        Median pairwise spacing
    """
    if len(peaks) < 2:
        return np.nan

    # Compute all pairwise distances
    distances = []
    for i in range(len(peaks)):
        for j in range(i+1, len(peaks)):
            distances.append(abs(peaks[j] - peaks[i]))

    return np.median(distances)


def fourier_spacing_analysis(profile, dx=1.0):
    """
    Analyze spacing using Fourier transform.

    Parameters:
    -----------
    profile : 1D array
        Longitudinal density profile
    dx : float
        Spatial resolution

    Returns:
    --------
    dominant_wavelength : float
        Dominant wavelength from Fourier analysis
    """
    # Remove mean
    profile_centered = profile - np.mean(profile)

    # FFT
    fft_result = fft(profile_centered)
    power_spectrum = np.abs(fft_result)**2

    # Frequencies
    freqs = fftfreq(len(profile), d=dx)

    # Dominant frequency (excluding zero frequency)
    valid_idx = np.where(freqs > 0)[0]
    dominant_freq_idx = np.argmax(power_spectrum[valid_idx]) + valid_idx[0]
    dominant_freq = freqs[dominant_freq_idx]

    if dominant_freq > 0:
        dominant_wavelength = 1.0 / dominant_freq
    else:
        dominant_wavelength = np.nan

    return dominant_wavelength


def extract_lambda_W(simulation_dir, snapshot_file):
    """
    Extract λ/W measurement from a single snapshot.

    Parameters:
    -----------
    simulation_dir : Path
        Directory containing simulation output
    snapshot_file : str
        Name of HDF5 snapshot file

    Returns:
    --------
    results : dict
        Dictionary containing λ/W measurements and diagnostics
    """
    snapshot_path = Path(simulation_dir) / snapshot_file

    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

    # Read HDF5 file
    with h5py.File(snapshot_path, 'r') as f:
        # Extract density field
        density = f['density'][:]

        # Get simulation parameters
        try:
            line_mass = f.attrs.get('line_mass', np.nan)
            plasma_beta = f.attrs.get('plasma_beta', np.nan)
            mach_number = f.attrs.get('mach_number', np.nan)
            time_tff = f.attrs.get('_time', np.nan)
        except:
            line_mass = np.nan
            plasma_beta = np.nan
            mach_number = np.nan
            time_tff = np.nan

    # Extract longitudinal profile
    profile = extract_longitudinal_profile(density, axis=0)

    # Normalize profile
    profile_norm = profile / np.mean(profile)

    # Find peaks
    peaks, properties = find_peaks(profile_norm, height=1.2, distance=5)

    if len(peaks) < 2:
        # Not enough peaks for reliable measurement
        return {
            'lambda_W_pairwise': np.nan,
            'lambda_W_fourier': np.nan,
            'n_peaks': len(peaks),
            'profile_mean': np.mean(profile_norm),
            'profile_std': np.std(profile_norm),
            'line_mass': line_mass,
            'plasma_beta': plasma_beta,
            'mach_number': mach_number,
            'time_tff': time_tff,
            'status': 'insufficient_peaks'
        }

    # Measure spacing using pairwise method
    spacing_pairwise = measure_pairwise_spacing(peaks)

    # Measure spacing using Fourier method
    spacing_fourier = fourier_spacing_analysis(profile)

    # Convert to physical units (assuming domain is 8 lambda_J)
    domain_length_lambda_J = 8.0
    dx_lambda_J = domain_length_lambda_J / len(profile)
    spacing_pairwise_lambda_J = spacing_pairwise * dx_lambda_J
    spacing_fourier_lambda_J = spacing_fourier * dx_lambda_J

    # Filament width (approximately 0.1 pc for HGBS, or ~0.3 lambda_J)
    W_lambda_J = 0.3

    # Compute lambda/W
    lambda_W_pairwise = spacing_pairwise_lambda_J / W_lambda_J
    lambda_W_fourier = spacing_fourier_lambda_J / W_lambda_J

    return {
        'lambda_W_pairwise': lambda_W_pairwise,
        'lambda_W_fourier': lambda_W_fourier,
        'lambda_W_mean': np.mean([lambda_W_pairwise, lambda_W_fourier]),
        'n_peaks': len(peaks),
        'peak_positions': peaks.tolist(),
        'profile_mean': np.mean(profile_norm),
        'profile_std': np.std(profile_norm),
        'line_mass': line_mass,
        'plasma_beta': plasma_beta,
        'mach_number': mach_number,
        'time_tff': time_tff,
        'status': 'success'
    }


def main():
    parser = argparse.ArgumentParser(description='Extract λ/W measurements from Athena++ snapshots')
    parser.add_argument('--simulation_dir', type=str, required=True,
                        help='Directory containing simulation output')
    parser.add_argument('--snapshot', type=str, default='final_snapshot.hdf5',
                        help='Name of snapshot file (default: final_snapshot.hdf5)')
    parser.add_argument('--output', type=str, required=True,
                        help='Output JSON file path')

    args = parser.parse_args()

    # Extract measurement
    results = extract_lambda_W(args.simulation_dir, args.snapshot)

    # Write to JSON
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results written to {args.output}")
    print(f"λ/W (pairwise): {results['lambda_W_pairwise']:.3f}")
    print(f"λ/W (Fourier): {results['lambda_W_fourier']:.3f}")


if __name__ == '__main__':
    main()
