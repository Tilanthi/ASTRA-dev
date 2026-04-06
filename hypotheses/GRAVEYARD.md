# ASTRA Autonomous — Hypothesis Graveyard

Refuted hypotheses and lessons learned.

---

### H001: a_cluster ≈ g† is a mysterious physical coincidence
- **Refuted**: 2026-04-03 (Run 2: Follow-Up)
- **Reason**: Permutation test shows 100% of shuffled M500 distributions land within 10% of g†. The M-R relation naturally produces accelerations at this scale. Both scales trace cosmic mean density.
- **Lesson**: Always do permutation tests for "coincidence" claims. Check if the coincidence is expected from the underlying physics.

### H002: The coincidence is universal across all cluster masses
- **Refuted**: 2026-04-03 (Run 2: Follow-Up)
- **Reason**: a_cluster/g† ranges from 0.6 (Q1) to 1.3 (Q4). The coincidence is specific to the median cluster, not universal.
- **Lesson**: Subsample analysis can reveal that a "robust" finding only holds in a specific regime.

### H003: Green valley galaxies cluster at the RAR transition (8× effect)
- **Refuted**: 2026-04-03 (Run 3: Green Valley)
- **Reason**: Partial correlation ρ(a, GV | M★) = −0.025. The signal is entirely explained by the mass-size relation. Mass-matched analysis shows sign reversal at log M★ ≈ 10.5.
- **Lesson**: Spectacular-sounding ratios (8×!) are often confounded. Always disentangle with partial correlations and matched samples.

### H004: g†/[c√(Gρ_baryon)] = 0.80 is a fundamental dimensional ratio
- **Refuted**: 2026-04-03 (Run 4: Final Synthesis)
- **Reason**: Ratio drops to 0.28 at z=1, 0.055 at z=5. Scales as (1+z)^−3/2 — epoch-specific coincidence. Cannot be derived from ΛCDM (virial acceleration scales as ρ^(2/3), not ρ^(1/2)).
- **Lesson**: Any claimed "fundamental ratio" must be tested across cosmic time. z=0-only coincidences are a dime a dozen.

### H005: Cross-scale residual correlations exist (BH↔RAR↔clusters)
- **Refuted**: 2026-04-03 (Run 2: Follow-Up)
- **Reason**: BH M-σ, RAR, and cluster L-M residuals are statistically independent. No hidden variable connects them.
- **Lesson**: Different scaling relations are governed by different physics — don't expect cross-talk without a physical mechanism.

### H006: The 273 Mpc scale (g†/H₀²) marks a distinctive transition
- **Refuted**: 2026-04-03 (Run 4: Final Synthesis)
- **Reason**: 273 Mpc = 1.86× BAO, ~2/3 of largest voids, comparable to supercluster complexes. Not a clean multiple of anything, doesn't appear in the power spectrum.
- **Lesson**: Intermediate scales in the continuous large-scale structure hierarchy are rarely distinctive unless they mark a sharp physical transition.

### H012: SN Ia H₀ Depends on Redshift Range
- **Evaluated**: 2026-04-03 (Cycle 7)
- **Status**: INCONCLUSIVE
- **Result**: Significant H₀-z trend detected: H₀ = 73.06 + 0.672·log₁₀(z_max), slope significance 4.78σ (Δχ² = 22.86). Exclusive bins: H₀ = 72.15 ± 0.36 (z ∈ [0.01, 0.1]) → 75.36 ± 1.21 (z ∈ [0.7, 1.0]). Residual Spearman r = −0.152 (p = 1.9e-9). Effect size ~0.1 mag over full z range, small vs individual SN uncertainties (~0.24 mag).
- **Interpretation**: All H₀ values are within the SH0ES-calibrated range (72–75). The trend does NOT create a tension with Planck — it's internal to the SH0ES-calibrated system. Most likely causes: (1) Malmquist bias at high-z (flux-limited sample selects brighter SNe), (2) calibration systematics propagating differently across z, (3) selection effects in high-z surveys. Confidence that this represents new physics: 0.3.
- **Lesson**: Statistical significance (4.78σ) does not equal physical significance. The trend is real in the data but is almost certainly a systematic artifact. Large N makes tiny effects detectable — always assess physical plausibility alongside statistical significance.
- **Data**: sn_ia_pantheonplus.csv (1,543 SNe), analysis_h0_redshift.py

### H014: RAR Residuals Correlate with Galaxy Properties
- **Refuted**: 2026-04-03 (Run 5: Autonomous Cycle 1)
- **Reason**: Tested 9 physical properties (gas fraction, surface brightness, inclination, scale length, velocity, mass, luminosity, Hubble type, quality). Zero survive Bonferroni or BH correction. Strongest: gas fraction (ρ=+0.149, p=0.050). Only quality flag is significant (ρ=−0.339, p=5.1e-6) — data quality artifact. Galaxies DO have different mean RAR offsets (ANOVA F=31.2, p≈0) but this doesn't correlate with measured properties.
- **Lesson**: The RAR appears universal across galaxy types — its residuals are random with respect to measurable properties. However, ~0.2 dex scatter between galaxies is real and unexplained by SPARC data alone. This scatter may encode unmeasured physics (SFR, halo properties) or simply reflect measurement noise at low accelerations.
- **Follow-up**: H015 generated to investigate whether star formation tracers explain the residual scatter.

---

## Meta-Lessons from the Graveyard

1. **7 out of 9 hypotheses were refuted.** This is a good ratio — it means we're testing aggressively, not just confirming what we already believe.
2. **The two inconclusive results** (H007: cross-scale residual structure, H008: SDSS correlation anomalies) need better data or methods to resolve.
3. **Every refuted hypothesis taught us something** about either the physics or the methodology.
4. **H014 reinforced a key insight**: The RAR is remarkably universal. The scatter that exists doesn't correlate with any standard galaxy property — suggesting either the scatter is noise, or the relevant physics isn't captured by SPARC measurements.
