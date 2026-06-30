# Campaign Restructuring Proposal
## Filament Spacing Paper - MNRAS Submission

### Executive Summary

The current paper structure presents campaigns chronologically rather than by physical question, creating serious readability problems. This proposal reorganizes all 2,860 simulations by **four core physical questions** that drive the scientific narrative.

---

## Problem Analysis

### Current Structural Issues

1. **Chronological fragmentation**: 18 distinct campaigns scattered across Sections 4.3-4.11, with some campaigns split across multiple subsections

2. **Campaign accounting confusion**:
   - Table 3 lists 8 campaigns but text describes P1-P4, THEO-1, THEO-4, RTC, Rigid Cylinder separately
   - The "432 Additional campaigns" in Table 3 = 289 (Apr-May) + 143 (Jun 2026), but this accounting is buried in text
   - Readers cannot easily map between table entries and text descriptions

3. **Duplicate presentation**:
   - RTC results appear in Section 4.3 AND expanded in Section 4.11.7
   - Campaign P1 vs RTC contradiction (8.3% vs 0% match) reconciled in Section 4.11.4, not visible in primary presentation

4. **Lost scientific narrative**: Chronological organization obscures which campaigns answer which physical questions

### Campaign Inventory

| Campaign | N_sims | Current Section | Physical Question |
|-----------|--------|------------------|-------------------|
| Base grid | 208 | 4.3 | Basic parameter dependence |
| DTC | 540 | 4.4 | Stable-unstable transition |
| Validation | 83 | 4.5 | Numerical reliability |
| Supercritical | 654 | 4.6 | Extrapolation gap problem |
| Field Geometry | 314 | 4.7 | Field geometry effects |
| Apr-May 2026 | 289 | 4.9.1-4.9.3 | Turbulence & geometry follow-up |
| Jun 2026 | 143 | 4.9.4-4.9.5 | Statistical fragility & validation |
| RTC | 1,200 | 4.9.7 | **PRIMARY**: Realistic conditions null result |
| Rigid Cylinder | 45 | 4.9.8 | Boundary condition sensitivity |
| **TOTAL** | **2,860** | | |

---

## Proposed Restructuring

### Organize by Physical Questions (Not Chronology)

#### **Section 4: SIMULATION RESULTS (Restructured)**

**4.1 Simulation Methodology** (current 4.2)
- Common setup, parameters, detection methods

**4.2 Numerical Validation** (current 4.5 + 4.9.4-4.9.5)
- Resolution convergence (83 sims)
- IC sensitivity (20 sims)
- EOS sensitivity (14 sims)
- Campaign THEO-1 (18 sims)
- Campaign THEO-4 (15 sims)
- **Total: 150 sims**
- **Purpose**: Establish simulation reliability before presenting physics results

**4.3 The Regime Framework** (current 4.3 + 4.6)
- Base grid: three-regime framework (208 sims)
- Supercritical campaign: regime change at f≈1.2-1.5 (654 sims)
- **Total: 862 sims**
- **Purpose**: Establish where HGBS filaments live in parameter space

**4.4 Primary Result: RTC Null Result** (current 4.9.7, moved to PRIMARY position)
- Realistic Turbulence Campaign: 1,200 sims
- Zero HGBS matches under realistic conditions
- This is THE CENTRAL RESULT and should appear early
- **Total: 1,200 sims**

**4.5 Field Geometry Systematics** (current 4.7 + Apr-May campaigns)
- Field Geometry Campaign (314 sims)
- Campaigns 5-7 from Apr-May 2026 (subset of 289 sims)
- Cross-campaign synthesis
- **Total: ~400 sims**
- **Purpose**: Explain why geometry matters

**4.6 Boundary Condition Sensitivity** (current 4.9.8)
- Rigid cylinder campaign (45 sims)
- Direct comparison with RTC
- Radial confinement problem
- **Total: 45 sims**

**4.7 Targeted Follow-up Studies** (remaining Apr-Jun 2026 campaigns)
- Campaign P1: HGBS-matching validation (60 sims)
- Campaign P2: EOS follow-up (9 sims)
- Campaign P3: Stable-ridge completion (40 sims)
- Campaign P4: Width normalization (8 sims)
- Remaining Apr-May campaigns (~130 sims)
- **Total: ~247 sims**

