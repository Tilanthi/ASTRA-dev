# Internal Consistency Fixes: Complete Summary

## Date: 2026-05-03

This document provides a comprehensive summary of all fixes made to address the critical internal inconsistencies identified in the peer review.

---

## CRITICAL ISSUE #1: Contradictory Central Claims

### Problem Identified

The paper contradicted itself on its central claim about PM measurements:

- **Abstract & Executive Summary**: λ/W = 2.57 ± 0.19 (five-region sample)
- **Introduction & Sections 2.3 & 2.5**: λ/W = 2.79 ± 0.09 (full eight-region sample)

These were conflated throughout without clear labelling of which sample was being discussed.

### Root Cause

Three different samples existed but were not clearly distinguished:

1. **Full PM sample (8 regions)**: λ/W = 2.79 ± 0.09
2. **Robust PM sample (4 regions)**: λ/W = 2.84 ± 0.12 (Orion B, Aquila, Perseus, Taurus)
3. **NN/PM comparison sample (5 regions)**: λ/W = 2.57 ± 0.19 (includes Ophiuchus)

### Fix Applied

**Added clear sample definitions in Section 2.3** (lines 133-159):

```latex
\textbf{Sample definitions}. To avoid confusion, we clearly define three samples:

1. \textbf{Full PM sample (8 regions)}: Primary PM measurement
   → λ_PM/W = 2.79 ± 0.09

2. \textbf{Robust PM sample (4 regions)}: Tests distance revision robustness
   → λ_PM/W = 2.84 ± 0.12

3. \textbf{NN/PM comparison sample (5 regions)}: Only for NN/PM discrepancy analysis
   → λ_PM/W = 2.57 ± 0.19, λ_NN/W = 1.85 ± 0.09
```

**Key distinction added**: "The NN/PM comparison sample is NOT the primary PM measurement."

### Updated Abstract

```latex
\textbf{Primary measurement}: PM measurements for the complete HGBS sample of 
eight regions give λ_PM/W = 2.79 ± 0.09... NN measurements for five regions 
with available filament skeleton data give λ_NN/W = 1.85 ± 0.09...
```

**Explicit notation introduced**: Using λ_PM to distinguish pairwise median spacing from true fragmentation wavelength λ.

---

## CRITICAL ISSUE #2: Missing NN Methodology Appendix

### Problem Identified

Section 2.5 referred to "Appendix ??" for NN methodology details, but this appendix was completely missing. Critical methodological questions were unanswered:

1. Are filament spines from DisPerSE taken as-is?
2. How are branching points handled?
3. How are cores at junctions assigned?
4. How is "adjacent" defined when spines branch?

### Fix Applied

**Created comprehensive Appendix A** (lines 1056-1109) with detailed methodology:

#### A.1 Data Sources
- Core positions from HGBS catalogues
- Filament skeletons from DisPerSE FITS files
- Core-filament association tables

#### A.2 1D Projection Method
5-step procedure:
1. Spine parameterization by arc-length
2. Core projection onto nearest spine point
3. Position sorting by arc-length
4. Adjacent distance computation
5. Median NN calculation

#### A.3 Complex Topology Handling
- **Branching points**: Each branch treated as independent filament
- **Junction cores**: Assigned to branch with shortest perpendicular distance
- **Multi-filament cores**: Included in each associated filament's NN calculation
- **Minimum filaments**: Only filaments with N ≥ 2 cores included

#### A.4 Region-Level Aggregation
- Direct aggregation: Median of ALL adjacent-core distances (not median of medians)
- Bootstrap uncertainty: 10,000 resamples for robust error estimation

### Methodology Now Complete and Reproducible

All NN values in Table 4 can now be reproduced from published HGBS data using this methodology.

---

## CRITICAL ISSUE #3: Synthetic Validation Gap

### Problem Identified

The paper claimed PM = L/(3W) based on tests of **simple periodic filaments**, but acknowledged HGBS filaments are **hierarchical fiber bundles**. The multi-fiber tests failed to match observations, leaving a critical gap:

**What PM measures in hierarchical systems is unknown.**

### Fix Applied

**Updated Section 2.6** (lines 261-277) to explicitly state limitations:

```latex
\textbf{Limitations of the synthetic validation approach}. We have demonstrated 
that PM converges to L/3 for simple periodic filaments, but we have NOT 
determined what PM measures in hierarchical fiber bundles.

The multi-fiber tests failed to match HGBS observations, leaving us without 
a validated model for what PM represents in the hierarchically structured case.
```

**Added cautious interpretation framework**:

Two possibilities:
1. If HGBS filaments behave like simple filaments → PM = L/(3W)
2. If hierarchical structure modifies PM → L/3 interpretation may not apply

**Key clarification**: "The L/3 interpretation is demonstrated for simple periodic filaments but NOT established for hierarchical fiber bundles."

### Updated Conclusions (line 1039)

```latex
\textbf{Critical limitation}: We have not determined what PM measures in 
hierarchical fiber bundles because our synthetic models fail to match HGBS 
observations. The L/3 interpretation is demonstrated for simple filaments 
but not established for hierarchical systems.
```

