# Critical Transition Zone Mapping (CTZM) Campaign
**Date**: 2026-05-13 | **Referee Response**: Near-Critical Extrapolation Validation

---

## Campaign Objective

**Primary Goal**: Determine whether the fragmentation wavelength ratio λ/W evolves smoothly or discontinuously across the critical transition zone (f ≈ 1.2–1.5) separating near-critical filaments (where longitudinal beading occurs) from supercritical filaments (where radial collapse dominates).

**Science Question**: Is the extrapolation from near-critical simulations (f ≲ 1.2) to the supercritical regime (f ≈ 1.5–3.0) where HGBS filaments exist justified by smooth evolution of λ/W across the transition zone?

**Referee Concern**: "The comparison between simulation predictions and HGBS observations rests on an unvalidated extrapolation from the near-critical regime (f ≈ 1.0–1.2 where λ/W can be directly measured) to the supercritical regime (f ≈ 1.5–3.0 where HGBS filaments lie). Our simulations demonstrate a physical regime change at f ≈ 1.2–1.5 where radial collapse suppresses longitudinal beading."

---

## Parameter Space

| Parameter | Values | Rationale |
|-----------|--------|-----------|
| **Line-mass fraction (f)** | 1.2, 1.3, 1.4, 1.5 | The transition zone where behavior changes |
| **Plasma beta (β)** | 0.3, 0.5, 1.0, 2.0 | Full magnetic range from strong to weak |
| **Mach number (M)** | 1.0, 2.0 | Representative turbulence levels |
| **Random seeds** | 3 per parameter point | Statistical robustness |
| **Field geometry** | Longitudinal (B∥x) | Primary geometry for λ/W calibration |

**Total Simulations**: 4 × 4 × 2 × 3 = **96 simulations**

---

## Key Technical Requirements

### 1. HDF5 Snapshot Strategy (CRITICAL)

**Challenge**: At f ≥ 1.2, radial collapse can suppress longitudinal beading. We need high-cadence snapshots to capture λ/W evolution **before** radial collapse dominates.

**Snapshot Configuration**:
- **Output interval**: Δt = 0.02 tJ (2.5× finer than standard 0.05 tJ)
- **Maximum snapshots**: 200 per simulation (covers t = 0 → 4.0 tJ)
- **Snapshots stored**: Full 3D density field for longitudinal profile extraction

**Rationale**: Fine temporal sampling enables:
1. Detection of transient beading patterns before radial collapse
2. Tracking of λ/W evolution as function of time
3. Determination of whether beading wavelength stabilizes before collapse

### 2. Extended Wall-Clock Timeout

**Challenge**: Transition-zone filaments may fragment more slowly than highly supercritical cases.

**Timeout Configuration**:
- **Wall-clock timeout**: 14,400 seconds (4 hours)
- **Simulation timeout**: t_max = 4.0 tJ (if fragmentation occurs earlier)

**Rationale**: Near-critical filaments can have t_frag ≈ 1.1–1.5 tJ; 4-hour timeout ensures we capture fragmentation even in borderline cases.

### 3. Problem Generator Modifications

**Required Changes from Standard Filament Setup**:

1. **HDF5 Output Configuration**:
   ```
   <output1>
     out_fmt       = 24      # HDF5 output
     dt            = 0.02    # Output every 0.02 tJ
     data_format   = %12.5e
     variable      = cons    # Conservative variables
     file_num      = 0       # Starting file number
     file_sfre     = full    # Full 3D output
   </output1>
   ```

2. **Timestep Watchdog Configuration**:
   ```
   <time>
     nlim          = 1.0e8   # Large nlim to allow extended runtime
     tlim          = 4.0     # Max simulation time (tJ)
     dt_watchdog   = 1.0e-8  # Fragmentation detection threshold
   </time>
   ```

---

## Physical Predictions

### Expected Behaviors

| f value | Expected behavior | λ/W measurement feasibility |
|---------|-------------------|-----------------------------|
| **1.2** | Near-critical, longitudinal beading likely | Direct measurement probable |
| **1.3** | Transition zone, mixed behavior possible | Measurement challenging but feasible |
| **1.4** | Early supercritical, radial collapse may dominate | Measurement requires early-time snapshots |
| **1.5** | Supercritical, radial collapse likely dominant | Measurement may be impossible |

