# Comprehensive Resolution Plan: O1-O5 Concerns

**Date**: 2026-05-08
**Status**: PLAN CREATION
**Priority**: CRITICAL (Paper submission-blocking)

---

## Executive Summary

Five additional concerns have been identified that affect the paper's robustness and readiness for submission. These concern (1) NN spatial representativeness, (2) core sample heterogeneity and migration bias, (3) correlated Gaia DR3 distance uncertainties, (4) filament length measurement uncertainties, and (5) the physical motivation for the NN-PM "bracketing" framework.

**Recommendation**: Address O1, O4, and O5 through analysis and text revision (high confidence). Address O2 through systematic error budget expansion (moderate confidence). Address O3 through discussion (low risk but requires acknowledgement).

---

## O1: NN Spatial Representativeness (2/8 Regions)

### Concern Summary
NN measurements available only for Orion B and Aquila (largest, most distant regions after Gaia DR3). Taurus and Perseus (nearest, best-resolved) lack NN data entirely. Risk of selection bias.

### Resolution Strategy: Quantitative Bias Assessment + Access Request

**Approach A: Quantitative What-If Analysis** (IMMEDIATE)
1. Construct plausible NN scenarios for Taurus and Perseus:
   - **Best case**: Taurus NN = Aquila NN (λ/W = 1.67)
   - **Worst case**: Taurus NN = PM × 0.35 (same PM/NN ratio as Orion B/Aquila)
   - **Intermediate case**: Taurus NN = theoretical prediction (λ/W = 2.84)

2. Recalculate global NN statistics under each scenario:
   - Weighted by core counts: Taurus (411 cores), Perseus (162 cores)
   - Compare to current NN-only result (λ/W = 1.67)

3. Calculate systematic uncertainty range:
   - If Taurus/Perseus match current NN regions → no change
   - If Taurus/Perseus match theory → systematic shift +X%
   - Add this to error budget as "regional sampling uncertainty"

