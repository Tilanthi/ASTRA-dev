# ASTRA Autonomous — Current State of Understanding

**Last updated**: 2026-04-03
**Runs completed**: 12 (Discovery → Follow-Up → Green Valley → Final Synthesis → Cycle 1 → Cycle 7 → Phase 2 → Phase 2 cross-domain → Cycle 8 → Current Run)
**Hypotheses tested**: 20
**Hypotheses confirmed**: 4 partially | **Refuted**: 12 | **Inconclusive**: 5

---

## What We Know (High Confidence)

### Acceleration Scales
- RAR transition scale g† = 4.023 × 10⁻¹¹ m/s² (from 3,384 data points, 175 SPARC galaxies)
- Galaxy cluster median acceleration a_cluster = 3.591 × 10⁻¹¹ m/s² (from 1,743 MCXC clusters)
- a_cluster/g† = 0.893, ratio robust across mass quartiles, redshift bins, selection methods
- Both scales trace the cosmic mean density — the agreement is cosmologically expected, not physically surprising

### Scaling Relations
- BH M-σ slope β = 4.73 ± 0.06 (230 BHs, consistent with AGN feedback models)
- Cluster L-M slope = 1.68 ± 0.01 (exceeds self-similar 1.33, indicating non-thermal pressure)
- RAR intrinsic scatter < 0.13 dex, universal across galaxy types

### Cosmology
- SN Ia ΛCDM: H₀ = 72.36 ± 0.28, Ω_m = 0.383 ± 0.020
- BIC strongly favors ΛCDM over w₀wₐCDM (ΔBIC = 11.3)
- w₀ = −0.71, wₐ = −0.80 consistent with cosmological constant at 1.8σ
- Hubble tension: 4.9σ between Planck (67.4) and SH0ES (73.04)
- The tension is methodological (ΛCDM-assuming vs model-independent), not purely temporal
- **NEW**: Hierarchical Bayesian analysis (H016) finds "true" H₀ = 70.24 ± 0.83, with distance_ladder biased HIGH (+2.48) and early-universe biased LOW (−1.9). Excluding biased categories: H₀ = 70.52 ± 0.52.
- **NEW**: Causal analysis (H017) confirms the split is driven by ΛCDM assumption, not epoch. t = −7.29, p = 5e−8. Independent methods converge to H₀ ≈ 70.5.
- **NEW**: Dark energy is the cosmological constant (H020). Piecewise w(z) models strongly disfavored (ΔBIC = +20). No evidence for DE phase transition.

### CMB
- Low-ℓ power deficit confirmed (quadrupole 4–5× lower than ΛCDM expectation)
- Anomaly catalog compiled, none individually exceed 5σ
- All anomalies robust across data releases (COBE → Planck NPIPE)

### Galaxy Populations
- 82,891 SDSS galaxies, PCA recovers blue cloud / red sequence bimodality
- Known correlations (M★-σ, sSFR-color, M★-concentration) confirmed, no unexpected correlations

---

## What We Think (Medium Confidence)

### Dimensional Analysis
- g†/[c√(Gρ_baryon)] = 0.80 at z=0 — closest-to-unity ratio found, but fails redshift test (drops to 0.28 at z=1)
- g†/cH₀ = 0.061 — not close to 1/(2π) ≈ 0.159 (standard MOND prediction requires n = 2.59)
- R = g†/H₀² = 273 Mpc — sits in middle of large-scale structure hierarchy, not distinctive

### Green Valley Connection
- Galaxies near RAR transition have 8× higher green valley fraction — but this is the mass-size relation in disguise
- Partial correlation ρ(a, GV | M★) = −0.025 — acceleration adds no information beyond mass
- SPARC gas fraction ρ(g_bar, gas_fraction) = −0.894 is the strongest single predictor but confounded with mass

---

## What We Suspect (Low Confidence)

- The a_cluster/g† coincidence, while expected from ΛCDM, may still encode useful information about the connection between galaxy-scale and cluster-scale physics
- The RAR transition scale g† may be related to the baryonic surface density threshold for disk stability, but this needs proper testing

---

## Cross-Domain Findings (NEW)

### Population Scaling Laws (CD-006)
- GDP ~ Population^0.938, CO2 ~ Population^0.925, Energy ~ Population^0.910
- **Universal sub-linear scaling** (β ≈ 0.93) — consistent across economic and environmental quantities
- DIFFERENT from biological (β = 0.75, Kleiber) and urban (β ~ 1.15, superlinear) scaling
- Countries are sub-linear: bigger countries are less economically efficient per capita

### COVID Mortality vs GDP (CD-001)
- CFR ~ (GDP/capita)^(-0.315), R² = 0.18, p = 4.6e-8
- 10× richer → 52% lower CFR (healthcare quality effect)
- But Deaths/Million ~ (GDP/capita)^1.1 — richer countries had MORE total deaths
- Paradox: better treatment, more exposure

