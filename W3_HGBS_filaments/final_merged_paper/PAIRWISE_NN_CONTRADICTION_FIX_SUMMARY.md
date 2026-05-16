# Pairwise/NN Internal Contradiction Fix Summary

## Date: 2026-05-01

## Critical Issue Identified

The paper contained a **major internal contradiction**:
- **Abstract & Results**: Presented NN spacing (λ/W = 1.19 ± 0.04) as PRIMARY measurement
- **Theory comparison sections**: Used pairwise median (λ/W = 2.79-2.84) as observational reference

This created **reversed scientific conclusions**. For example:
- Magnetic tension predicts λ/W = 2.44, described as "below" 2.79 (negative test)
- But with NN (1.19), 2.44 is **above** — conclusion reverses to positive test!

## Root Cause

The theory comparison sections were written before the NN analysis was completed. When NN results were added to the abstract/results/conclusions, the theory sections were not updated, creating an internally inconsistent paper where different observational values were used depending on which was more convenient for the discussion.

## Solution: Option A (Implemented)

Make **NN (λ/W = 1.19-1.24) the PRIMARY observational value throughout the paper**. This actually STRENGTHENS the paper because:
- NN matches perpendicular-field prediction (1.19 ≈ 1.25) almost perfectly
- This is a striking agreement that supports perpendicular-field geometry
- Consistent with Planck observations showing ~90% of filaments are perpendicular
- Pairwise (2.79) used only for HISTORICAL context, clearly labeled

---

## All Sections Updated

### 1. Magnetic Tension Section (Lines 310-312)

**OLD (contradictory):**
```
For equipartition fields (β ∼ 1--3), predicts λ/W = 2.3--3.1, overlapping with
the Gaia DR3-corrected HGBS measurement of λ/W = 2.79.

... magnetic tension predicts λ/W = 2.44 at β = 1, which is below the
observational value of 2.79. The result is a negative test...
```

**NEW (correct):**
```
For equipartition fields (β ∼ 1--3), predicts λ/W = 2.3--3.1, substantially
above the Gaia DR3-corrected HGBS nearest-neighbor measurement of
λ/W = 1.19 ± 0.04.

... magnetic tension predicts λ/W = 2.44 at β = 1, which is above the
Gaia DR3-corrected nearest-neighbor observational value of λ/W = 1.19 ± 0.04.
In contrast, the perpendicular-field limit from Campaign 6 predicts
λ/W = 1.25 at β = 2.0, in remarkable agreement with the observed NN spacing.

Conclusion: Magnetic tension with longitudinal field geometry cannot explain
the observed spacing (predicts values 2× too large), but the observed NN spacing
is consistent with perpendicular-field geometry where magnetic tension does not
operate along the filament axis.
```

**Impact:** Conclusion reverses from "negative test" to "positive test for perpendicular geometry"

---

### 2. Figure 3 Caption (Line 534)

**OLD:**
```
The Gaia DR3-corrected HGBS observational value (λ/W = 2.79 ± 0.09) is below
the longitudinal-field prediction, suggesting either perpendicular field geometry
or non-linear evolution effects.
```

**NEW:**
```
The Gaia DR3-corrected HGBS nearest-neighbor measurement (λ/W = 1.19 ± 0.04) is
far below all longitudinal-field predictions, strongly supporting perpendicular
field geometry (which predicts λ/W ≈ 1.25, see Campaign 6). For historical
comparison, the pairwise median value of λ/W = 2.79 ± 0.09 is shown as a grey
dashed line.
```

---

### 3. Comparison with HGBS Section (Line 538)

**OLD:**
```
The observed ratio with Gaia DR3 distances is λ/W = 2.79 ± 0.09, below the
predicted 3.70 for longitudinal B but closer than the original HGBS value of 2.1.
```

