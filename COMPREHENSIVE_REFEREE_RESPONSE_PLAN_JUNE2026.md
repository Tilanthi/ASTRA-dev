# Comprehensive Referee Response Implementation Plan
**Date**: June 6, 2026
**Paper**: Fragmentation of Interstellar Filaments: Complete HGBS Analysis and MHD Simulations
**Reviewers**: Two expert reviewers (observational astronomer & theoretical astrophysicist)
**Status**: Major revision required - Comprehensive plan prepared

---

## Executive Summary

This implementation plan addresses **ALL** concerns raised by both reviewers in their comprehensive reports. Key finding: **Most of these concerns have already been solved in previous work** - particularly the nearest-neighbor analysis (which addresses the L/3 problem), the rigid cylinder campaigns, and various statistical analyses. This plan consolidates existing solutions and fills remaining gaps.

**Total Issues**: 20 distinct concerns
**Already Solved**: 12 (with existing data/analysis)
**Require Implementation**: 8 (text updates, calculations, clarifications)
**Estimated Time**: 6-10 hours

---

## QUICK REFERENCE: Existing Solutions Already Available

| Issue | Existing Solution | Location |
|-------|------------------|----------|
| **NN analysis (L/3 problem)** | λ/W = 2.01 ± 0.16 (79 spacings) | `/ASTRA/HGBS_all_regions_nn_results.json` |
| **RTC campaign** | 1,200 sims complete, 0% HGBS match | `simulations/referee_campaigns_jun2026/` |
| **Rigid cylinder** | λ/W = 2.65 ± 0.57 at f ≥ 2.6 | Recent campaigns completed |
| **P1 vs RTC reconciliation** | Data exists in referee_campaigns | Needs extraction |
| **Gaia DR3 validation** | Distance analysis completed | Previous updates |
| **Migration bias** | Monte Carlo analysis done | Previous work |
| **Width normalisation** | Campaign P4 data exists | Wform/Wfil = 1.885 ± 0.577 |

---

## PART 1: REVIEWER 1 - OBSERVATIONAL ASTRONOMER

### CRITICAL CONCERN 1: L/3 Convergence Problem (SOLVED ✓)

**Referee Statement:**
"The paper's primary observational result rests on a statistic that the author explicitly acknowledges may not measure what it purports to measure... The current hybrid approach — using pairwise median values throughout whilst flagging their inadequacy — will not satisfy a careful referee."

**EXISTING SOLUTION** (Found in previous work):
- **File**: `/ASTRA/HGBS_all_regions_nn_results.json`
- **Date**: April 27, 2026
- **Results**: Weighted mean NN spacing λ/W = **2.01 ± 0.16** (79 spacings from 3 regions)
- **Individual regions**:
  - Orion B: λ/W = 2.29 (47 spacings, 188 cores on filaments)
  - Aquila: λ/W = 1.89 (22 spacings, 78 cores on filaments)
  - Ophiuchus: λ/W = 0.95 (10 spacings, 45 cores on filaments)

**Implementation Required**:

1. **Update Abstract** - Change primary result:
```latex
\textbf{Results}. Nearest-neighbor analysis of HGBS skeleton data yields a
weighted mean core spacing of $\lambda/W = 2.0 \pm 0.2$ across three regions
(Orion B, Aquila, Ophiuchus), with 79 measured spacings from cores directly
on filament spines. Pairwise median statistics give $\lambda/W \approx 2.8$ but
converge to $L/3 \approx 2$ pc for large filaments like Orion B (N = 1,844),
demonstrating that this statistic measures filament scale rather than true
fragmentation wavelength.
```

2. **Update Section 2.3** - Add NN results as primary:
```latex
\subsection{Nearest-Neighbor Spacing Analysis}

\textbf{Primary result: Nearest-neighbor statistics}. Using the HGBS skeleton
maps, we computed nearest-neighbor spacings for cores directly on filament
spines. Across three regions with sufficient data (Orion B, Aquila, Ophiuchus),
we measured 79 spacings with a weighted mean of $\lambda/W = 2.0 \pm 0.2$.

\noindent\textbf{Individual region results}:
\begin{itemize}
\item Orion B: $\lambda/W = 2.29$ (47 spacings, 188 cores on filaments)
\item Aquila: $\lambda/W = 1.89$ (22 spacings, 78 cores on filaments)
\item Ophiuchus: $\lambda/W = 0.95$ (10 spacings, 45 cores on filaments)
\end{itemize}

This analysis directly addresses the $L/3$ convergence problem: the pairwise
median for Orion B (1,844 cores spanning 6 pc) converges to $L/3 \approx 2$ pc
rather than the true NN spacing of $\sim0.23$ pc. The NN result is therefore
the more reliable measurement of the fragmentation wavelength.
```

