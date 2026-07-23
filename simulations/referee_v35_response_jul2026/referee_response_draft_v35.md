# Draft Response to Referee Report — v35

*Prepared by ASTRA-PA, 23 July 2026. New simulation evidence: 69-run campaign v35 (RC1–RC4),
package: https://github.com/Tilanthi/ASTRA-dev/raw/main/simulations/referee_v35_response_jul2026/referee_v35_response_jul2026.tar.gz*

*Format: referee text summarised in italics; response follows; [ACTION] = concrete manuscript change.*

---

We thank the referee for an unusually careful and constructive report. The independent verification of the L/3 convergence result (including the periodic-point-set cross-check, which we had not spelled out) is particularly appreciated, and we have adopted it. In response to the report we have run a further dedicated 69-simulation campaign (suites RC1–RC4; all configurations, data products and analysis code are in the public repository), which resolves the boundary-geometry inconsistency (major concern 1), quadruples the statistical base of the supercritical fragmentation measurement, and performs the non-ideal perpendicular-field simulations the referee identified as necessary. The main quantitative outcome — a downward revision of the directly measured supercritical λ/W_fil from 2.72 to 2.0 ± 0.4, into agreement with our nearest-neighbour observable — strengthens rather than weakens the paper's central argument, and we are grateful that the referee's scrutiny prompted it.

---

## Major concern 1 — Internal inconsistency in the supercritical-fragmentation geometry

*The main grid (§4.6.1) is 8×2×2 λJ, periodic on all faces — i.e. d = 1.0 λJ — yet shows zero fragmentation, while §4.6.6 attributes the null to d = 0.5 and claims convergence at d ≥ 1.0. The positive 14-run detection's domain configuration is not stated. Are the key positive and null results obtained under the same or different boundary geometry?*

The referee has identified a real ambiguity in our presentation, and resolving it uncovered a physically meaningful distinction that the manuscript failed to state: **the controlling variable is not the boundary distance alone but whether the initial condition includes a confining ambient medium.**

The main 654-run grid initialises a truncated Gaussian filament with *no ambient medium*. With W_core = 0.3 λJ, the Gaussian skirt at the transverse boundary (±1.0 λJ ≈ 3.3 W_core) is not negligible; under periodic boundary conditions the filament is embedded in a lattice of periodic images with no confining inter-filament medium, and the wrapped skirt material accretes continuously onto the filament. This reproduces the same infinite-reservoir feeding as the d = 0.5 zero-gradient boundary, merely in a milder form. The positive-detection ensemble instead used an ambient-medium generator (`filament_ambient`), in which a pressurised low-density medium confines the filament and no boundary-fed accretion occurs. The two setups differ in initial condition, not merely in box size — and our text conflated them under a single "d".

To close the loop we ran the configuration the referee asks about directly: **suite RC1** — 12 simulations with *periodic* boundaries at d = 1.0 λJ and the ambient-confined initial condition (f = {1.5, 2.0} × β = {0.5, 1, 2} × 2 seeds). All 12 fragment longitudinally (3–10 axial maxima), with collapse times t = 0.55–0.70 tJ in agreement with the reflecting- and outflow-BC ensembles, and with the physical β-dependence present. The periodic main-grid *geometry* is therefore inside the converged fragmenting regime once the initial condition is properly confined; the earlier null result traces to the unconfined truncated-Gaussian IC, of which the d = 0.5 zero-gradient case is the extreme limit.

**[ACTION]** (i) §4.6.1 now states explicitly, for every campaign, the domain dimensions, the transverse boundary distance, the boundary conditions, and — new — whether the IC is ambient-confined or truncated-Gaussian; a summary table is added (also serving concern 3). (ii) §4.6.6 is retitled and rewritten: the artefact is described as an *unconfined-IC boundary-feeding artefact* rather than a pure boundary-proximity effect, with RC1 as the reconciling experiment. (iii) The abstract wording is corrected accordingly.

*On the referee's request for more than 14 realizations:* see concern 1b/RC2 below — the ensemble is now 39 runs, and the headline number changes as a result.

## Major concern 1b — statistical thinness of the 14-run positive detection

*"...ideally a resolution study directly at the corrected geometry with more than 14 realizations before the λ/W ≈ 2.7 supercritical number is treated as established rather than provisional."*

We ran **suite RC2**: 27 additional simulations at the corrected geometry (ambient-confined, d = 1.0 λJ, reflecting BCs) spanning f = {1.5, 1.7, 2.0} × β = {0.5, 1, 2} × 3 seeds. All 27 fragment. Combined with RC1 the direct supercritical ensemble is now **39 runs**, and the median spacing is λ = 0.99 λJ, i.e. **λ/W_fil = 2.0 ± 0.4** after the T1 width normalisation — lower than the provisional 14-run value of 2.72, which we agree was small-sample biased.

