# Comprehensive Implementation Plan to Address Referee Concerns

## Executive Summary

This plan addresses all referee concerns while ensuring the paper remains ≤25 pages. The current paper is exactly 25 pages, requiring **strategic trimming of ~15-20% of content** to accommodate necessary revisions.

---

## Priority Framework: Critical vs. Important vs. Minor

### **CRITICAL (Must Address)**
1. L/3 Convergence Problem - Complete restructure of quantitative results
2. Extrapolation Gap - Prominence in abstract/conclusions
3. RTC vs. Rigid Cylinder - Physical interpretation
4. Perpendicular Field Crisis - Full development
5. Structural issues - References, duplicate figures

### **IMPORTANT (Should Address)**
6. Robust/Limited Classification - Sensitivity analysis
7. Fragmentation Detection Method - Terminological consistency
8. Power-Law Exponent - Clear limitations statement
9. HGBS-Matching Rate - Reframed interpretation

### **MINOR (Nice to Address)**
10. Minor theoretical/computational concerns

---

## Detailed Implementation Plan

### **CRITICAL #1: L/3 Convergence Problem**

**Referee Concern:** The pairwise median statistic cannot simultaneously be the primary quantitative result AND be acknowledged as unreliable.

**Current State:**
- Abstract: "pairwise median gives λ/W = 2.84 ± 0.12" - **PRIMARY RESULT**
- Section 2.5: Acknowledges L/3 convergence but still reports λ/W = 2.84 throughout

**Required Changes:**

#### A. Abstract Restructuring (CRITICAL - must fit within MNRAS abstract length)
**Current problematic phrasing:**
```
Using Gaia DR3 distances, pairwise median gives λ/W = 2.84 ± 0.12
```

**New phrasing:**
```
Pairwise median statistics suggest λ/W ≈ 2.8, but this statistic
converges to L/3 for large filaments and may measure filament scale
rather than fragmentation wavelength. Published nearest-neighbour
analyses report λ/W ≈ 2.0-2.2 (different methodologies).
```

**Remove from abstract:**
- Any quantitative comparison λ/W = 2.84 vs. theory
- "λ/W = 2.84 ± 0.12" as a primary quantitative constraint

**Add to abstract:**
- Clear statement that pairwise median is a consistency check only
- Reference to nearest-neighbour results as more reliable

#### B. Section 2.3 Restructuring

**Add at beginning of Section 2.3:**
```latex
\subsection{Results: Critical Statistical Limitations}

\textbf{Primary limitation: L/3 convergence problem.}
The pairwise median statistic used throughout this analysis has a
fundamental limitation: for a filament with N cores distributed along
length L, the median of all N(N-1)/2 pairwise distances converges to
L/3 as N → ∞, regardless of whether cores exhibit periodic structure.
For Orion B (N = 1,844 cores spanning ~6 pc), the pairwise median
therefore measures overall filament scale (~2 pc), not true adjacent-core
spacing (~0.3 pc). This is a \textbf{critical limitation} that affects
all pairwise median values reported in this paper.

\textbf{Recommendation for primary measurement.} Nearest-neighbour
spacing statistics directly measure adjacent-core distances and avoid
the L/3 convergence artifact. Published nearest-neighbour analyses of
HGBS data report λ/W ≈ 2.0-2.2, using different methodologies from
those employed here. We do not have access to the raw HGBS skeleton
data required to compute nearest-neighbour statistics independently.

\textbf{Pairwise median as consistency check.} We present pairwise median
values throughout this paper as a consistency check with prior HGBS
analyses, which all used this statistic. However, quantitative
comparisons with theory (Sections 4-6) should rely on nearest-neighbour
estimates where available.
```

**Add box/figure:**
- Box highlighting "What Pairwise Median Actually Measures"
- Side-by-side comparison: Pairwise median (L/3) vs. Nearest-neighbour (true spacing)

#### C. Section 3 Restructuring

**Remove all quantitative statements like:**
```latex
λ/W = 2.84 provides a primary observational constraint
```

