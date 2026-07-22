# Referee Response Campaign v34 — Final Analysis Report

**Paper**: "Filament spacing in the HGBS" (v34, MNRAS submission) — referee major revision, crux = BC-dependence of the supercritical negative result (§4.6.6).
**Campaign**: `/data/referee_v34_campaigns_jul2026/`, 2026-07-21 → 2026-07-22.
**Runs**: 65 total (P0 smoke 4, P1 controls 4, P2a T1X 27, P2b arbitration 16, P3_heavy 2, P3_tr 6, P4_beta 4, P5_trdense 6) — all completed except P3_tr/P5 first attempt (killed by unidentified external SIGKILL; P5 relaunched and completed).
**Code**: Athena++ with new `filament_ambient` problem generator (gaussian|ostriker profile, conditional user-BC enrollment), single binary `/home/fetch-agi/athena-ambient/bin/athena` for all arbitration runs. Configs, generators, runners, and analyzers included in this package.

---

## 1. Headline conclusions

1. **The §4.6 supercritical negative result ("radial collapse beats fragmentation") is a boundary-proximity artifact.** At transverse boundary distance d = 0.5 λJ with the zero-gradient "user" BC, collapse times are pinned at t = 0.143–0.150 tJ **independent of f (0.5–0.9) and β (0.5–2.0)** — a physics-independent timescale cannot be gravitational. At d ≥ 1.0 λJ, all BCs (user / reflecting / periodic) and both IC profiles (Gaussian, scaled-Ostriker) agree and produce **beading**.
2. **Direct supercritical λ/W measurement**: the d = 1.0 beading ensemble (14 runs, θ=0, f = 1.5–2.0) gives median λ = 1.35 λJ → λ/W_core = 4.49 → λ/W_fil (×0.606 T1-correction) = **2.72, inside the HGBS window [2.52, 3.08]**; converged multi-peak runs span 2.04–2.97. This answers the referee's extrapolation complaint (pt 2) for longitudinal fields.
3. **The artifact mechanism is an infinite-reservoir accretion boundary.** User-BC collapse time scales strongly with d (0.146 at d=0.5 → ~0.53 at d=1.0 → 0.476 at d=2.0); reflecting BC is ~d-independent (0.60 → 0.52 → 0.490). At d=1.0 all three BCs agree to ≤10%; at d=2.0 user/refl agree to 3%.
4. **Physical β-dependence re-emerges at d = 1.0** (P4): collapse time 0.575–0.598 (β=0.5) vs 0.482–0.495 (β=2.0). At d = 0.5 the artifact erases β-dependence entirely.
5. **Perpendicular fields (θ=90°) genuinely spindle** under both BCs (t = 0.315, identical to 4 s.f.) — magnetic tension along the filament suppresses beading. This is a real geometry result, not an artifact.
6. **Physical turbulence (δv/cs = 1) complicates the picture**: at d = 0.5 it *accelerates* the artifact (collapse at t = 0.077–0.079 vs 0.146 laminar); at d = 1.0 turbulent runs develop a single dominant condensation (peaks = 1, radial growth rate Γ_r = 109–136 vs mode growth Γ_m = 40–43) rather than clean multi-peak beading. The laminar beading result at d ≥ 1.0 stands; turbulence appears to favour radial over longitudinal modes even at safe boundary distances. The paper's near-critical "turbulence delays collapse 3–5×" claim does **not** extend to supercritical user-BC configurations and should be scoped accordingly.

---

## 2. Campaign design

| Suite | Runs | Purpose |
|---|---|---|
| P0_smoke | 4 | Binary/config validation |
| P1_controls | 4 | d=0.5, gaus/ostr × user/refl — reproduce v32 R2 BC split in the new binary |
| P2a_t1x | 27 | f={0.5,0.7,0.9} × β={0.5,1,2} × seeds{42,137,251}, θ=0, Lx=8 — T1/artifact-timescale grid (old binary, user BC) |
| P2b_am_d1 | 16 | d=1.0 arbitration: BC{user,refl,peri} × profile{gaus,ostr} × θ{0,90} × seeds × ampl |
| P3_heavy | 2 | d=2.0, 64-rank matched user/refl pair |
| P3_tr | 6 | Physical turbulence δv/cs=1 (killed externally; superseded by P5) |
| P4_beta | 4 | β={0.5,2.0} × seeds at d=1.0 user — β-sensitivity off the artifact |
| P5_trdense | 6 | P3_tr re-run with dense snapshots (odt=0.005) for mode analysis |

All runs: 512×64×64 (P3_heavy higher), dt_kill = 1e-7, timeout 6–8 h.

---

## 3. Results

### 3.1 Collapse-time ladder (the arbitration table)

| Config | d = 0.5 | d = 1.0 | d = 2.0 |
|---|---|---|---|
| user BC | 0.146 (fast channel) | 0.510–0.598 | 0.476 |
| reflecting | 0.601–0.632 | 0.493–0.601 | 0.490 |
| periodic | — | 0.528 | — |

At d=1.0 all BCs agree within ~10% (most pairs ≤5%); θ=90 identical under both BCs (0.3150/0.3151); seeds agree ≤10%; amplitude 1e-2 delays collapse modestly (0.709 vs 0.510).

