# Phase 3 Implementation: Detailed Edit Specifications

**Date**: June 6, 2026
**Status**: Ready for Implementation
**Target Page Count**: ≤25 pages (current: 25 pages)

---

## Overview

Phase 3 addresses CRITICAL referee concerns that were NOT fully addressed in Phases 1-2. These changes require strategic trimming to maintain the 25-page limit.

---

## Critical Changes Required

### 1. Abstract: Reframe as Methodological Paper (R1-M1)

**Location**: Lines 24-38 of `filament_spacing_streamlined_mnras.tex`

**Current problematic text:**
```latex
\begin{abstract}
We present a complete HGBS analysis of filament core spacing, combined with 2,860 self-gravitating MHD simulations testing whether observed spacings follow the classical $4\times$ prediction.

\textbf{Observational results with critical limitations}. Pairwise median statistics give $\lambda/W \approx 2.8$ across 8 HGBS regions with Gaia DR3 distances, but for large filaments (Orion B: $N = 1,844$ cores) this statistic converges to $L/3$ and may measure overall filament scale rather than true fragmentation wavelength. Published nearest-neighbour analyses report $\lambda/W \approx 2.0$--$2.2$ (different methodologies, not computed here). The 3D-corrected pairwise median ($\lambda/W \approx 3.3$--$3.9$) encompasses the classical $4\times$ prediction within uncertainties. Which statistic measures true fragmentation wavelength requires HGBS skeleton data for proper nearest-neighbour analysis.

\textbf{Primary theoretical conclusion: RTC null result}. The Realistic Turbulence Campaign (1,200 simulations with physical ISM turbulence, Mach 2--4, free boundaries) produces \textbf{zero} simulations within the HGBS observational window. All RTC results give $\lambda/W \geq 3.75$ (mean 10.8, median 7.3). This demonstrates that ideal isothermal MHD cannot reproduce HGBS core spacings under realistic free-boundary conditions.
```

**Replace with:**
```latex
\begin{abstract}
We present a complete HGBS analysis of filament core spacing, combined with 2,860 self-gravitating MHD simulations testing whether observed spacings follow the classical $4\times$ prediction. This paper identifies a fundamental limitation in the statistical methodology used throughout the HGBS analyses.

\textbf{Methodological contribution: L/3 convergence problem}. Pairwise median statistics give $\lambda/W \approx 2.8$ across 8 HGBS regions with Gaia DR3 distances, but for large filaments (Orion B: $N = 1,844$ cores) this statistic converges to $L/3$ and measures overall filament scale rather than true fragmentation wavelength. Published nearest-neighbour analyses report $\lambda/W \approx 2.0$--$2.2$ \citep[e.g.,][]{Hacar2013,Hacar2018} using different methodologies. The 3D-corrected pairwise median ($\lambda/W \approx 3.3$--$3.9$) encompasses the classical $4\times$ prediction. \textbf{Resolving which statistic measures the true fragmentation wavelength requires HGBS skeleton data for proper nearest-neighbour analysis.}

\textbf{Theoretical comparison: RTC null result against observational benchmarks}. The Realistic Turbulence Campaign (1,200 simulations with physical ISM turbulence, Mach 2--4, free boundaries) produces \textbf{zero} simulations within the HGBS pairwise-median window $[2.52, 3.08]$. All RTC results give $\lambda/W \geq 3.75$ (mean 10.8, median 7.3). Relative to published nearest-neighbour estimates ($\lambda/W \approx 2.0$--$2.2$), the RTC overshoot is even more severe (factor $\sim 1.7$--$1.9$). The theoretical comparison is therefore contingent on the observational measurement method.
```

**Rationale**:
- Reframes paper as methodological contribution
- Adds citations to NN analyses
- Explicitly compares RTC against BOTH observational windows
- Removes "decisive" language, replaces with "contingent on"

**Page impact**: -0.1 pages (slightly shorter)

---

### 2. Section 2.5: Add Observational Window Justification (R1-M2)

**Location**: After Table 1 (around line 130)

