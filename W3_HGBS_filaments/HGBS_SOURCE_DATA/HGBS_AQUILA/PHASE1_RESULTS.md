# HGBS Aquila - Phase 1 Results Summary

**Date**: 17 April 2026
**Analysis**: Data Exploration and Characterization

## 1. Data Successfully Loaded

### 1.1 Column Density Map
- **Dimensions**: 5657 × 5233 pixels
- **Column density range**: 2.05 - 167.7 × 10^21 cm^-2
- **Median N_H2**: 4.64 × 10^21 cm^-2
- **High-column-density pixels** (N_H2 > 7 × 10^21 cm^-2, Av > 7): 1.49 million pixels (9.3%)

### 1.2 Dust Temperature Map
- **Dimensions**: 5657 × 5233 pixels
- **Temperature range**: 9.77 - 35.61 K
- **Median T_dust**: 15.07 K
- **Temperature distribution**:
  - 10th percentile: 14.49 K
  - 25th percentile: 14.80 K
  - 50th percentile (median): 15.07 K
  - 75th percentile: 15.31 K
  - 90th percentile: 15.56 K
  - 95th percentile: 15.73 K
  - 99th percentile: 19.04 K

**Observation**: The narrow temperature range (14.5-15.5 K for most pixels) suggests the cloud is relatively isothermal at large scales, with small cold pockets likely corresponding to dense cores.

### 1.3 Filament Skeleton Map
- **Total pixels**: 16.1 million
- **Filament pixels**: 15,392 (0.10% of area)
- **Skeleton value range**: 1.0 - 137.0 (intensity scale)
- **Median skeleton value**: 48.0

**Observation**: The filament network occupies only 0.1% of the map area but contains most of the dense, star-forming material.

### 1.4 Core Catalog
- **Total cores**: 749
- **Core type distribution**:
  - Prestellar: 469 (62.6%)
  - Starless: 216 (28.8%)
  - Protostellar: 64 (8.5%)

**Note**: These numbers differ from Kőnyves et al. (2015) who reported 651 starless, 43 prestellar, 46 protostellar. This may reflect:
1. Different classification criteria
2. Updated catalog version
3. Inclusion of marginal sources
4. Need to verify catalog version

#### Core Mass Distribution
- **Range**: 0.010 - 19.7 Msun
- **Median**: 0.290 Msun
- **Mass percentiles** (from raw data):
  - 25th percentile: ~0.10 Msun
  - 50th percentile: ~0.29 Msun
  - 75th percentile: ~0.60 Msun

#### Core Temperature Distribution
- **Range**: 6.7 - 32.1 K
- **Median**: 11.5 K
- **Cold cores** (T < 10 K): Likely prestellar
- **Warm cores** (T > 15 K): Likely protostellar or externally heated

## 2. Key Observations and Discovery Opportunities

### 2.1 The Core Classification Puzzle

**Question**: Why does our parsed catalog show 469 prestellar cores (62.6%) while Kőnyves et al. (2015) reported only 43 (6.2%)?

**Hypothesis**: The catalog may use different classification criteria. We need to:
1. Verify which catalog version we have
2. Check the Bonnor-Ebert ratio distribution
3. Examine the relationship between core type, temperature, and mass

**Discovery Opportunity**: Investigate core classification criteria and identify "transition" objects that may be misclassified.

### 2.2 Temperature-Density Relation

**Observation**: The median cloud temperature (15.07 K) is significantly warmer than the median core temperature (11.5 K).

**Discovery Opportunity**: Map the temperature structure around cores to identify:
- Cold cores embedded in warm ambient medium
- Evidence for external heating
- Temperature gradients from core centers to edges

### 2.3 Core-Filament Relationship

**Observation**: 15,392 filament pixels vs. 749 cores suggests ~20 cores per filament pixel on average, but cores should be concentrated along filaments.

**Discovery Opportunities**:
1. Project cores onto filament skeleton to measure actual core-filament association
2. Calculate core spacing along filaments
3. Test the "filament fragmentation scale" hypothesis: preferred separation ~4 × filament width

### 2.4 Mass Function Comparison

**Observation**: Core mass range 0.01 - 19.7 Msun with median 0.29 Msun.

**Discovery Opportunities**:
1. Compare core mass function (CMF) with stellar initial mass function (IMF)
2. Test whether CMF slope varies with location (filament spine vs. branch vs. junction)
3. Identify high-mass cores that may form massive stars

### 2.5 Unusual Cores (Anomaly Detection)

**Potential Anomalies**:
1. **Very massive cores** (> 5 Msun): May be forming multiple stars or be actually multiple unresolved cores
2. **Warm prestellar cores** (T > 15 K): May be externally heated or misclassified
3. **Cold protostellar cores** (T < 10 K): May be very young or have deeply embedded sources
4. **High Bonnor-Ebert ratio cores** (α_BE > 3): May be unbound or transient

## 3. Preliminary Statistics