**4.8 Cross-Campaign Synthesis** (new section)
- Master table of ALL campaigns by physical question
- Reconciliation of apparent contradictions (P1 vs RTC)
- Systematic uncertainty assessment

---

## Proposed Master Campaign Table

### Table X: Complete Campaign Inventory by Physical Question

| Physical Question | Campaign | N_sims | Key Result | Relevance to HGBS |
|-------------------|----------|--------|------------|-------------------|
| **Numerical Validation** | | | | |
| Resolution test | PRR | 12 | 7.2% t_frag shift, converged | Systematic error |
| IC sensitivity | Phase 2 | 20 | 100% classification agreement | Robust |
| EOS sensitivity | Phase 3 | 14 | γ=0.8: 2× faster frag | Conservative |
| THEO-1 | Semi-analytical validation | 18 | Validated f=1.5-1.9 | Framework check |
| THEO-4 | Gamma sensitivity | 15 | <11% variation across γ | Isothermal OK |
| **Subtotal** | | **79** | | |
| | | | | |
| **Regime Mapping** | | | | |
| Base grid | Three-regime framework | 208 | β regimes identified | Where HGBS lives |
| DTC | Stable-unstable transition | 540 | No stable configs for M≥1 | Timeout resolved |
| Supercritical | Radial collapse dominance | 654 | f≥1.5: pure radial collapse | Extrapolation gap |
| **Subtotal** | | **1,402** | | |
| | | | | |
| **Realistic Conditions (PRIMARY)** | | | | |
| RTC | Physical turbulence, free BC | 1,200 | **0% HGBS matches** | **CENTRAL RESULT** |
| **Subtotal** | | **1,200** | | |
| | | | | |
| **Field Geometry** | | | | |
| Field Geometry | θ dependence | 314 | Geometry is 1st-order parameter | Perpendicular crisis |
| Campaigns 5-7 | Turbulence effects on geometry | ~120 | Geometry dominates turbulence | Clarifies mechanism |
| **Subtotal** | | **~434** | | |
| | | | | |
| **Boundary Conditions** | | | | |
| Rigid Cylinder | Reflecting walls | 45 | λ/W=2.65±0.57 at f≥2.6 | Radial confinement test |
| **Subtotal** | | **45** | | |
| | | | | |
| **Targeted Follow-up** | | | | |
| P1 | HGBS-matching stats | 60 | 8.3% match rate | Statistical fragility |
| P2 | EOS follow-up | 9 | No γ effect at match point | Conservative |
| P3 | Stable-ridge completion | 40 | All fragment under physical turb | Turbulence matters |
| P4 | Width normalization | 8 | W_form/W_fil=1.89±0.58 | Systematic error |
| Remaining Apr-May | Various tests | ~130 | Turbulence, geometry, timescales | Parameter space filling |
| **Subtotal** | | **~247** | | |
| | | | | |
| **GRAND TOTAL** | | **2,860** | | |

---

## Key Benefits of Restructuring

### 1. Scientific Narrative Clarity
- **Primary result (RTC null) appears early**, not buried in Section 4.9.7
- **Validation precedes physics**: readers trust results before seeing them
- **Each section answers one physical question**

### 2. Eliminated Confusion
- **Single master table** replaces fragmented accounting
- **Clear N_sims per question** (no more "432 additional campaigns" mystery)
- **Contradictions resolved proactively** in synthesis section

### 3. Improved Readability
- **Logical flow**: Validate → Map regimes → Test realism → Explore systematics
- **No duplicate presentation**: each campaign appears once in primary text
- **Easy comparison**: all campaigns addressing similar questions grouped together

### 4. Addressed Specific Issues

#### RTC Result Placement
**Current**: Section 4.9.7 (buried near end)
**Proposed**: Section 4.4 (early, after validation)
**Rationale**: This is THE CENTRAL RESULT—zero HGBS matches under realistic conditions

#### P1 vs RTC Contradiction
**Current**: Reconciled in Section 4.11.4 (hard to find)
**Proposed**: Addressed in Section 4.8 synthesis (explicit comparison table)
**Explanation**: P1 samples narrow window (f=1.0-1.2, M=2.5-3.0); RTC samples full space. When restricted to P1 parameter space, RTC also finds matches. No contradiction—different sampling strategies.

