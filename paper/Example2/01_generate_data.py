#!/usr/bin/env python3
"""
Step 1: Generate Stellar Cluster Data for V5.0 Discovery Test
==============================================================

Generates realistic stellar cluster properties based on:
- Main sequence mass-luminosity relation
- Hertzsprung-Russell diagram structure
- Stellar evolution tracks
- Initial mass function (Salpeter)
- Cluster age variations
"""

import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path('/Users/gjw255/astrodata/SWARM/ASTRA/RASTI_paper/Example2/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
n_stars = 10000

print("=" * 60)
print("STEP 1: Generating Stellar Cluster Data")
print("=" * 60)

# Stellar mass (solar masses, Salpeter IMF)
# Power law: N(M) ~ M^(-2.35)
mass_min, mass_max = 0.1, 50.0
alpha = 2.35

# Sample from power law distribution
u = np.random.random(n_stars)
mass = ((mass_max**(1-alpha) - mass_min**(1-alpha)) * u + mass_min**(1-alpha))**(1/(1-alpha))

# Luminosity (mass-luminosity relation for main sequence)
# L ~ M^3.5 for M > 0.5, L ~ M^2.3 for M < 0.5
luminosity = np.where(mass > 0.5,
                      mass ** 3.5,
                      mass ** 2.3)

# Effective temperature (main sequence)
# T ~ M^0.55 for M > 1, T ~ M^0.5 for M < 1
temperature = np.where(mass > 1.0,
                       5778 * mass ** 0.55,
                       5778 * mass ** 0.5)

# Surface gravity
# g ~ M/R^2, R ~ M^0.8 for main sequence
radius = np.where(mass > 1.0,
                  mass ** 0.8,
                  mass ** 0.9)
gravity = mass / (radius ** 2)

# Metallicity (varies by cluster)
# [Fe/H] from -2.0 to +0.5
metallicity_feh = np.random.uniform(-2.0, 0.5, n_stars)

# Age (log years) - young to old clusters
age_log = np.random.uniform(6.0, 10.0, n_stars)

# Evolutionary stage
# 0 = main sequence, 1 = red giant, 2 = white dwarf
evolutionary_stage = np.zeros(n_stars, dtype=int)

# Stars that evolved off main sequence
evolved_mask = (mass > 1.0) & (age_log > 9.0)
evolutionary_stage[evolved_mask] = 1  # Red giant branch

# Massive stars that became white dwarfs
wd_mask = (mass > 0.8) & (mass < 8.0) & (age_log > 9.5)
evolutionary_stage[wd_mask] = 2  # White dwarf

# Modify properties for evolved stars
# Red giants: cooler, larger
rg_mask = evolutionary_stage == 1
temperature[rg_mask] *= 0.5
radius[rg_mask] *= 10
luminosity[rg_mask] *= 100
gravity[rg_mask] /= 100

# White dwarfs: hot but small, dim
wd_mask = evolutionary_stage == 2
temperature[wd_mask] *= 2
radius[wd_mask] *= 0.01
luminosity[wd_mask] *= 0.01
gravity[wd_mask] *= 1000

# B-V color (approximate from temperature)
bv_color = 7000 / temperature - 0.7

# Absolute magnitude
absolute_mag = 4.83 - 2.5 * np.log10(luminosity)

# Parallax (mas) - assuming cluster at 2 kpc
distance_pc = 2000
parallax = 1000 / distance_pc + np.random.normal(0, 0.5, n_stars)

# Proper motion (mas/yr)
pm_ra = np.random.normal(0, 5, n_stars)
pm_dec = np.random.normal(0, 5, n_stars)

# Radial velocity (km/s)
radial_velocity = np.random.normal(30, 10, n_stars)

# Spectral type (numerical: O=0, B=1, A=2, F=3, G=4, K=5, M=6)
spectral_type = np.digitize(temperature, [30000, 10000, 7500, 6000, 5200, 3700])

# Cluster membership probability
# Core members: high probability, field stars: low probability
cluster_radius = np.sqrt(np.random.uniform(0, 100, n_stars))
membership_prob = np.exp(-cluster_radius / 20)

# Rotational velocity (km/s)
v_rotation = np.random.uniform(0, 200, n_stars)
v_rotation[evolutionary_stage == 1] *= 0.3  # Giants rotate slower

# Lithium abundance (depletes with age)
lithium_abundance = np.where(age_log < 8.0,
                             3.0 + np.random.normal(0, 0.3, n_stars),
                             np.maximum(0, 3.0 - (age_log - 8.0) * 0.5))

# Create DataFrame
df = pd.DataFrame({
    'star_id': range(n_stars),
    'mass': mass,
    'luminosity': luminosity,
    'log_luminosity': np.log10(luminosity),
    'temperature': temperature,
    'log_temperature': np.log10(temperature),
    'radius': radius,
    'gravity': gravity,
    'log_gravity': np.log10(gravity),
    'metallicity_feh': metallicity_feh,
    'age_log': age_log,
    'age_myr': 10 ** age_log / 1e6,
    'evolutionary_stage': evolutionary_stage,
    'bv_color': bv_color,
    'absolute_mag': absolute_mag,
    'parallax': parallax,
    'pm_ra': pm_ra,
    'pm_dec': pm_dec,
    'radial_velocity': radial_velocity,
    'spectral_type': spectral_type,
    'membership_prob': membership_prob,
    'v_rotation': v_rotation,
    'lithium_abundance': lithium_abundance
})

# Save data
output_path = DATA_DIR / 'stellar_data.csv'
df.to_csv(output_path, index=False)

print(f"✓ Generated {n_stars} stars")
print(f"  Mass range: {df['mass'].min():.2f} - {df['mass'].max():.2f} M_sun")
print(f"  Temperature range: {df['temperature'].min():.0f} - {df['temperature'].max():.0f} K")
print(f"  Evolutionary stages:")
print(f"    Main Sequence: {(df['evolutionary_stage'] == 0).sum()}")
print(f"    Red Giants: {(df['evolutionary_stage'] == 1).sum()}")
print(f"    White Dwarfs: {(df['evolutionary_stage'] == 2).sum()}")
print(f"  Columns: {len(df.columns)}")
print(f"  Saved to: {output_path}")
print("=" * 60)
