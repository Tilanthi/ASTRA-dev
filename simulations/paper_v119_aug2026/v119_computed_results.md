# v119 computed results (cluster referee_v119.py + local projection MC)  Aug 1 2026

## R2#1 Mean vs median adjacent spacing (independent re-implementation, half_pc=0.06)
| Region | N | median(pc) | mean(pc) | mean/med | CoV |
|--------|---|-----------|----------|----------|-----|
| OrionB | 699 | 0.177 | 0.249 | 1.40 | 0.83 |
| Aquila | 168 | 0.166 | 0.211 | 1.27 | 0.65 |
| Perseus| 438 | 0.297 | 0.465 | 1.57 | 0.96 |
| Taurus | 440 | 0.181 | 0.404 | 2.24 | 1.36 |
- mean/median = 1.27-2.24 (consistent with skewed/near-exponential gaps; exp gives 1.44).
- Using MEAN raises s/W toward classical (referee correct: paper's "only deepens" was BACKWARDS).
- Even mean stays sub-classical: s_mean/W ~ 1.7-4.7 (< classical 5-6). Adopted (lam/W)0~1.4 median -> ~2.0-2.2 mean-based.

## R2#14/#15 AICc gap-model comparison (dAICc, 0=best; k=free params)
| Region | Poisson(k=1) | shifted-exp(2) | periodic-Gauss(2) | gamma(2) | lognormal(2) |
|--------|------|------|------|------|------|
| OrionB | 245.8 | 46.4 | 580.0 | 87.1 | 0.0 |
| Aquila | 82.8 | 5.8 | 81.1 | 11.0 | 0.0 |
| Perseus| 37.1 | 0.0 | 367.3 | 22.4 | 2.5 |
| Taurus | 98.3 | 76.1 | 741.8 | 89.9 | 0.0 |
- LOGNORMAL best in 3/4 (OrionB,Aquila,Taurus); shifted-exp best in Perseus (lognormal Δ2.5, ~tied).
- Poisson (37-246) AND periodic (81-742) both strongly disfavoured EVERYWHERE -> two-sided result SURVIVES.
- BUT hard-core shifted-exp is NOT uniquely best -> soften "hard core"; broad skewed law (lognormal) fits best;
  small-gap deficit -> instrumental exclusion, not a demonstrated physical hard core. AICc correction tiny (n>>k).

## R2#3 Association-fraction sensitivity (median gap vs relaxed inclusion)
- OrionB frac 0.48->0.63: median 0.187->0.168 (spread ~11%)
- Aquila frac 0.37->0.48: median 0.173->0.160 (~8%)
- Perseus frac 0.47->0.74: median 0.315->0.312 (~2%, flat)
- Taurus frac 0.71->0.93: median 0.181->0.181 (flat, ~4%)
=> median spacing varies <~11% across a 15-30pt change in associated fraction and does NOT trend toward classical.
   Sub-classical result is NOT an artefact of selecting a core minority.

## R2#17 Projection inclination Monte-Carlo (isotropic 3D orientation)
- projection factor f=s_obs/s_true=sin(theta): median 0.866, mean 0.786, 16-84%=[0.54,0.99]
- deprojection multiplies observed spacings by 1.15 (median) / 1.27 (mean)
- adopted median s/W=1.4 -> 1.6 (median-corr) / 1.8 (mean-corr): sub-classical robustly survives (still << 5-6)

## R3#2 Arithmetic fix
- region-Plummer (lam/W)0=1.4 -> 5/1.4=3.6, 6/1.4=4.3  => region-Plummer-ONLY ratio 3.6-4.3 (NOT 2.5-4)
- "2.5-4" needs fixed-width DisPerSE folded in (5/2.1=2.4). Abstract must say so, or quote 3.6-4.3 for region-Plummer.
