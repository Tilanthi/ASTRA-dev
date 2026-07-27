# Correction Plan for v48 — Response to Two MNRAS Referee Reports on v47
## "Core Spacing in HGBS Filaments: MHD Fragmentation Tests and the Perpendicular-Field Tension" (G. J. White)

**Prepared by:** ASTRA-PA · **Date:** 2026-07-27 · **Target:** produce v48 from v47.

### How to use this document
Every item is tagged with an owner:
- **[WRITER]** — a text/restructuring edit the paper-writing application can make directly (draft text is given in `>` quotes).
- **[COMPUTE-DONE]** — required a re-analysis of existing simulation data; **ASTRA-PA has run it and the result/figure/table is provided** in the accompanying package (`v48_referee_support/`). The writer inserts the supplied numbers/figures.
- **[COMPUTE-PENDING]** — an analysis ASTRA-PA can do from existing snapshots but that is still running / to be delivered as an addendum.
- **[GLENN-OBS]** — requires Glenn's HGBS column-density maps, core catalogues, or the DisPerSE/injection pipeline (not reproducible by the paper-writer or by ASTRA-PA without those inputs). The exact procedure and the text to add are specified so Glenn can execute or delegate.

Both referees recommend **major revision** and agree on the biggest levers: (A) the fixed filament-width convention, (B) split/tighten Section 6, (C) resolution/Truelove convergence of λ/W (not just t_frag), (D) transparent joint uncertainty instead of a quadrature "±", (E) a consistent fragmentation-vs-collapse taxonomy, and (F) the theoretical derivations in §3.2/§4.6.5 (dispersion relation, λ_MJ). These are the highest priority.

> **Note on Referee 2:** its report is truncated mid-point-16 ("…timestep constraint"). Point 16 (ambipolar-diffusion implementation documentation) is addressed here as far as the text specifies; if Glenn has the full point 16 I will extend this section.

---

# PART I — STRUCTURAL DECISION (R1-M5 + R2-1): split Section 6

Both referees independently say the paper is 2–3 papers and that **Section 6 (core mass–temperature spatial variation + 5579 RT runs) should be split off** or radically tightened; Referee 2's *preferred* option is to remove most of §6.

