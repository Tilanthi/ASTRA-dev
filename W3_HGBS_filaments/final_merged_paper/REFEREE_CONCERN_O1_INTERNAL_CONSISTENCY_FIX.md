# Peer Review Concern O1: Internal Inconsistency in Primary Result - FIXED

## Date: 2026-05-01

## Referee Statement

> "The abstract, introduction, and conclusions present contradictory primary results, and the manuscript does not cleanly resolve which statistic is authoritative.
>
> The Introduction (Section 3, p.3) states: 'our primary measurement' is the global sky-plane NN spacing λ/W = 1.19 ± 0.04 for robust regions. Section 2.3 reinforces this. Yet the abstract opens with λ/W = 2.05 ± 0.05 (filament-constrained NN) as the primary result, and the Conclusions also foreground this value. These two numbers differ by a factor of 1.72×. The paper cannot have two simultaneous primary results that differ by nearly a factor of two."

## Root Cause

The paper had evolved through multiple revision cycles without fully reconciling the internal hierarchy of results:
- **Abstract** correctly foregrounded filament-constrained NN (λ/W = 2.05) as primary
- **Introduction** incorrectly foregrounded global NN (λ/W = 1.19) as primary
- **Section 2.3** incorrectly identified global NN as "primary measurement"
- **Jackknife discussion** incorrectly identified global NN as "primary observational result"
- **L/3 section** incorrectly stated "we adopt nearest-neighbor spacing as the primary fragmentation wavelength statistic"

## Solution Implemented

**Filament-constrained NN (λ/W = 2.05 ± 0.05) is now consistently identified as the primary result throughout the paper.**

Global sky-plane NN (λ/W = 1.19) and pairwise median (λ/W = 2.84) are now clearly identified as secondary/historical measurements retained for comparison with previous HGBS analyses.

---

## All Changes Made

### 1. Introduction (Line 68)
**BEFORE:**
> "In this paper, we report direct nearest-neighbor (adjacent-core) spacing measurements for all 8 HGBS regions... we find a weighted mean spacing of λ_NN = 0.119 ± 0.004 pc, corresponding to λ/W = 1.19 ± 0.04."

**AFTER:**
> "In this paper, we report **filament-constrained nearest-neighbor (NN) spacing**---the true along-filament fragmentation wavelength---by associating cores with filament skeletons... we find a weighted mean filament-constrained NN spacing of λ_fil = 0.205 ± 0.005 pc (λ/W = 2.05 ± 0.05). For historical comparison with previous HGBS analyses, we also report global sky-plane NN measurements... λ/W = 1.19 ± 0.04 (robust regions) or 1.24 ± 0.03 (full sample)."

**Key change:** Filament-constrained NN foregrounded as primary; global NN demoted to historical comparison.

---

### 2. Section 2.3 Results (Line 143)
**BEFORE:**
> "Primary result: Nearest-neighbor spacing (robust regions). We report direct nearest-neighbor (adjacent-core) spacing measurements... This result is our primary measurement and represents the first comprehensive HGBS analysis using an unbiased spacing statistic."

**AFTER:**
> "Global sky-plane NN measurements (for historical comparison). We report direct nearest-neighbor (adjacent-core) spacing measurements... These global sky-plane NN measurements are biased low by cross-filament associations (see Section 2.6) and are reported here for historical comparison with previous HGBS analyses. The **primary result** of this paper is the filament-constrained NN spacing (Section 2.6), which provides the true along-filament fragmentation wavelength."

**Key change:** Section heading changed from "Primary result" to "Global sky-plane NN measurements"; filament-constrained NN identified as primary.

---

### 3. Jackknife Verification (Line 159)
**BEFORE:**
> "However, our primary observational result is the NN spacing (λ/W = 1.24 ± 0.03 full sample, 1.19 ± 0.04 robust regions), which has smaller uncertainties and no L/3 convergence artifact."

**AFTER:**
> "However, the **primary observational result** of this paper is the filament-constrained NN spacing (λ/W = 2.05 ± 0.05 for robust regions; Section 2.6), which provides the true along-filament fragmentation wavelength by eliminating cross-filament bias. The global NN values reported here are useful for historical comparison but are biased low by cross-filament associations (bias factor 1.72×)."

**Key change:** Filament-constrained NN identified as primary; global NN demoted to historical comparison.

---

### 4. L/3 Convergence Section (Line 229)
**BEFORE:**
> "Primary result: Nearest-neighbor spacing. Following the recommendation above, we adopt nearest-neighbor spacing as the primary fragmentation wavelength statistic throughout this paper."

**AFTER:**
> "Global NN measurements and comparison with pairwise median. Following the recommendation above, we report global sky-plane nearest-neighbor spacing measurements throughout this paper for comparison with the historical HGBS literature... However, **the primary result** of this paper is the filament-constrained NN spacing (Section 2.6), which provides the true along-filament fragmentation wavelength by eliminating cross-filament bias."

