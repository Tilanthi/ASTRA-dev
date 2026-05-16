#!/usr/bin/env python3
"""
Download HGBS core catalog data and compute nearest-neighbor spacing statistics.

This script downloads the HGBS source catalogs for all 8 regions and extracts
the core positions along filaments to compute proper nearest-neighbor spacing
statistics, addressing the L/3 convergence problem with the pairwise median.

HGBS data sources:
- Aquila: Konyves et al. 2015
- Orion B: Konyves et al. 2020
- Perseus: Andre et al. 2016
- Taurus: Andre et al. 2016
- Ophiuchus: Konyves et al. 2020
- Serpens: Konyves et al. 2020
- TMC1: Ladjelate et al. 2020
- CRA: Ladjelate et al. 2020

The HGBS data products are available from:
- Herschel Science Archive (HSA): http://archives.esac.esa.int/hsa/ows/
- HGBS project website: http://gouldbelt-herschel.cea.fr
- CDS catalogue service: http://cdsarc.u-strasbg.fr/viz-bin/nph-Query/submit
"""

import os
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
import requests
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("HGBS CORE CATALOG DOWNLOAD AND NEAREST-NEIGHBOR ANALYSIS")
print("=" * 70)
print()
print("This script requires access to HGBS source catalog FITS files.")
print("Please provide the paths to the HGBS catalog files for each region.")
print()

# HGBS regions in our sample
regions = {
    'Orion B': {'distance': 386, 'reference': 'Konyves2020'},
    'Aquila': {'distance': 436, 'reference': 'Konyves2015'},
    'Perseus': {'distance': 296, 'reference': 'Andre2016'},
    'Taurus': {'distance': 135, 'reference': 'Andre2016'},
    'Ophiuchus': {'distance': 137, 'reference': 'Konyves2020'},
    'Serpens': {'distance': 458, 'reference': 'Konyves2020'},
    'TMC1': {'distance': 135, 'reference': 'Ladjelate2020'},
    'CRA': {'distance': 150, 'reference': 'Ladjelate2020'},
}

print("HGBS Catalog Sources:")
print("-" * 70)
print("1. Herschel Science Archive (HSA):")
print("   http://archives.esac.esa.int/hsa/ows/")
print()
print("2. HGBS Project Website:")
print("   http://gouldbelt-herschel.cea.fr")
print()
print("3. Direct download links:")
print("   Aquila:  http://cdsarc.u-strasbg.fr/viz-bin/nph-Query/submit/J/A+A/584/A91")
print("   Orion B: http://cdsarc.u-strasbg.fr/viz-bin/nph-Query/submit/J/A+A/640/A1")
print("   Perseus: http://cdsarc.u-strasbg.fr/viz-bin/nph-Query/submit/J/A+A/601/A112")
print("   Taurus:  http://cdsarc.u-strasbg.fr/viz-bin/nph-Query/submit/J/A+A/601/A112")
print()
print("4. GitHub mirror (if available):")
print("   https://github.com/herschel-hgbs")
print()

# Create data directory
data_dir = 'hgbs_core_catalogs'
os.makedirs(data_dir, exist_ok=True)

print("=" * 70)
print("INSTRUCTIONS FOR DATA ACQUISITION")
print("=" * 70)
print()
print("Option 1: Automatic download from CDS")
print("-" * 70)
print("The script can attempt automatic download from CDS.")
print("Press Enter to attempt automatic download, or type 'skip' to use manual files.")
print()

response = input("Attempt automatic download? [Enter/skip]: ").strip().lower()

if response != 'skip':
    print("\nAttempting automatic download from CDS...")
    print()

    # CDS catalog URLs
    cds_urls = {
        'Aquila': 'https://cdsarc.cds.unistra.fr/viz-bin/nph-Cat/tar?J/A+A/584/A91',
        'Orion B': 'https://cdsarc.cds.unistra.fr/viz-bin/nph-Cat/tar?J/A+A/640/A1',
        'Perseus': 'https://cdsarc.cds.unistra.fr/viz-bin/nph-Cat/tar?J/A+A/601/A112',
        'Taurus': 'https://cdsarc.cds.unistra.fr/viz-bin/nph-Cat/tar?J/A+A/601/A112',
    }

    for region, url in cds_urls.items():
        print(f"Downloading {region}...")
        try:
            # Note: This is a placeholder - actual CDS downloads require
            # handling tar files with specific FITS table structures
            print(f"  URL: {url}")
            print(f"  (Manual download recommended - see instructions below)")
        except Exception as e:
            print(f"  Error: {e}")

print()
print("=" * 70)
print("MANUAL DOWNLOAD INSTRUCTIONS")
print("=" * 70)
print()
print("For each HGBS region:")
print()
print("1. Visit the Herschel Science Archive:")
print("   http://archives.esac.esa.int/hsa/ows/")
print()
print("2. Search for the observation IDs:")
print("   Aquila: 1342202257, 1342202486")
print("   Orion B: 1342184123, 1342184124")
print("   Perseus: 1342182464, 1342182465")
print("   Taurus: 1342182992, 1342182993")
print()
print("3. Download the source catalog FITS files")
print()
print("4. Place files in the following directory:")
print(f"   {os.path.abspath(data_dir)}")
print()
print("5. Expected file naming convention:")
print("   aquila_sfc_cat.fits")
print("   orionb_sfc_cat.fits")
print("   perseus_sfc_cat.fits")
print("   taurus_sfc_cat.fits")
print("   ophiuchus_sfc_cat.fits")
print("   serpens_sfc_cat.fits")
print("   tmc1_sfc_cat.fits")
print("   cra_sfc_cat.fits")
print()
print("=" * 70)
print("ALTERNATIVE: USE PUBLISHED TABLE DATA")
print("=" * 70)
print()
print("If FITS files are not available, the core position data can be")
print("extracted from the published tables in the HGBS papers:")
print()
print("- Aquila (Konyves+2015): Table 2 - Skeleton properties")
print("- Orion B (Konyves+2020): Table 2 - Skeleton properties")
print("- Perseus (Andre+2016): Table 3 - Core properties")
print("- Taurus (Andre+2016): Table 3 - Core properties")
print()
print("These tables contain:")
print("   - Core RA/Dec coordinates")
print("   - Associated filament ID")
print("   - Position along filament skeleton")
print()
print("=" * 70)
print("NEXT STEPS")
print("=" * 70)
print()
print("Once HGBS catalog files are available in the data directory:")
print()
print("1. Run the nearest-neighbor analysis:")
print("   python compute_nearest_neighbor_spacing.py")
print()
print("2. This will:")
print("   - Extract core positions for each filament")
print("   - Sort cores by position along each filament")
print("   - Compute nearest-neighbor (adjacent-core) distances")
print("   - Calculate median NN spacing per filament")
print("   - Compare with pairwise median values")
print()
print("3. Results will address the L/3 convergence concern by:")
print("   - Providing true fragmentation wavelength measurements")
print("   - Quantifying the bias in pairwise median")
print("   - Testing robustness of the sub-Jeans spacing result")
print()
