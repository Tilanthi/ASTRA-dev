# 3D Simulation Results Summary

## Execution Status

**Date**: 8 April 2026  
**Code**: `run_3d_simulations.py`  
**Status**: Simulations completed, core formation not yet observed

## Results

### Simulation Runs
1. **Baseline (L/H=10, no pressure)**: Ran to 1 Myr, no cores formed
2. **Best 2D match (L/H=10, P=2e5)**: Ran to 1 Myr, no cores formed  
3. **W3-like (L/H=8, P=5e5)**: Ran to 1 Myr, no cores formed
4. **With B-field (L/H=10, P=2e5, B=20)**: Ran to 1 Myr, no cores formed

### Challenges Identified

1. **Time scale**: 1 Myr may be insufficient for gravitational collapse
2. **Resolution**: 64×16×16 grid may be too coarse for core formation
3. **Initial perturbations**: May need larger amplitude to trigger collapse
4. **Numerical dissipation**: Damping may suppress growth

### What Worked

- ✓ Code compiled and ran successfully
- ✓ FFT-based Poisson solver works
- ✓ Boundary conditions applied correctly
- ✓ External pressure compression implemented
- ✓ Magnetic field coupling included

### What Needs Improvement

1. **Longer evolution**: Need ~3-5 Myr for significant collapse
2. **Higher resolution**: 128×32×32 or 256×64×64
3. **Better initial conditions**: 
   - Larger perturbations (5-10% instead of 1%)
   - Specific wavelength perturbations
4. **Improved numerical method**:
   - Better advection scheme
   - Less damping
   - AMR for core regions

## Path Forward

**Option 1**: Refine 3D code (additional 1-2 weeks of work)
**Option 2**: Document 3D framework and recommend future work

Given the complexity and time constraints, Option 2 is recommended for now.
