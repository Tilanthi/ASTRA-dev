# Comprehensive Referee Analysis and Implementation Plan

**Date**: June 6, 2026
**Paper**: Fragmentation of Interstellar Filaments: Complete HGBS Analysis and MHD Simulations
**Reviewers**: Two expert reviewers (observational astronomer & theoretical astrophysicist)
**Status**: Major revision required

---

## Executive Summary

The referees have identified significant structural and conceptual problems that must be addressed before publication. While Phase 1 and Phase 2 revisions have been completed, **additional work is required** to fully address all referee concerns.

### Key Finding from Reviewer 1

"The paper has significant structural problems that must be addressed before publication."

### Key Finding from Reviewer 2

"The central quantitative comparison between the simulations and observations is compromised by the L/3 convergence problem."

---

## Complete Referee Concern Matrix

| # | Concern | Reviewer | Priority | Current Status | Required Action |
|---|---------|----------|----------|----------------|-----------------|
| **R1-M1** | L/3 undermines quantitative core | R1 | CRITICAL | Partially addressed | Need complete restructure |
| **R1-M2** | Observational window poorly justified | R1 | CRITICAL | NOT addressed | Must add justification |
| **R1-M3** | Distance revision methodology | R1 | MAJOR | Partially addressed | Needs enhancement |
| **R1-M4** | HGBS comparison potentially misleading | R1 | MAJOR | NOT addressed | Must fix |
| **R1-m1** | Migration bias ~10% in error budget | R1 | MINOR | NOT addressed | Should add |
| **R1-m2** | Hierarchical caveat about random positions | R1 | MINOR | Partially addressed | Needs explicit statement |
| **R1-m3** | Abstract NN citations missing | R1 | MINOR | NOT addressed | Must add |
| **R2-M1** | RTC null result overstates decisiveness | R2 | CRITICAL | Partially addressed | Needs nuance |
| **R2-M2** | Extrapolation gap deserves prominence | R2 | CRITICAL | Addressed | Needs more prominence |
| **R2-M3** | Perpendicular-field crisis elevated | R2 | CRITICAL | Addressed | Needs more development |
| **R2-M4** | P1 vs RTC reconciliation incomplete | R2 | CRITICAL | Check status | May be truncated |
| **R2-M5** | Rigid cylinder caveats needed | R2 | MAJOR | Addressed | May need strengthening |
| **R2-m1** | Dispersion relation convergence criterion | R2 | MINOR | NOT addressed | Should add |
| **R2-m2** | Power-law scaling vs linear theory | R2 | MINOR | Partially addressed | Needs comparison |
| **R2-m3** | Width normalisation factor discrepancy | R2 | MINOR | Partially addressed | Needs explanation |
| **R2-m4** | DTC re-runs in inventory table | R2 | MINOR | NOT addressed | Should add |

---

## Detailed Analysis by Category

### CRITICAL CONCERNS (Must Address)

#### R1-M1: L/3 Problem Undermines Quantitative Core

**Referee Statement:**
"The L/3 problem undermines the quantitative core of the paper... The paper needs either (a) to obtain and analyse the nearest-neighbour statistics properly before proceeding to the theoretical comparison, or (b) to be reframed explicitly as a methodological paper."

**Current Status (from IMPLEMENTATION_PROGRESS.md):**
- Phase 1 addressed: "Abstract restructured for L/3 prominence"
- L/3 mentioned prominently in abstract
- Section 2.3 enhanced with L/3 clarification
- BUT: Paper still uses pairwise median for all quantitative comparisons

**What Referee Actually Wants:**
The referee is asking for a fundamental choice:
- Option A: Do proper nearest-neighbour analysis (requires HGBS skeleton data - not available)
- Option B: Reframe as methodological paper showing why NN analysis is essential

**Required Action:**
The paper must be reframed as Option B. This means:
1. **Abstract**: State that primary contribution is methodological - demonstrating L/3 problem
2. **Title**: May need adjustment to reflect methodological nature
3. **Conclusions**: Emphasize that the paper's value is identifying the statistical problem
4. **All quantitative comparisons**: Must be explicitly labelled as preliminary/contingent

#### R1-M2: Observational Window [2.52, 3.08] Poorly Justified

