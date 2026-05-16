#!/usr/bin/env python3
"""Update paths in all OPH phase scripts"""

import os

scripts = [
    'hgbs_discovery_phase2.py',
    'hgbs_discovery_phase3.py',
    'hgbs_discovery_phase4.py',
    'hgbs_discovery_phase5.py'
]

# OPH file names
opn_dir = "/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH"
col_map = "HGBS_oph_l1688_column_density_map.fits"
skel_map = "HGBS_oph_l1688_skeleton_map.fits"
temp_map = "HGBS_oph-L1688_dust_temperature_map.fits"
derived_cat = "HGBS_ophiuchus_derived_core_catalog.txt"

for script in scripts:
    if not os.path.exists(script):
        print(f"Skipping {script} - not found")
        continue

    with open(script, 'r') as f:
        content = f.read()

    # Update directory
    content = content.replace("HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB'",
                             f"HGBS_DIR = '{opn_dir}'")

    content = content.replace("HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA'",
                             f"HGBS_DIR = '{opn_dir}'")

    # Update distance (OrionB 260 -> OPH 130)
    content = content.replace("DISTANCE_PC = 260.0  # Distance to Aquila",
                             "DISTANCE_PC = 130.0  # Distance to Ophiuchus")
    content = content.replace("DISTANCE_PC = 260.0",
                             "DISTANCE_PC = 130.0")

    # Update file names
    content = content.replace("HGBS_aquilaM2_column_density_map.fits", col_map)
    content = content.replace("HGBS_aquilaM2_skeleton_map.fits", skel_map)
    content = content.replace("HGBS_aquilaM2_dust_temperature_map.fits", temp_map)
    content = content.replace("HGBS_orionB_column_density_map.fits", col_map)
    content = content.replace("HGBS_orionB_skeleton_map.fits", skel_map)

    # Update catalog names
    content = content.replace("HGBS_aquilaM2_derived_core_catalog.txt", derived_cat)
    content = content.replace("HGBS_orionb_derived_core_catalog.txt", derived_cat)
    content = content.replace("HGBS_orionB_derived_core_catalog.txt", derived_cat)

    # Update region names in output
    content = content.replace("Aquila", "Ophiuchus")
    content = content.replace("OrionB", "Ophiuchus")
    content = content.replace("Orion B", "Ophiuchus")

    with open(script, 'w') as f:
        f.write(content)

    print(f"Updated {script}")

print("\nAll scripts updated. Ready to run phases 2-5.")
