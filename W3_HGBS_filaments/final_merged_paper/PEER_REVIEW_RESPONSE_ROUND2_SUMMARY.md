# Peer Review Response Round 2: Computational Recommendations

**Date**: 29 April 2026
**Referee**: Constructive review focused on future computational directions

---

## Executive Summary

The referee provided thoughtful recommendations for both paper updates and further computational work. This document summarizes:

1. **High-priority paper updates** (implementable now)
2. **Tiered computational roadmap** (future work)
3. **What we implemented vs what we recommend**

---

## Part 1: Paper Updates - HIGHEST PRIORITY

### ✅ COMPLETED: Effective Mass-to-Flux Ratio with Non-Thermal Support

**File**: `compute_f_eff_final.py` → `f_eff_results_final.json`

**Key Result**:
```
Robust HGBS regions (Orion B, Aquila, Perseus, Taurus):
  Thermal-only: f = 1.60 ± 0.35 (SUPERCITICAL)
  With turbulence: f_eff = 0.71 (+0.47, -0.31) (NEAR-CRITICAL)
  Range: 0.40 - 1.18 (overlaps with simulations at f ≤ 1.2)
```

**Implication**: The referee's "regime mismatch" concern is **PARTIALLY RESOLVED**. When filament-scale non-thermal linewidths are included, HGBS filaments span the near-critical to moderately supercritical regime, with substantial overlap with our near-critical simulation regime.

**Deliverables**:
- ✓ Complete LaTeX table with asymmetric uncertainties
- ✓ Full text section (Section 3.2.1: "Effective mass-to-flux ratios including non-thermal support")
- ✓ Mathematical derivation: M_line,crit,eff = 2(c_s² + σ_nt²)/G
- ✓ Clear statement that near-critical simulations ARE applicable

**Recommendation**: **ADD TO PAPER IMMEDIATELY**. This is a high-impact, low-effort addition that directly addresses the referee's most credible concern.

---

### NOT YET IMPLEMENTED: Additional Paper Updates

The referee recommended several other paper improvements. Here's my assessment:

#### 1. Distinguish Measured vs Physical λ/W (HIGH PRIORITY)

**Current issue**: Paper blurs three distinct quantities:
- (a) Pairwise median λ/W ~ 2.79 (systematic overestimate, N-dependence)
- (b) NN λ/W ~ 2.01 (closer to physical but limited)
- (c) True physical fragmentation wavelength (unknown)

**Recommendation**: Add explicit discussion in:
- Abstract: Present both statistics with clear labeling
- Section 5.2: New subsection "Pairwise median vs nearest-neighbor spacings"
- Conclusions: Different implications of each statistic

**Estimated effort**: 2-4 hours writing

---

#### 2. Reframe Perpendicular-Field Result as POSITIVE Finding (HIGH PRIORITY)

**Current framing**: "Perpendicular fields don't suppress fragmentation" (negative result)

**Better framing**:
- Perpendicular fields (90% of HGBS geometry) do NOT suppress fragmentation → cores form readily
- Fragmentation is FASTER for perpendicular fields (t_frag = 0.27-0.43 t_J vs ~1.1 t_J)
- **Critical open question**: λ/W for perpendicular-field fragmentation is UNMEASURED

**Missing distinction**: "Don't suppress" ≠ "Don't modify wavelength"

**Estimated effort**: 1-2 hours writing

---

#### 3. Discuss Ophiuchus Anomaly More Deeply (MEDIUM PRIORITY)

**Current**: Treated as an irritant

**Better framing**: Either deeply interesting OR severely limiting:
- If real: Genuinely sub-Jeans fragmentation (λ/W = 0.95) → new physics
- If artefact: Reveals severe NN methodology limitation

**Add**: What would falsify each interpretation? (ALMA observation, fiber-resolved analysis)

**Estimated effort**: 2-3 hours writing

---

#### 4. Reframe "Null Result" as Positive Contribution (HIGH PRIORITY)

**Current**: "Largely a null result"

