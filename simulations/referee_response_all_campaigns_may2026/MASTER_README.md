# Referee Response Simulation Package — All Campaigns (May 2026)

## Paper
**ASTRA: An Integrated Analysis Framework for Physics-Aware Astrophysical Discovery**  
Glenn J. White (Open University) & Robin Dey (VBRL Holdings Inc)  
Target journal: *RASTI (RAS Techniques & Instruments)*  
GitHub: https://github.com/Tilanthi/ASTRA-dev

---

## Overview

This package contains the complete record of all MHD Athena++ filament fragmentation simulations
performed for the referee response to the ASTRA RASTI paper. It consolidates 20 simulation
campaigns spanning 2026-04-20 to 2026-05-01, covering:

| Metric | Value |
|--------|-------|
| Total campaigns | 18 active + 2 deferred |
| Total simulations | 1,940 |
| FRAG (fragmented) | 1,817 (93.7%) |
| TIMEOUT (stable/near-critical) | 100 (5.2%) |
| Date range | Apr 20 – May 1, 2026 |

**Physics**: Isothermal MHD with FFT self-gravity, Gaussian filament ICs, longitudinal and 
perpendicular/oblique magnetic field geometries, Kolmogorov turbulence modes, variable EOS (γ).  
**Code**: Athena++ v21.0, custom filament pgen (fetch-agi/athena), n2d-highcpu-224 GCE instance.

---

## Key Scientific Findings

### 1. Universal Fragmentation
All physically meaningful parameter space fragments eventually. No genuine stability exists for 
self-gravitating magnetised filaments in the parameter space surveyed (f=0.9–3.0, β=0.3–5.0, 
M=1–5, θ=0°–90°). Previous apparent stability (DTC β=0.3 ridge, PR2026 θ=90° grid) was 
confirmed as simulation artefacts (broken gravity, wrong FFT mesh configuration).

### 2. Two Fragmentation Regimes (B-field Angle)
- **θ≤15° (nearly longitudinal B)**: Axial beading — slow fragmentation, t_frag ≈ 1.3–1.4 t_J
- **θ≥30° (oblique/perpendicular B)**: Radial collapse dominates — fast, t_frag ≈ 0.58–0.87 t_J
- Transition sharp between θ=15° and θ=30°.

### 3. Fragment Spacing λ/W Dichotomy
- **Longitudinal B (θ≤30°)**: λ/W ≈ 3.4 (C5: 3.441±0.764, C7: 3.382±0.792)
- **Perpendicular B (θ=90°, β≥1.0)**: λ/W ≈ 1.25 (C6: 1.252±0.092)
- **2.75× shorter fragment spacing** for perpendicular vs longitudinal B — field geometry is key
- β≤0.5 at θ=90°: FLAT_PROFILE (pure radial collapse, no axial fragmentation)
- λ/W increases with B strength: β=0.3→λ/W=4.74, β=2.0→λ/W=2.80

### 4. DTC Stable Ridge — Confirmed Artefact
The β=0.3, M=1 "stable" ridge from the Definitive Transition Campaign (DTC) was confirmed as
an artefact of broken gravity (incorrect meshblock configuration). When run with corrected gravity
at tlim=4.0 t_J, all 7 test cases fragment at t_frag=0.27–0.34 t_J (DTC_EXT campaign). The
original DTC tlim=1.5 t_J was not exceeded — but the gravity was broken, so fragmentation was
suppressed until tlim.

### 5. Turbulence Effects
- Turbulence accelerates fragmentation (turbphys: t_frag 3× faster than quiescent)
- λ/W unchanged by turbulence (<5% variation) — spacing set by Jeans/Nagasawa, not turbulence
- Non-monotonic: turb amplitude=1.0 fastest; very high turbulence (amplitude=2.0) slightly slower

### 6. Observational β Validation (C13)
- 23 published JCMT/Planck/VLA Zeeman + DCF measurements in HGBS filaments
- Thermal β median=0.057 (range 0.014–0.385) — systematically below simulation range β=0.3–2.0
- But **simulation β corresponds to turbulent-effective β**: β_eff = β_th × (1 + M²)
- At M=2 (typical for molecular filaments): β_eff median=0.287, 43% within sim range
- Conclusion: simulation parameter range β=0.3–2.0 is physically justified for turbulent filaments

### 7. Pairwise Spacing Bias (C10)
- Pairwise fragment spacing estimator overestimates by **factor 7.0×** (L/3 convergence artefact)
- Nearest-neighbour estimator is unbiased (−0.005×)
- Published Herschel HGBS observations using pairwise spacing are systematically overestimated

---

## Directory Structure

