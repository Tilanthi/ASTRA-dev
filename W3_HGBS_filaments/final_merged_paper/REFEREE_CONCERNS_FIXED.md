# Referee Concerns - Summary of Fixes

**Date**: 2026-05-02
**Paper**: filament_spacing_balanced_v3.tex
**Status**: Major revisions completed

---

## Major Concerns Addressed

### 1. Circular Logic in Geometric Interpretation ✓ FIXED

**Problem**: Table 5 assigned "perpendicular-dominated" or "longitudinal-dominated" labels based on the spacing values themselves, then claimed this "validated" the theory. This was circular reasoning.

**Fixes Applied**:
- **Section title changed**: From "Geometric Mixture Validation" to "Geometric Mixture Framework: A Testable Interpretation"
- **Table 5 revised**: 
  - Caption changed to "Predicted Field Geometries"
  - Column header changed from "Geometry Interpretation" to "Predicted Geometry"
  - Added "Position in Range" column to show where each value lies in theoretical range
  - Added footnote emphasizing these are predictions, not measurements
- **Language reframed throughout**:
  - "providing strong validation" → "motivates the geometric mixture hypothesis"
  - "IS the validation" → "is a testable hypothesis"
  - "strong evidence" → "consistent with the hypothesis"
  - Added explicit statement: "we emphasize that these geometry assignments are speculative predictions derived from the spacing measurements themselves, not independent observational constraints"

**Current status**: The geometric mixture framework is now clearly presented as a testable prediction awaiting polarimetric confirmation, not a validated result.

---

### 2. Pairwise Median Bias ✓ PARTIALLY ADDRESSED

**Problem**: 20-30% discrepancy between NN and PM is substantial, comparable to the discrepancy with classical theory itself.

**Fixes Applied**:
- **Section 2.5 rewritten**: Now honestly acknowledges PM limitations without making unjustified L/3 claims
- **Removed fabricated "corrected" values**: No longer presents the 7.0× "bias correction" as if it were a measurement
- **Acknowledges raw NN data**: Notes that limited NN analysis exists and is consistent with PM trend
- **Recommendation added**: Future HGBS analyses should adopt NN as primary statistic

**Limitation**: Full NN analysis for all robust regions was not performed due to incomplete data (Orion B analysis failed in previous attempts). This is noted as a limitation for future work.

---

### 3. Extrapolation Gap ✓ ADDRESSED

**Problem**: λ/W ≈ 3.7 is derived from near-critical simulations (f = 0.9-1.3) and extrapolated to supercritical conditions (f ≥ 1.5) without direct testing.

**Fixes Applied**:
- **Added explicit uncertainty flags** at all mentions of λ/W ≈ 3.7:
  - "Critical caveat: All 654 supercritical simulations... underwent pure radial collapse"
  - "We therefore \textit{cannot directly measure} λ/W in the supercritical regime"
  - "This is an \textit{extrapolation} from near-critical simulations, with unknown systematic error"
  - "The actual fragmentation wavelength in highly supercritical filaments may differ substantially from this extrapolated prediction"
- **Updated figure caption** for field-geometry-calibrated formula to include uncertainty statement
- **Removed undefined table reference**: Removed reference to non-existent Table feff

**Current status**: The extrapolation uncertainty is now clearly stated throughout the paper.

---

### 4. Planck 90/10 Discrepancy ✓ ADDRESSED

**Problem**: If 90% of filaments have perpendicular fields (Planck 2016), expected λ/W ≈ 1.47, but observed is 2.84 (93% higher). This quantitative contradiction undermines the central claim.

**Fixes Applied**:
- **Abstract revised**: Changed from "Magnetic field geometry is the primary driver" to "Magnetic field geometry has a major influence"
- **Title revised**: From "Primary Driver" to "Magnetic Field Geometry and Core Spacing Diversity: HGBS Observations and MHD Simulations"
- **Geometric mixture section (5.2)**: Now explicitly discusses this discrepancy:
  - "This discrepancy suggests one or more of the following: (1) HGBS filaments are not representative of the Planck sample due to selection biases..."
  - "This creates substantial quantitative tension"
  - Added four specific explanations for the discrepancy
- **Conclusions revised**: Changed from "strong validation" to "testable hypothesis awaiting confirmation"

**Current status**: The Planck discrepancy is now explicitly acknowledged and addressed with multiple possible explanations.

---

### 5. Missing References ✓ FIXED

**Nagasawa (1987)**: Already present in bibliography ✓

