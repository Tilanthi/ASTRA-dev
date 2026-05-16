# Additional Critical Issues - Implementation Plan
## Peer Review Feedback - May 2026 (Round 2)

### Overview
Four additional critical issues identified requiring immediate attention before resubmission.

---

## Issue 1: Central Measurement Interpretation Inconsistency [CRITICAL]

**Problem**: Paper acknowledges PM/NN are uncalibrated estimators, then proceeds to test theories against them. Logical tension never resolved.

**Required Changes**:

1. **Abstract** - Make clearer distinction:
   - Current: "tests theoretical models against these measurements"
   - Change to: "We compare theoretical predictions with our measurements as **qualitative consistency checks only**, recognizing that neither statistic has been quantitatively validated against the true fragmentation wavelength"

2. **Discussion Section 5.1** - Add explicit framework at start:
   ```latex
   \subsection{Interpreting Uncalibrated Statistics: A Consistency Framework}
   
   Given that neither PM nor NN has been validated as a calibrated estimator of the true fragmentation wavelength (Section~\ref{sec:forward_model}), we adopt the following interpretive framework for comparing theoretical predictions with observations:
   
   \begin{itemize}
       \item \textbf{Qualitative consistency only}: Agreement within a factor of $\sim$2 between theory and observation suggests the mechanism may be operating in the observed systems, but cannot be interpreted as quantitative confirmation.
       
       \item \textbf{Order-of-magnitude constraints}: Theories predicting $\lambda/W < 1$ (sub-filament spacing) or $\lambda/W > 10$ (multi-filament scales) can be ruled out as inconsistent with observations.
       
       \item \textbf{Relative comparisons}: The fact that NN (along-fiber) and PM (including cross-fiber) give similar sub-Jeans values constrains theories that would predict large differences between these statistics.
       
       \item \textbf{No quantitative validation}: We do \textbf{not} claim that any theoretical model is "confirmed" or "validated" by agreement with PM or NN measurements. All theoretical comparisons are qualitative consistency assessments subject to the calibration uncertainty.
   \end{itemize}
   ```

3. **Throughout Discussion** - Replace language:
   - "is consistent with" → "shows qualitative consistency with"
   - "predicts...within the PM-NN range" → "predicts...within the observed range (qualitative comparison only)"
   - "provides a quantitative constraint" → "provides a qualitative constraint"
   - Add disclaimer: "(recognizing that neither PM nor NN has been quantitatively validated)"

4. **Conclusions** - Reframe theoretical comparisons:
   - Move theoretical discussion to end, after observational results
   - Clearly label as "Qualitative theoretical comparisons" not "Quantitative tests"

---

## Issue 2: PM/NN Forward-Model Discrepancy Analysis [CRITICAL]

**Problem**: Need to analyze what PM/NN ~ 1.29 + PM/(L/3) ~ 0.2 implies for effective L/λ ratio.

**Required Analysis**:

For synthetic model with regular beading:
- PM → L/3 (for uniform beading)
- NN → λ_true
- PM/NN → (L/3) / λ_true = L / (3λ_true)
- For L = 5 pc, λ = 0.20 pc: PM/NN = 5 / (3 × 0.20) = 8.33 ✓

For HGBS data:
- Observed: PM/NN ≈ 1.29
- Observed: PM/(L/3) ≈ 0.2 (not 1.0)
- This implies PM ≈ 0.2 × (L/3), not L/3

**Key insight**: If PM is not converging to L/3 in HGBS data, then the synthetic PM/NN ratio is not the appropriate baseline.

**Derived relationship**:
- PM/NN = [PM/(L/3)] × [(L/3)/λ_true] × [λ_true/NN]
- PM/NN = [PM/(L/3)] × [L/(3λ_true)] × [λ_true/NN]
- For regular beading: PM/(L/3) = 1, λ_true/NN = 1, so PM/NN = L/(3λ_true)

**What PM/NN ≈ 1.29 implies**:
Given PM/(L/3) ≈ 0.2, if we assume NN ≈ λ_true (along-fiber spacing):
- PM/NN ≈ 0.2 × L/(3λ_true) × 1
- 1.29 ≈ 0.2 × L/(3λ_true)
- L/(3λ_true) ≈ 1.29 / 0.2 ≈ 6.45
- L/λ_true ≈ 19.35

