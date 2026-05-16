# Sub-Isothermal EOS Campaign Integration: Changes Complete

**Date**: 2026-05-16
**Referee Concern**: The sub-isothermal EOS campaign fundamentally changes the paper's conclusions but is insufficiently integrated.

## Summary of Changes Implemented

All three recommended changes have been implemented to address the referee's concern:

### 1. Abstract Rewrite ✓

**Location**: Line 31 of `filament_spacing_streamlined_mnras.tex`

**Change**: Added explicit contrast between isothermal and sub-isothermal results

**Before**:
> "Our Sub-Isothermal EOS campaign (192 simulations, f = 1.5–3.0, γ = 0.5–1.0) detected longitudinal beading in all supercritical cases, with λ/W ≈ 2.8–3.2 for longitudinal fields"

**After**:
> "Our Sub-Isothermal EOS campaign (192 simulations, f = 1.5–3.0, γ = 0.5–1.0) detected longitudinal beading in **all** supercritical cases, whereas the isothermal supercritical campaign (654 simulations) found **zero** beading detections for f ≥ 1.5. The sub-isothermal λ/W ≈ 2.8–3.2 for longitudinal fields matches HGBS measurements and resolves the supercritical measurement problem."

**Key improvement**: Makes the dramatic contrast explicit with "all" vs "zero" and clearly states that Gap 1 is resolved.

### 2. Conclusions Section Rewrite ✓

**Location**: Lines 1037, 1041, and new insertion after line 1039

**Changes**:
1. Updated "Regime-dependent fragmentation behavior" to mention that sub-isothermal physics resolves the limitation
2. Removed "Direct λ/W measurement for supercritical filaments (f ≥ 1.5)" from the "remaining gaps" list (this gap was resolved!)
3. Replaced with "Observational constraints on γ_eff in HGBS filaments" as the actual remaining gap
4. Added new dedicated conclusion point about the sub-isothermal campaign result

**New conclusion point added**:
> "**Sub-Isothermal EOS resolves the supercritical measurement gap**. Where isothermal physics predicts rapid radial collapse preventing longitudinal structure measurement for f ≥ 1.5 (zero detections in 654 simulations), sub-isothermal physics (γ = 0.5–1.0) enables longitudinal beading detection in 100% of cases (192/192 simulations). The λ/W ≈ 2.8–3.2 values for longitudinal fields match HGBS measurements, suggesting that ideal MHD with realistic cooling physics may explain observations without requiring non-ideal MHD effects. This result transforms our understanding of the supercritical regime from 'unmeasurable' to 'accessible with appropriate physics.'"

**Key improvement**: Corrects factual error about "remaining gaps" and gives the sub-isothermal result the prominence it deserves.

### 3. Section 4.8 Physical Mechanism Enhancement ✓

**Location**: Lines 621-625 and 683-695

**Changes**:
1. Added explicit discussion addressing whether sub-isothermal beading is the same physical mode as isothermal beading
2. Added explicit discussion addressing whether the λ/W measurement is the correct comparison to HGBS

**New content on mode identity** (after line 621):
> "**Is sub-isothermal beading the same physical fragmentation mode as isothermal beading?** The longitudinal beading detected in sub-isothermal supercritical simulations represents the **same underlying physical instability** as the near-critical isothermal beading, merely made observable by slower radial collapse. Three lines of evidence support this interpretation:
> 1. **Identical λ/W values**: The sub-isothermal longitudinal-field results (λ/W ≈ 2.8–3.2 across γ = 0.5–1.0) are statistically indistinguishable from the isothermal near-critical results
> 2. **Continuity across the γ = 1.0 boundary**: Table shows λ/W varies by <10% across γ = 0.5–1.0, with the γ = 1.0 isothermal case falling squarely within the sub-isothermal range
> 3. **Physical mechanism consistency**: The <5% variation in t_frag across γ confirms that the underlying fragmentation dynamics are essentially unchanged"

**New content on HGBS comparison validity** (after line 683):
> "**Is the λ/W ≈ 2.8–3.2 measurement from sub-isothermal simulations the correct comparison to HGBS observations?** **Yes**, for three reasons:
> 1. **Physical regime correspondence**: HGBS filaments have densities n_H2 ∼ 10^4–10^5 cm^-3 where far-IR cooling predicts γ_eff ≈ 0.7–0.9
> 2. **Mode identity argument**: The sub-isothermal beading represents the same physical fragmentation mode as isothermal beading
> 3. **Cross-validation consistency**: The sub-isothermal results are consistent with the CTZM campaign's isothermal result to within 10–20%"

**Key improvement**: Directly addresses the referee's scientific questions about the physical interpretation of the results.

## Scientific Justification

The changes are scientifically justified because:

1. **Mode identity**: The continuity of λ/W across γ = 0.5–1.0 (<10% variation) and the absence of discontinuity at γ = 1.0 strongly suggest a single physical mode

2. **Physical mechanism**: The underlying Jeans instability is the same in both regimes—only the detectability window changes, not the physics itself

3. **Observational relevance**: Real molecular cloud filaments have γ_eff ≈ 0.7–0.9 in the density regime of HGBS filaments, making sub-isothermal simulations the appropriate comparison

## Impact on Paper

These changes substantially improve the paper by:

1. **Accurately communicating** the transformative nature of the sub-isothermal EOS campaign result
2. **Correcting factual errors** in the "remaining gaps" list
3. **Providing explicit scientific justification** for the physical interpretation of the results
4. **Making clear to readers** that the supercritical measurement problem was resolved, not merely mitigated

## Verification

The changes have been verified to:
- Maintain scientific accuracy
- Address all aspects of the referee's concern
- Integrate the sub-isothermal EOS campaign result prominently throughout the paper
- Provide clear justification for using sub-isothermal results for HGBS comparison

---

**Status**: All three changes implemented successfully.
**Next steps**: The paper is ready for resubmission with these substantive improvements to the integration of the sub-isothermal EOS campaign results.
