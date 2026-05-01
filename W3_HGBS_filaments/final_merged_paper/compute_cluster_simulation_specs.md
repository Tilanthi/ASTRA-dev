# Compute Cluster Simulation Specifications
## For Resolving Peer Review Concerns and Critical Gaps

**Date**: 29 April 2026  
**Purpose**: Definitive tests to address all peer review concerns and missing observables  
**Framework**: Athena++ MHD with Ray parallelization  
**Estimated Total Simulations**: ~400-600 across 4 campaigns

---

## Executive Summary

This specification document defines four simulation campaigns designed to definitively resolve the critical gaps identified in peer review:

1. **CAMPAIGN 1**: Perpendicular-field λ/W measurements (100-150 sims) - HIGHEST PRIORITY
2. **CAMPAIGN 2**: Multi-fibre bundle simulations (80-120 sims) - SECONDARY PRIORITY
3. **CAMPAIGN 3**: Non-ideal MHD linear growth (60-80 sims) - TERTIARY PRIORITY
4. **CAMPAIGN 4**: Near-critical λ/W calibration (80-100 sims) - VALIDATION PRIORITY

All campaigns are designed with explicit λ/W measurement as the primary output, addressing the core critique that previous work only measured t_frag.

---

## CAMPAIGN 1: Perpendicular-Field λ/W Measurements (HIGHEST PRIORITY)

### Scientific Objective
Measure the fragmentation wavelength λ/W for perpendicular magnetic field geometry (θ = 90°), which characterizes ~90% of HGBS filaments per Planck polarization measurements. This addresses the PRIMARY gap identified in peer review: we know perpendicular fields don't suppress fragmentation (based on t_frag), but we don't know whether they modify λ/W.

### Key Question
Does perpendicular-field fragmentation produce λ/W ≈ 4.0 (classical hydrodynamic value, as suggested by lack of magnetic tension along the axis) or a modified wavelength that could help explain the observed sub-Jeans spacing (λ/W ≈ 2.8)?

### Parameter Space
```python
PARAMETERS = {
    'f': [1.2, 1.5, 2.0, 2.5],  # mass-to-flux ratio
    'beta': [0.5, 1.0, 2.0, 3.0],  # plasma beta
    'theta': [90],  # perpendicular field only
    'mach': [1.0],  # fixed turbulence for initial campaign
    'resolution': '128^3 standard, 256^3 for validation',
    'seeds': 3  # random seeds per parameter point
}
```

Total simulations: 4 × 4 × 1 × 1 × 3 = 48 (minimal) to 96 (extended)

### Critical Simulation Requirements

#### 1. Extended Runtime Configuration
```bash
# MUST run until t > 2.0 t_J to allow longitudinal beading to develop
# Previous simulations stopped at t_frag when radial collapse began
wallclock_timeout = 21600  # 6 hours (vs. previous 2 hours)
max_simulation_time = 2.5  # t_J units
```

#### 2. HDF5 Snapshot Strategy
```python
# DENSE snapshots for λ/W measurement
snapshot_interval = 0.05  # t_J units (very fine)
snapshot_start = 0.5      # t_J units (start after initial transient)
variables_to_save = [
    'rho',      # density for λ/W measurement
    'vx', 'vy', 'vz',  # velocity fields
    'Bx', 'By', 'Bz'   # magnetic fields
]
# SAVE ALL SNAPSHOTS - no selective retention
# Expected storage: ~5-10 GB per simulation
```

#### 3. λ/W Measurement Pipeline
```python
def measure_lambda_W(density_field, axis='x'):
    """
    Measure fragmentation wavelength from density field.
    
    Method: Peak finding in longitudinal density profiles
    1. Extract density along filament axis (average over y-z plane)
    2. Apply Gaussian smoothing (σ = 2 cells)
    3. Find local maxima (peaks) with prominence > 5% of max density
    4. Compute spacing between adjacent peaks
    5. Return median spacing as λ/W
    6. Also report: N_peaks, std(λ), min(λ), max(λ)
    
    Quality flags:
    - 'NO_PEAKS': No longitudinal structure (radial collapse only)
    - 'FEW_PEAKS': < 3 peaks (insufficient statistics)
    - 'GOOD': >= 3 peaks with consistent spacing
    """
    # Implementation details provided in analysis scripts
```

#### 4. Domain Size Considerations
```
# Use longer domain to capture multiple wavelengths
Lx = 16 * lambda_J  # (vs. previous 8 * lambda_J)
Ly = Lz = 2 * lambda_J  # maintain transverse resolution

# Rationale: Perpendicular fields may produce λ/W ≠ 4.0
# Need to capture at least 2-3 fragmentation wavelengths
```