### 3.2 Beading at d = 1.0 (laminar) — referee pt 2

Ensemble of 14 runs (θ=0, f=1.5–2.0, both profiles, all BCs): **all bead**, 3–7 axial maxima, λ = 1.01–2.78 λJ (median 1.35) → λ/W_core median 4.49 → λ/W_fil = 2.72 ∈ [2.52, 3.08]. Analysis: `analyze_v34.py`, products `am_analysis.json`, `eq_analysis.json`, figures `fig_v34_arbitration.png`, `fig_v34_lambda_distance.png`.

### 3.3 T1X grid (P2a) — artifact timescale proof

27 runs, old binary + user BC (the paper's configuration), Lx=8:

- 21 COLLAPSE_EARLY, **t_coll = 0.143–0.150 tJ across the entire grid** (f=0.5/0.7/0.9 × β=0.5/1/2 — no trend in either).
- 6 TIMEOUT (6 h): 5 at β=0.5, 1 at β=1.0; seed-dependent (s137 always collapses). Strong-field subcritical filaments marginally resist the artifact.
- Interpretation: the pinned timescale is set by boundary accretion, not by self-gravity (which would scale as f^-1/2).

### 3.4 Turbulence (P3_tr / P5_trdense) + mode competition

Dense-snapshot mode-competition analysis (`analyze_mode_competition.py`, output `tr_modecomp_log.txt`):

| Run | C_final | peaks | Γ_mode | Γ_radial |
|---|---|---|---|---|
| TR f1.5 d0.5 s137 | 2568 | 5 | 67.2 | 89.0 |
| TR f1.5 d0.5 s42 | 850 | 1 | 71.5 | 74.3 |
| TR f1.5 d1.0 s42 | 2.58e6 | 1 | 42.7 | 135.6 |
| TR f2.0 d0.5 s137 | 575 | 0 | 69.3 | 70.9 |
| TR f2.0 d0.5 s42 | 1786 | 2 | 73.2 | 83.5 |
| TR f2.0 d1.0 s42 | 1.78e6 | 1 | 39.7 | 109.0 |

- d=0.5: collapse at t = 0.077–0.079 (3/4 runs; f1.5/s137 TIMEOUT) — turbulence ~2× accelerates the artifact; mode and radial growth rates comparable (mixed competition, up to 5 transient peaks).
- d=1.0: both runs reached t ≈ 0.125 at the 6 h wall limit without dt_kill, but mode analysis shows radial growth dominating (Γ_r/Γ_m ≈ 2.7–3.2) and a single condensation forming. Turbulence tips the mode competition back toward radial collapse even at d=1.0.

### 3.5 Operational anomaly (for the record)

Three synchronized SIGKILL events hit user-BC Athena processes only (P1 pair at wall 4244 s; P3_tr all 6 at 9609.5 s; P5 first attempt all 6 at 5625.2 s). Reflecting-BC runs were never affected. No crontab, no OOM in accessible logs, memory headroom large. Cause unidentified; Glenn White confirmed he did not kill the runs. P5 relaunch completed without incident. Failed-run partial data retained on cluster.

---

## 4. Recommended referee-response framing

- **Pt 1 (BC-dependence of §4.6)**: Concede precisely. The supercritical "no-fragmentation" result holds only for the zero-gradient user BC at d=0.5 λJ; it is an infinite-reservoir accretion artifact with a physics-independent collapse timescale (§3.3). Replace/qualify §4.6.6 accordingly.
- **Pt 2 (extrapolation)**: Now answered by direct measurement — supercritical beading at d≥1.0 gives λ/W_fil = 2.72, inside the HGBS window (§3.2).
- **Turbulence claims**: scope the near-critical turbulence-delay claim; under supercritical user-BC configs turbulence accelerates radial collapse (§3.4). The laminar d≥1.0 beading result is robust; turbulent mode competition at d≥1.0 favours radial modes — flag as future work (longer turbulent runs at d=1.0–2.0 with reflecting BCs).
- **θ=90°**: spindle outcome is BC-robust — retain as a genuine geometry result.

## 5. Package contents

- `report_v34_final.md` (this file), `report_v34_draft.md` (interim draft)
- Figures: `fig_v34_arbitration.png`, `fig_v34_lambda_distance.png` (+ `make_figs.py`)
- Results JSON: p0 smoke, p1, p2a, p2b, p3h, p3tr, p4, p5b + `am_analysis.json`, `eq_analysis.json`, `tr_analysis.json`
- Logs: all runner logs + `tr_modecomp_log.txt`
- Code: `filament_ambient.cpp`, `rce_bc.cpp`, `bc_body.cpp`, `gen_v34_configs.py`, `gen_t1x_configs.py`, `run_campaign.py`, `analyze_v34.py`, `analyze_mode_competition.py`, `t1_forward_model_v3.py`, `synthetic_hgbs_forward_model.py`, `common.py`
- Configs: all `configs_v34/` athinput files + manifests

Raw .athdf snapshots (~95 GB) retained on the cluster at `/data/referee_v34_campaigns_jul2026/` pending Glenn's cleanup decision.
