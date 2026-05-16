# HGBS Aquila Discovery Science Plan

**Date**: 17 April 2026
**Region**: Aquila Rift (Molecular Cloud Complex)
**Data**: Herschel Gould Belt Survey (HGBS)

## 1. Available Data Inventory

### 1.1 FIR Intensity Maps (5 bands)
- 70 μm (PACS) - 144 MB
- 160 μm (PACS) - 144 MB
- 250 μm (SPIRE) - 35 MB
- 350 μm (SPIRE) - 12 MB
- 500 μm (SPIRE) - 6 MB

### 1.2 Derived Products
- Column density map (N_H2)
- Dust temperature map (T_dust)
- High-resolution column density map (18.2" beam)
- Filament skeleton map

### 1.3 Catalogs
- **Observed core catalog**: 65+ columns of photometry at 5 wavelengths
  - Peak flux densities, integrated fluxes, sizes, position angles
  - Detection significances, local contrasts
- **Derived core catalog**: ~750 dense cores with physical properties
  - Core masses (0.08 - 5+ Msun)
  - Dust temperatures (9-13 K)
  - Peak/average column densities
  - Volume densities
  - Bonnor-Eert mass ratios
  - Core types: starless, prestellar, protostellar

### 1.4 Key Publications
- André et al. 2010 (A&A, 518, L102) - HGBS overview
- Kőnyves et al. 2015 (arXiv:1507.05926) - Aquila core census

## 2. What Has Been Published (Kőnyves et al. 2015)

### 2.1 Published Results
1. **Core census**: 651 starless cores, 43 prestellar cores, 46 protostellar cores
2. **Core mass function (CMF)**: Similar shape to IMF, suggesting stellar origin
3. **Temperature distribution**: Prestellar cores colder (T~11 K) than starless
4. **Density thresholds**: Critical density for star formation identified
5. **Filament properties**: Characteristic width ~0.1 pc
6. **Core location**: Most prestellar cores found within filaments

### 2.2 Limitations of Published Work
- Focus on global statistics and CMF comparison with IMF
- Limited analysis of core formation sequences
- Basic filament characterization (width, length, mass-per-unit-length)
- No detailed SED analysis beyond single-temperature graybody fits
- Limited investigation of core-filament relationships
- No temporal evolution constraints
- No comparison with theoretical collapse models

## 3. Discovery Opportunities: Going Beyond Published Results

### 3.1 Physics of Filament Fragmentation

**Hypothesis 1: Fragmentation Scale Hierarchy**
- **Question**: Do filaments fragment hierarchically, with characteristic fragmentation lengths that follow the filament's width?
- **Method**: 
  - Analyze core spacing along filament skeleton
  - Calculate power spectrum of column density along filaments
  - Compare with predictions from sausage instability
- **Expected**: Preferred separation ~4× filament width (linear perturbation theory)
- **Discovery potential**: Direct test of fragmentation theory in real filaments

**Hypothesis 2: Mass-per-unit-length Variations**
- **Question**: How does M_line vary along individual filaments, and what controls core formation locations?
- **Method**:
  - Extract M_line profile along skeleton with high spatial resolution
  - Identify "critical" segments where M_line > M_line,crit
  - Correlate core locations with M_line peaks and variations
- **Expected**: Cores form preferentially at M_line maxima
- **Discovery potential**: Direct link between filament stability and core formation

### 3.2 Core Formation Sequences

**Hypothesis 3: Temperature-Density Evolution Sequence**
- **Question**: Is there a continuous evolution sequence from starless → prestellar → protostellar in T_dust-n space?
- **Method**:
  - Plot cores in temperature-density plane
  - Identify evolutionary tracks
  - Compare with models of core collapse and heating
- **Expected**: Prestellar cores follow distinct cooling track
- **Discovery potential**: First observational constraint on pre-collapse evolution

**Hypothesis 4: SED Shape Classification**
- **Question**: Can SED shapes (beyond single-T fits) distinguish core evolutionary states?
- **Method**:
  - Fit modified blackbody with variable β (dust emissivity index)
  - Search for 70 μm excess as embedded protostar indicator
  - Compare β distributions across core types
- **Expected**: Protostellar cores show β variations and 70 μm excess
- **Discovery potential**: New evolutionary diagnostic using FIR SEDs

### 3.3 Filament-Core Connection

**Hypothesis 5: Core Mass vs. Local Filament Properties**
- **Question**: Does core mass correlate with local filament width, density, or M_line?
- **Method**:
  - For each core, extract local filament properties at core location
  - Correlate core mass with: local N_H2, local M_line, local width, curvature
  - Multivariate analysis to identify dominant parameter
- **Expected**: Core mass set by local filament properties, not global cloud properties
- **Discovery potential**: Direct test of core formation theory

**Hypothesis 6: Spine vs. Branch Core Formation**
- **Question**: Do cores forming on filament spines differ from those on branches/junctions?
- **Method**:
  - Use skeleton map to identify spine, branches, junctions
  - Compare core properties by location type
  - Test if branch cores have different masses/temperatures
- **Expected**: Junction cores may be more massive due to material accumulation
- **Discovery potential**: Role of filament network geometry in star formation

### 3.4 Beyond Single-Temperature Graybody Fits

**Hypothesis 7: Temperature Structure within Cores**
- **Question**: Do individual cores show internal temperature gradients?
- **Method**:
  - Pixel-by-pixel SED fitting (where S/N allows)
  - Compare core center vs. edge temperatures
  - Search for heating from embedded sources
- **Expected**: Protostellar cores show central heating; prestellar are isothermal
- **Discovery potential**: First constraints on internal core thermodynamics

**Hypothesis 8: Dust Opacity Index Variations**
- **Question**: Does the dust emissivity index β vary across the cloud?
- **Method**:
  - Two-parameter SED fitting (T_dust, β) using PACS+SPIRE bands
  - Create β map of the region
  - Correlate β variations with column density and environment
- **Expected**: β may decrease in dense regions (dust grain coagulation)
- **Discovery potential**: Dust evolution traced through FIR SEDs

### 3.5 Velocity-Driven Star Formation

**Hypothesis 9: Filament Convergence Zones**
- **Question**: Where filaments intersect or merge, do we see enhanced core formation?
- **Method**:
  - Identify filament junctions from skeleton map
  - Compare core density and properties at junctions vs. along spines
  - Search for evidence of mass flow along filaments toward junctions
- **Expected**: Junctions have enhanced M_line and more massive cores
- **Discovery potential**: Evidence for mass flow in filament networks

**Hypothesis 10: Hierarchical Fragmentation**
- **Question**: Do secondary filaments fragment differently from primary filaments?
- **Method**:
  - Classify filaments by mass/length/hierarchy
  - Compare fragmentation scales and core properties
  - Test for scaling relationships
- **Expected**: Smaller filaments have smaller characteristic fragmentation scales
- **Discovery potential**: Universal fragmentation behavior?

## 4. Proposed Analysis Workflow with ASTRA

### Phase 1: Data Exploration and Characterization (Week 1)
1. Load and visualize all FITS maps
2. Extract basic statistics: column density distribution, temperature distribution
3. Characterize filament network from skeleton map
4. Summarize catalog properties

### Phase 2: Core-Filament Association (Week 2)
1. Project each core onto filament skeleton
2. Calculate distance from spine for each core
3. Extract local filament properties at each core location
4. Classify cores by location: spine, branch, junction

### Phase 3: Advanced SED Analysis (Week 3)
1. Perform two-parameter (T, β) SED fits for all cores
2. Create β map of the region
3. Search for 70 μm excess in cores
4. Classify cores by SED shape

### Phase 4: Statistical Analysis (Week 4)
1. Test Hypothesis 1: Core spacing analysis
2. Test Hypothesis 2: M_line variations
3. Test Hypothesis 3: T-n evolution tracks
4. Test Hypothesis 5: Core mass vs. local filament properties

### Phase 5: Discovery Mode (Week 5)
1. Apply ASTRA's anomaly detection to find unusual cores
2. Search for correlations not predicted by standard models
3. Identify candidate transition objects
4. Generate new hypotheses for follow-up

## 5. Expected Novel Results

1. **Quantitative fragmentation scales**: Direct measurement of how filaments fragment
2. **Core formation criteria**: Physical conditions required for core formation
3. **Evolutionary diagnostics**: New methods to classify core evolutionary state
4. **Dust properties**: β variations as tracer of dust evolution
5. **Filament network role**: How filament geometry influences star formation

## 6. Connection to Published Results

This work extends Kőnyves et al. (2015) by:
- Moving from global statistics to local correlations
- Beyond single-T fits to full SED characterization
- From core identification to core-filament relationships
- From phenomenological description to physical understanding

## 7. Next Steps

1. Set up data analysis pipeline in HGBS directory
2. Begin with Phase 1: Data exploration and characterization
3. Write Python scripts for ASTRA integration
4. Document results in working notebook

---
**Status**: Ready to begin Phase 1
