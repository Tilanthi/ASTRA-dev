#!/usr/bin/env python3
"""
Analysis pipeline for Critical Regime Filament Spacing Campaign

Processes Athena++ output files to measure λ/W (fragmentation spacing / filament width)
"""

import sys
import numpy as np
import h5py
import pandas as pd
from pathlib import Path
from scipy.spatial import cKDTree
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt


def analyze_simulation(sim_dir: Path, verbose: bool = False) -> dict:
    """
    Analyze one simulation directory and measure λ/W.

    Parameters:
    -----------
    sim_dir : Path
        Path to simulation directory
    verbose : bool
        Print progress messages

    Returns:
    --------
    dict with keys: lambda_over_W, n_frag, t_frag, density_contrast
    """

    if verbose:
        print(f"Analyzing {sim_dir.name}")

    # Load final snapshot
    vtk_files = sorted(sim_dir.glob("*.vtk"))
    if not vtk_files:
        # Try HDF5 outputs
        h5_files = list(sim_dir.glob("*.h5"))
        if not h5_files:
            return None

        # Load from HDF5
        return _analyze_hdf5(h5_files[-1], verbose)

    return _analyze_vtk(vtk_files[-1], verbose)


def _analyze_vtk(vtk_file: Path, verbose: bool) -> dict:
    """Analyze VTK output file."""

    # Read VTK file (simplified - in practice, use vtk library)
    # For now, this is a placeholder that would read the actual density field

    # Expected VTK structure:
    # STRUCTURED_POINTS
    # DIMENSIONS 512 512 1024
    # POINT_DATA 512*512*1024
    # SCALARS density float
    # ...

    # This would be implemented with vtk or pyvista library
    # For now, return placeholder result

    return {
        'lambda_over_W': np.nan,
        'n_frag': 0,
        't_frag': np.nan,
        'density_contrast': np.nan
    }


def _analyze_hdf5(h5_file: Path, verbose: bool) -> dict:
    """Analyze HDF5 output file."""

    try:
        with h5py.File(h5_file, 'r') as f:
            # Load density field
            rho = f['density'][:]  # Shape: (nx, ny, nz)

            # Get grid dimensions
            nx, ny, nz = rho.shape

            # Get physical scale from metadata
            try:
                dx = f['dx'][()]
                Lx = nx * dx
            except:
                dx = 1.0  # Default
                Lx = nx

            # Filament axis is z (periodic boundary)
            # Project density onto x-y plane to identify filament center
            rho_xy = np.mean(rho, axis=2)

            # Find filament center (maximum of projected density)
            y_center, x_center = np.unravel_index(np.argmax(rho_xy), rho_xy.shape)

            # Extract radial profile from filament center
            r_max = min(x_center, nx - x_center, y_center, ny - y_center)
            r_pixels = np.arange(1, r_max)

            rho_radial = []
            for r in r_pixels:
                # Extract circle at radius r
                y_grid, x_grid = np.ogrid[-ny:ny, -nx:nx]
                mask = ((x_grid - x_center)**2 + (y_grid - y_center)**2) == r**2

                if np.any(mask):
                    rho_radial.append(np.mean(rho_xy[mask]))
                else:
                    # Interpolate if needed
                    from scipy.interpolate import RegularGridInterpolator
                    interp = RegularGridInterpolator(
                        (np.arange(ny), np.arange(nx)),
                        rho_xy, method='linear', bounds_error=False, fill_value=None
                    )
                    y_circle = np.arange(ny)[np.abs(np.arange(ny) - y_center) <= r]
                    x_circle = np.arange(nx)[np.abs(np.arange(nx) - x_center) <= r]
                    if len(y_circle) > 0 and len(x_circle) > 0:
                        values = interp((y_circle, x_circle))
                        if np.any(~np.isnan(values)):
                            rho_radial.append(np.nanmean(values))
                        else:
                            break
                    else:
                        break

            if len(rho_radial) < 10:
                return None

            r_pixels = np.arange(len(rho_radial))

            # Fit Gaussian to get filament width
            def gaussian(r, A, sigma, x0, bg):
                return bg + A * np.exp(-(r - x0)**2 / (2 * sigma**2))

            try:
                popt, _ = curve_fit(
                    gaussian, r_pixels, rho_radial,
                    p0=[rho_xy.max(), 10.0, 0.0, rho_xy.min()],
                    maxfev=10000
                )
                W_pixels = 2.355 * popt[1]  # FWHM
            except:
                return None

            # Project density onto filament axis
            # Use narrow cylinder around filament center
            mask_radius = int(W_pixels / 2.0)
            y_mask, x_mask = np.ogrid[-ny:ny, -nx:nx]
            mask = (x_mask - x_center)**2 + (y_mask - y_center)**2 < mask_radius**2

            rho_1d = np.mean(rho[mask], axis=(0, 1))

            # Smooth the 1D profile
            from scipy.ndimage import gaussian_filter1d
            rho_1d_smooth = gaussian_filter1d(rho_1d, sigma=3)

            # Find peaks (cores)
            peaks, properties = find_peaks(
                rho_1d_smooth,
                height=5.0 * rho_1d_smooth.mean(),
                distance=W_pixels,
                prominence=0.5 * rho_1d_smooth.std()
            )

            n_frag = len(peaks)

            if verbose:
                print(f"  Found {n_frag} fragments")

            if n_frag < 2:
                return {
                    'lambda_over_W': np.nan,
                    'n_frag': n_frag,
                    't_frag': np.nan,
                    'density_contrast': rho_1d_smooth.max() / rho_1d_smooth.mean()
                }

            # Calculate pairwise median spacing
            from itertools import combinations
            spacings = [abs(p1 - p2) for p1, p2 in combinations(peaks, 2)]
            lambda_median = np.median(spacings)

            # Convert to physical units
            W_physical = W_pixels * dx
            lambda_physical = lambda_median * dx

            return {
                'lambda_over_W': lambda_physical / W_physical,
                'n_frag': n_frag,
                't_frag': np.nan,  # Would be extracted from time series
                'density_contrast': rho_1d_smooth.max() / rho_1d_smooth.mean()
            }

    except Exception as e:
        if verbose:
            print(f"  Error: {e}")
        return None


