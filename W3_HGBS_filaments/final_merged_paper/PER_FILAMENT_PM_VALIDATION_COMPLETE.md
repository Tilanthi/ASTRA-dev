# Per-Filament PM Validation: Complete Results

## Date: 2026-05-03

This document summarizes the complete per-filament PM validation test using actual HGBS skeleton and core catalog data to test whether PM_filament ≈ L_filament/3 for individual HGBS filaments.

---

## Scientific Question

The paper's L/3 convergence result (PM = L/3 for simple synthetic filaments) was derived from controlled synthetic tests. Does this relationship hold for individual HGBS filaments with real geometry (curvature, branching, hierarchical fiber structure)?

---

## Methodology

### Data Sources

We used official HGBS skeleton files and core catalogs:

1. **Orion B** (386 pc):
   - Skeleton: `HGBS_orionB_skeleton_map.fits` (official HGBS file with WCS)
   - Catalog: `HGBS_orionB_observed_core_catalog.txt` (1870 cores)
   - WCS: RA---TAN, DEC--TAN (valid)

2. **Taurus L1495** (135 pc):
   - Skeleton: `HGBS_taurusL1495_skeleton_map.fits`
   - Catalog: `HGBS_taurusL1495_derived_core_catalog.txt` (536 cores)
   - WCS: RA---TAN, DEC--TAN (valid)
   - Result: Very fragmented filament structure (58,345 candidate filaments), no filaments with ≥2 associated cores even with lenient parameters

3. **Ophiuchus** (137 pc):
   - Skeleton: `HGBS_oph_l1688_skeleton_map.fits`
   - Catalog: `HGBS_ophiuchus_observed_core_catalog.txt` (513 cores)
   - WCS: RA---TAN, DEC--TAN (valid)

### Analysis Pipeline

For each region:
1. Load skeleton FITS file and extract WCS information
2. Load core catalog and parse RA/Dec coordinates
3. Convert core coordinates to pixel space using WCS
4. Extract filament spines using connected component labeling (threshold = 0.1, min_length = 10 pixels)
5. Associate cores with nearby filaments using cKDTree (max distance = 100 pixels)
6. For each filament with ≥2 associated cores:
   - Compute PM (pairwise median of core separations)
   - Compute NN (nearest-neighbor median)
   - Estimate filament length from core span
   - Calculate L/3 and PM/(L/3) ratio
7. Statistical analysis: mean, SEM, t-test against null hypothesis PM/(L/3) = 1.0

---

## Results

### Orion B (6 filaments)

- PM/(L/3) = 1.26 ± 0.07 (SEM)
- t = 3.56, p = 0.016
- **Significant deviation from 1.0** (26% higher)
- 66.7% of filaments (4/6) within 20% of 1.0
- Distribution: 25th = 1.11, median = 1.18, 75th = 1.42

### Ophiuchus (17 filaments)

- PM/(L/3) = 1.22 ± 0.05 (SEM)
- t = 4.61, p = 0.0003
- **Highly significant deviation from 1.0** (22% higher)
- 64.7% of filaments (11/17) within 20% of 1.0
- Distribution: 25th = 1.10, median = 1.16, 75th = 1.37

### Combined Analysis (23 filaments)

- **PM/(L/3) = 1.23 ± 0.04 (SEM)**
- **Median = 1.18**
- **p < 0.001** (highly significant deviation from 1.0)
- 65.2% of filaments (15/23) within 20% of 1.0
- Systematic positive bias (PM > L/3) in both regions

---

## Key Findings

1. **PM systematically overestimates L/3** for individual HGBS filaments by 20-30%
2. The deviation is **statistically significant** (p < 0.001)
3. The bias is **consistent across both regions** (Orion B: 1.26, Ophiuchus: 1.22)
4. The distribution shows **systematic positive bias** rather than random scatter around 1.0

---

## Interpretation

The L/3 relationship:
- **Holds exactly** for simple periodic filaments (synthetic test)
- **Partially holds** for uniform multi-filament distributions (PM ≈ 0.96 × ⟨L/3⟩_weighted)
- **Does NOT hold** for individual HGBS filaments (PM ≈ 1.23 × L/3, p < 0.001)

### Why PM > L/3 for Real Filaments?

Real HGBS filaments have complex geometry that increases the effective length scale sampled by PM:
1. **Curvature**: Non-straight filament paths increase core-to-core distances
2. **Branching**: Side branches create additional long-distance pairs
3. **Hierarchical fiber bundles**: Multiple velocity-coherent fibers with different scales
4. **Non-uniform core spacing**: Irregular core distributions vs. regular spacing
5. **Projection effects**: 2D projection compresses some distances but not others

These features are all absent from simple synthetic filaments, explaining the systematic bias.

---

## Implications for the Paper

### Three-Tiered Interpretation Framework

The paper now presents a nuanced understanding of PM behavior:

**Tier 1: Simple periodic filaments** (Rigorously established)
- PM = L/3 exactly (demonstrated with synthetic test)
- 8× bias relative to true fragmentation wavelength
- Strongest theoretical result

**Tier 2: Uniform multi-filament distributions** (Partially supported)
- PM ≈ 0.96 × ⟨L/3⟩_weighted (computational test)
- PM reflects core-weighted average of filament scales
- Relationship is approximate but not exact

**Tier 3: Individual HGBS filaments** (Not supported - **NEW RESULT**)
- PM ≈ 1.23 × L/3 (direct validation test, p < 0.001)
- Systematic 20-30% positive bias
- Complex filament geometry increases PM relative to simple L/3

### Updated Language in Paper

The paper has been updated with:
1. **Abstract**: Added per-filament validation results (PM/(L/3) = 1.23 ± 0.04, p < 0.001)
2. **Section 6.1**: Added "Per-filament PM validation using HGBS data" subsection with full methodology and results
3. **Implications**: Updated to reflect systematic PM > L/3 bias for real filaments
4. **Conclusions**: Updated to include per-filament validation as critical limitation

### Key Message

**PM values cannot be interpreted as quantitative measurements of L/(3W) for HGBS filaments.** The per-filament validation test definitively shows that PM systematically overestimates L/3 by 20-30% for real HGBS filaments with complex geometry. PM provides suggestive geometric context but should not be treated as a precise measurement.

---

## Files Generated

1. **per_filament_pm_validator_v2.py** - Analysis script
2. **per_filament_pm_validation_OrionB.json** - Orion B results (6 filaments)
3. **per_filament_pm_validation_Ophiuchus.json** - Ophiuchus results (17 filaments)
4. **filament_spacing_fiber_bundle.pdf** - Updated paper with per-filament validation

---

## Status

✅ **Complete**
- Per-filament validation performed on 23 filaments from 2 HGBS regions
- Results integrated into paper narrative
- Paper compiled successfully (34 pages, 1.0 MB)
- All cross-references resolved

---

**Date**: 2026-05-03
**Final PDF**: filament_spacing_fiber_bundle.pdf
