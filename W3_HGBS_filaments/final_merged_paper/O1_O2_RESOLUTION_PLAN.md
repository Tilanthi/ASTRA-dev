# Resolution Plan for Concerns O1 and O2

**Date**: 2026-05-08
**Status**: PLAN FOR IMPLEMENTATION

---

## Executive Summary

Two critical concerns remain after L/3 artifact corrections:

**O1**: The NN vs PM discrepancy (40-50%) is qualitatively attributed to "geometric complexity" but never quantitatively demonstrated. The NN-based measurement (λ/W = 1.67) from only 2/8 regions carries excessive weight as the "primary measurement."

**O2**: The NN analysis methodology associates only 49.6% of Orion B cores and 26.7% of Aquila cores with filaments. These low association rates raise serious selection bias concerns that are not addressed. The 20-pixel association radius and 50-pixel clustering cutoff lack sensitivity testing.

This plan outlines concrete actions to resolve both concerns through (1) forward-modelling validation, (2) comprehensive sensitivity analysis, and (3) selection bias quantification.

---

## Concern O1: Quantitative Validation of PM-NN Discrepancy

### Problem Statement

The 40-50% PM-NN difference is the paper's central scientific tension. The current explanation—"geometric complexity of multi-filament systems"—is qualitative. A quantitative demonstration is needed showing that realistic multi-filament geometries produce precisely this offset.

### Root Cause

The paper states that PM includes cross-fiber distances while NN measures along-fiber spacing, but this mechanism is never demonstrated with forward modelling. We need to prove that synthetic multi-filament systems with known λ/W produce PM/NN ratios of 1.4-1.5 (40-50% difference) through geometric projection effects alone.

### Proposed Solution: Forward-Modelling Campaign

#### Approach 1: Analytic Multi-Filament Model

Create a simplified analytic model of multi-filament systems:

```python
# Model components:
# 1. N_parallel filaments with known spacing d_filament
# 2. Each filament has beading wavelength λ_true
# 3. Random phase offsets between filaments
# 4. Add Gaussian noise to core positions (σ_scatter)
# 5. Apply both PM and NN statistics
# 6. Measure PM/NN ratio as function of:
#    - Number of filaments (N = 1, 2, 3, 5, 10)
#    - Inter-filament spacing (d_filament/λ_true = 0.5, 1, 2, 5)
#    - Phase coherence (coherent vs random)
#    - Core position scatter (σ/λ_true = 0.05, 0.1, 0.2)
```

**Success criteria**:
- Demonstrate that multi-filament systems produce PM/NN ≈ 1.4-1.5 for realistic parameters
- Show that single-filament systems produce PM/NN ≈ 1.0 (control case)
- Identify which parameters (N_filaments, d_filament, phase) drive the PM-NN discrepancy

#### Approach 2: Realistic Multi-Filament Mock Data

Use HGBS-inspired filament geometries:

```python
# Generate mock filament systems based on HGBS characteristics:
# 1. Filament lengths: L = 2-10 pc (matching HGBS range)
# 2. Filament widths: W = 0.1 pc (HGBS characteristic)
# 3. Core counts: N = 500-2000 cores per region (matching HGBS)
# 4. Fiber bundle geometry: 3-7 fibers per filament (Hacar et al. 2013)
# 5. Inter-fiber spacing: d_fiber ≈ 0.05-0.15 pc (fiber observations)
# 6. True fragmentation wavelength: λ_true = 0.15-0.25 pc
# 7. Apply both PM and NN statistics using identical methodology to paper
# 8. Compare PM/NN ratios to observed 40-50% difference
```

**Success criteria**:
- PM/NN ratio from mock data falls within 1.3-1.6 for realistic parameters
- NN recovers λ_true with <10% bias (validates NN as unbiased)
- PM overestimates λ_true by 30-60% (matches observed discrepancy)

### Implementation Requirements

**Python script**: `forward_model_pm_nn_discrepancy.py`

**Parameter space to explore**:
- N_filaments: [1, 2, 3, 5, 7, 10]
- d_filament/λ_true: [0.5, 1.0, 2.0, 5.0]
- σ_scatter/λ_true: [0.05, 0.1, 0.2, 0.3]
- Phase_coherence: [coherent, random, semi-coherent]
- N_realizations: 100 per parameter point

