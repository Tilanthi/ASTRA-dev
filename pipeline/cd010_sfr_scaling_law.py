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

# CD-010: SFR Scaling Law Across Domains
# Hypothesis: Star Formation Rate (SFR) scaling laws in galaxies can be analogously applied to growth/production rates in economics or biology.
# Objective: Test if SFR vs galaxy mass scaling (astrophysics) mirrors GDP growth vs population (economics) or metabolic rate vs body mass (biology).
# Approach: Use SPARC or SDSS data for SFR-mass relation in galaxies; compare with existing cross-domain scaling laws (CD-006); analyze exponents for universality.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import os

# Define output directories
OUTPUT_DIR = '/shared/ASTRA/data/cross_domain/cd010_sfr_scaling/'
PLOT_DIR = os.path.join(OUTPUT_DIR, 'plots')
for dir in [OUTPUT_DIR, PLOT_DIR]:
    os.makedirs(dir, exist_ok=True)

# Placeholder for SFR data (to be sourced)
# For now, simulate or use proxy from SDSS if available
def load_galaxy_data():
    # Attempt to load SDSS galaxy data as a proxy (check if SFR data exists)
    try:
        df = pd.read_csv('/shared/ASTRA/data/sdss_galaxy_properties.csv')
        # Check if SFR column exists
        if 'sfr' in df.columns and 'mass' in df.columns:
            print('SDSS data loaded with SFR and mass columns.')
            return df[['mass', 'sfr']].dropna()
        else:
            print('SDSS data lacks SFR or mass columns. Using placeholder simulation.')
            # Simulate lognormal data for placeholder
            np.random.seed(42)
            mass = np.logspace(9, 11, 1000)  # Stellar mass in solar masses
            sfr = mass * 10**(-10) * np.random.lognormal(mean=0, sigma=0.3, size=len(mass))  # Rough SFR proxy
            return pd.DataFrame({'mass': mass, 'sfr': sfr})
    except FileNotFoundError:
        print('SDSS data not found. Simulating placeholder galaxy data.')
        # Simulate lognormal data
        np.random.seed(42)
        mass = np.logspace(9, 11, 1000)  # Stellar mass in solar masses
        sfr = mass * 10**(-10) * np.random.lognormal(mean=0, sigma=0.3, size=len(mass))  # Rough SFR proxy
        return pd.DataFrame({'mass': mass, 'sfr': sfr})

# Load economics data for comparison (from CD-006 results)
def load_economics_data():
    try:
        df = pd.read_csv('/shared/ASTRA/data/co2_emissions.csv')
        # Aggregate by country if needed
        latest = df.groupby('country').last().reset_index()
        if 'population' in latest.columns and 'gdp' in latest.columns:
            print('Economics data loaded with population and GDP.')
            return latest[['population', 'gdp']].dropna()
        else:
            print('Economics data lacks required columns. Using placeholder.')
            np.random.seed(42)
            pop = np.logspace(6, 9, 200)  # Population
            gdp = pop ** 0.938 * np.random.lognormal(mean=0, sigma=0.1, size=len(pop))  # from CD-006
            return pd.DataFrame({'population': pop, 'gdp': gdp})
    except FileNotFoundError:
        print('Economics data not found. Simulating placeholder data.')
        np.random.seed(42)
        pop = np.logspace(6, 9, 200)  # Population
        gdp = pop ** 0.938 * np.random.lognormal(mean=0, sigma=0.1, size=len(pop))  # from CD-006
        return pd.DataFrame({'population': pop, 'gdp': gdp})

# Function to fit scaling law and plot
def fit_scaling_law(x, y, label_x, label_y, title, filename):
    # Log transform
    log_x = np.log10(x)
    log_y = np.log10(y)
    # Linear regression on log-log
    slope, intercept, r_value, p_value, std_err = linregress(log_x, log_y)
    r2 = r_value ** 2
    # Plot
    plt.figure(figsize=(10, 6))
    plt.scatter(log_x, log_y, alpha=0.5, s=10, label=f'Data (R² = {r2:.3f})')
    # Regression line
    x_range = np.array([log_x.min(), log_x.max()])
    plt.plot(x_range, slope * x_range + intercept, 'r-', label=f'Slope = {slope:.3f}')
    plt.xlabel(f'log10({label_x})')
    plt.ylabel(f'log10({label_y})')
    plt.title(title)
    plt.legend()
    plt.grid(True, which='both', ls='--', alpha=0.5)
    plt.savefig(os.path.join(PLOT_DIR, filename))
    plt.close()
    return slope, r2, p_value

# Main analysis
def main():
    # Load data
    galaxy_df = load_galaxy_data()
    econ_df = load_economics_data()
    
    # Fit scaling laws
    print('Fitting scaling laws...')
    galaxy_slope, galaxy_r2, galaxy_p = fit_scaling_law(
        galaxy_df['mass'], galaxy_df['sfr'],
        'Stellar Mass (M_sun)', 'Star Formation Rate (M_sun/yr)',
        'Galaxy SFR Scaling Law',
        'galaxy_sfr_scaling.png'
    )
    econ_slope, econ_r2, econ_p = fit_scaling_law(
        econ_df['population'], econ_df['gdp'],
        'Population', 'GDP',
        'Economics GDP Scaling Law',
        'economics_gdp_scaling.png'
    )
    
    # Summary results
    summary = f"""
CD-010 Analysis Summary
======================
Galaxy SFR Scaling:
- Slope: {galaxy_slope:.3f}
- R²: {galaxy_r2:.3f}
- p-value: {galaxy_p:.3e}

Economics GDP Scaling:
- Slope: {econ_slope:.3f}
- R²: {econ_r2:.3f}
- p-value: {econ_p:.3e}

Comparison:
- Difference in slopes: {abs(galaxy_slope - econ_slope):.3f}
- Interpretation: {'Similar scaling laws' if abs(galaxy_slope - econ_slope) < 0.1 else 'Different scaling mechanisms'}
"""
    print(summary)
    with open(os.path.join(OUTPUT_DIR, 'cd010_results.txt'), 'w') as f:
        f.write(summary)
    
    # Note on data limitations
    note = "Note: If SFR data is placeholder, results are illustrative. Source actual SPARC SFR data for robust analysis."
    print(note)
    with open(os.path.join(OUTPUT_DIR, 'cd010_results.txt'), 'a') as f:
        f.write(f"\n{note}")

if __name__ == "__main__":
    main()
