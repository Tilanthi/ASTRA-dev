# Instructions for v54 — Response to Two Referee Reports on v53
## "Core Spacing in HGBS Filaments: MHD Fragmentation Tests and the Perpendicular-Field Tension" (G. J. White)

**Prepared by:** ASTRA-PA · **Date:** 2026-07-27 · **Produce:** v54 from v53.

### Orientation
v53 has already absorbed most of the previous round's fixes (region-specific deconvolved widths, Table 7 mass-to-flux, the Fig. 1 pipeline figure, the Truelove Appendix A / Table A1, the NN-pipeline counts). **The two new referees are broadly positive and both recommend Major Revision that is achievable by re-framing + a few small additions — no large new simulation campaign is required.** They converge on one central message:

> **Scope the "consistency" claim correctly and make the *negative* result the headline.** The longitudinal match explains only the ~10% minority; the ~90% perpendicular population is *not* explained, and the perpendicular numbers are resolution-limited. Present a **population-weighted** comparison, downgrade "tension"-as-established-result language, and mark the simulation–observation agreement as **provisional on the T1 normalisation**.

Every instruction below is tagged: **[TEXT]** (drop-in wording for the writer), **[COMPUTE-DONE]** (ASTRA-PA computed it; number/figure supplied in `support/`), **[COMPUTE-RUNNING]** (a higher-resolution check is running on the cluster; result to follow), **[GLENN-OBS]** (needs Glenn's HGBS catalogues/DisPerSE code). Draft text is in `>` blockquotes; the writer should adapt to house style but keep the quantitative content.

---

# A. THE SINGLE HIGHEST-PRIORITY ADDITION — population-weighted synthesis (Referee 2 #1) [COMPUTE-DONE]

Referee 2 #1 is the most important new requirement and the paper currently omits it: if ~90% of filaments are perpendicular, the **population-weighted** theoretical prediction is dominated by the perpendicular number, and the paper must compute it and compare to the observed ensemble.

**ASTRA-PA has computed it** (`support/population_weighted_synthesis.json`, `support/figures/population_weighted.png`):

- Longitudinal (10%): λ/W_fil ≈ **2.1**.
- Perpendicular (90%): λ/W_fil ≈ **0.85** (ideal-MHD) to **1.4** (ambipolar, onset).
- **Population-weighted prediction** = 0.9 × [perp] + 0.1 × [long] = **0.97 (with perp = 0.85) to 1.47 (with perp = 1.4); full band ≈ [0.85, 1.54]** over f_perp ∈ [0.8, 1.0].
- **Observed NN** = **1.9** (fixed 0.10 pc width) to **2.5** (region-specific widths).
- **Verdict:** the population-weighted MHD prediction (~1.0–1.5) lies **well below** the observed spacing (~1.9–2.5). **Taken at face value, current MHD models under-predict the spacing of the bulk (perpendicular) population; the longitudinal "consistency" applies only to the ~10% minority.**

### Required changes
1. **[TEXT] Add a short synthesis paragraph in §5.1** (immediately after introducing the longitudinal match), with the number:
   > "Because Planck Collaboration (2016) find that only ~10% of filaments have longitudinal large-scale fields, the population-weighted prediction is dominated by the perpendicular case: 0.9 × (λ/W_fil ≈ 0.85–1.4)_⊥ + 0.1 × (λ/W_fil ≈ 2.1)_∥ ≈ 1.0–1.5. This is well below the observed NN spacing (λ/W ≈ 1.9 under the fixed-width convention, ≈ 2.5 with region-specific widths). Taken at face value, therefore, current ideal- and non-ideal-MHD models **under-predict** the spacing of the majority of the observed population; the agreement we find is confined to the ~10% longitudinal minority. Consistency with the full sample would require either the internal filament fields to be substantially more longitudinal than the large-scale 10% (untested; Section 5), a contribution from hierarchical fibre fragmentation (Section 3.3), or a change in the perpendicular result once the resolution limitation (Appendix A) is removed."
2. **[TEXT] Add one clause to the Abstract** so the scope is explicit there, not only in §5:
   > "…consistent with observation for the ~10% longitudinal minority; the population-weighted prediction for the ~90% perpendicular majority (λ/W ≈ 1.0–1.5) lies below the observed ≈ 1.9–2.5, so current MHD models do not yet explain the bulk of the sample."
3. **[TEXT] Add the supplied figure** `population_weighted.png` as a new figure (or a panel of the summary figure), showing longitudinal / perpendicular / population-weighted predictions against the observed band and the IM92 value.
4. **[TEXT] Propagate the two dominant uncertainties** in the paragraph: the large-scale→internal field mapping (state it is circumstantial; if internal fields are more longitudinal the weighted value rises toward observation) and the perpendicular resolution limitation (Appendix A; the higher-resolution check is in progress — see §C below).

---

# B. THE PERPENDICULAR RESULT IS RESOLUTION-LIMITED — downgrade the framing (Referee 2 #2, Referee 1 #6) [TEXT + COMPUTE-RUNNING]

Both referees flag that the perpendicular λ/W (0.85 ideal, 1.4 ambipolar) is measured at N_J ≈ 1–2 cells per Jeans length (Truelove violated; Table A1), and that the paper nonetheless names it "the perpendicular-field tension" in the abstract/title-adjacent framing. Referee 2 requires **either** a higher-resolution rerun **or** a language downgrade.

- **[COMPUTE-RUNNING]** ASTRA-PA has launched a **higher-resolution perpendicular rerun** (2 representative ambipolar configs at doubled transverse resolution, 512×128×128, so N_J ≳ 4 at the measurement epoch) on the cluster. This directly tests Referee 2's option (a). *Note on the direction of the bias:* under-resolution seeds spurious small-scale fragmentation → extra peaks → **shorter** apparent λ, so the true perpendicular λ/W may be **larger** than 0.85 (i.e. the resolution fix could *reduce* the tension). The rerun will settle this; result to be delivered as an addendum (ETA ~a day given the slow ambipolar timestep). **Until it lands, adopt the downgrade (option b) below** — it is the safe, referee-accepted path and does not depend on the rerun.
- **[TEXT] Downgrade the "tension" framing throughout** (Referee 2 #2, Referee 1 #5/#6):
  - In the **Abstract**, replace "We term this mismatch the perpendicular-field tension" with a scoped, provisional statement:
    > "The majority perpendicular-field population is not reproduced by our current simulations, which are resolution-limited for this geometry (Appendix A): ideal-MHD and ambipolar runs give λ/W_fil ≈ 0.85 and ≈ 1.4 at N_J ≈ 1–2 cells per Jeans length. We flag this as a preliminary, unresolved discrepancy pending a convergence study, rather than an established result."
  - Keep the phrase "perpendicular-field tension" only in the body as a *label for the open question*, not as a demonstrated quantity.
  - **[TEXT]** Everywhere the perpendicular λ/W appears, use "our current resolution-limited simulations produce λ/W ≈ …" (Referee 1 #6), not "perpendicular fields produce λ/W ≈ …".
  - **[TEXT]** In **Table 9** (and any results table), move the perpendicular λ/W entries out of any row that implies equal footing with the resolved longitudinal numbers, or add a **"resolution status" column** (see §D) marking the perpendicular rows "resolution-limited (N_J ≈ 1–2)."

---

# C. T1 IS CALIBRATED ON LONGITUDINAL GEOMETRY ONLY — flag the perpendicular systematic (Referee 2 #4) [COMPUTE-DONE]

Referee 2 #4 asks what geometries/β the n=72 T1 calibration spans, and whether T1 should differ for perpendicular fields. **ASTRA-PA checked the calibration set** (`support/T1_geometry_breakdown.json`): the 72 runs carry **no θ field and span β = 0.5/1.0/2.0 with a single (longitudinal) geometry** — i.e. **T1 = 0.65 is calibrated on longitudinal-field runs only.**

### Required changes
1. **[TEXT] State the calibration composition explicitly** in §3.1 (the T1 paragraph):
   > "The T1 calibration sample (n = 72) spans β = 0.5, 1.0, 2.0 at fixed longitudinal field geometry (θ = 0°). It does not include perpendicular-field configurations."
2. **[TEXT] Flag the resulting systematic for the perpendicular comparison** (Referee 2 #4): anisotropic magnetic pressure changes the beam-convolved column-density width differently for a perpendicular field seen at a given viewing angle, so applying the longitudinal-calibrated T1 to the perpendicular runs carries an **additional, unquantified systematic**. Add to §5.1 / Appendix A:
   > "Because T1 is calibrated only on longitudinal-field snapshots, its application to the perpendicular runs carries an additional, currently unquantified width-normalisation systematic (anisotropic magnetic pressure can alter the projected width with field orientation); this compounds the resolution limitation for the perpendicular numbers."
3. This strengthens the case for the downgrade in §B and should be one of the reasons cited for treating the perpendicular λ/W as preliminary.

---

# D. TABLE 9 vs SEC. 4.6.6 CROSS-REFERENCE (Referee 2 #3) [TEXT]

v53's Table 9 caption already explains the near-critical-vs-supercritical distinction, but Referee 2 wants (i) a clarifying sentence at the **start of §5.1** and (ii) the two results merged into one table with a **status column** so a first-pass reader cannot conflate them.

1. **[TEXT] First sentence of §5.1:**
   > "Two simulation numbers appear for the longitudinal case and must not be conflated: the *near-critical* grid (Table 9) is a calibration that does **not** extrapolate to the supercritical regime and does **not** match observation, while the *directly measured supercritical* ensemble (Section 4.6.6, λ/W_fil ≈ 2.1) is the relevant comparison and does match. All numbers use the same T1 factor; the difference is the physical regime, not the normalisation."
2. **[TEXT] Merge Table 9 with the Sec. 4.6.6 result** into one summary table with a **"role/status" column**:
   | Configuration | λ/W_core | λ/W_fil (×T1) | Role / status |
   |---|---|---|---|
   | Longitudinal near-critical (Table 9, β=2.0) | 2.80 | 1.82 | calibration — **not** applicable to comparison |
   | Longitudinal supercritical ensemble (§4.6.6) | 3.27 | **2.1** | **primary comparison — matches obs (T1-provisional)** |
   | Perpendicular near-critical (β≥1) | 1.25 | 0.81 | **resolution-limited (N_J≈1–2); preliminary** |
   | Perpendicular ambipolar (onset) | ~2.2 | 1.4 | **resolution-limited, fragmentation-onset; preliminary** |
   (Populate exactly from the paper's current numbers; the point is the status column.)

---

# E. SECTION 6 / COMPANION PAPER (Referee 2 #5) [TEXT]

Referee 2 #5: the non-isothermal argument leans on an unpublished "White, in prep." companion (with a self-flagged anti-conservative Moran's I) plus a single n=1 simulation, yet the abstract/Conclusions state "the isothermal assumption is not conservative locally" as a general claim.

### Required changes (choose one; softening is simplest)
1. **[TEXT] Soften to what is actually demonstrated here.** In the Abstract and Conclusions replace the general claim with the single-realisation scope:
   > "A single illustrative simulation shows that an imposed ~12% temperature gradient shifts the local λ/W by ~0.2 and relocates which half of the filament fragments; this indicates the isothermal assumption *can be* non-conservative locally under plausible conditions (a fuller cloud-scale analysis is deferred to a companion paper)."
   Remove any wording that presents the environment-dependent M–T variation as established in *this* paper; attribute it only as "suggestive, companion analysis in preparation."
2. **[TEXT]** Do not cite the companion's Moran's I significance as support here; if the companion result is needed, make it available to the editor/referees (Glenn's call). Given Referee 2's framing, **option 1 (soften) is recommended** and requires only wording changes.

---

# F. REFEREE 2 MINOR ITEMS

- **F1. Seeds-per-point for power-law fits (t_frag(f) ∝ f^0.39±0.01)** [TEXT + GLENN/DATA]: report the number of seeds per grid point for the key fits, and **propagate the ~2% seed-to-seed stochasticity into the exponent uncertainty** (currently fit-only). If the main-grid used few seeds/point, widen the quoted error (e.g. 0.39 ± 0.01_fit → ± 0.03 including seed scatter). *(ASTRA-PA can recompute the exponent error with seed scatter if pointed at the main-grid results JSON.)*
- **F2. Independent skeleton cross-check (FilFinder vs DisPerSE) only for Taurus** [GLENN-OBS]: extend to all four robust regions, or justify why Taurus alone suffices. Add the resulting per-region comparison to §2.9.
- **F3. Manual spur editing not in the §2.8 systematic budget** [GLENN-OBS/TEXT]: either quantify it (two independent editors → compare λ/W) or **list it explicitly as an unquantified systematic** in §2.8. The latter is a one-line addition:
  > "Manual spur removal during skeleton cleaning is an additional, currently unquantified systematic; we estimate its effect on λ/W is smaller than the width-convention term but have not bounded it with independent re-editing."
- **F4. Jeans-swindle confirmation (Eq. 7–10)** [TEXT — verify with Glenn]: state explicitly whether the periodic FFT self-gravity solver subtracts the mean density (∇²φ = 4πG(ρ − ⟨ρ⟩)); a periodic Poisson solve with nonzero mean is ill-posed without it. Athena++'s FFT gravity **does** subtract the mean by construction — add one sentence confirming this:
  > "The periodic FFT Poisson solver operates on the density fluctuation ρ − ⟨ρ⟩ (the Jeans-swindle background subtraction is implicit in the FFT solver), so the periodic problem is well-posed."
- **F5. Abstract uncertainty statistic** [TEXT]: Referee 2 finds "cloud-to-cloud scatter σ≈0.4" unconventional as the headline. **Pick one primary, clearly-defined statistic for the abstract** — the bootstrap 95% CI already computed (spacing 0.261–0.298 pc; convert to λ/W under the fixed width for the abstract) — and relegate the quadrature sum / plausible range / cloud-to-cloud scatter to the body as a sensitivity discussion. Draft:
  > "…λ/W ≈ 1.9 (bootstrap 95% CI on the spacing 0.261–0.298 pc); we discuss the width-convention and cloud-to-cloud systematics separately in Section 2."
- **F6. Clustered (non-periodic) injection test** [GLENN-OBS]: the 1.11–1.29 bias correction assumes periodic input spacings; real cores may be clustered. Add a **clustered-injection recovery test** to bound this on the primary NN result. *(ASTRA-PA can run the injection–recovery with a clustered input point process if given the injection code; otherwise Glenn runs it.)* This also answers Referee 1's minor "discuss whether clustered rather than periodic injections would alter recovery."

---

# G. REFEREE 1 — FRAMING AND MAJOR EDITORIAL

- **G1. Emphasise the NN methodology (Referee 1 #2)** [TEXT]: expand the NN section (L/3 argument, injection-recovery, robustness, population, bootstrap, leave-one-out) and **cut later discussion** to compensate (see G-length). Referee 1 considers this the paper's strongest contribution; give it prominence.
- **G2. "Provisionally consistent assuming T1" (Referee 1 #3, #4)** [TEXT]: replace every "consistent with observations" for the simulation comparison with **"provisionally consistent with observations, assuming the adopted T1 normalisation."** State plainly: *one subset of simulations reproduces one subset of observations after a calibration that still carries substantial uncertainty* — not "the simulations explain the observations."
- **G3. Headline the negative result (Referee 1 #5)** [TEXT]: make the **principal stated conclusion** "current ideal-MHD (and resolution-limited non-ideal) fragmentation models do not explain the majority of observed filaments." This dovetails with the population-weighted number (§A). Put it first in the Conclusions and reflect it in the Abstract's closing sentence.
- **G4. Resolution language (Referee 1 #6)** [TEXT]: see §B — "our current resolution-limited simulations produce…" throughout the perpendicular discussion.
- **G5. Expand the width discussion (Referee 1 #7)** [TEXT + GLENN-OBS]: width uncertainty (~25%) is the dominant observational systematic. Add a dedicated subsection covering: **Gaussian vs Plummer fitting; profile/aperture selection; environmental dependence; beam convolution; and specifically why Taurus differs so dramatically** (median width and λ/W). If Glenn has the per-region width fits, tabulate Gaussian-vs-Plummer widths side by side.
- **G6. Statistical independence earlier (Referee 1 #8)** [TEXT]: state that **clouds, not cores, are the independent units** early in §2 (before quoting thousands of spacings), not only in the later hierarchical-statistics subsection.
- **G7. Longitudinal-field evidence = "circumstantial" (Referee 1 #9)** [TEXT]: consistently describe the large-scale-to-internal field mapping as **circumstantial evidence**, not stronger. (v53 already hedges "internal geometry untested"; make the word "circumstantial" explicit and consistent.)

## Referee 1 minor
- **G8** [TEXT/GLENN]: injection-recovery — explicitly discuss whether **clustered** injections would change recovery (merges with F6).
- **G9** [TEXT/GLENN]: morphological closing — give **quantitative justification for the adopted bridging length** (why that value; sensitivity already partly shown — cite it here).
- **G10** [TEXT]: core migration — **cite numerical studies of migration distributions** (not just a quoted percentage), e.g. protostellar drift analyses; if none exists for the NN statistic specifically, say so.
- **G11** [TEXT]: **reorder equations** so assumptions are defined before the equation appears (several theoretical equations currently precede their definitions).
- **G12** [TEXT]: add a **concise simulation-grid summary table near the start of Section 4** (Appendix B has the full table; a compact orientation table up front is what Referee 1 asks for).
- **G13. Length (Referee 1 presentation)** [TEXT]: **cut ~15–20% of the discussion.** Each of {sub-Jeans spacing, width caveats, distance revisions, T1 uncertainty} is currently explained multiple times; **explain each once in detail**, remove repeats from Abstract↔Conclusions and within §5. Removing duplicated caveats also satisfies Referee 1's "remove several repeated caveats appearing in both Abstract and Conclusions."
- **G14. Key pipeline figure (Referee 1 Figures)** [TEXT]: v53's Fig. 1 already shows the raw→pipeline→NN pipeline. **Extend it (or add a companion panel) to carry the logic all the way through:** Observed → pipeline → NN spacing → simulation prediction → T1 transformation → comparison. Referee 1 wants the *whole* logic (including the simulation/T1 arm) in one figure; the population-weighted figure (§A) can serve as the right-hand half.
- **G15. Conclusions structured Established / Likely / Speculative (Referee 1 Conclusions)** [TEXT]: restructure the Conclusions bullets under three explicit headers, per Referee 1's list:
  - **Established:** Gaia revisions increase physical spacings; NN spacing is sub-Jeans; pairwise statistics measure L/3, not fragmentation; longitudinal simulations approach observed spacing *after T1 calibration*; present perpendicular simulations do not (and are resolution-limited).
  - **Likely:** hierarchical fibre fragmentation contributes.
  - **Speculative:** internal field geometry explains the discrepancy; higher-resolution ambipolar runs may remove the tension.

## Referee 1 technical wording pass [TEXT]
- Replace **"prove"/"demonstrate" → "indicate"** for simulation interpretation; **"show" → "suggest"** for unresolved mechanisms.
- **Avoid statistical-significance phrasing where no formal CI is quoted.**
- **Label every quoted uncertainty** as statistical / systematic / sensitivity-derived.
- Remove repeated caveats duplicated between Abstract and Conclusions (merges with G13).

---

# H. FIGURE DEFECTS STILL PRESENT IN v53 [COMPUTE-DONE / TEXT]

Two figure defects flagged previously are **still in v53** and must be fixed:
- **H1. Figure A1 internal inconsistency:** the plot annotation reads **"Mean ratio: 0.915 (256³ frags 8.5% earlier)"** while Eq. (A1) and the caption say **0.928 ± 0.016**. These must agree. Recompute the mean t_frag(256³)/t_frag(128³) from the six matched points and set the figure annotation, Eq. (A1), and caption to the *same* value (one is a 6-point mean, the other likely a subset/median). [GLENN/DATA to pick the correct value from the six pairs; if the six pairs are in the released data, ASTRA-PA can compute it.]
- **H2. Figure A2 literal `\n`:** the x-axis tick label reads **"γ = 1.0\n(isothermal)"** with an un-rendered literal `\n`. Regenerate with a real newline (or "γ = 1.0 (isothermal)" on one line). **Grep the whole figure pipeline** for `\\n` in label/title strings and fix all instances (this bug has recurred across versions).

---

# I. WHAT ASTRA-PA PROVIDES (in `support/`) AND WHAT IS PENDING

**[COMPUTE-DONE] — supplied now:**
- `population_weighted_synthesis.json` + `figures/population_weighted.png` — §A (the decisive new number: weighted 1.0–1.5 vs observed 1.9–2.5).
- `T1_geometry_breakdown.json` — §C (T1 calibration is longitudinal-only, β=0.5/1.0/2.0).

**[COMPUTE-RUNNING] — cluster, ETA ~1 day:**
- Higher-resolution perpendicular ambipolar rerun (512×128×128, N_J ≳ 4) — §B / Referee 2 #2(a). Will report whether the perpendicular λ/W is resolution-robust or shifts (and in which direction). Delivered as an addendum; the v54 text should adopt the downgrade now and can be strengthened when this lands.

**[COMPUTE-can-do-on-request]:**
- Re-fit t_frag(f) exponent with seed scatter propagated (F1) — needs the main-grid results JSON.
- Clustered (non-periodic) injection–recovery test (F6/G8) — needs the injection code.
- Fig. A1 mean-ratio recomputation (H1) — needs the six 128³/256³ t_frag pairs.

**[GLENN-OBS] — needs HGBS maps/catalogues/DisPerSE code:**
- FilFinder-vs-DisPerSE cross-check for the other three regions (F2).
- Manual-spur-editing systematic quantification (F3).
- Gaussian-vs-Plummer per-region width table + Taurus explanation (G5).

**No fatal flaws, no large new campaign required.** The revision is: (1) add the population-weighted number and make the negative result the headline; (2) downgrade the perpendicular framing to "preliminary/resolution-limited" and mark T1 as longitudinal-calibrated; (3) mark the simulation match "provisional on T1"; (4) soften §6 to the single-realisation claim; (5) fix the two figure defects and do the wording/length pass. Items (1)–(3) are the ones both referees will check first.