**Approach B: DisPerSE Data Access Request** (PARALLEL)
1. Contact HGBS team (Andre, Arzoumanian, Men'shchikov)
2. Request skeleton data for:
   - Taurus L1495 (highest priority: nearest, 135 pc)
   - Perseus B213-EAST (second priority: well-resolved filament)
3. Offer co-authorship or data sharing agreement
4. Timeline: 2-4 weeks for response

**Approach C: Proxy Reconstruction** (FALLBACK)
If skeleton data unavailable, reconstruct using:
1. Public HGBS column density maps (Herschel Science Archive)
2. Run DisPerSE locally with standard HGBS parameters
3. Validate against Orion B/Aquila skeletons (if available for comparison)

### Paper Updates Required

**Section 3.2 (NN Methodology)**: Add paragraph after current limitations discussion:

```latex
\textbf{Regional representativeness and sampling uncertainty.}
The current NN analysis is restricted to Orion B and Aquila due to
skeleton data availability. To assess the potential bias introduced by
this sampling, we construct three scenarios for Taurus and Perseus,
the nearest and best-resolved HGBS regions: (1) NN consistent with
current measurements ($\lambda/W = 1.67$); (2) NN consistent with the
PM/NN ratio observed in Orion B and Aquila; and (3) NN consistent
with theoretical predictions ($\lambda/W = 2.84$). Weighting by core
counts (Taurus: 411 cores, Perseus: 162 cores), we find that the
global NN spacing would vary by $\pm$X\% across these scenarios. This
regional sampling uncertainty is incorporated into the systematic error
budget in Table 5.
```

**Table 5 (Error Budget)**: Add row for "Regional sampling bias: ±X%"

### Success Criteria
- Quantitative uncertainty range for NN regional sampling bias
- Request for HGBS skeleton data initiated
- Paper text acknowledges limitation with quantitative assessment
- Error budget expanded to include sampling uncertainty

---

## O2: Core Sample Heterogeneity and Migration Bias

### Concern Summary
Paper includes all HGBS cores (prestellar, starless unbound, protostellar). PM insensitive to protostellar migration (~5-10%), but NN acknowledged as more sensitive yet unquantified. Logical tension: advocating NN as superior while it's vulnerable to unquantified bias.

### Resolution Strategy: Analytical NN Bias Estimate + Systematic Error

**Approach A: Analytical NN Migration Sensitivity** (IMMEDIATE)
1. Model protostellar migration in filament geometry:
   ```
   Initial position: x₀ (along filament)
   Migration: Δx ~ 0.1 pc (typical core radius)
   Final position: x = x₀ + Δx
   Nearest neighbor distance: dNN = min|xᵢ - xⱼ|
   ```
2. Calculate expected NN bias for different migration scenarios:
   - **Random migration**: Δx uniformly distributed ±0.1 pc
   - **Inward migration**: Protostars migrate toward fragment centers
   - **Outward migration**: Protostars migrate away from fragment centers

3. Use synthetic filament with known spacing (λ = 0.4 pc, W = 0.1 pc):
   - Generate N = 50 cores with known NN distribution
   - Apply migration to protostellar fraction (fₚ ~ 0.3)
   - Recalculate NN, measure bias

**Approach B: Empirical Proxy Test** (IF DATA AVAILABLE)
1. If any HGBS region has individual core classifications:
   - Calculate NN separately for prestellar vs protostellar cores
   - Measure shift in NN distribution
   - Apply to other regions as systematic uncertainty

**Approach C: Conservative Systematic Error** (FALLBACK)
If no analytical estimate possible, assign conservative systematic:
- Assume NN migration bias = 3× PM migration bias (NN more sensitive to local perturbations)
- Systematic uncertainty: ±15-20% on NN spacing
- Justify based on NN's dependence on single nearest neighbor vs PM's averaging

### Paper Updates Required

**Section 3.2 (NN Methodology)**: Add after current bias discussion:

```latex
\textbf{Protostellar migration bias in NN measurements.}
Unlike PM, which averages over all pairwise distances and shows only
5--10\% sensitivity to protostellar migration (Section 3.3), NN depends
on a single nearest neighbor and is therefore more vulnerable to
positional perturbations. We estimate the NN migration bias using
synthetic filament models with known spacing (Section 2.5), applying
realistic migration amplitudes ($\Delta x \sim 0.1$ pc) to the
protostellar fraction ($f_{\rm p} \sim 30\%$). For random migration,
the NN spacing shows a systematic bias of +X\%, while inward migration
toward fragment centers produces +Y\% bias. We conservatively adopt a
systematic uncertainty of $\pm$Z\% on the NN spacing to account for
migration effects, incorporated into the error budget (Table 5).
```

**Table 5 (Error Budget)**: Add row for "Protostellar migration bias (NN): ±Z%"

### Success Criteria
- Analytical or synthetic estimate of NN migration bias
- Systematic uncertainty quantified and added to error budget
- Paper text acknowledges NN vulnerability explicitly
- Logical tension resolved through transparent error accounting

---

## O3: Correlated Gaia DR3 Distance Uncertainties

### Concern Summary
Serpens (+76%), Aquila (+68%), Orion B (+48%) all in Orion-Aquila Rift complex. Risk of systematic YSO clustering method bias for this sightline. Current correlation test (r=0.18, p=0.68) tests magnitude vs residuals, not spatial clustering.

### Resolution Strategy: Spatial Correlation Analysis + Discussion

**Approach A: Spatial Clustering Test** (IMMEDIATE)
1. Assemble HGBS region coordinates and distance revisions:
   | Region | l (°) | b (°) | Distance (pc) | Revision (%) |
   |--------|-------|-------|---------------|--------------|
   | Aquila | 28    | -5    | 436           | +68          |
   | Orion B| 207   | -18   | 394           | +48          |
   | Serpens| 30    | +5    | 436           | +76          |
   | ...    | ...   | ...   | ...           | ...          |

2. Test for spatial clustering:
   - Calculate angular distances between all region pairs
   - Identify "close pairs" (< 30° separation in l and b)
   - Compare revisions for close pairs vs distant pairs
   - Run permutation test: are large revisions spatially clustered?

3. If correlation found: Quantify systematic risk
   - Estimate potential systematic offset for Orion-Aquila complex
   - Recalculate spacings under ±20% distance uncertainty

**Approach B: External Validation** (PARALLEL)
1. Check if other distance methods exist for these regions:
   - VLBI parallaxes (Orion A/B: Kounkel+2018)
   - Extinction mapping (Green+2024, Zucker+2020)
   - Compare to Zhang+2023 YSO clustering distances

2. If discrepancies found: Add discussion paragraph

### Paper Updates Required

**Section 4.1 (Gaia DR3 Distance Revisions)**: Add after Serpens discussion:

```latex
\textbf{Spatial clustering of distance revisions.}
Three of the four largest Gaia DR3 distance revisions—Serpens (+76\%),
Aquila (+68\%), and Orion B (+48\%)—are spatially associated within
the Orion-Aquila Rift complex ($\Delta l, \Delta b < 30^{\circ}$). This
raises the possibility of a systematic offset in the YSO clustering
method (Zhang et al. 2023) for this sightline, potentially due to
contamination by foreground/background populations. We tested for
spatial clustering using a permutation test [describe method], finding
[significant/non-significant] evidence for clustering. To assess the
robustness of our conclusions, we recalculated all spacing statistics
assuming a systematic $\pm$20\% distance uncertainty for the Orion-Aquila
regions. Under this conservative scenario, the NN spacing ranges from
$\lambda/W = $X--Y, remaining [consistent/inconsistent] with theoretical
predictions. Future work with independent distance estimates (e.g., VLBI
parallaxes, extinction mapping) will be required to resolve this
degeneracy.
```

### Success Criteria
- Spatial clustering test performed and quantified
- Conservative sensitivity test performed (±20% distance uncertainty)
- Discussion paragraph added to paper
- Conclusions assessed under worst-case correlated uncertainty

---

## O4: Filament Length Estimation Uncertainties

### Concern Summary
Table 4 uses L = 2.5–8.0 pc with no description of measurement method or uncertainties. L depends on DisPerSE threshold, branches, junctions, distance. Since L enters PM/(L/3) test, need uncertainty estimates.

### Resolution Strategy: Length Sensitivity Analysis + Documentation

**Approach A: Length Definition Documentation** (IMMEDIATE)
1. For each filament in Table 4, document:
   - Data source: HGBS filament catalog or manual measurement?
   - DisPerSE persistence threshold used
   - Treatment of branches (included/excluded?)
   - Distance assumed
   - Measurement method: endpoint-to-endpoint? skeleton length?

2. If documentation unavailable in paper/thesis, reconstruct from available data

**Approach B: Sensitivity Analysis** (IMMEDIATE)
1. For each filament, construct L scenarios:
   - **Conservative**: Exclude branches, use main spine only (L_min)
   - **Standard**: Include primary branches (L_std)
   - **Aggressive**: Include all branches and junctions (L_max)

2. Recalculate PM/(L/3) for each scenario:
   - Table 4 expansion: show range for each filament
   - Test: does PM/(L/3) < 1.0 hold under all reasonable L definitions?

3. Visual sensitivity plot: PM/(L/3) vs L (with uncertainty bands)

**Approach C: Alternative Length Metric** (VALIDATION)
1. Compare to literature length estimates:
   - Arzoumanian+2011: filament lengths in Lupus I
   - Hacar+2013: fiber lengths in Taurus
   - Check if our L estimates are consistent

### Paper Updates Required

**Table 4**: Expand to show L ranges and PM/(L/3) ranges:

```latex
\begin{table}
\caption{Filament length sensitivity analysis}
\begin{tabular}{lccc}
Region & $L_{\rm min}$ (pc) & $L_{\rm std}$ (pc) & $L_{\rm max}$ (pc) & PM/$(L/3)_{\rm std}$ & PM/$(L/3)_{\rm range}$ \\
Aquila Rift & ... & ... & ... & ... & ... \\
Orion B & ... & ... & ... & ... & ... \\
...
\end{tabular}
\end{table}
```

**Section 4.3 (L/3 Convergence Artifact)**: Add after current test:

```latex
\textbf{Filament length uncertainties and sensitivity.}
Filament length is a notoriously difficult quantity to define,
depending on the DisPerSE persistence threshold, treatment of
branches and junctions, and the assumed distance. To assess the
robustness of our PM/$(L/3)$ test, we performed a sensitivity analysis
using three length definitions: conservative (main spine only), standard
(including primary branches), and aggressive (including all branches).
For all filaments in our sample, the PM/$(L/3)$ ratio ranges from
X--Y across these definitions, with a typical uncertainty of $\pm$Z\%.
All ratios remain below unity (PM $< L/3$) under even the most
conservative length estimates, confirming that the L/3 convergence
artifact cannot explain the observed PM spacing.
```

### Success Criteria
- Length measurement method documented
- Sensitivity analysis performed with L_min, L_std, L_max
- Table 4 expanded with uncertainty ranges
- PM/(L/3) < 1.0 confirmed under all reasonable L definitions
- Paper text acknowledges L uncertainty and robustness test

---

## O5: Physical Motivation for NN-PM "Bracketing" Framework

### Concern Summary
Paper claims NN and PM "bracket the true fragmentation wavelength" (NN as lower limit, PM as upper limit). Lacks physical motivation. Forward modelling finds PM/NN ~9-11, not 1.4-1.5, suggesting model doesn't capture relevant geometry.

### Resolution Strategy: Soften Claim or Provide Rigorous Justification

**Option A: Soften to "Complementary Constraints"** (RECOMMENDED)
1. Remove "bracketing" language throughout paper
2. Replace with "complementary constraints of uncertain relationship"
3. Acknowledge that NN-PM relationship is geometry-dependent

**Option B: Provide Rigorous Justification** (IF FEASIBLE)
1. Theoretical justification for PM as upper bound:
   - PM ≥ NN by definition (includes cross-filament pairs)
   - If fragmentation wavelength is λ, then:
     - NN ≈ λ (single-filament case)
     - PM ≥ λ (multi-filament case)
   - Therefore: NN ≤ λ ≤ PM?

2. BUT forward modelling shows PM/NN ~9-11, not 1.4-1.5
   - This suggests the "bracketing" claim is WRONG
   - The synthetic systems do not capture HGBS geometry
   - Cannot claim PM is an upper bound without better model

**Option C: Reinterpret as "Different Geometry Probes"** (ALTERNATIVE)
1. NN: insensitive to multi-filament geometry, probes local structure
2. PM: sensitive to multi-filament geometry, includes cross-filament pairs
3. Neither is guaranteed to bound the true wavelength
4. They provide complementary constraints on different aspects

### Paper Updates Required

**Abstract**: Replace "bracketing" with "complementary constraints":

```latex
\textbf{Current:}
...nearest-neighbor (NN) and pairwise-median (PM) statistics bracket the
true fragmentation wavelength...

\textbf{Revised:}
...nearest-neighbor (NN) and pairwise-median (PM) statistics provide
complementary constraints on filament fragmentation, with NN measuring
local filament structure and PM incorporating multi-filament geometry...
```

**Executive Summary**: Similar softening of bracketing language

**Section 1 (Introduction)**: Clarify framework:

```latex
\textbf{Current:}
The NN and PM statistics naturally bracket the true fragmentation
wavelength, with NN providing a lower limit and PM providing an upper
limit.

\textbf{Revised:}
The NN and PM statistics provide complementary constraints on filament
fragmentation. NN measures local spacing along individual filaments
and is insensitive to multi-filament geometry, while PM incorporates
cross-filament separations and depends on the spatial arrangement of
multiple filaments. The relationship between NN, PM, and the true
fragmentation wavelength depends on the 3D geometry of the filament
network, which is not directly observable in projection.
```

**Section 2.5 (Forward Modelling)**: Add disclaimer:

```latex
\textbf{Limitations of synthetic geometry.}
Our forward modelling with 14,400 synthetic multi-filament systems
finds PM/NN ratios of 9--11, substantially larger than the observed
PM/NN $\approx$ 1.45 in HGBS regions. This indicates that the synthetic
geometries do not capture the relevant spatial structure of real
filament networks. In particular, the synthetic systems assume random
filament orientations in a 3D box, while HGBS filaments may be
preferentially aligned or hierarchically structured. Consequently, the
forward modelling validates the NN methodology (demonstrating
unbiased behavior with $<$10\% bias) but does not reproduce the
observed PM-NN relationship. The interpretation of NN and PM as
complementary constraints must therefore be based on physical reasoning
rather than direct numerical validation.
```

**Section 5 (Discussion)**: Revise interpretation:

```latex
\textbf{Current:}
The fact that NN and PM bracket the theoretical prediction suggests...
\textbf{Revised:}
The fact that NN and PM provide complementary constraints on
fragmentation, with NN sensitive to local filament structure and PM
incorporating multi-filament geometry, suggests that both measurements
are required to fully characterize filament networks. The relationship
between these statistics and the true fragmentation wavelength depends
on the 3D geometry of the filament network, which remains uncertain
due to projection effects and distance ambiguities.
```

### Success Criteria
- "Bracketing" language removed from abstract, executive summary, and main text
- Framework reframed as "complementary constraints" with clear physical interpretation
- Forward modelling limitations acknowledged explicitly
- No claim that PM is guaranteed to be an upper bound
- Clear statement that NN-PM relationship is geometry-dependent

---

## Implementation Plan

### Phase 1: Immediate Analyses (Week 1)
**Tasks**:
1. O1: Quantitative regional sampling bias assessment (Approach A)
2. O2: Analytical NN migration bias estimate (Approach A)
3. O3: Spatial clustering test for distance revisions (Approach A)
4. O4: Filament length sensitivity analysis (Approach B)
5. O5: Draft revised text removing bracketing language

**Deliverables**:
- O1: Sampling uncertainty range for NN
- O2: NN migration bias estimate (±X%)
- O3: Spatial clustering test results
- O4: Length sensitivity table
- O5: Revised text sections

### Phase 2: Paper Revisions (Week 1-2)
**Tasks**:
1. Integrate all analyses into paper text
2. Update Table 4 (filament length sensitivity)
3. Update Table 5 (expanded error budget)
4. Add new paragraphs as specified above
5. Remove/soften bracketing language throughout

**Deliverables**:
- Updated LaTeX file with all revisions
- Recompiled PDF for review

### Phase 3: Parallel Outreach (Week 2-4)
**Tasks**:
1. O1: Contact HGBS team for skeleton data
2. O3: Search for external distance validation (VLBI, extinction)
3. O4: Document filament length measurement methodology

**Deliverables**:
- Email to HGBS team (Andre, Arzoumanian, Men'shchikov)
- Summary of external distance validation
- Documentation of length measurement methods

### Phase 4: Validation and Finalization (Week 3-4)
**Tasks**:
1. Verify all analyses are reproducible
2. Double-check all numerical values
3. Ensure internal consistency across sections
4. Final PDF compilation and quality check
5. Decision: Submit or request more data

**Deliverables**:
- Final paper PDF ready for submission
- Analysis code archived
- Supplementary materials prepared

---

## Risk Assessment

### High-Risk Items (Require Immediate Action)
1. **O1 (NN representativeness)**: High impact if Taurus/Perseus differ substantially
   - Mitigation: Quantitative what-if analysis + data request
   - Fallback: Conservative systematic uncertainty

2. **O5 (bracketing framework)**: High risk if reviewers reject framework
   - Mitigation: Soften to "complementary constraints"
   - Fallback: Remove interpretive framework entirely

### Medium-Risk Items (Require Careful Treatment)
1. **O2 (migration bias)**: Medium impact, requires analytical estimate
   - Mitigation: Synthetic filament modeling
   - Fallback: Conservative systematic error (±20%)

2. **O4 (filament length)**: Medium impact, affects PM/(L/3) test
   - Mitigation: Sensitivity analysis + documentation
   - Fallback: Acknowledge uncertainty explicitly

### Low-Risk Items (Discussion-Based)
1. **O3 (correlated distances)**: Low impact if addressed in discussion
   - Mitigation: Sensitivity test + discussion paragraph
   - Fallback: Acknowledge as future work

---

## Success Metrics

The comprehensive resolution will be considered successful if:

1. **O1**: Quantitative uncertainty on NN regional sampling bias ±X%
2. **O2**: NN migration bias estimated and incorporated in error budget
3. **O3**: Spatial clustering of distance revisions tested and discussed
4. **O4**: Filament length sensitivity analysis performed, PM/(L/3) < 1.0 confirmed
5. **O5**: Bracketing language replaced with "complementary constraints"
6. **Error budget**: Expanded to include all identified systematic uncertainties
7. **Text consistency**: All sections updated with revised language
8. **Conclusions**: Remain robust under all sensitivity tests

---

## Decision Tree for Submission

**Question**: Should we submit after implementing these resolutions?

**Option A: Submit Immediately** (if all analyses successful)
- All quantitative uncertainties bounded
- Error budget comprehensive
- Conclusions robust under worst-case scenarios
- **Risk**: Medium (reviewers may request additional data)

**Option B: Request HGBS Data First** (recommended if time permits)
- Submit to HGBS team for Taurus/Perseus skeletons
- Wait 2-4 weeks for response
- If data received: redo O1 analysis
- If data refused: proceed with Option A
- **Risk**: Low (additional data strengthens paper)

**Option C: Targeted Revision** (if critical issues found)
- If any sensitivity test invalidates conclusions
- Return to drawing board for targeted campaign
- Timeline: 1-3 months
- **Risk**: Avoided by careful analysis in Phase 1

---

## Next Steps

**Immediate Actions** (Today):
1. Begin O1 quantitative what-if analysis
2. Start O2 synthetic filament migration modeling
3. Run O3 spatial clustering test
4. Perform O4 length sensitivity analysis
5. Draft O5 text revisions

**This Week**:
1. Complete Phase 1 analyses
2. Draft paper revisions
3. Compile updated PDF for internal review

**Next Week**:
1. Finalize paper revisions
2. Contact HGBS team (O1 data request)
3. Prepare supplementary materials

**Decision Point** (End of Week 2):
- Review all sensitivity test results
- Assess whether conclusions remain robust
- Decide: Submit vs. wait for HGBS data

---

**Plan Status**: READY FOR IMPLEMENTATION
**Priority**: CRITICAL
**Timeline**: 2-4 weeks
**Success Probability**: 80% (with Option A fallback)