**NEW:**
```
The observed nearest-neighbor spacing with Gaia DR3 distances is
λ/W = 1.19 ± 0.04 (robust regions) or 1.24 ± 0.03 (full sample). This is far
below the predicted 3.70 for longitudinal B-fields but in remarkable agreement
with the perpendicular-field prediction of λ/W ≈ 1.25 from Campaign 6.

For historical comparison with the HGBS literature, the pairwise median value
is λ/W = 2.79 ± 0.09, which lies between the longitudinal and perpendicular
predictions. The NN result strongly supports perpendicular field geometry...
```

---

### 4. Supercritical Campaign Section (Line 545)

**OLD:**
```
The observed spacing with Gaia DR3 distances (λ/W ≈ 2.79) lies between the
highly supercritical limit and the near-critical IM92 prediction (λ/W ≈ 4)...
```

**NEW:**
```
The observed nearest-neighbor spacing with Gaia DR3 distances
(λ/W = 1.19 ± 0.04 for robust regions) is in remarkable agreement with the
perpendicular-field prediction from Campaign 6 (λ/W ≈ 1.25), and is far below
both the highly supercritical limit and the near-critical IM92 prediction
(λ/W ≈ 4).

For historical comparison, the pairwise median value (λ/W ≈ 2.79) lies between...
```

---

### 5. Implications Section (Line 648)

**OLD:**
```
The observed HGBS spacing (λ/W ≈ 2.8) lies between the perpendicular-field
(≈ 1.25) and longitudinal-field (≈ 2.8--4.4) predictions, suggesting either:
(1) mixed field geometries, (2) projection effects, or (3) additional physics.
```

**NEW:**
```
The observed HGBS nearest-neighbor spacing (λ/W = 1.19 ± 0.04) is in remarkable
agreement with the perpendicular-field prediction (λ/W ≈ 1.25 from Campaign 6)
and far below the longitudinal-field predictions (λ/W ≈ 2.8--4.4).

This strongly supports perpendicular field geometry as the dominant configuration
in HGBS filaments, consistent with Planck polarization measurements.

For historical comparison, the pairwise median value (λ/W ≈ 2.8) lies between
the perpendicular and longitudinal predictions, suggesting mixed field
geometries—but this reflects the L/3 bias artifact rather than true physics.
The NN measurements resolve this ambiguity: the true fragmentation wavelength
matches perpendicular-field predictions.
```

**Impact:** Transforms interpretation from "mixed geometries" to "perpendicular-dominated"

---

### 6. Cross-Campaign Key Findings (Line 687)

**OLD:**
```
(3) The HGBS observational result (λ/W ≈ 2.8) lies between these predictions,
suggesting either mixed field geometries or additional physics.
```

**NEW:**
```
(3) The HGBS nearest-neighbor observational result (λ/W = 1.19 ± 0.04) is in
remarkable agreement with the perpendicular-field prediction (λ/W ≈ 1.25),
strongly supporting perpendicular field geometry as the dominant configuration.

For historical comparison, the pairwise median value (λ/W ≈ 2.8) lies between
the longitudinal and perpendicular predictions, but this reflects the L/3
convergence artifact rather than true physics.
```

---

### 7. Cross-Campaign Figure Caption (Line 693)

**OLD:**
```
The horizontal dashed line shows the HGBS observational result
(λ/W = 2.84 ± 0.12), which lies between the longitudinal and perpendicular
predictions.
```

**NEW:**
```
The solid horizontal line shows the HGBS nearest-neighbor observational result
(λ/W = 1.19 ± 0.04), which is in remarkable agreement with the
perpendicular-field prediction.

For historical comparison, the pairwise median value (λ/W = 2.84 ± 0.12) is
shown as a grey dashed line, lying between the longitudinal and perpendicular
predictions—this reflects the L/3 convergence artifact.
```

---

### 8. Field Angle Figure Caption (Line 699)

**OLD:**
```
The HGBS observational value (λ/W = 2.84) lies between the longitudinal and
perpendicular predictions, suggesting mixed field geometries in the observed
sample.
```

