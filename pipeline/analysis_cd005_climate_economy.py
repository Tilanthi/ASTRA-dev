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

# Analysis Script for CD-005: GDP Growth vs Temperature Anomaly
# Objective: Test if national GDP growth rates relate nonlinearly to temperature anomalies
# Author: ASTRA Autonomous
# Date: 2026-04-03

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import os

# Paths
co2_path = '/shared/ASTRA/data/climate/co2_emissions.csv'
temp_path = '/shared/ASTRA/data/climate/global_temperature.csv'
output_dir = '/shared/ASTRA/data/climate/plots/'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Load data
co2_df = pd.read_csv(co2_path)
temp_df = pd.read_csv(temp_path, skiprows=1)  # Skip header row with title

# Prepare temperature data (average yearly anomalies)
temp_df['Year'] = temp_df['Year'].astype(int)
temp_df['Annual_Anomaly'] = temp_df['J-D'].replace('***', np.nan).astype(float)
temp_data = temp_df[['Year', 'Annual_Anomaly']].dropna()

# Prepare CO2 emissions and GDP data by country-year
co2_df = co2_df[['country', 'year', 'gdp', 'population', 'temperature_change_from_co2']].dropna(subset=['gdp', 'year'])
co2_df['year'] = co2_df['year'].astype(int)

# Compute GDP growth rates by country
def calculate_growth_rate(group):
    group = group.sort_values('year')
    group['gdp_growth'] = group['gdp'].pct_change() * 100  # Percentage change
    return group

country_growth = co2_df.groupby('country').apply(calculate_growth_rate).reset_index(drop=True)

# Merge with temperature data
# Since temperature data is global, we'll join on year
merged_data = pd.merge(country_growth, temp_data, left_on='year', right_on='Year', how='inner')

# Drop rows with missing critical values
analysis_data = merged_data.dropna(subset=['gdp_growth', 'Annual_Anomaly'])

print(f'Data points for analysis: {len(analysis_data)}')
print(f'Countries included: {analysis_data["country"].nunique()}')

# Analysis: Test for nonlinear relationship
X = analysis_data[['Annual_Anomaly']]
y = analysis_data['gdp_growth']

# Polynomial regression (quadratic to test for inverted-U shape)
poly = PolynomialFeatures(degree=2)
X_poly = poly.fit_transform(X)
model = LinearRegression()
model.fit(X_poly, y)
scores = cross_val_score(model, X_poly, y, cv=5, scoring='r2')

# Results
print(f'Model coefficients: {model.coef_}')
print(f'Intercept: {model.intercept_}')
print(f'Cross-validation R2 scores: {scores}')
print(f'Average R2: {scores.mean()}')

# Determine if there is a peak (optimal temperature) - for quadratic, check if coefficient for x^2 is negative
is_peaked = model.coef_[2] < 0
if is_peaked:
    optimal_temp = -model.coef_[1] / (2 * model.coef_[2])
    print(f'Optimal temperature anomaly for GDP growth: {optimal_temp:.2f} °C')
else:
    print('No optimal temperature found; relationship may not be peaked.')

# Visualization
plt.figure(figsize=(10, 6))
plt.scatter(X, y, alpha=0.5, label='Data points')

# Plot the fitted curve
X_range = np.linspace(X.min(), X.max(), 100).reshape(-1, 1)
X_range_poly = poly.transform(X_range)
y_pred = model.predict(X_range_poly)
plt.plot(X_range, y_pred, color='red', label='Quadratic fit')

plt.xlabel('Temperature Anomaly (°C)')
plt.ylabel('GDP Growth Rate (%)')
plt.title('GDP Growth vs Temperature Anomaly (CD-005)')
plt.legend()
plt.grid(True)
plot_path = os.path.join(output_dir, 'cd005_gdp_growth_vs_temp_anomaly.png')
plt.savefig(plot_path)
plt.close()

print(f'Plot saved to {plot_path}')

# Save results summary
summary_path = '/shared/ASTRA/hypotheses/cd005_results.txt'
with open(summary_path, 'w') as f:
    f.write(f'CD-005 Analysis Results\n')
    f.write(f'-----------------------\n')
    f.write(f'Data points analyzed: {len(analysis_data)}\n')
    f.write(f'Countries included: {analysis_data["country"].nunique()}\n')
    f.write(f'R2 Cross-validation scores: {scores}\n')
    f.write(f'Average R2: {scores.mean():.3f}\n')
    if is_peaked:
        f.write(f'Optimal temperature anomaly for GDP growth: {optimal_temp:.2f} °C\n')
    else:
        f.write('No optimal temperature found; relationship may not be peaked.\n')
    f.write(f'Plot saved to: {plot_path}\n')

print(f'Results summary saved to {summary_path}')