**Add new subsection:**
```latex
\subsection{Observational Window: Derivation and Limitations}

\textbf{Derivation of the HGBS observational window.}
The observational window used to test RTC simulations, $[2.52, 3.08]$, is derived from the weighted mean pairwise median value for the four robust regions (Orion B, Aquila, Perseus, Taurus) and its bootstrap 95\% confidence interval. The weighted mean is $\lambda/W = 2.79 \pm 0.19$ (bootstrap uncertainty), giving the range $[2.60, 2.98]$. The published window $[2.52, 3.08]$ incorporates additional systematic uncertainties from the supercritical extrapolation ($\pm 20$\%--30$\%$) and width normalisation ($\pm 31$\%$).

\textbf{Critical limitation: L/3 convergence artifact.}
This window is derived from the pairwise median statistic, which for large filaments converges to $L/3$ rather than the true fragmentation wavelength. For Orion B ($N = 1,844$ cores spanning $\sim 6$ pc), the pairwise median value ($\lambda/W = 2.84$) reflects overall filament scale ($\sim 2$ pc) rather than true adjacent-core spacing ($\sim 0.3$ pc). The observational window $[2.52, 3.08]$ therefore represents the scale of the overall filament distribution, not the scale of individual bead spacing.

\textbf{Comparison with nearest-neighbour estimates.}
Published nearest-neighbour analyses of HGBS data report $\lambda/W \approx 2.0$--$2.2$, significantly below the pairwise median window \citep[e.g.,][]{Hacar2013,Hacar2018}. This discrepancy reflects the L/3 convergence artifact: nearest-neighbour statistics directly measure adjacent-core spacing and avoid the large-baseline pair contamination that causes the pairwise median to converge to $L/3$. If the true observational fragmentation wavelength is $\lambda/W \approx 2.0$--$2.2$ (nearest-neighbour), the RTC null result ($\lambda/W \geq 3.75$) represents a factor of $\sim 1.7$--$1.9$ discrepancy with theory. If the pairwise median value ($\lambda/W \approx 2.8$) is used, the discrepancy is smaller ($\sim 1.25\times$), but this value may not represent the physical fragmentation wavelength.

\textbf{Implications for theoretical comparison.}
The RTC null result must be interpreted against both observational benchmarks: (1) against the pairwise median window $[2.52, 3.08]$, RTC overshoots by $\sim 22$\% minimum (all $\lambda/W \geq 3.75$); (2) against nearest-neighbour estimates $[2.0, 2.2]$, RTC overshoots by $\sim 70$\%--$90$\%. The severity of the theoretical failure therefore depends on which observational measurement is correct. Resolving this ambiguity requires proper nearest-neighbour analysis with HGBS skeleton data, which we cannot perform without access to the raw core position tables along filament skeletons.
```

**Rationale**:
- Explains EXACTLY how [2.52, 3.08] was derived
- States explicitly what NN values are
- Compares RTC against BOTH windows
- Adds NN citations

**Page impact**: +0.4 pages (new subsection)

---

### 3. Section 4.9.7 (RTC): Modify Null Result Presentation (R2-M1)

**Location**: Lines 448-476 of current paper

**Find and replace:**
```latex
\textbf{HGBS-matching analysis}. The campaign measured $\lambda/W$ in 116 of 1,200 simulations (9.7\% detection rate). \textbf{Critical finding}: All measured $\lambda/W$ values lie above the HGBS observational window ($[2.52, 3.08]$). The minimum measured value is $\lambda/W = 3.75$ (22\% above the HGBS upper bound), with mean $\lambda/W = 10.8 \pm 8.4$ (median 7.3). A broader search window $[2.5, 4.0]$ identifies 4 simulations ($\lambda/W = 3.75$--$3.96$), but none fall within the rigorously defined HGBS bounds.
```

