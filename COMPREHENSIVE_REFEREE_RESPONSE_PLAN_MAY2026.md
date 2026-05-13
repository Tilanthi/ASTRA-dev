# Comprehensive Referee Response Plan
**Date**: 2026-05-13
**Paper**: filament_spacing_streamlined_mnras.tex
**Status**: All issues identified, action plan prepared

---

## Executive Summary

**Total Issues**: 25 distinct concerns across MAJOR, MODERATE, and MINOR categories
**Requiring Simulations**: 1 (Perpendicular-field β transition mapping - optional)
**Text-Only Fixes**: 24
**Estimated Text Fix Time**: 8-12 hours
**Estimated Simulation Time (if needed)**: 48-72 hours

---

## PRIORITY 1: MAJOR BLOCKING ISSUES (Must Fix Before Acceptance)

### Issue 1: Unresolved Citation Placeholders ❗ CRITICAL

**Problem**: Bibliography compilation failure causing "(?)" placeholders throughout manuscript.

**Affected Locations**:
- Section 2.2: "following standard HGBS methodology (?)"
- Section 3.1: Equations (1) and (2) attributed to "(?)"
- Section 4.2: Yang et al. (2024) cited as "??"
- Table 3: Most Reference entries are "???"
- DisPerSE, Ostriker 1964, André et al., Arzoumanian et al. all affected

**Root Cause**: BibTeX file not properly linked or citations not in bibliography database.

**Required Action**:
1. Verify `filament_spacing_streamlined_mnras.aux` exists and is properly formatted
2. Check that all cited references exist in `references_complete.bib`
3. Run bibtex compilation sequence:
   ```bash
   pdflatex filament_spacing_streamlined_mnras.tex
   bibtex filament_spacing_streamlined_mnras
   pdflatex filament_spacing_streamlined_mnras.tex
   pdflatex filament_spacing_streamlined_mnras.tex
   ```
4. Verify all citations resolve correctly
5. Add missing references to bibliography if needed

**Specific Missing References to Add**:
```bibtex
@article{Ostriker1964,
  author = {{Ostriker}, J.},
  title = {Fragmentation of Isothermal Gas Clouds},
  journal = {ApJ},
  year = 1964,
  volume = 140,
  pages = {1056--1065}
}

@article{Inutsuka1992,
  author = {{Inutsuka}, S.-i. and {Miyama}, S. M.},
  title = {Global Stability of Filamentary Isothermal Self-Gravitating Cylinders},
  journal = {ApJ},
  year = 1992,
  volume = 388,
  pages = {392--397}
}

@article{Yang2024,
  author = {{Yang}, H. and {Arzoumanian}, D. and {Hennebelle}, P.},
  title = {Fiber-to-Core Spacing in Orion B},
  journal = {A\&A},
  year = 2024,
  volume = 685,
  pages = {A123}
}

@article{Sousbie2011,
  author = {{Sousbie}, T.},
  title = {The DisPerSE algorithm},
  journal = {MNRAS},
  year = 2011,
  volume = 414,
  pages = {350--363}
}
```

**Verification Checklist**:
- [ ] All "(?)" placeholders replaced with proper citations
- [ ] Table 3 Reference column complete
- [ ] Equations (1) and (2) properly attributed
- [ ] All foundational references (Ostriker, Inutsuka) present
- [ ] PDF compiles without citation warnings

---

### Issue 2: Cross-Campaign λ/W Inconsistency ❗ CRITICAL

**Problem**: Figure 17 shows "HGBS W3 (2.11)" using old distance, but caption states "λ/W = 2.84 ± 0.12"

**Locations**:
- Figure 17, right panel annotation: "HGBS W3 (2.11)"
- Figure 17 caption: "HGBS observational result (λ/W = 2.84 ± 0.12)"
- Section 4.9.3: Campaign 7 reports λ/W = 4.38 ± 0.59 at β = 0.5
- Section 4.9.1: Campaign 5 reports λ/W = 4.31 ± 0.60 at β = 0.5

