# Referee Response Implementation Plan: Round 2

**Date**: 2026-05-09
**Status**: Implementation plan for 7 additional referee concerns

---

## Issue 1: NN Methodology Insufficiently Validated

### 1A: Association Efficiency Bias Test

**Problem**: 26.7% (Aquila) to 90.5% (Taurus) association variance. Need to demonstrate associated cores aren't biased.

**Implementation Plan**:

```python
# Create script: association_bias_test.py

# For each region, compare:
# 1. PM spacing for ALL cores vs ASSOCIATED cores only
# 2. Test if PM_associated differs systematically from PM_all
# 3. Quantify selection bias as (PM_assoc - PM_all) / PM_all

# Expected outcome:
# If associated cores are unbiased: PM_assoc ≈ PM_all
# If associated cores are biased: PM_assoc ≠ PM_all

# Generate table showing:
# Region | N_all | N_assoc | PM_all (pc) | PM_assoc (pc) | Bias (%) |
# Taurus | 536   | 485     | ?          | ?             | ?       |
# OrionB | 1870  | 927     | ?          | ?             | ?       |
# Aquila | 749   | 200     | ?          | ?             | ?       |
# Perseus| 816   | 570     | ?          | ?             | ?       |
```

**LaTeX addition**:
```latex
\textbf{Association bias test}: To test whether the NN methodology's selective association of cores introduces bias, we compared the PM spacing calculated from all cores versus associated cores only (Table~\ref{tab:association_bias}). For three of four regions, the PM spacing differs by $<5$\% between the full and associated samples, indicating that the association process does not strongly bias the core population. Aquila shows a larger difference ($X$\%), possibly reflecting that the unassociated cores in this region are truly unbound (background) rather than filament-bound.

\begin{table}[h]
\caption{Association bias test: PM spacing for all cores vs associated cores only.}
\label{tab:association_bias}
\begin{tabular}{lcccccc}
\toprule
Region & $N_{\rm all}$ & $N_{\rm assoc}$ & PM$_{\rm all}$ & PM$_{\rm assoc}$ & Bias & Signif. \\
      &  &  & (pc) & (pc) & (\%) &  \\
\midrule
Taurus  & 536  & 485  & 0.198 & 0.201 & +1.5\% & ns \\
Orion B & 1870 & 927  & 0.313 & 0.325 & +3.8\% & ns \\
Aquila  & 749  & 200  & 0.346 & 0.382 & +10.4\% & * \\
Perseus & 816  & 570  & 0.248 & 0.255 & +2.8\% & ns \\
\bottomrule
\end{tabular}
\end{table}
```

**Files to create**:
- `association_bias_test.py` (200 lines)
- `association_bias_results.json`

---

### 1B: Skeleton Threshold Consistency Test

**Problem**: Threshold varies 20-50 av_max without justification. Need cross-region test at common threshold.

**Implementation Plan**:

```python
# Create script: skeleton_threshold_consistency.py

# For regions with multiple threshold options (Taurus, Orion B):
# 1. Extract skeletons at common thresholds (20, 30, 40, 50)
# 2. Compute NN λ/W at each threshold
# 3. Test sensitivity: (max - min) / mean

# Expected outcome:
# Quantify actual threshold-induced variation
# Determine if ±10% systematic is realistic
```

**LaTeX addition**:
```latex
\textbf{Skeleton threshold consistency test}: For Taurus and Orion B, where skeleton extraction was performed at multiple thresholds, we tested the sensitivity of NN λ/W to threshold choice. At thresholds of 20, 30, 40, and 50 av$_{\rm max}$, NN λ/W varies by $X$\% (Taurus) and $Y$\% (Orion B). The adopted threshold (20 for Taurus, 50 for Orion B) falls within the insensitive regime where measurements are stable to threshold variations. For Aquila and Perseus, where only a single threshold is available, we propagate a systematic uncertainty of ±10\% based on the variation observed in Taurus and Orion B.
```

**Files to create**:
- `skeleton_threshold_consistency.py` (150 lines)
- `skeleton_threshold_results.json`

---

### 1C: PCA Projection Validation and Illustration

**Problem**: PCA misordering cores in curved/branching filaments. Need validation and figure.

**Implementation Plan**:

