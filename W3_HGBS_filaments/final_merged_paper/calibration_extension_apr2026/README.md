# CALIBRATION_EXTENSION Campaign — Field-Geometry Calibration at f=1.3-2.0 (Apr 2026)

**36 MHD simulations**: Targeted measurement of the calibration factor C(f, β) = λ_frag/λ_MJ at intermediate supercriticality (f = 1.3-2.0, β = 0.3-1.0) to constrain the extrapolation uncertainty from near-critical (f = 1.0-1.2) to HGBS-relevant (f = 1.5-3.0) regimes.

## Science Motivation

**Peer Review Issue**: The field-geometry calibration λ_frag = (1.11 ± 0.12) λ_MJ(θ, β) is derived entirely from near-critical simulations at f = 1.0-1.2. Its application to HGBS filaments at f ≈ 1.5-3.0 constitutes a regime extrapolation of factor ~2-3 in supercriticality with NO demonstrated functional form for how the 1.11 factor scales with f.

**Key Question**: Does the calibration factor C(f, β) remain constant at ~1.11 across the f = 1.3-2.0 range, or does it vary systematically with supercriticality?

**Expected Result**: Direct measurement of C(f, β) at intermediate supercriticality, enabling:
1. Quantification of extrapolation uncertainty
2. Test of whether C(f) is constant or f-dependent
3. Improved λ/W prediction for HGBS filaments

## Simulation Configuration

**Parameter space:**
- Line-mass fraction: f = 1.3, 1.4, 1.5, 1.6, 1.8, 2.0 (6 values)
- Plasma beta: β = 0.3, 0.5, 1.0 (3 values)
- Field geometry: θ = 0° (longitudinal, baseline for calibration)
- Mach number: M = 1.0 (fixed)
- Random seeds: 42, 137 (2 seeds per parameter point)
- **Total simulations: 36**

**Mesh and domain:**
- Resolution: 256 × 64 × 64 cells
- MeshBlock: 32³
- Domain: 8 × 2 × 2 λ_J (periodic on all faces)
- Filament profile: Gaussian with W_core = 0.3 λ_J
- λ_J = 1 by construction (four_pi_G = 4π²)

**Physics configuration:**
- Magnetic field: Purely longitudinal (B || x-axis)
- Equation of state: Isothermal (γ = 1.0, P = ρc_s², c_s = 1)
- Self-gravity: FFT Poisson solver with 24 meshblocks
- Turbulence: Kolmogorov spectrum, δv/c_s = 10⁻⁴ (8 modes, v_x2 = v_x3 = 0)
- Boundary conditions: Periodic on all faces

**Runtime parameters:**
- tlim: 6.0 t_J (sufficient to capture fragmentation)
- Timeout: 3600s wall (1 hour, conservative for slower fragmentation at higher f)
- Output interval: Every 0.01 t_J (HST files for detailed analysis)
- MPI ranks: 24 (matches 24 FFT meshblocks required for correct gravity)

## Classification Criteria

**Primary outcome metric:**
- **FRAG**: Longitudinal beading detected with measurable wavelength λ_frag
- **STABLE**: No longitudinal beading within tlim
- **RADIAL_COLLAPSE**: Radial collapse dominates (cylinder flattens) without longitudinal structure

**Detection method:**
1. HST analysis: Measure peak-to-peak spacing in longitudinally-averaged density
2. FFT analysis: Compute power spectrum along x-axis, identify dominant wavelength
3. Visual inspection: Verify beading morphology in density slices

**Calibration factor measurement:**
For FRAG cases only:
- Extract λ_frag from HST time series
- Compute λ_MJ(θ=0°, β) from linear theory
- Calculate C = λ_frag / λ_MJ
- Report mean ± std across 2 seeds

## Scientific Deliverables

1. **C(f, β) table**: Calibration factor as function of f and β
2. **λ/W measurements**: Direct fragmentation wavelength-to-width ratios at f = 1.3-2.0
3. **Uncertainty quantification**: Standard error on C across β values and seeds
4. **Extrapolation analysis**: Test of constancy hypothesis (C = constant vs C(f) functional form)

## Expected Computational Cost

**Per simulation:**
- Setup: ~5 minutes (problem generation + initialization)
- Main evolution: ~15-45 minutes depending on f
- Higher f → faster fragmentation → shorter runtime
- Conservative estimate: 1 hour per simulation including overhead

**Total campaign:**
- 36 simulations × 1 hour = 36 hours wall time
- With 200 CPUs and 8 concurrent jobs (np=24 each): ~5 hours total
- Disk: ~2 GB for simulation outputs (36 dirs × ~50 MB each)

## Files

- `calibration_extension_spec.json` — Machine-readable parameter grid
- `run_campaign.py` — Python script to generate Athena++ input files
- `analyze_calibration.py` — Analysis script to measure C(f, β) from outputs
- `README.md` — This file

## Naming Convention

Simulation directories: `calib_f{f}_beta{beta}_s{seed}`
Example: `calib_f1.5_beta0.5_s42`

## Success Criteria

**Minimum success (baseline):**
- At least 50% of simulations show FRAG with measurable λ_frag
- C(f, β) measured for at least 3 f values at β = 0.3

**Full success (ideal):**
- >75% FRAG rate across parameter space
- Complete C(f, β) table for all 6 × 3 parameter combinations
- Clear functional form for C(f) dependence identified (constant, linear, power-law)

## Technical Notes

**Why f = 1.3-2.0?**
- f < 1.3: Too close to existing calibration (f = 1.0-1.2)
- f > 2.0: Rapid radial collapse dominates, longitudinal beading may be suppressed
- f = 1.3-2.0: Sweet spot where beading may still be detectable

**Why β = 0.3-1.0?**
- Covers weak (β = 1.0) to moderate (β = 0.3) magnetic fields
- β > 1.0: Field too weak to affect fragmentation (converges to hydrodynamic)
- β < 0.3: Approaches magnetically subcritical regime

**Timeout rationale:**
- At f = 1.3, fragmentation may be slower (t_frag ~ 1.2-1.5 t_J)
- At f = 2.0, fragmentation is faster (t_frag ~ 0.8-1.0 t_J)
- 3600s (1 hour) is conservative; may adjust downward after first few runs complete

## Contact

Operator: ASTRA PA (astra-pa)
Cluster: External 200-CPU system
Campaign date: April 2026
Status: READY FOR EXECUTION
