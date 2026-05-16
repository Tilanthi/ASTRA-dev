#!/usr/bin/env python3
"""
Debug script to understand HGBS skeleton and core data structure.
"""

import numpy as np
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import astropy.units as u

print("Loading HGBS Taurus skeleton...")
skeleton_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_taurusL1495_skeleton_map.fits'

with fits.open(skeleton_file) as hdul:
    data = hdul[0].data
    header = hdul[0].header

print(f"Skeleton data shape: {data.shape}")
print(f"Skeleton data range: {data.min()} to {data.max()}")
print(f"Number of non-zero pixels: {(data > 0).sum()}")

# Get WCS
wcs = WCS(header)
print(f"\nWCS info:")
print(f"  CTYPE1: {header.get('CTYPE1')}")
print(f"  CTYPE2: {header.get('CTYPE2')}")
print(f"  CRVAL1: {header.get('CRVAL1')}")
print(f"  CRVAL2: {header.get('CRVAL2')}")
print(f"  CRPIX1: {header.get('CRPIX1')}")
print(f"  CRPIX2: {header.get('CRPIX2')}")
print(f"  CDELT1: {header.get('CDELT1')}")
print(f"  CDELT2: {header.get('CDELT2')}")

# Get skeleton pixels
skeleton_y, skeleton_x = np.where(data > 0)
print(f"\nSkeleton pixels range:")
print(f"  x: {skeleton_x.min()} to {skeleton_x.max()}")
print(f"  y: {skeleton_y.min()} to {skeleton_y.max()}")

# Convert a few skeleton pixels to world coords
print(f"\nFirst 5 skeleton pixel (x,y) -> (RA, Dec):")
for i in range(min(5, len(skeleton_x))):
    world_coord = wcs.pixel_to_world(skeleton_x[i], skeleton_y[i])
    print(f"  ({skeleton_x[i]:4d}, {skeleton_y[i]:4d}) -> "
          f"({world_coord.ra.deg:.6f}, {world_coord.dec.deg:.6f})")

# Load cores
print(f"\nLoading HGBS Taurus core catalog...")
catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_taurusL1495_derived_core_catalog.txt'

cores = []
with open(catalog_file, 'r') as f:
    for line in f:
        if line.startswith('!') or not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 4:
            try:
                # Parse RA/Dec from columns
                ra_str = parts[2]
                dec_str = parts[3]

                # Parse the coordinates (format: HH MM SS.ss +DD MM SS)
                hms = ra_str.split()
                if len(hms) >= 3:
                    ra = f"{hms[0]}h{hms[1]}m{hms[2]}s"

                dms = dec_str.split()
                if len(dms) >= 3:
                    dec = f"{dms[0]}d{dms[1]}m{dms[2]}s"

                coord = SkyCoord(ra, dec, unit=(u.hourangle, u.deg))
                cores.append({
                    'ra': coord.ra.deg,
                    'dec': coord.dec.deg,
                    'id': parts[1],
                })

                if len(cores) >= 10:
                    break
            except Exception as e:
                continue

print(f"\nFirst 10 cores:")
print(f"  {'ID':<20} {'RA (deg)':<12} {'Dec (deg)':<12}")
print(f"  {'-'*20} {'-'*12} {'-'*12}")
for core in cores:
    print(f"  {core['id']:<20} {core['ra']:12.6f} {core['dec']:12.6f}")

# Convert core RA/Dec to pixel coordinates
print(f"\nConverting cores to pixel coordinates...")
for core in cores[:5]:
    world_coord = SkyCoord(core['ra']*u.deg, core['dec']*u.deg)
    pixel_coord = wcs.world_to_pixel(world_coord)
    print(f"  {core['id']}: ({core['ra']:.6f}, {core['dec']:.6f}) -> "
          f"pixel ({pixel_coord[0]:.2f}, {pixel_coord[1]:.2f})")

    # Find distance to nearest skeleton pixel
    dists = np.sqrt((skeleton_x - pixel_coord[0])**2 + (skeleton_y - pixel_coord[1])**2)
    min_dist = dists.min()
    print(f"    Distance to nearest skeleton pixel: {min_dist:.2f} pixels")

print(f"\nSuggestion: The distance threshold might need to be increased.")
print(f"Current threshold: 10 pixels")
print(f"Typical distances: Check the output above")
