# Critical Regime Filament Spacing Simulation Campaign
# Target: f ≈ 2-3 (moderate supercriticality) regime directly relevant to HGBS filaments
# Purpose: Measure λ/W from MHD simulations to test theoretical explanations for observed λ/W ≈ 2.11

## Campaign Overview

This campaign addresses the critical gap identified in peer review: MHD simulations in the moderate supercriticality regime (f ≈ 2-3) that directly measure fragmentation wavelength λ/W for comparison with HGBS observations.

### Scientific Objectives

1. **Primary**: Measure λ/W as a function of (f, β, M) in the regime f ≈ 2-3
2. **Test magnetic tension mechanism**: Does λ/W approach 2.11 for realistic (β, M) values?
3. **Test hierarchical fragmentation**: Does λ/W remain ~4 at the fiber level even in supercritical filaments?
4. **Map the transition**: Characterize how λ/W varies from f ≈ 1 (near-critical) to f ≈ 3 (moderately supercritical)

### Parameter Space Coverage

#### Core Grid (f, β, M)

| Parameter | Values | Rationale |
|-----------|--------|-----------|
| f (line-mass ratio) | 1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0 | HGBS-relevant range |
| β (plasma beta) | 0.3, 0.5, 0.7, 1.0, 1.5, 2.0 | HGBS-inferred range |
| M (Mach number) | 1.0, 2.0, 3.0 | Typical turbulent conditions |

**Total base grid**: 7 × 6 × 3 = 126 simulations

#### Extended Grid (refinement)

For each combination that shows λ/W in the range 1.5-2.5:
- Additional β values at increments of 0.2
- Additional f values at increments of 0.1

Expected extended grid: ~200 additional simulations

**Total campaign**: ~325 simulations

### Simulation Specifications

#### Athena++ Configuration

```
Grid: 512³ resolution
Domain: Cylindrical filament with periodic boundary conditions
  - Length: L = 32H (where H = cs²/2πGρ₀)
  - Radius: R = 2H
  - Resolution: Δx = H/16 → ~32 cells across critical wavelength

Time integration:
  - Courant factor: CFL = 0.3
  - End time: t = 2.0 t_ff (free-fall time)
  - Output interval: Δt = 0.01 t_ff

Initial conditions:
  - Density profile: ρ(r) = ρ₀ / [1 + (r/R)²]
  - Magnetic field: Uniform B₀ along filament axis
  - Turbulence: Random velocity field with spectrum ∝ k⁻²
  - f varied by adjusting ρ₀ relative to critical mass per unit length
```

#### Physical Units

```
Reference values for HGBS filaments:
  - n(H₂) = 10⁴ cm⁻³ → ρ₀ = 2.3 × 10⁻²⁰ g cm⁻³
  - T = 10 K → cs = 0.19 km s⁻¹
  - B = 3-30 μG → β = 0.1-10
  - M_line,crit = 16 M⊙ pc⁻¹
  - W_fil = 0.1 pc
```

### Measurement Protocol

#### Primary Observable: λ/W

For each simulation, measure:

1. **Core identification**: Local density maxima with ρ > 5ρ₀
2. **Core positions**: Project onto filament axis
3. **Spacing calculation**: Pairwise median of core separations
4. **λ/W calculation**: (median spacing) / (filament width W)

#### Secondary Observables

- Fragmentation timescale: t_frag (time to first fragmentation)
- Density contrast: C = ρ_max/ρ₀
- Number of fragments: N_frag
- Growth rate: γ from early-time exponential phase

### Analysis Pipeline

```python
# Post-processing script (analyze_simulation.py)

import numpy as np
import h5py
from scipy.spatial import cKDTree
from scipy.signal import find_peaks

def measure_lambda_over_w(filename):
    """Measure λ/W from simulation output."""

    # Load 3D density field
    with h5py.File(filename, 'r') as f:
        rho = f['density'][:]  # shape: (nx, ny, nz)
        time = f['time'][()]

    # Identify filament axis (z-axis by construction)
    filament_axis = 2

    # Project onto transverse plane
    rho_xy = np.mean(rho, axis=filament_axis)

    # Identify filament skeleton in transverse plane
    skeleton = identify_skeleton(rho_xy)

    # Project density onto skeleton
    rho_1d = np.mean(rho[skeleton], axis=(0,1))

    # Find core positions along filament
    peaks, _ = find_peaks(rho_1d, height=5.0, distance=16)
    core_positions = peaks * dx  # Convert to physical units

    # Calculate pairwise median spacing
    if len(core_positions) < 2:
        return None  # No fragmentation

    from itertools import combinations
    spacings = [abs(p1 - p2) for p1, p2 in combinations(core_positions, 2)]
    lambda_median = np.median(spacings)

    # Calculate filament width
    from scipy.optimize import curve_fit
    def gaussian(r, A, sigma, x0):
        return A * np.exp(-(r - x0)² / (2*sigma²))

    # Fit radial profile
    r_profile = np.arange(-R, R, dx)
    rho_radial = rho[:, ny//2, nz//2]
    popt, _ = curve_fit(gaussian, r_profile, rho_radial, p0=[rho0, R, 0])
    W = 2.355 * popt[1]  # FWHM

    return lambda_median / W, len(core_positions), time
```

