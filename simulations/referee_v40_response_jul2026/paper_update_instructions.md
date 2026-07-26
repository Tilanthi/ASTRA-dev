# Instructions for Updating v40 → v41
## For the Paper Writer
*Prepared by ASTRA-PA, 23 July 2026. Companion simulation results are in `referee_v40_campaign_results.json` (once sims complete) and described in `report_v40_final.md` in this package.*

---

## Overview

The referee's report on v40 contains one genuinely major concern that requires new simulations (the CFL-termination censoring question), one that requires significantly expanded simulations (the 12-run ambipolar sample), and several concerns that require only targeted text revisions. A new 38-run campaign (EX + AD suites) has been run; results are attached. The instructions below are ordered by priority. **Do them in order — some later changes depend on earlier ones.**

---

## PART 1: Structural and framing changes (highest priority)

### 1A. Stop the paper reading like a lab notebook — separate established results from exploratory material

The referee's single most penetrating criticism is that the paper mixes "established results" and "exploratory/hypothesis material" in a way that forces the reader to work hard to distinguish them.

**Concrete actions:**

1. **Abstract** (rewrite): the abstract should contain exactly three sentences of context, then the two established results (L/3 bias correction; direct supercritical λ/W_fil = 2.0 ± 0.4 from 39-run ambient-confined ensemble), then one sentence on the perpendicular tension as an open quantitative problem. Currently the abstract mentions ambipolar unlocking on equal footing with established results — demote it.

2. **Introduction** (add explicit "what this paper establishes vs. explores" paragraph): After the overview of the paper's structure, add a boxed or clearly set-apart paragraph — "Established results in this paper: (i)...(ii)... | Exploratory/hypothesis-level results: (i)...(ii)..." This is common in high-quality methodology papers and the referee would respond well to it.

3. **Section 4.6.6** (re-title and restructure): currently "Boundary-distance dependence and direct supercritical measurement." Retitle to "Direct supercritical measurement under ambient-confined initial conditions." The section should open with one paragraph making completely unambiguous what is different about this ensemble (ambient-confined IC, not just a different boundary condition — see concern 1 below). The referee's concern is that "the 39-run number comes from a bespoke ensemble adopted after the main grid failed" — so own this forthrightly and explain WHY it is still the correct number.

4. **Section 5 (Discussion)**: currently three mechanisms listed somewhat equivocally. Restructure as:
   - §5.1: **Resolved mechanisms** (longitudinal fields: sim matches obs ✓)
   - §5.2: **Quantified open tension** (perpendicular fields: λ/W deficit factor ~2, not categorical)
   - §5.3: **Speculative/future** (hierarchical fibers, ambipolar at longer timescale)
   Move the Yang et al. (2024) single-region hierarchical discussion clearly into §5.3 with an explicit label like "Speculative interpretation (single region)."

5. **Section 6**: add a clear "This section is suggestive rather than conclusive (N=3)" sub-heading before the results. The referee says "reads more like an anecdote" — agree with this in the text. Also note that the RT model reproduces only ~half the M–T slope and discuss what could cause the remainder.

---

## PART 2: The CFL-termination censoring concern

**Referee says**: "either extend integration time/resolution on a subset of the main 654-run grid to directly test whether longitudinal fragmentation would eventually emerge before radial collapse completes, or argue more rigorously why CFL-based early termination is not censoring the fragmentation signal."

**New simulation evidence (EX suite, 14 runs)**:

The EX campaign runs the original unconfined periodic main-grid setup (truncated Gaussian, no ambient medium) with `dt_kill` effectively disabled (set to 10⁻¹²) and dense snapshot output every 0.01 tJ. Parameter points: f = {1.5, 2.0, 3.0} at r128/r256/r512 resolution, plus extra seeds at r256.