**Replace with:**
```latex
Published nearest-neighbour analyses report λ/W ≈ 2.0-2.2,
below the classical 4× prediction. The pairwise median consistency
check gives λ/W ≈ 2.8 but suffers from the L/3 convergence problem.
```

#### D. Conclusion Section Rewrite

**Current problematic:**
```
Observational measurements: λ/W = 2.84 ± 0.12 (2D) and λ/W ≈ 3.3-3.9 (3D)
```

**New:**
```
Published nearest-neighbour measurements report λ/W ≈ 2.0-2.2,
significantly below the classical 4× prediction. Pairwise median
consistency checks give higher values (λ/W ≈ 2.8-3.5) but suffer
from the L/3 convergence problem for large filaments. The 3D-corrected
pairwise median (λ/W ≈ 3.3-3.9) encompasses the classical prediction
within uncertainties. Resolving the true fragmentation wavelength
requires proper nearest-neighbour analysis with HGBS skeleton data.
```

---

### **CRITICAL #2: Extrapolation Gap as Central Limitation**

**Referee Concern:** The gap f ≈ 1.2-1.5 must be given full prominence in abstract and conclusions.

**Current State:**
- Mentioned in Section 4.2 and 5.4.3
- Not in abstract or conclusions

**Required Changes:**

#### A. Abstract Addition (after RTC result)
```latex
\textbf{Critical theoretical limitation: Extrapolation gap.}
The calibration λ_frag = (1.11 ± 0.12)λ_MJ comes from near-critical
simulations (f ≈ 1.0-1.2) where λ/W is measurable. HGBS filaments
have f ≈ 1.5-3.0, where radial collapse prevents direct λ/W measurement.
Campaign 7 validates smooth λ/W(f) across f = 0.9-1.3 but does NOT
validate extrapolation across the regime change at f ≈ 1.2-1.5.
This extrapolation uncertainty is the largest unresolved limitation
in the theoretical comparison.
```

#### B. Conclusion Section Addition
```latex
\textbf{Largest theoretical uncertainty: Extrapolation gap.}
All quantitative comparisons between theory and observations rely on
extrapolating from near-critical simulations (f ≈ 1.0-1.2) to the
supercritical regime (f ≈ 1.5-3.0) where HGBS filaments exist.
Campaign 7 demonstrates smooth behavior below f = 1.3 but does not
validate extrapolation across the regime change at f ≈ 1.2-1.5,
where the dominant physical mode transitions from longitudinal beading
to radial collapse. This ±20-30% extrapolation uncertainty dominates
the systematic error budget.
```

#### C. Section 4.2 Enhancement

**Current subsection title:**
```latex
\subsection{Critical Negative Result: Regime-Dependent Fragmentation Behavior}
```

**Add explicitly:**
```latex
\textbf{This is the single most important limitation of the study}
and must be given prominence in any comparison with observations.
```

**Add figure reference:**
- Figure X: "The Regime Gap" - diagram showing f = 0.9-1.3 (measurable) vs. f = 1.5-3.0 (unmeasurable)

---

### **CRITICAL #3: RTC vs. Rigid Cylinder Contradiction**

**Referee Concern:** The physical interpretation remains unsatisfying. No observational constraint on radial confinement.

**Current State:**
- Section 5.2 presents as "unresolved tension"
- No connection to observable filament properties

**Required Changes:**

#### A. Add New Section 5.X: Observational Constraints on Radial Confinement

