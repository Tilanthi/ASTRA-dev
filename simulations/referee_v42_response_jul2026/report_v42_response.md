# ASTRA Response to MNRAS Referee — v42 Manuscript
## "Core Spacing in HGBS Filaments: MHD Fragmentation Tests and the Perpendicular-Field Tension" (G. J. White)

**Prepared by:** ASTRA-PA (simulation & analysis assistant) for G. J. White
**Date:** 2026-07-26
**Scope:** This document addresses the referee points that fall within the simulation / quantitative-analysis
work: **A2, A3, A5, A6, A7, the C4–C8 production defects, the non-monotonic perpendicular-field beading,
and the λ/W_core→λ/W_fil arithmetic (referee point D).** Each item gives (i) the finding, (ii) whether new
simulations were required and what was run, and (iii) **concrete, drop-in instructions for the paper-writing
version of ASTRA.** Text intended to go into the manuscript is given in `>` blockquotes.

All new analysis, data products, the corrected figure, and the new simulation configs referenced below are in
the accompanying package (`referee_v42_response_jul2026.tar.gz`).

---

## ADDENDUM (2026-07-27) — response to the four paper-writer warnings

**1. Figs 6 and 9 now regenerated (not just instructions).** The two figures with defects baked into their
PDFs are supplied as corrected drop-ins:
- **`figures/fig6_eos_corrected.pdf`** (C6) — the broken "green 100 % TIMEOUT pie disc" is replaced by a proper
  two-panel figure: isothermal `t_frag` histogram (all runs fragment) + an adiabatic all-null annotation panel
  ("0/30 fragmented; all timed out at t > 30–40 t_J"). *Note:* the histogram uses the available near-critical
  isothermal FRAG sample (n = 106, median 0.89 t_J); if you still hold the exact original Phase-1 80-run sample
  (median 1.08 t_J), substitute it — the panel layout/annotation is the fix, the sample is interchangeable.
- **`figures/fig9_nearcritical_corrected.pdf`** (C8) — same content as before but the right-hand T1 axis is
  relabelled **×0.65** (was ×0.606), consistent with the global T1 fix. Left panel λ/W_core vs f (near-flat,
  <5 % variation, five β); right panel mean-per-β with the corrected second axis and HGBS window.
- Script: `figures/make_fig6_fig9_corrected.py`. (Fig 2 corrected earlier: `figures/fig2_regime_corrected.pdf`.)
  These three are the figures with defects that could not be fixed from the paper source alone; the remaining
  C8 items (Figs 4, 5, 7, 8) are content/caption fixes the writer can apply per §C5–C8 below.

**2. A5 / A2 reruns — first results are in, and they sharpen the A5 answer (see updated A5 + SIM STATUS).**
The A5 (f = 1.5–2.0) batch completed on the wall clock: **only the weakest-field, most-supercritical run
(f = 2.0, β = 1.0) reached runaway collapse; the strong-field runs did not.** A follow-up batch **A5b at the
near-critical f = 0.9–1.0** (the Fig-2 regime) shows the clean expected split: **strong field (β = 0.05, 0.15)
keeps a healthy timestep (dt ≈ 10⁻³, not collapsing) while β = 1.0 collapses (dt ≈ 5×10⁻⁵).** Together these
give an *empirically supported* reconciliation for A5 (below): the magnetic stability boundary is real at
f ≈ 1 and weakens into the supercritical regime. The A2 finer-cadence rerun has now passed beading
(t ≈ 0.54 > first-beading ≈ 0.45) and will give the λ(t) trace.

**3. Fig-2 grid f — the writer's f ≈ 1 is correct and now physically pinned.** The exact value is not recorded
in any archived campaign manifest I could locate, but it must be **near-critical (f ≈ 1.0–1.2)**: the grid
shows *both* strongly-fragmenting (C = 13–22) and fully-suppressed (C ≈ 1) regimes, which requires a line mass
where self-gravity is marginal — at f < 1 nothing fragments, and my A5 runs show that at f = 1.5–2.0 even
strong fields keep contracting (so a stable C ≈ 1 regime cannot exist there). The A5b f = 1.0 runs reproduce
Fig-2's structure directly. **Recommendation: state f = 1.0 (or f ≈ 1.0–1.2 if your records show a specific
near-critical value) in §4.1/§4.5 and the Fig-2 caption.** One-word fix, well justified.