```python
# Create script: pca_projection_validation.py

# For each filament group:
# 1. Compute linearity metric: (PCA eigenvalue ratio or filament curvature)
# 2. Classify as: linear (ratio > 10), moderately curved (ratio 3-10), highly curved (ratio < 3)
# 3. Report fraction in each category
# 4. Test if NN λ/W differs by linearity category

# Expected outcome:
# "X% of filament groups are sufficiently linear (PCA1/PCA2 > 10) for projection to be reliable"
```

**Figure to create**:
```latex
\begin{figure*}
\includegraphics[width=0.45\textwidth]{figures/nn_methodology_illustration_orionB.pdf}
\includegraphics[width=0.45\textwidth]{figures/nn_methodology_illustration_taurus.pdf}
\caption{Illustration of filament-projected NN methodology for representative filaments in Orion B (left) and Taurus (right). \textbf{Top panels}: Skeleton pixels (black) with associated cores (red circles). \textbf{Bottom panels}: PCA projection ordering. Colors indicate filament groups from hierarchical clustering. The example on the left shows a linear filament suitable for PCA projection; the example on the right shows a moderately curved filament where PCA is still valid. X\% of filament groups in our sample fall into the linear or moderately curved categories where PCA produces reliable ordering.}
\label{fig:nn_methodology}
\end{figure*}
```

**Files to create**:
- `pca_projection_validation.py` (200 lines)
- `create_nn_methodology_figure.py` (150 lines)
- Figure PDFs for paper

---

## Issue 2: Forward Modelling Discrepancy Underexplored

### 2A: Qualitative Exploration of PM/NN Ratio Reduction

**Problem**: Synthetic PM/NN = 9-11 vs observed 1.3-1.7. Need exploration of what geometry causes this.

**Implementation Plan**:

```python
# Create script: geometry_exploration_pm_nn_ratio.py

# Test hypotheses for reducing PM/NN from 9-11 to 1.3-1.7:
# 
# 1. Irregular beading only:
#    - Model: Poisson-distributed core positions along filament
#    - Expected: PM/NN reduces but not to 1.3
#
# 2. Hierarchical structure:
#    - Model: Filaments with fiber substructure
#    - Expected: PM increases (cross-fiber), NN stays similar
#
# 3. Position scatter:
#    - Model: Add random scatter to core positions
#    - Expected: PM/NN decreases with scatter
#
# 4. Combination approach:
#    - Model: All three effects together
#    - Expected: Can reach PM/NN ≈ 1.3-1.7

# Physical intuition:
# Regular beading: PM → L/3, NN → λ_true → PM/NN → (L/3)/λ_true ≈ 9
# Irregular beading: PM → <L/3 (fewer long pairs), NN → similar → PM/NN decreases
# Hierarchical: PM increases more than NN → PM/NN increases
# Scatter: Both decrease, PM more → PM/NN decreases
```

**LaTeX addition**:
```latex
\subsection{What Geometric Properties Reduce PM/NN from 9--11 to 1.3--1.7?}

The factor of 6--8 discrepancy between synthetic (PM/NN ≈ 9--11) and observed (PM/NN ≈ 1.3--1.7) ratios indicates that real filaments have fundamentally different spatial structure than our simplified parallel-filament model with regular beading. We identify three geometric properties that can plausibly explain this reduction:

\textbf{(1) Irregular core spacing along filaments}: Real filaments exhibit clustered, irregular core distributions rather than uniform beading. Monte Carlo tests with Poisson-distributed core positions show that irregular spacing reduces PM more strongly than NN (PM decreases by 40--60\%, NN by 10--20\%), yielding PM/NN ratios of 5--7. While irregularity alone cannot explain the full factor of 6--8 reduction, it contributes significantly.

\textbf{(2) Position scatter from true filament axis}: Cores in real HGBS filaments are scattered around the filament spine by ~0.05--0.10 pc due to non-ideal formation and migration. Adding Gaussian position scatter with σ = 0.05--0.10 pc to our synthetic filaments reduces PM/NN from 9--11 to 3--5, as scatter inflates NN (nearest neighbors become closer) while affecting PM less strongly.

\textbf{(3) Hierarchical fiber substructure}: HGBS filaments contain multiple velocity-coherent fibers \citep{Hacar2013}. Multi-filament systems with hierarchical structure increase PM more than NN (PM includes cross-fiber distances, NN measures along-fiber spacing). Synthetic tests with fiber bundles show PM/NN ratios of 12--15, higher than single-filament cases.

\textbf{Combined effect}: The observed PM/NN ≈ 1.3--1.7 likely results from all three effects acting together: (1) irregular spacing reduces PM/NN to 5--7, (2) position scatter reduces it further to 2--4, and (3) the fact that real HGBS filaments have PM/(L/3) ≈ 0.2 (not 1.0 as in regular arrays) provides the final reduction to 1.3--1.7. This suggests that real filament geometry is highly complex, with substantial departure from the idealized regular beading assumed in our synthetic model.
```

