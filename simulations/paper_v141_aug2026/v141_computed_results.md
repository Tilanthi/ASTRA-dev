# v141 computed results (August 2026 referee round)

All three reports asked for new computations. These were run on the cluster against the
HGBS column-density maps, published DisPerSE skeleton maps and observed core catalogues.

## 1. Core-masking radius sensitivity (Referee 2, item 3)
Script: `/tmp/rv141b.py`. The core-masked eligibility reconstruction of v140 fixed the
masking radius at 0.06 pc. Varying it 0.03-0.12 pc:

| r_mask (pc) | Orion B      | Aquila      | Perseus     | Taurus      |
|-------------|--------------|-------------|-------------|-------------|
| 0 (raw)     | 1.56 [417]   | 3.14 [306]  | 1.96 [199]  | 0.81 [186]  |
| 0.030       | 1.89 [317]   | 3.14 [306]  | 3.68 [85]   | 1.80 [43]   |
| 0.045       | 2.04 [277]   | 3.15 [305]  | 3.91 [70]   | 1.61 [37]   |
| 0.060       | **2.02** [268] | **3.17** [303] | **4.13** [57] | (3.11) [13] |
| 0.090       | 1.98 [252]   | 3.21 [296]  | 4.45 [41]   | -- [1]      |
| 0.120       | 1.95 [238]   | 3.20 [297]  | 3.62 [37]   | -- [1]      |

(cells are S_elig = (L_elig/N_elig)/W with N_elig in brackets)

**Verdict**: Orion B and Aquila are stable to within 8% and 2%. Perseus drifts 3.6-4.5.
**Taurus is an artefact of the specific masking radius** (1.8 -> 1.6 -> 3.1 over 0.03-0.06 pc,
then N_elig = 1). The Taurus S_elig value is WITHDRAWN from the paper.

## 2. Moving-block bootstrap of the gap-model comparison (Referee 2, item 2)
400 resamples per cloud of contiguous 5-gap blocks drawn within single skeleton components.

| Cloud   | n_gaps | r1     | n_eff | dAICc periodic (median [5,95]) | dAICc Poisson (median [5,95]) |
|---------|--------|--------|-------|-------------------------------|-------------------------------|
| Orion B | 699    | +0.035 | 651   | 507 [415, 599]                | 221 [190, 250]                |
| Aquila  | 168    | -0.146 | 225   | 69 [45, 97]                   | 83 [71, 102]                  |
| Perseus | 438    | +0.119 | 344   | 326 [249, 391]                | 35 [31, 48]                   |
| Taurus  | 440    | +0.564 | 122   | 696 [587, 803]                | 86 [55, 118]                  |

**Verdict**: the two-sided rejection (both periodic AND pure-Poisson) SURVIVES in all four
clouds under block resampling, even in Taurus where n_eff falls to 122 of 440. The claim is
UPGRADED, not downgraded. What does not survive is discrimination among the broad models:
shifted-exponential sits inside the lognormal bootstrap interval in Orion B, Aquila, Perseus.

## 3. Persistence-threshold robustness (Referee 3, item 2 - "essential")
Script: `/tmp/rv141.py` (branch pruning) and `/tmp/rv141c.py` (independent extraction).

### (a) Branch-persistence pruning of the published 3-sigma skeleton, all four clouds
Branch persistence = (max N_H2 on branch - N_H2 at attaching junction)/sigma_map.

| Cloud   | 3sig (published)              | 4sig                | 6sig     | 8sig     |
|---------|-------------------------------|---------------------|----------|----------|
| Orion B | L=283.8 pc, s=0.1773, L/N=0.2852 | 237.1, 0.1628, 0.2797 | 236.2, 0.1628, 0.2792 | 236.4, 0.1628, 0.2795 |
| Aquila  | 96.8, 0.1662, 0.3141          | 81.8, 0.1617, 0.3040 | 81.8, 0.1617, 0.3040 | 81.2, 0.1617, 0.3018 |
| Perseus | 73.6, 0.2969, 0.1470          | 66.8, 0.2978, 0.1424 | 66.0, 0.3002, 0.1416 | 65.3, 0.3002, 0.1402 |
| Taurus  | 36.8, 0.1805, 0.0794          | 34.6, 0.1715, 0.0765 | 34.0, 0.1746, 0.0754 | 33.6, 0.1742, 0.0750 |

