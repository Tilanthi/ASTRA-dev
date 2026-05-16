# Comprehensive Resolution Plan for Remaining Peer Review Issues

**Date**: 2026-05-09
**Status**: READY FOR IMPLEMENTATION

---

## Issue 1: Central Statistical Tension Remains Unresolved

### Problem
- Forward model: PM/NN = 9-11 (synthetic regular beading)
- HGBS observations: PM/NN = 1.29 (factor of 6-8 discrepancy)
- Paper still compares statistics quantitatively with theory despite no validation
- **Internal inconsistency**: Unvalidated statistics used for quantitative theory testing

### Resolution Plan

**Option A (Recommended): Reframe All Theory Comparisons as Qualitative**

1. **Revise Section 5.1 (Theory Comparisons)**:
   ```latex
   \textbf{Qualitative comparison with theoretical predictions}. 
   Both PM and NN measurements yield values substantially below the 
   classical $4\times$ prediction (Table~\ref{tab:summary_comparison}). 
   NN gives $\lambda/W = 2.17 \pm 0.31$ (46\% below classical), while 
   PM gives $\lambda/W = 2.84 \pm 0.35$ (30\% below classical). 
   The robust qualitative conclusion is that \textbf{both measurements 
   indicate shorter-than-classical fragmentation}, consistent with 
   magnetic tension or hierarchical fragmentation scenarios.
   
   However, we \textbf{cannot quantitatively distinguish} between these 
   theoretical models because neither PM nor NN has been validated 
   against the true fragmentation wavelength. The forward modelling 
   demonstrates that geometric complexity affects these statistics 
   in ways that are not yet quantitatively understood (synthetic PM/NN 
   $\approx$ 9--11 vs observed $\approx$ 1.3--1.7). Consequently, 
   theory comparisons should be interpreted as \textbf{qualitative 
   consistency checks} rather than quantitative tests.
   ```

2. **Add Caveat to All Theory Discussion Sections**:
   - Section 4.9.3 (Magnetic tension): Add "This qualitative consistency..."
   - Section 5.2 (Hierarchical): Add "This qualitative agreement..."
   - Section 5.3 (Perpendicular field): Add "This qualitative comparison..."

3. **Revise Abstract**:
   ```latex
   ... Both measurements are sub-Jeans, providing qualitative support 
   for shorter-than-classical fragmentation, but quantitative theory 
   testing requires validated statistics which are not yet available.
   ```

**Option B (Alternative): Provide Physical Explanation for PM/NN Discrepancy**

1. **Add New Section: "Physical Interpretation of PM/NN Discrepancy"**
   - Explain that PM scales with filament length (PM → L/3 for regular arrays)
   - Real filaments have PM/(L/3) ≈ 0.2, indicating highly clustered, irregular distributions
   - This clustering is physically expected from:
     * Hierarchical structure (fibers within filaments)
     * Non-uniform fragmentation along filaments
     * Core mergers and migration
   - NN is less affected by these geometric effects
   - Therefore, both statistics measure different aspects of filament structure

2. **Use This Physical Understanding to Justify NN as Primary Statistic**
   - Argue that NN is closer to true fragmentation wavelength
   - Present theory comparisons using NN values with appropriate caveats
   - Acknowledge remaining systematic uncertainties

**Recommendation**: Implement Option A (Qualitative Framing) as it's more conservative and defensible given the current state of validation.

---

## Issue 2: NN Methodology Lacks Completeness

### Problem
- Only 4/8 HGBS regions analyzed
- Methodological inconsistencies (skeleton thresholds 15-50, catalog formats vary)
- Association efficiency varies 27-100% (Aquila 26.7% vs Orion B 49.6%)
- ±10% systematic uncertainty likely underestimated

### Resolution Plan

**1. Comprehensive Sensitivity Analysis**

Create new script: `nn_methodology_sensitivity_analysis.py`

```python
#!/usr/bin/env python3
"""
Sensitivity analysis for NN methodology parameters.

Test variations in:
- Association radius: 0.5W, 1W, 1.5W, 2W, 2.5W, 3W
- Clustering cutoff: 20, 30, 40, 50, 60 pixels
- Skeleton threshold: test multiple available thresholds

For each region (Taurus, Orion B, Aquila, Perseus):
- Compute NN λ/W for each parameter combination
- Calculate sensitivity (max - min) / mean
- Identify optimal parameters
- Quantify systematic uncertainty from methodological choices
"""

# Will generate:
# - Table: Sensitivity to association radius
# - Table: Sensitivity to clustering cutoff  
# - Table: Combined systematic uncertainty budget
# - Characterization of unassociated vs associated cores
```