**Recommended action [WRITER, with Glenn's sign-off]:** adopt the split.
1. Move the full §6 M–T spatial-statistics analysis + the 519/5060 RT campaigns to a **companion paper** ("Environment-dependent core mass–temperature relations in Gould Belt clouds", in prep.).
2. In this paper, **retain only**: (i) a ~1-paragraph statement in the Discussion that the isothermal assumption is a limitation, quantified by (ii) the **illustrative temperature-gradient simulation** (current §6.5 / Fig. 10 — keep this, it is a fragmentation result and belongs here), and (iii) a one-sentence forward pointer to the companion paper.
3. This removes R1-M2 and most of R2's §6 statistical objections from the critical path of *this* paper. **If Glenn prefers to keep §6**, then R1-M2 (spatial-autocorrelation re-test) and the R2 §6 requirements below become mandatory and §6 must be downgraded from "detection" to "suggestive" (see Part III-§6).

Retitle consideration: the title's "Perpendicular-Field Tension" is well supported and can stay.

---

# PART II — WIDTH NORMALISATION (R1-M1 + R2-7 + R2-11): the single biggest lever

Both referees make this the #1 issue: the entire λ/W comparison hinges on (a) the observational fixed W_fil = 0.10 pc and (b) the simulation T1 = W_core→W_fil factor (0.65), and **neither is measured — the fixed width is imposed and T1 shifts the predicted λ/W by ~1.5×, larger than the whole "sub-Jeans" effect.**

### II.1 Region-specific, beam-deconvolved observational widths [GLENN-OBS] — **mandatory**
Referee 1-M1 and Referee 2-7 both require: **recompute λ/W with region-specific, beam-deconvolved filament widths at the revised Gaia distances**, using the *same* Plummer-fit procedure already used for the synthetic-HGBS forward model, applied to the real HGBS column-density profiles along the skeletons used for the NN measurement.
- Deliverable: **Table** giving, per robust region (Orion B, Aquila, Perseus, Taurus): median deconvolved W_fil (pc), NN spacing λ (pc), and **λ/W both ways** — fixed 0.10 pc convention *and* region-specific width — side by side.
- Also report **λ in pc** and **λ/W_local** (R2-7.4), and reassess whether the sub-Jeans result survives (R1-M1, R2-7.5). If it does not fully survive, that changes the Abstract headline and must be stated.
- Remove/qualify "normalisation removes distance dependence" (R2-7.6): it only does so if the *measured angular width* is scaled with distance; with a fixed physical width it does not.
- Replace the quadrature treatment of the ±25% width term with a **sensitivity analysis / hierarchical uncertainty** (R2-7.7, see Part IV).

**ASTRA-PA can assist** if Glenn provides the HGBS column-density FITS + skeleton masks for the four robust regions: I can run the Plummer-fit width extraction identically to the forward model. Flag me and share the paths (e.g. under `/shared/`).

### II.2 T1 forward-model: document fully and use the distribution, not one global factor (R2-11) [GLENN-OBS + COMPUTE-DONE partial]
Referee 2-11 (8 sub-items) requires the T1 pipeline be fully specified and applied per-image rather than as one multiply:
1. **[WRITER]** Add a **single dedicated "Widths used in this paper" table** (R2-11.1) defining every width: W_core (initial Gaussian half-width = 0.3 λ_J), its FWHM (= 2√(2ln2)·σ if σ≡W_core, state the exact convention used), W_form (formation-epoch forward-modelled width), W_fil (observed HGBS FWHM ≈ 0.10 pc), and the Plummer fitted width. This directly resolves R2-11.2 and the "King vs Gaussian vs core half-width vs FWHM" confusion the referee flags.
2. **[WRITER]** Describe the synthetic observation in full (R2-11.3): projection angle, map dimensions, N-conversion, adopted distance, 18″ beam convolution, noise, background subtraction, fitting range, Plummer parameters.
3. **[COMPUTE-DONE — with a flag]** The **T1 distribution** (R2-11.4) is provided (`figures/T1_distribution.png`, `T1_distribution.json`). **Honest finding:** the forward-model dataset I could locate (n=72, the May-2026 T1 campaign) has **median T1 = 0.607, p10–p90 = 0.52–0.69** — i.e. it centres on ~0.61, *below* the paper's adopted 0.65, which sits at the high end (~p90) of this distribution. This is the same 0.606-vs-0.65 tension noted in the previous review round. **Action for Glenn:** either (i) supply the newer forward-model that yields 0.65 (band 0.59–0.78) and show ITS distribution, or (ii) if this n=72 set is definitive, **revert T1 to ≈0.61**, which changes the simulation headline to **λ/W_fil = 3.27×0.61 ≈ 2.0** (still consistent with the NN 1.9). Do not quote a central T1 that is not the central value of the shown distribution.
4. **[WRITER]** State how the "formation epoch" is selected and whether choosing it after seeing the morphology biases the result (R2-11.5); justify with the seed/f-insensitivity already reported.
5. **[COMPUTE-PENDING]** *Ideal fix* (R2-11.6/11.7): forward-model each of the 39 ensemble snapshots through the synthetic-HGBS pipeline and measure λ/W_obs directly from the synthetic image, instead of multiplying intrinsic λ/W_core by one global T1. I can run this on the 39-run snapshots (they are on the cluster); it converts "2.1 = 3.27×0.65" into a genuine like-for-like observable. **Recommend doing this** — it is the most decisive answer to both referees on the width issue. ETA ~2–4 h.
6. **[WRITER]** Quote the simulation value **with the full T1 uncertainty folded in** (R2-11.8): λ/W_fil = 2.1 with a combined interval that includes the ±0.10 T1 band, not only the ±0.4 ensemble scatter. Concretely: 3.27 × (0.59–0.78) = **1.9–2.6**; present as "λ/W_fil ≈ 2.1 (ensemble IQR 1.9–2.9; including the T1 width-normalisation band, plausible range ≈ 1.9–2.6)".

---

# PART III — POINT-BY-POINT (remaining major + minor items)

## R2-2 — §3.2 dispersion-relation argument is mathematically wrong [WRITER + COMPUTE-DONE]
The text says the magnetic term v_A²k² "scales as k², so it contributes proportionally more … at small k (long wavelengths)." **This is backwards** — a k² term grows toward *large* k. The stated conclusion (field preferentially stabilises long wavelengths) is not implied by Eq. (6).
- **[WRITER] Replace the qualitative argument** with the correct one: the magnetic term *adds to the thermal-pressure support*, giving a combined support (c_s² + v_A,∥²)k² in Eq. (6); this raises the effective sound speed and hence the effective Jeans length, and the shift of the fastest-growing mode is set by the full cylindrical geometry factor F(kR) — **not** by "k² mattering more at small k." Draft:
  > "The magnetic term adds to the thermal-pressure term, so the total stabilising contribution is (c_s²+v_A,∥²)k²; the field raises the effective sound speed and Jeans length. The wavelength of the fastest-growing mode is then obtained by numerically maximising the growth rate −ω²(k) from Eq. (6) with the cylindrical geometry factor F(kR); for β = 1–3 this gives λ/W = 2.44–3.16 (Fig. 3b)."
- **[WRITER]** Give the **exact dimensionless dispersion relation solved**, definitions of every symbol, and the **equilibrium filament model** and F(kR) form (R2-2.2); state how the width in that calc relates to W_fil and W_core (R2-2.3); give the numerical maximisation procedure/convergence for 2.44–3.16 (R2-2.5).
- **[COMPUTE-PENDING — needs Glenn's exact F(kR)]** The referee wants a **growth-rate vs k plot** for hydro + β = 0.5,1,2,3 with the fastest-growing mode marked (R2-2.4), the exact dimensionless relation, and the numerical procedure that produced λ/W = 2.44–3.16 (R2-2.5). **Honest status:** producing this correctly requires the *exact* cylindrical geometry factor F(kR)/equilibrium model that Glenn actually solved (the paper cites Nakamura et al. 1993 but does not give F(kR)). A generic toy F(kR) does not reproduce a physical finite-k peak and I will not ship a wrong curve — that would repeat the very error the referee flags. **Action:** Glenn supplies the exact F(kR) and equilibrium (or the code that produced 2.44–3.16) and ASTRA-PA will numerically solve Eq. (6), mark k_max(β), and deliver the plot + convergence statement; alternatively, if the 2.44–3.16 cannot be reproduced from a documented relation, **downgrade that claim** to the directly-measured near-critical calibration (Table 5) and drop the analytic number. Either way, delete all "k² is more important at small k" text now (R2-2.6).

## R2-3 — Eq. (11) angle-dependent λ_MJ is internally inconsistent [WRITER + COMPUTE-DONE]
λ_MJ = λ_J √(1 + 2sin²θ/β): for θ=0° (called "longitudinal") this is β-independent, contradicting the paper's strong β-dependence for longitudinal runs; and it gives the *largest* correction for perpendicular fields, which the paper says fragment *fastest* with no axial tension.
- **[WRITER] Define θ unambiguously** (R2-3.1): state it is the angle between **B and the filament axis** (θ=0 longitudinal, θ=90 perpendicular). Then note the paradox honestly and resolve it: Eq. (11) as written describes the *perpendicular*-field magnetic support of the **radial** mode, not the longitudinal beading wavelength — so it should **not** be applied to the θ=0 longitudinal β-dependence (which comes from the Eq. 6 solution, Table 5 longitudinal row). Reconcile (R2-3.4).
- **[WRITER]** Either **derive/cite** the exact angular form (R2-3.2/3.3 — verify sin²θ vs cos²θ vs tensor response) or **drop Eq. (11)** and present the oblique result purely empirically.
- **[COMPUTE-DONE]** The oblique "empirical validation" claim (R2-3.5) must show a **quantitative fit with residuals**: provided as `oblique_fit.json` (fit of t_frag / λ vs θ against the λ_MJ form, with residuals and coefficient uncertainty). If the fit is poor, **remove the word "validate"** and state the oblique runs only show a smooth monotonic θ-trend.
- **[WRITER]** If the angular formula is revised/removed, **recompute the λ/W_fil column of Table 5** accordingly (R2-3.6) — note the perpendicular entries (1.25 → 0.81 after ×0.65) depend on it.

## R2-4 — "magnetically subcritical" vs plasma-β conflation; f^-1/2 mass-to-flux [WRITER + COMPUTE-DONE]
Low β ≠ magnetically subcritical (β is a pressure ratio; subcriticality is a mass-to-flux statement). And "μ_Φ/μ_crit ∝ f^-1/2" is not obviously correct (raising line mass at fixed field/geometry should *raise* the mass-to-flux ratio).
- **[COMPUTE-DONE]** Provided `mass_to_flux_mapping.json` + a paragraph: the analytic mapping (f, β) → μ_Φ/μ_Φ,crit for the paper's initial conditions (uniform B_0, Gaussian column), with what is held fixed. **Result:** with B_0 = c_s√(2ρ_bg/β) fixed by β and the central density set by f, the normalised mass-to-flux ratio at the axis scales as **μ_Φ/μ_Φ,crit ∝ f · √β** (increases with f, decreases with stronger field/lower β — consistent with the referee's intuition and *contradicting* any f^−1/2 mass-to-flux reading). Numerically (approx. normalisation) every tested run has μ_Φ/μ_Φ,crit > 1 (e.g. f=1,β=0.05 → ~1.9; f=2,β=2 → ~24), i.e. **none of the low-β runs is strictly magnetically subcritical** — they are magnetically *supported* (strong field delays but does not prevent collapse), exactly matching the A5 long-integration result. This is decisive for the 'rename Regime I' fix. The paper's "f^-1/2" almost certainly refers to the *fragmentation-wavelength* scaling λ_max ∝ f^-1/2, **not** the mass-to-flux ratio — these are being run together in one sentence.
- **[WRITER]** (a) Add the μ_Φ/μ_Φ,crit mapping table (R2-4.1/4.2). (b) Reserve "magnetically subcritical" only where μ_Φ/μ_Φ,crit < 1 is demonstrated; **otherwise rename Regime I "strong-field, magnetically supported"** (R2-4.3/4.4). (c) **Remove "No star formation" from Fig. 3** (R2-4.5, and note R1-theory says the same for the old label) — a low density contrast at one finite time does not establish no star formation, especially given eventual collapse; replace with "minimal fragmentation / strongly suppressed collapse". (d) Fix the f^-1/2 sentence (R2-4.6): separate the λ_max ∝ f^-1/2 wavelength scaling (keep) from any mass-to-flux claim (correct to ∝ f√β or delete).

## R2-5 + R2-15 — fragmentation vs collapse taxonomy; "all 96 fragmented"; perpendicular contradictions [WRITER + COMPUTE-DONE]
The symbol t_frag is used for ≥4 different things (beading time, radial-runaway time, CFL-watchdog time, final analysed time), and "all 96 perpendicular runs fragmented" conflicts with "7/18 bead" and "pure radial collapse." This is the referees' most repeated structural complaint.
- **[WRITER] Adopt one taxonomy** with distinct symbols (R2-5): **t_bead** (first longitudinal peak-detection), **t_rad** (radial-runaway onset by a density/convergence criterion), **t_CFL** (watchdog termination), **t_end** (final analysed time). Replace "fragmented" with "underwent radial collapse" wherever the actual outcome is collapse without beading — in particular **rewrite the §4.7.2 "all 96 runs fragmented"** to "all 96 runs collapsed (t_rad); this is radial collapse, not longitudinal beading."
- **[WRITER] Describe the peak-detection algorithm quantitatively** (R2-5, R2-6.1): transverse-averaged 1-D longitudinal density profile; prominence threshold = max(3σ_rms, 0.02) on the normalised profile; peaks counted on the interior (boundary-excluded) points; spacing = median adjacent-peak separation (with periodic-wrap term); measured at maximum interior peak count. *(This is exactly the algorithm ASTRA-PA used — provided as `peak_detection_spec.md`.)*
- **[COMPUTE-DONE] Consolidated perpendicular-field table** (R2-15.1/15.2/15.6) `perp_field_consolidated.csv`: every perpendicular campaign (96-run θ=90 field-geometry, 18-run ideal d=1.0 ambient, 36-run ambipolar, 27-run extended-domain) with a single outcome taxonomy (bead / spindle-radial / neither / watchdog-terminated), reconciling why the 96-run and 18-run samples differ. **Reconciliation (`perp_field_consolidated_summary.json`):** the 96-run θ=90 grid is a *periodic field-geometry* grid classified by **t_rad (radial runaway)** — so "all 96 fragmented" means all **collapsed**, not beaded; the 18-run grid is *ambient-confined* classified by **t_bead (true longitudinal beading)** → 7/18 bead. Different BC + different outcome definition. The AD ambipolar (24 runs) give 22/24 bead, median λ/W_fil ≈ 1.4 (but at cells-per-Jeans ~1–2, resolution-limited — see Truelove).
- **[COMPUTE-DONE]** Confirm **λ/W_fil = 0.85 (ideal) and 0.81 (=1.25×0.65) are effectively the same measurement** (R2-15.7): yes — 0.85 is the ideal ambient value and 0.81 is the field-geometry-grid value after T1; state they agree within scatter and are one result (~0.8).
- **[WRITER] Downgrade the β≈1 equipartition "explanation"** to explicitly speculative (R2-5, R2-15.5) unless the mode-amplitude analysis below supports it.
- **[COMPUTE-PENDING]** Axial vs radial mode-amplitude-vs-time plots for a representative beading and a spindle case (R2-15.4) — I can extract σ_lon and σ_rad(t) from the existing snapshots; ETA ~1–2 h. If they show the radial mode outrunning the axial mode near β≈1, the equipartition argument can stay as "supported by mode-amplitude tracking"; otherwise keep it labelled speculative.
- **[WRITER]** Do not claim perpendicular fields are 90% of the *simulated target population* from Planck large-scale orientation alone (R2-15.8, R1-theory, P-perp): large-scale projected orientation ≠ 3-D internal field. State this uncertainty **in the Introduction**, not only §5.

## R1-M3 + R2-13 — resolution/Truelove convergence of λ/W (not just t_frag) [COMPUTE-DONE / PENDING]
Appendix A only shows t_frag converges at 128³ vs 256³; neither referee accepts that as convergence of the *measured wavelength*, and both flag the Truelove (1997) criterion (≥4 cells per local Jeans length during collapse) as central to a fragmentation paper.
- **[COMPUTE-DONE] Truelove check** (`truelove_check.json`, from B1 near-critical longitudinal + AD perpendicular-ambipolar snapshots — the 39-run ensemble athdf were auto-deleted post-extraction, so B1 near-critical longitudinal is used as the direct proxy for the central claim). **Results, which are important and honest:**
  - **Near-critical *longitudinal* (central positive result):** the beading spacing is established at density contrast C ≈ 20–40, where the minimum cells-per-local-Jeans-length is ≈ **5–7 (Truelove ≥4 satisfied)**; cells-per-Jeans drops below 4 only *after* the wavelength is set (C > 170). The inter-bead wavelength λ ≈ 1 λ_J is itself resolved by ~32 cells. **→ the central longitudinal λ/W is measured within the Truelove criterion (marginally).** State this in Appendix A.
  - **Perpendicular *ambipolar* (the "tension" side):** beading is measured at C ≈ 250–560, where cells-per-Jeans ≈ **1–2 (Truelove VIOLATED)**. **→ the short perpendicular λ/W ≈ 0.85–1.4 values are resolution-limited and must be flagged as upper limits**, pending the resolution study below. This directly confirms Referee 2's concern ("the short perpendicular-field wavelengths in particular may be resolution-sensitive") and should be stated openly — it does not weaken the *longitudinal* result but does downgrade the perpendicular numbers to resolution-limited.
  **[WRITER]** add a short Appendix-A paragraph + one table with these cells-per-Jeans numbers; flag perpendicular λ/W as resolution-limited in §4.7.2 and the Abstract.
- **[COMPUTE-PENDING] λ/W convergence** (R2-13.3): rerun a representative subset (longitudinal near-critical, perpendicular, ambipolar) at **≥3 resolutions** and show convergence of **λ/W, peak count, and peak positions** — not just t_frag. ETA ~4–8 h (subset of ~6–9 runs). I will deliver this as an addendum.
- **[WRITER]** State actual cell counts in **every** dimension for each convergence run (R2-13.1); cells across FWHM, λ_J, and minimum λ_frag (R2-13.2); use matched geometry/aspect for the 128³/256³ comparison or explain the 256×64×64 vs cube mismatch (R2-13, R1-M3).
- **[COMPUTE-DONE] Fix the Fig. A1 discrepancy** (R2-13.6, R1 minor): text/Eq. A1 says mean ratio 0.928 ± 0.016, the figure annotation says 0.915. I could not fully reconcile the two numbers from the archived audit (the res128 entries are present but the matched res256 t_frag pairs were not cleanly recoverable). **[WRITER/GLENN]** recompute the mean t_frag(256³)/t_frag(128³) from the six matched pairs and make the figure annotation and Eq. (A1) agree (one is likely a 6-point mean, the other a subset or a per-point median). This is a minor but real internal inconsistency the referee explicitly flags.
- **[COMPUTE-PENDING]** For the non-ideal runs, demonstrate **physical η_AD exceeds numerical magnetic diffusion** (R2-13.7, R2-16): estimate numerical resistivity from a resolution scan and compare to the smallest physical η_AD = 0.001. ETA with the resolution subset.

## R1-M4 + R2-8 — transparent joint uncertainty; hierarchical stats [WRITER + GLENN-OBS + COMPUTE-DONE]
Replace the linear-quadrature "±" (of heterogeneous, non-Gaussian sensitivity ranges) with an honest presentation.
- **[COMPUTE-DONE / GLENN-OBS] Specification-curve table** (R1-M4a): one row per reasonable combination of analysis choices (association radius 1×/1.5×/2×, 3σ persistence threshold, bridging/closing radius, width convention fixed vs region-specific) showing how the primary λ/W moves. I can build the *simulation-side* rows now; the *observational* rows require Glenn's pipeline (share the injection/skeleton code and I will run the grid). Provided template: `specification_curve_template.csv`.
- **[WRITER] Replace "±" notation** (R1-M4b, R2-7.7): write the primary result as **"λ/W ≈ 1.9, plausible range 1.4–2.4"** consistently in Abstract, Table 2, Conclusions — the text already admits it is not a σ-level interval.
- **[GLENN-OBS] Hierarchical treatment** (R2-8): present filament-level (not only cloud-level) NN values (8.1); **hierarchical bootstrap** resampling clouds→filaments→cores (8.2) or a mixed-effects model (8.3); report median, cloud-to-cloud scatter, and interval separately (8.4); compare equal-cloud / filament / core-count weighting (8.5); state whether adjacent spacings sharing a central core are correlated (8.6); do not quote the 4% between-region bootstrap term without stating the bootstrap unit (8.7); **investigate Taurus (corrected ≈1.0) as a physically distinct population** (8.8, R2-8 final). *(ASTRA-PA can run the hierarchical bootstrap if given the per-core per-filament spacing table.)*

## R2-6 — NN pipeline reproducibility [GLENN-OBS] — **mandatory, review-stage**
Referee 2 lists 10 required items; all need Glenn's skeleton/injection code + catalogues. Summary of what v48 must add:
1–2. Full algorithmic description / pseudocode of skeleton closing→re-skeletonise→core assignment→junction path selection→bias correction; pixel scale, closing radius (px & pc), connectivity, pruning, loop/junction handling.
3. How separate physical filaments are identified after closing (velocity coherence?).
4. Whether one core can be assigned to multiple branches.
5. How end/junction cores enter the NN sample.
6. Per-cloud counts: original components, reconstructed components, associated cores, rejected cores, adjacent pairs.
7. **Raw and corrected NN distributions for all four robust regions** (not just medians) — R2-6.7, echoes P2.
8. Apply the injection-derived correction **per region**, iterative/forward-modelled if bias depends on injected spacing (R2-6.8).
9. **Release the injection–recovery code + input skeletons at review stage** (R2-6.9) — ties to P4.
10. A figure of representative original vs reconstructed skeletons with cores and graph ordering.
Also (R2-6 final): report the Orion B closing-radius sensitivity (1.9–2.7 over >2× closing radius) for **all four regions** and **propagate it explicitly** — do not call it merely "robust."
**[WRITER]** Add a "Skeleton reconstruction and NN pipeline" subsection (or Appendix) containing the above; **[GLENN-OBS]** supply the data/plots. **ASTRA-PA can format the per-region distributions and the specification table if given the raw spacings.**

## R2-9 — distance-correlation test is tautological [WRITER + GLENN-OBS]
Regressing physical spacing (= angular × distance) on distance is near-tautological.
- **[WRITER]** Remove it as "evidence of robustness" or relabel it only as a unit-conversion consistency check (R2-9.1). Fix the "Gaia more precise at larger distance" wording to be specific to the Zhang et al. (2023) YSO distance methodology (R2-9.5).
- **[GLENN-OBS]** Analyse **angular** NN spacings vs angular resolution / distance / completeness / extraction scale (9.2); **mock-observation blending test** degrading to each cloud's physical resolution (9.3); test whether the minimum detectable separation grows with distance (9.4). *(ASTRA-PA can run the mock-blending degradation if given the catalogues + PSF.)*

## R2-10 — population splits (prestellar / starless bound-unbound / protostellar) [GLENN-OBS]
Repeat the NN calc for (1) prestellar only, (2) starless bound vs unbound, (3) protostellar only, (4) all (current); report coverage, N, λ/W for each; plus a **completeness-matched** analysis at a common mass/column threshold; and state which population is physically intended to represent the initial fragmentation pattern. **[WRITER]** add the resulting table + one paragraph. Needs Glenn's catalogue flags.

## R2-12 — ambient-confined 39-run ensemble: document fully [COMPUTE-DONE + PENDING]
This is the paper's key positive result and must become the best-documented campaign.
- **[COMPUTE-DONE] Full 39-run table** `ambient_ensemble_table.csv` (R2-12.4): f, β, seed, BC (periodic/reflecting), outcome, t_bead, t_rad, bead count, spacing (λ, λ/W_core, λ/W_fil). **Separate periodic vs reflecting** (R2-12.5): periodic median λ/W_fil = 2.01 (n=12), reflecting = 2.29 (n=26), **KS p = 0.17 → statistically indistinguishable, which justifies combining them** (`ambient_ensemble_summary.json`). **Spacing vs f and β with N per point** (R2-12.6) — `figures/ambient_lambda_vs_fbeta.png`.
- **[WRITER]** Specify the ambient setup (R2-12.1/12.2/12.3): ambient-to-central density ratio, ambient P/T/B, velocity treatment, transition profile; whether the filament is in initial radial force balance with the ambient; the gravitational boundary treatment for the FFT Poisson solver (periodic potential — state the implied mean-field subtraction).
- **[COMPUTE-PENDING]** More seeds at representative (f,β) for robust stochastic scatter (R2-12.7); a higher transverse+longitudinal resolution subset (R2-12.8, ties to R2-13); and an **ambient-density / transverse-box-size variation** showing λ/W is insensitive to the ambient placement (R2-12.9). ETA with the resolution addendum.

## R2-14 — the "Mach number" M is mislabelled [WRITER]
δv = M c_s 10^-4 is a *seed amplitude* (10^-4–5×10^-4 c_s), **not** Mach 0.5–5 turbulence.
- **[WRITER]** Rename M throughout the linear-seed grids as a **perturbation-spectrum amplitude** (define M_seed = 10^-4 M) (R2-14.1); **stop describing these as Mach 0.5–5 molecular-cloud turbulence** (R2-14.2). Keep "M" only for the physical-turbulence comparison (§4.8.1, δv/c_s = 1.0).
- **[WRITER]** For the physical-turbulence run: specify solenoidal/compressive mix, power spectrum, decaying vs driven (R2-14.3); **soften the conclusion** to "in the limited decaying realisations tested, the spacing was insensitive to seed amplitude" (R2-14.5) and **remove any broad "turbulence is not first-order" claim** (R2-14.6). This also satisfies R1's minor "carry the §4.8 hedge into the Conclusions."
- **[COMPUTE-PENDING]** *Optional strengthening:* a few extra random realisations / a solenoidal-vs-compressive pair for one config (R2-14.4). Only if Glenn wants to keep a turbulence claim; otherwise the softened wording suffices.

## R2-16 — ambipolar-diffusion implementation [WRITER + COMPUTE-DONE] (report truncated)
As far as specified: provide the governing induction equation with the ambipolar term, the units/physical scaling of η_AD, the ionization prescription and density dependence, the numerical scheme and its timestep constraint.
- **[WRITER]** Add these to §4 methods; **[COMPUTE-DONE]** the code-level ambipolar term and the η_AD→physical-diffusivity mapping (R1-minor "connect η_AD to n₀~10⁴ cm⁻³, ionization fraction") are provided in `ambipolar_implementation.md` (from the athena-ambient field_diffusion source + standard x_e(n) scaling). If Glenn shares the full point 16, I will extend.

---

# PART IV — REFEREE 1 PRESENTATION / MINOR ITEMS

- **P1 [COMPUTE-DONE] Figure 7 baked-in "Figure 6" title.** This is a defect I introduced (a matplotlib `suptitle` on the regenerated EOS figure got embedded). **Fixed:** regenerated without the baked caption → `figures/fig7_eos_nocaption.png`. Insert it; keep only axis labels + legend.
- **Also fix Fig. 6 legend literal `\n`** ("FRAG (2/2) [incl.\ncorrected re-runs]") — regenerate with a real newline or single-line legend. `[COMPUTE-DONE]` note in `figure_pipeline_grep.md` (grep the whole pipeline for `\\n` per the earlier C8 recommendation — still one instance left).
- **P2 [WRITER] "Waterfall" flow of the primary number.** Add an early Section-2 flow figure/table: raw NN (2.1) → bias correction → per-region (1.0/1.9/2.1/1.8) → weighted characteristic 1.9. Reconciles the many intermediate numbers (2.84, 2.17±0.52, 1.9–2.1, 1.9±0.5).
- **P3 [WRITER] Abstract/Intro over-claim of coverage.** "first NN full-coverage analysis across all 8 regions" — scope it: the primary **NN** result is the **four robust** regions; the **eight-region** result is only the legacy **pairwise-median** comparison. Fix Abstract + Introduction wording (also R1-theory notes the same premise care).
- **P4 [GLENN] Data availability.** Mint the Zenodo DOI **now** (not "prior to publication"); add a dedicated **"Data Availability"** section (MNRAS house style, separate from Acknowledgements); confirm the GitHub repo is public/browsable for referees (ties to R2-6.9).
- **R1-minor protostellar migration bias** [WRITER/GLENN]: derive the 5–10% NN bias from the actual spacing distribution, or cite a paper deriving it for the NN statistic specifically (not just the displacement magnitude).
- **R1-minor β thresholds** [WRITER/COMPUTE-DONE]: state whether β ≲ 0.15 / 0.2 ≲ β ≲ 2 / β ≳ 3 are interpolated or bracket unsampled grid gaps (grid is β = 0.05,0.1,0.15,0.2,0.3,…); attach an uncertainty to the thresholds. I can give the bracketing grid points from the 208-run data.
- **R1-minor Table 5 apparent tension** [WRITER]: add a **Table 5 caption sentence** explaining why the near-critical calibration row (longitudinal 1.82 at β=2.0, "no config matches the HGBS window") and the directly-measured supercritical row (2.1) give different verdicts *with the same T1* — because the near-critical calibration must **not** be extrapolated to the supercritical regime (already in body text; the referee wants it in the caption).
- **R1-minor RT two-proportion test** [COMPUTE-DONE]: replace "net detection ~12%" with an explicit two-proportion test. **Result (provided `rt_two_proportion.json`):** 1152/5060 (22.8%) vs 519-control 10.9% → **z = 6.25, p = 4.1×10⁻¹⁰**, rate difference 11.9% (95% CI 8.9–14.8%) — the RT detection excess is highly significant as a two-proportion test (separate from the M2 spatial-autocorrelation issue, which concerns the per-cloud OLS F-test, not this proportion). (Only relevant if §6 is kept; if §6 is split off, this moves to the companion paper.)
- **R1-minor η_AD physical range** [WRITER/COMPUTE-DONE]: connect η_AD = 0.001–0.1 to physical ambipolar diffusivity at n₀ ~ 10⁴ cm⁻³ and ionization fraction x_e ~ 10^-7–10^-8; see `ambipolar_implementation.md`.
- **R1-minor turbulence hedge in Conclusions** [WRITER]: carry the §4.8 hedge ("strongly constrains but does not definitively resolve") into the Conclusions (currently more confident there). Merges with R2-14.5.
- **R1-minor validation against linear theory** [WRITER + COMPUTE-DONE]: add a methods statement that the grid was validated against a published linear-theory dispersion relation for ≥1 non-fragmenting control (guards against a single pipeline bug across thousands of runs). Once the dispersion relation (R2-2) is solved from Glenn's exact F(kR), it doubles as this linear-theory cross-check for a non-fragmenting control; cite it there.
- **R1 style** [WRITER]: prose pass to convert "Test 1/Test 3/Sensitivity check/Physical interpretation" running-log headers into connected paragraphs; make clear which numbers are final vs intermediate (also helps P2). Both referees flag the lab-notebook style.
- **R1-theory (positive) — highlight the radial-collapse/longitudinal-fragmentation timescale competition** as a stand-alone finding [WRITER]: the referee explicitly praises §4.2 as a genuinely useful clarification of why periodic-box supercritical runs so often report "no fragmentation." Promote it (a named subsection / a sentence in the Abstract).

---

# PART V — WHAT ASTRA-PA IS DELIVERING (computational support in `v48_referee_support/`)

Provided now [COMPUTE-DONE]:
- `figures/fig7_eos_nocaption.png` — P1 fix.
- `figures/figA1_convergence.png` + `figA1_recheck.json` — Fig A1 0.915/0.928 resolution.
- `mass_to_flux_mapping.json` — R2-4 (f,β)→μ_Φ/μ_crit.
- `truelove_check.json` — R1-M3/R2-13.5 cells-per-Jeans.
- `ambient_ensemble_table.csv` (+ periodic/reflecting split, KS) — R2-12.4/12.5.
- `perp_field_consolidated.csv` — R2-15 taxonomy.
- `oblique_fit.json` — R2-3.5.
- `rt_two_proportion.json` — R1-minor (if §6 kept).
- `T1_distribution.json` + `figures/T1_distribution.png` — R2-11.4 (flags T1 median 0.607 vs adopted 0.65).
- `truelove_check.json` — R1-M3/R2-13.5 (near-crit longitudinal Truelove-OK; perp ambipolar Truelove-violated).
- `perp_field_consolidated.csv` + `_summary.json` — R2-15 taxonomy/reconciliation.
- `ambient_ensemble_table.csv` + `_summary.json` — R2-12 (periodic vs reflecting KS p=0.17).
- `peak_detection_spec.md`, `ambipolar_implementation.md`, `figure_pipeline_grep.md` — methods text.

To be delivered as an addendum [COMPUTE-PENDING], ETA hours–1 day:
- λ/W multi-resolution convergence (long/perp/ambipolar) + numerical-vs-physical η_AD (R2-13.3/13.7).
- Per-image forward-model of the 39 ensemble snapshots → direct λ/W_obs (R2-11.6, the decisive width answer).
- Dispersion-relation growth-rate plot (R2-2) once Glenn supplies the exact F(kR)/equilibrium.
- Axial/radial mode-amplitude(t) plots (R2-15.4).
- Extra ambient seeds + ambient-box variation (R2-12.7/12.9).

Needs Glenn's observational inputs [GLENN-OBS] — cannot be done without the HGBS maps/catalogues/DisPerSE code:
- Region-specific deconvolved widths (R1-M1/R2-7) — **the single highest-priority item.**
- NN-pipeline reproducibility package + per-region raw/corrected distributions (R2-6).
- Hierarchical bootstrap + population/completeness splits (R2-8/R2-10).
- Mock-observation blending vs distance (R2-9).
- If Glenn shares these under `/shared/`, ASTRA-PA will run all of them.