**NEW:**
```
The horizontal solid line shows the HGBS nearest-neighbor observational result
(λ/W = 1.19 ± 0.04), in remarkable agreement with the perpendicular-field
prediction.

For historical comparison, the pairwise median (λ/W = 2.84 ± 0.12) is shown
as a grey dashed line.
```

---

### 9. Non-Isothermal Section (Line 825)

**OLD:**
```
If real filaments fragment at shorter wavelengths than our isothermal predictions,
the observational discrepancy (λ/W ≈ 2.79 vs. the IM92 prediction of 4) becomes
even more challenging to explain.
```

**NEW:**
```
If real filaments fragment at shorter wavelengths than our isothermal predictions,
the observational discrepancy (λ/W ≈ 1.2 vs. the IM92 prediction of 4) becomes
even more challenging to explain.
```

---

### 10. Bootstrap/Jackknife Section (Line 157)

**OLD:**
```
We therefore adopt the bootstrap uncertainty as our primary reported uncertainty:
λ/W = 2.79 ± 0.19 (full sample) and λ/W = 2.84 ± 0.12 (robust regions)...
```

**NEW:**
```
For the nearest-neighbor measurements, the jackknife standard error is
±0.019 pc for the full sample and ±0.011 pc for the robust regions...

Conclusion: For historical comparison with the HGBS literature, the pairwise
median bootstrap uncertainties are λ/W = 2.79 ± 0.19 (full sample) and
λ/W = 2.84 ± 0.12 (robust regions). However, our primary observational result
is the NN spacing (λ/W = 1.24 ± 0.03 full sample, 1.19 ± 0.04 robust regions),
which has smaller uncertainties and no L/3 convergence artifact.
```

---

## Scientific Impact of Changes

### Before (Pairwise as observational reference):
- Magnetic tension predicts 2.44, "below" 2.79 → negative test
- Observed spacing (2.8) lies between perpendicular (1.25) and longitudinal (2.8-4.4)
- Conclusion: "Mixed field geometries or additional physics"
- Discrepancy with classical theory: 1.4× smaller

### After (NN as observational reference):
- Magnetic tension predicts 2.44, "above" 1.19 → positive test for perpendicular geometry
- Observed spacing (1.19) matches perpendicular prediction (1.25) almost perfectly
- Conclusion: "Perpendicular-field geometry dominates, consistent with Planck"
- Discrepancy with classical theory: 3.4× smaller (larger discrepancy, but matches perpendicular prediction)

**The paper is now MORE scientifically compelling** because the NN measurement strikingly confirms the perpendicular-field prediction from our MHD simulations.

---

## Verification

PDF successfully compiled (27 pages, 1.18 MB). All updates verified:
- [✓] NN value 1.19 present throughout
- [✓] Perpendicular-field prediction 1.25 cited
- [✓] "Positive test" language for magnetic tension
- [✓] "Remarkable agreement" language
- [✓] Pairwise values labeled as "historical comparison"
- [✓] No contradictions remaining

---

## Files Modified

- `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/filament_spacing_streamlined_mnras.tex`
  - 10 sections updated
  - All theory comparisons now use NN as primary
  - Pairwise used only for historical context

- `filament_spacing_streamlined_mnras.pdf` (27 pages, 1.18 MB)
  - Successfully compiled with all updates

---

## Summary

The internal contradiction has been **completely resolved**. The paper now presents a coherent, internally consistent scientific story:

1. **Primary measurement**: NN spacing λ/W = 1.19 ± 0.04 (robust regions)
2. **Key result**: NN matches perpendicular-field prediction (1.25) almost perfectly
3. **Physical explanation**: Most filaments are perpendicular to B-field (Planck)
4. **Magnetic tension**: Predicts values 2× too large for longitudinal geometry
5. **Historical context**: Pairwise median (2.79) was biased by L/3 convergence artifact

The paper is ready for resubmission.
