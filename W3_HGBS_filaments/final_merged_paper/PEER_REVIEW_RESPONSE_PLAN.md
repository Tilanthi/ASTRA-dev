# Peer Review Response Plan
## Filament Spacing Paper - MNRAS Major Revision

---

## EXECUTIVE SUMMARY

The reviewer has identified VALID concerns that must be addressed. However, based on my analysis, **NO NEW MHD SIMULATIONS ARE REQUIRED**. The issues can be resolved through:

1. **Clarification and transparency** about simulation limitations
2. **Re-analysis of existing data** where available
3. **More honest framing** of negative results
4. **Targeted re-runs** of only a few critical simulations with longer runtimes (if needed)

The reviewer's concern that "the central negative result...must be presented more prominently and honestly" is CORRECT and should guide our approach.

---

## DETAILED RESPONSE PLAN BY CONCERN

### **MAJOR CONCERN 1: Central Negative Result About Radial Collapse**

**Reviewer's Point**: The paper presents the campaign as a success while burying the fact that all 654 supercritical simulations underwent radial collapse rather than longitudinal fragmentation. If λ/W cannot be measured directly, what was actually calibrated to produce Equation 11?

**Assessment**: **VALID** concern. The current paper is misleading about this limitation.

**Response Strategy**:
1. **Prominently feature** the radial collapse negative result
2. **Clarify the source of Equation 11**: It comes from a SEPARATE earlier campaign (not the 314 PR campaign or 1591 simulations)
3. **Be explicit**: The 1.11 calibration is NOT from the current paper's simulations
4. **Action required**: Add explicit statement about what can and cannot be tested with current simulations

**Text Changes Required**:
- Add prominent box/paragraph in Section 4.3 explaining the negative result upfront
- Clarify that Equation 11 comes from earlier work (cite the source campaign)
- Be honest: "Our supercritical simulations cannot directly test λ/W predictions"
- Re-frame the campaign as testing t_frag (which we CAN measure) rather than λ/W

**NO NEW SIMULATIONS NEEDED** - just better communication of existing limitations.

---

### **MAJOR CONCERN 2: DTC "STABLE" vs Supercritical "All Fragmented" Reconciliation**

**Reviewer's Point**: DTC used 600-second wall-clock timeouts and found STABLE configurations. Supercritical campaign used 7200-10800 second timeouts and found fragmentation. If STABLE results are artifacts of insufficient runtime, the DTC transition map is unreliable.

**Assessment**: **VALID** concern. The timeout comparison is not in physical units.

**Response Strategy**:
1. **Convert wall-clock to physical time** for both campaigns
2. **Quantify the uncertainty**: What fraction of "STABLE" points would fragment with longer runs?
3. **Propagate uncertainty** through Figure 2 interpretation
4. **Consider targeted re-runs** with longer timeouts for critical grid points

**Action Required**:
- **Create conversion table** of wall-clock → t_J for each campaign phase
- **Re-run a subset** of DTC "STABLE" points with longer timeouts to quantify frag rate
- **Update Figure 2** to show confidence intervals rather than binary classification

**Targeted Re-Runs Recommended**:
- Select 10-15 representative "STABLE" points from DTC
- Run with 6-hour wall-clock timeout (matching Phase 4 adiabatic runs)
- Measure what fraction actually fragment
- Use this to quantify uncertainty in DTC results

**Simulation Investment**: ~20 re-runs × 6 hours = 120 hours → **FEASIBLE**

---

### **MAJOR CONCERN 3: Resolution Convergence Test Unresolved**

**Reviewer's Point**: Only 8% agreement (2/24) between 128³ and 256³, and 256³ runs timed out at 4 hours. The conclusion "resolution agreement cannot be assessed" is unsatisfying.

**Assessment**: **VALID** concern. Current framing is too optimistic.

**Response Strategy**:
1. **Run 256³ simulations to completion** for at least a subset
2. **Update Figure 3 caption** to be clearer about timeout artifacts
3. **Either present converged results** OR **honestly frame resolution uncertainty**