### Ray Parallelization Configuration
```yaml
ray_cluster:
    num_cpus: 64  # adjust for your cluster
    num_nodes: 4  # if using multi-node
    per_job: 
        simulations: 4  # parallel sims per Ray job
        walltime: "08:00:00"  # 8 hours per job
    
athena_config:
    mpi_per_sim: 4  # MPI processes per simulation
    omp_per_mpi: 2  # OpenMP threads per MPI process
    total_cores_per_sim: 8
```

### Data Reduction Requirements

#### Primary Outputs (for each simulation)
```json
{
    "simulation_id": "PERP_LW_f1.5_beta1.0_seed1",
    "parameters": {
        "f": 1.5,
        "beta": 1.0,
        "theta": 90,
        "mach": 1.0,
        "resolution": 128
    },
    "results": {
        "t_frag": 0.35,  # t_J units
        "lambda_W": {
            "value": 3.7,
            "std": 0.4,
            "n_peaks": 5,
            "min": 3.1,
            "max": 4.3,
            "quality_flag": "GOOD"
        },
        "final_state": {
            "max_density": 1.5e-15,  # g/cm^3
            "longitudinal_variance": 0.03,  # σ²(ρ_x)/<ρ>²
            "collapsed": true
        }
    },
    "snapshots": [
        {
            "time": 0.5,
            "lambda_W": 3.8,
            "peak_locations": [2.1, 6.3, 10.5, 14.7]  # in units of W
        },
        # ... more snapshots
    ]
}
```

#### Secondary Outputs (for archive)
- Full HDF5 snapshots (for re-analysis)
- Simulation logs (stdout/stderr)
- Configuration files (athena input files)

### Success Criteria
1. **Primary**: At least 70% of simulations achieve 'GOOD' quality flag (>= 3 peaks)
2. **Secondary**: Clear trend in λ/W vs. f and/or β (or lack thereof)
3. **Tertiary**: Convergence test at 256³ resolution confirms 128³ results

### Timeline Estimate
- **Simulation time**: 48-96 sims × 6 hours = 288-576 core-hours
- **Analysis time**: Minimal (automated pipeline)
- **Total wall-clock**: 1-2 weeks on 64-core cluster

---

## CAMPAIGN 2: Multi-Fibre Bundle Simulations (SECONDARY PRIORITY)

### Scientific Objective
Test the hierarchical structure hypothesis: if filaments consist of multiple velocity-coherent fibres, and each fibre fragments at λ/W ≈ 4.0, does the apparent filament-level spacing compress to λ/W ≈ 2.8 due to projection/averaging effects?

This is the "most promising explanation" for the discrepancy that wasn't tested.

### Key Question
Can the √N_fibres compression model (Yang et al. 2024) explain the observed factor of 1.4 discrepancy between classical theory (λ/W = 4.0) and observations (λ/W = 2.8)?

### Parameter Space
```python
PARAMETERS = {
    'n_fibres': [1, 2, 4, 6, 8],  # number of fibres in bundle
    'fibre_separation': [1.5, 2.0, 2.5],  # in units of W
    'f_global': [1.2, 1.5],  # global mass-to-flux for bundle
    'beta': [1.0, 2.0],  # plasma beta
    'relative_phase': [0, 0.5, 1.0],  # phase offset between fibres
    'seeds': 2
}
```

Total simulations: 5 × 3 × 2 × 2 × 3 × 2 = 360 (full parameter space)  
Recommended: Start with 80-120 simulations covering key parameter combinations

### Simulation Setup

#### Geometry: Cylindrical Fibre Bundle
```
# Initial condition: N_fibre parallel filaments arranged in bundle
# Each fibre is a cylindrical density perturbation

FIBRE_GEOMETRY = {
    'type': 'cylinder_bundle',
    'arrangement': 'hexagonal_close_packed',  # for N >= 3
    'fibre_radius': 0.5 * W,  # each fibre has radius 0.5 W
    'separation': variable,  # 1.5-2.5 W centre-to-centre
    'length': Lx = 16 * lambda_J,
    'domain_width': Ly = Lz = (n_fibres + 2) * W
}

# Density profile for each fibre:
rho(r) = rho_0 * sech^2((r - r_centre) / fibre_radius)
# Overlapping fibres add their densities
```

#### Magnetic Field Configuration
```
# Two options to test:
# OPTION A: Global longitudinal field through entire bundle
B_field = [B0, 0, 0]  # uniform across all fibres

# OPTION B: Individual fibre fields (more realistic but harder)
# Each fibre has its own field, total field adds vectorially
# This requires careful setup to avoid numerical issues

# Start with OPTION A for initial campaign
```

