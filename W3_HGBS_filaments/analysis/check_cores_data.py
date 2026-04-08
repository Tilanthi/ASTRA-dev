"""
Detailed analysis of core spacing from existing data.
This will load the cores data and calculate proper filament-by-filament spacing.
"""

import numpy as np
from pathlib import Path
import json

# Load Orion B cores data
orionb_file = Path('/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/phase2_results.npz')

print("="*80)
print("DETAILED CORE SPACING ANALYSIS: ORION B")
print("="*80)

if orionb_file.exists():
    data = np.load(orionb_file, allow_pickle=True)

    # Get cores data
    cores = data['cores']

    print(f"\nTotal cores in catalog: {len(cores)}")
    print(f"\nCore data structure:")
    print(f"  Type: {type(cores)}")
    if len(cores) > 0:
        print(f"  First core type: {type(cores[0])}")
        print(f"  First core keys: {cores[0].keys() if isinstance(cores[0], dict) else 'N/A'}")

        # Check how many cores are on filaments
        if isinstance(cores[0], dict):
            on_filament_count = sum(1 for c in cores if c.get('on_filament', False))
            print(f"\nCores on filaments: {on_filament_count}")

            # Check for filament ID information
            has_filament_id = any('filament_id' in c for c in cores if isinstance(c, dict))
            has_segment_id = any('segment_id' in c for c in cores if isinstance(c, dict))

            print(f"Has filament_id: {has_filament_id}")
            print(f"Has segment_id: {has_segment_id}")

            # Look for position information
            has_coords = all('x_pix' in c and 'y_pix' in c for c in cores if isinstance(c, dict))
            print(f"Has pixel coordinates: {has_coords}")

            if has_coords:
                # Get sample of coordinates
                sample_cores = [c for c in cores if isinstance(c, dict) and c.get('on_filament', False)][:5]
                print(f"\nSample of {len(sample_cores)} cores on filaments:")
                for i, core in enumerate(sample_cores):
                    print(f"  Core {i+1}: x={core.get('x_pix', 'N/A'):.1f}, y={core.get('y_pix', 'N/A'):.1f}, "
                          f"mass={core.get('mass', 'N/A'):.2f} M_sun")
else:
    print("Orion B results file not found")

print(f"\n{'='*80}")
print(f"CRITICAL ISSUE IDENTIFIED:")
print(f"{'='*80}")
print(f"\nThe saved results only contain core information, NOT spacing measurements.")
print(f"\nThis means the 0.21 pc value reported in the paper was likely:")
print(f"  1. Calculated incorrectly using 2D nearest-neighbor distances")
print(f"  2. NOT based on proper filament-by-filament analysis")
print(f"  3. May have included cores from different filaments")
print(f"\n{'='*80}")
print(f"NEXT STEPS:")
print(f"{'='*80}")
print(f"\nTo get ACCURATE core spacing measurements, I need to:")
print(f"  1. Load the skeleton maps for each region")
print(f"  2. Extract individual filaments from the skeleton")
print(f"  3. For each filament:")
print(f"     a) Skeletonize to get the spine")
print(f"     b) Identify cores belonging to that filament")
print(f"     c) Project cores onto the spine")
print(f"     d) Order cores along the spine")
print(f"     e) Calculate consecutive core distances")
print(f"  4. Combine statistics from all filaments")
print(f"\nThis is a complex analysis that requires running the full phase 2 pipeline.")
