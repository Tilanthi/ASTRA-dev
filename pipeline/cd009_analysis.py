# ASTRA Cross-Domain Analysis for CD-009: Information-Theoretic Analysis of Cross-Domain Time Series
# Date: 2026-04-03
# Hypothesis: Mutual information (MI) between astrophysical and terrestrial time series should be zero if domains are independent.
# Objective: Compute MI between all pairs of time series; apply permutation tests for significance.

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression
from scipy.stats import percentileofscore
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

# Output directory for plots and results
OUTPUT_DIR = '/shared/ASTRA/data/cross_domain/cd009_mi_analysis/'
PLOT_DIR = os.path.join(OUTPUT_DIR, 'plots')
RESULTS_FILE = os.path.join(OUTPUT_DIR, 'mi_results.txt')
os.makedirs(PLOT_DIR, exist_ok=True)

# Function to load and preprocess time series data
def load_time_series(file_path, time_col, value_col, name):
    try:
        df = pd.read_csv(file_path)
        df[time_col] = pd.to_datetime(df[time_col])
        df = df.sort_values(time_col)
        return {
            'name': name,
            'time': df[time_col].values,
            'value': df[value_col].values
        }
    except Exception as e:
        print(f'Error loading {name}: {e}')
        return None

# List of time series datasets to analyze
# Astrophysics
datasets = [
    {'path': '/shared/ASTRA/data/discovery_run/cmb_power_spectrum.csv', 'time_col': 'ell', 'value_col': 'D_ell', 'name': 'CMB Power Spectrum'},
    {'path': '/shared/ASTRA/data/discovery_run/sn_ia_pantheonplus.csv', 'time_col': 'z', 'value_col': 'm_B', 'name': 'SN Ia Magnitude'},
    # Terrestrial
    {'path': '/shared/ASTRA/data/climate/global_temperature.csv', 'time_col': 'Year', 'value_col': 'Annual_Mean', 'name': 'Global Temperature Anomaly'},
    # Economics - using VIX as time series
    {'path': '/shared/ASTRA/data/economics/vix_volatility.csv', 'time_col': 'Date', 'value_col': 'VIX_Close', 'name': 'VIX Volatility Index'},
    # Epidemiology - aggregate COVID cases to global daily
    {'path': '/shared/ASTRA/data/epidemiology/covid_global.csv', 'time_col': 'date', 'value_col': 'new_cases', 'name': 'COVID Daily New Cases'}
]

# Load all datasets
loaded_series = []
for ds in datasets:
    ts = load_time_series(ds['path'], ds['time_col'], ds['value_col'], ds['name'])
    if ts is not None:
        loaded_series.append(ts)

# For COVID data, aggregate to global daily if loaded
for ts in loaded_series:
    if ts['name'] == 'COVID Daily New Cases':
        df = pd.read_csv('/shared/ASTRA/data/epidemiology/covid_global.csv')
        df['date'] = pd.to_datetime(df['date'])
        global_daily = df.groupby('date')['new_cases'].sum().reset_index()
        ts['time'] = global_daily['date'].values
        ts['value'] = global_daily['new_cases'].values

# Function to align two time series by interpolating to common time points
def align_time_series(ts1, ts2):
    # Convert time to numeric for interpolation (if datetime)
    t1 = pd.to_numeric(pd.Series(ts1['time'])).values if isinstance(ts1['time'][0], pd.Timestamp) else ts1['time']
    t2 = pd.to_numeric(pd.Series(ts2['time'])).values if isinstance(ts2['time'][0], pd.Timestamp) else ts2['time']
    # Find overlapping range
    t_common = np.linspace(max(t1[0], t2[0]), min(t1[-1], t2[-1]), num=100)
    # Interpolate both series to common time points
    v1 = np.interp(t_common, t1, ts1['value'])
    v2 = np.interp(t_common, t2, ts2['value'])
    return v1, v2

# Compute mutual information and perform permutation test
def compute_mi_with_permutation(ts1, ts2, n_permutations=10000):
    try:
        v1, v2 = align_time_series(ts1, ts2)
        if len(v1) < 2 or len(v2) < 2:
            return None, None, 'Insufficient overlapping data'
        # Compute true MI
        mi_true = mutual_info_regression(v1.reshape(-1, 1), v2)[0]
        # Permutation test
        mi_perm = []
        for _ in range(n_permutations):
            v2_perm = np.random.permutation(v2)
            mi_perm.append(mutual_info_regression(v1.reshape(-1, 1), v2_perm)[0])
        # Compute p-value
        p_value = 1 - (percentileofscore(mi_perm, mi_true) / 100)
        return mi_true, p_value, 'Success'
    except Exception as e:
        return None, None, f'Error: {str(e)}'

# Analyze all pairs
results = []
with open(RESULTS_FILE, 'w') as f:
    f.write('ASTRA CD-009 Mutual Information Analysis Results\n')
    f.write('Date: 2026-04-03\n')
    f.write('-----------------------------------------------\n\n')
    for i in range(len(loaded_series)):
        for j in range(i+1, len(loaded_series)):
            ts1 = loaded_series[i]
            ts2 = loaded_series[j]
            pair_name = f"{ts1['name']} vs {ts2['name']}"
            print(f'Analyzing pair: {pair_name}')
            mi, p_val, status = compute_mi_with_permutation(ts1, ts2)
            if mi is not None:
                result_line = f"Pair: {pair_name}\nMutual Information: {mi:.6f}\np-value (permutation test): {p_val:.6f}\nStatus: {status}\n\n"
                f.write(result_line)
                results.append({
                    'pair': pair_name,
                    'mi': mi,
                    'p_value': p_val
                })
                # Plot the aligned time series
                v1, v2 = align_time_series(ts1, ts2)
                plt.figure(figsize=(10, 6))
                plt.subplot(2, 1, 1)
                plt.plot(v1, label=ts1['name'])
                plt.legend()
                plt.subplot(2, 1, 2)
                plt.plot(v2, label=ts2['name'], color='orange')
                plt.legend()
                plt.suptitle(f"Time Series Comparison: {pair_name}\nMI = {mi:.4f}, p = {p_val:.4f}")
                plt.tight_layout()
                plot_file = os.path.join(PLOT_DIR, f"mi_plot_{i}_{j}.png")
                plt.savefig(plot_file)
                plt.close()
            else:
                f.write(f"Pair: {pair_name}\nMutual Information: N/A\np-value: N/A\nStatus: {status}\n\n")

# Summary of significant results
significant = [r for r in results if r['p_value'] < 0.01]
with open(RESULTS_FILE, 'a') as f:
    f.write('Summary of Significant Results (p < 0.01):\n')
    if significant:
        for r in significant:
            f.write(f"- {r['pair']}: MI = {r['mi']:.6f}, p = {r['p_value']:.6f}\n")
    else:
        f.write('No significant mutual information found between any cross-domain time series pairs.\n')

print(f'Analysis complete. Results saved to {RESULTS_FILE}')
print(f'Plots saved to {PLOT_DIR}')