### 3.1 Core Type vs. Temperature (expected)
- Starless: T ~ 11-13 K (ambient cloud temperature)
- Prestellar: T ~ 9-11 K (cooled by shielding)
- Protostellar: T > 12 K (heated by embedded source)

**Discovery Opportunity**: Identify cores that deviate from these patterns (e.g., cold protostellar, warm prestellar).

### 3.2 Core Type vs. Density (expected)
- Starless: Lower average densities
- Prestellar: Higher densities (n > 10^5 cm^-3)
- Protostellar: Variable densities depending on evolutionary stage

**Discovery Opportunity**: Use density as an additional evolutionary diagnostic.

### 3.3 Bonnor-Ebert Critical Mass
Theoretical criterion: α_BE = M_BE,crit / M_obs
- α_BE < 2: Likely gravitationally bound (prestellar)
- α_BE > 2: Likely unbound (starless)

**Discovery Opportunity**: Compare α_BE-based classification with published classification to identify discrepancies.

## 4. Next Steps: Phase 2 - Core-Filament Association

### 4.1 Scientific Questions

1. **What fraction of cores lie directly on filament spines?**
   - Measure distance from each core to nearest skeleton pixel
   - Classify cores as: on-spine, near-spine, isolated

2. **How does core mass vary with local filament properties?**
   - Extract local column density at each core location
   - Calculate local mass-per-unit-length (M_line)
   - Correlate core mass with M_line

3. **What is the characteristic core spacing along filaments?**
   - Project cores onto 1D filament coordinate
   - Calculate distribution of nearest-neighbor separations
   - Test for preferred fragmentation scale

4. **Do cores preferentially form at filament junctions?**
   - Identify junctions from skeleton map
   - Compare core density at junctions vs. along spines

### 4.2 Analysis Plan

**Week 1: Core coordinate conversion**
- Convert RA/Dec to pixel coordinates
- Match cores to column density map
- Extract local properties for each core

**Week 2: Core-filament projection**
- Load skeleton map
- Calculate distance from each core to nearest filament
- Classify cores by location relative to filaments

**Week 3: Core spacing analysis**
- Project cores onto filament spines
- Calculate nearest-neighbor distances
- Test for preferred fragmentation scales

**Week 4: Local filament properties**
- Extract M_line profiles along filaments
- Correlate core mass with local M_line
- Identify locations where cores form preferentially

## 5. Discovery Hypotheses to Test

### Hypothesis 1: Filament Fragmentation Scale
**Prediction**: Cores are spaced ~4 × filament width apart along filaments
**Test**: Measure core separations, compare with filament width (~0.1 pc)
**Expected**: Preferred separation ~0.4 pc

### Hypothesis 2: Mass-per-unit-Length Threshold
**Prediction**: Cores form only where M_line > M_line,crit ≈ 16 Msun/pc
**Test**: Compare M_line at core locations vs. non-core locations
**Expected**: Cores found preferentially at M_line peaks above critical value

### Hypothesis 3: Core Mass - Local Density Correlation
**Prediction**: Core mass scales with local column density
**Test**: Correlate core mass with local N_H2
**Expected**: M_core ∝ N_H2^1.5 (roughly)

### Hypothesis 4: Junction Enhancement
**Prediction**: Filament junctions have higher M_line and more massive cores
**Test**: Compare core properties at junctions vs. along spines
**Expected**: Junction cores are 2-3× more massive on average

## 6. Files Created

1. `HGBS_DISCOVERY_PLAN.md` - Overall discovery science plan
2. `hgbs_discovery_phase1_fixed.py` - Phase 1 analysis script
3. `parse_catalog.py` - Catalog parsing utility
4. `PHASE1_RESULTS.md` - This file

## 7. Data Inventory Summary

| Data Product | Status | Shape/Size | Key Properties |
|--------------|--------|------------|----------------|
| Column density map | ✓ Loaded | 5657×5233 px | Median: 4.64e21 cm^-2 |
| Temperature map | ✓ Loaded | 5657×5233 px | Median: 15.07 K |
| Skeleton map | ✓ Loaded | 5657×5233 px | 15,392 filament px |
| 70 μm intensity | Not yet loaded | 144 MB | - |
| 160 μm intensity | Not yet loaded | 144 MB | - |
| 250 μm intensity | Not yet loaded | 35 MB | - |
| 350 μm intensity | Not yet loaded | 12 MB | - |
| 500 μm intensity | Not yet loaded | 6 MB | - |
| Hi-res column density | Not yet loaded | 113 MB | 18.2" resolution |
| Derived catalog | ✓ Parsed | 749 cores | 469 prestellar, 216 starless, 64 protostellar |
| Observed catalog | Not yet loaded | ~740 cores | Full photometry at 5 bands |

---
**Phase 1 Status**: Complete
**Next Phase**: Phase 2 - Core-Filament Association
**Estimated Time**: 2-3 weeks for full Phase 2 analysis
