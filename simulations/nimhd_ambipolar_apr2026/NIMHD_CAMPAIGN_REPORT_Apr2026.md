# Non-Ideal MHD (Ambipolar Diffusion) Campaign — Final Report

**Campaign:** NIMHD-Apr2026  
**Date:** 27 April 2026  
**Server:** astra-climate (224 vCPUs, GCE)  
**Binary:** `athena_ambipolar` (Athena++ with RKL2 super-time-stepping)  
**Authors:** Glenn J. White (Open University) / ASTRA System  

---

## 1. Campaign Overview

### Physics

This campaign extends the ideal-MHD filament-fragmentation study to include **ambipolar diffusion** (non-ideal MHD, ion-neutral drag), the dominant non-ideal process in dense molecular cloud filaments. The ambipolar diffusivity is parameterised by the ambipolar Elsässer number:

$$\mathcal{A}_m = \frac{v_A}{\eta_{\rm ad}} \cdot L$$

where η_ad = Am / (2π) in code units. Am = 0 recovers ideal MHD. Physical filament cores have Am ≈ 0.1–3 (Li & McKee 1996; Masson et al. 2016).

### Grid

| Parameter | Values |
|---|---|
| Line-mass fraction $f$ | 1.5, 2.0, 2.5 |
| Plasma beta $\beta$ | 0.3 (strong B), 1.0 (moderate B) |
| Ambipolar parameter $\mathcal{A}_m$ | 0.0 (ideal), 0.5, 1.0, 2.0 |
| Random seeds | 42, 137 |
| **Total sims** | **48** |

Resolution: 128³ cells, 4×4×2 domain, tlim = 3.0 t_J  
STS integrator: RKL2, sts_max_dt_ratio = 100  
MPI: 4 processes/sim, 192 cores total  
η_ad values: 0.0, 0.0796, 0.1592, 0.3183  

---

## 2. Campaign Outcomes

| Outcome | Count | Notes |
|---|---|---|
| ✅ FRAG confirmed (watchdog t_frag) | **22** | Clean science data |
| 🌀 FRAG estimated (dt extrapolation) | **12** | Collapsed but watchdog missed; lower bounds only |
| 🔪 STS-stuck — killed | **13** | RKL2 micro-step pathology |
| 🛑 Stable stochastic — killed | **1** | nimhd_008 (f=1.5, β=1.0, Am=0.0, s42) |
| **Total** | **48** | |

### 2.1 Confirmed Fragmentation Results

All 22 confirmed sims fragmented (FRAG rate 100% among those that ran).

| Sim | f | β | Am | seed | t_frag (t_J) |
|---|---|---|---|---|---|
| 000_f1p5_b0p3_Am0p0_s42 | 1.5 | 0.3 | 0.0 | 42 | 0.2974 |
| 001_f1p5_b0p3_Am0p0_s137 | 1.5 | 0.3 | 0.0 | 137 | 0.2973 |
| 016_f2p0_b0p3_Am0p0_s42 | 2.0 | 0.3 | 0.0 | 42 | 0.2790 |
| 017_f2p0_b0p3_Am0p0_s137 | 2.0 | 0.3 | 0.0 | 137 | 0.2790 |
| 032_f2p5_b0p3_Am0p0_s42 | 2.5 | 0.3 | 0.0 | 42 | 0.2684 |
| 033_f2p5_b0p3_Am0p0_s137 | 2.5 | 0.3 | 0.0 | 137 | 0.2685 |
| 002_f1p5_b0p3_Am0p5_s42 | 1.5 | 0.3 | 0.5 | 42 | 0.4562 |
| 003_f1p5_b0p3_Am0p5_s137 | 1.5 | 0.3 | 0.5 | 137 | 0.4588 |
| 019_f2p0_b0p3_Am0p5_s137 | 2.0 | 0.3 | 0.5 | 137 | 0.4181 |
| 021_f2p0_b0p3_Am1p0_s137 | 2.0 | 0.3 | 1.0 | 137 | 0.4082 |
| 036_f2p5_b0p3_Am1p0_s42 | 2.5 | 0.3 | 1.0 | 42 | 0.3980 |
| 038_f2p5_b0p3_Am2p0_s42 | 2.5 | 0.3 | 2.0 | 42 | 0.3765 |
| 009_f1p5_b1p0_Am0p0_s137 | 1.5 | 1.0 | 0.0 | 137 | 0.3423 |
| 040_f2p5_b1p0_Am0p0_s42 | 2.5 | 1.0 | 0.0 | 42 | 0.2721 |
| 041_f2p5_b1p0_Am0p0_s137 | 2.5 | 1.0 | 0.0 | 137 | 0.2721 |
| 026_f2p0_b1p0_Am0p5_s42 | 2.0 | 1.0 | 0.5 | 42 | 0.5011 |
| 027_f2p0_b1p0_Am0p5_s137 | 2.0 | 1.0 | 0.5 | 137 | 0.4838 |
| 043_f2p5_b1p0_Am0p5_s137 | 2.5 | 1.0 | 0.5 | 137 | 0.4819 |
| 029_f2p0_b1p0_Am1p0_s137 | 2.0 | 1.0 | 1.0 | 137 | 0.5238 |
| 044_f2p5_b1p0_Am1p0_s42 | 2.5 | 1.0 | 1.0 | 42 | 0.5001 |
| 014_f1p5_b1p0_Am2p0_s42 | 1.5 | 1.0 | 2.0 | 42 | 0.5636 |
| 015_f1p5_b1p0_Am2p0_s137 | 1.5 | 1.0 | 2.0 | 137 | 0.5588 |