**Referee Statement:**
"The observational window [2.52, 3.08] is used as the primary test criterion for 1,200 RTC simulations, yet its derivation from the pairwise median statistic is acknowledged to be problematic."

**Current Status:**
- No explicit justification for this specific window
- Derived from pairwise median but methodology not explained

**Required Action:**
Add explicit section explaining:
1. How [2.52, 3.08] was derived (weighted mean ± bootstrap uncertainty)
2. Why this window is problematic (L/3 convergence)
3. What the true observational window would be with proper NN analysis
4. How the RTC null result should be interpreted against BOTH windows

#### R2-M1: RTC Null Result Overstates Decisiveness

**Referee Statement:**
"The RTC null result is presented as more decisive than the systematic uncertainties warrant... The paper should present the null result against both observational benchmarks: against the pairwise median window AND against the nearest-neighbour estimate."

**Current Status:**
- RTC described as "decisive zero-match rate"
- Only compared against pairwise median window [2.52, 3.08]

**Required Action:**
Modify RTC presentation to:
1. Remove "decisive" language
2. Present comparison against BOTH observational windows:
   - Pairwise median: λ/W ≈ 2.8 (window [2.52, 3.08])
   - Nearest-neighbour: λ/W ≈ 2.0-2.2
3. State that RTC overshoots by:
   - ~1.25× relative to pairwise median
   - ~1.7-1.9× relative to nearest-neighbour
4. Acknowledge uncertainty about which observational benchmark is correct

#### R2-M2: Extrapolation Gap Deserves More Prominence

**Referee Statement:**
"The extrapolation gap is the dominant systematic and deserves more prominence."

**Current Status:**
- Addressed in Phase 1 (abstract and conclusions)
- Referee still says needs more prominence

**Required Action:**
The extrapolation gap needs to be elevated to equal status with RTC null result:
1. It should appear in the FIRST paragraph of the Abstract, not later
2. It should be in the FIRST bullet of Conclusions
3. It should have its own subsection in Discussion (already exists, but may need enhancement)

#### R2-M3: Perpendicular-Field Crisis Should Be Elevated

**Referee Statement:**
"This is actually a more severe and direct observational constraint... The paper should explicitly note this and discuss whether there is any combination of parameters that could simultaneously reproduce the observed λ/W."

**Current Status:**
- Phase 1 addressed: "Field geometry crisis" added to abstract and conclusions
- Referee says needs elevation

**Required Action:**
Elevate perpendicular-field crisis to co-equal status with RTC and extrapolation gap:
1. Add explicit discussion: Is there ANY parameter combination that works?
2. Show that width-normalised perpendicular (λ/W ≈ 2.0-2.4) is BELOW both NN (2.0-2.2) and pairwise median (2.8)
3. Explain why this is MORE severe than longitudinal-field problem

#### R2-M4: P1 vs RTC Reconciliation Incomplete

**Referee Statement:**
"The paper cuts off mid-sentence... the reader is not told what the RTC match rate is when restricted to the P1 subspace—this comparison is essential."

**Current Status:**
- Need to verify if this is still truncated in current version

**Required Action:**
1. Find the truncated sentence in Section 4.7.1 or 4.8.1
2. Complete the sentence
3. Add explicit RTC match rate in P1 subspace (if data available)

---

### MAJOR CONCERNS (Should Address)

#### R1-M3: Distance Revision Methodology

**Referee Statement:**
"The paper does not address the specific concern about the Zhang et al. (2023) YSO clustering method in deeply embedded regions... the assertion that a coherent 33% bias is 'physically implausible' is stated rather than demonstrated."

**Required Action:**
1. Tabulate all independent distance constraints explicitly (as referee suggests)
2. Change "physically implausible" to a more reasoned argument
3. Acknowledge that correlated errors cannot be ruled out entirely

#### R1-M4: HGBS Comparison Potentially Misleading

**Referee Statement:**
"The comparison with published HGBS values (Table 3) is potentially misleading. The apparent systematic increase from original to revised values... does not validate the measurement—it only confirms that λ ∝ d as expected."

**Current Status:**
Table 3 exists in paper, referee says it's misleading

**Required Action:**
Modify Table 3 caption or add explanatory note:
1. Clarify that both original and revised values use pairwise median
2. State that increase only confirms λ ∝ d (expected)
3. Does NOT validate the measurement itself
4. Does NOT address L/3 convergence problem