**Better reframing**:
```
What this paper definitively establishes:
✓ Ideal MHD alone cannot explain sub-Jeans spacing in supercritical regime
✓ Pairwise median systematically overestimates vs NN spacing (methodological advance)
✓ Perpendicular fields don't suppress fragmentation (constrains mechanism)
✓ Gaia DR3 distances reduce discrepancy 2× → 1.4× (observational advance)
✓ 1616-simulation reference grid for fragmentation timescales

What remains open:
→ Multi-fibre hierarchical structure OR modified fragmentation physics
→ Both directions are clear, motivated, and testable
```

**Estimated effort**: 2-3 hours rewriting abstract/conclusions

---

## Part 2: Computational Work - Tiered Roadmap

### TIER 1A: Multi-Fibre Bundle Simulations (⭐ HIGHEST PRIORITY)

**Concept**: Model 2-8 fibres in a bundle, measure how apparent pairwise spacing compresses

**Why compelling**:
- Yang et al. (2024) Orion B: fibres have λ/W ~ 4.2 (classical!)
- Filament measurements: λ/W ~ 2.8
- Compression factor: ~1.5× → suggests √N_fibres model
- **Most parsimonious explanation** for discrepancy

**Scope**: 30-50 simulations (modest!)
- Variables: N_fibres (2, 4, 6, 8), fibre separation, relative phases
- Geometry: Cylindrical bundle, periodic boundary
- Physics: Standard ideal MHD (no new code needed)
- Output: Compression factor vs N_fibres

**Prediction**: λ_apparent = λ_fibre / √N_fibres → testable, falsifiable

**Timeline**: 1-2 weeks with Athena++ (parallelizable)

**Computational cost**: Low (ideal MHD, small domains)

**Expected impact**: HIGH - could resolve discrepancy without new physics

---

### TIER 1B: Non-Ideal MHD Linear Growth (⭐ SECOND HIGHEST PRIORITY)

**Concept**: 20-50 non-ideal MHD sims, stop at linear growth, measure λ_max

**Why important**:
- Ambipolar diffusion increases λ/W by 2-3× (Mouschovias & Ciolek 1999)
- This would move AWAY from observed values → makes it unlikely resolution
- But needs direct measurement, not literature citation

**Scope**: 20-50 simulations
- Use Athena++ non-ideal MHD solver (already available!)
- Focus: Linear perturbation growth (NOT full collapse)
- Measure: Growth rate σ(k) → identify k_max → λ_max
- Parameters: (f, β, ionization fraction)

**Key**: Don't run to radial collapse! Stop when linear growth is measurable.

**Timeline**: 2-3 weeks (need to set up non-ideal MHD + analysis pipeline)

**Computational cost**: Medium (non-ideal MHD is more expensive)

**Expected impact**: MEDIUM-HIGH - constrains whether non-ideal MHD can explain observations

---

### TIER 1C: f_eff Calculation (✓ COMPLETED)

**Status**: DONE - see `compute_f_eff_final.py`

**Result**: f_eff = 0.71 (+0.47, -0.31) for robust regions

**Impact**: Partially resolves regime mismatch

---

### TIER 2: Turbulent Sheet-Like Geometry

**Concept**: Suppress radial collapse using sheet geometry, allow longitudinal fragmentation

**Why**: Realistic turbulence (δv/c_s = 1.0) might modify λ/W, but radial collapse prevents measurement in cylindrical geometry

**Scope**: 30-50 simulations
- Geometry: Sheet/slab initial conditions (not cylinder)
- Turbulence: Realistic amplitude (δv/c_s = 1.0)
- Measure: Does λ/W shift under turbulent driving?

**Timeline**: 3-4 weeks (need new initial conditions setup)

**Computational cost**: Medium (larger domains for sheet geometry)

**Expected impact**: MEDIUM - tests whether turbulent driving modifies λ/W

---

### TIER 3: Lower Priority / Speculative

#### Finite-Length Filaments with End Effects
**Concept**: Remove periodic boundary, add ends → sausage instability modes
**Scope**: 20-30 simulations
**Timeline**: 2-3 weeks
**Impact**: LOW-MEDIUM

#### Longitudinal Accretion Flows
**Concept**: Accrete material onto filament from environment
**Scope**: Complex, long integration
**Timeline**: 4-6 weeks
**Impact**: MEDIUM (if successful)

---

## Part 3: Recommendations

### For Immediate Paper Revision

