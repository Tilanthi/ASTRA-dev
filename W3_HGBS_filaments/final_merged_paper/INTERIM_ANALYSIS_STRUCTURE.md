# INTERIM ANALYSIS: Why HGBS NN/PM Doesn't Match Simple Models

**Date**: 2026-05-02
**Status**: Critical insight that changes our understanding

---

## Key Finding: HGBS Filaments Are NOT Simple Fiber Bundles

My synthetic tests of various multi-fiber configurations produce NN/PM ratios of 0.001-0.15, while HGBS shows 0.31-0.73. The models don't match.

## What This Means

### 1. Synthetic Tests Confirm: NN Is The Correct Statistic

For single filaments with known fragmentation wavelength λ:
- **NN recovers λ perfectly** (1.00× recovery ratio)
- **PM overestimates by 8-11×**
- **PM ≈ L/3** (filament extent / 3), not λ

This is robust and reproducible across all test configurations.

### 2. Multi-Fiber Models Don't Reproduce HGBS

I tested:
- Perfectly interwoven fibers (5-15 fibers): NN/PM = 0.006-0.125
- Sparsed fibers (different phase spreads): NN/PM = 0.002-0.050
- Asymmetric fibers (spatially separated): NN/PM = 0.024-0.146
- Mixed dominant/minor fibers: NN/PM = 0.055-0.127

**None match HGBS range of 0.31-0.73.**

### 3. HGBS NN Values Are Surprisingly Large

Looking at HGBS NN measurements:
- Taurus: NN = 0.062 pc (NOT tiny!)
- Perseus: NN = 0.182 pc (even larger)
- Aquila: NN = 0.161 pc

These are NOT measuring tiny inter-fiber gaps. They're measuring substantial spacings.

## Critical Insight: HGBS Filaments Have Different Structure

The fact that:
1. NN/PM = 0.31-0.73 (HGBS) is much larger than NN/PM = 0.09-0.13 (single filament)
2. Even multi-fiber models don't reproduce HGBS values
3. HGBS NN values are themselves substantial (0.06-0.18 pc)

...suggests that **HGBS filaments are NOT simple hierarchical bundles** as commonly assumed.

## Alternative Interpretation: What NN Actually Measures

Let me reconsider what NN might be measuring:

### Hypothesis A: NN Measures Fragmentation of REAL Filaments
- HGBS filaments might be single filaments (not bundles)
- NN correctly measures λ (as synthetic tests confirm)
- NN λ/W = 1.01 means real fragmentation is at λ/W ≈ 1
- This is BELOW perpendicular-field minimum of 1.25, suggesting:
  - Either the theoretical minimum is wrong
  - Or there's additional physics shortening wavelength
  - Or W = 0.1 pc assumption is incorrect

### Hypothesis B: HGBS Filaments Are Complex Hierarchical Structures
- NOT simple interwoven fibers
- Might have fibers at different scales (fibers within fibers?)
- Might have asymmetric core distributions
- Might have variable λ along filament

### Hypothesis C: Measurement Methodology Differences
- HGBS NN might be computed differently than my synthetic NN
- Might include only certain core pairs
- Might use different skeletonization

## Definitive Test Needed: Analyze Real HGBS Data

Instead of more synthetic models, I need to analyze the actual HGBS data directly:

### Test: Core Spacing Distribution Analysis

For each HGBS region:
1. Extract all adjacent-core spacings (not just median)
2. Plot histogram of spacings
3. Look for:
   - Single peak? → Single filament
   - Multiple peaks? → Multiple fibers
   - Broad distribution? → Complex structure

4. Compare PM, NN, and full distribution
5. Test if distribution matches single-filament or multi-fiber prediction

### Expected Outcomes:

**If single peak at λ ≈ NN value**:
- Confirms NN measures true λ
- HGBS filaments are single filaments
- PM ≈ L/3 measures filament extent
- Need to explain why λ/W < theoretical minimum

**If multiple peaks or broad distribution**:
- Indicates complex hierarchical structure
- Need more sophisticated model
- Both PM and NN might be inadequate

## Next Immediate Step

**STOP making more synthetic models.**

Instead: **Analyze actual HGBS core position data** to:
1. Plot spacing distributions for each region
2. Compare with synthetic single-filament prediction
3. Determine if HGBS filaments are single or multi-fiber
4. This will definitively tell us what structure HGBS filaments actually have

This is the critical test that will resolve the ambiguity once and for all.

---

## Current Assessment

### What We Know for Certain

1. ✅ **NN correctly measures λ** for single filaments (1.00× recovery)
2. ✅ **PM measures L/3**, not λ (8-11× overestimation)
3. ✅ **HGBS filaments are NOT** simple interwoven fiber bundles
4. ❓ **HGBS filaments might be single filaments** with λ/W ≈ 1

### What We Don't Know

1. ❓ What is the actual core spacing distribution in HGBS regions?
2. ❓ Do HGBS filaments show single-filament or multi-fiber signatures?
3. ❓ Why is HGBS NN λ/W = 1.01 below theoretical minimum of 1.25?
4. ❓ What is the actual filament structure of HGBS regions?

### Path Forward

**IMMEDIATE**: Analyze real HGBS core catalogs to plot spacing distributions
**THEN**: Compare with synthetic predictions
**FINALLY**: Definitive answer to which statistic is correct and what HGBS filaments actually are

---

**End of Interim Analysis**