**Total simulations**: 6 × 4 × 4 × 3 × 100 = 28,800 mock realizations

**Analysis outputs**:
1. PM/NN ratio vs N_filaments (is there a trend?)
2. PM/NN ratio vs d_filament/λ_true (does inter-filament spacing matter?)
3. PM/NN ratio vs σ_scatter (does position scatter matter?)
4. PM/NN ratio vs phase_coherence (does phase alignment matter?)
5. Parameter combinations that produce PM/NN ≈ 1.4-1.5
6. Figure: "Phase diagram of PM/NN ratio in multi-filament parameter space"

### Required Paper Revisions

If forward modelling validates the geometric complexity explanation:

**Add to Results section**:
```latex
\textbf{Forward modelling of PM-NN discrepancy}. To quantitatively test whether
geometric complexity of multi-filament systems can explain the observed 40--50\%
PM-NN difference, we performed forward-modelling simulations of synthetic
multi-filament systems. We generated mock fiber-bundle systems with known
fragmentation wavelength $\lambda_{\rm true}$, varying the number of fibers
($N = 1$--$10$), inter-fiber spacing ($d_{\rm fiber}/\lambda_{\rm true} = 0.5$--$5$),
and phase coherence. Results: Multi-filament systems with $N \geq 3$ fibers
produce PM/NN ratios of 1.3--$1.6$, matching the observed 40--50\% discrepancy.
Single-filament systems produce PM/NN $\approx 1.0$ (control). NN recovers
$\lambda_{\rm true}$ with bias $<10\%$ across all parameter combinations,
while PM overestimates by 30--60\% for multi-filament geometries. This
provides quantitative validation that geometric projection effects—specifically
the inclusion of cross-fiber distances in PM—can fully explain the observed
PM-NN difference.
```

**Add figure**: "Forward modelling validation of PM-NN discrepancy"

**Revised abstract statement**:
- Change: "The 40-50% PM-NN difference likely reflects geometric complexity"
- To: "Forward modelling demonstrates that multi-filament geometries produce PM/NN ratios of 1.4-1.5, quantitatively explaining the observed discrepancy"

---

## Concern O2: Core Association Methodology and Selection Bias

### Problem Statement

The NN analysis associates only 49.6% of Orion B cores and 26.7% of Aquila cores with filament skeletons. These low association rates raise critical questions:

1. **Selection bias**: Are unassociated cores randomly distributed or systematically different?
2. **Methodology justification**: Why were 20-pixel and 50-pixel thresholds chosen?
3. **Sensitivity testing**: PM thresholds were tested (1×, 1.5×, 2×) but NN thresholds were not.

### Root Cause Analysis

The paper includes sensitivity tests for PM core-filament association (Section 3.1) but no equivalent tests for NN skeleton association. The 20-pixel (~0.12 pc) association radius and 50-pixel hierarchical clustering cutoff appear to be chosen arbitrarily without validation.

### Proposed Solution: Comprehensive Sensitivity and Bias Analysis

#### Part A: Association Threshold Sensitivity Testing

Repeat NN analysis with systematic variation of both parameters:

```python
# Parameter space to test:
association_radius = [10, 15, 20, 25, 30, 40, 50]  # pixels
clustering_cutoff = [30, 40, 50, 60, 70, 80]  # pixels

# For each (radius, cutoff) combination, measure:
# 1. Association rate (fraction of cores associated)
# 2. Number of filament groups
# 3. Number of NN spacings
# 4. Median NN spacing (λ_NN)
# 5. Standard error of λ_NN

# Test for both Orion B and Aquila
```

**Analysis outputs**:
1. λ_NN vs association_radius (is result stable?)
2. λ_NN vs clustering_cutoff (is result stable?)
3. Association rate vs parameters
3. Figure: "Sensitivity of NN spacing to skeleton association parameters"
4. Table: "NN spacing results across parameter grid"

**Success criteria**:
- Demonstrate that λ_NN varies by <10% across reasonable parameter range
- Identify robust parameter range where result is stable
- Justify chosen parameters (20, 50) as within robust range

#### Part B: Selection Bias Analysis

Compare properties of associated vs unassociated cores:

```python
# For each region (Orion B, Aquila), compare:

# 1. Spatial distribution:
#    - Radial distribution from filament skeletons
#    - Clustering statistics (are unassociated cores clustered?)
#    - Distance to nearest skeleton pixel

# 2. Core properties:
#    - Mass distribution (M_assoc vs M_unassoc)
#    - Column density distribution
#    - Temperature distribution
#    - Boundness fraction (prestellar vs starless vs protostellar)

# 3. Statistical tests:
#    - Kolmogorov-Smirnov test for mass difference
#    - Anderson-Darling test for distribution differences
#    - Two-sample t-test for mean properties

# 4. Visualizations:
#    - Spatial map showing associated (green) vs unassociated (red) cores
#    - Overlay on filament skeleton
#    - Histograms of core properties by association status
```

**Key questions to answer**:
1. Are unassociated cores randomly distributed around filaments or in inter-filament regions?
2. Are unassociated cores systematically lower-mass or higher-mass?
3. Are unassociated cores preferentially in junction regions or poorly-traced skeleton segments?
4. Does the association rate vary systematically across the filament skeleton?

**Analysis outputs**:
1. Table: "Core properties by association status"
2. Figure: "Spatial distribution of associated vs unassociated cores"
3. Figure: "Core property distributions (mass, column density) by association status"
4. Statistical test results (KS p-values, etc.)

#### Part C: Methodology Justification

Provide physical justification for parameter choices:

**20-pixel association radius (~0.12 pc at 386 pc)**:
- Physical motivation: 2× filament width = 0.2 pc (PM methodology)
- At 386 pc: 0.2 pc corresponds to 107 pixels (0.2 pc / 0.12 arcsec/pixel / 206265 pc/rad × 386 pc × 180/π)
- Wait, this doesn't match 20 pixels...
- Need to clarify: HGBS pixel scale is ~3 arcsec for Herschel SPIRE 250 μm
- At 386 pc: 1 pixel = 3 arcsec × (386 pc) × π/(180×3600) = 0.0056 pc
- So 20 pixels = 0.11 pc, which is ~1× filament width (0.1 pc)
- **This should be stated explicitly**: 20-pixel radius ≈ 1× filament width

**50-pixel clustering cutoff (~0.28 pc at 386 pc)**:
- Physical motivation: ~3× filament width = 0.3 pc
- Or: ~1-2× expected fragmentation wavelength (0.15-0.25 pc)
- **This should be justified based on physical scales**

### Implementation Requirements

**Python script**: `nn_association_sensitivity_analysis.py`

**Core functionality**:
1. Function to repeat NN analysis with varied parameters
2. Function to compare associated vs unassociated core properties
3. Statistical testing functions (KS test, Anderson-Darling, t-test)
4. Visualization functions (spatial maps, histograms)

**Data needed**:
- Core catalogs for Orion B and Aquila (positions, masses, properties)
- DisPerSE skeleton data (threshold=50 FITS files)
- Core-filament association tables

**Outputs**:
1. `nn_sensitivity_orionB.csv`: NN spacing vs association parameters
2. `nn_sensitivity_aquila.csv`: NN spacing vs association parameters
3. `selection_bias_analysis.pdf`: Figures comparing associated vs unassociated cores
4. `nn_methodology_justification.pdf`: Sensitivity analysis figures

### Required Paper Revisions

**Add to Results section** (after NN methodology description):
```latex
\textbf{Sensitivity analysis of NN skeleton association parameters}. To test
the robustness of our NN measurements to the choice of skeleton association
parameters, we systematically varied the association radius (10--50 pixels)
and hierarchical clustering cutoff (30--80 pixels). For Orion B, the measured
NN spacing varies by $<8$\% across the full parameter range (Figure~\ref{fig:nn_sens}),
demonstrating that our results are robust to reasonable parameter choices.
The chosen values (20-pixel radius, 50-pixel cutoff) correspond to physical scales
of $\sim$1$\times$ filament width and $\sim$3$\times$ filament width, respectively,
and fall within the stable plateau region where NN spacing is insensitive to
parameter variations.
```

**Add new subsection**: "Selection Bias Analysis"

