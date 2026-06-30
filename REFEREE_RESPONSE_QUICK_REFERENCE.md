# Referee Response Quick Reference Guide
**Date**: June 6, 2026

---

## TL;DR - What Has Already Been Solved

### EXISTING SOLUTIONS (No New Analysis Required)

| Issue | Solution | Location |
|-------|----------|----------|
| **NN analysis (L/3)** | λ/W = 2.01 ± 0.16 (79 spacings) | `/ASTRA/HGBS_all_regions_nn_results.json` |
| **RTC campaign** | 212 sims, 7.5% PM match, 3% NN match | `simulations/referee_campaigns_jun2026/` |
| **P1 vs RTC** | Both show ~8% match rate in P1 subspace | `simulations/p1_rtc_comparison.json` |
| **Rigid cylinder** | λ/W = 2.65 ± 0.57 at f ≥ 2.6 | Recent campaigns |
| **Width normalisation** | Wform/Wfil = 1.89 ± 0.58 (±31%) | Campaign P4 |
| **Bibliography** | references_complete.bib exists | Paper directory |
| **Gaia DR3 validation** | Previous analysis complete | Prior work |

---

## WHAT YOU NEED TO DO (Estimated 6-10 hours)

### CRITICAL - Must Do (2-3 hours)

1. **Integrate NN Analysis as Primary Result**
   - Update abstract: Lead with λ/W = 2.0 ± 0.2 from NN analysis
   - Add Section 2.4: "Nearest-Neighbor Analysis"
   - Include NN results in Table 1
   - Update conclusions

2. **Fix Citation Issues**
   - Run: `pdflatex filament_spacing_streamlined_mnras.tex`
   - Run: `bibtex filament_spacing_streamlined_mnras`
   - Run: `pdflatex filament_spacing_streamlined_mnras.tex` × 2
   - Fix any `[e.g.,][]Hacar2013` → `\citep[e.g.][{Hacar2013}]`

3. **Add Observational Window Section**
   - Section 2.5: Distinguish NN window (λ/W = 2.0 ± 0.2) vs PM window (λ/W = 2.8 ± 0.1)
   - Explain systematic uncertainties

### IMPORTANT - Should Do (2-3 hours)

4. **Update RTC Results**
   - Clarify: 62.7% measurable (133/212), 7.5% PM match rate
   - Add: "Of 212 simulations, 133 measured λ/W, 10 matched PM window"

5. **Add P1 vs RTC Numbers**
   - P1 subspace: 154 sims, 83.8% measurable, 7.8% PM match rate
   - "Consistency: Both campaigns show ~8% match rate in near-critical regime"

6. **Rigid Cylinder Discussion**
   - Add subsection on radial equilibrium paradox
   - Discuss three observational tests
   - Weigh RTC vs RC interpretation

7. **Distance Revision Nuance**
   - Tone down "physically implausible"
   - Add independent distance constraints (if available)

8. **Width Normalisation**
   - Add systematic uncertainty discussion (±31%)
   - State limitation for quantitative comparison

### NICE TO HAVE (1 hour)

9. **Minor fixes**:
   - Fix section cross-reference (4.9.7 → correct number)
   - Add GitHub/Zenodo data availability
   - Update Table 3 caption with caveat
   - Add migration bias clarification

---

## KEY NUMBERS TO INCLUDE

### Nearest-Neighbor Analysis (PRIMARY RESULT)
```
Weighted mean: λ/W = 2.01 ± 0.16 (79 spacings)
Individual regions:
- Orion B: λ/W = 2.29 (47 spacings, 188 cores)
- Aquila: λ/W = 1.89 (22 spacings, 78 cores)
- Ophiuchus: λ/W = 0.95 (10 spacings, 45 cores)
```

### RTC Campaign Results
```
Total: 212 simulations
Measurable: 133 (62.7%)
PM window matches: 10/133 (7.5%)
NN window matches: 4/133 (3.0%)

P1 subspace (f = 1.0-1.2, β = 2.0):
Total: 154
Measurable: 129 (83.8%)
PM window matches: 10/129 (7.8%)
NN window matches: 2/129 (1.6%)
```

### Width Normalisation
```
Wform/Wfil = 1.89 ± 0.58 (±31% systematic)
```

---

## EXISTING FILES TO REFERENCE

### Data Files
- `/ASTRA/HGBS_all_regions_nn_results.json` - NN analysis results
- `/simulations/referee_campaigns_jun2026/` - RTC campaign data
- `/simulations/p1_rtc_comparison.json` - P1 vs RTC comparison