### Deliverables

For each completed simulation:
- `λ_W.txt`: One-line file with λ/W measurement
- `fragmentation_data.h5`: HDF5 file with core positions, spacings, times
- `density_slice_*.png`: Visualization of density field at key times

### Campaign Summary (upon completion)

- `results_summary.csv`: Table of all (f, β, M, λ/W, N_frag, t_frag) values
- `lambda_vs_beta.png`: λ/W vs β for different f values
- `lambda_vs_f.png`: λ/W vs f for different β values
- `comparison_with_observation.pdf`: Direct comparison with HGBS λ/W = 2.11

## Computational Requirements

Per simulation (512³ resolution):
- Memory: ~8 GB RAM
- Wallclock time: ~6-8 hours on 32 cores
- Disk space: ~2 GB per simulation (snapshots + outputs)

Total campaign (~325 simulations):
- Core-hours: ~65,000 core-hours
- Recommended allocation: 200 cores → ~325 hours (~2 weeks)
- Storage: ~650 GB

## Ray-based Parallel Execution

The campaign uses Python's Ray framework for parallel execution on HPC clusters.

### Driver Script Structure

```python
# run_campaign.py
import ray
from simulation import AthenaRunner

ray.init(num_cpus=200)

@ray.remote
def run_simulation(f, beta, M, seed):
    """Run one simulation in parallel."""
    runner = AthenaRunner(
        f=f, beta=beta, M=M,
        resolution=512,
        seed=seed
    )
    result = runner.execute()
    return {
        'f': f,
        'beta': beta,
        'M': M,
        'seed': seed,
        'lambda_over_W': result['lambda_over_W'],
        'n_frag': result['n_frag'],
        't_frag': result['t_frag']
    }

# Parameter grid
f_values = [1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0]
beta_values = [0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
M_values = [1.0, 2.0, 3.0]

# Launch all simulations
futures = []
for f in f_values:
    for beta in beta_values:
        for M in M_values:
            for seed in [1, 2]:  # 2 seeds per point
                future = run_simulation.remote(f, beta, M, seed)
                futures.append(future)

# Collect results
results = ray.get(futures)

# Save results
import pandas as pd
df = pd.DataFrame(results)
df.to_csv('results_summary.csv', index=False)
```

## Success Criteria

The campaign will be considered successful if:

1. **λ/W measured** for ≥80% of (f, β, M) combinations
2. **Cover HGBS regime**: At least 10 simulations have f ∈ [2.0, 2.5], β ∈ [0.5, 1.5], M ∈ [2.0, 3.0]
3. **Converged results**: Each simulation runs to t ≥ 1.5 t_ff or completes fragmentation
4. **Reproducibility**: ≥2 seeds per parameter point with ≤30% variance in λ/W

## Expected Scientific Outcomes

### Scenario 1: Magnetic tension confirmed
If simulations with f ≈ 2-3, β ≈ 0.5-1.5 yield λ/W ≈ 2.0-2.3:
- Strong support for magnetic tension mechanism
- Explains observed universal λ/W ≈ 2.1
- Predicts specific (β, M) combinations for observational test

### Scenario 2: Hierarchical fragmentation supported
If all simulations yield λ/W ≈ 3-4 regardless of β:
- Magnetic tension has weak effect in supercritical regime
- Observed λ/W ≈ 2 requires hierarchical interpretation
- Suggests fiber-level physics is dominant

### Scenario 3: New physics required
If λ/W shows unexpected behavior (e.g., non-monotonic with β):
- Indicates missing physics (ambipolar diffusion, non-isothermal EOS)
- Requires theoretical re-examination of filament fragmentation
- May point to new observational signatures

## Timeline

Week 1-2: Set up and test simulations (10 pilot runs)
Week 3-6: Run base grid (126 simulations)
Week 7-8: Run extended grid (200 simulations)
Week 9: Analysis and comparison with observations
Week 10: Paper preparation

## Notes

- This campaign directly addresses the primary criticism from peer review
- Results will enable a revised paper with full HGBS-relevant simulation coverage
- All simulation data will be made publicly available
- Analysis code will be archived on GitHub with DOI
