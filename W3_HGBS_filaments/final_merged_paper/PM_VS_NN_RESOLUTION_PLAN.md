# Plan to Definitively Resolve PM vs NN Discrepancy

**Date**: 2026-05-02
**Status**: Awaiting execution

---

## The Core Problem

NN measurements give λ/W = 1.01, which is:
- **2.8× smaller** than PM (λ/W = 2.79)
- **Below the theoretical minimum** of 1.25 for perpendicular-field fragmentation
- Inconsistent with the geometric mixture framework that relies on PM values

Current paper offers two interpretations but doesn't RESOLVE which is correct.

---

## Proposed Solution: Three-Pronged Attack

### Prong 1: Synthetic/Hierarchical Filament Tests (Computational)

**Objective**: Determine which statistic correctly recovers known fragmentation wavelengths under controlled conditions

**Methodology**:
1. **Create synthetic filament bundles** with known properties:
   - Single filaments: N_fibers = 1, fragmentation at known λ/W
   - Fiber bundles: N_fibers = 3-10, each fiber fragments independently at λ/W = 4
   - Vary: number of fibers, inter-fiber spacing, relative phases, overlap patterns

2. **Apply both statistics** to synthetic core catalogs:
   - PM: median of all N(N-1)/2 pairwise distances
   - NN: median of adjacent-core spacings along skeleton

3. **Recovery analysis**:
   - Does PM recover the true filament-scale λ/W?
   - Does NN recover fiber-scale spacing or inter-fiber gaps?
   - How do NN/PM ratios vary with fiber bundle properties?

4. **Statistical discrimination test**:
   - Compute expected NN/PM ratio for single-filament case
   - Compute expected NN/PM ratio for multi-fiber case
   - Compare with observed HGBS values (0.31-0.73)

**Expected outcomes**:
- If single-filament case produces NN ≈ PM, then HGBS NN << PM suggests multi-fiber structure
- If multi-fiber case reproduces NN/PM ≈ 0.3-0.7, validates hierarchical interpretation
- Quantitative relationship between fiber bundle properties and NN/PM ratio

**Timeline**: 2-3 weeks (Python analysis, no new simulations needed)

---

### Prong 2: Fiber-Resolved Analysis of Real HGBS Data (Observational)

**Objective**: Directly measure fragmentation wavelength within individual velocity-coherent fibers

**Data sources**:
1. **Taurus**: Hacar et al. (2013) - 7 velocity-coherent fibers in B213
2. **Orion B**: Hacar et al. (2018) - Fiber catalog available
3. **Other regions**: Where fiber catalogs exist

**Methodology**:
1. **For each fiber**:
   - Extract cores belonging to that fiber (using velocity information)
   - Compute PM_fiber (pairwise median within fiber)
   - Compute NN_fiber (nearest-neighbor within fiber)

2. **For each filament** (all fibers combined):
   - Compute PM_filament (existing values: 1.98-3.46)
   - Compute NN_filament (existing values: 0.62-1.82)

3. **Comparison**:
   - Does PM_fiber recover classical ~4× prediction?
   - What is PM_fiber / PM_filament ratio?
   - What is NN_fiber / NN_filament ratio?
   - Are these ratios consistent with synthetic test predictions?

**Expected outcomes**:
- If PM_fiber ≈ 4×, validates that PM measures true fragmentation wavelength at appropriate scale
- If PM_fiber / PM_filament matches synthetic bundle predictions, confirms hierarchical structure
- If NN_fiber ≈ 4×, would indicate NN is correct and PM is wrong (unlikely but testable)

**Timeline**: 3-4 weeks (requires accessing and analyzing fiber catalogs)

---

### Prong 3: Spatial Distribution Analysis (Statistical Test)

**Objective**: Distinguish single-filament vs fiber-bundle scenarios from core position distributions

**Methodology**:
1. **Two-point correlation function analysis**:
   - Compute ξ(r) for core positions along filament skeleton
   - Single-filament prediction: Single peak at λ_frag
   - Multi-fiber prediction: Multiple scales or broadened peak