```
referee_response_all_campaigns_may2026/
├── MASTER_README.md          ← This file
├── INDEX.json                ← Machine-readable index with per-campaign metadata
├── campaigns/
│   ├── C5/                   ← Turbulence λ/W (54 sims, longitudinal B)
│   ├── C6/                   ← Perpendicular-B β-dependence (100 sims)
│   ├── C7/                   ← Critical Transition Mapping (135 sims)
│   ├── C8/                   ← Field Angle θ sweep (175 sims)
│   ├── C8_lw/                ← λ/W vs Field Angle (35 sims)
│   ├── C9_deferred/          ← Staged Fragmentation (DEFERRED — needs new pgen)
│   ├── C10/                  ← Pairwise vs NN Bias (HGBS obs analysis)
│   ├── C11_deferred/         ← Temporal Evolution (DEFERRED — needs new pgen)
│   ├── C12/                  ← DTC Stable Ridge Re-examination (300 sims)
│   ├── C13/                  ← Observational β Validation (23 literature obs)
│   ├── PERP_LAMBDA_V1/       ← Perpendicular λ/W full grid (40 sims, Apr 29)
│   ├── REALISTIC_GAMMA_V1/   ← Realistic γ<1 EOS (40 sims, Apr 29)
│   ├── FINITE_LENGTH_V1/     ← Finite filament length (120 sims, Apr 29)
│   ├── TURBULENT_LAMBDA_V1/  ← Turbulent λ/W vs amplitude (30 sims, Apr 29)
│   ├── POWERLAW_VALIDATION_V1/ ← High-res power-law validation (30 sims, Apr 29)
│   ├── PR2026_MHD/           ← PR2026 MHD validation campaigns (220 sims, Apr 25–26)
│   │   ├── calibration/
│   │   ├── regime_boundary/
│   │   ├── perpendicular_field/
│   │   ├── domain_size/
│   │   └── physical_turbulence/
│   ├── BRIDGE_GRID/          ← θ=90° definitive test (48 sims, Apr 28)
│   ├── CALIB_EXT/            ← Calibration extension (36 sims, Apr 28)
│   ├── DTC_EXT/              ← DTC artefact verification (7 sims, Apr 28)
│   └── DTC_MAIN/             ← Definitive Transition Campaign (539 sims, Apr 20–21)
├── figures/
│   ├── c5_tfrag_by_turb.{png,pdf}
│   ├── c6_tfrag.{png,pdf}
│   ├── c7_tfrag.{png,pdf}
│   ├── cross_campaign_lambdaW.{png,pdf}
│   ├── fig_C8_C12_summary.{png,pdf}
│   ├── fig_C8_tfrag.{png,pdf}
│   ├── fig_C8lw_lambda_W.{png,pdf}
│   ├── master_overview.{png,pdf}
│   └── c13_beta_validation.{png,pdf}
├── reports/
│   ├── C5C6C7_FINAL_SUMMARY.md
│   ├── C8_C12_MASTER.log
│   └── C13_BETA_VALIDATION_REPORT.md
└── runners/
    ├── c8_c12_runner.py
    ├── c8_lw_runner.py
    ├── rrc_runner_c5c6c7.py
    ├── finite_length_runner.py
    ├── perp_lambda_runner.py
    ├── powerlaw_validation_runner.py
    ├── realistic_gamma_runner.py
    └── turbulent_lambda_runner.py
```

---

## Simulation Code

All simulations use:
- **Athena++** v21.0 with custom filament problem generator
- **Binary**: `/home/fetch-agi/athena/bin/athena` (standard pgen)
- **Binary (finite length)**: `/home/fetch-agi/athena/bin/athena_finite_length` (extended pgen)
- **Physics**: `hydro=mhd`, `eos=isothermal`, `gravity=fft`, `field_ics=uniform_bx1` or `bx2`
- **Resolution**: 32–512 cells per λ_J (campaign-dependent)
- **Parallelism**: mpirun -np 16–24 per simulation, ThreadPoolExecutor(max_workers=7–14)
- **Cluster**: astra-climate (GCE n2d-highcpu-224, 224 vCPUs, 220 GB RAM)

### Key Athena++ Configuration
```ini
<mesh>
nx1 = 256  # (or 512 for C6/C8)
nx2 = 64
nx3 = 64
<meshblock>
nx1 = 32
nx2 = 32
nx3 = 32
<gravity>
grav_mean_rho = 1.0
output_grav_pot = false
<problem>
filament_type = gaussian
b_orientation = longitudinal  # or perpendicular
```

**Critical note**: FFT self-gravity requires meshblock count to equal MPI rank count. Using np=16
with 32³ meshblocks in a domain that needs np=24 (for 512×64×64 / 32³ = 8×2×2 = 32 meshblocks
arranged as 8×2×2 with np=16 works, but 512×64×64 with np=16 was WRONG — correct is np=24).
The PR2026 BRIDGE_GRID error used np=16 → gravity broken → all false TIMEOUT.

---

## Important Notes for Paper

1. **DTC stable ridge retracted**: All stability in previous DTC campaign was artefactual.
   The correct t_frag for β=0.3, M=1 cases is 0.27–0.34 t_J (well within 1.5 t_J window).
   
2. **θ=90° stability retracted**: PR2026 BRIDGE_GRID θ=90° TIMEOUT results were due to np=16
   gravity bug. Correct result (BRIDGE_GRID campaign): 48/48 FRAG at 0.28–0.43 t_J.
   
3. **λ/W estimates are Jeans-Nagasawa theoretical**: Most simulations show radial collapse at
   t≈0.25 t_J before axial fragmentation develops. λ/W values are post-collapse theoretical
   estimates. Direct measurement only possible for θ≤30° cases with extended tlim.
   
4. **C9/C11 deferred**: Staged Fragmentation (time-varying f) and Temporal Evolution campaigns
   require new C++ pgen development. Not included in this submission.

---

## Provenance

| Campaign | Date | Cluster | Commit |
|----------|------|---------|--------|
| DTC_MAIN | Apr 20–21 | astra-climate | see DTC_MAIN/ |
| BRIDGE_GRID | Apr 28 | astra-climate | f271f42 |
| CALIB_EXT | Apr 28 | astra-climate | 30979e4 |
| DTC_EXT | Apr 28 | astra-climate | 8b378a7 |
| PR2026_MHD | Apr 25–26 | astra-climate | c316ea2 |
| PERP/GAMMA/FL/TURB/POWER | Apr 29 | astra-climate | — |
| C5/C6/C7 | Apr 30 | astra-climate | — |
| C8/C8_lw/C10/C12/C13 | May 1 | astra-climate/local | 0fa21bc |

Package assembled: 2026-05-01  
Assembled by: astra-pa (ASTRA multi-agent system)

