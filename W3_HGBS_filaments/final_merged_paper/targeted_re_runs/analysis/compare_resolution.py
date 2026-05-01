#!/usr/bin/env python3
"""
Resolution Convergence Analysis

Compares 256^3 simulation results with 128^3 reference values
to assess resolution convergence and quantify resolution uncertainty.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import matplotlib as mpl

# Configuration
STATUS_DIR = "../output/status"
RUN_LIST_PATH = "../simulations/run_list.json"
OUTPUT_DIR = "../output/analysis"
FIGURE_DIR = "../output/figures"

# Set up matplotlib for publication-quality figures
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Latin Modern Roman']
mpl.rcParams['text.usetex'] = True
mpl.rcParams['figure.dpi'] = 300
mpl.rcParams['savefig.dpi'] = 300
mpl.rcParams['axes.linewidth'] = 1.0
mpl.rcParams['xtick.major.width'] = 1.0
mpl.rcParams['ytick.major.width'] = 1.0

def load_run_list() -> Dict:
    """Load simulation specifications."""
    with open(RUN_LIST_PATH, 'r') as f:
        return json.load(f)

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

def compare_resolution(run_list: Dict, status_files: Dict[str, Dict]) -> List[Dict]:
    """
    Compare 256^3 results with 128^3 reference values.

    Returns:
    --------
    comparisons : list of dict
        List of comparison results with keys:
        run_id, f, beta, mach, tfrag_128, tfrag_256, diff, rel_diff, converged
    """
    comparisons = []
    res_sims = [s for s in run_list['simulations'] if s['priority'] == 2]

    for sim in res_sims:
        run_id = sim['run_id']

        if run_id not in status_files:
            continue

        status_256 = status_files[run_id]
        tfrag_256 = status_256.get('t_frag')
        tfrag_128 = sim.get('ref_tfrag_128')

        # Only compare if both values are available
        if tfrag_256 and tfrag_128 and status_256['status'] == 'FRAG':
            diff = tfrag_256 - tfrag_128
            rel_diff = abs(diff) / tfrag_128
            converged = rel_diff < 0.05

            comparisons.append({
                'run_id': run_id,
                'f': sim['f'],
                'beta': sim['beta'],
                'mach': sim['mach'],
                'tfrag_128': tfrag_128,
                'tfrag_256': tfrag_256,
                'diff': diff,
                'rel_diff': rel_diff,
                'converged': converged
            })

    return comparisons

def plot_resolution_comparison(comparisons: List[Dict]):
    """Generate resolution comparison figure."""
    if not comparisons:
        print("No comparisons available for plotting")
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
    os.makedirs(FIGURE_DIR, exist_ok=True)
    fig_path = os.path.join(FIGURE_DIR, 'resolution_comparison.pdf')
    plt.savefig(fig_path, format='pdf', bbox_inches='tight')
    plt.savefig(fig_path.replace('.pdf', '.png'), format='png', bbox_inches='tight', dpi=300)

    print(f"Saved: {fig_path}")

    plt.close()

def plot_resolution_uncertainty(comparisons: List[Dict]):
    """Generate resolution uncertainty plot."""
    if not comparisons:
        print("No comparisons available for plotting")
        return

    # Create figure
    fig, ax = plt.subplots(figsize=(6, 5))

    # Extract data
    f_values = [c['f'] for c in comparisons]
    rel_diffs = [c['rel_diff'] * 100 for c in comparisons]  # Convert to percentage
    colors = ['green' if c['converged'] else 'red' for c in comparisons]

    # Plot bar chart
    bars = ax.bar(range(len(f_values)), rel_diffs, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)

    # Add 5% threshold line
    ax.axhline(y=5, color='black', linestyle='--', linewidth=1, label='5\% threshold')

    # Labels and title
    ax.set_xlabel('Run ID', fontsize=12)
    ax.set_ylabel('Relative Difference [\%]', fontsize=12)
    ax.set_title('Resolution Dependence by Parameter Point', fontsize=14)
    ax.set_xticks(range(len(f_values)))
    ax.set_xticklabels([c['run_id'].split('_')[-1] for c in comparisons], rotation=45, ha='right', fontsize=8)

    # Grid and legend
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.legend(fontsize=10)

    # Tight layout
    plt.tight_layout()

    # Save figure
    os.makedirs(FIGURE_DIR, exist_ok=True)
    fig_path = os.path.join(FIGURE_DIR, 'resolution_uncertainty.pdf')
    plt.savefig(fig_path, format='pdf', bbox_inches='tight')
    plt.savefig(fig_path.replace('.pdf', '.png'), format='png', bbox_inches='tight', dpi=300)

    print(f"Saved: {fig_path}")

    plt.close()

def analyze_resolution_results(comparisons: List[Dict]) -> Dict:
    """Analyze resolution convergence results."""
    if not comparisons:
        return {"error": "No comparisons available"}

    converged = [c for c in comparisons if c['converged']]
    not_converged = [c for c in comparisons if not c['converged']]

    rel_diffs = [c['rel_diff'] for c in comparisons]

    return {
        "total_comparisons": len(comparisons),
        "converged_count": len(converged),
        "not_converged_count": len(not_converged),
        "convergence_rate": len(converged) / len(comparisons),
        "mean_rel_diff": np.mean(rel_diffs),
        "std_rel_diff": np.std(rel_diffs),
        "median_rel_diff": np.median(rel_diffs),
        "max_rel_diff": np.max(rel_diffs),
        "min_rel_diff": np.min(rel_diffs)
    }

def main():
    """Main analysis workflow."""
    print("Resolution Convergence Analysis")
    print("=" * 60)

    # Create output directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FIGURE_DIR, exist_ok=True)

    # Load data
    print("Loading simulation data...")
    run_list = load_run_list()
    status_files = load_status_files()

    # Perform comparisons
    print("Performing resolution comparisons...")
    comparisons = compare_resolution(run_list, status_files)

    if not comparisons:
        print("Error: No resolution comparisons available.")
        print("Check that 256^3 simulations have completed.")
        sys.exit(1)

    print(f"Found {len(comparisons)} valid comparisons")

    # Analyze results
    print("\nAnalyzing convergence...")
    results = analyze_resolution_results(comparisons)

    print(f"Total comparisons: {results['total_comparisons']}")
    print(f"Converged (<5%): {results['converged_count']}")
    print(f"Not converged (>5%): {results['not_converged_count']}")
    print(f"Convergence rate: {results['convergence_rate']*100:.1f}%")
    print(f"Mean relative difference: {results['mean_rel_diff']*100:.2f}% +/- {results['std_rel_diff']*100:.2f}%")

    # Save results
    output_path = os.path.join(OUTPUT_DIR, "resolution_analysis.json")
    with open(output_path, 'w') as f:
        json.dump({"results": results, "comparisons": comparisons}, f, indent=2)

    print(f"\nResults saved to {output_path}")

    # Generate figures
    print("\nGenerating figures...")
    plot_resolution_comparison(comparisons)
    plot_resolution_uncertainty(comparisons)

    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