**Action Required**:
- **Re-run 6-10 representative 256³ simulations** with 6-hour timeout
- These should reach t_frag and enable proper resolution comparison
- Update paper with either converged results or explicit uncertainty statement

**Targeted Re-Runs Recommended**:
- Select representative parameter points: low/medium/high f, low/medium/high β
- Run at 256³ with 6-hour wall-clock timeout
- Compare t_frag with 128³ results
- Quantify resolution dependence

**Simulation Investment**: ~10 re-runs × 6 hours × 16 MPI = 960 CPU-hours → **FEASIBLE**

---

### **MAJOR CONCERN 4: λ_frag Calibration Requires Clearer Justification**

**Reviewer's Point**: If supercritical simulations underwent radial collapse, where did the 1.11 ± 0.12 calibration come from? The paper must specify (a) which simulations actually yielded measurable λ_frag, (b) what peak detection procedure was used, and (c) how Equation 11 was fitted.

**Assessment**: **VALID** concern. The source of the 1.11 calibration is not clearly documented.

**Response Strategy**:
1. **Trace the source** of the 1.11 calibration in earlier work
2. **If unclear**: Remove the calibration claim, frame as theoretical prediction
3. **Be explicit**: What CAN we measure from our simulations? (t_frag, not λ/W)

**Critical Question**: Does the 1.11 calibration come from:
- A separate campaign not described in this paper?
- The near-critical Phase 1 simulations (which DO show beading)?
- Earlier work that needs to be properly cited?

**Investigation Required**:
- Search earlier simulation campaigns for the source of 1.11 calibration
- If from Phase 1 near-critical sims: Clarify this explicitly
- If from separate work: Either include that work or remove calibration claim

**NO NEW SIMULATIONS NEEDED** - just better documentation and attribution.

---

### **MAJOR CONCERN 5: Statistical Treatment Weaknesses**

**Reviewer's Point**: χ² test has p=0.047 but weighted means carry correlated uncertainties. Pairwise median with small-N has poorly characterized sampling properties. Distance uncertainties (3-5%) translate to correlated systematic shifts. Limited regions add scatter without signal.

**Assessment**: **VALID** concerns. Statistical treatment needs strengthening.

**Response Strategy**:
1. **Bootstrap analysis** to quantify uncertainty in weighted mean
2. **Sensitivity test**: Compare prestellar-only vs all-core spacing
3. **Propagate distance uncertainties** through to λ/W
4. **Consider excluding limited regions** if they add only scatter

**Action Required**:
- Perform bootstrap resampling to quantify uncertainty in weighted mean
- Run sensitivity analysis with only prestellar cores for robust regions
- Add uncertainty ranges to account for systematic distance errors
- More carefully discuss inclusion of limited regions

**NO NEW SIMULATIONS NEEDED** - statistical re-analysis only.

---

### **MAJOR CONCERN 6: Core Selection Criterion**

**Reviewer's Point**: Including all cores (unbound starless + protostellar) may bias spacing measurements. Protostellar clustering could affect pairwise spacing.

**Assessment**: **REASONABLE** concern. Sensitivity test is warranted.

**Response Strategy**:
1. **Prestellar-only sensitivity test** for robust regions
2. **Quantify impact** on spacing measurement
3. **Present both results** with discussion

**Action Required**:
- Extract prestellar-core-only spacings for Orion B, Aquila, Perseus
- Compare with all-core spacings
- Present as supplementary analysis

**NO NEW SIMULATIONS NEEDED** - data re-analysis only.

---

### **MAJOR CONCERN 7: Magnetic Tension Logical Inconsistency**

**Reviewer's Point**: Paper cites two different predictions for longitudinal B: λ/W = 2.44 (Nakamura dispersion relation) vs λ/W = 3.70 (simulation calibration). These differ by 52%. Which is authoritative?

**Assessment**: **VALID** concern. Need to reconcile the two predictions.

**Response Strategy**:
1. **Clarify the distinction**: 2.44 is from linear perturbation theory, 3.70 is from simulation calibration
2. **Explain the discrepancy**: Linear theory assumes small perturbations; simulations include non-linear effects
3. **State which is more appropriate** for comparison with HGBS observations
4. **Reconcile with observational value** of 2.79