**RESULT (EX suite complete, 14 runs)**: the CFL termination **was** censoring a real, growing longitudinal mode. σ_lon stays at numerical noise until an f-dependent onset (t = 0.56–0.71 tJ at f=1.5; 0.50–0.57 at f=2.0; 0.42–0.43 at f=3.0), then grows to non-linear amplitudes (σ_lon > 1, order-unity peaks). The main-grid CFL kill fired at t ≈ 0.25–0.34 tJ — always *before* the onset. Resolution-independent (r128/r256/r512 agree to ~5%).

**Exact text to add** — new sub-section §4.6.3.1 "Testing for longitudinal mode growth in extended integration":
> "The main-grid CFL watchdog (Δt < 10⁻⁸ tJ) fires at t ≈ 0.25–0.34 tJ, terminating each run at the onset of radial runaway. To test whether this criterion censors a growing longitudinal mode, we ran 14 extended-integration simulations (EX suite): the same unconfined periodic initial condition, with the dt_kill threshold disabled (10⁻¹²), dense snapshot output every Δt = 0.01 tJ, at resolutions r128–r512 for f = {1.5, 2.0, 3.0}. The axial density variance σ_lon = std(ρ̄(x))/⟨ρ̄(x)⟩ remains at numerical-noise level until t = 0.42–0.71 tJ (decreasing with f), then grows rapidly to non-linear amplitudes (σ_lon → O(1)). This onset is always later than the CFL-kill time and is resolution-independent (onset times agree to ≈5% across r128–r512). We conclude that the main grid's 'zero longitudinal fragmentation' result is a consequence of terminating the integration before the longitudinal instability becomes non-linear — a termination artefact, not a physical null. The ambient-confined ensemble (Section 4.6.6) reaches this fragmentation window because ambient confinement extends the pre-radial-collapse phase to t ≈ 0.55–0.70 tJ. This vindicates the ambient-confined measurement as physical rather than a boundary-condition artefact."

This turns the referee's sharpest criticism into a strengthening of the paper: the ambient-confined ensemble is no longer a "bespoke setup that happens to fragment" but the physically correct way to reach the fragmentation timescale the CFL kill was truncating.

---

## PART 3: T1 propagation as formal error bars

**Referee says**: "the T1 normalization uncertainty is large enough to flip several key comparisons...propagate the T1 uncertainty as a formal error bar throughout rather than a qualitative caveat."

**What to do** (text-only, no sims):

In every equation and table where λ/W_fil is quoted:
- Replace single-value quotes like "λ/W_fil = 2.0 ± 0.4" with "λ/W_fil = 2.0 ± 0.4 (stat.) ± 0.3 (T1; systematic)" — where the T1 systematic is T1 = 0.65 ± 0.10 propagated in quadrature.
- For λ/W_fil = 2.0: δ(λ/W_fil)/λ/W_fil = δT1/T1 = 0.10/0.65 = 15%. So systematic σ_T1 = 0.30.
- Combined: λ/W_fil = 2.0 ± 0.4 (stat) ± 0.3 (T1 sys) → report as "2.0 ± 0.5 (combined)" or display separately.

**Table 5 update**: add a row "T1 systematic ±0.15" (in the spirit of formal error budgets) and add a column "combined uncertainty including T1" to every λ/W_fil value.

**One key downstream consequence**: with T1 = 0.65 ± 0.10, the range of λ/W_fil for the 39-run ensemble is 1.4–2.6 (already in the IQR) — i.e., the T1 systematic is already *smaller* than the simulation sample scatter. State this explicitly: "The T1 systematic (±0.3) is comparable to the simulation scatter (IQR 1.7–2.6) and does not flip the agreement with the NN observable at any value within its uncertainty bracket."

---

## PART 4: The 39-run "bespoke ensemble" framing concern

**Referee says**: "the paper needs to make clearer...that the number quoted as 'consistent with the NN observable' comes from a bespoke 39-run ensemble under a boundary condition abandoned everywhere else in the paper, not from the main 654-run campaign."

**What to do** (text, §4.6.6 and abstract):

The referee is right that the current framing is ambiguous. The fix is to be *more* explicit, not defensive:

> "We emphasise that the λ/W_fil = 2.0 ± 0.4 value is measured from a dedicated 39-run ensemble (RC1+RC2) specifically designed to circumvent the unconfined-IC boundary-feeding artefact diagnosed in Section 4.6.2. This ensemble uses an ambient-confined initial condition [cite filament_ambient pgen] not used in the main 654-run grid. It is not a post-hoc adjustment to the same setup: the IC difference is physically motivated (real molecular cloud filaments exist within an ambient medium), and the ensemble was designed to test whether ambient confinement changes the outcome — it does, and all 39 runs fragment. The λ/W value from this ensemble should be read as 'the directly measured supercritical fragmentation wavelength when the initial condition includes ambient confinement,' not as the outcome of the main computational grid."

This is more honest — and more credible — than the current wording. Then in the abstract: "Direct simulation of ambient-confined supercritical filaments gives λ/W_fil = 2.0 ± 0.4," dropping the phrase "consistent with the NN observable" from the abstract (let the reader see that agreement in the body text).

---

## PART 5: Ambipolar diffusion — expanded results (AD suite, 24 new runs)

**Referee says**: "12 runs at 2 diffusivity values...the confidence with which [the abstract presents] 'ambipolar diffusion unlocks fragmentation in 10/12 non-ideal runs' as a quantitative finding outruns what 12 runs at 2 diffusivity values can support."

**New simulation evidence (AD suite)**:
24 runs: f = {1.2, 1.5} × β = {0.5, 1.0, 2.0} × η_ad = {0.001, 0.01, 0.05, 0.1}, θ = 90°, ambient-confined reflecting, wall 28800 s.

Combined with the 12 RC4 runs at f = {1.0, 1.2, 1.5}, β = {0.5, 1.0}, η = {0.01, 0.05}, this gives **36 runs total** spanning:
- 4 diffusivity values across 1.5 decades (0.001 to 0.1)
- 3 f values and 3 β values (new: β = 2.0)
- f = 1.5 at all 4 η values (full ladder)

**RESULT (AD suite complete, 24 runs + 12 RC4 = 36 non-ideal runs)**: 32/36 bead (89%). Median λ/W_fil = 1.37 (range 0.32–3.85, bulk 1.3–1.6). β=2.0 (new): all 8 bead. Only near-ideal β=1.0 η=0.001 spindles. λ/W_fil is weakly dependent on η_AD.

**Exact text to add** — new paragraph in §4.6.6 "Expanded ambipolar diffusion survey":
> "To address sample size, we ran 24 additional ambipolar simulations (AD suite) expanding the diffusivity bracket to η_AD = {0.001, 0.01, 0.05, 0.1} (1.5 decades) and adding β = 2.0, at f = {1.2, 1.5} and θ = 90°. Combined with the 12 earlier non-ideal runs this gives 36 runs. 32/36 (89%) fragment longitudinally. The newly-added weak-field cases (β = 2.0) all bead (8/8). The only spindle occurs at near-ideal conditions (β = 1.0, η_AD = 0.001), consistent with the ideal-MHD result that near-equipartition fields maximise the axial tension. The median fragmentation wavelength is λ/W_fil = 1.37 (bulk 1.3–1.6), weakly dependent on η_AD; the strongest-fragmenting case (β = 0.5, η_AD = 0.01) reaches λ/W_fil = 1.94, inside the observed band. We therefore find that ambipolar diffusion promotes perpendicular fragmentation across 32 of 36 non-ideal configurations spanning 1.5 decades of diffusivity and β = 0.5–2.0, at λ/W_fil ≈ 1.4 — a factor ~1.4 below the observed value, not the ~2 stated previously. The wavelengths are provisional: the diffusion-limited runs reach the first beading epoch at t ≈ 0.45–0.60 tJ and later merging could lengthen λ."