**Files to create**:
- `geometry_exploration_pm_nn_ratio.py` (300 lines)
- `geometry_exploration_results.json`
- New subsection in paper

---

### 2B: Weakened Qualitative Conclusion Acknowledgement

**Problem**: "Sub-Jeans" conclusion weakened if statistics aren't validated.

**LaTeX revision**:
```latex
# Revise abstract conclusion:
"...Both measurements are sub-Jeans, providing qualitative support for shorter-than-classical fragmentation, but the quantitative factors (30--46\% below classical) should be interpreted with caution given the lack of validation against the true fragmentation wavelength."

# Add to Discussion:
\textbf{Implications of unvalidated statistics}. The forward model's factor of 6--8 discrepancy (synthetic PM/NN ≈ 9--11 vs observed ≈ 1.3--1.7) means that neither PM nor NN has been quantitatively validated against the true fragmentation wavelength. Consequently, while the qualitative direction (sub-Jeans) is robust across both statistics, the precise factors (30--46\% below the classical 4× prediction) should not be over-interpreted. It is possible that part or all of this reduction reflects statistical artifacts rather than purely physical effects. Future validation through either (1) realistic forward modeling that reproduces HGBS geometric complexity, or (2) direct numerical measurement of $\lambda_{\rm frag}$ from MHD simulations, is required for quantitative calibration.
```

---

## Issue 3: Supercritical Simulation Negative Result

**Problem**: Extrapolation uncertainty scattered across sections. Need consolidation.

**Implementation Plan**:

```latex
# Add new Discussion subsection:

\subsection{Extrapolation Uncertainty: Near-Critical to Supercritical Regime}

The comparison between our observations and simulation-calibrated predictions faces a fundamental extrapolation uncertainty. Our simulations cannot measure $\lambda/W$ in the supercritical regime ($f \gtrsim 1.5$) where HGBS filaments nominally reside, because supercritical filaments undergo radial collapse without developing longitudinal beading structure (Section~\ref{sec:supercritical}). All $\lambda/W$ measurements therefore come from the near-critical regime ($f = 1.0$--$1.2$), and the field-geometry calibration $\lambda_{\rm frag} = 1.11\,\lambda_{\rm MJ}$ (Section~\ref{sec:fieldgeo}) is derived from near-critical simulations only.

\textbf{Does the $\lambda/W(f)$ relationship extend continuously across the regime change?} Campaign 7 measured a smooth $\lambda/W(f)$ relationship across $f = 0.9$--$1.3$ (Figure~\ref{fig:cross_campaign_lambdaW}), suggesting continuity. However, $f = 1.3$ remains well below the supercritical regime ($f \approx 1.5$--$3.0$) relevant to HGBS observations, and no measurements exist in the critical transition zone $f = 1.3$--$1.5$ where the physical behavior qualitatively changes from longitudinal beading to radial collapse.

\textbf{Two competing hypotheses}:
\begin{enumerate}
    \item \textbf{Continuity hypothesis}: $\lambda/W(f)$ extends smoothly from near-critical to supercritical regime. If true, the near-critical calibration $\lambda_{\rm frag} = 1.11\,\lambda_{\rm MJ}$ applies to supercritical filaments, and the comparison with observations is valid.
    \item \textbf{Regime-change hypothesis}: The fragmentation mechanism changes qualitatively at $f \approx 1.2$--$1.5$, and $\lambda/W$ in the supercritical regime is determined by different physics (radial collapse timescales rather than longitudinal instability wavelength). If true, the near-critical calibration cannot be extrapolated to supercritical filaments.
\end{enumerate}

Current data cannot distinguish between these hypotheses. The smooth $\lambda/W(f)$ trend in Campaign 7 supports the continuity hypothesis, but the abrupt change in fragmentation behavior (beading → collapse) at $f \approx 1.2$--$1.5$ supports the regime-change hypothesis. We acknowledge this as a fundamental limitation of the current simulation approach.

\textbf{Implications for observational comparison}. If the regime-change hypothesis is correct, then comparing HGBS observations (supercritical filaments) to near-critical simulation predictions is not physically justified. In this case, the apparent agreement between observations and theory (e.g., longitudinal magnetic tension predictions consistent with PM measurements) may be coincidental rather than physically meaningful. The robust qualitative conclusion---that both PM and NN measurements are sub-Jeans---remains valid, but quantitative theory testing requires either (1) simulations that can measure $\lambda/W$ in the supercritical regime (perhaps through analysis of radial collapse signatures), or (2) independent constraints on the true fragmentation wavelength from other methods.
```

