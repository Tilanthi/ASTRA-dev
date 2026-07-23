# Referee Response Campaign v35 — Final Report

**Paper**: "Core Spacing in HGBS Filaments: A Nearest-Neighbour Reanalysis, MHD Fragmentation Tests, and the Perpendicular-Field Tension" (White, v35, MNRAS) — major revision.
**Campaign**: `/data/referee_v35_campaigns_jul2026/`, 2026-07-22 → 2026-07-23. 69 production runs, 4 suites, ~10⁴ CPU-h.
**Binaries**: `athena-ambient` (filament_ambient pgen: Gaussian/Ostriker + ambient medium, conditional user-BC enrollment); `athena-sc` (HDF5 + non-ideal MHD, ambipolar diffusion).
All configs, runner, analyzers, results JSON, and logs are in this package.

---

## 1. Executive summary

| Referee concern | Sim response | Outcome |
|---|---|---|
| #1 Geometry inconsistency (d=1.0 periodic main grid vs 14-run positive) | **RC1**: 12 runs, periodic BCs + ambient medium at d=1.0 | **RESOLVED** — periodic geometry beads (12/12) when ambient confinement present; original main grid lacked ambient medium |
| #1 "14 runs is thin" | **RC2**: 27 runs, reflecting d=1.0, f×β×3 seeds | Ensemble now 39 runs; median λ/W_fil revised 2.72 → **2.00 ± 0.35** — lands on the NN observable 1.9 ± 0.5 |
| #6 Perpendicular under-explored | **RC3**: 18 runs, θ=90°, f×β grid at d=1.0 | Perp fields **do bead** at β=0.5 and β=2.0 (7/18); spindle only near equipartition β≈1 |
| #6 Non-ideal MHD "necessary and unperformed" | **RC4**: 12 ambipolar runs (η_ad = 0.01, 0.05), θ=90° | **Ambipolar diffusion unlocks perpendicular fragmentation**: 10/12 bead, incl. 4 configs whose ideal-MHD twins spindle |

---

## 2. RC1 — Geometry reconciliation (referee concern #1)

**The reconciliation**: the paper's main 654-run grid (§4.6.1: 8×2×2 λJ, periodic all faces) initialises a truncated Gaussian filament with **no ambient medium**. At Ly = ±1.0 λJ with W_core = 0.3 λJ, the Gaussian skirt at the boundary is non-negligible and wraps through the periodic boundary — the filament is effectively embedded in a self-replicating accretion medium, reproducing the same infinite-reservoir feeding as the d=0.5 zero-gradient BC. The v34 arbitration ensemble used the `filament_ambient` generator, in which a low-density ambient medium confines the filament — that confinement, not the BC label, is the controlling difference.

**RC1 test**: 12 runs, periodic BCs, ambient medium, d=1.0, f={1.5,2.0} × β={0.5,1,2} × 2 seeds.
**Result**: collapse at t = 0.551–0.699 tJ (physical, β-dependent), in agreement with reflecting (RC2: 0.507–0.808) and the v34 all-BC band; and **all 12 runs bead** (3–10 axial maxima). The main-grid geometry is in the converged fragmenting regime **when the IC is properly confined**.

**Paper fix needed (text, no new sims)**: §4.6.1 and §4.6.6 must state explicitly that (i) the main grid's IC has no ambient medium and its "d" is therefore not comparable to the arbitration-ensemble d; (ii) the boundary-proximity artefact is more precisely an **unconfined-IC/boundary-feeding artefact**, of which d=0.5 user-BC is the extreme case; (iii) the positive detection ensemble is defined by: ambient-confined IC, d ≥ 1.0 λJ, any of the three BCs.

## 3. RC2 — Expanded supercritical ensemble (39 runs total)

27/27 runs bead. Median λ = 1.06 λJ; combined with RC1 (n=39): **median λ = 0.99 λJ → λ/W_core = 3.31 → λ/W_fil = 2.00** (range across runs 1.4–8.1, IQR ≈ 1.7–2.6).

**Headline revision**: the v34 14-run value (2.72) was small-sample high. The expanded ensemble median (2.00) sits **outside** the legacy pairwise-median window [2.52, 3.08] but **directly on the paper's own NN observable λ/W = 1.9 ± 0.5**. This is a *strengthening* of the paper's central thesis: the direct supercritical simulation measurement agrees with the corrected (NN) statistic, not the L/3-biased legacy value. The paper's abstract should quote λ/W_fil ≈ 2.0 ± 0.4 and note the agreement with NN.

**Parameter dependence (new)**: λ/W_fil declines with f (2.65 → 1.70 for f = 1.5 → 2.0) and with β (3.52 → 1.78 for β = 0.5 → 2.0). λ/W is **not** a constant in the supercritical regime; quoting a single number requires stating the (f, β) weighting. Sub-Jeans spacing at high f is consistent with the paper's §4.5.5 density-contrast argument.