2. **Spacing distribution analysis**:
   - Histogram of all adjacent-core spacings (not just median)
   - Single-filament: Narrow distribution centered at λ_frag
   - Multi-fiber: Broader distribution with multiple peaks

3. **Spatial autocorrelation**:
   - Test for periodicity at multiple scales
   - Single-filament: One dominant periodicity
   - Multi-fiber: Multiple periodicities (fiber spacing + fragmentation spacing)

4. **Model comparison**:
   - Fit single-filament model vs multi-fiber model to observed distributions
   - Use Bayesian model selection (Bayes factor)
   - Quantify evidence for each scenario

**Expected outcomes**:
- Statistical discrimination between single-filament and fiber-bundle hypotheses
- Quantitative measure of multi-scale structure
- Independent validation of synthetic test predictions

**Timeline**: 2-3 weeks (analysis of existing HGBS catalogs)

---

## Integration: Definitive Resolution Framework

### Decision Tree for PM vs NN

```
START: Observed NN/PM = 0.31-0.73, NN λ/W = 1.01

Step 1: Synthetic Tests
├─ Single-filament case produces NN ≈ PM?
│  ├─ YES → HGBS NN << PM requires multi-fiber explanation
│  └─ NO → Investigate statistical bias
│
Step 2: Multi-fiber Synthetic Tests
├─ Reproduces NN/PM ≈ 0.3-0.7?
│  ├─ YES → Validates hierarchical interpretation
│  └─ NO → Re-evaluate assumptions
│
Step 3: Fiber-Resolved Analysis
├─ PM_fiber ≈ 4× (classical)?
│  ├─ YES → PM validated at fiber scale
│  └─ NO → Both PM and NN may be measuring wrong scale
│
Step 4: Model Selection (Spatial Analysis)
├─ Multi-fiber model favored?
│  ├─ YES → Hierarchical fragmentation confirmed
│  └─ NO → Single-filament with unusual physics
│
CONCLUSION: Definitive answer to which statistic is correct
```

### Possible Outcomes and Implications

**Outcome A: Multi-fiber hypothesis validated** (most likely)
- Synthetic multi-fiber tests reproduce NN/PM ≈ 0.3-0.7
- Fiber-resolved analysis shows PM_fiber ≈ 4×
- Spatial analysis shows multi-scale structure
- **Conclusion**: PM is correct; NN measures inter-fiber gaps
- **Implication**: Geometric mixture framework stands, paper is correct

**Outcome B: Single-filament validated** (unlikely but testable)
- Synthetic single-filament tests show NN ≈ PM
- Fiber-resolved analysis shows PM_fiber ≈ PM_filament
- Spatial analysis shows single-scale structure
- **Conclusion**: Both PM and NN problematic; both wrong by similar factor
- **Implication**: Entire framework needs revision; λ/W values systematically biased

**Outcome C: NN is actually correct** (very unlikely given λ/W < theoretical minimum)
- Fiber-resolved analysis shows NN_fiber ≈ 4×
- Spatial analysis consistent with NN measuring true fragmentation
- **Conclusion**: PM overestimates by 2-3× for unknown reason
- **Implication**: Geometric mixture framework collapses; regional diversity compressed

**Outcome D: Ambiguity remains** (if tests are inconclusive)
- Multiple interpretations remain viable
- **Conclusion**: Paper must present both scenarios with equal weight
- **Implication**: Current hedged language is appropriate, but future work required

---

## Required Work Breakdown

### Phase 1: Synthetic Tests (Prong 1)
- **Python script development**: 3 days
- **Synthetic catalog generation**: 2 days  
- **Analysis and validation**: 3 days
- **Documentation and figures**: 2 days
- **Total**: ~2 weeks

### Phase 2: Fiber-Resolved Analysis (Prong 2)
- **Access fiber catalogs**: 2 days
- **Data processing scripts**: 5 days
- **Analysis per region**: 5 days
- **Cross-region comparison**: 3 days
- **Documentation and figures**: 3 days
- **Total**: ~3-4 weeks