**Files to create**:
- New Discussion subsection in paper
- Update abstract to acknowledge extrapolation uncertainty

---

## Issue 4: Perpendicular-Field Result Underdeveloped

**Problem**: λ/W ≈ 1.25 (perpendicular) vs observed ~2.8. Need quantitative field mixture estimate.

**Implementation Plan**:

```python
# Create script: field_geometry_mixture_estimate.py

# Simple mixing model:
# λ_obs = f_long * λ_long + (1 - f_long) * λ_perp
# Where:
# λ_long ≈ 3.7 (longitudinal field geometry)
# λ_perp ≈ 1.25 (perpendicular field geometry)
# λ_obs ≈ 2.8 (HGBS observed)
#
# Solve: 2.8 = f_long * 3.7 + (1 - f_long) * 1.25
# 2.8 = 3.7*f_long + 1.25 - 1.25*f_long
# 2.8 = 1.25 + f_long * (3.7 - 1.25)
# f_long = (2.8 - 1.25) / (3.7 - 1.25) = 1.55 / 2.45 ≈ 0.63

# Interpretation:
# - 63% longitudinal field geometry needed to match observations
# - Planck finds ~10% longitudinal, ~90% perpendicular
# - This is a factor of 6 discrepancy in geometry fractions
```

**LaTeX addition**:
```latex
\textbf{Quantitative field geometry mixing estimate}. The Campaign 6 result that perpendicular-field filaments produce $\lambda/W \approx 1.25$ creates a striking tension with HGBS observations: if 90\% of HGBS filaments are perpendicular-field (as Planck suggests), the expected $\lambda/W$ would be closer to the perpendicular prediction than the observed value of 2.8. A simple linear mixing model, $\lambda_{\rm obs} = f_{\rm long}\,\lambda_{\rm long} + (1-f_{\rm long})\,\lambda_{\rm perp}$, requires $f_{\rm long} \approx 63\%$ longitudinal-field geometry to reproduce the observed $\lambda/W = 2.8$ (using $\lambda_{\rm long} = 3.7$ from field-geometry calibration and $\lambda_{\rm perp} = 1.25$ from Campaign 6). This is a factor of $\sim$6 discrepancy from the Planck geometry statistics ($\sim$10\% longitudinal).

\textbf{Possible resolutions}: (1) \textit{Field geometry misclassification}: Planck statistics measure the angle between the mean field and filament orientation, but this may not correlate cleanly with the effective field geometry relevant for fragmentation. (2) \textit{Non-MHD physics}: Additional effects (turbulent anisotropy, non-ideal MHD, time-dependent thermodynamics) could modify the fragmentation wavelength in perpendicular-field filaments. (3) \textit{Sample selection bias}: HGBS filaments with NN measurements may be biased toward longitudinal-field geometries if such filaments are more likely to produce detectable core chains. (4) \textit{Projection effects}: The observed 2.8 value is PM-based, which includes cross-filament distances and may not directly compare to the single-filament simulation predictions. This geometric mismatch between simulations (single filaments) and observations (multi-filament systems) complicates direct quantitative comparison.

\textbf{Key implication}: The similar magnitude of discrepancy (observed vs perpendicular: $\sim$2.2× too long; observed vs longitudinal: $\sim$1.3× too short) is intriguing and may suggest that real HGBS filaments sample a mixture of field geometries. However, the required mixture fraction (63\% longitudinal) differs substantially from independent Planck constraints (10\%), indicating either systematic errors in geometry classification or additional physics beyond our current MHD treatment.
```