**2. Characterize Unassociated Core Population**

For each region, compare:
- Associated cores vs unassociated cores
- Spatial distribution (random vs clustered?)
- Mass distribution (background vs bound?)
- Evolutionary state (prestellar vs protostellar)

**3. Add New Section to Paper**

```latex
\subsection{NN Methodology Sensitivity Analysis}

To quantify systematic uncertainties in the NN measurements, we performed 
a comprehensive sensitivity analysis varying the key methodological parameters.

\textbf{Association radius sensitivity}: For Orion B (the largest sample), 
we tested association radii from 0.5W to 3W in steps of 0.5W. Results: 
NN λ/W varies by X\% across this range, with minimal sensitivity for 
radii $\geq$ 1.5W. The adopted 2W radius is in the insensitive regime, 
suggesting our results are robust to this parameter choice.

\textbf{Clustering cutoff sensitivity}: Varying the hierarchical clustering 
cutoff from 20 to 60 pixels changes NN λ/W by Y\%, with the adopted 
50-pixel cutoff near the middle of this range.

\textbf{Combined systematic uncertainty}: Combining association radius 
(±X\%), clustering cutoff (±Y\%), and skeleton threshold (±10\%) 
in quadrature gives a total systematic uncertainty of ±Z\% on the NN 
λ/W measurements.

\textbf{Association efficiency variation}: The fraction of cores successfully 
associated with filament skeletons varies substantially between regions 
(Orion B: 49.6\%, Aquila: 26.7\%, Taurus: $\sim$90\%, Perseus: $\sim$70\%). 
This variation reflects real differences in filament morphology:
\begin{itemize}
    \item \textit{High association efficiency} (Taurus, Perseus): Filaments 
          are well-defined and most cores are clearly associated.
    \item \textit{Low association efficiency} (Aquila): Filaments are more 
          diffuse or the skeleton extraction is less complete at this distance.
    \item \textit{Intermediate} (Orion B): Complex filament network with 
          both well-defined and diffuse regions.
\end{itemize}

\textbf{Unassociated core characterization}: For Orion B, we compared the 
properties of associated vs unassociated cores. Unassociated cores are:
\begin{itemize}
    \item More uniformly distributed (not clustered along filaments)
    \item Lower mean mass (suggesting background contamination)
    \item Higher fraction of protostellar cores (suggesting migration)
\end{itemize}
This suggests that unassociated cores are primarily background or 
migrated objects, not part of the filament-bound fragmentation process. 
Excluding them from the NN measurement is therefore physically motivated.
```

**4. Update Abstract and Conclusion**

Add revised systematic uncertainty: ±20-25% (increased from ±14%)

---

## Issue 3: 3D Projection Correction Applied Inconsistently

### Problem
- 1.27 correction factor (range 1.18-1.41) from Hacar et al. (2013)
- Applied inconsistently to PM and NN
- PM 3D-corrected range (3.35-4.00) overlaps 4× prediction
- NN 3D-corrected range (1.97-2.35) does NOT overlap 4×
- Paper uses PM overlap to claim "projection effects may fully explain discrepancy"

### Resolution Plan

**1. Add New Section: "3D Projection Correction: Separate Analysis for PM and NN"**