def analyze_all(simulation_dir: Path, output_file: str = "results_summary.csv"):
    """
    Analyze all simulations and create summary table.
    """

    sim_dirs = sorted(simulation_dir.glob("f*_*"))
    results = []

    for sim_dir in sim_dirs:
        result = analyze_simulation(sim_dir, verbose=True)
        if result is not None:
            # Extract parameters from directory name
            # Expected format: f2.00_beta1.00_M2.0_seed1
            parts = sim_dir.name.split('_')
            f = float(parts[0][1:])
            beta = float(parts[1][4:])
            M = float(parts[2][1:])
            seed = int(parts[3][4:])

            result['f'] = f
            result['beta'] = beta
            result['M'] = M
            result['seed'] = seed
            results.append(result)

    # Create summary table
    df = pd.DataFrame(results)
    df = df[['f', 'beta', 'M', 'seed', 'lambda_over_W', 'n_frag', 'density_contrast']]
    df.to_csv(output_file, index=False)

    print(f"\nSaved {len(df)} results to {output_file}")

    return df


def plot_comparison_with_observation(df: pd.DataFrame, output_file: str = "comparison.pdf"):
    """
    Plot simulation results vs HGBS observation (λ/W = 2.11).
    """

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Panel 1: λ/W vs β for different f values
    for f in df['f'].unique():
        subset = df[df['f'] == f]
        axes[0].errorbar(
            subset['beta'], subset['lambda_over_W'],
            yerr=subset['lambda_over_W'] * 0.05,  # 5% uncertainty
            fmt='o-', label=f'f = {f:.1f}',
            capsize=3
        )

    axes[0].axhline(y=2.11, color='red', linestyle='--', linewidth=2, label='HGBS observed')
    axes[0].set_xlabel('β')
    axes[0].set_ylabel('λ/W')
    axes[0].set_title('Fragmentation spacing vs plasma beta')
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # Panel 2: λ/W vs f for different β values
    for beta in [0.5, 1.0, 1.5]:
        subset = df[df['beta'] == beta]
        axes[1].errorbar(
            subset['f'], subset['lambda_over_W'],
            yerr=subset['lambda_over_W'] * 0.05,
            fmt='o-', label=f'β = {beta:.1f}',
            capsize=3
        )

    axes[1].axhline(y=2.11, color='red', linestyle='--', linewidth=2, label='HGBS observed')
    axes[1].axhline(y=4.0, color='gray', linestyle=':', linewidth=2, label='IM92 prediction')
    axes[1].set_xlabel('f (line-mass ratio)')
    axes[1].set_ylabel('λ/W')
    axes[1].set_title('Fragmentation spacing vs supercriticality')
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    # Panel 3: 2D contour plot
    f_grid = np.unique(df['f'])
    beta_grid = np.unique(df['beta'])
    lambda_grid = df.pivot(index='f', columns='beta', values='lambda_over_W')

    cf = axes[2].contourf(f_grid, beta_grid, lambda_grid.T, levels=20, cmap='viridis')
    axes[2].contour(f_grid, beta_grid, lambda_grid.T, levels=[2.11], colors='red', linewidths=2)
    axes[2].clabel(cf, inline=True, fontsize=8)
    axes[2].scatter(df['f'], df['beta'], c=df['lambda_over_W'], cmap='viridis', edgecolor='black')
    axes[2].axhline(y=2.11, color='red', linestyle='--', linewidth=2, label='HGBS λ/W')
    axes[2].set_xlabel('f')
    axes[2].set_ylabel('β')
    axes[2].set_title('λ/W across parameter space')
    axes[2].legend()
    axes[2].grid(alpha=0.3)

    plt.colorbar(cf, ax=axes[2], label='λ/W')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved comparison plot to {output_file}")