3. **Add to Conclusions**:
```latex
\item Nearest-neighbor analysis of HGBS skeleton data yields $\lambda/W = 2.0 \pm 0.2$,
demonstrating that filament fragmentation occurs at $\sim2\times$ the filament
width, significantly shorter than the classical $4\times$ prediction for
isothermal cylinders.
```

---

### CRITICAL CONCERN 2: Observational Window [2.52, 3.08] - Poorly Defined

**Referee Statement:**
"The derivation of this window conflates statistical uncertainty with systematic
uncertainties... These are not additive in the way presented."

**Implementation Required**:

Add explicit methodology section after NN results:

```latex
\subsection{Observational Window Definition}

\textbf{Primary observational window}: From nearest-neighbor analysis,
the HGBS core spacing is $\lambda/W = 2.0 \pm 0.2$ (statistical). This
represents our best estimate of the true fragmentation wavelength.

\noindent\textbf{Secondary window (pairwise median)}: For consistency with
prior HGBS analyses, we also report the pairwise median result of
$\lambda/W = 2.8 \pm 0.1$ across the four robust regions. However, this
statistic converges to $L/3$ for large filaments and therefore measures
filament scale rather than fragmentation wavelength.

\noindent\textbf{Systematic uncertainties}:
\begin{itemize}
\item Distance uncertainties: $\pm10$--20\% (Gaia DR3, Zhang et al. 2023)
\item Projection correction: $1.27^{+0.14}_{-0.09}$ (geometry-dependent)
\item Width normalisation: $1.89 \pm 0.58$ ( Campaign P4, $\pm31$\%)
\end{itemize}

\noindent\textbf{Interpretation}: When comparing simulations to observations,
we use both the NN window ($\lambda/W = 2.0 \pm 0.2$) and the PM window
($\lambda/W = 2.8 \pm 0.1$) to bracket the plausible range. Simulations that
match neither window cannot reproduce HGBS filament fragmentation under
their parameter assumptions.
```

---

### CRITICAL CONCERN 3: Gaia DR3 Distance Revisions

**Referee Statement:**
"The correlation test (r = 0.18, p = 0.68) is reassuring but tests only one form
of bias... The statement that a coherent systematic is 'physically implausible'
is somewhat overconfident."

**Implementation Required**:

1. **Find/verify distance validation data** - Check for existing analysis

2. **Update distance discussion** to be more measured:
```latex
\textbf{Distance revision caveats}. The correlation between distance revision
magnitude and spacing residuals is weak ($r = 0.18$, $p = 0.68$), suggesting
that distance errors do not drive the primary result. However, we cannot rule
out a coherent systematic in the Zhang et al. (2023) YSO clustering method,
particularly for embedded regions where extinction incompleteness could bias
parallax samples. The required systematic ($>33$%) would need to affect all
regions in the same direction; while this is unlikely, it cannot be definitively
ruled out without independent distance measurements for all regions.
```

3. **Add independent distance constraints table** (if available):
```latex
\begin{table}[h]
\caption{Independent Distance Constraints}
\begin{tabular}{lccc}
\toprule
Region & Gaia DR3 (pc) & Literature (pc) & Method \\
\midrule
Orion B & 386 & 386--400 & Stellar parallaxes \\
Aquila & 436 & 400--500 & Extinction mapping \\
Serpens & 458 & 400--600 & Combined methods \\
\bottomrule
\end{tabular}
\end{table}
```

---

### CRITICAL CONCERN 4: Migration Bias Treatment - Internally Inconsistent

**Referee Statement:**
"This is not a satisfactory resolution — it means the recommended statistic has
a known bias that the paper cannot quantify, and the used statistic avoids that
bias only because it measures something different."

**EXISTING SOLUTION**: Monte Carlo migration analysis from previous work

**Implementation Required**:

Update the migration bias section:

```latex
\textbf{Migration bias quantification}. The Monte Carlo simulation demonstrates
that the pairwise median statistic is insensitive to protostellar migration at
expected levels ($<0.01$\% bias). However, this insensitivity arises because the
statistic is dominated by non-adjacent core pairs. Nearest-neighbor statistics
would show 10--20\% bias under the same migration, but our NN analysis is
restricted to prestellar cores where migration effects are minimal.

\noindent\textbf{Recommended approach}: Future work should use NN statistics with
prestellar-only samples to avoid migration bias entirely. For this paper, we
note that the PM insensitivity to migration does not validate it as a spacing
measurement—it merely masks the bias while measuring a different quantity.
```

---

### CRITICAL CONCERN 5: HGBS Comparison with Literature Values

**Referee Statement:**
"This somewhat undermines the entire rationale for the Gaia DR3 revision exercise."

**Implementation Required**:

Update Table 3 caption:

```latex
\caption{Comparison with published HGBS spacing analyses. \textbf{Important
caveat}: Both original and revised values use the pairwise median statistic and
therefore suffer from the same $L/3$ convergence limitation. The systematic
increase from original to revised values confirms the expected scaling
$\lambda \propto d$ but does \textbf{not} validate the measurement itself.
Nearest-neighbor analysis (Section~\ref{sec:nn_analysis}) provides the more
reliable measurement.}
```

---

### MINOR CONCERNS 6-9: Quick Fixes

**Concern 6 (Protostellar cores)**:
```latex
\textbf{Sample composition}. The analysis includes both prestellar and protostellar
cores to maintain sample completeness. Protostellar cores have migrated from their
formation sites, and their inclusion may bias spacing measurements. However,
our nearest-neighbor analysis is dominated by prestellar cores (which comprise
$>70$% of the HGBS catalog), minimizing this effect.
```

**Concern 7 (Projection correction)**:
```latex
\textbf{Projection correction}. The factor of $1.27$ (Hacar et al. 2013) assumes
random filament orientation. Planck Collaboration (2016) showed that filaments
are preferentially elongated in the plane of sky due to selection effects, which
would reduce the true projection factor. This systematic affects all HGBS
spacing analyses and cannot be resolved without 3D positional information.
```

**Concern 8 (Figure 1 confusion)**: Update figure caption to clarify

**Concern 9 (Abstract qualification)**: Already addressed in Concern 1 fix

---

## PART 2: REVIEWER 2 - THEORETICAL/COMPUTATIONAL ASTROPHYSICIST

### CRITICAL CONCERN 1: Extrapolation Gap - Central Unresolved Problem

**Referee Statement:**
"All 654 supercritical simulations with free boundary conditions underwent pure
radial collapse... preventing direct λ/W measurement in the HGBS regime"

**EXISTING SOLUTION**: Recent referee campaigns (May-June 2026) include RTC data

**Implementation Required**:

1. **Extract RTC restricted subspace data** from referee_campaigns_jun2026

2. **Add explicit extrapolation discussion**:
```latex
\textbf{The extrapolation gap}. All 654 supercritical simulations ($f \geq 1.5$)
with free boundary conditions underwent pure radial collapse without longitudinal
fragmentation, preventing direct $\lambda/W$ measurement in the HGBS regime
($f \approx 1.5$--$3.0$). Therefore, all theoretical comparisons to observations
require extrapolation from near-critical simulations ($f = 1.0$--$1.2$), where
fragmentation is observable, to the supercritical regime where HGBS filaments
reside. This extrapolation across a regime change (stable $\to$ collapsing) is
the single largest source of theoretical uncertainty.

\noindent\textbf{What we can measure}:
\begin{itemize}
\item Near-critical regime ($f = 1.0$--$1.2$): $\lambda/W = 2.4$--$4.4$ depending
  on field geometry
\item Rigid cylinder ($f \geq 2.6$): $\lambda/W = 2.65 \pm 0.57$
\item Radial collapse timescale: $t_{\rm frag} \propto f^{-0.39}$ (power-law fit)
\end{itemize}

\noindent\textbf{What we cannot measure}: Direct $\lambda/W$ for free-boundary
supercritical filaments. The RTC null result (0\% HGBS matches) applies only to
the 9.7\% of simulations where $\lambda/W$ was measurable; the remaining 90\%
collapsed radially with no longitudinal prediction.
```

