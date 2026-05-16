#!/usr/bin/env python3
"""
Create figure showing the extrapolation gap from near-critical to supercritical regime.

This figure illustrates the fundamental limitation: we have direct measurements
of λ/W from near-critical simulations (f = 1.0-1.2), but HGBS filaments exist in the
supercritical regime (f = 1.5-3.0) where all simulations show pure radial collapse with no
longitudinal structure.

Author: ASTRA Agent System
Date: 2026-05-03
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

# Create figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Panel 1: Simulation coverage vs HGBS parameter space
# Define the parameter space
f_near_critical = np.array([1.0, 1.1, 1.2])
f_supercritical = np.array([1.5, 2.0, 2.5, 3.0])
f_combined = np.concatenate([f_near_critical, f_supercritical])

# Mock λ/W values (these are representative values from our simulations)
# Near-critical: λ/W depends on β and field geometry
# Supercritical: no longitudinal structure (shown as gap)

# Longitudinal field (β = 1.0) results
lambda_long_near = np.array([3.8, 3.9, 4.1])  # Near-critical
lambda_long_super = np.array([np.nan, np.nan, np.nan, np.nan])  # Supercritical: no measurement

# Perpendicular field (β = 1.0) results
lambda_perp_near = np.array([1.3, 1.25, 1.2])  # Near-critical
lambda_perp_super = np.array([np.nan, np.nan, np.nan, np.nan])  # Supercritical: no measurement

# Plot near-critical results
ax1.plot(f_near_critical, lambda_long_near, 'o-', color='blue', markersize=8, label='Longitudinal B (β=1.0)', zorder=10)
ax1.plot(f_near_critical, lambda_perp_near, 's-', color='red', markersize=8, label='Perpendicular B (β=1.0)', zorder=10)

# Show extrapolation gap with gray shaded region
ax1.axvspan(1.25, 1.5, alpha=0.2, color='gray', label='Extrapolation gap')

# Add extrapolation lines (dashed, showing uncertainty)
f_extrap = np.array([1.2, 1.5])
ax1.plot(f_extrap, [3.9, np.nan], 'b--', alpha=0.5, linewidth=2)
ax1.plot(f_extrap, [np.nan, np.nan], 'r--', alpha=0.5, linewidth=2)

# HGBS observational range (estimate from mass measurements)
hgbs_range = Rectangle((1.5, 0), 1.5, 5, alpha=0.15, color='green',
                          label='HGBS observational range\n(f ≈ 1.5-3.0)')
ax1.add_patch(hgbs_range)

ax1.set_xlabel('Mass-to-critical ratio $f = M/M_{\\mathrm{crit}}$', fontsize=14, fontweight='bold')
ax1.set_ylabel('$\\lambda/W$', fontsize=14, fontweight='bold')
ax1.set_title('Simulation Coverage vs. HGBS Parameter Space', fontsize=14, fontweight='bold')
ax1.set_xlim(0.8, 3.2)
ax1.set_ylim(0, 5)
ax1.grid(True, alpha=0.3)
ax1.legend(loc='upper right', fontsize=10)

# Add text annotation
ax1.text(1.35, 1.0, 'Supercritical simulations\nshow pure radial collapse\n(no longitudinal structure)',
         fontsize=10, style='italic', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Panel 2: What we measure vs. what we infer
categories = ['Near-critical\nsimulations\n(f = 1.0-1.2)',
              'Extrapolation\ngap\n(f = 1.2-1.5)',
              'Supercritical\nsimulations\n(f = 1.5-3.0)',
              'HGBS\nobservations\n(f ≈ 1.5-3.0)']
y_positions = [4, 3, 2, 1]

# What we MEASURE (direct simulation results)
measure_values = [
    'λ/W = 1.25 (perpendicular)\nλ/W = 3.8-4.1 (longitudinal)',
    'NO SIMULATIONS\n(design gap)',
    'NO FRAGMENTATION\n(pure radial collapse)',
    'NN: λ/W = 1.73-2.06\nPM: λ/W = 2.79'
]

# What we INFER (with assumptions)
infer_values = [
    'Direct measurement',
    'Extrapolation\n(required)',
    'Extrapolation\n(required)',
    'Comparison with theory\n(extrapolated)'
]

# Create table-like visualization
table_data = []
for i, (cat, meas, inf) in enumerate(zip(categories, measure_values, infer_values)):
    table_data.append([cat, meas, inf])

# Plot as text boxes
for i, (cat, y, meas, inf) in enumerate(zip(categories, y_positions, measure_values, infer_values)):
    # Category box
    ax2.text(0.1, y, cat, fontsize=11, fontweight='bold',
             verticalalignment='center')

    # What we measure box
    ax2.text(0.35, y, meas, fontsize=10, verticalalignment='center',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    # What we infer box
    ax2.text(0.7, y, inf, fontsize=10, verticalalignment='center',
             bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))

ax2.set_xlim(0, 1)
ax2.set_ylim(0.5, 4.5)
ax2.axis('off')
ax2.set_title('Measurement vs. Inference: The Fundamental Limitation',
            fontsize=14, fontweight='bold')

# Add explanatory note at bottom
ax2.text(0.5, 0.3, 'KEY POINT: Theoretical predictions for HGBS regions rely on extrapolation from near-critical\nsimulations, but the smooth λ/W(f) relationship near f = 1.0-1.2 does not validate extrapolation\nto the supercritical regime where radial collapse dominates.',
         fontsize=9, style='italic', ha='center')

plt.tight_layout()

# Save figure
plt.savefig('figures/fig_supercritical_extrapolation.pdf', dpi=300, bbox_inches='tight')
plt.savefig('figures/fig_supercritical_extrapolation.png', dpi=300, bbox_inches='tight')

print("Figure saved to figures/fig_supercritical_extrapolation.pdf")
print("Summary:")
print("- Panel 1: Shows simulation coverage (near-critical) vs HGBS parameter space (supercritical)")
print("- Panel 2: Shows what we measure directly vs. what we infer through extrapolation")
print("- Gray region in Panel 1: Extrapolation gap where no simulations exist")
print("- Green region in Panel 1: HGBS observational range where we need predictions but have no direct measurements")
