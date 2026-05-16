# Peer Review Validation Tests — MNRAS Filament Paper

**Purpose**: Address theoretical reviewer concerns through targeted Athena++ MHD simulations

**Date**: 2026-04-21

**Cluster**: 220-core HPC system using Ray parallelization

---

## Overview

This package contains three critical simulation campaigns designed to address the major theoretical concerns raised in the peer review:

1. **TEST_M3_RESOLUTION**: Resolution convergence test for stochastic zone (24 simulations)
2. **TEST_M2_EQUILIBRIUM**: Equilibrium vs. non-equilibrium initial conditions (20 simulations)
3. **TEST_M5_NONISOTHERMAL**: Non-isothermal equation of state effects (10 simulations)

**Total simulations**: 54
**Estimated runtime**: ~150-200 hours on 220 cores (depending on resolution tests)

---

## Quick Start

```bash
# Extract the package
tar -xzf peer_review_validation_tests.tar.gz
cd peer_review_validation_tests/

# Verify Ray installation
python3 -c "import ray; print(f'Ray {ray.__version__} OK')"

# Run the campaigns (execute sequentially)
./run_all_tests.sh
```

Each campaign can also be run independently:

```bash
cd TEST_M3_RESOLUTION/
python3 run_resolution_test.py
```

---

## Campaign Specifications

### TEST_M3_RESOLUTION: Resolution Convergence Test

**Purpose**: Validate whether the "stochastic transition zone" reflects physical behavior or numerical noise (Reviewer concern T-M3)

**Scientific justification**: The Truelove criterion (16 cells/λ_J) was established for uniform-density collapse, not magnetized filament fragmentation. If the apparent stochasticity at 12 parameter points is resolution-dependent, the claim is spurious.

**Parameter selection**: Representative points from the DTC transition region where β_crit varies most rapidly:

| Test Point | f | β | M | Rationale |
|------------|---|---|---|-----------|
| R1 | 1.4 | 0.3 | 1.0 | Near M=1 stability ridge |
| R2 | 1.4 | 0.5 | 1.0 | M=1, near transition |
| R3 | 1.5 | 0.3 | 1.0 | Low-f, low-β edge |
| R4 | 1.5 | 0.5 | 2.0 | Central transition zone |
| R5 | 1.6 | 0.3 | 2.0 | Higher f, M=2 |
| R6 | 1.6 | 0.5 | 2.0 | M=2 transition |
| R7 | 1.7 | 0.5 | 2.0 | Mid-f range |
| R8 | 1.7 | 0.7 | 3.0 | Higher M |
| R9 | 1.8 | 0.3 | 2.0 | High-f, low-β |
| R10 | 1.8 | 0.5 | 3.0 | High-f, higher M |
| R11 | 1.9 | 0.5 | 2.0 | Upper f range |
| R12 | 2.0 | 0.7 | 3.0 | Highest f in test |

**Resolutions tested**:
- **128³** (baseline, matches DTC)
- **256³** (2× resolution, 32 cells/λ_J → exceeds Truelove criterion)

**Seeds**: 42 and 137 for all points (matches DTC)

**Simulations**: 12 points × 2 resolutions × 2 seeds = **48 simulations**

**Success criteria**:
- If stochastic behavior (P_frag = 0.5) persists at 256³ → physical result
- If stochasticity disappears or changes systematically → resolution-dependent artifact

**Analysis**: Compare fragmentation outcomes, λ/W, and growth rates between resolutions. Compute convergence metrics.

---

### TEST_M2_EQUILIBRIUM: Equilibrium Initial Conditions

**Purpose**: Establish whether DTC results are robust to the choice of initial conditions (Reviewer concern T-M2)

**Scientific justification**: The DTC initializes filaments with ρ(r) = ρ₀/[1+(r/W)²] and uniform B₀, which is not in magnetohydrostatic equilibrium. The filament may undergo transient radial collapse before fragmentation develops, potentially contaminating the results.

**Parameter selection**: Representative points spanning the HGBS-relevant parameter space:

| Test Point | f | β | M | Physical regime |
|------------|---|---|---|-----------------|
| E1 | 1.4 | 0.3 | 1.0 | Near-critical, M=1 |
| E2 | 1.4 | 0.7 | 2.0 | Low-f, M=2 |
| E3 | 1.6 | 0.5 | 2.0 | Central transition |
| E4 | 1.8 | 0.5 | 2.0 | Mid-f, M=2 |
| E5 | 2.0 | 0.7 | 3.0 | High-f, M=3 |
| E6 | 1.5 | 0.5 | 1.0 | Low-f edge |
| E7 | 1.7 | 0.7 | 3.0 | Higher M |
| E8 | 1.9 | 0.3 | 2.0 | High-f, low-β |
| E9 | 1.6 | 0.9 | 1.0 | Higher β |
| E10 | 1.8 | 0.5 | 1.0 | Mid-f, M=1 |