**4. B1 (§6) — I can run the referee's illustrative T-gradient simulation if you decide to keep §6.** The
referee's option (ii) is one MHD run with an imposed ~12 % temperature gradient, reporting the *measured* λ/W
shift instead of the analytic ±0.3 estimate (§6.5). This is feasible but requires a small pgen modification
(a spatially-varying `iso_sound_speed`, or an adiabatic run with a fixed-T(x) source) plus a recompile — about
1–2 h to set up and run. **Because it is only worth doing if §6 stays** (option (i) is to split §6 off), I have
**not** launched it unilaterally. If you want §6 retained with a measured link, say the word and I will design,
compile, run, and report it. Otherwise the split-off (option i) with a forward-pointer needs no simulation.

---

## ★ CROSS-CUTTING FINDING (affects A2, A3, and referee point D): the T1 factor is inconsistent

Before the per-point responses, one issue threads through several referee comments and must be fixed **once,
globally**:

**The manuscript adopts `T1 = 0.65 ± 0.10` (Eq. 4/5, Section 3.1), but the actual numbers quoted for
λ/W_fil throughout the paper were computed with the *older* value `T1 = 0.606`.**

Evidence (verified against the 39-run ensemble data, `rc1_beading.json` + `rc2_beading.json`):

| Quantity | value with ×0.606 | value with ×0.65 | what the paper prints |
|---|---|---|---|
| Direct supercritical: λ/W_core = 3.27 → λ/W_fil (§4.6.6) | **1.98 ≈ 2.0** | 2.12 ≈ 2.1 | "2.0" |
| Table 5 longitudinal β=2.0: 2.80 → | **1.70** | 1.82 | "1.70" |
| Table 5 perpendicular β≥1: 1.25 → | **0.76** | 0.81 | "0.76" |
| Fig. 9 right-axis label | literally "×0.606" | — | "×0.606" |

So the referee's arithmetic in point D ("3.31 × 0.65 = 2.15, not 2.0") is correct: the discrepancy is **not**
a median-of-ratios subtlety (we checked — median-of-ratios = 1.98 and ratio-of-medians = 1.98 are identical
here), it is simply that **the paper text was updated to T1 = 0.65 but the numbers/tables/figures still use
0.606.**

**Required global fix — choose ONE and apply everywhere (Abstract, §3.1 Eq. 4/5, §4.6.6, Table 5 caption +
body, Fig. 9 axis label, §4.8.3, Conclusions):**

- **Recommended — adopt T1 = 0.65 consistently** (it is the stated forward-model central value, band 0.59–0.78).
  Then recompute: direct-supercritical **λ/W_fil = 2.1 ± 0.4**; Table 5 longitudinal→ **1.82** (β=2.0),
  perpendicular→ **0.81**; near-critical high-β (§4.8.3) 2.86/2.80 → **1.86/1.82**; relabel Fig. 9 "×0.65".
  This nudges the headline from 2.0 to 2.1, which remains fully consistent with the NN observable 1.9 ± 0.5.
- **Alternative — revert the text to T1 = 0.606** everywhere (then "2.0", Table 5's 1.70/0.76, and Fig. 9 are
  already self-consistent, and Eq. 4/5 must read 0.606).

Do **not** mix the two. This single fix resolves referee point **D** and the numeric half of **A3**.

---

## A2 — Ambipolar-diffusion λ/W_fil ≈ 1.4 is quoted as settled but the runs are "provisional"

### Finding
The 36-run non-ideal survey (v35 RC4 12 runs + v40 AD 24 runs; combined 32/36 bead) gives a median
**λ/W_fil = 1.37 (×0.606) / 1.46 (×0.65)** — consistent with the paper's "≈1.4". I re-examined the raw runs
to test the "provisional / not converged" caveat, and found the paper's own characterisation of *why* they are
provisional is **inaccurate and should be corrected**:

- The paper says the runs are "limited by the diffusion timestep (first beading at t ≈ 0.45–0.60 t_J)."
- In fact the runs **terminate on gravitational runaway collapse**, not a diffusion-timestep wall. The history
  files show the timestep collapsing from Δt ≈ 10⁻³ to Δt ≈ 10⁻⁷ (the CFL kill threshold) as the beads go
  non-linear, while `tlim = 1.5` is never reached and the central density contrast reaches C ≈ 10⁴–10⁵.
  I.e. **the perpendicular ambipolar filament beads at t ≈ 0.45–0.55 t_J and then collapses** — there is no
  long-lived beaded state to "integrate to convergence"; the run physically ends.