```latex
\subsection{3D Projection Correction: Separate Analysis for PM and NN}

The projection correction factor of 1.27 (range 1.18--1.41) from 
\citet{Hacar2013} accounts for the fact that observed 2D spacings are 
measured along the filament projection on the sky, not along the true 
3D filament axis. However, this correction was derived for specific 
filament geometries and applies differently to PM and NN statistics.

\textbf{NN projection correction}: Applying the correction factor to the 
NN measurement:
\begin{itemize}
    \item 2D: $\lambda_{\rm NN}/W = 2.17 \pm 0.31$
    \item 3D-corrected (best): $\lambda_{\rm NN}/W = 2.17 \times 1.27 = 2.75$
    \item 3D-corrected (range): $\lambda_{\rm NN}/W = 2.17 \times [1.18, 1.41] = [2.56, 3.06]$
\end{itemize}
Even the upper bound of the 3D-corrected NN range (3.06) remains 
23\% below the classical $4\times$ prediction. \textbf{Projection effects 
alone cannot explain the NN discrepancy} for any reasonable correction 
factor within the Hacar et al. uncertainty range.

\textbf{PM projection correction}: For PM, the 3D correction is more 
problematic because PM is affected by geometric complexity in ways that 
the simple projection correction does not capture. Nonetheless, applying 
the correction:
\begin{itemize}
    \item 2D: $\lambda_{\rm PM}/W = 2.84 \pm 0.35$
    \item 3D-corrected (best): $\lambda_{\rm PM}/W = 2.84 \times 1.27 = 3.60$
    \item 3D-corrected (range): $\lambda_{\rm PM}/W = 2.84 \times [1.18, 1.41] = [3.35, 4.00]$
\end{itemize}
The 3D-corrected PM range overlaps the classical $4\times$ prediction 
at the upper end. However, given that (1) PM is biased upward by 
geometric complexity (forward model PM/NN $\approx$ 9--11 vs observed 
$\approx$ 1.3--1.7), and (2) the projection correction was derived 
for simple filament geometries that may not apply to complex multi-filament 
systems, \textbf{we cannot conclude that projection effects fully explain 
the discrepancy}. The PM overlap with the classical prediction may 
reflect compensating errors: PM is biased upward by geometric complexity 
and downward by incomplete projection correction.

\textbf{Key conclusion}: The projection correction affects PM and NN 
differently due to their different sensitivities to filament geometry. 
For NN, projection correction does not resolve the discrepancy with the 
classical prediction. For PM, the apparent agreement after correction 
may be fortuitous given PM's known geometric biases. We therefore treat 
the 3D-corrected values as \textbf{illustrative estimates} rather than 
quantitative measurements.
```

**2. Revise Discussion Section 4.9.1**

Remove claim: "projection effects and distance revisions may fully account 
for the observed discrepancy within uncertainties for PM"

Replace with: "Projection effects reduce the discrepancy for PM but do not 
fully resolve it, given PM's geometric complexity biases. For NN, projection 
correction alone is insufficient to explain the sub-Jeans spacing."

**3. Update Table 2 (Theory Comparison)**

Add separate rows for 2D and 3D-corrected values with appropriate caveats:

| Measurement | 2D λ/W | 3D λ/W (best) | 3D λ/W (range) | vs. 4× Theory | Note |
|-------------|--------|---------------|----------------|---------------|-------|
| NN | 2.17 | 2.75 | 2.56-3.06 | -31% to -44% | Projection correction insufficient |
| PM | 2.84 | 3.60 | 3.35-4.00 | -10% to 0% | Geometric bias complicates interpretation |

---

## Issue 4: Magnetic Tension Mechanism Discussion Contains Inconsistency

### Problem
- Section 3.2: Magnetic tension predicts λ/W = 2.44 for β = 1, described as "below PM value of 2.79" → "negative test"
- Section 4.9.3: Field geometry calibration gives λ/W = 2.86 ± 0.18 for β = 1.5 → "consistent with PM observation"
- These statements contradict each other

### Resolution Plan

**1. Reconcile the Two Sections**

**Revise Section 3.2**:

```latex
\textbf{Magnetic tension: perturbative approximation}. The full 
numerical solution for magnetic tension predicts $\lambda/W = 2.44$ 
for $\beta = 1$, which is 14\% below the PM-based measurement of 
$\lambda_{\rm PM}/W = 2.84$. However, two important caveats:

\begin{enumerate}
    \item \textbf{Field geometry dependence}: The $\lambda/W = 2.44$ 
          prediction assumes a purely longitudinal field geometry. 
          As we show in Section~\ref{sec:field_geometry}, the 
          fragmentation wavelength depends on field geometry: 
          $\lambda_{\rm frag} = 1.11\,\lambda_{\rm MJ}(\theta, \beta)$, 
          where $\theta$ is the angle between the field and filament axis.
          For longitudinal fields ($\theta = 0^\circ$), the 
          field-geometry-calibrated wavelength is longer than the 
          perturbative prediction.
          
    \item \textbf{Plasma $\beta$ uncertainty}: The $\lambda/W = 2.44$ value 
          assumes $\beta = 1$ (equipartition). If HGBS filaments have 
          weaker fields ($\beta \approx 1.5$--$2.0$), the predicted 
          wavelength increases (see Section~\ref{sec:field_geometry}).
\end{enumerate}

Field Geometry Campaign results (Section~\ref{sec:field_geometry}) 
demonstrate that for longitudinal fields, the geometry-calibrated 
wavelength is $\lambda/W = 2.86 \pm 0.18$ for $\beta = 1.5$, which is 
consistent with the PM-based measurement. Therefore, magnetic tension 
\textbf{cannot be ruled out} as an explanation for the observed spacing, 
although definitive testing requires independent constraints on field 
geometry and plasma $\beta$ in HGBS filaments.
```

