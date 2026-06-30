#!/usr/bin/env python3
"""
Analyze RTC campaign data to compute restricted matching rate for
physically motivated subspace addressing Referee Concern 3.

HGBS matching window: λ/W ∈ [2.52, 3.08]
"""

import pandas as pd
import numpy as np

# Read RTC results
rtc_file = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/simulations/realistic_turbulence_jun2026/data/RTC_results_final.csv"
df = pd.read_csv(rtc_file)

print(f"Total RTC simulations: {len(df)}")
print(f"Columns: {df.columns.tolist()}")

# HGBS matching window
hgbs_min = 2.52
hgbs_max = 3.08

# Check which columns have λ/W data
print(f"\nλ/W column name: 'lW'")
print(f"λ/W status column: 'lW_status'")
print(f"Unique lW_status values: {df['lW_status'].unique()}")

# Count simulations with valid λ/W measurements
valid_lw = df[df['lW_status'].isin(['ok:5_peaks', 'ok:4_peaks', 'ok:3_peaks', 'ok'])]
print(f"\nSimulations with valid λ/W measurements: {len(valid_lw)}")

# Count HGBS matches in full sample
hgbs_matches = df[(df['lW'] >= hgbs_min) & (df['lW'] <= hgbs_max) &
                  (df['lW_status'].isin(['ok:5_peaks', 'ok:4_peaks', 'ok:3_peaks', 'ok']))]
print(f"HGBS matches (full sample): {len(hgbs_matches)} / {len(df)} = {100*len(hgbs_matches)/len(df):.2f}%")

# Define physically motivated subspace
# Based on observational constraints:
# β ∈ [1, 2] (magnetically regulated regime from Pattle et al. 2019)
# f ∈ [1.2, 2.0] (actively fragmenting filaments, not extremely supercritical)
# θ = 0° (longitudinal B - may need to include mild oblique)
# M ∈ [1, 3] (transonic turbulence typical of HGBS filaments)

restricted = df[
    (df['beta'] >= 1.0) & (df['beta'] <= 2.0) &
    (df['f'] >= 1.2) & (df['f'] <= 2.0) &
    (df['theta'] == 0) &
    (df['mturb'] >= 1.0) & (df['mturb'] <= 3.0)
]

print(f"\n=== RESTRICTED (PHYSICALLY MOTIVATED) SUBSPACE ===")
print(f"Criteria: β∈[1,2], f∈[1.2,2.0], θ=0° (longitudinal), M∈[1,3]")
print(f"Total simulations in restricted subspace: {len(restricted)}")

# Valid λ/W measurements in restricted subspace
restricted_valid = restricted[restricted['lW_status'].isin(['ok:5_peaks', 'ok:4_peaks', 'ok:3_peaks', 'ok'])]
print(f"Valid λ/W measurements in restricted subspace: {len(restricted_valid)}")

# HGBS matches in restricted subspace
restricted_matches = restricted[(restricted['lW'] >= hgbs_min) & (restricted['lW'] <= hgbs_max) &
                                (restricted['lW_status'].isin(['ok:5_peaks', 'ok:4_peaks', 'ok:3_peaks', 'ok']))]

print(f"HGBS matches in restricted subspace: {len(restricted_matches)}")

if len(restricted_valid) > 0:
    print(f"Restricted matching rate: {len(restricted_matches)} / {len(restricted_valid)} = {100*len(restricted_matches)/len(restricted_valid):.2f}%")
else:
    print(f"Restricted matching rate: N/A (no valid λ/W measurements)")

# Test alternative subspace definitions
print(f"\n=== ALTERNATIVE SUBSPACE DEFINITIONS ===")

# Alternative 1: Include mild oblique (θ ∈ [0, 30])
alt1 = df[
    (df['beta'] >= 1.0) & (df['beta'] <= 2.0) &
    (df['f'] >= 1.2) & (df['f'] <= 2.0) &
    (df['theta'] <= 30) &
    (df['mturb'] >= 1.0) & (df['mturb'] <= 3.0)
]
alt1_valid = alt1[alt1['lW_status'].isin(['ok:5_peaks', 'ok:4_peaks', 'ok:3_peaks', 'ok'])]
alt1_matches = alt1[(alt1['lW'] >= hgbs_min) & (alt1['lW'] <= hgbs_max) &
                    (alt1['lW_status'].isin(['ok:5_peaks', 'ok:4_peaks', 'ok:3_peaks', 'ok']))]
print(f"Alt 1 (θ ≤ 30°): {len(alt1_matches)} / {len(alt1_valid)} = {100*len(alt1_matches)/len(alt1_valid):.2f}%" if len(alt1_valid) > 0 else "Alt 1: N/A")

# Alternative 2: Wider β range [0.5, 3]
alt2 = df[
    (df['beta'] >= 0.5) & (df['beta'] <= 3.0) &
    (df['f'] >= 1.2) & (df['f'] <= 2.0) &
    (df['theta'] == 0) &
    (df['mturb'] >= 1.0) & (df['mturb'] <= 3.0)
]
alt2_valid = alt2[alt2['lW_status'].isin(['ok:5_peaks', 'ok:4_peaks', 'ok:3_peaks', 'ok'])]
alt2_matches = alt2[(alt2['lW'] >= hgbs_min) & (alt2['lW'] <= hgbs_max) &
                    (alt2['lW_status'].isin(['ok:5_peaks', 'ok:4_peaks', 'ok:3_peaks', 'ok']))]
print(f"Alt 2 (β ∈ [0.5, 3]): {len(alt2_matches)} / {len(alt2_valid)} = {100*len(alt2_matches)/len(alt2_valid):.2f}%" if len(alt2_valid) > 0 else "Alt 2: N/A")

# Summary statistics
print(f"\n=== SUMMARY STATISTICS FOR PAPER ===")
print(f"Full sample matching rate: {100*len(hgbs_matches)/len(df):.2f}% ({len(hgbs_matches)}/{len(df)})")
print(f"Restricted subspace matching rate: {100*len(restricted_matches)/len(restricted_valid):.2f}% ({len(restricted_matches)}/{len(restricted_valid)})" if len(restricted_valid) > 0 else "Restricted: N/A")
print(f"\nConclusion: ", end="")
if len(restricted_valid) > 0 and len(restricted_matches) > 0:
    rate = 100*len(restricted_matches)/len(restricted_valid)
    if rate > 10:
        print(f"The restricted matching rate ({rate:.1f}%) is substantially higher than the global rate, supporting Interpretation A.")
    else:
        print(f"Even the restricted matching rate ({rate:.1f}%) remains low, suggesting Interpretation B cannot be dismissed.")
else:
    print("Insufficient valid λ/W measurements in restricted subspace to draw conclusions.")

# Print some example matches
if len(hgbs_matches) > 0:
    print(f"\n=== EXAMPLE HGBS MATCHES (FULL SAMPLE) ===")
    print(hgbs_matches[['run_id', 'f', 'beta', 'mturb', 'theta', 'lW', 'lW_status']].head(10).to_string())
