#!/usr/bin/env python3
"""
Verify the RTC λ/W values to check for HGBS matches.
HGBS window: [2.52, 3.08]
"""

import pandas as pd
import numpy as np

# Read RTC results
rtc_file = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/simulations/realistic_turbulence_jun2026/data/RTC_results_final.csv"
df = pd.read_csv(rtc_file)

# HGBS window
hgbs_min, hgbs_max = 2.52, 3.08

print(f"Looking for λ/W in HGBS window: [{hgbs_min}, {hgbs_max}]")

# Check all valid measurements
valid = df[df['lW_status'].isin(['ok:5_peaks', 'ok:4_peaks', 'ok:3_peaks', 'ok:6_peaks', 'ok:2_peaks'])]
print(f"\nValid measurements: {len(valid)}")

# Find values in HGBS window
in_window = valid[(valid['lW'] >= hgbs_min) & (valid['lW'] <= hgbs_max)]
print(f"\nValues IN HGBS window: {len(in_window)}")

if len(in_window) > 0:
    print("\nHGBS matches found:")
    print(in_window[['run_id', 'f', 'beta', 'mturb', 'theta', 'lW', 'lW_status']].to_string())
else:
    print("\nNO HGBS matches found!")

# Find closest values
valid['dist_to_window'] = np.minimum(
    np.abs(valid['lW'] - hgbs_min),
    np.abs(valid['lW'] - hgbs_max)
)
closest = valid.nsmallest(20, 'dist_to_window')

print(f"\n=== 20 CLOSEST VALUES TO HGBS WINDOW ===")
print(closest[['run_id', 'f', 'beta', 'mturb', 'theta', 'lW', 'lW_status', 'dist_to_window']].to_string())

# Check if any values might be in a slightly different window
print(f"\n=== CHECKING ALTERNATIVE WINDOWS ===")
for w_min, w_max in [(2.0, 3.5), (2.5, 4.0), (3.0, 4.5)]:
    in_alt = valid[(valid['lW'] >= w_min) & (valid['lW'] <= w_max)]
    print(f"Window [{w_min}, {w_max}]: {len(in_alt)} matches")
