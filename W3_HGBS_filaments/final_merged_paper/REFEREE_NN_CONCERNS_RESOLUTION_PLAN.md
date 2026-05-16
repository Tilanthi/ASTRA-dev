# Referee Response Plan: NN Measurement Issues

**Date**: 2026-05-08
**Status**: CRITICAL - Submission-blocking

---

## Executive Summary

The referee has identified two critical issues with the NN measurement:
1. **Coverage**: NN analysis covers only 2/8 regions (Orion B, Aquila), but paper claims "complete HGBS analysis"
2. **Calibration**: Forward modelling failed to validate NN as an unbiased estimator (PM/NN = 9-11 synthetic vs 1.4-1.5 observed)

**Key Insight**: We already have NN skeleton data for all regions in the HGBS_SOURCE_DATA directory, and `filament_constrained_nn_results_4regions.json` contains NN results for Taurus and Perseus. This is a fixable problem, not a fundamental limitation.

---

## Issue 1: NN Coverage (2/8 Regions)

### Current Problem
- Primary result λ/W = 1.67 from only Orion B + Aquila
- Title says "complete HGBS analysis" but NN covers only 25% of sample
- Three-scenario analysis ±13% uncertainty not fully propagated
- "Representative" claim based on circular reasoning (PM-NN difference consistency)

### Solution: Use Existing NN Data for Taurus and Perseus

**Data Available**:
- Taurus skeleton files: `HGBS_taurusL1495_skeleton_map_thresh50.fits`
- Perseus skeleton files: `HGBS_perseus_skeleton_map_thresh50.fits`
- Existing NN results: `filament_constrained_nn_results_4regions.json`

**Extracted Values** (from existing JSON):
```
Taurus:   NN λ/W = 1.73, 471 spacings, 485 cores (135 pc)
Perseus:  NN λ/W = 3.06, 606 spacings, 652 cores (296 pc)
Aquila:   NN λ/W = 2.05, 362 spacings, 487 cores (436 pc)
Orion B:  NN λ/W = 1.95, 1135 spacings, 1408 cores (386 pc)
```

**Wait - there's a discrepancy**:
- Paper reports Aquila NN λ/W = 1.49, Orion B NN λ/W = 1.84
- JSON reports Aquila NN λ/W = 2.05, Orion B NN λ/W = 1.95

This suggests different methodologies or thresholds. Need to verify which values are correct before using them.

### Required Actions

**Step 1: Verify NN Methodology Consistency**
1. Check if `filament_constrained_nn_results_4regions.json` uses same methodology as paper
2. If consistent, update paper with Taurus + Perseus values
3. If inconsistent, re-run NN analysis for all 4 regions using consistent methodology

**Step 2: Calculate Global NN Mean**
Using inverse-variance weighting (or simple core-weighted mean):
```
4-region NN mean = (1.73*485 + 3.06*652 + 2.05*487 + 1.95*1408) / (485+652+487+1408)
                = 2.17 (approximately)
```

**Step 3: Update Paper**
1. Replace 2-region NN result (1.67) with 4-region NN result (2.17)
2. Update all references to "2/8 regions" to "4/8 regions" 
3. Add disclaimer that 4 regions (Ophiuchus, Serpens, TMC1, CRA) lack NN analysis
4. Update title if necessary: "Complete HGBS Analysis" → "HGBS Analysis with Filament-Projected NN Measurements"

**Step 4: Title Decision**
- If 4/8 regions with NN: Can keep "Complete HGBS Analysis" if justified
- If want to be conservative: "Filament-Projected NN Analysis of HGBS Regions"
- Abstract should clearly state: "NN analysis of 4/8 regions"

---

## Issue 2: Forward Model Calibration Failure

### Current Problem
- Forward model: PM/NN = 9-11
- Observed: PM/NN = 1.4-1.5
- Factor of 6-8 discrepancy means model provides no useful constraint
- NN bias of -8.8% not negligible

### Root Cause Analysis