This means: **Effective filament length is ~19× the fragmentation wavelength**, or **~4.8× the L/λ ratio of the synthetic model**.

**Physical interpretation**: Real HGBS filaments have:
- Multiple fragments per filament (not just 2-3 as in synthetic model)
- Irregular spacing (not uniform beading)
- Multi-filament networks (not single filaments)

**Add to Discussion**:

```latex
\subsection{What Does the PM/NN Ratio Tell Us About Filament Structure?}

The forward-model PM/NN ratio of 9--11 for regular beading with $L = 5$ pc and $\lambda = 0.20$ pc reflects the geometry of the synthetic model: PM converges to $L/3$ while NN measures $\lambda_{\rm true}$, giving PM/NN $= L/(3\lambda_{\rm true}) \approx 8.3$. 

For HGBS data, we observe PM/NN $\approx$ 1.29, which is a factor of 6--8 smaller. However, this discrepancy does \textbf{not} necessarily imply different fragmentation physics. Instead, it reflects the failure of the $L/3$ convergence assumption in real filaments: HGBS regions show PM/($L/3$) $\approx$ 0.2, not 1.0.

We can derive the effective $L/\lambda$ ratio implied by the HGBS observations:
\begin{equation}
   \frac{\rm PM}{\rm NN} = \frac{{\rm PM}}{L/3} \times \frac{L}{3\lambda_{\rm true}} \times \frac{\lambda_{\rm true}}{{\rm NN}}
\end{equation}
Assuming NN $\approx \lambda_{\rm true}$ (along-fiber spacing) and using the observed PM/($L/3$) $\approx$ 0.2:
\begin{equation}
   1.29 \approx 0.2 \times \frac{L}{3\lambda_{\rm true}} \implies \frac{L}{\lambda_{\rm true}} \approx 19
\end{equation}
This $L/\lambda_{\rm true} \approx 19$ ratio is physically reasonable for HGBS filaments: it represents multi-fragment systems with $\sim$19 core spacings along the filament length, compared to only $\sim$25 spacings in the synthetic model ($L = 5$ pc, $\lambda = 0.20$ pc). The observed PM/NN ratio is therefore consistent with real filaments having more fragments and more complex geometry than the single-filament synthetic model, not with different fragmentation physics.

The key insight is that the PM/NN ratio encodes the $L/\lambda$ geometry of the filament system, not the fragmentation physics itself. The synthetic model is correct for what it models (single filaments with regular beading), but real HGBS filaments have substantially different spatial structure.
```

---

## Issue 3: NN Methodology Gaps [HIGH PRIORITY]

**Problem**: 
1. Taurus and Perseus methodology not reported to same detail as Orion B/Aquila
2. Aquila selection bias not addressed (73% of cores unassociated)

**Required Changes**:

1. **Add Taurus methodology section**:
   ```latex
   \subsubsection{Taurus NN Methodology}
   
   Taurus (536 cores, distance = 135 pc) shows the highest core-filament association efficiency at 90.5\% (485 associated cores), indicating well-defined filament structures with most cores clearly aligned along filament spines. The NN analysis identified 471 spacings from 14 filament groups with a weighted mean $\lambda_{\rm NN}/W = 1.733 \pm 0.270$. Skeleton extraction used a persistence threshold of 20 av$_{\rm max}$ following standard HGBS methodology. Core-filament association used the standard 2W radius (20 pixels at 135 pc distance = 0.04 pc/pixel). The high association efficiency suggests minimal selection bias in the Taurus NN measurement.
   ```

2. **Add Perseus methodology section**:
   ```latex
   \subsubsection{Perseus NN Methodology}
   
   Perseus (816 cores, distance = 296 pc) shows intermediate association efficiency at 69.9\% (570 associated cores). The NN analysis identified 606 spacings from 18 filament groups with a weighted mean $\lambda_{\rm NN}/W = 3.062 \pm 0.247$, the highest of the four regions. Skeleton extraction used a persistence threshold of 20 av$_{\rm max}$. Core-filament association used the standard 2W radius. The moderate association efficiency suggests some cores are genuinely unbound or located in diffuse regions away from main filaments, but the majority are filament-associated.
   ```