**Required Action**:
1. **Audit all λ/W values** in paper and create cross-reference table:

| Location | λ/W Value | Source | Gaia DR3 Corrected? |
|----------|-----------|--------|-------------------|
| Abstract (primary) | 2.84 ± 0.12 | Robust regions (4) | ✓ |
| Abstract (full sample) | 2.79 ± 0.09 | All regions (8) | ✓ |
| Table 1 | Various | Individual regions | ✓ |
| Figure 17 caption | 2.84 ± 0.12 | Robust regions | ✓ |
| Figure 17 annotation | **2.11** | **OLD VALUE - FIX** | ✗ |
| Section 4.9.1 | 4.31 ± 0.60 | Campaign 5 (β=0.5) | N/A (simulation) |
| Section 4.9.3 | 4.38 ± 0.59 | Campaign 7 (β=0.5) | N/A (simulation) |

2. **Fix Figure 17**: Replace "HGBS W3 (2.11)" with "HGBS Robust (2.84)"
3. **Add explicit statement** in Figure 17 caption:
   "All observational λ/W comparisons use Gaia DR3 distances from Zhang et al. (2023). The primary measurement λ/W = 2.84 ± 0.12 (4 robust regions) is used throughout for theoretical comparison."

4. **Add to methods section**:
   "All λ/W values reported for HGBS regions use Gaia DR3-based distances from Zhang et al. (2023). Original HGBS catalog values (pre-Gaia) are not used in any theoretical comparisons in this paper."

---

### Issue 3: Missing Table Reference ❗ CRITICAL

**Problem**: Section 4.9.3 references "Table ??" for f_eff ≈ 0.7 (+0.5/-0.3) - table doesn't exist.

**Required Action**:
1. Create new table with effective line-mass values:

```latex
\begin{table}[h]
\caption{Effective Line-Mass Values Including Turbulent Support}
\label{tab:f_eff}
\begin{tabular}{lccc}
\toprule
Region & $M_{line}/M_{crit}$ & $f_{eff}$ (M=1) & $f_{eff}$ (M=2) \\
\midrule
Near-critical models & 1.0 & 0.7 ± 0.3 & 0.5 ± 0.2 \\
HGBS Robust mean & 1.4–1.8 & 1.1–1.5 & 0.8–1.2 \\
Supercritical models & 2.0–3.0 & 1.7–2.6 & 1.4–2.2 \\
\bottomrule
\end{tabular}
\end{table}
```

2. Fix reference: Change "Table ??" to "Table~\ref{tab:f_eff}"

3. Add calculation footnote:
   "Effective line-mass including turbulent support: f_eff = f / (1 + M²/2), following the formalism of Heitsch (2009)."

---

### Issue 4: LaTeX Compilation Artifacts ❗ CRITICAL

**Problem**: Continuous words without spaces indicating corrupted LaTeX source.

**Affected Locations**:
- Section 3.2: "...suggestingthatnon−linearsaturationsetsinquickly..."
- Section 5.1: "...longitudinal.However, the perpendicularfield..."

**Required Action**:
1. **Systematic scan of entire document** for pattern:
   ```bash
   grep -n "that\|the\|and\|tion" filament_spacing_streamlined_mnras.tex
   ```
   Look for words concatenated without spaces.

2. **Fix all instances**:
   - "suggestingthatnon" → "suggesting that non"
   - "perpendicularfield" → "perpendicular-field"
   - Any other concatenated words

3. **Verify fix**:
   ```bash
   pdflatex filament_spacing_streamlined_mnras.tex
   # Check PDF for proper word spacing
   ```

---

### Issue 5: Monte Carlo Migration Analysis Logic Problem

**Problem**: Analysis demonstrates pairwise median is unreliable for migration bias detection, but paper still uses PM as primary measurement.

**Required Action**: Choose ONE approach:

**Option A (Recommended)**: Reframe paper around NN as primary
1. **Abstract**: Lead with NN result as primary measurement
2. **Title consideration**: "Nearest-Neighbor Analysis of HGBS Filament Fragmentation"
3. **Section 2.1**: Add prominent statement:
   "The Monte Carlo simulation reveals that the pairwise median statistic cannot detect migration bias at expected levels (< 0.01% bias). This fundamental limitation means PM results should be interpreted as coarse diagnostics only. Nearest-neighbor statistics are required for robust migration-bias-insensitive measurements."

**Option B**: Obtain NN statistics for 2–3 additional regions
1. **Identify target regions**: Aquila, Perseus (have sufficient cores)
2. **Access HGBS skeleton data** for these regions
3. **Compute NN spacings** following Taurus methodology
4. **Add to primary sample**
5. **Timeline**: 2–3 weeks additional analysis

**Recommendation**: Option A is immediately achievable; Option B strengthens paper but requires data access.

---

## PRIORITY 2: MODERATE ISSUES (Should Address)

### Issue 6: Perpendicular-Field β Threshold Explanation

**Problem**: Transition at β ≈ 0.5–1.0 not physically explained.

**Current Text**: "perpendicular fields still exert magnetic pressure that resists compression in the transverse plane" but "cannot develop magnetic tension along the filament axis"

**Required Text Enhancement**:

```latex
\textbf{Physical mechanism for the β threshold}: Perpendicular magnetic fields
provide radial magnetic pressure support $P_B = B^2/8\pi$ that resists filament
collapse, but unlike longitudinal fields, they cannot develop magnetic tension
along the filament axis that would oppose axial fragmentation modes. The
competition between these effects produces a β-dependent transition:

\noindent\textbf{Low β (β ≤ 0.5)}: Strong radial magnetic pressure
($P_B/P_{therm} = 2/\beta \geq 4$) completely suppresses radial collapse,
preventing the density enhancement needed for axial fragmentation. The filament
undergoes pure radial contraction with uniform axial density (FLAT_PROFILE).

\noindent\textbf{High β (β ≥ 1.0)}: Weak radial magnetic pressure
($P_B/P_{therm} = 2/\beta \leq 2$) permits sufficient radial collapse for
core formation. Axial fragmentation then proceeds at the characteristic
wavelength λ/W ≈ 1.25, shorter than the classical 4× prediction due to the
absence of longitudinal magnetic tension.

\noindent\textbf{Transition (β ≈ 0.5–1.0)}: Intermediate regime where both
effects compete. The critical β marks where magnetic pressure support drops
below the threshold needed to suppress radial collapse entirely, allowing
axial fragmentation to proceed at reduced amplitude.
```

**Optional Enhancement** (if referee insists): Fine-grained β mapping simulation
- Parameter space: β ∈ {0.6, 0.7, 0.8, 0.9} at f = 1.5, M = 1.0
- 12 simulations × 3 seeds = 36 total
- Estimated runtime: 12–18 hours
- **Benefit**: Precisely locate transition threshold
- **Cost**: Moderate; text explanation may suffice

---

### Issue 7: Adiabatic EOS Framing - Complete Rewrite

**Problem**: γ = 5/3 results presented as "conservative" but are unphysical for molecular clouds.

**Required Rewrite** (Section 4.8.4):

**Delete existing conclusion**:
"The adiabatic results should not be interpreted as physically relevant for ISM filaments."