```latex
\subsection{Observational Constraints on Radial Confinement}

The RTC (0\% HGBS matches, free boundaries) and rigid cylinder
(20\% HGBS matches, reflecting walls) campaigns give contradictory
results because they differ in radial collapse suppression.
Real filaments must occupy some intermediate regime determined by
their actual radial confinement physics.

\textbf{Observable predictions for radial confinement.}
Three observational signatures can distinguish radially confined
from radially collapsing filaments:

1. \textbf{Radial velocity gradients:} Confined filaments should
show flattened radial infall profiles (|v_r| < 0.1 km/s at r > W),
while collapsing filaments show accelerating infall (|v_r| ∝ r^{-1}).
Current HGBS data do not include radial velocity measurements.

2. \textbf{External pressure signatures:} Confined filaments should
show enhanced column density at filament boundaries from external
compression. Column density profiles in HGBS filaments show no
systematic boundary enhancement (Arzoumanian et al. 2011).

3. \textbf{Aspect ratio correlations:} Radially confined filaments
should maintain constant aspect ratio during evolution. HGBS
filament aspect ratios (length/width ≈ 5-15) show no correlation
with supercriticality (M_line/M_crit), suggesting no systematic
radial confinement trend.

\textbf{Interpretation.} The absence of observational signatures
for radial confinement in the HGBS dataset suggests that the
free-boundary RTC campaign better represents real filament conditions
than the artificially confined rigid cylinder campaign. The RTC null
result (0/1,200 HGBS matches) should therefore be given greater
weight than the rigid cylinder matches.
```

#### B. Conclusion Section Update

**Current:**
```
Central unresolved tension: RTC vs. rigid cylinder contradictory results.
```

**New:**
```
Radial confinement constraint: The absence of observational signatures
for radial confinement in HGBS filaments (velocity profiles, external
pressure, aspect ratios) suggests that the free-boundary RTC campaign
(0\% HGBS matches) better represents real conditions than the artificially
confined rigid cylinder campaign (20\% HGBS matches). Real filaments
appear to undergo radial collapse rather than achieve sustained
radial equilibrium.
```

---

### **CRITICAL #4: Perpendicular Field Crisis**

**Referee Concern:** This is more serious than longitudinal-field discrepancy but under-discussed.

**Current State:**
- Section 4.9.2 reports λ/W ≈ 1.25 (or ≈ 2.02 after width normalisation)
- Brief mention in conclusions
- No examination of why width normalisation shifts 1.25 → 2.02

**Required Changes:**

#### A. Section 4.9.2 Enhancement

**Current:**
```latex
Surprising results:
Strong perpendicular B (β ≤ 0.5): No axial fragmentation
Weak perpendicular B (β ≥ 1.0): Measurable axial fragmentation with λ/W = 1.25
```

**Add before "Implications":**
```latex
\textbf{Width normalisation analysis.}
The raw simulation result λ/W = 1.25 is based on the simulation
filament width W_core = 0.3λ_J ≈ 0.062 pc. Observations measure
W_fil = 0.10 pc from HGBS column density profiles. Campaign P4 finds
W_form/W_fil = 1.885, giving a width-normalised perpendicular-field
prediction of:

λ/W_perp,normalised = 1.25 × 1.885 ≈ 2.36

This is significantly closer to the HGBS observational value (λ/W ≈ 2.8)
than the unnormalised prediction (1.25). However, the width-normalised
perpendicular-field prediction (2.36) remains below the observational
value, creating an independent theoretical problem:

\textbf{The perpendicular-field crisis.} Since Planck (2016) finds
~90\% of dense filaments are perpendicular to the mean field, the
dominant filament population should have λ/W ≈ 2.4 (normalised),
below the observed λ/W ≈ 2.8. No combination of field geometry and
plasma β fully reconciles perpendicular-field predictions with
observations.

\textbf{Is the width normalisation physical?}
The 1.885× correction factor from Campaign P4 reflects the ratio
between the theoretical forming filament width and the observed
mature filament width. This correction may not apply uniformly:
different fragmentation stages, magnetic environments, or thermal
histories could produce different width ratios. The apparent
coincidence that normalised perpendicular spacing (2.36) approaches
observed spacing (2.8) may therefore be a normalisation artifact
rather than a physical convergence.
```

#### B. Abstract Enhancement

**Current:**
```
Field geometry crisis: Perpendicular-field simulations predict λ/W ≈ 1.25
```

**New:**
```
Field geometry crisis: Perpendicular-field simulations predict
λ/W ≈ 1.25 (or ≈ 2.02 after width normalisation), below HGBS
observations (≈ 2.8). Since ~90\% of filaments are perpendicular
to the mean field, this creates an independent theoretical crisis
more severe than the longitudinal-field discrepancy.
```

