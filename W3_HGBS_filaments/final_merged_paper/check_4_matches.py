#!/usr/bin/env python3
"""
Check the 4 matches in the [2.5, 4.0] window to understand the source of the claim.
"""

import pandas as pd

# Read RTC results
rtc_file = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/simulations/realistic_turbulence_jun2026/data/RTC_results_final.csv"
df = pd.read_csv(rtc_file)

# Get valid measurements
valid = df[df['lW_status'].isin(['ok:5_peaks', 'ok:4_peaks', 'ok:3_peaks', 'ok:6_peaks', 'ok:2_peaks'])]

# Window [2.5, 4.0]
in_window = valid[(valid['lW'] >= 2.5) & (valid['lW'] <= 4.0)]
print(f"=== 4 MATCHES IN WINDOW [2.5, 4.0] ===")
print(in_window[['run_id', 'f', 'beta', 'mturb', 'theta', 'lW', 'lW_status']].to_string())

# The actual HGBS window [2.52, 3.08]
hgbs_window = valid[(valid['lW'] >= 2.52) & (valid['lW'] <= 3.08)]
print(f"\n=== ACTUAL HGBS WINDOW [2.52, 3.08] ===")
print(f"Matches: {len(hgbs_window)}")
if len(hgbs_window) > 0:
    print(hgbs_window[['run_id', 'f', 'beta', 'mturb', 'theta', 'lW', 'lW_status']].to_string())
