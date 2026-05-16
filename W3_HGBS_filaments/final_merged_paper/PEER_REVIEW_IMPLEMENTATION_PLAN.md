# Peer Review Implementation Plan
## Major Revision - May 2026

### Overview
Comprehensive peer review with 16 issues requiring fixes before resubmission.

---

## Major Issues (M1-M5) - Priority: CRITICAL

### M1: Self-Limitation Overdone [CRITICAL]

**Problem**: Repetitive disclaimers that neither PM nor NN are calibrated create impression measurements are worthless.

**Required Changes**:

1. **Consolidate disclaimers** into one focused section:
   - Remove from abstract (keep only brief statement)
   - Remove from Executive Summary (or move to later)
   - Keep in Section 5 (Interpretive Framework) and Conclusions
   
2. **Differentiate PM vs NN clearly**:
   - PM: Strongly contaminated by cross-fiber distances → not reliable
   - NN: Less sensitive to geometric complexity → contains meaningful local information
   
3. **Add positive framing** for NN:
   - "NN provides meaningful constraint on local along-fiber spacing"
   - "Forward modeling confirms NN is less contaminated by cross-fiber distances than PM"
   - "NN measurements are robust qualitative probes of filament structure"

### M2: Forward Modeling Deserves More Analysis [CRITICAL]

**Problem**: PM/NN discrepancy attributed to "geometric complexity" without systematic investigation.

**Required Analysis**:

1. **Map PM/NN across geometric parameters** using existing 14,400 simulations:
   - Vary: number of sub-filaments (1, 2, 3, 5)
   - Vary: core distribution (uniform, clustered/Poisson, multi-scale)
   - Vary: effective length per cluster
   
2. **Add analytical investigation** to Section 5.2:
   ```latex
   \subsection{Systematic Investigation of the PM/NN Discrepancy}
   
   The factor of 6--8 discrepancy between synthetic PM/NN ($\approx$ 9--11) and observed HGBS PM/NN ($\approx$ 1.29) motivates a systematic investigation of which geometric properties of the synthetic model fail to capture real filament structure.
   
   \textbf{Hypothesis 1: Multi-filament bundling}. Real HGBS filaments are not single isolated filaments but bundles of multiple velocity-coherent fibers. Our forward model includes multi-filament systems, but the PM/NN ratio provides a constraint on the effective number of fibers. For $N_{\rm fil}$ filaments with random spatial distribution, the PM statistic incorporates cross-fiber distances that scale approximately as $L_{\rm bundle} / N_{\rm fil}^{1/2}$, while NN remains sensitive to local along-fiber spacing. This reduces PM/NN from the single-filament value of $\approx$ 8-11 toward the observed $\approx$ 1.3.
   
   \textbf{Hypothesis 2: Irregular beading}. The synthetic model assumes uniform spacing with $\lambda_{\rm true} = 0.20$ pc. Real HGBS filaments show irregular, clustered core distributions. For Poisson-distributed core positions along filaments, the NN distribution becomes exponential with mean $\langle {\rm NN} \rangle \approx \lambda_{\rm true}$ but the PM is dominated by long-distance pairs between sparse clusters, reducing the effective PM/NN ratio.
   
   \textbf{Hypothesis 3: Effective filament length}. HGBS filaments may have shorter effective lengths per core cluster than the $L = 5$ pc assumed in the synthetic model. If real filaments consist of multiple shorter segments (e.g., $L_{\rm eff} \approx 1-2$ pc) connected by junctions, then PM converges to $L_{\rm eff}/3$ rather than $L/3$, reducing PM/NN proportionally.
   ```

### M3: Critical Regime Disconnect [HIGH]

**Problem**: Supercritical regime where HGBS filaments reside has different physics, but not enough discussion.

**Required Additions**:

1. **Add physical mechanisms section**:
   ```latex
   \subsection{Why Do Supercritical Filaments Show Regular Spacing?}
   
   Our simulations show that filaments with $f \gtrsim 1.5$ undergo radial collapse before longitudinal fragmentation develops, preventing direct numerical measurement of $\lambda/W$ in this regime. Yet HGBS filaments (inferred $f \approx 1.5$--$3.0) clearly show regular core spacing with $\lambda/W \approx 2$--$3. How can this be understood?
   
   \textbf{Possible resolution mechanisms}:
   
   \begin{enumerate}
       \item \textbf{Turbulent seeding}: Turbulent density fluctuations with characteristic scale $\sim$0.1--0.3 pc may pre-seed fragmentation before radial collapse can complete. If the fluctuation growth time is shorter than the radial collapse timescale, local overdensities can collapse into cores even as the global filament undergoes radial contraction. Campaign 5 shows turbulence does not modify $\lambda/W$ in the near-critical regime, but this cannot be extrapolated to supercritical conditions.
       
       \item \textbf{Hierarchical concentration}: Radial contraction of supercritical filaments may concentrate pre-existing density fluctuations rather than creating new ones. If the filament forms with initial density modulations (from turbulent cascades or previous fragmentation generations), radial collapse will preferentially amplify these modulations, producing cores at the pre-existing wavelength even if new fragmentation is suppressed.
       
       \item \textbf{Effective line-mass reduction}: Turbulent pressure support reduces the effective line-mass fraction: $f_{\rm eff} = f_{\rm thermal} / (1 + \mathcal{M}^2)$ approximately. For $\mathcal{M} \approx 2$--$3$, this can reduce $f_{\rm eff}$ by factors of 4--$9$, potentially bringing nominally supercritical filaments into the near-critical regime where longitudinal fragmentation operates. This effect is briefly mentioned but not developed in detail.
   \end{enumerate}
   
   \textbf{Implication}: The observation that supercritical HGBS filaments show regular spacing with $\lambda/W \approx 2$--$3$ suggests that at least one of these mechanisms is operating. The calibration $\lambda_{\rm frag} = 1.11\,\lambda_{\rm MJ}$ from near-critical simulations may therefore apply more broadly than assumed, but this requires direct theoretical investigation.
   ```