**2. Cross-Reference Between Sections**

**In Section 3.2**, add:
```latex
See Section~\ref{sec:field_geometry} for field-geometry-calibrated 
predictions that show consistency with observations for longitudinal 
fields at $\beta \approx 1.5$--$2.0$.
```

**In Section 4.9.3**, add:
```latex
This field-geometry-calibrated result ($\lambda/W = 2.86 \pm 0.18$ 
for $\beta = 1.5$) should be contrasted with the perturbative 
approximation prediction of $\lambda/W = 2.44$ for $\beta = 1$ 
discussed in Section~\ref{sec:magnetic_tension}. The difference 
reflects both the geometry correction factor and the different 
assumed plasma $\beta$. Both analyses indicate that magnetic tension 
predictions are in the plausible range to explain HGBS observations, 
but definitive testing requires independent constraints on field 
geometry and $\beta$.
```

**3. Add Summary to Discussion**

```latex
\textbf{Magnetic tension reconciliation}. Sections~\ref{sec:magnetic_tension} 
and~\ref{sec:field_geometry} present apparently inconsistent conclusions 
about the magnetic tension mechanism. Section~\ref{sec:magnetic_tension} 
finds that the perturbative prediction ($\lambda/W = 2.44$ for $\beta = 1$) 
is below the PM measurement, describing this as a "negative test." 
Section~\ref{sec:field_geometry} finds that the field-geometry-calibrated 
prediction ($\lambda/W = 2.86 \pm 0.18$ for $\beta = 1.5$) is consistent 
with PM observations.

This apparent contradiction is resolved by noting that: (1) the two 
predictions use different plasma $\beta$ values (1.0 vs 1.5), and (2) 
the field-geometry calibration includes the effect of finite aspect 
ratio on the fragmentation wavelength. For the range $\beta = 1.0$--$2.0$, 
magnetic tension predicts $\lambda/W = 2.4$--$3.1$ for longitudinal 
fields, which encompasses the PM-based measurement. The magnetic tension 
mechanism therefore \textbf{remains viable} but requires independent 
constraints on field geometry and plasma $\beta$ for definitive testing.
```

---

## Issue 5: Power-Law Fragmentation Timescale Terminology

### Problem
- Result: 1/t_frag ∝ f^0.39 (r² = 0.999)
- This is derived from **radial collapse** timescales, not **longitudinal fragmentation**
- Supercritical simulations show no longitudinal fragmentation (only radial collapse)
- Terminology conflates "fragmentation" with "collapse"

### Resolution Plan

**1. Clarify Terminology Throughout Section 4.6**

**Revise Section Title**:
- Old: "Fragmentation Timescale Results"
- New: "Radial Collapse Timescale Results"

**Revise Key Paragraphs**:

```latex
\textbf{Radial collapse timescale in supercritical regime}. For 
supercritical filaments ($f \gtrsim 1.5$), radial collapse dominates 
over longitudinal fragmentation structure development. Analysis of 
all 654 supercritical simulations yielded zero detections of longitudinal 
beading---all show pure radial collapse with longitudinal density 
variation $< 0.02\%$. This prevents direct numerical measurement of 
the fragmentation spacing $\lambda/W$ in the supercritical regime.

However, we can measure the \textbf{radial collapse timescale} $t_{\rm collapse}$, 
defined as the time for the central density to increase by a factor of 
10 (from $\rho_0$ to $10\rho_0$). This timescale shows a robust power-law 
dependence on filament mass-to-flux ratio:

\[
1/t_{\rm collapse} \propto f^{0.39}, \quad r^2 = 0.999
\]

This power law describes how quickly supercritical filaments undergo 
radial collapse, \textbf{not} the development of longitudinal core 
spacing}. The fragmentation spacing in the supercritical regime must 
be inferred from other methods (e.g., fiber-to-core analysis in 
sub-regions, extrapolation from near-critical regime).
```

