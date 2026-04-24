#!/usr/bin/env python3
"""
Generate Analysis Figures

Creates publication-quality figures for the peer review validation campaign,
including DTC fragmentation rate and resolution convergence visualizations.
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path
from typing import Dict, List

# Configuration
STATUS_DIR = "../output/status"
RUN_LIST_PATH = "../simulations/run_list.json"
OUTPUT_DIR = "../output/figures"

# Set up matplotlib for publication-quality figures
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Latin Modern Roman']
mpl.rcParams['text.usetex'] = True
mpl.rcParams['figure.dpi'] = 300
mpl.rcParams['savefig.dpi'] = 300
mpl.rcParams['axes.linewidth'] = 1.0
mpl.rcParams['xtick.major.width'] = 1.0
mpl.rcParams['ytick.major.width'] = 1.0

def load_status_files() -> Dict[str, Dict]:
    """Load all status files."""
    status_files = {}
    status_dir = Path(STATUS_DIR)

    if not status_dir.exists():
        return status_files

    for status_file in status_dir.glob("status_*.json"):
        try:
            with open(status_file, 'r') as f:
                data = json.load(f)
                run_id = data['run_id']
                status_files[run_id] = data
        except Exception as e:
            print(f"Warning: Could not load {status_file}: {e}")

    return status_files

def plot_dtc_frag_fraction(status_files: Dict[str, Dict]):
    """Plot DTC fragmentation fraction by f value."""
    dtc_results = [s for s in status_files.values() if s['run_id'].startswith('dtc_rerun_')]

    if not dtc_results:
        print("No DTC results available for plotting")
        return

    # Group by f value
    f_groups = {}
    for r in dtc_results:
        f = r['f']
        if f not in f_groups:
            f_groups[f] = {'FRAG': 0, 'STABLE': 0, 'TIMEOUT': 0, 'FAILED': 0}
        f_groups[f][r['status']] += 1

    # Calculate fragmentation fraction
    f_values = sorted(f_groups.keys())
    frag_frac = []
    frag_err = []

    for f in f_values:
        total = sum(f_groups[f].values())
        frag = f_groups[f]['FRAG']
        frac = frag / total if total > 0 else 0
        err = np.sqrt(frac * (1 - frac) / total) if total > 0 else 0  # Binomial error

        frag_frac.append(frac)
        frag_err.append(err)

    # Create figure
    fig, ax = plt.subplots(figsize=(6, 5))

    # Plot with error bars
    ax.errorbar(f_values, frag_frac, yerr=frag_err, fmt='o-', color='black',
                markersize=8, capsize=5, linewidth=1.5, label='Fragmentation fraction')

    # Add reference line at 0 (no fragmentation) and 1 (all fragment)
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.3)

    # Labels and title
    ax.set_xlabel('Line-mass ratio $f$', fontsize=12)
    ax.set_ylabel('Fragmentation fraction', fontsize=12)
    ax.set_title('DTC Re-run: Fragmentation vs Line-mass', fontsize=14)

    # Y-axis limits
    ax.set_ylim(-0.1, 1.1)

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')

    # Tight layout
    plt.tight_layout()

    # Save figure
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fig_path = os.path.join(OUTPUT_DIR, 'dtc_frag_fraction.pdf')
    plt.savefig(fig_path, format='pdf', bbox_inches='tight')
    plt.savefig(fig_path.replace('.pdf', '.png'), format='png', bbox_inches='tight', dpi=300)

    print(f"Saved: {fig_path}")

    plt.close()

def plot_dtc_tfrag_distribution(status_files: Dict[str, Dict]):
    """Plot distribution of t_frag for DTC re-runs."""
    dtc_results = [s for s in status_files.values() if s['run_id'].startswith('dtc_rerun_') and s['status'] == 'FRAG']

    if not dtc_results:
        print("No DTC fragmentation results available for plotting")
        return

    t_frag_values = [r['t_frag'] for r in dtc_results]

    # Create figure
    fig, ax = plt.subplots(figsize=(6, 5))

    # Plot histogram
    ax.hist(t_frag_values, bins=10, color='black', alpha=0.7, edgecolor='white')

    # Add mean and median lines
    mean_t = np.mean(t_frag_values)
    median_t = np.median(t_frag_values)
    ax.axvline(mean_t, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_t:.2f} $t_J$')
    ax.axvline(median_t, color='blue', linestyle='--', linewidth=2, label=f'Median: {median_t:.2f} $t_J$')

    # Labels and title
    ax.set_xlabel('$t_{frag}$ [$t_J$]', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title('DTC Re-run: Fragmentation Time Distribution', fontsize=14)

    # Legend
    ax.legend(fontsize=10)

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')

    # Tight layout
    plt.tight_layout()

    # Save figure
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fig_path = os.path.join(OUTPUT_DIR, 'dtc_tfrag_distribution.pdf')
    plt.savefig(fig_path, format='pdf', bbox_inches='tight')
    plt.savefig(fig_path.replace('.pdf', '.png'), format='png', bbox_inches='tight', dpi=300)

    print(f"Saved: {fig_path}")

    plt.close()

def plot_resolution_scatter(status_files: Dict[str, Dict], run_list: Dict):
    """Plot resolution comparison scatter plot."""
    res_sims = [s for s in run_list['simulations'] if s['priority'] == 2]

    comparisons = []
    for sim in res_sims:
        run_id = sim['run_id']
        if run_id in status_files:
            status_256 = status_files[run_id]
            tfrag_256 = status_256.get('t_frag')
            tfrag_128 = sim.get('ref_tfrag_128')

            if tfrag_256 and tfrag_128 and status_256['status'] == 'FRAG':
                rel_diff = abs(tfrag_256 - tfrag_128) / tfrag_128
                converged = rel_diff < 0.05
                comparisons.append({
                    'tfrag_128': tfrag_128,
                    'tfrag_256': tfrag_256,
                    'converged': converged,
                    'rel_diff': rel_diff
                })

    if not comparisons:
        print("No resolution comparisons available for plotting")
        return

    # Create figure
    fig, ax = plt.subplots(figsize=(6, 5))

    # Extract data
    tfrag_128 = [c['tfrag_128'] for c in comparisons]
    tfrag_256 = [c['tfrag_256'] for c in comparisons]
    colors = ['green' if c['converged'] else 'red' for c in comparisons]

    # Plot scatter
    ax.scatter(tfrag_128, tfrag_256, c=colors, s=100, alpha=0.7, edgecolors='black', linewidth=0.5)

    # Plot 1:1 line
    t_min = min(min(tfrag_128), min(tfrag_256))
    t_max = max(max(tfrag_128), max(tfrag_256))
    ax.plot([t_min, t_max], [t_min, t_max], 'k--', linewidth=1, label='1:1 line')

    # Plot 5% lines
    ax.plot([t_min, t_max], [t_min*0.95, t_max*0.95], 'k:', linewidth=0.5, alpha=0.5, label='$\\pm$5\%')
    ax.plot([t_min, t_max], [t_min*1.05, t_max*1.05], 'k:', linewidth=0.5, alpha=0.5)

    # Labels and title
    ax.set_xlabel('$t_{frag}$ (128$^3$) [$t_J$]', fontsize=12)
    ax.set_ylabel('$t_{frag}$ (256$^3$) [$t_J$]', fontsize=12)
    ax.set_title('Resolution Convergence Test', fontsize=14)

    # Grid and legend
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=10)

    # Equal aspect ratio
    ax.set_aspect('equal', adjustable='box')

    # Tight layout
    plt.tight_layout()

    # Save figure
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fig_path = os.path.join(OUTPUT_DIR, 'resolution_comparison.pdf')
    plt.savefig(fig_path, format='pdf', bbox_inches='tight')
    plt.savefig(fig_path.replace('.pdf', '.png'), format='png', bbox_inches='tight', dpi=300)

    print(f"Saved: {fig_path}")

    plt.close()

def plot_summary_dashboard(status_files: Dict[str, Dict], run_list: Dict):
    """Create summary dashboard figure."""
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))

    # Subplot 1: Campaign completion status
    ax1 = axes[0, 0]
    total = len(status_files)
    frag = sum(1 for s in status_files.values() if s['status'] == 'FRAG')
    stable = sum(1 for s in status_files.values() if s['status'] == 'STABLE')
    timeout = sum(1 for s in status_files.values() if s['status'] == 'TIMEOUT')

    labels = ['FRAG', 'STABLE', 'TIMEOUT']
    sizes = [frag, stable, timeout]
    colors = ['red', 'green', 'orange']
    ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax1.set_title('Campaign Completion Status')

    # Subplot 2: DTC fragmentation by f value
    ax2 = axes[0, 1]
    dtc_results = [s for s in status_files.values() if s['run_id'].startswith('dtc_rerun_')]
    if dtc_results:
        f_groups = {}
        for r in dtc_results:
            f = r['f']
            if f not in f_groups:
                f_groups[f] = {'FRAG': 0, 'STABLE': 0}
            f_groups[f][r['status']] += 1

        f_values = sorted(f_groups.keys())
        frag_frac = [f_groups[f]['FRAG'] / (f_groups[f]['FRAG'] + f_groups[f]['STABLE']) for f in f_values]

        ax2.plot(f_values, frag_frac, 'o-', color='black', markersize=8, linewidth=1.5)
        ax2.set_xlabel('Line-mass $f$')
        ax2.set_ylabel('Fragmentation fraction')
        ax2.set_title('DTC Re-run Results')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(-0.1, 1.1)

    # Subplot 3: Resolution convergence
    ax3 = axes[1, 0]
    res_sims = [s for s in run_list['simulations'] if s['priority'] == 2]
    comparisons = []

    for sim in res_sims:
        run_id = sim['run_id']
        if run_id in status_files:
            status_256 = status_files[run_id]
            tfrag_256 = status_256.get('t_frag')
            tfrag_128 = sim.get('ref_tfrag_128')

            if tfrag_256 and tfrag_128 and status_256['status'] == 'FRAG':
                rel_diff = abs(tfrag_256 - tfrag_128) / tfrag_128
                comparisons.append(rel_diff * 100)  # Convert to percentage

    if comparisons:
        bars = ax3.bar(range(len(comparisons)), comparisons, color=['green' if c < 5 else 'red' for c in comparisons])
        ax3.axhline(y=5, color='black', linestyle='--', linewidth=1)
        ax3.set_xlabel('Parameter Point')
        ax3.set_ylabel('Relative Difference [\%]')
        ax3.set_title('Resolution Convergence')
        ax3.grid(True, alpha=0.3, axis='y')

    # Subplot 4: Summary statistics
    ax4 = axes[1, 1]
    ax4.axis('off')

    dtc_frag_frac = sum(1 for s in dtc_results if s['status'] == 'FRAG') / len(dtc_results) if dtc_results else 0
    res_conv_rate = sum(1 for c in comparisons if c < 5) / len(comparisons) if comparisons else 0

    summary_text = f"""
    Campaign Summary

    Total simulations: {total}

    DTC Re-runs: {len(dtc_results)}
    Fragmentation rate: {dtc_frag_frac*100:.1f}\%

    Resolution tests: {len(comparisons)}
    Convergence rate: {res_conv_rate*100:.1f}\%
    """

    ax4.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment='center', family='monospace')

    # Tight layout
    plt.tight_layout()

    # Save figure
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fig_path = os.path.join(OUTPUT_DIR, 'summary_dashboard.pdf')
    plt.savefig(fig_path, format='pdf', bbox_inches='tight')
    plt.savefig(fig_path.replace('.pdf', '.png'), format='png', bbox_inches='tight', dpi=300)

    print(f"Saved: {fig_path}")

    plt.close()

def main():
    """Main plotting workflow."""
    print("Generating Analysis Figures")
    print("=" * 60)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load data
    print("Loading simulation results...")
    status_files = load_status_files()

    if not status_files:
        print("Error: No status files found. Run simulations first.")
        sys.exit(1)

    with open(RUN_LIST_PATH, 'r') as f:
        run_list = json.load(f)

    print(f"Loaded {len(status_files)} status files")

    # Generate figures
    print("\nGenerating DTC fragmentation fraction plot...")
    plot_dtc_frag_fraction(status_files)

    print("Generating DTC t_frag distribution plot...")
    plot_dtc_tfrag_distribution(status_files)

    print("Generating resolution comparison plot...")
    plot_resolution_scatter(status_files, run_list)

    print("Generating summary dashboard...")
    plot_summary_dashboard(status_files, run_list)

    print("\nFigure generation complete!")
    print(f"Figures saved to {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
