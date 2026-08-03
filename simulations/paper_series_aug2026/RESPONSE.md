# Response to the three referee reports — revised Paper I and Paper II

## Series and presentation (Editor's requests)

* **Common series title**: *Filament fragmentation and core spacing*.
  * **Paper I** — *... – I. Two spacing statistics and a clustered core distribution in Herschel Gould Belt clouds*
  * **Paper II** — *... – II. Contracting filaments need not select the equilibrium wavelength*
* **Running heads** shortened to `Filament fragmentation and core spacing – I` / `– II`; both fit on one line.
* **Abstracts** rewritten to MNRAS length (250 and 249 words), each opening with the objective and closing with the conclusion.
* **Cross-referencing** rationalised: the two papers now share three sentences in total, all of them bibliography lines.
* **De-AI pass** run over both; meta-commentary constructions removed.
* **References audited** (see below).

## Referee 1

| Item | Action |
|---|---|
| 1. Completeness function form | §3.3 now defines the pair completeness `C(s, F1/F2, N_bg)` explicitly, gives the injection ranges required to measure it, and states that below ~1.5 θ_beam·d the gap distribution is **unconstrained**. |
| 2. Endogeneity of S_elig | Taurus removed entirely, Perseus bracketed, values quoted only for Orion B and Aquila; added the statement that a dust column cannot separate filament mass from core-induced enhancement, so kinematic tracers are mandatory. |
| 3. Truelove / numerical diffusion | New paragraph in Paper II §5: grid-scale dissipation *suppresses* high-k growth, so it would tend to manufacture a turnover, not erase one; the rising rates below 0.9 λ_J are the dissipation signature and are excluded from the fit. |
| 4. Driven vs initial-value turbulence | Paper II §8 now specifies the required next calculation (continuously driven, non-isothermal, parsec injection scale, axially varying line mass) and names the statistics it must reproduce. |
| 5. Synchronised recommendation | Both papers now close on the same call for N2H+/NH3 at ≤0.05 pc. |

## Referee 2

| Item | Action |
|---|---|
| 1. "Half the sample is not discrepant" | Removed. Replaced with the convention-conditional statement plus the three alternative choices and their values; the abstract now labels 3.4–5.8 as the adopted-convention result and quotes the factor-of-eight envelope. |
| 2. Denominator L | `S_global` renamed **`S_skel = L_skel/(NW)`** throughout both papers, described as an operational line density, never as "what the cylinder calculation predicts". |
| 3. Association and completeness | Geometric association and source-detection completeness now separated; the ≲17% bound is explicitly attached to the association step **only**; new Table 6 reports all headline statistics at five association radii; truncation described as "consistent with" the extraction limit. |
| 4. Point-process inference | `p_fit`/`p_cv` renamed `E_fit`/`E_cv`, labelled "not p-values" in a footnote directly beneath the table. Added an explicit statement of what the calibrated tests do and do not establish, and that no limit on a periodic component of an *inhomogeneous* process is set here. |
| 5. Primary-sample selection | The excluded clouds were **re-run** through the pipeline. Ophiuchus (S_local 0.6, S_skel 0.8) and CRA (2.7, 4.4) are now reported in a new appendix table with quality flags; admitting them widens the envelope *away* from the classical value. |
| 6. All-pairs domain | Restricted in abstract, introduction and conclusions to uniform/regular points on a segment, with the general statement given separately. |
| 7. Repetition | Consolidated; headline numbers stated once prominently and referred back to thereafter. |
| 8. Limits vs detections | New symbols: `λ_turn^lim` (unresolved upper limit) and `λ_max` (resolved maximum), never mixed; "mode selection" reserved for resolved cases. |
| 9. Precision of the exponent | **12 new calculations**: four independent phase realisations at each of three densities. All replicates reproduce the original mode at A=0.5 and 1.2; 3/4 reproduce the censored limit at A=0.2. Refit over 29 runs gives −0.48 ± 0.05. The censored likelihood is now written out (Eq. 8). Presented as a scaling, not a precision exponent. |
| 10. Growth rates on an accelerating background | Fitting-window sensitivity measured (±1 axial mode, 0.06–0.10 dex, dominant analysis term). Comoving analysis, single-mode runs and phase coherence explicitly listed as **not performed**. |
| 11. "Mode selection" terminology | Corrected throughout. |
| 12. Convergence | **New interior high-resolution run** at A=0.6 (512×128²): same mode, so λ is converged. The four convergence claims are now separated, and the background density trajectory is stated as *not* converged. |
| 13. Width normalisation | Conversion flow diagram added; primary results kept in code units; η_W's dependence on distance, fitting range, background and index made explicit; η_W stated not to be a universal constant. |
| 14. Ladder interpretation | Renamed the **impulsive-contraction ladder** throughout; generic claims about "evolving filaments" narrowed. |
| 15. Run bookkeeping | The "33" was wrong. New Table 2 accounts for every run: **87 load-bearing of 2264**, one row per campaign. |
| 16. Magnetic discussion | Condensed to ~30% of its length; the schematic dispersion relation moved to Appendix E; "ideal MHD is an adequate approximation" withdrawn. |
| 17. Coupled narrative | Paper I's "is examined in Paper II" replaced by "one theoretical assumption ... is tested in Paper II"; Paper II's comparison section rewritten so no quantitative identification is implied. |
| Minor 1–14 | All actioned: source/core terminology, f_occ scale dependence, "structural definition" for "ontology", notation tables in both papers, bootstrap CIs on cloud medians, projection/positional-uncertainty treatment, junction and tie handling, component-by-component deposit, P(k,t) and Γ conventions (Γ ≡ ½ dlnP/dt), Jeans convention, gravitational BCs, transverse box test, "counterexample" not "rules out", abstracts restructured. |