**Action Required**:
- Add discussion explaining why 2.44 and 3.70 differ
- Clarify that 2.44 is perturbative approximation
- State that 3.70 includes non-linear effects
- Discuss which is more relevant for HGBS comparison

**NO NEW SIMULATIONS NEEDED** - clarification only.

---

### **MODERATE CONCERNS**

**8. Broken LaTeX references**: Fix acknowledgments section
**9. Jadhav et al. reference**: Verify pagination format (may be arXiv-only)
**10. Three-regime framework lacks observational basis**: Cite observational constraints on M, β for HGBS
**11. Projection correction not self-consistent**: Quantify uncertainty range (1.2-1.57)
**12. Software citations/data availability**: Deposit on Zenodo with DOI
**13. Near-critical vs supercritical regime**: Make regime change more central to narrative
**14. Terminology inconsistency**: Distinguish W_fil (0.10 pc) from W_core (0.3 λ_J)
**15. "Most extensive" claim needs citation**: Find previous largest campaign
**16. Figure 3 caption clarity**: Make timeout explicit in caption
**17. Equation 9 fit range clarification**: Specify fit was across all β and M simultaneously
**18. Duplicate reference**: Fix Konyves 2020 vs Ladjelate 2020 citation conflict
**19. Define subscript notation**: Clarify ρ_x1 notation
**20. Wall-clock to t_J conversion**: Create table summarizing timeouts

---

## RECOMMENDED SIMULATION PLAN

Based on the analysis, **MINIMAL NEW SIMULATIONS** are needed:

### **Priority 1: DTC Re-runs (Most Critical)**
- **Goal**: Quantify how many "STABLE" points are actually timeout artifacts
- **Scope**: 15 representative DTC "STABLE" points
- **Configuration**: 128³, 6-hour wall-clock timeout
- **Investment**: 15 × 6 h × 16 MPI = 1,440 CPU-hours
- **Expected Outcome**: Quantify uncertainty in DTC transition map

### **Priority 2: Resolution Convergence (Important)**
- **Goal**: Achieve true resolution convergence assessment
- **Scope**: 8-10 representative parameter points at 256³
- **Configuration**: 256³, 6-hour wall-clock timeout
- **Investment**: 10 × 6 h × 16 MPI = 960 CPU-hours
- **Expected Outcome**: Either converged results or quantified resolution uncertainty

### **Total Investment**: ~2,400 CPU-hours

This is **FEASIBLE** and much less than running entirely new campaigns. The key insight is that we don't need new science—we need to run existing simulations longer to reach completion.

---

## STRUCTURAL CHANGES TO PAPER

### **Add New Section After Abstract: "Executive Summary of Limitations"**
Be upfront about what the simulations CAN and CANNOT test:
- "Our supercritical simulations (f ≥ 1.5) undergo radial collapse before longitudinal beading develops"
- "We therefore measure t_frag (fragmentation timescale) rather than λ/W (fragmentation spacing)"
- "The λ_frag = 1.11 λ_MJ calibration comes from earlier work [citation], not the simulations presented here"

### **Reorganize Section 4 (MHD Simulations)**
1. **Section 4.1**: Simulation methodology (existing)
2. **Section 4.2**: Negative result - Radial collapse in supercritical filaments (NEW, prominent)
3. **Section 4.3**: Fragmentation timescales (what we CAN measure)
4. **Section 4.4**: Field Geometry Campaign (existing, but clarify λ_frag source)
5. **Section 4.5**: Three-regime framework (existing)
6. **Section 4.6**: Supercritical filament campaign (existing)
7. **Section 4.7**: Definitive Transition Campaign (existing, add uncertainty quantification)

### **Add Section: "Quantifying Systematic Uncertainties"**
- Bootstrap analysis of weighted mean uncertainty
- Distance uncertainty propagation
- Resolution uncertainty (from Priority 2 re-runs)
- DTC classification uncertainty (from Priority 1 re-runs)

---

