#!/usr/bin/env python3
"""
Selection Bias Analysis for Orion B NN Analysis

This script addresses Major Concern 2 from observational astronomer review:
Only 10.2% of Orion B cores (188/1,844) are included in NN analysis.
Are the included cores representative of the full population?

Properties to analyze:
- Core mass (M_core)
- Dust temperature (T_dust)
- Bonnor-Ebert ratio (alpha_BE)
- Core type (starless=1, prestellar=2, protostellar=3)
- Peak column density (Nh2_peak)
- Average volume density (nh2_ave)

Author: ASTRA Analysis System
Date: 2026-05-05
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
import pandas as pd
import json

def parse_hgbs_orionb_catalog(catalog_file):
    """
    Parse HGBS Orion B catalog file.

    Returns DataFrame with core properties.
    """
    print(f"Parsing HGBS Orion B catalog: {catalog_file}")

    cores = []
    with open(catalog_file, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    # Find data start (after header)
    data_start = None
    for i, line in enumerate(lines):
        if line.startswith('---'):
            data_start = i + 1
            break

    if data_start is None:
        print("ERROR: Could not find data start marker")
        return None

    # Parse data lines
    for line in lines[data_start:]:
        line = line.strip()
        if not line or line.startswith(('|', '!')):
            continue

        parts = line.split()
        if len(parts) < 19:
            continue

        try:
            # Parse core ID
            core_id = int(parts[0])

            # Parse coordinates (RA, Dec)
            ra_str = parts[2]
            dec_str = parts[3]

            # Parse physical properties
            # Columns: (7) M_core, (8) M_core_err, (9) T_dust, (10) T_dust_err,
            #          (11) Nh2_peak, (12-13) Nh2_ave, (14-15) nh2_peak/ave,
            #          (16) alpha_BE, (17) core_type

            m_core = float(parts[6]) if parts[6] != '9999.99' else np.nan
            t_dust = float(parts[8]) if parts[8] != '9999.99' else np.nan
            nh2_peak = float(parts[10]) if parts[10] != '9999.99' else np.nan
            nh2_ave = float(parts[11]) if parts[11] != '9999.99' else np.nan
            alpha_be = float(parts[15]) if parts[15] != '9999.99' else np.nan
            core_type = int(parts[16]) if parts[16].isdigit() else -1

            cores.append({
                'id': core_id,
                'ra': ra_str,
                'dec': dec_str,
                'm_core': m_core,
                't_dust': t_dust,
                'nh2_peak': nh2_peak,
                'nh2_ave': nh2_ave,
                'alpha_be': alpha_be,
                'core_type': core_type
            })
        except (ValueError, IndexError) as e:
            continue

    df = pd.DataFrame(cores)
    print(f"Parsed {len(df)} cores from catalog")
    return df


def load_nn_included_cores(nn_results_file):
    """
    Load list of cores included in NN analysis.

    NOTE: The current NN results JSON does NOT contain individual core IDs.
    This is a limitation that prevents full selection bias analysis.

    Returns: None with explanation
    """
    print(f"\nChecking NN results file: {nn_results_file}")

    if not Path(nn_results_file).exists():
        print(f"ERROR: NN results file not found")
        return None

    with open(nn_results_file, 'r') as f:
        data = json.load(f)

    print(f"NN results keys: {list(data.keys())}")
    print(f"Statistics keys: {list(data.get('statistics', {}).keys())}")

    # Check if individual core data is available
    if 'included_core_ids' in data:
        return data['included_core_ids']
    elif 'cores' in data and isinstance(data['cores'], list):
        return [c['id'] for c in data['cores']]
    else:
        print("\n" + "="*80)
        print("CRITICAL LIMITATION: NN results file does NOT contain individual core IDs")
        print("="*80)
        print("\nThe NN analysis JSON file contains only summary statistics:")
        print(f"  - n_filament_groups: {data['statistics']['n_filament_groups']}")
        print(f"  - n_cores_used: {data['statistics']['n_cores_used']}")
        print(f"  - n_spacings: {data['statistics']['n_spacings']}")
        print("\nIt does NOT contain:")
        print("  - List of which 188 cores were included")
        print("  - Core-spine association mapping")
        print("  - Individual core properties")
        print("\nWithout this information, we CANNOT perform a proper selection bias")
        print("analysis to compare included vs excluded cores.")
        print("\nRecommendation:")
        print("  The original NN analysis code that generated these results must be")
        print("  re-run to output the list of included core IDs. Then this analysis")
        print("  can be performed properly.")
        print("="*80)

        return None


def perform_selection_bias_analysis(full_catalog, included_core_ids):
    """
    Perform selection bias analysis comparing included vs excluded cores.

    This requires the list of included core IDs, which is not currently available.
    """

    if included_core_ids is None:
        print("\n" + "="*80)
        print("SELECTION BIAS ANALYSIS - HONEST ASSESSMENT")
        print("="*80)
        print("\nCANNOT perform full selection bias analysis because:")
        print("  1. NN results file does not contain individual core IDs")
        print("  2. Core-spine association mapping not available")
        print("  3. Original NN analysis code output not available")

        print("\nWhat we CAN say:")
        print(f"  - Full catalog: {len(full_catalog)} cores")
        print(f"  - NN analysis: 188 cores (10.2%)")
        print(f"  - Excluded: 1,656 cores (89.8%)")

        print("\nWhat we CANNOT determine without core ID list:")
        print("  - Whether included cores have different mass distribution")
        print("  - Whether included cores have different temperature distribution")
        print("  - Whether included cores have different evolutionary state distribution")
        print("  - Whether included cores are preferentially in certain environments")

        print("\nHonest assessment for paper:")
        print("  The 10.2% inclusion rate with unknown selection properties is a")
        print("  CRITICAL limitation. We cannot assume the NN sample is")
        print("  representative without quantifying the selection bias.")

        print("\nRequired for full analysis:")
        print("  1. Re-run original NN analysis with core ID output")
        print("  2. Compare mass/temp/density/type distributions")
        print("  3. Perform KS tests for each property")
        print("  4. Quantify selection bias magnitude")

        print("="*80)
        return

    # If we had the core IDs, this is what we would do:
    print("\nPerforming selection bias analysis...")

    # Create masks
    included_mask = full_catalog['id'].isin(included_core_ids)
    df_included = full_catalog[included_mask]
    df_excluded = full_catalog[~included_mask]

    print(f"\nSample sizes:")
    print(f"  Included: {len(df_included)} cores")
    print(f"  Excluded: {len(df_excluded)} cores")

    properties = ['m_core', 't_dust', 'nh2_peak', 'alpha_be']

    for prop in properties:
        print(f"\n{prop}:")
        inc_values = df_included[prop].dropna()
        exc_values = df_excluded[prop].dropna()

        print(f"  Included: mean={np.mean(inc_values):.3f}, std={np.std(inc_values):.3f}")
        print(f"  Excluded: mean={np.mean(exc_values):.3f}, std={np.std(exc_values):.3f}")

        # KS test
        ks_stat, p_value = stats.ks_2samp(inc_values, exc_values)
        print(f"  KS test: statistic={ks_stat:.3f}, p={p_value:.3f}")

        if p_value < 0.05:
            print(f"  ** SIGNIFICANT DIFFERENCE (p < 0.05) **")
        else:
            print(f"  No significant difference")

    # Core type distribution
    print(f"\nCore type distribution:")
    for core_type in [1, 2, 3]:
        type_name = {1: 'starless', 2: 'prestellar', 3: 'protostellar'}[core_type]
        inc_frac = (df_included['core_type'] == core_type).sum() / len(df_included)
        exc_frac = (df_excluded['core_type'] == core_type).sum() / len(df_excluded)
        print(f"  {type_name}: included={inc_frac:.1%}, excluded={exc_frac:.1%}")


def main():
    """Main analysis routine."""

    print("="*80)
    print("SELECTION BIAS ANALYSIS FOR ORION B NN MEASUREMENT")
    print("="*80)

    # File paths
    catalog_file = Path('/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/HGBS_orionb_derived_core_catalog.txt')
    nn_results_file = Path('/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/nearest_neighbor_along_filaments_results.json')

    # Parse full catalog
    full_catalog = parse_hgbs_orionb_catalog(catalog_file)
    if full_catalog is None:
        print("ERROR: Could not parse catalog")
        return

    # Load NN included cores (will return None due to missing data)
    included_core_ids = load_nn_included_cores(nn_results_file)

    # Perform analysis (will show honest assessment of limitations)
    perform_selection_bias_analysis(full_catalog, included_core_ids)

    # Generate summary for paper
    print(f"\n" + "="*80)
    print("SUMMARY FOR PAPER UPDATE")
    print("="*80)

    print("""
The NN analysis for Orion B uses only 188 of 1,844 cores (10.2%).

HONEST ASSESSMENT OF LIMITATION:
We CANNOT perform a proper selection bias analysis because:
- The NN results file does not contain individual core IDs
- The core-spine association mapping is not available
- The original NN analysis code output is not available

Without knowing WHICH 188 cores were included, we CANNOT determine:
- Whether included cores have different mass distributions
- Whether included cores have different temperature distributions
- Whether included cores have different evolutionary states
- Whether the 10.2% sample is representative of the full population

CRITICAL IMPLICATION:
The λ/W = 2.29 measurement should be regarded as PRELIMINARY because:
1. Only 10.2% of cores are included
2. Selection criteria are unknown
3. Selection bias is unquantified
4. We cannot assume representativeness

REQUIRED FOR ROBUST ANALYSIS:
1. Re-run original NN analysis with core ID output
2. Compare all core properties between included/excluded
3. Quantify selection bias magnitude
4. Apply minimum 3 cores per spine criterion
""")


if __name__ == '__main__':
    main()
