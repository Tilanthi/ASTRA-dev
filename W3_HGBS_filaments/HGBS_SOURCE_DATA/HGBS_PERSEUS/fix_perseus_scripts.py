#!/usr/bin/env python3
"""
Fix Perseus phase scripts with correct paths and imports.
"""

import os

HGBS_PERSEUS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS/HGBS_PERSEUS'

# Perseus-specific data
perseus_data = {
    'HGBS_DIR': HGBS_PERSEUS_DIR,
    'COL_DEN_FILE': 'HGBS_perseus_hires_column_density_map.fits',
    'TEMP_FILE': 'HGBS_perseus_dust_temperature_map.fits',
    'SKELETON_FILE': 'HGBS_perseus_skeleton_map.fits',
    'CAT_FILE': 'HGBS_perseus_derived_core_catalog.txt',
    'CAT_PARSER': 'parse_perseus_catalog',
    'CAT_PARSER_FUNC': 'parse_perseus_catalog',
    'DISTANCE': '260.0',  # Perseus distance ~260 pc
    'REGION_NAME': 'Perseus'
}

def fix_script(script_path, phase_num):
    """Fix a single phase script."""
    with open(script_path, 'r') as f:
        content = f.read()

    # Fix HGBS_DIR
    content = content.replace(
        "HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS'",
        f"HGBS_DIR = '{perseus_data['HGBS_DIR']}'"
    )

    # Fix FITS file paths
    content = content.replace(
        "COL_DEN_FILE = os.path.join(HGBS_DIR, 'HGBS_tauN3_hires_column_density_map.fits')",
        f"COL_DEN_FILE = os.path.join(HGBS_DIR, '{perseus_data['COL_DEN_FILE']}')"
    )

    content = content.replace(
        "TEMP_FILE = os.path.join(HGBS_DIR, 'HGBS_taurus_L1495_dust_temperature_map.fits')",
        f"TEMP_FILE = os.path.join(HGBS_DIR, '{perseus_data['TEMP_FILE']}')"
    )

    content = content.replace(
        "TEMP_FILE = os.path.join(HGBS_DIR, 'HGBS_orionB_dust_temperature_map.fits')",
        f"TEMP_FILE = os.path.join(HGBS_DIR, '{perseus_data['TEMP_FILE']}')"
    )

    content = content.replace(
        "SKELETON_FILE = os.path.join(HGBS_DIR, 'HGBS_taurusL1495_skeleton_map.fits')",
        f"SKELETON_FILE = os.path.join(HGBS_DIR, '{perseus_data['SKELETON_FILE']}')"
    )

    # Fix catalog paths and imports
    content = content.replace(
        "from parse_taurus_catalog import parse_taurus_catalog",
        f"from {perseus_data['CAT_PARSER']} import {perseus_data['CAT_PARSER_FUNC']}"
    )

    content = content.replace(
        "from parse_catalog import parse_hgbs_catalog",
        f"from {perseus_data['CAT_PARSER']} import {perseus_data['CAT_PARSER_FUNC']}"
    )

    content = content.replace(
        "self.cores = parse_taurus_catalog(os.path.join(HGBS_DIR, 'HGBS_taurusL1495_derived_core_catalog.txt'))",
        f"self.cores = {perseus_data['CAT_PARSER_FUNC']}(os.path.join(HGBS_DIR, '{perseus_data['CAT_FILE']}'))"
    )

    content = content.replace(
        "self.cores = parse_hgbs_catalog(os.path.join(HGBS_DIR, 'HGBS_orionB_derived_core_catalog.txt'))",
        f"self.cores = {perseus_data['CAT_PARSER_FUNC']}(os.path.join(HGBS_DIR, '{perseus_data['CAT_FILE']}'))"
    )

    content = content.replace(
        "CAT_FILE = os.path.join(HGBS_DIR, 'HGBS_taurusL1495_derived_core_catalog.txt')",
        f"CAT_FILE = os.path.join(HGBS_DIR, '{perseus_data['CAT_FILE']}')"
    )

    # Fix results file path
    content = content.replace(
        "results_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS/phase2_results.npz'",
        "results_file = os.path.join(HGBS_DIR, 'phase2_results.npz')"
    )

    content = content.replace(
        "results_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/phase2_results.npz'",
        "results_file = os.path.join(HGBS_DIR, 'phase2_results.npz')"
    )

    # Fix distance
    content = content.replace(
        "DISTANCE_PC = 140.0",
        f"DISTANCE_PC = {perseus_data['DISTANCE']}"
    )

    # Fix region name in headers
    content = content.replace("HGBS AQUILA", "HGBS PERSEUS")
    content = content.replace("HGBS Taurus", "HGBS Perseus")
    content = content.replace("Taurus L1495", "Perseus")
    content = content.replace("Taurus (L1495)", "Perseus")

    # Fix pixel size fallback for Phase 4
    content = content.replace(
        "self.pixel_size_pc = 0.00378  # From Phase 3",
        "self.pixel_size_pc = 0.006  # Approximate for Perseus"
    )

    with open(script_path, 'w') as f:
        f.write(content)

    print(f"Fixed {os.path.basename(script_path)}")

# Fix all phase scripts
for i in range(1, 6):
    script_path = os.path.join(HGBS_PERSEUS_DIR, f'hgbs_discovery_phase{i}.py')
    if os.path.exists(script_path):
        fix_script(script_path, i)

print("\nAll Perseus scripts fixed!")