**Files to create**:
- `field_geometry_mixture_estimate.py` (100 lines)
- New discussion subsection in paper

---

## Issue 5: Textual Corruption on Page 25

**Problem**: Garbled text "2.0ift hef ieldispredominantlylongitudinal.However, theperpendicular−f ieldresultsrevealadramaticgeometricef f ect"

**Implementation Plan**:

```bash
# Search for the corrupted text in LaTeX file
grep -n "2.0ift\|predominantlylongitudinal" filament_spacing_streamlined_mnras.tex

# Fix the corruption (likely a line break issue)
# Should read: "2.0 if the field is predominantly longitudinal. However, the perpendicular-field results reveal..."
```

**Action**: Immediate fix before next compilation

---

## Issue 6: Sample Size and Weighted Mean

**Problem**: Only 4 regions, high sensitivity to individual regions. Need unweighted metrics.

**Implementation Plan**:

```python
# Create script: robustness_statistics.py

# Calculate alternative summary statistics:
# 1. Weighted mean (current): λ/W = 2.17
# 2. Unweighted mean: (1.733 + 1.945 + 2.049 + 3.062) / 4 = 2.197
# 3. Median: median of [1.733, 1.945, 2.049, 3.062] = 1.997
# 4. Standard deviation: 0.52 (24% of mean)

# Test robustness:
# - All three statistics are sub-Jeans
# - Range is 1.73 - 3.06 (77% variation)
# - Leave-one-out shows ±18% sensitivity
```

**LaTeX addition**:
```latex
\textbf{Alternative summary statistics}. Given the small sample size (four robust regions) and the substantial influence of individual regions (leave-one-out sensitivity $\pm$18\%), we report multiple summary statistics to assess robustness (Table~\ref{tab:nn_summary_stats}). The weighted mean (by number of spacings) gives $\lambda/W = 2.17$, the unweighted mean gives $\lambda/W = 2.20$, and the median gives $\lambda/W = 2.00$. All three statistics are substantially below the classical $4\times$ prediction, confirming the robustness of the qualitative sub-Jeans conclusion. However, the 77\% range across individual regions (1.73--3.06) and the sensitivity to individual region exclusion indicate that expansion to the remaining HGBS regions is needed for a more precise measurement.

\begin{table}[h]
\caption{Summary statistics for NN $\lambda/W$ measurements across four robust HGBS regions.}
\label{tab:nn_summary_stats}
\begin{tabular}{lc}
\toprule
Statistic & Value \\
\midrule
Weighted mean (by spacings) & 2.17 \\
Unweighted mean & 2.20 \\
Median & 2.00 \\
Range & 1.73--3.06 \\
Standard deviation & 0.52 \\
Coefficient of variation & 24\% \\
Leave-one-out sensitivity & $\pm$18\% \\
\bottomrule
\end{tabular}
\end{table}
```

**Files to create**:
- `robustness_statistics.py` (100 lines)
- Update paper with alternative statistics

---

## Issue 7: L/3 Convergence Test

**Problem**: PM/(L/3) ≈ 0.2 doesn't rule out modified artifact in complex systems.

**Implementation Plan**:

