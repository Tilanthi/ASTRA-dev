# v130 computed results (10th cycle)  Aug 2026

## INTERMITTENCY / DUTY CYCLE  (R1-9 "most valuable new analysis"; R1-2 table)
Occupancy half-length 0.06 pc per core; cell size 1 pc for counts-in-cells.
| Region | half(pc) | L_tot(pc) | L_core(pc) | duty | N_assoc | f_assoc | (L/N)/W | (L_core/N)/W | med/W | mean/W | Fano(1pc) | Gini |
|--------|------|-------|------|------|------|------|------|------|------|------|------|------|
| OrionB | 0.06 | 337.3 | 92.0 | 0.27 | 995 | 0.53 | 3.39 | 0.92 | 1.77 | 2.49 | 2.84 | 0.49 |
| OrionB | 0.30 | 337.3 | 116.9| 0.35 | 1591| 0.85 | 2.12 | 0.74 | 1.96 | 2.51 | 4.46 | 0.50 |
| Aquila | 0.06 | 106.0 | 28.6 | 0.27 | 308 | 0.41 | 3.44 | 0.93 | 1.66 | 2.11 | 1.59 | 0.40 |
| Aquila | 0.30 | 106.0 | 38.3 | 0.36 | 521 | 0.70 | 2.03 | 0.73 | 1.94 | 2.29 | 2.05 | 0.36 |
| Perseus| 0.06 | 289.6 | 35.1 | 0.12 | 501 | 0.61 | 5.78 | 0.70 | 2.97 | 4.65 | 5.73 | 0.43 |
| Perseus| 0.30 | 289.6 | 39.8 | 0.14 | 691 | 0.85 | 4.19 | 0.58 | 3.20 | 4.89 |10.47 | 0.47 |
| Taurus | 0.06 | 209.5 | 13.3 | 0.06 | 463 | 0.86 | 4.52 | 0.29 | 1.81 | 4.04 |25.23 | 0.57 |
| Taurus | 0.30 | 209.5 | 13.9 | 0.07 | 518 | 0.97 | 4.04 | 0.27 | 1.86 | 3.98 |27.31 | 0.57 |

**KEY**: duty cycle 6-27% of skeleton is core-bearing. Fano factor at 1 pc = 1.6-25.2 (ALL > 1) => statistically
significant OVER-DISPERSION (clustering) on ~pc scales, while the GAP statistics show small-scale EXCLUSION
(CoV<=1, Clark-Evans R>1). Two-scale behaviour = INTERMITTENCY, now MEASURED not inferred. Gini 0.36-0.57.

### core-free run lengths WITHIN core-bearing components (pc), half=0.06
- OrionB N=740 med 0.11 mean 0.21 90th 0.51 max 2.05; frac length in runs>1pc = 0.15
- Aquila N=277 med 0.11 mean 0.18 90th 0.42 max 1.53; 0.05
- Perseus N=207 med 0.08 mean 0.14 90th 0.30 max 1.22; 0.04
- Taurus  N= 33 med 0.05 mean 0.11 90th 0.24 max 0.84; 0.00
NOTE: components with ZERO cores contribute additional core-free length (e.g. OrionB: 92 occupied + ~155 in-run
= 247 pc of 337 pc total, so ~90 pc lies in wholly core-free components).

## AQUILA LOS-DEPTH toy model (R2-3.3, R3-4)  [CORRECTS A SIGN ERROR IN THE PAPER]
Two crests blended along the LOS at d=436 pc, intrinsic s0=0.20 pc:
- depth 10/20/40/60 pc -> median projected spacing / true = 0.41/0.44/0.47/0.49 (i.e. -59% to -51%)
- pure distance-depth scaling alone: +/-1.1/2.3/4.6/6.9%
=> Chance superposition INTERLEAVES cores and SHORTENS the median ACS (worst case ~-50%), so LOS blending
   biases the ACS toward MORE sub-classical, NOT less. Paper previously said "inflate by tens of per cent" - WRONG SIGN.
   Realistic effect much smaller (most associated cores lie on coherent crests); carry as one-sided bounded systematic.

## BOOTSTRAP p-FLOOR raised 1e3 -> 1e5 (R3-6)
| Region | n | D_exp | p_exp | D_per | p_per |
|--------|---|-------|-------|-------|-------|
| OrionB | 699 | 0.174 | <1e-5 | 0.163 | <1e-5 |
| Aquila | 168 | 0.216 | <1e-5 | 0.194 | <1e-5 |
| Perseus| 438 | 0.070 | 1.7e-3| 0.167 | <1e-5 |
| Taurus | 440 | 0.156 | <1e-5 | 0.238 | <1e-5 |
=> replace "p_boot<1e-3" with these; Perseus exponential is the only non-floor value (1.7e-3).