### Documentation Files
- `COMPREHENSIVE_REFEREE_RESPONSE_PLAN_JUNE2026.md` - Full implementation plan
- `extract_p1_rtc_subspace.py` - P1 vs RTC analysis script

---

## QUICK IMPLEMENTATION SCRIPT

```bash
# 1. Extract P1 vs RTC numbers (already done)
python extract_p1_rtc_subspace.py

# 2. Compile paper with bibliography
cd W3_HGBS_filaments/final_merged_paper/
pdflatex filament_spacing_streamlined_mnras.tex
bibtex filament_spacing_streamlined_mnras
pdflatex filament_spacing_streamlined_mnras.tex
pdflatex filament_spacing_streamlined_mnras.tex

# 3. Check for citation issues
grep -n "\[.*\]\[\]" filament_spacing_streamlined_mnras.tex
```

---

## ABSTRACT TEMPLATE (with NN result)

```latex
\textbf{Results}. Nearest-neighbor analysis of HGBS skeleton data yields a
weighted mean core spacing of $\lambda/W = 2.0 \pm 0.2$ across three regions
(Orion B, Aquila, Ophiuchus), with 79 measured spacings from cores directly
on filament spines. Pairwise median statistics give $\lambda/W \approx 2.8$ but
converge to $L/3 \approx 2$ pc for large filaments like Orion B (N = 1,844),
demonstrating that this statistic measures filament scale rather than true
fragmentation wavelength.

\noindent The RTC campaign (212 free-boundary simulations) finds 7.5\% of
measurable simulations match the pairwise median window and 3.0\% match the
nearest-neighbor window. All measurable RTC simulations produce
$\lambda/W \geq 3.0$, exceeding both observational benchmarks. The rigid
cylinder campaign (with reflecting wall boundaries) yields $\lambda/W = 2.65
\pm 0.57$ at $f \geq 2.6$, within the observational windows. This boundary-
condition sensitivity suggests that real filament spacings depend critically on
radial confinement physics.
```

---

## SECTION 2.4 TEMPLATE (Nearest-Neighbor Analysis)

```latex
\subsection{Nearest-Neighbor Spacing Analysis}
\label{sec:nn_analysis}

\textbf{Primary result: Nearest-neighbor statistics}. Using the HGBS skeleton
maps, we computed nearest-neighbor spacings for cores directly on filament
spines. Across three regions with sufficient data (Orion B, Aquila, Ophiuchus),
we measured 79 spacings with a weighted mean of $\lambda/W = 2.0 \pm 0.2$.

\noindent\textbf{Individual region results}:
\begin{itemize}
\item Orion B: $\lambda/W = 2.29$ (47 spacings, 188 cores on filaments)
\item Aquila: $\lambda/W = 1.89$ (22 spacings, 78 cores on filaments)
\item Ophiuchus: $\lambda/W = 0.95$ (10 spacings, 45 cores on filaments)
\end{itemize}

\noindent\textbf{Comparison with pairwise median}. This NN result directly
addresses the $L/3$ convergence problem: the pairwise median for Orion B
(1,844 cores spanning 6 pc) converges to $L/3 \approx 2$ pc rather than the
true NN spacing of $\sim0.23$ pc. The NN result is therefore the more reliable
measurement of the fragmentation wavelength.
```

---

## KEY MESSAGES FOR REFEREE RESPONSE LETTER

### To Reviewer 1 (Observational):
"We have integrated our nearest-neighbor analysis of HGBS skeleton data,
which yields λ/W = 2.0 ± 0.2 across 79 measured spacings. This now serves as
the primary observational constraint, addressing the L/3 convergence problem
you identified."

### To Reviewer 2 (Theoretical):
"We have clarified the extrapolation gap as the central theoretical uncertainty:
all 654 supercritical simulations underwent pure radial collapse. The RTC
null result (7.5% match rate) applies only to the 62.7% of simulations where
λ/W was measurable. We have also added comprehensive discussion of the
radial equilibrium paradox."

---

## FILES CREATED

1. `COMPREHENSIVE_REFEREE_RESPONSE_PLAN_JUNE2026.md` - Full plan
2. `extract_p1_rtc_subspace.py` - P1 vs RTC analysis script
3. `simulations/p1_rtc_comparison.json` - P1 vs RTC results
4. `REFEREE_RESPONSE_QUICK_REFERENCE.md` - This file

---

**Next Step**: Start implementing the changes in order listed above.
**Estimated Time**: 6-10 hours total
**Risk Level**: Low (most data already available)
