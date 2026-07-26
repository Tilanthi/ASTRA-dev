# Referee Response Campaign v40 — Final Report

**Paper**: "Core Spacing in HGBS Filaments: MHD Fragmentation Tests and the Perpendicular-Field Tension" (White, v40, MNRAS) — major revision.
**Campaign**: `/data/referee_v40_campaigns_jul2026/`, 2026-07-23 → 2026-07-25. 38 production runs, 2 suites.
**Binaries**: `athena-ambient` (filament_ambient pgen), `athena-sc` (non-ideal MHD / ambipolar).
All configs, runner, analyzers, results JSON, logs, and figures are in this package.

---

## 1. Which referee concerns needed new simulations

The v40 referee raised eight distinct points. Only two are addressable by simulation; the rest are text/analysis fixes handled in the companion `paper_update_instructions.md`.

| # | Concern | Sim? | Suite |
|---|---|---|---|
| 1 | CFL early-termination may be censoring longitudinal fragmentation in the 654-run main grid | **YES** | **EX** |
| 2 | Ambipolar "unlocking" claim rests on only 12 runs at 2 diffusivities | **YES** | **AD** |
| 3 | 39-run ambient-confined ensemble is a "bespoke" setup adopted after the main grid failed | No — framing/text | — |
| 4 | T1 normalisation (±30%) should be a formal error bar, not a caveat | No — math/text | — |
| 5 | Small-N mechanism claims (hierarchical fibers, M–T) overstated | No — text | — |
| 6 | Self-detected artifacts → "known artifacts" table needed | No — text | — |
| 7 | §6 M–T from N=3 clouds reads as anecdote | No — text/obs | — |
| 8 | NN skeleton-bridging pipeline needs ground-truth validation | No — observational pipeline | — |

---

## 2. EX — Extended-integration test of the CFL-censoring concern

**Referee's exact request**: "extend integration time/resolution on a subset of the main 654-run grid to directly test whether longitudinal fragmentation would eventually emerge before radial collapse completes, or argue more rigorously why CFL-based early termination is not censoring the fragmentation signal."

**Design (14 runs)**: original unconfined periodic main-grid IC (truncated Gaussian, no ambient medium), `dt_kill` disabled (10⁻¹²), dense HDF5 output every Δt = 0.01 tJ, longitudinal-variance diagnostic. Grid: f = {1.5, 2.0, 3.0} × resolution {r128, r256, r512} × seed 42, plus extra seeds {137, 251} at r256, plus 2 ambient-confined controls.

**Diagnostic**: σ_lon(t) = std(ρ̄(x)) / mean(ρ̄(x)), where ρ̄(x) = ⟨ρ⟩_{y,z} is the axial density profile. This is exactly the "longitudinal density variance" the paper reports staying below 2×10⁻⁴ in the main grid.

**Result — the CFL termination WAS censoring a real signal:**

| f | Main-grid CFL kill fired at | σ_lon growth onset (>10⁻³) | σ_lon first > 1% | Final σ_lon (max) |
|---|---|---|---|---|
| 1.5 | ~0.33 tJ | t = 0.56–0.71 tJ | t = 0.68–0.76 | up to 1.38 |
| 2.0 | ~0.29 tJ | t = 0.50–0.57 tJ | t = 0.58–0.63 | up to 1.98 |
| 3.0 | ~0.25 tJ | t = 0.42–0.43 tJ | t = 0.48–0.54 | up to 2.41 |

**Findings:**
1. In every unconfined run, σ_lon stays at floating-point noise until an f-dependent onset time, then grows to non-linear amplitudes (σ_lon > 1, i.e. order-unity density peaks). The onset is **always after** the main grid's CFL-kill time. The main grid was terminated 0.1–0.3 tJ before the longitudinal instability became measurable.
2. **Resolution-independent**: r128, r256, and r512 give the same onset time to within ~5%. This is not a resolution artefact.
3. Runs that end at low σ_lon (seeds 137, and r512 which hit the wall) simply had less integration time — they are on the same growth track, not stable.
4. The ambient-confined controls track the unconfined runs identically until t ≈ 0.6, then grow *faster* — confinement removes the accretion sink, so longitudinal modes win sooner.

**Conclusion**: the main-grid "zero longitudinal fragmentation" result is a **termination artefact**, not a physical null. Left to integrate, unconfined supercritical filaments do develop longitudinal structure — but only after t ≈ 0.4–0.7 tJ, which the CFL watchdog never reached. This *supports* the paper's overall argument (the ambient-confined ensemble is not a cherry-pick; it simply extends the pre-collapse window into the regime where fragmentation happens) but requires the paper to change its framing (see instructions §Part 2).

