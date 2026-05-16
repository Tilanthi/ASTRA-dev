# Expanded Referee Response Campaign — Test Design Specifications

**Date**: 2026-05-13
**Total Simulations**: 204
**Campaign Package Version**: 1.0

## Overview

This document provides detailed test specifications for the three sub-campaigns addressing referee concerns B2, B3, and B5. Each test is designed to answer a specific scientific question with minimal parameter space while maintaining statistical robustness.

---

## Sub-Campaign 1: CTZM_PERP (96 Simulations)

### Referee Concern
**B2**: The perpendicular-field result creates unresolved tension. Perpendicular fields give λ/W ≈ 1.25, but HGBS observes λ/W ≈ 2.8.

### Scientific Question
Does the smooth λ/W(f) evolution observed in longitudinal CTZM also hold for perpendicular fields across the critical transition zone (f = 1.2–1.5)?

### Hypothesis
- **H1 (Geometry Independence)**: λ/W(f) evolution is smooth for perpendicular fields (R² > 0.9), confirming that smooth evolution is a general feature of filament fragmentation physics.
- **H2 (Geometry Dependence)**: Perpendicular fields show discontinuous evolution or early onset of radial collapse, revealing fundamental differences in fragmentation physics.

### Parameter Space Justification

| Parameter | Values | Justification |
|-----------|--------|---------------|
| **f** | [1.2, 1.3, 1.4, 1.5] | Bridges the gap between near-critical (f<1.2) and supercritical (f>1.5) regimes |
| **β** | [0.3, 0.5, 1.0, 2.0] | Spans strong to weak magnetic fields; covers HGBS range |
| **M** | [1.0, 2.0] | Tests subsonic to transonic turbulence |
| **seeds** | [0, 1, 2] | 3 seeds for statistical robustness at each parameter point |
| **θ** | 90° | Perpendicular field geometry (HGBS-relevant) |

### Sample Size Calculation
- 4 f values × 4 β values × 2 M values × 3 seeds = **96 simulations**
- This provides 3 independent measurements per (f, β, M) cell
- At 90% power to detect R² > 0.9 vs R² < 0.5

### Success Criteria
- **Primary**: Linear fit R² > 0.9 for at least 3 of 4 β values
- **Secondary**: < 10% radial collapse classifications across entire campaign
- **Exploratory**: Quantify any f-dependent behavior in perpendicular geometry

### Deliverables
1. λ/W vs f plots for each β value with linear fits and R²
2. Classification breakdown (beading vs radial collapse)
3. Slope comparison: longitudinal vs perpendicular
4. Smooth evolution confirmation/disproof

---

## Sub-Campaign 2: EOS_SENSITIVITY (48 Simulations)

### Referee Concern
**B3**: The EOS sensitivity testing is incomplete. The paper states "isothermal predictions are therefore conservative" for λ/W, but λ/W was never measured for γ ≠ 1.

### Scientific Question
Does the fragmentation wavelength λ/W depend on the adiabatic index γ for realistic molecular cloud conditions (γ = 0.7–1.0)?

### Hypothesis
- **H1 (EOS Independence)**: λ/W is independent of γ across γ = 0.7–1.0, validating the isothermal assumption.
- **H2 (EOS Dependence)**: λ/W varies systematically with γ, requiring non-isothermal correction factors in theoretical predictions.

### Parameter Space Justification

| Parameter | Values | Justification |
|-----------|--------|---------------|
| **f** | [1.0, 1.1, 1.2] | Near-critical regime where λ/W measurement is possible |
| **γ** | [0.7, 0.8, 0.9, 1.0] | Covers range from strongly cooling (γ=0.7) to isothermal (γ=1.0) |
| **β** | [1.0] | Fixed to reduce parameter space; equipartition field |
| **M** | [1.0] | Fixed; subsonic regime |
| **seeds** | [0, 1, 2, 3] | 4 seeds for robust statistics at each γ |

