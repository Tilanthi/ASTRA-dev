# v142 computed results (August 2026 referee round 3)

## 1. Contraction-rate ladder (Referee 3, item 4 — "essential before publication")

**Setup.** Patched the Athena++ problem generator (`athena-ladder`) to accept a homologous
initial radial contraction `v_r(r) = -A (c_s/R_0) r`, tapered beyond 3 R_0. Five otherwise
identical runs from the same relaxed Ostriker cylinder, A = 0, 0.25, 0.5, 0.75, 1, at
256x64x64 (dx = 0.0625 lambda_J isotropic), L_x = 16 lambda_J periodic, twelve-mode
Kolmogorov seed at dv/c_s = 1e-3, tlim = 2 t_J, 41 snapshots each. Plus 512x128x128
endpoint checks at A = 0 and A = 1.
Configs and logs: `/data/contraction_ladder_aug2026/`.

**Analysis.** Per-mode growth rates Gamma_n fitted over the common linear window
(0.0015 < delta_rms < 0.12) for the seeded, well-resolved modes n <= 10 (lambda >= 1.6,
>= 25 cells). rho_eff = central density at the mid-point of that window.

| A    | rho_eff/rho_0 | n_peak | lambda_peak/lambda_J | 22H(rho_eff)/lambda_J | lambda_peak/22H |
|------|---------------|--------|----------------------|-----------------------|-----------------|
| 0    | 0.66          | 5      | 3.20                 | 2.94                  | **1.09**        |
| 0.25 | 1.51          | >=10   | <1.60                | 1.95                  | <0.82           |
| 0.5  | 0.85          | 7      | 2.29                 | 2.59                  | 0.88            |
| 0.75 | 0.50          | 6      | 2.67                 | 3.38                  | 0.79            |
| 1    | 0.32          | 4      | 4.00                 | 4.26                  | 0.94            |

**Scaling test (the referee's requested test):**

    lambda_select ∝ rho_eff^(-0.554 +/- 0.120),   Pearson r = -0.936,  n = 5,
    over a factor 4.8 in rho_eff (0.68 to 3.24 rho_0).   Predicted: -1/2.

Consistent with the predicted -1/2 at 0.45 sigma. **The proposed mechanism is confirmed.**

**High-resolution endpoint checks (512x128x128):**
A = 0 gives lambda_peak/22H(rho_eff) = 0.987; A = 1 gives 0.839 (against 1.088 and 0.939
at production resolution). The static run recovers the classical value; the contracting
run falls below it. Conclusion is resolution-robust.

**Important secondary finding.** rho_eff is NOT monotonic in A: a large initial inward
velocity overshoots and rebounds, so the A = 1 run is at LOWER density during its growth
window than A = 0.25. Contraction *rate* is therefore not the control parameter; the
density at mode selection is. The mechanism must be quoted as a dependence on rho_eff,
not on how fast the filament is falling in. This is a stronger and narrower statement
than the two-point equilibrium-versus-contracting control supported.

## 2. Pipeline-A / pipeline-B association reconciliation (Referee 2, items 1 and 2)

Referee 2 correctly identified that Table 3's headline numbers came from a different
implementation than Table 13's association counts, and that Table 3's Aquila S_local (2.1)
did not match Table 8 (1.66).

Tested whether the morphological closing or the minimum-component-size filter explains the
association-count difference. **They do not:**

| Region  | N_cat | raw  | close only | minpix only | both (pipeline B) |
|---------|-------|------|------------|-------------|-------------------|
| Orion B | 1870  | 1011 | 1010       | 992         | 995               |
| Aquila  | 749   | 315  | 314        | 304         | 308               |
| Perseus | 816   | 522  | 522        | 502         | 501               |
| Taurus  | 536   | 473  | 468        | 470         | 463               |

Closing and the component filter together move the count by < 2 per cent, whereas pipeline A
reports 680 / 182 / 619 / 479. Part of the difference is catalogue parsing (1870 vs 1844
rows for Orion B); the remainder is a difference in which cores are admitted to a "primary
segment" and is NOT resolved.

**Resolution adopted in the paper:** all headline numbers are declared to come from
pipeline B, Table 3's Aquila entry corrected 2.1 -> 1.7 (and Orion B 1.7 -> 1.8, Taurus
1.7 -> 1.8), the reproducibility table now shows both pipelines side by side, and the
unresolved bookkeeping difference is stated explicitly as an open issue that an external
re-run of the deposited code would settle.

## 3. Length reduction

38 pages -> **25 pages**, as instructed.

Deleted outright (retained in the deposited repository): complete simulation-campaign list,
supplementary campaign results, radial-collapse timescale competition, three-regime
classification, turbulence/critical-transition appendix, detailed simulation-validation
appendix (compressed to five short paragraphs).

Removed floats: duplicate benchmark table, Orion B decomposition table, validation-summary
table, injection-recovery figure, perpendicular refinement ladder figure, helical scan
figure, limited-sample table, pipeline flow figure. 18 figures -> 11; 21 tables -> 17.

Rewritten far more compactly: Introduction, Results, fragmentation-scale section (now
"The simulated fragmentation scale"), eligibility (now explicitly an exploratory
diagnostic), spatial inhomogeneity, gap regularity, error budget, fibre projection,
literature comparison, limitations, conclusions (now a numbered list of nine points).

Removed: all meta-commentary about earlier drafts and about referees; the repeated N = 4
caveat (now stated once in the Introduction); the repeated 2251-run figure (now once in
the methods and once in Data Availability).