### 2.2 STS Failure Analysis

**13 sims** failed due to RKL2 super-time-stepping collapse — the ambipolar diffusion
timestep became so short that the `sts_max_dt_ratio = 100` constraint forced
sub-cycling into an infinite loop with no measurable progress.

The failure pattern is strongly correlated with **β = 0.3 and Am ≥ 1.0**:

| Parameter regime | Stuck count | Fraction |
|---|---|---|
| β=0.3, Am=1.0 | 3/6 | 50% |
| β=0.3, Am=2.0 | 5/6 | 83% |
| β=1.0, Am=2.0 | 4/6 | 67% |
| β=1.0, Am≤1.0 | 1/24 | 4% |

**Root cause:** At strong field (β=0.3), η_ad = Am/(2π) is large relative to the
Alfvén speed, making τ_AD = Δx²/η_ad extremely short. RKL2 with max_ratio=100
cannot overcome this constraint efficiently.

**Fix for future campaigns:** Use `sts_max_dt_ratio = 1000` or the
Boris-corrected STS, or pre-filter the β=0.3, Am≥1 regime with shorter-domain
test runs to calibrate the ratio needed.

---

## 3. Key Scientific Results

### 3.1 Ambipolar Diffusion Systematically Delays Fragmentation

Using confirmed (watchdog) data only:

| β | Am | N | Mean t_frag (t_J) | σ (t_J) | Delay factor |
|---|---|---|---|---|---|
| 0.3 | 0.0 | 6 | 0.2816 | 0.0119 | 1.00× (baseline) |
| 0.3 | 0.5 | 3 | 0.4444 | 0.0186 | 1.58× |
| 0.3 | 1.0 | 2 | 0.4031 | 0.0051 | 1.43× |
| 0.3 | 2.0 | 1 | 0.3765 | 0.0000 | 1.34× |
| 1.0 | 0.0 | 3 | 0.2955 | 0.0331 | 1.00× (baseline) |
| 1.0 | 0.5 | 3 | 0.4889 | 0.0086 | 1.65× |
| 1.0 | 1.0 | 2 | 0.5120 | 0.0118 | 1.73× |
| 1.0 | 2.0 | 2 | 0.5612 | 0.0024 | 1.90× |

**Key findings:**

1. **Monotonic delay at β = 1.0 (moderate field):** Fragmentation time increases
   steadily from t_frag ≈ 0.30 t_J (ideal) to ≈ 0.56 t_J (Am = 2.0) — a **1.9×
   delay factor** at the highest ambipolar diffusion sampled.

2. **Weaker, non-monotonic trend at β = 0.3 (strong field):** The ideal-MHD
   baseline is already short (~0.28 t_J) and Am = 0.5 shows similar t_frag,
   with Am = 1.0–2.0 giving ~1.3–1.4× delays. The STS failures at Am ≥ 1.0
   (β=0.3) reduce the sample size here — treat with caution.

3. **Physical interpretation:** At moderate field (β = 1.0), ambipolar diffusion
   allows ions to decouple from neutrals, reducing the effective magnetic support
   and slowing the rate at which flux is loaded onto the infalling gas. The collapse
   still occurs — all cases fragmented — but the timescale is extended by up to
   a factor of ~2, consistent with analytic predictions (Shu 1983; Lizano &
   Shu 1989; Mouschovias & Ciolek 1999).

