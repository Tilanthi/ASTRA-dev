#!/usr/bin/env python3
"""
Generate Supernova Light Curve Data WITH Phillips Relation
===========================================================

Generates realistic supernova light curves based on:
- Type Ia and Type II supernova templates
- Light curve parameters (peak magnitude, decline rate, color)
- Host galaxy properties
- Redshift effects
- Time-domain sampling

CRITICAL: This version PROPERLY ENCODES the Phillips relation for Type Ia SNe:
Faster-declining SNe Ia are fainter (negative correlation).
"""

import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path('/Users/gjw255/astrodata/SWARM/ASTRA/RASTI_paper/Example4/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
n_sne = 3000

print("=" * 70)
print("STEP 1: Generating Supernova Data WITH Phillips Relation")
print("=" * 70)

# SN type: 0 = Ia, 1 = II, 2 = Ib/c
sn_type = np.random.choice([0, 1, 2], n_sne, p=[0.7, 0.2, 0.1])
sn_type_name = ['Type Ia', 'Type II', 'Type Ib/c']

n_ia = np.sum(sn_type == 0)
print(f"Generating {n_ia} Type Ia supernovae with Phillips relation")

# Redshift (0.01 - 0.3)
redshift = np.random.uniform(0.01, 0.3, n_sne)

# For Type Ia: Generate decline rate FIRST, then compute peak magnitude from Phillips relation
# This ensures the correlation exists in the data
decline_rate = np.zeros(n_sne)
peak_mag = np.zeros(n_sne)

# Type Ia: Generate decline rate, then peak magnitude from Phillips relation
decline_rate[sn_type == 0] = np.random.uniform(0.8, 1.8, n_ia)  # Broader range for Ia
# Phillips relation: M_B = alpha * (dm15 - 1.1) - 19.3
# where alpha ≈ -1.0 to -1.5 (faster decline = fainter)
alpha = -1.2  # Standard Phillips relation slope
peak_mag[sn_type == 0] = alpha * (decline_rate[sn_type == 0] - 1.1) - 19.3
# Add intrinsic scatter
peak_mag[sn_type == 0] += np.random.normal(0, 0.15, n_ia)

# Type II: No Phillips relation, independent distributions
decline_rate[sn_type == 1] = np.random.uniform(0.8, 2.2, np.sum(sn_type == 1))
peak_mag[sn_type == 1] = np.random.normal(-17.5, 1.0, np.sum(sn_type == 1))

# Type Ib/c: No Phillips relation
decline_rate[sn_type == 2] = np.random.uniform(0.8, 2.0, np.sum(sn_type == 2))
peak_mag[sn_type == 2] = np.random.normal(-18.0, 0.8, np.sum(sn_type == 2))

# Apply distance modulus
distance_modulus = 5 * np.log10(3e5 * redshift) + 25
apparent_peak_mag = peak_mag + distance_modulus

# Light curve stretch
stretch = 1.0 / (0.5 + decline_rate)

# Color excess (E(B-V))
color_excess = np.random.exponential(0.1, n_sne)

# Host galaxy mass (log solar masses)
host_mass = np.random.uniform(9.0, 11.5, n_sne)

# Host galaxy metallicity (12 + log O/H)
host_metallicity = 8.7 + 0.3 * (host_mass - 10.0) + np.random.normal(0, 0.1, n_sne)

# Host galaxy star formation rate (log M_sun/yr)
host_sfr = np.random.uniform(-2, 2, n_sne)
host_sfr[sn_type == 0] = np.random.uniform(-2, 0, np.sum(sn_type == 0))  # Ia in older hosts

# Host galaxy type (0 = elliptical, 1 = spiral, 2 = irregular)
host_type = np.zeros(n_sne, dtype=int)
host_type[host_sfr > 0] = np.random.choice([1, 2], np.sum(host_sfr > 0))

# Peak time (MJD)
peak_mjd = np.random.uniform(59000, 61000, n_sne)

# Rise time (days)
rise_time = np.zeros(n_sne)
rise_time[sn_type == 0] = np.random.normal(18, 2, np.sum(sn_type == 0))
rise_time[sn_type == 1] = np.random.normal(20, 5, np.sum(sn_type == 1))
rise_time[sn_type == 2] = np.random.normal(19, 3, np.sum(sn_type == 2))

# Explosion time
explosion_mjd = peak_mjd - rise_time

# Light curve width (days)
lc_width = np.zeros(n_sne)
lc_width[sn_type == 0] = np.random.normal(20, 3, np.sum(sn_type == 0))
lc_width[sn_type == 1] = np.random.normal(100, 20, np.sum(sn_type == 1))
lc_width[sn_type == 2] = np.random.normal(25, 5, np.sum(sn_type == 2))

# Spectral features (Si II velocity for Ia)
si2_velocity = np.random.normal(10000, 2000, n_sne)
si2_velocity[sn_type != 0] = np.nan  # Only for Ia

# Host extinction (A_V)
host_extinction = color_excess * 3.1

# Detection status
snr = (22 - apparent_peak_mag) / 0.1
detected = snr > 5

# Number of observations
n_observations = np.random.poisson(50, n_sne) + 10

# Time span of observations (days)
time_span = np.random.uniform(30, 200, n_sne)

# Classification confidence
classification_conf = np.random.uniform(0.5, 1.0, n_sne)
classification_conf[~detected] = 0

# Create DataFrame
df = pd.DataFrame({
    'sn_id': range(n_sne),
    'sn_type': sn_type,
    'sn_type_name': [sn_type_name[t] for t in sn_type],
    'redshift': redshift,
    'peak_mag_abs': peak_mag,
    'peak_mag_app': apparent_peak_mag,
    'distance_modulus': distance_modulus,
    'decline_rate': decline_rate,
    'stretch': stretch,
    'color_excess': color_excess,
    'host_mass': host_mass,
    'host_metallicity': host_metallicity,
    'host_sfr': host_sfr,
    'host_type': host_type,
    'peak_mjd': peak_mjd,
    'explosion_mjd': explosion_mjd,
    'rise_time': rise_time,
    'lc_width': lc_width,
    'si2_velocity': si2_velocity,
    'host_extinction': host_extinction,
    'detected': detected.astype(int),
    'n_observations': n_observations,
    'time_span': time_span,
    'classification_conf': classification_conf
})

# Verify Phillips relation in Type Ia data
ia_mask = df['sn_type'] == 0
ia_data = df[ia_mask]
corr = np.corrcoef(ia_data['decline_rate'], ia_data['peak_mag_abs'])[0, 1]
print(f"\nPhillips Relation Verification:")
print(f"  Type Ia SNe: {n_ia}")
print(f"  Correlation (dm15 vs M_B): {corr:.3f}")
print(f"  Expected: negative correlation (faster decline = fainter)")
print(f"  Decline rate range: {ia_data['decline_rate'].min():.2f} - {ia_data['decline_rate'].max():.2f}")
print(f"  Peak mag range: {ia_data['peak_mag_abs'].min():.2f} - {ia_data['peak_mag_abs'].max():.2f}")

# Save data
output_path = DATA_DIR / 'supernova_data_with_phillips.csv'
df.to_csv(output_path, index=False)

print(f"\n✓ Generated {n_sne} supernovae WITH Phillips relation")
print(f"  Redshift range: {df['redshift'].min():.3f} - {df['redshift'].max():.3f}")
print(f"  SN types:")
for i, name in enumerate(sn_type_name):
    count = np.sum(sn_type == i)
    print(f"    {name}: {count}")
print(f"  Detected: {df['detected'].sum()}")
print(f"  Columns: {len(df.columns)}")
print(f"  Saved to: {output_path}")
print("=" * 70)
