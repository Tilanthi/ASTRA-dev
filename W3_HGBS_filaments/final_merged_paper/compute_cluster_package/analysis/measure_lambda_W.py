#!/usr/bin/env python3
"""
measure_lambda_W.py

Primary analysis script for measuring fragmentation wavelength
from Athena++ HDF5 outputs.

Usage:
    python measure_lambda_W.py <simulation_directory> [options]

Outputs:
    - lambda_W_summary.json  (primary result)
    - peak_evolution.png     (diagnostic plot)
    - density_profiles.txt   (for re-analysis)

Author: Peer Review Response
Date: 29 April 2026
"""

import h5py
import json
import numpy as np
from pathlib import Path
import argparse
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

def measure_lambda_W(density_field, axis=0, W_units=8, prominence_threshold=0.05):
    """
    Measure fragmentation wavelength from 3D density field.

    Parameters
    ----------
    density_field : 3D array
        Density field from Athena++ snapshot
    axis : int
        Filament axis (default: 0 = x)
    W_units : float
        Filament width in grid units (default: 8 for 128³)
    prominence_threshold : float
        Minimum peak prominence as fraction of max density

    Returns
    -------
    result : dict
        Dictionary with lambda_W measurement and quality flags
    """
    # Average over transverse plane
    if axis == 0:
        rho_1d = density_field.mean(axis=(1, 2))
    elif axis == 1:
        rho_1d = density_field.mean(axis=(0, 2))
    else:
        rho_1d = density_field.mean(axis=(0, 1))

    # Normalize to mean
    rho_mean = rho_1d.mean()
    rho_1d_norm = rho_1d / rho_mean

    # Find peaks
    peaks, properties = find_peaks(
        rho_1d_norm,
        prominence=prominence_threshold,
        distance=int(W_units * 0.5)  # minimum spacing between peaks
    )

    # Compute spacing
    if len(peaks) < 2:
        return {
            'lambda_W': np.nan,
            'lambda_W_std': np.nan,
            'n_peaks': len(peaks),
            'quality_flag': 'NO_PEAKS' if len(peaks) == 0 else 'FEW_PEAKS',
            'peaks': peaks.tolist(),
            'prominences': properties.get('prominences', []).tolist()
        }

    # Spacing in grid units
    spacings = np.diff(peaks)
    lambda_grid = spacings.mean()

    # Convert to lambda/W
    lambda_W = lambda_grid / W_units
    lambda_W_std = spacings.std() / W_units
    lambda_W_min = spacings.min() / W_units
    lambda_W_max = spacings.max() / W_units

    # Quality assessment
    if len(peaks) >= 3:
        quality_flag = 'GOOD'
    else:
        quality_flag = 'FEW_PEAKS'

    return {
        'lambda_W': float(lambda_W),
        'lambda_W_std': float(lambda_W_std),
        'lambda_W_min': float(lambda_W_min),
        'lambda_W_max': float(lambda_W_max),
        'n_peaks': int(len(peaks)),
        'quality_flag': quality_flag,
        'peaks': peaks.tolist(),
        'prominences': properties.get('prominences', []).tolist(),
        'rho_mean': float(rho_mean)
    }

def extract_parameters(sim_dir):
    """Extract simulation parameters from directory name or files."""
    sim_dir = Path(sim_dir)

    # Parse directory name
    # Expected format: CAMPAIGN_f{F}_beta{B}_mach{M}_res{R}_seed{S}
    params = {
        'f': 1.0,
        'beta': 1.0,
        'mach': 1.0,
        'resolution': 128,
        'seed': 1
    }

    # Try to extract from directory name
    name_parts = sim_dir.name.split('_')
    for part in name_parts:
        if part.startswith('f') and part[1:].replace('.','',1).isdigit():
            params['f'] = float(part[1:])
        elif part.startswith('beta') and part[4:].replace('.','',1).isdigit():
            params['beta'] = float(part[4:])
        elif part.startswith('mach') and part[4:].replace('.','',1).isdigit():
            params['mach'] = float(part[4:])
        elif part.startswith('res') and part[3:].isdigit():
            params['resolution'] = int(part[3:])
        elif part.startswith('seed') and part[4:].isdigit():
            params['seed'] = int(part[4:])

    return params