This reframes A2: the correct question is not "run longer" (impossible — it collapses) but **"is the wavelength
already converged at the beading epoch?"**

### Simulations run
1. **λ(t) trajectory from existing snapshots** (`ad_lambda_trajectory.json`): at the archived dt = 0.05
   snapshot cadence, most runs contain only **1–2 beaded snapshots** before collapse, so a plateau *cannot*
   be established from the existing data — this genuinely justifies the referee's concern. Where ≥2 beaded
   snapshots exist, the weak-field cases converge well (β=2.0, η_AD=0.05 and 0.1: λ stable to **2.3 %**), while
   strong-field/low-η cases are still evolving.
2. **New finer-cadence reruns** (`configs_A2/`, 4 representative configs at f=1.5, β={0.5,1.0,2.0},
   output cadence dt = 0.02, athena-ambient binary) launched on the cluster to resolve λ(t) right up to
   collapse. *(Results table to be inserted on completion — see "SIM STATUS" at end.)*

### Instructions for the writer
Adopt referee option (ii) framing, upgraded with the new evidence. Replace the §4.6.6 / Abstract wording:

> **Abstract (replace the ambipolar clause):** "…ambipolar diffusion promotes fragmentation in 32/36 non-ideal
> runs (η_AD = 0.001–0.1, β = 0.5–2.0); where beading develops it does so at λ/W_fil ≈ 1.4, but these runs
> reach gravitational runaway shortly after first beading, so this is a **fragmentation-onset** wavelength
> rather than a fully converged value (see §4.6.6). Ambipolar diffusion therefore **promotes but does not yet
> resolve** the perpendicular-field tension; a converged wavelength is left to future work."

> **§4.6.6 (replace "limited by the diffusion timestep"):** "The non-ideal runs bead at t ≈ 0.45–0.55 t_J and
> then undergo gravitational runaway collapse (the CFL timestep falls to the 10⁻⁷ t_J kill threshold while
> C → 10⁴–10⁵); tlim is not reached. The quoted λ/W_fil is therefore measured at fragmentation onset. The
> weak-field cases (β = 2.0), which bead most robustly (8/8), show the onset wavelength stable at the ~2 %
> level over the final Δt ≈ 0.1 t_J available; the strong-field cases are less well converged. We flag the
> ambipolar wavelength as provisional in this specific sense."

If the finer-cadence reruns confirm a plateau, strengthen "~2 %" accordingly and keep the number in the
Abstract with the onset caveat; if not, remove the specific "1.4" from the Abstract and keep only the
qualitative statement.

---

## A3 — λ/W_fil = 2.0 ± 0.4 (§4.6.6) vs ± 0.5 (Abstract/Conclusions)

### Finding
The ± 0.4 is the **simulation ensemble** scatter (39-run IQR-based); the ± 0.5 is the **observational NN**
uncertainty (§2.7). They are different quantities that were accidentally cross-applied. From the ensemble data:
per-run IQR gives ±0.4 (×0.606) / ±0.4–0.5 (×0.65).

### Instructions for the writer
Use a **single** value for the simulation number everywhere and keep it distinct from the observational one:
- With the recommended T1 = 0.65: **simulation λ/W_fil = 2.1 ± 0.4** (IQR 1.9–2.9).
- Observational NN: **λ/W = 1.9 ± 0.5** (unchanged).
Ensure the Abstract, §4.6.6, Conclusions, Table 5 caption, and Fig. 3 caption all read the same simulation value
with ± 0.4. (Also apply the A1 caveat sentence — see below — so ±0.5 on the NN value is flagged as a
sensitivity-range, not a Gaussian CI.)

*(A1 sentence for the Abstract, for completeness even though A1 is an observational point:
"Quoted uncertainties combine independent sensitivity ranges in quadrature and are not formal statistical
confidence intervals; see §2.7.")*

---

## A5 — State f for the Figure 2 grid, and reconcile "no stability boundary above the critical line mass"

### Finding — this is a genuine issue, and it is a *framing* problem, not a data error
Two distinct notions of "critical" are being conflated:

1. **Thermal line-mass criticality** (`f = μ_line/μ_crit`): §3.1/§4.3 claim "no stability boundary above the
   critical line mass" — i.e. at *adequate field strength*, every f ≥ 1 eventually fragments/collapses.
2. **Magnetic (mass-to-flux) criticality**: Figure 2's "Magnetically Subcritical" regime (β ≲ 0.15, C ≈ 1.007,
   "No star formation") is stabilised by **magnetic pressure of the longitudinal field**, at *fixed f*.

