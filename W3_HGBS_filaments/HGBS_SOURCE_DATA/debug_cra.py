#!/usr/bin/env python3
"""
Debug script to understand CRA catalog format
"""

from astropy.coordinates import SkyCoord
from astropy import units as u

# Sample CRA line
line = "       1  185752.5-371441   18 57 52.59   -37 14 41.2     0.011  0.011"

parts = line.split()
print(f"Parts: {parts}")
print(f"Number of parts: {len(parts)}")

# CRA format parsing
core_id = int(parts[0])
ra_h = parts[2]
ra_m = parts[3]
ra_s = parts[4]
dec_d = parts[5]  # Includes sign
dec_m = parts[6]
dec_s = parts[7]

ra_str = f"{ra_h}:{ra_m}:{ra_s}"
dec_str = f"{dec_d}:{dec_m}:{dec_s}"

print(f"RA string: {ra_str}")
print(f"Dec string: {dec_str}")

coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
print(f"Coord: RA={coord.ra.deg:.6f} deg, Dec={coord.dec.deg:.6f} deg")

# Now let's parse the full catalog
print("\n" + "="*60)
print("Parsing full CRA catalog:")
print("="*60)

cores = []
with open('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA/HGBS_CRA/HGBS_craNS_derived_core_catalog.txt', 'r') as f:
    lines = f.readlines()

# Find data start
data_start = None
for i, line in enumerate(lines):
    if not line.strip() or line.startswith('|') or line.startswith('!') or \
       line.startswith('-') or 'TABLE' in line or 'Description' in line or 'runNO' in line:
        continue
    parts = line.split()
    if parts and parts[0].isdigit() and len(parts) >= 8:
        data_start = i
        print(f"Found data start at line {data_start}")
        break

if data_start:
    for i, line in enumerate(lines[data_start:data_start+10]):
        parts = line.split()
        if len(parts) >= 8:
            try:
                ra_h = parts[2]
                ra_m = parts[3]
                ra_s = parts[4]
                dec_d = parts[5]
                dec_m = parts[6]
                dec_s = parts[7]

                ra_str = f"{ra_h}:{ra_m}:{ra_s}"
                dec_str = f"{dec_d}:{dec_m}:{dec_s}"

                coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
                print(f"Core {parts[0]}: RA={coord.ra.deg:.4f}, Dec={coord.dec.deg:.4f}")
            except Exception as e:
                print(f"Error parsing line {i}: {e}")
                print(f"  Line: {line.strip()}")
                print(f"  Parts: {parts[:8]}")