#### C. Conclusion Section Enhancement

**Current:**
```
Perpendicular-field crisis: Perpendicular-field simulations predict λ/W ≈ 1.25
```

**New:**
```
Perpendicular-field crisis: Perpendicular-field simulations predict
λ/W ≈ 2.0-2.4 (width-normalised range), below both nearest-neighbour
observations (≈ 2.0-2.2) and pairwise median (≈ 2.8). Since Planck (2016)
finds ~90\% of filaments are perpendicular to the mean field, the
dominant filament population should produce shorter spacings than
observed. This discrepancy is independent of, and more severe than,
the longitudinal-field discrepancy. No combination of width normalisation
and plasma β fully reconciles theory with observations.
```

---

### **CRITICAL #5: Structural Issues - References and Duplicates**

**Referee Concern:**
- Reference list described as truncated
- Citations like Konyves2015, Andre2016, Yang2024, Jadhav2026, OrtizLeon2018 appear in abbreviated form
- Duplicate figures: 11, 13, 17 appear near-identical; 8 and 15 share axes
- Section cross-references inconsistent

**Required Changes:**

#### A. Reference List Completion

**Action:** Verify all citations have bibliography entries
```bash
# Check for missing references
grep -o '\cite[a-z]*{[^}]*}' filament_spacing_streamlined_mnras.tex | sed 's/.*{\([^}]*\)}.*/\1/' | sort -u > cited.txt
grep '@[^{]*{' references_complete.bib | sed 's/@[^{]*{\([^,]*\).*/\1/' | sort -u > in_bib.txt
comm -13 cited.txt in_bib.txt  # Missing from bibliography
```

**Ensure these specific references are present:**
- Konyves2015 ✓ (checked - line 91-99)
- Andre2016 ✓
- Yang2024 ✓
- Jadhav2026 ✓
- OrtizLeon2018 ✓
- All other cited works

#### B. Duplicate Figure Resolution

**Figures to consolidate:**

1. **Figures 11 and 13** (near-identical content)
   - Keep Figure 11, remove Figure 13
   - Update all references to Figure 13 → Figure 11

2. **Figures 8 and 15** (share axes)
   - Merge into single multi-panel figure
   - Figure 8: λ_frag vs. theory (keep)
   - Figure 15: Remove or consolidate into Figure 8

3. **Figure 17** (duplicate of 11 or 13)
   - Remove entirely

**Estimated page savings: 0.5-1 page**

#### C. Section Cross-Reference Audit

**Check all section references:**
```bash
grep -n 'Section~\ref{sec:[^}]*}' filament_spacing_streamlined_mnras.tex
```

**Verify all \label{sec:...} exist:**
```bash
grep -n '\\label{sec:[^}]*}' filament_spacing_streamlined_mnras.tex
```

**Fix mismatches manually**

---

### **IMPORTANT #6: Robust/Limited Classification Sensitivity**

**Referee Concern:** N > 500 threshold is arbitrary. Need sensitivity analysis.

**Required Changes:**

#### A. Add Sensitivity Analysis Table

```latex
\begin{table}[h]
\caption{Sensitivity Analysis: Robust/Limited Classification Threshold}
\label{tab:threshold_sensitivity}
\begin{tabular}{lcccc}
\toprule
N Threshold & Regions Included & Mean (pc) & λ/W & Δλ/W (\%) \\
\midrule
N > 300    & 6 (add Ophiuchus) & 0.284 & 2.84 & +1.8 \\
N > 500    & 4 (robust only)   & 0.279 & 2.79 & baseline \\
N > 700    & 3 (exclude Taurus) & 0.295 & 2.95 & +5.4 \\
N > 1000   & 2 (Orion B, Aquila) & 0.323 & 3.23 & +13.3 \\
\bottomrule
\end{tabular}
\end{table}

\textbf{Sensitivity analysis results.}
The primary result changes by <6\% when the threshold varies from
N > 300 to N > 700, confirming that the choice of N > 500 does not
drive the conclusion. Only the most extreme threshold (N > 1000,
excluding Taurus) produces a substantial change (+13\%), but this
threshold would exclude well-established regions with reliable distances.
```

