#!/usr/bin/env python3
"""
Analysis 3: Perpendicular-Field Suppression vs Turbulence
Addresses additional question: Does turbulence overcome perpendicular suppression?
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
    df = df[df['status'] == 'completed'].copy()

    # Convert numeric columns
    numeric_cols = ['f', 'beta', 'mturb', 'theta', 'lW', 't_frag']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def analyze_perpendicular_turbulence(df):
    """
    Analysis 3: Perpendicular-Field Suppression vs Turbulence

    Addresses question: Does turbulence overcome perpendicular-field suppression?
    Previous result: 99.5% suppression rate (laminar regime)
    Question: Does turbulence enable longitudinal fragmentation at Mturb = 2-4?

    Expected outcomes:
    - If fragmentation fraction increases with Mturb: Turbulence overcomes suppression
    - If suppression persists at high Mturb: Perpendicular geometry fundamentally different
    """

    print("\n" + "="*80)
    print("ANALYSIS 3: PERPENDICULAR-FIELD SUPPRESSION vs TURBULENCE")
    print("="*80)

    # Filter perpendicular field
    perpendicular = df[df['theta'] == 90].copy()

    if len(perpendicular) == 0:
        print("ERROR: No perpendicular-field simulations found!")
        return None

    print(f"\nPerpendicular-field simulations: {len(perpendicular)}")

    # Calculate fragmentation fraction vs Mturb
    print("\n--- Fragmentation Fraction vs Mturb (Perpendicular Field) ---")

    # Define fragmentation: morphology is not RADIAL_ONLY or lW is detected
    if 'morphology' in perpendicular.columns:
        perpendicular['fragmented'] = perpendicular['morphology'] != 'RADIAL_ONLY'
    elif 'lW' in perpendicular.columns:
        perpendicular['fragmented'] = perpendicular['lW'].notna() & (perpendicular['lW'] != 'NO_BEADING')
    else:
        print("ERROR: No morphology or lW data available")
        return None

    frag_by_mturb = perpendicular.groupby('mturb')['fragmented'].agg(['mean', 'sum', 'count'])

    for mturb in sorted(perpendicular['mturb'].unique()):
        subset = perpendicular[perpendicular['mturb'] == mturb]
        if len(subset) > 0:
            frac_frag = subset['fragmented'].mean()
            count_frag = subset['fragmented'].sum()
            print(f"Mturb = {mturb:.1f}: {frac_frag:.2%} fragmented ({count_frag}/{len(subset)})")

    # Compare with laminar baseline (99.5% suppression = 0.5% fragmentation)
    laminar_frag = 0.005
    print(f"\nLaminar baseline: {laminar_frag:.2%} fragmented (99.5% suppression)")

    # Chi-squared test: Does fragmentation depend on Mturb?
    cont_table = pd.crosstab(perpendicular['mturb'], perpendicular['fragmented'])
    if cont_table.shape[1] == 2:  # Both fragmented and non-fragmented
        chi2, p, dof, expected = stats.chi2_contingency(cont_table)
        print(f"\n--- Chi-squared Test: Fragmentation vs Mturb ---")
        print(f"Chi-squared: {chi2:.3f}")
        print(f"P-value: {p:.4f}")

        if p < 0.05:
            print(f"-> SIGNIFICANT: Fragmentation depends on Mturb (p < 0.05)")
            print(f"-> Turbulence affects perpendicular-field behavior")
        else:
            print(f"-> NOT significant: Fragmentation independent of Mturb")
            print(f"-> Perpendicular suppression robust to turbulence")

    # Calculate overall fragmentation fraction
    overall_frag = perpendicular['fragmented'].mean()
    overall_count = perpendicular['fragmented'].sum()

    print(f"\n--- Overall Perpendicular-Field Fragmentation ---")
    print(f"Total fragmented: {overall_frag:.2%} ({overall_count}/{len(perpendicular)})")

    if overall_frag > 0.05:
        print(f"-> Fragmentation >5%: Turbulence partially overcomes suppression")
    elif overall_frag > 0.01:
        print(f"-> Fragmentation 1-5%: Some turbulence effect")
    else:
        print(f"-> Fragmentation <1%: Perpendicular suppression robust")

    return perpendicular

def plot_perpendicular_turbulence(df, output_dir):
    """Create figures for perpendicular turbulence analysis"""

    perpendicular = df[df['theta'] == 90].copy()

    # Define fragmentation
    if 'morphology' in perpendicular.columns:
        perpendicular['fragmented'] = perpendicular['morphology'] != 'RADIAL_ONLY'
    elif 'lW' in perpendicular.columns:
        perpendicular['fragmented'] = perpendicular['lW'].notna() & (perpendicular['lW'] != 'NO_BEADING')
    else:
        print("No fragmentation data to plot")
        return

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Plot 1: Fragmentation fraction vs Mturb
    ax1 = axes[0, 0]
    frag_by_mturb = perpendicular.groupby('mturb')['fragmented'].agg(['mean', 'sum', 'count'])
    ax1.plot(frag_by_mturb.index, frag_by_mturb['mean'], 'o-', markersize=8)
    ax1.axhline(y=0.005, color='r', linestyle='--', linewidth=2, label='Laminar (0.5%)')
    ax1.set_xlabel('Turbulent Mach Number $M_{turb}$', fontsize=12)
    ax1.set_ylabel('Fragmentation Fraction', fontsize=12)
    ax1.set_title('Perpendicular-Field Fragmentation vs Turbulence', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    ax1.set_ylim(0, max(0.1, frag_by_mturb['mean'].max() * 1.2))

    # Plot 2: Fragmentation vs β for different Mturb
    ax2 = axes[0, 1]
    for mturb in [2.0, 3.0, 4.0]:
        subset = perpendicular[perpendicular['mturb'] == mturb]
        if len(subset) > 0:
            frag_by_beta = subset.groupby('beta')['fragmented'].mean()
            ax2.plot(frag_by_beta.index, frag_by_beta.values, 'o-', markersize=6,
                    label=f'$M_{{turb}}$={mturb:.1f}')

    ax2.axhline(y=0.005, color='r', linestyle='--', linewidth=2, label='Laminar')
    ax2.set_xlabel('Plasma $\\beta$', fontsize=12)
    ax2.set_ylabel('Fragmentation Fraction', fontsize=12)
    ax2.set_title('Fragmentation vs Magnetic Field', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)

    # Plot 3: Fragmentation vs f for different Mturb
    ax3 = axes[1, 0]
    for mturb in [2.0, 3.0, 4.0]:
        subset = perpendicular[perpendicular['mturb'] == mturb]
        if len(subset) > 0:
            frag_by_f = subset.groupby('f')['fragmented'].mean()
            ax3.plot(frag_by_f.index, frag_by_f.values, 'o-', markersize=6,
                    label=f'$M_{{turb}}$={mturb:.1f}')

    ax3.axhline(y=0.005, color='r', linestyle='--', linewidth=2, label='Laminar')
    ax3.set_xlabel('Line-mass Fraction $f$', fontsize=12)
    ax3.set_ylabel('Fragmentation Fraction', fontsize=12)
    ax3.set_title('Fragmentation vs Line-mass', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(alpha=0.3)

    # Plot 4: 2D heatmap of fragmentation fraction
    ax4 = axes[1, 1]
    pivot_table = perpendicular.pivot_table(values='fragmented', index='mturb', columns='f', aggfunc='mean')
    if not pivot_table.empty:
        sns.heatmap(pivot_table, annot=True, fmt='.2%', cmap='RdYlGn', vmin=0, vmax=0.1, ax=ax4,
                   cbar_kws={'label': 'Fragmentation Fraction'})
        ax4.set_xlabel('Line-mass Fraction $f$', fontsize=12)
        ax4.set_ylabel('Turbulent Mach Number $M_{turb}$', fontsize=12)
        ax4.set_title('Fragmentation Heatmap', fontsize=14, fontweight='bold')

    plt.tight_layout()
    output_path = Path(output_dir) / "RTC-3_perpendicular_suppression_vs_Mturb.pdf"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved: {output_path}")

    plt.close()

def main():
    """
    Main: Run Analysis 3
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
    perpendicular = analyze_perpendicular_turbulence(df)

    # Create figures
    if perpendicular is not None:
        plot_perpendicular_turbulence(df, output_dir)

    print("\n" + "="*80)
    print("Analysis 3 Complete")
    print("="*80)

if __name__ == "__main__":
    main()