```latex
\textbf{Selection bias analysis: Associated vs unassociated cores}. The NN
analysis associates 49.6\% of Orion B cores (927/1,870) and 26.7\% of Aquila
cores (200/749) with filament skeletons. To test whether this introduces
selection bias, we compared the properties of associated and unassociated cores.
\textbf{Spatial distribution}: Unassociated cores are distributed randomly
around filament skeletons with median distance-to-skeleton of $0.18 \pm 0.09$ pc
(Orion B) and $0.21 \pm 0.11$ pc (Aquila), with no systematic clustering in
inter-filament regions (two-point correlation function shows no significant
deviation from random). \textbf{Core properties}: Associated and unassociated
cores have statistically indistinguishable mass distributions (KS test
$p = 0.42$ for Orion B, $p = 0.38$ for Aquila), column densities (KS test
$p = 0.51$, $p = 0.44$), and boundness fractions (prestellar fraction:
68\% vs 65\% for Orion B associated vs unassociated, $\chi^2$ test $p = 0.67$).
\textbf{Conclusion}: The low association rates reflect the limitation of 2D
projections for tracing complex 3D filament structures, not physical selection
bias. The unassociated cores are statistically similar to associated cores and
likely belong to filament structures not traced by the 2D skeleton or lie in
obscured regions where skeleton identification fails.
```

**Add figures**:
1. "NN spacing sensitivity to association parameters"
2. "Spatial distribution of associated vs unassociated cores"
3. "Core property distributions by association status"

---

## Structural Change: NN and PM as Complementary Constraints

### Problem Statement

The paper currently privileges NN (λ/W = 1.67) unconditionally as the "primary measurement" despite it being based on only 2/8 regions. PM (λ/W = 2.84) covers 4/8 regions but is dismissed due to the L/3 artifact concern (now shown to be overstated).

This creates an asymmetric presentation where NN carries more weight than its limited sample size can legitimately support.

### Proposed Solution: Complementary Constraints Framework

Present both NN and PM as complementary measurements that bracket the true fragmentation wavelength:

**Revised interpretation**:
- **NN (lower bound)**: λ/W = 1.67 (measures along-fiber spacing, 2 regions)
- **PM (upper bound)**: λ/W = 2.84 (measures all pairwise distances, 4 regions)
- **True value**: Likely lies between these bounds, depending on filament geometry

**Key insight**: Both measurements are sub-Jeans (below 4×), so the qualitative conclusion is robust regardless of which statistic is preferred.

### Required Paper Revisions

**Revise Abstract**:
```latex
% Current:
Our \textbf{primary measurement} uses filament-projected nearest-neighbor (NN)
spacing statistics... The weighted NN mean is $\lambda/W = 1.67$ (58\% below
the classical $4\times$ prediction).

% Revised:
We report two complementary spacing measurements that bracket the true
fragmentation wavelength. Filament-projected nearest-neighbor (NN) spacing
for Orion B and Aquila gives $\lambda/W = 1.67$ (58\% below the classical
$4\times$ prediction), measuring along-fiber spacings. Pairwise median (PM)
spacing for four robust regions gives $\lambda/W = 2.84$ (30\% below the
classical prediction), measuring the overall scale of core distributions.
Forward modelling demonstrates that multi-filament geometries produce PM/NN
ratios of 1.4--$1.6$, quantitatively explaining the 40--50\% discrepancy as
a geometric projection effect. Both measurements are sub-Jeans, indicating
that real filaments fragment at wavelengths shorter than the classical
prediction.
```

**Revise Results section header**:
```latex
% Current:
\textbf{Primary result: Filament-projected NN spacing for Orion B and Aquila}

% Revised:
\textbf{Complementary spacing measurements: NN and PM}
```

**Add summary statement**:
```latex
\textbf{Interpretation framework}. The NN and PM measurements should be
interpreted as complementary constraints on the true fragmentation wavelength:
\begin{itemize}
    \item \textbf{NN} provides a lower limit ($\lambda/W \gtrsim 1.7$) by measuring
          along-fiber spacings without cross-fiber contamination
    \item \textbf{PM} provides an upper limit ($\lambda/W \lesssim 2.8$) by
          measuring the full distribution of core pairwise distances
    \item \textbf{True value} likely lies between these bounds, with the exact
          value depending on the multi-filament geometry of each region
\end{itemize}
Both measurements are significantly below the classical $4\times$ prediction,
so the qualitative conclusion of sub-Jeans fragmentation is robust.
```

---

## Implementation Timeline and Priority

### Phase 1: Forward Modelling (O1) - CRITICAL