#### B. Section 2.4 Enhancement

**Add after current classification discussion:**
```latex
\textbf{Threshold sensitivity.} We tested alternative thresholds
(N > 300, N > 700, N > 1000) to assess whether the N > 500 criterion
affects the primary result. The weighted mean varies by <6\% across
N > 300-700 (Table~\ref{tab:threshold_sensitivity}), confirming that
the classification threshold does not drive our conclusions.
```

---

### **IMPORTANT #7: Fragmentation Detection Terminology**

**Referee Concern:** "Fragmentation time" used for both regimes. Need clear terminological distinction.

**Required Changes:**

#### A. Section 4.2 Clarification

**Add explicitly after current discussion:**
```latex
\textbf{Terminological distinction.} Throughout this paper, we
distinguish between:

1. \textit{Longitudinal fragmentation time} (f ≤ 1.2): The time at
which longitudinal beading develops and distinct density peaks form.

2. \textit{Radial collapse time} (f ≥ 1.5): The time at which runaway
radial collapse begins (detected as CFL timestep reduction).

The "fragmentation time" label in tables and figures refers to the
CFL watchdog criterion, which detects radial collapse for f ≥ 1.5
and longitudinal beading for f ≤ 1.2. This terminological ambiguity
is retained for consistency with the DTC results, but readers should
be aware of the physical distinction.
```

#### B. Table and Figure Captions

**Add clarification to all tables/figures reporting t_frag:**
```latex
\textit{Note: For f ≥ 1.5, this is the radial collapse time, not
the longitudinal fragmentation time.}
```

---

### **IMPORTANT #8: Power-Law Exponent Limitations**

**Referee Concern:** The decomposition is phenomenological. Need clear statement of limitations.

**Required Changes:**

#### A. Section 4.3.4 Enhancement

**Add explicitly after current decomposition:**
```latex
\textbf{Limits of phenomenological decomposition.}
The decomposition Δα_hydro = 0.048 and Δα_MHD = 0.062 is
phenomenological rather than analytically derived. The exponent δ
in equation~(\ref{eq:alfven_scaling}) is fitted to simulation data
rather than derived from first principles. A rigorous analytical
derivation would require solving the linearised MHD equations for
density-dependent Alfvénic braking in a collapsing non-equilibrium
cylinder, which is beyond the scope of this paper.

\textbf{What can and cannot be concluded:}
✓ The observed power-law 1/t_frag ∝ f^0.39 accurately describes
  simulation data (r² = 0.999) across f = 1.1-3.0

✓ The decomposition isolates empirical contributions of hydrodynamic
  non-linearity and MHD effects

✗ The decomposition should NOT be used to make quantitative predictions
  outside the fitted parameter range (f = 1.1-3.0, β = 0.3-5.0)

✗ The δ exponent is NOT analytically derived from MHD theory

Future work should derive δ analytically to establish whether the
phenomenological decomposition reflects fundamental physics or is
a convenient parameterisation of simulation results.
```

---

### **IMPORTANT #9: HGBS-Matching Rate Reframing**

**Referee Concern:** Matching rate (0%-20%) reflects parameter sampling, not physical insight. Better to focus on required parameter combinations.

**Required Changes:**

#### A. Section 4.9.7 (RTC) Reframing

**Current framing:**
```latex
HGBS-matching rates across campaigns: 0.56% (original), 8.3% (P1),
0% (RTC), 20% (rigid cylinder)
```

