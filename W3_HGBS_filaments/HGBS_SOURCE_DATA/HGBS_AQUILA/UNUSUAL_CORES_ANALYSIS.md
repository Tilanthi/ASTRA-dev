# HGBS Aquila Discovery Science - Unusual Cores Analysis

**Date**: 17 April 2026
**Focus**: Identifying discovery targets beyond published results

## 1. Catalog Statistics Summary

### 1.1 Core Classification

| Type | Count | Percentage | Median Mass (Msun) | Median T (K) | Median α_BE | Bound Fraction |
|------|-------|------------|-------------------|-------------|-------------|----------------|
| Starless | 216 | 28.8% | 0.090 | 13.10 | 5.85 | 0% |
| Prestellar | 469 | 62.6% | 0.420 | 11.50 | 1.40 | 64.2% |
| Protostellar | 64 | 8.5% | 0.715 | 12.45 | 0.50 | 79.7% |
| **Total** | **749** | **100%** | **0.290** | **11.50** | **-** | **-** |

**Key Observations**:
1. Prestellar cores dominate (62.6%) - differs from Kőnyves et al. (2015)
2. Clear mass growth through evolution: 0.09 → 0.42 → 0.72 Msun
3. Prestellar are coldest (11.5 K) - consistent with being shielded and unheated
4. Protostellar are slightly warmer (12.45 K) - internal heating from embedded source
5. Starless are warmest (13.1 K) - can be externally heated, no internal source

### 1.2 Consistency Checks

✓ **Good consistency**:
- Starless cores are mostly unbound (0% bound, α_BE = 5.85)
- Protostellar cores are mostly bound (80% bound, α_BE = 0.50)
- Prestellar cores are intermediate (64% bound, α_BE = 1.40)
- No bound starless cores found (consistent with no unbound prestellar contamination)

⚠ **Needs investigation**:
- High fraction of prestellar cores (63% vs. 6% in Kőnyves et al. 2015)
- Suggests different classification criteria or catalog version
- Need to verify classification method

## 2. Discovery Targets Identified

### 2.1 Very Massive Cores (M > 5 Msun)

**Count**: 8 cores

These cores are potential sites of massive star or cluster formation:

| Core Name | Mass (Msun) | T (K) | Type | Notes |
|-----------|-------------|-------|------|-------|
| 182957.5-015843 | 19.70 | 8.2 | Prestellar | **Most massive in catalog** |
| 183110.2-020438 | 11.46 | 10.3 | Prestellar | Very massive |
| 182832.0-015356 | 10.15 | 8.4 | Prestellar | Very massive |
| 182942.1-015007 | 7.55 | 8.0 | Prestellar | Massive |
| 182958.6-020822 | 6.27 | 7.6 | Prestellar | Massive, cold |
| 183004.1-020305 | 7.98 | 15.5 | Protostellar | Massive, warm |
| 182830.9-034733 | 5.81 | 8.6 | Prestellar | Massive |
| 182957.7-015758 | 5.16 | 8.3 | Prestellar | Massive |

**Discovery Questions**:
- Are these truly single cores or multiple unresolved cores?
- Will they form single massive stars or multiple stars/cluster?
- What are their local filament properties? (M_line, local density)
- Are they located at filament junctions where material accumulates?
- Why are most massive cores prestellar (not yet formed stars)?

**Analysis Needed**:
1. High-resolution imaging to check for substructure
2. Extract local filament properties
3. Compare with theoretical predictions for massive core collapse
4. Search for outflows or other signs of active star formation

### 2.2 Cold Protostellar Cores (T < 10 K)

**Count**: 1 core

| Core Name | T (K) | Mass (Msun) | Notes |
|-----------|-------|-------------|-------|
| 183638.6-022344 | 9.3 | 0.85 | Very young? Or deeply embedded? |

**Discovery Questions**:
- Is this a very young protostar (first hydrostatic core phase)?
- Or is the heating source so deeply embedded that it doesn't warm the envelope?
- Check for 70 μm emission (protostars should have strong 70 μm)

**Analysis Needed**:
1. Check SED shape: Is there 70 μm excess?
2. Compare with models of first hydrostatic cores (FHSC)
3. Check for outflow signatures
4. Determine if this represents a distinct evolutionary phase

### 2.3 Warm Prestellar Cores (T > 15 K)

**Count**: 26 cores

These are classified as prestellar but are unusually warm:

**Discovery Questions**:
1. **External heating**: Are these near bright stars or HII regions?
2. **Misclassification**: Should some be reclassified as protostellar?
3. **Transient phase**: Do they represent a brief transition phase?
4. **Lower density**: Are they less dense and thus more susceptible to external heating?

**Analysis Needed**:
1. Check local environment (distance from sources of external radiation)
2. Compare densities with cooler prestellar cores
3. Search for 70 μm excess (hidden protostar?)
4. Determine if warm prestellar cores have different α_BE distribution

**Sub-categories to investigate**:
- Warm but bound (α_BE < 2): May be prestellar cores heated externally
- Warm and unbound (α_BE > 2): May be starless cores misclassified as prestellar

### 2.4 High Bonnor-Ebert Prestellar Cores (α > 3)

**Count**: 71 cores (15% of prestellar cores)

These are classified as prestellar but have high α_BE suggesting they may be unbound:

**Discovery Questions**:
1. **Classification issue**: Should these be reclassified as starless?
2. **Non-equilibrium**: Are they collapsing (not in equilibrium)?
3. **Selection effect**: Are low-mass cores preferentially given prestellar classification?
4. **Mass threshold**: Is there a mass below which cores are rarely prestellar?

**Analysis Needed**:
1. Compare mass distribution: high-α vs. low-α prestellar cores
2. Check if high-α cores are systematically less massive or less dense
3. Investigate classification criteria used in catalog
4. Determine if reclassification would change CMF shape

## 3. Discovery Hypotheses to Test

### Hypothesis 1: Core Evolution Sequence
**Prediction**: Starless → Prestellar → Protostellar sequence should show:
- Increasing mass: M_starless < M_prestellar < M_protostellar ✓ (confirmed)
- Temperature evolution: T_prestellar < T_starless < T_protostellar ✓ (confirmed)
- α_BE evolution: α_starless > α_prestellar > α_protostellar ✓ (confirmed)

**Discovery**: The 8 very massive cores (M > 5 Msun) are mostly prestellar, not protostellar. Why?

**Possible explanations**:
1. Massive cores have longer prestellar phase
2. Massive cores fragment before collapse completes
3. Timescale for massive core collapse is longer
4. Some massive cores may not collapse (will remain starless)

### Hypothesis 2: Prestellar Classification Criteria
**Observation**: 63% of cores are prestellar (vs. 6% in Kőnyves et al. 2015)

**Possible explanations**:
1. Different catalog: This may be a different catalog version
2. Different criteria: Classification may be based on α_BE alone
3. Different definition: "Prestellar" vs. "bound starless" distinction

**Discovery action**: Verify catalog version and classification criteria

### Hypothesis 3: Massive Core Environments
**Prediction**: Massive cores should form at locations where filaments merge

**Test**:
1. Map massive cores onto filament skeleton
2. Check if they are at filament junctions
3. Extract local M_line at core locations
4. Compare with typical M_line along filaments

**Expected**: Massive cores found preferentially at junctions with high M_line

### Hypothesis 4: Warm Prestellar Cores
**Prediction**: Warm prestellar cores are either:
1. Externally heated (near bright sources)
2. Misclassified (actually protostellar)
3. Lower density (less shielded)

**Test**:
1. Map distances to known heating sources
2. Check for 70 μm emission (protostellar signature)
3. Compare densities with cool prestellar cores
4. Examine local column density

## 4. Phase 2 Analysis Priorities

### Priority 1: Core-Filament Association
**Goal**: Understand where cores form relative to filaments

**Tasks**:
1. Convert core RA/Dec to pixel coordinates
2. Load skeleton map
3. Calculate distance from each core to nearest filament
4. Extract local filament properties at core locations
5. Classify cores by filament location: spine, branch, junction, isolated

**Discovery value**: Will test theories of filament fragmentation and core formation

### Priority 2: Massive Core Investigation
**Goal**: Understand the 8 cores with M > 5 Msun

**Tasks**:
1. High-resolution imaging to check for substructure
2. Extract local environment (N_H2, T_dust, M_line)
3. Check for 70 μm excess (protostellar activity?)
4. Compare with theoretical mass limits (Jeans mass, turbulent core mass)

**Discovery value**: Massive cores are rare and may form massive stars or clusters

### Priority 3: Warm Prestellar Core Analysis
**Goal**: Understand why 26 prestellar cores are warm (T > 15 K)

**Tasks**:
1. Check for 70 μm excess (hidden protostars?)
2. Map distance to external heating sources
3. Compare densities with cool prestellar cores
4. Re-evaluate classification criteria

**Discovery value**: May reveal new evolutionary phase or classification issue

### Priority 4: Core Spacing Analysis
**Goal**: Measure fragmentation scale along filaments

**Tasks**:
1. Project cores onto 1D filament coordinate
2. Calculate nearest-neighbor separations
3. Test for preferred separation scale
4. Compare with filament width (expected: separation ~4 × width)

**Discovery value**: Direct test of filament fragmentation theory

## 5. Expected Novel Results

Based on Phase 1 analysis, we expect to discover:

1. **Core-filament relationship**: Quantitative relationship between core location and local filament properties
2. **Massive core environments**: What conditions lead to formation of M > 5 Msun cores
3. **Fragmentation scale**: Direct measurement of characteristic core spacing
4. **Evolutionary diagnostics**: Improved classification using multi-parameter space (M, T, α_BE, location)
5. **Anomalous cores**: Nature of warm prestellar and cold protostellar cores

## 6. Files Created

1. `HGBS_DISCOVERY_PLAN.md` - Overall discovery science plan
2. `PHASE1_RESULTS.md` - Phase 1 data exploration results
3. `unusual_cores.txt` - List of unusual cores for investigation
4. `catalog_analysis.py` - Catalog analysis script
5. `parse_catalog.py` - Catalog parsing utility
6. `hgbs_discovery_phase1_fixed.py` - Phase 1 analysis script

## 7. Next Steps

**Immediate**: Begin Phase 2 analysis with core-filament association
**Week 1-2**: Complete core coordinate conversion and filament mapping
**Week 3**: Core spacing and fragmentation analysis
**Week 4**: Local environment analysis for unusual cores
**Week 5**: Discovery mode with ASTRA anomaly detection

---
**Phase 1 Status**: Complete with discovery targets identified
**Phase 2 Status**: Ready to begin - Core-Filament Association
**Discovery Potential**: High - 45 unusual cores identified for detailed study
