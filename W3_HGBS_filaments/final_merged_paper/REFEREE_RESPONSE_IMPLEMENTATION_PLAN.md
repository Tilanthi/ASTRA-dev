# Referee Response Implementation Plan

**Date**: 2026-05-08
**Timeline**: Implement TODAY (May 8)

---

## Summary of Approach

Due to methodology inconsistencies between existing NN analyses, I will take the **honesty + transparency** approach rather than trying to reconcile different methodologies. This directly addresses the referee's Option B requirement.

---

## Changes Required

### 1. Title Revision (Mandatory)

**Current**: "Fragmentation of Interstellar Filaments: Complete HGBS Analysis and MHD Simulations"

**Change to**: "Fragmentation of Interstellar Filaments: HGBS Analysis with Filament-Projected NN Measurements"

**Rationale**: Remove "complete" which is misleading when NN only covers 2/8 regions

### 2. Abstract Revision (Mandatory)

**Current abstract opening**:
```
We analyse core spacing measurements along filaments in the Herschel Gould Belt Survey (HGBS), combined with self-gravitating MHD simulations. We report two complementary spacing measurements that provide different constraints on filament fragmentation. Filament-projected nearest-neighbor (NN) spacing for Orion B and Aquila gives λ/W = 1.67 (58% below the classical 4× prediction)...
```

**Change to**:
```
We analyse core spacing measurements along filaments in the Herschel Gould Belt Survey (HGBS), combined with self-gravitating MHD simulations. We report two complementary spacing measurements with different sensitivities to filament geometry. Filament-projected nearest-neighbor (NN) spacing for Orion B and Aquila (2/8 HGBS regions, 51% of cores) gives λ/W = 1.67 (58% below the classical 4× prediction), measuring along-filament spacings. Pairwise median (PM) spacing for all eight regions gives λ/W = 2.84 (30% below the classical prediction), incorporating multi-filament geometry. The relationship between these statistics and the true fragmentation wavelength remains uncertain due to projection effects and geometric complexity.
```

**Key changes**:
- Explicitly state "2/8 HGBS regions, 51% of cores"
- Remove claim that NN is "physically meaningful" or "unbiased"
- Add uncertainty language about relationship to true wavelength

### 3. Remove All "Unbiased" Claims (Mandatory)

**Find and replace throughout paper**:

- Remove: "NN is statistically unbiased" 
- Replace with: "NN is less sensitive to cross-filament contamination than PM"

- Remove: "NN provides an unbiased measurement of the true fragmentation wavelength"
- Replace with: "NN measures local filament structure along fiber spines"

- Remove: "NN should be used for testing theoretical predictions"
- Replace with: "NN provides complementary constraints for theoretical comparisons"

### 4. Add Forward Modelling Disclaimer (Mandatory)

**Add to Section 2.5 (Forward Modelling)** after the current results:

```latex
\textbf{Limitations of synthetic geometry.} Our forward modelling with 14,400 
synthetic multi-filament systems finds PM/NN ratios of 9--11, substantially 
larger than the observed PM/NN $\approx$ 1.45 in HGBS regions. This indicates 
that the synthetic geometries do not capture the relevant spatial structure of 
real filament networks. In particular, the synthetic systems assume random 
filament orientations in a 3D box, while HGBS filaments may be preferentially 
aligned or hierarchically structured. Consequently, the forward modelling 
demonstrates that NN is less sensitive to multi-filament geometry than PM, 
but cannot validate either statistic as a calibrated estimator of the true 
fragmentation wavelength. We report both NN and PM as complementary constraints 
with unknown relationship to the true fragmentation wavelength.
```

### 5. Update Conclusions (Mandatory)

**Current conclusions**:
```
NN provides an unbiased measurement of the true fragmentation wavelength...
```

**Change to**:
```latex
\textbf{Primary result}.} The NN analysis of Orion B and Aquila (2/8 regions,
51\% of cores) yields $\lambda_{\rm NN}/W = 1.67$, while the PM analysis of 
all eight regions yields $\lambda_{\rm PM}/W = 2.84$. Both measurements are 
substantially below the classical $4\times$ prediction. However, the relationship 
between these statistics and the true fragmentation wavelength remains uncertain 
due to: (1) projection effects of 3D filament networks onto 2D observations; 
(2) geometric complexity of multi-filament systems; and (3) inability of 
forward modelling to reproduce the observed PM/NN ratio (synthetic: 9--11 vs 
observed: 1.4--1.5). We report both measurements as complementary constraints,
with NN preferred for theoretical comparisons due to its direct measurement of 
along-filament structure, but acknowledge that neither has been quantitatively 
validated against the true fragmentation wavelength.
```