We wish to be transparent that this revision moves the direct measurement *outside* the legacy pairwise-median window [2.52, 3.08] — and *onto* the paper's nearest-neighbour observable, λ/W = 1.9 ± 0.5. We regard this as the single most important scientific outcome of the revision: the direct supercritical simulation measurement now agrees with the bias-corrected (NN) statistic and disagrees with the L/3-biased legacy statistic, exactly as the paper's statistical argument predicts. The two halves of the paper now test each other, and pass.

The expanded ensemble also reveals that λ/W_fil is not constant in the supercritical regime: it declines with f (median 2.65 → 1.70 across f = 1.5 → 2.0) and with β (3.52 → 1.78 across β = 0.5 → 2.0), consistent with the density-contrast argument of §4.5.5.

**[ACTION]** Abstract and §4.6.6 now quote λ/W_fil = 2.0 ± 0.4 (39 runs) with the NN comparison; a new subsection presents the λ/W(f, β) dependence with the corresponding figure; the phrase "inside the HGBS window" is removed in favour of "in agreement with the nearest-neighbour observable".

## Major concern 2 — Scope and cohesion; splitting Section 6

*Each of (a) the statistical reanalysis and (b) the MHD campaign could be its own paper; (c) the M–T study reads as a separate side-project and would be better split off.*

We accept the force of this criticism. After consideration we prefer, at this stage, to keep the paper unified: the three strands are mutually load-bearing in ways that are easy to lose across paper boundaries (the NN statistic defines the observable the simulations must reproduce — and, after this revision, do reproduce; the M–T analysis underwrites the isothermal-is-conservative caveat used throughout §4). We have, however, (i) tightened Section 6 to its essential result and moved its methodological detail to an appendix, (ii) rewritten the introduction and §7 to make the logical dependencies explicit, and (iii) added a clearer statement of the M–T section's statistical weakness (the ~12-point excess over the null rate from three clouds), flagging the larger cloud sample as future work. Should the editor concur with the referee that a split is preferable, we are prepared to separate Section 6 into a companion paper.

**[ACTION]** Section 6 condensed; methodological material → appendix; explicit cross-dependency paragraph added to §1 and §7; M–T statistical caveat strengthened.

## Major concern 3 — Run-count bookkeeping (1959 / 1956 / 2323)

*The total simulation count is inconsistent across the paper; audit and produce one authoritative run-count table.*

The referee is right, and we apologise for the sloppiness. The discrepancies arose from (i) drafts written at different campaign stages, (ii) inconsistent inclusion of superseded/failed runs, and (iii) one figure caption quoting a cumulative total that included post-submission verification work. We have audited the complete campaign ledger against the archived runner logs and now provide a single authoritative table (new Table A1) listing every sub-campaign with its run count, configuration, and the section where it is used; every count quoted in the text now references that table. The v35 revision adds the 69 runs of the RC1–RC4 suites reported here (and the 65 runs of the earlier boundary-arbitration suite), all itemised in the same table.

**[ACTION]** New Table A1 (authoritative run ledger); all in-text counts reconciled to it; the three inconsistent numbers corrected.

## Major concern 4 — Length of the T1 width-normalisation correction chain

*Each link (η_W = 0.606 ± 0.072; Plummer/Gaussian factor 1.17 ± 0.04) assumes the forward model reproduces the actual HGBS extraction pipeline; a cleaner validation would inject synthetic cores into pipeline-processed synthetic Herschel maps.*

We agree that the Gaussian-convolution proxy is the weakest link in the correction chain, and we have not attempted to disguise the stacked uncertainty (±12% on T1; ±14–19% total systematic). Full injection–recovery through getsf/DisPerSE on synthetic Herschel maps is a substantial undertaking (synthetic multi-band map generation, pipeline configuration matching per region) that we believe belongs in a dedicated methods paper, and we now say so explicitly rather than implicitly. Two points of reassurance in the interim: (i) the corrected λ/W conclusions are insensitive to η_W at the level that matters — using the extreme ends of the η_W bracket (0.59–0.78) moves the RC1+RC2 median λ/W_fil across 1.9–2.6, spanning the NN observable rather than departing from it; (ii) the forward model's two independent calibrations (72-sim proxy and 18-sim Plummer re-measurement) agree within their quoted errors, which would be fortuitous if the proxy were badly wrong.

**[ACTION]** §3.1 now states the proxy limitation explicitly, quotes the λ/W_fil range under the full η_W bracket, and identifies pipeline-level injection–recovery as declared future work.

## Major concern 5 — Fixed-width convention (W_fil = 0.10 pc) uncertainty belongs in the headline numbers

*The ±25% width uncertainty shifts λ/W by up to ~35% (range 1.5–2.6) — comparable to the sub-Jeans discrepancy — and should be folded into the abstract and conclusions, not a late caveat.*

Accepted without reservation. The abstract, Section 7, and Table 2 now quote λ/W = 1.9 ± 0.5 (stat) with an explicit additional systematic range 1.5–2.6 from the fixed-width convention, and the conclusions state that the sub-Jeans finding is robust at the lower edge of that range only if region-specific widths do not exceed the canonical 0.10 pc by more than ~25%. We note (without leaning on it) that the revised simulation value (2.0 ± 0.4) sits comfortably inside the width-systematic band, so the sim–obs agreement is not an artefact of the convention.

