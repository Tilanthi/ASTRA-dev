# Rigid Cylinder Campaign - Complete Setup Guide

## Overview

This campaign addresses the referee's concern about extrapolation from near-critical (f ≈ 1.0–1.2) to supercritical (f ≥ 1.5) regime by using rigid cylindrical boundary conditions in Athena++ to suppress radial collapse.

## Scientific Goal

**Question**: Does the fragmentation wavelength λ/W from near-critical simulations (f ≤ 1.2) extrapolate continuously to the supercritical regime (f ≥ 1.5)?

**Method**: Use rigid cylindrical wall at r = R_cylinder to suppress radial collapse, allowing longitudinal fragmentation modes to develop even in supercritical filaments.

## Campaign Specifications

### Parameter Grid
- **f (line-mass fraction)**: 1.5, 1.8, 2.2, 2.6, 3.0 (5 values)
- **β (plasma beta)**: 0.5, 1.0, 2.0 (3 values)
- **M (Mach number)**: 1.0 (fixed)
- **θ (field geometry)**: 0° (longitudinal, fixed)
- **Seeds**: 1, 2, 3 (3 per parameter point)
- **Total simulations**: 5 × 3 × 1 × 1 × 3 = **45 simulations**

### Domain & Resolution
- **Axial length**: L_x = 16 λ_J (to accommodate 3–4 wavelengths)
- **Cylinder radius**: R_cyl = 1.0 λ_J (rigid reflecting wall)
- **Resolution**: 256 × 64 × 64 cells
- **High axial resolution** critical for accurate λ/W measurement

### Simulation Parameters
- **EOS**: Isothermal (γ = 1.0)
- **t_max**: 2.0 t_J (sufficient for fragmentation)
- **Output interval**: Every 0.05 t_J (40 snapshots total)
- **CFL number**: 0.4

### Boundary Conditions
- **x boundaries**: Outflow
- **y, z boundaries**: Reflecting (rigid cylinder wall at r = R_cyl)
- **This suppresses radial collapse while allowing longitudinal modes**

## Ray Cluster Setup

### Hardware Requirements
- **CPUs**: 220 cores
- **Memory**: 400 GB total (object store: 100 GB)
- **Storage**: ~500 GB for HDF5 outputs

### Installation

```bash
# On cluster head node
module load python/3.9
pip install ray[default]==2.9.0 numpy scipy h5py astropy matplotlib

# Or if using conda
conda create -n rigid_cylinder python=3.9
conda activate rigid_cylinder
pip install ray numpy scipy h5py astropy matplotlib
```

### Initialize Ray Cluster

```bash
# Start Ray head node
ray start --head \\
    --num-cpus=220 \\
    --port=6379 \\
    --redis-max-memory=100000000000 \\
    --object-store-memory=100000000000 \\
    --dashboard-host=0.0.0.0 \\
    --dashboard-port=8265
```

### Athena++ Installation

Athena++ must be compiled with:
- HDF5 output enabled
- 3D cartesian geometry
- MHD modules

Install from: https://github.com/PrincetonUniversity/athena

## Execution

### Step 1: Prepare Environment

```bash
# Set paths
export ATHENA_HOME=/path/to/athena  # UPDATE THIS
export PATH=$ATHENA_HOME/bin:$PATH
export PYTHONPATH=$ATHENA_HOME/python:$PATH

# Create output directory
mkdir -p /rigid_cylinder_outputs
```

### Step 2: Launch Campaign

```bash
cd /Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/rigid_cylinder_campaign

# Option 1: Interactive
python rigid_cylinder_ray_campaign.py --config

# Option 2: Submit all
python rigid_cylinder_ray_campaign.py --submit

# Option 3: Just show instructions
python rigid_cylinder_launcher.py
```

### Step 3: Monitor Progress

```bash
# Ray dashboard
http://localhost:8265

# Check cluster status
ray status

# List running jobs
ray list
```

### Step 4: Analyze Results (Automatic)

Analysis runs automatically when simulations complete. Manual analysis:

```bash
python analyze_rigid_cylinder.py /rigid_cylinder_outputs
```

### Step 5: Package for GitHub

```bash
python rigid_cylinder_ray_campaign.py --package
```

This creates:
- `rigid_cylinder_campaign_YYYYMMDD.tar.gz`
- Pushes to `Tilanthi/ASTRA-dev/campaigns/`
- Provides full URL for paper

## Expected Results

### If Extrapolation is Valid
- Smooth λ/W(f) relation from f = 1.5 to 3.0
- Power-law exponent similar to near-critical regime (~ -0.1 to -0.2)
- Continuous transition at f ≈ 1.2–1.5

### If Extrapolation Fails
- Sharp discontinuity in λ/W at f ≈ 1.8–2.0
- Different functional form than near-critical
- Or no longitudinal structure (pure radial collapse even with rigid BC)

## Analysis Deliverables

1. **JSON results**: `rigid_cylinder_analysis.json`
   - λ/W for each simulation
   - Classification (FRAGMENTED, STABLE, etc.)
   - Power-law fit parameters

2. **Plot**: `rigid_cylinder_lambdaW_vs_f.pdf`
   - λ/W vs. f (linear and log-log)
   - Comparison with near-critical extrapolation
   - Comparison with HGBS observation

3. **Paper-ready summary**
   - Table with all λ/W measurements
   - Statistical analysis
   - Figure for manuscript

## Troubleshooting

### Issue: No fragmentation detected
**Possible causes**:
- Rigid BC too restrictive
- Simulation time too short
- Resolution too low

**Solutions**:
- Increase t_max to 3.0 t_J
- Increase axial resolution to 512
- Relax rigid BC (allow small radial motion)

### Issue: Athena++ compilation errors
**Solution**: Ensure HDF5 library is installed and linked correctly

### Issue: Ray cluster won't start
**Solutions**:
- Check port 6379 is available
- Check Redis is not already running
- Verify memory allocation

## Contact

For issues or questions, contact:
- G. J. White
- Email: [your email]
- GitHub: Tilanthi/ASTRA-dev