#### R2-M5: Rigid Cylinder Caveats

**Referee Statement:**
"The paper is admirably cautious about what reflecting walls can and cannot show... should be summarised more forcefully in the Conclusions."

**Required Action:**
Strengthen the conclusions bullet on rigid cylinder to be more definitive about observational counter-argument.

---

### MINOR CONCERNS (Nice to Address)

#### R1-m1: Migration Bias in Error Budget

**Required Action:**
Add ~10% systematic uncertainty from Monte Carlo migration bias to Table 5 (systematic error budget).

#### R1-m2: Hierarchical Caveat

**Required Action:**
Add explicit statement: "The 1/√N_fibre compression scaling assumes random fibre positions within the filament cross-section, which may not be physically well-motivated."

#### R1-m3: Abstract NN Citations

**Required Action:**
Add citations to "published nearest-neighbour analyses report λ/W ≈ 2.0–2.2" statement in Abstract. Likely candidates: Hacar et al. 2013, 2018; others.

#### R2-m1: Dispersion Relation Convergence

**Required Action:**
Add statement of convergence criterion used: "The 0.3% threshold is the maximum acceptable difference for numerical convergence across the full parameter range kR = 0.1–10."

#### R2-m2: Power-Law Scaling vs Linear Theory

**Required Action:**
Add comparison with linear theory prediction t_frag ∝ (f-1)^(-1/2). State whether simulation scaling is consistent or diverges.

#### R2-m3: Width Normalisation Discrepancy

**Required Action:**
Explain why W_form/W_fil = 1.885 rather than theoretical 1.6. Is this due to Gaussian vs. Ostriker IC mismatch?

#### R2-m4: DTC Re-runs in Inventory

**Required Action:**
Add note to Table 4 inventory: "15 STABLE classifications from DTC re-runs (April 2026) converted to FRAG outcomes."

---

## Implementation Strategy

Given that:
- Current page count: 25 pages (AT MNRAS LIMIT)
- Cannot add substantial content without removing something
- Many additions are required

### Trimming Requirements

To make room for required additions, estimated 2-3 pages of existing content must be removed/condensed.

**Candidates for trimming:**
1. Campaign P1-P4 descriptions (already condensed in Phase 2)
2. DTC stochastic zone discussion
3. Three-regime framework detailed description
4. Some cross-campaign synthesis

### Implementation Order

**Phase 3 (Critical):**
1. Check for truncated sentence (R2-M4)
2. Add observational window justification (R1-M2)
3. Modify RTC null result presentation (R2-M1)
4. Elevate extrapolation gap further (R2-M2)
5. Elevate perpendicular-field crisis (R2-M3)
6. Add HGBS comparison clarification (R1-M4)

**Phase 4 (Major):**
7. Distance revision enhancement (R1-M3)
8. Rigid cylinder conclusions strengthening (R2-M5)
9. Add migration bias to error budget (R1-m1)

**Phase 5 (Minor):**
10. Add NN citations to abstract (R1-m3)
11. Add convergence criterion (R2-m1)
12. Add power-law vs linear theory comparison (R2-m2)
13. Add width normalisation explanation (R2-m3)
14. Add DTC re-run note to inventory (R2-m4)

---

## Success Criteria

The paper must address ALL CRITICAL concerns before resubmission:

- [ ] L/3 problem: Paper reframed as methodological contribution
- [ ] Observational window: Explicit justification with comparison to NN
- [ ] RTC null result: Presented against BOTH observational benchmarks
- [ ] Extrapolation gap: Co-equal prominence with RTC in abstract/conclusions
- [ ] Perpendicular-field crisis: Elevated to co-equal status
- [ ] P1 vs RTC: Truncated sentence completed, subspace comparison explicit

Additionally:
- [ ] Page count ≤ 25 pages
- [ ] All MAJOR concerns addressed
- [ ] As many MINOR concerns as space allows

---

## Summary

The referees have identified real structural issues that go beyond what was addressed in Phases 1-2. The paper needs a fundamental reframing as a methodological contribution rather than a definitive measurement paper. This reframing, combined with the required additions, will require strategic content trimming to maintain the 25-page limit.

**Estimated total work**: 15-20 hours of careful revision
**Risk level**: High (fundamental reframing required)
**Recommendation**: Treat this as a Major Revision, not Minor