### Measurement Strategy

#### Apparent Spacing Measurement
```python
def measure_apparent_spacing(density_field_3d):
    """
    Measure apparent spacing when N_fibres are projected together.
    
    This simulates what HGBS measurements do: they see the combined
    emission from all fibres along the line of sight and measure
    core spacing from that combined map.
    
    Method:
    1. Project density field along z-axis: Σ(x,y) = ∫ ρ(x,y,z) dz
    2. Identify filament skeleton from Σ(x,y)
    3. Extract cores from projected map (SExtractor-like)
    4. Compute pairwise median and nearest-neighbor spacings
    5. Return both statistics
    
    Compare with:
    - True individual fibre spacings (from analysis of single fibres)
    - Expected compression: lambda_apparent ≈ lambda_fibre / sqrt(N_fibres)
    """
```

#### Expected Results
```python
# If hierarchical structure hypothesis is correct:
EXPECTED = {
    'n_fibres = 1': lambda_apparent/W ≈ 4.0,  # classical
    'n_fibres = 2': lambda_apparent/W ≈ 2.8,  # observed!
    'n_fibres = 4': lambda_apparent/W ≈ 2.0,
    'n_fibres = 8': lambda_apparent/W ≈ 1.4
}

# The key test: Does 2-fibre bundle give λ/W ≈ 2.8?
# If YES: hierarchical structure is a viable explanation
# If NO: need other mechanisms
```

### Data Requirements
```json
{
    "simulation_id": "BUNDLE_N2_f1.5_sep2.0_phase0.0",
    "parameters": {
        "n_fibres": 2,
        "separation": 2.0,  # W
        "f_global": 1.5,
        "relative_phase": 0.0
    },
    "results": {
        "individual_fibre_spacing": {
            "fibre_1": {"lambda_W": 4.1, "n_cores": 4},
            "fibre_2": {"lambda_W": 3.9, "n_cores": 4}
        },
        "apparent_spacing": {
            "pairwise_median": 2.9,  # λ/W
            "nearest_neighbor": 2.1,  # λ/W
            "n_cores_total": 8
        },
        "compression_factor": {
            "measured": 4.0 / 2.9 = 1.38,
            "expected": 1 / sqrt(2) = 0.707,
            "agreement": "PARTIAL"  # note: measured ≠ expected
        }
    }
}
```

### Success Criteria
1. **Critical**: 2-fibre bundle produces λ/W ≈ 2.5-3.0 (overlap with observations)
2. **Important**: Compression factor follows predictable trend with N_fibres
3. **Validation**: Individual fibres fragment at λ/W ≈ 4.0 (classical)

### Timeline Estimate
- **Simulation time**: 80-120 sims × 8 hours = 640-960 core-hours
  (more expensive due to larger domains and complex ICs)
- **Analysis time**: Moderate (requires custom projection code)
- **Total wall-clock**: 2-3 weeks on 64-core cluster

---

## CAMPAIGN 3: Non-Ideal MHD Linear Growth (TERTIARY PRIORITY)

### Scientific Objective
Test whether non-ideal MHD effects (ambipolar diffusion, Hall effect) modify the fragmentation wavelength in the linear growth phase. This addresses the question: can non-ideal MHD explain the observed sub-Jeans spacing?

### Key Question
Does ambipolar diffusion increase λ/W by factor of 2-3 (as suggested by Mouschovias & Ciolek 1999), which would move AWAY from observed values, or does it produce λ/W ≈ 2.8?

### Important: Different Strategy from Full Collapse
```
CRITICAL DISTINCTION: 
- Previous campaigns ran to full radial collapse (t_frag ~ 0.3 t_J)
- This campaign stops at LINEAR GROWTH phase (t ~ 0.5-1.0 t_J)
- Goal: Measure GROWTH RATE vs. k to identify k_max → λ_max
- NOT to measure collapse time or final core properties
```

### Parameter Space
```python
PARAMETERS = {
    'f': [1.0, 1.2, 1.5],  # near-critical to supercritical
    'ionization_fraction': [1e-7, 3e-7, 1e-6, 3e-6],  # x_e
    'beta': [0.5, 1.0, 2.0],  # plasma beta
    'chi_ad': [0.1, 0.5, 1.0],  # AD diffusivity
    'seeds': 2
}
```

Total simulations: 3 × 4 × 3 × 3 × 2 = 216  
Recommended: Start with 60-80 simulations covering key parameter space

### Non-Ideal MHD Configuration for Athena++

