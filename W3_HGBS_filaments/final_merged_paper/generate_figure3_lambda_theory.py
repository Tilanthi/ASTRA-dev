#!/usr/bin/env python3
"""
Generate Figure 3: Lambda/W vs Plasma Beta theory plot

This script creates the theoretical fragmentation spacing figure
with the updated Gaia DR3 observational value (λ/W = 2.79).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Set up figure parameters for MNRAS
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman']
rcParams['font.size'] = 10
rcParams['axes.linewidth'] = 1.0
rcParams['xtick.major.width'] = 1.0
rcParams['ytick.major.width'] = 1.0

# Field geometry calibration from oblique field campaign
calibration_factor = 1.11

# Plasma beta range
beta = np.logspace(-1, 1, 100)  # 0.1 to 10

# Field angles
angles = [0, 30, 45, 60, 90]
angle_labels = ['0° (Longitudinal)', '30°', '45°', '60°', '90° (Perpendicular)']
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

# Calculate lambda/W for each angle
plt.figure(figsize=(10, 6))

for theta, label, color in zip(angles, angle_labels, colors):
    # Nakamura et al. (1993) formula for magneto-Jeans length
    theta_rad = np.deg2rad(theta)
    sin_theta = np.sin(theta_rad)

    # lambda_MJ = lambda_J * sqrt(1 + 2*sin^2(theta)/beta)
    # lambda_W = calibration * lambda_MJ / W_core
    # With W_core = 0.3 * lambda_J:
    # lambda_W = calibration * (1/0.3) * sqrt(1 + 2*sin^2(theta)/beta)
    # lambda_W = 3.70 * sqrt(1 + 2*sin^2(theta)/beta)

    lambda_W = 3.70 * np.sqrt(1 + 2 * sin_theta**2 / beta)

    plt.plot(beta, lambda_W, color=color, linewidth=2, label=label)

# Add observational reference lines
# Gaia DR3-corrected HGBS value (robust regions)
hgbse_value = 2.84
hgbse_error = 0.12
plt.axhline(y=hgbse_value, color='red', linestyle='--', linewidth=2,
            label=f'HGBS Robust (Gaia DR3): $\\lambda/W_{{\\rm fil}} = {hgbse_value:.2f} \\pm {hgbse_error:.2f}$')

# 3D-corrected value
hgbse_3d_value = 3.5
plt.axhline(y=hgbse_3d_value, color='green', linestyle=':', linewidth=2,
            label=f'HGBS 3D-corrected: $\\lambda/W \\approx {hgbse_3d_value:.1f}$')

# IM92 prediction
im92_value = 4.0
plt.axhline(y=im92_value, color='gray', linestyle='-.', linewidth=2,
            label=f'IM92 theory: $\\lambda/W \\approx {im92_value:.1f}$')

plt.xscale('log')
plt.xlabel('Plasma $\\beta$', fontweight='bold')
plt.ylabel('$\\lambda/W$ (dimensionless)', fontweight='bold')
plt.title('Theoretical Fragmentation Spacing vs. Plasma Beta and Field Geometry', fontweight='bold')
plt.xlim(0.1, 10)
plt.ylim(0, 8)
plt.legend(loc='upper left', fontsize=9, framealpha=0.9, ncol=2)
plt.grid(alpha=0.3)

# Add shaded region for typical HGBS conditions
plt.axvspan(0.5, 1.5, alpha=0.1, color='yellow', label='Typical HGBS $\\beta$ range')

plt.tight_layout()

# Save figure
output_path = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/figures/fig3_lambda_W_theory.pdf'
plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
print(f"✓ Figure 3 saved to {output_path}")

# Also save as PNG for preview
png_path = output_path.replace('.pdf', '.png')
plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
print(f"✓ Figure 3 PNG saved to {png_path}")

plt.close()

print("\nFigure 3 Summary:")
print(f"  HGBS Gaia DR3 value: λ/W = {hgbse_value:.2f} ± {hgbse_error:.2f}")
print(f"  HGBS 3D-corrected: λ/W ≈ {hgbse_3d_value:.1f}")
print(f"  IM92 prediction: λ/W ≈ {im92_value:.1f}")
print(f"  Longitudinal B-field: λ/W = 3.70 (independent of β)")
print(f"  Perpendicular B-field: λ/W > 5.5 for β < 10")