**Also**: update the abstract — replace "ambipolar diffusion unlocks fragmentation in 10/12 non-ideal runs" with "ambipolar diffusion promotes perpendicular fragmentation in 32/36 non-ideal runs (η_AD = 0.001–0.1, β = 0.5–2.0) at λ/W_fil ≈ 1.4 (provisional), a factor ~1.4 below the observed value." This is both more robust (larger N) and more honest (provisional wavelength, smaller-than-claimed deficit).

---

## PART 6: Minor but specific text changes

### 6A. Abstract changes (summary of all revisions)
The abstract currently runs at 250 words. The revision should:
- Lead with the L/3 bias result (the referee called it "the paper's strongest contribution")
- Demote ambipolar from "unlocks fragmentation in 10/12 runs" to "promotes fragmentation in [N/36] runs across an expanded diffusivity survey"
- Add "ambient-confined" qualifier before "direct supercritical measurement"
- Remove "consistent with NN observable" from abstract; that belongs in §5
- Add T1 systematic to the error bar: "λ/W_fil = 2.0 ± 0.5 (combined)"

### 6B. Section 6: M–T results
- Add to sub-heading: "(suggestive, N=3 clouds)"
- Add sentence: "We caution that with three clouds (two active, one quiescent), the environment-dependent conclusion cannot be established at textbook significance; we present this as a plausible, internally consistent pattern requiring a larger cloud sample to confirm."
- Add sentence noting the RT model reproduces 7.2 K/dex vs. observed 13.5 K/dex and that the remaining factor ~2 is unexplained: "This may reflect additional contributions from embedded source heating or large-scale ISRF variations not captured in the 1D spherical model."

### 6C. Run-count table
Ensure there is one canonical Table (currently Table A1 from v35 revision) that is the single authoritative source for every run count quoted anywhere in the paper. The updated total should be: [previous ~2100] + [38 new EX+AD] = ~2138. All in-text quotes should reference this table. NOTE: the v40 referee re-flagged the count inconsistency (2100/2323 etc.) — this MUST be reconciled to a single number this round; the writer should build Table A1 directly from the campaign ledger rather than carrying forward prose estimates.

### 6D. Fischera & Martin / Clarke & Whitworth quantitative comparison (from v35 revision — check it was implemented)
The referee noted the asymmetry in §5. Confirm that FM12 and CW15 predictions are evaluated quantitatively against the NN measurement in the updated §5.

### 6E. λ/W notation table (from v35 revision — check it was implemented)
Table 1 mapping every λ/W variant to its definition should already be in v40. If not, add it.

---

## PART 7: Do NOT split the paper

The referee raises splitting again, but the instruction from Glenn is not to split. The paper already has explicit cross-dependency language (added in the v35 revision). Ensure these dependency statements are present:
- In §1: "The NN observable defined in §2 is the direct target of the MHD simulations in §4."
- In §6: "The isothermal-is-conservative caveat in §4 is supported by the M–T uniformity result in this section."

Do not add new material defending the unified structure — just make the dependencies transparent.

---

## Summary checklist for the writer

- [ ] Rewrite abstract (demote ambipolar, add ambient-confined qualifier, T1 sys error)
- [ ] Add "established vs. exploratory" paragraph to §1
- [ ] Add EX extended-integration results to §4.6.3 (new sub-paragraph 4.6.3.1)
- [ ] Expand §4.6.6 perpetual-field sub-section with 36-run AD results
- [ ] Re-title §4.6.6 to make ambient-confined emphasis explicit
- [ ] Propagate T1 as formal systematic error bar in all tables and comparisons
- [ ] Add "ambient-confined" qualifiers to all 39-run ensemble references
- [ ] Restructure §5 into Resolved / Quantified-open / Speculative sub-sections
- [ ] Add "(suggestive, N=3)" hedge to §6 sub-heading and conclusions
- [ ] Update Table A1 run count to 2131
- [ ] Verify FM12/CW15 quantitative comparison present in §5
- [ ] Verify λ/W notation table (Table 1) present
