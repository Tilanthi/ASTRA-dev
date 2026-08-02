# Supporting computations for v142 (internal record, not part of the manuscript)

## 1. Contraction-rate ladder

Athena++ problem generator extended to accept a homologous initial radial contraction
`v_r(r) = -A (c_s/R_0) r`, tapered beyond 3 R_0. Five otherwise identical runs from the same
relaxed Ostriker cylinder at A = 0, 0.25, 0.5, 0.75, 1, on 256x64x64 (dx = 0.0625 lambda_J,
isotropic), L_x = 16 lambda_J periodic, twelve-mode Kolmogorov seed at dv/c_s = 1e-3,
tlim = 2 t_J, 41 snapshots each; plus 512x128x128 endpoint checks at A = 0 and A = 1.
Configs and logs: `/data/contraction_ladder_aug2026/`.

Per-mode growth rates fitted over the common linear window (0.0015 < delta_rms < 0.12) for
the seeded, well-resolved modes n <= 10. rho_eff = central density at the mid-point of that
window.

| A    | rho_eff/rho_0 | n_peak | lambda_peak/lambda_J | 22H(rho_eff)/lambda_J | lambda_peak/22H |
|------|---------------|--------|----------------------|-----------------------|-----------------|
| 0    | 0.66          | 5      | 3.20                 | 2.94                  | 1.09            |
| 0.25 | 1.51          | >=10   | <1.60                | 1.95                  | <0.82           |
| 0.5  | 0.85          | 7      | 2.29                 | 2.59                  | 0.88            |
| 0.75 | 0.50          | 6      | 2.67                 | 3.38                  | 0.79            |
| 1    | 0.32          | 4      | 4.00                 | 4.26                  | 0.94            |

    lambda_select ∝ rho_eff^(-0.554 +/- 0.120),  Pearson r = -0.936,  n = 5,
    spanning a factor 4.8 in rho_eff.  Predicted exponent -1/2.

512x128x128 endpoints: lambda_peak/22H(rho_eff) = 0.987 (A = 0) and 0.839 (A = 1), against
1.088 and 0.939 at production resolution.

rho_eff is not monotonic in A: a large initial inward velocity overshoots and rebounds, so
the A = 1 run grows its modes at lower density than the A = 0.25 run. The control parameter
is the density at mode selection, not the contraction rate.

## 2. Core-masking radius sensitivity of the eligible line density

| r_mask (pc) | Orion B      | Aquila      | Perseus     | Taurus      |
|-------------|--------------|-------------|-------------|-------------|
| 0 (raw)     | 1.56 [417]   | 3.14 [306]  | 1.96 [199]  | 0.81 [186]  |
| 0.030       | 1.89 [317]   | 3.14 [306]  | 3.68 [85]   | 1.80 [43]   |
| 0.045       | 2.04 [277]   | 3.15 [305]  | 3.91 [70]   | 1.61 [37]   |
| 0.060       | 2.02 [268]   | 3.17 [303]  | 4.13 [57]   | 3.11 [13]   |
| 0.090       | 1.98 [252]   | 3.21 [296]  | 4.45 [41]   | -- [1]      |
| 0.120       | 1.95 [238]   | 3.20 [297]  | 3.62 [37]   | -- [1]      |

Cells: S_elig = (L_elig/N_elig)/W, with N_elig in brackets.

## 3. Moving-block bootstrap of the gap-model comparison

400 resamples per cloud of contiguous five-gap blocks drawn within single skeleton components.

| Cloud   | n_gaps | r1     | n_eff | dAICc periodic, median [5,95] | dAICc Poisson, median [5,95] |
|---------|--------|--------|-------|-------------------------------|------------------------------|
| Orion B | 699    | +0.035 | 651   | 507 [415, 599]                | 221 [190, 250]               |
| Aquila  | 168    | -0.146 | 225   | 69 [45, 97]                   | 83 [71, 102]                 |
| Perseus | 438    | +0.119 | 344   | 326 [249, 391]                | 35 [31, 48]                  |
| Taurus  | 440    | +0.564 | 122   | 696 [587, 803]                | 86 [55, 118]                 |

