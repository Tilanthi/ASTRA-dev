# CD-009: Information-Theoretic Analysis of Cross-Domain Time Series
# Hypothesis: Mutual information between astrophysical and terrestrial time series should be zero
# if domains are independent. Non-zero MI would suggest unexpected connections.
# Approach: Compute MI between all pairs of time series from different domains,
# apply permutation tests for significance (p<0.01), use 10K bootstraps, BH correction.

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import StandardScaler
from scipy.stats import percentileofscore
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Define output paths
OUTPUT_DIR = '/shared/ASTRA/data/cross_domain/cd009_mutual_information'
PLOT_DIR = os.path.join(OUTPUT_DIR, 'plots')
os.makedirs(PLOT_DIR, exist_ok=True)

# Step 1: Load relevant time series data from all domains
# Astrophysics: SN Ia redshift vs time or distance modulus trend
# Climate: global temperature anomalies
# Economics: GDP trends (global or major economies)
# Epidemiology: COVID-19 cases time series (global or by country)
# We’ll use annual or monthly aggregated data where possible for consistency

def load_time_series():
    # Dictionary to store loaded time series
    time_series = {}
    
    # Astrophysics: SN Ia (using redshift as proxy for time evolution)
    try:
        sn_ia = pd.read_csv('/shared/ASTRA/data/discovery_run/data/sn_ia_pantheonplus.csv')
        sn_ia = sn_ia[['zHD', 'mB']].dropna()  # Redshift and apparent magnitude
        sn_ia = sn_ia.sort_values('zHD').rolling(window=50).mean().dropna()  # Smooth trend
        sn_ia_ts = sn_ia['mB'].values  # Magnitude as time series proxy
        time_series['SN_Ia_mB'] = {'data': sn_ia_ts, 'domain': 'Astrophysics', 'length': len(sn_ia_ts)}
    except (FileNotFoundError, KeyError):
        print("SN Ia data not found or invalid. Skipping Astrophysics domain.")

    # Climate: Global temperature anomalies
    try:
        temp = pd.read_csv('/shared/ASTRA/data/climate/global_temperature.csv')
        print("Temperature data columns:", temp.columns.tolist())
        # Try to find a reasonable temperature column dynamically
        temp_col = None
        for col in temp.columns:
            if 'mean' in col.lower() or 'temperature' in col.lower() or 'anomaly' in col.lower():
                temp_col = col
                break
        if temp_col is None and len(temp.columns) > 1:
            # Fallback: use the second column if no meaningful name found
            temp_col = temp.columns[1]
        if temp_col:
            # Ensure numeric data
            temp[temp_col] = pd.to_numeric(temp[temp_col], errors='coerce')
            temp_ts = temp[temp_col].dropna().values
            if len(temp_ts) > 0:
                time_series['Temperature_Anomaly'] = {'data': temp_ts, 'domain': 'Climate', 'length': len(temp_ts)}
                print(f"Using column '{temp_col}' for temperature data.")
            else:
                print("No valid numeric data in temperature column. Skipping Climate domain.")
        else:
            print("No suitable temperature column found. Skipping Climate domain.")
    except (FileNotFoundError, KeyError):
        print("Temperature data not found or invalid. Skipping Climate domain.")

    # Economics: Global GDP trend (will aggregate from country data if needed)
    try:
        gdp = pd.read_csv('/shared/ASTRA/data/economics/gdp.csv')
        gdp_global = gdp.groupby('Year')['GDP'].sum().reset_index()
        gdp_global = gdp_global[gdp_global['Year'] >= 1960]  # Modern era
        gdp_ts = gdp_global['GDP'].values
        time_series['Global_GDP'] = {'data': gdp_ts, 'domain': 'Economics', 'length': len(gdp_ts)}
    except (FileNotFoundError, KeyError):
        print("GDP data not found or invalid. Skipping Economics domain.")

    # Epidemiology: COVID-19 global daily cases, aggregated to monthly
    try:
        covid = pd.read_csv('/shared/ASTRA/data/epidemiology/covid_global.csv')
        covid['date'] = pd.to_datetime(covid['date'])
        # Rename the grouped columns to avoid conflicts
        covid_monthly = covid.groupby([covid['date'].dt.year.rename('year'), covid['date'].dt.month.rename('month')])['new_cases'].sum().reset_index()
        covid_ts = covid_monthly['new_cases'].values
        time_series['COVID_Cases'] = {'data': covid_ts, 'domain': 'Epidemiology', 'length': len(covid_ts)}
    except (FileNotFoundError, KeyError):
        print("COVID data not found or invalid. Skipping Epidemiology domain.")

    return time_series

# Step 2: Preprocess time series to handle different lengths
# Resample/interpolate to shortest common length for fair comparison
def normalize_length(ts1, ts2):
    min_len = min(len(ts1), len(ts2))
    if len(ts1) > min_len:
        indices = np.linspace(0, len(ts1)-1, min_len).astype(int)
        ts1 = ts1[indices]
    if len(ts2) > min_len:
        indices = np.linspace(0, len(ts2)-1, min_len).astype(int)
        ts2 = ts2[indices]
    return ts1, ts2

