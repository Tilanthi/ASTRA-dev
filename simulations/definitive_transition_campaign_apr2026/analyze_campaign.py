#!/usr/bin/env python3
"""
Analyze Definitive 2D Transition Campaign results
Extract fragmentation metrics and map transition boundary
"""

import numpy as np
import h5py
import json
import os
from pathlib import Path
from scipy.signal import find_peaks
from scipy.interpolate import griddata
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

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
    import glob
    snapshot_files = glob.glob(os.path.join(sim_dir, "*.0.04.00.tab"))  # t = 4.0

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

def plot_transition_boundary(results, output_dir, mach_value):
    """Create 2D colormap of C_final in (f, beta) plane"""

    # Filter by Mach number
    mach_results = [r for r in results if abs(r['mach'] - mach_value) < 0.1 and r.get('status') == 'analyzed']

    if not mach_results:
        print(f"No results for M = {mach_value}")
        return

    # Extract data points
    f_vals = np.array([r['f'] for r in mach_results])
    beta_vals = np.array([r['beta'] for r in mach_results])
    C_vals = np.array([r['C_final'] for r in mach_results])

    # Create regular grid for interpolation
    f_grid = np.linspace(1.3, 2.3, 100)
    beta_grid = np.linspace(0.2, 1.4, 100)
    F, B = np.meshgrid(f_grid, beta_grid)

    # Interpolate C_final onto regular grid
    points = np.column_stack((f_vals, beta_vals))
    C_grid = griddata(points, C_vals, (F, B), method='cubic')

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Custom colormap: blue (suppressed) -> yellow (transition) -> red (fragmented)
    colors = ['#3B4CC0', '#B4DDDB', '#F7F7B6', '#E8A87C', '#C41E3A']
    cmap = LinearSegmentedColormap.from_list('fragment', colors, N=256)

    # Plot colormap
    im = ax.contourf(F, B, C_grid, levels=50, cmap=cmap, vmin=1.0, vmax=3.0)

    # Add contour lines for C_final = 1.5 and 2.0
    cs1 = ax.contour(F, B, C_grid, levels=[1.5], colors='black', linewidths=2, linestyles='--')
    cs2 = ax.contour(F, B, C_grid, levels=[2.0], colors='black', linewidths=2, linestyles='-')

    # Plot data points
    scatter = ax.scatter(f_vals, beta_vals, c=C_vals, cmap=cmap, vmin=1.0, vmax=3.0,
                        s=100, edgecolors='black', linewidths=1.5)

    # Labels and title
    ax.set_xlabel('Supercriticality $f$', fontsize=14)
    ax.set_ylabel('Plasma $\\beta$', fontsize=14)
    ax.set_title(f'Fragmentation Transition Boundary (M = {mach_value:.1f})', fontsize=16)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('$C_{\\mathrm{final}}$', fontsize=14)

    # Add grid
    ax.grid(True, alpha=0.3)

    # Add text annotations
    ax.text(1.45, 1.25, 'FRAGMENTED', fontsize=12, fontweight='bold', color='darkred')
    ax.text(2.1, 0.35, 'SUPPRESSED', fontsize=12, fontweight='bold', color='darkblue')

    # Tight layout
    plt.tight_layout()

    # Save figure
    output_path = os.path.join(output_dir, f"transition_boundary_M{mach_value:.0f}.pdf")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  Saved: {output_path}")