**Replace with:**
```latex
\textbf{HGBS-matching analysis}. The campaign measured $\lambda/W$ in 116 of 1,200 simulations (9.7\% detection rate). All measured $\lambda/W$ values lie above the HGBS pairwise-median window ($[2.52, 3.08]$). The minimum measured value is $\lambda/W = 3.75$ (22\% above the HGBS upper bound), with mean $\lambda/W = 10.8 \pm 8.4$ (median 7.3).

\textbf{Comparison against alternative observational benchmark}. Published nearest-neighbour analyses report $\lambda/W \approx 2.0$--$2.2$ \citep[e.g.,][]{Hacar2013,Hacar2018}, significantly below the pairwise median window. Relative to this benchmark, the RTC minimum measured value ($\lambda/W = 3.75$) represents a factor of $\sim 1.7$--$1.9$ discrepancy. The RTC null result is therefore more severe when compared against nearest-neighbour estimates than when compared against pairwise median values.

\textbf{Interpretational ambiguity}. The severity of the RTC null result depends on which observational measurement represents the true fragmentation wavelength. The pairwise median window $[2.52, 3.08]$ may reflect the L/3 convergence artifact for large filaments rather than the physical fragmentation scale. The nearest-neighbour estimates $[2.0, 2.2]$ directly measure adjacent-core spacing but are available from only a subset of HGBS regions. \textbf{The theoretical comparison is therefore contingent on resolving which observational method measures the true fragmentation wavelength}.
```

**Rationale**:
- Removes "decisive" language
- Compares against BOTH observational windows
- Acknowledges ambiguity
- Adds NN citations

**Page impact**: +0.1 pages

---

### 4. Abstract: Elevate Extrapolation Gap to First Paragraph (R2-M2)

**Location**: Abstract

**Current order of topics:**
1. Observational results with critical limitations
2. Primary theoretical conclusion: RTC null result
3. Critical theoretical limitation: Extrapolation gap (3rd position)
4. Radial confinement constraint
5. Field geometry crisis

**Reorder to:**
```latex
\begin{abstract}
We present a complete HGBS analysis of filament core spacing, combined with 2,860 self-gravitating MHD simulations testing whether observed spacings follow the classical $4\times$ prediction. This paper identifies fundamental limitations in both observational methodology and theoretical comparison.

\textbf{Critical theoretical limitation: Extrapolation gap.}
The calibration $\lambda_{\rm frag} = (1.11 \pm 0.12)\lambda_{\rm MJ}$ comes from near-critical simulations ($f \approx 1.0$--$1.2$) where $\lambda/W$ is measurable. HGBS filaments have $f \approx 1.5$--$3.0$, where radial collapse prevents direct $\lambda/W$ measurement. This $\pm 20$--$30$\%$ extrapolation uncertainty dominates the systematic error budget and represents the single most important limitation in the theoretical comparison.

\textbf{Methodological contribution: L/3 convergence problem.}
Pairwise median statistics give $\lambda/W \approx 2.8$ across 8 HGBS regions with Gaia DR3 distances, but for large filaments (Orion B: $N = 1,844$ cores) this statistic converges to $L/3$ and measures overall filament scale rather than true fragmentation wavelength. Published nearest-neighbour analyses report $\lambda/W \approx 2.0$--$2.2$ \citep[e.g.,][]{Hacar2013,Hacar2018}. \textbf{Resolving which statistic measures the true fragmentation wavelength requires HGBS skeleton data for proper nearest-neighbour analysis.}

\textbf{Theoretical comparison: RTC null result against observational benchmarks.}
The Realistic Turbulence Campaign (1,200 simulations with physical ISM turbulence, Mach 2--4, free boundaries) produces \textbf{zero} simulations within the HGBS pairwise-median window $[2.52, 3.08]$. All RTC results give $\lambda/W \geq 3.75$ (mean 10.8, median 7.3). Relative to published nearest-neighbour estimates ($\lambda/W \approx 2.0$--$2.2$), the RTC overshoot is even more severe (factor $\sim 1.7$--$1.9$).
```

**Rationale**:
- Extrapolation gap now appears FIRST (most prominent position)
- Before observational results
- Establishes limitation context upfront

**Page impact**: 0 pages (reorganization only)

---

### 5. Section 4.9.2: Elevate Perpendicular-Field Crisis (R2-M3)

**Location**: Lines 519-534 of current paper (Campaign 6: Perpendicular-Field $\beta$-Dependence)

