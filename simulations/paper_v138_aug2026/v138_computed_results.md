# v138 computed results (3-referee round)

## R1#4 CROSS-VALIDATED inhomogeneous null (leave-one-cloud-out intensity; referee: is it circular?)
lambda(N_H2) built from the OTHER three clouds, tested out-of-sample on the held-out cloud, 200 realisations:
| Held-out | F_obs | out-of-sample null median (95th) | p |
|----------|-------|----------------------------------|---|
| OrionB | 2.84 | 4.00 (4.94) | 1.000 |
| Aquila | 1.59 | 1.33 (2.20) | 0.274 |
| Perseus| 5.73 | 7.89 (9.42) | 0.995 |
| Taurus | 25.23 | 8.82 (12.74) | **0.005** |
=> **"Only Taurus shows excess clumping" SURVIVES out-of-sample validation.** Not an artefact of fitting the
   intensity to the same cores. Aquila moves from p=0.945 (in-sample) to 0.274 (out-of-sample) but stays consistent.

## R1#3 ELIGIBLE LENGTH — corrected convention + full sensitivity
**IMPORTANT: v137 quoted 1.34/2.73/1.67/0.69, computed with eligible length on a pixel/edge basis but total length
on a per-component DIAMETER basis. Inconsistent. Recomputed with EDGE-SUM for BOTH (matching the paper's
(L/N)/W = 3.39/3.44/5.78/4.52).**
(L_el/N_el)/W at each threshold [f_elig in brackets]:
| thr (cm^-2) | OrionB | Aquila | Perseus | Taurus |
|------|--------|--------|---------|--------|
| 4e21  | 1.90 [0.43] | 3.44 [1.00] | 3.47 [0.52] | 1.87 [0.36] |
| 6e21  | 1.68 [0.26] | 3.44 [1.00] | 2.31 [0.21] | 0.98 [0.12] |
| **7.15e21 (fiducial)** | **1.57 [0.20]** | **3.18 [0.92]** | **2.03 [0.14]** | **0.84 [0.08]** |
| 9e21  | 1.52 [0.15] | 2.71 [0.75] | 1.84 [0.09] | 0.70 [0.04] |
| 1.2e22| 1.50 [0.10] | 1.99 [0.48] | 1.43 [0.04] | 0.55 [0.02] |
| local W, T=10K | 1.73 [0.33] | 3.40 [0.99] | 2.08 [0.16] | 0.76 [0.05] |
| T=15K, W=0.13pc| 1.59 [0.16] | 2.84 [0.81] | 1.90 [0.10] | 0.76 [0.05] |
=> (L_el/N_el)/W = 0.8-3.4 across ALL variants; sub-classical in all four clouds (Aquila only marginally).
   The trend is MONOTONIC: a stricter eligibility threshold makes it MORE sub-classical, so the fiducial choice is
   conservative. Local-width and warmer-gas variants change little. Conclusion is robust to the criterion.