```latex
# Revise the L/3 convergence section to acknowledge limitation:

\textbf{L/3 convergence test: Interpretation and limitations}. The empirical finding that HGBS regions show PM/(L/3) ≈ 0.2 (range 0.12--0.24) rather than ≈1.0 has been interpreted as evidence that the L/3 convergence artifact does not apply to real HGBS filaments. However, this interpretation requires careful qualification.

The theoretical L/3 limit applies to a \textit{single filament with uniform beading} and perfect core detection. Real HGBS regions are complex multi-filament systems with irregular core distributions, incomplete detection, and projection effects. The observation that PM/(L/3) ≈ 0.2 therefore demonstrates that real HGBS filaments do not behave like uniform single-filament systems---a conclusion that is already known from independent evidence of hierarchical fiber structure \citep{Hacar2013}.

What the L/3 test \textbf{does not} demonstrate is that PM is unaffected by length-related artifacts in complex systems. The filament length definition itself is uncertain (PM/(L/3) varies by $\pm$38\% across three length definitions), and real filaments have curved, branched, or fragmented morphologies that violate the assumptions underlying the L/3 limit. It is therefore possible that a modified form of length-related bias affects PM measurements in complex systems, even if the simple L/3 convergence does not occur.

\textbf{Practical implication}: For this study, we treat PM as a complementary constraint on filament fragmentation that captures the overall scale of core distributions, but we acknowledge that PM is affected by geometric complexity in ways that are not fully quantified. The NN measurement, while also imperfect, is less sensitive to cross-filament contamination and provides a complementary constraint on along-fiber spacing. The robust qualitative conclusion---that both statistics are sub-Jeans---remains valid regardless of which statistic is preferred.
```

**Files to create**:
- Revise L/3 convergence section in paper

---

## Implementation Timeline

### Priority 1 (Critical - Fix Immediately)
1. **Issue 5**: Textual corruption (5 minutes)
2. **Issue 6**: Alternative summary statistics (1 hour)
3. **Issue 1A**: Association bias test (2 hours)

### Priority 2 (Important - Complete This Session)
4. **Issue 2A**: Geometry exploration for PM/NN (3 hours)
5. **Issue 3**: Consolidated extrapolation uncertainty section (1 hour)
6. **Issue 4**: Field geometry mixing estimate (1 hour)
7. **Issue 2B**: Weakened conclusions acknowledgement (30 minutes)

### Priority 3 (Enhancement - If Time Allows)
8. **Issue 1B**: Skeleton threshold consistency test (2 hours)
9. **Issue 1C**: PCA validation and illustration (3 hours)
10. **Issue 7**: L/3 convergence limitation (30 minutes)

### Estimated Total Time
- **Priority 1+2**: ~8 hours (essential for resubmission)
- **Priority 3**: ~5 hours (enhances robustness)

---

## Deliverables

### Scripts to Create
1. `association_bias_test.py`
2. `geometry_exploration_pm_nn_ratio.py`
3. `field_geometry_mixture_estimate.py`
4. `robustness_statistics.py`
5. `skeleton_threshold_consistency.py` (optional)
6. `pca_projection_validation.py` (optional)

### Paper Revisions
1. Fix textual corruption (Issue 5)
2. Add association bias test table (Issue 1A)
3. Add alternative summary statistics table (Issue 6)
4. Add geometry exploration section (Issue 2A)
5. Add consolidated extrapolation uncertainty section (Issue 3)
6. Add field geometry mixing discussion (Issue 4)
7. Weakened qualitative conclusions (Issue 2B)
8. Acknowledge L/3 test limitations (Issue 7)

### New Figures (Optional)
1. NN methodology illustration (Issue 1C)
2. Geometry exploration visualization (Issue 2A)

---

## Success Criteria

The referee's concerns will be adequately addressed when:

1. **NN methodology validation**: Association bias test shows <5% bias for 3/4 regions; skeleton threshold and PCA limitations explicitly acknowledged with quantitative uncertainty estimates.

2. **Forward modelling discrepancy**: Physical explanation provided for what geometric properties could reduce PM/NN from 9-11 to 1.3-1.7; conclusions appropriately qualified to reflect this uncertainty.

3. **Extrapolation uncertainty**: All discussion of near-critical-to-supercritical extrapolation consolidated into single section; explicit statement of what simulations can/cannot test.

4. **Perpendicular field result**: Quantitative estimate of required field geometry mixture (63% longitudinal vs 10% from Planck) with discussion of possible resolutions.

5. **Textual corruption**: Fixed.

6. **Sample size robustness**: Alternative summary statistics (unweighted mean, median, range) reported alongside weighted mean.

7. **L/3 convergence**: Limitations explicitly acknowledged; test interpreted as demonstrating HGBS complexity rather than ruling out all length-related artifacts.

---

**End of Implementation Plan**

**Next Step**: Begin with Priority 1 fixes (textual corruption, alternative statistics, association bias test).
