#!/usr/bin/env python3
"""
HGBS Aquila - Catalog Analysis and Visualization

This script analyzes the core catalog in detail and creates
statistical summaries for discovery science planning.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os

rcParams['figure.dpi'] = 120
rcParams['font.size'] = 9
rcParams['figure.facecolor'] = 'white'

# Import the catalog parser
from parse_catalog import parse_hgbs_catalog

def analyze_catalog_statistics(cores):
    """Perform detailed statistical analysis of the core catalog."""

    # Separate by type
    starless = [c for c in cores if c.get('type') == 'starless']
    prestellar = [c for c in cores if c.get('type') == 'prestellar']
    protostellar = [c for c in cores if c.get('type') == 'protostellar']

    print("\n" + "="*70)
    print("DETAILED CORE CATALOG ANALYSIS")
    print("="*70)

    print(f"\nTotal cores: {len(cores)}")
    print(f"  Starless: {len(starless)} ({100*len(starless)/len(cores):.1f}%)")
    print(f"  Prestellar: {len(prestellar)} ({100*len(prestellar)/len(cores):.1f}%)")
    print(f"  Protostellar: {len(protostellar)} ({100*len(protostellar)/len(cores):.1f}%)")

    # Analysis by type
    for ctype, clist in [('Starless', starless), ('Prestellar', prestellar), ('Protostellar', protostellar)]:
        print(f"\n{ctype.upper()} CORES (N={len(clist)})")
        print("-" * 50)

        # Mass statistics
        masses = [c['mass'] for c in clist if 'mass' in c and not np.isnan(c['mass'])]
        if masses:
            masses = np.array(masses)
            print(f"Mass [Msun]:")
            print(f"  Range: {np.min(masses):.3f} - {np.max(masses):.3f}")
            print(f"  Median: {np.median(masses):.3f}")
            print(f"  Mean: {np.mean(masses):.3f}")
            print(f"  Std: {np.std(masses):.3f}")
            for p in [10, 25, 50, 75, 90, 95]:
                print(f"  {p}%ile: {np.percentile(masses, p):.3f}")

        # Temperature statistics
        temps = [c['temp'] for c in clist if 'temp' in c and not np.isnan(c['temp'])]
        if temps:
            temps = np.array(temps)
            print(f"Temperature [K]:")
            print(f"  Range: {np.min(temps):.2f} - {np.max(temps):.2f}")
            print(f"  Median: {np.median(temps):.2f}")
            print(f"  Mean: {np.mean(temps):.2f}")
            print(f"  Std: {np.std(temps):.2f}")

        # Size statistics
        sizes = [c['r_core_deconv'] for c in clist if 'r_core_deconv' in c and not np.isnan(c['r_core_deconv'])]
        if sizes:
            sizes = np.array(sizes)
            print(f"Radius (deconvolved) [pc]:")
            print(f"  Range: {np.min(sizes):.4f} - {np.max(sizes):.4f}")
            print(f"  Median: {np.median(sizes):.4f}")

        # Bonnor-Ebert statistics
        alpha = [c['alpha_be'] for c in clist if 'alpha_be' in c and not np.isnan(c['alpha_be'])]
        if alpha:
            alpha = np.array(alpha)
            print(f"Bonnor-Ebert ratio:")
            print(f"  Range: {np.min(alpha):.3f} - {np.max(alpha):.3f}")
            print(f"  Median: {np.median(alpha):.3f}")
            n_bound = sum(1 for a in alpha if a < 2.0)
            print(f"  Bound (α<2): {n_bound}/{len(alpha)} ({100*n_bound/len(alpha):.1f}%)")

        # Peak column density
        nh2 = [c['nh2_peak'] for c in clist if 'nh2_peak' in c and not np.isnan(c['nh2_peak'])]
        if nh2:
            nh2 = np.array(nh2)
            print(f"Peak N_H2 [10^21 cm^-2]:")
            print(f"  Range: {np.min(nh2):.2f} - {np.max(nh2):.2f}")
            print(f"  Median: {np.median(nh2):.2f}")

    # Cross-type comparisons
    print("\n" + "="*70)
    print("CROSS-TYPE COMPARISONS")
    print("="*70)

    # Mass comparison
    print("\nMass distribution by type:")
    for ctype, clist in [('Starless', starless), ('Prestellar', prestellar), ('Protostellar', protostellar)]:
        masses = [c['mass'] for c in clist if 'mass' in c and not np.isnan(c['mass'])]
        if masses:
            print(f"  {ctype}: median = {np.median(masses):.3f} Msun, range = {np.min(masses):.3f} - {np.max(masses):.3f} Msun")

    # Temperature comparison
    print("\nTemperature distribution by type:")
    for ctype, clist in [('Starless', starless), ('Prestellar', prestellar), ('Protostellar', protostellar)]:
        temps = [c['temp'] for c in clist if 'temp' in c and not np.isnan(c['temp'])]
        if temps:
            print(f"  {ctype}: median = {np.median(temps):.2f} K, range = {np.min(temps):.2f} - {np.max(temps):.2f} K")

    # Bonnor-Ebert comparison
    print("\nBonnor-Ebert ratio by type:")
    for ctype, clist in [('Starless', starless), ('Prestellar', prestellar), ('Protostellar', protostellar)]:
        alpha = [c['alpha_be'] for c in clist if 'alpha_be' in c and not np.isnan(c['alpha_be'])]
        if alpha:
            alpha = np.array(alpha)
            n_bound = sum(1 for a in alpha if a < 2.0)
            print(f"  {ctype}: median α = {np.median(alpha):.3f}, bound fraction = {100*n_bound/len(alpha):.1f}%")

    # Identify unusual cores
    print("\n" + "="*70)
    print("UNUSUAL CORES (Discovery Targets)")
    print("="*70)

    # Very massive cores
    massive = [c for c in cores if 'mass' in c and c['mass'] > 5.0]
    print(f"\nVery massive cores (M > 5 Msun): {len(massive)}")
    for c in massive[:10]:  # Show first 10
        print(f"  {c['name']}: M = {c['mass']:.2f} Msun, T = {c.get('temp', np.nan):.1f} K, type = {c.get('type', 'unknown')}")

    # Cold protostellar cores (potential young or deeply embedded)
    cold_proto = [c for c in protostellar if 'temp' in c and c['temp'] < 10.0]
    print(f"\nCold protostellar cores (T < 10 K): {len(cold_proto)}")
    for c in cold_proto[:10]:
        print(f"  {c['name']}: T = {c['temp']:.1f} K, M = {c.get('mass', np.nan):.2f} Msun")

    # Warm prestellar cores (potential misclassification or external heating)
    warm_pre = [c for c in prestellar if 'temp' in c and c['temp'] > 15.0]
    print(f"\nWarm prestellar cores (T > 15 K): {len(warm_pre)}")
    for c in warm_pre[:10]:
        print(f"  {c['name']}: T = {c['temp']:.1f} K, M = {c.get('mass', np.nan):.2f} Msun, α_BE = {c.get('alpha_be', np.nan):.2f}")

    # High Bonnor-Ebert ratio prestellar cores (may be unbound)
    unbound_pre = [c for c in prestellar if 'alpha_be' in c and c['alpha_be'] > 3.0]
    print(f"\nHigh α_BE prestellar cores (α > 3, likely unbound): {len(unbound_pre)}")
    for c in unbound_pre[:10]:
        print(f"  {c['name']}: α_BE = {c['alpha_be']:.2f}, M = {c.get('mass', np.nan):.2f} Msun")

    # Bound starless cores (potential prestellar candidates)
    bound_starless = [c for c in starless if 'alpha_be' in c and c['alpha_be'] < 2.0]
    print(f"\nBound starless cores (α_BE < 2, potential prestellar): {len(bound_starless)}")
    for c in bound_starless[:10]:
        print(f"  {c['name']}: α_BE = {c['alpha_be']:.2f}, M = {c.get('mass', np.nan):.2f} Msun, T = {c.get('temp', np.nan):.1f} K")

    return {
        'starless': starless,
        'prestellar': prestellar,
        'protostellar': protostellar,
        'massive': massive,
        'cold_proto': cold_proto,
        'warm_pre': warm_pre,
        'unbound_pre': unbound_pre,
        'bound_starless': bound_starless
    }

def main():
    """Run catalog analysis."""
    cat_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS/HGBS_AQUILA/HGBS_aquilaM2_derived_core_catalog.txt'

    print("Loading core catalog...")
    cores = parse_hgbs_catalog(cat_file)
    print(f"Loaded {len(cores)} cores")

    results = analyze_catalog_statistics(cores)

    # Save unusual cores to file for further investigation
    output_dir = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS'
    unusual_file = os.path.join(output_dir, 'unusual_cores.txt')

    with open(unusual_file, 'w') as f:
        f.write("# UNUSUAL CORES IN AQUILA REGION\n")
        f.write("# Generated by ASTRA Discovery System\n\n")

        f.write(f"# Very massive cores (M > 5 Msun): {len(results['massive'])}\n")
        for c in results['massive']:
            f.write(f"{c['name']}: M={c['mass']:.2f} Msun, T={c.get('temp', np.nan):.1f}K, type={c.get('type', '?')}\n")

        f.write(f"\n# Cold protostellar cores (T < 10 K): {len(results['cold_proto'])}\n")
        for c in results['cold_proto']:
            f.write(f"{c['name']}: T={c['temp']:.1f}K, M={c.get('mass', np.nan):.2f}Msun\n")

        f.write(f"\n# Warm prestellar cores (T > 15 K): {len(results['warm_pre'])}\n")
        for c in results['warm_pre']:
            f.write(f"{c['name']}: T={c['temp']:.1f}K, M={c.get('mass', np.nan):.2f}Msun, α={c.get('alpha_be', np.nan):.2f}\n")

        f.write(f"\n# Bound starless cores (α_BE < 2): {len(results['bound_starless'])}\n")
        for c in results['bound_starless']:
            f.write(f"{c['name']}: α={c['alpha_be']:.2f}, M={c.get('mass', np.nan):.2f}Msun, T={c.get('temp', np.nan):.1f}K\n")

    print(f"\nUnusual cores saved to: {unusual_file}")
    print("\nAnalysis complete!")

if __name__ == '__main__':
    main()