# Step 3: Compute mutual information with permutation test for significance
def compute_mi_with_significance(ts1, ts2, n_permutations=10000):
    # Standardize the data
    scaler = StandardScaler()
    ts1 = scaler.fit_transform(ts1.reshape(-1, 1)).flatten()
    ts2 = scaler.fit_transform(ts2.reshape(-1, 1)).flatten()

    # Compute actual MI
    mi_actual = mutual_info_regression(ts1.reshape(-1, 1), ts2)[0]

    # Permutation test
    mi_permuted = []
    for _ in range(n_permutations):
        ts2_perm = np.random.permutation(ts2)
        mi_perm = mutual_info_regression(ts1.reshape(-1, 1), ts2_perm)[0]
        mi_permuted.append(mi_perm)
    mi_permuted = np.array(mi_permuted)

    # P-value as fraction of permutations with MI >= actual MI
    p_value = 1 - percentileofscore(mi_permuted, mi_actual, kind='strict') / 100
    return mi_actual, p_value

# Step 4: Analyze all cross-domain pairs
def analyze_cross_domain_pairs(time_series):
    results = []
    pairs = []
    for ts1_name, ts1_info in time_series.items():
        for ts2_name, ts2_info in time_series.items():
            if ts1_info['domain'] != ts2_info['domain'] and (ts2_name, ts1_name) not in pairs:
                print(f'Computing MI for {ts1_name} ({ts1_info["domain"]}) vs {ts2_name} ({ts2_info["domain"]})')
                ts1_data, ts2_data = normalize_length(ts1_info['data'], ts2_info['data'])
                mi, p = compute_mi_with_significance(ts1_data, ts2_data)
                results.append({
                    'Pair': f'{ts1_name} vs {ts2_name}',
                    'Domain1': ts1_info['domain'],
                    'Domain2': ts2_info['domain'],
                    'MI': mi,
                    'P-value': p,
                    'Length': min(ts1_info['length'], ts2_info['length'])
                })
                pairs.append((ts1_name, ts2_name))
    return pd.DataFrame(results)

# Step 5: Apply multiple testing correction and report
def apply_correction(results_df):
    if not results_df.empty:
        p_values = results_df['P-value'].values
        corrected = multipletests(p_values, alpha=0.01, method='fdr_bh')
        results_df['Corrected_P-value'] = corrected[1]
        results_df['Significant'] = corrected[0]
    return results_df

# Step 6: Visualize results
def plot_mi_results(results_df):
    if results_df.empty:
        print("No results to plot.")
        return
    plt.figure(figsize=(10, 6))
    sns.barplot(data=results_df, x='MI', y='Pair', hue='Significant', dodge=False)
    plt.title('Mutual Information Across Cross-Domain Time Series Pairs')
    plt.xlabel('Mutual Information')
    plt.ylabel('Time Series Pair')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, 'cd009_mi_barplot.png'))
    plt.close()

    # Heatmap of MI values
    pivot = results_df.pivot_table(values='MI', index='Domain1', columns='Domain2', fill_value=0)
    plt.figure(figsize=(8, 6))
    sns.heatmap(pivot, annot=True, cmap='coolwarm', center=0)
    plt.title('Mutual Information Heatmap Across Domains')
    plt.savefig(os.path.join(PLOT_DIR, 'cd009_mi_heatmap.png'))
    plt.close()

# Main execution
def main():
    print('Loading time series data...')
    time_series = load_time_series()
    if len(time_series) < 2:
        print("Not enough data to perform cross-domain analysis. At least 2 domains are required.")
        with open(os.path.join(OUTPUT_DIR, 'cd009_summary.txt'), 'w') as f:
            f.write('CD-009 Mutual Information Analysis Summary\n')
            f.write('=======================================\n')
            f.write('Error: Insufficient data. Analysis aborted.\n')
        return
    print('Analyzing cross-domain pairs...')
    results_df = analyze_cross_domain_pairs(time_series)
    print('Applying multiple testing correction...')
    results_df = apply_correction(results_df)
    print('Generating plots...')
    plot_mi_results(results_df)

    # Save results
    if not results_df.empty:
        results_df.to_csv(os.path.join(OUTPUT_DIR, 'cd009_results.csv'), index=False)
    with open(os.path.join(OUTPUT_DIR, 'cd009_summary.txt'), 'w') as f:
        f.write('CD-009 Mutual Information Analysis Summary\n')
        f.write('=======================================\n')
        if results_df.empty:
            f.write('No cross-domain pairs analyzed due to insufficient data.\n')
        else:
            f.write(f'Total pairs analyzed: {len(results_df)}\n')
            significant = results_df[results_df['Significant']].sort_values('MI', ascending=False) if 'Significant' in results_df.columns else pd.DataFrame()
            f.write(f'Significant pairs (p<0.01 corrected): {len(significant)}\n')
            if not significant.empty:
                f.write('Top significant pairs:\n')
                for _, row in significant.head(3).iterrows():
                    f.write(f'- {row["Pair"]}: MI={row["MI"]:.4f}, p={row["Corrected_P-value"]:.4f}\n')
            else:
                f.write('No significant mutual information detected between cross-domain time series.\n')
        f.write('\nFull results in cd009_results.csv and plots in plots/ directory.\n')
    print('Analysis complete. Results saved to', OUTPUT_DIR)

if __name__ == '__main__':
    main()