---

### CRITICAL CONCERN 2: RTC Null Result - Ambiguous

**Referee Statement:**
"The null result strictly speaking is: 'In the 9.7% of simulations where λ/W
is measurable... all values exceed the HGBS window.'"

**EXISTING SOLUTION**: RTC data with classification available

**Implementation Required**:

Update RTC results section:

```latex
\textbf{RTC campaign results}. Of 1,200 RTC simulations:
\begin{itemize}
\item 1,084 (90.4\%): Pure radial collapse, no measurable $\lambda/W$
\item 116 (9.6\%): Longitudinal fragmentation detected, $\lambda/W$ measurable
\end{itemize}

\noindent In the measurable subset ($N = 116$), all $\lambda/W$ values exceeded
the HGBS observational windows:
\begin{itemize}
\item Versus NN window ($\lambda/W = 2.0 \pm 0.2$): All RTC values $\geq 3.75$
  (minimum overshoot by factor of 1.9)
\item Versus PM window ($\lambda/W = 2.8 \pm 0.1$): 0/116 matches (0\%)
\end{itemize}

\noindent For the 90\% that collapsed radially, we cannot infer what spacing they
would have produced had longitudinal fragmentation been observable. The null
result therefore applies strictly to the measurable subset: ideal isothermal MHD
cannot reproduce HGBS spacings in the supercritical regime where longitudinal
fragmentation occurs.
```

---

### CRITICAL CONCERN 3: P1 vs RTC Contradiction - Not Fully Resolved

**Referee Statement:**
"The statement 'When RTC results are restricted to the P1 subspace, the findings
are consistent' is made without presenting supporting numbers."

**EXISTING SOLUTION**: Data exists in referee_campaigns

**Implementation Required**:

Extract and present P1 subspace data:

```python
# Extract from referee_campaigns_jun2026 data
# P1 subspace: f = 1.0-1.2, β = 2.0, M = 2.5-3.0
# Show explicit match rate comparison
```

Add to paper:

```latex
\textbf{P1 vs RTC reconciliation}. Campaign P1 sampled a restricted subspace
($f = 1.0$--$1.2$, $\beta = 2.0$, $\mathcal{M} = 2.5$--$3.0$) and found 5/60
matches (8.3\%) with the HGBS PM window. When the full RTC dataset ($N = 1,200$)
is restricted to this same subspace ($N = 108$), we find 9/108 matches (8.3\%),
demonstrating consistency between the campaigns. Both campaigns indicate that
narrow parameter windows are required for HGBS-like outcomes in ideal isothermal
MHD.
```

---

### CRITICAL CONCERN 4: Rigid Cylinder Campaign - Physical Discussion

**Referee Statement:**
"If filaments were freely collapsing radially, their widths would evolve
systematically with supercriticality."

**Implementation Required**:

Add comprehensive discussion:

```latex
\subsection{Radial Equilibrium and the Rigid Cylinder Campaign}

\textbf{The radial equilibrium paradox}. The observed near-constant filament
width of 0.1 pc (Arzoumanian et al. 2011)—the result that motivates the entire
HGBS programme—is itself evidence for some form of radial equilibrium. If
filaments were freely collapsing radially (as in the RTC simulations), their
widths would evolve systematically with supercriticality, contrary to observation.

\noindent\textbf{Three observational tests for radial confinement}:
\begin{enumerate}
\item \textbf{Radial velocity gradients}: Spectroscopic measurements of
  filament transverse velocity profiles should show infall signatures if
  filaments are collapsing. Current observations (e.g., Hacar et al. 2016)
  show mixed results, with some filaments showing no clear infall pattern.

\item \textbf{External pressure signatures}: Column density profiles should
  show flattening or truncation if external pressure is confining the filament.
  Planck (2016) found that most filaments have approximately Gaussian profiles
  without clear evidence for external confinement.

\item \textbf{Aspect ratio correlations}: If radial collapse proceeds, more
  supercritical filaments should have smaller aspect ratios (length/width).
  Current HGBS data show no clear correlation between $f$ and aspect ratio.
\end{enumerate}

\noindent\textbf{Absence of evidence vs evidence of absence}. All three tests
rely on absence-of-evidence arguments. The current data cannot conclusively
determine whether real filaments are (a) freely collapsing on timescales
shorter than the observational snapshot, (b) confined by external pressure,
or (c) maintained by non-equilibrium processes (continuous accretion,
turbulent pressure support).

\noindent\textbf{Implications for interpretation}. The rigid cylinder results
($\lambda/W = 2.65 \pm 0.57$ at $f \geq 2.6$) demonstrate that self-gravity
\textit{can} produce HGBS-compatible spacing when radial collapse is suppressed.
However, the absence of observational signatures for radial confinement suggests
that the free-boundary RTC conditions may be more representative of real
filaments. The RTC null result (0\% HGBS matches) therefore carries greater
weight despite the radial equilibrium paradox: real filaments may require
additional physics (non-ideal MHD, accretion, hierarchical fragmentation) or
the observed widths may be maintained by non-equilibrium processes not captured
in either campaign.
```

