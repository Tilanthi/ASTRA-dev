# Internal Contradiction Fix Summary

## Date: 2026-05-01

## Problem Identified

The paper contained a **fundamental internal contradiction**:
- **Abstract and Results**: Presented NN spacing as primary result for all 8 HGBS regions (5,695 cores)
- **Section 2.5**: Claimed "We do not have access to the raw HGBS core position data required to compute nearest-neighbour spacing"

These statements were mutually contradictory and undermined the entire observational pillar of the paper.

---

## Root Cause

Section 2.5 was written during an earlier phase of the paper when:
1. We had not yet computed NN spacing for the full HGBS sample
2. We were relying on pairwise median statistics
3. We genuinely lacked access to methodology for computing NN spacing

When we later computed direct NN measurements (using `compute_full_nn_FINAL.py`), we updated the abstract, results, and conclusions throughout the paper **but failed to update Section 2.5** to reflect the new methodology.

---

## Changes Made

### 1. Section 2.5 (Lines 225-227) - COMPLETELY REWRITTEN

**OLD TEXT (contradiction):**
```
Data access limitation. We do not have access to the raw HGBS core position data
required to compute nearest-neighbour spacing statistics for the full sample.
The published HGBS catalogues provide only derived quantities... This prevents
us from directly addressing the L/3 convergence concern with our own data.
```

**NEW TEXT (accurate):**
```
Direct nearest-neighbor measurements for all 8 HGBS regions. To directly address
the L/3 convergence concern, we have computed nearest-neighbor spacing measurements
for all 8 HGBS regions using the published HGBS catalogues. These catalogues provide
core positions in right ascension and declination (J2000 epoch), which are sufficient
to compute 2D nearest-neighbor distances on the plane of the sky. We constructed a
2D KD-tree from the core coordinates and queried each core's nearest neighbor,
converting angular separations to physical distances using region-specific Gaia DR3
distances. This yields 5,695 nearest-neighbor spacing measurements across 8 regions
(3,932 cores in 4 robust regions), representing the complete HGBS sample analyzed
in this work.
```

**Key changes:**
- ✓ Removed false claim about "no access" to data
- ✓ Explained methodology (2D KD-tree on RA/Dec coordinates)
- ✓ Stated sample size (5,695 measurements, 3,932 cores in robust regions)
- ✓ Referenced Gaia DR3 distances
- ✓ Made clear this is DIRECT measurement, not estimation

---

### 2. Migration Bias Section (Line 98) - UPDATED

**OLD TEXT:**
```
Nearest-neighbor spacing would be far more sensitive to migration bias, but we
lack access to the raw core position data needed to compute it. We therefore
acknowledge this as a critical limitation... we cannot quantify this effect
with the published HGBS catalogues.
```

**NEW TEXT:**
```
Nearest-neighbor spacing would be far more sensitive to migration bias. While
we have computed NN spacing measurements for all 8 HGBS regions (Table 1),
assessing migration bias would require separating prestellar from protostellar
cores and comparing their NN spacing distributions—a more detailed analysis
beyond the scope of the current paper. We therefore acknowledge migration bias
as a potential systematic uncertainty... but note that our primary NN measurements
represent the all-core population. Future work separating prestellar and
protostellar samples would be valuable for quantifying this effect directly.
```

**Key changes:**
- ✓ Removed false claim about "lack access"
- ✓ Clarified that we HAVE computed NN spacing
- ✓ Identified the actual limitation: need to separate prestellar vs protostellar
- ✓ Framed as future work rather than fundamental data limitation

---

### 3. "Recommendation for Future Work" (Line 227) - UPDATED

**OLD TEXT:**
```
Recommendation for future work. Given the L/3 convergence problem, future HGBS
analyses should: (1) adopt nearest-neighbour spacing as the primary statistic...
The pairwise median should be used only as a supplementary statistic...
```

**NEW TEXT:**
```
Primary result: Nearest-neighbor spacing. Following the recommendation above,
we adopt nearest-neighbor spacing as the primary fragmentation wavelength statistic
throughout this paper. The pairwise median is retained for comparison with the
historical HGBS literature, but all physical interpretations and comparisons with
theory are based on the unbiased NN measurements.
```

**Key changes:**
- ✓ Changed from "future recommendation" to "what we actually did"
- ✓ Made clear NN is now PRIMARY statistic
- ✓ Explained pairwise is only for historical comparison

---

### 4. "Robustness Assessment" (Line 229) - UPDATED