### CO2-Temperature (CD-002)
- R² = 0.999974 — essentially perfect linear relationship
- Subtle curvature (F = 1876) but sub-linear at high emissions
- Country-level slopes cluster at 440-450 °C/GtC
- No regime shift or threshold detected

### GDP Growth vs Temperature Anomaly (CD-005)
- No significant relationship found between GDP growth rates and temperature anomalies
- Quadratic model fit yields R² ≈ 0.000 (cross-validated), indicating no predictive power
- No optimal temperature anomaly detected; hypothesis of a peaked relationship refuted

### Causal Structure of Climate-Economy-Pandemic System (CD-007)
- **NEW**: Causal discovery using NOTEARS algorithm produced a fully connected graph with 9 nodes and 72 edges, suggesting high interdependence or overfitting. Clear causal pathways (e.g., CO2 → GDP or GDP → pandemic outcomes) are not distinctly identifiable due to bidirectional edges. Confidence in actionable causal structure is low (0.3).

---

## What We've Ruled Out

1. ~~a_cluster ≈ g† is a mysterious coincidence~~ → Cosmologically expected (permutation test: 100% of shuffled samples within 10%)
2. ~~Green valley galaxies cluster at the RAR transition~~ → Mass-size relation in disguise (ρ = −0.025 controlling for mass)
3. ~~g†/[c√(Gρ_baryon)] = 0.80 is fundamental~~ → Epoch-specific coincidence (ratio = 0.28 at z=1, 0.055 at z=5)
4. ~~Cross-scale residual correlations exist~~ → BH M-σ, RAR, and cluster L-M residuals are independent
5. ~~Clean dimensional ratios connect acceleration scales~~ → No simple fractions (1, 2π, √2, etc.)
6. ~~273 Mpc scale is distinctive~~ → Not a clean multiple of anything, doesn't mark a transition in the power spectrum
7. ~~RAR residuals correlate with galaxy properties~~ → Zero physical properties survive multiple comparison correction (N=173, 9 properties tested). The RAR is universal; residual scatter is uncorrelated with SPARC measurements. Quality flag artifact confirms the analysis method works.
8. **NEW**: ~~Cluster L-M slope excess correlates with environment~~ → H009 analysis found no significant variation in L-M slope across density bins (p=0.512, slopes 1.69–1.71). Environmental density does not affect the excess over self-similar scaling.

---

## Strategic Direction (Supercharged)

We've spent 5 cycles rigorously ruling out candidates — that was Phase 1. Now we shift to **Phase 2: Discovery Mode**.

**New priorities (H016–H024)**:
- H016 (P1): Hierarchical Bayesian H₀ — can we resolve the tension from within the data?
- H017 (P1): Causal discovery across all datasets — hidden variables driving cosmological anomalies
- H020 (P1): Dark energy phase transition — does w(z) change at a specific redshift?
- H021 (P1): g† / (c²√Λ) — does the acceleration scale encode the cosmological constant?
- H018 (P2): Galaxy trichotomy — is there a hidden third population in SDSS?
- H019 (P2): BH-cluster unified scaling — common mass assembly pathway?
- H022 (P2): Correlated anomalies — CMB + H₀ + cluster excess share a common origin?
- H023 (P3): RAR as maximum entropy — is the RAR informationally optimal?
- H024 (P2): Multi-outlier objects — new astrophysical populations?

**Strategy shift**: From "what can we rule out?" to "what can we discover?" Use all datasets simultaneously. Cross-correlate anomalies. Use causal discovery. Use information theory. Look for objects that break multiple rules. Never stop.

---

## Available Resources

### Datasets
| Dataset | N | Location |
|---------|---|----------|
| SPARC RAR | 3,384 pts / 175 galaxies | `radial_acceleration_relation.csv` |
| Galaxy Clusters | 1,744 | `galaxy_cluster_data.csv` |
| BH M-σ | 230 | `bh_msigma_clean.csv` |
| SDSS Galaxies | 82,891 | `sdss_galaxy_properties.csv` |
| SN Ia Pantheon+ | 1,544 | `sn_ia_pantheonplus.csv` |
| H₀ Compilation | 53 | `h0_compilation.csv` |
| CMB Power Spectrum | 250 bins | `cmb_power_spectrum.csv` |
| BAO | 8 | (in analysis scripts) |

### Previous Analyses
- `analysis_crossscale.py` — Scaling relations, RAR, BH M-σ, clusters
- `analysis_cosmology_v3.py` — SN Ia + BAO fitting
- `analysis_cmb.py` — CMB power spectrum analysis
- `analysis_discovery.py` — Acceleration coincidence
- `analysis_followup.py` — Deep dive subsamples
- `analysis_greenvalley.py` — Green valley connection
- `analysis_final_synthesis.py` — Dimensional ratio tests

### Plots (12 original + follow-ups)
All in `/shared/ASTRA/data/discovery_run/plots/`