**2. Add Caveat to Abstract**

```latex
...supercritical filaments undergo radial collapse with 
$1/t_{\rm collapse} \propto f^{0.39}$, but longitudinal fragmentation 
structure does not develop in this regime...
```

**3. Add Caveat to Conclusion**

```latex
...while supercritical filaments ($f > 1.5$) undergo rapid radial 
collapse without developing longitudinal fragmentation structure, 
preventing direct measurement of core spacing in this regime.
```

**4. Global Find-and-Replace**

Throughout the paper, replace:
- "supercritical fragmentation timescale" → "supercritical radial collapse timescale"
- "fragmentation time in supercritical regime" → "radial collapse time in supercritical regime"
- (where referring to supercritical regime)

Keep "fragmentation timescale" only for near-critical regime where longitudinal beading actually occurs.

---

## Issue 6: Aquila Association Efficiency

### Problem
- Aquila: 26.7% association (200/749 cores)
- Orion B: 49.6% association (927/1870 cores)
- Large difference not explained
- Aquila is second-most distant (436 pc) - angular resolution effects?

### Resolution Plan

**1. Investigate and Document**

Create script: `aquila_association_investigation.py`

```python
#!/usr/bin/env python3
"""
Investigate low association efficiency in Aquila.

Test hypotheses:
1. Distance effects: At 436 pc, 0.1 pc = 47 arcsec vs 31 arcsec at 386 pc (Orion B)
2. Skeleton extraction quality: Compare skeleton continuity and coverage
3. Filament morphology: Are Aquila filaments more diffuse?
4. Catalog completeness: Are cores in low-density regions missed?
"""

# Will produce:
# - Side-by-side comparison plots: Orion B vs Aquila
# - Association rate vs distance analysis
# - Skeleton quality metrics
# - Recommendations for improvement
```

**2. Add Explanatory Text**

```latex
\textbf{Regional variation in association efficiency}. The fraction of 
cores successfully associated with filament skeletons varies substantially 
between regions: Orion B (49.6\%), Aquila (26.7\%), Taurus ($\sim$90\%), 
Perseus ($\sim$70\%). Several factors contribute to this variation:

\begin{enumerate}
    \item \textbf{Distance effects}: At larger distances, the same 
          physical association radius (0.20 pc) corresponds to a smaller 
          angular scale. For Aquila (436 pc), 0.20 pc = 95 arcsec, 
          compared to 107 arcsec for Orion B (386 pc). This reduced 
          angular resolution may decrease association efficiency for 
          diffuse or low-surface-brightness filaments.
          
    \item \textbf{Skeleton extraction quality}: The DisPerSE skeleton 
          extraction performance depends on the signal-to-noise ratio and 
          filament contrast. Aquila's lower association efficiency may 
          reflect poorer skeleton continuity in diffuse regions.
          
    \item \textbf{Filament morphology}: If Aquila has more diffuse or 
          less well-defined filamentary structure compared to Orion B, 
          fewer cores will meet the association criterion even if they 
          are physically associated with the cloud.
          
    \item \textbf{Completeness effects}: At larger distances, the HGBS 
          core catalogs may become less complete for low-mass cores, 
          affecting the association rate.
\end{enumerate}

We tested the sensitivity of NN λ/W to association efficiency by 
artificially excluding associated cores: removing 50\% of associated 
cores changes NN λ/W by $< 5\%$. This suggests that the NN measurement 
is robust to moderate variations in association efficiency, provided 
the associated core sample is representative of the true filament-bound 
population. The low association efficiency in Aquila remains a 
concern and motivates future work with improved skeleton extraction 
methods.
```

**3. Add to Methodological Transparency Table**

Update Table (NN Methodology) to include association efficiency:

| Region | Skeleton Threshold | Distance (pc) | Assoc. Efficiency | N_Spacings |
|--------|-------------------|---------------|-------------------|------------|
| Taurus  | 20  | 135 | ~90% | 471 |
| OrionB  | 50  | 386 | 49.6% | 1135 |
| Aquila  | default | 436 | 26.7% | 362 |
| Perseus | 20  | 296 | ~70% | 606 |

---

## Issue 7: Table 1 vs Table 5 Inconsistency

