#!/usr/bin/env python3
"""
Analyze Transition Mapping Campaign results
Extract fragmentation statistics: C_final, lambda_frag, n_peaks
"""

import numpy as np
import h5py
import json
import os
from pathlib import Path
from scipy.signal import find_peaks
from scipy.fft import fft, fftfreq

def analyze_simulation(sim_dir, sim_name):
    """
    Analyze a single simulation to extract fragmentation metrics

    Returns dict with:
    - C_final: final density contrast
    - n_peaks: number of fragmentation peaks
    - lambda_frag: mean fragmentation wavelength
    - lambda_frag_std: std of fragmentation wavelength
    - rho1d_last: final 1D density profile
    - peak_positions: positions of identified peaks
    """

    # Load final snapshot
    snapshot_path = os.path.join(sim_dir, "block*.0.04.00.tab")  # t = 4.0

    # Use glob to find the actual file (meshblock naming varies)
    import glob
    snapshot_files = glob.glob(os.path.join(sim_dir, "*.0.04.00.tab"))

    if not snapshot_files:
        return None

    try:
        # Read HDF5 output (Athena++ tab format)
        with h5py.File(snapshot_files[0], 'r') as f:
            # Get density field
            rho = f['prim']['rho'][...]  # Shape: (nx1, nx2, nx3)

            # Compute 1D density profile along filament axis (x1)
            # Average over cross-section (x2, x3)
            rho1d = np.mean(rho, axis=(1, 2))

            # Compute density contrast
            C_final = np.max(rho1d) / np.mean(rho1d)

            # Find peaks in log density
            log_rho = np.log10(rho1d)
            mean_log = np.mean(log_rho)
            std_log = np.std(log_rho)

            # Adaptive prominence threshold
            peaks, properties = find_peaks(
                log_rho,
            prominence=0.5 * std_log,
            distance=16  # Minimum spacing: 16 cells = 1.0 lambda_J
            )

            n_peaks = len(peaks)

            if n_peaks > 1:
                # Convert peak indices to physical positions
                x_coords = np.linspace(-8.0, 8.0, len(rho1d))
                peak_positions = x_coords[peaks]

                # Compute spacings between consecutive peaks
                spacings = np.diff(peak_positions)

                # Remove outliers using IQR method
                if len(spacings) > 3:
                    q25, q75 = np.percentile(spacings, [25, 75])
                    iqr = q75 - q25
                    lower = q25 - 1.5 * iqr
                    upper = q75 + 1.5 * iqr
                    robust_spacings = spacings[(spacings >= lower) & (spacings <= upper)]
                else:
                    robust_spacings = spacings

                if len(robust_spacings) > 0:
                    lambda_frag = np.mean(robust_spacings)
                    lambda_frag_std = np.std(robust_spacings)
                else:
                    lambda_frag = np.mean(spacings) if len(spacings) > 0 else 0.0
                    lambda_frag_std = 0.0
            else:
                peak_positions = np.array([])
                lambda_frag = 0.0
                lambda_frag_std = 0.0

            return {
                'run_id': sim_name,
                'C_final': float(C_final),
                'n_peaks': int(n_peaks),
                'lambda_frag': float(lambda_frag),
                'lambda_frag_std': float(lambda_frag_std),
                'peak_positions': peak_positions.tolist(),
                'status': 'analyzed'
            }

    except Exception as e:
        print(f"Error analyzing {sim_name}: {str(e)}")
        return {
            'run_id': sim_name,
            'status': 'error',
            'error': str(e)
        }

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Transition Mapping Campaign")
    parser.add_argument("--simulation-base", type=str,
                       default="/path/to/simulations/transition_mapping_campaign_apr2026",
                       help="Base directory for simulations")
    parser.add_argument("--output", type=str,
                       default="transition_mapping_analysis.json",
                       help="Output JSON file")

    args = parser.parse_args()

    # Load manifest
    manifest_path = os.path.join(args.simulation_base, "simulation_manifest.json")

    if not os.path.exists(manifest_path):
        print(f"ERROR: Manifest not found: {manifest_path}")
        return 1

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    print(f"Analyzing {len(manifest)} simulations...")

    results = []

    for i, sim_config in enumerate(manifest):
        sim_name = sim_config['run_id']
        sim_dir = sim_config['config_dir']

        print(f"[{i+1}/{len(manifest)}] Analyzing: {sim_name}")

        result = analyze_simulation(sim_dir, sim_name)

        if result and result.get('status') == 'analyzed':
            # Merge with simulation parameters
            result.update(sim_config)
            results.append(result)

        # Progress update every 10
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(manifest)} completed")

    # Save results
    output_path = os.path.join(args.simulation_base, args.output)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    print(f"Successfully analyzed: {len(results)}/{len(manifest)} simulations")

    # Print summary statistics
    if results:
        print("\nSummary Statistics:")
        print("="*60)

        # Group by f value
        f_values = sorted(set([r['f'] for r in results]))
        beta_values = sorted(set([r['beta'] for r in results]))

        print(f"\nf values analyzed: {f_values}")
        print(f"beta values analyzed: {beta_values}")

        # Find fragmentation transition
        print("\nFragmentation by (f, beta):")
        print("f    | beta | C_final | n_peaks | lambda_frag | Fragmented?")
        print("-" * 65)

        for f in f_values:
            for beta in beta_values:
                # Find matching result (use seed=42 for representative)
                matches = [r for r in results
                          if abs(r['f'] - f) < 0.01
                          and abs(r['beta'] - beta) < 0.01
                          and r['seed'] == 42]

                if matches:
                    r = matches[0]
                    frag = "YES" if r['C_final'] > 1.5 else "MARGINAL" if r['C_final'] > 1.1 else "NO"
                    print(f"{f:4.1f} | {beta:4.1f} | {r['C_final']:7.3f} | {r['n_peaks']:7} | {r['lambda_frag']:11.3f} | {frag}")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
