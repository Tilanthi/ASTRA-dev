# Expanded Referee Response Campaign — May 2026

**Date**: 2026-05-13
**Total Simulations**: 204 (3 sub-campaigns)
**Expected Runtime**: ~26 hours on 220 vCPU

## Overview

This expanded campaign addresses three specific referee concerns from the latest review:

| Sub-Campaign | Sims | Referee Concern | Objective |
|--------------|------|-----------------|-----------|
| **CTZM_PERP** | 96 | B2 | Test if smooth λ/W(f) evolution holds for perpendicular fields |
| **EOS_SENSITIVITY** | 48 | B3 | Measure λ/W for non-isothermal EOS (γ≠1) |
| **TURB_AMPLITUDE** | 60 | B5 | Test λ/W stability from linear to supersonic turbulence |

## Sub-Campaign Details

### 1. CTZM_PERP: Perpendicular-Field Transition Zone (96 sims)

**Addresses Referee Concern B2**: Perpendicular-field result creates unresolved tension (λ/W ≈ 1.25 vs observed 2.8)

**Parameter Space**:
- f = [1.2, 1.3, 1.4, 1.5]
- β = [0.3, 0.5, 1.0, 2.0]
- M = [1.0, 2.0]
- seeds = [0, 1, 2]
- θ = 90° (perpendicular to filament axis)

**Key Question**: Does the smooth λ/W(f) evolution observed in longitudinal CTZM also hold for perpendicular fields?

**Impact**:
- If YES: Extrapolation validation is geometry-independent, significantly strengthening the paper
- If NO: Reveals fundamental difference in fragmentation physics between field geometries

---

### 2. EOS_SENSITIVITY: Non-Isothermal EOS Effects (48 sims)

**Addresses Referee Concern B3**: EOS sensitivity testing is incomplete — λ/W implications for γ≠1 remain unknown

**Parameter Space**:
- f = [1.0, 1.1, 1.2] (near-critical regime where λ/W is measurable)
- γ = [0.7, 0.8, 0.9, 1.0]
- β = 1.0 (fixed to reduce parameter space)
- M = 1.0
- seeds = [0, 1, 2, 3]

**Key Question**: Does the fragmentation wavelength λ/W depend on the adiabatic index γ?

**Current Gap**: Paper acknowledges that γ affects t_frag but claims "isothermal predictions are therefore conservative" for λ/W. However, λ/W was never measured for γ≠1, making this claim untested.

**Impact**:
- Establishes whether non-isothermal effects modify the fragmentation scale
- Critical for real molecular clouds where γ ≈ 0.7-0.95 due to radiative cooling

---

### 3. TURB_AMPLITUDE: Turbulence Amplitude Scaling (60 sims)

**Addresses Referee Concern B5**: Turbulence amplitude extrapolation to supersonic filaments is untested

**Parameter Space**:
- f = [1.0, 1.2]
- perturb_ampl = [10⁻⁴, 10⁻³, 10⁻², 10⁻¹, 1.0] (linear to fully supersonic)
- β = 1.0
- M = 1.0
- seeds = [0, 1, 2]

**Key Question**: Is λ/W independent of perturbation amplitude across the linear to supersonic regime?

**Current Gap**: All simulations use small perturbations (δv = M × cs × 10⁻⁴), but real filaments have supersonic turbulence with full amplitude. The paper assumes λ/W is amplitude-independent, but this has not been tested for supersonic conditions.

**Impact**:
- Validates or refutes the extrapolation from small-amplitude simulations to real supersonic filaments
- Addresses a critical assumption in comparing simulations to HGBS observations

---

## Campaign Structure

```
/data/ctzm_perp_runs/         # CTZM_PERP outputs
/data/eos_sensitivity_runs/   # EOS_SENSITIVITY outputs
/data/turb_amplitude_runs/    # TURB_AMPLITUDE outputs

Each directory will contain:
├── {campaign}_results.json    # Full per-sim results
└── stdout.txt                 # Per-simulation logs
```

## Running the Campaign

```bash
# On astra-climate (220 vCPU)
cd /path/to/ASTRA-dev/simulations/ctzm_perp_may2026
python3 ctzm_perp_runner.py
```

The runner will execute campaigns sequentially:
1. CTZM_PERP (96 sims, ~12 hours)
2. EOS_SENSITIVITY (48 sims, ~6 hours)
3. TURB_AMPLITUDE (60 sims, ~8 hours)

## Expected Deliverables

### For Each Sub-Campaign:
- **{campaign}_results.json**: Full per-sim results with λ/W measurements
- **Summary statistics**: Fragmentation rate, beading rate, mean λ/W by parameter
- **Figures**: λ/W vs primary parameter (f, γ, or ampl) with error bars

### Integration with Paper:

**If CTZM_PERP confirms smooth evolution**:
- Add to Section 3.2.1: "Smooth λ/W(f) evolution is geometry-independent"
- Strengthens extrapolation validation for perpendicular-field HGBS filaments (~90% of sample)

**If EOS_SENSITIVITY shows γ-dependence**:
- Update Section 5.1.1 with quantitative λ/W(γ) relationship
- Refine theoretical comparison to account for non-isothermal effects

**If TURB_AMPLITUDE confirms amplitude independence**:
- Add to Section 4.6.4: "λ/W stability demonstrated across linear to supersonic regime"
- Validates extrapolation to real turbulent filaments

## Referee Concern Mapping

| Concern | Addressed By | How |
|---------|--------------|-----|
| **B1**: Central negative result not foregrounded | N/A | Presentation issue — rewrite text only |
| **B2**: Perpendicular-field tension | CTZM_PERP | Tests smooth evolution for θ=90° |
| **B3**: EOS sensitivity gap | EOS_SENSITIVITY | Measures λ/W(γ) for γ≠1 |
| **B4**: Calibration validation | Existing CTZM | Already validated for longitudinal fields |
| **B5**: Turbulence amplitude | TURB_AMPLITUDE | Tests λ/W across perturbation amplitudes |

## Timeline and Priority

**High Priority** (addresses core scientific weaknesses):
1. **CTZM_PERP**: 96 sims, ~12 hours — Tests geometry dependence of smooth evolution

**Medium Priority** (addresses important but secondary gaps):
2. **TURB_AMPLITUDE**: 60 sims, ~8 hours — Validates supersonic extrapolation
3. **EOS_SENSITIVITY**: 48 sims, ~6 hours — Tests non-isothermal effects

## Contact

Campaign designed by: Claude (ASTRA System)
Date: 2026-05-13
Referee context: Addresses B2 (perpendicular tension), B3 (EOS gap), B5 (turbulence)
Total compute budget: 204 sims × ~7.5 min ≈ 26 hours on 220 vCPU
