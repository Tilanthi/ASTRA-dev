#!/usr/bin/env python3
"""
Test core coordinate parsing
"""

from astropy.coordinates import SkyCoord
import astropy.units as u

catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_taurusL1495_derived_core_catalog.txt'

print("Testing core coordinate parsing...")
print()

with open(catalog_file, 'r') as f:
    for i, line in enumerate(f):
        if line.startswith('!') or not line.strip():
            continue

        parts = line.split()
        if len(parts) < 4:
            continue

        source_name = parts[1]
        print(f"Line {i+1}: {source_name}")

        # Parse format like "040924.1+284723"
        if len(source_name) >= 15:
            # Extract RA part (before the +)
            ra_part = source_name[:10]  # HHMMSS.s
            # Extract Dec part (after the +)
            dec_part = source_name[10:]   # DDMMSS

            print(f"  RA part: {ra_part}, Dec part: {dec_part}")

            try:
                # Convert to degrees
                # RA: HHMMSS.s -> HH:MM:SS.s
                ra_hours = float(ra_part[:2])
                ra_min = float(ra_part[2:4])
                ra_sec = float(ra_part[4:])
                ra_deg = 15 * (ra_hours + ra_min/60 + ra_sec/3600)

                # Dec: DDMMSS -> DD:MM:SS
                dec_sign = -1 if '-' in source_name else 1
                dec_clean = dec_part.replace('+', '').replace('-', '')
                dec_deg_raw = float(dec_clean[:2])
                dec_min = float(dec_clean[2:4])
                dec_sec = float(dec_clean[4:] if len(dec_clean) > 4 else 0)
                dec_deg = dec_sign * (dec_deg_raw + dec_min/60 + dec_sec/3600)

                print(f"  Parsed: RA={ra_deg:.6f}°, Dec={dec_deg:.6f}°")

                # Verify with SkyCoord
                coord = SkyCoord(ra_deg*u.deg, dec_deg*u.deg)
                print(f"  SkyCoord: RA={coord.ra.deg:.6f}°, Dec={coord.dec.deg:.6f}°")
                print(f"  HMS: {coord.ra.hms}, DMS: {coord.dec.dms}")
                print()

            except Exception as e:
                print(f"  ERROR: {e}")
                print()

        if i >= 9:  # Test first 10 cores
            break