def plot_cross_sections(results, output_dir):
    """Plot C_final vs f for different beta values"""

    mach_values = [1.0, 2.0, 3.0]

    for mach in mach_values:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Filter by Mach number
        mach_results = [r for r in results if abs(r['mach'] - mach) < 0.1 and r.get('status') == 'analyzed']

        if not mach_results:
            continue

        # Panel 1: C_final vs f (grouped by beta)
        ax = axes[0]
        beta_values = sorted(set([r['beta'] for r in mach_results]))

        for beta in beta_values:
            beta_results = [r for r in mach_results if abs(r['beta'] - beta) < 0.01]
            f_vals = [r['f'] for r in beta_results]
            C_vals = [r['C_final'] for r in beta_results]

            # Average over seeds
            f_unique = sorted(set(f_vals))
            C_mean = []
            C_std = []

            for f in f_unique:
                f_results = [r for r in beta_results if abs(r['f'] - f) < 0.01]
                C_f = [r['C_final'] for r in f_results]
                C_mean.append(np.mean(C_f))
                C_std.append(np.std(C_f))

            ax.plot(f_unique, C_mean, 'o-', label=f'$\\beta = {beta:.1f}$', linewidth=2, markersize=8)
            ax.fill_between(f_unique, np.array(C_mean)-np.array(C_std), np.array(C_mean)+np.array(C_std), alpha=0.2)

        ax.axhline(y=1.5, color='black', linestyle='--', linewidth=2, label='Transition threshold')
        ax.set_xlabel('Supercriticality $f$', fontsize=12)
        ax.set_ylabel('$C_{\\mathrm{final}}$', fontsize=12)
        ax.set_title(f'Density Contrast vs $f$ (M = {mach:.0f})', fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0.9, 3.5)

        # Panel 2: C_final vs beta (grouped by f)
        ax = axes[1]
        f_values = sorted(set([r['f'] for r in mach_results]))

        for f in f_values:
            f_results = [r for r in mach_results if abs(r['f'] - f) < 0.01]
            beta_vals = [r['beta'] for r in f_results]
            C_vals = [r['C_final'] for r in f_results]

            # Average over seeds
            beta_unique = sorted(set(beta_vals))
            C_mean = []
            C_std = []

            for beta in beta_unique:
                beta_results = [r for r in f_results if abs(r['beta'] - beta) < 0.01]
                C_b = [r['C_final'] for r in beta_results]
                C_mean.append(np.mean(C_b))
                C_std.append(np.std(C_b))

            ax.plot(beta_unique, C_mean, 's-', label=f'$f = {f:.1f}$', linewidth=2, markersize=8)
            ax.fill_between(beta_unique, np.array(C_mean)-np.array(C_std), np.array(C_mean)+np.array(C_std), alpha=0.2)

        ax.axhline(y=1.5, color='black', linestyle='--', linewidth=2, label='Transition threshold')
        ax.set_xlabel('Plasma $\\beta$', fontsize=12)
        ax.set_ylabel('$C_{\\mathrm{final}}$', fontsize=12)
        ax.set_title(f'Density Contrast vs $\\beta$ (M = {mach:.0f})', fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0.9, 3.5)

        plt.tight_layout()

        # Save figure
        output_path = os.path.join(output_dir, f"cross_sections_M{mach:.0f}.pdf")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  Saved: {output_path}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Definitive 2D Transition Campaign")
    parser.add_argument("--simulation-base", type=str,
                       default="/path/to/simulations/definitive_transition_campaign_apr2026",
                       help="Base directory for simulations")
    parser.add_argument("--output", type=str,
                       default="definitive_transition_analysis.json",
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

        # Progress update every 20
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{len(manifest)} completed")

    # Save results
    output_path = os.path.join(args.simulation_base, args.output)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    print(f"Successfully analyzed: {len(results)}/{len(manifest)} simulations")

    # Create output directory for figures
    figures_dir = os.path.join(args.simulation_base, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    # Generate figures
    print("\nGenerating figures...")

    # Transition boundary plots for each Mach number
    for mach in [1.0, 2.0, 3.0, 4.0, 5.0]:
        plot_transition_boundary(results, figures_dir, mach)

    # Cross-section plots
    plot_cross_sections(results, figures_dir)

    print(f"\nFigures saved to: {figures_dir}")

    # Print summary statistics
    if results:
        print("\nSummary Statistics:")
        print("="*70)

        # Group by Mach number
        mach_values = sorted(set([r['mach'] for r in results]))

        print(f"\nFragmentation by (f, beta, M):")
        print("f    | beta | M    | C_final | n_peaks | lambda_frag | Fragmented?")
        print("-" * 75)

        for mach in mach_values:
            mach_results = [r for r in results if abs(r['mach'] - mach) < 0.1]

            for f in [1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2]:
                for beta in [0.3, 0.5, 0.7, 0.9, 1.1, 1.3]:
                    # Find matching result (use seed=42 for representative)
                    matches = [r for r in mach_results
                              if abs(r['f'] - f) < 0.01
                              and abs(r['beta'] - beta) < 0.01
                              and r['seed'] == 42]

                    if matches:
                        r = matches[0]
                        frag = "YES" if r['C_final'] > 2.0 else "MARGINAL" if r['C_final'] > 1.5 else "NO"
                        print(f"{f:4.1f} | {beta:4.1f} | {mach:4.1f} | {r['C_final']:7.3f} | {r['n_peaks']:7} | {r['lambda_frag']:11.3f} | {frag}")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