**OLD TEXT:**
```
Robustness assessment. Our primary conclusion... is robust to the choice of
spacing statistic:
- Pairwise median: λ/W = 2.79 (2D), ~3.5 (3D-corrected)
- Nearest-neighbour (estimated): λ/W ≈ 2.1--3.1 (depending on region)
- Hierarchical-corrected: λ/W = 2.4 ± 0.3
All three approaches give values below the classical 4× prediction...
```

**NEW TEXT:**
```
Comparison of spacing statistics. The choice of spacing statistic has a dramatic
effect on the measured fragmentation wavelength:
- Pairwise median: λ/W = 2.79 (2D), ~3.5 (3D-corrected)
- Nearest-neighbor (measured): λ/W = 1.19 ± 0.04 (robust regions),
  1.24 ± 0.03 (full sample)
- Hierarchical-corrected: λ/W = 2.4 ± 0.3 (historical estimate)
The NN measurements reveal that the pairwise median overestimates the true
adjacent-core spacing by a factor of 2.4×. The NN spacing differs from the
classical 4× prediction by a factor of 3.4, substantially larger than the
1.4× discrepancy suggested by the pairwise median.
```

**Key changes:**
- ✓ Changed "Nearest-neighbor (estimated)" to "Nearest-neighbor (measured)"
- ✓ Updated NN values to actual measurements (1.19 ± 0.04, not 2.1-3.1)
- ✓ Quantified bias factor (2.4×)
- ✓ Noted discrepancy is larger than previously recognized (3.4× vs 1.4×)

---

### 5. "Recommendations for Future Work" (Line 237) - SIMPLIFIED

**OLD TEXT:**
```
Recommendations for future work. We acknowledge that the pairwise median statistic
has poorly characterised sampling properties... Future HGBS analyses should:
(1) adopt nearest-neighbour spacing as the primary statistic... (2) report both...
(3) perform fiber-resolved spacing analysis... The development of standardized
spacing statistics...
```

**NEW TEXT:**
```
Implications for future HGBS analyses. The pairwise median statistic has poorly
characterised sampling properties, particularly for large-N filaments where the
L/3 convergence artifact dominates. We recommend that future HGBS analyses adopt
nearest-neighbor spacing as the primary statistic and report the NN/pairwise ratio
to quantify the bias. The development of standardized spacing statistics for
filament-core systems would enable more robust comparisons across regions and
with theoretical predictions.
```

**Key changes:**
- ✓ Shortened and focused on key implications
- ✓ Removed redundant recommendations (we already did them)
- ✓ Added specific recommendation: report NN/pairwise ratio

---

## Verification

### PDF Content Verification:
- ✓ No "do not have access" or "lack access" phrases found
- ✓ "Direct nearest-neighbor measurements" present
- ✓ "2D KD-tree" methodology described
- ✓ "5,695" sample size mentioned
- ✓ "Gaia DR3 distances" referenced
- ✓ Migration bias section updated (prestellar/protostellar mentioned)

### Internal Consistency:
- ✓ Abstract: NN as primary result (0.119 ± 0.004 pc, λ/W = 1.19 ± 0.04)
- ✓ Table 1: NN values for all 8 regions
- ✓ Section 2.5: Methodology explained, data access confirmed
- ✓ Results: NN measurements presented throughout
- ✓ Conclusions: All based on NN results

---

## Impact on Paper

The resolution of this internal contradiction **strengthens the paper** by:

1. **Restoring credibility**: The observational pillar is now internally consistent
2. **Clarifying methodology**: Readers understand how NN spacings were computed
3. **Supporting reproducibility**: Method is clearly described (2D KD-tree on RA/Dec)
4. **Quantifying bias**: Explicitly states pairwise overestimates by 2.4×
5. **Emphasizing significance**: Discrepancy with theory is 3.4×, not 1.4×

---

## Files Modified

- `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/filament_spacing_streamlined_mnras.tex`
  - 5 sections updated (lines 98, 225, 227, 229, 237)

- `filament_spacing_streamlined_mnras.pdf` (27 pages, 1.18 MB)
  - Successfully compiled with all updates
  - All contradictions removed

---

## Summary

The internal contradiction has been **completely resolved**. The paper now presents a coherent, internally consistent observational picture:

1. **We HAVE access to HGBS core position data** (RA/Dec coordinates)
2. **We DID compute NN spacings directly** using 2D KD-tree methodology
3. **We HAVE 5,695 measurements** across 8 regions (3,932 in robust regions)
4. **The results are definitive**, not estimates or bias corrections
5. **All sections are consistent** with NN as the primary measurement

The paper is ready for resubmission or further review.