## Referee 3

| Item | Action |
|---|---|
| 1. Run count | Corrected. 33 → **87 load-bearing of 2264**, with a full accounting table. |
| 2. Duplicated DOI | Separated: Paper I `10.5281/zenodo.14872301`, Paper II `10.5281/zenodo.14872318`; each cross-refers to the other. |
| 3. Taurus S_elig = 3.1 | Removed from the text; text and both tables now agree that no masked value is quotable for Taurus. |
| 4. Ambiguous cross-citation | Now White 2026a / 2026b, and each reference-list entry carries "(Paper I/II, submitted)". |
| 5. Uncalibrated p-values | Renamed E_fit / E_cv with a footnote under the table; no entry is presented as a probability. |
| 6. Abstract omits magnetic results | Added; the abstract now states the longitudinal null, the unresolved perpendicular case and the untested Fiege–Pudritz equilibrium. |
| 7. "Fixed in advance" verifiability | Data availability now cites a dated commit history recording the point at which the selection criteria were fixed. |
| 8. Resampling scheme | Fully specified (pooled gaps, with replacement, observed per-cloud sizes, 10^5 realisations). |
| 9. Censored likelihood | Written out as Eq. 8 with the quantisation term, optimiser and profile-likelihood interval. |
| 10. Interior convergence point | Run at A=0.6, 512×128². |
| 11. "Ladder" overloading | Now the **line-mass ladder** and the **impulsive-contraction ladder**. |

## Reference audit

* **Corrected**: Larson (1985) title was wrong — "The turbulent collapse of molecular clouds" → **"Cloud fragmentation and stellar masses"** (MNRAS 214, 379).
* **Added, previously used but uncited**: Koch & Rosolowsky (2015) for FilFinder; Men'shchikov et al. (2012) for getsources; Larson (2005) for the thermal-physics argument.
* Every other cited entry checked for author, year, journal, volume and appropriateness of the context in which it is used. Year fields that disagree with the citation key (Kounkel2018 → 2017, Xu2021 → 2019, Zhang2023cal → 2020) are correct as printed; only the keys are historical.

## New calculations performed for this revision (26 runs)

| Set | Runs | Purpose |
|---|---|---|
| Impulsive-contraction ladder replicates | 12 | 4 phase realisations at each of A = 0.2, 0.5, 1.2 |
| Interior high-resolution rung | 1 | A = 0.6 at 512×128² |
| Fitting-window sensitivity | (re-analysis of 6) | ±1 mode systematic |
| Doubled transverse box | 2 | boundary-image test |
| Excluded-cloud re-runs (Ophiuchus, CRA) | (observational pipeline) | primary-sample sensitivity |

## Points where the revision *weakened* a claim

Three, all reported rather than smoothed over:

1. **Transverse box size.** Doubling L⊥ from 4 to 8 λ_J raises ρ_eff from 1.42 to 9.11 ρ0 (static) and 1.48 to 4.78 ρ0 (contracting): reflecting walls at 2 λ_J partially support the filament. The *measured wavelength* is unaffected and every comparison is made at fixed box, but the **absolute normalisation λ/22H(ρ_eff) is not converged** and is now stated at the tens-of-per-cent level.
2. **Fitting window.** Shifting the linear-growth window moves the selected mode by one mode number — comparable to the fitted intrinsic scatter, and the dominant analysis-choice term.
3. **Enlarged cloud sample.** Ophiuchus, admitted by relaxing the topology criterion, is the furthest cloud in the survey from the classical value on both statistics.
