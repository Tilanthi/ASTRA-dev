#!/usr/bin/env python3
"""
Analysis Script for Rigid Cylinder Campaign
==============================================

Extracts λ/W measurements from completed rigid cylinder simulations
and produces plots and statistics for the paper.

Usage:
    python analyze_rigid_cylinder.py /path/to/rigid_cylinder_outputs

Author: G. J. White
Date: June 2026
"""

import sys
import json
import glob
import numpy as np
import h5py
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def extract_lambda_W(hdf5_file, sim_params):
    """Extract λ/W measurement from HDF5 output."""

    try:
        with h5py.File(hdf5_file, 'r') as f:
            # Get last density snapshot
            if 'density' in f:
                rho_grp = f['density']
                rho = rho_grp[-1]  # Last time step
            else:
                # Try alternative path
                rho = f['rho'][-1]

            # Squeeze if needed
            if rho.ndim > 2:
                rho = rho.squeeze()

            # Handle different shapes
            if rho.ndim == 3:
                # (nx, ny, nz)
                # Average over y and z to get axial profile
                rho_axial = np.mean(rho, axis=(1, 2))
            elif rho.ndim == 2:
                # (nx, ny) - assume this is already axial profile
                rho_axial = np.mean(rho, axis=1)
            else:
                rho_axial = rho.flatten()

        # Normalize
        rho_mean = np.mean(rho_axial)
        if rho_mean > 0:
            rho_norm = rho_axial / rho_mean
        else:
            return None

        # Find peaks (cores)
        nx = len(rho_axial)
        min_spacing = max(nx // 64, 5)
        peaks, properties = find_peaks(
            rho_norm,
            distance=min_spacing,
            prominence=0.1,
            width=5
        )

        # Classification
        n_peaks = len(peaks)

        if n_peaks < 2:
            return {
                'n_peaks': n_peaks,
                'lambda_W': None,
                'classification': 'NO_FRAGMENTATION' if n_peaks < 2 else 'SINGLE_PEAK',
                'axial_profile': rho_norm.tolist() if n_peaks > 0 else None
            }

        # Calculate spacings
        dx = sim_params['L_x'] / nx
        spacings = np.diff(peaks) * dx

        # Median spacing
        lambda_median = np.median(spacings)

        # Convert to λ/W
        W_cyl = sim_params['cylinder_radius']
        lambda_by_W = lambda_median / W_cyl

        return {
            'n_peaks': n_peaks,
            'lambda_W': lambda_by_W,
            'spacings': spacings.tolist(),
            'classification': 'FRAGMENTED',
            'axial_profile': rho_norm.tolist(),
            'peak_locations': peaks.tolist()
        }

    except Exception as e:
        return {
            'error': str(e),
            'classification': 'ERROR',
            'lambda_W': None
        }

def analyze_campaign(output_dir):
    """Analyze all simulations in output directory."""

    print(f"Analyzing rigid cylinder campaign in: {output_dir}")

    # Find all result directories
    sim_dirs = sorted([d for d in Path(output_dir).iterdir() if d.is_dir()])

    if not sim_dirs:
        print("No simulation directories found!")
        return {}

    results = []

    for sim_dir in sim_dirs:
        sim_id = sim_dir.name

        # Parse simulation parameters from directory name
        # Expected format: rigid_f{f}_beta{beta}_m{mach}_theta{theta}_seed{seed}
        try:
            parts = sim_id.split('_')

            sim_params = {
                'L_x': 16.0,  # Default
                'cylinder_radius': 1.0,
            }

            for part in parts:
                if part.startswith('f'):
                    sim_params['f'] = float(part[1:])
                elif part.startswith('beta'):
                    sim_params['beta'] = float(part[1:])
                elif part.startswith('m'):
                    sim_params['mach'] = float(part[1:])
                elif part.startswith('theta'):
                    sim_params['theta'] = float(part[1:])
                elif part.startswith('seed'):
                    sim_params['seed'] = int(part[1:])
        except:
            print(f"  Warning: Could not parse parameters from {sim_id}")
            continue

        # Find HDF5 files
        hdf5_files = list(sim_dir.glob("outputs/*.hdf5"))

        if not hdf5_files:
            print(f"  No HDF5 files found in {sim_dir}")
            continue

        # Analyze the last HDF5 file
        hdf5_file = sorted(hdf5_files)[-1]

        analysis = extract_lambda_W(hdf5_file, sim_params)

        results.append({
            'sim_id': sim_id,
            'output_dir': str(sim_dir),
            'hdf5_file': str(hdf5_file),
            'parameters': sim_params,
            'analysis': analysis,
            'classification': analysis.get('classification', 'UNKNOWN'),
            'lambda_W': analysis.get('lambda_W'),
            'n_peaks': analysis.get('n_peaks', 0),
        })

        status = "✓" if analysis.get('lambda_W') else "✗"
        print(f"  {status} {sim_id}: λ/W = {analysis.get('lambda_W', 'N/A'):.2f}" if analysis.get('lambda_W') else f"  {status} {sim_id}: {analysis.get('classification', 'UNKNOWN')}")

    # Save results
    analysis_file = Path(output_dir) / "rigid_cylinder_analysis.json"
    with open(analysis_file, 'w') as f:
        json.dump({
            'output_dir': str(output_dir),
            'total_analyzed': len(results),
            'results': results,
            'timestamp': str(np.datetime64('now')),
        }, f, indent=2)

    print(f"\nAnalysis saved to: {analysis_file}")

    # Generate plots
    plot_results(results, output_dir)

    return results

def plot_results(results, output_dir):
    """Generate plots for paper."""

    # Extract fragmented results with λ/W measurements
    frag_data = [(r['parameters']['f'], r['lambda_W'])
                  for r in results if r['classification'] == 'FRAGMENTED' and r['lambda_W'] is not None]

    if not frag_data:
        print("No fragmented simulations with λ/W measurements found!")
        return

    f_vals = [d[0] for d in frag_data]
    lambda_W_vals = [d[1] for d in frag_data]

    # Sort by f
    sorted_data = sorted(zip(f_vals, lambda_W_vals))
    f_sorted = [d[0] for d in sorted_data]
    lambda_sorted = [d[1] for d in sorted_data]

    # Create plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Plot 1: λ/W vs f
    ax1.scatter(f_sorted, lambda_sorted, c='blue', s=100, edgecolors='black', alpha=0.7)
    ax1.set_xlabel('Line-mass fraction f', fontsize=12)
    ax1.set_ylabel('λ/W', fontsize=12)
    ax1.set_title('Rigid Cylinder: Fragmentation Wavelength vs. Line-mass', fontsize=14)
    ax1.grid(True, alpha=0.3)

    # Add near-critical comparison
    ax1.axhline(y=3.7, color='red', linestyle='--', label='Near-critical extrapolation (λ/W ≈ 3.7)')
    ax1.axhline(y=2.79, color='green', linestyle='--', label='HGBS observation')
    ax1.axvline(x=1.2, color='gray', linestyle=':', label='Near-critical limit')
    ax1.legend()

    # Plot 2: λ/W vs f (log-log)
    ax2.loglog(f_sorted, lambda_sorted, 'bo-', color='blue', markersize=8)
    ax2.set_xlabel('Line-mass fraction f', fontsize=12)
    ax2.set_ylabel('λ/W', fontsize=12)
    ax2.set_title('Rigid Cylinder: λ/W vs. f (log-log)', fontsize=14)
    ax2.grid(True, alpha=0.3)

    # Fit power law
    def power_law(x, a, b):
        return a * x**b

    try:
        popt, pcov = curve_fit(power_law, f_sorted, lambda_sorted, p0=[3.7, -0.1])
        perr = np.sqrt(np.diag(pcov))

        f_fit = np.linspace(min(f_sorted), max(f_sorted), 50)
        lambda_fit = power_law(f_fit, *popt)

        ax2.plot(f_fit, lambda_fit, 'r-', label=f'Fit: λ/W = {popt[0]:.2f} × f^{popt[1]:.2f}')
        ax2.legend()

        print(f"\nPower-law fit: λ/W = {popt[0]:.2f} × f^{popt[1]:.2f}")
        print(f"  Exponent b = {popt[1]:.2f} ± {perr[1]:.2f}")

        # Check if extrapolation is valid
        # Near-critical Campaign 7 gave λ/W(f) decreasing smoothly
        # If rigid cylinder shows similar trend, extrapolation is supported
        # If different trend or discontinuity, extrapolation is not supported

        lambda_at_15 = power_law(1.5, *popt)
        lambda_at_30 = power_law(3.0, *popt)

        print(f"\n  λ/W at f=1.5: {lambda_at_15:.2f}")
        print(f"  λ/W at f=3.0: {lambda_at_30:.2f}")

        # Compare with near-critical extrapolation
        # At f=1.2, near-critical gives λ/W ≈ 3.0
        lambda_at_12 = power_law(1.2, *popt)
        print(f"  λ/W at f=1.2 (extrapolated): {lambda_at_12:.2f}")
        print(f"  (Near-critical Campaign 7: λ/W ≈ 3.0)")

    except Exception as e:
        print(f"Power-law fit failed: {e}")

    plt.tight_layout()
    plot_file = Path(output_dir) / "rigid_cylinder_lambdaW_vs_f.pdf"
    plt.savefig(plot_file)
    print(f"\nPlot saved to: {plot_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_rigid_cylinder.py <output_directory>")
        print("\nExample:")
        print("  python analyze_rigid_cylinder.py /rigid_cylinder_outputs")
        sys.exit(1)

    output_dir = sys.argv[1]

    if not Path(output_dir).exists():
        print(f"Error: Directory not found: {output_dir}")
        sys.exit(1)

    results = analyze_campaign(output_dir)

    print("\n" + "="*70)
    print("ANALYSIS SUMMARY")
    print("="*70)

    frag_count = sum(1 for r in results if r['classification'] == 'FRAGMENTED')
    total_count = len(results)

    print(f"Total simulations analyzed: {total_count}")
    print(f"Fragmented: {frag_count}")
    print(f"Fragmentation rate: {frag_count/total_count*100:.1f}%")

    lambda_W_vals = [r['lambda_W'] for r in results if r['lambda_W'] is not None]

    if lambda_W_vals:
        print(f"\nλ/W measurements: {lambda_W_vals}")
        print(f"Mean λ/W: {np.mean(lambda_W_vals):.2f}")
        print(f"Std λ/W: {np.std(lambda_W_vals):.2f}")

if __name__ == "__main__":
    main()