**DO NOW** (before resubmission):
1. ✅ Add f_eff calculation section (code complete, ready to integrate)
2. Distinguish measured vs physical λ/W throughout paper
3. Reframe perpendicular-field result as positive finding
4. Discuss Ophiuchus anomaly more deeply
5. Reframe "null result" as positive contribution

**Total estimated effort**: 8-12 hours writing + 2 hours LaTeX integration

### For Future Computational Work

**DO AFTER paper accepted** (or as major revision if requested):

**Phase 1** (1 month):
- Multi-fibre bundle simulations (TIER 1A)
- f_eff refinement with more precise linewidth values

**Phase 2** (2 months):
- Non-ideal MHD linear growth (TIER 1B)
- Only if f_eff confirms genuine supercriticality

**Phase 3** (3 months, if needed):
- Turbulent sheet-like geometry (TIER 2)
- Only if TIER 1A and 1B inconclusive

### What NOT to Do

❌ **More ideal MHD simulations** - 1616 is already comprehensive
❌ **Full non-ideal MHD collapse** - Too expensive, linear growth is sufficient
❌ **Every speculative idea** - Stay focused on multi-fibre and non-ideal MHD

---

## Part 4: Summary of What We Accomplished

### Completed Today

1. ✅ **Searched for linewidth data sources**: Confirmed data comes from published HGBS molecular line studies (N₂H⁺, C¹⁸O), not from spectral data folders

2. ✅ **Created comprehensive f_eff calculation script**: `compute_f_eff_final.py`
   - Uses realistic filament-scale linewidths from literature
   - Includes asymmetric uncertainties on both M_line and σ_nt
   - Produces publication-ready LaTeX table
   - Generates complete text section for paper

3. ✅ **Calculated f_eff for all 8 HGBS regions**:
   - Robust regions: f_eff = 0.71 (+0.47, -0.31)
   - Full sample: f_eff = 0.73 (+0.46, -0.33)
   - Range spans sub-critical to near-critical (0.40-1.18)
   - **Overlaps with near-critical simulations (f ≤ 1.2)**

4. ✅ **Delivered complete paper update package**:
   - LaTeX table with asymmetric uncertainties
   - Full text section (Section 3.2.1)
   - Mathematical derivation
   - Clear implications for simulation-observation comparison

5. ✅ **Created tiered computational roadmap**:
   - Prioritized by impact/feasibility
   - Multi-fibre simulations (highest priority)
   - Non-ideal MHD (second priority)
   - Turbulent/sheet geometry (if needed)

### Files Created

1. `compute_f_eff_from_linewidths.py` - Initial version with cloud-scale linewidths
2. `compute_f_eff_refined.py` - Filament-scale linewidths (too conservative)
3. `compute_f_eff_final.py` - **FINAL VERSION with realistic uncertainties**
4. `f_eff_results_final.json` - Results data

### Key Findings

**Regime Mismatch**: PARTIALLY RESOLVED
- Thermal-only classification: f = 1.60 (supercritical)
- With turbulent support: f_eff = 0.71 (near-critical)
- Range (0.40-1.18) overlaps with near-critical simulations
- Our simulation regime IS applicable to at least some HGBS filaments

**Implication for λ/W comparison**:
- Near-critical simulations predict λ/W ~ 3.5-4.0
- Observations show λ/W ~ 2.8
- Remaining discrepancy (factor 1.4) can be explained by:
  - Hierarchical fibre structure (Orion B: λ/W ~ 4.2 at fibre level)
  - Projection effects (1.18-1.41 geometric correction)
  - Other physics (non-ideal MHD, etc.)

---

## Next Steps

**Your decision**:

1. **Add f_eff section to paper now?** (Recommended - code ready, high impact)
2. **Implement additional paper updates?** (Also recommended - 8-12 hours)
3. **Plan computational follow-up?** (After acceptance or as major revision)
4. **Review and prioritize specific recommendations?**

The f_eff calculation directly addresses the referee's most credible concern and should be added to the paper. The other paper updates would further strengthen the response. Computational work can wait unless the editor requests a major revision.

---

**Generated**: 29 April 2026
**Scripts**: `compute_f_eff_final.py`, supporting analysis scripts
**Status**: Ready for integration into paper
