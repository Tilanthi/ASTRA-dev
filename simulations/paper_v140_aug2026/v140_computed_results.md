# v140 — THE CORE-MASKED ELIGIBILITY TEST (referee-2 essential). RESULT: WEAKENS OUR CLAIM.
Eligibility recomputed on a CORE-MASKED BACKGROUND column density: skeleton pixels within 0.06 pc of an associated
core have their N_H2 replaced by interpolation along the spine from untainted pixels, then the M_line,crit threshold
is applied to that reconstructed background. 25-34% of skeleton pixels are core-tainted.
| Region | f_elig raw | N_el raw | S_elig raw | f_elig masked | N_el masked | **S_elig masked** |
|--------|-----------|----------|-----------|---------------|-------------|-------------------|
| OrionB | 0.19 | 417 | 1.56 | 0.16 | 268 | **2.02** |
| Aquila | 0.91 | 306 | 3.14 | 0.90 | 303 | **3.17** |
| Perseus| 0.13 | 199 | 1.96 | 0.08 |  57 | **4.13** |
| Taurus | 0.07 | 186 | 0.81 | 0.02 |  13 | **3.11** |
**CONCLUSION: the raw eligibility criterion WAS partly endogenous.** Cores raise their own local column density above
the threshold, so raw eligibility preferentially selects core sites and artificially depresses L_elig/N_elig.
With the core contribution removed, S_elig = 2.0-4.1 (vs raw 0.8-3.1): still below the classical 5-6 in all four
clouds, but with MUCH reduced margin, and Aquila is only marginal.
**CRITICAL CAVEAT**: N_elig collapses in Perseus (199->57) and Taurus (186->13). With 13 cores the Taurus value is
not a usable statistic. The strong "sub-classical in all four clouds on eligible filament" claim DOES NOT SURVIVE
in its previous form and must be substantially weakened. Adopt the core-masked values as fiducial, quote the raw
values as the endogeneity-affected comparison, and flag Perseus/Taurus as sample-limited.

## 2. Inhomogeneous-null Fano test, 10,000 realisations (was 200)
Intensity lambda(x) ∝ [max(N_H2(x) − 1e21, 0)]^alpha, alpha fitted by ML with
leave-one-cloud-out cross-validation (alpha = 1.6–2.4, CV mean 2.0); normalisation
fixed so each realisation contains N_obs cores. Empirical p = (1+#{F_null ≥ F_obs})/(1+N_MC).

| Region  | F_obs | null median | 95th pct | p        |
|---------|-------|-------------|----------|----------|
| Orion B | 2.84  | 3.64        | —        | 0.9844   |
| Aquila  | 1.59  | 2.13        | —        | 0.8823   |
| Perseus | 5.73  | 7.14        | —        | 0.9552   |
| Taurus  | 25.23 | 13.41       | 17.1     | 0.0002   |

Taurus is now resolved rather than sitting at the Monte-Carlo floor (was p=0.005 at N=200).

## 3. Pair-correlation null envelopes at the classical scale
95 per cent pointwise envelope from the same null. Observed g at 5.5 W_fil:

| Region  | g_obs | 95% envelope   | inside? |
|---------|-------|----------------|---------|
| Orion B | 1.02  | [0.84, 1.26]   | yes     |
| Aquila  | 0.89  | [0.58, 1.52]   | yes     |
| Perseus | 1.02  | [0.91, 1.14]   | yes     |
| Taurus  | 1.00  | [0.91, 1.10]   | yes     |

=> "no statistically significant classical-scale periodicity" is now a calibrated
statement rather than a visual one.

## Note on the null's direction of bias
The intensity is built from the observed column density, which the cores themselves
raise. The null therefore already contains part of the signal being tested for, so it
is biased AGAINST detecting excess clumping. The three non-detections are upper limits
on excess clumping, not evidence of its absence. This caveat is now carried into
Section 2.11, Table 9, the abstract and the Conclusions.