### 6. Add Future Work Statement (Mandatory)

**Add to Section 5 (Discussion)**:

```latex
\textbf{Future work: Complete NN analysis.} The current NN analysis is 
restricted to 2/8 HGBS regions due to skeleton data availability and 
methodological consistency requirements. Expanding the NN analysis to 
additional regions (especially Taurus and Perseus, which have excellent 
data quality and small distance uncertainties) would test the robustness 
of the NN measurement and reduce regional sampling uncertainty. This 
requires: (1) consistent application of the NN methodology across all 
regions; (2) validation of skeleton quality and threshold selection; 
and (3) careful error propagation. Until such a complete NN analysis is 
available, the PM measurement (covering all 8 regions) should be used 
for literature comparisons, while the NN measurement (covering 2 regions) 
should be interpreted as a preliminary constraint on filament fragmentation.
```

---

## Implementation Steps (TODAY)

### Step 1: Update Title (5 minutes)
```bash
# Edit filament_spacing_streamlined_mnras.tex
# Change title to remove "Complete"
```

### Step 2: Update Abstract (15 minutes)
- Add "2/8 regions, 51% of cores" qualifier
- Add uncertainty language
- Remove "unbiased" claims
- Add forward modelling disclaimer

### Step 3: Global Find/Replace (10 minutes)
Remove all instances of:
- "unbiased"
- "validated"
- "physically meaningful quantity"

Replace with more cautious language.

### Step 4: Add Disclaimer Paragraphs (20 minutes)
- Add to Section 2.5 (forward modelling limitations)
- Add to Section 5 (future work statement)
- Update conclusions with uncertainty acknowledgment

### Step 5: Recompile PDF (5 minutes)
```bash
pdflatex filament_spacing_streamlined_mnras.tex
bibtex filament_spacing_streamlined_mnras
pdflatex filament_spacing_streamlined_mnras.tex
pdflatex filament_spacing_streamlined_mnras.tex
```

### Step 6: Verification (10 minutes)
- Check title change
- Check abstract qualifiers
- Verify "unbiased" removed
- Check disclaimers added
- Verify conclusions updated

---

## Expected Referee Response

With these changes, the referee should see that:

1. **Coverage limitation acknowledged**: Title and abstract clearly state 2/8 regions
2. **Calibration uncertainty acknowledged**: Forward modelling failure explicitly discussed
3. **No overclaiming**: "Unbiased" language removed throughout
4. **Transparent about limitations**: Future work statement added

This addresses the referee's Option B requirement: "revise the title and abstract to accurately reflect that the NN result is based on 2/8 regions, with quantified representativeness uncertainty included prominently."

---

## Risk Assessment

**Risk**: Referee may still request 4-region NN analysis

**Mitigation**: The honest acknowledgment of limitations may satisfy the referee, especially if:
- We explain that methodology consistency is important
- We provide a clear path forward (future work statement)
- We don't overclaim the significance of the 2-region result

**Alternative**: If referee insists on 4-region analysis, we have existing data (JSON file) that can be referenced with appropriate caveats about methodology differences.

---

## Success Criteria

The referee will be satisfied if:
1. ✅ Title no longer says "Complete"
2. ✅ Abstract states "2/8 regions" prominently
3. ✅ No claims of "unbiased" calibration
4. ✅ Forward modelling failure acknowledged
5. ✅ Relationship to true wavelength stated as "uncertain"
6. ✅ Future work path clearly defined

---

## Next Actions

**Immediate (next hour)**:
1. Update title in LaTeX file
2. Update abstract with all qualifiers
3. Global find/replace for "unbiased"

**This afternoon**:
4. Add disclaimer paragraphs
5. Update conclusions
6. Recompile PDF
7. Final review

**Decision point**: After reviewing changes, decide whether to submit or do additional work.

---

**Bottom line**: This approach addresses the referee's concerns through honesty and transparency, avoiding the need for time-consuming new analysis that might introduce more inconsistencies.
