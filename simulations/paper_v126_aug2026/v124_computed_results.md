# v124 computed results (cluster rv124*.py)  Aug 2026 — 9th referee cycle

## Coverage-bias BOUND (R2#4/R3#2)  [association radius 0.06->0.30 pc]
| Region | assoc@0.06 | assoc@0.30 | median/W @0.06 | median/W @0.30 | shift |
|--------|-----------|-----------|----------------|----------------|-------|
| OrionB | 53% | 85% | 1.77 | 1.96 | +11% |
| Aquila | 41% | 70% | 1.66 | 1.94 | +16% |
| Perseus| 61% | 85% | 2.97 | 3.20 | +8% |
| Taurus | 86% | 97% | 1.81 | 1.86 | +3% |
=> Adding back the rejected cores (to 70-97% coverage) lengthens the median adjacent spacing by only +3..+16%;
   stays sub-classical. Coverage bias is bounded at <~16%, one-sided (toward classical). Add to error budget as a NUMBER.
   (Note assoc% here are the re-implementation's; paper's adopted per-Table are 24/37/76/89% at the tighter def.)

## Three-tier line density (fixed W=0.10 pc), all same re-implementation (R2#1/#5, R3#6)
| Region | median adj s/W (intra-cluster) | mean adj s/W (core-bearing avg) | full-skel (L/N)/W |
|--------|-------------------------------|--------------------------------|-------------------|
| OrionB | 1.8 | 2.5 | 3.4 |
| Aquila | 1.7 | 2.1 | 3.4 |
| Perseus| 3.0 | 4.7 | 5.8 |
| Taurus | 1.8 | 4.0 | 4.5 |
=> hierarchy median < mean < full-L/N. The near-classical global L/N (3.4-5.8) is PARTLY clustering (median->mean skew)
   and PARTLY dilution by core-poor filament (mean->full). Honest reframe: no quasi-periodic comb; clustered/intermittent
   local spacing sub-classical, global line density diluted toward classical. (pair-correlation flat, no comb - fig_paircorr)

## Unbranched-segment analysis (R2#3): ATTEMPTED, degenerate.
- Naive junction-removal on the morphologically-bridged skeleton over-fragments: 300-3200 segments, only 13-20 with >=2
  cores; per-segment stats dominated by fragmentation, not usable. A clean per-segment statistic needs collinear-segment
  merging across spurious bridging junctions (itself the "what is a filament" ambiguity). REPORT as deferred + address the
  underlying concern via coverage sensitivity (above) + three-tier decomposition + DisPerSE/FilFinder envelope.

## Aquila LOS depth (R3#3): cite Zucker2020 (Aquila/Serpens ~ tens of pc LOS depth in 3D dust); keep as sourced bound.
## L/3 bias priority (R3#4): rephrase novelty = "identifying region-extent bias as the source of the HGBS pairwise-median
   discrepancy", not new order statistics (triangular-dist median is textbook). Cite Clark-Evans / point-process context.
## FP eigenvalue (R1#2/R3#1): rebalance abstract (option b: strongest UNTESTED candidate is magnetic); add explicit
   force-balanced helical initialization criteria to roadmap; keep Table14 "<~2x" labelled OOM (done).