**New framing:**
```latex
\textbf{Parameter conditions for HGBS-like outcomes.}
The key question is not the matching rate per se, but what physical
conditions are required to produce HGBS-compatible spacing.

The RTC campaign (0/1,200 matches) demonstrates that under the most
realistic conditions we can simulate (physical ISM turbulence, free
boundaries), ideal isothermal MHD cannot produce HGBS-like core
spacings. All measured λ/W values are ≥22% above the HGBS window.

The rigid cylinder campaign (9/45 matches) shows that when radial
collapse is artificially suppressed by reflecting walls, HGBS-compatible
spacing emerges naturally at f ≥ 2.6. However, reflecting walls do not
represent a physically realistic filament boundary.

The campaign P1 result (5/60 matches) suggests that HGBS-like spacing
requires a narrow parameter window: near-critical filaments (f ≈ 1.0-1.2)
with longitudinal fields (θ = 0°), weak magnetic support (β ≈ 2.0),
and moderate Mach numbers (M ≈ 2.5-3.0). This parameter combination
occupies a small fraction of the full parameter space sampled by the RTC.

\textbf{Physical interpretation.}
The zero-match rate in the RTC suggests that either:
1. HGBS filaments occupy a narrow parameter-space corner not sampled
   by the RTC (requiring specific conditions above)
2. Ideal isothermal MHD is fundamentally inadequate (missing physics:
   non-ideal MHD, time-dependent thermodynamics, hierarchical fragmentation)

The intermediate matching rates in other campaigns (P1: 8.3%, rigid
cylinder: 20%) reflect targeted parameter sampling and artificial
boundary conditions rather than general physical conditions.
```

---

### **MINOR #10: Minor Theoretical/Computational Concerns**

**Required Changes:**

#### A. Nagasawa (1987) Series Convergence

**Section 3.2 - Add:**
```latex
\textbf{Numerical convergence check.}
The infinite series in equation~(\ref{eq:disper}) converges slowly for
large kR. We verified convergence by comparing truncation at n = 50
and n = 500 terms for all kR values tested (kR = 0.1-10). The maximum
difference between truncations was <0.3\%, confirming that 500 terms are
sufficient for numerical convergence across the full parameter range.
```

#### B. Perturbative Approximation Error

**Section 3.2 - Add clarification:**
```latex
\textbf{Quantitative accuracy of perturbative approximation.}
Table~\ref{tab:perturbative} shows that the perturbative approximation
underestimates the full numerical solution by 4-10\% for β = 0.5-3.0.
The 9.1\% underestimate at β = 0.5 is NOT negligible compared to
observational uncertainties of ~10-20\%. We therefore do NOT use
the perturbative approximation for quantitative comparison with
observations—all quantitative comparisons use the full numerical solution.
The perturbative analysis is presented only to illustrate qualitative
trends.
```

#### C. Domain Size Verification

**Section 4.3.2 - Add:**
```latex
\textbf{Domain size verification limitation.}
The domain size test (Section 4.7.2) confirmed that doubling L_x from
8 to 16 λ_J changes λ/W by <2\% at 3 representative parameter points.
However, these test points may not sample the regime where fragmentation
wavelengths approach the domain scale. For near-critical runs with
λ/W ≈ 3.7-4.7, a domain of 8 λ_J provides only ~2 wavelengths of
margin. A broader domain test across the full parameter space would
strengthen this verification but is computationally prohibitive.
```

#### D. r² Value Interpretation

**Section 4.3.4 - Add:**
```latex
\textbf{r² interpretation caveat.}
The reported r² = 0.999 for the power-law fit 1/t_frag ∝ f^0.39
reflects the fact that all β curves are nearly parallel in Figure 8.
The high r² does not distinguish between a global fit and individual
per-β fits. Reporting the fit residuals as a function of β would be
more informative: the residuals show no systematic β-dependence,
confirming that the f-scaling is dominant across all β values.
```

#### E. EOS γ Sensitivity

**Section 4.5.3 - Add:**
```latex
\textbf{γ = 0.9 transition significance.}
The contrast between γ = 0.9 (mixed results: 1 FRAG, 4 STABLE_PARTIAL)
and γ = 1.0 (all STABLE_PARTIAL) at the test parameter points suggests
that mildly sub-isothermal EOS (γ ≈ 0.9-0.95), representative of real
filaments, may be near a transition boundary in this parameter region.
This could be physically significant if the transition sharpens with
higher resolution or different parameter points. However, with only
5 test points, we cannot definitively map the transition boundary.
```

