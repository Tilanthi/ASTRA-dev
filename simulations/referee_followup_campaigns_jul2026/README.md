# Referee Follow-up Campaigns (Jul 2026)

Two Athena++ campaigns that **fully close** (rather than tone down) referee
concerns #4 and #5 on the HGBS filament-spacing paper, by adding the independent
diagnostics the referee asked for.

Both use the **validated configuration** from the Jul 2026 audit (transverse
`user` boundary conditions, required by the current Athena++ binary; see
`simulations/referee_audit_response_jul2026/`).

| Campaign | Referee point | What it tests | Runs |
|---|---|---|---|
| **A** — density-contrast `t_frag` validation | #4 | Is `1/t_frag ∝ f^0.39` physical, or a CFL-trigger artifact? | 16 |
| **B** — synthetic-HGBS T1 forward model | #5 | Measure T1 directly by observing simulated filaments through a synthetic HGBS pipeline | 11 |

Total ~27 short runs (each collapses in ≲ a few minutes; overnight wall-clock ≪ the audit's 6 h/run).

---

## Files

```
referee_followup_campaigns_jul2026/
├── README.md                              ← this file
├── common.py                              ← shared .athinput builder (validated config)
├── generate_campaignA_tfrag_configs.py    ← Campaign A config generator
├── generate_campaignB_t1_configs.py       ← Campaign B config generator
├── run_campaign.py                        ← shared MPI/HST-polling runner
├── analyze_campaignA_density_contrast.py  ← Campaign A: t(contrast) scaling fits
├── synthetic_hgbs_forward_model.py        ← Campaign B: project→beam→Plummer T1 pipeline
└── configs/                               ← generated .athinput files + manifests
```

---

## Campaign A — density-contrast validation of the `t_frag` scaling (referee #4)

**The referee's concern.** The paper reports `1/t_frag ∝ f^0.39` (r²=0.999), but
`t_frag` there is defined by a CFL-timestep-crash trigger. The referee wants the
scaling checked against a physically motivated collapse diagnostic.

**What A does.** Re-runs an f-grid `{1.1, 1.3, 1.5, 2.0, 2.5, 3.0}` (β=1.0, two
seeds) plus a β-spread, with **dense HDF5 output** (Δt=0.005), so the time to
reach fixed density contrasts (10, 100, 1000) can be measured from the snapshots
independently of the CFL trigger. The analyzer also reads the CFL-trigger time
(dt ≤ 1e-8, matching the paper) from each `.hst`, then fits `1/t ∝ f^α` for both
diagnostics. **If the density-contrast exponents agree with the CFL exponent
(~0.39), the scaling reflects physical collapse dynamics, not the trigger.**

## Campaign B — synthetic-HGBS T1 forward model (referee #5)

**The referee's concern.** T1 (=0.606, Plummer-corrected ~0.71) dominates every
simulation–observation comparison but was derived via a Gaussian-convolution
proxy; the referee wants the simulated filaments forward-modelled through a
complete synthetic HGBS pipeline.

**What B does.** Runs an `f × β` grid, then `synthetic_hgbs_forward_model.py`
builds a synthetic column-density map for each filament, convolves it with the
HGBS 18″ beam (mapped to λ_J units, tested at three beam widths spanning near/far
distances), and fits the radial profile with the **same Plummer-2 model used on
real HGBS data** — yielding `W_fil` (Plummer FWHM), `W_gauss`, and `W_form`
directly, hence `T1 = W_form / W_fil` and `ratio_GP = W_gauss / W_plum`, with no
proxy. Compares to the paper's 0.606 / 0.71 / 1.17.

---

## Cluster workflow

```bash
# 0. on the local Mac, generate the configs (already in this package, but to regenerate):
python3 generate_campaignA_tfrag_configs.py
python3 generate_campaignB_t1_configs.py

# 1. transfer this directory to the cluster, then:
cd referee_followup_campaigns_jul2026

# 2. Campaign A (low dt_kill so dense snapshots cover the contrast crossings):
python3 run_campaign.py --athena_path /path/to/athena \
    --config_dir configs --max_concurrent 12 --dt_kill 1e-6 \
    --resultsout campaignA_results.json
python3 analyze_campaignA_density_contrast.py
#   -> campaignA_density_contrast_timing.json

# 3. Campaign B:
python3 run_campaign.py --athena_path /path/to/athena \
    --config_dir configs --max_concurrent 12 --dt_kill 2e-5 \
    --resultsout campaignB_results.json
python3 synthetic_hgbs_forward_model.py
#   -> campaignB_synthetic_hgbs_t1.json
```

`run_campaign.py` discovers every `.athinput` under `--config_dir` (pass
`configs/A_main_fgrid` etc. to run one suite at a time). It polls each run's
`.hst` every 20 s and stops it once `dt ≤ dt_kill` for three consecutive polls
(radial-collapse runaway); Athena++ writes the HDF5 snapshots up to that point.

## Notes for the cluster

* `--athena_path` must point at the **validated** Athena++ binary (the one that
  requires transverse `user` BCs — same binary as the audit).
* The problem generator is the paper's filament generator
  (`four_pi_G`, `f_line_mass`, `plasma_beta`, `theta_deg`, `mach_number`,
  `perturb_ampl`, `random_seed`, `W_core`), with λ_J = 1.
* Each run is short (collapse well before `tlim`); the whole package is an
  overnight job at most.

## What to send back for paper integration

* `campaignA_density_contrast_timing.json` — per-run crossing times + the fitted
  exponents for each diagnostic (the key output for referee #4).
* `campaignB_synthetic_hgbs_t1.json` — per-run `T1`, `ratio_GP`, beam dependence
  (the key output for referee #5).

The paper will then either (A) state that the f-scaling is confirmed physical,
or tone it down further if the exponents disagree; and (B) replace the
Gaussian-proxy T1 with the forward-modelled value, or confirm 0.606/0.71.
