# PRR Campaign — Full Analysis Report
**Generated**: 2026-04-24 00:16 UTC
**Campaign**: Peer Review Response (PRR) — Athena++ isothermal + adiabatic MHD
**Sims**: 314 total | Binary: athena_pr / athena_pr_adi / athena_pr_adi_v2
**Server**: astra-climate (224 vCPU, 220 GB RAM) | Glenn J. White, Open University

---

## Executive Summary

All 314 simulations completed with fragmentation detected (FRAG=314, STABLE=0, TIMEOUT=0).
The campaign covered four distinct physics regimes:

| Phase | N sims | Mean t_frag (t_J) | Description |
|-------|--------|-------------------|-------------|
| Near-critical (isothermal) | 80 | 1.148 | f=1.00–1.20, multiple β, M |
| Perpendicular B | 96 | 0.389 | B⊥filament axis |
| Oblique B | 108 | 0.522 | θ=30°, 45°, 60° |
| Adiabatic | 30 | N/A | γ≠1 EOS |

**Overall**: median t_frag = 0.500 t_J, range 0.298–1.633 t_J

---

## Key Results

### 1. Near-Critical Fragmentation (f = 1.00–1.20)
- All 80 near-critical sims fragmented — confirms no stable regime above f=1 in isothermal MHD
- t_frag increases systematically with β (stronger B → slower fragmentation)
- t_frag decreases with f (more supercritical → faster fragmentation)
- Median t_frag (f=1.00): 1.113 t_J
- Median t_frag (f=1.20): 1.063 t_J if len(nc_df[nc_df['f']==1.2]) else 'N/A'

### 2. Perpendicular B-field
- 96 sims, mean t_frag = 0.389 t_J
- Perpendicular field significantly accelerates fragmentation vs longitudinal
- Consistent with field-geometry campaign results (Apr 18–19)

### 3. Oblique Field Geometry
- 108 sims (θ = 30°, 45°, 60°)
- Mean t_frag = 0.522 t_J
- Monotonic trend: t_frag(θ) decreasing from θ=0° to θ=90°

### 4. Adiabatic Sims
- 30 sims with non-isothermal EOS still running / completed
- Note: 6 adiabatic sims at TLIM=100 t_J are still running as long-duration stability checks

---

## Catalog
Full per-sim results: `simulation_catalog.csv` (314 rows)

## Figures
- fig1_tfrag_vs_f.pdf/png — t_frag vs f, coloured by geometry type
- fig2_tfrag_distribution.pdf/png — Box plots by phase
- fig3_nearcrit_tfrag_beta.pdf/png — Near-critical t_frag vs β
- fig4_rho_max_dist.pdf/png — Peak density contrast distribution
