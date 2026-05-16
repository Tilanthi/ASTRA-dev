# Filament-Specific HGBS Analysis: Definitive PM vs NN Resolution

**Date**: 2026-05-02
**Status**: In Progress

---

## What We're Doing

After discovering that my previous analysis measured **region-wide** spacings instead of **filament-specific** spacings, I'm now:

1. **Loading HGBS skeleton maps** for each region (DisPerSE output showing filament spines)
2. **Extracting individual filament structures** from the skeleton maps
3. **Associating cores with filaments** based on proximity to spine
4. **Ordering cores along each filament** by projection onto the spine
5. **Computing NN and PM statistics** along filaments (not region-wide)

This matches the HGBS methodology and should produce values comparable to the literature.

---

## Why This Matters

The HGBS literature values (e.g., Taurus NN = 0.062 pc) are computed from cores **along individual filaments**, not all cores in the region. My previous analysis measured region-wide structure, giving values 3-10× too large.

**Correct approach:**
- Extract filament skeleton from HGBS skeleton maps
- Select only cores that lie along each filament
- Order cores by position along the 1D spine
- Compute spacings between adjacent cores along the spine

---

## Expected Results

If the analysis is correct:
1. **NN values should match literature**: ~0.06-0.18 pc range
2. **PM values should be larger**: PM measures all pairwise distances
3. **NN/PM ratio**: Should be in HGBS range (0.31-0.73)
4. **λ/W values**: Will tell us which statistic is correct

### If NN λ/W ≈ 1.01 (below theoretical minimum):
- Either the theoretical minimum needs revision
- Or width assumption (0.1 pc) is incorrect
- Or additional physics shortens wavelength

### If PM λ/W ≈ 2.79 (matches HGBS):
- PM might be measuring something other than fragmentation
- Could be L/(3W) as synthetic tests suggest
- Regional variations might reflect magnetic geometry

---

## Regions Being Analyzed

| Region | Distance (pc) | Skeleton | Catalog |
|--------|---------------|----------|---------|
| Ophiuchus | 140 | HGBS_oph_l1688_skeleton_map.fits | HGBS_ophiuchus_observed_core_catalog.txt |
| Perseus | 280 | HGBS_perseus_skeleton_map.fits | HGBS_perseus_observed_core_catalog.txt |
| Taurus | 140 | HGBS_taurusTMC1_skeleton_map.fits | HGBS_taurusTMC1_observed_core_catalog.txt |
| Orion B | 386 | HGBS_orionB_skeleton_map_thresh50.fits | HGBS_orionB_derived_core_catalog.txt |
| Serpens | 436 | HGBS_serpens_skeleton_map.fits | HGBS_serpens_observed_core_catalog.txt |
| Corona Australis | 150 | HGBS_craNS_skeleton_map.fits | HGBS_craNS_observed_core_catalog.txt |
| Aquila | 300 | HGBS_aquilaM2_skeleton_map.fits | HGBS_aquilaM2_observed_core_catalog.txt |

---

## Technical Implementation

The `analyze_hgbs_filament_specific.py` script:

1. **Loads skeleton FITS files** using astropy
2. **Extracts WCS information** to convert between pixel and sky coordinates
3. **Labels connected components** in skeleton map to find individual filaments
4. **Orders pixels along each filament** using PCA direction
5. **Associates cores** with nearest filament (within 15 pixels)
6. **Projects cores** onto filament spine to get position along filament
7. **Orders cores** by position along spine
8. **Computes NN** from adjacent core spacings along spine
9. **Computes PM** from all pairwise core spacings within each filament

---

## Status

**Script executing**: analyze_hgbs_filament_specific.py
**Expected runtime**: 5-10 minutes (7 regions with skeleton extraction and core association)
**Output**: FILAMENT_SPECIFIC_ANALYSIS/filament_specific_results.json

---

## Next Steps

Once analysis completes:
1. Compare measured NN values with HGBS literature
2. Assess NN/PM ratio vs HGBS range
3. Evaluate λ/W values against theoretical predictions
4. Determine which statistic (NN or PM) correctly measures fragmentation wavelength
5. Update paper with definitive conclusions

---

**End of Plan**