### M4: Aquila Sensitivity Analysis [HIGH]

**Problem**: Need explicit sensitivity analysis excluding Aquila.

**Required Addition**:

1. **Add to Table 4** (leave-one-out):
   - Row: "Excluding Aquila" with NN λ/W value
   
2. **Calculate** NN weighted mean without Aquila:
   - Without Aquila: Orion B (700), Taurus (471), Perseus (606) = 1777 spacings
   - Need to compute weighted mean

### M5: Table 2 Note Inconsistency [HIGH]

**Problem**: Note says "832 spacings from 2 regions" but should be "1909 spacings from 4 regions".

**Required Fix**:

```latex
\noindent\textbf{Notes:} ... (4) Sample sizes: NN based on 1909 total spacings from 4 regions (Orion B: 700, Aquila: 132, Taurus: 471, Perseus: 606); PM based on 4 regions for robust result.
```

---

## Moderate Issues (Mo1-Mo2)

### Mo1: Move Executive Summary [MEDIUM]

**Problem**: "EXECUTIVE SUMMARY OF LIMITATIONS" before abstract is unusual.

**Solution**: Move Section "Executive Summary of Limitations" from start of paper to end of Discussion (before Conclusions).

### Mo2: Spatial Clustering Distance Scenario [MEDIUM]

**Problem**: Permutation test found clustering but not followed up.

**Required Addition**:

```latex
\textbf{Spatial clustering of distance revisions}: The permutation test finding significant clustering (p = 0.019) in the Orion-Aquila Rift raises the possibility of systematic distance bias. If Serpens, Aquila, and Orion B share a systematic overestimate of +20%, the PM-weighted mean would decrease to $\lambda/W \approx$ [CALCULATE]. This represents a lower bound consistent with spatial clustering uncertainty.
```

---

## Minor Issues (Mi1-Mi6)

### Mi1: Fix LaTeX Formatting Artifacts

Find and fix: "massfraction.Caveat:T hisconclusionappliesonlytothenear−criticalregimewherelongitudinalbeadingoccurs.Inthesupercriticalregim≳1.5"

### Mi2: Fix Table 4 Column Header

"N_spacings" should give spacing counts, not core counts. Verify consistency with Table 5.

### Mi3: Fix Figure 1 Caption Ordering

Make ordering consistent between caption and panel headers.

### Mi4: Add Zenodo DOI

Replace GitHub URL with Zenodo DOI for long-term preservation.

### Mi5: Include NCRI in Simulation Count

Add NCRI (14 simulations) to total count (2000 → 2014).

### Mi6: Clarify Taurus Spacing

Add note that Taurus is a counter-example (spacing slightly decreased despite distance revision).

---

## Implementation Order

### Phase 1: CRITICAL Fixes (M1-M5)
1. M5: Fix Table 2 note (quick fix)
2. M1: Consolidate self-limitation language
3. M4: Add Aquila exclusion to Table 4
4. M2: Add PM/NN analysis subsection
5. M3: Add supercritical mechanisms section

### Phase 2: MODERATE Fixes (Mo1-Mo2)
6. Mo1: Move Executive Summary
7. Mo2: Add spatial clustering scenario

### Phase 3: MINOR Fixes (Mi1-Mi6)
8. Mi1: Fix LaTeX artifacts
9. Mi2: Fix Table 4 header
10. Mi3: Fix Figure 1 caption
11. Mi4: Add Zenodo DOI
12. Mi5: Update simulation count
13. Mi6: Add Taurus note

### Phase 4: Final Polish
14. Compile PDF
15. Verify all cross-references
16. Final proofread

---

## Estimated Time: 3-4 hours

Phase 1: 120 minutes
Phase 2: 45 minutes
Phase 3: 60 minutes
Phase 4: 30 minutes
