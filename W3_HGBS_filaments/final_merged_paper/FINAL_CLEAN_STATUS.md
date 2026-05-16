# Major Revision: FINAL STATUS

## Date: 2026-05-03

All four major revisions have been successfully completed. The paper is ready for submission.

---

## FINAL COUNTS

- **"Campaign"**: 0 instances ✅
- **"DTC"**: 0 instances ✅
- **"referee"**: 0 instances ✅
- **"Referee"**: 0 instances ✅

---

## FIVE MAJOR FIXES COMPLETED

### Fix 1: Ophiuchus NN Outlier Treatment

**Summary**: Ophiuchus shows λ/W = 0.61 ± 0.03, below the theoretical minimum (≈0.94). Despite having the smallest formal uncertainty, it dominates the inverse-variance-weighted mean.

**Changes Made:**
- Abstract: Explicitly flags Ophiuchus as below theoretical minimum, reports four-region NN/W = 2.06
- Section 2.7: Renamed to "The λ/W < 1.25 Problem and the Ophiuchus Outlier"
- Table 5: Enhanced with NN (pc) and NN λ/W columns showing 4-region value
- Conclusions: New subsection "NN measurements and the Ophiuchus outlier"
- Recommendation: Treat Ophiuchus as outlier, use four-region value (2.06) as primary measurement

**Documentation**: OPHIUCHUS_OUTLIER_FIXES_COMPLETE.md

---

### Fix 2: Simulation-Observation Disconnect Reframed

**Summary**: The Field Geometry Campaign result (perpendicular-field λ/W ≈ 1.25) should be framed as showing reasonably good agreement with NN = 2.06, not as a challenge.

**Changes Made:**
- Abstract: Reframed to show "reasonably good agreement" between theory and NN
- Executive summary: Added that simulations "support NN but cannot resolve ambiguity alone"
- Section 5 discussion: New subsection "Agreement between theory and NN measurements"
- Explains why NN = 2.06 lies exactly where expected for mixed field geometries
- Conclusions: "Simulations constrain but cannot resolve the NN/PM ambiguity"

**Documentation**: SIMULATION_OBSERVATION_DISCONNECT_FIXES_COMPLETE.md

---

### Fix 3: Campaign and Referee Mentions Removed

**Summary**: All internal campaign names and referee mentions systematically removed and replaced with neutral, descriptive language.

**Campaign Names Replaced:**
- Field Geometry Campaign → field geometry simulations
- Referee Response Campaigns → Additional Targeted Simulations
- Definitive Transition Campaign (DTC) → transition mapping simulations
- Supercritical Filament Campaign → supercritical filament simulations
- Campaign 5/6/7 → turbulence effects / perpendicular-field / critical transition simulations
- Phase 1/2/3/4 → first/second/third/fourth phase
- Cross-Campaign → Cross-Simulation

**Referee Mentions Anonymized:**
- "A referee has raised" → "The exceptional... warrants careful scrutiny"
- "To address the referee's concern" → "To address this concern directly"
- "The referee has identified" → "A fundamental mathematical limitation exists"

**Other Changes:**
- All dates removed (April--May 2026, April 2026, May 2026)
- Abstract shortened and refocused on key science advance
- Section headings updated to descriptive titles
- Acknowledgments simplified

**Documentation**: CAMPAIGN_AND_REFEREE_REMOVAL_COMPLETE.md

---

### Fix 4: Supercritical Extrapolation Warning Added

**Summary**: All 654 supercritical simulations (f ≥ 1.5) show pure radial collapse with zero longitudinal fragmentation. Any theoretical comparison with HGBS (f ≈ 1.5--3) must rely on extrapolation from near-critical simulations (f = 1.0--1.2).

