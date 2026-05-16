# PM vs NN Discrepancy Resolution

## Date: 2026-05-08

## Problem

The paper claimed that nearest-neighbor (NN) statistics "validated filament-ordered structure" while using pairwise median (PM) values ($\lambda/W = 2.84$) as the primary result. This was misleading because:

1. The NN measurement gives a **different value** ($\lambda/W = 2.29$ for Orion B) than PM ($\lambda/W = 3.13$)
2. The paper never reported or discussed this discrepancy
3. The "validation" was circular — it only proved ordering exists, not that PM measures $\lambda$

## Solution Implemented: Option B (Modified)

Updated the paper to present **both measurements explicitly** and acknowledge the PM artifact honestly:

### 1. Abstract Changes (Lines 27-28)

**Before**: Claimed NN > PM "opposite of L/3 convergence prediction"

**After**: 
- Reports both PM and NN measurements for Orion B
- States NN is 27% smaller than PM, **consistent with L/3 artifact**
- Quotes constrained range: $\lambda/W = 2.3$--$2.8$

### 2. Primary Results Section (Line 132)

**Added**:
- Distinguishes $\lambda_{\rm PM}$ (overall scale) from $\lambda_{\rm NN}$ (true wavelength)
- Reports Orion B NN value: $\lambda_{\rm NN}/W = 2.29 \pm 0.47$
- States both measurements give sub-Jeans values
- Clarifies true wavelength likely closer to NN result

### 3. Section 2.5 (Statistical Methods) — Complete Rewrite (Lines 201-224)

**Before**: Generic discussion of L/3 problem with no data

**After**:
- **Direct comparison table** for Orion B:
  - PM: $\lambda/W = 3.13$ ($0.313$ pc)
  - NN: $\lambda/W = 2.29 \pm 0.47$ ($0.229$ pc)
  - Difference: 27% (NN smaller)
- **Physical interpretation**:
  - NN measures true fragmentation wavelength
  - PM measures overall scale of core distributions
  - 27% difference consistent with L/3 convergence artifact
- **Honest assessment**: "The true fragmentation wavelength likely lies closer to the NN-based result of $\lambda/W \approx 2.3$"
- **Cites Polychroni et al. 2023** for Orion B NN analysis

### 4. Conclusions Section (Line 747)

**Before**: "NN is larger than PM — opposite of L/3 bias prediction"

**After**:
- Reports NN is **27% smaller** than PM
- States this is **consistent with expected L/3 artifact**
- Quotes constrained range: $\lambda/W = 2.3$--$2.8$
- Clarifies NN provides more reliable constraint

### 5. Bibliography Addition

Added **Polychroni et al. 2023** reference for Orion B skeleton-based NN analysis.

## Key Changes in Scientific Interpretation

| Aspect | Before | After |
|--------|--------|-------|
| Primary measurement | $\lambda/W = 2.84$ (PM only) | $\lambda/W = 2.3$--$2.8$ (constrained range) |
| NN interpretation | "Validation" of PM | Independent measurement, more reliable |
| L/3 artifact | Dismissed (claimed NN > PM) | **Confirmed** (NN 27% smaller than PM) |
| True wavelength | Implied to be PM value | Closer to NN value ($\approx 2.3$) |

## What This Achieves

1. **Scientific honesty**: Acknowledges PM artifact and provides both measurements
2. **Maintains core conclusion**: Both PM and NN give sub-Jeans values
3. **Strengthens paper**: NN measurement is physically meaningful
4. **Removes circular logic**: No longer claims NN "validates" PM
5. **Provides uncertainty range**: $\lambda/W = 2.3$--$2.8$ reflects current knowledge limits

## Limitations Acknowledged

1. Orion B NN analysis used only 188/1,844 cores (10%)
2. Comprehensive NN analysis requires raw HGBS skeleton data (not publicly available)
3. Only one region (Orion B) has published NN measurements
4. True wavelength could be closer to 2.3 or 2.8 depending on region

## Final Status

✅ **Paper updated with Option B (Modified)**
✅ **Both PM and NN measurements reported explicitly**
✅ **L/3 convergence artifact acknowledged and confirmed**
✅ **Circular validation logic removed**
✅ **Honest uncertainty range provided**
✅ **PDF compiled successfully**: 24 pages, 1.0 MB

## Impact on Paper

- **Primary conclusion unchanged**: Sub-Jeans spacing confirmed by both methods
- **Uncertainty increased**: From ±0.12 to range of 2.3-2.8 (±17%)
- **Scientific integrity improved**: Honest about PM limitations
- **Future work clarified**: Need comprehensive NN analysis for all regions
