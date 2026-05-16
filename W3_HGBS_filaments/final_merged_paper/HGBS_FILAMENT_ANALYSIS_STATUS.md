# HGBS Filament-Specific Analysis: In Progress

**Date**: 2026-05-02 12:30 PM
**Status**: Running filament-specific analysis

---

## What Changed

After discovering my previous analysis measured **region-wide** spacings instead of **filament-specific** spacings, I'm now analyzing HGBS data using the correct methodology.

### The Key Issue

- **My previous analysis**: Measured all cores in each region
  - Taurus NN = 0.621 pc (10× too large!)
  - Perseus NN = 0.534 pc (3× too large!)

- **HGBS methodology**: Measure cores along individual filament skeletons
  - Taurus NN = 0.062 pc (literature value)
  - Perseus NN = 0.182 pc (literature value)

### The Fix

I'm now:
1. Loading HGBS skeleton maps (DisPerSE output)
2. Extracting individual filament spines
3. Associating cores with filaments
4. Ordering cores along each filament spine
5. Computing NN and PM along filaments (not region-wide)

---

## Analysis Status

**Script**: `analyze_hgbs_filament_specific.py`
**Regions**: 4 regions (Ophiuchus, Perseus, Taurus, Orion B)
**Status**: Running...

### Regions Being Analyzed

| Region | Distance | Skeleton | Catalog |
|--------|----------|----------|---------|
| Ophiuchus | 140 pc | HGBS_oph_l1688_skeleton_map.fits | HGBS_ophiuchus_observed_core_catalog.txt |
| Perseus | 280 pc | HGBS_perseus_skeleton_map.fits | HGBS_perseus_observed_core_catalog.txt |
| Taurus | 140 pc | HGBS_taurusTMC1_skeleton_map.fits | HGBS_taurusTMC1_observed_core_catalog.txt |
| Orion B | 386 pc | HGBS_orionB_skeleton_map_thresh50.fits | HGBS_orionb_derived_core_catalog.txt |

---

## Expected Results

### If Analysis Is Correct

1. **NN values should match literature**:
   - Taurus: ~0.06 pc (literature: 0.062 pc)
   - Perseus: ~0.18 pc (literature: 0.182 pc)

2. **PM values should be larger**:
   - PM measures all pairwise distances along filaments
   - Should be > NN (as synthetic tests showed)

3. **NN/PM ratio**:
   - Should be in HGBS range (0.31-0.73)
   - Single filament prediction: ~0.125
   - Multi-fiber prediction: <0.1

4. **λ/W values**:
   - Will tell us which statistic is correct
   - NN λ/W expected: ~1.01 (if matches literature)
   - PM λ/W expected: ~2.79 (if matches HGBS reported)

---

## Timeline

- **12:22 PM**: Script launched (first attempt - had path issues)
- **12:45 PM**: Script relaunched with corrected paths
- **~12:55 PM**: Expected completion (4 regions)

---

## Next Steps

Once analysis completes:

1. **Verify correctness**: Compare NN values with literature
2. **Assess NN/PM ratio**: Check if in HGBS range
3. **Evaluate λ/W values**: Against theoretical predictions
4. **Definitive conclusion**: Which statistic measures fragmentation wavelength?

---

**End of Status Update**
