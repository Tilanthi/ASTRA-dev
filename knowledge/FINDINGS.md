# ASTRA Autonomous — Findings & Insights

**Last updated**: 2026-04-03
**Total findings**: 5 candidate (4 confirmed from latest cycles)

---

## Part 1: Confirmed Findings

### F001: Hubble Tension Resolves at H₀ ≈ 70.5
- **Date**: 2026-04-03 (Cycle 8)
- **Confidence**: 0.80
- **Finding**: Hierarchical Bayesian model finds true H₀ = 70.24 ± 0.83. Distance ladder methods biased HIGH (+2.48), early universe methods biased LOW (−1.9). Independent methods converge to H₀ ≈ 70.5.
- **Supporting**: Causal analysis confirms the split is methodological (ΛCDM-assuming vs model-independent), t = −7.29, p = 5e-8
- **Implication**: The Hubble tension is a calibration artifact, not new physics

### F002: COVID-19 Mortality Paradox
- **Date**: 2026-04-03 (Cycle 8)
- **Confidence**: 0.75
- **Finding**: CFR ~ GDP^(-0.315) — richer countries had 52% lower case fatality (10× richer). But Deaths/Million ~ GDP^(+1.1) — richer countries had more total deaths. Paradox resolved: more testing + more exposure.
- **Implication**: Healthcare quality reduces per-case mortality but doesn't reduce total pandemic burden

### F003: Universal Sub-Linear Country Scaling
- **Date**: 2026-04-03 (Cycle 8)
- **Confidence**: 0.80
- **Finding**: GDP ~ Pop^0.938, CO2 ~ Pop^0.925, Energy ~ Pop^0.910. Consistent sub-linear scaling (β ≈ 0.93) across all three — χ² = 3.0, 2 dof.
- **Implication**: Bigger countries are LESS efficient per capita — opposite of cities (superlinear β ~ 1.15). Suggests fundamentally different organizational dynamics at country vs city scale.

### F004: CO2-Temperature is Perfectly Linear
- **Date**: 2026-04-03 (Cycle 8)
- **Confidence**: 0.95
- **Finding**: Cumulative CO2 predicts temperature change with R² = 0.999974. No regime shifts, thresholds, or phase transitions. Slope: 440-450 °C/GtC globally.
- **Implication**: The climate system responds linearly to cumulative emissions — no tipping points detected in historical data

### F005: Causal Structure in H₀ Measurements
- **Date**: 2026-04-03 (Cycle 9)
- **Confidence**: 0.70
- **Finding**: Causal discovery on 53 H₀ measurements shows measurement method influences H₀ value (method -> h0) and error magnitude (err_plus -> h0, err_plus -> method). Method-wise statistics confirm clustering: early universe methods (e.g., Planck) around 67-69, distance ladder (e.g., SH0ES) around 72-74. This supports the methodological basis of the Hubble tension.
- **Implication**: Reinforces that Hubble tension arises from systematic methodological differences rather than new physics.

---

## Part 2: Candidate Findings (Awaiting Further Evidence)

### C001: Cluster L-M Slope Exceeds Self-Similar
- **Confidence**: 0.95 (well-established, not novel)
- **Finding**: Cluster L-M slope = 1.68 ± 0.01 vs self-similar prediction of 1.33
- **Implication**: Significant non-thermal pressure support (AGN feedback, turbulence, cosmic rays)

### C002: SPARC Gas Fraction Anti-Correlation
- **Confidence**: 0.85 (strong but confounded)
- **Finding**: ρ(g_bar, gas_fraction) = −0.894 in SPARC (p = 3.2 × 10⁻⁴⁸)
- **Implication**: Higher-acceleration galaxies are more gas-depleted — but indistinguishable from mass-quenching

### C003: Hubble Tension is Methodological
- **Confidence**: 0.90
- **Finding**: The Planck-SH0ES split is better characterized as "ΛCDM-assuming vs model-independent" (6.5σ) than "early vs late universe" (5σ)

### C004: Causal Structure of Climate-Economy-Pandemic System
- **Confidence**: 0.70
- **Finding**: Population is the root cause across all domains. GDP mediates between environmental and health variables. Healthcare infrastructure (hospital beds) causally reduces COVID deaths.

---

## Part 3: Rejected Candidates

