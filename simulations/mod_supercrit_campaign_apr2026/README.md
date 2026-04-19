# Moderate Supercriticality Campaign — April 2026

## Overview
5×5 parameter grid exploring the **moderate supercriticality regime** (f ≈ 2–3)
of magnetised filament fragmentation.

**f = √(2/β)** = dimensionless mass-to-flux ratio (Alfvénic criticality parameter)

## Parameter Grid

| Parameter | Values |
|-----------|--------|
| f (mass-to-flux) | 1.5, 2.0, 2.5, 3.0, 3.5 |
| β (plasma beta) | 0.889, 0.500, 0.320, 0.222, 0.163 |
| M (Mach number) | 1.0, 2.0, 3.0, 4.0, 5.0 |
| **Total sims** | **25** |

## Physical Context
- **f_crit = √3 ≈ 1.73**: stability threshold (β_crit = 2/3)
- All f values here are above f_crit → firmly in the gravitationally supercritical regime
- f ≈ 1.5: just above critical (weakly supercritical)
- f ≈ 3.5: strongly supercritical (rapid fragmentation expected)

## Sim IDs
`MSC_f{ftag}_M{mtag}` — e.g., `MSC_f2p0_M3p0`

## Setup (identical to sweep campaigns)
- **Code**: Athena++ `filament_spacing` problem
- **Grid**: 256×64×64, domain [-8,8]×[-2,2]×[-2,2] in λ_J
- **MHD**: B₀ along x₃ (perpendicular to fragmentation axis x₁)
- **Self-gravity**: FFT solver, four_pi_G = 4π² = 39.478418
- **Isothermal**: c_s = 1, γ = 1
- **Seeded perturbation**: λ = 2.0 λ_J, amplitude 0.01
- **End time**: t_lim = 4.0 t_J
- **MPI**: 32 procs per sim (32 meshblocks of 32³)
- **Concurrent**: 7 sims per batch (7×32=224 vCPUs)

## Execution
Run from agent container:
```bash
python3 /shared/ASTRA/simulations/mod_supercrit_campaign_apr2026/scripts/launch_mod_supercrit.py
```

Then after completion, on astra-climate:
```bash
python3 /home/fetch-agi/analyse_mod_supercrit.py
```

## Output
- `/home/fetch-agi/mod_supercrit/C4_mod_supercrit/MSC_*/` — HDF5 snapshots
- `/home/fetch-agi/analysis_mod_supercrit/` — JSON + 5 figures
- `/shared/ASTRA/simulations/mod_supercrit_campaign_apr2026/results/` — synced results

## Overlap with Previous Campaigns
Three M=3 points overlap with the β-sweep (C1C2):
- MSC_f2p0_M3p0 ↔ SWEEP_M30_b0p50
- MSC_f2p5_M3p0 ↔ SWEEP_M30_b0p32
- MSC_f3p0_M3p0 ↔ SWEEP_M30_b0p22

These serve as cross-validation between campaigns.

## Figures
1. **fig1_Ct_by_f** — C(t) time series, 5 panels (one per f), lines coloured by M
2. **fig2_heatmaps** — C_final and N_cores as 5×5 heatmaps
3. **fig3_Cfinal_vs_params** — C_final vs f (by M) and C_final vs M (by f)
4. **fig4_density_profiles_5x5** — All 25 1-D density profiles at t=4
5. **fig5_Cfinal_vs_f_comparison** — Comparison with β-sweep campaign at M=3