```python
# Athena++ non-ideal MHD module configuration
NON_IDEAL_CONFIG = {
    'ambipolar_diffusion': True,
    'hall_effect': True,  # can be disabled if numerical issues
    'ohmic_resistivity': False,  # negligible at these densities
    
    # Ionization fraction (uniform for initial test)
    'xi_init': variable,  # 1e-7 to 1e-6
    
    # Ambipolar diffusion coefficient
    'chi_ad': variable,  # 0.1 to 1.0
    
    # Density-dependent ionization (optional refinement)
    'ionization_model': 'power_law',
    # n_e ∝ n^(alpha) with alpha ≈ 0.5-1.0
}
```

### Measurement Strategy: Dispersion Relation

```python
def measure_dispersion_relation(simulation_data):
    """
    Extract growth rate σ(k) for each wavenumber k.
    
    Method:
    1. For each snapshot at time t_i:
       - Fourier transform density along x: ρ̃(k, t_i)
    2. Track amplitude growth: |ρ̃(k, t)| for each k
    3. Fit exponential growth: |ρ̃(k, t)| ∝ exp(σ(k) * t)
    4. Extract σ(k) for each k
    5. Find k_max where σ(k) is maximum
    6. Convert: λ_max = 2π / k_max
    
    Output:
    - σ(k) curve for all k
    - k_max, λ_max for this simulation
    - Comparison with ideal MHD case
    """
    
    # Expected results based on literature:
    # - Ideal MHD: k_max corresponds to λ/W ≈ 4.0
    # - Non-ideal: k_max shifts to SMALLER k → LARGER λ
    # - Mouschovias & Ciolek (1999): λ increases by 2-3×
    
    # Key test: Does λ shift toward 2.8 or away from it?
```

### Snapshot Strategy
```python
# Need frequent early snapshots to capture linear growth
SNAPSHOTS = {
    'start_time': 0.1,  # t_J (start early for linear phase)
    'end_time': 1.0,    # t_J (stop before non-linear)
    'interval': 0.05,   # t_J (20 snapshots total)
    'variables': ['rho', 'vx', 'vy', 'vz', 'Bx', 'By', 'Bz',
                  'Jx', 'Jy', 'Jz']  # current density for AD effects
}
```

### Expected Challenges
1. **Numerical stiffness**: Non-ideal MHD requires small timesteps
   - Solution: Use adaptive timestepping, expect 2-3× slower
2. **Numerical instability**: Hall effect can be unstable
   - Solution: Start with ambipolar only, add Hall later if needed
3. **Parameter space is large**: x_e, χ_AD, density all affect coupling
   - Solution: Focus on physically motivated values (see below)

### Physically Motivated Parameters
```python
# From literature (n_e measurements in molecular clouds)
# n_H2 = 1e4 cm^-3: x_e ≈ 1e-7 (very weakly ionized)
# n_H2 = 1e5 cm^-3: x_e ≈ 3e-8 (even less ionized)

# For our simulations (n_0 ≈ 1e4 cm^-3):
# Start with x_e = 1e-7, 3e-7, 1e-6

# Ambipolar diffusion coefficient:
# χ_AD = v_A^2 * t_ion (where t_ion is ion-neutral collision time)
# Typical values: 0.1 to 1.0 (dimensionless)

# Start with:
TEST_CASES = [
    {'x_e': 1e-7, 'chi': 0.1},  # weak coupling
    {'x_e': 1e-7, 'chi': 1.0},  # moderate coupling
    {'x_e': 3e-7, 'chi': 0.5},  # intermediate
    {'x_e': 1e-6, 'chi': 0.5},  # strong coupling
]
```

### Success Criteria
1. **Primary**: Clear measurement of λ_max for each parameter combination
2. **Secondary**: Trend in λ vs. coupling strength (or lack thereof)
3. **Tertiary**: Determine whether non-ideal MHD moves λ toward or away from 2.8

### Timeline Estimate
- **Simulation time**: 60-80 sims × 12 hours = 720-960 core-hours
  (non-ideal MHD is 2-3× slower due to numerical stiffness)
- **Analysis time**: Significant (dispersion relation fitting)
- **Total wall-clock**: 3-4 weeks on 64-core cluster

### Priority Note
This campaign is TERTIARY priority because:
1. It's computationally expensive
2. Most promising explanation is multi-fibre (Campaign 2)
3. Run this only if Campaigns 1 and 2 are inconclusive

---

## CAMPAIGN 4: Near-Critical λ/W Calibration (VALIDATION PRIORITY)

### Scientific Objective
Directly measure λ/W for near-critical filaments (f = 1.0-1.2) with longitudinal magnetic fields. This provides the baseline calibration for comparing with observations and validates the field-geometry calibration used throughout the paper.