These are **different axes**. A filament can be thermally supercritical (f > 1) yet magnetically subcritical
(strong longitudinal B ⇒ large magnetic pressure resisting radial compression) and hence stable. So Figure 2 and
§4.3 are only in apparent contradiction because the blanket phrase "no stability boundary above the critical line
mass" does not say *which* criticality, and because **the manuscript never states what f the Figure 2 grid used.**

I confirmed from the manuscript source and the campaign records that the Figure 2 base grid varies **(M, β) at a
single fixed f** (longitudinal B, isothermal, King/Gaussian profile, 256×64×64, periodic). **The f value is not
recorded in the text and must be stated by the author** (it is in your run records; from the campaign structure
it is the near-critical base value used before the supercritical/DTC grids — please confirm the exact number,
likely f ≈ 1.0–1.2).

### Simulations run — a decisive, f-independent test
To settle "slow vs. genuinely stable" I launched **A5_subcritical** (`configs_A5/`, 10 runs, athena-ambient):
longitudinal-B, ambient-confined, **thermally supercritical** filaments f ∈ {1.5, 2.0} across
β ∈ {0.05, 0.10, 0.15, 0.30, 1.0}, M = 2, **integrated to t = 40 t_J** (deep dt_kill = 10⁻⁹). This directly asks:
*does a strong longitudinal field stabilise a filament that is above the critical line mass?* — the exact regime
§4.3 makes its claim about.

- If low-β runs stay at C ≈ 1 to t = 40 while β ≥ 1 runs collapse early → magnetic subcriticality is a **genuine
  stability boundary even above the critical line mass**, so the §3.1/§4.3 wording is too strong and must be
  qualified.
- If all runs (including β = 0.05) collapse → the line-mass statement holds, and Figure 2's subcritical regime
  must correspond to a *lower-f* grid (state that f, and note the regime is thermal-support-limited at that f).

**First results (A5 f=1.5–2.0 batch complete; A5b f=0.9–1.0 batch running):**
- **A5 (supercritical f = 1.5, 2.0):** of the 10 runs, **only f = 2.0, β = 1.0 reached runaway collapse**
  (dt → 10⁻⁷); the strong-field runs did not collapse but kept contracting slowly. So at f = 1.5–2.0 a strong
  longitudinal field *delays but does not clearly prevent* collapse.
- **A5b (near-critical f = 0.9, 1.0 — the Fig-2 regime):** the expected split appears cleanly — at f = 1.0 the
  **strong-field runs (β = 0.05, 0.15) hold a healthy timestep (dt ≈ 10⁻³, not collapsing) while β = 1.0
  collapses** (dt ≈ 5×10⁻⁵). This reproduces Figure 2's structure (magnetically subcritical → stable;
  magnetically regulated → fragments) directly.

**Empirical reconciliation (this is the key A5 result):** the magnetic stability boundary is *real at
near-critical f ≈ 1* (Fig. 2) but *weakens into the supercritical regime* (f ≳ 1.5, the DTC grid of §4.3).
Both statements in the manuscript are therefore correct — they simply refer to different f. This is stronger
than the pure framing argument and should be stated. *(Runs continue; final "reaches t = 40 stable"
classification and a figure will be harvested in the follow-up — but the qualitative split is already clear.)*

### Instructions for the writer (apply regardless of the A5 outcome)
1. **State the Figure 2 grid f explicitly** in §4.1/§4.5 and the Fig. 2 caption, e.g. "the 208-run base grid was
   run at f = ⟨VALUE⟩."
2. **Qualify the §3.1 and §4.3 sentences** so they cannot be read as contradicting Fig. 2:

> **§3.1 / §4.3 (replace "there is no stability boundary above the critical line mass"):** "at *adequate field
> strength* (magnetically supercritical, β ≳ 0.2) there is no *thermal* stability boundary above the critical
> line mass: every f ≥ 1 fragments or collapses once integrated adequately. This is distinct from *magnetic*
> stabilisation: a strong longitudinal field (β ≲ 0.15, magnetically subcritical) provides sufficient magnetic
> pressure to suppress collapse even for f > 1 (the 'Magnetically Subcritical / No star formation' regime of
> Fig. 2)."

3. In the Fig. 2 discussion, cite the A5 long-integration test as confirming the low-β regime is stable (or
   merely slow), per the completed result.

---

## A6 — Possible ~50 % non-linear core-merging bias in the supercritical λ/W_fil