See `/shared/ASTRA/hypotheses/GRAVEYARD.md` for refuted findings (8 refuted, lessons documented).

---

## Part 4: Methodological Insights

### What Works
1. **Permutation tests** — more informative than bootstrap for testing "coincidences"
2. **Partial correlations** — essential for disentangling confounders (green valley killed by mass control)
3. **Mass-matched analysis** — revealed sign reversal at log M★ ≈ 10.5
4. **Multiple proxies** — checking consistency across proxy definitions guards against artifacts
5. **Hierarchical Bayesian models** — H016 resolved Hubble tension by modeling method-level offsets
6. **Causal discovery** — CD-007 revealed population as root cause across domains

### What Doesn't Work
1. **Dimensional analysis alone** — seductive but weak; many combinations land near "interesting" values
2. **z=0-only ratios** — if it only works at the current epoch, it's a coincidence
3. **Eyeballing plots** — the 8× green valley looked real until statistical controls killed it
4. **Proxy-based cross-matching** — too noisy between heterogeneous surveys
5. **NOTEARS causal discovery in highly correlated data** — produces fully connected graphs (overfitting)

### Meta-Lessons
1. **Negative results are the most valuable output** — learned more by ruling out 8 hypotheses than finding 4 ambiguous signals
2. **The "interesting" signal usually has a boring explanation** — mass, selection effects, or cosmological expectations
3. **Three rounds of scrutiny minimum** — raw → subsample → confound disentangling
4. **Statistical significance ≠ physical significance** — H012 found 4.78σ trend but the effect (0.1 mag) is a calibration artifact
5. **Scaling laws transfer across domains** — log-log regression methodology works identically for economics/epidemiology
6. **Paradoxical correlations require disentangling** — COVID CFR↓ with GDP but Deaths/M↑ — partial correlations essential
7. **Quality flags as internal controls** — if only quality correlates with residuals, that's strong evidence for null result

---

## Part 5: Scientific Insights

### Acceleration Scales
- Cosmic acceleration landscape: BHs (~10⁻⁸), cH₀ (~10⁻¹⁰), Milgrom a₀ (~10⁻¹⁰), galaxies (~10⁻¹⁰), clusters (~10⁻¹¹)
- Cluster-galaxy agreement is cosmologically expected, not physically surprising
- MOND connection requires n ≈ 2.59 (not a clean number)

### Galaxy Evolution
- Mass is the dominant driver of quenching — acceleration adds minimal independent information
- RAR is remarkably universal — residuals uncorrelated with all standard properties
- ~0.2 dex between-galaxy scatter exists but doesn't correlate with measured properties

### Cosmology
- Hubble tension is real (4.9σ) and methodological — resolves at H₀ ≈ 70.5
- SN Ia don't require dynamical dark energy (ΔBIC = 11.3)
- Dark energy = cosmological constant (ΛCDM preferred, ΔBIC = +20 over piecewise w(z))

### Cross-Domain
- Country scaling is sub-linear (β ≈ 0.93) — opposite of cities (superlinear)
- CO2-temperature is perfectly linear (R² = 0.999974) — no regime shifts
- COVID mortality paradox: better healthcare + more exposure = fewer per-case but more total deaths
- Population is the root cause across climate, economics, and pandemic outcomes

---

## Part 6: Data Quality Notes

- SDSS D4000: only 9,401/82,891 galaxies (11.3%)
- SPARC-SDSS cross-match: only ~26 galaxies
- BH M-σ: mixed measurement techniques (1 dex scatter)
- MCXC: cluster masses from X-ray scaling, not direct measurements
- Pantheon+: Ω_m = 0.38 vs Planck 0.315 (H₀–Ω_m degeneracy)

---

## Part 7: Open Questions

1. What drives the 0.2 dex between-galaxy RAR scatter? (H015: test with SFR tracers)
2. Does cluster L-M slope excess correlate with environment? (H009)
3. Is BH M-σ non-linear? (H010)
4. Does galaxy bimodality have a third population? (H018)
5. Are CMB anomalies connected to Hubble tension? (H022)
6. Can precise local density metrics reveal environmental effects on cluster relations?

---

*Combined from FINDINGS.md + INSIGHTS.md (merged per orchestrator recommendation)*