# HGBS Aquila Discovery Science - Project Summary

**Date**: 17 April 2026
**Region**: Aquila Rift Molecular Cloud (Herschel Gould Belt Survey)
**Goal**: Real discovery science using ASTRA on Herschel FIR data

---

## 1. What Has Been Accomplished

### Phase 1: Data Exploration and Characterization ✓ COMPLETE

**Data Successfully Loaded**:
- Column density map (5657×5233 px, median: 4.64×10^21 cm^-2)
- Dust temperature map (median: 15.07 K)
- Filament skeleton map (15,392 filament pixels)
- Derived core catalog (749 cores parsed)

**Key Findings**:
1. **Core catalog contains 749 cores**:
   - 469 prestellar (62.6%)
   - 216 starless (28.8%)
   - 64 protostellar (8.5%)

2. **Mass progression through evolution**:
   - Starless: median 0.09 Msun
   - Prestellar: median 0.42 Msun
   - Protostellar: median 0.72 Msun

3. **Temperature evolution**:
   - Starless: median 13.10 K (warmest - external heating)
   - Prestellar: median 11.50 K (coldest - shielded)
   - Protostellar: median 12.45 K (internal heating)

4. **Bonnor-Ebert ratios** (gravitational binding):
   - Starless: median α = 5.85 (0% bound)
   - Prestellar: median α = 1.40 (64% bound)
   - Protostellar: median α = 0.50 (80% bound)

---

## 2. Discovery Targets Identified

### Very Massive Cores (M > 5 Msun): 8 found
- **Most massive**: 19.7 Msun (prestellar, 8.2 K)
- Potential sites of massive star/cluster formation
- Need investigation: Are they single cores or multiples?
- Key question: Why are most still prestellar?

### Warm Prestellar Cores (T > 15 K): 26 found
- Classified as prestellar but unusually warm
- Possible explanations: external heating, misclassification, or new phase
- Need investigation: Check for hidden protostars (70 μm excess)

### High-α Prestellar Cores (α > 3): 71 found
- Classified as prestellar but likely unbound
- May be misclassification or non-equilibrium objects
- Need investigation: Re-evaluate classification criteria

### Cold Protostellar Core (T < 10 K): 1 found
- Very young or deeply embedded protostar
- Could be first hydrostatic core phase
- Need investigation: Check SED shape and evolutionary state

---

## 3. Files Created

### Documentation
- `README.md` (this file) - Project summary
- `HGBS_DISCOVERY_PLAN.md` - Overall discovery science plan
- `PHASE1_RESULTS.md` - Phase 1 data exploration results
- `UNUSUAL_CORES_ANALYSIS.md` - Detailed analysis of discovery targets
- `unusual_cores.txt` - List of unusual cores for investigation

### Analysis Scripts
- `parse_catalog.py` - Catalog parsing utility
- `catalog_analysis.py` - Detailed catalog analysis
- `hgbs_discovery_phase1_fixed.py` - Phase 1 data exploration
- `hgbs_discovery_phase1.py` - Initial version (superseded)

---

## 4. Key Scientific Questions

### Question 1: Filament Fragmentation
**Hypothesis**: Filaments fragment with characteristic spacing ~4× filament width (~0.4 pc)
**Test**: Measure core spacing along filaments
**Discovery value**: Direct test of fragmentation theory

### Question 2: Core Formation Criteria
**Hypothesis**: Cores form only where M_line > M_line,crit ≈ 16 Msun/pc
**Test**: Correlate core locations with local filament properties
**Discovery value**: Identify physical conditions for star formation

### Question 3: Massive Core Formation
**Hypothesis**: Massive cores form at filament junctions where material accumulates
**Test**: Map massive cores onto filament network
**Discovery value**: Understand origin of massive star formation

### Question 4: Evolutionary Diagnostics
**Hypothesis**: Multi-parameter space (M, T, α_BE, location) improves classification
**Test**: Analyze unusual cores in multi-parameter space
**Discovery value**: New evolutionary sequence with fewer misclassifications

---

## 5. Phase 2: Core-Filament Association (NEXT)

### Goals
1. Map cores onto filament skeleton
2. Extract local filament properties for each core
3. Calculate core spacing along filaments
4. Identify core formation preferences (spine vs. branch vs. junction)

### Tasks
1. **Coordinate conversion**: RA/Dec → pixel coordinates
2. **Skeleton projection**: Calculate distance from each core to nearest filament
3. **Local properties**: Extract N_H2, M_line at each core location
4. **Spacing analysis**: Measure nearest-neighbor distances along filaments
5. **Junction analysis**: Compare cores at junctions vs. along spines

### Expected Duration
- Week 1: Coordinate conversion and skeleton mapping
- Week 2: Local property extraction
- Week 3: Spacing and fragmentation analysis
- Week 4: Junction and environment analysis

---

## 6. Connection to Published Results

### Kőnyves et al. (2015) - Aquila Core Census
**Published results**:
- 651 starless, 43 prestellar, 46 protostellar
- Focus on core mass function (CMF)
- Comparison with stellar initial mass function (IMF)

### How This Work Extends Published Results
1. **From global to local**: Focus on core-filament relationships, not just statistics
2. **From phenomenology to physics**: Test theories of fragmentation and core formation
3. **From identification to evolution**: Use multi-parameter space for classification
4. **From known to novel**: Investigate unusual cores that don't fit standard categories