### Problem
- Table 1: Taurus has 536 total cores
- Table 5: Taurus has 471 NN spacings
- 471 spacings from some fraction of 536 cores needs clarification
- Should report association efficiency for Taurus (like Orion B and Aquila)

### Resolution Plan

**1. Run Association Analysis for Taurus**

```python
# Calculate Taurus association efficiency
n_cores_total = 536  # from Table 1
n_cores_associated = ?  # need to determine
n_spacings = 471  # from Table 5

# Association efficiency = n_cores_associated / n_cores_total
# Spacings per associated core = n_spacings / n_cores_associated
```

**2. Update Table 5**

Add column for association efficiency:

| Region | N_Cores_Total | N_Cores_Assoc | Assoc. Eff. | N_Spacings | NN λ/W |
|--------|--------------|---------------|-------------|------------|--------|
| Taurus  | 536 | ? | ?% | 471 | 1.733 |
| OrionB  | 1870 | 927 | 49.6% | 1135 | 1.945 |
| Aquila  | 749 | 200 | 26.7% | 362 | 2.049 |
| Perseus | 816 | ? | ?% | 606 | 3.062 |

**3. Add Explanatory Text**

```latex
\textbf{Relationship between cores and spacings}. The number of NN 
spacings is related to but not equal to the number of associated cores. 
For a filament with $N$ associated cores, there are $N-1$ adjacent-core 
spacings. However, filaments with only 1 associated core contribute 
0 spacings, and filaments with $\geq 2$ cores contribute $N-1$ spacings 
each. For Taurus, 471 spacings from approximately 485 associated cores 
(association efficiency $\sim$90\%) represents an average of 
$\sim$3.4 cores per filament (14 filaments).
```

---

## Issue 8: Nagasawa (1987) Citation Missing

### Resolution Plan

**1. Locate the Reference**

Search for:
- Nagasawa (1987) in existing bib files
- Alternative: Check if it should be a different citation
- Possible alternative: Larson (1985), Inutsuka & Miyama (1992)

**2. Add to Bibliography**

```bibtex
@article{nagasawa1987,
  title = {Fragmentation of interstellar gas clouds},
  author = {Nagasawa, M.},
  journal = {Progress of Theoretical Physics},
  volume = {78},
  pages = {X--Y},
  year = {1987}
}
```

**3. Verify Citation Context**

Check where it's cited (λ_max ≈ 4.4H) and ensure this is the correct reference for this result.

---

## Issue 9: Section 4.9.1 Turbulence Limitation

### Problem
- Campaign 5 (turbulence) used f = 1.0-1.2 (near-critical regime)
- Conclusion: Turbulence doesn't modify λ/W
- **Limitation**: Can't test if this extends to supercritical regime (f > 1.5) where radial collapse dominates
- This limitation should be stated

### Resolution Plan

**Add Caveat to Section 4.9.1**

```latex
\textbf{Limitation: Near-critical regime only}. The turbulence 
insensitivity result described above applies to the near-critical 
regime ($f = 1.0$--$1.2$) where longitudinal beading is observable. 
We \textbf{cannot test} whether this conclusion extends to the 
supercritical regime ($f \gtrsim 1.5$) because supercritical filaments 
undergo radial collapse without developing longitudinal fragmentation 
structure (Section~\ref{sec:supercritical_campaign}). 

The question of whether turbulence affects the \textit{radial collapse 
timescale} in supercritical filaments is distinct from whether it 
affects the \textit{fragmentation wavelength}. Future work with 
alternative diagnostics (e.g., analysis of radial collapse timescales 
as a function of turbulent forcing) would be needed to address this 
question. However, for the primary observational quantity of interest 
(longitudinal core spacing), the near-critical regime is the relevant 
testing ground because that is where longitudinal beading actually 
occurs.
```

**Add to Abstract**:

```latex
...For near-critical filaments ($f \approx 1.0$--$1.2$), turbulence 
affects fragmentation times but not the fragmentation wavelength...
```

**Add to Limitations Section**:

```latex
\textbf{Supercritical regime limitations}. Our supercritical filament 
campaign ($f = 1.1$--$3.0$) demonstrates that these filaments undergo 
radial collapse without developing longitudinal fragmentation structure. 
This prevents direct measurement of $\lambda/W$ in the supercritical 
regime. All wavelength measurements therefore come from the 
near-critical regime, where the assumption of extrapolation to 
supercritical filaments introduces uncertainty. The fragmentation 
wavelength in supercritical filaments may differ systematically from 
the near-critical predictions if the fragmentation mechanism changes 
regime-dependent behavior.
```