### Key Question
Do near-critical simulations produce λ/W ≈ 3.5-4.0 as claimed in the paper? Or is there a systematic offset?

### Parameter Space
```python
PARAMETERS = {
    'f': [1.00, 1.05, 1.10, 1.15, 1.20],  # near-critical
    'beta': [0.5, 1.0, 2.0],  # plasma beta
    'theta': [0],  # longitudinal field only
    'mach': [1.0],
    'resolution': [128, 256],  # convergence test
    'seeds': 3
}
```

Total simulations: 5 × 3 × 1 × 1 × 2 × 3 = 90

### Critical Requirements

#### 1. Extended Runtime for Longitudinal Beading
```python
# Near-critical filaments have LONG fragmentation times
# Must run to t > 1.5 t_J to capture beading

RUNTIME_CONFIG = {
    'max_time': 2.0,  # t_J units
    'wallclock': 14400,  # 4 hours
    'snapshot_interval': 0.1,  # t_J
    'snapshot_start': 0.5  # t_J
}
```

#### 2. High-Resolution Validation
```python
# Must confirm 128³ results at 256³ resolution
# Key question: Does λ/W change with resolution?

RESOLUTION_TEST = {
    'base_resolution': 128,
    'high_resolution': 256,
    'parameters_to_test': [
        {'f': 1.10, 'beta': 1.0},
        {'f': 1.15, 'beta': 1.0},
        {'f': 1.20, 'beta': 1.0}
    ],
    'tolerance': 0.2  # λ/W must agree within 0.2
}
```

#### 3. Measurement Methodology
```python
def measure_lambda_W_near_critical(density_field):
    """
    Measure λ/W for near-critical filaments.
    
    Challenge: At f ≈ 1.0, beading is weak and develops slowly
    Solution: Use sensitive peak detection with low threshold
    
    Method:
    1. Extract longitudinal density profile
    2. Apply Gaussian smoothing (σ = 3 cells for smooth peaks)
    3. Find peaks with prominence > 3% of max density
    4. Compute spacing statistics
    5. Quality flag: 'WEAK' if peak_prominence < 5%
    """
```

### Data Reduction
```json
{
    "simulation_id": "NEAR_CRIT_f1.10_beta1.0_res128_seed1",
    "results": {
        "lambda_W": {
            "value": 3.7,
            "std": 0.5,
            "n_peaks": 4,
            "peak_prominence": 0.08,  # 8% of max density
            "quality_flag": "WEAK"  # near-critical beading is weak
        },
        "t_frag": 1.25,  # t_J (longer than supercritical)
        "convergence": {
            "res128": 3.7,
            "res256": 3.8,
            "difference": 0.1,
            "converged": true
        }
    }
}
```

### Success Criteria
1. **Primary**: Measure λ/W for all f values with 'WEAK' or 'GOOD' quality
2. **Secondary**: Demonstrate resolution convergence (Δ < 0.2 in λ/W)
3. **Tertiary**: Confirm claimed range of λ/W ≈ 3.5-4.0

### Timeline Estimate
- **Simulation time**: 90 sims × 4 hours = 360 core-hours
- **Analysis time**: Minimal
- **Total wall-clock**: 1 week on 64-core cluster

---

## General Requirements for All Campaigns

### Athena++ Version and Configuration
```bash
ATHENA_VERSION = "21.0 or later (with non-ideal MHD support)"

CONFIG = {
    'coord': 'cartesian',  # all simulations in Cartesian
    'eos': 'isothermal',  # T = 10 K fixed
    'gravity': 'self-gravity',
    'solver': 'hlld',  # MHD solver
    'mpi': True,
    'omp_num_threads': 2,
    
    # Critical settings
    'Ncell_x': 128,  # or 256 for high-res
    'Ncell_y': 128,
    'Ncell_z': 128,
    
    # Boundary conditions
    'ix1_bc': 'periodic',  # longitudinal
    'ix2_bc': 'outflow',   # transverse
    'ix3_bc': 'outflow',
    
    # Output
    'output': 'hdf5',
    'dt': 'variable',  # adaptive timestep
    'cfl_number': 0.3  # conservative for stability
}
```

### Ray Parallelization Template
```python
# ray_cluster_config.yaml
cluster_config:
    cluster_name: "astra_filament_sims"
    max_workers: 64
    provider:
        type: "local"  # or "slurm" if available
    
    per_simulation:
        cpu: 8
        gpu: 0
        memory: 16  # GB
        runtime: "08:00:00"  # 8 hours max per sim
    
    directories:
        work_dir: "/path/to/athena_sims/"
        output_dir: "/path/to/outputs/"
        log_dir: "/path/to/logs/"
```

### Data Management

