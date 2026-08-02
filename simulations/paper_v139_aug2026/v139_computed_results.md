# v139 computed results (3-referee round)

## R3#1 ELIGIBILITY WITH NON-THERMAL SUPPORT (virial line mass)
N_crit(W=0.10pc, T=10K, sigma_nt/c_s): thermal 7.3e21; transonic (sig_nt=c_s) 1.47e22; sig_nt=2c_s 3.67e22
(L_el/N_el)/W  [f_elig, N_el]:
| support | OrionB | Aquila | Perseus | Taurus |
|---------|--------|--------|---------|--------|
| thermal only | 1.56 [0.19,416] | 3.14 [0.91,306] | 1.96 [0.13,199] | 0.81 [0.07,186] |
| transonic    | 1.38 [0.07,166] | 1.76 [0.34,205] | 1.28 [0.03, 67] | 0.46 [0.01, 49] |
| sig_nt=2c_s  | 0.83 [0.01, 47] | 1.12 [0.05, 45] | 0.67 [0.01, 22] | -- [0.00, 0]   |
=> **Adding non-thermal support makes the eligible length SMALLER and the result MORE sub-classical.**
   The thermal-only choice is therefore the CONSERVATIVE one; the sub-classical conclusion survives and strengthens.
   At sigma_nt=2c_s the eligible lengths become tiny (0-5 pc, N_el 0-47) and the statistic degenerates - Taurus has
   no eligible filament at all. The transonic case is the physically reasonable comparison.

## R3#3 NON-INDEPENDENCE OF ADJACENT GAPS (autocorrelation + runs test)
| Region | lag-1 r (mean/median) | runs-test z | p |
|--------|----------------------|-------------|---|
| OrionB | -0.093 / -0.142 | +0.41 | 0.68 |
| Aquila | -0.135 / -0.151 | +0.36 | 0.72 |
| Perseus| +0.090 / +0.072 | **-4.15** | **<0.001** |
| Taurus | -0.051 / +0.018 | **-5.35** | **<0.001** |
=> lag-1 autocorrelation is WEAK everywhere (|r|<0.14), but the RUNS TEST shows significant non-independence in
   Perseus and Taurus (too few runs = similar-sized gaps grouped together, i.e. long gaps cluster in core-poor
   stretches - exactly the inhomogeneity documented elsewhere). Orion B and Aquila are consistent with independence.
   CONSEQUENCE: the KS/AICc p-values are optimistic for Perseus and Taurus; the effective number of independent
   gaps is smaller than N. Must be stated. The two-sided rejection is so strong (dAICc 37-742) that it survives a
   large reduction in effective N, but the quoted p-values should not be read at face value for those two clouds.

## R3#2 MASKED NULL (mask 0.06 pc around each core, rebuild the exposure)
Ratio lambda_masked/lambda_unmasked per column-density bin rises steeply with N_H2:
  OrionB 1.06 -> 5.70 ; Aquila 1.05 -> 3.93 ; Perseus 1.16 -> 9.93 ; Taurus 1.20 -> 6.98
=> Masking removes a large fraction of the HIGHEST-column skeleton length, i.e. the highest-column material is
   largely core-adjacent. The null's intensity in its top bins is therefore poorly constrained by core-free
   filament. DIRECTION OF BIAS: because the unmasked null assigns high intensity to pixels that are themselves
   core sites, it reproduces the observed clumping too easily, so it is CONSERVATIVE against detecting excess
   clustering. The "three of four show no excess" result may therefore be partly an artefact of that construction;
   TAURUS, which exceeds the null even so, is strengthened. Must be stated as a limitation.
