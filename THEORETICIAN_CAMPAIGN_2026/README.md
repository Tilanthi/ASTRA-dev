# THEORETICIAN CAMPAIGN 2026

## Executive Summary

This campaign addresses two critical theoretical problems identified by peer review:

1. **Perpendicular-Field Crisis**: λ/W ≈ 1.25 for perpendicular fields (90% of HGBS filaments per Planck) vs observed λ/W ≈ 2.17
2. **Supercritical Extrapolation**: Current λ/W ≈ 3.70 prediction is entirely extrapolated from f ≤ 1.3, while HGBS filaments have f ≈ 1.5-3.0

## Campaign Design

### Campaign A: Mixed Field Geometry (280 simulations)

**Purpose**: Quantify λ/W vs θ to determine what field geometry reproduces observations

**Parameter Space**:
- θ ∈ {0°, 15°, 30°, 45°, 60°, 75°, 90°} (magnetic field angle)
- f ∈ {1.0, 1.5, 2.0, 2.5} (mass-to-critical ratio)
- β ∈ {0.3, 1.0} (plasma beta)
- Seeds: {42, 137, 251, 367, 499}

**Domain**: L = 16λJ, Nx = 512×64×64

**Expected Outcome**: 
- Quantitative mixing model: λ/W(θ) = A·cosⁿ(θ) + B·sinⁿ(θ)
- Determine θ_mix such that λ/W(θ_mix) = 2.17 (observed)
- Test whether HGBS filaments require mixed field geometries

### Campaign B: Supercritical Extension (180 simulations)

**Purpose**: Direct λ/W measurements in supercritical regime (f ≥ 1.5)

**Parameter Space**:
- f ∈ {1.3, 1.5, 1.8, 2.0, 2.5, 3.0}
- β ∈ {0.3, 1.0, 3.0}
- θ = 0° (longitudinal field)
- Seeds: {42, 137, 251, 367, 499}

**Domain**: L = 24λJ, Nx = 768×64×64 (extended longitudinal domain)

**Expected Outcome**:
- Direct λ/W(f) measurements for f ≥ 1.3
- Test smoothness of λ/W(f) across near-critical → supercritical transition
- Revised λ_frag calibration without extrapolation

### Campaign C: Perpendicular Extended (10 simulations)

**Purpose**: Domain size convergence test for perpendicular-field result

**Parameter Space**:
- f ∈ {1.0, 1.5, 2.0}
- L ∈ {12, 16, 20, 24}λJ
- θ = 90° (perpendicular field)
- Seeds: {42, 137, 251}

**Domain**: Nx = 512×64×64

**Expected Outcome**:
- Verify λ/W ≈ 1.25 is robust to domain size changes
- Test if longer domains recover different fragmentation

## Ray Execution

**System Requirements**:
- 220 CPUs total
- 13 concurrent simulations × 16 cores = 208 active cores
- ~10,000 CPU-hours total
- ~50 hours wall time

**Execution**:
```bash
cd THEORETICIAN_CAMPAIGN_2026
python run_campaign.py
```

**Monitoring**:
- Ray dashboard: http://localhost:8265
- Progress: Check `theoretician_campaign_2026_results.json`

## Analysis Protocol

### 1. Mixed Field Modeling

Fit model: λ/W(θ) = A·cosⁿ(θ) + B·sinⁿ(θ)

Where:
- A = λ/W(θ=0°) = longitudinal value
- B = λ/W(θ=90°) = perpendicular value
- n = geometry coupling exponent

**Key Question**: What θ_mix gives λ/W = 2.17?

### 2. Supercritical Calibration

Fit models to λ/W(f):
- Power law: λ/W = a·fᵇ
- Exponential: λ/W = a·exp(b·f) + c
- Broken power law: transition at f ≈ 1.2

**Key Question**: Does λ/W(f) remain smooth for f > 1.3?

### 3. Quantitative Predictions

**For HGBS filaments (observed λ/W ≈ 2.17)**:
- If pure longitudinal (θ = 0°): requires f ≈ [value from Campaign B]
- If pure perpendicular (θ = 90°): cannot explain (λ/W = 1.25 << 2.17)
- If mixed geometry: requires θ ≈ [value from Campaign A]

**Revised theoretical calibration**:
- Replace extrapolated λ/W ≈ 3.70 with measured values from Campaign B
- Provide uncertainty estimates for supercritical regime

## Expected Deliverables

1. **lambda_W_vs_theta.png**: Mixed field geometry curve
2. **lambda_W_vs_f_supercritical.png**: Supercritical calibration curve  
3. **mixing_model_parameters.json**: Best-fit mixing model
4. **supercritical_calibration.json**: Revised λ_frag calibration
5. **field_geometry_analysis.pdf**: 4-page scientific summary
6. **theoretician_campaign_summary.json**: Complete results summary

## Success Criteria

- **Crisis 1 Resolved**: Quantitative answer to "what field geometry explains observations?"
- **Crisis 2 Resolved**: Direct λ/W measurements for f ≥ 1.5, no extrapolation needed
- **Paper Ready**: Results can be directly integrated into manuscript revision

## Timeline

- Day 1-2: Campaign A execution (~22 hours)
- Day 3-4: Campaign B execution (~16 hours)
- Day 4-5: Campaign C execution (~6 hours)
- Day 5-6: Analysis and plot generation
- Day 7: Summary report and paper integration

**Total**: ~7 days from start to publication-ready results
