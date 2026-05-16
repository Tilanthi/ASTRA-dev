#!/usr/bin/env python3
"""
Generate IC Comparison Figures

Creates publication-quality figures comparing King profile vs
uniform density initial conditions for the IC sensitivity test.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path
from typing import Dict, List
import os

# Set up matplotlib for publication quality
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Computer Modern Roman']
mpl.rcParams['text.usetex'] = True
mpl.rcParams['axes.linewidth'] = 1.0
mpl.rcParams['xtick.major.width'] = 1.0
mpl.rcParams['ytick.major.width'] = 1.0
mpl.rcParams['xtick.minor.width'] = 0.5
mpl.rcParams['ytick.minor.width'] = 0.5

def load_comparison_data() -> Dict:
    """Load IC sensitivity comparison data."""
    comparison_path = "output/analysis/ic_sensitivity_summary.json"

    if not os.path.exists(comparison_path):
        raise FileNotFoundError(f"Comparison data not found. Run compare_ic_sensitivity.py first.")

    with open(comparison_path, 'r') as f:
        return json.load(f)

def load_measurements() -> List[Dict]:
    """Load λ/W measurements."""
    measurements_path = "output/analysis/lambda_W_measurements.json"

    if not os.path.exists(measurements_path):
        raise FileNotFoundError(f"Measurements not found. Run analyze_lambda_W.py first.")

    with open(measurements_path, 'r') as f:
        return json.load(f)

def plot_ic_comparison_scatter(measurements: List[Dict], output_path: str):
    """Create scatter plot comparing King vs Uniform IC λ/W values."""
    # Group measurements by parameters (f, beta, M)
    param_groups = {}
    for m in measurements:
        if m['status'] != 'SUCCESS' or m['lambda_W'] is None:
            continue

        key = (m['f'], m['beta'], m['mach'])
        if key not in param_groups:
            param_groups[key] = {}
        param_groups[key][m['ic_type']] = m['lambda_W']

    # Filter for points with both IC types
    paired_data = []
    for key, values in param_groups.items():
        if 'king' in values and 'uniform' in values:
            paired_data.append({
                'f': key[0],
                'beta': key[1],
                'mach': key[2],
                'king': values['king'],
                'uniform': values['uniform']
            })

    if not paired_data:
        print("Warning: No paired data found for comparison")
        return

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 8))

    # Extract data
    king_vals = [d['king'] for d in paired_data]
    unif_vals = [d['uniform'] for d in paired_data]

    # Color by f value
    f_vals = [d['f'] for d in paired_data]
    colors = plt.cm.viridis(np.array(f_vals) / max(f_vals))

    # Plot scatter
    ax.scatter(king_vals, unif_vals, c=colors, s=100, alpha=0.7, edgecolors='black', linewidth=0.5)

    # Add 1:1 line
    min_val = min(min(king_vals), min(unif_vals))
    max_val = max(max(king_vals), max(unif_vals))
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='1:1 line')

    # Labels and title
    ax.set_xlabel('King Profile IC: $\\lambda/W$', fontsize=14)
    ax.set_ylabel('Uniform Density IC: $\\lambda/W$', fontsize=14)
    ax.set_title('Initial Condition Sensitivity Test\nNear-Critical Regime ($f = 1.0-1.3$)', fontsize=16)

    # Grid and legend
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.legend(loc='upper left', fontsize=12)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=1.0, vmax=1.3))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Mass-to-Line-Mass Ratio $f$', fontsize=12)

    # Add statistics text
    king_mean = np.mean(king_vals)
    unif_mean = np.mean(unif_vals)
    diff_pct = (unif_mean - king_mean) / king_mean * 100

    stats_text = f'$\\langle \\lambda/W \\rangle_{{\\rm King}} = {king_mean:.3f}$\n'
    stats_text += f'$\\langle \\lambda/W \\rangle_{{\\rm Uniform}} = {unif_mean:.3f}$\n'
    stats_text += f'Difference = {diff_pct:+.1f}%'

    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
            fontsize=12, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved IC comparison scatter plot to {output_path}")

def plot_parameter_dependence(comparison: Dict, output_path: str):
    """Create multi-panel plot showing parameter dependence."""
    param_dep = comparison['parameter_dependence']

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Dependence on f
    if param_dep['by_f']:
        ax = axes[0]
        f_vals = sorted(param_dep['by_f'].keys())

        king_vals = [param_dep['by_f'][f]['king'] for f in f_vals]
        unif_vals = [param_dep['by_f'][f]['uniform'] for f in f_vals]
        diffs = [param_dep['by_f'][f]['difference_percent'] for f in f_vals]

        x = np.arange(len(f_vals))
        width = 0.35

        ax.bar(x - width/2, king_vals, width, label='King IC', color='steelblue', alpha=0.8)
        ax.bar(x + width/2, unif_vals, width, label='Uniform IC', color='coral', alpha=0.8)

        ax.set_xlabel('Mass-to-Line-Mass Ratio $f$', fontsize=14)
        ax.set_ylabel('$\\lambda/W$', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels([f'{f:.2f}' for f in f_vals])
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_title('Dependence on $f$', fontsize=14)

    # Plot 2: Dependence on beta
    if param_dep['by_beta']:
        ax = axes[1]
        beta_vals = sorted(param_dep['by_beta'].keys())

        king_vals = [param_dep['by_beta'][b]['king'] for b in beta_vals]
        unif_vals = [param_dep['by_beta'][b]['uniform'] for b in beta_vals]
        diffs = [param_dep['by_beta'][b]['difference_percent'] for b in beta_vals]

        x = np.arange(len(beta_vals))
        width = 0.35

        ax.bar(x - width/2, king_vals, width, label='King IC', color='steelblue', alpha=0.8)
        ax.bar(x + width/2, unif_vals, width, label='Uniform IC', color='coral', alpha=0.8)

        ax.set_xlabel('Plasma Beta $\\beta$', fontsize=14)
        ax.set_ylabel('$\\lambda/W$', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels([f'{b:.1f}' for b in beta_vals])
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_title('Dependence on $\\beta$', fontsize=14)

    plt.suptitle('IC Sensitivity: Parameter Dependence', fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved parameter dependence plot to {output_path}")

def plot_distribution_comparison(measurements: List[Dict], output_path: str):
    """Create histogram comparing λ/W distributions."""
    king_vals = [m['lambda_W'] for m in measurements if m['status'] == 'SUCCESS' and m['lambda_W'] is not None and m.get('ic_type') == 'king']
    unif_vals = [m['lambda_W'] for m in measurements if m['status'] == 'SUCCESS' and m['lambda_W'] is not None and m.get('ic_type') == 'uniform']

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot histograms
    bins = np.linspace(min(min(king_vals), min(unif_vals)) - 0.5,
                       max(max(king_vals), max(unif_vals)) + 0.5, 15)

    ax.hist(king_vals, bins=bins, alpha=0.6, label='King IC', color='steelblue', density=True)
    ax.hist(unif_vals, bins=bins, alpha=0.6, label='Uniform IC', color='coral', density=True)

    # Add means as vertical lines
    ax.axvline(np.mean(king_vals), color='steelblue', linestyle='--', linewidth=2, label=f'King mean: {np.mean(king_vals):.3f}')
    ax.axvline(np.mean(unif_vals), color='coral', linestyle='--', linewidth=2, label=f'Uniform mean: {np.mean(unif_vals):.3f}')

    # Labels and title
    ax.set_xlabel('$\\lambda/W$', fontsize=14)
    ax.set_ylabel('Probability Density', fontsize=14)
    ax.set_title('Distribution of Fragmentation Wavelength\nNear-Critical Regime ($f = 1.0-1.3$)', fontsize=16)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved distribution comparison to {output_path}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate IC comparison figures")
    parser.add_argument("--output-dir", type=str, default="output/analysis/figures",
                       help="Output directory for figures")
    args = parser.parse_args()

    print("Generating IC Comparison Figures")
    print("="*60)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Load data
    try:
        comparison = load_comparison_data()
        measurements = load_measurements()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # Generate figures
    print("\nGenerating figures...")

    scatter_path = os.path.join(args.output_dir, "ic_comparison_scatter.pdf")
    plot_ic_comparison_scatter(measurements, scatter_path)

    param_path = os.path.join(args.output_dir, "ic_parameter_dependence.pdf")
    plot_parameter_dependence(comparison, param_path)

    dist_path = os.path.join(args.output_dir, "ic_distribution_comparison.pdf")
    plot_distribution_comparison(measurements, dist_path)

    print(f"\nAll figures saved to {args.output_dir}/")
    print("\nFigure files:")
    print(f"  - ic_comparison_scatter.pdf")
    print(f"  - ic_parameter_dependence.pdf")
    print(f"  - ic_distribution_comparison.pdf")

if __name__ == "__main__":
    main()
