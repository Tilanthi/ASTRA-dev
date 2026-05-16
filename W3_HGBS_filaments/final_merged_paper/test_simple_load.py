#!/usr/bin/env python3
"""
Simplified test to just load cores from HGBS catalog
"""

catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_taurusL1495_derived_core_catalog.txt'

print("Loading HGBS Taurus catalog...")
print()

cores = []
with open(catalog_file, 'r') as f:
    line_count = 0
    for line in f:
        line_count += 1
        if line.startswith('!'):
            continue
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) < 5:
            print(f"Line {line_count}: Skipping (only {len(parts)} parts)")
            continue

        source_name = parts[1]
        print(f"Line {line_count}: source_name = '{source_name}'")

        if '+' in source_name:
            ra_part, dec_part = source_name.split('+')
            print(f"  RA part: '{ra_part}', Dec part: '{dec_part}'")

            try:
                # RA: HHMMSS.s
                ra_h = float(ra_part[:2])
                ra_m = float(ra_part[2:4])
                ra_s = float(ra_part[4:])
                ra_deg = 15 * (ra_h + ra_m/60 + ra_s/3600)

                # Dec: DDMMSS
                dec_d = float(dec_part[:2])
                dec_m = float(dec_part[2:4])
                dec_s = float(dec_part[4:] if len(dec_part) > 4 else 0)
                dec_deg = dec_d + dec_m/60 + dec_s/3600

                print(f"  RA={ra_deg:.6f}°, Dec={dec_deg:.6f}°")
                cores.append({'ra': ra_deg, 'dec': dec_deg, 'id': source_name})
            except Exception as e:
                print(f"  ERROR: {e}")

        if len(cores) >= 5:
            break

print()
print(f"Successfully loaded {len(cores)} cores")
