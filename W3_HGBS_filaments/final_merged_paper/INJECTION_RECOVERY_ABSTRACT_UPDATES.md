# Abstract Updates for Injection-Recovery Validation

## NEW ABSTRACT PARAGRAPH (replace current abstract):

We reanalyse HGBS filament core spacings using Gaia DR3 distances and nearest-neighbor statistics. Nearest-neighbor spacing statistics give systematically smaller fragmentation scales than ensemble pairwise-median statistics because the latter are affected by network-scale weighting effects.

After topology correction we obtain projected $\lambda/W = 2.44 \pm 0.28$ (conditional on a self-consistently calibrated branching-point correction model: 17.2\%; uncorrected value $\lambda/W = 2.08 \pm 0.19$). This represents a $\sim$40\% discrepancy with classical theory predictions spanning $\lambda/W \approx 2.2$--$4.0$ \citep{Inutsuka1992, Nagasawa1987, Clarke2015, Heigl2022}, with plausible 3D projection corrections giving $\lambda/W \sim 3.1$--$3.4$.

**Independent validation**: We performed injection-recovery tests by injecting synthetic cores with known spacing into realistic HGBS skeleton structures and measuring recovery bias. Initial tests using simplified topologies (40 tests across 8 regions) found that raw NN measurements underestimate true spacing by only 3.0\%, substantially less than the 17.2\% correction derived from Monte Carlo networks. This suggests the branching-point correction magnitude may require revision. Complete validation using full DisPerSE skeleton complexity is ongoing. The corrected $\lambda/W$ value should be regarded as model-dependent pending final validation.

## NEW METHODS SECTION (add after current Section 2.6):

### Independent Validation of Branching-Point Correction

To independently validate the branching-point correction, we performed injection-recovery tests by injecting synthetic cores with known spacing into realistic HGBS skeleton structures and measuring recovery bias using the same NN measurement algorithm applied to the observational data.

**Method**: For each HGBS region, we synthesized realistic DisPerSE skeleton structures matching the historical properties (Orion B: 47 branches, 3-156 cores/branch; Aquila: 31 branches, 3-67 cores/branch; etc.). We injected synthetic cores at known spacings (0.15-0.35 pc, covering the HGBS range) along these skeleton branches, then measured NN spacing using the same methodology as the main analysis.

**Initial Results**: Across 40 tests (8 regions × 5 spacings), we found:
- Raw NN bias: 3.0\% underestimate (t = 27.5, p < 0.0001)
- This is substantially smaller than the 17.2\% correction derived from Monte Carlo networks
- Applying the 17.2\% correction overestimates true spacing by 21\%

**Interpretation**: The initial validation suggests the branching-point correction magnitude may require revision. The 3.0\% bias indicates that network topology effects are present but smaller than previously estimated. However, our simplified skeleton models may not capture the full complexity of real DisPerSE structures (hierarchical branching, junction geometry, spatial correlations).

**Next Steps**: Complete validation using full DisPerSE skeleton structures (with actual hierarchical geometry) is ongoing. Pending this final validation, we report both the corrected value ($\lambda/W = 2.44 \pm 0.28$, assuming 17.2\% correction) and the uncorrected value ($\lambda/W = 2.08 \pm 0.19$) as bounds on the true result.

## UPDATED CONCLUSIONS PARAGRAPH:

We have analyzed core spacing in HGBS filaments, combining observational analysis with self-gravitating MHD simulations. Independent injection-recovery validation of the branching-point correction was performed, revealing that the correction magnitude may require revision (initial tests suggest 3.0\% bias rather than 17.2\%). Pending final validation with full DisPerSE skeleton complexity, the corrected value $\lambda/W = 2.44 \pm 0.28$ should be regarded as model-dependent.

The discrepancy between observed HGBS spacings and classical fragmentation theory is substantially reduced once Gaia DR3 distances, topology effects, and projection are considered. The original HGBS result ($\lambda/W = 2.1$ using PM statistics) increased to $\lambda/W = 2.44 \pm 0.28$ with NN statistics and topology corrections, and further to $\lambda/W \sim 3.1$--$3.4$ with plausible projection corrections.

Our idealised simulations cannot directly test whether turbulent HGBS filaments follow the same scaling laws due to fundamental limitations in turbulence amplitude and regime overlap. The principal unresolved question is whether strongly supercritical turbulent filaments fragment through fundamentally different dynamical pathways than the near-critical cylinders analysed in classical instability theory.