#### Directory Structure
```
athena_sims/
├── campaign1_perp_lambda/
│   ├── f1.5_beta1.0_seed1/
│   │   ├── input/              # Athena++ input files
│   │   ├── outputs/            # HDF5 snapshots
│   │   │   ├── *.hdf5
│   │   └── analysis/           # Reduced data products
│   │       ├── lambda_W.json   # Primary result
│   │       ├── peak_data.txt   # Peak locations
│   │       └── dispersion.png  # Diagnostic plots
│   └── ...
├── campaign2_bundle/
│   └── ...
├── campaign3_nonideal/
│   └── ...
├── campaign4_nearcrit/
│   └── └── ...
└── analysis/
    ├── scripts/
    │   ├── measure_lambda_W.py
    │   ├── measure_dispersion.py
    │   ├── bundle_projection.py
    │   └── compile_results.py
    ├── figures/
    └── summary_tables/
```

#### File Naming Convention
```
Simulation ID: {CAMPAIGN}_{PARAMS}_res{RES}_seed{SEED}

Example: PERP_f1.5_beta1.0_mach1.0_res128_seed1

Files:
- {SIM_ID}.input          # Athena++ input file
- {SIM_ID}_hdf5/          # Snapshot directory
- {SIM_ID}_summary.json   # Primary results
- {SIM_ID}_peaks.txt      # Peak locations vs time
- {SIM_ID}_log.txt        # Simulation log
```

### Analysis Pipeline (Python)

#### Primary Analysis Script
```python
#!/usr/bin/env python3
"""
analyze_lambda_W.py

Primary analysis script for measuring fragmentation wavelength
from Athena++ HDF5 outputs.

Usage:
    python analyze_lambda_W.py <simulation_directory>

Outputs:
    - lambda_W_summary.json  (primary result)
    - peak_evolution.png     (diagnostic plot)
    - density_profiles.txt   (for re-analysis)
"""

import h5py
import numpy as np
import json
from pathlib import Path

def measure_lambda_W(density_field, axis=0, W_units=8):
    """
    Measure fragmentation wavelength from 3D density field.
    
    Parameters
    ----------
    density_field : 3D array
        Density field from Athena++ snapshot
    axis : int
        Filament axis (default: 0 = x)
    W_units : float
        Filament width in grid units (default: 8 for 128³)
    
    Returns
    -------
    result : dict
        Dictionary with lambda_W measurement and quality flags
    """
    # Average over transverse plane
    rho_1d = density_field.mean(axis=(1, 2))
    
    # Normalize
    rho_1d = rho_1d / rho_1d.mean()
    
    # Find peaks
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(
        rho_1d,
        prominence=0.05,  # 5% of max density
        distance=W_units//2  # minimum spacing
    )
    
    # Compute spacing
    if len(peaks) < 3:
        return {
            'lambda_W': np.nan,
            'n_peaks': len(peaks),
            'quality_flag': 'FEW_PEAKS',
            'peaks': peaks.tolist()
        }
    
    # Spacing in grid units
    spacings = np.diff(peaks)
    lambda_grid = spacings.mean()
    
    # Convert to lambda/W
    lambda_W = lambda_grid / W_units
    
    return {
        'lambda_W': lambda_W,
        'lambda_W_std': spacings.std() / W_units,
        'lambda_W_min': spacings.min() / W_units,
        'lambda_W_max': spacings.max() / W_units,
        'n_peaks': len(peaks),
        'quality_flag': 'GOOD' if len(peaks) >= 3 else 'FEW_PEAKS',
        'peaks': peaks.tolist()
    }

def process_simulation(sim_dir):
    """Process all snapshots from one simulation."""
    sim_dir = Path(sim_dir)
    
    results = []
    for snapshot in sorted(sim_dir.glob("*.hdf5")):
        with h5py.File(snapshot, 'r') as f:
            rho = f['dens'][:]
        
        result = measure_lambda_W(rho)
        result['time'] = float(snapshot.stem.split('.')[-2])
        results.append(result)
    
    # Find final (converged) value
    final = max(results, key=lambda r: r['time'])
    
    summary = {
        'simulation_id': sim_dir.name,
        'final_lambda_W': final['lambda_W'],
        'quality_flag': final['quality_flag'],
        'evolution': results,
        'parameters': extract_parameters(sim_dir)
    }
    
    # Save summary
    with open(sim_dir / 'lambda_W_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary

if __name__ == '__main__':
    import sys
    process_simulation(sys.argv[1])
```

