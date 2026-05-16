# Comprehensive Fix Implementation Plan
## Peer Review Feedback - May 2026

### Overview
This plan addresses 9 critical issues identified in the latest manuscript version. All issues will be fixed before PDF regeneration.

---

## Issue 1: PM/NN Ratio Discrepancy Undermines Core Methodology [CRITICAL]

**Problem**: Factor of 6-8 discrepancy (forward model: 9-11, observations: 1.3-1.7) means the model fails catastrophically. Cannot simultaneously argue NN is better AND forward model validates it.

**Required Changes**:

1. **Abstract (line 25)** - Add explicit concession:
   - Current: "neither statistic has been quantitatively validated against the true fragmentation wavelength"
   - Change to: "The factor of 6-8 discrepancy means **neither PM nor NN can currently be interpreted as a calibrated fragmentation wavelength estimator**. We present an observational characterization of two complementary statistics whose theoretical interpretation awaits future forward modelling with realistic filament geometries."

2. **Introduction (line 58)** - Reframe NN novelty section:
   - Remove language claiming NN is "better" than PM
   - Emphasize NN provides complementary constraint, not superior measurement

3. **Conclusions (line 980)** - Add explicit statement:
   - "Given the forward model's factor of 6-8 discrepancy in reproducing the observed PM/NN ratio, **we cannot claim that NN provides a validated measurement of the true fragmentation wavelength**. Both statistics provide complementary constraints on filament fragmentation, but their theoretical interpretation remains uncertain."

4. **Remove any language claiming NN is validated or superior** throughout the paper

---

## Issue 2: Supercritical Regime Extrapolation Gap [CRITICAL]

**Problem**: Calibration from f ≈ 1.0-1.2, but HGBS filaments are f ≈ 1.5-3.0. Physical regime change at f ≈ 1.2-1.5 makes extrapolation uncertain.

**Required Changes**:

1. **Section 5.1 (Discussion)** - Add explicit flag:
   - "The comparison between simulation predictions and HGBS observations **rests on an unvalidated extrapolation** from the near-critical regime (f ≈ 1.0-1.2 where λ/W can be directly measured) to the supercritical regime (f ≈ 1.5-3.0 where HGBS filaments lie). Our simulations demonstrate a physical regime change at f ≈ 1.2-1.5 where radial collapse suppresses longitudinal beading, preventing direct measurement of λ/W in the observationally relevant supercritical regime."

2. **Table 9 (Systematic Uncertainty Budget)** - Increase extrapolation uncertainty:
   - Current: ±5%
   - Change to: ±15% (with note: "Large uncertainty due to regime transition at f ≈ 1.2-1.5")

3. **Abstract (line 25)** - Add disclaimer:
   - "The fragmentation wavelength calibration (λ_frag = 1.11 λ_MJ) comes from near-critical simulations (f ≈ 1.0-1.2) and **cannot be directly measured in the supercritical regime** (f ≳ 1.5) where radial collapse dominates."

---

## Issue 3: Formatting and Internal Consistency Issues [HIGH PRIORITY]

**Problem**: Text formatting breakdown, inconsistent table values, broken cross-references.

**Required Changes**:

1. **Section 3.1** - Find and fix continuous running text:
   ```bash
   # Search for the problem text
   grep -n "Caveat.*conclusion.*applies.*only.*near.*critical" filament_spacing_streamlined_mnras.tex
   ```
   - Fix spacing: "Caveat: This conclusion applies only to the near-critical regime where longitudinal beading occurs..."

2. **Table 2** - Fix "NN (3D-corrected)" value:
   - Current: ~2.1 (incorrect, matches 2D value)
   - Change to: ~2.8 (correct 3D-corrected value: 2.17 × 1.27 = 2.76)

3. **Section 4.9.3** - Fix broken cross-reference:
   ```bash
   grep -n "Table ??" filament_spacing_streamlined_mnras.tex
   ```
   - Replace with correct table reference (likely Table 6 or 7)

---

## Issue 4: Statistical Power of NN Sample [HIGH PRIORITY]

**Problem**: Only 4 regions, Orion B + Perseus = 68% of spacings. Leave-one-out shows 18% sensitivity. More fragile than PM (8 regions).

**Required Changes**:

1. **Abstract** - Add explicit statement:
   - "The NN measurement is based on only four HGBS regions (Orion B, Aquila, Taurus, Perseus), with Orion B and Perseus contributing 68% of all spacings. Leave-one-out analysis shows the weighted mean is sensitive to individual regions (±18% maximum change), indicating the NN result is more fragile than the PM result based on all eight regions."

2. **Conclusions (line 980)** - Add prominence:
   - Move NN statistical power limitation earlier in conclusions
   - Emphasize this is more fragile than PM measurement

---

## Issue 5: Projection Correction Applied Identically [MEDIUM PRIORITY]

**Problem**: 1.27 factor from Hacar et al. (2013) applied identically to PM and NN. But PM has cross-fiber distances, so projection correction is physically ill-defined.

**Required Changes**:

1. **Section 3.2 (3D projection correction)** - Add caution:
   - "The projection correction factor of 1.27 from Hacar et al. (2013) was derived for fiber-resolved core measurements along individual filaments. Applying this correction to PM is **physically ill-defined** because PM incorporates cross-fiber distances that are not purely along-filament spacings. The 3D-corrected PM value should therefore be treated with considerable caution."

2. **Abstract** - Remove or weaken claim about PM 3D-corrected overlapping classical:
   - Current: "while the 3D-corrected PM value (λ/W ≈ 3.5) is within 15% of classical"
   - Change to: "The 3D-corrected PM value (λ/W ≈ 3.5) should be treated with caution due to the ill-defined nature of projection corrections for cross-fiber distances."