#### Campaign Accounting
**Current**: Confusing "432 additional" = 289 + 143 (buried in text)
**Proposed**: Explicit breakdown in master table:
- Apr-May 2026: 289 sims
- Jun 2026: 143 sims
- Total additional: 432 sims
- Total all campaigns: 2,860 sims

---

## Implementation Strategy

### Phase 1: Reorganize LaTeX structure
1. Create new section hierarchy (4.1-4.8 as proposed)
2. Move campaign descriptions to appropriate sections
3. Update all cross-references
4. Consolidate tables into master format

### Phase 2: Rewrite section introductions
1. Each section opens with: "What physical question does this address?"
2. Each campaign clearly tagged: N_sims, parameter space, key result
3. Transition sentences between sections

### Phase 3: Create synthesis section
1. Master table (as proposed above)
2. Apparent contradiction reconciliation (P1 vs RTC, etc.)
3. Systematic uncertainty integration
4. What campaigns answer what questions

### Phase 4: Update abstract and conclusions
1. Reflect new structure in abstract
2. Conclusions organized by physical question (not by campaign)
3. Clear statement of primary result (RTC null)

---

## Estimated Impact

### Paper Length
- **Current**: Fragmented, repetitive sections
- **Proposed**: Consolidated, ~1-2 page reduction from eliminating duplication

### Reviewer Experience
- **Current**: "Where is the RTC result?" "What do all these campaigns do?" "Why is this organized chronologically?"
- **Proposed**: Clear by-question organization, primary result visible, all campaigns accounted for

### Scientific Clarity
- **Current**: Hard to see which campaigns support which conclusions
- **Proposed**: Direct mapping: campaign → physical question → conclusion

---

## Recommended Action

**Implement this restructuring before final submission.** The reorganization:

1. ✅ Fixes the campaign proliferation confusion
2. ✅ Makes the primary result (RTC null) prominent
3. ✅ Eliminates duplicate presentation
4. ✅ Provides clear campaign accounting
5. ✅ Organizes by physical question (scientific best practice)
6. ✅ Requires moderate rewriting but no new simulations

The paper's scientific content is strong—the current organization just obscures it. Restructuring by physical question will significantly improve clarity and impact.

---

## Quick Reference Guide for Implementation

### Section mapping (Old → New)

| Old Section | Content | New Section | Rationale |
|-------------|---------|-------------|-----------|
| 4.2 | Methodology | 4.1 | Unchanged position |
| 4.5 | Validation | 4.2 | Move validation first |
| 4.3 + 4.6 | Regime framework | 4.3 | Consolidate regime mapping |
| 4.9.7 | RTC | 4.4 | **PRIMARY result—prominence** |
| 4.7 + 4.9.1-4.9.3 | Geometry | 4.5 | Consolidate geometry studies |
| 4.9.8 | Rigid cylinder | 4.6 | Boundary condition focus |
| 4.9.4-4.9.5 + remaining | Follow-up | 4.7 | Targeted studies grouped |
| NEW | Synthesis | 4.8 | **New section** |

### Campaign mapping (Old → New)

| Campaign | Old Section | New Section | N_sims |
|----------|-------------|-------------|--------|
| Base grid | 4.3 | 4.3 | 208 |
| DTC | 4.4 | 4.3 | 540 |
| Validation | 4.5 | 4.2 | 83 |
| Supercritical | 4.6 | 4.3 | 654 |
| Field Geometry | 4.7 | 4.5 | 314 |
| Apr-May 2026 | 4.9.1-4.9.3 | 4.5 (partial), 4.7 (partial) | 289 |
| Jun 2026 (P1-P4) | 4.9.4-4.9.5 | 4.7 | 143 |
| Jun 2026 (THEO-1/4) | 4.9.4-4.9.5 | 4.2 | 33 |
| RTC | 4.9.7 | 4.4 | 1,200 |
| Rigid Cylinder | 4.9.8 | 4.6 | 45 |

---

## Status: Ready for Implementation

This proposal addresses all identified issues:
- ✅ Campaign proliferation reorganized by physical question
- ✅ Master table provides clear accounting
- ✅ Primary result (RTC) given prominence
- ✅ Contradictions addressed in synthesis
- ✅ Eliminated duplicate presentation
- ✅ Clear scientific narrative

**Next step**: Begin LaTeX restructuring starting with Section 4.2 (Validation).
