# TA-1 + TA-4 Referee Response Campaigns — Final Report
**Authors**: Glenn J. White (Open University) & Robin Dey (VBRL Holdings Inc)  
**Generated**: 2026-05-12  |  **Cluster**: astra-climate (224 vCPU AMD EPYC)  
**Wall time**: 52 minutes total (02:48–03:40 UTC)  
**Result**: 64/64 FRAG | 0 TIMEOUT | 0 FAILED

---

## Executive Summary

Two targeted campaigns address referee comments TA-1 and TA-4:

**TA-1** (4 sims): Fine-cadence HDF5 time-series at f=1.4, β=1.0, θ=0° demonstrates the
late-time sampling bias in λ/W measurements. All 4 sims FRAG at t_frag = 1.464±0.011 t_J.
The λ/W diagnostic is only detectable in the final ~20% of the simulation (t > 0.79 t_frag),
and measured values span 2.7–49.8 (mean 10.5±7.8) — nearly factor-18 scatter — confirming
that peak-detection λ/W reflects instantaneous core arrangement, not a robust physical wavelength.

**TA-4** (60 sims): Re-verification of all 12 DTC stochastic zone parameter points at 6h wall
time. 60/60 FRAG, 0 TIMEOUT. Mean t_frag = 1.432±0.059 t_J. Every DTC STABLE classification
was a timeout artifact from the original 600s wall-clock limit.

---

## 1. Campaign Setup

### TA-1: Multi-Epoch λ/W Demonstration
- Config: f=1.4, β=1.0, θ=0°, seeds=[42,137,314,527], 512×64×64, L=16λ_J
- HDF5 cadence: **0.02 t_J** (very fine — 50 snapshots per t_J)
- ALL HDF5 retained until multi-epoch post-processing, then deleted
- Wall limit: 10800s (3h)

### TA-4: DTC Stochastic Zone Re-verification
- Config: 12 parameter points × 5 seeds = 60 sims, 512×64×64, L=16λ_J, θ=0°
- Wall limit: 21600s (6h)
- Parameters: 12 DTC stochastic zone (f, β) points at M=1 (minimal perturbations)

---

## 2. TA-1 Results: λ/W Temporal Evolution

### Fragmentation Times
All 4 seeds fragment at t_frag = 1.4641 ± 0.0105 t_J (< 1% seed variation).

| Seed | t_frag (t_J) | n_snaps | n_valid_λ/W | First detection (t/t_frag) |
|------|-------------|---------|-------------|---------------------------|
| 42  | 1.4671 | 74 | 16 | 0.79 |
| 137 | 1.4485 | 73 | 15 | 0.80 |
| 314 | 1.4712 | 74 | 14 | 0.80 |
| 527 | 1.4695 | 74 | 15 | 0.80 |

### Key Findings

**1. Detection only in final 20% of sim**: The column density peak-finder returns no valid
measurements before t ≈ 0.79–0.80 t_frag. In the preceding 80% of the simulation, the
filament undergoes quasi-static gravitational condensation without clear axial density
modulation detectable by the peak-finding algorithm. λ/W is therefore only measurable
in the run-up to radial collapse — not the physically clean fragmentation phase.

**2. Enormous scatter**: Within the measurable window, λ/W ranges from 2.7 to 49.8 across
all seeds and snapshots:

| Seed | λ/W range | Notes |
|------|-----------|-------|
| 42  | 6.6–49.8 | 2–4 peaks; very variable |
| 137 | 4.1–18.2 | 2–3 peaks; variable |
| 314 | 2.7–19.1 | 2–5 peaks; variable |
| 527 | 2.9–8.3  | 2–4 peaks; most stable |

The scatter within a single seed's time evolution reaches factor 7–18. Across seeds,
the mean early-window λ/W ranges from 3.8 (seed 527) to 20.1 (seed 42) — a factor-5 range
for identical physical parameters, driven purely by which density peaks the algorithm detects.

**3. Physical interpretation**: The scatter arises because in a 16λ_J domain, the theoretical
fragmentation wavelength λ/W ≈ 3.4 predicts ~16 evenly-spaced clumps. In practice, the
collapse proceeds stochastically — only 2–5 dominant density maxima become detectable
simultaneously, their spacing varying as different clumps merge or separate during collapse.
The measurement is not sampling a stationary spatial pattern but a dynamically evolving one.

**Conclusion for TA-1**: The λ/W ≈ 3.4 ± 0.8 reported from C5/C7 represents the mean of a
very broad distribution. The quoted σ = 0.8 severely underestimates the true measurement
uncertainty, which spans a factor ~10 (2.7–49.8 in this campaign). The λ/W diagnostic is
not reliably comparable to observational clump-spacing catalogues.

---

## 3. TA-4 Results: DTC Stochastic Zone

### Per-Point Results (all 5/5 FRAG)