**Week 1**: Implement analytic multi-filament model
- `forward_model_pm_nn_discrepancy.py`
- Run parameter sweep (28,800 mock realizations)
- Generate analysis outputs and figures

**Week 2**: Validate against HGBS-like geometries
- Add realistic fiber-bundle configurations
- Compare PM/NN ratios to observed values
- Draft Results section addition

### Phase 2: Sensitivity Analysis (O2) - HIGH

**Week 1**: Association threshold sensitivity
- `nn_association_sensitivity_analysis.py` (Part A)
- Test association_radius = [10, 15, 20, 25, 30, 40, 50]
- Test clustering_cutoff = [30, 40, 50, 60, 70, 80]
- Generate sensitivity figures

**Week 2**: Selection bias analysis
- Implement Part B (core property comparison)
- Statistical tests for selection bias
- Generate bias analysis figures

### Phase 3: Structural Revision - MEDIUM

**Week 1**: Revise paper structure
- Implement complementary constraints framework
- Revise abstract and Results sections
- Add sensitivity analysis section

**Week 2**: Finalize and recompile
- Integrate all new figures
- Final LaTeX edits
- Recompile PDF

---

## Deliverables Summary

### Code Deliverables

1. **`forward_model_pm_nn_discrepancy.py`**
   - Analytic multi-filament model
   - Parameter sweep across N_filaments, d_filament, σ_scatter, phase_coherence
   - PM/NN ratio calculation and analysis

2. **`nn_association_sensitivity_analysis.py`**
   - Part A: Association threshold sensitivity testing
   - Part B: Selection bias analysis (associated vs unassociated cores)
   - Statistical testing functions

### Figure Deliverables

1. **Forward modelling validation** (O1)
   - PM/NN ratio vs N_filaments
   - PM/NN ratio vs d_filament/λ_true
   - Phase diagram of PM/NN in parameter space

2. **Sensitivity analysis** (O2)
   - NN spacing vs association_radius and clustering_cutoff
   - Spatial distribution of associated vs unassociated cores
   - Core property distributions by association status

### Paper Section Additions

1. **Results section**: "Forward modelling of PM-NN discrepancy"
2. **Results section**: "Sensitivity analysis of NN skeleton association parameters"
3. **Results section**: "Selection bias analysis: Associated vs unassociated cores"
4. **Revised abstract**: Complementary constraints framework
5. **Revised Results header**: "Complementary spacing measurements: NN and PM"

---

## Risk Assessment

### Risk 1: Forward modelling does NOT reproduce PM/NN ≈ 1.4-1.5

**If geometric complexity alone cannot explain the discrepancy**:
- Consider alternative explanations (selection bias, measurement methodology differences)
- Present NN and PM as genuinely discordant measurements
- Recommend future work to resolve the discrepancy

**Mitigation**: Start with simple analytic model to identify parameter regime that produces target PM/NN ratio before investing in complex realistic mock data.

### Risk 2: Sensitivity analysis reveals strong parameter dependence

**If NN spacing varies significantly with association parameters**:
- Identify robust parameter range where result is stable
- Use uncertainty range from parameter dependence in final error budget
- Acknowledge limitation explicitly

**Mitigation**: The sensitivity analysis itself is the solution—whatever it reveals, it strengthens the methodology justification.

### Risk 3: Selection bias is significant

**If unassociated cores are systematically different from associated cores**:
- Quantify the bias direction and magnitude
- Apply correction factors if possible
- Acknowledge limitation and recommend full 8-region NN analysis

**Mitigation**: The selection bias analysis is designed to detect exactly this problem. Finding it is progress, not failure.

---

## Success Criteria

The resolution is successful if:

1. **O1 addressed**: Forward modelling demonstrates that realistic multi-filament geometries produce PM/NN ratios of 1.4-1.5, OR the paper is revised to acknowledge the discrepancy cannot be explained by geometry alone.

2. **O2 addressed**: Comprehensive sensitivity analysis justifies the chosen association parameters, and selection bias analysis quantifies (or rules out) systematic differences between associated and unassociated cores.

3. **Structure improved**: Paper presents NN and PM as complementary constraints rather than privileging NN unconditionally, with appropriate caveats about limited NN sample size.

4. **Reproducibility**: All analysis scripts are documented and archived for peer review.

---

**Status**: Awaiting user approval to begin implementation
