# Option A Implementation: NN as Primary Measurement

## Date: 2026-05-08

## Problem Resolved

The paper previously suffered from a fundamental inconsistency:
- **Claimed**: NN is the "physically meaningful fragmentation wavelength"
- **But used**: PM (λ/W = 2.84) as the primary result
- **Problem**: Having it both ways — scientifically inconsistent

## Solution Implemented: Option A

Restructured the paper to make **filament-projected NN the primary measurement** and **PM the legacy comparison statistic**.

---

## Changes Made

### 1. Abstract — Complete Restructure

**Before**: 
- Led with PM result (λ/W = 2.84)
- NN presented as supplementary "validation"

**After**:
- **Primary measurement**: λ/W = 2.29 ± 0.47 (NN for Orion B)
- **Legacy comparison**: λ/W = 2.84 (PM for 4 regions)
- **Clear distinction**: NN for testing theory, PM for literature comparison

**Key text**:
```
Our primary measurement uses filament-projected nearest-neighbor (NN) spacing 
statistics, which directly measure the distance between adjacent cores along filament 
spines—the physically meaningful fragmentation wavelength. For Orion B, 
λ_NN = 0.229 ± 0.047 pc, corresponding to λ/W = 2.29 ± 0.47. This value 
differs from the classical theoretical prediction of 4× by 43%, providing strong 
evidence for sub-Jeans filament fragmentation.

For comparison with previous HGBS studies, we also report PM-based measurements: 
λ_PM/W = 2.84 ± 0.12 (4-region weighted mean). The NN measurement should be 
used for testing theoretical predictions.
```

### 2. Section 2.3 (Results) — Complete Rewrite

**Before**:
- "Primary result: Continuous weighting scheme" (PM-based)
- NN mentioned as supplementary validation

**After**:
- **Primary result**: Filament-projected NN spacing for Orion B
- **Why NN is primary**: Directly measures fragmentation wavelength
- **PM for literature comparison**: Reported separately
- **Clear hierarchy**: NN → theory testing, PM → literature comparison

**Structure**:
1. NN as primary measurement (λ/W = 2.29 ± 0.47)
2. Why NN is primary (physical meaning, no L/3 artifact)
3. Limitations (188/1,844 cores, one region)
4. PM measurements for literature comparison (λ/W = 2.84)
5. PM vs NN comparison (27% difference, L/3 artifact)

### 3. Conclusions Section — Lead with NN

**Before**:
- First bullet: PM measurements with NN mentioned later
- Confused hierarchy

**After**:
- **First bullet**: "Primary result: Filament-projected NN spacing"
  - λ/W = 2.29 ± 0.47 for Orion B
  - 43% below classical 4× prediction
  - Should be used for testing theories
  
- **Second bullet**: "PM measurements for literature comparison"
  - λ/W = 2.84 (4-region weighted mean)
  - 27% larger than NN (L/3 artifact)
  - For HGBS literature comparison only

### 4. Executive Summary — Updated

**Changed**:
- Point (3) now references NN as primary
- Point (4) clarifies PM vs NN distinction
- Removed misleading "primary sample: λ/W = 2.84" reference

---

## Scientific Impact

| Aspect | Before | After |
|--------|--------|-------|
| **Primary measurement** | λ/W = 2.84 (PM) | **λ/W = 2.29 (NN)** |
| **Primary interpretation** | PM measures spacing scale | **NN measures true wavelength** |
| **Theory testing** | Used PM | **Use NN (physically meaningful)** |
| **Literature comparison** | Used PM (inconsistent) | **Use PM (appropriate)** |
| **Uncertainty acknowledged** | Vague | **Explicit: NN ± 0.47** |

---

## Key Numerical Changes

| Measurement | Value | Use |
|------------|-------|-----|
| **NN (Orion B)** | λ/W = 2.29 ± 0.47 | **Primary: Theory testing** |
| **PM (4 regions)** | λ/W = 2.84 ± 0.12 | **Legacy: Literature comparison** |
| **PM (Orion B)** | λ/W = 3.13 | Shows L/3 artifact |
| **NN vs PM difference** | NN is 27% smaller | Confirms L/3 convergence |

---

## What This Achieves

✅ **Resolves fundamental inconsistency**: No more "having it both ways"

✅ **Scientifically honest**: NN is primary because it's physically meaningful

✅ **Referee-friendly**: Clear hierarchy, no circular logic

✅ **Maintains core conclusion**: Both show sub-Jeans spacing

✅ **Proper uncertainty**: ±0.47 (20%) vs ±0.12 (4%) — reflects true limitations

✅ **Clear methodology**: NN → theory, PM → literature

---

## Limitations Acknowledged

1. **Single region**: NN measurement only for Orion B (not all 8 regions)
2. **Partial coverage**: 188/1,844 cores (10%) due to association thresholds
3. **Data access**: Comprehensive NN analysis requires raw HGBS skeleton data (not public)
4. **Future work needed**: NN measurements for all regions would be ideal

These limitations are **honestly stated** rather than hidden, making the science more transparent.

---

## Verbage: Clarified Language

**Removed confusing/hedged terms**:
- "Validation" (when NN ≠ PM)
- "Holistic assessment" (circular reasoning for Aquila)
- "Primary sample" (when PM shouldn't be primary)
- "Both give sub-Jeans" (without clarification of which to use)

**Added clear/honest language**:
- "Primary measurement" (NN only)
- "For literature comparison" (PM only)
- "Should be used for testing theoretical predictions" (NN)
- "Should not be used for testing theoretical predictions" (PM)
- "Physically meaningful fragmentation wavelength" (NN)
- "Overall scale of core distributions" (PM)

---

## Final Paper Status

- **PDF**: filament_spacing_streamlined_mnras.pdf
- **Pages**: 24
- **File size**: 1.0 MB
- **Compilation**: Successful (no critical errors)

---

## Summary

The paper now presents a **clear, consistent hierarchy**:
1. **NN measurement** (λ/W = 2.29 ± 0.47) → Primary result for theory testing
2. **PM measurement** (λ/W = 2.84) → Legacy comparison for HGBS literature

This resolves the fundamental inconsistency of claiming NN is "physically meaningful" while using PM as the primary result.

**The paper is now scientifically consistent and referee-ready.**