### Sample Size Calculation
- 3 f values × 4 γ values × 4 seeds = **48 simulations**
- 4 seeds provide mean ± SEM for each (f, γ) combination
- At 80% power to detect Δλ/W > 0.3 between γ values

### Physical Background
- Real molecular clouds have γ ≈ 0.7–0.95 due to radiative cooling
- Isothermal assumption (γ = 1.0) is commonly used but not rigorously tested for λ/W
- Linear theory predicts λ_MJ ∝ c_s/√(Gρ), but non-linear fragmentation may differ

### Success Criteria
- **Primary**: < 5% variation in λ/W across γ = 0.7–1.0 (independence confirmed)
- **Secondary**: Quantify any γ-dependence with functional form
- **Exploratory**: Test whether γ affects t_frag-λ/W coupling

### Deliverables
1. λ/W vs γ plot with error bars
2. Statistical test for γ-dependence (ANOVA or equivalent)
3. Quantified γ-dependence factor if H2 is supported
4. Recommendation on whether non-isothermal corrections are needed

---

## Sub-Campaign 3: TURB_AMPLITUDE (60 Simulations)

### Referee Concern
**B5**: The turbulence amplitude in simulations is δv = M × cs × 10⁻⁴ ("small compared to sound speed"), but real filaments have supersonic turbulence (M ∼ 2–5 with full amplitude). The extrapolation to supersonic conditions has not been demonstrated.

### Scientific Question
Is the fragmentation wavelength λ/W independent of perturbation amplitude from the linear regime (10⁻⁴) to the fully supersonic regime (1.0)?

### Hypothesis
- **H1 (Amplitude Independence)**: λ/W is constant across perturbation amplitudes, validating the extrapolation from small-amplitude simulations to real turbulent filaments.
- **H2 (Amplitude Dependence)**: λ/W varies with perturbation amplitude, indicating that small-amplitude simulations do not capture supersonic fragmentation physics.

### Parameter Space Justification

| Parameter | Values | Justification |
|-----------|--------|---------------|
| **f** | [1.0, 1.2] | Near-critical to early transition zone |
| **ampl** | [10⁻⁴, 10⁻³, 10⁻², 10⁻¹, 1.0] | Spans 4 orders of magnitude from linear to supersonic |
| **β** | [1.0] | Fixed; equipartition field |
| **M** | [1.0] | Fixed; subsonic background |
| **seeds** | [0, 1, 2] | 3 seeds for statistical robustness |

### Sample Size Calculation
- 2 f values × 5 amplitudes × 3 seeds = **60 simulations**
- 3 seeds provide mean ± SEM for each (f, ampl) combination
- At 80% power to detect Δλ/W > 0.4 across amplitude range

### Physical Background
- Linear perturbation theory: Growth rate ∝ √(Gρ) but wavelength set by Jeans scale
- Non-linear regime: Large perturbations may trigger secondary fragmentation
- Real clouds: Supersonic turbulence creates shocks that could affect core spacing

### Success Criteria
- **Primary**: < 10% variation in λ/W across amplitude range (independence confirmed)
- **Secondary**: Quantify any amplitude-dependence with functional form
- **Exploratory**: Test whether large amplitudes change classification (beading vs collapse)

### Deliverables
1. λ/W vs amplitude plot (log scale) with error bars
2. Statistical test for amplitude-dependence
3. Quantified amplitude-dependence factor if H2 is supported
4. Assessment of whether supersonic extrapolation is valid

---

## Simulation Methodology (Common to All Campaigns)

### Numerical Parameters
| Parameter | Value | Justification |
|-----------|-------|---------------|
| **Domain** | 256 × 64 × 64 cells | Adequate resolution for longitudinal modes |
| **Physical size** | L = 8 λ_J | Accommodates 2–3 fragmentation wavelengths |
| **Resolution** | Δx = L/256 = 0.03 λ_J | Resolves core formation (validated in previous work) |
| **WALI time** | 4.0 t_J | Allows fragmentation for f > 1.0 |
| **HDF5 output** | dt = 0.02 t_J | Fine time-sampling for λ/W measurement |
| **MPI ranks** | 32 | Optimal for 256³ domain (32³ meshblocks) |