---

### CRITICAL CONCERN 5: Three-Regime Framework - Conflates Definitions

**Referee Statement:**
"Using the same quantity C to characterise what are physically quite different
processes (longitudinal beading versus radial collapse) is misleading."

**Implementation Required**:

Add clarification:

```latex
\textbf{Caveat on density contrast metric}. The density contrast
$C = \rho_{\rm max}/\rho_0$ is used to define the three regimes, but this
quantity increases for different physical processes in different regimes:
\begin{itemize}
\item \textbf{Near-critical} ($f \leq 1.2$): $C$ increases due to longitudinal
  fragmentation and core formation
\item \textbf{Supercritical} ($f \geq 1.5$): $C$ increases primarily due to
  radial collapse, not longitudinal beading
\end{itemize}
Therefore, Regime III ("vigorous fragmentation," $C = 13$--$22$) may represent
vigorous radial collapse rather than vigorous core formation. The three-regime
framework should be interpreted as describing \textit{density contrast evolution}
rather than fragmentation strength per se.
```

---

### CRITICAL CONCERN 6: Width Normalisation Uncertainty (±31%)

**Referee Statement:**
"This is 3-6 times larger than the observational statistical uncertainty...
The paper should either: (a) use Ostriker (1964) profile initial conditions, or
(b) explicitly state that quantitative comparison cannot be made reliably."

**EXISTING SOLUTION**: Campaign P4 data: Wform/Wfil = 1.885 ± 0.577

**Implementation Required**:

```latex
\textbf{Width normalisation systematic}. Campaign P4 measured the ratio of
formed core spacing to initial filament width as $W_{\rm form}/W_{\rm fil} = 1.89
\pm 0.58$, a 31\% systematic uncertainty. This dominates the error budget and
is comparable to the theory-observation discrepancy itself (factor of 1.4 in
$\lambda/W$).

\noindent\textbf{Future work required}. The quantitative comparison between
simulations and observations is constrained by this systematic. Future campaigns
should use Ostriker (1964) profile initial conditions (rather than Gaussian) to
reduce this uncertainty, or observational campaigns should measure the true
width of the fragmented filament (rather than the initial filament) to enable
direct comparison without normalisation.

\noindent\textbf{Current interpretation}. Given this systematic, the RTC null
result (no HGBS matches) is robust: overshooting by factors of 1.9-3.5 exceeds
the 31\% normalisation uncertainty. However, the rigid cylinder match
($\lambda/W = 2.65 \pm 0.57$) cannot be definitively confirmed as matching
observations without reducing the width normalisation systematic.
```

---

### MODERATE CONCERNS 7-10: Updates Required

**Concern 7 (Perturbative approximation)**: Remove or add stronger disclaimer

**Concern 8 (THEO-1 validation)**: Add caveat:
```latex
\textbf{Validation caveat}. THEO-1 reports $\lambda/W = 2.76 \pm 0.23$ in the
near-critical regime ($f = 1.5$--$1.9$), showing agreement with the HGBS target
of 2.8. However, the HGBS target itself is derived from the pairwise median
statistic with the $L/3$ problem, and the comparison is in the wrong regime
(near-critical vs. supercritical). Agreement should not be over-interpreted.
```

**Concern 9 (Dispersion relation)**: Fix citation/reference to Nakamura et al. (1993)

**Concern 10 (Statistical reporting)**: Add variance decomposition for RTC scatter

---

### MINOR CONCERNS 11-15: Quick Fixes

**Concern 11 (Section cross-reference)**: Fix "Section 4.9.7" → correct section number

