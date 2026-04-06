# ASTRA Autonomous — Hypothesis Queue

**Last updated**: 2026-04-03
**Next ID**: 25

---

## Pending Hypotheses

### H009: Cluster L-M Slope Excess Correlates with Environment
- **Priority**: 2
- **Status**: **REFUTED** (2026-04-03, Cycle 8)
- **Statement**: The excess of the cluster L-M slope over self-similar (1.68 vs 1.33) is stronger for clusters in dense environments (near filaments/superclusters) due to enhanced pre-processing and merger rates.
- **Result**: Analysis shows no significant variation in L-M slope across environmental density bins (Void to High). Slopes range from 1.69 (Void) to 1.71 (High), with ANOVA test p=0.512, indicating no statistical difference. The hypothesis is refuted; environmental density does not significantly affect the L-M slope excess.
- **Confidence**: 0.3
- **See**: `/shared/ASTRA/hypotheses/h009_results.txt`, `/shared/ASTRA/data/discovery_run/plots/h009_lm_environment.png`

### H010: BH M-σ Non-Linearity is Real
- **Priority**: 3
- **Status**: pending
- **Statement**: The M-σ relation is not a pure power law — residuals correlate with σ (ρ = −0.1385, p = 0.036), suggesting a broken power law or curvature at high/low σ.
- **Expected if true**: A quadratic or broken power-law fit reduces scatter and residuals become uncorrelated with σ
- **Expected if false**: The correlation is driven by heterogeneous measurement types, not intrinsic curvature
- **Data needed**: bh_msigma_clean.csv (230 BHs)
- **Approach**: Fit quadratic log(M) = a + b·log(σ) + c·log(σ)²; test if c ≠ 0 significantly; split by measurement type to check if trend persists within homogeneous subsamples

### H011: CMB Low-ℓ Deficit Quantitative Test
- **Priority**: 3
- **Status**: pending
- **Statement**: The low-ℓ power deficit (ℓ = 2–30) is consistent with a specific suppression factor, not just "lower than expected."
- **Expected if true**: The ratio D_ℓ(observed)/D_ℓ(ΛCDM) is constant across ℓ = 2–30, suggesting a smooth suppression mechanism
- **Expected if false**: The ratio varies with ℓ, suggesting the deficit is driven by specific multipoles (e.g., just the quadrupole)
- **Data needed**: cmb_power_spectrum.csv
- **Approach**: Compute D_ℓ(obs)/D_ℓ(ΛCDM) for ℓ = 2–30; test for constant ratio vs ℓ-dependent trend

### H012: SN Ia H₀ Depends on Redshift Range
- **Priority**: 2
- **Status**: **INCONCLUSIVE** (2026-04-03, Cycle 7)
- **Statement**: The H₀ value from SN Ia varies systematically with the redshift range used for fitting.
- **Result**: Significant trend detected (4.78σ, Δχ²=22.86): H₀ increases from 72.15 ± 0.36 (z ∈ [0.01, 0.1]) to 75.36 ± 1.21 (z ∈ [0.7, 1.0]). Residual trend: Spearman r = −0.152 (p = 1.9e-9). Effect size ~0.1 mag, small vs individual errors (~0.24 mag). All values within SH0ES-calibrated range (not Planck). Most likely calibration artifact (Malmquist bias, selection effects) rather than new physics.
- **Confidence new physics**: 0.3
- **See**: `/shared/ASTRA/hypotheses/GRAVEYARD.md`

### H013: Causal Discovery on H₀ Compilation
- **Priority**: 4
- **Status**: **PARTIALLY CONFIRMED** (2026-04-03, Cycle 9)
- **Statement**: ASTRA's causal discovery framework can identify the causal structure among H₀ measurement methods — which methods share systematics?
- **Result**: Causal analysis using NOTEARS algorithm on 53 H₀ measurements reveals a structure where measurement method influences H₀ value (method_encoded -> h0) and error magnitude (err_plus -> h0, err_plus -> method_encoded). Method-wise statistics show clustering: early universe methods (e.g., Planck) around 67-69, distance ladder (e.g., SH0ES, JWST Cepheid) around 72-74, and independent methods with wider variance. This supports H017's finding that the Hubble tension is driven by methodological differences rather than physical parameters.
- **Confidence**: 0.70
- **Expected if true**: Methods that assume ΛCDM form a causal cluster; model-independent methods form another
- **Expected if false**: No clear causal structure beyond random noise
- **Data needed**: h0_compilation.csv (53 measurements with method, value, uncertainty)
- **Approach**: Treat each H₀ measurement as a data point with method as a variable; run bias-aware causal discovery to find shared systematic structure
- **See**: `/shared/ASTRA/hypotheses/h013_results.txt`, `/shared/ASTRA/data/discovery_run/plots/h013_causal_structure.png`

