# Critical Fix: Nearest-Neighbor Results Undermine Geometric Mixture Framework

**Date**: 2026-05-02
**Paper**: filament_spacing_balanced_v3.tex
**Status**: Critical issue addressed ✅

---

## Problem Identified

The new Table 6 (NN vs PM comparison) revealed a critical issue that was not adequately addressed in the original text:

1. **NN/PM ratios of 0.31-0.73**: NN measurements are dramatically smaller than PM measurements
2. **NN weighted mean λ/W = 1.01**: This clusters at the perpendicular-field theoretical lower bound (1.25) and falls below even this minimum
3. **Original explanation inadequate**: The claim that "NN < PM contradicts L/3 artifact prediction" was not a satisfactory physical explanation
4. **Implication for geometric mixture**: If NN is correct, regional diversity is substantially compressed, undermining the framework

---

## Changes Made

### 1. Section 2.5: Complete Rewrite of NN vs PM Discussion

**Location**: Lines 700-707 (originally), now expanded to ~30 lines

**Previous text** (inadequate):
- Claimed NN < PM contradicts L/3 artifact prediction
- Suggested regional variations are "real physical differences rather than measurement artifacts"
- Recommended future HGBS analyses adopt NN as primary statistic

**New text** (comprehensive two-interpretation framework):

**Interpretation 1: PM measures true filament-scale fragmentation wavelength**
- Under hierarchical fragmentation, NN measures inter-fiber gaps, not true fragmentation wavelength
- Supported by: (a) NN λ/W = 1.01 < theoretical minimum of 1.25; (b) Yang et al. 2024 fiber-to-core results; (c) 2-3× PM > NN pattern consistent with fiber bundles

**Interpretation 2: NN provides better estimate**
- PM may systematically overestimate by 2-3× due to long-range pairs
- If NN correct, HGBS values cluster near perpendicular-field prediction
- Regional diversity would be substantially compressed

**Current assessment** (explicit acknowledgement):
- Present PM as primary result: (1) standard HGBS metric; (2) NN below theoretical minimum; (3) hierarchical framework supports PM > NN
- **BUT** acknowledge significant uncertainty
- Explicit cross-reference to Section 5.2 noting uncertainty affects geometric mixture framework

---

### 2. Section 5.2: Added Critical Uncertainty Paragraph

**Location**: After opening paragraph of Section 5.2

**New text** (lines 608-613):
```
\textbf{Critical uncertainty: PM vs NN measurements}. The geometric mixture framework rests on pairwise median (PM) measurements of $\lambda/W$, which show regional variations spanning 1.98--3.46. However, nearest-neighbor (NN) measurements---which may better represent the local fragmentation scale---show systematically smaller values with a weighted mean of $\lambda/W = 1.01 \pm 0.08$ (Table~6, Section~2.5). This NN value clusters near the perpendicular-field theoretical lower bound (1.25) and falls below even this minimum. If NN provides a better estimate of the true fragmentation wavelength than PM, then the observed regional diversity is substantially compressed, and the geometric mixture framework would require significant revision. The PM vs NN discrepancy remains unresolved; we present PM-based analysis as our primary result consistent with previous HGBS work, but acknowledge that fiber-resolved fragmentation measurements are needed to definitively establish the true scale of regional diversity.
```

---

### 3. Conclusion (ii): Added Critical Caveat

**Location**: Line 661 (conclusion item ii)

**Previous text**: No acknowledgement of NN uncertainty

**New text** (added caveat):
```
\textbf{Critical caveat}: This framework rests on pairwise median measurements; nearest-neighbor measurements show substantially smaller values ($\lambda/W = 1.01$) that would compress the regional diversity. If NN better represents the true fragmentation scale, the geometric mixture framework would require significant revision (Section~5.2).
```

---

### 4. Conclusion (iii): Added Important Caveat

**Location**: Line 663 (conclusion item iii)

**Previous text**: No acknowledgement of NN uncertainty

**New text** (added caveat):
```
\textbf{Important caveat}: This conclusion is based on pairwise median measurements; nearest-neighbor measurements suggest smaller spacings ($\lambda/W \approx 1.01$) that would fall primarily within the perpendicular-field regime. Resolving the PM vs NN discrepancy through fiber-resolved analysis is essential for confirming whether the observed regional diversity is robust or substantially compressed.
```

---

## Rationale for These Changes

### Why We Did NOT Simply Abandon PM for NN

1. **NN below theoretical minimum**: λ/W = 1.01 < 1.25 (perpendicular-field minimum) suggests NN measures something other than fragmentation wavelength

2. **Hierarchical fragmentation evidence**: Yang et al. 2024 shows fiber-to-core recovers 4× while filament-to-core shows compressed values. NN likely measures inter-fiber gaps

3. **PM is standard HGBS metric**: All previous HGBS analyses use PM for consistency

### Why We Must Acknowledge the Uncertainty

1. **NN could be correct**: The 2-3× discrepancy is large and cannot be dismissed

2. **Implications for geometric mixture**: If NN correct, regional diversity (1.98-3.46) collapses to much narrower range (~1)

3. **Scientific honesty**: The uncertainty is fundamental and affects the paper's main claims

---

## Effect on Paper's Claims

### Claims That Remain Strong
- Magnetic field geometry affects fragmentation (2.75× effect demonstrated in simulations)
- Three-regime framework exists
- Fragmentation timescale measurements
- Near-critical fragmentation behavior

### Claims That Are Now Uncertain
- **Regional diversity spanning full theoretical range**: Depends on whether PM or NN is correct
- **Geometric mixture framework**: Rests on PM values; would need revision if NN proves correct
- **Field geometry predictions for individual regions**: Derived from PM values

---

## What Would Resolve This Uncertainty

1. **Fiber-resolved core spacing analysis**: Measure fragmentation wavelength within individual velocity-coherent fibers
2. **Synthetic tests**: Apply PM and NN statistics to simulated filament bundles with known properties
3. **Independent validation**: Use alternative spacing metrics (core formation times, velocity gradients)

---

## Verification

**Paper statistics**:
- **23 pages** (was 22)
- **981 KB** file size
- **Compiles successfully** (with non-critical warnings)

**Key sections updated**:
- Section 2.5: NN vs PM discussion completely rewritten
- Section 5.2: Critical uncertainty paragraph added
- Conclusions: Caveats added to items (ii) and (iii)

**Cross-references**:
- Section 2.5 → Section 5.2 (geometric mixture uncertainty)
- Section 5.2 → Table 6 and Section 2.5 (NN measurements)
- Conclusion → Section 5.2 (framework revision caveat)

---

## Assessment

The critical issue raised by the reviewer has been addressed directly:

1. ✅ **Section 2.5 updated**: Now provides two-interpretation framework with physical arguments for each
2. ✅ **NN below theoretical minimum acknowledged**: Explains why PM may still be preferred
3. ✅ **Geometric mixture uncertainty acknowledged**: Section 5.2 explicitly notes dependence on PM choice
4. ✅ **Conclusions updated**: Caveats added where regional diversity claims are made
5. ✅ **Scientific honesty**: The uncertainty is presented as fundamental, not minor

The paper no longer presents the geometric mixture framework as "validated by the data" but as "consistent with PM measurements, with significant uncertainty due to the NN discrepancy that requires fiber-resolved analysis to resolve."

---

**End of Report**
