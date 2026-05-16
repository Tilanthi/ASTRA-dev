#!/usr/bin/env python3
"""
Parse HGBS derived core catalog more robustly
"""
import re
import numpy as np

def parse_hgbs_catalog(filename):
    """
    Parse the HGBS derived core catalog.

    Returns a list of dictionaries with core properties.
    """
    cores = []

    with open(filename, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    # Find where data starts (after header separator)
    data_start = None
    for i, line in enumerate(lines):
        if '---' in line and i > 30:
            data_start = i + 1
            break

    if data_start is None:
        print("Could not find data start")
        return cores

    # Parse data lines
    for line in lines[data_start:]:
        line = line.strip()
        if not line or line.startswith('|'):
            continue

        # Split by whitespace
        parts = line.split()

        # Need at least core number, name, coordinates, and some physical properties
        if len(parts) < 15:
            continue

        try:
            core = {}

            # Core number (first field)
            core['id'] = int(parts[0])

            # Core name (second field - something like 182154.6-025557)
            core['name'] = parts[1] if len(parts) > 1 else ''

            # RA and Dec (sexagesimal format like 18:21:54.63 and -02:55:57.2)
            if len(parts) > 3:
                core['ra'] = parts[2]
                core['dec'] = parts[3]

            # Position in parts continues from here:
            # R_core (deconvolved, observed) - two values
            # M_core, M_err - two values
            # T_dust, T_err - two values
            # Nh2_peak - one value
            # Nh2_ave (observed, deconvolved) - two values
            # nh2_peak - one value
            # nh2_ave (observed, deconvolved) - two values
            # alpha_BE - one value
            # Core type - text
            # Comments - text

            # Parse numerical values starting from position 4
            idx = 4

            # R_core deconvolved (pc)
            if idx < len(parts):
                try:
                    core['r_core_deconv'] = float(parts[idx])
                except:
                    core['r_core_deconv'] = np.nan
                idx += 1

            # R_core observed (pc)
            if idx < len(parts):
                try:
                    core['r_core_obs'] = float(parts[idx])
                except:
                    core['r_core_obs'] = np.nan
                idx += 1

            # M_core (Msun)
            if idx < len(parts):
                try:
                    core['mass'] = float(parts[idx])
                except:
                    core['mass'] = np.nan
                idx += 1

            # M_err
            if idx < len(parts):
                try:
                    core['mass_err'] = float(parts[idx])
                except:
                    core['mass_err'] = np.nan
                idx += 1

            # T_dust (K)
            if idx < len(parts):
                try:
                    core['temp'] = float(parts[idx])
                except:
                    core['temp'] = np.nan
                idx += 1

            # T_err
            if idx < len(parts):
                try:
                    core['temp_err'] = float(parts[idx])
                except:
                    core['temp_err'] = np.nan
                idx += 1

            # Nh2_peak (10^21 cm^-2)
            if idx < len(parts):
                try:
                    core['nh2_peak'] = float(parts[idx])
                except:
                    core['nh2_peak'] = np.nan
                idx += 1

            # Nh2_ave observed
            if idx < len(parts):
                try:
                    core['nh2_ave_obs'] = float(parts[idx])
                except:
                    core['nh2_ave_obs'] = np.nan
                idx += 1

            # Nh2_ave deconvolved
            if idx < len(parts):
                try:
                    core['nh2_ave_deconv'] = float(parts[idx])
                except:
                    core['nh2_ave_deconv'] = np.nan
                idx += 1

            # nh2_peak (10^4 cm^-3)
            if idx < len(parts):
                try:
                    core['n_peak'] = float(parts[idx])
                except:
                    core['n_peak'] = np.nan
                idx += 1

            # nh2_ave observed
            if idx < len(parts):
                try:
                    core['n_ave_obs'] = float(parts[idx])
                except:
                    core['n_ave_obs'] = np.nan
                idx += 1

            # nh2_ave deconvolved
            if idx < len(parts):
                try:
                    core['n_ave_deconv'] = float(parts[idx])
                except:
                    core['n_ave_deconv'] = np.nan
                idx += 1

            # alpha_BE
            if idx < len(parts):
                try:
                    core['alpha_be'] = float(parts[idx])
                except:
                    core['alpha_be'] = np.nan
                idx += 1

            # Core type and comments (remaining text)
            if idx < len(parts):
                remaining = ' '.join(parts[idx:])
                core['type'] = 'unknown'
                core['comments'] = ''

                if 'starless' in remaining.lower():
                    core['type'] = 'starless'
                elif 'prestellar' in remaining.lower():
                    core['type'] = 'prestellar'
                elif 'protostellar' in remaining.lower():
                    core['type'] = 'protostellar'

                if 'tentative bound' in remaining.lower():
                    core['comments'] = 'tentative bound'
                elif 'no sed fit' in remaining.lower():
                    core['comments'] = 'no sed fit'

            cores.append(core)

        except Exception as e:
            # Skip lines that don't parse correctly
            continue

    return cores

def summarize_cores(cores):
    """Print summary statistics of parsed cores."""
    print(f"\nTotal cores parsed: {len(cores)}")

    # Count by type
    types = {}
    masses = []
    temps = []
    sizes = []
    alpha_be = []

    for core in cores:
        ctype = core.get('type', 'unknown')
        types[ctype] = types.get(ctype, 0) + 1

        if 'mass' in core and not np.isnan(core['mass']):
            masses.append(core['mass'])
        if 'temp' in core and not np.isnan(core['temp']):
            temps.append(core['temp'])
        if 'r_core_deconv' in core and not np.isnan(core['r_core_deconv']):
            sizes.append(core['r_core_deconv'])
        if 'alpha_be' in core and not np.isnan(core['alpha_be']):
            alpha_be.append(core['alpha_be'])

    print("\nCore type distribution:")
    for ctype, count in types.items():
        print(f"  {ctype}: {count}")

    if masses:
        masses = np.array(masses)
        print(f"\nMass statistics (Msun):")
        print(f"  Range: {np.min(masses):.3f} - {np.max(masses):.3f}")
        print(f"  Median: {np.median(masses):.3f}")

    if temps:
        temps = np.array(temps)
        print(f"\nTemperature statistics (K):")
        print(f"  Range: {np.min(temps):.2f} - {np.max(temps):.2f}")
        print(f"  Median: {np.median(temps):.2f}")

    return cores

if __name__ == '__main__':
    import os
    cat_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS/HGBS_AQUILA/HGBS_aquilaM2_derived_core_catalog.txt'
    cores = parse_hgbs_catalog(cat_file)
    summarize_cores(cores)
