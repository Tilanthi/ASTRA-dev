# L/3 Artifact Claim: Reassessment and Correction

**Date**: 2026-05-08
**Status**: ⚠️ REQUIRES CORRECTION

---

## Reviewer's Concern: Validated

The reviewer correctly identified that the L/3 artifact claim is based on limited testing and overstated. Comprehensive validation reveals:

### Empirical Results (from 16,800 simulations)

**PM vs L correlation in HGBS data**:
- R² = 0.595 (moderate but not conclusive with n=4)
- p-value = 0.127 (NOT statistically significant)
- PM increases with L (slope = 0.023 pc/pc) as expected from L/3 artifact
- BUT: small sample size (4 regions) limits statistical power

**PM/(L/3) ratios for HGBS regions**:
| Region | L (pc) | L/3 (pc) | PM (pc) | PM/(L/3) |
|--------|---------|---------|---------|----------|
| Taurus | 2.5 | 0.833 | 0.198 | **0.24** |
| Ophiuchus | 3.0 | 1.000 | 0.206 | **0.21** |
| Perseus | 4.0 | 1.333 | 0.248 | **0.19** |
| Aquila | 5.0 | 1.667 | 0.346 | **0.21** |
| Orion B | 8.0 | 2.667 | 0.313 | **0.12** |

**Critical finding**: If PM converged to L/3, we would expect PM/(L/3) ≈ 1.0 for all regions. Instead, values range from 0.12 to 0.24, clustering around ~0.20. **PM does NOT converge to L/3 in real HGBS data.**

---

### Simulation vs Reality Mismatch

**Predicted bias for Orion B parameters** (L = 8 pc, λ_true ≈ 0.18 pc):
- Simulation predicts: **994% bias** (PM → L/3)
- Empirically observed: **41% bias**

**Predicted bias for Aquila parameters** (L = 5 pc, λ_true ≈ 0.15 pc):
- Simulation predicts: **876% bias**
- Empirically observed: **57% bias**

**The 194% bias figure is misleading** because:
1. It applies to a specific synthetic case (λ_true = 0.20 pc, L = 2.0 pc)
2. Real HGBS filaments have different L values (5-10 pc)
3. Real HGBS filaments are complex multi-filament systems, not single beaded filaments
4. The synthetic model doesn't capture HGBS complexity

---

## Root Cause of Mismatch

The injection-recovery simulation assumes:
- **Single filament** with periodic beading
- **Uniform spacing** between beads
- **No sub-filament structure**
- **No fiber bundles**

Real HGBS filaments are:
- **Multi-filament systems** with complex geometry
- **Fiber bundles** with sub-structure
- **Variable beading** along filaments
- **Multiple orientations** in 3D space

The L/3 artifact may apply to simplified single-filament systems but does NOT fully capture the complexity of real HGBS measurements.

---

## Corrected Interpretation

### What the L/3 Artifact Actually Means

**For synthetic single-filament systems with uniform beading**:
- PM converges to L/3 for large N
- This can produce large upward biases (>100%)
- **BUT**: This is an idealized case that doesn't match HGBS complexity

**For real HGBS multi-filament systems**:
- PM does NOT simply converge to L/3
- Empirical PM/(L/3) ratios cluster around ~0.2
- Observed PM-NN differences (40-50%) are real but smaller
- The bias mechanism is more complex than simple L/3 convergence

### The 40-50% PM-NN Difference

**Real explanation**: PM and NN measure different things in complex multi-filament systems:
- **PM**: Measures all pairwise distances across ALL filaments and fibers
- **NN**: Measures adjacent-core spacings ALONG filament spines

In a fiber bundle:
- PM includes cross-fiber distances (large, unrelated to fragmentation)
- NN captures true along-fiber fragmentation spacing
- The 40-50% difference reflects geometric complexity, not simple L/3 artifact

---

## Required Paper Corrections

### 1. Abstract and Headline Changes

**REMOVE**:
- "194% upward bias" from abstract
- "PM converges to L/3" as definitive statement

**REPLACE WITH**:
- "For our synthetic test case, PM shows 194% bias (λ_true = 0.20 pc, L = 2.0 pc). However, real HGBS filaments have longer L (5-10 pc) and show PM/(L/3) ≈ 0.2, not 1.0. The 40-50% observed PM-NN difference reflects geometric complexity of multi-filament systems, not simple L/3 convergence."

### 2. Statistical Methods Section

**ADD**:
- Empirical PM vs L correlation analysis (R² = 0.60, p = 0.127)
- PM/(L/3) ratio table for all HGBS regions
- Caveat that L/3 artifact demonstrated for synthetic single-filament systems may not fully apply to complex multi-filament HGBS data

**REMOVE**:
- Definitive statements about PM converging to L/3 in real HGBS data
- The 194% figure as headline result

### 3. Revised L/3 Artifact Statement

**Current (incorrect)**:
> "Injection-recovery Monte Carlo simulations confirm that the pairwise median (PM) statistic suffers from an L/3 convergence artifact... PM shows 194% upward bias"

**Corrected**:
> "Injection-recovery Monte Carlo simulations demonstrate that for synthetic single-filament systems with uniform beading, PM converges toward L/3 and can show large upward biases (up to 194% for λ_true = 0.20 pc, L = 2.0 pc). However, real HGBS filaments are complex multi-filament systems. Empirical analysis shows PM/(L/3) ≈ 0.2 for HGBS regions (not 1.0 as expected if PM converged to L/3), and PM shows only moderate correlation with filament length (R² = 0.60, p = 0.127, n=4). The 40--50% PM-NN difference observed in HGBS data likely reflects geometric complexity of multi-filament systems rather than simple L/3 convergence."

---

## Summary

### What Was Wrong

1. **Overstated claim**: 194% bias presented as general result, but only applies to specific synthetic case
2. **Inadequate validation**: No comparison of predicted vs. observed bias for real HGBS parameters
3. **Missing empirical test**: PM vs. L/N dependence not tested with actual HGBS data
4. **Simplified model**: Synthetic single-filament system doesn't capture HGBS multi-filament complexity

### What Needs Correction

1. **Remove 194% from headline**: This is misleading and doesn't apply to real HGBS data
2. **Add empirical validation**: Show PM vs L correlation (weak, R² = 0.60, p = 0.127)
3. **Contextualize bias range**: PM bias depends on λ_true/(L/3) ratio; for HGBS parameters, observed 40-50% bias is much smaller than synthetic case
4. **Acknowledge complexity**: Real HGBS filaments are multi-filament systems, not simple beaded filaments
5. **Revise interpretation**: 40-50% PM-NN difference reflects geometric complexity, not simple L/3 artifact

### Correct Bottom Line

The L/3 artifact is **REAL for simplified synthetic systems** but **does NOT fully explain the PM-NN difference in real HGBS data**. The 194% figure is misleading as a headline result.

---

**Status**: ⚠️ PAPER REQUIRES SUBSTANTIAL REVISION TO L/3 ARTIFACT CLAIMS

**Next Steps**:
1. Correct abstract and remove 194% figure from headline
2. Add empirical validation section
3. Revise Statistical Methods section
4. Contextualize all L/3 artifact claims as applying to synthetic systems, not necessarily to HGBS
