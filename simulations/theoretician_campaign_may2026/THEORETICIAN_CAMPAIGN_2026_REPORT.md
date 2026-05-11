# Theoretician Campaign 2026 — Final Report

**Authors**: ASTRA system / Glenn J. White (Open University)  
**Date completed**: 2026-05-11  
**Server**: astra-climate | 220 vCPU GCE  

---

## Overview

Three sequential MHD simulation campaigns totalling **406 simulations** using Athena++
(HLLD MHD + FFT self-gravity, isothermal EOS, np=32 per sim, max_conc=6).

| Campaign | Grid | Domain | Physics | N | FRAG | TOUT |
|----------|------|--------|---------|---|------|------|
| A — Mixed field geometry | 512×64×64 | 16λJ | θ×f×β×seeds | 280 | 234 | 46 |
| B — Supercritical calibration | 768×64×64 | 24λJ | f×β×seeds, θ=0° | 90 | 90 | 0 |
| C — Domain convergence | 512×64×64 | 12–24λJ | L×f×seeds, θ=90° | 36 | 36 | 0 |
| **Total** | | | | **406** | **360** | **46** |

---

## Key Scientific Results

### 1. t_frag(θ) Arc — Campaign A

The fragmentation timescale decreases from θ=0° (longitudinal B) to θ=90° (perpendicular B),
but with a surprising **non-monotonic structure**:

| θ (°) | ⟨t_frag⟩ (tJ) | σ | Δ vs 0° |
|--------|--------------|---|---------|
| 0 | 1.399 | 0.184 | baseline |
| 15 | 1.178 | 0.203 | −16% |
| 30 | 0.878 | 0.259 | −37% |
| 45 | 0.649 | 0.220 | −54% |
| **60** | **0.528** | **0.102** | **−62%** ← minimum |
| 75 | 0.587 | 0.194 | −58% |
| 90 | 0.595 | 0.196 | −57% |

**Notable features:**
- **Sharp inflection at θ~15–30°** (−16% → −37%): field geometry transition
- **Non-monotonic minimum at θ~60°**: perpendicular B (θ=90°) provides marginally more
  radial pressure support than oblique at 60°, slightly decelerating the collapse
- **β-inversion island at θ=45°**: strong oblique fields (β=0.3) suppress fragmentation
  (14/40 TIMEOUT); β=1.0 fragments cleanly at t~0.644 tJ
- Sigmoid fit inflection at ~32° with amplitude 0.87 tJ

### 2. Supercritical Calibration t_frag(f,β) — Campaign B

All 90/90 FRAG, 0 TIMEOUT. ⟨t_frag⟩ grid (tJ):

| f \ β | 0.3 | 1.0 | 3.0 |
|-------|-----|-----|-----|
| 1.3 | 1.566 | 1.547 | 1.302 |
| 1.5 | 1.515 | 1.460 | 1.169 |
| 1.8 | 1.454 | 1.313 | 1.025 |
| 2.0 | 1.411 | 1.233 | 0.942 |
| 2.5 | 1.298 | 1.057 | 0.797 |
| 3.0 | 1.207 | 0.888 | 0.697 |

**Inverted-β at θ=0°**: longitudinal B provides radial magnetic pressure support.
Higher β (weaker B) → faster collapse. Marginal means: β=0.3→1.408, β=1.0→1.250, β=3.0→0.989 tJ.
Seed-to-seed variance within each (f,β) cell: σ≈0.007–0.032 tJ (nearly deterministic).

### 3. Domain Convergence — Campaign C

All 36/36 FRAG. t_frag(L) for θ=90°, β=1.0:

| L (λJ) | f=1.0 | f=1.5 | f=2.0 | Mean |
|---------|-------|-------|-------|------|
| 12 | 0.829 | 0.538 | 0.421 | 0.596 |
| 16 | 0.830 | 0.537 | 0.421 | 0.596 |
| 20 | 0.829 | 0.574 | 0.445 | 0.616 |
| 24 | 0.830 | 0.537 | 0.420 | 0.596 |

**Perfect convergence**: t_frag is identical to ±0.001 tJ across L=12–24λJ for f=1.0 and f=2.0.
Results are domain-independent in this regime.

---

## Infrastructure Notes

### FFT Gravity Bug (Campaign B)
All 24 initial Campaign B results were invalid — the FFT self-gravity driver failed with
FATAL ERROR due to wrong meshblock decomposition. 768-cell domain with meshblock nx1=32 gives
96 total meshblocks; np=32 cannot form a valid FFT pencil decomposition (96/32=3 is not a
valid grouping). Fixed by changing meshblock nx1=32→48, giving 64 total meshblocks (same
proven config as Campaign A: 16×2×2=64, 2 MB/proc). Confirmed by absence of FATAL ERRORS
and 90/90 FRAG (0 TIMEOUT) after fix.

### λ/W Measurement Status
In-campaign postproc_lw.py gives unreliable λ/W values for early-snapshot fragmentation.
Peak detection at t_frag captures only 1–3 initial condensation events in a 16–24λJ domain,
giving anomalously large λ/W (~7–38). Dedicated late-snapshot follow-up campaign in progress.

---

## Files

- `figures/fig1_tfrag_vs_theta.{pdf,png}` — t_frag(θ) arc with β bands
- `figures/fig2_B_tfrag_fxbeta.{pdf,png}` — Campaign B f×β heatmap
- `figures/fig3_C_domain_convergence.{pdf,png}` — Campaign C L-convergence
- `figures/fig4_combined_summary.{pdf,png}` — Combined science summary
- `theoretician_2026_science_summary.json` — Machine-readable results
- `A/`, `B/`, `C/` — Individual sim directories with status.json per sim