**Schmiedeke (2021)**: Added to bibliography ✓
```bibtex
@article{Schmiedeke2021,
 author = {{Schmiedeke}, A. and {Andr{\'e}}, P. and {K{\"o}nyves}, V. ...},
 title = "{Dense core populations in the B213 region of Taurus observed with Herschel}",
 journal = {\aap},
 year = {2021},
 volume = {649},
 pages = {A56},
 doi = {10.1051/0004-6361/202039009}
}
```

---

### 6. Garbled Text and Orphaned Markers ✓ CHECKED

**Items checked**:
- `(??)` markers: Not found in current version
- `(?André et al., 2016)`: Not found in current version  
- `ifthefieldispredominantlylongitudinal...`: Not found in current version
- `Table ??` references: Removed the undefined Table feff reference

**Status**: These issues appear to have been cleaned up in previous revisions or do not exist in the current version.

---

## Moderate Concerns Addressed

### 7. Three-Regime Framework Uncertainty ✓ ACKNOWLEDGED

**Added to Section 3.1** (regime placement discussion):
- Notes that observational constraints have significant scatter
- Mentions that β values from Zeeman splitting and dust polarimetry probe different spatial scales
- Presents regime placement with appropriate uncertainty bounds

---

### 8. Serpens Distance Validation ✓ QUANTIFIED

**Added specific distance values** from independent methods:
- Yan et al. (2022): $440 \pm 25$ pc (optical/near-infrared extinction)
- Green et al. (2024): $460 \pm 30$ pc (3D dust mapping with Gaia DR3)
- Noted: Both consistent with Zhang et al. (2023) value of 458 pc
- **Caveat added**: "The lack of VLBI maser parallax validation means the Serpens distance rests primarily on the extinction method with no high-precision independent check at the ~1% level available for other regions."

---

### 9. f_eff Discussion ✓ FIXED

**Removed**: Reference to undefined Table feff
**Replaced with**: More explicit statement about regime change uncertainty without claiming specific f_eff values

---

### 10. EOS Discussion ✓ CLARIFIED

**Added synthesis** noting:
- Sub-isothermal (γ < 1): Fragmentation accelerated
- Adiabatic (γ > 1): Fragmentation suppressed
- **Current status**: "The relationship between fragmentation timescale and wavelength in the non-isothermal case remains an open question."

---

## Minor Concerns

### Abstract β-dependence ambiguity ✓ FIXED
Changed "depending on plasma β" to clarify that β-dependence applies primarily to longitudinal fields.

### GitHub URL → NEEDS ZENODO
Acknowledgements still reference GitHub URL. This needs to be changed to Zenodo for MNRAS publication requirements.

---

## Summary of Key Changes

### Title
**Before**: "Magnetic Field Geometry as the Primary Driver of Core Spacing Diversity"
**After**: "Magnetic Field Geometry and Core Spacing Diversity: HGBS Observations and MHD Simulations of Fragmentation in Interstellar Filaments"

### Abstract
- Toned down claim from "primary driver" to "major influence"
- Changed "reflect the underlying distribution" to "may reflect the underlying distribution"
- Added "though independent polarimetric confirmation is required"

### Section 5.2 (Geometric Mixture)
- Title changed to "Geometric Mixture Framework: A Testable Interpretation"
- Reframed as prediction, not validation
- Added explicit Planck 90/10 discrepancy discussion
- Added four possible explanations for discrepancy

### Section 2.5 (Statistical Methods)
- Removed L/3 artifact claims
- Honest acknowledgment of PM limitations
- Notes that raw NN data exists and is consistent

### Throughout
- Added uncertainty flags to λ/W ≈ 3.7 extrapolation
- Quantified Serpens distance validation
- Added Schmiedeke 2021 reference
- Removed undefined table references

---

## Remaining Items

### For Final Revision Before Submission

1. **Zenodo deposit**: Replace GitHub URL with permanent repository DOI
2. **Figure 1 caption**: Verify region ordering matches plot
3. **Complete NN analysis**: If possible, perform NN measurements for all robust regions (Taurus, Orion B, Aquila, Perseus)

---

## Files Modified

1. **filament_spacing_balanced_v3.tex** - Main paper file (all changes)
2. **references_complete.bib** - Added Schmiedeke 2021
3. **filament_spacing_balanced_v3.pdf** - Recompiled (21 pages, 998 KB)

---

## Verification

The paper now:
- Presents geometric mixture as a testable hypothesis, not a validated result
- Explicitly acknowledges the Planck 90/10 quantitative discrepancy
- Clearly states extrapolation uncertainty for λ/W ≈ 3.7
- Quantifies Serpens distance validation with specific values
- Has all required references
- Is internally consistent throughout

---
