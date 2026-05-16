#!/usr/bin/env python3
"""Update paths in OPH scripts"""

# Read the file
with open('hgbs_discovery_phase1_fixed.py', 'r') as f:
    content = f.read()

# Replace paths
content = content.replace("HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB'",
                         "HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH'")

content = content.replace("'70_micron': os.path.join(HGBS_DIR, 'HGBS_OrionB_070.fits')",
                         "'70_micron': os.path.join(HGBS_DIR, 'HGBS_oph_L1688_070.fits')")

content = content.replace("'160_micron': os.path.join(HGBS_DIR, 'HGBS_OrionB_160.fits')",
                         "'160_micron': os.path.join(HGBS_DIR, 'HGBS_oph_L1688_160.fits')")

content = content.replace("'250_micron': os.path.join(HGBS_DIR, 'HGBS_OrionB_250.fits')",
                         "'250_micron': os.path.join(HGBS_DIR, 'HGBS_oph_L1688_250.fits')")

content = content.replace("'350_micron': os.path.join(HGBS_DIR, 'HGBS_OrionB_350.fits')",
                         "'350_micron': os.path.join(HGBS_DIR, 'HGBS_oph_L1688_350.fits')")

content = content.replace("'500_micron': os.path.join(HGBS_DIR, 'HGBS_OrionB_500.fits')",
                         "'500_micron': os.path.join(HGBS_DIR, 'HGBS_oph_L1688_500.fits')")

content = content.replace("'column_density': os.path.join(HGBS_DIR, 'HGBS_orionB_column_density_map.fits')",
                         "'column_density': os.path.join(HGBS_DIR, 'HGBS_oph_l1688_column_density_map.fits')")

content = content.replace("'dust_temperature': os.path.join(HGBS_DIR, 'HGBS_orionB_hires_column_density_map.fits'),  # Using hires for temp",
                         "'dust_temperature': os.path.join(HGBS_DIR, 'HGBS_oph-L1688_dust_temperature_map.fits')")

content = content.replace("'column_density_hires': os.path.join(HGBS_DIR, 'HGBS_orionB_hires_column_density_map.fits')",
                         "'column_density_hires': os.path.join(HGBS_DIR, 'HGBS_oph_l1688_hires_column_density_map.fits')")

content = content.replace("'skeleton': os.path.join(HGBS_DIR, 'HGBS_orionB_skeleton_map.fits')",
                         "'skeleton': os.path.join(HGBS_DIR, 'HGBS_oph_l1688_skeleton_map.fits')")

content = content.replace("'derived': os.path.join(HGBS_DIR, 'HGBS_orionb_derived_core_catalog.txt')",
                         "'derived': os.path.join(HGBS_DIR, 'HGBS_ophiuchus_derived_core_catalog.txt')")

content = content.replace("'observed': os.path.join(HGBS_DIR, 'HGBS_orionB_observed_core_catalog.txt')",
                         "'observed': os.path.join(HGBS_DIR, 'HGBS_ophiuchus_observed_core_catalog.txt')")

content = content.replace("import parse_orionb_catalog",
                         "import parse_oph_catalog")

content = content.replace("parse_orionb_catalog.parse_orionb_catalog",
                         "parse_oph_catalog.parse_oph_catalog")

content = content.replace("dist_pc = 260  # Distance to Aquila",
                         "dist_pc = 130  # Distance to Ophiuchus")

content = content.replace("HGBS AQUILA",
                         "HGBS OPHIUCHUS")

content = content.replace("HGBS Aquila Discovery Science",
                         "HGBS Ophiuchus Discovery Science")

content = content.replace("Aquila region data",
                         "Ophiuchus region data")

content = content.replace("beam_size_pc = 260 * 0.023 / 206265",
                         "beam_size_pc = 130 * 0.023 / 206265")

# Write back
with open('hgbs_discovery_phase1_fixed.py', 'w') as f:
    f.write(content)

print("Updated hgbs_discovery_phase1_fixed.py")