3sig -> 4sig removes 15-21% of skeleton length but changes s_ACS,med by only
-8.2/-2.7/+0.3/-5.0% and L/N by -1.9/-3.2/-3.1/-3.7%. Saturates beyond 4sig.
(Lengths here are component-diameter sums, not the paper's edge-sums; only the
fractional changes are quoted in the paper.)

### (b) Independent persistence-thresholded extraction (from-scratch merge tree), Orion B
Descending-sweep merge tree -> persistence pairing of maxima -> steepest-ascent ridge walk
from retained saddles. Threshold is a free parameter, so the 2-sigma direction is accessible.

| threshold | L (pc) | N_assoc | S_local | S_global | f_occ |
|-----------|--------|---------|---------|----------|-------|
| 2 sigma   | 160.7  | 635     | 1.63    | 2.53     | 0.409 |
| 3 sigma   | 153.9  | 615     | 1.63    | 2.50     | 0.413 |
| 4 sigma   | 147.8  | 597     | 1.63    | 2.48     | 0.416 |

**Verdict**: S_local is unchanged to three significant figures over a factor of two in
persistence threshold; S_global moves 2%. The persistence threshold is NOT the source of
the factor-of-two DisPerSE/FilFinder difference; the filament ONTOLOGY is.
(Aquila/Perseus/Taurus runs of (b) were still executing at write-up; (a) covers all four.)

## 4. FilFinder parameters as actually used (Referee 3, item 3)
The Fig. 2 caption previously quoted a global threshold 3e21 cm^-2, adaptive threshold
0.1 pc and **branch threshold 40 pc**. Inspection of the analysis code shows FilFinder2D
was run with an EXTERNALLY SUPPLIED mask (`use_existing_mask=True`) followed by `medskel()`,
so no adaptive or branch thresholding was invoked at all. The mask is a 92nd-percentile
column-density cut:

| Cloud   | 70th pct N_H2 (cm^-2) | 92nd pct N_H2 (cm^-2) |
|---------|-----------------------|-----------------------|
| Orion B | 1.32e21               | 2.46e21               |

The referee was right that "40 pc" is impossible. The caption has been corrected to state
what was actually done, and the error is acknowledged in the caption itself.

## 5. Initial condition of the production simulations (Referee 3, item 4)
The manuscript stated rho(r) = rho_0/[1+(r/W)^2], a p=2 Plummer with divergent line mass.
Inspection of the problem generator (`filament_ambient.cpp` / `filament_spacing.cpp`) shows
the default and production profile is GAUSSIAN:

    rho(r) = rho_bg + rho_amp * exp(-r^2 / 2 W_core^2),
    rho_amp = f * M_line,crit / (2 pi W_core^2),  M_line,crit = 2 c_s^2 / G,
    rho_bg = 1 (uniform ambient), W_core = 0.3 lambda_J

and the alternative (used for the equilibrium-recovery control) is the Ostriker p=4 profile:

    rho(r) = rho_bg + f rho_c,ost / [1 + (r/W_core)^2]^2,  rho_c,ost = 2 c_s^2/(pi G W_core^2)

Neither is p=2. Both have convergent line mass, so no truncation radius is needed; f is
imposed exactly by the rho_amp normalisation. B_0 = c_s sqrt(2 rho_bg/beta). Velocity seed:
12 Kolmogorov modes k_n = 2 pi n / L_x, A_n ~ k_n^(-11/6), random phases. v_r = v_phi = 0.
Section 4.1 has been rewritten with the full specification and the previous statement is
flagged in the text as an error.