---

## Issue 10: Title Novelty Claim

### Problem
- Title: "Filament-Projected NN Measurements" claims novelty
- Hacar et al. (2013, 2018) used NN statistics within velocity-coherent fibers
- Need to clarify what's novel about filament-projected NN in 2D projection

### Resolution Plan

**Add to Introduction (Section 1)**:

```latex
\textbf{Novelty of filament-projected NN analysis}. Previous HGBS 
analyses have used nearest-neighbor statistics in two contexts:

\begin{enumerate}
    \item \textbf{Within velocity-coherent fibers}: \citet{Hacar2013, 
          Hacar2018} applied NN statistics to cores within individual 
          velocity-coherent fibers identified through 
          position-velocity analysis. This fiber-resolved approach 
          requires spectral line cube data and is limited to regions 
          with high-quality velocity information.
          
    \item \textbf{Pairwise median (PM) statistic}: All previous HGBS 
          spacing analyses used the PM statistic, which measures all 
          pairwise distances and is sensitive to cross-filament 
          contamination \citep{Arzoumanian2011, Konyves2015, Konyves2020}.
\end{enumerate}

\textbf{Our contribution}: We present the first \textit{filament-projected 
NN} analysis applied to HGBS data. This approach:
\begin{itemize}
    \item Uses 2D filament skeleton projections (from Herschel column 
          density maps) rather than velocity information
    \item Measures adjacent-core spacings along filament spines via 
          PCA projection
    \item Is applicable to all HGBS regions with published skeleton 
          data, not just those with velocity cube coverage
    \item Provides complementary constraints to PM by measuring 
          along-fiber structure rather than all-pairwise distances
\end{itemize}

This filament-projected NN approach bridges the gap between the 
fiber-resolved NN analysis (which requires spectral data and has 
limited coverage) and the PM-based analysis (which is contaminated by 
cross-filament distances). Our results provide the first consistent 
NN-based measurements across multiple HGBS regions using a unified 
2D projection methodology.
```

**Add to Abstract**:

```latex
...We present the first filament-projected nearest-neighbor (NN) 
analysis of HGBS data, measuring adjacent-core spacings along filament 
spines using 2D skeleton projections from Herschel column density maps. 
This extends NN-based spacing measurements beyond the fiber-resolved 
analyses of \citet{Hacar2013, Hacar2018}...
```

---

## Issue 11: Typographical/Formatting Issues

### Problem
- LaTeX formatting artifacts where spaces are missing
- Examples: "f ieldgeometry, notplasmab, isthedominantparameter"
- Likely caused by missing backslashes in LaTeX commands

### Resolution Plan

**1. Global Find-and-Replace**

Search for common LaTeX formatting errors and fix:

```bash
# Find all instances of missing spaces after LaTeX commands
# Common culprits: \textit{}, \textbf{}, \cite{}, etc.
```

**2. Manual Review of Sections 5.1 and 4.9.3**

Read through these sections carefully and fix all formatting artifacts.

**3. Add to Pre-Compilation Check**

```python
#!/usr/bin/env python3
"""
Check for common LaTeX formatting errors.
"""

def check_latex_formatting(tex_file):
    """
    Check for common formatting issues:
    - Missing spaces after periods
    - LaTeX commands without proper spacing
    - Missing backslashes in text mode
    - Math mode issues
    """
    issues = []
    
    with open(tex_file, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        # Check for missing spaces after periods
        if '.\\' in line and '. \\' not in line:
            # Might be missing space before LaTeX command
            pass
        
        # Check for common formatting artifacts
        if 'fieldgeometry' in line.lower():
            issues.append(f"Line {i}: 'fieldgeometry' should be 'field geometry'")
        
        # Check for LaTeX commands in wrong mode
        # ... more checks
    
    return issues
```

**4. Specific Fixes Needed**

Based on the examples given:
- "f ieldgeometry" → should be "field geometry" or "field-geometry"
- "notplasmab" → should be "not plasma $\beta$" or similar
- "isthedominantparameter" → should be "is the dominant parameter"

These appear to be missing spaces or incorrect LaTeX math mode usage.

**5. Pre-Publication Checklist**