**Initial conditions compared**:
1. **Profile-based (DTC standard)**: ρ(r) = ρ₀/[1+(r/W)²], uniform B₀
2. **Uniform IC**: ρ = ρ₀ (constant), B = B₀ (constant), with small random perturbations

**Resolution**: 256³ (matches DTC resolution for W3 validation, 32 cells/λ_J)

**Seeds**: 42 only (single seed sufficient for IC comparison)

**Simulations**: 10 points × 2 IC approaches = **20 simulations**

**Analysis**:
- Measure radial collapse timescale (ρ_center evolution at t < 0.5 t_J)
- Measure fragmentation timescale (C_final exceeds threshold)
- Compare final outcomes: λ/W, N_cores, growth rates
- Establish whether results are IC-dependent or robust

**Success criteria**:
- If fragmentation outcomes are similar between IC approaches → results are robust
- If outcomes differ significantly → DTC results may be contaminated by transient effects

---

### TEST_M5_NONISOTHERMAL: Non-Isothermal Equation of State

**Purpose**: Test whether the paper's central negative conclusion holds under more realistic thermodynamics (Reviewer concern T-M5)

**Scientific justification**: HGBS filaments have temperature gradients (~15K envelope → ~10K interior), giving γ_eff ≈ 0.9 (mildly polytropic). Clarke et al. (2016) showed non-isothermal effects can shift fragmentation boundaries substantially.

**Parameter selection**: Representative points from the HGBS regime:

| Test Point | f | β | M | Relevance |
|------------|---|---|---|-----------|
| N1 | 1.5 | 0.5 | 2.0 | Typical HGBS |
| N2 | 1.6 | 0.7 | 2.0 | Moderate β |
| N3 | 1.8 | 0.3 | 3.0 | Higher M |
| N4 | 1.7 | 0.5 | 2.0 | Mid-range |
| N5 | 1.9 | 0.7 | 2.0 | Upper f |

**Equations of state tested**:
1. **Isothermal** (γ = 1.0): Baseline for comparison
2. **Mildly cooling** (γ_eff = 0.9): Represents realistic HGBS temperature gradient
3. **Moderately cooling** (γ_eff = 0.8): Tests sensitivity to cooling strength

**Resolution**: 256³ (32 cells/λ_J, well-resolved)

