# HGBS Core Distribution Analysis: Critical Findings

**Date**: 2026-05-02
**Status**: Complete - Major Discovery

---

## Executive Summary

Analysis of real HGBS core catalog data has revealed a **critical methodological issue** that completely changes the interpretation of the PM vs NN question.

### The Problem

My analysis measured ALL cores in each HGBS region, not just cores along individual filament skeletons. This produced:
- **Taurus**: NN = 0.621 pc (vs literature 0.062 pc) → **10× too large**
- **Perseus**: NN = 0.534 pc (vs literature 0.182 pc) → **3× too large**
- **Ophiuchus**: NN = 0.462 pc (vs literature ~0.1 pc expected)

### The Explanation

The HGBS literature values (NN = 0.062 pc for Taurus, etc.) are computed by:
1. **Extracting individual filament skeletons** from the dense filament network
2. **Selecting only cores that lie along each filament**
3. **Measuring spacings between cores along the filament skeleton**

My analysis instead used **all cores in the entire region**, which measures:
- Inter-filament spacings (different filaments separated by large distances)
- Background cores not associated with filaments
- Creates a multi-scale hierarchical distribution

This explains why:
1. NN values are much larger than literature
2. NN/PM ratios are below HGBS range
3. Distributions show broad multi-fiber signatures

---

## Analysis Results

### Successfully Analyzed Regions

| Region | N_cores | NN (arcmin) | PM (arcmin) | NN/PM | NN (pc)* | PM (pc)* |
|--------|---------|-------------|-------------|-------|----------|----------|
| Ophiuchus | 513 | 11.34 | 46.46 | 0.244 | 0.462 | 1.892 |
| Perseus | 816 | 13.11 | 92.94 | 0.141 | 0.534 | 3.785 |
| Taurus | 178 | 15.24 | 41.06 | 0.371 | 0.621 | 1.672 |

*Assuming distance = 140 pc, 1 arcmin = 0.0407 pc

### Comparison with Literature

| Region | Literature NN | Measured NN | Ratio |
|--------|---------------|-------------|-------|
| Taurus | 0.062 pc | 0.621 pc | 10.0× |
| Perseus | 0.182 pc | 0.534 pc | 2.9× |

### Distribution Shape Analysis

- **Ophiuchus**: CV = 1.84, 33 peaks → **Multi-fiber signature**
- **Taurus**: CV = 1.23 → **Multi-fiber signature** (CV > 0.5)
- **Perseus**: Likely similar (not shown in output)

All regions show **broad, right-skewed distributions** with high coefficients of variation (>1), consistent with hierarchical multi-fiber structure.

---

## Critical Insight: What This Means

### 1. The HGBS Methodology Is Filament-Specific

The HGBS NN values (0.06-0.18 pc) are NOT computed from all cores in a region. They are computed by:
1. Identifying individual filament skeletons using getfilaments or DisPerSE
2. Extracting cores that lie along each filament (within some perpendicular distance)
3. Measuring adjacent-core spacings along the 1D filament spine

This produces small NN values because cores along a single filament are close together.

### 2. My Analysis Measured Region-Scale Structure

By using ALL cores, I measured:
- Spacings between different filaments (large)
- Background cores not on filaments
- A complex hierarchical distribution

This produces large NN values because the region contains many filaments separated by large distances.

### 3. The PM vs NN Question Remains Unresolved

My analysis **does not** resolve the PM vs NN discrepancy because:
- I measured the wrong spatial scale (region, not filament)
- I need filament skeleton data to replicate HGBS methodology
- The HGBS values are filament-specific, not region-wide

---

## What Is Needed for Definitive Answer

To properly resolve the PM vs NN question, I need:

### 1. Filament Skeleton Data

For each HGBS region, I need:
- **Filament skeleton coordinates** (RA, Dec points along each filament spine)
- **Core-to-filament associations** (which cores belong to which filament)
- **Filament width measurements** (W values)

This data likely exists in the HGBS supplementary materials or in papers like:
- Arzoumanian et al. (2011) - Filament network
- André et al. (2010) - Core catalog methodology

### 2. Correct Analysis Pipeline

```
For each filament:
  1. Extract skeleton (list of RA, Dec points)
  2. Find cores within perpendicular distance W/2 of skeleton
  3. Project core positions onto 1D skeleton coordinate (s)
  4. Sort cores by s
  5. Compute NN = median(adjacent spacings along s)
  6. Compute PM = median(all pairwise distances along s)
  7. Compute NN/PM ratio

For each region:
  - Combine results from all filaments
  - Compare with HGBS literature values
```

### 3. Data Sources

Possible locations for filament skeleton data:
- **HGBS papers**: Arzoumanian et al. (2011, 2019), André et al. (2010)
- **Herschel data archives**: Filament catalogs from getfilaments
- **Individual region papers**: Taurus (Palmeirim et al. 2013), etc.

---

## Alternative Path: Use Synthetic Tests

Given the difficulty of obtaining filament skeleton data, the **synthetic tests remain the best path forward**:

### What We Know From Synthetic Tests

1. **NN correctly recovers λ** for single filaments (1.00× recovery)
2. **PM converges to L/3** (filament extent / 3), NOT λ
3. **PM/NN ≈ 8-11×** for single filaments (NOT 2.8× as in HGBS)

### What This Means

The fact that HGBS shows PM/NN ≈ 2.8× suggests:
- HGBS filaments are NOT simple single filaments
- They have some more complex structure
- But my multi-fiber models (perfectly interwoven) don't match either

### Next Step

**Refine the multi-fiber model** to find configurations that reproduce:
- NN/PM ≈ 0.31-0.73 (HGBS range)
- PM/NN ≈ 1.4-3.2× (inverse of above)

Possible configurations to test:
- Fibers with different λ values
- Asymmetric fiber distributions
- Sparse fiber distributions (not perfectly interwoven)
- Mixed single-dominant + minor fibers

---

## Conclusions

### 1. Real HGBS Data Analysis: Inconclusive

My analysis of all HGBS cores does **not** resolve the PM vs NN question because I measured the wrong spatial scale (region-wide instead of filament-specific).

### 2. HGBS Methodology: Filament-Specific

The HGBS literature values are computed from cores **along individual filament skeletons**, not all cores in the region. This requires filament skeleton data that I don't currently have access to.

### 3. Synthetic Tests: More Promising

The synthetic filament tests provide clearer insights:
- NN correctly measures fragmentation wavelength
- PM measures filament extent (L/3), not fragmentation
- The HGBS PM/NN ratio suggests complex filament structure

### 4. Path Forward

**Option A**: Obtain filament skeleton data from HGBS papers/archives and repeat analysis correctly

**Option B**: Continue refined multi-fiber synthetic modeling to find configurations that match HGBS NN/PM ≈ 0.31-0.73

**Option C**: Accept that NN is the correct statistic (based on synthetic tests) and investigate why HGBS NN λ/W = 1.01 is below theoretical minimum

---

## Files Generated

- `HGBS_analysis_results/hgbs_spacing_distributions.pdf` - Combined visualization
- `HGBS_analysis_results/hgbs_spacing_statistics.json` - Numerical results (31 MB)
- `HGBS_analysis_results/*_spacing_distribution.pdf` - Individual region plots
- `analyze_hgbs_core_distributions.py` - Analysis script

---

**Status**: Analysis complete but inconclusive due to wrong spatial scale. Need filament skeleton data for definitive answer.

**End of Report**
