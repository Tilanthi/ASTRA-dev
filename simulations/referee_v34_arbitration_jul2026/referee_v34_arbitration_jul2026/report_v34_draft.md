# Referee-v34 Response Campaigns — Boundary-Condition Arbitration, Equilibration, Turbulence, and Expanded T1 Calibration

**Date**: 2026-07-21 | **Executor**: astra-pa (autonomous, Glenn-authorized)
**Cluster**: astra-climate (GCP e2, 224 CPU) | **Total new sims**: 59 (32 arbitration/equilibration/turbulence + 27 T1 calibration)
**Binaries**: `/home/fetch-agi/athena-ambient/bin/athena` (NEW, pgen `filament_ambient`) and `/home/fetch-agi/athena/bin/athena` (existing, T1X only, for pipeline continuity)
**Data**: `/data/referee_v34_campaigns_jul2026/`

---

## 1. Motivation and referee-point mapping

The referee's major point 1 identifies §4.6.6 as the crux problem: the headline "supercritical filaments collapse radially before fragmenting" result flips under an independent replication that differs *only* in the transverse boundary condition (reflecting walls instead of external-pressure user BCs). The referee asks for a resolution — e.g. "boundary conditions coupling to an external pressurized/turbulent medium" — before the longitudinal λ/W ≈ 3.7 and the perpendicular-field tension can be trusted.

These campaigns directly address:

| Referee point | Campaign | What it measures |
|---|---|---|
| 1 (BC dependence; crux) | AM (arbitration) | bead-vs-spindle outcome as a function of transverse boundary distance d = {0.5, 1.0, 2.0} λJ × BC = {user (zero-gradient outflow), reflecting, periodic}, at identical resolution (64 cells/λJ) and ICs, in a **single binary** |
| 1 + paper's own "decisive follow-up" (IC equilibration) | EQ | same as AM but with a scaled-Ostriker initial profile (exact radial hydrostatic equilibrium at f=1 in isolation; imbalance ~ (f−1)), vs the paper's Gaussian |
| 4 (turbulence, timescale race) | TR | supercritical runs with physical turbulence (perturb_ampl = 1.0 → δv/cs ~ 1), testing whether the collapse-vs-fragmentation race flips |
| 5 (T1 = single point of failure) | T1X | 27-run expansion of the η_W forward-model calibration: f ∈ {0.5, 0.7, 0.9} × β ∈ {0.5, 1.0, 2.0} × seeds {42, 137, 251} (vs 18-run Plummer re-measurement and 6-run July E-suite) |
| 3 (external pressure confinement) | AM ambient reservoir | the widened transverse domain (up to 4×4 λJ) contains a pressurized ambient medium *inside* the computational domain, so confinement is provided dynamically by ambient gas rather than by the boundary |

## 2. Method: single-binary arbitration (removes the pgen confound)

The July R1/R2 comparison used two different binaries/pgens (filament_rce vs filament_supercritical). The new pgen `filament_ambient` supports BOTH BC families with conditional enrollment:

- `ix2_bc = user` → external-pressure zero-gradient ghost cells (identical implementation to filament_rce; p_ext_ratio = 0 → standard outflow)
- `ix2_bc = reflecting|periodic` → Athena++ built-ins

plus an IC selector `profile = gaussian | ostriker`. Everything else (perturbation spectrum, 12-mode k^−11/6 Kolmogorov seeding, W_core = 0.3, grav_mean_rho = 1.0, four_pi_G = 4π², HLLD, isothermal, FFT self-gravity) is shared. The July dichotomy is reproduced by the single binary:

| control (d = 0.5, f = 2.0, β = 1.0) | t_runaway (tJ) | matches July |
|---|---|---|
| gaussian + user | 0.146 | July "paper config" 0.14 ✓ |
| gaussian + reflecting | 0.632 | July replication 0.63–0.96 ✓ |
| ostriker + user | 0.186 | — |
| ostriker + reflecting | 0.601 | — |

## 3. Results

[TBF after campaign completion]

### 3.1 Arbitration grid (AM/EQ) — outcome matrix
### 3.2 Boundary-distance scaling of the collapse time
### 3.3 Beading wavelengths where present
### 3.4 Turbulence race (TR)
### 3.5 T1X: expanded η_W calibration

## 4. Point-by-point referee response material

### Point 1 (crux: BC dependence)
[TBF]

### Point 2 (extrapolation framing)
Editorial recommendation: [TBF]

### Point 3 (idealized BCs)
[TBF]

### Point 4 (turbulence)
[TBF]

### Point 5 (T1 systematic)
[TBF]

### Point 6 (4 regions only)
No new simulations possible — observational statistics issue. Text suggestion: state the n=4 limitation in the abstract or in the sentence where λ/W = 1.9 first appears, and make the ~28% combined systematic part of the headline number's error bar rather than a separate line item.

### Point 7 (scope/split)
Glenn's decision: keep single paper. Text suggestion: add a one-paragraph roadmap at the end of §1 that explicitly flags the paper as two coupled halves (observational reanalysis; MHD campaign) and states the internal dependency (the MHD half is conditional on the configuration issue resolved in §4.6.x).

### Minor points
- Symbol glossary: add a one-page table (W_fil, W_core, T1, η_W, λ/W flavors) after §1.
- r² = 0.999 quoted alongside "configuration-dependent" exponent: lead with the caveat, demote r².
- BH-FDR: mention in abstract/§6 intro, not only §6.5.

## 5. Disk cleanup (first task)
/data/referee_followup_campaigns_jul2026: 179 GB → 5.1 MB (1,286 .athdf + .xdmf deleted; .hst, configs, analyzers, logs retained). /data now 446 GB free. All June-July analysis products had already been pushed to GitHub.

## 6. Reproducibility
- pgen: filament_ambient.cpp (attached in package)
- configs: configs_v34/ (59 .athinput + manifests)
- runner: run_campaign.py (CFL-runaway polling, dt_kill = 1e-7)
- analyzers: analyze_v34.py, t1_forward_model_v3.py, synthetic_hgbs_forward_model.py