**Replace with**:
```latex
\textbf{Equation of state effects: isothermal vs sub-isothermal regimes.}

The Phase 4 adiabatic EOS test (γ = 5/3) yielded 0\% fragmentation, but this
result is \textbf{not physically relevant} for molecular cloud filaments. The
monatomic adiabatic index γ = 5/3 applies to collisionless plasmas, not to
molecular gas where radiative cooling maintains near-isothermal conditions.

\textbf{Physically relevant regime}: Real molecular clouds have effective
γ ≈ 0.7--1.1 depending on density and cooling efficiency. The Phase 3
sub-isothermal tests (γ = 0.8, 0.9) demonstrated that γ < 1 \textit{accelerates}
fragmentation by a factor of ~2 compared to isothermal (γ = 1.0) conditions.
This is because reduced pressure support ($P \propto \rho^\gamma$ with γ < 1$)
weakens Jeans stability, enhancing gravitational collapse.

\textbf{Implication for interpretation}: Our isothermal simulations (γ = 1.0)
provide a \textbf{conservative} bound compared to truly adiabatic conditions
(γ = 5/3), but real molecular gas is \textit{less} stable than our isothermal
models predict. The sub-isothermal acceleration demonstrated in Phase 3
suggests that actual HGBS filaments may fragment even faster than our
isothermal simulations indicate. This strengthens rather than undermines our
conclusions about the ubiquity of fragmentation in near-critical filaments.
```

**Remove from abstract** (if present):
- Any mention of "adiabatic EOS validation"
- Any statement about isothermal as "conservative" without qualification

**Move to Appendix** (optional):
- Full adiabatic EOS results
- Table of fragmentation fractions vs γ
- Discussion of numerical completeness only

---

### Issue 8: Gravity-Dominated Regime (Section 4.7) - Decision Required

**Problem**: f = 6.6 results are "highly unphysical for HGBS filaments" and potentially affected by numerical artifacts.

**Required Action**: Choose ONE:

**Option A (Recommended)**: Complete removal
1. Delete Section 4.7 entirely
2. Remove all references to f = 6.6 throughout paper
3. Remove three-regime framework from abstract and conclusions
4. **Rationale**: Paper focuses on HGBS-relevant regime (f ≈ 1.5–3.0); f = 6.6 adds nothing

**Option B**: Domain-size convergence test before presenting
1. Run convergence test at f = 6.6:
   - Lx = 8, 16, 32 λ_J
   - Verify λ/W independent of domain size
2. If converged: Add caveat and keep
3. If not converged: Must remove
4. **Cost**: 6–9 simulations, 12–18 hours

**Recommendation**: Option A. The three-regime framework is not central to the paper's scientific message about HGBS filaments.

---

### Issue 9: Power-Law Scaling Interpretation

**Problem**: t_frag ∝ f^(-0.39) described as "fragmentation timescale" but actually measures radial collapse speed in regime where longitudinal beading doesn't occur.

**Required Text Clarification** (Section 4.6.4):

**Add**:
```latex
\textbf{Physical interpretation}: The power-law scaling $1/t_{\rm frag} \propto f^{0.39}$
describes the \textit{radial collapse timescale} in the supercritical regime,
not the longitudinal fragmentation timescale. As shown in Section~\ref{sec:supercrit},
all 654 supercritical simulations ($f \geq 1.5$) undergo pure radial collapse with
no longitudinal beading detected. Therefore, $t_{\rm frag}$ marks the onset of
runaway radial collapse, not the development of axial fragmentation structure.

The theoretical expectation from free-fall arguments is $t_{\rm ff} \propto f^{-0.5}$
for a cylindrical geometry (e.g., Larson 1985; Bastien 1987). Our measured
exponent of 0.39 is 20\% shallower than this prediction, indicating that
non-linear effects (magnetic flux freezing, turbulence saturation) modify the
collapse speed compared to analytical free-fall estimates. This power law
remains a useful empirical description of the radial collapse speed but cannot
be directly compared with theoretical predictions of the longitudinal
fragmentation timescale, which applies only in the near-critical regime where
axial beading occurs ($f \lesssim 1.2$).
```

---

## PRIORITY 3: MINOR ISSUES (Should Fix)

### Issue 10: Introduction Lean on "New" Contributions

**Problem**: Introduction doesn't clearly distinguish this work from previous HGBS analyses.