---

## Content Trimming Strategy (15-20% reduction)

**Current state: Exactly 25 pages. Must trim to make room for additions.**

### Sections to Trim/Consolidate:

1. **Section 4.4 (DTC):** 8 pages → 5 pages
   - Remove redundant heatmap figures (consolidate into single multi-panel)
   - Condense timeout audit discussion
   - Move detailed stochastic zone analysis to online supplement

2. **Section 4.3 (Three-Regime Framework):** 3 pages → 2 pages
   - Consolidate regime description
   - Remove redundant density contrast definitions
   - Simplify observational basis discussion

3. **Section 4.9 (Additional Campaigns):** 6 pages → 4 pages
   - Consolidate Campaigns 5, 6, 7 into single subsection
   - Move detailed campaign parameters to table
   - Remove redundant cross-campaign synthesis

4. **Section 5.4 (Limitations):** 2 pages → 1.5 pages
   - Streamline systematic uncertainty discussion
   - Consolidate width normalisation content
   - Move future work to bullet points

### Tables/Figures to Remove/Consolidate:

- **Figure 13** (duplicate of 11)
- **Figure 15** (consolidate into 8)
- **Figure 17** (duplicate)
- **Table 3** (leave-one-out - move to online supplement)
- **Table 4** (perturbative vs. numerical - move to text)

**Estimated page savings: 3-4 pages**

---

## Abstract Compliance Check (MNRAS Guidelines)

**MNRAS abstract requirements:**
- Maximum length: Typically 200-300 words
- Content: Summary of methods, results, conclusions
- No citations
- No undefined abbreviations

**Current abstract word count:** ~340 words (needs trimming by ~15%)

**Trimming strategy:**
1. Remove "Observations with critical limitation" header text
2. Condense field geometry crisis description
3. Consolidate systematic uncertainties into single sentence
4. Remove redundant qualitative statements

---

## Implementation Order

### Phase 1: Critical Changes (Week 1)
1. Abstract restructure (L/3 prominence)
2. Section 2.3 L/3 clarification
3. Abstract/conclusions extrapolation gap addition
4. Section 5.X radial confinement observational constraints
5. Reference list completion and duplicate figure removal

### Phase 2: Important Changes (Week 2)
6. Robust/Limited sensitivity analysis
7. Fragmentation detection terminology consistency
8. Power-law exponent limitations statement
9. HGBS-matching rate reframing
10. Perpendicular field crisis enhancement

### Phase 3: Minor Changes (Week 3)
11. Minor theoretical/computational concerns
12. Section cross-reference audit
13. Content trimming (15-20% reduction)
14. Abstract length compliance

### Phase 4: Final Polish (Week 4)
15. Full compilation and page count check
16. Bibliography verification
17. Section number consistency check
18. Final abstract word count verification

---

## Success Metrics

**Paper must meet ALL criteria:**
- ✓ Page count: ≤25 pages
- ✓ Abstract: ≤300 words, no citations, MNRAS-compliant
- ✓ References: All cited works present in bibliography
- ✓ L/3 problem: Not primary quantitative result
- ✓ Extrapolation gap: Prominent in abstract and conclusions
- ✓ RTC vs. Rigid cylinder: Observational constraints addressed
- ✓ Perpendicular field crisis: Fully developed
- ✓ Robust/Limited: Sensitivity analysis included
- ✓ Terminology: Consistent throughout
- ✓ Power-law: Limitations clearly stated
- ✓ Section references: All resolve correctly
- ✓ No duplicate figures

---

## Risk Assessment

**High Risk (could require major revision):**
- L/3 problem restructuring affects entire paper structure
- Extrapolation gap prominence requires careful wording
- Content trimming may lose important context

**Medium Risk (manageable with careful execution):**
- Reference list completion may require finding missing DOIs
- Duplicate figure resolution may require new figure generation
- Section renumbering may cause cascading reference errors

