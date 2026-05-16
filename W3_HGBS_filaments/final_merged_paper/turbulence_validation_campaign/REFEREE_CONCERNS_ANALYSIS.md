# Referee Concerns Analysis
## Response Strategy - Simulation vs Text Revisions

**Date**: 26 April 2026

---

## Summary of Referee Concerns

| # | Concern | New Sims Needed? | Response Strategy |
|---|---------|------------------|-------------------|
| 1 | Central disconnect - supercritical sims can't measure λ/W | **NO** | Text revisions clarifying what results actually mean |
| 2 | Unrealistic turbulence (δv/cs ~ 10⁻⁴) | **YES** | Turbulence validation campaign (48 sims) |
| 3 | Stochastic zone may be duration artifact | **NO** | Analyze existing sim duration data |
| 4 | Perpendicular field λ/W predictions | **NO** | Theoretical calculation using existing calibration |

---

## Concern 1: Central Disconnect (NO NEW SIMS)

### Referee's Point
The simulation campaign (1,616 runs) cannot directly measure the quantity it seeks to constrain. Supercritical filaments (f ≥ 1.5) show zero longitudinal beading in all 654 simulations. The comparison rests entirely on extrapolation from near-critical simulations (f = 1.00-1.20).

### Why New Simulations Won't Help
Running more supercritical simulations with the same setup will just reproduce the same result (radial collapse dominates). The issue is conceptual, not numerical.

### Response Strategy: Text Revisions

**Add to Section 5.1 (Discussion), after the calibration caveat:**

```latex
\textbf{Implications of the supercritical radial collapse result for
theoretical framework}. The universal preference for radial collapse over
longitudinal beading in supercritical filaments ($f \gtrsim 1.5$) has important
implications for how we interpret the observational comparison. If real HGBS
filaments are indeed in the supercritical regime ($f \approx 1.5$--$3.0$ based
on typical column densities), then the observed discrete core spacing cannot
arise from the classical linear instability growth mechanism that operates in
near-critical filaments. Several alternative mechanisms warrant consideration:

\begin{enumerate}
    \item \textbf{Fragmentation during filament formation}: Cores may form
    during the assembly process of filaments from larger cloud structures,
    rather than from fragmentation of pre-existing filaments. The observed
    spacing would then reflect the fragmentation scale of the parent cloud
    rather than the internal filament dynamics.

    \item \textbf{Turbulent fragmentation}: At realistic ISM turbulence
    levels ($\delta v/c_s \sim 1$--$10$, well above our simulated values),
    turbulent forcing may create density structures that collapse into cores
    on timescales competitive with radial collapse. The observed spacing could
    reflect the turbulent driving scale rather than gravitational instability.

    \item \textbf{Hierarchical structure}: As discussed in Section~3.2, the
    fiber-resolved analysis in Orion B shows that fiber-to-core spacing
    recovers the classical $4\times$ prediction, while filament-to-core
    measurements show sub-Jeans values. This suggests that what we measure as
    ``core spacing'' at the filament level may be a projection/averaging effect
    across multiple fiber bundles, each fragmenting at the classical scale.

    \item \textbf{Non-equilibrium filaments}: Real filaments are not static
    equilibria but are continuously accreting mass, evolving, and interacting
    with their environment. The supercritical radial collapse result may be
    specific to isolated equilibrium filaments and may not apply to
    dynamically evolving filaments where longitudinal structure can develop
    concurrently with radial evolution.
\end{enumerate}

Our simulation results demonstrate that {\it within the idealized framework
of isolated, equilibrium filaments with weak perturbations}, supercritical
configurations prefer radial collapse over longitudinal beading. This is a
valid numerical result with clear implications: any theoretical framework that
relies on longitudinal beading in supercritical filaments must address why
this mechanism is not observed in our simulations. However, we cannot conclude
that real HGBS filaments must be near-critical; they may form cores via
mechanisms outside the scope of our simulation setup. The calibration
$\lambda_{\rm frag} = 1.11\,\lambda_{MJ}$ derived from near-critical simulations
should therefore be regarded as a {\it conditional prediction}: {\it if} HGBS
filaments fragment via the same linear instability mechanism that operates in
our near-critical simulations, {\it then} the predicted spacing is
$\lambda/W_{\rm core} = 3.70 \pm 0.40$ (longitudinal B-fields).
Alternative core formation mechanisms would yield different predictions.
```

**Modify Abstract to reflect this caveat:**

Change:
> Our simulation campaign covers supercritical filaments, transition boundary mapping, field geometry effects, and validation tests.

To:
> Our simulation campaign reveals that {\it supercritical filaments} ($f \gtrsim 1.5$) undergo rapid radial collapse before longitudinal beading can develop, preventing direct measurement of fragmentation wavelengths in this regime. We therefore calibrate the theoretical prediction using {\it near-critical simulations} ($f = 1.00$--$1.20$) where longitudinal beading is directly observed, and consider the implications for supercritical HGBS filaments.

---

## Concern 2: Turbulence Implementation (NEW SIMS - 48 total)

### Referee's Point
δv/cs ~ 10⁻⁴ is unrealistically weak. The claim that t_frag is independent of M cannot be generalized to real filaments.