**Key change:** Section heading changed from "Primary result" to "Global NN measurements and comparison"; filament-constrained NN identified as primary.

---

### 5. Serpens Exclusion Impact (Line 181)
**BEFORE:**
> "More importantly, the robust-only result (λ/W = 2.84) is our primary measurement, and it differs from the full sample by only 1.8%."

**AFTER:**
> "For the primary result of this paper (filament-constrained NN spacing; Section 2.6), Serpens was excluded from the robust sample due to skeleton extraction issues (it was extracted as a single continuous filament), so the primary result is already independent of the Serpens distance."

**Key change:** Removed incorrect statement that pairwise median (λ/W = 2.84) is the primary measurement.

---

### 6. Future Work Priorities (Line 880)
**BEFORE:**
> "Future work priorities are: (1) Filament-constrained nearest-neighbor spacing analysis for all HGBS regions..."

**AFTER:**
> "Future work priorities: (1) Explaining the significant regional variation in filament-constrained spacing (λ/W ranges from 1.73 to 3.06, σ = 0.51)..."

**Key change:** Removed filament-constrained analysis from future work (already completed) and added new priorities based on completed results.

---

## Consistent Hierarchy Established

### Primary Result
**Filament-constrained NN spacing**: λ/W = 2.05 ± 0.05 (all 4 robust regions)
- Provides the **true along-filament fragmentation wavelength**
- Eliminates cross-filament bias
- Based on 2,574 spacings from 3,032 cores across 458 filaments
- Identified as "primary result", "primary measurement", "definitive measurement" throughout paper

### Secondary Results (Historical Comparison)
**Global sky-plane NN spacing**: λ/W = 1.19 ± 0.04 (robust regions)
- Biased low by cross-filament associations (1.72×)
- Retained for historical comparison with previous HGBS analyses
- Identified as "for historical comparison", "useful for historical comparison"

**Pairwise median spacing**: λ/W = 2.84 ± 0.12 (robust regions)
- Biased high by L/3 convergence artifact (1.39×)
- Retained for historical comparison with HGBS literature
- Identified as "for historical comparison with the HGBS literature"

---

## Verification

### Before Fix (Inconsistent)
- Abstract: λ/W = 2.05 (filament-constrained) as primary ✓
- Introduction: λ/W = 1.19 (global NN) as primary ✗
- Section 2.3: λ/W = 1.19 (global NN) as primary ✗
- Conclusions: λ/W = 2.05 (filament-constrained) as primary ✓

### After Fix (Consistent)
- Abstract: λ/W = 2.05 (filament-constrained) as primary ✓
- Introduction: λ/W = 2.05 (filament-constrained) as primary ✓
- Section 2.3: λ/W = 2.05 (filament-constrained) as primary ✓
- Jackknife: λ/W = 2.05 (filament-constrained) as primary ✓
- L/3 section: λ/W = 2.05 (filament-constrained) as primary ✓
- Conclusions: λ/W = 2.05 (filament-constrained) as primary ✓

**All sections now agree on the primary result.**

---

## Scientific Justification

**Why is filament-constrained NN the primary result?**

1. **Eliminates cross-filament bias**: Global NN includes associations between cores on different filaments, which underestimates the true along-filament spacing by 1.72×

2. **True physical measurement**: Filament-constrained NN measures the distance between adjacent cores **on the same filament**, which is the actual fragmentation wavelength set by physics

3. **Larger sample size**: 2,574 spacings from 3,032 cores across 458 filaments (vs. 848 spacings in previous 2-region analysis)

4. **Robust statistics**: Uncertainty of ±0.05 (compared to ±0.13 in previous 2-region analysis)

5. **Definitive measurement**: Provides the first unbiased measurement of the true along-filament fragmentation wavelength for all 4 robust HGBS regions

---

## Files Modified

- `filament_spacing_streamlined_mnras.tex` (6 sections updated)
- `filament_spacing_streamlined_mnras.pdf` (recompiled, 29 pages, 1.20 MB)

---

## Summary

The internal inconsistency has been **fully resolved**. The paper now consistently identifies **filament-constrained NN spacing (λ/W = 2.05 ± 0.05)** as the primary result throughout:

- ✓ Abstract
- ✓ Introduction
- ✓ Section 2.3 (Results)
- ✓ Section 2.5 (Jackknife verification)
- ✓ Section 2.5 (L/3 convergence)
- ✓ Section 2.6 (Filament-constrained analysis)
- ✓ Conclusions

Global NN (λ/W = 1.19) and pairwise median (λ/W = 2.84) are now clearly demoted to **secondary/historical measurements** retained for comparison with previous HGBS analyses.

The referee's concern has been **completely addressed**. The paper no longer has two simultaneous primary results that differ by a factor of 1.72×.

---

## Date Completed: 2026-05-01

PDF compiled successfully. All sections verified for consistency.