def print_hgbs_comparison(df: pd.DataFrame):
    """Print summary of simulations in HGBS parameter range."""

    print("\n" + "="*70)
    print("HGBS REGIME COMPARISON")
    print("="*70)

    hgb = df[
        (df['f'] >= 2.0) & (df['f'] <= 2.5) &
        (df['beta'] >= 0.5) & (df['beta'] <= 1.5) &
        (df['M'] >= 2.0) & (df['M'] <= 3.0)
    ]

    if len(hgb) == 0:
        print("No simulations in HGBS parameter range!")
        return

    print(f"\nSimulations in HGBS regime (f=2-2.5, β=0.5-1.5, M=2-3): {len(hgb)}")
    print(f"\nλ/W statistics:")
    print(f"  Mean:   {hgb['lambda_over_W'].mean():.3f} ± {hgb['lambda_over_W'].std():.3f}")
    print(f"  Median: {hgb['lambda_over_W'].median():.3f}")
    print(f"  Range:  {hgb['lambda_over_W'].min():.3f} - {hgb['lambda_over_W'].max():.3f}")

    # Compare with HGBS observation
    diff = hgb['lambda_over_W'].mean() - 2.11
    print(f"\nComparison with HGBS (λ/W = 2.11):")
    print(f"  Difference: {diff:+.3f} ({100*diff/2.11:+.1f}%)")

    if abs(diff) < 0.2:
        print("  → Good agreement!")
    elif abs(diff) < 0.5:
        print("  → Moderate agreement")
    else:
        print("  → Poor agreement")

    # Magnetic tension prediction
    for beta_test in [0.5, 1.0, 1.5]:
        subset = hgb[hgb['beta'] == beta_test]
        if len(subset) > 0:
            print(f"\nAt β = {beta_test:.1f}: λ/W = {subset['lambda_over_W'].mean():.3f}")

    print("\n" + "="*70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze filament spacing simulations")
    parser.add_argument("sim_dir", type=str, help="Simulation directory")
    parser.add_argument("--output", type=str, default="results_summary.csv",
                       help="Output CSV file")
    parser.add_argument("--plot", type=str, default="comparison.pdf",
                       help="Output plot file")

    args = parser.parse_args()

    sim_dir = Path(args.sim_dir)

    # Analyze all simulations
    df = analyze_all(sim_dir, args.output)

    # Generate comparison plot
    plot_comparison_with_observation(df, args.plot)

    # Print HGBS comparison
    print_hgbs_comparison(df)


if __name__ == "__main__":
    main()