### Response: Turbulence Validation Campaign
**Specification provided in `README.md` and `config.json`**

**Minimum viable campaign**: 48 simulations
- f ∈ {1.5, 2.0}
- β ∈ {0.3, 1.0}
- M ∈ {1.0, 2.0}
- δv/cs ∈ {0.1, 0.5, 1.0}
- 2 seeds per point

### Expected Outcomes

| Outcome | Interpretation | Paper Revision |
|---------|---------------|----------------|
| <20% variation in t_frag | Independence is robust | Add validation text, caveat extreme amplitudes |
| 20-50% variation | Moderate dependence | Qualify independence claims |
| >50% variation | Strong dependence | Major revision of Mach number conclusions |

---

## Concern 3: Stochastic Zone (NO NEW SIMS - ANALYZE EXISTING DATA)

### Referee's Point
Are the 12 stochastic points (1/2 fragmentation) genuinely stochastic or just duration artifacts?

### Response: Check Simulation Durations

**Add to Section 4.3 analysis:**

```python
# Analysis script to check simulation durations for stochastic points
stochastic_points = [...]  # 12 parameter points
for point in stochastic_points:
    duration_seed1 = results[point]['seed1']['sim_duration']
    duration_seed2 = results[point]['seed2']['sim_duration']
    # Check if durations are similar (>80% agreement)
    # If one seed ran 2x longer, that's evidence for duration artifact
```

**Expected finding**: If durations are similar, stochasticity is genuine. If not, may need extended re-runs.

---

## Concern 4: Perpendicular Field Predictions (NO NEW SIMS - THEORETICAL)

### Referee's Point
Could perpendicular field calibration produce λ/W ≈ 2.79 consistent with observations?

### Response: Theoretical Calculation

Using λ_frag = 1.11 × λ_MJ with λ_MJ = λ_J × √(1 + 2sin²θ/β):

**For θ = 90° (perpendicular):**
λ_MJ = λ_J × √(1 + 2/β)

**Example calculations:**
- β = 0.3: λ_MJ = λ_J × √(1 + 2/0.3) = λ_J × 2.83
- β = 1.0: λ_MJ = λ_J × √(1 + 2/1.0) = λ_J × 1.73
- β = 2.0: λ_MJ = λ_J × √(1 + 2/2.0) = λ_J × 1.41

**Calibrated predictions (λ/W_core):**
- β = 0.3: λ/W_core = 1.11 × 2.83 / 0.3 = 10.5
- β = 1.0: λ/W_core = 1.11 × 1.73 / 0.3 = 6.4
- β = 2.0: λ/W_core = 1.11 × 1.41 / 0.3 = 5.2

**After width conversion (divide by 3.3):**
- β = 0.3: λ/W_fil = 3.2
- β = 1.0: λ/W_fil = 1.9
- β = 2.0: λ/W_fil = 1.6

**Key insight**: For β ≈ 1.0-2.0 (typical HGBS values), perpendicular field predictions give λ/W_fil = 1.6-1.9, which is **below** the observed 2.79. This is in the wrong direction - perpendicular fields predict shorter spacings, not longer.

**Add to Section 5.2:**

```latex
\textbf{Perpendicular field predictions}. Using the field-geometry-calibrated
formula $\lambda_{\rm frag} = 1.11\,\lambda_{MJ}$ with
$\lambda_{MJ} = \lambda_J\sqrt{1 + 2\sin^2\theta/\beta}$, we can predict
the spacing for perpendicular field geometry ($\theta = 90^\circ$). For
typical HGBS conditions ($\beta = 1.0$--$2.0$), this gives
$\lambda/W_{\rm fil} = 1.6$--$1.9$ after width conversion---{\it below} the
observed value of $2.84$. The perpendicular field result therefore cannot
explain the observed sub-Jeans spacing; if anything, perpendicular fields
would predict even shorter spacings than longitudinal fields, moving the
prediction further from the observed value. The fact that most HGBS filaments
are perpendicular to the mean field (Planck Collaboration 2016) combined
with our finding that perpendicular fields accelerate fragmentation only
deepens the discrepancy between simple magnetic tension theory and
observations.
```

---

## Priority Order for Response

1. **HIGH**: Address Concern 2 (Turbulence) - Run 48 simulations if time permits
2. **HIGH**: Address Concern 1 (Disconnect) - Text revisions required regardless
3. **MEDIUM**: Address Concern 4 (Perpendicular) - Theoretical calculation, add text
4. **MEDIUM**: Address Concern 3 (Stochastic) - Analyze existing data

---

## Decision Framework for Additional Simulations

**Run turbulence validation campaign if:**
- External 200 CPU machine is available
- 8-12 hour wall time is acceptable
- You want to strengthen the Mach number independence claim

**Skip turbulence validation and address via text if:**
- Computational resources are unavailable
- Time is limited
- You're comfortable qualifying the Mach number result

**Recommended path**: Run the minimum viable campaign (48 simulations, ~8 hours). The referee's concern is valid, and having numerical evidence at realistic amplitudes would substantially strengthen the paper's claims.