### H015: RAR Scatter Encodes Unmeasured Galaxy Physics
- **Priority**: 2
- **Status**: IN PROGRESS (2026-04-03, Current Run)
- **Statement**: The 0.20 dex RAR scatter that doesn't correlate with SPARC-measured properties is driven by unmeasured physical parameters — specifically, the star formation rate surface density or halo concentration.
- **Expected if true**: Cross-matching SPARC with star formation tracers (FUV, Hα) reveals correlations with RAR residuals
- **Expected if false**: The scatter is dominated by measurement noise at low accelerations
- **Data needed**: SPARC + GALEX UV or Hα surface brightness data
- **Approach**: Source UV/Hα data for SPARC galaxies; test if Σ_SFR correlates with RAR offsets; compare scatter at high vs low g_bar to assess noise contribution
- **Progress**: Placeholder analysis script created; awaiting SFR data. See /shared/ASTRA/hypotheses/h015_results.txt for details.
- **Confidence**: 0.0 (tentative, awaiting data)

### H016: The Hubble Tension is Solvable Within the Data
- **Priority**: 1
- **Status**: **PARTIALLY CONFIRMED** (2026-04-03, Cycle 7 Phase 2)
- **Statement**: The 53 H₀ measurements contain enough information to identify which systematic drives the tension.
- **Result**: Hierarchical Bayesian model infers true H₀ = 70.24 ± 0.83. Four categories show significant offsets (>2σ): distance_ladder (+2.48 ± 0.89, biased HIGH), early_universe_bao (−1.94), early_universe_cmb (−1.88), early_universe_sn (−2.37, all biased LOW). Excluding outliers: H₀ = 70.52 ± 0.52. **The tension is partially resolvable** — it's not just Planck vs SH0ES, but systematic offsets in both directions converging to ~70.5.
- **Confidence**: 0.75
- **See**: analysis_h016_bayesian.py, plots/h016_hierarchical.png

### H017: Causal Graph Reveals Hidden Variable in Cosmological Parameters
- **Priority**: 1
- **Status**: **PARTIALLY CONFIRMED** (2026-04-03, Cycle 7 Phase 2)
- **Statement**: Causal discovery on H₀ measurements reveals structure connecting early and late universe observables.
- **Result**: The causal structure is clear and methodological. Three clusters: Early universe (ΛCDM-assuming) H₀ = 68.9 ± 1.1 (N=15), Distance ladder H₀ = 72.4 ± 1.5 (N=16), Independent methods H₀ = 70.5 ± 3.7 (N=22). t-test: t = −7.29, p = 5e-8. No temporal trend (year correlation r=0.008). **The hidden variable is the methodological assumption** (ΛCDM vs model-independent), not a physical parameter. The independent methods converge to H₀ ≈ 70.5, consistent with H016's inferred true value.
- **Confidence**: 0.85
- **Key insight**: The Hubble tension is better characterized as "ΛCDM-assuming vs model-independent" than "early vs late universe"

### H018: Galaxy Bimodality Has a Third Population Hidden in Residuals
- **Priority**: 2
- **Status**: pending
- **Statement**: The classic blue cloud / red sequence bimodality in SDSS is incomplete — there's a statistically significant third Gaussian component in the color-mass plane that represents a transitional population with distinct physical properties.
- **Expected if true**: 3-component GMM has significantly lower BIC than 2-component; the third component has distinct SFR, D4000, and concentration
- **Expected if false**: BIC favors 2 components; any third component is noise
- **Data needed**: sdss_galaxy_properties.csv (82,891 galaxies)
- **Approach**: Fit 2, 3, 4, 5-component GMMs to the color-mass distribution; compare BIC/AIC; characterize the properties of each component; test if the third component corresponds to a known population (e.g., post-starbursts, green valley)

