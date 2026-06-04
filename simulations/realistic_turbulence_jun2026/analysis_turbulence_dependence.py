#!/usr/bin/env python3
"""
Analysis 2: Turbulence Amplitude Dependence
Addresses Referee Concern #2: Does turbulence-independence extend to physical regime?
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

def analyze_turbulence_dependence(df):
    """
    Analysis 2: Turbulence Amplitude Dependence

    Addresses Referee Concern #2:
    - Does λ/W depend on Mturb in physical regime (Mturb = 2-4)?
    - Is turbulence-independence (linear regime) valid at physical amplitudes?

    Expected outcomes:
    - If λ/W independent of Mturb (p > 0.05): Turbulence-independence holds
    - If λ/W depends on Mturb (p < 0.05): Turbulence matters in physical regime
    """

    print("\n" + "="*80)
    print("ANALYSIS 2: TURBULENCE AMPLITUDE DEPENDENCE (Referee Concern #2)")
    print("="*80)

    # Filter longitudinal field only (primary comparison)
    longitudinal = df[(df['theta'] == 0) & (df['lW'].notna())].copy()

    if len(longitudinal) == 0:
        print("ERROR: No longitudinal simulations with λ/W data found!")
        return None

    print(f"\nLongitudinal simulations with λ/W data: {len(longitudinal)}")

    # Calculate mean λ/W vs Mturb
    print("\n--- Mean λ/W vs Mturb (Longitudinal Field) ---")
    lw_by_mturb = longitudinal.groupby('mturb')['lW'].agg(['mean', 'std', 'count'])
    for mturb in sorted(longitudinal['mturb'].unique()):
        subset = longitudinal[longitudinal['mturb'] == mturb]
        if len(subset) > 0:
            mean_lw = subset['lW'].mean()
            std_lw = subset['lW'].std()
            print(f"Mturb = {mturb:.1f}: λ/W = {mean_lw:.3f} ± {std_lw:.3f} (N={len(subset)})")

    # ANOVA: Does λ/W depend on Mturb?
    mturb_values = sorted(longitudinal['mturb'].unique())
    groups = [longitudinal[longitudinal['mturb'] == m]['lW'].dropna().values for m in mturb_values]

    if all(len(g) > 0 for g in groups):
        f_stat, p_value = stats.f_oneway(*groups)
        print(f"\n--- ANOVA: λ/W vs Mturb ---")
        print(f"F-statistic: {f_stat:.3f}")
        print(f"P-value: {p_value:.4f}")

        if p_value < 0.05:
            print(f"-> SIGNIFICANT: λ/W depends on Mturb (p < 0.05)")
            print(f"-> Referee Concern #2 VALIDATED: Turbulence matters in physical regime")
            print(f"-> Turbulence-independence claim only applies to LINEAR regime")
        else:
            print(f"-> NOT significant: λ/W independent of Mturb (p >= 0.05)")
            print(f"-> Turbulence-independence EXTENDS to physical regime")
            print(f"-> Addresses Referee Concern #2")

    # Linear regression for each β
    print(f"\n--- Linear Regression: λ/W vs Mturb for each β ---")
    for beta in sorted(longitudinal['beta'].unique()):
        subset = longitudinal[longitudinal['beta'] == beta].dropna(subset=['lW', 'mturb'])
        if len(subset) >= 5:
            slope, intercept, r, p, se = stats.linregress(subset['mturb'], subset['lW'])
            print(f"β = {beta:.1f}: slope = {slope:.4f} ± {se:.4f}, r = {r:.3f}, p = {p:.4f}")

            if p < 0.05:
                print(f"  -> SIGNIFICANT Mturb dependence at β = {beta:.1f}")
            else:
                print(f"  -> No significant Mturb dependence at β = {beta:.1f}")

    # Compare with HGBS
    hgb_value = 2.51
    print(f"\n--- Comparison with HGBS (λ/W = {hgb_value:.2f}) ---")
    for mturb in sorted(longitudinal['mturb'].unique()):
        subset = longitudinal[longitudinal['mturb'] == mturb]
        if len(subset) > 0:
            mean_lw = subset['lW'].mean()
            std_lw = subset['lW'].std()
            z_score = abs(mean_lw - hgb_value) / std_lw if std_lw > 0 else 0
            print(f"Mturb = {mturb:.1f}: λ/W = {mean_lw:.3f} ± {std_lw:.3f}")
            print(f"  Difference from HGBS: {abs(mean_lw - hgb_value):.3f} ({z_score:.1f}σ)")

    return longitudinal

def plot_turbulence_dependence(df, output_dir):
    """Create figures for turbulence dependence analysis"""

    longitudinal = df[(df['theta'] == 0) & (df['lW'].notna())].copy()

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Plot 1: λ/W vs Mturb (longitudinal)
    ax1 = axes[0, 0]
    for beta in sorted(longitudinal['beta'].unique()):
        subset = longitudinal[longitudinal['beta'] == beta]
        if len(subset) > 0:
            lw_by_mturb = subset.groupby('mturb')['lW'].agg(['mean', 'std'])
            ax1.errorbar(lw_by_mturb.index, lw_by_mturb['mean'], yerr=lw_by_mturb['std'],
                         fmt='o-', capsize=5, markersize=6, label=f'$\\beta$={beta:.1f}')

    ax1.axhline(y=2.51, color='k', linestyle='--', linewidth=2, label='HGBS value')
    ax1.set_xlabel('Turbulent Mach Number $M_{turb}$', fontsize=12)
    ax1.set_ylabel('Fragmentation Scale $\\lambda/W$', fontsize=12)
    ax1.set_title('λ/W vs Turbulence (Longitudinal B)', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)

    # Plot 2: λ/W vs β for different Mturb
    ax2 = axes[0, 1]
    for mturb in [2.0, 3.0, 4.0]:
        subset = longitudinal[longitudinal['mturb'] == mturb]
        if len(subset) > 0:
            lw_by_beta = subset.groupby('beta')['lW'].agg(['mean', 'std'])
            ax2.errorbar(lw_by_beta.index, lw_by_beta['mean'], yerr=lw_by_beta['std'],
                         fmt='o-', capsize=5, markersize=6, label=f'$M_{{turb}}$={mturb:.1f}')

    ax2.axhline(y=2.51, color='k', linestyle='--', linewidth=2, label='HGBS value')
    ax2.set_xlabel('Plasma $\\beta$', fontsize=12)
    ax2.set_ylabel('Fragmentation Scale $\\lambda/W$', fontsize=12)
    ax2.set_title('λ/W vs Magnetic Field Strength', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)

    # Plot 3: Coefficient of variation vs Mturb
    ax3 = axes[1, 0]
    cv_by_mturb = longitudinal.groupby('mturb')['lW'].agg(lambda x: x.std() / x.mean() if x.mean() > 0 else 0)
    ax3.plot(cv_by_mturb.index, cv_by_mturb.values, 'o-', markersize=8)
    ax3.set_xlabel('Turbulent Mach Number $M_{turb}$', fontsize=12)
    ax3.set_ylabel('Coefficient of Variation $\\sigma/\\mu$', fontsize=12)
    ax3.set_title('Scatter vs Turbulence', fontsize=14, fontweight='bold')
    ax3.grid(alpha=0.3)

    # Plot 4: 2D heatmap (λ/W vs Mturb and β)
    ax4 = axes[1, 1]
    pivot_table = longitudinal.pivot_table(values='lW', index='mturb', columns='beta', aggfunc='mean')
    if not pivot_table.empty:
        sns.heatmap(pivot_table, annot=True, fmt='.2f', cmap='viridis', ax=ax4, cbar_kws={'label': '$\\lambda/W$'})
        ax4.set_xlabel('Plasma $\\beta$', fontsize=12)
        ax4.set_ylabel('Turbulent Mach Number $M_{turb}$', fontsize=12)
        ax4.set_title('λ/W Heatmap', fontsize=14, fontweight='bold')

    plt.tight_layout()
    output_path = Path(output_dir) / "RTC-2_lW_vs_Mturb_physical.pdf"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved: {output_path}")

    plt.close()

def main():
    """
    Main: Run Analysis 2
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
    longitudinal = analyze_turbulence_dependence(df)

    # Create figures
    if longitudinal is not None:
        plot_turbulence_dependence(df, output_dir)

    print("\n" + "="*80)
    print("Analysis 2 Complete")
    print("="*80)

if __name__ == "__main__":
    main()