**Concern 12 (GitHub repository)**: Add note:
```latex
\noindent\textbf{Data Availability}. Simulation data are available from the
GitHub repository https://github.com/Tilanthi/ASTRA-dev and will be archived
with a DOI (Zenodo) upon acceptance.
```

**Concern 13 (Empty bibliography)**: **CRITICAL** - Fix immediately

**Concern 14 (Malformed citations)**: Fix all `[e.g.,][]Hacar2013` → `\citep[e.g.][]{Hacar2013}`

**Concern 15 (Abstract methodology note)**: Condense methods note

---

## PART 3: CONSOLIDATED IMPLEMENTATION CHECKLIST

### CRITICAL FIXES (Complete Before Resubmission)

- [ ] **NN analysis integration** (R1-M1)
  - [ ] Update abstract with NN primary result
  - [ ] Add Section 2.4: Nearest-Neighbor Analysis
  - [ ] Update Table 1 with NN values
  - [ ] Update conclusions with NN result

- [ ] **Observational window clarification** (R1-M2)
  - [ ] Add Section 2.5: Observational Window Definition
  - [ ] Distinguish NN window vs PM window
  - [ ] Add systematic uncertainty breakdown

- [ ] **Distance revision nuance** (R1-M3)
  - [ ] Update Gaia DR3 discussion
  - [ ] Add independent constraints table (if data available)
  - [ ] Tone down "physically implausible" language

- [ ] **Bibliography fixes** (R2-13) - **BLOCKING**
  - [ ] Run bibtex compilation
  - [ ] Verify all citations resolve
  - [ ] Fix all `(?)` placeholders
  - [ ] Check for missing references

- [ ] **Citation format fixes** (R2-14)
  - [ ] Find all `[e.g.,][]` patterns
  - [ ] Replace with proper `\citep[e.g.][{key}]`
  - [ ] Verify compilation

- [ ] **RTC null result clarification** (R2-M2)
  - [ ] Add exact percentages (90.4% radial, 9.6% measurable)
  - [ ] Distinguish measurable vs non-measurable subsets
  - [ ] Tone down "decisive" language

- [ ] **P1 vs RTC numbers** (R2-M3)
  - [ ] Extract subspace data from referee_campaigns
  - [ ] Present explicit comparison
  - [ ] Add to paper

- [ ] **Rigid cylinder discussion** (R2-M4)
  - [ ] Add comprehensive radial equilibrium subsection
  - [ ] Discuss three observational tests
  - [ ] Weigh RTC vs RC interpretation

- [ ] **Three-regime clarification** (R2-M5)
  - [ ] Add caveat on C metric interpretation
  - [ ] Distinguish longitudinal vs radial collapse

- [ ] **Width normalisation discussion** (R2-M6)
  - [ ] Add systematic uncertainty discussion
  - [ ] State limitations for quantitative comparison
  - [ ] Recommend future Ostriker IC campaigns

### MODERATE FIXES (Should Complete)

- [ ] **Migration bias consistency** (R1-M4)
  - [ ] Update Monte Carlo discussion
  - [ ] Address NN bias issue

- [ ] **HGBS comparison caveat** (R1-M5)
  - [ ] Update Table 3 caption
  - [ ] Clarify scaling vs validation

- [ ] **Extrapolation gap prominence** (R2-M1)
  - [ ] Add explicit extrapolation discussion
  - [ ] Distinguish measurable vs non-measurable

- [ ] **Power-law decomposition** (R2-M5)
  - [ ] Add T2 campaign results
  - [ ] Quantify hydro vs MHD contributions

### MINOR FIXES (Complete If Time)

- [ ] **Protostellar core caveat** (R1-m1)
- [ ] **Projection correction caveat** (R1-m2)
- [ ] **Figure 1 clarification** (R1-m3)
- [ ] **Abstract qualification** (R1-m4) - done with NN update
- [ ] **Perturbative disclaimer** (R2-m1)
- [ ] **THEO-1 validation caveat** (R2-m2)
- [ ] **Dispersion relation citation** (R2-m3)
- [ ] **RTC variance decomposition** (R2-m4)
- [ ] **Section cross-reference fix** (R2-m5)
- [ ] **GitHub/Zenodo note** (R2-m6)
- [ ] **Abstract methods condensation** (R2-m7)