**Why does synthetic PM/NN = 9-11 but observed = 1.4-1.5?**

Looking at the forward model code (`forward_model_pm_nn_discrepancy_fixed.py`):
```python
# Single filament control: PM/NN = 8.98 ± 1.75
# Theoretical expectation: PM/NN = (L/3) / λ_true = (5.0/3) / 0.2 = 8.33
```

This is because in the synthetic model:
- PM converges to L/3 for a single filament (5.0/3 = 1.67 pc)
- NN measures λ_true = 0.2 pc
- So PM/NN = 1.67/0.2 = 8.35

But in real HGBS data:
- PM = 0.284 pc (λ/W = 2.84)
- NN = 0.167 pc (λ/W = 1.67) for Orion B + Aquila
- PM/NN = 0.284/0.167 = 1.70

**The fundamental issue**: In real filaments, PM does NOT converge to L/3 because:
1. Multi-filament geometry breaks the single-filament assumption
2. Real filaments have varying lengths, not uniform L = 5 pc
3. Core distributions are not uniform, they're clustered
4. Projection effects mix multiple filament systems

### Solution: Reframe Forward Modelling Results

**The forward modelling does NOT validate NN as unbiased. Instead:**

1. **What the forward model actually shows**:
   - For synthetic single filaments with uniform beading: PM/NN = 9-11
   - For real HGBS filaments: PM/NN = 1.4-1.5
   - This factor of 6-8 discrepancy proves real filaments are NOT single-filament systems

2. **What NN bias actually means**:
   - The -8.8% NN bias is relative to KNOWN synthetic λ_true
   - But we don't know λ_true for real filaments
   - So we can't use this bias to correct real NN measurements
   - The forward model does NOT provide useful calibration for real data

3. **Reframed interpretation**:
   - NN measures along-filament spacing, PM includes cross-filament distances
   - Forward modelling shows these statistics behave differently in synthetic vs real systems
   - Neither statistic is "validated" as measuring true fragmentation wavelength
   - Both provide complementary constraints with unknown relationship to λ_true

### Required Actions

**Step 1: Abstract Revision**
Change from:
```
We report two complementary spacing measurements. Filament-projected
NN spacing for Orion B and Aquila gives λ/W = 1.67...
```

To:
```
We report two complementary spacing measurements with different
sensitivities to filament geometry. Filament-projected NN analysis
of 4 HGBS regions gives λ/W = [4-region value], measuring along-filament
spacings. PM analysis of 8 regions gives λ/W = 2.84, incorporating
multi-filament geometry. The relationship between these statistics and
the true fragmentation wavelength remains uncertain due to projection
effects and geometric complexity.
```

**Step 2: Remove "Unbiased" Claims**
- Remove all references to NN being "statistically unbiased" or "validated"
- Replace with: "NN is less sensitive to cross-filament contamination than PM"
- Acknowledge that forward modelling cannot calibrate either statistic

**Step 3: Error Budget Update**
Add to systematic uncertainties:
```
Forward modelling constraint: Unable to validate NN/PM relationship
  to true fragmentation wavelength due to synthetic-real discrepancy
  (factor of 6-8 in PM/NN ratio).
```

**Step 4: Conclusions Revision**
Change from:
```
NN provides an unbiased measurement of the true fragmentation wavelength...
```

To:
```
NN and PM provide complementary constraints on filament fragmentation,
but neither has been quantitatively validated against the true fragmentation
wavelength due to the complexity of real filament geometries. Forward
modelling with 14,400 synthetic systems produces PM/NN ratios of 9-11,
while HGBS regions show 1.4-1.5, indicating that real filaments have
substantially different geometric structure than the synthetic model.
Both measurements should be reported, with NN preferred for theoretical
comparisons due to its direct measurement of along-filament structure.
```

---

## Implementation Plan

### Phase 1: Verify Existing NN Data (TODAY)
1. Check `filament_constrained_nn_results_4regions.json` methodology
2. Compare to paper's NN values for consistency
3. If inconsistent, identify cause (threshold? distance? method?)

