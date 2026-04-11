# Executive Summary — MHD Simulations for Filament Fragmentation (V2)

**Date:** 2026-04-11 | **Code:** Athena++ 128³ isothermal MHD | **Grid:** 2×2 in (ℳ, β)

---

## The Problem

HGBS observations show filament cores spaced at λ/W = 2.1 ± 0.1 (0.21 pc across 9 regions). The classical Inutsuka & Miyama (1992) prediction gives λ/W = 4.0. What explains this factor-of-two discrepancy?

## Four Simulations

| | β = 1 (equipartition) | β = 0.1 (mag-dominated) |
|---|---|---|
| **ℳ = 1** | KE=0.70, ME=1.05, ℳ_A=0.82 | KE=0.76, ME=10.02, ℳ_A=0.28 |
| **ℳ = 3** | KE=1.89, ME=1.56, ℳ_A=1.10 | KE=4.30, ME=10.25, ℳ_A=0.65 |

## Key Finding: Magnetic Tension Resolves the 2× vs 4× Discrepancy

The magnetic field is **strongly anisotropic** — dominated by the mean-field direction (along the filament). In this geometry, **tension** (not pressure) is the dominant magnetic effect.

- Magnetic **pressure** (perpendicular B) *increases* λ/W to 7–18 — makes it **worse**
- Magnetic **tension** (parallel B) *decreases* λ/W to ~2.2 for β=1 — **matches observations**

| Model | M1,β1 | M3,β1 | M1,β0.1 | M3,β0.1 | **Observed** |
|---|---|---|---|---|---|
| IM92 (no B) | 4.0 | 4.0 | 4.0 | 4.0 | — |
| **Tension model** | **2.29** | **2.20** | 0.87 | 0.87 | **2.1** |

## β Constraint

- **β ~ 0.5–1.0 required** to match observations (tension model → λ/W ≈ 2.1)
- **β = 0.1 excluded** — would give λ/W < 1 (cores closer than filament width)
- Consistent with Crutcher (2012) Zeeman measurements (β ~ 0.2–2.0)

## Dynamo Physics

- β=1: Active small-scale dynamo (γ ≈ 2–5), but field remains anisotropic (ME_∥/ME_⊥ = 3–36)
- β=0.1: Dynamo **quenched** by strong mean field. ME_perp/ME_total < 1.3%. Essentially no field amplification.

## For the Paper

**Suggested paragraph:** Magnetic tension along filaments provides a natural, quantitative explanation for the observed λ/W ≈ 2.1. For β ≈ 1, λ_frag = 4W × c_s/c_eff,∥ ≈ 2.2W, in excellent agreement with the HGBS composite.

**Key figures:** `fig_g_comprehensive_6panel.pdf` (paper figure), `fig_h_alfven_diagnostics.pdf` (supplementary)

## Files

All results in `/shared/W3_HGBS_filaments/athena_mhd_results_v2/`:
- 8 figures (PNG 300dpi + PDF)
- `simulation_results_v2.json` — all quantitative data
- `MHD_SIMULATION_REPORT_V2.md` — full report with analysis and paper text

---

*ASTRA-PA, 2026-04-11*