### Novel Contributions Expected
1. Quantitative fragmentation scale measurement
2. Core formation criteria (M_line threshold)
3. Environmental dependence of core properties
4. Improved evolutionary diagnostics
5. Nature of unusual cores (massive, warm prestellar, cold protostellar)

---

## 7. Discovery Potential

### High-Impact Discoveries Possible

1. **If massive cores are at filament junctions**:
   - New understanding of massive star formation
   - Filament network geometry controls star formation

2. **If core spacing is ~4× filament width**:
   - First direct confirmation of fragmentation theory
   - Predictive power for star formation locations

3. **If warm prestellar cores have 70 μm excess**:
   - May be hidden protostars (new class of objects)
   - Evolutionary sequence revision needed

4. **If core mass correlates with local M_line**:
   - Direct link between filament stability and core formation
   - Predictive model for core masses

---

## 8. Data Inventory

### Available in HGBS_AQUILA folder
| File | Size | Description |
|------|------|-------------|
| aquilaM2-070.fits | 144 MB | 70 μm intensity (PACS) |
| aquilaM2-160.fits | 144 MB | 160 μm intensity (PACS) |
| aquilaM2-250.fits | 35 MB | 250 μm intensity (SPIRE) |
| aquilaM2-350.fits | 12 MB | 350 μm intensity (SPIRE) |
| aquilaM2-500.fits | 6 MB | 500 μm intensity (SPIRE) |
| HGBS_aquilaM2_column_density_map.fits | 113 MB | N_H2 map |
| HGBS_aquilaM2_dust_temperature_map.fits | 113 MB | T_dust map |
| HGBS_aquilaM2_hires_column_density_map.fits | 113 MB | High-res N_H2 (18.2") |
| HGBS_aquilaM2_skeleton_map.fits | 226 MB | Filament skeleton |
| HGBS_aquilaM2_derived_core_catalog.txt | 137 KB | Core physical properties |
| HGBS_aquilaM2_observed_core_catalog.txt | 446 KB | Core photometry |
| HGBS_aquilaM2_core_blowups.pdf | 68 MB | Core images |
| HGBS_aquilaM2_core_SEDs.pdf | 5.9 MB | Core SEDs |

---

## 9. ASTRA Integration Plan

### How ASTRA Will Be Used

**Phase 2 (Analysis)**:
- Use ASTRA's causal inference to identify correlations
- Apply dimensional analysis to core-filament relationships
- Use Bayesian model comparison to test fragmentation theories

**Phase 3 (Discovery Mode)**:
- Apply ASTRA's anomaly detection to find unusual cores
- Generate new hypotheses from multi-parameter correlations
- Identify patterns not predicted by standard models

**Phase 4 (Validation)**:
- Compare results with theoretical predictions
- Test hypotheses on independent regions (e.g., Orion)
- Generate predictions for follow-up observations

---

## 10. Timeline and Milestones

### ✓ Complete (April 17, 2026)
- Phase 1: Data exploration and characterization
- Catalog parsing and statistics
- Discovery target identification

### In Progress (April 18 - May 15, 2026)
- Phase 2: Core-filament association
- Coordinate conversion and mapping
- Local property extraction

### Planned (May 16 - June 15, 2026)
- Phase 3: Spacing and fragmentation analysis
- Phase 4: Discovery mode with ASTRA
- Phase 5: Validation and interpretation

### Expected Completion
- **Early June 2026**: Analysis complete
- **Mid-June 2026**: Paper draft ready
- **July 2026**: Internal review and revision
- **August 2026**: Submission to MNRAS / ApJ

---

## 11. Quick Start Guide

### To View Results
```bash
cd /Users/gjw255/astrodata/SWARM/ASTRA/HGBS

# Read summary documents
cat README.md
cat UNUSUAL_CORES_ANALYSIS.md

# View unusual cores
cat unusual_cores.txt
```

### To Run Analysis
```bash
# Phase 1 (already complete)
python hgbs_discovery_phase1_fixed.py

# Catalog analysis
python catalog_analysis.py

# Phase 2 (coming soon)
# python hgbs_discovery_phase2.py  # Will be created next
```

### To Inspect Data
```python
from astropy.io import fits
import matplotlib.pyplot as plt

# Load column density map
data, header = fits.open('HGBS_AQUILA/HGBS_aquilaM2_column_density_map.fits')[0].data, header

# Display
plt.imshow(data, origin='lower', cmap='viridis')
plt.colorbar(label='N_H2 (cm^-2)')
plt.show()
```

---

## 12. Contact and Collaboration

**Principal Investigator**: Glenn J. White
**System**: ASTRA (Autonomous Scientific Discovery in Astrophysics)
**Data**: Herschel Gould Belt Survey (HGBS)

**For questions about this analysis**:
- Review the documentation files in this directory
- Check the discovery plan (HGBS_DISCOVERY_PLAN.md)
- Examine the unusual cores analysis (UNUSUAL_CORES_ANALYSIS.md)

---

**Status**: Phase 1 complete, Phase 2 ready to begin
**Next milestone**: Core-filament association analysis
**Discovery potential**: High - 45 unusual cores + 749 total cores to investigate