**Seeds**: 42 only (EOS comparison doesn't require multiple seeds)

**Simulations**: 5 points × 3 EOS variants = **15 simulations**

**Analysis**:
- Extract λ/W for each case
- Compare with isothermal baseline
- Establish whether non-isothermal effects shift predictions significantly
- Quantify the offset: Δ(λ/W) = λ/W_noniso - λ/W_iso

**Success criteria**:
- If |Δ(λ/W)| < 0.2 → non-isothermal effects are minor, paper's conclusion holds
- If |Δ(λ/W)| > 0.5 → non-isothermal effects are significant, may affect conclusion

---

## Athena++ Configuration

All simulations use:

**Physics**:
- Self-gravitating ideal MHD
- FFT-based Poisson solver for gravity
- HLLD Riemann solver
- 2nd-order reconstruction in space and time

**Units**:
- 4πG = 4π² → λ_J = 1.0 code unit
- c_s = 1.0 (sound speed)
- B₀ set by plasma β

**Domain**:
- Longitudinal (x1): L = 8λ_J
- Transverse (x2, x3): L = 2λ_J × 2λ_J
- Periodic boundary conditions

**Time integration**:
- CFL = 0.3
- t_max = 4.0 t_J (sufficient for fragmentation)
- Output interval: Δt = 0.5 t_J (9 snapshots total)

**Initial perturbations**:
- Magneto-Jeans wavelength: λ_MJ = λ_J√(1 + 2/β)
- Amplitude: ε = 10⁻⁴ (small enough for linear regime)
- Seeds: 42, 137 (for stochastic tests)

---

## Cluster Requirements

### Hardware
- **Minimum**: 100 CPU cores
- **Recommended**: 220 CPU cores (optimal for Ray configuration)
- **Memory**: 2 GB per CPU core minimum
- **Storage**: 50 GB free space for HDF5 outputs

### Software
```bash
# Required modules
module load python/3.9
module load openmpi/4.1.1
module load hdf5/1.12.1

# Or install via conda
conda create -n athena python=3.9
conda activate athena
pip install ray[default] h5py numpy matplotlib
```

### Athena++ binary
- Place `athena` binary at: `athena/bin/athena`
- Ensure MPI-enabled build with FFTW support
- Test: `mpirun -np 4 athena/bin/athena -i test.in -d outputs/`

---

## Directory Structure

```
peer_review_validation_tests/
├── README.md                      # This file
├── run_all_tests.sh              # Master script to run all campaigns
├── athena/                       # Athena++ binary (create symlink)
│   └── bin/athena
├── TEST_M3_RESOLUTION/           # Resolution convergence test
│   ├── run_resolution_test.py    # Ray-based driver
│   ├── config/
│   │   └── test_points.json      # 12 stochastic zone points
│   └── results/
├── TEST_M2_EQUILIBRIUM/          # Equilibrium IC test
│   ├── run_equilibrium_test.py
│   ├── config/
│   │   └── test_points.json      # 10 representative points
│   └── results/
├── TEST_M5_NONISOTHERMAL/        # Non-isothermal EOS test
│   ├── run_nonisothermal_test.py
│   ├── config/
│   │   └── test_points.json      # 5 HGBS points
│   └── results/
└── analysis/                     # Post-processing scripts
    ├── analyze_resolution.py
    ├── analyze_equilibrium.py
    ├── analyze_nonisothermal.py
    └── generate_report.py
```

---

## Runtime Estimates

### TEST_M3_RESOLUTION (48 simulations)
- **128³**: ~4 hours per sim on 16 cores → ~12 hours for 48 sims (parallelized)
- **256³**: ~32 hours per sim on 16 cores → ~96 hours for 48 sims (parallelized)
- **Total**: ~110 hours on 220 cores

### TEST_M2_EQUILIBRIUM (20 simulations)
- **256³**: ~32 hours per sim on 16 cores → ~40 hours for 20 sims (parallelized)
- **Total**: ~45 hours on 220 cores

### TEST_M5_NONISOTHERMAL (15 simulations)
- **256³**: ~32 hours per sim on 16 cores → ~30 hours for 15 sims (parallelized)
- **Total**: ~35 hours on 220 cores

**Grand total**: ~190 hours (8 days) on 220 cores

---

## Expected Output

Each simulation produces:
- **HDF5 snapshots**: 9 time slices at t = 0, 0.5, 1.0, ..., 4.0 t_J
- **HST file**: Full time history of diagnostic quantities
- **Log file**: Athena++ run log

Analysis scripts will extract:
- Density contrast C(t) = ρ_max/ρ_mean
- Fragmentation wavelength λ/W
- Number of cores N_cores
- Growth rate γ (from linear phase fit)
- Comparison metrics between test conditions

---

## Validation Criteria

### TEST_M3_RESOLUTION
✅ **Pass**: Stochasticity persists at 256³ (physical)
❌ **Fail**: Stochasticity disappears or changes pattern (numerical artifact)

### TEST_M2_EQUILIBRIUM
✅ **Pass**: Fragmentation outcomes agree within 20% between IC approaches (robust)
⚠️ **Partial**: Outcomes differ systematically (needs careful interpretation)
❌ **Fail**: Outcomes disagree qualitatively (DTC results not robust)

### TEST_M5_NONISOTHERMAL
✅ **Pass**: Non-isothermal effects change λ/W by < 0.2 (paper's conclusion stands)
⚠️ **Partial**: Effects are moderate (0.2 < Δ < 0.5) (may affect conclusion)
❌ **Fail**: Effects are large (Δ > 0.5) (central conclusion undermined)

---

## Reporting

After completion, run:

```bash
cd analysis/
python3 generate_report.py
```

This will create:
- `VALIDATION_REPORT.pdf`: Summary of all tests
- `VALIDATION_DATA.json`: Machine-readable results
- `figures/`: Diagnostic plots

---

## Troubleshooting

**Ray initialization fails**:
```bash
# Kill existing Ray workers
ray stop

# Restart with explicit resources
ray start --head --num-cpus=220
```

**Athena++ segfaults**:
- Check that HDF5 output directory exists
- Reduce `nprocs_per_sim` if memory-limited
- Verify MPI compatibility between build and runtime

**Simulations hang**:
- Check disk space: `df -h`
- Monitor with: `watch -n 10 nvidia-smi` (if GPU) or `htop`
- Review Athena++ logs for error messages

---

## Contact

For questions about simulation parameters or analysis:
- **Paper correspondence**: G.J. White (Open University)
- **ASTRA system**: astra-core system documentation

---

## References

1. Truelove et al. 1997, ApJ, 489, L179 — The Truelove criterion
2. Clarke et al. 2016, MNRAS, 458, 343 — Non-isothermal filament fragmentation
3. Hanawa & Tomisaka 2015, ApJ, 802, 21 — Filament equilibrium structure

---

*Package prepared for MNRAS second revision | 2026-04-21*