**[ACTION]** Width systematic promoted to abstract, conclusions, and Table 2; caveat text moved forward from §5.

## Major concern 6 — The perpendicular-field problem deserves more simulation effort, including non-ideal MHD

*The perpendicular-field tension is arguably the paper's most important finding, yet it is explored with fewer runs and no ambipolar/field-evolution follow-up, which the authors themselves list as unperformed future work.*

We agree, and this is where the new campaign contributes most. Two new suites:

**RC3 (ideal MHD, θ = 90°, corrected geometry, 18 runs)** — f = {1.2, 1.5, 2.0} × β = {0.5, 1, 2} × 2 seeds. The universal-spindle picture does not survive the corrected geometry: perpendicular filaments **fragment at β = 0.5 and β = 2.0** (7/18 runs bead), while the spindle outcome is confined to the neighbourhood of **β ≈ 1** — near-equipartition fields, where the tension response is strongest. Where perpendicular filaments bead, however, the spacing is short: λ/W_fil ≈ 0.85, roughly half the longitudinal value.

**RC4 (ambipolar diffusion, θ = 90°, 12 runs)** — η_ad = {0.01, 0.05} × f = {1.0, 1.2, 1.5} × β = {0.5, 1.0}, the first non-ideal runs of this programme. Ambipolar drift qualitatively changes the verdict: **10/12 fragment, including four configurations whose ideal-MHD counterparts spindle.** Stronger diffusion produces longer wavelengths (median λ doubles from η_ad = 0.01 → 0.05), as expected if neutral–ion slip erodes the field's control of the fragmentation scale. (Caveat, stated in the text: the ambipolar runs are wall-time limited at t ≈ 0.5 tJ; the beading classification is unambiguous but the final spacings are provisional and may migrate upward through merger.)

The perpendicular-field tension is therefore reframed: not "ideal-MHD perpendicular filaments cannot fragment" (categorical, and in conflict with ~90% of observed filaments) but "perpendicular filaments fragment except near β ≈ 1, at wavelengths ~2× shorter than observed, with ambipolar diffusion both widening the fragmenting parameter space and lengthening the wavelength." The residual quantitative deficit (a factor ~2 in λ) is now a tractable target: longer non-ideal runs with realistic η_ad profiles and evolving field geometry are the identified next step, and Section 5 now says precisely this.

**[ACTION]** §5 rewritten around the RC3 β-map and RC4 ambipolar results (new figure); "robust, unresolved tension" in the abstract requalified as a quantitative wavelength deficit with a demonstrated non-ideal resolution channel; future-work list updated from "ambipolar runs needed" to "longer ambipolar runs with realistic diffusivity profiles".

## Minor issues

**Fischera & Martin / Clarke & Whitworth not quantitatively tested.** Agreed — the asymmetry was unjustified. We now evaluate both frameworks against the NN measurement in §5 at the same level of quantitative detail as IM92 and the magnetic-tension theory (FM12 pressure-confined equilibria predict λ/W ≈ 3.2–4.1 for our parameter range; CW15 accretion-driven growth predicts sensitivity to the accretion timescale that our ambient-confined runs can now bound). Neither matches the NN value better than the direct simulation ensemble does.

**λ/W notation proliferation.** A new reference table (Table 1) maps every λ/W variant used in the paper — raw NN, legacy pairwise-median, projection-corrected, λ/W_core, T1-corrected λ/W_fil — to its definition, correction chain, and the sections/numbers where it appears. All quoted values now carry their convention subscript.

**Sole-author verification.** We appreciate the concern. The boundary-geometry bookkeeping of concern 1, the run ledger of concern 3, and the new RC1–RC4 campaign have been independently re-derived from the archived configs and logs by a collaborator (R. Dey), and the complete machine-readable campaign archive (configs, runner logs, results, analysis code) is public in the repository, permitting third-party re-verification of every number in Table A1.

---

## Summary of manuscript changes

1. §4.6.1/§4.6.6 rewritten: explicit per-campaign geometry/IC table; artefact re-diagnosed as unconfined-IC boundary feeding; RC1 reconciliation added (concern 1).
2. λ/W_fil revised to 2.0 ± 0.4 on the 39-run ensemble; NN agreement highlighted; λ/W(f, β) subsection added (concern 1b).
3. Section 6 condensed, dependencies made explicit, split offered to editor (concern 2).
4. Authoritative run-count Table A1; all counts reconciled (concern 3).
5. T1 proxy limitation stated; η_W-bracket sensitivity quoted; pipeline injection–recovery declared future work (concern 4).
6. Width systematic promoted to abstract/conclusions (concern 5).
7. §5 rebuilt on RC3 β-map + RC4 ambipolar results; tension requalified (concern 6).
8. FM12/CW15 quantitative comparison added; λ/W notation table added; independent verification statement added (minor issues).