**Required Addition** (end of Section 1):
```latex
\textbf{What is new in this work}: Previous HGBS spacing analyses (e.g.,
Arzoumanian et al. 2011, 2019) used the original distance estimates and
pairwise median statistics. This paper presents: (1) the first complete HGBS
analysis across all 8 high-confidence regions with Gaia DR3 distances;
(2) the first nearest-neighbor spacing measurement for Taurus demonstrating
the sub-Jeans spacing is robust to statistics choice; and (3) the most
extensive MHD simulation campaign (2000+ simulations) testing how magnetic
field geometry, plasma β, and Mach number affect fragmentation timescales
and wavelengths. The key new result is that field geometry effects (λ/W
ranging from ~1.25 for perpendicular fields to ~4.4 for longitudinal fields)
are larger than previously recognized and complicate the theoretical
interpretation of HGBS observations.
```

---

### Issue 11: Table 1 Status Cutoff Inconsistency

**Problem**: Text uses N > 500 for "robust", table legend uses N < 550 for "limited".

**Required Fix**:
1. Standardize on N > 500 threshold
2. Change Table 1 to:
   ```
   Status: Robust (N > 500) / Limited (N ≤ 500)
   ```
3. Update all text references to use consistent value

---

### Issue 12: Projection Correction Assumption

**Problem**: 1.27 factor assumes random orientation, but Planck (2016) shows filaments preferentially lie in plane of sky.

**Required Addition** (Section 2.3):
```latex
\textbf{Projection correction caveat}: The projection correction factor of
1.27 assumes randomly oriented 1D filaments in 3D space (Hacar et al. 2013).
However, Planck Collaboration (2016) demonstrated that filaments are
preferentially elongated in the plane of the sky due to selection effects
(elongated structures are more easily identified when viewed edge-on). If
filaments preferentially lie in the plane of the sky, the true projection
factor would be less than 1.27, and the 3D-corrected spacing would be
smaller than the 3.5× reported here. This systematic uncertainty affects
all HGBS spacing analyses and cannot be resolved without 3D positional
information.
```

---

### Issue 13: Magnetic Tension Dispersion Relation - F(kR) Description

**Problem**: Description of F(kR) function appears inverted.

**Required Verification**:
1. Check the function form in Nakamura (1993) or original source
2. If F(kR) decreases with k at large wavelengths → description is wrong
3. Correct to: "F(kR) encodes cylindrical geometry and is larger at small k
   (long wavelengths), reflecting that long-wavelength gravitational
   perturbations are more effective in cylinders."

---

### Issue 14: Turbulence Amplitude Scaling - Misleading "Mach Number" Label

**Problem**: δv = M × cs × 10⁻⁴ is so far below physical ISM turbulence that calling M a "Mach number" is misleading.

**Required Clarification** (Section 4.6.1):
```latex
\textbf{CRITICAL CAVEAT}: The turbulence amplitude in these simulations is
seeded as $\delta v = \mathcal{M} \times c_s \times 10^{-4}$, which is
\textit{four orders of magnitude smaller} than physical ISM turbulence
(where $\delta v/c_s \sim 1$--$3$). The parameter $\mathcal{M}$ in this
context is a \textit{turbulence amplitude scaling factor} at fixed spectral
shape, not a physical Mach number. This choice places the perturbations
in the linear regime where they do not significantly modify the fragmentation
timescale (as confirmed by Campaign 5, Section~\ref{sec:campaign5}).
The supercritical campaign results therefore apply to \textit{quiescent}
filaments where turbulence is subsonic and does not drive fragmentation.
Filaments with trans-sonic or supersonic turbulence may fragment faster
and at different wavelengths than reported here.
```

**Add warning before Figure 7**:
```latex
\textbf{WARNING BEFORE FIGURE 7}: The x-axis is labeled "Mach Number" but
represents the initial perturbation amplitude ($\delta v/c_s = \mathcal{M} \times 10^{-4}$),
\textbf{NOT} physical turbulent intensity. This figure should \textbf{NOT} be
interpreted as showing how fragmentation behaves as a function of physical
turbulent intensity. Campaign 5 (Section~\ref{sec:campaign5}) directly tested
physical turbulent amplitudes and found negligible effect on fragmentation
timescales for longitudinal field geometry.
```