| f | β | DTC M | t_frag mean (t_J) | σ | Category |
|---|---|-------|-------------------|----|----------|
| 1.4 | 0.3 | 3+4 | 1.5109 | 0.0250 | β=0.3 (covered by C12) |
| 1.4 | 0.7 | 2.0  | **1.4830** | 0.0156 | **★ KEY — β≠0.3, unverified** |
| 1.4 | 1.3 | 1.0  | **1.3228** | 0.0186 | **★ KEY — β≠0.3, unverified** |
| 1.5 | 0.3 | 3.0  | 1.4879 | 0.0234 | β=0.3 (covered by C12) |
| 1.5 | 0.5 | 2.0  | **1.4607** | 0.0173 | **★ KEY — β≠0.3, unverified** |
| 1.5 | 1.1 | 1.0  | **1.3389** | 0.0192 | **★ KEY — β≠0.3, unverified** |
| 1.6 | 0.3 | 3.0  | 1.4689 | 0.0218 | β=0.3 (covered by C12) |
| 1.6 | 0.5 | 2.0  | **1.4375** | 0.0184 | **★ KEY — β≠0.3, unverified** |
| 1.6 | 0.9 | 1.0  | **1.3902** | 0.0214 | **★ KEY — β≠0.3, unverified** |
| 1.7 | 0.3 | 2.0  | 1.4485 | 0.0232 | β=0.3 (covered by C12) |
| 1.8 | 0.3 | 2.0  | 1.4307 | 0.0251 | β=0.3 (covered by C12) |
| 1.9 | 0.3 | 2.0  | 1.4071 | 0.0206 | β=0.3 (covered by C12) |

**Overall**: t_frag = 1.432 ± 0.059 t_J, range [1.306, 1.545] t_J

### Why the DTC Misclassified These as STABLE

The DTC used a 600s wall-clock limit at 128³ resolution. Based on the TRR campaign
(April 2026), fragmentation at 128³ requires ~12,000–15,000s wall time for β=0.3 cells
(t_frag ≈ 1.0–1.43 t_J). The β≠0.3 cells verified here fragment at t_frag ≈ 1.32–1.51 t_J,
implying similar or greater wall-clock requirements.

The **stochastic** outcome (one seed FRAG, one STABLE) arose because the two DTC seeds
approached the 600s limit at slightly different rates due to turbulence. The seed that
happened to be advancing faster just crossed the collapse threshold before wall-clock expiry.
With 6h wall time, all seeds FRAG without exception.

### Physical Trends
- **β effect**: Higher β → faster fragmentation at constant f
  - β=0.3: 1.459 t_J | β=0.5: 1.449 t_J | β=0.9: 1.390 t_J | β=1.1: 1.339 t_J | β=1.3: 1.323 t_J
  - Counter-intuitive (stronger B → faster collapse at θ=0°): consistent with C7/C8 results
    where longitudinal B field's tension aids axial fragmentation
- **f effect**: Higher f → faster fragmentation (0.04 t_J per Δf=0.1 at β=0.3)
- Seed-to-seed variation: σ = 0.015–0.025 t_J (< 2% of t_frag) — highly reproducible

---

## 4. Disk and Resource Usage

- Pre-launch: 3.3 GB used (463 GB free)
- Peak during TA-1 (4 concurrent fine-cadence sims): 20 GB (~70 MB/HDF5 file)
- Post-completion (all HDF5 deleted): **3.7 GB used** — net +0.4 GB
- Active cores during run: 192 (6 × 32 MPI ranks)

---

## 5. Output Files

| File | Description |
|------|-------------|
| fig1_ta1_lw_timeseries.pdf/png | λ/W vs t/t_frag per seed (4-panel) |
| fig2_ta4_stochastic_zone.pdf/png | t_frag(f,β) and histogram for 60 sims |
| fig3_ta1_combined_bias.pdf/png | All seeds combined, showing detection gap + scatter |
| ta1_ta4_summary.json | Machine-readable summary statistics |
| FINAL_REPORT.md | This document |

---

## 6. Summary for Referee Response

**TA-1** — Addresses the question: *does λ/W change with measurement epoch?*  
Answer: Yes, dramatically — from 2.7 to 49.8 across the measurable window. The λ/W 
diagnostic is not reliable for quantitative comparison with observations. The late-time 
sampling bias is confirmed: snapshots taken near t_frag show inflated λ/W due to collapse 
onto a few dominant cores. But the early-time measurements also scatter enormously, so 
there is no "clean" measurement window.

**TA-4** — Addresses the question: *are the DTC stochastic zone STABLE cells real?*  
Answer: No. All 60 re-run sims FRAG at t_frag ≈ 1.43 t_J with 6h wall time. The original 
DTC 600s limit was responsible for every STABLE classification. The stochastic pattern 
(seed-dependent outcomes) was a timing artifact, not genuine physical bistability. 
Universal fragmentation is confirmed across the entire tested (f, β) parameter space at θ=0°.