## 4. Persistence-threshold robustness

Branch-persistence pruning of the published 3-sigma skeletons (branch persistence =
(max N_H2 on branch - N_H2 at attaching junction)/sigma_map):

| Cloud   | 3 sigma (L pc, s_med pc, L/N pc) | 4 sigma              | 6 sigma              | 8 sigma              |
|---------|----------------------------------|----------------------|----------------------|----------------------|
| Orion B | 283.8, 0.1773, 0.2852            | 237.1, 0.1628, 0.2797| 236.2, 0.1628, 0.2792| 236.4, 0.1628, 0.2795|
| Aquila  | 96.8, 0.1662, 0.3141             | 81.8, 0.1617, 0.3040 | 81.8, 0.1617, 0.3040 | 81.2, 0.1617, 0.3018 |
| Perseus | 73.6, 0.2969, 0.1470             | 66.8, 0.2978, 0.1424 | 66.0, 0.3002, 0.1416 | 65.3, 0.3002, 0.1402 |
| Taurus  | 36.8, 0.1805, 0.0794             | 34.6, 0.1715, 0.0765 | 34.0, 0.1746, 0.0754 | 33.6, 0.1742, 0.0750 |

Merge-tree persistence extraction with a free threshold, Orion B:

| threshold | L (pc) | N_assoc | S_local | S_global | f_occ |
|-----------|--------|---------|---------|----------|-------|
| 2 sigma   | 160.7  | 635     | 1.63    | 2.53     | 0.409 |
| 3 sigma   | 153.9  | 615     | 1.63    | 2.50     | 0.413 |
| 4 sigma   | 147.8  | 597     | 1.63    | 2.48     | 0.416 |

## 5. Measurement counts adopted in the manuscript

| Region  | catalogue | associated | f_assoc | ACS pairs | S_local (fixed 0.10 pc) |
|---------|-----------|------------|---------|-----------|-------------------------|
| Orion B | 1870      | 995        | 0.53    | 699       | 1.77                    |
| Aquila  | 749       | 308        | 0.41    | 168       | 1.66                    |
| Perseus | 816       | 501        | 0.61    | 438       | 2.97                    |
| Taurus  | 536       | 463        | 0.86    | 440       | 1.81                    |

Effect of the morphological closing and the minimum-component-size filter on the
association count (both < 2 per cent):

| Region  | N_cat | raw  | closing only | minpix only | both |
|---------|-------|------|--------------|-------------|------|
| Orion B | 1870  | 1011 | 1010         | 992         | 995  |
| Aquila  | 749   | 315  | 314          | 304         | 308  |
| Perseus | 816   | 522  | 522          | 502         | 501  |
| Taurus  | 536   | 473  | 468          | 470         | 463  |

## 6. FilFinder configuration as run

FilFinder2D with the cloud distance set per region and an externally supplied mask
(`use_existing_mask=True`) followed by `medskel()`. The mask is a 92nd-percentile
column-density cut (Orion B: 2.46e21 cm^-2; 70th percentile 1.32e21 cm^-2). No adaptive
or branch thresholding is invoked.

## 7. Simulation initial condition as coded

Production (default) profile, Gaussian:

    rho(r) = rho_bg + rho_amp exp(-r^2 / 2 W_core^2),
    rho_amp = f M_line,crit / (2 pi W_core^2),   M_line,crit = 2 c_s^2 / G,
    rho_bg = 1,  W_core = 0.3 lambda_J

Equilibrium-control profile, Ostriker (p = 4):

    rho(r) = rho_bg + f rho_c,ost / [1 + (r/W_core)^2]^2,  rho_c,ost = 2 c_s^2/(pi G W_core^2)

B_0 = c_s sqrt(2 rho_bg / beta); velocity seed of 12 Kolmogorov modes k_n = 2 pi n / L_x with
A_n ~ k_n^(-11/6) and random phases; v_r = v_phi = 0 in the production runs.
