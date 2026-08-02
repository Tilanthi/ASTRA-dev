# v137 computed results — the two ESSENTIAL referee tests. Both change the paper's conclusions.

## TEST 1: INHOMOGENEOUS POISSON NULL, conditioned on local N_H2 (referee essential #1)
Empirical intensity lambda(N_H2) measured from the data itself (cores per pc in bins of column density),
then synthetic cores drawn on the ACTUAL skeletons with that intensity; 200 realisations; same pipeline.
| Region | F_obs(1pc) | null median | null 95th | p | verdict |
|--------|-----------|-------------|-----------|---|---------|
| OrionB | 2.84 | 3.83 | 4.65 | 0.995 | observed LESS over-dispersed than the inhomogeneous null |
| Aquila | 1.59 | 2.29 | 3.13 | 0.945 | same |
| Perseus| 5.73 | 7.34 | 8.73 | 0.965 | same |
| Taurus | 25.23 | 13.02 | 17.47 | **0.005** | genuine EXCESS over the null |
**CONCLUSION: the referee was right.** In 3 of 4 clouds the observed over-dispersion is FULLY accounted for
(indeed over-accounted) by the column-density structure of the parent filament. Only TAURUS shows intermittency
beyond what the filament's own inhomogeneity predicts. The claim of physical intermittency must be WEAKENED:
what is established is strongly inhomogeneous core occurrence, largely inherited from the filament structure.
Occupancy: obs 0.324/0.295/0.477/0.362 vs null median 0.288/0.270/0.407/0.490 -> only Taurus below null.

## TEST 2: FRAGMENTATION-ELIGIBLE LENGTH (referee essential #2)
Eligibility set INDEPENDENTLY of cores: N_H2 > 7.15e21 cm^-2, the column at which a 0.10 pc-wide filament
reaches M_line,crit = 16 Msun/pc (mu=2.8). Standard HGBS supercriticality threshold.
| Region | f_elig = L_el/L | N_el | (L/N)/W all | (L_el/N_el)/W eligible |
|--------|------|------|------|------|
| OrionB | 0.20 | 431 | 2.85 | **1.34** |
| Aquila | 0.87 | 308 | 3.14 | **2.73** |
| Perseus| 0.46 | 204 | 1.47 | **1.67** |
| Taurus | 0.36 | 193 | 0.79 | **0.69** |
**CONCLUSION: the near-classical global line density was largely an artefact of including subcritical filament
that was never eligible to fragment.** Restricted to supercritical material, the length per core is 0.7-2.7 W,
i.e. SUB-CLASSICAL in all four clouds. This RESOLVES the local/global tension: once only fragmentation-eligible
filament is counted, both the local and the global statistics agree that the spacing is sub-classical.
NOTE: these L use the per-component arclength (diameter) convention, so absolute (L/N)/W differ from the
edge-sum values quoted elsewhere (3.4-5.8); the eligible FRACTIONS and the eligible-vs-all RATIOS are the robust
outputs and are what the paper should quote.

## TEST 3: per-cloud statistics (for the requested table; fixes the R>1 error)
Paper's Fig 9 values: CoV Taurus 1.36 OrionB 0.83 Perseus 0.96 Aquila 0.65
                      R    Taurus 0.64 OrionB 1.03 Perseus 0.92 Aquila 1.14
R = observed median gap / median expected for an exponential of the same mean.
R>1 = deficit of small gaps (mild exclusion): ONLY OrionB (1.03) and Aquila (1.14).
R<1 = EXCESS of small gaps (small-scale clustering): Perseus (0.92) and Taurus (0.64).
=> the manuscript's blanket claim "deficit of the smallest separations (R>1)" is WRONG for 2 of 4 clouds
   and must be replaced by a per-cloud statement. F(1pc): 2.84/1.59/5.73/25.23. AICc-preferred gap model:
   lognormal (OrionB, Aquila, Taurus), shifted-exponential (Perseus).
