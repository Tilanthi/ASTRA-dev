# H015 Analysis: RAR Scatter vs Star Formation Rate Proxies
# Created: 2026-04-03
# Objective: Test if RAR scatter correlates with SFR proxies (SB_disk) in SPARC galaxies

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Constants (CGS units from UnifiedPhysicsEngine)
G = 6.674e-8  # cm^3 g^-1 s^-2
M_sun = 1.989e33  # g
pc = 3.0857e18  # cm

# Paths
SPARC_CATALOG = '/shared/ASTRA/data/discovery_run/sparc_catalog.csv'
GSWLC_MATCHED = '/shared/ASTRA/data/h015_star_formation/sparc_gswlc_matched.csv'
OUTPUT_PLOT = '/shared/ASTRA/data/discovery_run/plots/h015_rar_scatter_vs_sfr_proxy.png'
OUTPUT_RESULTS = '/shared/ASTRA/hypotheses/h015_results.txt'

# Helper functions
def load_sparc_data():
    """Load SPARC catalog and filter for analysis."""
    df = pd.read_csv(SPARC_CATALOG)
    # Filter for galaxies with rotation curve data and quality flag
    df = df[df['V_flat_kms'] > 0]  # Ensure we have valid flat velocity
    return df

def compute_rar_scatter(df):
    """Compute RAR scatter as g_obs vs g_bar at a reference radius."""
    # Placeholder: Compute RAR scatter using simplified g_bar and g_obs
    # g_bar = baryonic acceleration, approximated from mass models if available
    # For simplicity, use V^2/R at R_eff as proxy (needs full rotation curve ideally)
    df['R_eff_pc'] = df['R_eff_kpc'] * 1e3  # kpc to pc
    df['R_eff_cm'] = df['R_eff_pc'] * pc
    df['M_bar'] = df['L_36_1e9_Lsun'] * 0.5  # Rough L to M conversion (Upsilon=0.5)
    df['M_bar_g'] = df['M_bar'] * M_sun
    df['g_bar'] = (G * df['M_bar_g']) / (df['R_eff_cm'] ** 2)  # baryonic acceleration
    df['V_eff'] = df['V_flat_kms']  # Approximate
    df['g_obs'] = (df['V_eff'] ** 2) / (df['R_eff_kpc'] * 1e5)  # V^2/R in cm/s^2
    df['log_g_bar'] = np.log10(df['g_bar'])
    df['log_g_obs'] = np.log10(df['g_obs'])
    # Fit linear relation to log(g_obs) vs log(g_bar)
    X = df[['log_g_bar']].values
    y = df['log_g_obs'].values
    model = LinearRegression()
    model.fit(X, y)
    df['log_g_pred'] = model.predict(X)
    df['rar_residual'] = df['log_g_obs'] - df['log_g_pred']
    return df, model.coef_[0], model.intercept_, r2_score(y, df['log_g_pred'])

def compute_sfr_proxies(df):
    """Compute SFR surface density proxies like SB_disk."""
    df['R_disk_pc'] = df['R_disk_kpc'] * 1e3  # kpc to pc
    df['area_disk'] = np.pi * (df['R_disk_pc'] * pc) ** 2  # cm^2
    df['Sigma_star'] = (df['L_36_1e9_Lsun'] * M_sun * 0.5) / df['area_disk']  # g/cm^2
    df['log_SB_disk'] = np.log10(df['SB_disk_Lsun_pc2'])
    df['log_Sigma_star'] = np.log10(df['Sigma_star'])
    return df

def correlate_residuals(df):
    """Correlate RAR residuals with SFR proxies."""
    correlations = []
    for proxy in ['log_SB_disk', 'log_Sigma_star']:
        mask = df[proxy].notna() & df['rar_residual'].notna()
        if mask.sum() > 10:
            rho, p_val = spearmanr(df.loc[mask, proxy], df.loc[mask, 'rar_residual'])
            correlations.append({'proxy': proxy, 'rho': rho, 'p_val': p_val, 'n': mask.sum()})
    return pd.DataFrame(correlations)