## PAPER REVISION CHECKLIST

### **Must Fix (Major Concerns)**
- [ ] Prominently feature radial collapse negative result (Section 4.2)
- [ ] Clarify source of λ_frag = 1.11 calibration (Section 4.3)
- [ ] Quantify DTC "STABLE" uncertainty (Priority 1 re-runs)
- [ ] Achieve or honestly frame resolution convergence (Priority 2 re-runs)
- [ ] Bootstrap statistical analysis of weighted mean
- [ ] Prestellar-only sensitivity test
- [ ] Reconcile λ/W = 2.44 vs 3.70 predictions
- [ ] Fix broken LaTeX references in acknowledgments

### **Should Fix (Moderate Concerns)**
- [ ] Verify and fix Jadhav et al. reference
- [ ] Add observational basis for three-regime placement
- [ ] Quantify projection correction uncertainty range
- [ ] Deposit data on Zenodo with DOI
- [ ] Distinguish W_fil vs W_core terminology
- [ ] Add citation for "most extensive" claim
- [ ] Clarify Figure 3 caption about timeout
- [ ] Specify Equation 9 fit range
- [ ] Fix duplicate reference conflict
- [ ] Define ρ_x1 subscript notation
- [ ] Add timeout conversion table

### **Narrative Changes**
- [ ] Make near-critical vs supercritical regime distinction more central
- [ ] Frame campaign as testing t_frag (not λ/W) for supercritical filaments
- [ ] Be honest: "Our simulations cannot directly test λ/W predictions"
- [ ] Present limitations upfront rather than burying them

---

## ESTIMATED TIMELINE

### **Phase 1: Targeted Re-runs (2-3 weeks)**
- Week 1: Run 15 DTC "STABLE" points with 6-hour timeout
- Week 2: Run 10 resolution convergence points with 6-hour timeout
- Week 3: Analyze results and quantify uncertainties

### **Phase 2: Paper Revision (1-2 weeks)**
- Make all structural changes listed above
- Re-write sections to be more honest about limitations
- Add statistical analysis sections
- Fix all moderate concerns

### **Phase 3: Final Polish (1 week)**
- Proofread all changed sections
- Verify all cross-references
- Final compilation check
- Submit revised manuscript

**Total: 4-6 weeks**

---

## CRITICAL INSIGHT: The Regime Change

The reviewer's last point is actually the MOST IMPORTANT: **Near-critical filaments (f ≈ 1.0-1.2) show longitudinal beading, while supercritical filaments (f ≥ 1.5) undergo radial collapse.**

This is NOT a bug—it's a real physical result! We should make this CENTRAL to the narrative:

**New Narrative Structure**:
1. HGBS filaments span a range of f values
2. Near-critical filaments (f ≈ 1.0-1.2) exhibit longitudinal beading → λ/W ≈ 4 (classical)
3. Supercritical filaments (f ≥ 1.5) undergo radial collapse → no λ/W measurement possible
4. Observed λ/W ≈ 2.79 may reflect mixing of these regimes, or projection effects

This is actually a STRONGER story than trying to claim we measured λ/W directly from supercritical simulations!

---

## FINAL RECOMMENDATION

**DO NOT RUN NEW SIMULATION CAMPAIGNS**

Instead:
1. Run **30 targeted re-runs** (15 DTC + 10 resolution + 5 validation) with longer timeouts
2. **Re-frame the paper** to be honest about what was measured (t_frag) vs. what wasn't (λ/W for supercritical)
3. **Make the regime change** (near-critical = beading, supercritical = collapse) a central result
4. **Add statistical rigor** through bootstrap and sensitivity analyses

This approach:
- Addresses all reviewer concerns
- Requires minimal new computational investment
- Results in a more honest and scientifically stronger paper
- May actually tell a clearer physical story than the original framing

---

## NEXT STEPS (Awaiting Permission)

1. Run the 30 targeted re-runs (Priority 1 + 2 above)
2. Analyze results to quantify uncertainties
3. Make all paper revisions as outlined above
4. Submit revised manuscript with comprehensive response to reviewer
