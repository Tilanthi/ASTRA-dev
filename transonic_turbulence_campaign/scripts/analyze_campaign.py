#!/usr/bin/env python3
"""
analyze_campaign.py

Analyze full campaign results and generate comparison with HGBS.

Usage:
    python analyze_campaign.py <results_directory>
    python analyze_campaign.py <results_directory> --output-summary campaign_summary.csv
"""

import sys
import os
import h5py
import numpy as np
import pandas as pd
import argparse
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
import json

# Import local modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.extract_lambda_W import (
    load_density_field, extract_1d_density, detect_cores,
    extract_lambda_W, classify_fragmentation
)
from scripts.monitor_turbulence import compute_mach_number


def parse_run_id(run_id: str) -> Dict:
    """
    Extract parameters from run ID.

    Expected format: f1.2_beta0.5_theta0_M1.0_seed42

    Parameters
    ----------
    run_id : str
        Run ID string

    Returns
    -------
    params : dict
        Dictionary of parameters
    """
    import re

    pattern = r'f([\d\.]+)_beta([\d\.]+)_theta(\d+)_M([\d\.]+)_seed(\d+)'
    match = re.match(pattern, run_id)

    if match:
        return {
            'f': float(match.group(1)),
            'beta': float(match.group(2)),
            'theta': int(match.group(3)),
            'M_driver': float(match.group(4)),
            'seed': int(match.group(5))
        }
    else:
        raise ValueError(f"Cannot parse run_id: {run_id}")


def find_hdf5_files(run_dir: Path) -> List[Path]:
    """Find all HDF5 files in run directory."""
    hdf5_files = []

    # Common patterns
    for pattern in ["*.h5", "*.hdf5", "turb.*.h5"]:
        hdf5_files.extend(run_dir.glob(pattern))

    return sorted(hdf5_files)


def analyze_single_run(run_dir: Path) -> Dict:
    """
    Analyze a single simulation run.

    Parameters
    ----------
    run_dir : Path
        Path to run directory

    Returns
    -------
    results : dict
        Analysis results
    """
    run_id = run_dir.name

    # Parse parameters
    try:
        params = parse_run_id(run_id)
    except ValueError:
        print(f"Warning: Could not parse run_id: {run_id}")
        return None

    # Find HDF5 files
    hdf5_files = find_hdf5_files(run_dir)

    if not hdf5_files:
        print(f"Warning: No HDF5 files found in {run_dir}")
        return None

    # Use final snapshot
    final_file = hdf5_files[-1]

    # Load density
    try:
        rho, dx = load_density_field(str(final_file))
    except Exception as e:
        print(f"Warning: Could not load density from {final_file}: {e}")
        return None

    # Extract 1D profile
    rho_1d = extract_1d_density(rho, axis=0)

    # Detect cores
    peaks, _ = detect_cores(rho_1d, dx, threshold=3.0, min_distance=10)

    # Extract spacing
    lambda_W, lambda_W_std = extract_lambda_W(peaks, dx, W_core=0.3)

    # Classify outcome
    outcome, confidence = classify_fragmentation(rho)

    # Analyze turbulence
    mach_numbers = []
    times = []

    for h5_file in hdf5_files[::5]:  # Every 5th file
        try:
            with h5py.File(h5_file, 'r') as f:
                time, M_turb = compute_mach_number(f)
                times.append(time)
                mach_numbers.append(M_turb)
        except:
            continue

    mach_numbers = np.array(mach_numbers)

    # Compile results
    results = {
        'run_id': run_id,
        **params,
        'n_cores': len(peaks),
        'lambda_W': lambda_W if not np.isnan(lambda_W) else None,
        'lambda_W_std': lambda_W_std if not np.isnan(lambda_W_std) else None,
        'outcome': outcome,
        'confidence': confidence,
        'M_turb_mean': float(np.mean(mach_numbers)) if len(mach_numbers) > 0 else None,
        'M_turb_std': float(np.std(mach_numbers)) if len(mach_numbers) > 0 else None,
        'M_turb_max': float(np.max(mach_numbers)) if len(mach_numbers) > 0 else None,
    }

    return results