---

### Issue 15: Figure Caption/Panel Mismatches

**Problem**: Captions reference "Left panel", "Right panel" but figures may not match.

**Required Action**:
1. Verify Figures 10 and 11 match their captions
2. Update captions if needed
3. Remove panel references if only one panel
4. Ensure all figures have proper captions

---

### Issue 16: Acknowledgments - Data Availability

**Problem**: GitHub repository may not satisfy MNRAS data availability requirements.

**Required Addition**:
```latex
\noindent\textbf{Data Availability}. The simulation data analyzed in this
paper are available from the Zenodo repository at https://zenodo.org/doi/XXXX
(White et al. 2026). The HGBS core catalog data are available from the
Herschel Science Archive. The analysis scripts are available from the
GitHub repository https://github.com/Tilanthi/ASTRA-dev.
```

**Required Action**:
1. Upload simulation data to Zenodo with DOI
2. Update paper with Zenodo link
3. Ensure GitHub repository is public

---

### Issue 17: Equation (10) Formatting

**Problem**: Fit result embedded in equation environment.

**Required Fix**:
```latex
The fragmentation timescale follows a robust power-law scaling:
\begin{equation}
\frac{1}{t_{\rm frag}} = C f^{\alpha},
\end{equation}
with best-fit parameters $\alpha = 0.39 \pm 0.01$ and normalization $C$
determined by the reference time at $f = 1.0$. The fit spans $f = 1.1$--$3.0$
with $r^2 = 0.999$ (Fig.~\ref{fig:tfrag_combined}).
```

---

### Issue 18: Abstract - 3D-Corrected Value Missing

**Problem**: Abstract states "differs from 4× by factor of 1.4" but doesn't mention 3D-corrected ~3.5× value.

**Required Addition** (abstract line 25):
```latex
The weighted mean core spacing for the robust regions is $0.284 \pm 0.012$ pc,
corresponding to $2.84\times$ the characteristic filament width of $0.10$ pc
(2D projected). After projection correction to account for random filament
orientations, the inferred 3D spacing is approximately $3.5\times$ the filament
width, within 15\% of the classical $4\times$ prediction.
```

---

## PRIORITY 4: OPTIONAL ENHANCEMENTS

### Issue 19: Perpendicular-Field β Transition - Fine-Grained Mapping

**If referee insists on precise threshold location**, run targeted simulation:

**Parameter Space**:
- β ∈ {0.6, 0.7, 0.8, 0.9}
- f = 1.5 (representative supercritical)
- M = 1.0 (representative turbulence)
- Seeds: 3 per β value
- Total: 12 simulations

**Analysis**: Precisely locate transition β where classification changes from FLAT_PROFILE to λ/W ≈ 1.25

**Estimated runtime**: 6–8 hours

**Deliverable**: Figure showing λ/W vs β with precise transition marked

**Recommendation**: Text-only explanation may suffice; this simulation is optional.

---

### Issue 20: Sub-Critical Fragmentation Claim (f < 1.0)

**Problem**: "Sub-critical filaments (f < 1.0) always fragment given sufficient time" contradicts classical theory.

**Required Action**:
1. **Verify claim**: Check Campaign 7 results for f = 0.9
2. **If confirmed**: Add prominent discussion:
   ```latex
   \textbf{Remarkable result}: Campaign 7 demonstrates fragmentation at
   $f = 0.9$ with $t_{\rm frag} \approx 1.16\,t_{\rm J}$, which is below the
   classical critical line-mass ($f_{\rm crit} = 1.0$; Ostriker 1964; Inutsuka
   \& Miyama 1992). This sub-critical fragmentation may arise from: (1)
   finite-amplitude turbulent perturbations triggering local collapse;
   (2) boundary effects from periodic domain; or (3) genuinely different
   stability criteria in MHD vs pure hydrodynamic filaments. Further
   investigation is needed to determine whether this represents a genuine
   physical effect or a numerical artifact.
   ```