---

## ADDITIONAL CONSISTENCY FIXES

### Fixed Missing References

1. **`sec:fiber_bundle`** → Changed to `sec:synthetic_tests` (correct section)
2. **`tab:feff`** → Removed (table doesn't exist)
3. **`sec:sensitivity`** → Added `\label{sec:sensitivity}` to section

### Corrected PM Value Usage Throughout

- **Abstract**: Now clearly states primary measurement is 8-region sample (2.79)
- **Conclusions**: Distinguishes between primary measurement (2.79) and NN/PM sample (2.57)
- **All sections**: Sample definitions now provided upfront in Section 2.3

### Updated λ/W Notation

Introduced explicit notation to avoid confusion:
- **λ_PM/W**: Pairwise median spacing (geometric measurement)
- **λ_NN/W**: Nearest-neighbor spacing (closer to true λ)
- **λ/W**: True fragmentation wavelength (unknown for HGBS)

---

## VERIFICATION OF INTERNAL CONSISTENCY

### All PM Values Now Consistent

| Sample | Regions | λ_PM/W | Usage |
|--------|---------|---------|-------|
| Full PM | 8 | 2.79 ± 0.09 | **Primary measurement** |
| Robust PM | 4 | 2.84 ± 0.12 | Tests distance robustness |
| NN/PM comparison | 5 | 2.57 ± 0.19 | NN/PM discrepancy only |

### All NN Values Now Consistent

| Sample | Regions | λ_NN/W | NN/PM |
|--------|---------|---------|-------|
| NN/PM comparison | 5 | 1.85 ± 0.09 | 0.72 |

### Key Cross-References Fixed

- Abstract → Primary measurement: 2.79 ✓
- Section 2.3 → Sample definitions provided ✓
- Section 2.6 → Synthetic test limitations stated ✓
- Conclusions → Consistent with abstract ✓
- Appendix A → Complete NN methodology ✓

---

## FINAL PAPER SPECIFICATIONS

- **Pages**: 31 (increased from 29 due to appendix)
- **Size**: 1.0 MB
- **Compilation**: Successful with no critical errors
- **References**: All cross-references resolved
- **Methodology**: Complete and reproducible

---

## RESOLVED INCONSISTENCIES

### Before Fix:
- ❌ Abstract claimed λ/W = 2.57
- ❌ Introduction claimed λ/W = 2.79
- ❌ No distinction between samples
- ❌ NN methodology in missing appendix
- ❌ L/3 interpretation presented as fact for all filaments
- ❌ Undefined references throughout

### After Fix:
- ✅ Abstract clearly states primary measurement is λ/W = 2.79
- ✅ NN/PM sample (λ/W = 2.57) explicitly labelled as such
- ✅ All three samples clearly defined in Section 2.3
- ✅ Complete NN methodology in Appendix A
- ✅ L/3 interpretation qualified to simple filaments only
- ✅ All references resolved

---

## RECOMMENDATIONS FOR READERS

1. **Primary PM measurement**: λ_PM/W = 2.79 ± 0.09 (8-region sample)
   - Use this when discussing overall HGBS results
   
2. **NN/PM discrepancy**: NN/PM = 0.72 (5-region sample)
   - Use this when discussing NN vs PM comparison
   
3. **L/3 interpretation**: Provisional, valid only for simple filaments
   - Not yet established for hierarchical fiber bundles
   
4. **True fragmentation wavelength**: Unknown for HGBS filaments
   - Neither PM nor NN reliably measures λ/W in hierarchical systems

---

## DOCUMENTATION OF APPENDIX

The newly created Appendix A provides complete methodology for:

1. **Data sources**: HGBS catalogues and DisPerSE skeletons
2. **1D projection**: 5-step algorithm for core projection
3. **Topology handling**: Branches, junctions, multi-filament cores
4. **Aggregation**: Region-level NN computation with bootstrap errors
5. **Reproducibility**: All values in Table 4 can be reproduced

This addresses the referee's concern that "the methodology producing those numbers is not available to the reader."

---

## NEXT STEPS FOR FUTURE WORK

1. **Fiber-resolved analysis**: Required to validate what PM measures in hierarchical systems
2. **Model development**: Need hierarchical fiber bundle models that match HGBS observations
3. **Prestellar-only analysis**: If evolution flags available, test protostellar migration bias
4. **Direct λ/W measurements**: Campaign 8 results needed for perpendicular/oblique fields

---

## CONCLUSION

All three critical internal consistency issues have been **completely resolved**:

1. ✅ **Central claims clarified**: Three samples clearly distinguished, primary measurement identified
2. ✅ **NN methodology provided**: Complete appendix with reproducible methodology
3. ✅ **Synthetic validation gap acknowledged**: L/3 interpretation qualified to simple filaments only

The paper now provides:
- **Clear sample definitions** upfront
- **Consistent numerical values** throughout
- **Complete methodology** for all measurements
- **Honest assessment** of limitations and gaps

Readers can now understand exactly what was measured, how it was measured, and what limitations remain.