def analyze_campaign(results_dir: str) -> pd.DataFrame:
    """
    Analyze all simulations in campaign.

    Parameters
    ----------
    results_dir : str
        Path to results directory

    Returns
    -------
    df : DataFrame
        Campaign results
    """
    results_path = Path(results_dir)

    # Find all run directories
    run_dirs = [d for d in results_path.iterdir() if d.is_dir()]

    if not run_dirs:
        print(f"Warning: No run directories found in {results_dir}")
        return pd.DataFrame()

    print(f"Found {len(run_dirs)} run directories")

    # Analyze each run
    results = []

    for i, run_dir in enumerate(run_dirs, 1):
        print(f"Analyzing {i}/{len(run_dirs)}: {run_dir.name}")

        result = analyze_single_run(run_dir)

        if result is not None:
            results.append(result)

    # Create DataFrame
    df = pd.DataFrame(results)

    return df


def generate_comparison_plots(df: pd.DataFrame, output_dir: str):
    """
    Generate comparison plots with HGBS.

    Parameters
    ----------
    df : DataFrame
        Campaign results
    output_dir : str
        Output directory for plots
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Figure 1: λ/W vs M_driver for different configurations
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Longitudinal field
    ax = axes[0]
    for beta_val in sorted(df['beta'].unique()):
        subset = df[(df['theta'] == 0) & (df['beta'] == beta_val)]

        if len(subset) > 0:
            grouped = subset.groupby('M_driver').agg({
                'lambda_W': ['mean', 'std'],
                'M_turb_mean': 'mean'
            })

            ax.errorbar(grouped.index, grouped[('lambda_W', 'mean')],
                       yerr=grouped[('lambda_W', 'std')],
                       marker='o', label=f'β={beta_val}', capsize=5)

    ax.axhline(y=2.79, color='k', linestyle='--', linewidth=2,
              label='HGBS PM')
    ax.set_xlabel('Driving Mach Number')
    ax.set_ylabel('λ/W')
    ax.set_title('Longitudinal Field (θ=0°)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Perpendicular field
    ax = axes[1]
    for beta_val in sorted(df['beta'].unique()):
        subset = df[(df['theta'] == 90) & (df['beta'] == beta_val)]

        if len(subset) > 0:
            grouped = subset.groupby('M_driver').agg({
                'lambda_W': ['mean', 'std'],
                'M_turb_mean': 'mean'
            })

            ax.errorbar(grouped.index, grouped[('lambda_W', 'mean')],
                       yerr=grouped[('lambda_W', 'std')],
                       marker='s', label=f'β={beta_val}', capsize=5)

    ax.axhline(y=2.79, color='k', linestyle='--', linewidth=2,
              label='HGBS PM')
    ax.set_xlabel('Driving Mach Number')
    ax.set_ylabel('λ/W')
    ax.set_title('Perpendicular Field (θ=90°)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path / 'lambda_W_vs_M.pdf', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Plot saved: {output_path / 'lambda_W_vs_M.pdf'}")

    # Figure 2: λ/W vs line-mass fraction
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Longitudinal field
    ax = axes[0]
    for m_val in sorted(df['M_driver'].unique()):
        subset = df[(df['theta'] == 0) & (df['M_driver'] == m_val)]

        if len(subset) > 0:
            grouped = subset.groupby('f').agg({
                'lambda_W': ['mean', 'std']
            })

            ax.errorbar(grouped.index, grouped[('lambda_W', 'mean')],
                       yerr=grouped[('lambda_W', 'std')],
                       marker='o', label=f'M={m_val}', capsize=5)

    ax.axhline(y=2.79, color='k', linestyle='--', linewidth=2,
              label='HGBS PM')
    ax.set_xlabel('Line-Mass Fraction (f)')
    ax.set_ylabel('λ/W')
    ax.set_title('Longitudinal Field (θ=0°)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Perpendicular field
    ax = axes[1]
    for m_val in sorted(df['M_driver'].unique()):
        subset = df[(df['theta'] == 90) & (df['M_driver'] == m_val)]

        if len(subset) > 0:
            grouped = subset.groupby('f').agg({
                'lambda_W': ['mean', 'std']
            })

            ax.errorbar(grouped.index, grouped[('lambda_W', 'mean')],
                       yerr=grouped[('lambda_W', 'std')],
                       marker='s', label=f'M={m_val}', capsize=5)

    ax.axhline(y=2.79, color='k', linestyle='--', linewidth=2,
              label='HGBS PM')
    ax.set_xlabel('Line-Mass Fraction (f)')
    ax.set_ylabel('λ/W')
    ax.set_title('Perpendicular Field (θ=90°)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path / 'lambda_W_vs_f.pdf', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Plot saved: {output_path / 'lambda_W_vs_f.pdf'}")

    # Figure 3: Outcome phase diagram
    fig, ax = plt.subplots(figsize=(10, 8))

    for outcome in ['BEADING', 'RADIAL_COLLAPSE']:
        subset = df[df['outcome'] == outcome]

        if len(subset) > 0:
            ax.scatter(subset['M_turb_mean'], subset['lambda_W'],
                      s=100, alpha=0.6, label=outcome)

    ax.axhline(y=2.79, color='k', linestyle='--', linewidth=2,
              label='HGBS PM')
    ax.axvline(x=1.0, color='r', linestyle=':', linewidth=2,
              label='Transonic threshold')
    ax.set_xlabel('Turbulent Mach Number')
    ax.set_ylabel('λ/W')
    ax.set_title('Fragmentation Outcome Phase Diagram')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path / 'outcome_phase_diagram.pdf', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Plot saved: {output_path / 'outcome_phase_diagram.pdf'}")


def print_summary(df: pd.DataFrame):
    """Print campaign summary statistics."""
    print("\n" + "="*60)
    print("Campaign Summary")
    print("="*60)

    print(f"\nTotal simulations: {len(df)}")

    print(f"\nTurbulence Statistics:")
    print(f"  Mean M_turb: {df['M_turb_mean'].mean():.3f} ± {df['M_turb_mean'].std():.3f}")
    print(f"  Min M_turb: {df['M_turb_mean'].min():.3f}")
    print(f"  Max M_turb: {df['M_turb_mean'].max():.3f}")
    print(f"  Transonic (M >= 1): {(df['M_turb_mean'] >= 1.0).sum()} simulations")
    print(f"  Supersonic (M >= 2): {(df['M_turb_mean'] >= 2.0).sum()} simulations")

    print(f"\nFragmentation Statistics:")
    valid_lambdaw = df[df['lambda_W'].notna()]
    print(f"  Valid λ/W measurements: {len(valid_lambdaw)}/{len(df)}")

    if len(valid_lambdaw) > 0:
        print(f"  Mean λ/W: {valid_lambdaw['lambda_W'].mean():.3f} ± {valid_lambdaw['lambda_W'].std():.3f}")
        print(f"  Range: {valid_lambdaw['lambda_W'].min():.3f} - {valid_lambdaw['lambda_W'].max():.3f}")

    print(f"\nOutcome Distribution:")
    outcome_counts = df['outcome'].value_counts()
    for outcome, count in outcome_counts.items():
        print(f"  {outcome}: {count} ({count/len(df)*100:.1f}%)")

    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze full turbulence campaign results"
    )
    parser.add_argument(
        "results_dir",
        help="Path to campaign results directory"
    )
    parser.add_argument(
        "--output-summary", "-o",
        help="Save summary CSV to file"
    )
    parser.add_argument(
        "--plot-dir", "-p",
        help="Directory for comparison plots"
    )

    args = parser.parse_args()

    print("="*60)
    print("Transonic Turbulence Campaign Analysis")
    print("="*60)
    print(f"\nResults directory: {args.results_dir}")

    # Analyze campaign
    df = analyze_campaign(args.results_dir)

    if df.empty:
        print("\nNo results to analyze.")
        return

    # Print summary
    print_summary(df)

    # Save summary
    if args.output_summary:
        df.to_csv(args.output_summary, index=False)
        print(f"\nSummary saved to: {args.output_summary}")

    # Generate plots
    if args.plot_dir:
        generate_comparison_plots(df, args.plot_dir)

    print("\n" + "="*60)


if __name__ == "__main__":
    main()