def validate_with_gswlc(sparc_df):
    """Validate SFR proxy using GSWLC matched data."""
    gswlc = pd.read_csv(GSWLC_MATCHED)
    # Merge with sparc_df to get proxies
    merged = pd.merge(sparc_df, gswlc, on='galaxy', how='inner')
    # Check correlation between logSFR and proxies in matched sample
    correlations = []
    for proxy in ['log_SB_disk', 'log_Sigma_star']:
        mask = merged[proxy].notna() & merged['gswlc_logSFR'].notna()
        if mask.sum() > 5:
            rho, p_val = pearsonr(merged.loc[mask, proxy], merged.loc[mask, 'gswlc_logSFR'])
            correlations.append({'proxy': proxy, 'rho': rho, 'p_val': p_val, 'n': mask.sum()})
    return pd.DataFrame(correlations)

def plot_results(df, correlations):
    """Plot RAR residuals vs SFR proxies."""
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.scatter(df['log_g_bar'], df['log_g_obs'], c=df['rar_residual'], cmap='viridis', alpha=0.5)
    plt.colorbar(label='RAR Residual (log g_obs - log g_pred)')
    plt.xlabel('log(g_bar) [cm/s²]')
    plt.ylabel('log(g_obs) [cm/s²]')
    plt.title('RAR with Residuals')
    plt.subplot(1, 2, 2)
    plt.scatter(df['log_SB_disk'], df['rar_residual'], alpha=0.5)
    plt.xlabel('log(SB_disk) [L_sun/pc²]')
    plt.ylabel('RAR Residual')
    plt.title(f'RAR Residual vs SB_disk\nrho={correlations.loc[correlations["proxy"] == "log_SB_disk", "rho"].values[0]:.2f}, p={correlations.loc[correlations["proxy"] == "log_SB_disk", "p_val"].values[0]:.3f}')
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT)
    plt.close()

def save_results(df, correlations, slope, intercept, r2, validation):
    """Save analysis results."""
    with open(OUTPUT_RESULTS, 'w') as f:
        f.write('H015 Analysis Results\n')
        f.write('=====================\n')
        f.write(f'RAR Fit: slope={slope:.2f}, intercept={intercept:.2f}, R2={r2:.3f}\n')
        f.write(f'Sample size: {len(df)} galaxies\n')
        f.write('\nCorrelations with RAR Residuals:\n')
        for _, row in correlations.iterrows():
            f.write(f"{row['proxy']}: rho={row['rho']:.3f}, p={row['p_val']:.3e}, n={row['n']}\n")
        f.write('\nValidation with GSWLC (actual SFR):\n')
        for _, row in validation.iterrows():
            f.write(f"Proxy {row['proxy']} vs logSFR: r={row['rho']:.3f}, p={row['p_val']:.3e}, n={row['n']}\n")
        f.write('\nConclusion: TBC after full analysis\n')

# Main Analysis
def main():
    # Step 1: Load data
    sparc_df = load_sparc_data()
    print(f'Loaded {len(sparc_df)} SPARC galaxies')
    
    # Step 2: Compute RAR scatter
    sparc_df, slope, intercept, r2 = compute_rar_scatter(sparc_df)
    print(f'RAR fit: slope={slope:.2f}, intercept={intercept:.2f}, R2={r2:.3f}')
    
    # Step 3: Compute SFR proxies
    sparc_df = compute_sfr_proxies(sparc_df)
    
    # Step 4: Correlate RAR residuals with SFR proxies
    correlations = correlate_residuals(sparc_df)
    print('Correlations with RAR residuals:')
    print(correlations)
    
    # Step 5: Validate proxies using GSWLC matched data
    validation = validate_with_gswlc(sparc_df)
    print('Validation with GSWLC actual SFR:')
    print(validation)
    
    # Step 6: Generate plots
    plot_results(sparc_df, correlations)
    
    # Step 7: Save results
    save_results(sparc_df, correlations, slope, intercept, r2, validation)
    print(f'Results saved to {OUTPUT_RESULTS}')

if __name__ == '__main__':
    main()
