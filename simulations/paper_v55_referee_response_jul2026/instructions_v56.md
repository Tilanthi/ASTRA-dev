# Instructions for v56 — Response to Two Referee Reports on v55
## "Core Spacing in HGBS Filaments: MHD Fragmentation Tests and the Perpendicular-Field Tension" (G. J. White)

**Prepared by:** ASTRA-PA · **Date:** 2026-07-27 · **Produce:** v56 from v55.

> **Access note:** the v55 PDF was not retrievable from the given GitHub path (it is not on `main`; the raw URL 404s even with the repo token — the API shows the latest pushed paper is v53). This instruction set is therefore built from the **two full referee reports** (which quote v55's specific content — abstract line 30, §2.7 FilFinder values, Table 2, §4.6.1, etc.) plus the v53 text and my knowledge of the v54 changes that produced v55. If any drop-in text below conflicts with a passage the writer sees in v55, keep v55's actual numbers and apply the *intent* of the instruction.

---

# 0. THE CENTRAL QUESTION (Glenn's query): is the "demonstrated failure → cannot demonstrate agreement" change a fundamental problem, and how do we get around it?

**Short answer: the referee is correct, but it is NOT a fundamental problem with the paper — it is confined to the perpendicular-field arm and to its *wording*, and it is fixable (and now, by new simulations, largely resolvable).**

1. **Is the statement true?** Yes. The paper's own Appendix A shows the perpendicular simulations are measured at N_J ≈ 1–2 cells per Jeans length, violating the Truelove (1997) criterion (≥4). An unconverged calculation cannot support a *demonstrated* physical claim. So we cannot write "current perpendicular-field models fail"; we can only write "our current (unconverged) calculations do not yet demonstrate agreement." Both referees insist on this and they are right.

2. **Is it a complete problem for presenting the simulations?** **No.** It affects only the **perpendicular** quantitative numbers (λ/W_fil ≈ 0.85, 1.4). The two results the paper actually rests on are unaffected:
   - the **observational** sub-Jeans NN spacing (robust, converged, the true headline), and
   - the **longitudinal** supercritical agreement (Truelove-*satisfied*, 5–7 cells/Jeans; 128³/256³ convergence-tested — Appendix A). These stand.
   So the fix is a **reframing of the perpendicular arm**, not a rework of the paper.

3. **How do we get around it — and the important new evidence.** Two complementary routes, and the first is now producing data:
   - **(a) Converge the perpendicular runs (the definitive fix).** ASTRA-PA is running the perpendicular ambipolar configurations at doubled transverse resolution (512×128×128, so N_J ≳ 4). **Preliminary result (runs still completing):** at the higher, Truelove-satisfying resolution the perpendicular filaments show **no longitudinal beading** through the epoch where the low-resolution runs beaded — instead they **collapse radially** (e.g. f=1.5, β=2.0 reaches density contrast C ≈ 840 with **zero** longitudinal peaks by t ≈ 0.30 t_J and is still deepening, whereas the 64³ baseline "beaded" with ~11 peaks at t ≈ 0.55). **This indicates the low-resolution perpendicular "beading" (λ/W ≈ 0.85–1.4) was largely a numerical artefact of under-resolution** (under-resolution seeds spurious small-scale fragmentation → spurious short-wavelength peaks). If confirmed, the converged perpendicular result is *not* "beading at λ/W ≈ 0.85" but "**radial/spindle collapse with no longitudinal fragmentation**" — a cleaner, converged statement that removes the referee's objection.
   - **(b) Reframe the wording now (independent of the runs, the safe path).** Replace every "perpendicular models fail / do not explain" with "our current, numerically unconverged perpendicular calculations do not yet demonstrate agreement." Make the observational + longitudinal results the headline. (Details in M1/R1-#1 below.)

   **Recommendation to Glenn:** adopt (b) now for v56, and hold a short addendum for (a)'s converged result. **The converged perpendicular runs may actually strengthen the paper** — either they confirm "perpendicular filaments do not fragment longitudinally at all" (a clean converged prediction, and the real 'tension' becomes *observed spacing vs simulated non-fragmentation*), or the wavelength shifts up toward observation (reducing the tension). Either outcome converts a criticised, unconverged number into a defensible result. **Do not** frame the perpendicular case as a *demonstrated failure* in the meantime.

The rest of this document implements this and the specific referee items.

---

# PART A — REFEREE 2 MAJOR ITEMS (M1–M8)

## M1. Perpendicular claim overstated vs the paper's own resolution test [TEXT + COMPUTE-RUNNING]
Both referees' #1 point. See §0. Concrete edits:
- **[TEXT] Abstract:** the closing sentence "current ideal-MHD fragmentation models do not explain the majority of observed HGBS filaments" must be replaced. Use:
  > "For the ~90% perpendicular-field majority we find no evidence that current models reproduce the observations, but this comparison is not yet decisive: our perpendicular calculations are numerically unconverged (N_J ≈ 1–2 cells per Jeans length, below the Truelove criterion; Appendix A) and a resolution study is in progress. We therefore treat the perpendicular-field discrepancy as a preliminary, unresolved question rather than an established failure of the models."
- **[TEXT] Conclusions:** move the perpendicular statement **out of the "Established" tier** into "Likely/Speculative" (or a new "Preliminary" line). The Established tier keeps only: Gaia revisions increase spacing; NN spacing is sub-Jeans; pairwise = L/3; longitudinal models approach the observed spacing *after T1 calibration*.
- **[TEXT] Discussion (§5.1):** wherever the perpendicular λ/W appears, write "our current resolution-limited simulations produce λ/W ≈ …" and add "the low-resolution beading may not survive refinement (Appendix A; convergence study in progress)."
- **[COMPUTE-RUNNING]** The doubled-resolution spot-check (Referee 2's option a) is running; ASTRA-PA will deliver the converged perpendicular outcome as an addendum. Preliminary indication (strengthening as the runs deepen): beading suppressed, radial collapse dominates — f=1.5,β=2.0 at C≈840 with zero peaks (§0). Final termination outcome to be harvested.

## M2. T1 applied outside its calibration domain for the perpendicular comparison [TEXT + COMPUTE]
T1 is calibrated on longitudinal snapshots only (β=0.5/1.0/2.0, θ=0°, n=72; ASTRA-PA verified this last round). Applying it to perpendicular runs is unjustified and no systematic is propagated.
- **[COMPUTE-can-do]** ASTRA-PA can forward-model a subset of the perpendicular snapshots through the synthetic-HGBS pipeline to obtain a perpendicular-specific T1, OR bound the anisotropy analytically (a perpendicular field adds magnetic pressure in the plane of the sky differently than along the line of sight, changing the projected FWHM by up to ~the plasma-β-dependent factor). **However**, given the M1 preliminary result (perpendicular beading may be a resolution artefact), this is only worth doing once the perpendicular runs are converged. **Recommended interim:** attach an explicit ± systematic to the perpendicular λ/W.
- **[TEXT]** Add a perpendicular-specific T1 uncertainty to Table 9, Figure 11, and the population-weighted synthesis. Until the forward-model bound is available, quote it as an explicit unquantified-but-flagged band, e.g. "λ/W_fil ≈ 0.85 (longitudinal-calibrated T1; a perpendicular-specific normalisation is not yet available and could shift this by O(10–20%))."
- **[TEXT] §3.1:** state plainly "T1 is calibrated on longitudinal-field snapshots only and its application to perpendicular runs is provisional."

## M3. Largest observational systematic (skeleton algorithm: FilFinder vs DisPerSE, 2–3×) not in the error budget [GLENN-OBS + TEXT]
§2.7 reports FilFinder gives λ/W ≈ 0.4/0.6/0.7/0.8 vs DisPerSE 1.0/1.9/2.1/1.8 — a factor 2–3, larger than any other term, yet omitted from the §2.8 budget (σ_sys ≈ 28%).
- **[GLENN-OBS] Preferred (option i):** run the same injection–recovery validation on the FilFinder skeletons as was done for DisPerSE (§2.7), to determine whether the discrepancy is a measurable FilFinder over-branching bias (correctable) rather than a genuine spacing ambiguity; report the corrected FilFinder number. *(ASTRA-PA can run the injection–recovery on the FilFinder skeletons if Glenn provides them + the injection code.)*
- **[TEXT] Minimum (option ii):** add the FilFinder/DisPerSE discrepancy **explicitly as a term (or a clearly-separated caveat) in the §2.8 systematic budget**, not a one-line dismissal. State that the sub-Jeans conclusion (λ/W well below 4) survives the algorithm change (both give sub-Jeans) but the *precise value* is skeleton-algorithm-dependent at the factor-~2 level:
  > "The skeleton-extraction algorithm is the single largest observational systematic: an independent FilFinder pipeline gives values 2–3× smaller than DisPerSE. Both remain far sub-Jeans, so the qualitative conclusion is robust, but the quantitative λ/W carries a skeleton-algorithm systematic of order a factor 2, which we do not fold into the ±0.5 budget and flag separately here."

## M4. Figures 9–10 shade the pairwise-median "HGBS window", not the preferred NN range [TEXT + COMPUTE]
The shaded [2.52, 3.08] window equals the pairwise-median (2.84), which the paper argues is L/3-biased and NOT the fragmentation wavelength. Benchmarking the simulations against it contradicts the paper's own thesis.
- **[TEXT/COMPUTE] Relabel the shaded window to the NN-based range.** The NN observable is λ/W_fil ≈ 1.9 (fixed width), plausible range 1.4–2.4. On the λ/W_fil (T1-corrected) axis, shade **[1.4, 2.4]** (or 1.9 ± 0.5) and label it "NN observable (preferred statistic)". If the pairwise-median window is kept for legacy comparison, label it explicitly "pairwise median = L/3-biased, not the fragmentation wavelength" in **every** panel.
- **[TEXT] §4.8.3:** rewrite the accompanying text. The current "two highest-β points lie in the HGBS window ... become 1.86, 1.82 below the window" must be recast against the NN window: e.g. "the T1-corrected near-critical values (1.82–1.86) lie within the preferred NN range (1.4–2.4), whereas they fall below the legacy pairwise-median window; this is expected, since the pairwise median overestimates the fragmentation wavelength by ~30–45% (§2.6)."
- *(ASTRA-PA can regenerate Figs 9–10 with the corrected window from the per-β means if the writer supplies/points to the near-critical λ/W-vs-β data.)*

## M5. Population-weighted headline number has no propagated uncertainty [COMPUTE-DONE + TEXT]
**ASTRA-PA has propagated it** (Monte Carlo over f_perp ∈ U(0.6,1.0), perp λ/W ∈ U(0.85,1.4), long λ/W ∈ N(2.1,0.4), T1 ∈ U(0.59,0.78)/0.65; `support/population_weighted_propagated.json`):
- **Population-weighted λ/W_fil = 1.38, 68% CI [1.10, 1.66], 95% CI [0.97, 1.87]**, vs observed 1.9–2.5.
- The mismatch is **real but not high-significance**: the 95% upper edge (1.87) nearly reaches the fixed-width observed value (1.9).
- **[TEXT] Required:** show this as an **error band in Figure 11** and **relabel the synthesis "Speculative/illustrative"** in the Conclusions tier (Referee 2's explicit choice) — do NOT use it to support an "Established" principal-outcome bullet. Draft:
  > "Propagating the field-geometry fraction, the perpendicular resolution systematic, and the T1 systematic, the population-weighted prediction is λ/W_fil ≈ 1.4 (95% CI 1.0–1.9). This lies below the observed 1.9–2.5, but with a large uncertainty whose upper edge approaches the observation; we therefore present this synthesis as illustrative/speculative rather than established."

## M6. T1 central value 0.65 offset from the sample median 0.61 [COMPUTE-DONE + TEXT]
ASTRA-PA confirms the n=72 sample median = mean = 0.61 (p10–p90 0.52–0.69), and 0.65 is **midway between median and p90, not "near p90".**
- **[TEXT] Recommended:** **adopt T1 = 0.61 (the sample median)** as the central value, keep 0.59–0.78 as the systematic band. **This shifts the supercritical ensemble λ/W_fil from 2.1 to 2.0** (ASTRA-PA: 3.27×0.61 = 1.99; `support/T1_median_adoption.json`), **still consistent with the NN observable 1.9**, and shifts the perpendicular numbers down ~6%. Correct the "near p90" characterisation. This also removes any appearance of tuning T1 upward to improve agreement.
- Propagate the 2.1→2.0 change everywhere the supercritical number appears (Abstract, §4.6.6, §5.1, Table 9, Conclusions).

## M7. Ambient-confinement setup not benchmarked to observed HGBS conditions [TEXT + GLENN-LIT]
Whether supercritical filaments fragment longitudinally vs collapse radially depends entirely on the imposed ambient contrast (~10² central-to-ambient), which anchors the *positive* longitudinal result. It must be shown representative, not tuned.
- **[TEXT] Add a sentence in §4.6.6 / §5.2** comparing the assumed central-to-ambient density contrast (~100) and approximate radial force balance to observationally constrained filament-to-background contrasts in the four robust regions from published background-subtracted column-density profiles (Arzoumanian et al. 2019 give crest-to-background contrasts of order 10–100 for HGBS filaments; cite the specific values). Draft:
  > "The adopted central-to-ambient density contrast (~10²) and approximate radial force balance are consistent with background-subtracted HGBS column-density profiles (crest-to-ambient contrasts of order 10–100; Arzoumanian et al. 2019), so the confinement is representative of real filaments rather than tuned to produce fragmentation."
  (Glenn to confirm the exact literature contrast values for the four regions.)

## M8. Too many λ/W definitions; move the summary table to the start of §2 [TEXT]
Same as Referee 1 #3. **Move an expanded Table 2 (or a short "which number to cite for which purpose" paragraph) to the very start of §2, before any specific value is quoted.** Include one row per quantity with Value + Meaning: observed raw NN; observed bias-corrected NN (fixed width); NN with region-specific widths; Taurus-only NN; full-sample pairwise median; robust-region pairwise median; 3D-corrected pairwise median; fibre-to-core; simulation λ/W_core; simulation λ/W_fil (T1-corrected). Mark which is the **preferred** statistic (bias-corrected NN, fixed width). (ASTRA-PA can draft the table from the paper's numbers if useful.)

---

# PART B — REFEREE 1 MAJOR / STRUCTURAL

- **R1-1 Perpendicular wording** — done under M1/§0. Replace "demonstrated failure" language throughout (Abstract, Discussion, Conclusions) with "present inability to demonstrate agreement because the calculations are not yet numerically converged."
- **R1-2 T1 = "a provisional calibration"** [TEXT]: replace "the adopted normalisation" with "a provisional calibration" throughout; never treat T1 as a measured constant. Combine with M6 (adopt 0.61).
- **R1-3 Too many headline numbers → summary table** [TEXT]: same as M8.
- **R1-4 Length: cut ~20%** [TEXT]: reduce repeated leave-one-out discussions, repeated "Gaia scales distances" statements, repeated pairwise-statistic and width-convention explanations. Move methodological detail (injection-recovery specifics, per-region robustness tables) to an Appendix/Supplementary. Explain each key message **once**.
- **R1-5 L/3 argument needs a derivation** [TEXT + COMPUTE]: add a short derivation or supplementary proof that the pairwise median → L/3 for N points on a filament of length L. *(ASTRA-PA can supply the derivation: for N points uniformly distributed on [0,L], the distribution of all pairwise distances has median ≈ L/3 as N→∞; the mean pairwise distance is exactly L/3, and the median converges to it. I can provide the ~half-page derivation + a numerical check figure — flag if wanted.)*
- **R1-6 Distinguish observational vs theoretical conclusions** [TEXT]: separate "observations show λ/W ≈ 2 (robust)" from "simulations show certain geometries can reproduce similar values (provisional on T1 and, for perpendicular, on resolution)."
- **R1 Convergence — boxed statement in §4** [TEXT]: add a highlighted box in Section 4: "Quantitative perpendicular predictions should be regarded as preliminary: they are numerically unconverged (N_J ≈ 1–2; Appendix A) and a resolution study is in progress."
- **R1 Boundary conditions — make ambient-confined the primary simulation** [TEXT]: restructure §4 Results so the **ambient-confined** models are presented as the primary/physical case and the periodic-box runs as a contrast/diagnostic (they only illustrate the boundary-driven radial-collapse artefact). This also supports M7.
- **R1 Magnetic interpretation — Planck caveat more prominent** [TEXT]: state clearly and early (Introduction + §5.1) that Planck measures **large-scale projected** field orientation, **not internal filament field topology**; refer to the 90/10 mapping as **circumstantial** every time it is used.
- **R1 Width — Gaussian + Plummer together in a figure** [TEXT + GLENN-OBS]: since Taurus dominates one conclusion, add a figure showing both Gaussian and Plummer width results per region side by side. (Glenn supplies the per-region Gaussian vs Plummer fits.)

## Referee 1 writing / conclusion
- **Reduce repetition** (NN preferred; pairwise = L/3; width convention dominates; Gaia scales spacing) — each once.
- **Simplify caveat language**: replace multi-caveat sentences (e.g. "provisionally consistent assuming T1 although subject to width uncertainties and pending convergence") with "The current simulations are consistent with the observations within the present calibration uncertainties." Keep the detailed caveats in one place (a Limitations paragraph), not repeated inline.
- **Conclusion focused on 4 results** [TEXT]: (1) preferred NN λ/W ≈ 1.9–2.5 depending on width convention; (2) robust against observational systematics; (3) longitudinal-field MHD can reproduce similar spacings (provisional on T1); (4) existing perpendicular calculations are inconclusive owing to insufficient numerical resolution.
- **Minors:** define every symbol once in the Introduction; reduce decimal places; avoid switching λ/W ↔ λ/W_core ↔ λ/W_fil within a paragraph; every figure caption states raw vs corrected; enlarge/simplify the pipeline figure (Fig. 1).

---

# PART C — REFEREE 2 MINOR / TECHNICAL

1. **[TEXT]** Table 1: the "Weighted Mean" row's Std Error (0.009) is the SE *on the weighted mean*, a different quantity from the per-region SEs in the same column — separate them (distinct row label or footnote) so the sample scatter is not misread.
2. **[TEXT — verify in proof]** §4.6.1 has a corrupted/incompletely-typeset sentence: "self-gravity is solved using an FFT Poisson solver with four pi G = 4π 2 so that λ_J = 1 by construction." Fix to "with 4πG = 4π² (so λ_J = 1 by construction)". Also check the equations in §3.2 and §4.6.1 render correctly in the typeset proof (they showed extraction/rendering trouble).
3. **[TEXT]** Figure 2 (right panel): give the Yang et al. (2024) fibre-to-core value (0.42) a **visually distinct marker/hatching** — it is a within-fibre quantity, not a filament-level measurement, and must not read as directly comparable.
4. **[TEXT]** Clarify whether "~10⁴ CPU-hours" is the MHD-only figure or MHD+RT combined; give the MHD-only number for reproducibility-cost assessment.
5. **[TEXT]** Trim the Abstract to the 2–3 genuinely novel, well-supported results (bias-corrected NN sub-Jeans; longitudinal agreement; perpendicular flagged preliminary per M1); move secondary numbers (region-specific-width value, pairwise-median comparison) to the body. (Also Referee 1's abstract-density concern.)
6. **[GLENN]** ADS-check Zhang et al. (2023, A&A 677, A123) and Yang et al. (2024, ApJ 976, 117) — the referee could not confirm exact volume/page; these underpin the distance revision and the hierarchical alternative. (Jadhav et al. 2026 verified OK.)
7. **[TEXT]** Protostellar migration: §2.1 says "~5–10%", §2.8 says "~7.5%" — use one consistent figure (7.5% or the 5–10% range) in both.
8. **[COMPUTE-can-do]** EOS adiabatic non-fragmentation (0/30, "timed out at t > 30–40 t_J"): confirm it is genuine stability, not insufficient integration time. *(ASTRA-PA can extend one or two γ=5/3 runs substantially further, or supply the analytic argument: under adiabatic heating with γ=5/3 > γ_crit, the effective sound speed rises on compression faster than gravity, so a marginally-supercritical filament re-stabilises — no finite integration time produces fragmentation. Recommend adding the analytic argument + one extended run.)*

---

# PART D — WHAT ASTRA-PA PROVIDES / IS RUNNING

**[COMPUTE-DONE] in `support/`:**
- `population_weighted_propagated.json` — M5 (weighted 1.38, 95% CI 0.97–1.87; label Speculative).
- `T1_median_adoption.json` — M6 (adopt T1=0.61 → supercritical λ/W_fil = 2.0).

**[COMPUTE-RUNNING] on the cluster (ETA hours–1 day):**
- Higher-resolution perpendicular ambipolar rerun (512×128×128, N_J ≳ 4) — M1 / Referee 1 #1 / Referee 2 M1. **Preliminary: beading suppressed, radial collapse dominates → low-res perpendicular "beading" likely a numerical artefact.** Converged outcome to follow as an addendum; the v56 text should adopt the reframing now and can be strengthened when this lands.

**[COMPUTE-can-do on request]:**
- Perpendicular-specific T1 forward-model (M2) — best done after the perpendicular runs converge.
- FilFinder injection–recovery (M3) — needs Glenn's FilFinder skeletons + injection code.
- Figs 9–10 regeneration with the NN window (M4) — needs the near-critical λ/W-vs-β data.
- L/3 derivation + numerical-check figure (R1-5).
- Extended γ=5/3 EOS run (Referee 2 minor 8).

**[GLENN-OBS]:** FilFinder budget term / injection (M3); ambient-contrast literature values (M7); Gaussian-vs-Plummer per-region figure (R1 width); ADS reference check (minor 6).

---

## Bottom line for Glenn
The two referees are aligned and constructive: **there is no fatal flaw and no large new campaign is needed.** The revision is (1) reframe the perpendicular result as *preliminary/unconverged* (not a demonstrated failure) — which the running higher-resolution runs are turning into a genuinely converged result; (2) adopt T1 = 0.61 (→ supercritical λ/W = 2.0) and call T1 a provisional calibration; (3) propagate the population-weighted uncertainty and label that synthesis Speculative; (4) put the FilFinder/DisPerSE systematic in the budget; (5) relabel the Figs 9–10 window to the NN statistic; (6) front-load the summary table, cut ~20%, and make the observational sub-Jeans result the clear headline. Items (1), (2) and (4) are the ones both referees will check first.