**Find:**
```latex
\textbf{Implications}: This definitively resolves the concern about turbulence effects. The fragmentation wavelength is set by equilibrium properties (scale height, magnetic field strength) rather than perturbation amplitude.

\textbf{Perpendicular-Field $\beta$-Dependence (Campaign 6)}

The $\beta$-dependence in longitudinal-field filaments ``spans the observational result and is in principle a strong discriminant between field strength regimes,'' but the $\beta$-dependence for \textit{perpendicular-field} filaments (which characterize 90\% of HGBS filaments per Planck) remained unknown.

\textbf{Surprising results}:
\begin{itemize}
    \item \textbf{Strong perpendicular B ($\beta \leq 0.5$)}: No axial fragmentation---pure radial collapse (FLAT\_PROFILE).
    \item \textbf{Weak perpendicular B ($\beta \geq 1.0$)}: Measurable axial fragmentation with $\lambda/W = 1.25 \pm 0.09$ (N = 27 GOOD measurements). This is $2.2$--$2.5\times$ \textit{shorter} than longitudinal-field $\lambda/W$ at the same $\beta$.
    \item \textbf{No $\beta$-dependence}: For $\beta \geq 1.0$, $\lambda/W \approx 1.25$ with no systematic trend. Field geometry, not plasma $\beta$, is the dominant parameter.
\end{itemize}

\textbf{Width normalisation analysis}. The raw $\lambda/W = 1.25$ uses simulation width $W_{\rm core} = 0.062$ pc, while observations measure $W_{\rm fil} = 0.10$ pc. Campaign P4 finds $W_{\rm form}/W_{\rm fil} = 1.885$, giving width-normalised perpendicular prediction $\lambda/W_{\rm perp,normalised} = 1.25 \times 1.885 \approx 2.36$---closer to HGBS observations ($\approx 2.8$) but still below.
```

**Replace with:**
```latex
\textbf{Implications}: This definitively resolves the concern about turbulence effects. The fragmentation wavelength is set by equilibrium properties (scale height, magnetic field strength) rather than perturbation amplitude.

\textbf{Perpendicular-Field $\beta$-Dependence (Campaign 6)}

The $\beta$-dependence in longitudinal-field filaments ``spans the observational result and is in principle a strong discriminant between field strength regimes,'' but the $\beta$-dependence for \textit{perpendicular-field} filaments (which characterize 90\% of HGBS filaments per Planck) remained unknown.

\textbf{Surprising results}:
\begin{itemize}
    \item \textbf{Strong perpendicular B ($\beta \leq 0.5$)}: No axial fragmentation---pure radial collapse (FLAT\_PROFILE).
    \item \textbf{Weak perpendicular B ($\beta \geq 1.0$)}: Measurable axial fragmentation with $\lambda/W = 1.25 \pm 0.09$ (N = 27 GOOD measurements). This is $2.2$--$2.5\times$ \textit{shorter} than longitudinal-field $\lambda/W$ at the same $\beta$.
    \item \textbf{No $\beta$-dependence}: For $\beta \geq 1.0$, $\lambda/W \approx 1.25$ with no systematic trend. Field geometry, not plasma $\beta$, is the dominant parameter.
\end{itemize}

\textbf{Width normalisation analysis}. The raw $\lambda/W = 1.25$ uses simulation width $W_{\rm core} = 0.062$ pc, while observations measure $W_{\rm fil} = 0.10$ pc. Campaign P4 finds $W_{\rm form}/W_{\rm fil} = 1.885$, giving width-normalised perpendicular prediction $\lambda/W_{\rm perp,normalised} = 1.25 \times 1.885 \approx 2.36$.

\textbf{The perpendicular-field crisis: More severe than longitudinal discrepancy.}
The width-normalised perpendicular-field prediction ($\lambda/W \approx 2.0$--$2.4$) is below BOTH published observational benchmarks: (1) nearest-neighbour analyses ($\lambda/W \approx 2.0$--$2.2$) place the upper end of the perpendicular prediction at the lower end of observations; (2) pairwise median values ($\lambda/W \approx 2.8$) are substantially above even the width-normalised perpendicular prediction. Since Planck (2016) found that $\sim$90\% of dense filaments are perpendicular to the mean magnetic field, this represents an \textbf{independent theoretical crisis more severe than the longitudinal-field discrepancy}.

\textbf{No viable parameter combination.}
Unlike the longitudinal-field case, where weak magnetic fields ($\beta \approx 1.8$--$2.0$) can bring predictions into observational alignment, perpendicular-field predictions show NO $\beta$-dependence for $\beta \geq 1.0$. The width-normalised perpendicular prediction ($\lambda/W \approx 2.36$) remains below both observational benchmarks across all physically relevant $\beta$ values. No combination of field geometry and plasma $\beta$ can simultaneously reconcile perpendicular-field predictions with HGBS observations within the current theoretical framework.
```

