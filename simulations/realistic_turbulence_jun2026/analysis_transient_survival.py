#!/usr/bin/env python3
"""
Analysis 1: Transient Peak Survival
Addresses Referee Concern #1: Do transient peaks survive long enough to form bound cores?
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path

def load_results(results_file):
    """Load campaign results"""
    df = pd.read_csv(results_file)

    # Filter completed simulations
    df = df[df['status'] == 'completed'].copy()

    # Convert numeric columns
    numeric_cols = ['f', 'beta', 'mturb', 'theta', 'lW', 't_frag', 'tau_peak']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def analyze_transient_survival(df):
    """
    Analysis 1: Transient Peak Survival

    Addresses Referee Concern #1:
    - Does turbulence increase transient peak survival time?
    - Do peaks survive long enough to form bound cores (τ_peak ≥ 0.1 tJ)?

    Expected outcomes:
    - If τ_peak increases with Mturb: Turbulence enables longer peak survival
    - If τ_peak ≥ 0.1 tJ for significant fraction: Peaks can form bound cores
    """

    print("\n" + "="*80)
    print("ANALYSIS 1: TRANSIENT PEAK SURVIVAL (Referee Concern #1)")
    print("="*80)

    # Filter supercritical filaments (where transient beading is relevant)
    supercritical = df[df['f'] >= 1.5].copy()

    if len(supercritical) == 0:
        print("ERROR: No supercritical simulations found!")
        return None

    print(f"\nSupercritical simulations: {len(supercritical)}")

    # Check if tau_peak data exists
    if 'tau_peak' not in supercritical.columns or supercritical['tau_peak'].isna().all():
        print("ERROR: No tau_peak data available!")
        print("Transient survival analysis requires tau_peak column in results.")
        return None

    # Calculate survival statistics by Mturb
    print("\n--- Survival Fraction vs Mturb ---")
    for mturb in sorted(supercritical['mturb'].unique()):
        subset = supercritical[supercritical['mturb'] == mturb]

        if len(subset) > 0:
            # Count peaks that survive to bound status
            if 'survives_to_bound' in subset.columns:
                survival_frac = subset['survives_to_bound'].mean()
                survival_count = subset['survives_to_bound'].sum()
                print(f"Mturb = {mturb:.1f}: {survival_frac:.2%} survive ({survival_count}/{len(subset)})")

    # Calculate mean tau_peak vs Mturb
    print("\n--- Mean Tau_peak vs Mturb ---")
    for mturb in sorted(supercritical['mturb'].unique()):
        subset = supercritical[supercritical['mturb'] == mturb]
        if len(subset) > 0 and 'tau_peak' in subset.columns:
            mean_tau = subset['tau_peak'].mean()
            std_tau = subset['tau_peak'].std()
            print(f"Mturb = {mturb:.1f}: τ_peak = {mean_tau:.3f} ± {std_tau:.3f} tJ")

    # Linear regression: tau_peak vs Mturb
    valid_data = supercritical.dropna(subset=['tau_peak', 'mturb'])
    if len(valid_data) >= 10:
        slope, intercept, r, p, se = stats.linregress(
            valid_data['mturb'],
            valid_data['tau_peak']
        )
        print(f"\n--- Linear Regression: τ_peak vs Mturb ---")
        print(f"Slope: {slope:.4f} ± {se:.4f} tJ per Mturb")
        print(f"Correlation: r = {r:.3f}")
        print(f"P-value: {p:.4f}")

        if p < 0.05:
            print(f"-> SIGNIFICANT: τ_peak depends on Mturb (p < 0.05)")
            if slope > 0:
                print(f"-> Turbulence INCREASES peak survival time")
            else:
                print(f"-> Turbulence DECREASES peak survival time")
        else:
            print(f"-> NOT significant: τ_peak independent of Mturb (p >= 0.05)")

    # Calculate fraction meeting 0.1 tJ threshold
    if 'tau_peak' in supercritical.columns:
        meets_threshold = supercritical['tau_peak'] >= 0.1
        fraction = meets_threshold.mean()
        count = meets_threshold.sum()
        print(f"\n--- Threshold Analysis (τ_peak ≥ 0.1 tJ) ---")
        print(f"Fraction meeting threshold: {fraction:.2%} ({count}/{len(supercritical)})")

        if fraction >= 0.2:
            print(f"-> SUCCESS: ≥20% of peaks survive long enough for bound cores")
            print(f"-> Addresses Referee Concern #1: THEO-1/HGBS agreement is physically meaningful")
        elif fraction >= 0.05:
            print(f"-> MODERATE: 5-20% of peaks survive long enough")
            print(f"-> Partially addresses Referee Concern #1")
        else:
            print(f"-> FAILURE: <5% of peaks survive long enough")
            print(f"-> Referee Concern #1 VALIDATED: Agreement may be coincidental")

    return supercritical

def plot_transient_survival(df, output_dir):
    """Create figures for transient survival analysis"""

    supercritical = df[df['f'] >= 1.5].copy()

    if 'tau_peak' not in supercritical.columns or supercritical['tau_peak'].isna().all():
        print("No tau_peak data to plot")
        return

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Plot 1: Survival fraction vs Mturb
    ax1 = axes[0, 0]
    if 'survives_to_bound' in supercritical.columns:
        survival_by_mturb = supercritical.groupby('mturb')['survives_to_bound'].mean()
        ax1.plot(survival_by_mturb.index, survival_by_mturb.values, 'o-', markersize=8)
        ax1.axhline(y=0.2, color='r', linestyle='--', label='20% threshold')
        ax1.set_xlabel('Turbulent Mach Number $M_{turb}$', fontsize=12)
        ax1.set_ylabel('Survival Fraction', fontsize=12)
        ax1.set_title('Transient Peak Survival vs Turbulence', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(alpha=0.3)

    # Plot 2: Mean tau_peak vs Mturb
    ax2 = axes[0, 1]
    tau_by_mturb = supercritical.groupby('mturb')['tau_peak'].agg(['mean', 'std'])
    ax2.errorbar(tau_by_mturb.index, tau_by_mturb['mean'], yerr=tau_by_mturb['std'],
                 fmt='o-', capsize=5, markersize=8)
    ax2.axhline(y=0.1, color='r', linestyle='--', label='0.1 tJ threshold')
    ax2.set_xlabel('Turbulent Mach Number $M_{turb}$', fontsize=12)
    ax2.set_ylabel('Mean Peak Lifetime $\\tau_{peak}$ [$t_J$]', fontsize=12)
    ax2.set_title('Transient Peak Lifetime vs Turbulence', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)

    # Plot 3: Distribution of tau_peak for different Mturb
    ax3 = axes[1, 0]
    for mturb in [2.0, 3.0, 4.0]:
        subset = supercritical[supercritical['mturb'] == mturb]
        if len(subset) > 0 and 'tau_peak' in subset.columns:
            ax3.hist(subset['tau_peak'].dropna(), bins=20, alpha=0.5, label=f'$M_{{turb}}$={mturb:.1f}')
    ax3.axvline(x=0.1, color='r', linestyle='--', linewidth=2, label='0.1 tJ threshold')
    ax3.set_xlabel('Peak Lifetime $\\tau_{peak}$ [$t_J$]', fontsize=12)
    ax3.set_ylabel('Count', fontsize=12)
    ax3.set_title('Distribution of Peak Lifetimes', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(alpha=0.3)

    # Plot 4: Survival vs f and beta
    ax4 = axes[1, 1]
    if 'survives_to_bound' in supercritical.columns:
        survival_fb = supercritical.groupby(['f', 'beta'])['survives_to_bound'].mean().reset_index()
        scatter = ax4.scatter(survival_fb['f'], survival_fb['beta'],
                            c=survival_fb['survives_to_bound'], s=100, cmap='RdYlGn', vmin=0, vmax=1)
        ax4.set_xlabel('Line-mass Fraction $f$', fontsize=12)
        ax4.set_ylabel('Plasma $\\beta$', fontsize=12)
        ax4.set_title('Survival vs $f$ and $\\beta$', fontsize=14, fontweight='bold')
        plt.colorbar(scatter, ax=ax4, label='Survival Fraction')
        ax4.grid(alpha=0.3)

    plt.tight_layout()
    output_path = Path(output_dir) / "RTC-1_transient_survival_vs_Mturb.pdf"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved: {output_path}")

    plt.close()

def main():
    """
    Main: Run Analysis 1
    """
    # Paths
    results_file = Path("results/RTC_results_all1200.csv")
    output_dir = Path("results/figures")

    if not results_file.exists():
        print(f"ERROR: Results file not found: {results_file}")
        print("Run rtc_ray_submit.py first to generate results")
        return

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load results
    print(f"Loading results from: {results_file}")
    df = load_results(results_file)
    print(f"Loaded {len(df)} simulations")

    # Run analysis
    supercritical = analyze_transient_survival(df)

    # Create figures
    if supercritical is not None:
        plot_transient_survival(df, output_dir)

    print("\n" + "="*80)
    print("Analysis 1 Complete")
    print("="*80)

if __name__ == "__main__":
    main()