def process_simulation(sim_dir, W_units=8):
    """Process all snapshots from one simulation."""
    sim_dir = Path(sim_dir)

    if not sim_dir.exists():
        print(f"Error: Directory {sim_dir} does not exist")
        return None

    # Find all HDF5 snapshots
    hdf5_files = sorted(sim_dir.glob("**/*.hdf5")) | sorted(sim_dir.glob("**/*.h5"))
    if not hdf5_files:
        hdf5_files = sorted(sim_dir.glob("*.hdf5")) | sorted(sim_dir.glob("*.h5"))

    if not hdf5_files:
        print(f"Warning: No HDF5 files found in {sim_dir}")
        return None

    results = []
    for snapshot in hdf5_files:
        try:
            with h5py.File(snapshot, 'r') as f:
                if 'dens' in f:
                    rho = f['dens'][:]
                elif 'rho' in f:
                    rho = f['rho'][:]
                else:
                    print(f"Warning: No density field found in {snapshot}")
                    continue

            # Get time from filename or dataset
            time_str = snapshot.stem.split('.')[-2] if '.' in snapshot.stem else 'final'
            try:
                time = float(time_str)
            except ValueError:
                time = len(results) * 0.1  # fallback

            result = measure_lambda_W(rho, W_units=W_units)
            result['time'] = time
            result['snapshot'] = str(snapshot)
            results.append(result)

        except Exception as e:
            print(f"Error processing {snapshot}: {e}")
            continue

    if not results:
        print(f"Error: No valid snapshots processed from {sim_dir}")
        return None

    # Find final (converged) value
    final = max(results, key=lambda r: r['time'])

    summary = {
        'simulation_id': sim_dir.name,
        'final_lambda_W': final['lambda_W'],
        'final_quality_flag': final['quality_flag'],
        'n_snapshots': len(results),
        'evolution': results,
        'parameters': extract_parameters(sim_dir)
    }

    return summary

def save_summary(summary, sim_dir):
    """Save summary to JSON file."""
    sim_dir = Path(sim_dir)
    summary_file = sim_dir / 'lambda_W_summary.json'

    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"Saved summary to {summary_file}")
    return summary_file

def plot_evolution(summary, output_dir):
    """Plot evolution of lambda_W over time."""
    if not summary['evolution']:
        return

    times = [r['time'] for r in summary['evolution'] if not np.isnan(r['lambda_W'])]
    lambdas = [r['lambda_W'] for r in summary['evolution'] if not np.isnan(r['lambda_W'])]

    if not times:
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(times, lambdas, 'o-')
    ax.axhline(y=4.0, linestyle='--', color='gray', label='Classical')
    ax.axhline(y=2.8, linestyle=':', color='red', label='Observed')
    ax.set_xlabel('Time (t_J)')
    ax.set_ylabel('λ/W')
    ax.set_title(f"Fragmentation Wavelength Evolution\n{summary['simulation_id']}")
    ax.legend()
    ax.grid(True, alpha=0.3)

    output_file = Path(output_dir) / 'lambda_W_evolution.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved evolution plot to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Measure fragmentation wavelength from Athena++ outputs')
    parser.add_argument('sim_dir', help='Simulation directory')
    parser.add_argument('--W-units', type=float, default=8.0,
                       help='Filament width in grid units (default: 8.0 for 128³)')
    parser.add_argument('--prominence', type=float, default=0.05,
                       help='Peak prominence threshold (default: 0.05)')
    parser.add_argument('--plot', action='store_true',
                       help='Generate evolution plots')

    args = parser.parse_args()

    # Process simulation
    summary = process_simulation(args.sim_dir, W_units=args.W_units)

    if summary is None:
        print("Failed to process simulation")
        return 1

    # Save summary
    save_summary(summary, args.sim_dir)

    # Generate plot
    if args.plot:
        plot_evolution(summary, args.sim_dir)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Simulation: {summary['simulation_id']}")
    print(f"Parameters: f={summary['parameters']['f']}, "
          f"β={summary['parameters']['beta']}, "
          f"resolution={summary['parameters']['resolution']}")
    print(f"\nFinal λ/W: {summary['final_lambda_W']:.2f}")
    print(f"Quality flag: {summary['final_quality_flag']}")
    print(f"N peaks: {summary['evolution'][-1]['n_peaks']}")
    print(f"{'='*60}\n")

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