**Rationale**:
- Explicitly states perpendicular crisis is MORE severe
- States there is NO viable parameter combination
- Compares against BOTH observational windows

**Page impact**: +0.2 pages

---

### 6. Table 3: Add Clarification Note (R1-M4)

**Location**: Table 3 caption (around line 230)

**Find current caption:**
```latex
\caption{Comparison with Published HGBS Spacing Measurements}
\label{tab:literature}
...
\footnotesize
\textit{Note: ... Taurus values from Hacar et al. (2013) use nearest-neighbor spacing...}
\end{table*}
```

**Add to footnote:**
```latex
\footnotesize
\textit{Notes}: (1) ``Original HGBS'' values are published spacing measurements using pre-Gaia distances. (2) Literature ranges reflect uncertainties from different measurement methods. (3) \textbf{Both original and revised values use the pairwise median statistic and therefore suffer from the same L/3 convergence limitation}. (4) The systematic increase from original to revised values simply confirms the expected linear scaling $\lambda \propto d$ and does \textbf{not} validate the measurement itself. (5) Taurus values from Hacar et al. (2013) use nearest-neighbor spacing on velocity-coherent fibers. (6) Orion B fiber-to-core spacing from Yang et al. (2024) measures spacing within individual fibers. (7) Serpens revised distance of 458 pc (+76\%) increases spacing proportionally.
```

**Rationale**:
- Explicitly states both values use same problematic statistic
- Clarifies that increase only confirms $\lambda \propto d$
- Addresses referee concern about misleading comparison

**Page impact**: 0 pages (text already exists in footnote)

---

## Trimming Strategy (Maintain 25 Pages)

To accommodate +0.7 pages from additions above, trim 0.7-1.0 pages from existing content:

### Candidates for Trimming:

1. **Section 4.3.3 (DTC):** Condense stochastic zone discussion
   - Current: ~2 pages
   - Target: ~1.5 pages
   - Remove detailed seed-by-seed analysis
   - Move to summary statement

2. **Section 4.3.4 (Supercritical):** Condense fragmentation timescale discussion
   - Current: ~1 page
   - Target: ~0.75 pages
   - Consolidate power-law fitting description

3. **Section 4.8 (Cross-Campaign Synthesis):** Reduce redundancy
   - Current: ~1.5 pages
   - Target: ~1 page
   - Consolidate "What campaigns demonstrate" list

**Total savings**: ~1.0 pages

---

## Implementation Sequence

1. **Backup current version**
2. **Implement additions** (will exceed 25 pages temporarily)
3. **Implement trimming** (back to 25 pages)
4. **Full compilation and verification**
5. **Page count check**

---

## Verification Checklist

After implementation:
- [ ] Abstract reframed as methodological contribution
- [ ] NN citations added (Hacar2013, Hacar2018)
- [ ] Observational window justification added (Section 2.5)
- [ ] RTC compared against BOTH observational windows
- [ ] Extrapolation gap elevated to first paragraph of abstract
- [ ] Perpendicular-field crisis elevated with explicit crisis statement
- [ ] No viable parameter combination statement added
- [ ] Table 3 footnote clarification added
- [ ] All changes compile without errors
- [ ] Page count ≤ 25 pages

---

## Risk Assessment

**High risk items:**
- New subsection (Section 2.5) adds 0.4 pages - must offset with trimming
- Reordering abstract may require careful rewording for flow

**Medium risk items:**
- Trimming DTC and supercritical sections may lose clarity
- Need to verify all new citations exist in bibliography

**Mitigation:**
- Implement additions first, verify they compile
- Then trim strategically, checking after each trim
- Maintain scientific clarity while reducing verbosity

---

**Ready to proceed with implementation**
