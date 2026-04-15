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
Step 1: Generate Exoplanet Transit Data for V5.0 Discovery Test
================================================================

Generates realistic exoplanet transit data based on:
- Transit photometry (light curves)
- Radial velocity measurements
- Planet radius and orbital period distributions
- Stellar host properties
- Multi-planet systems
"""

import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path('/Users/gjw255/astrodata/SWARM/ASTRA/RASTI_paper/Example3/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
n_observations = 5000
n_systems = 500

print("=" * 60)
print("STEP 1: Generating Exoplanet Transit Data")
print("=" * 60)

# System ID
system_ids = np.random.randint(0, n_systems, n_observations)

# Stellar host properties
stellar_mass = np.random.uniform(0.5, 2.0, n_observations)  # Solar masses
stellar_radius = np.random.uniform(0.7, 1.5, n_observations)  # Solar radii
stellar_temperature = np.random.uniform(4000, 7000, n_observations)  # K
stellar_metallicity = np.random.uniform(-0.5, 0.5, n_observations)  # [Fe/H]

# Planet properties
# Planet radius (Earth radii) - power law distribution
planet_radius = np.random.power(2, n_observations) * 15 + 0.5

# Orbital period (days) - log-uniform
orbital_period = 10 ** np.random.uniform(0.5, 3.0, n_observations)

# Semi-major axis (AU) from Kepler's third law
# a^3 = P^2 * M_star
semi_major_axis = (orbital_period ** 2 * stellar_mass) ** (1/3)

# Orbital inclination (degrees)
# Transit requires i ~ 90 degrees
orbital_inclination = np.random.normal(90, 5, n_observations)
orbital_inclination = np.clip(orbital_inclination, 85, 95)

# Transit depth (ppm) - (Rp/Rs)^2
transit_depth = ((planet_radius * 0.089) / stellar_radius) ** 2 * 1e6

# Transit duration (hours)
transit_duration = (stellar_radius * 0.00465) * orbital_period ** (1/3) / semi_major_axis

# Impact parameter
b = np.random.uniform(0, 1, n_observations) * (1 + (stellar_radius * 0.00465) / semi_major_axis)

# Eccentricity
eccentricity = np.random.beta(2, 5, n_observations)
eccentricity = np.clip(eccentricity, 0, 0.9)

# Argument of periastron (degrees)
omega = np.random.uniform(0, 360, n_observations)

# Radial velocity semi-amplitude (m/s)
# K = 28.4 * (Mp sin i) * (M_star)^(-2/3) * (P/1yr)^(-1/3)
planet_mass = planet_radius ** 2.5  # Mass-radius relation approximation
rv_semi_amplitude = 28.4 * planet_mass * stellar_mass ** (-2/3) * (orbital_period / 365.25) ** (-1/3)
rv_semi_amplitude *= np.sin(np.radians(orbital_inclination))

# Radial velocity measurement error (m/s)
rv_error = np.random.uniform(0.5, 5.0, n_observations)

# Transit timing variation (seconds)
ttv = np.random.normal(0, 60, n_observations)

# Signal-to-noise ratio
snr_transit = transit_depth / np.sqrt(transit_depth + 1000)
snr_rv = rv_semi_amplitude / rv_error

# Detection status (combined SNR threshold)
detected_transit = snr_transit > 7
detected_rv = snr_rv > 7

# Planet type classification
# Rocky: < 1.5 Re, Super-Earth: 1.5-2.5 Re, Neptune: 2.5-4 Re, Gas Giant: > 4 Re
planet_type = np.digitize(planet_radius, [1.5, 2.5, 4.0])
planet_type_labels = {0: 'Rocky', 1: 'Super-Earth', 2: 'Neptune', 3: 'Gas Giant'}
planet_type_name = [planet_type_labels[i] for i in planet_type]

# Habitable zone status
# Simplified HZ boundaries based on stellar mass
hz_inner = 0.75 * np.sqrt(stellar_mass)
hz_outer = 1.5 * np.sqrt(stellar_mass)
in_habitable_zone = (semi_major_axis >= hz_inner) & (semi_major_axis <= hz_outer)

# Number of planets in system
n_planets_in_system = np.random.poisson(2, n_observations) + 1

# Transit multiplicity
transit_multiplicity = np.random.binomial(n_planets_in_system, 0.3)

# Equilibrium temperature (K)
# Teq = T_star * (R_star / 2a)^(1/2)
equilibrium_temperature = stellar_temperature * np.sqrt(stellar_radius / (2 * semi_major_axis))

# Albedo
albedo = np.random.uniform(0.1, 0.5, n_observations)

# Insolation flux (Earth units)
insolation_flux = stellar_temperature ** 4 * (stellar_radius / semi_major_axis) ** 2 / 5778 ** 4

# Create DataFrame
df = pd.DataFrame({
    'observation_id': range(n_observations),
    'system_id': system_ids,
    'stellar_mass': stellar_mass,
    'stellar_radius': stellar_radius,
    'stellar_temperature': stellar_temperature,
    'stellar_metallicity': stellar_metallicity,
    'planet_radius': planet_radius,
    'planet_mass': planet_mass,
    'orbital_period': orbital_period,
    'semi_major_axis': semi_major_axis,
    'orbital_inclination': orbital_inclination,
    'transit_depth': transit_depth,
    'transit_duration': transit_duration,
    'impact_parameter': b,
    'eccentricity': eccentricity,
    'omega': omega,
    'rv_semi_amplitude': rv_semi_amplitude,
    'rv_error': rv_error,
    'ttv': ttv,
    'snr_transit': snr_transit,
    'snr_rv': snr_rv,
    'detected_transit': detected_transit.astype(int),
    'detected_rv': detected_rv.astype(int),
    'planet_type': planet_type,
    'planet_type_name': planet_type_name,
    'in_habitable_zone': in_habitable_zone.astype(int),
    'n_planets_in_system': n_planets_in_system,
    'transit_multiplicity': transit_multiplicity,
    'equilibrium_temperature': equilibrium_temperature,
    'albedo': albedo,
    'insolation_flux': insolation_flux
})

# Save data
output_path = DATA_DIR / 'exoplanet_data.csv'
df.to_csv(output_path, index=False)

print(f"✓ Generated {n_observations} exoplanet observations")
print(f"  Systems: {n_systems}")
print(f"  Planet radius range: {df['planet_radius'].min():.2f} - {df['planet_radius'].max():.2f} Re")
print(f"  Orbital period range: {df['orbital_period'].min():.2f} - {df['orbital_period'].max():.2f} days")
print(f"  Planet types:")
for ptype, count in df['planet_type_name'].value_counts().items():
    print(f"    {ptype}: {count}")
print(f"  In habitable zone: {df['in_habitable_zone'].sum()}")
print(f"  Detected by transit: {df['detected_transit'].sum()}")
print(f"  Detected by RV: {df['detected_rv'].sum()}")
print(f"  Columns: {len(df.columns)}")
print(f"  Saved to: {output_path}")
print("=" * 60)
