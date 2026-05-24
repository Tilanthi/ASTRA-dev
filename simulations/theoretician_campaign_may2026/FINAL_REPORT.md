# Theoretician Campaign 2026 — FINAL REPORT
**Authors**: Glenn J. White (Open University) & Robin Dey (VBRL Holdings Inc)  
**Completed**: 2026-05-11 19:15 UTC  
**Server**: astra-climate (GCE, 220 vCPU, AMD EPYC 7B13)

## Overview
406 Athena++ MHD filament simulations across three sub-campaigns, addressing:
1. **Campaign A**: t_frag dependence on magnetic field-filament angle θ
2. **Campaign B**: Supercritical calibration — t_frag(f, β) at θ=0°, extended domain
3. **Campaign C**: Domain-length convergence at θ=90°

**Total: 406 sims | 360 FRAG (88.7%) | 46 TIMEOUT (11.3%) | 0 FAILED**

---

## Campaign A — θ Sweep (280 sims)
**Config**: f=[1.0,1.5,2.0,2.5], β=[0.3,1.0], θ=[0,15,30,45,60,75,90]°, 5 seeds  
**Grid**: 512×64×64, domain=16 λ_J, np=32

| θ (°) | FRAG | TOUT | t_frag (t_J) | σ |
|-------|------|------|--------------|---|
|   0   |  33  |   7  | 1.3994       | 0.1838 |
|  15   |  26  |  14  | 1.1781       | 0.2029 |
|  30   |  39  |   1  | 0.8784       | 0.2590 |
|  45   |  26  |  14  | 0.6485       | 0.2200 |
|  60   |  30  |  10  | 0.5277       | 0.1024 |
|  75   |  40  |   0  | 0.5873       | 0.1942 |
|  90   |  40  |   0  | 0.5952       | 0.1960 |

### Mixing Model Fit
```
t_frag(θ) = t₀ + (t₉₀ - t₀) × sin^n(θ)
  t₀  = 1.4165 ± 0.0919 t_J   [θ=0°, longitudinal]
  t₉₀ = 0.4857 ± 0.0522 t_J   [θ=90°, perpendicular]
  n   = 0.791 ± 0.240
```
**Critical angle**: θ_c ≈ 20–25° — steepest t_frag gradient; TIMEOUT rate drops from 35% at θ=15° to 2.5% at θ=30°

---

## Campaign B — Supercritical Calibration (90 sims)
**Config**: f=[1.3,1.5,1.8,2.0,2.5,3.0], β=[0.3,1.0,3.0], 5 seeds, θ=0°  
**Grid**: 768×64×64, domain=24 λ_J, np=32  
**All 90 FRAG — zero TIMEOUT**

| f   | t_frag (t_J) | σ    |
|-----|--------------|------|
| 1.3 | 1.4716       | 0.1210 |
| 1.5 | 1.3813       | 0.1533 |
| 1.8 | 1.2639       | 0.1791 |
| 2.0 | 1.1951       | 0.1935 |
| 2.5 | 1.0507       | 0.2049 |
| 3.0 | 0.9305       | 0.2114 |

### Power-Law Fit
```
t_frag(f) = 1.712 × f^{-0.536}   [θ=0°, longitudinal B]
```
β-dependence: β=0.3→1.409, β=1.0→1.250, β=3.0→0.989 t_J (28% range)

---

## Campaign C — Domain Convergence (36 sims)
**Config**: L=[12,16,20,24] λ_J, f=[1.0,1.5,2.0], β=1.0, 3 seeds, θ=90°  
**All 36 FRAG — perfect domain independence**

| L (λ_J) | t_frag (t_J) | σ     |
|---------|--------------|-------|
|   12    | 0.5959       | 0.1713|
|   16    | 0.5959       | 0.1719|
|   20    | 0.6159       | 0.1632|
|   24    | 0.5958       | 0.1723|

**Grand mean = 0.601 ± 0.009 t_J — completely L-independent (σ_L/mean < 1.5%)**

---

## Deliverables
- `fig1_tfrag_vs_theta.pdf/png` — Mixing model + β-coloured arc
- `fig2_B_tfrag_fxbeta.pdf/png` — Supercritical power-law calibration
- `fig3_C_domain_convergence.pdf/png` — Domain convergence at θ=90°
- `fig4_combined_summary.pdf/png` — 5-panel publication summary
- `mixing_model_params.json` — Mixing model fit parameters
- `supercritical_calibration.json` — Power-law calibration
- `domain_convergence.json` — Domain convergence statistics
- `all_406_results.json` — Full record for all 406 simulations