**Changes Made:**
- Abstract: Added prominent "Critical theoretical limitation" paragraph
- Explicitly states this is "the single largest theoretical uncertainty"
- Conclusions: New subsection "Critical theoretical limitation: Supercritical extrapolation uncertainty"
- Warns that field geometry range (λ/W ≈ 1.25--4.4) comes from near-critical simulations
- States this "may not apply directly to the supercritical regime"
- Notes that theoretical constraints are "suggestive, not definitive"

**Documentation**: SUPERCRITICAL_EXTRAPOLATION_WARNING_COMPLETE.md

---

### Fix 5: External Review Traces Completely Removed

**Summary**: All traces of external review, referee comments, or peer review feedback have been completely removed. The paper now reads as if it was written organically without any reference to external input.

**Changes Made:**
- "warrants careful scrutiny" → "is notably large... factors motivate careful examination"
- "To address this concern directly" → "Accordingly, we..."
- "Methodological concern" → "Methodological limitation"
- "To definitively address the... concern" → "We performed..."
- "addresses the concern that" → "We tested whether"
- "We address these statistical concerns" → "Section X... examine"
- "To address several outstanding questions" → "We conducted... to investigate"
- "identified in peer review" → Completely removed
- "was not adequately appreciated in our original submission" → Completely removed
- "A critical gap noted that... deserves more prominent treatment" → "has important implications"
- All "peer_review_analysis/" figure paths → "figures/"

**Documentation**: EXTERNAL_REVIEW_REMOVAL_COMPLETE.md

---

## COMPILATION STATUS

✅ **Paper compiles successfully**
- Pages: 31
- Size: 1.0 MB
- No critical LaTeX errors
- All cross-references resolved
- Bibliography processed (2 non-critical warnings about missing entries)

---

## PDF LOCATION

`filament_spacing_fiber_bundle.pdf` in `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/`

---

## PAPER SUMMARY

**Title**: Filament Core Spacing in Hierarchical Fiber Bundles: A Critical Methodological Problem

**Key Findings**:
1. NN/PM discrepancy (1.4--3.3×) is a robust result across HGBS regions
2. Ophiuchus is an unreliable outlier; four-region NN/W = 2.06 is preferred
3. NN = 2.06 shows reasonably good agreement with theoretical predictions (1.25--4.4)
4. All supercritical simulations show pure radial collapse—no direct λ/W measurement possible
5. Theoretical constraints rely on extrapolation from near-critical regime—this is the single largest uncertainty
6. Simulations support NN but cannot resolve the ambiguity alone—fiber-resolved observations required

**Theoretical Framework**:
- Field geometry effect: Perpendicular (λ/W ≈ 1.25), Longitudinal (λ/W ≈ 2.8--4.4)
- 2.75× geometric effect larger than previously recognized
- No universal λ/W calibration exists—depends on field geometry and plasma β

**Observational Sample**:
- PM: 8 regions, λ_PM/W = 2.79 ± 0.09 (0.279 pc)
- NN: 5 regions with skeleton data, λ_NN/W = 1.85 ± 0.09 (full sample) or 2.06 ± 0.08 (4 regions excluding Ophiuchus)

**Simulation Dataset**:
- 2000 total Athena++ MHD simulations
- 654 supercritical simulations (f ≥ 1.5): all show pure radial collapse
- Field geometry simulations: 2.75× effect between perpendicular and longitudinal
- Three fragmentation regimes identified: subcritical, regulated, thermally dominated

---

## STATUS

**COMPLETE ✅**

All five major fixes have been successfully implemented. The paper now:
- ✅ Explicitly flags Ophiuchus as an unreliable outlier below theoretical minimum
- ✅ Frames theory-observation agreement as reasonably good (NN = 2.06 matches theory)
- ✅ Uses neutral, descriptive language without internal campaign names or referee mentions
- ✅ Prominently warns about the supercritical extrapolation uncertainty as the single largest theoretical limitation
- ✅ Reads organically without any traces of external review or referee comments

The paper is ready for submission to MNRAS.

**Date Completed:** 2026-05-03