### Magnetic Field Dependence

| β value | Expected effect on transition |
|---------|------------------------------|
| **0.3** | Strong B delays collapse, may enable beading at higher f |
| **0.5** | Moderate B support, intermediate behavior |
| **1.0** | Weak B support, transition occurs at lower f |
| **2.0** | Very weak B, collapse dominates at lower f |

---

## Analysis Pipeline

### Stage 1: Peak Detection from Longitudinal Profiles

**Algorithm**:
1. Extract density profile ρ(x) along filament axis (y = z = 0)
2. Apply smoothing kernel (σ = 2 cells) to reduce noise
3. Find local maxima using scipy.signal.find_peaks
4. Filter peaks by prominence (> 5% above background)
5. Measure spacing between adjacent peaks
6. Compute median spacing → λ_meas

**Output**: For each snapshot, record:
- Snapshot number and time (t/tJ)
- Number of detected peaks
- Median spacing λ_meas (cells)
- λ/W ratio: λ_meas / W_core
- Density contrast: ρ_max / ρ_0

### Stage 2: Time Evolution Analysis

**For each simulation**:
1. Track λ_meas(t) from t = 0 → t_frag
2. Determine if λ_meas stabilizes before fragmentation
3. Classify simulation outcome:
   - **BEADING_STABLE**: Longitudinal beading detected, λ_meas stabilizes
   - **BEADING_TRANSIENT**: Beading detected but λ_meas unstable
   - **RADIAL_COLLAPSE**: No longitudinal beading detected

**Output Classification**:
```python
{
  "simulation_id": "f1.3_b0.5_M1.0_seed0",
  "classification": "BEADING_STABLE",
  "t_frag": 1.245,
  "lambda_W_final": 2.87,
  "lambda_W_stable_time": 1.10,
  "n_peaks_final": 6,
  "density_contrast": 8.42
}
```

### Stage 3: Transition Zone Mapping

**Smooth vs Discontinuous Test**:

1. **λ/W vs f curves**: Plot λ/W_final as function of f for each β
2. **Statistical test**: Fit piecewise-linear model with breakpoint at f_crit
   - Null hypothesis: Single linear trend λ/W(f) = a + bf
   - Alternative hypothesis: Two regimes with breakpoint at f = 1.35
3. **Decision criterion**: If breakpoint model improves R² by > 0.10 → discontinuous transition

**Visualization**:
- Figure 1: λ/W vs f for all β values with error bars
- Figure 2: Classification map (BEADING vs RADIAL) in (f, β) plane
- Figure 3: Time evolution of λ/W for representative cases

---

## Ray Cluster Configuration

### Infrastructure Specifications

- **Platform**: astra-climate Google Cloud E2 instances
- **CPUs**: 220 vCPUs total
- **Concurrent simulations**: 6 (optimized for memory constraints)
- **MPI ranks per simulation**: 32 (256³ domain = 8×2×2 MeshBlocks, 32³ blocks)
- **Memory per simulation**: ~8 GB RAM
- **Disk I/O**: HDF5 snapshots → ~2 GB per simulation (200 snapshots × 10 MB)

### Execution Configuration

**Ray Launcher**:
```python
# ctzm_launcher.py
import ray
import subprocess
import json
from pathlib import Path

RAY_CONFIG = {
    "num_cpus": 220,
    "concurrent_sims": 6,
    "mpi_ranks_per_sim": 32,
    "timeout_sec": 14400,  # 4 hours
    "sim_binary": "/path/to/athena_ic"  # Compiled from filament_ctzm.cpp
}

PARAMETER_GRID = [
    {"f": 1.2, "beta": 0.3, "mach": 1.0, "seed": i} for i in range(3)
    + {"f": 1.3, "beta": 0.3, "mach": 1.0, "seed": i} for i in range(3)
    # ... (full parameter space)
]
```

**Estimated Wall Time**:
- Per simulation: ~2–3 hours average (f = 1.2) to ~0.5 hours (f = 1.5)
- Total for 96 sims at 6 concurrent: **~48–72 hours**

---