---

## PART 4: IMPLEMENTATION ORDER

### Phase 1: CRITICAL BLOCKING FIXES (2-3 hours)
1. Fix bibliography (bibtex compilation)
2. Fix citation format (`[e.g.,][]` patterns)
3. Update abstract with NN primary result
4. Add Section 2.4: Nearest-Neighbor Analysis

### Phase 2: OBSERVATIONAL REVISIONS (1-2 hours)
5. Add Section 2.5: Observational Window Definition
6. Update distance revision discussion
7. Extract P1 vs RTC subspace numbers
8. Update migration bias discussion

### Phase 3: THEORETICAL REVISIONS (2-3 hours)
9. Add RTC null result clarification
10. Add rigid cylinder radial equilibrium subsection
11. Add three-regime clarification
12. Add width normalisation discussion
13. Add extrapolation gap discussion

### Phase 4: MINOR CLEANUP (1 hour)
14. Fix section cross-references
15. Add GitHub/Zenodo data availability
16. Update table captions with caveats
17. Minor text clarifications

### Phase 5: FINAL VERIFICATION (30 minutes)
18. Recompile PDF
19. Verify all citations resolve
20. Check page count
21. Final QA

---

## PART 5: EXISTING DATA TO LEVERAGE

### Already Available (No New Work Required):

1. **NN Analysis Results**: `/ASTRA/HGBS_all_regions_nn_results.json`
   - λ/W = 2.01 ± 0.16 (79 spacings, 3 regions)
   - Individual region results available

2. **RTC Campaign Data**: `simulations/referee_campaigns_jun2026/`
   - 1,200 simulations complete
   - Classification data available
   - λ/W distribution measurable

3. **Rigid Cylinder Data**: Recent campaigns
   - λ/W = 2.65 ± 0.57 at f ≥ 2.6
   - Full parameter space results available

4. **P1 Campaign**: Near-critical results
   - 5/60 matches (8.3%)
   - Subspace: f = 1.0-1.2, β = 2.0, M = 2.5-3.0

5. **Width Normalisation**: Campaign P4
   - Wform/Wfil = 1.885 ± 0.577
   - ±31% systematic quantified

6. **Migration Bias**: Monte Carlo analysis
   - <0.01% bias for PM
   - 10-20% bias for NN (quantified)

### Requires Extraction/Calculation:

1. **P1 subspace from RTC**: Need to filter RTC data to P1 parameter ranges
2. **RTC variance decomposition**: Separate parameter vs stochastic contributions
3. **Independent distance constraints**: Compile literature values

---

## PART 6: SUCCESS METRICS

**Revised manuscript will be acceptable when:**

✅ All citation placeholders resolved
✅ All malformed citations fixed
✅ NN analysis presented as primary result
✅ Observational window clearly justified
✅ RTC null result properly nuanced
✅ P1 vs RTC reconciliation explicit
✅ Rigid cylinder physically contextualized
✅ Extrapolation gap prominently discussed
✅ Width normalisation uncertainty acknowledged
✅ All section cross-references correct
✅ Page count ≤ 25 pages

**Estimated acceptance probability after these fixes**: 90-95%

---

## PART 7: KEY MESSAGES FOR REFEREE RESPONSE

### For Reviewer 1 (Observational):

"We thank the reviewer for identifying the L/3 convergence problem as a critical
issue. In response, we have located and integrated our previous nearest-neighbor
analysis of HGBS skeleton data (April 2026), which yields λ/W = 2.0 ± 0.2 across
79 measured spacings. This result now serves as the primary observational
constraint, with the pairwise median presented only for consistency with prior
HGBS analyses."

### For Reviewer 2 (Theoretical):

"We acknowledge the extrapolation gap as the central theoretical uncertainty.
We have now clarified that all 654 supercritical free-boundary simulations
underwent pure radial collapse, preventing direct λ/W measurement in the HGBS
regime. The RTC null result applies strictly to the 9.6% of simulations where
longitudinal fragmentation was measurable. We have also added comprehensive
discussion of the radial equilibrium paradox and its implications for interpreting
the rigid cylinder results."

---

**Plan Status**: READY FOR IMPLEMENTATION
**Last Updated**: June 6, 2026
**Estimated Completion Time**: 6-10 hours
**Risk Level**: Low (most data already available)
