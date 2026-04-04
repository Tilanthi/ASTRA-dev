#!/usr/bin/env python3
"""
Step 1: Generate Galaxy Data for V5.0 Discovery Test

Generates realistic galaxy properties based on astrophysical relations:
- Star-forming main sequence (log SFR vs log mass)
- Mass-metallicity relation
- Mass-size relation
- Color-mass relation (red/blue sequence)
- Environmental quenching effects
"""

import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path('/Users/gjw255/astrodata/SWARM/ASTRA/RASTI_paper/Example1/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
n_galaxies = 5000

print("=" * 60)
print("STEP 1: Generating Galaxy Data")
print("=" * 60)

# Stellar mass (log scale, solar masses)
log_mass = np.random.uniform(9.0, 11.8, n_galaxies)

# Star formation rate (main sequence relation: log SFR ~ 0.7*log_mass - 6.5)
log_sfr_main = 0.7 * log_mass - 6.5
log_sfr_scatter = np.random.normal(0, 0.4, n_galaxies)
log_sfr = log_sfr_main + log_sfr_scatter

# Quenched galaxies (20% of sample)
quenched_mask = np.random.random(n_galaxies) < 0.2
log_sfr[quenched_mask] = np.random.uniform(-3, 0, np.sum(quenched_mask))

# Metallicity (mass-metallicity relation)
metallicity = 8.7 + 0.3 * (log_mass - 10.0)
metallicity += np.random.normal(0, 0.1, n_galaxies)

# Size (mass-size relation)
log_size = 0.25 * (log_mass - 10.0) + 0.5
log_size += np.random.normal(0, 0.2, n_galaxies)

# Concentration (structural evolution)
concentration = np.random.uniform(2.0, 4.0, n_galaxies)
concentration[quenched_mask] = np.random.uniform(3.5, 4.5, np.sum(quenched_mask))

# Color (u-r) - red/blue sequence
color_ur = np.random.uniform(1.0, 4.0, n_galaxies)
color_ur[quenched_mask] = np.random.uniform(2.5, 5.0, np.sum(quenched_mask))

# Local density (environment)
local_density = np.random.exponential(1.0, n_galaxies)
local_density[quenched_mask] *= 2.0  # Quenched galaxies in denser environments

# Halo mass (log scale)
log_halo_mass = np.random.uniform(11.0, 15.0, n_galaxies)

# Redshift (0.01 - 0.2)
redshift = np.random.uniform(0.01, 0.2, n_galaxies)

# Lookback time (approximate conversion)
lookback_gyr = redshift * 13.5

# Surface density
surface_density = 10**log_mass / (np.pi * (10**log_size)**2)

# Specific SFR
ssfr = log_sfr - log_mass

# Create DataFrame
df = pd.DataFrame({
    'objid': range(n_galaxies),
    'ra': np.random.uniform(0, 360, n_galaxies),
    'dec': np.random.uniform(-30, 70, n_galaxies),
    'redshift': redshift,
    'log_mass': log_mass,
    'stellar_mass': 10**log_mass,
    'log_sfr': log_sfr,
    'sfr': 10**log_sfr,
    'metallicity': metallicity,
    'log_size': log_size,
    'size_kpc': 10**log_size,
    'concentration': concentration,
    'color_ur': color_ur,
    'surface_density': surface_density,
    'local_density': local_density,
    'log_halo_mass': log_halo_mass,
    'lookback_gyr': lookback_gyr,
    'quenched_def': quenched_mask.astype(int),
    'ssfr': ssfr
})

# Save data
output_path = DATA_DIR / 'galaxy_data.csv'
df.to_csv(output_path, index=False)

print(f"✓ Generated {n_galaxies} galaxies")
print(f"  Redshift range: {df['redshift'].min():.3f} - {df['redshift'].max():.3f}")
print(f"  Mass range (log): {df['log_mass'].min():.2f} - {df['log_mass'].max():.2f}")
print(f"  Quenched fraction: {df['quenched_def'].mean():.1%}")
print(f"  Columns: {len(df.columns)}")
print(f"  Saved to: {output_path}")
print("=" * 60)
