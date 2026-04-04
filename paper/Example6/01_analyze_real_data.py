#!/usr/bin/env python3
"""
Test Case 6: Discovery-Mode Analysis on SDSS-like Galaxy Data
=============================================================

This test case demonstrates ASTRA's discovery-mode operation using
realistic galaxy data based on published SDSS scaling relations.

The data is generated using empirical relations from the literature:
- Kauffmann et al. 2003: galaxy property distributions
- Tremonti et al. 2004: mass-metallicity relation
- Brinchmann et al. 2004: star formation main sequence

This demonstrates ASTRA's ability to:
1. Recover known astrophysical relations (validation)
2. Identify outliers and interesting objects (discovery)
3. Generate testable hypotheses for follow-up
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
from sklearn.ensemble import IsolationForest

DATA_DIR = Path('/Users/gjw255/astrodata/SWARM/ASTRA/RASTI_AI')
FIGURES_DIR = Path('/Users/gjw255/astrodata/SWARM/ASTRA/RASTI_paper/Example6/figures')
FIGURES_DIR.mkdir(exist_ok=True, parents=True)

print("=" * 70)
print("TEST CASE 6: Discovery-Mode Analysis on SDSS-like Galaxy Data")
print("=" * 70)

# Load data
df = pd.read_csv(DATA_DIR / 'sdss_galaxies_realistic.csv')
print(f"\n[DATA] Loaded {len(df)} galaxies")
print(f"  Mass range: {df['log_mass'].min():.2f} - {df['log_mass'].max():.2f} log M_sun")
print(f"  SFR range: {df['sfr'].min():.2f} - {df['sfr'].max():.2f} log SFR")
print(f"  Redshift range: {df['redshift'].min():.3f} - {df['redshift'].max():.3f}")

# ============================================================================
# Analysis 1: Recover the Star-Forming Main Sequence (Validation)
# ============================================================================

print("\n[ANALYSIS 1] Star-Forming Main Sequence")
print("-" * 50)

# Fit the main sequence (excluding quenched galaxies)
sf_mask = df['sfr'] > -1  # Star-forming
sf_galaxies = df[sf_mask]

# Linear fit: log SFR vs log mass
slope, intercept, r_value, p_value, std_err = stats.linregress(
    sf_galaxies['log_mass'], sf_galaxies['sfr']
)

print(f"Main Sequence: log SFR = {slope:.2f} * log Mass + {intercept:.2f}")
print(f"  Correlation: r = {r_value:.3f}, p < {p_value:.3e}")
print(f"  Expected: slope ~0.8 (Elbaz et al. 2007)")

# ============================================================================
# Analysis 2: Recover Mass-Metallicity Relation (Validation)
# ============================================================================

print("\n[ANALYSIS 2] Mass-Metallicity Relation")
print("-" * 50)

slope_mz, intercept_mz, r_mz, p_mz, _ = stats.linregress(
    df['log_mass'], df['metallicity']
)

print(f"Mass-Metallicity: 12+log(O/H) = {slope_mz:.2f} * log Mass + {intercept_mz:.2f}")
print(f"  Correlation: r = {r_mz:.3f}, p < {p_mz:.3e}")
print(f"  Expected: slope ~0.3 (Tremonti et al. 2004)")

# ============================================================================
# Analysis 3: Discovery Mode - Identify Outliers and Interesting Objects
# ============================================================================

print("\n[ANALYSIS 3] Discovery Mode - Outlier Detection")
print("-" * 50)

# Use isolation forest to detect outliers in multi-dimensional space
features = ['log_mass', 'sfr', 'metallicity', 'color_gr', 'ssfr']
X = df[features].values

iso_forest = IsolationForest(contamination=0.05, random_state=42)
outliers = iso_forest.fit_predict(X) == -1

print(f"Detected {np.sum(outliers)} outliers ({100*np.mean(outliers):.1f}%)")

# Characterize outliers
outlier_galaxies = df[outliers]

print("\nOutlier categories:")
print(f"  Starbursts in sample: {np.sum(df['is_starburst'])}")
print(f"  Starbursts in outliers: {np.sum(outlier_galaxies['is_starburst'])}")
print(f"  Post-starbursts in sample: {np.sum(df['is_psb'])}")
print(f"  Post-starbursts in outliers: {np.sum(outlier_galaxies['is_psb'])}")
print(f"  Quenched in sample: {np.sum(df['is_quenched'])}")
print(f"  Quenched in outliers: {np.sum(outlier_galaxies['is_quenched'])}")

# Identify galaxies above/below the main sequence
sf_galaxies['ms_residual'] = sf_galaxies['sfr'] - (slope * sf_galaxies['log_mass'] + intercept)
ms_outliers = np.abs(sf_galaxies['ms_residual']) > 1.0  # >1 dex from MS

print(f"\nMain Sequence outliers (>1 dex): {np.sum(ms_outliers)}")
print(f"  Above MS (starbursts): {np.sum(sf_galaxies['ms_residual'] > 1.0)}")
print(f"  Below MS (quenched/transitioning): {np.sum(sf_galaxies['ms_residual'] < -1.0)}")

# ============================================================================
# Generate Figures
# ============================================================================

plt.style.use('default')
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10

# Figure 1: Main Sequence with outliers
fig1, ax = plt.subplots(figsize=(10, 8))

# Plot star-forming galaxies
scatter = ax.scatter(sf_galaxies['log_mass'], sf_galaxies['sfr'],
                     c=sf_galaxies['ssfr'], cmap='RdYlBu_r',
                     alpha=0.6, s=20, edgecolors='none',
                     vmin=-12, vmax=-8)

# Plot main sequence fit
mass_range = np.linspace(sf_galaxies['log_mass'].min(), sf_galaxies['log_mass'].max(), 100)
ax.plot(mass_range, slope * mass_range + intercept, 'k--',
        linewidth=2, alpha=0.8, label=f'Main Sequence (slope={slope:.2f})')

# Highlight outliers
ms_outlier_mask = np.abs(sf_galaxies['ms_residual']) > 1.0
if np.any(ms_outlier_mask):
    ax.scatter(sf_galaxies.loc[ms_outlier_mask, 'log_mass'],
               sf_galaxies.loc[ms_outlier_mask, 'sfr'],
               c='red', s=50, marker='o', edgecolors='black',
               linewidths=1.5, label=f'MS Outliers ({np.sum(ms_outlier_mask)})')

ax.set_xlabel('Stellar Mass (log $M_*/M_\\odot$)', fontsize=12)
ax.set_ylabel('Star Formation Rate (log SFR)', fontsize=12)
ax.set_title('Star-Forming Main Sequence: Discovery Mode Analysis', fontsize=13, fontweight='bold')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)

cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Specific SFR (yr$^{-1}$)', fontsize=10)

plt.tight_layout()
plt.savefig(FIGURES_DIR / 'figure1_main_sequence_discovery.png', dpi=300)
plt.savefig(FIGURES_DIR / 'figure1_main_sequence_discovery.pdf')
print(f"\n✓ Saved: figure1_main_sequence_discovery.png/pdf")

# Figure 2: Mass-Metallicity Relation
fig2, ax = plt.subplots(figsize=(10, 8))

scatter2 = ax.scatter(df['log_mass'], df['metallicity'],
                      c=df['sfr'], cmap='viridis',
                      alpha=0.6, s=20, edgecolors='none')

ax.plot(mass_range, slope_mz * mass_range + intercept_mz, 'r--',
        linewidth=2, alpha=0.8, label=f'Mass-Metallicity (slope={slope_mz:.2f})')

ax.set_xlabel('Stellar Mass (log $M_*/M_\\odot$)', fontsize=12)
ax.set_ylabel('Gas Phase Metallicity (12 + log O/H)', fontsize=12)
ax.set_title('Mass-Metallicity Relation', fontsize=13, fontweight='bold')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)

cbar2 = plt.colorbar(scatter2, ax=ax)
cbar2.set_label('Star Formation Rate (log SFR)', fontsize=10)

plt.tight_layout()
plt.savefig(FIGURES_DIR / 'figure2_mass_metallicity.png', dpi=300)
plt.savefig(FIGURES_DIR / 'figure2_mass_metallicity.pdf')
print(f"✓ Saved: figure2_mass_metallicity.png/pdf")

# Figure 3: Outlier Analysis
fig3, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left panel: SSFR distribution
ax = axes[0]
ax.hist(df['ssfr'], bins=50, alpha=0.7, color='steelblue', edgecolor='black')
ax.axvline(-11, color='red', linestyle='--', linewidth=2, label='Star-forming/Quenched boundary')
ax.set_xlabel('Specific SFR (log yr$^{-1}$)', fontsize=12)
ax.set_ylabel('Number of Galaxies', fontsize=12)
ax.set_title('Specific SFR Distribution', fontsize=13, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# Right panel: Color-Mass diagram with outliers
ax = axes[1]
scatter3 = ax.scatter(df['log_mass'], df['color_gr'],
                      c=df['ssfr'], cmap='RdYlBu_r',
                      alpha=0.6, s=20, edgecolors='none',
                      vmin=-12, vmax=-8)

if np.any(outliers):
    ax.scatter(df.loc[outliers, 'log_mass'], df.loc[outliers, 'color_gr'],
               c='red', s=50, marker='o', edgecolors='black',
               linewidths=1.5, label=f'Outliers ({np.sum(outliers)})')

ax.set_xlabel('Stellar Mass (log $M_*/M_\\odot$)', fontsize=12)
ax.set_ylabel('Color $(g-r)$', fontsize=12)
ax.set_title('Color-Mass Diagram with Outlier Detection', fontsize=13, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

cbar3 = plt.colorbar(scatter3, ax=ax)
cbar3.set_label('Specific SFR (log yr$^{-1}$)', fontsize=10)

plt.tight_layout()
plt.savefig(FIGURES_DIR / 'figure3_outlier_analysis.png', dpi=300)
plt.savefig(FIGURES_DIR / 'figure3_outlier_analysis.pdf')
print(f"✓ Saved: figure3_outlier_analysis.png/pdf")

print("\n" + "=" * 70)
print("DISCOVERY ANALYSIS COMPLETE")
print("=" * 70)
print("\nSummary of Discoveries:")
print(f"1. Recovered star-forming main sequence: slope = {slope:.2f} (expected ~0.8)")
print(f"2. Recovered mass-metallicity relation: slope = {slope_mz:.2f} (expected ~0.3)")
print(f"3. Identified {np.sum(outliers)} outlier galaxies requiring follow-up:")
print(f"   - {np.sum(outlier_galaxies['is_starburst'])} starbursts")
print(f"   - {np.sum(outlier_galaxies['is_psb'])} post-starbursts")
print(f"   - {np.sum(outlier_galaxies['is_quenched'])} unusual quenched galaxies")
print(f"   - {np.sum(ms_outliers)} main sequence outliers")
print("=" * 70)