### Phase 2: Expand NN Analysis (TODAY-TOMORROW)
**Option A: Use Existing 4-Region Results** (if methodology consistent)
1. Update paper with Taurus + Perseus NN values
2. Calculate 4-region weighted mean
3. Update all NN references throughout paper
4. Recompile PDF

**Option B: Re-run NN Analysis** (if methodology inconsistent)
1. Run NN analysis script on Taurus skeleton file
2. Run NN analysis script on Perseus skeleton file
3. Verify methodology matches Orion B/Aquila
4. Calculate 4-region weighted mean
5. Update paper

### Phase 3: Reframe Forward Modelling (TODAY)
1. Remove all "unbiased" claims
2. Add explicit statement about PM/NN discrepancy
3. Update abstract with uncertainty language
4. Update conclusions with calibration caveat

### Phase 4: Title Decision (TODAY)
Options:
- "Complete HGBS Analysis with Filament-Projected NN Measurements" (if 4/8 regions)
- "Filament-Projected NN Spacing Analysis of 4 HGBS Regions"
- "HGBS Filament Spacing: NN Analysis of 4 Regions and PM Analysis of 8 Regions"

### Phase 5: Final PDF (TODAY)
1. Compile updated paper
2. Verify all references consistent
3. Check error budget complete
4. Ready for submission

---

## Critical Decision Points

### Decision 1: Use Existing or Re-run NN Analysis?
**Check**: Does `filament_constrained_nn_results_4regions.json` use same methodology as paper?

**If yes**: Use existing values, update paper immediately
**If no**: Must re-run NN analysis for consistency

### Decision 2: What is the 4-Region NN Result?
**Calculate**: Core-weighted mean of 4 regions
- Taurus: 1.73 × 485 cores
- Perseus: 3.06 × 652 cores
- Aquila: 2.05 × 487 cores
- Orion B: 1.95 × 1408 cores

Need to determine if this is the right weighting scheme.

### Decision 3: Title After 4-Region NN?
- If 4/8 regions with NN: Can claim "NN analysis of majority of cores by mass/volume"
- Conservative: Be explicit about 4/8 coverage in title and abstract
- Avoid "complete" unless fully justified

---

## Success Criteria

The referee's concerns will be addressed if:

1. **Coverage**: NN analysis includes at least 4/8 regions (Orion B, Aquila, Taurus, Perseus)
   - This represents ~70% of cores by count
   - Abstract clearly states: "NN analysis of 4 HGBS regions"

2. **Calibration**: Abstract and conclusions acknowledge uncertainty
   - Remove "unbiased" language
   - State: "relationship between NN/PM and true λ remains uncertain"
   - Include forward modelling discrepancy (PM/NN = 9-11 vs 1.4-1.5)

3. **Transparency**: Error budget includes all identified uncertainties
   - Regional sampling: ±13% (or reduced with 4 regions)
   - NN methodology: ±5-10%
   - Forward modelling constraint: unable to validate

4. **Consistency**: All sections use same numbers and language
   - Abstract, results, conclusions all consistent
   - No overstated claims

---

## Timeline

**Today (May 8)**:
- Verify NN data consistency
- Calculate 4-region NN result
- Reframe forward modelling language
- Draft title options

**Tomorrow (May 9)**:
- Re-run NN analysis if needed
- Update all paper sections
- Compile final PDF
- Decision: Submit or additional revisions

**Total Time**: 1-2 days to complete

---

## Next Immediate Actions

1. **Check NN consistency**: Read `filament_constrained_nn_results_4regions.json` methodology section
2. **Calculate 4-region mean**: Determine correct weighting scheme
3. **Update abstract**: Reframe language with uncertainty acknowledgment
4. **Decide on title**: Choose most accurate descriptor

**The key insight**: This is fixable with existing data. The referee is asking for honest representation of what we've measured, not fundamental new work.