#### Compilation Script
```python
#!/usr/bin/env python3
"""
compile_campaign_results.py

Compile all simulation results into summary tables and figures.

Usage:
    python compile_campaign_results.py <campaign_directory>
"""

import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def compile_results(campaign_dir):
    """Compile all results from a campaign."""
    campaign_dir = Path(campaign_dir)
    
    # Collect all results
    all_results = []
    for sim_dir in campaign_dir.glob("*_seed*"):
        summary_file = sim_dir / 'lambda_W_summary.json'
        if summary_file.exists():
            with open(summary_file) as f:
                data = json.load(f)
                all_results.append(data)
    
    # Convert to DataFrame
    df = pd.json_normalize(all_results)
    
    # Save summary table
    df.to_csv(campaign_dir / 'campaign_summary.csv', index=False)
    
    # Generate figures
    generate_figures(df, campaign_dir)
    
    return df

def generate_figures(df, campaign_dir):
    """Generate summary figures."""
    # Figure 1: λ/W vs. f
    fig, ax = plt.subplots()
    for beta in df['parameters.beta'].unique():
        subset = df[df['parameters.beta'] == beta]
        ax.errorbar(subset['f'], subset['final_lambda_W'],
                    yerr=subset['lambda_W_std'],
                    label=f'β={beta}', marker='o')
    ax.axhline(y=4.0, linestyle='--', color='gray', label='Classical')
    ax.axhline(y=2.8, linestyle=':', color='red', label='Observed')
    ax.set_xlabel('Mass-to-flux ratio f')
    ax.set_ylabel('Fragmentation wavelength λ/W')
    ax.legend()
    plt.savefig(campaign_dir / 'lambda_W_vs_f.png', dpi=150)
```

### Quality Control and Validation

#### Pre-Simulation Checks
```python
def validate_simulation_setup(sim_params):
    """Validate parameters before running simulation."""
    checks = []
    
    # Check 1: Resolution is sufficient
    if sim_params['resolution'] < 128:
        checks.append('WARNING: Resolution < 128³ may not resolve beading')
    
    # Check 2: Domain size is adequate
    Lx = sim_params['domain_length_x']
    min_lambda = 2.0  # minimum expected wavelength
    if Lx < 3 * min_lambda:
        checks.append('ERROR: Domain too short to capture 3 wavelengths')
    
    # Check 3: Runtime is sufficient
    max_time = sim_params['max_time']
    if sim_params['f'] < 1.3 and max_time < 1.5:
        checks.append('WARNING: Near-critical sims need t > 1.5 t_J')
    
    # Check 4: Output frequency
    snapshot_interval = sim_params['snapshot_interval']
    if snapshot_interval > 0.1:
        checks.append('WARNING: Coarse snapshots may miss peak evolution')
    
    return checks
```

#### Post-Simulation Validation
```python
def validate_simulation_results(sim_dir):
    """Validate results after simulation completes."""
    summary_file = sim_dir / 'lambda_W_summary.json'
    
    with open(summary_file) as f:
        data = json.load(f)
    
    issues = []
    
    # Check 1: Did we get enough peaks?
    if data['quality_flag'] == 'NO_PEAKS':
        issues.append('CRITICAL: No longitudinal structure - radial collapse only')
    elif data['quality_flag'] == 'FEW_PEAKS':
        issues.append('WARNING: < 3 peaks - unreliable statistics')
    
    # Check 2: Is lambda_W physically reasonable?
    lambda_W = data['final_lambda_W']
    if lambda_W < 1.0:
        issues.append(f'UNUSUAL: λ/W = {lambda_W:.2f} < 1.0')
    elif lambda_W > 10.0:
        issues.append(f'UNUSUAL: λ/W = {lambda_W:.2f} > 10.0')
    
    # Check 3: Did simulation run long enough?
    final_time = data['evolution'][-1]['time']
    if final_time < data['parameters']['max_time'] * 0.9:
        issues.append(f'WARNING: Simulation stopped early at t={final_time:.2f}')
    
    return issues
```

### Deliverables Format

#### For Each Campaign
```
campaign_{NAME}/
├── README.md                    # Campaign description
├── simulation_table.csv         # All parameters and results
├── summary_statistics.json     # Aggregate statistics
├── figures/
│   ├── lambda_W_vs_f.png        # Main result
│   ├── lambda_W_vs_beta.png
│   ├── quality_flags.png        # Data quality assessment
│   └── convergence.png          # Resolution convergence
└── data/
    ├── raw_results/             # All JSON files from sims
    └── processed/               # Compiled CSV files
```