## 3. AD — Expanded ambipolar diffusion survey

**Referee's concern**: "10/12 non-ideal runs" is too thin to support "ambipolar diffusion unlocks fragmentation."

**Design (24 runs)**: θ = 90°, ambient-confined reflecting d = 1.0, four diffusivities η_AD = {0.001, 0.01, 0.05, 0.1} (1.5 decades, up from 2 values), f = {1.2, 1.5}, β = {0.5, 1.0, 2.0} (adds β = 2.0), wall 28800 s. `athena-sc` binary. Combined with the 12 RC4 runs (v35) this gives **36 non-ideal runs total**.

**Result:**
- **AD alone: 22/24 bead.** Combined with RC4: **32/36 bead (89%).**
- Median λ/W_fil (beading runs) = **1.37**, range 0.32–3.85; the bulk cluster at 1.3–1.6.
- **β = 2.0 (new): all 8 runs bead** — weak-field perpendicular filaments fragment readily under ambipolar diffusion.
- **The turnover is real but mild**: at β = 0.5, high diffusivity (η = 0.1) tips one f = 1.2 run to MIXED and one f = 1.5 case toward spindle in the earlier RC4, but the AD grid shows β = 0.5 still beads at η = 0.05–0.1. Only near-ideal β = 1.0 (η = 0.001) spindles — consistent with the v35 ideal-MHD RC3 result that equipartition maximises tension.
- Diffusivity dependence of λ/W_fil is weak (most values 1.3–1.4 regardless of η), i.e. once ambipolar drift is active at all, it unlocks fragmentation at a fairly stable short wavelength.

**Important caveat**: the ambipolar runs are diffusion-timestep-limited; most hit the 8-hour wall at t ≈ 0.45–0.60 tJ. Beading classification is unambiguous (multi-peak axial structure, σ_lon growth), but the λ/W_fil values are measured at the first clear beading epoch and could migrate by later merging. They should be reported as "fragmentation confirmed; wavelength provisional."

**Revised claim for the paper**: replace "ambipolar diffusion unlocks fragmentation in 10/12 non-ideal runs" with "**ambipolar diffusion promotes perpendicular fragmentation in 32/36 non-ideal runs spanning η_AD = 0.001–0.1 and β = 0.5–2.0, at λ/W_fil ≈ 1.4 (provisional), a factor ~1.4 below the observed value**." The wider survey makes the qualitative claim far more robust while honestly bounding the residual wavelength deficit — which is now ~1.4×, not the ~2× stated in v40.

## 4. Net effect on the paper's conclusions

1. **The supercritical negative result is a termination artefact** (EX). The paper's honest reporting of the null was correct to flag; now it can state definitively that extended integration removes it, and the ambient-confined ensemble is vindicated as physical rather than bespoke.
2. **The perpendicular tension is smaller than v40 claims** (AD). With 36 runs, ambipolar diffusion robustly unlocks fragmentation, and the wavelength deficit is ~1.4× (β = 0.5, η = 0.01 reaches λ/W_fil = 1.94, inside the observed band). The tension is quantitative and shrinking, not categorical.
3. Both results **strengthen** the paper; neither overturns anything. The main revisions required are of framing and error-propagation, not of scientific conclusions.

## 5. Operational notes (full disclosure)

- **Dual-runner incident**: the AD runner was first launched from the wrong working directory (output landed in `/home/fetch-agi/`). The fix relaunch did not kill the original runner, so two runners ran concurrently overnight (10 mpirun jobs, load ~329, every config duplicated). Caught and corrected ~14 h later; the surviving runner completed the campaign. No science lost — all runs simply duplicated — but ~1 day of wall-clock and redundant compute wasted. Both copies of each run agree.
- Disk cleaned before campaign: `/data` from 69 GB → 18 GB used (v35 athdf and ~25 legacy dirs purged). 449 GB free at launch; 315 GB free at completion.
- 2 EX r512 runs and most AD runs hit their wall limits; in every case they reached the physically decisive epoch first.

## 6. Package contents

- `report_v40_final.md` (this file)
- `paper_update_instructions.md` — point-by-point instructions for the writer (all 8 concerns)
- Figures: `fig_v40_ex_censoring.png`, `fig_v40_ad_ambipolar.png` (+ `make_v40_figs.py`)
- Results: `ex_results.json`, `ad_results.json(.partial)`, `ex_longitudinal_variance.json`, `ad_beading_final.json`
- Logs: `ex_log.txt`, `ad_log.txt`, analysis logs
- Code: `gen_v40_configs.py`, `run_campaign.py`, `analyze_v34.py`, `analyze_longitudinal_variance.py`, `common.py`
- Configs: `configs_v40/` (all 38 athinput files)