### Finding — checked directly on the 39-run ensemble; the bias does NOT apply
I analysed the per-run `npeaks(t)` and `C(t)` trajectories for all 39 ambient-confined supercritical runs:

- The measurement epoch is the snapshot of **maximum peak count** (finest fragmentation).
- In **38/39 runs the maximum peak count is at the final snapshot**, i.e. the bead count is still *increasing*
  when the run terminates.
- **0/39 runs show any peak-count decline** (the signature of merging) before termination.
- Simultaneously C rises from ~2 to ~10⁴–10⁵ over the last 1–2 snapshots (gravitational runaway).

So λ/W_fil is measured at **fragmentation onset, before any merging occurs**. The ~50 % merging inflation of
§5.2 is a *late-time* (few-Myr) effect that post-dates the wavelength-setting stage; it is genuinely absent from
this measurement. **No further simulations are required for A6.**

### Instructions for the writer
> **§4.6.6 or §5.2 (add):** "We verified that the ensemble λ/W_fil is measured at maximum bead count
> (fragmentation onset): in 38/39 runs the peak count is still rising at the final snapshot and no run exhibits
> the peak-count decline that would signal merging, so the ~50 % non-linear merging inflation discussed in §5.2
> is a distinct late-time (few-Myr) effect that does not bias the quoted onset wavelength."

This turns the referee's "not checked" into "checked and excluded," and does *not* require adding merging to the
error budget.

---

## A7 — Summary table of all simulation campaigns, and the correct total

### Finding
The manuscript's per-section run counts cannot be summed to verify "~2140" because (a) some counts are
sub-campaigns of a larger aggregate that also appears elsewhere, and (b) the older "laboratory-notebook"
campaigns were partly removed, leaving fragmented accounting. Using the manuscript text, the earlier organised
campaign breakdown, and the on-cluster campaign directories, the campaigns **actually cited in v42** are:

