#!/usr/bin/env python3
import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy import ndimage
from astropy.wcs import WCS
from collections import defaultdict

# Load skeleton
print("Loading skeleton...")
hdul = fits.open('HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits')
skeleton = hdul[0].data.astype(np.float64)
wcs = WCS(hdul[0].header)
hdul.close()

print(f"Skeleton shape: {skeleton.shape}")

# Load catalog
print("Loading catalog...")
cores = []
with open('HGBS_ORIB/HGBS_orionB_observed_core_catalog.txt', 'r', encoding='latin-1', errors='ignore') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    parts = line.split()
    if len(parts) >= 8 and parts[0].isdigit():
        try:
            ra_str = f"{parts[2]}:{parts[3]}:{parts[4]}"
            dec_str = f"{parts[5]}:{parts[6]}:{parts[7]}"
            coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
            cores.append({'id': int(parts[0]), 'ra': coord.ra.deg, 'dec': coord.dec.deg})
            if len(cores) >= 1844:  # Known Orion B core count
                break
        except:
            pass

print(f"Loaded {len(cores)} cores")

# Extract filaments
print("Extracting filaments...")
threshold = np.percentile(skeleton[skeleton > 0], 50)
mask = skeleton > threshold
labeled, n_features = ndimage.label(mask)
print(f"Found {n_features} features at threshold {threshold:.3f}")

filaments = []
for i in range(1, n_features + 1):
    yp, xp = np.where(labeled == i)
    if len(yp) >= 100:
        vals = skeleton[yp, xp]
        order = np.argsort(-vals)
        filaments.append({'id': i, 'y': yp[order], 'x': xp[order]})

print(f"Extracted {len(filaments)} filaments (>= 100 pixels)")

# Associate cores (using 2W = 0.2 pc threshold)
from astropy.wcs import utils
print("Associating cores...")
core_assoc = {}
for i, core in enumerate(cores):
    try:
        px, py = utils.skycoord_to_pixel(wcs, SkyCoord(core['ra'], core['dec'], unit='deg'))
        min_dist = float('inf')
        closest = None
        for fil in filaments:
            d = np.sqrt(np.min((fil['x'] - px)**2 + (fil['y'] - py)**2))
            if d < min_dist:
                min_dist = d
                closest = fil['id']
        if min_dist < 30:  # ~2W in pixels
            core_assoc[i] = closest
    except:
        pass

print(f"Associated {len(core_assoc)}/{len(cores)} cores")

# Order cores along filaments
print("Ordering cores along filaments...")
fil_cores = defaultdict(list)
for ci, fi in core_assoc.items():
    fil_cores[fi].append(ci)

ordered = {}
for fi, cis in fil_cores.items():
    if len(cis) < 2:
        continue
    fil = next(f for f in filaments if f['id'] == fi)
    positions = []
    for ci in cis:
        try:
            px, py = utils.skycoord_to_pixel(wcs, SkyCoord(cores[ci]['ra'], cores[ci]['dec'], unit='deg'))
            closest_idx = np.argmin((fil['x'] - px)**2 + (fil['y'] - py)**2)
            positions.append((closest_idx / fil['x'].shape[0], ci))
        except:
            pass
    positions.sort()
    ordered[fi] = [p[1] for p in positions]

print(f"Ordered {len(ordered)} filaments with 2+ cores")

# Compute NN spacings
print("Computing NN spacings...")
spacings = []
for fi, cis in ordered.items():
    coords = SkyCoord(ra=[cores[i]['ra'] for i in cis]*u.deg, dec=[cores[i]['dec'] for i in cis]*u.deg)
    for j in range(len(coords)-1):
        sep = coords[j].separation(coords[j+1]).radian * 386  # Orion B distance
        spacings.append(sep)

spacings = np.array(spacings)
print(f"Computed {len(spacings)} spacings")

if len(spacings) > 0:
    print(f"\n{'='*60}")
    print("ORION B FILAMENT-PROJECTED NN RESULTS")
    print(f"{'='*60}")
    print(f"N cores total: {len(cores)}")
    print(f"N cores associated: {len(core_assoc)}")
    print(f"N filaments with 2+ cores: {len(ordered)}")
    print(f"N NN spacings: {len(spacings)}")
    print(f"NN median: {np.median(spacings):.4f} pc")
    print(f"NN mean: {np.mean(spacings):.4f} pc")
    print(f"NN std: {np.std(spacings):.4f} pc")
    print(f"λ/W (W=0.1 pc): {np.median(spacings)/0.1:.2f}")
    print(f"{'='*60}")