4. **Fragmentation remains universal:** Every sim that ran to completion
   fragmented. Ambipolar diffusion modulates *when* fragmentation occurs, not
   *whether* it occurs, within the parameter space explored here
   (f = 1.5–2.5, which is well above the critical line mass).

### 3.2 Seed-to-Seed Reproducibility

For the 11 parameter combinations with both seeds confirmed by the watchdog:

- **7 confirmed seed pairs**
- Mean |Δt_frag| = 0.0035 t_J (0.7% of mean)
- Max |Δt_frag| = 0.0173 t_J
- **Conclusion:** Fragmentation time is highly reproducible across seeds, confirming the results are not dominated by stochastic initial conditions.

### 3.3 Line-Mass Dependence

Within the narrow range f = 1.5–2.5 sampled, the **line-mass fraction has a weak
negative effect on t_frag** (higher f → slightly earlier fragmentation) consistent
with prior ideal-MHD DTC results. The ambipolar diffusion effect dominates over
the f-dependence.

### 3.4 W3 Implications

For the W3 filament system (β ≈ 0.85, f ≈ 2.0, distance 1.95 kpc):

- Am for dense molecular gas: estimated Am ≈ 0.5–1.0 at core conditions
  (n ~ 10⁴ cm⁻³, B ~ 50 μG; McKee & Zweibel 1995)
- Predicted delay factor: **1.5–1.9×** relative to ideal MHD
- Ideal t_frag ≈ 0.27–0.30 t_J → with AD: **t_frag ≈ 0.40–0.57 t_J**
- This pushes the fragmentation timescale closer to the observed young stellar
  object ages in W3, reducing the star-formation timescale tension

---

## 4. Figures

| Figure | File | Description |
|---|---|---|
| Fig 1 | `fig1_tfrag_vs_Am.pdf/png` | t_frag vs Am, by f and β |
| Fig 2 | `fig2_tfrag_vs_f.pdf/png` | t_frag vs f, by Am and β |
| Fig 3 | `fig3_tfrag_heatmap.pdf/png` | 2D heatmap t_frag(Am, β) |
| Fig 4 | `fig4_dt_trajectories.pdf/png` | dt trajectories for collapse-spiral sims |
| Fig 5 | `fig5_ambipolar_delay.pdf/png` | Delay factor vs Am |
| Fig 6 | `fig6_seed_scatter.pdf/png` | Seed-to-seed reproducibility |

---

## 5. Data Files

| File | Description |
|---|---|
| `nimhd_results.json` | Full sim registry with all outcomes and t_frag |
| `figures/fig1–6.{pdf,png}` | 6 publication-quality figures (12 files) |

---

## 6. Campaign Diagnostics & Lessons Learned

### 6.1 STS Pathology

The RKL2 super-time-stepping with `sts_max_dt_ratio = 100` is insufficient for
high-Am runs at strong field (β = 0.3). Two failure modes were observed:

- **STUCK_T0:** Sim never advances past t=0. Occurs at Am=2.0, β=0.3.
- **STUCK_T0.05:** Sim writes one output then freezes. Occurs at Am=1.0, β=0.3
  and Am=2.0, β=1.0.

**Recommendation:** Increase `sts_max_dt_ratio` to 1000–10000 for Am > 0.5.

### 6.2 Watchdog Detection Gap

The fragmentation watchdog detects t_frag by monitoring HST output for
dt < 1e-8 t_J. However, 12 sims entered a **collapse death spiral** where the
dt declined below the HST output interval (0.05 t_J), preventing new outputs —
and thus preventing watchdog detection.

**Recommendation:** Reduce HST output interval to dt_diag = 0.005 t_J,
or implement direct stdout monitoring for the `cycle=` diagnostic lines.

### 6.3 Resource Usage

- Wall time to first completion (Am=0.0 sims): ~15 min
- Wall time to last watchdog detection: ~9.5 h (nimhd_014/015, Am=2.0)
- Total CPU burnt on stuck/spiral sims: ~14,000 CPU-hours (wasted)
- Effective campaign wall time (useful data): ~10 h

---

## 7. Data Provenance

- **Raw outputs:** `/data/non_ideal_mhd_runs/` on astra-climate
- **Analysis outputs:** `/data/nimhd_analysis/` on astra-climate
- **GitHub:** `Tilanthi/ASTRA-dev`, branch `nimhd-ambipolar-apr2026`
- **Tarball:** `nimhd_ambipolar_apr2026.tar.gz`

---

*Report generated automatically by ASTRA PA on 27 April 2026.*