---

## Issue 6: Magnetic Tension Geometric Challenge [MEDIUM PRIORITY]

**Problem**: Planck shows 90% of filaments perpendicular to field, Campaign 6 shows perpendicular fields give λ/W ≈ 1.25 — much shorter than observed. This essentially rules out perpendicular-field magnetic tension.

**Required Changes**:

1. **Discussion (Section 5.1)** - Add prominent subsection:
   - "\textbf{Perpendicular-field magnetic tension is ruled out}. The Campaign 6 result showing λ/W ≈ 1.25 for perpendicular fields, combined with the Planck finding that 90% of dense filaments are perpendicular to the mean field, creates a striking tension: **perpendicular-field magnetic tension cannot explain the observed HGBS spacing of λ/W ≈ 2.8**. This refocuses the theoretical question from 'why are observed spacings shorter than classical?' to 'why are observed spacings longer than perpendicular-field predictions?'"

2. **Abstract** - Give this more prominence:
   - Move earlier in abstract discussion of theoretical explanations

---

## Issue 7: Ambipolar Diffusion Timescale Estimate [LOW PRIORITY]

**Problem**: t_AD ~ 10-20 t_ff stated without derivation or citation.

**Required Changes**:

1. **Section 5.1.1** - Add derivation or citation:
   - Add: "For typical filament conditions (B ∼ 10--50 μG, n ∼ 10^4 cm^-3), dimensional analysis of the ambipolar diffusion timescale t_AD ∼ L^2/η_AD, where η_AD ∝ B^2/n is the ambipolar diffusivity, gives t_AD ∼ 10--20 t_ff following the formulation of \citet{Mouschovias1991}."

---

## Issue 8: Streamline Repetitive Limitations [LOW PRIORITY]

**Problem**: Executive Summary of Limitations + individual section discussions + conclusions all repeat the same material.

**Required Changes**:

1. **Move Executive Summary to later position**:
   - Move from Section 0 (before Introduction) to Section 5.3 (after main Discussion)
   - Rename to "Comprehensive Limitations Summary"
   - Keep content but reduce repetition elsewhere

2. **Abstract** - Keep concise, don't repeat all limitations

3. **Conclusions** - Focus on main findings, not exhaustive limitations list

---

## Issue 9: Additional Statistical Analysis [ENHANCEMENT]

**Problem**: Need to demonstrate robustness of statistical conclusions.

**Required Changes**:

1. **Create comprehensive statistical analysis script**:
   - Bootstrap confidence intervals for all summary statistics
   - Leave-one-out sensitivity for both PM and NN
   - Alternative robust statistics (median, trimmed mean)
   - Correlation analysis between PM/NN and filament properties

---

## Implementation Order (Priority Sequence):

### Phase 1: CRITICAL Issues (Must Fix First)
1. ✅ Issue 1: PM/NN discrepancy concession (abstract, intro, conclusions)
2. ✅ Issue 2: Supercritical extrapolation disclaimer (discussion, Table 9)
3. ✅ Issue 3: Formatting fixes (Section 3.1, Table 2, cross-refs)

### Phase 2: HIGH PRIORITY Issues
4. ✅ Issue 4: Statistical power prominence (abstract, conclusions)
5. ✅ Issue 5: Projection correction caution (Section 3.2, abstract)
6. ✅ Issue 6: Magnetic tension challenge (Discussion, abstract)

### Phase 3: MEDIUM/LOW PRIORITY Issues
7. ✅ Issue 7: Ambipolar diffusion derivation (Section 5.1.1)
8. ✅ Issue 8: Streamline limitations (move Executive Summary)
9. ✅ Issue 9: Enhanced statistical analysis (create script)

### Phase 4: Final Polish
10. ✅ Compile PDF with all changes
11. ✅ Verify all cross-references work
12. ✅ Final proofread for formatting issues

---

## Files to Modify:

1. **filament_spacing_streamlined_mnras.tex** (main paper)
   - Abstract (line ~25)
   - Introduction (line ~58)
   - Section 3.1 (formatting)
   - Section 3.2 (projection correction)
   - Section 4.9.3 (cross-reference)
   - Table 2 (NN 3D-corrected value)
   - Table 9 (systematic uncertainty)
   - Section 5.1 (Discussion)
   - Section 5.1.1 (ambipolar diffusion)
   - Conclusions (line ~980)

2. **New statistical analysis script** (comprehensive_analysis.py)
   - Bootstrap CIs
   - Leave-one-out
   - Alternative statistics
   - Correlations

---

## Success Criteria:

✅ Abstract explicitly concedes neither PM nor NN are calibrated estimators
✅ Supercritical extrapolation flagged as unvalidated throughout
✅ All formatting issues fixed (no running text, correct table values, working cross-refs)
✅ Statistical power limitations prominent in abstract/conclusions
✅ Projection correction for PM treated with appropriate caution
✅ Perpendicular-field magnetic tension ruled out explicitly
✅ Ambipolar diffusion estimate supported with derivation/citation
✅ Repetitive limitations streamlined (Executive Summary moved)
✅ Comprehensive statistical analysis completed
✅ PDF compiles without errors
✅ All cross-references verified working

---

## Estimated Time: 3-4 hours

Phase 1 (Critical): 90 minutes
Phase 2 (High Priority): 60 minutes
Phase 3 (Medium/Low): 60 minutes
Phase 4 (Final Polish): 30 minutes