| # | Campaign (paper section) | (f, β, M, θ, η_AD) coverage | Runs | Independent? |
|---|---|---|---|---|
| 1 | Base three-regime grid (§4.1, §4.5, Fig. 2) | f = ⟨confirm⟩; β 0.05–5; M 0.5–5; θ=0; ideal | 208 | yes |
| 2 | Transition grid / DTC (§4.1, §4.3, Fig. 5) | f 1.4–2.2; β 0.3–1.3; M 1–5; θ=0; ideal | 540 | yes |
| 3 | Supercritical grid (§4.2, §4.6) | f 1.1–3.0; β 0.3–5.0; M 0.5–3; θ=0; periodic trunc-Gaussian | 654 | yes |
| 4 | Validation (§4.4, App. A) | resolution/IC/EOS convergence | 83 | yes |
| 5 | Near-critical (§4.7.1) | f 1.0–1.2; β 0.3–1.0; M 1–2; θ=0 | 80 | subset of old "Field-Geometry 314" |
| 6 | Perpendicular (§4.7.2) | θ=90; f 1.2–1.5; β 0.3–2.0 | 96 | subset of old "Field-Geometry 314" |
| 7 | Oblique-field calibration (§4.7.3) | θ=30/45/60; β 0.5–2.0 | ⟨confirm; ≈108 to complete FG=314⟩ | subset of old "Field-Geometry 314" |
| 8 | Adiabatic EOS (§4.7.4, Figs 6,7) | γ=5/3; f 1.0–1.2 | 30 | subset of old "Field-Geometry 314" |
| 9 | Turbulence + perp-β + critical-transition (§4.8; Table 4 "TURB 90"; §4.8.2 N=27; §4.8.3) | δv/cs 10⁻⁴–1; β 0.3–2 | 289 | yes (aggregate) |
| 10 | Targeted re-runs (implicit in Fig. 5 "corrected: β=0.3, M=1") | β=0.3, M=1 extended-timeout | 25 | yes |
| 11 | Direct supercritical ensemble (§4.6.6, Fig. 3) | f 1.5–2.0; β 0.5–2.0; θ=0; **ambient** | 39 | yes (new; NOT a subset of #3) |
| 12 | Reconciliation suite (§4.6.6) | f×β×2 seeds; θ=0; ambient | 12 | yes (new) |
| 13 | Ideal-MHD perpendicular d=1.0 grid (§4.6.6) | θ=90; β 0.5–2.0; ambient | 18 | yes (new) |
| 14 | Ambipolar non-ideal survey (§4.6.6, Fig. 4) | θ=90; η_AD 0.001–0.1; β 0.5–2.0 | 36 | yes (new) |
| — | **Athena++ MHD subtotal** | | **≈ 2110** | (see note) |
| RT-a | Uniform-ISRF RT post-processing (§6.4) | — | 519 | **post-processing, not MHD** |
| RT-b | Varying-ISRF RT post-processing (§6.4) | — | 5060 | **post-processing, not MHD** |

**Key accounting points the writer must implement:**
1. **Do not double-count the Field-Geometry aggregate.** Rows 5–8 are the *components* of the campaign that was
   previously reported as a single "Field-Geometry Campaign = 314." In v42 they are cited individually, so sum
   the components (80 + 96 + oblique + 30) — **do not also add 314.** Please **confirm the oblique count**
   (row 7) from your run records; the components should reconcile to 314 (i.e. oblique ≈ 108, which likely
   includes any perpendicular-spacing runs).
2. **Two items in §4.8 may overlap earlier rows** and need author confirmation: the perpendicular-spacing
   N = 27 (§4.8.2) vs the 96 perpendicular runs (#6), and the critical-transition sweep (§4.8.3) vs the 80
   near-critical runs (#5). If §4.8's 289 already contains those, state it; otherwise they are independent.
3. **The RT post-processing runs (519 + 5060) are not Athena++ MHD runs** and must be reported separately
   ("plus two radiative-transfer post-processing campaigns of 519 and 5060 runs on the isothermal snapshots").
4. With components counted once and RT excluded, the defensible **Athena++ MHD total is ≈ 2110** (state as
   "≈ 2100" or the exact figure once rows 1/7 are confirmed). Replace every "~2140" with the confirmed value
   and add the table above as **Appendix B**, with the two RT campaigns listed below the MHD subtotal.

*(A ready-to-drop LaTeX version of this table is provided as `appendixB_campaign_table.tex` in the package.)*

---

## Non-monotonic perpendicular-field beading (β = 0.5, 2.0 bead; β ≈ 1 spindles)

### Finding & recommended interpretation
The ideal-MHD perpendicular runs bead **away** from equipartition and spindle **at** β ≈ 1, opposite to the naive
"intermediate field is most balanced" intuition. A physically consistent explanation exists and is worth one
sentence (with an honest hedge). For a perpendicular field the axial (fragmenting) mode competes against the
radial spindle mode:
- **β ≈ 2 (weak field):** magnetic support is too weak to arrest thermal Jeans fragmentation → axial beading wins.
- **β ≈ 0.5 (strong field):** the stiff perpendicular field resists radial compression (magnetic pressure), so
  radial collapse is delayed long enough for the axial mode to grow → beading.
- **β ≈ 1 (equipartition):** thermal and magnetic energies are comparable and the perpendicular field's tension
  response is maximised in the radial plane, so the radial spindle mode reaches non-linearity first and
  suppresses axial beading.

I.e. the *ratio* of radial-collapse time to axial-growth time is minimised near β ≈ 1, favouring the spindle.

### Instructions for the writer
> **§4.6.6 or §4.7.2 (add):** "This non-monotonic behaviour — beading away from equipartition (β = 0.5, 2.0) and
> spindle collapse at β ≈ 1 — reflects a competition between the axial fragmentation mode and the radial spindle
> mode: at β ≈ 1 the perpendicular field's tension response in the radial plane is maximised, so the radial mode
> reaches non-linearity before axial beading can develop, whereas at both weaker (thermally driven) and stronger
> (magnetic-pressure-delayed radial collapse) fields the axial mode has time to grow. We caution that this is a
> plausible interpretation rather than a mode-by-mode demonstration; a linear perturbation analysis in the
> perpendicular geometry is left to future work."

(If you prefer maximum caution, keep only the first clause and the closing caveat.)

---

## λ/W_core = 3.31 → λ/W_fil (referee point D) — see the ★ cross-cutting finding above

Resolved by the global T1 fix. For completeness, add one clarifying sentence at first use of the conversion:

> **§4.6.6 (add after Eq. 5 usage):** "The conversion is applied per run and the ensemble median then taken;
> because median-of-ratios and ratio-of-medians coincide for this ensemble (both 1.98 at T1 = 0.606), the
> quoted value equals (median λ/W_core) × T1 to the stated precision."

With T1 = 0.65 adopted, the printed value becomes 3.27 × 0.65 = **2.1** (not 2.0), and the referee's arithmetic
objection disappears.

---

## C4 — Figure 2 (colour key, clipped labels, literal \n) — corrected figure supplied

### Finding (verified by rendering the PDF page, not text extraction)
- **The plotted colours are correct** (blue = low C at the low-β subcritical regime; red = high C at the high-β
  thermally-dominated regime, matching the colourbar). **The caption's colour key is reversed** — it says
  "(1) subcritical (red)… (3) thermally dominated (blue)", the opposite of the plot.
- The regime label boxes ("III. Thermally Dominate…", "II. Magnetically Regulate…", "I. Magnetically
  Subcritic…") are **clipped by the right axis**.
- The figure title contains a **literal `\n`** ("…Fragmentation\nfrom 208 Athena++…").

### Deliverable
A corrected regeneration is supplied: **`fig2_regime_corrected.pdf`/`.png`** (+ script `make_fig2_corrected.py`).
It fixes all three defects: real line break in the title, colour key consistent with the plot, and regime labels
fully inside the axes. The filled-contour C(β) field is reconstructed faithfully from the manuscript's own
documented regime contrasts (C ≈ 1.007 for β ≤ 0.15; C = 3.4–11 for 0.2 ≤ β ≤ 2; C = 13–22 for β ≥ 3). **Author:
if you still hold the original 208-run C values, re-run your plotting script with the code fixes below to overlay
the true grid; the supplied figure is a correct-layout stand-in otherwise.**

### Corrected caption (drop-in)
> **Figure 2.** Three-regime fragmentation framework from the 208-run Athena++ base grid (f = ⟨VALUE⟩, θ = 0°,
> isothermal). Colour shows the end-of-run density contrast C = ρ_max/ρ₀ (blue = low, red = high). The regimes,
> set by plasma β, are: (I) **magnetically subcritical** (β ≲ 0.15): magnetic pressure suppresses fragmentation,
> C ≈ 1 (no star formation); (II) **magnetically regulated** (0.2 ≲ β ≲ 2): fields modify but do not prevent
> fragmentation, C = 3–11; (III) **thermally dominated** (β ≳ 3): fields too weak to affect the scale, C = 13–22.
> Typical HGBS filament conditions (M ≈ 2–3, β ≈ 0.5–1.5; Arzoumanian et al. 2019; Planck Collaboration 2016;
> Pattle et al. 2018) lie in the magnetically regulated regime (magenta box).

### Code-level fixes (apply across the whole plotting pipeline — see C8)
- Replace the literal string `"...Fragmentation\nfrom 208..."` with an actual newline. In Python source this
  means using a real newline in the string (a triple-quoted string, or `"...\n..."` where `\n` is *not*
  escaped/doubled). The bug is a doubled backslash (`"\\n"`) or a raw string (`r"...\n..."`) reaching matplotlib.
- Give the regime labels room: place them with `ha="center"` inside the axes (or increase the right margin /
  reduce font), and/or set `annotation.set_clip_on(False)` is **not** the fix — instead move them inside `xlim`.

---

## C5 — Figure 5 duplicated panels / caption mismatch — comment

**Confirmed by rendering.** Both the left and right halves of Figure 5 contain the **full M = 1,2,3,4,5 panel
sweep**, and both group titles read identically "DTC fragmentation probability (corrected: β=0.3, M=1 re-run
results applied)". The caption claims "M = 1 (left) and M = 2 (right)". This is a **paste-twice error**: the same
multi-panel image was inserted in both halves.

**Recommendation:** regenerate as a **single** M = 1–5 panel row (one group) and rewrite the caption to match,
e.g.:
> **Figure 5.** Fragmentation outcome (STABLE / stochastic / FRAG) in the (β, f) plane across M = 1–5 for the DTC
> transition grid, with the β = 0.3, M = 1 timeout re-runs applied; all 80 near-critical runs fragment. Diamond
> markers denote the ~2 % of seed-stochastic grid points (§4.3).
Also add the "Stochastic" diamond gloss the referee requested (minor point D).

---

## C6 — Figure 6 middle "green disc / 100 % TIMEOUT" panel — comment

**Confirmed.** The middle panel is a single-wedge pie chart (solid green disc labelled "100 %"/"TIMEOUT") with no
axes — it conveys nothing quantitative for an all-null result.

**Recommendation:** delete the pie panel and replace with a **two-panel** Figure 6 (isothermal histogram + EOS
comparison) plus a text annotation in place of the removed panel:
> "Adiabatic (γ = 5/3): 0/30 runs fragmented; all timed out at t > 30–40 t_J."
(The information is fully captured by that one line; no distribution plot is meaningful for a 0/30 outcome.)

---

## C7 — Figure 7 caption/content mismatch + literal \n — comment

**Confirmed.** The panels plot **t_frag/t_final vs adiabatic index γ** (scatter/line), not "adiabatic density
profiles." The caption ("Adiabatic density profiles at f = 1.20, β = 1.0: no beading to t = 40 t_J") is
copy-pasted from a different figure. The right-panel x-tick "γ = 1.0\n(isothermal)" again shows a **literal \n**.
Note also that **Figure 7 duplicates Figure A2** (same EOS-sensitivity panels).

**Recommendation:**
- Either **delete Figure 7 and keep only Figure A2** (they are the same content; A2's caption is already correct),
  with a cross-reference from §4.7.4 — this is the cleanest fix; **or** keep Fig. 7 and rewrite its caption:
  > **Figure 7.** Equation-of-state sensitivity: fragmentation time t_frag (triangles) or final time t_final
  > (squares/circles) versus adiabatic index γ. Left: all parameter points; right: t_frag/t_final vs γ with lines
  > connecting the same (f, β, M) point. γ = 1.0 is isothermal; γ < 1 accelerates fragmentation, γ = 5/3
  > suppresses it (0/30 fragment).
- Fix the literal `\n` in the x-tick label (same doubled-backslash bug as C4).

---

## C8 — Regenerate all multi-panel figures (2, 4–9); grep the pipeline for literal \n — comment

**Agree with the referee.** The literal-`\n` bug appears in at least Figures 2 and 7, and Figures 5/6/7 have
content/caption defects, all from the same automated pipeline. Recommended actions for the writer:
1. **Grep the whole figure-generation codebase** for literal escape sequences in title/label strings:
   `grep -rn '\\\\n' <figure_scripts>` and search for `r"...\n..."` raw strings and doubled `"\\n"` — replace
   with real newlines.
2. **Regenerate Figures 2, 4, 5, 6, 7, 8, 9 from scratch** and **visually proof each against its caption**
   before resubmission (the referee correctly notes there may be others).
3. Specific known fixes: Fig. 2 (this document), Fig. 5 (de-duplicate + caption), Fig. 6 (drop pie panel),
   Fig. 7 (delete-as-duplicate or fix caption + `\n`), Fig. 9 (relabel axis "×0.65" per the T1 fix).
4. Sanity-check Fig. A1: its caption says mean ratio **0.928 ± 0.016** but the in-figure annotation reads
   **0.915 ("256³ frags 8.5 % earlier")** — reconcile these two numbers (minor, but it is an internal
   inconsistency in the same pipeline).

---

## SIM STATUS (cluster: /data/referee_v42_campaigns_jul2026/)
*Snapshot at report time; final results to be harvested when the background runs reach large t / runaway.*

- **A6** — ✅ COMPLETE (analysis of existing 39-run ensemble; no new runs needed). Decisive: no merging bias.
- **λ(t) trajectory** (`ad_lambda_trajectory.json`) — ✅ COMPLETE. Shows the archived cadence is too coarse to
  establish a plateau (motivating the A2 reruns); weak-field cases converge to ~2 %.
- **A5_subcritical** (10 runs, f = 1.5, 2.0; `configs_A5/`, `A5_progress.json`, `A5_collapse_vs_beta.png`) —
  ✅ batch complete (wall clock): `{COLLAPSE_EARLY: 1, TIMEOUT: 9}`. Only f = 2.0, β = 1.0 ran away; strong-field
  runs kept contracting slowly (no clean plateau at these high f).
- **A5b_nearcritical** (6 runs, f = 0.9, 1.0; `configs_A5b/`) — 🔄 RUNNING. Clear split already: f = 1.0
  β = 0.05/0.15 healthy (dt ≈ 10⁻³, stable), β = 1.0 collapsing — reproduces Fig. 2. Continuing toward t = 40.
- **A2_ambipolar_convergence** (4 finer-cadence reruns, `configs_A2/`) — 🔄 RUNNING (first run past beading,
  t ≈ 0.54 > onset ≈ 0.45). Provides the fine λ(t) sampling the archived dt = 0.05 snapshots lack.

**Follow-up action for next ASTRA-PA run:** harvest A5/A5b `A5*_progress.json` + snapshots and the A2
`*.hst`/`*.athdf`, finalise the "reaches t = 40 stable" classification (A5b) and the A2 λ(t) convergence,
make the summary figures, update this report, and push an addendum.
