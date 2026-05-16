# Multi-Filament L/3 Validation: Options and Analysis

## Date: 2026-05-03

This document outlines three approaches to address the L/3 validation gap: computational tests, data analysis, and language revision.

---

## THE PROBLEM

**The L/3 convergence result (8× bias)** is derived from a single-filament test (N=30 cores, L=9.6 pc). However:

1. HGBS regions contain **hundreds of filaments of varying lengths**
2. The **effective L is ill-defined** for multi-filament regions
3. **Multi-fiber synthetic tests fail to match HGBS observations**
4. The paper uses L/3 convergence to reinterpret HGBS PM values with **more confidence than warranted**

---

## OPTION 1: Multi-Filament PM Convergence Test (Computational)

### Test Design

**Objective:** Determine what PM converges to for a realistic distribution of filaments.

**Method:**
1. Generate a synthetic region with realistic filament distribution:
   - Number of filaments: 50--200 (matching HGBS regions like Orion B: 273 filaments)
   - Filament lengths: Log-normal distribution with L ∈ [1 pc, 15 pc] (matching HGBS)
   - Cores per filament: Poisson(λ) where λ ∈ [3, 20] depending on L
   - Each filament: cores with regular spacing λ_true (0.2--0.4 pc)

2. Compute PM for the pooled region (all cores from all filaments)

3. Compare PM to:
   - Mean(L_i)/3 (average of individual filament L/3 values)
   - Weighted mean(L_i)/3 (weighted by cores per filament)
   - L_eff/3 where L_eff is some effective length
   - True λ_true (the fragmentation wavelength)

**Key Questions:**
- Does PM converge to a predictable value for multi-filament regions?
- Is PM related to some effective L_eff, or does it behave differently?
- How does the bias compare to the single-filament case (8×)?

**Expected Outcome:**
If PM ≈ mean(L_i)/3 for multi-filament regions, this would validate the L/3 interpretation.
If PM behaves differently, this would highlight the need for language revision.

---

## OPTION 2: Per-Filament PM Validation Using HGBS Data

### Test Design

**Objective:** Validate the L/3 relationship on individual HGBS filaments.

**Method:**
1. For each HGBS region (Orion B, Aquila, Perseus, Taurus):
   - Extract individual filaments from DisPerSE skeleton data
   - For filaments with N ≥ 10 cores:
     - Compute PM_filament (pairwise median for that filament alone)
     - Compute L_filament (filament length from skeleton)
     - Test PM_filament ≈ L_filament/3

2. Analyze:
   - Distribution of PM_filament / (L_filament/3) ratios
   - Mean and scatter
   - Filament-to-filament variation

**Key Questions:**
- Does the L/3 relationship hold for individual HGBS filaments?
- What is the scatter around the L/3 prediction?
- Are there systematic deviations based on filament properties (length, core count)?

**Data Availability:**
We have access to:
- HGBS core catalogs (published)
- HGBS filament skeleton data (DisPerSE outputs)
- Core-filament associations (published)

**Expected Outcome:**
If most filaments show PM ≈ L/3 with small scatter, this validates the L/3 interpretation at the filament level.
If filaments show large deviations or systematic trends, this reveals limitations of the L/3 framework.

---

## OPTION 3: Substantially Soften the Language

If computational validation is not feasible or shows inconclusive results, the paper should be revised to reflect honest uncertainty:

### Required Language Changes

**Abstract:**
- Remove: "PM converges to L/3 (filament geometry)"
- Replace with: "PM converges to L/3 for simple periodic filaments in synthetic tests, but we cannot determine what PM measures in multi-filament regions"

**Section 6.1 (Discussion):**
- Remove: "should now be interpreted as L/(3W)"
- Replace with: "may represent geometric characterizations in simple cases, but we cannot definitively interpret PM for hierarchical multi-filament systems"

**Conclusions:**
- Add explicit statement: "The L/3 interpretation is demonstrated for single filaments but not established for multi-filament regions. The validation gap remains: we have not determined what PM measures in complex hierarchical systems."

---

## RECOMMENDATION

**Primary approach:** Do **Option 1** (computational test) first. This is the most direct way to address the validation gap.

**If Option 1 shows PM ≈ mean(L_i)/3:** Then we can strengthen the L/3 interpretation with proper qualification (it holds on average for multi-filament regions).

**If Option 1 shows different behavior:** Then we must do **Option 3** (language revision) and explicitly acknowledge that PM behavior in multi-filament regions is fundamentally different from the single-filament case.

**Option 2** (per-filament validation) could be done in parallel as additional supporting evidence if data access allows.

---

## NEXT STEPS

1. **Immediate:** Create synthetic multi-filament generator script
2. **Run test:** Generate 100 realizations with 50--200 filaments each
3. **Analyze:** Determine what PM converges to
4. **Decision:** Based on results, either strengthen or revise L/3 interpretation
5. **If feasible:** Add per-filament validation using HGBS data

Would you like me to proceed with Option 1 (computational multi-filament test) or would you prefer to start with Option 3 (language revision)?