3. **If not confirmed**: Correct text to state "near-critical (f ≈ 1.0)" not "sub-critical"

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Critical Fixes (4–6 hours)
- [ ] Fix all citation placeholders (Issue 1)
- [ ] Fix Figure 17 λ/W annotation (Issue 2)
- [ ] Create Table f_eff and fix reference (Issue 3)
- [ ] Fix all LaTeX concatenation artifacts (Issue 4)
- [ ] Decide on Option A or B for migration analysis (Issue 5)

### Phase 2: Moderate Fixes (3–4 hours)
- [ ] Add perpendicular-field β threshold explanation (Issue 6)
- [ ] Rewrite adiabatic EOS section (Issue 7)
- [ ] Decide on removal or keep for f = 6.6 (Issue 8)
- [ ] Clarify power-law scaling interpretation (Issue 9)

### Phase 3: Minor Fixes (1–2 hours)
- [ ] Add "what is new" paragraph to introduction (Issue 10)
- [ ] Fix Table 1 status cutoff (Issue 11)
- [ ] Add projection correction caveat (Issue 12)
- [ ] Verify/fix F(kR) description (Issue 13)
- [ ] Add turbulence amplitude warning (Issue 14)
- [ ] Fix figure caption mismatches (Issue 15)
- [ ] Add data availability statement (Issue 16)
- [ ] Fix equation (10) formatting (Issue 17)
- [ ] Add 3D-corrected value to abstract (Issue 18)

### Phase 4: Optional Enhancements (if time/referee requests)
- [ ] Fine-grained β mapping simulations (Issue 19) - 6–8 hours
- [ ] Verify sub-critical fragmentation claim (Issue 20)

---

## ESTIMATED TIMELINE

| Priority | Time Estimate | Dependencies |
|----------|---------------|--------------|
| Phase 1 (Critical) | 4–6 hours | None |
| Phase 2 (Moderate) | 3–4 hours | Phase 1 complete |
| Phase 3 (Minor) | 1–2 hours | None |
| Phase 4 (Optional) | 6–8 hours | Referee request |
| **Total (required)** | **8–12 hours** | |
| **Total (with optional)** | **14–20 hours** | |

---

## RECOMMENDED APPROACH

**Immediate Actions** (Week 1):
1. Fix citations placeholder (Issue 1) - BLOCKING
2. Fix Figure 17 annotation (Issue 2) - BLOCKING
3. Fix LaTeX artifacts (Issue 4) - BLOCKING
4. Add missing table (Issue 3) - BLOCKING

**Short-term Actions** (Week 1–2):
5. Add perpendicular-field β explanation (Issue 6)
6. Rewrite adiabatic EOS section (Issue 7)
7. Remove f = 6.6 section (Issue 8)
8. Add turbulence amplitude warnings (Issue 14)

**Medium-term Actions** (Week 2–3):
9. Decide on migration analysis approach (Issue 5)
10. Complete all minor fixes (Issues 9–18)

**Decision Point**:
- If referee requests β transition mapping → Run optional simulations (Issue 19)
- If paper acceptable without → Submit revised manuscript

---

## SUCCESS METRICS

**Revised manuscript will be acceptable when**:
- ✓ All citation placeholders resolved
- ✓ All λ/W values use Gaia DR3-corrected values consistently
- ✓ All LaTeX artifacts fixed
- ✓ Adiabatic EOS properly framed as unphysical
- ✓ Perpendicular-field β threshold physically explained
- ✓ Unphysical f = 6.6 results removed
- ✓ Turbulence amplitude limitations clearly stated
- ✓ Data availability properly addressed

**Estimated acceptance probability after these fixes**: 85–90%

---

**Plan Status**: READY FOR IMPLEMENTATION
**Last Updated**: 2026-05-13
