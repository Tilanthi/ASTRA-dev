#!/usr/bin/env python3
"""
Generate Figure 1: Core spacing comparison with Gaia DR3 distances

This script creates the spacing comparison figure with updated Gaia DR3 values.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams

# Set up figure parameters for MNRAS
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman']
rcParams['font.size'] = 10
rcParams['axes.linewidth'] = 1.0
rcParams['xtick.major.width'] = 1.0
rcParams['ytick.major.width'] = 1.0

# HGBS region data with Gaia DR3 distances
regions = ['Orion B', 'Aquila', 'Perseus', 'Taurus', 'Ophiuchus', 'Serpens', 'TMC1', 'CRA']
distances = np.array([386, 436, 296, 135, 137, 458, 135, 150])  # pc (Gaia DR3)
n_cores = np.array([1844, 749, 816, 536, 513, 194, 178, 239])
spacings = np.array([0.313, 0.346, 0.248, 0.198, 0.206, 0.331, 0.195, 0.248])  # pc (Gaia DR3)
std_errors = np.array([0.047, 0.047, 0.040, 0.040, 0.053, 0.097, 0.056, 0.072])  # pc
status = ['Robust', 'Robust', 'Robust', 'Robust', 'Limited', 'Limited', 'Limited', 'Limited']

# Weighted mean (from Table 1)
weighted_mean = 0.279  # pc
weighted_mean_error = 0.009  # pc

# 3D-corrected value
spacing_3d = 0.35  # pc (approximately 3.5 * 0.1 pc)

# Theoretical IM92 prediction
im92_prediction = 0.4  # pc (4 * 0.1 pc)

# Literature values for comparison
literature_regions = ['Aquila (K15)', 'Perseus (A16)', 'Orion B fiber (Y24)']
literature_spacings = [0.24, 0.24, 0.42]
literature_errors = [0.02, 0.02, 0.03]

# Create figure with two panels
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Left panel: HGBS region spacings
x_pos = np.arange(len(regions))
colors = ['#1f77b4' if s == 'Robust' else '#7f7f7f' for s in status]

bars = ax1.bar(x_pos, spacings, yerr=std_errors, capsize=5, color=colors,
               edgecolor='black', linewidth=0.8, alpha=0.8)

# Add weighted mean line
ax1.axhline(y=weighted_mean, color='red', linestyle='--', linewidth=2,
            label=f'Weighted mean: {weighted_mean:.3f} ± {weighted_mean_error:.3f} pc')

# Add 3D-corrected line
ax1.axhline(y=spacing_3d, color='green', linestyle=':', linewidth=2,
            label=f'3D-corrected: ~{spacing_3d:.2f} pc')

# Add IM92 prediction
ax1.axhline(y=im92_prediction, color='gray', linestyle='-.', linewidth=2,
            label=f'IM92 theory: ~{im92_prediction:.1f} pc')

ax1.set_xlabel('HGBS Region', fontweight='bold')
ax1.set_ylabel('Core Spacing (pc)', fontweight='bold')
ax1.set_title('HGBS Core Spacings (Gaia DR3 Distances)', fontweight='bold')
ax1.set_xticks(x_pos)
ax1.set_xticklabels(regions, rotation=45, ha='right')
ax1.set_ylim(0, 0.5)
ax1.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax1.grid(axis='y', alpha=0.3)

# Add sample size annotations
for i, (x, n) in enumerate(zip(x_pos, n_cores)):
    ax1.text(x, spacings[i] + std_errors[i] + 0.01, f'n={n}',
             ha='center', va='bottom', fontsize=8, color='black')

# Right panel: Comparison with literature
x_lit = np.arange(len(literature_regions))
width = 0.35

# Our measurements (matching regions)
our_matching = [0.346, 0.248, 0.313]  # Aquila, Perseus, Orion B
our_matching_err = [0.047, 0.040, 0.047]

bars1 = ax2.bar(x_lit - width/2, our_matching, width, yerr=our_matching_err,
                capsize=5, label='This work (Gaia DR3)', color='#1f77b4',
                edgecolor='black', linewidth=0.8, alpha=0.8)

bars2 = ax2.bar(x_lit + width/2, literature_spacings, width, yerr=literature_errors,
                capsize=5, label='Literature', color='#ff7f0e',
                edgecolor='black', linewidth=0.8, alpha=0.8)

# Add reference lines
ax2.axhline(y=weighted_mean, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
ax2.axhline(y=im92_prediction, color='gray', linestyle='-.', linewidth=1.5, alpha=0.7)
ax2.axhline(y=spacing_3d, color='green', linestyle=':', linewidth=1.5, alpha=0.7)

ax2.set_xlabel('Region / Measurement', fontweight='bold')
ax2.set_ylabel('Core Spacing (pc)', fontweight='bold')
ax2.set_title('Comparison with Published Measurements', fontweight='bold')
ax2.set_xticks(x_lit)
ax2.set_xticklabels(literature_regions, rotation=25, ha='right')
ax2.set_ylim(0, 0.5)
ax2.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax2.grid(axis='y', alpha=0.3)

# Add value annotations on bars
for i, (our, lit) in enumerate(zip(our_matching, literature_spacings)):
    ax2.text(i - width/2, our + our_matching_err[i] + 0.01, f'{our:.3f}',
             ha='center', va='bottom', fontsize=7, color='black')
    ax2.text(i + width/2, lit + literature_errors[i] + 0.01, f'{lit:.2f}',
             ha='center', va='bottom', fontsize=7, color='black')

# Create legend for status colors
robust_patch = mpatches.Patch(color='#1f77b4', label='Robust (N>550)')
limited_patch = mpatches.Patch(color='#7f7f7f', label='Limited (N<500)')
ax1.legend(handles=[bars.patches[0], robust_patch, limited_patch],
           loc='upper left', fontsize=9, framealpha=0.9)

plt.tight_layout()

# Save figure
output_path = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/figures/figure1_spacing_comparison.pdf'
plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
print(f"✓ Figure 1 saved to {output_path}")

# Also save as PNG for preview
png_path = output_path.replace('.pdf', '.png')
plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
print(f"✓ Figure 1 PNG saved to {png_path}")

plt.close()

print("\nFigure 1 Summary:")
print(f"  Weighted mean: {weighted_mean:.3f} ± {weighted_mean_error:.3f} pc")
print(f"  3D-corrected: ~{spacing_3d:.2f} pc")
print(f"  IM92 prediction: ~{im92_prediction:.1f} pc")
print(f"  Ratio to filament width: {weighted_mean/0.1:.2f}× (2D), {spacing_3d/0.1:.1f}× (3D)")