### Classification Scheme
Each simulation is classified based on HDF5 analysis:
- **BEADING_STABLE**: ≥2 λ/W measurements with CV < 0.3
- **BEADING_TRANSIENT**: ≥2 λ/W measurements with CV > 0.3
- **RADIAL_COLLAPSE**: <2 λ/W measurements or pure radial collapse
- **TIMEOUT**: WALI time limit reached before fragmentation
- **FAILED**: Numerical error or crash

### λ/W Measurement Method
1. Load all HDF5 snapshots from simulation
2. Reconstruct global density from meshblocks
3. Compute column-averaged linear mass density along filament axis
4. Apply Gaussian smoothing (σ = 2 cells)
5. Detect peaks with adaptive prominence threshold
6. Measure spacings between consecutive peaks
7. Report median λ/W and std dev across all snapshots

---

## Statistical Analysis Plan

### Primary Analysis
For each campaign, fit the relevant relationship:
- **CTZM_PERP**: λ/W(f) = a × f + b (linear fit per β)
- **EOS_SENSITIVITY**: λ/W(γ) = constant (test for variance)
- **TURB_AMPLITUDE**: λ/W(ampl) = constant (test for variance)

### Secondary Analysis
- **R² goodness-of-fit**: Quantify how well linear model describes data
- **ANOVA**: Test for significant differences between parameter groups
- **Bootstrap confidence intervals**: Resample to estimate uncertainty

### Power Analysis
- All campaigns designed for 80–90% power to detect effect sizes of:
  - Δλ/W > 0.3 (EOS_SENSITIVITY)
  - Δλ/W > 0.4 (TURB_AMPLITUDE)
  - R² difference > 0.4 (CTZM_PERP smoothness test)

---

## Risk Assessment

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Ray cluster setup issues | Medium | High | Provide setup script; test before full run |
| Athena++ binary incompatibility | Low | High | Verify binary before launching |
| HDF5 storage overflow | Low | Medium | Automatic pruning; 8 GB cap |
| Wall-time limits exceeded | Medium | Medium | 4-hour limit; monitor and extend if needed |

### Scientific Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| All sims show radial collapse (CTZM_PERP) | Low | High | Would reveal major geometry dependence |
| No clear γ-dependence (EOS_SENSITIVITY) | Medium | Low | Negative result still valuable |
| Large amplitude effects (TURB_AMPLITUDE) | Low | High | Would invalidate current extrapolation |

---

## Timeline and Milestones

### Phase 1: Setup (Day 1)
- [ ] Install Ray cluster dependencies
- [ ] Configure Athena++ binary path
- [ ] Test single simulation end-to-end
- [ ] Verify HDF5 analysis pipeline

### Phase 2: Execution (Days 2–4)
- [ ] CTZM_PERP: ~12 hours
- [ ] EOS_SENSITIVITY: ~6 hours
- [ ] TURB_AMPLITUDE: ~8 hours

### Phase 3: Analysis (Day 5)
- [ ] Run analyse_campaign.py on each campaign
- [ ] Generate all figures and statistics
- [ ] Verify results quality

### Phase 4: Packaging (Day 5)
- [ ] Package results into transfer format
- [ ] Generate summary report
- [ ] Transfer to local machine

---

## Contact and Support

**Campaign Designer**: Claude (ASTRA System)
**Date**: 2026-05-13
**Version**: 1.0

For technical issues with Ray cluster setup or Athena++ execution, consult:
- Ray documentation: https://docs.ray.io/
- Athena++ user guide: Available in Athena++ distribution

For scientific questions about test design, refer to the main paper and referee response documents.

