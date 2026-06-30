#!/usr/bin/env python3
"""
Analyze RTC campaign λ/W distribution to understand where values fall
relative to HGBS window [2.52, 3.08].
"""

import pandas as pd
import numpy as np

# Read RTC results
rtc_file = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/simulations/realistic_turbulence_jun2026/data/RTC_results_final.csv"
df = pd.read_csv(rtc_file)

# Get valid λ/W measurements
valid = df[df['lW_status'].isin(['ok:5_peaks', 'ok:4_peaks', 'ok:3_peaks', 'ok:6_peaks', 'ok:2_peaks'])].copy()

print(f"Total simulations: {len(df)}")
print(f"Valid λ/W measurements: {len(valid)}")

# HGBS window
hgbs_min, hgbs_max = 2.52, 3.08

print(f"\n=== λ/W DISTRIBUTION (VALID MEASUREMENTS) ===")
print(f"Mean λ/W: {valid['lW'].mean():.3f}")
print(f"Median λ/W: {valid['lW'].median():.3f}")
print(f"Std λ/W: {valid['lW'].std():.3f}")
print(f"Min λ/W: {valid['lW'].min():.3f}")
print(f"Max λ/W: {valid['lW'].max():.3f}")

# Count relative to HGBS window
below_hgbs = valid[valid['lW'] < hgbs_min]
in_hgbs_window = valid[(valid['lW'] >= hgbs_min) & (valid['lW'] <= hgbs_max)]
above_hgbs = valid[valid['lW'] > hgbs_max]

print(f"\n=== RELATIVE TO HGBS WINDOW [{hgbs_min}, {hgbs_max}] ===")
print(f"Below HGBS window: {len(below_hgbs)} ({100*len(below_hgbs)/len(valid):.1f}%)")
print(f"Within HGBS window: {len(in_hgbs_window)} ({100*len(in_hgbs_window)/len(valid):.1f}%)")
print(f"Above HGBS window: {len(above_hgbs)} ({100*len(above_hgbs)/len(valid):.1f}%)")

# Distribution by geometry
print(f"\n=== BY FIELD GEOMETRY ===")
for theta in sorted(valid['theta'].unique()):
    theta_df = valid[valid['theta'] == theta]
    print(f"θ = {theta:2.0f}°: n={len(theta_df):3d}, mean λ/W={theta_df['lW'].mean():.2f}, median={theta_df['lW'].median():.2f}")

# Distribution by β
print(f"\n=== BY PLASMA BETA ===")
for beta in sorted(valid['beta'].unique()):
    beta_df = valid[valid['beta'] == beta]
    print(f"β = {beta:.1f}: n={len(beta_df):3d}, mean λ/W={beta_df['lW'].mean():.2f}")

# Distribution by f
print(f"\n=== BY LINE-MASS FRACTION f ===")
for f_val in sorted(valid['f'].unique()):
    f_df = valid[valid['f'] == f_val]
    print(f"f = {f_val:.1f}: n={len(f_df):3d}, mean λ/W={f_df['lW'].mean():.2f}")

# Check perpendicular field specifically
perp = valid[valid['theta'] == 90]
print(f"\n=== PERPENDICULAR FIELD (θ=90°) SPECIFICALLY ===")
print(f"n = {len(perp)}")
print(f"Mean λ/W: {perp['lW'].mean():.3f}")
print(f"Median λ/W: {perp['lW'].median():.3f}")
print(f"All perpendicular λ/W values: {sorted(perp['lW'].values)}")

# Check longitudinal field specifically
long = valid[valid['theta'] == 0]
print(f"\n=== LONGITUDINAL FIELD (θ=0°) SPECIFICALLY ===")
print(f"n = {len(long)}")
print(f"Mean λ/W: {long['lW'].mean():.3f}")
print(f"Median λ/W: {long['lW'].median():.3f}")

# Restricted subspace (physically motivated)
restricted = valid[
    (valid['beta'] >= 1.0) & (valid['beta'] <= 2.0) &
    (valid['f'] >= 1.2) & (valid['f'] <= 2.0) &
    (valid['theta'] == 0) &
    (valid['mturb'] >= 1.0) & (valid['mturb'] <= 3.0)
]
print(f"\n=== RESTRICTED SUBSPACE (β∈[1,2], f∈[1.2,2.0], θ=0°, M∈[1,3]) ===")
print(f"n = {len(restricted)}")
if len(restricted) > 0:
    print(f"Mean λ/W: {restricted['lW'].mean():.3f}")
    print(f"Median λ/W: {restricted['lW'].median():.3f}")
    print(f"All λ/W values: {sorted(restricted['lW'].values)}")

# Show examples with highest λ/W
print(f"\n=== TOP 10 λ/W VALUES ===")
top10 = valid.nlargest(10, 'lW')
print(top10[['run_id', 'f', 'beta', 'mturb', 'theta', 'lW', 'lW_status']].to_string())

# Show closest to HGBS window
valid['dist_to_hgbs_center'] = np.abs(valid['lW'] - 2.8)
closest = valid.nsmallest(10, 'dist_to_hgbs_center')
print(f"\n=== CLOSEST TO HGBS CENTER (2.8) ===")
print(closest[['run_id', 'f', 'beta', 'mturb', 'theta', 'lW', 'lW_status']].to_string())
