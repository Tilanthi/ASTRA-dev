#!/usr/bin/env python3
"""Update paths for TAURUS analysis scripts"""

import os

scripts = [
    'hgbs_discovery_phase1_fixed.py',
    'hgbs_discovery_phase2.py',
    'hgbs_discovery_phase3.py',
    'hgbs_discovery_phase4.py',
    'hgbs_discovery_phase5.py'
]

region = 'TAURUS'
hgb_dir = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS'

# File name mappings
files = {
    'column_density': 'HGBS_tauN3_hires_column_density_map.fits',
    'skeleton': 'HGBS_taurusL1495_skeleton_map.fits',
    'dust_temperature': 'HGBS_taurus_L1495_dust_temperature_map.fits',
    'derived_catalog': 'HGBS_taurusL1495_derived_core_catalog.txt',
    'observed_catalog': 'HGBS_taurusL1495_observed_core_catalog.txt'
}

for script in scripts:
    if not os.path.exists(script):
        print(f"Skipping {script} - not found")
        continue

    with open(script, 'r') as f:
        content = f.read()

    # Update HGBS_DIR
    content = content.replace("HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB'",
                             f"HGBS_DIR = '{hgb_dir}'")
    content = content.replace("HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA'",
                             f"HGBS_DIR = '{hgb_dir}'")
    content = content.replace("HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH'",
                             f"HGBS_DIR = '{hgb_dir}'")

    # Update distance
    content = content.replace("DISTANCE_PC = 260.0", "DISTANCE_PC = 140.0")
    content = content.replace("dist_pc = 260", "dist_pc = 140")

    # Update file names
    content = content.replace("HGBS_orionB_column_density_map.fits", files['column_density'])
    content = content.replace("HGBS_aquilaM2_column_density_map.fits", files['column_density'])
    content = content.replace("HGBS_oph_l1688_column_density_map.fits", files['column_density'])

    content = content.replace("HGBS_orionB_skeleton_map.fits", files['skeleton'])
    content = content.replace("HGBS_aquilaM2_skeleton_map.fits", files['skeleton'])
    content = content.replace("HGBS_oph_l1688_skeleton_map.fits", files['skeleton'])

    content = content.replace("HGBS_orionB_hires_column_density_map.fits", files['column_density'])
    content = content.replace("HGBS_aquilaM2_dust_temperature_map.fits", files['dust_temperature'])
    content = content.replace("HGBS_oph-L1688_dust_temperature_map.fits", files['dust_temperature'])

    content = content.replace("HGBS_orionb_derived_core_catalog.txt", files['derived_catalog'])
    content = content.replace("HGBS_aquilaM2_derived_core_catalog.txt", files['derived_catalog'])
    content = content.replace("HGBS_ophiuchus_derived_core_catalog.txt", files['derived_catalog'])

    content = content.replace("HGBS_orionB_observed_core_catalog.txt", files['observed_catalog'])
    content = content.replace("HGBS_aquilaM2_observed_core_catalog.txt", files['observed_catalog'])
    content = content.replace("HGBS_ophiuchus_observed_core_catalog.txt", files['observed_catalog'])

    # Update region names in output
    content = content.replace("Aquila", "Taurus")
    content = content.replace("OrionB", "Taurus")
    content = content.replace("Orion B", "Taurus")
    content = content.replace("Ophiuchus", "Taurus")

    # Update parser imports
    content = content.replace("import parse_orionb_catalog", "import parse_taurus_catalog")
    content = content.replace("import parse_oph_catalog", "import parse_taurus_catalog")
    content = content.replace("parse_orionb_catalog.parse_orionb_catalog", "parse_taurus_catalog.parse_taurus_catalog")
    content = content.replace("parse_oph_catalog.parse_oph_catalog", "parse_taurus_catalog.parse_taurus_catalog")

    with open(script, 'w') as f:
        f.write(content)

    print(f"Updated {script}")

print(f"\nAll scripts updated for {region}")