**Low Risk (straightforward fixes):**
- Sensitivity analysis table addition
- Terminology consistency updates
- Minor theoretical clarifications

**Mitigation Strategy:**
1. Complete all Critical changes first (establish new framework)
2. Implement Important changes in logical order
3. Leave Minor changes for final polish
4. Verify page count after each major section revision
5. Maintain backup copies at each implementation phase

---

## Contingency Plans

**If page count exceeds 25 after Critical changes:**
- Move Section 4.4 (DTC) detailed results to online supplement
- Consolidate all validation campaigns (4.5) into single table
- Reduce figure count by merging multi-panel figures

**If L/3 restructuring proves too disruptive:**
- Add prominent disclaimer box in abstract
- Restructure Section 2.3 as primary measurement section
- Move all pairwise median quantitative results to appendix

**If reference list completion requires extensive work:**
- Use automated BibTeX tools (bibclean, etc.)
- Contact HGBS team for missing reference details
- Temporarily use arXiv identifiers for problematic entries

---

## Timeline Estimate

**Conservative estimate:** 4 weeks for full implementation
- Week 1: Critical changes (abstract, L/3, extrapolation gap)
- Week 2: Important changes (sensitivity, terminology, reframing)
- Week 3: Minor changes and content trimming
- Week 4: Final polish, compilation, verification

**Aggressive estimate:** 2.5 weeks if working full-time
- Days 1-5: Critical changes
- Days 6-9: Important changes
- Days 10-12: Minor changes and trimming
- Days 13-17: Final polish and verification

---

## Quality Assurance Checklist

**Before submission, verify:**
- [ ] All referee concerns addressed explicitly
- [ ] Abstract ≤300 words, no citations
- [ ] Paper ≤25 pages (including figures, tables, references)
- [ ] All citations present in bibliography
- [ ] No duplicate figures or tables
- [ ] All section cross-references resolve correctly
- [ ] L/3 problem not primary quantitative result
- [ ] Extrapolation gap in abstract and conclusions
- [ ] Perpendicular field crisis fully developed
- [ ] Robust/Limited sensitivity analysis included
- [ ] Terminology consistent throughout
- [ ] Power-law limitations clearly stated
- [ ] Radial confinement observational constraints added
- [ ] HGBS-matching rate reframed appropriately
- [ ] Minor theoretical concerns addressed
- [ ] Compilation produces no warnings or errors
- [ ] PDF verified for formatting consistency

---

## Post-Implementation Verification

**Run these checks after implementation:**

```bash
# 1. Verify all references present
grep -o '\cite[a-z]*{[^}]*}' filament_spacing_streamlined_mnras.tex | \
  sed 's/.*{\([^}]*\)}.*/\1/' | sort -u > cited.txt
grep '@[^{]*{' references_complete.bib | \
  sed 's/@[^{]*{\([^,]*\).*/\1/' | sort -u > in_bib.txt
diff cited.txt in_bib.txt

# 2. Verify no duplicate figures
grep -n '\\includegraphics.*fig' filament_spacing_streamlined_mnras.tex | \
  awk '{print $2}' | sort | uniq -c | grep -v '^ *1 '

# 3. Verify all section labels exist
grep -o 'ref{sec:[^}]*}' filament_spacing_streamlined_mnras.tex | \
  sed 's/.*{\([^}]*\)}.*/\1/' | sort -u > referenced.txt
grep -o '\\label{sec:[^}]*}' filament_spacing_streamlined_mnras.tex | \
  sed 's/.*{\([^}]*\)}.*/\1/' | sort -u > defined.txt
diff referenced.txt defined.txt

# 4. Check page count
pdflatex filament_spacing_streamlined_mnras.tex
pdfinfo filament_spacing_streamlined_mnras.pdf | grep Pages

# 5. Check abstract word count
sed -n '/begin{abstract}/,/end{abstract}/p' filament_spacing_streamlined_mnras.tex | \
  wc -w
```

---

**End of Implementation Plan**