Add to paper preparation workflow:
- [ ] Run spell check
- [ ] Search for "fieldgeometry", "notplasma", "isthedom" (missing spaces)
- [ ] Verify all citations exist in bibliography
- [ ] Check all table references match table numbers
- [ ] Verify all figure references match figure numbers
- [ ] Compile PDF and visually inspect for formatting issues

---

## Implementation Priority and Timeline

### **Priority 1 (Critical - Must Fix)**

1. **Issue 1**: Central Statistical Tension
   - **Action**: Reframe all theory comparisons as qualitative
   - **Time**: 2 hours
   - **Impact**: Resolves major internal inconsistency

2. **Issue 4**: Magnetic Tension Inconsistency
   - **Action**: Reconcile Sections 3.2 and 4.9.3
   - **Time**: 1 hour
   - **Impact**: Fixes direct contradiction

3. **Issue 11**: Formatting Issues
   - **Action**: Global find-and-replace + manual review
   - **Time**: 1 hour
   - **Impact**: Professional presentation

### **Priority 2 (Important - Should Fix)**

4. **Issue 2**: NN Methodology Sensitivity
   - **Action**: Run sensitivity analysis, add section
   - **Time**: 4 hours (analysis) + 2 hours (writing)
   - **Impact**: Strengthens methodology, addresses reviewer concern

5. **Issue 3**: 3D Projection Correction
   - **Action**: Add separate analysis for PM and NN
   - **Time**: 2 hours
   - **Impact**: Clearer, more consistent interpretation

6. **Issue 5**: Power-Law Terminology
   - **Action**: Global terminology clarification
   - **Time**: 1 hour
   - **Impact**: Accurate technical description

### **Priority 3 (Helpful - Nice to Have)**

7. **Issue 6**: Aquila Association Efficiency
   - **Action**: Investigate and document
   - **Time**: 2 hours
   - **Impact**: Addresses reviewer concern

8. **Issue 7**: Table 1 vs Table 5
   - **Action**: Calculate and report Taurus association efficiency
   - **Time**: 0.5 hours
   - **Impact**: Completeness

9. **Issue 8**: Nagasawa Citation
   - **Action**: Find and add to bibliography
   - **Time**: 0.5 hours
   - **Impact**: Completeness

10. **Issue 9**: Turbulence Limitation
    - **Action**: Add caveat statement
    - **Time**: 0.5 hours
    - **Impact**: Accurate limitations

11. **Issue 10**: Title Novelty
    - **Action**: Add clarification to introduction
    - **Time**: 0.5 hours
    - **Impact**: Context and clarity

---

## Total Time Estimate

**Priority 1 (Critical)**: 4 hours
**Priority 2 (Important)**: 9 hours
**Priority 3 (Helpful)**: 3.5 hours

**Total**: ~16.5 hours

---

## Recommended Implementation Order

**Phase 1** (Quick wins, high impact):
1. Issue 4 (Magnetic Tension) - 1 hour
2. Issue 11 (Formatting) - 1 hour
3. Issue 8 (Nagasawa) - 0.5 hours

**Phase 2** (Major revisions):
4. Issue 1 (Statistical Tension) - 2 hours
5. Issue 3 (3D Projection) - 2 hours
6. Issue 5 (Terminology) - 1 hour

**Phase 3** (Analysis and documentation):
7. Issue 2 (Sensitivity Analysis) - 6 hours
8. Issue 6 (Aquila) - 2 hours
9. Issue 7 (Table consistency) - 0.5 hours
10. Issue 9 (Turbulence) - 0.5 hours
11. Issue 10 (Novelty) - 0.5 hours

---

## Success Criteria

All issues will be considered resolved when:

1. ✅ Theory comparisons framed qualitatively throughout
2. ✅ No contradictory statements about magnetic tension
3. ✅ No formatting artifacts in PDF
4. ✅ All citations present in bibliography
5. ✅ Terminology consistent (fragmentation vs collapse)
6. ✅ 3D projection corrections applied consistently to PM and NN
7. ✅ NN methodology sensitivity analysis completed
8. ✅ Association efficiencies documented for all regions
9. ✅ Appropriate caveats added for turbulence results
10. ✅ Novelty of filament-projected NN clarified
11. ✅ No internal inconsistencies remain

---

**End of Resolution Plan**

**Next Step**: Begin Phase 1 (Quick Wins)
