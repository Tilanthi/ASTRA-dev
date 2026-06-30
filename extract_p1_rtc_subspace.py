#!/usr/bin/env python3
"""
Extract P1 subspace comparison data from RTC campaign results.

P1 subspace: f = 1.0-1.2, β = 2.0, M = 2.5-3.0
This script filters RTC data to compare P1 vs RTC match rates.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path

# P1 subspace definition
P1_RANGES = {
    'f': (1.0, 1.2),
    'beta': (1.9, 2.1),  # Allow small tolerance around 2.0
    'M': (2.5, 3.0)
}

# HGBS windows
NN_WINDOW = (2.0 - 0.2, 2.0 + 0.2)  # λ/W = 2.0 ± 0.2
PM_WINDOW = (2.52, 3.08)  # Pairwise median window

def load_rtc_data():
    """Load RTC campaign data."""
    base_path = Path('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/simulations/referee_campaigns_jun2026')

    # Try different possible files
    candidates = [
        base_path / 'referee_combined_all.csv',
        base_path / 'referee_campaigns_all143_v2.csv',
        base_path / 'referee_campaigns_summary_v2.json'
    ]

    for candidate in candidates:
        if candidate.exists():
            print(f"Loading: {candidate}")
            if candidate.suffix == '.csv':
                return pd.read_csv(candidate)
            elif candidate.suffix == '.json':
                with open(candidate) as f:
                    return json.load(f)

    print("No RTC data file found!")
    return None

def filter_p1_subspace(df):
    """Filter RTC data to P1 subspace parameters."""
    if df is None or len(df) == 0:
        return None

    # Filter by f
    mask_f = (df['f'] >= P1_RANGES['f'][0]) & (df['f'] <= P1_RANGES['f'][1])

    # Filter by beta
    mask_beta = (df['beta'] >= P1_RANGES['beta'][0]) & (df['beta'] <= P1_RANGES['beta'][1])

    # Filter by M (if column exists)
    mask_M = pd.Series([True] * len(df))
    if 'M' in df.columns or 'Mach' in df.columns:
        m_col = 'M' if 'M' in df.columns else 'Mach'
        mask_M = (df[m_col] >= P1_RANGES['M'][0]) & (df[m_col] <= P1_RANGES['M'][1])

    # Combined mask
    p1_mask = mask_f & mask_beta & mask_M

    return df[p1_mask]

def calculate_match_rates(df, window_name, window_range):
    """Calculate HGBS match rates for given window."""
    if df is None or len(df) == 0:
        return None

    # Check for λ/W column (may be named differently)
    lw_col = None
    for col in ['lambda_W', 'lambda_W', 'lW', 'lw', 'lambda_over_W']:
        if col in df.columns:
            lw_col = col
            break

    if lw_col is None:
        print(f"No λ/W column found in data!")
        return None

    # Filter to measurable (non-null λ/W values)
    measurable = df[df[lw_col].notna()]

    # Calculate matches
    matches = measurable[(measurable[lw_col] >= window_range[0]) &
                         (measurable[lw_col] <= window_range[1])]

    results = {
        'window': window_name,
        'window_range': window_range,
        'total_sims': len(df),
        'measurable': len(measurable),
        'matches': len(matches),
        'match_rate': len(matches) / len(measurable) if len(measurable) > 0 else 0,
        'measurable_rate': len(measurable) / len(df)
    }

    return results

def main():
    """Main analysis function."""
    print("="*70)
    print("P1 vs RTC Subspace Comparison")
    print("="*70)

    # Load RTC data
    df = load_rtc_data()

    if df is None:
        print("\nERROR: Could not load RTC data")
        print("Please check referee_campaigns_jun2026 directory")
        return

    print(f"\nLoaded {len(df)} RTC simulations")
    print(f"Columns: {list(df.columns)}")

    # Filter to P1 subspace
    p1_df = filter_p1_subspace(df)

    if p1_df is None or len(p1_df) == 0:
        print("\nNo simulations in P1 subspace found!")
        print("This may mean:")
        print("  1. Column names don't match expected names")
        print("  2. P1 subspace parameters not covered in RTC")
        print("  3. Data file format different")
        return

    print(f"\nP1 subspace: {len(p1_df)} simulations")
    print(f"  f range: {p1_df['f'].min():.2f} - {p1_df['f'].max():.2f}")
    if 'beta' in p1_df.columns:
        print(f"  β range: {p1_df['beta'].min():.2f} - {p1_df['beta'].max():.2f}")
    if 'M' in p1_df.columns:
        print(f"  M range: {p1_df['M'].min():.2f} - {p1_df['M'].max():.2f}")

    # Calculate match rates for full RTC
    print("\n" + "="*70)
    print("FULL RTC CAMPAIGN (N = {})".format(len(df)))
    print("="*70)

    for name, window in [('PM window', PM_WINDOW), ('NN window', NN_WINDOW)]:
        results = calculate_match_rates(df, name, window)
        if results:
            print(f"\n{name} {window}:")
            print(f"  Total: {results['total_sims']}")
            print(f"  Measurable: {results['measurable']} ({results['measurable_rate']:.1%})")
            print(f"  Matches: {results['matches']}/{results['measurable']}")
            print(f"  Match rate: {results['match_rate']:.1%}")

    # Calculate match rates for P1 subspace
    print("\n" + "="*70)
    print("P1 SUBSPACE (N = {})".format(len(p1_df)))
    print("="*70)

    for name, window in [('PM window', PM_WINDOW), ('NN window', NN_WINDOW)]:
        results = calculate_match_rates(p1_df, name, window)
        if results:
            print(f"\n{name} {window}:")
            print(f"  Total: {results['total_sims']}")
            print(f"  Measurable: {results['measurable']} ({results['measurable_rate']:.1%})")
            print(f"  Matches: {results['matches']}/{results['measurable']}")
            print(f"  Match rate: {results['match_rate']:.1%}")

    # Save results
    output = {
        'analysis_date': '2026-06-06',
        'p1_subspace_definition': P1_RANGES,
        'rtc_total': len(df),
        'p1_subspace_total': len(p1_df),
        'full_rtc_results': {},
        'p1_subspace_results': {}
    }

    for name, window in [('PM', PM_WINDOW), ('NN', NN_WINDOW)]:
        rtc_res = calculate_match_rates(df, name, window)
        p1_res = calculate_match_rates(p1_df, name, window)
        output['full_rtc_results'][name] = rtc_res
        output['p1_subspace_results'][name] = p1_res

    output_file = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/simulations/p1_rtc_comparison.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n\nResults saved to: {output_file}")
    print("="*70)

if __name__ == '__main__':
    main()