#### Summary Statistics JSON Format
```json
{
    "campaign": "campaign1_perp_lambda",
    "n_simulations": 96,
    "n_successful": 84,
    "n_failed": 12,
    
    "results": {
        "mean_lambda_W": 3.7,
        "std_lambda_W": 0.6,
        "range_lambda_W": [2.1, 5.2],
        "n_good_quality": 68,
        "n_few_peaks": 16,
        "n_no_peaks": 0
    },
    
    "trends": {
        "lambda_W_vs_f": {
            "slope": -0.2,
            "correlation": -0.35,
            "p_value": 0.02
        },
        "lambda_W_vs_beta": {
            "slope": 0.1,
            "correlation": 0.15,
            "p_value": 0.31
        }
    },
    
    "comparison_with_observation": {
        "observed_lambda_W": 2.8,
        "simulated_mean": 3.7,
        "discrepancy_factor": 1.32,
        "overlap_range": [2.1, 5.2],
        "conclusion": "PARTIAL_OVERLAP"
    }
}
```

---

## Execution Order and Priorities

### Phase 1: Immediate (Weeks 1-2)
**Campaign 4 (Near-Critical Calibration)** and **Campaign 1 (Perpendicular λ/W)**

**Why this order:**
1. Campaign 4 is quick and validates baseline
2. Campaign 1 addresses the PRIMARY gap
3. Both use standard MHD (no non-ideal complications)

**Parallel execution:** Can run Campaigns 1 and 4 simultaneously on different nodes

### Phase 2: Conditional (Weeks 3-6)
**Campaign 2 (Multi-Fibre Bundles)** - ONLY if Campaign 1 results warrant

**Trigger conditions:**
- If Campaign 1 shows λ/W ≈ 4.0 for perpendicular fields → Campaign 2 is CRITICAL
- If Campaign 1 shows λ/W ≈ 2.8 for perpendicular fields → Campaign 2 is lower priority
- If Campaign 1 fails (no peaks) → Re-run with different parameters first

**Why conditional:** Campaign 2 is the "most promising explanation" but is expensive

### Phase 3: Tertiary (Weeks 7-10)
**Campaign 3 (Non-Ideal MHD)** - ONLY if Campaigns 1 and 2 are inconclusive

**Trigger conditions:**
- If Campaign 1 + 2 cannot explain observations
- If referee specifically requests non-ideal MHD tests
- If preparing for major revision (not minor revision)

**Why last:** Most expensive and most complex

---

## Summary Table of Campaigns

| Campaign | Priority | N_sims | Core-hours | Duration | Key Deliverable |
|----------|----------|--------|------------|----------|-----------------|
| 1: Perp λ/W | HIGHEST | 48-96 | 288-576 | 1-2 weeks | λ/W for θ=90° |
| 2: Multi-fibre | SECONDARY | 80-120 | 640-960 | 2-3 weeks | Bundle compression test |
| 3: Non-ideal | TERTIARY | 60-80 | 720-960 | 3-4 weeks | λ vs coupling strength |
| 4: Near-crit | VALIDATION | 90 | 360 | 1 week | Baseline calibration |

**Total estimated compute time:**
- Best case (Campaigns 1 + 4): ~650 core-hours (~1 week on 64 cores)
- Medium case (Campaigns 1 + 2 + 4): ~1300 core-hours (~3 weeks on 64 cores)
- Worst case (All 4 campaigns): ~2000 core-hours (~6 weeks on 64 cores)

---

## Getting Started: Minimal Working Example

### Test Simulation
```bash
# Start with a single test simulation
cd campaign1_perp_lambda/
mkdir test_f1.5_beta1.0

# Create Athena++ input file
cat > test_f1.5_beta1.0/input.inp <<EOF
<job>
problem_id = filament_perp_test

<time>
tlim = 2.5
nlim = 100000
dt_par = 0.3

<mesh>
nx1 = 128
nx2 = 128
nx3 = 128

<hydro>
iso_sound_speed = 1.88e4   # 0.187 km/s in CGS

<field>
B1 = 1e-4  # weak field for β = 1.0

<gravity>
grav_const = 6.674e-8  # CGS

<output>
dt = 0.05
file_type = 'hdf5'
variable = 'prim'
EOF

# Run simulation (using Ray)
python run_with_ray.py test_f1.5_beta1.0/input.inp
```

### Verify Output
```bash
# Check if simulation produced peaks
python analyze_lambda_W.py test_f1.5_beta1.0/

# Expected output:
# lambda_W_summary.json with quality_flag = 'GOOD'
# If quality_flag = 'NO_PEAKS', need longer runtime or different params
```

---

## Contact and Support

For questions about these specifications, simulation setup, or data reduction:
- Analysis scripts: See `analysis/` directory
- Ray configuration: See `ray_cluster_config.yaml`
- Athena++ documentation: https://princetonuniversity.github.io/Athena++/

---

**End of Specification Document**
