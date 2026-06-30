#!/usr/bin/env python3
"""
Simplified Campaign Launcher for Rigid Cylinder Simulations
===========================================================

This script provides a step-by-step guide for running the rigid cylinder
campaign on a 220 CPU Ray cluster.

Author: G. J. White
Date: June 2026
"""

import os
import sys

# ============================================================================
# INSTALLATION INSTRUCTIONS
# ============================================================================

INSTALLATION_GUIDE = """
INSTALLATION INSTRUCTIONS
=======================

1. INSTALL REQUIRED PACKAGES:
```bash
pip install ray[default] numpy scipy h5py astropy
```

2. CLUSTER SETUP:
```bash
# On the cluster head node:
conda activate athena
# OR
module load ray

# Initialize Ray cluster:
ray start --head --num-cpus=220 --port=6379 \\
    --redis-max-memory=100000000000 \\
    --object-store-memory=100000000000
```

3. ATHENA++ SETUP:
Ensure Athena++ is installed and accessible. If not, see:
https://github.com/PrincetonUniversity/athena

4. SET PATHS:
```bash
export ATHENA_BIN=/path/to/athena/bin  # UPDATE THIS
export PATH=$ATHENA_BIN:$PATH
```

5. CREATE OUTPUT DIRECTORY:
```bash
mkdir -p /rigid_cylinder_outputs
```

"""

# ============================================================================
# QUICK START
# ============================================================================

QUICK_START = """
QUICK START
===========

Step 1: Generate simulation list
-----------------------------------
python rigid_cylinder_ray_campaign.py --config

This will show the campaign configuration.


Step 2: Launch simulations
---------------------------
python rigid_cylinder_ray_campaign.py --submit

This will:
- Generate 45 simulation configurations
- Submit them to the Ray cluster
- Monitor progress
- Analyze results automatically
- Package for GitHub


Step 3: Monitor progress
-------------------------
In a separate terminal, monitor Ray status:
```bash
ray status

# View dashboard at:
# http://localhost:8265
```


Step 4: Package and push
-----------------------
When simulations complete:
python rigid_cylinder_ray_campaign.py --package

This will:
- Analyze all results
- Extract λ/W measurements
- Package into tar.gz
- Push to GitHub


CAMPAIGN PARAMETERS
===================
- Line-mass f: [1.5, 1.8, 2.2, 2.6, 3.0]
- Plasma β: [0.5, 1.0, 2.0]
- Seeds per point: 3
- Total simulations: 45
- Runtime per sim: ~1-2 hours
- Estimated total: 45-90 hours

EXPECTED RESULTS
===============
If λ/W extrapolation is valid:
- Smooth λ/W(f) relation from f = 1.5 to 3.0
- λ/W decreases with f (as in near-critical)

If extrapolation fails:
- Sharp discontinuity at f ≈ 1.8-2.0
- Different functional form
- Or no longitudinal structure

"""

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*70)
    print("RIGID CYLINDER CAMPAIGN - QUICK START")
    print("="*70)

    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        print(INSTALLATION_GUIDE)
    else:
        print(QUICK_START)
        print()
        print("\nFor installation instructions, run:")
        print("  python rigid_cylinder_launcher.py --install")

if __name__ == "__main__":
    main()