## Deliverables

### Simulation Outputs

1. **HDF5 snapshot files** (200 per sim): Longitudinal density profiles
2. **Fragmentation logs**: t_frag, classification, final state
3. **Parameter log**: JSON file with simulation IDs and parameters

### Analysis Outputs

1. **Peak detection results**: `ctzm_peak_detection.json`
2. **Classification summary**: `ctzm_classification_summary.json`
3. **λ/W vs f dataset**: `ctzm_lambda_W_vs_f.csv`
4. **Statistical test results**: `ctzm_smooth_vs_discontinuous.json`
5. **Figures**:
   - `fig_lambda_W_vs_f.pdf`: λ/W vs f for all β
   - `fig_classification_map.pdf`: BEADING vs RADIAL in (f, β) plane
   - `fig_time_evolution.pdf`: λ/W(t) for representative cases

### Paper Integration

**New Section for MNRAS Paper**:

```latex
\subsection{Critical Transition Zone Mapping}

To validate the extrapolation from near-critical simulations ($f \lesssim 1.2$)
to the supercritical regime where HGBS filaments reside ($f \approx 1.5$--$3$),
we conducted a Critical Transition Zone Mapping (CTZM) campaign spanning
$f = 1.2$--$1.5$ with fine temporal resolution (HDF5 snapshots every
$\Delta t = 0.02\,t_{\rm J}$). This enables direct measurement of the
fragmentation wavelength $\lambda/W$ in the transition zone where
longitudinal beading and radial collapse compete.

\textbf{Campaign specifications}: 96 simulations with $f \in \{1.2, 1.3, 1.4, 1.5\}$,
$\beta \in \{0.3, 0.5, 1.0, 2.0\}$, $\mathcal{M} \in \{1.0, 2.0\}$, and 3 random
seeds per parameter point. All simulations use longitudinal magnetic field
geometry with isothermal equation of state.

\textbf{Key result}: [To be filled after analysis]
```

---

## Success Criteria

The campaign will be considered successful if it produces:

1. **Definitive classification** of each (f, β, M) parameter point as BEADING or RADIAL
2. **Measured λ/W values** for all BEADING cases with quantified uncertainties
3. **Statistical test result** for smooth vs discontinuous transition (p-value < 0.05 preferred)
4. **Clear statement** on whether extrapolation from f ≲ 1.2 to f ≈ 1.5–3.0 is justified

**Referee Response**: The results will enable a clear response to the referee's concern:

- **If smooth**: "The CTZM campaign demonstrates smooth evolution of λ/W across f = 1.2–1.5, validating the extrapolation from near-critical simulations to the supercritical regime."
- **If discontinuous**: "The CTZM campaign reveals a discontinuous transition in λ/W at f ≈ 1.35, indicating that theoretical predictions must be regime-specific. Our λ/W measurements apply to the near-critical regime (f ≲ 1.35), while HGBS filaments require supercritical-specific theory."

---

## Files Included

1. **README.md** (this file): Campaign overview and specifications
2. **filament_ctzm.cpp**: Athena++ problem generator with fine HDF5 output
3. **ctzm_launcher.py**: Ray distributed execution script
4. **ctzm_analyze.py**: Peak detection and classification pipeline
5. **ctzm_parameter_grid.json**: Full parameter space specification
6. **compile_athena_ic.sh**: Binary compilation script

---

## Execution Checklist

- [ ] Compile `athena_ic` binary from `filament_ctzm.cpp`
- [ ] Verify HDF5 output configuration (Δt = 0.02 tJ)
- [ ] Test single simulation to confirm snapshot behavior
- [ ] Deploy Ray cluster on astra-climate (220 vCPUs)
- [ ] Run full 96-simulation campaign (expected 48–72 hours)
- [ ] Verify all simulations completed successfully (check exit codes)
- [ ] Run peak detection analysis on all HDF5 outputs
- [ ] Generate classification summary and λ/W vs f dataset
- [ ] Perform statistical test for smooth vs discontinuous transition
- [ ] Generate figures for paper integration
- [ ] Draft referee response section based on results

---

**Campaign Status**: READY FOR DEPLOYMENT
**Last Updated**: 2026-05-13