3. **Add Aquila selection bias discussion**:
   ```latex
   \textbf{Aquila selection bias assessment}. The low core-filament association efficiency in Aquila (26.7\%, 200 associated out of 749 cores) raises concern about selection bias: if unassociated cores are systematically different from associated cores, the NN spacing derived from 27\% of cores may not be representative. We assess two hypotheses:
   
   \begin{enumerate}
       \item \textbf{Unassociated cores are background} (not filament-bound): If unassociated cores are distributed randomly in the cloud rather than along filaments, then excluding them from NN analysis is appropriate and does not introduce bias. The NN measurement would genuinely reflect filament-bound core spacing.
       
       \item \textbf{Skeleton extraction failed} in complex regions: If unassociated cores are located along filaments but the skeleton extraction missed them (due to low persistence threshold, complex branching, or projection effects), then excluding them could bias NN by under-sampling dense or complex regions.
   \end{enumerate}
   
   We cannot distinguish between these hypotheses without access to individual core positions and properties beyond the published HGBS catalogs. However, we note that: (1) Aquila's large distance (436 pc) increases the angular scale of filament structures, potentially causing skeleton fragmentation; (2) The association efficiency deficit (73\% unassociated vs 10--30\% in other regions) is large enough that even a small bias could significantly affect results. \textbf{Conservative approach}: We treat the Aquila NN measurement as having larger systematic uncertainty than other regions, but we retain it in the weighted mean because excluding it would introduce selection bias. Future work with access to raw HGBS data should perform selection bias analysis comparing associated vs unassociated core properties.
   ```

---

## Issue 4: Abstract Length Reduction [MEDIUM PRIORITY]

**Problem**: Abstract too long for MNRAS guidelines (~250-300 words recommended, current likely 400+).

**Required Changes**:

1. **Measure current abstract length**:
   - Count words in current abstract
   - Target: ~250-300 words maximum

2. **Reduction strategy**:
   - Remove detailed methodology (can go in first paragraph of introduction)
   - Remove repetition of "complementary statistics" concept
   - Consolidate L/3 convergence discussion
   - Shorten theoretical model discussion
   - Move detailed limitations to paper body, keep only key points in abstract

3. **Target structure**:
   - Paragraph 1: Primary result (NN = 2.17, PM = 2.84, both sub-Jeans)
   - Paragraph 2: Critical limitation (PM/NN forward-model discrepancy, neither calibrated)
   - Paragraph 3: L/3 convergence test result
   - Paragraph 4: Theoretical status (perpendicular-field ruled out, others remain viable)
   - Paragraph 5: Key limitations (extrapolation, statistical power)

---

## Implementation Order

### Phase 1: CRITICAL Issues (Must Fix)
1. ✅ Issue 1: Add interpretive framework to Discussion
2. ✅ Issue 1: Update abstract language for qualitative vs quantitative
3. ✅ Issue 2: Add PM/NN ratio analysis subsection
4. ✅ Issue 3: Add Taurus/Perseus methodology sections
5. ✅ Issue 3: Add Aquila selection bias discussion

### Phase 2: HIGH PRIORITY
6. ✅ Issue 4: Reduce abstract length to ~300 words

### Phase 3: Final Polish
7. ✅ Recompile PDF
8. ✅ Verify all cross-references work
9. ✅ Final proofread

---

## Files to Modify

1. **filament_spacing_streamlined_mnras.tex**
   - Abstract (reduce length, clarify qualitative vs quantitative)
   - Section 5.1: Add interpretive framework subsection
   - Section 5.1: Add PM/NN ratio analysis subsection
   - Add Taurus methodology section
   - Add Perseus methodology section
   - Add Aquila selection bias discussion

---

## Estimated Time: 2-3 hours

Phase 1 (Critical): 90 minutes
Phase 2 (High Priority): 45 minutes  
Phase 3 (Final Polish): 30 minutes