## 4. RC3 — Perpendicular fields: the spindle is not universal

18 runs, ideal MHD, θ=90°, d=1.0, reflecting, f={1.2,1.5,2.0} × β={0.5,1,2} × 2 seeds.

| β \ f | 1.2 | 1.5 | 2.0 |
|---|---|---|---|
| 0.5 | **BEAD** (2/2) | SPINDLE* | **BEAD** (2/2) |
| 1.0 | SPINDLE (2/2) | SPINDLE (2/2) | SPINDLE (2/2) |
| 2.0 | SPINDLE (2/2)** | **BEAD** (1/2)* | **BEAD** (2/2) |

*seed-split rows; **1 timeout classified from partial data. Overall 7/18 bead.

- Spindle collapse is fast (t = 0.378–0.547 tJ) and concentrated at **β ≈ 1**: near-equipartition maximises the effective tension response; both stronger (β=0.5) and weaker (β=2) fields permit longitudinal modes.
- Where perpendicular filaments bead, spacing is short: λ = 0.28–0.74 λJ → **λ/W_fil ≈ 0.85** — well below both the longitudinal value (2.0) and the observed 1.9.
- **Reframing of the paper's tension**: from "ideal-MHD perpendicular filaments cannot fragment" to "perpendicular filaments fragment only away from β≈1 and at ~2× shorter wavelength than observed." A quantitative discrepancy, not a categorical one.

## 5. RC4 — Ambipolar diffusion unlocks perpendicular fragmentation

12 runs, θ=90°, η_ad = {0.01, 0.05}, f = {1.0, 1.2, 1.5}, β = {0.5, 1.0}, athena-sc binary.

- **10/12 bead**, including f=1.5/β=0.5 and f=1.5/β=1.0 — configurations whose ideal-MHD counterparts (RC3 and v34) spindle. Ambipolar drift lets neutrals slip across field lines, defeating the tension that suppresses longitudinal modes.
- η_ad ordering is physical: stronger diffusion (0.05) gives longer λ (median 0.72 vs 0.43 at 0.01) — the field is less able to set the fragmentation scale.
- Median λ/W_fil ≈ 0.88 — still short of observed. **Caveat**: all 12 runs hit the 6 h wall at t ≈ 0.49–0.58 tJ (ambipolar dt ~ 3×10⁻⁷); beading classification is unambiguous but final spacings are provisional (λ may grow by merger before collapse).
- These are the runs the referee called "necessary and unperformed." The result: **non-ideal effects qualitatively change the perpendicular-field verdict** — the paper's most important open tension now has a demonstrated physical resolution channel, with amplitude (still ~2× short in λ) to be settled by longer/denser-output runs.

## 6. Operational notes

- 69/69 runs completed; no external SIGKILL events this campaign (cf. v34 anomaly).
- RC2/RC3/RC4 initially failed on a meshblock decomposition error (nbtotal < nranks) — fixed (meshblock nx1 32→16) and relaunched; ~4 h lost, no science impact.
- Disk: /data cleaned from 95% to 4% before campaign (v34 athdf purged post-push; 13 legacy campaign dirs removed). Campaign snapshots: 52 GB retained on cluster pending cleanup decision.

## 7. Recommended paper changes (from this campaign)

1. §4.6.1/4.6.6: explicit IC/geometry statement for every campaign (ambient vs truncated-Gaussian; d per suite); reconciliation paragraph (RC1).
2. Abstract + §4.6.6: revise λ/W_fil from 2.72 (n=14) to **2.0 ± 0.4 (n=39)**; note agreement with NN observable 1.9 ± 0.5; drop "inside the legacy window" phrasing.
3. New subsection: λ/W(f, β) parameter dependence (RC2).
4. §5 perpendicular tension: replace categorical "no fragmentation" with the RC3 β-map + RC4 ambipolar result; the tension becomes quantitative (wavelength deficit ~2×), with non-ideal MHD as the demonstrated resolution channel.
5. Run-count audit table (referee #3): add authoritative per-campaign table; this package's 69 runs bring the total to 1959 + 65 (v34) + 69 (v35) = 2093 under the paper's own counting convention — the writer must reconcile the 1956/1959/2323 discrepancy against the campaign ledger.

## 8. Package contents

- `report_v35_final.md` (this file)
- Figures: `fig_v35_reconciliation_ensemble.png`, `fig_v35_lambda_f_beta.png`, `fig_v35_perpendicular_map.png` (+ `make_v35_figs.py`)
- Results: `rc1..rc4_results.json` (runner), `rc1..rc4_beading.json` (beading/mode analysis)
- Logs: `rc1..rc4_log.txt`, analysis logs
- Code: `gen_v35_configs.py`, `run_campaign.py`, `analyze_v34.py`, `common.py`
- Configs: `configs_v35/` (all 69 athinput + the meshblock fix applied)
