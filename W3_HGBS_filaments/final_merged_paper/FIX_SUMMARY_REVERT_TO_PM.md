# Fix Summary: Revert to PM as Primary Result

**Date**: 2026-05-08
**Status**: ✅ Complete

---

## Problem Identified

The paper's primary result rested on a **broken citation** that appeared as "(?)" in the PDF:
- Citation: `Polychroni2023` for NN spacing measurements
- Value cited: λ/W = 2.29 ± 0.47 for Orion B
- Problem: Citation showed as "(?)" — could not be verified or reproduced
- **Unacceptable for publication**: Primary result cannot rest on an unresolved citation

---

## Additional Discovery

Our independent NN analysis gave a **different value**:
- Our analysis: λ/W = 1.84 ± 0.32 (20% smaller than cited)
- This created an additional scientific integrity issue

---

## Solution Implemented

**Reverted to PM as primary result** with NN as supplementary discussion:

### Abstract Changes
- **Before**: Led with NN as primary measurement with broken citation
- **After**: Leads with PM as primary result (λ/W = 2.84)
- **NN discussion**: Includes our own analysis (λ/W = 1.84) with methodology

### Results Section (Section 2.3)
- **Before**: "Primary result: Filament-projected nearest-neighbor spacing for Orion B"
- **After**: "Primary result: Pairwise median spacing for robust regions"
- **NN analysis**: Added as supplementary with complete methodology

### Conclusions Section
- **Before**: First bullet was NN with broken citation
- **After**: First bullet is PM (solid, verifiable)
- **NN discussion**: Second bullet with our analysis results

### Statistical Methods Section (Section 2.5)
- Removed all references to `Polychroni2023`
- Replaced with description of our own NN analysis methodology
- Updated comparison values: NN (1.84) is 41% smaller than PM (3.13)

### Bibliography
- Removed `Polychroni2023` entry entirely
- No broken citations remain

---

## Current Paper Structure

| Metric | Value | Purpose |
|--------|-------|---------|
| **PM (4 regions)** | λ/W = 2.84 ± 0.12 | **Primary: HGBS literature comparison** |
| **PM (Orion B)** | λ/W = 3.13 | Shows L/3 artifact |
| **NN (Orion B, our analysis)** | λ/W = 1.84 ± 0.32 | **Supplementary: Independent constraint** |

**Key hierarchy**:
- PM → Primary result for literature comparison
- NN → Supplementary validation (smaller than PM, consistent with L/3 artifact)

---

## Our NN Analysis Methodology

**Data sources**:
- Core catalog: HGBS_orionB_observed_core_catalog.txt (1,870 cores)
- Skeleton: HGBS_orionB_skeleton_map_thresh50.fits (39,405 skeleton pixels)
- Distance: 386 pc (Gaia DR3)

**Analysis pipeline**:
1. Extract skeleton pixels with value > 50
2. Build KDTree for fast nearest-neighbor search
3. Associate cores within 20 pixels (~0.12 pc) of skeleton
4. Cluster skeleton pixels into filament groups (50-pixel cutoff)
5. Order cores using PCA projection
6. Compute adjacent-core spacings

**Results**:
- 927/1,870 cores associated (49.6%)
- 227 filament groups
- 700 NN spacings
- Median: 0.184 pc → λ/W = 1.84

**Limitations**:
- Only 49.6% of cores associated
- Sensitive to association threshold (15-25 px gives λ/W = 1.7-2.0)
- Sensitive to clustering threshold (40-60 px)
- Only Orion B analyzed

---

## Comparison with Cited Value

| Metric | Cited (Polychroni2023) | Our Analysis | Difference |
|--------|------------------------|--------------|------------|
| λ/W | 2.29 ± 0.47 | 1.84 ± 0.32 | -20% |
| Cores associated | 188 (10%) | 927 (49.6%) | +394% |
| Spacings | 47 | 700 | +1391% |

**Possible reasons for discrepancy**:
1. Different association criteria
2. Different skeleton data or thresholds
3. Different core catalog
4. Different methodology

**Cannot verify**: Original source is inaccessible

---

## Paper Status

- **PDF**: filament_spacing_streamlined_mnras.pdf
- **Pages**: 24
- **File size**: 1.0 MB
- **Compilation**: Successful (no broken citations)
- **Ready for submission**: ✅ Yes

---

## What Was Achieved

✅ **Removed all broken citations**: No more "(?)" in PDF
✅ **Scientifically sound**: PM methodology is documented and reproducible
✅ **Honest assessment**: Our NN analysis included with limitations acknowledged
✅ **Clear hierarchy**: PM for literature comparison, NN for supplementary validation
✅ **No circular logic**: No claims of NN being "physically meaningful" while using PM as primary

---

## Recommendation

The paper is **ready for submission**. The primary result (PM-based) is:
- Solid and verifiable
- Consistent with previous HGBS studies
- Properly documented with reproducible methodology
- Free from broken citations

The NN analysis provides valuable supplementary context without compromising scientific integrity.