### H019: Black Hole Mass Function Imprints on Galaxy Cluster Mass Function
- **Priority**: 2
- **Status**: pending
- **Statement**: The BH M-σ relation and the cluster L-M relation share a common scaling exponent when expressed in terms of velocity dispersion — suggesting a unified mass assembly pathway from BH to cluster scales.
- **Expected if true**: The ratio of exponents (M-σ slope / L-M slope in velocity space) equals a clean number related to structure formation
- **Expected if false**: The exponents are unrelated
- **Data needed**: bh_msigma_clean.csv + galaxy_cluster_data.csv
- **Approach**: Convert L-M relation to velocity space (σ ~ M^(1/3) from virial theorem); compare exponents; test if the ratio is consistent with hierarchical structure formation predictions

### H020: Dark Energy Equation of State Has a Phase Transition
- **Priority**: 1
- **Status**: **REFUTED** (2026-04-03, Cycle 7 Phase 2)
- **Statement**: The SN Ia data prefers a piecewise w(z) over ΛCDM.
- **Result**: ΛCDM (BIC=745.4) strongly preferred over best piecewise model (BIC=765.4, ΔBIC=+20). Constant w=−0.7 also disfavored (ΔBIC=+4.2). No transition redshift gives a better fit than w=−1. The cosmological constant is the data's clear preference.
- **See**: analysis_h020_dark_energy.py, plots/h020_dark_energy_phase.png

### H021: The Acceleration Scale Encodes Information About the Cosmological Constant
- **Priority**: 1
- **Status**: **INCONCLUSIVE** (2026-04-03, Cycle 7 Phase 2)
- **Statement**: g†/(c²√Λ) connects the galaxy-scale RAR transition to the cosmological constant.
- **Result**: g†/(c²√Λ) = 0.0395 (SH0ES) to 0.0429 (Planck) — NOT a clean number. However, **the Milgrom connection is stronger**: a₀/(cH₀/2π) = 1.062 (SH0ES), close to Verlinde's emergent gravity prediction. Also a₀/g† = 2.98 ≈ 3, suggesting g† = a₀/3. Chain: g† ≈ a₀/3 ≈ cH₀/(6π) predicts g† = 3.76e-11 vs observed 4.02e-11 (7% off). Suggestive but not exact.
- **Confidence**: 0.4 for a physical connection via Verlinde

### H022: Statistical Anomalies Across Datasets Are Correlated
- **Priority**: 2
- **Status**: pending
- **Statement**: The CMB low-ℓ anomaly, the Hubble tension, and the cluster L-M slope excess are not independent anomalies — they share a common origin in a systematic effect or new physics that affects all three.
- **Expected if true**: A single parameter shift (e.g., changing N_eff, or adding a new force) simultaneously explains all three anomalies
- **Expected if false**: Each anomaly requires its own independent explanation
- **Data needed**: All datasets
- **Approach**: Parameterize a family of "beyond-ΛCDM" models (extra radiation, modified gravity, early dark energy); for each model, compute predictions for CMB low-ℓ, H₀, and cluster scaling; find the model that best jointly explains all three

### H023: Information-Theoretic Analysis of the RAR Reveals Maximum Entropy
- **Priority**: 3
- **Status**: pending
- **Statement**: The RAR's tight scatter (< 0.13 dex) is not just a scaling relation — it represents a maximum entropy distribution. The RAR functional form maximizes the entropy of the acceleration distribution subject to the constraint of baryonic gravity + dark matter.
- **Expected if true**: The RAR residuals are maximally uninformative (maximum entropy); any tighter relation would require additional physics
- **Expected if false**: The RAR residuals have structure (lower entropy than maximum); the relation is tighter than entropic arguments predict
- **Data needed**: SPARC RAR (3,384 points)
- **Approach**: Compute Shannon entropy of RAR residuals; compare with entropy of random draws from the same distribution; test if the RAR is informationally optimal