### Phase 3: Spatial Analysis (Prong 3)
- **Correlation function code**: 3 days
- **Distribution analysis code**: 2 days
- **Model fitting/comparison**: 5 days
- **Validation with synthetic data**: 3 days
- **Documentation and figures**: 2 days
- **Total**: ~2-3 weeks

### Phase 4: Integration and Reporting
- **Cross-prong synthesis**: 3 days
- **Decision framework documentation**: 2 days
- **Paper revision or new manuscript**: 5 days
- **Total**: ~2 weeks

**Total Timeline**: 9-11 weeks for complete analysis

---

## Minimum Viable Analysis (Quickest Path to Answer)

If timeline is constrained, **Prong 1 (Synthetic Tests) + Prong 3 (Spatial Analysis)** alone could provide definitive answer:

1. **Week 1-2**: Synthetic single-filament and multi-fiber tests
2. **Week 3-4**: Spatial correlation and distribution analysis
3. **Week 5**: Cross-validation and decision

This would give ~80% of discriminating power with 50% of the effort.

---

## Success Criteria

The analysis will be considered successful if it:

1. **Definitively identifies** which statistic (PM, NN, or neither) correctly measures fragmentation wavelength
2. **Provides quantitative framework** for interpreting NN/PM ratios in terms of filament structure
3. **Validates or falsifies** the hierarchical fragmentation interpretation
4. **Resolves the apparent contradiction** between NN λ/W = 1.01 and theoretical minimum of 1.25
5. **Enables unambiguous conclusion** about whether geometric mixture framework is robust or compromised

---

## Risk Mitigation

### Risk 1: Fiber catalogs unavailable for some regions
- **Mitigation**: Use available regions (Taurus, Orion B) where fiber catalogs exist
- **Fallback**: Focus on synthetic tests which don't require observational data

### Risk 2: Synthetic tests don't match observed values
- **Mitigation**: Explore broader parameter space (more fibers, different configurations)
- **Fallback**: Use spatial analysis to discriminate scenarios

### Risk 3: Results remain ambiguous
- **Mitigation**: Present multiple competing interpretations with clear statement of uncertainty
- **Fallback**: Recommend specific future observations to resolve (e.g., ALMA fiber mapping)

---

## Deliverables

1. **Synthetic test package**:
   - Python scripts for generating synthetic filament bundles
   - Analysis code for PM/NN recovery tests
   - Quantitative relationship between fiber properties and NN/PM ratio

2. **Fiber-resolved analysis**:
   - PM_fiber and NN_fiber measurements for each region with fiber data
   - Comparison with PM_filament and NN_filament
   - Assessment of hierarchical fragmentation predictions

3. **Spatial analysis results**:
   - Two-point correlation functions
   - Spacing distributions with model fits
   - Bayesian model selection results

4. **Integrated decision framework**:
   - Decision tree for interpreting PM vs NN in any filament
   - Quantitative criteria for single-filament vs multi-fiber discrimination
   - Clear statement of which statistic is correct and why

5. **Paper revision or new manuscript**:
   - Depending on outcome, either:
     - **Validation paper**: "Hierarchical fragmentation explains NN/PM discrepancy in HGBS filaments"
     - **Major revision**: Updated framework incorporating new understanding
     - **Methods paper**: "Statistical methods for fragmentation wavelength in multi-fiber filaments"

---

## Recommendation

**Execute Prong 1 (Synthetic Tests) immediately** as it:
1. Requires no new observational data
2. Can be completed in 2 weeks
3. Provides 80% of discriminating power
4. Informs design of Prongs 2 and 3

**Then execute Prong 3 (Spatial Analysis)** for independent validation using existing HGBS catalogs.

**Defer Prong 2 (Fiber Analysis)** until synthetic results confirm multi-fiber hypothesis is worth testing with real data.

This approach gets to answer in ~4-5 weeks rather than 9-11 weeks, with ability to extend to full analysis if needed.

---

**Status**: Plan complete, awaiting approval to execute Prong 1 (Synthetic Tests)

**End of Plan**
