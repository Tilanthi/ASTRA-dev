#!/usr/bin/env python3

# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Step 1: Generate Cosmology Data for V5.0 Discovery Test
========================================================

Generates realistic cosmology data based on:
- Large scale structure (galaxy clustering)
- Hubble diagram (distance vs redshift)
- Cosmic microwave background measurements
- Dark energy constraints
- Baryon acoustic oscillations
"""

import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path('/Users/gjw255/astrodata/SWARM/ASTRA/RASTI_paper/Example5/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
n_galaxies = 8000

print("=" * 60)
print("STEP 1: Generating Cosmology Data")
print("=" * 60)

# Redshift (0.01 - 2.0)
redshift = np.random.uniform(0.01, 2.0, n_galaxies)

# Comoving distance (Mpc/h) - LCDM approximation
H0 = 70.0  # Hubble constant
Omega_m = 0.3  # Matter density
Omega_L = 0.7  # Dark energy density

# Simplified comoving distance calculation
def comoving_distance(z):
    # Approximate for LCDM
    return (3000 / H0) * (z - 0.1 * z**2 + 0.05 * z**3)

comoving_dist = comoving_distance(redshift)

# Angular position (RA, Dec in degrees)
ra = np.random.uniform(0, 360, n_galaxies)
dec = np.random.uniform(-90, 90, n_galaxies)

# Galaxy clustering signal
# 2-point correlation function
separation = np.random.uniform(0.1, 100, n_galaxies)  # Mpc/h
correlation_function = (separation / 5.0) ** (-1.8)
correlation_function += np.random.normal(0, 0.1, n_galaxies)

# BAO peak position
bao_scale = 105.0  # Mpc/h (sound horizon scale)
bao_detection = np.exp(-0.5 * ((separation - bao_scale) / 10.0) ** 2)

# Hubble diagram: distance modulus vs redshift
distance_modulus = 5 * np.log10(comoving_dist * (1 + redshift)) + 25

# Add peculiar velocities
peculiar_velocity = np.random.normal(0, 300, n_galaxies)  # km/s
redshift_observed = redshift + peculiar_velocity / 300000

# Distance modulus error
dist_mod_error = np.random.uniform(0.1, 0.3, n_galaxies)
distance_modulus_obs = distance_modulus + np.random.normal(0, dist_mod_error, n_galaxies)

# Galaxy magnitudes
apparent_mag = distance_modulus + np.random.normal(-20, 1, n_galaxies)
absolute_mag = apparent_mag - distance_modulus

# Galaxy color (g-r)
galaxy_color = np.random.normal(0.7, 0.3, n_galaxies)

# Stellar mass (log solar masses)
stellar_mass = np.random.normal(10.5, 0.5, n_galaxies)

# Star formation rate (log M_sun/yr)
sfr = np.random.normal(0, 1, n_galaxies)

# Environment density
environment_density = np.random.exponential(1.0, n_galaxies)

# Weak lensing shear
shear_1 = np.random.normal(0, 0.02, n_galaxies)
shear_2 = np.random.normal(0, 0.02, n_galaxies)

# CMB temperature fluctuations (for a subset)
n_cmb = 1000
cmb_l = np.arange(2, n_cmb + 2)
cmb_cl = 1000 * (cmb_l / 50.0) ** (-2.5) * np.exp(-cmb_l / 2000)
cmb_cl += np.random.normal(0, 50, n_cmb)

# Hubble constant measurements from different probes
n_h0 = 500
h0_probes = np.random.choice(['CMB', 'SN', 'BAO', 'Lensing'], n_h0)
h0_values = np.zeros(n_h0)
h0_errors = np.zeros(n_h0)

h0_values[h0_probes == 'CMB'] = np.random.normal(67.4, 0.5, np.sum(h0_probes == 'CMB'))
h0_errors[h0_probes == 'CMB'] = 0.5
h0_values[h0_probes == 'SN'] = np.random.normal(73.0, 1.0, np.sum(h0_probes == 'SN'))
h0_errors[h0_probes == 'SN'] = 1.0
h0_values[h0_probes == 'BAO'] = np.random.normal(69.0, 0.8, np.sum(h0_probes == 'BAO'))
h0_errors[h0_probes == 'BAO'] = 0.8
h0_values[h0_probes == 'Lensing'] = np.random.normal(71.0, 2.0, np.sum(h0_probes == 'Lensing'))
h0_errors[h0_probes == 'Lensing'] = 2.0

# Dark energy equation of state (w)
w_measurements = np.random.normal(-1.0, 0.1, 100)
w_errors = np.random.uniform(0.05, 0.15, 100)

# Create DataFrame for galaxies
df_galaxies = pd.DataFrame({
    'galaxy_id': range(n_galaxies),
    'redshift': redshift,
    'redshift_observed': redshift_observed,
    'comoving_distance': comoving_dist,
    'ra': ra,
    'dec': dec,
    'separation': separation,
    'correlation_function': correlation_function,
    'bao_detection': bao_detection,
    'distance_modulus': distance_modulus,
    'distance_modulus_obs': distance_modulus_obs,
    'dist_mod_error': dist_mod_error,
    'apparent_mag': apparent_mag,
    'absolute_mag': absolute_mag,
    'galaxy_color': galaxy_color,
    'stellar_mass': stellar_mass,
    'sfr': sfr,
    'environment_density': environment_density,
    'shear_1': shear_1,
    'shear_2': shear_2
})

# Save galaxy data
galaxy_path = DATA_DIR / 'cosmology_galaxy_data.csv'
df_galaxies.to_csv(galaxy_path, index=False)

# Create DataFrame for H0 measurements
df_h0 = pd.DataFrame({
    'measurement_id': range(n_h0),
    'probe': h0_probes,
    'h0_value': h0_values,
    'h0_error': h0_errors
})

# Save H0 data
h0_path = DATA_DIR / 'cosmology_h0_data.csv'
df_h0.to_csv(h0_path, index=False)

# Create DataFrame for CMB
df_cmb = pd.DataFrame({
    'l': cmb_l,
    'cl': cmb_cl
})

# Save CMB data
cmb_path = DATA_DIR / 'cosmology_cmb_data.csv'
df_cmb.to_csv(cmb_path, index=False)

# Create DataFrame for w measurements
df_w = pd.DataFrame({
    'measurement_id': range(100),
    'w_value': w_measurements,
    'w_error': w_errors
})

# Save w data
w_path = DATA_DIR / 'cosmology_w_data.csv'
df_w.to_csv(w_path, index=False)

print(f"✓ Generated cosmology dataset")
print(f"  Galaxies: {n_galaxies:,}")
print(f"  Redshift range: {redshift.min():.3f} - {redshift.max():.3f}")
print(f"  H0 measurements: {n_h0}")
print(f"  CMB l-modes: {n_cmb}")
print(f"  w measurements: 100")
print(f"\nFiles saved:")
print(f"  - {galaxy_path}")
print(f"  - {h0_path}")
print(f"  - {cmb_path}")
print(f"  - {w_path}")
print("=" * 60)