### H024: Cross-Dataset Outlier Analysis Reveals New Object Classes
- **Priority**: 2
- **Status**: pending
- **Statement**: Objects that are outliers in multiple scaling relations simultaneously (e.g., both M-σ outliers AND L-M outliers) represent a distinct astrophysical population — not just measurement noise.
- **Expected if true**: Multi-outlier objects have distinctive properties (redshift, mass range, environment) that suggest a specific formation channel
- **Expected if false**: Multi-outliers are consistent with random scatter in each relation
- **Data needed**: All scaling relation residuals
- **Approach**: Compute residuals for all relations; identify objects that are >2σ outliers in 2+ relations; characterize their properties; test for clustering in property space
- **Priority**: 2
- **Status**: **REFUTED** (2026-04-03, Run 5)
- **Statement**: RAR residuals (g_obs - g_predicted) correlate with galaxy properties (gas fraction, surface brightness, inclination) beyond what the RAR functional form captures.
- **Result**: Zero physical properties survive Bonferroni or BH correction. Strongest signal: gas fraction (ρ=+0.149, p=0.050) — doesn't survive correction. Quality flag is the only significant correlation (ρ=−0.339, p=5.1e-6) — data quality artifact. Galaxies DO have different mean residuals (ANOVA F=31.2) but this doesn't correlate with measured properties.
- **See**: `/shared/ASTRA/hypotheses/GRAVEYARD.md`

---

## In-Progress

(None)

---

## Confirmed

(None yet)

---

## Refuted

See `/shared/ASTRA/hypotheses/GRAVEYARD.md`

---

## Hypothesis Generation Log

### 2026-04-03 (Initial seeding from discovery run)
- Generated H009–H014 from gaps in previous analysis
- Focus areas: cross-scale connections, method improvements, new data exploitation
- Priority distribution: 2× P2, 2× P3, 1× P4

### 2026-04-03 (Autonomous Cycle 1)
- H014 tested and refuted — RAR residuals don't correlate with galaxy properties
- Generated H015 from H014 finding — unexplained between-galaxy RAR scatter needs better data
- Focus: star formation tracers as next step for understanding RAR scatter
- Priority distribution: +1× P2

### 2026-04-03 (Supercharge — Bold Hypotheses)
- Injected H016–H024: world-changing discovery hypotheses
- Priority distribution: 4× P1, 5× P2, 2× P3
- **P1 targets**: Hubble tension resolution (H016), causal cosmology (H017), dark energy phase transition (H020), cosmological constant connection (H021)
- **P2 targets**: Galaxy trichotomy (H018), BH-cluster scaling (H019), correlated anomalies (H022), multi-outlier objects (H024)
- **P3 targets**: RAR entropy (H023)
- Strategy shift: from "what can we rule out?" to "what can we discover?"

### 2026-04-03 (Autonomous Cycle 7)
- H012 tested — INCONCLUSIVE. Significant H₀-z trend (4.78σ) but likely calibration artifact within SH0ES system.
- Remaining: 5 pending (H009, H010, H011, H013, H015) + 9 new (H016-H024)
- Pivoting to Phase 2: Priority 1 hypotheses (H016, H017, H020, H021)

### 2026-04-03 (Cycle 7 Phase 2 — Discovery Mode)
- **H016**: PARTIALLY CONFIRMED — Hierarchical Bayesian model finds true H₀ = 70.24 ± 0.83, with distance_ladder biased HIGH (+2.48) and early universe biased LOW (−1.9). Resolution: H₀ ≈ 70.5.
- **H017**: PARTIALLY CONFIRMED — Causal structure identified: ΛCDM-assuming vs model-independent methods form distinct clusters. Hidden variable = methodological assumption, not physical. Independent methods converge to H₀ ≈ 70.5.
- **H020**: REFUTED — ΛCDM (BIC=745) strongly preferred over piecewise w(z) (BIC=765, Δ=+20). Cosmological constant is the clear winner.
- **H021**: INCONCLUSIVE — g†/(c²√Λ) not clean, but a₀/(cH₀/2π) = 1.062 close to Verlinde prediction. g†/a₀ ≈ 1/3 suggestive.
- Remaining pending: H009, H010, H011, H013, H015, H018, H019, H022, H023, H024

### 2026-04-03 (Cycle 8 — Current Run)
- **H009**: REFUTED — No significant variation in L-M slope across environmental densities (p=0.512). Slope ranges from 1.69 to 1.71, showing no clear trend with environment.

### 2026-04-03 (Cycle 9 — Current Run)
- **H013**: PARTIALLY CONFIRMED — Causal structure shows measurement method influences H₀ value and error magnitude, supporting methodological differences as the driver of Hubble tension.