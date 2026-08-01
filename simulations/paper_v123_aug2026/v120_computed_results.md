# v120 computed results (cluster referee_v120*.py + projection MC)  Aug 2026 — 8th referee cycle

## R1-1 / R2-3.3  LOCAL-WIDTH per-segment Δs/W (perpendicular Gaussian FWHM at each gap midpoint, beam-deconv 18.2")
| Region | Npairs | median(Δs/W_loc) | mean | CoV | median W_loc(pc) | ratio-of-medians med(Δs)/med(W) | corr(Δs,W_loc) |
|--------|--------|------------------|------|-----|-----------------|-------------------------------|----------------|
| Taurus | 190fit | 0.61 | 2.72 | 2.52 | 0.129 | 1.40 | 0.10 |
| OrionB | 545fit | 0.91 | 1.63 | 1.52 | 0.154 | 1.15 | 0.04 |
| Perseus| 219fit | 1.05 | 2.86 | 2.27 | 0.154 | 1.93 | 0.31 |
| Aquila | 146fit | 0.99 | 1.72 | 1.47 | 0.137 | 1.21 | -0.06 |
=> Proper per-segment local normalization: median Δs/W_local ≈ 0.6–1.05, STILL sub-classical; weak Δs–W correlation;
   ratio-of-medians ≈ median-of-ratios within the convention envelope, so cloud-level ratio is NOT badly biased.

## R1-2  DIRECT LINE DENSITY N/L (ordering-independent: assoc cores / total skeleton arclength)
| Region | assoc | tot_skel(pc) | N/L(/pc) | 1/(N/L)(pc) | s_LD/Wplum | s_LD/Wfix | median NN(pc) |
|--------|-------|-------------|----------|-------------|-----------|-----------|---------------|
| Taurus | 463 | 209 | 2.21 | 0.452 | 5.20 | 4.52 | 0.181 |
| OrionB | 995 | 337 | 2.95 | 0.339 | 2.29 | 3.39 | 0.177 |
| Perseus| 501 | 290 | 1.73 | 0.578 | 5.35 | 5.78 | 0.297 |
| Aquila | 308 | 106 | 2.90 | 0.344 | 3.02 | 3.44 | 0.166 |
=> KEY TEMPERING: global core line density gives s/W ≈ 2.3–5.8; Taurus & Perseus NEAR-CLASSICAL, only OrionB clearly
   sub-classical. Mean adjacent gap inflated by skeleton branch-jumps (Taurus mean/med=2.24) => mean NOT robust; use
   median (robust descriptor) + N/L (robust line density). "Sub-classical" = CLUSTERING/intra-group statement, not a
   global line-density deficit.

## R1-3  1-D PAIR-CORRELATION g(s) along skeleton (vs uniform-random MC on matched components)
- Taurus: small-s(0.05-0.15) g=1.13; classical(0.48pc) g=1.04; global max s=0.07pc g=1.16
- OrionB: small-s g=1.03; classical(0.81) g=0.88; max s=1.02pc g=1.28
- Perseus: small-s g=1.05; classical(0.59) g=1.03; max s=0.77pc g=1.16
- Aquila: small-s g=1.00; classical(0.63) g=0.93; max s=1.12pc g=1.51
=> NO peak at classical scale (g≈1 there, OrionB/Aquila slightly <1). Mild small-scale excess (Taurus); weak ~1pc
   region-envelope features. => No hidden classical-scale comb.

## R1-4 / R3-M2  COVERAGE BIAS (2D Euclidean median NN, associated vs REJECTED cores; DisPerSE robust skel)
| Region | cov | medNN_assoc | medNN_rejected | rejected/assoc |
|--------|-----|-------------|----------------|----------------|
| Taurus | 0.86 | 0.053 | 0.157 | 2.96 |
| OrionB | 0.53 | 0.130 | 0.195 | 1.50 |
| Perseus| 0.61 | 0.137 | 0.287 | 2.09 |
| Aquila | 0.41 | 0.146 | 0.212 | 1.46 |
=> Rejected cores 1.5–3× MORE widely spaced => selection biases the median spacing SHORT (toward sub-classical),
   confirmed quantitatively (direction referee worried about). Add to Table 6 systematic budget.

## R1-5 / R2  FilFinder INJECTION-RECOVERY (synthetic periodic cores on FilFinder spine, arclength NN)
- Taurus 0.15->0.149 0.20->0.200 0.25->0.250 (|err|0.2%); OrionB |err|0.9%; Perseus 0.5%; Aquila 1.0%
=> recovered=injected to <1% => FilFinder's shorter s/W is REAL (denser, more-branched network = different object),
   NOT an estimator/branching artefact. Symmetric with DisPerSE inj-rec now.

## R1-5 persistence-threshold: deposited thresh15/20/25/50 maps are DEGENERATE (near-empty, cov<0.12) => unusable as
   a persistence ladder; rely on FilFinder cross-check + bridging/association-radius sensitivity (4-7%).

## R2-17 projection MC (v119): isotropic factor median 0.87 mean 0.79; deproject +15-27% (acts against sub-classical).

## R3-M5  Fiege-Pudritz order-of-magnitude (read-off, NOT a new eigensolve):
- FP2000 m=0 sausage on force-balanced helical equilibria: toroidally-dominated fields shorten fastest-growing λ to
  ~order the filament diameter vs ~4× diameter (~5-6 FWHM) for the unmagnetized Ostriker cylinder => up to ~factor 2
  shortening for strongly-wound fields. For our β≈0.3-2 (magnetic ~ thermal, not toroidally dominated) expect the
  LOW end, factor ≲2 => could supply PART but likely not all of the observed deficit. Present as OOM, flagged read-off.
